from rna_keymap_ui import _indented_layout, draw_km
from .keymaps import addon_keymaps

def draw_kmi(display_keymaps, kc, km, kmi, layout, level, label=''):
    map_type = kmi.map_type

    col = _indented_layout(layout, level)

    if kmi.show_expanded:
        col = col.column(align=True)
        box = col.box()
    else:
        box = col.column()

    split = box.split()

    # header bar
    row = split.row(align=True)
    row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)

    if km.is_modal:
        row.separator()
        row.prop(kmi, "propvalue", text="")
    else:
        label = kmi.name if label == '' else label
        row.label(text=label)

    row = split.row()
    row.prop(kmi, "map_type", text="")
    if map_type == 'KEYBOARD':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'MOUSE':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'NDOF':
        row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        subrow = row.row()
        subrow.prop(kmi, "type", text="")
        subrow.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        row.prop(kmi, "type", text="")
    else:
        row.label()

    if (not kmi.is_user_defined) and kmi.is_user_modified:
        row.operator("preferences.keyitem_restore", text="", icon='BACK').item_id = kmi.id
    else:
        row.operator(
            "preferences.keyitem_remove",
            text="",
            # Abusing the tracking icon, but it works pretty well here.
            icon=('TRACKING_CLEAR_BACKWARDS' if kmi.is_user_defined else 'X')
        ).item_id = kmi.id

    # Expanded, additional event settings
    if kmi.show_expanded:
        box = col.box()

        split = box.split(factor=0.4)
        sub = split.row()

        if km.is_modal:
            sub.prop(kmi, "propvalue", text="")
        else:
            # One day...
            # sub.prop_search(kmi, "idname", bpy.context.window_manager, "operators_all", text="")
            sub.prop(kmi, "idname", text="")

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            sub = split.column()
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
                subrow_repeat = subrow.row(align=True)
                subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
                subrow_repeat.prop(kmi, "repeat", text="Repeat")
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            if map_type in {'KEYBOARD', 'MOUSE'} and kmi.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.prop(kmi, "direction")

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)
            # Use `*_ui` properties as integers aren't practical.
            subrow.prop(kmi, "shift_ui", toggle=True)
            subrow.prop(kmi, "ctrl_ui", toggle=True)
            subrow.prop(kmi, "alt_ui", toggle=True)
            subrow.prop(kmi, "oskey_ui", text="Cmd", toggle=True)

            subrow.prop(kmi, "key_modifier", text="", event=True)

        # Operator properties
        box.template_keymap_item_properties(kmi)

        # Modal key maps attached to this operator
        if not km.is_modal:
            kmm = kc.keymaps.find_modal(kmi.idname)
            if kmm:
                draw_km(display_keymaps, kc, kmm, None, layout, level + 1)
                layout.context_pointer_set("keymap", km)


def find_matching_keymaps(keyconfig):
    for km_add, kmi_add in addon_keymaps:
        km = keyconfig.keymaps[km_add.name]

        for kmi_con in km.keymap_items:
            if kmi_add.idname == kmi_con.idname:
                yield (km, kmi_con)


def draw_keyboard_shorcuts(pref_data, layout, context, keymap_spacing=0.15):
    col = layout.box().column()
    row = col.row(align=True)
    wm = context.window_manager
    show_keymaps = pref_data.show_keymaps

    if show_keymaps:
        row.prop(pref_data, "show_keymaps", text="", icon="DISCLOSURE_TRI_DOWN", emboss=False)
    else:
        row.prop(pref_data, "show_keymaps", text="", icon="DISCLOSURE_TRI_RIGHT", emboss=False)
    row.label(text="Keymap List:", icon="KEYINGSET")

    if not show_keymaps:
        return

    kc = wm.keyconfigs.user
    # TIP - The list(dic.fromkeys is for removing duplicate keymaps
    get_kmi_l = list(dict.fromkeys(find_matching_keymaps(keyconfig=kc)))

    for km, kmi in get_kmi_l:
        label = ''
        col.context_pointer_set("keymap", km)
        draw_kmi([], kc, km, kmi, col, level=0, label=label)
        col.separator(factor=keymap_spacing)
