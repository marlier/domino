#!/usr/bin/env python

import logging
import datetime

from cloudant import Cloudant
import user as User
import util as Util

conf = Util.load_conf()

def all_teams():
    '''
    Get all teams from the db.
    '''
    c = Cloudant()
    return c.view("teams/all")

def get_team_names():
    '''
    Return an array of all team names
    '''
    names = []
    teams = all_teams()
    for team in teams:
        names.append(team.name)
    return names

def get_teams(_ids):
    '''
    Get a list of teams by ids or name, which is comma separated
    '''
    if teams_raw == None: return []
    teams = []
    for _id in _ids:
        teams.append(Team(_id))
    return teams

def flatten_teams(teams):
    '''
    Flatten a list of user objects in a comma separated user id list
    '''
    if len(teams) > 0 and isinstance(teams, list):
        tmp = []
        for t in teams:
            tmp.append(t.id)
        return tmp
    else:
        return None
        
def get_default_teams():
    '''
    Return the default team
    '''
    teams = []
    for team in all_teams():
        if team.catchall == True:
            teams.append(team)
    return teams

def get_team_by_name(name):
    '''
    Return a team object by giving the name of that team
    '''
    teams = []
    for team in all_teams():
        if team.name == name:
            teams.append(team)
    return teams

def check_user(user, team):
    '''
    This fuction checks if a specific user is a member of a specific team
    '''
    for u in team.members:
        if user._id == u._id:
            return True
    return False
    
class Team:
    def __init__(self, _id=0, users=True):
        '''
        This initializes a team object. If id is given, loads that team. If not, creates a new team object with default values.
        '''
        logging.debug("Initializing team: %s" % id)

        if _id == 0:
            self.name = ''
            self.email = ''
            self.members = []
            self.catchall = False
            self.parent = 0
            self.oncall_count = 1
            self.phone = conf['twilio_number']
            self._id = _id
        else:
            self.load(_id, users)
            
    def load(self, _id, users=True):
        '''
        load a team with a specific id
        '''
        logging.debug("Loading team: %s" % _id)
        
        try:
            c = Cloudant()
            self.__dict__.update(c.get(_id))
        except Exception, e:
            Util.strace(e)
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
        c = Cloudant()
        return c.save(self.__dict__)
            
    def delete(self):
        '''
        Delete the team form the db.
        '''
        logging.debug("Deleting team: %s" % self.name)
        c = Cloudant()
        return c.delete(self._id)

    def notifyOncallChange(self,orig):
        '''
        This method sends sms messages to tell people that whose on call has been changed
        '''
        # send sms to everyone whose oncall (only if their place has changed)
        current_member_ids = []
        for i, u in enumerate(self.members):
            current_member_ids.append(u.id)
            if orig[i].id != u.id and int(self.oncall_count) > (i):
                # send sms to u
                Twilio.send_sms(u, self, None, "You're now on call for team %s in spot %d" % (self.name, (i+1)))
        # notify people who are no longer on call
        orig_oncall = orig[:int(self.oncall_count)]
        current_oncall = current_member_ids[:int(self.oncall_count)]
        for u in orig_oncall:
            if u.id not in current_oncall:
                # send sms to u for not being oncall
                Twilio.send_sms(u, self, None, "You're no longer on call for team %s" % (self.name))
            
    def scrub(self):
        '''
        This scrubs the team from objects in the tean object. This is mainly used to make the user convertable to json format.
        '''
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
