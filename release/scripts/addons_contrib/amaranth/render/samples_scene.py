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


class AMTH_RENDER_OT_cycles_samples_percentage_set(bpy.types.Operator):

    """Save the current number of samples per shader as final (gets saved in .blend)"""
    bl_idname = "scene.amaranth_cycles_samples_percentage_set"
    bl_label = "Set as Render Samples"

    def execute(self, context):
        cycles = context.scene.cycles
        cycles.use_samples_final = True

        context.scene["amth_cycles_samples_final"] = [
            cycles.diffuse_samples,
            cycles.glossy_samples,
            cycles.transmission_samples,
            cycles.ao_samples,
            cycles.mesh_light_samples,
            cycles.subsurface_samples,
            cycles.volume_samples]

        self.report({"INFO"}, "Render Samples Saved")

        return {"FINISHED"}


class AMTH_RENDER_OT_cycles_samples_percentage(bpy.types.Operator):

    """Set a percentage of the final render samples"""
    bl_idname = "scene.amaranth_cycles_samples_percentage"
    bl_label = "Set Render Samples Percentage"

    percent: IntProperty(
            name="Percentage",
            description="Percentage to divide render samples by",
            subtype="PERCENTAGE", default=0
            )

    def execute(self, context):
        percent = self.percent
        cycles = context.scene.cycles
        cycles_samples_final = context.scene["amth_cycles_samples_final"]

        cycles.use_samples_final = False

        if percent == 100:
            cycles.use_samples_final = True

        cycles.diffuse_samples = int((cycles_samples_final[0] / 100) * percent)
        cycles.glossy_samples = int((cycles_samples_final[1] / 100) * percent)
        cycles.transmission_samples = int(
            (cycles_samples_final[2] / 100) * percent)
        cycles.ao_samples = int((cycles_samples_final[3] / 100) * percent)
        cycles.mesh_light_samples = int(
            (cycles_samples_final[4] / 100) * percent)
        cycles.subsurface_samples = int(
            (cycles_samples_final[5] / 100) * percent)
        cycles.volume_samples = int((cycles_samples_final[6] / 100) * percent)

        return {"FINISHED"}


def render_cycles_scene_samples(self, context):

    layout = self.layout
    scene = context.scene
    render = scene.render
    if utils.cycles_exists():
        cscene = scene.cycles
        list_sampling = scene.amaranth_cycles_list_sampling

    # Set Render Samples
    if utils.cycles_exists() and cscene.progressive == "BRANCHED_PATH":
        layout.separator()
        split = layout.split()
        col = split.column()

        col.operator(
            AMTH_RENDER_OT_cycles_samples_percentage_set.bl_idname,
            text="%s" %
            "Set as Render Samples" if cscene.use_samples_final else "Set New Render Samples",
            icon="%s" %
            "PINNED" if cscene.use_samples_final else "UNPINNED")

        col = split.column()
        row = col.row(align=True)
        row.enabled = True if scene.get("amth_cycles_samples_final") else False

        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="100%").percent = 100
        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="75%").percent = 75
        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="50%").percent = 50
        row.operator(
            AMTH_RENDER_OT_cycles_samples_percentage.bl_idname,
            text="25%").percent = 25

    # List Samples
    if (len(scene.render.layers) > 1) or (len(bpy.data.scenes) > 1):

        box = layout.box()
        row = box.row(align=True)
        col = row.column(align=True)

        row = col.row(align=True)
        row.alignment = "LEFT"
        row.prop(scene, "amaranth_cycles_list_sampling",
                 icon="%s" % "TRIA_DOWN" if list_sampling else "TRIA_RIGHT",
                 emboss=False)

    if list_sampling:
        if len(scene.render.layers) == 1 and render.layers[0].samples == 0:
            pass
        else:
            col.separator()
            col.label(text="RenderLayers:", icon="RENDERLAYERS")

            for rl in scene.render.layers:
                row = col.row(align=True)
                row.label(text=rl.name, icon="BLANK1")
                row.prop(
                    rl, "samples", text="%s" %
                    "Samples" if rl.samples > 0 else "Automatic (%s)" %
                    (cscene.aa_samples if cscene.progressive == "BRANCHED_PATH" else cscene.samples))

        if (len(bpy.data.scenes) > 1):
            col.separator()

            col.label(text="Scenes:", icon="SCENE_DATA")

            if utils.cycles_exists() and cscene.progressive == "PATH":
                for s in bpy.data.scenes:
                    if s != scene:
                        row = col.row(align=True)
                        if s.render.engine == "CYCLES":
                            cscene = s.cycles

                            row.label(s.name)
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
        # Note: add versioning code to adress changes introduced in 2.79.1
        if bpy.app.version >= (2, 79, 1):
            from cycles import properties as _cycles_props
            _cycles_props.CyclesRenderSettings.use_samples_final = BoolProperty(
                    name="Use Final Render Samples",
                    description="Use current shader samples as final render samples",
                    default=False
                    )
        else:
            bpy.types.CyclesRenderSettings.use_samples_final = BoolProperty(
                    name="Use Final Render Samples",
                    description="Use current shader samples as final render samples",
                    default=False
                    )



def clear():
    wm = bpy.context.window_manager
    for p in ("amarath_cycles_list_sampling", "use_samples_final"):
        if p in wm:
            del wm[p]


def register():
    init()
    bpy.utils.register_class(AMTH_RENDER_OT_cycles_samples_percentage)
    bpy.utils.register_class(AMTH_RENDER_OT_cycles_samples_percentage_set)
    if utils.cycles_exists():
        if bpy.app.version >= (2, 79, 1):
            bpy.types.CYCLES_RENDER_PT_sampling.append(render_cycles_scene_samples)
        else:
            bpy.types.CyclesRender_PT_sampling.append(render_cycles_scene_samples)


def unregister():
    bpy.utils.unregister_class(AMTH_RENDER_OT_cycles_samples_percentage)
    bpy.utils.unregister_class(AMTH_RENDER_OT_cycles_samples_percentage_set)
    if utils.cycles_exists():
        if bpy.app.version >= (2, 79, 1):
            bpy.types.CYCLES_RENDER_PT_sampling.remove(render_cycles_scene_samples)
        else:
            bpy.types.CyclesRender_PT_sampling.remove(render_cycles_scene_samples)


    clear()
