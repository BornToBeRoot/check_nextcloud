#!/usr/bin/python
import urllib2, base64, xml.etree.ElementTree, sys, traceback

# Some helper functions
def calc_size_suffix(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)

        num /= 1024.0

    return "%.1f%s%s" % (num, 'Yi', suffix)

def calc_size_nagios(num, suffix='B'):
	for unit in ['','K','M','G','T','P','E','Z']:
		if abs(num) < 1000.0:
			return "%3.1f%s%s" % (num, unit, suffix)

		num /= 1000.0

	return "%.1f%s%s" % (num, 'Y', suffix)

# Command line parser
from optparse import OptionParser

parser = OptionParser(usage='%prog -u username -p password -H cloud.example.com -c [system|storage|shares|webserver|php|database|activeUsers|uploadFilesize]')
parser.add_option('-v', '--version', dest='version', default=False, action='store_true', help='Print the version of this script')
parser.add_option('-u', '--username', dest='username', type='string', help='Username of the user with administrative permissions on the nextcloud server')
parser.add_option('-p', '--password', dest='password', type='string', help='Password of the user')
parser.add_option('-H', '--hostname', dest='hostname', type='string', help='Nextcloud server address (make sure that the address is a trusted domain in the config.php)')
parser.add_option('-c', '--check', dest='check', choices=['system','storage','shares','webserver','php','database','activeUsers','uploadFilesize'], help='The thing you want to check [system|storage|shares|webserver|php|database|activeUsers|uploadFilesize]')
parser.add_option('--upload-filesize', dest='upload_filesize', default='512.0MiB', help='Filesize in MiB, GiB without spaces (default="512.0GiB")')
parser.add_option('--protocol', dest='protocol', choices=['https', 'http'], default='https', help='Protocol you want to use [http|https] (default="https")')
parser.add_option('--ignore-proxy', dest='ignore_proxy', default=False, action='store_true', help='Ignore any configured proxy server on this system for this request')
parser.add_option('--api-url', dest='api_url', type='string', default='/ocs/v2.php/apps/serverinfo/api/v1/info', help='Url of the api (default="/ocs/v2.php/apps/serverinfo/api/v1/info")')

(options, args) = parser.parse_args()

# Print the version of this script
if options.version:
	print 'Version 1.1'
	sys.exit(0)

# Validate the user input...
if not options.username and not options.password and not options.hostname and not options.check:
	parser.print_help()
	sys.exit(3)

if not options.username:
	parser.error('Username is required, use parameter [-u|--username].')
	sys.exit(3)

if not options.password:
	parser.error('Password is required, use parameter [-p|--password].')
	sys.exit(3)

if not options.hostname:
	parser.error('Hostname is required, use parameter [-H|--hostname]')
	sys.exit(3)

if not options.check:
	parser.error('Check is required, use parameter [-c|--check]')
	sys.exit(3)

# Re-validate the hostname given by the user (make sure they dont entered a "https://", "http://" or "/")
hostname = options.hostname.lstrip('[https|http]://').split('/')[0]

# Re-validate the api_url
if options.api_url.startswith('/'):
	api_url = options.api_url
else:
	api_url = '/{0}'.format(options.api_url)

# Create the url to access the api
url = '{0}://{1}{2}'.format(options.protocol, hostname, api_url)

# Encode credentials as base64
credential = base64.b64encode(options.username + ':' + options.password)

try:
	# Create the request
	request = urllib2.Request(url)

	# Add the authentication and api request header
	request.add_header('Authorization', "Basic %s" % credential)
	request.add_header('OCS-APIRequest','true')
	
	# Proxy handler
	if(options.ignore_proxy):
		proxy_handler = urllib2.ProxyHandler({})
		opener = urllib2.build_opener(proxy_handler)

		response = opener.open(request)
	else:
		response = urllib2.urlopen(request)

	# Read the content
	content = response.read()

except urllib2.HTTPError as error:      # User is not authorized (401)
	print 'UNKOWN - [WEBREQUEST] {0} {1}'.format(error.code, error.reason)
	sys.exit(3)

except urllib2.URLError as error:	# Connection has timed out (wrong url / server down)
	print 'UNKOWN - [WEBREQUEST] {0}'.format(str(error.reason).split(']')[0].strip())
	sys.exit(3)

try:
	# Convert the webrequest response to xml
	xml_root = xml.etree.ElementTree.fromstring(content)
except xml.etree.ElementTree.ParseError:
	print 'UNKOWN - [XML] Content contains no or wrong xml data... check the url and if the api is reachable!'
	sys.exit(3)

# Check if the xml is valid and the api gives usefull informations
try:
	# Get the meta informations
	xml_meta = xml_root.find('meta')

	xml_meta_status = str(xml_meta.find('status').text)
	xml_meta_statuscode = int(xml_meta.find('statuscode').text)
	xml_meta_message = str(xml_meta.find('message').text)

	# Check the meta informations
	if not (xml_meta_status == 'ok' and xml_meta_statuscode == 200 and xml_meta_message == 'OK'):
		print 'UNKOWN - [API] invalid meta data... status: {0}, statuscode: {1}, message: {2}'.format(xml_meta_status, xml_meta_statuscode, xml_meta_message)
		sys.exit(3)

except AttributeError:
	print 'UNKOWN - [XML] Content contains no or wrong xml data... check the url and if the api is reachable!'
	sys.exit(3)

# Get the nextcloud version... other informations about the system like RAM/CPU/DISK are nagios/centreon own checks - so we don't need them here...
if options.check == 'system':
	xml_system = xml_root.find('data').find('nextcloud').find('system')

	xml_system_version = str(xml_system.find('version').text) 

	print 'OK - Nextcloud version: {0}'.format(xml_system_version)
	sys.exit(0)

# Get informations about the storage
if options.check == 'storage':
	xml_storage = xml_root.find('data').find('nextcloud').find('storage')

	xml_storage_users = int(xml_storage.find('num_users').text)
	xml_storage_files = int(xml_storage.find('num_files').text)
	xml_storage_storages = int(xml_storage.find('num_storages').text)
	xml_storage_storages_local = int(xml_storage.find('num_storages_local').text)
	xml_storage_storages_home = int(xml_storage.find('num_storages_home').text)
	xml_storage_storages_other = int(xml_storage.find('num_storages_other').text)

	print 'OK - Users: {0}, files: {1}, storages: {2}, storages local: {3}, storages home: {4}, storages other: {5} | users={0}, files={1}, storages={2}, storages_local={3}, storages_home={4}, storage_other={5}'.format(xml_storage_users, xml_storage_files, xml_storage_storages, xml_storage_storages_local, xml_storage_storages_home, xml_storage_storages_other)
	sys.exit(0)

# Get informations about the shares
if options.check == 'shares':
	xml_shares = xml_root.find('data').find('nextcloud').find('shares')

	xml_shares_shares = int(xml_shares.find('num_shares').text)
	xml_shares_shares_user = int(xml_shares.find('num_shares_user').text)
	xml_shares_shares_groups = int(xml_shares.find('num_shares_groups').text)
	xml_shares_shares_link = int(xml_shares.find('num_shares_link').text)
	xml_shares_shares_link_no_password = int(xml_shares.find('num_shares_link_no_password').text)
	xml_shares_fed_shares_sent = int(xml_shares.find('num_fed_shares_sent').text)
	xml_shares_fed_shares_received = int(xml_shares.find('num_fed_shares_received').text)

	print 'OK - Shares: {0}, shares user: {1}, shares groups: {2}, shares link: {3}, shares link no password: {4}, shares federation sent: {5}, shares federation received: {6} | shares={0}, shares_user={1}, shares_groups={2}, shares_link={3}, shares_link_no_password={4}, federation_shares_sent={5}, federation_shares_received={6}'.format(xml_shares_shares, xml_shares_shares_user, xml_shares_shares_groups, xml_shares_shares_link, xml_shares_shares_link_no_password, xml_shares_fed_shares_sent, xml_shares_fed_shares_received)
	sys.exit(0)

# Get informations about the webserver
if options.check == 'webserver':
	xml_webserver = str(xml_root.find('data').find('server').find('webserver').text)

	print 'OK - Webserver: {0}'.format(xml_webserver)
	sys.exit(0)

# Get informations about php
if options.check == 'php':
	xml_php = xml_root.find('data').find('server').find('php')

	xml_php_version = str(xml_php.find('version').text)
	xml_php_memory_limit = int(xml_php.find('memory_limit').text)
	xml_php_max_execution_time = str(xml_php.find('max_execution_time').text)
	xml_php_upload_max_filesize = int(xml_php.find('upload_max_filesize').text)

	print 'OK - PHP version: {0}, memory limit {1}, max execution time: {2}s, upload max filesize: {3}'.format(xml_php_version, calc_size_suffix(xml_php_memory_limit), xml_php_max_execution_time, calc_size_suffix(xml_php_upload_max_filesize))
	sys.exit(0)

# Get informations about the database
if options.check == 'database':
	xml_database = xml_root.find('data').find('server').find('database')

	xml_database_type = str(xml_database.find('type').text)
	xml_database_version = str(xml_database.find('version').text)
	xml_database_size = float(xml_database.find('size').text)

	print 'OK - Database: {0}, version {1}, size: {2} | database_size={3}'.format(xml_database_type, xml_database_version, calc_size_suffix(xml_database_size), calc_size_nagios(xml_database_size))
	sys.exit(0)

# Check the active users
if options.check == 'activeUsers':
	xml_activeUsers = xml_root.find('data').find('activeUsers')

	xml_activeUsers_last5minutes = int(xml_activeUsers.find('last5minutes').text)
	xml_activeUsers_last1hour = int(xml_activeUsers.find('last1hour').text)
	xml_activeUsers_last24hours = int(xml_activeUsers.find('last24hours').text)

	print 'OK - Last 5 minutes: {0} user(s), last 1 hour: {1} user(s), last 24 hour: {2} user(s) | users_last_5_minutes={0}, users_last_1_hour={1}, users_last_24_hours={2}'.format(xml_activeUsers_last5minutes, xml_activeUsers_last1hour, xml_activeUsers_last24hours)
	sys.exit(0)

if options.check == 'uploadFilesize':
	xml_php = xml_root.find('data').find('server').find('php')
	
	# Get upload max filesize
	xml_php_upload_max_filesize = int(xml_php.find('upload_max_filesize').text)

	# Convert
	upload_max_filesize = calc_size_suffix(xml_php_upload_max_filesize)

	if options.upload_filesize == upload_max_filesize:
		print 'OK - Upload max filesize: {0}'.format(upload_max_filesize)
		sys.exit(0)		
	else:
		print 'CRITICAL - Upload max filesize is set to {0}, but should be {1}'.format(upload_max_filesize, options.upload_filesize)
		sys.exit(2)