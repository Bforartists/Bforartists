# SPDX-FileCopyrightText: 2025 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
This file does not run anything, its methods are accessed for tests by ``run_blender_setup.py``.

Does not thoroughly test the quick effects themselves (as in, testing that they apply the right
settings), it just tests that adding them works and doesn't crash when done through the UI. This
tends to break, indicating regressions elsewhere.
"""
import modules.ui_test_utils as ui


def add_quick_fur():
    import bpy

    e, t, window = ui.test_window()

    object = bpy.context.object
    # Just a pre-condition
    t.assertIsNotNone(object)

    yield from ui.call_operator(e, "Quick Fur")

    curves_object = bpy.context.object
    t.assertIsNotNone(curves_object)
    t.assertEqual(curves_object.type, 'CURVES')
    # Multiple modifiers are added and reordered then. Just make sure there's at least one nodes
    # modifier.
    t.assertEqual(curves_object.modifiers[0].type, 'NODES')


def add_quick_smoke():
    import bpy

    if not bpy.app.build_options.fluid:
        print("Fluid is not enabled, skipping quick smoke test")

    e, t, window = ui.test_window()

    object = bpy.context.object
    # Just a pre-condition
    t.assertIsNotNone(object)

    yield from ui.call_operator(e, "Quick Smoke")
    t.assertEqual(object.modifiers[0].type, 'FLUID')
    t.assertEqual(object.modifiers[0].fluid_type, 'FLOW')
    t.assertEqual(object.modifiers[0].flow_settings.flow_type, 'SMOKE')


def add_quick_liquid():
    import bpy

    if not bpy.app.build_options.fluid:
        print("Fluid is not enabled, skipping quick liquid test")

    e, t, window = ui.test_window()

    object = bpy.context.object
    # Just a pre-condition
    t.assertIsNotNone(object)

    yield from ui.call_operator(e, "Quick Liquid")
    t.assertEqual(object.modifiers[0].type, 'FLUID')
    t.assertEqual(object.modifiers[0].flow_settings.flow_type, 'LIQUID')


def add_quick_explode():
    import bpy

    e, t, window = ui.test_window()

    object = bpy.context.object
    # Just a pre-condition
    t.assertIsNotNone(object)

    yield from ui.call_operator(e, "Quick Explode")
    t.assertEqual(object.modifiers[0].type, 'PARTICLE_SYSTEM')
    t.assertEqual(object.modifiers[1].type, 'EXPLODE')

    # Just start and stop the animation.
    yield from ui.call_operator(e, "Play Animation")
    yield from ui.call_operator(e, "Play Animation")
