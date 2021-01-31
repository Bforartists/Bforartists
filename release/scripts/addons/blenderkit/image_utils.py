import bpy
import numpy
import os

def get_orig_render_settings():
    rs = bpy.context.scene.render
    ims = rs.image_settings

    vs = bpy.context.scene.view_settings

    orig_settings = {
        'file_format': ims.file_format,
        'quality': ims.quality,
        'color_mode': ims.color_mode,
        'compression': ims.compression,
        'exr_codec': ims.exr_codec,
        'view_transform': vs.view_transform
    }
    return orig_settings


def set_orig_render_settings(orig_settings):
    rs = bpy.context.scene.render
    ims = rs.image_settings
    vs = bpy.context.scene.view_settings

    ims.file_format = orig_settings['file_format']
    ims.quality = orig_settings['quality']
    ims.color_mode = orig_settings['color_mode']
    ims.compression = orig_settings['compression']
    ims.exr_codec = orig_settings['exr_codec']

    vs.view_transform = orig_settings['view_transform']


def img_save_as(img, filepath='//', file_format='JPEG', quality=90, color_mode='RGB', compression=15, view_transform = 'Raw', exr_codec = 'DWAA'):
    '''Uses Blender 'save render' to save images - BLender isn't really able so save images with other methods correctly.'''

    ors = get_orig_render_settings()

    rs = bpy.context.scene.render
    vs = bpy.context.scene.view_settings

    ims = rs.image_settings
    ims.file_format = file_format
    ims.quality = quality
    ims.color_mode = color_mode
    ims.compression = compression
    ims.exr_codec = exr_codec
    vs.view_transform = view_transform


    img.save_render(filepath=bpy.path.abspath(filepath), scene=bpy.context.scene)

    set_orig_render_settings(ors)


def generate_hdr_thumbnail():
    scene = bpy.context.scene
    ui_props = scene.blenderkitUI
    hdr_image = ui_props.hdr_upload_image#bpy.data.images.get(ui_props.hdr_upload_image)

    base, ext = os.path.splitext(hdr_image.filepath)
    thumb_path = base + '.jpg'
    thumb_name = os.path.basename(thumb_path)

    max_thumbnail_size = 2048
    size = hdr_image.size
    ratio = size[0] / size[1]

    imageWidth = size[0]
    imageHeight = size[1]
    thumbnailWidth = min(size[0], max_thumbnail_size)
    thumbnailHeight = min(size[1], int(max_thumbnail_size / ratio))

    tempBuffer = numpy.empty(imageWidth * imageHeight * 4, dtype=numpy.float32)
    inew = bpy.data.images.new(thumb_name, imageWidth, imageHeight, alpha=False, float_buffer=False)

    hdr_image.pixels.foreach_get(tempBuffer)

    inew.filepath = thumb_path
    inew.colorspace_settings.name = 'Linear'
    inew.pixels.foreach_set(tempBuffer)

    bpy.context.view_layer.update()
    if thumbnailWidth < imageWidth:
        inew.scale(thumbnailWidth, thumbnailHeight)

    img_save_as(inew, filepath=inew.filepath)
