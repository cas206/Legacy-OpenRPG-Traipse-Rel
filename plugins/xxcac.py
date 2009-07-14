import os
import orpg.pluginhandler

class Plugin(orpg.pluginhandler.PluginHandler):
    # Initialization subroutine.
    #
    # !self : instance of self
    # !openrpg : instance of the the base openrpg control
    def __init__(self, plugindb, parent):
        orpg.pluginhandler.PluginHandler.__init__(self, plugindb, parent)

        # The Following code should be edited to contain the proper information
        self.name = 'Command Alias Creator'
        self.author = 'Dj Gilcrease'
        self.help = "This plugin lets you add Command Aliases.\neg /sits insted of /me sits down"
        self.newcmdaliases = {}


    def plugin_enabled(self):
        self.plugin_addcommand('/cmdalias', self.on_cmdalias, '[cmdalias_name fullcommand] [remove cmdalias_name] [clear] - (eg. <font color="#000000">/cmdalias /sits /me sits down</font> to add a command. OR <font color="#000000">/cmdalias remove /sits</font> to remove a single command. OR <font color="#000000">/cmdalias clear</font to clear the entire list)')
        self.newcmdaliases = self.plugindb.GetDict("xxcac", "newcmdaliases", {})

        for n in self.newcmdaliases:
            if not self.shortcmdlist.has_key(n) and not self.cmdlist.has_key(n):
                self.plugin_commandalias(n, self.newcmdaliases[n])


    def plugin_disabled(self):
        self.plugin_removecmd('/cmdalias')
        for n in self.newcmdaliases:
            self.plugin_removecmd(n)

    def on_cmdalias(self, cmdargs):
        args = cmdargs.split(" ",-1)
        if len(args) == 0:
            self.chat.InfoPost("USAGE: /cmdalias [cmdalias_name fullcommand] [remove cmdalias_name] [clear] - (eg. /sits /me sits down)")

        elif args[0] == 'remove':
            if self.newcmdaliases.has_key(args[1]):
                del self.newcmdaliases[args[1]]
                self.plugindb.SetDict("xxcac", "newcmdaliases", self.newcmdaliases)
                self.plugin_removecmd(args[1])
        elif args[0] == 'clear':
            for n in self.newcmdaliases:
                self.plugin_removecmd(n)
            self.newcmdaliases = {}
            self.plugindb.SetDict("xxcac", "newcmdaliases", self.newcmdaliases)
        else:
            oldcmd = cmdargs[len(args[0])+1:]
            self.newcmdaliases[args[0]] = oldcmd
            self.plugindb.SetDict("xxcac", "newcmdaliases", self.newcmdaliases)
            self.plugin_commandalias(args[0], oldcmd)
