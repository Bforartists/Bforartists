# Purpose: DXF12 tag wrapper
# Created: 21.07.2012, taken from my ezdxf project
# Copyright (C) 2012, Manfred Moitzi
# License: MIT License
from __future__ import unicode_literals
__author__ = "mozman <mozman@gmx.at>"


from .dxfattr import DXFAttr, DXFAttributes, DefSubclass
from .dxfentity import DXFEntity
from . import const
from .const import XTYPE_3D, XTYPE_2D_3D

def make_attribs(additional=None):
    dxfattribs = {
        'handle': DXFAttr(5),
        'layer': DXFAttr(8),  # layername as string, default is '0'
        'linetype': DXFAttr(6),  # linetype as string, special names BYLAYER/BYBLOCK, default is BYLAYER
        'thickness': DXFAttr(39),
        'color': DXFAttr(62),  # dxf color index, 0 .. BYBLOCK, 256 .. BYLAYER, default is 256
        'paperspace': DXFAttr(67),  # 0 .. modelspace, 1 .. paperspace, default is 0
        'extrusion': DXFAttr(210, XTYPE_3D),
    }
    if additional:
        dxfattribs.update(additional)
    return DXFAttributes(DefSubclass(None, dxfattribs))


class Line(DXFEntity):
    DXFATTRIBS = make_attribs({
        'start': DXFAttr(10, XTYPE_2D_3D),
        'end': DXFAttr(11, XTYPE_2D_3D),
    })


class Point(DXFEntity):
    DXFATTRIBS = make_attribs({
        'point': DXFAttr(10, XTYPE_2D_3D),
    })


class Circle(DXFEntity):
    DXFATTRIBS = make_attribs({
        'center': DXFAttr(10, XTYPE_2D_3D),
        'radius': DXFAttr(40),
    })


class Arc(DXFEntity):
    DXFATTRIBS = make_attribs({
        'center': DXFAttr(10, XTYPE_2D_3D),
        'radius': DXFAttr(40),
        'startangle': DXFAttr(50),
        'endangle': DXFAttr(51),
    })


class Trace(DXFEntity):
    DXFATTRIBS = make_attribs({
        'vtx0': DXFAttr(10, XTYPE_2D_3D),
        'vtx1': DXFAttr(11, XTYPE_2D_3D),
        'vtx2': DXFAttr(12, XTYPE_2D_3D),
        'vtx3': DXFAttr(13, XTYPE_2D_3D),
    })


Solid = Trace


class Face(DXFEntity):
    DXFATTRIBS = make_attribs({
        'vtx0': DXFAttr(10, XTYPE_2D_3D),
        'vtx1': DXFAttr(11, XTYPE_2D_3D),
        'vtx2': DXFAttr(12, XTYPE_2D_3D),
        'vtx3': DXFAttr(13, XTYPE_2D_3D),
        'invisible_edge': DXFAttr(70),
    })


class Text(DXFEntity):
    DXFATTRIBS = make_attribs({
        'insert': DXFAttr(10, XTYPE_2D_3D),
        'height': DXFAttr(40),
        'text': DXFAttr(1),
        'rotation': DXFAttr(50),  # in degrees (circle = 360deg)
        'oblique': DXFAttr(51),  # in degrees, vertical = 0deg
        'style': DXFAttr(7),  # text style
        'width': DXFAttr(41),  # width FACTOR!
        'textgenerationflag': DXFAttr(71),  # 2 = backward (mirr-x), 4 = upside down (mirr-y)
        'halign': DXFAttr(72),  # horizontal justification
        'valign': DXFAttr(73),  # vertical justification
        'alignpoint': DXFAttr(11, XTYPE_2D_3D),
    })


class Insert(DXFEntity):
    DXFATTRIBS = make_attribs({
        'attribsfollow': DXFAttr(66),
        'name': DXFAttr(2),
        'insert': DXFAttr(10, XTYPE_2D_3D),
        'xscale': DXFAttr(41),
        'yscale': DXFAttr(42),
        'zscale': DXFAttr(43),
        'rotation': DXFAttr(50),
        'colcount': DXFAttr(70),
        'rowcount': DXFAttr(71),
        'colspacing': DXFAttr(44),
        'rowspacing': DXFAttr(45),
    })


class SeqEnd(DXFEntity):
    DXFATTRIBS = DXFAttributes(DefSubclass(None, {'handle': DXFAttr(5), 'paperspace': DXFAttr(67), }))


class Attrib(DXFEntity):  # also ATTDEF
    DXFATTRIBS = make_attribs({
        'insert': DXFAttr(10, XTYPE_2D_3D),
        'height': DXFAttr(40),
        'text': DXFAttr(1),
        'prompt': DXFAttr(3),  # just in ATTDEF not ATTRIB
        'tag': DXFAttr(2),
        'flags': DXFAttr(70),
        'fieldlength': DXFAttr(73),
        'rotation': DXFAttr(50),
        'oblique': DXFAttr(51),
        'width': DXFAttr(41),  # width factor
        'style': DXFAttr(7),
        'textgenerationflag': DXFAttr(71),  # 2 = backward (mirr-x), 4 = upside down (mirr-y)
        'halign': DXFAttr(72),  # horizontal justification
        'valign': DXFAttr(74),  # vertical justification
        'alignpoint': DXFAttr(11, XTYPE_2D_3D),
    })


class Polyline(DXFEntity):
    DXFATTRIBS = make_attribs({
        'elevation': DXFAttr(10, XTYPE_2D_3D),
        'flags': DXFAttr(70),
        'defaultstartwidth': DXFAttr(40),
        'defaultendwidth': DXFAttr(41),
        'mcount': DXFAttr(71),
        'ncount': DXFAttr(72),
        'msmoothdensity': DXFAttr(73),
        'nsmoothdensity': DXFAttr(74),
        'smoothtype': DXFAttr(75),
    })

    def get_vertex_flags(self):
        return const.VERTEX_FLAGS[self.get_mode()]

    @property
    def flags(self):
        return self.get_dxf_attrib('flags', 0)

    def get_mode(self):
        flags = self.flags
        if flags & const.POLYLINE_SPLINE_FIT_VERTICES_ADDED:
            return 'spline2d'
        elif flags & const.POLYLINE_3D_POLYLINE:
            return 'polyline3d'
        elif flags & const.POLYLINE_3D_POLYMESH:
            return 'polymesh'
        elif flags & const.POLYLINE_POLYFACE:
            return 'polyface'
        else:
            return 'polyline2d'

    def is_mclosed(self):
        return bool(self.flags & const.POLYLINE_MESH_CLOSED_M_DIRECTION)

    def is_nclosed(self):
        return bool(self.flags & const.POLYLINE_MESH_CLOSED_N_DIRECTION)


class Vertex(DXFEntity):
    DXFATTRIBS = make_attribs({
        'location': DXFAttr(10, XTYPE_2D_3D),
        'startwidth': DXFAttr(40),
        'endwidth': DXFAttr(41),
        'bulge': DXFAttr(42),
        'flags': DXFAttr(70),
        'tangent': DXFAttr(50),
        'vtx0': DXFAttr(71),
        'vtx1': DXFAttr(72),
        'vtx2': DXFAttr(73),
        'vtx3': DXFAttr(74),
    })


class Block(DXFEntity):
    DXFATTRIBS = make_attribs({
        'name': DXFAttr(2),
        'name2': DXFAttr(3),
        'flags': DXFAttr(70),
        'basepoint': DXFAttr(10, XTYPE_2D_3D),
        'xrefpath': DXFAttr(1),
    })


class EndBlk(SeqEnd):
    DXFATTRIBS = DXFAttributes(DefSubclass(None, {'handle': DXFAttr(5)}))
