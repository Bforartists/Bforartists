# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

import bpy

from bfa_3Dsequencer.sync.core import get_sync_settings
from bfa_3Dsequencer.sync.ops import SEQUENCER_OT_set_master_scene
from bfa_3Dsequencer.utils import register_classes, unregister_classes


class SEQUENCER_PT_SyncPanel(bpy.types.Panel):
    """3D View Sync Panel."""

    bl_label = "3D View Sync"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "View"

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False
        master_scene = get_sync_settings().master_scene

        settings = get_sync_settings()

        row = self.layout.row()
        row.label(text="Sync mode:")
        row.prop(settings, "sync_mode", text="")

        if settings.sync_mode == "LEGACY":
            # Master Scene prop
            row = self.layout.row(align=True)
            row.label(text="Synchronization Timeline:")
            self.layout.prop(context.window_manager.timeline_sync_settings, "master_scene", text="", icon="SEQ_STRIP_DUPLICATE",)

            if (
                not master_scene
                or not master_scene.sequence_editor
                or not master_scene.sequence_editor.strips
            ):
                # Button to set pinned scene as master
                row = self.layout.row(align=True)
                row.operator("sequencer.set_master_scene", text="Use Pinned Scene", icon="PINNED")

                self.layout.label(text="Set the Timeline", icon="QUESTION")
                self.layout.label(text="to sync from Sequencer", icon="NONE")
                return

    #        # Operator to syncronize viewport
    #        self.layout.operator("wm.timeline_sync_toggle", text="Synchronize Timeline to 3D View", icon="VIEW3D", depress=settings.enabled)

    #        # Operator to update to active scene strip
    #        self.layout.operator('sequencer.change_3d_view_scene', text='Toggle Active Scene Strip', icon="FILE_REFRESH")


def SEQUENCER_HT_Syncbutton(self, context):
    layout = self.layout

    master_scene = get_sync_settings().master_scene

    settings = get_sync_settings()

    if settings.sync_mode == "LEGACY":        
        if context.workspace.sequencer_scene:
            if (
                    context.workspace.sequencer_scene != master_scene
                ):
                row = layout.row(align=True)
                row.operator("sequencer.set_master_scene", text="Set Sync", icon='SEQ_STRIP_DUPLICATE')
            else:
                text = "Sync (Legacy)"
                row = layout.row(align=True)
                row.operator("wm.timeline_sync_toggle", text=text, icon="VIEW3D", depress=settings.is_sync())
                row.operator("sequencer.set_master_scene", text="", icon='SEQ_STRIP_DUPLICATE')
    else:
        text = "Sync"
        row = layout.row(align=True)
        row.operator("wm.timeline_sync_toggle", text=text, icon="VIEW3D", depress=settings.is_sync())


class SEQUENCER_PT_SyncPanelAdvancedSettings(bpy.types.Panel):
    """3D View Sync advanced settings Panel."""

    bl_label = "Advanced Settings"
    bl_parent_id = "SEQUENCER_PT_SyncPanel"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Sequencer"

    def draw(self, context):
        settings = get_sync_settings()
        if settings.sync_mode == "LEGACY":
            self.layout.prop(settings, "bidirectional")
        self.layout.prop(settings, "keep_gpencil_tool_settings")
        self.layout.prop(settings, "use_preview_range")
        self.layout.prop(settings, "sync_all_windows")
        self.layout.prop(settings, "active_follows_playhead")


def SEQUENCER_OT_toggle_active(self, context):
    layout = self.layout
    layout.separator()

    strip = context.active_strip
    # Operator to syncronize viewport
    #layout.operator('sequencer.change_3d_view_scene', text='Toggle Active Scene Strip', icon="FILE_REFRESH")
    try:
        layout.operator_context = 'INVOKE_REGION_WIN'
        if strip and strip.type == 'SCENE':
            layout.operator('sequencer.change_3d_view_scene', text='Toggle Active Scene Strip', icon="FILE_REFRESH")
        else:
            pass
    except:
        pass


classes = (
    SEQUENCER_PT_SyncPanel,
    SEQUENCER_PT_SyncPanelAdvancedSettings,
)


def register():
    register_classes(classes)
    bpy.types.SEQUENCER_MT_context_menu.append(SEQUENCER_OT_toggle_active)

    bpy.types.SEQUENCER_HT_header.append(SEQUENCER_HT_Syncbutton)


def unregister():
    unregister_classes(classes)
    bpy.types.SEQUENCER_MT_context_menu.remove(SEQUENCER_OT_toggle_active)

    bpy.types.SEQUENCER_HT_header.remove(SEQUENCER_HT_Syncbutton)
