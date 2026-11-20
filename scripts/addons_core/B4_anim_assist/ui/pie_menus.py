"""Pie menus for rapid tool access + keymaps."""

from __future__ import annotations

import bpy
from bpy.types import Menu

_addon_keymaps: list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]] = []


class ANIMASSIST_MT_pie_curve_tools(Menu):
    bl_idname = "ANIMASSIST_MT_pie_curve_tools"
    bl_label = "Anim Assist"

    def draw(self, _context: bpy.types.Context) -> None:
        pie = self.layout.menu_pie()
        # Cardinal directions first (W, E, S, N), then diagonals (NW, NE, SW, SE)
        pie.operator("animassist.blend_neighbor", text="Blend Neighbor", icon="TRACKING_FORWARDS_SINGLE")
        pie.operator("animassist.ease_to_ease", text="Ease To Ease", icon="IPO_EASE_IN_OUT")
        pie.operator("animassist.blend_frame", text="Blend Frame", icon="IPO_BEZIER")
        pie.operator("animassist.blend_offset", text="Blend Offset", icon="ARROW_LEFTRIGHT")
        pie.operator("animassist.push_pull", text="Push / Pull", icon="FULLSCREEN_EXIT")
        pie.operator("animassist.smooth_keys", text="Smooth Keys", icon="SMOOTHCURVE")
        pie.operator("animassist.anim_offset", text="Anim Offset", icon="ANIM")
        pie.separator()  # 8th slot empty


class ANIMASSIST_MT_pie_key_types(Menu):
    bl_idname = "ANIMASSIST_MT_pie_key_types"
    bl_label = "Key Types"

    def draw(self, _context: bpy.types.Context) -> None:
        pie = self.layout.menu_pie()
        for kt, label in (
            ("KEYFRAME", "Keyframe"),
            ("BREAKDOWN", "Breakdown"),
            ("MOVING_HOLD", "Moving Hold"),
            ("EXTREME", "Extreme"),
            ("JITTER", "Jitter"),
        ):
            op = pie.operator("animassist.set_key_type", text=label)
            op.key_type = kt


def register_keymaps() -> None:
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is None:
        return

    # Graph Editor: Ctrl+Shift+D
    km = kc.keymaps.new(name="Graph Editor", space_type="GRAPH_EDITOR")
    kmi = km.keymap_items.new("wm.call_menu_pie", "D", "PRESS", ctrl=True, shift=True)
    kmi.properties.name = ANIMASSIST_MT_pie_curve_tools.bl_idname
    _addon_keymaps.append((km, kmi))

    # Dope Sheet: Ctrl+Shift+K
    km = kc.keymaps.new(name="Dopesheet", space_type="DOPESHEET_EDITOR")
    kmi = km.keymap_items.new("wm.call_menu_pie", "K", "PRESS", ctrl=True, shift=True)
    kmi.properties.name = ANIMASSIST_MT_pie_key_types.bl_idname
    _addon_keymaps.append((km, kmi))


def unregister_keymaps() -> None:
    for km, kmi in _addon_keymaps:
        km.keymap_items.remove(kmi)
    _addon_keymaps.clear()


classes: list[type] = [
    ANIMASSIST_MT_pie_curve_tools,
    ANIMASSIST_MT_pie_key_types,
]