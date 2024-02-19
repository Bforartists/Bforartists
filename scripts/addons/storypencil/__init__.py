# SPDX-FileCopyrightText: 2022-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# ----------------------------------------------
# Define Addon info
# ----------------------------------------------
bl_info = {
    "name": "Storypencil - Storyboard Tools",
    "description": "Storyboard tools",
    "author": "Antonio Vazquez, Matias Mendiola, Daniel Martinez Lara, Rodrigo Blaas, Samuel Bernou",
    "version": (1, 1, 4),
    "blender": (3, 3, 0),
    "location": "",
    "warning": "",
    "category": "Sequencer",
}

# ----------------------------------------------
# Import modules
# ----------------------------------------------
if "bpy" in locals():
    import importlib

    importlib.reload(utils)
    importlib.reload(synchro)
    importlib.reload(dopesheet_overlay)
    importlib.reload(scene_tools)
    importlib.reload(sound)
    importlib.reload(render)
    importlib.reload(ui)
else:
    from . import utils
    from . import synchro
    from . import dopesheet_overlay
    from . import scene_tools
    from . import sound
    from . import render
    from . import ui

import bpy
from bpy.types import (
    Scene,
    WindowManager,
    WorkSpace,
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
    EnumProperty,
)

# --------------------------------------------------------------
# Register all operators, props and panels
# --------------------------------------------------------------
classes = (
    synchro.STORYPENCIL_PG_Settings,
    scene_tools.STORYPENCIL_OT_Setup,
    scene_tools.STORYPENCIL_OT_NewScene,
    synchro.STORYPENCIL_OT_WindowBringFront,
    synchro.STORYPENCIL_OT_WindowCloseOperator,
    synchro.STORYPENCIL_OT_SyncToggleSecondary,
    synchro.STORYPENCIL_OT_SetSyncMainOperator,
    synchro.STORYPENCIL_OT_AddSecondaryWindowOperator,
    synchro.STORYPENCIL_OT_Switch,
    synchro.STORYPENCIL_OT_TabSwitch,
    sound.STORYPENCIL_OT_duplicate_sound_in_edit_scene,
    render.STORYPENCIL_OT_RenderAction,
    ui.STORYPENCIL_PT_Settings,
    ui.STORYPENCIL_PT_ModePanel,
    ui.STORYPENCIL_PT_SettingsNew,
    ui.STORYPENCIL_PT_RenderPanel,
    ui.STORYPENCIL_PT_General,
)


def save_mode(self, context):
    wm = context.window_manager
    if context.scene.storypencil_mode == 'WINDOW':
        context.scene.storypencil_use_new_window = True
    else:
        context.scene.storypencil_use_new_window = False

    wm['storypencil_use_new_window'] = context.scene.storypencil_use_new_window
    # Close all secondary windows
    if context.scene.storypencil_use_new_window is False:
        c = context.copy()
        for win in context.window_manager.windows:
            # Don't close actual window
            if win == context.window:
                continue
            win_id = str(win.as_pointer())
            if win_id != wm.storypencil_settings.main_window_id and win.parent is None:
                c["window"] = win
                bpy.ops.wm.window_close(c)


addon_keymaps = []
def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is None:
        return
    km = kc.keymaps.new(name="Sequencer", space_type="SEQUENCE_EDITOR")
    kmi = km.keymap_items.new(
        idname="storypencil.tabswitch",
        type="TAB",
        value="PRESS",
        shift=False, ctrl=False, alt = False, oskey=False,
        )

    addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    register_keymaps()

    Scene.storypencil_scene_duration = IntProperty(
        name="Scene Duration",
        description="Default Duration for new Scene",
        default=48,
        min=1,
        soft_max=250,
    )

    Scene.storypencil_use_new_window = BoolProperty(name="Open in new window",
                                                    description="Use secondary main window to edit scenes",
                                                    default=False)

    Scene.storypencil_main_workspace = PointerProperty(type=WorkSpace,
                                                       description="Main Workspace used for editing Storyboard")
    Scene.storypencil_main_scene = PointerProperty(type=Scene,
                                                   description="Main Scene used for editing Storyboard")
    Scene.storypencil_edit_workspace = PointerProperty(type=WorkSpace,
                                                       description="Workspace used for changing drawings")

    Scene.storypencil_base_scene = PointerProperty(type=Scene,
                                                   description="Template Scene used for creating new scenes")

    Scene.storypencil_render_render_path = StringProperty(name="Output Path", subtype='FILE_PATH', maxlen=256,
                                                          description="Directory/name to save files")

    Scene.storypencil_name_prefix = StringProperty(name="Scene Name Prefix", maxlen=20, default="")

    Scene.storypencil_name_suffix = StringProperty(name="Scene Name Suffix", maxlen=20, default="")

    Scene.storypencil_render_onlyselected = BoolProperty(name="Render only Selected Strips",
                                                         description="Render only the selected strips",
                                                         default=True)

    Scene.storypencil_render_channel = IntProperty(name="Channel",
                                                   description="Channel to set the new rendered video",
                                                   default=5, min=1, max=128)

    Scene.storypencil_add_render_strip = BoolProperty(name="Import Rendered Strips",
                                                      description="Add a Strip with the render",
                                                      default=True)

    Scene.storypencil_render_step = IntProperty(name="Image Steps",
                                                description="Minimum frames number to generate images between keyframes (0 to disable)",
                                                default=0, min=0, max=128)

    Scene.storypencil_render_numbering = EnumProperty(name="Image Numbering",
                                                      items=(
                                                            ('FRAME', "Frame", "Use real frame number"),
                                                            ('CONSECUTIVE', "Consecutive", "Use sequential numbering"),
                                                            ),
                                                      description="Defines how frame is named")

    Scene.storypencil_add_render_byfolder = BoolProperty(name="Folder by Strip",
                                                         description="Create a separated folder for each strip",
                                                         default=True)

    Scene.storypencil_copy_sounds = BoolProperty(name="Copy Sounds",
                                                 description="Copy automatically the sounds from VSE to edit scene",
                                                 default=True)

    Scene.storypencil_mode = EnumProperty(name="Mode",
                                          items=(
                                                ('SWITCH', "Switch", "Use same window and switch scene"),
                                                ('WINDOW', "New Window", "Use a new window for editing"),
                                                ),
                                          update=save_mode,
                                          description="Defines how frame is named")
    Scene.storypencil_selected_scn_only = BoolProperty(name='Selected Scene Only',
                                                       default=False,
                                                       description='Selected Scenes only')
    Scene.storypencil_skip_sound_mute = BoolProperty(name='Ignore Muted Sound',
                                                     default=True,
                                                     description='Skip muted sound')

    WindowManager.storypencil_settings = PointerProperty(
        type=synchro.STORYPENCIL_PG_Settings,
        name="Storypencil settings",
        description="Storypencil tool settings",
    )

    # Append Handlers
    bpy.app.handlers.frame_change_post.append(synchro.on_frame_changed)
    bpy.app.handlers.load_post.append(synchro.sync_autoconfig)

    bpy.context.window_manager.storypencil_settings.active = False
    bpy.context.window_manager.storypencil_settings.main_window_id = ""
    bpy.context.window_manager.storypencil_settings.secondary_windows_ids = ""

    # UI integration in dopesheet header
    bpy.types.DOPESHEET_HT_header.append(synchro.draw_sync_header)
    dopesheet_overlay.register()

    synchro.sync_autoconfig()

    # UI integration in VSE header
    bpy.types.SEQUENCER_HT_header.remove(synchro.draw_sync_sequencer_header)
    bpy.types.SEQUENCER_HT_header.append(synchro.draw_sync_sequencer_header)

    bpy.types.SEQUENCER_MT_add.append(scene_tools.draw_new_scene)
    bpy.types.VIEW3D_MT_draw_gpencil.append(scene_tools.setup_storyboard)


def unregister():
    unregister_keymaps()

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    # Remove Handlers
    bpy.app.handlers.frame_change_post.remove(synchro.on_frame_changed)
    bpy.app.handlers.load_post.remove(synchro.sync_autoconfig)

    # remove UI integration
    bpy.types.DOPESHEET_HT_header.remove(synchro.draw_sync_header)
    dopesheet_overlay.unregister()
    bpy.types.SEQUENCER_HT_header.remove(synchro.draw_sync_sequencer_header)

    bpy.types.SEQUENCER_MT_add.remove(scene_tools.draw_new_scene)
    bpy.types.VIEW3D_MT_draw_gpencil.remove(scene_tools.setup_storyboard)

    del Scene.storypencil_scene_duration
    del WindowManager.storypencil_settings

    del Scene.storypencil_base_scene
    del Scene.storypencil_main_workspace
    del Scene.storypencil_main_scene
    del Scene.storypencil_edit_workspace

    del Scene.storypencil_render_render_path
    del Scene.storypencil_name_prefix
    del Scene.storypencil_name_suffix
    del Scene.storypencil_render_onlyselected
    del Scene.storypencil_render_channel
    del Scene.storypencil_render_step
    del Scene.storypencil_add_render_strip
    del Scene.storypencil_render_numbering
    del Scene.storypencil_add_render_byfolder
    del Scene.storypencil_copy_sounds
    del Scene.storypencil_mode
    del Scene.storypencil_selected_scn_only
    del Scene.storypencil_skip_sound_mute

if __name__ == '__main__':
    register()
