# <pep8-80 compliant>

# ##### BEGIN GPL LICENSE BLOCK #####
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


__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "3.2"
__date__ = "20 Jun 2015"


DEBUG = False

# Properties used in this add-on.
class CPUVProperties():
    default = None
    selseq = None
    uvmap = None
    transuv = None

    def __init__(self):
        self.default = CPUVDefaultOpsProps()
        self.selseq = CPUVSelSeqOpsProps()
        self.uvmap = CPUVUVMapOpsProps()
        self.transuv = CPUVTransUVOpsProps()


class CPUVDefaultOpsProps():
    src_uv_map = None
    src_obj = None
    src_faces = None


class CPUVSelSeqOpsProps():
    src_uv_map = None
    src_obj = None
    src_faces = None


class CPUVUVMapOpsProps():
    src_uv_map = None
    src_obj = None
    src_faces = None


class CPUVTransUVOpsProps():
    topology_copied = []


def init_properties(props):
    props.src_uv_map = None
    props.src_obj = None
    props.src_faces = None
