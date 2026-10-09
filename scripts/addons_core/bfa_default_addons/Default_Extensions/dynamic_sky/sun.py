# SPDX-FileCopyrightText: 2015 Pratik Solanki (Draguu)
#
# SPDX-License-Identifier: GPL-2.0-or-later

from math import asin, atan2, cos, degrees, radians, sin, sqrt

import bpy
from bpy.app.handlers import persistent
from bpy.props import IntProperty
from bpy.types import GizmoGroup, Operator
from mathutils import Matrix, Vector

from .presets import sky_world_ok

# Real sun lamps managed by the add-on carry this ID property; the sun list
# is entry 0 = the shader sun (always), then tagged lamps sorted by name.
SUN_TAG = "dynamic_sky_sun"


# --- pure math helpers (headless-testable, no bpy.context) ---------------

def sun_vector(elevation, azimuth):
    # Radians -> unit vector toward the sun.
    # Azimuth 0 = north (+Y), 90 deg = east (+X): compass-clockwise.
    ch = cos(elevation)
    return (sin(azimuth) * ch, cos(azimuth) * ch, sin(elevation))


def elev_azim(v):
    # Inverse of sun_vector for any non-zero vector
    x, y, z = v[0], v[1], v[2]
    length = sqrt(x * x + y * y + z * z)
    if length == 0.0:
        return 0.0, 0.0
    return asin(max(-1.0, min(1.0, z / length))), atan2(x, y)


def time_to_elev_azim(hours):
    # ponytail: flat arc model (rise 6:00, noon 12:00, set 18:00);
    # a geographic lat/long/date model is the upgrade path
    return radians(90.0 - abs(hours - 12.0) * 15.0), radians(hours * 15.0)


def direction_to_time(v):
    # Nearest arc time for any sun direction: elevation fixes |h - 12|,
    # the azimuth picks morning vs afternoon (near-ties go to afternoon)
    elevation, azimuth = elev_azim(v)
    dt = (90.0 - degrees(elevation)) / 15.0
    morning, afternoon = 12.0 - dt, 12.0 + dt

    def azim_dist(hours):
        d = abs(degrees(azimuth) % 360.0 - (hours * 15.0) % 360.0)
        return min(d, 360.0 - d)

    hours = morning if azim_dist(morning) + 1e-9 < azim_dist(afternoon) else afternoon
    return min(max(hours, 0.0), 24.0)


def format_time(hours, mode):
    # mode 'H24' -> "17:42", 'H12' -> "5:42 PM"
    total = int(round(hours * 60.0)) % (24 * 60)
    h, m = divmod(total, 60)
    if mode == 'H12':
        suffix = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return "{:d}:{:02d} {:s}".format(h12, m, suffix)
    return "{:d}:{:02d}".format(h, m)


# --- sun list ------------------------------------------------------------

def sun_lamps():
    return sorted((o for o in bpy.data.objects
                   if o.type == 'LIGHT' and o.data.type == 'SUN' and o.get(SUN_TAG)),
                  key=lambda o: o.name)


def active_lamp(scene):
    # None = the shader sun (index 0, or a stale out-of-range index)
    index = scene.dynamic_sky_sun_index - 1
    if index < 0:
        return None
    lamps = sun_lamps()
    return lamps[index] if index < len(lamps) else None


def _sky_ball(scene):
    world = scene.world
    if not (world and world.node_tree and "Sky_normal" in world.node_tree.nodes):
        return None
    return world.node_tree.nodes["Sky_normal"].outputs[0]


def _lamp_direction(obj):
    # ponytail: local rotation only - parenting/constraints/non-euler
    # rotation modes are ignored; we created these lamps with plain eulers
    return tuple(obj.rotation_euler.to_matrix().col[2])


def _aim_lamp(obj, elevation, azimuth):
    # Sun lamps emit along -Z, so track +Z toward the sun
    obj.rotation_euler = (Vector(sun_vector(elevation, azimuth))
                          .to_track_quat('Z', 'Y').to_euler())


def _active_direction(scene):
    lamp = active_lamp(scene)
    if lamp is not None:
        return _lamp_direction(lamp)
    ball = _sky_ball(scene)
    return tuple(ball.default_value) if ball is not None else None


def _set_active_direction(scene, elevation, azimuth):
    lamp = active_lamp(scene)
    if lamp is not None:
        _aim_lamp(lamp, elevation, azimuth)
        return
    ball = _sky_ball(scene)
    if ball is not None:
        ball.default_value = sun_vector(elevation, azimuth)


# Stateless Scene property callbacks: the sun's own storage (shader ball or
# lamp rotation) stays the single source of truth, so presets and old files
# that write the raw vector remain correct and nothing can feedback-loop.

def _elevation_get(scene):
    direction = _active_direction(scene)
    return elev_azim(direction)[0] if direction else 0.0


def _elevation_set(scene, value):
    direction = _active_direction(scene)
    if direction:
        _set_active_direction(scene, value, elev_azim(direction)[1])


def _azimuth_get(scene):
    direction = _active_direction(scene)
    return elev_azim(direction)[1] if direction else 0.0


def _azimuth_set(scene, value):
    direction = _active_direction(scene)
    if direction:
        _set_active_direction(scene, elev_azim(direction)[0], value)


# --- time of day ---------------------------------------------------------

# The ball stays the single source of truth, so presets that hand-place
# the sun can't leave a stale time behind. The last set time is kept as an
# idprop hint: one elevation maps to two arc times (morning/afternoon),
# and for an off-arc sun the azimuth can't break the tie — the hint can,
# but only while it still matches the ball's actual elevation (anything
# else rewrote the ball raw, so the hint is stale and gets ignored).

def _time_get(world):
    nt = world.node_tree
    if not (nt and "Sky_normal" in nt.nodes):
        return 12.0
    ball = nt.nodes["Sky_normal"].outputs[0].default_value
    stored = world.get("dynamic_sky_time")
    if (stored is not None
            and abs(time_to_elev_azim(stored)[0] - elev_azim(ball)[0]) < 1e-3):
        return stored
    return direction_to_time(ball)


def _time_set(world, hours):
    # ponytail: time drives the shader sun only; per-lamp offsets if ever needed
    if world.library is not None:
        return
    nt = world.node_tree
    if not (nt and "Sky_normal" in nt.nodes):
        return
    ball = nt.nodes["Sky_normal"].outputs[0]
    x, y, z = ball.default_value[0], ball.default_value[1], ball.default_value[2]
    # Keep the sun's azimuth offset from the arc: a hand-placed (preset)
    # sun slides from where it is instead of teleporting onto the arc.
    # On-arc suns have offset 0, so plain slider use and keyframed
    # animation sweep exactly as before. At the zenith azimuth is
    # meaningless, so no offset.
    offset = 0.0
    if x * x + y * y > 1e-8:
        offset = (elev_azim((x, y, z))[1]
                  - time_to_elev_azim(_time_get(world))[1])
    elevation, azimuth = time_to_elev_azim(hours)
    ball.default_value = sun_vector(elevation, azimuth + offset)
    world["dynamic_sky_time"] = hours


def _time_fcurve(anim):
    action = anim and anim.action
    if not action:
        return None
    fcurves = getattr(action, "fcurves", None)
    if fcurves is not None:
        # pre-slotted actions (Blender < 4.4, compat layer gone in 5.1)
        return next((f for f in fcurves if f.data_path == "dynamic_sky_time"), None)
    for layer in action.layers:
        for strip in layer.strips:
            bag = strip.channelbag(anim.action_slot)
            if bag is not None:
                fcurve = bag.fcurves.find("dynamic_sky_time")
                if fcurve is not None:
                    return fcurve
    return None


@persistent
def _sun_time_frame(scene, _depsgraph=None):
    # update= callbacks don't fire for animated properties, so evaluate the
    # time fcurve ourselves each frame and reassign (which does fire it)
    for world in bpy.data.worlds:
        fcurve = _time_fcurve(world.animation_data)
        if fcurve is not None:
            world.dynamic_sky_time = fcurve.evaluate(scene.frame_current)


# --- operators -----------------------------------------------------------

class DYNSKY_OT_sun_add(Operator):
    bl_idname = "dynsky.sun_add"
    bl_label = "Add Sun Light"
    bl_description = "Add a real sun lamp to the sky's sun list"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        light = bpy.data.lights.new("Sun", 'SUN')
        obj = bpy.data.objects.new(light.name, light)
        obj[SUN_TAG] = 1
        context.collection.objects.link(obj)
        hours = context.scene.world.dynamic_sky_time if context.scene.world else 12.0
        _aim_lamp(obj, *time_to_elev_azim(hours))
        context.scene.dynamic_sky_sun_index = 1 + sun_lamps().index(obj)
        return {'FINISHED'}


class DYNSKY_OT_sun_remove(Operator):
    bl_idname = "dynsky.sun_remove"
    bl_label = "Remove Sun Light"
    bl_description = "Remove the selected sun lamp (the sky sun can't be removed)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.scene.dynamic_sky_sun_index > 0

    def execute(self, context):
        obj = active_lamp(context.scene)
        if obj is None:
            context.scene.dynamic_sky_sun_index = 0
            return {'CANCELLED'}
        light = obj.data
        bpy.data.objects.remove(obj)
        if light.users == 0:
            bpy.data.lights.remove(light)
        context.scene.dynamic_sky_sun_index = min(
            context.scene.dynamic_sky_sun_index, len(sun_lamps()))
        return {'FINISHED'}


class DYNSKY_OT_sun_select(Operator):
    bl_idname = "dynsky.sun_select"
    bl_label = "Select Sun"
    bl_description = "Edit this sun's settings"

    index: IntProperty()

    def execute(self, context):
        context.scene.dynamic_sky_sun_index = self.index
        return {'FINISHED'}


# --- viewport gizmo ------------------------------------------------------

class DYNSKY_GGT_sun(GizmoGroup):
    bl_idname = "DYNSKY_GGT_sun"
    bl_label = "Dynamic Sky Sun"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'PERSISTENT'}

    @classmethod
    def poll(cls, context):
        return context.scene.dynamic_sky_show_gizmo and sky_world_ok(context)

    def setup(self, context):
        # ponytail: two fixed-size dials at the world origin; per-sun
        # placement and an arrow pointing at the sun are polish for later
        azim = self.gizmos.new("GIZMO_GT_dial_3d")
        azim.target_set_prop("offset", context.scene, "dynamic_sky_azimuth")
        elev = self.gizmos.new("GIZMO_GT_dial_3d")
        elev.target_set_prop("offset", context.scene, "dynamic_sky_elevation")
        for gz, color in ((azim, (0.8, 0.8, 0.2)), (elev, (0.2, 0.6, 0.9))):
            gz.color = color
            gz.alpha = 0.6
            gz.color_highlight = color
            gz.alpha_highlight = 1.0
            gz.use_draw_value = True
        self._azim, self._elev = azim, elev

    def draw_prepare(self, context):
        # Elevation dial stands in the vertical plane of the current azimuth
        azimuth = context.scene.dynamic_sky_azimuth
        self._elev.matrix_basis = (Matrix.Rotation(radians(90.0) - azimuth, 4, 'Z')
                                   @ Matrix.Rotation(radians(90.0), 4, 'X'))
