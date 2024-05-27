# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import (
        Operator,
        Menu,
        )
from bpy.props import (
        BoolProperty,
        StringProperty,
        )

from bl_ui.properties_paint_common import UnifiedPaintPanel

from . edit_mesh import *
from . view_menus import *
# Object Menus #

# ********** Object Menu **********
class VIEW3D_MT_Object(Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        view = context.space_data

        layout.menu("VIEW3D_MT_mirror")
        layout.menu("VIEW3D_MT_object_parent")
        layout.menu("VIEW3D_MT_Duplicate")
        layout.operator("object.join")
        layout.menu("VIEW3D_MT_make_links", text="Make Links")
        layout.menu("VIEW3D_MT_object_relations")
        layout.separator()

        ob = context.active_object
        if ob and ob.type == 'GPENCIL' and context.gpencil_data:
            layout.operator_menu_enum("gpencil.convert", "type", text="Convert to")
        else:
            layout.operator_menu_enum("object.convert", "target")

        layout.menu("VIEW3D_MT_object_showhide")
        layout.separator()

        layout.menu("VIEW3D_MT_object_constraints")
        layout.menu("VIEW3D_MT_object_track")
        layout.separator()

        layout.menu("VIEW3D_MT_object_rigid_body")
        layout.menu("VIEW3D_MT_object_quick_effects")
        layout.separator()

        layout.operator("view3d.copybuffer", text="Copy Objects", icon='COPYDOWN')
        layout.operator("view3d.pastebuffer", text="Paste Objects", icon='PASTEDOWN')
        layout.separator()

        layout.operator_context = 'EXEC_DEFAULT'
        layout.operator("object.delete", text="Delete").use_global = False
        layout.operator("object.delete", text="Delete Global").use_global = True


# ********** Object Interactive Mode **********
class VIEW3D_MT_InteractiveMode(Menu):
    bl_label = "Interactive Mode"
    bl_description = "Menu of objects' interactive modes (Window Types)"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        psys = hasattr(obj, "particle_systems")
        psys_items = len(obj.particle_systems.items()) > 0 if psys else False

        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Edit", icon="EDITMODE_HLT").mode = "EDIT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Sculpt", icon="SCULPTMODE_HLT").mode = "SCULPT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Vertex Paint", icon="VPAINT_HLT").mode = "VERTEX_PAINT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Weight Paint", icon="WPAINT_HLT").mode = "WEIGHT_PAINT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Texture Paint", icon="TPAINT_HLT").mode = "TEXTURE_PAINT"
        if obj and psys_items:
            layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Particle Edit",
                            icon="PARTICLEMODE").mode = "PARTICLE_EDIT"
#        if context.gpencil_data:
#            layout.operator("view3d.interactive_mode_grease_pencil", icon="GREASEPENCIL")


# ********** Interactive Mode Other **********
class VIEW3D_MT_InteractiveModeOther(Menu):
    bl_idname = "VIEW3D_MT_Object_Interactive_Other"
    bl_label = "Interactive Mode"
    bl_description = "Menu of objects interactive mode"

    def draw(self, context):
        layout = self.layout
        layout.operator("object.editmode_toggle", text="Edit/Object Toggle",
                        icon='OBJECT_DATA')


# ********** Grease Pencil Interactive Mode **********
class VIEW3D_OT_Interactive_Mode_Grease_Pencil(Operator):
    bl_idname = "view3d.interactive_mode_grease_pencil"
    bl_label = "Edit Strokes"
    bl_description = "Toggle Edit Strokes for Grease Pencil"

    @classmethod
    def poll(cls, context):
        return (context.gpencil_data is not None)

    def execute(self, context):
        try:
            bpy.ops.gpencil.editmode_toggle()
        except:
            self.report({'WARNING'}, "It is not possible to enter into the interactive mode")
        return {'FINISHED'}

class VIEW3D_MT_Interactive_Mode_GPencil(Menu):
    bl_idname = "VIEW3D_MT_interactive_mode_gpencil"
    bl_label = "Interactive Mode"
    bl_description = "Menu of objects interactive mode"

    def draw(self, context):
        toolsettings = context.tool_settings
        layout = self.layout
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Object", icon="OBJECT_DATAMODE").mode = "OBJECT"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Edit", icon="EDITMODE_HLT").mode = "EDIT_GPENCIL"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Sculpt", icon="SCULPTMODE_HLT").mode = "SCULPT_GPENCIL"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Draw", icon="GREASEPENCIL").mode = "PAINT_GPENCIL"
        layout.operator(VIEW3D_OT_SetObjectMode.bl_idname, text="Weight Paint", icon="WPAINT_HLT").mode = "WEIGHT_GPENCIL"


# ********** Text Interactive Mode **********
class VIEW3D_OT_Interactive_Mode_Text(Operator):
    bl_idname = "view3d.interactive_mode_text"
    bl_label = "Enter Edit Mode"
    bl_description = "Toggle object's editmode"

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def execute(self, context):
        bpy.ops.object.editmode_toggle()
        self.report({'INFO'}, "Spacebar shortcut won't work in the Text Edit mode")
        return {'FINISHED'}


# ********** Object Camera Options **********
class VIEW3D_MT_Camera_Options(Menu):
    bl_label = "Camera"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.select_camera", text="Select Camera")
        layout.operator("object.camera_add", text="Add Camera")
        layout.operator("view3d.view_camera", text="View Camera")
        layout.operator("view3d.camera_to_view", text="Camera to View")
        layout.operator("view3d.camera_to_view_selected", text="Camera to Selected")
        layout.operator("view3d.object_as_camera", text="Object As Camera")


class VIEW3D_MT_Duplicate(Menu):
    bl_label = "Duplicate"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.duplicate_move")
        layout.operator("object.duplicate_move_linked")


class VIEW3D_MT_UndoS(Menu):
    bl_label = "Undo/Redo"

    def draw(self, context):
        layout = self.layout

        layout.operator("ed.undo")
        layout.operator("ed.redo")
        layout.separator()
        layout.operator("ed.undo_history")


# Set Mode Operator #
class VIEW3D_OT_SetObjectMode(Operator):
    bl_idname = "object.set_object_mode"
    bl_label = "Set the object interactive mode"
    bl_description = "I set the interactive mode of object"
    bl_options = {'REGISTER'}

    mode: StringProperty(
                    name="Interactive mode",
                    default="OBJECT"
                    )

    def execute(self, context):
        if (context.active_object):
            try:
                bpy.ops.object.mode_set(mode=self.mode)
            except TypeError:
                msg = context.active_object.name + ": It is not possible to enter into the interactive mode"
                self.report(type={"WARNING"}, message=msg)
        else:
            self.report(type={"WARNING"}, message="There is no active object")
        return {'FINISHED'}


# currently unused
class VIEW3D_MT_Edit_Gpencil(Menu):
    bl_label = "GPencil"

    def draw(self, context):
        toolsettings = context.tool_settings
        layout = self.layout

        layout.operator("gpencil.brush_paint", text="Sculpt Strokes").wait_for_input = True
        layout.prop_menu_enum(toolsettings.gpencil_sculpt, "tool", text="Sculpt Brush")
        layout.separator()
        layout.menu("VIEW3D_MT_edit_gpencil_transform")
        layout.operator("transform.mirror", text="Mirror")
        layout.menu("GPENCIL_MT_snap")
        layout.separator()
        layout.menu("VIEW3D_MT_object_animation")   # NOTE: provides keyingset access...
        layout.separator()
        layout.menu("VIEW3D_MT_edit_gpencil_delete")
        layout.operator("gpencil.duplicate_move", text="Duplicate")
        layout.separator()
        layout.menu("VIEW3D_MT_select_gpencil")
        layout.separator()
        layout.operator("gpencil.copy", text="Copy")
        layout.operator("gpencil.paste", text="Paste")
        layout.separator()
        layout.prop_menu_enum(toolsettings, "proportional_edit")
        layout.prop_menu_enum(toolsettings, "proportional_edit_falloff")
        layout.separator()
        layout.operator("gpencil.reveal")
        layout.operator("gpencil.hide", text="Show Active Layer Only").unselected = True
        layout.operator("gpencil.hide", text="Hide Active Layer").unselected = False
        layout.separator()
        layout.operator_menu_enum("gpencil.move_to_layer", "layer", text="Move to Layer")
        layout.operator_menu_enum("gpencil.convert", "type", text="Convert to Geometry...")


# List The Classes #

classes = (
    VIEW3D_MT_Object,
    VIEW3D_MT_UndoS,
    VIEW3D_MT_Camera_Options,
    VIEW3D_MT_InteractiveMode,
    VIEW3D_MT_InteractiveModeOther,
    VIEW3D_OT_SetObjectMode,
    VIEW3D_MT_Duplicate,
    VIEW3D_OT_Interactive_Mode_Text,
    VIEW3D_OT_Interactive_Mode_Grease_Pencil,
    VIEW3D_MT_Interactive_Mode_GPencil,
    VIEW3D_MT_Edit_Gpencil,
)


# Register Classes & Hotkeys #
def register():
    for cls in classes:
        bpy.utils.register_class(cls)


# Unregister Classes & Hotkeys #
def unregister():

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
