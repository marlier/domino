About
=====
Domino is an open source alerting fronted for any monitoring system or infrastructure. It is backend agnostic, and can receive alerts from ANY source via http calls. It has built in SMS and phone call capabilities using Twilio's API.

Key features
============
 * Highly Available, scalable, and load balancing. Domino naturally runs in an active/active cluster
 * Alerting via SMS, telephone, RSS and email. (with usage of the API, you can create your own means of alerting)
 * Be able to ack alerts via SMS and phone
 * Can be used with any existing monitoring systems(s). Domino aggregates alerts and does not know or care where the alerts are coming from.
 * Automatic escalation of alerts.
 * Group alerts and route them to the right people by taging them with a user(s) or team name(s)
 * Full accessability through the read/write restful API.
 * Create rules that add/remove alert tags based on critieria you specify.
 * Get analyitics on your alerts (most frequest, newest, oldest, graphing datapoints, uptime, or build your own analyitics)
 
Screenshots
===========
![Dashboard](https://raw.github.com/CBarraford/domino/master/screenshots/dashboard.png "Dashboard")
![Alserts](https://raw.github.com/CBarraford/domino/master/screenshots/alerts.png "alerts")
More screenshots are available in the "screenshots" directory

Documentation
=============
documentation is available on the github [wiki](https://github.com/cbarraford/domino/wiki).

Denpencies
==========
 * Flask (http://http://flask.pocoo.org/)
 * twilio-python (https://github.com/twilio/twilio-python)
 * MySQLdb (http://sourceforge.net/projects/mysql-python/)
 * Simplejson (http://pypi.python.org/pypi/simplejson/)

Important Notes
 * This software does use Twilio (www.twilio.com) to handle SMS and phone calls. If you want to use these telcomm features, you must setup your own Twilio account.
 * One of the domino daemons (domino-comm) must be accessable by twilio's servers so they can make http calls to it.

Building a RPM
==============
To build an RPM of Domino run the following command
```
    python setup.py bdist_rpm
```

Building a DEB
==============
To build a deb package, you must have "python-stdeb" installed.
```
    python setup.py --command-packages=stdeb.command bdist_deb
```
Packages will show up in deb_dist directory

