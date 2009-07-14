import os
import orpg.pluginhandler

class Plugin(orpg.pluginhandler.PluginHandler):
    # Initialization subroutine.
    #
    # !self : instance of self
    # !chat : instance of the chat window to write to
    def __init__(self, plugindb, parent):
        orpg.pluginhandler.PluginHandler.__init__(self, plugindb, parent)


        # The Following code should be edited to contain the proper information
        self.name = 'Font Tools'
        self.author = 'mDuo13'
        self.help = "You can change your font in chat by typing '/myfont *key*'\n"
        self.help += "where *key* is this plugin's shorthand for a font, like 'c'\n"
        self.help += "for Courier. You can type /myfont list for the whole list.\n"
        self.help += "You can use another font by typing '/myfont custom=*name*', where\n"
        self.help += "*name* is the EXACT name of the font, case-sensitive and all.\n"
        self.help += "Font resizing is no longer supported by the plugin as it is in\n"
        self.help += "the official code now. (Try typing '/fontsize *x*' to change your\n"
        self.help += "font to size *x*.)"
        #define any variables here, but always define them as ''. you will set thier values and proper type in plugin_enabled
        self.fontstring = ''
        self.fontlist = {}

    def plugin_enabled(self):
        #This is where you set any variables that need to be initalized when your plugin starts
        #You can add new /commands like
        self.plugin_addcommand('/myfont', self.on_myfont, '[list|custom (fontname)|fontname] - This lets you change the font type for your messages, but leaves other peoples alone')
        #Argument 1 is the command it self
        #Argument 2 is the function to be called when you issue the command
        #Argument 3 is the help text for the command

        self.fontstring = self.plugindb.GetString("xxfontchng", "fontstring", "")
        self.fontlist = {"a" : "<font>",
                        "arial" : "<font>",
                        "c" : "<font face='Courier New, Courier, monospace'>",
                        "courier" : "<font face='Courier New, Courier, monospace'>",
                        "t" : "<font face='Times New Roman, Times, serif'>",
                        "times" : "<font face='Times New Roman, Times, serif'>",
                        "tempus" : "<font face='Tempus Sans ITC'>",
                        "westminster" : "<font face='Westminster' size=+1>",
                        "mistral" : "<font face='Mistral' size=+2>",
                        "lucida sans" : "<font face='Lucida Sans'>",
                        "lucida handwriting" : "<font face='Lucida Handwriting'>",
                        "western" : "<font face='Rockwell'>",
                        "rockwell" : "<font face='Rockwell'>"}

    def plugin_disabled(self):
        self.plugin_removecmd('/myfont')

    def on_myfont(self, cmdargs):
        args = cmdargs.split(None,1)

        if len(args) == 0 or args[0] == 'list':
            the_list = ''
            for entry in self.fontlist.keys():
                the_list += '<br />' + self.fontlist[entry] + entry + '</font>'
            the_list += '<br />custom *anyfont*'
            self.chat.InfoPost(the_list)
        elif args[0] == 'custom':
            self.fontstring = '<font face="' + args[1] + '">'
        elif self.fontlist.has_key(args[0]):
            self.fontstring = self.fontlist[args[0]]
            self.chat.InfoPost("Your font now looks " + self.fontstring + "like this.</font>")
            self.plugindb.SetString("xxfontchng", "fontstring", self.fontstring)
        else:
            self.chat.InfoPost("Invalid font name. Type /myfont list for a list of font names, or use custom preceding the font name")

    def pre_parse(self, text):
        #This is called just before a message is parsed by openrpg
        cmdsearch = text.split(None,1)
        if len(cmdsearch) == 0:
            return text
        cmd = cmdsearch[0].lower()
        start = len(cmd)
        end = len(text)
        cmdargs = text[start:end]

        if cmd == "/whisper" or cmd == "/w":
            text = cmd + ' ' + cmdargs[:cmdargs.find("=")+1] + self.fontstring + cmdargs + '</font>'
        elif cmd == "/me" or cmd == "/he" or cmd == "/she":
            text = cmd + ' ' + self.fontstring + cmdargs + '</font>'
        elif cmd[0] != '/':
            text = self.fontstring + text + '</font>'
        return text

    def send_msg(self, text, send):
        if self.fontstring.find("<font") > -1:
            text = self.fontstring + text + '</font>'
        return text, send
