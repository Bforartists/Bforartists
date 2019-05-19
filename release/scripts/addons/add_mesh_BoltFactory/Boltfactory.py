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


import bpy
from mathutils import Matrix
from bpy.types import Operator
from bpy_extras.object_utils import AddObjectHelper
from bpy.props import (
        BoolProperty,
        EnumProperty,
        FloatProperty,
        IntProperty,
        FloatVectorProperty,
        )
from . import createMesh




class add_mesh_bolt(Operator, AddObjectHelper):
    bl_idname = "mesh.bolt_add"
    bl_label = "Add Bolt"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    bl_description = "Construct many types of Bolts"


    MAX_INPUT_NUMBER = 50


    # Model Types
    Model_Type_List = [('bf_Model_Bolt', 'BOLT', 'Bolt Model'),
                       ('bf_Model_Nut', 'NUT', 'Nut Model')]
    bf_Model_Type: EnumProperty(
            attr='bf_Model_Type',
            name='Model',
            description='Choose the type off model you would like',
            items=Model_Type_List, default='bf_Model_Bolt'
            )
    # Head Types
    Model_Type_List = [('bf_Head_Hex', 'HEX', 'Hex Head'),
                        ('bf_Head_Cap', 'CAP', 'Cap Head'),
                        ('bf_Head_Dome', 'DOME', 'Dome Head'),
                        ('bf_Head_Pan', 'PAN', 'Pan Head'),
                        ('bf_Head_CounterSink', 'COUNTER SINK', 'Counter Sink Head')]
    bf_Head_Type: EnumProperty(
            attr='bf_Head_Type',
            name='Head',
            description='Choose the type off Head you would like',
            items=Model_Type_List, default='bf_Head_Hex'
            )
    # Bit Types
    Bit_Type_List = [('bf_Bit_None', 'NONE', 'No Bit Type'),
                    ('bf_Bit_Allen', 'ALLEN', 'Allen Bit Type'),
                    ('bf_Bit_Philips', 'PHILLIPS', 'Phillips Bit Type')]
    bf_Bit_Type: EnumProperty(
            attr='bf_Bit_Type',
            name='Bit Type',
            description='Choose the type of bit to you would like',
            items=Bit_Type_List, default='bf_Bit_None'
            )
    # Nut Types
    Nut_Type_List = [('bf_Nut_Hex', 'HEX', 'Hex Nut'),
                    ('bf_Nut_Lock', 'LOCK', 'Lock Nut')]
    bf_Nut_Type: EnumProperty(
            attr='bf_Nut_Type',
            name='Nut Type',
            description='Choose the type of nut you would like',
            items=Nut_Type_List, default='bf_Nut_Hex'
            )
    # Shank Types
    bf_Shank_Length: FloatProperty(
            attr='bf_Shank_Length',
            name='Shank Length', default=0,
            min=0, soft_min=0, max=MAX_INPUT_NUMBER,
            description='Length of the unthreaded shank'
            )
    bf_Shank_Dia: FloatProperty(
            attr='bf_Shank_Dia',
            name='Shank Dia', default=3,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Diameter of the shank'
            )
    bf_Phillips_Bit_Depth: FloatProperty(
            attr='bf_Phillips_Bit_Depth',
            name='Bit Depth', default=1.1431535482406616,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Depth of the Phillips Bit'
            )
    bf_Allen_Bit_Depth: FloatProperty(
            attr='bf_Allen_Bit_Depth',
            name='Bit Depth', default=1.5,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Depth of the Allen Bit'
            )
    bf_Allen_Bit_Flat_Distance: FloatProperty(
            attr='bf_Allen_Bit_Flat_Distance',
            name='Flat Dist', default=2.5,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Flat Distance of the Allen Bit'
            )
    bf_Hex_Head_Height: FloatProperty(
            attr='bf_Hex_Head_Height',
            name='Head Height', default=2,
            min=0, soft_min=0, max=MAX_INPUT_NUMBER,
            description='Height of the Hex Head'
            )
    bf_Hex_Head_Flat_Distance: FloatProperty(
            attr='bf_Hex_Head_Flat_Distance',
            name='Flat Dist', default=5.5,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Flat Distance of the Hex Head'
            )
    bf_CounterSink_Head_Dia: FloatProperty(
            attr='bf_CounterSink_Head_Dia',
            name='Head Dia', default=6.300000190734863,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Diameter of the Counter Sink Head'
            )
    bf_Cap_Head_Height: FloatProperty(
            attr='bf_Cap_Head_Height',
            name='Head Height', default=3,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Height of the Cap Head'
            )
    bf_Cap_Head_Dia: FloatProperty(
            attr='bf_Cap_Head_Dia',
            name='Head Dia', default=5.5,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Diameter of the Cap Head'
            )
    bf_Dome_Head_Dia: FloatProperty(
            attr='bf_Dome_Head_Dia',
            name='Dome Head Dia', default=5.599999904632568,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Length of the unthreaded shank'
            )
    bf_Pan_Head_Dia: FloatProperty(
            attr='bf_Pan_Head_Dia',
            name='Pan Head Dia', default=5.599999904632568,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Diameter of the Pan Head')

    bf_Philips_Bit_Dia: FloatProperty(
            attr='bf_Philips_Bit_Dia',
            name='Bit Dia', default=1.8199999332427979,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Diameter of the Philips Bit')

    bf_Thread_Length: FloatProperty(
            attr='bf_Thread_Length',
            name='Thread Length', default=6,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Length of the Thread')

    bf_Major_Dia: FloatProperty(
            attr='bf_Major_Dia',
            name='Major Dia', default=3,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Outside diameter of the Thread')

    bf_Pitch: FloatProperty(
            attr='bf_Pitch',
            name='Pitch', default=0.3499999940395355,
            min=0.1, soft_min=0.1,
            max=7.0,
            description='Pitch if the thread'
            )
    bf_Minor_Dia: FloatProperty(
            attr='bf_Minor_Dia',
            name='Minor Dia', default=2.6211137771606445,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Inside diameter of the Thread'
            )
    bf_Crest_Percent: IntProperty(
            attr='bf_Crest_Percent',
            name='Crest Percent', default=10,
            min=1, soft_min=1,
            max=90,
            description='Percent of the pitch that makes up the Crest'
            )
    bf_Root_Percent: IntProperty(
            attr='bf_Root_Percent',
            name='Root Percent', default=10,
            min=1, soft_min=1,
            max=90,
            description='Percent of the pitch that makes up the Root'
            )
    bf_Div_Count: IntProperty(
            attr='bf_Div_Count',
            name='Div count', default=36,
            min=4, soft_min=4,
            max=4096,
            description='Div count determine circle resolution'
            )
    bf_Hex_Nut_Height: FloatProperty(
            attr='bf_Hex_Nut_Height',
            name='Hex Nut Height', default=2.4000000953674316,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Height of the Hex Nut'
            )
    bf_Hex_Nut_Flat_Distance: FloatProperty(
            attr='bf_Hex_Nut_Flat_Distance',
            name='Hex Nut Flat Dist', default=5.5,
            min=0, soft_min=0,
            max=MAX_INPUT_NUMBER,
            description='Flat distance of the Hex Nut'
            )

    def draw(self, context):
        layout = self.layout
        col = layout.column()

        # ENUMS
        col.prop(self, 'bf_Model_Type')
        col.separator()

        # Bit
        if self.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(self, 'bf_Bit_Type')
            if self.bf_Bit_Type == 'bf_Bit_None':
                pass
            elif self.bf_Bit_Type == 'bf_Bit_Allen':
                col.prop(self, 'bf_Allen_Bit_Depth')
                col.prop(self, 'bf_Allen_Bit_Flat_Distance')
            elif self.bf_Bit_Type == 'bf_Bit_Philips':
                col.prop(self, 'bf_Phillips_Bit_Depth')
                col.prop(self, 'bf_Philips_Bit_Dia')
            col.separator()
        # Head
        if self.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(self, 'bf_Head_Type')
            if self.bf_Head_Type == 'bf_Head_Hex':
                col.prop(self, 'bf_Hex_Head_Height')
                col.prop(self, 'bf_Hex_Head_Flat_Distance')
            elif self.bf_Head_Type == 'bf_Head_Cap':
                col.prop(self, 'bf_Cap_Head_Height')
                col.prop(self, 'bf_Cap_Head_Dia')
            elif self.bf_Head_Type == 'bf_Head_Dome':
                col.prop(self, 'bf_Dome_Head_Dia')
            elif self.bf_Head_Type == 'bf_Head_Pan':
                col.prop(self, 'bf_Pan_Head_Dia')
            elif self.bf_Head_Type == 'bf_Head_CounterSink':
                col.prop(self, 'bf_CounterSink_Head_Dia')
            col.separator()
        # Shank
        if self.bf_Model_Type == 'bf_Model_Bolt':
            col.label(text='Shank')
            col.prop(self, 'bf_Shank_Length')
            col.prop(self, 'bf_Shank_Dia')
            col.separator()
        # Nut
        if self.bf_Model_Type == 'bf_Model_Nut':
            col.prop(self, 'bf_Nut_Type')
            col.prop(self, 'bf_Hex_Nut_Height')
            col.prop(self, 'bf_Hex_Nut_Flat_Distance')
        # Thread
        col.label(text='Thread')
        if self.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(self, 'bf_Thread_Length')
        col.prop(self, 'bf_Major_Dia')
        col.prop(self, 'bf_Minor_Dia')
        col.prop(self, 'bf_Pitch')
        col.prop(self, 'bf_Crest_Percent')
        col.prop(self, 'bf_Root_Percent')
        col.prop(self, 'bf_Div_Count')

        # generic transform props
        col.separator()
        col.prop(self, 'align')
        col.prop(self, 'location')
        col.prop(self, 'rotation')

    @classmethod
    def poll(cls, context):
        return context.scene is not None

    def execute(self, context):
        createMesh.Create_New_Mesh(self, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)

        return {'FINISHED'}

# Register:
def menu_func_bolt(self, context):
    self.layout.operator(
        add_mesh_bolt.bl_idname,
        text="Bolt",
        icon="MOD_SCREW")

classes = (
    add_mesh_bolt,
)

		
		
def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func_bolt)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func_bolt)
