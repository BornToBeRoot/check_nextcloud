# check_nextcloud.py

Nagios/Centreon plugin for nextcloud serverinfo API (https://github.com/nextcloud/serverinfo)

## Syntax / Help

```
./check_nextcloud.py -u username -p password -H cloud.example.com -c [system|storage|shares|webserver|php|database|users]


Options:
  -h, --help            show this help message and exit
  -v, --version         Print the version of this script
  -u USERNAME, --username=USERNAME
                        Username of the user with administrative permissions
                        on the nextcloud server
  -p PASSWORD, --password=PASSWORD
                        Password of the user
  -H HOSTNAME, --hostname=HOSTNAME
                        Nextcloud server address (make sure that the address
                        is a trusted domain in the config.php)
  -c CHECK, --check=CHECK
                        The thing you want to check
                        [system|storage|shares|webserver|php|database|users]
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
  `$USER1$/plugins_custom/check_nextcloud.py -u $_HOSTCLOUDUSER$ -p $_HOSTCLOUDPWD$ -H $HOSTNAME$ -c $ARG1$ --ignore-proxy`
* Create a service for each thing you want to check (system, storage, etc.) and link it to your host(s)
* Add the credentials of your nextcloud admin user as custom macro (CLOUDUSER, COUDPWD) to your host.

## Example 1

```
./check_nextcloud.py -u adminUser -p secretPassword -H cloud.example.com -c system --ignore-proxy

OK - Nextcloud version: 12.0.3.3
```

## Example 2

```
./check_nextcloud.py -u adminUser -p secretPassword -H cloud.example.com -c users --ignore-proxy

OK - Last 5 minutes: 3 user(s), last 1 hour: 10 user(s), last 24 hour: 44 user(s) | users_last_5_minutes=3, users_last_1_hour=10, users_last_24_hours=44
```

This will return a status message and create a graph based on the performance data.
