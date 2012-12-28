#!/usr/bin/env python

import logging, urllib
import datetime
from datetime import date, timedelta
import math

import mysql_layer as Mysql
import twilio_layer as Twilio
import user_layer as User
import team_layer as Team
import email_layer as Email
import notification_layer as Notification
import util_layer as Util

conf = Util.load_conf()

def frequent_alerts(since=7):
    '''
    Get the most frequent alerts
    '''
    _db = Mysql.Database()
    _db._cursor.execute( '''SELECT DISTINCT environment,colo,host,service, COUNT(*) AS count FROM alerts_history WHERE createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s DAY) AND DATE_SUB(CURDATE(),INTERVAL -1 DAY) GROUP BY environment,colo,host,service  ORDER BY count DESC;''' % (since))
    alerts = _db._cursor.fetchall()
    print "alerts", alerts
    _db.close()
    for alert in alerts:
        for key in alert:
            if isinstance(alert[key], str):
                if (alert[key].startswith("'") and alert[key].endswith("'")) or (alert[key].startswith('"') and alert[key].endswith('"')): 
                    alert[key] = alert[key][1:-1]
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
    _db.close()
    d = []
    alerts = []
    # convert to dictionary
    for a in raw_alerts:
        t = round_date(a['createDate'], units)
        alerts.append({'count':a['count'], 'date':t})
        d.append(t)
    
    # fill in gaps in the data array
    # ensure d list has the oldest date and current date so we can properly fill the gaps
    now = round_date(datetime.datetime.utcnow(), units)
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
    
    return {'unit':units, 'segment':amount, 'search':terms, 'datapoints':graph_data, 'min':min, 'max':max}

def all_alert_history(since=None,mylimit=25):
    '''
    Get all alerts.
    '''
    if mylimit == 0: mylimit = 1
    if since == None:
        return Mysql.query('''SELECT * FROM alerts_history ORDER BY id DESC LIMIT %s''' % (mylimit), "alerts")
    else:
        return Mysql.query('''SELECT * FROM alerts_history WHERE createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s DAY) AND DATE_SUB(CURDATE(),INTERVAL -1 DAY) ORDER BY id DESC LIMIT %s''' % (int(since), mylimit), "alerts")

def all_alerts(since=None):
    '''
    Get current alerts. This means the current status for each environment/colo/host/service.
    '''
    if since == None or since == 0:
        return Mysql.query('''SELECT * FROM alerts ORDER BY id DESC''', "alerts")
    else:
        return Mysql.query('''SELECT * FROM alerts WHERE id > %s ORDER BY id DESC''' % (since), "alerts")

def active(team=None):
    '''
    All active alerts
    '''
    if team == None:
        return Mysql.query('''SELECT * FROM alerts WHERE ack != 0 ORDER BY id DESC''', "alerts")
    else:
        all_alerts = Mysql.query('''SELECT * FROM alerts WHERE ack != 0 ORDER BY id DESC''', "alerts")
        team_alerts = []
        for a in all_alerts:
            if team in a.tags.split(','):
                team_alerts.append(a)
        return team_alerts

def get_current_alert(environment,colo,host,service):
    '''
    Get the current status of an alert specified by environment, colo, host, and service
    '''
    return Mysql.query('''SELECT * FROM alerts WHERE environment = "'%s'" and colo = "'%s'" and host = "'%s'" and service = "'%s'" LIMIT 1''' % (environment, colo, host, service), "alerts")
    
def check_alerts():
    '''
    This returns a list of alerts that needs a notification sent out.
    '''
    return Mysql.query('''SELECT * FROM alerts WHERE ack != 0 AND (NOW() - lastAlertSent) > %s ORDER BY id DESC''' % (conf['alert_interval']), "alerts")
    
class Alert():
    def __init__(self, id=0):
        '''
        Initialize the alert object.
        If id is given, load alert with that id. Otherwise, create a new alert with default attributes.
        '''
        logging.debug("Initializing alert: %s" % id)

        if id == 0:
            self.message = ''
            self.host = ''
            self.service = ''
            self.colo = ''
            self.enironment = ''
            self.status = 3
            self.ack = 1
            self.ackby = 0
            self.remote_ip_address = '0.0.0.0'
            self.acktime = '0000-00-00 00:00:00'
            self.lastAlertSent = '0000-00-00 00:00:00'
            self.tries = 0
            self.id = id
        else:
            self.load(id)
            self.id = int(id)

    def load(self, id):
        '''
        Load an alert with a specific id.
        '''
        logging.debug("Loading alert: %s" % id)
        try:
            self.__dict__.update(Mysql.query('''SELECT * FROM alerts_history WHERE id = %s LIMIT 1''' % (id), "alerts")[0].__dict__)
            if isinstance(self.status, str) and len(self.status) > 1:
                if self.status.upper() == "OK": 
                    self.status = 0
                elif self.status.upper() == "WARNING":
                    self.status = 1
                elif self.status.upper() == "CRITICAL":
                    self.status = 2
                else:
                    self.status = 3
        except Exception, e:
            Util.strace(e)
            return False
    
    def save(self):
        '''
        Save the alert to the db.
        '''
        logging.debug("Saving alert: %s" % self.id)
        try:
            _db = Mysql.Database()
            _db._cursor.execute('''REPLACE INTO alerts (id,message,ack,ackby,acktime,lastAlertSent,tries,host,service,environment,colo,status,tags,remote_ip_address) VALUES (%s,"%s",%s,%s,%s,%s,%s,%s,"%s","%s","%s",%s,%s,"%s")''', (self.id, self.message, self.ack, self.ackby, self.acktime, self.lastAlertSent, self.tries, self.host, self.service, self.environment, self.colo, self.status, self.tags, self.remote_ip_address))
            if self.id == 0:
                _db._cursor.execute('''SELECT id FROM alerts ORDER BY id DESC LIMIT 1''')
                tmp = _db._cursor.fetchone()
                self.id = tmp['id']
            _db._cursor.execute('''REPLACE INTO alerts_history (id,message,ack,ackby,acktime,lastAlertSent,tries,host,service,environment,colo,status,tags,remote_ip_address) VALUES (%s,"%s",%s,%s,%s,%s,%s,"%s","%s","%s",%s,%s,"%s","%s")''', (self.id,self.message,self.ack,self.ackby,self.acktime, self.lastAlertSent, self.tries,self.host,self.service, self.environment, self.colo, self.status, self.tags, self.remote_ip_address))
            _db.save()
            _db.close()
            return True
        except Exception, e:
            Util.strace(e)
            return False
    
    def ack_alert(self,user):
        '''
        Acknowledge the alert.
        '''
        logging.debug("Acknowledging alert: %s" % self.id)
        try:
            self.ack = 0
            self.ackby = user.id
            self.acktime = datetime.datetime.utcnow()
            self.save()
            return True
        except Exception, e:
            Util.strace(e)
            return False
        
    def send_alert(self):
        '''
        This method sends pages/emails to teams/people for an alert that is due for an email.
        '''
        logging.debug("Sending Alert: %s" % self.id)
        try:
            self.lastAlertSent = datetime.datetime.utcnow()
            self.save()
            newNotification = Notification.Notification()
            if "page" in self.tags.split(','):
                newNotification.noteType = "page"
            else:
                newNotification.noteType = "email"
            newNotification.alert = self.id
            newNotification.message = self.message
            newNotification.tags = self.tags
            newNotification.status = self.status
            newNotification.link = "%s:%s/detail?host=%s&environment=%s&colo=%s&service=%s" % (conf['webui_address'], conf['webui_port'], urllib.quote_plus(self.host), urllib.quote_plus(self.environment), urllib.quote_plus(self.colo), urllib.quote_plus(self.service))
            newNotification.save()
            team_names = Team.get_team_names()
            self.teams = []
            for name in team_names:
                if name in self.tags.split(','): self.teams.append(name)
            if len(self.teams) == 0:
                self.teams = Team.get_default_teams()
            else:
                teams = []
                for t in self.teams:
                    teams.append(Team.get_team_by_name(t))
                self.teams = teams
            if len(self.teams) == 0:
                logging.error("Failed to find any 'catchall' teams. This alert (%i) will not be sent" % (self.id))
                return False
            if "page" in self.tags.split(','):
                for team in self.teams:
                    if len(team.on_call()) > 0:
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

            #send email
            e = Email.Email(self.teams, self)
            if e.send_alert_email() == False:
                logging.error("Failed to send email for alert (%i)." % (self.id))
                # action if the email fails
                return False
            else:
                return True
        except Exception, e:
            Util.strace(e)
            return False

    def hasTag(self, tag):
        '''
        Checks to see if an alert has a specific tag. Returns bool
        '''
        if isinstance(self.tags, str):
            tags = self.tags.split(',')
        else:
            tags = self.tags
        if tag.lower() in [x.lower() for x in tags]:
            return True
        else:
            return False

    def subjectize(self):
        '''
        Take alert attributes in put them into a one-liner
        '''
        return "%s(%s): %s - %s/%s" % (self.colo, self.environment, self.status_wordform(), self.host, self.service)
    
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
    
    def delete(self):
        '''
        Delete the alert form the db.
        '''
        logging.debug("Deleting alert: %s" % self.id)
        return Mysql.delete('alerts', self.id)
            
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
        if hasattr(self, 'lastAlertSent') and type(self.lastAlertSent) is datetime.datetime:
            self.lastAlertSent = self.lastAlertSent.isoformat()
        if hasattr(self, 'teams'):
            clean_teams = []
            for t in self.teams:
                if hasattr(t, "scrub"):
                    clean_teams.append(t.scrub())
            self.teams = clean_teams
        return self.__dict__
        
    def print_alert(self, SMS=False):
        '''
        Print out the contents of an alert.
        the SMS param is to make the output SMS friendly or not
        '''
        if SMS == True:
            output = "ack:%s\ntries:%s\ntags:%s\nsummary:%s\n" % (self.ack, self.tries, self.tags, self.summarize())
        else:
            output = "id:%i\nack:%s\nacktime:%s\ntries:%s\ntags:%s\nmessage:%s\n" % (self.id, self.ack, self.acktime, self.tries, self.tags, self.message)
        logging.debug("Printing alert: %s" % self.id)
        return output
