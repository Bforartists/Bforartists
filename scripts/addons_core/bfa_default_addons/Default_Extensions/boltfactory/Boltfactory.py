# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later
"""
Boltfactory Extension from https://projects.blender.org/extensions/add_mesh_BoltFactory
"""

import bpy
import bmesh
from mathutils import Matrix
from bpy.types import Operator
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
)
from bpy_extras import object_utils
from bpy_extras.object_utils import AddObjectHelper
from . import createMesh


class AddMeshBolt(Operator, AddObjectHelper):
    """
    Builds the pop-up menu with dynamic content
    """
    bl_idname = "mesh.bolt_add"
    bl_label = "Add Bolt"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}
    bl_description = "Construct many types of Bolts"

    MAX_INPUT_NUMBER = 250  # mm

    def update_head_type(self, context):
        """
        Reset the bit type when head type is set to None.
        """
        if self.bf_Head_Type == 'bf_Head_None':
            self.bf_Bit_Type = 'bf_Bit_None'

    Bolt: BoolProperty(name="Bolt",
                       default=True,
                       description="Bolt")
    change: BoolProperty(name="Change",
                         default=False,
                         description="change Bolt")

    bolts_to_change_count: IntProperty(
        name="Number of Bolts to Change",
        default=0,
        description="Stores the count of selected bolts to be changed for UI display"
    )

    # Model Types
    Model_Type_List = [('bf_Model_Bolt', 'BOLT', 'Bolt Model'),
                       ('bf_Model_Nut', 'NUT', 'Nut Model')]
    bf_Model_Type: EnumProperty(
        name='Model',
        description='Choose the type of model you would like',
        items=Model_Type_List, default='bf_Model_Bolt'
    )

    # Head Types
    Head_Type_List = [('bf_Head_None', 'NONE', 'No Head'),
                       ('bf_Head_Hex', 'HEX', 'Hex Head'),
                       ('bf_Head_12Pnt', '12 POINT', '12 Point Head'),
                       ('bf_Head_Cap', 'CAP', 'Cap Head'),
                       ('bf_Head_Dome', 'DOME', 'Dome Head'),
                       ('bf_Head_Pan', 'PAN', 'Pan Head'),
                       ('bf_Head_CounterSink', 'COUNTER SINK', 'Counter Sink Head')]
    bf_Head_Type: EnumProperty(
        name='Head',
        description='Choose the type of Head you would like',
        items=Head_Type_List, default='bf_Head_Hex',
        update=update_head_type  # Call this function when the head type changes
    )

    # Bit Types
    Bit_Type_List = [('bf_Bit_None', 'NONE', 'No Bit Type'),
                     ('bf_Bit_Allen', 'ALLEN', 'Allen Bit Type'),
                     ('bf_Bit_Torx', 'TORX', 'Torx Bit Type'),
                     ('bf_Bit_Robertson', 'ROBERTSON', 'Robertson Bit Type (Square)'),
                     ('bf_N_Bit_Allen', 'N SIDED ALLEN', 'Allen Bit Type with any number of faces'),
                     ('bf_Bit_Star', 'STAR', 'Six pointed Star Bit Type'),
                     ('bf_Bit_Double_Square', 'DOUBLE SQUARE', 'Eight pointed Bit Type'),
                     ('bf_Double_Hex', 'DOUBLE HEX', '12 pointed Bit Type as two hexagons'),
                     ('bf_Triple_Square_XZN', 'TRIPLE SQUARE XZN', '12 pointed Bit Type as three Squares'),
                     ('bf_12_Spline', '12 SPLINE', '12 pointed Bit Type as four Triangles'),
                     ('bf_Bit_Philips', 'PHILLIPS', 'Phillips Bit Type')]
    bf_Bit_Type: EnumProperty(
        name='Bit Type',
        description='Choose the type of bit to you would like',
        items=Bit_Type_List, default='bf_Bit_None'
    )

    # Nut Types
    Nut_Type_List = [('bf_Nut_Hex', 'REGULAR', 'Regular Flat Nut'),
                     ('bf_Nut_Lock', 'LOCK', 'Lock Nut'),
                     ('bf_Nut_12Pnt', '12 POINT', '12 Point Nut')]
    bf_Nut_Type: EnumProperty(
        name='Nut Type',
        description='Choose the type of nut you would like',
        items=Nut_Type_List, default='bf_Nut_Hex'
    )

    # Shank Properties
    bf_Shank_Length: FloatProperty(
        name='Shank Length (mm)', default=0,
        min=0, soft_min=0, max=MAX_INPUT_NUMBER,
        description='Length of the unthreaded shank',
        unit='NONE',
    )
    bf_Shank_Dia: FloatProperty(
        name='Shank Dia (mm)', default=3,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Diameter of the shank',
        unit='NONE',
    )

    # Bit Properties
    # DIN 7985 - Phillips Pan Head Screws (type H recess) or the ISO 7045.
    bf_Phillips_Bit_Depth: FloatProperty(
        name='Bit Depth (mm)', default=1.1431535482406616,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Depth of the Phillips Bit',
        unit='NONE',
    )
    bf_Philips_Bit_Dia: FloatProperty(
        name='Bit Dia (mm)', default=1.8199999332427979,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Diameter of the Philips Bit',
        unit='NONE',
    )
    bf_Allen_Bit_Depth: FloatProperty(
        name='Bit Depth (mm)', default=1.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Depth of the Allen Bit',
        unit='NONE',
    )
    bf_Allen_Bit_Flat_Distance: FloatProperty(
        name='Flat Dist (mm)', default=2.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Flat Distance of the Allen Bit',
        unit='NONE',
    )

    # Robertson
    Robertson_Size_Type_List = [('bf_Robertson_R00', 'Size: R00', 'R00, for M2'),       # M2
                                ('bf_Robertson_R0', 'Size: R0', 'R0 for M2.5 & M3'),    # M2.5 / M3
                                ('bf_Robertson_R1', 'Size: R1', 'R1 for M3.5'),         # M3.5
                                ('bf_Robertson_R2', 'Size: R2', 'R2 for M4 & M5'),      # M4 / M5
                                ('bf_Robertson_R3', 'Size: R3', 'R3 for M6'),           # M6
                                ('bf_Robertson_R4', 'Size: R4', 'R4 for M8 & M10'),     # M8 / M10
                                ]
    bf_Robertson_Size_Type: EnumProperty(
        name='Robertson',
        description='Size of the Robertson Bit',
        items=Robertson_Size_Type_List, default='bf_Robertson_R0'
    )
    bf_Security_Bit: BoolProperty(
        name='Security pin', default=0,
        description='Adds a central security tab or pin in the bit'
    )

    # Torx Size Properties
    Torx_Size_Type_List = [('bf_Torx_T6', 'T6', 'T6'),
                           ('bf_Torx_T8', 'T8', 'T8'),
                           ('bf_Torx_T10', 'T10', 'T10'),
                           ('bf_Torx_T15', 'T15', 'T15'),
                           ('bf_Torx_T20', 'T20', 'T20'),
                           ('bf_Torx_T25', 'T25', 'T25'),
                           ('bf_Torx_T30', 'T30', 'T30'),
                           ('bf_Torx_T40', 'T40', 'T40'),
                           ('bf_Torx_T45', 'T45', 'T45'),
                           ('bf_Torx_T50', 'T50', 'T50'),
                           ('bf_Torx_T55', 'T55', 'T55'),
                           ('bf_Torx_T60', 'T60', 'T60'),
                           ('bf_Torx_T70', 'T70', 'T70'),
                           ('bf_Torx_T80', 'T80', 'T80'),
                           ('bf_Torx_T90', 'T90', 'T90'),
                           ('bf_Torx_T100', 'T100', 'T100'),
                           ]
    bf_Torx_Size_Type: EnumProperty(
        name='Torx Size',
        description='Size of the Torx Bit',
        items=Torx_Size_Type_List, default='bf_Torx_T10'
    )
    bf_Torx_Bit_Depth: FloatProperty(
        name='Bit Depth (mm)', default=1.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Depth of the Torx Bit',
        unit='NONE',
    )
    bf_N_Sided_Bit: IntProperty(
        name='Bit Side Count', default=6,
        min=3, soft_min=3,
        max=16,
        description='Number of sides for a bit',
    )

    # Bolt Head Properties
    bf_Hex_Head_Height: FloatProperty(
        name='Head Height (mm)', default=2,
        min=0, soft_min=0, max=MAX_INPUT_NUMBER,
        description='Height of the Head',
        unit='NONE',
    )
    bf_Hex_Head_Flat_Distance: FloatProperty(
        name='Flat Dist (mm)', default=5.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Flat Distance of the Head',
        unit='NONE',
    )
    bf_12_Point_Head_Height: FloatProperty(
        name='Head Height (mm)', default=3.0,
        min=0, soft_min=0, max=MAX_INPUT_NUMBER,
        description='Height of the 12 Point Head',
        unit='NONE',
    )
    bf_12_Point_Head_Flat_Distance: FloatProperty(
        name='Flat Dist (mm)', default=3.0,
        min=0.001, soft_min=0,  # limit to 0.001 to avoid calculation error
        max=MAX_INPUT_NUMBER,
        description='Flat Distance of the 12 Point Head',
        unit='NONE',
    )
    bf_12_Point_Head_Flange_Dia: FloatProperty(
        name='12 Point Head Flange Dia (mm)', default=5.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Flange diameter of the 12 point Head',
        unit='NONE',
    )
    bf_CounterSink_Head_Dia: FloatProperty(
        name='Head Dia (mm)', default=6.300000190734863,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Diameter of the Counter Sink Head',
        unit='NONE',
    )
    bf_CounterSink_Head_Angle: FloatProperty(
        name='Head angle', default=1.5708,
        min=0.5, soft_min=0.5,
        max=2.62,
        description='Included Angle of the Counter Sink Head',
        unit='ROTATION',
    )
    bf_Cap_Head_Height: FloatProperty(
        name='Head Height (mm)', default=3,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Height of the Cap Head',
        unit='NONE',
    )
    bf_Cap_Head_Dia: FloatProperty(
        name='Head Dia (mm)', default=5.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Diameter of the Cap Head',
        unit='NONE',
    )
    bf_Dome_Head_Dia: FloatProperty(
        name='Dome Head Dia (mm)', default=5.599999904632568,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Length of the unthreaded shank',
        unit='NONE',
    )
    bf_Pan_Head_Dia: FloatProperty(
        name='Pan Head Dia (mm)', default=5.599999904632568,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Diameter of the Pan Head',
        unit='NONE',
    )

    # Thread Properties
    bf_Thread_Length: FloatProperty(
        name='Thread Length (mm)', default=6,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Length of the Thread',
        unit='NONE',
    )
    bf_Major_Dia: FloatProperty(
        name='Major Dia (mm)', default=3,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Outside diameter of the Thread',
        unit='NONE',
    )
    bf_Pitch: FloatProperty(
        name='Pitch (mm)', default=0.3499999940395355,
        min=0.1, soft_min=0.1,
        soft_max=7,
        description='Pitch of the thread',
        unit='NONE',
    )
    bf_Minor_Dia: FloatProperty(
        name='Minor Dia (mm)', default=2.6211137771606445,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Core diameter of the thread. Defines the root for bolts and the crest for nuts',
        unit='NONE',
    )
    Thread_Root_Type_List = [('FLAT', 'Flat', 'A flat thread root, like a standard UN profile.'),
                             ('TRIANGLE', 'Triangle', 'A simple triangular thread root (V-thread).')]
    bf_Thread_Root_Type: EnumProperty(
        name='Thread Root Type',
        description='Choose the shape of the thread root',
        items=Thread_Root_Type_List, default='FLAT'
    )
    bf_Rounded_Root_Dia: FloatProperty(
        name='Rounded Root Dia (mm)', default=2.571,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Diameter for rounded thread root',
        unit='NONE',
    )
    bf_Crest_Percent: FloatProperty(
        name='Crest Percent', default=12.5,
        min=1, soft_min=1,
        max=90,
        description='Percent of the pitch that makes up the Crest',
    )
    bf_Root_Percent: FloatProperty(
        name='Root Percent', default=25,
        min=1, soft_min=1,
        max=90,
        description='Percent of the pitch that makes up the Root',
    )

    # Resolution
    bf_Div_Count: IntProperty(
        name='Div count', default=36,
        min=4, soft_min=4,
        max=4096,
        description='Div count determine circle resolution',
    )

    # Nut Properties
    bf_Hex_Nut_Height: FloatProperty(
        name='Nut Height (mm)', default=2.4000000953674316,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Height of the Nut',
        unit='NONE',
    )
    bf_N_Sided: IntProperty(
        name='Side Count', default=6,
        min=3, soft_min=3,
        max=16,
        description='Number of sides (faces)',
    )
    bf_Hex_Nut_Flat_Distance: FloatProperty(
        name='Nut Flat Dist (mm)', default=5.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Flat distance of the Nut',
        unit='NONE',
    )
    bf_12_Point_Nut_Height: FloatProperty(
        name='12 Point Nut Height (mm)', default=2.4000000953674316,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Height of the 12 Point Nut',
        unit='NONE',
    )
    bf_12_Point_Nut_Flat_Distance: FloatProperty(
        name='12 Point Nut Flat Dist (mm)', default=3.0,
        min=0.001, soft_min=0,  # limit to 0.001 to avoid calculation error
        max=MAX_INPUT_NUMBER,
        description='Flat distance of the 12 point Nut',
        unit='NONE',
    )
    bf_12_Point_Nut_Flange_Dia: FloatProperty(
        name='12 Point Nut Flange Dia (mm)', default=5.5,
        min=0, soft_min=0,
        max=MAX_INPUT_NUMBER,
        description='Flange diameter of the 12 point Nut',
        unit='NONE',
    )

    def _update_bolt_properties(self, obj):
        """Helper function to set custom properties on a bolt object."""
        obj.data["Bolt"] = True
        obj.data["change"] = False

        for param_name in BoltParameters():
            if hasattr(self, param_name):
                try:
                    obj.data[param_name] = getattr(self, param_name)
                except TypeError as e:
                    print(f"Warning: Type error setting {param_name} on {obj.name}: {e}")

    def draw(self, context):
        """
        This function actually builds the pop-up GUI
        """
        layout = self.layout

        if self.change and self.bolts_to_change_count > 1:
            label_text = f"Changing {self.bolts_to_change_count} Selected Bolts:"
            box = layout.box()
            box.label(text=label_text, icon='INFO')

        col = layout.column()

        # Nut or Bolt
        col.prop(self, 'bf_Model_Type')
        col.separator()

        # Bit
        if self.bf_Model_Type == 'bf_Model_Bolt':
            if self.bf_Head_Type == 'bf_Head_None':
                col.label(text="No bit type available when Head is None.")
            else:
                col.prop(self, 'bf_Bit_Type')
            if self.bf_Bit_Type == 'bf_Bit_None':
                pass
            elif self.bf_Bit_Type == 'bf_Bit_Allen':
                col.prop(self, 'bf_Allen_Bit_Depth')
                col.prop(self, 'bf_Allen_Bit_Flat_Distance')
            elif self.bf_Bit_Type == 'bf_Bit_Torx':
                col.prop(self, 'bf_Torx_Bit_Depth')
                col.prop(self, 'bf_Torx_Size_Type')
            elif self.bf_Bit_Type == 'bf_Bit_Robertson':
                col.prop(self, 'bf_Security_Bit')
                col.prop(self, 'bf_Robertson_Size_Type')
            elif self.bf_Bit_Type == 'bf_N_Bit_Allen':
                col.prop(self, 'bf_Security_Bit')
                col.prop(self, 'bf_N_Sided_Bit')
                col.prop(self, 'bf_Allen_Bit_Depth')
                col.prop(self, 'bf_Allen_Bit_Flat_Distance')
            elif (self.bf_Bit_Type in ['bf_Bit_Star', 'bf_Bit_Double_Square', 'bf_Double_Hex',
                                       'bf_Triple_Square_XZN', 'bf_12_Spline']):
                col.prop(self, 'bf_Security_Bit')
                col.prop(self, 'bf_Allen_Bit_Depth')
                col.prop(self, 'bf_Allen_Bit_Flat_Distance')
            elif self.bf_Bit_Type == 'bf_Bit_Philips':
                col.prop(self, 'bf_Phillips_Bit_Depth')
                col.prop(self, 'bf_Philips_Bit_Dia')
            col.separator()

        # Head
        if self.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(self, 'bf_Head_Type')
            if self.bf_Head_Type == 'bf_Head_None':
                pass
            elif self.bf_Head_Type == 'bf_Head_Hex':
                col.prop(self, 'bf_Hex_Head_Height')
                col.prop(self, 'bf_Hex_Head_Flat_Distance')
                col.prop(self, 'bf_N_Sided')
            elif self.bf_Head_Type == 'bf_Head_12Pnt':
                col.prop(self, 'bf_12_Point_Head_Height')
                col.prop(self, 'bf_12_Point_Head_Flat_Distance')
                col.prop(self, 'bf_12_Point_Head_Flange_Dia')
            elif self.bf_Head_Type == 'bf_Head_Cap':
                col.prop(self, 'bf_Cap_Head_Height')
                col.prop(self, 'bf_Cap_Head_Dia')
            elif self.bf_Head_Type == 'bf_Head_Dome':
                col.prop(self, 'bf_Dome_Head_Dia')
            elif self.bf_Head_Type == 'bf_Head_Pan':
                col.prop(self, 'bf_Pan_Head_Dia')
            elif self.bf_Head_Type == 'bf_Head_CounterSink':
                col.prop(self, 'bf_CounterSink_Head_Dia')
                col.prop(self, 'bf_CounterSink_Head_Angle')
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
            if self.bf_Nut_Type == "bf_Nut_12Pnt":
                col.prop(self, 'bf_12_Point_Nut_Height')
                col.prop(self, 'bf_12_Point_Nut_Flat_Distance')
                col.prop(self, 'bf_12_Point_Nut_Flange_Dia')
            else:
                col.prop(self, 'bf_Hex_Nut_Height')
                col.prop(self, 'bf_Hex_Nut_Flat_Distance')
                col.prop(self, 'bf_N_Sided')

        # Thread
        col.label(text='Thread')
        if self.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(self, 'bf_Thread_Length')
        col.prop(self, 'bf_Major_Dia')
        col.prop(self, 'bf_Minor_Dia')
        col.prop(self, 'bf_Pitch')
        col.separator()
        if self.bf_Model_Type == 'bf_Model_Bolt':
            col.prop(self, 'bf_Thread_Root_Type', text="Root Shape")
            if self.bf_Thread_Root_Type == 'TRIANGLE':
                col.prop(self, 'bf_Rounded_Root_Dia')
            col.separator()
        col.prop(self, 'bf_Crest_Percent')
        col.prop(self, 'bf_Root_Percent')
        col.prop(self, 'bf_Div_Count')

        if not self.change:
            # generic transform props
            col.separator()
            col.prop(self, 'align')
            col.prop(self, 'location')
            col.prop(self, 'rotation')

    @classmethod
    def poll(cls, context):
        """Standard Blender gatekeeper"""
        return context.scene is not None

    def execute(self, context):
        """
        If the poll passes this function either modifies a mesh or creates a new one
        """
        # 1. SETUP AND VALIDATION
        if self.change:
            selected_valid_bolts = [
                obj for obj in context.selected_objects
                if obj.type == 'MESH' and obj.data and 'Bolt' in obj.data
            ]
            active_obj = context.active_object
            # Simplified validation condition
            if not (active_obj and active_obj in selected_valid_bolts):
                self.report(
                    {'WARNING'},
                    "Active object must be a valid, selected Bolt, and at least one Bolt must be selected."
                )
                return {'CANCELLED'}

        # This formula ensures that bolts (or other objects) are generated at their default sizes
        # regardless of the unit scale setting in the scene. It normalizes the scale to maintain
        # consistent dimensions across various unit configurations.
        scene = context.scene
        adjusted_scale = 0.001 / scene.unit_settings.scale_length

        # Prevent geometry collapse due to distance between scene scale 1 and 0.001
        dynamic_merge_dist = 0.0001 * adjusted_scale

        # 2. SOURCE MESH CREATION
        mesh_data_block = createMesh.create_new_mesh(self, context, adjusted_scale)
        if not mesh_data_block:
            self.report({'ERROR'}, "Failed to create source mesh geometry.")
            return {'CANCELLED'}

        final_objects_affected_names = []

        # 3. MAIN LOGIC WITH GUARANTEED CLEANUP
        try:
            current_mode = context.mode

            if self.change:
                # --- UPDATE EXISTING BOLTS (Object Mode only) ---
                bm = bmesh.new()
                try:
                    bm.from_mesh(mesh_data_block)
                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dynamic_merge_dist)

                    for obj in selected_valid_bolts:
                        # More Pythonic way to check for any smooth polygon
                        is_smooth = any(p.use_smooth for p in obj.data.polygons)

                        bm.to_mesh(obj.data)

                        for p in obj.data.polygons:
                            p.use_smooth = is_smooth

                        obj.data.update()
                        self._update_bolt_properties(obj)
                        final_objects_affected_names.append(obj.name)
                finally:
                    bm.free()  # Ensure bmesh is always freed

            elif current_mode == "OBJECT":
                # --- CREATE NEW BOLT ---
                bm = bmesh.new()
                try:
                    bm.from_mesh(mesh_data_block)
                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dynamic_merge_dist)
                    bm.to_mesh(mesh_data_block)
                finally:
                    bm.free()

                new_obj = object_utils.object_data_add(context, mesh_data_block, operator=self)
                if new_obj:
                    self._update_bolt_properties(new_obj)
                    final_objects_affected_names.append(new_obj.name)

            elif current_mode == "EDIT_MESH":
                # --- ADD GEOMETRY IN EDIT MODE ---
                obj = context.edit_object
                bm_edit = bmesh.from_edit_mesh(obj.data)

                temp_bm = bmesh.new()
                try:
                    temp_bm.from_mesh(mesh_data_block)

                    # Use a single matrix for transformation
                    mat_world = Matrix.Translation(self.location) @ self.rotation.to_matrix().to_4x4()
                    mat_local = obj.matrix_world.inverted() @ mat_world

                    bmesh.ops.transform(temp_bm, matrix=mat_local, verts=temp_bm.verts)

                    # Convert temp_bm to a mesh, then import it into bm_edit
                    temp_mesh = bpy.data.meshes.new(name="TempBoltMesh")
                    temp_bm.to_mesh(temp_mesh)
                    temp_bm.free()

                    # Append the new mesh geometry into the edit bmesh
                    bm_edit.from_mesh(temp_mesh)

                    # Clean up the temporary mesh datablock
                    bpy.data.meshes.remove(temp_mesh)

                    # Optional: remove doubles to merge overlapping vertices
                    bmesh.ops.remove_doubles(bm_edit, verts=bm_edit.verts, dist=dynamic_merge_dist)

                    bm_edit.normal_update()
                    bmesh.update_edit_mesh(obj.data)
                    final_objects_affected_names.append(obj.name)
                finally:
                    temp_bm.free()

        except Exception as e:
            self.report({'ERROR'}, f"Operation failed: {str(e)}")
            return {'CANCELLED'}
        finally:
            # Centralized cleanup for the source mesh datablock
            if mesh_data_block and not mesh_data_block.users:
                bpy.data.meshes.remove(mesh_data_block)

        return {'FINISHED'}


# Register functions:

def bolt_contex_menu(self, context):
    """
    Function to add or remove the right click context menu.
    Only presents as visible when a Boltfactory object is currently selected.
    """
    obj = context.object
    layout = self.layout
    active_obj = context.active_object
    # Explicitly get the list of currently selected objects
    selected_objects = context.selected_objects

    # Check if the active object itself is a valid, selected bolt
    is_active_obj_valid_bolt_for_ui = (active_obj
                                       and active_obj in selected_objects
                                       and active_obj.type == 'MESH'
                                       and active_obj.data
                                       and 'Bolt' in active_obj.data.keys()
                                       )

    # Count how many of the currently selected objects are valid bolts
    selected_valid_bolts = [
        obj for obj in selected_objects
        if obj.type == 'MESH' and obj.data and 'Bolt' in obj.data.keys()
    ]

    # Show the menu item if the active object can source parameters AND
    # there's at least one valid bolt selected (which would include the active one)
    if is_active_obj_valid_bolt_for_ui and len(selected_valid_bolts) > 0:
        if active_obj.data['bf_Model_Type'] == 'bf_Model_Nut':
            op_text = "Change Nut..."
        else:
            op_text = "Change Bolt..."
        if len(selected_valid_bolts) > 1:
            op_text = f"Change {len(selected_valid_bolts)} Selected Bolts"

        # If all conditions pass, draw the "Change Bolt" operator button
        props = layout.operator("mesh.bolt_add", text=op_text)
        props.change = True
        props.bolts_to_change_count = len(selected_valid_bolts)

        # Load parameters from the active_obj as the baseline for the UI
        for prm in BoltParameters():  # Assuming BoltParameters() is your list of property names
            if prm in active_obj.data:  # Check if parameter exists on the object's data
                value_to_set = active_obj.data[prm]
                setattr(props, prm, value_to_set)
            else:
                # This case means a parameter defined in BoltParameters()
                # is not present in the active_obj.data.
                # You might want to log this or decide on a default.
                # For now, we'll just skip setting it on 'props',
                # which means the operator might use its own default for that property.
                # print(f"Warning: Parameter '{prm}' not found in data of '{active_obj.name}'")
                pass
        layout.separator()


def menu_func_bolt(self, context):
    """
    Function to populate or remove the toolbar menu entry
    Menu -> Add -> Mesh -> Bolt
    """
    layout = self.layout
    layout.separator()
    oper = self.layout.operator(AddMeshBolt.bl_idname, text="Bolt", icon="MOD_SCREW")
    oper.change = False


classes = (
    AddMeshBolt,
)


def register():
    """Register Boltfactory in Blender, called from init.py"""
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func_bolt)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(bolt_contex_menu)


def unregister():
    """Un-Register Boltfactory in Blender, called from init.py"""
    bpy.types.VIEW3D_MT_object_context_menu.remove(bolt_contex_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func_bolt)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


def BoltParameters():
    """
    These are all the parameters that are stored to make a BoltFactory object.
    This list needs to match the preset files & GUI element variables.
    :return: A list of strings list for each of the parameters.
    """
    BoltParameters = [
        "bf_Model_Type",
        "bf_Head_Type",
        "bf_Bit_Type",
        "bf_Nut_Type",
        "bf_Shank_Length",
        "bf_Shank_Dia",
        "bf_Phillips_Bit_Depth",
        "bf_Allen_Bit_Depth",
        "bf_Allen_Bit_Flat_Distance",
        "bf_Torx_Bit_Depth",
        "bf_Robertson_Size_Type",
        "bf_Security_Bit",
        "bf_N_Sided_Bit",
        "bf_Torx_Size_Type",
        "bf_Hex_Head_Height",
        "bf_Hex_Head_Flat_Distance",
        "bf_N_Sided",
        "bf_12_Point_Head_Height",
        "bf_12_Point_Head_Flat_Distance",
        "bf_12_Point_Head_Flange_Dia",
        "bf_CounterSink_Head_Dia",
        "bf_CounterSink_Head_Angle",
        "bf_Cap_Head_Height",
        "bf_Cap_Head_Dia",
        "bf_Dome_Head_Dia",
        "bf_Pan_Head_Dia",
        "bf_Philips_Bit_Dia",
        "bf_Thread_Length",
        "bf_Major_Dia",
        "bf_Pitch",
        "bf_Rounded_Root_Dia",
        "bf_Minor_Dia",
        "bf_Thread_Root_Type",
        "bf_Crest_Percent",
        "bf_Root_Percent",
        "bf_Div_Count",
        "bf_Hex_Nut_Height",
        "bf_Hex_Nut_Flat_Distance",
        "bf_12_Point_Nut_Height",
        "bf_12_Point_Nut_Flat_Distance",
        "bf_12_Point_Nut_Flange_Dia",
    ]
    return BoltParameters
