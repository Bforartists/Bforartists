# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

import bpy

from bfa_3Dsequencer.scene.core import (
    get_scene_cameras,
    get_valid_shot_scenes,
)

from bfa_3Dsequencer.sync.core import (
    get_sync_master_strip,
    get_sync_settings,
)

from bfa_3Dsequencer.utils import register_classes, unregister_classes


class DOPESHEET_PT_Sequence(bpy.types.Panel):
    bl_label = "Sequencer Sync"
    bl_space_type = 'DOPESHEET_EDITOR'
    bl_region_type = 'HEADER'
    bl_parent_id = "DOPESHEET_PT_view_view_options"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return get_sync_settings().enabled

    def draw(self, context: bpy.types.Context):
        self.layout.prop(
            context.window_manager.sequence_settings,
            "overlay_dopesheet",
            text="Scene Strip Overlay",
        )


class SEQUENCE_MT_active_shot_camera_select(bpy.types.Menu):
    bl_idname = "SHOT_MT_camera_select"
    bl_label = "Camera"
    bl_description = "Select active scene's camera"

    def draw(self, context):
        strip, _ = get_sync_master_strip(True)

        # Draw a menu entry foreach camera in the scene.
        for cam in get_scene_cameras(strip.scene):
            props = self.layout.operator(
                "sequence.active_shot_camera_set",
                text=cam.name,
                icon="OUTLINER_OB_CAMERA" if strip.scene_camera == cam else "NONE",
            )
            props.camera = cam.name


class SEQUENCE_MT_active_shot_scene_select(bpy.types.Menu):
    bl_idname = "SHOT_MT_scene_select"
    bl_label = "Scene"
    bl_description = "Select active scene"

    def draw(self, context):
        strip, _ = get_sync_master_strip(True)
        # Draw a menu entry for each valid scene.
        for scene in get_valid_shot_scenes():
            props = self.layout.operator(
                "sequence.active_shot_scene_set",
                text=scene.name,
                icon="SCENE_DATA" if strip.scene == scene else "NONE",
            )
            props.scene = scene.name


class SEQUENCE_UL_shot(bpy.types.UIList):
    bl_idname = "SEQUENCE_UL_shot"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        row = layout.row(align=True)
        subrow = row.row()

        subrow.prop(item, "name", text="", emboss=False)
        subrow.ui_units_x = 8

        icon = (
            "OUTLINER_OB_CAMERA"
            if item.scene_camera == context.scene.camera
            else "BLANK1"
        )
        camera_name = item.scene_camera.name if item.scene_camera else "Active"
        subrow = row.row(align=True)
        subrow.alignment = "EXPAND"
        subrow.label(text=camera_name, icon=icon)
        sub = row.row()
        icon = "SCENE_DATA" if item.scene == context.scene else "BLANK1"
        sub.alignment = "RIGHT"
        sub.label(text=item.scene.name, icon=icon)

    def filter_items(self, context, data, propname):
        objects = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        # Keep only scene strips.
        flt_flags = [
            self.bitflag_filter_item if isinstance(obj, bpy.types.Strip) else 0
            for obj in objects
        ]
        flt_neworder = []

        # Prepare data for sorting and perform sort
        sort_data = [(idx, obj.frame_final_start) for idx, obj in enumerate(objects)]
        flt_neworder = helper_funcs.sort_items_helper(sort_data, key=lambda obj: obj[1])

        return flt_flags, flt_neworder


class VIEW3D_PT_sequence(bpy.types.Panel):
    bl_label = "Sequencer Sync"
    bl_category = "View"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        master_scene = get_sync_settings().master_scene

        self.layout.prop(
            context.window_manager.timeline_sync_settings,
            "master_scene",
            text="Master Scene:",
            icon="SEQ_STRIP_DUPLICATE",
        )

        if (
            not master_scene
            or not master_scene.sequence_editor
            or not master_scene.sequence_editor.sequences
        ):
            self.layout.label(text="Set the Master Scene to sync from Sequencer", icon="QUESTION")
            return

        self.layout.label(text="Sequencer Scene Strips:")
        # Draw scene lists in the master sequence.
        self.draw_shots_list(context, master_scene.sequence_editor)
        # Draw active scene details if any.
        if strip := get_sync_master_strip(use_cache=True)[0]:
            self.draw_shot_strip(context, strip)

    def draw_shots_list(self, context, sed):
        """Draw scene list in the given sequence editor"""
        self.layout.template_list(
            SEQUENCE_UL_shot.bl_idname,
            "",
            sed,
            "sequences",
            context.window_manager.sequence_settings,
            "shot_active_index",
            type="DEFAULT",
            rows=4,
        )

    # Camera Sub Panels
    def draw_shot_strip(self, context, strip):
        """Draw scene strip details."""
        self.layout.label(text="Scene Strip Settings:")
        shot_box = self.layout.box()
        row = shot_box.row(align=True)
        row.label(text=strip.name, icon="SEQUENCE")

        # Scene selection.
        row.menu(
            SEQUENCE_MT_active_shot_scene_select.bl_idname,
            text=strip.scene.name,
            icon="SCENE_DATA",
        )
        row.operator("sequence.child_scene_setup_create", text="", icon="DUPLICATE")

        # Camera selection.
        col = shot_box.column()
        active_cam = context.scene.camera
        strip_cam = strip.scene_camera
        if not active_cam:
            text = "None"
            icon = "NONE"
        elif not strip_cam:
            text = "Active"
            icon = "NONE"
        else:
            text = (
                f"Active ({context.scene.camera.name})"
                if active_cam != strip_cam
                else strip.scene_camera.name
            )
            icon = "OUTLINER_OB_CAMERA" if active_cam == strip_cam else "CAMERA_DATA"


        row = col.row(align=True, heading="")
        row.label(text="Camera", icon="OUTLINER_DATA_CAMERA")

        row.menu(
            SEQUENCE_MT_active_shot_camera_select.bl_idname,
            text=text,
            icon=icon,
        )

        if not active_cam:
            row.operator("view3d.switchactivecamto", icon="VIEW_SWITCHACTIVECAM", text="")

        # Helper button to set strip camera to scene's active camera.
        if active_cam != strip_cam:
            row.operator("object.select_camera", icon="RESTRICT_SELECT_OFF", text="")
            props = row.operator(
                "sequence.active_shot_camera_set",
                icon="OUTLINER_OB_CAMERA",
                text="",
            )
            props.camera = context.scene.camera.name

        # Operator to remove camera
        if strip_cam:
            row.operator("object.select_camera", icon="RESTRICT_SELECT_OFF", text="")
            row.operator("sequence.active_shot_camera_none", icon="X", text="")


class PROPERTIES_PT_obj_users_scene_check(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_label = "Sequencer Usage"

    def draw(self, context):
        self.layout.operator("sequence.check_obj_users_scene", icon="TEXT")


classes = (
    DOPESHEET_PT_Sequence,
    SEQUENCE_MT_active_shot_camera_select,
    SEQUENCE_MT_active_shot_scene_select,
    SEQUENCE_UL_shot,
    VIEW3D_PT_sequence,
    PROPERTIES_PT_obj_users_scene_check,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
