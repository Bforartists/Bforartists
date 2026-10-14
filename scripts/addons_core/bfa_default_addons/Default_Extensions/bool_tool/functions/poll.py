import bpy

from ..constants import (
    CONVERTABLE_TYPES,
)
from .mesh import (
    is_instanced_mesh,
)
from .object import (
    has_evaluated_mesh,
)


#### ------------------------------ FUNCTIONS ------------------------------ ####

def basic_poll(cls, context, check_active=True):
    """Basic poll for Boolean operators."""

    if context.mode != 'OBJECT':
        cls.poll_message_set("Boolean operators can only be performed in Object Mode")
        return False

    if check_active:
        if context.active_object is None:
            cls.poll_message_set("No active object")
            return False

    return True


def destructive_op_confirmation(cls, context, event, canvases: list, title="Boolean Operation"):
    """
    Creates & returns the confirmation pop-up window for destructive Boolean operators.\n
    Confirmation window is triggered by canvases that have instanced data or shape keys.\n
    If none of the canvases have them the operator is executed without any confirmation.
    """

    if len(canvases) == 0:
        return cls.execute(context)

    has_instanced_data = any(obj for obj in canvases if is_instanced_mesh(obj.data))
    has_shape_keys = any(obj for obj in canvases if obj.data.shape_keys)

    if has_instanced_data or has_shape_keys:
        # Instanced data message.
        if has_instanced_data and not has_shape_keys:
            message = ("Object(s) you're trying to cut have instanced object data.\n"
                       "In order to apply modifiers, they need to be made single-user.\n"
                       "Do you proceed?")

        # Shape keys message.
        if has_shape_keys and not has_instanced_data:
            message = ("Object(s) you're trying to cut have shape keys.\n"
                       "In order to apply modifiers shape keys need to be applied as well.\n"
                       "Do you proceed?")

        # Combined message.
        if has_instanced_data and has_shape_keys:
            message = ("Object(s) you're trying to cut have shape keys and instanced object data.\n"
                       "In order to apply modifiers shape keys need to be applied & object data made single user.\n"
                       "Do you proceed?")

        popup = context.window_manager.invoke_confirm(cls, event, title=title,
                                                      confirm_text="Yes", icon='WARNING',
                                                      message=message)

        cls._unflippable = True
        return popup

    # Execute without confirmation window.
    else:
        return cls.execute(context)


def convert_to_mesh_confirmation(cls, context, event, cutters: list, title="Boolean Operation"):
    """
    Creates & returns the confirmation pop-up window when the object is
    about to be converted to mesh to be used as a cutter.

    NOTE (1): Only triggers during brush Boolean operators,
    because object gets destroyed in the destructive one anyway.

    NOTE (2): This is only required because of the limitation of legacy Boolean modifier.
    Geometry nodes implementation works with any object type. When the add-on is
    updated to work with custom modifiers this will not be necesary anymore.
    """

    if len(cutters) == 0:
        return cls.execute(context)

    is_convertable = any(
        obj.type in CONVERTABLE_TYPES and has_evaluated_mesh(context, obj)
        for obj in cutters
    )

    if is_convertable:
        message = ("Some of the selected objects are not of the Mesh type, but output mesh.\n"
                   "In order to use them as cutters, they need to be converted to mesh.\n"
                   "This is a destructive operator. Do you proceed?")

        popup = context.window_manager.invoke_confirm(cls, event, title=title,
                                                      confirm_text="Yes", icon='WARNING',
                                                      message=message)

        cls._unflippable = True
        return popup

    # Execute without confirmation window.
    else:
        return cls.execute(context)



#### ------------------------------ /operator_helpers/ ------------------------------ ####

def _guess_toggle_state(modifiers):
    """Guess whether cutters should be hidden or revealed."""

    enabled = 0
    disabled = 0
    for mod in modifiers:
        if mod.show_viewport:
            enabled += 1
        else:
            disabled += 1

    if enabled > disabled:
        return "On"
    else:
        return "Off"
