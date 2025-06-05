# SPDX-FileCopyrightText: 2019-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from io_mesh_atomic.pdb_import import ELEMENTS_DEFAULT

class AtomPropExport(object):
    __slots__ = ('element', 'location')
    def __init__(self, element, location):
        self.element  = element
        self.location = location


def export_pdb(obj_type, filepath_pdb):

    list_atoms = []
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
                list_atoms.append(AtomPropExport(name, location))
        else:
            if not obj.parent:
                location = obj.location
                list_atoms.append(AtomPropExport(name, location))

    pdb_file_p = open(filepath_pdb, "w")
    pdb_file_p.write("REMARK This pdb file has been created with Blender "
                     "and the addon Atomic Blender - PDB\n"
                     "REMARK For more details see the wiki pages of Blender.\n"
                     "REMARK\n"
                     "REMARK\n")

    for i, atom in enumerate(list_atoms):
        string = "ATOM %6d%3s%24.3f%8.3f%8.3f%6.2f%6.2f%12s\n" % (
                                      i, atom.element,
                                      atom.location[0],
                                      atom.location[1],
                                      atom.location[2],
                                      1.00, 1.00, atom.element)
        pdb_file_p.write(string)

    pdb_file_p.close()

    return True
