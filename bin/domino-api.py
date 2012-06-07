#!/usr/bin/env python
# This runs as a service. It listens for API requests

import web
import os, sys
import urllib
import logging
import time

# add this file location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if cmd_folder not in sys.path:
     sys.path.insert(-1, cmd_folder)
     sys.path.insert(-1, cmd_folder + "/classes")

import api_layer as API
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("api")

# set port and IP to listen for alerts
# these are inhereited from the conf file
sys.argv = [conf['api_listen_ip'],conf['api_port']]

# debug mode
web.config.debug = conf['server_debug']

#load valid urls to listen to for http calls
urls = (
    '/api/(.+)', 'api',
    '/healthcheck', 'healthcheck'
)
app = web.application(urls, globals())

class healthcheck:
	'''
	This checks the system to see if capable of handling api requests
	'''
	def GET(self):
		return Util.healthcheck()
	def POST(self):
		return Util.healthcheck()

class api:
	'''
	This class handles new alerts being set to the Domino server
	'''
	def GET(self,name):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		data = web.input(action=name)
		logging.info("Receiving a GET api query\n%s" % (data))
		apicall = API.Api(**data)
		return apicall.fulljson
	
	def POST(self, name):
		web.header('Access-Control-Allow-Origin',      '*')
		web.header('Access-Control-Allow-Credentials', 'true')
		data = web.input(action=name)
		logging.info("Receiving a POST api query\n%s" % (data))
		apicall = API.Api(**data)
		return apicall.fulljson

if __name__ == "__main__":
	app.run()