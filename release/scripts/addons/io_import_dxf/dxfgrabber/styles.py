# Purpose: handle text styles
# Created: 06.01.2014
# Copyright (C) 2014, Manfred Moitzi
# License: MIT License
from __future__ import unicode_literals
__author__ = "mozman <mozman@gmx.at>"

from .dxfentity import DXFEntity
from .layers import Table
from .dxfattr import DXFAttr, DXFAttributes, DefSubclass
from .tags import ClassifiedTags


class Style(object):
    def __init__(self, wrapper):
        self.name = wrapper.get_dxf_attrib('name')
        self.height = wrapper.get_dxf_attrib('height')
        self.width = wrapper.get_dxf_attrib('width')
        self.oblique = wrapper.get_dxf_attrib('oblique')
        # backward & mirror_y was first and stays for compatibility
        self.backward = bool(wrapper.get_dxf_attrib('generation_flags') & 2)
        self.mirror_y = bool(wrapper.get_dxf_attrib('generation_flags') & 4)
        self.is_backwards = self.backward
        self.is_upside_down = self.mirror_y
        self.font = wrapper.get_dxf_attrib('font')
        self.bigfont = wrapper.get_dxf_attrib('bigfont', "")


class StyleTable(Table):
    name = 'styles'

    @staticmethod
    def from_tags(tags, drawing):
        dxfversion = drawing.dxfversion
        styles = StyleTable()
        for entrytags in styles._classified_tags(tags):
            dxfstyle = styles.wrap(entrytags, dxfversion)
            styles._table_entries[dxfstyle.get_dxf_attrib('name')] = Style(dxfstyle)
        return styles
    
    @staticmethod
    def wrap(tags, dxfversion):
        return DXF12Style(tags) if dxfversion == "AC1009" else DXF13Style(tags)


class DXF12Style(DXFEntity):
    DXFATTRIBS = DXFAttributes(DefSubclass(None, {
        'handle': DXFAttr(5),
        'name': DXFAttr(2),
        'flags': DXFAttr(70),
        'height': DXFAttr(40),  # fixed height, 0 if not fixed
        'width': DXFAttr(41),  # width factor
        'oblique': DXFAttr(50),  # oblique angle in degree, 0 = vertical
        'generation_flags': DXFAttr(71),  # 2 = backward, 4 = mirrored in Y
        'last_height': DXFAttr(42),  # last height used
        'font': DXFAttr(3),  # primary font file name
        'bigfont': DXFAttr(4),  # big font name, blank if none
    }))

none_subclass = DefSubclass(None, {'handle': DXFAttr(5)})
symbol_subclass = DefSubclass('AcDbSymbolTableRecord', {})
style_subclass = DefSubclass('AcDbTextStyleTableRecord', {
    'name': DXFAttr(2),
    'flags': DXFAttr(70),
    'height': DXFAttr(40),  # fixed height, 0 if not fixed
    'width': DXFAttr(41),  # width factor
    'oblique': DXFAttr(50),  # oblique angle in degree, 0 = vertical
    'generation_flags': DXFAttr(71),  # 2 = backward, 4 = mirrored in Y
    'last_height': DXFAttr(42),  # last height used
    'font': DXFAttr(3),  # primary font file name
    'bigfont': DXFAttr(4),  # big font name, blank if none
})


class DXF13Style(DXF12Style):
    DXFATTRIBS = DXFAttributes(none_subclass, symbol_subclass, style_subclass)

DEFAULT_STYLE = """  0
STYLE
  2
STANDARD
 70
0
 40
0.0
 41
1.0
 50
0.0
 71
0
 42
1.0
  3
Arial
  4

"""

default_text_style = Style(DXF12Style(ClassifiedTags.from_text(DEFAULT_STYLE)))