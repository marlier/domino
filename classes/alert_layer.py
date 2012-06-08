#!/usr/bin/env python

import logging
import datetime
from datetime import date, timedelta
import math

import mysql_layer as Mysql
import twilio_layer as Twilio
import user_layer as User
import team_layer as Team
import email_layer as Email
import util_layer as Util

conf = Util.load_conf()

def all_alert_history(since=None, count=None):
	'''
	Get all alerts.
	'''
	if since == None and (count == None or count == 0):
		return Mysql.query('''SELECT * FROM alerts_history ORDER BY createDate DESC''', "alerts")
	elif since == None and (count != None or count != 0):
		return Mysql.query('''SELECT * FROM alerts_history LIMIT %s ORDER BY createDate DESC''' % (count), "alerts")
	elif since != None and (count == None or count == 0):
		return Mysql.query('''SELECT * FROM alerts_history WHERE createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s DAY) AND DATE_SUB(CURDATE(),INTERVAL -1 DAY) ORDER BY createDate DESC''' % (since), "alerts")
	elif since != None and (count != None or count != 0):
		return Mysql.query('''SELECT * FROM alerts_history WHERE createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s DAY) AND DATE_SUB(CURDATE(),INTERVAL -1 DAY) LIMIT %s ORDER BY createDate DESC''' % (since,count), "alerts")
	else:
		logging.error("History query missed logic traps");

def frequent_alerts(since=7):
	'''
	Get the most frequent alerts
	'''
	_db = Mysql.Database()
	_db._cursor.execute( '''SELECT DISTINCT environment,colo,host,service, COUNT(*) AS num  FROM alerts_history WHERE createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s DAY) AND DATE_SUB(CURDATE(),INTERVAL -1 DAY) GROUP BY environment,colo,host,service  ORDER BY num DESC;''' % (since))
	alerts = _db._cursor.fetchall()
	_db.close()
	#alerts = []
	#for a in raw_alerts:
	#	alerts.append({'environment':a['environment'], 'colo':a[1], 'host':a[2], 'service':a[3], 'count':a[4]})
	#logging.debug(alerts)
	return alerts

def round_date(t,unit):
	'''
	round the date to the closest unit
	'''
	unit = unit.lower()
	t = t.replace(microsecond = 0)
	timeperiods = ['second', 'minute', 'hour', 'day']
	for i,x in enumerate(timeperiods):
		if x != unit:
			if i == 0:
				t = t.replace(second=0)
			elif i == 1:
				t = t.replace(minute=0)
			elif i == 2:
				t = t.replace(hour=0)
	return t

def graph_data(amount=7, units="HOUR", terms = None):
	'''
	Collect graph data
	'''
	terms_query = ''
	if terms != None:
		terms = terms.split("+")
		for t in terms:
			if ":" in t:
				terms_query = "%s %s='%s' and" % (terms_query, t.split(":")[0].strip(), t.split(":")[1].strip())
	_db = Mysql.Database()
	#print ('''select COUNT(id) as count,createDate from alerts_history WHERE %s createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s %s) AND DATE_SUB(CURDATE(),INTERVAL -1 %s) group by %s(createDate);''' % (terms_query, amount, units, units, units))
	_db._cursor.execute( '''select COUNT(id) as count,createDate from alerts_history WHERE %s createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s %s) AND DATE_SUB(CURDATE(),INTERVAL -1 %s) group by %s(createDate);''' % (terms_query, amount, units, units, units))
	raw_alerts = _db._cursor.fetchall()
	d = []
	alerts = []
	# convert to dictionary
	for a in raw_alerts:
		t = round_date(a['createDate'], units)
		alerts.append({'count':a['count'], 'date':t})
		d.append(t)
	
	# fill in gaps in the data array
	# ensure d list has the oldest date and current date so we can properly fill the gaps
	now = round_date(datetime.datetime.now(), units)
	d.append(now)
	if units.lower() == "second":
		d.insert(0,now - datetime.timedelta(seconds=amount))
		date_set = set(d[0]+timedelta(seconds=x) for x in range(amount))
	elif units.lower() == "minute":
		d.insert(0,now - datetime.timedelta(minutes=amount))
		date_set = set(d[0]+timedelta(minutes=x) for x in range(amount))
	elif units.lower() == "hour":
		d.insert(0,now - datetime.timedelta(hours=amount))
		logging.error(d[0])
		date_set = set(d[0]+timedelta(hours=x) for x in range(amount))
	elif units.lower() == "day":
		d.insert(0,now - datetime.timedelta(days=amount))
		date_set = set(d[0]+timedelta(days=x) for x in range(amount))
	missing = sorted(date_set-set(d))
	for m in missing:
		alerts.append({'count':0, 'date':m})
	alerts = sorted(alerts, key=lambda k: k['count'])
	min = alerts[0]['count']
	max = alerts[-1]['count']
	alerts = sorted(alerts, key=lambda k: k['date'])
	# putting dates in isoformat
	for a in alerts:
		a['date'] = a['date'].isoformat()
	#ensuring that the right amount of data continues
	graph_data = alerts[-(amount - 1):]
	logging.debug(graph_data)
	
	return {'unit':units, 'segment':amount, 'terms':terms, 'data':graph_data, 'min':min, 'max':max}
	
def all_alerts(team=None):
	'''
	Get current alerts. This means the current status for each host/service.
	'''
	if team == None:
		return Mysql.query('''SELECT * FROM alerts ORDER BY createDate DESC''', "alerts")
	else:
		return Mysql.query('''SELECT * FROM alerts WHERE team = '%s' ORDER BY createDate DESC''' % (team), "alerts")
	return Mysql.query('''SELECT * FROM alerts ORDER BY createDate DESC''', "alerts")

def active(team=None):
	'''
	All active alerts
	'''
	if team == None:
		return Mysql.query('''SELECT * FROM alerts WHERE ack != 0 ORDER BY createDate DESC''', "alerts")
	else:
		all_alerts = Mysql.query('''SELECT * FROM alerts WHERE ack != 0 ORDER BY createDate DESC''', "alerts")
		team_alerts = []
		for a in all_alerts:
			for t in a.teams:
				if t.id == team:
					team_alerts.append(a)
					break
		return team_alerts

def acked():
	'''
	Get the last 20 inactive alerts.
	'''
	return Mysql.query('''SELECT * FROM alerts WHERE ack = 0 ORDER BY createDate DESC LIMIT 20''', "alerts")

def fresh_alerts():
	'''
	This returns a list of alerts that are considered "fresh". These are compared to incoming alerts to deem that as duplicates of alerts that already exist or not.
	'''
	return Mysql.query('''select * from alerts where (NOW() - createDate) < %s ORDER BY createDate DESC''' % (conf['alert_freshness']), "alerts")
	
def check_paging_alerts():
	'''
	This returns a list of alerts that needs an notification sent out.
	'''
	return Mysql.query('''SELECT * FROM alerts WHERE ack != 0 AND (NOW() - lastPageSent) > %s and position != 0 ORDER BY createDate DESC''' % (conf['paging_alert_interval']), "alerts")
	
def check_email_alerts():
	'''
	This returns a list of alerts that needs an notification sent out.
	'''
	return Mysql.query('''SELECT * FROM alerts WHERE ack != 0 AND (NOW() - lastEmailSent) > %s and position != 0 ORDER BY createDate DESC''' % (conf['email_alert_interval']), "alerts")

class Alert():
	def __init__(self, id=0):
		'''
		Initialize the alert object.
		If id is given, load alert with that id. Otherwise, create a new alert with default attributes.
		'''
		logging.debug("Initializing alert: %s" % id)
		self.db = Mysql.Database()
		if id == 0:
			self.message = ''
			self.host = ''
			self.service = ''
			self.colo = ''
			self.enironment = ''
			self.status = 3
			self.position = 1
			self.teams = '' #Team.get_default_teams()
			self.ack = 1
			self.ackby = 0
			self.acktime = '0000-00-00 00:00:00'
			self.lastPageSent = '0000-00-00 00:00:00'
			self.lastEmailSent = '0000-00-00 00:00:00'
			self.tries = 0
			self.id = id
		else:
			self.load_alert(id)
			self.id = int(id)

	def load_alert(self, id):
		'''
		Load an alert with a specific id.
		'''
		logging.debug("Loading alert: %s" % id)
		try:
			self.db._cursor.execute( '''SELECT * FROM alerts_history WHERE id = %s LIMIT 1''', id)
			alert = self.db._cursor.fetchone()
			# remove strings that are surrounded by quotes
			for key in alert:
				if isinstance(alert[key], str):
					if (alert[key].startswith("'") and alert[key].endswith("'")) or (alert[key].startswith('"') and alert[key].endswith('"')): 
						alert[key] = alert[key][1:-1]
			self.__dict__.update(alert)
			self.teams = Team.get_teams(self.teams)
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
	
	def save(self):
		'''
		Save the alert to the db.
		'''
		logging.debug("Saving alert: %s" % self.id)
		try:
			#print '''REPLACE INTO alerts (id,message,teams,ack,ackby,acktime,lastPageSent,lastEmailSent,tries,host,service,environment,colo,status,position,tags) VALUES (%s,"%s","%s",%s,%s,%s,%s,%s,%s,"%s","%s","%s","%s",%s,%s,"%s")''' % (self.id, self.message, Team.flatten_teams(self.teams), self.ack, self.ackby, self.acktime, self.lastPageSent, self.lastEmailSent, self.tries, self.host, self.service, self.environment, self.colo, self.status, self.position, self.tags)
			self.db._cursor.execute('''REPLACE INTO alerts (id,message,teams,ack,ackby,acktime,lastPageSent,lastEmailSent,tries,host,service,environment,colo,status,position,tags) VALUES (%s,"%s","%s",%s,%s,%s,%s,%s,%s,"%s","%s","%s","%s",%s,%s,"%s")''', (self.id, self.message, Team.flatten_teams(self.teams), self.ack, self.ackby, self.acktime, self.lastPageSent, self.lastEmailSent, self.tries, self.host, self.service, self.environment, self.colo, self.status, self.position, self.tags))
			self.db._cursor.execute('''REPLACE INTO alerts_history (id,message,teams,ack,ackby,acktime,lastPageSent,lastEmailSent,tries,host,service,environment,colo,status,position,tags) VALUES (%s,"%s","%s",%s,%s,%s,%s,%s,%s,"%s","%s","%s","%s",%s,%s,"%s")''', (self.id,self.message,Team.flatten_teams(self.teams),self.ack,self.ackby,self.acktime, self.lastPageSent, self.lastEmailSent, self.tries,self.host,self.service, self.environment, self.colo, self.status, self.position, self.tags))
			self.db.save()
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
	
	def ack_alert(self,user):
		'''
		Acknowledge the alert.
		'''
		logging.debug("Acknowledging alert: %s" % self.id)
		try:
			self.ack = 0
			self.ackby = user.id
			self.acktime = datetime.datetime.now()
			self.save()
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
	
	def send_page(self):
		'''
		This method sends pages to people who need to get one via sms or phone.
		'''
		logging.debug("Sending Page Alert: %s" % self.id)
		
		try:
			self.tries += 1
			self.lastPageSent = datetime.datetime.now()
			self.save()
			if len(self.teams) == 0: self.teams = Team.get_default_teams()
			if len(self.teams) == 0:
				logging.error("Failed to find any 'catchall' teams. This alert (%i) will not be sent" % (self.id))
				return False
			for team in self.teams:
				if self.position == 2 and len(team.on_call()) > 0:
					# send page
					# based on the number of alert attempts, gather a lits of users to alert.
					if "alert_escalation" in conf and conf['alert_escalation'] > 0:
						escalate = float(conf['alert_escalation'])
						num = int(math.ceil(self.tries/escalate))
						if num == 0: num = 1
						alert_users = team.on_call()[:num]
					else:
						alert_users = team.oncall[0]
					# loop through users to alert
					for i,au in enumerate(alert_users):
						if "call_failover" in conf and conf['call_failover'] >= 0:
							if conf['call_failover'] == 0:
								Twilio.make_call(au, team, alert=self)
							else:
								# check to see if enough tries have been made to this user to switch to calls instead of SMS
								if int(math.ceil(self.tries/float(i+1))) > conf['call_failover']:
									Twilio.make_call(user=au, team=team, alert=self)
								else:
									Twilio.send_sms(au, team, self, "%s\n%s" % (self.subjectize(), self.summarize()))
						else:
							Twilio.send_sms(au, team, self, "%s\n%s" % (self.subjectize(), self.summarize()))
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
		
	def send_email(self):
		'''
		This method sends emails to teams/people for an alert that is due for an email.
		'''
		logging.debug("Sending Email Alert: %s" % self.id)
		try:
			self.lastEmailSent = datetime.datetime.now()
			self.save()
			if len(self.teams) == 0: self.teams = Team.get_default_teams()
			if len(self.teams) == 0:
				logging.error("Failed to find any 'catchall' teams. This alert (%i) will not be sent" % (self.id))
				return False
			#send email
			e = Email.Email(self.teams, self)
			if e.send_alert_email() == False:
				logging.error("Failed to send email for alert (%i)." % (self.id))
				# action if the email fails
				return False
			else:
				return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
	
	def subjectize(self):
		'''
		Take alert attributes in put them into a one-liner
		'''
		return "%s: %s - %s/%s" % (self.colo, self.status_wordform(), self.host, self.service)
	
	def summarize(self):
		'''
		Shorten message to a one liner
		'''
		tmp = self.message.split('\n')
		if len(tmp) > 0:
			return self.message.split('\n')[0] + "..."
		else:
			return self.message.split('\n')[0]
	
	def status_wordform(self):
		if self.status == 0 or self.status == "0":
			return "OK"
		elif self.status == 1 or self.status == "1":
			return "Warning"
		elif self.status == 2 or self.status == "2":
			return "Critical"
		else:
			return "Unknown"
	
	def delete_alert(self):
		'''
		Delete the alert form the db.
		'''
		logging.debug("Deleting alert: %s" % self.id)
		try:
			self.db._cursor.execute('''DELETE FROM alerts WHERE id=%s''', (self.id))
			self.db.save()
			self.db.close()
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
			
	def scrub(self):
		'''
		This scrubs the user from objects in the user object. This is mainly used to make the user convertable to json format.
		'''
		if hasattr(self, 'db'):
			del self.db
		if hasattr(self, 'createDate') and type(self.createDate) is datetime.datetime:
			self.createDate = self.createDate.isoformat()
		if hasattr(self, 'acktime') and type(self.acktime) is datetime.datetime:
			self.acktime = self.acktime.isoformat()
		if hasattr(self, 'lastPageSent') and type(self.lastPageSent) is datetime.datetime:
			self.lastPageSent = self.lastPageSent.isoformat()
		if hasattr(self, 'lastEmailSent') and type(self.lastEmailSent) is datetime.datetime:
			self.lastEmailSent = self.lastEmailSent.isoformat()
		if hasattr(self, 'teams'):
			clean_teams = []
			for t in self.teams:
				clean_teams.append(t.scrub())
			self.teams = clean_teams
		return self.__dict__
		
	def print_alert(self, SMS=False):
		'''
		Print out the contents of an alert.
		the SMS param is to make the output SMS friendly or not
		'''
		if SMS == True:
			output = "ack:%s|tries:%s|teams:%s|summary:%s\n" % (self.ack, self.tries, self.teams, self.summarize())
		else:
			output = "id:%i\nack:%s\nacktime:%s\ntries:%s\nteams:%s\nmessage:%s\n" % (self.id, self.ack, self.acktime, self.tries, self.teams, self.message)
		logging.debug("Printing alert: %s" % self.id)
		return output