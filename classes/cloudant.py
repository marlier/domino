#!/usr/bin/env python

import logging
import couchdb

import util as Util

conf = Util.load_conf()

class Cloudant:
    def __init__(self):
        '''
        Initialize the cloudant db
        '''
        try:
            self.cloudant = couchdb.Server("https://%s:%s@%s.cloudant.com" % (conf['cloudant_api_key'], conf['cloudant_api_passwd'], conf['cloudant_username']))
            if conf['cloudant_db_name'] in self.cloudant:
                self.db = self.cloudant[conf['cloudant_db_name']]
            else:
                logging.error("Cannot connect to db, creating new one....")
                self.cloudant.create(conf['cloudant_db_name'])
                self.db = self.cloudant[conf['cloudant_db_name']]
        except Exception, e:
            Util.strace(e)
            return False

    def save(self, d):
        '''
        Save a doc
        '''
        try:
            self.db.save(d)
        except Exception, e:
            Util.strace(e)
            return False

    def delete(self, d):
        '''
        Delete a doc
        '''
        # if passed a dictionary, get _id, other assume _id passed
        if isinstance(d, dict):
            if "_id" in d:
                _id = d['_id']
        else:
            _id = d
        try:
            del self.db[_id]
        except Exception, e:
            Util.strace(e)
            return False        

    def get(self, _id):
        '''
        Get a doc by _id
        '''
        try:
            return self.db.get(_id)
        except Exception, e:
            Util.strace(e)
            return False

    def healthcheck(self):
        '''
        Test database
        '''
        try:
            test_doc = {}
            test_doc['id'] = "test_doc"
            test_doc['name'] = "test"
            test_doc['type'] = "test"
            if self.db.save(test_doc) and self.db.delete(test_doc):
                return True
            else:
                return False
        except Exception, e:
            Util.strace(e)
            return False
