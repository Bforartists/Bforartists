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

"""
Blender-CoD: Blender Add-On for Call of Duty modding
Version: alpha 3

Copyright (c) 2011 CoDEmanX, Flybynyt -- blender-cod@online.de

http://code.google.com/p/blender-cod/

TODO
- Test pose matrix exports, global or local?

"""

import bpy
from datetime import datetime

def save(self, context, filepath="",
         use_selection=False,
         use_framerate=24,
         use_frame_start=1,
         use_frame_end=250,
         use_notetrack=True,
         use_notetrack_format='1'):

    armature = None
    last_frame_current = context.scene.frame_current

    # There's no context object right after object deletion, need to set one
    if context.object:
        last_mode = context.object.mode
    else:
        last_mode = 'OBJECT'

        if bpy.data.objects:
            context.scene.objects.active = bpy.data.objects[0]
        else:
            return "Nothing to export."

    # HACK: Force an update, so that bone tree is properly sorted for hierarchy table export
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    # Check input objects, don't move this above hack!
    for ob in bpy.data.objects:

        # Take the first armature
        if ob.type == 'ARMATURE' and len(ob.data.bones) > 0:
            armature = ob
            break
    else:
        return "No armature to export."

    # Get the wanted bones
    if use_selection:
        bones = [b for b in armature.data.bones if b.select]
    else:
        bones = armature.data.bones

    # Get armature matrix once for later global coords/matrices calculation per frame
    a_matrix = armature.matrix_world

    # There's valid data for export, create output file
    try:
        file = open(filepath, "w")
    except IOError:
        return "Could not open file for writing:\n%s" % filepath

     # write the header
    file.write("// XANIM_EXPORT file in CoD animation v3 format created with Blender v%s\n" \
               % bpy.app.version_string)
    file.write("// Source file: %s\n" % filepath)
    file.write("// Export time: %s\n\n" % datetime.now().strftime("%d-%b-%Y %H:%M:%S"))
    file.write("ANIMATION\n")
    file.write("VERSION 3\n\n")

    file.write("NUMPARTS %i\n" % len(bones))

    # Write bone table
    for i_bone, bone in enumerate(bones):
        file.write("PART %i \"%s\"\n" % (i_bone, bone.name))

    # Exporter shall use Blender's framerate (render settings, used as playback speed)
    # Note: Time remapping not taken into account
    file.write("\nFRAMERATE %i\n" % use_framerate)

    file.write("NUMFRAMES %i\n\n" % (abs(use_frame_start - use_frame_end) + 1))

    # If start frame greater than end frame, export animation reversed
    if use_frame_start < use_frame_end:
        frame_order = 1
        frame_min = use_frame_start
        frame_max = use_frame_end
    else:
        frame_order = -1
        frame_min = use_frame_end
        frame_max = use_frame_start

    for i_frame, frame in enumerate(range(use_frame_start,
                                          use_frame_end + frame_order,
                                          frame_order),
                                    frame_min):

        file.write("FRAME %i\n" % i_frame)

        # Set frame directly
        context.scene.frame_set(frame)

        # Get PoseBones for that frame
        if use_selection:
            bones = [b for b in armature.pose.bones if b.bone.select]
        else:
            bones = armature.pose.bones

        # Write bone orientations
        for i_bone, bone in enumerate(bones):

            # Skip bone if 'Selection only' is enabled and bone not selected
            if use_selection and not bone.bone.select: # It's actually posebone.bone!
                continue

            file.write("PART %i\n" % i_bone)


            """ Doesn't seem to be right... or maybe it is? root can't have rotation, it rather sets the global orientation
            if bone.parent is None:
                file.write("OFFSET 0.000000 0.000000 0.000000\n")
                file.write("SCALE 1.000000 1.000000 1.000000\n")
                file.write("X 1.000000, 0.000000, 0.000000\n")
                file.write("Y 0.000000, 1.000000, 0.000000\n")
                file.write("Z 0.000000, 0.000000, 1.000000\n\n")
            else:
            """

            b_tail = a_matrix * bone.tail
            file.write("OFFSET %.6f %.6f %.6f\n" % (b_tail[0], b_tail[1], b_tail[2]))
            file.write("SCALE 1.000000 1.000000 1.000000\n") # Is this even supported by CoD?
            
            file.write("X %.6f %.6f %.6f\n" % (bone.matrix[0][0], bone.matrix[1][0], bone.matrix[2][0]))
            file.write("Y %.6f %.6f %.6f\n" % (bone.matrix[0][1], bone.matrix[1][1], bone.matrix[2][1]))
            file.write("Z %.6f %.6f %.6f\n\n" % (bone.matrix[0][2], bone.matrix[1][2], bone.matrix[2][2]))

            """
            # Is a local matrix used (above) or a global?
            # Rest pose bone roll shouldn't matter if local is used... o_O
            # Note: Converting to xanim delta doesn't allow bone moves (only root?)
            b_matrix = a_matrix * bone.matrix
            file.write("X %.6f %.6f %.6f\n" % (b_matrix[0][0], b_matrix[1][0], b_matrix[2][0]))
            file.write("Y %.6f %.6f %.6f\n" % (b_matrix[0][1], b_matrix[1][1], b_matrix[2][1]))
            file.write("Z %.6f %.6f %.6f\n" % (b_matrix[0][2], b_matrix[1][2], b_matrix[2][2]))
            """

    # Blender timeline markers to notetrack nodes
    markers = []
    for m in context.scene.timeline_markers:
        if frame_max >= m.frame >= frame_min:
            markers.append([m.frame, m.name])
    markers = sorted(markers)

    # Cache marker string
    marker_string = "NUMKEYS %i\n" % len(markers)

    for m in markers:
        marker_string += "FRAME %i \"%s\"\n" % (m[0], m[1])

    # Write notetrack data
    if use_notetrack_format == '7':
        # Always 0 for CoD7, no matter if there are markers or not!
        file.write("NUMKEYS 0\n")
    else:
        file.write("NOTETRACKS\n\n")

        for i_bone, bone in enumerate(bones):

            file.write("PART %i\n" % (i_bone))

            if i_bone == 0 and use_notetrack and use_notetrack_format == '1' and len(markers) > 0:

                file.write("NUMTRACKS 1\n\n")
                file.write("NOTETRACK 0\n")
                file.write(marker_string)
                file.write("\n")

            else:
                file.write("NUMTRACKS 0\n\n")

    # Close to flush buffers!
    file.close()

    if use_notetrack and use_notetrack_format in {'5', '7'}:

        import os.path
        filepath = os.path.splitext(filepath)[0] + ".NT_EXPORT"

        try:
            file = open(filepath, "w")
        except IOError:
            return "Could not open file for writing:\n%s" % filepath

        if use_notetrack_format == '7':
            file.write("FIRSTFRAME %i\n" % use_frame_start)
            file.write("NUMFRAMES %i\n" % (abs(use_frame_end - use_frame_start) + 1))
        file.write(marker_string)

        file.close()

    # Set frame_current and mode back
    context.scene.frame_set(last_frame_current)
    bpy.ops.object.mode_set(mode=last_mode, toggle=False)

    # Quit with no errors
    return
