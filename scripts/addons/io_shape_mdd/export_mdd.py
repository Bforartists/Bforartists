# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

# Contributors: Bill L.Nieuwendorp

"""
This script Exports Lightwaves MotionDesigner format.

The .mdd format has become quite a popular Pipeline format<br>
for moving animations from package to package.

Be sure not to use modifiers that change the number or order of verts in the mesh
"""

import bpy
import mathutils
from struct import pack


def zero_file(filepath):
    """
    If a file fails, this replaces it with 1 char, better not remove it?
    """
    file = open(filepath, 'w')
    file.write('\n')  # apparently macosx needs some data in a blank file?
    file.close()


def check_vertcount(mesh, vertcount):
    """
    check and make sure the vertcount is consistent throughout the frame range
    """
    if len(mesh.vertices) != vertcount:
        raise Exception('Error, number of verts has changed during animation, cannot export')


def save(context, filepath="", frame_start=1, frame_end=300, fps=25.0, use_rest_frame=False):
    """
    Blender.Window.WaitCursor(1)

    mesh_orig = Mesh.New()
    mesh_orig.getFromObject(obj.name)
    """

    scene = context.scene
    obj = context.object

    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    orig_frame = scene.frame_current
    scene.frame_set(frame_start)
    depsgraph = context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)
    me = obj_eval.to_mesh()

    #Flip y and z
    '''
    mat_flip = mathutils.Matrix(((1.0, 0.0, 0.0, 0.0),
                                 (0.0, 0.0, 1.0, 0.0),
                                 (0.0, 1.0, 0.0, 0.0),
                                 (0.0, 0.0, 0.0, 1.0),
                                 ))
    '''
    mat_flip = mathutils.Matrix()

    numverts = len(me.vertices)

    numframes = frame_end - frame_start + 1
    if use_rest_frame:
        numframes += 1

    f = open(filepath, 'wb')  # no Errors yet:Safe to create file

    # Write the header
    f.write(pack(">2i", numframes, numverts))

    # Write the frame times (should we use the time IPO??)
    f.write(pack(">%df" % (numframes), *[frame / fps for frame in range(numframes)]))  # seconds

    if use_rest_frame:
        check_vertcount(me, numverts)
        me.transform(mat_flip @ obj.matrix_world)
        f.write(pack(">%df" % (numverts * 3), *[axis for v in me.vertices for axis in v.co]))

    obj_eval.to_mesh_clear()

    for frame in range(frame_start, frame_end + 1):  # in order to start at desired frame
        scene.frame_set(frame)
        depsgraph = context.evaluated_depsgraph_get()
        obj_eval = obj.evaluated_get(depsgraph)
        me = obj_eval.to_mesh()
        check_vertcount(me, numverts)
        me.transform(mat_flip @ obj.matrix_world)

        # Write the vertex data
        f.write(pack(">%df" % (numverts * 3), *[axis for v in me.vertices for axis in v.co]))

        obj_eval.to_mesh_clear()

    f.close()

    print('MDD Exported: %r frames:%d\n' % (filepath, numframes - 1))
    scene.frame_set(orig_frame)

    return {'FINISHED'}
