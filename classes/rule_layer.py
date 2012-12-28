#!/usr/bin/env python

import logging
import datetime

import mysql_layer as Mysql
import util_layer as Util

def applyRules(alert):
    '''
    Get all the rules that can be applied to the specified alert and apply them
    '''
    rules = get_rules(alert.environment, alert.colo, alert.host, alert.service, alert.status, alert.tag)
    for rule in rules:
        tags = alert.tags.split(',')
        if rule['addTag'] != 'NULL' and rule['addTag'] is not None:
            for tag in rule['addTag'].split(','):
                if tag not in tags: tags.append(tag.strip())
        if rule['removeTag'] != 'NULL' and rule['removeTag'] is not None:
            for tag in rule['removeTag'].split(','):
                if tag in tags: tags.remove(tag)
    alert.tags = ",".join(tags)
    return alert.tags

def get_rules(environment, colo, host, service, status, tag):
    '''
    return a list of rule objections
    '''
    rules = []
    all_rules = Mysql.query('''select * from inbound_rules''', 'inbound_rules')
    if None == environment == colo == host == service == status == tag:
        return all_rules
    for rule in all_rules:
        print rule.__dict__
        if compare_rule_vals(rule.environment, environment) is False: continue
        print 'passed env'
        if compare_rule_vals(rule.colo ,colo) is False: continue
        print 'passed colo'
        if compare_rule_vals(rule.host ,host) is False: continue
        print 'passed host'
        if compare_rule_vals(rule.service ,service) is False: continue
        print 'passed service'
        if compare_rule_vals(rule.status ,status) is False: continue
        print 'passed status'
        if rule.tag is not None:
            if tag is not None:
                if tag.lower() not in rule.tag.lower().split(','): continue
        print 'passed tags'
        rules.append(rule);
    return rules

def compare_rule_vals(rule_val, my_val):
    print rule_val, my_val
    if rule_val is None: return True
    if my_val is not None:
        if rule_val.lower() != my_val.lower():
            return False
        else:
            return True
    else:
        return False
    return True

class Rule:
    def __init__(self, id=0):
        ''' 
        This initializes a rule object. If id is given, loads that rule. If not, creates a new rule object with default values.
        '''
        logging.debug("Initializing rule: %s" % id) 

        if id == 0:
            self.colo = None
            self.host = None
            self.service = None
            self.environment = None
            self.tag = None
            self.status = None
            self.addTag = None
            self.removeTag = None
            self.id = id
        else:
            self.load(id)
            self.id = int(id)

    def load(self, id):
        '''
        Load a rule with a specific id.
        '''
        logging.debug("Loading rule: %s" % id)
        try:
            self.__dict__.update(Mysql.query('''SELECT * FROM inbound_rules WHERE id = %s LIMIT 1''' % (id), 'inbound_rules')[0].__dict__)
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
        Save rule
        '''
        logging.debug("Saving rule: %s" % self.id)
        mysql_col = []
        mysql_val = []
        for key in self.__dict__:
            if self.__dict__[key] is not None:
                mysql_col.append(key)
                if isinstance(self.__dict__[key], int):
                    mysql_val.append('%s' % self.__dict__[key])
                else:
                    mysql_val.append('"%s"' % self.__dict__[key])
        return Mysql.save('''REPLACE INTO inbound_rules (%s) VALUES (%s)''' % (','.join(mysql_col), ','.join(mysql_val)))

    def delete(self):
        '''
        Delete a rule from the database
        '''
        logging.debug("Deleting rule: %s" % self.id)
        return Mysql.delete('inbound_rules', self.id)

    def print_rule(self, SMS=False):
        '''
        Print out contents of a rule. SMS variable makes it SMS friendly. 
        '''
        ## FIXME

    def scrub(self):
        ''' 
        This convert the rule to a dict
        '''
        if hasattr(self, 'createDate') and type(self.createDate) is datetime.datetime:
            self.createDate = self.createDate.isoformat()
        return self.__dict__
