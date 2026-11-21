"""User-facing operators for install/uninstall hygiene.

Provides:

* ``animassist.deep_uninstall`` — wipe every persistent trace of Anim Assist
  from the current .blend before disabling the addon. Asks for confirmation,
  exposes per-category toggles in the dialog so the user can scope what gets
  cleared.

* ``animassist.purge_zombie_classes`` — manual trigger for the same defensive
  cleanup that runs at the top of register(). Exposed as an operator so users
  who hit "class already registered" errors can fix them without restarting
  Bforartists.

* ``animassist.report_saved_versions`` — diagnostic that walks open scenes
  and prints any saved schema versions newer than the installed addon.
"""

from __future__ import annotations

from bpy.props import BoolProperty
from bpy.types import Operator

from ..core import lifecycle
from ..core.logging import get_logger
from ..core.helpers import confirm_dialog, report_failure

_log = get_logger(__name__)


class AA_OT_deep_uninstall(Operator):
    """Wipe all Anim Assist data from the current .blend.

    Run BEFORE disabling/uninstalling the addon for a clean slate. After
    this finishes, disable the addon and re-enable it (or install a new
    version) - no leftover state will collide.

    WARNING: This is destructive. It removes hand-flagged manual override
    keys, lipsync sequencer strips, and Speakers created by the setup
    operator. Hand-keyed animation data on the bones themselves is NOT
    removed - only Anim Assist's per-key metadata sidecar.
    """

    bl_idname = "animassist.deep_uninstall"
    bl_label = "Anim Assist: Deep Uninstall (Purge All Data)"
    bl_options = {"REGISTER"}

    purge_action_props: BoolProperty(  # type: ignore[valid-type]
        name="Manual Override Flags",
        description=(
            "Remove the per-keyframe manual-override sidecar metadata from "
            "every Action. Your keyframes themselves are not deleted."
        ),
        default=True,
    )
    purge_scene_data: BoolProperty(  # type: ignore[valid-type]
        name="Scene PropertyGroups",
        description=(
            "Clear all Anim Assist scene-level configuration (layer stacks, "
            "lipsync layer links, viseme captures, rig wiring). Resets the "
            "addon to a fresh state on this .blend."
        ),
        default=True,
    )
    purge_sequencer: BoolProperty(  # type: ignore[valid-type]
        name="Lipsync Sequencer Strips",
        description="Remove sound strips named AA_P12_* from every scene's sequencer",
        default=True,
    )
    purge_speakers: BoolProperty(  # type: ignore[valid-type]
        name="Lipsync Speakers",
        description="Remove Speaker datablocks named AA_P12_*",
        default=True,
    )
    purge_handlers: BoolProperty(  # type: ignore[valid-type]
        name="App Handlers",
        description=(
            "Remove any application handlers (load_post, undo_post, etc.) "
            "registered by the addon. Defensive cleanup if a previous "
            "register() left handlers behind"
        ),
        default=True,
    )

    def invoke(self, context, event):  # noqa: ARG002
        return context.window_manager.invoke_props_dialog(self, width=420)

    def draw(self, context):  # noqa: ARG002
        layout = self.layout
        layout.label(text="Wipe Anim Assist data from this .blend?", icon="ERROR")
        col = layout.column(align=True)
        col.prop(self, "purge_action_props")
        col.prop(self, "purge_scene_data")
        col.prop(self, "purge_sequencer")
        col.prop(self, "purge_speakers")
        col.prop(self, "purge_handlers")
        layout.separator()
        layout.label(
            text="Run this before uninstalling for a clean reinstall.",
            icon="INFO",
        )

    def execute(self, context):  # noqa: ARG002
        try:
            counts = lifecycle.deep_uninstall(
                purge_action_props=self.purge_action_props,
                purge_scene_data=self.purge_scene_data,
                purge_sequencer=self.purge_sequencer,
                purge_speakers=self.purge_speakers,
                purge_handlers=self.purge_handlers,
            )
        except Exception as exc:
            _log.exception("deep_uninstall failed")
            return report_failure(self, "Deep uninstall did not finish", "Save your file, restart Bforartists, and run it again", exc)

        msg = (
            "Purged: " + str(counts["action_idprops"]) + " action flags, "
            + str(counts["scenes_reset"]) + " scenes, "
            + str(counts["seq_strips_removed"]) + " strips, "
            + str(counts["speakers_removed"]) + " speakers, "
            + str(counts["handlers_removed"]) + " handlers"
        )
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class AA_OT_purge_zombie_classes(Operator):
    """Force-unregister any leftover Anim Assist classes from a prior load.

    Useful if Bforartists reports 'class already registered' on enable.
    """

    bl_idname = "animassist.purge_zombie_classes"
    bl_label = "Anim Assist: Repair Registration"
    bl_description = "Force-unregister leftover Anim Assist classes from a previous load. Use when enabling reports 'class already registered'"
    bl_options = {"REGISTER"}

    def invoke(self, context, event):  # type: ignore[no-untyped-def]
        return confirm_dialog(self, context, event, 'Force-unregister leftover Anim Assist classes? Disable and re-enable the add-on afterwards.')

    def execute(self, context):  # noqa: ARG002
        removed = lifecycle.purge_zombie_classes()
        if removed:
            self.report({"WARNING"}, "Removed " + str(removed) + " zombie class(es)")
        else:
            self.report({"INFO"}, "No zombie classes found")
        return {"FINISHED"}


class AA_OT_report_saved_versions(Operator):
    """Report any open scenes saved with a newer Anim Assist than installed."""

    bl_idname = "animassist.report_saved_versions"
    bl_label = "Anim Assist: Check Saved Settings Version"
    bl_options = {"REGISTER"}

    def execute(self, context):  # noqa: ARG002
        warnings = lifecycle.check_saved_versions()
        if not warnings:
            self.report({"INFO"}, "All open scenes are within installed schema range")
            return {"FINISHED"}
        for w in warnings:
            self.report({"WARNING"}, w)
        return {"FINISHED"}


CLASSES: tuple[type, ...] = (
    AA_OT_deep_uninstall,
    AA_OT_purge_zombie_classes,
    AA_OT_report_saved_versions,
)
