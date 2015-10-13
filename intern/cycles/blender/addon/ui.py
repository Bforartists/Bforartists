#
# Copyright 2011-2013 Blender Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# <pep8 compliant>

import bpy

from bpy.types import (
        Panel,
        Menu,
        Operator,
        )


class CYCLES_MT_sampling_presets(Menu):
    bl_label = "Sampling Presets"
    preset_subdir = "cycles/sampling"
    preset_operator = "script.execute_preset"
    COMPAT_ENGINES = {'CYCLES'}
    draw = Menu.draw_preset


class CYCLES_MT_integrator_presets(Menu):
    bl_label = "Integrator Presets"
    preset_subdir = "cycles/integrator"
    preset_operator = "script.execute_preset"
    COMPAT_ENGINES = {'CYCLES'}
    draw = Menu.draw_preset


class CyclesButtonsPanel:
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    COMPAT_ENGINES = {'CYCLES'}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine in cls.COMPAT_ENGINES


def use_cpu(context):
    cscene = context.scene.cycles
    device_type = context.user_preferences.system.compute_device_type

    return (device_type == 'NONE' or cscene.device == 'CPU')


def use_branched_path(context):
    cscene = context.scene.cycles
    device_type = context.user_preferences.system.compute_device_type

    return (cscene.progressive == 'BRANCHED_PATH' and device_type != 'OPENCL')


def draw_samples_info(layout, context):
    cscene = context.scene.cycles
    integrator = cscene.progressive

    # Calculate sample values
    if integrator == 'PATH':
        aa = cscene.samples
        if cscene.use_square_samples:
            aa = aa * aa
    else:
        aa = cscene.aa_samples
        d = cscene.diffuse_samples
        g = cscene.glossy_samples
        t = cscene.transmission_samples
        ao = cscene.ao_samples
        ml = cscene.mesh_light_samples
        sss = cscene.subsurface_samples
        vol = cscene.volume_samples

        if cscene.use_square_samples:
            aa = aa * aa
            d = d * d
            g = g * g
            t = t * t
            ao = ao * ao
            ml = ml * ml
            sss = sss * sss
            vol = vol * vol

    # Draw interface
    # Do not draw for progressive, when Square Samples are disabled
    if use_branched_path(context) or (cscene.use_square_samples and integrator == 'PATH'):
        col = layout.column(align=True)
        col.scale_y = 0.6
        col.label("Total Samples:")
        col.separator()
        if integrator == 'PATH':
            col.label("%s AA" % aa)
        else:
            col.label("%s AA, %s Diffuse, %s Glossy, %s Transmission" %
                      (aa, d * aa, g * aa, t * aa))
            col.separator()
            col.label("%s AO, %s Mesh Light, %s Subsurface, %s Volume" %
                      (ao * aa, ml * aa, sss * aa, vol * aa))


class CyclesRender_PT_sampling(CyclesButtonsPanel, Panel):
    bl_label = "Sampling"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles
        device_type = context.user_preferences.system.compute_device_type

        row = layout.row(align=True)
        row.menu("CYCLES_MT_sampling_presets", text=bpy.types.CYCLES_MT_sampling_presets.bl_label)
        row.operator("render.cycles_sampling_preset_add", text="", icon="ZOOMIN")
        row.operator("render.cycles_sampling_preset_add", text="", icon="ZOOMOUT").remove_active = True

        row = layout.row()
        sub = row.row()
        sub.active = device_type != 'OPENCL'
        sub.prop(cscene, "progressive", text="")
        row.prop(cscene, "use_square_samples")

        split = layout.split()

        col = split.column()
        sub = col.column(align=True)
        sub.label("Settings:")

        seed_sub = sub.row(align=True)
        seed_sub.prop(cscene, "seed")
        seed_sub.prop(cscene, "use_animated_seed", text="", icon="TIME")

        sub.prop(cscene, "sample_clamp_direct")
        sub.prop(cscene, "sample_clamp_indirect")

        if cscene.progressive == 'PATH' or use_branched_path(context) == False:
            col = split.column()
            sub = col.column(align=True)
            sub.label(text="Samples:")
            sub.prop(cscene, "samples", text="Render")
            sub.prop(cscene, "preview_samples", text="Preview")
        else:
            sub.label(text="AA Samples:")
            sub.prop(cscene, "aa_samples", text="Render")
            sub.prop(cscene, "preview_aa_samples", text="Preview")
            sub.separator()
            sub.prop(cscene, "sample_all_lights_direct")
            sub.prop(cscene, "sample_all_lights_indirect")

            col = split.column()
            sub = col.column(align=True)
            sub.label(text="Samples:")
            sub.prop(cscene, "diffuse_samples", text="Diffuse")
            sub.prop(cscene, "glossy_samples", text="Glossy")
            sub.prop(cscene, "transmission_samples", text="Transmission")
            sub.prop(cscene, "ao_samples", text="AO")
            sub.prop(cscene, "mesh_light_samples", text="Mesh Light")
            sub.prop(cscene, "subsurface_samples", text="Subsurface")
            sub.prop(cscene, "volume_samples", text="Volume")

        if use_cpu(context) or cscene.feature_set == 'EXPERIMENTAL':
            layout.row().prop(cscene, "sampling_pattern", text="Pattern")

        for rl in scene.render.layers:
            if rl.samples > 0:
                layout.separator()
                layout.row().prop(cscene, "use_layer_samples")
                break

        draw_samples_info(layout, context)


class CyclesRender_PT_volume_sampling(CyclesButtonsPanel, Panel):
    bl_label = "Volume Sampling"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles

        row = layout.row()
        row.label("Heterogeneous:")
        row = layout.row()
        row.prop(cscene, "volume_step_size")
        row.prop(cscene, "volume_max_steps")


class CyclesRender_PT_light_paths(CyclesButtonsPanel, Panel):
    bl_label = "Light Paths"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles

        row = layout.row(align=True)
        row.menu("CYCLES_MT_integrator_presets", text=bpy.types.CYCLES_MT_integrator_presets.bl_label)
        row.operator("render.cycles_integrator_preset_add", text="", icon="ZOOMIN")
        row.operator("render.cycles_integrator_preset_add", text="", icon="ZOOMOUT").remove_active = True

        split = layout.split()

        col = split.column()

        sub = col.column(align=True)
        sub.label("Transparency:")
        sub.prop(cscene, "transparent_max_bounces", text="Max")
        sub.prop(cscene, "transparent_min_bounces", text="Min")
        sub.prop(cscene, "use_transparent_shadows", text="Shadows")

        col.separator()

        col.prop(cscene, "caustics_reflective")
        col.prop(cscene, "caustics_refractive")
        col.prop(cscene, "blur_glossy")

        col = split.column()

        sub = col.column(align=True)
        sub.label(text="Bounces:")
        sub.prop(cscene, "max_bounces", text="Max")
        sub.prop(cscene, "min_bounces", text="Min")

        sub = col.column(align=True)
        sub.prop(cscene, "diffuse_bounces", text="Diffuse")
        sub.prop(cscene, "glossy_bounces", text="Glossy")
        sub.prop(cscene, "transmission_bounces", text="Transmission")
        sub.prop(cscene, "volume_bounces", text="Volume")


class CyclesRender_PT_motion_blur(CyclesButtonsPanel, Panel):
    bl_label = "Motion Blur"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        rd = context.scene.render

        self.layout.prop(rd, "use_motion_blur", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles
        rd = scene.render
        layout.active = rd.use_motion_blur

        col = layout.column()
        col.prop(cscene, "motion_blur_position", text="Position")
        col.prop(rd, "motion_blur_shutter")


class CyclesRender_PT_film(CyclesButtonsPanel, Panel):
    bl_label = "Film"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles

        split = layout.split()

        col = split.column()
        col.prop(cscene, "film_exposure")
        col.prop(cscene, "film_transparent")

        col = split.column()
        sub = col.column(align=True)
        sub.prop(cscene, "filter_type", text="")
        if cscene.filter_type != 'BOX':
            sub.prop(cscene, "filter_width", text="Width")


class CyclesRender_PT_performance(CyclesButtonsPanel, Panel):
    bl_label = "Performance"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        cscene = scene.cycles

        split = layout.split()

        col = split.column(align=True)

        col.label(text="Threads:")
        col.row(align=True).prop(rd, "threads_mode", expand=True)
        sub = col.column(align=True)
        sub.enabled = rd.threads_mode == 'FIXED'
        sub.prop(rd, "threads")

        sub = col.column(align=True)
        sub.label(text="Tiles:")
        sub.prop(cscene, "tile_order", text="")

        sub.prop(rd, "tile_x", text="X")
        sub.prop(rd, "tile_y", text="Y")

        sub.prop(cscene, "use_progressive_refine")

        subsub = sub.column(align=True)
        subsub.enabled = not rd.use_border
        subsub.prop(rd, "use_save_buffers")

        col = split.column(align=True)

        col.label(text="Viewport:")
        col.prop(cscene, "debug_bvh_type", text="")
        col.separator()
        col.prop(cscene, "preview_start_resolution")

        col.separator()

        col.label(text="Final Render:")
        col.prop(rd, "use_persistent_data", text="Persistent Images")

        col.separator()

        col.label(text="Acceleration structure:")
        col.prop(cscene, "debug_use_spatial_splits")


class CyclesRender_PT_layer_options(CyclesButtonsPanel, Panel):
    bl_label = "Layer"
    bl_context = "render_layer"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        rl = rd.layers.active

        split = layout.split()

        col = split.column()
        col.prop(scene, "layers", text="Scene")
        col.prop(rl, "layers_exclude", text="Exclude")

        col = split.column()
        col.prop(rl, "layers", text="Layer")
        col.prop(rl, "layers_zmask", text="Mask Layer")

        split = layout.split()

        col = split.column()
        col.label(text="Material:")
        col.prop(rl, "material_override", text="")
        col.separator()
        col.prop(rl, "samples")

        col = split.column()
        col.prop(rl, "use_sky", "Use Environment")
        col.prop(rl, "use_solid", "Use Surfaces")
        col.prop(rl, "use_strand", "Use Hair")


class CyclesRender_PT_layer_passes(CyclesButtonsPanel, Panel):
    bl_label = "Passes"
    bl_context = "render_layer"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        rl = rd.layers.active

        split = layout.split()

        col = split.column()
        col.prop(rl, "use_pass_combined")
        col.prop(rl, "use_pass_z")
        col.prop(rl, "use_pass_mist")
        col.prop(rl, "use_pass_normal")
        col.prop(rl, "use_pass_vector")
        col.prop(rl, "use_pass_uv")
        col.prop(rl, "use_pass_object_index")
        col.prop(rl, "use_pass_material_index")
        col.separator()
        col.prop(rl, "use_pass_shadow")
        col.prop(rl, "use_pass_ambient_occlusion")
        col.separator()
        col.prop(rl, "pass_alpha_threshold")

        col = split.column()
        col.label(text="Diffuse:")
        row = col.row(align=True)
        row.prop(rl, "use_pass_diffuse_direct", text="Direct", toggle=True)
        row.prop(rl, "use_pass_diffuse_indirect", text="Indirect", toggle=True)
        row.prop(rl, "use_pass_diffuse_color", text="Color", toggle=True)
        col.label(text="Glossy:")
        row = col.row(align=True)
        row.prop(rl, "use_pass_glossy_direct", text="Direct", toggle=True)
        row.prop(rl, "use_pass_glossy_indirect", text="Indirect", toggle=True)
        row.prop(rl, "use_pass_glossy_color", text="Color", toggle=True)
        col.label(text="Transmission:")
        row = col.row(align=True)
        row.prop(rl, "use_pass_transmission_direct", text="Direct", toggle=True)
        row.prop(rl, "use_pass_transmission_indirect", text="Indirect", toggle=True)
        row.prop(rl, "use_pass_transmission_color", text="Color", toggle=True)
        col.label(text="Subsurface:")
        row = col.row(align=True)
        row.prop(rl, "use_pass_subsurface_direct", text="Direct", toggle=True)
        row.prop(rl, "use_pass_subsurface_indirect", text="Indirect", toggle=True)
        row.prop(rl, "use_pass_subsurface_color", text="Color", toggle=True)

        col.separator()
        col.prop(rl, "use_pass_emit", text="Emission")
        col.prop(rl, "use_pass_environment")

        if hasattr(rd, "debug_pass_type"):
            layout.prop(rd, "debug_pass_type")


class CyclesRender_PT_views(CyclesButtonsPanel, Panel):
    bl_label = "Views"
    bl_context = "render_layer"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        rd = context.scene.render
        self.layout.prop(rd, "use_multiview", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        rv = rd.views.active

        layout.active = rd.use_multiview
        basic_stereo = (rd.views_format == 'STEREO_3D')

        row = layout.row()
        row.prop(rd, "views_format", expand=True)

        if basic_stereo:
            row = layout.row()
            row.template_list("RENDERLAYER_UL_renderviews", "name", rd, "stereo_views", rd.views, "active_index", rows=2)

            row = layout.row()
            row.label(text="File Suffix:")
            row.prop(rv, "file_suffix", text="")

        else:
            row = layout.row()
            row.template_list("RENDERLAYER_UL_renderviews", "name", rd, "views", rd.views, "active_index", rows=2)

            col = row.column(align=True)
            col.operator("scene.render_view_add", icon='ZOOMIN', text="")
            col.operator("scene.render_view_remove", icon='ZOOMOUT', text="")

            row = layout.row()
            row.label(text="Camera Suffix:")
            row.prop(rv, "camera_suffix", text="")


class Cycles_PT_post_processing(CyclesButtonsPanel, Panel):
    bl_label = "Post Processing"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        split = layout.split()

        col = split.column()
        col.prop(rd, "use_compositing")
        col.prop(rd, "use_sequencer")

        col = split.column()
        col.prop(rd, "dither_intensity", text="Dither", slider=True)


class CyclesCamera_PT_dof(CyclesButtonsPanel, Panel):
    bl_label = "Depth of Field"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.camera and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        cam = context.camera
        ccam = cam.cycles
        dof_options = cam.gpu_dof

        split = layout.split()

        col = split.column()
        col.label("Focus:")
        col.prop(cam, "dof_object", text="")

        sub = col.row()
        sub.active = cam.dof_object is None
        sub.prop(cam, "dof_distance", text="Distance")

        hq_support = dof_options.is_hq_supported
        sub = col.column(align=True)
        sub.label("Viewport:")
        subhq = sub.column()
        subhq.active = hq_support
        subhq.prop(dof_options, "use_high_quality")
        sub.prop(dof_options, "fstop")
        if dof_options.use_high_quality and hq_support:
            sub.prop(dof_options, "blades")

        col = split.column()

        col.label("Aperture:")
        sub = col.column(align=True)
        sub.prop(ccam, "aperture_type", text="")
        if ccam.aperture_type == 'RADIUS':
            sub.prop(ccam, "aperture_size", text="Size")
        elif ccam.aperture_type == 'FSTOP':
            sub.prop(ccam, "aperture_fstop", text="Number")

        sub = col.column(align=True)
        sub.prop(ccam, "aperture_blades", text="Blades")
        sub.prop(ccam, "aperture_rotation", text="Rotation")
        sub.prop(ccam, "aperture_ratio", text="Ratio")


class Cycles_PT_context_material(CyclesButtonsPanel, Panel):
    bl_label = ""
    bl_context = "material"
    bl_options = {'HIDE_HEADER'}

    @classmethod
    def poll(cls, context):
        return (context.material or context.object) and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        ob = context.object
        slot = context.material_slot
        space = context.space_data
        is_sortable = len(ob.material_slots) > 1

        if ob:
            rows = 1
            if (is_sortable):
                rows = 4

            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=rows)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ZOOMIN', text="")
            col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")

            col.menu("MATERIAL_MT_specials", icon='DOWNARROW_HLT', text="")

            if is_sortable:
                col.separator()

                col.operator("object.material_slot_move", icon='TRIA_UP', text="").direction = 'UP'
                col.operator("object.material_slot_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

            if ob.mode == 'EDIT':
                row = layout.row(align=True)
                row.operator("object.material_slot_assign", text="Assign")
                row.operator("object.material_slot_select", text="Select")
                row.operator("object.material_slot_deselect", text="Deselect")

        split = layout.split(percentage=0.65)

        if ob:
            split.template_ID(ob, "active_material", new="material.new")
            row = split.row()

            if slot:
                row.prop(slot, "link", text="")
            else:
                row.label()
        elif mat:
            split.template_ID(space, "pin_id")
            split.separator()


class Cycles_PT_mesh_displacement(CyclesButtonsPanel, Panel):
    bl_label = "Displacement"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        if CyclesButtonsPanel.poll(context):
            if context.mesh or context.curve or context.meta_ball:
                if context.scene.cycles.feature_set == 'EXPERIMENTAL':
                    return True

        return False

    def draw(self, context):
        layout = self.layout

        mesh = context.mesh
        curve = context.curve
        mball = context.meta_ball

        if mesh:
            cdata = mesh.cycles
        elif curve:
            cdata = curve.cycles
        elif mball:
            cdata = mball.cycles

        layout.prop(cdata, "displacement_method", text="Method")
        layout.prop(cdata, "use_subdivision")
        layout.prop(cdata, "dicing_rate")


class CyclesObject_PT_motion_blur(CyclesButtonsPanel, Panel):
    bl_label = "Motion Blur"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        if CyclesButtonsPanel.poll(context) and ob:
            if ob.type in {'MESH', 'CURVE', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                return True
            if ob.dupli_type == 'GROUP' and ob.dupli_group:
                return True
            # TODO(sergey): More duplicator types here?
        return False

    def draw_header(self, context):
        layout = self.layout

        rd = context.scene.render
        # scene = context.scene

        layout.active = rd.use_motion_blur

        ob = context.object
        cob = ob.cycles

        layout.prop(cob, "use_motion_blur", text="")

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render
        # scene = context.scene

        ob = context.object
        cob = ob.cycles

        layout.active = (rd.use_motion_blur and cob.use_motion_blur)

        row = layout.row()
        row.prop(cob, "use_deform_motion", text="Deformation")

        sub = row.row()
        sub.active = cob.use_deform_motion
        sub.prop(cob, "motion_steps", text="Steps")


class CyclesObject_PT_cycles_settings(CyclesButtonsPanel, Panel):
    bl_label = "Cycles Settings"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return (CyclesButtonsPanel.poll(context) and
                ob and ((ob.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META', 'LAMP'}) or
                        (ob.dupli_type == 'GROUP' and ob.dupli_group)))

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles
        ob = context.object
        cob = ob.cycles
        visibility = ob.cycles_visibility

        layout.label(text="Ray Visibility:")
        flow = layout.column_flow()

        flow.prop(visibility, "camera")
        flow.prop(visibility, "diffuse")
        flow.prop(visibility, "glossy")
        flow.prop(visibility, "transmission")
        flow.prop(visibility, "scatter")

        if ob.type != 'LAMP':
            flow.prop(visibility, "shadow")

        col = layout.column()
        col.label(text="Performance:")
        row = col.row()
        row.active = scene.render.use_simplify and cscene.use_camera_cull
        row.prop(cob, "use_camera_cull")


class CYCLES_OT_use_shading_nodes(Operator):
    """Enable nodes on a material, world or lamp"""
    bl_idname = "cycles.use_shading_nodes"
    bl_label = "Use Nodes"

    @classmethod
    def poll(cls, context):
        return (getattr(context, "material", False) or getattr(context, "world", False) or
                getattr(context, "lamp", False))

    def execute(self, context):
        if context.material:
            context.material.use_nodes = True
        elif context.world:
            context.world.use_nodes = True
        elif context.lamp:
            context.lamp.use_nodes = True

        return {'FINISHED'}


def find_node(material, nodetype):
    if material and material.node_tree:
        ntree = material.node_tree

        active_output_node = None
        for node in ntree.nodes:
            if getattr(node, "type", None) == nodetype:
                if getattr(node, "is_active_output", True):
                    return node
                if not active_output_node:
                    active_output_node = node
        return active_output_node

    return None


def find_node_input(node, name):
    for input in node.inputs:
        if input.name == name:
            return input

    return None


def panel_node_draw(layout, id_data, output_type, input_name):
    if not id_data.use_nodes:
        layout.operator("cycles.use_shading_nodes", icon='NODETREE')
        return False

    ntree = id_data.node_tree

    node = find_node(id_data, output_type)
    if not node:
        layout.label(text="No output node")
    else:
        input = find_node_input(node, input_name)
        layout.template_node_view(ntree, node, input)

    return True


class CyclesLamp_PT_preview(CyclesButtonsPanel, Panel):
    bl_label = "Preview"
    bl_context = "data"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.lamp and \
               not (context.lamp.type == 'AREA' and
                    context.lamp.cycles.is_portal) \
               and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        self.layout.template_preview(context.lamp)


class CyclesLamp_PT_lamp(CyclesButtonsPanel, Panel):
    bl_label = "Lamp"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.lamp and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        lamp = context.lamp
        clamp = lamp.cycles
        cscene = context.scene.cycles

        layout.prop(lamp, "type", expand=True)

        split = layout.split()
        col = split.column(align=True)

        if lamp.type in {'POINT', 'SUN', 'SPOT'}:
            col.prop(lamp, "shadow_soft_size", text="Size")
        elif lamp.type == 'AREA':
            col.prop(lamp, "shape", text="")
            sub = col.column(align=True)

            if lamp.shape == 'SQUARE':
                sub.prop(lamp, "size")
            elif lamp.shape == 'RECTANGLE':
                sub.prop(lamp, "size", text="Size X")
                sub.prop(lamp, "size_y", text="Size Y")

        if not (lamp.type == 'AREA' and clamp.is_portal):
            sub = col.column(align=True)
            if use_branched_path(context):
                sub.prop(clamp, "samples")
            sub.prop(clamp, "max_bounces")

        col = split.column()

        sub = col.column(align=True)
        sub.active = not (lamp.type == 'AREA' and clamp.is_portal)
        sub.prop(clamp, "cast_shadow")
        sub.prop(clamp, "use_multiple_importance_sampling", text="Multiple Importance")

        if lamp.type == 'AREA':
            col.prop(clamp, "is_portal", text="Portal")

        if lamp.type == 'HEMI':
            layout.label(text="Not supported, interpreted as sun lamp")


class CyclesLamp_PT_nodes(CyclesButtonsPanel, Panel):
    bl_label = "Nodes"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.lamp and not (context.lamp.type == 'AREA' and
                                     context.lamp.cycles.is_portal) and \
               CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        lamp = context.lamp
        if not panel_node_draw(layout, lamp, 'OUTPUT_LAMP', 'Surface'):
            layout.prop(lamp, "color")


class CyclesLamp_PT_spot(CyclesButtonsPanel, Panel):
    bl_label = "Spot Shape"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        lamp = context.lamp
        return (lamp and lamp.type == 'SPOT') and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        lamp = context.lamp

        split = layout.split()

        col = split.column()
        sub = col.column()
        sub.prop(lamp, "spot_size", text="Size")
        sub.prop(lamp, "spot_blend", text="Blend", slider=True)

        col = split.column()
        col.prop(lamp, "show_cone")


class CyclesWorld_PT_preview(CyclesButtonsPanel, Panel):
    bl_label = "Preview"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.world and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        self.layout.template_preview(context.world)


class CyclesWorld_PT_surface(CyclesButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return context.world and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        world = context.world

        if not panel_node_draw(layout, world, 'OUTPUT_WORLD', 'Surface'):
            layout.prop(world, "horizon_color", text="Color")


class CyclesWorld_PT_volume(CyclesButtonsPanel, Panel):
    bl_label = "Volume"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        world = context.world
        return world and world.node_tree and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        world = context.world
        panel_node_draw(layout, world, 'OUTPUT_WORLD', 'Volume')


class CyclesWorld_PT_ambient_occlusion(CyclesButtonsPanel, Panel):
    bl_label = "Ambient Occlusion"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return context.world and CyclesButtonsPanel.poll(context)

    def draw_header(self, context):
        light = context.world.light_settings
        self.layout.prop(light, "use_ambient_occlusion", text="")

    def draw(self, context):
        layout = self.layout

        light = context.world.light_settings

        row = layout.row()
        sub = row.row()
        sub.active = light.use_ambient_occlusion
        sub.prop(light, "ao_factor", text="Factor")
        row.prop(light, "distance", text="Distance")


class CyclesWorld_PT_mist(CyclesButtonsPanel, Panel):
    bl_label = "Mist Pass"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if CyclesButtonsPanel.poll(context):
            if context.world:
                for rl in context.scene.render.layers:
                    if rl.use_pass_mist:
                        return True

        return False

    def draw(self, context):
        layout = self.layout

        world = context.world

        split = layout.split(align=True)
        split.prop(world.mist_settings, "start")
        split.prop(world.mist_settings, "depth")

        layout.prop(world.mist_settings, "falloff")


class CyclesWorld_PT_ray_visibility(CyclesButtonsPanel, Panel):
    bl_label = "Ray Visibility"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return CyclesButtonsPanel.poll(context) and context.world

    def draw(self, context):
        layout = self.layout

        world = context.world
        visibility = world.cycles_visibility

        flow = layout.column_flow()

        flow.prop(visibility, "camera")
        flow.prop(visibility, "diffuse")
        flow.prop(visibility, "glossy")
        flow.prop(visibility, "transmission")
        flow.prop(visibility, "scatter")


class CyclesWorld_PT_settings(CyclesButtonsPanel, Panel):
    bl_label = "Settings"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.world and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        world = context.world
        cworld = world.cycles
        cscene = context.scene.cycles

        split = layout.split()

        col = split.column()

        col.label(text="Surface:")
        col.prop(cworld, "sample_as_light", text="Multiple Importance")

        sub = col.column(align=True)
        sub.active = cworld.sample_as_light
        sub.prop(cworld, "sample_map_resolution")
        if use_branched_path(context):
            sub.prop(cworld, "samples")
        sub.prop(cworld, "max_bounces")

        col = split.column()
        col.label(text="Volume:")
        sub = col.column()
        sub.active = use_cpu(context)
        sub.prop(cworld, "volume_sampling", text="")
        sub.prop(cworld, "volume_interpolation", text="")
        col.prop(cworld, "homogeneous_volume", text="Homogeneous")


class CyclesMaterial_PT_preview(CyclesButtonsPanel, Panel):
    bl_label = "Preview"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.material and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        self.layout.template_preview(context.material)


class CyclesMaterial_PT_surface(CyclesButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        if not panel_node_draw(layout, mat, 'OUTPUT_MATERIAL', 'Surface'):
            layout.prop(mat, "diffuse_color")


class CyclesMaterial_PT_volume(CyclesButtonsPanel, Panel):
    bl_label = "Volume"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat and mat.node_tree and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        # cmat = mat.cycles

        panel_node_draw(layout, mat, 'OUTPUT_MATERIAL', 'Volume')


class CyclesMaterial_PT_displacement(CyclesButtonsPanel, Panel):
    bl_label = "Displacement"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        mat = context.material
        return mat and mat.node_tree and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        panel_node_draw(layout, mat, 'OUTPUT_MATERIAL', 'Displacement')


class CyclesMaterial_PT_settings(CyclesButtonsPanel, Panel):
    bl_label = "Settings"
    bl_context = "material"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.material and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        cmat = mat.cycles

        split = layout.split()
        col = split.column()
        col.label(text="Surface:")
        col.prop(cmat, "sample_as_light", text="Multiple Importance")
        col.prop(cmat, "use_transparent_shadow")

        col = split.column()
        col.label(text="Volume:")
        sub = col.column()
        sub.active = use_cpu(context)
        sub.prop(cmat, "volume_sampling", text="")
        sub.prop(cmat, "volume_interpolation", text="")
        col.prop(cmat, "homogeneous_volume", text="Homogeneous")

        layout.separator()
        split = layout.split()

        col = split.column(align=True)
        col.label("Viewport Color:")
        col.prop(mat, "diffuse_color", text="")
        col.prop(mat, "alpha")

        col.separator()
        col.label("Viewport Alpha:")
        col.prop(mat.game_settings, "alpha_blend", text="")

        col = split.column(align=True)
        col.label("Viewport Specular:")
        col.prop(mat, "specular_color", text="")
        col.prop(mat, "specular_hardness", text="Hardness")

        col.separator()
        col.prop(mat, "pass_index")


class CyclesTexture_PT_context(CyclesButtonsPanel, Panel):
    bl_label = ""
    bl_context = "texture"
    bl_options = {'HIDE_HEADER'}
    COMPAT_ENGINES = {'CYCLES'}

    def draw(self, context):
        layout = self.layout

        tex = context.texture
        space = context.space_data
        pin_id = space.pin_id
        use_pin_id = space.use_pin_id
        user = context.texture_user

        space.use_limited_texture_context = False

        if not (use_pin_id and isinstance(pin_id, bpy.types.Texture)):
            pin_id = None

        if not pin_id:
            layout.template_texture_user()

        if user or pin_id:
            layout.separator()

            split = layout.split(percentage=0.65)
            col = split.column()

            if pin_id:
                col.template_ID(space, "pin_id")
            else:
                propname = context.texture_user_property.identifier
                col.template_ID(user, propname, new="texture.new")

            if tex:
                split = layout.split(percentage=0.2)
                split.label(text="Type:")
                split.prop(tex, "type", text="")


class CyclesTexture_PT_node(CyclesButtonsPanel, Panel):
    bl_label = "Node"
    bl_context = "texture"

    @classmethod
    def poll(cls, context):
        node = context.texture_node
        return node and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        node = context.texture_node
        ntree = node.id_data
        layout.template_node_view(ntree, node, None)


class CyclesTexture_PT_mapping(CyclesButtonsPanel, Panel):
    bl_label = "Mapping"
    bl_context = "texture"

    @classmethod
    def poll(cls, context):
        node = context.texture_node
        # TODO(sergey): perform a faster/nicer check?
        return node and hasattr(node, 'texture_mapping') and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        node = context.texture_node

        mapping = node.texture_mapping

        layout.prop(mapping, "vector_type", expand=True)

        row = layout.row()

        row.column().prop(mapping, "translation")
        row.column().prop(mapping, "rotation")
        row.column().prop(mapping, "scale")

        layout.label(text="Projection:")

        row = layout.row()
        row.prop(mapping, "mapping_x", text="")
        row.prop(mapping, "mapping_y", text="")
        row.prop(mapping, "mapping_z", text="")


class CyclesTexture_PT_colors(CyclesButtonsPanel, Panel):
    bl_label = "Color"
    bl_context = "texture"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        # node = context.texture_node
        return False
        # return node and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        node = context.texture_node

        mapping = node.color_mapping

        split = layout.split()

        col = split.column()
        col.label(text="Blend:")
        col.prop(mapping, "blend_type", text="")
        col.prop(mapping, "blend_factor", text="Factor")
        col.prop(mapping, "blend_color", text="")

        col = split.column()
        col.label(text="Adjust:")
        col.prop(mapping, "brightness")
        col.prop(mapping, "contrast")
        col.prop(mapping, "saturation")

        layout.separator()

        layout.prop(mapping, "use_color_ramp", text="Ramp")
        if mapping.use_color_ramp:
            layout.template_color_ramp(mapping, "color_ramp", expand=True)


class CyclesParticle_PT_textures(CyclesButtonsPanel, Panel):
    bl_label = "Textures"
    bl_context = "particle"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        return psys and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        psys = context.particle_system
        part = psys.settings

        row = layout.row()
        row.template_list("TEXTURE_UL_texslots", "", part, "texture_slots", part, "active_texture_index", rows=2)

        col = row.column(align=True)
        col.operator("texture.slot_move", text="", icon='TRIA_UP').type = 'UP'
        col.operator("texture.slot_move", text="", icon='TRIA_DOWN').type = 'DOWN'
        col.menu("TEXTURE_MT_specials", icon='DOWNARROW_HLT', text="")

        if not part.active_texture:
            layout.template_ID(part, "active_texture", new="texture.new")
        else:
            slot = part.texture_slots[part.active_texture_index]
            layout.template_ID(slot, "texture", new="texture.new")


class CyclesRender_PT_CurveRendering(CyclesButtonsPanel, Panel):
    bl_label = "Cycles Hair Rendering"
    bl_context = "particle"

    @classmethod
    def poll(cls, context):
        psys = context.particle_system
        return CyclesButtonsPanel.poll(context) and psys and psys.settings.type == 'HAIR'

    def draw_header(self, context):
        ccscene = context.scene.cycles_curves
        self.layout.prop(ccscene, "use_curves", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        ccscene = scene.cycles_curves

        layout.active = ccscene.use_curves

        layout.prop(ccscene, "primitive", text="Primitive")
        layout.prop(ccscene, "shape", text="Shape")

        if not (ccscene.primitive in {'CURVE_SEGMENTS', 'LINE_SEGMENTS'} and ccscene.shape == 'RIBBONS'):
            layout.prop(ccscene, "cull_backfacing", text="Cull back-faces")

        if ccscene.primitive == 'TRIANGLES' and ccscene.shape == 'THICK':
            layout.prop(ccscene, "resolution", text="Resolution")
        elif ccscene.primitive == 'CURVE_SEGMENTS':
            layout.prop(ccscene, "subdivisions", text="Curve subdivisions")

        row = layout.row()
        row.prop(ccscene, "minimum_width", text="Min Pixels")
        row.prop(ccscene, "maximum_width", text="Max Ext.")


class CyclesRender_PT_bake(CyclesButtonsPanel, Panel):
    bl_label = "Bake"
    bl_context = "render"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'CYCLES'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles
        cbk = scene.render.bake

        layout.operator("object.bake", icon='RENDER_STILL').type = cscene.bake_type

        col = layout.column()
        col.prop(cscene, "bake_type")
        col.separator()

        split = layout.split()

        col = split.column()
        col.prop(cbk, "margin")
        col.prop(cbk, "use_clear")

        col = split.column()
        col.prop(cbk, "use_selected_to_active")
        sub = col.column()
        sub.active = cbk.use_selected_to_active
        sub.prop(cbk, "use_cage", text="Cage")
        if cbk.use_cage:
            sub.prop(cbk, "cage_extrusion", text="Extrusion")
            sub.prop_search(cbk, "cage_object", scene, "objects", text="")
        else:
            sub.prop(cbk, "cage_extrusion", text="Ray Distance")

        if cscene.bake_type == 'NORMAL':
            layout.separator()
            box = layout.box()
            box.label(text="Normal Settings:")
            box.prop(cbk, "normal_space", text="Space")

            row = box.row(align=True)
            row.label(text="Swizzle:")
            row.prop(cbk, "normal_r", text="")
            row.prop(cbk, "normal_g", text="")
            row.prop(cbk, "normal_b", text="")


class CyclesParticle_PT_CurveSettings(CyclesButtonsPanel, Panel):
    bl_label = "Cycles Hair Settings"
    bl_context = "particle"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        ccscene = scene.cycles_curves
        psys = context.particle_system
        use_curves = ccscene.use_curves and psys
        return CyclesButtonsPanel.poll(context) and use_curves and psys.settings.type == 'HAIR'

    def draw(self, context):
        layout = self.layout

        psys = context.particle_settings
        cpsys = psys.cycles

        row = layout.row()
        row.prop(cpsys, "shape", text="Shape")

        layout.label(text="Thickness:")
        row = layout.row()
        row.prop(cpsys, "root_width", text="Root")
        row.prop(cpsys, "tip_width", text="Tip")

        row = layout.row()
        row.prop(cpsys, "radius_scale", text="Scaling")
        row.prop(cpsys, "use_closetip", text="Close tip")


class CyclesScene_PT_simplify(CyclesButtonsPanel, Panel):
    bl_label = "Simplify"
    bl_context = "scene"
    COMPAT_ENGINES = {'CYCLES'}

    def draw_header(self, context):
        rd = context.scene.render
        self.layout.prop(rd, "use_simplify", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        cscene = scene.cycles

        layout.active = rd.use_simplify
        split = layout.split()

        col = split.column()
        col.label(text="Viewport:")
        col.prop(rd, "simplify_subdivision", text="Subdivision")
        col.prop(rd, "simplify_child_particles", text="Child Particles")

        col = split.column()
        col.label(text="Render:")
        col.prop(rd, "simplify_subdivision_render", text="Subdivision")
        col.prop(rd, "simplify_child_particles_render", text="Child Particles")

        col = layout.column()
        col.prop(cscene, "use_camera_cull")
        subsub = col.column()
        subsub.active = cscene.use_camera_cull
        subsub.prop(cscene, "camera_cull_margin")


def draw_device(self, context):
    scene = context.scene
    layout = self.layout

    if scene.render.engine == 'CYCLES':
        from . import engine
        cscene = scene.cycles

        layout.prop(cscene, "feature_set")

        device_type = context.user_preferences.system.compute_device_type
        if device_type in {'CUDA', 'OPENCL', 'NETWORK'}:
            layout.prop(cscene, "device")

        if engine.with_osl() and use_cpu(context):
            layout.prop(cscene, "shading_system")


def draw_pause(self, context):
    layout = self.layout
    scene = context.scene

    if scene.render.engine == "CYCLES":
        view = context.space_data

        if view.viewport_shade == 'RENDERED':
            cscene = scene.cycles
            layername = scene.render.layers.active.name
            layout.prop(cscene, "preview_pause", icon="PAUSE", text="")
            layout.prop(cscene, "preview_active_layer", icon="RENDERLAYERS", text=layername)


def get_panels():
    types = bpy.types
    panels = [
        "RENDER_PT_render",
        "RENDER_PT_output",
        "RENDER_PT_encoding",
        "RENDER_PT_dimensions",
        "RENDER_PT_stamp",
        "RENDER_PT_freestyle",
        "RENDERLAYER_PT_layers",
        "RENDERLAYER_PT_freestyle",
        "RENDERLAYER_PT_freestyle_lineset",
        "RENDERLAYER_PT_freestyle_linestyle",
        "SCENE_PT_scene",
        "SCENE_PT_color_management",
        "SCENE_PT_custom_props",
        "SCENE_PT_audio",
        "SCENE_PT_unit",
        "SCENE_PT_keying_sets",
        "SCENE_PT_keying_set_paths",
        "SCENE_PT_physics",
        "WORLD_PT_context_world",
        "WORLD_PT_custom_props",
        "DATA_PT_context_mesh",
        "DATA_PT_context_camera",
        "DATA_PT_context_lamp",
        "DATA_PT_context_speaker",
        "DATA_PT_normals",
        "DATA_PT_texture_space",
        "DATA_PT_curve_texture_space",
        "DATA_PT_mball_texture_space",
        "DATA_PT_vertex_groups",
        "DATA_PT_shape_keys",
        "DATA_PT_uv_texture",
        "DATA_PT_vertex_colors",
        "DATA_PT_camera",
        "DATA_PT_camera_display",
        "DATA_PT_camera_stereoscopy",
        "DATA_PT_camera_safe_areas",
        "DATA_PT_lens",
        "DATA_PT_speaker",
        "DATA_PT_distance",
        "DATA_PT_cone",
        "DATA_PT_customdata",
        "DATA_PT_custom_props_mesh",
        "DATA_PT_custom_props_camera",
        "DATA_PT_custom_props_lamp",
        "DATA_PT_custom_props_speaker",
        "DATA_PT_custom_props_arm",
        "DATA_PT_custom_props_curve",
        "DATA_PT_custom_props_lattice",
        "DATA_PT_custom_props_metaball",
        "TEXTURE_PT_preview",
        "TEXTURE_PT_custom_props",
        "TEXTURE_PT_clouds",
        "TEXTURE_PT_wood",
        "TEXTURE_PT_marble",
        "TEXTURE_PT_magic",
        "TEXTURE_PT_blend",
        "TEXTURE_PT_stucci",
        "TEXTURE_PT_image",
        "TEXTURE_PT_image_sampling",
        "TEXTURE_PT_image_mapping",
        "TEXTURE_PT_musgrave",
        "TEXTURE_PT_voronoi",
        "TEXTURE_PT_distortednoise",
        "TEXTURE_PT_voxeldata",
        "TEXTURE_PT_pointdensity",
        "TEXTURE_PT_pointdensity_turbulence",
        "TEXTURE_PT_mapping",
        "TEXTURE_PT_ocean",
        "TEXTURE_PT_influence",
        "TEXTURE_PT_colors",
        "PARTICLE_PT_context_particles",
        "PARTICLE_PT_custom_props",
        "PARTICLE_PT_emission",
        "PARTICLE_PT_hair_dynamics",
        "PARTICLE_PT_cache",
        "PARTICLE_PT_velocity",
        "PARTICLE_PT_rotation",
        "PARTICLE_PT_physics",
        "SCENE_PT_rigid_body_world",
        "SCENE_PT_rigid_body_cache",
        "SCENE_PT_rigid_body_field_weights",
        "PARTICLE_PT_boidbrain",
        "PARTICLE_PT_render",
        "PARTICLE_PT_draw",
        "PARTICLE_PT_children",
        "PARTICLE_PT_field_weights",
        "PARTICLE_PT_force_fields",
        "PARTICLE_PT_vertexgroups",
        "MATERIAL_PT_custom_props",
        "MATERIAL_PT_freestyle_line",
        "BONE_PT_custom_props",
        "OBJECT_PT_custom_props",
        ]

    return [getattr(types, p) for p in panels if hasattr(types, p)]


def register():
    bpy.types.RENDER_PT_render.append(draw_device)
    bpy.types.VIEW3D_HT_header.append(draw_pause)

    for panel in get_panels():
        panel.COMPAT_ENGINES.add('CYCLES')


def unregister():
    bpy.types.RENDER_PT_render.remove(draw_device)
    bpy.types.VIEW3D_HT_header.remove(draw_pause)

    for panel in get_panels():
        panel.COMPAT_ENGINES.remove('CYCLES')
