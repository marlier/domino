#!/usr/bin/env python
# load configuraiton of Domino
# init logging
# send tracebacks to a log file
# run a healthcheck on the system

from ConfigParser import SafeConfigParser
import sys, traceback, os
import logging

def init_logging(log_file_name = 'server'):
	'''
	Loads logging with a file destination
	var log_file_name is the file name without a file extension
	'''
	conf = load_conf()
	# create log directory if it doesn't already exist
	if not os.path.exists(conf['logdir']):
	    os.makedirs(conf['logdir'])
	logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s', filename='%s/%s.log' % (conf['logdir'], log_file_name),level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')

def load_conf(config_file = '/opt/domino/domino.conf'):
	'''
	This function loads the conf file into the program's memory
	'''
	parser = SafeConfigParser()
	parser.read(config_file)
	conf={}
	#take in all keys and values from the conf file into the variable "conf"
	for section_name in parser.sections():
		for name, value in parser.items(section_name):
			conf[name] = value
	# making sure a mysql password is set
	if 'mysql_passwd' not in conf:
		conf['mysql_passwd'] = ''
	
	# converting strings to integers
	conf['alert_interval']=int(conf['alert_interval'])
	conf['alert_escalation']=int(conf['alert_escalation'])
	conf['api_port']=int(conf['api_port'])
	conf['port']=int(conf['port'])
	conf['call_failover']=int(conf['call_failover'])
	conf['mysql_port']=int(conf['mysql_port'])
	conf['email_port']=int(conf['email_port'])
	return conf
	
def strace(e):
	conf = load_conf()
	logging.error(e.__str__())
	import notification as Notification
	if conf['loglevel'] == 'DEBUG': traceback.print_exc(file=open('%s/strace.out' % (conf['logdir']), "a"))
	newNotification = Notification.Notification()
	newNotification.noteType = "error"
	newNotification.alert = 0
    # character escape any double quotes so mysql won't vomit
	newNotification.message = e.__str__().replace('"', '\\"')
	newNotification.tags = ''
	newNotification.status = 2
	newNotification.link = ""
	newNotification.save()

def healthcheck(healthtype):
	'''
	This checks the system to see if capable of handling api requests
	'''
	logging.info("Initiating a healcheck of the system.")
	try:
		checks = {}
		if healthtype == "comm" or healthtype == "alert":
			import mysql as Mysql
			db_conn = Mysql.Database()
			dbcheck = db_conn.healthcheck()
			checks['Database'] = dbcheck
		
		if healthtype == "comm":
			import email as Email
			email = Email.Email()
			emailcheck = email.healthcheck()
			checks['Email'] = emailcheck
		
		if healthtype == "comm":
			import domino_twilio as Twilio
			twiliocheck = Twilio.healthcheck()
			checks['Twilio'] = twiliocheck

		failed = []
		for k,v in checks.items():
			if checks[k] == False:
				failed.append(k)
			
		if len(failed) > 0:
			return "One or more health checks failed (%s). Check the logs for more information.\n" % (', '.join(failed))
		else:
			return "OK\n"
	except Exception, e:
		strace(e)
		return "Failed to run all healthchecks.\n"
