# -*- coding:utf-8 -*-

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
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110- 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# support routines for render measures in final image
# Author: Antonio Vazquez (antonioya)
# Archipack adaptation by : Stephen Leger (s-leger)
#
# ----------------------------------------------------------
# noinspection PyUnresolvedReferences
import bpy
# noinspection PyUnresolvedReferences
import bgl
from shutil import copyfile
from os import path, listdir
import subprocess
# noinspection PyUnresolvedReferences
import bpy_extras.image_utils as img_utils
# noinspection PyUnresolvedReferences
from math import ceil
from bpy.types import Operator
# from bl_ui import properties_render


class ARCHIPACK_OT_render_thumbs(Operator):
    bl_idname = "archipack.render_thumbs"
    bl_label = "Render presets thumbs"
    bl_description = "Setup default presets and update thumbs"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        # Ensure CYCLES engine is available
        # hasattr(context.scene, 'cycles')
        return context.scene

    def background_render(self, context, cls, preset):
        generator = path.dirname(path.realpath(__file__)) + path.sep + "archipack_thumbs.py"
        addon_name = __name__.split('.')[0]
        matlib_path = context.preferences.addons[addon_name].preferences.matlib_path
        # Run external instance of blender like the original thumbnail generator.
        cmd = [
            bpy.app.binary_path,
            "--background",
            "--factory-startup",
            "-noaudio",
            # "--addons", addon_name,
            "--python", generator,
            "--",
            "addon:" + addon_name,
            "matlib:" + matlib_path,
            "cls:" + cls,
            "preset:" + preset
            ]

        # print(" ".join(cmd))

        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
        for stdout_line in iter(popen.stdout.readline, ""):
            yield stdout_line
        popen.stdout.close()
        popen.wait()

    def copy_to_user_path(self, category):
        """
        Copy factory presets to writeable presets folder
        Two cases here:
        1 there is not presets thumbs found (official version)
        2 thumbs already are there (unofficial)
        """
        file_list = []
        # load default presets
        dir_path = path.dirname(path.realpath(__file__))
        sub_path = "presets" + path.sep + category
        source_path = path.join(dir_path, sub_path)
        if path.exists(source_path):
            file_list.extend([f
                for f in listdir(source_path)
                if (f.endswith('.py') or f.endswith('.txt')) and
                not f.startswith('.')])

        target_path = path.join("presets", category)
        presets_path = bpy.utils.user_resource('SCRIPTS',
                                              target_path,
                                              create=True)
        # files from factory not found in user dosent require a recompute
        skipfiles = []
        for f in file_list:
            # copy python/txt preset
            if not path.exists(presets_path + path.sep + f):
                copyfile(source_path + path.sep + f, presets_path + path.sep + f)

            # skip txt files (material presets)
            if f.endswith(".txt"):
                skipfiles.append(f)

            # when thumbs already are in factory folder but not found in user one
            # simply copy them, and add preset to skip list
            thumb_filename = f[:-3] + ".png"
            if path.exists(source_path + path.sep + thumb_filename):
                if not path.exists(presets_path + path.sep + thumb_filename):
                    copyfile(source_path + path.sep + thumb_filename, presets_path + path.sep + thumb_filename)
                    skipfiles.append(f)

        return skipfiles

    def scan_files(self, category):
        file_list = []

        # copy from factory to user writeable folder
        skipfiles = self.copy_to_user_path(category)

        # load user def presets
        preset_paths = bpy.utils.script_paths("presets")
        for preset in preset_paths:
            presets_path = path.join(preset, category)
            if path.exists(presets_path):
                file_list += [presets_path + path.sep + f[:-3]
                    for f in listdir(presets_path)
                    if f.endswith('.py') and
                    not f.startswith('.') and
                    f not in skipfiles]

        file_list.sort()
        return file_list

    def rebuild_thumbs(self, context):
        file_list = []
        dir_path = path.dirname(path.realpath(__file__))
        sub_path = "presets"
        presets_path = path.join(dir_path, sub_path)
        # print(presets_path)
        if path.exists(presets_path):
            dirs = listdir(presets_path)
            for dir in dirs:
                abs_dir = path.join(presets_path, dir)
                if path.isdir(abs_dir):
                    files = self.scan_files(dir)
                    file_list.extend([(dir, file) for file in files])

        ttl = len(file_list)
        for i, preset in enumerate(file_list):
            dir, file = preset
            cls = dir[10:]
            # context.scene.archipack_progress = (100 * i / ttl)
            log_all = False
            for l in self.background_render(context, cls, file + ".py"):
                if "[log]" in l:
                    print(l[5:].strip())
                elif "blender.crash" in l:
                    print("Unexpected error")
                    log_all = True
                if log_all:
                    print(l.strip())

    def invoke(self, context, event):
        addon_name = __name__.split('.')[0]
        matlib_path = context.preferences.addons[addon_name].preferences.matlib_path

        if matlib_path == '':
            self.report({'WARNING'}, "You should setup a default material library path in addon preferences")
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        # context.scene.archipack_progress_text = 'Generating thumbs'
        # context.scene.archipack_progress = 0
        self.rebuild_thumbs(context)
        # context.scene.archipack_progress = -1
        return {'FINISHED'}


def register():
    bpy.utils.register_class(ARCHIPACK_OT_render_thumbs)


def unregister():
    bpy.utils.unregister_class(ARCHIPACK_OT_render_thumbs)
