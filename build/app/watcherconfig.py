#!/usr/bin/env python3
"""
    parse configuration for script.
    the whole config is done via env variables
"""

import os
from vault import Vault

class WatcherConfig(object):

    def __init__(self):
        """
            initialize and check configuration
        """
        # rancher api service
        self.rancher_api_url=os.getenv('WATCHER_RANCHER_API_URL','')
        self.rancher_api_key=os.getenv('WATCHER_RANCHER_API_KEY','')
        self.rancher_api_secret=os.getenv('WATCHER_RANCHER_API_SECRET','')

        # approle key and secret id for vault
        self.vault_server=os.getenv('WATCHER_VAULT_SERVER','')
        self.vault_role_id=os.getenv('WATCHER_VAULT_ROLE_ID','')
        self.vault_secret_id=os.getenv('WATCHER_VAULT_SECRET_ID','')

        # if all three values are specified we try to load the credentials for the
        # rancher api and the mikrotik firewall from the vault
        if self.vault_server and self.vault_role_id and self.vault_secret_id:
            try:
                # load the vault
                vault = Vault(self.vault_server, role_id=self.vault_role_id, secret_id=self.vault_secret_id)
                vault.request_access_token()

                # now load the different config values (if they exist)
                try:
                    self.rancher_api_key = vault.retrieve_secret('rancher/api/home/watcher','key')
                except:
                    pass
                try:
                    self.rancher_api_secret = vault.retrieve_secret('rancher/api/home/watcher','secret')
                except:
                    pass
            except:
                pass

        # if no rancher api config was given raise an error
        if not self.rancher_api_url or not self.rancher_api_key or not self.rancher_api_secret:
            raise Exception('Invalid Rancher Configuration')

        # docker labels for config

        # whats the container label which activates or disables the watching of ip changes
        self.docker_label_enable=os.getenv('WATCHER_DOCKER_LABEL_ENABLE','cloud.hutter.watcher.ip.enable')
        # comma separated list of services of which the containers need to be rebooted if the ip of
        # the monitored container changes
        self.docker_label_reboot=os.getenv('WATCHER_DOCKER_LABEL_REBOOT','cloud.hutter.watcher.ip.reboot')

        # etcd configuration
        self.etcd_host=os.getenv('WATCHER_ETCD_HOST','etcd.hutter.local')
        self.etcd_port=os.getenv('WATCHER_ETCD_PORT','2379')

        # loglevel
        self.loglevel = os.getenv('WATCHER_LOGLEVEL','info')

        # time in seconds between runs
        self.schedule = os.getenv('WATCHER_SCHEDULE','60')