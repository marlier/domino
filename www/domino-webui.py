#!/usr/bin/env python
# This runs as a service. It listens for API requests

from flask import Flask, render_template, url_for
import os, sys
import urllib
import logging
import time

# add classes location to sys.path
cmd_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if (cmd_folder + "/classes") not in sys.path:
	sys.path.insert(-1, cmd_folder + "/classes")

import util_layer as Util

conf = Util.load_conf()
Util.init_logging("webui")

app = Flask(__name__)

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

@app.route('/static/js/lib.js')
def libjs(api_address=conf['api_address'], api_port=conf['api_port']):
	return render_template('lib.js', api_address=api_address, api_port=api_port)


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
	app.run(port=conf['webui_port'], host=conf['webui_listen_ip'], debug=conf['server_debug'])
