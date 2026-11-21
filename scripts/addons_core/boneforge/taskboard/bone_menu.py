"""BoneCraft Task Board — Bone right-click context menu.

Prepends a 'BoneCraft' sub-menu to the Pose Mode W-key / right-click
context menu (VIEW3D_MT_pose_context_menu).  The sub-menu exposes the
most-used advanced-rigging operators directly on the active bone so
users never need to hunt through Phase 2C panels.

Menu items
----------
  Add Space Switch     → boneforge.add_space          (advanced_rigging/space_switch.py)
  Add SDK Driver       → boneforge.add_sdk_driver      (advanced_rigging/sdk_system.py)
  Add to Spline Chain  → boneforge.add_spline_chain    (advanced_rigging/spline_ik.py)
  Set as Ribbon IK     → boneforge.setup_ribbon_ik     (advanced_rigging/ribbon.py)
  Add Chain Dynamics   → boneforge.add_chain_dynamics  (advanced_rigging/chain_dynamics.py)
  ──────────────────
  Open Task Board      → (switches focus to the BoneCraft N-panel tab hint)
  Run Health Check     → boneforge.open_health_check

All items use poll() guards so they only appear when the underlying
operator is available.  The menu itself is always appended even if
individual operators are absent — a missing operator silently skips.
"""

import bpy
from bpy.types import Menu, Operator
from boneforge.i18n import T


# ── Items definition ──────────────────────────────────────────
# (label, icon, bl_idname, requires_pose_mode)

_MENU_ITEMS = (
    ("Add Space Switch",    "CONSTRAINT_BONE", "boneforge.add_space",         True),
    ("Add SDK Driver",      "DRIVER",           "boneforge.add_sdk_driver",    True),
    ("Add to Spline Chain", "CURVE_DATA",       "boneforge.add_spline_chain",  True),
    ("Set as Ribbon IK",    "MOD_SMOOTH",       "boneforge.setup_ribbon_ik",   True),
    ("Add Chain Dynamics",  "FORCE_VORTEX",     "boneforge.add_chain_dynamics",True),
)

_HEALTH_ITEMS = (
    ("Run Health Check",    "VIEWZOOM",         "boneforge.open_health_check", False),
    ("Refresh Task Board",  "FILE_REFRESH",     "boneforge.taskboard_refresh", True),
)


def _operator_exists(bl_idname: str) -> bool:
    """Return True if an operator with this bl_idname is registered."""
    category, name = bl_idname.split(".", 1)
    cat_ops = getattr(bpy.ops, category, None)
    if cat_ops is None:
        return False
    return hasattr(cat_ops, name)


# ── Sub-menu ──────────────────────────────────────────────────

class BF_MT_BoneContextMenu(Menu):
    """BoneCraft operators for the selected bone."""
    bl_label   = "BoneCraft"
    bl_idname  = "BF_MT_bone_context_menu"

    def draw(self, context):
        layout = self.layout
        pbone  = context.active_pose_bone

        # Rigging tools section.
        layout.label(text=T("Rigging"))
        any_rigging = False
        for label, icon, idname, needs_pose in _MENU_ITEMS:
            if needs_pose and pbone is None:
                continue
            if _operator_exists(idname):
                layout.operator(idname, text=label, icon=icon)
                any_rigging = True

        if not any_rigging:
            layout.label(text=T("(Advanced rigging operators not loaded)"), icon='INFO')

        # Diagnostics section.
        layout.separator()
        layout.label(text=T("Diagnostics"))
        for label, icon, idname, needs_pose in _HEALTH_ITEMS:
            if needs_pose and pbone is None:
                continue
            if _operator_exists(idname):
                layout.operator(idname, text=label, icon=icon)

        # Hint toward BoneForge tab.
        layout.separator()
        layout.label(text=T("→ See BoneCraft tab for Task Board"))


# ── Prepend function ──────────────────────────────────────────

def _prepend_to_pose_menu(self, context):
    """Draw function injected into VIEW3D_MT_pose_context_menu."""
    if (
        context.active_object is not None
        and context.active_object.type == 'ARMATURE'
        and context.mode == 'POSE'
    ):
        self.layout.menu(BF_MT_BoneContextMenu.bl_idname, icon='TOOL_SETTINGS')
        self.layout.separator()


# ── Registration ──────────────────────────────────────────────

def register():
    bpy.utils.register_class(BF_MT_BoneContextMenu)
    bpy.types.VIEW3D_MT_pose_context_menu.prepend(_prepend_to_pose_menu)


def unregister():
    bpy.types.VIEW3D_MT_pose_context_menu.remove(_prepend_to_pose_menu)
    try:
        bpy.utils.unregister_class(BF_MT_BoneContextMenu)
    except RuntimeError:
        pass
