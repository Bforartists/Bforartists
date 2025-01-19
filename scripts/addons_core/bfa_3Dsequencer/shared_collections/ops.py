# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

import bpy

from bfa_3Dsequencer.shared_collections import core
from bfa_3Dsequencer.utils import register_classes, unregister_classes


class COLLECTION_OT_shared_folder_from_collection(bpy.types.Operator):
    bl_idname = "collection.shared_folder_from_collection"
    bl_label = "Make Shared Collection"
    bl_description = "Create a shared collection from an existing collection"
    bl_options = {"UNDO"}

    @classmethod
    def poll(self, context: bpy.types.Context):
        return context.collection and not core.is_shared_folder(context.collection)

    def execute(self, context: bpy.types.Context):
        core.make_shared_folder_from_collection(context.collection)
        return {"FINISHED"}


def get_scenes_from_selected_sequences(
    sed: bpy.types.SequenceEditor,
) -> list[bpy.types.Scene]:
    """Return scenes from the list of selected sequences in `sed`."""
    return [
        s.scene
        for s in sed.sequences
        if isinstance(s, bpy.types.Strip) and s.select and s.scene
    ]


def get_active_or_selected_scenes(context: bpy.types.Context) -> list[bpy.types.Scene]:
    """
    Get active or selected scenes based on `context`.
    If context's area is a sequence editor, returns all the scenes from selected scene strips.
    Otherwise, return a list containing only context's active scene.

    :param context: The context.
    :return: The list of (active or selected) scenes based on `context`.
    """
    if context.area.type == "SEQUENCE_EDITOR" and context.scene.sequence_editor:
        return get_scenes_from_selected_sequences(context.scene.sequence_editor)
    else:
        return [context.scene]


def build_collection_colors_enum():
    """Build the enum list of available collection colors."""
    values = [("NONE", "", "", "OUTLINER_COLLECTION", 0)]
    for i in range(1, 9):
        values.append((f"COLOR_{i:02}", "", "", f"COLLECTION_COLOR_{i:02}", i))
    return values


class COLLECTION_OT_shared_folder_new(bpy.types.Operator):
    bl_idname = "collection.shared_folder_new"
    bl_label = "New Shared Collection"
    bl_description = "Create a new shared collection"
    bl_options = {"UNDO"}
    # Setup "name" as primary property (gets UI focus)
    bl_property = "name"

    name: bpy.props.StringProperty(
        name="Name", description="Name of the shared collection", options={"SKIP_SAVE"}
    )

    # Build the color enum items list once
    COLLECTION_COLOR_ENUM = build_collection_colors_enum()

    color: bpy.props.EnumProperty(
        name="Color",
        description="Shared collection color",
        items=COLLECTION_COLOR_ENUM,
    )

    sequencer_link_mode: bpy.props.EnumProperty(
        name="Link in Shots",
        items=(
            ("NONE", "None", "None"),
            ("CURRENT", "Current", "Current Scene"),
            ("SELECTED", "Selected", "Selected Scene"),
        ),
        default="SELECTED",
    )

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event):
        return context.window_manager.invoke_props_dialog(self, width=340)

    def draw(self, context: bpy.types.Context):
        self.layout.use_property_split = True
        self.layout.prop(self, "name")
        self.layout.prop(self, "color", expand=True, text="Color")
        if context.area.type == "SEQUENCE_EDITOR":
            self.layout.prop(self, "sequencer_link_mode")

    def execute(self, context: bpy.types.Context):
        if not self.name:
            self.report({"ERROR"}, "Shared collection name is empty")
            return {"CANCELLED"}

        # Get scenes based on context
        scenes = get_active_or_selected_scenes(context)
        if context.area.type == "SEQUENCE_EDITOR":
            if self.sequencer_link_mode == "CURRENT":
                # Easy way of getting the currently active scene in a VSE override setup
                scenes = [context.window.scene]
            elif self.sequencer_link_mode == "NONE":
                scenes = []

        col, linked = core.create_and_link_shared_folder(self.name, scenes)
        col.color_tag = self.color
        core.set_active_shared_folder(context, col)

        self.report(
            {"INFO"},
            f"Shared collection '{self.name}' created and linked in {len(linked)} scene(s)",
        )

        if context.area.type == "SEQUENCE_EDITOR":
            context.area.tag_redraw()

        return {"FINISHED"}


class COLLECTION_OT_shared_folder_shots_link(bpy.types.Operator):
    bl_idname = "collection.shared_folder_shots_link"
    bl_label = "Link Shared Collection in Shots"
    bl_description = "Link a shared collection in active or selected scenes"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared Collection")

    def execute(self, context: bpy.types.Context):
        scenes = get_active_or_selected_scenes(context)
        collection = bpy.data.collections[self.shared_folder_name]
        linked = core.link_shared_folder(collection, scenes)
        core.set_active_shared_folder(context, collection)

        self.report(
            {"INFO"},
            f"Linked shared collection '{self.shared_folder_name}' in {len(linked)} scene(s)",
        )

        if not linked:
            return {"CANCELLED"}

        return {"FINISHED"}


class COLLECTION_OT_shared_folder_shots_unlink(bpy.types.Operator):
    bl_idname = "collection.shared_folder_shots_unlink"
    bl_label = "Unlink Shared Collection from Scenes"
    bl_description = "Unlink a shared collection from active or selected scenes"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared Collection")

    def execute(self, context: bpy.types.Context):
        scenes = get_active_or_selected_scenes(context)
        collection = bpy.data.collections[self.shared_folder_name]
        unlinked = core.unlink_shared_folder(collection, scenes)
        core.set_active_shared_folder(context, collection)

        self.report(
            {"INFO"},
            f"Unlinked shared collection '{self.shared_folder_name}' from {len(unlinked)} scene(s)",
        )

        if not unlinked:
            return {"CANCELLED"}

        return {"FINISHED"}


class COLLECTION_OT_shared_folder_shots_select(bpy.types.Operator):
    bl_idname = "collection.shared_folder_shots_select"
    bl_label = "Select Scenes by Shared collection"
    bl_description = "Select scenes that uses a shared collection"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared collection")

    @classmethod
    def poll(self, context: bpy.types.Context):
        return context.scene.sequence_editor is not None

    def execute(self, context: bpy.types.Context):
        seqs = core.get_scene_sequence_users(
            bpy.data.collections[self.shared_folder_name], context.scene.sequence_editor
        )
        bpy.ops.sequencer.select_all(action="DESELECT")
        for seq in seqs:
            seq.select = True

        return {"FINISHED"}


class COLLECTION_OT_shared_folder_delete(bpy.types.Operator):
    bl_idname = "collection.shared_folder_delete"
    bl_label = "Delete Shared collection"
    bl_description = "Delete a shared collection"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared collection")

    def execute(self, context: bpy.types.Context):
        core.delete_shared_folder(bpy.data.collections[self.shared_folder_name])
        self.report({"INFO"}, f"Deleted shared collection '{self.shared_folder_name}'")

        return {"FINISHED"}


classes = (
    COLLECTION_OT_shared_folder_from_collection,
    COLLECTION_OT_shared_folder_new,
    COLLECTION_OT_shared_folder_shots_link,
    COLLECTION_OT_shared_folder_shots_unlink,
    COLLECTION_OT_shared_folder_shots_select,
    COLLECTION_OT_shared_folder_delete,
)


def register():
    register_classes(classes)


def unregister():
    unregister_classes(classes)
