# SPDX-License-Identifier: GPL-2.0-or-later

from typing import List, Sequence, Tuple

import bpy
import functools
import os
from bpy.app.handlers import persistent

from bpy.types import (
    Context,
    MetaSequence,
    Operator,
    PropertyGroup,
    SceneSequence,
    Window,
    WindowManager,
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    StringProperty,
)
from .scene_tools import STORYPENCIL_OT_NewScene
from .render import STORYPENCIL_OT_RenderAction
from .sound import delete_sounds, send_sound_to_strip_scene

def window_id(window: Window) -> str:
    """ Get Window's ID.

    :param window: the Window to consider
    :return: the Window's ID
    """
    return str(window.as_pointer())


def get_window_from_id(wm: WindowManager, win_id: str) -> Window:
    """Get a Window object from its ID (serialized ptr).

    :param wm: a WindowManager holding Windows
    :param win_id: the ID of the Window to get
    :return: the Window matching the given ID, None otherwise
    """
    return next((w for w in wm.windows if w and window_id(w) == win_id), None)


def get_main_windows_list(wm: WindowManager) -> Sequence[Window]:
    """Get all the Main Windows held by the given WindowManager `wm`"""
    return [w for w in wm.windows if w and w.parent is None]


def join_win_ids(ids: List[str]) -> str:
    """Join Windows IDs in a single string"""
    return ";".join(ids)


def split_win_ids(ids: str) -> List[str]:
    """Split a Windows IDs string into individual IDs"""
    return ids.split(";")


class STORYPENCIL_OT_SetSyncMainOperator(Operator):
    bl_idname = "storypencil.sync_set_main"
    bl_label = "Set as Sync Main"
    bl_description = "Set this Window as main for Synchronization"
    bl_options = {'INTERNAL'}

    win_id: bpy.props.StringProperty(
        name="Window ID",
        default="",
        options=set(),
        description="Main window ID",
    )

    def copy_settings(self, main_window, secondary_window):
        if main_window is None or secondary_window is None:
            return
        secondary_window.scene.storypencil_main_workspace = main_window.scene.storypencil_main_workspace
        secondary_window.scene.storypencil_main_scene = main_window.scene.storypencil_main_scene
        secondary_window.scene.storypencil_edit_workspace = main_window.scene.storypencil_edit_workspace

    def execute(self, context):
        options = context.window_manager.storypencil_settings
        options.main_window_id = self.win_id
        wm = bpy.context.window_manager
        scene = context.scene
        wm['storypencil_use_new_window'] = scene.storypencil_use_new_window

        main_windows = get_main_windows_list(wm)
        main_window = get_main_window(wm)
        secondary_window = get_secondary_window(wm)
        # Active sync
        options.active = True
        if secondary_window is None:
            # Open a new window
            if len(main_windows) < 2:
                bpy.ops.storypencil.create_secondary_window()
                secondary_window = get_secondary_window(wm)
                self.copy_settings(get_main_window(wm), secondary_window)
                return {'FINISHED'}
            else:
                # Reuse the existing window
                secondary_window = get_not_main_window(wm)
        else:
            # Open new secondary
            if len(main_windows) < 2:
                bpy.ops.storypencil.create_secondary_window()
                secondary_window = get_secondary_window(wm)
                self.copy_settings(get_main_window(wm), secondary_window)
                return {'FINISHED'}
            else:
                # Reuse the existing window
                secondary_window = get_not_main_window(wm)

        if secondary_window:
            enable_secondary_window(wm, window_id(secondary_window))
            win_id = window_id(secondary_window)
            self.copy_settings(get_main_window(wm), secondary_window)
            bpy.ops.storypencil.sync_window_bring_front(win_id=win_id)

        return {'FINISHED'}


class STORYPENCIL_OT_AddSecondaryWindowOperator(Operator):
    bl_idname = "storypencil.create_secondary_window"
    bl_label = "Create Secondary Window"
    bl_description = "Create a Secondary Main Window and enable Synchronization"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        # store existing windows
        windows = set(context.window_manager.windows[:])
        bpy.ops.wm.window_new_main()
        # get newly created window by comparing to previous list
        new_window = (set(context.window_manager.windows[:]) - windows).pop()
        # activate sync system and enable sync for this window
        toggle_secondary_window(context.window_manager, window_id(new_window))
        context.window_manager.storypencil_settings.active = True
        # trigger initial synchronization to open the current Sequence's Scene
        on_frame_changed()
        # Configure the new window
        self.configure_new_secondary_window(context, new_window)

        return {'FINISHED'}

    def configure_new_secondary_window(self, context, new_window):
        wrk_name = context.scene.storypencil_edit_workspace.name
        # Open the 2D workspace
        blendpath = os.path.dirname(bpy.app.binary_path)
        version = bpy.app.version
        version_full = str(version[0]) + '.' + str(version[1])
        template = os.path.join("scripts", "startup",
                                "bl_app_templates_system")
        template = os.path.join(template, wrk_name, "startup.blend")
        template_path = os.path.join(blendpath, version_full, template)
        # Check if workspace exist and add it if missing
        for wk in bpy.data.workspaces:
            if wk.name == wrk_name:
                new_window.workspace = wk
                return
        with context.temp_override(window=new_window):
            bpy.ops.workspace.append_activate(context, idname=wrk_name, filepath=template_path)


class STORYPENCIL_OT_WindowBringFront(Operator):
    bl_idname = "storypencil.sync_window_bring_front"
    bl_label = "Bring Window Front"
    bl_description = "Bring a Window to Front"
    bl_options = {'INTERNAL'}

    win_id: bpy.props.StringProperty()

    def execute(self, context):
        win = get_window_from_id(context.window_manager, self.win_id)
        if not win:
            return {'CANCELLED'}
        with context.temp_override(window=win):
            bpy.ops.wm.window_fullscreen_toggle()
            bpy.ops.wm.window_fullscreen_toggle()
        return {'FINISHED'}


class STORYPENCIL_OT_WindowCloseOperator(Operator):
    bl_idname = "storypencil.close_secondary_window"
    bl_label = "Close Window"
    bl_description = "Close a specific Window"
    bl_options = {'INTERNAL'}

    win_id: bpy.props.StringProperty()

    def execute(self, context):
        win = get_window_from_id(context.window_manager, self.win_id)
        if not win:
            return {'CANCELLED'}
        with context.temp_override(window=win):
            bpy.ops.wm.window_close()
        return {'FINISHED'}


def validate_sync(window_manager: WindowManager) -> bool:
    """
    Ensure synchronization system is functional, with a valid main window.
    Disable it otherwise and return the system status.
    """
    if not window_manager.storypencil_settings.active:
        return False
    if not get_window_from_id(window_manager, window_manager.storypencil_settings.main_window_id):
        window_manager.storypencil_settings.active = False
    return window_manager.storypencil_settings.active


def get_secondary_window_indices(wm: WindowManager) -> List[str]:
    """Get secondary Windows indices as a list of IDs

    :param wm: the WindowManager to consider
    :return: the list of secondary Windows IDs
    """
    return split_win_ids(wm.storypencil_settings.secondary_windows_ids)


def is_secondary_window(window_manager: WindowManager, win_id: str) -> bool:
    """Return wether the Window identified by 'win_id' is a secondary window.

    :return: whether this Window is a sync secondary
    """
    return win_id in get_secondary_window_indices(window_manager)


def enable_secondary_window(wm: WindowManager, win_id: str):
    """Enable the secondary status of a Window.

    :param wm: the WindowManager instance
    :param win_id: the id of the window
    """
    secondary_indices = get_secondary_window_indices(wm)
    win_id_str = win_id
    # Delete old indice if exist
    if win_id_str in secondary_indices:
        secondary_indices.remove(win_id_str)

    # Add indice
    secondary_indices.append(win_id_str)

    # rebuild the whole list of valid secondary windows
    secondary_indices = [
        idx for idx in secondary_indices if get_window_from_id(wm, idx)]

    wm.storypencil_settings.secondary_windows_ids = join_win_ids(secondary_indices)


def toggle_secondary_window(wm: WindowManager, win_id: str):
    """Toggle the secondary status of a Window.

    :param wm: the WindowManager instance
    :param win_id: the id of the window
    """
    secondary_indices = get_secondary_window_indices(wm)
    win_id_str = win_id
    if win_id_str in secondary_indices:
        secondary_indices.remove(win_id_str)
    else:
        secondary_indices.append(win_id_str)

    # rebuild the whole list of valid secondary windows
    secondary_indices = [
        idx for idx in secondary_indices if get_window_from_id(wm, idx)]

    wm.storypencil_settings.secondary_windows_ids = join_win_ids(secondary_indices)


def get_main_window(wm: WindowManager) -> Window:
    """Get the Window used to drive the synchronization system

    :param wm: the WindowManager instance
    :returns: the main Window or None
    """
    return get_window_from_id(wm=wm, win_id=wm.storypencil_settings.main_window_id)


def get_secondary_window(wm: WindowManager) -> Window:
    """Get the first secondary Window

    :param wm: the WindowManager instance
    :returns: the Window or None
    """
    for w in wm.windows:
        win_id = window_id(w)
        if is_secondary_window(wm, win_id):
            return w

    return None


def get_not_main_window(wm: WindowManager) -> Window:
    """Get the first not main Window

    :param wm: the WindowManager instance
    :returns: the Window or None
    """
    for w in wm.windows:
        win_id = window_id(w)
        if win_id != wm.storypencil_settings.main_window_id:
            return w

    return None


def get_main_strip(wm: WindowManager) -> SceneSequence:
    """Get Scene Strip at current time in Main window

    :param wm: the WindowManager instance
    :returns: the Strip at current time or None
    """
    context = bpy.context
    scene = context.scene
    main_scene = scene.storypencil_main_scene

    if main_scene.storypencil_use_new_window:
        main_window = get_main_window(wm=wm)
        if not main_window or not main_window.scene.sequence_editor:
            return None
        seq_editor = main_window.scene.sequence_editor
        return seq_editor.sequences.get(wm.storypencil_settings.main_strip_name, None)
    else:
        seq_editor = main_scene.sequence_editor.sequences
        for strip in seq_editor:
            if strip.type != 'SCENE':
                continue
            if strip.scene.name == scene.name:
                return strip

    return None


class STORYPENCIL_OT_SyncToggleSecondary(Operator):
    bl_idname = "storypencil.sync_toggle_secondary"
    bl_label = "Toggle Secondary Window Status"
    bl_description = "Enable/Disable synchronization for a specific Window"
    bl_options = {'INTERNAL'}

    win_id: bpy.props.StringProperty(name="Window Index")

    def execute(self, context):
        wm = context.window_manager
        toggle_secondary_window(wm, self.win_id)
        return {'FINISHED'}


def get_sequences_at_frame(
        frame: int,
        sequences: Sequence[Sequence]) -> Sequence[bpy.types.Sequence]:
    """ Get all sequencer strips at given frame.

    :param frame: the frame to consider
    """
    return [s for s in sequences if frame >= s.frame_start + s.frame_offset_start and
                                    frame < s.frame_start + s.frame_offset_start + s.frame_final_duration and
                                    s.type == 'SCENE']


def get_sequence_at_frame(
        frame: int,
        sequences: Sequence[bpy.types.Sequence] = None,
        skip_muted: bool = True,
) -> Tuple[bpy.types.Sequence, int]:
    """
    Get the higher sequence strip in channels stack at current frame.
    Recursively enters scene sequences and returns the original frame in the
    returned strip's time referential.

    :param frame: the frame to consider
    :param skip_muted: skip muted strips
    :returns: the sequence strip and the frame in strip's time referential
    """

    strips = get_sequences_at_frame(frame, sequences or bpy.context.sequences)

    # exclude muted strips
    if skip_muted:
        strips = [strip for strip in strips if not strip.mute]

    if not strips:
        return None, frame

    # Remove strip not scene type. Switch is only with Scenes
    for strip in strips:
        if strip.type != 'SCENE':
            strips.remove(strip)

    # consider higher strip in stack
    strip = sorted(strips, key=lambda x: x.channel)[-1]
    # go deeper when current strip is a MetaSequence
    if isinstance(strip, MetaSequence):
        return get_sequence_at_frame(frame, strip.sequences, skip_muted)
    if isinstance(strip, SceneSequence):
        # apply time offset to get in sequence's referential
        frame = frame - strip.frame_start + strip.scene.frame_start
        # enter scene's sequencer if used as input
        if strip.scene_input == 'SEQUENCER':
            return get_sequence_at_frame(frame, strip.scene.sequence_editor.sequences)
    return strip, frame


def set_scene_frame(scene, frame, force_update_main=False):
    """
    Set `scene` frame_current to `frame` if different.

    :param scene: the scene to update
    :param frame: the frame value
    :param force_update_main: whether to force the update of main scene
    """
    options = bpy.context.window_manager.storypencil_settings
    if scene.frame_current != frame:
        scene.frame_current = int(frame)
        scene.frame_set(int(frame))
        if force_update_main:
            update_sync(
                bpy.context, bpy.context.window_manager.storypencil_settings.main_window_id)


def setup_window_from_scene_strip(window: Window, strip: SceneSequence):
    """Change the Scene and camera of `window` based on `strip`.

    :param window: [description]
    :param scene_strip: [description]
    """
    if window.scene != strip.scene:
        window.scene = strip.scene
    if strip.scene_camera and strip.scene_camera != window.scene.camera:
        strip.scene.camera = strip.scene_camera


@persistent
def on_frame_changed(*args):
    """
    React to current frame changes and synchronize secondary windows.
    """
    # ensure context is fully initialized, i.e not '_RestrictData
    if not isinstance(bpy.context, Context):
        return

    # happens in some cases (not sure why)
    if not bpy.context.window:
        return

    wm = bpy.context.window_manager

    # early return if synchro is disabled / not available
    if not validate_sync(wm) or len(bpy.data.scenes) < 2:
        return

    # get current window id
    update_sync(bpy.context)


def update_sync(context: Context, win_id=None):
    """ Update synchronized Windows based on the current `context`.

    :param context: the context
    :param win_id: specify a window id (context.window is used otherwise)
    """
    wm = context.window_manager

    if not win_id:
        win_id = window_id(context.window)

    main_scene = get_window_from_id(
        wm, wm.storypencil_settings.main_window_id).scene
    if not main_scene.sequence_editor:
        return

    # return if scene's sequence editor has no sequences
    sequences = main_scene.sequence_editor.sequences
    if not sequences:
        return

    # bidirectionnal sync: change main time from secondary window
    if (
            win_id != wm.storypencil_settings.main_window_id
            and is_secondary_window(wm, win_id)
    ):
        # get strip under time cursor in main window
        strip, old_frame = get_sequence_at_frame(
            main_scene.frame_current,
            sequences=sequences
        )
        # only do bidirectional sync if secondary window matches the strip at current time in main
        if not isinstance(strip, SceneSequence) or strip.scene != context.scene:
            return

        # calculate offset
        frame_offset = context.scene.frame_current - old_frame
        if frame_offset == 0:
            return

        new_main_frame = main_scene.frame_current + frame_offset
        update_main_time = True
        # check if a valid scene strip is available under new frame before changing main time
        f_start = strip.frame_start + strip.frame_offset_start
        f_end = f_start + strip.frame_final_duration
        if new_main_frame < f_start or new_main_frame >= f_end:
            new_strip, _ = get_sequence_at_frame(
                new_main_frame,
                main_scene.sequence_editor.sequences,
            )
            update_main_time = isinstance(new_strip, SceneSequence)
        if update_main_time:
            # update main time change in the next event loop + force the sync system update
            # because Blender won't trigger a frame_changed event to avoid infinite recursion
            bpy.app.timers.register(
                functools.partial(set_scene_frame, main_scene,
                                  new_main_frame, True)
            )

        return

    # return if current window is not main window
    if win_id != wm.storypencil_settings.main_window_id:
        return

    secondary_windows = [
        get_window_from_id(wm, win_id)
        for win_id
        in get_secondary_window_indices(wm)
        if win_id and win_id != wm.storypencil_settings.main_window_id
    ]

    # only work with at least 2 windows
    if not secondary_windows:
        return

    seq, frame = get_sequence_at_frame(main_scene.frame_current, sequences)

    # return if no sequence at current time or not a scene strip
    if not isinstance(seq, SceneSequence) or not seq.scene:
        wm.storypencil_settings.main_strip_name = ""
        return

    wm.storypencil_settings.main_strip_name = seq.name
    # change the scene on secondary windows
    # warning: only one window's scene can be changed in this event loop,
    #          otherwise it may crashes Blender randomly
    for idx, win in enumerate(secondary_windows):
        if not win:
            continue
        # change first secondary window immediately
        if idx == 0:
            setup_window_from_scene_strip(win, seq)
        else:
            # trigger change in next event loop for other windows
            bpy.app.timers.register(
                functools.partial(setup_window_from_scene_strip, win, seq)
            )

    set_scene_frame(seq.scene, frame)


def sync_all_windows(wm: WindowManager):
    """Enable synchronization on all main windows held by `wm`."""
    wm.storypencil_settings.secondary_windows_ids = join_win_ids([
        window_id(w)
        for w
        in get_main_windows_list(wm)
    ])


@persistent
def sync_autoconfig(*args):
    """Autoconfigure synchronization system.
    If a window contains a VSE area on a scene with a valid sequence_editor,
    makes it main window and enable synchronization on all other main windows.
    """
    main_windows = get_main_windows_list(bpy.context.window_manager)
    # don't try to go any further if only one main window
    if len(main_windows) < 2:
        return

    # look for a main window with a valid sequence editor
    main = next(
        (
            win
            for win in main_windows
            if win.scene.sequence_editor
            and any(area.type == 'SEQUENCE_EDITOR' for area in win.screen.areas)
        ),
        None
    )
    # if any, set as main and activate sync on all other windows
    if main:
        bpy.context.window_manager.storypencil_settings.main_window_id = window_id(
            main)
        sync_all_windows(bpy.context.window_manager)
        bpy.context.window_manager.storypencil_settings.active = True


def sync_active_update(self, context):
    """ Update function for WindowManager.storypencil_settings.active. """
    # ensure main window is valid, using current context's window if none is set
    if (
            self.active
            and (
            not self.main_window_id
            or not get_window_from_id(context.window_manager, self.main_window_id)
            )
    ):
        self.main_window_id = window_id(context.window)
        # automatically sync all other windows if nothing was previously set
        if not self.secondary_windows_ids:
            sync_all_windows(context.window_manager)

    on_frame_changed()


def draw_sync_header(self, context):
    """Draw Window sync tools header."""

    wm = context.window_manager
    self.layout.separator()
    if wm.get('storypencil_use_new_window') is not None:
        new_window = wm['storypencil_use_new_window']
    else:
        new_window = False

    if not new_window:
        if context.scene.storypencil_main_workspace:
            if context.scene.storypencil_main_workspace.name != context.workspace.name:
                if context.area.ui_type == 'DOPESHEET':
                    row = self.layout.row(align=True)
                    row.operator(STORYPENCIL_OT_Switch.bl_idname,
                                 text="Back To VSE")


def draw_sync_sequencer_header(self, context):
    """Draw Window sync tools header."""
    if context.space_data.view_type != 'SEQUENCER':
        return

    wm = context.window_manager
    layout = self.layout
    layout.separator()
    row = layout.row(align=True)
    row.label(text="Scenes:")
    if context.scene.storypencil_use_new_window:
        row.operator(STORYPENCIL_OT_SetSyncMainOperator.bl_idname, text="Edit")
    else:
        row.operator(STORYPENCIL_OT_Switch.bl_idname, text="Edit")

    row.separator()
    layout.operator_context = 'INVOKE_REGION_WIN'
    row.operator(STORYPENCIL_OT_NewScene.bl_idname, text="New")

    layout.operator_context = 'INVOKE_DEFAULT'
    row.separator(factor=0.5)
    row.operator(STORYPENCIL_OT_RenderAction.bl_idname, text="Render")


class STORYPENCIL_PG_Settings(PropertyGroup):
    """
    PropertyGroup with storypencil settings.
    """
    active: BoolProperty(
        name="Synchronize",
        description=(
            "Automatically open current Sequence's Scene in other "
            "Main Windows and activate Time Synchronization"),
        default=False,
        update=sync_active_update
    )

    main_window_id: StringProperty(
        name="Main Window ID",
        description="ID of the window driving the Synchronization",
        default="",
    )

    secondary_windows_ids: StringProperty(
        name="Secondary Windows",
        description="Serialized Secondary Window Indices",
        default="",
    )

    active_window_index: IntProperty(
        name="Active Window Index",
        description="Index for using Window Manager's windows in a UIList",
        default=0
    )

    main_strip_name: StringProperty(
        name="Main Strip Name",
        description="Scene Strip at current time in the Main window",
        default="",
    )

    show_main_strip_range: BoolProperty(
        name="Show Main Strip Range in Secondary Windows",
        description="Draw main Strip's in/out markers in synchronized secondary Windows",
        default=True,
    )


# -------------------------------------------------------------
# Switch manually between Main and Edit Scene and Layout
#
# -------------------------------------------------------------
class STORYPENCIL_OT_Switch(Operator):
    bl_idname = "storypencil.switch"
    bl_label = "Switch"
    bl_description = "Switch workspace"
    bl_options = {'REGISTER', 'UNDO'}

    # Get active strip
    def act_strip(self, context):
        scene = context.scene
        sequences = scene.sequence_editor.sequences
        if not sequences:
            return None
        # Get strip under time cursor
        strip, old_frame = get_sequence_at_frame(
            scene.frame_current, sequences=sequences)
        return strip

    # ------------------------------
    # Poll
    # ------------------------------
    @classmethod
    def poll(cls, context):
        scene = context.scene
        if scene.storypencil_main_workspace is None or scene.storypencil_main_scene is None:
            return False
        if scene.storypencil_edit_workspace is None:
            return False

        return True

    # ------------------------------
    # Execute button action
    # ------------------------------
    def execute(self, context):
        wm = context.window_manager
        scene = context.scene
        wm['storypencil_use_new_window'] = scene.storypencil_use_new_window

        # Switch to Main
        if scene.storypencil_main_workspace.name != context.workspace.name:
            cfra_prv = scene.frame_current
            prv_pin = None
            if scene.storypencil_main_workspace is not None:
                if scene.storypencil_main_workspace.use_pin_scene:
                    scene.storypencil_main_workspace.use_pin_scene = False

                context.window.workspace = scene.storypencil_main_workspace

            if scene.storypencil_main_scene is not None:
                context.window.scene = scene.storypencil_main_scene
            strip = self.act_strip(context)
            if strip:
                context.window.scene.frame_current = int(cfra_prv + strip.frame_start) - 1

            # Delete sounds
            if scene.storypencil_copy_sounds:
                delete_sounds(scene)

            #bpy.ops.sequencer.reload()
        else:
            # Switch to Edit
            strip = self.act_strip(context)
            # save camera
            if strip is not None and strip.type == "SCENE":
                # Save data
                strip.scene.storypencil_main_workspace = scene.storypencil_main_workspace
                strip.scene.storypencil_main_scene = scene.storypencil_main_scene
                strip.scene.storypencil_edit_workspace = scene.storypencil_edit_workspace

                # Set workspace and Scene
                cfra_prv = scene.frame_current
                if scene.storypencil_edit_workspace.use_pin_scene:
                    scene.storypencil_edit_workspace.use_pin_scene = False

                context.window.workspace = scene.storypencil_edit_workspace
                context.window.workspace.update_tag()

                context.window.scene = strip.scene
                # Copy sounds
                if scene.storypencil_copy_sounds:
                    send_sound_to_strip_scene(strip, clear_sequencer=True, skip_mute=scene.storypencil_skip_sound_mute)


                active_frame = cfra_prv - strip.frame_start + 1
                if active_frame < strip.scene.frame_start:
                    active_frame = strip.scene.frame_start
                context.window.scene.frame_current = int(active_frame)

                # Set camera
                if strip.scene_input == 'CAMERA':
                    for screen in bpy.data.screens:
                        for area in screen.areas:
                            if area.type == 'VIEW_3D':
                                # select camera as view
                                if strip and strip.scene.camera is not None:
                                    area.spaces.active.region_3d.view_perspective = 'CAMERA'

                if scene.storypencil_copy_sounds:
                    bpy.ops.sequencer.reload()

        return {"FINISHED"}


class STORYPENCIL_OT_TabSwitch(Operator):
    bl_idname = "storypencil.tabswitch"
    bl_label = "Switch using tab key"
    bl_description = "Wrapper used to handle the Tab key to switch"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        if context.scene.storypencil_use_new_window:
            bpy.ops.storypencil.sync_set_main('INVOKE_DEFAULT', True)
        else:
            bpy.ops.storypencil.switch('INVOKE_DEFAULT', True)

        return {'FINISHED'}
