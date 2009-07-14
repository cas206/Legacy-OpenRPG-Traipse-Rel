from math import sqrt

import wx

import orpg.dirpath
from orpg.orpgCore import *

from _object import MapObject

class MapCircle(MapObject):
    def __init__(self, canvas, center=wx.Point(0,0), radius=0, color="#000000"):
        MapObject.__init__(self, canvas=canvas)
        self.start = center
        self.radius = int(radius)
        self.color = color

        r, g, b = self.RGBHex.rgb_tuple(self.color)
        self.hcolor = self.RGBHex.hexstring(r^255, g^255, b^255)

        self.id = 'circle-' + self.canvas.GetNewObjectId()


    def Draw(self, dc):
        path = dc.CreatePath()

        if not self.highlighed:
            c = self.color
        else:
            c = self.hcolor
        r, g, b = self.RGBHex.rgb_tuple(c)

        pen = wx.TRANSPARENT_PEN
        brush = wx.TRANSPARENT_BRUSH
        if self.IsShown():
            brush = wx.Brush(wx.Color(r, g, b, 128))
            pen = wx.Pen(wx.Color(r, g, b, 128))
        elif self.canvas.toolWnd.gmToolBar.IsShown():
            brush = wx.Brush(wx.Color(r, g, b, 40))
            pen = wx.Pen(wx.Color(r, g, b, 40))
            font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
            dc.SetFont(font, wx.RED)
            w, h = dc.GetTextExtent("Hidden")
            dc.DrawText("Hidden", self.start.x-(w/2), self.start.y-(h/2), dc.CreateBrush(wx.WHITE_BRUSH))

        dc.SetBrush(brush)
        dc.SetPen(pen)

        path.AddCircle(self.start.x, self.start.y, self.radius)
        path.CloseSubpath()
        dc.DrawPath(path)

        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

        if self.selected:
            self.DrawSelection(dc)

    def DrawSelection(self, dc):
        dc.SetBrush(wx.GREEN_BRUSH)
        dc.SetPen(wx.GREEN_PEN)
        path = dc.CreatePath()

        path.AddRectangle(self.start.x-self.radius, self.start.y-self.radius, 5, 5)
        path.AddRectangle(self.start.x-self.radius, self.start.y+self.radius, 5, 5)
        path.AddRectangle(self.start.x+self.radius, self.start.y-self.radius, 5, 5)
        path.AddRectangle(self.start.x+self.radius, self.start.y+self.radius, 5, 5)

        path.MoveToPoint(self.start.x, self.start.y)
        path.AddLineToPoint(self.start.x-10, self.start.y)
        path.MoveToPoint(self.start.x, self.start.y)
        path.AddLineToPoint(self.start.x, self.start.y+10)
        path.MoveToPoint(self.start.x, self.start.y)
        path.AddLineToPoint(self.start.x+10, self.start.y)
        path.MoveToPoint(self.start.x, self.start.y)
        path.AddLineToPoint(self.start.x, self.start.y-10)

        dc.DrawPath(path)

        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

    def InObject(self, pos):
        xd = (self.start.x-pos.x)*(self.start.x-pos.x)
        yd = (self.start.y-pos.y)*(self.start.y-pos.y)
        distance = sqrt(xd+yd)

        if distance <= self.radius:
            return True

        return False

    def GetName(self):
        return 'Circle: ' + str(self.id) + ' Radius:' + str(self.radius) + ' Color:' + self.color

    def ShowProperties(self, event):
        dlg = wx.Dialog(self.canvas, wx.ID_ANY, "Circle Properties")
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        radius = wx.TextCtrl(dlg, wx.ID_ANY)
        radius.SetValue(str(self.radius))

        colorbtn = wx.Button(dlg, wx.ID_ANY, "Color")
        colorbtn.SetForegroundColour(self.hcolor)

        def ColorBtn(event):
            newcolor = self.RGBHex.do_hex_color_dlg(self.canvas)
            if newcolor == None:
                return

            colorbtn.SetForegroundColour(newcolor)
            dlg.Unbind(wx.EVT_BUTTON)

        dlg.Bind(wx.EVT_BUTTON, ColorBtn, colorbtn)

        sizer.Add(wx.StaticText(dlg, wx.ID_ANY, "Radius:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        sizer.Add(radius, 0, wx.EXPAND|wx.ALL, 3)
        sizer.Add(colorbtn, 0, wx.ALL, 2)
        sizer.Add(wx.Button(dlg, wx.ID_OK), 0, wx.ALL, 3)

        dlg.SetSizer(sizer)
        dlg.SetAutoLayout(True)
        dlg.Fit()
        dlg.Show()

        if dlg.ShowModal() == wx.ID_OK:
            self.radius = int(radius.GetValue())
            r,g,b = colorbtn.GetForegroundColour().Get()
            self.color = self.RGBHex.hexstring(r, g, b)
            self.hcolor = self.RGBHex.hexstring(r^255, g^255, b^255)
            self.Update(send=True, action="update")


    def OnLeftDown(self, pos):
        self.start = pos
        self.lastRadius = 0
        self.radius = 0

    def OnMotion(self, pos):
        dc = wx.ClientDC(self.canvas)
        self.canvas.PrepareDC(dc)
        dc.SetLogicalFunction(wx.EQUIV)
        dc.SetUserScale(self.canvas.zoomScale, self.canvas.zoomScale)


        if self.radius > 0:
            dc.DrawCircle(self.start.x, self.start.y, self.radius)

        xd = (self.start.x-pos.x)*(self.start.x-pos.x)
        yd = (self.start.y-pos.y)*(self.start.y-pos.y)
        self.radius = sqrt(xd+yd)

        #self.lastRadius = self.radius
        dc.DrawCircle(self.start.x, self.start.y, self.radius)

    def OnLeftUp(self, pos):
        xd = (self.start.x-pos.x)*(self.start.x-pos.x)
        yd = (self.start.y-pos.y)*(self.start.y-pos.y)
        radius = sqrt(xd+yd)

        if radius > 15:
            self.canvas.zOrder['front'].append(MapCircle(self.canvas, self.start, radius, self.canvas.whiteboardColor))
            self.Update(send=True, action='new')
        self.lastRadius = 0
        self.start = wx.Point(0,0)
        self.radius = 0

    def _toxml(self, action="update"):
        return ''