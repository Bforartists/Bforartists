# --- HEADER MENUS AND PIE ---
"""The "Anim Assist" menu in each editor's header, and the Anim Assist pie.

Each editor's menu follows the same structure as that editor's Anim Assist
home (see ``layout_homes``): the Graph Editor by action, the Dope Sheet by
stage, the 3D Viewport by scope. Every menu starts with search and repeat,
and ends with the ways to open the full panel, the Anim Assist workspace,
and a separate window.

The pie gathers the existing Anim Assist pies behind one shortcut. Its
hotkey is off by default and is switched on from Properties > Scene >
Anim Assist > Settings.
"""

from __future__ import annotations

import bpy
from bpy.types import Menu

from .. import constants

#: Per editor: (menu class to append to, preference toggle, submenus).
#: Submenus are (key, label, icon, operator idnames; None draws a separator).
MENUS: dict[str, tuple[str, str, tuple[tuple[str, str, str, tuple[str | None, ...]], ...]]] = {
    "VIEW_3D": ("VIEW3D_MT_editor_menus", "header_menu_view3d", (
        ("thispose", "This Pose", "POSE_HLT", (
            "p4_nudge_current", "p4_offset_selected", "p4_reapply_last", None,
            "p9_mirror_pose", "p9_swap_poses", "p9_select_opposite", None,
            "p8_match_to_world", "p8_match_to_parent", "p8_visual_match")),
        ("whole", "Whole Animation", "ANIM", (
            "anim_offset", "anim_offset_toggle_mask", None,
            "p5_enable_overlay", "p5_disable_overlay", "p5_run_diagnostics", None,
            "p11_add_layer", "p11_assign_selected", "p11_toggle_solo")),
        ("rig", "Rig", "ARMATURE_DATA", (
            "p7_quick_proxy", "p7_one_click_proxy_bake", "p7_smart_bake", None,
            "p7_one_click_cleanup")),
        ("face", "Face", "SHAPEKEY_DATA", (
            "p12_setup_lipsync", "p12_bake_lipsync", "p12_rebake")),
    )),
    "GRAPH_EDITOR": ("GRAPH_MT_editor_menus", "header_menu_graph", (
        ("select", "Select", "RESTRICT_SELECT_OFF", (
            "select_local_extremes", "select_every_nth", "select_between_selected",
            "select_flat_segments", "select_neighbors", None,
            "isolate_selected_channels", "show_all_channels")),
        ("shape", "Shape Curves", "IPO_BEZIER", (
            "blend_neighbor", "blend_offset", "blend_frame", "ease_to_ease",
            "push_pull", "smooth_keys", "batch_interpolation", "select_handles", "set_handle_type")),
        ("retime", "Retime", "TIME", (
            "p6_insert_time", "p6_remove_time", "p6_scale_keys", "p6_offset_keys",
            "p6_ripple_forward", "p6_snap_to_frames", None, "anim_offset")),
        ("clean", "Clean Up", "BRUSH_DATA", (
            "scan_redundant_keys", "scan_spike_keys", "scan_dense_keys",
            "snap_keys_to_integer_frames", None, "safe_delete_selected_keys")),
        ("poserig", "Pose & Bake", "ARMATURE_DATA", (
            "mirror_selected_keys", "p8_quick_match", "p7_bake_range")),
    )),
    "DOPESHEET_EDITOR": ("DOPESHEET_MT_editor_menus", "header_menu_dopesheet", (
        ("block", "Block", "POSE_HLT", (
            "breakdown_current_frame", "breakdown_favor_prev", "breakdown_favor_next",
            "breakdown_midpoint", None, "modal_drag_breakdown")),
        ("inbetween", "Inbetween", "KEYFRAME", (
            "inbetween_selected_gap", "inbetween_distribute", "inbetween_on_clusters", None,
            "breakdown_push_prev", "breakdown_pull_prev", "breakdown_pull_next",
            "breakdown_push_next")),
        ("time", "Time", "TIME", (
            "p6_insert_time", "p6_remove_time", "p6_scale_keys", "p6_ripple_forward", None,
            "p6_detect_gaps", "p6_fill_gaps", None, "anim_offset")),
        ("mirror", "Pose & Match", "MOD_MIRROR", (
            "p9_mirror_pose", "p9_swap_poses", "p9_select_opposite", None,
            "p8_quick_match", "p7_smart_bake")),
        ("keys", "Keys & Channels", "KEYFRAME_HLT", (
            "select_all_visible", "select_first_last", "select_frame_range", None,
            "isolate_selected_channels", "show_all_channels", None,
            "safe_delete_selected_keys")),
    )),
}

MENUS["NLA_EDITOR"] = ("NLA_MT_editor_menus", "header_menu_nla", tuple(
    (key, label, "NONE", ()) for key, label in (
        ("arrange", "Arrange & Time"), ("blend", "Blend & Corrections"),
        ("actions", "Actions & Tracks"), ("bake", "Bake & Finish"))))

_SPACE_SLUG = {"NLA_EDITOR": "nla", "VIEW_3D": "v3d", "GRAPH_EDITOR": "ge", "DOPESHEET_EDITOR": "ds"}

#: Pie slots in Blender's order: W, E, S, N, NW, NE, SW, SE.
PIE_SLOTS: tuple[tuple[str, str, str], ...] = (
    ("p10_pie_key_tools", "Key Tools", "KEYFRAME_HLT"),
    ("p10_pie_breakdown", "Breakdown", "POSE_HLT"),
    ("p10_search_tools", "Search Tools", "VIEWZOOM"),
    ("p10_pie_transform", "Transform", "ORIENTATION_GIMBAL"),
    ("p10_pie_symmetry", "Symmetry", "MOD_MIRROR"),
    ("p10_pie_switch", "Switch", "FILE_REFRESH"),
    ("p10_pie_proxy", "Proxy", "EMPTY_AXIS"),
    ("p10_repeat_last", "Repeat Last", "RECOVER_LAST"),
)

#: (keymap name, space type, label shown in Settings) for the pie hotkey.
PIE_KEYMAPS: tuple[tuple[str, str, str], ...] = (
    ("3D View", "VIEW_3D", "3D Viewport"),
    ("Graph Editor", "GRAPH_EDITOR", "Graph Editor"),
    ("Dopesheet", "DOPESHEET_EDITOR", "Dope Sheet"),
)
#: Unused by every default Bforartists 5.1.2 keymap (checked against all 3,207 items).
PIE_KEY: dict[str, object] = {"type": "D", "value": "PRESS", "shift": True, "alt": True}


def menu_idname(space: str, key: str = "") -> str:
    slug = _SPACE_SLUG[space]
    return f"ANIMASSIST_MT_home_{slug}_{key}" if key else f"ANIMASSIST_MT_home_{slug}"


# ---------------------------------------------------------------------------
# Menus
# ---------------------------------------------------------------------------

def _submenu(space: str, key: str, label: str, ops: tuple[str | None, ...]) -> type[Menu]:
    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        if space == "NLA_EDITOR":
            from .nla_panels import native, timing
            if key == "arrange":
                timing(layout, "NUDGE", "Nudge Back 1 Frame", -1)
                timing(layout, "NUDGE", "Nudge Forward 1 Frame", 1)
                native(layout, "MOVE", "Move Selected Clips")
                timing(layout, "START", "Align Starts")
                timing(layout, "END", "Align Ends")
                timing(layout, "SEQUENCE", "Sequence Clips")
            elif key == "blend":
                layout.operator("animassist.nla_correction")
                layout.operator("animassist.nla_influence")
                from ..core.nla_context import active_target, is_correction
                item = active_target(_context)
                edit = layout.column()
                edit.enabled = bool(item and is_correction(item.strip))
                native(edit, "CORRECTION", "Edit Correction")
                native(layout, "EDIT", "Edit Action")
                native(layout, "FINISH", "Finish Editing")
                for editor, label in (("DOPESHEET_EDITOR", "Open Dope Sheet"), ("GRAPH_EDITOR", "Open Graph Editor")):
                    layout.operator("animassist.nla_open_editor", text=label).editor = editor
            elif key == "actions":
                layout.operator("animassist.nla_add_clip")
                native(layout, "DUPLICATE", "Duplicate Independent")
                native(layout, "LINKED", "Duplicate Linked")
                layout.operator("animassist.nla_unique")
                for command, label in (("UP", "Move Selected Tracks Up"), ("DOWN", "Move Selected Tracks Down"), ("PUSHDOWN", "Push Down Action"), ("STASH", "Stash Action")):
                    native(layout, command, label)
            else:
                layout.operator("animassist.nla_bake")
                layout.operator("animassist.nla_activate_bake")
                layout.operator("animassist.nla_empty_tracks")
            return
        for op in ops:
            if op is None:
                layout.separator()
            else:
                layout.operator(f"animassist.{op}")

    name = menu_idname(space, key)
    return type(name, (Menu,), {"bl_idname": name, "bl_label": label, "draw": draw})


def _top_menu(space: str, submenus) -> type[Menu]:
    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        if space == "GRAPH_EDITOR" and getattr(_context.space_data, "mode", "") == "DRIVERS":
            from .driver_panels import DRIVER_SECTIONS
            for key, label, _draw_section in DRIVER_SECTIONS:
                layout.menu(f"ANIMASSIST_MT_driver_{key}", text=label)
            return
        if space != "NLA_EDITOR":
            layout.operator("animassist.p10_search_tools", text="Search Anim Assist Tools...", icon="VIEWZOOM")
            layout.operator("animassist.p10_repeat_last", text="Repeat Last Tool", icon="RECOVER_LAST")
        layout.separator()
        for key, _label, icon, _ops in submenus:
            layout.menu(menu_idname(space, key), icon=icon)
        layout.separator()
        layout.operator("animassist.open_home", icon="PROPERTIES")
        layout.operator("animassist.add_workspace", text="Anim Assist Workspace", icon="WORKSPACE")
        layout.separator()
        layout.operator("animassist.open_home_window", icon="WINDOW")

    name = menu_idname(space)
    return type(name, (Menu,), {"bl_idname": name, "bl_label": constants.ANIMASSIST_CATEGORY, "draw": draw})


class ANIMASSIST_MT_pie_home(Menu):
    """One shortcut for every Anim Assist pie, plus search and repeat."""

    bl_idname = "ANIMASSIST_MT_pie_home"
    bl_label = constants.ANIMASSIST_CATEGORY

    def draw(self, _context: bpy.types.Context) -> None:
        pie = self.layout.menu_pie()
        for op, text, icon in PIE_SLOTS:
            pie.operator(f"animassist.{op}", text=text, icon=icon)


def _driver_submenu(key, label, draw_section) -> type[Menu]:
    def draw(self, context):
        draw_section(self.layout, context)
    name = f"ANIMASSIST_MT_driver_{key}"
    return type(name, (Menu,), {"bl_idname": name, "bl_label": label, "draw": draw})


def _build_classes() -> tuple[type, ...]:
    out: list[type] = []
    from .driver_panels import DRIVER_SECTIONS
    for key, label, draw_section in DRIVER_SECTIONS:
        out.append(_driver_submenu(key, label, draw_section))
    for space, (_menus, _pref, submenus) in MENUS.items():
        out += [_submenu(space, key, label, ops) for key, label, _icon, ops in submenus]
        out.append(_top_menu(space, submenus))
    out.append(ANIMASSIST_MT_pie_home)
    return tuple(out)


CLASSES: tuple[type, ...] = _build_classes()


# ---------------------------------------------------------------------------
# Header entries
# ---------------------------------------------------------------------------

def _header_entry(space: str, pref_name: str):
    def draw(self, context: bpy.types.Context) -> None:
        from ..prefs import get_prefs
        prefs = get_prefs(context)
        if prefs is not None and not getattr(prefs, pref_name, True):
            return
        if getattr(context.space_data, "mode", "") == "TIMELINE":
            return  # keep the Timeline header short
        self.layout.menu(menu_idname(space))
    return draw


_appended: list[tuple[type, object]] = []


def register() -> None:
    """Add the header entries and the pie keymaps."""
    for space, (menus, pref_name, _submenus) in MENUS.items():
        target = getattr(bpy.types, menus, None)
        if target is None:
            continue
        fn = _header_entry(space, pref_name)
        target.append(fn)
        _appended.append((target, fn))
    register_pie_keymaps()


def unregister() -> None:
    unregister_pie_keymaps()
    for target, fn in reversed(_appended):
        try:
            target.remove(fn)
        except Exception:
            pass
    _appended.clear()


# ---------------------------------------------------------------------------
# Pie hotkey
# ---------------------------------------------------------------------------

_pie_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


def _pie_enabled() -> bool:
    from ..prefs import get_prefs
    prefs = get_prefs()
    return bool(prefs is not None and prefs.pie_hotkey_enabled)


def register_pie_keymaps() -> None:
    wm = getattr(bpy.context, "window_manager", None)
    kc = wm.keyconfigs.addon if wm is not None else None
    if kc is None:
        return
    active = _pie_enabled()
    for km_name, space, _label in PIE_KEYMAPS:
        km = kc.keymaps.new(name=km_name, space_type=space)
        kmi = km.keymap_items.new("wm.call_menu_pie", **PIE_KEY)
        kmi.properties.name = ANIMASSIST_MT_pie_home.bl_idname
        kmi.active = active
        _pie_keymaps.append((km, kmi))


def unregister_pie_keymaps() -> None:
    for km, kmi in _pie_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception:
            pass
    _pie_keymaps.clear()


def set_pie_hotkey_active(active: bool) -> None:
    """Switch the pie shortcut on or off in every editor (user and add-on keymaps)."""
    for _km, kmi in _pie_keymaps:
        kmi.active = active
    for kmi in _user_pie_items():
        kmi.active = active


def _user_pie_items():
    wm = getattr(bpy.context, "window_manager", None)
    kc = wm.keyconfigs.user if wm is not None else None
    if kc is None:
        return
    for km_name, _space, _label in PIE_KEYMAPS:
        km = kc.keymaps.get(km_name)
        if km is None:
            continue
        for kmi in km.keymap_items:
            if kmi.idname == "wm.call_menu_pie" and getattr(kmi.properties, "name", "") == ANIMASSIST_MT_pie_home.bl_idname:
                yield kmi


def pie_keymap_items(context: bpy.types.Context):
    """(label, key map item) per editor, preferring the user's editable copy."""
    kc = context.window_manager.keyconfigs
    for km_name, _space, label in PIE_KEYMAPS:
        found = None
        for config in (kc.user, kc.addon):
            km = config.keymaps.get(km_name) if config is not None else None
            if km is None:
                continue
            found = next((k for k in km.keymap_items if k.idname == "wm.call_menu_pie"
                          and getattr(k.properties, "name", "") == ANIMASSIST_MT_pie_home.bl_idname), None)
            if found is not None:
                break
        if found is not None:
            yield label, found


__all__ = ["CLASSES", "MENUS", "PIE_KEY", "PIE_KEYMAPS", "PIE_SLOTS", "menu_idname",
           "pie_keymap_items", "register", "set_pie_hotkey_active", "unregister"]
