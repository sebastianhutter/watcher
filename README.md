# watcher

simple python app to monitor ip changes of containers and reboot certain containers.

## labels


-watch for changes of the ip address
```cloud.hutter.watcher.ip.enabled: true```
-last known primary ip of c
```cloud.hutter.watcher.ip.last_known: ip```
-comma separated list of containers to reboot when the ip changes
```cloud.hutter.watcher.ip.onchange.reboot```