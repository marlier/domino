#!/usr/bin/env python

import logging
import MySQLdb, MySQLdb.cursors 
import datetime
import random

import util_layer as Util
import user_layer as User
import alert_layer as Alert
import team_layer as Team
import rule_layer as Rule
import notification_layer as Notification

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
        if table == "users" or table == "alerts":
            # if we're querying users or alerts, we want to get team data to include
            _db._cursor.execute('''SELECT * FROM teams''')
            teams = _db._cursor.fetchall()
        elif table == "teams":
            # if we're querying teams, we want o get user data to include
            _db._cursor.execute('''SELECT * FROM users''')
            users = _db._cursor.fetchall()
        for t in temp:
            # remove any quotes around strings that the db may have
            for key in t:
                if isinstance(t[key], str):
                    if (t[key].startswith("'") and t[key].endswith("'")) or (t[key].startswith('"') and t[key].endswith('"')): 
                        t[key] = t[key][1:-1]
            if table == "users":
                tmp = User.User()
                # get user id
                uid = t['id']
                
                # get all teams and their members
                if teams == None: continue
                
                #see if any of the teams has this user id.
                userTeams = []
                for z in teams:
                    for m in z['members'].split(','):
                        if int(m) == int(uid):
                            y = Team.Team()
                            y.__dict__.update(z)
                            del y.members
                            userTeams.append(y)         
                t['teams'] = userTeams
            elif table == "alerts":
                tmp = Alert.Alert()
                alert_teams = []
                # convert teams from ids, to object instances
                t['teams'] = t['teams'].split(',')
                if teams != None:
                    for x in teams:
                        if str(x['id']) in t['teams']:
                            z = Team.Team()
                            z.__dict__.update(x)
                            del z.members
                            alert_teams.append(z)
                t['teams'] = alert_teams
            elif table == "teams":
                tmp = Team.Team()
                members = []
                # convert members from ids, to object instances
                _db._cursor.execute('''SELECT * FROM users WHERE id IN (%s)''' % (t['members']))
                y = _db._cursor.fetchall()
                if y != None:
                    for x in y:
                        z = User.User()
                        z.__dict__.update(x)
                        members.append(z)
                t['members'] = members
            elif table == "notifications":
                tmp = Notification.Notification()
                _db._cursor.execute('''SELECT * FROM alerts_history WHERE id = %s''' % (tmp.alert))
                y = _db._cursor.fetchone()
                if y != None:
                    z = Alert.Alert()
                    z.__dict__.update(y)
                    del z.teams
                    t['alert'] = z
            elif table == "inbound_rules":
                tmp = Rule.Rule()
            tmp.__dict__.update(t)
            objects.append(tmp)
        _db.close()
        return objects
    except Exception, e:
        Util.strace(e)
        return False

def save(sqlstr):
    '''
    Save the team to the db.
    '''
    logging.debug("Mysql Save query: %s" % sqlstr)
    try:
        _db = Database()
        _db._cursor.execute('''%s''' % (sqlstr))
        _db.save()
        _db.close()
        return True
    except Exception, e:
        Util.strace(e)
        return False


def delete(table, id):
    '''
    Deletes a row from a table
    '''
    try:
        _db = Database()
        _db._cursor.execute( '''DELETE FROM %s WHERE id=%s''' % (table, id))
        _db.save()
        _db.close()
        return True
    except Exception, e:
        Util.strace(e)
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
            try:
                logging.error("Cannot connect to db, creating new one....")
                db = MySQLdb.connect(host=conf['mysql_host'], port=conf['mysql_port'], user=conf['mysql_username'], passwd=conf['mysql_passwd'], cursorclass=MySQLdb.cursors.DictCursor)
                c = db.cursor()
                cmd = "CREATE DATABASE %s;" % (conf['mysql_db'])
                c.execute(cmd)
                cmd = "use %s;" % (conf['mysql_db'])
                c.execute(cmd)
                cmd = '''CREATE TABLE IF NOT EXISTS alerts (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, message TEXT, teams CHAR(50), ack INT NOT NULL DEFAULT 0, ackby INT NOT NULL DEFAULT 0, acktime TIMESTAMP, lastAlertSent TIMESTAMP, tries INT NOT NULL DEFAULT 0, host CHAR(20), service CHAR(50), environment CHAR(20), colo CHAR(20), status INT NOT NULL DEFAULT 3, tags VARCHAR(255), remote_ip_address VARCHAR(45), UNIQUE active(environment,colo,host,service));'''
                c.execute(cmd)
                cmd = '''CREATE TABLE IF NOT EXISTS alerts_history (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP, message TEXT, teams CHAR(50), ack INT NOT NULL DEFAULT 0, ackby INT NOT NULL DEFAULT 0, acktime TIMESTAMP, lastAlertSent TIMESTAMP, tries INT NOT NULL DEFAULT 0, host CHAR(20), service CHAR(50), environment CHAR(20), colo CHAR(20), status INT NOT NULL DEFAULT 3, tags VARCHAR(255), remote_ip_address VARCHAR(45));'''
                c.execute(cmd)
                cmd = '''CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, name CHAR(50), email CHAR(50), phone varchar(50), lastAlert INT NOT NULL DEFAULT 0);'''
                c.execute(cmd)
                cmd = '''CREATE TABLE IF NOT EXISTS teams (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, name CHAR(50), email CHAR(50), oncall_count INT NOT NULL DEFAULT 0, catchall INT NOT NULL DEFAULT 1, members TEXT, phone CHAR(12));'''
                c.execute(cmd)
                cmd = '''CREATE TABLE IF NOT EXISTS healthcheck (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, name CHAR(30));'''
                c.execute(cmd)
                cmd = '''CREATE TABLE IF NOT EXISTS notifications (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, noteType VARCHAR(15), message TEXT, tags VARCHAR(255), status INT NOT NULL DEFAULT 3, link VARCHAR(255), alert INT NOT NULL DEFAULT 0)'''
                c.execute(cmd)
                cmd = '''CREATE TABLE IF NOT EXISTS inbound_rules (id INT PRIMARY KEY AUTO_INCREMENT, createDate TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, host CHAR(20), service CHAR(50), environment CHAR(20), colo CHAR(20), status INT, tag VARCHAR(255), addTag VARCHAR(255), removeTag VARCHAR(255), UNIQUE active(environment,colo,host,service,tag,status));'''
                c.execute(cmd)
                self.connectDB()
                return True
            except Exception, e:
                Util.strace(e)
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
            Util.strace(e)
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
            Util.strace(e)
            return False
            
    def close(self):
        '''
        Close the connection to the database.
        '''
        try:
            logging.debug("closing connection to the db")
            self._connection.close()
            self._cursor.close()
            return True
        except Exception, e:
            Util.strace(e)
            return False
