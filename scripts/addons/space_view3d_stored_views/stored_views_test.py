# SPDX-FileCopyrightText: 2019-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

bl_info = {
    "name": "Stored Views",
    "description": "Save and restore User defined views, pov, layers and display configs",
    "author": "nfloyd, Francesco Siddi",
    "version": (0, 3, 7),
    "blender": (2, 80, 0),
    "location": "View3D > Properties > Stored Views",
    "warning": "",
    "doc_url": "https://wiki.blender.org/index.php/Extensions:2.5/"
               "Py/Scripts/3D_interaction/stored_views",
    "category": "3D View"
}

"""
ACKNOWLEDGMENT
==============
import/export functionality is mostly based
on Bart Crouch's Theme Manager Addon

TODO: quadview complete support : investigate. Where's the data?
TODO: lock_camera_and_layers. investigate usage
TODO: list reordering

NOTE: logging setup has to be provided by the user in a separate config file
    as Blender will not try to configure logging by default in an add-on
    The Config File should be in the Blender Config folder > /scripts/startup/config_logging.py
    For setting up /location of the config folder see:
    https://docs.blender.org/manual/en/latest/getting_started/
    installing/configuration/directories.html
    For configuring logging itself in the file, general Python documentation should work
    As the logging calls are not configured, they can be kept in the other modules of this add-on
    and will not have output until the logging configuration is set up
"""


import bpy
from bpy.props import (
    BoolProperty,
    IntProperty,
    PointerProperty,
)
from bpy.types import (
    AddonPreferences,
    Operator,
    Panel
)

import logging
module_logger = logging.getLogger(__name__)

import gzip
import os
import pickle
import shutil

from bpy_extras.io_utils import (
    ExportHelper,
    ImportHelper,
)

import blf

import hashlib
import bpy


# Utility function get preferences setting for exporters
def get_preferences():
    # replace the key if the add-on name changes
    addon = bpy.context.preferences.addons[__package__]
    show_warn = (addon.preferences.show_exporters if addon else False)

    return show_warn


class StoredView():
    def __init__(self, mode, index=None):
        self.logger = logging.getLogger('%s.StoredView' % __name__)
        self.scene = bpy.context.scene
        self.view3d = bpy.context.space_data
        self.index = index
        self.data_store = DataStore(mode=mode)

    def save(self):
        if self.index == -1:
            stored_view, self.index = self.data_store.create()
        else:
            stored_view = self.data_store.get(self.index)
        self.from_v3d(stored_view)
        self.logger.debug('index: %s name: %s' % (self.data_store.current_index, stored_view.name))

    def set(self):
        stored_view = self.data_store.get(self.index)
        self.update_v3d(stored_view)
        self.logger.debug('index: %s name: %s' % (self.data_store.current_index, stored_view.name))

    def from_v3d(self, stored_view):
        raise NotImplementedError("Subclass must implement abstract method")

    def update_v3d(self, stored_view):
        raise NotImplementedError("Subclass must implement abstract method")

    @staticmethod
    def is_modified(context, stored_view):
        raise NotImplementedError("Subclass must implement abstract method")


class POV(StoredView):
    def __init__(self, index=None):
        super().__init__(mode='POV', index=index)
        self.logger = logging.getLogger('%s.POV' % __name__)

    def from_v3d(self, stored_view):
        view3d = self.view3d
        region3d = view3d.region_3d

        stored_view.distance = region3d.view_distance
        stored_view.location = region3d.view_location
        stored_view.rotation = region3d.view_rotation
        stored_view.perspective_matrix_md5 = POV._get_perspective_matrix_md5(region3d)
        stored_view.perspective = region3d.view_perspective
        stored_view.lens = view3d.lens
        stored_view.clip_start = view3d.clip_start
        stored_view.clip_end = view3d.clip_end

        if region3d.view_perspective == 'CAMERA':
            stored_view.camera_type = view3d.camera.type  # type : 'CAMERA' or 'MESH'
            stored_view.camera_name = view3d.camera.name  # store string instead of object
        if view3d.lock_object is not None:
            stored_view.lock_object_name = view3d.lock_object.name  # idem
        else:
            stored_view.lock_object_name = ""
        stored_view.lock_cursor = view3d.lock_cursor
        stored_view.cursor_location = view3d.cursor_location

    def update_v3d(self, stored_view):
        view3d = self.view3d
        region3d = view3d.region_3d
        region3d.view_distance = stored_view.distance
        region3d.view_location = stored_view.location
        region3d.view_rotation = stored_view.rotation
        region3d.view_perspective = stored_view.perspective
        view3d.lens = stored_view.lens
        view3d.clip_start = stored_view.clip_start
        view3d.clip_end = stored_view.clip_end
        view3d.lock_cursor = stored_view.lock_cursor
        if stored_view.lock_cursor is True:
            # update cursor only if view is locked to cursor
            self.scene.cursor.location = stored_view.cursor_location

        if stored_view.perspective == "CAMERA":

            lock_obj = self._get_object(stored_view.lock_object_name)
            if lock_obj:
                view3d.lock_object = lock_obj
            else:
                cam = self._get_object(stored_view.camera_name)
                if cam:
                    view3d.camera = cam

    @staticmethod
    def _get_object(name, pointer=None):
        return bpy.data.objects.get(name)

    @staticmethod
    def is_modified(context, stored_view):
        # TODO: check for others param, currently only perspective
        # and perspective_matrix are checked
        POV.logger = logging.getLogger('%s.POV' % __name__)
        view3d = context.space_data
        region3d = view3d.region_3d
        if region3d.view_perspective != stored_view.perspective:
            POV.logger.debug('view_perspective')
            return True

        md5 = POV._get_perspective_matrix_md5(region3d)
        if (md5 != stored_view.perspective_matrix_md5 and
          region3d.view_perspective != "CAMERA"):
            POV.logger.debug('perspective_matrix')
            return True

        return False

    @staticmethod
    def _get_perspective_matrix_md5(region3d):
        md5 = hashlib.md5(str(region3d.perspective_matrix).encode('utf-8')).hexdigest()
        return md5


class Layers(StoredView):
    def __init__(self, index=None):
        super().__init__(mode='LAYERS', index=index)
        self.logger = logging.getLogger('%s.Layers' % __name__)

    def from_v3d(self, stored_view):
        view3d = self.view3d
        stored_view.view_layers = view3d.layers
        stored_view.scene_layers = self.scene.layers
        stored_view.lock_camera_and_layers = view3d.lock_camera_and_layers

    def update_v3d(self, stored_view):
        view3d = self.view3d
        view3d.lock_camera_and_layers = stored_view.lock_camera_and_layers
        if stored_view.lock_camera_and_layers is True:
            self.scene.layers = stored_view.scene_layers
        else:
            view3d.layers = stored_view.view_layers

    @staticmethod
    def is_modified(context, stored_view):
        Layers.logger = logging.getLogger('%s.Layers' % __name__)
        if stored_view.lock_camera_and_layers != context.space_data.lock_camera_and_layers:
            Layers.logger.debug('lock_camera_and_layers')
            return True
        if stored_view.lock_camera_and_layers is True:
            for i in range(20):
                if stored_view.scene_layers[i] != context.scene.layers[i]:
                    Layers.logger.debug('scene_layers[%s]' % (i, ))
                    return True
        else:
            for i in range(20):
                if stored_view.view_layers[i] != context.space_data.view3d.layers[i]:
                    return True
        return False


class Display(StoredView):
    def __init__(self, index=None):
        super().__init__(mode='DISPLAY', index=index)
        self.logger = logging.getLogger('%s.Display' % __name__)

    def from_v3d(self, stored_view):
        view3d = self.view3d
        stored_view.viewport_shade = view3d.viewport_shade
        stored_view.show_only_render = view3d.show_only_render
        stored_view.show_outline_selected = view3d.show_outline_selected
        stored_view.show_all_objects_origin = view3d.show_all_objects_origin
        stored_view.show_relationship_lines = view3d.show_relationship_lines
        stored_view.show_floor = view3d.show_floor
        stored_view.show_axis_x = view3d.show_axis_x
        stored_view.show_axis_y = view3d.show_axis_y
        stored_view.show_axis_z = view3d.show_axis_z
        stored_view.grid_lines = view3d.grid_lines
        stored_view.grid_scale = view3d.grid_scale
        stored_view.grid_subdivisions = view3d.grid_subdivisions
        stored_view.material_mode = self.scene.game_settings.material_mode
        stored_view.show_textured_solid = view3d.show_textured_solid

    def update_v3d(self, stored_view):
        view3d = self.view3d
        view3d.viewport_shade = stored_view.viewport_shade
        view3d.show_only_render = stored_view.show_only_render
        view3d.show_outline_selected = stored_view.show_outline_selected
        view3d.show_all_objects_origin = stored_view.show_all_objects_origin
        view3d.show_relationship_lines = stored_view.show_relationship_lines
        view3d.show_floor = stored_view.show_floor
        view3d.show_axis_x = stored_view.show_axis_x
        view3d.show_axis_y = stored_view.show_axis_y
        view3d.show_axis_z = stored_view.show_axis_z
        view3d.grid_lines = stored_view.grid_lines
        view3d.grid_scale = stored_view.grid_scale
        view3d.grid_subdivisions = stored_view.grid_subdivisions
        self.scene.game_settings.material_mode = stored_view.material_mode
        view3d.show_textured_solid = stored_view.show_textured_solid

    @staticmethod
    def is_modified(context, stored_view):
        Display.logger = logging.getLogger('%s.Display' % __name__)
        view3d = context.space_data
        excludes = ["material_mode", "quad_view", "lock_rotation", "show_sync_view", "use_box_clip", "name"]
        for k, v in stored_view.items():
            if k not in excludes:
                if getattr(view3d, k) != getattr(stored_view, k):
                    return True

        if stored_view.material_mode != context.scene.game_settings.material_mode:
            Display.logger.debug('material_mode')
            return True


class View(StoredView):
    def __init__(self, index=None):
        super().__init__(mode='VIEW', index=index)
        self.logger = logging.getLogger('%s.View' % __name__)
        self.pov = POV()
        self.layers = Layers()
        self.display = Display()

    def from_v3d(self, stored_view):
        self.pov.from_v3d(stored_view.pov)
        self.layers.from_v3d(stored_view.layers)
        self.display.from_v3d(stored_view.display)

    def update_v3d(self, stored_view):
        self.pov.update_v3d(stored_view.pov)
        self.layers.update_v3d(stored_view.layers)
        self.display.update_v3d(stored_view.display)

    @staticmethod
    def is_modified(context, stored_view):
        if POV.is_modified(context, stored_view.pov) or \
           Layers.is_modified(context, stored_view.layers) or \
           Display.is_modified(context, stored_view.display):
            return True
        return False


class DataStore():
    def __init__(self, scene=None, mode=None):
        if scene is None:
            scene = bpy.context.scene
        stored_views = scene.stored_views
        self.mode = mode

        if mode is None:
            self.mode = stored_views.mode

        if self.mode == 'VIEW':
            self.list = stored_views.view_list
            self.current_index = stored_views.current_indices[0]
        elif self.mode == 'POV':
            self.list = stored_views.pov_list
            self.current_index = stored_views.current_indices[1]
        elif self.mode == 'LAYERS':
            self.list = stored_views.layers_list
            self.current_index = stored_views.current_indices[2]
        elif self.mode == 'DISPLAY':
            self.list = stored_views.display_list
            self.current_index = stored_views.current_indices[3]

    def create(self):
        item = self.list.add()
        item.name = self._generate_name()
        index = len(self.list) - 1
        self._set_current_index(index)
        return item, index

    def get(self, index):
        self._set_current_index(index)
        return self.list[index]

    def delete(self, index):
        if self.current_index > index:
            self._set_current_index(self.current_index - 1)
        elif self.current_index == index:
            self._set_current_index(-1)

        self.list.remove(index)

    def _set_current_index(self, index):
        self.current_index = index
        mode = self.mode
        stored_views = bpy.context.scene.stored_views
        if mode == 'VIEW':
            stored_views.current_indices[0] = index
        elif mode == 'POV':
            stored_views.current_indices[1] = index
        elif mode == 'LAYERS':
            stored_views.current_indices[2] = index
        elif mode == 'DISPLAY':
            stored_views.current_indices[3] = index

    def _generate_name(self):
        default_name = str(self.mode)
        names = []
        for i in self.list:
            i_name = i.name
            if i_name.startswith(default_name):
                names.append(i_name)
        names.sort()
        try:
            l_name = names[-1]
            post_fix = l_name.rpartition('.')[2]
            if post_fix.isnumeric():
                post_fix = str(int(post_fix) + 1).zfill(3)
            else:
                if post_fix == default_name:
                    post_fix = "001"
            return default_name + "." + post_fix
        except:
            return default_name

    @staticmethod
    def sanitize_data(scene):

        def check_objects_references(mode, list):
            to_remove = []
            for i, list_item in enumerate(list.items()):
                key, item = list_item
                if mode == 'POV' or mode == 'VIEWS':
                    if mode == 'VIEWS':
                        item = item.pov

                    if item.perspective == "CAMERA":

                        camera = bpy.data.objects.get(item.camera_name)
                        if camera is None:
                            try:  # pick a default camera TODO: ask to pick?
                                camera = bpy.data.cameras[0]
                                item.camera_name = camera.name
                            except:  # couldn't find a camera in the scene
                                pass

                        obj = bpy.data.objects.get(item.lock_object_name)
                        if obj is None and camera is None:
                            to_remove.append(i)

            for i in reversed(to_remove):
                list.remove(i)

        modes = ['POV', 'VIEW', 'DISPLAY', 'LAYERS']
        for mode in modes:
            data = DataStore(scene=scene, mode=mode)
            check_objects_references(mode, data.list)


def stored_view_factory(mode, *args, **kwargs):
    if mode == 'POV':
        return POV(*args, **kwargs)
    elif mode == 'LAYERS':
        return Layers(*args, **kwargs)
    elif mode == 'DISPLAY':
        return Display(*args, **kwargs)
    elif mode == 'VIEW':
        return View(*args, **kwargs)

"""
  If view name display is enabled,
  it will check periodically if the view has been modified
  since last set.
  get_preferences_timer() is the time in seconds between these checks.
  It can be increased, if the view become sluggish
  It is set in the add-on preferences
"""


# Utility function get_preferences_timer for update of 3d view draw
def get_preferences_timer():
    # replace the key if the add-on name changes
    # TODO: expose refresh rate to ui???
    addon = bpy.context.preferences.addons[__package__]
    timer_update = (addon.preferences.view_3d_update_rate if addon else False)

    return timer_update


def init_draw(context=None):
    if context is None:
        context = bpy.context

    if "stored_views_osd" not in context.window_manager:
        context.window_manager["stored_views_osd"] = False

    if not context.window_manager["stored_views_osd"]:
        context.window_manager["stored_views_osd"] = True
        bpy.ops.stored_views.draw()


def _draw_callback_px(self, context):
    area = context.area
    if area and area.type == 'VIEW_3D':
        ui_scale = context.preferences.system.ui_scale
        r_width = text_location = context.region.width
        r_height = context.region.height
        font_id = 0  # TODO: need to find out how best to get font_id
        blf.size(font_id, 11 * ui_scale)
        text_size = blf.dimensions(0, self.view_name)

        # compute the text location
        text_location = 0
        overlap = context.preferences.system.use_region_overlap
        if overlap:
            for region in area.regions:
                if region.type == "UI":
                    text_location = r_width - region.width

        text_x = text_location - text_size[0] - 10
        text_y = r_height - text_size[1] - 8
        blf.position(font_id, text_x, text_y, 0)
        blf.draw(font_id, self.view_name)


class VIEW3D_OT_stored_views_draw(Operator):
    bl_idname = "stored_views.draw"
    bl_label = "Show current"
    bl_description = "Toggle the display current view name in the view 3D"

    _handle = None
    _timer = None

    @staticmethod
    def handle_add(self, context):
        VIEW3D_OT_stored_views_draw._handle = bpy.types.SpaceView3D.draw_handler_add(
            _draw_callback_px, (self, context), 'WINDOW', 'POST_PIXEL')
        VIEW3D_OT_stored_views_draw._timer = \
            context.window_manager.event_timer_add(get_preferences_timer(), context.window)

    @staticmethod
    def handle_remove(context):
        if VIEW3D_OT_stored_views_draw._handle is not None:
            bpy.types.SpaceView3D.draw_handler_remove(VIEW3D_OT_stored_views_draw._handle, 'WINDOW')
        if VIEW3D_OT_stored_views_draw._timer is not None:
            context.window_manager.event_timer_remove(VIEW3D_OT_stored_views_draw._timer)
        VIEW3D_OT_stored_views_draw._handle = None
        VIEW3D_OT_stored_views_draw._timer = None

    @classmethod
    def poll(cls, context):
        # return context.mode == 'OBJECT'
        return True

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if not context.area or context.area.type != "VIEW_3D":
            return {"PASS_THROUGH"}

        data = DataStore()
        stored_views = context.scene.stored_views

        if len(data.list) > 0 and \
           data.current_index >= 0 and \
           not stored_views.view_modified:

            if not stored_views.view_modified:
                sv = data.list[data.current_index]
                self.view_name = sv.name
                if event.type == 'TIMER':
                    is_modified = False
                    if data.mode == 'VIEW':
                        is_modified = View.is_modified(context, sv)
                    elif data.mode == 'POV':
                        is_modified = POV.is_modified(context, sv)
                    elif data.mode == 'LAYERS':
                        is_modified = Layers.is_modified(context, sv)
                    elif data.mode == 'DISPLAY':
                        is_modified = Display.is_modified(context, sv)
                    if is_modified:
                        module_logger.debug(
                                'view modified - index: %s name: %s' % (data.current_index, sv.name)
                                )
                        self.view_name = ""
                        stored_views.view_modified = is_modified

                return {"PASS_THROUGH"}
        else:
            module_logger.debug('exit')
            context.window_manager["stored_views_osd"] = False
            VIEW3D_OT_stored_views_draw.handle_remove(context)

            return {'FINISHED'}

    def execute(self, context):
        if context.area.type == "VIEW_3D":
            self.view_name = ""
            VIEW3D_OT_stored_views_draw.handle_add(self, context)
            context.window_manager.modal_handler_add(self)

            return {"RUNNING_MODAL"}
        else:
            self.report({"WARNING"}, "View3D not found. Operation Cancelled")

            return {"CANCELLED"}

class VIEW3D_OT_stored_views_initialize(Operator):
    bl_idname = "view3d.stored_views_initialize"
    bl_label = "Initialize"

    @classmethod
    def poll(cls, context):
        return not hasattr(bpy.types.Scene, 'stored_views')

    def execute(self, context):
        bpy.types.Scene.stored_views: PointerProperty(
                                            type=properties.StoredViewsData
                                            )
        scenes = bpy.data.scenes
        data = DataStore()
        for scene in scenes:
            DataStore.sanitize_data(scene)
        return {'FINISHED'}


from bpy.types import PropertyGroup
from bpy.props import (
        BoolProperty,
        BoolVectorProperty,
        CollectionProperty,
        FloatProperty,
        FloatVectorProperty,
        EnumProperty,
        IntProperty,
        IntVectorProperty,
        PointerProperty,
        StringProperty,
        )


class POVData(PropertyGroup):
    distance: FloatProperty()
    location: FloatVectorProperty(
            subtype='TRANSLATION'
            )
    rotation: FloatVectorProperty(
            subtype='QUATERNION',
            size=4
            )
    name: StringProperty()
    perspective: EnumProperty(
            items=[('PERSP', '', ''),
                   ('ORTHO', '', ''),
                   ('CAMERA', '', '')]
            )
    lens: FloatProperty()
    clip_start: FloatProperty()
    clip_end: FloatProperty()
    lock_cursor: BoolProperty()
    cursor_location: FloatVectorProperty()
    perspective_matrix_md5: StringProperty()
    camera_name: StringProperty()
    camera_type: StringProperty()
    lock_object_name: StringProperty()


class LayersData(PropertyGroup):
    view_layers: BoolVectorProperty(size=20)
    scene_layers: BoolVectorProperty(size=20)
    lock_camera_and_layers: BoolProperty()
    name: StringProperty()


class DisplayData(PropertyGroup):
    name: StringProperty()
    viewport_shade: EnumProperty(
            items=[('BOUNDBOX', 'BOUNDBOX', 'BOUNDBOX'),
                   ('WIREFRAME', 'WIREFRAME', 'WIREFRAME'),
                   ('SOLID', 'SOLID', 'SOLID'),
                   ('TEXTURED', 'TEXTURED', 'TEXTURED'),
                   ('MATERIAL', 'MATERIAL', 'MATERIAL'),
                   ('RENDERED', 'RENDERED', 'RENDERED')]
            )
    show_only_render: BoolProperty()
    show_outline_selected: BoolProperty()
    show_all_objects_origin: BoolProperty()
    show_relationship_lines: BoolProperty()
    show_floor: BoolProperty()
    show_axis_x: BoolProperty()
    show_axis_y: BoolProperty()
    show_axis_z: BoolProperty()
    grid_lines: IntProperty()
    grid_scale: FloatProperty()
    grid_subdivisions: IntProperty()
    material_mode: StringProperty()
    show_textured_solid: BoolProperty()
    quad_view: BoolProperty()
    lock_rotation: BoolProperty()
    show_sync_view: BoolProperty()
    use_box_clip: BoolProperty()


class ViewData(PropertyGroup):
    pov: PointerProperty(
            type=POVData
            )
    layers: PointerProperty(
            type=LayersData
            )
    display: PointerProperty(
            type=DisplayData
            )
    name: StringProperty()


class StoredViewsData(PropertyGroup):
    pov_list: CollectionProperty(
            type=POVData
            )
    layers_list: CollectionProperty(
            type=LayersData
            )
    display_list: CollectionProperty(
            type=DisplayData
            )
    view_list: CollectionProperty(
            type=ViewData
            )
    mode: EnumProperty(
            name="Mode",
            items=[('VIEW', "View", "3D View settings"),
                   ('POV', "POV", "POV settings"),
                   ('LAYERS', "Layers", "Layers settings"),
                   ('DISPLAY', "Display", "Display settings")],
            default='VIEW'
            )
    current_indices: IntVectorProperty(
            size=4,
            default=[-1, -1, -1, -1]
            )
    view_modified: BoolProperty(
            default=False
            )

class VIEW3D_OT_stored_views_save(Operator):
    bl_idname = "stored_views.save"
    bl_label = "Save Current"
    bl_description = "Save the view 3d current state"

    index: IntProperty()

    def execute(self, context):
        mode = context.scene.stored_views.mode
        sv = stored_view_factory(mode, self.index)
        sv.save()
        context.scene.stored_views.view_modified = False
        init_draw(context)

        return {'FINISHED'}


class VIEW3D_OT_stored_views_set(Operator):
    bl_idname = "stored_views.set"
    bl_label = "Set"
    bl_description = "Update the view 3D according to this view"

    index: IntProperty()

    def execute(self, context):
        mode = context.scene.stored_views.mode
        sv = stored_view_factory(mode, self.index)
        sv.set()
        context.scene.stored_views.view_modified = False
        init_draw(context)

        return {'FINISHED'}


class VIEW3D_OT_stored_views_delete(Operator):
    bl_idname = "stored_views.delete"
    bl_label = "Delete"
    bl_description = "Delete this view"

    index: IntProperty()

    def execute(self, context):
        data = DataStore()
        data.delete(self.index)

        return {'FINISHED'}


class VIEW3D_OT_New_Camera_to_View(Operator):
    bl_idname = "stored_views.newcamera"
    bl_label = "New Camera To View"
    bl_description = "Add a new Active Camera and align it to this view"

    @classmethod
    def poll(cls, context):
        return (
            context.space_data is not None and
            context.space_data.type == 'VIEW_3D' and
            context.space_data.region_3d.view_perspective != 'CAMERA'
            )

    def execute(self, context):

        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.camera_add()
        cam = context.active_object
        cam.name = "View_Camera"
        # make active camera by hand
        context.scene.camera = cam

        bpy.ops.view3d.camera_to_view()
        return {'FINISHED'}


# Camera marker & switcher by Fsiddi
class VIEW3D_OT_SetSceneCamera(Operator):
    bl_idname = "cameraselector.set_scene_camera"
    bl_label = "Set Scene Camera"
    bl_description = "Set chosen camera as the scene's active camera"

    hide_others = False

    def execute(self, context):
        chosen_camera = context.active_object
        scene = context.scene

        if self.hide_others:
            for c in [o for o in scene.objects if o.type == 'CAMERA']:
                c.hide = (c != chosen_camera)
        scene.camera = chosen_camera
        bpy.ops.object.select_all(action='DESELECT')
        chosen_camera.select_set(True)
        return {'FINISHED'}

    def invoke(self, context, event):
        if event.ctrl:
            self.hide_others = True

        return self.execute(context)


class VIEW3D_OT_PreviewSceneCamera(Operator):
    bl_idname = "cameraselector.preview_scene_camera"
    bl_label = "Preview Camera"
    bl_description = "Preview chosen camera and make scene's active camera"

    def execute(self, context):
        chosen_camera = context.active_object
        bpy.ops.view3d.object_as_camera()
        bpy.ops.object.select_all(action="DESELECT")
        chosen_camera.select_set(True)
        return {'FINISHED'}


class VIEW3D_OT_AddCameraMarker(Operator):
    bl_idname = "cameraselector.add_camera_marker"
    bl_label = "Add Camera Marker"
    bl_description = "Add a timeline marker bound to chosen camera"

    def execute(self, context):
        chosen_camera = context.active_object
        scene = context.scene

        current_frame = scene.frame_current
        marker = None
        for m in reversed(sorted(filter(lambda m: m.frame <= current_frame,
                                        scene.timeline_markers),
                                 key=lambda m: m.frame)):
            marker = m
            break
        if marker and (marker.camera == chosen_camera):
            # Cancel if the last marker at or immediately before
            # current frame is already bound to the camera.
            return {'CANCELLED'}

        marker_name = "F_%02d_%s" % (current_frame, chosen_camera.name)
        if marker and (marker.frame == current_frame):
            # Reuse existing marker at current frame to avoid
            # overlapping bound markers.
            marker.name = marker_name
        else:
            marker = scene.timeline_markers.new(marker_name)
        marker.frame = scene.frame_current
        marker.camera = chosen_camera
        marker.select = True

        for other_marker in [m for m in scene.timeline_markers if m != marker]:
            other_marker.select = False

        return {'FINISHED'}

# gpl authors: nfloyd, Francesco Siddi





# TODO: reinstate filters?
class IO_Utils():

    @staticmethod
    def get_preset_path():
        # locate stored_views preset folder
        paths = bpy.utils.preset_paths("stored_views")
        if not paths:
            # stored_views preset folder doesn't exist, so create it
            paths = [os.path.join(bpy.utils.user_resource('SCRIPTS'), "presets",
                    "stored_views")]
            if not os.path.exists(paths[0]):
                os.makedirs(paths[0])

        return(paths)

    @staticmethod
    def stored_views_apply_from_scene(scene_name, replace=True):
        scene = bpy.context.scene
        scene_exists = True if scene_name in bpy.data.scenes.keys() else False

        if scene_exists:
            sv = bpy.context.scene.stored_views
            # io_filters = sv.settings.io_filters

            structs = [sv.view_list, sv.pov_list, sv.layers_list, sv.display_list]
            if replace is True:
                for st in structs:  # clear swap and list
                    while len(st) > 0:
                        st.remove(0)

            f_sv = bpy.data.scenes[scene_name].stored_views
            # f_sv = bpy.data.scenes[scene_name].stored_views
            f_structs = [f_sv.view_list, f_sv.pov_list, f_sv.layers_list, f_sv.display_list]
            """
            is_filtered = [io_filters.views, io_filters.point_of_views,
                           io_filters.layers, io_filters.displays]
            """
            for i in range(len(f_structs)):
                """
                if is_filtered[i] is False:
                    continue
                """
                for j in f_structs[i]:
                    item = structs[i].add()
                    # stored_views_copy_item(j, item)
                    for k, v in j.items():
                        item[k] = v
            DataStore.sanitize_data(scene)
            return True
        else:
            return False

    @staticmethod
    def stored_views_export_to_blsv(filepath, name='Custom Preset'):
        # create dictionary with all information
        dump = {"info": {}, "data": {}}
        dump["info"]["script"] = bl_info['name']
        dump["info"]["script_version"] = bl_info['version']
        dump["info"]["version"] = bpy.app.version
        dump["info"]["preset_name"] = name

        # get current stored views settings
        scene = bpy.context.scene
        sv = scene.stored_views

        def dump_view_list(dict, list):
            if str(type(list)) == "<class 'bpy_prop_collection_idprop'>":
                for i, struct_dict in enumerate(list):
                    dict[i] = {"name": str,
                               "pov": {},
                               "layers": {},
                               "display": {}}
                    dict[i]["name"] = struct_dict.name
                    dump_item(dict[i]["pov"], struct_dict.pov)
                    dump_item(dict[i]["layers"], struct_dict.layers)
                    dump_item(dict[i]["display"], struct_dict.display)

        def dump_list(dict, list):
            if str(type(list)) == "<class 'bpy_prop_collection_idprop'>":
                for i, struct in enumerate(list):
                    dict[i] = {}
                    dump_item(dict[i], struct)

        def dump_item(dict, struct):
            for prop in struct.bl_rna.properties:
                if prop.identifier == "rna_type":
                    # not a setting, so skip
                    continue

                val = getattr(struct, prop.identifier)
                if str(type(val)) in ["<class 'bpy_prop_array'>"]:
                    # array
                    dict[prop.identifier] = [v for v in val]
                # address the pickle limitations of dealing with the Vector class
                elif str(type(val)) in ["<class 'Vector'>",
                                       "<class 'Quaternion'>"]:
                    dict[prop.identifier] = [v for v in val]
                else:
                    # single value
                    dict[prop.identifier] = val

        # io_filters = sv.settings.io_filters
        dump["data"] = {"point_of_views": {},
                        "layers": {},
                        "displays": {},
                        "views": {}}

        others_data = [(dump["data"]["point_of_views"], sv.pov_list),  # , io_filters.point_of_views),
                       (dump["data"]["layers"], sv.layers_list),       # , io_filters.layers),
                       (dump["data"]["displays"], sv.display_list)]    # , io_filters.displays)]
        for list_data in others_data:
            # if list_data[2] is True:
            dump_list(list_data[0], list_data[1])

        views_data = (dump["data"]["views"], sv.view_list)
        # if io_filters.views is True:
        dump_view_list(views_data[0], views_data[1])

        # save to file
        filepath = filepath
        filepath = bpy.path.ensure_ext(filepath, '.blsv')
        file = gzip.open(filepath, mode='wb')
        pickle.dump(dump, file, protocol=pickle.HIGHEST_PROTOCOL)
        file.close()

    @staticmethod
    def stored_views_apply_preset(filepath, replace=True):
        if not filepath:
            return False

        file = gzip.open(filepath, mode='rb')
        dump = pickle.load(file)
        file.close()
        # apply preset
        scene = bpy.context.scene
        sv = getattr(scene, "stored_views", None)

        if not sv:
            return False

        # io_filters = sv.settings.io_filters
        sv_data = {
            "point_of_views": sv.pov_list,
            "views": sv.view_list,
            "layers": sv.layers_list,
            "displays": sv.display_list
        }
        for sv_struct, props in dump["data"].items():
            """
            is_filtered = getattr(io_filters, sv_struct)
            if is_filtered is False:
                continue
            """
            sv_list = sv_data[sv_struct]  # .list
            if replace is True:  # clear swap and list
                while len(sv_list) > 0:
                    sv_list.remove(0)
            for key, prop_struct in props.items():
                sv_item = sv_list.add()

                for subprop, subval in prop_struct.items():
                    if isinstance(subval, dict):  # views : pov, layers, displays
                        v_subprop = getattr(sv_item, subprop)
                        for v_subkey, v_subval in subval.items():
                            if isinstance(v_subval, list):  # array like of pov,...
                                v_array_like = getattr(v_subprop, v_subkey)
                                for i in range(len(v_array_like)):
                                    v_array_like[i] = v_subval[i]
                            else:
                                setattr(v_subprop, v_subkey, v_subval)  # others
                    elif isinstance(subval, list):
                        array_like = getattr(sv_item, subprop)
                        for i in range(len(array_like)):
                            array_like[i] = subval[i]
                    else:
                        setattr(sv_item, subprop, subval)

        DataStore.sanitize_data(scene)

        return True


class VIEW3D_OT_stored_views_import(Operator, ImportHelper):
    bl_idname = "stored_views.import_blsv"
    bl_label = "Import Stored Views preset"
    bl_description = "Import a .blsv preset file to the current Stored Views"

    filename_ext = ".blsv"
    filter_glob: StringProperty(
        default="*.blsv",
        options={'HIDDEN'}
    )
    replace: BoolProperty(
        name="Replace",
        default=True,
        description="Replace current stored views, otherwise append"
    )

    @classmethod
    def poll(cls, context):
        return get_preferences()

    def execute(self, context):
        # the usual way is to not select the file in the file browser
        exists = os.path.isfile(self.filepath) if self.filepath else False
        if not exists:
            self.report({'WARNING'},
                        "No filepath specified or file could not be found. Operation Cancelled")
            return {'CANCELLED'}

        # apply chosen preset
        apply_preset = IO_Utils.stored_views_apply_preset(
                            filepath=self.filepath, replace=self.replace
                            )
        if not apply_preset:
            self.report({'WARNING'},
                        "Please Initialize Stored Views first (in the 3D View Properties Area)")
            return {'CANCELLED'}

        # copy preset to presets folder
        filename = os.path.basename(self.filepath)
        try:
            shutil.copyfile(self.filepath,
                            os.path.join(IO_Utils.get_preset_path()[0], filename))
        except:
            self.report({'WARNING'},
                        "Stored Views: preset applied, but installing failed (preset already exists?)")
            return{'CANCELLED'}

        return{'FINISHED'}


class VIEW3D_OT_stored_views_import_from_scene(Operator):
    bl_idname = "stored_views.import_from_scene"
    bl_label = "Import stored views from scene"
    bl_description = "Import currently stored views from an another scene"

    scene_name: StringProperty(
        name="Scene Name",
        description="A current blend scene",
        default=""
    )
    replace: BoolProperty(
        name="Replace",
        default=True,
        description="Replace current stored views, otherwise append"
    )

    @classmethod
    def poll(cls, context):
        return get_preferences()

    def draw(self, context):
        layout = self.layout

        layout.prop_search(self, "scene_name", bpy.data, "scenes")
        layout.prop(self, "replace")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        # filepath should always be given
        if not self.scene_name:
            self.report({"WARNING"},
                        "No scene name was given. Operation Cancelled")
            return{'CANCELLED'}

        is_finished = IO_Utils.stored_views_apply_from_scene(
                            self.scene_name, replace=self.replace
                            )
        if not is_finished:
            self.report({"WARNING"},
                        "Could not find the specified scene. Operation Cancelled")
            return {"CANCELLED"}

        return{'FINISHED'}


class VIEW3D_OT_stored_views_export(Operator, ExportHelper):
    bl_idname = "stored_views.export_blsv"
    bl_label = "Export Stored Views preset"
    bl_description = "Export the current Stored Views to a .blsv preset file"

    filename_ext = ".blsv"
    filepath: StringProperty(
        default=os.path.join(IO_Utils.get_preset_path()[0], "untitled")
    )
    filter_glob: StringProperty(
        default="*.blsv",
        options={'HIDDEN'}
    )
    preset_name: StringProperty(
        name="Preset name",
        default="",
        description="Name of the stored views preset"
    )

    @classmethod
    def poll(cls, context):
        return get_preferences()

    def execute(self, context):
        IO_Utils.stored_views_export_to_blsv(self.filepath, self.preset_name)

        return{'FINISHED'}


class VIEW3D_PT_properties_stored_views(Panel):
    bl_label = "Stored Views"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "View"

    def draw(self, context):
        self.logger = logging.getLogger('%s Properties panel' % __name__)
        layout = self.layout

        if bpy.ops.view3d.stored_views_initialize.poll():
            layout.operator("view3d.stored_views_initialize")
            return

        stored_views = context.scene.stored_views

        # UI : mode
        col = layout.column(align=True)
        col.prop_enum(stored_views, "mode", 'VIEW')
        row = layout.row(align=True)
        row.operator("view3d.camera_to_view", text="Camera To view")
        row.operator("stored_views.newcamera")

        row = col.row(align=True)
        row.prop_enum(stored_views, "mode", 'POV')
        row.prop_enum(stored_views, "mode", 'LAYERS')
        row.prop_enum(stored_views, "mode", 'DISPLAY')

        # UI : operators
        row = layout.row()
        row.operator("stored_views.save").index = -1

        # IO Operators
        if core.get_preferences():
            row = layout.row(align=True)
            row.operator("stored_views.import_from_scene", text="Import from Scene")
            row.operator("stored_views.import_blsv", text="", icon="IMPORT")
            row.operator("stored_views.export_blsv", text="", icon="EXPORT")

        data_store = DataStore()
        list = data_store.list
        # UI : items list
        if len(list) > 0:
            row = layout.row()
            box = row.box()
            # items list
            mode = stored_views.mode
            for i in range(len(list)):
                # associated icon
                icon_string = "MESH_CUBE"  # default icon
                # TODO: icons for view
                if mode == 'POV':
                    persp = list[i].perspective
                    if persp == 'PERSP':
                        icon_string = "MESH_CUBE"
                    elif persp == 'ORTHO':
                        icon_string = "MESH_PLANE"
                    elif persp == 'CAMERA':
                        if list[i].camera_type != 'CAMERA':
                            icon_string = 'OBJECT_DATAMODE'
                        else:
                            icon_string = "OUTLINER_DATA_CAMERA"
                if mode == 'LAYERS':
                    if list[i].lock_camera_and_layers is True:
                        icon_string = 'SCENE_DATA'
                    else:
                        icon_string = 'RENDERLAYERS'
                if mode == 'DISPLAY':
                    shade = list[i].viewport_shade
                    if shade == 'TEXTURED':
                        icon_string = 'TEXTURE_SHADED'
                    if shade == 'MATERIAL':
                        icon_string = 'MATERIAL_DATA'
                    elif shade == 'SOLID':
                        icon_string = 'SOLID'
                    elif shade == 'WIREFRAME':
                        icon_string = "WIRE"
                    elif shade == 'BOUNDBOX':
                        icon_string = 'BBOX'
                    elif shade == 'RENDERED':
                        icon_string = 'MATERIAL'
                # stored view row
                subrow = box.row(align=True)
                # current view indicator
                if data_store.current_index == i and context.scene.stored_views.view_modified is False:
                    subrow.label(text="", icon='CHECKMARK')
                subrow.operator("stored_views.set",
                                text="", icon=icon_string).index = i
                subrow.prop(list[i], "name", text="")
                subrow.operator("stored_views.save",
                                text="", icon="REC").index = i
                subrow.operator("stored_views.delete",
                                text="", icon="PANEL_CLOSE").index = i

        layout = self.layout
        scene = context.scene
        layout.label(text="Camera Selector")
        cameras = sorted([o for o in scene.objects if o.type == 'CAMERA'],
                         key=lambda o: o.name)

        if len(cameras) > 0:
            for camera in cameras:
                row = layout.row(align=True)
                row.context_pointer_set("active_object", camera)
                row.operator("cameraselector.set_scene_camera",
                                   text=camera.name, icon='OUTLINER_DATA_CAMERA')
                row.operator("cameraselector.preview_scene_camera",
                                   text='', icon='RESTRICT_VIEW_OFF')
                row.operator("cameraselector.add_camera_marker",
                                   text='', icon='MARKER')
        else:
            layout.label(text="No cameras in this scene")
# Addon Preferences

class VIEW3D_OT_stored_views_preferences(AddonPreferences):
    bl_idname = __name__

    show_exporters: BoolProperty(
        name="Enable I/O Operators",
        default=False,
        description="Enable Import/Export Operations in the UI:\n"
                    "Import Stored Views preset,\n"
                    "Export Stored Views preset and \n"
                    "Import stored views from scene",
    )
    view_3d_update_rate: IntProperty(
        name="3D view update",
        description="Update rate of the 3D view redraw\n"
                    "Increase the value if the UI feels sluggish",
        min=1, max=10,
        default=1
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.prop(self, "view_3d_update_rate", toggle=True)
        row.prop(self, "show_exporters", toggle=True)


# Register
classes = [
    VIEW3D_OT_stored_views_initialize,
    VIEW3D_OT_stored_views_preferences,
    VIEW3D_PT_properties_stored_views,
    POVData,
    LayersData,
    DisplayData,
    ViewData,
    StoredViewsData,
    VIEW3D_OT_stored_views_draw,
    VIEW3D_OT_stored_views_save,
    VIEW3D_OT_stored_views_set,
    VIEW3D_OT_stored_views_delete,
    VIEW3D_OT_New_Camera_to_View,
    VIEW3D_OT_SetSceneCamera,
    VIEW3D_OT_PreviewSceneCamera,
    VIEW3D_OT_AddCameraMarker,
#    IO_Utils,
    VIEW3D_OT_stored_views_import,
    VIEW3D_OT_stored_views_import_from_scene,
    VIEW3D_OT_stored_views_export
    ]


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)


def unregister():
    ui.VIEW3D_OT_stored_views_draw.handle_remove(bpy.context)
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
    if hasattr(bpy.types.Scene, "stored_views"):
        del bpy.types.Scene.stored_views


if __name__ == "__main__":
    register()
