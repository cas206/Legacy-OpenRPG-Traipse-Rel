from math import sqrt

import wx

import orpg.dirpath
from orpg.orpgCore import *

from _object import MapObject

class MapLine(MapObject):
    def __init__(self, canvas, start=wx.Point(0,0), width=1, color="#000000", points=[]):
        MapObject.__init__(self, canvas=canvas)
        self.start = wx.Point(start[0], start[1])
        self.color = color
        self.points = points
        self.width = width

        r, g, b = self.RGBHex.rgb_tuple(self.color)
        self.hcolor = self.RGBHex.hexstring(r^255, g^255, b^255)

        self.id = 'line-' + self.canvas.GetNewObjectId()


    def Draw(self, dc):
        path = dc.CreatePath()

        if not self.highlighed:
            c = self.color
        else:
            c = self.hcolor
        r, g, b = self.RGBHex.rgb_tuple(c)

        pen = wx.Pen(wx.Color(r, g, b, 0), self.width)
        if self.IsShown():
            pen = wx.Pen(wx.Color(r, g, b, 255), self.width)
        elif self.canvas.toolWnd.gmToolBar.IsShown():
            pen = wx.Pen(wx.Color(r, g, b, 40), self.width)
        dc.SetPen(pen)

        dc.DrawLines(self.points)

        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

        if self.selected:
            self.DrawSelection(dc)

    def DrawSelection(self, dc):
        dc.SetBrush(wx.GREEN_BRUSH)
        dc.SetPen(wx.GREEN_PEN)
        path = dc.CreatePath()

        dc.DrawPath(path)

        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

    def InObject(self, pos):
        for point in self.points:
            xd = (point[0]-pos.x)*(point[0]-pos.x)
            yd = (point[1]-pos.y)*(point[1]-pos.y)
            distance = sqrt(xd+yd)

            if distance <= self.width+1:
                return True

        return False

    def GetName(self):
        return self.id + ' Color:' + self.color

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
        self.lastPoint = pos
        self.start = pos
        self.points.append((pos.x, pos.y))

    def OnMotion(self, pos):
        dc = wx.ClientDC(self.canvas)
        self.canvas.PrepareDC(dc)

        r,g,b = self.RGBHex.rgb_tuple(self.canvas.whiteboardColor)
        pen = wx.Pen(wx.Color(r,g,b,255), int(self.canvas.toolWnd.LineWidth.GetStringSelection()))
        dc.SetPen(pen)

        xd = (self.lastPoint.x-pos.x)*(self.lastPoint.x-pos.x)
        yd = (self.lastPoint.y-pos.y)*(self.lastPoint.y-pos.y)
        distance = sqrt(xd+yd)

        if distance > 5:
            if self.canvas.toolWnd.currentLine == 'Free':
                self.points.append((pos.x, pos.y))
                self.lastPoint = pos
                dc.DrawLines(self.points)
            else:
                dc.SetLogicalFunction(wx.INVERT)
                dc.DrawLine(self.start.x, self.start.y, self.lastPoint.x, self.lastPoint.y)
                dc.DrawLine(self.start.x, self.start.y, pos.x, pos.y)
                dc.SetLogicalFunction(wx.COPY)
                dc.DrawLines(self.points)
                self.lastPoint = pos

        dc.SetPen(wx.NullPen)

    def OnLeftUp(self, pos):
        if self.canvas.toolWnd.currentLine == 'Free' and len(self.points) > 2:
            self.points.append((pos.x, pos.y))
            self.canvas.zOrder['front'].append(MapLine(self.canvas, self.points[0], int(self.canvas.toolWnd.LineWidth.GetStringSelection()), self.canvas.whiteboardColor, self.points))
            self.start = wx.Point(0,0)
            self.points = []

    def OnLeftDClick(self, pos):
        if self.canvas.toolWnd.currentLine == 'Poly' and len(self.points) > 2:
            self.points.append((pos.x, pos.y))
            self.canvas.zOrder['front'].append(MapLine(self.canvas, self.points[0], int(self.canvas.toolWnd.LineWidth.GetStringSelection()), self.canvas.whiteboardColor, self.points))
            self.points = []
            self.start = wx.Point(0,0)

    def _toxml(self, action="update"):
        return ''