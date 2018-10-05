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

# For now group all tools together
# we may want to move these into per space-type files.
#
# For now keep this in a single file since it's an area that may change,
# so avoid making changes all over the place.

import bpy
from bpy.types import Panel

from .space_toolsystem_common import (
    ToolSelectPanelHelper,
    ToolDef,
)
from .properties_material_gpencil import (
    GPENCIL_UL_matslots,
)


def generate_from_brushes_ex(
        context, *,
        icon_prefix,
        brush_test_attr,
        brush_category_attr,
        brush_category_layout,
):
    # Categories
    brush_categories = {}
    if context.mode != 'GPENCIL_PAINT':
        for brush in context.blend_data.brushes:
            if getattr(brush, brush_test_attr) and brush.gpencil_settings is None:
                category = getattr(brush, brush_category_attr)
                name = brush.name
                brush_categories.setdefault(category, []).append(
                    ToolDef.from_dict(
                        dict(
                            text=name,
                            icon=icon_prefix + category.lower(),
                            data_block=name,
                        )
                    )
                )
    else:
        def draw_settings(context, layout, tool):
            _defs_gpencil_paint.draw_settings_common(context, layout, tool)

        for brush_type in brush_category_layout:
            for brush in context.blend_data.brushes:
                if getattr(brush, brush_test_attr) and brush.gpencil_settings.gp_icon == brush_type[0]:
                    category = brush_type[0]
                    name = brush.name
                    text = name

                    # Define icon.
                    icon_name = {
                        'PENCIL': 'draw_pencil',
                        'PEN': 'draw_pen',
                        'INK': 'draw_ink',
                        'INKNOISE': 'draw_noise',
                        'BLOCK': 'draw_block',
                        'MARKER': 'draw_marker',
                        'FILL': 'draw_fill',
                        'SOFT': 'draw.eraser_soft',
                        'HARD': 'draw.eraser_hard',
                        'STROKE': 'draw.eraser_stroke',
                    }[category]
                    brush_categories.setdefault(category, []).append(
                        ToolDef.from_dict(
                            dict(
                                text=text,
                                icon=icon_prefix + icon_name,
                                data_block=name,
                                widget=None,
                                operator="gpencil.draw",
                                draw_settings=draw_settings,
                            )
                        )
                    )

    def tools_from_brush_group(groups):
        assert(type(groups) is tuple)
        if len(groups) == 1:
            tool_defs = tuple(brush_categories.pop(groups[0], ()))
        else:
            tool_defs = tuple(item for g in groups for item in brush_categories.pop(g, ()))

        if len(tool_defs) > 1:
            return (tool_defs,)
        else:
            return tool_defs

    # Each item below is a single toolbar entry:
    # Grouped for multiple or none if no brushes are found.
    tool_defs = tuple(
        tool_def
        for category in brush_category_layout
        for tool_def in tools_from_brush_group(category)
    )
    # Ensure we use all types.
    if brush_categories:
        print(brush_categories)
    assert(len(brush_categories) == 0)
    return tool_defs


def generate_from_enum_ex(
        context, *,
        icon_prefix,
        data,
        attr,
):
    tool_defs = []
    for enum in data.rna_type.properties[attr].enum_items_static:
        name = enum.name
        identifier = enum.identifier
        tool_defs.append(
            ToolDef.from_dict(
                dict(
                    text=name,
                    icon=icon_prefix + identifier.lower(),
                    data_block=identifier,
                )
            )
        )
    return tuple(tool_defs)


class _defs_view3d_generic:
    @ToolDef.from_fn
    def cursor():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("view3d.cursor3d")
            layout.prop(props, "use_depth")
            layout.prop(props, "orientation")
        return dict(
            text="Cursor",
            description=(
                "Set the cursor location, drag to transform"
            ),
            icon="ops.generic.cursor",
            keymap=(
                ("view3d.cursor3d", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
                ("transform.translate",
                 dict(release_confirm=True, cursor_transform=True),
                 dict(type='EVT_TWEAK_A', value='ANY'),
                 ),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def cursor_click():
        return dict(
            text="None",
            icon="ops.generic.cursor",
            keymap=(
                # This is a dummy keymap entry, until particle system is properly working with toolsystem.
                ("view3d.cursor3d", dict(), dict(type='ACTIONMOUSE', value='CLICK', ctrl=True, alt=True, shift=True)),
            ),
        )

    @ToolDef.from_fn
    def ruler():
        return dict(
            text="Measure",
            description=(
                "Measure distance and angles.\n"
                "\u2022 Drag anywhere for new measurement.\n"
                "\u2022 Drag ruler segment to measure an angle.\n"
                "\u2022 Drag ruler outside the view to remove.\n"
                "\u2022 Ctrl to snap.\n"
                "\u2022 Shift to measure surface thickness"
            ),
            icon="ops.view3d.ruler",
            widget="VIEW3D_GGT_ruler",
            keymap=(
                ("view3d.ruler_add", dict(), dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )


def _defs_annotate_factory():

    class _defs_annotate:
        @staticmethod
        def draw_settings_common(context, layout, tool):
            ts = context.tool_settings

            space_type = tool.space_type
            if space_type == 'VIEW_3D':
                layout.separator()

                row = layout.row(align=True)
                row.prop(ts, "annotation_stroke_placement_view3d", text="Placement")
                if ts.gpencil_stroke_placement_view3d == 'CURSOR':
                    row.prop(ts.gpencil_sculpt, "lockaxis")
                elif ts.gpencil_stroke_placement_view3d in {'SURFACE', 'STROKE'}:
                    row.prop(ts, "use_gpencil_stroke_endpoints")

        @ToolDef.from_fn
        def scribble():
            def draw_settings(context, layout, tool):
                _defs_annotate.draw_settings_common(context, layout, tool)
            return dict(
                text="Annotate",
                icon="ops.gpencil.draw",
                cursor='PAINT_BRUSH',
                keymap=(
                    ("gpencil.annotate",
                     dict(mode='DRAW', wait_for_input=False),
                     dict(type='ACTIONMOUSE', value='PRESS')),
                ),
                draw_settings=draw_settings,
            )

        @ToolDef.from_fn
        def line():
            def draw_settings(context, layout, tool):
                _defs_annotate.draw_settings_common(context, layout, tool)
            return dict(
                text="Annotate Line",
                icon="ops.gpencil.draw.line",
                cursor='CROSSHAIR',
                keymap=(
                    ("gpencil.annotate",
                     dict(mode='DRAW_STRAIGHT', wait_for_input=False),
                     dict(type='EVT_TWEAK_A', value='ANY')),
                ),
                draw_settings=draw_settings,
            )

        @ToolDef.from_fn
        def poly():
            def draw_settings(context, layout, tool):
                _defs_annotate.draw_settings_common(context, layout, tool)
            return dict(
                text="Annotate Polygon",
                icon="ops.gpencil.draw.poly",
                cursor='CROSSHAIR',
                keymap=(
                    ("gpencil.annotate",
                     dict(mode='DRAW_POLY', wait_for_input=False),
                     dict(type='ACTIONMOUSE', value='PRESS')),
                ),
                draw_settings=draw_settings,
            )

        @ToolDef.from_fn
        def eraser():
            def draw_settings(context, layout, tool):
                # TODO: Move this setting to toolsettings
                user_prefs = context.user_preferences
                layout.prop(user_prefs.edit, "grease_pencil_eraser_radius", text="Radius")
            return dict(
                text="Annotate Eraser",
                icon="ops.gpencil.draw.eraser",
                cursor='CROSSHAIR',  # XXX: Always show brush circle when enabled
                keymap=(
                    ("gpencil.annotate",
                     dict(mode='ERASER', wait_for_input=False),
                     dict(type='ACTIONMOUSE', value='PRESS')),
                ),
                draw_settings=draw_settings,
            )
    return _defs_annotate


# Needed so annotation gets a keymap per space type.
_defs_annotate_image = _defs_annotate_factory()
_defs_annotate_view3d = _defs_annotate_factory()


class _defs_transform:

    @ToolDef.from_fn
    def translate():
        def draw_settings(context, layout, tool):
            tool_settings = context.tool_settings
            layout.prop(tool_settings, "use_gizmo_apron")
        return dict(
            text="Move",
            # cursor='SCROLL_XY',
            icon="ops.transform.translate",
            widget="TRANSFORM_GGT_gizmo",
            operator="transform.translate",
            # TODO, implement as optional fallback gizmo
            # keymap=(
            #     ("transform.translate", dict(release_confirm=True), dict(type='EVT_TWEAK_A', value='ANY')),
            # ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def rotate():
        def draw_settings(context, layout, tool):
            tool_settings = context.tool_settings
            layout.prop(tool_settings, "use_gizmo_apron")
        return dict(
            text="Rotate",
            # cursor='SCROLL_XY',
            icon="ops.transform.rotate",
            widget="TRANSFORM_GGT_gizmo",
            operator="transform.rotate",
            # TODO, implement as optional fallback gizmo
            # keymap=(
            #     ("transform.rotate", dict(release_confirm=True), dict(type='EVT_TWEAK_A', value='ANY')),
            # ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def scale():
        def draw_settings(context, layout, tool):
            tool_settings = context.tool_settings
            layout.prop(tool_settings, "use_gizmo_apron")
        return dict(
            text="Scale",
            # cursor='SCROLL_XY',
            icon="ops.transform.resize",
            widget="TRANSFORM_GGT_gizmo",
            operator="transform.resize",
            # TODO, implement as optional fallback gizmo
            # keymap=(
            #     ("transform.resize", dict(release_confirm=True), dict(type='EVT_TWEAK_A', value='ANY')),
            # ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def scale_cage():
        return dict(
            text="Scale Cage",
            icon="ops.transform.resize.cage",
            widget="VIEW3D_GGT_xform_cage",
            operator="transform.resize",
        )

    @ToolDef.from_fn
    def transform():
        def draw_settings(context, layout, tool):
            tool_settings = context.tool_settings
            layout.prop(tool_settings, "use_gizmo_apron")
            layout.prop(tool_settings, "use_gizmo_mode")
        return dict(
            text="Transform",
            description=(
                "Supports any combination of grab, rotate & scale at once"
            ),
            icon="ops.transform.transform",
            widget="TRANSFORM_GGT_gizmo",
            # No keymap default action, only for gizmo!
            draw_settings=draw_settings,
        )


class _defs_view3d_select:

    @ToolDef.from_fn
    def border():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("view3d.select_box")
            layout.prop(props, "mode", expand=True)
        return dict(
            text="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap=(
                ("view3d.select_box",
                 dict(mode='ADD'),
                 dict(type='EVT_TWEAK_A', value='ANY')),
                ("view3d.select_box",
                 dict(mode='SUB'),
                 dict(type='EVT_TWEAK_A', value='ANY', ctrl=True)),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def circle():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("view3d.select_circle")
            layout.prop(props, "radius")
        return dict(
            text="Select Circle",
            icon="ops.generic.select_circle",
            widget=None,
            keymap=(
                ("view3d.select_circle",
                 dict(deselect=False),
                 dict(type='ACTIONMOUSE', value='PRESS')),
                ("view3d.select_circle",
                 dict(deselect=True),
                 dict(type='ACTIONMOUSE', value='PRESS', ctrl=True)),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def lasso():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("view3d.select_lasso")
            layout.prop(props, "mode", expand=True)
        return dict(
            text="Select Lasso",
            icon="ops.generic.select_lasso",
            widget=None,
            keymap=(
                ("view3d.select_lasso",
                 dict(mode='ADD'),
                 dict(type='EVT_TWEAK_A', value='ANY')),
                ("view3d.select_lasso",
                 dict(mode='SUB'),
                 dict(type='EVT_TWEAK_A', value='ANY', ctrl=True)),
            ),
            draw_settings=draw_settings,
        )
# -----------------------------------------------------------------------------
# Object Modes (named based on context.mode)


class _defs_edit_armature:

    @ToolDef.from_fn
    def roll():
        return dict(
            text="Roll",
            icon="ops.armature.bone.roll",
            widget=None,
            keymap=(
                ("transform.transform",
                 dict(release_confirm=True, mode='BONE_ROLL'),
                 dict(type='EVT_TWEAK_A', value='ANY'),),
            ),
        )

    @ToolDef.from_fn
    def bone_envelope():
        return dict(
            text="Bone Envelope",
            icon="ops.transform.bone_envelope",
            widget=None,
            keymap=(
                ("transform.transform",
                 dict(release_confirm=True, mode='BONE_ENVELOPE'),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def bone_size():
        return dict(
            text="Bone Size",
            icon="ops.transform.bone_size",
            widget=None,
            keymap=(
                ("transform.transform",
                 dict(release_confirm=True, mode='BONE_SIZE'),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def extrude():
        return dict(
            text="Extrude",
            icon="ops.armature.extrude_move",
            widget=None,
            keymap=(
                ("armature.extrude_move",
                 dict(TRANSFORM_OT_translate=dict(release_confirm=True)),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def extrude_cursor():
        return dict(
            text="Extrude to Cursor",
            icon="ops.armature.extrude_cursor",
            widget=None,
            keymap=(
                ("armature.click_extrude", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )


class _defs_edit_mesh:

    @ToolDef.from_fn
    def cube_add():
        return dict(
            text="Add Cube",
            icon="ops.mesh.primitive_cube_add_gizmo",
            widget=None,
            keymap=(
                ("view3d.cursor3d", dict(), dict(type='ACTIONMOUSE', value='CLICK')),
                ("mesh.primitive_cube_add_gizmo", dict(), dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def rip_region():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.rip_move")
            props_macro = props.MESH_OT_rip
            layout.prop(props_macro, "use_fill")

        return dict(
            text="Rip Region",
            icon="ops.mesh.rip",
            widget=None,
            keymap=(
                ("mesh.rip_move",
                 dict(TRANSFORM_OT_translate=dict(release_confirm=True)),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def rip_edge():
        return dict(
            text="Rip Edge",
            icon="ops.mesh.rip_edge",
            widget=None,
            keymap=(
                ("mesh.rip_edge_move",
                 dict(TRANSFORM_OT_translate=dict(release_confirm=True)),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def poly_build():
        return dict(
            text="Poly Build",
            icon="ops.mesh.polybuild_hover",
            widget="VIEW3D_GGT_mesh_preselect_elem",
            keymap=(
                ("mesh.polybuild_face_at_cursor_move",
                 dict(TRANSFORM_OT_translate=dict(release_confirm=True)),
                 dict(type='ACTIONMOUSE', value='PRESS')),
                ("mesh.polybuild_split_at_cursor_move",
                 dict(TRANSFORM_OT_translate=dict(release_confirm=True)),
                 dict(type='ACTIONMOUSE', value='PRESS', ctrl=True)),
                ("mesh.polybuild_dissolve_at_cursor", dict(), dict(type='ACTIONMOUSE', value='CLICK', alt=True)),
            ),
        )

    @ToolDef.from_fn
    def edge_slide():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("transform.edge_slide")
            layout.prop(props, "correct_uv")

        return dict(
            text="Edge Slide",
            icon="ops.transform.edge_slide",
            widget=None,
            keymap=(
                ("transform.edge_slide", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')
                 ),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def vert_slide():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("transform.vert_slide")
            layout.prop(props, "correct_uv")

        return dict(
            text="Vertex Slide",
            icon="ops.transform.vert_slide",
            widget=None,
            keymap=(
                ("transform.vert_slide", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def spin():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.spin")
            layout.prop(props, "steps")
            props = tool.gizmo_group_properties("MESH_GGT_spin")
            layout.prop(props, "axis")

        return dict(
            text="Spin",
            icon="ops.mesh.spin",
            widget="MESH_GGT_spin",
            keymap=(
                ("mesh.spin", dict(),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def spin_duplicate():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.spin")
            layout.prop(props, "steps")
            props = tool.gizmo_group_properties("MESH_GGT_spin")
            layout.prop(props, "axis")

        return dict(
            text="Spin (Duplicate)",
            icon="ops.mesh.spin.duplicate",
            widget="MESH_GGT_spin",
            keymap=(
                ("mesh.spin", dict(dupli=True),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def inset():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.inset")
            layout.prop(props, "use_outset")
            layout.prop(props, "use_individual")
            layout.prop(props, "use_even_offset")
            layout.prop(props, "use_relative_offset")

        return dict(
            text="Inset Faces",
            icon="ops.mesh.inset",
            widget=None,
            keymap=(
                ("mesh.inset", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def bevel():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.bevel")
            layout.prop(props, "offset_type")
            layout.prop(props, "segments")
            layout.prop(props, "profile", slider=True)
            layout.prop(props, "vertex_only")

        return dict(
            text="Bevel",
            icon="ops.mesh.bevel",
            widget=None,
            keymap=(
                ("mesh.bevel", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def extrude():
        def draw_settings(context, layout, tool):
            props = tool.gizmo_group_properties("MESH_GGT_extrude")
            layout.prop(props, "axis_type", expand=True)
        return dict(
            text="Extrude Region",
            # The operator description isn't useful in this case, give our own.
            description=(
                "Extrude freely or along an axis"
            ),
            icon="ops.mesh.extrude_region_move",
            widget="MESH_GGT_extrude",
            # Important to use same operator as 'E' key.
            operator="view3d.edit_mesh_extrude_move_normal",
            keymap=(
                ("mesh.extrude_context_move",
                 dict(TRANSFORM_OT_translate=dict(release_confirm=True)),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def extrude_normals():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.extrude_region_shrink_fatten")
            props_macro = props.TRANSFORM_OT_shrink_fatten
            layout.prop(props_macro, "use_even_offset")
        return dict(
            text="Extrude Along Normals",
            icon="ops.mesh.extrude_region_shrink_fatten",
            widget=None,
            operator="mesh.extrude_region_shrink_fatten",
            keymap=(
                ("mesh.extrude_region_shrink_fatten",
                 dict(TRANSFORM_OT_shrink_fatten=dict(release_confirm=True)),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def extrude_individual():
        return dict(
            text="Extrude Individual",
            icon="ops.mesh.extrude_faces_move",
            widget=None,
            keymap=(
                ("mesh.extrude_faces_move", dict(TRANSFORM_OT_shrink_fatten=dict(release_confirm=True)),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def extrude_cursor():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.dupli_extrude_cursor")
            layout.prop(props, "rotate_source")

        return dict(
            text="Extrude to Cursor",
            icon="ops.mesh.dupli_extrude_cursor",
            widget=None,
            keymap=(
                ("mesh.dupli_extrude_cursor", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def loopcut_slide():

        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.loopcut_slide")
            props_macro = props.MESH_OT_loopcut
            layout.prop(props_macro, "number_cuts")
            props_macro = props.TRANSFORM_OT_edge_slide
            layout.prop(props_macro, "correct_uv")

        return dict(
            text="Loop Cut",
            icon="ops.mesh.loopcut_slide",
            widget="VIEW3D_GGT_mesh_preselect_edgering",
            keymap=(
                ("mesh.loopcut_slide",
                 dict(TRANSFORM_OT_edge_slide=dict(release_confirm=True)),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def offset_edge_loops_slide():
        return dict(
            text="Offset Edge Loop Cut",
            icon="ops.mesh.offset_edge_loops_slide",
            widget=None,
            keymap=(
                ("mesh.offset_edge_loops_slide", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def vertex_smooth():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.vertices_smooth")
            layout.prop(props, "repeat")
        return dict(
            text="Smooth",
            icon="ops.mesh.vertices_smooth",
            widget="WM_GGT_value_operator_redo",
            keymap=(
                # Use 0.0, so dragging increases from nothing.
                ("mesh.vertices_smooth", dict(factor=0.0),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def vertex_randomize():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("transform.vertex_random")
            layout.prop(props, "uniform")
            layout.prop(props, "normal")
            layout.prop(props, "seed")
        return dict(
            text="Randomize",
            icon="ops.transform.vertex_random",
            widget="WM_GGT_value_operator_redo",
            keymap=(
                # Use 0.0, so dragging increases from nothing.
                ("transform.vertex_random", dict(offset=0.0),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def shear():
        return dict(
            text="Shear",
            icon="ops.transform.shear",
            widget=None,
            keymap=(
                ("transform.shear", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def tosphere():
        return dict(
            text="To Sphere",
            icon="ops.transform.tosphere",
            widget=None,
            keymap=(
                ("transform.tosphere", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def shrink_fatten():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("transform.shrink_fatten")
            layout.prop(props, "use_even_offset")

        return dict(
            text="Shrink/Fatten",
            icon="ops.transform.shrink_fatten",
            widget=None,
            keymap=(
                ("transform.shrink_fatten", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def push_pull():
        return dict(
            text="Push/Pull",
            icon="ops.transform.push_pull",
            widget=None,
            keymap=(
                ("transform.push_pull", dict(release_confirm=True),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def knife():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.knife_tool")
            layout.prop(props, "use_occlude_geometry")
            layout.prop(props, "only_selected")

        return dict(
            text="Knife",
            icon="ops.mesh.knife_tool",
            widget=None,
            keymap=(
                ("mesh.knife_tool",
                 dict(wait_for_input=False),
                 dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def bisect():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("mesh.bisect")
            layout.prop(props, "use_fill")
            layout.prop(props, "clear_inner")
            layout.prop(props, "clear_outer")
            layout.prop(props, "threshold")
        return dict(
            text="Bisect",
            icon="ops.mesh.bisect",
            widget=None,
            keymap=(
                ("mesh.bisect",
                 dict(),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )


class _defs_edit_curve:

    @ToolDef.from_fn
    def draw():
        def draw_settings(context, layout, tool):
            # Tool settings initialize operator options.
            tool_settings = context.tool_settings
            cps = tool_settings.curve_paint_settings

            col = layout.row()

            col.prop(cps, "curve_type")

            if cps.curve_type == 'BEZIER':
                col.prop(cps, "error_threshold")
                col.prop(cps, "fit_method")
                col.prop(cps, "use_corners_detect")

                col = layout.row()
                col.active = cps.use_corners_detect
                col.prop(cps, "corner_angle")

        return dict(
            text="Draw",
            cursor='PAINT_BRUSH',
            icon=None,
            widget=None,
            keymap=(
                ("curve.draw", dict(wait_for_input=False), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def extrude():
        return dict(
            text="Extrude",
            icon=None,
            widget=None,
            keymap=(
                ("curve.extrude_move",
                 dict(TRANSFORM_OT_translate=dict(release_confirm=True)),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def extrude_cursor():
        return dict(
            text="Extrude Cursor",
            icon=None,
            widget=None,
            keymap=(
                ("curve.vertex_add", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )


class _defs_pose:

    @ToolDef.from_fn
    def breakdown():
        return dict(
            text="Breakdowner",
            icon="ops.pose.breakdowner",
            widget=None,
            keymap=(
                ("pose.breakdown", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def push():
        return dict(
            text="Push",
            icon="ops.pose.push",
            widget=None,
            keymap=(
                ("pose.push", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def relax():
        return dict(
            text="Relax",
            icon="ops.pose.relax",
            widget=None,
            keymap=(
                ("pose.relax", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )


class _defs_particle:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            icon_prefix="brush.particle.",
            data=context.tool_settings.particle_edit,
            attr="tool",
        )


class _defs_sculpt:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_brushes_ex(
            context,
            icon_prefix="brush.sculpt.",
            brush_test_attr="use_paint_sculpt",
            brush_category_attr="sculpt_tool",
            brush_category_layout=(
                ('DRAW',),
                ('GRAB', 'THUMB'),
                ('SNAKE_HOOK',),
                ('BLOB', 'INFLATE'),
                ('SMOOTH', 'SCRAPE', 'FLATTEN'),
                ('CREASE', 'PINCH'),
                ('CLAY', 'CLAY_STRIPS'),
                ('LAYER',),
                ('NUDGE', 'ROTATE'),
                ('FILL',),
                ('SIMPLIFY',),
                ('MASK',),
            )
        )

    @ToolDef.from_fn
    def hide_border():
        return dict(
            text="Box Hide",
            icon="ops.sculpt.border_hide",
            widget=None,
            keymap=(
                ("paint.hide_show", dict(action='HIDE'), dict(type='EVT_TWEAK_A', value='ANY')),
                ("paint.hide_show", dict(action='SHOW'), dict(type='EVT_TWEAK_A', value='ANY', ctrl=True)),
                ("paint.hide_show", dict(action='SHOW', area='ALL'), dict(type='SELECTMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def mask_border():
        return dict(
            text="Box Mask",
            icon="ops.sculpt.border_mask",
            widget=None,
            keymap=(
                ("view3d.select_box", dict(mode='ADD'), dict(type='EVT_TWEAK_A', value='ANY')),
                ("view3d.select_box", dict(mode='SUB'), dict(type='EVT_TWEAK_A', value='ANY', ctrl=True)),
            ),
        )


class _defs_vertex_paint:

    @staticmethod
    def poll_select_mask(context):
        ob = context.active_object
        return ob.type == 'MESH' and ob.data.use_paint_mask

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_brushes_ex(
            context,
            icon_prefix="brush.paint_vertex.",
            brush_test_attr="use_paint_vertex",
            brush_category_attr="vertex_tool",
            brush_category_layout=(
                ('MIX',),
                ('BLUR', 'AVERAGE'),
                ('SMEAR',),
                (
                    'ADD', 'SUB', 'MUL', 'LIGHTEN', 'DARKEN',
                    'COLORDODGE', 'DIFFERENCE', 'SCREEN', 'HARDLIGHT',
                    'OVERLAY', 'SOFTLIGHT', 'EXCLUSION', 'LUMINOCITY',
                    'SATURATION', 'HUE', 'ERASE_ALPHA', 'ADD_ALPHA',
                ),
            )
        )


class _defs_texture_paint:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_brushes_ex(
            context,
            icon_prefix="brush.paint_texture.",
            brush_test_attr="use_paint_image",
            brush_category_attr="image_tool",
            brush_category_layout=(
                ('DRAW',),
                ('SOFTEN',),
                ('SMEAR',),
                ('CLONE',),
                ('FILL',),
                ('MASK',),
            )
        )


class _defs_weight_paint:

    @staticmethod
    def poll_select_mask(context):
        ob = context.active_object
        return (ob.type == 'MESH' and
                (ob.data.use_paint_mask or
                 ob.data.use_paint_mask_vertex))

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_brushes_ex(
            context,
            icon_prefix="brush.paint_weight.",
            brush_test_attr="use_paint_weight",
            brush_category_attr="vertex_tool",
            brush_category_layout=(
                ('MIX',),
                ('BLUR', 'AVERAGE'),
                ('SMEAR',),
                (
                    'ADD', 'SUB', 'MUL', 'LIGHTEN', 'DARKEN',
                    'COLORDODGE', 'DIFFERENCE', 'SCREEN', 'HARDLIGHT',
                    'OVERLAY', 'SOFTLIGHT', 'EXCLUSION', 'LUMINOCITY',
                    'SATURATION', 'HUE',
                ),
            )
        )

    @ToolDef.from_fn
    def sample_weight():
        return dict(
            text="Sample Weight",
            icon="ops.paint.weight_sample",
            widget=None,
            keymap=(
                ("paint.weight_sample", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def sample_weight_group():
        return dict(
            text="Sample Vertex Group",
            icon="ops.paint.weight_sample_group",
            widget=None,
            keymap=(
                ("paint.weight_sample_group", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
            ),
        )

    @ToolDef.from_fn
    def gradient():
        def draw_settings(context, layout, tool):
            brush = context.tool_settings.weight_paint.brush
            if brush is not None:
                from .properties_paint_common import UnifiedPaintPanel
                UnifiedPaintPanel.prop_unified_weight(layout, context, brush, "weight", slider=True, text="Weight")
            props = tool.operator_properties("paint.weight_gradient")
            layout.prop(props, "type")

        return dict(
            text="Gradient",
            icon="ops.paint.weight_gradient",
            widget=None,
            keymap=(
                ("paint.weight_gradient", dict(), dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )


class _defs_image_generic:

    @staticmethod
    def poll_uvedit(context):
        ob = context.edit_object
        if ob is not None:
            data = ob.data
            if data is not None:
                return bool(getattr(data, "uv_layers", False))
        return False

    @ToolDef.from_fn
    def cursor():
        return dict(
            text="Cursor",
            description=(
                "Set the cursor location, drag to transform"
            ),
            icon="ops.generic.cursor",
            keymap=(
                ("uv.cursor_set", dict(), dict(type='ACTIONMOUSE', value='PRESS')),
                ("transform.translate",
                 dict(release_confirm=True, cursor_transform=True),
                 dict(type='EVT_TWEAK_A', value='ANY'),
                 ),
            ),
        )


class _defs_image_uv_transform:

    @ToolDef.from_fn
    def transform():
        return dict(
            text="Transform",
            description=(
                "Supports any combination of grab, rotate & scale at once"
            ),
            icon="ops.transform.transform",
            widget="IMAGE_GGT_gizmo2d",
            # No keymap default action, only for gizmo!
        )


class _defs_image_uv_select:

    @ToolDef.from_fn
    def border():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("uv.select_box")
            layout.prop(props, "deselect")
        return dict(
            text="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap=(
                ("uv.select_box",
                 dict(),
                 dict(type='EVT_TWEAK_A', value='ANY')),
                ("uv.select_box",
                 dict(deselect=True),
                 dict(type='EVT_TWEAK_A', value='ANY', ctrl=True)),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def circle():
        def draw_settings(context, layout, tool):
            props = tool.operator_properties("uv.select_circle")
            layout.prop(props, "radius")
        return dict(
            text="Select Circle",
            icon="ops.generic.select_circle",
            widget=None,
            keymap=(
                ("uv.select_circle",
                 dict(deselect=False),
                 dict(type='ACTIONMOUSE', value='PRESS')),
                ("uv.select_circle",
                 dict(deselect=True),
                 dict(type='ACTIONMOUSE', value='PRESS', ctrl=True)),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def lasso():
        return dict(
            text="Select Lasso",
            icon="ops.generic.select_lasso",
            widget=None,
            keymap=(
                ("uv.select_lasso",
                 dict(deselect=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
                # ("uv.select_lasso",
                #  dict(deselect=True),
                #  dict(type='EVT_TWEAK_A', value='ANY', ctrl=True)),
            ),
        )


class _defs_image_uv_sculpt:

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_enum_ex(
            context,
            icon_prefix="brush.uv_sculpt.",
            data=context.tool_settings,
            attr="uv_sculpt_tool",
        )


class _defs_gpencil_paint:
    @staticmethod
    def draw_color_selector(context, layout):
        brush = context.active_gpencil_brush
        gp_settings = brush.gpencil_settings
        ma = gp_settings.material
        row = layout.row(align=True)

        icon_id = 0
        if ma:
            icon_id = ma.id_data.preview.icon_id
            txt_ma = ma.name
            maxw = 25
            if len(txt_ma) > maxw:
                txt_ma = txt_ma[:maxw - 5] + '..' + txt_ma[-3:]
        else:
            txt_ma = ""

        row.label(text="Material:")
        sub = row.row()
        sub.ui_units_x = 8
        sub.popover(
            panel="TOPBAR_PT_gpencil_materials",
            text=txt_ma,
            icon_value=icon_id,
        )

        row.prop(gp_settings, "pin_material", text="")

    @staticmethod
    def draw_settings_common(context, layout, tool):
        ob = context.active_object
        if ob and ob.mode == 'GPENCIL_PAINT':
            brush = context.active_gpencil_brush
            gp_settings = brush.gpencil_settings

            if gp_settings.gpencil_brush_type == 'ERASE':
                row = layout.row(align=True)
                row.prop(brush, "size", text="Radius")
                row.prop(gp_settings, "use_pressure", text="", icon='STYLUS_PRESSURE')
                if gp_settings.eraser_mode == 'SOFT':
                    row = layout.row(align=True)
                    row.prop(gp_settings, "pen_strength", slider=True)
                    row.prop(gp_settings, "use_strength_pressure", text="", icon='STYLUS_PRESSURE')
            elif gp_settings.gpencil_brush_type == 'FILL':
                row = layout.row()
                row.prop(gp_settings, "gpencil_fill_leak", text="Leak Size")
                row.prop(brush, "size", text="Thickness")
                row.prop(gp_settings, "gpencil_fill_simplyfy_level", text="Simplify")

                _defs_gpencil_paint.draw_color_selector(context, layout)

                row = layout.row(align=True)
                row.prop(gp_settings, "gpencil_fill_draw_mode", text="")
                row.prop(gp_settings, "gpencil_fill_show_boundary", text="", icon='GRID')

            else:  # bgpsettings.gpencil_brush_type == 'DRAW':
                row = layout.row(align=True)
                row.prop(brush, "size", text="Radius")
                row.prop(gp_settings, "use_pressure", text="", icon='STYLUS_PRESSURE')
                row = layout.row(align=True)
                row.prop(gp_settings, "pen_strength", slider=True)
                row.prop(gp_settings, "use_strength_pressure", text="", icon='STYLUS_PRESSURE')

                _defs_gpencil_paint.draw_color_selector(context, layout)

    @staticmethod
    def generate_from_brushes(context):
        return generate_from_brushes_ex(
            context,
            icon_prefix="brush.gpencil.",
            brush_test_attr="use_paint_grease_pencil",
            brush_category_attr="grease_pencil_tool",
            brush_category_layout=(
                ('PENCIL',),
                ('PEN',),
                ('INK',),
                ('INKNOISE',),
                ('BLOCK',),
                ('MARKER',),
                ('FILL',),
                ('SOFT',),
                ('HARD',),
                ('STROKE',),
            )
        )


class _defs_gpencil_edit:
    @ToolDef.from_fn
    def bend():
        return dict(
            text="Bend",
            icon="ops.gpencil.edit_bend",
            widget=None,
            keymap=(
                ("transform.bend",
                 dict(release_confirm=True),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def box_select():
        return dict(
            text="Select Box",
            icon="ops.generic.select_box",
            widget=None,
            keymap=(
                ("gpencil.select_box",
                 dict(),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def circle_select():
        return dict(
            text="Select Circle",
            icon="ops.generic.select_circle",
            widget=None,
            keymap=(
                ("gpencil.select_circle",
                 dict(),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def lasso_select():
        return dict(
            text="Select Lasso",
            icon="ops.generic.select_lasso",
            widget=None,
            keymap=(
                ("gpencil.select_lasso",
                 dict(),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def mirror():
        return dict(
            text="Mirror",
            icon="ops.gpencil.edit_mirror",
            widget=None,
            keymap=(
                ("transform.mirror",
                 dict(release_confirm=True),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def shear():
        return dict(
            text="Shear",
            icon="ops.gpencil.edit_shear",
            widget=None,
            keymap=(
                ("transform.shear",
                 dict(release_confirm=True),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )

    @ToolDef.from_fn
    def tosphere():
        return dict(
            text="To Sphere",
            icon="ops.gpencil.edit_to_sphere",
            widget=None,
            keymap=(
                ("transform.tosphere",
                 dict(release_confirm=True),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
        )


class _defs_gpencil_sculpt:
    @staticmethod
    def draw_settings_common(context, layout, tool):
        ob = context.active_object
        if ob and ob.mode == 'GPENCIL_SCULPT':
            ts = context.tool_settings
            settings = ts.gpencil_sculpt
            tool = settings.tool
            brush = settings.brush

            layout.prop(brush, "size", slider=True)

            row = layout.row(align=True)
            row.prop(brush, "strength", slider=True)
            row.prop(brush, "use_pressure_strength", text="")

            if tool in {'THICKNESS', 'STRENGTH', 'PINCH', 'TWIST'}:
                row.separator()
                row.prop(brush, "direction", expand=True, text="")

    @ToolDef.from_fn
    def smooth():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Smooth",
            icon="ops.gpencil.sculpt_smooth",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='SMOOTH', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def thickness():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Thickness",
            icon="ops.gpencil.sculpt_thickness",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='THICKNESS', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def strength():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Strength",
            icon="ops.gpencil.sculpt_strength",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='STRENGTH', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def grab():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Grab",
            icon="ops.gpencil.sculpt_grab",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='GRAB', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def push():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Push",
            icon="ops.gpencil.sculpt_push",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='PUSH', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def twist():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Twist",
            icon="ops.gpencil.sculpt_twist",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='TWIST', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def pinch():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Pinch",
            icon="ops.gpencil.sculpt_pinch",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='PINCH', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def randomize():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Randomize",
            icon="ops.gpencil.sculpt_randomize",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='RANDOMIZE', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )

    @ToolDef.from_fn
    def clone():
        def draw_settings(context, layout, tool):
            _defs_gpencil_sculpt.draw_settings_common(context, layout, tool)

        return dict(
            text="Clone",
            icon="ops.gpencil.sculpt_clone",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='CLONE', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )


class _defs_gpencil_weight:
    @staticmethod
    def draw_settings_common(context, layout, tool):
        ob = context.active_object
        if ob and ob.mode == 'GPENCIL_WEIGHT':
            settings = context.tool_settings.gpencil_sculpt
            brush = settings.brush

            layout.prop(brush, "size", slider=True)

            row = layout.row(align=True)
            row.prop(brush, "strength", slider=True)
            row.prop(brush, "use_pressure_strength", text="")

    @ToolDef.from_fn
    def paint():
        def draw_settings(context, layout, tool):
            _defs_gpencil_weight.draw_settings_common(context, layout, tool)

        return dict(
            text="Draw",
            icon="ops.gpencil.sculpt_weight",
            widget=None,
            keymap=(
                ("gpencil.brush_paint",
                 dict(mode='WEIGHT', wait_for_input=False),
                 dict(type='EVT_TWEAK_A', value='ANY')),
            ),
            draw_settings=draw_settings,
        )


class TOPBAR_PT_gpencil_materials(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Materials"
    bl_ui_units_x = 14

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'

    @staticmethod
    def draw(self, context):
        layout = self.layout
        ob = context.object

        if ob:
            is_sortable = len(ob.material_slots) > 1
            rows = 1
            if (is_sortable):
                rows = 10

            row = layout.row()

            row.template_list("GPENCIL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.menu("GPENCIL_MT_color_specials", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

                col.separator()

                sub = col.column(align=True)
                sub.operator("gpencil.color_isolate", icon='LOCKED', text="").affect_visibility = False
                sub.operator("gpencil.color_isolate", icon='HIDE_OFF', text="").affect_visibility = True


class IMAGE_PT_tools_active(ToolSelectPanelHelper, Panel):
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_category = "Tools"
    bl_label = "Tools"  # not visible
    bl_options = {'HIDE_HEADER'}

    # Satisfy the 'ToolSelectPanelHelper' API.
    keymap_prefix = "Image Editor Tool:"

    @classmethod
    def tools_from_context(cls, context, mode=None):
        if mode is None:
            if context.space_data is None:
                mode = 'VIEW'
            else:
                mode = context.space_data.mode
        for tools in (cls._tools[None], cls._tools.get(mode, ())):
            for item in tools:
                if not (type(item) is ToolDef) and callable(item):
                    yield from item(context)
                else:
                    yield item

    @classmethod
    def tools_all(cls):
        yield from cls._tools.items()

    # for reuse
    _tools_transform = (
        _defs_image_uv_transform.transform,
    )

    _tools_select = (
        (
            _defs_image_uv_select.border,
            _defs_image_uv_select.circle,
            _defs_image_uv_select.lasso,
        ),
    )

    _tools_annotate = (
        (
            _defs_annotate_image.scribble,
            _defs_annotate_image.line,
            _defs_annotate_image.poly,
            _defs_annotate_image.eraser,
        ),
    )

    _tools = {
        None: [
            # for all modes
        ],
        'VIEW': [
            _defs_image_generic.cursor,
            *_tools_select,
            None,
            *_tools_transform,
            None,
            *_tools_annotate,
            None,
            lambda context: (
                _defs_image_uv_sculpt.generate_from_brushes(context)
                if _defs_image_generic.poll_uvedit(context)
                else ()
            ),
        ],
        'MASK': [
            None,
        ],
        'PAINT': [
            _defs_texture_paint.generate_from_brushes,
        ],
    }


class VIEW3D_PT_tools_active(ToolSelectPanelHelper, Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = "Tools"
    bl_label = "Tools"  # not visible
    bl_options = {'HIDE_HEADER'}

    # Satisfy the 'ToolSelectPanelHelper' API.
    keymap_prefix = "3D View Tool:"

    @classmethod
    def tools_from_context(cls, context, mode=None):
        if mode is None:
            mode = context.mode
        for tools in (cls._tools[None], cls._tools.get(mode, ())):
            for item in tools:
                if not (type(item) is ToolDef) and callable(item):
                    yield from item(context)
                else:
                    yield item

    @classmethod
    def tools_all(cls):
        yield from cls._tools.items()

    # for reuse
    _tools_transform = (
        _defs_transform.transform,
        _defs_transform.translate,
        _defs_transform.rotate,
        (
            _defs_transform.scale,
            _defs_transform.scale_cage,
        ),
    )

    _tools_select = (
        (
            _defs_view3d_select.border,
            _defs_view3d_select.circle,
            _defs_view3d_select.lasso,
        ),
    )

    _tools_annotate = (
        (
            _defs_annotate_view3d.scribble,
            _defs_annotate_view3d.line,
            _defs_annotate_view3d.poly,
            _defs_annotate_view3d.eraser,
        ),
        _defs_view3d_generic.ruler,
    )

    _tools_gpencil_select = (
        (
            _defs_gpencil_edit.box_select,
            _defs_gpencil_edit.circle_select,
            _defs_gpencil_edit.lasso_select,
        ),
    )

    _tools = {
        None: [
            # Don't use this! because of paint modes.
            # _defs_view3d_generic.cursor,
            # End group.
        ],
        'OBJECT': [
            _defs_view3d_generic.cursor,
            *_tools_select,
            None,
            *_tools_transform,
            None,
            *_tools_annotate,
        ],
        'POSE': [
            _defs_view3d_generic.cursor,
            *_tools_select,
            None,
            *_tools_transform,
            None,
            *_tools_annotate,
            None,
            (
                _defs_pose.breakdown,
                _defs_pose.push,
                _defs_pose.relax,
            ),
        ],
        'EDIT_ARMATURE': [
            _defs_view3d_generic.cursor,
            *_tools_select,
            None,
            *_tools_transform,
            None,
            *_tools_annotate,
            _defs_edit_armature.roll,
            (
                _defs_edit_armature.bone_size,
                _defs_edit_armature.bone_envelope,
            ),
            None,
            (
                _defs_edit_armature.extrude,
                _defs_edit_armature.extrude_cursor,
            ),
        ],
        'EDIT_MESH': [
            _defs_view3d_generic.cursor,
            *_tools_select,
            None,
            *_tools_transform,
            None,
            *_tools_annotate,
            None,
            _defs_edit_mesh.cube_add,
            None,
            (
                _defs_edit_mesh.extrude,
                _defs_edit_mesh.extrude_normals,
                _defs_edit_mesh.extrude_individual,
                _defs_edit_mesh.extrude_cursor,
            ),
            _defs_edit_mesh.inset,
            _defs_edit_mesh.bevel,
            (
                _defs_edit_mesh.loopcut_slide,
                _defs_edit_mesh.offset_edge_loops_slide,
            ),
            (
                _defs_edit_mesh.knife,
                _defs_edit_mesh.bisect,
            ),
            _defs_edit_mesh.poly_build,
            (
                _defs_edit_mesh.spin,
                _defs_edit_mesh.spin_duplicate,
            ),
            (
                _defs_edit_mesh.vertex_smooth,
                _defs_edit_mesh.vertex_randomize,
            ),
            (
                _defs_edit_mesh.edge_slide,
                _defs_edit_mesh.vert_slide,
            ),
            (
                _defs_edit_mesh.shrink_fatten,
                _defs_edit_mesh.push_pull,
            ),
            (
                _defs_edit_mesh.shear,
                _defs_edit_mesh.tosphere,
            ),
            (
                _defs_edit_mesh.rip_region,
                _defs_edit_mesh.rip_edge,
            ),
        ],
        'EDIT_CURVE': [
            _defs_view3d_generic.cursor,
            *_tools_select,
            None,
            *_tools_transform,
            None,
            *_tools_annotate,
            None,
            _defs_edit_curve.draw,
            (
                _defs_edit_curve.extrude,
                _defs_edit_curve.extrude_cursor,
            )
        ],
        'PARTICLE': [
            _defs_view3d_generic.cursor,
            _defs_particle.generate_from_brushes,
        ],
        'SCULPT': [
            _defs_sculpt.generate_from_brushes,
            None,
            _defs_sculpt.hide_border,
            _defs_sculpt.mask_border,
        ],
        'PAINT_TEXTURE': [
            _defs_texture_paint.generate_from_brushes,
        ],
        'PAINT_VERTEX': [
            _defs_vertex_paint.generate_from_brushes,
            None,
            lambda context: (
                VIEW3D_PT_tools_active._tools_select
                if _defs_vertex_paint.poll_select_mask(context)
                else ()
            ),
        ],
        'PAINT_WEIGHT': [
            # TODO, check for mixed pose mode
            _defs_view3d_generic.cursor,
            _defs_weight_paint.generate_from_brushes,
            None,
            _defs_weight_paint.sample_weight,
            _defs_weight_paint.sample_weight_group,
            None,
            lambda context: (
                VIEW3D_PT_tools_active._tools_select
                if _defs_weight_paint.poll_select_mask(context)
                else ()
            ),
            None,
            _defs_weight_paint.gradient,
        ],
        'GPENCIL_PAINT': [
            _defs_gpencil_paint.generate_from_brushes,
        ],
        'GPENCIL_EDIT': [
            _defs_view3d_generic.cursor,
            _defs_gpencil_edit.box_select,
            _defs_gpencil_edit.circle_select,
            _defs_gpencil_edit.lasso_select,
            None,
            _defs_gpencil_edit.bend,
            _defs_gpencil_edit.mirror,
            _defs_gpencil_edit.shear,
            _defs_gpencil_edit.tosphere,
        ],
        'GPENCIL_SCULPT': [
            _defs_gpencil_sculpt.smooth,
            _defs_gpencil_sculpt.thickness,
            _defs_gpencil_sculpt.strength,
            _defs_gpencil_sculpt.grab,
            _defs_gpencil_sculpt.push,
            _defs_gpencil_sculpt.twist,
            _defs_gpencil_sculpt.pinch,
            _defs_gpencil_sculpt.randomize,
            _defs_gpencil_sculpt.clone,
            None,
            *_tools_gpencil_select,
        ],
        'GPENCIL_WEIGHT': [
            _defs_gpencil_weight.paint,
        ],
    }


classes = (
    IMAGE_PT_tools_active,
    VIEW3D_PT_tools_active,
    TOPBAR_PT_gpencil_materials,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
