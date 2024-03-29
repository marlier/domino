#!/usr/bin/env python
# twilio layer

import logging

from twilio.rest import TwilioRestClient
from twilio import twiml

import user as User
import alert as Alert
import team as Team
import util as Util

conf = Util.load_conf()

def auth():
	'''
	This method finds the appropriate twilio account and token info for the user to use and authenticates with twilio.
	'''
	logging.debug("Authenticating with twilio: %s:%s" % (conf['twilio_acct'], conf['twilio_token']))
	try:
		return TwilioRestClient(conf['twilio_acct'], conf['twilio_token'])
	except Exception, e:
		logging.error("Failed to authenticate with the twilio credentials")
		Util.strace(e)
		return False

def split_sms(sms):
	'''
	This function splits an sms messages into 160 character list, so it can send parts of message in 160 char segments.
	'''
	if len(sms) > 160:
		output = []
		while len(sms) > 160:
			output.append(sms[:160])
			sms = sms[160:]
		if len(sms) > 0: output.append(sms)
		return output
	else:
		return [sms]
    
def send_sms(user=None, team=None, alert=None, _message="Nothing"):
	'''
	This method sends a text message to a user.
	'''
	logging.debug("Sending sms message to: %s, %s" % (user.name, _message))
	if alert != None:
		user.lastAlert = alert.id
		user.save()
	myauth = auth()
	for i,text_segment in enumerate(split_sms(_message)):
		if i < conf['text_limit']:
			myauth.sms.messages.create(to=user.phone, from_=team.phone, body=text_segment)
		elif i == conf['text_limit']:
			text_segment = text_segment[:-3] + '...'
			myauth.sms.messages.create(to=user.phone, from_=team.phone, body=text_segment)
		else:
			break

def make_call(user=None, team=None, alert=None):
	'''
	This method calls a user about an alert.
	'''
	logging.debug("Calling user: %s" % user.name)
	user.lastAlert = alert.id
	user.save()
	return auth().calls.create(to=user.phone, from_=team.phone, url='''%s:%s/call/%s?init=True''' % (conf['server_address'],conf['port'],alert.id))
	
def validate_phone(user):
	'''
	This method attempts to authenticate a user's phone number with Twilio.
	'''
	logging.debug("Creating validation code for new phone number/user")
	try:
		response = auth().caller_ids.validate(user.phone)
                logging.debug(response)
                logging.debug(response["validation_code"])
		return {"success":True, "message" : response["validation_code"]}
	except Exception, e:
		if e.status == 400:
			return {"success":False, "message":e.__str__()}
		else:
			Util.strace(e)
			return {"success":False, "message":e.__str__()}

def invalidate_phone(user):
    '''
    This method deletes a phone number from twilio's servers
    '''
    logging.debug("Deleting phone number")
    try:
        response = auth().caller_ids.list(phone_number=user.phone)
        if len(response) > 0:
            response[0].delete()
        return True
    except Exception, e:
        Util.strace(e)
        return False

def healthcheck():
	logging.info("Performing twilio healthcheck.")
	if auth():
		logging.info("Twilio healthcheck was successful.")
		return True
	else:
		logging.error("Failed Twilio authentication. Healthcheck failed.")
		return False
