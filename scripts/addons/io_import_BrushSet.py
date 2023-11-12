# SPDX-FileCopyrightText: 2020-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import os
from bpy.props import (
    StringProperty,
)

bl_info = {
    "name": "Import BrushSet",
    "author": "Daniel Grauer (kromar), CansecoGPC",
    "version": (1, 3, 1),
    "blender": (2, 80, 0),
    "location": "File > Import > BrushSet",
    "description": "Imports all image files from a folder.",
    "warning": '',    # used for warning icon and text in addons panel
    "doc_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Import-Export/BrushSet",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export",
}

fakeUser = False


def load_brush_set(dirpath):
    extensions = tuple(bpy.path.extensions_image)
    for file in os.listdir(dirpath):
        if not file.lower().endswith(extensions):
            continue

        # Load the image into data.
        path = os.path.join(dirpath, file)
        try:
            image = bpy.data.images.load(path)
        except BaseException as ex:
            print("Failed to load %r, error: %r" % (file, ex))
            continue

        image.use_fake_user = fakeUser

        # Create new texture.
        # NOTE: use the image name instead of `file` in case
        # it's encoding isn't `utf-8` compatible.
        texture = bpy.data.textures.new(image.name, 'IMAGE')
        texture.use_fake_user = fakeUser

        # Assign the image to the texture.
        texture.image = image

        print("imported:", repr(file))

    print("Brush Set imported!")

# -----------------------------------------------------------------------------


class BrushSetImporter(bpy.types.Operator):
    '''Load Brush Set'''
    bl_idname = "import_image.brushset"
    bl_label = "Import BrushSet"


    # creating a temporary filter to avoid overriding the users filters
    temp_filters: bool = True
    def draw(self, context):
        if self.temp_filters:
            context.space_data.params.use_filter = True
            context.space_data.params.use_filter_folder = True
            context.space_data.params.use_filter_image = True
            self.temp_filters = False

    directory: StringProperty(
        name="Directory",
        description="Directory",
        maxlen=1024,
        subtype='DIR_PATH',
    )

    def execute(self, context):
        load_brush_set(self.directory)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

# -----------------------------------------------------------------------------


def menu_func(self, context):
    self.layout.operator(BrushSetImporter.bl_idname, text="Brush Set")


# -----------------------------------------------------------------------------
# GUI

'''
class Brush_set_UI(bpy.types.Panel):

    bl_space_type ='USER_PREFERENCES'
    bl_label = 'Brush_Path'
    bl_region_type = 'WINDOW'
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):

        scn = context.scene
        layout = self.layout
        column = layout.column(align=True)
        column.label(text='Brush Directory:')
        column.prop(scn,'filepath')
'''

# -----------------------------------------------------------------------------

classes = (
    BrushSetImporter,
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func)


def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
