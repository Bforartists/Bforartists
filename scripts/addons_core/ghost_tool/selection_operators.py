"""
selection_operators.py — Box selection for ghost markers.

Provides a modal box-select operator that draws a selection rectangle
and selects all ghosts within it. Supports shift-extend selection.
"""

from __future__ import annotations

from typing import Optional

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils
from mathutils import Vector

from .ghost_data import GhostStore, Ghost
from .session_state import SessionState
from .utils import log, warn, debug, tag_viewport_redraw


# ---------------------------------------------------------------------------
# Helper: world-to-screen projection
# ---------------------------------------------------------------------------

def _world_to_screen(
    context: bpy.types.Context,
    world_pos: Vector,
) -> Optional[tuple[float, float]]:
    """Project a 3D world-space point to 2D screen coordinates."""
    region = context.region
    region_3d = context.region_data
    if not region or not region_3d:
        return None

    screen_pos = view3d_utils.location_3d_to_region_2d(region, region_3d, world_pos)
    if screen_pos is None:
        return None
    return (screen_pos.x, screen_pos.y)


# ---------------------------------------------------------------------------
# Box Select Draw Handler
# ---------------------------------------------------------------------------

_box_draw_handler = None
_box_rect: Optional[tuple[float, float, float, float]] = None


def _draw_selection_box():
    """GPU draw callback for the selection rectangle overlay.

    Wrapped in try/finally to guarantee GPU state is always restored,
    even if batch creation or drawing raises an exception.
    """
    if _box_rect is None:
        return

    x1, y1, x2, y2 = _box_rect

    # Rectangle outline vertices
    verts = [
        (x1, y1), (x2, y1),
        (x2, y1), (x2, y2),
        (x2, y2), (x1, y2),
        (x1, y2), (x1, y1),
    ]
    indices = [(i, i + 1) for i in range(0, len(verts), 2)]

    gpu.state.blend_set('ALPHA')
    gpu.state.line_width_set(1.5)
    try:
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {"pos": verts}, indices=indices)

        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 0.3, 0.8))
        batch.draw(shader)

        # Semi-transparent fill
        fill_verts = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
        fill_indices = [(0, 1, 2), (0, 2, 3)]
        fill_batch = batch_for_shader(shader, 'TRIS', {"pos": fill_verts}, indices=fill_indices)
        shader.uniform_float("color", (1.0, 1.0, 0.3, 0.1))
        fill_batch.draw(shader)
    except Exception as exc:
        warn(f"Box select draw error: {exc}")
    finally:
        gpu.state.blend_set('NONE')
        gpu.state.line_width_set(1.0)


# ---------------------------------------------------------------------------
# Box Select Operator
# ---------------------------------------------------------------------------

class GHOST_OT_box_select(bpy.types.Operator):
    """Draw a selection rectangle to select multiple ghost markers.

    Click and drag to draw a box. All ghosts whose screen-space positions
    fall within the box are selected. Shift-drag extends the existing
    selection. Plain drag replaces it.

    Keybindings during modal:
        MOUSEMOVE — Update box corner
        LEFTMOUSE release — Confirm selection
        RIGHTMOUSE or ESC — Cancel
    """

    bl_idname = "ghost_tool.box_select"
    bl_label = "Box Select Ghosts"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Require active ghost display with ghosts present."""
        if not hasattr(context.scene, 'ghost_tool'):
            cls.poll_message_set("Initialize Ghost Tool first")
            return False
        if not context.scene.ghost_tool.is_active:
            cls.poll_message_set("Turn on Ghost Tool first")
            return False
        if not context.scene.ghost_tool.show_cached_markers:
            cls.poll_message_set("Show cached markers in Marker options first")
            return False
        if not len(GhostStore.get(context.scene)):
            cls.poll_message_set("Generate markers for an animated object first")
            return False
        return SessionState.poll_available(cls)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Begin the box selection.

        Args:
            context: The current Blender context.
            event: The triggering event.

        Returns:
            set[str]: {'RUNNING_MODAL'} on success.
        """
        global _box_draw_handler, _box_rect

        if not SessionState.available(self):
            self.report({'WARNING'}, "Finish or cancel the current Ghost Tool gesture first")
            return {'CANCELLED'}
        # Guard against reentrancy: if a box select is already running, cancel
        if _box_draw_handler is not None:
            return {'CANCELLED'}

        # Validate context.area exists
        if not context.area:
            return {'CANCELLED'}

        # Initialize instance state (avoid class-variable sharing)
        self._start_x = event.mouse_region_x
        self._start_y = event.mouse_region_y
        self._extend = event.shift

        # Initialize the rectangle
        _box_rect = (self._start_x, self._start_y, self._start_x, self._start_y)

        # Register the draw handler for the selection rectangle overlay
        SessionState.begin_gesture(self, context.scene)
        try:
            _box_draw_handler = bpy.types.SpaceView3D.draw_handler_add(
                _draw_selection_box, (), 'WINDOW', 'POST_PIXEL'
            )
            context.window_manager.modal_handler_add(self)
        except Exception:
            self._cleanup(context)
            raise
        return {'RUNNING_MODAL'}

    def modal(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Handle events during box selection.

        Wrapped in try/except to guarantee cleanup on any exception.

        Args:
            context: The current Blender context.
            event: The current event.

        Returns:
            set[str]: Modal state.
        """
        global _box_rect

        try:
            if not SessionState.owns_gesture(self, context.scene):
                self._cleanup(context)
                return {'CANCELLED'}
            if event.type == 'MOUSEMOVE':
                _box_rect = (
                    self._start_x, self._start_y,
                    event.mouse_region_x, event.mouse_region_y,
                )
                tag_viewport_redraw(context)
                return {'RUNNING_MODAL'}

            if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
                self._finish_selection(context, event)
                self._cleanup(context)
                return {'FINISHED'}

            if event.type in {'RIGHTMOUSE', 'ESC'}:
                self._cleanup(context)
                return {'CANCELLED'}

            return {'RUNNING_MODAL'}

        except Exception as exc:
            warn(f"Box select modal error: {exc}")
            self._cleanup(context)
            return {'CANCELLED'}

    def _finish_selection(
        self,
        context: bpy.types.Context,
        event: bpy.types.Event,
    ) -> None:
        """Test all ghost screen positions against the box and update selection.

        Args:
            context: The current Blender context.
            event: The release event.
        """
        if not context.scene.ghost_tool.show_cached_markers:
            return
        store = GhostStore.get(context.scene)
        session = SessionState.get(context.scene)

        # Determine box bounds (handle any drag direction)
        x1 = min(self._start_x, event.mouse_region_x)
        y1 = min(self._start_y, event.mouse_region_y)
        x2 = max(self._start_x, event.mouse_region_x)
        y2 = max(self._start_y, event.mouse_region_y)

        # Skip if box is too small (accidental click)
        if (x2 - x1) < 5 and (y2 - y1) < 5:
            return

        # Clear existing selection unless extending
        if not self._extend:
            session.clear_selection()

        # Test each ghost's screen position against the box
        selected_count = 0
        for ghost in store:
            screen_pos = _world_to_screen(context, ghost.world_position)
            if screen_pos is None:
                continue

            sx, sy = screen_pos
            if x1 <= sx <= x2 and y1 <= sy <= y2:
                session.select(ghost.uid)
                selected_count += 1

        self.report({'INFO'}, f"Box selected {selected_count} ghosts")

    def _cleanup(self, context: bpy.types.Context) -> None:
        """Remove the draw handler and clear the rectangle overlay."""
        global _box_draw_handler, _box_rect
        SessionState.end_gesture(self)

        _box_rect = None

        if _box_draw_handler is not None:
            try:
                bpy.types.SpaceView3D.draw_handler_remove(
                    _box_draw_handler, 'WINDOW'
                )
            except Exception as exc:
                debug(f"Failed to remove box select draw handler: {exc}")
            _box_draw_handler = None

        tag_viewport_redraw(context)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    GHOST_OT_box_select,
)


def register() -> None:
    """Register selection operator classes."""
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    """Unregister selection operator classes."""
    global _box_draw_handler, _box_rect

    # Clean up draw handler if still active
    _box_rect = None
    if _box_draw_handler is not None:
        try:
            bpy.types.SpaceView3D.draw_handler_remove(
                _box_draw_handler, 'WINDOW'
            )
        except Exception as exc:
            debug(f"Failed to remove box select draw handler during unregister: {exc}")
        _box_draw_handler = None

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
