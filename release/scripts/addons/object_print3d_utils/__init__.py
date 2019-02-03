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

# <pep8 compliant>

bl_info = {
    "name": "3D Print Toolbox",
    "author": "Campbell Barton",
    "blender": (2, 80, 0),
    "location": "3D View > Toolbox",
    "description": "Utilities for 3D printing",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Modeling/PrintToolbox",
    "support": 'OFFICIAL',
    "category": "Mesh",
    }


if "bpy" in locals():
    import importlib
    importlib.reload(ui)
    importlib.reload(operators)
    importlib.reload(mesh_helpers)
else:
    import math

    import bpy
    from bpy.props import (
            StringProperty,
            BoolProperty,
            FloatProperty,
            EnumProperty,
            PointerProperty,
            )
    from bpy.types import (
            AddonPreferences,
            PropertyGroup,
            )

    from . import (
            ui,
            operators,
            )


class Print3D_Scene_Props(PropertyGroup):
    export_format: EnumProperty(
        name="Format",
        description="Format type to export to",
        items=(
            ('STL', "STL", ""),
            ('PLY', "PLY", ""),
            ('WRL', "VRML2", ""),
            ('X3D', "X3D", ""),
            ('OBJ', "OBJ", ""),
        ),
        default='STL',
    )
    use_export_texture: BoolProperty(
        name="Copy Textures",
        description="Copy textures on export to the output path",
        default=False,
    )
    use_apply_scale: BoolProperty(
        name="Apply Scale",
        description="Apply scene scale setting on export",
        default=False,
    )
    export_path: StringProperty(
        name="Export Directory",
        description="Path to directory where the files are created",
        default="//", maxlen=1024, subtype="DIR_PATH",
    )
    thickness_min: FloatProperty(
        name="Thickness",
        description="Minimum thickness",
        subtype='DISTANCE',
        default=0.001,  # 1mm
        min=0.0, max=10.0,
    )
    threshold_zero: FloatProperty(
        name="Threshold",
        description="Limit for checking zero area/length",
        default=0.0001,
        precision=5,
        min=0.0, max=0.2,
    )
    angle_distort: FloatProperty(
        name="Angle",
        description="Limit for checking distorted faces",
        subtype='ANGLE',
        default=math.radians(45.0),
        min=0.0, max=math.radians(180.0),
    )
    angle_sharp: FloatProperty(
        name="Angle",
        subtype='ANGLE',
        default=math.radians(160.0),
        min=0.0, max=math.radians(180.0),
    )
    angle_overhang: FloatProperty(
        name="Angle",
        subtype='ANGLE',
        default=math.radians(45.0),
        min=0.0, max=math.radians(90.0),
    )


classes = (
    ui.VIEW3D_PT_Print3D_Object,
    ui.VIEW3D_PT_Print3D_Mesh,

    operators.MESH_OT_Print3D_Info_Volume,
    operators.MESH_OT_Print3D_Info_Area,

    operators.MESH_OT_Print3D_Check_Degenerate,
    operators.MESH_OT_Print3D_Check_Distorted,
    operators.MESH_OT_Print3D_Check_Solid,
    operators.MESH_OT_Print3D_Check_Intersections,
    operators.MESH_OT_Print3D_Check_Thick,
    operators.MESH_OT_Print3D_Check_Sharp,
    operators.MESH_OT_Print3D_Check_Overhang,
    operators.MESH_OT_Print3D_Check_All,

    operators.MESH_OT_Print3D_Clean_Isolated,
    operators.MESH_OT_Print3D_Clean_Distorted,
    # operators.MESH_OT_Print3D_Clean_Thin,
    operators.MESH_OT_Print3D_Clean_Non_Manifold,

    operators.MESH_OT_Print3D_Select_Report,

    operators.MESH_OT_Print3D_Scale_To_Volume,
    operators.MESH_OT_Print3D_Scale_To_Bounds,

    operators.MESH_OT_Print3D_Export,

    Print3D_Scene_Props,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.print_3d = PointerProperty(type=Print3D_Scene_Props)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.print_3d
