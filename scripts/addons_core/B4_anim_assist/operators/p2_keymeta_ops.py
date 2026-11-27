"""Per-keyframe metadata operators (7 ops)."""

from __future__ import annotations

from bpy.props import BoolProperty, StringProperty
from bpy.types import Operator

from ..core import key_metadata as meta
from ..core.context_utils import in_anim_editor, iter_selected_keys, key_identity
from ..core.logging import get_logger

_log = get_logger(__name__)


class _AnimEditorOp(Operator):
    @classmethod
    def poll(cls, context):
        return in_anim_editor(context)


class ANIMASSIST_OT_tag_selected_keys(_AnimEditorOp):
    bl_idname = "animassist.tag_selected_keys"
    bl_label = "Tag Selected Keys"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Stamp a string tag onto every selected key's metadata record"
    bl_options = {"REGISTER", "UNDO"}

    tag: StringProperty(  # type: ignore[valid-type]
        name="Tag",
        description="String written into the tag field of every selected key's metadata",
        default="",
    )

    def execute(self, context):
        if not self.tag:
            self.report({"WARNING"}, "Empty tag")
            return {"CANCELLED"}
        scene = context.scene
        n = 0
        for obj, _a, fc, _i, kp in iter_selected_keys(context):
            meta.upsert_meta(scene, key_identity(obj.name, fc, kp.co.x), tag=self.tag)
            n += 1
        self.report({"INFO"}, f"Tagged {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_clear_tag_selected(_AnimEditorOp):
    bl_idname = "animassist.clear_tag_selected_keys"
    bl_label = "Clear Tags on Selected Keys"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Erase the tag field on every selected key's metadata record"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        n = 0
        for obj, _a, fc, _i, kp in iter_selected_keys(context):
            ident = key_identity(obj.name, fc, kp.co.x)
            item = meta.get_meta(scene, ident)
            if item:
                item.tag = ""
                n += 1
        self.report({"INFO"}, f"Cleared {n} tags")
        return {"FINISHED"}


class ANIMASSIST_OT_set_key_note(_AnimEditorOp):
    bl_idname = "animassist.set_key_note"
    bl_label = "Set Note on Selected Keys"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Attach a free-form note to every selected key"
    bl_options = {"REGISTER", "UNDO"}

    note: StringProperty(  # type: ignore[valid-type]
        name="Note",
        description="Free-form annotation written into the metadata note field",
        default="",
    )

    def execute(self, context):
        scene = context.scene
        n = 0
        for obj, _a, fc, _i, kp in iter_selected_keys(context):
            meta.upsert_meta(scene, key_identity(obj.name, fc, kp.co.x), note=self.note)
            n += 1
        self.report({"INFO"}, f"Note set on {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_protect_selected(_AnimEditorOp):
    bl_idname = "animassist.protect_selected_keys"
    bl_label = "Protect Selected Keys"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Mark or unmark selected keys as protected from Safe Delete"
    bl_options = {"REGISTER", "UNDO"}

    protected: BoolProperty(  # type: ignore[valid-type]
        name="Protected",
        description="True to protect, False to clear the protected flag",
        default=True,
    )

    def execute(self, context):
        scene = context.scene
        n = 0
        for obj, _a, fc, _i, kp in iter_selected_keys(context):
            meta.upsert_meta(
                scene, key_identity(obj.name, fc, kp.co.x), protected=self.protected
            )
            n += 1
        self.report({"INFO"}, f"{'Protected' if self.protected else 'Unprotected'} {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_set_key_flavor(_AnimEditorOp):
    bl_idname = "animassist.set_key_flavor"
    bl_label = "Set Key Flavor"
    # --- EXPLAINER HELP INTEGRATION ---
    bl_description = "Stamp a 'flavor' label (block / spline / polish) onto every selected key"
    bl_options = {"REGISTER", "UNDO"}

    flavor: StringProperty(  # type: ignore[valid-type]
        name="Flavor",
        description="Secondary tag axis stored in the metadata flavor field",
        default="",
    )

    def execute(self, context):
        scene = context.scene
        n = 0
        for obj, _a, fc, _i, kp in iter_selected_keys(context):
            meta.upsert_meta(scene, key_identity(obj.name, fc, kp.co.x), flavor=self.flavor)
            n += 1
        self.report({"INFO"}, f"Flavor set on {n} keys")
        return {"FINISHED"}


class ANIMASSIST_OT_clear_all_metadata(_AnimEditorOp):
    bl_idname = "animassist.clear_all_key_metadata"
    bl_label = "Clear All Key Metadata"
    bl_description = "Remove every key metadata record from the scene"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        pg = getattr(scene, "anim_assist", None)
        if pg is None:
            return {"CANCELLED"}
        n = len(pg.key_metadata)
        pg.key_metadata.clear()
        meta.mark_dirty(scene)
        self.report({"INFO"}, f"Cleared {n} records")
        return {"FINISHED"}


class ANIMASSIST_OT_prune_orphan_metadata(_AnimEditorOp):
    bl_idname = "animassist.prune_orphan_key_metadata"
    bl_label = "Prune Orphan Key Metadata"
    bl_description = "Drop metadata whose keyframe no longer exists"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        removed = meta.prune_orphans(context)
        self.report({"INFO"}, f"Pruned {removed} records")
        return {"FINISHED"}


classes: tuple[type, ...] = (
    ANIMASSIST_OT_tag_selected_keys,
    ANIMASSIST_OT_clear_tag_selected,
    ANIMASSIST_OT_set_key_note,
    ANIMASSIST_OT_protect_selected,
    ANIMASSIST_OT_set_key_flavor,
    ANIMASSIST_OT_clear_all_metadata,
    ANIMASSIST_OT_prune_orphan_metadata,
)
