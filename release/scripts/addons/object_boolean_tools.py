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

# <pep8 compliant>

bl_info = {
    "name": "Bool Tool",
    "author": "Vitor Balbio, Mikhail Rachinskiy, TynkaTopi, Meta-Androcto, Simon Appelt",
    "version": (0, 4, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Edit Tab",
    "description": "Bool Tool Hotkey: Ctrl Shift B",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/object/bool_tools.html",
    "category": "Object",
}

import bpy
from bpy.types import (
    AddonPreferences,
    Operator,
    Panel,
    Menu,
)
from bpy.props import (
    BoolProperty,
    StringProperty,
)


# -------------------  Bool Tool FUNCTIONS -------------------------
# Utils:

# Hide boolean objects
def update_BoolHide(self, context):
    ao = context.view_layer.objects.active
    objs = [i.object for i in ao.modifiers if i.type == "BOOLEAN"]
    hide_state = context.scene.BoolHide

    for o in objs:
        o.hide_viewport = hide_state


def isCanvas(_obj):
    try:
        if _obj["BoolToolRoot"]:
            return True
    except:
        return False


def isBrush(_obj):
    try:
        if _obj["BoolToolBrush"]:
            return True
    except:
        return False


# TODO
# def isPolyBrush(_obj):
#     try:
#         if _obj["BoolToolPolyBrush"]:
#             return True
#     except:
#         return False


def object_visibility_set(ob, value=False):
    ob.visible_camera = value
    ob.visible_diffuse = value
    ob.visible_glossy = value
    ob.visible_shadow = value
    ob.visible_transmission = value
    ob.visible_volume_scatter = value


def BT_ObjectByName(obj):
    for ob in bpy.context.view_layer.objects:
        if isCanvas(ob) or isBrush(ob):
            if ob.name == obj:
                return ob


def FindCanvas(obj):
    for ob in bpy.context.view_layer.objects:
        if isCanvas(ob):
            for mod in ob.modifiers:
                if "BTool_" in mod.name:
                    if obj.name in mod.name:
                        return ob


def isFTransf():
    preferences = bpy.context.preferences
    addons = preferences.addons
    addon_prefs = addons[__name__].preferences
    if addon_prefs.fast_transform:
        return True
    else:
        return False


def ConvertToMesh(obj):
    act = bpy.context.view_layer.objects.active
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    bpy.context.view_layer.objects.active = act


# Do the Union, Difference and Intersection Operations with a Brush
def Operation(context, _operation):
    prefs = context.preferences.addons[__name__].preferences
    useWire = prefs.use_wire

    for selObj in context.selected_objects:
        if (
            selObj != context.active_object and
            (selObj.type == "MESH" or selObj.type == "CURVE")
        ):
            if selObj.type == "CURVE":
                ConvertToMesh(selObj)
            actObj = context.active_object
            selObj.hide_render = True

            if useWire:
                selObj.display_type = "WIRE"
            else:
                selObj.display_type = "BOUNDS"

            object_visibility_set(selObj, value=False)

            if _operation == "SLICE":
                # copies instance_collection property(empty), but group property is empty (users_group = None)
                clone = actObj.copy()
                context.collection.objects.link(clone)

                space_data = context.space_data
                is_local_view = bool(space_data.local_view)

                if is_local_view:
                    clone.local_view_set(space_data, True)

                sliceMod = clone.modifiers.new("BTool_" + selObj.name, "BOOLEAN")  # add mod to clone obj
                sliceMod.object = selObj
                sliceMod.operation = "DIFFERENCE"
                clone["BoolToolRoot"] = True

            newMod = actObj.modifiers.new("BTool_" + selObj.name, "BOOLEAN")
            newMod.object = selObj

            if _operation == "SLICE":
                newMod.operation = "INTERSECT"
            else:
                newMod.operation = _operation

            actObj["BoolToolRoot"] = True
            selObj["BoolToolBrush"] = _operation
            selObj["BoolTool_FTransform"] = "False"


# Remove Objects form the BoolTool System
def Remove(context, thisObj_name, Prop):
    # Find the Brush pointed in the Tree View and Restore it, active is the Canvas
    actObj = context.active_object

    # Restore the Brush
    def RemoveThis(_thisObj_name):
        for obj in bpy.context.view_layer.objects:
            # if it's the brush object
            if obj.name == _thisObj_name:
                obj.display_type = "TEXTURED"
                del obj["BoolToolBrush"]
                del obj["BoolTool_FTransform"]
                object_visibility_set(obj, value=True)

                # Remove it from the Canvas
                for mod in actObj.modifiers:
                    if "BTool_" in mod.name:
                        if _thisObj_name in mod.name:
                            actObj.modifiers.remove(mod)

    if Prop == "THIS":
        RemoveThis(thisObj_name)

    # If the remove was called from the Properties:
    else:
        # Remove the Brush Property
        if Prop == "BRUSH":
            Canvas = FindCanvas(actObj)

            if Canvas:
                for mod in Canvas.modifiers:
                    if "BTool_" in mod.name and actObj.name in mod.name:
                        Canvas.modifiers.remove(mod)

            actObj.display_type = "TEXTURED"
            del actObj["BoolToolBrush"]
            del actObj["BoolTool_FTransform"]
            object_visibility_set(actObj, value=True)

        if Prop == "CANVAS":
            for mod in actObj.modifiers:
                if "BTool_" in mod.name:
                    RemoveThis(mod.object.name)


# Toggle the Enable the Brush Object Property
def EnableBrush(context, objList, canvas):
    for obj in objList:
        for mod in canvas.modifiers:
            if "BTool_" in mod.name and mod.object.name == obj:

                if mod.show_viewport:
                    mod.show_viewport = False
                    mod.show_render = False
                else:
                    mod.show_viewport = True
                    mod.show_render = True


# Find the Canvas and Enable this Brush
def EnableThisBrush(context, set):
    canvas = None
    for obj in bpy.context.view_layer.objects:
        if obj != bpy.context.active_object:
            if isCanvas(obj):
                for mod in obj.modifiers:
                    if "BTool_" in mod.name:
                        if mod.object == bpy.context.active_object:
                            canvas = obj

    for mod in canvas.modifiers:
        if "BTool_" in mod.name:
            if mod.object == bpy.context.active_object:
                if set == "None":
                    if mod.show_viewport:
                        mod.show_viewport = False
                        mod.show_render = False
                    else:
                        mod.show_viewport = True
                        mod.show_render = True
                else:
                    if set == "True":
                        mod.show_viewport = True
                    else:
                        mod.show_viewport = False
                return


# Toggle the Fast Transform Property of the Active Brush
def EnableFTransf(context):
    actObj = bpy.context.active_object

    if actObj["BoolTool_FTransform"] == "True":
        actObj["BoolTool_FTransform"] = "False"
    else:
        actObj["BoolTool_FTransform"] = "True"
    return


# Apply All Brushes to the Canvas
def ApplyAll(context, list):
    objDeleteList = []
    for selObj in list:
        if isCanvas(selObj) and selObj == context.active_object:
            for mod in selObj.modifiers:
                if "BTool_" in mod.name:
                    objDeleteList.append(mod.object)
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except:  # if fails the means it is multiuser data
                    context.active_object.data = context.active_object.data.copy()  # so just make data unique
                    bpy.ops.object.modifier_apply(modifier=mod.name)
            del selObj["BoolToolRoot"]

    for obj in context.scene.objects:
        if isCanvas(obj):
            for mod in obj.modifiers:
                # do not delete brush that is used by another canvas
                if mod.type == "BOOLEAN" and mod.object in objDeleteList:
                    objDeleteList.remove(mod.object)  # remove it from deletion

    bpy.ops.object.select_all(action="DESELECT")
    for obj in objDeleteList:
        obj.select_set(True)
    bpy.ops.object.delete()


# Apply This Brush to the Canvas
def ApplyThisBrush(context, brush):
    for obj in context.scene.objects:
        if isCanvas(obj):
            for mod in obj.modifiers:
                if "BTool_" + brush.name in mod.name:
                    # Apply This Brush
                    context.view_layer.objects.active = obj
                    try:
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    except:  # if fails the means it is multiuser data
                        context.active_object.data = context.active_object.data.copy()  # so just make data unique
                        bpy.ops.object.modifier_apply(modifier=mod.name)
                    bpy.ops.object.select_all(action="TOGGLE")
                    bpy.ops.object.select_all(action="DESELECT")

    # Garbage Collector
    brush.select_set(True)
    # bpy.ops.object.delete()


# ------------------ Bool Tool OPERATORS --------------------------------------

# TODO
# class BTool_DrawPolyBrush(Operator):
#     bl_idname = "btool.draw_polybrush"
#     bl_label = "Draw Poly Brush"
#     bl_description = (
#         "Draw Polygonal Mask, can be applied to Canvas > Brush or Directly\n"
#         "Note: ESC to Cancel, Enter to Apply, Right Click to erase the Lines"
#     )

#     count = 0
#     store_cont_draw = False

#     @classmethod
#     def poll(cls, context):
#         return context.active_object is not None

#     def set_cont_draw(self, context, start=False):
#         # store / restore GP continuous drawing (see T52321)
#         scene = context.scene
#         tool_settings = scene.tool_settings
#         continuous = tool_settings.use_gpencil_continuous_drawing
#         if start:
#             self.store_cont_draw = continuous
#             tool_settings.use_gpencil_continuous_drawing = True
#         else:
#             tool_settings.use_gpencil_continuous_drawing = self.store_cont_draw

#     def modal(self, context, event):
#         self.count += 1
#         actObj = bpy.context.active_object
#         if self.count == 1:
#             actObj.select_set(True)
#             bpy.ops.gpencil.draw("INVOKE_DEFAULT", mode="DRAW_POLY")

#         if event.type == "RIGHTMOUSE":
#             # use this to pass to the Grease Pencil eraser (see T52321)
#             pass

#         if event.type in {"RET", "NUMPAD_ENTER"}:

#             bpy.ops.gpencil.convert(type="POLY")
#             self.set_cont_draw(context)

#             for obj in context.selected_objects:
#                 if obj.type == "CURVE":
#                     obj.name = "PolyDraw"
#                     bpy.context.view_layer.objects.active = obj
#                     bpy.ops.object.select_all(action="DESELECT")
#                     obj.select_set(True)
#                     bpy.ops.object.convert(target="MESH")
#                     bpy.ops.object.mode_set(mode="EDIT")
#                     bpy.ops.mesh.select_all(action="SELECT")
#                     bpy.ops.mesh.edge_face_add()
#                     bpy.ops.mesh.flip_normals()
#                     bpy.ops.object.mode_set(mode="OBJECT")
#                     bpy.ops.object.origin_set(type="ORIGIN_CENTER_OF_MASS")
#                     bpy.ops.object.modifier_add(type="SOLIDIFY")
#                     for mod in obj.modifiers:
#                         if mod.name == "Solidify":
#                             mod.name = "BTool_PolyBrush"
#                             mod.thickness = 1
#                             mod.offset = 0
#                     obj["BoolToolPolyBrush"] = True

#                     bpy.ops.object.select_all(action="DESELECT")
#                     bpy.context.view_layer.objects.active = actObj
#                     bpy.context.view_layer.update()
#                     actObj.select_set(True)
#                     obj.select_set(True)

#                     bpy.context.view_layer.grease_pencil.clear()
#                     bpy.ops.gpencil.data_unlink()

#             return {"FINISHED"}

#         if event.type == "ESC":
#             bpy.ops.ed.undo()  # remove o Grease Pencil
#             self.set_cont_draw(context)

#             self.report({"INFO"}, "Draw Poly Brush: Operation Cancelled by User")
#             return {"CANCELLED"}

#         return {"RUNNING_MODAL"}

#     def invoke(self, context, event):
#         if context.object:
#             self.set_cont_draw(context, start=True)
#             context.window_manager.modal_handler_add(self)
#             return {"RUNNING_MODAL"}
#         else:
#             self.report({"WARNING"}, "No active object, could not finish")
#             return {"CANCELLED"}


# Fast Transform
class BTool_FastTransform(Operator):
    bl_idname = "btool.fast_transform"
    bl_label = "Fast Transform"
    bl_description = "Enable Fast Transform"

    operator: StringProperty("")

    count = 0

    def modal(self, context, event):
        self.count += 1
        actObj = bpy.context.active_object
        useWire = bpy.context.preferences.addons[__name__].preferences.use_wire
        if self.count == 1:

            if isBrush(actObj) and actObj["BoolTool_FTransform"] == "True":
                EnableThisBrush(bpy.context, "False")
                if useWire:
                    actObj.display_type = "WIRE"
                else:
                    actObj.display_type = "BOUNDS"

            if self.operator == "Translate":
                bpy.ops.transform.translate("INVOKE_DEFAULT")
            if self.operator == "Rotate":
                bpy.ops.transform.rotate("INVOKE_DEFAULT")
            if self.operator == "Scale":
                bpy.ops.transform.resize("INVOKE_DEFAULT")

        if event.type == "LEFTMOUSE":
            if isBrush(actObj):
                EnableThisBrush(bpy.context, "True")
                actObj.display_type = "WIRE"
            return {"FINISHED"}

        if event.type in {"RIGHTMOUSE", "ESC"}:
            if isBrush(actObj):
                EnableThisBrush(bpy.context, "True")
                actObj.display_type = "WIRE"
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):
        if context.object:
            context.window_manager.modal_handler_add(self)
            return {"RUNNING_MODAL"}
        else:
            self.report({"WARNING"}, "No active object, could not finish")
            return {"CANCELLED"}


# -------------------  Bool Tool OPERATOR CLASSES --------------------------------------------------------


# Brush operators
# --------------------------------------------------------------------------------------


class BToolSetup():

    def execute(self, context):
        Operation(context, self.mode)
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "At least two objects must be selected")
            return {"CANCELLED"}

        return self.execute(context)


class BTool_Union(Operator, BToolSetup):
    bl_idname = "btool.boolean_union"
    bl_label = "Brush Union"
    bl_description = "This operator add a union brush to a canvas"
    bl_options = {"REGISTER", "UNDO"}

    mode = "UNION"


class BTool_Inters(Operator, BToolSetup):
    bl_idname = "btool.boolean_inters"
    bl_label = "Brush Intersection"
    bl_description = "This operator add a intersect brush to a canvas"
    bl_options = {"REGISTER", "UNDO"}

    mode = "INTERSECT"


class BTool_Diff(Operator, BToolSetup):
    bl_idname = "btool.boolean_diff"
    bl_label = "Brush Difference"
    bl_description = "This operator add a difference brush to a canvas"
    bl_options = {"REGISTER", "UNDO"}

    mode = "DIFFERENCE"


class BTool_Slice(Operator, BToolSetup):
    bl_idname = "btool.boolean_slice"
    bl_label = "Brush Slice"
    bl_description = "This operator add a intersect brush to a canvas"
    bl_options = {"REGISTER", "UNDO"}

    mode = "SLICE"


# Auto Boolean operators
# --------------------------------------------------------------------------------------


class Auto_Boolean:

    def objects_prepare(self):
        for ob in bpy.context.selected_objects:
            if ob.type != "MESH":
                ob.select_set(False)
        bpy.ops.object.make_single_user(object=True, obdata=True)
        bpy.ops.object.convert(target="MESH")

    def mesh_selection(self, ob, select_action):
        obj = bpy.context.active_object

        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")

        bpy.ops.mesh.reveal()
        bpy.ops.mesh.select_all(action=select_action)

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.context.view_layer.objects.active = obj

    def boolean_operation(self):
        obj = bpy.context.active_object
        obj.select_set(False)
        obs = bpy.context.selected_objects

        self.mesh_selection(obj, "DESELECT")

        for ob in obs:
            self.mesh_selection(ob, "SELECT")
            self.boolean_mod(obj, ob, self.mode)

        obj.select_set(True)

    def boolean_mod(self, obj, ob, mode, ob_delete=True):
        md = obj.modifiers.new("Auto Boolean", "BOOLEAN")
        md.show_viewport = False
        md.operation = mode
        md.object = ob

        override = {"object": obj}
        bpy.ops.object.modifier_apply(override, modifier=md.name)

        if ob_delete:
            bpy.data.objects.remove(ob)

    def execute(self, context):
        self.objects_prepare()
        self.boolean_operation()
        return {"FINISHED"}

    def invoke(self, context, event):
        if len(context.selected_objects) < 2:
            self.report({"ERROR"}, "At least two objects must be selected")
            return {"CANCELLED"}

        return self.execute(context)


class OBJECT_OT_BoolTool_Auto_Union(Operator, Auto_Boolean):
    bl_idname = "object.booltool_auto_union"
    bl_label = "Bool Tool Union"
    bl_description = "Combine selected objects"
    bl_options = {"REGISTER", "UNDO"}

    mode = "UNION"


class OBJECT_OT_BoolTool_Auto_Difference(Operator, Auto_Boolean):
    bl_idname = "object.booltool_auto_difference"
    bl_label = "Bool Tool Difference"
    bl_description = "Subtract selected objects from active object"
    bl_options = {"REGISTER", "UNDO"}

    mode = "DIFFERENCE"


class OBJECT_OT_BoolTool_Auto_Intersect(Operator, Auto_Boolean):
    bl_idname = "object.booltool_auto_intersect"
    bl_label = "Bool Tool Intersect"
    bl_description = "Keep only intersecting geometry"
    bl_options = {"REGISTER", "UNDO"}

    mode = "INTERSECT"


class OBJECT_OT_BoolTool_Auto_Slice(Operator, Auto_Boolean):
    bl_idname = "object.booltool_auto_slice"
    bl_label = "Bool Tool Slice"
    bl_description = "Slice active object along the selected objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        space_data = context.space_data
        is_local_view = bool(space_data.local_view)
        self.objects_prepare()

        ob1 = context.active_object
        ob1.select_set(False)
        self.mesh_selection(ob1, "DESELECT")

        for ob2 in context.selected_objects:

            self.mesh_selection(ob2, "SELECT")

            ob1_copy = ob1.copy()
            ob1_copy.data = ob1.data.copy()

            for coll in ob1.users_collection:
                coll.objects.link(ob1_copy)

            if is_local_view:
                ob1_copy.local_view_set(space_data, True)

            self.boolean_mod(ob1, ob2, "DIFFERENCE", ob_delete=False)
            self.boolean_mod(ob1_copy, ob2, "INTERSECT")
            ob1_copy.select_set(True)

        context.view_layer.objects.active = ob1_copy

        return {"FINISHED"}


# Utils Class ---------------------------------------------------------------

# Find the Brush Selected in Three View
class BTool_FindBrush(Operator):
    bl_idname = "btool.find_brush"
    bl_label = ""
    bl_description = "Find the selected brush"

    obj: StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        for ob in bpy.context.view_layer.objects:
            if ob.name == self.obj:
                bpy.ops.object.select_all(action="TOGGLE")
                bpy.ops.object.select_all(action="DESELECT")
                bpy.context.view_layer.objects.active = ob
                ob.set_select(state=True)
        return {"FINISHED"}


# Move The Modifier in The Stack Up or Down
class BTool_MoveStack(Operator):
    bl_idname = "btool.move_stack"
    bl_label = ""
    bl_description = "Move this Brush Up/Down in the Stack"

    modif: StringProperty("")
    direction: StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        if self.direction == "UP":
            bpy.ops.object.modifier_move_up(modifier=self.modif)
        if self.direction == "DOWN":
            bpy.ops.object.modifier_move_down(modifier=self.modif)
        return {"FINISHED"}


# Enable or Disable a Brush in the Three View
class BTool_EnableBrush(Operator):
    bl_idname = "btool.enable_brush"
    bl_label = ""
    bl_description = "Removes all BoolTool config assigned to it"

    thisObj: StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        # in this case is just one object but the function accept more than one at once
        EnableBrush(context, [self.thisObj], context.active_object)
        return {"FINISHED"}


# Enable or Disable a Brush Directly
class BTool_EnableThisBrush(Operator):
    bl_idname = "btool.enable_this_brush"
    bl_label = ""
    bl_description = "Toggles this brush"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        EnableThisBrush(context, "None")
        return {"FINISHED"}


# Enable or Disable a Brush Directly
class BTool_EnableFTransform(Operator):
    bl_idname = "btool.enable_ftransf"
    bl_label = ""
    bl_description = "Use Fast Transformations to improve speed"

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        EnableFTransf(context)
        return {"FINISHED"}


# Other Operations -------------------------------------------------------

# Remove a Brush or a Canvas
class BTool_Remove(Operator):
    bl_idname = "btool.remove"
    bl_label = "Bool Tool Remove"
    bl_description = "Removes all BoolTool config assigned to it"
    bl_options = {"UNDO"}

    thisObj: StringProperty("")
    Prop: StringProperty("")

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        Remove(context, self.thisObj, self.Prop)
        return {"FINISHED"}


# Apply All to Canvas
class BTool_AllBrushToMesh(Operator):
    bl_idname = "btool.to_mesh"
    bl_label = "Apply All Canvas"
    bl_description = "Apply all brushes of this canvas"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        lists = bpy.context.selected_objects
        ApplyAll(context, lists)
        return {"FINISHED"}


# Apply This Brush to the Canvas
class BTool_BrushToMesh(Operator):
    bl_idname = "btool.brush_to_mesh"
    bl_label = "Apply this Brush to Canvas"
    bl_description = "Apply this brush to the canvas"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):

        if isBrush(context.active_object):
            return True
        else:
            return False

    def execute(self, context):
        ApplyThisBrush(context, bpy.context.active_object)
        return {"FINISHED"}


# TODO
# Apply This Brush To Mesh


# ------------------- MENU CLASSES ------------------------------

# 3Dview Header Menu
class VIEW3D_MT_booltool_menu(Menu):
    bl_label = "Bool Tool"
    bl_idname = "VIEW3D_MT_booltool_menu"

    def draw(self, context):
        layout = self.layout

        layout.label(text="Auto Boolean")
        layout.operator(OBJECT_OT_BoolTool_Auto_Difference.bl_idname, text="Difference", icon="SELECT_SUBTRACT")
        layout.operator(OBJECT_OT_BoolTool_Auto_Union.bl_idname, text="Union", icon="SELECT_EXTEND")
        layout.operator(OBJECT_OT_BoolTool_Auto_Intersect.bl_idname, text="Intersect", icon="SELECT_INTERSECT")
        layout.operator(OBJECT_OT_BoolTool_Auto_Slice.bl_idname, text="Slice", icon="SELECT_DIFFERENCE")

        layout.separator()

        layout.label(text="Brush Boolean")
        layout.operator(BTool_Diff.bl_idname, text="Difference", icon="SELECT_SUBTRACT")
        layout.operator(BTool_Union.bl_idname, text="Union", icon="SELECT_EXTEND")
        layout.operator(BTool_Inters.bl_idname, text="Intersect", icon="SELECT_INTERSECT")
        layout.operator(BTool_Slice.bl_idname, text="Slice", icon="SELECT_DIFFERENCE")

        if isCanvas(context.active_object):
            layout.separator()
            layout.operator(BTool_AllBrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply All")
            Rem = layout.operator(BTool_Remove.bl_idname, icon="X", text="Remove All")
            Rem.thisObj = ""
            Rem.Prop = "CANVAS"

        if isBrush(context.active_object):
            layout.separator()
            layout.operator(BTool_BrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply Brush")
            Rem = layout.operator(BTool_Remove.bl_idname, icon="X", text="Remove Brush")
            Rem.thisObj = ""
            Rem.Prop = "BRUSH"


def VIEW3D_BoolTool_Menu(self, context):
    self.layout.menu(VIEW3D_MT_booltool_menu.bl_idname)


# ---------------- Toolshelf: Tools ---------------------


class VIEW3D_PT_booltool_tools(Panel):
    bl_category = "objectmode"
    bl_label = "Bool Tool"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def draw(self, context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Auto Boolean")
        col.operator(OBJECT_OT_BoolTool_Auto_Difference.bl_idname, text="Difference", icon="SELECT_SUBTRACT")
        col.operator(OBJECT_OT_BoolTool_Auto_Union.bl_idname, text="Union", icon="SELECT_EXTEND")
        col.operator(OBJECT_OT_BoolTool_Auto_Intersect.bl_idname, text="Intersect", icon="SELECT_INTERSECT")
        col.operator(OBJECT_OT_BoolTool_Auto_Slice.bl_idname, text="Slice", icon="SELECT_DIFFERENCE")

        col = layout.column(align=True)
        col.label(text="Brush Boolean")
        col.operator(BTool_Diff.bl_idname, text="Difference", icon="SELECT_SUBTRACT")
        col.operator(BTool_Union.bl_idname, text="Union", icon="SELECT_EXTEND")
        col.operator(BTool_Inters.bl_idname, text="Intersect", icon="SELECT_INTERSECT")
        col.operator(BTool_Slice.bl_idname, text="Slice", icon="SELECT_DIFFERENCE")

        # TODO Draw Poly Brush
        # main.separator()

        # col = main.column(align=True)
        # col.label(text="Draw:", icon="MESH_CUBE")
        # col.separator()
        # col.operator(BTool_DrawPolyBrush.bl_idname, icon="LINE_DATA")


# ---------- Toolshelf: Properties --------------------------------------------------------


class VIEW3D_PT_booltool_config(Panel):
    bl_category = "objectmode"
    bl_label = "Properties"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_booltool_tools"

    @classmethod
    def poll(cls, context):
        actObj = context.active_object
        return isCanvas(actObj) or isBrush(actObj)  # or isPolyBrush(actObj)

    def draw(self, context):
        layout = self.layout
        actObj = context.active_object

        row = layout.row(align=True)

        if isCanvas(actObj):

            row.label(text="CANVAS", icon="MESH_GRID")
            row = layout.row()
            row.prop(context.scene, "BoolHide", text="Hide Bool objects")
            row = layout.row(align=True)
            row.operator(BTool_AllBrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply All")

            row = layout.row(align=True)
            Rem = row.operator(BTool_Remove.bl_idname, icon="X", text="Remove All")
            Rem.thisObj = ""
            Rem.Prop = "CANVAS"

            if isBrush(actObj):
                layout.separator()

        if isBrush(actObj):

            if actObj["BoolToolBrush"] == "DIFFERENCE":
                icon = "SELECT_SUBTRACT"
            elif actObj["BoolToolBrush"] == "UNION":
                icon = "SELECT_EXTEND"
            elif actObj["BoolToolBrush"] == "INTERSECT":
                icon = "SELECT_INTERSECT"
            elif actObj["BoolToolBrush"] == "SLICE":
                icon = "SELECT_DIFFERENCE"

            row.label(text="BRUSH", icon=icon)

            if actObj["BoolTool_FTransform"] == "True":
                icon = "PMARKER_ACT"
            else:
                icon = "PMARKER"
            if isFTransf():
                pass

            if isFTransf():
                row = layout.row(align=True)
                row.operator(BTool_EnableFTransform.bl_idname, text="Fast Vis", icon=icon)
                row.operator(BTool_EnableThisBrush.bl_idname, text="Enable", icon="HIDE_OFF")
            else:
                row.operator(BTool_EnableThisBrush.bl_idname, icon="HIDE_OFF")

            layout.operator(BTool_BrushToMesh.bl_idname, icon="MOD_LATTICE", text="Apply Brush")
            Rem = layout.operator(BTool_Remove.bl_idname, icon="X", text="Remove Brush")
            Rem.thisObj = ""
            Rem.Prop = "BRUSH"

        # TODO
        # if isPolyBrush(actObj):
        #     layout.label(text="POLY BRUSH", icon="LINE_DATA")
        #     mod = actObj.modifiers["BTool_PolyBrush"]
        #     layout.prop(mod, "thickness", text="Size")


# ---------- Toolshelf: Brush Viewer -------------------------------------------------------


class VIEW3D_PT_booltool_bviewer(Panel):
    bl_category = "objectmode"
    bl_label = "Brush Viewer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_booltool_tools"

    @classmethod
    def poll(cls, context):
        actObj = bpy.context.active_object

        if isCanvas(actObj):
            return True
        else:
            return False

    def draw(self, context):

        actObj = bpy.context.active_object

        if isCanvas(actObj):

            for mod in actObj.modifiers:
                container = self.layout.box()
                row = container.row(align=True)

                if "BTool_" in mod.name:

                    if mod.operation == "DIFFERENCE":
                        icon = "SELECT_SUBTRACT"
                    elif mod.operation == "UNION":
                        icon = "SELECT_EXTEND"
                    elif mod.operation == "INTERSECT":
                        icon = "SELECT_INTERSECT"
                    elif mod.operation == "SLICE":
                        icon = "SELECT_DIFFERENCE"

                    objSelect = row.operator("btool.find_brush", text=mod.object.name, icon=icon, emboss=False)
                    objSelect.obj = mod.object.name

                    EnableIcon = "RESTRICT_VIEW_ON"
                    if mod.show_viewport:
                        EnableIcon = "RESTRICT_VIEW_OFF"
                    Enable = row.operator(BTool_EnableBrush.bl_idname, icon=EnableIcon, emboss=False)
                    Enable.thisObj = mod.object.name

                    Remove = row.operator("btool.remove", text="", icon="X", emboss=False)
                    Remove.thisObj = mod.object.name
                    Remove.Prop = "THIS"

                else:
                    row.label(text=mod.name)

                Up = row.operator("btool.move_stack", icon="TRIA_UP", emboss=False)
                Up.modif = mod.name
                Up.direction = "UP"

                Dw = row.operator("btool.move_stack", icon="TRIA_DOWN", emboss=False)
                Dw.modif = mod.name
                Dw.direction = "DOWN"


# ------------------ BOOL TOOL ADD-ON PREFERENCES ----------------------------


shortcut_list = (
    ("3D View", None),
    ("Menu", "Ctrl Shift B"),

    ("Auto Operators", None),
    ("Difference", "Ctrl Shift Num -"),
    ("Union", "Ctrl Shift Num +"),
    ("Intersect", "Ctrl Shift Num *"),
    ("Slice", "Ctrl Shift Num /"),

    ("Brush Operators", None),
    ("Difference", "Ctrl Num -"),
    ("Union", "Ctrl Num +"),
    ("Intersect", "Ctrl Num *"),
    ("Slice", "Ctrl Num /"),
    ("Brush To Mesh", "Ctrl Num Enter"),
    ("All Brushes To Mesh", "Ctrl Shift Num Enter"),
)


def UpdateBoolTool_Pref(self, context):
    if self.fast_transform:
        RegisterFastT()
    else:
        UnRegisterFastT()


# Define Panel classes for updating
panels = (
    VIEW3D_PT_booltool_tools,
    VIEW3D_PT_booltool_config,
    VIEW3D_PT_booltool_bviewer,
)


def update_panels(self, context):
    try:
        for panel in panels:
            if "bl_rna" in panel.__dict__:
                bpy.utils.unregister_class(panel)

        for panel in panels:
            panel.bl_category = context.preferences.addons[
                __name__
            ].preferences.category
            bpy.utils.register_class(panel)

    except Exception as e:
        message = "Bool Tool: Updating Panel locations has failed"
        print("\n[{}]\n{}\n\nError:\n{}".format(__name__, message, e))


def icon_tria(prop):
    if prop:
        return "TRIA_DOWN"
    return "TRIA_RIGHT"


class PREFS_BoolTool_Props(AddonPreferences):
    bl_idname = __name__

    fast_transform: BoolProperty(
        name="Fast Transformations",
        update=UpdateBoolTool_Pref,
        description="Replace the Transform HotKeys (G,R,S)\n"
        "for a custom version that can optimize the visualization of Brushes",
    )
    use_wire: BoolProperty(
        name="Display As Wirewrame",
        description="Display brush as wireframe instead of bounding box",
    )
    category: StringProperty(
        name="Tab Name",
        description="Set sidebar tab name",
        default="Edit",
        update=update_panels,
    )
    show_shortcuts: BoolProperty(name="Shortcuts")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.prop(self, "category")
        col.prop(self, "fast_transform")
        col.prop(self, "use_wire")

        col = layout.column()
        col.scale_y = 1.2
        col.use_property_split = False
        col.prop(self, "show_shortcuts", icon=icon_tria(self.show_shortcuts))

        if self.show_shortcuts:

            col = layout.column()

            for key_name, key_comb in shortcut_list:
                if key_comb is None:
                    col.separator()
                    col.label(text=key_name)
                else:
                    row = col.row(align=True)
                    row.scale_y = 0.7
                    row.box().label(text=key_name)
                    row.box().label(text=key_comb)


# ------------------- Class List ------------------------------------------------

classes = (
    PREFS_BoolTool_Props,
    VIEW3D_MT_booltool_menu,
    VIEW3D_PT_booltool_tools,
    VIEW3D_PT_booltool_config,
    VIEW3D_PT_booltool_bviewer,
    OBJECT_OT_BoolTool_Auto_Union,
    OBJECT_OT_BoolTool_Auto_Difference,
    OBJECT_OT_BoolTool_Auto_Intersect,
    OBJECT_OT_BoolTool_Auto_Slice,
    BTool_Union,
    BTool_Diff,
    BTool_Inters,
    BTool_Slice,
    # TODO Draw Poly Brush
    # BTool_DrawPolyBrush,
    BTool_Remove,
    BTool_AllBrushToMesh,
    BTool_BrushToMesh,
    BTool_FindBrush,
    BTool_MoveStack,
    BTool_EnableBrush,
    BTool_EnableThisBrush,
    BTool_EnableFTransform,
    BTool_FastTransform,
)


# ------------------- REGISTER ------------------------------------------------

addon_keymaps = []
addon_keymapsFastT = []


# Fast Transform HotKeys Register
def RegisterFastT():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Object Mode", space_type="EMPTY")

    kmi = km.keymap_items.new(BTool_FastTransform.bl_idname, "G", "PRESS")
    kmi.properties.operator = "Translate"
    addon_keymapsFastT.append((km, kmi))

    kmi = km.keymap_items.new(BTool_FastTransform.bl_idname, "R", "PRESS")
    kmi.properties.operator = "Rotate"
    addon_keymapsFastT.append((km, kmi))

    kmi = km.keymap_items.new(BTool_FastTransform.bl_idname, "S", "PRESS")
    kmi.properties.operator = "Scale"
    addon_keymapsFastT.append((km, kmi))


# Fast Transform HotKeys UnRegister
def UnRegisterFastT():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymapsFastT:
            km.keymap_items.remove(kmi)

    addon_keymapsFastT.clear()


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    update_panels(None, bpy.context)

    # Scene variables
    bpy.types.Scene.BoolHide = BoolProperty(
        default=False,
        description="Hide boolean objects",
        update=update_BoolHide,
    )
    bpy.types.VIEW3D_MT_object.append(VIEW3D_BoolTool_Menu)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon

    # create the boolean menu hotkey
    if kc is not None:
        km = kc.keymaps.new(name="Object Mode")

        kmi = km.keymap_items.new("wm.call_menu", "B", "PRESS", ctrl=True, shift=True)
        kmi.properties.name = "VIEW3D_MT_booltool_menu"
        addon_keymaps.append((km, kmi))

        # Brush Operators
        kmi = km.keymap_items.new(BTool_Union.bl_idname, "NUMPAD_PLUS", "PRESS", ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(BTool_Diff.bl_idname, "NUMPAD_MINUS", "PRESS", ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(BTool_Inters.bl_idname, "NUMPAD_ASTERIX", "PRESS", ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(BTool_Slice.bl_idname, "NUMPAD_SLASH", "PRESS", ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(BTool_BrushToMesh.bl_idname, "NUMPAD_ENTER", "PRESS", ctrl=True)
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            BTool_AllBrushToMesh.bl_idname,
            "NUMPAD_ENTER",
            "PRESS",
            ctrl=True,
            shift=True,
        )
        addon_keymaps.append((km, kmi))

        # Auto Operators
        kmi = km.keymap_items.new(
            OBJECT_OT_BoolTool_Auto_Union.bl_idname,
            "NUMPAD_PLUS",
            "PRESS",
            ctrl=True,
            shift=True,
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            OBJECT_OT_BoolTool_Auto_Difference.bl_idname,
            "NUMPAD_MINUS",
            "PRESS",
            ctrl=True,
            shift=True,
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            OBJECT_OT_BoolTool_Auto_Intersect.bl_idname,
            "NUMPAD_ASTERIX",
            "PRESS",
            ctrl=True,
            shift=True,
        )
        addon_keymaps.append((km, kmi))
        kmi = km.keymap_items.new(
            OBJECT_OT_BoolTool_Auto_Slice.bl_idname,
            "NUMPAD_SLASH",
            "PRESS",
            ctrl=True,
            shift=True,
        )
        addon_keymaps.append((km, kmi))


def unregister():
    # Keymapping
    # remove keymaps when add-on is deactivated
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc is not None:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)

    addon_keymaps.clear()
    UnRegisterFastT()
    bpy.types.VIEW3D_MT_object.remove(VIEW3D_BoolTool_Menu)
    del bpy.types.Scene.BoolHide

    for cls in classes:
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
