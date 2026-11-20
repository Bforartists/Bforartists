"""BoneCraft — Sidebar tab consolidation (v6.1.1 UX revision).

4 tabs in the BoneCraft category. Rig Builder is not in the sidebar: it lives
in Properties > Scene tab (see RB_CLASSES and autorig/rb_placement.py):

  [Setup Rigging]  (order=10)
                   Retarget, Rigify Tools

  [Skin]           (order=20)
                   Weight Tools, Correctives

  [VRChat]         (order=35, bl_category=CATS — moved to CATS tab)
                   Cluster A — VRChat Setup:   A-Naming Extras,
                                               A-Set Up Humanoid Bones
                   Cluster B — Body & Physics: B-Add Hair Physics,
                                               B-Attach Clothing,
                                               B-Viseme Library

  [Import/Export]  (order=50, bl_category=CATS — moved to CATS tab,
                   registered by io_hub/panel.py)
                   Format bridges (VRM, MMD), Unity/VRChat export, Unreal FBX

  [Review]         (order=40)   (bl_idname=BF_PT_sb_animate — kept for child links)
                   Collections, Pose Library, Graph Tools,
                   Rig Validator, Rig Readme, Bone Inspector

Project strip: Overview (order=-1000) — avatar name + Task Board + Rig Notes.
Task Board and Bone Inspector are registered by panel.py / bone_inspector.py.

REGISTRATION ORDER: sidebar.py registers before panel.py / bone_inspector.py
so parent idnames exist when those modules register their children.

Hierarchy (all bl_space_type=VIEW_3D, bl_region_type=UI, bl_category=BoneCraft)
---------------------------------------------------------------------------
BF_PT_sb_overview      "Overview"    order=-1000   (project strip)
    BONEFORGE_PT_taskboard          <- panel.py
    BONEFORGE_PT_taskboard_no_arm   <- panel.py
    BF_PT_sb_rig_notes   "Rig Notes"

BF_PT_sb_setup         "Setup Rigging"  order=10
    BF_PT_sb_retarget    "Retarget"
    BF_PT_sb_rigify      "Rigify Tools"

BF_PT_rb_setup         "Setup Rigging"  order=0   (bl_category=Rig Builder)
    BF_PT_sb_quick_rig   "Quick Rig"
    BF_PT_sb_wizard      "Auto-Rig Wizard"
    BF_PT_rb_mannequin   "Mannequin"

BF_PT_sb_skin          "Skin"        order=20
    BF_PT_sb_weights     "Weight Tools"
    BF_PT_sb_correctives "Correctives"

BF_PT_sb_vrchat        "VRChat"      order=35
    BF_PT_sb_vrc_humanoid  "Set Up Humanoid Bones" order=2  (cluster A)
    BF_PT_sb_vrc_hair      "Add Hair Physics"      order=4  (cluster B)
    BONEFORGE_PT_p2c_viseme_library "Viseme Library" order=6 (advanced_rigging/viseme.py)

BF_PT_sb_animate       "Review"      order=40   (bl_idname kept for child links)
    BF_PT_sb_collections  "Collections"
    BF_PT_sb_pose_lib     "Pose Library"
    BF_PT_sb_graph        "Graph Tools"
    BF_PT_sb_rig_validator "Rig Validator"
    BF_PT_sb_rig_readme    "Rig Readme"
    BONEFORGE_PT_bone_inspector     <- bone_inspector.py
    BONEFORGE_PT_control_layer      <- advanced_rigging/control_layer.py
    BONEFORGE_PT_picker             <- control_ui/picker.py

BF_PT_sb_io            "Import / Export"  order=50  (bl_category=CATS) <- io_hub/panel.py
    BONEFORGE_PT_profile_export     <- io_hub/profile_export.py
"""

import bpy
from bpy.types import Panel

import logging
from boneforge.i18n import T
from boneforge.autorig import rb_placement

logger = logging.getLogger(__name__)

# -- Constants -------------------------------------------------

_SPACE    = 'VIEW_3D'
_REGION   = 'UI'
_CAT      = 'BoneCraft'
_CATS_CAT = 'CATS'

_RB_CAT = 'Rig Builder'


def _active_is(context, *types):
    """True when the active object is one of ``types`` (show-don't-hide gates)."""
    obj = context.active_object
    return obj is not None and obj.type in types


def _avatar_armature(context):
    from boneforge.core import find_avatar_armature
    return find_avatar_armature(context)


# -- Helpers ---------------------------------------------------

# =============================================================
# Confession Layer — H6 + A1 (Brainstorm Council)
#
# Classifies the active pose bone by jurisdiction and shows one
# plain-language sentence explaining what it is and how to use it.
# On first access for each armature a mapping is built and cached;
# subsequent draws are a dict lookup only.
# =============================================================

_confession_cache: dict = {}  # armature_name -> {fingerprint, bone_map}


def _build_confession_bone_map(arm_obj) -> dict:
    """Build bone classification map for a generated Rigify rig.

    Returns {bone_name: {jurisdiction, ctrl_name, orphaned, ik_fk_prop}}.

    jurisdiction values:
      CONTROL    — animator-facing controller (custom shape present)
      DEFORM     — DEF- prefix: driven by a controller
      PASSTHROUGH— MCH-/ORG-: internal mechanism, no user-facing role
      UNKNOWN    — no prefix and no custom shape (root, pivot, legacy)
    """
    all_names = {b.name for b in arm_obj.data.bones}
    pose_bones = arm_obj.pose.bones
    bone_map: dict = {}

    for bone in arm_obj.data.bones:
        name = bone.name
        pb = pose_bones.get(name)

        if name.startswith("DEF-"):
            base = name[4:]
            ctrl_name = None
            for candidate in (base, f"{base}.ctl", f"ctrl.{base}"):
                if candidate in all_names and not candidate.startswith(
                    ("DEF-", "MCH-", "ORG-")
                ):
                    ctrl_name = candidate
                    break
            if ctrl_name is None:
                base_clean = base.rstrip(".0123456789")
                for n in all_names:
                    if n.startswith(("DEF-", "MCH-", "ORG-")):
                        continue
                    if n.rstrip(".0123456789") == base_clean:
                        ctrl_name = n
                        break
            # A1 — Orphan Signal
            orphaned = (ctrl_name is not None) and (ctrl_name not in all_names)
            bone_map[name] = {
                "jurisdiction": "DEFORM",
                "ctrl_name": ctrl_name,
                "orphaned": orphaned,
                "ik_fk_prop": None,
            }

        elif name.startswith(("MCH-", "ORG-")):
            bone_map[name] = {
                "jurisdiction": "PASSTHROUGH",
                "ctrl_name": None,
                "orphaned": False,
                "ik_fk_prop": None,
            }

        else:
            has_custom_shape = pb is not None and pb.custom_shape is not None
            ik_fk_prop = None
            if pb is not None:
                for prop_key in ("ik_fk_switch", "IK_FK", "ik_fk", "IK/FK"):
                    if prop_key in pb.keys():
                        ik_fk_prop = prop_key
                        break
            bone_map[name] = {
                "jurisdiction": "CONTROL" if has_custom_shape else "UNKNOWN",
                "ctrl_name": None,
                "orphaned": False,
                "ik_fk_prop": ik_fk_prop,
            }

    return bone_map


def _get_confession_bone_map(arm_obj) -> dict:
    """Return cached bone map, rebuilding when bone count changes."""
    key = arm_obj.name
    fingerprint = len(arm_obj.data.bones)
    cached = _confession_cache.get(key)
    if cached is None or cached["fingerprint"] != fingerprint:
        bone_map = _build_confession_bone_map(arm_obj)
        _confession_cache[key] = {"fingerprint": fingerprint, "bone_map": bone_map}
        return bone_map
    return cached["bone_map"]


def _draw_confession_layer(layout, context):
    """Draw the Confession Layer for the active pose bone.

    Shows a plain-language sentence explaining bone jurisdiction.
    When no bone is selected shows an armature-level summary so the
    panel is never blank (idle frame).
    """
    obj = context.active_object
    if obj is None or obj.type != "ARMATURE":
        return

    try:
        from boneforge.autorig.quick_human import _is_generated_rigify_control_rig
    except ImportError:
        return

    if not _is_generated_rigify_control_rig(obj):
        return

    try:
        bone_map = _get_confession_bone_map(obj)
    except Exception:
        layout.label(text="Bone index unavailable.", icon="ERROR")
        return

    box = layout.box()
    col = box.column(align=True)
    col.scale_y = 0.85

    pb = context.active_pose_bone

    if pb is None:
        ctrl_count = sum(
            1 for info in bone_map.values() if info["jurisdiction"] == "CONTROL"
        )
        ik_count = sum(
            1 for info in bone_map.values()
            if info["jurisdiction"] == "CONTROL" and info["ik_fk_prop"] is not None
        )
        total = len(bone_map)
        col.label(text="Enter Pose Mode, select a bone to see its role.",
                  icon="INFO")
        col.separator(factor=0.4)
        col.label(
            text=f"{total} bones  •  {ctrl_count} controllers"
                 f"  •  {ik_count} IK/FK"
        )
        return

    name = pb.name
    info = bone_map.get(
        name,
        {"jurisdiction": "UNKNOWN", "ctrl_name": None, "orphaned": False,
         "ik_fk_prop": None},
    )
    jurisdiction = info["jurisdiction"]

    if jurisdiction == "DEFORM":
        ctrl = info["ctrl_name"]
        if info["orphaned"]:
            col.label(text="DEF bone — follows a controller.")
            col.label(text=f"Expected: \"{ctrl}\"")
            col.label(text="— but that control is missing from this rig.")
        elif ctrl:
            col.label(text="DEF bone — follows its controller.")
            col.label(text=f"Select \"{ctrl}\" to pose this part.")
        else:
            col.label(text="DEF bone — driven by a controller.")
            col.label(text="Find and select its control bone to pose.")

    elif jurisdiction == "PASSTHROUGH":
        prefix = "MCH" if name.startswith("MCH-") else "ORG"
        col.label(text=f"{prefix} bone — internal mechanism.")
        col.label(text="Not for direct animation.")
        col.label(text="Deselect and select a controller instead.")

    elif jurisdiction == "CONTROL":
        ik_fk_prop = info["ik_fk_prop"]
        if ik_fk_prop is not None:
            try:
                val = float(pb[ik_fk_prop])
                mode = "IK" if val < 0.5 else "FK"
                col.label(text=f"Controller — {mode} mode.")
                if mode == "IK":
                    col.label(text="Move/rotate this bone; the chain follows.")
                    col.label(text=f"Switch to FK: set \"{ik_fk_prop}\" → 1.0")
                else:
                    col.label(text="Rotate each joint independently.")
                    col.label(text=f"Switch to IK: set \"{ik_fk_prop}\" → 0.0")
            except (KeyError, TypeError, ValueError):
                col.label(text="Controller bone — grab/rotate to pose.")
        else:
            col.label(text="Controller bone — grab/rotate to pose.")
            col.label(text="This drives the rig's deform bones.")

    else:
        col.label(text="No declared role for this bone.", icon="QUESTION")
        col.label(text="May be a root, pivot, or legacy control.")
        col.label(text="Treat as uncharted — test before keying.")


def _delegate_draw(self, context, import_path: str, class_name: str, target=None):
    """Import *class_name* from *import_path* and call its draw().

    Exception handling is intentionally split:
    - ImportError   : phase not loaded — expected in partial installs.
    - AttributeError: class name mismatch — developer error.
    - All others    : runtime draw crash — log + show ERROR label.
    """
    try:
        mod = __import__(import_path, fromlist=[class_name])
    except ImportError:
        self.layout.label(
            text=f"{import_path.split('.')[-1]} not loaded",
            icon='INFO',
        )
        return

    try:
        cls = getattr(mod, class_name)
    except AttributeError:
        self.layout.label(
            text=f"{class_name} not found in module",
            icon='QUESTION',
        )
        return

    try:
        cls.draw(target or self, context)
    except Exception as exc:
        logger.warning(f"[BoneCraft Sidebar] draw error in {class_name}: {exc}")
        self.layout.label(text=T("Draw error -- see console"), icon='ERROR')


class _CompactPanel:
    """Stand-in ``self`` for Rig Builder draw code: same panel, compact layout."""

    def __init__(self, panel, layout):
        object.__setattr__(self, "_panel", panel)
        object.__setattr__(self, "layout", layout)

    def __getattr__(self, name):
        return getattr(self._panel, name)


def rb_draw_target(panel, context):
    """What Rig Builder draw code should use as ``self`` in this region."""
    region = getattr(context, "region", None)
    width = getattr(region, "width", None)
    if width is None:
        return panel
    if not rb_placement.is_compact(width, context.preferences.system.ui_scale):
        return panel
    from boneforge.autorig.compact_layout import CompactLayout
    return _CompactPanel(panel, CompactLayout(panel.layout))


def _draw_explainer(layout, context, line1, line2=None):
    """Teaching text; hidden when Show Helpers is off (Preferences, or VRChat's Compact Mode)."""
    from boneforge.core.helpers import draw_helper
    draw_helper(layout, context, line1, line2)


# =============================================================
# HUB: Overview / Project Strip  (order=-1000)
# Always visible when an avatar armature is in context.
# Shows the active avatar name; Task Board + Rig Notes are children.
# =============================================================

class BF_PT_sb_overview(Panel):
    """BoneCraft -> Overview hub: project strip, Task Board, Rig Notes.

    Sits at order=-1000 so it dominates the BoneCraft tab. Acts as a
    persistent project strip — avatar name, quick health, and notes —
    rather than a navigation hub. Task Board and Rig Notes are children
    registered by panel.py and here respectively.
    """
    bl_label       = " "
    bl_idname      = "BF_PT_sb_overview"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_order       = -1000

    def draw_header(self, context):
        self.layout.label(text=T("Overview"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        try:
            if not context.preferences.addons["boneforge"].preferences.show_tab_boneforge:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        if not (_avatar_armature(context) is not None):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Overview needs an avatar: select its armature or one of its meshes.', ('ARMATURE',))
            return
        from boneforge.core import find_avatar_armature
        arm = find_avatar_armature(context)
        if arm is None:
            return
        from boneforge.core.helpers import draw_wrapped
        draw_wrapped(self.layout, context, arm.name, icon='ARMATURE_DATA')     # the active avatar, whole name


class BF_PT_sb_rig_notes(Panel):
    """Rig notes / README — advanced_rigging. Child of Overview."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_rig_notes"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_overview"
    bl_options     = {'DEFAULT_CLOSED'}
    bl_order       = 2                     # below Task Board

    def draw_header(self, context):
        self.layout.label(text=T("Rig Notes"))

    @classmethod
    def poll(cls, context):
        from boneforge.core import find_avatar_armature
        return find_avatar_armature(context) is not None

    def draw(self, context):
        _delegate_draw(self, context,
                       "boneforge.advanced_rigging.rig_notes",
                       "BONEFORGE_PT_p2c_rig_notes")


# =============================================================
# TAB: Rig Builder — unchanged, creation workflows only.
# =============================================================

class BF_PT_rb_setup(Panel):
    """Rig Builder -> Setup hub: Quick Rig, Auto-Rig Wizard, Mannequin."""
    bl_label       = " "
    bl_idname      = "BF_PT_rb_setup"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _RB_CAT
    bl_order       = 1     # first BoneCraft section in the Scene tab

    def draw_header(self, context):
        self.layout.label(text=T("Rig Builder"))

    @classmethod
    def poll(cls, context):
        # In Properties > Scene tab while Scene Properties is on. The Rig Builder
        # show switch only controls the viewport copy (see _register_rig_builder_shelf).
        from boneforge.core.tab_switches import scene_tab_on
        return scene_tab_on(context)

    def draw(self, context):
        layout = rb_draw_target(self, context).layout
        if context.active_object is None or context.active_object.type not in {'ARMATURE', 'MESH'}:
            layout.label(
                text=T("Pick a rig source below to start."),
                icon='INFO',
            )


# =============================================================
# HUB: Setup Rigging  (order=10)
# =============================================================

class BF_PT_sb_setup(Panel):
    """BoneCraft -> Setup hub: retarget, Rigify config."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_setup"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_order       = 10

    def draw_header(self, context):
        self.layout.label(text=T("Setup Rigging"))

    @classmethod
    def poll(cls, context):
        try:
            prefs = context.preferences.addons["boneforge"].preferences
            if not prefs.show_tab_boneforge:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        obj = context.active_object
        if obj is None or obj.type != 'ARMATURE':
            from boneforge.core.helpers import draw_wrapped
            draw_wrapped(self.layout, context, T("Select an armature to see Retarget and Rigify Tools."), icon='INFO')
            return
        _draw_explainer(
            self.layout, context,
            T("Tools for rigs you already have."),
            T("Use Rig Builder to create a new rig."),
        )


class BF_PT_sb_quick_rig(Panel):
    """Premade Quick Rig library — Rig Builder tab."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_quick_rig"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _RB_CAT
    bl_parent_id   = "BF_PT_rb_setup"
    bl_order       = 2                     # after the Auto-Rig Wizard (owner, 2026-10-10)

    def draw_header(self, context):
        rb_draw_target(self, context).layout.label(text=T("Quick Rig - premade armatures"))

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        BF_PT_sb_quick_rig._draw_quick_rig(rb_draw_target(self, context), context)

    def _draw_quick_rig(self, context):
        layout = self.layout

        from boneforge.autorig.quick_human import (
            discover_rigify_metarigs,
            FALLBACK_OP_ID,
        )
        from boneforge.core.helpers import draw_helper, options_fold

        scene = context.scene

        col = layout.column(align=True)

        # Guard: scene may be None in headless/background render contexts.
        if scene is None:
            col.label(text="No active scene.", icon='ERROR')
            return

        active = context.active_object
        if (active is not None and active.type == 'ARMATURE'
                and "bonecraft_dropped_rig" in active):
            box = layout.box()
            box.label(text=T("Dropped rig: fit it to a mesh"))
            box.prop(scene, "boneforge_drop_target_mesh", text=T("Mesh"))   # which mesh: needed first
            box.operator("boneforge.fit_dropped_rig",
                         text=T("Fit Dropped Rig"), icon='MOD_SHRINKWRAP')

        # Safe accessors — fall back to sane defaults if scene props are not
        # yet registered (e.g. autorig module still loading on first draw).
        def _sp(name, default):
            v = getattr(scene, name, None)
            return v if v is not None else default

        rigify_rigs = discover_rigify_metarigs()

        groups = {"humans": [], "quadrupeds": [], "other": [], "unknown": []}
        for rig_descriptor in rigify_rigs:
            groups[rig_descriptor["group"]].append(rig_descriptor)

        if rigify_rigs:
            col.label(text=f"Rigify metarigs ({len(rigify_rigs)}):")
            for group_key, group_label in (
                ("humans", "Humans"),
                ("quadrupeds", "Quadrupeds"),
                ("other", "Other"),
                ("unknown", "Other"),
            ):
                try:
                    self._draw_group(col, groups[group_key], group_label, scene)
                except Exception as exc:
                    logger.exception(
                        "[BoneCraft] Quick Rig %s group draw failed",
                        group_key,
                    )
                    col.label(
                        text=f"[{group_label} group failed: {exc}]",
                        icon='ERROR',
                    )
        else:
            enable_box = col.box()
            enable_row = enable_box.row()
            enable_row.scale_y = 1.5
            enable_row.operator(
                "boneforge.enable_rigify",
                text=T("Enable Rigify"),
                icon='PLUGIN',
            )
            enable_box.label(
                text=T("Rigify must be enabled to select Rigify default rigs."),
                icon='INFO',
            )

        col.separator(factor=0.5)
        col.label(text=T("No Rigify required:"))
        op = col.operator(
            "boneforge.add_quick_rig",
            text=T("BoneCraft Basic Humanoid (19 bones)"),
            icon='OUTLINER_OB_ARMATURE',
        )
        op.rig_op_id = FALLBACK_OP_ID
        op.rig_label = "BoneCraft Humanoid"
        # act first, tune later: fit, weights, controllers and pose are the operator's own options,
        # remembered from the last rig and adjusted after the click (owner's UI critique, 2026-10-10)
        draw_helper(layout, context, T("Fit, weights, controllers and pose: adjust them after adding, "
                                       "in the Adjust Last Operation panel."))

        from boneforge.autorig.quick_human import _is_rigify_metarig
        more = options_fold(layout, "bc_quick_rig_more", text="Troubleshooting")
        if more is None:
            pass
        elif _is_rigify_metarig(context.active_object):
            col.separator()
            row = more.row(align=True)
            row.scale_y = 1.2
            row.operator(
                "boneforge.generate_rigify_control_rig",
                text=T("Generate Control Rig (active metarig)"),
                icon='CON_KINEMATIC',
            )
        elif (
            context.active_object is not None
            and context.active_object.type == "ARMATURE"
        ):
            more.operator(
                "boneforge.inspect_rigify_controls",
                text=T("Inspect Active Rig Controls"),
                icon='VIEWZOOM',
            )

        col.label(
            text=T("Need precise marker placement? Use the Auto-Rig Wizard above."),
            icon='INFO',
        )

        col.separator()
        col.label(text=T("Switch active rig's rest pose:"))
        pose_row = col.row(align=True)
        pose_row.scale_y = 1.2
        active_is_armature = (
            context.active_object is not None
            and context.active_object.type == "ARMATURE"
        )
        pose_row.enabled = active_is_armature
        t_pose_op = pose_row.operator(
            "boneforge.set_rest_pose",
            text=T("T-Pose"),
            icon='ARMATURE_DATA',
        )
        t_pose_op.pose_type = "T_POSE"
        a_pose_op = pose_row.operator(
            "boneforge.set_rest_pose",
            text=T("A-Pose"),
            icon='ARMATURE_DATA',
        )
        a_pose_op.pose_type = "A_POSE"
        if not active_is_armature:
            col.label(
                text=T("Select an armature to enable T-Pose / A-Pose."),
                icon='INFO',
            )

        if more is not None:
            more.operator(
                "boneforge.diagnose_quick_rig",
                text=T("Diagnose Quick Rig (print to console)"),
                icon='CONSOLE',
            )

    def _draw_group(self, col, rigs, group_label, scene):
        """Render two-buttons-per-row grid for a metarig group."""
        if not rigs:
            return
        col.label(text=group_label, icon='BLANK1')
        rig_index = 0
        while rig_index < len(rigs):
            row = col.row(align=True)
            for column_index in range(2):
                descriptor_index = rig_index + column_index
                if descriptor_index >= len(rigs):
                    row.label(text="")
                    continue
                rig_descriptor = rigs[descriptor_index]
                try:
                    op = row.operator(
                        "boneforge.add_quick_rig",
                        text=rig_descriptor["label"],
                        icon='OUTLINER_OB_ARMATURE',
                    )
                    op.rig_op_id = rig_descriptor["op_id"]
                    op.rig_label = rig_descriptor["label"]
                except Exception as exc:
                    logger.exception(
                        "[BoneCraft] Quick Rig button render failed: %s",
                        rig_descriptor,
                    )
                    row.label(
                        text=f"[{rig_descriptor.get('rig_name', '?')} "
                             f"failed: {exc}]",
                        icon='ERROR',
                    )
            rig_index += 2


class BF_PT_sb_wizard(Panel):
    """Auto-Rig Wizard — Rig Builder tab."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_wizard"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _RB_CAT
    bl_parent_id   = "BF_PT_rb_setup"
    bl_order       = 1                     # first in Rig Builder (owner, 2026-10-10)

    def draw_header(self, context):
        rb_draw_target(self, context).layout.label(text=T("Auto-Rig Wizard"))

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        _delegate_draw(self, context,
                       "boneforge.autorig.wizard",
                       "BF_PT_WizardPanel",
                       target=rb_draw_target(self, context))


class BF_PT_rb_mannequin(Panel):
    """Mannequin generation — Rig Builder tab."""
    bl_label       = " "
    bl_idname      = "BF_PT_rb_mannequin"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _RB_CAT
    bl_parent_id   = "BF_PT_rb_setup"
    bl_order       = 3

    def draw_header(self, context):
        self.layout.label(text=T("Mannequin"))

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        _delegate_draw(self, context,
                       "boneforge.autorig.mannequin",
                       "BF_PT_MannequinPanel",
                       target=rb_draw_target(self, context))


class BF_PT_sb_retarget(Panel):
    """Retarget panel — autorig. Child of Setup Rigging."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_retarget"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_setup"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Retarget"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        return True

    def draw(self, context):
        if not (_active_is(context, 'ARMATURE')):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Retarget needs an armature selected.', ('ARMATURE',))
            return
        _draw_explainer(
            self.layout, context,
            "Remaps animation data from one armature to another.",
            "Use when applying animations built for a different skeleton.",
        )
        _delegate_draw(self, context,
                       "boneforge.autorig.retarget",
                       "BF_PT_RetargetPanel")


class BF_PT_sb_rigify(Panel):
    """Rigify enhancement — animation. Child of Setup Rigging."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_rigify"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_setup"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Rigify Tools"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        return True

    def draw(self, context):
        if not (_active_is(context, 'ARMATURE')):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Rigify Tools needs an armature selected.', ('ARMATURE',))
            return
        _draw_explainer(
            self.layout, context,
            "Enhance and manage Rigify-generated control rigs.",
            "Use after generating a Rigify rig to access BoneCraft enhancements.",
        )
        _delegate_draw(self, context,
                       "boneforge.animation.rigify_enhance",
                       "BF_PT_RigifyEnhancePanel")


# =============================================================
# HUB: Skin  (order=20)
# =============================================================

class BF_PT_sb_skin(Panel):
    """BoneCraft -> Skin hub: weights and corrective shapes."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_skin"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_order       = 20

    def draw_header(self, context):
        self.layout.label(text=T("Skin"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        try:
            if not context.preferences.addons["boneforge"].preferences.show_tab_boneforge:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        if not (_active_is(context, 'ARMATURE', 'MESH')):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Skin needs an armature or a mesh selected.', ('ARMATURE', 'MESH'))
            return
        obj = context.active_object
        layout = self.layout
        layout.label(
            text=obj.name if obj else "No object selected",
            icon='MOD_VERTEX_WEIGHT',
        )
        _draw_explainer(
            layout, context,
            T("Paint weights and fix mesh deformation."),
            T("Expand a section below to get started."),
        )


class BF_PT_sb_weights(Panel):
    """Weight tools — weights. Child of Skin."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_weights"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_skin"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Weight Tools"))

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type in {'ARMATURE', 'MESH'}

    def draw(self, context):
        layout = self.layout
        _draw_explainer(
            layout, context,
            "Paint and adjust vertex weights that control mesh deformation.",
            "Use when the mesh pinches, collapses, or moves wrong during posing.",
        )
        from boneforge.weights.weight_tools import draw_automatic_weight_recalculation
        draw_automatic_weight_recalculation(layout, context)
        for module_path, class_name in (
            ("boneforge.weights.weight_tools",    "BONEFORGE_PT_p2b_flood_fill"),
            ("boneforge.weights.weight_transfer", "BONEFORGE_PT_p2b_weight_transfer"),
            ("boneforge.weights.weight_mirror",   "BONEFORGE_PT_p2b_weight_mirror"),
            ("boneforge.weights.weight_table",    "BONEFORGE_PT_p2b_weight_table"),
            ("boneforge.weights.deform_control",  "BONEFORGE_PT_p2b_deform_control"),
        ):
            layout.separator(factor=0.3)
            _delegate_draw(self, context, module_path, class_name)


class BF_PT_sb_correctives(Panel):
    """Corrective shape keys — animation. Child of Skin."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_correctives"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_skin"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Correctives"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        return True

    def draw(self, context):
        if not (_active_is(context, 'ARMATURE')):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Correctives needs an armature selected.', ('ARMATURE',))
            return
        _draw_explainer(
            self.layout, context,
            "Add corrective shape keys that fix deformation at specific poses.",
            "Use after weight painting to clean up stubborn problem areas at joints.",
        )
        _delegate_draw(self, context,
                       "boneforge.animation.correctives",
                       "BF_PT_CorrectivesPanel")


# =============================================================
# HUB: VRChat  (order=35)
# Avatar setup groups communicated through panel naming and explainer text:
#   A — VRChat Setup (panels ordered 1-2)
#   B — Body & Physics (panels ordered 4-6)
# =============================================================

def _cats_armature(context):
    """The armature the CATS-tab tools work on: the CATS Armature picker's, else the active armature."""
    from boneforge.core.armature import active_armature
    return active_armature(context)


def _cats_object_ready(context):
    """True when the CATS tab's avatar sections have something to work on: an armature from the picker or
    the selection, or an active mesh. A selected empty (a pivot marker, a camera) no longer hides them."""
    obj = context.active_object
    return _cats_armature(context) is not None or (obj is not None and obj.type == 'MESH')


class BF_PT_sb_vrchat(Panel):
    """BoneCraft -> VRChat hub: avatar assembly and publishing."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_vrchat"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CATS_CAT
    bl_order       = 35

    def draw_header(self, context):
        self.layout.label(text=T("Avatar Tools"))

    @classmethod
    def poll(cls, context):
        try:
            prefs = context.preferences.addons["boneforge"].preferences
            if not prefs.show_tab_cats:
                return False
        except Exception:
            pass
        return True                                   # show, don't hide: draw() says what to select

    def draw(self, context):
        layout = self.layout
        if not _cats_object_ready(context):
            from boneforge.core import needs
            needs.draw(layout, context, "Avatar Tools needs an armature or a mesh selected.", ("ARMATURE", "MESH"))
            return
        arm = _cats_armature(context)
        obj = arm if arm is not None else context.active_object
        from boneforge.core.helpers import draw_wrapped, _BOX
        draw_wrapped(layout, context, obj.name if obj else "No object", icon='COMMUNITY')

        # Compact Mode: a shortcut to the Show Helpers preference.
        from boneforge.core.helpers import draw_compact_toggle
        draw_compact_toggle(layout, context)

        # Cluster overview — always visible regardless of compact mode.
        layout.separator(factor=0.3)
        col = layout.column(align=True)
        col.scale_y = 0.8
        # wrapped to the sidebar's width, on either side of the viewport
        for text, icon in (("A — VRChat setup: humanoid bones.", 'STRIP_COLOR_01'),
                           ("B — Body & Physics: hair, visemes.", 'STRIP_COLOR_04'),
                           ("Performance, clothing, facial tools and naming: VRChat Tools, below.", 'TOOL_SETTINGS')):
            draw_wrapped(col, context, T(text), icon=icon)

        layout.separator(factor=0.3)
        cats_hint = layout.box()
        cats_hint.scale_y = 0.85
        # one sentence kept as two strings: joined, so it wraps as one paragraph
        draw_wrapped(cats_hint, context, T("Cats users: Fix Model / Join Meshes / Cleanup /") + " "
                     + T("Translate live in the main CATS tool stack."), icon='INFO', inset=_BOX)


# ── Cluster A — VRChat Setup ───────────────────────────────────

class BF_PT_sb_vrc_humanoid(Panel):
    """Humanoid bone mapping, validator, and eye bone setup."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_vrc_humanoid"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CATS_CAT
    bl_parent_id   = "BF_PT_sb_vrchat"
    bl_order       = 2
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Set Up Humanoid Bones"))

    @classmethod
    def poll(cls, context):
        return _cats_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        _draw_explainer(
            layout, context,
            "Maps your bones to VRChat's humanoid avatar definition.",
            "Required for IK, locomotion, and full-body tracking to work.",
        )
        for module_path, class_name in (
            ("boneforge.vrchat.humanoid.mapper",    "BONEFORGE_PT_vrc_humanoid"),
            ("boneforge.vrchat.humanoid.validator", "BONEFORGE_PT_vrc_humanoid_validator"),
            ("boneforge.vrchat.humanoid.eye_setup", "BONEFORGE_PT_vrc_eye_setup"),
        ):
            layout.separator(factor=0.3)
            _delegate_draw(self, context, module_path, class_name)


# ── Cluster B — Body & Physics ─────────────────────────────────

class BF_PT_sb_vrc_hair(Panel):
    """Hair physics: chain detection, generation, PhysBone, colliders."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_vrc_hair"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CATS_CAT
    bl_parent_id   = "BF_PT_sb_vrchat"
    bl_order       = 4
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Add Hair Physics"))

    @classmethod
    def poll(cls, context):
        return _cats_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        _draw_explainer(
            layout, context,
            "Sets up PhysBone chains on hair, ears, tails, or accessories.",
            "Run after Set Up Humanoid Bones. Skip if avatar has no dynamic parts.",
        )
        for module_path, class_name in (
            ("boneforge.vrchat.hair.detector",  "BONEFORGE_PT_vrc_hair_detect"),
            ("boneforge.vrchat.hair.generator", "BONEFORGE_PT_vrc_hair_generator"),
            ("boneforge.vrchat.hair.physbone",  "BONEFORGE_PT_vrc_physbone"),
            ("boneforge.vrchat.hair.collision", "BONEFORGE_PT_vrc_colliders"),
        ):
            layout.separator(factor=0.3)
            _delegate_draw(self, context, module_path, class_name)


# ── VRChat Tools — the embedded VRChat utilities in one section ──────

VRC_TOOL_GROUPS = (
    # (group heading, ((module, hidden panel class), ...)) in the owner's order (2026-10-10)
    ("Performance", (
        ("boneforge.vrchat.performance.rank",       "BONEFORGE_PT_vrc_performance"),
        ("boneforge.vrchat.performance.decimation", "BONEFORGE_PT_vrc_decimation"),
        ("boneforge.vrchat.performance.optimizer",  "BONEFORGE_PT_vrc_optimizer"),
    )),
    ("Clothing", (
        ("boneforge.vrchat.clothing.bone_match", "BONEFORGE_PT_vrc_bone_match"),
        ("boneforge.vrchat.clothing.collision",  "BONEFORGE_PT_vrc_collision"),
        ("boneforge.vrchat.clothing.merge",      "BONEFORGE_PT_vrc_clothing_merge"),
    )),
    ("Facial", (
        ("boneforge.vrchat.visemes.vrchat_mapper", "BONEFORGE_PT_vrc_viseme_mapper"),
        ("boneforge.vrchat.visemes.face_tracking", "BONEFORGE_PT_vrc_face_tracking"),
    )),
    ("Naming", (
        ("boneforge.vrchat.naming.detector",     "BONEFORGE_PT_vrc_naming_detect"),
        ("boneforge.vrchat.naming.presets",      "BONEFORGE_PT_vrc_naming_presets"),
        ("boneforge.vrchat.naming.batch_rename", "BONEFORGE_PT_vrc_batch_rename"),
    )),
)
_VRC_ARMATURE_ONLY = {"Clothing", "Facial", "Naming"}


def _vrc_tool_on(class_name):
    """True while the tool's hidden panel is registered (a VRChat tool package switched off unregisters it)."""
    cls = getattr(bpy.types, class_name, None)
    return cls is not None and getattr(cls, "is_registered", False)


class BF_PT_cats_vrc_tools(Panel):
    """CATS -> VRChat Tools: performance, clothing, facial and naming utilities."""
    bl_label       = " "
    bl_idname      = "BF_PT_cats_vrc_tools"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CATS_CAT
    bl_order       = 36                                  # right after the VRChat section (35)
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("VRChat Tools"))

    @classmethod
    def poll(cls, context):
        try:
            if not context.preferences.addons["boneforge"].preferences.show_tab_cats:
                return False
        except Exception:
            pass
        return any(_vrc_tool_on(c) for _heading, tools in VRC_TOOL_GROUPS for _m, c in tools)

    def draw(self, context):
        layout = self.layout
        if not _cats_object_ready(context):               # show, don't hide: say what to select
            from boneforge.core import needs
            needs.draw(layout, context, "VRChat Tools needs an armature or a mesh selected.", ("ARMATURE", "MESH"))
            return
        is_armature = _cats_armature(context) is not None
        for heading, tools in VRC_TOOL_GROUPS:
            tools = [(m, c) for m, c in tools if _vrc_tool_on(c)]
            if not tools:
                continue
            layout.separator(factor=0.5)
            layout.label(text=T(heading))
            if heading in _VRC_ARMATURE_ONLY and not is_armature:
                layout.label(text=T("Select the armature to use these tools."), icon='INFO')
                continue
            for module_path, class_name in tools:
                layout.separator(factor=0.3)
                if heading == "Facial":
                    title = ("VRChat Viseme Mapping" if class_name == "BONEFORGE_PT_vrc_viseme_mapper"
                             else "Face Tracking")
                    layout.label(text=T(title))
                _delegate_draw(self, context, module_path, class_name)


# =============================================================
# HUB: Review  (order=40)
# Formerly "Animate". Renamed to "Review" — contains animation
# organisation tools AND inspect/diagnostic tools. bl_idname
# kept as BF_PT_sb_animate so all child panels keep their links.
# =============================================================

class BF_PT_sb_animate(Panel):
    """BoneCraft -> Review hub: animate, inspect, validate.

    Merges the former Animate and Inspect tabs. bl_idname preserved
    as BF_PT_sb_animate so Collections, Pose Library, Graph Tools,
    and Bone Inspector (registered by bone_inspector.py) keep their
    bl_parent_id links without modification.
    """
    bl_label       = " "
    bl_idname      = "BF_PT_sb_animate"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_order       = 40

    def draw_header(self, context):
        self.layout.label(text=T("Review"))

    @classmethod
    def poll(cls, context):
        # Show, don't hide: when the requirement fails, draw() says what to select.
        try:
            if not context.preferences.addons["boneforge"].preferences.show_tab_boneforge:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        if not (_active_is(context, 'ARMATURE')):
            from boneforge.core import needs
            needs.draw(self.layout, context, 'Review needs an armature selected.', ('ARMATURE',))
            return
        self.layout.label(
            text=context.active_object.name,
            icon='ACTION',
        )


class BF_PT_sb_collections(Panel):
    """Bone collection manager — ui_panels. Child of Review."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_collections"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_animate"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Collections"))

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
        )

    def draw(self, context):
        _draw_explainer(
            self.layout, context,
            "Manage and toggle bone collection visibility on your armature.",
            "Organize control, deform, and helper bone groups.",
        )
        _delegate_draw(self, context,
                       "boneforge.ui_panels.collection_ui",
                       "BF_PT_CollectionPanel")


class BF_PT_sb_pose_lib(Panel):
    """Pose library — animation. Child of Review."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_pose_lib"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_animate"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Pose Library"))

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
        )

    def draw(self, context):
        _draw_explainer(
            self.layout, context,
            "Save and apply named poses to your rig.",
            "Use for storing expressions, rest poses, or animation reference frames.",
        )
        _delegate_draw(self, context,
                       "boneforge.animation.pose_library",
                       "BF_PT_PoseLibraryPanel")


class BF_PT_sb_graph(Panel):
    """Graph & Animation tools — animation. Child of Review."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_graph"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_animate"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Graph Tools"))

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
        )

    def draw(self, context):
        _draw_explainer(
            self.layout, context,
            "Clean F-curves, smooth keyframes, and manage animation curve data.",
            "Companion tools for working in the Graph Editor.",
        )
        _delegate_draw(self, context,
                       "boneforge.animation.graph_tools",
                       "BF_PT_GraphToolsPanel")


class BF_PT_sb_rig_validator(Panel):
    """Rig validation checks — advanced_rigging. Child of Review."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_rig_validator"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_animate"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Rig Validator"))

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
        )

    def draw(self, context):
        _draw_explainer(
            self.layout, context,
            "Checks for common rig errors — missing bones, broken constraints, naming issues.",
            "Run when something behaves unexpectedly or before handing off the rig.",
        )
        _delegate_draw(self, context,
                       "boneforge.advanced_rigging.rig_validator",
                       "BONEFORGE_PT_p2c_rig_validator")


class BF_PT_sb_rig_readme(Panel):
    """Rig Readme — per-armature documentation — advanced_rigging. Child of Review."""
    bl_label       = " "
    bl_idname      = "BF_PT_sb_rig_readme"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_animate"
    bl_options     = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Rig Readme"))

    @classmethod
    def poll(cls, context):
        return (
            context.active_object is not None
            and context.active_object.type == 'ARMATURE'
        )

    def draw(self, context):
        _draw_explainer(
            self.layout, context,
            "View or edit the embedded README for this rig.",
            "Documents bone conventions, known quirks, and usage notes.",
        )
        _delegate_draw(self, context,
                       "boneforge.advanced_rigging.rig_notes",
                       "BONEFORGE_PT_p2c_rig_readme")


class BF_PT_sb_bone_counsel(Panel):
    """Bone Role Counsel — Confession Layer (H6 + A1).

    Shows one plain-language sentence about the selected bone's
    jurisdiction (controller, DEF, MCH/ORG, unknown) so animators
    always know whether they are touching the right bone.

    When no bone is selected shows an armature summary (idle frame)
    so the panel is never blank.
    """
    bl_label       = "Bone Role"
    bl_idname      = "BF_PT_sb_bone_counsel"
    bl_space_type  = _SPACE
    bl_region_type = _REGION
    bl_category    = _CAT
    bl_parent_id   = "BF_PT_sb_animate"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is None or obj.type != "ARMATURE":
            return False
        try:
            from boneforge.autorig.quick_human import _is_generated_rigify_control_rig
            return _is_generated_rigify_control_rig(obj)
        except ImportError:
            return False

    def draw(self, context):
        _draw_confession_layer(self.layout, context)


# =============================================================
# Registration
# NOTE: every parent panel MUST precede its children.
# BONEFORGE_PT_taskboard* registered by panel.py
# BONEFORGE_PT_bone_inspector registered by bone_inspector.py
# =============================================================

_CLASSES = (
    # Project strip + children
    BF_PT_sb_overview,
    BF_PT_sb_rig_notes,
    # Setup Rigging hub — parent before children
    BF_PT_sb_setup,
    BF_PT_sb_retarget,
    BF_PT_sb_rigify,
    # Skin hub — parent before children
    BF_PT_sb_skin,
    BF_PT_sb_weights,
    BF_PT_sb_correctives,
    # Avatar Tools hub — parent before children (setup, then body/physics)
    BF_PT_sb_vrchat,
    BF_PT_sb_vrc_humanoid,   # A-2
    BF_PT_sb_vrc_hair,       # B-4
    BF_PT_cats_vrc_tools,    # CATS section, order 36
    # Review hub — parent before children (animate + inspect merged)
    BF_PT_sb_animate,
    BF_PT_sb_collections,
    BF_PT_sb_pose_lib,
    BF_PT_sb_graph,
    BF_PT_sb_rig_validator,
    BF_PT_sb_rig_readme,
    BF_PT_sb_bone_counsel,  # Confession Layer — bone role guidance (v8.2.1)
)

# Rig Builder panels register separately, in Properties > Scene tab only
# (rb_placement.SCENE_PLACEMENT); the Scene tab exists whatever is selected.
RB_CLASSES = (
    BF_PT_rb_setup,        # parent before children
    BF_PT_sb_quick_rig,
    BF_PT_sb_wizard,
    BF_PT_rb_mannequin,
)


_SHELF_SUFFIX = "_Shelf"


def _shelf_tab_poll(cls, context):
    """The Rig Builder viewport tab follows its Preferences show switch."""
    try:
        prefs = context.preferences.addons["boneforge"].preferences
        if not prefs.show_tab_rig_builder:
            return False
    except Exception:
        pass
    return True


def _helper_methods(orig):
    """The original panel's own methods (e.g. Quick Rig's _draw_group) for a copy."""
    return {name: value for name, value in vars(orig).items()
            if not name.startswith("__") and not name.startswith("bl_")
            and (callable(value) or isinstance(value, (staticmethod, classmethod)))}


def _register_rig_builder_shelf():
    """Copies of the Scene-tab Rig Builder panels in the 3D viewport, on the side Preferences name."""
    from boneforge import tab_sides
    region = tab_sides.region_for(tab_sides.side_of("rig_builder"))
    for orig in RB_CLASSES:
        attrs = dict(_helper_methods(orig))
        attrs.update({
            "bl_idname": orig.bl_idname + _SHELF_SUFFIX,
            "bl_label": getattr(orig, "bl_label", " "),
            "bl_space_type": "VIEW_3D",
            "bl_region_type": region,
            "bl_category": rb_placement.RB_CATEGORY,
            "bl_options": set(getattr(orig, "bl_options", set())),
            "bl_order": getattr(orig, "bl_order", 0),    # the Auto-Rig Wizard first, as in the Scene tab
            "draw": orig.draw,
            "draw_header": orig.draw_header,
        })
        if orig is BF_PT_rb_setup:
            attrs["poll"] = classmethod(_shelf_tab_poll)
        else:
            attrs["bl_parent_id"] = orig.bl_parent_id + _SHELF_SUFFIX
            attrs["poll"] = classmethod(orig.poll.__func__)
        bpy.utils.register_class(type(orig.__name__ + _SHELF_SUFFIX, (Panel,), attrs))


def register_rig_builder():
    for cls in RB_CLASSES:
        for key, value in rb_placement.SCENE_PLACEMENT.items():
            setattr(cls, key, value)
        if not cls.is_registered:
            bpy.utils.register_class(cls)
    _register_rig_builder_shelf()


def unregister_rig_builder():
    # Look the live panel up by id: after an add-on reload the class objects
    # in this module can be stale copies of the ones Blender holds.
    for cls in reversed(RB_CLASSES):
        live = getattr(bpy.types, cls.bl_idname + _SHELF_SUFFIX, None)
        if live is not None:
            bpy.utils.unregister_class(live)
    for cls in reversed(RB_CLASSES):
        live = getattr(bpy.types, cls.bl_idname, None)
        if live is not None:
            bpy.utils.unregister_class(live)


def register():
    from boneforge.core import needs                  # the Select button of every 'needs X' note
    for cls in needs.classes:
        bpy.utils.register_class(cls)
    for cls in _CLASSES:
        bpy.utils.register_class(cls)
    register_rig_builder()


def unregister():
    unregister_rig_builder()
    for cls in reversed(_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    from boneforge.core import needs
    for cls in reversed(needs.classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
