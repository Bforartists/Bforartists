"""Drop-down menus for Anim Assist."""

from __future__ import annotations

import bpy
from bpy.types import Menu


class ANIMASSIST_MT_interpolation(Menu):
    bl_idname = "ANIMASSIST_MT_interpolation"
    bl_label = "Batch Interpolation"

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        for itype, label in (("CONSTANT", "Constant"), ("LINEAR", "Linear"), ("BEZIER", "Bezier")):
            op = layout.operator("animassist.batch_interpolation", text=label)
            op.interp_type = itype


class ANIMASSIST_MT_key_type(Menu):
    bl_idname = "ANIMASSIST_MT_key_type"
    bl_label = "Set Key Type"

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        for kt, label in (
            ("KEYFRAME", "Keyframe"),
            ("BREAKDOWN", "Breakdown"),
            ("MOVING_HOLD", "Moving Hold"),
            ("EXTREME", "Extreme"),
            ("JITTER", "Jitter"),
        ):
            op = layout.operator("animassist.set_key_type", text=label)
            op.key_type = kt


class ANIMASSIST_MT_select_key_type(Menu):
    bl_idname = "ANIMASSIST_MT_select_key_type"
    bl_label = "Select by Key Type"

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        for kt, label in (
            ("KEYFRAME", "Keyframe"),
            ("BREAKDOWN", "Breakdown"),
            ("MOVING_HOLD", "Moving Hold"),
            ("EXTREME", "Extreme"),
            ("JITTER", "Jitter"),
        ):
            op = layout.operator("animassist.select_by_key_type", text=label)
            op.key_type = kt
            op.deselect = False


class ANIMASSIST_MT_handle_type(Menu):
    bl_idname = "ANIMASSIST_MT_handle_type"
    bl_label = "Set Handle Type"

    def draw(self, _context: bpy.types.Context) -> None:
        layout = self.layout
        for ht, label in (
            ("AUTO_CLAMPED", "Auto Clamped"),
            ("AUTO", "Auto"),
            ("VECTOR", "Vector"),
            ("ALIGNED", "Aligned"),
            ("FREE", "Free"),
        ):
            op = layout.operator("animassist.set_handle_type", text=label)
            op.handle_type = ht


classes: list[type] = [
    ANIMASSIST_MT_interpolation,
    ANIMASSIST_MT_key_type,
    ANIMASSIST_MT_select_key_type,
    ANIMASSIST_MT_handle_type,
]