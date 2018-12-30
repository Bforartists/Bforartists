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
from bpy.types import Operator
import os
import shutil


class collectImagesOsc(Operator):
    """Collect all images in the blend file and put them in IMAGES folder"""
    bl_idname = "file.collect_all_images"
    bl_label = "Collect Images"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):

        imagespath = "%s/IMAGES"  % (os.path.dirname(bpy.data.filepath))

        if not os.path.exists(imagespath):
            os.mkdir(imagespath)

        bpy.ops.file.make_paths_absolute()

        for image in bpy.data.images:
            try:
                image.update()

                if image.has_data:
                    if not os.path.exists(os.path.join(imagespath,os.path.basename(image.filepath))):
                        shutil.copy(image.filepath, os.path.join(imagespath,os.path.basename(image.filepath)))
                        image.filepath = os.path.join(imagespath,os.path.basename(image.filepath))
                    else:
                        print("%s exists." % (image.name))
                else:
                    print("%s missing path." % (image.name))
            except:
                print("%s missing path." % (image.name))

        bpy.ops.file.make_paths_relative()

        return {'FINISHED'}
