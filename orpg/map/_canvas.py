from threading import Lock
import mimetypes
import xml.dom.minidom as minidom

import wx

import orpg.dirpath
from orpg.orpgCore import *
from orpg.tools.rgbhex import RGBHex

from _object import *

from _circles import MapCircle
from _text import MapText
from _lines import MapLine
from _grid import GridLayer
from _fog import FogLayer

USE_BUFFER = True
if "wxMAC" in wx.PlatformInfo:
    USE_BUFFER = False

class MapCanvas(wx.ScrolledWindow):
    def __init__(self, parent, openrpg):
        wx.ScrolledWindow.__init__(self, parent, wx.ID_ANY, style=wx.HSCROLL | wx.VSCROLL | wx.NO_FULL_REPAINT_ON_RESIZE | wx.SUNKEN_BORDER)

        self.openrpg = openrpg
        self.log = self.openrpg.get_component("log")
        self.xml = self.openrpg.get_component("xml")
        self.dir_struct = self.openrpg.get_component("dir_struct")
        self.validate = self.openrpg.get_component("validate")
        self.settings = self.openrpg.get_component("settings")
        self.session = self.openrpg.get_component("session")
        self.chat = self.openrpg.get_component("chat")

        self.lock = Lock()

        self.RGBHex = RGBHex()

        self.toolWnd = parent

        self.shift = False
        self.ctrl = False

        self.selectedObjects = []
        self.overObjects = []
        self._objectId = 0

        self.gridLayer = GridLayer(self)
        self.circleLayer = MapCircle(self)
        self.textLayer = MapText(self)
        self.lineLayer = MapLine(self)
        self.fogLayer = FogLayer(self)

        self.zOrder = {}
        self.zOrder['tiles'] = []
        self.zOrder["back"] = []
        self.zOrder["front"] = []

        self.bgImage = None
        self.bgType = 'Image'
        self.bgPath = None
        self.backgroundColor = '#008040'

        self.gridType = 'Square'
        self.gridLines = wx.SOLID
        self.gridSnap = True
        self.gridSize = 60
        self.gridColor = "#000000"

        self.whiteboardColor = "#000000"

        self.zoomScale = 1.0
        self.lastZoomTime = time.time()
        self.lastZoomScale = 1.0

        self.useFog = False
        self.fogRegion = []
        self.fogColor = "#000000"

        self.zoomScale = 1.0
        self.lastZoomTime = time.time()
        self.lastZoomScale = 1.0
        self.zoomTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnZoomTimer, self.zoomTimer)
        #self.zoomTimer.Start(1000)

        self.imageCache = {}

        self._SetSize((1000,1000))

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_MOUSEWHEEL, self.OnZoom)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)
        self.Bind(wx.EVT_LEFT_DCLICK, self.OnLeftDClick)
        self.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
        self.Bind(wx.EVT_MOTION, self.OnMotion)
        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnBackground)
        self.Bind(wx.EVT_KEY_DOWN, self.OnKey)
        self.Bind(wx.EVT_KEY_UP, self.OnKey)

        self.Bind(EVT_ENTER_OBJECT, self.EnterObject)
        self.Bind(EVT_LEAVE_OBJECT, self.LeaveObject)
        self.Bind(EVT_SELECT_OBJECT, self.ObjectSelected)
        self.Bind(EVT_DESELECT_OBJECT, self.ObjectDeselected)

        self.roleTimer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnRoleTimer, self.roleTimer)

        wx.CallAfter(self.OnSize, None)


    #Public API
    def UpdateMap(self, send=True):
        cdc = wx.ClientDC(self)
        self.PrepareDC(cdc)
        cdc.SetBackgroundMode(wx.TRANSPARENT)
        if USE_BUFFER:
            bdc = wx.BufferedDC(cdc, self._buffer)
            bdc.Clear()
            dc = wx.GraphicsContext.Create(bdc)
        else:
            cdc.Clear()
            dc = wx.GraphicsContext.Create(cdc)


        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)

        #Draw BG Color
        r,g,b = self.RGBHex.rgb_tuple(self.backgroundColor)
        brush = wx.Brush(wx.Color(r,g,b,255))
        dc.SetBrush(brush)

        path = dc.CreatePath()

        dc.PushState()
        path.AddRectangle(0, 0, self.size[0]+2, self.size[1]+2)
        dc.DrawPath(path)
        dc.PopState()

        dc.SetBrush(wx.NullBrush)

        #Set the Zoom
        dc.Scale(self.zoomScale, self.zoomScale)

        #Draw BG Image
        if self.bgImage != None:
            if self.bgType == 'Image':
                dc.DrawBitmap(self.bgImage, self.offset[0], self.offset[1], self.bgImage.GetWidth(), self.bgImage.GetHeight())
            else:
                bmpW = self.bgImage.GetWidth()
                bmpH = self.bgImage.GetHeight()

                pos = wx.Point(self.offset[0], self.offset[1])
                while pos.x < self.size[0]:
                    dc.DrawBitmap(self.bgImage, pos.x, pos.y, self.bgImage.GetWidth(), self.bgImage.GetHeight())
                    while pos.y < self.size[1]:
                        pos.y += bmpH
                        dc.DrawBitmap(self.bgImage, pos.x, pos.y, self.bgImage.GetWidth(), self.bgImage.GetHeight())
                    pos.y = 0
                    pos.x += bmpW

        #Draw Tiles
        for tile in self.zOrder['tiles']:
            tile.Draw(dc)

        #Draw Grid
        self.gridLayer.Draw(dc)

        #Draw Objects
        for object in self.zOrder['back']:
            object.Draw(dc)

        zl = self.zOrder.keys()
        zl.remove('back')
        zl.remove('front')
        zl.remove('tiles')
        zl.sort()

        for layer in zl:
            for object in self.zOrder[layer]:
                object.Draw(dc)

        for object in self.zOrder['front']:
            object.Draw(dc)


        #Draw Fog
        if self.useFog:
            self.fogLayer.Draw(dc)

        dc.SetBrush(wx.NullBrush)

        dc.Scale(1/self.zoomScale, 1/self.zoomScale)

        if self.zoomScale != 1.0:
            pos = self.GetViewStart()
            unit = self.GetScrollPixelsPerUnit()
            pos = [pos[0]*unit[0],pos[1]*unit[1]]
            font = wx.Font(8, wx.DEFAULT, wx.NORMAL, wx.NORMAL)
            dc.SetFont(font, wx.BLACK)

            dc.DrawText("Zoom Factor: " + str(self.zoomScale), pos[0], pos[1], dc.CreateBrush(wx.WHITE_BRUSH))

    def Clear(self):
        self._SetSize((1000,1000))
        self.selectedObjects = []
        self.overObjects = []
        self._objectId = 0
        self.bgImage = None
        self.bgType = 'Image'
        self.bgPath = None

        self.backgroundColor = '#008040'
        r, g, b = self.RGBHex.rgb_tuple(self.backgroundColor)
        self.toolWnd._SetColorBtn(wx.Color(r, g, b, 255), self.toolWnd.BGColorBtn)

        self.gridType = 'Square'
        self.gridLines = wx.SOLID
        self.gridSnap = True
        self.gridSize = 60
        self.gridColor = "#000000"

        self.whiteboardColor = "#000000"
        r, g, b = self.RGBHex.rgb_tuple(self.whiteboardColor)
        self.toolWnd._SetColorBtn(wx.Color(r, g, b, 255), self.toolWnd.ColorBtn)

        self.zoomScale = 1.0
        self.lastZoomTime = time.time()
        self.lastZoomScale = 1.0

        self.useFog = False
        self.fogRegion = []
        self.fogColor = "#000000"

        self.OnRemoveAllObjects(None)

        self.toolWnd.Freeze()
        for btn in self.toolWnd.exclusiveToolList:
            self.toolWnd.exclusiveToolList[btn].SetToggled(False)

        self.toolWnd.FogBtn.SetToggled(False)
        self.toolWnd.SelectorBtn.SetToggled(True)
        self.toolWnd.Thaw()

    def GetNewObjectId(self):
        return str(self._objectId+1)

    #Map Events
    def OnBackground(self, event):
        #Dont do it
        pass

    def OnPaint(self, event):
        if USE_BUFFER:
            dc = wx.PaintDC(self)
            self.PrepareDC(dc)
            dc.DrawBitmap(self._buffer, 0, 0)
        else:
            event.Skip()


    def OnSize(self, event):
        self._buffer = wx.EmptyBitmap(self.size[0], self.size[1])
        self._FixScroll()
        wx.CallAfter(self.UpdateMap)


    def OnZoom(self, event):
        if event.GetWheelRotation() < 0:
            self.zoomScale -= .1
            if self.zoomScale < .5:
                self.zoomScale = .5
            else:
                self.lastZoomTime = time.time()
                self._FixScroll()
                self.UpdateMap()
        else:
            self.zoomScale += .1

            if self.zoomScale > 1.5:
                self.zoomScale = 1.5
            else:
                self.lastZoomTime = time.time()
                self._FixScroll()
                self.UpdateMap()

    def OnKey(self, event):
        self.shift = False
        self.ctrl = False
        if event.ShiftDown():
            self.shift = True
        elif event.ControlDown():
            self.ctrl = True


    def EnterObject(self, event):
        obj = event.GetObject()
        self.overObjects.append(obj)
        obj.Highlight()

    def LeaveObject(self, event):
        obj = event.GetObject()
        try:
            self.overObjects.remove(obj)
        except:
            pass
        obj.UnHighlight()

    def ObjectSelected(self, event):
        obj = event.GetObject()
        self.selectedObjects.append(obj)
        try:
            self.overObjects.remove(obj)
        except:
            pass
        obj.UnHighlight()

    def ObjectDeselected(self, event):
        obj = event.GetObject()
        try:
            self.selectedObjects.remove(obj)
        except:
            pass
        obj.Update()

    def OnLeftDown(self, event):
        dc = wx.ClientDC(self)
        self.PrepareDC(dc)
        pos = event.GetLogicalPosition(dc)
        pos.x /= self.zoomScale
        pos.y /= self.zoomScale

        if self.toolWnd.AddShapeBtn.GetToggled() and self.toolWnd.currentShape == 'Circle':
            self.circleLayer.OnLeftDown(pos)

        elif self.toolWnd.AddTextBtn.GetToggled():
            self.textLayer.OnLeftDown(pos)

        elif self.toolWnd.DrawBtn.GetToggled():
            self.lineLayer.OnLeftDown(pos)

        elif self.toolWnd.SelectorBtn.GetToggled() and (self.selectedObjects == [] or self.ctrl or self.shift) and not (self.useFog and self.fogLayer.region.Contains(pos.x, pos.y) and not self.toolWnd.gmToolBar.IsShown()):
            self.initiatPos = pos
            self.lxd = 0
            self.lyd = 0
            if len(self.overObjects) == 0:
                return
            elif len(self.overObjects) == 1:
                self.overObjects[0].Select()
            else:
                if not self.shift:
                    menu = wx.Menu("Object Selection")
                    id = 0
                    for obj in self.overObjects:
                        menu.Append(id, obj.GetName())
                        id += 1

                    def selectmenu(event):
                        id = event.GetId()
                        self.overObjects[id].Select()
                        self.Unbind(wx.EVT_MENU)

                    self.Bind(wx.EVT_MENU, selectmenu)
                    self.PopupMenu(menu)
                else:
                    for i in xrange(len(self.overObjects)):
                        self.overObjects[0].Select()

        elif self.toolWnd.SelectorBtn.GetToggled() and not self.selectedObjects == []:
            xd = (self.initiatPos.x+pos.x)*(self.initiatPos.x+pos.x)
            yd = (self.initiatPos.y+pos.y)*(self.initiatPos.y+pos.y)

            for i in xrange(len(self.selectedObjects)):
                self.selectedObjects[0].Deselect()

        elif self.toolWnd.FogToolBtn.GetToggled():
            self.fogLayer.OnLeftDown(pos)

    def OnLeftDClick(self, event):
        dc = wx.ClientDC(self)
        self.PrepareDC(dc)
        pos = event.GetLogicalPosition(dc)
        pos.x /= self.zoomScale
        pos.y /= self.zoomScale

        if self.toolWnd.DrawBtn.GetToggled():
            self.lineLayer.OnLeftDClick(pos)

    def OnLeftUp(self, event):
        dc = wx.ClientDC(self)
        self.PrepareDC(dc)
        pos = event.GetLogicalPosition(dc)
        pos.x /= self.zoomScale
        pos.y /= self.zoomScale

        if self.toolWnd.AddShapeBtn.GetToggled() and self.toolWnd.currentShape == 'Circle':
            self.circleLayer.OnLeftUp(pos)

        elif self.toolWnd.FogToolBtn.GetToggled():
            self.fogLayer.OnLeftUp(pos)

        elif self.toolWnd.DrawBtn.GetToggled():
            self.lineLayer.OnLeftUp(pos)

        elif self.toolWnd.SelectorBtn.GetToggled() and self.selectedObjects == []:
            rgn = wx.Region(self.initiatPos.x, self.initiatPos.y, self.lxd, self.lyd)

            for object in self.zOrder['back']:
                if rgn.Contains(object.start.x, object.start.y):
                    object.Select()

            zl = self.zOrder.keys()
            zl.remove('back')
            zl.remove('front')
            zl.remove('tiles')
            zl.sort()

            for layer in zl:
                for object in self.zOrder[layer]:
                    if rgn.Contains(object.start.x, object.start.y):
                        object.Select()

            for object in self.zOrder['front']:
                if rgn.Contains(object.start.x, object.start.y):
                    object.Select()

            self.lxd = 0
            self.lyd = 0
            self.initiatPos = pos
        self.Refresh()

    def OnMotion(self, event):
        dc = wx.ClientDC(self)
        self.PrepareDC(dc)
        pos = event.GetLogicalPosition(dc)
        pos.x /= self.zoomScale
        pos.y /= self.zoomScale


        #HitTest
        for object in self.zOrder['back']:
            object.HitTest(pos)

        zl = self.zOrder.keys()
        zl.remove('back')
        zl.remove('front')
        zl.remove('tiles')
        zl.sort()

        for layer in zl:
            for object in self.zOrder[layer]:
                object.HitTest(pos)

        for object in self.zOrder['front']:
            object.HitTest(pos)

        if self.toolWnd.AddShapeBtn.GetToggled() and event.m_leftDown and self.toolWnd.currentShape == 'Circle':
            self.circleLayer.OnMotion(pos)

        elif self.toolWnd.DrawBtn.GetToggled() and self.lineLayer.start != wx.Point(0,0):
            self.lineLayer.OnMotion(pos)

        elif self.toolWnd.SelectorBtn.GetToggled() and self.selectedObjects != [] and not (self.ctrl or self.shift):
            xd = (pos.x-self.initiatPos.x)
            yd = (pos.y-self.initiatPos.y)
            for obj in self.selectedObjects:
                obj.start.x += xd
                obj.start.y += yd
                obj.Update()
                self.initiatPos = pos


        elif self.toolWnd.SelectorBtn.GetToggled() and self.selectedObjects == [] and event.m_leftDown:
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            pen = wx.Pen(wx.BLACK, 3, wx.DOT)
            dc.SetPen(pen)
            dc.SetLogicalFunction(wx.INVERT)

            xd = (pos.x-self.initiatPos.x)
            yd = (pos.y-self.initiatPos.y)

            if self.lxd != 0 and self.lyd != 0:
                r = wx.Rect(self.initiatPos.x, self.initiatPos.y, self.lxd, self.lyd)
                dc.DrawRectangleRect(r)

            self.lxd = xd
            self.lyd = yd
            r = wx.Rect(self.initiatPos.x, self.initiatPos.y, self.lxd, self.lyd)
            dc.DrawRectangleRect(r)

        elif (self.toolWnd.FogToolBtn.GetToggled()) and event.m_leftDown:
            self.fogLayer.OnMotion(pos)

    def OnRightDown(self, event):
        mapmenu = wx.Menu()

        item = wx.MenuItem(mapmenu, wx.ID_ANY, "Load Map", "Load Map")
        #self.Bind(wx.EVT_MENU, self.OnOpenBtn, item)
        mapmenu.AppendItem(item)

        item = wx.MenuItem(mapmenu, wx.ID_ANY, "Save Map", "Save Map")
        #self.Bind(wx.EVT_MENU, self.OnSaveBtn, item)
        mapmenu.AppendItem(item)

        item = wx.MenuItem(mapmenu, wx.ID_ANY, "Default Map", "Default Map")
        self.Bind(wx.EVT_MENU, self.OnDefaultBtn, item)
        mapmenu.AppendItem(item)

        item = wx.MenuItem(mapmenu, wx.ID_ANY, "Map Properties", "Map Properties")
        #self.Bind(wx.EVT_MENU, OnMapPropsBtn, item)
        mapmenu.AppendItem(item)

        bgmenu = wx.Menu()

        item = wx.MenuItem(bgmenu, wx.ID_ANY, "Change Background Image", "Change Background Image")
        self.Bind(wx.EVT_MENU, self.OnBGBtn, item)
        bgmenu.AppendItem(item)

        item = wx.MenuItem(bgmenu, wx.ID_ANY, "Change Background Color", "Change Background Color")
        self.Bind(wx.EVT_MENU, self.OnBGColorBtn, item)
        bgmenu.AppendItem(item)

        item = wx.MenuItem(bgmenu, wx.ID_ANY, "Grid Properties", "Grid Properties")
        #self.Bind(wx.EVT_MENU, self.OnGridBtn, item)
        bgmenu.AppendItem(item)

        fogmenu = wx.Menu()

        item = wx.MenuItem(fogmenu, wx.ID_ANY, "Toggle Fog", "Toggle Fog")
        self.Bind(wx.EVT_MENU, self.OnFogBtn, item)
        fogmenu.AppendItem(item)

        item = wx.MenuItem(fogmenu, wx.ID_ANY, "Fog Color", "Fog Color")
        self.Bind(wx.EVT_MENU, self.OnFogColorBtn, item)
        fogmenu.AppendItem(item)

        menu = wx.Menu()

        if self.toolWnd.gmToolBar.IsShown():
            menu.AppendMenu(wx.ID_ANY, "Map", mapmenu)
            menu.AppendMenu(wx.ID_ANY, "Background", bgmenu)
            menu.AppendMenu(wx.ID_ANY, "Fog", fogmenu)
            menu.AppendSeparator()
            item = wx.MenuItem(menu, wx.ID_ANY, "Miniture Properties", "Miniture Properties")
            #self.Bind(wx.EVT_MENU, self.OnColorBtn, item)
            menu.AppendItem(item)
            menu.AppendSeparator()

        item = wx.MenuItem(menu, wx.ID_ANY, "Whiteboard Color", "Whiteboard Color")
        self.Bind(wx.EVT_MENU, self.OnColorBtn, item)
        menu.AppendItem(item)


        def ObjectMenu(event):
            id = event.GetId()
            objid = int(menu.GetHelpString(id))
            menuname = menu.GetLabel(id)
            obj = self.overObjects[objid]

            if menuname == "Move To Back":
                self.MoveToBack(obj)

            elif menuname == "Move Back":
                self.MoveBack(obj)

            elif menuname == "Move Forward":
                self.MoveForward(obj)

            elif menuname == "Move To Front":
                self.MoveToFront(obj)

            elif menuname == "Remove":
                self.zOrder[obj.zOrder].remove(obj)
                obj.Update()

            self.Unbind(wx.EVT_MENU)
            self.overObjects.remove(obj)


        if len(self.overObjects):
            menu.AppendSeparator()

        id = 0
        for obj in self.overObjects:
            if obj.IsShown() or self.toolWnd.gmToolBar.IsShown():
                objmenu = wx.Menu()
                item = wx.MenuItem(objmenu, wx.ID_ANY, "Move To Back", str(id))
                self.Bind(wx.EVT_MENU, ObjectMenu, item)
                objmenu.AppendItem(item)
                item = wx.MenuItem(objmenu, wx.ID_ANY, "Move Back", str(id))
                self.Bind(wx.EVT_MENU, ObjectMenu, item)
                objmenu.AppendItem(item)
                item = wx.MenuItem(objmenu, wx.ID_ANY, "Move Forward", str(id))
                self.Bind(wx.EVT_MENU, ObjectMenu, item)
                objmenu.AppendItem(item)
                item = wx.MenuItem(objmenu, wx.ID_ANY, "Move To Front", str(id))
                self.Bind(wx.EVT_MENU, ObjectMenu, item)
                objmenu.AppendItem(item)
                objmenu.AppendSeparator()
                if obj.IsShown():
                    item = wx.MenuItem(objmenu, wx.ID_ANY, "Hide", str(id))
                    self.Bind(wx.EVT_MENU, obj.Hide, item)
                    objmenu.AppendItem(item)
                    objmenu.AppendSeparator()
                elif self.toolWnd.gmToolBar.IsShown():
                    item = wx.MenuItem(objmenu, wx.ID_ANY, "Show", str(id))
                    self.Bind(wx.EVT_MENU, obj.Show, item)
                    objmenu.AppendItem(item)
                    objmenu.AppendSeparator()
                item = wx.MenuItem(objmenu, wx.ID_ANY, "Remove", str(id))
                self.Bind(wx.EVT_MENU, ObjectMenu, item)
                objmenu.AppendItem(item)
                item = wx.MenuItem(objmenu, wx.ID_ANY, "Properties", str(id))
                self.Bind(wx.EVT_MENU, obj.ShowProperties, item)
                objmenu.AppendItem(item)
                menu.AppendMenu(wx.ID_ANY, obj.GetName(), objmenu)

        menu.AppendSeparator()
        item = wx.MenuItem(menu, wx.ID_ANY, "Remove All Objects", "Remove All Whiteboard Items")
        self.Bind(wx.EVT_MENU, self.OnRemoveAllObjects, item)
        menu.AppendItem(item)

        self.PopupMenu(menu)


    def OnRemoveAllObjects(self, event):
        for layer in self.zOrder:
            for i in xrange(len(self.zOrder[layer])):
                del self.zOrder[layer][0]

        self.zOrder = {}
        self.zOrder['tiles'] = []
        self.zOrder["back"] = []
        self.zOrder["front"] = []
        if event != None:
            self.UpdateMap()

    def MoveToBack(self, object):
        self.zOrder[object.zOrder].remove(object)
        self.zOrder['back'].append(object)
        object.zOrder = 'back'
        self.UpdateMap()

    def MoveToFront(self, object):
        self.zOrder[object.zOrder].remove(object)
        self.zOrder['front'].append(object)
        object.zOrder = 'front'
        self.UpdateMap()

    def MoveBack(self, object):
        self.zOrder[object.zOrder].remove(object)

        zl = self.zOrder.keys()
        zl.remove('back')
        zl.remove('front')
        zl.remove('tiles')
        zl.sort()
        lzo = 1
        if len(zl):
            lzo = zl.pop()

        if object.zOrder == 'back' or object.zOrder == 1:
            self.zOrder['back'].append(object)
            object.zOrder = 'back'
        elif object.zOrder == 'front':
            if not self.zOrder.has_key(lzo):
                self.zOrder[lzo] = []
            self.zOrder[lzo].append(object)
            object.zOrder = lzo
        else:
            object.zOrder -= 1
            if not self.zOrder.has_key(object.zOrder):
                self.zOrder[object.zOrder] = []
            self.zOrder[object.zOrder].append(object)
        self.UpdateMap()

    def MoveForward(self, object):
        self.zOrder[object.zOrder].remove(object)

        zl = self.zOrder.keys()
        zl.remove('back')
        zl.remove('front')
        zl.remove('tiles')
        zl.sort()
        lzo = 1
        if len(zl):
            lzo = zl.pop()

        if object.zOrder == 'back':
            if not self.zOrder.has_key(1):
                self.zOrder[1] = []
            self.zOrder[1].append(object)
            object.zOrder = 1
        elif z == 'front':
            self.zOrder['front'].append(object)
            object.zOrder = 'front'
        else:
            object.zOrder += 1
            if not self.zOrder.has_key(object.zOrder):
                self.zOrder[object.zOrder] = []
            self.zOrder[object.zOrder].append(object)
        self.UpdateMap()

    def OnScroll(self, event):
        event.Skip()
        self.Refresh()

    def OnZoomTimer(self, event):
        if (time.time() - self.lastZoomTime) >= 3 and self.lastZoomScale != self.zoomScale:
            #Send Zoome Notice to other clients
            self.lastZoomTime = time.time()
            self.lastZoomScale = self.zoomScale

    def OnRoleTimer(self, event):
        #Figure out the users role
        if self.session.my_role() == self.session.ROLE_GM:
            self.role = 'GM'
        elif self.session.my_role() == self.session.ROLE_PLAYER:
            self.role = 'Player'
        else:
            self.role = 'Lurker'

        if self.role == 'GM' and not self.toolWnd.gmToolBar.IsShown() and not (str(self.session.group_id) == '0' and str(self.session.status) == '1'):
            self.toolWnd.Freeze()
            self.toolWnd.gmToolBar.Show()
            self.toolWnd.Thaw()
        elif self.role == 'Player' and not (str(self.session.group_id) == '0' and str(self.session.status) == '1'):
            if self.toolWnd.gmToolBar.IsShown():
                self.toolWnd.Freeze()
                self.toolWnd.gmToolBar.Hide()
                self.toolWnd.Thaw()

            if not self.toolWnd.playerToolBar.IsShown():
                self.toolWnd.Freeze()
                self.toolWnd.playerToolBar.Show()
                self.toolWnd.Thaw()
        elif self.role == 'Lurker' or (str(self.session.group_id) == '0' and str(self.session.status) == '1'):
            if self.toolWnd.playerToolBar.IsShown():
                self.toolWnd.Freeze()
                self.toolWnd.gmToolBar.Hide()
                self.toolWnd.playerToolBar.Hide()
                self.toolWnd.Thaw()

        try:
            self.toolWnd.Layout()
        except:
            pass

    def OnClose(self, event):
        self.zoomTimer.Stop()
        self.roleTimer.Stop()
        event.Skip()

    #Toolbar Events
    def OnDefaultBtn(self, event):
        self.Clear()
        wx.CallAfter(self.UpdateMap)

    def OnColorBtn(self, event):
        newcolor = self.RGBHex.do_hex_color_dlg(self.toolWnd)
        if newcolor == None:
            return

        self.whiteboardColor = newcolor
        r, g, b = self.RGBHex.rgb_tuple(self.whiteboardColor)
        self.toolWnd._SetColorBtn(wx.Color(r, g, b, 255), self.toolWnd.ColorBtn)

    def OnBGColorBtn(self, event):
        newcolor = self.RGBHex.do_hex_color_dlg(self.toolWnd)
        if newcolor == None:
            return

        self.backgroundColor = newcolor
        r, g, b = self.RGBHex.rgb_tuple(self.backgroundColor)
        self.toolWnd._SetColorBtn(wx.Color(r, g, b, 255), self.toolWnd.BGColorBtn)
        self.UpdateMap()

    def OnFogColorBtn(self, event):
        newcolor = self.RGBHex.do_hex_color_dlg(self.toolWnd)
        if newcolor == None:
            return

        self.fogColor = newcolor
        r, g, b = self.RGBHex.rgb_tuple(self.fogColor)
        self.toolWnd._SetColorBtn(wx.Color(r, g, b, 255), self.toolWnd.FogColorBtn)
        self.UpdateMap()

    def OnExlusiveBtn(self, event):
        id = event.GetId()
        #This is backwards because the Toggle Switch does not get set until AFTER The mouse gets released
        if not self.toolWnd.exclusiveToolList[id].GetToggled():
            self.toolWnd.Freeze()
            #Disable all mutualy exclusive tools
            for btn in self.toolWnd.exclusiveToolList:
                if self.toolWnd.exclusiveToolList[btn].GetId() != id:
                    self.toolWnd.exclusiveToolList[btn].SetToggled(False)
            self.toolWnd.Thaw()
        else:
            wx.CallAfter(self.toolWnd.SelectorBtn.SetToggled, True)

    def OnFogBtn(self, event):
        if not self.toolWnd.FogBtn.GetToggled():
            self.useFog = True
        else:
            self.useFog = False
            self.toolWnd.Freeze()
            self.toolWnd.SelectorBtn.SetToggled(True)
            self.toolWnd.FogToolBtn.SetToggled(False)
            self.toolWnd.Thaw()
        self.fogRegion = []
        self.UpdateMap()

    def OnBGBtn(self, event):
        dlg = wx.Dialog(self.toolWnd, wx.ID_ANY, title="Background Properties")
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        filename = wx.TextCtrl(dlg, wx.ID_ANY)
        filename.Hide()

        bgpath = wx.TextCtrl(dlg, wx.ID_ANY)
        if self.bgPath != None:
            bgpath.SetValue(self.bgPath)

        bgtype = wx.Choice(dlg, wx.ID_ANY, choices=['Image', 'Texture'])
        bgtype.SetStringSelection(self.bgType)

        browsebtn = wx.Button(dlg, wx.ID_ANY, "Browse")
        okbtn = wx.Button(dlg, wx.ID_OK)
        cancelbtn = wx.Button(dlg, wx.ID_CANCEL)

        sizer.Add(wx.StaticText(dlg, wx.ID_ANY, "Image Path"), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        sizer.Add(bgpath, 0, wx.EXPAND|wx.ALL, 3)
        sizer.Add(wx.StaticText(dlg, wx.ID_ANY, "Image Type"), 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 2)
        sizer.Add(bgtype, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 3)
        sizer.Add(browsebtn, 0, wx.EXPAND|wx.ALL, 2)
        sizer.Add(okbtn, 0, wx.EXPAND|wx.ALL, 3)
        sizer.Add(cancelbtn, 0, wx.EXPAND|wx.ALL, 2)

        dlg.SetSizer(sizer)
        dlg.SetAutoLayout(True)
        dlg.Fit()

        def OnBrowse(event):
            filedlg = wx.FileDialog(self, "Select an Image File", self.dir_struct["user"], wildcard="Image files (*.bmp, *.gif, *.jpg, *.png)|*.bmp;*.gif;*.jpg;*.png", style=wx.HIDE_READONLY|wx.OPEN)
            if filedlg.ShowModal() != wx.ID_OK:
                filedlg.Destroy()
                return

            bgpath.SetValue(filedlg.GetPath())
            filename.SetValue(filedlg.GetFilename())

        dlg.Bind(wx.EVT_BUTTON, OnBrowse, browsebtn)
        dlg.Show()

        if not dlg.ShowModal() == wx.ID_OK:
            dlg.Destroy()
            return

        self.bgType = bgtype.GetStringSelection()

        if bgpath.GetValue().lower().find('http:') == -1:
            file = open(bgpath.GetValue(), "rb")
            imgdata = file.read()
            file.close()

            (imgtype,j) = mimetypes.guess_type(filename.GetValue())

            postdata = urllib.urlencode({'filename':filename.GetValue(), 'imgdata':imgdata, 'imgtype':imgtype})

            thread.start_new_thread(self.__Upload, (postdata, bgpath.GetValue(), "Background"))
        else:
            self.bgImage = self._LoadImage(bgpath.GetValue())
            self.UpdateMap()


    #Private Methods
    def _SetSize(self, size):
        if size[0] == -1:
            size[0] = self.size[0]
        if size[1] == -1:
            size[1] = self.size[1]

        if size[0] < 300:
            size = (300, size[1])
        if size[1] < 300:
            size = (size[0], 300)

        size1  = self.GetClientSizeTuple()

        if size[0] < size1[0]:
            size = (size1[0], size[1])
        if size[1] < size1[1]:
            size = (size[0], size1[1])

        self.sizeChanged = 1
        self.size = size
        self._FixScroll()

    def _FixScroll(self):
        scale = self.zoomScale
        pos = self.GetViewStart()
        unit = self.GetScrollPixelsPerUnit()
        pos = [pos[0]*unit[0],pos[1]*unit[1]]
        size = self.GetClientSize()
        unit = [10*scale,10*scale]
        if (unit[0] == 0 or unit[1] == 0):
            return
        pos[0] /= unit[0]
        pos[1] /= unit[1]
        mx = [int(self.size[0]*scale/unit[0])+1, int(self.size[1]*scale/unit[1]+1)]
        self.SetScrollbars(unit[0], unit[1], mx[0], mx[1], pos[0], pos[1])

    def _LoadImage(self, path, miniId=None):
        if self.imageCache.has_key(path):
            return self.imageCache[path]

        while len(self.imageCache) > int(self.settings.get_setting("ImageCacheSize")):
            keys = self.imageCache.keys()
            del self.imageCache[keys[0]]


        thread.start_new_thread(self.__DownloadImage, (path, miniId))

        return wx.Bitmap(orpg.dirpath.dir_struct["icon"] + "fetching.png", wx.BITMAP_TYPE_PNG)

    def _ClearCache(self):
        for key in self.imageCache:
            del self.imageCache[key]

    #Threads
    def __Upload(self, postdata, filename, type="Background"):
        self.lock.acquire()

        url = self.settings.get_setting('ImageServerBaseURL')
        file = urllib.urlopen(url, postdata)
        recvdata = file.read()
        file.close()
        try:
            xml_dom = minidom.parseString(recvdata)._get_documentElement()

            if xml_dom.nodeName == 'path':
                path = xml_dom.getAttribute('url')
                path = urllib.unquote(path)

                if type == 'Background':
                    self.bgImage = self._LoadImage(path)
                    self.bgPath = path

                else:
                    self.minis.append(self.mapLayer.AddMiniture(path))

                self.UpdateMap()

            else:
                self.chat.InfoPost(xml_dom.getAttribute('msg'))
        except Exception, e:
            print e
            print recvdata

        self.lock.release()

    def __DownloadImage(self, path, miniId):
        self.lock.acquire()

        uriPath = urllib.unquote(path)
        try:
            data = urllib.urlretrieve(uriPath)

            if data[0] and data[1].getmaintype() == "image":
                imageType = data[1].gettype()
                img = wx.ImageFromMime(data[0], imageType).ConvertToBitmap()
                self.imageCache[path] = img

                if miniId == None:
                    self.bgImage = img
                    if self.bgType == 'Image':
                        self._SetSize((img.GetHeight(), img.GetWidth()))

                else:
                    mini = self.GetMiniById(miniId)
                    mini.image = img

                self.UpdateMap()
        except Exception, e:
            self.chat.InfoPost("Unable to resolve/open the specified URI; image was NOT laoded:" + path)

        urllib.urlcleanup()
        self.lock.release()