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
    '''
    If a file fails, this replaces it with 1 char, better not remove it?
    '''
    file = open(filepath, 'w')
    file.write('\n') # apparently macosx needs some data in a blank file?
    file.close()


def check_vertcount(mesh, vertcount):
    '''
    check and make sure the vertcount is consistent throughout the frame range
    '''
    if len(mesh.vertices) != vertcount:
        raise Exception('Error, number of verts has changed during animation, cannot export')
        f.close()
        zero_file(filepath)
        return


def write(filename, sce, ob, PREF_STARTFRAME, PREF_ENDFRAME, PREF_FPS):
    """
    Blender.Window.WaitCursor(1)

    mesh_orig = Mesh.New()
    mesh_orig.getFromObject(ob.name)
    """

    bpy.ops.object.mode_set(mode='OBJECT')

    orig_frame = sce.frame_current
    sce.set_frame(PREF_STARTFRAME)
    me = ob.create_mesh(sce, True, 'PREVIEW')

    #Flip y and z
    mat_flip = mathutils.Matrix(\
    [1.0, 0.0, 0.0, 0.0],\
    [0.0, 0.0, 1.0, 0.0],\
    [0.0, 1.0, 0.0, 0.0],\
    [0.0, 0.0, 0.0, 1.0],\
    )

    numverts = len(me.vertices)

    numframes = PREF_ENDFRAME - PREF_STARTFRAME + 1
    PREF_FPS = float(PREF_FPS)
    f = open(filename, 'wb') #no Errors yet:Safe to create file

    # Write the header
    f.write(pack(">2i", numframes, numverts))

    # Write the frame times (should we use the time IPO??)
    f.write(pack(">%df" % (numframes), *[frame / PREF_FPS for frame in range(numframes)])) # seconds

    #rest frame needed to keep frames in sync
    """
    Blender.Set('curframe', PREF_STARTFRAME)
    me_tmp.getFromObject(ob.name)
    """

    check_vertcount(me, numverts)
    me.transform(mat_flip * ob.matrix_world)
    f.write(pack(">%df" % (numverts * 3), *[axis for v in me.vertices for axis in v.co]))

    for frame in range(PREF_STARTFRAME, PREF_ENDFRAME + 1):#in order to start at desired frame
        """
        Blender.Set('curframe', frame)
        me_tmp.getFromObject(ob.name)
        """

        sce.set_frame(frame)
        me = ob.create_mesh(sce, True, 'PREVIEW')
        check_vertcount(me, numverts)
        me.transform(mat_flip * ob.matrix_world)

        # Write the vertex data
        f.write(pack(">%df" % (numverts * 3), *[axis for v in me.vertices for axis in v.co]))

    """
    me_tmp.vertices= None
    """
    f.close()

    print('MDD Exported: %s frames:%d\n' % (filename, numframes - 1))
    """
    Blender.Window.WaitCursor(0)
    Blender.Set('curframe', orig_frame)
    """
    sce.set_frame(orig_frame)

from bpy.props import *
from io_utils import ExportHelper


class ExportMDD(bpy.types.Operator, ExportHelper):
    '''Animated mesh to MDD vertex keyframe file'''
    bl_idname = "export.mdd"
    bl_label = "Export MDD"
    
    filename_ext = ".mdd"

    # get first scene to get min and max properties for frames, fps

    minframe = 1
    maxframe = 300000
    minfps = 1
    maxfps = 120

    # List of operator properties, the attributes will be assigned
    # to the class instance from the operator settings before calling.
    fps = IntProperty(name="Frames Per Second", description="Number of frames/second", min=minfps, max=maxfps, default=25)
    frame_start = IntProperty(name="Start Frame", description="Start frame for baking", min=minframe, max=maxframe, default=1)
    frame_end = IntProperty(name="End Frame", description="End frame for baking", min=minframe, max=maxframe, default=250)

    @classmethod
    def poll(cls, context):
        ob = context.active_object
        return (ob and ob.type == 'MESH')

    def execute(self, context):
        filepath = self.properties.filepath
        filepath = bpy.path.ensure_ext(filepath, self.filename_ext)
        
        write(filepath,
              context.scene,
              context.active_object,
              self.properties.frame_start,
              self.properties.frame_end,
              self.properties.fps,
              )

        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ExportMDD.bl_idname, text="Lightwave Point Cache (.mdd)")


def register():
    bpy.types.INFO_MT_file_export.append(menu_func)


def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
