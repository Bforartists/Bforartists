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

bl_info = {
    "name": "Cell Fracture Crack It",
    "author": "Nobuyuki Hirakata",
    "version": (0, 1, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Toolshelf > Create Tab",
    "description": "Displaced Cell Fracture Addon",
    "warning": "Make sure to enable 'Object: Cell Fracture' Addon",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/Object/CrackIt",
    "category": "Object"
}

if 'bpy' in locals():
    import importlib
    importlib.reload(operator)

else:
    from . import operator

import bpy
from bpy.types import PropertyGroup
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        )
from .operator import (
    CRACKIT_OT_fracture,
    CRACKIT_OT_material,
    CRACKIT_PT_main,
    )
import os


class CrackItProperties(PropertyGroup):
    # Input on toolshelf before execution
    # In Panel subclass, In bpy.types.Operator subclass,
    # reference them by context.scene.crackit

    fracture_childverts: BoolProperty(
            name="From Child Verts",
            description="Use child object's vertices and position for origin of crack",
            default=False
            )
    fracture_scalex: FloatProperty(
            name="Scale X",
            description="Scale X",
            default=1.00,
            min=0.00,
            max=1.00
            )
    fracture_scaley: FloatProperty(
            name="Scale Y",
            description="Scale Y",
            default=1.00,
            min=0.00,
            max=1.00
            )
    fracture_scalez: FloatProperty(
            name="Scale Z",
            description="Scale Z",
            default=1.00,
            min=0.00,
            max=1.00
            )
    fracture_div: IntProperty(
            name="Max Crack",
            description="Max Crack",
            default=100,
            min=0,
            max=10000
            )
    fracture_margin: FloatProperty(
            name="Margin Size",
            description="Margin Size",
            default=0.001,
            min=0.000,
            max=1.000
            )
    extrude_offset: FloatProperty(
            name="Offset",
            description="Extrude Offset",
            default=0.10,
            min=0.00,
            max=2.00
            )
    extrude_random: FloatProperty(
            name="Random",
            description="Extrude Random",
            default=0.30,
            min=-1.00,
            max=1.00
            )
    # Path of the addon
    material_addonpath = os.path.dirname(__file__)
    # Selection of material preset
    # Note: you can choose the original name in the library blend
    # or the prop name
    material_preset: EnumProperty(
            name="Preset",
            description="Material Preset",
            items=[
                ('crackit_organic_mud', "Organic Mud", "Mud material"),
                ('crackit_mud', "Mud", "Mud material"),
                ('crackit_tree_moss', "Tree Moss", "Tree Material"),
                ('crackit_tree_dry', "Tree Dry", "Tree Material"),
                ('crackit_tree_red', "Tree Red", "Tree Material"),
                ('crackit_rock', "Rock", "Rock Material"),
                ('crackit_lava', "Lava", "Lava Material"),
                ('crackit_wet-paint', "Wet Paint", "Paint Material"),
                ('crackit_soap', "Soap", "Soap Material"),
                ]
            )
    material_lib_name: BoolProperty(
            name="Library Name",
            description="Use the original Material name from the .blend library\n"
                        "instead of the one defined in the Preset",
            default=True
            )

classes = (
    CRACKIT_OT_fracture,
    CRACKIT_OT_material,
    CRACKIT_PT_main,
    CrackItProperties,
    )

def register():

    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.Scene.crackit = PointerProperty(type=CrackItProperties)
    
def unregister():

    del bpy.types.Scene.crackit
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)