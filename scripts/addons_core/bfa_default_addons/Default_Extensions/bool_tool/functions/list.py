import bpy
from .. import __package__ as base_package
from .set import convert_to_mesh


#### ------------------------------ /all/ ------------------------------ ####

def list_canvases():
    """List all canvases in the scene"""
    canvas = []
    for obj in bpy.data.objects:
        if obj.booleans.canvas:
            canvas.append(obj)

    return canvas



#### ------------------------------ /selected/ ------------------------------ ####

def list_candidate_objects(context):
    """List objects from selected ones that can be used as cutter"""

    brushes = []
    for obj in context.selected_objects:
        if obj != context.active_object and obj.type in ('MESH', 'CURVE', 'FONT'):
            if obj.type in ('CURVE', 'FONT'):
                if obj.data.bevel_depth != 0 or obj.data.extrude != 0:
                    convert_to_mesh(context, obj)
                    brushes.append(obj)
            else:
                brushes.append(obj)

    return brushes


def list_selected_cutters(context):
    """List selected cutters"""

    cutters = []
    active_object = context.active_object
    selected_objects = context.selected_objects

    if selected_objects:
        for obj in selected_objects:
            if obj != active_object and obj.type == 'MESH':
                if obj.booleans.cutter:
                    cutters.append(obj)

    if active_object:
        if active_object.booleans.cutter:
            cutters.append(active_object)

    return cutters


def list_selected_canvases(context):
    """List selected canvases"""

    canvases = []
    active_object = context.active_object
    selected_objects = context.selected_objects

    if selected_objects:
        for obj in selected_objects:
            if obj != active_object and obj.type == 'MESH':
                if obj.booleans.canvas:
                    canvases.append(obj)

    if active_object:
        if active_object.booleans.canvas:
            canvases.append(active_object)

    return canvases



#### ------------------------------ /users/ ------------------------------ ####

def list_canvas_cutters(canvases):
    """List cutters that are used by specified canvases"""

    cutters = []
    modifiers = []
    for canvas in canvases:
        for modifier in canvas.modifiers:
            if modifier.type == 'BOOLEAN' and "boolean_" in modifier.name:
                if modifier.object:
                    cutters.append(modifier.object)
                    modifiers.append(modifier)

    return cutters, modifiers


def list_canvas_slices(canvases):
    """Returns list of slices for specified canvases"""

    slices = []
    for obj in bpy.data.objects:
        if obj.booleans.slice:
            if obj.booleans.slice_of in canvases:
                slices.append(obj)

    return slices


def list_cutter_users(cutters):
    """List canvases that use specified cutters"""

    cutter_users = []
    canvas = list_canvases()
    for obj in canvas:
        for modifier in obj.modifiers:
            if modifier.type == 'BOOLEAN' and modifier.object in cutters:
                cutter_users.append(obj)

    return cutter_users


def list_cutter_modifiers(canvases, cutters):
    """List modifiers on specified canvases that use specified cutters"""

    if not canvases:
        canvases = list_canvases()

    modifiers = []
    for canvas in canvases:
        for modifier in canvas.modifiers:
            if modifier.type == 'BOOLEAN':
                if modifier.object in cutters:
                    modifiers.append(modifier)

    return modifiers


def list_unused_cutters(cutters, *canvases, do_leftovers=False):
    """Takes in list of cutters and returns only those that have no other user besides specified canvas"""
    """When `include_visible` is True it will return cutters that aren't used by any visible modifiers"""

    prefs = bpy.context.preferences.addons[base_package].preferences
    other_canvases = list_canvases()

    leftovers = []
    original_cutters = cutters[:]

    for obj in other_canvases:
        if obj not in canvases:
            if any(modifier.object in cutters for modifier in obj.modifiers):
                cutters[:] = [cutter for cutter in cutters if cutter not in [modifier.object for modifier in obj.modifiers]]
                if prefs.parent and do_leftovers:
                    leftovers = [cutter for cutter in original_cutters if cutter not in cutters]

    return cutters, leftovers
