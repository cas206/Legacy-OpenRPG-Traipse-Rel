from math import sqrt

import wx

import orpg.dirpath
from orpg.orpgCore import *

from _object import MapObject

class FogLayer(MapObject):
    def __init__(self, canvas):
        MapObject.__init__(self, canvas=canvas)

    def Draw(self, dc):
        path = dc.CreatePath()
        r, g, b = self.RGBHex.rgb_tuple(self.canvas.fogColor)
        if self.canvas.toolWnd.gmToolBar.IsShown():
            brush = wx.Brush(wx.Color(r, g, b, 128))
        else:
            brush = wx.Brush(wx.Color(r, g, b, 255))
        dc.SetBrush(brush)

        self.region = wx.Region(0, 0, self.canvas.size[0]+2, self.canvas.size[1]+2)

        points = []
        lp = 's'
        for point in self.canvas.fogRegion:
            if point == 's' or point == 'h':
                if lp == 's' and len(points) > 0:
                    self.region.XorRegion(wx.RegionFromPoints(points))
                    self.region.SubtractRegion(wx.RegionFromPoints(points))
                elif len(points) > 0:
                    self.region.UnionRegion(wx.RegionFromPoints(points))
                lp = point
                points = []
            else:
                points.append((point.x, point.y))

        if len(points) > 0:
            if lp == 's':
                self.region.XorRegion(wx.RegionFromPoints(points))
                self.region.SubtractRegion(wx.RegionFromPoints(points))
            else:
                self.region.UnionRegion(wx.RegionFromPoints(points))

        dc.ClipRegion(self.region)

        dc.DrawRectangle(0, 0, self.canvas.size[0]+2, self.canvas.size[1]+2)

        dc.SetBrush(wx.NullBrush)

    def OnLeftDown(self, pos):
        self.start = pos
        self.lastPoint = pos
        if self.canvas.toolWnd.currentFog == 'Show':
            self.canvas.fogRegion.append('s')
        else:
            self.canvas.fogRegion.append('h')
        self.canvas.fogRegion.append(pos)

    def OnMotion(self, pos):
        cdc = wx.ClientDC(self.canvas)
        self.canvas.PrepareDC(cdc)

        dc = wx.GraphicsContext.Create(cdc)
        dc.Scale(self.canvas.zoomScale, self.canvas.zoomScale)

        dc.SetPen(wx.WHITE_PEN)

        path = dc.CreatePath()

        xd = (self.lastPoint.x-pos.x)*(self.lastPoint.x-pos.x)
        yd = (self.lastPoint.y-pos.y)*(self.lastPoint.y-pos.y)
        distance = sqrt(xd+yd)

        if distance > 5:
            path.MoveToPoint(self.lastPoint.x, self.lastPoint.y)
            path.AddLineToPoint(pos.x, pos.y)

            self.canvas.fogRegion.append(pos)
            self.lastPoint = pos

        path.CloseSubpath()
        dc.StrokePath(path)

        dc.SetPen(wx.NullPen)

    def OnLeftUp(self, pos):
        self.canvas.fogRegion.append(pos)
        self.canvas.fogRegion.append(self.start)
        self.canvas.UpdateMap()

