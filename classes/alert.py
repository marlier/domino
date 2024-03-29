#!/usr/bin/env python

import logging, urllib
import datetime
from datetime import date, timedelta
import math

import mysql as Mysql
import domino_twilio as Twilio
import user as User
import team as Team
import email as Email
import notification as Notification
import util as Util

conf = Util.load_conf()

def frequent_alerts(since=7):
    '''
    Get the most frequent alerts
    '''
    alerts = Mysql.rawquery('''SELECT DISTINCT environment,colo,host,service, COUNT(*) AS count FROM alerts_history WHERE createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s DAY) AND DATE_SUB(CURDATE(),INTERVAL -1 DAY) GROUP BY environment,colo,host,service  ORDER BY count DESC;''' % (since))
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
    for t in terms:
        if ":" in t:
            key = t.split(":")[0].strip()
            value = t.split(":")[1].strip()
            if key == "status":
                value = to_int_status(value)
            terms_query = "%s %s='%s' and" % (terms_query, key, value)
    raw_alerts = Mysql.rawquery( '''select COUNT(id) as count,createDate from alerts_history WHERE %s createDate >= DATE_SUB(NOW(),INTERVAL %s %s) group by %s(createDate);''' % (terms_query, amount, units, units))
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
    # putting dates in epoch format
    for a in alerts:
        a['date'] = a['date'].strftime('%s')
    #ensuring that the right amount of data continues
    graph_data = alerts[-(amount):]
    logging.debug(graph_data)
    
    return {'unit':units, 'segment':amount, 'search':terms, 'datapoints':graph_data, 'min':min, 'max':max}

def uptime(since=None,environment=None,colo=None,host=None,service=None):
    '''
    This function finds the uptime of a specific service
    '''
    if since == None: since = 30
    # get the number of alerts that occurred during the timeperiod
    count = Mysql.rawquery('''SELECT COUNT(id) as count FROM alerts_history WHERE environment = "%s" and colo = "%s" and host = "%s" and service = "%s" and createDate >= DATE_SUB(NOW(),INTERVAL %s DAY) order by createDate DESC''' % (environment, colo, host, service, since))[0]['count']
    # get the data from these historical alerts, plus 1 more to get the state of the alert at the beginning of the timeperiod
    alerts = Mysql.rawquery('''SELECT status, createDate FROM alerts_history WHERE environment = "%s" and colo = "%s" and host = "%s" and service = "%s" order by createDate DESC LIMIT %s''' % (environment, colo, host, service, int(count) + 1))
    alerts = list(alerts)
    # inserting the current datetime
    alerts.insert(0, { 'createDate': datetime.datetime.utcnow() } )
    dataset = []
    total_time = 0
    ok_time = 0
    wordform = ["OK", "Warning", "Critical", "Unknown"]
    for i,x in enumerate(alerts):
        if i == 0: continue
        diff = int((alerts[i-1]['createDate'] - alerts[i]['createDate']).total_seconds())
        status = int(alerts[i]['status'])
        if status == 0: ok_time += diff
        if status > 3:
            status = "Unknown"
        else:
            status = wordform[status]
        if diff + total_time > (since * 24 * 60 * 60):
            # the last alert duration is longer than the timeperiod specified, chopping it
            diff = (since * 24 * 60 * 60) - total_time
            total_time = since * 24 * 60 * 60
            alerts[i]['createDate'] = datetime.datetime.utcnow() - datetime.timedelta(days=since)
        else:
            total_time += diff
        dataset.append( { "duration": diff, "status": status, 'startDate':alerts[i]['createDate'].strftime('%s') } )
    if total_time < (since * 24 * 60 * 60):
        # looks like the alert is newer than the timeperiod specified, assigning the previous time as 'Unknown'
        dataset.append( { "duration": ((since * 24 * 60 * 60) - total_time), "status": "No Data", "startDate":(datetime.datetime.utcnow() - datetime.timedelta(days=7)).strftime('%s') } )
    percentage = "{0:.4f}".format((float(ok_time) / total_time) * 100, 4)
    return { "uptime":ok_time, "downtime":(total_time - ok_time), "totaltime": total_time, "percentage":percentage, "dataset":dataset }



def all_alert_history(since=None):
    '''
    Get all alerts.
    '''
    if since == None:
        return Mysql.query('''SELECT * FROM alerts_history ORDER BY id DESC''', "alerts")
    else:
        return Mysql.query('''SELECT * FROM alerts_history WHERE createDate BETWEEN DATE_SUB(CURDATE(),INTERVAL %s DAY) AND DATE_SUB(CURDATE(),INTERVAL -1 DAY) ORDER BY id DESC''' % (int(since)), "alerts")

def all_alerts(since=None):
    '''
    Get current alerts. This means the current status for each environment/colo/host/service.
    '''
    if since == None or since == 0:
        return Mysql.query('''SELECT * FROM alerts ORDER BY id DESC''', "alerts")
    else:
        return Mysql.query('''SELECT * FROM alerts WHERE id > %s ORDER BY id DESC''' % (since), "alerts")

def paging_active(team=None):
    '''
    All active paging alerts
    '''
    if team == None:
        return Mysql.query('''SELECT * FROM alerts WHERE status > 0 and ack != true and tags REGEXP '(page|^page,|,page,|,page$)' ORDER BY id DESC''', "alerts")
    else:
        all_alerts = Mysql.query('''SELECT * FROM alerts WHERE status > 0 and ack != true and tags REGEXP '(%s|^%s,|,%s,|,%s$)(=?page|^page,|,page,|,page$)' ORDER BY id DESC''' % (team,team,team,team), "alerts")
        team_alerts = []
        for a in all_alerts:
            if team in a.tags.split(','):
                team_alerts.append(a)
        return team_alerts

def get_current_alert(environment,colo,host,service):
    '''
    Get the current status of an alert specified by environment, colo, host, and service
    '''
    return Mysql.query('''SELECT * FROM alerts WHERE environment = "%s" and colo = "%s" and host = "%s" and service = "%s" LIMIT 1''' % (environment, colo, host, service), "alerts")
    
def check_alerts():
    '''
    This returns a list of alerts that needs a notification sent out.
    '''
    return Mysql.query('''SELECT * FROM alerts WHERE status > 0 and ack != true AND (NOW() - lastAlertSent) > %s ORDER BY id DESC''' % (conf['alert_interval']), "alerts")

def check_paging_alerts():
    ''' 
    This returns a list of paging alerts that needs a notification sent out.
    '''
    return Mysql.query('''SELECT * FROM alerts WHERE status > 0 and ack != true AND (NOW() - lastAlertSent) > %s and tags REGEXP '(page|^page,|,page,|,page$)' ORDER BY id DESC''' % (conf['page_alert_interval']), "alerts")

def get_alerts_with_filter(filt,sort,limit, offset=0, table="alerts", count=False):
    '''
    This returns a list of alerts that meets the filter supplied
    SECURITY RISK: MYSQL INJECTION
    '''
    if count == True:
        query = "SELECT COUNT(id) as count FROM %s " % table
    else:
        query = "SELECT * FROM %s " % table
    if len(filt) > 0:
        query += " WHERE "
        search_terms = []
        for ft in filt:
            key = ft.split(':')[0].strip()
            value = ft.split(':')[1].strip()
            if value[0] == '-':
                negative = True
                value = value[1:]
            else:
                negative = False
            if key == "tags":
                if negative:
                    isnot = "NOT "
                else:
                    isnot = ""
                search_terms.append("tags %sREGEXP '(%s|^%s,|,%s,|,%s$)'" % (isnot,value,value,value,value))
            elif key == "message":
                if negative:
                    search_terms.append("message NOT LIKE '%s'" % (value))
                else:
                    search_terms.append("message LIKE '%s'" % (value))
            else:
                if key == "status":
                    value = to_int_status(value)
                if negative:
                    search_terms.append("%s != '%s'" % (key, value))
                else:
                    search_terms.append("%s = '%s'" % (key, value))
        
        query += ' and '.join(search_terms)
    if sort == "ASC" or sort == "oldest" or sort == "old":
        query += " order by createDate ASC"
    else:
        query += " order by createDate DESC"

    if limit is not None and limit > 0:
        query += " limit %s, %s" % (offset, limit)
    if count == True:
        return Mysql.rawquery(query)
    else:
        return Mysql.query(query,'alerts')

def to_int_status(status):
    '''
    This converts a status (ie ok, warning, critical, or unknown) to its numerical value ( ie 0,1,2,3)
    '''
    if status is None: return 3
    try:
        i = int(status)
        if i > 3: i = 3
        return i
    except:
        pass
    if status.upper() == "OK": 
        return 0
    elif status.upper() == "WARNING":
        return 1
    elif status.upper() == "CRITICAL":
        return 2
    return 3

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
            self.environment = ''
            self.status = 3
            self.ack = 0
            self.ackby = 0
            self.createDate = datetime.datetime.utcnow()
            self.remote_ip_address = '0.0.0.0'
            self.acktime = '0000-00-00 00:00:00'
            self.lastAlertSent = '0000-00-00 00:00:00'
            self.tries = 0
            self.id = id
        else:
            self.load(id)
            tags = self.tags.split(',')
            # remove blank tags
            tags = filter (lambda a: a != '', tags)
            self.tags = ','.join(tags)
            self.id = int(id)

    def load(self, id):
        '''
        Load an alert with a specific id.
        '''
        logging.debug("Loading alert: %s" % id)
        try:
            self.__dict__.update(Mysql.query('''SELECT * FROM alerts_history WHERE id = %s LIMIT 1''' % (id), "alerts")[0].__dict__)
            self.status = to_int_status(self.status)
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
            _db._cursor.execute('''REPLACE INTO alerts (id,createDate,message,ack,ackby,acktime,lastAlertSent,tries,host,service,environment,colo,status,tags,remote_ip_address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (self.id, self.createDate, self.message, self.ack, self.ackby, self.acktime, self.lastAlertSent, self.tries, self.host, self.service, self.environment, self.colo, self.status, self.tags, self.remote_ip_address))
            if self.id == 0:
                _db._cursor.execute('''SELECT id FROM alerts ORDER BY id DESC LIMIT 1''')
                tmp = _db._cursor.fetchone()
                self.id = tmp['id']
            _db._cursor.execute('''REPLACE INTO alerts_history (id,createDate,message,ack,ackby,acktime,lastAlertSent,tries,host,service,environment,colo,status,tags,remote_ip_address) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''', (self.id, self.createDate, self.message, self.ack, self.ackby, self.acktime, self.lastAlertSent, self.tries, self.host, self.service, self.environment, self.colo, self.status, self.tags, self.remote_ip_address))
            _db.save()
            _db.close()
            return True
        except Exception, e:
            Util.strace(e)
            return False
    
    def ack_alert(self,user_id):
        '''
        Acknowledge the alert.
        '''
        logging.debug("Acknowledging alert: %s" % self.id)
        try:
            self.ack = 1
            self.ackby = user_id
            self.acktime = datetime.datetime.utcnow()
            self.save()
            return True
        except Exception, e:
            Util.strace(e)
            return False

    def unack_alert(self):
        ''' 
        Unacknowledge the alert.
        '''
        logging.debug("Unacknowledging alert: %s" % self.id)
        try:
            self.ack = 0
            self.acktime = '0000-00-00 00:00:00'
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
            if self.hasTag("silent"): return True
            if self.check_dependencies() == False:
                return True
            newNotification = Notification.Notification()
            if "page" in self.tags.split(','):
                newNotification.noteType = "page"
            else:
                newNotification.noteType = "email"
            newNotification.alert = self.id
            newNotification.message = self.message
            newNotification.tags = self.tags
            newNotification.status = self.status
            newNotification.link = "%s:%s/detail?host=%s&environment=%s&colo=%s&service=%s" % (conf['api_address'], conf['api_port'], urllib.quote_plus(self.host), urllib.quote_plus(self.environment), urllib.quote_plus(self.colo), urllib.quote_plus(self.service))
            newNotification.save()

            # get a list of teams/users to send alerts to
            team_names = Team.get_team_names()
            self.teams = []
            user_names = User.get_user_names()
            self.users = []
            tags = self.tags.lower().split(',')
            for name in team_names:
                if name.lower() in tags: self.teams.append(name)
            for name in user_names:
                if name.lower() in tags: self.users.append(name)
            if len(self.teams) == 0:
                self.teams = Team.get_default_teams()
            else:
                teams = []
                for t in self.teams:
                    teams.append(Team.get_team_by_name(t))
                self.teams = teams
            if len(self.users) > 0:
                users = []
                for u in self.users:
                    users.append(User.get_user_by_name(u))
                self.users = users
            if len(self.teams) == 0 and len(self.users) == 0:
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
                            # now see if enough tries warrants paging the parent team
                            if len(alert_users) < num:
                                parent = Team.Team(team.parent)
                                alert_users = alert_users + parent.on_call()[:(num - len(alert_users))]
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

            #send email
            e = Email.Email(self.teams, self.users, self)
            if e.send_alert_email() == False:
                logging.error("Failed to send email for alert (%i)." % (self.id))
                # action if the email fails
                return False
            else:
                return True
        except Exception, e:
            Util.strace(e)
            return False

    def check_dependencies(self):
        '''
        Checks to see if the dependencies of this alert are in ok status or not. Return true if all are OK
        '''
        alerts = Mysql.query('''SELECT id from alerts where ack = false and status != 0 and (environment = "%s") and (colo = "" or colo = "%s") and (host = "" or host = "%s") and service = ""''' % (self.environment, self.colo, self.host), 'alerts')
        if len(alerts) > 0:
            return False
        else:
            return True

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
            self.createDate = self.createDate.strftime('%s')
        if hasattr(self, 'acktime') and type(self.acktime) is datetime.datetime:
            self.acktime = self.acktime.strftime('%s')
        if hasattr(self, 'lastAlertSent') and type(self.lastAlertSent) is datetime.datetime:
            self.lastAlertSent = self.lastAlertSent.strftime('%s')
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
