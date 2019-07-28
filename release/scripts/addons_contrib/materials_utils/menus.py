import bpy

from .functions import *
from .operators import *

# -----------------------------------------------------------------------------
# menu classes

class VIEW3D_MT_materialutilities_assign_material(bpy.types.Menu):
    """Menu for choosing which material should be assigned to current selection"""
    # The menu is filled programmatically with available materials

    bl_idname = "VIEW3D_MT_materialutilities_assign_material"
    bl_label = "Assign Material"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        bl_id = VIEW3D_OT_materialutilities_assign_material_object.bl_idname
        obj = context.object

        if (not obj is None) and obj.mode == 'EDIT':
            bl_id = VIEW3D_OT_materialutilities_assign_material_edit.bl_idname

        for material_name, material in bpy.data.materials.items():
            layout.operator(bl_id,
                text = material_name,
                icon_value = material.preview.icon_id).material_name = material_name

        layout.operator(bl_id,
                        text = "Add New Material",
                        icon = 'ADD').material_name = "Unnamed material"


class VIEW3D_MT_materialutilities_clean_slots(bpy.types.Menu):
    """Menu for cleaning up the material slots"""

    bl_idname = "VIEW3D_MT_materialutilities_clean_slots"
    bl_label = "Clean Slots"

    def draw(self, context):
        layout = self.layout

        layout.label
        layout.operator(VIEW3D_OT_materialutilities_clean_material_slots.bl_idname,
                        text = "Clean Material Slots",
                        icon = 'X')
        layout.separator()
        layout.operator(VIEW3D_OT_materialutilities_remove_material_slot.bl_idname,
                        text = "Remove Active Material Slot",
                        icon = 'REMOVE')
        layout.operator(VIEW3D_OT_materialutilities_remove_all_material_slots.bl_idname,
                        text = "Remove All Material Slots",
                        icon = 'CANCEL')


class VIEW3D_MT_materialutilities_select_by_material(bpy.types.Menu):
    """Menu for choosing which material should be used for selection"""
    # The menu is filled programmatically with available materials

    bl_idname = "VIEW3D_MT_materialutilities_select_by_material"
    bl_label = "Select by Material"

    def draw(self, context):
        layout = self.layout

        obj = context.object
        layout.label

        if obj is None or obj.mode == 'OBJECT':
            #show all used materials in entire blend file
            for material_name, material in bpy.data.materials.items():
                # There's no point in showing materials with 0 users
                #  (It will still show materials with fake user though)
                if material.users > 0:
                    layout.operator(VIEW3D_OT_materialutilities_select_by_material_name.bl_idname,
                                    text = material_name,
                                    icon_value = material.preview.icon_id
                                    ).material_name = material_name

        elif obj.mode == 'EDIT':
            objects = context.selected_editable_objects
            materials_added = []

            for obj in objects:
                #show only the materials on this object
                material_slots = obj.material_slots
                for material_slot in material_slots:
                    material = material_slot.material

                    # Don't add a material that's already in the menu
                    if material.name in materials_added:
                        continue

                    layout.operator(VIEW3D_OT_materialutilities_select_by_material_name.bl_idname,
                        text = material.name,
                        icon_value = material.preview.icon_id
                        ).material_name = material.name

                    materials_added.append(material.name)

class VIEW3D_MT_materialutilities_specials(bpy.types.Menu):
    """Spcials menu for Material Utilities"""

    bl_idname = "VIEW3D_MT_materialutilities_specials"
    bl_label = "Specials"

    def draw(self, context):
        layout = self.layout

        #layout.operator(VIEW3D_OT_materialutilities_set_new_material_name.bl_idname, icon = "SETTINGS")

        #layout.separator()

        layout.operator(MATERIAL_OT_materialutilities_merge_base_names.bl_idname,
                        text = "Merge Base Names",
                        icon = "GREASEPENCIL")


class VIEW3D_MT_materialutilities_main(bpy.types.Menu):
    """Main menu for Material Utilities"""

    bl_idname = "VIEW3D_MT_materialutilities_main"
    bl_label = "Material Utilities"

    def draw(self, context):
        obj = context.object

        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'

        layout.menu(VIEW3D_MT_materialutilities_assign_material.bl_idname,
                     icon = 'ADD')
        layout.menu(VIEW3D_MT_materialutilities_select_by_material.bl_idname,
                     icon = 'VIEWZOOM')
        layout.separator()

        layout.operator(VIEW3D_OT_materialutilities_copy_material_to_others.bl_idname,
                         text = 'Copy Materials to Selected',
                         icon = 'COPY_ID')

        layout.separator()

        layout.menu(VIEW3D_MT_materialutilities_clean_slots.bl_idname,
                    icon = 'NODE_MATERIAL')

        layout.separator()
        layout.operator(VIEW3D_OT_materialutilities_replace_material.bl_idname,
                        text = 'Replace Material',
                        icon = 'OVERLAY')

        layout.operator(VIEW3D_OT_materialutilities_fake_user_set.bl_idname,
                       text = 'Set Fake User',
                       icon = 'FAKE_USER_OFF')

        layout.operator(VIEW3D_OT_materialutilities_change_material_link.bl_idname,
                       text = 'Change Material Link',
                       icon = 'LINKED')
        layout.separator()

        layout.menu(VIEW3D_MT_materialutilities_specials.bl_idname,
                        icon = 'SOLO_ON')



def materialutilities_specials_menu(self, contxt):
    self.layout.separator()
    self.layout.menu(VIEW3D_MT_materialutilities_main.bl_idname)


def materialutilities_menu_move(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'

    layout.operator(MATERIAL_OT_materialutilities_material_slot_move.bl_idname,
                    icon = 'TRIA_UP_BAR',
                    text = 'Move Slot to the Top').movement = 'TOP'
    layout.operator(MATERIAL_OT_materialutilities_material_slot_move.bl_idname,
                    icon = 'TRIA_DOWN_BAR',
                    text = 'Move Slot to the Bottom').movement = 'BOTTOM'
    layout.separator()

def materialutilities_menu_functions(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'

    layout.separator()

    layout.menu(VIEW3D_MT_materialutilities_assign_material.bl_idname,
                 icon = 'ADD')
    layout.menu(VIEW3D_MT_materialutilities_select_by_material.bl_idname,
                 icon = 'VIEWZOOM')
    layout.separator()

    layout.separator()

    layout.menu(VIEW3D_MT_materialutilities_clean_slots.bl_idname,
                icon = 'NODE_MATERIAL')

    layout.separator()
    layout.operator(VIEW3D_OT_materialutilities_replace_material.bl_idname,
                    text = 'Replace Material',
                    icon = 'OVERLAY')

    layout.operator(VIEW3D_OT_materialutilities_fake_user_set.bl_idname,
                   text = 'Set Fake User',
                   icon = 'FAKE_USER_OFF')

    layout.operator(VIEW3D_OT_materialutilities_change_material_link.bl_idname,
                   text = 'Change Material Link',
                   icon = 'LINKED')
    layout.separator()

    layout.menu(VIEW3D_MT_materialutilities_specials.bl_idname,
                    icon = 'SOLO_ON')
