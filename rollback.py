#!/usr/bin/env python

import sys
import os

HG = os.environ["HG"]

os.system(HG + " rollback")
os.system(HG + " revert --all")
print "Since you reverted, I am guessing there are issues with the last update"
print "PLEASE notify me on either the openrpg.com boards, or by email"
print "digitalxero@gmail.com"
print "You can continue using your rolled back version by launching openrpg from"
print "the command line with the command: OpenRPG*.py -n"
print "the -n tells the system not to update, it will still run the downloader"
print "but it will not change your files"
raw_input("press <enter> key to terminate program")