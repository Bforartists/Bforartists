# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Curve Tools",
    "description": "Adds some functionality for bezier/nurbs curve/surface modeling",
    "author": "Mackraken, Spivak Vladimir (cwolf3d)",
    "version": (0, 4, 6),
    "blender": (2, 80, 0),
    "location": "View3D > Tool Shelf > Edit Tab",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_curve/curve_tools.html",
    "category": "Add Curve",
}


import os, bpy, importlib, math
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        )
from bpy.props import (
        BoolProperty,
        IntProperty,
        FloatProperty,
        EnumProperty,
        CollectionProperty,
        StringProperty,
        FloatVectorProperty,
        )
from . import properties, operators, auto_loft, outline, remove_doubles
from . import path_finder, show_resolution, splines_sequence, fillet
from . import internal, cad, toolpath, exports

if 'bpy' in locals():
    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(auto_loft)
    importlib.reload(outline)
    importlib.reload(remove_doubles)
    importlib.reload(path_finder)
    importlib.reload(show_resolution)
    importlib.reload(splines_sequence)
    importlib.reload(fillet)
    importlib.reload(internal)
    importlib.reload(cad)
    importlib.reload(toolpath)
    importlib.reload(exports)

from bpy.types import (
        AddonPreferences,
        )


def UpdateDummy(object, context):
    scene = context.scene
    SINGLEDROP = scene.UTSingleDrop
    MOREDROP = scene.UTMOREDROP
    LOFTDROP = scene.UTLoftDrop
    ADVANCEDDROP = scene.UTAdvancedDrop
    EXTENDEDDROP = scene.UTExtendedDrop
    UTILSDROP = scene.UTUtilsDrop


class curvetoolsSettings(PropertyGroup):
    # selection
    SelectedObjects: CollectionProperty(
            type=properties.curvetoolsSelectedObject
            )
    NrSelectedObjects: IntProperty(
            name="NrSelectedObjects",
            default=0,
            description="Number of selected objects",
            update=UpdateDummy
            )
    # curve
    CurveLength: FloatProperty(
            name="CurveLength",
            default=0.0,
            precision=6
            )
    # splines
    SplineResolution: IntProperty(
            name="SplineResolution",
            default=64,
            min=2, max=1024,
            soft_min=2,
            description="Spline resolution will be set to this value"
            )
    SplineRemoveLength: FloatProperty(
            name="SplineRemoveLength",
            default=0.001,
            precision=6,
            description="Splines shorter than this threshold length will be removed"
            )
    SplineJoinDistance: FloatProperty(
            name="SplineJoinDistance",
            default=0.001,
            precision=6,
            description="Splines with starting/ending points closer to each other "
                        "than this threshold distance will be joined"
            )
    SplineJoinStartEnd: BoolProperty(
            name="SplineJoinStartEnd",
            default=False,
            description="Only join splines at the starting point of one and the ending point of the other"
            )
    splineJoinModeItems = (
            ('At_midpoint', 'At midpoint', 'Join splines at midpoint of neighbouring points'),
            ('Insert_segment', 'Insert segment', 'Insert segment between neighbouring points')
            )
    SplineJoinMode: EnumProperty(
            items=splineJoinModeItems,
            name="SplineJoinMode",
            default='At_midpoint',
            description="Determines how the splines will be joined"
            )
    # curve intersection
    LimitDistance: FloatProperty(
            name="LimitDistance",
            default=0.0001,
            precision=6,
            description="Displays the result of the curve length calculation"
            )

    intAlgorithmItems = (
            ('3D', '3D', 'Detect where curves intersect in 3D'),
            ('From_View', 'From View', 'Detect where curves intersect in the RegionView3D')
            )
    IntersectCurvesAlgorithm: EnumProperty(
            items=intAlgorithmItems,
            name="IntersectCurvesAlgorithm",
            description="Determines how the intersection points will be detected",
            default='3D'
            )
    intModeItems = (
            ('Insert', 'Insert', 'Insert points into the existing spline(s)'),
            ('Split', 'Split', 'Split the existing spline(s) into 2'),
            ('Empty', 'Empty', 'Add empty at intersections')
            )
    IntersectCurvesMode: EnumProperty(
            items=intModeItems,
            name="IntersectCurvesMode",
            description="Determines what happens at the intersection points",
            default='Split'
            )
    intAffectItems = (
            ('Both', 'Both', 'Insert points into both curves'),
            ('Active', 'Active', 'Insert points into active curve only'),
            ('Other', 'Other', 'Insert points into other curve only')
            )
    IntersectCurvesAffect: EnumProperty(
            items=intAffectItems,
            name="IntersectCurvesAffect",
            description="Determines which of the selected curves will be affected by the operation",
            default='Both'
            )
    PathFinderRadius: FloatProperty(
            name="PathFinder detection radius",
            default=0.2,
            precision=6,
            description="PathFinder detection radius"
            )
    curve_vertcolor: FloatVectorProperty(
            name="OUT",
            default=(0.2, 0.9, 0.9, 1),
            size=4,
            subtype="COLOR",
            min=0,
            max=1
            )
    path_color: FloatVectorProperty(
            name="OUT",
            default=(0.2, 0.9, 0.9, 0.1),
            size=4,
            subtype="COLOR",
            min=0,
            max=1
            )
    path_thickness: IntProperty(
            name="Path thickness",
            default=10,
            min=1, max=1024,
            soft_min=2,
            description="Path thickness (px)"
            )
    sequence_color: FloatVectorProperty(
            name="OUT",
            default=(0.2, 0.9, 0.9, 1),
            size=4,
            subtype="COLOR",
            min=0,
            max=1
            )
    font_thickness: IntProperty(
            name="Font thickness",
            default=2,
            min=1, max=1024,
            soft_min=2,
            description="Font thickness (px)"
            )
    font_size: FloatProperty(
            name="Font size",
            default=0.1,
            precision=3,
            description="Font size"
            )


# Curve Info
class VIEW3D_PT_curve_tools_info(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_label = "Curve Info"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curvetools.operatorcurveinfo", text="Curve")
        row = col.row(align=True)
        row.operator("curvetools.operatorsplinesinfo", text="Spline")
        row.operator("curvetools.operatorsegmentsinfo", text="Segment")
        row = col.row(align=True)
        row.operator("curvetools.operatorcurvelength", icon = "DRIVER_DISTANCE", text="Length")
        row.prop(context.scene.curvetools, "CurveLength", text="")

# Curve Edit
class VIEW3D_PT_curve_tools_edit(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_label = "Curve Edit"


    def draw(self, context):
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curvetools.bezier_points_fillet", text='Fillet/Chamfer')
        row = col.row(align=True)
        row.operator("curvetools.outline", text="Outline")
        row.operator("curvetools.add_toolpath_offset_curve", text="Recursive Offset")
        col.operator("curvetools.sep_outline", text="Separate Offset/Selected")
        col.operator("curvetools.bezier_cad_handle_projection", text='Extend Handles')
        col.operator("curvetools.bezier_cad_boolean", text="Boolean Splines")
        row = col.row(align=True)
        row.operator("curvetools.bezier_spline_divide", text='Subdivide')
        row.operator("curvetools.bezier_cad_subdivide", text="Multi Subdivide")

        col.operator("curvetools.split", text='Split at Vertex')
        col.operator("curvetools.add_toolpath_discretize_curve", text="Discretize Curve")
        col.operator("curvetools.bezier_cad_array", text="Array Splines")

# Curve Intersect
class VIEW3D_PT_curve_tools_intersect(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_label = "Intersect"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curvetools.bezier_curve_boolean", text="2D Curve Boolean")
        col.operator("curvetools.operatorintersectcurves", text="Intersect Curves")
        col.prop(context.scene.curvetools, "LimitDistance", text="Limit Distance")
        col.prop(context.scene.curvetools, "IntersectCurvesAlgorithm", text="Algorithm")
        col.prop(context.scene.curvetools, "IntersectCurvesMode", text="Mode")
        col.prop(context.scene.curvetools, "IntersectCurvesAffect", text="Affect")

# Curve Surfaces
class VIEW3D_PT_curve_tools_surfaces(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_label = "Surfaces"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        wm = context.window_manager
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curvetools.operatorbirail", text="Birail")
        col.operator("curvetools.convert_bezier_to_surface", text="Convert Bezier to Surface")
        col.operator("curvetools.convert_selected_face_to_bezier", text="Convert Faces to Bezier")

# Curve Path Finder
class VIEW3D_PT_curve_tools_loft(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_parent_id = "VIEW3D_PT_curve_tools_surfaces"
    bl_label = "Loft"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        wm = context.window_manager
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curvetools.create_auto_loft")
        lofters = [o for o in scene.objects if "autoloft" in o.keys()]
        for o in lofters:
            col.label(text=o.name)
        # layout.prop(o, '["autoloft"]', toggle=True)
        col.prop(wm, "auto_loft", toggle=True)
        col.operator("curvetools.update_auto_loft_curves")
        col = layout.column(align=True)


# Curve Sanitize
class VIEW3D_PT_curve_tools_sanitize(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_label = "Sanitize"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curvetools.operatororigintospline0start", icon = "OBJECT_ORIGIN", text="Set Origin to Spline Start")
        col.operator("curvetools.scale_reset", text='Reset Scale')

        col.label(text="Cleanup:")
        col.operator("curvetools.remove_doubles", icon = "TRASH", text='Remove Doubles')
        col.operator("curvetools.operatorsplinesremovezerosegment", icon = "TRASH", text="0-Segment Splines")
        row = col.row(align=True)
        row.operator("curvetools.operatorsplinesremoveshort", text="Short Splines")
        row.prop(context.scene.curvetools, "SplineRemoveLength", text="Threshold remove")

        col.label(text="Join Splines:")
        col.operator("curvetools.operatorsplinesjoinneighbouring", text="Join Neighbouring Splines")
        row = col.row(align=True)
        col.prop(context.scene.curvetools, "SplineJoinDistance", text="Threshold")
        col.prop(context.scene.curvetools, "SplineJoinStartEnd", text="Only at Ends")
        col.prop(context.scene.curvetools, "SplineJoinMode", text="Join Position")

# Curve Utilities
class VIEW3D_PT_curve_tools_utilities(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_label = "Utilities"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        row = col.row(align=True)
        row.label(text="Curve Resolution:")
        row = col.row(align=True)
        row.operator("curvetools.show_resolution", icon="HIDE_OFF", text="Show [ESC]")
        row.prop(context.scene.curvetools, "curve_vertcolor", text="")
        row = col.row(align=True)
        row.operator("curvetools.operatorsplinessetresolution", text="Set Resolution")
        row.prop(context.scene.curvetools, "SplineResolution", text="")


        row = col.row(align=True)
        row.label(text="Spline Order:")
        row = col.row(align=True)
        row.operator("curvetools.show_splines_sequence", icon="HIDE_OFF", text="Show [ESC]")
        row.prop(context.scene.curvetools, "sequence_color", text="")
        row = col.row(align=True)
        row.prop(context.scene.curvetools, "font_size", text="Font Size")
        row.prop(context.scene.curvetools, "font_thickness", text="Font Thickness")
        row = col.row(align=True)
        oper = row.operator("curvetools.rearrange_spline", text = "<")
        oper.command = 'PREV'
        oper = row.operator("curvetools.rearrange_spline", text = ">")
        oper.command = 'NEXT'
        row = col.row(align=True)
        row.operator("curve.switch_direction", text="Switch Direction")
        row = col.row(align=True)
        row.operator("curvetools.set_first_points", text="Set First Points")

# Curve Path Finder
class VIEW3D_PT_curve_tools_pathfinder(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Curve Edit"
    bl_parent_id = "VIEW3D_PT_curve_tools_utilities"
    bl_label = "Path Finder"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        col = layout.column(align=True)
        col.operator("curvetools.pathfinder", text="Path Finder [ESC]")
        col.prop(context.scene.curvetools, "PathFinderRadius", text="PathFinder Radius")
        col.prop(context.scene.curvetools, "path_color", text="")
        col.prop(context.scene.curvetools, "path_thickness", text="Thickness")

        col = layout.column(align=True)
        col.label(text="ESC or TAB - Exit PathFinder")
        col.label(text="X or DEL - Delete")
        col.label(text="Alt + Mouse Click - Select Spline")
        col.label(text="Alt + Shift + Mouse click - Add Spline to Selection")
        col.label(text="A - Deselect All")

# Add-ons Preferences Update Panel

# Define Panel classes for updating
panels = (
        VIEW3D_PT_curve_tools_info, VIEW3D_PT_curve_tools_edit,
        VIEW3D_PT_curve_tools_intersect, VIEW3D_PT_curve_tools_surfaces,
        VIEW3D_PT_curve_tools_loft, VIEW3D_PT_curve_tools_sanitize,
        VIEW3D_PT_curve_tools_utilities, VIEW3D_PT_curve_tools_pathfinder
        )


def update_panel(self, context):
    message = "Curve Tools: Updating Panel locations has failed"
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[__name__].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))
        pass


class CurveAddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    bl_idname = __name__

    category: StringProperty(
            name="Tab Category",
            description="Choose a name for the category of the panel",
            default="Edit",
            update=update_panel
            )

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        col = row.column()
        col.label(text="Tab Category:")
        col.prop(self, "category", text="")

# Context MENU
def curve_tools_context_menu(self, context):
    bl_label = 'Curve tools'

    self.layout.operator("curvetools.bezier_points_fillet", text="Fillet")
    self.layout.operator("curvetools.bezier_cad_handle_projection", text='Handle Projection')
    self.layout.operator("curvetools.bezier_spline_divide", text="Divide")
    self.layout.operator("curvetools.add_toolpath_offset_curve", text="Offset Curve")
    self.layout.operator("curvetools.remove_doubles", text='Remove Doubles')
    self.layout.separator()

def curve_tools_object_context_menu(self, context):
    bl_label = 'Curve tools'

    if context.active_object.type == "CURVE":
        self.layout.operator("curvetools.scale_reset", text="Scale Reset")
        self.layout.operator("curvetools.add_toolpath_offset_curve", text="Offset Curve")
        self.layout.operator("curvetools.remove_doubles", text='Remove Doubles')
        self.layout.separator()

# Import-export 2d svg
def menu_file_export(self, context):
    for operator in exports.operators:
        self.layout.operator(operator.bl_idname)

def menu_file_import(self, context):
    for operator in imports.operators:
        self.layout.operator(operator.bl_idname)

# REGISTER
classes = cad.operators + \
        toolpath.operators + \
        exports.operators + \
        operators.operators + \
        properties.operators + \
        path_finder.operators + \
        show_resolution.operators + \
        splines_sequence.operators + \
        outline.operators + \
        fillet.operators + \
        remove_doubles.operators + \
        [
            CurveAddonPreferences,
            curvetoolsSettings,
        ]

def register():
    bpy.types.Scene.UTSingleDrop = BoolProperty(
            name="One Curve",
            default=False,
            description="One Curve"
            )
    bpy.types.Scene.UTMOREDROP = BoolProperty(
            name="Curves",
            default=False,
            description="Curves"
            )
    bpy.types.Scene.UTLoftDrop = BoolProperty(
            name="Two Curves Loft",
            default=False,
            description="Two Curves Loft"
            )
    bpy.types.Scene.UTAdvancedDrop = BoolProperty(
            name="Advanced",
            default=True,
            description="Advanced"
            )
    bpy.types.Scene.UTExtendedDrop = BoolProperty(
            name="Extended",
            default=False,
            description="Extended"
            )
    bpy.types.Scene.UTUtilsDrop = BoolProperty(
            name="Curves Utils",
            default=True,
            description="Curves Utils"
            )

    for cls in classes:
        bpy.utils.register_class(cls)

    for panel in panels:
        bpy.utils.register_class(panel)

    auto_loft.register()

    bpy.types.TOPBAR_MT_file_export.append(menu_file_export)

    bpy.types.Scene.curvetools = bpy.props.PointerProperty(type=curvetoolsSettings)

    update_panel(None, bpy.context)

    bpy.types.VIEW3D_MT_edit_curve_context_menu.prepend(curve_tools_context_menu)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(curve_tools_object_context_menu)


def unregister():
    del bpy.types.Scene.UTSingleDrop
    del bpy.types.Scene.UTMOREDROP
    del bpy.types.Scene.UTLoftDrop
    del bpy.types.Scene.UTAdvancedDrop
    del bpy.types.Scene.UTExtendedDrop
    del bpy.types.Scene.UTUtilsDrop

    auto_loft.unregister()

    bpy.types.TOPBAR_MT_file_export.remove(menu_file_export)

    bpy.types.VIEW3D_MT_edit_curve_context_menu.remove(curve_tools_context_menu)
    bpy.types.VIEW3D_MT_object_context_menu.remove(curve_tools_object_context_menu)

    for panel in panels:
        bpy.utils.unregister_class(panel)

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
