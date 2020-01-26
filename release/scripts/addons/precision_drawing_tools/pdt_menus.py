# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# -----------------------------------------------------------------------
# Author: Alan Odom (Clockmender), Rune Morling (ermo) Copyright (c) 2019
# -----------------------------------------------------------------------
#
import bpy
from bpy.types import Panel
from .pdt_msg_strings import (
    PDT_LAB_ABS,
    PDT_LAB_AD2D,
    PDT_LAB_AD3D,
    PDT_LAB_ALLACTIVE,
    PDT_LAB_ANGLEVALUE,
    PDT_LAB_ARCCENTRE,
    PDT_LAB_BISECT,
    PDT_LAB_CVALUE,
    PDT_LAB_DEL,
    PDT_LAB_DIR,
    PDT_LAB_DISVALUE,
    PDT_LAB_EDGETOEFACE,
    PDT_LAB_FILLET,
    PDT_LAB_FLIPANGLE,
    PDT_LAB_FLIPPERCENT,
    PDT_LAB_INTERSECT,
    PDT_LAB_INTERSETALL,
    PDT_LAB_JOIN2VERTS,
    PDT_LAB_MODE,
    PDT_LAB_NOR,
    PDT_LAB_OPERATION,
    PDT_LAB_ORDER,
    PDT_LAB_ORIGINCURSOR,
    PDT_LAB_PERCENT,
    PDT_LAB_PERCENTS,
    PDT_LAB_PIVOTALPHA,
    PDT_LAB_PIVOTLOC,
    PDT_LAB_PIVOTLOCH,
    PDT_LAB_PIVOTSIZE,
    PDT_LAB_PIVOTWIDTH,
    PDT_LAB_PLANE,
    PDT_LAB_PROFILE,
    PDT_LAB_RADIUS,
    PDT_LAB_SEGMENTS,
    PDT_LAB_TAPER,
    PDT_LAB_TAPERAXES,
    PDT_LAB_TOOLS,
    PDT_LAB_USEVERTS,
    PDT_LAB_VARIABLES
)

def ui_width():
    """Return the Width of the UI Panel.

    Args:
        None.

    Returns:
        UI Width.
    """

    area = bpy.context.area
    resolution = bpy.context.preferences.system.ui_scale

    for reg in area.regions:
        if reg.type == "UI":
            region_width = reg.width
    return region_width

# PDT Panel menus
#
class PDT_PT_PanelDesign(Panel):
    bl_idname = "PDT_PT_PanelDesign"
    bl_label = "PDT Design"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ui_cutoff = bpy.context.preferences.addons[__package__].preferences.pdt_ui_width
        layout = self.layout
        pdt_pg = context.scene.pdt_pg
        #
        # Working Plane
        row = layout.row()
        row.label(text=f"Working {PDT_LAB_PLANE}:")
        row.prop(pdt_pg, "plane", text="")
        #
        # Move Mode
        row = layout.row()
        row.label(text=f"Move {PDT_LAB_MODE}:")
        row.prop(pdt_pg, "select", text="")
        #
        # Active or All Selected
        row = layout.row()
        #row.label(text="")
        row.prop(pdt_pg, "extend", text="All Selected Entities (Off: Active Only)")

        # --------------------
        # (1) Select Operation
        row = layout.row()
        box_1 = row.box()
        row = box_1.row()
        row.label(text=f"(1) Select {PDT_LAB_OPERATION}:")
        row.prop(pdt_pg, "operation", text="")

        # -----------------------
        # (a) Set Coordinates box
        row = box_1.row()
        box_1a = row.box()
        box_1a.label(text=f"(a) Either Set Coordinates + [Place »]")
        # ^ was PDT_LAB_VARIABLES
        #
        # cartesian input coordinates in a box
        row = box_1a.row()
        box = row.box()
        row = box.row()
        split = row.split(factor=0.35, align=True)
        split.label(text=PDT_LAB_CVALUE)
        split.prop(pdt_pg, "cartesian_coords", text="")
        row = box.row()
        row.operator("pdt.absolute", icon="EMPTY_AXIS", text=f"{PDT_LAB_ABS} »")
        row.operator("pdt.delta", icon="EMPTY_AXIS", text=f"{PDT_LAB_DEL} »")
        #
        # directional input coordinates in a box
        row = box_1a.row()
        box = row.box()
        #box.label(text="Directional/Polar Coordinates:")
        row = box.row()
        row.prop(pdt_pg, "distance", text=PDT_LAB_DISVALUE)
        row.prop(pdt_pg, "angle", text=PDT_LAB_ANGLEVALUE)
        row = box.row()
        row.operator("pdt.distance", icon="EMPTY_AXIS", text=f"{PDT_LAB_DIR} »")
        row.prop(pdt_pg, "flip_angle", text=PDT_LAB_FLIPANGLE)

        # ---------------------
        # (b) Miscellaneous box
        row = box_1.row()
        box_1b = row.box()
        box_1b.label(text="(b) Or Select |n| Entities + [Place »]")
        #
        # normal or arc centre
        row = box_1b.row()
        row.operator("pdt.normal", text=f"|3| {PDT_LAB_NOR} »")
        row.operator("pdt.centre", text=f"|3| {PDT_LAB_ARCCENTRE} »")
        #
        # Intersect
        box = box_1b.box()
        row = box.row()
        row.operator("pdt.intersect", text=f"|4| {PDT_LAB_INTERSECT} »")
        if ui_width() < ui_cutoff:
            row = box.row()
        row.prop(pdt_pg, "object_order", text=PDT_LAB_ORDER)
        #
        # percentage row
        row = box_1b.row()
        box = row.box()
        box.label(text=f"Do (1) at % between selected points")
        row = box.row()
        row.operator("pdt.percent", text=f"|2| % »")
        row.prop(pdt_pg, "percent", text=PDT_LAB_PERCENTS)
        if ui_width() < ui_cutoff:
            row = box.row()
        row.prop(pdt_pg, "flip_percent", text=PDT_LAB_FLIPPERCENT)

        # -----
        # Tools
        toolbox = layout.box()
        toolbox.label(text=PDT_LAB_TOOLS)
        row = toolbox.row()
        row.operator("pdt.origin", text=PDT_LAB_ORIGINCURSOR)
        row = toolbox.row()
        row.operator("pdt.angle2", text=PDT_LAB_AD2D)
        row.operator("pdt.angle3", text=PDT_LAB_AD3D)
        row = toolbox.row()
        row.operator("pdt.join", text=PDT_LAB_JOIN2VERTS)
        row.operator("pdt.linetobisect", text=PDT_LAB_BISECT)
        row = toolbox.row()
        row.operator("pdt.edge_to_face", text=PDT_LAB_EDGETOEFACE)
        row.operator("pdt.intersectall", text=PDT_LAB_INTERSETALL)
        #
        # Taper tool
        box = toolbox.box()
        row = box.row()
        row.operator("pdt.taper", text=PDT_LAB_TAPER)
        row.prop(pdt_pg, "taper", text=PDT_LAB_TAPERAXES)
        #
        # Fillet tool
        box = toolbox.box()
        row = box.row()
        row.prop(pdt_pg, "fillet_radius", text=PDT_LAB_RADIUS)
        row.prop(pdt_pg, "fillet_profile", text=PDT_LAB_PROFILE)
        row = box.row()
        row.prop(pdt_pg, "fillet_segments", text=PDT_LAB_SEGMENTS)
        row.prop(pdt_pg, "fillet_vertices_only", text=PDT_LAB_USEVERTS)
        row = box.row()
        row.operator("pdt.fillet", text=f"{PDT_LAB_FILLET}")
        row.prop(pdt_pg, "fillet_int", text="Intersect")


class PDT_PT_PanelPivotPoint(Panel):
    bl_idname = "PDT_PT_PanelPivotPoint"
    bl_label = "PDT Pivot Point"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ui_cutoff = bpy.context.preferences.addons[__package__].preferences.pdt_ui_width
        pdt_pg = context.scene.pdt_pg
        layout = self.layout
        row = layout.row()
        col = row.column()
        if context.window_manager.pdt_run_opengl is False:
            icon = "PLAY"
            txt = "Show"
        else:
            icon = "PAUSE"
            txt = "Hide"
        col.operator("pdt.modaldraw", icon=icon, text=txt)
        col = row.column()
        col.prop(pdt_pg, "pivot_size", text=PDT_LAB_PIVOTSIZE)
        if ui_width() < ui_cutoff:
            row = layout.row()
        col = row.column()
        col.prop(pdt_pg, "pivot_width", text=PDT_LAB_PIVOTWIDTH)
        col = row.column()
        col.prop(pdt_pg, "pivot_alpha", text=PDT_LAB_PIVOTALPHA)
        row = layout.row()
        split = row.split(factor=0.35, align=True)
        split.label(text=PDT_LAB_PIVOTLOCH)
        split.prop(pdt_pg, "pivot_loc", text=PDT_LAB_PIVOTLOC)
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotselected", icon="EMPTY_AXIS", text="Selection")
        col = row.column()
        col.operator("pdt.pivotcursor", icon="EMPTY_AXIS", text="Cursor")
        col = row.column()
        col.operator("pdt.pivotorigin", icon="EMPTY_AXIS", text="Origin")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewplanerot", icon="EMPTY_AXIS", text="Rotate")
        col = row.column()
        col.prop(pdt_pg, "pivot_ang", text="Angle")
        row = layout.row()
        col = row.column()
        col.operator("pdt.viewscale", icon="EMPTY_AXIS", text="Scale")
        col = row.column()
        col.operator("pdt.cursorpivot", icon="EMPTY_AXIS", text="Cursor To Pivot")
        row = layout.row()
        col = row.column()
        col.prop(pdt_pg, "pivot_dis", text="Scale Distance")
        col = row.column()
        col.prop(pdt_pg, "distance", text="System Distance")
        row = layout.row()
        split = row.split(factor=0.35, align=True)
        split.label(text="Scale")
        split.prop(pdt_pg, "pivot_scale", text="")
        row = layout.row()
        col = row.column()
        col.operator("pdt.pivotwrite", icon="FILE_TICK", text="PP Write")
        col = row.column()
        col.operator("pdt.pivotread", icon="FILE", text="PP Read")


class PDT_PT_PanelPartsLibrary(Panel):
    bl_idname = "PDT_PT_PanelPartsLibrary"
    bl_label = "PDT Parts Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ui_cutoff = context.preferences.addons[__package__].preferences.pdt_ui_width
        layout = self.layout
        pdt_pg = context.scene.pdt_pg
        row = layout.row()
        col = row.column()
        col.operator("pdt.append", text="Append")
        col = row.column()
        col.operator("pdt.link", text="Link")
        if ui_width() < ui_cutoff:
            row = layout.row()
        col = row.column()
        col.prop(pdt_pg, "lib_mode", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Objects")
        col = row.column()
        col.prop(pdt_pg, "object_search_string")
        row = box.row()
        row.prop(pdt_pg, "lib_objects", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Collections")
        col = row.column()
        col.prop(pdt_pg, "collection_search_string")
        row = box.row()
        row.prop(pdt_pg, "lib_collections", text="")
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="Materials")
        col = row.column()
        col.prop(pdt_pg, "material_search_string")
        row = box.row()
        row.prop(pdt_pg, "lib_materials", text="")
        row = box.row()
        row.operator("pdt.lib_show", text="Show Library File", icon='INFO')


class PDT_PT_PanelViewControl(Panel):
    bl_idname = "PDT_PT_PanelViewControl"
    bl_label = "PDT View Control"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    # Sub-layout highlight states
    _ui_groups = [False, False]

    def draw(self, context):
        ui_cutoff = context.preferences.addons[__package__].preferences.pdt_ui_width
        layout = self.layout
        ui_groups = self._ui_groups
        pdt_pg = context.scene.pdt_pg
        box = layout.box()
        row = box.row()
        col = row.column()
        col.label(text="View Rotation")
        col = row.column()
        col.operator("pdt.viewrot", text="Rotate Abs")
        row = box.row()
        split = row.split(factor=0.35, align=True)
        split.label(text="Rotation")
        split.prop(pdt_pg, "rotation_coords", text="")
        row = box.row()
        col = row.column()
        col.prop(pdt_pg, "vrotangle", text="Angle")
        if ui_width() < ui_cutoff:
            row = box.row()
        col = row.column()
        col.operator("pdt.viewleft", text="", icon="TRIA_LEFT")
        col = row.column()
        col.operator("pdt.viewright", text="", icon="TRIA_RIGHT")
        col = row.column()
        col.operator("pdt.viewup", text="", icon="TRIA_UP")
        col = row.column()
        col.operator("pdt.viewdown", text="", icon="TRIA_DOWN")
        col = row.column()
        col.operator("pdt.viewroll", text="", icon="RECOVER_LAST")
        row = box.row()
        col = row.column()
        col.operator("pdt.viewiso", text="Isometric")
        col = row.column()
        col.operator("pdt.reset_3d_view", text="Reset View")


class PDT_PT_PanelCommandLine(Panel):
    bl_idname = "PDT_PT_PanelCommandLine"
    bl_label = "PDT Command Line (? for help)"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "PDT"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        pdt_pg = context.scene.pdt_pg
        row = layout.row()
        col = row.column()
        col.prop(pdt_pg, "plane", text="Plane")
        col = row.column()
        col.prop(pdt_pg, "select", text="Mode")
        row = layout.row()
        row.label(text="Comand Line, uses Plane & Mode Options")
        row = layout.row()
        row.prop(pdt_pg, "command", text="")
        # Try Re-run
        row.operator("pdt.command_rerun", text="", icon="LOOP_BACK")
        row = layout.row()
        row.prop(pdt_pg, "maths_output", text="Maths Output")
