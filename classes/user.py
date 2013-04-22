#!/usr/bin/env python

import logging
import datetime

from cloudant import Cloudant
import team as Team
import domino_twilio as twilio
import util as Util

def all_users():
    '''
    Get all users from the db.
    '''
    c = Cloudant()
    return c.view("users/all")
        
def get_users(user_ids):
    '''
    Get a list of users by ids, which is comma separated
    '''
    users = []
    for t in user_ids:
        users.append(User(t))
    return users

def get_user_names():
    ''' 
    Return an array of all user names
    '''
    names = []
    for user in all_users():
        names.append(user.name)
    return names

def flatten_users(users):
    '''
    Flatten a list of user objects in a comma separated user id list
    '''
    if len(users) > 0 and isinstance(users, list):
        tmp = []
        for u in users:
            tmp.append(u._id)
        return tmp
    else:
        return None

def get_user_by_name(name):
    ''' 
    Return a user object by giving the name of that user
    '''
    for user in all_users():
        if name == user.name:
            return user
    return False

def get_user_by_phone(phone):
    '''
    Load user by their phone number (pattern matching by 'ends with')
    '''
    try:
        for user in all_users():
            if phone.startswith(user.phone):
                return user
        return False
    except Exception, e:
        Util.strace(e)
        return False

class User:
    def __init__(self, _id=0):
        '''
        This initializes a user object. If id is given, loads that user. If not, creates a new user object with default values.
        '''
        logging.debug("Initializing user: %s" % _id)

        if _id == 0:
            self.name = ''
            self.phone = ''
            self.email = ''
            self.lastAlert = 0
            self.type = "user"
        else:
            self.load(_id)

    def load(self, _id):
        '''
        load a user with a specific id
        '''
        logging.debug("Loading user: %s" % _id)
        try:
            c = Cloudant()
            self.__dict__.update(c.get(_id))
        except Exception, e:
            Util.strace(e)
            return False
    
    def save(self):
        '''
        Save the user to the db.
        '''
        logging.debug("Saving user: %s" % self.name)
        c = Cloudant()
        return c.save(self.__dict__)
    
    def scrub(self):
        '''
        This scrubs the user from objects in the user object. This is mainly used to make the user convertable to json format.
        '''
        return self.__dict__
        
            
    def delete(self):
        '''
        Delete the user form the db.
        '''
        logging.debug("Deleting user: %s" % self.name)
        c = Cloudant()
        return c.delete(self._id)
            
    def print_user(self, SMS=False):
        '''
        Print out the contents of a user object. SMS variable makes output SMS friendly.
        '''

        if SMS == True:
            output = "name:%s\nphone: %s \n" % (self.name, self.phone)
        else:
            output = "id:%i\nname:%s\nphone:%s\nemail:%s\n" % (self.id, self.name, self.phone, self.email)
        logging.debug("Printing user: %s" % output)
        return output
