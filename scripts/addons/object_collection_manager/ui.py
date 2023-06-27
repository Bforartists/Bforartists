# SPDX-FileCopyrightText: 2011 Ryan Inch
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy

from bpy.types import (
    Menu,
    Operator,
    Panel,
    UIList,
)

from bpy.props import (
    BoolProperty,
    StringProperty,
)

# For VARS
from . import internals

# For FUNCTIONS
from .internals import (
    update_collection_tree,
    update_property_group,
    generate_state,
    check_state,
    get_move_selection,
    get_move_active,
    update_qcd_header,
    add_vertical_separator_line,
)

preview_collections = {}
last_icon_theme_text = None
last_icon_theme_text_sel = None


class CollectionManager(Operator):
    '''Manage and control collections, with advanced features, in a popup UI'''
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
        collection = context.view_layer.layer_collection.collection

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
        button_row_1 = layout.row()

        op_sec = button_row_1.row()
        op_sec.alignment = 'LEFT'

        collapse_sec = op_sec.row()
        collapse_sec.alignment = 'LEFT'
        collapse_sec.enabled = False

        if len(internals.expanded) > 0:
            text = "Collapse All Items"
        else:
            text = "Expand All Items"

        collapse_sec.operator("view3d.expand_all_items", text=text)

        for laycol in internals.collection_tree:
            if laycol["has_children"]:
                collapse_sec.enabled = True
                break

        if prefs.enable_qcd:
            renum_sec = op_sec.row()
            renum_sec.alignment = 'LEFT'
            renum_sec.operator("view3d.renumerate_qcd_slots")

        undo_sec = op_sec.row(align=True)
        undo_sec.alignment = 'LEFT'
        undo_sec.operator("view3d.undo_wrapper", text="", icon='LOOP_BACK')
        undo_sec.operator("view3d.redo_wrapper", text="", icon='LOOP_FORWARDS')

        # menu & filter
        right_sec = button_row_1.row()
        right_sec.alignment = 'RIGHT'

        specials_menu = right_sec.row()
        specials_menu.alignment = 'RIGHT'
        specials_menu.menu("VIEW3D_MT_CM_specials_menu")

        display_options = right_sec.row()
        display_options.alignment = 'RIGHT'
        display_options.popover(panel="COLLECTIONMANAGER_PT_display_options",
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
        prop.is_master_collection = True
        prop.collection_name = 'Scene Collection'

        master_collection_row.separator()

        # name
        name_row = master_collection_row.row(align=True)
        name_field = name_row.row(align=True)
        name_field.prop(self, "master_collection", text='')
        name_field.enabled = False

        # set selection
        setsel = name_row.row(align=True)
        icon = 'DOT'
        some_selected = False

        if not collection.objects:
            icon = 'BLANK1'
            setsel.active = False

        else:
            all_selected = None
            all_unreachable = None

            for obj in collection.objects:
                if not obj.visible_get() or obj.hide_select:
                    if all_unreachable != False:
                        all_unreachable = True

                else:
                    all_unreachable = False

                if obj.select_get() == False:
                    # some objects remain unselected
                    icon = 'KEYFRAME'
                    all_selected = False

                else:
                    some_selected = True

                    if all_selected == False:
                        break

                    all_selected = True


            if all_selected:
                # all objects are selected
                icon = 'KEYFRAME_HLT'

            if all_unreachable:
                if collection.objects:
                    icon = 'DOT'

                setsel.active = False

        prop = setsel.operator("view3d.select_collection_objects",
                                   text="",
                                   icon=icon,
                                   depress=some_selected,
                                   )
        prop.is_master_collection = True
        prop.collection_name = 'Scene Collection'


        # global rtos
        global_rto_row = master_collection_row.row()
        global_rto_row.alignment = 'RIGHT'

        # used as a separator (actual separator not wide enough)
        global_rto_row.label()


        # set collection
        row_setcol = global_rto_row.row()
        row_setcol.alignment = 'LEFT'
        row_setcol.operator_context = 'INVOKE_DEFAULT'

        selected_objects = get_move_selection()
        active_object = get_move_active()
        CM_UL_items.selected_objects = selected_objects
        CM_UL_items.active_object = active_object

        collection = context.view_layer.layer_collection.collection

        icon = 'IMPORT'

        if collection.objects:
            icon = 'MESH_CUBE'

        if selected_objects:
            if active_object and active_object.name in collection.objects:
                icon = 'SNAP_VOLUME'

            elif not selected_objects.isdisjoint(collection.objects):
                icon = 'STICKY_UVS_LOC'

        else:
            row_setcol.active = False


        # add vertical separator line
        separator = row_setcol.row()
        separator.scale_x = 0.2
        separator.enabled = False
        separator.operator("view3d.cm_ui_separator_button",
                            text="",
                                icon='BLANK1',
                                )

        # add operator
        prop = row_setcol.operator("view3d.send_objects_to_collection", text="",
                                   icon=icon, emboss=False)
        prop.is_master_collection = True
        prop.collection_name = 'Scene Collection'

        # add vertical separator line
        separator = row_setcol.row()
        separator.scale_x = 0.2
        separator.enabled = False
        separator.operator("view3d.cm_ui_separator_button",
                            text="",
                                icon='BLANK1',
                                )

        copy_icon = 'COPYDOWN'
        swap_icon = 'ARROW_LEFTRIGHT'
        copy_swap_icon = 'SELECT_INTERSECT'

        if cm.show_exclude:
            exclude_all_history = internals.rto_history["exclude_all"].get(view_layer.name, [])
            depress = True if len(exclude_all_history) else False
            icon = 'CHECKBOX_HLT'
            buffers = [False, False]

            if internals.copy_buffer["RTO"] == "exclude":
                icon = copy_icon
                buffers[0] = True

            if internals.swap_buffer["A"]["RTO"] == "exclude":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_exclude_all_collections", text="", icon=icon, depress=depress)

        if cm.show_selectable:
            select_all_history = internals.rto_history["select_all"].get(view_layer.name, [])
            depress = True if len(select_all_history) else False
            icon = 'RESTRICT_SELECT_OFF'
            buffers = [False, False]

            if internals.copy_buffer["RTO"] == "select":
                icon = copy_icon
                buffers[0] = True

            if internals.swap_buffer["A"]["RTO"] == "select":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_restrict_select_all_collections", text="", icon=icon, depress=depress)

        if cm.show_hide_viewport:
            hide_all_history = internals.rto_history["hide_all"].get(view_layer.name, [])
            depress = True if len(hide_all_history) else False
            icon = 'HIDE_OFF'
            buffers = [False, False]

            if internals.copy_buffer["RTO"] == "hide":
                icon = copy_icon
                buffers[0] = True

            if internals.swap_buffer["A"]["RTO"] == "hide":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_hide_all_collections", text="", icon=icon, depress=depress)

        if cm.show_disable_viewport:
            disable_all_history = internals.rto_history["disable_all"].get(view_layer.name, [])
            depress = True if len(disable_all_history) else False
            icon = 'RESTRICT_VIEW_OFF'
            buffers = [False, False]

            if internals.copy_buffer["RTO"] == "disable":
                icon = copy_icon
                buffers[0] = True

            if internals.swap_buffer["A"]["RTO"] == "disable":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_disable_viewport_all_collections", text="", icon=icon, depress=depress)

        if cm.show_render:
            render_all_history = internals.rto_history["render_all"].get(view_layer.name, [])
            depress = True if len(render_all_history) else False
            icon = 'RESTRICT_RENDER_OFF'
            buffers = [False, False]

            if internals.copy_buffer["RTO"] == "render":
                icon = copy_icon
                buffers[0] = True

            if internals.swap_buffer["A"]["RTO"] == "render":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_disable_render_all_collections", text="", icon=icon, depress=depress)

        if cm.show_holdout:
            holdout_all_history = internals.rto_history["holdout_all"].get(view_layer.name, [])
            depress = True if len(holdout_all_history) else False
            icon = 'HOLDOUT_ON'
            buffers = [False, False]

            if internals.copy_buffer["RTO"] == "holdout":
                icon = copy_icon
                buffers[0] = True

            if internals.swap_buffer["A"]["RTO"] == "holdout":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_holdout_all_collections", text="", icon=icon, depress=depress)

        if cm.show_indirect_only:
            indirect_all_history = internals.rto_history["indirect_all"].get(view_layer.name, [])
            depress = True if len(indirect_all_history) else False
            icon = 'INDIRECT_ONLY_ON'
            buffers = [False, False]

            if internals.copy_buffer["RTO"] == "indirect":
                icon = copy_icon
                buffers[0] = True

            if internals.swap_buffer["A"]["RTO"] == "indirect":
                icon = swap_icon
                buffers[1] = True

            if buffers[0] and buffers[1]:
                icon = copy_swap_icon

            global_rto_row.operator("view3d.un_indirect_only_all_collections", text="", icon=icon, depress=depress)

        # treeview
        layout.row().template_list("CM_UL_items", "",
                                   cm, "cm_list_collection",
                                   cm, "cm_list_index",
                                   rows=15,
                                   sort_lock=True)

        # add collections
        button_row_2 = layout.row()
        prop = button_row_2.operator("view3d.add_collection", text="Add Collection",
                               icon='COLLECTION_NEW')
        prop.child = False

        prop = button_row_2.operator("view3d.add_collection", text="Add SubCollection",
                               icon='COLLECTION_NEW')
        prop.child = True


        button_row_3 = layout.row()

        # phantom mode
        phantom_mode = button_row_3.row(align=True)
        toggle_text = "Disable " if cm.in_phantom_mode else "Enable "
        phantom_mode.operator("view3d.toggle_phantom_mode", text=toggle_text+"Phantom Mode")
        phantom_mode.operator("view3d.apply_phantom_mode", text="", icon='CHECKMARK')

        if cm.in_phantom_mode:
            view.enabled = False

            if prefs.enable_qcd:
                renum_sec.enabled = False

            undo_sec.enabled = False
            specials_menu.enabled = False

            c_icon.enabled = False
            row_setcol.enabled = False
            button_row_2.enabled = False


    def execute(self, context):
        wm = context.window_manager

        update_property_group(context)

        cm = context.scene.collection_manager
        view_layer = context.view_layer

        self.view_layer = view_layer.name

        # make sure list index is valid
        if cm.cm_list_index >= len(cm.cm_list_collection):
            cm.cm_list_index = -1

        # check if history/buffer/phantom state still correct
        check_state(context, cm_popup=True, phantom_mode=True)

        # handle window sizing
        max_width = 960
        min_width = 456
        row_indent_width = 15
        width_step = 21
        qcd_width = 30
        scrollbar_width = 21

        width = min_width + row_indent_width + (width_step * internals.max_lvl)

        if bpy.context.preferences.addons[__package__].preferences.enable_qcd:
            width += qcd_width

        if len(internals.layer_collections) > 14:
            width += scrollbar_width

        if width > max_width:
            width = max_width

        return wm.invoke_popup(self, width=width)

    def __del__(self):
        if not self.window_open:
            # prevent destructor execution when changing templates
            return

        internals.collection_state.clear()
        internals.collection_state.update(generate_state())


class CM_UL_items(UIList):
    filtering = False
    last_filter_value = ""

    selected_objects = set()
    active_object = None

    visible_items = []
    new_collections = []

    filter_name: StringProperty(
                        name="Filter By Name",
                        default="",
                        description="Filter collections by name",
                        update=lambda self, context:
                            CM_UL_items.new_collections.clear(),
                        )

    use_filter_invert: BoolProperty(
                        name="Invert",
                        default=False,
                        description="Invert filtering (show hidden items, and vice-versa)",
                        )

    filter_by_selected: BoolProperty(
                        name="Filter By Selected",
                        default=False,
                        description="Filter collections to only show the ones that contain the selected objects",
                        update=lambda self, context:
                            CM_UL_items.new_collections.clear(),
                        )
    filter_by_qcd: BoolProperty(
                        name="Filter By QCD",
                        default=False,
                        description="Filter collections to only show the ones that are QCD slots",
                        update=lambda self, context:
                            CM_UL_items.new_collections.clear(),
                        )

    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        self.use_filter_show = True

        cm = context.scene.collection_manager
        prefs = context.preferences.addons[__package__].preferences
        view_layer = context.view_layer
        laycol = internals.layer_collections[item.name]
        collection = laycol["ptr"].collection
        selected_objects = CM_UL_items.selected_objects
        active_object = CM_UL_items.active_object

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
                highlight = True if internals.expand_history["target"] == item.name else False

                prop = row.operator("view3d.expand_sublevel", text="",
                                    icon='DISCLOSURE_TRI_DOWN',
                                    emboss=highlight, depress=highlight)
                prop.expand = False
                prop.name = item.name
                prop.index = index

            else:
                highlight = True if internals.expand_history["target"] == item.name else False

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

        prop.is_master_collection = False
        prop.collection_name = item.name

        if prefs.enable_qcd:
            QCD = row.row()
            QCD.scale_x = 0.4
            QCD.prop(item, "qcd_slot_idx", text="")

        # collection name
        c_name = row.row(align=True)

        #if rename[0] and index == cm.cm_list_index:
            #c_name.activate_init = True
            #rename[0] = False

        c_name.prop(item, "name", text="", expand=True)

        # set selection
        setsel = c_name.row(align=True)
        icon = 'DOT'
        some_selected = False

        if not collection.objects:
            icon = 'BLANK1'
            setsel.active = False

        if any((laycol["ptr"].exclude,
               collection.hide_select,
               collection.hide_viewport,
               laycol["ptr"].hide_viewport,)):
            # objects cannot be selected
            setsel.active = False

        else:
            all_selected = None
            all_unreachable = None

            for obj in collection.objects:
                if not obj.visible_get() or obj.hide_select:
                    if all_unreachable != False:
                        all_unreachable = True

                else:
                    all_unreachable = False

                if obj.select_get() == False:
                    # some objects remain unselected
                    icon = 'KEYFRAME'
                    all_selected = False

                else:
                    some_selected = True

                    if all_selected == False:
                        break

                    all_selected = True


            if all_selected:
                # all objects are selected
                icon = 'KEYFRAME_HLT'

            if all_unreachable:
                if collection.objects:
                    icon = 'DOT'

                setsel.active = False


        prop = setsel.operator("view3d.select_collection_objects",
                                   text="",
                                   icon=icon,
                                   depress=some_selected
                                   )
        prop.is_master_collection = False
        prop.collection_name = item.name

        # used as a separator (actual separator not wide enough)
        row.label()

        row = s2 if cm.align_local_ops else s1


        add_vertical_separator_line(row)


        # add send_objects_to_collection op
        set_obj_col = row.row()
        set_obj_col.operator_context = 'INVOKE_DEFAULT'

        icon = 'IMPORT'

        if collection.objects:
            icon = 'MESH_CUBE'

        if selected_objects:
            if active_object and active_object.name in collection.objects:
                icon = 'SNAP_VOLUME'

            elif not selected_objects.isdisjoint(collection.objects):
                icon = 'STICKY_UVS_LOC'

        else:
            set_obj_col.enabled = False


        prop = set_obj_col.operator("view3d.send_objects_to_collection", text="",
                                   icon=icon, emboss=False)
        prop.is_master_collection = False
        prop.collection_name = item.name

        add_vertical_separator_line(row)


        if cm.show_exclude:
            exclude_history_base = internals.rto_history["exclude"].get(view_layer.name, {})
            exclude_target = exclude_history_base.get("target", "")
            exclude_history = exclude_history_base.get("history", [])

            highlight = bool(exclude_history and exclude_target == item.name)
            icon = 'CHECKBOX_DEHLT' if laycol["ptr"].exclude else 'CHECKBOX_HLT'

            prop = row.operator("view3d.exclude_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight)
            prop.name = item.name

        if cm.show_selectable:
            select_history_base = internals.rto_history["select"].get(view_layer.name, {})
            select_target = select_history_base.get("target", "")
            select_history = select_history_base.get("history", [])

            highlight = bool(select_history and select_target == item.name)
            icon = ('RESTRICT_SELECT_ON' if laycol["ptr"].collection.hide_select else
                    'RESTRICT_SELECT_OFF')

            prop = row.operator("view3d.restrict_select_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight)
            prop.name = item.name

        if cm.show_hide_viewport:
            hide_history_base = internals.rto_history["hide"].get(view_layer.name, {})
            hide_target = hide_history_base.get("target", "")
            hide_history = hide_history_base.get("history", [])

            highlight = bool(hide_history and hide_target == item.name)
            icon = 'HIDE_ON' if laycol["ptr"].hide_viewport else 'HIDE_OFF'

            prop = row.operator("view3d.hide_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight)
            prop.name = item.name

        if cm.show_disable_viewport:
            disable_history_base = internals.rto_history["disable"].get(view_layer.name, {})
            disable_target = disable_history_base.get("target", "")
            disable_history = disable_history_base.get("history", [])

            highlight = bool(disable_history and disable_target == item.name)
            icon = ('RESTRICT_VIEW_ON' if laycol["ptr"].collection.hide_viewport else
                    'RESTRICT_VIEW_OFF')

            prop = row.operator("view3d.disable_viewport_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight)
            prop.name = item.name

        if cm.show_render:
            render_history_base = internals.rto_history["render"].get(view_layer.name, {})
            render_target = render_history_base.get("target", "")
            render_history = render_history_base.get("history", [])

            highlight = bool(render_history and render_target == item.name)
            icon = ('RESTRICT_RENDER_ON' if laycol["ptr"].collection.hide_render else
                    'RESTRICT_RENDER_OFF')

            prop = row.operator("view3d.disable_render_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight)
            prop.name = item.name

        if cm.show_holdout:
            holdout_history_base = internals.rto_history["holdout"].get(view_layer.name, {})
            holdout_target = holdout_history_base.get("target", "")
            holdout_history = holdout_history_base.get("history", [])

            highlight = bool(holdout_history and holdout_target == item.name)
            icon = ('HOLDOUT_ON' if laycol["ptr"].holdout else
                    'HOLDOUT_OFF')

            prop = row.operator("view3d.holdout_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight)
            prop.name = item.name

        if cm.show_indirect_only:
            indirect_history_base = internals.rto_history["indirect"].get(view_layer.name, {})
            indirect_target = indirect_history_base.get("target", "")
            indirect_history = indirect_history_base.get("history", [])

            highlight = bool(indirect_history and indirect_target == item.name)
            icon = ('INDIRECT_ONLY_ON' if laycol["ptr"].indirect_only else
                    'INDIRECT_ONLY_OFF')

            prop = row.operator("view3d.indirect_only_collection", text="", icon=icon,
                         emboss=highlight, depress=highlight)
            prop.name = item.name



        row = s2

        row.separator()
        row.separator()

        rm_op = row.row()
        prop = rm_op.operator("view3d.remove_collection", text="", icon='X', emboss=False)
        prop.collection_name = item.name


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
        subrow.prop(self, "use_filter_invert", text="", icon='ARROW_LEFTRIGHT')

        subrow = row.row(align=True)
        subrow.prop(self, "filter_by_selected", text="", icon='STICKY_UVS_LOC')

        if context.preferences.addons[__package__].preferences.enable_qcd:
            subrow.prop(self, "filter_by_qcd", text="", icon='EVENT_Q')

    def filter_items(self, context, data, propname):
        CM_UL_items.filtering = False

        flt_flags = []
        flt_neworder = []
        list_items = getattr(data, propname)


        if self.filter_name:
            CM_UL_items.filtering = True

            new_flt_flags = filter_items_by_name_custom(self.filter_name, self.bitflag_filter_item, list_items)

            flt_flags = merge_flt_flags(flt_flags, new_flt_flags)


        if self.filter_by_selected:
            CM_UL_items.filtering = True
            new_flt_flags = [0] * len(list_items)

            for idx, item in enumerate(list_items):
                collection = internals.layer_collections[item.name]["ptr"].collection

                # check if any of the selected objects are in the collection
                if not set(context.selected_objects).isdisjoint(collection.objects):
                    new_flt_flags[idx] = self.bitflag_filter_item

                # add in any recently created collections
                if item.name in CM_UL_items.new_collections:
                    new_flt_flags[idx] = self.bitflag_filter_item

            flt_flags = merge_flt_flags(flt_flags, new_flt_flags)


        if self.filter_by_qcd:
            CM_UL_items.filtering = True
            new_flt_flags = [0] * len(list_items)

            for idx, item in enumerate(list_items):
                if item.qcd_slot_idx:
                    new_flt_flags[idx] = self.bitflag_filter_item

                # add in any recently created collections
                if item.name in CM_UL_items.new_collections:
                    new_flt_flags[idx] = self.bitflag_filter_item

            flt_flags = merge_flt_flags(flt_flags, new_flt_flags)


        if not CM_UL_items.filtering: # display as treeview
            CM_UL_items.new_collections.clear()
            flt_flags = [0] * len(list_items)

            for idx, item in enumerate(list_items):
                if internals.layer_collections[item.name]["visible"]:
                    flt_flags[idx] = self.bitflag_filter_item


        if self.use_filter_invert:
            CM_UL_items.filtering = True # invert can act as pseudo filtering
            for idx, flag in enumerate(flt_flags):
                flt_flags[idx] = 0 if flag else self.bitflag_filter_item


        # update visible items list
        CM_UL_items.visible_items.clear()
        CM_UL_items.visible_items.extend(flt_flags)

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
        row.prop(cm, "show_holdout", icon='HOLDOUT_ON', icon_only=True)
        row.prop(cm, "show_indirect_only", icon='INDIRECT_ONLY_ON', icon_only=True)

        layout.separator()

        section_header = layout.row()
        section_header.label(text="Layout")

        row = layout.row()
        row.prop(cm, "align_local_ops")


class SpecialsMenu(Menu):
    bl_label = "Specials"
    bl_idname = "VIEW3D_MT_CM_specials_menu"

    def draw(self, context):
        layout = self.layout

        prop = layout.operator("view3d.remove_empty_collections")
        prop.without_objects = False

        prop = layout.operator("view3d.remove_empty_collections",
                               text="Purge All Collections Without Objects")
        prop.without_objects = True

        layout.separator()

        layout.operator("view3d.select_all_cumulative_objects")


class EnableAllQCDSlotsMenu(Menu):
    bl_label = "Global QCD Slot Actions"
    bl_idname = "VIEW3D_MT_CM_qcd_enable_all_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator("view3d.create_all_qcd_slots")

        layout.separator()

        layout.operator("view3d.enable_all_qcd_slots")
        layout.operator("view3d.enable_all_qcd_slots_isolated")

        layout.separator()

        layout.operator("view3d.isolate_selected_objects_collections")
        if context.mode == 'OBJECT':
            layout.operator("view3d.disable_selected_objects_collections")

        layout.separator()

        layout.operator("view3d.disable_all_non_qcd_slots")
        layout.operator("view3d.disable_all_collections")

        if context.mode == 'OBJECT':
            layout.separator()
            layout.operator("view3d.select_all_qcd_objects")

        layout.separator()

        layout.operator("view3d.discard_qcd_history")


def view3d_header_qcd_slots(self, context):
    update_collection_tree(context)

    view_layer = context.view_layer
    layout = self.layout
    idx = 1

    check_state(context, qcd=True)


    main_row = layout.row(align=True)
    current_qcd_history = internals.qcd_history.get(context.view_layer.name, [])

    main_row.operator_menu_hold("view3d.enable_all_qcd_slots_meta",
                                text="",
                                icon='HIDE_OFF',
                                depress=bool(current_qcd_history),
                                menu="VIEW3D_MT_CM_qcd_enable_all_menu")


    split = main_row.split()
    col = split.column(align=True)
    row = col.row(align=True)
    row.scale_y = 0.5

    selected_objects = get_move_selection()
    active_object = get_move_active()

    for x in range(20):
        qcd_slot_name = internals.qcd_slots.get_name(str(x+1))

        if qcd_slot_name:
            qcd_laycol = internals.layer_collections[qcd_slot_name]["ptr"]
            collection_objects = qcd_laycol.collection.objects

            icon_value = 0

            # if the active object is in the current collection use a custom icon
            if (active_object and active_object in selected_objects and
                active_object.name in collection_objects):
                icon = 'LAYER_ACTIVE'

            # if there are selected objects use LAYER_ACTIVE
            elif not selected_objects.isdisjoint(collection_objects):
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
            prop = row.operator("view3d.unassigned_qcd_slot", text="", icon='X', emboss=False)
            prop.slot = str(x+1)


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


def filter_items_by_name_custom(pattern, bitflag, items, propname="name", flags=None, reverse=False):
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

            # add in any recently created collections
            if item.name in CM_UL_items.new_collections:
                flags[i] |= bitflag

        return flags

def merge_flt_flags(l1, l2):
    for idx, _ in enumerate(l1):
        l1[idx] &= l2.pop(0)

    return l1 + l2
