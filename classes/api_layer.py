#!/usr/bin/env python

import logging, urllib, datetime
import simplejson as json

import mysql_layer as Mysql
import twilio_layer as Twilio
import user_layer as User
import alert_layer as Alert
import team_layer as Team
import email_layer as Email
import notification_layer as Notification
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
		#pagination
		self.limit = 25
		self.offset = 0
		
		self.default = 1
		self.active_count = 0
		self.twilio_token = conf['twilio_token']
		self.twilio_acct = conf['twilio_acct']
		self.twilio_number = conf['twilio_number']
		self.search = ''
		self.since = 0
		#graph data
		self.segment = 7
		self.unit = "DAY"
		
		self.terms = None
		self.sort = None
		self.status_message = None
		self.name = None
		self.phone = None
		self.email = None
		self.teams = None
		self.id = None
		self.ack = None
		self.message = None
		self.user_id = 0
		
		# default notification vars
		self.noteType = "email"
		
		# convert the dictionary array received into Api class attributes
		self.__dict__.update(data)
		
		# making sure values are correct var type
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
		if self.limit != 0:
			try:
				self.limit = int(self.limit)
			except Exception, e:
				self.populate(1006, "Limit is not a integer")
				return
		if self.offset != 0:
			try:
				self.offset = int(self.offset)
			except Exception, e:
				self.populate(1006, "Offset is not a integer")
				return
				
	def healthcheck(self):
		'''
		This checks the system to see if capable of handling api requests
		'''
		if Util.healthcheck():
			self.populate(200,"Healthchecks were successful")
		else:
			self.populate(500,"Healthchecks were not successful.")

	def get_obj(self):
		'''
		This gets an object(s)
		'''
		if self.objType == "Alert" or self.objType == "History":
			if self.objType == "History":
				objects = Alert.all_alert_history(self.since)
			else:
				if self.id==0 or self.id == None:
					objects = Alert.all_alerts()
				else:
					objects = [Alert.Alert(self.id)]
			for o in objects:
				o.status = o.status_wordform()
				o.summary = o.summarize()
		elif self.objType == "User":
			if self.id==0 or self.id == None:
				objects = User.all_users()
			else:
				objects = [User.User(self.id)]
		elif self.objType == "Team":
			if self.id==0 or self.id == None:
				objects = Team.all_teams()
			else:
				objects = [Team.Team(self.id)]
		elif self.objType == "Notification":
			if self.id==0 or self.id == None:
				objects = Notification.get_notifications(self.noteType, self.since, self.limit)
			else:
				objects = [Notification.Notification(self.id)]
		elif self.objType == "Analytics":
			if self.name == None:
				#return list of analytics names that are supported
				return self.populate(200, "OK", ['frequent'])
			elif self.name == "frequent":
				objects = Alert.frequent_alerts(self.since)
			else:
				return self.populate(301, "Invalid analytics name")
		elif self.objType == "Graph":
			if self.unit.upper() in ["SECOND", "MINUTE", "HOUR", "DAY"]:
				self.search = self.search.split(",")
				objects = []
				for t in self.search:
					objects.append(Alert.graph_data(self.segment,self.unit,t))
				return self.populate(200,"OK",objects)
			else:
				self.populate(1802,"Invalid API metic call: units parameter must be SECOND, MINUTE, HOUR, or DAY")			
		if self.search != None and len(self.search) > 0:
			objects = self.filter(objects)
		if self.sort != None and len(self.sort) > 0:
			if self.sort == "oldest":
				objects = objects[::-1]
		# take into account the offset and limit requested
		objects = objects[self.offset:]
		if self.limit > 0:
			objects = objects[:self.limit]
		dict_objs = []
		for x in objects:
			if hasattr(x, "scrub"):
				dict_objs.append(x.scrub())
			else:
				dict_objs.append(x)
		self.populate(200,"OK",dict_objs)

	def set_obj(self,data):
		'''
		This sets or saves an alert, or creates a new one
		'''
		if self.objType == "Alert":
			if self.id == None or self.id == 0:
				#create new alert
				# check to see if this alert is a new different than the one before it
				lastAlert = Alert.get_current_alert(self.environment, self.colo, self.host, self.service)
				if len(lastAlert) > 0: lastAlert = lastAlert[0]
				if len(lastAlert) == 0 or (lastAlert.host == self.host and lastAlert.service == self.service and lastAlert.colo == self.colo and lastAlert.environment == self.environment and lastAlert.status == self.status):
					if lastAlert.message == self.message:
						self.populate(200,"OK",json.dumps("Repeat alert"))
					else:
						lastAlert.message = self.message
						lastAlert.save()
						self.populate(200,"OK",json.dumps("Repeat alert, updated message."))
				else:
					logging.info("Recieved new alert")
					# save new alert to the db
					newalert = Alert.Alert()
					newalert.message = self.message
					newalert.host = self.host
					newalert.service = self.service
					newalert.colo = self.colo
					newalert.environment = self.environment
					newalert.tags = self.tags
					newalert.remote_addr = self.remote_ip_address
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
			elif self.id != 0:
				try:
					obj = Alert.Alert(self.id)
					obj.__dict__.update(data)
					if obj.save() == True:
						self.populate(200,"OK")
					else:
						self.populate(701,"Failed to save alert.")
				except Exception, e:
					self.populate(1602,e.__str__())
					Util.strace(e)
					return
		elif self.objType == "User":
			if self.id == None or self.id == 0:
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
			elif self.id != 0:
				try:
					obj = User.User(self.id)
					obj.__dict__.update(data)
					if obj.save() == True:
						self.populate(200,"OK")
					else:
						self.populate(701,"Failed to save user.")
				except Exception, e:
					self.populate(1602,e.__str__())
					Util.strace(e)
					return
		elif self.objType == "Team":
			if self.id == None or self.id == 0:
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
			elif self.id != 0:
				try:
					obj = Team.Team(self.id)
					# save the original members of the team to see if its changed
					orig_members = self.members[:self.oncall_count]
					obj.__dict__.update(data)
					obj.members = User.get_users(self.members)
					if obj.save() == True:
						# SMS the delta of whose on call
						oncall_list = []
						for i,o in enumerate(orig_members):
							oncall_list.append(o.id)
							if o.id != obj.members[i].id:
								Twilio.send_sms(o, self, None, "You're now on call for team %s in spot %d" % (self.name, (i+1)))
						for m in obj.members[:self.oncall_count]:
							if m.id not in oncall_list:
								Twilio.send_sms(m, self, None, "You're no longer on call for team %s" % (self.name))
						self.populate(200,"OK")
					else:
						self.populate(701,"Failed to save team.")
				except Exception, e:
					self.populate(1602,e.__str__())
					Util.strace(e)
					return
			
	def del_obj(self):
		'''
		This deletes an object
		'''
		try:
			obj = None
			if self.objType == "Alert":
				obj = Alert.Alert(self.id)
			elif self.objType == "User":
				obj = User.User(self.id)
			elif self.objType == "Team":
				obj = Team.Team(self.id)
			if obj != None:
				obj.delete()
				self.populate(200,"OK")
		except Exception, e:
			self.populate(1502,e.__str__())
			Util.strace(e)
			return
	
	def filter(self,objects):
		'''
		Filter objects 
		'''
		print type(self.search), self.search
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