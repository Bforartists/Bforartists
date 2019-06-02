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


if "bpy" in locals():
    from importlib import reload

    paths = reload(paths)
    utils = reload(utils)
    bg_blender = reload(bg_blender)
else:
    from blenderkit import paths, utils, bg_blender

import tempfile, os, subprocess, json, sys

import bpy

BLENDERKIT_EXPORT_DATA_FILE = "data.json"

ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
HIGH_PRIORITY_CLASS = 0x00000080
IDLE_PRIORITY_CLASS = 0x00000040
NORMAL_PRIORITY_CLASS = 0x00000020
REALTIME_PRIORITY_CLASS = 0x00000100


def check_thumbnail(props, imgpath):
    img = utils.get_hidden_image(imgpath, 'upload_preview', force_reload=True)
    if img is not None:  # and img.size[0] == img.size[1] and img.size[0] >= 512 and (
        # img.file_format == 'JPEG' or img.file_format == 'PNG'):
        props.has_thumbnail = True
        props.thumbnail_generating_state = ''
        return
    else:
        props.has_thumbnail = False
    output = ''
    if img is None or img.size[0] == 0 or img.filepath.find('thumbnail_notready.jpg') > -1:
        output += 'No thumbnail or wrong file path\n'
    else:
        pass;
        # this is causing problems on some platforms, don't know why..
        # if img.size[0] != img.size[1]:
        #     output += 'image not a square\n'
        # if img.size[0] < 512:
        #     output += 'image too small, should be at least 512x512\n'
        # if img.file_format != 'JPEG' or img.file_format != 'PNG':
        #     output += 'image has to be a jpeg or png'
    props.thumbnail_generating_state = output


def update_upload_model_preview(self, context):
    ob = utils.get_active_model()
    if ob is not None:
        props = ob.blenderkit
        imgpath = props.thumbnail
        check_thumbnail(props, imgpath)


def update_upload_scene_preview(self, context):
    s = bpy.context.scene
    props = s.blenderkit
    imgpath = props.thumbnail
    check_thumbnail(props, imgpath)


def update_upload_material_preview(self, context):
    if hasattr(bpy.context, 'active_object') \
            and bpy.context.active_object is not None \
            and bpy.context.active_object.active_material is not None:
        mat = bpy.context.active_object.active_material
        props = mat.blenderkit
        imgpath = props.thumbnail
        check_thumbnail(props, imgpath)


def update_upload_brush_preview(self, context):
    brush = utils.get_active_brush()
    if brush is not None:
        props = brush.blenderkit
        imgpath = bpy.path.abspath(brush.icon_filepath)
        check_thumbnail(props, imgpath)


def start_thumbnailer(self, context):
    # Prepare to save the file
    mainmodel = utils.get_active_model()
    mainmodel.blenderkit.is_generating_thumbnail = True
    mainmodel.blenderkit.thumbnail_generating_state = 'starting blender instance'

    binary_path = bpy.app.binary_path
    script_path = os.path.dirname(os.path.realpath(__file__))
    basename, ext = os.path.splitext(bpy.data.filepath)
    if not basename:
        basename = os.path.join(basename, "temp")
    if not ext:
        ext = ".blend"
    asset_name = mainmodel.blenderkit.name
    tempdir = tempfile.mkdtemp()

    file_dir = os.path.dirname(bpy.data.filepath)
    thumb_path = os.path.join(file_dir, asset_name)
    rel_thumb_path = os.path.join('//', asset_name)

    i = 0
    while os.path.isfile(thumb_path + '.jpg'):
        thumb_path = os.path.join(file_dir, asset_name + '_' + str(i).zfill(4))
        rel_thumb_path = os.path.join('//', asset_name + '_' + str(i).zfill(4))
        i += 1

    filepath = os.path.join(tempdir, "thumbnailer_blenderkit" + ext)
    tfpath = paths.get_thumbnailer_filepath()
    datafile = os.path.join(tempdir, BLENDERKIT_EXPORT_DATA_FILE)
    try:
        # save a copy of actual scene but don't interfere with the users models
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=False, copy=True)

        obs = utils.get_hierarchy(mainmodel)
        obnames = []
        for ob in obs:
            obnames.append(ob.name)
        with open(datafile, 'w') as s:
            bkit = mainmodel.blenderkit
            json.dump({
                "type": "model",
                "models": str(obnames),
                "thumbnail_angle": bkit.thumbnail_angle,
                "thumbnail_snap_to": bkit.thumbnail_snap_to,
                "thumbnail_background_lightness": bkit.thumbnail_background_lightness,
                "thumbnail_samples": bkit.thumbnail_samples,
                "thumbnail_denoising": bkit.thumbnail_denoising,
            }, s)

        flags = BELOW_NORMAL_PRIORITY_CLASS
        if sys.platform != 'win32':  # TODO test this on windows and find out how to change process priority on linux
            # without psutil - we don't want any more libs in the addon
            flags = 0

        proc = subprocess.Popen([
            binary_path,
            "--background",
            "-noaudio",
            tfpath,
            "--python", os.path.join(script_path, "autothumb_model_bg.py"),
            "--", datafile, filepath, thumb_path, tempdir
        ], bufsize=1, stdout=subprocess.PIPE, stdin=subprocess.PIPE, creationflags=flags)

        eval_path_computing = "bpy.data.objects['%s'].blenderkit.is_generating_thumbnail" % mainmodel.name
        eval_path_state = "bpy.data.objects['%s'].blenderkit.thumbnail_generating_state" % mainmodel.name
        eval_path = "bpy.data.objects['%s']" % mainmodel.name

        bg_blender.add_bg_process(eval_path_computing=eval_path_computing, eval_path_state=eval_path_state,
                                  eval_path=eval_path, process_type='THUMBNAILER', process=proc)

        mainmodel.blenderkit.thumbnail = rel_thumb_path + '.jpg'
        mainmodel.blenderkit.thumbnail_generating_state = 'Saving .blend file'

    except Exception as e:
        self.report({'WARNING'}, "Error while exporting file: %s" % str(e))
        return {'FINISHED'}


def start_material_thumbnailer(self, context):
    # Prepare to save the file
    mat = bpy.context.active_object.active_material
    mat.blenderkit.is_generating_thumbnail = True
    mat.blenderkit.thumbnail_generating_state = 'starting blender instance'

    binary_path = bpy.app.binary_path
    script_path = os.path.dirname(os.path.realpath(__file__))
    basename, ext = os.path.splitext(bpy.data.filepath)
    if not basename:
        basename = os.path.join(basename, "temp")
    if not ext:
        ext = ".blend"
    asset_name = mat.name
    tempdir = tempfile.mkdtemp()

    file_dir = os.path.dirname(bpy.data.filepath)

    thumb_path = os.path.join(file_dir, asset_name)
    rel_thumb_path = os.path.join('//', mat.name)
    i = 0
    while os.path.isfile(thumb_path + '.png'):
        thumb_path = os.path.join(file_dir, mat.name + '_' + str(i).zfill(4))
        rel_thumb_path = os.path.join('//', mat.name + '_' + str(i).zfill(4))
        i += 1

    filepath = os.path.join(tempdir, "material_thumbnailer_cycles" + ext)
    tfpath = paths.get_material_thumbnailer_filepath()
    datafile = os.path.join(tempdir, BLENDERKIT_EXPORT_DATA_FILE)
    try:
        # save a copy of actual scene but don't interfere with the users models
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=False, copy=True)

        with open(datafile, 'w') as s:
            bkit = mat.blenderkit
            json.dump({
                "type": "material",
                "material": mat.name,
                "thumbnail_type": bkit.thumbnail_generator_type,
                "thumbnail_scale": bkit.thumbnail_scale,
                "thumbnail_background": bkit.thumbnail_background,
                "thumbnail_background_lightness": bkit.thumbnail_background_lightness,
                "thumbnail_samples": bkit.thumbnail_samples,
                "thumbnail_denoising": bkit.thumbnail_denoising,
                "adaptive_subdivision": bkit.adaptive_subdivision,
                "texture_size_meters": bkit.texture_size_meters,
            }, s)

        flags = BELOW_NORMAL_PRIORITY_CLASS
        if sys.platform != 'win32':  # TODO test this on windows
            flags = 0

        proc = subprocess.Popen([
            binary_path,
            "--background",
            "-noaudio",
            tfpath,
            "--python", os.path.join(script_path, "autothumb_material_bg.py"),
            "--", datafile, filepath, thumb_path, tempdir
        ], bufsize=1, stdout=subprocess.PIPE, stdin=subprocess.PIPE, creationflags=flags)

        eval_path_computing = "bpy.data.materials['%s'].blenderkit.is_generating_thumbnail" % mat.name
        eval_path_state = "bpy.data.materials['%s'].blenderkit.thumbnail_generating_state" % mat.name
        eval_path = "bpy.data.materials['%s']" % mat.name

        bg_blender.add_bg_process(eval_path_computing=eval_path_computing, eval_path_state=eval_path_state,
                                  eval_path=eval_path, process_type='THUMBNAILER', process=proc)

        mat.blenderkit.thumbnail = rel_thumb_path + '.png'
        mat.blenderkit.thumbnail_generating_state = 'Saving .blend file'
    except Exception as e:
        self.report({'WARNING'}, "Error while packing file: %s" % str(e))
        return {'FINISHED'}


class GenerateThumbnailOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.blenderkit_generate_thumbnail"
    bl_label = "BlenderKit Thumbnail Generator"

    @classmethod
    def poll(cls, context):
        return bpy.context.active_object is not None

    def draw(self, context):
        ob = bpy.context.active_object
        while ob.parent is not None:
            ob = ob.parent
        props = ob.blenderkit
        layout = self.layout
        layout.label(text='thumbnailer settings')
        layout.prop(props, 'thumbnail_background_lightness')
        layout.prop(props, 'thumbnail_angle')
        layout.prop(props, 'thumbnail_snap_to')
        layout.prop(props, 'thumbnail_samples')
        layout.prop(props, 'thumbnail_denoising')

    def execute(self, context):
        start_thumbnailer(self, context)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class GenerateMaterialThumbnailOperator(bpy.types.Operator):
    """Tooltip"""
    bl_idname = "object.blenderkit_material_thumbnail"
    bl_label = "BlenderKit Material Thumbnail Generator"

    @classmethod
    def poll(cls, context):
        return bpy.context.active_object is not None

    def check(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        props = bpy.context.active_object.active_material.blenderkit
        layout.prop(props, 'thumbnail_generator_type')
        layout.prop(props, 'thumbnail_scale')
        layout.prop(props, 'thumbnail_background')
        if props.thumbnail_background:
            layout.prop(props, 'thumbnail_background_lightness')
        layout.prop(props, 'thumbnail_samples')
        layout.prop(props, 'thumbnail_denoising')
        layout.prop(props, 'adaptive_subdivision')

    def execute(self, context):
        start_material_thumbnailer(self, context)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register_thumbnailer():
    bpy.utils.register_class(GenerateThumbnailOperator)
    bpy.utils.register_class(GenerateMaterialThumbnailOperator)


def unregister_thumbnailer():
    bpy.utils.unregister_class(GenerateThumbnailOperator)
    bpy.utils.unregister_class(GenerateMaterialThumbnailOperator)
