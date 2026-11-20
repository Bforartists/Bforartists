"""BoneCraft Task Board — Main panel, Quick Win section, and Health Bar.

Registers one top-level panel in the dedicated 'BoneCraft' N-panel tab:

    BONEFORGE_PT_taskboard
        ├─ Health bar row   (score badge + label + armature name)
        ├─ Quick Win section (top-3 highest impact/effort ratio tasks)
        └─ Remaining tasks (grouped by category, each group collapsible)

Each task card shows:
    [status icon]  Title  [Fix button if operator is set]
    Description text (muted, wrapped)

An operator BF_OT_OpenHealthCheck opens the existing rig_validator panel.
An operator BF_OT_InvalidateTaskCache forces re-analysis.
"""

import bpy
from bpy.types import Panel, Operator

from boneforge.i18n import T
from .analyzer import (
    get_tasks,
    get_quick_wins,
    get_health_score,
    get_tasks_by_category,
    invalidate,
    invalidate_all,
)
from .tasks import (
    CATEGORY_LABELS,
    CATEGORY_ICONS,
    STATUS_ERROR,
    STATUS_WARNING,
    STATUS_SUGGESTION,
)

import logging

logger = logging.getLogger(__name__)

# ── Health bar score colour thresholds ───────────────────────
# Blender theme icon names used as colour proxies in the label.
_SCORE_ICONS = {
    90: "FUND",        # green circle  — Excellent
    70: "LAYER_ACTIVE", # yellow       — Good
    40: "ERROR",        # orange/red   — Needs work
     0: "CANCEL",       # red          — Critical
}


def _score_icon(score: int) -> str:
    for threshold in sorted(_SCORE_ICONS, reverse=True):
        if score >= threshold:
            return _SCORE_ICONS[threshold]
    return "CANCEL"


# ── Shared draw helper ────────────────────────────────────────

def _draw_task_card(layout, task, context, compact: bool = False):
    """Draw a single task as a card row inside *layout*.

    compact=True omits the description lines (used in Quick Win section).
    context is required for text-wrap width calculation.
    """
    from boneforge.core.helpers import draw_wrapped, draw_wrapped_operator, _BOX, _ICON, _measure, line_room
    # One thing per line, so a card reads in the 132 px Tool Shelf: title, why, then the fix.
    box = layout.box()
    # The status icon (error / warning / suggestion) goes on the title when every word still fits
    # beside it; in a narrow shelf it moves in front of the button so no word is split.
    region = getattr(context, "region", None)
    measure = _measure(context) if region is not None else None
    icon_on_title = measure is None or all(
        measure(w) <= line_room(region.width, context.preferences.system.ui_scale, True, _BOX)
        for w in task.title.split())
    draw_wrapped(box.column(align=True), context, task.title, icon=task.icon if icon_on_title else 'NONE',
                 translate=True, inset=_BOX)

    if not compact and task.description:
        desc = box.column(align=True)
        desc.scale_y = 0.8
        draw_wrapped(desc, context, task.description, translate=True, inset=_BOX)

    row = box.row(align=True)
    if not icon_on_title:
        row.label(text="", icon=task.icon)
    if task.operator:
        play = 'PLAY' if icon_on_title else 'NONE'          # one icon per row leaves the text more room
        try:                                                # wraps instead of "Open ..." in a narrow shelf
            draw_wrapped_operator(row, context, task.operator, T(task.operator_text), icon=play,
                                  inset=_BOX + (0 if icon_on_title else _ICON))
        except Exception:
            # Operator not registered in this Blender session — show label only.
            row.label(text=T(task.operator_text), icon=play)


# ── Operators ─────────────────────────────────────────────────

class BF_OT_InvalidateTaskCache(Operator):
    """Force the Task Board to re-analyse the active armature."""
    bl_idname  = "boneforge.taskboard_refresh"
    bl_label   = "Refresh Task Board"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
        )

    def execute(self, context):
        obj = context.active_object
        if obj:
            invalidate(obj.name)
        self.report({'INFO'}, "Task Board refreshed.")
        return {'FINISHED'}


class BF_OT_InvalidateAllTaskCache(Operator):
    """Clear the Task Board cache for all armatures."""
    bl_idname  = "boneforge.taskboard_refresh_all"
    bl_label   = "Refresh All"
    bl_options = {'REGISTER'}

    def execute(self, context):
        invalidate_all()
        self.report({'INFO'}, "Task Board cache cleared.")
        return {'FINISHED'}


class BF_OT_OpenHealthCheck(Operator):
    """Run the avatar's rig checks and display the results."""
    bl_idname = "boneforge.open_health_check"
    bl_label = "Open Health Check"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        from boneforge.core import find_avatar_armature
        if find_avatar_armature(context) is None:
            cls.poll_message_set(T("Select an armature or a mesh bound to one."))
            return False
        return True

    def execute(self, context):
        from boneforge.core import find_avatar_armature
        from boneforge.core.tool_registry import get_registry
        armature = find_avatar_armature(context)
        if armature is None:
            self.report({'WARNING'}, T("Select an armature or a mesh bound to one."))
            return {'CANCELLED'}
        if not get_registry().is_enabled("phase2c_advanced"):
            self.report({'WARNING'}, T("Enable Advanced Rigging Systems in add-on preferences."))
            return {'CANCELLED'}
        try:
            bpy.ops.boneforge.run_validation.get_rna_type()
        except (AttributeError, KeyError, RuntimeError):
            self.report({'ERROR'}, T("Rig Validator failed to register. Check the console for details."))
            return {'CANCELLED'}
        with context.temp_override(active_object=armature, object=armature):
            result = bpy.ops.boneforge.run_validation()
        invalidate(armature.name)
        return result

    def invoke(self, context, event):
        result = self.execute(context)
        if result != {'FINISHED'}:
            return result
        return context.window_manager.invoke_popup(self, width=480)

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.label(text=T("Rig Validator"))
        if not hasattr(wm, "boneforge_validation_results"):
            layout.label(text=T("Enable Advanced Rigging Systems in add-on preferences."), icon='INFO')
            return
        results = wm.boneforge_validation_results
        failed = sum(item.status == 'fail' for item in results)
        warnings = sum(item.status == 'warn' for item in results)
        layout.label(text=T("Failed checks: {count}").format(count=failed))
        layout.label(text=T("Warnings: {count}").format(count=warnings))
        layout.template_list("BONEFORGE_UL_ValidationResults", "health_check_results", wm,
                             "boneforge_validation_results", wm, "boneforge_validation_index", rows=8)
        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("boneforge.open_health_check", text=T("Refresh Results"), icon='FILE_REFRESH')


# ── Main panel ────────────────────────────────────────────────

class BONEFORGE_PT_taskboard(Panel):
    """BoneCraft Task Board — persistent navigation surface."""
    bl_label       = " "
    bl_idname      = "BONEFORGE_PT_taskboard"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "BoneCraft"
    bl_parent_id   = "BF_PT_sb_overview"
    bl_order       = 1                     # Overview: Task Board first, then Rig Notes

    def draw_header(self, context):
        self.layout.label(text=T("Task Board"))

    @classmethod
    def poll(cls, context):
        # v3.3.5: avatar context — armature OR a mesh parented / armature-
        # modifier-bound to one. Lets Task Board stay visible during
        # weight painting / shape key editing on a child mesh.
        from boneforge.core import find_avatar_armature
        return find_avatar_armature(context) is not None

    def draw(self, context):
        from boneforge.core import find_avatar_armature
        from boneforge.core.helpers import draw_wrapped, _BOX
        layout = self.layout
        arm_obj = find_avatar_armature(context)
        if arm_obj is None:
            draw_wrapped(layout, context, T("No avatar armature found."), icon="INFO")
            return

        # ── Health bar ────────────────────────────────────────
        score, label = get_health_score(arm_obj)
        health_box = layout.box()
        health_row = health_box.row(align=True)
        health_row.label(text="", icon=_score_icon(score))      # the score itself goes on the wrapped line
        health_row.operator(
            "boneforge.open_health_check",
            text="", icon="VIEWZOOM",
        )
        health_row.operator(
            "boneforge.taskboard_refresh",
            text="", icon="FILE_REFRESH",
        )
        draw_wrapped(health_box, context, f"{score} {label}  ·  {arm_obj.name}", inset=_BOX)

        tasks = get_tasks(arm_obj)

        if not tasks:
            layout.separator()
            col = layout.column()
            col.scale_y = 1.2
            draw_wrapped(col, context, T("No issues found — rig looks good!"), icon="CHECKMARK")
            return

        # ── Quick Win section ─────────────────────────────────
        quick_wins = get_quick_wins(arm_obj, n=3)
        if quick_wins:
            layout.separator(factor=0.5)
            draw_wrapped(layout, context, T("Quick Wins"))

            for task in quick_wins:
                _draw_task_card(layout, task, context, compact=False)

        # Quick Wins are already shown above; each task gets one card.
        quick_win_ids = {task.task_id for task in quick_wins}
        remaining_count = sum(task.task_id not in quick_win_ids for task in tasks)
        if not remaining_count:
            return

        # ── Remaining task list ───────────────────────────────
        layout.separator(factor=0.5)
        draw_wrapped(layout, context, f"{T('Remaining Tasks')} ({remaining_count})")

        for category, cat_tasks in get_tasks_by_category(arm_obj):
            cat_tasks = [task for task in cat_tasks if task.task_id not in quick_win_ids]
            if not cat_tasks:
                continue
            cat_label = CATEGORY_LABELS.get(category, category.title())
            cat_icon  = CATEGORY_ICONS.get(category, "DOT")

            # Collapsible sub-section per category.
            prop_key = f"boneforge_taskboard_collapsed_{category}"
            scene    = context.scene
            collapsed = scene.get(prop_key, False)

            expand_icon = 'TRIA_RIGHT' if collapsed else 'TRIA_DOWN'
            from boneforge.core.helpers import draw_wrapped_operator
            for op in draw_wrapped_operator(layout, context, "boneforge.taskboard_toggle_category",
                                            f"{cat_label} ({len(cat_tasks)})", icon=expand_icon, emboss=False):
                op.category = category                     # every line of a wrapped name toggles it

            if not collapsed:
                for task in cat_tasks:
                    _draw_task_card(layout, task, context, compact=False)


class BONEFORGE_PT_taskboard_no_arm(Panel):
    """Shown in the Overview hub when no armature is active."""
    bl_label       = " "
    bl_idname      = "BONEFORGE_PT_taskboard_no_arm"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "BoneCraft"
    bl_parent_id   = "BF_PT_sb_overview"

    def draw_header(self, context):
        self.layout.label(text=T("Task Board"))

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is None
            or context.active_object.type != 'ARMATURE'
        )

    def draw(self, context):
        # v3.2.2: the duplicate Start Auto-Rig button was removed here per
        # user feedback. The Auto-Rig Wizard panel (bl_order = -100) is
        # always visible at the top of the BoneForge tab and carries the
        # only Start button. Keep a hint so this Task Board sub-panel
        # doesn't render blank when no armature is selected.
        layout = self.layout
        layout.label(text=T("No armature selected."), icon='INFO')
        layout.separator(factor=0.5)
        layout.label(
            text=T("Use the 'Auto-Rig Wizard' panel above to start a new rig."),
            icon='INFO',
        )


# ── Category collapse toggle operator ────────────────────────

class BF_OT_ToggleTaskCategory(Operator):
    """Toggle collapse state for a task category in the Task Board."""
    bl_idname  = "boneforge.taskboard_toggle_category"
    bl_label   = "Toggle Category"
    bl_options = {'REGISTER', 'INTERNAL'}

    category: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, default="")

    def execute(self, context):
        if not self.category:
            return {'CANCELLED'}
        prop_key = f"boneforge_taskboard_collapsed_{self.category}"
        current  = context.scene.get(prop_key, False)
        context.scene[prop_key] = not current
        return {'FINISHED'}


# ── Registration ────────────────────────────────────────────

_CLASSES = (
    BF_OT_InvalidateTaskCache,
    BF_OT_InvalidateAllTaskCache,
    BF_OT_OpenHealthCheck,
    BF_OT_ToggleTaskCategory,
    BONEFORGE_PT_taskboard,
)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
