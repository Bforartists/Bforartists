# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from bpy.types import Operator
from bpy.props import (
    StringProperty,
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty
    )


from .enum_values import *
from .functions import *

from math import radians

# -----------------------------------------------------------------------------
# operator classes

class VIEW3D_OT_materialutilities_assign_material_edit(bpy.types.Operator):
    """Assign a material to the current selection"""

    bl_idname = "view3d.materialutilities_assign_material_edit"
    bl_label = "Assign Material (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty(
            name = 'Material Name',
            description = 'Name of Material to assign to current selection',
            default = "",
            maxlen = 63
            )
    new_material: BoolProperty(
            name = '',
            description = 'Add a new material, enter the name in the box',
            default = False
            )
    show_dialog: BoolProperty(
            name = 'Show Dialog',
            default = False
            )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def invoke(self, context, event):
        if self.show_dialog:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        row = col.split(factor = 0.9, align = True)

        if self.new_material:
            row.prop(self, "material_name")
        else:
            row.prop_search(self, "material_name", bpy.data, "materials")

        row.prop(self, "new_material", expand = True, icon = 'ADD')

    def execute(self, context):
        material_name = self.material_name

        if self.new_material:
            material_name = mu_new_material_name(material_name)
        elif material_name == "":
            self.report({'WARNING'}, "No Material Name given!")
            return {'CANCELLED'}

        return mu_assign_material(self, material_name, 'APPEND_MATERIAL')


class VIEW3D_OT_materialutilities_assign_material_object(bpy.types.Operator):
    """Assign a material to the current selection
    (See the operator panel [F9] for more options)"""

    bl_idname = "view3d.materialutilities_assign_material_object"
    bl_label = "Assign Material (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty(
            name = 'Material Name',
            description = 'Name of Material to assign to current selection',
            default = "",
            maxlen = 63
            )
    override_type: EnumProperty(
            name = 'Assignment method',
            description = '',
            items = mu_override_type_enums
            )
    new_material: BoolProperty(
            name = '',
            description = 'Add a new material, enter the name in the box',
            default = False
            )
    show_dialog: BoolProperty(
            name = 'Show Dialog',
            default = False
            )

    @classmethod
    def poll(cls, context):
        return len(context.selected_editable_objects) > 0

    def invoke(self, context, event):
        if self.show_dialog:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def draw(self, context):
        layout = self.layout

        col = layout.column()
        row = col.split(factor=0.9, align = True)

        if self.new_material:
            row.prop(self, "material_name")
        else:
            row.prop_search(self, "material_name", bpy.data, "materials")

        row.prop(self, "new_material", expand = True, icon = 'ADD')

        layout.prop(self, "override_type")


    def execute(self, context):
        material_name = self.material_name
        override_type = self.override_type

        if self.new_material:
            material_name = mu_new_material_name(material_name)
        elif material_name == "":
            self.report({'WARNING'}, "No Material Name given!")
            return {'CANCELLED'}

        result = mu_assign_material(self, material_name, override_type)
        return result

class VIEW3D_OT_materialutilities_select_by_material_name(bpy.types.Operator):
    """Select geometry that has the chosen material assigned to it
    (See the operator panel [F9] for more options)"""

    bl_idname = "view3d.materialutilities_select_by_material_name"
    bl_label = "Select By Material Name (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    extend_selection: BoolProperty(
            name = 'Extend Selection',
            description = 'Keeps the current selection and adds faces with the material to the selection'
            )
    material_name: StringProperty(
            name = 'Material Name',
            description = 'Name of Material to find and Select',
            maxlen = 63
            )
    show_dialog: BoolProperty(
            name = 'Show Dialog',
            default = False
    )

    @classmethod
    def poll(cls, context):
        return len(context.visible_objects) > 0

    def invoke(self, context, event):
        if self.show_dialog:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.prop_search(self, "material_name", bpy.data, "materials")

        layout.prop(self, "extend_selection", icon = "SELECT_EXTEND")

    def execute(self, context):
        material_name = self.material_name
        ext = self.extend_selection
        return mu_select_by_material_name(self, material_name, ext)


class VIEW3D_OT_materialutilities_copy_material_to_others(bpy.types.Operator):
    """Copy the material(s) of the active object to the other selected objects"""

    bl_idname = "view3d.materialutilities_copy_material_to_others"
    bl_label = "Copy material(s) to others (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.active_object.mode != 'EDIT')

    def execute(self, context):
        return mu_copy_material_to_others(self)


class VIEW3D_OT_materialutilities_clean_material_slots(bpy.types.Operator):
    """Removes any material slots from the selected objects that are not used"""

    bl_idname = "view3d.materialutilities_clean_material_slots"
    bl_label = "Clean Material Slots (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    # affect: EnumProperty(
    #         name = "Affect",
    #         description = "Which objects material slots should be cleaned",
    #         items = mu_clean_slots_enums,
    #         default = 'ACTIVE'
    #         )

    only_active: BoolProperty(
            name = 'Only active object',
            description = 'Only remove the material slots for the active object ' +
                            '(otherwise do it for every selected object)',
            default = True
            )

    @classmethod
    def poll(cls, context):
        return len(context.selected_editable_objects) > 0

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "only_active", icon = "PIVOT_ACTIVE")

    def execute(self, context):
        affect = "ACTIVE" if self.only_active else "SELECTED"

        return mu_cleanmatslots(self, affect)


class VIEW3D_OT_materialutilities_remove_material_slot(bpy.types.Operator):
    """Remove the active material slot from selected object(s)
    (See the operator panel [F9] for more options)"""

    bl_idname = "view3d.materialutilities_remove_material_slot"
    bl_label = "Remove Active Material Slot (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    only_active: BoolProperty(
            name = 'Only active object',
            description = 'Only remove the active material slot for the active object ' +
                            '(otherwise do it for every selected object)',
            default = True
            )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.active_object.mode != 'EDIT')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "only_active", icon = "PIVOT_ACTIVE")

    def execute(self, context):
        return mu_remove_material(self, self.only_active)

class VIEW3D_OT_materialutilities_remove_all_material_slots(bpy.types.Operator):
    """Remove all material slots from selected object(s)
    (See the operator panel [F9] for more options)"""

    bl_idname = "view3d.materialutilities_remove_all_material_slots"
    bl_label = "Remove All Material Slots (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    only_active: BoolProperty(
            name = 'Only active object',
            description = 'Only remove the material slots for the active object ' +
                            '(otherwise do it for every selected object)',
            default = True
            )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None) and (context.active_object.mode != 'EDIT')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "only_active", icon = "PIVOT_ACTIVE")

    def execute(self, context):
        return mu_remove_all_materials(self, self.only_active)


class VIEW3D_OT_materialutilities_replace_material(bpy.types.Operator):
    """Replace a material by name"""
    bl_idname = "view3d.materialutilities_replace_material"
    bl_label = "Replace Material (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    matorg: StringProperty(
            name = "Original",
            description = "Material to find and replace",
            maxlen = 63,
            )
    matrep: StringProperty(name="Replacement",
            description = "Material that will be used instead of the Original material",
            maxlen = 63,
            )
    all_objects: BoolProperty(
            name = "All Objects",
            description = "Replace for all objects in this blend file (otherwise only selected objects)",
            default = True,
            )
    update_selection: BoolProperty(
            name = "Update Selection",
            description = "Select affected objects and deselect unaffected",
            default = True,
            )

    def draw(self, context):
        layout = self.layout

        layout.prop_search(self, "matorg", bpy.data, "materials")
        layout.prop_search(self, "matrep", bpy.data, "materials")
        layout.separator()

        layout.prop(self, "all_objects", icon = "BLANK1")
        layout.prop(self, "update_selection", icon = "SELECT_INTERSECT")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return mu_replace_material(self.matorg, self.matrep, self.all_objects, self.update_selection)


class VIEW3D_OT_materialutilities_fake_user_set(bpy.types.Operator):
    """Enable/disable fake user for materials"""

    bl_idname = "view3d.materialutilities_fake_user_set"
    bl_label = "Set Fake User (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    fake_user: EnumProperty(
            name = "Fake User",
            description = "Turn fake user on or off",
            items = mu_fake_user_set_enums,
            default = 'TOGGLE'
            )

    affect: EnumProperty(
            name = "Affect",
            description = "Which materials of objects to affect",
            items = mu_fake_user_affect_enums,
            default = 'UNUSED'
            )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "fake_user", expand = True)
        layout.separator()

        layout.prop(self, "affect")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return mu_set_fake_user(self, self.fake_user, self.affect)


class VIEW3D_OT_materialutilities_change_material_link(bpy.types.Operator):
    """Link the materials to Data or Object, while keepng materials assigned"""

    bl_idname = "view3d.materialutilities_change_material_link"
    bl_label = "Change Material Linking (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    override: BoolProperty(
            name = "Override Data material",
            description = "Override the materials assigned to the object data/mesh when switching to 'Linked to Data'\n" +
                            "(WARNING: This will override the materials of other linked objects, " +
                             "which have the materials linked to Data)",
            default = False,
            )
    link_to: EnumProperty(
            name = "Link",
            description = "What should the material be linked to",
            items = mu_link_to_enums,
            default = 'OBJECT'
            )

    affect: EnumProperty(
            name = "Affect",
            description = "Which materials of objects to affect",
            items = mu_link_affect_enums,
            default = 'SELECTED'
            )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None)

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "link_to", expand = True)
        layout.separator()

        layout.prop(self, "affect")
        layout.separator()

        layout.prop(self, "override", icon = "DECORATE_OVERRIDE")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return mu_change_material_link(self, self.link_to, self.affect, self.override)

class MATERIAL_OT_materialutilities_merge_base_names(bpy.types.Operator):
    """Merges materials that has the same base names but ends with .xxx (.001, .002 etc)"""

    bl_idname = "material.materialutilities_merge_base_names"
    bl_label = "Merge Base Names"
    bl_description = "Merge materials that has the same base names but ends with .xxx (.001, .002 etc)"

    material_base_name: StringProperty(
                            name = "Material Base Name",
                            default = "",
                            description = 'Base name for materials to merge ' +
                                          '(e.g. "Material" is the base name of "Material.001", "Material.002" etc.)'
                            )
    is_auto: BoolProperty(
                            name = "Auto Merge",
                            description = "Find all available duplicate materials and Merge them"
                            )

    is_not_undo = False
    material_error = []          # collect mat for warning messages


    def replace_name(self):
        """If the user chooses a material like 'Material.042', clean it up to get a base name ('Material')"""

        # use the chosen material as a base one, check if there is a name
        self.check_no_name = (False if self.material_base_name in {""} else True)

        # No need to do this if it's already "clean"
        #  (Also lessens the potential of error given about the material with the Base name)
        if '.' not in self.material_base_name:
            return

        if self.check_no_name is True:
            for mat in bpy.data.materials:
                name = mat.name

                if name == self.material_base_name:
                    try:
                        base, suffix = name.rsplit('.', 1)

                        # trigger the exception
                        num = int(suffix, 10)
                        self.material_base_name = base
                        mat.name = self.material_base_name
                        return
                    except ValueError:
                        if name not in self.material_error:
                            self.material_error.append(name)
                        return

        return

    def split_name(self, material):
        """Split the material name into a base and a suffix"""

        name = material.name

        # No need to do this if it's already "clean"/there is no suffix
        if '.' not in name:
            return name, None

        base, suffix = name.rsplit('.', 1)

        try:
            # trigger the exception
            num = int(suffix, 10)
        except ValueError:
            # Not a numeric suffix
            # Don't report on materials not actually included in the merge!
            if ((self.is_auto or base == self.material_base_name)
                 and (name not in self.material_error)):
                self.material_error.append(name)
            return name, None

        if self.is_auto is False:
            if base == self.material_base_name:
                return base, suffix
            else:
                return name, None

        return base, suffix

    def fixup_slot(self, slot):
        """Fix material slots that was assigned to materials now removed"""

        if not slot.material:
            return

        base, suffix = self.split_name(slot.material)
        if suffix is None:
            return

        try:
            base_mat = bpy.data.materials[base]
        except KeyError:
            print("\n[Materials Utilities Specials]\nLink to base names\nError:"
                  "Base material %r not found\n" % base)
            return

        slot.material = base_mat

    def main_loop(self, context):
        """Loops through all objects and material slots to make sure they are assigned to the right material"""

        for obj in context.scene.objects:
            for slot in obj.material_slots:
                self.fixup_slot(slot)

    @classmethod
    def poll(self, context):
        return (context.mode == 'OBJECT') and (len(context.visible_objects) > 0)

    def draw(self, context):
        layout = self.layout

        box_1 = layout.box()
        box_1.prop_search(self, "material_base_name", bpy.data, "materials")
        box_1.enabled = not self.is_auto
        layout.separator()

        layout.prop(self, "is_auto", text = "Auto Rename/Replace", icon = "SYNTAX_ON")

    def invoke(self, context, event):
        self.is_not_undo = True
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Reset Material errors, otherwise we risk reporting errors erroneously..
        self.material_error = []

        if not self.is_auto:
            self.replace_name()

            if self.check_no_name:
                self.main_loop(context)
            else:
                self.report({'WARNING'}, "No Material Base Name given!")

                self.is_not_undo = False
                return {'CANCELLED'}

        self.main_loop(context)

        if self.material_error:
            materials = ", ".join(self.material_error)

            if len(self.material_error) == 1:
                waswere = " was"
                suff_s = ""
            else:
                waswere = " were"
                suff_s = "s"

            self.report({'WARNING'}, materials + waswere + " not removed or set as Base" + suff_s)

        self.is_not_undo = False
        return {'FINISHED'}

class MATERIAL_OT_materialutilities_material_slot_move(bpy.types.Operator):
    """Move the active material slot"""

    bl_idname = "material.materialutilities_slot_move"
    bl_label = "Move Slot"
    bl_description = "Move the material slot"
    bl_options = {'REGISTER', 'UNDO'}

    movement: EnumProperty(
                name = "Move",
                description = "How to move the material slot",
                items = mu_material_slot_move_enums
                )

    @classmethod
    def poll(self, context):
        # would prefer to access self.movement here, but can't..
        obj = context.active_object
        if not obj:
            return False
        if (obj.active_material_index < 0) or (len(obj.material_slots) <= 1):
            return False
        return True

    def execute(self, context):
        active_object = context.active_object
        active_material = context.object.active_material

        if self.movement == 'TOP':
            dir = 'UP'

            steps = active_object.active_material_index
        else:
            dir = 'DOWN'

            last_slot_index = len(active_object.material_slots) - 1
            steps = last_slot_index - active_object.active_material_index

        if steps == 0:
            self.report({'WARNING'}, active_material.name + " already at " + self.movement.lower() + '!')
        else:
            for i in range(steps):
                bpy.ops.object.material_slot_move(direction = dir)

            self.report({'INFO'}, active_material.name + ' moved to ' + self.movement.lower())

        return {'FINISHED'}



class MATERIAL_OT_materialutilities_join_objects(bpy.types.Operator):
    """Join objects that have the same (selected) material(s)"""

    bl_idname = "material.materialutilities_join_objects"
    bl_label = "Join by material (Material Utilities)"
    bl_description = "Join objects that share the same material"
    bl_options = {'REGISTER', 'UNDO'}

    material_name: StringProperty(
                            name = "Material",
                            default = "",
                            description = 'Material to use to join objects'
                            )
    is_auto: BoolProperty(
                            name = "Auto Join",
                            description = "Join objects for all materials"
                            )

    is_not_undo = True
    material_error = []          # collect mat for warning messages


    @classmethod
    def poll(self, context):
        # This operator only works in Object mode
        return (context.mode == 'OBJECT') and (len(context.visible_objects) > 0)

    def draw(self, context):
        layout = self.layout

        box_1 = layout.box()
        box_1.prop_search(self, "material_name", bpy.data, "materials")
        box_1.enabled = not self.is_auto
        layout.separator()

        layout.prop(self, "is_auto", text = "Auto Join", icon = "SYNTAX_ON")

    def invoke(self, context, event):
        self.is_not_undo = True
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # Reset Material errors, otherwise we risk reporting errors erroneously..
        self.material_error = []
        materials = []

        if not self.is_auto:
            if self.material_name == "":
                self.report({'WARNING'}, "No Material Name given!")

                self.is_not_undo = False
                return {'CANCELLED'}
            materials = [self.material_name]
        else:
            materials = bpy.data.materials.keys()

        result = mu_join_objects(self, materials)
        self.is_not_undo = False

        return result


class MATERIAL_OT_materialutilities_auto_smooth_angle(bpy.types.Operator):
    """Set Auto smooth values for selected objects"""
    # Inspired by colkai

    bl_idname = "view3d.materialutilities_auto_smooth_angle"
    bl_label = "Set Auto Smooth Angle (Material Utilities)"
    bl_options = {'REGISTER', 'UNDO'}

    affect: EnumProperty(
            name = "Affect",
            description = "Which objects of to affect",
            items = mu_affect_enums,
            default = 'SELECTED'
            )
    angle: FloatProperty(
            name = "Angle",
            description = "Maximum angle between face normals that will be considered as smooth",
            subtype = 'ANGLE',
            min = 0,
            max = radians(180),
            default = radians(35)
            )
    set_smooth_shading: BoolProperty(
            name = "Set Smooth",
            description = "Set Smooth shading for the affected objects\n"
                   "This overrides the current smooth/flat shading that might be set to different parts of the object",
            default = True
            )

    @classmethod
    def poll(cls, context):
        return (len(bpy.data.objects) > 0) and (context.mode == 'OBJECT')

    def invoke(self, context, event):
        self.is_not_undo = True
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout

        layout.prop(self, "angle")
        layout.prop(self, "affect")

        layout.prop(self, "set_smooth_shading", icon = "BLANK1")

    def execute(self, context):
        return mu_set_auto_smooth(self, self.angle, self.affect, self.set_smooth_shading)
