# Purpose: tag reader
# Created: 21.07.2012, taken from my ezdxf project
# Copyright (C) 2012, Manfred Moitzi
# License: MIT License
from __future__ import unicode_literals
__author__ = "mozman <mozman@gmx.at>"

from io import StringIO
from collections import namedtuple
from itertools import chain, islice
from . import tostr


DXFTag = namedtuple('DXFTag', 'code value')
NONE_TAG = DXFTag(999999, 'NONE')
APP_DATA_MARKER = 102
SUBCLASS_MARKER = 100
XDATA_MARKER = 1001


class DXFStructureError(Exception):
    pass


def point_tuple(value):
    return tuple(float(f) for f in value)


POINT_CODES = frozenset(chain(range(10, 20), (210, ), range(110, 113), range(1010, 1020)))


def is_point_tag(tag):
    return tag[0] in POINT_CODES


class TagIterator(object):
    def __init__(self, textfile, assure_3d_coords=False):
        self.textfile = textfile
        self.readline = textfile.readline
        self.undo = False
        self.last_tag = NONE_TAG
        self.undo_coord = None
        self.eof = False
        self.assure_3d_coords = assure_3d_coords

    def __iter__(self):
        return self

    def __next__(self):
        def undo_tag():
            self.undo = False
            tag = self.last_tag
            return tag

        def read_next_tag():
            try:
                code = int(self.readline())
                value = self.readline().rstrip('\n')
            except UnicodeDecodeError:
                raise  # because UnicodeDecodeError() is a subclass of ValueError()
            except (EOFError, ValueError):
                raise StopIteration()
            return code, value

        def read_point(code_x, value_x):
            try:
                code_y, value_y = read_next_tag()  # 2. coordinate is always necessary
            except StopIteration:
                code_y = 0  # -> DXF structure error in following if-statement

            if code_y != code_x + 10:
                raise DXFStructureError("invalid 2D/3D point found")

            value_y = float(value_y)
            try:
                code_z, value_z = read_next_tag()
            except StopIteration:  # 2D point at end of file
                self.eof = True  # store reaching end of file
                if self.assure_3d_coords:
                    value = (value_x, value_y, 0.)
                else:
                    value = (value_x, value_y)
            else:
                if code_z != code_x + 20:  # not a Z coordinate -> 2D point
                    self.undo_coord = (code_z, value_z)
                    if self.assure_3d_coords:
                        value = (value_x, value_y, 0.)
                    else:
                        value = (value_x, value_y)
                else:  # is a 3D point
                    value = (value_x, value_y, float(value_z))
            return value

        def next_tag():
            code = 999
            while code == 999:  # skip comments
                if self.undo_coord is not None:
                    code, value = self.undo_coord
                    self.undo_coord = None
                else:
                    code, value = read_next_tag()

                if code in POINT_CODES:  # 2D or 3D point
                    value = read_point(code, float(value))  # returns a tuple of floats, no casting needed
                else:
                    value = cast_tag_value(code, value)
            self.last_tag = DXFTag(code, value)
            return self.last_tag

        if self.eof:  # stored end of file
            raise StopIteration()

        if self.undo:
            return undo_tag()
        else:
            return next_tag()
    # for Python 2.7
    next = __next__

    def undo_tag(self):
        if not self.undo:
            self.undo = True
        else:
            raise ValueError('No tag to undo')


class StringIterator(TagIterator):
    def __init__(self, dxfcontent):
        super(StringIterator, self).__init__(StringIO(dxfcontent))


class TagCaster:
    def __init__(self):
        self._cast = self._build()

    def _build(self):
        table = {}
        for caster, codes in TYPES:
            for code in codes:
                table[code] = caster
        return table

    def cast(self, tag):
        code, value = tag
        typecaster = self._cast.get(code, tostr)
        try:
            value = typecaster(value)
        except ValueError:
            if typecaster is int:  # convert float to int
                value = int(float(value))
            else:
                raise
        return DXFTag(code, value)

    def cast_value(self, code, value):
        typecaster = self._cast.get(code, tostr)
        try:
            return typecaster(value)
        except ValueError:
            if typecaster is int:  # convert float to int
                return int(float(value))
            else:
                raise

TYPES = [
    (tostr, range(0, 10)),
    (point_tuple, range(10, 20)),
    (float, range(20, 60)),
    (int, range(60, 100)),
    (tostr, range(100, 106)),
    (point_tuple, range(110, 113)),
    (float, range(113, 150)),
    (int, range(170, 180)),
    (point_tuple, [210]),
    (float, range(211, 240)),
    (int, range(270, 290)),
    (int, range(290, 300)),  # bool 1=True 0=False
    (tostr, range(300, 370)),
    (int, range(370, 390)),
    (tostr, range(390, 400)),
    (int, range(400, 410)),
    (tostr, range(410, 420)),
    (int, range(420, 430)),
    (tostr, range(430, 440)),
    (int, range(440, 460)),
    (float, range(460, 470)),
    (tostr, range(470, 480)),
    (tostr, range(480, 482)),
    (tostr, range(999, 1010)),
    (point_tuple, range(1010, 1020)),
    (float, range(1020, 1060)),
    (int, range(1060, 1072)),
]

_TagCaster = TagCaster()
cast_tag = _TagCaster.cast
cast_tag_value = _TagCaster.cast_value


class Tags(list):
    """ DXFTag() chunk as flat list. """
    def find_all(self, code):
        """ Returns a list of DXFTag(code, ...). """
        return [tag for tag in self if tag.code == code]

    def tag_index(self, code, start=0, end=None):
        """ Return first index of DXFTag(code, ...). """
        if end is None:
            end = len(self)
        for index, tag in enumerate(islice(self, start, end)):
            if tag.code == code:
                return start+index
        raise ValueError(code)

    def get_value(self, code):
        for tag in self:
            if tag.code == code:
                return tag.value
        raise ValueError(code)

    @staticmethod
    def from_text(text):
        return Tags(StringIterator(text))

    def get_type(self):
        return self.__getitem__(0).value


class TagGroups(list):
    """
    Group of tags starting with a SplitTag and ending before the next SplitTag.

    A SplitTag is a tag with code == splitcode, like (0, 'SECTION') for splitcode=0.

    """
    def __init__(self, tags, split_code=0):
        super(TagGroups, self).__init__()
        self._buildgroups(tags, split_code)

    def _buildgroups(self, tags, split_code):
        def push_group():
            if len(group) > 0:
                self.append(group)

        def start_tag(itags):
            tag = next(itags)
            while tag.code != split_code:
                tag = next(itags)
            return tag

        itags = iter(tags)
        group = Tags([start_tag(itags)])

        for tag in itags:
            if tag.code == split_code:
                push_group()
                group = Tags([tag])
            else:
                group.append(tag)
        push_group()

    def get_name(self, index):
        return self[index][0].value

    @staticmethod
    def from_text(text, split_code=0):
        return TagGroups(Tags.from_text(text), split_code)


class ClassifiedTags:
    """ Manage Subclasses, AppData and Extended Data """

    def __init__(self, iterable=None):
        self.appdata = list()  # code == 102, keys are "{<arbitrary name>", values are Tags()
        self.subclasses = list()  # code == 100, keys are "subclassname", values are Tags()
        self.xdata = list()  # code >= 1000, keys are "APPNAME", values are Tags()
        if iterable is not None:
            self._setup(iterable)

    @property
    def noclass(self):
        return self.subclasses[0]

    def _setup(self, iterable):
        tagstream = iter(iterable)

        def collect_subclass(start_tag):
            """ a subclass can contain appdata, but not xdata, ends with
            SUBCLASSMARKER or XDATACODE.
            """
            data = Tags() if start_tag is None else Tags([start_tag])
            try:
                while True:
                    tag = next(tagstream)
                    if tag.code == APP_DATA_MARKER and tag.value[0] == '{':
                        app_data_pos = len(self.appdata)
                        data.append(DXFTag(tag.code, app_data_pos))
                        collect_appdata(tag)
                    elif tag.code in (SUBCLASS_MARKER, XDATA_MARKER):
                        self.subclasses.append(data)
                        return tag
                    else:
                        data.append(tag)
            except StopIteration:
                pass
            self.subclasses.append(data)
            return NONE_TAG

        def collect_appdata(starttag):
            """ appdata, can not contain xdata or subclasses """
            data = Tags([starttag])
            while True:
                try:
                    tag = next(tagstream)
                except StopIteration:
                    raise DXFStructureError("Missing closing DXFTag(102, '}') for appdata structure.")
                data.append(tag)
                if tag.code == APP_DATA_MARKER:
                    break
            self.appdata.append(data)

        def collect_xdata(starttag):
            """ xdata are always at the end of the entity and can not contain
            appdata or subclasses
            """
            data = Tags([starttag])
            try:
                while True:
                    tag = next(tagstream)
                    if tag.code == XDATA_MARKER:
                        self.xdata.append(data)
                        return tag
                    else:
                        data.append(tag)
            except StopIteration:
                pass
            self.xdata.append(data)
            return NONE_TAG

        tag = collect_subclass(None)  # preceding tags without a subclass
        while tag.code == SUBCLASS_MARKER:
            tag = collect_subclass(tag)
        while tag.code == XDATA_MARKER:
            tag = collect_xdata(tag)

        if tag is not NONE_TAG:
            raise DXFStructureError("Unexpected tag '%r' at end of entity." % tag)

    def __iter__(self):
        for subclass in self.subclasses:
            for tag in subclass:
                if tag.code == APP_DATA_MARKER and isinstance(tag.value, int):
                    for subtag in self.appdata[tag.value]:
                        yield subtag
                else:
                    yield tag

        for xdata in self.xdata:
            for tag in xdata:
                yield tag

    def get_subclass(self, name):
        for subclass in self.subclasses:
            if len(subclass) and subclass[0].value == name:
                return subclass
        raise KeyError("Subclass '%s' does not exist." % name)

    def get_xdata(self, appid):
        for xdata in self.xdata:
            if xdata[0].value == appid:
                return xdata
        raise ValueError("No extended data for APPID '%s'" % appid)

    def get_appdata(self, name):
        for appdata in self.appdata:
            if appdata[0].value == name:
                return appdata
        raise ValueError("Application defined group '%s' does not exist." % name)

    def get_type(self):
        return self.noclass[0].value

    @staticmethod
    def from_text(text):
        return ClassifiedTags(StringIterator(text))
