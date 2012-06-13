#!/usr/bin/env python

import logging
from email.mime.text import MIMEText
import smtplib
import socket
import urllib

import user_layer as User
import util_layer as Util

conf = Util.load_conf()

class Email:
	def __init__(self, teams=None, alert=None):
		'''
		Initiation of email class.
		'''
		self.smtp = conf['email_server']
		self.port = conf['email_port']
		self.username = conf['email_username']
		self.passwd = conf['email_passwd']
		self.subject = ''
		self.message = ''
		self.to = None
		self.cc = None
		self.teams = teams
		self.alert = alert
	
	def send_alert_email(self):
		'''
		Send an alert via email.
		'''
		self.to = []
		self.cc = []
		# gather whom to sent the email to
		for team in self.teams:
			if "@" in team.email:
				self.to.append(team.email)
			else:
				for u in team.members:
					self.cc.append(u.email)
					
		self.subject = self.alert.subjectize()
		self.message = '''%s
		
		%s?host=%s&environment=%s&colo=%s&service=%s
		''' % (self.alert.message, conf['server_address'], urllib.quote_plus(self.alert.host), urllib.quote_plus(self.alert.environment), urllib.quote_plus(self.alert.colo), urllib.quote_plus(self.alert.service))
		message = MIMEText(self.message)
		message['Subject'] = self.subject
		message['From'] = self.username
		message['To'] = ', '.join(self.to)
		message['CC'] = ', '.join(self.cc)
		try:
			mailServer = smtplib.SMTP(self.smtp, self.port)
			mailServer.ehlo(socket.gethostname())
			mailServer.starttls()
			mailServer.ehlo(socket.gethostname())
			mailServer.login(self.username,self.passwd)
			mailServer.sendmail(self.username,self.to,message.as_string())
			mailServer.close()
			logging.info("Sent email alert to %s\n%s" % (', '.join(self.to + self.cc), self.message))
			return True
		except Exception, e:
			logging.error("Failed to send email to %s\n%s" % (self.to, self.message))
			logging.error(e.__str__())
			Util.strace()
			return False
	
	def send_custom_email(self, to='', subject='', message=''):
		'''
		Send a custom email specifiying a to address, subject line, and message.
		'''
		self.to = to
		self.subject = subject
		self.message = message
		message = MIMEText(self.message)
		message['Subject'] = self.subject
		message['From'] = self.username
		message['To'] = self.to
		try:
			mailServer = smtplib.SMTP(self.smtp, self.port)
			mailServer.ehlo(socket.gethostname())
			mailServer.starttls()
			mailServer.ehlo(socket.gethostname())
			mailServer.login(self.username,self.passwd)
			mailServer.sendmail(self.username,self.to,message.as_string())
			mailServer.close()
			logging.info("Sent email to %s\n%s" % (self.to, self.message))
			return True
		except Exception, e:
			logging.error("Failed to send email to %s\n%s" % (self.to, self.message))
			logging.error(e.__str__())
			Util.strace()
			return False
			
	def healthcheck(self):
		logging.info("Performing an email test healthcheck.")
		message = MIMEText("Test email from Domino")
		message['Subject'] = "Test Check"
		message['From'] = self.username
		message['To'] = "foobar@dummy.com"
		try:
			mailServer = smtplib.SMTP(self.smtp, self.port)
			mailServer.ehlo(socket.gethostname())
			mailServer.starttls()
			mailServer.ehlo(socket.gethostname())
			mailServer.login(self.username,self.passwd)
			#mailServer.sendmail(self.username,self.to,message.as_string())
			mailServer.close()
			logging.info("Email healthcheck was successful.")
			return True
		except Exception, e:
			logging.error("Failed to send test email. Healthcheck failed.")
			Util.strace()
			return False
		
		