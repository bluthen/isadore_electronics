#!/bin/sh

if ! /bin/ping -c 1 exotericanalytics.com > /dev/null
then
	echo `date` - No internet >> /isadore/network_check.log
	/sbin/reboot
elif ! /bin/ping -c 1 10.0.0.29 > /dev/null
then
	echo `date` - Hub >> /isadore/network_check.log
	/sbin/reboot
fi
