# ##### BEGIN GPL LICENSE BLOCK #####
#
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
#
# ##### END GPL LICENSE BLOCK #####
# Contributed to by: meta-androcto, JayDez, sim88, sam, lijenstina, mkb, wisaac, CoDEmanX #


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


# Object Menus #

# ********** Object Menu **********
class VIEW3D_MT_Object(Menu):
    bl_context = "objectmode"
    bl_label = "Object"

    def draw(self, context):
        layout = self.layout
        view = context.space_data
        is_local_view = (view.local_view is not None)

        layout.operator("object.delete", text="Delete...").use_global = False
        layout.separator()
        layout.menu("VIEW3D_MT_object_parent")
        layout.menu("VIEW3D_MT_Duplicate")
        layout.operator("object.join")

        if is_local_view:
            layout.operator_context = 'EXEC_REGION_WIN'
            layout.operator("object.move_to_layer", text="Move out of Local View")
            layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu("VIEW3D_MT_make_links", text="Make Links...")
        layout.menu("VIEW3D_MT_Object_Data_Link")
        layout.separator()
        layout.menu("VIEW3D_MT_AutoSmooth", icon='ALIASED')
        layout.separator()
        layout.menu("VIEW3D_MT_object_constraints")
        layout.menu("VIEW3D_MT_object_track")
        layout.menu("VIEW3D_MT_object_animation")
        layout.separator()
        layout.menu("VIEW3D_MT_object_showhide")
        layout.separator()
        layout.operator_menu_enum("object.convert", "target")


# ********** Add Menu **********
class VIEW3D_MT_AddMenu(Menu):
    bl_label = "Add Object"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'

        layout.menu("VIEW3D_MT_mesh_add", text="Add Mesh",
                    icon='OUTLINER_OB_MESH')
        layout.menu("VIEW3D_MT_curve_add", text="Add Curve",
                    icon='OUTLINER_OB_CURVE')
        layout.menu("VIEW3D_MT_surface_add", text="Add Surface",
                    icon='OUTLINER_OB_SURFACE')
        layout.operator_menu_enum("object.metaball_add", "type",
                                  icon='OUTLINER_OB_META')
        layout.operator("object.text_add", text="Add Text",
                        icon='OUTLINER_OB_FONT')
        layout.operator_menu_enum("object.gpencil_add", "type", text="Grease Pencil", icon='OUTLINER_OB_GREASEPENCIL')
        layout.separator()
        layout.menu("VIEW3D_MT_armature_add", text="Add Armature",
                    icon='OUTLINER_OB_ARMATURE')
        layout.operator("object.add", text="Lattice",
                        icon='OUTLINER_OB_LATTICE').type = 'LATTICE'
        layout.separator()

        layout.operator_menu_enum("object.empty_add", "type", text="Empty", icon='OUTLINER_OB_EMPTY')
        layout.menu("VIEW3D_MT_image_add", text="Image", icon='OUTLINER_OB_IMAGE')
        layout.separator()

        layout.operator_menu_enum("object.light_add", "type",
                                  icon="OUTLINER_OB_LIGHT")
        layout.menu("VIEW3D_MT_lightprobe_add", icon='OUTLINER_OB_LIGHTPROBE')
        layout.separator()
        
        layout.operator("object.camera_add", text="Camera",
                        icon='OUTLINER_OB_CAMERA')
        layout.separator()

        layout.operator("object.speaker_add", text="Speaker", icon='OUTLINER_OB_SPEAKER')
        layout.separator()

        layout.operator_menu_enum("object.effector_add", "type",
                                  text="Force Field",
                                  icon='FORCE_FORCE')
        layout.menu("VIEW3D_MT_object_quick_effects", text="Quick Effects", icon='PARTICLES')
        layout.separator()

        has_collections = bool(bpy.data.collections)
        col = layout.column()
        col.enabled = has_collections

        if not has_collections or len(bpy.data.collections) > 10:
            col.operator_context = 'INVOKE_REGION_WIN'
            col.operator(
                "object.collection_instance_add",
                text="Collection Instance..." if has_collections else "No Collections to Instance",
                icon='OUTLINER_OB_GROUP_INSTANCE',
            )
        else:
            col.operator_menu_enum(
                "object.collection_instance_add",
                "collection",
                text="Collection Instance",
                icon='OUTLINER_OB_GROUP_INSTANCE',
            )


# ********** Object Mirror **********
class VIEW3D_MT_MirrorMenu(Menu):
    bl_label = "Mirror"

    def draw(self, context):
        layout = self.layout
        layout.operator("transform.mirror", text="Interactive Mirror")
        layout.separator()
        layout.operator_context = 'INVOKE_REGION_WIN'
        props = layout.operator("transform.mirror", text="X Global")
        props.constraint_axis = (True, False, False)
        props.orient_type = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Y Global")
        props.constraint_axis = (False, True, False)
        props.orient_type = 'GLOBAL'
        props = layout.operator("transform.mirror", text="Z Global")
        props.constraint_axis = (False, False, True)
        props.orient_type = 'GLOBAL'


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


# ********** Object Parent **********
class VIEW3D_MT_ParentMenu(Menu):
    bl_label = "Parent"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.parent_set", text="Set")
        layout.operator("object.parent_clear", text="Clear")


# ********** Object Group **********
class VIEW3D_MT_GroupMenu(Menu):
    bl_label = "Group"

    def draw(self, context):
        layout = self.layout
        layout.operator("collection.create")
        layout.operator("collection.objects_add_active")
        layout.separator()
        layout.operator("collection.objects_remove")
        layout.operator("collection.objects_remove_all")
        layout.operator("collection.objects_remove_active")


# ********** Object Camera Options **********
class VIEW3D_MT_Camera_Options(Menu):
    bl_label = "Camera"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'EXEC_REGION_WIN'
        layout.operator("object.camera_add", text="Add Camera", icon='OUTLINER_OB_CAMERA')
        layout.operator("view3d.object_as_camera", text="Object As Camera", icon='OUTLINER_OB_CAMERA')

class VIEW3D_MT_Object_Data_Link(Menu):
    bl_label = "Object Data"

    def draw(self, context):
        layout = self.layout

        layout.operator_menu_enum("object.make_local", "type", text="Make Local...")
        layout.menu("VIEW3D_MT_make_single_user")
        layout.operator("object.proxy_make", text="Make Proxy...")
        layout.operator("object.make_dupli_face")
        layout.separator()
        layout.operator("object.data_transfer")
        layout.operator("object.datalayout_transfer")


class VIEW3D_MT_Duplicate(Menu):
    bl_label = "Duplicate"

    def draw(self, context):
        layout = self.layout

        layout.operator("object.duplicate_move")
        layout.operator("object.duplicate_move_linked")


class VIEW3D_MT_KeyframeMenu(Menu):
    bl_label = "Keyframe"

    def draw(self, context):
        layout = self.layout
        layout.operator("anim.keyframe_insert_menu",
                        text="Insert Keyframe...")
        layout.operator("anim.keyframe_delete_v3d",
                        text="Delete Keyframe...")
        layout.operator("anim.keying_set_active_set",
                        text="Change Keying Set...")


class VIEW3D_MT_UndoS(Menu):
    bl_label = "Undo/Redo"

    def draw(self, context):
        layout = self.layout

        layout.operator("ed.undo")
        layout.operator("ed.redo")
        layout.separator()
        layout.operator("ed.undo_history")


# Display Wire (Thanks to marvin.k.breuer) #
class VIEW3D_OT_Display_Wire_All(Operator):
    bl_label = "Wire on All Objects"
    bl_idname = "view3d.display_wire_all"
    bl_description = "Enable/Disable Display Wire on All Objects"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        is_error = False
        for obj in bpy.data.objects:
            try:
                if obj.show_wire:
                    obj.show_all_edges = False
                    obj.show_wire = False
                else:
                    obj.show_all_edges = True
                    obj.show_wire = True
            except:
                is_error = True
                pass

        if is_error:
            self.report({'WARNING'},
                        "Wire on All Objects could not be completed for some objects")

        return {'FINISHED'}


# Matcap and AO, Wire all and X-Ray entries thanks to marvin.k.breuer
class VIEW3D_MT_Shade(Menu):
    bl_label = "Shade"

    def draw(self, context):
        layout = self.layout

#        layout.prop(context.space_data, "viewport_shade", expand=True)

        if context.active_object:
            if(context.mode == 'EDIT_MESH'):
                layout.operator("MESH_OT_faces_shade_smooth", icon='SHADING_RENDERED')
                layout.operator("MESH_OT_faces_shade_flat", icon='SHADING_SOLID')
            else:
                layout.operator("OBJECT_OT_shade_smooth", icon='SHADING_RENDERED')
                layout.operator("OBJECT_OT_shade_flat", icon='SHADING_SOLID')

        layout.separator()
        layout.operator("view3d.display_wire_all", text="Wire all", icon='SHADING_WIRE')
        layout.prop(context.object, "show_in_front", text="X-Ray", icon="META_CUBE")

        layout.separator()
        layout.prop(context.space_data.fx_settings, "use_ssao",
                    text="Ambient Occlusion", icon="GROUP")
#        layout.prop(context.space_data, "use_matcap", icon="MATCAP_01")

#        if context.space_data.use_matcap:
#            row = layout.column(1)
#            row.scale_y = 0.3
#            row.scale_x = 0.5
#            row.template_icon_view(context.space_data, "matcap_icon")


# Animation Player (Thanks to marvin.k.breuer) #
class VIEW3D_MT_Animation_Player(Menu):
    bl_label = "Animation"

    def draw(self, context):
        layout = self.layout

        layout.operator("screen.frame_jump", text="Jump REW", icon='REW').end = False
        layout.operator("screen.keyframe_jump", text="Previous FR", icon='PREV_KEYFRAME').next = False

        layout.separator()
        layout.operator("screen.animation_play", text="Reverse", icon='PLAY_REVERSE').reverse = True
        layout.operator("screen.animation_play", text="PLAY", icon='PLAY')
        layout.operator("screen.animation_play", text="Stop", icon='PAUSE')
        layout.separator()

        layout.operator("screen.keyframe_jump", text="Next FR", icon='NEXT_KEYFRAME').next = True
        layout.operator("screen.frame_jump", text="Jump FF", icon='FF').end = True
        layout.menu("VIEW3D_MT_KeyframeMenu", text="Keyframes", icon='DECORATE_ANIMATE')


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



# List The Classes #

classes = (
    VIEW3D_MT_AddMenu,
    VIEW3D_MT_Object,
    VIEW3D_MT_MirrorMenu,
    VIEW3D_MT_ParentMenu,
    VIEW3D_MT_GroupMenu,
    VIEW3D_MT_KeyframeMenu,
    VIEW3D_MT_UndoS,
    VIEW3D_MT_Camera_Options,
    VIEW3D_MT_InteractiveMode,
    VIEW3D_MT_InteractiveModeOther,
    VIEW3D_OT_SetObjectMode,
    VIEW3D_MT_Shade,
    VIEW3D_MT_Object_Data_Link,
    VIEW3D_MT_Duplicate,
    VIEW3D_MT_Animation_Player,
    VIEW3D_OT_Interactive_Mode_Text,
    VIEW3D_OT_Display_Wire_All,
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
