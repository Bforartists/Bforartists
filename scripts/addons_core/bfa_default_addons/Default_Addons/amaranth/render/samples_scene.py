# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Cycles: Samples per Scene

When working in production, it's often more convenient to do lighting and
compositing in different scenes (so you can later append the comp scene
    to bring together nodes, settings, lamps, RenderLayers).

This would lead to work with more than one scene. When doing render tests
you want to know at a glance how many samples the other scenes have,
without manually switching. This is the idea behind the feature.

Find it on the Sampling panel, on Render properties.
Developed during Caminandes Open Movie Project
"""

import bpy
from amaranth import utils
from bpy.props import BoolProperty


class CYCLES_RENDER_PT_amaranth_samples(bpy.types.Panel):
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    bl_label = "Samples per View Layer"
    bl_parent_id = "CYCLES_RENDER_PT_sampling"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'CYCLES'}

    @classmethod
    def poll(cls, context):
        return (
            utils.cycles_exists() and
            context.engine in cls.COMPAT_ENGINES and
            (len(context.scene.render.views) > 1) or (len(bpy.data.scenes) > 1)
        )

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        render = scene.render
        cscene = scene.cycles

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()

        if len(scene.render.views) == 1 and render.view_layers[0].samples == 0:
            pass
        else:
            for viewlayer in scene.view_layers:
                row = col.row(align=True)
                row.alignment = "RIGHT"
                row.label(text=viewlayer.name, icon="BLANK1")

                sub = row.row(align=True)
                sub.prop(viewlayer, "samples", text="")
                sub.active = viewlayer.samples > 0

        col = layout.column()

        if (len(bpy.data.scenes) > 1):
            col.separator()

            col.label(text="Other Scenes")

            if utils.cycles_exists():
                for s in bpy.data.scenes:
                    if s != scene:
                        row = col.row(align=True)
                        if s.render.engine == "CYCLES":
                            cscene = s.cycles

                            row = col.row(align=True)
                            row.alignment = "RIGHT"
                            row.label(text=s.name, icon="BLANK1")

                            sub = row.row(align=True)
                            sub.prop(cscene, "samples", text="")
                        else:
                            row.label(
                                text="Scene: '%s' is not using Cycles" %
                                s.name)
            else:
                for s in bpy.data.scenes:
                    if s != scene:
                        row = col.row(align=True)
                        if s.render.engine == "CYCLES":
                            cscene = s.cycles

                            row.label(text=s.name, icon="BLANK1")
                            row.prop(cscene, "aa_samples",
                                     text="AA Samples")
                        else:
                            row.label(
                                text="Scene: '%s' is not using Cycles" %
                                s.name)


def init():
    if utils.cycles_exists():
        from cycles import properties as _cycles_props
        _cycles_props.CyclesRenderSettings.use_samples_final = BoolProperty(
            name="Use Final Render Samples",
            description="Use current shader samples as final render samples",
            default=False,
        )


def clear():
    wm = bpy.context.window_manager
    for p in ("amarath_cycles_list_sampling", "use_samples_final"):
        if p in wm:
            del wm[p]


def register():
    init()
    if utils.cycles_exists():
        bpy.utils.register_class(CYCLES_RENDER_PT_amaranth_samples)


def unregister():
    if utils.cycles_exists():
        panel = CYCLES_RENDER_PT_amaranth_samples
        if "bl_rna" in panel.__dict__:
            bpy.utils.unregister_class(panel)

    clear()
