#!/bin/sh
#Hfuse is different for atmega88 don't copy atmega88's one.
avrdude -p m328 -c stk500v2 -P /dev/ttyUSB0 -U lfuse:w:0xF7:m -U hfuse:w:0xd9:m
