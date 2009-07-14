import os
import orpg.pluginhandler
from random import randint
from time import time

class Plugin(orpg.pluginhandler.PluginHandler):
    # Initialization subroutine.
    #
    # !self : instance of self
    # !chat : instance of the chat window to write to
    def __init__(self, plugindb, parent):
        orpg.pluginhandler.PluginHandler.__init__(self, plugindb, parent)

        # The Following code should be edited to contain the proper information
        self.name = 'Idle Time'
        self.author = 'Woody, mDuo13'
        self.help = "When you haven't sent a message to chat for a minute or more, this\n"
        self.help += "plugin sets your status to end with '(* Mins)' where the * is however many\n"
        self.help += "minutes you've been inactive. You can also set a custom message for the timed\n"
        self.help += "idle by typing '/idle status *text*' where *text* is that message."

        self.idle_timer_status = ''
        self.start_time = ''
        self.minutes = ''
        self.last_update = ''

    def plugin_enabled(self):
        #This is where you set any variables that need to be initalized when your plugin starts
        self.plugin_addcommand('/idle', self.on_idle, 'status - This sets your status to what ever you type')
        self.reset_time()

    def plugin_disabled(self):
        #Here you need to remove any commands you added, and anything else you want to happen when you disable the plugin
        #such as closing windows created by the plugin
        self.plugin_removecmd('/idle')

    def on_idle(self, cmdargs):
        args = cmdargs.split(None,1)

        if args[0] == 'status':
            self.idle_timer_status = cmdargs[7:]
        else:
            self.chat.InfoPost("Invalid syntax for /idle command")

    def reset_time(self):
        self.start_time = time()
        self.minutes = 0
        self.last_update = 0

    def pre_parse(self, text):
        #This is called just before a message is parsed by openrpg
        self.reset_time()
        return text

    def refresh_counter(self):
        if self.idle_timer_status == '':
            self.idle_timer_status = self.settings.get_setting("IdleStatusAlias")

        current_time = time()
        self.minutes = round((current_time - self.start_time)/60,1)

        if self.minutes > 1:
            plur = 's'
        else:
            plur = ''

        if current_time - self.last_update >= 30:
            self.session.set_text_status(self.idle_timer_status + ' (' + str(self.minutes) + ' min' + plur + ')')
            self.last_update = time()
