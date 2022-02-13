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
from bpy.props import (
        BoolProperty,
        IntProperty,
        )


def render_cycles_scene_samples(self, context):

    layout = self.layout
    scene = context.scene
    render = scene.render
    if utils.cycles_exists():
        cscene = scene.cycles
        list_sampling = scene.amaranth_cycles_list_sampling

    # List Samples
    #if (len(scene.render.layers) > 1) or (len(bpy.data.scenes) > 1):
    if (len(scene.render.views) > 1) or (len(bpy.data.scenes) > 1):

        box = layout.box()
        row = box.row(align=True)
        col = row.column(align=True)

        row = col.row(align=True)
        row.alignment = "LEFT"
        row.prop(scene, "amaranth_cycles_list_sampling",
                 icon="%s" % "TRIA_DOWN" if list_sampling else "TRIA_RIGHT",
                 emboss=False)

    if list_sampling:
        #if len(scene.render.layers) == 1 and render.layers[0].samples == 0:
        if len(scene.render.views) == 1 and render.view_layers[0].samples == 0:
            pass
        else:
            col.separator()
            #col.label(text="RenderLayers:", icon="RENDERLAYERS")
            col.label(text="View Layers:", icon="RENDERLAYERS")

            #for rl in scene.render.layers:
            for rl in scene.view_layers:
                row = col.row(align=True)
                row.label(text=rl.name, icon="BLANK1")
                row.prop(
                    rl, "samples", text="%s" %
                    "Samples" if rl.samples > 0 else "Automatic (%s)" %
                    cscene.samples)

        if (len(bpy.data.scenes) > 1):
            col.separator()

            col.label(text="Scenes:", icon="SCENE_DATA")

            if utils.cycles_exists():
                for s in bpy.data.scenes:
                    if s != scene:
                        row = col.row(align=True)
                        if s.render.engine == "CYCLES":
                            cscene = s.cycles

                            #row.label(s.name)
                            row.label(text=s.name)
                            row.prop(cscene, "samples", icon="BLANK1")
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
    scene = bpy.types.Scene
    if utils.cycles_exists():
        scene.amaranth_cycles_list_sampling = bpy.props.BoolProperty(
            default=False,
            name="Samples Per:")
        # Note: add versioning code to address changes introduced in 2.79.1
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
        bpy.types.CYCLES_RENDER_PT_sampling.append(render_cycles_scene_samples)


def unregister():
    if utils.cycles_exists():
        bpy.types.CYCLES_RENDER_PT_sampling.remove(render_cycles_scene_samples)


    clear()
