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


bl_info = {
    "name": "Icons",
    "author": "Crouch, N.tox, PKHG, Campbell Barton, Dany Lebel",
    "version": (1, 5, 2),
    "blender": (2, 57, 0),
    "location": "Text Editor > Properties or " "Console > Console Menu",
    "warning": "",
    "description": "Click an icon to display its name and "
                   "copy it to the clipboard",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/"
                "Py/Scripts/System/Display_All_Icons",
    "category": "Development",
}


import bpy


def create_icon_list_all():
    icons = bpy.types.UILayout.bl_rna.functions['prop'].parameters['icon'].\
        enum_items.keys()

    icons.remove("NONE")

    return icons


def create_icon_list():
    icons = create_icon_list_all()
    search = bpy.context.scene.icon_props.search.lower()

    if search == "":
        pass
    else:
        icons = [key for key in icons if search in key.lower()]

    return icons


class WM_OT_icon_info(bpy.types.Operator):
    bl_idname = "wm.icon_info"
    bl_label = "Icon Info"
    bl_description = "Click to copy this icon name to the clipboard"
    icon = bpy.props.StringProperty()
    icon_scroll = bpy.props.IntProperty()

    def invoke(self, context, event):
        bpy.data.window_managers['WinMan'].clipboard = self.icon
        self.report({'INFO'}, "Icon ID: %s" % self.icon)
        return {'FINISHED'}


class OBJECT_PT_icons(bpy.types.Panel):
    bl_space_type = "TEXT_EDITOR"
    bl_region_type = "UI"
    bl_label = "All icons"

    def __init__(self):
        self.amount = 10
        self.icon_list = create_icon_list()

    def draw(self, context):
        props = context.scene.icon_props
        # polling for updates
        if props.search != CONSOLE_HT_icons._search_old:
            self.icon_list = create_icon_list()
            # adjusting max value of scroller
#            IconProps.scroll = bpy.props.IntProperty(default=1, min=1,
#                max=max(1, len(self.icon_list) - self.amount + 1),
#                description="Drag to scroll icons")

        box = self.layout.box()
        # scroll view
        if not props.expand:
            # expand button
            toprow = box.row()
            toprow.prop(props, "expand", icon="TRIA_RIGHT", icon_only=True,
                text="", emboss=False) # icon_only broken?
            # search buttons
            row = toprow.row(align=True)
            row.prop(props, "search", icon="VIEWZOOM", text="")
            # scroll button
            row = toprow.row()
            row.active = props.bl_rna.scroll[1]['max'] > 1
            row.prop(props, "scroll")

            # icons
            row = box.row(align=True)
            if len(self.icon_list) == 0:
                row.label("No icons found")
            else:
                for icon in self.icon_list[props.scroll - 1:
                props.scroll - 1 + self.amount]:
                    row.operator("wm.icon_info", text=" ", icon=icon,
                        emboss=False).icon = icon
                if len(self.icon_list) < self.amount:
                    for i in range(self.amount - len(self.icon_list) \
                    % self.amount):
                        row.label("")

        # expanded view
        else:
            # expand button
            toprow = box.row()
            toprow.prop(props, "expand", icon="TRIA_DOWN", icon_only=True,
                text="", emboss=False)
            # search buttons
            row = toprow.row(align=True)
            row.prop(props, "search", icon="VIEWZOOM", text="")
            # scroll button
            row = toprow.row()
            row.active = False
            row.prop(props, "scroll")

            # icons
            col = box.column(align=True)
            if len(self.icon_list) == 0:
                col.label("No icons found")
            else:
                for i, icon in enumerate(self.icon_list):
                    if i % self.amount == 0:
                        row = col.row(align=True)
                    row.operator("wm.icon_info", text=" ", icon=icon,
                        emboss=False).icon = icon
                for i in range(self.amount - len(self.icon_list) \
                % self.amount):
                    row.label("")


class CONSOLE_HT_icons(bpy.types.Header):
    bl_space_type = 'CONSOLE'
    _search_old = ""

    def __init__(self):
        self.amount = 10
        self.icon_list = create_icon_list()

    def draw(self, context):
        props = context.scene.icon_props
        # polling for updates
        if props.search != self.__class__._search_old:
            self.__class__._search_old = props.search
            self.icon_list = create_icon_list()
            # adjusting max value of scroller
#            IconProps.scroll = bpy.props.IntProperty(default=1, min=1,
#                max=max(1, len(self.icon_list) - self.amount + 1),
#                description="Drag to scroll icons")

        # scroll view
        if props.console:
            layout = self.layout
            layout.separator()
            # search buttons
            row = layout.row()
            row.prop(props, "search", icon="VIEWZOOM")
            # scroll button
            row = layout.row()
            row.active = props.bl_rna.scroll[1]['max'] > 1
            row.prop(props, "scroll")

            # icons
            row = layout.row(align=True)
            if len(self.icon_list) == 0:
                row.label("No icons found")
            else:
                for icon in self.icon_list[props.scroll - 1:
                props.scroll - 1 + self.amount]:
                    row.operator("wm.icon_info", text="", icon=icon,
                        emboss=False).icon = icon


def menu_func(self, context):
    self.layout.prop(bpy.context.scene.icon_props, 'console')


def register():
    global IconProps

    icons_total = len(create_icon_list_all())
    icons_per_row = 10

    class IconProps(bpy.types.PropertyGroup):
        """
        Fake module like class
        bpy.context.scene.icon_props
        """
        console = bpy.props.BoolProperty(name='Show System Icons',
            description='Display the Icons in the console header',
            default=False)
        expand = bpy.props.BoolProperty(name="Expand",
            description="Expand, to display all icons at once",
            default=False)
        search = bpy.props.StringProperty(name="Search",
            description="Search for icons by name",
            default="")
        scroll = bpy.props.IntProperty(name="Scroll",
            description="Drag to scroll icons",
            default=1, min=1, max=max(1, icons_total - icons_per_row + 1))

    bpy.utils.register_module(__name__)
    bpy.types.Scene.icon_props = bpy.props.PointerProperty(type=IconProps)
    bpy.types.CONSOLE_MT_console.append(menu_func)


def unregister():
    if bpy.context.scene.get('icon_props') != None:
        del bpy.context.scene['icon_props']
    try:
        del bpy.types.Scene.icon_props
        bpy.types.CONSOLE_MT_console.remove(menu_func)
    except:
        pass
    if __name__ == "__main__":
        # unregistering is only done automatically when run as addon
        bpy.utils.unregister_class(OBJECT_PT_icons)
        bpy.utils.unregister_class(CONSOLE_HT_icons)

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
