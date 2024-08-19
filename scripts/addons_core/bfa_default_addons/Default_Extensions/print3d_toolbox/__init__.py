# SPDX-License-Identifier: GPL-2.0-or-later
# SPDX-FileCopyrightText: 2013-2024 Campbell Barton
# SPDX-FileContributor: Mikhail Rachinskiy


if "bpy" in locals():
    import importlib
    importlib.reload(report)
    if "export" in locals():
        importlib.reload(export)
    if "lib" in locals():
        importlib.reload(lib)
    importlib.reload(operators.analyze)
    importlib.reload(operators.cleanup)
    importlib.reload(operators.edit)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    import math

    import bpy
    from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty, StringProperty
    from bpy.types import PropertyGroup

    from . import operators, report, ui


class SceneProperties(PropertyGroup):

    # Analyze
    # -------------------------------------

    threshold_zero: FloatProperty(
        name="Threshold",
        description="Limit for checking zero area/length",
        default=0.0001,
        min=0.0,
        max=0.2,
        precision=5,
        step=0.01
    )
    angle_distort: FloatProperty(
        name="Angle",
        description="Limit for checking distorted faces",
        subtype="ANGLE",
        default=math.radians(45.0),
        min=0.0,
        max=math.radians(180.0),
        step=100,
    )
    thickness_min: FloatProperty(
        name="Thickness",
        description="Minimum thickness",
        subtype="DISTANCE",
        default=0.001,  # 1mm
        min=0.0,
        max=10.0,
        precision=3,
        step=0.1
    )
    angle_sharp: FloatProperty(
        name="Angle",
        subtype="ANGLE",
        default=math.radians(160.0),
        min=0.0,
        max=math.radians(180.0),
        step=100,
    )
    angle_overhang: FloatProperty(
        name="Angle",
        subtype="ANGLE",
        default=math.radians(45.0),
        min=0.0,
        max=math.radians(90.0),
        step=100,
    )

    # Export
    # -------------------------------------

    export_path: StringProperty(
        name="Export Directory",
        description="Path to directory where the files are created",
        default="//",
        maxlen=1024,
        subtype="DIR_PATH",
    )
    export_format: EnumProperty(
        name="Format",
        description="Export file format",
        items=(
            ("OBJ", "OBJ", ""),
            ("PLY", "PLY", ""),
            ("STL", "STL", ""),
        ),
        default="STL",
    )
    use_ascii_format: BoolProperty(
        name="ASCII",
        description="Export file in ASCII format, export as binary otherwise",
    )
    use_scene_scale: BoolProperty(
        name="Scene Scale",
        description="Apply scene scale setting on export",
    )
    use_copy_textures: BoolProperty(
        name="Copy Textures",
        description="Copy textures on export to the output path",
    )
    use_uv: BoolProperty(name="UVs")
    use_normals: BoolProperty(
        name="Normals",
        description="Export specific vertex normals if available, export calculated normals otherwise"
    )
    use_colors: BoolProperty(
        name="Colors",
        description="Export vertex color attributes"
    )


classes = (
    SceneProperties,

    ui.VIEW3D_PT_print3d_analyze,
    ui.VIEW3D_PT_print3d_cleanup,
    ui.VIEW3D_PT_print3d_edit,
    ui.VIEW3D_PT_print3d_export,
    ui.VIEW3D_PT_print3d_export_options,

    operators.analyze.MESH_OT_info_volume,
    operators.analyze.MESH_OT_info_area,
    operators.analyze.MESH_OT_check_degenerate,
    operators.analyze.MESH_OT_check_distorted,
    operators.analyze.MESH_OT_check_solid,
    operators.analyze.MESH_OT_check_intersections,
    operators.analyze.MESH_OT_check_thick,
    operators.analyze.MESH_OT_check_sharp,
    operators.analyze.MESH_OT_check_overhang,
    operators.analyze.MESH_OT_check_all,
    operators.analyze.MESH_OT_report_select,
    operators.analyze.WM_OT_report_clear,
    operators.cleanup.MESH_OT_clean_distorted,
    operators.cleanup.MESH_OT_clean_non_manifold,
    operators.edit.MESH_OT_hollow,
    operators.edit.OBJECT_OT_align_xy,
    operators.edit.MESH_OT_scale_to_volume,
    operators.edit.MESH_OT_scale_to_bounds,
    operators.IO_OT_export,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.print_3d = PointerProperty(type=SceneProperties)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.print_3d
