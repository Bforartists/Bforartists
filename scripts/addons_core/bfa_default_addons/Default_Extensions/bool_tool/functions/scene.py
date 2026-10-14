import bpy
from .. import __package__ as base_package

from .object import (
    hide_objects,
)
from .types import (
    Ray,
)
from .view import (
    region_2d_to_ray_3d,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def ensure_collection(context) -> bpy.types.Collection:
    """Returns the Boolean cutters collection and creates it if it doesn't exist."""

    prefs = context.preferences.addons[base_package].preferences
    collection_name = prefs.collection_name

    coll = bpy.data.collections.get(collection_name)

    # Create the collection if it doesn't exist.
    if coll is None:
        coll = bpy.data.collections.new(collection_name)
        coll.hide_render = True
        coll.color_tag = 'COLOR_01'
        context.scene.collection.children.link(coll)

    return coll


def delete_empty_collection(context):
    """Removes Boolean cutters collection if it has no more objects in it."""

    prefs = context.preferences.addons[base_package].preferences

    if not prefs.use_collection:
        return

    collection_name = prefs.collection_name
    collection = bpy.data.collections.get(collection_name)

    if not collection:
        return
    if collection.objects:
        return

    bpy.data.collections.remove(collection)


def raycast(context, position, objects):
    """Cast a ray in the scene to get the surface on any of the given objects."""

    region = context.region
    rv3d = context.region_data
    depsgraph = context.view_layer.depsgraph

    origin, direction = region_2d_to_ray_3d(region, rv3d, position)

    # Cast Ray
    with hide_objects(context, exceptions=objects):
        hit, location, normal, index, object, matrix = context.scene.ray_cast(depsgraph, origin, direction)
        ray = Ray(hit, location, normal, index, object, matrix)

    return ray
