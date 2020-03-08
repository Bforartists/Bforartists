# ##### BEGIN GPL LICENSE BLOCK #####
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8-80 compliant>

#---------------------------------------------#
# todo
#---------------------------------------------#
'''
- add file selection for single and multiple files
- option to enable/disable fake users
'''

#---------------------------------------------#
import bpy
import os
from bpy.props import *

# addon description
bl_info = {
    "name": "Import BrushSet",
    "author": "Daniel Grauer (kromar), CansecoGPC",
    "version": (1, 2, 2),
    "blender": (2, 80, 0),
    "location": "File > Import > BrushSet",
    "description": "Imports all image files from a folder.",
    "warning": '',    # used for warning icon and text in addons panel
    "doc_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/Scripts/Import-Export/BrushSet",
    "tracker_url": "https://developer.blender.org/maniphest/task/edit/form/2/",
    "category": "Import-Export",
}

#---------------------------------------------#

# extension filter (alternative use mimetypes)
# TODO: rewrite so it tries to load image and if it fails we know its not a format blender can load
ext_list = ['.bmp',
            '.png',
            '.jpg',
            '.jp2',
            '.rgb',
            '.dds',
            '.hdr',
            '.exr',
            '.dpx',
            '.cin',
            '.tga',
            '.tif'];

#---------------------------------------------#

fakeUser = False

def LoadBrushSet(filepath, filename):
    for file in os.listdir(filepath):
        path = (filepath + file)

        # get folder name
        (f1, f2) = os.path.split(filepath)
        (f3, foldername) = os.path.split(f1)

        # filter files by extensions (filter images)
        if any(file.lower().endswith(ext) for ext in ext_list):
            print("file: ", file)
            # create new texture
            texture = bpy.data.textures.new(file, 'IMAGE')
            texture.use_fake_user = fakeUser
            print("texture: ", texture)

            # now we need to load the image into data
            image = bpy.data.images.load(path)
            image.use_fake_user = fakeUser
            # image.source = 'FILE' #default is FILE so can remove this
            # image.filepath = path
            print("image: ", image, " ", path)
            print("texturename: ", texture.name)

            # and assign the image to the texture
            bpy.data.textures[texture.name].image = image


    print("Brush Set imported!")

#---------------------------------------------#

class BrushSetImporter(bpy.types.Operator):
    '''Load Brush Set'''
    bl_idname = "import_image.brushset"
    bl_label = "Import BrushSet"

    filename: StringProperty(name = "File Name",
                              description = "filepath",
                              default = "",
                              maxlen = 1024,
                              options = {'ANIMATABLE'},
                              subtype = 'NONE')

    filepath: StringProperty(name = "File Name",
                              description = "filepath",
                              default = "",
                              maxlen = 1024,
                              options = {'ANIMATABLE'},
                              subtype = 'NONE')

    def execute(self, context):
        LoadBrushSet(self.properties.filepath, self.properties.filename)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

#---------------------------------------------#

def menu_func(self, context):
    # clear the default name for import
    import_name = ""

    self.layout.operator(BrushSetImporter.bl_idname, text = "Brush Set").filename = import_name


#---------------------------------------------#
# GUI
#---------------------------------------------#

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

#---------------------------------------------#

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
