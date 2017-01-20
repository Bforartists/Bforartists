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

def console_namespace():
    import console_python
    get_consoles = console_python.get_console
    consoles = getattr(get_consoles, "consoles", None)
    if consoles:
        for console, stdout, stderr in get_consoles.consoles.values():
            return console.locals
    return {}


def console_math_data():
    from mathutils import Matrix, Vector, Quaternion, Euler

    data_matrix = {}
    data_quat = {}
    data_euler = {}
    data_vector = {}
    data_vector_array = {}

    for key, var in console_namespace().items():
        if key[0] == "_":
            continue

        var_type = type(var)

        if var_type is Matrix:
            if len(var.col) != 4 or len(var.row) != 4:
                if len(var.col) == len(var.row):
                    var = var.to_4x4() 
                else:  # todo, support 4x3 matrix
                    continue
            data_matrix[key] = var
        elif var_type is Vector:
            if len(var) < 3:
                var = var.to_3d()
            data_vector[key] = var
        elif var_type is Quaternion:
            data_quat[key] = var
        elif var_type is Euler:
            data_euler[key] = var
        elif var_type in {list, tuple}:
            if var:
                ok = True
                for item in var:
                    if type(item) is not Vector:
                        ok = False
                        break
                if ok:
                    data_vector_array[key] = var

    return data_matrix, data_quat, data_euler, data_vector, data_vector_array
