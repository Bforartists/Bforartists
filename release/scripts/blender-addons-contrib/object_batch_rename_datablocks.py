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

bl_info = {
    "name": "Batch Rename Datablocks",
    "author": "tstscr",
    "version": (1, 0),
    "blender": (2, 59, 0),
    "location": "Search > (rename)",
    "description": "Batch renaming of datablocks "
        "(e.g. rename materials after objectnames)",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
        "Scripts/Object/Batch_Rename_Datablocks",
    "tracker_url": "https://developer.blender.org/T25242",
    "category": "Object"}


import bpy
from bpy.props import *

def get_first_material_name(ob):
    for m_slot in ob.material_slots:
        if m_slot.material:
            material_name = m_slot.material.name
            return material_name

def get_name(self, ob):
    if self.naming_base == 'Object':
        return ob.name

    if self.naming_base == 'Mesh':
        if ob.data: return ob.data.name
        else: return ob.name

    if self.naming_base == 'Material':
        material_name = get_first_material_name(ob)
        if not material_name: return ob.name
        else: return material_name

    if self.naming_base == 'Custom':
        return self.rename_custom


def rename_datablocks_main(self, context):
    obs = context.selected_editable_objects
    for ob in obs:
        name = get_name(self, ob)

        if self.rename_object:
            if (self.rename_use_prefix
            and self.prefix_object):
                ob.name = self.rename_prefix + name
            else:
                ob.name = name

        if self.rename_data:
            if (ob.data
            and ob.data.users == 1):
                if (self.rename_use_prefix
                and self.prefix_data):
                    ob.data.name = self.rename_prefix + name
                else:
                    ob.data.name = name

        if self.rename_material:
            if ob.material_slots:
                for m_slot in ob.material_slots:
                    if m_slot.material:
                        if m_slot.material.users == 1:
                            if (self.rename_use_prefix
                            and self.prefix_material):
                                m_slot.material.name = self.rename_prefix + name
                            else:
                                m_slot.material.name = name

class OBJECT_OT_batch_rename_datablocks(bpy.types.Operator):
    """Batch rename Datablocks"""
    bl_idname = "object.batch_rename_datablocks"
    bl_label = "Batch Rename Datablocks"
    bl_options = {'REGISTER', 'UNDO'}

    name_origins = [
                    ('Object', 'Object', 'Object'),
                    ('Mesh', 'Mesh', 'Mesh'),
                    ('Material', 'Material', 'Material'),
                    ('Custom', 'Custom', 'Custom')
                    ]
    naming_base = EnumProperty(name='Name after:',
                                items=name_origins)
    rename_custom = StringProperty(name='Custom Name',
                                default='New Name',
                                description='Rename all with this String')
    rename_object = BoolProperty(name='Rename Objects',
                                default=False,
                                description='Rename Objects')
    rename_data = BoolProperty(name='Rename Data',
                                default=True,
                                description='Rename Object\'s Data')
    rename_material = BoolProperty(name='Rename Materials',
                                default=True,
                                description='Rename Objects\' Materials')
    rename_use_prefix = BoolProperty(name='Add Prefix',
                                default=False,
                                description='Prefix Objectnames with first Groups name')
    rename_prefix = StringProperty(name='Prefix',
                                default='',
                                description='Prefix name with this string')
    prefix_object = BoolProperty(name='Object',
                                default=True,
                                description='Prefix Object Names')
    prefix_data = BoolProperty(name='Data',
                                default=True,
                                description='Prefix Data Names')
    prefix_material = BoolProperty(name='Material',
                                default=True,
                                description='Prefix Material Names')

    dialog_width = 260

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text='Rename after:')

        row = layout.row()
        row.prop(self.properties, 'naming_base', expand=True)

        col = layout.column()
        col.prop(self.properties, 'rename_custom')

        col.separator()
        col.label('Datablocks to rename:')
        col.prop(self.properties, 'rename_object')
        col.prop(self.properties, 'rename_data')
        col.prop(self.properties, 'rename_material')

        col.separator()
        col.prop(self.properties, 'rename_use_prefix')
        col.prop(self.properties, 'rename_prefix')

        row = layout.row()
        row.prop(self.properties, 'prefix_object')
        row.prop(self.properties, 'prefix_data')
        row.prop(self.properties, 'prefix_material')

        col = layout.column()

    @classmethod
    def poll(cls, context):
        return context.selected_objects != None

    def execute(self, context):

        rename_datablocks_main(self, context)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_props_dialog(self, self.dialog_width)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_module(__name__)
    pass
def unregister():
    bpy.utils.unregister_module(__name__)
    pass
if __name__ == '__main__':
    register()
