# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2023, The SPA Studios. All rights reserved.

import bpy

from spa_sequencer.shared_folders import core
from spa_sequencer.utils import register_classes, unregister_classes


class COLLECTION_OT_shared_folder_from_collection(bpy.types.Operator):
    bl_idname = "collection.shared_folder_from_collection"
    bl_label = "Make Shared Folder"
    bl_description = "Create a shared folder from an existing collection"
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
        if isinstance(s, bpy.types.SceneSequence) and s.select and s.scene
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
    bl_label = "New Shared Folder"
    bl_description = "Create a new shared folder"
    bl_options = {"UNDO"}
    # Setup "name" as primary property (gets UI focus)
    bl_property = "name"

    name: bpy.props.StringProperty(
        name="Name", description="Name of the Shared Folder", options={"SKIP_SAVE"}
    )

    # Build the color enum items list once
    COLLECTION_COLOR_ENUM = build_collection_colors_enum()

    color: bpy.props.EnumProperty(
        name="Color",
        description="Shared Folder color",
        items=COLLECTION_COLOR_ENUM,
    )

    sequencer_link_mode: bpy.props.EnumProperty(
        name="Link in Shots",
        items=(
            ("NONE", "None", "None"),
            ("CURRENT", "Current", "Current Shot"),
            ("SELECTED", "Selected", "Selected Shots"),
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
            self.report({"ERROR"}, "Shared folder name is empty")
            return {"CANCELLED"}

        # Get scenes based on context
        scenes = get_active_or_selected_scenes(context)
        if context.area.type == "SEQUENCE_EDITOR":
            if self.sequencer_link_mode == "CURRENT":
                # Easy way of getting the currently active shot in a VSE override setup
                scenes = [context.window.scene]
            elif self.sequencer_link_mode == "NONE":
                scenes = []

        col, linked = core.create_and_link_shared_folder(self.name, scenes)
        col.color_tag = self.color
        core.set_active_shared_folder(context, col)

        self.report(
            {"INFO"},
            f"Shared folder '{self.name}' created and linked in {len(linked)} shot(s)",
        )

        if context.area.type == "SEQUENCE_EDITOR":
            context.area.tag_redraw()

        return {"FINISHED"}


class COLLECTION_OT_shared_folder_shots_link(bpy.types.Operator):
    bl_idname = "collection.shared_folder_shots_link"
    bl_label = "Link Shared Folder in Shots"
    bl_description = "Link a shared folder in active or selected shots"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared Folder")

    def execute(self, context: bpy.types.Context):
        scenes = get_active_or_selected_scenes(context)
        collection = bpy.data.collections[self.shared_folder_name]
        linked = core.link_shared_folder(collection, scenes)
        core.set_active_shared_folder(context, collection)

        self.report(
            {"INFO"},
            f"Linked shared folder '{self.shared_folder_name}' in {len(linked)} shot(s)",
        )

        if not linked:
            return {"CANCELLED"}

        return {"FINISHED"}


class COLLECTION_OT_shared_folder_shots_unlink(bpy.types.Operator):
    bl_idname = "collection.shared_folder_shots_unlink"
    bl_label = "Unlink Shared Folder from Shots"
    bl_description = "Unlink a shared folder from active or selected shots"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared Folder")

    def execute(self, context: bpy.types.Context):
        scenes = get_active_or_selected_scenes(context)
        collection = bpy.data.collections[self.shared_folder_name]
        unlinked = core.unlink_shared_folder(collection, scenes)
        core.set_active_shared_folder(context, collection)

        self.report(
            {"INFO"},
            f"Unlinked shared folder '{self.shared_folder_name}' from {len(unlinked)} shot(s)",
        )

        if not unlinked:
            return {"CANCELLED"}

        return {"FINISHED"}


class COLLECTION_OT_shared_folder_shots_select(bpy.types.Operator):
    bl_idname = "collection.shared_folder_shots_select"
    bl_label = "Select Shots by Shared Folder"
    bl_description = "Select shots that uses a shared folder"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared Folder")

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
    bl_label = "Delete Shared Folder"
    bl_description = "Delete a shared folder"
    bl_options = {"UNDO"}

    shared_folder_name: bpy.props.StringProperty(name="Shared Folder")

    def execute(self, context: bpy.types.Context):
        core.delete_shared_folder(bpy.data.collections[self.shared_folder_name])
        self.report({"INFO"}, f"Deleted shared folder '{self.shared_folder_name}'")

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
