# SPDX-License-Identifier: GPL-2.0-or-later

__author__ = "Nutti <nutti.metro@gmail.com>"
__status__ = "production"
__version__ = "6.7"
__date__ = "22 Sep 2022"

import bpy
import blf


def check_version(major, minor, _):
    """
    Check blender version
    """

    if bpy.app.version[0] == major and bpy.app.version[1] == minor:
        return 0
    if bpy.app.version[0] > major:
        return 1
    if bpy.app.version[1] > minor:
        return 1
    return -1


def make_annotations(cls):
    if check_version(2, 80, 0) < 0:
        return cls

    # make annotation from attributes
    props = {k: v
             for k, v in cls.__dict__.items()
             if isinstance(v, getattr(bpy.props, '_PropertyDeferred', tuple))}
    if props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in props.items():
            annotations[k] = v
            delattr(cls, k)

    return cls


class ChangeRegionType:
    def __init__(self, *_, **kwargs):
        self.region_type = kwargs.get('region_type', False)

    def __call__(self, cls):
        if check_version(2, 80, 0) >= 0:
            return cls

        cls.bl_region_type = self.region_type

        return cls


def matmul(m1, m2):
    if check_version(2, 80, 0) < 0:
        return m1 * m2

    return m1 @ m2


def layout_split(layout, factor=0.0, align=False):
    if check_version(2, 80, 0) < 0:
        return layout.split(percentage=factor, align=align)

    return layout.split(factor=factor, align=align)


def get_user_preferences(context):
    if hasattr(context, "user_preferences"):
        return context.user_preferences

    return context.preferences


def get_object_select(obj):
    if check_version(2, 80, 0) < 0:
        return obj.select

    return obj.select_get()


def set_object_select(obj, select):
    if check_version(2, 80, 0) < 0:
        obj.select = select
    else:
        obj.select_set(select)


def set_active_object(obj):
    if check_version(2, 80, 0) < 0:
        bpy.context.scene.objects.active = obj
    else:
        bpy.context.view_layer.objects.active = obj


def get_active_object(context):
    if check_version(2, 80, 0) < 0:
        return context.scene.objects.active
    else:
        return context.view_layer.objects.active


def object_has_uv_layers(obj):
    if check_version(2, 80, 0) < 0:
        return hasattr(obj.data, "uv_textures")
    else:
        return hasattr(obj.data, "uv_layers")


def get_object_uv_layers(obj):
    if check_version(2, 80, 0) < 0:
        return obj.data.uv_textures
    else:
        return obj.data.uv_layers


def icon(icon):
    if icon == 'IMAGE':
        if check_version(2, 80, 0) < 0:
            return 'IMAGE_COL'

    return icon


def set_blf_font_color(font_id, r, g, b, a):
    blf.color(font_id, r, g, b, a)


def set_blf_blur(font_id, radius):
    if check_version(2, 80, 0) < 0:
        blf.blur(font_id, radius)


def get_all_space_types():
    if check_version(2, 80, 0) >= 0:
        return {
            'CLIP_EDITOR': bpy.types.SpaceClipEditor,
            'CONSOLE': bpy.types.SpaceConsole,
            'DOPESHEET_EDITOR': bpy.types.SpaceDopeSheetEditor,
            'FILE_BROWSER': bpy.types.SpaceFileBrowser,
            'GRAPH_EDITOR': bpy.types.SpaceGraphEditor,
            'IMAGE_EDITOR': bpy.types.SpaceImageEditor,
            'INFO': bpy.types.SpaceInfo,
            'NLA_EDITOR': bpy.types.SpaceNLA,
            'NODE_EDITOR': bpy.types.SpaceNodeEditor,
            'OUTLINER': bpy.types.SpaceOutliner,
            'PROPERTIES': bpy.types.SpaceProperties,
            'SEQUENCE_EDITOR': bpy.types.SpaceSequenceEditor,
            'TEXT_EDITOR': bpy.types.SpaceTextEditor,
            'USER_PREFERENCES': bpy.types.SpacePreferences,
            'VIEW_3D': bpy.types.SpaceView3D,
        }
    else:
        return {
            'VIEW_3D': bpy.types.SpaceView3D,
            'TIMELINE': bpy.types.SpaceTimeline,
            'GRAPH_EDITOR': bpy.types.SpaceGraphEditor,
            'DOPESHEET_EDITOR': bpy.types.SpaceDopeSheetEditor,
            'NLA_EDITOR': bpy.types.SpaceNLA,
            'IMAGE_EDITOR': bpy.types.SpaceImageEditor,
            'SEQUENCE_EDITOR': bpy.types.SpaceSequenceEditor,
            'CLIP_EDITOR': bpy.types.SpaceClipEditor,
            'TEXT_EDITOR': bpy.types.SpaceTextEditor,
            'NODE_EDITOR': bpy.types.SpaceNodeEditor,
            'LOGIC_EDITOR': bpy.types.SpaceLogicEditor,
            'PROPERTIES': bpy.types.SpaceProperties,
            'OUTLINER': bpy.types.SpaceOutliner,
            'USER_PREFERENCES': bpy.types.SpaceUserPreferences,
            'INFO': bpy.types.SpaceInfo,
            'FILE_BROWSER': bpy.types.SpaceFileBrowser,
            'CONSOLE': bpy.types.SpaceConsole,
        }
