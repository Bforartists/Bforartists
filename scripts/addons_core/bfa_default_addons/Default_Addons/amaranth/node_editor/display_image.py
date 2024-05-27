# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Display Active Image Node on Image Editor

When selecting an Image node, it will show it on the Image editor (if
there is any available). If you don't like this behavior, you can
disable it from the Amaranth Toolset panel on the Scene properties.
Coded by the awesome Sergey Sharybin. This feature only works on Blender
2.68 and newer. Select an Image Node in the Compositor or Cycles nodes
editor, there must be at least one image editor available.
"""

import bpy


KEYMAPS = list()

image_nodes = ("CompositorNodeRLayers",
               "CompositorNodeImage",
               "CompositorNodeViewer",
               "CompositorNodeComposite",
               "ShaderNodeTexImage",
               "ShaderNodeTexEnvironment",
               "GeometryNodeImageTexture")


class AMTH_NODE_OT_show_active_node_image(bpy.types.Operator):
    """Display source image in the Image Editor (if available)"""
    bl_idname = "node.show_active_node_image"
    bl_label = "Open Node Source Image"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.space_data.type == 'NODE_EDITOR' \
            and context.active_node is not None \
            and context.active_node.bl_idname in image_nodes

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        mlocx = event.mouse_region_x
        mlocy = event.mouse_region_y
        select_node = bpy.ops.node.select(location=(mlocx, mlocy), extend=False)

        if 'FINISHED' in select_node:  # Only run if we're clicking on a node
            get_addon = "amaranth" in context.preferences.addons.keys()
            if not get_addon:
                return {"CANCELLED"}

            preferences = context.preferences.addons["amaranth"].preferences
            if preferences.use_image_node_display:
                if context.active_node:
                    active_node = context.active_node

                    if active_node.bl_idname in image_nodes:
                        # Use largest image editor
                        area = None
                        area_size = 0
                        for a in context.screen.areas:
                            if a.type == "IMAGE_EDITOR":
                                size = a.width * a.height
                                if size > area_size:
                                    area_size = size
                                    area = a
                        if area:
                            for space in area.spaces:
                                if space.type == "IMAGE_EDITOR":
                                    if active_node.bl_idname == "CompositorNodeViewer":
                                        space.image = bpy.data.images[
                                            "Viewer Node"]
                                    elif active_node.bl_idname in ["CompositorNodeComposite", "CompositorNodeRLayers"]:
                                        space.image = bpy.data.images[
                                            "Render Result"]
                                    elif active_node.bl_idname == "GeometryNodeImageTexture":
                                        if active_node.inputs['Image'].is_linked:
                                            self.report({'INFO'}, "Previewing linked sockets is not supported yet")
                                            break
                                        if active_node.inputs['Image'].default_value:
                                            space.image = active_node.inputs['Image'].default_value
                                    elif active_node.image:
                                        space.image = active_node.image
                                    else:
                                        self.report({'INFO'}, "No image detected")
                                        break
                                break
                        else:
                            return {'CANCELLED'}

            return {"FINISHED"}
        else:
            return {"PASS_THROUGH"}


def ui(self, context):
    node = context.active_node

    if node is not None and node.bl_idname in image_nodes:
        self.layout.separator()
        self.layout.operator_context = 'INVOKE_DEFAULT'
        self.layout.operator(
            AMTH_NODE_OT_show_active_node_image.bl_idname,
            icon="IMAGE", text="Display in Image Editor")


def register():
    bpy.utils.register_class(AMTH_NODE_OT_show_active_node_image)

    kc = bpy.context.window_manager.keyconfigs.addon
    if kc is not None:
        km = kc.keymaps.new(name="Node Editor", space_type="NODE_EDITOR")
        kmi = km.keymap_items.new("node.show_active_node_image",
                                  "LEFTMOUSE", "DOUBLE_CLICK")
        KEYMAPS.append((km, kmi))

    bpy.types.NODE_MT_node.append(ui)
    bpy.types.NODE_MT_context_menu.append(ui)


def unregister():
    bpy.utils.unregister_class(AMTH_NODE_OT_show_active_node_image)
    for km, kmi in KEYMAPS:
        km.keymap_items.remove(kmi)
    KEYMAPS.clear()

    bpy.types.NODE_MT_node.remove(ui)
    bpy.types.NODE_MT_context_menu.remove(ui)
