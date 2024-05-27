# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

""""Nodes based User interface for shaders exported to POV textures."""
import bpy

from bpy.utils import register_class, unregister_class
from bpy.types import Menu, Operator
from bpy.props import (
    StringProperty,
)

# def find_node_input(node, name):
# for input in node.inputs:
# if input.name == name:
# return input

# def panel_node_draw(layout, id_data, output_type, input_name):
# if not id_data.use_nodes:
# #layout.operator("pov.material_use_nodes", icon='SOUND')#'NODETREE')
# #layout.operator("pov.use_shading_nodes", icon='NODETREE')
# layout.operator("WM_OT_context_toggle", icon='NODETREE').data_path = \
# "material.pov.material_use_nodes"
# return False

# ntree = id_data.node_tree

# node = find_node(id_data, output_type)
# if not node:
# layout.label(text="No output node")
# else:
# input = find_node_input(node, input_name)
# layout.template_node_view(ntree, node, input)

# return True


class NODE_MT_POV_map_create(Menu):
    """Create maps"""

    bl_idname = "POVRAY_MT_node_map_create"
    bl_label = "Create map"

    def draw(self, context):
        layout = self.layout
        layout.operator("node.map_create")


def menu_func_nodes(self, context):
    ob = context.object
    if hasattr(ob, "active_material"):
        mat = context.object.active_material
        if mat and context.space_data.tree_type == "ObjectNodeTree":
            self.layout.prop(mat.pov, "material_use_nodes")
            self.layout.menu(NODE_MT_POV_map_create.bl_idname)
            self.layout.operator("wm.updatepreviewkey")
        if hasattr(mat, "active_texture") and context.scene.render.engine == "POVRAY_RENDER":
            tex = mat.active_texture
            if tex and context.space_data.tree_type == "TextureNodeTree":
                self.layout.prop(tex.pov, "texture_use_nodes")


# ------------------------------------------------------------------------------ #
# --------------------------------- Operators ---------------------------------- #
# ------------------------------------------------------------------------------ #


class NODE_OT_iso_add(Operator):
    bl_idname = "pov.nodeisoadd"
    bl_label = "Create iso props"

    def execute(self, context):
        ob = bpy.context.object
        if not bpy.context.scene.use_nodes:
            bpy.context.scene.use_nodes = True
        tree = bpy.context.scene.node_tree
        for node in tree.nodes:
            if node.bl_idname == "IsoPropsNode" and node.label == ob.name:
                tree.nodes.remove(node)
        isonode = tree.nodes.new("IsoPropsNode")
        isonode.location = (0, 0)
        isonode.label = ob.name
        return {"FINISHED"}


class NODE_OT_map_create(Operator):
    bl_idname = "node.map_create"
    bl_label = "Create map"

    def execute(self, context):
        x = y = 0
        space = context.space_data
        tree = space.edit_tree
        for node in tree.nodes:
            if node.select:
                x, y = node.location
            node.select = False
        tmap = tree.nodes.new("ShaderTextureMapNode")
        tmap.location = (x - 200, y)
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        mat = context.object.active_material
        layout.prop(mat.pov, "inputs_number")


class NODE_OT_povray_node_texture_map_add(Operator):
    bl_idname = "pov.nodetexmapadd"
    bl_label = "Texture map"

    def execute(self, context):
        tree = bpy.context.object.active_material.node_tree
        tmap = tree.nodes.active
        mtl = context.object.active_material
        mtl.node_tree.nodes.active = tmap
        el = tmap.color_ramp.elements.new(0.5)
        for el in tmap.color_ramp.elements:
            el.color = (0, 0, 0, 1)
        for inp in tmap.inputs:
            tmap.inputs.remove(inp)
        for outp in tmap.outputs:
            tmap.outputs.remove(outp)
        pattern = tmap.inputs.new("NodeSocketVector", "Pattern")
        pattern.hide_value = True
        for i in range(3):
            tmap.inputs.new("NodeSocketColor", "Shader")
        tmap.outputs.new("NodeSocketShader", "BSDF")
        tmap.label = "Texture Map"
        return {"FINISHED"}


class NODE_OT_povray_node_output_add(Operator):
    bl_idname = "pov.nodeoutputadd"
    bl_label = "Output"

    def execute(self, context):
        tree = bpy.context.object.active_material.node_tree
        tmap = tree.nodes.new("ShaderNodeOutputMaterial")
        mtl = context.object.active_material
        mtl.node_tree.nodes.active = tmap
        for inp in tmap.inputs:
            tmap.inputs.remove(inp)
        tmap.inputs.new("NodeSocketShader", "Surface")
        tmap.label = "Output"
        return {"FINISHED"}


class NODE_OT_povray_node_layered_add(Operator):
    bl_idname = "pov.nodelayeredadd"
    bl_label = "Layered material"

    def execute(self, context):
        tree = bpy.context.object.active_material.node_tree
        tmap = tree.nodes.new("ShaderNodeAddShader")
        mtl = context.object.active_material
        mtl.node_tree.nodes.active = tmap
        tmap.label = "Layered material"
        return {"FINISHED"}


class NODE_OT_povray_input_add(Operator):
    bl_idname = "pov.nodeinputadd"
    bl_label = "Add entry"

    def execute(self, context):
        mtl = context.object.active_material
        node = mtl.node_tree.nodes.active
        if node.type == "VALTORGB":
            number = 1
            for inp in node.inputs:
                if inp.type == "SHADER":
                    number += 1
            node.inputs.new("NodeSocketShader", "%s" % number)
            els = node.color_ramp.elements
            pos1 = els[len(els) - 1].position
            pos2 = els[len(els) - 2].position
            pos = (pos1 - pos2) / 2 + pos2
            el = els.new(pos)

        if node.bl_idname == "PovraySlopeNode":
            number = len(node.inputs)
            node.inputs.new("PovraySocketSlope", "%s" % number)

        return {"FINISHED"}


class NODE_OT_povray_input_remove(Operator):
    bl_idname = "pov.nodeinputremove"
    bl_label = "Remove input"

    def execute(self, context):
        mtl = context.object.active_material
        node = mtl.node_tree.nodes.active
        if node.type in {"VALTORGB", "ADD_SHADER"}:
            number = len(node.inputs) - 1
            if number > 5:
                inp = node.inputs[number]
                node.inputs.remove(inp)
                if node.type == "VALTORGB":
                    els = node.color_ramp.elements
                    number = len(els) - 2
                    el = els[number]
                    els.remove(el)
        return {"FINISHED"}


class NODE_OT_povray_image_open(Operator):
    bl_idname = "pov.imageopen"
    bl_label = "Open"

    filepath: StringProperty(
        name="File Path", description="Open image", maxlen=1024, subtype="FILE_PATH"
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        im = bpy.data.images.load(self.filepath)
        mtl = context.object.active_material
        node = mtl.node_tree.nodes.active
        node.image = im.name
        return {"FINISHED"}


# class TEXTURE_OT_povray_open_image(Operator):
# bl_idname = "pov.openimage"
# bl_label = "Open Image"

# filepath = StringProperty(
# name="File Path",
# description="Open image",
# maxlen=1024,
# subtype='FILE_PATH',
# )

# def invoke(self, context, event):
# context.window_manager.fileselect_add(self)
# return {'RUNNING_MODAL'}

# def execute(self, context):
# im=bpy.data.images.load(self.filepath)
# tex = context.texture
# tex.pov.image = im.name
# view_layer = context.view_layer
# view_layer.update()
# return {'FINISHED'}


classes = (
    NODE_MT_POV_map_create,
    NODE_OT_iso_add,
    NODE_OT_map_create,
    NODE_OT_povray_node_texture_map_add,
    NODE_OT_povray_node_output_add,
    NODE_OT_povray_node_layered_add,
    NODE_OT_povray_input_add,
    NODE_OT_povray_input_remove,
    NODE_OT_povray_image_open,
)


def register():
    bpy.types.NODE_HT_header.append(menu_func_nodes)
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.NODE_HT_header.remove(menu_func_nodes)
