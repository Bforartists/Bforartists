# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

from typing import Optional

import bpy

from ..preferences import get_addon_prefs
from .core import (
    delete_scene,
    duplicate_scene,
    get_valid_shot_scenes,
    rename_scene,
    slip_shot_content,
)
from .naming import shot_naming, ShotNamingProperty
from ..sync.core import (
    remap_frame_value,
)
from ..utils import register_classes, unregister_classes


def get_last_sequence(
    strips: list[bpy.types.Strip],
) -> Optional[bpy.types.Strip]:
    """Get the last sequence, i.e. the one with the greatest final frame number."""
    return max(strips, key=lambda x: x.right_handle) if strips else None


def get_last_used_frame(
    strips: list[bpy.types.Strip], scene: bpy.types.Scene
) -> int:
    """
    Get the last used internal frame of `scene` from the given list of `strips`.
    """
    scene_strips = [
        s
        for s in strips
        if isinstance(s, bpy.types.SceneStrip) and s.scene == scene
    ]

    if not scene_strips:
        return scene.frame_start - 1

    return max(remap_frame_value(s.right_handle - 1, s) for s in scene_strips)


def get_selected_scene_sequences(
    strips: list[bpy.types.Strip],
) -> list[bpy.types.SceneStrip]:
    """
    :param strips: The strips to consider.
    :return: The list of selected scene sequence strips.
    """
    return [s for s in strips if isinstance(s, bpy.types.SceneStrip) and s.select]


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
    bl_description = "Create a new scene and append it to the timeline"
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
        description="Scene creation mode",
        items=(
            ("EXISTING", "Use Existing", "Use existing scene"),
            ("TEMPLATE", "New From Template", "Create a new scene from a template"),
        ),
        default="EXISTING",
        update=update_default_source_scene,
    )

    source_scene: bpy.props.EnumProperty(
        name="Source",
        description="The scene the new scene will use (either directly or a copy of it)",
        items=get_template_scenes,
    )

    name: bpy.props.StringProperty(
        name="Scene Name",
        default="",
        options={"SKIP_SAVE"},
    )

    naming: bpy.props.PointerProperty(
        type=ShotNamingProperty,
        name="Scene Naming",
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
        if not context.sequencer_scene.sequence_editor:
            context.scene.sequence_editor_create()

        strips = context.sequencer_scene.sequence_editor.strips
        frame_offset_start = 0

        # Source scene handling.
        if self.scene_mode == "EXISTING":
            # Use existing scene as is.
            shot_scene = source_scene
            # Get the last frame used in the source scene to initialize the new strip.
            frame_offset_start = get_last_used_frame(strips, source_scene)
        else:
            # Duplicate source scene.
            shot_scene = duplicate_scene(context, source_scene, self.name)
            # Set new scene's frame_end based on duration.
            # Note: the end frame must be last 'useful' frame, hence the -1.
            shot_scene.frame_end = shot_scene.frame_start + self.duration - 1

        last_seq = get_last_sequence(strips)
        insert_frame = (
            last_seq.right_handle if last_seq else context.scene.frame_start
        )

        bpy.ops.sequencer.select_all(action="DESELECT")
        # Create a scene strip from the newly created scene.
        new_strip = strips.new_scene(
            self.naming.to_string(), shot_scene, self.channel, insert_frame
        )
        new_strip.duration = self.duration
        slip_shot_content(new_strip, frame_offset_start)
        new_strip.scene_camera = new_strip.scene.camera
        context.sequencer_scene.sequence_editor.active_strip = new_strip

        if self.scene_mode == "EXISTING":
            shot_scene.camera = source_scene.camera

        context.sequencer_scene.frame_end = max(
            new_strip.right_handle - 1, context.sequencer_scene.frame_end
        )

        # Move current frame to the new strip's start frame.
        context.sequencer_scene.frame_set(insert_frame)

        # Ensure newly created scene is visible.
        ensure_sequencer_frame_visible(context, new_strip.right_handle)

        self.report({"INFO"}, f"Created new scene '{new_strip.name}'")

        return {"FINISHED"}


class SEQUENCER_OT_shot_duplicate(bpy.types.Operator):
    bl_idname = "sequencer.shot_duplicate"
    bl_label = "Duplicate"
    bl_description = "Duplicate selected scene(s) and append them to the timeline"
    bl_options = {"UNDO"}

    duplicate_scene: bpy.props.BoolProperty(
        name="Duplicate Scene",
        description="Whether to also duplicate the underlying Scene",
        default=False,
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return bool(context.selected_strips)

    @staticmethod
    def duplicate_shot(
        context: bpy.types.Context,
        strip: bpy.types.SceneStrip,
        name: str,
        duplicate_scene: bool,
    ) -> bpy.types.SceneStrip:
        sed = strip.id_data.sequence_editor
        if duplicate_scene:
            shot_scene = duplicate_scene(context, strip.scene, name)
        else:
            shot_scene = strip.scene

        # Find the frame where to insert the duplicated strip
        insert_frame = get_last_sequence(sed.strips).right_handle

        # Create new strip
        new_strip = sed.strips.new_scene(
            name, shot_scene, strip.channel, insert_frame
        )

        new_strip.duration = strip.duration

        if not duplicate_scene:
            new_strip.scene_camera = strip.scene_camera
            frame_offset = get_last_used_frame(sed.strips, shot_scene)
            slip_shot_content(new_strip, frame_offset)
        else:
            new_strip.scene_camera = strip.scene.camera

        return new_strip

    def execute(self, context: bpy.types.Context):
        sed = context.scene.sequence_editor

        new_strips = []
        for strip in get_selected_scene_sequences(sed.strips):
            name = shot_naming.next_shot_name_from_sequences(sed)
            new_strip = self.duplicate_shot(context, strip, name, self.duplicate_scene)
            new_strips.append(new_strip)

        if not new_strips:
            return {"CANCELLED"}

        # Move current frame to the new strip's start frame.
        context.scene.frame_set(new_strips[0].left_handle)

        # Deselect all strips
        bpy.ops.sequencer.select_all(action="DESELECT")

        # Set the duplicated strip as the active one
        sed.active_strip = new_strips[0]
        for strip in new_strips:
            strip.select = True

        context.scene.frame_end = max(
            new_strips[-1].right_handle - 1, context.scene.frame_end
        )

        # Ensure created strips are visible.
        ensure_sequencer_frame_visible(context, new_strips[0].right_handle)

        self.report({"INFO"}, f"Duplicated {len(new_strips)} scene(s)")

        return {"FINISHED"}


class SEQUENCER_OT_shot_delete(bpy.types.Operator):
    bl_idname = "sequencer.shot_delete"
    bl_label = "Delete Scene"
    bl_description = "Delete selected scene(s) and optionally attached datablocks"
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
        return bool(context.selected_strips)

    def invoke(self, context: bpy.types.Context, event):
        self.strips = get_selected_scene_sequences(
            context.scene.sequence_editor.strips
        )
        if not self.strips:
            self.report({"ERROR"}, "No selected scenes")
            return {"CANCELLED"}

        self.scenes = set([s.scene for s in self.strips if s.scene])
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout.row()
        row.label(text=f"Delete {len(self.strips)} selected scene strip(s)?")
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
        strips = get_selected_scene_sequences(context.scene.sequence_editor.strips)

        # Store scenes to delete in a set to avoid duplicates
        scenes = set()
        # Delete the strips
        for strip in strips:
            if strip.scene and self.delete_scenes:
                scenes.add(strip.scene)
            context.scene.sequence_editor.strips.remove(strip)

        # Delete the scenes
        for scene in scenes:
            deleted_datablocks += delete_scene(scene, self.delete_orphan_scene_data)

        context.area.tag_redraw()
        self.report(
            {"INFO"},
            f"Deleted {len(strips)} scenes and {deleted_datablocks} datablock(s)",
        )

        return {"FINISHED"}


# BFA (#6780): opt-in batch operator aligning every scene strip's scene frame range
# (sfra/efra, the render range) to its visible extent in the sequencer timeline,
# with optional lead-in/out padding. Only the scene frame range is affected - the
# preview range, the strip's position in the master timeline and the strip's
# internal time range all stay unchanged. Non-destructive: strip handles/content
# are re-pinned after the range write (the Set-Scene-Range lesson) so the displayed
# content stays exactly where it is.
class SEQUENCER_OT_sync_scene_strip_ranges(bpy.types.Operator):
    """Set start and end frame of each scene strip's scene so they align to the strip's preview range in the sequencer timeline"""

    bl_idname = "sequencer.sync_scene_strip_ranges"
    bl_label = "Sync Scene Strip Frame Ranges"
    bl_description = (
        "Set start and end frame of each scene strip's scene to align with the "
        "strip's visible range in the sequencer timeline, with optional lead-in/out "
        "padding. Non-destructive: the strips keep their position in the timeline"
    )
    bl_options = {'REGISTER', 'UNDO'}

    lead_in: bpy.props.IntProperty(
        name="Lead In",
        description="Frames of padding added before each scene strip's content",
        default=0,
        min=0,
    )
    lead_out: bpy.props.IntProperty(
        name="Lead Out",
        description="Frames of padding added after each scene strip's content",
        default=0,
        min=0,
    )

    @classmethod
    def poll(cls, context: bpy.types.Context):
        # The master timeline lives on the sequencer scene (context.sequencer_scene),
        # not on the active shot scene (context.scene) - the old poll used the latter
        # and was permanently disabled in the Scene menu.
        ed = context.sequencer_scene.sequence_editor if context.sequencer_scene else None
        return ed is not None and any(
            isinstance(s, bpy.types.SceneStrip) for s in ed.strips_all
        )

    @staticmethod
    def iter_scene_strips(context: bpy.types.Context) -> list[bpy.types.SceneStrip]:
        ed = context.sequencer_scene.sequence_editor
        if not ed:
            return []
        # strips_all: recursive, meta-inclusive.
        return [s for s in ed.strips_all if isinstance(s, bpy.types.SceneStrip)]

    def invoke(self, context: bpy.types.Context, _event):
        # Operator dialog asking for lead-in/out, then Confirm runs execute().
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        strips = self.iter_scene_strips(context)
        todo = [s for s in strips if s.scene is not None]

        # 1. Per-scene target range: union of the visible extents of every strip
        #    sharing the scene, remapped into the scene's referential, padded.
        targets: dict[str, tuple[int, int]] = {}
        for strip in todo:
            # Scene frame shown at the strip's left handle (remap_frame_value identity).
            v_start = remap_frame_value(strip.left_handle, strip)
            v_end = remap_frame_value(strip.right_handle - 1, strip)
            if strip.scene.name in targets:
                old_start, old_end = targets[strip.scene.name]
                targets[strip.scene.name] = (
                    min(old_start, v_start),
                    max(old_end, v_end),
                )
            else:
                targets[strip.scene.name] = (v_start, v_end)

        # 2. Apply scene ranges, remembering each strip's pre-state.
        pre_state = []
        for strip in todo:
            v_start, v_end = targets[strip.scene.name]
            scene = strip.scene
            pre_state.append(
                (
                    strip,
                    strip.content_start,
                    strip.left_handle,
                    strip.right_handle,
                    strip.channel,
                    strip.duration,
                )
            )
            # A scene cannot start at a negative frame.
            scene.frame_start = max(v_start - self.lead_in, 1)
            scene.frame_end = v_end + self.lead_out

        # 3. Re-anchor strips: the scene-range write above can auto-derive a
        #    scene strip's content length (the Set-Scene-Range lesson), so read
        #    back and restore handles/content position exactly.
        for strip, content_start, left, right, channel, duration in pre_state:
            strip.content_start = content_start
            strip.channel = channel
            strip.duration = duration
            strip.left_handle = left
            strip.right_handle = right

        self.report(
            {'INFO'},
            f"Updated {len(targets)} scene strip range(s)"
            + (f", {len(strips) - len(todo)} skipped (no scene)" if len(todo) != len(strips) else ""),
        )
        return {'FINISHED'}


class SEQUENCER_OT_shot_rename(bpy.types.Operator):
    bl_idname = "sequencer.shot_rename"
    bl_label = "Rename"
    bl_description = "Rename the active scene"
    bl_options = {"REGISTER", "UNDO"}

    naming: bpy.props.PointerProperty(
        type=ShotNamingProperty,
        description="Name of the scene using shot naming system",
    )

    rename_scene: bpy.props.BoolProperty(
        name="Rename Scene",
        description="Whether to also rename strip's scene",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.scene.sequence_editor and isinstance(
            cls.active_shot(context), bpy.types.SceneStrip
        )

    @staticmethod
    def active_shot(context) -> bpy.types.SceneStrip:
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
            context.scene.sequence_editor.strips,
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
        # Evaluate scene strip renaming.
        if new_name != shot_strip.name:
            # Ensure strip name is available.
            if new_name in context.scene.sequence_editor.strips:
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
            for strip in context.scene.sequence_editor.strips
            if isinstance(strip, bpy.types.SceneStrip)
        ]

        if not scene_strips:
            return {"CANCELLED"}

        tmp_suffix = ".tmp.rename"
        current_name = ""
        scenes_to_rename = set()
        items_to_rename: dict[bpy.types.SceneStrip, tuple[str, bool]] = dict()

        # Go through the shots chronologically (sorted by the start frame)
        sorted_scene_strips = sorted(scene_strips, key=lambda x: x.left_handle)

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
    SEQUENCER_OT_sync_scene_strip_ranges,
    SEQUENCER_OT_shot_rename,
    SEQUENCER_OT_shot_chronological_numbering,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
