# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Copyright 2011, Ryan Inch

import bpy

from bpy.types import (
    Operator,
    Panel,
    UIList,
)

from bpy.props import (
    BoolProperty,
    StringProperty,
)

from .internals import (
    collection_tree,
    collection_state,
    expanded,
    get_max_lvl,
    layer_collections,
    rto_history,
    expand_history,
    phantom_history,
    copy_buffer,
    swap_buffer,
    qcd_slots,
    update_collection_tree,
    update_property_group,
    generate_state,
    get_move_selection,
    get_move_active,
    update_qcd_header,
)


preview_collections = {}
last_icon_theme_text = None
last_icon_theme_text_sel = None


class CollectionManager(Operator):
    bl_label = "Collection Manager"
    bl_idname = "view3d.collection_manager"

    last_view_layer = ""

    window_open = False

    master_collection: StringProperty(
        default='Scene Collection',
        name="",
        description="Scene Collection"
        )

    def __init__(self):
        self.window_open = True

    def draw(self, context):
        cls = CollectionManager
        layout = self.layout
        cm = context.scene.collection_manager
        prefs = context.preferences.addons[__package__].preferences
        view_layer = context.view_layer

        if view_layer.name != cls.last_view_layer:
            if prefs.enable_qcd:
                bpy.app.timers.register(update_qcd_header)

            update_collection_tree(context)
            cls.last_view_layer = view_layer.name

        # title and view layer
        title_row = layout.split(factor=0.5)
        main = title_row.row()
        view = title_row.row(align=True)
        view.alignment = 'RIGHT'

        main.label(text="Collection Manager")

        view.prop(view_layer, "use", text="")
        view.separator()

        window = context.window
        scene = window.scene
        view.template_search(
            window, "view_layer",
            scene, "view_layers",
            new="scene.view_layer_add",
            unlink="scene.view_layer_remove")

        layout.row().separator()
        layout.row().separator()

        # buttons
        button_row = layout.row()

        op_sec = button_row.row()
        op_sec.alignment = 'LEFT'

        collapse_sec = op_sec.row()
        collapse_sec.alignment = 'LEFT'
        collapse_sec.enabled = False

        if len(expanded) > 0:
            text = "Collapse All Items"
        else:
            text = "Expand All Items"

        collapse_sec.operator("view3d.expand_all_items", text=text)

        for laycol in collection_tree:
            if laycol["has_children"]:
                collapse_sec.enabled = True
                break

        if prefs.enable_qcd:
            renum_sec = op_sec.row()
            renum_sec.alignment = 'LEFT'
            renum_sec.operator("view3d.renumerate_qcd_slots")

        # filter
        filter_sec = button_row.row()
        filter_sec.alignment = 'RIGHT'

        filter_sec.popover(panel="COLLECTIONMANAGER_PT_display_options",
                           text="", icon='FILTER')

        mc_box = layout.box()
        master_collection_row = mc_box.row(align=True)

        # collection icon
        c_icon = master_collection_row.row()
        highlight = False
        if (context.view_layer.active_layer_collection ==
            context.view_layer.layer_collection):
                highlight = True

        prop = c_icon.operator("view3d.set_active_collection",
                                              text='', icon='GROUP', depress=highlight)
        prop.collection_index = -1
        prop.collection_name = 'Master Collection'

        master_collection_row.separator()

        # name
        name_row = master_collection_row.row()
        name_row.prop(self, "master_collection", text='')
        name_row.enabled = False

        master_collection_row.separator()

        # global rtos
        global_rto_row = master_collection_row.row()
        global_rto_row.alignment = 'RIGHT'

        row_setcol = global_rto_row.row()
        row_setcol.alignment = 'LEFT'
        row_setcol.operator_context = 'INVOKE_DEFAULT'
        selected_objects = get_move_selection()
        active_object = get_move_active()
        collection = context.view_layer.layer_collection.collection

        icon = 'MESH_CUBE'

        if selected_objects:
            if active_object and active_object.name in collection.objects:
                icon = 'SNAP_VOLUME'

            elif not set(selected_objects).isdisjoint(collection.objects):
                icon = 'STICKY_UVS_LOC'

        else:
            row_setcol.enabled = False

        prop = row_setcol.operator("view3d.set_collection", text="",
                                   icon=icon, emboss=False)
        prop.collection_index = 0
        prop.collection_name = 'Master Collection'

        copy_icon = 'COPYDOWN'
        swap_icon = 'ARROW_LEFTRIGHT'
        copy_swap_icon = 'SELECT_INTERSECT'

        if cm.show_exclude:
            exclude_all_history = rto_history["exclude_all"].get(view_layer.name, [])
            depress = True if len(exclude_all_history) else False
            icon = 'CHECKBOX_HLT'
            buffers = [False, False]

            if copy_buffer["RTO"] == "exclude":
                icon = copy_icon
                buffers[0] = True

            if swap_buffer["A"]["RTO"] == "exclude":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_exclude_all_collections", text="", icon=icon, depress=depress)

        if cm.show_selectable:
            select_all_history = rto_history["select_all"].get(view_layer.name, [])
            depress = True if len(select_all_history) else False
            icon = 'RESTRICT_SELECT_OFF'
            buffers = [False, False]

            if copy_buffer["RTO"] == "select":
                icon = copy_icon
                buffers[0] = True

            if swap_buffer["A"]["RTO"] == "select":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_restrict_select_all_collections", text="", icon=icon, depress=depress)

        if cm.show_hide_viewport:
            hide_all_history = rto_history["hide_all"].get(view_layer.name, [])
            depress = True if len(hide_all_history) else False
            icon = 'HIDE_OFF'
            buffers = [False, False]

            if copy_buffer["RTO"] == "hide":
                icon = copy_icon
                buffers[0] = True

            if swap_buffer["A"]["RTO"] == "hide":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_hide_all_collections", text="", icon=icon, depress=depress)

        if cm.show_disable_viewport:
            disable_all_history = rto_history["disable_all"].get(view_layer.name, [])
            depress = True if len(disable_all_history) else False
            icon = 'RESTRICT_VIEW_OFF'
            buffers = [False, False]

            if copy_buffer["RTO"] == "disable":
                icon = copy_icon
                buffers[0] = True

            if swap_buffer["A"]["RTO"] == "disable":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_disable_viewport_all_collections", text="", icon=icon, depress=depress)

        if cm.show_render:
            render_all_history = rto_history["render_all"].get(view_layer.name, [])
            depress = True if len(render_all_history) else False
            icon = 'RESTRICT_RENDER_OFF'
            buffers = [False, False]

            if copy_buffer["RTO"] == "render":
                icon = copy_icon
                buffers[0] = True

            if swap_buffer["A"]["RTO"] == "render":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_disable_render_all_collections", text="", icon=icon, depress=depress)

        # treeview
        layout.row().template_list("CM_UL_items", "",
                                   cm, "cm_list_collection",
                                   cm, "cm_list_index",
                                   rows=15,
                                   sort_lock=True)

        # add collections
        addcollec_row = layout.row()
        addcollec_row.operator("view3d.add_collection", text="Add Collection",
                               icon='COLLECTION_NEW').child = False

        addcollec_row.operator("view3d.add_collection", text="Add SubCollection",
                               icon='COLLECTION_NEW').child = True

        # phantom mode
        phantom_row = layout.row()
        toggle_text = "Disable " if cm.in_phantom_mode else "Enable "
        phantom_row.operator("view3d.toggle_phantom_mode", text=toggle_text+"Phantom Mode")

        if cm.in_phantom_mode:
            view.enabled = False
            if prefs.enable_qcd:
                renum_sec.enabled = False

            c_icon.enabled = False
            row_setcol.enabled = False
            addcollec_row.enabled = False


    def execute(self, context):
        wm = context.window_manager

        update_property_group(context)

        cm = context.scene.collection_manager
        view_layer = context.view_layer

        self.view_layer = view_layer.name

        # make sure list index is valid
        if cm.cm_list_index >= len(cm.cm_list_collection):
            cm.cm_list_index = -1

        # check if expanded & history/buffer state still correct
        if collection_state:
            new_state = generate_state()

            if new_state["name"] != collection_state["name"]:
                copy_buffer["RTO"] = ""
                copy_buffer["values"].clear()

                swap_buffer["A"]["RTO"] = ""
                swap_buffer["A"]["values"].clear()
                swap_buffer["B"]["RTO"] = ""
                swap_buffer["B"]["values"].clear()

                for name in list(expanded):
                    laycol = layer_collections.get(name)
                    if not laycol or not laycol["has_children"]:
                        expanded.remove(name)

                for name in list(expand_history["history"]):
                    laycol = layer_collections.get(name)
                    if not laycol or not laycol["has_children"]:
                        expand_history["history"].remove(name)

                for rto, history in rto_history.items():
                    if view_layer.name in history:
                        del history[view_layer.name]


            else:
                for rto in ["exclude", "select", "hide", "disable", "render"]:
                    if new_state[rto] != collection_state[rto]:
                        if view_layer.name in rto_history[rto]:
                            del rto_history[rto][view_layer.name]

                        if view_layer.name in rto_history[rto+"_all"]:
                            del rto_history[rto+"_all"][view_layer.name]

        # check if in phantom mode and if it's still viable
        if cm.in_phantom_mode:
            if layer_collections.keys() != phantom_history["initial_state"].keys():
                cm.in_phantom_mode = False

            if view_layer.name != phantom_history["view_layer"]:
                cm.in_phantom_mode = False

            if not cm.in_phantom_mode:
                for key, value in phantom_history.items():
                    try:
                        value.clear()
                    except AttributeError:
                        if key == "view_layer":
                            phantom_history["view_layer"] = ""

        # handle window sizing
        max_width = 960
        min_width = 456
        row_indent_width = 15
        width_step = 21
        qcd_width = 30
        scrollbar_width = 21
        lvl = get_max_lvl()

        width = min_width + row_indent_width + (width_step * lvl)

        if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
            width += qcd_width

        if len(layer_collections) > 14:
            width += scrollbar_width

        if width > max_width:
            width = max_width

        return wm.invoke_popup(self, width=width)

    def __del__(self):
        global collection_state

        if not self.window_open:
            # prevent destructor execution when changing templates
            return

        collection_state.clear()
        collection_state.update(generate_state())


class CM_UL_items(UIList):
    last_filter_value = ""

    filter_by_selected: BoolProperty(
                        name="Filter By Selected",
                        default=False,
                        description="Filter collections by selected items"
                        )
    filter_by_qcd: BoolProperty(
                        name="Filter By QCD",
                        default=False,
                        description="Filter collections to only show QCD slots"
                        )

    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        self.use_filter_show = True

        cm = context.scene.collection_manager
        prefs = context.preferences.addons[__package__].preferences
        view_layer = context.view_layer
        laycol = layer_collections[item.name]
        collection = laycol["ptr"].collection
        selected_objects = get_move_selection()
        active_object = get_move_active()

        column = layout.column(align=True)

        main_row = column.row()

        s1 = main_row.row(align=True)
        s1.alignment = 'LEFT'

        s2 = main_row.row(align=True)
        s2.alignment = 'RIGHT'

        row = s1

        # allow room to select the row from the beginning
        row.separator()

        # indent child items
        if laycol["lvl"] > 0:
            for _ in range(laycol["lvl"]):
                row.label(icon='BLANK1')

        # add expander if collection has children to make UIList act like tree view
        if laycol["has_children"]:
            if laycol["expanded"]:
                highlight = True if expand_history["target"] == item.name else False

                prop = row.operator("view3d.expand_sublevel", text="",
                                    icon='DISCLOSURE_TRI_DOWN',
                                    emboss=highlight, depress=highlight)
                prop.expand = False
                prop.name = item.name
                prop.index = index

            else:
                highlight = True if expand_history["target"] == item.name else False

                prop = row.operator("view3d.expand_sublevel", text="",
                                    icon='DISCLOSURE_TRI_RIGHT',
                                    emboss=highlight, depress=highlight)
                prop.expand = True
                prop.name = item.name
                prop.index = index

        else:
            row.label(icon='BLANK1')


        # collection icon
        c_icon = row.row()
        highlight = False
        if (context.view_layer.active_layer_collection == laycol["ptr"]):
                highlight = True

        prop = c_icon.operator("view3d.set_active_collection", text='', icon='GROUP',
                                              emboss=highlight, depress=highlight)

        prop.collection_index = laycol["row_index"]
        prop.collection_name = item.name

        if prefs.enable_qcd:
            QCD = row.row()
            QCD.scale_x = 0.4
            QCD.prop(item, "qcd_slot_idx", text="")

        c_name = row.row()

        #if rename[0] and index == cm.cm_list_index:
            #c_name.activate_init = True
            #rename[0] = False

        c_name.prop(item, "name", text="", expand=True)

        # used as a separator (actual separator not wide enough)
        row.label()

        row = s2 if cm.align_local_ops else s1

        # add set_collection op
        set_obj_col = row.row()
        set_obj_col.operator_context = 'INVOKE_DEFAULT'

        icon = 'MESH_CUBE'

        if selected_objects:
            if active_object and active_object.name in collection.objects:
                icon = 'SNAP_VOLUME'

            elif not set(selected_objects).isdisjoint(collection.objects):
                icon = 'STICKY_UVS_LOC'

        else:
            set_obj_col.enabled = False


        prop = set_obj_col.operator("view3d.set_collection", text="",
                                   icon=icon, emboss=False)
        prop.collection_index = laycol["id"]
        prop.collection_name = item.name


        if cm.show_exclude:
            exclude_history_base = rto_history["exclude"].get(view_layer.name, {})
            exclude_target = exclude_history_base.get("target", "")
            exclude_history = exclude_history_base.get("history", [])

            highlight = bool(exclude_history and exclude_target == item.name)
            icon = 'CHECKBOX_DEHLT' if laycol["ptr"].exclude else 'CHECKBOX_HLT'

            row.operator("view3d.exclude_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight).name = item.name

        if cm.show_selectable:
            select_history_base = rto_history["select"].get(view_layer.name, {})
            select_target = select_history_base.get("target", "")
            select_history = select_history_base.get("history", [])

            highlight = bool(select_history and select_target == item.name)
            icon = ('RESTRICT_SELECT_ON' if laycol["ptr"].collection.hide_select else
                    'RESTRICT_SELECT_OFF')

            row.operator("view3d.restrict_select_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight).name = item.name

        if cm.show_hide_viewport:
            hide_history_base = rto_history["hide"].get(view_layer.name, {})
            hide_target = hide_history_base.get("target", "")
            hide_history = hide_history_base.get("history", [])

            highlight = bool(hide_history and hide_target == item.name)
            icon = 'HIDE_ON' if laycol["ptr"].hide_viewport else 'HIDE_OFF'

            row.operator("view3d.hide_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight).name = item.name

        if cm.show_disable_viewport:
            disable_history_base = rto_history["disable"].get(view_layer.name, {})
            disable_target = disable_history_base.get("target", "")
            disable_history = disable_history_base.get("history", [])

            highlight = bool(disable_history and disable_target == item.name)
            icon = ('RESTRICT_VIEW_ON' if laycol["ptr"].collection.hide_viewport else
                    'RESTRICT_VIEW_OFF')

            row.operator("view3d.disable_viewport_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight).name = item.name

        if cm.show_render:
            render_history_base = rto_history["render"].get(view_layer.name, {})
            render_target = render_history_base.get("target", "")
            render_history = render_history_base.get("history", [])

            highlight = bool(render_history and render_target == item.name)
            icon = ('RESTRICT_RENDER_ON' if laycol["ptr"].collection.hide_render else
                    'RESTRICT_RENDER_OFF')

            row.operator("view3d.disable_render_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight).name = item.name



        row = s2

        row.separator()
        row.separator()

        rm_op = row.row()
        rm_op.operator("view3d.remove_collection", text="", icon='X',
                       emboss=False).collection_name = item.name


        if len(data.cm_list_collection) > index + 1:
            line_separator = column.row(align=True)
            line_separator.ui_units_y = 0.01
            line_separator.scale_y = 0.1
            line_separator.enabled = False

            line_separator.separator()
            line_separator.label(icon='BLANK1')

            for _ in range(laycol["lvl"] + 1):
                line_separator.label(icon='BLANK1')

            line_separator.prop(cm, "ui_separator")

        if cm.in_phantom_mode:
            c_icon.enabled = False
            c_name.enabled = False
            set_obj_col.enabled = False
            rm_op.enabled = False

            if prefs.enable_qcd:
                QCD.enabled = False


    def draw_filter(self, context, layout):
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")

        icon = 'ZOOM_OUT' if self.use_filter_invert else 'ZOOM_IN'
        subrow.prop(self, "use_filter_invert", text="", icon=icon)

        subrow = row.row(align=True)
        subrow.prop(self, "filter_by_selected", text="", icon='SNAP_VOLUME')

        if context.preferences.addons[__package__].preferences.enable_qcd:
            subrow.prop(self, "filter_by_qcd", text="", icon='EVENT_Q')

    def filter_items(self, context, data, propname):
        flt_flags = []
        flt_neworder = []

        list_items = getattr(data, propname)

        if self.filter_name:
            flt_flags = filter_items_by_name_insensitive(self.filter_name, self.bitflag_filter_item, list_items)

        elif self.filter_by_selected:
            flt_flags = [0] * len(list_items)

            for idx, item in enumerate(list_items):
                collection = layer_collections[item.name]["ptr"].collection

                # check if any of the selected objects are in the collection
                if not set(context.selected_objects).isdisjoint(collection.objects):
                    flt_flags[idx] |= self.bitflag_filter_item

        elif self.filter_by_qcd:
            flt_flags = [0] * len(list_items)

            for idx, item in enumerate(list_items):
                if item.qcd_slot_idx:
                    flt_flags[idx] |= self.bitflag_filter_item

        else: # display as treeview
            flt_flags = [self.bitflag_filter_item] * len(list_items)

            for idx, item in enumerate(list_items):
                if not layer_collections[item.name]["visible"]:
                    flt_flags[idx] = 0

        return flt_flags, flt_neworder



    def invoke(self, context, event):
        pass


class CMDisplayOptionsPanel(Panel):
    bl_label = "Display Options"
    bl_idname = "COLLECTIONMANAGER_PT_display_options"

    # set space type to VIEW_3D and region type to HEADER
    # because we only need it in a popover in the 3D View
    # and don't want it always present in the UI/N-Panel
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):
        cm = context.scene.collection_manager

        layout = self.layout

        panel_header = layout.row()
        panel_header.alignment = 'CENTER'
        panel_header.label(text="Display Options")

        layout.separator()

        section_header = layout.row()
        section_header.alignment = 'LEFT'
        section_header.label(text="Restriction Toggles")

        row = layout.row()
        row.prop(cm, "show_exclude", icon='CHECKBOX_HLT', icon_only=True)
        row.prop(cm, "show_selectable", icon='RESTRICT_SELECT_OFF', icon_only=True)
        row.prop(cm, "show_hide_viewport", icon='HIDE_OFF', icon_only=True)
        row.prop(cm, "show_disable_viewport", icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(cm, "show_render", icon='RESTRICT_RENDER_OFF', icon_only=True)

        layout.separator()

        section_header = layout.row()
        section_header.label(text="Layout")

        row = layout.row()
        row.prop(cm, "align_local_ops")


def view3d_header_qcd_slots(self, context):
    layout = self.layout

    idx = 1

    split = layout.split()
    col = split.column(align=True)
    row = col.row(align=True)
    row.scale_y = 0.5

    update_collection_tree(context)

    for x in range(20):
        qcd_slot_name = qcd_slots.get_name(str(x+1))

        if qcd_slot_name:
            qcd_laycol = layer_collections[qcd_slot_name]["ptr"]
            collection_objects = qcd_laycol.collection.objects
            selected_objects = get_move_selection()
            active_object = get_move_active()

            icon_value = 0

            # if the active object is in the current collection use a custom icon
            if (active_object and active_object in selected_objects and
                active_object.name in collection_objects):
                icon = 'LAYER_ACTIVE'


            # if there are selected objects use LAYER_ACTIVE
            elif not set(selected_objects).isdisjoint(collection_objects):
                icon = 'LAYER_USED'

            # If there are objects use LAYER_USED
            elif collection_objects:
                icon = 'NONE'
                active_icon = get_active_icon(context, qcd_laycol)
                icon_value = active_icon.icon_id

            else:
                icon = 'BLANK1'


            prop = row.operator("view3d.view_move_qcd_slot", text="", icon=icon,
                                icon_value=icon_value, depress=not qcd_laycol.exclude)
            prop.slot = str(x+1)

        else:
            row.label(text="", icon='X')


        if idx%5==0:
            row.separator()

        if idx == 10:
            row = col.row(align=True)
            row.scale_y = 0.5

        idx += 1


def view_layer_update(self, context):
    if context.view_layer.name != CollectionManager.last_view_layer:
        bpy.app.timers.register(update_qcd_header)
        CollectionManager.last_view_layer = context.view_layer.name


def get_active_icon(context, qcd_laycol):
    global last_icon_theme_text
    global last_icon_theme_text_sel

    tool_theme = context.preferences.themes[0].user_interface.wcol_tool
    pcoll = preview_collections["icons"]

    if qcd_laycol.exclude:
        theme_color = tool_theme.text
        last_theme_color = last_icon_theme_text
        icon = pcoll["active_icon_text"]

    else:
        theme_color = tool_theme.text_sel
        last_theme_color = last_icon_theme_text_sel
        icon = pcoll["active_icon_text_sel"]

    if last_theme_color == None or theme_color.hsv != last_theme_color:
        update_icon(pcoll["active_icon_base"], icon, theme_color)

        if qcd_laycol.exclude:
            last_icon_theme_text = theme_color.hsv

        else:
            last_icon_theme_text_sel = theme_color.hsv

    return icon


def update_icon(base, icon, theme_color):
    icon.icon_pixels = base.icon_pixels
    colored_icon = []

    for offset in range(len(icon.icon_pixels)):
        idx = offset * 4

        r = icon.icon_pixels_float[idx]
        g = icon.icon_pixels_float[idx+1]
        b = icon.icon_pixels_float[idx+2]
        a = icon.icon_pixels_float[idx+3]

        # add back some brightness and opacity blender takes away from the custom icon
        r = min(r+r*0.2,1)
        g = min(g+g*0.2,1)
        b = min(b+b*0.2,1)
        a = min(a+a*0.2,1)

        # make the icon follow the theme color (assuming the icon is white)
        r *= theme_color.r
        g *= theme_color.g
        b *= theme_color.b

        colored_icon.append(r)
        colored_icon.append(g)
        colored_icon.append(b)
        colored_icon.append(a)

    icon.icon_pixels_float = colored_icon


def filter_items_by_name_insensitive(pattern, bitflag, items, propname="name", flags=None, reverse=False):
        """
        Set FILTER_ITEM for items which name matches filter_name one (case-insensitive).
        pattern is the filtering pattern.
        propname is the name of the string property to use for filtering.
        flags must be a list of integers the same length as items, or None!
        return a list of flags (based on given flags if not None),
        or an empty list if no flags were given and no filtering has been done.
        """
        import fnmatch

        if not pattern or not items:  # Empty pattern or list = no filtering!
            return flags or []

        if flags is None:
            flags = [0] * len(items)

        # Make pattern case-insensitive
        pattern = pattern.lower()

        # Implicitly add heading/trailing wildcards.
        pattern = "*" + pattern + "*"

        for i, item in enumerate(items):
            name = getattr(item, propname, None)

            # Make name case-insensitive
            name = name.lower()

            # This is similar to a logical xor
            if bool(name and fnmatch.fnmatch(name, pattern)) is not bool(reverse):
                flags[i] |= bitflag

        return flags
