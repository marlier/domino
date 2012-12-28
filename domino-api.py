#!/usr/bin/env python
# This runs as a service. It listens for API requests

from flask import Flask, request, json, make_response, render_template, url_for
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

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'www/templates')
static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'www/static')

app = Flask(__name__, template_folder=tmpl_dir, static_folder=static_dir)

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

@app.route('/api/alert/<int:id>/addtag/<tag>', methods=['POST', 'OPTIONS'])
def addTag(id=0,tag=None):
    data = {}
    apicall = Api.Api(**data)
    apicall.id = id
    apicall.tag = tag
    print apicall.__dict__
    apicall.addaTag()
    resp = make_response(apicall.fulljson)
    resp.status = "%s %s" % (apicall.status, apicall.status_message)
    return resp 

@app.route('/api/alert/<int:id>/removetag/<tag>', methods=['POST', 'OPTIONS'])
def removeTag(id=0,tag=None):
    data = {}
    apicall = Api.Api(**data)
    apicall.id = id
    apicall.tag = tag 
    print apicall.__dict__
    apicall.removeaTag()
    resp = make_response(apicall.fulljson)
    resp.status = "%s %s" % (apicall.status, apicall.status_message)
    return resp

@app.route('/api/alert/<int:id>/ack', methods=['POST', 'OPTIONS'])
def ack_alert(id=0):
    apicall = Api.Api()
    apicall.id = id
    apicall.ack(id)
    resp = make_response(apicall.fulljson)
    resp.status = "%s %s" % (apicall.status, apicall.status_message)
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
        elif objType == "addTag":
            apicall.addTag()
    elif request.method == 'DELETE':
        if objType == "Alert":
            apicall.delAlert()
        elif objType == "User":
            apicall.delUser()
        elif objType == "Rule":
            apicall.delRule()
        elif objType == "Team":
            apicall.delTeam()
    if 'format' in data and data['format'] == "xml" and objType == "Notification":
        resp = make_response(apicall.feed)
    else:
        if hasattr(apicall, 'fulljson'):
            resp = make_response(apicall.fulljson)
            resp.status = "%s %s" % (apicall.status, apicall.status_message)
        else:
            resp = make_response(404)
    return resp

##### web ui ######
@app.route('/')
@app.route('/index.html')
@app.route('/dash')
@app.route('/dashboard')
@app.route('/dashboards')
def index():
    return render_template('index.html')

@app.route('/alert')
@app.route('/alerts')
def alerts():
    return render_template('alerts.html')

@app.route('/rule')
@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/team')
@app.route('/teams')
def teams():
    return render_template('teams.html')

@app.route('/user')
@app.route('/users')
def users():
    return render_template('users.html')

@app.route('/detail')
@app.route('/details')
def detail():
    return render_template('detail.html')

with app.test_request_context():
    url_for('static', filename="dash.js")
    url_for('static', filename="alerts.js")
    url_for('static', filename="detail.js")
    url_for('static', filename="teams.js")
    url_for('static', filename="users.js")
    url_for('static', filename="disclosureTriangle.png")
    url_for('static', filename="base.css")
    url_for('static', filename="jquery-ui.css")
    url_for('static', filename="colorbox.css")

if __name__ == "__main__":
    app.run(port=conf['api_port'], host=conf['api_listen_ip'], debug=conf['server_debug'])
