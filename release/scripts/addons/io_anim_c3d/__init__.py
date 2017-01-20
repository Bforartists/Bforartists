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

# <pep8-80 compliant>

# This script was developed with financial support from the Foundation for
# Science and Technology of Portugal, under the grant SFRH/BD/66452/2009.


bl_info = {
    "name": "C3D Graphics Lab Motion Capture file (.c3d)",
    "author": "Daniel Monteiro Basso <daniel@basso.inf.br>",
    "version": (2013, 12, 10, 1),
    "blender": (2, 69, 5),
    "location": "File > Import",
    "description": "Imports C3D Graphics Lab Motion Capture files",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
                "Scripts/Import-Export/C3D_Importer",
    "category": 'Import-Export',
}


import bpy
from bpy.props import (
        StringProperty,
        BoolProperty,
        FloatProperty,
        IntProperty,
        )

import math
import time
from mathutils import Vector
from . import import_c3d


class C3DAnimateCloud(bpy.types.Operator):
    """
        Animate the Marker Cloud
    """
    bl_idname = "import_anim.c3danim"
    bl_label = "Animate C3D"

    markerset = None
    uname = None
    curframe = 0
    fskip = 0
    scale = 0
    timer = None
    Y_up = False

    def modal(self, context, event):
        if event.type == 'ESC':
            return self.cancel(context)
        if event.type == 'TIMER':
            if self.curframe > self.markerset.endFrame:
                return self.cancel(context)
            fno = self.curframe
            if not self.use_frame_no:
                fno = (self.curframe - self.markerset.startFrame) / self.fskip
            for i in range(self.fskip):
                self.markerset.readNextFrameData()
            for ml in self.markerset.markerLabels:
                name = self.unames[self.prefix + ml]
                o = bpy.context.scene.objects[name]
                m = self.markerset.getMarker(ml, self.curframe)
                p = Vector(m.position) * self.scale
                o.location = Vector((p[0], -p[2], p[1])) if self.Y_up else p
                if m.confidence >= self.confidence:
                    o.keyframe_insert('location', frame=fno)
            self.curframe += self.fskip
        return {'PASS_THROUGH'}

    def execute(self, context):
        self.timer = context.window_manager.\
            event_timer_add(0.001, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)
        context.window_manager.event_timer_remove(self.timer)
        return {'FINISHED'}


class C3DImporter(bpy.types.Operator):
    """
        Load a C3D Marker Cloud
    """
    bl_idname = "import_anim.c3d"
    bl_label = "Import C3D"

    filepath = StringProperty(
            subtype='FILE_PATH',
            )
    Y_up = BoolProperty(
            name="Up vector is Y axis",
            default=False,
            description="Check when the data uses Y-up, uncheck when it uses Z-up",
            )
    from_inches = BoolProperty(
            name="Convert from inches to meters",
            default=False,
            description="Scale by 2.54/100",
            )
    scale = FloatProperty(
            name="Scale",
            default=1.0,
            description="Scale the positions by this value",
            min=0.0000001, max=1000000.0,
            soft_min=0.001, soft_max=100.0,
            )
    auto_scale = BoolProperty(
            name="Adjust scale automatically",
            default=False,
            description="Guess correct scale factor",
            )
    auto_magnitude = BoolProperty(
            name="Adjust scale magnitude",
            default=True,
            description="Automatically adjust scale magnitude",
            )
    size = FloatProperty(
            name="Empty Size",
            default=.03,
            description="The size of each empty",
            min=0.0001, max=1000000.0,
            soft_min=0.001, soft_max=100.0,
            )
    x_ray = BoolProperty(
            name="Use X-Ray",
            default=True,
            description="Show the empties over other objects",
            )
    frame_skip = IntProperty(
            name="Fps divisor",
            default=4,
            # usually the sample rate is 120, so the default 4 gives you 30fps
            description="Frame supersampling factor",
            min=1,
            )
    use_frame_no = BoolProperty(
            name="Use frame numbers",
            default=False,
            description="Offset start of animation according to the source",
            )
    show_names = BoolProperty(
            name="Show Names", default=False,
            description="Show the markers' name",
            )
    prefix = StringProperty(
            name="Name Prefix", maxlen=32,
            description="Prefix object names with this",
            )
    use_existing = BoolProperty(
            name="Use existing empties",
            default=False,
            description="Use previously created homonymous empties",
            )
    confidence = FloatProperty(
            name="Minimum Confidence Level", default=0,
            description="Only consider markers with at least "
                        "this confidence level",
            min=-1., max=1000000.0,
            soft_min=-1., soft_max=100.0,
            )

    filter_glob = StringProperty(default="*.c3d;*.csv", options={'HIDDEN'})

    def find_height(self, ms):
        """
            Heuristic to find the height of the subject in the markerset
            (only works for standing poses)
        """
        zmin = None
        hidx = 1 if self.properties.Y_up else 2
        for ml in ms.markerLabels:
            if 'LTOE' in ml:
                hd = ml.replace('LTOE', 'LFHD')
                if hd not in ms.markerLabels:
                    break
                pmin_idx = ms.markerLabels.index(ml)
                pmax_idx = ms.markerLabels.index(hd)
                zmin = ms.frames[0][pmin_idx].position[hidx]
                zmax = ms.frames[0][pmax_idx].position[hidx]
        if zmin is None:  # could not find named markers, get extremes
            allz = [m.position[hidx] for m in ms.frames[0]]
            zmin, zmax = min(allz), max(allz)
        return abs(zmax - zmin) or 1

    def adjust_scale_magnitude(self, height, scale):
        mag = math.log10(height * scale)
        #print('mag',mag, 'scale',scale)
        return scale * math.pow(10, -int(mag))

    def adjust_scale(self, height, scale):
        factor = height * scale / 1.75  # normalize
        if factor < 0.5:
            scale /= 10.0
            factor *= 10.0
        cmu_factors = [(1.0, 1.0), (1.1, 1.45), (1.6, 1.6), (2.54, 2.54)]
        sqerr, fix = min(((cf[0] - factor) ** 2.0, 1.0 / cf[1])
            for cf in cmu_factors)
        #print('height * scale: {:.2f}'.format(height * scale))
        #print(factor, fix)
        return scale * fix

    def execute(self, context):
        s = self.properties.size
        empty_size = (s, s, s)
        ms = import_c3d.read(self.properties.filepath, onlyHeader=True)
        ms.readNextFrameData()
        #print(ms.fileName)

        # determine the final scale
        height = self.find_height(ms)
        #print('h', height)
        scale = 1.0 if not self.properties.from_inches else 0.0254
        scale *= ms.scale
        if self.properties.auto_magnitude:
            scale = self.adjust_scale_magnitude(height, scale)
            #print('scale',scale)
        if self.properties.auto_scale:
            scale = self.adjust_scale(height, scale)
        scale *= self.properties.scale

        # create the empties and get their collision-free names
        unames = {}
        use_existing = self.properties.use_existing
        for ml in ms.markerLabels:
            name = self.properties.prefix + ml
            if use_existing and name in bpy.context.scene.objects:
                o = bpy.context.scene.objects[name]
            else:
                bpy.ops.object.add()
                o = bpy.context.active_object
                o.name = name
            unames[name] = o.name
            bpy.ops.transform.resize(value=empty_size)
            o.show_name = self.properties.show_names
            o.show_x_ray = self.properties.x_ray
        for name in unames.values():
            bpy.context.scene.objects[name].select = True

        # start animating the empties
        C3DAnimateCloud.markerset = ms
        C3DAnimateCloud.unames = unames
        C3DAnimateCloud.scale = scale
        C3DAnimateCloud.Y_up = self.properties.Y_up
        C3DAnimateCloud.fskip = self.properties.frame_skip
        C3DAnimateCloud.prefix = self.properties.prefix
        C3DAnimateCloud.use_frame_no = self.properties.use_frame_no
        C3DAnimateCloud.confidence = self.properties.confidence
        C3DAnimateCloud.curframe = ms.startFrame
        bpy.ops.import_anim.c3danim()
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_func(self, context):
    self.layout.operator(C3DImporter.bl_idname,
                         text="Graphics Lab Motion Capture (.c3d)")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_file_import.append(menu_func)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_file_import.remove(menu_func)


if __name__ == "__main__":
    register()
