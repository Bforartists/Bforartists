# SPDX-FileCopyrightText: 2015 Pratik Solanki (Draguu)
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
from bpy.types import Operator, Panel

from . import sun
from .presets import (DYNSKY_MT_presets, DYNSKY_OT_preset_save, NEW_TILE,
                      SKY_DEFAULTS, bundled_active, is_bundled_preset,
                      preset_files, sky_index, thumb_icon_id)
from .sky import SKY_VERSION


def is_sky_world(world):
    return bool(world and world.node_tree
                and (world.get("dynamic_sky_version") is not None
                     or "Sky_normal" in world.node_tree.nodes))


def find_sky_world(context):
    # The active world whenever it's structurally a Dynamic Sky — renames
    # don't matter, and any sky world works, not just the last created one.
    # Otherwise fall back to the stored name, then to any sky in the file.
    world = context.scene.world
    if is_sky_world(world):
        return world
    named = bpy.data.worlds.get(context.scene.dynamic_sky_name)
    if is_sky_world(named):
        return named
    for world in bpy.data.worlds:
        if is_sky_world(world):
            return world
    return None


# --- World properties (registered in __init__) ---------------------------
# The clouds toggle stays a stateless view over its socket. The background
# mode is REAL stored state: deriving it from the blend value made the tab
# jump to HDRI/Procedural whenever the Hybrid blend hit 1.0/0.0, and Hybrid
# always re-entered at 0.5 — both irritated users. sync_background_mode()
# in sky.py re-aligns the stored mode after programmatic socket writes
# (presets, reset, bake).

def _socket(world, node_name, index=0):
    if world and world.node_tree:
        node = world.node_tree.nodes.get(node_name)
        if node is not None:
            return node.inputs[index]
    return None


def _background_mode_update(world, _context):
    socket = _socket(world, "Sky_HDRI_blend")
    if socket is None:
        return
    mode = world.dynsky_background_mode
    if mode == 'HYBRID':
        # Re-enter at the last used blend, not a hardcoded default
        if socket.default_value != world.dynsky_hybrid_blend:
            socket.default_value = world.dynsky_hybrid_blend
    else:
        # Remember a mid-range blend for the next Hybrid visit
        if 0.0 < socket.default_value < 1.0:
            world.dynsky_hybrid_blend = socket.default_value
        target = 0.0 if mode == 'PROCEDURAL' else 1.0
        if socket.default_value != target:
            socket.default_value = target


def _clouds_over_get(world):
    socket = _socket(world, "Clouds_over_HDRI")
    return bool(socket is not None and socket.default_value > 0.5)


def _clouds_over_set(world, value):
    socket = _socket(world, "Clouds_over_HDRI")
    if socket is not None:
        socket.default_value = 1.0 if value else 0.0


# --- shared draw helpers -------------------------------------------------

def card_layout(layout):
    # The mockup card look: label column left, value column right,
    # checkboxes indented, no animate-decorator dots
    layout.use_property_split = True
    layout.use_property_decorate = False
    return layout


def queue_image_preview(image):
    # ID previews can't be created during draw; make it on the next tick
    def ensure(image=image):
        try:
            image.preview_ensure()
        except ReferenceError:
            pass
        return None
    bpy.app.timers.register(ensure)


def sky_prop(col, nodes, name, collection, index, text):
    node = nodes.get(name)
    if node is None:
        col.label(text="Missing node: {}".format(name), icon='ERROR')
        return
    i, sub = sky_index(index)
    socket = getattr(node, collection)[i]
    if sub is None:
        col.prop(socket, "default_value", text=text)
    else:
        col.prop(socket, "default_value", index=sub, text=text)


def draw_section(col, nodes, section):
    for name, collection, index, _default, row_section, label in SKY_DEFAULTS:
        if row_section == section:
            sky_prop(col, nodes, name, collection, index, label)


def draw_preset_grid(col, context):
    active = DYNSKY_MT_presets.bl_label.lower()
    grid = col.grid_flow(row_major=True, columns=4, even_columns=True,
                         even_rows=True)
    for display, path in preset_files():
        cell = grid.column(align=True)
        icon_id = thumb_icon_id(path)
        if icon_id:
            cell.template_icon(icon_value=icon_id, scale=3.0)
        cell.operator("dynsky.preset_apply", text=display,
                      depress=(display.lower() == active)).filepath = path
    # Document-model flow: a new preset starts from defaults, then one-click
    # saves overwrite it
    cell = grid.column(align=True)
    new_icon = thumb_icon_id(NEW_TILE)
    if new_icon:
        cell.template_icon(icon_value=new_icon, scale=3.0)
    cell.operator("dynsky.preset_add", text="New")
    row = col.row(align=True)
    row.menu("DYNSKY_MT_presets", text="", icon='DOWNARROW_HLT')
    row.operator("dynsky.preset_save", text="", icon='FILE_TICK')
    row.operator("dynsky.preset_duplicate", text="", icon='DUPLICATE')
    row.operator("dynsky.preset_delete", text="", icon='TRASH')
    if bundled_active():
        # Bundled presets are locked templates; the sections below gray out
        col.label(text="Bundled preset — duplicate to edit", icon='LOCKED')


class DYNSKY_OT_world_remove(Operator):
    bl_idname = "dynsky.world_remove"
    bl_label = "Delete Dynamic Sky"
    bl_description = "Delete this Dynamic Sky world"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return is_sky_world(context.scene.world)

    def execute(self, context):
        bpy.data.worlds.remove(context.scene.world)
        return {'FINISHED'}


# --- panels --------------------------------------------------------------

class DYNSKY_PT_main(Panel):
    bl_label = "Dynamic Sky"
    bl_idname = "DYNSKY_PT_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "Dynamic Sky"

    def draw(self, context):
        layout = self.layout
        world = find_sky_world(context)
        if world is None:
            layout.label(text="No Dynamic Sky world in this file", icon='INFO')
            layout.operator("sky.dyn", text="Create Dynamic Sky",
                            icon='MAT_SPHERE_SKY')
            return
        if world != context.scene.world:
            layout.label(text="No Dynamic Sky world is active", icon='INFO')
            layout.operator("dynsky.use_world", icon='WORLD',
                            text='Use "{:s}"'.format(world.name)).name = world.name
            layout.operator("sky.dyn", text="Create New", icon='ADD')
            return

        row = layout.row(align=True)
        row.prop(world, "name", text="", icon='MAT_SPHERE_SKY')
        row.operator("dynsky.world_remove", text="", icon='X')
        if world.get("dynamic_sky_version", 0) < SKY_VERSION:
            # e.g. an old world appended after load, which no handler sees
            layout.operator("dynsky.migrate", icon='FILE_REFRESH')


class _SkySubPanel:
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = "Dynamic Sky"
    bl_parent_id = "DYNSKY_PT_tools"

    @classmethod
    def poll(cls, context):
        return is_sky_world(context.scene.world)


class DYNSKY_PT_presets(_SkySubPanel, Panel):
    # Collapsible so a big user preset collection can be folded away
    bl_label = "Presets"
    bl_order = 1

    def draw(self, context):
        draw_preset_grid(self.layout.column(), context)


class DYNSKY_PT_time(_SkySubPanel, Panel):
    # Headerless row between the preset grid and the sections
    bl_label = ""
    bl_order = 2
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        world = context.scene.world
        # Sliders can't render clock text; slider + formatted label instead,
        # as both 24-hour and 12-hour clocks
        row = card_layout(self.layout.row(align=True))
        row.prop(world, "dynamic_sky_time", text="Time of Day", slider=True)
        row.label(text="{:s} · {:s}".format(
            sun.format_time(world.dynamic_sky_time, 'H24'),
            sun.format_time(world.dynamic_sky_time, 'H12')))


class DYNSKY_PT_sun(_SkySubPanel, Panel):
    bl_label = "Sun"
    bl_order = 3

    def draw(self, context):
        layout = card_layout(self.layout)
        layout.enabled = not bundled_active()
        scene = context.scene
        nodes = scene.world.node_tree.nodes

        col = layout.column()
        col.prop(scene, "dynamic_sky_elevation")
        col.prop(scene, "dynamic_sky_azimuth")

        lamp = sun.active_lamp(scene)
        if lamp is None:
            for name, collection, index, _default, section, label in SKY_DEFAULTS:
                if section == "Sun" and name != "Sky_normal":
                    sky_prop(col, nodes, name, collection, index, label)
        else:
            light = lamp.data
            col.prop(light, "energy", text="Strength")
            col.prop(light, "color", text="")
            if hasattr(light, "use_temperature"):
                # ponytail: native light temperature is 4.4+; older Blender
                # simply doesn't get the row
                row = col.row(align=True)
                row.use_property_split = False
                row.prop(light, "use_temperature", text="")
                row.prop(light, "temperature", text="Temperature")
        col.prop(scene, "dynamic_sky_show_gizmo")

        # Sun list below the sliders (mockup order): entry 0 = the shader
        # sun, then tagged lamps by name
        split = layout.row()
        split.use_property_split = False
        col = split.column(align=True)
        names = ["Sky Sun"] + [lamp.name for lamp in sun.sun_lamps()]
        for i, name in enumerate(names):
            col.operator("dynsky.sun_select", text=name, icon='LIGHT_SUN',
                         depress=(i == scene.dynamic_sky_sun_index)).index = i
        side = split.column(align=True)
        side.operator("dynsky.sun_add", text="", icon='ADD')
        side.operator("dynsky.sun_remove", text="", icon='REMOVE')


class DYNSKY_PT_background(_SkySubPanel, Panel):
    bl_label = "Background"
    bl_order = 4

    def draw(self, context):
        layout = card_layout(self.layout)
        layout.enabled = not bundled_active()
        world = context.scene.world
        nodes = world.node_tree.nodes

        tabs = layout.row(align=True)
        tabs.use_property_split = False
        tabs.prop(world, "dynsky_background_mode", expand=True)
        col = layout.column()
        mode = world.dynsky_background_mode
        if mode != 'PROCEDURAL':
            env = nodes.get("Environment_Texture")
            if env is not None:
                plain = col.column()
                plain.use_property_split = False
                if env.image is not None:
                    # Wide panorama strip of the loaded HDRI, mockup style
                    if env.image.preview is not None:
                        plain.template_icon(
                            icon_value=env.image.preview.icon_id, scale=8.0)
                    else:
                        queue_image_preview(env.image)
                plain.template_ID(env, "image", open="image.open")
                if env.image is None:
                    col.label(text="No HDRI image loaded", icon='ERROR')
            else:
                col.label(text="Missing node: Environment_Texture", icon='ERROR')
            sky_prop(col, nodes, "HDRI_rotation", "inputs", (2, 2), "Rotation")
            if mode == 'HYBRID':
                sky_prop(col, nodes, "Sky_HDRI_blend", "inputs", 0, "Blend")
        sky_prop(col, nodes, "Scene_Brightness", "inputs", 1, "Strength")
        if mode != 'PROCEDURAL':
            col.prop(world, "dynsky_clouds_over_hdri",
                     text="Procedural clouds over")
            # "Sun follows HDRI" is wishlist: needs sun detection in the image


class DYNSKY_PT_atmosphere(_SkySubPanel, Panel):
    bl_label = "Atmosphere"
    bl_order = 5
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = card_layout(self.layout)
        layout.enabled = not bundled_active()
        draw_section(layout.column(),
                     context.scene.world.node_tree.nodes, "Atmosphere")


class DYNSKY_PT_clouds(_SkySubPanel, Panel):
    bl_label = "Clouds & Weather"
    bl_order = 6
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = card_layout(self.layout)
        layout.enabled = not bundled_active()
        draw_section(layout.column(),
                     context.scene.world.node_tree.nodes, "Clouds")


class DYNSKY_PT_night(_SkySubPanel, Panel):
    bl_label = "Night Sky"
    bl_order = 7
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = card_layout(self.layout)
        layout.enabled = not bundled_active()
        draw_section(layout.column(),
                     context.scene.world.node_tree.nodes, "Night")


class DYNSKY_PT_footer(_SkySubPanel, Panel):
    bl_label = ""
    bl_order = 8
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        row = self.layout.row(align=True)
        row.operator("dynsky.sky_reset", text="Reset", icon='LOOP_BACK')
        # Contextual middle slot: user preset -> quick save; bundled (locked)
        # preset -> duplicate into an editable copy
        path = DYNSKY_OT_preset_save.active_preset_path()
        if path and is_bundled_preset(path):
            row.operator("dynsky.preset_duplicate", text="Duplicate",
                         icon='DUPLICATE')
        elif path:
            row.operator("dynsky.preset_save", text="Save", icon='FILE_TICK')
        row.operator("dynsky.bake_world", text="Bake to World", icon='WORLD_DATA')
        row.operator("dynsky.export_hdri", text="Export HDRI", icon='EXPORT')
