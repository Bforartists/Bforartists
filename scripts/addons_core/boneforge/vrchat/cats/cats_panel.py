"""BoneCraft VRChat CATS — Main N-Panel Tab (VIEW_3D sidebar).

The hub panel for all CATS-equivalent avatar tools. Uses bl_category="CATS"
so BoneCraft occupies the established CATS tab that VRChat avatar creators
already know. Each sub-panel draws a focused set of operators inline.

All panels follow the project pattern:
    bl_label = " "  (single space)
    draw_header(self, context) sets the visible header text.
"""

import bpy
from bpy.types import Panel

from boneforge.core import active_armature
from boneforge.i18n import T
from boneforge.vrchat.cats import pipeline


# ── Shared tab / space config ───────────────────────────────────────────────

_SPACE = 'VIEW_3D'
_REGION = 'UI'
_CATEGORY = "CATS"  # Proper noun — never wrapped in T()
_CATS_ARMATURE_ENUM_ITEMS = []


def _is_scene_armature(scene, obj) -> bool:
    return obj is not None and obj.type == 'ARMATURE' and scene.objects.get(obj.name) == obj


def _scene_armatures(scene) -> list:
    return sorted(
        (obj for obj in scene.objects if obj.type == 'ARMATURE'),
        key=lambda obj: obj.name.lower(),
    )


def _cats_armature_items(scene, context):
    global _CATS_ARMATURE_ENUM_ITEMS
    armatures = _scene_armatures(scene)
    if not armatures:
        _CATS_ARMATURE_ENUM_ITEMS = [
            ('__NONE__', T("No armatures found"), T("No armatures in scene"), 'ERROR', 0),
        ]
        return _CATS_ARMATURE_ENUM_ITEMS

    _CATS_ARMATURE_ENUM_ITEMS = [
        (obj.name, obj.name, obj.name, 'OUTLINER_OB_ARMATURE', index)
        for index, obj in enumerate(armatures)
    ]
    return _CATS_ARMATURE_ENUM_ITEMS


def _cats_armature_by_name(scene, name):
    if not name or name == '__NONE__':
        return None

    obj = scene.objects.get(name)
    if _is_scene_armature(scene, obj):
        return obj
    return None


def _cats_target_armature_update(scene, context):
    arm = _cats_armature_by_name(
        scene,
        getattr(scene, "boneforge_cats_target_armature_name", ""),
    )
    if arm is None:
        return

    try:
        for obj in context.selected_objects:
            if obj != arm and obj.type == 'ARMATURE':
                obj.select_set(False)
        arm.select_set(True)
        context.view_layer.objects.active = arm
    except Exception:
        pass


def _cats_target_armature(context):
    scene = context.scene
    arm = _cats_armature_by_name(
        scene,
        getattr(scene, "boneforge_cats_target_armature_name", ""),
    )
    if arm is not None:
        return arm

    active = context.active_object
    if _is_scene_armature(scene, active):
        scene.boneforge_cats_target_armature_name = active.name
        return active

    armatures = _scene_armatures(scene)
    if armatures:
        scene.boneforge_cats_target_armature_name = armatures[0].name
        return armatures[0]

    return None


# ── Status icon helpers ─────────────────────────────────────────────────────

def _phase_icon(status) -> str:
    if status == pipeline.OUTCOME_CHANGED:
        return 'CHECKMARK'
    if status == pipeline.OUTCOME_CLEAN:
        return 'RADIOBUT_OFF'
    if status == pipeline.OUTCOME_FAILED:
        return 'CANCEL'
    return 'DOT'


# ── Main panel ──────────────────────────────────────────────────────────────

class CATS_PT_main(Panel):
    """CATS hub panel — shows active armature name and hosts sub-panels."""

    bl_label = " "
    bl_idname = "CATS_PT_main"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text="CATS")

    @classmethod
    def poll(cls, context):
        # The CATS sidebar tab follows the Preferences "CATS" switch; sub-panels
        # gate per armature. The Properties > Scene tab copy is always shown.
        try:
            prefs = context.preferences.addons["boneforge"].preferences
            if not prefs.show_tab_cats:
                return False
        except Exception:
            pass
        return True

    def draw(self, context):
        pass


class CATS_PT_target_armature(Panel):
    """Scene armature target used by all CATS tools."""

    bl_label = " "
    bl_idname = "CATS_PT_target_armature"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_order = 0
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        arm = _cats_target_armature(context)
        # the label on its own line, so a narrow sidebar does not cut it to "Arma..."
        layout.label(text=T("Armature"))
        layout.prop(context.scene, "boneforge_cats_target_armature_name", text="")
        if arm is None:
            from boneforge.core.helpers import draw_wrapped
            draw_wrapped(layout, context, T("Select an armature to begin"), icon='INFO')


# ── Sub-panel: Pipeline Status ──────────────────────────────────────────────

class CATS_PT_pipeline_status(Panel):
    """Overview of per-phase pipeline completion status."""

    bl_label = " "
    bl_idname = "CATS_PT_pipeline_status"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Pipeline Status"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        grid = layout.grid_flow(
            row_major=True, columns=1, even_columns=True, even_rows=False, align=True,
        )
        for phase_id in pipeline.PIPELINE_PHASES:
            status = pipeline.get_phase_status(scene, phase_id)
            grid.row(align=True).label(
                text=phase_id.replace("_", " ").title(),
                icon=_phase_icon(status),
            )


# ── Sub-panel: Fix Model ────────────────────────────────────────────────────

class CATS_PT_fix_model(Panel):
    """Fix Model settings and operator."""

    bl_label = " "
    bl_idname = "CATS_PT_fix_model"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"

    def draw_header(self, context):
        self.layout.label(text=T("Fix Model"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "boneforge_vrc_fix_model_settings", None)
        if settings is not None:
            col = layout.column(align=True)
            col.prop(settings, "apply_modifiers", toggle=True)
            col.prop(settings, "remove_doubles", toggle=True)
            col.prop(settings, "recalculate_normals", toggle=True)
            col.prop(settings, "remove_loose", toggle=True)
            col.prop(settings, "remove_empty_groups", toggle=True)
            if hasattr(settings, "remove_zero_weight_bones"):
                col.prop(settings, "remove_zero_weight_bones", toggle=True)
            if hasattr(settings, "remove_constraints"):
                col.prop(settings, "remove_constraints", toggle=True)
            if hasattr(settings, "remove_rigidbodies"):
                col.prop(settings, "remove_rigidbodies", toggle=True)
            layout.separator(factor=0.5)
        layout.operator("boneforge.vrc_fix_model", text=T("Fix Model"), icon='MODIFIER')

# -- Sub-panel: Translate Bone Names

class CATS_PT_translate(Panel):
    """Bone-name translation and language-specific rename prep."""

    bl_label = " "
    bl_idname = "CATS_PT_translate"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Translate Bone Names"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        from boneforge.vrchat.cats import translate
        translate.BONEFORGE_PT_vrc_translate.draw(self, context)

# -- Sub-panel: Visemes

class CATS_PT_visemes(Panel):
    """Viseme generator and shape-key mapper operators."""

    bl_label = " "
    bl_idname = "CATS_PT_visemes"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Visemes"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "boneforge_cats_viseme_settings", None)
        if settings is not None:
            col = layout.column(align=True)
            col.prop(settings, "a_shape", text=T("A Shape"))
            col.prop(settings, "o_shape", text=T("O Shape"))
            col.prop(settings, "ch_shape", text=T("CH Shape"))
            layout.separator(factor=0.5)
            layout.operator(
                "boneforge.cats_auto_detect_shapes",
                text=T("Auto-Detect"),
                icon='VIEWZOOM',
            )
        layout.operator(
            "boneforge.cats_generate_visemes",
            text=T("Generate Visemes"),
            icon='SHAPEKEY_DATA',
        )
        if settings is not None:
            from boneforge.core.helpers import options_fold
            col = options_fold(layout, "bc_cats_visemes_options")
            if col is not None:
                col.prop(settings, "overwrite_existing")


# ── Sub-panel: Eye Tracking ─────────────────────────────────────────────────

class CATS_PT_eye_tracking(Panel):
    """Eye tracking bone and constraint setup."""

    bl_label = " "
    bl_idname = "CATS_PT_eye_tracking"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Eye Tracking"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        settings = getattr(context.scene, "boneforge_cats_eye_settings", None)
        if settings is not None:
            col = layout.column(align=True)
            col.prop(settings, "left_eye_bone", text=T("Left Eye"))
            col.prop(settings, "right_eye_bone", text=T("Right Eye"))
            layout.separator(factor=0.5)
            col = layout.column(align=True)
            col.prop(settings, "up_limit", text=T("Up Limit"))
            col.prop(settings, "down_limit", text=T("Down Limit"))
            col.prop(settings, "side_limit", text=T("Side Limit"))
            layout.separator(factor=0.5)
        layout.operator(
            "boneforge.cats_autodetect_eyes",
            text=T("Auto-Detect"),
            icon='VIEWZOOM',
        )
        layout.operator(
            "boneforge.cats_create_eye_tracking",
            text=T("Create Eye Tracking"),
            icon='HIDE_OFF',
        )


# ── Sub-panel: Pose & Shape Keys ────────────────────────────────────────────

class CATS_PT_pose_shape(Panel):
    """Pose-to-shape-key bake and shape-key-to-basis flatten."""

    bl_label = " "
    bl_idname = "CATS_PT_pose_shape"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Pose & Shape Keys"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator(
            "boneforge.cats_pose_to_shape",
            text=T("Pose to Shape Key"),
            icon='SHAPEKEY_DATA',
        )
        col.operator(
            "boneforge.cats_shape_key_to_basis",
            text=T("Shape Key to Basis"),
            icon='SHAPEKEY_DATA',
        )


# -- Sub-panel: Material Atlas

class CATS_PT_material_atlas(Panel):
    """Material atlas combiner, delegated to the shared atlas panel."""

    bl_label = " "
    bl_idname = "CATS_PT_material_atlas"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Material Atlas"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None or (
            context.active_object is not None and context.active_object.type == 'MESH'
        )

    def draw(self, context):
        from boneforge.vrchat.cats import material_atlas
        material_atlas.BONEFORGE_PT_vrc_w2_atlas.draw(self, context)

# -- Sub-panel: Mesh Tools

class CATS_PT_mesh_tools(Panel):
    """Mesh separation utilities."""

    bl_label = " "
    bl_idname = "CATS_PT_mesh_tools"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Mesh Tools"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.operator(
            "boneforge.cats_separate_by_materials",
            text=T("Separate by Materials"),
            icon='SEPARATE_BYMATERIAL',
        )
        col.operator(
            "boneforge.cats_separate_by_loose",
            text=T("Separate by Loose Parts"),
            icon='SEPARATE_LOOSE',
        )
        col.operator(
            "boneforge.cats_separate_by_shape_keys",
            text=T("Separate by Shape Keys"),
            icon='SHAPEKEY_DATA',
        )


# -- Sub-panel: Join Meshes

class CATS_PT_join_meshes(Panel):
    """Shape-key-safe mesh joining workflow."""

    bl_label = " "
    bl_idname = "CATS_PT_join_meshes"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Join Meshes"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        from boneforge.vrchat.cats import join_meshes
        join_meshes.BONEFORGE_PT_vrc_join_meshes.draw(self, context)

# -- Sub-panel: Transforms & FBT

class CATS_PT_transforms(Panel):
    """Apply transforms and Full Body Tracking bone adjustments."""

    bl_label = " "
    bl_idname = "CATS_PT_transforms"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Transforms & FBT"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "boneforge.cats_apply_all_transforms",
            text=T("Apply All Transforms"),
            icon='APPLYALL',
        )
        layout.separator(factor=0.5)
        col = layout.column(align=True)
        col.operator(
            "boneforge.cats_fix_fbt",
            text=T("Fix FBT"),
            icon='MODIFIER',
        )
        col.operator(
            "boneforge.cats_remove_fbt",
            text=T("Remove FBT"),
            icon='TRASH',
        )


# ── Sub-panel: Bone Tools ───────────────────────────────────────────────────

class CATS_PT_bone_tools(Panel):
    """Bone root creation, merge, and duplicate utilities."""

    bl_label = " "
    bl_idname = "CATS_PT_bone_tools"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Bone Tools"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        # act first, tune later: the root's name and the merge threshold are adjusted after the click
        layout.operator(
            "boneforge.cats_create_bone_root",
            text=T("Create Root Bone"),
            icon='ADD',
        )
        layout.separator(factor=0.5)
        layout.operator(
            "boneforge.cats_merge_bones",
            text=T("Merge Bones"),
            icon='AUTOMERGE_ON',
        )
        layout.separator(factor=0.5)
        layout.operator(
            "boneforge.cats_duplicate_bones",
            text=T("Duplicate Bones"),
            icon='DUPLICATE',
        )
        from boneforge.core.helpers import draw_helper
        draw_helper(layout, context, T("Root name and merge threshold: adjust them after the click, "
                                       "in the Adjust Last Operation panel."))


# ── Sub-panel: Armature Tools ───────────────────────────────────────────────

class CATS_PT_armature_tools(Panel):
    """Object-picker armature merge."""

    bl_label = " "
    bl_idname = "CATS_PT_armature_tools"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Armature Tools"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        from boneforge.vrchat.cats import armature_tools
        armature_tools.draw_merge_armatures_ui(self.layout, context)


# ── Sub-panel: Automatic Bone Weight Recalculation ─────────────────────────

class CATS_PT_automatic_bone_weight_recalculation(Panel):
    """Simple weight repair beside CATS bone and armature tools."""
    bl_label = " "
    bl_idname = "CATS_PT_automatic_bone_weight_recalculation"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Smart Automatic Weights"))

    @classmethod
    def poll(cls, context):
        return any(obj.type == 'ARMATURE' for obj in context.scene.objects)

    def draw(self, context):
        layout = self.layout
        if not hasattr(context.scene, "boneforge_weight_recalculation"):
            layout.label(text=T("Enable Weight & Deform Tools first"), icon='INFO')
            return
        action = layout.operator(
            "boneforge.automatic_bone_weight_recalculation",
            text=T("Smart Automatic Weights"), icon='MOD_VERTEX_WEIGHT')
        action.smart = True
        row = layout.row()
        expanded = context.scene.boneforge_cats_weight_advanced
        row.prop(context.scene, "boneforge_cats_weight_advanced",
                 text=T("Advanced Recalculation"),
                 icon='TRIA_DOWN' if expanded else 'TRIA_RIGHT', emboss=False)
        if expanded:
            layout.box().label(text="BoneForge > Skin > Weight Tools", icon='INFO')


# ── Sub-panel: Operation Ledger ─────────────────────────────────────────────

class CATS_PT_ledger(Panel):
    """Scrollable log of all CATS pipeline operations."""

    bl_label = " "
    bl_idname = "CATS_PT_ledger"
    bl_space_type = _SPACE
    bl_region_type = _REGION
    bl_category = _CATEGORY
    bl_parent_id = "CATS_PT_main"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        self.layout.label(text=T("Operation Ledger"))

    @classmethod
    def poll(cls, context):
        return active_armature(context) is not None

    def draw(self, context):
        layout = self.layout
        ledger = pipeline.get_ledger(context.scene)

        if not ledger:
            layout.label(text=T("No ledger entries"), icon='INFO')
        else:
            col = layout.column(align=True)
            for entry in ledger:
                status = entry.get("status", "")
                op_id = entry.get("op_id", "?")
                message = entry.get("message", "")
                t = entry.get("time", "")
                icon = (
                    'CHECKMARK' if status == pipeline.OUTCOME_CHANGED else
                    'RADIOBUT_OFF' if status == pipeline.OUTCOME_CLEAN else
                    'CANCEL' if status == pipeline.OUTCOME_FAILED else 'DOT'
                )
                col.row(align=True).label(
                    text=f"[{t}] {op_id} — {message}" if t else f"{op_id} — {message}",
                    icon=icon,
                )

        layout.separator(factor=0.5)
        row = layout.row(align=True)
        row.operator("boneforge.cats_clear_ledger", text=T("Clear"), icon='TRASH')
        row.operator("boneforge.cats_copy_ledger", text=T("Copy"), icon='COPYDOWN')


# ── Registration ────────────────────────────────────────────────────────────

classes = (
    CATS_PT_main,
    CATS_PT_target_armature,
    CATS_PT_pipeline_status,
    CATS_PT_fix_model,
    CATS_PT_translate,
    CATS_PT_visemes,
    CATS_PT_eye_tracking,
    CATS_PT_pose_shape,
    CATS_PT_material_atlas,
    CATS_PT_mesh_tools,
    CATS_PT_join_meshes,
    CATS_PT_transforms,
    CATS_PT_bone_tools,
    CATS_PT_armature_tools,
    CATS_PT_automatic_bone_weight_recalculation,
    CATS_PT_ledger,
)


def register():
    if hasattr(bpy.types.Scene, "boneforge_cats_target_armature"):
        del bpy.types.Scene.boneforge_cats_target_armature
    if hasattr(bpy.types.Scene, "boneforge_cats_target_armature_name"):
        del bpy.types.Scene.boneforge_cats_target_armature_name

    bpy.types.Scene.boneforge_cats_target_armature_name = bpy.props.EnumProperty(
        name="Armature",
        description="Armature used by CATS tools",
        items=_cats_armature_items,
        update=_cats_target_armature_update,
    )
    bpy.types.Scene.boneforge_cats_weight_advanced = bpy.props.BoolProperty(
        name="Advanced Recalculation", default=False)
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if hasattr(bpy.types.Scene, "boneforge_cats_weight_advanced"):
        del bpy.types.Scene.boneforge_cats_weight_advanced
    if hasattr(bpy.types.Scene, "boneforge_cats_target_armature_name"):
        del bpy.types.Scene.boneforge_cats_target_armature_name
    if hasattr(bpy.types.Scene, "boneforge_cats_target_armature"):
        del bpy.types.Scene.boneforge_cats_target_armature
