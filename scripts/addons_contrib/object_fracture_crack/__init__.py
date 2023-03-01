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
    "name": "Cell Fracture Crack It",
    "author": "ideasman42, phymec, Sergey Sharybin, Nobuyuki Hirakata",
    "version": (1, 0, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Create Tab",
    "description": "Fractured Object, or Cracked Surface",
    "warning": "Developmental",
    "doc_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
               "Scripts/Object/CellFracture",
    "category": "Object",
}


if "bpy" in locals():
    import importlib
    importlib.reload(operator)

else:
    from . import operator

import bpy
from bpy.props import (
        StringProperty,
        BoolProperty,
        IntProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        BoolVectorProperty,
        PointerProperty,
        )

from bpy.types import (
        Panel,
        PropertyGroup,
        )


class OBJECT_PT_FRACTURE_Panel(Panel):
    bl_idname = 'FRACTURE_PT_Panel'
    bl_label = "Fracture It"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Create"
    bl_context = 'objectmode'
    bl_options = {"DEFAULT_CLOSED"}


    def draw(self, context):
        # Show pop-upped menu when the button is hit.
        layout = self.layout
        layout.label(text="Use Fracture It First")
        layout.operator("object.add_fracture_cell",
                    text="Fracture It")
        layout.label(text="Use Crack It To Displace")
        layout.operator(operator.FRACTURE_OT_Crack.bl_idname,
                    text="Crack It")

        material_props = context.window_manager.fracture_material_props
        layout.separator()
        box = layout.box()
        col = box.column()
        row = col.row(align=True)
        col.label(text="Material Preset:")
        col.label(text="Add Materials Last")
        '''
        row_sub = row.row()
        row_sub.prop(material_props, "material_lib_name", text="",
                     toggle=True, icon="LONGDISPLAY")
        '''
        row = box.row()
        row.prop(material_props, "material_preset", text="")

        row = box.row()
        row.operator(operator.FRACTURE_OT_Material.bl_idname, icon="MATERIAL_DATA",
                    text="Append Material")


class FractureCellProperties(PropertyGroup):
    # -------------------------------------------------------------------------
    # Source Options
    source_vert_own: IntProperty(
            name="Own Verts",
            description="Use own vertices",
            min=0, max=2000,
            default=100,
            )
    source_vert_child: IntProperty(
            name="Child Verts",
            description="Use child object vertices",
            min=0, max=2000,
            default=0,
            )
    source_particle_own: IntProperty(
            name="Own Particles",
            description="All particle systems of the source object",
            min=0, max=2000,
            default=0,
            )
    source_particle_child: IntProperty(
            name="Child Particles",
            description="All particle systems of the child objects",
            min=0, max=2000,
            default=0,
            )
    source_pencil: IntProperty(
            name="Annotation Pencil",
            description="Annotation Grease Pencil",
            min=0, max=2000,
            default=0,
            )
    source_random: IntProperty(
            name="Random",
            description="Random seed position",
            min=0, max=2000,
            default=0,
            )
    '''
    source_limit: IntProperty(
            name="Source Limit",
            description="Limit the number of input points, 0 for unlimited",
            min=0, max=5000,
            default=100,
            )
    '''
    # -------------------------------------------------------------------------
    # Transform
    source_noise: FloatProperty(
            name="Noise",
            description="Randomize point distribution",
            min=0.0, max=1.0,
            default=0.0,
            )
    margin: FloatProperty(
            name="Margin",
            description="Gaps for the fracture (gives more stable physics)",
            min=0.0, max=0.5,
            default=0.001,
            )
    cell_scale: FloatVectorProperty(
            name="Scale",
            description="Scale Cell Shape",
            size=3,
            min=0.0, max=1.0,
            default=(1.0, 1.0, 1.0),
            )
    pre_simplify : FloatProperty(
            name="Simplify Base Mesh",
            description="Simplify base mesh before making cell. Lower face size, faster calculation",
            default=0.00,
            min=0.00,
            max=1.00
            )
    use_recenter: BoolProperty(
            name="Recenter",
            description="Recalculate the center points after splitting",
            default=True,
            )
    use_island_split: BoolProperty(
            name="Split Islands",
            description="Split disconnected meshes",
            default=True,
            )
    # -------------------------------------------------------------------------
    # Recursion
    recursion: IntProperty(
            name="Recursion",
            description="Break shards recursively",
            min=0, max=2000,
            default=0,
            )
    recursion_source_limit: IntProperty(
            name="Fracture Each",
            description="Limit the number of input points, 0 for unlimited (applies to recursion only)",
            min=2, max=2000, # Oviously, dividing in more than two objects is needed, to avoid no fracture object.
            default=8,
            )
    recursion_clamp: IntProperty(
            name="Max Fracture",
            description="Finish recursion when this number of objects is reached (prevents recursing for extended periods of time), zero disables",
            min=0, max=10000,
            default=250,
            )
    recursion_chance: FloatProperty(
            name="Recursion Chance",
            description="Likelihood of recursion",
            min=0.0, max=1.0,
            default=1.00,
            )
    recursion_chance_select: EnumProperty(
            name="Target",
            items=(('RANDOM', "Random", ""),
                   ('SIZE_MIN', "Small", "Recursively subdivide smaller objects"),
                   ('SIZE_MAX', "Big", "Recursively subdivide bigger objects"),
                   ('CURSOR_MIN', "Cursor Close", "Recursively subdivide objects closer to the cursor"),
                   ('CURSOR_MAX', "Cursor Far", "Recursively subdivide objects farther from the cursor"),
                   ),
            default='SIZE_MIN',
            )
    # -------------------------------------------------------------------------
    # Interior Meshes Options
    use_smooth_faces: BoolProperty(
            name="Smooth Faces",
            description="Smooth Faces of inner side",
            default=False,
            )
    use_sharp_edges: BoolProperty(
            name="Mark Sharp Edges",
            description="Set sharp edges when disabled",
            default=False,
            )
    use_sharp_edges_apply: BoolProperty(
            name="Edge Split Modifier",
            description="Add edge split modofier for sharp edges",
            default=False,
            )
    use_data_match: BoolProperty(
            name="Copy Original Data",
            description="Match original mesh materials and data layers",
            default=True,
            )
    material_index: IntProperty(
            name="Interior Material Slot",
            description="Material index for interior faces",
            default=0,
            )
    use_interior_vgroup: BoolProperty(
            name="Vertex Group",
            description="Create a vertex group for interior verts",
            default=False,
            )
    # -------------------------------------------------------------------------
    # Scene Options
    use_collection: BoolProperty(
            name="Use Collection",
            description="Use collection to organize fracture objects",
            default=True,
            )
    new_collection: BoolProperty(
            name="New Collection",
            description="Make new collection for fracture objects",
            default=True,
            )
    collection_name: StringProperty(
            name="Name",
            description="Collection name",
            default="Fracture",
            )
    original_hide: BoolProperty(
            name="Hide Original",
            description="Hide original object after cell fracture",
            default=True,
            )
    cell_relocate : BoolProperty(
            name="Move Beside Original",
            description="Move cells beside the original object",
            default=False,
            )
    # -------------------------------------------------------------------------
    # Custom Property Options
    use_mass: BoolProperty(
        name="Mass",
        description="Append mass data on custom properties of cell objects",
        default=False,
        )
    mass_name: StringProperty(
        name="Property Name",
        description="Name for custome properties",
        default="mass",
        )
    mass_mode: EnumProperty(
            name="Mass Mode",
            items=(('VOLUME', "Volume", "Objects get part of specified mass based on their volume"),
                   ('UNIFORM', "Uniform", "All objects get the specified mass"),
                   ),
            default='VOLUME',
            )
    mass: FloatProperty(
            name="Mass Factor",
            description="Mass to give created objects",
            min=0.001, max=1000.0,
            default=1.0,
            )
    # -------------------------------------------------------------------------
    # Debug
    use_debug_points: BoolProperty(
            name="Debug Points",
            description="Create mesh data showing the points used for fracture",
            default=False,
            )

    use_debug_redraw: BoolProperty(
            name="Show Progress Realtime",
            description="Redraw as fracture is done",
            default=False,
            )

    use_debug_bool: BoolProperty(
            name="Debug Boolean",
            description="Skip applying the boolean modifier",
            default=False,
            )


class FractureCrackProperties(PropertyGroup):
    modifier_decimate : FloatProperty(
        name="Reduce Faces",
        description="Apply Decimate Modifier to reduce face number",
        default=0.40,
        min=0.00,
        max=1.00
        )
    modifier_smooth : FloatProperty(
            name="Loose | Tight",
            description="Smooth Modifier",
            default=-0.50,
            min=-3.00,
            max=3.00
            )
    extrude_scale : FloatProperty(
            name="Extrude Blob",
            description="Extrude Scale",
            default=0.00,
            min=0.00,
            max=5.00
            )
    extrude_var : FloatProperty(
            name="Extrude Random ",
            description="Extrude Varriant",
            default=0.01,
            min=-4.00,
            max=4.00
            )
    extrude_num : IntProperty(
            name="Extrude Num",
            description="Extrude Number",
            default=1,
            min=0,
            max=10
            )
    modifier_wireframe : BoolProperty(
            name="Wireframe Modifier",
            description="Wireframe Modifier",
            default=False
            )


class FractureMaterialProperties(PropertyGroup):
    # Note: you can choose the original name in the library blend
    # or the prop name
    material_preset : EnumProperty(
            name="Preset",
            description="Material Preset",
            items=[
                ('crackit_organic_mud', "Organic Mud", "Mud material"),
                ('crackit_mud', "Mud", "Mud material"),
                ('crackit_tree_moss', "Tree Moss", "Tree Material"),
                ('crackit_tree_dry', "Tree Dry", "Tree Material"),
                ('crackit_tree_red', "Tree Red", "Tree Material"),
                ('crackit_rock', "Rock", "Rock Material"),
                ('crackit_lava', "Lava", "Lava Material"),
                ('crackit_wet-paint', "Wet Paint", "Paint Material"),
                ('crackit_soap', "Soap", "Soap Material"),
                ]
            )
    material_lib_name : BoolProperty(
            name="Library Name",
            description="Use the original Material name from the .blend library\n"
                        "instead of the one defined in the Preset",
            default=True
            )

classes = (
    FractureCellProperties,
    FractureCrackProperties,
    FractureMaterialProperties,
    operator.FRACTURE_OT_Cell,
    operator.FRACTURE_OT_Crack,
    operator.FRACTURE_OT_Material,
    OBJECT_PT_FRACTURE_Panel,
    )

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    bpy.types.WindowManager.fracture_cell_props = PointerProperty(
        type=FractureCellProperties
    )
    bpy.types.WindowManager.fracture_crack_props = PointerProperty(
        type=FractureCrackProperties
    )
    bpy.types.WindowManager.fracture_material_props = PointerProperty(
        type=FractureMaterialProperties
    )

def unregister():
    del bpy.types.WindowManager.fracture_material_props
    del bpy.types.WindowManager.fracture_crack_props
    del bpy.types.WindowManager.fracture_cell_props

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
