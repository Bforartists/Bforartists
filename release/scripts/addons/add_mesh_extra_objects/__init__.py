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
# Contributed to by:
# Pontiac, Fourmadmen, varkenvarken, tuga3d, meta-androcto, metalliandy     #
# dreampainter, cotejrp1, liero, Kayo Phoenix, sugiany, dommetysk, Jambay   #
# Phymec, Anthony D'Agostino, Pablo Vazquez, Richard Wilks, lijenstina,     #
# Sjaak-de-Draak, Phil Cote, cotejrp1, xyz presets by elfnor, revolt_randy, #


bl_info = {
    "name": "Extra Objects",
    "author": "Multiple Authors",
    "version": (0, 3, 3),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Add extra mesh object types",
    "warning": "",
    "wiki_url": "https://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/Add_Mesh/Add_Extra",
    "category": "Add Mesh",
}

# Note: Blocks has to be loaded before the WallFactory or the script
#       will not work properly after (F8) reload

if "bpy" in locals():
    import importlib
    importlib.reload(add_mesh_star)
    importlib.reload(add_mesh_twisted_torus)
    importlib.reload(add_mesh_gemstones)
    importlib.reload(add_mesh_gears)
    importlib.reload(add_mesh_3d_function_surface)
    importlib.reload(add_mesh_round_cube)
    importlib.reload(add_mesh_supertoroid)
    importlib.reload(add_mesh_pyramid)
    importlib.reload(add_mesh_torusknot)
    importlib.reload(add_mesh_honeycomb)
    importlib.reload(add_mesh_teapot)
    importlib.reload(add_mesh_pipe_joint)
    importlib.reload(add_mesh_solid)
    importlib.reload(add_mesh_round_brilliant)
    importlib.reload(add_mesh_menger_sponge)
    importlib.reload(add_mesh_vertex)
    importlib.reload(add_empty_as_parent)
    importlib.reload(mesh_discombobulator)
    importlib.reload(add_mesh_beam_builder)
    importlib.reload(Blocks)
    importlib.reload(Wallfactory)
    importlib.reload(add_mesh_triangles)
else:
    from . import add_mesh_star
    from . import add_mesh_twisted_torus
    from . import add_mesh_gemstones
    from . import add_mesh_gears
    from . import add_mesh_3d_function_surface
    from . import add_mesh_round_cube
    from . import add_mesh_supertoroid
    from . import add_mesh_pyramid
    from . import add_mesh_torusknot
    from . import add_mesh_honeycomb
    from . import add_mesh_teapot
    from . import add_mesh_pipe_joint
    from . import add_mesh_solid
    from . import add_mesh_round_brilliant
    from . import add_mesh_menger_sponge
    from . import add_mesh_vertex
    from . import add_empty_as_parent
    from . import mesh_discombobulator
    from . import add_mesh_beam_builder
    from . import Blocks
    from . import Wallfactory
    from . import add_mesh_triangles

import bpy
from bpy.types import Menu

class VIEW3D_MT_mesh_vert_add(Menu):
    # Define the "Single Vert" menu
    bl_idname = "VIEW3D_MT_mesh_vert_add"
    bl_label = "Single Vert"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_vert_add",
                        text="Add Single Vert")
        layout.separator()
        layout.operator("mesh.primitive_emptyvert_add",
                        text="Object Origin Only")
        layout.operator("mesh.primitive_symmetrical_vert_add",
                        text="Origin & Vert Mirrored")
        layout.operator("mesh.primitive_symmetrical_empty_add",
                        text="Object Origin Mirrored")


class VIEW3D_MT_mesh_gears_add(Menu):
    # Define the "Gears" menu
    bl_idname = "VIEW3D_MT_mesh_gears_add"
    bl_label = "Gears"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_gear",
                        text="Gear")
        layout.operator("mesh.primitive_worm_gear",
                        text="Worm")


class VIEW3D_MT_mesh_diamonds_add(Menu):
    # Define the "Diamonds" menu
    bl_idname = "VIEW3D_MT_mesh_diamonds_add"
    bl_label = "Diamonds"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_brilliant_add",
                        text="Brilliant Diamond")
        layout.operator("mesh.primitive_diamond_add",
                        text="Diamond")
        layout.operator("mesh.primitive_gem_add",
                        text="Gem")


class VIEW3D_MT_mesh_math_add(Menu):
    # Define the "Math Function" menu
    bl_idname = "VIEW3D_MT_mesh_math_add"
    bl_label = "Math Functions"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_z_function_surface",
                        text="Z Math Surface")
        layout.operator("mesh.primitive_xyz_function_surface",
                        text="XYZ Math Surface")
        self.layout.operator("mesh.primitive_solid_add", text="Regular Solid")
        self.layout.operator("mesh.make_triangle", icon="MESH_DATA")


class VIEW3D_MT_mesh_mech(Menu):
    # Define the "Math Function" menu
    bl_idname = "VIEW3D_MT_mesh_mech_add"
    bl_label = "Mechanical"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_mesh_pipe_joints_add",
                text="Pipe Joints")
        layout.menu("VIEW3D_MT_mesh_gears_add",
                text="Gears")


class VIEW3D_MT_mesh_extras_add(Menu):
    # Define the "Extra Objects" menu
    bl_idname = "VIEW3D_MT_mesh_extras_add"
    bl_label = "Extras"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.menu("VIEW3D_MT_mesh_diamonds_add", text="Diamonds",
                    icon="PMARKER_SEL")
        layout.separator()
        layout.operator("mesh.add_beam",
                        text="Beam Builder")
        layout.operator("mesh.wall_add",
                        text="Wall Factory")
        layout.separator()
        layout.operator("mesh.primitive_star_add",
                        text="Simple Star")
        layout.operator("mesh.primitive_steppyramid_add",
                        text="Step Pyramid")
        layout.operator("mesh.honeycomb_add",
                        text="Honeycomb")
        layout.operator("mesh.primitive_teapot_add",
                        text="Teapot+")
        layout.operator("mesh.menger_sponge_add",
                        text="Menger Sponge")


class VIEW3D_MT_mesh_torus_add(Menu):
    # Define the "Torus Objects" menu
    bl_idname = "VIEW3D_MT_mesh_torus_add"
    bl_label = "Torus Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_twisted_torus_add",
                        text="Twisted Torus")
        layout.operator("mesh.primitive_supertoroid_add",
                        text="Supertoroid")
        layout.operator("mesh.primitive_torusknot_add",
                        text="Torus Knot")


class VIEW3D_MT_mesh_pipe_joints_add(Menu):
    # Define the "Pipe Joints" menu
    bl_idname = "VIEW3D_MT_mesh_pipe_joints_add"
    bl_label = "Pipe Joints"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        layout.operator("mesh.primitive_elbow_joint_add",
                        text="Pipe Elbow")
        layout.operator("mesh.primitive_tee_joint_add",
                        text="Pipe T-Joint")
        layout.operator("mesh.primitive_wye_joint_add",
                        text="Pipe Y-Joint")
        layout.operator("mesh.primitive_cross_joint_add",
                        text="Pipe Cross-Joint")
        layout.operator("mesh.primitive_n_joint_add",
                        text="Pipe N-Joint")

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    lay_out = self.layout
    lay_out.operator_context = 'INVOKE_REGION_WIN'

    lay_out.separator()
    lay_out.menu("VIEW3D_MT_mesh_vert_add",
                text="Single Vert")
    lay_out.operator("mesh.primitive_round_cube_add",
                    text="Round Cube")
    lay_out.menu("VIEW3D_MT_mesh_math_add",
                text="Math Function", icon="PACKAGE")
    lay_out.menu("VIEW3D_MT_mesh_mech_add",
                text="Mechanical")
    lay_out.menu("VIEW3D_MT_mesh_torus_add",
                text="Torus Objects")
    lay_out.separator()
    lay_out.operator("discombobulate.ops",
                    text="Discombobulator")
    lay_out.separator()
    lay_out.menu("VIEW3D_MT_mesh_extras_add",
                text="Extras")
    lay_out.separator()
    lay_out.operator("object.parent_to_empty",
                    text="Parent To Empty")

# Register
classes = [
    VIEW3D_MT_mesh_vert_add,
    VIEW3D_MT_mesh_gears_add,
    VIEW3D_MT_mesh_diamonds_add,
    VIEW3D_MT_mesh_math_add,
    VIEW3D_MT_mesh_mech,
    VIEW3D_MT_mesh_extras_add,
    VIEW3D_MT_mesh_torus_add,
    VIEW3D_MT_mesh_pipe_joints_add,
    add_mesh_star.AddStar,
    add_mesh_twisted_torus.AddTwistedTorus,
    add_mesh_gemstones.AddDiamond,
    add_mesh_gemstones.AddGem,
    add_mesh_gears.AddGear,
    add_mesh_gears.AddWormGear,
    add_mesh_3d_function_surface.AddZFunctionSurface,
    add_mesh_3d_function_surface.AddXYZFunctionSurface,
    add_mesh_round_cube.AddRoundCube,
    add_mesh_supertoroid.add_supertoroid,
    add_mesh_pyramid.AddPyramid,
    add_mesh_torusknot.AddTorusKnot,
    add_mesh_honeycomb.add_mesh_honeycomb,
    add_mesh_teapot.AddTeapot,
    add_mesh_pipe_joint.AddElbowJoint,
    add_mesh_pipe_joint.AddTeeJoint,
    add_mesh_pipe_joint.AddWyeJoint,
    add_mesh_pipe_joint.AddCrossJoint,
    add_mesh_pipe_joint.AddNJoint,
    add_mesh_solid.Solids,
    add_mesh_round_brilliant.MESH_OT_primitive_brilliant_add,
    add_mesh_menger_sponge.AddMengerSponge,
    add_mesh_vertex.AddVert,
    add_mesh_vertex.AddEmptyVert,
    add_mesh_vertex.AddSymmetricalEmpty,
    add_mesh_vertex.AddSymmetricalVert,
    add_empty_as_parent.P2E,
    add_empty_as_parent.PreFix,
    mesh_discombobulator.discombobulator,
    mesh_discombobulator.discombobulator_dodads_list,
    mesh_discombobulator.discombob_help,
    mesh_discombobulator.VIEW3D_OT_tools_discombobulate,
    mesh_discombobulator.chooseDoodad,
    mesh_discombobulator.unchooseDoodad,
    add_mesh_beam_builder.addBeam,
    Wallfactory.add_mesh_wallb,
    add_mesh_triangles.MakeTriangle
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    # Add "Extras" menu to the "Add Mesh" menu
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu.
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

if __name__ == "__main__":
    register()
