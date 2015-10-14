#BEGIN GPL LICENSE BLOCK

#This program is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public License
#as published by the Free Software Foundation; either version 2
#of the License, or (at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software Foundation,
#Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

#END GPL LICENCE BLOCK

bl_info = {
    "name": "Btrace",
    "author": "liero, crazycourier, Atom, Meta-Androcto, MacKracken",
    "version": (1, 1, ),
    "blender": (2, 68, 0),
    "location": "View3D > Tools",
    "description": "Tools for converting/animating objects/particles into curves",
    "warning": "Still under development, bug reports appreciated",
    "wiki_url": "",
    "tracker_url": "https://developer.blender.org/maniphest/project/3/type/Bug/",
    "category": "Add Curve"}


import bpy
from .bTrace import *
import selection_utils
from bpy.props import FloatProperty, EnumProperty, IntProperty, BoolProperty, FloatVectorProperty

### Define Classes to register
classes = [
    TracerProperties,
    TracerPropertiesMenu,
    addTracerObjectPanel,
    OBJECT_OT_convertcurve,
    OBJECT_OT_objecttrace,
    OBJECT_OT_objectconnect,
    OBJECT_OT_writing,
    OBJECT_OT_particletrace,
    OBJECT_OT_traceallparticles,
    OBJECT_OT_curvegrow,
    OBJECT_OT_reset,
    OBJECT_OT_fcnoise,
    OBJECT_OT_meshfollow,
    OBJECT_OT_materialChango,
    OBJECT_OT_clearColorblender
    ]

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.WindowManager.curve_tracer = bpy.props.PointerProperty(type=TracerProperties)
    bpy.types.WindowManager.btrace_menu = bpy.props.PointerProperty(type=TracerPropertiesMenu, update=deselect_others)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.WindowManager.curve_tracer
if __name__ == "__main__":
    register()
