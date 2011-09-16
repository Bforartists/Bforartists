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

import bpy

from bpy.types import Panel, Menu

from cycles import enums
from cycles import engine

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

class CyclesRender_PT_integrator(CyclesButtonsPanel, Panel):
    bl_label = "Integrator"
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
        sub.label(text="Samples:")
        sub.prop(cscene, "samples", text="Render")
        sub.prop(cscene, "preview_samples", text="Preview")

        sub = col.column(align=True)
        sub.label("Tranparency:")
        sub.prop(cscene, "transparent_max_bounces", text="Max")
        sub.prop(cscene, "transparent_min_bounces", text="Min")
        sub.prop(cscene, "no_caustics")

        col = split.column()

        sub = col.column(align=True)
        sub.label(text="Bounces:")
        sub.prop(cscene, "max_bounces", text="Max")
        sub.prop(cscene, "min_bounces", text="Min")

        sub = col.column(align=True)
        sub.label(text="Light Paths:")
        sub.prop(cscene, "diffuse_bounces", text="Diffuse")
        sub.prop(cscene, "glossy_bounces", text="Glossy")
        sub.prop(cscene, "transmission_bounces", text="Transmission")

        #row = col.row()
        #row.prop(cscene, "blur_caustics")
        #row.active = not cscene.no_caustics
        
class CyclesRender_PT_film(CyclesButtonsPanel, Panel):
    bl_label = "Film"

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        cscene = scene.cycles

        split = layout.split()

        col = split.column();
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
        sub.prop(cscene, "debug_tile_size")
        sub.prop(cscene, "debug_min_size")

        col = split.column()

        sub = col.column(align=True)
        sub.label(text="Acceleration structure:")
        sub.prop(cscene, "debug_bvh_type", text="")
        sub.prop(cscene, "debug_use_spatial_splits")

class CyclesRender_PT_layers(CyclesButtonsPanel, Panel):
    bl_label = "Layers"
    bl_options = {'DEFAULT_CLOSED'}
    COMPAT_ENGINES = {'BLENDER_RENDER'}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        rd = scene.render

        # row = layout.row()
        # row.template_list(rd, "layers", rd.layers, "active_index", rows=2)

        # col = row.column(align=True)
        # col.operator("scene.render_layer_add", icon='ZOOMIN', text="")
        # col.operator("scene.render_layer_remove", icon='ZOOMOUT', text="")

        row = layout.row()
        # rl = rd.layers.active
        rl = rd.layers[0]
        row.prop(rl, "name")
        #row.prop(rd, "use_single_layer", text="", icon_only=True)

        split = layout.split()

        col = split.column()
        col.prop(scene, "layers", text="Scene")

        col = split.column()
        col.prop(rl, "layers", text="Layer")

        layout.separator()

        layout.prop(rl, "material_override", text="Material")

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
        col.prop(ccam, "aperture_size", text="Size")

        sub = col.column(align=True)
        sub.prop(ccam, "aperture_blades", text="Blades")
        sub.prop(ccam, "aperture_rotation", text="Rotation")

class Cycles_PT_context_material(CyclesButtonsPanel, Panel):
    bl_label = "Surface"
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

            row.template_list(ob, "material_slots", ob, "active_material_index", rows=2)

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
        return context.mesh or context.curve or context.meta_ball

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
        layout.prop(cdata, "use_subdivision");
        layout.prop(cdata, "dicing_rate");

class CyclesObject_PT_ray_visibility(CyclesButtonsPanel, Panel):
    bl_label = "Ray Visibility"
    bl_context = "object"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type in ('MESH', 'CURVE', 'CURVE', 'SURFACE', 'FONT', 'META') # todo: 'LAMP'

    def draw(self, context):
        layout = self.layout

        ob = context.object
        visibility = ob.cycles_visibility

        split = layout.split()

        col = split.column()
        col.prop(visibility, "camera")
        col.prop(visibility, "diffuse")
        col.prop(visibility, "glossy")

        col = split.column()
        col.prop(visibility, "transmission")
        col.prop(visibility, "shadow")

def find_node(material, nodetype):
    if material and material.node_tree:
        ntree = material.node_tree

        for node in ntree.nodes:
            if type(node) is not bpy.types.NodeGroup and node.type == nodetype:
                return node
    
    return None

def find_node_input(node, name):
    for input in node.inputs:
        if input.name == name:
            return input
    
    return None

def panel_node_draw(layout, id, output_type, input_name):
    if not id.node_tree:
        layout.prop(id, "use_nodes")
        return

    ntree = id.node_tree

    node = find_node(id, output_type)
    if not node:
        layout.label(text="No output node.")
    else:
        input = find_node_input(node, input_name)
        layout.template_node_view(ntree, node, input);

class CyclesLamp_PT_lamp(CyclesButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.lamp and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.lamp
        panel_node_draw(layout, mat, 'OUTPUT_LAMP', 'Surface')

class CyclesWorld_PT_surface(CyclesButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return context.world and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.world
        panel_node_draw(layout, mat, 'OUTPUT_WORLD', 'Surface')

class CyclesWorld_PT_volume(CyclesButtonsPanel, Panel):
    bl_label = "Volume"
    bl_context = "world"

    @classmethod
    def poll(cls, context):
        return context.world and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout
        layout.active = False

        mat = context.world
        panel_node_draw(layout, mat, 'OUTPUT_WORLD', 'Volume')

class CyclesMaterial_PT_surface(CyclesButtonsPanel, Panel):
    bl_label = "Surface"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        mat = context.material
        panel_node_draw(layout, mat, 'OUTPUT_MATERIAL', 'Surface')

class CyclesMaterial_PT_volume(CyclesButtonsPanel, Panel):
    bl_label = "Volume"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout
        layout.active = False

        mat = context.material
        panel_node_draw(layout, mat, 'OUTPUT_MATERIAL', 'Volume')

class CyclesMaterial_PT_displacement(CyclesButtonsPanel, Panel):
    bl_label = "Displacement"
    bl_context = "material"

    @classmethod
    def poll(cls, context):
        return context.material and CyclesButtonsPanel.poll(context)

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
        # return context.material and CyclesButtonsPanel.poll(context)
        return False

    def draw(self, context):
        layout = self.layout

        mat = context.material
    
        row = layout.row()
        row.label(text="Light Group:")
        row.prop(mat, "light_group", text="")

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
        use_pin_id = space.use_pin_id;
        user = context.texture_user
        node = context.texture_node

        if not use_pin_id or not isinstance(pin_id, bpy.types.Texture):
            pin_id = None

        if not pin_id:
            layout.template_texture_user()

        if user:
            layout.separator()

            split = layout.split(percentage=0.65)
            col = split.column()

            if pin_id:
                col.template_ID(space, "pin_id")
            elif user:
                col.template_ID(user, "texture", new="texture.new")
            
            if tex:
                row = split.row()
                row.prop(tex, "use_nodes", icon="NODETREE", text="")
                row.label()

                if not tex.use_nodes:
                    split = layout.split(percentage=0.2)
                    split.label(text="Type:")
                    split.prop(tex, "type", text="")

class CyclesTexture_PT_nodes(CyclesButtonsPanel, Panel):
    bl_label = "Nodes"
    bl_context = "texture"

    @classmethod
    def poll(cls, context):
        tex = context.texture
        return (tex and tex.use_nodes) and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout

        tex = context.texture
        panel_node_draw(layout, tex, 'OUTPUT_TEXTURE', 'Color')

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
        tex = context.texture
        node = context.texture_node
        return (node or (tex and tex.use_nodes)) and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout
        layout.label("Texture coordinate mapping goes here.");
        layout.label("Translate, rotate, scale, projection, XYZ.")

class CyclesTexture_PT_color(CyclesButtonsPanel, Panel):
    bl_label = "Color"
    bl_context = "texture"

    @classmethod
    def poll(cls, context):
        tex = context.texture
        node = context.texture_node
        return (node or (tex and tex.use_nodes)) and CyclesButtonsPanel.poll(context)

    def draw(self, context):
        layout = self.layout
        layout.label("Color modification options go here.");
        layout.label("Ramp, brightness, contrast, saturation.")

def draw_device(self, context):
    scene = context.scene
    layout = self.layout

    if scene.render.engine == "CYCLES":
        cscene = scene.cycles

        available_devices = engine.available_devices()
        available_cuda = 'cuda' in available_devices
        available_opencl = 'opencl' in available_devices

        if available_cuda or available_opencl:
            layout.prop(cscene, "device")
            if cscene.device == 'GPU' and available_cuda and available_opencl:
                layout.prop(cscene, "gpu_type")
        if cscene.device == 'CPU' and engine.with_osl():
            layout.prop(cscene, "shading_system")

def draw_pause(self, context):
    layout = self.layout
    scene = context.scene

    if scene.render.engine == "CYCLES":
        view = context.space_data

        if view.viewport_shade == "RENDERED":
            cscene = scene.cycles
            layout.prop(cscene, "preview_pause", icon="PAUSE", text="")

def get_panels():
    return [
        bpy.types.RENDER_PT_render,
        bpy.types.RENDER_PT_output,
        bpy.types.RENDER_PT_encoding,
        bpy.types.RENDER_PT_dimensions,
        bpy.types.RENDER_PT_stamp,
        bpy.types.WORLD_PT_context_world,
        bpy.types.DATA_PT_context_mesh,
        bpy.types.DATA_PT_context_camera,
        bpy.types.DATA_PT_context_lamp,
        bpy.types.DATA_PT_texture_space,
        bpy.types.DATA_PT_curve_texture_space,
        bpy.types.DATA_PT_mball_texture_space,
        bpy.types.DATA_PT_vertex_groups,
        bpy.types.DATA_PT_shape_keys,
        bpy.types.DATA_PT_uv_texture,
        bpy.types.DATA_PT_vertex_colors,
        bpy.types.DATA_PT_camera,
        bpy.types.DATA_PT_camera_display,
        bpy.types.DATA_PT_custom_props_mesh,
        bpy.types.DATA_PT_custom_props_camera,
        bpy.types.DATA_PT_custom_props_lamp,
        bpy.types.TEXTURE_PT_clouds,
        bpy.types.TEXTURE_PT_wood,
        bpy.types.TEXTURE_PT_marble,
        bpy.types.TEXTURE_PT_magic,
        bpy.types.TEXTURE_PT_blend,
        bpy.types.TEXTURE_PT_stucci,
        bpy.types.TEXTURE_PT_image,
        bpy.types.TEXTURE_PT_image_sampling,
        bpy.types.TEXTURE_PT_image_mapping,
        bpy.types.TEXTURE_PT_musgrave,
        bpy.types.TEXTURE_PT_voronoi,
        bpy.types.TEXTURE_PT_distortednoise,
        bpy.types.TEXTURE_PT_voxeldata,
        bpy.types.TEXTURE_PT_pointdensity,
        bpy.types.TEXTURE_PT_pointdensity_turbulence]

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

