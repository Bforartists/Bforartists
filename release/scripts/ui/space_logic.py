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
import bpy


class LOGIC_PT_properties(bpy.types.Panel):
    bl_space_type = 'LOGIC_EDITOR'
    bl_region_type = 'UI'
    bl_label = "Properties"

    @staticmethod
    def poll(context):
        ob = context.active_object
        return ob and ob.game

    def draw(self, context):
        layout = self.layout

        ob = context.active_object
        game = ob.game

        layout.operator("object.game_property_new", text="Add Game Property", icon='ZOOMIN')

        for i, prop in enumerate(game.properties):

            box = layout.box()
            row = box.row()
            row.prop(prop, "name", text="")
            row.prop(prop, "type", text="")
            row.prop(prop, "value", text="", toggle=True) # we dont care about the type. rna will display correctly
            row.prop(prop, "debug", text="", toggle=True, icon='INFO')
            row.operator("object.game_property_remove", text="", icon='X', emboss=False).index = i


class LOGIC_MT_logicbricks_add(bpy.types.Menu):
    bl_label = "Add"

    def draw(self, context):
        layout = self.layout

        layout.operator_menu_enum("logic.sensor_add", "type", text="Sensor")
        layout.operator_menu_enum("logic.controller_add", "type", text="Controller")
        layout.operator_menu_enum("logic.actuator_add", "type", text="Actuator")
        

class LOGIC_HT_header(bpy.types.Header):
    bl_space_type = 'LOGIC_EDITOR'

    def draw(self, context):
        layout = self.layout

        st = context.space_data

        row = layout.row(align=True)
        row.template_header()

        if context.area.show_menus:
            sub = row.row(align=True)
            sub.menu("LOGIC_MT_view")
            #sub.menu("LOGIC_MT_select")
            #sub.menu("LOGIC_MT_add")
        

class LOGIC_MT_view(bpy.types.Menu):
    bl_label = "View"

    def draw(self, context):
        layout = self.layout

        layout.column()
        
        layout.operator("logic.properties", icon='MENU_PANEL')


def register():
    pass


def unregister():
    pass

if __name__ == "__main__":
    register()
