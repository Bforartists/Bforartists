# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>

import bpy
from bpy.types import Panel
import bmesh
import sys

import dataclasses

from bpy.app.translations import contexts as i18n_contexts
from bl_ui.space_toolsystem_common import (
    toolsystem_column_count,
    Separator,
    OperatorEntry,
    MenuEntry,
    SetOperatorContext,
    draw_entries,
)


class ToolsystemPanel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True


# BFA - Import the default library wizard functions
def create_wizard_entry(obj, text, icon):
    """Debug version to check what's in wizard_handlers"""
    if not bpy.context.preferences.addons.get("bfa_default_library"):
        return False

    try:
        wizard_handlers = sys.modules["modular_child_addons.wizard_handlers"]

        # Debug: print all attributes of the module
        #print(f"DEBUG: wizard_handlers module attributes: {dir(wizard_handlers)}")

        # Check if the functions exist
        has_detect = hasattr(wizard_handlers, "detect_wizard_for_object")
        has_draw = hasattr(wizard_handlers, "draw_wizard_button")

        #print(f"DEBUG: detect_wizard_for_object exists: {has_detect}")
        #print(f"DEBUG: draw_wizard_button exists: {has_draw}")

        if has_detect:
            has_wizard, wizard_bl_idname, _ = wizard_handlers.detect_wizard_for_object(obj)
            #print(f"DEBUG: Wizard detection result: {has_wizard}, {wizard_bl_idname}")

            if has_wizard and wizard_bl_idname:
                return OperatorEntry(wizard_bl_idname, text=text, icon=icon)

    except Exception as e:
        #print(f"DEBUG: Wizard button error: {e}")
        import traceback
        traceback.print_exc()

    return OperatorEntry(wizard_bl_idname, poll=False)

# ------------------------ Object

class VIEW3D_PT_object_tab_transform(ToolsystemPanel):
    bl_label = "Transform"
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GREASE_PENCIL', 'POSE', 'EDIT_CURVES'}

    # TODO - Simplify this
    def draw(self, context):
        layout = self.layout
        obj = context.object

        entries = [
            OperatorEntry("transform.tosphere", text="To Sphere", icon='TOSPHERE'),
        ]

        if context.mode in {'EDIT_MESH'}:
            entries.extend([
                OperatorEntry("mesh.circularize", text="To Circle", icon='TOCIRCLE'),
                OperatorEntry("mesh.flatten", text="Flatten", icon="FLATTEN"),
                OperatorEntry("mesh.space_edge_loops_evenly", text="Space Edge Loops Evenly", icon='SPACE_LOOPS_EVENLY'),
            ])

        entries.extend([
            OperatorEntry("transform.shear", text="Shear", icon='SHEAR'),
            OperatorEntry("transform.bend", text="Bend", icon='BEND'),
            OperatorEntry("transform.push_pull", text="Push/Pull", icon='PUSH_PULL'),
        ])

        if context.mode in {'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL'}:
            entries.extend([
                Separator,
                OperatorEntry("transform.vertex_warp", text="Warp", icon='MOD_WARP'),
                SetOperatorContext('EXEC_REGION_WIN'),
                OperatorEntry("transform.vertex_random", text="Randomize", icon='RANDOMIZE', props={"offset": 0.1}),
                SetOperatorContext('INVOKE_REGION_WIN'),
            ])

        if context.mode == 'EDIT_MESH':
            entries.extend([
                Separator,
                OperatorEntry("transform.shrink_fatten", text="Shrink Fatten", icon='SHRINK_FATTEN'),
                OperatorEntry("transform.skin_resize", icon='MOD_SKIN'),
            ])
        elif context.mode == 'EDIT_CURVE':
            entries.extend([
                Separator,
                OperatorEntry("transform.transform", text="Radius", icon='SHRINK_FATTEN', props={"mode": 'CURVE_SHRINKFATTEN'}),
            ])
        elif context.mode == 'EDIT_CURVE':
            entries.extend([
                Separator,
                OperatorEntry("transform.transform", text="Opacity", icon='GP_OPACITY', props={"mode": 'GPENCIL_OPACITY'}),
            ])

        if context.active_object is not None and obj.type != 'ARMATURE':
            entries.extend([
                Separator,
                OperatorEntry("transform.translate", text="Move Texture Space", icon='MOVE_TEXTURESPACE', props={"texture_space": True}),
                OperatorEntry("transform.resize", text="Scale Texture Space", icon='SCALE_TEXTURESPACE', props={"texture_space": True}),
            ])
        elif context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'OBJECT'}:
            entries.extend([
                Separator,
                OperatorEntry("transform.translate", text="Move Texture Space", icon='MOVE_TEXTURESPACE', props={"texture_space": True}),
                OperatorEntry("transform.resize", text="Scale Texture Space", icon='SCALE_TEXTURESPACE', props={"texture_space": True}),
            ])

        if context.mode == 'OBJECT':
            entries.extend([
                Separator,
                SetOperatorContext('EXEC_REGION_WIN'),
                # XXX see alignmenu() in edit.c of b2.4x to get this working
                OperatorEntry("transform.transform", text="Align to Transform Orientation", icon='ALIGN_TRANSFORM', props={"mode": 'ALIGN'}),
                OperatorEntry("object.randomize_transform", icon='RANDOMIZE_TRANSFORM'),
                OperatorEntry("object.align", icon='ALIGN'),
                SetOperatorContext('INVOKE_REGION_WIN'),
            ])

        # armature specific extensions follow
        if context.active_object is not None and obj.type == 'ARMATURE' and obj.mode in {'EDIT', 'POSE'}:
            if obj.data.display_type == 'BBONE':
                entries.extend([
                    Separator,
                    OperatorEntry("transform.transform", text="Scale BBone", icon='TRANSFORM_SCALE', props={"mode": 'BONE_SIZE'}),
                ])
            elif obj.data.display_type == 'ENVELOPE':
                entries.extend([
                    Separator,
                    OperatorEntry("transform.transform", text="Scale Envelope Distance", icon='TRANSFORM_SCALE', props={"mode": 'BONE_SIZE'}),
                    OperatorEntry("transform.transform", text="Scale Radius", icon='TRANSFORM_SCALE', props={"mode": 'BONE_ENVELOPE'}),
                ])

        if context.active_object is not None and context.edit_object and context.edit_object.type == 'ARMATURE':
            entries.extend([
                Separator,
                OperatorEntry("armature.align", icon='ALIGN'),
            ])

        draw_entries(layout, context, entries)


class VIEW3D_PT_object_tab_set_origin(ToolsystemPanel):
    bl_label = "Set Origin"
    bl_category = "Object"
    bl_context="objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.origin_set", text="Geometry to Origin", icon='GEOMETRY_TO_ORIGIN', props={"type": 'GEOMETRY_ORIGIN'}),
            OperatorEntry("object.origin_set", text="Origin to Geometry", icon='ORIGIN_TO_GEOMETRY', props={"type": 'ORIGIN_GEOMETRY'}),
            OperatorEntry("object.origin_set", text="Origin to 3D Cursor", icon='ORIGIN_TO_CURSOR', props={"type": 'ORIGIN_CURSOR'}),
            OperatorEntry("object.origin_set", text="Origin to Center of Mass (Surface)", icon='ORIGIN_TO_CENTEROFMASS', props={"type": 'ORIGIN_CENTER_OF_MASS'}),
            OperatorEntry("object.origin_set", text="Origin to Center of Mass (Volume)", icon='ORIGIN_TO_VOLUME', props={"type": 'ORIGIN_CENTER_OF_VOLUME'}),
        )

        draw_entries(layout, context, entries)


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_global_x(bpy.types.Operator):
    """Mirror global around X axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.global_x"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Global X"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(True, False, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_global_y(bpy.types.Operator):
    """Mirror global around X axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.global_y"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Global X"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(False, True, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_global_z(bpy.types.Operator):
    """Mirror global around Z axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.global_z"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Global Z"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='GLOBAL', constraint_axis=(False, False, True))
        return {'FINISHED'}


class VIEW3D_PT_object_tab_mirror(ToolsystemPanel):
    bl_label = "Mirror"
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GREASE_PENCIL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        can_mirror_vgroup = context.edit_object and context.edit_object.type in {'MESH', 'SURFACE'}

        entries = (
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("mirror.global_x", text="X Global", icon='MIRROR_X'),
            OperatorEntry("mirror.global_y", text="Y Global", icon='MIRROR_Y'),
            OperatorEntry("mirror.global_z", text="Z Global", icon='MIRROR_Z'),
            OperatorEntry("object.vertex_group_mirror", icon='MIRROR_VERTEXGROUP', poll=can_mirror_vgroup),
        )

        draw_entries(layout, context, entries)


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_local_x(bpy.types.Operator):
    """Mirror local around X axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.local_x"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Local X"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='LOCAL', constraint_axis=(True, False, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_local_y(bpy.types.Operator):
    """Mirror local around Y axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.local_y"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Local Y"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='LOCAL', constraint_axis=(False, True, False))
        return {'FINISHED'}


# Workaround to separate the tooltips
class VIEW3D_MT_object_mirror_local_z(bpy.types.Operator):
    """Mirror local around Z axis"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mirror.local_z"        # unique identifier for buttons and menu items to reference.
    bl_label = "Mirror Local Z"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.transform.mirror(orient_type='LOCAL', constraint_axis=(False, False, True))
        return {'FINISHED'}


class VIEW3D_PT_object_tab_mirror_local(ToolsystemPanel):
    bl_label = "Mirror Local"
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GREASE_PENCIL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("mirror.local_x", text="X Local", icon='MIRROR_X'),
            OperatorEntry("mirror.local_y", text="Y Local", icon='MIRROR_Y'),
            OperatorEntry("mirror.local_z", text="Z Local", icon='MIRROR_Z'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_object_tab_clear(ToolsystemPanel):
    bl_label = "Clear"
    bl_category = "Object"
    bl_context="objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.location_clear", text="Location", icon='CLEARMOVE', props={"clear_delta": False}),
            OperatorEntry("object.rotation_clear", text="Rotation", icon='CLEARROTATE', props={"clear_delta": False}),
            OperatorEntry("object.scale_clear", text="Scale", icon='CLEARSCALE', props={"clear_delta": False}),
            Separator,
            OperatorEntry("object.origin_clear", text="Origin", icon='CLEARORIGIN'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_object_tab_apply(ToolsystemPanel):
    bl_label = "Apply"
    bl_category = "Object"
    bl_context="objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = [
            OperatorEntry("view3d.tb_apply_location", text="Location", icon='APPLYMOVE'),
            OperatorEntry("view3d.tb_apply_rotate", text="Rotation", icon='APPLYROTATE'),
            OperatorEntry("view3d.tb_apply_scale", text="Scale", icon='APPLYSCALE'),
            OperatorEntry("view3d.tb_apply_all", text="All Transforms", icon='APPLYALL'),
            OperatorEntry("view3d.tb_apply_rotscale", text="Rotation & Scale", icon='APPLY_ROTSCALE'),
            Separator,
            OperatorEntry("object.visual_transform_apply", text="Visual Transform", icon='VISUALTRANSFORM', text_ctxt=i18n_contexts.default),
            OperatorEntry("object.duplicates_make_real", icon='MAKEDUPLIREAL'),
            OperatorEntry("object.parent_inverse_apply", text="Parent Inverse", icon='APPLY_PARENT_INVERSE', text_ctxt=i18n_contexts.default),
            OperatorEntry("object.visual_geometry_to_objects", icon='VISUAL_GEOMETRY_TO_OBJECTS'),
        ]

        if context.preferences.addons.get("bfa_default_library"):
            entries.extend((
                Separator,
                OperatorEntry("object.apply_selected_objects", text="Visual Geometry and Join", icon='JOIN', 
                    props={"join_on_apply": True, "boolean_on_apply": False, "remesh_on_apply": False}),
                OperatorEntry("object.apply_selected_objects", text="Visual Geometry and Boolean", icon='MOD_BOOLEAN', 
                    props={"join_on_apply": False, "boolean_on_apply": True, "remesh_on_apply": False}),
                OperatorEntry("object.apply_selected_objects", text="Visual Geometry and Remesh", icon='MOD_REMESH', 
                    props={"join_on_apply": False, "boolean_on_apply": False, "remesh_on_apply": True}),
            ))

        draw_entries(layout, context, entries)


class VIEW3D_PT_object_tab_apply_delta(ToolsystemPanel):
    bl_label = "Apply Deltas"
    bl_category = "Object"
    bl_context="objectmode"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.transforms_to_deltas", text="Location to Deltas", icon='APPLYMOVEDELTA', 
                props={"mode": 'LOC'}, text_ctxt=i18n_contexts.default),
            OperatorEntry("object.transforms_to_deltas", text="Rotation to Deltas", icon='APPLYROTATEDELTA', 
                props={"mode": 'ROT'}, text_ctxt=i18n_contexts.default),
            OperatorEntry("object.transforms_to_deltas", text="Scale to Deltas", icon='APPLYSCALEDELTA', 
                props={"mode": 'SCALE'}, text_ctxt=i18n_contexts.default),
            OperatorEntry("object.transforms_to_deltas", text="All Transforms to Deltas", icon='APPLYALLDELTA', 
                props={"mode": 'ALL'}, text_ctxt=i18n_contexts.default),
            Separator,
            OperatorEntry("object.anim_transforms_to_deltas", icon='APPLYANIDELTA'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_object_tab_snap(ToolsystemPanel):
    bl_label = "Snap"
    bl_category = "Object"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_GREASE_PENCIL', 'POSE', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("view3d.snap_selected_to_cursor", text="Selection to Cursor", icon='SELECTIONTOCURSOR', props={"use_offset": False}),
            OperatorEntry("view3d.snap_selected_to_cursor", text="Selection to Cursor (Keep Offset)", icon='SELECTIONTOCURSOROFFSET', props={"use_offset": True}),
            OperatorEntry("view3d.snap_selected_to_active", text="Selection to Active", icon='SELECTIONTOACTIVE'),
            OperatorEntry("view3d.snap_selected_to_grid", text="Selection to Grid", icon='SELECTIONTOGRID'),
            Separator,
            OperatorEntry("view3d.snap_cursor_to_selected", text="Cursor to Selected", icon='CURSORTOSELECTION'),
            OperatorEntry("view3d.snap_cursor_to_center", text="Cursor to World Origin", icon='CURSORTOCENTER'),
            OperatorEntry("view3d.snap_cursor_to_active", text="Cursor to Active", icon='CURSORTOACTIVE'),
            OperatorEntry("view3d.snap_cursor_to_grid", text="Cursor to Grid", icon='CURSORTOGRID'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_object_tab_shading(ToolsystemPanel):
    bl_label = "Shading"
    bl_category = "Object"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.shade_smooth", icon='SHADING_SMOOTH'),
            OperatorEntry("object.shade_flat", icon='SHADING_FLAT'),
            OperatorEntry("object.shade_smooth_by_angle", text="Shade Smooth by Angle", icon='NORMAL_SMOOTH'),
        )

        draw_entries(layout, context, entries)

# ------------------------ Utility

class VIEW3D_PT_utility_tab_parent(ToolsystemPanel):
    bl_label = "Parents"
    bl_category = "Utility"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.parent_set", icon='PARENT_SET'),
            OperatorEntry("object.parent_clear", icon='PARENT_CLEAR'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_utility_tab_object_data(ToolsystemPanel):
    bl_label = "Object Data"
    bl_category = "Utility"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.make_single_user", icon='MAKE_SINGLE_USER'),
            MenuEntry("VIEW3D_MT_make_links", icon='LINK_DATA'),
            Separator,
            OperatorEntry("object.make_local", icon='MAKE_LOCAL'),
            OperatorEntry("object.make_override_library", icon='LIBRARY_DATA_OVERRIDE'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_utility_tab_assets(ToolsystemPanel):
    bl_label = "Assets"
    bl_category = "Utility"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("asset.mark", icon='ASSET_MANAGER'),
            OperatorEntry("asset.clear", icon='CLEAR', props={"set_fake_user": False}),
            create_wizard_entry(context.object, "Open Asset Wizard", 'WIZARD'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_utility_tab_constraints(ToolsystemPanel):
    bl_label = "Constraints"
    bl_category = "Utility"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.constraint_add_with_targets", icon='CONSTRAINT_DATA'),
            OperatorEntry("object.constraints_copy", icon='COPYDOWN'),
            OperatorEntry("object.constraints_clear", icon='CLEAR_CONSTRAINT'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_utility_tab_collection(ToolsystemPanel):
    bl_label = "Collection"
    bl_category = "Utility"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("object.move_to_collection", icon='GROUP'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_utility_tab_convert(ToolsystemPanel):
    bl_label = "Convert"
    bl_category = "Utility"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'OBJECT', 'EDIT_MESH', 'EDIT_ARMATURE', 'EDIT_SURFACE', 'EDIT_CURVE', 'EDIT_LATTICE', 'EDIT_METABALL', 'EDIT_CURVES'}

    def draw(self, context):
        layout = self.layout

        obj = context.active_object
        is_old_gpencil = obj and obj.type == 'GPENCIL' and context.gpencil_data
        is_hair = obj and obj.type == 'CURVES'

        if is_old_gpencil:
            entries = (
                # TODO - Remove legacy operators
                OperatorEntry("gpencil.convert", text="Path", icon='CURVE_PATH', props={"type": 'PATH'}),
                OperatorEntry("gpencil.convert", text="Bézier Curve", icon='OUTLINER_OB_CURVE', props={"type": 'CURVE'}),
                OperatorEntry("gpencil.convert", text="Polygon Curve", icon='MESH_DATA', props={"type": 'POLY'}),
                OperatorEntry("curves.convert_to_particle_system", text="Particle System", icon='PARTICLE_DATA', poll=is_hair),
            )
        else:
            entries = (
                OperatorEntry("object.convert", text="Mesh", icon='OUTLINER_OB_MESH', props={"target": 'MESH'}),
                OperatorEntry("object.convert", text="Curve", icon='OUTLINER_OB_CURVE', props={"target": 'CURVE'}),
                OperatorEntry("object.convert", text="Curves", icon='OUTLINER_OB_CURVES', props={"target": 'CURVES'}),
                OperatorEntry("object.convert", text="Point Cloud", icon='OUTLINER_OB_POINTCLOUD', props={"target": 'POINTCLOUD'}),
                OperatorEntry("object.convert", text="Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL', props={"target": 'GREASEPENCIL'}),
                OperatorEntry("curves.convert_to_particle_system", text="Particle System", icon='PARTICLE_DATA', poll=is_hair),
            )

        draw_entries(layout, context, entries)


# -------------------------------------- Mesh

class VIEW3D_PT_mesh_tab_merge(ToolsystemPanel):
    bl_label = "Merge"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        edit_obj = context.edit_object

        first_sel_is_vert = False
        last_sel_is_vert = False

        if edit_obj and edit_obj.type == "MESH":
            mesh = bmesh.from_edit_mesh(edit_obj.data)
            if "VERT" in mesh.select_mode:
                if len(mesh.select_history) >= 1:
                    first_sel_is_vert = isinstance(mesh.select_history[0], bmesh.types.BMVert)
                    last_sel_is_vert = isinstance(mesh.select_history[-1], bmesh.types.BMVert)

        entries = (
            OperatorEntry("mesh.merge", text="At Center", icon='MERGE_CENTER', props={"type": 'CENTER'}),
            OperatorEntry("mesh.merge", text="At Cursor", icon='MERGE_CURSOR', props={"type": 'CURSOR'}),
            OperatorEntry("mesh.merge", text="At First", icon='MERGE_AT_FIRST', props={"type": 'FIRST'}, poll=first_sel_is_vert),
            OperatorEntry("mesh.merge", text="At Last", icon='MERGE_AT_LAST', props={"type": 'LAST'}, poll=last_sel_is_vert),
            OperatorEntry("mesh.merge", text="Collapse", icon='MERGE', props={"type": 'COLLAPSE'}),
            Separator,
            OperatorEntry("mesh.remove_doubles", text="By Distance", icon='REMOVE_DOUBLES'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mesh_tab_split(ToolsystemPanel):
    bl_label = "Split"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mesh.split", text="Selection", icon='SPLIT'),
            OperatorEntry("mesh.edge_split", text="Faces by Edges", icon='SPLITEDGE', props={"type":'EDGE'}),
            OperatorEntry("mesh.edge_split", text="Faces/Edges by Vertices", icon='SPLIT_BYVERTICES', props={"type":'VERT'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mesh_tab_separate(ToolsystemPanel):
    bl_label = "Separate"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mesh.separate", text="Selection", icon='SEPARATE', props={"type": 'SELECTED'}),
            OperatorEntry("mesh.separate", text="By Material", icon='SEPARATE_BYMATERIAL', props={"type": 'MATERIAL'}),
            OperatorEntry("mesh.separate", text="By Loose Parts", icon='SEPARATE_LOOSE', props={"type": 'LOOSE'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mesh_tab_tools(ToolsystemPanel):
    bl_label = "Tools"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        
        from math import pi
        with_bullet = bpy.app.build_options.bullet

        entries = (
            OperatorEntry("mesh.extrude_repeat", icon='REPEAT'),
            OperatorEntry("mesh.spin", icon='SPIN', props={"angle": pi * 2}),
            Separator,
            OperatorEntry("mesh.knife_project", icon='KNIFE_PROJECT'),
            OperatorEntry("mesh.convex_hull", icon='CONVEXHULL', poll=with_bullet),
            Separator,
            OperatorEntry("mesh.symmetrize", icon='SYMMETRIZE', text="Symmetrize"),
            OperatorEntry("mesh.symmetry_snap", icon='SNAP_SYMMETRY'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mesh_tab_normals(ToolsystemPanel):
    bl_label = "Normals"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mesh.normals_make_consistent", text="Recalculate Outside", icon='RECALC_NORMALS', props={"inside": False}),
            OperatorEntry("mesh.normals_make_consistent", text="Recalculate Inside", icon='RECALC_NORMALS_INSIDE', props={"inside": True}),
            OperatorEntry("mesh.flip_normals", text="Flip", icon='FLIP_NORMALS'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mesh_tab_shading(ToolsystemPanel):
    bl_label = "Shading"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mesh.faces_shade_smooth", icon='SHADING_SMOOTH'),
            OperatorEntry("mesh.faces_shade_flat", icon='SHADING_FLAT'),
            Separator,
            OperatorEntry("mesh.mark_sharp", text="Smooth Edges", icon='SHADING_EDGE_SMOOTH', props={"clear": True}),
            OperatorEntry("mesh.mark_sharp", text="Sharp Edges", icon='SHADING_EDGE_SHARP'),
            Separator,
            OperatorEntry("mesh.mark_sharp", text="Smooth Vertices", icon='SHADING_VERT_SMOOTH', props={"use_verts": True, "clear": True}),
            OperatorEntry("mesh.mark_sharp", text="Sharp Vertices", icon='SHADING_VERT_SHARP', props={"use_verts": True}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mesh_tab_cleanup(ToolsystemPanel):
    bl_label = "Clean Up"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mesh.delete_loose", icon='DELETE'),
            Separator,
            OperatorEntry("mesh.decimate", icon='DECIMATE'),
            OperatorEntry("mesh.dissolve_degenerate", icon='DEGENERATE_DISSOLVE'),
            OperatorEntry("mesh.dissolve_limited", icon='DISSOLVE_LIMITED'),
            OperatorEntry("mesh.face_make_planar", icon='MAKE_PLANAR'),
            Separator,
            OperatorEntry("mesh.vert_connect_nonplanar", icon='SPLIT_NONPLANAR'),
            OperatorEntry("mesh.vert_connect_concave", icon='SPLIT_CONCAVE'),
            OperatorEntry("mesh.fill_holes", icon='FILL_HOLE'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mesh_tab_dissolve(ToolsystemPanel):
    bl_label = "Dissolve"
    bl_category = "Mesh"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mesh.dissolve_verts", icon='DISSOLVE_VERTS'),
            OperatorEntry("mesh.dissolve_edges", icon='DISSOLVE_EDGES'),
            OperatorEntry("mesh.dissolve_faces", icon='DISSOLVE_FACES'),
            Separator,
            OperatorEntry("mesh.dissolve_limited", icon='DISSOLVE_LIMITED'),
            OperatorEntry("mesh.dissolve_mode", icon='DISSOLVE_SELECTION'),
            Separator,
            OperatorEntry("mesh.edge_collapse", icon='EDGE_COLLAPSE'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_vertex_tab_vertex(ToolsystemPanel):
    bl_label = "Vertex"
    bl_category = "Vertex"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mesh.edge_face_add", text="Make Edge/Face", icon='MAKE_EDGEFACE'),
            OperatorEntry("mesh.vert_connect_path", text="Connect Vertex Path", icon='VERTEXCONNECTPATH'),
            OperatorEntry("mesh.vert_connect", text="Connect Vertex Pairs", icon='VERTEXCONNECT'),
            Separator,
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("mesh.vertices_smooth_laplacian", text="Smooth Laplacian", icon='SMOOTH_LAPLACIAN'),
            SetOperatorContext('INVOKE_REGION_WIN'),
            Separator,
            OperatorEntry("transform.vert_crease", icon='VERTEX_CREASE'),
            Separator,
            OperatorEntry("mesh.blend_from_shape", icon='BLENDFROMSHAPE'),
            OperatorEntry("mesh.shape_propagate_to_all", text="Propagate to Shapes", icon='SHAPEPROPAGATE'),
            Separator,
            OperatorEntry("object.vertex_parent_set", icon='VERTEX_PARENT'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_edge_tab_edge(ToolsystemPanel):
    bl_label = "Edge"
    bl_category = "Edge"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = [
            SetOperatorContext('INVOKE_REGION_WIN'),
            OperatorEntry("mesh.bridge_edge_loops", icon='BRIDGE_EDGELOOPS'),
            OperatorEntry("mesh.screw", icon='MOD_SCREW'),
            Separator,
            OperatorEntry("mesh.subdivide", icon='SUBDIVIDE_EDGES'),
            OperatorEntry("mesh.subdivide_edgering", icon='SUBDIV_EDGERING'),
            OperatorEntry("mesh.unsubdivide", icon='UNSUBDIVIDE'),
            Separator,
            OperatorEntry("mesh.edge_rotate", text="Rotate Edge CW", icon='ROTATECW', props={"use_ccw": False}),
            OperatorEntry("mesh.edge_rotate", text="Rotate Edge CCW", icon='ROTATECCW', props={"use_ccw": True}),
            Separator,
            OperatorEntry("transform.edge_crease", icon='CREASE'),
            OperatorEntry("transform.edge_bevelweight", icon='BEVEL'),
            Separator,
            OperatorEntry("mesh.mark_sharp", icon='MARKSHARPEDGES'),
            OperatorEntry("mesh.mark_sharp", text="Clear Sharp", icon='CLEARSHARPEDGES', props={"clear": True}),
            OperatorEntry("mesh.mark_sharp", text="Mark Sharp from Vertices", icon='MARKSHARPVERTS', props={"use_verts": True}),
            OperatorEntry("mesh.mark_sharp", text="Clear Sharp from Vertices", icon='CLEARSHARPVERTS', props={"use_verts": True, "clear": True}),
        ]

        if bpy.app.build_options.freestyle:
            entries.extend((
                Separator,
                OperatorEntry("mesh.mark_freestyle_edge", icon='MARK_FS_EDGE', props={"clear": False}),
                OperatorEntry("mesh.mark_freestyle_edge", text="Clear Freestyle Edge", icon='CLEAR_FS_EDGE', props={"clear": True}),
            ))

        draw_entries(layout, context, entries)


class VIEW3D_PT_face_tab_face(ToolsystemPanel):
    bl_label = "Face"
    bl_category = "Face"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            SetOperatorContext('INVOKE_REGION_WIN'),
            OperatorEntry("mesh.poke", icon='POKEFACES'),
            Separator,
            OperatorEntry("mesh.quads_convert_to_tris", icon='TRIANGULATE', props={"quad_method": 'BEAUTY', "ngon_method": 'BEAUTY'}),
            OperatorEntry("mesh.tris_convert_to_quads", icon='TRISTOQUADS'),
            OperatorEntry("mesh.solidify", text="Solidify Faces", icon='SOLIDIFY'),
            OperatorEntry("mesh.wireframe", icon='WIREFRAME'),
            Separator,
            OperatorEntry("mesh.fill", icon='FILL'),
            OperatorEntry("mesh.fill_grid", icon='GRIDFILL'),
            OperatorEntry("mesh.beautify_fill", icon='BEAUTIFY'),
            Separator,
            OperatorEntry("mesh.intersect", icon='INTERSECT'),
            OperatorEntry("mesh.intersect_boolean", icon='BOOLEAN_INTERSECT'),
            Separator,
            OperatorEntry("mesh.face_split_by_edges", icon='SPLITBYEDGES'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_uv_tab_uv(ToolsystemPanel):
    bl_label = "UV"
    bl_category = "UV"
    bl_context="mesh_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("uv.unwrap", text="Unwrap Angle Based", icon='UNWRAP_ABF', props={"method": 'ANGLE_BASED'}),
            OperatorEntry("uv.unwrap", text="Unwrap Conformal", icon='UNWRAP_LSCM', props={"method": 'CONFORMAL'}),
            OperatorEntry("uv.unwrap", text="Unwrap Minimum Stretch", icon='UNWRAP_MINSTRETCH', props={"method": 'MINIMUM_STRETCH'}),
            Separator,
            SetOperatorContext('INVOKE_DEFAULT'),
            OperatorEntry("uv.smart_project", icon='MOD_UVPROJECT'),
            OperatorEntry("uv.lightmap_pack", icon='LIGHTMAPPACK'),
            OperatorEntry("uv.follow_active_quads", icon='FOLLOWQUADS'),
            Separator,
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("uv.cube_project", icon='CUBEPROJECT'),
            OperatorEntry("uv.cylinder_project", icon='CYLINDERPROJECT'),
            OperatorEntry("uv.sphere_project", icon='SPHEREPROJECT'),
            Separator,
            SetOperatorContext('INVOKE_REGION_WIN'),
            OperatorEntry("uv.project_from_view", icon='PROJECTFROMVIEW', props={"scale_to_bounds": False}),
            OperatorEntry("uv.project_from_view", text="Project from View (Bounds)", icon='PROJECTFROMVIEW_BOUNDS', props={"scale_to_bounds": True}),
            Separator,
            OperatorEntry("mesh.mark_seam", icon='MARK_SEAM', props={"clear": False}),
            OperatorEntry("mesh.clear_seam", text="Clear Seam", icon='CLEAR_SEAM'),
            Separator,
            OperatorEntry("uv.reset", icon='RESET'),
        )

        draw_entries(layout, context, entries)


# Workaround to separate the tooltips
class MASK_MT_flood_fill_invert(bpy.types.Operator):
    """Inverts the mask"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.flood_fill_invert"        # unique identifier for buttons and menu items to reference.
    bl_label = "Invert Mask"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.mask_flood_fill(mode = 'INVERT')
        return {'FINISHED'}


# Workaround to separate the tooltips
class MASK_MT_flood_fill_fill(bpy.types.Operator):
    """Fills the mask"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.flood_fill_fill"        # unique identifier for buttons and menu items to reference.
    bl_label = "Fill Mask"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.mask_flood_fill(mode = 'VALUE', value = 1)
        return {'FINISHED'}


# Workaround to separate the tooltips
class MASK_MT_flood_fill_clear(bpy.types.Operator):
    """Clears the mask"""      # blender will use this as a tooltip for menu items and buttons.
    bl_idname = "mask.flood_fill_clear"        # unique identifier for buttons and menu items to reference.
    bl_label = "Clear Mask"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.paint.mask_flood_fill(mode = 'VALUE', value = 0)
        return {'FINISHED'}


class VIEW3D_PT_sculpt_tab_transform(ToolsystemPanel):
    bl_label = "Transform"
    bl_category = "Sculpt"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sculpt.mesh_filter", text="Sphere", icon='SPHERE', props={"type": 'SPHERE'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_sculpt_tab_sculpt(ToolsystemPanel):
    bl_label = "Sculpt"
    bl_category = "Sculpt"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("paint.hide_show", text="Box Hide", icon='BOX_HIDE', props={"action": 'HIDE'}),
            OperatorEntry("paint.hide_show", text="Box Show", icon='BOX_SHOW', props={"action": 'SHOW'}),
            OperatorEntry("paint.hide_show_lasso_gesture", text="Lasso Hide", icon='LASSO_HIDE', props={"action": 'HIDE'}),
            OperatorEntry("paint.hide_show_lasso_gesture", text="Lasso Show", icon='LASSO_SHOW', props={"action": 'SHOW'}),
            OperatorEntry("sculpt.trim_box_gesture", text="Box Trim", icon='BOX_TRIM', props={"trim_mode": 'DIFFERENCE'}),
            OperatorEntry("sculpt.trim_lasso_gesture", text="Lasso Trim", icon='LASSO_TRIM', props={"trim_mode": 'DIFFERENCE'}),
            OperatorEntry("sculpt.trim_box_gesture", text="Box Add", icon='BOX_ADD', props={"trim_mode": 'JOIN'}),
            OperatorEntry("sculpt.trim_lasso_gesture", text="Lasso Add", icon='LASSO_ADD', props={"trim_mode": 'JOIN'}),
            Separator,
            OperatorEntry("sculpt.project_line_gesture", text="Line Project", icon='LINE_PROJECT'),
            OperatorEntry("sculpt.face_set_edit", text="Fair Positions", icon='POSITION', props={"mode": 'FAIR_POSITIONS'}),
            OperatorEntry("sculpt.face_set_edit", text="Fair Tangency", icon='NODE_TANGENT', props={"mode": 'FAIR_TANGENCY'}),
            Separator,
            OperatorEntry("sculpt.sample_color", text="Sample Color", icon='EYEDROPPER'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_sculpt_tab_filters(ToolsystemPanel):
    bl_label = "Filter"
    bl_category = "Sculpt"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sculpt.mesh_filter", text="Smooth", icon='PARTICLEBRUSH_SMOOTH', props={"type": 'SMOOTH'}),
            OperatorEntry("sculpt.mesh_filter", text="Surface Smooth", icon='SURFACE_SMOOTH', props={"type": 'SURFACE_SMOOTH'}),
            OperatorEntry("sculpt.mesh_filter", text="Inflate", icon='INFLATE', props={"type": 'INFLATE'}),
            OperatorEntry("sculpt.mesh_filter", text="Relax Topology", icon='RELAX_TOPOLOGY', props={"type": 'RELAX'}),
            OperatorEntry("sculpt.mesh_filter", text="Relax Face Sets", icon='RELAX_FACE_SETS', props={"type": 'RELAX_FACE_SETS'}),
            OperatorEntry("sculpt.mesh_filter", text="Sharpen", icon='SHARPEN', props={"type": 'SHARPEN'}),
            OperatorEntry("sculpt.mesh_filter", text="Enhance Details", icon='ENHANCE', props={"type": 'ENHANCE_DETAILS'}),
            OperatorEntry("sculpt.mesh_filter", text="Erase Multires Displacement", icon='DELETE', props={"type": 'ERASE_DISPLACEMENT'}),
            OperatorEntry("sculpt.mesh_filter", text="Randomize", icon='RANDOMIZE', props={"type": 'RANDOM'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_sculpt_tab_set_pivot(ToolsystemPanel):
    bl_label = "Set Pivot"
    bl_category = "Sculpt"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}



    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sculpt.set_pivot_position", text="Pivot to Origin", icon='PIVOT_TO_ORIGIN', props={"mode": 'ORIGIN'}),
            OperatorEntry("sculpt.set_pivot_position", text="Pivot to Unmasked", icon='PIVOT_TO_UNMASKED', props={"mode": 'UNMASKED'}),
            OperatorEntry("sculpt.set_pivot_position", text="Pivot to Mask Border", icon='PIVOT_TO_MASKBORDER', props={"mode": 'BORDER'}),
            OperatorEntry("sculpt.set_pivot_position", text="Pivot to Active Vertex", icon='PIVOT_TO_ACTIVE_VERT', props={"mode": 'ACTIVE'}),
            OperatorEntry("sculpt.set_pivot_position", text="Pivot to Surface Under Cursor", icon='PIVOT_TO_SURFACE', props={"mode": 'SURFACE'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mask_tab_mask(ToolsystemPanel):
    bl_label = "Mask"
    bl_category = "Mask"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("mask.flood_fill_invert", text="Invert Mask", icon='INVERT_MASK'),
            OperatorEntry("mask.flood_fill_fill", text="Fill Mask", icon='FILL_MASK'),
            OperatorEntry("mask.flood_fill_clear", text="Clear Mask", icon='CLEAR_MASK'),
            Separator,
            OperatorEntry("sculpt.mask_filter", text='Smooth Mask', icon='PARTICLEBRUSH_SMOOTH', props={"filter_type": 'SMOOTH', "auto_iteration_count": True}),
            OperatorEntry("sculpt.mask_filter", text='Sharpen Mask', icon='SHARPEN', props={"filter_type": 'SHARPEN', "auto_iteration_count": True}),
            OperatorEntry("sculpt.mask_filter", text='Grow Mask', icon='SELECTMORE', props={"filter_type": 'GROW', "auto_iteration_count": True}),
            OperatorEntry("sculpt.mask_filter", text='Shrink Mask', icon='SELECTLESS', props={"filter_type": 'SHRINK', "auto_iteration_count": True}),
            OperatorEntry("sculpt.mask_filter", text='Increase Contrast', icon='INC_CONTRAST', props={"filter_type": 'CONTRAST_INCREASE', "auto_iteration_count": False}),
            OperatorEntry("sculpt.mask_filter", text='Decrease Contrast', icon='DEC_CONTRAST', props={"filter_type": 'CONTRAST_DECREASE', "auto_iteration_count": False}),
            Separator,
            OperatorEntry("sculpt.expand", text="Expand Mask by Topology", icon='MESH_DATA', props={"target": 'MASK', "falloff_type": 'GEODESIC', "invert": True}),
            OperatorEntry("sculpt.expand", text="Expand Mask by Curvature", icon='CURVE_DATA', props={"target": 'MASK', "falloff_type": 'NORMALS', "invert": False}),
            Separator,
            OperatorEntry("sculpt.paint_mask_extract", text="Mask Extract", icon='PACKAGE'),
            Separator,
            OperatorEntry("sculpt.paint_mask_slice", text="Mask Slice", icon='MASK_SLICE', props={"new_object": False}),
            OperatorEntry("sculpt.paint_mask_slice", text="Mask Slice and Fill Holes", icon='MASK_SLICE_FILL', props={"new_object": False}),
            OperatorEntry("sculpt.paint_mask_slice", text="Mask Slice to New Object", icon='MASK_SLICE_NEW'),
            Separator,
            OperatorEntry("sculpt.mask_from_cavity", text='Mask from Cavity', icon='DIRTY_VERTEX'),
            OperatorEntry("sculpt.mask_from_boundary", text="Mask from Mesh Boundary", icon='MASK_MESH_BOUNDARY', props={"settings_source": 'OPERATOR',"boundary_mode": 'MESH'}),
            OperatorEntry("sculpt.mask_from_boundary", text="Mask from Face Sets Boundary", icon='MASK_FACE_SETS_BOUNDARY', props={"settings_source": 'OPERATOR',"boundary_mode": "FACE_SETS"}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_mask_tab_random_mask(ToolsystemPanel):
    bl_label = "Random Mask"
    bl_category = "Mask"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sculpt.mask_init", text='Per Vertex', icon='SELECT_UNGROUPED_VERTS', props={"mode": 'RANDOM_PER_VERTEX'}),
            OperatorEntry("sculpt.mask_init", text='Per Face Set', icon='FACESEL', props={"mode": 'RANDOM_PER_FACE_SET'}),
            OperatorEntry("sculpt.mask_init", text='Per Loose Part', icon='SELECT_LOOSE', props={"mode": 'RANDOM_PER_LOOSE_PART'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_facesets_tab_facesets(ToolsystemPanel):
    bl_label = "Face Sets"
    bl_category = "Face Sets"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sculpt.face_sets_create", text='Face Set from Masked', icon='MASK_FACE_SETS', props={"mode": 'MASKED'}),
            OperatorEntry("sculpt.face_sets_create", text='Face Set from Visible', icon='MASK_FACE_SETS_VISIBLE', props={"mode": 'VISIBLE'}),
            OperatorEntry("sculpt.face_sets_create", text='Face Set from Edit Mode Selection', icon='EDITMODE_HLT', props={"mode": 'SELECTION'}),
            Separator,
            OperatorEntry("sculpt.face_set_edit", text='Grow Face Set', icon='SELECTMORE', props={"mode": 'GROW'}),
            OperatorEntry("sculpt.face_set_edit", text='Shrink Face Set', icon='SELECTLESS', props={"mode": 'SHRINK'}),
            Separator,
            OperatorEntry("sculpt.expand", text="Expand Face Set by Topology", icon='FACE_MAPS', 
                props={"target": 'FACE_SETS', "falloff_type": 'GEODESIC', "invert": False, "use_mask_preserve": False, "use_modify_active": False}
            ),
            OperatorEntry("sculpt.expand", text="Expand Active Face Set", icon='FACE_MAPS_ACTIVE', 
                props={"target": 'FACE_SETS', "falloff_type": 'BOUNDARY_FACE_SET', "invert": False, "use_mask_preserve": False, "use_modify_active": True}
            ),
            Separator,
            OperatorEntry("sculpt.face_set_change_visibility", text='Invert Visible Face Sets', icon='INVERT_MASK', props={"mode": 'TOGGLE'}),
            OperatorEntry("paint.hide_show_all", text='Show Active Face Set', icon='HIDE_OFF', props={"action": 'SHOW'}),
            Separator,
            OperatorEntry("sculpt.face_set_extract", text="Extract Face Set", icon='SEPARATE'),
            Separator,
            OperatorEntry("sculpt.face_sets_randomize_colors", text='Randomize Colors', icon='COLOR'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_facesets_tab_init_facesets(ToolsystemPanel):
    bl_label = "Initialize Face Sets"
    bl_category = "Face Sets"
    bl_context="sculpt_mode"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("sculpt.face_sets_init", text='By Loose Parts', icon='SELECT_LOOSE', props={"mode": 'LOOSE_PARTS'}),
            OperatorEntry("sculpt.face_sets_init", text='By Face Set Boundaries', icon='SELECT_BOUNDARY', props={"mode": 'FACE_SET_BOUNDARIES'}),
            OperatorEntry("sculpt.face_sets_init", text='By Materials', icon='MATERIAL_DATA', props={"mode": 'MATERIALS'}),
            OperatorEntry("sculpt.face_sets_init", text='By Normals', icon='RECALC_NORMALS', props={"mode": 'NORMALS'}),
            OperatorEntry("sculpt.face_sets_init", text='By UV Seams', icon='MARK_SEAM', props={"mode": 'UV_SEAMS'}),
            OperatorEntry("sculpt.face_sets_init", text='By Edge Creases', icon='CREASE', props={"mode": 'CREASES'}),
            OperatorEntry("sculpt.face_sets_init", text='By Edge Bevel Weight', icon='BEVEL', props={"mode": 'BEVEL_WEIGHT'}),
            OperatorEntry("sculpt.face_sets_init", text='By Sharp Edges', icon='SELECT_SHARPEDGES', props={"mode": 'SHARP_EDGES'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_paint_tab_paint(ToolsystemPanel):
    bl_label = "Paint"
    bl_category = "Paint"
    bl_context="vertexpaint"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("paint.vertex_color_set", icon='COLOR'),
            OperatorEntry("paint.vertex_color_smooth", icon='PARTICLEBRUSH_SMOOTH'),
            OperatorEntry("paint.vertex_color_dirt", icon='DIRTY_VERTEX'),
            OperatorEntry("paint.vertex_color_from_weight", icon='VERTCOLFROMWEIGHT'),
            Separator,
            OperatorEntry("paint.vertex_color_invert", text="Invert", icon='REVERSE_COLORS'),
            OperatorEntry("paint.vertex_color_levels", text="Levels", icon='LEVELS'),
            OperatorEntry("paint.vertex_color_hsv", text="Hue Saturation Value", icon='HUESATVAL'),
            OperatorEntry("paint.vertex_color_brightness_contrast", text="Bright/Contrast", icon='BRIGHTNESS_CONTRAST'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_paint_tab_color_picker(ToolsystemPanel):
    bl_label = "Color Picker"
    bl_category = "Paint"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'PAINT_VERTEX', 'PAINT_TEXTURE'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("paint.sample_color", text="Color Picker", icon='EYEDROPPER'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_weights_tab_weights(ToolsystemPanel):
    bl_label = "Weights"
    bl_category = "Weights"
    bl_context="weightpaint"
    bl_options = {'HIDE_BG'}
    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("paint.weight_from_bones", text="Assign Automatic from Bones", icon='BONE_DATA', props={"type": 'AUTOMATIC'}),
            OperatorEntry("paint.weight_from_bones", text="Assign from Bone Envelopes", icon='MOD_ENVELOPE', props={"type": 'ENVELOPES'}),
            Separator,
            OperatorEntry("object.vertex_group_normalize_all", text="Normalize All", icon='WEIGHT_NORMALIZE_ALL'),
            OperatorEntry("object.vertex_group_normalize", text="Normalize", icon='WEIGHT_NORMALIZE'),
            Separator,
            OperatorEntry("object.vertex_group_mirror", text="Mirror", icon='WEIGHT_MIRROR'),
            OperatorEntry("object.vertex_group_invert", text="Invert", icon='WEIGHT_INVERT'),
            OperatorEntry("object.vertex_group_clean", text="Clean", icon='WEIGHT_CLEAN'),
            Separator,
            OperatorEntry("object.vertex_group_quantize", text="Quantize", icon='WEIGHT_QUANTIZE'),
            OperatorEntry("object.vertex_group_levels", text="Levels", icon='WEIGHT_LEVELS'),
            OperatorEntry("object.vertex_group_smooth", text="Smooth", icon='WEIGHT_SMOOTH'),
            OperatorEntry("object.data_transfer", text="Transfer Weights", icon='WEIGHT_TRANSFER_WEIGHTS', props={"use_reverse_transfer": True, "data_type": 'VGROUP_WEIGHTS'}),
            OperatorEntry("object.vertex_group_limit_total", text="Limit Total", icon='WEIGHT_LIMIT_TOTAL'),
            Separator,
            OperatorEntry("paint.weight_set", icon='MOD_VERTEX_WEIGHT'),
        )

        draw_entries(layout, context, entries)


# ------------------------ Curve Edit Mode
class VIEW3D_PT_curve_tab_curve(ToolsystemPanel):
    bl_label = "Curve"
    bl_category = "Curve"
    bl_context="curve_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curve.split", icon='SPLIT'),
            OperatorEntry("curve.separate", icon='SEPARATE'),
            Separator,
            OperatorEntry("curve.cyclic_toggle", icon='TOGGLE_CYCLIC'),
            OperatorEntry("curve.decimate", icon='DECIMATE'),
            Separator,
            OperatorEntry("curve.dissolve_verts", icon='DISSOLVE_VERTS'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_curve_tab_control_points(ToolsystemPanel):
    bl_label = "Control Points"
    bl_category = "Control Points"
    bl_context="curve_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curve.extrude_move", text="Extrude Curve", icon='EXTRUDE_REGION'),
            Separator,
            OperatorEntry("curve.make_segment", icon='MAKE_CURVESEGMENT'),
            Separator,
            OperatorEntry("transform.tilt", icon='TILT'),
            OperatorEntry("curve.tilt_clear",icon='CLEAR_TILT'),
            Separator,
            OperatorEntry("curve.normals_make_consistent", icon='RECALC_NORMALS'),
            Separator,
            OperatorEntry("curve.smooth", icon='PARTICLEBRUSH_SMOOTH'),
            OperatorEntry("curve.smooth_weight", icon='SMOOTH_WEIGHT'),
            OperatorEntry("curve.smooth_radius", icon='SMOOTH_RADIUS'),
            OperatorEntry("curve.smooth_tilt", icon='SMOOTH_TILT'),
            Separator,
            OperatorEntry("object.vertex_parent_set", icon='VERTEX_PARENT'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_curve_tab_control_points_surface(ToolsystemPanel):
    bl_label = "Control Points"
    bl_category = "Control Points"
    bl_context="surface_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curve.extrude_move", text="Extrude Curve", icon='EXTRUDE_REGION'),
            Separator,
            OperatorEntry("curve.make_segment", icon='MAKE_CURVESEGMENT'),
            Separator,
            OperatorEntry("curve.smooth", icon='PARTICLEBRUSH_SMOOTH'),
            Separator,
            OperatorEntry("object.vertex_parent_set", icon='VERTEX_PARENT'),
        )

        draw_entries(layout, context, entries)


# ------------------------ Curves (Hair/Fur) Edit Mode
class VIEW3D_PT_curves_tab_edit_curves(ToolsystemPanel):
    bl_label = "Curves"
    bl_category = "Curves"
    bl_context="curves_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode == 'EDIT_CURVES'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curves.duplicate_move", icon='DUPLICATE'),
            Separator,
            OperatorEntry("curves.attribute_set", icon='NODE_ATTRIBUTE'),
            OperatorEntry("curves.cyclic_toggle", icon='TOGGLE_CYCLIC'),
            Separator,
            OperatorEntry("curves.separate", icon='SEPARATE'),
            OperatorEntry("curves.delete", icon='DELETE'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_curves_tab_edit_control_points(ToolsystemPanel):
    bl_label = "Control Points"
    bl_category = "Control Points"
    bl_context="curves_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode == 'EDIT_CURVES'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curves.extrude_move", text="Extrude Curve", icon='EXTRUDE_REGION'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_curves_tab_edit_segments(ToolsystemPanel):
    bl_label = "Segments"
    bl_category = "Segments"
    bl_context="curves_edit"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode == 'EDIT_CURVES'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curves.subdivide", text="Subdivide", icon='SUBDIVIDE_EDGES'),
            OperatorEntry("curves.switch_direction", text="Switch Direction", icon='SWITCH_DIRECTION'),
        )

        draw_entries(layout, context, entries)


# ------------------------ Curves (Hair/Fur) Sculpt Mode

class VIEW3D_PT_curves_tab_sculpt_curves(ToolsystemPanel):
    bl_label = "Curves"
    bl_category = "Curves"
    bl_context="curves_sculpt"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode == 'SCULPT_CURVES'

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curves.snap_curves_to_surface", text="Snap to Deformed Surface", icon='SNAP_SURFACE', props={"attach_mode": "DEFORM"}),
            OperatorEntry("curves.snap_curves_to_surface",text="Snap to Nearest Surface", icon='SNAP_TO_ADJACENT', props={"attach_mode": "NEAREST"}),
            Separator,
            OperatorEntry("curves.convert_to_particle_system", text="Convert to Particle System", icon='PARTICLES'),
        )

        draw_entries(layout, context, entries)


# ------------------------ Surface
class VIEW3D_PT_surface_tab_surface(ToolsystemPanel):
    bl_label = "Surface"
    bl_category = "Surface"
    bl_context="surface_edit"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curve.spin", icon='SPIN'),
            Separator,
            OperatorEntry("curve.split", icon='SPLIT'),
            OperatorEntry("curve.separate", icon='SEPARATE'),
            Separator,
            OperatorEntry("curve.cyclic_toggle", icon='TOGGLE_CYCLIC'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_segments_tab_segments(ToolsystemPanel):
    bl_label = "Segments"
    bl_category = "Segments"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        # curve and surface object in edit mode by poll, not by bl_context
        return view.show_toolshelf_tabs == True and context.mode in {'EDIT_SURFACE','EDIT_CURVE'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("curve.subdivide", icon='SUBDIVIDE_EDGES'),
            OperatorEntry("curve.switch_direction", icon='SWITCH_DIRECTION'),
        )

        draw_entries(layout, context, entries)


# ------------------------ Grease Pencil
class VIEW3D_PT_gp_gpencil_tab_dissolve(ToolsystemPanel):
    bl_label = "Dissolve"
    bl_context="grease_pencil_edit"
    bl_category = "Grease Pencil"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.dissolve", text="Dissolve", icon='DISSOLVE_VERTS', props={"type": 'POINTS'}),
            OperatorEntry("grease_pencil.dissolve", text="Dissolve Between", icon='DISSOLVE_BETWEEN', props={"type": 'BETWEEN'}),
            OperatorEntry("grease_pencil.dissolve", text="Dissolve Unselected", icon='DISSOLVE_UNSELECTED', props={"type": 'UNSELECT'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_gpencil_tab_cleanup(ToolsystemPanel):
    bl_label = "Clean Up"
    bl_context="grease_pencil_edit"
    bl_category = "Grease Pencil"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.clean_loose", text="Clean Loose Points", icon='DELETE_LOOSE'),
            OperatorEntry("grease_pencil.frame_clean_duplicate", text="Delete Duplicate Frames", icon='DELETE_DUPLICATE'),
            Separator,
            OperatorEntry("grease_pencil.stroke_merge_by_distance", text="Merge by Distance", icon='REMOVE_DOUBLES'),
            OperatorEntry("grease_pencil.reproject", text="Reproject Strokes", icon='REPROJECT'),
            OperatorEntry("grease_pencil.remove_fill_guides", icon='REMOVE_GUIDES'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_gpencil_tab_separate(ToolsystemPanel):
    bl_label = "Separate"
    bl_context="grease_pencil_edit"
    bl_category = "Grease Pencil"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.separate", text="Selection", icon='SEPARATE', props={"mode": 'SELECTED'}),
            OperatorEntry("grease_pencil.separate", text="By Material", icon='SEPARATE_BYMATERIAL', props={"mode": 'MATERIAL'}),
            OperatorEntry("grease_pencil.separate", text="By Layer", icon='SEPARATE_GP_STROKES', props={"mode": 'LAYER'}),
            Separator,
            OperatorEntry("grease_pencil.stroke_split", text="Split", icon='SPLIT'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_stroke_tab_stroke(ToolsystemPanel):
    bl_label = "Stroke"
    bl_context="grease_pencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.stroke_subdivide", text="Subdivide", icon='SUBDIVIDE_EDGES'),
            OperatorEntry("grease_pencil.stroke_subdivide_smooth", text="Subdivide and Smooth", icon='SUBDIVIDE_EDGES'),
            Separator,
            OperatorEntry("grease_pencil.stroke_simplify", text="Simplify (Fixed)", icon='MOD_SIMPLIFY', props={"mode": 'FIXED'}),
            OperatorEntry("grease_pencil.stroke_simplify", text="Simplify (Adaptive)", icon='SIMPLIFY_ADAPTIVE', props={"mode": 'ADAPTIVE'}),
            OperatorEntry("grease_pencil.stroke_simplify", text="Simplify (Sample)", icon='SIMPLIFY_SAMPLE', props={"mode": 'SAMPLE'}),
            OperatorEntry("grease_pencil.stroke_simplify", text="Simplify (Merge)", icon='MERGE', props={"mode": 'MERGE'}),
            Separator,
            OperatorEntry("grease_pencil.set_active_material", text="Set as Active Material", icon='MATERIAL'),
            Separator,
            OperatorEntry("grease_pencil.cyclical_set", text="Close", icon='TOGGLE_CLOSE', props={"type": 'CLOSE'}),
            OperatorEntry("grease_pencil.cyclical_set", text="Toggle Cyclic", icon='TOGGLE_CYCLIC', props={"type": 'TOGGLE'}),
            OperatorEntry("grease_pencil.stroke_switch_direction", text="Switch Direction", icon='FLIP'),
            Separator,
            OperatorEntry("grease_pencil.set_start_point", text="Set Start Point", icon='STARTPOINT'),
            OperatorEntry("grease_pencil.set_uniform_thickness", text="Normalize Thickness", icon='MOD_THICKNESS'),
            OperatorEntry("grease_pencil.set_uniform_opacity", text="Normalize Opacity", icon='MOD_OPACITY'),
            Separator,
            OperatorEntry("grease_pencil.set_curve_resolution", text="Set Curve Resolution", icon='SPLINE_RESOLUTION'),
        )

        draw_entries(layout, context, entries)


# BFA - Legacy
class VIEW3D_PT_gp_stroke_tab_simplify(ToolsystemPanel):
    bl_label = "Simplify"
    bl_context="grease_pencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.stroke_simplify", text="Fixed", icon='MOD_SIMPLIFY'),
            OperatorEntry("gpencil.stroke_simplify", text="Adaptative", icon='SIMPLIFY_ADAPTIVE'), # BFA - Legacy
            OperatorEntry("gpencil.stroke_sample", text="Sample", icon='SIMPLIFY_SAMPLE'), # BFA - Legacy
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_stroke_tab_toggle_caps(ToolsystemPanel):
    bl_label = "Set Caps"
    bl_context="grease_pencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.caps_set", text="Rounded", icon='TOGGLECAPS_DEFAULT', props={"type": 'ROUND'}),
            OperatorEntry("grease_pencil.caps_set", text="Flat", icon='TOGGLECAPS_BOTH', props={"type": 'FLAT'}),
            Separator,
            OperatorEntry("grease_pencil.caps_set", text="Toggle Start", icon='TOGGLECAPS_START', props={"type": 'START'}),
            OperatorEntry("grease_pencil.caps_set", text="Toggle End", icon='TOGGLECAPS_END', props={"type": 'END'}),
        )

        draw_entries(layout, context, entries)


# BFA - legacy
class VIEW3D_PT_gp_stroke_tab_reproject(ToolsystemPanel):
    bl_label = "Reproject Strokes"
    bl_context="grease_pencil_edit"
    bl_category = "Stroke"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("gpencil.reproject", text="Front", icon='VIEW_FRONT', props={"type": 'FRONT'}),
            OperatorEntry("gpencil.reproject", text="Side", icon='VIEW_LEFT', props={"type": 'SIDE'}),
            OperatorEntry("gpencil.reproject", text="Top", icon='VIEW_TOP', props={"type": 'TOP'}),
            OperatorEntry("gpencil.reproject", text="View", icon='VIEW', props={"type": 'VIEW'}),
            OperatorEntry("gpencil.reproject", text="Surface", icon='REPROJECT', props={"type": 'SURFACE'}),
            OperatorEntry("gpencil.reproject", text="Cursor", icon='CURSOR', props={"type": 'CURSOR'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_point_tab_point(ToolsystemPanel):
    bl_label = "Point"
    bl_context="grease_pencil_edit"
    bl_category = "Point"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.extrude_move", text="Extrude", icon='EXTRUDE_REGION'),
            OperatorEntry("grease_pencil.stroke_smooth", text="Smooth", icon='PARTICLEBRUSH_SMOOTH'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_draw_tab_draw(ToolsystemPanel):
    bl_label = "Draw"
    bl_context="greasepencil_paint"
    bl_category = "Draw"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("gpencil.interpolate", text="Interpolate", icon='INTERPOLATE'),
            OperatorEntry("gpencil.interpolate_sequence", text="Interpolate Sequence", icon='SEQUENCE'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_draw_tab_animation(ToolsystemPanel):
    bl_label = "Animation"
    bl_category = "Animation"
    bl_options = {'HIDE_BG'}

    # just show when the toolshelf tabs toggle in the view menu is on.
    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True and context.mode in {'PAINT_GPENCIL', 'PAINT_GREASE_PENCIL', 'EDIT_GREASE_PENCIL', 'SCULPT_GPENCIL', 'SCULPT_GREASE_PENCIL', 'VERTEX_GPENCIL'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("grease_pencil.insert_blank_frame", text="Insert Blank Keyframe (Active Layer)", icon='ADD'),
            OperatorEntry("grease_pencil.insert_blank_frame", text="Insert Blank Keyframe (All Layers)", icon='ADD_ALL', props={"all_layers": True}),
            Separator,
            OperatorEntry("grease_pencil.frame_duplicate", text="Duplicate Active Keyframe (Active Layer)", icon='DUPLICATE', props={"all": False}),
            OperatorEntry("grease_pencil.frame_duplicate", text="Duplicate Active Keyframe (All Layers)", icon='DUPLICATE_ALL', props={"all": True}),
            Separator,
            OperatorEntry("grease_pencil.active_frame_delete", text="Delete Active Keyframe (Active Layer)", icon='DELETE', props={"all": False}),
            OperatorEntry("grease_pencil.active_frame_delete", text="Delete Active Keyframes (All Layers)", icon='DELETE_ALL', props={"all": True}),
            Separator,
            OperatorEntry("grease_pencil.interpolate_sequence", text="Interpolate Sequence", icon='SEQUENCE', props={"use_selection": True}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_draw_tab_cleanup(ToolsystemPanel):
    bl_label = "Clean Up"
    bl_context="greasepencil_paint"
    bl_category = "Clean Up"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        ob = context.active_object

        entries = (
            OperatorEntry("gpencil.frame_clean_fill", text="Boundary Strokes", icon='CLEAN_CHANNELS', props={"mode": 'ACTIVE'}),
            OperatorEntry("gpencil.frame_clean_fill", text="Boundary Strokes all Frames", icon='CLEAN_CHANNELS_FRAMES', props={"mode": 'ALL'}),
            OperatorEntry("gpencil.frame_clean_loose", text="Delete Loose Points", icon='DELETE_LOOSE'),
            OperatorEntry("gpencil.frame_clean_duplicate", text="Delete Duplicated Frames", icon='DELETE_DUPLICATE'),
            OperatorEntry("gpencil.recalc_geometry", text="Recalculate Geometry", icon='FILE_REFRESH'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_weights_tab_weights(ToolsystemPanel):
    bl_label = "Weights"
    bl_context="greasepencil_weight"
    bl_category = "Weights"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("gpencil.vertex_group_normalize_all", text="Normalize All", icon='WEIGHT_NORMALIZE_ALL'),
            OperatorEntry("gpencil.vertex_group_normalize", text="Normalize", icon='WEIGHT_NORMALIZE'),
            Separator,
            OperatorEntry("gpencil.vertex_group_invert", text="Invert", icon='WEIGHT_INVERT'),
            OperatorEntry("gpencil.vertex_group_smooth", text="Smooth", icon='WEIGHT_SMOOTH'),
            Separator,
            OperatorEntry("gpencil.weight_sample", text="Sample Weight", icon='EYEDROPPER'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_weights_tab_generate_weights(ToolsystemPanel):
    bl_label = "Generate Weights"
    bl_context="greasepencil_weight"
    bl_category = "Weights"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("gpencil.generate_weights", text="With Empty Groups", icon='PARTICLEBRUSH_WEIGHT', props={"mode": 'NAME'}),
            OperatorEntry("gpencil.generate_weights", text="With Automatic Weights", icon='PARTICLEBRUSH_WEIGHT', props={"mode": 'AUTO'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_gp_paint_tab_paint(ToolsystemPanel):
    bl_label = "Paint"
    bl_context="greasepencil_vertex"
    bl_category = "Paint"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("gpencil.vertex_color_set", text="Set Vertex Color", icon='NODE_VERTEX_COLOR'),
            OperatorEntry("gpencil.stroke_reset_vertex_color", icon='RESET'),
            Separator,
            OperatorEntry("gpencil.vertex_color_invert", text="Invert", icon='NODE_INVERT'),
            OperatorEntry("gpencil.vertex_color_levels", text="Levels", icon='LEVELS'),
            OperatorEntry("gpencil.vertex_color_hsv", text="Hue Saturation Value", icon='HUESATVAL'),
            OperatorEntry("gpencil.vertex_color_brightness_contrast", text="Bright/Contrast", icon='BRIGHTNESS_CONTRAST'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_armature_tab_armature(ToolsystemPanel):
    bl_label = "Armature"
    bl_context="armature_edit"
    bl_category = "Armature"
    bl_options = {'HIDE_BG'}

    def draw(self, context):
        layout = self.layout
        armature = context.edit_object.data

        entries = (
            OperatorEntry("transform.transform", text="Set Bone Roll", icon='SET_ROLL', props={"mode": 'BONE_ROLL'}),
            OperatorEntry("armature.roll_clear", text="Clear Bone Roll", icon='CLEAR_ROLL'),
            Separator,
            OperatorEntry("armature.extrude_move", icon='EXTRUDE_REGION'),
            OperatorEntry("armature.extrude_forked", icon='EXTRUDE_REGION', poll=armature.use_mirror_x),
            OperatorEntry("armature.duplicate_move", icon='DUPLICATE'),
            OperatorEntry("armature.fill", icon='FILLBETWEEN'),
            Separator,
            OperatorEntry("armature.split", icon='SPLIT'),
            OperatorEntry("armature.separate", icon='SEPARATE'),
            OperatorEntry("armature.symmetrize", icon='SYMMETRIZE'),
            Separator,
            OperatorEntry("armature.subdivide", text="Subdivide", icon='SUBDIVIDE_EDGES'),
            OperatorEntry("armature.switch_direction", text="Switch Direction", icon='SWITCH_DIRECTION'),
            Separator,
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("armature.parent_set", text="Make Parent", icon='PARENT_SET'),
            OperatorEntry("armature.parent_clear", text="Clear Parent", icon='PARENT_CLEAR'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_armature_tab_recalc_bone_roll(ToolsystemPanel):
    bl_label = "Recalculate Bone Roll"
    bl_context="armature_edit"
    bl_category = "Armature"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        pass


class VIEW3D_PT_armature_tab_recalc_bone_roll_positive(ToolsystemPanel):
    bl_label = "Positive"
    bl_context = "armature_edit"
    bl_category = "Armature"
    bl_parent_id = "VIEW3D_PT_armature_tab_recalc_bone_roll"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("armature.calculate_roll", text= "Local + X Tangent", icon='ROLL_X_TANG_POS', props={"type": 'POS_X'}),
            OperatorEntry("armature.calculate_roll", text= "Local + Z Tangent", icon='ROLL_Z_TANG_POS', props={"type": 'POS_Z'}),
            OperatorEntry("armature.calculate_roll", text= "Global + X Axis", icon='ROLL_X_POS', props={"type": 'GLOBAL_POS_X'}),
            OperatorEntry("armature.calculate_roll", text= "Global + Y Axis", icon='ROLL_Y_POS', props={"type": 'GLOBAL_POS_Y'}),
            OperatorEntry("armature.calculate_roll", text= "Global + Z Axis", icon='ROLL_Z_POS', props={"type": 'GLOBAL_POS_Z'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_armature_tab_recalc_bone_roll_negative(ToolsystemPanel):
    bl_label = "Negative"
    bl_context = "armature_edit"
    bl_category = "Armature"
    bl_parent_id = "VIEW3D_PT_armature_tab_recalc_bone_roll"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("armature.calculate_roll", text= "Local - X Tangent", icon='ROLL_X_TANG_NEG', props={"type": 'NEG_X'}),
            OperatorEntry("armature.calculate_roll", text= "Local - Z Tangent", icon='ROLL_Z_TANG_NEG', props={"type": 'NEG_Z'}),
            OperatorEntry("armature.calculate_roll", text= "Global - X Axis", icon='ROLL_X_NEG', props={"type": 'GLOBAL_NEG_X'}),
            OperatorEntry("armature.calculate_roll", text= "Global - Y Axis", icon='ROLL_Y_NEG', props={"type": 'GLOBAL_NEG_Y'}),
            OperatorEntry("armature.calculate_roll", text= "Global - Z Axis", icon='ROLL_Z_NEG', props={"type": 'GLOBAL_NEG_Z'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_armature_tab_recalc_bone_roll_other(ToolsystemPanel):
    bl_label = "Other"
    bl_context = "armature_edit"
    bl_category = "Armature"
    bl_parent_id = "VIEW3D_PT_armature_tab_recalc_bone_roll"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        view = context.space_data
        return view.show_toolshelf_tabs == True

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("armature.calculate_roll", text= "Active Bone", icon='BONE_DATA', props={"type": 'ACTIVE'}),
            OperatorEntry("armature.calculate_roll", text= "View Axis", icon='MANIPUL', props={"type": 'VIEW'}),
            OperatorEntry("armature.calculate_roll", text= "Cursor", icon='CURSOR', props={"type": 'CURSOR'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_armature_tab_names(ToolsystemPanel):
    bl_label = "Names"
    bl_context="armature_edit"
    bl_category = "Armature"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("armature.autoside_names", text="Auto-Name Left/Right", icon='RENAME_X', props={"type": 'XAXIS'}),
            OperatorEntry("armature.autoside_names", text="Auto-Name Front/Back", icon='RENAME_Y', props={"type": 'YAXIS'}),
            OperatorEntry("armature.autoside_names", text="Auto-Name Top/Bottom", icon='RENAME_Z', props={"type": 'ZAXIS'}),
            OperatorEntry("armature.flip_names", icon='FLIP'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_pose(ToolsystemPanel):
    bl_label = "Pose"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.quaternions_flip", icon='FLIP'),
            Separator,
            SetOperatorContext('INVOKE_AREA'),
            OperatorEntry("armature.move_to_collection", text="Change Bone Layers", icon='GROUP_BONE'),
            Separator,
            OperatorEntry("poselib.create_pose_asset", text="Create Pose Asset", icon='ASSET_MANAGER'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_clear_transform(ToolsystemPanel):
    bl_label = "Clear Transform"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.transforms_clear", text="All", icon='CLEAR'),
            OperatorEntry("pose.user_transforms_clear", icon='NODE_TRANSFORM_CLEAR'),
            Separator,
            OperatorEntry("pose.loc_clear", text="Location", icon='CLEARMOVE'),
            OperatorEntry("pose.rot_clear", text="Rotation", icon='CLEARROTATE'),
            OperatorEntry("pose.scale_clear", text="Scale", icon='CLEARSCALE'),
            Separator,
            OperatorEntry("pose.user_transforms_clear", text="Reset Unkeyed", icon='RESET'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_apply(ToolsystemPanel):
    bl_label = "Apply"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.armature_apply", icon='MOD_ARMATURE'),
            OperatorEntry("pose.armature_apply", text="Apply Selected as Rest Pose", icon='MOD_ARMATURE_SELECTED', props={"selected": True}),
            OperatorEntry("pose.visual_transform_apply", icon='APPLYMOVE'),
            Separator,
            OperatorEntry("object.assign_property_defaults", icon='ASSIGN', props={"process_bones": True}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_inbetweens(ToolsystemPanel):
    bl_label = "In-Betweens"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.blend_with_rest", icon='PUSH_POSE'),
            OperatorEntry("pose.push", icon='POSE_FROM_BREAKDOWN'),
            OperatorEntry("pose.relax", icon='POSE_RELAX_TO_BREAKDOWN'),
            OperatorEntry("pose.breakdown", icon='BREAKDOWNER_POSE'),
            OperatorEntry("pose.blend_to_neighbor", icon='BLEND_TO_NEIGHBOUR'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_propagate(ToolsystemPanel):
    bl_label = "Propagate"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.propagate", text="To Next Keyframe", icon='PROPAGATE_NEXT', props={"mode": 'NEXT_KEY'}),
            OperatorEntry("pose.propagate", text="To Last Keyframe (Make Cyclic)", icon='PROPAGATE_PREVIOUS', props={"mode": 'LAST_KEY'}),
            Separator,
            OperatorEntry("pose.propagate", text="On Selected Keyframes", icon='PROPAGATE_SELECTED', props={"mode": 'SELECTED_KEYS'}),
            Separator,
            OperatorEntry("pose.propagate", text="On Selected Markers", icon='PROPAGATE_MARKER', props={"mode": 'SELECTED_MARKERS'}),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_motion_paths(ToolsystemPanel):
    bl_label = "Motion Paths"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.paths_calculate", text="Calculate", icon='MOTIONPATHS_CALCULATE'),
            OperatorEntry("pose.paths_clear", text="Clear", icon='MOTIONPATHS_CLEAR'),
            OperatorEntry("pose.paths_update", text="Update Armature Motion Paths", icon='MOTIONPATHS_UPDATE'),
            OperatorEntry("object.paths_update_visible", text="Update All Motion Paths", icon='MOTIONPATHS_UPDATE_ALL'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_ik(ToolsystemPanel):
    bl_label = "IK"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.ik_add", icon='ADD_IK'),
            OperatorEntry("pose.ik_clear", icon='CLEAR_IK'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_constraints(ToolsystemPanel):
    bl_label = "Constraints"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            OperatorEntry("pose.constraint_add_with_targets", icon='CONSTRAINT_DATA'),
            OperatorEntry("pose.constraints_copy", icon='COPYDOWN'),
            Separator,
            OperatorEntry("pose.constraints_clear", icon='CLEAR_CONSTRAINT'),
        )

        draw_entries(layout, context, entries)


class VIEW3D_PT_pose_tab_names(ToolsystemPanel):
    bl_label = "Names"
    bl_context="posemode"
    bl_category = "Pose"
    bl_options = {'HIDE_BG', 'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        entries = (
            SetOperatorContext('EXEC_REGION_WIN'),
            OperatorEntry("pose.autoside_names", text="Auto-Name Left/Right", icon='RENAME_X', props={"axis": 'XAXIS'}),
            OperatorEntry("pose.autoside_names", text="Auto-Name Front/Back", icon='RENAME_Y', props={"axis": 'YAXIS'}),
            OperatorEntry("pose.autoside_names", text="Auto-Name Top/Bottom", icon='STRING', props={"axis": 'ZAXIS'}),
            OperatorEntry("pose.flip_names", icon='FLIP'),
        )

        draw_entries(layout, context, entries)


classes = (
    # Object
    VIEW3D_PT_object_tab_transform,
    VIEW3D_PT_object_tab_set_origin,
    VIEW3D_PT_object_tab_mirror,
    VIEW3D_PT_object_tab_mirror_local,
    VIEW3D_PT_object_tab_clear,
    VIEW3D_PT_object_tab_apply,
    VIEW3D_PT_object_tab_apply_delta,
    VIEW3D_PT_object_tab_snap,
    VIEW3D_PT_object_tab_shading,

    # Utility
    VIEW3D_PT_utility_tab_parent,
    VIEW3D_PT_utility_tab_object_data,
    VIEW3D_PT_utility_tab_assets,
    VIEW3D_PT_utility_tab_constraints,
    VIEW3D_PT_utility_tab_collection,
    VIEW3D_PT_utility_tab_convert,

    # Mesh (Edit Mode)
    VIEW3D_PT_mesh_tab_merge,
    VIEW3D_PT_mesh_tab_split,
    VIEW3D_PT_mesh_tab_separate,
    VIEW3D_PT_mesh_tab_tools,
    VIEW3D_PT_mesh_tab_normals,
    VIEW3D_PT_mesh_tab_shading,
    VIEW3D_PT_mesh_tab_cleanup,
    VIEW3D_PT_mesh_tab_dissolve,
    VIEW3D_PT_vertex_tab_vertex,
    VIEW3D_PT_edge_tab_edge,
    VIEW3D_PT_face_tab_face,
    VIEW3D_PT_uv_tab_uv,

    # Mesh (Sculpt Mode)
    VIEW3D_PT_sculpt_tab_transform,
    VIEW3D_PT_sculpt_tab_sculpt,
    VIEW3D_PT_sculpt_tab_filters,
    VIEW3D_PT_sculpt_tab_set_pivot,
    VIEW3D_PT_mask_tab_mask,
    VIEW3D_PT_mask_tab_random_mask,
    VIEW3D_PT_facesets_tab_facesets,
    VIEW3D_PT_facesets_tab_init_facesets,

    # Mesh (Vertex Paint Mode)
    VIEW3D_PT_paint_tab_paint,
    VIEW3D_PT_paint_tab_color_picker,

    # Mesh (Weight Paint Mode)
    VIEW3D_PT_weights_tab_weights,

    # Curve (Edit Mode)
    VIEW3D_PT_curve_tab_curve,
    VIEW3D_PT_curve_tab_control_points,
    VIEW3D_PT_curve_tab_control_points_surface,
    VIEW3D_PT_surface_tab_surface,
    VIEW3D_PT_segments_tab_segments,

    # Curves [Hair/Fur] (Edit Mode)
    VIEW3D_PT_curves_tab_edit_curves,
    VIEW3D_PT_curves_tab_edit_control_points,
    VIEW3D_PT_curves_tab_edit_segments,

    # Curves [Hair/Fur] (Sculpt Mode)
    VIEW3D_PT_curves_tab_sculpt_curves,

    # Grease Pencil (Edit Mode)
    VIEW3D_PT_gp_gpencil_tab_dissolve,
    VIEW3D_PT_gp_gpencil_tab_cleanup,
    VIEW3D_PT_gp_gpencil_tab_separate,
    VIEW3D_PT_gp_stroke_tab_stroke,
    #VIEW3D_PT_gp_stroke_tab_simplify, # BFA - Legacy
    VIEW3D_PT_gp_stroke_tab_toggle_caps,
    #VIEW3D_PT_gp_stroke_tab_reproject, # BFA - Legacy
    VIEW3D_PT_gp_point_tab_point,

    # Grease Pencil (Draw Mode)
    VIEW3D_PT_gp_draw_tab_draw,
    VIEW3D_PT_gp_draw_tab_animation,
    VIEW3D_PT_gp_draw_tab_cleanup,

    # Grease Pencil (Weight Paint Mode)
    VIEW3D_PT_gp_weights_tab_weights,
    VIEW3D_PT_gp_weights_tab_generate_weights,

    # Grease Pencil (Vertex Paint Mode)
    VIEW3D_PT_gp_paint_tab_paint,

    # Armature (Edit Mode)
    VIEW3D_PT_armature_tab_armature,
    VIEW3D_PT_armature_tab_recalc_bone_roll,
    VIEW3D_PT_armature_tab_recalc_bone_roll_positive,
    VIEW3D_PT_armature_tab_recalc_bone_roll_negative,
    VIEW3D_PT_armature_tab_recalc_bone_roll_other,
    VIEW3D_PT_armature_tab_names,

    # Armature (Pose Mode)
    VIEW3D_PT_pose_tab_pose,
    VIEW3D_PT_pose_tab_clear_transform,
    VIEW3D_PT_pose_tab_apply,
    VIEW3D_PT_pose_tab_inbetweens,
    VIEW3D_PT_pose_tab_propagate,
    VIEW3D_PT_pose_tab_motion_paths,
    VIEW3D_PT_pose_tab_ik,
    VIEW3D_PT_pose_tab_constraints,
    VIEW3D_PT_pose_tab_names,

    # Operators - separated tooltips
    MASK_MT_flood_fill_invert,
    MASK_MT_flood_fill_fill,
    MASK_MT_flood_fill_clear,
    VIEW3D_MT_object_mirror_global_x,
    VIEW3D_MT_object_mirror_global_y,
    VIEW3D_MT_object_mirror_global_z,
    VIEW3D_MT_object_mirror_local_x,
    VIEW3D_MT_object_mirror_local_y,
    VIEW3D_MT_object_mirror_local_z,

)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
