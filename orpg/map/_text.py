from math import sqrt

import wx

import orpg.dirpath
from orpg.orpgCore import *

from _object import MapObject

class MapText(MapObject):
    def __init__(self, canvas, start=wx.Point(0,0), text='', size=12, weight=wx.NORMAL, style=wx.NORMAL, color="#000000"):
        MapObject.__init__(self, canvas=canvas)
        self.start = start
        self.color = color
        self.text = text
        self.weight = weight
        self.style = style
        self.size = size

        r, g, b = self.RGBHex.rgb_tuple(self.color)
        self.hcolor = self.RGBHex.hexstring(r^255, g^255, b^255)

        self.id = 'text-' + self.canvas.GetNewObjectId()


    def Draw(self, dc):
        if not self.highlighed:
            c = self.color
        else:
            c = self.hcolor

        font = wx.Font(self.size, wx.DEFAULT, self.weight, self.style)
        dc.SetFont(font, c)
        w, h = dc.GetTextExtent(self.text)


        if self.IsShown():
            dc.DrawText(self.text, self.start.x-(w/2), self.start.y-(h/2))
        elif self.canvas.toolWnd.gmToolBar.IsShown():
            r, g, b = self.RGBHex.rgb_tuple(c)
            dc.SetFont(font, wx.Color(r, g, b, 40))
            dc.DrawText(self.text, self.start.x-(w/2), self.start.y-(h/2))


        if self.selected:
            self.DrawSelection(dc)

    def DrawSelection(self, dc):
        w, h = dc.GetTextExtent(self.text)
        dc.SetBrush(wx.GREEN_BRUSH)
        dc.SetPen(wx.GREEN_PEN)
        path = dc.CreatePath()

        path.AddRectangle(self.start.x-((w/2)+1), self.start.y-((h/2)+1), 5, 5)
        path.AddRectangle(self.start.x-((w/2)+1), self.start.y+((h/2)+1), 5, 5)
        path.AddRectangle(self.start.x+((w/2)+1), self.start.y-((h/2)+1), 5, 5)
        path.AddRectangle(self.start.x+((w/2)+1), self.start.y+((h/2)+1), 5, 5)

        dc.DrawPath(path)

        dc.SetBrush(wx.NullBrush)
        dc.SetPen(wx.NullPen)

    def InObject(self, pos):
        dc = wx.ClientDC(self.canvas)
        self.canvas.PrepareDC(dc)
        font = wx.Font(self.size, wx.DEFAULT, self.weight, self.style)
        w, h = dc.GetTextExtent(self.text)
        rgn = wx.RegionFromPoints([(self.start.x-(w/2), self.start.y-(h/2)), (self.start.x-(w/2), self.start.y+(h/2)), (self.start.x+(w/2), self.start.y-(h/2)), (self.start.x+(w/2), self.start.y+(h/2))])

        if rgn.Contains(pos.x, pos.y):
            return True

        return False

    def GetName(self):
        return self.text + ' Color:' + self.color

    def ShowProperties(self, event):
        dlg = wx.Dialog(self.canvas, wx.ID_ANY, "Circle Properties")
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        text = wx.TextCtrl(dlg, wx.ID_ANY)
        text.SetValue(self.text)

        colorbtn = wx.Button(dlg, wx.ID_ANY, "Color")
        colorbtn.SetForegroundColour(self.color)

        size = wx.SpinCtrl(dlg, wx.ID_ANY, value=str(self.size), min=7, initial=12, name="Font Size: ")

        weight = wx.Choice(dlg, wx.ID_ANY, choices=["Normal", "Bold"])
        if self.weight == wx.NORMAL:
            weight.SetSelection(0)
        else:
            weight.SetSelection(1)

        style = wx.Choice(dlg, wx.ID_ANY, choices=["Normal", "Italic"])
        if self.weight == wx.NORMAL:
            style.SetSelection(0)
        else:
            style.SetSelection(1)

        def ColorBtn(event):
            newcolor = self.RGBHex.do_hex_color_dlg(self.canvas)
            if newcolor == None:
                return

            colorbtn.SetForegroundColour(newcolor)
            dlg.Unbind(wx.EVT_BUTTON)

        dlg.Bind(wx.EVT_BUTTON, ColorBtn, colorbtn)

        sizer.Add(wx.StaticText(dlg, wx.ID_ANY, "Text:"), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        sizer.Add(text, 0, wx.EXPAND|wx.ALL, 3)
        sizer.Add(size, 0, wx.ALL, 2)
        sizer.Add(weight, 0, wx.ALL, 3)
        sizer.Add(style, 0, wx.ALL, 2)
        sizer.Add(colorbtn, 0, wx.ALL, 3)
        sizer.Add(wx.Button(dlg, wx.ID_OK), 0, wx.ALL, 2)

        dlg.SetSizer(sizer)
        dlg.SetAutoLayout(True)
        dlg.Fit()
        dlg.Show()

        if dlg.ShowModal() == wx.ID_OK:
            self.text = text.GetValue()
            r,g,b = colorbtn.GetForegroundColour().Get()
            self.color = self.RGBHex.hexstring(r, g, b)
            self.hcolor = self.RGBHex.hexstring(r^255, g^255, b^255)
            self.size = int(size.GetValue())
            if weight.GetSelection() == 0:
                self.weight = wx.NORMAL
            else:
                self.weight = wx.BOLD

            if style.GetSelection() == 0:
                self.style = wx.NORMAL
            else:
                self.style = wx.ITALIC

            if event != None:
                self.Update(send=True, action="update")


    def OnLeftDown(self, pos):
        self.ShowProperties(None)
        self.color = self.canvas.whiteboardColor
        if self.text != '':
            self.canvas.zOrder['front'].append(MapText(self.canvas, pos, self.text, self.size, self.weight, self.style, self.color))
            self.Update(send=True, action='new')

        self.text = ''
        self.weight = wx.NORMAL
        self.size = 12
        self.style = wx.NORMAL
        self.color = self.canvas.whiteboardColor
        self.hcolor = self.canvas.whiteboardColor

    def _toxml(self, action="update"):
        return ''