# -*- coding:utf-8 -*-

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
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110- 1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# Author: Stephen Leger (s-leger)
# Inspired by Asset-Flinguer
# ----------------------------------------------------------
import sys
from mathutils import Vector
import bpy


def log(s):
    print("[log]" + s)


def create_lamp(context, loc):
    bpy.ops.object.light_add(
        type='POINT',
        radius=1,
        view_align=False,
        location=loc)
    lamp = context.active_object
    lamp.data.use_nodes = True
    tree = lamp.data.node_tree
    return tree, tree.nodes, lamp.data


def create_camera(context, loc, rot):
    bpy.ops.object.camera_add(
        view_align=True,
        enter_editmode=False,
        location=loc,
        rotation=rot)
    cam = context.active_object
    context.scene.camera = cam
    return cam


def get_center(o):
    x, y, z = o.bound_box[0]
    min_x = x
    min_y = y
    min_z = z
    x, y, z = o.bound_box[6]
    max_x = x
    max_y = y
    max_z = z
    return Vector((
        min_x + 0.5 * (max_x - min_x),
        min_y + 0.5 * (max_y - min_y),
        min_z + 0.5 * (max_z - min_z)))


def apply_simple_material(o, name, color):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes[1].inputs[0].default_value = color
    o.data.materials.append(m)


# /home/stephen/blender-28-git/build_linux_full/bin/blender --background --factory-startup -noaudio --python /home/stephen/blender-28-git/build_linux_full/bin/2.80/scripts/addons/archipack/archipack_thumbs.py -- addon:archipack matlib:/medias/stephen/DATA/lib/ cls:roof preset:/home/stephen/.config/blender/2.80/scripts/presets/archipack_roof/square.py


def generateThumb(context, cls, preset, engine):
    log("### RENDER THUMB ############################")

    # Cleanup scene
    for o in context.scene.objects:
        o.select_set(state=True)

    bpy.ops.object.delete()

    log("Start generating: %s" % cls)

    # setup render

    context.scene.render.engine = engine

    if engine == 'CYCLES':
        cycles = context.scene.cycles
        cycles.progressive = 'PATH'
        cycles.samples = 24
        try:
            cycles.use_square_samples = True
        except:
            pass
        cycles.preview_samples = 24
        cycles.aa_samples = 24
        cycles.transparent_max_bounces = 8
        cycles.transparent_min_bounces = 8
        cycles.transmission_bounces = 8
        cycles.max_bounces = 8
        cycles.min_bounces = 6
        cycles.caustics_refractive = False
        cycles.caustics_reflective = False
        cycles.use_transparent_shadows = True
        cycles.diffuse_bounces = 1
        cycles.glossy_bounces = 4

    elif engine == 'BLENDER_EEVEE':
        eevee = context.scene.eevee
        eevee.use_gtao = True
        eevee.use_ssr = True
        eevee.use_soft_shadows = True
        eevee.taa_render_samples = 64
    else:
        raise RuntimeError("Unsupported render engine %s" % engine)

    render = context.scene.render

    # engine settings
    render.resolution_x = 150
    render.resolution_y = 100
    render.filepath = preset[:-3] + ".png"

    # create object, loading preset
    getattr(bpy.ops.archipack, cls)('INVOKE_DEFAULT', filepath=preset, auto_manipulate=False)
    o = context.active_object
    size = o.dimensions
    center = get_center(o)

    # opposite / tan (0.5 * fov)  where fov is 49.134 deg
    dist = max(size) / 0.32
    loc = center + dist * Vector((-0.5, -1, 0.5)).normalized()

    log("Prepare camera")
    cam = create_camera(context, loc, (1.150952, 0.0, -0.462509))
    cam.data.lens = 50

    for ob in context.scene.objects:
        ob.select_set(state=False)

    o.select_set(state=True)

    bpy.ops.view3d.camera_to_view_selected()
    cam.data.lens = 45

    log("Prepare scene")
    # add plane
    bpy.ops.mesh.primitive_plane_add(
        size=1000,
        view_align=False,
        enter_editmode=False,
        location=(0, 0, 0)
    )

    p = context.active_object
    apply_simple_material(p, "Plane", (1, 1, 1, 1))

    # add 3 lights
    tree, nodes, lamp = create_lamp(context, (3.69736, -7, 6.0))
    lamp.energy = 50
    emit = nodes["Emission"]
    emit.inputs[1].default_value = 2000.0

    tree, nodes, lamp = create_lamp(context, (9.414563179016113, 5.446230888366699, 5.903861999511719))
    emit = nodes["Emission"]
    falloff = nodes.new(type="ShaderNodeLightFalloff")
    falloff.inputs[0].default_value = 5
    tree.links.new(falloff.outputs[2], emit.inputs[1])

    tree, nodes, lamp = create_lamp(context, (-7.847615718841553, 1.03135085105896, 5.903861999511719))
    emit = nodes["Emission"]
    falloff = nodes.new(type="ShaderNodeLightFalloff")
    falloff.inputs[0].default_value = 5
    tree.links.new(falloff.outputs[2], emit.inputs[1])

    # Set output filename.
    render.use_file_extension = True
    render.use_overwrite = True
    render.use_compositing = False
    render.use_sequencer = False
    render.resolution_percentage = 100
    # render.image_settings.file_format = 'PNG'
    # render.image_settings.color_mode = 'RGBA'
    # render.image_settings.color_depth = '8'

    # Configure output size.
    log("Render")

    # Render thumbnail
    bpy.ops.render.render(write_still=True)

    log("### COMPLETED ############################")


if __name__ == "__main__":

    preset = ""
    engine = 'BLENDER_EEVEE' #'CYCLES'
    for arg in sys.argv:
        if arg.startswith("cls:"):
            cls = arg[4:]
        if arg.startswith("preset:"):
            preset = arg[7:]
        if arg.startswith("matlib:"):
            matlib = arg[7:]
        if arg.startswith("addon:"):
            module = arg[6:]
        if arg.startswith("engine:"):
            engine = arg[7:]
    try:
        # log("### ENABLE %s ADDON ############################" % module)
        bpy.ops.wm.addon_enable(module=module)
        # log("### MATLIB PATH ############################")
        bpy.context.preferences.addons[module].preferences.matlib_path = matlib
    except:
        raise RuntimeError("module name not found")
    # log("### GENERATE ############################")
    generateThumb(bpy.context, cls, preset, engine)
