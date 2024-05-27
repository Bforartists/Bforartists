# SPDX-FileCopyrightText: 2011-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

""" This script is an exporter to the nuke's .chan files.
It takes the currently active object and writes it's transformation data
into a text file with .chan extension."""

from mathutils import Matrix, Euler
from math import radians, degrees


def save_chan(context, filepath, y_up, rot_ord):

    # get the active scene and object
    scene = context.scene
    obj = context.active_object
    camera = obj.data if obj.type == 'CAMERA' else None

    # get the range of an animation
    f_start = scene.frame_start
    f_end = scene.frame_end

    # prepare the correcting matrix
    rot_mat = Matrix.Rotation(radians(-90.0), 4, 'X').to_4x4()
    previous_rotation = Euler()

    filehandle = open(filepath, 'w')
    fw = filehandle.write

    # iterate the frames
    for frame in range(f_start, f_end + 1, 1):

        # set the current frame
        scene.frame_set(frame)

        # get the objects world matrix
        mat = obj.matrix_world.copy()

        # if the setting is proper use the rotation matrix
        # to flip the Z and Y axis
        if y_up:
            mat = rot_mat @ mat

        # create the first component of a new line, the frame number
        fw("%i\t" % frame)

        # create transform component
        t = mat.to_translation()
        fw("%f\t%f\t%f\t" % t[:])

        # create rotation component
        r = mat.to_euler(rot_ord, previous_rotation)

        fw("%f\t%f\t%f\t" % (degrees(r[0]), degrees(r[1]), degrees(r[2])))

        # store previous rotation for compatibility
        previous_rotation = r

        # if the selected object is a camera export vertical fov also
        if camera:
            vfov = degrees(camera.angle_y)
            fw("%f" % vfov)

        fw("\n")

    # after the whole loop close the file
    filehandle.close()

    return {'FINISHED'}
