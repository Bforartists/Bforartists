import bpy

from .modifier import (
    is_boolean_modifier,
)
from .object import (
    is_linked,
    change_parent,
)


#### ------------------------------ /poll/ ------------------------------ ####

def is_canvas(obj):
    """Checks whether the object is a Boolean canvas (i.e. has Boolean cutters)."""

    if obj.booleans.canvas == False:
        return False
    else:
        # Even if object is marked as a canvas, check if it actually has any cutters.
        cutters, __ = list_canvas_cutters([obj])
        if len(cutters) > 0:
            return True
        else:
            return False



#### ------------------------------ /list/ ------------------------------ ####

def list_all_canvases(scene):
    """Returns the list of all Boolean canvases in the scene."""

    canvases = []

    for obj in scene.objects:
        if is_canvas(obj):
            canvases.append(obj)

    return canvases


def list_selected_canvases(context):
    """Returns the list of canvases in the selection."""

    canvases = []
    active_object = context.active_object
    selected_objects = context.selected_objects

    if selected_objects:
        for obj in selected_objects:
            if obj == active_object:
                continue
            if obj.type != 'MESH':
                continue
            if is_canvas(obj):
                canvases.append(obj)

    if active_object:
        if is_canvas(active_object):
            canvases.append(active_object)

    return canvases


def list_canvas_cutters(canvases: list) -> tuple[list, dict]:
    """List cutters (and their associated modifiers) that are used by specified canvases."""

    cutters = []
    modifiers = {}
    for canvas in canvases:
        for mod in canvas.modifiers:
            if not is_boolean_modifier(mod):
                continue

            if mod.object not in cutters:
                cutters.append(mod.object)
            modifiers.setdefault(canvas, []).append(mod)

    return cutters, modifiers


def list_canvas_slices(context, canvases: list):
    """Returns the list of slices of specified canvases."""

    slices = []
    for obj in context.scene.objects:
        if obj.booleans.slice:
            if obj.booleans.slice_of in canvases:
                slices.append(obj)

    return slices



#### ------------------------------ /filter/ ------------------------------ ####

def filter_canvases(self, context, canvases: list) -> list:
    """Filter out objects from the given list if they can't be cut."""

    usable_canvases = []
    for canvas in canvases:
        # Exclude non-Mesh types.
        if canvas.type != 'MESH':
            self.report({'WARNING'}, f"{canvas.name} is not a Mesh type. Only Meshes can be cut")
            continue
        # Exclude linked objects.
        if is_linked(context, canvas):
            self.report({'WARNING'}, f"{canvas.name} is linked and can not be used as a cutter")
            continue

        usable_canvases.append(canvas)

    return usable_canvases



#### ------------------------------ /filter/ ------------------------------ ####

def create_slice(context, canvas, modifier=False):
    """Creates copy of canvas to be used as slice."""

    slice = canvas.copy()
    slice.data = canvas.data.copy()
    slice.name = slice.data.name = canvas.name + "_slice"

    # Parent to canvas.
    change_parent(context, slice, canvas, inverse=True)

    # Set Boolean properties.
    if modifier == True:
        slice.booleans.canvas = True
        slice.booleans.slice = True
        slice.booleans.slice_of = canvas

    # Add to canvas collections.
    for coll in canvas.users_collection:
        coll.objects.link(slice)

    # Add slices to local view.
    if context.space_data.local_view:
        slice.local_view_set(context.space_data, True)

    return slice
