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
# File: mapper/miniatures.py
# Author: Chris Davis
# Maintainer:
# Version:
#   $Id: miniatures.py,v Traipse 'Ornery-Orc' prof.ebral Exp $
#
# Description: This file contains some of the basic definitions for the chat
# utilities in the orpg project.
#
__version__ = "$Id: miniatures.py,v Traipse 'Ornery-Orc' prof.ebral Exp $"

from base import *
import thread, time, urllib, os.path, mimetypes

import xml.dom.minidom as minidom
from orpg.tools.orpg_settings import settings

from xml.etree.ElementTree import ElementTree, Element
from xml.etree.ElementTree import fromstring, tostring

MIN_STICKY_BACK = -0XFFFFFF
MIN_STICKY_FRONT = 0xFFFFFF

##----------------------------------------
##  miniature object
##----------------------------------------

FACE_NONE = 0
FACE_NORTH = 1
FACE_NORTHEAST = 2
FACE_EAST = 3
FACE_SOUTHEAST = 4
FACE_SOUTH = 5
FACE_SOUTHWEST = 6
FACE_WEST = 7
FACE_NORTHWEST = 8
SNAPTO_ALIGN_CENTER = 0
SNAPTO_ALIGN_TL = 1

def cmp_zorder(first,second):
    f = first.zorder
    s = second.zorder
    if f == None: f = 0
    if s == None: s = 0
    if f == s: value = 0
    elif f < s: value = -1
    else: value = 1
    return value

class BmpMiniature:
    def __init__(self, id, path, bmp, pos=cmpPoint(0,0), 
                heading=FACE_NONE, face=FACE_NONE, label="", 
                locked=False, hide=False, snap_to_align=SNAPTO_ALIGN_CENTER, 
                zorder=0, width=0, height=0, log=None, local=False, localPath='', localTime=-1, func='none'):
        self.heading = heading
        self.face = face
        self.label = label
        self.path = path
        self.pos = pos
        self.selected = False
        self.locked = locked
        self.snap_to_align = snap_to_align
        self.hide = hide
        self.id = id
        self.zorder = zorder
        self.left = 0
        self.local = local
        self.localPath = localPath
        self.localTime = localTime
        if not width: self.width = 0
        else: self.width = width
        if not height: self.height = 0
        else: self.height = height
        self.right = bmp.GetWidth()
        self.top = 0
        self.bottom = bmp.GetHeight()
        self.isUpdated = False
        self.gray = False
        self.set_bmp(bmp)

    def __del__(self):
        del self.image
        self.image = None

    def set_bmp(self, bmp):
        self.image = bmp
        self.image.ConvertAlphaToMask()
        self.generate_bmps()
        
    def generate_bmps(self):
        if self.width:
            bmp = self.image.Copy()
            bmp.Rescale(int(self.width), int(self.height))
        else:
            bmp = self.image
        self.bmp = bmp.ConvertToBitmap()
        self.bmp_gray = bmp.ConvertToGreyscale().ConvertToBitmap()

    def set_min_props(self, heading=FACE_NONE, face=FACE_NONE, label="", locked=False, hide=False, width=0, height=0):
        self.heading = heading
        self.face = face
        self.label = label
        if locked: self.locked = True
        else: self.locked = False
        if hide: self.hide = True
        else: self.hide = False
        self.width = int(width)
        self.height = int(height)
        self.isUpdated = True
        self.generate_bmps()

    def hit_test(self, pt):
        rect = self.get_rect()
        result = None
        result = rect.InsideXY(pt.x, pt.y)
        return result

    def get_rect(self):
        ret = wx.Rect(self.pos.x, self.pos.y, self.bmp.GetWidth(), self.bmp.GetHeight())
        return ret

    def draw(self, dc, mini_layer, op=wx.COPY):
        if self.hide and mini_layer.canvas.frame.session.my_role() == mini_layer.canvas.frame.session.ROLE_GM:
            # set the width and height of the image
            self.left = 0
            self.right = self.bmp.GetWidth()
            self.top = 0
            self.bottom = self.bmp.GetHeight()
            # grey outline
            graypen = wx.Pen("gray", 1, wx.DOT)
            dc.SetPen(graypen)
            dc.SetBrush(wx.TRANSPARENT_BRUSH)
            #if width or height < 20 then offset = 1
            if self.bmp.GetWidth() <= 20: xoffset = 1
            else: xoffset = 5
            if self.bmp.GetHeight() <= 20: yoffset = 1
            else: yoffset = 5
            dc.DrawRectangle(self.pos.x + xoffset, 
                self.pos.y + yoffset, self.bmp.GetWidth(), 
                self.bmp.GetHeight())
            dc.SetBrush(wx.NullBrush)
            dc.SetPen(wx.NullPen)
            if mini_layer.show_labels:
                ## draw label in the center of the mini
                label = mini_layer.get_mini_label(self)
                if len(label):
                    dc.SetTextForeground(wx.RED)
                    (textWidth,textHeight) = dc.GetTextExtent(label)
                    x = self.pos.x +((self.bmp.GetWidth() - textWidth) /2) - 1
                    y = self.pos.y + (self.bmp.GetHeight() / 2)
                    dc.SetPen(wx.GREY_PEN)
                    dc.SetBrush(wx.LIGHT_GREY_BRUSH)
                    dc.DrawRectangle(x, y, textWidth+2, textHeight+2)
                    if (textWidth+2 > self.right):
                        self.right += int((textWidth+2-self.right)/2)+1
                        self.left -= int((textWidth+2-self.right)/2)+1
                    self.bottom = y+textHeight+2-self.pos.y
                    dc.SetPen(wx.NullPen)
                    dc.SetBrush(wx.NullBrush)
                    dc.DrawText(label, x+1, y+1)
        
            #selected outline
            if self.selected:
                dc.SetPen(wx.RED_PEN)
                dc.SetBrush(wx.TRANSPARENT_BRUSH)
                dc.DrawRectangle(self.pos.x, self.pos.y, self.bmp.GetWidth(), self.bmp.GetHeight())
                dc.SetBrush(wx.NullBrush)
                dc.SetPen(wx.NullPen)
            return True
        elif self.hide: return True
        
        else:
            bmp = self.bmp_gray if self.gray else self.bmp
            try: dc.DrawBitmap(bmp, self.pos.x, self.pos.y, True)
            except: print bmp
            self.left = 0
            self.right = self.bmp.GetWidth()
            self.top = 0
            self.bottom = self.bmp.GetHeight()
            # Draw the facing marker if needed
            if self.face != 0:
                x_mid = self.pos.x + (self.bmp.GetWidth()/2)
                x_right = self.pos.x + self.bmp.GetWidth()
                y_mid = self.pos.y + (self.bmp.GetHeight()/2)
                y_bottom = self.pos.y + self.bmp.GetHeight()
                dc.SetPen(wx.WHITE_PEN)
                dc.SetBrush(wx.RED_BRUSH)
                triangle = []
                # Figure out which direction to draw the marker!!
                tri_list = {
                FACE_WEST: [cmpPoint(self.pos.x, self.pos.y), cmpPoint(self.pos.x-5, y_mid), cmpPoint(self.pos.x, y_bottom)], 
                FACE_EAST: [cmpPoint(x_right, self.pos.y), cmpPoint(x_right + 5, y_mid), cmpPoint(x_right, y_bottom)], 
                FACE_SOUTH: [cmpPoint(self.pos.x, y_bottom), cmpPoint(x_mid, y_bottom + 5), cmpPoint(x_right, y_bottom)],
                FACE_NORTH: [cmpPoint(self.pos.x, self.pos.y), cmpPoint(x_mid, self.pos.y - 5), cmpPoint(x_right, self.pos.y)],
                FACE_NORTHEAST: [cmpPoint(x_mid, self.pos.y), cmpPoint(x_right + 5, self.pos.y - 5), cmpPoint(x_right, y_mid), cmpPoint(x_right, self.pos.y)],
                FACE_SOUTHEAST: [cmpPoint(x_right, y_mid), cmpPoint(x_right + 5, y_bottom + 5), cmpPoint(x_mid, y_bottom), cmpPoint(x_right, y_bottom)],
                FACE_SOUTHWEST: [cmpPoint(x_mid, y_bottom), cmpPoint(self.pos.x - 5, y_bottom + 5),
                cmpPoint(self.pos.x, y_mid), cmpPoint(self.pos.x, y_bottom)],
                FACE_NORTHWEST: [cmpPoint(self.pos.x, y_mid), cmpPoint(self.pos.x - 5, self.pos.y - 5), cmpPoint(x_mid, self.pos.y), cmpPoint(self.pos.x, self.pos.y)]
                }
                for tri in tri_list[self.face]:
                    triangle.append(tri)
                del tri_list
                dc.DrawPolygon(triangle)
                dc.SetBrush(wx.NullBrush)
                dc.SetPen(wx.NullPen)
            # Draw the heading if needed
            if self.heading:
                x_adjust = 0
                y_adjust = 4
                x_half = self.bmp.GetWidth()/2
                y_half = self.bmp.GetHeight()/2
                x_quarter = self.bmp.GetWidth()/4
                y_quarter = self.bmp.GetHeight()/4
                x_3quarter = x_quarter*3
                y_3quarter = y_quarter*3
                x_full = self.bmp.GetWidth()
                y_full = self.bmp.GetHeight()
                x_center = self.pos.x + x_half
                y_center = self.pos.y + y_half
                # Remember, the pen/brush must be a different color than the
                # facing marker!!!!  We'll use black/cyan for starters.
                # Also notice that we will draw the heading on top of the
                # larger facing marker.
                dc.SetPen(wx.BLACK_PEN)
                dc.SetBrush(wx.CYAN_BRUSH)
                triangle = []
                # Figure out which direction to draw the marker!!
                tri_list = {
                FACE_NORTH: [cmpPoint(x_center - x_quarter, y_center - y_half ), 
                            cmpPoint(x_center, y_center - y_3quarter ), 
                            cmpPoint(x_center + x_quarter, y_center - y_half)],
                FACE_SOUTH: [cmpPoint(x_center - x_quarter, y_center + y_half ), 
                            cmpPoint(x_center, y_center + y_3quarter ), 
                            cmpPoint(x_center + x_quarter, y_center + y_half )],
                FACE_NORTHEAST: [cmpPoint(x_center + x_quarter, y_center - y_half ), 
                                cmpPoint(x_center + x_3quarter, y_center - y_3quarter ), 
                                cmpPoint(x_center + x_half, y_center - y_quarter)],
                FACE_EAST: [cmpPoint(x_center + x_half, y_center - y_quarter ), 
                            cmpPoint(x_center + x_3quarter, y_center ), 
                            cmpPoint(x_center + x_half, y_center + y_quarter )],
                FACE_SOUTHEAST: [cmpPoint(x_center + x_half, y_center + y_quarter ), 
                                cmpPoint(x_center + x_3quarter, y_center + y_3quarter ), 
                                cmpPoint(x_center + x_quarter, y_center + y_half )],
                FACE_SOUTHWEST: [cmpPoint(x_center - x_quarter, y_center + y_half ), 
                                cmpPoint(x_center - x_3quarter, y_center + y_3quarter ), 
                                cmpPoint(x_center - x_half, y_center + y_quarter )],
                FACE_WEST: [cmpPoint(x_center - x_half, y_center + y_quarter ), 
                            cmpPoint(x_center - x_3quarter, y_center ), 
                            cmpPoint(x_center - x_half, y_center - y_quarter )],
                FACE_NORTHWEST: [cmpPoint(x_center - x_half, y_center - y_quarter ), 
                                cmpPoint(x_center - x_3quarter, y_center - y_3quarter ), 
                                cmpPoint(x_center - x_quarter, y_center - y_half )]}
                for tri in tri_list[self.heading]:
                    triangle.append(tri)
                del tri_list
                dc.DrawPolygon(triangle)
                dc.SetBrush(wx.NullBrush)
                dc.SetPen(wx.NullPen)
            #selected outline
            if self.selected:
                dc.SetPen(wx.RED_PEN)
                dc.SetBrush(wx.TRANSPARENT_BRUSH)
                dc.DrawRectangle(self.pos.x, self.pos.y, self.bmp.GetWidth(), self.bmp.GetHeight())
                dc.SetBrush(wx.NullBrush)
                dc.SetPen(wx.NullPen)
            if mini_layer.show_labels:
                # draw label
                self.mini_label(mini_layer, dc)
            self.top-=5
            self.bottom+=5
            self.left-=5
            self.right+=5
            return True
        
        
    def mini_label(self, mini_layer, dc):
        label = mini_layer.get_mini_label(self)
        if len(label):
            dc.SetTextForeground(wx.RED)
            (textWidth,textHeight) = dc.GetTextExtent(label)
            x = self.pos.x +((self.bmp.GetWidth() - textWidth) /2) - 1
            y = self.pos.y + self.bmp.GetHeight() + 6
            dc.SetPen(wx.WHITE_PEN)
            dc.SetBrush(wx.WHITE_BRUSH)
            dc.DrawRectangle(x,y,textWidth+2,textHeight+2)
            if (textWidth+2 > self.right):
                self.right += int((textWidth+2-self.right)/2)+1
                self.left -= int((textWidth+2-self.right)/2)+1
            self.bottom = y+textHeight+2-self.pos.y
            dc.SetPen(wx.NullPen)
            dc.SetBrush(wx.NullBrush)
            dc.DrawText(label,x+1,y+1)

    def toxml(self, action="update"):
        if action == "del":
            xml_str = "<miniature action='del' id='" + self.id + "'/>"
            return xml_str
        xml_str = "<miniature"
        xml_str += " action='" + action + "'"
        xml_str += " label='" + self.label + "'"
        xml_str+= " id='" + self.id + "'"
        if self.pos != None:
            xml_str += " posx='" + str(self.pos.x) + "'"
            xml_str += " posy='" + str(self.pos.y) + "'"
        if self.heading != None: xml_str += " heading='" + str(self.heading) + "'"
        if self.face != None: xml_str += " face='" + str(self.face) + "'"
        if self.path != None: xml_str += " path='" + urllib.quote(self.path).replace('%3A', ':') + "'"
        if self.locked: xml_str += "  locked='1'"
        else: xml_str += "  locked='0'"
        if self.hide: xml_str += " hide='1'"
        else: xml_str += " hide='0'"
        if self.snap_to_align != None: xml_str += " align='" + str(self.snap_to_align) + "'"
        if self.id != None: xml_str += " zorder='" + str(self.zorder) + "'"
        if self.width != None: xml_str += " width='" + str(self.width) + "'"
        if self.height != None: xml_str += " height='" + str(self.height) + "'"
        if self.local:
            xml_str += ' local="' + str(self.local) + '"'
            xml_str += ' localPath="' + str(urllib.quote(self.localPath).replace('%3A', ':')) + '"'
            xml_str += ' localTime="' + str(self.localTime) + '"'
        xml_str += " />"
        if (action == "update" and self.isUpdated) or action == "new":
            self.isUpdated = False
            return xml_str
        else: return ''

    def takedom(self, xml_dom):
        self.id = xml_dom.get("id")
        if xml_dom.get("posx") != None: self.pos.x = int(xml_dom.get("posx"))
        if xml_dom.get("posy") != None: self.pos.y = int(xml_dom.get("posy"))
        if xml_dom.get("heading") != None: self.heading = int(xml_dom.get("heading"))
        if xml_dom.get("face") != None: self.face = int(xml_dom.get("face"))
        if xml_dom.get("path") != None:
            self.path = urllib.unquote(xml_dom.get("path"))
            self.set_bmp(ImageHandler.load(self.path, 'miniature', self.id))
        if xml_dom.get("locked") != None:
            if xml_dom.get("locked") == '1' or xml_dom.get("locked") == 'True': self.locked = True
            else: self.locked = False
        if xml_dom.get("hide") != None:
            if xml_dom.get("hide") == '1' or xml_dom.get("hide") == 'True': self.hide = True
            else: self.hide = False
        if xml_dom.get("label") != None: self.label = xml_dom.get("label")
        if xml_dom.get("zorder") != None: self.zorder = int(xml_dom.get("zorder"))
        if xml_dom.get("align") != None:
            if xml_dom.get("align") == '1' or xml_dom.get("align") == 'True': self.snap_to_align = 1
            else: self.snap_to_align = 0
        if xml_dom.get("width") != None: self.width = int(xml_dom.get("width"))
        if xml_dom.get("height") != None: self.height = int(xml_dom.get("height"))

##-----------------------------
## miniature layer
##-----------------------------
class miniature_layer(layer_base):
    def __init__(self, canvas):
        self.canvas = canvas
        layer_base.__init__(self)
        self.id = -1 
        self.miniatures = []
        self.serial_number = 0
        self.show_labels = True
        # Set the font of the labels to be the same as the chat window
        # only smaller.
        font_size = int(settings.get_setting('defaultfontsize'))
        if (font_size >= 10): font_size -= 2
        self.label_font = wx.Font(font_size, 
                                  wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
                                  wx.FONTWEIGHT_NORMAL,
                                  False, settings.get_setting('defaultfont'))

    def next_serial(self):
        self.serial_number += 1
        return self.serial_number

    def get_next_highest_z(self):
        z = len(self.miniatures)+1
        return z

    def cleanly_collapse_zorder(self):
        #  lock the zorder stuff
        sorted_miniatures = self.miniatures[:]
        sorted_miniatures.sort(cmp_zorder)
        i = 0
        for mini in sorted_miniatures:
            mini.zorder = i
            i = i + 1
        #  unlock the zorder stuff

    def collapse_zorder(self):
        #  lock the zorder stuff
        sorted_miniatures = self.miniatures[:]
        sorted_miniatures.sort(cmp_zorder)
        i = 0
        for mini in sorted_miniatures:
            if (mini.zorder != MIN_STICKY_BACK) and (mini.zorder != MIN_STICKY_FRONT): mini.zorder = i
            else: pass
            i = i + 1
        #  unlock the zorder stuff

    def rollback_serial(self):
        self.serial_number -= 1

    def add_miniature(self, id, path, pos=cmpPoint(0,0), label="", heading=FACE_NONE, 
            face=FACE_NONE, width=0, height=0, local=False, localPath='', localTime=-1):
        bmp = ImageHandler.load(path, 'miniature', id)
        if bmp:
            mini = BmpMiniature(id, path, bmp, pos, heading, face, label, 
                zorder=self.get_next_highest_z(), width=width, 
                height=height, local=local, localPath=localPath, localTime=localTime)
            self.miniatures.append(mini)
            xml_str = "<map><miniatures>"
            xml_str += mini.toxml("new")
            xml_str += "</miniatures></map>"
            self.canvas.frame.session.send(xml_str)

    def get_miniature_by_id(self, id):
        for mini in self.miniatures:
            if str(mini.id) == str(id): return mini
        return None

    def del_miniature(self, min):
        xml_str = "<map><miniatures>"
        xml_str += min.toxml("del")
        xml_str += "</miniatures></map>"
        self.canvas.frame.session.send(xml_str)
        self.miniatures.remove(min)
        del min
        self.collapse_zorder()

    def del_all_miniatures(self):
        while len(self.miniatures):
            min = self.miniatures.pop()
            del min
        self.collapse_zorder()

    def layerDraw(self, dc, topleft, size):
        dc.SetFont(self.label_font)
        sorted_miniatures = self.miniatures[:]
        sorted_miniatures.sort(cmp_zorder)
        for m in sorted_miniatures:
            if (m.pos.x>topleft[0]-m.right and
                m.pos.y>topleft[1]-m.bottom and
                m.pos.x<topleft[0]+size[0]-m.left and
                m.pos.y<topleft[1]+size[1]-m.top):
                m.draw(dc, self)

    def find_miniature(self, pt, only_unlocked=False):
        min_list = []
        for m in self.miniatures:
            if m.hit_test(pt):
                if m.hide and self.canvas.frame.session.my_role() != self.canvas.frame.session.ROLE_GM: continue
                if only_unlocked and not m.locked: min_list.append(m)
                elif not only_unlocked and m.locked: min_list.append(m)
                else: continue
        if len(min_list) > 0:
            return min_list
        else: return None

    def layerToXML(self, action="update"):
        """ format  """
        minis_string = ""
        if self.miniatures:
            for m in self.miniatures: minis_string += m.toxml(action)
        if minis_string != '':
            s = "<miniatures"
            s += " serial='" + str(self.serial_number) + "'"
            s += ">"
            s += minis_string
            s += "</miniatures>"
            return s
        else: return ""

    def layerTakeDOM(self, xml_dom):
        if xml_dom.get('serial') != None:
            self.serial_number = int(xml_dom.get('serial'))
        children = xml_dom.getchildren()
        for c in children:
            action = c.get("action")
            id = c.get('id')
            if action == "del": 
                mini = self.get_miniature_by_id(id)
                if mini: self.miniatures.remove(mini); del mini
            elif action == "new":
                pos = cmpPoint(int(c.get('posx')),int(c.get('posy')))
                path = urllib.unquote(c.get('path'))
                label = c.get('label')
                height = width = heading = face = snap_to_align = zorder = 0
                locked = hide = False
                if c.get('height') != None: height = int(c.get('height'))
                if c.get('width') != None: width = int(c.get('width'))
                if c.get('locked') == 'True' or c.get('locked') == '1': locked = True
                if c.get('hide') == 'True' or c.get('hide') == '1': hide = True
                if c.get('heading') != None: heading = int(c.get('heading'))
                if c.get('face') != None: face = int(c.get('face'))
                if c.get('align') != None: snap_to_align = int(c.get('align'))
                if c.get('zorder') != None: zorder = int(c.get('zorder'))
                min = BmpMiniature(id, path, ImageHandler.load(path, 'miniature', id), pos, heading, 
                    face, label, locked, hide, snap_to_align, zorder, width, height)
                self.miniatures.append(min)
                if c.get('local') == 'True' and os.path.exists(urllib.unquote(c.get('localPath'))):
                    localPath = urllib.unquote(c.get('localPath'))
                    local = True
                    localTime = float(c.get('localTime'))
                    if localTime-time.time() <= 144000:
                        file = open(localPath, "rb")
                        imgdata = file.read()
                        file.close()
                        filename = os.path.split(localPath)
                        (imgtype,j) = mimetypes.guess_type(filename[1])
                        postdata = urllib.urlencode({'filename':filename[1], 'imgdata':imgdata, 'imgtype':imgtype})
                        thread.start_new_thread(self.upload, (postdata, localPath, True))
                #  collapse the zorder.  If the client behaved well, then nothing should change.
                #  Otherwise, this will ensure that there's some kind of z-order
                self.collapse_zorder()
            else:
                mini = self.get_miniature_by_id(id)
                if mini: mini.takedom(c)

    def upload(self, postdata, filename, modify=False, pos=cmpPoint(0,0)):
        self.lock.acquire()
        url = settings.get_setting('ImageServerBaseURL')
        file = urllib.urlopen(url, postdata)
        recvdata = file.read()
        file.close()
        try:
            xml_dom = fromstring(recvdata)
            if xml_dom.tag == 'path':
                path = xml_dom.get('url')
                path = urllib.unquote(path)
                if not modify:
                    start = path.rfind("/") + 1
                    if self.canvas.parent.layer_handlers[2].auto_label: min_label = path[start:len(path)-4]
                    else: min_label = ""
                    id = 'mini-' + self.canvas.frame.session.get_next_id()
                    self.add_miniature(id, path, pos=pos, label=min_label, local=True, 
                        localPath=filename, localTime=time.time())
                else:
                    self.miniatures[len(self.miniatures)-1].local = True
                    self.miniatures[len(self.miniatures)-1].localPath = filename
                    self.miniatures[len(self.miniatures)-1].localTime = time.time()
                    self.miniatures[len(self.miniatures)-1].path = path
            else: print xml_dom.get('msg')
        except Exception, e:
            print e
            print recvdata
        finally:
            urllib.urlcleanup()
            self.lock.release()
####################################################################
        ## helper function

    def get_mini_label(self, mini):
        # override this to change the label displayed under each mini (and the label on hidden minis)
        return mini.label
