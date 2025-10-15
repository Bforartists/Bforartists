# SPDX-License-Identifier: GPL-3.0-or-later
# Thanks to Znight and Spa Studios for the work of making this real

from typing import Callable

import bpy

from bfa_3Dsequencer.preferences import get_addon_prefs
from bfa_3Dsequencer.sync.core import (
    get_sync_settings,
    remap_frame_value,
)

# Data structure to map source-to-duplicated datablock
DuplicationManifest = dict[bpy.types.ID, bpy.types.ID]


def duplicate_object(
    obj: bpy.types.Object,
    parent_col: bpy.types.Collection,
    manifest: DuplicationManifest,
) -> bpy.types.Object:
    """Duplicate `obj` and link it to `parent_col`.

    :param obj: The object to duplicate
    :param parent_col: The collection to link the duplicated object into
    :param manifest: Source to duplicated datablocks
    :return: The newly created object
    """

    def duplicate_datablock(datablock: bpy.types.ID):
        """
        Duplicate `datablock`, register in manifest and return the copy if `datablock`
        is valid, None otherwise.
        """
        if not datablock:
            return None

        db = datablock.copy()
        manifest[datablock] = db
        return db

    def duplicate_anim_data(datablock: bpy.types.ID):
        """
        Duplicate `datablock`'s anim data (action), register in manifest and return the
        copy if `datablock` is valid, None otherwise.
        """
        if datablock and datablock.animation_data and datablock.animation_data.action:
            action = duplicate_datablock(datablock.animation_data.action)
            datablock.animation_data.action = action
            return action
        return None

    # Copy the object and duplicate attached datablocks
    new_obj = duplicate_datablock(obj)
    new_obj.data = duplicate_datablock(new_obj.data)

    duplicate_anim_data(new_obj)
    duplicate_anim_data(new_obj.data)

    parent_col.objects.link(new_obj)

    return new_obj


def duplicate_objects(
    objs: list[bpy.types.Object],
    parent_col: bpy.types.Collection,
    manifest: DuplicationManifest,
):
    """Duplicate all objects in `objs` and link them to `parent_col`.

    :param obj: The objects to duplicate
    :param parent_col: The collection to link the duplicated object into
    :param manifest: Source to duplicated datablocks
    :return: The newly created objects
    """
    new_objs = []
    for obj in objs:
        new_obj = duplicate_object(obj, parent_col, manifest)
        new_objs.append(new_obj)
    return new_objs


def duplicate_collection(
    col: bpy.types.Collection,
    parent_col: bpy.types.Collection,
    manifest: DuplicationManifest,
) -> bpy.types.Collection:
    """
    Duplicate the collection `col` and link it to `parent_col`.
    If `col` has more than 1 user, only link it to `parent_col`.

    :param col: The collection to duplicate
    :param parent_col: The collection to link the duplicated collection into
    :param manifest: Source to duplicated datablocks
    :return: The newly created collection
    """
    # Only link collection with multiple users
    if col.users > 1:
        parent_col.children.link(col)
        return col

    # Create new collection
    new_col = bpy.data.collections.new(col.name)
    manifest[col] = new_col

    # Duplicate source objects into this new collection
    duplicate_objects(col.objects, new_col, manifest)
    # Duplicate children collection
    duplicate_collections(col.children, new_col, manifest)
    # Link the new collection to the specified parent
    parent_col.children.link(new_col)

    return new_col


def duplicate_collections(
    cols: list[bpy.types.Collection],
    parent_col: bpy.types.Collection,
    manifest: DuplicationManifest,
) -> list[bpy.types.Collection]:
    """Duplicate the collections `cols` and link them to `parent_col`.

    :param cols: The collections to duplicate
    :param parent_col: The collection to link the duplicated collections into
    :param manifest: Source to duplicated datablocks
    :return: The newly created collections
    """
    new_cols = []
    for col in cols:
        new_col = duplicate_collection(col, parent_col, manifest)
        new_cols.append(new_col)
    return new_cols


def is_local_single_user(datablock: bpy.types.ID):
    """Returns whether `datablock` is a local, single_user datablock."""
    return datablock and datablock.users == 1 and not datablock.library


def replace_in_datablock_name(
    datablock: bpy.types.ID,
    old_substr: str,
    new_substr: str,
    preprocess: Callable[[str], str] = lambda x: x,
):
    """
    Replace occurrences of substring `old_substr` by `new_substr` in `datablock`'s name.

    :param old_substr: The substring to replace
    :param new_substr: The new substring to use
    :param datablocks: The datablocks to modify
    :param preprocess: Pre-process function to apply if datablock contains `old_substr` in its name
    """
    # Discard datablocks that are not local single-users ones
    if not is_local_single_user(datablock):
        return

    if old_substr in datablock.name:
        datablock.name = preprocess(datablock.name).replace(old_substr, new_substr)


def remap_relations(manifest: DuplicationManifest):
    """Remap relations for duplicated datablocks.

    :param manifest: The duplication manifest holding source to duplicated datablocks.
    """

    def _reparent(src_object: bpy.types.Object, new_object: bpy.types.Object) -> bool:
        """
        Remap the parent of `new_object` to the duplicate of `src_object`'s parent if any.

        :param src_object: The source object.
        :param new_object: The duplicate of `src_object`.
        :return: Whether `new_object` has been reparented.
        """
        # Find the duplicate of source object's parent, return if not in the manifest.
        new_parent = manifest.get(src_object.parent, None)
        if not new_parent:
            return False

        # Parent the new object to its rightful owner.
        new_object.parent = new_parent
        # Assigning parent may update parent inverse matrix; restore it afterwards.
        new_object.matrix_parent_inverse = src_datablock.matrix_parent_inverse.copy()
        return True

    def _get_pointer_properties(datablock: bpy.types.ID) -> list[str]:
        """Get the names of pointer properties in `datablock`."""
        return [
            prop.identifier
            for prop in datablock.bl_rna.properties
            if isinstance(prop, bpy.types.PointerProperty)
        ]

    def _remap_pointer_properties(datablocks: list[bpy.types.ID]):
        """
        Remap all pointer properties of `datablocks` referencing a duplicated datablock.
        """
        for datablock in datablocks:
            for prop_name in _get_pointer_properties(datablock):
                if (value := getattr(datablock, prop_name)) in manifest:
                    setattr(datablock, prop_name, manifest[value])

    def _remap_constraints(new_object: bpy.types.Object):
        """Remap `new_object`'s constraints properties."""
        _remap_pointer_properties(new_object.constraints)

    def _remap_modifiers(new_object: bpy.types.Object):
        """Remap `new_object`'s modifiers properties."""
        _remap_pointer_properties(new_object.modifiers)
        if isinstance(new_object.data, bpy.types.GreasePencil):
            _remap_pointer_properties(new_object.grease_pencil_modifiers)
            _remap_pointer_properties(new_object.shader_effects)

    def _remap_drivers(new_datablock: bpy.types.ID):
        """Remap `new_datablock`'s drivers targets."""
        if not (anim_data := getattr(new_datablock, "animation_data", None)):
            return
        # Iterate over drivers and remap targets if applicable
        for fcurve in anim_data.drivers:
            for var in fcurve.driver.variables:
                for target in var.targets:
                    if target.id in manifest:
                        target.id = manifest[target.id]

    # Remap relationships and references to datablocks in duplicated elements
    for src_datablock, new_datablock in manifest.items():
        if isinstance(src_datablock, bpy.types.Object):
            _reparent(src_datablock, new_datablock)
            _remap_constraints(new_datablock)
            _remap_modifiers(new_datablock)
        # Remap animation drivers targets
        _remap_drivers(new_datablock)


def duplicate_scene(
    context: bpy.types.Context,
    scene: bpy.types.Scene,
    name: str,
    manifest: DuplicationManifest = None,
) -> bpy.types.Scene:
    """Duplicates `scene` as a new scene named `name`.

    :param context: The context
    :param scene: The Scene to duplicate
    :param name: The name of the new scene
    :param manifest: The duplication manifest mapping source-to-duplicated datablocks
    :returns: The new created scene
    """
    if name in bpy.data.scenes:
        raise ValueError(f"Scene '{scene}' already exists")

    # Creating a new empty scene leads to no camera being available.
    # This makes all 3D viewports switch to user perspective mode.
    # To avoid such changes in the UI and restore them properly,
    # save 3D views view_perspective modes before the operation.
    region3D_view_mode: dict[bpy.types.RegionView3D, str] = {}
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            region = area.spaces.active.region_3d
            region3D_view_mode[region] = region.view_perspective

    # Create a new scene based on the source scene's settings
    # Note: context override is not enough here - we need to make the scene to duplicate
    #       the active scene, as the operator uses that internally.
    initial_window_scene = context.window.scene
    context.window.scene = scene
    bpy.ops.scene.new(type="EMPTY")
    # This operator makes the newly created scene active
    new_scene = context.window.scene

    if manifest is None:
        manifest = DuplicationManifest()

    # Add the scene to the manifest
    manifest[scene] = new_scene

    # Duplicate scene's root collections and objects
    duplicate_collections(
        scene.collection.children, new_scene.collection, manifest=manifest
    )
    duplicate_objects(scene.collection.objects, new_scene.collection, manifest=manifest)

    # Preprocess: remap relationships between duplicated objects
    remap_relations(manifest)

    # Set new scene's properties based on source scene:
    # - Camera
    new_scene.camera = manifest.get(scene.camera)
    # - Active object
    new_scene.view_layers[0].objects.active = manifest.get(
        scene.view_layers[0].objects.active
    )
    # - World (link to the same world object)
    new_scene.world = scene.world

    # Rename the duplicated datablocks and the scene itself
    # Note: Specify to remove any Blender-automatic-numbering-suffix
    #       from datablocks that are impacted by the renaming.
    for datablock in manifest.values():
        replace_in_datablock_name(
            datablock,
            scene.name,
            name,
            preprocess=lambda x: x.rsplit(".", 1)[0],
        )

    new_scene.name = name

    # Restore active window to initial scene
    context.window.scene = initial_window_scene

    # Restore 3D views perspective mode
    for region3D, view_mode in region3D_view_mode.items():
        region3D.view_perspective = view_mode

    return new_scene


def rename_all_datablocks_from_collection(
    col: bpy.types.Collection, old_substr: str, new_substr: str
):
    """Recursively rename all local single-users datablocks starting from `col`,
    by replacing occurences of `old_substr` by `new_substr`.

    :param col: The root collection to start the renaming from
    :param old_substr: the substring to replace
    :param new_substr: the new substring to use
    """
    # Rename the collection itself
    replace_in_datablock_name(col, old_substr, new_substr)

    # Rename collection content
    for obj in col.objects:
        # Rename object, data and any attached action
        for datablock in (obj, obj.data):
            if not datablock:
                continue
            replace_in_datablock_name(datablock, old_substr, new_substr)
            if datablock.animation_data and datablock.animation_data.action:
                replace_in_datablock_name(
                    datablock.animation_data.action, old_substr, new_substr
                )

    # Recursively rename children collections
    for child_col in col.children:
        rename_all_datablocks_from_collection(child_col, old_substr, new_substr)


def rename_scene(scene: bpy.types.Scene, new_name: str):
    """Rename `scene` to `new_name` and replace occurences of `scene`'s original name
    by `new_name` in all local single-user datablocks within it.

    :param scene: The scene to rename
    :param new_name: The new name of the scene
    """
    # Early return if the scene is already name correctly
    if scene.name == new_name:
        return
    # Avoid clashing names if a scene is already named `new_name`
    if new_name in bpy.data.scenes:
        raise ValueError(f"Scene '{new_name}' already exists")

    # Rename scene content
    rename_all_datablocks_from_collection(scene.collection, scene.name, new_name)
    # Rename the scene itself
    scene.name = scene.name.replace(scene.name, new_name)


def is_orphan(datablock: bpy.types.ID) -> bool:
    """Return whether `datablock` is orphan, using advanced orphan detection."""
    # In some cases, datablock.users is set to 1 while not being used (update issue?).
    # Use 'bpy.data.user_map' to define whether this datablock is actually orphan.
    if datablock.users == 1:
        user_map = bpy.data.user_map(subset=[datablock])[datablock]
        # Exlude direct children from this result, since they are listed in
        # the returned set but should not be considered as users here.
        advanced_user_count = len(
            [db for db in user_map if getattr(db, "parent", None) != datablock]
        )
        return advanced_user_count == 0
    # Otherwise, datablock.users can be used safely to detect orphans
    return datablock.users == 0


def delete_datablock_if_orphan(datablock: bpy.types.ID) -> int:
    """
    Generic function to delete `datablock` if local and orphan, as well as its
    attached datablocks (children, data, animation action), recursively.

    :param datablock: The datablock to delete
    :returns: The total number of datablocks deleted by this operation
    """
    # Do not try to delete linked or non orphan datablocks
    if datablock.library or not is_orphan(datablock):
        return 0

    # Get and copy children list if any
    children = getattr(datablock, "children", [])[:]
    # Get data if any
    data = getattr(datablock, "data", None)
    # Get action if any
    action = getattr(getattr(datablock, "animation_data", None), "action", None)

    # Remove the datablock
    bpy.data.batch_remove([datablock])
    del_count = 1

    # Recursively clean up related datablocks:
    # - children (applicable for: objects, collections)
    for c in children:
        del_count += delete_datablock_if_orphan(c)
    # - data (applicable for: objects)
    if data:
        del_count += delete_datablock_if_orphan(data)
    # - action (applicable for: objects, data)
    if action:
        del_count += delete_datablock_if_orphan(action)

    return del_count


def delete_scene(scene: bpy.types.Scene, purge_orphan_datablocks: bool) -> int:
    """
    Delete `scene` and optionally delete datablock that were only used in this context.

    :param scene: The scene to delete
    :param purge_orphan_datablocks: Whether to delete orphan datablocks after scene deletion
    :returns: The number of datablocks deleted by this operation
    """
    potentially_orphan_datablocks: list[bpy.types.ID] = []

    if purge_orphan_datablocks:
        # Store top-level datablocks linked to this scene before its deletion.
        # We want to delete datablocks in a hierarchical way for user counts to be
        # relevant for detecting orphans.
        # Collections containing collections and objects, they should be deleted first.
        potentially_orphan_datablocks += scene.collection.children[:]
        # Then, all objects without parents should be considered.
        potentially_orphan_datablocks += [
            obj for obj in scene.collection.all_objects if not obj.parent
        ]

    # Delete the scene
    bpy.data.scenes.remove(scene)

    del_count = 1

    if purge_orphan_datablocks:
        # Datablocks are deleted from top to bottom recursively, dealing with
        # all collections first, and hierarchies of objects afterwards.
        for datablock in potentially_orphan_datablocks:
            del_count += delete_datablock_if_orphan(datablock)

    return del_count


def reload_strip(strip: bpy.types.Strip):
    """Re-evaluate content length and update `strip` display in the sequencer."""
    # For the strip to re-evaluate its internal scene duration, we need
    # to call the sequencer.reload operator, which runs on selected strips.
    # Adjust sequence editor selection for this to work properly.
    scene = strip.id_data
    # Store sequence editor selection
    selected_strips = [
        (s, s.select_left_handle, s.select_right_handle)
        for s in scene.sequence_editor.strips
        if s.select
    ]

    with bpy.context.temp_override(scene=scene):
        # Deselect everything but our strip
        bpy.ops.sequencer.select_all(action="DESELECT")
        strip.select = True
        # Force re-evaluation of strip scene's internal range and update strip display
        bpy.ops.sequencer.reload()
        # Restore sequence editor selection
        bpy.ops.sequencer.select_all(action="DESELECT")
        for strip, left, right in selected_strips:
            strip.select = True
            strip.select_left_handle = left
            strip.select_right_handle = right


def adapt_scene_range(strip: bpy.types.SceneStrip):
    """Ensure `strip`'s internel range is fully contained in the scene its using."""
    # Update internal scene's end frame if exceeding the original one
    new_frame_end = remap_frame_value(strip.frame_final_end - 1, strip)
    if new_frame_end <= strip.scene.frame_end:
        return

    strip.scene.frame_end = new_frame_end
    reload_strip(strip)


def adjust_shot_duration(
    strip: bpy.types.SceneStrip,
    frame_offset: int,
    from_frame_start: bool = False,
) -> bool:
    """
    Adjust the duration of `strip` and its underlying scene by offsetting either its end
    or start frame (`from_frame_start` set to True) by `frame_offset`.
    All strips on the same channel after `strip` are shifted accordingly.

    Note that `frame_offset` is automatically clamped to:
    - ensure a minimum strip duration of 1
    - from frame start: stay in strip's scene range

    :param strip: The strip to adjust the duration of.
    :param frame_offset: The frame offset to apply.
    :param from_frame_start: Whether to offset shot's inner start frame rather than its end frame.
    :return: Whether the function modified the duration of `strip`.
    """
    if not strip.scene:
        raise ValueError(f"Invalid shot: no scene set for '{strip.name}'")

    # Ensure the scene lasts at least 1 frame and compute effective offset
    new_duration = max(strip.frame_final_duration + frame_offset, 1)
    new_frame_offset = new_duration - strip.frame_final_duration

    # If adjusting from strip's frame start, clamp offset to never go beyond internal
    # scene's frame start.
    if from_frame_start:
        new_start_frame = max(
            remap_frame_value(strip.frame_final_start, strip) - new_frame_offset,
            strip.scene.frame_start,
        )
        new_frame_offset = new_start_frame - remap_frame_value(
            strip.frame_final_start, strip
        )

    if new_frame_offset == 0:
        return False

    # Get sequence editor and scene from strip
    sed_scene: bpy.types.Scene = strip.id_data
    sed: bpy.types.SequenceEditor = sed_scene.sequence_editor

    # Identify the other strips that must be shifted to adjust to this duration change
    impacted_strips = sorted(
        (
            s
            for s in sed.strips
            if s.frame_final_start > strip.frame_final_start
            and s.channel == strip.channel
        ),
        key=lambda s: s.frame_final_start,
    )
    # Shift all impacted strips by offset.
    # Note: we adjust order of execution based on offset's sign to avoid
    #       overlaps at all time and strips automatically changing channels.

    # Frame start: shift content by offset value and change duration while maintaining
    #              strip's frame final start.
    if from_frame_start:
        # Positive offset: increase frame start => decrease strip duration
        if new_frame_offset > 0:
            # 1. Adjust strip values
            strip.frame_offset_start += new_frame_offset
            strip.frame_start -= new_frame_offset
            # 2. Move impacted strips to the left
            for s in impacted_strips:
                s.frame_start -= new_frame_offset
        # Negative offset: decrease frame start => increase strip duration
        else:
            # 1. Move impacted strips to the right (reversed order)
            for s in reversed(impacted_strips):
                s.frame_start -= new_frame_offset
            # 2. Adjust strip values
            strip.frame_start -= new_frame_offset
            strip.frame_offset_start += new_frame_offset

    # Frame end: shift scene and strip's final frame by offset.
    else:
        # Positive offset: increase frame end => increase duration
        if new_frame_offset > 0:
            # 1. Move impacted strips to the right (reversed order)
            for s in reversed(impacted_strips):
                s.frame_start += new_frame_offset
            # 2. Adjust strip's duration
            strip.frame_final_end += new_frame_offset
        # Negative offset: decrease frame end => decrease duration
        else:
            # 1. Adjust strip's duration
            strip.frame_final_duration += new_frame_offset
            # 2. Move impacted strips to the left
            for s in impacted_strips:
                s.frame_start += new_frame_offset

    adapt_scene_range(strip)
    return True


def slip_shot_content(
    strip: bpy.types.SceneStrip, frame_offset: int, clamp_start: bool = False
):
    """
    Slip `strip` content by `frame_offset`.
    A positive offset moves strip's internal range forwards.

    :param strip: The scene strip to consider.
    :param frame_offset: The frame offset to apply.
    :param clamp_start: Whether to clamp to scene's frame start.
    """
    if clamp_start:
        # Clamp offset to never go beyond internal scene's frame start.
        new_start_frame = max(
            remap_frame_value(strip.frame_final_start, strip) + frame_offset,
            strip.scene.frame_start,
        )

        new_frame_offset = new_start_frame - remap_frame_value(
            strip.frame_final_start, strip
        )

    else:
        new_frame_offset = frame_offset

    # Store external values
    frame_final_duration = strip.frame_final_duration
    channel = strip.channel
    # Offset internal values to perform a content slip
    strip.frame_offset_start += new_frame_offset
    strip.frame_start -= new_frame_offset
    strip.frame_offset_end -= new_frame_offset
    # Ensure channel and duration are preserved
    strip.channel = channel
    strip.frame_final_duration = frame_final_duration
    adapt_scene_range(strip)


def get_valid_shot_scenes() -> list[bpy.types.Scene]:
    """Return the list of scenes considered as usable by a scene strip."""
    prefs = get_addon_prefs()
    return [
        scene
        for scene in bpy.data.scenes
        if (
            # Discard template scenes.
            not scene.name.startswith(prefs.shot_template_prefix)
            # Discard master sync scene.
            and scene != get_sync_settings().master_scene
            # Discard empty scenes.
            and len(scene.collection.all_objects)
        )
    ]


def get_scene_cameras(scene: bpy.types.Scene) -> list[bpy.types.Object]:
    """Return the list of cameras available in `scene`."""
    return sorted(
        (obj for obj in scene.objects if obj.type == "CAMERA"),
        key=lambda x: x.name,
    )


def register():
    pass


def unregister():
    pass
