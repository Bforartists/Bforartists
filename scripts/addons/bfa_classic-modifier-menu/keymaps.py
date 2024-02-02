import bpy
from .operators import (
    INVOKE_OT_ADD_GPENCIL_SHADERFX_MENU, 
    INVOKE_OT_CLASSIC_MODIFIER_MENU, 
    INVOKE_OT_ASSET_MODIFIER_MENU, 
    INVOKE_OT_ADD_GPENCIL_MODIFIER_MENU, 
    INVOKE_OT_ADD_GPENCIL_SHADERFX_MENU,
    INVOKE_OT_ADD_CONSTRAINTS_MENU,
    INVOKE_OT_ADD_BONE_CONSTRAINTS_MENU,
    )

addon_keymaps = []
keymap_defs = (
    (INVOKE_OT_CLASSIC_MODIFIER_MENU.bl_idname, 'A', True, None),
    (INVOKE_OT_ASSET_MODIFIER_MENU.bl_idname, 'NONE', False, None),
    (INVOKE_OT_ADD_GPENCIL_MODIFIER_MENU.bl_idname, 'A', True, None),
    (INVOKE_OT_ADD_GPENCIL_SHADERFX_MENU.bl_idname, 'A', True, None),
    (INVOKE_OT_ADD_CONSTRAINTS_MENU.bl_idname, 'A', True, None),
    (INVOKE_OT_ADD_BONE_CONSTRAINTS_MENU.bl_idname, 'A', True, None),
)

def register():
    addon_keymaps.clear()
    key_config = bpy.context.window_manager.keyconfigs.addon

    if key_config:
        key_map = key_config.keymaps.new(
            name='Property Editor', space_type="PROPERTIES", region_type='WINDOW')
        for operator, key, shift, props in keymap_defs:
            keymap_item = key_map.keymap_items.new(
                operator, key, value='PRESS', shift=shift)

            addon_keymaps.append((key_map, keymap_item))


def unregister():
    for key_map, key_entry in addon_keymaps:
        key_map.keymap_items.remove(key_entry)
    addon_keymaps.clear()
