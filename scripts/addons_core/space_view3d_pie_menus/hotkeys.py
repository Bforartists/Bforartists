# SPDX-FileCopyrightText: 2016-2024 Blender Foundation
#
# SPDX-License-Identifier: GPL-3.0-or-later

import bpy

PIE_ADDON_KEYMAPS = []

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


def register_hotkey(
        bl_idname, 
        *, 
        op_kwargs={}, 
        hotkey_kwargs={'type': "SPACE", 'value': "PRESS"}, 
        keymap_name='Window'
    ):

    global PIE_ADDON_KEYMAPS
    wm = bpy.context.window_manager

    space_type = wm.keyconfigs.default.keymaps[keymap_name].space_type

    addon_keyconfig = wm.keyconfigs.addon
    if not addon_keyconfig:
        # This happens when running Blender in background mode.
        return

    addon_keymaps = addon_keyconfig.keymaps
    addon_km = addon_keymaps.get(keymap_name)
    if not addon_km:
        addon_km = addon_keymaps.new(name=keymap_name, space_type=space_type)

    addon_kmi = addon_km.keymap_items.new(bl_idname, **hotkey_kwargs)
    for key in op_kwargs:
        value = op_kwargs[key]
        setattr(addon_kmi.properties, key, value)

    PIE_ADDON_KEYMAPS.append((addon_km, addon_kmi))


def get_sidebar(context):
    if not context.area.type == 'VIEW_3D':
        return None
    for region in context.area.regions:
        if region.type == 'UI':
            return region


def get_user_kmis_of_addon(context) -> list[tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]]:
    """This would ideally work by getting the AddonKMIs that we are already storing,
    but there's no PyAPI call for that.
    So for now, we just get the list of add-on related keymaps by hard-coding some operator names,
    which were presumably hotkeyed by this add-on."""

    ret = []

    if bpy.app.version >= (4, 5, 0):
        context.window_manager.keyconfigs.update()
        for addon_km, addon_kmi in PIE_ADDON_KEYMAPS:
            user_km = context.window_manager.keyconfigs.user.keymaps.get(addon_km.name)
            if not user_km:
                # This should never happen.
                print("Failed to find User KeyMap: ", addon_km.name)
                continue
            user_kmi = user_km.keymap_items.find_match(addon_km, addon_kmi)
            if not user_kmi:
                # This shouldn't really happen, but maybe it can, eg. if user changes idname.
                print("Failed to find User KeyMapItem: ", addon_km.name, addon_kmi.idname)
                continue
            ret.append((user_km, user_kmi))
    else:
        # Pre-Blender 4.5: We have to guess which user KMIs correspond to our addon KMIs, 
        # in this case based on operator idnames.
        keymap_names = set([addon_km.name for addon_km, addon_kmi in PIE_ADDON_KEYMAPS])
        user_kc = context.window_manager.keyconfigs.user

        for keymap_name in keymap_names:
            user_km = user_kc.keymaps.get(keymap_name)
            if not user_km:
                # This really shouldn't happen.
                continue

            for user_kmi in user_km.keymap_items:
                if user_kmi.idname in ('wm.call_menu_pie_drag_only', 'screen.area_join'):
                    if (user_km, user_kmi) not in ret:
                        ret.append((user_km, user_kmi))

    # Sort hotkeys by what's drawn in UI: keymap and pie name.
    ret.sort(
        key=lambda tup: "".join(get_kmi_ui_info(tup[0], tup[1])[1:])
    )

    return ret


def get_user_kmi_of_addon(context, keymap_name, op_idname, op_kwargs) -> tuple[bpy.types.KeyMap, bpy.types.KeyMapItem]:
    all_kmis = get_user_kmis_of_addon(context)
    for user_km, user_kmi in all_kmis:
        try:
            if (
                user_km.name == keymap_name and
                user_kmi.idname == op_idname and
                user_kmi.properties and 
                all([user_kmi.properties[key] == value for key, value in op_kwargs.items()])
            ):
                return user_km, user_kmi
        except KeyError:
            continue

    return None, None


def draw_hotkey_list(layout, context, compact=False):
    save_row = layout.row()
    save_row.operator('window.extra_pies_prefs_save', icon='FILE_TICK')
    save_row.operator('window.extra_pies_prefs_load', icon='IMPORT')

    sidebar = get_sidebar(context)
    if sidebar:
        compact = sidebar.width < 600

    if not compact:
        split = layout.row().split(factor=0.6)
        row = split.row()
        row.label(text="Pie Menu", icon='BLANK1')
        row.label(text="Keymap Name", icon='BLANK1')
        split.row().label(text="Key Combo")
        layout.separator()

    col = layout.column()

    for user_km, user_kmi in get_user_kmis_of_addon(context):
        col.context_pointer_set("keymap", user_km)
        draw_kmi(user_km, user_kmi, col.row(), compact)


def draw_kmi(km, kmi, layout, compact=False):
    """A simplified version of draw_kmi from rna_keymap_ui.py."""

    if DEBUG:
        layout = layout.box()

    first_split = layout.split(factor=0.6)

    info_row = first_split.row(align=True)
    if DEBUG:
        info_row.prop(kmi, "show_expanded", text="", emboss=False)
    info_row.prop(kmi, "active", text="", emboss=False)
    km_icon, km_name, kmi_name = get_kmi_ui_info(km, kmi)
    if compact:
        km_name = ""
    info_row.label(text=kmi_name)
    info_row.label(text=km_name, icon=km_icon)

    second_split = first_split.split(align=True, factor=0.6)
    sub = second_split.row(align=True)
    sub.enabled = kmi.active
    sub.prop(kmi, "type", text="", full_event=True)

    op_ui = second_split
    if kmi.is_user_modified:
        op_ui = third_split = second_split.split(align=True, factor=0.65)

    if kmi.idname == 'wm.call_menu_pie_drag_only':
        if not kmi.properties:
            sub.label(text="Missing properties. This should never happen!")
            return
        text = "" if compact else "Drag"
        
        sub = op_ui.row(align=True)
        sub.enabled = kmi.active
        op = sub.operator(
            'wm.toggle_keymap_item_property',
            text=text,
            icon='MOUSE_MOVE',
            depress=kmi.properties.on_drag,
        )
        op.km_name = km.name
        op.kmi_idname = kmi.idname
        op.pie_name = kmi.properties.name
        op.prop_name = 'on_drag'

    if kmi.is_user_modified:
        op_ui.operator(
            "preferences.keyitem_restore", text="", icon='BACK'
        ).item_id = kmi.id

    if DEBUG and kmi.show_expanded:
        layout.template_keymap_item_properties(kmi)


def get_kmi_ui_info(km, kmi) -> tuple[str, str, str]:
    km_name = km.name
    km_icon = KEYMAP_ICONS.get(km_name, 'BLANK1')
    km_name = KEYMAP_UI_NAMES.get(km_name, km_name)
    if kmi.properties and kmi.idname.startswith('wm.call_menu_pie'):
        if not hasattr(kmi.properties, 'name'):
            # Apparently this can happen when spamming the Reload Scripts operator...
            return "", "", ""
        name = kmi.properties.name
        if name:
            try:
                bpy_type = getattr(bpy.types, kmi.properties.name)
                kmi_name = bpy_type.bl_label
            except:
                kmi_name = "Missing (code 1). Try restarting."
        else:
            kmi_name = "Missing (code 2). Try restarting."
    else:
        try:
            parts = kmi.idname.split(".")
            bpy_type = getattr(bpy.ops, parts[0])
            bpy_type = getattr(bpy_type, parts[1])
            kmi_name = bpy_type.get_rna_type().name
        except:
            kmi_name = "Missing (code 3). Try restarting."

    return km_icon, km_name, kmi_name


def print_kmi(kmi):
    idname = kmi.idname
    keys = kmi.to_string()
    props = str(list(kmi.properties.items()))
    print(idname, props, keys)


class WM_OT_toggle_keymap_item_on_drag(bpy.types.Operator):
    "When Drag is enabled, this pie menu will only appear when the mouse is dragged while the assigned key combo is held down"
    bl_idname = "wm.toggle_keymap_item_property"
    bl_label = "Toggle On Drag"
    bl_options = {'REGISTER', 'INTERNAL'}

    km_name: bpy.props.StringProperty(options={'SKIP_SAVE'})
    kmi_idname: bpy.props.StringProperty(options={'SKIP_SAVE'})
    pie_name: bpy.props.StringProperty(options={'SKIP_SAVE'})
    prop_name: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        # Another sign of the fragility of Blender's keymap API.
        # The reason for the existence of this property wrapper operator is that
        # when we draw the `on_drag` property in the UI directly, Blender's keymap
        # system (for some reason??) doesn't realize that a keymap entry has changed,
        # and fails to refresh caches, which has disasterous results.
        # This operator fires a refreshing of internal keymap data via
        # `user_kmi.type = user_kmi.type`

        user_kc = context.window_manager.keyconfigs.user
        user_km = user_kc.keymaps.get(self.km_name)
        if not user_km:
            # This really shouldn't happen.
            self.report({'ERROR'}, f"Couldn't find KeyMap: {self.km_name}")
            return {'CANCELLED'}

        for user_kmi in user_km.keymap_items:
            if user_kmi.idname == self.kmi_idname and user_kmi.properties and user_kmi.properties.name == self.pie_name:
                if hasattr(user_kmi.properties, self.prop_name):
                    setattr(
                        user_kmi.properties,
                        self.prop_name,
                        not getattr(user_kmi.properties, self.prop_name),
                    )
                    # This is the magic line that causes internal keymap data to be kept up to date and not break.
                    user_kmi.type = user_kmi.type
                else:
                    self.report({'ERROR'}, "Property not in keymap: " + self.prop_name)
                    return {'CANCELLED'}

        return {'FINISHED'}

def refresh_all_kmis():
    context = bpy.context
    user_kc = context.window_manager.keyconfigs.user
    for km in user_kc.keymaps:
        for kmi in km.keymap_items:
            kmi.type = kmi.type

registry = [
    WM_OT_toggle_keymap_item_on_drag,
]


def unregister():
    global PIE_ADDON_KEYMAPS
    for addon_km, addon_kmi in PIE_ADDON_KEYMAPS:
        addon_km.keymap_items.remove(addon_kmi)
