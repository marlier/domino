#!/usr/bin/env python
# this is a service that listens for traffic from Twilio's servers

import web
import os, sys
import urllib
import logging
import time
from multiprocessing import Process

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(-1, cmd_folder)
     sys.path.insert(-1, cmd_folder + "/classes")


import twilio_layer as Twilio
import dominoCLI as domino
import user_layer as User
import alert_layer as Alert
import team_layer as Team
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("server")

# set port and IP to listen for alerts
# these are inhereited from the conf file
sys.argv = [conf['listen_ip'],conf['port']]

# debug mode
web.config.debug = conf['server_debug']

#load valid urls to listen to for http calls
urls = (
    '/sms/(.+)', 'sms',
    '/call/(.+)', 'call',
    '/healthcheck/(.+)', 'healthcheck',
)
app = web.application(urls, globals())

class healthcheck:
	'''
	This checks the system to see if capable of handling api requests
	'''
	def GET(self):
		return Util.healthcheck()
	def POST(self):
		return Util.healthcheck()


class sms:
	'''
	This class handles SMS messages
	'''
	def POST(self,name):
		d = web.input()
		logging.info("Receiving SMS message\n%s" % (d))
		# incoming text message, handle it
		web.header('Content-Type', 'text/xml')
		r = Twilio.twiml.Response()
		user = User.get_user_by_phone(d.From)
		# make sure person sending the text is an authorized user of Domino
		if user == False:
			logging.error("Unauthorized access attempt via SMS by %s\n%s" % (d.From, d))
			r.sms("You are not an authorized user")
		else:
			# split the output into 160 character segments
			for text_segment in Twilio.split_sms(domino-cli.run(d.Body + " -m -f " + d.From)):
				r.sms(text_segment)
		return r

class call:
	'''
	This class handles phone calls
	'''	
	def POST(self,name):
		d = web.input(init="true", Digits=0)
		logging.info("Receiving phone call\n%s" % (d))
		web.header('Content-Type', 'text/xml')
		r = Twilio.twiml.Response()
		# the message to say when a timeout occurs
		timeout_msg = "Sorry, didn't get any input from you. Goodbye."
		# check if this call was initialized by sending an alert
		if name == "alert":
			# the digit options to press
			digitOpts = '''
Press 1 to hear the message.
Press 2 to acknowledge this alert.
'''
			receiver = User.get_user_by_phone(d.To)
			alert = Alert.Alert(d.alert_id)
			# check if this is the first interaction for this call session
			if d.init.lower() == "true":
				with r.gather(action="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
					g.say('''Hello %s, a message from Domino. An alert has been issued with subject "%s". %s.''' % (receiver.name, alert.subject, digitOpts))
				r.say(timeout_msg)
			else:
				if int(d.Digits) == 1:
					with r.gather(action="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id), timeout="30", method="POST", numDigits="1") as g:
						g.say('''%s. %s''' % (alert.message, digitOpts))
					r.say(timeout_msg)
				elif int(d.Digits) == 2:
					if alert.ack_alert(receiver):
						r.say("The alert has been acknowledged. Thank you and goodbye.")
						r.redirect(url="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id))
					else:
						r.say("Sorry, failed to acknowledge the alert. Please try it via SMS")
						r.redirect(url="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id))
				elif d.Digits == 0:
					with r.gather(action="%s:%s/call/alert?alert_id=%s&init=false" % (conf['server_address'],conf['port'],alert.id), timeout="30", method="POST", numDigits="1") as g:
						g.say('''%s''' % (digitOpts))
					r.say(timeout_msg)
				else:
					r.say("Sorry, didn't understand the digits you entered. Goodbye")
		else:
			requester = User.get_user_by_phone(d.From)
			# get the team that is associate with this phone number the user called
			team = Team.get_team_by_phone(d.To)[0]
			oncall_users = team.on_call()
			# if caller is not a oncall user or they are, but calling a different team then they are in
			if requester == False or Team.check_user(requester, team) == False:
				if team == '':
					r.say("Sorry, The phone number you called is not associated with any team. Please contact you system administrator for help.")
				else:
					# get the first user on call and forward the call to them
					if len(oncall_users) > 0:
						for user in oncall_users:
							r.say("Calling %s." % user.name)
							r.dial(number=user.phone)
					else:
						r.say("Sorry, currently there is no one on call for %s. Please try again later." % team)
			else:
				# the caller is calling the same team phone number as the team that they are on
				# check if d.Digits is the default value (meaning, either the caller hasn't pushed a button and this is the beginning of the call, or they hit 0 to start over
				if int(d.Digits) == 0:
					if d.init.lower() == "true":
						if Team.check_oncall_user(requester, team) == True:
							# figure out where in line the user is on call
							for i,u in enumerate(team.members):
								if requester.id == u.id:
									oncall_status = "You are currently on call in spot %s" % (i + 1)
									break
						else:
							if len(oncall_users) > 0:
								oncall_status = "Currenty, %s is on call" % (oncall_users[0].name)
							else:
								oncall_status = "Currenty, no one is on call"
						with r.gather(action="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
							g.say('''Hello %s. %s. Press 1 if you want to hear the present status of alerts. Press 2 to acknowledge the last alert sent to you. Press 3 to conference call everyone on call into this call.''' % (requester.name, oncall_status))
					else:
						with r.gather(action="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
							g.say('''Press 1 if you want to hear the present status of alerts. Press 2 to acknowledge the last alert sent to you. Press 3 to conference call everyone on call into this call.''')
					r.say(timeout_msg)
				elif int(d.Digits) == 1:
					# getting the status of alerts
					r.say(domino.run("alert status -f " + requester.phone))
					r.redirect(url="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']))
				elif int(d.Digits) == 2:
					# acking the last alert sent to the user calling
					r.say(domino.run("alert ack -f " + requester.phone))
					r.redirect(url="%s:%s/call/event?init=false" % (conf['server_address'],conf['port']))
				elif int(d.Digits) == 3:
					# calling the other users on call
					if len(oncall_users) == 1 and Team.check_oncall_user(requester, team) == True:
						r.say("You're the only person on call. I have no one to forward you to.")
					else:
						if len(oncall_users) > 0:
							for user in oncall_users:
								r.say("Calling %s." % user.name)
								r.dial(number=user.phone)
						else:	
							r.say("Sorry, no one is currently on call to forward you to.")
				else:
					r.say("Sorry, number you pressed is not valid. Please try again.")
		return r

def check_alerts():
	'''
	This function runs in an infinite loop to find any unacked alerts that need an alert to be sent out.
	'''
	# intentionally creating an infinite loop.
	foobar = True
	while foobar == True:
		# looking for alerts that are due to page
		for a in Alert.check_paging_alerts():
			a.send_page()
		# looking for alerts that are due to email
		for a in Alert.check_email_alerts():
			a.send_email()
		time.sleep(5)

if __name__ == "__main__":
	p = Process(target=check_alerts)
	p.start()
	app.run()
