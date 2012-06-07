#!/usr/bin/env python

import sys, os, select, urllib, urllib2
from optparse import OptionParser
import simplejson as json
from ConfigParser import SafeConfigParser
import ast, logging

version="Raven 0.01"

# Parse the command line
parser = OptionParser()
parser.add_option('-m', '--message', dest='message', help='The message of the alert', type='string', default=None)
parser.add_option('-t', '--teams', dest='teams', help='The teams you want to send the message to (comma separated)', type='string', default=None)
parser.add_option('-H', '--host', dest='host', help='Hostname', type='string', default=None)
parser.add_option('-v', '--service', dest='service', help='Service name', type='string', default=None)
parser.add_option('-e', '--environment', dest='environment', help='Environment (ie Production, QA, Staging)', type='string', default=None)
parser.add_option('-d', '--colo', dest='colo', help='Colo or datacenter name', type='string', default=None)
parser.add_option('-s', '--status', dest='status', help='Alert status. 0=OK, 1=Warning, 2=Critical, 3=Unknown', type='int', default=None)
parser.add_option('-P', '--position', dest='position', help='Position. 0=No Alert, 1=email only, 2=paging, 3=paging with no acknowledgment required', type='int', default=None)
parser.add_option('-T', '--tags', dest='tags', help='Tags. A comma separated list of "tags" or "cagetories" this alert is associated', type='string', default=None)
parser.add_option('-z', '--server', dest='server', help='Domino Server address', type='string', default=None)
parser.add_option('-p', '--port', dest='port', help='Domino Port', type='int', default=None)
parser.add_option('-c', '--config', dest='config', help='Raven config file (required)', type='string', default=None)
parser.add_option('-V', '--version', dest='version', help='Print version number', action="store_true")
(opts, args) = parser.parse_args()

# print version number and exit
if opts.version == True:
	print version
	sys.exit(0)

# check for config file
if opts.config == None:
	print "Error: No config file passed (-c)"
	sys.exit(1)	

#load conf
parser = SafeConfigParser()
parser.read(opts.config)
conf={}
#take in all keys and values from the conf file into the variable "conf"
for section_name in parser.sections():
	for name, value in parser.items(section_name):
		conf[name] = value

# converting these from strings to dict
def convert_to_dict(var):
	'''
	Converts a string (input) to a dictionary (output)
	'''
	try:
		var = ast.literal_eval(var)
		return var
	except:
		# check if value is a single word, in which case, assume as default
		if len(var.split()) == 1:
			var={'default':var}
			return var
		else:
			logging.critical("Bad configuration variable: %s" % (var))
			raise "Bad configuration variable: %s" % (var)

conf['port']=int(conf['port'])
conf['aliases']=convert_to_dict(conf['aliases'])

if not os.path.exists('%s/%s.log' % (conf['logdir'], 'raven')):
	os.makedirs(conf['logdir'])
	f = file('%s/%s.log' % (conf['logdir'], 'raven'), "w+")
	f.close()

#init logging
logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename='%s/%s.log' % (conf['logdir'], 'raven'),level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

# set default values
if select.select([sys.stdin,],[],[],0.0)[0]:
	opts.message = sys.stdin.read()
if opts.message == None:
	print "Error: No message passed. This can be done via stdin or --message (-m)"
	sys.exit(1)
if opts.teams in conf['aliases']: opts.teams=conf['aliases'][opts.teams]
if opts.teams == None: opts.teams=conf['teams']
if opts.host == None: opts.host=conf['host']
if opts.service == None: opts.service=conf['service']
if opts.environment == None: opts.environment=conf['environment']
if opts.colo == None: opts.colo=conf['colo']
if opts.status == None: opts.status=conf['status']
if opts.position == None: opts.position=conf['position']
if opts.tags == None: opts.tags=conf['tags']
if opts.server == None: opts.server=conf['server']
if opts.port == None: opts.port=conf['port']

summary='''Sending a raven: 
    Environment: %s
    Colo: %s
    Host: %s
    Service: %s
    Teams: %s
    Status: %s
    Position: %s
    Tags: %s
    Server: %s
    Port: %s
    Message: %s''' % (opts.environment, opts.colo, opts.host, opts.service, opts.teams, opts.status, opts.position, opts.tags, opts.server, opts.port, opts.message)

logging.info(summary)

# create encoded url query
if opts.host.startswith('http'):
	query='%s:%i/api/create?target=alerts&message=%s&teams=%s&host=%s&service=%s&environment=%s&colo=%s&status=%s&position=%s&tags=%s' % (opts.server, opts.port,urllib.quote_plus(opts.message),urllib.quote_plus(opts.teams),urllib.quote_plus(opts.host),urllib.quote_plus(opts.service),urllib.quote_plus(opts.environment),urllib.quote_plus(opts.colo),opts.status,opts.position,urllib.quote_plus(opts.tags))
else:
	query='http://%s:%i/api/create?target=alerts&message=%s&teams=%s&host=%s&service=%s&environment=%s&colo=%s&status=%s&position=%s&tags=%s' % (opts.server, opts.port,urllib.quote_plus(opts.message),urllib.quote_plus(opts.teams),urllib.quote_plus(opts.host),urllib.quote_plus(opts.service),urllib.quote_plus(opts.environment),urllib.quote_plus(opts.colo),opts.status,opts.position,urllib.quote_plus(opts.tags))

try:
	# query the server
	req = urllib2.Request(query)
	response = urllib2.urlopen(req)
	rawreturn = response.read()
except urllib2.URLError, e:
	print e
	if e.reason[0] == 61:
		print "Unable to contact server. Check that the service is running on the server and you are inputting the correct host (-H) and port (-p)"
	else:
		print e
	sys.exit(1)

ret = json.loads(rawreturn)

if ret['status'] % 100 == 0:
	print "Successfully sent message: %s" % (ret['status_message'])
	sys.exit(0)
else:
	print "Failed to send message: %s" % (ret['status_message'])
	sys.exit(1)
