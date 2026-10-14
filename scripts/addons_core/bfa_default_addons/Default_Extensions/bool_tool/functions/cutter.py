import bpy
from .. import __package__ as base_package

from ..constants import (
    CONVERTABLE_TYPES,
)
from .modifier import (
    is_boolean_modifier,
)
from .object import (
    is_linked,
    has_evaluated_mesh,
    object_visibility_set,
    convert_to_mesh,
    change_parent,
    delete_object,
)
from .scene import (
    ensure_collection,
)


#### ------------------------------ /list/ ------------------------------ ####

def list_selected_cutters(context):
    """Returns the list of cutters in the selection."""

    cutters = []
    active_object = context.active_object
    selected_objects = context.selected_objects

    if selected_objects:
        for obj in selected_objects:
            if obj == active_object:
                continue
            if obj.type != 'MESH':
                continue
            if obj.booleans.cutter:
                cutters.append(obj)

    if active_object:
        if active_object.booleans.cutter:
            cutters.append(active_object)

    return cutters


def list_cutter_users(cutters: list, exclude: list=None) -> dict:
    """
    List canvases that use specified cutters.
    Canvases that should be excluded from the search can be specified with the `exclude` arg.
    Returns a dict of canvases (keys) and set of their Boolean modifiers that use cutters (values).
    """

    cutter_users = {}

    for key, values in bpy.data.user_map(subset=cutters).items():
        for value in values:
            if value.id_type != 'OBJECT':
                continue
            if exclude and value in exclude:
                continue
            if len(value.modifiers) == 0:
                continue

            for mod in value.modifiers:
                if not is_boolean_modifier(mod):
                    continue
                if mod.object not in cutters:
                    continue

                cutter_users.setdefault(value, set()).add(mod)

    return cutter_users



#### ------------------------------ /filter/ ------------------------------ ####

def filter_cutters(self, context, cutters: list, canvases: list) -> list:
    """
    Filter out objects from the given list if they can't be used as a cutter.
    If non-mesh type object has evaluated mesh, and can be converted to mesh it will be.
    """

    usable_cutters = []
    for cutter in cutters:
        # Exclude object if it is in both lists.
        if cutter in canvases:
            continue
        # Exclude linked objects.
        if is_linked(context, cutter):
            self.report({'WARNING'}, f"{cutter.name} is linked and can not be used as a cutter")
            continue

        if cutter.type == 'MESH':
            # Exclude if object is already a cutter for canvas.
            users = list_cutter_users([cutter]).keys()
            if any(canvas in users for canvas in canvases):
                continue
            # Exclude if canvas is cutting the object (avoid dependancy loop).
            users = list_cutter_users(canvases).keys()
            if cutter in users:
                self.report({'WARNING'}, f"{cutter.name} can not cut its own cutter (dependancy loop)")
                continue

            usable_cutters.append(cutter)

        elif cutter.type in CONVERTABLE_TYPES:
            if not has_evaluated_mesh(context, cutter):
                continue

            convert_to_mesh(context, cutter)
            usable_cutters.append(cutter)

    return usable_cutters



#### ------------------------------ /operate/ ------------------------------ ####

def make_cutter(context, cutter, mode: str, display='BOUNDS', collection=True):
    """Ensures the cutter has the correct properties."""

    # Hide Cutters
    cutter.hide_render = True
    cutter.display_type = display
    cutter.lineart.usage = 'EXCLUDE'
    object_visibility_set(cutter, value=False)

    # Cutters Collection
    if collection:
        cutters_collection = ensure_collection(context)
        if cutters_collection not in cutter.users_collection:
            cutters_collection.objects.link(cutter)

    # Set Boolean Property
    cutter.booleans.cutter = mode.capitalize()


def restore_cutter(context, cutter, unparent=True, unlink_collection=True):
    """Remove Boolean properties from a cutter object to restore it to a normal state."""

    prefs = context.preferences.addons[base_package].preferences

    # Restore Unused Cutters
    cutter.hide_render = False
    cutter.display_type = 'TEXTURED'
    cutter.lineart.usage = 'INHERIT'
    object_visibility_set(cutter, value=True)
    cutter.booleans.cutter = ""

    # Remove Parent & Collection
    if unparent:
        change_parent(context, cutter, None)

    if unlink_collection:
        cutters_collection = bpy.data.collections.get(prefs.collection_name)
        if cutters_collection in cutter.users_collection:
            cutters_collection.objects.unlink(cutter)


def handle_unused_cutters(context, cutters: list, canvases: list, delete=True):
    """Deletes or restores cutters with no remaining users (besides given list of canvases)."""

    prefs = context.preferences.addons[base_package].preferences

    for cutter in cutters:
        other_canvases = list_cutter_users([cutter], exclude=canvases).keys()

        if len(other_canvases) == 0:
            if delete:
                # Delete unused cutters & transfer their children to canvas.
                for child in cutter.children:
                    change_parent(context, child, cutter.parent, inverse=True)
                delete_object(cutter)

            else:
                # Restore unused cutters.
                restore_cutter(context, cutter,
                               unparent=prefs.parent and cutter.parent in canvases,
                               unlink_collection=prefs.use_collection)

        else:
            # Cutter has other users, parent it to one of them.
            if prefs.parent and cutter.parent in canvases:
                new_parent = next(c for c in other_canvases if not c.booleans.slice)
                change_parent(context, cutter, new_parent, inverse=True)
