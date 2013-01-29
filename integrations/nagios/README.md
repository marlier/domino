Nagios Integration
==================

Setting Up the Domino Contact
```
define contact {
        contact_name                    domino
        alias                           domino
        service_notification_period     24x7
        host_notification_period        24x7
        service_notification_options    w,u,c,r
        host_notification_options       u,d,r
        service_notification_commands   notify-by-raven
        host_notification_commands      host-notify-by-raven
}
```

Setting up the commands.cfg (You'll likely need to customize this but this is a good start)
```
define command{
    command_name    notify-by-raven
    command_line    /usr/bin/printf "%b" "$SERVICEOUTPUT$\n $LONGSERVICEOUTPUT$" | /opt/domino/bin/raven -c /opt/domino/conf/raven.conf -s $SERVICESTATEID$ -H $HOSTNAME$ -v "$SERVICEDESC$" -T "nagios,service,$_SERVICETAGS$"
}

define command{
    command_name    host-notify-by-raven
    command_line    /usr/bin/printf "%b" "Host is Down!" | /opt/domino/bin/raven -c /opt/domino/conf/raven.conf -s $HOSTSTATEID$ -H $HOSTNAME$ -v "" -T "nagios,host,$_HOSTTAGS$"
}
```

As a cron, run nagios_to_domino.rb on your nagios server(s). This will do three things
 * Delete any alerts within Domino that don't exist in nagios anymore
 * Add alerts that exist within nagios, but not domino
 * Sync any discrepancies between nagios and domino

You may need to modify this ruby script a bit to match the specific needs of your environment. Take a close read through the script and understand what its doing exactly before implementing into production.
```
ARG1 = status.dat file location
ARG2 = search terms against domino to find this nagios server's services/hosts
ARG3 = domain (this is used to chop off the domain name from hostnames)
ruby nagios_to_domino.rb /var/cache/nagios3/status.dat colo:BOS+tags:nagios BOS
```
