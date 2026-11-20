"""BoneCraft Task Board — Bone Inspector panel.

Expert opt-in panel that surfaces everything BoneCraft knows about the
currently selected pose bone in one place:

  ╔══════════════════════════════════╗
  ║  Bone Inspector  [active bone]   ║
  ╠═══════════════╦══════════════════╣
  ║ Basics        ║ name, length,    ║
  ║               ║ head/tail, roll  ║
  ╠═══════════════╬══════════════════╣
  ║ Constraints   ║ each constraint  ║
  ║               ║ with type+target ║
  ╠═══════════════╬══════════════════╣
  ║ BoneCraft     ║ deform_layer,    ║
  ║ Properties    ║ SDK drivers,     ║
  ║               ║ space-switch,    ║
  ║               ║ chain dynamics   ║
  ╠═══════════════╬══════════════════╣
  ║ Skin Weights  ║ top-5 vertex     ║
  ║               ║ groups by weight ║
  ╚═══════════════╩══════════════════╝

The panel lives in the 'BoneCraft' N-panel tab, order=50, and is
DEFAULT_CLOSED so it doesn't clutter the tab for casual users.
It only appears in Pose mode with an active bone.

No new operators are introduced here — the panel is purely read-only
except for a "Copy Name" shortcut and a small SDK shortcut link.
"""

import math

import bpy
from bpy.types import Panel

import logging
from boneforge.i18n import T

logger = logging.getLogger(__name__)

# ── Helpers ───────────────────────────────────────────────────

def _constraint_icon(ctype: str) -> str:
    """Map a Blender constraint type string to a reasonable icon."""
    _MAP = {
        "IK":                    "CON_KINEMATIC",
        "COPY_ROTATION":         "CON_ROTLIKE",
        "COPY_LOCATION":         "CON_LOCLIKE",
        "COPY_SCALE":            "CON_SIZELIKE",
        "COPY_TRANSFORMS":       "CON_TRANSLIKE",
        "LIMIT_ROTATION":        "CON_ROTLIMIT",
        "LIMIT_LOCATION":        "CON_LOCLIMIT",
        "LIMIT_SCALE":           "CON_SIZELIMIT",
        "TRACK_TO":              "CON_TRACKTO",
        "DAMPED_TRACK":          "CON_TRACKTO",
        "LOCKED_TRACK":          "CON_LOCKTRACK",
        "STRETCH_TO":            "CON_STRETCHTO",
        "FLOOR":                 "CON_FLOOR",
        "CHILD_OF":              "CON_CHILDOF",
        "TRANSFORM":             "CON_TRANSFORM",
        "SPLINE_IK":             "CON_SPLINEIK",
        "ACTION":                "ACTION",
        "ARMATURE":              "ARMATURE_DATA",
        "CLAMP_TO":              "CON_CLAMPTO",
        "PIVOT":                 "CON_PIVOT",
        "SHRINKWRAP":            "CON_SHRINKWRAP",
    }
    return _MAP.get(ctype, "CONSTRAINT_BONE")


def _get_weight_entries(armature_obj, bone_name: str) -> list:
    """Return list of (mesh_name, group_name, weight) tuples, sorted by weight desc.

    Walks all mesh children that use the armature modifier.
    """
    entries = []
    for child in armature_obj.children:
        if child.type != 'MESH':
            continue
        # Only look at meshes bound to this armature.
        has_arm_mod = any(
            m.type == 'ARMATURE' and m.object is armature_obj
            for m in child.modifiers
        )
        if not has_arm_mod:
            continue

        vg = child.vertex_groups.get(bone_name)
        if vg is None:
            continue

        # Accumulate weights for this vertex group.
        total_weight = 0.0
        count        = 0
        for vert in child.data.vertices:
            for ge in vert.groups:
                if ge.group == vg.index:
                    total_weight += ge.weight
                    count += 1
                    break

        if count > 0:
            avg = total_weight / count
            entries.append((child.name, vg.name, avg, count))

    entries.sort(key=lambda e: e[2], reverse=True)
    return entries[:8]   # cap at 8 rows


def _get_sdk_drivers(armature_obj, bone_name: str) -> list:
    """Return SDK driver relationships where this bone is driver or target.

    Reads from armature animation data if present.  Returns a list of
    dicts with keys: type ('driver' | 'driven'), data_path, expr.
    """
    results = []
    if armature_obj.animation_data is None:
        return results

    for driver in armature_obj.animation_data.drivers:
        dp = driver.data_path
        # Check if driver variable references this bone.
        for var in driver.driver.variables:
            for tgt in var.targets:
                if tgt.bone_target == bone_name:
                    results.append({
                        "type":      "driver",
                        "data_path": dp,
                        "expr":      driver.driver.expression,
                    })
        # Check if the driven path belongs to this bone.
        if f'bones["{bone_name}"]' in dp or f"bones['{bone_name}']" in dp:
            results.append({
                "type":      "driven",
                "data_path": dp,
                "expr":      driver.driver.expression,
            })

    # Deduplicate by data_path.
    seen = set()
    unique = []
    for r in results:
        key = (r["type"], r["data_path"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def _get_bf_bone_props(pbone) -> list:
    """Return list of (label, value) for known BoneCraft custom props on a pose bone."""
    props = []

    # Edit-bone custom props (access via pbone.bone).
    ebone = pbone.bone
    for key, label in (
        ("boneforge_deform_layer",   "Deform Layer"),
        ("boneforge_ik_target",      "IK Target Bone"),
        ("boneforge_space_switch",   "Space Switch"),
        ("boneforge_sdk_role",       "SDK Role"),
    ):
        val = ebone.get(key)
        if val is not None:
            props.append((label, str(val)))

    # Pose-bone custom props.
    for key, label in (
        ("boneforge_twist_factor",  "Twist Factor"),
        ("boneforge_dynamic_chain", "Dynamic Chain"),
    ):
        val = pbone.get(key)
        if val is not None:
            props.append((label, str(val)))

    return props


# ── Panel ─────────────────────────────────────────────────────

class BONEFORGE_PT_bone_inspector(Panel):
    """Expert read-out for the selected pose bone — BoneCraft properties,
    constraints, drivers, and skin-weight summary."""

    bl_label       = " "
    bl_idname      = "BONEFORGE_PT_bone_inspector"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"
    bl_category    = "BoneCraft"
    bl_parent_id   = "BF_PT_sb_animate"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Bone Inspector"))

    @classmethod
    def poll(cls, context):
        return (
            context.mode == 'POSE'
            and context.active_pose_bone is not None
        )

    def draw(self, context):
        layout   = self.layout
        pbone    = context.active_pose_bone
        arm_obj  = context.active_object
        ebone    = pbone.bone

        # ── Header badge ──────────────────────────────────────
        header_row = layout.row(align=True)
        header_row.label(text=pbone.name, icon='BONE_DATA')
        header_row.operator(
            "wm.context_set_string",
            text="", icon='COPYDOWN',
            emboss=False,
        ).value = pbone.name

        layout.separator(factor=0.4)

        # ── Section: Basics ───────────────────────────────────
        box = layout.box()
        box.label(text=T("Basics"), icon='INFO')

        col = box.column(align=True)
        col.scale_y = 0.85

        # Length
        length = (ebone.tail_local - ebone.head_local).length
        col.label(text=f"Length:  {length:.4f}")

        # Head / Tail in armature space
        h = ebone.head_local
        t = ebone.tail_local
        col.label(text=f"Head:   ({h.x:.3f}, {h.y:.3f}, {h.z:.3f})")
        col.label(text=f"Tail:   ({t.x:.3f}, {t.y:.3f}, {t.z:.3f})")

        # Roll
        col.label(text=f"Roll:    {math.degrees(ebone.roll):.1f}°")

        # Deform flag
        col.label(
            text=f"Deform:  {'Yes' if ebone.use_deform else 'No'}",
            icon='CHECKMARK' if ebone.use_deform else 'RADIOBUT_OFF',
        )

        # Parent
        if ebone.parent:
            col.label(text=f"Parent:  {ebone.parent.name}")

        layout.separator(factor=0.2)

        # ── Section: Constraints ──────────────────────────────
        constraints = pbone.constraints
        cbox = layout.box()
        cbox.label(
            text=f"Constraints  ({len(constraints)})",
        )

        if not constraints:
            cbox.label(text=T("None"), icon='RADIOBUT_OFF')
        else:
            for c in constraints:
                row = cbox.row(align=True)
                row.label(text="", icon=_constraint_icon(c.type))
                sub = row.column(align=True)
                sub.scale_y = 0.8

                # Name + type on first line.
                sub.label(text=f"{c.name}  [{c.type}]")

                # Target info if present.
                tgt = getattr(c, 'target', None)
                if tgt:
                    tname = tgt.name
                    sbone = getattr(c, 'subtarget', '')
                    if sbone:
                        sub.label(text=f"  → {tname} / {sbone}")
                    else:
                        sub.label(text=f"  → {tname}")

                # Mute/enabled.
                if not c.enabled:
                    sub.label(text=T("  (muted)"))

        layout.separator(factor=0.2)

        # ── Section: BoneForge Properties ─────────────────────
        bf_props = _get_bf_bone_props(pbone)
        bf_box = layout.box()
        bf_box.label(text=T("BoneCraft Properties"))

        if not bf_props:
            bf_box.label(text=T("No BoneCraft data on this bone"), icon='RADIOBUT_OFF')
        else:
            col = bf_box.column(align=True)
            col.scale_y = 0.85
            for label, value in bf_props:
                col.label(text=f"{label}:  {value}")

        layout.separator(factor=0.2)

        # ── Section: SDK / Drivers ────────────────────────────
        sdk_entries = _get_sdk_drivers(arm_obj, pbone.name)
        sdk_box = layout.box()
        sdk_box.label(
            text=f"SDK Drivers  ({len(sdk_entries)})",
        )

        if not sdk_entries:
            sdk_box.label(text=T("No drivers linked to this bone"), icon='RADIOBUT_OFF')
        else:
            col = sdk_box.column(align=True)
            col.scale_y = 0.8
            for entry in sdk_entries:
                role_icon = 'DRIVER' if entry['type'] == 'driver' else 'LINKED'
                role_text = T('Drives') if entry['type'] == 'driver' else T('Driven')
                col.label(
                    text=f"{role_text}: {entry['data_path']}",
                    icon=role_icon,
                )
                if entry['expr']:
                    col.label(text=f"  expr: {entry['expr'][:60]}")

        layout.separator(factor=0.2)

        # ── Section: Skin Weights ─────────────────────────────
        weight_entries = _get_weight_entries(arm_obj, pbone.name)
        w_box = layout.box()
        w_box.label(
            text=f"Skin Weights  ({len(weight_entries)} mesh{'es' if len(weight_entries) != 1 else ''})",
        )

        if not weight_entries:
            w_box.label(
                text=T("Not weighted to any child mesh"),
                icon='RADIOBUT_OFF',
            )
        else:
            col = w_box.column(align=True)
            col.scale_y = 0.85
            for mesh_name, _vg, avg_weight, vert_count in weight_entries:
                # Visual weight bar using repeated '█' chars (max 10 blocks).
                filled = round(avg_weight * 10)
                bar    = '█' * filled + '░' * (10 - filled)
                col.label(
                    text=f"{mesh_name}  {bar}  {avg_weight:.3f}  ({vert_count}v)",
                )


# ── Registration ──────────────────────────────────────────────

_CLASSES = (
    BONEFORGE_PT_bone_inspector,
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
