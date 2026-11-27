# --- SIDEBAR AND PROPERTIES LAYOUT ---
"""Where every Anim Assist panel lives, and how each home is organised.

Anim Assist has no tab in the 3D Viewport sidebar. Its panels live in three
homes, each organised for the job of the editor it sits in:

* Graph Editor sidebar, "Anim Assist" tab: by action (select, shape curves,
  retime, clean up).
* Dope Sheet sidebar, "Anim Assist" tab: by stage (block, inbetween, time,
  finish).
* Properties editor, Scene tab, "Anim Assist" section: by scope (this pose,
  whole animation, rig, face), plus setup, settings and help.

Panels keep their own drawing code. ``arrange`` re-parents them under the
generated group panels before registration, so this module is the single
source of truth for the layout.
"""

from __future__ import annotations

from dataclasses import dataclass

import bpy
from bpy.types import Panel

from .. import constants
from ..core.logging import get_logger

_log = get_logger(__name__)

HOME_LABEL: str = constants.ANIMASSIST_CATEGORY
PROPERTIES_CONTEXT: str = "scene"


@dataclass(frozen=True)
class Group:
    """A collapsible group of panels inside one home."""

    key: str
    label: str
    icon: str
    panels: tuple[str, ...]
    open: bool = False


#: Graph Editor and Dope Sheet sidebars: (subtitle, groups top to bottom).
SIDEBARS: dict[str, tuple[str, tuple[Group, ...]]] = {
    "GRAPH_EDITOR": ("Selected visible Action keys", (
        Group("select", "Select & Channels", "NONE", ("ANIMASSIST_PT_p2_selection", "ANIMASSIST_PT_p2_channels")),
        Group("shape", "Shape Curves", "NONE", ("ANIMASSIST_PT_curve_tools", "ANIMASSIST_PT_curve_interpolation"), open=True),
        Group("retime", "Retime", "NONE", ("ANIMASSIST_PT_p6_retime_GE", "ANIMASSIST_PT_anim_offset")),
        Group("clean", "Clean Up", "NONE", ("ANIMASSIST_PT_p2_keyutils", "ANIMASSIST_PT_p2_diagnostics", "ANIMASSIST_PT_key_manager", "ANIMASSIST_PT_p2_metadata")),
        Group("poserig", "Pose & Bake", "NONE", ("ANIMASSIST_PT_p9_mirror_GE", "ANIMASSIST_PT_p8_matching_GE", "ANIMASSIST_PT_graph_breakdown", "ANIMASSIST_PT_p3_interpolation", "ANIMASSIST_PT_p7_bake_ds_GE")),
        Group("shelf", "Quick Shelf", "NONE", ("ANIMASSIST_PT_p10_shelf_GE",)),
    )),
    "DOPESHEET_EDITOR": ("Pose and key timing", (
        Group("block", "Block & Tween", "NONE", ("ANIMASSIST_PT_p3_breakdown", "ANIMASSIST_PT_p3_inbetween", "ANIMASSIST_PT_p3_presets", "ANIMASSIST_PT_p3_modal", "ANIMASSIST_PT_p3_pose_compare", "ANIMASSIST_PT_p3_subsets", "ANIMASSIST_PT_p4_offset", "ANIMASSIST_PT_p3_options_dope"), open=True),
        Group("time", "Timing", "NONE", ("ANIMASSIST_PT_p6_retime", "ANIMASSIST_PT_anim_offset_dope")),
        Group("keys", "Keys & Channels", "NONE", ("ANIMASSIST_PT_p2_selection_ds", "ANIMASSIST_PT_p2_channels_ds", "ANIMASSIST_PT_p2_keyutils_ds", "ANIMASSIST_PT_key_manager_dope", "ANIMASSIST_PT_key_manager_timeline", "ANIMASSIST_PT_p2_metadata_ds")),
        Group("mirror", "Pose & Match", "NONE", ("ANIMASSIST_PT_p9_mirror", "ANIMASSIST_PT_p8_matching")),
        Group("bake", "Bake & Finish", "NONE", ("ANIMASSIST_PT_p7_bake_ds", "ANIMASSIST_PT_p2_diagnostics_ds")),
        Group("shelf", "Quick Shelf", "NONE", ("ANIMASSIST_PT_p10_shelf",)),
    )),
    "NLA_EDITOR": ("Clips, tracks and corrections", (
        Group("arrange", "Arrange & Time", "NONE", ("ANIMASSIST_PT_nla_arrange",), open=True),
        Group("blend", "Blend & Corrections", "NONE", ("ANIMASSIST_PT_nla_blend",), open=True),
        Group("actions", "Actions & Tracks", "NONE", ("ANIMASSIST_PT_nla_actions",)),
        Group("bake", "Bake & Finish", "NONE", ("ANIMASSIST_PT_nla_bake",)),
        Group("shelf", "Quick Shelf", "NONE", ("ANIMASSIST_PT_nla_shelf",)),
    )),
}

PROPERTIES_SUBTITLE: str = "Character: this pose, whole animation, rig, face"

#: The Quick Shelf sits directly under the Properties home, above the groups.
PROPERTIES_SHELF: str = "ANIMASSIST_PT_p10_shelf_v3d"

#: Properties home groups, top to bottom. The 3D Viewport panels move here.
PROPERTIES_GROUPS: tuple[Group, ...] = (
    Group("thispose", "This Pose", "POSE_HLT",
          ("ANIMASSIST_PT_p4_pose_offset", "ANIMASSIST_PT_p9_mirror_v3d",
           "ANIMASSIST_PT_p8_match_v3d"), open=True),
    Group("whole", "Whole Animation", "ANIM",
          ("ANIMASSIST_PT_anim_offset_3d", "ANIMASSIST_PT_p5_trajectory",
           "ANIMASSIST_PT_p11_layers_v3d")),
    Group("rig", "Rig", "ARMATURE_DATA", ("ANIMASSIST_PT_p7_proxy_bake",)),
    Group("face", "Face", "SHAPEKEY_DATA", ("ANIMASSIST_PT_p12_lipsync_v3d",)),
    Group("setup", "Setup (once per rig)", "PREFERENCES", ("ANIMASSIST_PT_home_setup_body", "ANIMASSIST_PT_p10_system")),
    Group("settings", "Settings", "SETTINGS", ("ANIMASSIST_PT_home_settings_body", "ANIMASSIST_PT_p10_macros")),
    Group("help", "Help & Diagnostics", "HELP", ("AA_PT_help_browser", "AA_PT_diagnostics")),
)

HOME_ROOT_IDNAME: str = "ANIMASSIST_PT_home"


def sidebar_group_idname(space: str, key: str) -> str:
    return f"ANIMASSIST_PT_{dict(GRAPH_EDITOR='ge', DOPESHEET_EDITOR='ds', NLA_EDITOR='nla_group')[space]}_{key}"


def home_group_idname(key: str) -> str:
    return f"ANIMASSIST_PT_home_{key}"


# ---------------------------------------------------------------------------
# Generated panels
# ---------------------------------------------------------------------------

def _icon_header(icon: str):
    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon=icon)
    return draw_header


def _draw_nothing(self, _context: bpy.types.Context) -> None:
    """Group panels only hold sub-panels."""


def _sidebar_title(space: str, subtitle: str) -> type[Panel]:
    def draw(self, context: bpy.types.Context) -> None:
        if space == "NLA_EDITOR":
            from .nla_panels import draw_target
            draw_target(self.layout, context)
            return
        from ..core.context_utils import iter_visible_fcurves
        col = self.layout.column(align=True)
        curves = list(iter_visible_fcurves(context))
        owners = {obj.name for obj, _action, _fc in curves}
        count = sum(k.select_control_point for _o, _a, fc in curves for k in fc.keyframe_points)
        col.label(text=f"Scope: {len(owners)} visible owners")
        col.label(text=f"Selected keys: {count}")
        col.label(text=f"Editable curves: {len(curves)}")
        supported = {fc.as_pointer() for _o, _a, fc in curves}
        if any(fc.as_pointer() not in supported for fc in (getattr(context, "editable_fcurves", ()) or ())
               if not fc.hide and not fc.mute and not fc.lock):
            from .ui_helpers import wrapped_label
            wrapped_label(col, context, "Unsupported source channels excluded. Object Actions only; pinned sources need an owner.", icon="INFO")
        if not curves:
            col.label(text="Show editable Action channels in this editor")
        if space == "DOPESHEET_EDITOR":
            row = col.row(align=True)
            row.operator("action.select_all", text="All").action = "SELECT"
            row.operator("action.select_all", text="None").action = "DESELECT"
            row.operator("action.select_all", text="Invert").action = "INVERT"

    name = f"{sidebar_group_idname(space, 'title')}"
    return type(name, (Panel,), {
        "bl_idname": name, "bl_label": HOME_LABEL, "bl_space_type": space,
        "bl_region_type": "UI", "bl_category": HOME_LABEL, "bl_order": 0,
        "bl_options": {"HIDE_HEADER"}, "draw": draw,
        "poll": classmethod(lambda cls, context: space != "GRAPH_EDITOR" or
                            getattr(context.space_data, "mode", "") != "DRIVERS"),
    })


def _group_panel(idname: str, group: Group, order: int, space: str, region: str,
                 parent: str = "", context: str = "") -> type[Panel]:
    ns = {
        "bl_idname": idname, "bl_label": group.label, "bl_space_type": space,
        "bl_region_type": region, "bl_order": order,
        "draw": _draw_nothing,
    }
    if region == "UI":
        ns["bl_category"] = HOME_LABEL
        if space == "GRAPH_EDITOR":
            ns["poll"] = classmethod(lambda cls, context: getattr(context.space_data, "mode", "") != "DRIVERS")
    if parent:
        ns["bl_parent_id"] = parent
    if context:
        ns["bl_context"] = context
    if not group.open:
        ns["bl_options"] = {"DEFAULT_CLOSED"}
    return type(idname, (Panel,), ns)


class ANIMASSIST_PT_home(Panel):
    """Anim Assist home in the Properties editor (Scene tab)."""

    bl_idname = HOME_ROOT_IDNAME
    bl_label = HOME_LABEL
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = PROPERTIES_CONTEXT

    def draw_header(self, _context: bpy.types.Context) -> None:
        self.layout.label(icon="ANIM")

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        row = layout.row()
        row.enabled = False
        row.label(text=PROPERTIES_SUBTITLE)
        row = layout.row(align=True)
        row.operator("animassist.p10_search_tools", text="Search Tools", icon="VIEWZOOM")
        row.operator("animassist.p10_repeat_last", text="Repeat Last", icon="RECOVER_LAST")


class ANIMASSIST_PT_home_setup_body(Panel):
    """One-time rig and scene setup, gathered in one place."""

    bl_idname = "ANIMASSIST_PT_home_setup_body"
    bl_label = "Setup"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = PROPERTIES_CONTEXT
    bl_options = {"HIDE_HEADER"}

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        col = layout.column(align=True)
        col.operator("animassist.p10_first_run_setup", text="Run First Run Setup", icon="CHECKMARK")
        col.operator("animassist.add_workspace", text="Add Anim Assist Workspace", icon="WORKSPACE")
        layout.separator()
        col = layout.column(align=True)
        col.label(text="Rig")
        col.operator("animassist.p9_build_cache", text="Find Left/Right Pairs", icon="MOD_MIRROR")
        col.operator("animassist.p9_validate_pairs", text="Check Pairs", icon="CHECKBOX_HLT")
        col.operator("animassist.p8_detect_all", text="Find IK/FK Switches", icon="CON_KINEMATIC")
        layout.separator()
        col = layout.column(align=True)
        col.label(text="Face")
        col.operator("animassist.p12_setup_lipsync", text="Set Up Lipsync", icon="SPEAKER")


class ANIMASSIST_PT_home_settings_body(Panel):
    """Where Anim Assist appears, its hotkey, and display options."""

    bl_idname = "ANIMASSIST_PT_home_settings_body"
    bl_label = "Settings"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = PROPERTIES_CONTEXT
    bl_options = {"HIDE_HEADER"}

    def draw(self, context: bpy.types.Context) -> None:
        from ..prefs import get_prefs
        from . import header_menus

        layout = self.layout
        prefs = get_prefs(context)
        if prefs is None:
            layout.label(text="Preferences unavailable", icon="ERROR")
            return

        col = layout.column(align=True)
        col.label(text="Shortcut", icon="EVENT_SHIFT")
        col.prop(prefs, "pie_hotkey_enabled", text="Anim Assist pie menu")
        sub = col.column(align=True)
        sub.active = prefs.pie_hotkey_enabled
        for label, kmi in header_menus.pie_keymap_items(context):
            row = sub.row(align=True)
            row.label(text=label)
            row.prop(kmi, "type", text="", full_event=True)
        col.operator("animassist.p10_check_hotkey_conflicts", text="Check for Conflicts", icon="ERROR")

        layout.separator()
        col = layout.column(heading="Header menu in", align=True)
        col.prop(prefs, "header_menu_view3d")
        col.prop(prefs, "header_menu_graph")
        col.prop(prefs, "header_menu_dopesheet")
        col.prop(prefs, "header_menu_nla")

        layout.separator()
        col = layout.column(align=True)
        col.prop(prefs, "show_explainer_help")
        col.prop(prefs, "compact_ui_mode")
        op = layout.operator("preferences.addon_show", text="All Preferences", icon="PREFERENCES")
        op.module = constants.ADDON_PACKAGE


# ---------------------------------------------------------------------------
# Re-parenting
# ---------------------------------------------------------------------------

def _dock_in_sidebar(cls: type[Panel], parent: str, order: int) -> None:
    cls.bl_parent_id = parent
    cls.bl_category = HOME_LABEL
    cls.bl_order = order
    options = set(getattr(cls, "bl_options", set()))
    direct = {"ANIMASSIST_PT_curve_tools", "ANIMASSIST_PT_curve_interpolation",
              "ANIMASSIST_PT_p3_breakdown", "ANIMASSIST_PT_p3_inbetween",
              "ANIMASSIST_PT_p6_retime", "ANIMASSIST_PT_p6_retime_GE",
              "ANIMASSIST_PT_p7_bake_ds", "ANIMASSIST_PT_p7_bake_ds_GE"}
    if cls.__name__ in direct or cls.__name__.startswith("ANIMASSIST_PT_nla_"):
        cls.bl_options = (options - {"DEFAULT_CLOSED"}) | {"HIDE_HEADER"}
    else:
        cls.bl_options = options | {"DEFAULT_CLOSED"}


def _move_to_properties(cls: type[Panel], parent: str, order: int | None, closed: bool = True) -> None:
    cls.bl_space_type = "PROPERTIES"
    cls.bl_region_type = "WINDOW"
    cls.bl_context = PROPERTIES_CONTEXT
    cls.bl_parent_id = parent
    if order is not None:
        cls.bl_order = order
    options = set(getattr(cls, "bl_options", set()))
    cls.bl_options = options | {"DEFAULT_CLOSED"} if closed else options - {"DEFAULT_CLOSED"}


def arrange(classes: tuple[type, ...]) -> tuple[type, ...]:
    """Re-parent Anim Assist panels into their homes; return the classes to register.

    Generated title and group panels come first so every parent is registered
    before its children. Idempotent: calling it again changes nothing.
    """
    panels = {c.__name__: c for c in classes if isinstance(c, type) and issubclass(c, Panel)}
    generated: list[type] = []
    # Drivers have their own top-level panels, not children of Action groups.
    placed: set[str] = {name for name in panels if name.startswith("ANIMASSIST_PT_driver_")}

    for space, (subtitle, groups) in SIDEBARS.items():
        generated.append(_sidebar_title(space, subtitle))
        for order, group in enumerate(groups, start=1):
            parent = sidebar_group_idname(space, group.key)
            generated.append(_group_panel(parent, group, order, space, "UI"))
            for index, name in enumerate(group.panels):
                cls = panels.get(name)
                if cls is None:
                    _log.warning("Layout lists missing panel %s", name)
                    continue
                _dock_in_sidebar(cls, parent, index)
                placed.add(name)

    generated.append(ANIMASSIST_PT_home)
    bodies = {c.__name__: c for c in (ANIMASSIST_PT_home_setup_body, ANIMASSIST_PT_home_settings_body)}
    shelf = panels.get(PROPERTIES_SHELF)
    if shelf is not None:
        _move_to_properties(shelf, HOME_ROOT_IDNAME, 0, closed=False)
        placed.add(PROPERTIES_SHELF)
    for order, group in enumerate(PROPERTIES_GROUPS, start=1):
        parent = home_group_idname(group.key)
        generated.append(_group_panel(parent, group, order, "PROPERTIES", "WINDOW",
                                      parent=HOME_ROOT_IDNAME, context=PROPERTIES_CONTEXT))
        for index, name in enumerate(group.panels):
            if name in bodies:
                bodies[name].bl_parent_id = parent
                bodies[name].bl_order = index
                continue
            cls = panels.get(name)
            if cls is None:
                _log.warning("Layout lists missing panel %s", name)
                continue
            _move_to_properties(cls, parent, index)
            placed.add(name)
    generated += bodies.values()  # after their group panels

    # Sub-panels follow their parents; anything unlisted still gets a home.
    for name, cls in panels.items():
        if getattr(cls, "bl_region_type", "") != "UI" or name in placed:
            continue
        space = getattr(cls, "bl_space_type", "")
        if getattr(cls, "bl_parent_id", ""):
            if space == "VIEW_3D":
                _move_to_properties(cls, cls.bl_parent_id, None)
            elif space in SIDEBARS:
                cls.bl_category = HOME_LABEL
        elif space == "VIEW_3D":
            _log.warning("Unplaced viewport panel %s; putting it under Help", name)
            _move_to_properties(cls, home_group_idname("help"), 99)
        elif space in SIDEBARS:
            _log.warning("Unplaced %s panel %s; putting it in the last group", space, name)
            _dock_in_sidebar(cls, sidebar_group_idname(space, SIDEBARS[space][1][-1].key), 99)

    return (*generated, *classes)


__all__ = [
    "Group",
    "HOME_LABEL",
    "HOME_ROOT_IDNAME",
    "PROPERTIES_GROUPS",
    "SIDEBARS",
    "arrange",
    "home_group_idname",
    "sidebar_group_idname",
]
