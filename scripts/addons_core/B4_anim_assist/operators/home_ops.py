# --- ANIM ASSIST HOMES ---
"""Open the Anim Assist panel, pop it into its own window, or add its workspace."""

from __future__ import annotations

import bpy
from bpy.types import Operator

from .. import constants
from ..core.helpers import report_failure
from ..core.logging import get_logger

_log = get_logger(__name__)

WORKSPACE_NAME: str = constants.ANIMASSIST_CATEGORY
SIDEBAR_SPACES: frozenset[str] = frozenset({"GRAPH_EDITOR", "DOPESHEET_EDITOR", "NLA_EDITOR"})


def _region(area: bpy.types.Area, kind: str) -> bpy.types.Region | None:
    return next((r for r in area.regions if r.type == kind), None)


def _show_sidebar_tab(area: bpy.types.Area) -> None:
    """Open an editor's sidebar on the Anim Assist tab (the tab needs one redraw first)."""
    area.spaces.active.show_region_ui = True
    area.tag_redraw()

    def _select_tab() -> None:
        ui = _region(area, "UI")
        if ui is not None:
            try:
                ui.active_panel_category = constants.ANIMASSIST_CATEGORY
            except Exception:
                _log.debug("Sidebar tab not ready", exc_info=True)
        return None

    bpy.app.timers.register(_select_tab, first_interval=0.1)


def _open_window_from(context: bpy.types.Context, source: bpy.types.Area) -> bpy.types.Window | None:
    """Duplicate ``source`` into a new window and turn it into the Properties home."""
    before = set(context.window_manager.windows[:])
    with context.temp_override(window=context.window, screen=context.window.screen,
                               area=source, region=_region(source, "WINDOW")):
        bpy.ops.screen.area_dupli("INVOKE_DEFAULT")
    new = [w for w in context.window_manager.windows if w not in before]
    if not new:
        return None
    area = new[0].screen.areas[0]
    if area.type != "PROPERTIES":
        area.type = "PROPERTIES"
    area.spaces.active.context = "SCENE"
    return new[0]


class ANIMASSIST_OT_open_home(Operator):
    bl_idname = "animassist.open_home"
    bl_label = "Open Anim Assist Panel"
    bl_description = (
        "Show the full Anim Assist panel: the sidebar tab in the Graph Editor and "
        "Dope Sheet, or Properties > Scene > Anim Assist elsewhere"
    )
    bl_options = {"REGISTER"}

    def execute(self, context: bpy.types.Context):
        area = context.area
        if area is not None and area.type in SIDEBAR_SPACES:
            _show_sidebar_tab(area)
            return {"FINISHED"}
        props = next((a for a in context.screen.areas if a.type == "PROPERTIES"), None)
        if props is not None:
            props.spaces.active.context = "SCENE"
            props.tag_redraw()
            self.report({"INFO"}, "Anim Assist is in the Properties editor, Scene tab")
            return {"FINISHED"}
        return bpy.ops.animassist.open_home_window("INVOKE_DEFAULT")


class ANIMASSIST_OT_open_home_window(Operator):
    bl_idname = "animassist.open_home_window"
    bl_label = "Open in Separate Window"
    bl_description = (
        "Open the Anim Assist panel in its own window that stays open while you "
        "work; move it anywhere, or to a second monitor"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.window is not None and context.screen is not None

    def execute(self, context: bpy.types.Context):
        source = next((a for a in context.screen.areas if a.type == "PROPERTIES"), None) or context.area
        if source is None:
            return report_failure(self, "No editor to open the window from",
                                  "Hover over an editor and try again")
        try:
            window = _open_window_from(context, source)
        except Exception as exc:
            return report_failure(self, "Could not open a new window",
                                  "Use Window > New Window instead", exc)
        if window is None:
            return report_failure(self, "Could not open a new window",
                                  "Use Window > New Window instead")
        return {"FINISHED"}


def _arrange_workspace(screen: bpy.types.Screen) -> None:
    """Graph Editor beside the viewport, sidebars on Anim Assist, Properties on Scene."""
    viewports = sorted((a for a in screen.areas if a.type == "VIEW_3D"), key=lambda a: a.x)
    if len(viewports) > 1:
        graph = viewports[-1]
        graph.type = "GRAPH_EDITOR"
        graph.ui_type = "FCURVES"
    for area in screen.areas:
        if area.type == "PROPERTIES":
            area.spaces.active.context = "SCENE"
        elif area.type == "VIEW_3D":
            area.spaces.active.show_region_ui = False
        elif area.type in SIDEBAR_SPACES and area.height > 100:
            _show_sidebar_tab(area)


class ANIMASSIST_OT_add_workspace(Operator):
    bl_idname = "animassist.add_workspace"
    bl_label = "Add Anim Assist Workspace"
    bl_description = (
        "Switch to the Anim Assist workspace, adding it first if needed: a copy of the "
        "Animation workspace with a Graph Editor and every Anim Assist home open. "
        "Your Animation workspace is not changed"
    )
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.window is not None

    def execute(self, context: bpy.types.Context):
        window = context.window
        existing = bpy.data.workspaces.get(WORKSPACE_NAME)
        if existing is not None:
            window.workspace = existing
            return {"FINISHED"}

        # workspace.duplicate copies the workspace on screen, and switching is
        # applied on the next event loop, so switch to the base first and copy
        # it from a timer once it is showing.
        base = bpy.data.workspaces.get("Animation") or context.workspace
        window.workspace = base
        _when_showing(window, base.name, _copy_workspace)
        return {"FINISHED"}


def _when_showing(window: bpy.types.Window, name: str, then, tries: int = 20) -> None:
    """Run ``then(window)`` once workspace ``name`` is on screen.

    Switching workspace is applied on the next event loop, and a screen only
    rebuilds its editors when it is showing, so both copying and re-arranging
    wait for the switch.
    """
    def _tick():
        try:
            if window.workspace.name != name:
                if tries <= 0:
                    _log.warning("Workspace switch to %s never happened", name)
                else:
                    _when_showing(window, name, then, tries - 1)
                return None
            then(window)
        except Exception:
            _log.exception("Setting up the Anim Assist workspace failed")
        return None

    bpy.app.timers.register(_tick, first_interval=0.05)


def _copy_workspace(window: bpy.types.Window) -> None:
    before = set(bpy.data.workspaces[:])
    with bpy.context.temp_override(window=window, screen=window.screen):
        bpy.ops.workspace.duplicate()
    new = [w for w in bpy.data.workspaces if w not in before]
    if not new:
        _log.warning("Duplicating the workspace made no copy")
        return
    new[0].name = WORKSPACE_NAME
    window.workspace = new[0]
    _when_showing(window, WORKSPACE_NAME, lambda win: _arrange_workspace(win.screen))


CLASSES: tuple[type, ...] = (
    ANIMASSIST_OT_open_home,
    ANIMASSIST_OT_open_home_window,
    ANIMASSIST_OT_add_workspace,
)
