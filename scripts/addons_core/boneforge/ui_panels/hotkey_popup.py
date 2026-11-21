"""BoneCraft Phase 1 — Viewport Hotkey Pop-up Panel.

A floating pop-up that replicates the full collection panel (with
bookmarks) at the cursor position when a configurable hotkey is pressed
in the 3D viewport. Dismisses on click-away, Escape, or second press.

Default hotkey: Ctrl+Shift+R  (no Blender default conflict).
"""

import bpy
from bpy.types import Operator

from boneforge.i18n import T
from boneforge.core import (
    active_armature,
    addon_prefs,
    get_draw,
)


# ── Pop-up operator ─────────────────────────────────────────────

class BF_OT_RigPanelPopup(Operator):
    """Open the BoneCraft rig panel at the cursor"""
    bl_idname = "boneforge.rig_panel_popup"
    bl_label = "BoneCraft Rig Panel"
    bl_description = "Open the BoneCraft collection and bookmark panel as a pop-up at the cursor"
    bl_options = {'REGISTER'}

    def execute(self, context):
        return context.window_manager.invoke_popup(self, width=self._popup_width(context))

    def invoke(self, context, event):
        arm = active_armature(context)
        if arm is None:
            self.report({'INFO'}, "Select an armature to open the rig panel")
            return {'CANCELLED'}
        return context.window_manager.invoke_popup(self, width=self._popup_width(context))

    def draw(self, context):
        layout = self.layout

        arm = active_armature(context)
        if arm is None:
            layout.label(text=T("Select an armature to open the rig panel"),
                         icon='INFO')
            return

        # Bookmarks at top (fetched from registry, not a direct import)
        draw_bookmarks = get_draw("bookmarks")
        if draw_bookmarks is not None:
            box = layout.box()
            box.label(text=T("Bookmarks"))
            draw_bookmarks(box, context)
            layout.separator()

        # Full collection list (fetched from registry)
        draw_collection_list = get_draw("collection_list")
        if draw_collection_list is not None:
            draw_collection_list(layout, context)
        else:
            layout.label(text=T("Collection panel not loaded"), icon='INFO')

    @staticmethod
    def _popup_width(context):
        try:
            return addon_prefs(context).popup_width
        except (KeyError, AttributeError):
            return 300


# ── Keymap ──────────────────────────────────────────────────────

addon_keymaps = []


def _register_keymap():
    """Register the default hotkey: Ctrl+Shift+R in the 3D Viewport."""
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return

    km = kc.keymaps.new(
        name="3D View",
        space_type='VIEW_3D',
        region_type='WINDOW',
    )
    kmi = km.keymap_items.new(
        BF_OT_RigPanelPopup.bl_idname,
        type='R',
        value='PRESS',
        ctrl=True,
        shift=True,
    )
    kmi.active = True
    addon_keymaps.append((km, kmi))


def _unregister_keymap():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# ── Registration ────────────────────────────────────────────────

classes = (
    BF_OT_RigPanelPopup,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    _register_keymap()


def unregister():
    _unregister_keymap()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
