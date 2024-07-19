import bpy
from .. import __package__ as base_package


#### ------------------------------ FUNCTIONS ------------------------------ ####

def add_boolean_modifier(canvas, cutter, mode, solver, apply=False):
    "Adds boolean modifier with specified cutter and properties to a single object"

    prefs = bpy.context.preferences.addons[base_package].preferences

    modifier = canvas.modifiers.new("boolean_" + cutter.name, 'BOOLEAN')
    modifier.operation = mode
    modifier.object = cutter
    modifier.solver = solver
    if prefs.show_in_editmode:
        modifier.show_in_editmode = True

    if apply:
        context_override = {'object': canvas}
        with bpy.context.temp_override(**context_override):
            bpy.ops.object.modifier_apply(modifier=modifier.name)


def object_visibility_set(obj, value=False):
    "Sets object visibility properties to either True or False"

    obj.visible_camera = value
    obj.visible_diffuse = value
    obj.visible_glossy = value
    obj.visible_shadow = value
    obj.visible_transmission = value
    obj.visible_volume_scatter = value


def convert_to_mesh(context, brush):
    "Converts active object into mesh"

    # store_selection
    stored_active = context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    brush.select_set(True)
    context.view_layer.objects.active = brush

    # Convert
    bpy.ops.object.convert(target='MESH')

    # restore_selection
    for obj in context.selected_objects:
        obj.select_set(True)
    context.view_layer.objects.active = stored_active


def delete_empty_collection():
    """Removes "boolean_cutters" collection if it has no more objects in it"""

    collection = bpy.data.collections.get("boolean_cutters")
    if not collection.objects:
        bpy.data.collections.remove(collection)


def create_slice(context, canvas, slices, modifier=False):
    """Creates copy of canvas to be used as slice"""

    prefs = bpy.context.preferences.addons[base_package].preferences

    slice = canvas.copy()
    context.collection.objects.link(slice)
    slice.data = canvas.data.copy()
    slice.name = slice.data.name = canvas.name + "_slice"

    # parent_to_canvas
    if prefs.parent:
        slice.parent = canvas
        slice.matrix_parent_inverse = canvas.matrix_world.inverted()

    # set_boolean_properties
    if modifier == True:
        slice.booleans.canvas = True
        slice.booleans.slice = True
        slice.booleans.slice_of = canvas
    slices.append(slice)

    # add_to_canvas_collections
    canvas_colls = canvas.users_collection
    for collection in canvas_colls:
        if collection != context.view_layer.active_layer_collection.collection:
            collection.objects.link(slice)

    for coll in slice.users_collection:
        if coll not in canvas_colls:
            coll.objects.unlink(slice)

    # remove_other_modifiers
    for mod in slice.modifiers:
        if "boolean_" in mod.name:
            slice.modifiers.remove(mod)

    # add_slices_to_local_view
    space_data = context.space_data
    if space_data.local_view:
        slice.local_view_set(space_data, True)
