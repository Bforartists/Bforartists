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

from blenderkit import paths, utils, bg_blender, ui_panels, icons, tasks_queue, download

import tempfile, os, subprocess, json, sys

import bpy
from bpy.props import (
    FloatProperty,
    IntProperty,
    EnumProperty,
    BoolProperty,
    StringProperty,
)

BLENDERKIT_EXPORT_DATA_FILE = "data.json"

thumbnail_resolutions = (
    ('256', '256', ''),
    ('512', '512', ''),
    ('1024', '1024 - minimum for public', ''),
    ('2048', '2048', ''),
)

thumbnail_angles = (
    ('DEFAULT', 'default', ''),
    ('FRONT', 'front', ''),
    ('SIDE', 'side', ''),
    ('TOP', 'top', ''),
)

thumbnail_snap = (
    ('GROUND', 'ground', ''),
    ('WALL', 'wall', ''),
    ('CEILING', 'ceiling', ''),
    ('FLOAT', 'floating', ''),
)


def get_texture_ui(tpath, iname):
    tex = bpy.data.textures.get(iname)

    if tpath.startswith('//'):
        tpath = bpy.path.abspath(tpath)

    if not tex or not tex.image or not tex.image.filepath == tpath:
        tasks_queue.add_task((utils.get_hidden_image, (tpath, iname)), only_last=True)
        tasks_queue.add_task((utils.get_hidden_texture, (iname,)), only_last=True)
        return None
    return tex


def check_thumbnail(props, imgpath):
    img = utils.get_hidden_image(imgpath, 'upload_preview', force_reload=True)
    # print(' check thumbnail ', img)
    if img is not None:  # and img.size[0] == img.size[1] and img.size[0] >= 512 and (
        # img.file_format == 'JPEG' or img.file_format == 'PNG'):
        props.has_thumbnail = True
        props.thumbnail_generating_state = ''

        tex = utils.get_hidden_texture(img.name)
        # pcoll = icons.icon_collections["previews"]
        # pcoll.load(img.name, img.filepath, 'IMAGE')

        return img
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
        img = check_thumbnail(props, imgpath)


def update_upload_scene_preview(self, context):
    s = bpy.context.scene
    props = s.blenderkit
    imgpath = props.thumbnail
    check_thumbnail(props, imgpath)


def update_upload_material_preview(self, context):
    if hasattr(bpy.context, 'active_object') \
            and bpy.context.view_layer.objects.active is not None \
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


def start_thumbnailer(self=None, json_args=None, props=None, wait=False, add_bg_process=True):
    # Prepare to save the file

    binary_path = bpy.app.binary_path
    script_path = os.path.dirname(os.path.realpath(__file__))

    ext = '.blend'

    tfpath = paths.get_thumbnailer_filepath()
    datafile = os.path.join(json_args['tempdir'], BLENDERKIT_EXPORT_DATA_FILE)
    try:
        with open(datafile, 'w', encoding='utf-8') as s:
            json.dump(json_args, s, ensure_ascii=False, indent=4)

        proc = subprocess.Popen([
            binary_path,
            "--background",
            "-noaudio",
            tfpath,
            "--python", os.path.join(script_path, "autothumb_model_bg.py"),
            "--", datafile,
        ], bufsize=1, stdout=subprocess.PIPE, stdin=subprocess.PIPE, creationflags=utils.get_process_flags())

        eval_path_computing = "bpy.data.objects['%s'].blenderkit.is_generating_thumbnail" % json_args['asset_name']
        eval_path_state = "bpy.data.objects['%s'].blenderkit.thumbnail_generating_state" % json_args['asset_name']
        eval_path = "bpy.data.objects['%s']" % json_args['asset_name']

        bg_blender.add_bg_process(name = f"{json_args['asset_name']} thumbnailer" ,eval_path_computing=eval_path_computing, eval_path_state=eval_path_state,
                                  eval_path=eval_path, process_type='THUMBNAILER', process=proc)


    except Exception as e:
        self.report({'WARNING'}, "Error while exporting file: %s" % str(e))
        return {'FINISHED'}


def start_material_thumbnailer(self=None, json_args=None, props=None, wait=False, add_bg_process=True):
    '''

    Parameters
    ----------
    self
    json_args - all arguments:
    props - blenderkit upload props with thumbnail settings, to communicate back, if not present, not used.
    wait - wait for the rendering to finish

    Returns
    -------

    '''
    if props:
        props.is_generating_thumbnail = True
        props.thumbnail_generating_state = 'starting blender instance'

    binary_path = bpy.app.binary_path
    script_path = os.path.dirname(os.path.realpath(__file__))

    tfpath = paths.get_material_thumbnailer_filepath()
    datafile = os.path.join(json_args['tempdir'], BLENDERKIT_EXPORT_DATA_FILE)

    try:
        with open(datafile, 'w', encoding='utf-8') as s:
            json.dump(json_args, s, ensure_ascii=False, indent=4)

        proc = subprocess.Popen([
            binary_path,
            "--background",
            "-noaudio",
            tfpath,
            "--python", os.path.join(script_path, "autothumb_material_bg.py"),
            "--", datafile,
        ], bufsize=1, stdout=subprocess.PIPE, stdin=subprocess.PIPE, creationflags=utils.get_process_flags())

        eval_path_computing = "bpy.data.materials['%s'].blenderkit.is_generating_thumbnail" % json_args['asset_name']
        eval_path_state = "bpy.data.materials['%s'].blenderkit.thumbnail_generating_state" % json_args['asset_name']
        eval_path = "bpy.data.materials['%s']" % json_args['asset_name']

        bg_blender.add_bg_process(name=f"{json_args['asset_name']} thumbnailer", eval_path_computing=eval_path_computing,
                                  eval_path_state=eval_path_state,
                                  eval_path=eval_path, process_type='THUMBNAILER', process=proc)
        if props:
            props.thumbnail_generating_state = 'Saving .blend file'

        if wait:
            while proc.poll() is None:
                stdout_data, stderr_data = proc.communicate()
                print(stdout_data)
    except Exception as e:
        if self:
            self.report({'WARNING'}, "Error while packing file: %s" % str(e))
        else:
            print(e)
        return {'FINISHED'}


class GenerateThumbnailOperator(bpy.types.Operator):
    """Generate Cycles thumbnail for model assets"""
    bl_idname = "object.blenderkit_generate_thumbnail"
    bl_label = "BlenderKit Thumbnail Generator"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bpy.context.view_layer.objects.active is not None

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
        layout.prop(props, 'thumbnail_resolution')
        layout.prop(props, 'thumbnail_denoising')
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        layout.prop(preferences, "thumbnail_use_gpu")

    def execute(self, context):
        asset = utils.get_active_model()
        asset.blenderkit.is_generating_thumbnail = True
        asset.blenderkit.thumbnail_generating_state = 'starting blender instance'

        tempdir = tempfile.mkdtemp()
        ext = '.blend'
        filepath = os.path.join(tempdir, "thumbnailer_blenderkit" + ext)

        path_can_be_relative = True
        file_dir = os.path.dirname(bpy.data.filepath)
        if file_dir == '':
            file_dir = tempdir
            path_can_be_relative = False

        an_slug = paths.slugify(asset.name)
        thumb_path = os.path.join(file_dir, an_slug)
        if path_can_be_relative:
            rel_thumb_path = os.path.join('//', an_slug)
        else:
            rel_thumb_path = thumb_path


        i = 0
        while os.path.isfile(thumb_path + '.jpg'):
            thumb_path = os.path.join(file_dir, an_slug + '_' + str(i).zfill(4))
            rel_thumb_path = os.path.join('//', an_slug + '_' + str(i).zfill(4))
            i += 1
        bkit = asset.blenderkit

        bkit.thumbnail = rel_thumb_path + '.jpg'
        bkit.thumbnail_generating_state = 'Saving .blend file'

        # save a copy of actual scene but don't interfere with the users models
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=False, copy=True)
        # get all included objects
        obs = utils.get_hierarchy(asset)
        obnames = []
        for ob in obs:
            obnames.append(ob.name)

        args_dict = {
            "type": "material",
            "asset_name": asset.name,
            "filepath": filepath,
            "thumbnail_path": thumb_path,
            "tempdir": tempdir,
        }
        thumbnail_args = {
            "type": "model",
            "models": str(obnames),
            "thumbnail_angle": bkit.thumbnail_angle,
            "thumbnail_snap_to": bkit.thumbnail_snap_to,
            "thumbnail_background_lightness": bkit.thumbnail_background_lightness,
            "thumbnail_resolution": bkit.thumbnail_resolution,
            "thumbnail_samples": bkit.thumbnail_samples,
            "thumbnail_denoising": bkit.thumbnail_denoising,
        }
        args_dict.update(thumbnail_args)

        start_thumbnailer(self,
                          json_args=args_dict,
                          props=asset.blenderkit, wait=False)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        # if bpy.data.filepath == '':
        #     ui_panels.ui_message(
        #         title="Can't render thumbnail",
        #         message="please save your file first")
        #
        #     return {'FINISHED'}

        return wm.invoke_props_dialog(self)


class ReGenerateThumbnailOperator(bpy.types.Operator):
    """
        Generate default thumbnail with Cycles renderer and upload it.
        Works also for assets from search results, without being downloaded before.
    """
    bl_idname = "object.blenderkit_regenerate_thumbnail"
    bl_label = "BlenderKit Thumbnail Re-generate"
    bl_options = {'REGISTER', 'INTERNAL'}

    asset_index: IntProperty(name="Asset Index", description='asset index in search results', default=-1)

    thumbnail_background_lightness: FloatProperty(name="Thumbnail Background Lightness",
                                                  description="set to make your material stand out", default=1.0,
                                                  min=0.01, max=10)

    thumbnail_angle: EnumProperty(
        name='Thumbnail Angle',
        items=thumbnail_angles,
        default='DEFAULT',
        description='thumbnailer angle',
    )

    thumbnail_snap_to: EnumProperty(
        name='Model Snaps To:',
        items=thumbnail_snap,
        default='GROUND',
        description='typical placing of the interior. Leave on ground for most objects that respect gravity :)',
    )

    thumbnail_resolution: EnumProperty(
        name="Resolution",
        items=thumbnail_resolutions,
        description="Thumbnail resolution",
        default="1024",
    )

    thumbnail_samples: IntProperty(name="Cycles Samples",
                                   description="cycles samples setting", default=100,
                                   min=5, max=5000)
    thumbnail_denoising: BoolProperty(name="Use Denoising",
                                      description="Use denoising", default=True)

    @classmethod
    def poll(cls, context):
        return True  # bpy.context.view_layer.objects.active is not None

    def draw(self, context):
        props = self
        layout = self.layout
        # layout.label('This will re-generate thumbnail and directly upload it to server. You should see your updated thumbnail online depending ')
        layout.label(text='thumbnailer settings')
        layout.prop(props, 'thumbnail_background_lightness')
        layout.prop(props, 'thumbnail_angle')
        layout.prop(props, 'thumbnail_snap_to')
        layout.prop(props, 'thumbnail_samples')
        layout.prop(props, 'thumbnail_resolution')
        layout.prop(props, 'thumbnail_denoising')
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        layout.prop(preferences, "thumbnail_use_gpu")

    def execute(self, context):
        if not self.asset_index > -1:
            return {'CANCELLED'}

        # either get the data from search results
        sr = bpy.context.window_manager['search results']
        asset_data = sr[self.asset_index].to_dict()

        tempdir = tempfile.mkdtemp()

        an_slug = paths.slugify(asset_data['name'])
        thumb_path = os.path.join(tempdir, an_slug)


        args_dict = {
            "type": "material",
            "asset_name": asset_data['name'],
            "asset_data": asset_data,
            # "filepath": filepath,
            "thumbnail_path": thumb_path,
            "tempdir": tempdir,
            "do_download": True,
            "upload_after_render": True,
        }
        thumbnail_args = {
            "type": "model",
            "thumbnail_angle": self.thumbnail_angle,
            "thumbnail_snap_to": self.thumbnail_snap_to,
            "thumbnail_background_lightness": self.thumbnail_background_lightness,
            "thumbnail_resolution": self.thumbnail_resolution,
            "thumbnail_samples": self.thumbnail_samples,
            "thumbnail_denoising": self.thumbnail_denoising,
        }
        args_dict.update(thumbnail_args)

        start_thumbnailer(self,
                          json_args=args_dict,
                          wait=False)
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        # if bpy.data.filepath == '':
        #     ui_panels.ui_message(
        #         title="Can't render thumbnail",
        #         message="please save your file first")
        #
        #     return {'FINISHED'}

        return wm.invoke_props_dialog(self)


class GenerateMaterialThumbnailOperator(bpy.types.Operator):
    """Generate default thumbnail with Cycles renderer."""
    bl_idname = "object.blenderkit_generate_material_thumbnail"
    bl_label = "BlenderKit Material Thumbnail Generator"
    bl_options = {'REGISTER', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return bpy.context.view_layer.objects.active is not None

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
        layout.prop(props, 'thumbnail_resolution')
        layout.prop(props, 'thumbnail_samples')
        layout.prop(props, 'thumbnail_denoising')
        layout.prop(props, 'adaptive_subdivision')
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        layout.prop(preferences, "thumbnail_use_gpu")

    def execute(self, context):
        asset = bpy.context.active_object.active_material
        tempdir = tempfile.mkdtemp()
        filepath = os.path.join(tempdir, "material_thumbnailer_cycles.blend")
        # save a copy of actual scene but don't interfere with the users models
        bpy.ops.wm.save_as_mainfile(filepath=filepath, compress=False, copy=True)

        thumb_dir = os.path.dirname(bpy.data.filepath)
        thumb_path = os.path.join(thumb_dir, asset.name)
        rel_thumb_path = os.path.join('//', asset.name)
        # auto increase number of the generated thumbnail.
        i = 0
        while os.path.isfile(thumb_path + '.png'):
            thumb_path = os.path.join(thumb_dir, asset.name + '_' + str(i).zfill(4))
            rel_thumb_path = os.path.join('//', asset.name + '_' + str(i).zfill(4))
            i += 1

        asset.blenderkit.thumbnail = rel_thumb_path + '.png'
        bkit = asset.blenderkit

        args_dict = {
            "type": "material",
            "asset_name": asset.name,
            "filepath": filepath,
            "thumbnail_path": thumb_path,
            "tempdir": tempdir,
        }

        thumbnail_args = {
            "thumbnail_type": bkit.thumbnail_generator_type,
            "thumbnail_scale": bkit.thumbnail_scale,
            "thumbnail_background": bkit.thumbnail_background,
            "thumbnail_background_lightness": bkit.thumbnail_background_lightness,
            "thumbnail_resolution": bkit.thumbnail_resolution,
            "thumbnail_samples": bkit.thumbnail_samples,
            "thumbnail_denoising": bkit.thumbnail_denoising,
            "adaptive_subdivision": bkit.adaptive_subdivision,
            "texture_size_meters": bkit.texture_size_meters,
        }
        args_dict.update(thumbnail_args)
        start_material_thumbnailer(self,
                                   json_args=args_dict,
                                   props=asset.blenderkit, wait=False)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)


class ReGenerateMaterialThumbnailOperator(bpy.types.Operator):
    """
        Generate default thumbnail with Cycles renderer and upload it.
        Works also for assets from search results, without being downloaded before
    """
    bl_idname = "object.blenderkit_regenerate_material_thumbnail"
    bl_label = "BlenderKit Material Thumbnail Re-Generator"
    bl_options = {'REGISTER', 'INTERNAL'}

    asset_index: IntProperty(name="Asset Index", description='asset index in search results', default=-1)

    thumbnail_scale: FloatProperty(name="Thumbnail Object Size",
                                   description="Size of material preview object in meters."
                                               "Change for materials that look better at sizes different than 1m",
                                   default=1, min=0.00001, max=10)
    thumbnail_background: BoolProperty(name="Thumbnail Background (for Glass only)",
                                       description="For refractive materials, you might need a background.\n"
                                                   "Don't use for other types of materials.\n"
                                                   "Transparent background is preferred",
                                       default=False)
    thumbnail_background_lightness: FloatProperty(name="Thumbnail Background Lightness",
                                                  description="Set to make your material stand out with enough contrast",
                                                  default=.9,
                                                  min=0.00001, max=1)
    thumbnail_samples: IntProperty(name="Cycles Samples",
                                   description="Cycles samples", default=100,
                                   min=5, max=5000)
    thumbnail_denoising: BoolProperty(name="Use Denoising",
                                      description="Use denoising", default=True)
    adaptive_subdivision: BoolProperty(name="Adaptive Subdivide",
                                       description="Use adaptive displacement subdivision", default=False)

    thumbnail_resolution: EnumProperty(
        name="Resolution",
        items=thumbnail_resolutions,
        description="Thumbnail resolution",
        default="1024",
    )

    thumbnail_generator_type: EnumProperty(
        name="Thumbnail Style",
        items=(
            ('BALL', 'Ball', ""),
            ('BALL_COMPLEX', 'Ball complex', 'Complex ball to highlight edgewear or material thickness'),
            ('FLUID', 'Fluid', 'Fluid'),
            ('CLOTH', 'Cloth', 'Cloth'),
            ('HAIR', 'Hair', 'Hair  ')
        ),
        description="Style of asset",
        default="BALL",
    )

    @classmethod
    def poll(cls, context):
        return True  # bpy.context.view_layer.objects.active is not None

    def check(self, context):
        return True

    def draw(self, context):
        layout = self.layout
        props = self
        layout.prop(props, 'thumbnail_generator_type')
        layout.prop(props, 'thumbnail_scale')
        layout.prop(props, 'thumbnail_background')
        if props.thumbnail_background:
            layout.prop(props, 'thumbnail_background_lightness')
        layout.prop(props, 'thumbnail_resolution')
        layout.prop(props, 'thumbnail_samples')
        layout.prop(props, 'thumbnail_denoising')
        layout.prop(props, 'adaptive_subdivision')
        preferences = bpy.context.preferences.addons['blenderkit'].preferences
        layout.prop(preferences, "thumbnail_use_gpu")

    def execute(self, context):

        if not self.asset_index > -1:
            return {'CANCELLED'}

        # either get the data from search results
        sr = bpy.context.window_manager['search results']
        asset_data = sr[self.asset_index].to_dict()

        tempdir = tempfile.mkdtemp()

        thumb_path = os.path.join(tempdir, asset_data['name'])

        args_dict = {
            "type": "material",
            "asset_name": asset_data['name'],
            "asset_data": asset_data,
            "thumbnail_path": thumb_path,
            "tempdir": tempdir,
            "do_download": True,
            "upload_after_render": True,
        }
        thumbnail_args = {
            "thumbnail_type": self.thumbnail_generator_type,
            "thumbnail_scale": self.thumbnail_scale,
            "thumbnail_background": self.thumbnail_background,
            "thumbnail_background_lightness": self.thumbnail_background_lightness,
            "thumbnail_resolution": self.thumbnail_resolution,
            "thumbnail_samples": self.thumbnail_samples,
            "thumbnail_denoising": self.thumbnail_denoising,
            "adaptive_subdivision": self.adaptive_subdivision,
            "texture_size_meters": utils.get_param(asset_data, 'textureSizeMeters', 1.0),
        }
        args_dict.update(thumbnail_args)
        start_material_thumbnailer(self,
                                   json_args=args_dict,
                                   wait=False)

        return {'FINISHED'}

    def invoke(self, context, event):
        # scene = bpy.context.scene
        # ui_props = scene.blenderkitUI
        # if ui_props.active_index > -1:
        #     sr = bpy.context.window_manager['search results']
        #     self.asset_data = dict(sr[ui_props.active_index])
        # else:
        #
        #     active_asset = utils.get_active_asset_by_type(asset_type = self.asset_type)
        #     self.asset_data = active_asset.get('asset_data')

        wm = context.window_manager
        return wm.invoke_props_dialog(self)


def register_thumbnailer():
    bpy.utils.register_class(GenerateThumbnailOperator)
    bpy.utils.register_class(ReGenerateThumbnailOperator)
    bpy.utils.register_class(GenerateMaterialThumbnailOperator)
    bpy.utils.register_class(ReGenerateMaterialThumbnailOperator)


def unregister_thumbnailer():
    bpy.utils.unregister_class(GenerateThumbnailOperator)
    bpy.utils.unregister_class(ReGenerateThumbnailOperator)
    bpy.utils.unregister_class(GenerateMaterialThumbnailOperator)
    bpy.utils.unregister_class(ReGenerateMaterialThumbnailOperator)
