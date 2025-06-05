# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from io_mesh_atomic.xyz_import import ELEMENTS_DEFAULT


class AtomsExport(object):
    __slots__ = ('element', 'location')
    def __init__(self, element, location):
        self.element  = element
        self.location = location


def export_xyz(obj_type, filepath_xyz):

    list_atoms = []
    counter = 0
    for obj in bpy.context.selected_objects:

        if "STICK" in obj.name.upper():
            continue

        if obj.type not in {'MESH', 'SURFACE', 'META'}:
            continue

        name = ""
        for element in ELEMENTS_DEFAULT:
            if element[1] in obj.name:
                if element[2] == "Vac":
                    name = "X"
                else:
                    name = element[2]

        if name == "":
            if obj_type == "0":
                name = "?"
            else:
                continue

        if len(obj.children) != 0:
            for vertex in obj.data.vertices:
                location = obj.matrix_world @ vertex.co
                list_atoms.append(AtomsExport(name, location))
                counter += 1
        else:
            if not obj.parent:
                location = obj.location
                list_atoms.append(AtomsExport(name, location))
                counter += 1

    xyz_file_p = open(filepath_xyz, "w")
    xyz_file_p.write("%d\n" % counter)
    xyz_file_p.write("This XYZ file has been created with Blender "
                     "and the addon Atomic Blender - XYZ. "
                     "For more details see the wiki pages of Blender.\n")

    for i, atom in enumerate(list_atoms):
        string = "%3s%15.5f%15.5f%15.5f\n" % (
                                      atom.element,
                                      atom.location[0],
                                      atom.location[1],
                                      atom.location[2])
        xyz_file_p.write(string)

    xyz_file_p.close()

    return True
