# Copyright (C) 2000-2001 The OpenRPG Project
#
#    openrpg-dev@lists.sourceforge.net
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
# File: mapper/map.py
# Author: OpenRPG
# Maintainer:
# Version:
#   $Id: map.py,v Traipse 'Ornery-Orc' prof.ebral Exp $
#
# Description:
#
__version__ = "$Id: map.py,v Traipse 'Ornery-Orc' prof.ebral Exp $"

from map_version import MAP_VERSION
from map_msg import *
from min_dialogs import *
from map_prop_dialog import *

import random, os, thread, traceback

from miniatures_handler import *
from whiteboard_handler import *
from background_handler import *
from grid_handler import *
from map_handler import *
from fog_handler import *

from orpg.dirpath import dir_struct
from images import ImageHandler
from orpg.orpgCore import component
from orpg.tools.orpg_settings import settings
from xml.etree.ElementTree import ElementTree, Element, parse
from xml.etree.ElementTree import fromstring, tostring

# Various marker modes for player tools on the map
MARKER_MODE_NONE = 0
MARKER_MODE_MEASURE = 1
MARKER_MODE_TARGET = 2
MARKER_MODE_AREA_TARGET = 3

class MapCanvas(wx.ScrolledWindow):
    def __init__(self, parent, ID, isEditor=0):
        self.parent = parent
        self.session = component.get("session")
        wx.ScrolledWindow.__init__(self, parent, ID, 
            style=wx.HSCROLL | wx.VSCROLL | wx.FULL_REPAINT_ON_RESIZE | wx.SUNKEN_BORDER )
        self.frame = parent
        self.MAP_MODE = 1      #Mode 1 = MINI, 2 = DRAW, 3 = TAPE MEASURE
        self.layers = {}
        self.layers['bg'] = layer_back_ground(self)
        self.layers['grid'] = grid_layer(self)
        self.layers['whiteboard'] = whiteboard_layer(self)
        self.layers['miniatures'] = miniature_layer(self)
        self.layers['fog'] = fog_layer(self)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.on_erase_background)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_RIGHT_DOWN, self.on_right_down)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_SCROLLWIN, self.on_scroll)
        self.Bind(wx.EVT_CHAR, self.on_char)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.set_size((1000,1000))
        self.root_dir = os.getcwd()
        self.size_change = 0
        self.isEditor = isEditor
        self.map_version = MAP_VERSION
        self.cacheSize = 32
        # Create the marker mode attributes for the map
        self.markerMode = MARKER_MODE_NONE
        self.markerStart = wx.Point( -1, -1 )
        self.markerStop = wx.Point( -1, -1 )
        self.markerMidpoint = wx.Point( -1, -1 )
        self.markerAngle = 0.0
        # Optimization of map refreshing during busy map load
        self.lastRefreshValue = 0
        self.requireRefresh = 0
        self.lastRefreshTime = 0
        self.zoom_display_timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self.better_refresh, self.zoom_display_timer)
        random.seed( time.time() )
        self.image_timer = wx.Timer(self, wx.NewId())
        self.Bind(wx.EVT_TIMER, self.processImages, self.image_timer)
        self.image_timer.Start(100)
        # Used to check if we've used the user cache size value
        self.cacheSizeSet = False
        self.inside = 0
        # miniatures drag
        self.drag = None

    def better_refresh(self, event=None):
        self.Refresh(True)

    def pre_destory_cleanup(self):
        self.layers["miniatures"].del_all_miniatures()

    def processImages(self, evt=None):
        self.session = component.get("session")
        if self.session.my_role() == self.session.ROLE_LURKER or (str(self.session.group_id) == '0' and str(self.session.status) == '1'):
            cidx = self.parent.get_tab_index("Background")
            self.parent.layer_tabs.EnableTab(cidx, False)
            cidx = self.parent.get_tab_index("Grid")
            self.parent.layer_tabs.EnableTab(cidx, False)
            cidx = self.parent.get_tab_index("Miniatures")
            self.parent.layer_tabs.EnableTab(cidx, False)
            cidx = self.parent.get_tab_index("Whiteboard")
            self.parent.layer_tabs.EnableTab(cidx, False)
            cidx = self.parent.get_tab_index("Fog")
            self.parent.layer_tabs.EnableTab(cidx, False)
            cidx = self.parent.get_tab_index("General")
            self.parent.layer_tabs.EnableTab(cidx, False)
        else:
            cidx = self.parent.get_tab_index("Background")
            if not self.parent.layer_tabs.GetEnabled(cidx):
                cidx = self.parent.get_tab_index("Miniatures")
                self.parent.layer_tabs.EnableTab(cidx, True)
                cidx = self.parent.get_tab_index("Whiteboard")
                self.parent.layer_tabs.EnableTab(cidx, True)
                cidx = self.parent.get_tab_index("Background")
                self.parent.layer_tabs.EnableTab(cidx, False)
                cidx = self.parent.get_tab_index("Grid")
                self.parent.layer_tabs.EnableTab(cidx, False)
                cidx = self.parent.get_tab_index("Fog")
                self.parent.layer_tabs.EnableTab(cidx, False)
                cidx = self.parent.get_tab_index("General")
                self.parent.layer_tabs.EnableTab(cidx, False)
                if self.session.my_role() == self.session.ROLE_GM:
                    cidx = self.parent.get_tab_index("Background")
                    self.parent.layer_tabs.EnableTab(cidx, True)
                    cidx = self.parent.get_tab_index("Grid")
                    self.parent.layer_tabs.EnableTab(cidx, True)
                    cidx = self.parent.get_tab_index("Fog")
                    self.parent.layer_tabs.EnableTab(cidx, True)
                    cidx = self.parent.get_tab_index("General")
                    self.parent.layer_tabs.EnableTab(cidx, True)
        if not self.cacheSizeSet:
            self.cacheSizeSet = True
            cacheSize = component.get('settings').get_setting("ImageCacheSize")
            if len(cacheSize): self.cacheSize = int(cacheSize)
            else: pass
        if not ImageHandler.Queue.empty():
            (path, image_type, imageId) = ImageHandler.Queue.get()
            if (path == 'failed' or path == dir_struct["icon"] + "failed.png"): 
                img = wx.Image(dir_struct["icon"] + "failed.png", wx.BITMAP_TYPE_PNG)
            else: img = wx.ImageFromMime(path[1], path[2])
            try:
                # Now, apply the image to the proper object
                if image_type == "miniature":
                    min = self.layers['miniatures'].get_miniature_by_id(imageId)
                    if min: min.set_bmp(img)
                elif image_type == "background" or image_type == "texture":
                    self.layers['bg'].bg_bmp = img.ConvertToBitmap()
                    if image_type == "background": self.set_size([img.GetWidth(), img.GetHeight()])
            except: pass
            # Flag that we now need to refresh!
            self.requireRefresh += 1

            """ Randomly purge an item from the cache, while this is lamo, it does
                keep the cache from growing without bounds, which is pretty important!"""
            if len(ImageHandler.Cache) >= self.cacheSize:
                ImageHandler.cleanCache()
        else:
            """ Now, make sure not only that we require a refresh, but that enough time has
                gone by since our last refresh.  This keeps back to back refreshing occuring during
                large map loads.  Of course, we are now trying to pack as many image refreshes as
                we can into a single cycle."""
            if self.requireRefresh and (self.requireRefresh == self.lastRefreshValue):
                if (self.lastRefreshTime) < time.time():
                    self.requireRefresh = 0
                    self.lastRefreshValue = 0
                    self.lastRefreshTime = time.time()
                    self.Refresh(True)
            else: self.lastRefreshValue = self.requireRefresh

    def on_scroll(self, evt):
        if self.drag: self.drag.Hide()
        if component.get('settings').get_setting("AlwaysShowMapScale") == "1": self.printscale()
        evt.Skip()

    def on_char(self, evt):
        if component.get('settings').get_setting("AlwaysShowMapScale") == "1": self.printscale()
        evt.Skip()

    def printscale(self):
        wx.BeginBusyCursor()
        dc = wx.ClientDC(self)
        self.PrepareDC(dc)
        self.showmapscale(dc)
        self.Refresh(True)
        wx.EndBusyCursor()

    def send_map_data(self, action="update"):
        wx.BeginBusyCursor()
        send_text = self.toxml(action)
        if send_text:
            if not self.isEditor: self.frame.session.send(send_text)
        wx.EndBusyCursor()

    def get_size(self):
        return self.size

    def set_size(self, size):
        if size[0] < 300: size = (300, size[1])
        if size[1] < 300: size = (size[0], 300)
        self.size_changed = 1
        self.size = size
        self.fix_scroll()
        self.layers['fog'].resize(size)

    def fix_scroll(self):
        scale = self.layers['grid'].mapscale
        pos = self.GetViewStart()
        unit = self.GetScrollPixelsPerUnit()
        pos = [pos[0]*unit[0],pos[1]*unit[1]]
        size = self.GetClientSize()
        unit = [10*scale,10*scale]
        if (unit[0] == 0 or unit[1] == 0): return
        pos[0] /= unit[0]
        pos[1] /= unit[1]
        mx = [int(self.size[0]*scale/unit[0])+1, int(self.size[1]*scale/unit[1]+1)]
        self.SetScrollbars(unit[0], unit[1], mx[0], mx[1], pos[0], pos[1])

    def on_resize(self, evt):
        self.fix_scroll()
        wx.CallAfter(self.Refresh, True)
        evt.Skip()

    def on_erase_background(self, evt):
        evt.Skip()

    def on_paint(self, evt):
        scale = self.layers['grid'].mapscale
        scrollsize = self.GetScrollPixelsPerUnit()
        clientsize = self.GetClientSize()
        topleft1 = self.GetViewStart()
        topleft = [topleft1[0]*scrollsize[0], topleft1[1]*scrollsize[1]]
        if (clientsize[0] > 1) and (clientsize[1] > 1):
            dc = wx.MemoryDC()
            bmp = wx.EmptyBitmap(clientsize[0]+1, clientsize[1]+1)
            dc.SelectObject(bmp)
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(wx.Brush(self.GetBackgroundColour(), wx.SOLID))
            dc.DrawRectangle(0,0,clientsize[0]+1,clientsize[1]+1)
            dc.SetDeviceOrigin(-topleft[0], -topleft[1])
            dc.SetUserScale(scale, scale)

            layer_order = []
            for i in xrange (0, len(self.parent.layer_handlers)-1):
                if self.parent.layer_tabs.GetPageText(i) in ('Background', 'Fog', 'General'): pass
                else: layer_order.append(self.parent.layer_tabs.GetPageText(i))
            self.layers['bg'].layerDraw(dc, scale, topleft, clientsize)

            for layer in layer_order:
                if layer == 'Grid': self.layers['grid'].layerDraw(dc, [topleft[0]/scale, topleft[1]/scale], 
                    [clientsize[0]/scale, clientsize[1]/scale])
                if layer == 'Miniatures': self.layers['miniatures'].layerDraw(dc, [topleft[0]/scale, topleft[1]/scale], 
                    [clientsize[0]/scale, clientsize[1]/scale])
                if layer == 'Whiteboard': self.layers['whiteboard'].layerDraw(dc)

            self.layers['fog'].layerDraw(dc, topleft, clientsize)
            dc.SetPen(wx.NullPen)
            dc.SetBrush(wx.NullBrush)
            dc.SelectObject(wx.NullBitmap); del dc
            wdc = self.preppaint()
            wdc.DrawBitmap(bmp, topleft[0], topleft[1])
            if settings.get_setting("AlwaysShowMapScale") == "1":
                self.showmapscale(wdc)
        try: evt.Skip()
        except: pass

    def preppaint(self):
        dc = wx.PaintDC(self)
        self.PrepareDC(dc)
        return (dc)

    def showmapscale(self, dc):
        scalestring = "Scale x" + `self.layers['grid'].mapscale`[:3]
        (textWidth, textHeight) = dc.GetTextExtent(scalestring)
        dc.SetUserScale(1, 1)
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.SetBrush(wx.LIGHT_GREY_BRUSH)
        x = dc.DeviceToLogicalX(0)
        y = dc.DeviceToLogicalY(0)
        dc.DrawRectangle(x, y, textWidth+2, textHeight+2)
        dc.SetPen(wx.RED_PEN)
        dc.DrawText(scalestring, x+1, y+1)
        dc.SetPen(wx.NullPen)
        dc.SetBrush(wx.NullBrush)

    def snapMarker(self, snapPoint):
        """Based on the position and unit size, figure out where we need to snap to.  As is, on
        a square grid, there are four possible places to snap.  On a hex gid, there are 6 or 12 snap
        points."""

        # If snap to grid is disabled, simply return snapPoint unmodified
        if self.layers['grid'].snap:
            # This means we need to determine where to snap our line.  We will support
            # snapping to four different snapPoints per square for now.
            # TODO!!!
            if self.layers['grid'].mode == GRID_HEXAGON: size = self.layers['grid'].unit_size_y
            else:
                size = int(self.layers['grid'].unit_size)
                # Find the uppper left hand corner of the grid we are to snap to
                offsetX = (snapPoint.x / size) * size
                offsetY = (snapPoint.y / size) * size
                # Calculate the delta value between where we clicked and the square it is near
                deltaX = snapPoint.x - offsetX
                deltaY = snapPoint.y - offsetY
                # Now, figure our what quadrant (x, y) we need to snap to
                snapSize = size / 2
                # Figure out the X snap placement
                if deltaX <= snapSize: quadXPos = offsetX
                else: quadXPos = offsetX + size
                # Now, figure out the Y snap placement
                if deltaY <= snapSize: quadYPos = offsetY
                else: quadYPos = offsetY + size
                # Create our snap snapPoint and return it
                snapPoint = wx.Point( quadXPos, quadYPos )
        return snapPoint

    # Bunch of math stuff for marking and measuring
    def calcSlope(self, start, stop):
        """Calculates the slop of a line and returns it."""
        if start.x == stop.x: s = 0.0001
        else: s = float((stop.y - start.y)) / float((stop.x - start.x))
        return s

    def calcSlopeToAngle(self, slope):
        """Based on the input slope, the angle (in degrees) will be returned."""
        # See if the slope is neg or positive
        if slope == abs(slope):
            # Slope is positive, so make sure it's not zero
            if slope == 0: a = 0
            else: a = 360 - atan(slope) * (180.0/pi)
        else: a = atan(abs(slope)) * (180.0/pi)
        return a

    def calcLineAngle(self, start, stop):
        """Based on two points that are on a line, return the angle of that line."""
        a = self.calcSlopeToAngle( self.calcSlope( start, stop ) )
        return a

    def calcPixelDistance(self, start, stop):
        """Calculate the distance between two pixels and returns it.  The calculated
        distance is the Euclidean Distance, which is:
        d = sqrt( (x2 - x1)**2 + (y2 - y1)**2 )"""
        d = sqrt( abs((stop.x - start.x)**2 - (stop.y - start.y)**2) )
        return d

    def calcUnitDistance(self, start, stop, lineAngle):
        distance = self.calcPixelDistance( start, stop )
        ln = "%0.2f" % lineAngle
        if self.layers['grid'].mode == GRID_HEXAGON:
            if ln == "0.00" or ln == "359.99": ud = distance / self.layers['grid'].unit_size_y
            else: ud = (sqrt(abs((stop.x - start.x)**2 + (stop.y - start.y)**2))) / self.layers['grid'].unit_size_y
        else:
            if ln == "0.00" or ln == "359.99": ud = distance / self.layers['grid'].unit_size
            else: ud = (sqrt(abs((stop.x - start.x)**2 + (stop.y - start.y)**2))) / self.layers['grid'].unit_size
            #ud = sqrt( abs((stop.x - start.x)**2 - (stop.y - start.y)**2) )
        return ud

    def on_tape_motion(self, evt):
        """Track mouse motion so we can update the marker visual every time it's moved"""
        # Make sure we have a mode to do anything, otherwise, we ignore this
        if self.markerMode:
            # Grap the current DC for all of the marker modes
            dc = wx.ClientDC( self )
            self.PrepareDC( dc )
            dc.SetUserScale(self.layers['grid'].mapscale,self.layers['grid'].mapscale)
            # Grab the current map position
            pos = self.snapMarker( evt.GetLogicalPosition( dc ) )
            # Set up the pen used for drawing our marker
            dc.SetPen( wx.Pen(wx.RED, 1, wx.LONG_DASH) )
            # Now, based on the marker mode, draw the right thing
            if self.markerMode == MARKER_MODE_MEASURE:
                if self.markerStop.x != -1 and self.markerStop.y != -1:
                    # Set the DC function that we need
                    dc.SetLogicalFunction(wx.INVERT)
                    # Erase old and Draw new marker line
                    dc.BeginDrawing()
                    dc.DrawLine( self.markerStart.x, self.markerStart.y, self.markerStop.x, self.markerStop.y )
                    dc.DrawLine( self.markerStart.x, self.markerStart.y, pos.x, pos.y )
                    dc.EndDrawing()
                    # Restore the default DC function
                    dc.SetLogicalFunction(wx.COPY)
                # As long as we are in marker mode, we ned to update the stop point
                self.markerStop = pos
            dc.SetPen(wx.NullPen)
            del dc

    def on_tape_down(self, evt):
        """Greg's experimental tape measure code.  Hopefully, when this is done, it will all be
        modal based on a toolbar."""
        dc = wx.ClientDC( self )
        self.PrepareDC( dc )
        dc.SetUserScale(self.layers['grid'].mapscale,self.layers['grid'].mapscale)
        pos = evt.GetLogicalPosition( dc )
        # If grid snap is enabled, then snap the tool to a proper position
        pos = self.snapMarker( evt.GetLogicalPosition( dc ) )
        # Maker mode should really be set by a toolbar
        self.markerMode = MARKER_MODE_MEASURE
        # Erase the old line if her have one
        if self.markerStart.x != -1 and self.markerStart.y != -1:
            # Set up the pen used for drawing our marker
            dc.SetPen( wx.Pen(wx.RED, 1, wx.LONG_DASH) )
            # Set the DC function that we need
            dc.SetLogicalFunction(wx.INVERT)
            # Draw the marker line
            dc.BeginDrawing()
            dc.DrawLine( self.markerStart.x, self.markerStart.y, self.markerStop.x, self.markerStop.y )
            dc.EndDrawing()
            # Restore the default DC function and pen
            dc.SetLogicalFunction(wx.COPY)
            dc.SetPen(wx.NullPen)
        # Save our current start and reset the stop value
        self.markerStart = pos
        self.markerStop = pos
        del dc

    def on_tape_up(self, evt):
        """When we release the middle button, disable any marking updates that we have been doing."""
        # If we are in measure mode, draw the actual UNIT distance
        if self.markerMode == MARKER_MODE_MEASURE:
            dc = wx.ClientDC( self )
            self.PrepareDC( dc )
            dc.SetUserScale(self.layers['grid'].mapscale,self.layers['grid'].mapscale)
            # Draw the measured distance on the DC.  Since we want
            # the text to match the line angle, calculate the angle
            # of the line.
            lineAngle = self.calcLineAngle( self.markerStart, self.markerStop )
            distance = self.calcUnitDistance( self.markerStart, self.markerStop, lineAngle )
            midPoint = (self.markerStart + self.markerStop)
            midPoint.x /= 2
            midPoint.y /= 2
            # Adjust out font to be bigger & scaled
            font = dc.GetFont()
            # Set the DC function that we need
            dc.SetLogicalFunction(wx.INVERT)
            # Set the pen we want to use
            dc.SetPen(wx.BLACK_PEN)
            # Now, draw the text at the proper angle on the canvas
            self.markerMidpoint = midPoint
            self.markerAngle = lineAngle
            dText = "%0.2f Units" % (distance)
            dc.BeginDrawing()
            dc.DrawRotatedText( dText, midPoint.x, midPoint.y, lineAngle )
            dc.EndDrawing()
            # Restore the default font and DC
            dc.SetFont(wx.NullFont)
            dc.SetLogicalFunction(wx.COPY)
            del font
            del dc
        self.markerMode = MARKER_MODE_NONE

    # MODE 1 = MOVE, MODE 2 = whiteboard, MODE 3 = Tape measure
    def on_left_down(self, evt):
        if evt.ShiftDown(): self.on_tape_down (evt)
        else: self.frame.on_left_down(evt)

    def on_right_down(self, evt):
        if evt.ShiftDown(): pass
        else: self.frame.on_right_down(evt)

    def on_left_dclick(self, evt):
        if evt.ShiftDown(): pass
        else: self.frame.on_left_dclick(evt)

    def on_left_up(self, evt):
        if evt.ShiftDown(): self.on_tape_up(evt)
        elif component.get('tree_fs').dragging:
            tree = component.get('tree_fs')
            if tree.drag_obj.map_aware():
                tree.drag_obj.on_send_to_map(evt)
                tree.dragging = False
                tree.drag_obj = None
        else: self.frame.on_left_up(evt)

    def on_motion(self, evt):
        if evt.ShiftDown(): self.on_tape_motion(evt)
        elif evt.LeftIsDown() and component.get('tree_fs').dragging: pass
        else: self.frame.on_motion(evt)

    def on_zoom_out(self, evt):
        if self.layers['grid'].mapscale > 0.2:
            # attempt to keep same logical point at center of screen
            scale = self.layers['grid'].mapscale
            scrollsize = self.GetScrollPixelsPerUnit()
            clientsize = self.GetClientSize()
            topleft1 = self.GetViewStart()
            topleft = [topleft1[0]*scrollsize[0], topleft1[1]*scrollsize[1]]
            scroll_x = (((topleft[0]+clientsize[0]/2)*(scale-.1)/scale)-clientsize[0]/2)/scrollsize[0]
            scroll_y = (((topleft[1]+clientsize[1]/2)*(scale-.1)/scale)-clientsize[1]/2)/scrollsize[1]
            self.Scroll(scroll_x, scroll_y)
            self.layers['grid'].mapscale -= .1
            scalestring = "x" + `self.layers['grid'].mapscale`[:3]
            self.frame.get_current_layer_handler().zoom_out_button.SetToolTip(wx.ToolTip("Zoom out from " + scalestring) )
            self.frame.get_current_layer_handler().zoom_in_button.SetToolTip(wx.ToolTip("Zoom in from " + scalestring) )
            self.set_size(self.size)
            dc = wx.ClientDC(self)
            dc.BeginDrawing()
            scalestring = "Scale x" + `self.layers['grid'].mapscale`[:3]
            (textWidth,textHeight) = dc.GetTextExtent(scalestring)
            dc.SetPen(wx.LIGHT_GREY_PEN)
            dc.SetBrush(wx.LIGHT_GREY_BRUSH)
            dc.DrawRectangle(dc.DeviceToLogicalX(0),dc.DeviceToLogicalY(0),textWidth,textHeight)
            dc.SetPen(wx.RED_PEN)
            dc.DrawText(scalestring,dc.DeviceToLogicalX(0),dc.DeviceToLogicalY(0))
            dc.SetPen(wx.NullPen)
            dc.SetBrush(wx.NullBrush)
            dc.EndDrawing()
            del dc
            self.zoom_display_timer.Start(500,1)

    def on_zoom_in(self, evt):
        # attempt to keep same logical point at center of screen
        scale = self.layers['grid'].mapscale
        scrollsize = self.GetScrollPixelsPerUnit()
        clientsize = self.GetClientSize()
        topleft1 = self.GetViewStart()
        topleft = [topleft1[0]*scrollsize[0], topleft1[1]*scrollsize[1]]
        scroll_x = (((topleft[0]+clientsize[0]/2)*(scale+.1)/scale)-clientsize[0]/2)/scrollsize[0]
        scroll_y = (((topleft[1]+clientsize[1]/2)*(scale+.1)/scale)-clientsize[1]/2)/scrollsize[1]
        self.Scroll(scroll_x, scroll_y)
        self.layers['grid'].mapscale += .1
        scalestring = "x" + `self.layers['grid'].mapscale`[:3]
        self.frame.get_current_layer_handler().zoom_out_button.SetToolTip(wx.ToolTip("Zoom out from " + scalestring) )
        self.frame.get_current_layer_handler().zoom_in_button.SetToolTip(wx.ToolTip("Zoom in from " + scalestring) )
        self.set_size(self.size)
        dc = wx.ClientDC(self)
        dc.BeginDrawing()
        scalestring = "Scale x" + `self.layers['grid'].mapscale`[:3]
        (textWidth,textHeight) = dc.GetTextExtent(scalestring)
        dc.SetPen(wx.LIGHT_GREY_PEN)
        dc.SetBrush(wx.LIGHT_GREY_BRUSH)
        dc.DrawRectangle(dc.DeviceToLogicalX(0), dc.DeviceToLogicalY(0), textWidth,textHeight)
        dc.SetPen(wx.RED_PEN)
        dc.DrawText(scalestring, dc.DeviceToLogicalX(0), dc.DeviceToLogicalY(0))
        dc.SetPen(wx.NullPen)
        dc.SetBrush(wx.NullBrush)
        dc.EndDrawing()
        del dc
        self.zoom_display_timer.Start(500, 1)

    def on_prop(self, evt):
        self.session = component.get("session")
        self.chat = component.get("chat")
        if (self.session.my_role() != self.session.ROLE_GM):
            self.chat.InfoPost("You must be a GM to use this feature")
            return
        dlg = general_map_prop_dialog(self.frame.GetParent(),self.size,self.layers['bg'],self.layers['grid'])
        if dlg.ShowModal() == wx.ID_OK:
            self.set_size(dlg.size)
            self.send_map_data()
            self.Refresh(False)
        dlg.Destroy()
        os.chdir(self.root_dir)

    def add_miniature(self, min_url, min_label='', min_unique=-1):
        if min_unique == -1: min_unique = not self.use_serial
        if min_url == "" or min_url == "http://": return
        if min_url[:7] != "http://" : min_url = "http://" + min_url
        # make label
        wx.BeginBusyCursor()
        if self.auto_label:
            if min_label == '': min_label = self.get_label_from_url( min_url )
            if not min_unique and self.use_serial:
                min_label = '%s %d' % ( min_label, self.layers['miniatures'].next_serial() )
        else: min_label = ""
        if self.frame.min_url.FindString(min_url) == -1: self.frame.min_url.Append(min_url)
        try:
            id = 'mini-' + self.frame.session.get_next_id()
            self.layers['miniatures'].add_miniature(id, min_url, label=min_label)
        except:
            self.layers['miniatures'].rollback_serial()
        wx.EndBusyCursor()
        self.send_map_data()
        self.Refresh(False)

    def get_label_from_url(self, url=''):
        if url == '': return ''
        start = url.rfind("/")+1
        label = url[start:len(url)-4]
        return label

    def toxml(self, action="update"):
        if action == "new":
            self.size_changed = 1
        xml_str = "<map version='" + self.map_version + "'"
        changed = self.size_changed
        if self.size_changed:
            xml_str += " sizex='" + str(self.size[0]) + "'"
            xml_str += " sizey='" + str(self.size[1]) + "'"
        s = ""
        keys = self.layers.keys()
        for k in keys:
            if (k != "fog" or action != "update"): s += self.layers[k].layerToXML(action)
        self.size_changed = 0
        if s: return xml_str + " action='" + action + "'>" + s + "</map>"
        else:
            if changed: return xml_str + " action='" + action + "'/>"
            else: return ""

    def takexml(self, xml):
        """
          Added Process Dialog to display during long map parsings
          as well as a try block with an exception traceback to try
          and isolate some of the map related problems users have been
          experiencing --Snowdog 5/15/03
         
          Apparently Process Dialog causes problems with linux.. commenting it out. sheez.
           --Snowdog 5/27/03
        """
        try:
            xml_dom = fromstring(xml)
            if xml_dom == None: return
            node_list = xml_dom.findall("map")
            if len(node_list) < 1: 
                if xml_dom.tag == 'map': node_list = [xml_dom]
            if len(node_list) < 1: pass
            else:
                # set map version to incoming data so layers can convert
                self.map_version = node_list[0].get("version")
                action = node_list[0].get("action")
                if action == "new":
                    self.layers = {}
                    try: self.layers['bg'] = layer_back_ground(self)
                    except: pass
                    try: self.layers['grid'] = grid_layer(self)
                    except: pass
                    try: self.layers['miniatures'] = miniature_layer(self)
                    except: pass
                    try: self.layers['whiteboard'] = whiteboard_layer(self)
                    except: pass
                    try: self.layers['fog'] = fog_layer(self)
                    except: pass
                sizex = node_list[0].get("sizex") or ''
                if sizex != "":
                    sizex = int(float(sizex))
                    sizey = self.size[1]
                    self.set_size((sizex,sizey))
                    self.size_changed = 0
                sizey = node_list[0].get("sizey") or ''
                if sizey != "":
                    sizey = int(float(sizey))
                    sizex = self.size[0]
                    self.set_size((sizex,sizey))
                    self.size_changed = 0
                children = node_list[0].getchildren()
                #fog layer must be computed first, so that no data is inadvertently revealed
                for c in children:
                    name = c.tag
                    if name == "fog": self.layers[name].layerTakeDOM(c)
                for c in children:
                    name = c.tag
                    if name != "fog": self.layers[name].layerTakeDOM(c)
                # all map data should be converted, set map version to current version
                self.map_version = MAP_VERSION
                self.Refresh(True)
        except: pass

    def re_ids_in_xml(self, xml):
        exception = "\nDeprecated call to: Function re_ids_in_xml, line 679, map.py\nThis can mangle XML, please report!"
        logger.exception(exception)
        new_xml = ""
        tmp_map = map_msg()
        xml_dom = fromstring(xml)
        node_list = xml_dom.findall("map")
        if len(node_list) < 1: pass
        else:
            tmp_map.init_from_dom(node_list[0])
            if tmp_map.children.has_key("miniatures"):
                miniatures_layer = tmp_map.children["miniatures"]
                if miniatures_layer:
                    minis = miniatures_layer.get_children().keys()
                    if minis:
                        for mini in minis:
                            m = miniatures_layer.children[mini]
                            id = 'mini-' + self.frame.session.get_next_id()
                            m.init_prop("id", id)
            # This allows for backward compatibility with older maps which do not
            # have a whiteboard node.  As such, if it's not there, we'll just happily
            # move on and process as always.
            if tmp_map.children.has_key("whiteboard"):
                whiteboard_layer = tmp_map.children["whiteboard"]
                if whiteboard_layer:
                    lines = whiteboard_layer.get_children().keys()
                    if lines:
                        for line in lines:
                            l = whiteboard_layer.children[line]
                            if l.tagname == 'line': id = 'line-' + self.frame.session.get_next_id()
                            elif l.tagname == 'text': id = 'text-' + self.frame.session.get_next_id()
                            elif l.tagname == 'circle': id = 'circle-' + self.frame.session.get_next_id()
                            l.init_prop("id", id)
            new_xml = tmp_map.get_all_xml()
        return new_xml

class map_wnd(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id)
        self.canvas = MapCanvas(self, -1)
        self.session = component.get('session')
        self.top_frame = component.get('frame')
        self.chat = self.top_frame.chat
        self.root_dir = os.getcwd()
        self.current_layer = 2
        self.layer_tabs = orpgTabberWnd(self, style=FNB.FNB_NO_X_BUTTON|FNB.FNB_BOTTOM|FNB.FNB_NO_NAV_BUTTONS)

        self.layer_handlers = []
        self.layer_handlers.append(background_handler(self.layer_tabs, -1, self.canvas))
        self.layer_tabs.AddPage(self.layer_handlers[0], "Background")
        self.layer_handlers.append(grid_handler(self.layer_tabs, -1, self.canvas))
        self.layer_tabs.AddPage(self.layer_handlers[1], "Grid")
        self.layer_handlers.append(miniatures_handler(self.layer_tabs, -1, self.canvas))
        self.layer_tabs.AddPage(self.layer_handlers[2], "Miniatures", True)
        self.layer_handlers.append(whiteboard_handler(self.layer_tabs, -1, self.canvas))
        self.layer_tabs.AddPage(self.layer_handlers[3], "Whiteboard")
        self.layer_handlers.append(fog_handler(self.layer_tabs, -1, self.canvas))
        self.layer_tabs.AddPage(self.layer_handlers[4], "Fog")
        self.layer_handlers.append(map_handler(self.layer_tabs, -1, self.canvas))
        self.layer_tabs.AddPage(self.layer_handlers[5], "General")
        self.layer_tabs.SetSelection(2)

        self.layer_order = {1: 'grid', 2: 'miniatures', 3: 'whiteboard'}
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.EXPAND)
        self.sizer.Add(self.layer_tabs, 0, wx.EXPAND)
        self.SetSizer(self.sizer)
        self.Bind(FNB.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.on_layer_change)
        #self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnLeave)
        self.load_default()

    def OnLeave(self, evt):
        if "__WXGTK__" in wx.PlatformInfo: wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    def load_default(self):
        if self.session.is_connected() and (self.session.my_role() != self.session.ROLE_GM) and (self.session.use_roles()):
            self.chat.InfoPost("You must be a GM to use this feature")
            return
        f = open(dir_struct["template"] + "default_map.xml")
        self.new_data(f.read())
        f.close()
        self.canvas.send_map_data("new")
        if not self.session.is_connected() and (self.session.my_role() != self.session.ROLE_GM):
            self.session.update_role("GM")

    def new_data(self, data):
        self.canvas.takexml(data)
        self.update_tools()

    def on_save(self,evt):
        if (self.session.my_role() != self.session.ROLE_GM):
            self.chat.InfoPost("You must be a GM to use this feature")
            return
        d = wx.FileDialog(self.GetParent(), "Save map data", dir_struct["user"], "", "*.xml", wx.SAVE)
        if d.ShowModal() == wx.ID_OK:
            f = open(d.GetPath(), "w")
            data = '<nodehandler class="min_map" icon="compass" module="core" name="miniature Map">'
            data += self.canvas.toxml("new")
            data += "</nodehandler>"
            data = data.replace(">",">\n")
            f.write(data)
            f.close()
        d.Destroy()
        os.chdir(self.root_dir)

    def on_open(self, evt):
        if self.session.is_connected() and (self.session.my_role() != self.session.ROLE_GM) and (self.session.use_roles()):
            self.chat.InfoPost("You must be a GM to use this feature")
            return
        d = wx.FileDialog(self.GetParent(), "Select a file", dir_struct["user"], "", "*.xml", wx.OPEN)
        if d.ShowModal() == wx.ID_OK:
            f = open(d.GetPath())
            new_xml = f.read()
            f.close()
            if new_xml != None:
                self.canvas.takexml(new_xml)
                self.canvas.send_map_data("new")
                self.update_tools()
                if not self.session.is_connected() and (self.session.my_role() != self.session.ROLE_GM):
                    self.session.update_role("GM")
        d.Destroy()
        os.chdir(self.root_dir)

    def get_current_layer_handler(self):
        return self.layer_handlers[self.current_layer]

    def get_tab_index(self, layer):
        """Return the index of a chatpanel in the wxNotebook."""
        for i in xrange(self.layer_tabs.GetPageCount()):
            if (self.layer_tabs.GetPageText(i) == layer):
                return i
        return 0

    def on_layer_change(self, evt):
        layer = self.layer_tabs.GetPage(evt.GetSelection())
        for i in xrange(0, len(self.layer_handlers)):
            if layer == self.layer_handlers[i]: self.current_layer = i
        if self.current_layer == 0:
            bg = self.layer_handlers[0]
            if (self.session.my_role() != self.session.ROLE_GM): bg.url_path.Show(False)
            else: bg.url_path.Show(True)
        self.canvas.Refresh(False)
        evt.Skip()

    def on_left_down(self, evt):
        self.layer_handlers[self.current_layer].on_left_down(evt)

    def on_left_dclick(self, evt):
        self.layer_handlers[self.current_layer].on_left_dclick(evt)

    def on_right_down(self, evt):
        self.layer_handlers[self.current_layer].on_right_down(evt)

    def on_left_up(self, evt):
        self.layer_handlers[self.current_layer].on_left_up(evt)

    def on_motion(self, evt):
        self.layer_handlers[self.current_layer].on_motion(evt)

    def MapBar(self, id, data):
        self.canvas.MAP_MODE = data
        if id == 1: self.canvas.MAP_MODE = data

    def set_map_focus(self, evt):
        self.canvas.SetFocus()

    def pre_exit_cleanup(self):
        # do some pre exit clean up for bitmaps or other objects
        try:
            ImageHandler.flushCache()
            self.canvas.pre_destory_cleanup()
        except: pass

    def update_tools(self):
        for h in self.layer_handlers:
            h.update_info()

    def on_hk_map_layer(self, evt):
        id = self.top_frame.mainmenu.GetHelpString(evt.GetId())
        if id == "Background Layer": self.current_layer = self.get_tab_index("Background")
        if id == "Grid Layer": self.current_layer = self.get_tab_index("Grid")
        if id == "Miniature Layer": self.current_layer = self.get_tab_index("Miniatures")
        elif id == "Whiteboard Layer": self.current_layer = self.get_tab_index("Whiteboard")
        elif id == "Fog Layer": self.current_layer = self.get_tab_index("Fog")
        elif id == "General Properties": self.current_layer = self.get_tab_index("General")
        self.layer_tabs.SetSelection(self.current_layer)

    def on_flush_cache(self, evt):
        ImageHandler.flushCache()

    def build_menu(self):
        # temp menu
        menu = wx.Menu()
        item = wx.MenuItem(menu, wx.ID_ANY, "&Load Map", "Load Map")
        self.top_frame.Bind(wx.EVT_MENU, self.on_open, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, wx.ID_ANY, "&Save Map", "Save Map")
        self.top_frame.Bind(wx.EVT_MENU, self.on_save, item)
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, wx.ID_ANY, "Background Layer\tCtrl+1", "Background Layer")
        self.top_frame.Bind(wx.EVT_MENU, self.on_hk_map_layer, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, wx.ID_ANY, "Grid Layer\tCtrl+2", "Grid Layer")
        self.top_frame.Bind(wx.EVT_MENU, self.on_hk_map_layer, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, wx.ID_ANY, "Miniature Layer\tCtrl+3", "Miniature Layer")
        self.top_frame.Bind(wx.EVT_MENU, self.on_hk_map_layer, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, wx.ID_ANY, "Whiteboard Layer\tCtrl+4", "Whiteboard Layer")
        self.top_frame.Bind(wx.EVT_MENU, self.on_hk_map_layer, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, wx.ID_ANY, "Fog Layer\tCtrl+5", "Fog Layer")
        self.top_frame.Bind(wx.EVT_MENU, self.on_hk_map_layer, item)
        menu.AppendItem(item)
        item = wx.MenuItem(menu, wx.ID_ANY, "General Properties\tCtrl+6", "General Properties")
        self.top_frame.Bind(wx.EVT_MENU, self.on_hk_map_layer, item)
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, wx.ID_ANY, "&Flush Image Cache\tCtrl+F", "Flush Image Cache")
        self.top_frame.Bind(wx.EVT_MENU, self.on_flush_cache, item)
        menu.AppendItem(item)
        menu.AppendSeparator()
        item = wx.MenuItem(menu, wx.ID_ANY, "&Properties", "Properties")
        self.top_frame.Bind(wx.EVT_MENU, self.canvas.on_prop, item)
        menu.AppendItem(item)
        self.top_frame.mainmenu.Insert(2, menu, '&Map')

    def get_hot_keys(self):
        self.build_menu()
        return []
