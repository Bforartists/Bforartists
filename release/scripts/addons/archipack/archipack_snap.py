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
# Author: Stephen Leger (s-leger)
# Inspired by Okavango's np_point_move
# ----------------------------------------------------------
"""
    Usage:
        from .archipack_snap import snap_point

        snap_point(takeloc, draw_callback, action_callback, constraint_axis)

        arguments:

        takeloc Vector3d location of point to snap

        constraint_axis boolean tuple for each axis
              eg: (True, True, False) to constrtaint to xy plane

        draw_callback(context, sp)
            sp.takeloc
            sp.placeloc
            sp.delta

        action_callback(context, event, state, sp)
            state in {'RUNNING', 'SUCCESS', 'CANCEL'}
            sp.takeloc
            sp.placeloc
            sp.delta

        with 3d Vectors
        - delta     = placeloc - takeloc
        - takeloc
        - placeloc


        NOTE:
            may change grid size to 0.1 round feature (SHIFT)
            see https://blenderartists.org/forum/showthread.php?205158-Blender-2-5-Snap-mode-increment
            then use a SHIFT use grid snap

"""

import bpy
from bpy.types import Operator
from mathutils import Vector, Matrix
import logging

logger = logging.getLogger("archipack")


def dumb_callback(context, event, state, sp):
    return


def dumb_draw(sp, context):
    return


class SnapStore:
    """
        Global store
    """
    callback = None
    draw = None
    helper = None
    takeloc = Vector()
    placeloc = Vector()
    constraint_axis = (True, True, False)
    helper_matrix = Matrix()
    transform_orientation = 'GLOBAL'
    release_confirm = True
    instances_running = 0

    # context related
    act = None
    sel = []
    use_snap = False
    snap_elements = None
    snap_target = None
    pivot_point = None
    trans_orientation = None


def snap_point(takeloc=None,
               draw=None,
               callback=dumb_callback,
               takemat=None,
               constraint_axis=(True, True, False),
               transform_orientation='GLOBAL',
               mode='OBJECT',
               release_confirm=True):
    """
        Invoke op from outside world
        in a convenient importable function

        transform_orientation in [‘GLOBAL’, ‘LOCAL’, ‘NORMAL’, ‘GIMBAL’, ‘VIEW’]

        draw(sp, context) a draw callback
        callback(context, event, state, sp) action callback

        Use either :
        takeloc Vector, unconstraint or system axis constraints
        takemat Matrix, constaint to this matrix as 'LOCAL' coordsys
            The snap source helper use it as world matrix
            so it is possible to constraint to user defined coordsys.
    """
    SnapStore.draw = draw
    SnapStore.callback = callback
    SnapStore.constraint_axis = constraint_axis
    SnapStore.release_confirm = release_confirm

    if takemat is not None:
        SnapStore.helper_matrix = takemat
        takeloc = takemat.translation.copy()
        transform_orientation = 'LOCAL'
    elif takeloc is not None:
        SnapStore.helper_matrix = Matrix.Translation(takeloc)
    else:
        raise ValueError("ArchipackSnap: Either takeloc or takemat must be defined")

    SnapStore.takeloc = takeloc
    SnapStore.placeloc = takeloc.copy()

    SnapStore.transform_orientation = transform_orientation

    # @NOTE: unused mode var to switch between OBJECT and EDIT mode
    # for ArchipackSnapBase to be able to handle both modes
    # must implements corresponding helper create and delete actions
    SnapStore.mode = mode
    bpy.ops.archipack.snap('INVOKE_DEFAULT')
    # return helper so we are able to move it "live"
    return SnapStore.helper


class ArchipackSnapBase():
    """
        Helper class for snap Operators
        store and restore context
        create and destroy helper
        install and remove a draw_callback working while snapping

        store and provide access to 3d Vectors
        in draw_callback and action_callback
        - delta     = placeloc - takeloc
        - takeloc
        - placeloc
    """

    def __init__(self):
        self._draw_handler = None

    def init(self, context, event):
        # Store context data
        # if SnapStore.instances_running < 1:
        SnapStore.sel = context.selected_objects[:]
        SnapStore.act = context.object
        bpy.ops.object.select_all(action="DESELECT")
        ts = context.tool_settings
        SnapStore.use_snap = ts.use_snap
        SnapStore.snap_elements = ts.snap_elements
        SnapStore.snap_target = ts.snap_target
        SnapStore.pivot_point = ts.transform_pivot_point
        SnapStore.trans_orientation = context.scene.transform_orientation
        self.create_helper(context)
        # Use a timer to broadcast a TIMER event while transform.translate is running
        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)

        if SnapStore.draw is not None:
            args = (self, context)
            self._draw_handler = bpy.types.SpaceView3D.draw_handler_add(SnapStore.draw, args, 'WINDOW', 'POST_PIXEL')

    def remove_timer(self, context):
        if self._timer is not None:
            context.window_manager.event_timer_remove(self._timer)

    def exit(self, context):

        self.remove_timer(context)

        if self._draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handler, 'WINDOW')

        # Restore original context
        if hasattr(context, "tool_settings"):
            ts = context.tool_settings
            ts.use_snap = SnapStore.use_snap
            ts.snap_elements = SnapStore.snap_elements
            ts.snap_target = SnapStore.snap_target
            ts.transform_pivot_point = SnapStore.pivot_point
        context.scene.transform_orientation = SnapStore.trans_orientation
        for o in SnapStore.sel:
            o.select_set(state=True)
        if SnapStore.act is not None:
            SnapStore.act.select_set(state=True)
            context.view_layer.objects.active = SnapStore.act
        self.destroy_helper(context)
        logger.debug("Snap.exit %s", context.object.name)

    def create_helper(self, context):
        """
            Create a helper with fake user
            or find older one in bpy data and relink to scene
            currently only support OBJECT mode

            Do target helper be linked to scene in order to work ?

        """
        helper = bpy.data.objects.get('Archipack_snap_helper')
        if helper is not None:
            print("helper found")
            if context.scene.objects.get('Archipack_snap_helper') is None:
                print("link helper")
                # self.link_object_to_scene(context, helper)
                context.scene.collection.objects.link(helper)
        else:
            print("create helper")
            m = bpy.data.meshes.new("Archipack_snap_helper")
            m.vertices.add(count=1)
            helper = bpy.data.objects.new("Archipack_snap_helper", m)
            context.scene.collection.objects.link(helper)
            helper.use_fake_user = True
            helper.data.use_fake_user = True

        helper.matrix_world = SnapStore.helper_matrix
        helper.select_set(state=True)
        context.view_layer.objects.active = helper
        SnapStore.helper = helper

    def destroy_helper(self, context):
        """
            Unlink helper
            currently only support OBJECT mode
        """
        if SnapStore.helper is not None:
            # @TODO: Fix this
            # self.unlink_object_from_scene(context, SnapStore.helper)
            SnapStore.helper = None

    @property
    def delta(self):
        return self.placeloc - self.takeloc

    @property
    def takeloc(self):
        return SnapStore.takeloc

    @property
    def placeloc(self):
        # take from helper when there so the delta
        # is working even while modal is running
        if SnapStore.helper is not None:
            return SnapStore.helper.location
        else:
            return SnapStore.placeloc


class ARCHIPACK_OT_snap(ArchipackSnapBase, Operator):
    bl_idname = 'archipack.snap'
    bl_label = 'Archipack snap'
    bl_options = {'INTERNAL'}  # , 'UNDO'

    def modal(self, context, event):

        if SnapStore.helper is not None:
            logger.debug("Snap.modal event %s %s location:%s",
                         event.type,
                         event.value,
                         SnapStore.helper.location)

        context.area.tag_redraw()

        if event.type in ('TIMER', 'NOTHING'):
            SnapStore.callback(context, event, 'RUNNING', self)
            return {'PASS_THROUGH'}

        if event.type not in ('ESC', 'RIGHTMOUSE', 'LEFTMOUSE', 'MOUSEMOVE', 'INBETWEEN_MOUSEMOVE'):
            return {'PASS_THROUGH'}

        if event.type in ('ESC', 'RIGHTMOUSE'):
            SnapStore.callback(context, event, 'CANCEL', self)
        else:
            SnapStore.placeloc = SnapStore.helper.location
            # on tt modal exit with right click, the delta is 0 so exit
            if self.delta.length == 0:
                SnapStore.callback(context, event, 'CANCEL', self)
            else:
                SnapStore.callback(context, event, 'SUCCESS', self)

        self.exit(context)
        # self.report({'INFO'}, "ARCHIPACK_OT_snap exit")
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':

            if event.type in ('ESC', 'RIGHTMOUSE'):
                return {'FINISHED'}

            self.init(context, event)

            logger.debug("Snap.invoke event %s %s location:%s act:%s",
                         event.type,
                         event.value,
                         SnapStore.helper.location, context.object.name)

            context.window_manager.modal_handler_add(self)

            bpy.ops.transform.translate('INVOKE_DEFAULT',
                                        constraint_axis=SnapStore.constraint_axis,
                                        constraint_orientation=SnapStore.transform_orientation,
                                        release_confirm=SnapStore.release_confirm)

            logger.debug("Snap.invoke transform.translate done")

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'FINISHED'}


def register():
    bpy.utils.register_class(ARCHIPACK_OT_snap)


def unregister():
    bpy.utils.unregister_class(ARCHIPACK_OT_snap)
