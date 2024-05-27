# SPDX-FileCopyrightText: 2010 Mariano Hidalgo
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Scene Information",
    "author": "uselessdreamer",
    "version": (0, 3, 1),
    "blender": (2, 80, 0),
    "location": "Properties > Scene > Blend Info Panel",
    "description": "Show information about the .blend",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/system/blend_info.html",
    "category": "System",
}

import bpy


def quantity_string(quantity, text_single, text_plural, text_none=None):
    sep = " "

    if not text_none:
        text_none = text_plural

    if quantity == 0:
        string = str(quantity) + sep + text_none

    if quantity == 1:
        string = str(quantity) + sep + text_single

    if quantity >= 2:
        string = str(quantity) + sep + text_plural

    if quantity < 0:
        return None

    return string


class OBJECT_PT_blendinfo(bpy.types.Panel):
    bl_label = "Blend Info"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ob_cols = []
        db_cols = []

        objects = bpy.data.objects

        layout = self.layout

        # OBJECTS

        l_row = layout.row()
        num = len(bpy.data.objects)
        l_row.label(text=quantity_string(num, "Object", "Objects")
            + " in the scene:",
            icon='OBJECT_DATA')

        l_row = layout.row()
        ob_cols.append(l_row.column())
        ob_cols.append(l_row.column())

        row = ob_cols[0].row()
        meshes = [o for o in objects.values() if o.type == 'MESH']
        num = len(meshes)
        row.label(text=quantity_string(num, "Mesh", "Meshes"),
            icon='MESH_DATA')

        row = ob_cols[1].row()
        curves = [o for o in objects.values() if o.type == 'CURVE']
        num = len(curves)
        row.label(text=quantity_string(num, "Curve", "Curves"),
            icon='CURVE_DATA')

        row = ob_cols[0].row()
        cameras = [o for o in objects.values() if o.type == 'CAMERA']
        num = len(cameras)
        row.label(text=quantity_string(num, "Camera", "Cameras"),
            icon='CAMERA_DATA')

        row = ob_cols[1].row()
        lamps = [o for o in objects.values() if o.type == 'LIGHT']
        num = len(lamps)
        row.label(text=quantity_string(num, "Lamp", "Lamps"),
            icon='LIGHT_DATA')

        row = ob_cols[0].row()
        armatures = [o for o in objects.values() if o.type == 'ARMATURE']
        num = len(armatures)
        row.label(text=quantity_string(num, "Armature", "Armatures"),
            icon='ARMATURE_DATA')

        row = ob_cols[1].row()
        lattices = [o for o in objects.values() if o.type == 'LATTICE']
        num = len(lattices)
        row.label(text=quantity_string(num, "Lattice", "Lattices"),
            icon='LATTICE_DATA')

        row = ob_cols[0].row()
        empties = [o for o in objects.values() if o.type == 'EMPTY']
        num = len(empties)
        row.label(text=quantity_string(num, "Empty", "Empties"),
            icon='EMPTY_DATA')

        row = ob_cols[1].row()
        empties = [o for o in objects.values() if o.type == 'SPEAKER']
        num = len(empties)
        row.label(text=quantity_string(num, "Speaker", "Speakers"),
            icon='OUTLINER_OB_SPEAKER')

        layout.separator()

        # DATABLOCKS

        l_row = layout.row()
        num = len(bpy.data.objects)
        l_row.label(text="Datablocks in the scene:")

        l_row = layout.row()
        db_cols.append(l_row.column())
        db_cols.append(l_row.column())

        row = db_cols[0].row()
        num = len(bpy.data.meshes)
        row.label(text=quantity_string(num, "Mesh", "Meshes"),
            icon='MESH_DATA')

        row = db_cols[1].row()
        num = len(bpy.data.curves)
        row.label(text=quantity_string(num, "Curve", "Curves"),
            icon='CURVE_DATA')

        row = db_cols[0].row()
        num = len(bpy.data.cameras)
        row.label(text=quantity_string(num, "Camera", "Cameras"),
            icon='CAMERA_DATA')

        row = db_cols[1].row()
        num = len(bpy.data.lights)
        row.label(text=quantity_string(num, "Lamp", "Lamps"),
            icon='LIGHT_DATA')

        row = db_cols[0].row()
        num = len(bpy.data.armatures)
        row.label(text=quantity_string(num, "Armature", "Armatures"),
            icon='ARMATURE_DATA')

        row = db_cols[1].row()
        num = len(bpy.data.lattices)
        row.label(text=quantity_string(num, "Lattice", "Lattices"),
            icon='LATTICE_DATA')

        row = db_cols[0].row()
        num = len(bpy.data.materials)
        row.label(text=quantity_string(num, "Material", "Materials"),
            icon='MATERIAL_DATA')

        row = db_cols[1].row()
        num = len(bpy.data.worlds)
        row.label(text=quantity_string(num, "World", "Worlds"),
            icon='WORLD_DATA')

        row = db_cols[0].row()
        num = len(bpy.data.textures)
        row.label(text=quantity_string(num, "Texture", "Textures"),
            icon='TEXTURE_DATA')

        row = db_cols[1].row()
        num = len(bpy.data.images)
        row.label(text=quantity_string(num, "Image", "Images"),
            icon='IMAGE_DATA')

        row = db_cols[0].row()
        num = len(bpy.data.texts)
        row.label(text=quantity_string(num, "Text", "Texts"),
            icon='TEXT')

# Register
classes = [
    OBJECT_PT_blendinfo
]

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)


if __name__ == "__main__":
    register()
