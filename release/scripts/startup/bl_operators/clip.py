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
import os
import shutil
from bpy.types import Operator
from bpy_extras.io_utils import unpack_list


def CLIP_track_view_selected(sc, track):
    if track.select_anchor:
        return True

    if sc.show_marker_pattern and track.select_pattern:
        return True

    if sc.show_marker_search and track.select_search:
        return True

    return False


class CLIP_OT_track_to_empty(Operator):
    """Create an Empty object which will be copying movement of active track"""

    bl_idname = "clip.track_to_empty"
    bl_label = "Link Empty to Track"
    bl_options = {'UNDO', 'REGISTER'}

    def _link_track(self, context, track):
        sc = context.space_data
        constraint = None
        ob = None

        ob = bpy.data.objects.new(name=track.name, object_data=None)
        ob.select = True
        bpy.context.scene.objects.link(ob)
        bpy.context.scene.objects.active = ob

        for con in ob.constraints:
            if con.type == 'FOLLOW_TRACK':
                constraint = con
                break

        if constraint is None:
            constraint = ob.constraints.new(type='FOLLOW_TRACK')

        constraint.clip = sc.clip
        constraint.track = track.name
        constraint.use_3d_position = False

    def execute(self, context):
        sc = context.space_data
        clip = sc.clip

        for track in clip.tracking.tracks:
            if CLIP_track_view_selected(sc, track):
                self._link_track(context, track)

        return {'FINISHED'}


class CLIP_OT_tracks_to_mesh(Operator):
    """Create vertex cloud using coordinates of tracks"""

    bl_idname = "clip.tracks_to_mesh"
    bl_label = "Tracks to Mesh"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.space_data.type != 'CLIP_EDITOR':
            return False

        sc = context.space_data
        clip = sc.clip

        return clip

    def execute(self, context):
        sc = context.space_data
        clip = sc.clip

        new_verts = []

        mesh = bpy.data.meshes.new(name="Tracks")
        for track in clip.tracking.tracks:
            if track.has_bundle:
                new_verts.append(track.bundle)

        if new_verts:
            mesh.vertices.add(len(new_verts))
            mesh.vertices.foreach_set("co", unpack_list(new_verts))

        ob = bpy.data.objects.new(name="Tracks", object_data=mesh)

        bpy.context.scene.objects.link(ob)

        return {'FINISHED'}


class CLIP_OT_delete_proxy(Operator):
    """Delete movie clip proxy files from the hard drive"""

    bl_idname = "clip.delete_proxy"
    bl_label = "Delete Proxy"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.space_data.type != 'CLIP_EDITOR':
            return False

        sc = context.space_data

        return sc.clip

    def invoke(self, context, event):
        wm = context.window_manager

        return wm.invoke_confirm(self, event)

    def _rmproxy(self, abspath):
        if not os.path.exists(abspath):
            return

        if os.path.isdir(abspath):
            shutil.rmtree(abspath)
        else:
            os.remove(abspath)

    def execute(self, context):
        sc = context.space_data
        clip = sc.clip
        if clip.use_proxy_custom_directory:
            proxydir = clip.proxy.directory
        else:
            clipdir = os.path.dirname(clip.filepath)
            proxydir = os.path.join(clipdir, 'BL_proxy')

        clipfile = os.path.basename(clip.filepath)
        proxy = os.path.join(proxydir, clipfile)
        absproxy = bpy.path.abspath(proxy)

        # proxy_<quality>[_undostorted]
        for x in (25, 50, 75, 100):
            d = os.path.join(absproxy, 'proxy_' + str(x))

            self._rmproxy(d)
            self._rmproxy(d + '_undistorted')
            self._rmproxy(os.path.join(absproxy, 'proxy_' + str(x) + '.avi'))

        tc = ('free_run.blen_tc',
              'interp_free_run.blen_tc',
              'record_run.blen_tc')

        for x in tc:
            self._rmproxy(os.path.join(absproxy, x))

        # remove proxy per-clip directory
        try:
            os.rmdir(absproxy)
        except OSError:
            pass

        # remove [custom] proxy directory if empty
        try:
            absdir = bpy.path.abspath(proxydir)
            os.rmdir(absdir)
        except OSError:
            pass

        return {'FINISHED'}


class CLIP_OT_set_viewport_background(Operator):
    """Set current movie clip as a camera background in 3D viewport \
(works only when a 3D viewport is visible)"""

    bl_idname = "clip.set_viewport_background"
    bl_label = "Set as Background"
    bl_options = {'UNDO', 'REGISTER'}

    @classmethod
    def poll(cls, context):
        if context.space_data.type != 'CLIP_EDITOR':
            return False

        sc = context.space_data

        return sc.clip

    def _set_background(self, space_v3d, clip, user):
        bgpic = None

        for x in space_v3d.background_images:
            if x.source == 'MOVIE':
                bgpic = x
                break

        if not bgpic:
            bgpic = space_v3d.background_images.add()

        bgpic.source = 'MOVIE'
        bgpic.clip = clip
        bgpic.clip_user.proxy_render_size = user.proxy_render_size
        bgpic.clip_user.use_render_undistorted = user.use_render_undistorted
        bgpic.use_camera_clip = False
        bgpic.view_axis = 'CAMERA'

        space_v3d.show_background_images = True

    def execute(self, context):
        sc = context.space_data
        clip = sc.clip

        for area in context.window.screen.areas:
            if area.type == 'VIEW_3D':
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        self._set_background(space, clip, sc.clip_user)

        return {'FINISHED'}


class CLIP_OT_constraint_to_fcurve(Operator):
    """Create F-Curves for object which will copy \
object's movement caused by this constraint"""

    bl_idname = "clip.constraint_to_fcurve"
    bl_label = "Constraint to F-Curve"
    bl_options = {'UNDO', 'REGISTER'}

    def _bake_object(self, scene, ob):
        con = None
        clip = None
        sfra = None
        efra = None
        frame_current = scene.frame_current
        matrices = []

        # Find constraint which would eb converting
        # TODO: several camera solvers and track followers would fail,
        #       but can't think about eal workflow where it'll be useful
        for x in ob.constraints:
            if x.type in ('CAMERA_SOLVER', 'FOLLOW_TRACK'):
                con = x

        if not con:
            return

        if con.type == 'FOLLOW_TRACK' and con.use_3d_position:
            mat = ob.matrix_world.copy()
            ob.constraints.remove(con)
            ob.matrix_world = mat

            return

        # Get clip used for parenting
        if con.use_active_clip:
            clip = scene.active_clip
        else:
            clip = con.clip

        if not clip:
            return

        # Find start and end frames
        for track in clip.tracking.tracks:
            if sfra is None:
                sfra = track.markers[0].frame
            else:
                sfra = min(sfra, track.markers[0].frame)

            if efra is None:
                efra = track.markers[-1].frame
            else:
                efra = max(efra, track.markers[-1].frame)

        if sfra is None or efra is None:
            return

        # Store object matrices
        for x in range(sfra, efra + 1):
            scene.frame_set(x)
            matrices.append(ob.matrix_world.copy())

        ob.animation_data_create()

        # Apply matrices on object and insert keyframes
        i = 0
        for x in range(sfra, efra + 1):
            scene.frame_set(x)
            ob.matrix_world = matrices[i]

            ob.keyframe_insert("location")

            if ob.rotation_mode == 'QUATERNION':
                ob.keyframe_insert("rotation_quaternion")
            else:
                ob.keyframe_insert("rotation_euler")

            i += 1

        ob.constraints.remove(con)

        scene.frame_set(frame_current)

    def execute(self, context):
        scene = context.scene

        for ob in scene.objects:
            if ob.select:
                self._bake_object(scene, ob)

        return {'FINISHED'}
