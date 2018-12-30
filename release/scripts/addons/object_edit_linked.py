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
    "version": (0, 9, 1),
    "blender": (2, 80, 0),
    "location": "File > External Data > Edit Linked Library",
    "description": "Allows editing of objects linked from a .blend library.",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Object/Edit_Linked_Library",
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
                context.active_object.library is not None)

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

        if targetpath:
            logger.debug(target.name + " is linked to " + targetpath)

            if self.use_autosave:
                if not bpy.data.filepath:
                    # File is not saved on disk, better to abort!
                    self.report({'ERROR'}, "Current file does not exist on disk, we cannot autosave it, aborting")
                    return {'CANCELLED'}
                bpy.ops.wm.save_mainfile()

            settings["original_file"] = bpy.data.filepath
            settings["linked_file"] = bpy.path.abspath(targetpath)

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
    bl_category = "View"
    bl_context = 'objectmode'

    @classmethod
    def poll(cls, context: bpy.context):
        return (context.active_object is not None) or (settings["original_file"] != "")

    def draw_common(self, scene, layout, props):
        props.use_autosave = scene.use_autosave
        props.use_instance = scene.use_instance

        layout.prop(scene, "use_autosave")
        layout.prop(scene, "use_instance")

    def draw(self, context: bpy.context):
        layout = self.layout
        scene = context.scene
        icon = "OUTLINER_DATA_" + context.active_object.type

        target = None

        if context.active_object.proxy:
            target = context.active_object.proxy
        else:
            target = context.active_object.instance_collection

        if settings["original_file"] == "" and (
                (target and
                target.library is not None) or
                context.active_object.library is not None):

            if (target is not None):
                props = layout.operator("object.edit_linked", icon="LINK_BLEND",
                                        text="Edit Library: %s" % target.name)
            else:
                props = layout.operator("object.edit_linked", icon="LINK_BLEND",
                                        text="Edit Library: %s" % context.active_object.name)

            self.draw_common(scene, layout, props)

            if (target is not None):
                layout.label(text="Path: %s" %
                            target.library.filepath)
            else:
                layout.label(text="Path: %s" %
                            context.active_object.library.filepath)

        elif settings["original_file"] != "":

            if scene.use_instance:
                layout.operator("wm.return_to_original",
                                text="Reload Current File",
                                icon="FILE_REFRESH").use_autosave = False

                layout.separator()

                # XXX - This is for nested linked assets... but it only works
                # when launching a new Blender instance. Nested links don't
                # currently work when using a single instance of Blender.
                props = layout.operator("object.edit_linked",
                                        text="Edit Library: %s" % context.active_object.instance_collection.name,
                                        icon="LINK_BLEND")

                self.draw_common(scene, layout, props)

                layout.label(text="Path: %s" %
                            context.active_object.instance_collection.library.filepath)

            else:
                props = layout.operator("wm.return_to_original", icon="LOOP_BACK")
                props.use_autosave = scene.use_autosave

                layout.prop(scene, "use_autosave")

        else:
            layout.label(text="%s is not linked" % context.active_object.name,
                        icon=icon)


class TOPBAR_MT_edit_linked_submenu(bpy.types.Menu):
    bl_label = 'Edit Linked Library'
    bl_idname = 'view3d.TOPBAR_MT_edit_linked_submenu'

    def draw(self, context):
        self.layout.separator()
        self.layout.operator(OBJECT_OT_EditLinked.bl_idname)
        self.layout.operator(WM_OT_ReturnToOriginal.bl_idname)


addon_keymaps = []
classes = (
    OBJECT_OT_EditLinked,
    WM_OT_ReturnToOriginal,
    VIEW3D_PT_PanelLinkedEdit,
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

    # Keymapping (deactivated by default; activated when a library object is selected)
    kc = bpy.context.window_manager.keyconfigs.addon 
    if kc: # don't register keymaps from command line
        km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')
        kmi = km.keymap_items.new("object.edit_linked", 'NUMPAD_SLASH', 'PRESS', shift=True)
        kmi.active = True
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new("wm.return_to_original", 'NUMPAD_SLASH', 'PRESS', shift=True)
        kmi.active = True
        addon_keymaps.append((km, kmi))


def unregister():

    bpy.app.handlers.load_post.remove(linked_file_check) 
    bpy.types.TOPBAR_MT_file_external_data.remove(TOPBAR_MT_edit_linked_submenu) 

    del bpy.types.Scene.use_autosave
    del bpy.types.Scene.use_instance

    # handle the keymap
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for c in reversed(classes):
        bpy.utils.unregister_class(c)


if __name__ == "__main__":
    register()
