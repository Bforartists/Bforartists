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

#
#  Main author       : Clemens Barth (Blendphys@root-1.de)
#  Authors           : Clemens Barth, Christine Mottet (Icosahedra), ...
#
#  Homepage(Wiki)    : http://development.root-1.de/Atomic_Blender.php
#
#  Start of project              : 2012-03-25 by Clemens Barth
#  First publication in Blender  : 2012-05-27 by Clemens Barth
#  Last modified                 : 2019-03-19
#
#
#
#  To do:
#  ======
#
#  1. Include other shapes: dodecahedron, ...
#  2. Skin option for parabolic shaped clusters
#  3. Skin option for icosahedron
#  4. Icosahedron: unlimited size ...
#

bl_info = {
    "name": "Atomic Blender - Cluster",
    "description": "Creating nanoparticles/clusters formed by atoms",
    "author": "Clemens Barth",
    "version": (0, 5),
    "blender": (2, 80, 0),
    "location": "Panel: View 3D - Tools (right side)",
    "warning": "",
    "wiki_url": "... will be updated asap ...",
    "category": "Add Mesh"}

import os
import io
import bpy
from bpy.types import Operator, Panel
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import (StringProperty,
                       BoolProperty,
                       EnumProperty,
                       IntProperty,
                       FloatProperty)

from . import add_mesh_cluster

ATOM_Cluster_PANEL = 0

# -----------------------------------------------------------------------------
#                                                                           GUI


class CLASS_ImportCluster(bpy.types.Operator):
    bl_idname = "mesh.cluster"
    bl_label = "Atom cluster"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    def execute(self, context):

        global ATOM_Cluster_PANEL
        ATOM_Cluster_PANEL = 1

        return {'FINISHED'}


class CLASS_PT_atom_cluster_panel(Panel):
    bl_label       = "Atomic Blender - Cluster"
    bl_space_type  = "VIEW_3D"
    bl_region_type = "UI"


    @classmethod
    def poll(self, context):
        global ATOM_Cluster_PANEL

        if ATOM_Cluster_PANEL == 0:
            return False

        return True

    def draw(self, context):
        layout = self.layout

        scn = context.scene.atom_cluster

        row = layout.row()
        row.label(text="Cluster properties")
        box = layout.box()
        row = box.row()
        row.prop(scn, "shape")

        if scn.shape in ["parabolid_square","parabolid_ab","parabolid_abc"]:
            row = box.row()
            row.prop(scn, "parabol_diameter")
            row = box.row()
            row.prop(scn, "parabol_height")
        elif scn.shape in ["icosahedron"]:
            row = box.row()
            row.prop(scn, "icosahedron_size")
        else:
            row = box.row()
            row.prop(scn, "size")
            row = box.row()
            row.prop(scn, "skin")

        row = box.row()
        row.prop(scn, "lattice_parameter")
        row = box.row()
        row.prop(scn, "element")
        row = box.row()
        row.prop(scn, "radius_type")
        row = box.row()
        row.prop(scn, "scale_radius")
        row = box.row()
        row.prop(scn, "scale_distances")

        row = layout.row()
        row.label(text="Load cluster")
        box = layout.box()
        row = box.row()
        row.operator("atom_cluster.load")
        row = box.row()
        row.label(text="Number of atoms")
        row = box.row()
        row.prop(scn, "atom_number_total")
        row = box.row()
        row.prop(scn, "atom_number_drawn")


# The properties (gadgets) in the panel. They all go to scene
# during initialization (see end)
class CLASS_atom_cluster_Properties(bpy.types.PropertyGroup):

    def Callback_radius_type(self, context):
        scn = bpy.context.scene.atom_cluster
        DEF_atom_cluster_radius_type(scn.radius_type,
                                     scn.radius_how,)

    size: FloatProperty(
        name = "Size", default=30.0, min=0.1,
        description = "Size of cluster in Angstroem")
    skin: FloatProperty(
        name = "Skin", default=1.0, min=0.0, max = 1.0,
        description = "Skin of cluster in % of size (skin=1.0: show all atoms, skin=0.1: show only the outer atoms)")
    parabol_diameter: FloatProperty(
        name = "Diameter", default=30.0, min=0.1,
        description = "Top diameter in Angstroem")
    parabol_height: FloatProperty(
        name = "Height", default=30.0, min=0.1,
        description = "Height in Angstroem")
    icosahedron_size: IntProperty(
        name = "Size", default=1, min=1, max=13,
        description = "Size n: 1 (13 atoms), 2 (55 atoms), 3 (147 atoms), 4 (309 atoms), 5 (561 atoms), ..., 13 (8217 atoms)")
    shape: EnumProperty(
        name="",
        description="Choose the shape of the cluster",
        items=(('sphere_square',  "Sphere - square",   "Sphere with square lattice"),
               ('sphere_hex_ab',  "Sphere - hex ab",  "Sphere with hexagonal ab-lattice"),
               ('sphere_hex_abc', "Sphere - hex abc", "Sphere with hexagonal abc-lattice"),
               ('pyramide_square',  "Pyramide - Square",    "Pyramide: square (abc-lattice)"),
               ('pyramide_hex_abc', "Pyramide - Tetraeder", "Pyramide: tetraeder (abcabc-lattice)"),
               ('octahedron',           "Octahedron",           "Octahedron"),
               ('truncated_octahedron', "Truncated octahedron", "Truncated octahedron"),
               ('icosahedron', "Icosahedron", "Icosahedron"),
               ('parabolid_square', "Paraboloid: square",  "Paraboloid with square lattice"),
               ('parabolid_ab',     "Paraboloid: hex ab",  "Paraboloid with ab-lattice"),
               ('parabolid_abc',    "Paraboloid: hex abc", "Paraboloid with abc-lattice")),
               default='sphere_square',)
    lattice_parameter: FloatProperty(
        name = "Lattice", default=4.08, min=1.0,
        description = "Lattice parameter in Angstroem")
    element: StringProperty(name="Element",
        default="Gold", description = "Enter the name of the element")
    radius_type: EnumProperty(
        name="Radius",
        description="Which type of atom radii?",
        items=(('0',"predefined", "Use pre-defined radii"),
               ('1',"atomic", "Use atomic radii"),
               ('2',"van der Waals","Use van der Waals radii")),
               default='0',)
    scale_radius: FloatProperty(
        name = "Scale R", default=1.0, min=0.0,
        description = "Scale radius of atoms")
    scale_distances: FloatProperty(
        name = "Scale d", default=1.0, min=0.0,
        description = "Scale distances")

    atom_number_total: StringProperty(name="Total",
        default="---", description = "Number of all atoms in the cluster")
    atom_number_drawn: StringProperty(name="Drawn",
        default="---", description = "Number of drawn atoms in the cluster")


# The button for reloading the atoms and creating the scene
class CLASS_atom_cluster_load_button(Operator):
    bl_idname = "atom_cluster.load"
    bl_label = "Load"
    bl_description = "Load the cluster"

    def execute(self, context):
        scn    = context.scene.atom_cluster

        add_mesh_cluster.DEF_atom_read_atom_data()
        del add_mesh_cluster.ATOM_CLUSTER_ALL_ATOMS[:]

        if scn.shape in ["parabolid_ab", "parabolid_abc", "parabolid_square"]:
            parameter1 = scn.parabol_height
            parameter2 = scn.parabol_diameter
        elif scn.shape == "pyramide_hex_abc":
            parameter1 = scn.size * 1.6
            parameter2 = scn.skin
        elif scn.shape == "pyramide_square":
            parameter1 = scn.size * 1.4
            parameter2 = scn.skin
        elif scn.shape in ["octahedron", "truncated_octahedron"]:
            parameter1 = scn.size * 1.4
            parameter2 = scn.skin
        elif scn.shape in ["icosahedron"]:
            parameter1 = scn.icosahedron_size
        else:
            parameter1 = scn.size
            parameter2 = scn.skin

        if scn.shape in ["octahedron", "truncated_octahedron", "sphere_square", "pyramide_square", "parabolid_square"]:
            numbers = add_mesh_cluster.create_square_lattice(
                                scn.shape,
                                parameter1,
                                parameter2,
                                (scn.lattice_parameter/2.0))

        if scn.shape in ["sphere_hex_ab", "parabolid_ab"]:
            numbers = add_mesh_cluster.create_hexagonal_abab_lattice(
                                scn.shape,
                                parameter1,
                                parameter2,
                                scn.lattice_parameter)

        if scn.shape in ["sphere_hex_abc", "pyramide_hex_abc", "parabolid_abc"]:
            numbers = add_mesh_cluster.create_hexagonal_abcabc_lattice(
                                scn.shape,
                                parameter1,
                                parameter2,
                                scn.lattice_parameter)

        if scn.shape in ["icosahedron"]:
            numbers = add_mesh_cluster.create_icosahedron(
                                parameter1,
                                scn.lattice_parameter)

        DEF_atom_draw_atoms(scn.element,
                            scn.radius_type,
                            scn.scale_radius,
                            scn.scale_distances,
                            scn.shape)

        scn.atom_number_total = str(numbers[0])
        scn.atom_number_drawn = str(numbers[1])

        return {'FINISHED'}


def DEF_atom_draw_atoms(prop_element,
                        prop_radius_type,
                        prop_scale_radius,
                        prop_scale_distances,
                        coll_name):

    FLAG = False
    # Get the details about the atom (Name, radius, color, etc.).
    for element in add_mesh_cluster.ATOM_CLUSTER_ELEMENTS:
        if prop_element in element.name:
            number = element.number
            name = element.name
            color = element.color
            radii = element.radii
            FLAG = True
            break

    # If no element could be found, use gold. This may happen if the user does
    # not correctly wrote the name of the atom.
    if not FLAG:
        number = 79
        name = "Gold"
        color = (1.0,  0.81,  0.13, 1.0)
        radii = [1.34]

    # First, we create a collection for the atoms, which includes the 
    # representative ball and the mesh.
    coll_atom_name = "Cluster (" + coll_name + ")_" + name.lower()
    # Create the new collection and ...
    coll_atom = bpy.data.collections.new(coll_atom_name)
    # ... link it to the collection, which contains all parts of the 
    # element (ball and mesh).
    bpy.data.collections.new(coll_atom_name)
    bpy.context.scene.collection.children.link(coll_atom)

    # Create the material.
    material = bpy.data.materials.new(name)
    material.name = name
    material.diffuse_color = color

    atom_vertices = []
    for atom in add_mesh_cluster.ATOM_CLUSTER_ALL_ATOMS:
        atom_vertices.append( atom.location * prop_scale_distances )

    # Build the mesh
    atom_mesh = bpy.data.meshes.new("Mesh_"+name)
    atom_mesh.from_pydata(atom_vertices, [], [])
    atom_mesh.update()
    new_atom_mesh = bpy.data.objects.new(name+ "_mesh", atom_mesh)

    # Link active object to the new collection
    coll_atom.objects.link(new_atom_mesh)

    bpy.ops.surface.primitive_nurbs_surface_sphere_add(
                            view_align=False, enter_editmode=False,
                            location=(0,0,0), rotation=(0.0, 0.0, 0.0))

    ball = bpy.context.view_layer.objects.active
    ball.name = name + "_ball"
    # Hide this ball because its appearance has no meaning. It is just the
    # representative ball. The ball is visible at the vertices of the mesh.
    # Rememmber, this is a dupliverts construct!
    ball.hide_set(True)

    # Scale the radius.
    ball.scale  = (radii[int(prop_radius_type)]*prop_scale_radius,) * 3

    ball.active_material = material
    ball.parent = new_atom_mesh
    new_atom_mesh.instance_type = 'VERTS'

    # Note the collection where the ball was placed into.
    coll_all = ball.users_collection
    if len(coll_all) > 0:
        coll_past = coll_all[0]
    else:
        coll_past = bpy.context.scene.collection
    
    # Put the atom into the new collection 'atom' and ...
    coll_atom.objects.link(ball)
    # ... unlink the atom from the other collection.
    coll_past.objects.unlink(ball)

    # ------------------------------------------------------------------------
    # SELECT ALL LOADED OBJECTS
    bpy.ops.object.select_all(action='DESELECT')
    new_atom_mesh.select_set(True)
    bpy.context.view_layer.objects.active = new_atom_mesh

    return True


# The entry into the menu 'file -> import'
def DEF_menu_func(self, context):
    self.layout.operator(CLASS_ImportCluster.bl_idname, icon='PLUGIN')


classes = (CLASS_ImportCluster, 
           CLASS_PT_atom_cluster_panel, 
           CLASS_atom_cluster_Properties, 
           CLASS_atom_cluster_load_button)


def register():
    from bpy.utils import register_class    
    for cls in classes:
        register_class(cls)
        
    bpy.types.Scene.atom_cluster = bpy.props.PointerProperty(type=
                                                  CLASS_atom_cluster_Properties)
    bpy.types.VIEW3D_MT_mesh_add.append(DEF_menu_func)
    

def unregister():
    from bpy.utils import register_class
    for cls in classes:
        unregister_class(cls)
        
    bpy.types.VIEW3D_MT_mesh_add.remove(DEF_menu_func)


if __name__ == "__main__":

    register()
