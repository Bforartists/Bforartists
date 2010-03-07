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

import bpy
import sys as py_sys
platform = py_sys.platform

class SaveDirty(bpy.types.Operator):
    '''Select object matching a naming pattern'''
    bl_idname = "image.save_dirty"
    bl_label = "Save Dirty"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        unique_paths = set()
        for image in bpy.data.images:
            if image.dirty:
                path = bpy.utils.expandpath(image.filename)
                if "\\" not in path and "/" not in path:
                    self.report({'WARNING'}, "Invalid path: " + path)
                elif path in unique_paths:
                    self.report({'WARNING'}, "Path used by more then one image: " + path)
                else:
                    unique_paths.add(path)
                    image.save()
        return {'FINISHED'}


_proj_hack = [""]
class ProjectEdit(bpy.types.Operator):
    '''Select object matching a naming pattern'''
    bl_idname = "image.project_edit"
    bl_label = "Project Edit"
    bl_options = {'REGISTER'}

    def execute(self, context):
        import os
        import subprocess

        EXT = "tga" # until we have a way to save as another format!
        EDITOR = "gimp" # until we have a way to set a default image edior            

        for image in bpy.data.images:
            image.tag = True

        bpy.ops.paint.image_from_view()
        
        image_new = None
        for image in bpy.data.images:
            if not image.tag:
                image_new = image
                break
        
        if not image_new:
            self.report({'ERROR'}, "Could not make new image")
            return {'CANCELLED'}
        
        filename = os.path.basename(bpy.data.filename)
        filename = os.path.splitext(filename)[0]

        if filename.startswith("."): # TODO, have a way to check if the file is saved, assuem .B25.blend
            filename = os.path.join(os.path.dirname(bpy.data.filename), filename)
        else:
            filename = "//" + filename
        
        obj = context.object

        if obj:
            filename += "_" + bpy.utils.clean_name(obj.name)
        
        filename_final = filename + "." + EXT
        i = 0

        while os.path.exists(bpy.utils.expandpath(filename_final)):
            filename_final = filename + ("%.3d.%s" % (i, EXT))
            i += 1
        
        image_new.name = os.path.basename(filename_final)
        _proj_hack[0] = image_new.name
        
        image_new.filename_raw = filename_final # TODO, filename raw is crummy
        image_new.save()
        
        subprocess.Popen([EDITOR, bpy.utils.expandpath(filename_final)])
        
        return {'FINISHED'}


class ProjectApply(bpy.types.Operator):
    '''Select object matching a naming pattern'''
    bl_idname = "image.project_apply"
    bl_label = "Project Apply"
    bl_options = {'REGISTER'}

    def execute(self, context):
        image_name = _proj_hack[0] # TODO, deal with this nicer

        try:
            image = bpy.data.images[_proj_hack[0]]
        except KeyError:
            self.report({'ERROR'}, "Could not find image '%s'" % image_name)
            return {'CANCELLED'}

        image.reload()
        bpy.ops.paint.project_image(image=image_name)

        return {'FINISHED'}


classes = [
    SaveDirty,
    ProjectEdit,
    ProjectApply]


def register():
    register = bpy.types.register
    for cls in classes:
        register(cls)


def unregister():
    unregister = bpy.types.unregister
    for cls in classes:
        unregister(cls)

if __name__ == "__main__":
    register()
