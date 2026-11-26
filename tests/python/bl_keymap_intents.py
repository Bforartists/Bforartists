# SPDX-FileCopyrightText: 2026 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

# ./blender.bin --background --factory-startup --python tests/python/bl_keymap_intents.py
#
# Preferences round trip (needs a scratch `BLENDER_USER_RESOURCES`, run without `--factory-startup`
# for the second step):
#   ./blender.bin --background --factory-startup --python tests/python/bl_keymap_intents.py -- --persist-save
#   ./blender.bin --background --python tests/python/bl_keymap_intents.py -- --persist-check

"""
Key map intents: a shortcut with a meaning ("G" is "Move") shared by key map items across key maps.

- Items referencing an intent take their key from it.
- Re-binding an intent re-binds every item bound through it.
- Editing the key of an item detaches it from its intent, restoring the item links it again.
- Exported key configurations store the intents table and load back with the links intact.
"""

__all__ = (
    "main",
)

import sys
import unittest

import bpy

INTENT = "move"
INTENT_KEY = 'G'
INTENT_KEY_NEW = 'W'
# Detached in the persistence test.
DETACH_KEYMAP = "Object Mode"
DETACH_KEY = 'Q'


def keyconfig_update():
    """
    Apply pending key configuration changes.
    Normally done from the event loop, which doesn't run in background mode.
    """
    wm = bpy.context.window_manager
    wm.keyconfigs.active = wm.keyconfigs.active


def items_with_intent(kc, idname):
    return [
        (km, kmi)
        for km in kc.keymaps
        for kmi in km.keymap_items
        if kmi.intent == idname
    ]


def item_key(kmi):
    return (kmi.type, kmi.value, kmi.shift, kmi.ctrl, kmi.alt, kmi.oskey, kmi.hyper, kmi.key_modifier)


class TestKeyMapIntents(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # The key configuration presets aren't loaded in background mode.
        bpy.utils.keyconfig_init()
        keyconfig_update()

    def setUp(self):
        self.wm = bpy.context.window_manager
        self.kc_user = self.wm.keyconfigs.user
        self.kc_active = self.wm.keyconfigs.active
        self.assertIn(INTENT, self.kc_user.intents)
        self.assertEqual(self.kc_user.intents[INTENT].type, INTENT_KEY)

    def tearDown(self):
        keyconfig_update()

    def test_default_intents(self):
        intent = self.kc_user.intents[INTENT]
        self.assertEqual(intent.label, "Move")
        self.assertEqual(intent.category, "Transform")
        self.assertEqual(intent.value, 'PRESS')
        # Every intent of the preset is categorized.
        for intent in self.kc_active.intents:
            self.assertTrue(intent.category, intent.name)
        self.assertFalse(intent.is_user_modified)
        self.assertFalse(intent.is_user_defined)
        # The preset defines the same intents.
        for intent in self.kc_active.intents:
            self.assertIn(intent.name, self.kc_user.intents)

    def test_items_resolved(self):
        intent = self.kc_user.intents[INTENT]
        served = items_with_intent(self.kc_user, INTENT)
        self.assertEqual(len(served), intent.contexts)
        # Serves many contexts (the point of an intent).
        self.assertGreaterEqual(len({km.name for km, _ in served}), 10)
        for km, kmi in served:
            with self.subTest(keymap=km.name, item=kmi.idname):
                self.assertEqual(item_key(kmi), item_key(intent))
                self.assertFalse(kmi.is_user_modified)

    def test_rebind(self):
        intent = self.kc_user.intents[INTENT]
        served_before = items_with_intent(self.kc_user, INTENT)

        intent.type = INTENT_KEY_NEW
        keyconfig_update()

        intent = self.kc_user.intents[INTENT]
        self.assertEqual(intent.type, INTENT_KEY_NEW)
        self.assertTrue(intent.is_user_modified)
        served = items_with_intent(self.kc_user, INTENT)
        self.assertEqual(len(served), len(served_before))
        for km, kmi in served:
            with self.subTest(keymap=km.name, item=kmi.idname):
                self.assertEqual(kmi.type, INTENT_KEY_NEW)
                # Following the intent is not a change to the item itself.
                self.assertFalse(kmi.is_user_modified)
        # The preset is not touched.
        self.assertEqual(self.kc_active.intents[INTENT].type, INTENT_KEY)
        # Other intents are untouched.
        self.assertEqual(self.kc_user.intents["rotate"].type, 'R')

        intent.restore_to_default()
        keyconfig_update()

        intent = self.kc_user.intents[INTENT]
        self.assertEqual(intent.type, INTENT_KEY)
        self.assertFalse(intent.is_user_modified)
        for km, kmi in items_with_intent(self.kc_user, INTENT):
            self.assertEqual(kmi.type, INTENT_KEY)

    def test_detach_and_restore(self):
        km = self.kc_user.keymaps[DETACH_KEYMAP]
        kmi = next(kmi for kmi in km.keymap_items if kmi.intent == INTENT)
        kmi_id = kmi.id
        count_before = len(items_with_intent(self.kc_user, INTENT))

        # Editing the key of an item detaches it.
        kmi.type = DETACH_KEY
        self.assertEqual(kmi.intent, "")
        keyconfig_update()

        km = self.kc_user.keymaps[DETACH_KEYMAP]
        kmi = km.keymap_items.from_id(kmi_id)
        self.assertEqual(kmi.intent, "")
        self.assertEqual(kmi.type, DETACH_KEY)
        self.assertTrue(kmi.is_user_modified)
        # Detaching one item leaves the others linked.
        self.assertEqual(len(items_with_intent(self.kc_user, INTENT)), count_before - 1)

        # Re-binding the intent doesn't touch the detached item.
        self.kc_user.intents[INTENT].type = INTENT_KEY_NEW
        keyconfig_update()
        kmi = self.kc_user.keymaps[DETACH_KEYMAP].keymap_items.from_id(kmi_id)
        self.assertEqual(kmi.type, DETACH_KEY)
        self.kc_user.intents[INTENT].restore_to_default()
        keyconfig_update()

        # Restoring the item links it again.
        km = self.kc_user.keymaps[DETACH_KEYMAP]
        kmi = km.keymap_items.from_id(kmi_id)
        km.restore_item_to_default(kmi)
        keyconfig_update()
        kmi = self.kc_user.keymaps[DETACH_KEYMAP].keymap_items.from_id(kmi_id)
        self.assertEqual(kmi.intent, INTENT)
        self.assertEqual(kmi.type, INTENT_KEY)
        self.assertFalse(kmi.is_user_modified)
        self.assertEqual(len(items_with_intent(self.kc_user, INTENT)), count_before)

    def test_link_item(self):
        km = self.kc_user.keymaps[DETACH_KEYMAP]
        kmi = km.keymap_items.new("wm.search_menu", 'F3', 'PRESS', shift=1)
        kmi_id = kmi.id
        # Linking takes the key from the intent on the next update.
        kmi.intent = INTENT
        keyconfig_update()

        km = self.kc_user.keymaps[DETACH_KEYMAP]
        kmi = km.keymap_items.from_id(kmi_id)
        self.assertIsNotNone(kmi)
        self.assertEqual(kmi.intent, INTENT)
        self.assertEqual(item_key(kmi), item_key(self.kc_user.intents[INTENT]))

        # And follows the intent.
        self.kc_user.intents[INTENT].type = INTENT_KEY_NEW
        keyconfig_update()
        kmi = self.kc_user.keymaps[DETACH_KEYMAP].keymap_items.from_id(kmi_id)
        self.assertEqual(kmi.type, INTENT_KEY_NEW)

        self.kc_user.intents[INTENT].restore_to_default()
        km = self.kc_user.keymaps[DETACH_KEYMAP]
        km.keymap_items.remove(km.keymap_items.from_id(kmi_id))
        keyconfig_update()
        self.assertIsNone(self.kc_user.keymaps[DETACH_KEYMAP].keymap_items.from_id(kmi_id))

    def test_export_import(self):
        import os
        import tempfile
        from bl_keymap_utils.io import keyconfig_export_as_data

        # Export a re-bound intent, so the table carries a non-default key.
        self.kc_user.intents[INTENT].type = INTENT_KEY_NEW
        keyconfig_update()
        # Names only, the items are rebuilt by later updates.
        served_before = sorted((km.name, kmi.idname) for km, kmi in items_with_intent(self.kc_user, INTENT))

        with tempfile.TemporaryDirectory() as dir_temp:
            filepath = os.path.join(dir_temp, "intents_test.py")
            keyconfig_export_as_data(self.wm, self.kc_active, filepath, all_keymaps=True)
            with open(filepath, "r", encoding="utf-8") as fh:
                source = fh.read()
            self.assertIn("keyconfig_intents", source)
            self.assertIn("\"intent\": '%s'" % INTENT, source)

            self.kc_user.intents[INTENT].restore_to_default()
            keyconfig_update()

            # Run the file the way `bpy.utils.keyconfig_set` does, without activating it.
            exec(compile(source, filepath, "exec"), {"__name__": "__main__", "__file__": filepath})

        kc = self.wm.keyconfigs["intents_test"]
        try:
            self.assertIn(INTENT, kc.intents)
            intent = kc.intents[INTENT]
            self.assertEqual(intent.label, "Move")
            self.assertEqual(intent.category, "Transform")
            self.assertEqual(intent.type, INTENT_KEY_NEW)
            served = items_with_intent(kc, INTENT)
            self.assertEqual(sorted((km.name, kmi.idname) for km, kmi in served), served_before)
            for km, kmi in served:
                self.assertEqual(kmi.type, INTENT_KEY_NEW)
        finally:
            self.wm.keyconfigs.remove(kc)


# -----------------------------------------------------------------------------
# Preferences Round Trip

def persist_save():
    bpy.utils.keyconfig_init()
    keyconfig_update()
    kc_user = bpy.context.window_manager.keyconfigs.user

    kc_user.intents[INTENT].type = INTENT_KEY_NEW
    km = kc_user.keymaps[DETACH_KEYMAP]
    kmi = next(kmi for kmi in km.keymap_items if kmi.intent == INTENT)
    kmi.type = DETACH_KEY
    assert kmi.intent == ""
    keyconfig_update()

    bpy.ops.wm.save_userpref()
    print("Saved preferences with intent {!r} on {!r} and one item detached".format(INTENT, INTENT_KEY_NEW))


def persist_check():
    bpy.utils.keyconfig_init()
    keyconfig_update()
    kc_user = bpy.context.window_manager.keyconfigs.user

    intent = kc_user.intents[INTENT]
    assert intent.type == INTENT_KEY_NEW, intent.type
    assert intent.is_user_modified
    served = items_with_intent(kc_user, INTENT)
    assert served
    for km, kmi in served:
        assert kmi.type == INTENT_KEY_NEW, (km.name, kmi.idname, kmi.type)

    km = kc_user.keymaps[DETACH_KEYMAP]
    detached = [kmi for kmi in km.keymap_items if kmi.type == DETACH_KEY and kmi.is_user_modified]
    assert len(detached) == 1, [kmi.idname for kmi in detached]
    assert detached[0].intent == ""
    assert not any(kmi.intent == INTENT and kmi.type != INTENT_KEY_NEW for kmi in km.keymap_items)

    # Restoring the intent through the preferences works after a restart too.
    intent.restore_to_default()
    keyconfig_update()
    assert kc_user.intents[INTENT].type == INTENT_KEY
    for km, kmi in items_with_intent(kc_user, INTENT):
        assert kmi.type == INTENT_KEY, (km.name, kmi.idname, kmi.type)
    print("Preferences round trip OK: {:d} items follow intent {!r}".format(len(served), INTENT))


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--persist-save" in argv:
        persist_save()
    elif "--persist-check" in argv:
        persist_check()
    else:
        unittest.main(argv=[__file__] + argv)


if __name__ == "__main__":
    main()
