# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy, json, hashlib
from . import __package__ as base_package

PIE_ADDON_KEYMAPS = {}

KEYMAP_ICONS = {
    'Object Mode': 'OBJECT_DATAMODE',
    'Window': 'WINDOW',
    '3D View': 'VIEW3D',
    'Mesh': 'OUTLINER_DATA_MESH',
    'Outliner': 'OUTLINER',
    'Object Non-modal': 'OBJECT_DATAMODE',
    'Sculpt': 'SCULPTMODE_HLT',
    'Armature': 'ARMATURE_DATA',
}

KEYMAP_UI_NAMES = {
    'Armature': "Armature Edit",
    'Object Non-modal': "Object Mode",
}

DEBUG = False

def register_hotkey(bl_idname, hotkey_kwargs, *, key_cat='Window', op_kwargs={}):
    """This function inserts a 'hash' into the created KeyMapItems' properties,
    so they can be compared to each other, and duplicates can be avoided."""

    global PIE_ADDON_KEYMAPS
    wm = bpy.context.window_manager

    space_type = wm.keyconfigs.default.keymaps[key_cat].space_type

    addon_keyconfig = wm.keyconfigs.addon
    if not addon_keyconfig:
        # This happens when running Blender in background mode.
        return

    # We limit the hash to a few digits, otherwise it errors when trying to store it.
    kmi_string = json.dumps(
        [bl_idname, hotkey_kwargs, key_cat, space_type, op_kwargs], sort_keys=True
    ).encode("utf-8")
    kmi_hash = hashlib.md5(kmi_string).hexdigest()

    # If it already exists, don't create it again.
    for existing_kmi_hash, existing_kmi_tup in PIE_ADDON_KEYMAPS.items():
        existing_addon_kc, existing_addon_km, existing_kmi = existing_kmi_tup
        if kmi_hash == existing_kmi_hash:
            # The hash we just calculated matches one that is in storage.
            user_kc = wm.keyconfigs.user
            user_km = user_kc.keymaps.get(existing_addon_km.name)
            # NOTE: It's possible on Reload Scripts that some KeyMapItems remain in storage,
            # but are unregistered by Blender for no reason.
            # I noticed this particularly in the Weight Paint keymap.
            # So it's not enough to check if a KMI with a hash is in storage, we also need to check if a corresponding user KMI exists.
            user_kmi = find_kmi_in_km_by_hash(user_km, kmi_hash)
            if user_kmi:
                print(
                    base_package + ": Hotkey already exists, skipping: ",
                    existing_kmi.name,
                    existing_kmi.to_string(),
                    kmi_hash,
                )
                return

    addon_keymaps = addon_keyconfig.keymaps
    addon_km = addon_keymaps.get(key_cat)
    if not addon_km:
        addon_km = addon_keymaps.new(name=key_cat, space_type=space_type)

    addon_kmi = addon_km.keymap_items.new(bl_idname, **hotkey_kwargs)
    for key in op_kwargs:
        value = op_kwargs[key]
        setattr(addon_kmi.properties, key, value)

    addon_kmi.properties['hash'] = kmi_hash

    PIE_ADDON_KEYMAPS[kmi_hash] = (
        addon_keyconfig,
        addon_km,
        addon_kmi,
    )


def draw_hotkey_list(layout, context, compact=False):
    user_kc = context.window_manager.keyconfigs.user

    keymap_data = list(PIE_ADDON_KEYMAPS.items())
    keymap_data = sorted(keymap_data, key=lambda tup: "".join(get_kmi_ui_info(tup[1][1], tup[1][2])))

    if not compact:
        split = layout.row().split(factor=0.6)
        row = split.row()
        row.label(text="Operator", icon='BLANK1')
        row.label(text="Keymap Category", icon='BLANK1')
        split.row().label(text="Key Combo")
        layout.separator()

    prev_kmi = None
    for kmi_hash, kmi_tup in keymap_data:
        addon_kc, addon_km, addon_kmi = kmi_tup

        user_km = user_kc.keymaps.get(addon_km.name)
        if not user_km:
            # This really shouldn't happen.
            continue
        user_kmi = find_kmi_in_km_by_hash(user_km, kmi_hash)

        col = layout.column()
        col.context_pointer_set("keymap", user_km)
        user_row = col.row()

        if DEBUG and False:
            # Debug code: Draw add-on and user KeyMapItems side-by-side.
            split = user_row.split(factor=0.5)
            addon_row = split.row()
            user_row = split.row()
            draw_kmi(addon_km, addon_kmi, addon_row)
        if not user_kmi:
            # This should only happen for one frame during Reload Scripts.
            print(
                base_package + ": Can't find this hotkey to draw: ",
                addon_kmi.name,
                addon_kmi.to_string(),
            )
            continue

        draw_kmi(user_km, user_kmi, user_row, compact=compact)
        prev_kmi = user_kmi


def draw_kmi(km, kmi, layout, compact=False):
    """A simplified version of draw_kmi from rna_keymap_ui.py."""

    if DEBUG:
        layout = layout.box()

    main_split = layout.split(factor=0.6)

    info_row = main_split.row(align=True)
    if DEBUG:
        info_row.prop(kmi, "show_expanded", text="", emboss=False)
    info_row.prop(kmi, "active", text="", emboss=False)
    km_icon, km_name, kmi_name = get_kmi_ui_info(km, kmi)
    if compact:
        kmi_name = kmi_name.replace(" Pie", "")
        km_name = ""
    info_row.label(text=kmi_name)
    info_row.label(text=km_name, icon=km_icon)

    keycombo_row = main_split.row(align=True)
    sub = keycombo_row.row(align=True)
    sub.enabled = kmi.active
    if kmi.idname == 'wm.call_menu_pie_drag_only':
        op_row = sub.row(align=True)
        if not compact:
            op_row.scale_x = 0.75
        text = "" if compact else "Drag"
        op = op_row.operator('wm.toggle_keymap_item_property', text=text, icon='MOUSE_MOVE', depress=kmi.properties.on_drag)
        op.prop_name = 'on_drag'
        op.addon_kmi_hash = kmi.properties['hash']
    sub.prop(kmi, "type", text="", full_event=True)

    if kmi.is_user_modified:
        keycombo_row.operator(
            "preferences.keyitem_restore", text="", icon='BACK'
        ).item_id = kmi.id

    if DEBUG and kmi.show_expanded:
        layout.template_keymap_item_properties(kmi)


def get_kmi_ui_info(km, kmi) -> tuple[str, str, str]:
    km_name = km.name
    km_icon = KEYMAP_ICONS.get(km_name, 'BLANK1')
    km_name = KEYMAP_UI_NAMES.get(km_name, km_name)
    if kmi.idname.startswith('wm.call_menu_pie'):
        bpy_type = getattr(bpy.types, kmi.properties.name)
        kmi_name = bpy_type.bl_label + " Pie"
    else:
        parts = kmi.idname.split(".")
        bpy_type = getattr(bpy.ops, parts[0])
        bpy_type = getattr(bpy_type, parts[1])
        kmi_name = bpy_type.get_rna_type().name

    return km_icon, km_name, kmi_name


def print_kmi(kmi):
    idname = kmi.idname
    keys = kmi.to_string()
    props = str(list(kmi.properties.items()))
    print(idname, props, keys)


def find_kmi_in_km_by_hash(keymap, kmi_hash):
    """There's no solid way to match modified user keymap items to their
    add-on equivalent, which is necessary to draw them in the UI reliably.

    To remedy this, we store a hash in the KeyMapItem's properties.

    This function lets us find a KeyMapItem with a stored hash in a KeyMap.
    Eg., we can pass a User KeyMap and an Addon KeyMapItem's hash, to find the
    corresponding user keymap, even if it was modified.

    The hash value is unfortunately exposed to the users, so we just hope they don't touch that.
    """

    for kmi in keymap.keymap_items:
        if not kmi.properties:
            continue
        try:
            if 'hash' not in kmi.properties:
                continue
        except TypeError:
            # Happens sometimes on file load...?
            continue

        if kmi.properties['hash'] == kmi_hash:
            return kmi


class WM_OT_toggle_keymap_item_on_drag(bpy.types.Operator):
    "Toggle whether this pie menu should only appear after mouse drag"
    bl_idname = "wm.toggle_keymap_item_property"
    bl_label = "Toggle On Drag"
    bl_options = {'REGISTER', 'INTERNAL'}

    addon_kmi_hash: bpy.props.StringProperty(options={'SKIP_SAVE'})
    prop_name: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        # Another sign of the fragility of Blender's keymap API.
        # The reason for the existence of this property wrapper operator is that
        # when we draw the `on_drag` property in the UI directly, Blender's keymap
        # system (for some reason??) doesn't realize that a keymap entry has changed,
        # and fails to refresh caches, which has disasterous results.
        # This operator fires a refreshing of internal keymap data via
        # `user_kmi.type = user_kmi.type`
        addon_tup = PIE_ADDON_KEYMAPS.get(self.addon_kmi_hash)
        if not addon_tup:
            self.report({'ERROR'}, "Failed to find add-on KeymapItem with the given hash.")
            return {'CANCELLED'}
        
        addon_kc, addon_km, addon_kmi = addon_tup
        user_kc = context.window_manager.keyconfigs.user
        user_km = user_kc.keymaps.get(addon_km.name)

        user_kmi = find_kmi_in_km_by_hash(user_km, self.addon_kmi_hash)
        if not user_kmi:
            self.report({'ERROR'}, "Failed to find user KeymapItem corresponding to stored hash.")
            return {'CANCELLED'}
        
        if user_kmi.properties and hasattr(user_kmi.properties, self.prop_name):
            setattr(user_kmi.properties, self.prop_name, not getattr(user_kmi.properties, self.prop_name))
            # This is the magic line that causes internal keymap data to be kept up to date and not break.
            user_kmi.type = user_kmi.type
        else:
            self.report({'ERROR'}, "Property not in keymap: " + self.prop_name)
            return {'CANCELLED'}

        return {'FINISHED'}

registry = [
    WM_OT_toggle_keymap_item_on_drag,
]

def unregister():
    global PIE_ADDON_KEYMAPS
    for kmi_hash, km_tuple in PIE_ADDON_KEYMAPS.items():
        kc, km, kmi = km_tuple
        km.keymap_items.remove(kmi)

    PIE_ADDON_KEYMAPS = {}
