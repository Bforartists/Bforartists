import bpy
from .. import __package__ as base_package
from .object import convert_to_mesh


#### ------------------------------ /all/ ------------------------------ ####

def list_canvases():
    """List all canvases in the scene"""
    canvas = []
    for obj in bpy.context.scene.objects:
        if obj.booleans.canvas:
            canvas.append(obj)

    return canvas



#### ------------------------------ /selected/ ------------------------------ ####

def list_candidate_objects(self, context, canvas):
    """Filter out objects from selected ones that can't be used as a cutter"""

    cutters = []
    for obj in context.selected_objects:
        if obj != context.active_object and obj.type in ('MESH', 'CURVE', 'FONT'):
            if obj.library or obj.override_library:
                self.report({'ERROR'}, f"{obj.name} is linked and can not be used as a cutter")

            else:
                if obj.type in ('CURVE', 'FONT'):
                    if obj.data.bevel_depth != 0 or obj.data.extrude != 0:
                        convert_to_mesh(context, obj)
                        cutters.append(obj)

                else:
                    if (obj.booleans.cutter == "") or (canvas not in list_cutter_users([obj])):
                        cutters.append(obj)

    return cutters


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
        for mod in canvas.modifiers:
            if mod.type == 'BOOLEAN' and "boolean_" in mod.name:
                if mod.object:
                    cutters.append(mod.object)
                    modifiers.append(mod)

    return cutters, modifiers


def list_canvas_slices(canvases):
    """Returns list of slices for specified canvases"""

    slices = []
    for obj in bpy.context.scene.objects:
        if obj.booleans.slice:
            if obj.booleans.slice_of in canvases:
                slices.append(obj)

    return slices


def list_cutter_users(cutters):
    """List canvases that use specified cutters"""

    cutter_users = []
    canvases = list_canvases()
    for obj in canvases:
        for mod in obj.modifiers:
            if mod.type == 'BOOLEAN' and mod.object in cutters:
                cutter_users.append(obj)

    return cutter_users


def list_cutter_modifiers(canvases, cutters):
    """List modifiers on specified canvases that use specified cutters"""

    if not canvases:
        canvases = list_canvases()

    modifiers = []
    for canvas in canvases:
        for mod in canvas.modifiers:
            if mod.type == 'BOOLEAN':
                if mod.object in cutters:
                    modifiers.append(mod)

    return modifiers


def list_unused_cutters(cutters, *canvases, do_leftovers=False):
    """Takes in list of cutters and returns only those that have no other user besides specified canvas"""
    """When `include_visible` is True it will return cutters that aren't used by any visible modifiers"""

    other_canvases = list_canvases()
    original_cutters = cutters[:]

    for obj in other_canvases:
        if obj in canvases:
            return

        if any(mod.object in cutters for mod in obj.modifiers if mod.type == 'BOOLEAN'):
            cutters[:] = [cutter for cutter in cutters if cutter not in [mod.object for mod in obj.modifiers]]

    leftovers = []
    # return_cutters_that_do_have_other_users_(so_that_parents_can_be_reassigned)
    if do_leftovers:
        leftovers = [cutter for cutter in original_cutters if cutter not in cutters]

    return cutters, leftovers


def list_pre_boolean_modifiers(obj):
    """Returns list of boolean modifiers + all modifiers that come before last boolean modifier"""

    # find_the_index_of_last_boolean_modifier
    last_boolean_index = -1
    for i in reversed(range(len(obj.modifiers))):
        if obj.modifiers[i].type == 'BOOLEAN':
            last_boolean_index = i
            break

    # if_boolean_modifier_found_list_all_modifiers_before
    if last_boolean_index != -1:
        return [mod for mod in obj.modifiers[:last_boolean_index + 1]]
    else:
        return []
