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

from bpy.types import (
    Operator,
    Panel,
    UIList,
)

from bpy.props import BoolProperty

from .internals import (
    collection_tree,
    expanded,
    get_max_lvl,
    layer_collections,
    update_collection_tree,
    update_property_group,
)

from .operators import (
    rto_history,
    phantom_history,
    )


class CollectionManager(Operator):
    bl_label = "Collection Manager"
    bl_idname = "view3d.collection_manager"

    last_view_layer = ""

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        view_layer = context.view_layer.name

        if view_layer != self.last_view_layer:
            update_collection_tree(context)
            self.last_view_layer = view_layer

        title_row = layout.split(factor=0.5)
        main = title_row.row()
        view = title_row.row(align=True)
        view.alignment = 'RIGHT'

        main.label(text="Collection Manager")

        view.prop(context.view_layer, "use", text="")
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

        filter_row = layout.row()
        filter_row.alignment = 'RIGHT'

        filter_row.popover(panel="COLLECTIONMANAGER_PT_restriction_toggles", text="", icon='FILTER')

        toggle_row = layout.split(factor=0.3)
        toggle_row.alignment = 'LEFT'

        sec1 = toggle_row.row()
        sec1.alignment = 'LEFT'
        sec1.enabled = False

        if len(expanded) > 0:
            text = "Collapse All Items"
        else:
            text = "Expand All Items"

        sec1.operator("view3d.expand_all_items", text=text)

        for laycol in collection_tree:
            if laycol["has_children"]:
                sec1.enabled = True
                break

        sec2 = toggle_row.row()
        sec2.alignment = 'RIGHT'

        if scn.show_exclude:
            exclude_all_history = rto_history["exclude_all"].get(view_layer, [])
            depress = True if len(exclude_all_history) else False

            sec2.operator("view3d.un_exclude_all_collections", text="", icon='CHECKBOX_HLT', depress=depress)

        if scn.show_selectable:
            select_all_history = rto_history["select_all"].get(view_layer, [])
            depress = True if len(select_all_history) else False

            sec2.operator("view3d.un_restrict_select_all_collections", text="", icon='RESTRICT_SELECT_OFF', depress=depress)

        if scn.show_hideviewport:
            hide_all_history = rto_history["hide_all"].get(view_layer, [])
            depress = True if len(hide_all_history) else False

            sec2.operator("view3d.un_hide_all_collections", text="", icon='HIDE_OFF', depress=depress)

        if scn.show_disableviewport:
            disable_all_history = rto_history["disable_all"].get(view_layer, [])
            depress = True if len(disable_all_history) else False

            sec2.operator("view3d.un_disable_viewport_all_collections", text="", icon='RESTRICT_VIEW_OFF', depress=depress)

        if scn.show_render:
            render_all_history = rto_history["render_all"].get(view_layer, [])
            depress = True if len(render_all_history) else False

            sec2.operator("view3d.un_disable_render_all_collections", text="", icon='RESTRICT_RENDER_OFF', depress=depress)

        layout.row().template_list("CM_UL_items", "", context.scene, "CMListCollection", context.scene, "CMListIndex", rows=15, sort_lock=True)

        addcollec_row = layout.row()
        addcollec_row.operator("view3d.add_collection", text="Add Collection", icon='COLLECTION_NEW').child = False

        addcollec_row.operator("view3d.add_collection", text="Add SubCollection", icon='COLLECTION_NEW').child = True

        phantom_row = layout.row()
        toggle_text = "Disable " if scn.CM_Phantom_Mode else "Enable "
        phantom_row.operator("view3d.toggle_phantom_mode", text=toggle_text+"Phantom Mode")

        if scn.CM_Phantom_Mode:
            view.enabled = False
            addcollec_row.enabled = False


    def execute(self, context):
        wm = context.window_manager

        update_property_group(context)
        self.view_layer = context.view_layer.name

        # sync selection in ui list with active layer collection
        try:
            active_laycol_name = context.view_layer.active_layer_collection.name
            active_laycol_row_index = layer_collections[active_laycol_name]["row_index"]
            context.scene.CMListIndex = active_laycol_row_index
        except:
            context.scene.CMListIndex = -1

        # check if in phantom mode and if it's still viable
        if context.scene.CM_Phantom_Mode:
            if set(layer_collections.keys()) != set(phantom_history["initial_state"].keys()):
                context.scene.CM_Phantom_Mode = False

            if context.view_layer.name != phantom_history["view_layer"]:
                context.scene.CM_Phantom_Mode = False

        # handle window sizing
        max_width = 960
        min_width = 456
        width_step = 21
        scrollbar_width = 21
        lvl = get_max_lvl()

        width = min_width + (width_step * lvl)

        if len(layer_collections) > 14:
            width += scrollbar_width

        if width > max_width:
            width = max_width

        return wm.invoke_popup(self, width=width)


def update_selection(self, context):
    scn = context.scene

    if scn.CMListIndex == -1:
        return

    selected_item = scn.CMListCollection[scn.CMListIndex]
    layer_collection = layer_collections[selected_item.name]["ptr"]

    context.view_layer.active_layer_collection = layer_collection


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


class CM_UL_items(UIList):
    last_filter_value = ""

    filter_by_selected: BoolProperty(
                        name="Filter By Selected",
                        default=False,
                        description="Filter collections by selected items"
                        )

    def draw_item(self, context, layout, data, item, icon, active_data,active_propname, index):
        self.use_filter_show = True

        scn = context.scene
        view_layer = context.view_layer.name
        laycol = layer_collections[item.name]
        collection = laycol["ptr"].collection

        split = layout.split(factor=0.96)
        row = split.row(align=True)
        row.alignment = 'LEFT'

        # indent child items
        if laycol["lvl"] > 0:
            for _ in range(laycol["lvl"]):
                row.label(icon='BLANK1')

        # add expander if collection has children to make UIList act like tree view
        if laycol["has_children"]:
            if laycol["expanded"]:
                prop = row.operator("view3d.expand_sublevel", text="", icon='DISCLOSURE_TRI_DOWN', emboss=False)
                prop.expand = False
                prop.name = item.name
                prop.index = index

            else:
                prop = row.operator("view3d.expand_sublevel", text="", icon='DISCLOSURE_TRI_RIGHT', emboss=False)
                prop.expand = True
                prop.name = item.name
                prop.index = index

        else:
            row.label(icon='BLANK1')


        row.label(icon='GROUP')

        name_row = row.row()

        #if rename[0] and index == scn.CMListIndex:
            #name_row.activate_init = True
            #rename[0] = False

        name_row.prop(item, "name", text="", expand=True)

        # used as a separator (actual separator not wide enough)
        row.label()

        # add set_collection op
        row_setcol = row.row()
        row_setcol.operator_context = 'INVOKE_DEFAULT'

        icon = 'MESH_CUBE'

        if len(context.selected_objects) > 0 and context.active_object:
            if context.active_object.name in collection.objects:
                icon = 'SNAP_VOLUME'
        else:
            row_setcol.enabled = False


        prop = row_setcol.operator("view3d.set_collection", text="", icon=icon, emboss=False)
        prop.collection_index = laycol["id"]
        prop.collection_name = item.name


        if scn.show_exclude:
            exclude_history_base = rto_history["exclude"].get(view_layer, {})
            exclude_target = exclude_history_base.get("target", "")
            exclude_history = exclude_history_base.get("history", [])

            depress = True if len(exclude_history) and exclude_target == item.name else False
            emboss = True if len(exclude_history) and exclude_target == item.name else False
            icon = 'CHECKBOX_DEHLT' if laycol["ptr"].exclude else 'CHECKBOX_HLT'

            row.operator("view3d.exclude_collection", text="", icon=icon, emboss=emboss, depress=depress).name = item.name

        if scn.show_selectable:
            select_history_base = rto_history["select"].get(view_layer, {})
            select_target = select_history_base.get("target", "")
            select_history = select_history_base.get("history", [])

            depress = True if len(select_history) and select_target == item.name else False
            emboss = True if len(select_history) and select_target == item.name else False
            icon = 'RESTRICT_SELECT_ON' if laycol["ptr"].collection.hide_select else 'RESTRICT_SELECT_OFF'

            row.operator("view3d.restrict_select_collection", text="", icon=icon, emboss=emboss, depress=depress).name = item.name

        if scn.show_hideviewport:
            hide_history_base = rto_history["hide"].get(view_layer, {})
            hide_target = hide_history_base.get("target", "")
            hide_history = hide_history_base.get("history", [])

            depress = True if len(hide_history) and hide_target == item.name else False
            emboss = True if len(hide_history) and hide_target == item.name else False
            icon = 'HIDE_ON' if laycol["ptr"].hide_viewport else 'HIDE_OFF'

            row.operator("view3d.hide_collection", text="", icon=icon, emboss=emboss, depress=depress).name = item.name

        if scn.show_disableviewport:
            disable_history_base = rto_history["disable"].get(view_layer, {})
            disable_target = disable_history_base.get("target", "")
            disable_history = disable_history_base.get("history", [])

            depress = True if len(disable_history) and disable_target == item.name else False
            emboss = True if len(disable_history) and disable_target == item.name else False
            icon = 'RESTRICT_VIEW_ON' if laycol["ptr"].collection.hide_viewport else 'RESTRICT_VIEW_OFF'

            row.operator("view3d.disable_viewport_collection", text="", icon=icon, emboss=emboss, depress=depress).name = item.name

        if scn.show_render:
            render_history_base = rto_history["render"].get(view_layer, {})
            render_target = render_history_base.get("target", "")
            render_history = render_history_base.get("history", [])

            depress = True if len(render_history) and render_target == item.name else False
            emboss = True if len(render_history) and render_target == item.name else False
            icon = 'RESTRICT_RENDER_ON' if laycol["ptr"].collection.hide_render else 'RESTRICT_RENDER_OFF'

            row.operator("view3d.disable_render_collection", text="", icon=icon, emboss=emboss, depress=depress).name = item.name


        rm_op = split.row()
        rm_op.alignment = 'RIGHT'
        rm_op.operator("view3d.remove_collection", text="", icon='X', emboss=False).collection_name = item.name

        if scn.CM_Phantom_Mode:
            name_row.enabled = False
            row_setcol.enabled = False
            rm_op.enabled = False


    def draw_filter(self, context, layout):
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")

        icon = 'ZOOM_OUT' if self.use_filter_invert else 'ZOOM_IN'
        subrow.prop(self, "use_filter_invert", text="", icon=icon)

        subrow = row.row(align=True)
        subrow.prop(self, "filter_by_selected", text="", icon='SNAP_VOLUME')

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

        else: # display as treeview
            flt_flags = [self.bitflag_filter_item] * len(list_items)

            for idx, item in enumerate(list_items):
                if not layer_collections[item.name]["visible"]:
                    flt_flags[idx] = 0

        return flt_flags, flt_neworder



    def invoke(self, context, event):
        pass


class CMRestrictionTogglesPanel(Panel):
    bl_label = "Restriction Toggles"
    bl_idname = "COLLECTIONMANAGER_PT_restriction_toggles"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'

    def draw(self, context):

        layout = self.layout

        row = layout.row()

        row.prop(context.scene, "show_exclude", icon='CHECKBOX_HLT', icon_only=True)
        row.prop(context.scene, "show_selectable", icon='RESTRICT_SELECT_OFF', icon_only=True)
        row.prop(context.scene, "show_hideviewport", icon='HIDE_OFF', icon_only=True)
        row.prop(context.scene, "show_disableviewport", icon='RESTRICT_VIEW_OFF', icon_only=True)
        row.prop(context.scene, "show_render", icon='RESTRICT_RENDER_OFF', icon_only=True)
