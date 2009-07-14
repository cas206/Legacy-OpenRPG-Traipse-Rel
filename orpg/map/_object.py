from math import sqrt

import wx

import orpg.dirpath
from orpg.orpgCore import *
from orpg.tools.rgbhex import RGBHex

wxEVT_ENTER_OBJECT = wx.NewEventType()
wxEVT_LEAVE_OBJECT = wx.NewEventType()
wxEVT_SELECT_OBJECT = wx.NewEventType()
wxEVT_DESELECT_OBJECT = wx.NewEventType()
EVT_ENTER_OBJECT = wx.PyEventBinder(wxEVT_ENTER_OBJECT)
EVT_LEAVE_OBJECT = wx.PyEventBinder(wxEVT_LEAVE_OBJECT)
EVT_SELECT_OBJECT = wx.PyEventBinder(wxEVT_SELECT_OBJECT)
EVT_DESELECT_OBJECT = wx.PyEventBinder(wxEVT_DESELECT_OBJECT)

class ObjectEvent(wx.PyCommandEvent):
    def __init__(self, eventType, object):
        wx.PyCommandEvent.__init__(self, eventType)

        self._object = object

        self._eventType = eventType
        self.notify = wx.NotifyEvent(eventType, -1)

    def GetNotifyEvent(self):
        return self.notify

    def GetObject(self):
        return self._object

    def GetId(self):
        return self._object.GetId()

class MapObject:
    def __init__(self, **kwargs):
        self.id = -1
        self.start = wx.Point(0,0)
        self.color = "#000000"
        self.hcolor = "#ffffff"
        self.lineWidth = 1
        self.zOrder = 'front'
        self.selected = False
        self.inObject = False
        self.highlighed = False
        self.isshown = True
        self.canvas = None
        self.RGBHex = RGBHex()
        self.trans = 1

        for atter, value in kwargs.iteritems():
            setattr(self, atter, value)

        try:
            if self.id == wx.ID_ANY:
                self.id = wx.NewId()
        except:
            self.id = wx.NewId()

    #Public Methods
    def HitTest(self, pos):
        if self.InObject(pos) and not self.inObject and not self.selected:
            self.inObject = True
            evt = ObjectEvent(wxEVT_ENTER_OBJECT, self)
            self.canvas.GetEventHandler().ProcessEvent(evt)
        elif not self.InObject(pos) and self.inObject and not self.selected:
            self.inObject = False
            evt = ObjectEvent(wxEVT_LEAVE_OBJECT, self)
            self.canvas.GetEventHandler().ProcessEvent(evt)

    def GetId(self):
        return self.id

    def IsShown(self):
        return self.isshown

    def Show(self, event=None, show=True):
        self.isshown = show
        self.Update(send=True, action="update")

    def Hide(self, event=None):
        self.isshown = False
        self.Update(send=True, action="update")

    def IsSelected(self):
        return self.selected

    def Select(self, select=True):
        self.selected = select

        if select:
            evt = ObjectEvent(wxEVT_SELECT_OBJECT, self)
        else:
            evt = ObjectEvent(wxEVT_DESELECT_OBJECT, self)

        self.canvas.GetEventHandler().ProcessEvent(evt)

    def Deselect(self):
        self.selected = False
        evt = ObjectEvent(wxEVT_DESELECT_OBJECT, self)
        self.canvas.GetEventHandler().ProcessEvent(evt)

    def Update(self, send=False, action="update"):
        self.canvas.UpdateMap()
        if send:
            self.canvas.session.send(self._toxml(action))

    def GetName(self):
        return 'ID: ' + str(self.id) + ' Color: ' + self.color

    def InObject(self, pos):
        pass

    def Draw(self, dc):
        if self.selected:
            self.DrawSelected(dc)

    def DrawSelected(self, dc):
        pass

    def Highlight(self):
        self.highlighed = True
        self.Update()

    def UnHighlight(self):
        self.highlighed = False
        self.Update()

    def OnLeftDown(self, pos):
        if self.inObject and self.selected:
            self.start = pos
            self.Deselect()

        elif self.inObject and not self.selected:
            self.Select()

        else:
            self.start = pos

        self.Update()

    def OnMotion(self, pos):
        cdc = wx.ClientDC(self.canvas)
        self.canvas.PrepareDC(cdc)
        dc = wx.GraphicsContext.Create(cdc)

        if self.selected:
            self.start = pos
            self.Draw(dc)

    def OnLeftUp(self, pos):
        pass

    def OnRightDown(self, pos):
        pass

    def OnLeftDClick(self, pos):
        pass

    def ShowProperties(self, event):
        pass

    def _toxml(self, action="update"):
        return ''