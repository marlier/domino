Raven
=====

Raven is a command line tool that pushes alerts to [domino](https://github.com/cbarraford/domino)

Included is a sample config file. Make your edits to this file and place it 
```
   /etc/raven.conf
```

It has a queuing feature, that when an alert is sent to domino that
fails to be recieved, it is saved on the disk locally (/var/spool/raven) to be resent
later.

Building an RPM
===============

To build the rpm, you will need rpmbuild installed on your system. Once you do run
```
    bash build_rpm
```
Once that succeeds, your rpm will be in ./RPMS/noarch/
