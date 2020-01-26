#====================== BEGIN GPL LICENSE BLOCK ======================
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
#======================= END GPL LICENSE BLOCK ========================

# <pep8 compliant>

import random
import time
import re
import collections
import enum

ORG_PREFIX = "ORG-"  # Prefix of original bones.
MCH_PREFIX = "MCH-"  # Prefix of mechanism bones.
DEF_PREFIX = "DEF-"  # Prefix of deformation bones.
ROOT_NAME = "root"   # Name of the root bone.

_PREFIX_TABLE = { 'org': "ORG", 'mch': "MCH", 'def': "DEF", 'ctrl': '' }

#=======================================================================
# Name structure
#=======================================================================

NameParts = collections.namedtuple('NameParts', ['prefix', 'base', 'side_z', 'side', 'number'])


def split_name(name):
    name_parts = re.match(r'^(?:(ORG|MCH|DEF)-)?(.*?)([._-][tTbB])?([._-][lLrR])?(?:\.(\d+))?$', name)
    return NameParts(*name_parts.groups())


def combine_name(parts, *, prefix=None, base=None, side_z=None, side=None, number=None):
    eff_prefix = prefix if prefix is not None else parts.prefix
    eff_number = number if number is not None else parts.number
    if isinstance(eff_number, int):
        eff_number = '%03d' % (eff_number)

    return ''.join([
        eff_prefix+'-' if eff_prefix else '',
        base if base is not None else parts.base,
        side_z if side_z is not None else parts.side_z or '',
        side if side is not None else parts.side or '',
        '.'+eff_number if eff_number else '',
    ])


def insert_before_lr(name, text):
    parts = split_name(name)

    if parts.side:
        return combine_name(parts, base=parts.base + text)
    else:
        return name + text


def make_derived_name(name, subtype, suffix=None):
    """ Replaces the name prefix, and optionally adds the suffix (before .LR if found).
    """
    assert(subtype in _PREFIX_TABLE)

    parts = split_name(name)
    new_base = parts.base + (suffix or '')

    return combine_name(parts, prefix=_PREFIX_TABLE[subtype], base=new_base)


#=======================================================================
# Name mirroring
#=======================================================================

class Side(enum.IntEnum):
    LEFT = -1
    MIDDLE = 0
    RIGHT = 1

    @staticmethod
    def from_parts(parts):
        if parts.side:
            if parts.side[1].lower() == 'l':
                return Side.LEFT
            else:
                return Side.RIGHT
        else:
            return Side.MIDDLE

    @staticmethod
    def to_string(parts, side):
        if side != Side.MIDDLE:
            side_char = 'L' if side == Side.LEFT else 'R'
            side_str = parts.side or parts.side_z

            if side_str:
                sep, schar = side_str[0:2]
                if schar.lower() == schar:
                    side_char = side_char.lower()
            else:
                sep = '.'

            return sep + side_char
        else:
            return ''

    @staticmethod
    def to_name(parts, side):
        new_side = Side.to_string(parts, side)
        return combine_name(parts, side=new_side)


class SideZ(enum.IntEnum):
    TOP = 2
    MIDDLE = 0
    BOTTOM = -2

    @staticmethod
    def from_parts(parts):
        if parts.side_z:
            if parts.side_z[1].lower() == 't':
                return SideZ.TOP
            else:
                return Side.BOTTOM
        else:
            return Side.MIDDLE

    @staticmethod
    def to_string(parts, side):
        if side != SideZ.MIDDLE:
            side_char = 'T' if side == SideZ.TOP else 'B'
            side_str = parts.side_z or parts.side

            if side_str:
                sep, schar = side_str[0:2]
                if schar.lower() == schar:
                    side_char = side_char.lower()
            else:
                sep = '.'

            return sep + side_char
        else:
            return ''

    @staticmethod
    def to_name(parts, side):
        new_side = SideZ.to_string(parts, side)
        return combine_name(parts, side_z=new_side)


def get_name_side(name):
    return Side.from_parts(split_name(name))


def get_name_side_z(name):
    return SideZ.from_parts(split_name(name))


def get_name_base_and_sides(name):
    parts = split_name(name)
    base = combine_name(parts, side='', side_z='')
    return base, Side.from_parts(parts),  SideZ.from_parts(parts)


def change_name_side(name, side=None, *, side_z=None):
    parts = split_name(name)
    new_side = None if side is None else Side.to_string(parts, side)
    new_side_z = None if side_z is None else SideZ.to_string(parts, side_z)
    return combine_name(parts, side=new_side, side_z=new_side_z)


def mirror_name(name):
    parts = split_name(name)
    side = Side.from_parts(parts)

    if side != Side.MIDDLE:
        return Side.to_name(parts, -side)
    else:
        return name


def mirror_name_z(name):
    parts = split_name(name)
    side = SideZ.from_parts(parts)

    if side != SideZ.MIDDLE:
        return SideZ.to_name(parts, -side)
    else:
        return name


#=======================================================================
# Name manipulation
#=======================================================================

def get_name(bone):
    return bone.name if bone else None


def strip_trailing_number(name):
    return combine_name(split_name(name), number='')


def strip_prefix(name):
    return combine_name(split_name(name), prefix='')


def unique_name(collection, base_name):
    parts = split_name(base_name)
    name = combine_name(parts, number='')
    count = 1

    while name in collection:
        name = combine_name(parts, number=count)
        count += 1

    return name


def org_name(name):
    """ Returns the name with ORG_PREFIX stripped from it.
    """
    if name.startswith(ORG_PREFIX):
        return name[len(ORG_PREFIX):]
    else:
        return name


def strip_org(name):
    """ Returns the name with ORG_PREFIX stripped from it.
    """
    if name.startswith(ORG_PREFIX):
        return name[len(ORG_PREFIX):]
    else:
        return name
org_name = strip_org


def strip_mch(name):
    """ Returns the name with ORG_PREFIX stripped from it.
        """
    if name.startswith(MCH_PREFIX):
        return name[len(MCH_PREFIX):]
    else:
        return name

def strip_def(name):
    """ Returns the name with DEF_PREFIX stripped from it.
        """
    if name.startswith(DEF_PREFIX):
        return name[len(DEF_PREFIX):]
    else:
        return name

def org(name):
    """ Prepends the ORG_PREFIX to a name if it doesn't already have
        it, and returns it.
    """
    if name.startswith(ORG_PREFIX):
        return name
    else:
        return ORG_PREFIX + name
make_original_name = org


def mch(name):
    """ Prepends the MCH_PREFIX to a name if it doesn't already have
        it, and returns it.
    """
    if name.startswith(MCH_PREFIX):
        return name
    else:
        return MCH_PREFIX + name
make_mechanism_name = mch


def deformer(name):
    """ Prepends the DEF_PREFIX to a name if it doesn't already have
        it, and returns it.
    """
    if name.startswith(DEF_PREFIX):
        return name
    else:
        return DEF_PREFIX + name
make_deformer_name = deformer


def random_id(length=8):
    """ Generates a random alphanumeric id string.
    """
    tlength = int(length / 2)
    rlength = int(length / 2) + int(length % 2)

    chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
    text = ""
    for i in range(0, rlength):
        text += random.choice(chars)
    text += str(hex(int(time.time())))[2:][-tlength:].rjust(tlength, '0')[::-1]
    return text
