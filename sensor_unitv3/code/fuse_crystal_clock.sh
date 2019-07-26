#!/bin/sh
if [ "$FMICRO" = "m88" ]; then
avrdude -p $FMICRO -c stk500v2 -P /dev/ttyUSB0 -U lfuse:w:0xF7:m -U hfuse:w:0xdc:m
else
avrdude -p $FMICRO -c stk500v2 -P /dev/ttyUSB0 -U lfuse:w:0xF7:m -U hfuse:w:0xd9:m
fi;
