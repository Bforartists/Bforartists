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
#,
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

if "bpy" in locals():
    from imp import reload as _reload
    for val in _modules_loaded.values():
        _reload(val)
_modules = (
    "add_mesh_torus",
    "animsys_update",
    "image",
    "mesh",
    "nla",
    "object_align",
    "object",
    "object_randomize_transform",
    "object_quick_effects",
    "presets",
    "screen_play_rendered_anim",
    "sequencer",
    "uvcalc_follow_active",
    "uvcalc_lightmap",
    "uvcalc_smart_project",
    "vertexpaint_dirt",
    "wm",
)
__import__(name=__name__, fromlist=_modules)
_namespace = globals()
_modules_loaded = {name: _namespace[name] for name in _modules}
del _namespace


import bpy


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)
