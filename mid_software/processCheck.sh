#!/bin/sh
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

if ps ax | grep -v grep | grep runDaemon.py > /dev/null
then
    echo "Good." > /dev/null
else
    cd $(dirname $(readlink -f $0))
    /bin/rm -f /tmp/MID.pid
    /usr/bin/python runDaemon.py start
fi
