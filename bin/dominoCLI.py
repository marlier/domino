#!/usr/bin/env python
# this is a simple command line utility for Domino. Its designed to use via text messages.

import os
import sys
import logging
from optparse import OptionParser

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(-1, cmd_folder)
     sys.path.insert(-1, cmd_folder + "/classes")

import user_layer as User
import team_layer as Team
import alert_layer as Alert
import util_layer as Util

conf = Util.load_conf()

Util.init_logging("client")

def alert():
	'''
	This function handles the rest of the command as it pertains to an alert(s).
	'''
	# Parse the command line
	parser = OptionParser()
	parser.add_option('-i', '--id', dest='id', help='Alert id', type='int', default=0)
	parser.add_option('-t', '--team', dest='team', help='The team you want to send the message to', type='string', default='default')
	parser.add_option('-f', '--from', dest='_from', help='The phone number of the person using domino (for sms identication purposes)', type='string', default='')
	parser.add_option('-a', '--ack', dest='ack', help='Ack the results of alert list query', action="store_true", default=False)
	parser.add_option('-m', '--mobile', dest='mobile', help='Flag as mobile device, format output for it.', action="store_true", default=False)
	(opts, args) = parser.parse_args()
	
	user_usage='''
domino-cli.py alert status -t <team> -a
domino-cli.py alert ack -i <id> -f <phone number>
	'''

	if (len(sys.argv) > 2) and sys.argv[2] in ['status', 'ack']:
		mode = sys.argv[2]
		if mode == "status": o = alert_status(opts)
		if mode == "ack": o = alert_ack(opts)
		return o
	else:
		return user_usage

def alert_status(opts):
	'''
	Printing out alerts that haven't been acked. If -a is given, will ack them.
	'''
	user = None
	if len(opts.team) > 0:
		alerts = Alert.active(opts.team)
	else:
		alerts = Alert.active()
	if len(alerts) == 0: return "No active alerts."
	if opts.ack == True:
		if opts._from == '':
			return "Must use option -f to ack alerts"
		else:
			user = User.get_user_by_phone(opts._from)
			output = "Acking alerts as %s...\n" % (u.name)
	else:
		output = ''
	for a in alerts:
		output=output + "%s" % (a.print_alert(opts.mobile))
		if user != None: a.ack_alert(user)
	return output

def alert_ack(opts):
	'''
	Acking a specific alert. Assumes the last alert to be sent to user if not given.
	'''
	user = None
	if opts._from == '': return "Must use option -f for identification."
	user = User.get_user_by_phone(opts._from)
	if user == False: return "No user ends with that phone number (-f)"
	output = "Acking alerts as %s...\n" % (user.name)
	if opts.id > 0:
		alert = Alert.Alert(opts.id)
		alert.ack_alert(user)
		return "Acknowledged"
	if user.lastAlert > 0:
		alert = Alert.Alert(user.lastAlert)
		alert.ack_alert(user)
		return "Acknowledged"
	else:
		return "No alert associated with your user"

def oncall():
	# Parse the command line
	parser = OptionParser()
	parser.add_option('-t', '--team', dest='team', help='A team name', type='string', default='default')
	parser.add_option('-f', '--from', dest='_from', help='The phone number of the person using Domino (for sms identication purposes)', type='string', default='')
	parser.add_option('-m', '--mobile', dest='mobile', help='Flag as mobile device, format output for it.', action="store_true", default=False)
	(opts, args) = parser.parse_args()
	
	user_usage='''
domino-cli.py oncall -t <team>
	'''
	
	if (len(sys.argv) > 2) and sys.argv[1] in ['oncall']:
		mode = sys.argv[2]
		o = oncall_status(opts)
		return o
	else:
		return user_usage

def oncall_status(opts):
	'''
	Get a list of people oncall for a specific team
	'''
	if len(opts.team) > 0:
		team = Team.get_team_by_name(opts.team)
		users = team.on_call()
	else:
		return "No team specified (-t)."
	output = ''
	if len(users) == 0:
		return "No one is on call on the %s team." % (opts.team)
	else:
		team = Team.get_team_by_name(opts.team)[0]
		output = output + "Team: %s (%s)\n" % (team.name, team.phone)
		for u in users:
			output = output + u.print_user(opts.mobile)
	oncall_users = []
	return output

def run(args):
	'''
	This gets run from domino-server to execute the Domino CLI
	'''
	# convert argsuments into input params
	sys.argv = args.split()
	# gotta pad the arguments because usually sys.argv[0] is the python file name
	sys.argv.insert(0, 'spacer')
	return main()

def main():
	usage = '''
domino-cli.py alert status -t <team> -a
domino-cli.py alert ack -i <id> -f <phone number>

domino-cli.py oncall -t <team>
'''

	# converting all parameters to be lowercase to remove any case sensitivity
	sys.argv = map(lambda x:x.lower(),sys.argv)

	if (len(sys.argv) > 1) and sys.argv[1] in ['status', 'alert', 'alerts', 'ack', 'oncall']:
		mode = sys.argv[1]
		if mode == "user" or mode == 'users': o = user()
		if mode == "alert" or mode == 'alerts': o = alert()
		if mode == "status":
			sys.argv.insert(1, "alert")
			o = alert()
		if mode == "ack": 
			sys.argv.insert(1, "alert")
			o = alert()
		if mode == "oncall": o = oncall()
		#if mode == "rotation": o = rotation()
		logging.info("Oncall.py output: %s" % o)
		return o
	else:
		return usage

if __name__ == "__main__": print main()
