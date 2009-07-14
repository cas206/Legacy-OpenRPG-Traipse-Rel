#!/usr/bin/env python

import sys
import os

HG = os.environ["HG"]

import pyver
pyver.checkPyVersion()


os.system(HG + ' pull "http://hg.assembla.com/traipse"')
os.system(HG + " update -C grumpy-goblin")

for key in sys.modules.keys():
    if 'orpg' in key:
        del sys.modules[key]

from orpg.orpg_wx import *
import orpg.main

if WXLOADED:
    mainapp = orpg.main.orpgApp(0)
    mainapp.MainLoop()
else:
    print "You really really need wx!"
