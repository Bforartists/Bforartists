"""Opt-in persistent settings editor; existing RNA remains the settings authority."""

from dataclasses import dataclass
from uuid import uuid4

import bpy
from . import motion_paths as mp
from .session_state import SessionState

_targets = {}
_sections = {}


@dataclass
class EditingTarget:
    scene: object
    obj: object
    path_uid: str
    path_key: tuple | None
    source_window: object
    editor_window: object = None
    # Window addresses are reused after a window closes; its screen is not.
    editor_screen: object = None


def capture_target(context):
    scene = context.scene
    settings = scene.ghost_tool
    index = settings.motion_paths_index
    entry = settings.motion_paths[index] if 0 <= index < len(settings.motion_paths) else None
    if entry is not None and entry.is_folder:
        entry = None
    # A selected list row is deliberate; fall back to the active object's path.
    if entry is None:
        index = mp.active_entry_index(context)
        entry = settings.motion_paths[index] if index >= 0 else None
    uid, key = "", None
    obj = context.active_object
    if entry is not None:
        uid = entry.get("_ghost_editor_uid", "")
        if not uid:
            uid = uuid4().hex
            entry["_ghost_editor_uid"] = uid
        key = mp.entry_key(entry)
        obj = scene.objects.get(entry.object_name)
    return EditingTarget(scene, obj, uid, key, context.window)


def resolve_target(target, scene):
    from .target_binding import resolve_editor_target
    return resolve_editor_target(target, scene)


def is_editor(context):
    return _owns_window(context.window)


def _owns_window(window):
    try:
        target = _targets.get(window.as_pointer()) if window is not None else None
        if target is None or target.editor_window != window:
            return False
        screen = target.editor_screen
        # Reading the name raises ReferenceError once the screen was freed.
        return screen is None or (bool(screen.name) and window.screen == screen)
    except ReferenceError:
        return False


def draw_editor(layout, context):
    from .ui_panel import _wrapped_label
    pointer = context.window.as_pointer()
    target = _targets[pointer]
    entry, reason = resolve_target(target, context.scene)
    layout.label(text="Settings Editor (Prototype)")
    row = layout.row(align=True)
    row.operator("ghost_tool.refresh_editor_target", text="Refresh Target")
    row.operator("ghost_tool.return_from_editor", text="Return to Viewport")
    try:
        _wrapped_label(layout, context, f"Scene: {target.scene.name}")
        _wrapped_label(layout, context, f"Object: {target.obj.name if target.obj else '(none)'}")
        _wrapped_label(layout, context, f"Path: {entry.label if entry else '(none)'}")
    except ReferenceError:
        layout.label(text="Target removed", icon='ERROR')
    if reason:
        _wrapped_label(layout, context, reason, icon='ERROR')
        return
    layout.label(text="Target locked; Refresh Target follows selection.")
    if not SessionState.available():
        layout.label(text="Finish or cancel the gesture to edit settings.", icon='INFO')
    body = layout.column()
    body.enabled = SessionState.available()
    settings = target.scene.ghost_tool
    sections = ('paths', 'edit', 'look', 'settings')
    first = _sections.get(pointer, 'paths')
    if first not in sections:
        first = 'paths'
    for section in (first,) + tuple(s for s in sections if s != first):
        if section == first:
            # Contextual access must reveal the requested settings even when this
            # section was previously collapsed in the persistent window.
            header, panel = body, body.box()
        else:
            header, panel = body.panel(f"ghost_editor_{section}", default_closed=True)
        header.label(text={'paths': "Path Settings", 'edit': "Editing Settings", 'look': "Look", 'settings': "Settings"}[section])
        if panel is None:
            continue
        if section == 'paths':
            if entry is None:
                panel.label(text="Select a path row, then Refresh Target.")
            else:
                for name in mp.dialog_props(entry):
                    if name in mp.RANGE_PROPS:
                        continue
                    panel.prop(entry, name)
                panel.prop(entry, "visible")
                panel.prop(entry, "in_front")
                panel.prop(entry, "use_own_range")
                if entry.use_own_range:
                    panel.prop(entry, "own_range_mode")
                    for name in mp.own_range_props(entry.own_range_mode):
                        panel.prop(entry, name)
                    panel.prop(entry, "own_step")
            for name in ("paths_show_handles", "paths_show_markers", "paths_show_key_dots", "paths_step"):
                panel.prop(settings, name)
        elif section == 'edit':
            panel.prop(settings, "editing_mode")
            panel.prop(settings, "curve_mode" if settings.editing_mode == 'RESHAPE' else "smooth_neighbors_on_commit")
            panel.prop(settings, "sculpt_falloff_radius")
            if settings.sculpt_falloff_radius > 0:
                panel.prop(settings, "sculpt_falloff_curve")
            easing = target.scene.ghost_tool_easing
            panel.prop(easing, "active_preset")
            if easing.active_preset == 'CUSTOM':
                for name in ("custom_left_x", "custom_left_y", "custom_right_x", "custom_right_y"):
                    panel.prop(easing, name)
        elif section == 'look':
            from .ui_panel import _draw_look
            _draw_look(panel, context)
        else:
            for name in ("grab_radius", "use_custom_range"):
                panel.prop(settings, name)
            if settings.use_custom_range:
                panel.prop(settings, "custom_range_start")
                panel.prop(settings, "custom_range_end")


class GHOST_OT_open_settings_editor(bpy.types.Operator):
    """Open persistent settings for an explicitly captured scene, object and path"""
    bl_idname = "ghost_tool.open_settings_editor"
    bl_label = "Settings Editor (Prototype)"
    section: bpy.props.EnumProperty(
        items=[(s, s.title(), "") for s in ('paths', 'edit', 'look', 'settings')],
        default='paths', options={'HIDDEN', 'SKIP_SAVE'})

    @classmethod
    def poll(cls, context):
        if context.window is None or context.screen is None:
            cls.poll_message_set("Open a 3D Viewport window first")
            return False
        return SessionState.poll_available(cls)

    def execute(self, context):
        # Only one prototype editor is owned at a time. Reopening deliberately refreshes its target.
        target = capture_target(context)
        windows = list(context.window_manager.windows)
        window = next((w for w in windows if _owns_window(w)), None)
        if window is None:
            before = {w.as_pointer() for w in windows}
            if bpy.ops.ghost_tool.open_window() != {'FINISHED'}:
                return {'CANCELLED'}
            window = next((w for w in context.window_manager.windows if w.as_pointer() not in before), None)
            if window is None:
                return {'CANCELLED'}
        window.scene = context.scene
        target.editor_window = window
        target.editor_screen = window.screen
        _targets.clear()
        _sections.clear()
        _targets[window.as_pointer()] = target
        _sections[window.as_pointer()] = self.section
        for area in window.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}


class GHOST_OT_refresh_editor_target(bpy.types.Operator):
    """Use the source viewport's current selection as the editor target"""
    bl_idname = "ghost_tool.refresh_editor_target"
    bl_label = "Refresh Target"

    @classmethod
    def poll(cls, context):
        if not is_editor(context):
            cls.poll_message_set("Open the prototype settings editor first")
            return False
        return SessionState.poll_available(cls)

    def execute(self, context):
        pointer = context.window.as_pointer()
        source = _targets[pointer].source_window
        if source in context.window_manager.windows[:]:
            area = next((a for a in source.screen.areas if a.type == 'VIEW_3D'), None)
            with context.temp_override(window=source, area=area):
                target = capture_target(context)
            context.window.scene = target.scene
        else:
            target = capture_target(context)
        _targets[pointer] = target
        target.editor_window = context.window
        target.editor_screen = context.window.screen
        context.area.tag_redraw()
        return {'FINISHED'}


class GHOST_OT_return_from_editor(bpy.types.Operator):
    """Close only this prototype window and retain the viewport selection"""
    bl_idname = "ghost_tool.return_from_editor"
    bl_label = "Return to Viewport"

    @classmethod
    def poll(cls, context):
        if not is_editor(context):
            cls.poll_message_set("Use Return from the prototype settings editor")
            return False
        return SessionState.poll_available(cls)

    def execute(self, context):
        from .ui_panel import _ghost_windows
        pointer = context.window.as_pointer()
        result = bpy.ops.wm.window_close()
        if result == {'FINISHED'}:
            _targets.pop(pointer, None)
            _sections.pop(pointer, None)
            _ghost_windows.discard(pointer)
        return result


@bpy.app.handlers.persistent
def _clear_on_load(*_args):
    _targets.clear()
    _sections.clear()


CLASSES = (GHOST_OT_open_settings_editor, GHOST_OT_refresh_editor_target, GHOST_OT_return_from_editor)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.app.handlers.load_pre.append(_clear_on_load)


def unregister():
    if _clear_on_load in bpy.app.handlers.load_pre:
        bpy.app.handlers.load_pre.remove(_clear_on_load)
    _clear_on_load()
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
