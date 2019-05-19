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

ORG_PREFIX = "ORG-"  # Prefix of original bones.
MCH_PREFIX = "MCH-"  # Prefix of mechanism bones.
DEF_PREFIX = "DEF-"  # Prefix of deformation bones.
ROOT_NAME = "root"   # Name of the root bone.

#=======================================================================
# Name manipulation
#=======================================================================


def strip_trailing_number(s):
    m = re.search(r'\.(\d{3})$', s)
    return s[0:-4] if m else s


def strip_prefix(name):
    return re.sub(r'^(?:ORG|MCH|DEF)-', '', name)


def unique_name(collection, base_name):
    base_name = strip_trailing_number(base_name)
    count = 1
    name = base_name

    while collection.get(name):
        name = "%s.%03d" % (base_name, count)
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


_prefix_functions = { 'org': org, 'mch': mch, 'def': deformer, 'ctrl': lambda x: x }


def insert_before_lr(name, text):
    name_parts = re.match(r'^(.*?)((?:[._-][lLrR](?:\.\d+)?)?)$', name)
    name_base, name_suffix = name_parts.groups()
    return name_base + text + name_suffix


def make_derived_name(name, subtype, suffix=None):
    """ Replaces the name prefix, and optionally adds the suffix (before .LR if found).
    """
    assert(subtype in _prefix_functions)

    name = strip_prefix(name)

    if suffix:
        name = insert_before_lr(name, suffix)

    return _prefix_functions[subtype](name)


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
