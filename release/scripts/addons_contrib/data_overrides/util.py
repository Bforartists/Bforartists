### BEGIN GPL LICENSE BLOCK #####
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
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import bpy, time, sys, hashlib
from bpy.types import UILayout
from math import *

def data_uuid(id_data, path=""):
    identifier = id_data.name.encode(encoding="utf-8")
    if id_data.library:
        identifier += b'\0' + id_data.library.filepath.encode(encoding="utf-8")
    if path:
        identifier += b'\0' + path.encode(encoding="utf-8")

    m = hashlib.md5()
    m.update(identifier)
    return m.hexdigest(), int.from_bytes(m.digest(), byteorder='big') % 0xFFFFFFFF

_id_collections = [ c.identifier for c in bpy.types.BlendData.bl_rna.properties if isinstance(c, bpy.types.CollectionProperty) and isinstance(c.fixed_type, bpy.types.ID) ]
def _id_data_blocks(blend_data):
    for name in _id_collections:
        coll = getattr(blend_data, name)
        for id_data in coll:
            yield id_data

def find_id_data(blend_data, name, library):
    if library:
        for id_data in _id_data_blocks(blend_data):
            if id_data.library and id_data.library.filepath == library and id_data.name == name:
                return id_data
    else:
        for id_data in _id_data_blocks(blend_data):
            if not id_data.library and id_data.name == name:
                return id_data

def id_data_from_enum(identifier):
    for id_data in _id_data_blocks(bpy.data):
        if str(id_data.as_pointer()) == identifier:
            return id_data

def id_data_enum_item(id_data):
    #identifier, number = id_data_uuid(id_data)
    number = id_data.as_pointer() % 0xFFFFFFFF
    identifier = str(id_data.as_pointer())
    return (identifier, id_data.name, "", UILayout.icon(id_data), number)
