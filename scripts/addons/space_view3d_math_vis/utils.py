# SPDX-FileCopyrightText: 2010-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy


def console_namespace():
    import console_python
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'CONSOLE':
                for region in area.regions:
                    if region.type == 'WINDOW':
                        console = console_python.get_console(hash(region))
                        if console:
                            return console[0].locals
    return {}


def is_display_list(listvar):
    from mathutils import Vector

    for var in listvar:
        if not isinstance(var, Vector):
            return False
    return True


class VarStates:

    @staticmethod
    def store_states():
        # Store the display states, called upon unregister the Add-on
        # This is useful when you press F8 to reload the Addons.
        # Then this function preserves the display states of the
        # console variables.
        state_props = bpy.context.window_manager.MathVisStatePropList
        variables = get_math_data()

        for index, state_prop in reversed(list(enumerate(state_props))):
            if state_prop.name not in variables:
                # Variable has been removed from console
                state_props.remove(index)

        for key, ktype in variables.items():
            if key and key not in state_props:
                prop = state_props.add()
                prop.name = key
                prop.ktype = ktype.__name__
                prop.state = [True, False]

    @staticmethod
    def get_index(key):
        index = bpy.context.window_manager.MathVisStatePropList.find(key)
        return index

    @staticmethod
    def delete(key):
        state_props = bpy.context.window_manager.MathVisStatePropList
        index = state_props.find(key)
        if index != -1:
            state_props.remove(index)

    @staticmethod
    def toggle_display_state(key):
        state_props = bpy.context.window_manager.MathVisStatePropList
        if key in state_props:
            state_props[key].state[0] = not state_props[key].state[0]
        else:
            print("Odd: Can not find key %s in MathVisStateProps" % (key))

    @staticmethod
    def toggle_lock_state(key):
        state_props = bpy.context.window_manager.MathVisStatePropList
        if key in state_props:
            state_props[key].state[1] = not state_props[key].state[1]
        else:
            print("Odd: Can not find key %s in MathVisStateProps" % (key))


def get_math_data():
    from mathutils import Matrix, Vector, Quaternion, Euler

    locals = console_namespace()
    if not locals:
        return {}

    variables = {}
    for key, var in locals.items():
        if len(key) == 0 or key[0] == "_":
            continue

        type_var = type(var)

        # Rules out sets/dicts.
        # It's also possible the length check below is slow
        # for data with underlying linked-list structure.
        if not hasattr(type_var, "__getitem__"):
            continue

        # Don't do a truth test on the data because this causes an error with some
        # array types, see T66107.
        len_fn = getattr(type_var, "__len__", None)
        if len_fn is None:
            continue
        if len_fn(var) == 0:
            continue

        if isinstance(var, (Matrix, Vector, Quaternion, Euler)) or \
           isinstance(var, (tuple, list)) and is_display_list(var):

            variables[key] = type_var

    return variables


def cleanup_math_data():

    locals = console_namespace()
    if not locals:
        return

    variables = get_math_data()

    for key in variables.keys():
        index = VarStates.get_index(key)
        if index == -1:
            continue

        state_prop = bpy.context.window_manager.MathVisStatePropList.get(key)
        if state_prop.state[1]:
            continue

        del locals[key]
        bpy.context.window_manager.MathVisStatePropList.remove(index)


def console_math_data():
    from mathutils import Matrix, Vector, Quaternion, Euler

    data_matrix = {}
    data_quat = {}
    data_euler = {}
    data_vector = {}
    data_vector_array = {}

    for key, var in console_namespace().items():
        if key[0] == "_":
            continue

        state_prop = bpy.context.window_manager.MathVisStatePropList.get(key)
        if state_prop:
            disp, lock = state_prop.state
            if not disp:
                continue

        if isinstance(var, Matrix):
            if len(var.col) != 4 or len(var.row) != 4:
                if len(var.col) == len(var.row):
                    var = var.to_4x4()
                else:  # todo, support 4x3 matrix
                    continue
            data_matrix[key] = var
        elif isinstance(var, Vector):
            if len(var) < 3:
                var = var.to_3d()
            data_vector[key] = var
        elif isinstance(var, Quaternion):
            data_quat[key] = var
        elif isinstance(var, Euler):
            data_euler[key] = var
        elif type(var) in {list, tuple} and is_display_list(var):
            data_vector_array[key] = var

    return data_matrix, data_quat, data_euler, data_vector, data_vector_array
