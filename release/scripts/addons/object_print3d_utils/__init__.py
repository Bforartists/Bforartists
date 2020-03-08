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
    "name": "3D-Print Toolbox",
    "author": "Campbell Barton",
    "blender": (2, 82, 0),
    "location": "3D View > Sidebar",
    "description": "Utilities for 3D printing",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/mesh/3d_print_toolbox.html",
    "support": 'OFFICIAL',
    "category": "Mesh",
}


if "bpy" in locals():
    import importlib
    importlib.reload(ui)
    importlib.reload(operators)
    importlib.reload(mesh_helpers)
    if "export" in locals():
        importlib.reload(export)
else:
    import math

    import bpy
    from bpy.types import PropertyGroup
    from bpy.props import (
        StringProperty,
        BoolProperty,
        FloatProperty,
        EnumProperty,
        PointerProperty,
    )

    from . import (
        ui,
        operators,
    )


class SceneProperties(PropertyGroup):
    export_format: EnumProperty(
        name="Format",
        description="Format type to export to",
        items=(
            ('STL', "STL", ""),
            ('PLY', "PLY", ""),
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
        default="//",
        maxlen=1024,
        subtype="DIR_PATH",
    )
    thickness_min: FloatProperty(
        name="Thickness",
        description="Minimum thickness",
        subtype='DISTANCE',
        default=0.001,  # 1mm
        min=0.0,
        max=10.0,
    )
    threshold_zero: FloatProperty(
        name="Threshold",
        description="Limit for checking zero area/length",
        default=0.0001,
        precision=5,
        min=0.0,
        max=0.2,
    )
    angle_distort: FloatProperty(
        name="Angle",
        description="Limit for checking distorted faces",
        subtype='ANGLE',
        default=math.radians(45.0),
        min=0.0,
        max=math.radians(180.0),
    )
    angle_sharp: FloatProperty(
        name="Angle",
        subtype='ANGLE',
        default=math.radians(160.0),
        min=0.0,
        max=math.radians(180.0),
    )
    angle_overhang: FloatProperty(
        name="Angle",
        subtype='ANGLE',
        default=math.radians(45.0),
        min=0.0,
        max=math.radians(90.0),
    )


classes = (
    SceneProperties,

    ui.VIEW3D_PT_print3d_analyze,
    ui.VIEW3D_PT_print3d_cleanup,
    ui.VIEW3D_PT_print3d_transform,
    ui.VIEW3D_PT_print3d_export,

    operators.MESH_OT_print3d_info_volume,
    operators.MESH_OT_print3d_info_area,
    operators.MESH_OT_print3d_check_degenerate,
    operators.MESH_OT_print3d_check_distorted,
    operators.MESH_OT_print3d_check_solid,
    operators.MESH_OT_print3d_check_intersections,
    operators.MESH_OT_print3d_check_thick,
    operators.MESH_OT_print3d_check_sharp,
    operators.MESH_OT_print3d_check_overhang,
    operators.MESH_OT_print3d_check_all,
    operators.MESH_OT_print3d_clean_distorted,
    # operators.MESH_OT_print3d_clean_thin,
    operators.MESH_OT_print3d_clean_non_manifold,
    operators.MESH_OT_print3d_select_report,
    operators.MESH_OT_print3d_scale_to_volume,
    operators.MESH_OT_print3d_scale_to_bounds,
    operators.MESH_OT_print3d_export,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.print_3d = PointerProperty(type=SceneProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.print_3d
