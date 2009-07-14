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
# File: mapper/isometric.py
# Author: Todd Faris (Snowdog)
# Maintainer:
# Version:
#
# Description:
#   helper class definition for drawing and line collision within an isometric grid
#   based on a interger based coordinate system where X increase to the right
#   and Y increases in the downward direction


class IsoGrid:
    def __init__(self,width):
        self.ratio = 2.0
        self.width = width
        self.height = 0
        self.CalcRatio()
        self.center_x = 0
        self.center_y = 0

    def Ratio(self, r ):
        "changes the height/width ratio of the isometric rectangle with respect to the horizontal (x) axis"
        self.ratio = float(r)
        self.CalcRatio()

    def CalcRatio(self):
        if (self.ratio <= 0): self.ratio = 1
        self.height = int( float(self.width)/float(self.ratio) )

    def BoundPlace(self, left,top):
        "Places the isometric rectangle using its upper left bounding corner for positioning"
        dx,dy = self.CornerOffset()
        self.Recenter( left+dx, top+dy)

    def Recenter(self,x,y):
        "Places the isomentric rectangle using the centerpoint"
        self.center_x = x
        self.center_y = y

    def Top(self):
        "Returns the topmost point of the isometric rectangle as a tuple (x,y)"
        x = int(self.center_x)
        y = int(self.center_y) - int(self.height/2)
        return(x,y)

    def Left(self):
        "Returns the leftmost point of the isometric rectangle as a tuple (x,y)"
        x = int(self.center_x) - int(self.width/2)
        y = int(self.center_y)
        return(x,y)

    def Right(self):
        "Returns the rightmost point of the isometric rectangle as a tuple (x,y)"
        x,y = self.Left()
        x = x + self.width
        return(x,y)

    def Bottom(self):
        "Returns the bottommost point of the isometric rectangle as a tuple (x,y)"
        x,y = self.Top()
        y = y + self.height
        return(x,y)

    def Center(self):
        "Returns the center point of the isometric rectangle as a tuple (x,y)"
        x = int(self.center_x)
        y = int(self.center_y)
        return(x,y)

    def CornerOffset(self):
        """Returns a tuple (delta_x,delta_y) representing the offset from the centerpoint
        of the isometric rectangle to the upper left corner of its rectangular bounding box"""
        dx = float(self.width/2)
        dy = float(self.height/2)
        return (dx,dy)

    def Height(self):
        "Returns the height of the isometric rectangle based on current ratio"
        return int(self.height)

    def Width(self):
        "returns the width of the isomentric rectangle"
        return int(self.width)
