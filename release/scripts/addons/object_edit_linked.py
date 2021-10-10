# ***** BEGIN GPL LICENSE BLOCK *****
#
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
# ***** END GPL LICENCE BLOCK *****

bl_info = {
    "name": "Edit Linked Library",
    "author": "Jason van Gumster (Fweeb), Bassam Kurdali, Pablo Vazquez, Rainer Trummer",
    "version": (0, 9, 2),
    "blender": (2, 80, 0),
    "location": "File > External Data / View3D > Sidebar > Item Tab / Node Editor > Sidebar > Node Tab",
    "description": "Allows editing of objects, collections, and node groups linked from a .blend library.",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/object/edit_linked_library.html",
    "category": "Object",
}

import bpy
import logging
import os

from bpy.app.handlers import persistent

logger = logging.getLogger('object_edit_linked')

settings = {
    "original_file": "",
    "linked_file": "",
    "linked_objects": [],
    "linked_nodes": []
    }


@persistent
def linked_file_check(context: bpy.context):
    if settings["linked_file"] != "":
        if os.path.samefile(settings["linked_file"], bpy.data.filepath):
            logger.info("Editing a linked library.")
            bpy.ops.object.select_all(action='DESELECT')
            for ob_name in settings["linked_objects"]:
                bpy.data.objects[ob_name].select_set(True) # XXX Assumes selected object is in the active scene
            if len(settings["linked_objects"]) == 1:
                context.view_layer.objects.active = bpy.data.objects[settings["linked_objects"][0]]
        else:
            # For some reason, the linked editing session ended
            # (failed to find a file or opened a different file
            # before returning to the originating .blend)
            settings["original_file"] = ""
            settings["linked_file"] = ""


class OBJECT_OT_EditLinked(bpy.types.Operator):
    """Edit Linked Library"""
    bl_idname = "object.edit_linked"
    bl_label = "Edit Linked Library"

    use_autosave: bpy.props.BoolProperty(
            name="Autosave",
            description="Save the current file before opening the linked library",
            default=True)
    use_instance: bpy.props.BoolProperty(
            name="New Blender Instance",
            description="Open in a new Blender instance",
            default=False)

    @classmethod
    def poll(cls, context: bpy.context):
        return settings["original_file"] == "" and context.active_object is not None and (
                (context.active_object.instance_collection and
                context.active_object.instance_collection.library is not None) or
                (context.active_object.proxy and
                context.active_object.proxy.library is not None) or
                context.active_object.library is not None or
                (context.active_object.override_library and
                context.active_object.override_library.reference.library is not None))

    def execute(self, context: bpy.context):
        target = context.active_object

        if target.instance_collection and target.instance_collection.library:
            targetpath = target.instance_collection.library.filepath
            settings["linked_objects"].extend({ob.name for ob in target.instance_collection.objects})
        elif target.library:
            targetpath = target.library.filepath
            settings["linked_objects"].append(target.name)
        elif target.proxy:
            target = target.proxy
            targetpath = target.library.filepath
            settings["linked_objects"].append(target.name)
        elif target.override_library:
            target = target.override_library.reference
            targetpath = target.library.filepath
            settings["linked_objects"].append(target.name)

        if targetpath:
            logger.debug(target.name + " is linked to " + targetpath)

            if self.use_autosave:
                if not bpy.data.filepath:
                    # File is not saved on disk, better to abort!
                    self.report({'ERROR'}, "Current file does not exist on disk, we cannot autosave it, aborting")
                    return {'CANCELLED'}
                bpy.ops.wm.save_mainfile()

            settings["original_file"] = bpy.data.filepath
            # Using both bpy and os abspath functions because Windows doesn't like relative routes as part of an absolute path
            settings["linked_file"] = os.path.abspath(bpy.path.abspath(targetpath))

            if self.use_instance:
                import subprocess
                try:
                    subprocess.Popen([bpy.app.binary_path, settings["linked_file"]])
                except:
                    logger.error("Error on the new Blender instance")
                    import traceback
                    logger.error(traceback.print_exc())
            else:
                bpy.ops.wm.open_mainfile(filepath=settings["linked_file"])

            logger.info("Opened linked file!")
        else:
            self.report({'WARNING'}, target.name + " is not linked")
            logger.warning(target.name + " is not linked")

        return {'FINISHED'}


class NODE_OT_EditLinked(bpy.types.Operator):
    """Edit Linked Library"""
    bl_idname = "node.edit_linked"
    bl_label = "Edit Linked Library"

    use_autosave: bpy.props.BoolProperty(
            name="Autosave",
            description="Save the current file before opening the linked library",
            default=True)
    use_instance: bpy.props.BoolProperty(
            name="New Blender Instance",
            description="Open in a new Blender instance",
            default=False)

    @classmethod
    def poll(cls, context: bpy.context):
        return settings["original_file"] == "" and context.active_node is not None and (
                (context.active_node.type == 'GROUP' and
                hasattr(context.active_node.node_tree, "library") and
                context.active_node.node_tree.library is not None) or
                (hasattr(context.active_node, "monad") and
                context.active_node.monad.library is not None))

    def execute(self, context: bpy.context):
        target = context.active_node
        if (target.type == "GROUP"):
            target = target.node_tree
        else:
            target = target.monad

        targetpath = target.library.filepath
        settings["linked_nodes"].append(target.name)

        if targetpath:
            logger.debug(target.name + " is linked to " + targetpath)

            if self.use_autosave:
                if not bpy.data.filepath:
                    # File is not saved on disk, better to abort!
                    self.report({'ERROR'}, "Current file does not exist on disk, we cannot autosave it, aborting")
                    return {'CANCELLED'}
                bpy.ops.wm.save_mainfile()

            settings["original_file"] = bpy.data.filepath
            # Using both bpy and os abspath functions because Windows doesn't like relative routes as part of an absolute path
            settings["linked_file"] = os.path.abspath(bpy.path.abspath(targetpath))

            if self.use_instance:
                import subprocess
                try:
                    subprocess.Popen([bpy.app.binary_path, settings["linked_file"]])
                except:
                    logger.error("Error on the new Blender instance")
                    import traceback
                    logger.error(traceback.print_exc())
            else:
                bpy.ops.wm.open_mainfile(filepath=settings["linked_file"])

            logger.info("Opened linked file!")
        else:
            self.report({'WARNING'}, target.name + " is not linked")
            logger.warning(target.name + " is not linked")

        return {'FINISHED'}


class WM_OT_ReturnToOriginal(bpy.types.Operator):
    """Load the original file"""
    bl_idname = "wm.return_to_original"
    bl_label = "Return to Original File"

    use_autosave: bpy.props.BoolProperty(
            name="Autosave",
            description="Save the current file before opening original file",
            default=True)

    @classmethod
    def poll(cls, context: bpy.context):
        return (settings["original_file"] != "")

    def execute(self, context: bpy.context):
        if self.use_autosave:
            bpy.ops.wm.save_mainfile()

        bpy.ops.wm.open_mainfile(filepath=settings["original_file"])

        settings["original_file"] = ""
        settings["linked_objects"] = []
        logger.info("Back to the original!")
        return {'FINISHED'}


class VIEW3D_PT_PanelLinkedEdit(bpy.types.Panel):
    bl_label = "Edit Linked Library"
    bl_space_type = "VIEW_3D"
    bl_region_type = 'UI'
    bl_category = "Item"
    bl_context = 'objectmode'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context: bpy.context):
        return (context.active_object is not None) or (settings["original_file"] != "")

    def draw_common(self, scene, layout, props):
        if props is not None:
            props.use_autosave = scene.use_autosave
            props.use_instance = scene.use_instance

            layout.prop(scene, "use_autosave")
            layout.prop(scene, "use_instance")

    def draw(self, context: bpy.context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        icon = "OUTLINER_DATA_" + context.active_object.type.replace("LIGHT_PROBE", "LIGHTPROBE")

        target = None

        if context.active_object.proxy:
            target = context.active_object.proxy
        else:
            target = context.active_object.instance_collection

        if settings["original_file"] == "" and (
                (target and
                target.library is not None) or
                context.active_object.library is not None or
                (context.active_object.override_library is not None and
                context.active_object.override_library.reference is not None)):

            if (target is not None):
                props = layout.operator("object.edit_linked", icon="LINK_BLEND",
                                        text="Edit Library: %s" % target.name)
            elif (context.active_object.library):
                props = layout.operator("object.edit_linked", icon="LINK_BLEND",
                                        text="Edit Library: %s" % context.active_object.name)
            else:
                props = layout.operator("object.edit_linked", icon="LINK_BLEND",
                                        text="Edit Override Library: %s" % context.active_object.override_library.reference.name)

            self.draw_common(scene, layout, props)

            if (target is not None):
                layout.label(text="Path: %s" %
                            target.library.filepath)
            elif (context.active_object.library):
                layout.label(text="Path: %s" %
                            context.active_object.library.filepath)
            else:
                layout.label(text="Path: %s" %
                            context.active_object.override_library.reference.library.filepath)

        elif settings["original_file"] != "":

            if scene.use_instance:
                layout.operator("wm.return_to_original",
                                text="Reload Current File",
                                icon="FILE_REFRESH").use_autosave = False

                layout.separator()

                # XXX - This is for nested linked assets... but it only works
                # when launching a new Blender instance. Nested links don't
                # currently work when using a single instance of Blender.
                if context.active_object.instance_collection is not None:
                    props = layout.operator("object.edit_linked",
                            text="Edit Library: %s" % context.active_object.instance_collection.name,
                            icon="LINK_BLEND")
                else:
                    props = None

                self.draw_common(scene, layout, props)

                if context.active_object.instance_collection is not None:
                    layout.label(text="Path: %s" %
                            context.active_object.instance_collection.library.filepath)

            else:
                props = layout.operator("wm.return_to_original", icon="LOOP_BACK")
                props.use_autosave = scene.use_autosave

                layout.prop(scene, "use_autosave")

        else:
            layout.label(text="%s is not linked" % context.active_object.name,
                        icon=icon)


class NODE_PT_PanelLinkedEdit(bpy.types.Panel):
    bl_label = "Edit Linked Library"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    if bpy.app.version >= (2, 93, 0):
        bl_category = "Node"
    else:
        bl_category = "Item"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_node is not None

    def draw_common(self, scene, layout, props):
        if props is not None:
            props.use_autosave = scene.use_autosave
            props.use_instance = scene.use_instance

            layout.prop(scene, "use_autosave")
            layout.prop(scene, "use_instance")

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        icon = 'NODETREE'

        target = context.active_node

        if settings["original_file"] == "" and (
                (target.type == 'GROUP' and hasattr(target.node_tree, "library") and
                target.node_tree.library is not None) or
                (hasattr(target, "monad") and target.monad.library is not None)):

            if (target.type == "GROUP"):
                props = layout.operator("node.edit_linked", icon="LINK_BLEND",
                                        text="Edit Library: %s" % target.name)
            else:
                props = layout.operator("node.edit_linked", icon="LINK_BLEND",
                                        text="Edit Library: %s" % target.monad.name)

            self.draw_common(scene, layout, props)

            if (target.type == "GROUP"):
                layout.label(text="Path: %s" % target.node_tree.library.filepath)
            else:
                layout.label(text="Path: %s" % target.monad.library.filepath)

        elif settings["original_file"] != "":

            if scene.use_instance:
                layout.operator("wm.return_to_original",
                                text="Reload Current File",
                                icon="FILE_REFRESH").use_autosave = False

                layout.separator()

                props = None

                self.draw_common(scene, layout, props)

                #layout.label(text="Path: %s" %
                #            context.active_object.instance_collection.library.filepath)

            else:
                props = layout.operator("wm.return_to_original", icon="LOOP_BACK")
                props.use_autosave = scene.use_autosave

                layout.prop(scene, "use_autosave")

        else:
            layout.label(text="%s is not linked" % target.name, icon=icon)


class TOPBAR_MT_edit_linked_submenu(bpy.types.Menu):
    bl_label = 'Edit Linked Library'

    def draw(self, context):
        self.layout.separator()
        self.layout.operator(OBJECT_OT_EditLinked.bl_idname)
        self.layout.operator(WM_OT_ReturnToOriginal.bl_idname)


addon_keymaps = []
classes = (
    OBJECT_OT_EditLinked,
    NODE_OT_EditLinked,
    WM_OT_ReturnToOriginal,
    VIEW3D_PT_PanelLinkedEdit,
    NODE_PT_PanelLinkedEdit,
    TOPBAR_MT_edit_linked_submenu
    )


def register():
    bpy.app.handlers.load_post.append(linked_file_check)

    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Scene.use_autosave = bpy.props.BoolProperty(
            name="Autosave",
            description="Save the current file before opening a linked file",
            default=True)

    bpy.types.Scene.use_instance = bpy.props.BoolProperty(
            name="New Blender Instance",
            description="Open in a new Blender instance",
            default=False)

    # add the function to the file menu
    bpy.types.TOPBAR_MT_file_external_data.append(TOPBAR_MT_edit_linked_submenu.draw)




def unregister():

    bpy.app.handlers.load_post.remove(linked_file_check)
    bpy.types.TOPBAR_MT_file_external_data.remove(TOPBAR_MT_edit_linked_submenu)

    del bpy.types.Scene.use_autosave
    del bpy.types.Scene.use_instance


    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
