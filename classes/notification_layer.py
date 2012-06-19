#!/usr/bin/env python

import logging
import datetime

import mysql_layer as Mysql
import util_layer as Util

def all_notifications():
	'''
	Get all users from the db.
	'''
	return Mysql.query('''SELECT * FROM notifications''', "notifications")

def get_notifications(noteType="email", since=0, limit=25):
	'''
	return a list of notification objects
	'''
	return Mysql.query('''SELECT * FROM notifications WHERE noteType = '%s' and id > %s ORDER BY id DESC LIMIT %s''' % (noteType, since, limit), "notifications")


class Notification:
	def __init__(self, id=0):
		'''
		This initializes a notification object. If id is given, loads that notification. If not, creates a new notification object with default values.
		'''
		logging.debug("Initializing notification: %s" % id)

		if id == 0:
			self.createDate = '0000-00-00 00:00:00'
			self.noteType = ''
			self.message = ''
			self.alert = 0
			self.link = ''
			self.tags = ''
			self.status = 3
			self.id = id
		else:
			self.load(id)
			self.id = int(id)

	def load(self, id):
		'''
		load a notification with a specific id
		'''
		logging.debug("Loading notification: %s" % id)
		try:
			self.__dict__.update(Mysql.query('''SELECT * FROM notifications WHERE id = %s LIMIT 1''' % (id), "notifications")[0].__dict__)
		except Exception, e:
			Util.strace(e)
			self.id = 0
			return False
	
	def save(self):
		'''
		Save the notification to the db.
		'''
		logging.debug("Saving notification: %s" % self.id)
		alert = 0
		if isinstance(self.alert, int) or isinstance(self.alert, long):
			alert = self.alert
		else:
			alert = self.alert.id
		return Mysql.save('''REPLACE INTO notifications (id,noteType,message,link,tags,status,alert) VALUES (%s,"%s","%s","%s","%s","%s",%s)''' % (self.id,self.noteType,self.message,self.link,self.tags,self.status,alert))
	
	def scrub(self):
		'''
		This scrubs the notification from objects in the user object. This is mainly used to make the notification convertable to json format.
		'''
		if hasattr(self, 'createDate') and type(self.createDate) is datetime.datetime:
			self.createDate = self.createDate.isoformat()
		return self.__dict__
		
			
	def delete(self):
		'''
		Delete the notificaion form the db.
		'''
		logging.debug("Deleting notification: %s" % self.id)
		return Mysql.delete('notifications', self.id)
			
	def print_notification(self, SMS=False):
		'''
		Print out the contents of a notificaion object. SMS variable makes output SMS friendly.
		'''

		if SMS == True:
			output = "Message:%s\nLink:%s\n" % (self.message, self.link)
		else:
			output = "id:%i\nMessage:%s\nlink:%s\n" % (self.id, self.message, self.link)
		logging.debug("Printing user: %s" % output)
		return output
