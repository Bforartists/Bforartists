#
# Copyright 2011, Blender Foundation.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#

# <pep8 compliant>

import bpy

from bpy.types import Panel, Menu, Operator


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


class CyclesButtonsPanel():
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine == 'CYCLES'


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
        sub.active = (device_type == 'NONE' or cscene.device == 'CPU')
        sub.prop(cscene, "progressive")
        
        if not cscene.progressive:
            row.prop(cscene, "squared_samples")
        
        split = layout.split()
        
        col = split.column()
        sub = col.column(align=True)
        sub.label("Settings:")
        sub.prop(cscene, "seed")
        sub.prop(cscene, "sample_clamp")

        if cscene.progressive or (device_type != 'NONE' and cscene.device == 'GPU'):
            col = split.column()
            sub = col.column(align=True)
            sub.label(text="Samples:")
            sub.prop(cscene, "samples", text="Render")
            sub.prop(cscene, "preview_samples", text="Preview")
        else:
            sub.label(text="AA Samples:")
            sub.prop(cscene, "aa_samples", text="Render")
            sub.prop(cscene, "preview_aa_samples", text="Preview")

            col = split.column()
            sub = col.column(align=True)
            sub.label(text="Samples:")
            sub.prop(cscene, "diffuse_samples", text="Diffuse")
            sub.prop(cscene, "glossy_samples", text="Glossy")
            sub.prop(cscene, "transmission_samples", text="Transmission")
            sub.prop(cscene, "ao_samples", text="AO")
            sub.prop(cscene, "mesh_light_samples", text="Mesh Light")
            sub.prop(cscene, "subsurface_samples", text="Subsurface")

        if cscene.feature_set == 'EXPERIMENTAL' and (device_type == 'NONE' or cscene.device == 'CPU'):
            layout.row().prop(cscene, "sampling_pattern", text="Pattern")

        for rl in scene.render.layers:
            if rl.samples > 0:
                layout.separator()
                layout.row().prop(cscene, "use_layer_samples")
                break


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

        col.prop(cscene, "no_caustics")
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


class CyclesRender_PT_motion_blur(CyclesButtonsPanel, Panel):
    bl_label = "Motion Blur"
    bl_options = {'DEFAULT_CLOSED'}

    def draw_header(self, context):
        rd = context.scene.render

        self.layout.prop(rd, "use_motion_blur", text="")

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render
        layout.active = rd.use_motion_blur

        row = layout.row()
        row.prop(rd, "motion_blur_shutter")


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
        col.row().prop(rd, "threads_mode", expand=True)
        sub = col.column()
        sub.enabled = rd.threads_mode == 'FIXED'
        sub.prop(rd, "threads")

        sub = col.column(align=True)
        sub.label(text="Tiles:")
        sub.prop(cscene, "tile_order", text="")

        sub.prop(rd, "tile_x", text="X")
        sub.prop(rd, "tile_y", text="Y")

        sub.prop(cscene, "use_progressive_refine")

        subsub = sub.column()
        subsub.enabled = not rd.use_border
        subsub.prop(rd, "use_save_buffers")

        col = split.column(align=True)

        col.label(text="Viewport:")
        col.prop(cscene, "debug_bvh_type", text="")
        col.separator()
        col.prop(cscene, "preview_start_resolution")

        col.separator()

        col.label(text="Final Render:")
        col.prop(cscene, "use_cache")
        col.prop(rd, "use_persistent_data", text="Persistent Images")

        col.separator()

        col.label(text="Acceleration structure:")   
        col.prop(cscene, "debug_use_spatial_splits")


class CyclesRender_PT_opengl(CyclesButtonsPanel, Panel):
    bl_label = "OpenGL Render"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        split = layout.split()

        col = split.column()
        col.prop(rd, "use_antialiasing")
        sub = col.row()
        sub.active = rd.use_antialiasing
        sub.prop(rd, "antialiasing_samples", expand=True)

        col = split.column()
        col.label(text="Alpha:")
        col.prop(rd, "alpha_mode", text="")


class CyclesRender_PT_layers(CyclesButtonsPanel, Panel):
    bl_label = "Layer List"
    bl_context = "render_layer"
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render
        rl = rd.layers.active

        row = layout.row()
        row.template_list("RENDERLAYER_UL_renderlayers", "", rd, "layers", rd.layers, "active_index", rows=2)

        col = row.column(align=True)
        col.operator("scene.render_layer_add", icon='ZOOMIN', text="")
        col.operator("scene.render_layer_remove", icon='ZOOMOUT', text="")

        row = layout.row()
        if rl:
            row.prop(rl, "name")
        row.prop(rd, "use_single_layer", text="", icon_only=True)


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
        col.prop(rl, "use_pass_shadow")

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
        col.prop(rl, "use_pass_ambient_occlusion")


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

        split = layout.split()

        col = split.column()
        col.label("Focus:")
        col.prop(cam, "dof_object", text="")

        sub = col.row()
        sub.active = cam.dof_object is None
        sub.prop(cam, "dof_distance", text="Distance")

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

        if ob:
            row = layout.row()

            row.template_list("MATERIAL_UL_matslots", "", ob, "material_slots", ob, "active_material_index", rows=2)

            col = row.column(align=True)
            col.operator("object.material_slot_add", icon='ZOOMIN', text="")
            col.operator("object.material_slot_remove", icon='ZOOMOUT', text="")

            col.menu("MATERIAL_MT_specials", icon='DOWNARROW_HLT', text="")

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


class Cycles_PT_mesh_normals(CyclesButtonsPanel, Panel):
    bl_label = "Normals"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return CyclesButtonsPanel.poll(context) and context.mesh

    def draw(self, context):
        layout = self.layout

        mesh = context.mesh

        split = layout.split()

        col = split.column()
        col.prop(mesh, "show_double_sided")

        col = split.column()
        col.label()


class CyclesObject_PT_ray_visibility(CyclesButtonsPanel, Panel):
    bl_label = "Ray Visibility"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return CyclesButtonsPanel.poll(context) and ob and ob.type in {'MESH', 'CURVE', 'CURVE', 'SURFACE', 'FONT', 'META', 'LAMP'}

    def draw(self, context):
        layout = self.layout

        ob = context.object
        visibility = ob.cycles_visibility

        flow = layout.column_flow()

        flow.prop(visibility, "camera")
        flow.prop(visibility, "diffuse")
        flow.prop(visibility, "glossy")
        flow.prop(visibility, "transmission")

        if ob.type != 'LAMP':
            flow.prop(visibility, "shadow")


class CYCLES_OT_use_shading_nodes(Operator):
    """Enable nodes on a material, world or lamp"""
    bl_idname = "cycles.use_shading_nodes"
    bl_label = "Use Nodes"

    @classmethod
    def poll(cls, context):
        return context.material or context.world or context.lamp

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

        for node in ntree.nodes:
            if getattr(node, "type", None) == nodetype:
                return node

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
        return context.lamp and CyclesButtonsPanel.poll(context)

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
        device_type = context.user_preferences.system.compute_device_type

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

        if not cscene.progressive and (device_type == 'NONE' or cscene.device == 'CPU'):
            col.prop(clamp, "samples")

        col = split.column()
        col.prop(clamp, "cast_shadow")

        layout.prop(clamp, "use_multiple_importance_sampling")

        if lamp.type == 'HEMI':
            layout.label(text="Not supported, interpreted as sun lamp")


class CyclesLamp_PT_nodes(CyclesButtonsPanel, Panel):
    bl_label = "Nodes"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.lamp and CyclesButtonsPanel.poll(context)

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
        # world = context.world
        # world and world.node_tree and CyclesButtonsPanel.poll(context)
        return False

    def draw(self, context):
        layout = self.layout
        layout.active = False

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

        layout.active = light.use_ambient_occlusion

        row = layout.row()
        row.prop(light, "ao_factor", text="Factor")
        row.prop(light, "distance", text="Distance")


class CyclesWorld_PT_mist(CyclesButtonsPanel, Panel):
    bl_label = "Mist Pass"
    bl_context = "world"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        if CyclesButtonsPanel.poll(context):
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
        device_type = context.user_preferences.system.compute_device_type

        col = layout.column()

        col.prop(cworld, "sample_as_light")
        sub = col.row(align=True)
        sub.active = cworld.sample_as_light
        sub.prop(cworld, "sample_map_resolution")
        if not cscene.progressive and (device_type == 'NONE' or cscene.device == 'CPU'):
            sub.prop(cworld, "samples")


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
        # mat = context.material
        # mat and mat.node_tree and CyclesButtonsPanel.poll(context)
        return False

    def draw(self, context):
        layout = self.layout
        layout.active = False

        mat = context.material
        cmat = mat.cycles

        panel_node_draw(layout, mat, 'OUTPUT_MATERIAL', 'Volume')

        layout.prop(cmat, "homogeneous_volume")


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
        col.prop(mat, "diffuse_color", text="Viewport Color")

        col = split.column(align=True)
        col.label()
        col.prop(mat, "pass_index")

        col = layout.column()
        col.prop(cmat, "sample_as_light")
        col.prop(cmat, "use_transparent_shadow")


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
        return node and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        node = context.texture_node

        mapping = node.texture_mapping

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
        #return node and CyclesButtonsPanel.poll(context)

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
        scene = context.scene
        cscene = scene.cycles
        psys = context.particle_system
        experimental = (cscene.feature_set == 'EXPERIMENTAL')
        return CyclesButtonsPanel.poll(context) and experimental and psys

    def draw_header(self, context):
        ccscene = context.scene.cycles_curves
        self.layout.prop(ccscene, "use_curves", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        ccscene = scene.cycles_curves

        layout.active = ccscene.use_curves

        layout.prop(ccscene, "preset", text="Mode")

        if ccscene.preset == 'CUSTOM':
            layout.prop(ccscene, "primitive", text="Primitive")

            if ccscene.primitive == 'TRIANGLES':
                layout.prop(ccscene, "triangle_method", text="Method")
                if ccscene.triangle_method == 'TESSELLATED_TRIANGLES':
                    layout.prop(ccscene, "resolution", text="Resolution")
                layout.prop(ccscene, "use_smooth", text="Smooth")
            elif ccscene.primitive == 'LINE_SEGMENTS':
                layout.prop(ccscene, "use_backfacing", text="Check back-faces")

                row = layout.row()
                row.prop(ccscene, "use_encasing", text="Exclude encasing")
                sub = row.row()
                sub.active = ccscene.use_encasing
                sub.prop(ccscene, "encasing_ratio", text="Ratio for encasing")

                layout.prop(ccscene, "line_method", text="Method")
                layout.prop(ccscene, "use_tangent_normal", text="Use tangent normal as default")
                layout.prop(ccscene, "use_tangent_normal_geometry", text="Use tangent normal geometry")
                layout.prop(ccscene, "use_tangent_normal_correction", text="Correct tangent normal for slope")
                layout.prop(ccscene, "interpolation", text="Interpolation")

                row = layout.row()
                row.prop(ccscene, "segments", text="Segments")
                row.prop(ccscene, "normalmix", text="Ray Mix")
            elif ccscene.primitive in {'CURVE_SEGMENTS', 'CURVE_RIBBONS'}:
                layout.prop(ccscene, "subdivisions", text="Curve subdivisions")
                layout.prop(ccscene, "use_backfacing", text="Check back-faces")

                layout.prop(ccscene, "interpolation", text="Interpolation")
                row = layout.row()
                row.prop(ccscene, "segments", text="Segments")

            row = layout.row()
            row.prop(ccscene, "use_parents", text="Include parents")

        row = layout.row()
        row.prop(ccscene, "minimum_width", text="Min Pixels")
        row.prop(ccscene, "maximum_width", text="Max Ext.")


class CyclesParticle_PT_CurveSettings(CyclesButtonsPanel, Panel):
    bl_label = "Cycles Hair Settings"
    bl_context = "particle"

    @classmethod
    def poll(cls, context):
        scene = context.scene
        cscene = scene.cycles
        ccscene = scene.cycles_curves
        use_curves = ccscene.use_curves and context.particle_system
        experimental = cscene.feature_set == 'EXPERIMENTAL'
        return CyclesButtonsPanel.poll(context) and experimental and use_curves

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

        rd = context.scene.render

        layout.active = rd.use_simplify

        row = layout.row()
        row.prop(rd, "simplify_subdivision", text="Subdivision")
        row.prop(rd, "simplify_child_particles", text="Child Particles")


def draw_device(self, context):
    scene = context.scene
    layout = self.layout

    if scene.render.engine == 'CYCLES':
        from . import engine
        cscene = scene.cycles

        layout.prop(cscene, "feature_set")

        device_type = context.user_preferences.system.compute_device_type
        if device_type == 'CUDA':
            layout.prop(cscene, "device")
        elif device_type == 'OPENCL':
            layout.prop(cscene, "device")

        if engine.with_osl() and (cscene.device == 'CPU' or device_type == 'NONE'):
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
    return (
        types.RENDER_PT_render,
        types.RENDER_PT_output,
        types.RENDER_PT_encoding,
        types.RENDER_PT_dimensions,
        types.RENDER_PT_stamp,
        types.SCENE_PT_scene,
        types.SCENE_PT_color_management,
        types.SCENE_PT_custom_props,
        types.SCENE_PT_audio,
        types.SCENE_PT_unit,
        types.SCENE_PT_keying_sets,
        types.SCENE_PT_keying_set_paths,
        types.SCENE_PT_physics,
        types.WORLD_PT_context_world,
        types.WORLD_PT_custom_props,
        types.DATA_PT_context_mesh,
        types.DATA_PT_context_camera,
        types.DATA_PT_context_lamp,
        types.DATA_PT_context_speaker,
        types.DATA_PT_texture_space,
        types.DATA_PT_curve_texture_space,
        types.DATA_PT_mball_texture_space,
        types.DATA_PT_vertex_groups,
        types.DATA_PT_shape_keys,
        types.DATA_PT_uv_texture,
        types.DATA_PT_vertex_colors,
        types.DATA_PT_camera,
        types.DATA_PT_camera_display,
        types.DATA_PT_lens,
        types.DATA_PT_speaker,
        types.DATA_PT_distance,
        types.DATA_PT_cone,
        types.DATA_PT_customdata,
        types.DATA_PT_custom_props_mesh,
        types.DATA_PT_custom_props_camera,
        types.DATA_PT_custom_props_lamp,
        types.DATA_PT_custom_props_speaker,
        types.DATA_PT_custom_props_arm,
        types.DATA_PT_custom_props_curve,
        types.DATA_PT_custom_props_lattice,
        types.DATA_PT_custom_props_metaball,
        types.TEXTURE_PT_custom_props,
        types.TEXTURE_PT_clouds,
        types.TEXTURE_PT_wood,
        types.TEXTURE_PT_marble,
        types.TEXTURE_PT_magic,
        types.TEXTURE_PT_blend,
        types.TEXTURE_PT_stucci,
        types.TEXTURE_PT_image,
        types.TEXTURE_PT_image_sampling,
        types.TEXTURE_PT_image_mapping,
        types.TEXTURE_PT_musgrave,
        types.TEXTURE_PT_voronoi,
        types.TEXTURE_PT_distortednoise,
        types.TEXTURE_PT_voxeldata,
        types.TEXTURE_PT_pointdensity,
        types.TEXTURE_PT_pointdensity_turbulence,
        types.TEXTURE_PT_mapping,
        types.TEXTURE_PT_influence,
        types.TEXTURE_PT_colors,
        types.PARTICLE_PT_context_particles,
        types.PARTICLE_PT_custom_props,
        types.PARTICLE_PT_emission,
        types.PARTICLE_PT_hair_dynamics,
        types.PARTICLE_PT_cache,
        types.PARTICLE_PT_velocity,
        types.PARTICLE_PT_rotation,
        types.PARTICLE_PT_physics,
        types.SCENE_PT_rigid_body_world,
        types.SCENE_PT_rigid_body_cache,
        types.SCENE_PT_rigid_body_field_weights,
        types.PARTICLE_PT_boidbrain,
        types.PARTICLE_PT_render,
        types.PARTICLE_PT_draw,
        types.PARTICLE_PT_children,
        types.PARTICLE_PT_field_weights,
        types.PARTICLE_PT_force_fields,
        types.PARTICLE_PT_vertexgroups,
        types.MATERIAL_PT_custom_props,
        types.BONE_PT_custom_props,
        types.OBJECT_PT_custom_props,
        )


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
