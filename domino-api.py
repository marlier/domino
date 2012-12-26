#!/usr/bin/env python
# This runs as a service. It listens for API requests

from flask import Flask, request, json, make_response
import os, sys
import urllib
import logging
import time
from datetime import timedelta

# add classes location to sys.path
cmd_folder = os.path.dirname((os.path.abspath(__file__)))
if (cmd_folder + "/classes") not in sys.path:
    sys.path.insert(-1, cmd_folder + "/classes")

import api_layer as Api
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("api")

app = Flask(__name__)

@app.route('/api/healthcheck')
def healthcheck():
    '''
    This checks the system to see if capable of handling api requests
    '''
    return Util.healthcheck("alert")


@app.route('/api/alert', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
@app.route('/api/alert/<int:id>', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
def alert_instance(id=0):
    return process_request("Alert", id)

@app.route('/api/alert/<int:id>/ack', methods=['POST', 'OPTIONS'])
def ack_alert(id=0):
    apicall = Api.Api(**data)
    apicall.id = id
    apicall.ack(id)
    resp = make_response(apicall.fulljson)
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

@app.route('/api/user', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
@app.route('/api/user/<int:id>', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
def user_instance(id=0):
    return process_request("User", id)
    
@app.route('/api/team', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
@app.route('/api/team/<int:id>', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
def team_instance(id=0):
    return process_request("Team", id)

@app.route('/api/rule', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
@app.route('/api/rule/<int:id>', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
def rule_instance(id=0):
    return process_request("Rule", id)

@app.route('/api/notification', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
@app.route('/api/notification/<int:id>', methods=['GET', 'POST', 'DELETE', 'OPTIONS'])
def note_instance(id=0):
    return process_request("Notification", id)

@app.route('/api/history', methods=['GET'])
def alerthistory():
    return process_request("History")

@app.route('/api/analytics', methods=['GET'])
def analytics():
    return process_request("Analytics")

@app.route('/api/graph', methods=['GET'])
def graph():
    return process_request("Graph")

def process_request(objType, id=0):
    '''
    Handles all incoming requests.
    '''
    if request.headers['Content-Type'] == 'application/json':
        data = request.json
    else:
        rawdata = request.args
        data = {}
        # converting from multidict to dict
        for key, value in rawdata.items():
            data[key] = value
    # add remote ip address to dict
    data['remote_ip_address'] = request.remote_addr
    data['fullurl'] = request.url
    logging.info("Receiving a api request for %s( id:%d )\n%s" % (objType, id, data))
    apicall = Api.Api(**data)
    apicall.id = id
    apicall.objType = objType
    if request.method == 'GET':
        if objType == "Alert":
            apicall.getAlert()
        elif objType == "User":
            apicall.getUser()
        elif objType == "Team":
            apicall.getTeam()
        elif objType == "Rule":
            apicall.getRule()
        elif objType == "Notification":
            apicall.getNotification()
        elif objType == "History":
            apicall.getHistory()
        elif objType == "Analytics":
            apicall.getAnalytics()
        elif objType == "Graph":
            apicall.getGraph()
    elif request.method == 'POST':
        if objType == "Alert":
            apicall.setAlert(data)
        elif objType == "User":
            apicall.setUser(data)
        elif objType == "Rule":
            apicall.setRule(data)
        elif objType == "Team":
            apicall.setTeam(data)
    elif request.method == 'DELETE':
        if objType == "Alert":
            apicall.delAlert()
        elif objType == "User":
            apicall.delUser()
        elif objType == "Rule":
            apicall.delRule()
        elif objType == "Team":
            apicall.delTeam()
    elif request.method == 'OPTIONS':
        resp = make_response()
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        resp.headers['Access-Control-Allow-Origin'] = '*'
        resp.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        resp.headers['Access-Control-Max-Age'] = 1000
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return resp
    if 'format' in data and data['format'] == "xml" and objType == "Notification":
        resp = make_response(apicall.feed)
    else:
        resp = make_response(apicall.fulljson)
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp

if __name__ == "__main__":
    app.run(port=conf['api_port'], host=conf['api_listen_ip'], debug=conf['server_debug'])
