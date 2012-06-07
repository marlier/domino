#!/usr/bin/env python

import logging
import MySQLdb, MySQLdb.cursors 
import datetime
import random

import util_layer as Util
import user_layer as User
import alert_layer as Alert
import team_layer as Team

conf = Util.load_conf()

def query(q_string,table):
	'''
	Query the db with the given string and return with an array of user objects.
	'''
	try:
		_db = Database()
		_db._cursor.execute( '''%s''' % (q_string))
		#logging.debug("Running mysql query: %s" % q_string)
		temp = _db._cursor.fetchall()
		if len(temp) == 0: return []
		objects = []
		for t in temp:
			if table == "users":
				objects.append(User.User(t['id']))
			elif table == "alerts":
				objects.append(Alert.Alert(t['id']))
			elif table == "teams":
				objects.append(Team.Team(t['id']))
		_db.close()
		return objects
	except Exception, e:
		logging.error(e.__str__())
		Util.strace()
		return False
	
class Database:
	def __init__(self):
		'''
		Initialize the db.
		'''
		#logging.debug("Initializing db")
		self.connectDB()

	def connectDB(self):
		'''
		Connect to the db.
		'''
		#logging.debug("Connecting to db at %s on port %s, as %s" % (conf['mysql_host'], conf['mysql_port'], conf['mysql_username']))
		try:
			self._connection = MySQLdb.connect(host=conf['mysql_host'], port=conf['mysql_port'], user=conf['mysql_username'], passwd=conf['mysql_passwd'], db=conf['mysql_db'], cursorclass=MySQLdb.cursors.DictCursor)
			self._cursor = self._connection.cursor()
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			try:
				logging.error("Cannot connect to db, creating new one....")
				db = MySQLdb.connect(host=conf['mysql_host'], port=conf['mysql_port'], user=conf['mysql_username'], passwd=conf['mysql_passwd'], cursorclass=MySQLdb.cursors.DictCursor)
				c = db.cursor()
				cmd = "CREATE DATABASE %s;" % (conf['mysql_db'])
				c.execute(cmd)
				cmd = "use %s;" % (conf['mysql_db'])
				c.execute(cmd)
				cmd = '''CREATE TABLE IF NOT EXISTS alerts (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, message TEXT, teams CHAR(50), ack INT NOT NULL DEFAULT 0, ackby INT NOT NULL DEFAULT 0, acktime TIMESTAMP, lastPageSent TIMESTAMP, lastEmailSent TIMESTAMP, tries INT NOT NULL DEFAULT 0, host CHAR(50), service CHAR(50), environment CHAR(30), colo CHAR(50), status CHAR(20), position INT NOT NULL DEFAULT 0, tags VARCHAR(255), UNIQUE active(environment,colo,host,service));'''
				c.execute(cmd)
				cmd = '''CREATE TABLE IF NOT EXISTS alerts_history (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, message TEXT, teams CHAR(50), ack INT NOT NULL DEFAULT 0, ackby INT NOT NULL DEFAULT 0, acktime TIMESTAMP, lastPageSent TIMESTAMP, lastEmailSent TIMESTAMP, tries INT NOT NULL DEFAULT 0, host CHAR(50), service CHAR(50), environment CHAR(30), colo CHAR(50), status CHAR(20), position INT NOT NULL DEFAULT 0, tags VARCHAR(255));'''
				c.execute(cmd)
				cmd = '''CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, name CHAR(50), email CHAR(50), phone varchar(50), lastAlert INT NOT NULL DEFAULT 0);'''
				c.execute(cmd)
				cmd = '''CREATE TABLE IF NOT EXISTS teams (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, name CHAR(50), email CHAR(50), oncall_count INT NOT NULL DEFAULT 0, catchall INT NOT NULL DEFAULT 1, members TEXT, phone CHAR(12));'''
				c.execute(cmd)
				cmd = '''CREATE TABLE IF NOT EXISTS healthcheck (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, name CHAR(30));'''
				c.execute(cmd)
				self.connectDB()
				return True
			except Exception, e:
				logging.error(e.__str__())
				Util.strace()
				return False
	
	def healthcheck(self):
		'''
		This performs a write, read, and delete actions on the database for verification that the db works.
		'''
		try:
			logging.info("Performing a database healthcheck...")
			char_set="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
			testname=''.join(random.sample(char_set,30))
			logging.info(testname)
			self._cursor.execute( '''INSERT INTO healthcheck (name) VALUES (%s)''', (testname))
			self.save()
			self._cursor.execute( '''SELECT name FROM healthcheck WHERE name = "%s" LIMIT 1''' % (testname))
			testQuery = self._cursor.fetchone()
			if len(testQuery) == 0 or testQuery == None:
				logging.error("Unable to find newly created healthcheck entry. Healthcheck failed.")
				return False
			if testQuery['name'] != testname:
				logging.error("Failed to read the db correctly. Healthcheck failed.")
				return False
			self._cursor.execute( '''Delete FROM healthcheck WHERE name = "%s"''' % (testname))
			self.save()
			self._cursor.execute( '''SELECT name FROM healthcheck WHERE name = "%s" LIMIT 1''' % (testname))
			testQuery = self._cursor.fetchone()
			if testQuery != None:
				logging.error("Unable to delete healthcheck entry. Healthcheck failed.")
				return False
			self.close()
			logging.info("Database healthcheck was successful.")
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
			
	def save(self):
		'''
		Save the changes to the db.
		'''
		try:
			logging.debug("saving changing to the db")
			self._connection.commit()
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False
			
	def close(self):
		'''
		Close the connection to the database.
		'''
		try:
 			logging.debug("closing connection to the db")
 			self._connection.close ()
			self._cursor.close()
			return True
		except Exception, e:
			logging.error(e.__str__())
			Util.strace()
			return False