# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
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

import os
import bpy
import bgl
import blf
import math


def draw_callback(self, context):
    mid = int(360 * self.recv / self.fsize)
    cx = 200
    cy = 30
    blf.position(0, 230, 23, 0)
    blf.size(0, 20, 72)
    blf.draw(0, "{0:2d}% of {1}".format(
        100 * self.recv // self.fsize, self.hfsize))

    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(.7, .7, .7, 0.8)
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex2i(cx, cy)
    for i in range(mid):
        x = cx + 20 * math.sin(math.radians(float(i)))
        y = cy + 20 * math.cos(math.radians(float(i)))
        bgl.glVertex2f(x, y)
    bgl.glEnd()

    bgl.glColor4f(.0, .0, .0, 0.6)
    bgl.glBegin(bgl.GL_TRIANGLE_FAN)
    bgl.glVertex2i(cx, cy)
    for i in range(mid, 360):
        x = cx + 20 * math.sin(math.radians(float(i)))
        y = cy + 20 * math.cos(math.radians(float(i)))
        bgl.glVertex2f(x, y)
    bgl.glEnd()

    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


class CMUMocapDownloadImport(bpy.types.Operator):
    bl_idname = "mocap.download_import"
    bl_label = "Download and Import a file"

    remote_file: bpy.props.StringProperty(
        name="Remote File",
        description="Location from where to download the file data")
    local_file: bpy.props.StringProperty(
        name="Local File",
        description="Destination where to save the file data")
    do_import: bpy.props.BoolProperty(
        name="Manual Import",
        description="Import the resource non-automatically",
        default=False)

    timer = None
    fout = None
    src = None
    fsize = 0
    recv = 0
    cloud_scale = 1

    def modal(self, context, event):
        context.area.tag_redraw()
        if event.type == 'ESC':
            self.fout.close()
            os.unlink(self.local_file)
            return self.cancel(context)
        if event.type == 'TIMER':
            to_read = min(self.fsize - self.recv, 100 * 2 ** 10)
            data = self.src.read(to_read)
            self.fout.write(data)
            self.recv += to_read
            if self.fsize == self.recv:
                self.fout.close()
                return self.cancel(context)
        return {'PASS_THROUGH'}

    def cancel(self, context):
        context.window_manager.event_timer_remove(self.timer)
        bpy.types.SpaceView3D.draw_handler_remove(self.handle, 'WINDOW')
        cml = context.preferences.addons['cmu_mocap_browser'].preferences
        if os.path.exists(self.local_file):
            return self.import_or_open(cml)
        return {'CANCELLED'}

    def execute(self, context):
        cml = context.preferences.addons['cmu_mocap_browser'].preferences
        if not os.path.exists(self.local_file):
            try:
                os.makedirs(os.path.split(self.local_file)[0])
            except:
                pass
            from urllib.request import urlopen
            self.src = urlopen(self.remote_file)
            info = self.src.info()
            self.fsize = int(info["Content-Length"])
            m = int(math.log10(self.fsize) // 3)
            self.hfsize = "{:.1f}{}".format(
                self.fsize * math.pow(10, -m * 3),
                ['b', 'Kb', 'Mb', 'Gb', 'Tb', 'Eb', 'Pb'][m])  # :-p
            self.fout = open(self.local_file, 'wb')
            self.recv = 0
            self.handle = bpy.types.SpaceView3D.draw_handler_add(
                draw_callback, (self, context), 'WINDOW', 'POST_PIXEL')
            self.timer = context.window_manager.\
                event_timer_add(0.001, context.window)
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.import_or_open(cml)
        return {'FINISHED'}

    def import_or_open(self, cml):
        if cml.automatically_import or self.do_import:
            if self.local_file.endswith("mpg"):
                bpy.ops.wm.path_open(filepath=self.local_file)
            elif self.local_file.endswith("asf"):
                try:
                    bpy.ops.import_anim.asf(
                        filepath=self.local_file,
                        from_inches=True,
                        use_rot_x=True, use_rot_z=True,
                        armature_name=cml.subject_import_name)
                except AttributeError:
                    self.report({'ERROR'}, "To use this feature "
                        "please enable the Acclaim ASF/AMC Importer addon.")
                    return {'CANCELLED'}
            elif self.local_file.endswith("amc"):
                ob = bpy.context.active_object
                if not ob or ob.type != 'ARMATURE' or \
                    'source_file_path' not in ob:
                    self.report({'ERROR'}, "Please select a CMU Armature.")
                    return {'CANCELLED'}
                try:
                    bpy.ops.import_anim.amc(
                        filepath=self.local_file,
                        frame_skip=cml.frame_skip)
                except AttributeError:
                    self.report({'ERROR'}, "To use this feature please "
                        "enable the Acclaim ASF/AMC Importer addon.")
                    return {'CANCELLED'}
            elif self.local_file.endswith("c3d"):
                try:
                    bpy.ops.import_anim.c3d(
                        filepath=self.local_file,
                        from_inches=False,
                        auto_scale=True,
                        scale=cml.cloud_scale,
                        show_names=False,
                        frame_skip=cml.frame_skip)
                except AttributeError:
                    self.report({'ERROR'}, "To use this feature "
                        "please enable the C3D Importer addon.")
                    return {'CANCELLED'}

        return {'FINISHED'}
