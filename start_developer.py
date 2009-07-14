#!/usr/bin/env python

import sys
import os

import pyver
pyver.checkPyVersion()


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
