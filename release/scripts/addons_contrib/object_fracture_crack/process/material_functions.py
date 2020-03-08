# gpl: author Nobuyuki Hirakata

import bpy
import os


# Allow changing the original material names from the .blend file
# by replacing them with the UI Names from the EnumProperty
def get_ui_mat_name(mat_name):
    mat_ui_name = "CrackIt Material"
    try:
        # access the Scene type directly to get the name from the enum
        mat_items = bpy.types.Scene.crackit[1]["type"].bl_rna.material_preset[1]["items"]
        for mat_id, mat_list in enumerate(mat_items):
            if mat_name in mat_list:
                mat_ui_name = mat_items[mat_id][1]
                break
        del mat_items
    except Exception as e:
        error_handlers(
                False, "get_ui_mat_name", e,
                "Retrieving the EnumProperty key UI Name could not be completed", True
                )
        pass

    return mat_ui_name


# error_type='ERROR' for popup massage
def error_handlers(self, op_name, error, reports="ERROR", func=False, error_type='WARNING'):
    if self and reports:
        self.report({error_type}, reports + " (See Console for more info)")

    is_func = "Function" if func else "Operator"
    print("\n[Cell Fracture Crack It]\n{}: {}\nError: "
          "{}\nReport: {}\n".format(is_func, op_name, error, reports))


def appendMaterial(mat_lib_name, mat_name, mat_ui_names="Nameless Material"):
    file_path = _makeFilePath(os.path.dirname(__file__))
    bpy.ops.wm.append(filename=mat_name, directory=file_path)

    # If material is loaded some times, select the last-loaded material
    last_material = _getAppendedMaterial(mat_name)

    if last_material:
        mat = bpy.data.materials[last_material]
        # skip renaming if the prop is True
        if not mat_lib_name:
            mat.name = mat_ui_names

        # Apply Only one material in the material slot
        for m in bpy.context.object.data.materials:
            bpy.ops.object.material_slot_remove()

        bpy.context.object.data.materials.append(mat)

        return True

    return False


# Make file path of addon
def _makeFilePath(addon_path):
    material_folder = "/materials"
    blend_file = "/materials1.blend"
    category = "\\Material\\"

    file_path = addon_path + material_folder + blend_file + category
    return file_path


# Get last-loaded material, such as ~.002
def _getAppendedMaterial(material_name):
    # Get material name list
    material_names = [m.name for m in bpy.data.materials if material_name in m.name]
    if material_names:
        # Return last material in the sorted order
        material_names.sort()

        return material_names[-1]

    return None
