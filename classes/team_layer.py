#!/usr/bin/env python

import logging
import datetime

import mysql_layer as Mysql
import user_layer as User
import util_layer as Util

conf = Util.load_conf()

def all_teams(id=None):
	'''
	Get all teams from the db.
	'''
	if id == None or id == 0:
		return Mysql.query('''SELECT * FROM teams ORDER BY id DESC''', "teams")
	else:
		return Mysql.query('''SELECT * FROM teams WHERE id > %s ORDER BY id DESC''' % (id), "teams")

def get_team_names():
    '''
    Return an array of all team names
    '''
    names = []
    teams = Mysql.query('''SELECT * FROM teams ORDER BY id DESC''', "teams")
    for team in teams:
        names.append(team.name)
    return names

def get_teams(teams_raw):
	'''
	Get a list of teams by ids or name, which is comma separated
	'''
	if teams_raw == None: return []
	if (teams_raw.startswith("'") and teams_raw.endswith("'")) or (teams_raw.startswith('"') and teams_raw.endswith('"')): 
		teams_raw = teams_raw[1:-1]
	teams = []
	for t in teams_raw.split(","):
		try:
			t = int(t)
			teams.append(Team(t))
		except:
			t = get_team_by_name(t)
			if t != False and len(t) > 0: teams.extend(t)
	return teams

def flatten_teams(teams):
	'''
	Flatten a list of user objects in a comma separated user id list
	'''
	if len(teams) > 0 and isinstance(teams, list):
		tmp = []
		for t in teams:
			tmp.append(t.id)
		return ','.join( map( str, tmp ) )
	else:
		return None
		
def get_default_teams():
	'''
	Return the default team
	'''
	return Mysql.query('''SELECT * FROM teams WHERE catchall = 0''', "teams")

def get_team_by_name(name):
	'''
	Return a team object by giving the name of that team
	'''
	return Mysql.query('''SELECT * FROM teams WHERE name = "%s"''' % (name), "teams")

def get_team_by_phone(phone):
	'''
	Return a team object by giving the phone number of that team
	'''
	return Mysql.query('''SELECT * FROM teams WHERE phone = "%s"''' % (phone), "teams")	


def find_user(id):
	'''
	This function looks for teams with a specific user in.
	'''
	teams = []
	for t in all_teams():
		for u in t.members:
			if int(id) == int(u.id):
				teams.append(t)
	return teams

def find_user_oncall(id):
	'''
	This function looks for a specific is on call in any team
	'''
	teams = []
	all_teams = all_teams()
	for t in all_teams:
		for u in t.oncall:
			if id == u.id: teams.append(t)
	return teams

def check_user(user, team):
	'''
	This fuction checks if a specific user is a member of a specific team
	'''
	for u in team.members:
		if user.id == u.id:
			return True
	return False
	
def check_oncall_user(user, team):
	'''
	This fuction checks if a specific user is on call for a specific team
	'''
	for u in team.on_call():
		if user.id == u.id:
			return True
	return False


class Team:
	def __init__(self, id=0, users=True):
		'''
		This initializes a team object. If id is given, loads that team. If not, creates a new team object with default values.
		'''
		logging.debug("Initializing team: %s" % id)

		if id == 0:
			self.name = ''
			self.email = ''
			self.members = ''
			self.catchall = 1
			self.oncall_count = 0
			self.phone = conf['twilio_number']
			self.id = id
		else:
			self.load(id, users)
			self.id = int(id)
			
	def load(self, id, users=True):
		'''
		load a team with a specific id
		'''
		logging.debug("Loading team: %s" % id)
		
		try:
			self.__dict__.update(Mysql.query('''SELECT * FROM teams WHERE id = %s LIMIT 1''' % (id), "teams")[0].__dict__)
		except Exception, e:
			Util.strace(e)
			self.id = 0
			return False
	
	def on_call(self):
		'''
		Get a list of all users that are currently on call for a specific team.
		'''
		if hasattr(self, 'members'):
			return self.members[:self.oncall_count]
		else:
			return []
	
	def save(self):
		'''
		Save the team to the db.
		'''
		logging.debug("Saving team: %s" % self.name)
		return Mysql.save('''REPLACE INTO teams (id,name,email,members,oncall_count,phone,catchall) VALUES (%s,'%s','%s','%s',%s,'%s',%s)''' % (self.id,self.name,self.email,User.flatten_users(self.members),self.oncall_count,self.phone,self.catchall))
			
	def delete(self):
		'''
		Delete the team form the db.
		'''
		logging.debug("Deleting team: %s" % self.name)
		return Mysql.delete('teams', self.id)
			
	def scrub(self):
		'''
		This scrubs the team from objects in the tean object. This is mainly used to make the user convertable to json format.
		'''
		if hasattr(self, 'db'):
			del self.db
		if hasattr(self, 'createDate') and type(self.createDate) is datetime.datetime:
			self.createDate = self.createDate.isoformat()
		if hasattr(self, 'members'):
			clean_members = []
			if isinstance(self.members, list):
				for m in self.members:
					clean_members.append(m.scrub())
				self.members = clean_members
		return self.__dict__
			
	def print_team(self, SMS=False):
		'''
		Print out the contents of a team object. SMS variable makes output SMS friendly.
		'''

		oncall_users = ''
		for i,u in enumerate(self.on_call()):
			if i == 0:
				oncall_users = u.name
			else:
				oncall_users = "%s, %s" % (oncall_users, u.name)
		
		members = ''
		for i,u in enumerate(self.members):
			if i == 0:
				members = u.name
			else:
				members = "%s, %s" % (self, u.name)	
		
		if SMS == True:
			output = "name:%s\nphone:%s\noncall:%s\n" % (self.name, self.phone, self.on_call()[0])
		else:
			output = "id:%i \nname:%s \nphone:%s \noncall:%s \nmembers:%s \n" % (self.id, self.name, self.phone, oncall_users, members)
		logging.debug("Printing team: %s" % output)
		return output
