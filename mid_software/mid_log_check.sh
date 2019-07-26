#!/bin/bash


export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
cd $(dirname $(readlink -f $0))

if test `find MID_WWW -mmin +15` 
then
	echo 'MID.log older than 15min'
	killall python
	sleep 5
	killall -9 python
	sleep 5
	./processCheck.sh
fi
