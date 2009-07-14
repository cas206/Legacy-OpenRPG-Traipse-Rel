import os
from orpg.orpg_wx import *
import random
import orpg.pluginhandler


ID_ROLL = wx.NewId()

class Plugin(orpg.pluginhandler.PluginHandler):
    # Initialization subroutine.
    #
    # !self : instance of self
    # !chat : instance of the chat window to write to
    def __init__(self, plugindb, parent):
        orpg.pluginhandler.PluginHandler.__init__(self, plugindb, parent)

        self.name = 'Game Status Controller'
        self.author = 'Woody, updated by mDuo13'
        self.help = 'This plugin lets you quickly and easily manage a status that includes \n'
        self.help += 'your HP and AC for AD&D 2nd Edition. Type /gsc to open up the manager\n'
        self.help += 'window, and from there just change the values as necessary and the changes\n'
        self.help += 'will be reflected in your status. To revert to your regular status, close\n'
        self.help += 'the GSC window.'

        self.frame = None

    def plugin_enabled(self):
        self.plugin_addcommand('/gsc', self.on_gsc, '- The GSC command')
        self.frame = RollerFrame(None, -1, "Game Status Ctrl (GSC)", self)
        self.frame.Hide()

        item = wx.MenuItem(self.menu, wx.ID_ANY, "GSC Window", "GSC Window", wx.ITEM_CHECK)
        self.topframe.Bind(wx.EVT_MENU, self._toggleWindow, item)
        self.menu.AppendItem(item)

    def plugin_disabled(self):
        self.plugin_removecmd('/gsc')
        try:
            self.frame.TimeToQuit(1)
        except:
            pass

    def on_gsc(self, cmdargs):
        item = self.menu.FindItemById(self.menu.FindItem("GSC Window"))
        item.Check(True)
        self.frame.Show()
        self.frame.Raise()

    #Events
    def _toggleWindow(self, evt):
        id = evt.GetId()
        item = self.menu.FindItemById(id)
        if self.frame.IsShown():
            self.frame.Hide()
            item.Check(False)
        else:
            self.frame.Show()
            item.Check(True)


class RollerFrame(wx.Frame):
    def __init__(self, parent, ID, title, plugin):
        wx.Frame.__init__(self, parent, ID, title,
                         wx.DefaultPosition, wx.Size(200, 70))

        self.settings = plugin.settings
        self.session = plugin.session
        self.plugin = plugin

        self.panel = wx.Panel(self,-1)
        menu = wx.Menu()
        menu.AppendSeparator()
        menu.Append(wx.ID_EXIT, "&Close", "Close this window")
        menuBar = wx.MenuBar()
        menuBar.Append(menu, "&File");
        self.SetMenuBar(menuBar)

        self.old_idle = self.settings.get_setting('IdleStatusAlias')

        wx.StaticText(self.panel, -1, "AC:", wx.Point(0, 5))
        self.ac = wx.SpinCtrl(self.panel, ID_ROLL, "", wx.Point(18, 0), wx.Size(45, -1), min = -100, max = 100, initial = 10)
        self.ac.SetValue(10)

        wx.StaticText(self.panel, -1, "/", wx.Point(136, 5))
        self.max_hp = wx.SpinCtrl(self.panel, ID_ROLL, "", wx.Point(144, 0), wx.Size(48, -1), min = -999, max = 999, initial = 10)
        self.max_hp.SetValue(10)

        wx.StaticText(self.panel, -1, "HP:", wx.Point(65, 5))
        self.hp = wx.SpinCtrl(self.panel, ID_ROLL, "", wx.Point(83, 0), wx.Size(48, -1), min = -999, max = 999, initial = 10)
        self.hp.SetValue(10)

        self.Bind(wx.EVT_SPINCTRL, self.SetStatus, id=ID_ROLL)
        self.Bind(wx.EVT_TEXT, self.SetStatus, id=ID_ROLL)
        self.Bind(wx.EVT_MENU, self.TimeToQuit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_CLOSE, self._close)
        self.SetStatus(None)

    def SetStatus(self, evt):
        new_status = "AC: " + str(self.ac.GetValue()) + "   HP: " + str(self.hp.GetValue()) + "/" + str(self.max_hp.GetValue())
        self.settings.set_setting('IdleStatusAlias',new_status)
        self.session.set_text_status(new_status)

    def TimeToQuit(self, event):
        self.settings.set_setting('IdleStatusAlias',self.old_idle)
        self.session.set_text_status(self.old_idle)
        self.frame = None
        self.Destroy()

    def _close(self, evt):
        self.Hide()
        item = self.plugin.menu.FindItemById(self.plugin.menu.FindItem("GSC Window"))
        item.Check(False)
