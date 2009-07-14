from threading import Lock
import mimetypes
import xml.dom.minidom as minidom

import wx

import orpg.dirpath
from orpg.orpgCore import *
from orpg.tools.rgbhex import RGBHex
import orpg.tools.ButtonPanel as BP

from _canvas import MapCanvas

class MapWnd(wx.Panel):
    def __init__(self, parent, openrpg):
        wx.Panel.__init__(self, parent, wx.ID_ANY)
        self.openrpg = openrpg
        self.log = self.openrpg.get_component("log")
        self.xml = self.openrpg.get_component("xml")
        self.dir_struct = self.openrpg.get_component("dir_struct")
        self.validate = self.openrpg.get_component("validate")
        self.settings = self.openrpg.get_component("settings")

        self.Freeze()
        sizer = wx.GridBagSizer(hgap=1, vgap=1)
        sizer.SetEmptyCellSize((0,0))

        self.canvas = MapCanvas(self, self.openrpg)
        sizer.Add(self.canvas, (0,0), flag=wx.EXPAND)

        self.gmToolBar = BP.ButtonPanel(self, wx.ID_ANY)
        sizer.Add(self.gmToolBar, (1,0), flag=wx.EXPAND)
        self.playerToolBar = BP.ButtonPanel(self, wx.ID_ANY)
        sizer.Add(self.playerToolBar, (2,0), flag=wx.EXPAND)

        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(0)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        self._CreateToolBar()

        self.Bind(wx.EVT_MOUSEWHEEL, self.canvas.OnZoom)
        self.Bind(wx.EVT_KEY_DOWN, self.canvas.OnKey)
        self.Bind(wx.EVT_KEY_UP, self.canvas.OnKey)
        self.Layout()
        self.Thaw()

        wx.CallAfter(self.PostLoad)

    #Public API
    def PostLoad(self):
        self.canvas.Clear()
        #self.canvas.roleTimer.Start(100)
        self.canvas.UpdateMap()

    #Events


    #Private Methods
    def _SetColorBtn(self, color, btn):
        dc = wx.MemoryDC()
        bmp = wx.EmptyBitmap(16, 16)
        dc.SelectObject(bmp)
        dc.SetBrush(wx.Brush(color))
        dc.DrawRectangle(0,0, 16, 16)

        del dc

        btn.SetBitmap(bmp)

    def _CreateToolBar(self):
        self.exclusiveToolList = {}

        self.OpenBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'open.bmp', wx.BITMAP_TYPE_BMP), kind=wx.ITEM_NORMAL, shortHelp="Load New Map", longHelp="Load New Map")
        self.gmToolBar.AddButton(self.OpenBtn)

        self.SaveBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'save.bmp', wx.BITMAP_TYPE_BMP), kind=wx.ITEM_NORMAL, shortHelp="Save Map", longHelp="Save Map")
        self.gmToolBar.AddButton(self.SaveBtn)

        self.DefaultBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'defaultmap.png', wx.BITMAP_TYPE_PNG), kind=wx.ITEM_NORMAL, shortHelp="Load Default Map", longHelp="Load Default Map")
        self.gmToolBar.AddButton(self.DefaultBtn)
        self.Bind(wx.EVT_BUTTON, self.canvas.OnDefaultBtn, id=self.DefaultBtn.GetId())

        self.MapPropsBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'compass.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_NORMAL, shortHelp="Map Properties", longHelp="Map Properties")
        self.gmToolBar.AddButton(self.MapPropsBtn)


        self.gmToolBar.AddSeparator()

        self.BGBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'img.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_NORMAL, shortHelp="Change Background", longHelp="Change Background")
        self.gmToolBar.AddButton(self.BGBtn)
        self.Bind(wx.EVT_BUTTON, self.canvas.OnBGBtn, id=self.BGBtn.GetId())

        self.BGColorBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.EmptyBitmap(16,16), kind=wx.ITEM_NORMAL, shortHelp="Map Background Color", longHelp="Map Background Color")
        self.gmToolBar.AddButton(self.BGColorBtn)
        self._SetColorBtn(wx.GREEN, self.BGColorBtn)
        self.Bind(wx.EVT_BUTTON, self.canvas.OnBGColorBtn, id=self.BGColorBtn.GetId())

        self.TileAddBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'chess.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_NORMAL, shortHelp="Add Map Tile", longHelp="Add Map Tile")
        self.gmToolBar.AddButton(self.TileAddBtn)

        self.TileMoveBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'crosshair.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_CHECK, shortHelp="Edit Tiles", longHelp="Edit Tiles")
        self.gmToolBar.AddButton(self.TileMoveBtn)
        self.exclusiveToolList[self.TileMoveBtn.GetId()] = self.TileMoveBtn
        self.Bind(wx.EVT_BUTTON, self.canvas.OnExlusiveBtn, id=self.TileMoveBtn.GetId())

        self.GridBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'grid.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_NORMAL, shortHelp="Set Grid", longHelp="Set Grid")
        self.gmToolBar.AddButton(self.GridBtn)

        self.gmToolBar.AddSeparator()

        self.FogBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'fogon.png', wx.BITMAP_TYPE_PNG), kind=wx.ITEM_CHECK, shortHelp="Turn Fog On", longHelp="Turn Fog On")
        self.gmToolBar.AddButton(self.FogBtn)
        self.Bind(wx.EVT_BUTTON, self.canvas.OnFogBtn, id=self.FogBtn.GetId())

        self.FogToolBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'showfog.png', wx.BITMAP_TYPE_PNG), kind=wx.ITEM_CHECK, shortHelp="Show Tool", longHelp="Show Tool")
        self.gmToolBar.AddButton(self.FogToolBtn)
        self.exclusiveToolList[self.FogToolBtn.GetId()] = self.FogToolBtn
        self.Bind(wx.EVT_BUTTON, self.canvas.OnExlusiveBtn, id=self.FogToolBtn.GetId())
        menu = wx.Menu("Fog Tool")
        item = wx.MenuItem(menu, 1, "Show", "Show")
        self.Bind(wx.EVT_MENU, self.OnFogSelection, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, 2, "Hide", "Hide")
        self.Bind(wx.EVT_MENU, self.OnFogSelection, item)
        menu.AppendItem(item)
        self.currentFog = 'Show'
        self.FogToolBtn.SetMenu(menu)

        self.FogColorBtn = BP.ButtonInfo(self.gmToolBar, wx.ID_ANY, wx.EmptyBitmap(16,16), kind=wx.ITEM_NORMAL, shortHelp="Fog Color", longHelp="Fog Color")
        self.gmToolBar.AddButton(self.FogColorBtn)
        self._SetColorBtn(wx.BLACK, self.FogColorBtn)
        self.Bind(wx.EVT_BUTTON, self.canvas.OnFogColorBtn, id=self.FogColorBtn.GetId())

        self.gmToolBar.AddSeparator()

        self.MiniPropsBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'questionhead.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_NORMAL, shortHelp="Miniture Properties", longHelp="Miniture Properties")
        self.gmToolBar.AddButton(self.MiniPropsBtn)

        self.gmToolBar.DoLayout()

        self.SelectorBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'mouse.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_CHECK, shortHelp="Selection Tool", longHelp="Selection Tool")
        self.playerToolBar.AddButton(self.SelectorBtn)
        self.exclusiveToolList[self.SelectorBtn.GetId()] = self.SelectorBtn
        self.Bind(wx.EVT_BUTTON, self.canvas.OnExlusiveBtn, id=self.SelectorBtn.GetId())

        self.MeasureBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'tape.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_CHECK, shortHelp="Measure Tool", longHelp="Measure Tool")
        self.playerToolBar.AddButton(self.MeasureBtn)
        self.exclusiveToolList[self.MeasureBtn.GetId()] = self.MeasureBtn
        self.Bind(wx.EVT_BUTTON, self.canvas.OnExlusiveBtn, id=self.MeasureBtn.GetId())

        self.ColorBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.EmptyBitmap(16,16), kind=wx.ITEM_NORMAL, shortHelp="Select a Color", longHelp="Select a Color")
        self.playerToolBar.AddButton(self.ColorBtn)
        self._SetColorBtn(wx.BLACK, self.ColorBtn)
        self.Bind(wx.EVT_BUTTON, self.canvas.OnColorBtn, id=self.ColorBtn.GetId())

        self.DrawBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'draw.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_CHECK, shortHelp="Freehand Line Tool", longHelp="Freehand Line Tool")
        self.playerToolBar.AddButton(self.DrawBtn)
        self.exclusiveToolList[self.DrawBtn.GetId()] = self.DrawBtn
        self.Bind(wx.EVT_BUTTON, self.canvas.OnExlusiveBtn, id=self.DrawBtn.GetId())
        menu = wx.Menu("Line Tool")
        item = wx.MenuItem(menu, 3, "Free Draw", "Free Draw")
        self.Bind(wx.EVT_MENU, self.OnLineSelection, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, 4, "Poly Draw", "Poly Draw")
        self.Bind(wx.EVT_MENU, self.OnLineSelection, item)
        menu.AppendItem(item)
        self.currentLine = 'Free'
        self.DrawBtn.SetMenu(menu)

        self.AddTextBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'text.png', wx.BITMAP_TYPE_PNG), kind=wx.ITEM_CHECK, shortHelp="Add Text Tool", longHelp="Add Text Tool")
        self.playerToolBar.AddButton(self.AddTextBtn)
        self.exclusiveToolList[self.AddTextBtn.GetId()] = self.AddTextBtn
        self.Bind(wx.EVT_BUTTON, self.canvas.OnExlusiveBtn, id=self.AddTextBtn.GetId())

        self.AddShapeBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'circle.png', wx.BITMAP_TYPE_PNG), kind=wx.ITEM_CHECK, shortHelp="Add Shape Tool", longHelp="Add Shape Tool")
        self.playerToolBar.AddButton(self.AddShapeBtn)
        self.exclusiveToolList[self.AddShapeBtn.GetId()] = self.AddShapeBtn
        self.Bind(wx.EVT_BUTTON, self.canvas.OnExlusiveBtn, id=self.AddShapeBtn.GetId())
        menu = wx.Menu("Shape Tool")
        item = wx.MenuItem(menu, 5, "Circle", "Circle")
        self.Bind(wx.EVT_MENU, self.OnShapeSelection, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, 6, "Rectangle", "Rectangle")
        self.Bind(wx.EVT_MENU, self.OnShapeSelection, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, 7, "Arc", "Arc")
        self.Bind(wx.EVT_MENU, self.OnShapeSelection, item)
        menu.AppendItem(item)
        self.currentShape = 'Circle'
        self.AddShapeBtn.SetMenu(menu)

        self.LineWidth = wx.Choice(self.playerToolBar, wx.ID_ANY, choices=["1","2","3","4","5","6","7","8","9","10"])
        self.LineWidth.SetSelection(0)
        self.playerToolBar.AddControl(self.LineWidth)

        self.playerToolBar.AddSeparator()

        self.MiniBtn = BP.ButtonInfo(self.playerToolBar, wx.ID_ANY, wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'player.gif', wx.BITMAP_TYPE_GIF), kind=wx.ITEM_NORMAL, shortHelp="Add Mini", longHelp="Add Mini")
        self.playerToolBar.AddButton(self.MiniBtn)

        self.playerToolBar.DoLayout()

    def OnShapeSelection(self, event):
        id = event.GetId()
        if id == 5:
            self.currentShape = 'Circle'
            self.AddShapeBtn.Bitmap = wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'circle.png', wx.BITMAP_TYPE_PNG)
        elif id == 6:
            self.currentShape = 'Rectangle'
            self.AddShapeBtn.Bitmap = wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'rectangle.png', wx.BITMAP_TYPE_PNG)
        elif id == 7:
            self.currentShape = 'Arc'
            self.AddShapeBtn.Bitmap = wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'arc.png', wx.BITMAP_TYPE_PNG)

    def OnLineSelection(self, event):
        id = event.GetId()
        if id == 3:
            self.currentLine = 'Free'
            self.DrawBtn.Bitmap = wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'draw.gif', wx.BITMAP_TYPE_GIF)
            self.DrawBtn.SetShortHelp("Freehand Line Tool")
            self.DrawBtn.SetLongHelp("Freehand Line Tool")
        elif id == 4:
            self.currentLine = 'Poly'
            self.DrawBtn.Bitmap = wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'dash.png', wx.BITMAP_TYPE_PNG)
            self.DrawBtn.SetShortHelp("Poly Line Tool")
            self.DrawBtn.SetLongHelp("Poly Line Tool")

    def OnFogSelection(self, event):
        id = event.GetId()
        if id == 1:
            self.currentFog = 'Show'
            self.FogToolBtn.Bitmap = wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'showfog.png', wx.BITMAP_TYPE_PNG)
            self.FogToolBtn.SetShortHelp("Show Fog Tool")
            self.FogToolBtn.SetLongHelp("Show Fog Tool")
        elif id == 2:
            self.currentFog = 'Hide'
            self.FogToolBtn.Bitmap = wx.Bitmap(orpg.dirpath.dir_struct["icon"] + 'hidefog.png', wx.BITMAP_TYPE_PNG)
            self.FogToolBtn.SetShortHelp("Hide Fog Tool")
            self.FogToolBtn.SetLongHelp("Hide Fog Tool")

### Test Stuff
class BlankFrame(wx.Frame):
    def __init__(self, openrpg):
        wx.Frame.__init__(self, None, title="New Map Test Window", size=(740,480))

        self.map = MapWnd(self, openrpg)
        self.basesizer = wx.BoxSizer(wx.VERTICAL)
        self.basesizer.Add(self.map, 1, wx.EXPAND)

        self.SetSizer(self.basesizer)
        self.SetAutoLayout(True)
        #self.Fit()


class BlankApp(wx.App):
    def OnInit(self):
        self.frame = BlankFrame()
        self.frame.Show()
        self.SetTopWindow(self.frame)


        return True

if __name__ == "__main__":
    app = BlankApp(0)
    app.MainLoop()