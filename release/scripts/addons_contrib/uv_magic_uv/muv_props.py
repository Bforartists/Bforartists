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
__version__ = "4.1"
__date__ = "13 Nov 2016"


import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty

DEBUG = False


def get_loaded_texture_name(scene, context):
    items = [(key, key, "") for key in bpy.data.images.keys()]
    items.append(("None", "None", ""))
    return items


# Properties used in this add-on.
class MUV_Properties():
    cpuv = None
    cpuv_obj = None
    cpuv_selseq = None
    transuv = None
    uvbb = None
    texproj = None
    texlock = None
    texwrap = None
    wsuv = None

    def __init__(self):
        self.cpuv = MUV_CPUVProps()
        self.cpuv_obj = MUV_CPUVProps()
        self.cpuv_selseq = MUV_CPUVSelSeqProps()
        self.transuv = MUV_TransUVProps()
        self.uvbb = MUV_UVBBProps()
        self.texproj = MUV_TexProjProps()
        self.texlock = MUV_TexLockProps()
        self.texwrap = MUV_TexWrapProps()
        self.wsuv = MUV_WSUVProps()


class MUV_CPUVProps():
    src_uvs = []
    src_pin_uvs = []


class MUV_CPUVSelSeqProps():
    src_uvs = []
    src_pin_uvs = []


class MUV_TransUVProps():
    topology_copied = []


class MUV_UVBBProps():
    uv_info_ini = []
    ctrl_points_ini = []
    ctrl_points = []
    running = False


class MUV_TexProjProps():
    running = False


class MUV_TexLockProps():
    verts_orig = None
    intr_verts_orig = None
    intr_running = False


class MUV_TexWrapProps():
    src_face_index = -1


class MUV_WSUVProps():
    ref_sv = None
    ref_suv = None


def init_props(scene):
    scene.muv_props = MUV_Properties()
    scene.muv_uvbb_cp_size = FloatProperty(
        name="Size",
        description="Control Point Size",
        default=6.0,
        min=3.0,
        max=100.0)
    scene.muv_uvbb_cp_react_size = FloatProperty(
        name="React Size",
        description="Size event fired",
        default=10.0,
        min=3.0,
        max=100.0)
    scene.muv_uvbb_uniform_scaling = BoolProperty(
        name="Uniform Scaling",
        description="Enable Uniform Scaling",
        default=False)
    scene.muv_texproj_tex_magnitude = FloatProperty(
        name="Magnitude",
        description="Texture Magnitude.",
        default=0.5,
        min=0.0,
        max=100.0)
    scene.muv_texproj_tex_image = EnumProperty(
        name="Image",
        description="Texture Image.",
        items=get_loaded_texture_name)
    scene.muv_texproj_tex_transparency = FloatProperty(
        name="Transparency",
        description="Texture Transparency.",
        default=0.2,
        min=0.0,
        max=1.0)


def clear_props(scene):
    del scene.muv_props
    del scene.muv_uvbb_cp_size
    del scene.muv_uvbb_cp_react_size
    del scene.muv_texproj_tex_magnitude
    del scene.muv_texproj_tex_image
    del scene.muv_texproj_tex_transparency
