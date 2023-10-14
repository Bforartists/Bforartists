# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

from typing import Optional

import bpy

from spa_sequencer.preferences import get_addon_prefs
from spa_sequencer.shot.core import (
    adjust_shot_duration,
    delete_scene,
    duplicate_scene,
    get_valid_shot_scenes,
    rename_scene,
    slip_shot_content,
)
from spa_sequencer.shot.naming import shot_naming, ShotNamingProperty
from spa_sequencer.sync.core import (
    get_sync_master_strip,
    get_sync_settings,
    remap_frame_value,
)
from spa_sequencer.utils import register_classes, unregister_classes


def get_last_sequence(
    sequences: list[bpy.types.Sequence],
) -> Optional[bpy.types.Sequence]:
    """Get the last sequence, i.e. the one with the greatest final frame number."""
    return max(sequences, key=lambda x: x.frame_final_end) if sequences else None


def get_last_used_frame(
    sequences: list[bpy.types.Sequence], scene: bpy.types.Scene
) -> int:
    """
    Get the last used internal frame of `scene` from the given list of `sequences`.
    """
    scene_sequences = [
        s
        for s in sequences
        if isinstance(s, bpy.types.SceneSequence) and s.scene == scene
    ]

    if not scene_sequences:
        return scene.frame_start - 1

    return max(remap_frame_value(s.frame_final_end - 1, s) for s in scene_sequences)


def get_selected_scene_sequences(
    sequences: list[bpy.types.Sequence],
) -> list[bpy.types.SceneSequence]:
    """
    :param sequences: The sequences to consider.
    :return: The list of selected scene sequence strips.
    """
    return [s for s in sequences if isinstance(s, bpy.types.SceneSequence) and s.select]


def ensure_sequencer_frame_visible(context: bpy.types.Context, frame: int):
    """Ensure `frame` is visible within context's sequencer area.

    :param context: The context - context.area has to be a SequenceEditor.
    :param frame: The frame to consider.
    """
    if not context.area.type == "SEQUENCE_EDITOR":
        return
    frame_coord = context.region.view2d.view_to_region(frame, 0, clip=False)[0]
    if frame_coord < 0 or frame_coord > context.region.width:
        # Temp override current frame value and move view to frame.
        frame_old = context.scene.frame_current
        context.scene.frame_current = frame
        bpy.ops.sequencer.view_frame()
        context.scene.frame_current = frame_old


class SEQUENCER_OT_shot_new(bpy.types.Operator):
    bl_idname = "sequencer.shot_new"
    bl_label = "New Shot"
    bl_description = "Create a new shot and append it to the timeline"
    bl_options = {"REGISTER", "UNDO"}

    template_names = []

    def get_template_scenes(self, context):
        """Get the scenes matching template naming rule defined in preferences."""
        prefs = get_addon_prefs()
        prefix = prefs.shot_template_prefix

        shot_scenes = get_valid_shot_scenes()

        def matches_mode(scene):
            match self.scene_mode:
                case "EXISTING":
                    # Do not consider templates when using an existing scene.
                    return scene in shot_scenes
                case "TEMPLATE":
                    # Only show template scenes in this case.
                    return scene.name.startswith(prefix)
                case _:
                    return True

        # Keep this enum values list alive (see https://developer.blender.org/T97243).
        SEQUENCER_OT_shot_new.template_names = [
            (s.name, s.name, "")
            for s in bpy.data.scenes
            if s != context.scene and matches_mode(s)
        ]

        return SEQUENCER_OT_shot_new.template_names

    def update_default_source_scene(self, context):
        if self.scene_mode == "EXISTING" and (
            scene := getattr(context.scene.sequence_editor.active_strip, "scene")
        ):
            self.source_scene = scene.name

    scene_mode: bpy.props.EnumProperty(
        name="Scene",
        description="Shot creation mode",
        items=(
            ("EXISTING", "Use Existing", "Use existing scene"),
            ("TEMPLATE", "New From Template", "Create a new scene from a template"),
        ),
        default="EXISTING",
        update=update_default_source_scene,
    )

    source_scene: bpy.props.EnumProperty(
        name="Source",
        description="The scene the new shot will use (either directly or a copy of it)",
        items=get_template_scenes,
    )

    name: bpy.props.StringProperty(
        name="Shot Name",
        default="",
        options={"SKIP_SAVE"},
    )

    naming: bpy.props.PointerProperty(
        type=ShotNamingProperty,
        name="Shot Naming",
    )

    duration: bpy.props.IntProperty(
        name="Duration",
        default=24,
        min=1,
    )

    channel: bpy.props.IntProperty(
        name="Channel",
        default=1,
        min=1,
        max=32,
    )

    def validate_inputs(self, context: bpy.types.Context) -> bool:
        if self.name == "":
            self.report({"ERROR_INVALID_INPUT"}, "Name cannot be empty")
            return False
        if self.source_scene not in bpy.data.scenes:
            self.report({"ERROR_INVALID_INPUT"}, "Source scene cannot be empty")
            return False
        return True

    def invoke(self, context: bpy.types.Context, _event):
        if not (sed := context.scene.sequence_editor):
            self.name = shot_naming.default_shot_name()
        else:
            self.name = shot_naming.next_shot_name_from_sequences(sed)
            self.naming.init_from_name(self.name)
            if self.scene_mode == "EXISTING" and (
                scene := getattr(sed.active_strip, "scene", None)
            ):
                self.source_scene = scene.name

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context: bpy.types.Context):
        self.layout.use_property_split = True
        row = self.layout.row(align=True)
        self.naming.draw(row, show_init_from_next=True)
        self.layout.prop(self, "scene_mode")
        self.layout.prop(self, "source_scene")
        self.layout.prop(self, "duration")
        self.layout.prop(self, "channel")

    def execute(self, context: bpy.types.Context):
        # Validate the inputs
        if not self.validate_inputs(context):
            return {"CANCELLED"}

        source_scene = bpy.data.scenes[self.source_scene]
        # Create sequence editor data if needed.
        if not context.scene.sequence_editor:
            context.scene.sequence_editor_create()

        sequences = context.scene.sequence_editor.sequences
        frame_offset_start = 0

        # Source scene handling.
        if self.scene_mode == "EXISTING":
            # Use existing scene as is.
            shot_scene = source_scene
            # Get the last frame used in the source scene to initialize the new strip.
            frame_offset_start = get_last_used_frame(sequences, source_scene)
        else:
            # Duplicate source scene.
            shot_scene = duplicate_scene(context, source_scene, self.name)
            # Set new scene's frame_end based on duration.
            # Note: the end frame must be last 'useful' frame, hence the -1.
            shot_scene.frame_end = shot_scene.frame_start + self.duration - 1

        last_seq = get_last_sequence(sequences)
        insert_frame = (
            last_seq.frame_final_end if last_seq else context.scene.frame_start
        )

        bpy.ops.sequencer.select_all(action="DESELECT")
        # Create a scene strip from the newly created scene.
        new_strip = sequences.new_scene(
            self.naming.to_string(), shot_scene, self.channel, insert_frame
        )
        new_strip.frame_final_duration = self.duration
        slip_shot_content(new_strip, frame_offset_start)
        new_strip.scene_camera = new_strip.scene.camera
        context.scene.sequence_editor.active_strip = new_strip

        if self.scene_mode == "EXISTING":
            shot_scene.camera = source_scene.camera

        context.scene.frame_end = max(
            new_strip.frame_final_end - 1, context.scene.frame_end
        )

        # Move current frame to the new strip's start frame.
        context.scene.frame_set(insert_frame)

        # Ensure newly created shot is visible.
        ensure_sequencer_frame_visible(context, new_strip.frame_final_end)

        self.report({"INFO"}, f"Created new shot '{new_strip.name}'")

        return {"FINISHED"}


class SEQUENCER_OT_shot_duplicate(bpy.types.Operator):
    bl_idname = "sequencer.shot_duplicate"
    bl_label = "Duplicate"
    bl_description = "Duplicate selected shot(s) and append them to the timeline"
    bl_options = {"UNDO"}

    duplicate_scene: bpy.props.BoolProperty(
        name="Duplicate Scene",
        description="Whether to also duplicate the underlying Scene",
        default=False,
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return bool(context.selected_sequences)

    @staticmethod
    def duplicate_shot(
        context: bpy.types.Context,
        strip: bpy.types.SceneSequence,
        name: str,
        duplicate_scene: bool,
    ) -> bpy.types.SceneSequence:
        sed = strip.id_data.sequence_editor
        if duplicate_scene:
            shot_scene = duplicate_scene(context, strip.scene, name)
        else:
            shot_scene = strip.scene

        # Find the frame where to insert the duplicated strip
        insert_frame = get_last_sequence(sed.sequences).frame_final_end

        # Create new strip
        new_strip = sed.sequences.new_scene(
            name, shot_scene, strip.channel, insert_frame
        )

        new_strip.frame_final_duration = strip.frame_final_duration

        if not duplicate_scene:
            new_strip.scene_camera = strip.scene_camera
            frame_offset = get_last_used_frame(sed.sequences, shot_scene)
            slip_shot_content(new_strip, frame_offset)
        else:
            new_strip.scene_camera = strip.scene.camera

        return new_strip

    def execute(self, context: bpy.types.Context):
        sed = context.scene.sequence_editor

        new_strips = []
        for strip in get_selected_scene_sequences(sed.sequences):
            name = shot_naming.next_shot_name_from_sequences(sed)
            new_strip = self.duplicate_shot(context, strip, name, self.duplicate_scene)
            new_strips.append(new_strip)

        if not new_strips:
            return {"CANCELLED"}

        # Move current frame to the new strip's start frame.
        context.scene.frame_set(new_strips[0].frame_final_start)

        # Deselect all strips
        bpy.ops.sequencer.select_all(action="DESELECT")

        # Set the duplicated strip as the active one
        sed.active_strip = new_strips[0]
        for strip in new_strips:
            strip.select = True

        context.scene.frame_end = max(
            new_strips[-1].frame_final_end - 1, context.scene.frame_end
        )

        # Ensure created strips are visible.
        ensure_sequencer_frame_visible(context, new_strips[0].frame_final_end)

        self.report({"INFO"}, f"Duplicated {len(new_strips)} shot(s)")

        return {"FINISHED"}


class SEQUENCER_OT_shot_delete(bpy.types.Operator):
    bl_idname = "sequencer.shot_delete"
    bl_label = "Delete Shot"
    bl_description = "Delete selected shot(s) and optionally attached datablocks"
    bl_options = {"UNDO"}

    delete_scenes: bpy.props.BoolProperty(
        name="Delete Scenes",
        description="Whether to also delete underlying scene(s)",
        default=False,
        options=set(),
    )

    delete_orphan_scene_data: bpy.props.BoolProperty(
        name="Delete Orphan Data",
        description="Delete any datablock orphaned by this process",
        default=True,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return bool(context.selected_sequences)

    def invoke(self, context: bpy.types.Context, event):
        self.strips = get_selected_scene_sequences(
            context.scene.sequence_editor.sequences
        )
        if not self.strips:
            self.report({"ERROR"}, "No selected shots")
            return {"CANCELLED"}

        self.scenes = set([s.scene for s in self.strips if s.scene])
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout.row()
        row.label(text=f"Delete {len(self.strips)} selected shot strip(s)?")
        box = self.layout.box()
        box.label(text="Advanced", icon="SETTINGS")
        row = box.row(align=True)
        row.prop(self, "delete_scenes")
        if self.delete_scenes:
            row.prop(self, "delete_orphan_scene_data")
            box.alert = True
            box.label(text="Those scene(s) will be deleted:", icon="ERROR")
            box.alert = False
            subbox = box.box()
            col = subbox.column(align=True)
            for scene in self.scenes:
                row = col.row()
                row.label(text=scene.name, icon="DOT")

    def execute(self, context: bpy.types.Context):
        deleted_datablocks = 0
        strips = get_selected_scene_sequences(context.scene.sequence_editor.sequences)

        # Store scenes to delete in a set to avoid duplicates
        scenes = set()
        # Delete the strips
        for strip in strips:
            if strip.scene and self.delete_scenes:
                scenes.add(strip.scene)
            context.scene.sequence_editor.sequences.remove(strip)

        # Delete the scenes
        for scene in scenes:
            deleted_datablocks += delete_scene(scene, self.delete_orphan_scene_data)

        context.area.tag_redraw()
        self.report(
            {"INFO"},
            f"Deleted {len(strips)} shots and {deleted_datablocks} datablock(s)",
        )

        return {"FINISHED"}


class SEQUENCER_OT_shot_timing_adjust(bpy.types.Operator):
    bl_idname = "sequencer.shot_timing_adjust"
    bl_label = "Adjust Timing"
    bl_description = "Adjust the timing of the active shot interactively"
    bl_options = {"GRAB_CURSOR_X", "BLOCKING", "UNDO"}

    offset: bpy.props.IntProperty(
        name="Offset",
    )

    mode: bpy.props.EnumProperty(
        name="Mode",
        items=(
            ("DURATION", "Duration", "Adjust strip duration"),
            ("SLIP", "Slip", "Slip strip content"),
        ),
        default="DURATION",
        options={"SKIP_SAVE"},
    )

    strip_handle: bpy.props.EnumProperty(
        name="Strip Adjustment Handle",
        items=(
            ("LEFT", "Left", "Left"),
            ("RIGHT", "Right", "Right"),
        ),
        default="RIGHT",
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return cls.get_active_strip(context) is not None

    @staticmethod
    def get_active_strip(
        context: bpy.types.Context,
    ) -> Optional[bpy.types.SceneSequence]:
        if context.area.type == "DOPESHEET_EDITOR":
            strip = get_sync_master_strip(use_cache=True)[0]
            return strip if strip and strip.scene == context.window.scene else None
        elif context.scene.sequence_editor and isinstance(
            context.scene.sequence_editor.active_strip, bpy.types.SceneSequence
        ):
            return context.scene.sequence_editor.active_strip

        return None

    def setup(self, context: bpy.types.Context):
        self.strip = self.get_active_strip(context)
        if not self.strip:
            self.report({"ERROR"}, "No current Shot Strip")
            return False
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        if not self.setup(context):
            return {"CANCELLED"}

        context.window.cursor_modal_set("SCROLL_X")

        self.start_mouse_coords = context.region.view2d.region_to_view(
            x=event.mouse_region_x, y=event.mouse_region_y
        )

        if context.area.type == "SEQUENCE_EDITOR":
            self.strip_handle = "LEFT" if self.strip.select_left_handle else "RIGHT"

        self.original_strip_duration = self.strip.frame_final_duration
        self.original_strip_scene_end = self.strip.scene.frame_end
        self.original_strip_offset_start = self.strip.frame_offset_start
        self.original_edit_frame_end = get_sync_settings().master_scene.frame_end

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def update_header_text(self, context, event):
        text = (
            f"Offset: {self.offset}"
            f" | New Shot Duration: {self.strip.frame_final_duration}"
        )
        context.area.header_text_set(text)

    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        self.update_header_text(context, event)
        # Cancel
        if event.type in {"RIGHTMOUSE", "ESC"}:
            self.cancel(context)
            return {"CANCELLED"}
        # Validate
        elif (event.type in {"LEFTMOUSE"} and event.value in {"PRESS", "RELEASE"}) or (
            event.type in {"RET", "NUMPAD_ENTER"} and event.value in {"PRESS"}
        ):
            if self.offset == 0:
                self.cancel(context)
                return {"CANCELLED"}
            self.restore_ui(context)
            return {"FINISHED"}
        # Update
        elif event.type in {"MOUSEMOVE"}:
            mouse_coords = context.region.view2d.region_to_view(
                x=event.mouse_region_x, y=event.mouse_region_y
            )
            offset = int(mouse_coords[0] - self.start_mouse_coords[0])
            if offset != self.offset:
                self.offset = offset
                self.execute(context)

        return {"RUNNING_MODAL"}

    def execute(self, context: bpy.types.Context):
        if not self.options.is_invoke:
            if not self.setup(context):
                return {"CANCELLED"}

        from_frame_start = self.strip_handle == "LEFT"
        select = self.mode == "DURATION"
        self.strip.select_left_handle = select and from_frame_start
        self.strip.select_right_handle = select and not from_frame_start
        # Adjust offset sign to match direction.
        # For instance, a positive offset (going to the right in modal):
        #  - SHRINKS the strip if using left handle (from frame start)
        #  - EXTENDS the strip otherwise (from frame end)
        offset = -self.offset if from_frame_start else self.offset
        # Compute current absolute offset from original duration
        if self.mode == "SLIP":
            delta = self.strip.frame_offset_start - self.original_strip_offset_start
            slip_shot_content(self.strip, offset - delta, clamp_start=True)
        else:
            delta = self.strip.frame_final_duration - self.original_strip_duration
            adjust_shot_duration(self.strip, offset - delta, from_frame_start)

        edit_scene = get_sync_settings().master_scene
        if from_frame_start or self.mode == "SLIP":
            # NOTE: When adjusting from frame start, the current frame does not change.
            #       Set time to a non meaningful value before re-setting the correct frame
            #       value, to trigger time-dependent updates (e.g: synchronization).
            edit_scene.frame_set(-1)
            update_frame = self.strip.frame_final_start
        else:
            update_frame = self.strip.frame_final_end - 1

        # Set sequencer's frame to strip's new end frame
        edit_scene.frame_set(update_frame)

        # Update both edit and internal scene's end frame if going past original ones
        frame_end = self.strip.frame_final_end - 1
        edit_scene.frame_end = max(frame_end, self.original_edit_frame_end)
        self.strip.scene.frame_end = max(
            remap_frame_value(frame_end, self.strip),
            self.original_strip_scene_end,
        )

        return {"FINISHED"}

    def restore_ui(self, context: bpy.types.Context):
        context.area.header_text_set(None)
        context.window.cursor_modal_restore()

    def cancel(self, context: bpy.types.Context):
        if self.offset:
            self.offset = 0
            self.execute(context)
        # Restore scenes' original end frames
        context.scene.frame_end = self.original_edit_frame_end
        self.strip.scene.frame_end = self.original_strip_scene_end
        self.restore_ui(context)


class SEQUENCER_OT_shot_rename(bpy.types.Operator):
    bl_idname = "sequencer.shot_rename"
    bl_label = "Rename"
    bl_description = "Rename the active shot"
    bl_options = {"REGISTER", "UNDO"}

    naming: bpy.props.PointerProperty(
        type=ShotNamingProperty,
        description="Name of the shot using shot naming system",
    )

    rename_scene: bpy.props.BoolProperty(
        name="Rename Scene",
        description="Whether to also rename strip's scene",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.scene.sequence_editor and isinstance(
            cls.active_shot(context), bpy.types.SceneSequence
        )

    @staticmethod
    def active_shot(context) -> bpy.types.SceneSequence:
        return context.scene.sequence_editor.active_strip

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        self.naming.init_from_name(self.active_shot(context).name)
        return context.window_manager.invoke_props_dialog(self)

    @staticmethod
    def draw_rename_details(
        layout,
        src: str,
        dst: str,
        icon: str,
        forbidden_names: Optional[list[str]] = None,
    ):
        """Helper function to draw renaming details from `src` to `dst`."""
        row = layout.row(align=True)
        row.alignment = "RIGHT"
        row.label(text=src, icon=icon)
        if src != dst:
            row.label(text=dst, icon="FORWARD")
            # Display warning if dst name is in the forbidden name list.
            if dst in forbidden_names:
                row.alert = True
                row.label(text="Already exists!", icon="ERROR")
                row.alert = False

    def draw(self, context: bpy.types.Context):
        shot_strip = self.active_shot(context)

        # Display naming widget.
        row = self.layout.row()
        self.naming.draw(row, show_init_from_next=True)
        current_name = self.naming.to_string()

        self.layout.prop(self, "rename_scene")

        # Strip renaming details.
        self.draw_rename_details(
            self.layout,
            shot_strip.name,
            current_name,
            "SEQUENCE",
            context.scene.sequence_editor.sequences,
        )

        # Scene renaming details.
        if self.rename_scene:
            self.draw_rename_details(
                self.layout,
                shot_strip.scene.name,
                current_name,
                "SCENE_DATA",
                bpy.data.scenes,
            )

    def execute(self, context: bpy.types.Context):
        shot_strip = self.active_shot(context)
        new_name = self.naming.to_string()

        # First, evaluate whether all renaming steps (strip/scene) can occur.
        do_rename_strip = do_rename_scene = False
        # Evaluate shot strip renaming.
        if new_name != shot_strip.name:
            # Ensure strip name is available.
            if new_name in context.scene.sequence_editor.sequences:
                self.report({"ERROR"}, f"Shot '{new_name}' already exists")
                return {"CANCELLED"}
            do_rename_strip = True
        # Evaluate scene renaming.
        if self.rename_scene and shot_strip.scene.name != new_name:
            # Ensure scene name is available.
            if new_name in bpy.data.scenes:
                self.report({"ERROR"}, f"Scene '{new_name}' already exists")
                return {"CANCELLED"}
            do_rename_scene = True

        # Perform renaming.
        if do_rename_strip:
            shot_strip.name = new_name
        if do_rename_scene:
            rename_scene(shot_strip.scene, new_name)

        # Force UI update to display new names in sequencer.
        context.area.tag_redraw()
        return {"FINISHED"}


class SEQUENCER_OT_shot_chronological_numbering(bpy.types.Operator):
    bl_idname = "sequencer.shot_chronological_numbering"
    bl_label = "Chronological Numbering"
    bl_description = (
        "Rename all the shots in the edit scene to follow a chronological numbering"
    )
    bl_options = {"REGISTER", "UNDO"}

    first_shot_name: bpy.props.PointerProperty(
        name="First Shot",
        type=ShotNamingProperty,
        description="Name of the first shot",
    )

    rename_scenes: bpy.props.EnumProperty(
        name="Rename Scenes Policy",
        items=(
            ("NONE", "None", "Do not rename scenes"),
            ("MATCHING", "Matching", "Only rename scene if it matches strip's name"),
            ("ALL", "All", "Rename all scenes to match strip's name"),
        ),
        description="Policy for renaming scenes",
        default="NONE",
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return context.scene.sequence_editor is not None

    def draw(self, context):
        self.layout.use_property_split = True
        self.layout.use_property_decorate = False
        self.first_shot_name.draw(self.layout, text="First Shot")
        self.layout.separator()
        self.layout.prop(self, "rename_scenes", text="Rename Scenes")

    def invoke(self, context: bpy.types.Context, event):
        return context.window_manager.invoke_props_dialog(self, width=350)

    def execute(self, context: bpy.types.Context):
        scene_strips = [
            strip
            for strip in context.scene.sequence_editor.sequences
            if isinstance(strip, bpy.types.SceneSequence)
        ]

        if not scene_strips:
            return {"CANCELLED"}

        tmp_suffix = ".tmp.rename"
        current_name = ""
        scenes_to_rename = set()
        items_to_rename: dict[bpy.types.SceneSequence, tuple[str, bool]] = dict()

        # Go through the shots chronologically (sorted by the start frame)
        sorted_scene_strips = sorted(scene_strips, key=lambda x: x.frame_final_start)

        # 1st pass: list items (strips/scenes) to rename.
        for strip in sorted_scene_strips:
            if not current_name:
                current_name = self.first_shot_name.to_string()
            else:
                current_name = shot_naming.next_shot_name_from_name(current_name)

            # Evaluate if scene has to be renamed.
            do_rename_scene = False
            if self.rename_scenes == "ALL" or (
                self.rename_scenes == "MATCHING" and strip.name == strip.scene.name
            ):
                # Store scenes to rename in a set. If multiple strips
                # uses the same scene, only consider the first renaming.
                if strip.scene not in scenes_to_rename:
                    scenes_to_rename.add(strip.scene)
                    do_rename_scene = True
            # Store renaming details for this strip.
            items_to_rename[strip] = (current_name, do_rename_scene)

        # 2nd pass: ensure new scene names won't conflict with existing ones.
        for strip, (new_name, do_rename_scene) in items_to_rename.items():
            if do_rename_scene and (scene := bpy.data.scenes.get(new_name, None)):
                # Check that the name does not clash with another scene that won't get
                # renamed.
                if scene not in scenes_to_rename:
                    # Stop the execution before renaming anything to avoid any partial
                    # renaming.
                    self.report(
                        {"ERROR"}, f"Name conflict: Scene {new_name} already exists"
                    )
                    return {"CANCELLED"}

        # 3rd pass: add temp suffix to avoid clashes between items to rename.
        for strip, (_, do_rename_scene) in items_to_rename.items():
            strip.name += tmp_suffix
            if do_rename_scene:
                rename_scene(strip.scene, strip.scene.name + tmp_suffix)

        # 4th pass: use final name.
        for strip, (new_name, do_rename_scene) in items_to_rename.items():
            strip.name = new_name
            if do_rename_scene:
                rename_scene(strip.scene, new_name)

        # NOTE: for sequencer override, force update area display.
        context.area.tag_redraw()
        return {"FINISHED"}


classes = (
    SEQUENCER_OT_shot_new,
    SEQUENCER_OT_shot_duplicate,
    SEQUENCER_OT_shot_delete,
    SEQUENCER_OT_shot_timing_adjust,
    SEQUENCER_OT_shot_rename,
    SEQUENCER_OT_shot_chronological_numbering,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
