#!/usr/bin/env python
"""
    simple python script watches ip changes of the different
    containers and starts dependent containers if an ip changes
"""

import traceback
import logging
import schedule
import time
import etcd

from rancher_api import RancherApi
from watcherconfig import WatcherConfig

# configure logger
# http://docs.python-guide.org/en/latest/writing/logging/
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def scheduled_task():
    """
        get managed containers. check if their ip address has changed
        and if so restart required containers
    """

    # connect to the rancher service
    logger.info('Connect to rancher api service')
    rancher = RancherApi(config.rancher_api_url, config.rancher_api_key, config.rancher_api_secret)

    # connect to etcd
    etcd_client = etcd.Client(host=config.etcd_host, port=int(config.etcd_port), allow_reconnect=True, allow_redirect=True)
    try:
        etcd_client.write('/container', None, dir=True)
    except etcd.EtcdNotFile:
        # the container folder already exists
        pass

    logger.info('Retrieve managed containers from rancher')
    managed_containers=rancher.get_containers_with_label(label=config.docker_label_enable,labelvalue='true',state='running')

    for c in managed_containers:
        logger.info("Checking container {}".format(c['name']))
        # get the current container ip
        if not 'io.rancher.container.ip' in c['labels']:
            logger.warn("Can not get the current ip of container. Continue with next container")
            continue
        else:
            current_ip = c['labels']['io.rancher.container.ip']
            logger.debug("Current IP {}".format(current_ip))

        logger.info("Check for last known ip in etcd")
        try:
            last_known_ip = etcd_client.read('/container/{}/ip'.format(c['name'])).value
        except etcd.EtcdKeyNotFound:
            logger.info('No ip recorded. Writing ip into etcd')
            # the key does not exist yet. so lets make sure the container folder exists
            try:
                etcd_client.write('/container/{}'.format(c['name']), None, ttl=600, dir=True)
            except etcd.EtcdNotFile:
                # the container folder already exists
                pass
            # and write the current ip into etcd
            etcd_client.write('/container/{}/ip'.format(c['name']), current_ip, ttl=600)
            last_known_ip = current_ip
        except:
            logger.warn("Not able to gt last known ip.")
            continue
        logger.info("Last known ip is {}".format(last_known_ip))

        # now compare the ip address retrieved from etcd
        # with the ip address reported by rancher
        # if they match we have nothing todo
        # if they dont match we may need to reboot some containers
        if current_ip != last_known_ip:
            logger.info('Current ip {} differs from last known ip {}'.format(current_ip, last_known_ip))
            # lets get the list of containers which need to be rebooted
            logger.info('Check for containers which need to be rebooted when the ip of the container changes')
            if config.docker_label_reboot in c['labels']:
                for r in c['labels'][config.docker_label_reboot].split(","):
                    logger.info("Container with name '{}' marked to reboot".format(r))
                    rc = rancher.get_containers(state='running',name=r)
                    if len(rc) != 1:
                        logger.warn('Could not find running container with name {}'.format(r))
                        continue
                    rc = rc[0]

                    # reboot the container
                    logger.info('Rebooting container')
                    rancher.restart_container(rc['id'])
                    rancher.wait_for_container(rc['id'],'running')
            else:
                logger.warn('No containers for reboot specified')

            logger.info('All actions executed. Store current ip into etcd')
            etcd_client.write('/container/{}/ip'.format(c['name']), current_ip, ttl=600)
        else:
            logger.info("Last known ip matches current ip. Nothing todo")
            continue

def main():
    """
        main function
    """
    # initialize the configuration
    logger.info('Started watcher script')
    logger.info('Load configuration')
    global config
    config = WatcherConfig()

    # set the log level
    if config.loglevel == "info":
        logger.setLevel(logging.INFO)
    if config.loglevel == "debug":
        logger.setLevel(logging.DEBUG)

    # start scheduler
    logger.info('Start scheduler and run update tasks')
    schedule.every(int(config.schedule)).seconds.do(scheduled_task)

    # loop and run scheduled tasks
    while 1:
        schedule.run_pending()
        time.sleep(1)



if __name__ == '__main__':
    try:
        main()
    except Exception as err:
        logger.error(err)
        traceback.print_exc()