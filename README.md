# Nagios/Centron check | Nextcloud serverinfo

Nagios/Centreon plugin for nextcloud serverinfo API (https://github.com/nextcloud/serverinfo)

This branch contains the check for Python 3. A version for Python 2.7 can be found [here](https://github.com/BornToBeRoot/check_nextcloud/tree/stable-python2.7).

## Syntax / Help

```
./check_nextcloud.py -u username -p password -H cloud.example.com -c [system|storage|shares|webserver|php|database|users|apps]


Options:
  -h, --help            show this help message and exit
  -v, --version         Print the version of this script
  -u USERNAME, --username=USERNAME
                        Username of the user with administrative permissions
                        on the nextcloud server
  -p PASSWORD, --password=PASSWORD
                        Password of the user
  -t TOKEN, --nc-token=TOKEN
                        NC-Token for the Serverinfo API
  -H HOSTNAME, --hostname=HOSTNAME
                        Nextcloud server address (make sure that the address
                        is a trusted domain in the config.php)
  -c CHECK, --check=CHECK
                        The thing you want to check
                        [system|storage|shares|webserver|php|database|activeUsers|uploadFilesize|apps]
  --upload-filesize     Filesize in MiB, GiB without spaces (default="512.0GiB")
  --protocol=PROTOCOL   Protocol you want to use [http|https]
                        (default="https")
  --ignore-proxy        Ignore any configured proxy server on this system for
                        this request
  --api-url=API_URL     Url of the api
                        (default="/ocs/v2.php/apps/serverinfo/api/v1/info")

```

## Install

* Copy the check (python script) in your nagios/centreon plugins folder
* Create a check with the following command line:
  ```
  $USER1$/plugins_custom/check_nextcloud.py -u $_HOSTCLOUDUSER$ -p $_HOSTCLOUDPWD$ -H $HOSTNAME$ -c $ARG1$ --ignore-proxy
  ```
  or for the check: `uploadFilesize`
  ```
  $USER1$/plugins_custom/check_nextcloud.py -u $_HOSTCLOUDUSER$ -p $_HOSTCLOUDPWD$ -H $HOSTNAME$ -c $ARG1$ --upload-filesize=$ARG2$ --ignore-proxy
  ```
* Create a service for each thing you want to check (system, storage, etc.) and link it to your host(s)
* Add the credentials of your nextcloud admin user as custom macro (CLOUDUSER, COUDPWD) to your host.

## Example 1

```
./check_nextcloud.py -u adminUser -p secretPassword -H cloud.example.com -c system --ignore-proxy

OK - Nextcloud version: 12.0.3.3
```

## Example 2

```
./check_nextcloud.py -u adminUser -p secretPassword -H cloud.example.com -c activeUsers --ignore-proxy

OK - Last 5 minutes: 3 user(s), last 1 hour: 10 user(s), last 24 hour: 44 user(s) | users_last_5_minutes=3, users_last_1_hour=10, users_last_24_hours=44
```

This will return a status message and create a graph based on the performance data.

## Example 3

```
./check_nextcloud.py -u adminUser -p secretPassword -H cloud.example.com -c uploadFilesize --upload-filesize=2.0GiB --ignore-proxy

OK - Upload max filesize: 2.0GiB

# Or, when changed after an update...

CRITICAL - Upload max filesize is set to 512.0MiB, but should be 2.0GiB

```



## Icinga config example


Adjust the command path to your local situation.

```
object CheckCommand "check_nextcloud" {
  command = [ "/var/lib/nagios/src/check_nextcloud/check/check_nextcloud.py" ]
  arguments = {
    "--nc-token" = {
      value = "$nextcloud_token$"
      description = "NC-Token for the Serverinfo API"
    }
    "--hostname" = {
      value = "$nextcloud_hostname$"
      description = "Hostname"
    }
    "--api-url" = {
      value = "$nextcloud_api_url$"
      description = "Api-url"
    }
    "--check" = {
      value = "$nextcloud_check$"
      description = "Which check to run"
    }
    "--perfdata-format" = {
      value = "nagios"
      description = "The perfdata format we like"
    }
  }
}
```

```
apply Service for (checkname in ["system","storage","shares","webserver","php","database","activeUsers","uploadFilesize","apps"]) {
  import "generic-service"
  name = "check-nextcloud-" + checkname
  check_interval = 30m
  retry_interval = 10m
  display_name = "Nextcloud monitor " + checkname
  vars.notification_interval = 1d

  vars.nextcloud_check = checkname
  vars.nextcloud_hostname = host.vars.nextcloud_hostname
  vars.nextcloud_token = host.vars.nextcloud_token
  vars.nextcloud_api_url = host.vars.nextcloud_api_url
  vars.notification["mail"] = {  }
  check_command = "check_nextcloud"

  assign where (host.address || host.address6) && host.vars.nextcloud_token
}
```

```
object Host "server42.example.com" {

  display_name = "My Nextcloud server"
  address = "<IP>"

  ...

  # The token can be set with: occ config:app:set serverinfo token --value yourtoken
  vars.nextcloud_token = "XXX"
  vars.nextcloud_hostname = "nextcloud.example.com"

  # Optional if you e.g. use a subdirectory.
  vars.nextcloud_api_url = "/subdir/ocs/v2.php/apps/serverinfo/api/v1/info"
}

```
