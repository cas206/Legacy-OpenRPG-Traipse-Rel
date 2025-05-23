# Copyright (C) 2000-2001 The OpenRPG Project
#
#        openrpg-dev@lists.sourceforge.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
# --
#
# File: chatmacro.py
# Author: Chris Davis
# Maintainer:
# Version:
#   $Id: chatmacro.py,v Traipse 'Ornery-Orc' prof.ebral Exp $
#
# Description: The file contains code for the form based nodehanlers
#

__version__ = "$Id: chatmacro.py,v Traipse 'Ornery-Orc' prof.ebral Exp $"

from core import *

##########################
## text node handler
##########################
class macro_handler(node_handler):
    """ A nodehandler for text blocks. Will open text in a text frame
        <nodehandler name='?' module='chatmacro' class='macro_handler'>
            <text>some text here</text>
        </nodehandler >
    """
    def __init__(self,xml,tree_node):
        node_handler.__init__(self,xml,tree_node)
        self.xml = xml

    def set_text(self, txt):
        self.xml.find('text').text = txt

    def on_use(self,evt):
        actionlist = self.xml.find('text').text.split("\n")
        for line in actionlist:
            if(line != ""):
                if line[0] != "/": ## it's not a slash command
                    action = self.chat.ParsePost(line, True, True)
                else:
                    action = line
                    self.chat.chat_cmds.docmd(action)
        return 1

    def get_design_panel(self,parent):
        return macro_edit_panel(parent,self)

    def tohtml(self):
        title = self.xml.get("name")
        txt = string.replace(self.xml.find('text').text,'\n',"<br />")
        return "<P><b>"+title+":</b><br />"+txt

P_TITLE = wx.NewId()
P_BODY = wx.NewId()
B_CHAT = wx.NewId()

class macro_edit_panel(wx.Panel):
    def __init__(self, parent, handler):
        wx.Panel.__init__(self, parent, -1)
        self.handler = handler
        sizer = wx.StaticBoxSizer(wx.StaticBox(self, -1, "Chat Macro"), wx.VERTICAL)
        self.text = {}
        self.text[P_TITLE] = wx.TextCtrl(self, P_TITLE, handler.xml.get('name'))
        self.text[P_BODY] = wx.TextCtrl(self, P_BODY, handler.xml.find('text').text, style=wx.TE_MULTILINE)
        sizer.Add(wx.StaticText(self, -1, "Title:"), 0, wx.EXPAND)
        sizer.Add(self.text[P_TITLE], 0, wx.EXPAND)
        sizer.Add(wx.StaticText(self, -1, "Text Body:"), 0, wx.EXPAND)
        sizer.Add(self.text[P_BODY], 1, wx.EXPAND)
        sizer.Add(wx.Button(self, B_CHAT, "Send To Chat"),0,wx.EXPAND)
        self.Bind(wx.EVT_TEXT, self.on_text, id=P_TITLE)
        self.Bind(wx.EVT_TEXT, self.on_text, id=P_BODY)
        self.Bind(wx.EVT_BUTTON, self.handler.on_use, id=B_CHAT)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        self.Fit()

    def on_text(self,evt):
        id = evt.GetId()
        txt = self.text[id].GetValue()
        if txt == "": return
        if id == P_TITLE:
            self.handler.xml.set('name',txt)
            self.handler.rename(txt)
        elif id == P_BODY: self.handler.set_text(txt)
