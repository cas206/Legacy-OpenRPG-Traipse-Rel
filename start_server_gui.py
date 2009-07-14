#!/usr/bin/env python

import os
import sys

HG = os.environ["HG"]

import pyver
pyver.checkPyVersion()

os.system(HG + ' pull "http://hg.assembla.com/traipse"')
os.system(HG + ' update')

from orpg.orpg_wx import *

if WXLOADED:
    import orpg.networking.mplay_server_gui
    app = orpg.networking.mplay_server_gui.ServerGUIApp(0)
    app.MainLoop()
