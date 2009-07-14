import os
import orpg.plugindb # VEG
import orpg.pluginhandler
import thread
import cherrypy._cpserver as server
import socket
import wx

 # VEG (march 21, 2007): Now remembers your last web server on/off setting

class Plugin(orpg.pluginhandler.PluginHandler):
    # Initialization subroutine.
    #
    # !self : instance of self
    # !openrpg : instance of the the base openrpg control
    def __init__(self, plugindb, parent):
        orpg.pluginhandler.PluginHandler.__init__(self, plugindb, parent)

        # The Following code should be edited to contain the proper information
        self.name = 'CherryPy Web Server'
        self.author = 'Dj Gilcrease'
        self.help = 'This plugin turns OpenRPG into a Web server\n'
        self.help += 'allowing you to host your map and mini files localy'

        #You can set variables below here. Always set them to a blank value in this section. Use plugin_enabled
        #to set their proper values.
        self.isServerRunning = 'off'
        self.host = 0

    def plugin_menu(self):
        self.menu = wx.Menu()
        self.toggle = self.menu.AppendCheckItem(wx.ID_ANY, 'On')
        self.topframe.Bind(wx.EVT_MENU, self.cherrypy_toggle, self.toggle)

        ports = wx.Menu()
        self.portClient = ports.AppendRadioItem(wx.ID_ANY, 'Client:9557')
        self.portServer = ports.AppendRadioItem(wx.ID_ANY, 'Server:9558')
        self.topframe.Bind(wx.EVT_MENU, self.port_change, self.portClient)
        self.topframe.Bind(wx.EVT_MENU, self.port_change, self.portServer)
        self.menu.AppendMenu(wx.ID_ANY, 'Port', ports)

    def port_change(self, evt):
        if self.portClient.IsChecked() == True: self.on_cherrypy("port 9557")
        if self.portServer.IsChecked() == True: self.on_cherrypy("port 9558")

    def cherrypy_toggle(self, evt):
        if self.toggle.IsChecked() == True: self.on_cherrypy("on")
        if self.toggle.IsChecked() == False: self.on_cherrypy("off")

    def plugin_enabled(self):
        self.port = 9557
        self.plugin_addcommand('/cherrypy', self.on_cherrypy, '[on | off | port | status] - This controls the CherryPy Web Server')
        tmp = socket.gethostbyname_ex(socket.gethostname())
        for ip in tmp[2]:
            self.host = ip
            if ip[:7] == '192.168' or ip[:3] == '10.' or ip == '127.0.0.1' or (ip[:3] == '172' and (int(ip[5:6]) >= 16 and int(ip[5:6]) <=32)) :
                self.chat.InfoPost("[WARNING] Cherrypy has detected that you may be behind a router. This is your internal IP. For other users to properly connect, you may have to use your external IP, with port forwarding on port 80.<br />This feature is not suported in any way.")

        #if str(self.plugindb.GetString("xxcherrypy", "auto_start", "off")) == "on":  # VEG
        #    self.on_cherrypy("on")                                                   # VEG

    def plugin_disabled(self):
        #Here you need to remove any commands you added, and anything else you want to happen when you disable the plugin
        #such as closing windows created by the plugin
        self.plugin_removecmd('/cherrypy')
        if self.isServerRunning == 'on':
            server.stop()
            self.isServerRunning = 'off'
        else:
            pass


    def on_cherrypy(self, cmdargs):
        args = cmdargs.split(None,-1)

        if len(args) == 0 or args[0] == 'status':
            self.chat.InfoPost("CherryPy Web Server is currently: " + self.isServerRunning)
            self.chat.InfoPost("CherryPy Web Server address is: http://" + str(self.host) + ':' + str(self.port) + '/webfiles/')

        elif args[0] == 'on' and self.isServerRunning == 'off':
            self.webserver = thread.start_new_thread(self.startServer, (self.port,))
            self.isServerRunning = 'on'
            self.toggle.Check(True)
            self.plugindb.SetString("xxcherrypy", "auto_start", "on") # VEG

        elif args[0] == 'off' and self.isServerRunning == 'on':
            server.stop()
            self.isServerRunning = 'off'
            self.toggle.Check(False)
            self.chat.InfoPost("CherryPy Web Server is now disabled")
            self.plugindb.SetString("xxcherrypy", "auto_start", "off") # VEG

        elif args[0] == 'port':
            if self.isServerRunning == 'on':
                self.port = int(args[1])
                server.stop()
                self.webserver = thread.start_new_thread(self.startServer, (self.port,))
            self.port = int(args[1])
            self.chat.InfoPost("CherryPy Web Server is currently: " + self.isServerRunning)
            self.chat.InfoPost("CherryPy Web Server address is: http://" + str(self.host) + ':' + str(self.port) + '/webfiles/')



    def startServer(self, port):
        try:
            if self.host == 0:
                raise Exception("Invalid IP address.<br />This error means you are behind a router or some other form of network that is giving you a Privet IP only (ie. 192.168.x.x, 10.x.x.x, 172.16 - 32.x.x)")

            self.chat.InfoPost("CherryPy Web Server is now running on http://" + str(self.host) + ':' + str(self.port) + '/webfiles/')
            server.start(configMap =
                        {'staticContentList': [['', r''+orpg.dirpath.dir_struct["user"]+'webfiles/'],
                                               ['webfiles', r''+orpg.dirpath.dir_struct["user"]+'webfiles/'],
                                               ['Textures', r''+orpg.dirpath.dir_struct["user"]+'Textures/'],
                                               ['Maps', r''+orpg.dirpath.dir_struct["user"]+'Maps/'],
                                               ['Miniatures', r''+orpg.dirpath.dir_struct["user"]+'Miniatures']],
                        'socketPort': port,
                        'logToScreen': 0,
                        'logFile':orpg.dirpath.dir_struct["user"]+'webfiles/log.txt',
                        'sessionStorageType':'ram',
                        'threadPool':10,
                        'sessionTimeout':30,
                        'sessionCleanUpDelay':30})

        except Exception, e:
            self.chat.InfoPost("FAILED to start server!")
            self.chat.InfoPost(str(e))
            self.isServerRunning = 'off'
            self.toggle.Check(False)
