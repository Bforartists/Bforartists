# --- TRANSFORM OFFSET CONTROLS ---
"""Sidebar panels for transform offset and pose manipulation.

Placement:

* **Transform Offset** — Dope Sheet sidebar (DOPESHEET_EDITOR). This is the
  primary panel where key selection, offset amounts, scope, and space live.
* **Pose Offset** — 3D Viewport sidebar (VIEW_3D), Pose-Mode only. Provides
  the Push/Pull buttons, current-frame nudge, and modal drag for viewport
  workflows. This is an explicitly viewport-transform tool per the directive.

Every panel inherits from :class:`PanelAnatomyMixin` so the canonical
Primary → Scope → Advanced draw ordering is respected, and uses
:mod:`..ui.ui_helpers` helpers instead of raw ``layout.operator`` /
``layout.prop`` calls.
"""

from __future__ import annotations

import bpy

from ..core.p4_properties import get_p4
from . import ui_helpers as uh
from .editor_placement import (
    DopeSheetSidebarPanel,
    View3DSidebarPanel,
)
from .panel_anatomy import PanelAnatomyMixin


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _p4_available(context: bpy.types.Context) -> bool:
    if get_p4(context) is None:
        return False
    obj = getattr(context, "active_object", None)
    if obj is None:
        return False
    adata = getattr(obj, "animation_data", None)
    return adata is not None and adata.action is not None


def _draw_context_warning(layout, context) -> None:
    obj = getattr(context, "active_object", None)
    if obj is None:
        layout.label(text="No active object.", icon="INFO")
        return
    adata = getattr(obj, "animation_data", None)
    if adata is None or adata.action is None:
        layout.label(text=f"{obj.name} has no animation data.", icon="INFO")
        return
    if get_p4(context) is None:
        layout.label(text="Offset property group unavailable.", icon="ERROR")


# ---------------------------------------------------------------------------
# Transform Offset (Dope Sheet)
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p4_offset(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Primary keyed transform offset controls."""

    bl_category = "Pose"
    bl_order = 80
    bl_idname = "ANIMASSIST_PT_p4_offset"
    bl_label = "Transform Offset"

    def draw_primary(self, context):
        layout = self.layout
        if not _p4_available(context):
            _draw_context_warning(layout, context)
            return
        p4 = get_p4(context)

        # --- Amounts ---
        uh.section_header(layout, "Offset Amounts", icon="ORIENTATION_LOCAL")
        col = layout.column(align=True)
        col.prop(p4, "translate_amount", text="Translate")
        col.prop(p4, "rotate_amount", text="Rotate")
        col.prop(p4, "scale_amount", text="Scale")
        uh.separator(layout)

        # --- Core operators ---
        uh.section_header(layout, "Actions", icon="PLAY")
        uh.explained_op(layout, context, "animassist.p4_nudge_current",
                        text="Nudge Current Frame",
                        icon="KEYFRAME_HLT",
                        help_id="op.animassist.p4_nudge_current")
        uh.explained_op(layout, context, "animassist.p4_offset_selected",
                        text="Offset Selected Keys",
                        icon="KEYFRAME",
                        help_id="op.animassist.p4_offset_selected")
        uh.explained_op(layout, context, "animassist.p4_modal_offset",
                        text="Interactive Drag",
                        icon="MOUSE_LMB_DRAG",
                        help_id="op.animassist.p4_modal_offset")
        uh.separator(layout)

        # --- Axis filter buttons ---
        row = layout.row(align=True)
        row.operator("animassist.p4_offset_translate_only", text="T Only", icon="CON_LOCLIMIT")
        row.operator("animassist.p4_offset_rotate_only", text="R Only", icon="CON_ROTLIMIT")
        row.operator("animassist.p4_offset_scale_only", text="S Only", icon="CON_SIZELIMIT")
        row.operator("animassist.p4_offset_trs_combined", text="TRS", icon="OBJECT_ORIGIN")
        uh.separator(layout)

        # --- Reapply / Invert ---
        row = layout.row(align=True)
        uh.explained_op(row, context, "animassist.p4_reapply_last",
                        text="Reapply Last",
                        icon="FILE_REFRESH",
                        help_id="op.animassist.p4_reapply_last")
        uh.explained_op(row, context, "animassist.p4_invert_last",
                        text="Invert Last",
                        icon="LOOP_BACK",
                        help_id="op.animassist.p4_invert_last")

    def draw_scope(self, context):
        layout = self.layout
        if not _p4_available(context):
            return
        p4 = get_p4(context)

        uh.section_header(layout, "Scope & Filters", icon="RESTRICT_SELECT_OFF")
        uh.explained_prop(layout, context, p4, "channel_mask",
                          help_id="op.animassist.p4_offset_translate_only")
        uh.explained_prop(layout, context, p4, "scope",
                          help_id="prop.p4_frame_range_falloff")
        if p4.scope == "FRAME_RANGE":
            row = layout.row(align=True)
            row.prop(p4, "range_start")
            row.prop(p4, "range_end")
        uh.explained_prop(layout, context, p4, "space",
                          help_id="prop.p4_space_local")
        uh.explained_prop(layout, context, p4, "falloff_shape",
                          help_id="prop.p4_falloff_linear")

        col = layout.column(align=True)
        col.prop(p4, "skip_locked")
        col.prop(p4, "skip_muted")
        col.prop(p4, "selected_channels_only")
        col.prop(p4, "keyed_channels_only")

    def draw_advanced(self, context):
        layout = self.layout
        if not _p4_available(context):
            return
        p4 = get_p4(context)

        uh.section_header(layout, "Advanced", icon="PREFERENCES")

        # R2 audit fix: pivot_mode UI hidden because only INDIVIDUAL is
        # wired through the pipeline.  Pivot-relative orbit is TODO.
        # uh.explained_prop(layout, context, p4, "pivot_mode",
        #                   help_id="prop.p4_pivot_individual")

        uh.explained_prop(layout, context, p4, "preserve_contact_axis", text="Contact",
                          help_id="prop.p4_preserve_contact")
        uh.explained_prop(layout, context, p4, "auto_key_missing",
                          help_id="prop.p4_auto_key_missing")
        uh.explained_prop(layout, context, p4, "mirror_sign_enabled",
                          help_id="prop.p4_mirror_sign")
        if p4.mirror_sign_enabled:
            layout.prop(p4, "mirror_axis")

        uh.separator(layout)

        uh.explained_prop(layout, context, p4, "fine_step",
                          help_id="prop.p4_fine_step")
        uh.explained_prop(layout, context, p4, "active_preset",
                          help_id="op.animassist.p4_apply_preset")


# ---------------------------------------------------------------------------
# Push/Pull (Dope Sheet sub-panel)
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p4_pushpull(PanelAnatomyMixin, DopeSheetSidebarPanel):
    """Push / Pull single-axis offset buttons and amount."""

    bl_idname = "ANIMASSIST_PT_p4_pushpull"
    bl_label = "Push / Pull"
    bl_parent_id = "ANIMASSIST_PT_p4_offset"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_primary(self, context):
        layout = self.layout
        if not _p4_available(context):
            _draw_context_warning(layout, context)
            return
        p4 = get_p4(context)

        layout.prop(p4, "push_amount")
        uh.separator(layout)

        # Push row.
        uh.section_header(layout, "Push", icon="FORWARD")
        row = layout.row(align=True)
        uh.explained_op(row, context, "animassist.p4_push_x",
                        text="X", icon="EVENT_X",
                        help_id="op.animassist.p4_push_x")
        uh.explained_op(row, context, "animassist.p4_push_y",
                        text="Y", icon="EVENT_Y",
                        help_id="op.animassist.p4_push_y")
        uh.explained_op(row, context, "animassist.p4_push_z",
                        text="Z", icon="EVENT_Z",
                        help_id="op.animassist.p4_push_z")

        uh.separator(layout, factor=0.5)

        # Pull row.
        uh.section_header(layout, "Pull", icon="BACK")
        row = layout.row(align=True)
        uh.explained_op(row, context, "animassist.p4_pull_x",
                        text="X", icon="EVENT_X",
                        help_id="op.animassist.p4_pull_x")
        uh.explained_op(row, context, "animassist.p4_pull_y",
                        text="Y", icon="EVENT_Y",
                        help_id="op.animassist.p4_pull_y")
        uh.explained_op(row, context, "animassist.p4_pull_z",
                        text="Z", icon="EVENT_Z",
                        help_id="op.animassist.p4_pull_z")


# ---------------------------------------------------------------------------
# Pose Offset (VIEW_3D)
# ---------------------------------------------------------------------------

class ANIMASSIST_PT_p4_pose_offset(PanelAnatomyMixin, View3DSidebarPanel):
    """Quick transform offset for selected bones, 3D Viewport context."""

    bl_category = "Motion"
    bl_order = 20
    bl_idname = "ANIMASSIST_PT_p4_pose_offset"
    bl_label = "Pose Offset"

    @classmethod
    def poll(cls, context):
        obj = getattr(context, "active_object", None)
        if obj is None:
            return False
        return obj.mode == "POSE" and obj.type == "ARMATURE"

    def draw_primary(self, context):
        layout = self.layout
        if not _p4_available(context):
            _draw_context_warning(layout, context)
            return
        p4 = get_p4(context)

        uh.section_header(layout, "Quick Offset", icon="ORIENTATION_LOCAL")
        uh.explained_op(layout, context, "animassist.p4_nudge_current",
                        text="Nudge Current Frame",
                        icon="KEYFRAME_HLT",
                        help_id="op.animassist.p4_nudge_current")
        uh.explained_op(layout, context, "animassist.p4_modal_offset",
                        text="Interactive Drag",
                        icon="MOUSE_LMB_DRAG",
                        help_id="op.animassist.p4_modal_offset")
        uh.separator(layout)

        layout.prop(p4, "push_amount")
        uh.separator(layout, factor=0.5)
        row = layout.row(align=True)
        row.operator("animassist.p4_push_x", text="+X")
        row.operator("animassist.p4_push_y", text="+Y")
        row.operator("animassist.p4_push_z", text="+Z")
        row = layout.row(align=True)
        row.operator("animassist.p4_pull_x", text="-X")
        row.operator("animassist.p4_pull_y", text="-Y")
        row.operator("animassist.p4_pull_z", text="-Z")
        uh.separator(layout)

        row = layout.row(align=True)
        row.operator("animassist.p4_reapply_last", text="Reapply", icon="FILE_REFRESH")
        row.operator("animassist.p4_invert_last", text="Invert", icon="LOOP_BACK")

    def draw_scope(self, context):
        layout = self.layout
        if not _p4_available(context):
            return
        p4 = get_p4(context)

        uh.explained_prop(layout, context, p4, "space",
                          help_id="prop.p4_space_local")
        uh.explained_prop(layout, context, p4, "preserve_contact_axis", text="Contact",
                          help_id="prop.p4_preserve_contact")
        uh.explained_prop(layout, context, p4, "mirror_sign_enabled",
                          help_id="prop.p4_mirror_sign")
        uh.explained_prop(layout, context, p4, "fine_step",
                          help_id="prop.p4_fine_step")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

CLASSES: tuple[type, ...] = (
    ANIMASSIST_PT_p4_offset,
    ANIMASSIST_PT_p4_pushpull,
    ANIMASSIST_PT_p4_pose_offset,
)
