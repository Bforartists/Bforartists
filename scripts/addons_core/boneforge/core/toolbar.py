"""BoneCraft's tools in the 3D Viewport tool bar, kept to one copy each.

``bpy.utils.unregister_tool`` removes a tool through the class that registered it. After an add-on
reload that class is gone: the new module's class cannot remove the old copy, and the tool bar would
show the tool twice. ``register``/``unregister`` here remove every tool with the class's id first,
whichever class (or reloaded copy) added it, together with its keymap.
"""
import bpy


def _tools(tool_cls):
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    panel = ToolSelectPanelHelper._tool_class_from_space_type(tool_cls.bl_space_type)
    return None if panel is None else panel._tools.get(tool_cls.bl_context_mode)


def _find(tools, idname):
    """The ToolDef with this id in a mode's tool list (top level or inside a group), or None."""
    for item in tools:
        if type(item) is tuple:                          # a group (a ToolDef is a named tuple, not a group)
            for sub in item:
                if getattr(sub, "idname", None) == idname:
                    return sub
        elif getattr(item, "idname", None) == idname:
            return item
    return None


def drop(tool_cls):
    """Remove every tool with ``tool_cls``'s id from its mode's tool bar."""
    tools = _tools(tool_cls)
    if tools is None:
        return
    while True:
        tool_def = _find(tools, tool_cls.bl_idname)
        if tool_def is None:
            break
        stand_in = type("BoneCraftToolStandIn", (), {
            "bl_space_type": tool_cls.bl_space_type,
            "bl_context_mode": tool_cls.bl_context_mode,
            "_bl_tool": tool_def,
        })
        bpy.utils.unregister_tool(stand_in)              # removes it and its keymap
    if "_bl_tool" in tool_cls.__dict__:
        del tool_cls._bl_tool


def register(tool_cls, **kwargs):
    drop(tool_cls)
    bpy.utils.register_tool(tool_cls, **kwargs)


def unregister(tool_cls):
    drop(tool_cls)
