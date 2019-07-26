#!/bin/sh

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

if ps ax | grep -v grep | grep runDaemon_RTM2000Interface.py > /dev/null
then
    echo "Good." > /dev/null
else
#    echo "Starting"
    cd $(dirname $(readlink -f $0))
    /bin/rm -f /tmp/MID_RTM2000.pid
    /usr/bin/python runDaemon_RTM2000Interface.py start
fi
