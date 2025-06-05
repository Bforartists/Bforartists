# SPDX-FileCopyrightText: 2019-2022 Alan Odom (Clockmender)
# SPDX-FileCopyrightText: 2019-2022 Rune Morling (ermo)
#
# SPDX-License-Identifier: GPL-2.0-or-later

# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
#
bl_info = {
    "name": "Precision Drawing Tools (PDT)",
    "author": "Alan Odom (Clockmender), Rune Morling (ermo)",
    "version": (1, 5, 3),
    "blender": (3, 0, 0),
    "location": "View3D > UI > PDT",
    "description": "Precision Drawing Tools for Accurate Modelling",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/3d_view/precision_drawing_tools/index.html",
    "category": "3D View",
}


# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
    import importlib

    importlib.reload(pdt_design)
    importlib.reload(pdt_pivot_point)
    importlib.reload(pdt_menus)
    importlib.reload(pdt_library)
    importlib.reload(pdt_view)
    importlib.reload(pdt_xall)
    importlib.reload(pdt_bix)
    importlib.reload(pdt_etof)
    importlib.reload(pdt_tangent)
    importlib.reload(pdt_trig_waves)
else:
    from . import pdt_design
    from . import pdt_pivot_point
    from . import pdt_menus
    from . import pdt_library
    from . import pdt_view
    from . import pdt_xall
    from . import pdt_bix
    from . import pdt_etof
    from . import pdt_tangent
    from . import pdt_trig_waves

import bpy
import os
from pathlib import Path
from bpy.types import (
    AddonPreferences,
    PropertyGroup, Scene,
    WindowManager,
    Object,
)
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from .pdt_msg_strings import (
    PDT_DES_COORDS,
    PDT_DES_FILLETPROF,
    PDT_DES_FILLETRAD,
    PDT_DES_FILLETSEG,
    PDT_DES_FILLETVERTS,
    PDT_DES_FILLINT,
    PDT_DES_FLIPANG,
    PDT_DES_FLIPPER,
    PDT_DES_LIBCOLS,
    PDT_DES_LIBMATS,
    PDT_DES_LIBMODE,
    PDT_DES_LIBOBS,
    PDT_DES_LIBSER,
    PDT_DES_MOVESEL,
    PDT_DES_OBORDER,
    PDT_DES_OFFANG,
    PDT_DES_OFFDIS,
    PDT_DES_OFFPER,
    PDT_DES_OPMODE,
    PDT_DES_OUTPUT,
    PDT_DES_PIVOTDIS,
    PDT_DES_PPLOC,
    PDT_DES_PPSCALEFAC,
    PDT_DES_PPSIZE,
    PDT_DES_PPTRANS,
    PDT_DES_PPWIDTH,
    PDT_DES_ROTMOVAX,
    PDT_DES_TRIM,
    PDT_DES_VALIDLET,
    PDT_DES_WORPLANE,
    PDT_DES_TANCEN1,
    PDT_DES_TANCEN2,
    PDT_DES_TANCEN3,
    PDT_DES_RADIUS1,
    PDT_DES_RADIUS2,
    PDT_DES_TPOINT,
    PDT_DES_EXPCOLL,
    PDT_DES_TANMODE,
)
from .pdt_command import command_run
from .pdt_functions import scale_set


# Declare enum items variables
#
_pdt_obj_items = []
_pdt_col_items = []
_pdt_mat_items = []


class PDTPreferences(AddonPreferences):
    # This must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.

    bl_idname = __name__

    debug: BoolProperty(
        name="Enable console debug output from PDT scripts",
        default=False,
        description="NOTE: Does not enable debugging globally in Blender (only in PDT scripts)",
    )

    pdt_ui_width: IntProperty(
        name="UI Width Cut-off",
        default=350,
        description="Cutoff width for shrinking items per line in menus",
    )

    pdt_input_round: IntProperty(
        name="Input Rounding", default=5, description="Rounding Factor for Inputs"
    )

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        row1 = box.row()
        row2 = box.row()
        row1.prop(self, "debug")
        row2.prop(self, "pdt_ui_width")
        row2.prop(self, "pdt_input_round")


def enumlist_objects(self, context):
    """Populate Objects List from Parts Library.

    Creates list of objects that optionally have search string contained in them
    to populate variable pdt_lib_objects enumerator.

    Args:
        context: Blender bpy.context instance.

    Returns:
        list of Object Names.
    """

    scene = context.scene
    pg = scene.pdt_pg
    file_path = pg.pdt_library_path
    path = Path(bpy.path.abspath(file_path))
    _pdt_obj_items.clear()

    if path.is_file() and ".blend" in str(path):
        with bpy.data.libraries.load(str(path)) as (data_from, _):
            if len(pg.object_search_string) == 0:
                object_names = [obj for obj in data_from.objects]
            else:
                object_names = [obj for obj in data_from.objects if pg.object_search_string in obj]
        for object_name in object_names:
            _pdt_obj_items.append((object_name, object_name, ""))
    else:
        _pdt_obj_items.append(("MISSING", "Library Not Set", ""))
    return _pdt_obj_items


def enumlist_collections(self, context):
    """Populate Collections List from Parts Library.

    Creates list of collections that optionally have search string contained in them
    to populate variable pg.lib_collections enumerator

    Args:
        context: Blender bpy.context instance.

    Returns:
        list of Collections Names.
    """

    scene = context.scene
    pg = scene.pdt_pg
    file_path = pg.pdt_library_path
    path = Path(bpy.path.abspath(file_path))
    _pdt_col_items.clear()

    if path.is_file() and ".blend" in str(path):
        with bpy.data.libraries.load(str(path)) as (data_from, _):
            if len(pg.collection_search_string) == 0:
                object_names = [obj for obj in data_from.collections]
            else:
                object_names = [
                    obj for obj in data_from.collections if pg.collection_search_string in obj
                ]
        for object_name in object_names:
            _pdt_col_items.append((object_name, object_name, ""))
    else:
        _pdt_col_items.append(("MISSING", "Library Not Set", ""))
    return _pdt_col_items


def enumlist_materials(self, context):
    """Populate Materials List from Parts Library.

    Creates list of materials that optionally have search string contained in them
    to populate variable pg.lib_materials enumerator.

    Args:
        context: Blender bpy.context instance.

    Returns:
        list of Object Names.
    """

    scene = context.scene
    pg = scene.pdt_pg
    file_path = pg.pdt_library_path
    path = Path(bpy.path.abspath(file_path))
    _pdt_mat_items.clear()

    if path.is_file() and ".blend" in str(path):
        with bpy.data.libraries.load(str(path)) as (data_from, _):
            if len(pg.material_search_string) == 0:
                object_names = [obj for obj in data_from.materials]
            else:
                object_names = [
                    obj for obj in data_from.materials if pg.material_search_string in obj
                ]
        for object_name in object_names:
            _pdt_mat_items.append((object_name, object_name, ""))
    else:
        _pdt_mat_items.append(("MISSING", "Library Not Set", ""))
    return _pdt_mat_items


class PDTSceneProperties(PropertyGroup):
    """Contains all PDT related properties."""

    pdt_library_path: StringProperty(
        name="Library",
        default="",
        description="Parts Library File",
        maxlen=1024,
        subtype="FILE_PATH",
    )

    object_search_string: StringProperty(name="Search", default="", description=PDT_DES_LIBSER)
    collection_search_string: StringProperty(name="Search", default="", description=PDT_DES_LIBSER)
    material_search_string: StringProperty(name="Search", default="", description=PDT_DES_LIBSER)

    cartesian_coords: FloatVectorProperty(
        name="Coords", default=(0.0, 0.0, 0.0), subtype="XYZ", description=PDT_DES_COORDS
    )
    distance: FloatProperty(
        name="Distance", default=0.0, precision=5, description=PDT_DES_OFFDIS, unit="LENGTH"
    )
    angle: FloatProperty(
        name="Angle", min=-180, max=180, default=0.0, precision=5, description=PDT_DES_OFFANG
    )
    percent: FloatProperty(name="Percent", default=0.0, precision=5, description=PDT_DES_OFFPER)
    plane: EnumProperty(
        items=(
            ("XZ", "Front(X-Z)", "Use X-Z Plane"),
            ("XY", "Top(X-Y)", "Use X-Y Plane"),
            ("YZ", "Right(Y-Z)", "Use Y-Z Plane"),
            ("LO", "View", "Use View Plane"),
        ),
        name="Working Plane",
        default="XZ",
        description=PDT_DES_WORPLANE,
    )
    select: EnumProperty(
        items=(
            ("REL", "Current Pos.", "Move Relative to Current Position"),
            (
                "SEL",
                "Selected Entities",
                "Move Relative to Selected Object or Vertex (Cursor & Pivot Only)",
            ),
        ),
        name="Move Mode",
        default="SEL",
        description=PDT_DES_MOVESEL,
    )
    operation: EnumProperty(
        items=(
            ("CU", "Move Cursor", "This function will Move the Cursor"),
            ("PP", "Move Pivot Point", "This function will Move the Pivot Point"),
            ("MV", "Move Entities", "This function will Move selected Vertices or Objects"),
            ("NV", "Add New Vertex", "This function will Add a New Vertex"),
            (
                "EV",
                "Extrude Vertex/Vertices",
                "This function will Extrude Vertex/Vertices Only in EDIT Mode",
            ),
            ("SE", "Split Edges", "This function will Split Edges Only in EDIT Mode"),
            (
                "DG",
                "Duplicate Geometry",
                "This function will Duplicate Geometry in EDIT Mode (Delta & Direction Only)",
            ),
            (
                "EG",
                "Extrude Geometry",
                "This function will Extrude Geometry in EDIT Mode (Delta & Direction Only)",
            ),
        ),
        name="Operation",
        default="CU",
        description=PDT_DES_OPMODE,
    )
    taper: EnumProperty(
        items=(
            ("RX-MY", "RotX-MovY", "Rotate X - Move Y"),
            ("RX-MZ", "RotX-MovZ", "Rotate X - Move Z"),
            ("RY-MX", "RotY-MovX", "Rotate Y - Move X"),
            ("RY-MZ", "RotY-MovZ", "Rotate Y - Move Z"),
            ("RZ-MX", "RotZ-MovX", "Rotate Z - Move X"),
            ("RZ-MY", "RotZ-MovY", "Rotate Z - Move Y"),
        ),
        name="Axes",
        default="RX-MY",
        description=PDT_DES_ROTMOVAX,
    )

    flip_angle: BoolProperty(name="Flip Angle", default=False, description=PDT_DES_FLIPANG)
    flip_percent: BoolProperty(name="Flip %", default=False, description=PDT_DES_FLIPPER)

    extend: BoolProperty(name="Trim/Extend All", default=False, description=PDT_DES_TRIM)

    lib_objects: EnumProperty(items=enumlist_objects, name="Objects", description=PDT_DES_LIBOBS)
    lib_collections: EnumProperty(
        items=enumlist_collections, name="Collections", description=PDT_DES_LIBCOLS
    )
    lib_materials: EnumProperty(
        items=enumlist_materials, name="Materials", description=PDT_DES_LIBMATS
    )
    lib_mode: EnumProperty(
        items=(
            ("OBJECTS", "Objects", "Use Objects"),
            ("COLLECTIONS", "Collections", "Use Collections"),
            ("MATERIALS", "Materials", "Use Materials"),
        ),
        name="Mode",
        default="OBJECTS",
        description=PDT_DES_LIBMODE,
    )

    rotation_coords: FloatVectorProperty(
        name="Rotation", default=(0.0, 0.0, 0.0), subtype="XYZ", description="Rotation Coordinates"
    )

    object_order: EnumProperty(
        items=(
            ("1,2,3,4", "1,2,3,4", "Objects 1 & 2 are First Line"),
            ("1,3,2,4", "1,3,2,4", "Objects 1 & 3 are First Line"),
            ("1,4,2,3", "1,4,2,3", "Objects 1 & 4 are First Line"),
        ),
        name="Order",
        default="1,2,3,4",
        description=PDT_DES_OBORDER,
    )
    vrotangle: FloatProperty(name="View Rotate Angle", default=10, max=180, min=-180)
    command: StringProperty(
        name="Command", default="CA0,0,0", update=command_run, description=PDT_DES_VALIDLET,
    )
    maths_output: FloatProperty(
        name="Maths output", default=0, description=PDT_DES_OUTPUT,
    )
    error: StringProperty(name="Error", default="")

    # Was pivot* -- is now pivot_*
    pivot_loc: FloatVectorProperty(
        name="Pivot Location", default=(0.0, 0.0, 0.0), subtype="XYZ", description=PDT_DES_PPLOC,
    )
    pivot_scale: FloatVectorProperty(
        name="Pivot Scale", default=(1.0, 1.0, 1.0), subtype="XYZ", description=PDT_DES_PPSCALEFAC
    )
    pivot_size: FloatProperty(
        name="Pivot Factor", min=0.4, max=10, default=2, precision=1, description=PDT_DES_PPSIZE
    )
    pivot_width: IntProperty(name="Width", min=1, max=5, default=2, description=PDT_DES_PPWIDTH)

    pivot_ang: FloatProperty(name="Pivot Angle", min=-180, max=180, default=0.0)

    pivot_dis: FloatProperty(
        name="Pivot Dist", default=0.0, min=0, update=scale_set, description=PDT_DES_PIVOTDIS,
    )
    pivot_alpha: FloatProperty(
        name="Alpha", min=0.2, max=1, default=0.6, precision=1, description=PDT_DES_PPTRANS,
    )
    pivot_show: BoolProperty()

    # Was filletrad
    fillet_radius: FloatProperty(
        name="Fillet Radius", min=0.0, default=1.0, unit="LENGTH", description=PDT_DES_FILLETRAD
    )
    # Was filletnum
    fillet_segments: IntProperty(
        name="Fillet Segments", min=1, default=4, description=PDT_DES_FILLETSEG
    )
    # Was filletpro
    fillet_profile: FloatProperty(
        name="Fillet Profile", min=0.0, max=1.0, default=0.5, description=PDT_DES_FILLETPROF
    )
    # Was filletbool
    fillet_vertices_only: BoolProperty(
        name="Fillet Vertices Only", default=True, description=PDT_DES_FILLETVERTS,
    )
    fillet_intersect: BoolProperty(
        name="Intersect", default=False, description=PDT_DES_FILLINT,
    )
    tangent_point0: FloatVectorProperty(
        name="Coordst1", default=(0.0, 0.0, 0.0), subtype="XYZ", description=PDT_DES_TANCEN1
    )
    tangent_point1: FloatVectorProperty(
        name="Coordst2", default=(0.0, 0.0, 0.0), subtype="XYZ", description=PDT_DES_TANCEN2
    )
    tangent_radius0: FloatProperty(
        name="Arc Radius 1", min=0.00001,  default=1, unit="LENGTH", description=PDT_DES_RADIUS1
    )
    tangent_radius1: FloatProperty(
        name="Arc Radius 2", min=0.00001, default=1, unit="LENGTH", description=PDT_DES_RADIUS2
    )
    tangent_point2: FloatVectorProperty(
        name="Coordst3", default=(0.0, 0.0, 0.0), subtype="XYZ", description=PDT_DES_TANCEN3
    )
    menu_expand: BoolProperty(
        name="Expand", default=False, description=PDT_DES_EXPCOLL,
    )
    tangent_mode: EnumProperty(
        items=(
            ("inner", "Inner", "Inner Tangents"),
            ("outer", "Outer", "Outer Tangents"),
            ("both", "Inner & Outer", "Inner & Outer Tangents"),
            ("point", "From Point", "Tangents from Point"),
        ),
        name="Working Plane",
        default="both",
        description=PDT_DES_TANMODE,
    )

    # For Trig Waves
    trig_type : EnumProperty(
        items=(
            ("sin", "Sine", "Sine Wave"),
            ("cos", "Cosine", "Cosine Wave"),
            ("tan", "Tangent", "Tangent Wave"),
        ),
        name="Wave Form",
        default="sin",
        description="Trig. Wave Form",
    )
    trig_cycles : IntProperty(name="Cycles #", default=1, min=1,
        description="1 Cycle = 180 Degrees")
    trig_amp : FloatProperty(name="Amplitude", default=1, min=0.01,
        description="Maximum Height of 1 Cycle (forms Basis for Tangents)")
    trig_len : FloatProperty(name="Cycle Length", default=2, min=0.02,
        description="Length in Blender Units of 1 Cycle")
    trig_obj : PointerProperty(name="Object", type=Object)
    trig_del : BoolProperty(name="Empty Object", default=False,
        description="Delete ALL Vertices in Object First")
    trig_res : IntProperty(name="Resolution", default=18, min=4, max=72,
        description="Number of Vertices per Cycle (180 Degrees)")
    trig_tanmax : FloatProperty(name="Tangent Max", default=10, min=0.1,
        description="Maximum Permitted Tangent Value")
    trig_off : FloatVectorProperty(name="Start Location", default=(0,0,0),
        description="Location in World Space for Origin of Wave")
    trig_abs : BoolProperty(name="Absolute", default=False,
        description="Use Absolute Values Only")


# List of All Classes in the Add-on to register
#
# Due to the way PropertyGroups work, this needs to be listed/loaded first
# (and unloaded last)
#
classes = (
    PDTPreferences,
    PDTSceneProperties,
    pdt_bix.PDT_OT_LineOnBisection,
    pdt_command.PDT_OT_CommandReRun,
    pdt_design.PDT_OT_PlacementAbs,
    pdt_design.PDT_OT_PlacementDelta,
    pdt_design.PDT_OT_PlacementDis,
    pdt_design.PDT_OT_PlacementView,
    pdt_design.PDT_OT_PlacementCen,
    pdt_design.PDT_OT_PlacementPer,
    pdt_design.PDT_OT_PlacementNormal,
    pdt_design.PDT_OT_PlacementInt,
    pdt_design.PDT_OT_JoinVerts,
    pdt_design.PDT_OT_Angle2,
    pdt_design.PDT_OT_Angle3,
    pdt_design.PDT_OT_Origin,
    pdt_design.PDT_OT_Taper,
    pdt_design.PDT_OT_Fillet,
    pdt_etof.PDT_OT_EdgeToFace,
    pdt_library.PDT_OT_Append,
    pdt_library.PDT_OT_Link,
    pdt_library.PDT_OT_LibShow,
    pdt_menus.PDT_PT_PanelDesign,
    pdt_menus.PDT_PT_PanelTools,
    pdt_menus.PDT_PT_PanelTangent,
    pdt_menus.PDT_PT_PanelCommandLine,
    pdt_menus.PDT_PT_PanelViewControl,
    pdt_menus.PDT_PT_PanelPivotPoint,
    pdt_menus.PDT_PT_PanelPartsLibrary,
    pdt_menus.PDT_PT_PanelTrig,
    pdt_pivot_point.PDT_OT_ModalDrawOperator,
    pdt_pivot_point.PDT_OT_ViewPlaneRotate,
    pdt_pivot_point.PDT_OT_ViewPlaneScale,
    pdt_pivot_point.PDT_OT_PivotToCursor,
    pdt_pivot_point.PDT_OT_CursorToPivot,
    pdt_pivot_point.PDT_OT_PivotSelected,
    pdt_pivot_point.PDT_OT_PivotOrigin,
    pdt_pivot_point.PDT_OT_PivotWrite,
    pdt_pivot_point.PDT_OT_PivotRead,
    pdt_tangent.PDT_OT_TangentOperate,
    pdt_tangent.PDT_OT_TangentOperateSel,
    pdt_tangent.PDT_OT_TangentSet1,
    pdt_tangent.PDT_OT_TangentSet2,
    pdt_tangent.PDT_OT_TangentSet3,
    pdt_tangent.PDT_OT_TangentSet4,
    pdt_tangent.PDT_OT_TangentExpandMenu,
    pdt_trig_waves.PDT_OT_WaveGenerator,
    pdt_view.PDT_OT_ViewRot,
    pdt_view.PDT_OT_ViewRotL,
    pdt_view.PDT_OT_ViewRotR,
    pdt_view.PDT_OT_ViewRotU,
    pdt_view.PDT_OT_ViewRotD,
    pdt_view.PDT_OT_ViewRoll,
    pdt_view.PDT_OT_ViewIso,
    pdt_view.PDT_OT_Reset3DView,
    pdt_xall.PDT_OT_IntersectAllEdges,
)


def register():
    """Register Classes and Create Scene Variables.

    Operates on the classes list defined above.
    """

    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    # OpenGL flag
    #
    window_manager = WindowManager
    # Register Internal OpenGL Property
    #
    window_manager.pdt_run_opengl = BoolProperty(default=False)

    Scene.pdt_pg = PointerProperty(type=PDTSceneProperties)


def unregister():
    """Unregister Classes and Delete Scene Variables.

    Operates on the classes list defined above.
    """

    from bpy.utils import unregister_class

    # remove OpenGL data
    pdt_pivot_point.PDT_OT_ModalDrawOperator.handle_remove(
        pdt_pivot_point.PDT_OT_ModalDrawOperator, bpy.context
    )
    window_manager = bpy.context.window_manager
    pdt_wm = "pdt_run_opengl"
    if pdt_wm in window_manager:
        del window_manager[pdt_wm]

    for cls in reversed(classes):
        unregister_class(cls)

    del Scene.pdt_pg


if __name__ == "__main__":
    register()
