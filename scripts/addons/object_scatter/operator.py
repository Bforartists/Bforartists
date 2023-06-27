# SPDX-FileCopyrightText: 2018-2023 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import gpu
import blf
import math
import enum
import random

from itertools import islice
from mathutils.bvhtree import BVHTree
from mathutils import Vector, Matrix, Euler
from gpu_extras.batch import batch_for_shader

from bpy_extras.view3d_utils import (
    region_2d_to_vector_3d,
    region_2d_to_origin_3d
)


# Modal Operator
################################################################

class ScatterObjects(bpy.types.Operator):
    bl_idname = "object.scatter"
    bl_label = "Scatter Objects"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return (
            currently_in_3d_view(context)
            and context.active_object is not None
            and context.active_object.mode == 'OBJECT')

    def invoke(self, context, event):
        self.target_object = context.active_object
        self.objects_to_scatter = get_selected_non_active_objects(context)

        if self.target_object is None or len(self.objects_to_scatter) == 0:
            self.report({'ERROR'}, "Select objects to scatter and a target object")
            return {'CANCELLED'}

        self.base_scale = get_max_object_side_length(self.objects_to_scatter)

        self.targets = []
        self.active_target = None
        self.target_cache = {}

        self.enable_draw_callback()
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if not event_is_in_region(event, context.region) and self.active_target is None:
            return {'PASS_THROUGH'}

        if event.type == 'ESC':
            return self.finish('CANCELLED')

        if event.type == 'RET' and event.value == 'PRESS':
            self.create_scatter_object()
            return self.finish('FINISHED')

        event_used = self.handle_non_exit_event(event)
        if event_used:
            return {'RUNNING_MODAL'}
        else:
            return {'PASS_THROUGH'}

    def handle_non_exit_event(self, event):
        if self.active_target is None:
            if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
                self.active_target = StrokeTarget()
                self.active_target.start_build(self.target_object)
                return True
        else:
            build_state = self.active_target.continue_build(event)
            if build_state == BuildState.FINISHED:
                self.targets.append(self.active_target)
                self.active_target = None
            self.remove_target_from_cache(self.active_target)
            return True

        return False

    def enable_draw_callback(self):
        self._draw_callback_view = bpy.types.SpaceView3D.draw_handler_add(self.draw_view, (), 'WINDOW', 'POST_VIEW')
        self._draw_callback_px = bpy.types.SpaceView3D.draw_handler_add(self.draw_px, (), 'WINDOW', 'POST_PIXEL')

    def disable_draw_callback(self):
        bpy.types.SpaceView3D.draw_handler_remove(self._draw_callback_view, 'WINDOW')
        bpy.types.SpaceView3D.draw_handler_remove(self._draw_callback_px, 'WINDOW')

    def draw_view(self):
        for target in self.iter_targets():
            target.draw()

        draw_matrices_batches(list(self.iter_matrix_batches()))

    def draw_px(self):
        draw_text((20, 20, 0), "Instances: " + str(len(self.get_all_matrices())))

    def finish(self, return_value):
        self.disable_draw_callback()
        bpy.context.area.tag_redraw()
        return {return_value}

    def create_scatter_object(self):
        matrix_chunks = make_random_chunks(
            self.get_all_matrices(), len(self.objects_to_scatter))

        collection = bpy.data.collections.new("Scatter")
        bpy.context.collection.children.link(collection)

        for obj, matrices in zip(self.objects_to_scatter, matrix_chunks):
            make_duplicator(collection, obj, matrices)

    def get_all_matrices(self):
        settings = self.get_current_settings()

        matrices = []
        for target in self.iter_targets():
            self.ensure_target_is_in_cache(target)
            matrices.extend(self.target_cache[target].get_matrices(settings))
        return matrices

    def iter_matrix_batches(self):
        settings = self.get_current_settings()
        for target in self.iter_targets():
            self.ensure_target_is_in_cache(target)
            yield self.target_cache[target].get_batch(settings)

    def iter_targets(self):
        yield from self.targets
        if self.active_target is not None:
            yield self.active_target

    def ensure_target_is_in_cache(self, target):
        if target not in self.target_cache:
            entry = TargetCacheEntry(target, self.base_scale)
            self.target_cache[target] = entry

    def remove_target_from_cache(self, target):
        self.target_cache.pop(self.active_target, None)

    def get_current_settings(self):
        return bpy.context.scene.scatter_properties.to_settings()

class TargetCacheEntry:
    def __init__(self, target, base_scale):
        self.target = target
        self.last_used_settings = None
        self.base_scale = base_scale
        self.settings_changed()

    def get_matrices(self, settings):
        self._handle_new_settings(settings)
        if self.matrices is None:
            self.matrices = self.target.get_matrices(settings)
        return self.matrices

    def get_batch(self, settings):
        self._handle_new_settings(settings)
        if self.gpu_batch is None:
            self.gpu_batch = create_batch_for_matrices(self.get_matrices(settings), self.base_scale)
        return self.gpu_batch

    def _handle_new_settings(self, settings):
        if settings != self.last_used_settings:
            self.settings_changed()
        self.last_used_settings = settings

    def settings_changed(self):
        self.matrices = None
        self.gpu_batch = None


# Duplicator Creation
######################################################

def make_duplicator(target_collection, source_object, matrices):
    triangle_scale = 0.1

    duplicator = triangle_object_from_matrices(source_object.name + " Duplicator", matrices, triangle_scale)
    duplicator.instance_type = 'FACES'
    duplicator.use_instance_faces_scale = True
    duplicator.show_instancer_for_viewport = True
    duplicator.show_instancer_for_render = False
    duplicator.instance_faces_scale = 1 / triangle_scale

    copy_obj = source_object.copy()
    copy_obj.name = source_object.name + " - copy"
    copy_obj.location = (0, 0, 0)
    copy_obj.parent = duplicator

    target_collection.objects.link(duplicator)
    target_collection.objects.link(copy_obj)

def triangle_object_from_matrices(name, matrices, triangle_scale):
    mesh = triangle_mesh_from_matrices(name, matrices, triangle_scale)
    return bpy.data.objects.new(name, mesh)

def triangle_mesh_from_matrices(name, matrices, triangle_scale):
    mesh = bpy.data.meshes.new(name)
    vertices, polygons = mesh_data_from_matrices(matrices, triangle_scale)
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    mesh.validate()
    return mesh

unit_triangle_vertices = (
    Vector((-3**-0.25, -3**-0.75, 0)),
    Vector((3**-0.25, -3**-0.75, 0)),
    Vector((0, 2/3**0.75, 0)))

def mesh_data_from_matrices(matrices, triangle_scale):
    vertices = []
    polygons = []
    triangle_vertices = [triangle_scale * v for v in unit_triangle_vertices]

    for i, matrix in enumerate(matrices):
        vertices.extend((matrix @ v for v in triangle_vertices))
        polygons.append((i * 3 + 0, i * 3 + 1, i * 3 + 2))

    return vertices, polygons


# Target Provider
#################################################

class BuildState(enum.Enum):
    FINISHED = enum.auto()
    ONGOING = enum.auto()

class TargetProvider:
    def start_build(self, target_object):
        pass

    def continue_build(self, event):
        return BuildState.FINISHED

    def get_matrices(self, scatter_settings):
        return []

    def draw(self):
        pass

class StrokeTarget(TargetProvider):
    def start_build(self, target_object):
        self.points = []
        self.bvhtree = bvhtree_from_object(target_object)
        self.batch = None

    def continue_build(self, event):
        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            return BuildState.FINISHED

        mouse_pos = (event.mouse_region_x, event.mouse_region_y)
        location, *_ = shoot_region_2d_ray(self.bvhtree, mouse_pos)
        if location is not None:
            self.points.append(location)
            self.batch = None
        return BuildState.ONGOING

    def draw(self):
        if self.batch is None:
            self.batch = create_line_strip_batch(self.points)
        draw_line_strip_batch(self.batch, color=(1.0, 0.4, 0.1, 1.0), thickness=5)

    def get_matrices(self, scatter_settings):
        return scatter_around_stroke(self.points, self.bvhtree, scatter_settings)

def scatter_around_stroke(stroke_points, bvhtree, settings):
    scattered_matrices = []
    for point, local_seed in iter_points_on_stroke_with_seed(stroke_points, settings.density, settings.seed):
        matrix = scatter_from_source_point(bvhtree, point, local_seed, settings)
        scattered_matrices.append(matrix)
    return scattered_matrices

def iter_points_on_stroke_with_seed(stroke_points, density, seed):
    for i, (start, end) in enumerate(iter_pairwise(stroke_points)):
        segment_seed = sub_seed(seed, i)
        segment_vector = end - start

        segment_length = segment_vector.length
        amount = round_random(segment_length * density, segment_seed)

        for j in range(amount):
            t = random_uniform(sub_seed(segment_seed, j, 0))
            origin = start + t * segment_vector
            yield origin, sub_seed(segment_seed, j, 1)

def scatter_from_source_point(bvhtree, point, seed, settings):
    # Project displaced point on surface
    radius = random_uniform(sub_seed(seed, 0)) * settings.radius
    offset = random_vector(sub_seed(seed, 2)) * radius
    location, normal, *_ = bvhtree.find_nearest(point + offset)
    assert location is not None
    normal.normalize()

    up_direction = normal if settings.use_normal_rotation else Vector((0, 0, 1))

    # Scale
    min_scale = settings.scale * (1 - settings.random_scale)
    max_scale = settings.scale
    scale = random_uniform(sub_seed(seed, 1), min_scale, max_scale)

    # Location
    location += normal * settings.normal_offset * scale

    # Rotation
    z_rotation = Euler((0, 0, random_uniform(sub_seed(seed, 3), 0, 2 * math.pi))).to_matrix()
    up_rotation = up_direction.to_track_quat('Z', 'X').to_matrix()
    local_rotation = random_euler(sub_seed(seed, 3), settings.rotation).to_matrix()
    rotation = local_rotation @ up_rotation @ z_rotation

    return Matrix.Translation(location) @ rotation.to_4x4() @ scale_matrix(scale)


# Drawing
#################################################

box_vertices = (
    (-1, -1,  1), ( 1, -1,  1), ( 1,  1,  1), (-1,  1,  1),
    (-1, -1, -1), ( 1, -1, -1), ( 1,  1, -1), (-1,  1, -1))

box_indices = (
    (0, 1, 2), (2, 3, 0), (1, 5, 6), (6, 2, 1),
    (7, 6, 5), (5, 4, 7), (4, 0, 3), (3, 7, 4),
    (4, 5, 1), (1, 0, 4), (3, 2, 6), (6, 7, 3))

box_vertices = tuple(Vector(vertex) * 0.5 for vertex in box_vertices)

def draw_matrices_batches(batches):
    shader = get_uniform_color_shader()
    shader.bind()
    shader.uniform_float("color", (0.4, 0.4, 1.0, 0.3))

    gpu.state.blend_set('ALPHA')
    gpu.state.depth_mask_set(False)

    for batch in batches:
        batch.draw(shader)

    gpu.state.blend_set('NONE')
    gpu.state.depth_mask_set(True)

def create_batch_for_matrices(matrices, base_scale):
    coords = []
    indices = []

    scaled_box_vertices = [base_scale * vertex for vertex in box_vertices]

    for matrix in matrices:
        offset = len(coords)
        coords.extend((matrix @ vertex for vertex in scaled_box_vertices))
        indices.extend(tuple(index + offset for index in element) for element in box_indices)

    batch = batch_for_shader(get_uniform_color_shader(),
        'TRIS', {"pos" : coords}, indices = indices)
    return batch


def draw_line_strip_batch(batch, color, thickness=1):
    shader = get_uniform_color_shader()
    gpu.state.line_width_set(thickness)
    shader.bind()
    shader.uniform_float("color", color)
    batch.draw(shader)

def create_line_strip_batch(coords):
    return batch_for_shader(get_uniform_color_shader(), 'LINE_STRIP', {"pos" : coords})


def draw_text(location, text, size=15, color=(1, 1, 1, 1)):
    font_id = 0
    ui_scale = bpy.context.preferences.system.ui_scale
    blf.position(font_id, *location)
    blf.size(font_id, round(size * ui_scale))
    blf.draw(font_id, text)


# Utilities
########################################################

'''
Pythons random functions are designed to be used in cases
when a seed is set once and then many random numbers are
generated. To improve the user experience I want to have
full control over how random seeds propagate through the
functions. This is why I use custom random functions.

One benefit is that changing the object density does not
generate new random positions for all objects.
'''

def round_random(value, seed):
    probability = value % 1
    if probability < random_uniform(seed):
        return math.floor(value)
    else:
        return math.ceil(value)

def random_vector(x, min=-1, max=1):
    return Vector((
        random_uniform(sub_seed(x, 0), min, max),
        random_uniform(sub_seed(x, 1), min, max),
        random_uniform(sub_seed(x, 2), min, max)))

def random_euler(x, factor):
    return Euler(tuple(random_vector(x) * factor))

def random_uniform(x, min=0, max=1):
    return random_int(x) / 2147483648 * (max - min) + min

def random_int(x):
    x = (x<<13) ^ x
    return (x * (x * x * 15731 + 789221) + 1376312589) & 0x7fffffff

def sub_seed(seed, index, index2=0):
    return random_int(seed * 3243 + index * 5643 + index2 * 54243)


def currently_in_3d_view(context):
    return context.space_data.type == 'VIEW_3D'

def get_selected_non_active_objects(context):
    return set(context.selected_objects) - {context.active_object}

def make_random_chunks(sequence, chunk_amount):
    sequence = list(sequence)
    random.shuffle(sequence)
    return make_chunks(sequence, chunk_amount)

def make_chunks(sequence, chunk_amount):
    length = math.ceil(len(sequence) / chunk_amount)
    return [sequence[i:i+length] for i in range(0, len(sequence), length)]

def iter_pairwise(sequence):
    return zip(sequence, islice(sequence, 1, None))

def bvhtree_from_object(object):
    import bmesh
    bm = bmesh.new()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    object_eval = object.evaluated_get(depsgraph)
    mesh = object_eval.to_mesh()
    bm.from_mesh(mesh)
    bm.transform(object.matrix_world)

    bvhtree = BVHTree.FromBMesh(bm)
    object_eval.to_mesh_clear()
    return bvhtree

def shoot_region_2d_ray(bvhtree, position_2d):
    region = bpy.context.region
    region_3d = bpy.context.space_data.region_3d

    origin = region_2d_to_origin_3d(region, region_3d, position_2d)
    direction = region_2d_to_vector_3d(region, region_3d, position_2d)

    location, normal, index, distance = bvhtree.ray_cast(origin, direction)
    return location, normal, index, distance

def scale_matrix(factor):
    m = Matrix.Identity(4)
    m[0][0] = factor
    m[1][1] = factor
    m[2][2] = factor
    return m

def event_is_in_region(event, region):
    return (region.x <= event.mouse_x <= region.x + region.width
        and region.y <= event.mouse_y <= region.y + region.height)

def get_max_object_side_length(objects):
    return max(
        max(obj.dimensions[0] for obj in objects),
        max(obj.dimensions[1] for obj in objects),
        max(obj.dimensions[2] for obj in objects)
    )

def get_uniform_color_shader():
    return gpu.shader.from_builtin('UNIFORM_COLOR')


# Registration
###############################################

def register():
    bpy.utils.register_class(ScatterObjects)

def unregister():
    bpy.utils.unregister_class(ScatterObjects)
