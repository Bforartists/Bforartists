# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

import bpy

from bfa_3Dsequencer.sync.core import get_sync_settings
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
        settings = get_sync_settings()

        # Master Scene prop
        self.layout.prop(settings, "master_scene", text="Master Scene:", icon="SEQ_STRIP_DUPLICATE")

#        # Operator to syncronize viewport
#        self.layout.operator("wm.timeline_sync_toggle", text="Synchronize Timeline to 3D View", icon="VIEW3D", depress=settings.enabled)

#        # Operator to update to active scene strip
#        self.layout.operator('sequencer.change_3d_view_scene', text='Toggle Active Scene Strip', icon="FILE_REFRESH")

def SEQUENCER_HT_Syncbutton(self, context):
    settings = get_sync_settings()
    self.layout.operator("wm.timeline_sync_toggle", text="Sync", icon="VIEW3D", depress=settings.enabled)

class SEQUENCER_PT_SyncPanelAdvancedSettings(bpy.types.Panel):
    """3D View Sync advanced settings Panel."""

    bl_label = "Advanced Settings"
    bl_parent_id = "SEQUENCER_PT_SyncPanel"
    bl_space_type = "SEQUENCE_EDITOR"
    bl_region_type = "UI"
    bl_category = "Sequencer"

    def draw(self, context):
        settings = get_sync_settings()
        self.layout.prop(settings, "keep_gpencil_tool_settings")
        self.layout.prop(settings, "bidirectional")
        self.layout.prop(settings, "use_preview_range")
        self.layout.prop(settings, "sync_all_windows")
        self.layout.prop(settings, "active_follows_playhead")

def SEQUENCER_OT_toggle_active(self, context):
    layout = self.layout
    layout.separator()

    strip = context.active_sequence_strip
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
