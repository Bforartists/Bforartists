# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Export Camera Animation",
    "author": "Campbell Barton",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "File > Export > Cameras & Markers (.py)",
    "description": "Export Cameras & Markers (.py)",
    "warning": "",
    "doc_url": "{BLENDER_MANUAL_URL}/addons/import_export/anim_camera.html",
    "support": 'OFFICIAL',
    "category": "Import-Export",
}


import bpy


def write_cameras(context, fh, frame_start, frame_end, only_selected=False):

    data_attrs = (
        "lens",
        "shift_x",
        "shift_y",
        "dof.focus_distance",
        "clip_start",
        "clip_end",
        "display_size",
    )

    obj_attrs = (
        "hide_render",
    )

    fw = fh.write

    scene = bpy.context.scene

    cameras = []

    for obj in scene.objects:
        if only_selected and not obj.select_get():
            continue
        if obj.type != 'CAMERA':
            continue

        cameras.append((obj, obj.data))

    frame_range = range(frame_start, frame_end + 1)

    fw("import bpy\n"
       "cameras = {}\n"
       "scene = bpy.context.scene\n"
       "frame = scene.frame_current - 1\n"
       "\n")

    for obj, obj_data in cameras:
        fw("data = bpy.data.cameras.new(%r)\n" % obj.name)
        for attr in data_attrs:
            fw("data.%s = %s\n" % (attr, repr(obj_data.path_resolve(attr))))

        fw("obj = bpy.data.objects.new(%r, data)\n" % obj.name)

        for attr in obj_attrs:
            fw("obj.%s = %s\n" % (attr, repr(getattr(obj, attr))))

        fw("bpy.context.collection.objects.link(obj)\n")
        fw("cameras[%r] = obj\n" % obj.name)
        fw("\n")

    for f in frame_range:
        scene.frame_set(f)
        fw("# new frame\n")
        fw("scene.frame_set(%d + frame)\n" % f)

        for obj, obj_data in cameras:
            fw("obj = cameras[%r]\n" % obj.name)

            matrix = obj.matrix_world.copy()
            fw("obj.location = %r, %r, %r\n" % matrix.to_translation()[:])
            fw("obj.scale = %r, %r, %r\n" % matrix.to_scale()[:])
            fw("obj.rotation_euler = %r, %r, %r\n" % matrix.to_euler()[:])

            fw("obj.keyframe_insert(\"location\")\n")
            fw("obj.keyframe_insert(\"scale\")\n")
            fw("obj.keyframe_insert(\"rotation_euler\")\n")

            # only key the angle
            fw("data = obj.data\n")
            fw("data.lens = %s\n" % obj_data.lens)
            fw("data.keyframe_insert(\"lens\")\n")

            fw("\n")

    # now markers
    fw("# markers\n")
    for marker in scene.timeline_markers:
        fw("marker = scene.timeline_markers.new(%r)\n" % marker.name)
        fw("marker.frame = %d + frame\n" % marker.frame)

        # will fail if the cameras not selected
        if marker.camera:
            fw("marker.camera = cameras.get(%r)\n" % marker.camera.name)
        fw("\n")


from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy_extras.io_utils import ExportHelper


class CameraExporter(bpy.types.Operator, ExportHelper):
    """Save a python script which re-creates cameras and markers elsewhere"""
    bl_idname = "export_animation.cameras"
    bl_label = "Export Camera & Markers"

    filename_ext = ".py"
    filter_glob: StringProperty(default="*.py", options={'HIDDEN'})

    frame_start: IntProperty(name="Start Frame",
            description="Start frame for export",
            default=1, min=1, max=300000)
    frame_end: IntProperty(name="End Frame",
            description="End frame for export",
            default=250, min=1, max=300000)
    only_selected: BoolProperty(name="Only Selected",
            default=True)

    def execute(self, context):
        with open(self.filepath, 'w', encoding='utf-8') as fh:
            write_cameras(context, fh, self.frame_start, self.frame_end, self.only_selected)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.frame_start = context.scene.frame_start
        self.frame_end = context.scene.frame_end

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}


def menu_export(self, context):
    import os
    default_path = os.path.splitext(bpy.data.filepath)[0] + ".py"
    self.layout.operator(CameraExporter.bl_idname, text="Cameras & Markers (.py)").filepath = default_path


def register():
    bpy.utils.register_class(CameraExporter)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)


def unregister():
    bpy.utils.unregister_class(CameraExporter)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
