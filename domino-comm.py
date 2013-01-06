#!/usr/bin/env python
# this is a service that listens for traffic from Twilio's servers
# this also sends out repeat alerts when appropriate to

from flask import Flask, request, Response
import os, sys
import urllib
import logging
import time
from multiprocessing import Process

# add classes location to sys.path
cmd_folder = os.path.dirname((os.path.abspath(__file__)))
if (cmd_folder + "/classes") not in sys.path:
    sys.path.insert(-1, cmd_folder + "/classes")

import twilio_layer as Twilio
import dominoCLI as domino
import user_layer as User
import alert_layer as Alert
import team_layer as Team
import rule_layer as Rule
import util_layer as Util

conf = Util.load_conf()
Util.init_logging("comm")

app = Flask(__name__)

@app.route('/api/healthcheck')
def healthcheck():
    '''
    This checks the system to see if capable of handling api requests
    '''
    return Util.healthcheck("comm")

@app.route('/sms', methods=['GET'])
def sms():
    '''
    This class handles SMS messages
    '''
    rawdata = request.args
    d = {}
    # converting from multidict to dict
    for key, value in rawdata.items():
        d[key] = value  
    logging.info("Receiving SMS message\n%s" % (d))
    r = Twilio.twiml.Response()
    user = User.get_user_by_phone(d['From'])
    team = Team.get_team_by_phone(d['To'])[0]
    # make sure person sending the text is an authorized user of Domino
    if user == False:
        logging.error("Unauthorized access attempt via SMS by %s\n%s" % (d['From'], d))
        r.sms("You are not an authorized user")
    else:
        # split the output into 160 character segments
        for text_segment in Twilio.split_sms(domino.run("%s -m -t %s -f %s" %(d['Body'],team.name,d['From']))):
            r.sms(text_segment)
    return str(r)

@app.route('/call/<int:alert_id>', methods=['GET'])
def outboundcall():
    '''
    This class handles phone calls that were initiated by Domino to notify someone of an alert. (outbound phone calls)
    ''' 
    rawdata = request.args
    d = {}
    # converting from multidict to dict
    for key, value in rawdata.items():
        d[key] = value
    if "init" not in d: d['init'] = "true"
    if "Digits" not in d: d['Digits'] = 0
    logging.info("Receiving phone call\n%s" % (d))
    r = Twilio.twiml.Response()
    # the message to say when a timeout occurs
    timeout_msg = "Sorry, didn't get any input from you. Goodbye."
    # check if this call was initialized by sending an alert
    # the digit options to press
    digitOpts = '''
Press 1 to hear the message.
Press 2 to acknowledge this alert.
'''
    receiver = User.get_user_by_phone(d['To'])
    alert = Alert.Alert(alert_id)
    # check if this is the first interaction for this call session
    if d['init'].lower() == "true":
        with r.gather(action="%s:%s/call/%s?init=false" % (conf['server_address'],conf['port'],alert.id), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
            g.say('''Hello %s, a message from Domino. An alert has been issued with subject "%s". %s.''' % (receiver.name, alert.subject, digitOpts))
        r.say(timeout_msg)
    else:
        if int(d['Digits']) == 1:
            with r.gather(action="%s:%s/call/%s?init=false" % (conf['server_address'],conf['port'],alert.id), timeout="30", method="POST", numDigits="1") as g:
                g.say('''%s. %s''' % (alert.message, digitOpts))
            r.say(timeout_msg)
        elif int(d['Digits']) == 2:
            if alert.ack_alert(receiver):
                r.say("The alert has been acknowledged. Thank you and goodbye.")
                r.redirect(url="%s:%s/call/%s?init=false" % (conf['server_address'],conf['port'],alert.id))
            else:
                r.say("Sorry, failed to acknowledge the alert. Please try it via SMS")
                r.redirect(url="%s:%s/call/%s?init=false" % (conf['server_address'],conf['port'],alert.id))
        elif d['Digits'] == 0:
            with r.gather(action="%s:%s/call/%s?init=false" % (conf['server_address'],conf['port'],alert.id), timeout="30", method="POST", numDigits="1") as g:
                g.say('''%s''' % (digitOpts))
            r.say(timeout_msg)
        else:
            r.say("Sorry, didn't understand the digits you entered. Goodbye")
    return str(r)

@app.route('/call', methods=['GET'])
def inboundcall():
    '''
    This class handles phone calls initiated by a person (inbound phone calls)
    ''' 
    rawdata = request.args
    d = {}
    # converting from multidict to dict
    for key, value in rawdata.items():
        d[key] = value
    if "init" not in d: d['init'] = "true"
    if "Digits" not in d: d['Digits'] = 0
    logging.info("Receiving phone call\n%s" % (d))
    r = Twilio.twiml.Response()
    # the message to say when a timeout occurs
    timeout_msg = "Sorry, didn't get any input from you. Goodbye."
    # check if this call was initialized by sending an alert
    requester = User.get_user_by_phone(d['From'])
    # get the team that is associate with this phone number the user called
    team = Team.get_team_by_phone(d['To'])[0]
    oncall_users = team.on_call()
    # if caller is not a oncall user or they are, but calling a different team then they are in
    if requester == False or Team.check_user(requester, team) == False:
        if team == '':
            r.say("Sorry, The phone number you called is not associated with any team. Please contact you system administrator for help.")
        else:
            # get the first user on call and forward the call to them
            if len(oncall_users) > 0:
                for user in oncall_users:
                    r.say("Calling %s." % user.name)
                    r.dial(number=user.phone)
            else:
                r.say("Sorry, currently there is no one on call for %s. Please try again later." % team)
    else:
        # the caller is calling the same team phone number as the team that they are on
        # check if d.Digits is the default value (meaning, either the caller hasn't pushed a button and this is the beginning of the call, or they hit 0 to start over
        if int(d['Digits']) == 0:
            if d['init'].lower() == "true":
                if Team.check_oncall_user(requester, team) == True:
                    # figure out where in line the user is on call
                    for i,u in enumerate(team.members):
                        if requester.id == u.id:
                            oncall_status = "You are currently on call in spot %s" % (i + 1)
                            break
                else:
                    if len(oncall_users) > 0:
                        oncall_status = "Currenty, %s is on call" % (oncall_users[0].name)
                    else:
                        oncall_status = "Currenty, no one is on call"
                with r.gather(action="%s:%s/call?init=false" % (conf['server_address'],conf['port']), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
                    g.say('''Hello %s. %s. Press 1 if you want to hear the present status of alerts. Press 2 to acknowledge the last alert sent to you. Press 3 to conference call everyone on call into this call.''' % (requester.name, oncall_status))
            else:
                with r.gather(action="%s:%s/call?init=false" % (conf['server_address'],conf['port']), timeout=conf['call_timeout'], method="POST", numDigits="1") as g:
                    g.say('''Press 1 if you want to hear the present status of alerts. Press 2 to acknowledge the last alert sent to you. Press 3 to conference call everyone on call into this call.''')
            r.say(timeout_msg)
        elif int(d['Digits']) == 1:
            # getting the status of alerts
            r.say(domino.run("alert status -f " + requester.phone))
            r.redirect(url="%s:%s/call?init=false" % (conf['server_address'],conf['port']))
        elif int(d['Digits']) == 2:
            # acking the last alert sent to the user calling
            r.say(domino.run("alert ack -f " + requester.phone))
            r.redirect(url="%s:%s/call?init=false" % (conf['server_address'],conf['port']))
        elif int(d['Digits']) == 3:
            # calling the other users on call
            if len(oncall_users) == 1 and Team.check_oncall_user(requester, team) == True:
                r.say("You're the only person on call. I have no one to forward you to.")
            else:
                if len(oncall_users) > 0:
                    for user in oncall_users:
                        if user.id != requester.id:
                            r.say("Calling %s." % user.name)
                            r.dial(number=user.phone)
                else:   
                    r.say("Sorry, no one is currently on call to forward you to.")
        else:
            r.say("Sorry, number you pressed is not valid. Please try again.")
    return str(r)

def check_alerts():
    '''
    This function runs in an infinite loop to find any unacked alerts that need an alert to be sent out.
    '''
    # intentionally creating an infinite loop.
    foobar = True
    while foobar == True:
        # delete any rules that have expired
        Rule.expire_rules();

        # looking for alerts that are due to page
        for a in Alert.check_alerts():
            a.send_alert()
        time.sleep(5)

if __name__ == "__main__":
    p = Process(target=check_alerts)
    p.start()
    app.run(port=conf['port'], host=conf['listen_ip'], debug=conf['server_debug'])
