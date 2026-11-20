# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Outliner collection creation tests, run through ui_simulate/run.py."""

import modules.ui_test_utils as ui


def _setup(*, object_count=2, sync=False):
    import bpy

    bpy.ops.wm.read_homefile(use_empty=True)
    yield
    e, t, window = ui.test_window()
    scene = window.scene
    source = bpy.data.collections.new("Source")
    duplicate = bpy.data.collections.new("Other Membership")
    scene.collection.children.link(source)
    scene.collection.children.link(duplicate)
    for index in range(object_count):
        obj = bpy.data.objects.new("Object {:02d}".format(index), None)
        source.objects.link(obj)
        duplicate.objects.link(obj)

    area = ui.largest_area(window.screen)
    area.type = 'OUTLINER'
    area.spaces.active.display_mode = 'VIEW_LAYER'
    area.spaces.active.use_sync_select = sync
    yield
    return t, window, area, source, duplicate


def _create(area, t, *, select=True, **properties):
    import bpy

    region = next(region for region in area.regions if region.type == 'WINDOW')
    with bpy.context.temp_override(area=area, region=region):
        bpy.ops.outliner.select_all(action='SELECT' if select else 'DESELECT')
        selected = {item for item in bpy.context.selected_ids if isinstance(item, bpy.types.Object)}
        t.assertEqual(selected, set(bpy.context.scene.objects) if select else set())
        before = set(bpy.data.collections)
        t.assertEqual(bpy.ops.outliner.collection_new(**properties), {'FINISHED'})
        created = set(bpy.data.collections) - before
    t.assertEqual(len(created), 1)
    return created.pop()


def move_outliner_selection_without_viewport_sync():
    """Move each selected object once, including objects appearing in two collections."""
    t, window, area, source, duplicate = yield from _setup()
    objects = set(window.scene.objects)
    t.assertFalse(any(obj.select_get() for obj in objects))
    created = _create(area, t, move_selected=True)
    t.assertEqual(set(created.objects), objects)
    t.assertEqual(len(source.objects), 0)
    t.assertEqual(len(duplicate.objects), 0)
    t.assertEqual(window.view_layer.active_layer_collection.collection, created)
    for obj in objects:
        t.assertEqual(tuple(obj.users_collection), (created,))


def move_selection_with_viewport_sync():
    t, window, area, source, duplicate = yield from _setup(sync=True)
    objects = set(window.scene.objects)
    created = _create(area, t, move_selected=True)
    t.assertEqual(set(created.objects), objects)
    t.assertTrue(all(obj.select_get() for obj in objects))


def move_single_object():
    t, window, area, source, duplicate = yield from _setup(object_count=1)
    objects = set(window.scene.objects)
    created = _create(area, t, move_selected=True)
    t.assertEqual(set(created.objects), objects)


def no_outliner_selection_creates_empty_collection():
    t, window, area, source, duplicate = yield from _setup()
    objects = set(source.objects)
    created = _create(area, t, select=False, move_selected=True)
    t.assertEqual(len(created.objects), 0)
    t.assertEqual(set(source.objects), objects)
    t.assertEqual(set(duplicate.objects), objects)


def default_operator_keeps_selected_objects_in_place():
    """Without move_selected (shortcuts, plain menu entries, API calls) the collection stays empty."""
    t, window, area, source, duplicate = yield from _setup()
    objects = set(source.objects)
    created = _create(area, t)
    t.assertEqual(len(created.objects), 0)
    t.assertEqual(set(source.objects), objects)
    t.assertEqual(set(duplicate.objects), objects)


def nested_move_selection_stays_in_the_active_collection():
    """Nested with move_selected: the new collection is made inside the active one."""
    t, window, area, source, duplicate = yield from _setup()
    objects = set(window.scene.objects)
    layer_collection = window.view_layer.layer_collection.children[source.name]
    window.view_layer.active_layer_collection = layer_collection
    yield
    created = _create(area, t, nested=True, move_selected=True)
    t.assertIn(created, set(source.children))
    t.assertNotIn(created, set(window.scene.collection.children))
    t.assertEqual(set(created.objects), objects)
    for obj in objects:
        t.assertEqual(tuple(obj.users_collection), (created,))
