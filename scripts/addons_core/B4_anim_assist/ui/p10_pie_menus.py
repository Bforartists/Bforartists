from __future__ import annotations
import bpy


# Pie menu item definitions (op_id, label, icon)

_KEY_TOOLS_ITEMS = (
    ("animassist.tag_selected_keys", "Tag Keys", "KEY_HLT"),
    ("animassist.safe_delete_selected_keys", "Delete Key", "KEY_DEHLT"),
    ("animassist.offset_selected_frames", "Nudge Key", "FORWARD"),
    ("animassist.select_all_visible", "Select All Keys", "CHECKBOX_HLT"),
    ("animassist.snap_keys_to_integer_frames", "Snap Key", "SNAP_ON"),
    ("animassist.copy_selected_keys", "Copy Key", "COPYDOWN"),
    ("animassist.paste_keys_at_frame", "Paste Key", "PASTEDOWN"),
    ("animassist.mirror_selected_keys", "Mirror Time", "ARROW_LEFTRIGHT"),
)

_BREAKDOWN_ITEMS = (
    ("animassist.breakdown_current_frame", "Breakdown", "KEYFRAME"),
    ("animassist.inbetween_selected_gap", "Inbetween", "KEYFRAME_HLT"),
    ("animassist.breakdown_from_clipboard", "From Clipboard", "UV_SYNC_SELECT"),
    ("animassist.breakdown_weighted", "Breakdown Weighted", "EYEDROPPER"),
    ("animassist.breakdown_percentage", "Apply Preset %", "PRESET"),
    ("animassist.breakdown_push_prev", "Push Prev", "FULLSCREEN_ENTER"),
    ("animassist.breakdown_push_next", "Push Next", "FULLSCREEN_EXIT"),
    ("animassist.breakdown_midpoint", "Midpoint", "SMOOTHCURVE"),
)

_TRANSFORM_ITEMS = (
    ("animassist.p4_offset_selected", "Offset Apply", "CON_LOCLIKE"),
    ("animassist.p4_push_x", "Push", "FORWARD"),
    ("animassist.p4_pull_x", "Pull", "BACK"),
    ("animassist.p4_modal_offset", "Offset Modal", "EYEDROPPER"),
    ("animassist.p4_nudge_current", "Nudge Current", "CON_ROTLIKE"),
    ("animassist.p6_scale_keys", "Retime", "TIME"),
    ("animassist.p6_insert_time", "Ripple Insert", "ADD"),
    ("animassist.p6_remove_time", "Ripple Remove", "REMOVE"),
)

_PROXY_ITEMS = (
    ("animassist.p7_create_locator", "Create Locator", "EMPTY_SINGLE_ARROW"),
    ("animassist.p7_create_proxy", "Create Proxy", "OUTLINER_OB_ARMATURE"),
    ("animassist.p7_bake_selected", "Bake Proxy", "ACTION"),
    ("animassist.p7_cleanup_session", "Cleanup Session", "TRASH"),
    ("animassist.p7_recover_session", "Recover Session", "RECOVER_LAST"),
    ("animassist.p7_remove_constraints", "Remove Constraints", "CONSTRAINT"),
    ("animassist.p7_one_click_proxy_bake", "Bake All", "ACTION"),
    ("animassist.p7_match_locator_to_target", "Locator Snap", "SNAP_ON"),
)

_SWITCH_ITEMS = (
    ("animassist.p8_match_trs", "Match Pose", "ORIENTATION_VIEW"),
    ("animassist.p8_compensate_single", "Switch & Match", "MOD_MIRROR"),
    ("animassist.p8_detect_space_enums", "Detect Spaces", "SYSTEM"),
    ("animassist.p8_batch_switch", "Batch Switch", "LINKED"),
    ("animassist.p8_nav_prev_switch", "History Prev", "BACK"),
    ("animassist.p8_nav_next_switch", "History Next", "FORWARD"),
    ("animassist.p8_toggle_preview", "Switch Preview", "PLAY"),
    ("animassist.p8_bake_switch_range", "Match Range", "SEQ_SEQUENCER"),
)

_SYMMETRY_ITEMS = (
    ("animassist.p9_mirror_pose", "Mirror Pose", "MOD_MIRROR"),
    ("animassist.p9_mirror_selected", "Mirror Selected", "CHECKMARK"),
    ("animassist.p9_swap_poses", "Swap Poses", "ARROW_LEFTRIGHT"),
    ("animassist.p9_select_opposite", "Select Opposite", "UV_SYNC_SELECT"),
    ("animassist.p9_batch_mirror", "Batch Mirror", "LINKED"),
    ("animassist.p9_mirror_frame", "Mirror Frame", "FRAME_PREV"),
    ("animassist.p9_mirror_range", "Mirror Range", "SEQ_SEQUENCER"),
    ("animassist.p9_mirror_preview", "Mirror Preview", "PLAY"),
)


class ANIMASSIST_MT_p10_pie_key_tools(bpy.types.Menu):
    bl_idname = "ANIMASSIST_MT_p10_pie_key_tools"
    bl_label = "Key Tools"

    def draw(self, context):
        pie = self.layout.menu_pie()
        for op_id, label, icon in _KEY_TOOLS_ITEMS:
            try:
                pie.operator(op_id, text=label, icon=icon)
            except Exception:
                pie.separator()


class ANIMASSIST_MT_p10_pie_breakdown(bpy.types.Menu):
    bl_idname = "ANIMASSIST_MT_p10_pie_breakdown"
    bl_label = "Breakdown"

    def draw(self, context):
        pie = self.layout.menu_pie()
        for op_id, label, icon in _BREAKDOWN_ITEMS:
            try:
                pie.operator(op_id, text=label, icon=icon)
            except Exception:
                pie.separator()


class ANIMASSIST_MT_p10_pie_transform(bpy.types.Menu):
    bl_idname = "ANIMASSIST_MT_p10_pie_transform"
    bl_label = "Transform"

    def draw(self, context):
        pie = self.layout.menu_pie()
        for op_id, label, icon in _TRANSFORM_ITEMS:
            try:
                pie.operator(op_id, text=label, icon=icon)
            except Exception:
                pie.separator()


class ANIMASSIST_MT_p10_pie_proxy(bpy.types.Menu):
    bl_idname = "ANIMASSIST_MT_p10_pie_proxy"
    bl_label = "Proxy Controls"

    def draw(self, context):
        pie = self.layout.menu_pie()
        for op_id, label, icon in _PROXY_ITEMS:
            try:
                pie.operator(op_id, text=label, icon=icon)
            except Exception:
                pie.separator()


class ANIMASSIST_MT_p10_pie_switch(bpy.types.Menu):
    bl_idname = "ANIMASSIST_MT_p10_pie_switch"
    bl_label = "Space Switch"

    def draw(self, context):
        pie = self.layout.menu_pie()
        for op_id, label, icon in _SWITCH_ITEMS:
            try:
                pie.operator(op_id, text=label, icon=icon)
            except Exception:
                pie.separator()


class ANIMASSIST_MT_p10_pie_symmetry(bpy.types.Menu):
    bl_idname = "ANIMASSIST_MT_p10_pie_symmetry"
    bl_label = "Symmetry"

    def draw(self, context):
        pie = self.layout.menu_pie()
        for op_id, label, icon in _SYMMETRY_ITEMS:
            try:
                pie.operator(op_id, text=label, icon=icon)
            except Exception:
                pie.separator()


CLASSES = (
    ANIMASSIST_MT_p10_pie_key_tools,
    ANIMASSIST_MT_p10_pie_breakdown,
    ANIMASSIST_MT_p10_pie_transform,
    ANIMASSIST_MT_p10_pie_proxy,
    ANIMASSIST_MT_p10_pie_switch,
    ANIMASSIST_MT_p10_pie_symmetry,
)
