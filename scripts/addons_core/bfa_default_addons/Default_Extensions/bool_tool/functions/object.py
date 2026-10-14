import bpy
import bmesh
from mathutils import Vector, Matrix
from contextlib import contextmanager


#### ------------------------------ /poll/ ------------------------------ ####

def is_linked(context, obj) -> bool:
    """Checks whether the object is linked from an external .blend file (including library-overrides)."""

    if obj not in context.editable_objects:
        if obj.library:
            return True
        else:
            return False
    else:
        if obj.override_library:
            return True
        else:
            return False


def has_evaluated_mesh(context, obj):
    """Checks if an evaluated object has mesh (created by Geometry Nodes modifiers)."""

    # Exclude cases that return Python errors.
    if not obj:
        return False
    if bpy.app.version < (5, 2, 0) and obj.type == 'EMPTY':
        return False
    if obj.instance_type != 'NONE':
        return False

    depsgraph = context.view_layer.depsgraph
    obj_eval = depsgraph.id_eval_get(obj)

    geometry = None
    try:
        geometry = obj_eval.evaluated_geometry()
    except:
        pass

    if not geometry or not geometry.mesh:
        return False
    else:
        return True



#### ------------------------------ /operate/ ------------------------------ ####

def object_visibility_set(obj, value=False):
    """Sets object visibility properties to either True or False."""

    obj.visible_camera = value
    obj.visible_shadow = value
    obj.visible_diffuse = value
    obj.visible_glossy = value
    obj.visible_transmission = value
    obj.visible_volume_scatter = value
    if bpy.app.version >= (5, 2, 0):
        obj.visible_raycast = value

    obj.hide_probe_volume = not value
    obj.hide_probe_sphere = not value
    obj.hide_probe_plane = not value


def convert_to_mesh(context, obj):
    """Converts active object into mesh (applying all modifiers and shape keys in the process)."""

    original_mode = obj.mode

    if original_mode != 'OBJECT':
        edit_objects = context.objects_in_mode
        bpy.ops.object.mode_set(mode='OBJECT')

    # Store selection.
    stored_active = context.active_object
    stored_selection = context.selected_objects
    for ob in context.scene.objects:
        ob.select_set(False)

    # Make `obj` active and only one selected.
    obj.select_set(True)
    context.view_layer.objects.active = obj

    # Convert.
    bpy.ops.object.convert(target='MESH')

    if original_mode != 'OBJECT':
        for ob in edit_objects:
            ob.select_set(True)
        bpy.ops.object.mode_set(mode=original_mode)

    # Restore selection.
    for ob in stored_selection:
        ob.select_set(True)
    context.view_layer.objects.active = stored_active


def change_parent(context, obj, parent, inverse=False):
    """Changes or removes parent from an object while keeping the transformation."""

    context.evaluated_depsgraph_get().update()

    obj.parent = parent
    if inverse and parent is not None:
        obj.matrix_parent_inverse = parent.matrix_world.inverted()


def set_object_origin(obj, bm, point='CENTER', custom: Vector=None):
    """Sets the origin of a mesh type object to given position by shifting vertices."""

    # Center of the bounding box.
    if point == 'CENTER_OBJ':
        position_local = 0.125 * sum((Vector(b) for b in obj.bound_box), Vector())
        position_world = obj.matrix_world @ position_local

    # Center of the geometry.
    elif point == 'CENTER_MESH':
        if len(bm.verts) > 0:
            position_local = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
        else:
            position_local = Vector((0, 0, 0))
        position_world = obj.matrix_world @ position_local

    # Custom origin point (should be local Vector).
    elif point == 'CUSTOM':
        position_local = custom
        position_world = obj.matrix_world @ custom

    matrix = Matrix.Translation(position_local)
    bmesh.ops.transform(bm, matrix=matrix.inverted(), verts=bm.verts)
    bm.to_mesh(obj.data)

    obj.location = position_world


@contextmanager
def hide_objects(context, exceptions: list):
    """Hides objects during the context, and restores their visibility afterwards."""

    hidden_objects = []
    for obj in context.scene.objects:
        if obj in exceptions:
            continue
        if obj.hide_get() == False:
            hidden_objects.append(obj)
            obj.hide_set(True)

    try:
        yield

    finally:
        for obj in hidden_objects:
            obj.hide_set(False)


def delete_object(cutter, purge_data=True):
    """Deletes the object and optionally purges its data if it has no more users."""

    orphaned_data = cutter.data
    bpy.data.objects.remove(cutter)

    if purge_data and orphaned_data.users == 0:
        bpy.data.meshes.remove(orphaned_data)
