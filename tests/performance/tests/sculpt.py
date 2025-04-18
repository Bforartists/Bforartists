# SPDX-FileCopyrightText: 2024 Blender Authors
#
# SPDX-License-Identifier: Apache-2.0

import api
import enum
import pathlib


class SculptMode(enum.IntEnum):
    MESH = 1
    MULTIRES = 2
    DYNTOPO = 3


class BrushType(enum.Enum):
    DRAW = "Draw"
    CLAY_STRIPS = "Clay Strips"
    SMOOTH = "Smooth"


def set_view3d_context_override(context_override):
    """
    Set context override to become the first viewport in the active workspace

    The ``context_override`` is expected to be a copy of an actual current context
    obtained by `context.copy()`
    """

    for area in context_override["screen"].areas:
        if area.type != 'VIEW_3D':
            continue
        for space in area.spaces:
            if space.type != 'VIEW_3D':
                continue
            for region in area.regions:
                if region.type != 'WINDOW':
                    continue
                context_override["area"] = area
                context_override["region"] = region


def prepare_sculpt_scene(context: any, mode: SculptMode):
    """
    Prepare a clean state of the scene suitable for benchmarking

    It creates a high-res object and moves it to a sculpt mode.

    For dyntopo & normal mesh sculpting, we create a grid with 2.2M vertices.
    For multires sculpting, we create a grid with 22k vertices - with a multires
    modifier set to level 3, this results in an equivalent number of 2.2M vertices
    inside sculpt mode.
    """
    import bpy

    # Ensure the current mode is object, as it might not be the always the case
    # if the benchmark script is run from a non-clean state of the .blend file.
    if context.object:
        bpy.ops.object.mode_set(mode='OBJECT')

    # Delete all current objects from the scene.
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.outliner.orphans_purge()

    group = bpy.data.node_groups.new("Test", 'GeometryNodeTree')
    group.interface.new_socket("Geometry", in_out='OUTPUT', socket_type='NodeSocketGeometry')
    group_output_node = group.nodes.new('NodeGroupOutput')

    if mode == SculptMode.MESH:
        size = 1500
    elif mode == SculptMode.MULTIRES:
        size = 150
    elif mode == SculptMode.DYNTOPO:
        size = 1500
    else:
        raise NotImplementedError

    grid_node = group.nodes.new('GeometryNodeMeshGrid')
    grid_node.inputs["Size X"].default_value = 2.0
    grid_node.inputs["Size Y"].default_value = 2.0
    grid_node.inputs["Vertices X"].default_value = size
    grid_node.inputs["Vertices Y"].default_value = size

    group.links.new(grid_node.outputs["Mesh"], group_output_node.inputs[0])

    bpy.ops.mesh.primitive_plane_add(size=2, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))

    ob = context.object
    md = ob.modifiers.new("Test", 'NODES')
    md.node_group = group

    bpy.ops.object.modifier_apply(modifier="Test")

    bpy.ops.object.select_all(action='SELECT')
    # Move the plane to the sculpt mode.
    bpy.ops.object.mode_set(mode='SCULPT')

    if mode == SculptMode.MULTIRES:
        bpy.ops.object.subdivision_set(level=3)
    elif mode == SculptMode.DYNTOPO:
        bpy.ops.sculpt.dynamic_topology_toggle()


def prepare_brush(context: any, brush_type: BrushType):
    """Activates and sets common brush settings"""
    import bpy
    bpy.ops.brush.asset_activate(
        asset_library_type='ESSENTIALS',
        relative_asset_identifier='brushes/essentials_brushes-mesh_sculpt.blend/Brush/' +
                                  brush_type.value)

    # Reduce the brush strength to avoid deforming the mesh too much and influencing multiple strokes
    context.tool_settings.sculpt.brush.strength = 0.1


def generate_stroke(context):
    """
    Generate stroke for the bpy.ops.sculpt.brush_stroke operator

    The generated stroke coves the full plane diagonal.
    """
    import bpy
    from mathutils import Vector

    template = {
        "name": "stroke",
        "mouse": (0.0, 0.0),
        "mouse_event": (0, 0),
        "is_start": True,
        "location": (0, 0, 0),
        "pressure": 1.0,
        "time": 1.0,
        "size": 1.0,
        "x_tilt": 0,
        "y_tilt": 0
    }

    version = bpy.app.version
    if version[0] <= 4 and version[1] <= 3:
        template["pen_flip"] = False

    num_steps = 100
    start = Vector((context['area'].width, context['area'].height))
    end = Vector((0, 0))
    delta = (end - start) / (num_steps - 1)

    stroke = []
    for i in range(num_steps):
        step = template.copy()
        step["mouse_event"] = start + delta * i
        stroke.append(step)

    return stroke


def _run_brush_test(args: dict):
    import bpy
    import time
    context = bpy.context

    timeout = 5
    total_time_start = time.time()

    # Create an undo stack explicitly. This isn't created by default in background mode.
    bpy.ops.ed.undo_push()

    prepare_sculpt_scene(context, args['mode'])
    prepare_brush(context, args['brush_type'])

    context_override = context.copy()
    set_view3d_context_override(context_override)

    min_measurements = 5
    max_measurements = 100

    measurements = []
    while True:
        with context.temp_override(**context_override):
            start = time.time()
            bpy.ops.sculpt.brush_stroke(stroke=generate_stroke(context_override), override_location=True)
            measurements.append(time.time() - start)

        if len(measurements) >= min_measurements and (time.time() - total_time_start) > timeout:
            break
        if len(measurements) >= max_measurements:
            break

    return sum(measurements) / len(measurements)


def _run_bvh_test(args: dict):
    import bpy
    import time
    context = bpy.context

    timeout = 5
    total_time_start = time.time()

    # Create an undo stack explicitly. This isn't created by default in background mode.
    bpy.ops.ed.undo_push()

    prepare_sculpt_scene(context, args['mode'])

    context_override = context.copy()
    set_view3d_context_override(context_override)

    min_measurements = 5
    max_measurements = 100

    measurements = []
    while True:
        with context.temp_override(**context_override):
            start = time.time()
            bpy.ops.sculpt.optimize()
            measurements.append(time.time() - start)

        if len(measurements) >= min_measurements and (time.time() - total_time_start) > timeout:
            break
        if len(measurements) >= max_measurements:
            break

    return sum(measurements) / len(measurements)


class SculptBrushTest(api.Test):
    def __init__(self, filepath: pathlib.Path, mode: SculptMode, brush_type: BrushType):
        self.filepath = filepath
        self.mode = mode
        self.brush_type = brush_type

    def name(self):
        return "{}_{}".format(self.mode.name.lower(), self.brush_type.name.lower())

    def category(self):
        return "sculpt"

    def run(self, env, _device_id):
        args = {
            'mode': self.mode,
            'brush_type': self.brush_type,
        }

        result, _ = env.run_in_blender(_run_brush_test, args, [self.filepath])

        return {'time': result}


class SculptRebuildBVHTest(api.Test):
    def __init__(self, filepath: pathlib.Path, mode: SculptMode):
        self.filepath = filepath
        self.mode = mode

    def name(self):
        return "{}_rebuild_bvh".format(self.mode.name.lower())

    def category(self):
        return "sculpt"

    def run(self, env, _device_id):
        args = {
            'mode': self.mode,
        }

        result, _ = env.run_in_blender(_run_bvh_test, args, [self.filepath])

        return {'time': result}


def generate(env):
    filepaths = env.find_blend_files('sculpt/*')
    # For now, we only expect there to ever be a single file to use as the basis for generating other brush tests
    assert len(filepaths) == 1
    brush_tests = [SculptBrushTest(filepaths[0], mode, brush_type) for mode in SculptMode for brush_type in BrushType]
    bvh_tests = [SculptRebuildBVHTest(filepaths[0], mode) for mode in SculptMode]
    return brush_tests + bvh_tests
