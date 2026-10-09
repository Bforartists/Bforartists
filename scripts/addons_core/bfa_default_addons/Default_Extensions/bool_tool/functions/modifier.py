import bpy
import bmesh
from contextlib import contextmanager
from .. import __package__ as base_package

from .mesh import (
    is_instanced_mesh,
)
from .object import (
    convert_to_mesh,
)


#### ------------------------------ /list/ ------------------------------ ####

def enumerate_boolean_modifiers(obj) -> int:
    """Returns the number of Boolean modifiers on the object."""

    num = 0
    for mod in obj.modifiers:
        if is_boolean_modifier(mod):
            num += 1

    return num


def get_modifiers_to_apply(context, obj, custom_list=None) -> list:
    """Returns the list of modifiers that need to be applied based on add-on preferences."""

    prefs = context.preferences.addons[base_package].preferences

    # Apply all modifiers.
    if prefs.apply_order == 'ALL':
        modifiers = list(obj.modifiers)

    # Apply only Boolean modifiers.
    elif prefs.apply_order == 'BOOLEANS':
        if custom_list is None:
            modifiers = [mod for mod in obj.modifiers if is_boolean_modifier(mod)]
        else:
            modifiers = custom_list

    # Apply all modifiers that come before last Boolean modifier.
    elif prefs.apply_order == 'BEFORE':
        # Find the index of a last Boolean modifier.
        last_boolean_index = -1
        for i in reversed(range(len(obj.modifiers))):
            if obj.modifiers[i].type == 'BOOLEAN':
                last_boolean_index = i
                break

        # If a Boolean modifier is found, list all modifiers that come before it.
        if last_boolean_index != -1:
            modifiers = [mod for mod in obj.modifiers[:last_boolean_index + 1]]
        else:
            modifiers = []

    return modifiers



#### ------------------------------ /poll/ ------------------------------ ####

def is_boolean_modifier(mod, check_cutter=True) -> bool:
    """Checks if a modifier is a Boolean modifier (and optionally if it has a valid cutter)."""

    if mod is None:
        return False
    if mod.type != 'BOOLEAN':
        return False
    if check_cutter and mod.object is None:
        return False

    return True



#### ------------------------------ FUNCTIONS ------------------------------ ####

def add_boolean_modifier(self, context, obj, cutter, mode, solver, pin=False, redo=True):
    """Adds the Boolean modifier with specified cutter and properties to a given object."""

    if bpy.app.version < (5, 0, 0) and solver == 'FLOAT':
        solver = 'FAST'

    prefs = context.preferences.addons[base_package].preferences
    name = "boolean_" + cutter.name.replace("boolean_", "")

    modifier = obj.modifiers.new(name, 'BOOLEAN')
    modifier.operation = mode
    modifier.object = cutter
    modifier.solver = solver
    modifier.show_in_editmode = prefs.show_in_editmode

    # Set solver options (inherited from operator properties, i.e. `self`).
    if redo:
        modifier.material_mode = self.material_mode
        modifier.use_self = self.use_self
        modifier.use_hole_tolerant = self.use_hole_tolerant
        modifier.double_threshold = self.double_threshold

    # Move modifier to the index 0 (make it first in the stack).
    if pin:
        index = obj.modifiers.find(modifier.name)
        obj.modifiers.move(index, 0)

    return modifier


def apply_modifiers(context, obj, modifiers: list, force_clean=False):
    """
    Apply modifiers on object.
    Instead of using `bpy.ops.object.modifier_apply`, by default this function uses
    `to_mesh` built-in function to create a temporary mesh from the evaluated object
    (basically with visible modifiers applied). Temporary mesh is then transferred
    to objects mesh using `bmesh`.

    This method is up to 2x faster, although it's considered experimental
    and may fail in some cases, so a fallback to `bpy.ops.object.modifier_apply` is kept.
    """

    prefs = context.preferences.addons[base_package].preferences
    _stored_active_obj = context.active_object

    # Make object data unique if it's instanced.
    if is_instanced_mesh(obj.data):
        context.active_object.data = context.active_object.data.copy()

    try:
        # Don't use this method if it's not enabled by user in preferences, unless caller forces it.
        if not prefs.fast_modifier_apply:
            if not force_clean:
                raise Exception()

        context.view_layer.objects.active = obj
        with hide_modifiers(obj, excluding=modifiers):
            # Create a temporary mesh from evaluated object.
            depsgraph = context.evaluated_depsgraph_get()
            evaluated_obj = obj.evaluated_get(depsgraph)
            temp_data = evaluated_obj.to_mesh(preserve_all_data_layers=True,
                                              depsgraph=depsgraph)

            # Create `bmesh` from temporary mesh and update edit mesh.
            if context.mode == 'EDIT_MESH':
                bm = bmesh.from_edit_mesh(obj.data)
                bm.clear()
                bm.from_mesh(temp_data)
                bmesh.update_edit_mesh(obj.data)
            else:
                bm = bmesh.new()
                bm.from_mesh(temp_data)
                bm.to_mesh(obj.data)

            bm.free()
            evaluated_obj.to_mesh_clear()

            # Remove modifiers.
            for mod in modifiers:
                obj.modifiers.remove(mod)

            # Remove shape keys if there are any.
            # (after above operations none of the shape keys have any effect).
            if obj.data.shape_keys:
                obj.shape_key_clear()

    except Exception as e:
        # print("Error applying modifiers with `bmesh` method:", e, "falling back to `bpy.ops` method")

        context_override = {"active_object": obj, "mode": 'OBJECT'}
        with context.temp_override(**context_override):
            # Apply shape keys if there are any.
            if obj.data.shape_keys:
                bpy.ops.object.shape_key_remove(all=True, apply_mix=True)

            # If all modifiers need to be applied convert to Mesh.
            if modifiers == obj.modifiers.values():
                print("Applying all modifiers by converting to Mesh")
                convert_to_mesh(context, obj)
                return

            for mod in modifiers:
                bpy.ops.object.modifier_apply(modifier=mod.name)

    context.view_layer.objects.active = _stored_active_obj


@contextmanager
def hide_modifiers(obj, excluding: list):
    """Hides all modifiers of a given object in the viewport except those in `excluding` list."""

    visible_modifiers = []
    for mod in obj.modifiers:
        if mod in excluding:
            continue
        if mod.show_viewport == True:
            visible_modifiers.append(mod)
            mod.show_viewport = False

    try:
        yield
    finally:
        for mod in visible_modifiers:
            mod.show_viewport = True


def add_modifier_asset(obj, path: str, asset: str):
    """Loads in the node group asset and adds a Geometry Nodes modifier using it."""

    try:
        # Load in the node group.
        if bpy.app.version >= (5, 0, 0):
            with bpy.data.libraries.load(path, link=True, pack=True) as (data_from, data_to):
                if asset in data_from.node_groups:
                    data_to.node_groups = [asset]

        else:
            with bpy.data.libraries.load(path) as (data_from, data_to):
                if asset in data_from.node_groups:
                    data_to.node_groups = [asset]

        node_group = bpy.data.node_groups[asset]

        # Add modifier to the object.
        mod = obj.modifiers.new(asset, type='NODES')
        mod.node_group = node_group
        mod.show_group_selector = False
        mod.show_manage_panel = False

        return mod

    except Exception as e:
        print("Modifier node group could not be loaded:", e)
        return None


def update_modifier_input(modifier, socket: str, value):
    """Change the value of the geometry nodes modifier input socket."""

    try:
        if bpy.app.version >= (5, 2, 0):
            socket = getattr(modifier.properties.inputs, socket)
            socket.value = value
        else:
            modifier[f"{socket}"] = value
    except:
        """
        NOTE: There are plethora of reasons why this can fail, node trees are finicky.
        Accounting for all possible cases is borderline impossible, so this check is necessary
        to at least fail silently and not throw Python error to users.
        """
        pass
