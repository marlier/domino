#!/usr/bin/env python

import logging, urllib, datetime
import simplejson as json
from pprint import pprint

import mysql_layer as Mysql
import twilio_layer as Twilio
import user_layer as User
import alert_layer as Alert
import team_layer as Team
import email_layer as Email
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("api")

class Api():
	'''
	This API class is designed to return json via http request
	Not even close to being done (obviously)
	'''
	def __init__(self, **data):
		'''
		Initialize the api class
		'''
		# set some default attribute values
		self.count = 0
		self.default = 1
		self.active_count = 0
		self.twilio_token = conf['twilio_token']
		self.twilio_acct = conf['twilio_acct']
		self.twilio_number = conf['twilio_number']
		self.search = None
		self.segment = 0
		self.terms = None
		self.sort = None
		self.status_message = None
		self.name = None
		self.phone = None
		self.email = None
		self.teams = None
		self.id = None
		self.ack = None
		self.user_id = 0
		
		# convert the dictionary array received into Api class attributes
		self.__dict__.update(data)
		# making sure values are correct var type
		try:
			self.count = int(self.count)
		except Exception, e:
			self.populate(1002, "Count is not a integer")
			return
		if self.id != None:
			try:
				self.id = int(self.id)
			except Exception, e:
				self.populate(1003, "ID is not a integer")
				return
		if self.user_id != 0:
			try:
				self.user_id = int(self.user_id)
			except Exception, e:
				self.populate(1005, "User_id is not a integer")
				return
		if self.segment != 0:
			try:
				self.segment = int(self.segment)
			except Exception, e:
				self.populate(1006, "Segment is not a integer")
				return
				
		#init database connection
		self.db = Mysql.Database()

		if self.action.lower() == "query":
			self.query()
		elif self.action.lower() == "create":
			self.create()
		elif self.action.lower() == "edit":
			self.edit()
		elif self.action.lower() == "delete":
			self.delete()
		elif self.action.lower() == "metric":
			self.metrics()
		elif self.action.lower() == "healthcheck":
			self.healthcheck()
		else:
			self.populate(1001,"Invalid action type")

	def healthcheck(self):
		'''
		This checks the system to see if capable of handling api requests
		'''
		if Util.healthcheck():
			self.populate(200,"Healthchecks were successful")
		else:
			self.populate(500,"Healthchecks were not successful.")

	def query(self):
		'''
		This gathers information requested by the user
		'''
		if self.target == "alert" or self.target == "alerts":
			objects = Alert.all_alerts()
			for o in objects:
				o.status = o.status_wordform()
				o.summary = o.summarize()
		elif self.target == "alerthistory":
			objects = Alert.all_alert_history(self.since, self.count)
			for o in objects:
				o.status = o.status_wordform()
				o.summary = o.summarize()
		elif self.target == "user" or self.target == "users":
			objects = User.all_users()
		elif self.target == "team" or self.target == "teams":
			objects = Team.all_teams()
		else:
			self.populate(1101,"Invalid API query call: Missing valid target parameter")
			return
		if self.search != None and len(self.search) > 0:
			objects = self.filter(objects)
		if self.sort != None and len(self.sort) > 0:
			if self.sort == "old":
				objects = objects[::-1]
			elif self.sort == "new":
				pass
		dict_objs = []
		for x in objects:
			dict_objs.append(x.scrub())
			if len(dict_objs) >= self.count and self.count != 0: break
		self.populate(200,"OK",dict_objs)
	
	def create(self):
		'''
		This creates a new object (ie alert, user, team, etc) and saves it to db.
		'''
		if self.target == "alert" or self.target == "alerts":
			if self.message:
				self.message = urllib.unquote_plus(self.message)
			else:
				self.populate(1201,"No message in alert creation")
				return
			if self.teams:
				self.teams = urllib.unquote_plus(self.teams)
			# check to see if this alert is a new one
			isNewAlert = True
			fresh_alerts = Alert.fresh_alerts()
			if len(fresh_alerts) > 0:
				for a in fresh_alerts:
					if a.message == self.message and a.tags == self.tags and a.teams == self.teams and a.host == self.host and a.service == self.service and a.colo == self.colo and a.environment == self.environment: 
						isNewAlert == False
						self.populate(200,"OK",json.dumps("Repeat alert"))
						break
			if isNewAlert == True:
				logging.info("Recieved new alert")
				# save new alert to the db
				newalert = Alert.Alert()
				newalert.message = self.message
				newalert.host = self.host
				newalert.service = self.service
				newalert.colo = self.colo
				newalert.environment = self.environment
				newalert.tags = self.tags
				try:
					newalert.status = int(self.status)
				except:
					pass
				try:
					newalert.position = int(self.position)
				except:
					pass
				if newalert.status == 0 or newalert.position == 3:
					newalert.ack = 0
				newalert.teams = Team.get_teams(self.teams)
				if newalert.save() == True:
					if newalert.send_page() == True and newalert.send_email() == True:
						self.populate(200,"OK")
					else:
						self.populate(1202, "Failed to send new alert")
				else:
					self.populate(1202, "Failed to save new alert")

		elif self.target == "user" or self.target == "users":
			if self.name == None or len(self.name) <= 0:
				self.populate(1301,"No name parameter given in user creation")
				return
			if self.email == None or len(self.email) <= 0 or "@" not in self.email:
				self.populate(1302,"No or invalid email parameter given in user creation")
				return
			if self.phone == None or len(self.phone) != 12:
				self.populate(1303,"No or invalid phone number parameter given in user creation")
				return
			newuser = User.User()
			newuser.name = self.name
			newuser.email = self.email
			newuser.phone = self.phone
			if newuser.save():
				logging.info("Sucessfully created new user: %s" % (newuser.name))
				valid_code = Twilio.validate_phone(newuser)
				if valid_code['success'] == False:
					self.populate(1401,valid_code['message'])
					return
				elif valid_code['success'] == True:
					self.populate(1400,"Validation Code: %s" % (valid_code))
					return
			else:
				self.populate(1305, "Failed to save team data")
		elif self.target == "team" or self.target == "teams":
			if self.name == None or len(self.name) <= 0:
				self.populate(1901,"No name parameter given in team creation")
				return
			newteam = Team.Team()
			newteam.name = self.name
			newteam.email = self.email
			newteam.members = User.get_users(self.members)
			newteam.oncall_count = self.oncall_count
			newteam.catchall = self.catchall
			if len(self.phone) == 11 and self.phone[0:1] != "+": self.phone = "+%s" % (self.phone) 
			newteam.phone = self.phone
			if newteam.save():
				self.populate(200,"OK")
			else:
				self.populate(1902, "Failed to save team data")
		else:
			self.populate(1101,"Invalid API create call: Missing valid target parameter")
			return
	
	def edit(self):
		'''
		Receive new info for an already existent object
		'''
		if self.id == None:
			self.populate(1699,"Invalid API edit call: Missing valid id parameter")
			return
		if self.target == "alert" or self.target == "alerts":
			try:
				obj = Alert.Alert(self.id)
				if self.ack == 0 or self.ack == True or self.ack.lower() == "true":
					obj.ack_alert(self.user_id)
				if self.ack == 1 or self.ack == False or self.ack.lower() == "false":
					obj.ack = 0
					if obj.save():
						self.populate(200,"OK edit alert")
					else:
						self.populate(701,"Failed to save alert.")
			except Exception, e:
				self.populate(1602,e.__str__())
				Util.strace()
				return
		elif self.target == "user" or self.target == "users":
			try:
				obj = User.User(self.id)
				if self.name != None:
					if len(self.name) > 0: 
						obj.name = self.name
					else:
						self.populate(1603,"Bad name parameter")
						return
				if self.phone != None:
					if len(self.phone) == 12: 
						obj.phone = self.phone
					else:
						self.populate(1604,"Bad phone parameter")
						return
				if self.email != None:
					if len(self.email) > 0 and "@" in self.email:
						obj.email = self.email
					else:
						self.populate(1605,"Bad email parameter")
						return
				if obj.save():
					self.populate(200,"OK")
				else:
					self.populate(1608, "Failed to save user data")
			except Exception, e:
				self.populate(1602,e.__str__())
				Util.strace()
				return
		elif self.target == "team" or self.target == "teams":
			if self.name == None or len(self.name) <= 0:
				self.populate(1901,"No name parameter given in team creation")
				return
			obj = Team.Team(self.id)
			if self.name != None: obj.name = self.name
			if self.email != None: obj.email = self.email
			if self.members != None: obj.members = User.get_users(self.members)
			if self.oncall_count != None: obj.oncall_count = self.oncall_count
			if self.catchall != None: obj.catchall = self.catchall
			if len(self.phone) == 11 and self.phone[0:1] != "+": self.phone = "+%s" % (self.phone) 
			if self.phone != None: obj.phone = self.phone
			if obj.save():
				self.populate(200,"OK")
			else:
				self.populate(1902, "Failed to save team data")
		else:
			self.populate(1601,"Invalid API edit call: Missing valid target parameter")
			return
			
	def delete(self):
		'''
		delete an object
		'''
		if self.target == "alert" or self.target == "alerts":
			try:
				obj = Alert.Alert(self.id)
				obj.delete_alert()
				self.populate(200,"OK")
			except Exception, e:
				self.populate(1502,e.__str__())
				Util.strace()
				return
		elif self.target == "user" or self.target == "users":
			try:
				obj = User.User(self.id)
				obj.delete_user()
				self.populate(200,"OK")
			except Exception, e:
				self.populate(1502,e.__str__())
				Util.strace()
				return
		elif self.target == "team" or self.target == "teams":
			try:
				obj = Team.Team(self.id)
				obj.delete_team()
				self.populate(200,"OK")
			except Exception, e:
				self.populate(1502,e.__str__())
				Util.strace()
				return
		else:
			self.populate(1501,"Invalid API delete call: Missing valid target parameter")
			return
	
	def metrics(self):
		'''
		Get metric data
		'''
		if self.metric == "frequent":
			objects = Alert.frequent_alerts()			
			if self.search != None and len(self.search) > 0:
				objects = self.filter(objects)
			if len(objects) >= self.count and self.count != 0:
				objects = objects[:self.count]
			self.populate(200,"OK",objects)
		elif self.metric == "graph":
			if self.segment == None: self.segment = 7
			if self.unit == None: self.unit = "DAY"
			if self.search == None: self.search = ''
			#print self.terms
			if self.unit.upper() in ["SECOND", "MINUTE", "HOUR", "DAY"]:
				self.search = self.search.split(",")
				objects = []
				for t in self.search:
					objects.append(Alert.graph_data(self.segment,self.unit,t))
				self.populate(200,"OK",objects)
				
			else:
				self.populate(1802,"Invalid API metic call: units parameter must be SECOND, MINUTE, HOUR, or DAY")	
		else:
			self.populate(1801,"Invalid API metic call: Missing valid metric parameter")
			return
	
	def filter(self,objects):
		'''
		Filter objects 
		'''
		self.search = self.search.split(",")
		filtered_objects = []
		for o in objects:
			all_search_criteria_met = []
			for i,c in enumerate(self.search):
				# the ":" is interpreted as search for an exact match for a specific column of data
				if ":" in c:
					key = c[:c.index(":")].strip()
					keyval = o.__dict__[key]
					comp_val = c[c.index(":"):][1:].strip()
					
					if isinstance(keyval, str):
						vals = keyval.lower().split(',')
						if comp_val.lower() in vals:
							all_search_criteria_met.append(True)
						else:
							all_search_criteria_met.append(False)
					elif isinstance(keyval, list):
						found_c = False
						for x in keyval:
							if hasattr(x, 'name'):
								all_search_criteria_met.append(True)
								found_c = True
								break
						if found_c == False: all_search_criteria_met.append(False)
				# if it stats with "-" its skipping objects where the word is found 
				elif c.startswith("-"):
					c = c[1:].strip()
					found_c = False
					for attr, value in o.__dict__.iteritems():
						try:
							if c.lower() in str(value).lower():
								found_c = True
						except Exception, e:
							pass
					if found_c == True: 
						all_search_criteria_met.append(False)
					else:
						all_search_criteria_met.append(True)
				else:
					found_c = False
					for attr, value in o.__dict__.iteritems():
						try:
							if c.lower().strip() in str(value).lower():
								found_c = True
						except Exception, e:
							pass
					if found_c == False: 
						all_search_criteria_met.append(False)
					else:
						all_search_criteria_met.append(True)
			if False not in all_search_criteria_met:
				filtered_objects.append(o)
		return filtered_objects
		
	def populate(self,status=500, status_message="Internal application layer error", data=None):
		'''
		generate json to return to requester.
		'''
		self.status = status
		self.status_message = status_message
		self.data = data
		if self.status % 100 != 0:
			logging.error(self.status_message)
		fulljson = {}
		fulljson['status'] = self.status
		fulljson['status_message'] = self.status_message
		fulljson['data'] = self.data
		self.fulljson = json.dumps(fulljson, skipkeys=True, sort_keys=True, indent=4 * ' ')
	
	def print_obj(self):
		'''
		Print out the attributes of an object, and make it pretty
		'''
		pprint (vars(self))
		
		
		
		
		
