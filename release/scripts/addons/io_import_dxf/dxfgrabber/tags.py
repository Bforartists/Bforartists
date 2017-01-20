# Purpose: tag reader
# Created: 21.07.2012, taken from my ezdxf project
# Copyright (C) 2012, Manfred Moitzi
# License: MIT License
from __future__ import unicode_literals
__author__ = "mozman <mozman@gmx.at>"

import os
from .const import ENV_CYTHON

OPTIMIZE = True
if ENV_CYTHON in os.environ:
    if os.environ[ENV_CYTHON].upper() in ('1', 'ON', 'TRUE'):
        OPTIMIZE = True
    else:
        OPTIMIZE = False
try:
    if not OPTIMIZE:
        raise ImportError
    CYTHON_EXT = True
    from.cytags import TagIterator, Tags, TagGroups, DXFTag, NONE_TAG
    from.cytags import DXFStructureError, StringIterator, ClassifiedTags
except ImportError:
    CYTHON_EXT = False
    from.pytags import TagIterator, Tags, TagGroups, DXFTag, NONE_TAG
    from.pytags import DXFStructureError, StringIterator, ClassifiedTags


import sys
from .codepage import toencoding
from .const import acadrelease
from array import array


class DXFInfo(object):
    def __init__(self):
        self.release = 'R12'
        self.version = 'AC1009'
        self.encoding = 'cp1252'
        self.handseed = '0'

    def DWGCODEPAGE(self, value):
        self.encoding = toencoding(value)

    def ACADVER(self, value):
        self.version = value
        self.release = acadrelease.get(value, 'R12')

    def HANDSEED(self, value):
        self.handseed = value


def dxfinfo(stream):
    info = DXFInfo()
    tag = DXFTag(999999, '')
    tagreader = TagIterator(stream)
    while tag != DXFTag(0, 'ENDSEC'):
        tag = next(tagreader)
        if tag.code != 9:
            continue
        name = tag.value[1:]
        method = getattr(info, name, None)
        if method is not None:
            method(next(tagreader).value)
    return info


def binary_encoded_data_to_bytes(data):
    PY3 = sys.version_info[0] >= 3
    byte_array = array('B' if PY3 else b'B')
    for text in data:
        byte_array.extend(int(text[index:index+2], 16) for index in range(0, len(text), 2))
    return byte_array.tobytes() if PY3 else byte_array.tostring()
