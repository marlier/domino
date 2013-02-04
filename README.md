About
=====
Domino is an open source alerting fronted for any monitoring system or infrastructure. It is backend agnostic, and can receive alerts from ANY source via http calls. It has built in SMS and phone call capabilities using Twilio's API.

Key features
============
 * alerting via SMS, telephone, RSS and email. (with usage of the API, you can create your own means of alerting)
 * Be able to ack alerts, view alerts, etc via SMS and phone
 * can be used with any existing monitoring solution(s). Domino aggregates alerts and does not know or care where the alerts are coming from.
 * automatic escalation of alerts.
 * Group alerts and route them to the right people via tags
 * highly customizable to fit your alerting and escalation procedures
 * Full accessability through the read/write restful API.
 * Create rules that add/remove alert tags based on critieria you specify.
 * Get basic stats on your alerts (most frequest, newest, oldest, graphing datapoints, or build your own stats)
 
Documentation
documentation is available on the github [wiki](https://github.com/cbarraford/domino/wiki).

Denpencies
 * Flask (http://http://flask.pocoo.org/)
 * twilio-python (https://github.com/twilio/twilio-python)
 * MySQLdb (http://sourceforge.net/projects/mysql-python/)
 * Simplejson (http://pypi.python.org/pypi/simplejson/)

Important Notes
 * The server you run Domino on and the mysql server must be on UTC timezone.
 * This software does use Twilio (www.twilio.com) to handle SMS and phone calls. If you want to use these telcome features, you must setup your own Twilio account.
 * One of the domino daemons (domino-comm) must be accessable by twilio's servers so they can make http calls to it.

Building a RPM
==============
To build an RPM of Domino run the following command
```
    python setup.py bdist_rpm
```

