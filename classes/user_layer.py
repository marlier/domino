#!/usr/bin/env python

import logging
import datetime

import mysql_layer as Mysql
import team_layer as Team
import twilio_layer as twilio
import util_layer as Util

def all_users():
	'''
	Get all users from the db.
	'''
	return Mysql.query('''SELECT * FROM users''', "users")

def get_users(user_ids, teams=False):
	'''
	Get a list of users by ids, which is comma separated
	'''
	users = []
	for t in user_ids.split(","):
		users.append(User(t, teams))
	return users

def flatten_users(users):
	'''
	Flatten a list of user objects in a comma separated user id list
	'''
	if len(users) > 0 and isinstance(users, list):
		tmp = []
		for u in users:
			tmp.append(u.id)
		return ','.join( map( str, tmp ) )
	else:
		return None

def get_user_by_phone(phone):
	'''
	Load user by their phone number (pattern matching by 'ends with')
	'''
	try:
		x = Mysql.query('''SELECT * FROM users WHERE phone LIKE '%%%s' LIMIT 1''' % phone, "users")
		if len(x) == 0: return False
		return x[0]
	except Exception, e:
		logging.error(e.__str__())
		return False

class User:
	def __init__(self, id=0, teams=True):
		'''
		This initializes a user object. If id is given, loads that user. If not, creates a new user object with default values.
		'''
		logging.debug("Initializing user: %s" % id)
		self.db = Mysql.Database()
		if id == 0:
			self.name = ''
			self.phone = ''
			self.email = ''
			self.lastAlert = 0
			self.id = id
		else:
			self.load_user(id, teams)
			self.id = int(id)

	def load_user(self, id, teams=True):
		'''
		load a user with a specific id
		'''
		logging.debug("Loading user: %s" % id)
		try:
			self.db._cursor.execute( '''SELECT * FROM users WHERE id = %s LIMIT 1''', id)
			user = self.db._cursor.fetchone()
			self.__dict__.update(user)
			if teams == True:
				#get teams the user is in
				self.teams = Team.find_user(id)
			else:
				try:
					del self.teams
				except:
					pass
			
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			self.id = 0
			return False
	
	def save(self):
		'''
		Save the user to the db.
		'''
		logging.debug("Saving user: %s" % self.name)
		try:
			self.db._cursor.execute('''REPLACE INTO users (id,name,email,phone,lastAlert) VALUES (%s,%s,%s,%s,%s)''', (self.id,self.name,self.email,self.phone,self.lastAlert))
			self.db.save()
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
		if hasattr(self, 'teams'):
			clean_teams = []
			for t in self.teams:
				clean_teams.append(t.scrub())
			self.teams = clean_teams
		return self.__dict__
		
			
	def delete_user(self):
		'''
		Delete the user form the db.
		'''
		logging.debug("Deleting user: %s" % self.name)
		try:
			self.db._cursor.execute('''DELETE FROM users WHERE id=%s''', (self.id))
			self.db.save()
			self.db.close()
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
			
	def print_user(self, SMS=False):
		'''
		Print out the contents of a user object. SMS variable makes output SMS friendly.
		'''

		if SMS == True:
			output = "name:%s|phone: %s \n" % (self.name, self.phone)
		else:
			output = "id:%i\nname:%s\nphone:%s\nemail:%s\n" % (self.id, self.name, self.phone, self.email)
		logging.debug("Printing user: %s" % output)
		return output