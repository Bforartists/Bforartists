# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import os

from bpy.types import (
    Operator,
)


# -------------------------------------------------------------
#  Add a new scene and set to new strip
#
# -------------------------------------------------------------
class STORYPENCIL_OT_NewScene(Operator):
    bl_idname = "storypencil.new_scene"
    bl_label = "New Scene"
    bl_description = "Create a new scene base on template scene"
    bl_options = {'REGISTER', 'UNDO'}

    scene_name: bpy.props.StringProperty(default="Scene")
    num_strips: bpy.props.IntProperty(default=1, min=1, max=128, description="Number of scenes to add")

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        scene = context.scene
        scene_base = scene.storypencil_base_scene
        if scene_base is not None and scene_base.name in bpy.data.scenes:
            return True

        return False

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "scene_name", text="Scene Name")
        col.prop(self, "num_strips", text="Repeat")

    def format_to3(self, value):
        return f"{value:03}"

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        scene_prv = context.scene
        cfra_prv = scene_prv.frame_current
        scene_base = scene_prv.storypencil_base_scene
        repeat = self.num_strips

        offset = 0
        for i in range(repeat):
            # Set context to base scene and duplicate
            context.window.scene = scene_base
            bpy.ops.scene.new(type='FULL_COPY')
            scene_new = context.window.scene
            new_name = scene_prv.storypencil_name_prefix + \
                self.scene_name + scene_prv.storypencil_name_suffix
            id = 0
            while new_name in bpy.data.scenes:
                id += 1
                new_name = scene_prv.storypencil_name_prefix + self.scene_name + \
                    scene_prv.storypencil_name_suffix + '.' + self.format_to3(id)

            scene_new.name = new_name
            # Set duration of new scene
            scene_new.frame_end = scene_new.frame_start + \
                scene_prv.storypencil_scene_duration - 1

            # Back to original scene
            context.window.scene = scene_prv
            scene_prv.frame_current = cfra_prv
            bpy.ops.sequencer.scene_strip_add(
                frame_start=cfra_prv + offset, scene=scene_new.name)

            # Add offset for repeat
            offset += scene_new.frame_end - scene_new.frame_start + 1

            scene_new.update_tag()
            scene_prv.update_tag()

        return {"FINISHED"}


def draw_new_scene(self, context):
    """Add menu options."""

    self.layout.operator_context = 'INVOKE_REGION_WIN'
    row = self.layout.row(align=True)
    row.operator(STORYPENCIL_OT_NewScene.bl_idname, text="New Template Scene")


def setup_storyboard(self, context):
    """Add Setup menu option."""
    # For security, check if this is the default template.
    is_gpencil = context.active_object and context.active_object.name == 'Stroke'
    if is_gpencil and context.workspace.name in ('2D Animation', '2D Full Canvas') and context.scene.name == 'Scene':
        if "Video Editing" not in bpy.data.workspaces:
            row = self.layout.row(align=True)
            row.separator()
            row = self.layout.row(align=True)
            row.operator(STORYPENCIL_OT_Setup.bl_idname,
                         text="Setup Storyboard Session")


# -------------------------------------------------------------
#  Setup all environment
#
# -------------------------------------------------------------
class STORYPENCIL_OT_Setup(Operator):
    bl_idname = "storypencil.setup"
    bl_label = "Setup"
    bl_description = "Configure all settings for a storyboard session"
    bl_options = {'REGISTER', 'UNDO'}

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        return True

    def get_workspace(self, type):
        for wrk in bpy.data.workspaces:
            if wrk.name == type:
                return wrk

        return None

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        scene_base = context.scene
        # Create Workspace
        templatepath = None
        if "Video Editing" not in bpy.data.workspaces:
            template_path = None
            for path in bpy.utils.app_template_paths():
                template_path = path

            filepath = os.path.join(
                template_path, "Video_Editing", "startup.blend")
            bpy.ops.workspace.append_activate(
                idname="Video Editing", filepath=filepath)
        # Create New scene
        bpy.ops.scene.new()
        scene_edit = context.scene
        scene_edit.name = 'Edit'
        # Rename original base scene
        scene_base.name = 'Base'
        # Setup Edit scene settings
        scene_edit.storypencil_main_workspace = self.get_workspace(
            "Video Editing")
        scene_edit.storypencil_main_scene = scene_edit
        scene_edit.storypencil_base_scene = scene_base
        scene_edit.storypencil_edit_workspace = self.get_workspace(
            "2D Animation")

        # Add a new strip (need set the area context)
        context.window.scene = scene_edit
        area_prv = context.area.ui_type
        context.area.ui_type = 'SEQUENCE_EDITOR'
        prv_frame = scene_edit.frame_current

        scene_edit.frame_current = scene_edit.frame_start
        bpy.ops.storypencil.new_scene()

        context.area.ui_type = area_prv
        scene_edit.frame_current = prv_frame

        scene_edit.update_tag()
        bpy.ops.sequencer.reload()

        return {"FINISHED"}
