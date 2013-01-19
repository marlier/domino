#!/usr/bin/env python

import logging, urllib, datetime
import simplejson as json
from werkzeug.contrib.atom import AtomFeed
from datetime import date

import mysql_layer as Mysql
import twilio_layer as Twilio
import user_layer as User
import alert_layer as Alert
import team_layer as Team
import email_layer as Email
import rule_layer as Rule
import notification_layer as Notification
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("api")

class Api():
    '''
    This API class is designed to return json via http request
    '''
    def __init__(self, **data):
        '''
        Initialize the api class
        '''
        # set some default attribute values
        
        # default option vars
        self.limit = 25
        self.offset = 0
        self.search = ''
        self.since = 0
        self.sort = 'newest'
        
        # set defualt attr for teams
        self.oncall_count = 0
        self.twilio_token = conf['twilio_token']
        self.twilio_acct = conf['twilio_acct']
        self.twilio_number = conf['twilio_number']

        # graph data
        self.segment = 7
        self.unit = "DAY"
        
        # default json vars
        self.status_message = None
        
        # default user vars
        self.name = None
        self.phone = None
        self.email = None
        self.teams = None
        self.id = 0
        
        # default alert vars
        self.ack = 0
        self.message = None

        # default rule vars
        self.addTag = None
        self.removeTag = None
        self.environment = None
        self.colo = None
        self.host = None
        self.service = None
        self.status = None
        self.tag = None
        
        # default notification vars
        self.noteType = "email"
        self.format = "json"
        
        # convert the dictionary array received into Api class attributes
        self.__dict__.update(data)
        
        # making sure values are correct var type
        try:
            self.id = int(self.id)
        except Exception, e:
            self.populate(1003, "ID is not a integer")
            return
        try:
            self.segment = int(self.segment)
        except Exception, e:
            self.populate(1006, "Segment is not a integer")
            return
        try:
            self.limit = int(self.limit)
        except Exception, e:
            self.populate(1007, "Limit is not a integer")
            return
        try:
            self.offset = int(self.offset)
        except Exception, e:
            self.populate(1008, "Offset is not a integer")
            return
        try:
            self.since = int(self.since)
        except Exception, e:
            self.populate(1009, "Since is not a integer")
            return
        try:
            self.ack = int(self.ack)
        except Exception, e:
            self.populate(1012, "Ack is not a integer")
            return
        try:
            self.oncall_count = int(self.oncall_count)
        except Exception, e:
            self.populate(1013, "Oncall_count is not a integer")
            return

    def ackAlert(self, ack):
        '''
        Ack/Unack an alert
        '''
        try:
            alert = Alert.Alert(self.id)
            if ack == True:
                success = alert.ack_alert(0)
            else:
                success = alert.unack_alert()
            if success == True:
                alert.status = alert.status_wordform()
                alert.summary = alert.summarize()
                objects = self.processGetResults([alert])
                self.populate(200, "OK", objects)
                return
            else:
                self.populate(403, "Failed to ack alert")
        except Exception, e:
            self.populate(403,e.__str__())
            Util.strace(e)
            return

    def addaTag(self):
        ''' 
        Add tag to an alert
        '''
        try:
            alert = Alert.Alert(self.id)
            tags = alert.tags.split(',')
            if self.tag not in tags:
                tags.append(self.tag.strip())
            alert.tags = ",".join(tags)
            alert.save()
            alert.status = alert.status_wordform()
            alert.summary = alert.summarize()
            objects = self.processGetResults([alert])
            self.populate(200, "OK", objects)
            return
        except Exception, e:
            self.populate(1690,e.__str__())
            Util.strace(e)
            return

    def removeaTag(self):
        ''' 
        Remove tag to an alert
        '''
        try:
            alert = Alert.Alert(self.id)
            tags = alert.tags.split(',')
            if self.tag in tags:
                tags.remove(self.tag)
            alert.tags = ",".join(tags)
            alert.save()
            alert.status = alert.status_wordform()
            alert.summary = alert.summarize()
            objects = self.processGetResults([alert])
            self.populate(200, "OK", objects)
            return
        except Exception, e:
            self.populate(1691,e.__str__())
            Util.strace(e)
            return

    def getAlert(self):
        if self.id==0 or self.id == None:
            objects = Alert.get_alerts_with_filter(self.search, self.sort, self.limit, self.offset)
        else:
            objects = [Alert.Alert(self.id)]
        for o in objects:
            o.status = o.status_wordform()
            o.summary = o.summarize()
        dict_objects = []
        for o in objects:
            if hasattr(o, "scrub"):
                dict_objects.append(o.scrub())
        self.populate(200,"OK",dict_objects)

    def getHistory(self):
        if self.id==0 or self.id == None:
            objects = Alert.get_alerts_with_filter(self.search, self.sort, self.limit, self.offset, "alerts_history")
        else:
            objects = [Alert.Alert(self.id)]
        for o in objects:
            o.status = o.status_wordform()
            o.summary = o.summarize()
        dict_objects = []
        for o in objects:
            if hasattr(o, "scrub"):
                dict_objects.append(o.scrub())
        self.populate(200,"OK",dict_objects)

    def getUser(self):
        if self.id==0 or self.id == None:
            objects = User.all_users(self.since)
        else:
            objects = [User.User(self.id)]
        objects = self.processGetResults(objects)
        self.populate(200,"OK",objects)        

    def getTeam(self):
        if self.id==0 or self.id == None:
            objects = Team.all_teams(self.since)
        else:
            objects = [Team.Team(self.id)]
        objects = self.processGetResults(objects)
        self.populate(200,"OK",objects)

    def getNotification(self):
        if self.id==0 or self.id == None:
            objects = Notification.get_notifications(self.noteType, self.since, self.limit)
        else:
            objects = [Notification.Notification(self.id)]
        objects = self.processGetResults(objects)
        self.populate(200,"OK",objects)

    def getRule(self):
        if self.id==0 or self.id == None:
            if self.environment == '': self.environment = None
            if self.colo == '': self.colo = None
            if self.host == '': self.host = None
            if self.service == '': self.service = None
            if self.status == '': self.status = None
            if self.tag == '': self.tag = None
            objects = Rule.get_rules(self.environment, self.colo, self.host, self.service, self.status, self.tag)
        else:
            objects = [Rule.Rule(self.id)]
        for o in objects:
            o.status = o.status_wordform() 
        objects = self.processGetResults(objects)
        self.populate(200,"OK",objects)

    def getGraph(self):
        if self.unit.upper() in ["SECOND", "MINUTE", "HOUR", "DAY"]:
            data = Alert.graph_data(self.segment,self.unit,self.search)
            return self.populate(200,"OK",[data])
        else:
            self.populate(1802,"Invalid API metic call: units parameter must be SECOND, MINUTE, HOUR, or DAY") 

    def getAnalytics(self):
        if self.name == None:
            # return list of analytics names that are supported
            self.populate(200, "OK", ['frequent', 'count'])
        elif self.name == "frequent":
            objects = Alert.frequent_alerts(self.since)
            dict_objects = []
            objects = self.pagination(objects)
            for o in objects:
                if hasattr(o, "scrub"):
                    dict_objects.append(o.scrub())
                elif isinstance(o, dict):
                    dict_objects.append(o)
                else:
                    dict_objects.append(o.__dict__)
            self.populate(200,"OK",dict_objects)
        elif self.name == "count":
            objects = Alert.get_alerts_with_filter(self.search, self.sort, self.limit, self.offset, "alerts", True)
            self.populate(200, "OK",objects)
        else:
            self.populate(301, "Invalid analytics name")        

    def processGetResults(self, objects):
        objects = self.filter(objects)
        objects = self.sortit(objects)
        objects = self.pagination(objects)
        dict_objects = []
        for o in objects:
            if hasattr(o, "scrub"):
                dict_objects.append(o.scrub())
            elif isinstance(o, dict):
                dict_objects.append(o)
            else:
                dict_objects.append(o.__dict__)
        return dict_objects

    def sortit(self,objects):
        if self.sort != None and len(self.sort) > 0:
            if self.sort.lower() == "oldest":
                objects = objects[::-1]
                objects.sort(key = lambda x: x.createDate)
            elif self.sort.lower() == "newest":
                objects.sort(key = lambda x: x.createDate)
        return objects

    def pagination(self,objects):
        objects = objects[self.offset:]
        if self.limit > 0:
            objects = objects[:self.limit]
        return objects

    def setAlert(self,data):
        if self.id == None or self.id == 0:
            # create new alert
            # check to see if this alert is a new different than the one before it
            lastAlert = Alert.get_current_alert(self.environment, self.colo, self.host, self.service)
            alertFound = False
            if len(lastAlert) > 0:
                lastAlert = lastAlert[0]
                alertFound = True
            logging.info("Recieved alert submission")
            if alertFound == True and (lastAlert.service == self.service and lastAlert.status == int(self.status) and lastAlert.host == self.host and lastAlert.colo == self.colo and lastAlert.environment == self.environment):
                if lastAlert.message == self.message:
                    self.populate(200,"OK",json.dumps("Repeat alert"))
                else:
                    lastAlert.message = self.message
                    lastAlert.createDate = datetime.datetime.utcnow()
                    lastAlert.save()
                    self.populate(200,"OK",json.dumps("Repeat alert, updated message."))
            else:
                # save new alert to the db
                newalert = Alert.Alert()
                newalert.message = self.message
                newalert.host = self.host
                newalert.service = self.service
                newalert.colo = self.colo
                newalert.environment = self.environment
                tags = self.tags.split(',')
                # remove blank tags
                tags = filter (lambda a: a != '', tags)
                newalert.tags = ','.join(tags)
                newalert.remote_addr = self.remote_ip_address
                try:
                    if self.status is None:
                        newalert.status = 3
                    else:
                        newalert.status = int(self.status)
                except:
                    pass
                newalert.teams = Team.get_teams(self.teams)
                # apply inbound rules (if any)
                newalert.tags = Rule.applyRules(newalert)
                # save alert
                if newalert.save() == True:
                    # don't send an alert if its in OK status and is first time alert
                    if newalert.status == 0 and alertFound == False:
                        self.populate(200,"OK")
                    else:
                        if newalert.send_alert() == True:
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

    def setUser(self,data):
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
                self.populate(200,"OK")
                return
            else:
                self.populate(1305, "Failed to save user data")
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

    def setRule(self,data):
        if self.id is not None and self.id > 0:
            rule = Rule.Rule(self.id)
        else:
            rule = Rule.Rule()
        if self.environment != '': rule.environment = self.environment
        if self.colo != '': rule.colo = self.colo
        if self.host != '': rule.host = self.host
        if self.service != '': rule.service = self.service
        if self.status != '' or self.status is None:
            if self.status is None:
                rule.status = None
            else:
                rule.status = Alert.to_int_status(self.status)
        if self.tag != '': rule.tag = self.tag
        if self.addTag != '': rule.addTag = self.addTag
        if self.removeTag != '': rule.removeTag = self.removeTag
        if rule.save():
            self.populate(200, "OK", [rule.__dict__])
        else:
            self.populate(1910, "Failed to save rule")
            
    def setTeam(self,data):
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
        else:
            try:
                obj = Team.Team(self.id)
                # save the original members of the team to see if its changed
                orig_members = User.get_users(self.members)
                obj.__dict__.update(data)
                obj.members = User.get_users(self.members)
                if obj.save() == True:
                    # SMS the delta of whose on call
                    obj.notifyOncallChange(orig_members)
                    self.populate(200,"OK")
                else:
                    self.populate(701,"Failed to save team.")
            except Exception, e:
                self.populate(1602,e.__str__())
                Util.strace(e)
                return

    def rotateTeam(self):
        if self.id == None or self.id == 0:
            self.populate(403, "Error: failed to give a valid team id")
        else:
            team = Team.Team(self.id)
            orig_members = team.members
            for i in range(self.count):
                team.members.append(team.members.pop(0))
            if team.save():
                team.notifyOncallChange(orig_members)
                self.populate(200, "OK")
            else:
                self.populate(403, "Failed to save team")

    def delAlert(self):
        try:
            obj = Alert.Alert(self.id)
            obj.delete()
            self.populate(200,"OK")
        except Exception, e:
            self.populate(1502,e.__str__())
            Util.strace(e)
            return 

    def delUser(self):
        try:
            obj = User.User(self.id)
            obj.delete()
            self.populate(200,"OK")
        except Exception, e:
            self.populate(1502,e.__str__())
            Util.strace(e)
            return

    def delTeam(self):
        try:
            obj = Team.Team(self.id)
            obj.delete()
            self.populate(200,"OK")
        except Exception, e:
            self.populate(1502,e.__str__())
            Util.strace(e)
            return

    def delRule(self):
        try:
            obj = Rule.Rule(self.id)
            obj.delete()
            self.populate(200,"OK")
        except Exception, e:
            self.populate(1502,e.__str__())
            Util.strace(e)
            return

    def reg_phone(self):
        user = User.User(self.id)
        valid_code = Twilio.validate_phone(user)
        if valid_code['success'] == False:
            self.populate(404,valid_code['message'])
        elif valid_code['success'] == True:
            self.populate(200, "OK", {'verification_code': valid_code['message']})

    def dereg_phone(self):
        user = User.User(self.id)
        if Twilio.invalidate_phone(user):
            self.populate(200,"OK")
        else:
            self.populate(404, "failed")

    def sms_test(self):
        user = User.User(self.id)
        auth = Twilio.auth()
        try:
            auth.sms.messages.create(to=user.phone, from_=conf['twilio_number'], body="This is a test SMS message from Domino. Looks like you got it. Yay!")
            self.populate(200, "OK")
        except Exception, e:
            Util.strace(e)
            self.populate(404, "Fail: %s" % (e.__str__))

    def filter(self,objects):
        '''
        Filter objects 
        '''
        if self.search == None or len(self.search) == 0: return objects
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
                        if comp_val.startswith("-"):
                            comp_val = comp_val[1:].strip()
                            if comp_val.lower() in vals:
                                all_search_criteria_met.append(False)
                            else:
                                all_search_criteria_met.append(True)
                        else:
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
                filtered_objects.insert(0,o)
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
        # generate XML RSS (Atom) feed
        if self.format == "xml" and self.objType == "Notification":
            feed = AtomFeed('Domino Notification Feed', feed_url=self.fullurl)
            for x in self.data:
                createDate = datetime.datetime.strptime(x['createDate'], '%Y-%m-%dT%H:%M:%S')
                feed.add("%s: %s" % (x['noteType'], x['id']), unicode(x['message']), id=x['id'], content_type="text", url=x['link'], updated=createDate, published=createDate)
            self.feed = feed.get_response()
        else:
            self.fulljson = json.dumps(self.data, skipkeys=True, sort_keys=True, indent=4 * ' ')
