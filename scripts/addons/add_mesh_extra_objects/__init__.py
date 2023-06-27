# SPDX-FileCopyrightText: 2011-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Contributed to by:
# Pontiac, Fourmadmen, varkenvarken, tuga3d, meta-androcto, metalliandy     #
# dreampainter, cotejrp1, liero, Kayo Phoenix, sugiany, dommetysk, Jambay   #
# Phymec, Anthony D'Agostino, Pablo Vazquez, Richard Wilks, lijenstina,     #
# Sjaak-de-Draak, Phil Cote, cotejrp1, xyz presets by elfnor, revolt_randy, #
# Vladimir Spivak (cwolf3d), #


bl_info = {
    "name": "Extra Objects",
    "author": "Multiple Authors",
    "version": (0, 3, 9),
    "blender": (2, 80, 0),
    "location": "View3D > Add > Mesh",
    "description": "Add extra mesh object types",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/add_mesh/mesh_extra_objects.html",
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
    from . import add_mesh_beam_builder
    from . import Blocks
    from . import Wallfactory
    from . import add_mesh_triangles

    from .add_mesh_rocks import __init__
    from .add_mesh_rocks import rockgen

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
        oper = layout.operator("mesh.primitive_gear", text="Gear")
        oper.change = False
        oper = layout.operator("mesh.primitive_worm_gear", text="Worm")
        oper.change = False


class VIEW3D_MT_mesh_diamonds_add(Menu):
    # Define the "Diamonds" menu
    bl_idname = "VIEW3D_MT_mesh_diamonds_add"
    bl_label = "Diamonds"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        oper = layout.operator("mesh.primitive_brilliant_add", text="Brilliant Diamond")
        oper.change = False
        oper = layout.operator("mesh.primitive_diamond_add", text="Diamond")
        oper.change = False
        oper = layout.operator("mesh.primitive_gem_add", text="Gem")
        oper.change = False


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
        self.layout.operator("mesh.make_triangle")


class VIEW3D_MT_mesh_extras_add(Menu):
    # Define the "Extra Objects" menu
    bl_idname = "VIEW3D_MT_mesh_extras_add"
    bl_label = "Extras"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        oper = layout.operator("mesh.add_beam", text="Beam Builder")
        oper.change = False
        oper = layout.operator("mesh.wall_add", text="Wall Factory")
        oper.change = False
        layout.separator()
        oper = layout.operator("mesh.primitive_star_add", text="Simple Star")
        oper.change = False
        oper = layout.operator("mesh.primitive_steppyramid_add", text="Step Pyramid")
        oper.change = False
        oper = layout.operator("mesh.honeycomb_add", text="Honeycomb")
        oper.change = False
        oper = layout.operator("mesh.primitive_teapot_add", text="Teapot+")
        oper = layout.operator("mesh.menger_sponge_add", text="Menger Sponge")


class VIEW3D_MT_mesh_torus_add(Menu):
    # Define the "Torus Objects" menu
    bl_idname = "VIEW3D_MT_mesh_torus_add"
    bl_label = "Torus Objects"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        oper = layout.operator("mesh.primitive_twisted_torus_add", text="Twisted Torus")
        oper.change = False
        oper = layout.operator("mesh.primitive_supertoroid_add", text="Supertoroid")
        oper.change = False
        oper = layout.operator("mesh.primitive_torusknot_add", text="Torus Knot")
        oper.change = False


class VIEW3D_MT_mesh_pipe_joints_add(Menu):
    # Define the "Pipe Joints" menu
    bl_idname = "VIEW3D_MT_mesh_pipe_joints_add"
    bl_label = "Pipe Joints"

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_REGION_WIN'
        oper = layout.operator("mesh.primitive_elbow_joint_add", text="Pipe Elbow")
        oper.change = False
        oper = layout.operator("mesh.primitive_tee_joint_add", text="Pipe T-Joint")
        oper.change = False
        oper = layout.operator("mesh.primitive_wye_joint_add", text="Pipe Y-Joint")
        oper.change = False
        oper = layout.operator("mesh.primitive_cross_joint_add", text="Pipe Cross-Joint")
        oper.change = False
        oper = layout.operator("mesh.primitive_n_joint_add", text="Pipe N-Joint")
        oper.change = False

# Register all operators and panels

# Define "Extras" menu
def menu_func(self, context):
    layout = self.layout
    layout.operator_context = 'INVOKE_REGION_WIN'

    layout.separator()
    layout.menu("VIEW3D_MT_mesh_vert_add",
                text="Single Vert", icon="DECORATE")
    oper = layout.operator("mesh.primitive_round_cube_add",
                    text="Round Cube", icon="SPHERE")
    oper.change = False
    layout.menu("VIEW3D_MT_mesh_torus_add",
                text="Torus Objects", icon="MESH_TORUS")
    layout.separator()
    layout.menu("VIEW3D_MT_mesh_math_add",
                text="Math Function", icon="PACKAGE")
    layout.menu("VIEW3D_MT_mesh_gears_add",
                text="Gears", icon="PREFERENCES")
    layout.menu("VIEW3D_MT_mesh_pipe_joints_add",
                text="Pipe Joints", icon="EMPTY_DATA")
    layout.separator()
    layout.menu("VIEW3D_MT_mesh_diamonds_add", text="Diamonds")
    layout.menu("VIEW3D_MT_mesh_extras_add",
                text="Extras")
    layout.separator()
    layout.operator("object.parent_to_empty",
                    text="Parent To Empty")

def Extras_contex_menu(self, context):
    bl_label = 'Change'

    obj = context.object
    layout = self.layout

    if obj == None or obj.data is None:
        return

    if 'Gear' in obj.data.keys():
        props = layout.operator("mesh.primitive_gear", text="Change Gear")
        props.change = True
        for prm in add_mesh_gears.GearParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'WormGear' in obj.data.keys():
        props = layout.operator("mesh.primitive_worm_gear", text="Change WormGear")
        props.change = True
        for prm in add_mesh_gears.WormGearParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Beam' in obj.data.keys():
        props = layout.operator("mesh.add_beam", text="Change Beam")
        props.change = True
        for prm in add_mesh_beam_builder.BeamParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Wall' in obj.data.keys():
        props = layout.operator("mesh.wall_add", text="Change Wall")
        props.change = True
        for prm in Wallfactory.WallParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'ElbowJoint' in obj.data.keys():
        props = layout.operator("mesh.primitive_elbow_joint_add", text="Change ElbowJoint")
        props.change = True
        for prm in add_mesh_pipe_joint.ElbowJointParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'TeeJoint' in obj.data.keys():
        props = layout.operator("mesh.primitive_tee_joint_add", text="Change TeeJoint")
        props.change = True
        for prm in add_mesh_pipe_joint.TeeJointParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'WyeJoint' in obj.data.keys():
        props = layout.operator("mesh.primitive_wye_joint_add", text="Change WyeJoint")
        props.change = True
        for prm in add_mesh_pipe_joint.WyeJointParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'CrossJoint' in obj.data.keys():
        props = layout.operator("mesh.primitive_cross_joint_add", text="Change CrossJoint")
        props.change = True
        for prm in add_mesh_pipe_joint.CrossJointParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'NJoint' in obj.data.keys():
        props = layout.operator("mesh.primitive_n_joint_add", text="Change NJoint")
        props.change = True
        for prm in add_mesh_pipe_joint.NJointParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Diamond' in obj.data.keys():
        props = layout.operator("mesh.primitive_diamond_add", text="Change Diamond")
        props.change = True
        for prm in add_mesh_gemstones.DiamondParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Gem' in obj.data.keys():
        props = layout.operator("mesh.primitive_gem_add", text="Change Gem")
        props.change = True
        for prm in add_mesh_gemstones.GemParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Brilliant' in obj.data.keys():
        props = layout.operator("mesh.primitive_brilliant_add", text="Change Brilliant")
        props.change = True
        for prm in add_mesh_round_brilliant.BrilliantParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Roundcube' in obj.data.keys():
        props = layout.operator("mesh.primitive_round_cube_add", text="Change Roundcube")
        props.change = True
        for prm in add_mesh_round_cube.RoundCubeParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'TorusKnot' in obj.data.keys():
        props = layout.operator("mesh.primitive_torusknot_add", text="Change TorusKnot")
        props.change = True
        for prm in add_mesh_torusknot.TorusKnotParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'SuperToroid' in obj.data.keys():
        props = layout.operator("mesh.primitive_supertoroid_add", text="Change SuperToroid")
        props.change = True
        for prm in add_mesh_supertoroid.SuperToroidParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'TwistedTorus' in obj.data.keys():
        props = layout.operator("mesh.primitive_twisted_torus_add", text="Change TwistedTorus")
        props.change = True
        for prm in add_mesh_twisted_torus.TwistedTorusParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Star' in obj.data.keys():
        props = layout.operator("mesh.primitive_star_add", text="Change Star")
        props.change = True
        for prm in add_mesh_star.StarParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'Pyramid' in obj.data.keys():
        props = layout.operator("mesh.primitive_steppyramid_add", text="Change Pyramid")
        props.change = True
        for prm in add_mesh_pyramid.PyramidParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

    if 'HoneyComb' in obj.data.keys():
        props = layout.operator("mesh.honeycomb_add", text="Change HoneyComb")
        props.change = True
        for prm in add_mesh_honeycomb.HoneyCombParameters():
            setattr(props, prm, obj.data[prm])
        layout.separator()

# Register
classes = [
    VIEW3D_MT_mesh_vert_add,
    VIEW3D_MT_mesh_gears_add,
    VIEW3D_MT_mesh_diamonds_add,
    VIEW3D_MT_mesh_math_add,
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
    add_mesh_beam_builder.addBeam,
    Wallfactory.add_mesh_wallb,
    add_mesh_triangles.MakeTriangle,
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

    add_mesh_rocks.register()

    # Add "Extras" menu to the "Add Mesh" menu and context menu.
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(Extras_contex_menu)


def unregister():
    # Remove "Extras" menu from the "Add Mesh" menu and context menu.
    bpy.types.VIEW3D_MT_object_context_menu.remove(Extras_contex_menu)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)

    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)

    add_mesh_rocks.unregister()

if __name__ == "__main__":
    register()
