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

# <pep8 compliant>
import bpy
from bpy.types import (
    Menu,
)

__all__ = (
    "ToolDef",
    "ToolSelectPanelHelper",
    "activate_by_name",
    "activate_by_name_or_cycle",
    "description_from_name",
    "keymap_from_name",
    "keymap_from_context",
)

# Support reloading icons.
if "_icon_cache" in locals():
    release = bpy.app.icons.release
    for icon_value in _icon_cache.values():
        if icon_value != 0:
            release(icon_value)
    del release


# (filename -> icon_value) map
_icon_cache = {}


def _keymap_fn_from_seq(keymap_data):

    # standalone
    def _props_assign_recursive(rna_props, py_props):
        for prop_id, value in py_props.items():
            if isinstance(value, dict):
                _props_assign_recursive(getattr(rna_props, prop_id), value)
            else:
                setattr(rna_props, prop_id, value)

    def keymap_fn(km):
        for op_idname, op_props_dict, kmi_kwargs in keymap_fn.keymap_data:
            kmi = km.keymap_items.new(op_idname, **kmi_kwargs)
            kmi_props = kmi.properties
            if op_props_dict:
                _props_assign_recursive(kmi_props, op_props_dict)
    keymap_fn.keymap_data = keymap_data
    return keymap_fn


def _item_is_fn(item):
    return (not (type(item) is ToolDef) and callable(item))


from collections import namedtuple
ToolDef = namedtuple(
    "ToolDef",
    (
        # The name to display in the interface.
        "text",
        # Description (for tooltip), when not set, use the description of 'operator'.
        "description",
        # The name of the icon to use (found in ``release/datafiles/icons``) or None for no icon.
        "icon",
        # An optional cursor to use when this tool is active.
        "cursor",
        # An optional gizmo group to activate when the tool is set or None for no gizmo.
        "widget",
        # Optional keymap for tool, either:
        # - A function that populates a keymaps passed in as an argument.
        # - A tuple filled with triple's of:
        #   ``(operator_id, operator_properties, keymap_item_args)``.
        #
        # Warning: currently 'from_dict' this is a list of one item,
        # so internally we can swap the keymap function for the keymap it's self.
        # This isn't very nice and may change, tool definitions shouldn't care about this.
        "keymap",
        # Optional data-block assosiated with this tool.
        # (Typically brush name, usage depends on mode, we could use for non-brush ID's in other modes).
        "data_block",
        # Optional primary operator (for introspection only).
        "operator",
        # Optional draw settings (operator options, toolsettings).
        "draw_settings",
    )
)
del namedtuple


def from_dict(kw_args):
    """
    Use so each tool can avoid defining all members of the named tuple.
    Also convert the keymap from a tuple into a function
    (since keymap is a callback).
    """
    kw = {
        "description": None,
        "icon": None,
        "cursor": None,
        "widget": None,
        "keymap": None,
        "data_block": None,
        "operator": None,
        "draw_settings": None,
    }
    kw.update(kw_args)

    keymap = kw["keymap"]
    if kw["keymap"] is None:
        pass
    elif type(keymap) is tuple:
        keymap = [_keymap_fn_from_seq(keymap)]
    else:
        keymap = [keymap]
    kw["keymap"] = keymap
    return ToolDef(**kw)


def from_fn(fn):
    """
    Use as decorator so we can define functions.
    """
    return ToolDef.from_dict(fn())


ToolDef.from_dict = from_dict
ToolDef.from_fn = from_fn
del from_dict
del from_fn


class ToolSelectPanelHelper:
    """
    Generic Class, can be used for any toolbar.

    - keymap_prefix:
      The text prefix for each key-map for this spaces tools.
    - tools_all():
      Returns (context_mode, tools) tuple pair for all tools defined.
    - tools_from_context(context, mode=None):
      Returns tools available in this context.

    Each tool is a 'ToolDef' or None for a separator in the toolbar, use ``None``.
    """

    @staticmethod
    def _tool_class_from_space_type(space_type):
        return next(
            (cls for cls in ToolSelectPanelHelper.__subclasses__()
             if cls.bl_space_type == space_type),
            None
        )

    @staticmethod
    def _icon_value_from_icon_handle(icon_name):
        import os
        if icon_name is not None:
            assert(type(icon_name) is str)
            icon_value = _icon_cache.get(icon_name)
            if icon_value is None:
                dirname = bpy.utils.resource_path('LOCAL')
                if not os.path.exists(dirname):
                    # TODO(campbell): use a better way of finding datafiles.
                    dirname = bpy.utils.resource_path('SYSTEM')
                filename = os.path.join(dirname, "datafiles", "icons", icon_name + ".dat")
                try:
                    icon_value = bpy.app.icons.new_triangles_from_file(filename)
                except Exception as ex:
                    if not os.path.exists(filename):
                        print("Missing icons:", filename, ex)
                    else:
                        print("Corrupt icon:", filename, ex)
                    # Use none as a fallback (avoids layout issues).
                    if icon_name != "none":
                        icon_value = ToolSelectPanelHelper._icon_value_from_icon_handle("none")
                    else:
                        icon_value = 0
                _icon_cache[icon_name] = icon_value
            return icon_value
        else:
            return 0

    @staticmethod
    def _tools_flatten(tools):
        """
        Flattens, skips None and calls generators.
        """
        for item in tools:
            if item is None:
                yield None
            elif type(item) is tuple:
                for sub_item in item:
                    if sub_item is None:
                        yield None
                    elif _item_is_fn(sub_item):
                        yield from sub_item(context)
                    else:
                        yield sub_item
            else:
                if _item_is_fn(item):
                    yield from item(context)
                else:
                    yield item

    @staticmethod
    def _tools_flatten_with_tool_index(tools):
        for item in tools:
            if item is None:
                yield None, -1
            elif type(item) is tuple:
                i = 0
                for sub_item in item:
                    if sub_item is None:
                        yield None
                    elif _item_is_fn(sub_item):
                        for item_dyn in sub_item(context):
                            yield item_dyn, i
                            i += 1
                    else:
                        yield sub_item, i
                        i += 1
            else:
                if _item_is_fn(item):
                    for item_dyn in item(context):
                        yield item_dyn, -1
                else:
                    yield item, -1

    @staticmethod
    def _tool_get_active(context, space_type, mode, with_icon=False):
        """
        Return the active Python tool definition and icon name.
        """
        cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)
        if cls is not None:
            tool_active = ToolSelectPanelHelper._tool_active_from_context(context, space_type, mode)
            tool_active_text = getattr(tool_active, "name", None)
            for item in ToolSelectPanelHelper._tools_flatten(cls.tools_from_context(context, mode)):
                if item is not None:
                    if item.text == tool_active_text:
                        if with_icon:
                            icon_value = ToolSelectPanelHelper._icon_value_from_icon_handle(item.icon)
                        else:
                            icon_value = 0
                        return (item, tool_active, icon_value)
        return None, None, 0

    @staticmethod
    def _tool_get_by_name(context, space_type, text):
        """
        Return the active Python tool definition and index (if in sub-group, else -1).
        """
        cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)
        if cls is not None:
            for item, index in ToolSelectPanelHelper._tools_flatten_with_tool_index(cls.tools_from_context(context)):
                if item is not None:
                    if item.text == text:
                        return (cls, item, index)
        return None, None, -1

    @staticmethod
    def _tool_active_from_context(context, space_type, mode=None, create=False):
        if space_type == 'VIEW_3D':
            if mode is None:
                mode = context.mode
            tool = context.workspace.tools.from_space_view3d_mode(mode, create=create)
            if tool is not None:
                tool.refresh_from_context()
                return tool
        elif space_type == 'IMAGE_EDITOR':
            space_data = context.space_data
            if mode is None:
                if space_data is None:
                    mode = 'VIEW'
                else:
                    mode = space_data.mode
            tool = context.workspace.tools.from_space_image_mode(mode, create=create)
            if tool is not None:
                tool.refresh_from_context()
                return tool
        return None

    @staticmethod
    def _tool_text_from_button(context):
        return context.button_operator.name

    @classmethod
    def _km_action_simple(cls, kc, context_descr, text, keymap_fn):
        km_idname = f"{cls.keymap_prefix:s} {context_descr:s}, {text:s}"
        km = kc.keymaps.get(km_idname)
        if km is None:
            km = kc.keymaps.new(km_idname, space_type=cls.bl_space_type, region_type='WINDOW')
            keymap_fn[0](km)
        keymap_fn[0] = km

    # Special internal function, gives use items that contain keymaps.
    @staticmethod
    def _tools_flatten_with_keymap(tools):
        for item_parent in tools:
            if item_parent is None:
                continue
            for item in item_parent if (type(item_parent) is tuple) else (item_parent,):
                # skip None or generator function
                if item is None or _item_is_fn(item):
                    continue
                if item.keymap is not None:
                    yield item

    @classmethod
    def register(cls):
        wm = bpy.context.window_manager
        # Write into defaults, users may modify in preferences.
        kc = wm.keyconfigs.default

        # Track which tool-group was last used for non-active groups.
        # Blender stores the active tool-group index.
        #
        # {tool_name_first: index_in_group, ...}
        cls._tool_group_active = {}

        # ignore in background mode
        if kc is None:
            return

        for context_mode, tools in cls.tools_all():
            if context_mode is None:
                context_descr = "All"
            else:
                context_descr = context_mode.replace("_", " ").title()

            for item in cls._tools_flatten_with_keymap(tools):
                keymap_data = item.keymap
                if callable(keymap_data[0]):
                    cls._km_action_simple(kc, context_descr, item.text, keymap_data)

    @classmethod
    def keymap_ui_hierarchy(cls, context_mode):
        # See: bpy_extras.keyconfig_utils
        for context_mode_test, tools in cls.tools_all():
            if context_mode_test == context_mode:
                for item in cls._tools_flatten_with_keymap(tools):
                    km = item.keymap[0]
                    # print((km.name, cls.bl_space_type, 'WINDOW', []))
                    yield (km.name, cls.bl_space_type, 'WINDOW', [])

    # -------------------------------------------------------------------------
    # Layout Generators
    #
    # Meaning of recieved values:
    # - Bool: True for a separator, otherwise False for regular tools.
    # - None: Signal to finish (complete any final operations, e.g. add padding).

    @staticmethod
    def _layout_generator_single_column(layout, scale_y):
        col = layout.column(align=True)
        col.scale_y = scale_y
        is_sep = False
        while True:
            if is_sep is True:
                col = layout.column(align=True)
                col.scale_y = scale_y
            elif is_sep is None:
                yield None
                return
            is_sep = yield col

    @staticmethod
    def _layout_generator_multi_columns(layout, column_count, scale_y):
        scale_x = scale_y * 1.1
        column_last = column_count - 1

        col = layout.column(align=True)

        row = col.row(align=True)

        row.scale_x = scale_x
        row.scale_y = scale_y

        is_sep = False
        column_index = 0
        while True:
            if is_sep is True:
                if column_index != column_last:
                    row.label(text="")
                col = layout.column(align=True)
                row = col.row(align=True)
                row.scale_x = scale_x
                row.scale_y = scale_y
                column_index = 0

            is_sep = yield row
            if is_sep is None:
                if column_index == column_last:
                    row.label(text="")
                    yield None
                    return

            if column_index == column_count:
                column_index = 0
                row = col.row(align=True)
                row.scale_x = scale_x
                row.scale_y = scale_y
            column_index += 1

    @staticmethod
    def _layout_generator_detect_from_region(layout, region, scale_y):
        """
        Choose an appropriate layout for the toolbar.
        """
        # Currently this just checks the width,
        # we could have different layouts as preferences too.
        system = bpy.context.user_preferences.system
        view2d = region.view2d
        view2d_scale = (
            view2d.region_to_view(1.0, 0.0)[0] -
            view2d.region_to_view(0.0, 0.0)[0]
        )
        width_scale = region.width * view2d_scale / system.ui_scale

        if width_scale > 120.0:
            show_text = True
            column_count = 1
        else:
            show_text = False
            # 2 column layout, disabled
            if width_scale > 80.0:
                column_count = 2
            else:
                column_count = 1

        if column_count == 1:
            ui_gen = ToolSelectPanelHelper._layout_generator_single_column(layout, scale_y=scale_y)
        else:
            ui_gen = ToolSelectPanelHelper._layout_generator_multi_columns(layout, column_count=column_count, scale_y=scale_y)

        return ui_gen, show_text

    @classmethod
    def draw_cls(cls, layout, context, detect_layout=True, scale_y=1.75):
        # Use a classmethod so it can be called outside of a panel context.

        # XXX, this UI isn't very nice.
        # We might need to create new button types for this.
        # Since we probably want:
        # - tool-tips that include multiple key shortcuts.
        # - ability to click and hold to expose sub-tools.

        space_type = context.space_data.type
        tool_active_text = getattr(
            ToolSelectPanelHelper._tool_active_from_context(context, space_type),
            "name", None,
        )

        if detect_layout:
            ui_gen, show_text = cls._layout_generator_detect_from_region(layout, context.region, scale_y)
        else:
            ui_gen = ToolSelectPanelHelper._layout_generator_single_column(layout, scale_y)
            show_text = True

        # Start iteration
        ui_gen.send(None)

        for item in cls.tools_from_context(context):
            if item is None:
                ui_gen.send(True)
                continue

            if type(item) is tuple:
                is_active = False
                i = 0
                for i, sub_item in enumerate(item):
                    if sub_item is None:
                        continue
                    is_active = (sub_item.text == tool_active_text)
                    if is_active:
                        index = i
                        break
                del i, sub_item

                if is_active:
                    # not ideal, write this every time :S
                    cls._tool_group_active[item[0].text] = index
                else:
                    index = cls._tool_group_active.get(item[0].text, 0)

                item = item[index]
                use_menu = True
            else:
                index = -1
                use_menu = False

            is_active = (item.text == tool_active_text)
            icon_value = ToolSelectPanelHelper._icon_value_from_icon_handle(item.icon)

            sub = ui_gen.send(False)

            if use_menu:
                sub.operator_menu_hold(
                    "wm.tool_set_by_name",
                    text=item.text if show_text else "",
                    depress=is_active,
                    menu="WM_MT_toolsystem_submenu",
                    icon_value=icon_value,
                ).name = item.text
            else:
                sub.operator(
                    "wm.tool_set_by_name",
                    text=item.text if show_text else "",
                    depress=is_active,
                    icon_value=icon_value,
                ).name = item.text
        # Signal to finish any remaining layout edits.
        ui_gen.send(None)

    def draw(self, context):
        self.draw_cls(self.layout, context)

    @staticmethod
    def tool_active_from_context(context):
        # BAD DESIGN WARNING: last used tool
        workspace = context.workspace
        space_type = workspace.tools_space_type
        mode = workspace.tools_mode
        return ToolSelectPanelHelper._tool_active_from_context(context, space_type, mode)

    @staticmethod
    def draw_active_tool_header(
            context, layout,
            *,
            show_tool_name=False,
    ):
        # BAD DESIGN WARNING: last used tool
        workspace = context.workspace
        space_type = workspace.tools_space_type
        mode = workspace.tools_mode
        item, tool, icon_value = ToolSelectPanelHelper._tool_get_active(context, space_type, mode, with_icon=True)
        if item is None:
            return None
        # Note: we could show 'item.text' here but it makes the layout jitter when switching tools.
        # Add some spacing since the icon is currently assuming regular small icon size.
        layout.label(text="    " + item.text if show_tool_name else " ", icon_value=icon_value)
        draw_settings = item.draw_settings
        if draw_settings is not None:
            draw_settings(context, layout, tool)
        return tool


# The purpose of this menu is to be a generic popup to select between tools
# in cases when a single tool allows to select alternative tools.
class WM_MT_toolsystem_submenu(Menu):
    bl_label = ""

    @staticmethod
    def _tool_group_from_button(context):
        # Lookup the tool definitions based on the space-type.
        cls = ToolSelectPanelHelper._tool_class_from_space_type(context.space_data.type)
        if cls is not None:
            button_text = ToolSelectPanelHelper._tool_text_from_button(context)
            for item_group in cls.tools_from_context(context):
                if type(item_group) is tuple:
                    for sub_item in item_group:
                        if sub_item.text == button_text:
                            return cls, item_group
        return None, None

    def draw(self, context):
        layout = self.layout
        layout.scale_y = 2.0

        _cls, item_group = self._tool_group_from_button(context)
        if item_group is None:
            # Should never happen, just in case
            layout.label(text="Unable to find toolbar group")
            return

        for item in item_group:
            if item is None:
                layout.separator()
                continue
            icon_value = ToolSelectPanelHelper._icon_value_from_icon_handle(item.icon)
            layout.operator(
                "wm.tool_set_by_name",
                text=item.text,
                icon_value=icon_value,
            ).name = item.text


def _activate_by_item(context, space_type, item, index):
    tool = ToolSelectPanelHelper._tool_active_from_context(context, space_type, create=True)
    tool.setup(
        name=item.text,
        keymap=item.keymap[0].name if item.keymap is not None else "",
        cursor=item.cursor or 'DEFAULT',
        gizmo_group=item.widget or "",
        data_block=item.data_block or "",
        operator=item.operator or "",
        index=index,
    )


def activate_by_name(context, space_type, text):
    _cls, item, index = ToolSelectPanelHelper._tool_get_by_name(context, space_type, text)
    if item is None:
        return False
    _activate_by_item(context, space_type, item, index)
    return True


def activate_by_name_or_cycle(context, space_type, text, offset=1):

    # Only cycle when the active tool is activated again.
    cls, item, _index = ToolSelectPanelHelper._tool_get_by_name(context, space_type, text)
    if item is None:
        return False

    tool_active = ToolSelectPanelHelper._tool_active_from_context(context, space_type)
    text_active = getattr(tool_active, "name", None)

    text_current = ""
    for item_group in cls.tools_from_context(context):
        if type(item_group) is tuple:
            index_current = cls._tool_group_active.get(item_group[0].text, 0)
            for sub_item in item_group:
                if sub_item.text == text:
                    text_current = item_group[index_current].text
                    break
            if text_current:
                break

    if text_current == "":
        return activate_by_name(context, space_type, text)
    if text_active != text_current:
        return activate_by_name(context, space_type, text_current)

    index_found = (tool_active.index + offset) % len(item_group)

    cls._tool_group_active[item_group[0].text] = index_found

    item_found = item_group[index_found]
    _activate_by_item(context, space_type, item_found, index_found)
    return True


def description_from_name(context, space_type, text, *, use_operator=True):
    # Used directly for tooltips.
    _cls, item, _index = ToolSelectPanelHelper._tool_get_by_name(context, space_type, text)
    if item is None:
        return False

    # Custom description.
    description = item.description
    if description is not None:
        return description

    # Extract from the operator.
    if use_operator:
        operator = item.operator

        if operator is None:
            if item.keymap is not None:
                operator = item.keymap[0].keymap_items[0].idname

        if operator is not None:
            import _bpy
            return _bpy.ops.get_rna_type(operator).description
    return ""


def keymap_from_name(context, space_type, text):
    # Used directly for tooltips.
    _cls, item, _index = ToolSelectPanelHelper._tool_get_by_name(context, space_type, text)
    if item is None:
        return False

    keymap = item.keymap
    # List container of one.
    if keymap:
        return keymap[0]
    return ""


def keymap_from_context(context, space_type):
    """
    Keymap for popup toolbar, currently generated each time.
    """

    def modifier_keywords_from_item(kmi):
        kw = {}
        for (attr, default) in (
                ("any", False),
                ("shift", False),
                ("ctrl", False),
                ("alt", False),
                ("oskey", False),
                ("key_modifier", 'NONE'),
        ):
            val = getattr(kmi, attr)
            if val != default:
                kw[attr] = val
        return kw

    def dict_as_tuple(d):
        return tuple((k, v) for (k, v) in sorted(d.items()))

    use_simple_keymap = False

    # Generate items when no keys are mapped.
    use_auto_keymap = True

    # Temporary, only create so we can pass 'properties' to find_item_from_operator.
    use_hack_properties = True

    km_name = "Toolbar Popup"
    wm = context.window_manager
    keyconf = wm.keyconfigs.active
    keymap = keyconf.keymaps.get(km_name)
    if keymap is None:
        keymap = keyconf.keymaps.new(km_name, space_type='EMPTY', region_type='TEMPORARY')
    for kmi in keymap.keymap_items:
        keymap.keymap_items.remove(kmi)

    kmi_unique_args = set()

    cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)

    items_all = [
        # 0: tool
        # 1: keymap item (direct access)
        # 2: keymap item (newly calculated for toolbar)
        [item, None, None]
        for item in ToolSelectPanelHelper._tools_flatten(cls.tools_from_context(context))
        if item is not None
    ]

    if use_hack_properties:
        kmi_hack = keymap.keymap_items.new("wm.tool_set_by_name", 'A', 'PRESS')
        kmi_hack_properties = kmi_hack.properties

        kmi_hack_brush_select = keymap.keymap_items.new("paint.brush_select", 'A', 'PRESS')
        kmi_hack_brush_select_properties = kmi_hack_brush_select.properties

    if use_simple_keymap:
        # Simply assign a key from A-Z.
        for i, (item, _, _) in enumerate(items_all):
            key = chr(ord('A') + i)
            kmi = keymap.keymap_items.new("wm.tool_set_by_name", key, 'PRESS')
            kmi.properties.name = item.text
    else:
        for item_container in items_all:
            item = item_container[0]
            # Only check the first item in the tools key-map (a little arbitrary).

            if use_hack_properties:
                # First check for direct assignment.
                kmi_hack_properties.name = item.text
                kmi_found = wm.keyconfigs.find_item_from_operator(
                    idname="wm.tool_set_by_name",
                    context='INVOKE_REGION_WIN',
                    # properties={"name": item.text},
                    properties=kmi_hack_properties,
                )[1]

                if kmi_found is None:
                    if item.data_block:
                        # PAINT_OT_brush_select
                        brush = bpy.data.brushes.get(item.data_block)
                        if brush is not None:
                            mode = context.active_object.mode
                            attr_op, attr_brush = {
                                'SCULPT': ("sculpt_tool", "sculpt_tool"),
                                'WEIGHT_PAINT': ("weight_paint_tool", "vertex_tool"),
                                'VERTEX_PAINT': ("vertex_paint_tool", "vertex_tool"),
                                'TEXTURE_PAINT': ("texture_paint_tool", "image_tool"),
                            }.get(mode, (None, None))
                            if attr_op is not None:
                                kmi_hack_brush_select_properties.paint_mode = mode
                                setattr(kmi_hack_brush_select_properties, attr_op, getattr(brush, attr_brush))
                                kmi_found = wm.keyconfigs.find_item_from_operator(
                                    idname="paint.brush_select",
                                    context='INVOKE_REGION_WIN',
                                    properties=kmi_hack_brush_select_properties,
                                )[1]
                            elif mode == 'GPENCIL_PAINT':
                                # TODO: gpencil.brush_select
                                # By default no keys are mapped to this, pass.
                                pass
                            else:
                                print("Unsupported mode:", mode)
                            del mode, attr_op, attr_brush

            else:
                kmi_found = None

            if kmi_found is not None:
                pass
            elif item.operator is not None:
                kmi_found = wm.keyconfigs.find_item_from_operator(
                    idname=item.operator,
                    context='INVOKE_REGION_WIN',
                )[1]
            elif item.keymap is not None:
                kmi_first = item.keymap[0].keymap_items[0]
                kmi_found = wm.keyconfigs.find_item_from_operator(
                    idname=kmi_first.idname,
                    # properties=kmi_first.properties,  # prevents matches, don't use.
                    context='INVOKE_REGION_WIN',
                )[1]
                del kmi_first
            else:
                kmi_found = None
            item_container[1] = kmi_found

        # More complex multi-pass test.
        for item_container in items_all:
            item, kmi_found = item_container[:2]
            if kmi_found is None:
                continue
            kmi_found_type = kmi_found.type

            # Only for single keys.
            if (
                    (len(kmi_found_type) == 1) or
                    # When a tool is being activated instead of running an operator, just copy the shortcut.
                    (kmi_found.idname in {"wm.tool_set_by_name", "WM_OT_tool_set_by_name"})
            ):
                kmi_args = {"type": kmi_found_type, **modifier_keywords_from_item(kmi_found)}
                kmi = keymap.keymap_items.new(idname="wm.tool_set_by_name", value='PRESS', **kmi_args)
                kmi.properties.name = item.text
                item_container[2] = kmi
                if use_auto_keymap:
                    kmi_unique_args.add(dict_as_tuple(kmi_args))

        # Test for key_modifier, where alpha key is used as a 'key_modifier'
        # (grease pencil holding 'D' for example).
        for item_container in items_all:
            item, kmi_found, kmi_exist = item_container
            if kmi_found is None or kmi_exist:
                continue

            kmi_found_type = kmi_found.type
            if kmi_found_type in {
                    'LEFTMOUSE',
                    'RIGHTMOUSE',
                    'MIDDLEMOUSE',
                    'BUTTON4MOUSE',
                    'BUTTON5MOUSE',
                    'BUTTON6MOUSE',
                    'BUTTON7MOUSE',
                    'ACTIONMOUSE',
                    'SELECTMOUSE',
            }:
                kmi_found_type = kmi_found.key_modifier
                # excludes 'NONE'
                if len(kmi_found_type) == 1:
                    kmi_args = {"type": kmi_found_type, **modifier_keywords_from_item(kmi_found)}
                    del kmi_args["key_modifier"]
                    kmi_tuple = dict_as_tuple(kmi_args)
                    if kmi_tuple in kmi_unique_args:
                        continue
                    kmi = keymap.keymap_items.new(idname="wm.tool_set_by_name", value='PRESS', **kmi_args)
                    kmi.properties.name = item.text
                    item_container[2] = kmi
                    if use_auto_keymap:
                        kmi_unique_args.add(kmi_tuple)

        if use_auto_keymap:
            # Map all unmapped keys to numbers,
            # while this is a bit strange it means users will not confuse regular key bindings to ordered bindings.

            # Free events (last used first).
            kmi_type_auto = ('ONE', 'TWO', 'THREE', 'FOUR', 'FIVE', 'SIX', 'SEVEN', 'EIGHT', 'NINE', 'ZERO')
            # Map both numbers and num-pad.
            kmi_type_dupe = {
                'ONE': 'NUMPAD_1',
                'TWO': 'NUMPAD_2',
                'THREE': 'NUMPAD_3',
                'FOUR': 'NUMPAD_4',
                'FIVE': 'NUMPAD_5',
                'SIX': 'NUMPAD_6',
                'SEVEN': 'NUMPAD_7',
                'EIGHT': 'NUMPAD_8',
                'NINE': 'NUMPAD_9',
                'ZERO': 'NUMPAD_0',
            }

            def iter_free_events():
                for mod in ({}, {"shift": True}, {"ctrl": True}, {"alt": True}):
                    for e in kmi_type_auto:
                        yield (e, mod)

            iter_events = iter(iter_free_events())

            for item_container in items_all:
                item, kmi_found, kmi_exist = item_container
                if kmi_exist:
                    continue
                kmi_args = None
                while True:
                    key, mod = next(iter_events, (None, None))
                    if key is None:
                        break
                    kmi_args = {"type": key, **mod}
                    kmi_tuple = dict_as_tuple(kmi_args)
                    if kmi_tuple in kmi_unique_args:
                        kmi_args = None
                    else:
                        break

                if kmi_args is not None:
                    kmi = keymap.keymap_items.new(idname="wm.tool_set_by_name", value='PRESS', **kmi_args)
                    kmi.properties.name = item.text
                    item_container[2] = kmi
                    if use_auto_keymap:
                        kmi_unique_args.add(kmi_tuple)

                    key = kmi_type_dupe.get(kmi_args["type"])
                    if key is not None:
                        kmi_args["type"] = key
                        kmi_tuple = dict_as_tuple(kmi_args)
                        if not kmi_tuple in kmi_unique_args:
                            kmi = keymap.keymap_items.new(idname="wm.tool_set_by_name", value='PRESS', **kmi_args)
                            kmi.properties.name = item.text
                            if use_auto_keymap:
                                kmi_unique_args.add(kmi_tuple)

    if use_hack_properties:
        keymap.keymap_items.remove(kmi_hack)

    if True:
        # The shortcut will show, so we better support running it.
        kmi_search = wm.keyconfigs.find_item_from_operator(
            idname="wm.search_menu",
            context='INVOKE_REGION_WIN',
        )[1]
        if kmi_search:
            keymap.keymap_items.new(
                "wm.search_menu",
                type=kmi_search.type,
                value='PRESS',
                **modifier_keywords_from_item(kmi_search),
            )

    wm.keyconfigs.update()
    return keymap


classes = (
    WM_MT_toolsystem_submenu,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
