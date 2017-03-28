#!/usr/bin/env python
import requests
import logging
import time

# initialize the logger object
logger = logging.getLogger(__name__)

class RancherApi (object):
    """
    simple rancher metadata client to get information
    to running services, hosts and containers from the
    rancher metadata service
    """

    def __init__(self, rancher_api_url, rancher_api_key, rancher_api_secret):
        """
            initialize rancher metadata client
        """
        self.api_url = rancher_api_url
        self.api_key = rancher_api_key
        self.api_secret = rancher_api_secret
        self.headers = {'Accept':'application/json'}

        self.containers_url = self.api_url + "/containers"
        self.services_url = self.api_url + "/services"
        self.hosts_url = self.api_url + "/hosts"

        r = requests.get(self.api_url, headers=self.headers, auth=requests.auth.HTTPBasicAuth(self.api_key, self.api_secret))
        r.raise_for_status()

    def get_containers(self, state=None, name=None):
        """
            get a list of all containers known to the rancher service
        """
        url = self.containers_url + "?"

        if state:
            url = url + "&state={}".format(state)
        if name:
            url = url + "&name={}".format(name)

        r = requests.get(url, headers=self.headers, auth=requests.auth.HTTPBasicAuth(self.api_key, self.api_secret))
        r.raise_for_status()
        json = r.json()['data']
        return json

    def get_services(self):
        """
            get a list of all services known to the rancher service
        """
        r = requests.get(self.services_url, headers=self.headers, auth=requests.auth.HTTPBasicAuth(self.api_key, self.api_secret))
        r.raise_for_status()
        json = r.json()['data']
        return json

    def get_hosts(self):
        """
            get a list of all rancher hosts
        """
        r = requests.get(self.hosts_url, headers=self.headers, auth=requests.auth.HTTPBasicAuth(self.api_key, self.api_secret))
        r.raise_for_status()
        json = r.json()['data']
        return json

    def get_containers_with_label(self, label, state=None, labelvalue=None, container_id=None):
        """
            get containers filtered by label
            if a container id is set it will only containers having the label and
            having the container id
        """
        containers = []
        for c in self.get_containers(state=state):
            if label in c['labels']:
                if labelvalue:
                    if c['labels'][label] != labelvalue:
                        continue
                if not container_id:
                    containers.append(c)
                else:
                    if container_id == c['external_id']:
                        containers.append(c)
                        break
        return containers

    def get_host_of_container(self, container_id):
        """
            returns a dict with information to the docker host
            the speficied container is running on
        """
        host = {}
        for h in self.get_hosts():
            if container_id in h['instanceIds']:
                host = h
                break

        return host

    def restart_container(self, container_id):
        """
            restarts a container
        """
        logger.info("Rebooting container with id {}".format(container_id))
        r = requests.get(self.containers_url + "/" + container_id, headers=self.headers, auth=requests.auth.HTTPBasicAuth(self.api_key, self.api_secret))
        r.raise_for_status()
        try:
            # restart the container
            restart_url = r.json()['actions']['restart']
            logger.debug("Execute reboot action with '{}'".format(restart_url))
            r = requests.post(restart_url, headers=self.headers, auth=requests.auth.HTTPBasicAuth(self.api_key, self.api_secret))
            self.wait_for_container(container_id, 'running')
        except:
            raise

    def wait_for_container(self, container_id, state):
        """
            waits until the specified container is in the specified state
        """
        logger.info("Waiting for container '{}' to go into state '{}'".format(container_id,state))
        current_state = None

        while current_state != state:
            r = requests.get(self.containers_url + "/" + container_id, headers=self.headers, auth=requests.auth.HTTPBasicAuth(self.api_key, self.api_secret))
            current_state = r.json()['state']
            logger.debug("Still waiting for container")
            time.sleep(1)

