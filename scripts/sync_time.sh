#!/bin/bash

# force a clock update. Assumes ntp is installed.
# see http://askubuntu.com/a/256004
sudo service ntp stop
sudo ntpd -gq
sudo service ntp start
