#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
"""
Remember Layers for Render
If you're doing lighting/rendering tasks, you'll probably have a bunch of
layers that you want/need to be enabled for final renders.

When tweaking lighting, or if somebody else has to open the file to check
something, you/they are likely to tweak the layers visibility and forget
which ones were needed for the render to look good.

In the Render Layers properties, you'll now find a "Save Current Layers for
Render" button, this will save the currently visible scene layers as those
that should be enabled for render. You can adjust this further by clicking
on the slots on the right.

Now all you need to do before saving your file for rendering is press the
"View Layers for Render". Find it on the Render Layers properties.
"""

import bpy
from bpy.types import Operator
from bpy.props import (
        BoolProperty,
        IntProperty,
        )


# FEATURE: Set Layers to Render
class AMTH_SCENE_OT_layers_render_save(Operator):
    """Save the current scene layers as those that should be enabled for final renders"""
    bl_idname = "scene.amaranth_layers_render_save"
    bl_label = "Save as Layers for Render"

    def execute(self, context):
        which = []
        n = -1

        for l in context.scene.layers:
            n += 1
            if l:
                which.append(n)

        context.scene["amth_layers_for_render"] = which
        self.report({"INFO"}, "Layers for Render Saved")

        return {"FINISHED"}


class AMTH_SCENE_OT_layers_render_view(Operator):
    """Enable the scene layers that should be active for final renders"""
    bl_idname = "scene.amaranth_layers_render_view"
    bl_label = "View Layers for Render"

    def execute(self, context):
        scene = context.scene
        layers_render = scene["amth_layers_for_render"]

        for window in bpy.context.window_manager.windows:
            screen = window.screen

            for area in screen.areas:
                if area.type == "VIEW_3D":
                    override = {
                        "window": window,
                        "screen": screen,
                        "scene": scene,
                        "area": area,
                        "region": area.regions[4],
                        "blend_data": context.blend_data}

                    if layers_render:
                        bpy.ops.view3d.layers(
                            override,
                            nr=layers_render[0] + 1,
                            extend=False,
                            toggle=False)

                        for n in layers_render:
                            context.scene.layers[n] = True
                    else:
                        bpy.ops.view3d.layers(
                            override,
                            nr=1,
                            extend=False,
                            toggle=False)
                        self.report({"INFO"}, "No layers set for render")

                    break

        return {"FINISHED"}


class AMTH_SCENE_OT_layers_render_set_individual(Operator):
    """Whether this layer should be enabled or not for final renders"""
    bl_idname = "scene.amaranth_layers_render_set_individual"
    bl_label = "Set This Layer for Render"

    toggle = BoolProperty()
    number = IntProperty()

    def execute(self, context):
        number = self.number

        new_layers = []

        for la in context.scene["amth_layers_for_render"]:
            new_layers.append(la)

        if len(context.scene["amth_layers_for_render"]) and number in new_layers:
            new_layers.remove(number)
        else:
            new_layers.append(number)

        # Remove Duplicates
        new_layers = list(set(new_layers))
        context.scene["amth_layers_for_render"] = new_layers

        bpy.ops.scene.amaranth_layers_render_view()

        return {"FINISHED"}


class AMTH_SCENE_OT_layers_render_clear(Operator):
    """Clear layers for render"""
    bl_idname = "scene.amaranth_layers_render_clear"
    bl_label = "Clear Layers for Render"

    def execute(self, context):

        if context.scene.get("amth_layers_for_render"):
            context.scene["amth_layers_for_render"] = []

        return {"FINISHED"}


def ui_layers_for_render(self, context):
    get_addon = "amaranth" in context.user_preferences.addons.keys()
    if not get_addon:
        return

    if context.user_preferences.addons["amaranth"].preferences.use_layers_for_render:
        lfr_available = context.scene.get("amth_layers_for_render")
        if lfr_available:
            lfr = context.scene["amth_layers_for_render"]

        layout = self.layout
        layout.label("Layers for Rendering:")
        split = layout.split()
        col = split.column(align=True)
        row = col.row(align=True)
        row.operator(
            AMTH_SCENE_OT_layers_render_save.bl_idname,
            text="Replace Layers" if lfr_available else "Save Current Layers for Render",
            icon="FILE_REFRESH" if lfr_available else "LAYER_USED")

        if lfr_available:
            row.operator(
                AMTH_SCENE_OT_layers_render_clear.bl_idname,
                icon="X", text="")
            col = col.column(align=True)
            col.enabled = True if lfr_available else False
            col.operator(
                AMTH_SCENE_OT_layers_render_view.bl_idname,
                icon="RESTRICT_VIEW_OFF")

            split = split.split()
            col = split.column(align=True)
            row = col.row(align=True)

            for n in range(0, 5):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname,
                    text="",
                    icon="LAYER_ACTIVE" if n in lfr else "BLANK1").number = n
            row = col.row(align=True)
            for n in range(10, 15):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname,
                    text="",
                    icon="LAYER_ACTIVE" if n in lfr else "BLANK1").number = n

            split = split.split()
            col = split.column(align=True)
            row = col.row(align=True)

            for n in range(5, 10):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname,
                    text="",
                    icon="LAYER_ACTIVE" if n in lfr else "BLANK1").number = n
            row = col.row(align=True)
            for n in range(15, 20):
                row.operator(
                    AMTH_SCENE_OT_layers_render_set_individual.bl_idname,
                    text="",
                    icon="LAYER_ACTIVE" if n in lfr else "BLANK1").number = n


def ui_layers_for_render_header(self, context):
    get_addon = "amaranth" in context.user_preferences.addons.keys()
    if not get_addon:
        return

    if context.user_preferences.addons["amaranth"].preferences.use_layers_for_render:
        if context.scene.get("amth_layers_for_render"):
            self.layout.operator(
                AMTH_SCENE_OT_layers_render_view.bl_idname,
                text="", icon="IMGDISPLAY")

# // FEATURE: Set Layers to Render


def register():
    bpy.utils.register_class(AMTH_SCENE_OT_layers_render_clear)
    bpy.utils.register_class(AMTH_SCENE_OT_layers_render_save)
    bpy.utils.register_class(AMTH_SCENE_OT_layers_render_set_individual)
    bpy.utils.register_class(AMTH_SCENE_OT_layers_render_view)
    bpy.types.VIEW3D_HT_header.append(ui_layers_for_render_header)
    bpy.types.RENDERLAYER_PT_layers.append(ui_layers_for_render)


def unregister():
    bpy.utils.unregister_class(AMTH_SCENE_OT_layers_render_clear)
    bpy.utils.unregister_class(AMTH_SCENE_OT_layers_render_save)
    bpy.utils.unregister_class(AMTH_SCENE_OT_layers_render_set_individual)
    bpy.utils.unregister_class(AMTH_SCENE_OT_layers_render_view)
    bpy.types.VIEW3D_HT_header.remove(ui_layers_for_render_header)
    bpy.types.RENDERLAYER_PT_layers.remove(ui_layers_for_render)
