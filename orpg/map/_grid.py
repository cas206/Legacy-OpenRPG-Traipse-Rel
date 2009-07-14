import wx

import orpg.dirpath
from orpg.orpgCore import *
from orpg.tools.rgbhex import RGBHex

class GridLayer:
    def __init__(self, canvas):
        self.canvas = canvas
        self.RGBHex = RGBHex()

    def Draw(self, dc):
        r, g, b = self.RGBHex.rgb_tuple(self.canvas.gridColor)
        pen = wx.Pen(wx.Color(r, g, b, 255), 1, self.canvas.gridLines)
        dc.SetPen(pen)

        path = dc.CreatePath()

        if self.canvas.gridType == 'Square':
            self._DrawSquare(dc, path)

        dc.SetPen(wx.NullPen)

    def _DrawSquare(self, dc, path):
        path.MoveToPoint(0, 0)
        y = 0
        while y < self.canvas.size[1]:
            path.AddLineToPoint(self.canvas.size[0], y)
            y += self.canvas.gridSize
            path.MoveToPoint(0, y)

        path.MoveToPoint(0, 0)
        x = 0
        while x < self.canvas.size[0]:
            path.AddLineToPoint(x, self.canvas.size[0])
            x += self.canvas.gridSize
            path.MoveToPoint(x, 0)

        dc.StrokePath(path)