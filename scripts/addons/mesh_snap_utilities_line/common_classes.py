# SPDX-FileCopyrightText: 2018-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from mathutils import (
    Vector,
    Matrix,
)
from mathutils.geometry import intersect_point_line
from .drawing_utilities import SnapDrawn
from .common_utilities import (
    convert_distance,
    get_units_info,
    location_3d_to_region_2d,
)


class SnapNavigation():
    __slots__ = (
        'use_ndof',
        '_rotate',
        '_move',
        '_zoom',
        '_ndof_all',
        '_ndof_orbit',
        '_ndof_orbit_zoom',
        '_ndof_pan')

    @staticmethod
    def debug_key(key):
        for member in dir(key):
            print(member, getattr(key, member))

    @staticmethod
    def convert_to_flag(shift, ctrl, alt):
        return (shift << 0) | (ctrl << 1) | (alt << 2)

    def __init__(self, context, use_ndof):
        # TO DO:
        # 'View Orbit', 'View Pan', 'NDOF Orbit View', 'NDOF Pan View'
        self.use_ndof = use_ndof and context.preferences.inputs.use_ndof

        self._rotate = set()
        self._move = set()
        self._zoom = set()

        if self.use_ndof:
            self._ndof_all = set()
            self._ndof_orbit = set()
            self._ndof_orbit_zoom = set()
            self._ndof_pan = set()

        for key in context.window_manager.keyconfigs.user.keymaps['3D View'].keymap_items:
            if key.idname == 'view3d.rotate':
                self._rotate.add((self.convert_to_flag(
                    key.shift, key.ctrl, key.alt), key.type, key.value))
            elif key.idname == 'view3d.move':
                self._move.add((self.convert_to_flag(
                    key.shift, key.ctrl, key.alt), key.type, key.value))
            elif key.idname == 'view3d.zoom':
                if key.type == 'WHEELINMOUSE':
                    self._zoom.add((self.convert_to_flag(
                        key.shift, key.ctrl, key.alt), 'WHEELUPMOUSE', key.value, key.properties.delta))
                elif key.type == 'WHEELOUTMOUSE':
                    self._zoom.add((self.convert_to_flag(
                        key.shift, key.ctrl, key.alt), 'WHEELDOWNMOUSE', key.value, key.properties.delta))
                else:
                    self._zoom.add((self.convert_to_flag(
                        key.shift, key.ctrl, key.alt), key.type, key.value, key.properties.delta))

            elif self.use_ndof:
                if key.idname == 'view3d.ndof_all':
                    self._ndof_all.add((self.convert_to_flag(
                        key.shift, key.ctrl, key.alt), key.type))
                elif key.idname == 'view3d.ndof_orbit':
                    self._ndof_orbit.add((self.convert_to_flag(
                        key.shift, key.ctrl, key.alt), key.type))
                elif key.idname == 'view3d.ndof_orbit_zoom':
                    self._ndof_orbit_zoom.add(
                        (self.convert_to_flag(key.shift, key.ctrl, key.alt), key.type))
                elif key.idname == 'view3d.ndof_pan':
                    self._ndof_pan.add((self.convert_to_flag(
                        key.shift, key.ctrl, key.alt), key.type))

    def run(self, context, event, snap_location):
        evkey = (self.convert_to_flag(event.shift, event.ctrl,
                 event.alt), event.type, event.value)

        if evkey in self._rotate:
            if snap_location:
                bpy.ops.view3d.rotate_custom_pivot(
                    'INVOKE_DEFAULT', pivot=snap_location)
            else:
                bpy.ops.view3d.rotate('INVOKE_DEFAULT', use_cursor_init=True)
            return True

        if evkey in self._move:
            bpy.ops.view3d.move('INVOKE_DEFAULT')
            return True

        for key in self._zoom:
            if evkey == key[0:3]:
                if key[3]:
                    if snap_location:
                        bpy.ops.view3d.zoom_custom_target(
                            'INVOKE_DEFAULT', delta=key[3], target=snap_location)
                    else:
                        bpy.ops.view3d.zoom('INVOKE_DEFAULT', delta=key[3])
                else:
                    bpy.ops.view3d.zoom('INVOKE_DEFAULT')
                return True

        if self.use_ndof:
            ndofkey = evkey[:2]
            if ndofkey in self._ndof_all:
                bpy.ops.view3d.ndof_all('INVOKE_DEFAULT')
                return True
            if ndofkey in self._ndof_orbit:
                bpy.ops.view3d.ndof_orbit('INVOKE_DEFAULT')
                return True
            if ndofkey in self._ndof_orbit_zoom:
                bpy.ops.view3d.ndof_orbit_zoom('INVOKE_DEFAULT')
                return True
            if ndofkey in self._ndof_pan:
                bpy.ops.view3d.ndof_pan('INVOKE_DEFAULT')
                return True

        return False


class CharMap:
    __slots__ = (
        'unit_system',
        'uinfo',
        'length_entered',
        'length_entered_value',
        'line_pos')

    ascii = {
        ".", ",", "-", "+", "1", "2", "3",
        "4", "5", "6", "7", "8", "9", "0",
        "c", "m", "d", "k", "h", "a",
        " ", "/", "*", "'", "\""
        # "="
    }
    type = {
        'BACK_SPACE', 'DEL',
        'LEFT_ARROW', 'RIGHT_ARROW'
    }

    def __init__(self, context):
        scale = context.scene.unit_settings.scale_length
        separate_units = context.scene.unit_settings.use_separate
        self.unit_system = context.scene.unit_settings.system
        self.uinfo = get_units_info(scale, self.unit_system, separate_units)

        self.clear()

    def modal_(self, context, event):
        if event.value == 'PRESS':
            type = event.type
            ascii = event.ascii
            if (type in self.type) or (ascii in self.ascii):
                if ascii:
                    pos = self.line_pos
                    if ascii == ",":
                        ascii = "."
                    self.length_entered = self.length_entered[:pos] + \
                        ascii + self.length_entered[pos:]
                    self.line_pos += 1

                if self.length_entered:
                    pos = self.line_pos
                    if type == 'BACK_SPACE':
                        self.length_entered = self.length_entered[:pos -
                                                                  1] + self.length_entered[pos:]
                        self.line_pos -= 1

                    elif type == 'DEL':
                        self.length_entered = self.length_entered[:pos] + \
                            self.length_entered[pos + 1:]

                    elif type == 'LEFT_ARROW':
                        self.line_pos = (
                            pos - 1) % (len(self.length_entered) + 1)

                    elif type == 'RIGHT_ARROW':
                        self.line_pos = (
                            pos + 1) % (len(self.length_entered) + 1)

                    try:
                        self.length_entered_value = bpy.utils.units.to_value(
                            self.unit_system, 'LENGTH', self.length_entered)
                    except:  # ValueError:
                        self.length_entered_value = 0.0  # invalid
                        # self.report({'INFO'}, "Operation not supported yet")
                else:
                    self.length_entered_value = 0.0

                return True

        return False

    def get_converted_length_str(self, length):
        if self.length_entered:
            pos = self.line_pos
            ret = self.length_entered[:pos] + '|' + self.length_entered[pos:]
        else:
            ret = convert_distance(length, self.uinfo)

        return ret

    def clear(self):
        self.length_entered = ''
        self.length_entered_value = 0.0
        self.line_pos = 0


class Constrain:
    def __init__(self, prefs, scene, obj):
        self.last_type = None
        self.last_vec = None
        self.rotMat = None
        self.preferences = prefs
        trans_orient = scene.transform_orientation_slots[0]
        self.orientation = [None, None]
        if trans_orient.type == 'LOCAL':
            self.orientation[0] = obj.matrix_world.to_3x3().transposed()
            self.orientation[1] = Matrix.Identity(3)
        else:
            self.orientation[0] = Matrix.Identity(3)
            self.orientation[1] = obj.matrix_world.to_3x3().transposed()

        self.orientation_id = 0
        self.center = Vector((0.0, 0.0, 0.0))
        self.center_2d = Vector((0.0, 0.0))
        self.projected_vecs = Matrix(([0.0, 0.0], [0.0, 0.0], [0.0, 0.0]))

    def _constrain_set(self, mcursor):
        vec = (mcursor - self.center_2d)
        vec.normalize()

        dot_x = abs(vec.dot(self.projected_vecs[0]))
        dot_y = abs(vec.dot(self.projected_vecs[1]))
        dot_z = abs(vec.dot(self.projected_vecs[2]))

        if dot_x > dot_y and dot_x > dot_z:
            vec = self.orientation[self.orientation_id][0]
            type = 'X'

        elif dot_y > dot_x and dot_y > dot_z:
            vec = self.orientation[self.orientation_id][1]
            type = 'Y'

        else:  # dot_z > dot_y and dot_z > dot_x:
            vec = self.orientation[self.orientation_id][2]
            type = 'Z'

        return vec, type

    def modal(self, event, shift_callback):
        type = event.type
        if self.last_type == type:
            self.orientation_id += 1

        if type == 'X':
            if self.orientation_id < 2:
                self.last_vec = self.orientation[self.orientation_id][0]
            else:
                self.orientation_id = 0
                self.last_vec = type = None
        elif type == 'Y':
            if self.orientation_id < 2:
                self.last_vec = self.orientation[self.orientation_id][1]
            else:
                self.orientation_id = 0
                self.last_vec = type = None
        elif type == 'Z':
            if self.orientation_id < 2:
                self.last_vec = self.orientation[self.orientation_id][2]
            else:
                self.orientation_id = 0
                self.last_vec = type = None
        elif shift_callback and type in {'RIGHT_SHIFT', 'LEFT_SHIFT'}:
            if self.orientation_id < 1:
                type = 'shift'
                self.last_vec = shift_callback()
            else:
                self.orientation_id = 0
                self.last_vec = type = None
        else:
            return False

        self.preferences.auto_constrain = False
        self.last_type = type
        return True

    def toggle(self):
        self.rotMat = None  # update
        if self.preferences.auto_constrain:
            self.orientation_id = (self.orientation_id + 1) % 2
            self.preferences.auto_constrain = self.orientation_id != 0
        else:
            self.preferences.auto_constrain = True

    def update(self, region, rv3d, mcursor, center):
        if rv3d.view_matrix != self.rotMat or self.center != center:
            self.rotMat = rv3d.view_matrix.copy()

            self.center = center.copy()
            self.center_2d = location_3d_to_region_2d(
                region, rv3d, self.center)

            vec = self.center + self.orientation[self.orientation_id][0]
            self.projected_vecs[0] = location_3d_to_region_2d(
                region, rv3d, vec) - self.center_2d
            vec = self.center + self.orientation[self.orientation_id][1]
            self.projected_vecs[1] = location_3d_to_region_2d(
                region, rv3d, vec) - self.center_2d
            vec = self.center + self.orientation[self.orientation_id][2]
            self.projected_vecs[2] = location_3d_to_region_2d(
                region, rv3d, vec) - self.center_2d

            self.projected_vecs[0].normalize()
            self.projected_vecs[1].normalize()
            self.projected_vecs[2].normalize()

        return self._constrain_set(mcursor)


class SnapUtilities:
    """
    __slots__ = (
        "sctx",
        "draw_cache",
        "outer_verts",
        "unit_system",
        "rd",
        "obj",
        "bm",
        "geom",
        "type",
        "location",
        "preferences",
        "normal",
        "snap_vert",
        "snap_edge",
        "snap_face",
        "incremental",
    )
    """

    constrain_keys = {
        'X': Vector((1, 0, 0)),
        'Y': Vector((0, 1, 0)),
        'Z': Vector((0, 0, 1)),
        'RIGHT_SHIFT': 'shift',
        'LEFT_SHIFT': 'shift',
    }

    snapwidgets = []
    constrain = None

    @staticmethod
    def set_contrain(context, key):
        widget = SnapUtilities.snapwidgets[-1] if SnapUtilities.snapwidgets else None
        if SnapUtilities.constrain == key:
            SnapUtilities.constrain = None
            if hasattr(widget, "get_normal"):
                widget.get_normal(context)
            return

        if hasattr(widget, "normal"):
            if key == 'shift':
                import bmesh
                if isinstance(widget.geom, bmesh.types.BMEdge):
                    verts = widget.geom.verts
                    widget.normal = verts[1].co - verts[0].co
                    widget.normal.normalise()
                else:
                    return
            else:
                widget.normal = SnapUtilities.constrain_keys[key]

        SnapUtilities.constrain = key

    def snap_context_update_and_return_moving_objects(self, context):
        moving_objects = set()
        moving_snp_objects = set()
        children = set()
        for obj in context.view_layer.objects.selected:
            moving_objects.add(obj)

        temp_children = set()
        for obj in context.visible_objects:
            temp_children.clear()
            while obj.parent is not None:
                temp_children.add(obj)
                parent = obj.parent
                if parent in moving_objects:
                    children.update(temp_children)
                    temp_children.clear()
                obj = parent

        del temp_children

        moving_objects.difference_update(children)

        self.sctx.clear_snap_objects(True)

        for obj in context.visible_objects:
            is_moving = obj in moving_objects or obj in children
            snap_obj = self.sctx.add_obj(obj, obj.matrix_world)
            if is_moving:
                moving_snp_objects.add(snap_obj)

            if obj.instance_type == 'COLLECTION':
                mat = obj.matrix_world.copy()
                for ob in obj.instance_collection.objects:
                    snap_obj = self.sctx.add_obj(ob, mat @ ob.matrix_world)
                    if is_moving:
                        moving_snp_objects.add(snap_obj)

        del children
        return moving_objects, moving_snp_objects

    def snap_context_update(self, context):
        def visible_objects_and_duplis():
            if self.preferences.outer_verts:
                for obj in context.visible_objects:
                    yield (obj, obj.matrix_world)

                    if obj.instance_type == 'COLLECTION':
                        mat = obj.matrix_world.copy()
                        for ob in obj.instance_collection.objects:
                            yield (ob, mat @ ob.matrix_world)
            else:
                for obj in context.objects_in_mode_unique_data:
                    yield (obj, obj.matrix_world)

        self.sctx.clear_snap_objects(True)

        for obj, matrix in visible_objects_and_duplis():
            self.sctx.add_obj(obj, matrix)

    def snap_context_init(self, context, snap_edge_and_vert=True):
        from .snap_context_l import global_snap_context_get

        # Create Snap Context
        self.sctx = global_snap_context_get(
            context.evaluated_depsgraph_get(), context.region, context.space_data)
        ui_scale = context.preferences.system.ui_scale
        self.sctx.set_pixel_dist(12 * ui_scale)

        if SnapUtilities.snapwidgets:
            widget = SnapUtilities.snapwidgets[-1]

            self.obj = widget.snap_obj.data[0] if widget.snap_obj else context.active_object
            self.bm = widget.bm
            self.geom = widget.geom
            self.type = widget.type
            self.location = widget.location
            self.preferences = widget.preferences
            self.draw_cache = widget.draw_cache
            if hasattr(widget, "normal"):
                self.normal = widget.normal

        else:
            # init these variables to avoid errors
            self.obj = context.active_object
            self.bm = None
            self.geom = None
            self.type = 'OUT'
            self.location = Vector()

            preferences = context.preferences.addons[__package__].preferences
            self.preferences = preferences

            # Init DrawCache
            self.draw_cache = SnapDrawn(
                preferences.out_color,
                preferences.face_color,
                preferences.edge_color,
                preferences.vert_color,
                preferences.center_color,
                preferences.perpendicular_color,
                preferences.constrain_shift_color,
                tuple(
                    context.preferences.themes[0].user_interface.axis_x) + (1.0,),
                tuple(
                    context.preferences.themes[0].user_interface.axis_y) + (1.0,),
                tuple(
                    context.preferences.themes[0].user_interface.axis_z) + (1.0,),
                self.sctx.rv3d,
                ui_scale)

        self.snap_vert = self.snap_edge = snap_edge_and_vert

        shading = context.space_data.shading
        self.snap_face = not (snap_edge_and_vert and (
            shading.show_xray or shading.type == 'WIREFRAME'))

        self.sctx.set_snap_mode(self.snap_vert, self.snap_edge, self.snap_face)

        # Configure the unit of measure
        unit_system = context.scene.unit_settings.system
        scale = context.scene.unit_settings.scale_length
        scale /= context.space_data.overlay.grid_scale
        self.rd = bpy.utils.units.to_value(
            unit_system, 'LENGTH', str(1 / scale))

        self.incremental = bpy.utils.units.to_value(
            unit_system, 'LENGTH', str(self.preferences.incremental))

    def snap_to_grid(self):
        if self.type == 'OUT' and self.preferences.increments_grid:
            loc = self.location / self.rd
            self.location = Vector((round(loc.x),
                                    round(loc.y),
                                    round(loc.z))) * self.rd

    def snap_context_free(self):
        self.sctx = None
        del self.sctx

        del self.bm
        del self.draw_cache
        del self.geom
        del self.location
        del self.rd
        del self.snap_face
        del self.snap_obj
        del self.type

        del self.preferences

        SnapUtilities.constrain = None
