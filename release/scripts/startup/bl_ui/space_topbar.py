# SPDX-License-Identifier: GPL-2.0-or-later

# <pep8 compliant>
import bpy
import os
from pathlib import Path

user_path = Path(bpy.utils.resource_path('USER')).parent
local_path = Path(bpy.utils.resource_path('LOCAL')).parent

from bpy.types import Header, Menu, Panel


class TOPBAR_HT_upper_bar(Header):
    bl_space_type = 'TOPBAR'

    def draw(self, context):
        region = context.region

        if region.alignment == 'RIGHT':
            self.draw_right(context)
        else:
            self.draw_left(context)

    def draw_left(self, context):
        layout = self.layout

        window = context.window
        screen = context.screen

        TOPBAR_MT_editor_menus.draw_collapsible(context, layout)

        layout.separator()

        if not screen.show_fullscreen:
            layout.template_ID_tabs(
                window, "workspace",
                new="workspace.add",
                menu="TOPBAR_MT_workspace_menu",
            )
        else:
            layout.operator(
                "screen.back_to_previous",
                icon='SCREEN_BACK',
                text="Back to Previous",
            )

    def draw_right(self, context):
        layout = self.layout

        window = context.window
        screen = context.screen
        scene = window.scene

        # If statusbar is hidden, still show messages at the top
        if not screen.show_statusbar:
            layout.template_reports_banner()
            layout.template_running_jobs()


class TOPBAR_PT_tool_settings_extra(Panel):
    """
    Popover panel for adding extra options that don't fit in the tool settings header
    """
    bl_idname = "TOPBAR_PT_tool_settings_extra"
    bl_region_type = 'HEADER'
    bl_space_type = 'TOPBAR'
    bl_label = "Extra Options"

    def draw(self, context):
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
        layout = self.layout

        # Get the active tool
        space_type, mode = ToolSelectPanelHelper._tool_key_from_context(
            context)
        cls = ToolSelectPanelHelper._tool_class_from_space_type(space_type)
        item, tool, _ = cls._tool_get_active(
            context, space_type, mode, with_icon=True)
        if item is None:
            return

        # Draw the extra settings
        item.draw_settings(context, layout, tool, extra=True)


class TOPBAR_PT_tool_fallback(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Layers"
    bl_ui_units_x = 8

    def draw(self, context):
        from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
        layout = self.layout

        tool_settings = context.tool_settings
        ToolSelectPanelHelper.draw_fallback_tool_items(layout, context)
        if tool_settings.workspace_tool_type == 'FALLBACK':
            tool = context.tool
            ToolSelectPanelHelper.draw_active_tool_fallback(context, layout, tool)


class TOPBAR_PT_gpencil_layers(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Layers"
    bl_ui_units_x = 14

    @classmethod
    def poll(cls, context):
        if context.gpencil_data is None:
            return False

        ob = context.object
        if ob is not None and ob.type == 'GPENCIL':
            return True

        return False

    def draw(self, context):
        layout = self.layout
        gpd = context.gpencil_data

        # Grease Pencil data...
        if (gpd is None) or (not gpd.layers):
            layout.operator("gpencil.layer_add", text="New Layer")
        else:
            self.draw_layers(context, layout, gpd)

    def draw_layers(self, context, layout, gpd):
        row = layout.row()

        col = row.column()
        layer_rows = 10
        col.template_list("GPENCIL_UL_layer", "", gpd, "layers", gpd.layers, "active_index",
                          rows=layer_rows, sort_reverse=True, sort_lock=True)

        gpl = context.active_gpencil_layer
        if gpl:
            srow = col.row(align=True)
            srow.prop(gpl, "blend_mode", text="Blend")

            srow = col.row(align=True)
            srow.prop(gpl, "opacity", text="Opacity", slider=True)
            srow.prop(gpl, "use_mask_layer", text="",
                      icon='MOD_MASK' if gpl.use_mask_layer else 'MOD_MASK_OFF')

            srow = col.row(align=True)
            srow.prop(gpl, "use_lights")

        col = row.column()

        sub = col.column(align=True)
        sub.operator("gpencil.layer_add", icon='ADD', text="")
        sub.operator("gpencil.layer_remove", icon='REMOVE', text="")

        gpl = context.active_gpencil_layer
        if gpl:
            sub.menu("GPENCIL_MT_layer_context_menu", icon='DOWNARROW_HLT', text="")

            if len(gpd.layers) > 1:
                col.separator()

                sub = col.column(align=True)
                sub.operator("gpencil.layer_move", icon='TRIA_UP', text="").type = 'UP'
                sub.operator("gpencil.layer_move", icon='TRIA_DOWN', text="").type = 'DOWN'

                col.separator()

                sub = col.column(align=True)
                sub.operator("gpencil.layer_isolate", icon='HIDE_OFF', text="").affect_visibility = True
                sub.operator("gpencil.layer_isolate", icon='LOCKED', text="").affect_visibility = False


class TOPBAR_MT_editor_menus(Menu):
    bl_idname = "TOPBAR_MT_editor_menus"
    bl_label = ""

    def draw(self, context):
        layout = self.layout

        layout.menu("TOPBAR_MT_file")
        layout.menu("TOPBAR_MT_edit")

        layout.menu("TOPBAR_MT_render")

        layout.menu("TOPBAR_MT_window")
        layout.menu("TOPBAR_MT_help")


class TOPBAR_MT_file_cleanup(Menu):
    bl_label = "Clean Up"

    def draw(self, _context):
        layout = self.layout
        layout.separator()

        op_props = layout.operator("outliner.orphans_purge", text="Unused Data", icon = "CLEAN_CHANNELS")
        op_props.do_local_ids = True
        op_props.do_linked_ids = True
        op_props.do_recursive = False
        op_props = layout.operator("outliner.orphans_purge", text="Recursive Unused Data", icon = "CLEAN_CHANNELS")
        op_props.do_local_ids = True
        op_props.do_linked_ids = True
        op_props.do_recursive = True

        layout.separator()
        op_props = layout.operator("outliner.orphans_purge", text="Unused Linked Data", icon = "CLEAN_CHANNELS")
        op_props.do_local_ids = False
        op_props.do_linked_ids = True
        op_props.do_recursive = False
        op_props = layout.operator("outliner.orphans_purge", text="Recursive Unused Linked Data", icon = "CLEAN_CHANNELS")
        op_props.do_local_ids = False
        op_props.do_linked_ids = True
        op_props.do_recursive = True

        layout.separator()
        op_props = layout.operator("outliner.orphans_purge", text="Unused Local Data", icon = "CLEAN_CHANNELS")
        op_props.do_local_ids = True
        op_props.do_linked_ids = False
        op_props.do_recursive = False
        op_props = layout.operator("outliner.orphans_purge", text="Recursive Unused Local Data", icon = "CLEAN_CHANNELS")
        op_props.do_local_ids = True
        op_props.do_linked_ids = False
        op_props.do_recursive = True


class TOPBAR_MT_file(Menu):
    bl_label = "File"

    #bfa - incremental save calculation
    @staticmethod
    def _save_calculate_incremental_name():
        import re
        dirname, base_name = os.path.split(bpy.data.filepath)
        base_name_no_ext, ext = os.path.splitext(base_name)
        match = re.match(r"(.*)_([\d]+)$", base_name_no_ext)
        if match:
            prefix, number = match.groups()
            number = int(number) + 1
        else:
            prefix, number = base_name_no_ext, 1
        prefix = os.path.join(dirname, prefix)
        while os.path.isfile(output := "%s_%03d%s" % (prefix, number, ext)):
            number += 1
        return output

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.read_homefile", text="New", icon='NEW')
        layout.menu("TOPBAR_MT_file_new", text="New from Template")
        layout.operator("wm.open_mainfile", text="Open", icon='FILE_FOLDER')
        layout.menu("TOPBAR_MT_file_open_recent")
        layout.operator("wm.revert_mainfile", icon='FILE_REFRESH')
        layout.operator("wm.recover_last_session", icon='RECOVER_LAST')
        layout.operator("wm.recover_auto_save", text="Recover Auto Save", icon='RECOVER_AUTO')

        layout.separator()

        layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
        layout.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="Save As", icon='SAVE_AS')
        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="Save Copy", icon='SAVE_COPY').copy = True

        if bpy.data.is_saved:
            default_operator_contest = layout.operator_context
            layout.operator_context = 'EXEC_DEFAULT'
            layout.operator( "wm.save_as_mainfile", text="Incremental Save", icon='SAVE_AS').filepath = self._save_calculate_incremental_name()
            layout.operator_context = default_operator_contest
        else:
            col = layout.column()
            col.active = bpy.data.is_saved
            col.operator( "wm.save_as_mainfile", text="Incremental Save (Unsaved)", icon='SAVE_AS').filepath = "" #bfa dummy unsaved

        layout.separator()

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.link", text="Link", icon='LINK_BLEND')
        layout.operator("wm.append", text="Append", icon='APPEND_BLEND')
        layout.menu("TOPBAR_MT_file_previews")

        layout.separator()

        layout.menu("TOPBAR_MT_file_import")
        layout.menu("TOPBAR_MT_file_export")

        layout.separator()

        layout.menu("TOPBAR_MT_file_external_data")
        layout.menu("TOPBAR_MT_file_cleanup")

        layout.separator()

        layout.operator("wm.quit_blender", text="Quit", icon='QUIT')


class TOPBAR_MT_file_new(Menu):
    bl_label = "New File from Template"

    @staticmethod
    def app_template_paths():
        import os

        template_paths = bpy.utils.app_template_paths()

        # Expand template paths.

        # Use a set to avoid duplicate user/system templates.
        # This is a corner case, but users managed to do it! T76849.
        app_templates = set()
        for path in template_paths:
            for d in os.listdir(path):
                if d.startswith(("__", ".")):
                    continue
                template = os.path.join(path, d)
                if os.path.isdir(template):
                    app_templates.add(d)

        return sorted(app_templates)

    @staticmethod
    def draw_ex(layout, _context, *, use_splash=False, use_more=False):
        layout.operator_context = 'INVOKE_DEFAULT'

        # Limit number of templates in splash screen, spill over into more menu.
        paths = TOPBAR_MT_file_new.app_template_paths()
        splash_limit = 5

        if use_splash:
            icon = 'FILE_NEW'
            show_more = len(paths) > (splash_limit - 1)
            if show_more:
                paths = paths[:splash_limit - 2]
        elif use_more:
            icon = 'FILE_NEW'
            paths = paths[splash_limit - 2:]
            show_more = False
        else:
            icon = 'NONE'
            show_more = False

        # Draw application templates.
        if not use_more:
            props = layout.operator("wm.read_homefile", text="General", icon=icon)
            props.app_template = ""

        for d in paths:
            props = layout.operator(
                "wm.read_homefile",
                text=bpy.path.display_name(d),
                icon=icon,
            )
            props.app_template = d

        layout.operator_context = 'EXEC_DEFAULT'

        if show_more:
            layout.menu("TOPBAR_MT_templates_more", text="...")

    def draw(self, context):
        TOPBAR_MT_file_new.draw_ex(self.layout, context)


class TOPBAR_MT_templates_more(Menu):
    bl_label = "Templates"

    def draw(self, context):
        bpy.types.TOPBAR_MT_file_new.draw_ex(self.layout, context, use_more=True)


class TOPBAR_MT_file_import(Menu):
    bl_idname = "TOPBAR_MT_file_import"
    bl_label = "Import"
    bl_owner_use_filter = False

    def draw(self, _context):
        if bpy.app.build_options.collada:
            self.layout.operator("wm.collada_import", text="Collada (.dae)", icon = "LOAD_DAE")
        if bpy.app.build_options.alembic:
            self.layout.operator("wm.alembic_import", text="Alembic (.abc)", icon = "LOAD_ABC")

        if bpy.app.build_options.usd:
            self.layout.operator(
                "wm.usd_import", text="Universal Scene Description (.usd, .usdc, .usda)", icon = "LOAD_USD")

        self.layout.operator("wm.gpencil_import_svg", text="SVG as Grease Pencil", icon = "LOAD_SVG_GPENCIL")
        self.layout.operator("wm.obj_import", text="Wavefront (.obj) (experimental)")


class TOPBAR_MT_file_export(Menu):
    bl_idname = "TOPBAR_MT_file_export"
    bl_label = "Export"
    bl_owner_use_filter = False

    def draw(self, _context):
        self.layout.operator("wm.obj_export", text="Wavefront OBJ (.obj) (experimental)", icon = "SAVE_OBJ")
        if bpy.app.build_options.collada:
            self.layout.operator("wm.collada_export", text="Collada (.dae)", icon = "SAVE_DAE")
        if bpy.app.build_options.alembic:
            self.layout.operator("wm.alembic_export", text="Alembic (.abc)", icon = "SAVE_ABC")
        if bpy.app.build_options.usd:
            self.layout.operator(
                "wm.usd_export", text="Universal Scene Description (.usd, .usdc, .usda)", icon = "SAVE_USD")

        # Pugixml lib dependency
        if bpy.app.build_options.pugixml:
            self.layout.operator("wm.gpencil_export_svg", text="Grease Pencil as SVG", icon = "SAVE_SVG")
        # Haru lib dependency
        if bpy.app.build_options.haru:
            self.layout.operator("wm.gpencil_export_pdf", text="Grease Pencil as PDF", icon = "SAVE_PDF")


class TOPBAR_MT_file_external_data(Menu):
    bl_label = "External Data"

    def draw(self, _context):
        layout = self.layout

        icon = 'CHECKBOX_HLT' if bpy.data.use_autopack else 'CHECKBOX_DEHLT'
        layout.operator("file.autopack_toggle", icon=icon)

        layout.separator()

        pack_all = layout.row()
        pack_all.operator("file.pack_all", icon = "PACKAGE")
        pack_all.active = not bpy.data.use_autopack

        layout.separator()

        layout.operator("file.pack_libraries", icon = "PACKAGE")
        layout.operator("file.unpack_libraries", icon = "PACKAGE")

        unpack_all = layout.row()
        unpack_all.operator("file.unpack_all", icon = "PACKAGE")
        unpack_all.active = not bpy.data.use_autopack

        layout.separator()

        layout.operator("file.make_paths_relative", icon = "RELATIVEPATH")
        layout.operator("file.make_paths_absolute", icon = "ABSOLUTEPATH")

        layout.separator()

        layout.operator("file.report_missing_files", icon = "ERROR")
        layout.operator("file.find_missing_files", icon = "VIEWZOOM")


class TOPBAR_MT_file_previews(Menu):
    bl_label = "Data Previews"

    def draw(self, _context):
        layout = self.layout

        layout.operator("wm.previews_ensure", icon = "FILE_REFRESH")
        layout.operator("wm.previews_batch_generate", icon = "BATCH_GENERATE")

        layout.separator()

        layout.operator("wm.previews_clear", icon = "DATABLOCK_CLEAR")
        layout.operator("wm.previews_batch_clear", icon = "BATCH_GENERATE_CLEAR")


class TOPBAR_MT_render(Menu):
    bl_label = "Render"

    def draw(self, context):
        layout = self.layout

        rd = context.scene.render

        layout.operator("render.render", text="Render Image", icon='RENDER_STILL').use_viewport = True
        props = layout.operator("render.render", text="Render Animation", icon='RENDER_ANIMATION')
        props.animation = True
        props.use_viewport = True

        layout.separator()

        layout.operator("sound.mixdown", text="Mixdown Audio", icon='PLAY_AUDIO')

        layout.separator()

        layout.operator("render.opengl", text="OpenGL Render Image", icon = 'RENDER_STILL_VIEW')
        layout.operator("render.opengl", text="OpenGL Render Animation", icon = 'RENDER_ANI_VIEW').animation = True


        layout.separator()

        layout.operator("render.view_show", text="Show/Hide Render", icon = 'HIDE_RENDERVIEW')
        layout.operator("render.play_rendered_anim", text="Play rendered Animation", icon='PLAY')

        layout.separator()

        layout.prop(rd, "use_lock_interface", text="Lock Interface")


class TOPBAR_MT_edit(Menu):
    bl_label = "Edit"

    def draw(self, context):
        layout = self.layout

        layout.operator("ed.undo", icon='UNDO')
        layout.operator("ed.redo", icon='REDO')

        layout.separator()

        layout.menu("TOPBAR_MT_undo_history")

        layout.separator()

        layout.operator("screen.repeat_last", icon='REPEAT',)
        layout.operator("screen.repeat_history", text="Repeat History", icon='REDO_HISTORY',)

        layout.separator()

        layout.operator("screen.redo_last", text="Adjust Last Operation", icon = "LASTOPERATOR")

        layout.separator()

        layout.operator("wm.search_menu", text="Menu Search", icon='SEARCH_MENU')
        layout.operator("wm.search_operator", text="Operator Search", icon='VIEWZOOM')

        layout.separator()

        # Mainly to expose shortcut since this depends on the context.
        props = layout.operator("wm.call_panel", text="Rename Active Item", icon='RENAME')
        props.name = "TOPBAR_PT_name"
        props.keep_open = False

        layout.operator("wm.batch_rename", text = "Batch Rename", icon='RENAME')

        layout.separator()

        layout.operator("preferences.app_template_install", text="Install Application Template", icon = "APPTEMPLATE")

        layout.separator()

        layout.operator_context = 'INVOKE_AREA'

        if any(bpy.utils.app_template_paths()):
            app_template = context.preferences.app_template
        else:
            app_template = None

        if app_template:
            layout.label(text= "-- Template: " + bpy.path.display_name(app_template, has_ext=False)+" --")

        layout.operator("wm.save_homefile", icon='SAVE_PREFS')
        props = layout.operator("wm.read_factory_settings", icon='LOAD_FACTORY')
        if app_template:
            props.app_template = app_template

        layout.separator()

        #bfa - preferences path exists
        if os.path.isdir(Path(bpy.utils.resource_path('USER'))):
            layout.operator("wm.path_open", text="Open Preferences Folder", icon = "FOLDER_REDIRECT").filepath = str(user_path)
        #bfa - preferences path does not exist yet
        else:
            #layout.operator("wm.path_open", text="Open Preferences Folder", icon = "FOLDER_REDIRECT").filepath = str(local_path)
            layout.operator("topbar.no_prefsfolder", text="Open Preferences Folder", icon = "FOLDER_REDIRECT")

        layout.operator("screen.userpref_show", text="Preferences", icon='PREFERENCES')


# Workaround to separate the tooltips for the preferences folder
class TOPBAR_MT_edit_no_prefsfolder(bpy.types.Operator):
    """The preferences folder does not exist yet\nThe file browser will open at the installation directory instead\nPlease click at Next in the splash sceen first"""
    bl_idname = "topbar.no_prefsfolder"        # unique identifier for buttons and menu items to reference.
    bl_label = "Open Installation folder"         # display name in the interface.
    bl_options = {'REGISTER', 'UNDO'}  # enable undo for the operator.

    def execute(self, context):        # execute() is called by blender when running the operator.
        bpy.ops.wm.path_open(filepath = str(local_path))
        return {'FINISHED'}


class TOPBAR_MT_window(Menu):
    bl_label = "Window"

    def draw(self, context):
        import sys

        layout = self.layout
        operator_context_default = layout.operator_context

        layout.operator("wm.window_new", icon = "NEW_WINDOW")
        layout.operator("wm.window_new_main", icon = "NEW_WINDOW_MAIN")

        layout.separator()

        layout.operator("wm.window_fullscreen_toggle", icon='FULLSCREEN_ENTER')

        layout.separator()

        layout.operator("screen.workspace_cycle", text="Next Workspace", icon = "FRAME_NEXT").direction = 'NEXT'
        layout.operator("screen.workspace_cycle", text="Previous Workspace", icon = "FRAME_PREV").direction = 'PREV'

        layout.separator()

        layout.prop(context.screen, "show_statusbar")

        layout.separator()

        layout.operator("screen.screenshot", icon='MAKE_SCREENSHOT')


        # Showing the status in the area doesn't work well in this case.
        # - From the top-bar, the text replaces the file-menu (not so bad but strange).
        # - From menu-search it replaces the area that the user may want to screen-shot.
        # Setting the context to screen causes the status to show in the global status-bar.
        layout.operator_context = 'INVOKE_SCREEN'
        layout.operator("screen.screenshot_area", icon = "MAKE_SCREENSHOT_AREA")
        layout.operator_context = operator_context_default

        if sys.platform[:3] == "win":
            layout.separator()
            layout.operator("wm.console_toggle", icon='CONSOLE')


class TOPBAR_MT_help(Menu):
    bl_label = "Help"

    def draw(self, context):
        layout = self.layout

        layout.operator("wm.url_open", text="Manual", icon='HELP').url = "https://www.bforartists.de/bforartists-2-reference-manual/"
        layout.operator("wm.url_open", text="Release notes", icon='URL').url = "https://www.bforartists.de/release-notes/"

        layout.separator()

        layout.operator("wm.url_open", text="Bforartists Website", icon='URL').url = "https://www.bforartists.de"
        layout.operator("wm.url_open", text="Quickstart Learning Videos (Youtube)", icon='URL').url = "https://www.youtube.com/watch?v=sZlqqMAGgMs&list=PLB0iqEbIPQTZArhZspyYSJOS_00jURpUB"

        layout.separator()

        layout.operator("wm.url_open", text="Report a Bug", icon='URL').url = "https://github.com/Bforartists/Bforartists/issues"

        layout.separator()

        layout.operator("wm.url_open_preset", text="Python API Reference", icon='URL').type = 'API'
        layout.operator("wm.sysinfo", icon='TEXT')

        layout.separator()

        layout.operator("wm.splash", icon='BLENDER')


class TOPBAR_MT_file_context_menu(Menu):
    bl_label = "File Context Menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator_context = 'INVOKE_AREA'
        layout.menu("TOPBAR_MT_file_new", text="New", icon='FILE_NEW')
        layout.operator("wm.open_mainfile", text="Open...", icon='FILE_FOLDER')

        layout.separator()

        layout.operator("wm.link", text="Link...", icon='LINK_BLEND')
        layout.operator("wm.append", text="Append...", icon='APPEND_BLEND')

        layout.separator()

        layout.menu("TOPBAR_MT_file_import", icon='IMPORT')
        layout.menu("TOPBAR_MT_file_export", icon='EXPORT')

        layout.separator()

        layout.operator("screen.userpref_show", text="Preferences...", icon='PREFERENCES')


class TOPBAR_MT_workspace_menu(Menu):
    bl_label = "Workspace"

    def draw(self, _context):
        layout = self.layout

        layout.operator("workspace.duplicate", text="Duplicate", icon='DUPLICATE')
        if len(bpy.data.workspaces) > 1:
            layout.operator("workspace.delete", text="Delete", icon='DELETE')

        layout.separator()

        layout.operator("workspace.reorder_to_front", text="Reorder to Front", icon='TRIA_LEFT_BAR')
        layout.operator("workspace.reorder_to_back", text="Reorder to Back", icon='TRIA_RIGHT_BAR')

        layout.separator()

        # For key binding discoverability.
        props = layout.operator("screen.workspace_cycle", text="Previous Workspace", icon='BACK')
        props.direction = 'PREV'
        props = layout.operator("screen.workspace_cycle", text="Next Workspace", icon='FORWARD')
        props.direction = 'NEXT'


# Grease Pencil Object - Primitive curve
class TOPBAR_PT_gpencil_primitive(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'HEADER'
    bl_label = "Primitives"

    def draw(self, context):
        settings = context.tool_settings.gpencil_sculpt

        layout = self.layout
        # Curve
        layout.template_curve_mapping(settings, "thickness_primitive_curve", brush=True)


# Only a popover
class TOPBAR_PT_name(Panel):
    bl_space_type = 'TOPBAR'  # dummy
    bl_region_type = 'HEADER'
    bl_label = "Rename Active Item"
    bl_ui_units_x = 14

    def draw(self, context):
        layout = self.layout

        # Edit first editable button in popup
        def row_with_icon(layout, icon):
            row = layout.row()
            row.activate_init = True
            row.label(icon=icon)
            return row

        mode = context.mode
        space = context.space_data
        space_type = None if (space is None) else space.type
        found = False
        if space_type == 'SEQUENCE_EDITOR':
            layout.label(text="Sequence Strip Name")
            item = context.active_sequence_strip
            if item:
                row = row_with_icon(layout, 'SEQUENCE')
                row.prop(item, "label", text="")
                found = True
        elif space_type == 'NODE_EDITOR':
            layout.label(text="Node Label")
            item = context.active_node
            if item:
                row = row_with_icon(layout, 'NODE')
                row.prop(item, "label", text="")
                found = True
        elif space_type == 'NLA_EDITOR':
            layout.label(text="NLA Strip Name")
            item = next(
                (strip for strip in context.selected_nla_strips if strip.active), None)
            if item:
                row = row_with_icon(layout, 'NLA')
                row.prop(item, "name", text="")
                found = True
        else:
            if mode == 'POSE' or (mode == 'WEIGHT_PAINT' and context.pose_object):
                layout.label(text="Bone Name")
                item = context.active_pose_bone
                if item:
                    row = row_with_icon(layout, 'BONE_DATA')
                    row.prop(item, "name", text="")
                    found = True
            elif mode == 'EDIT_ARMATURE':
                layout.label(text="Bone Name")
                item = context.active_bone
                if item:
                    row = row_with_icon(layout, 'BONE_DATA')
                    row.prop(item, "name", text="")
                    found = True
            else:
                layout.label(text="Object Name")
                item = context.object
                if item:
                    row = row_with_icon(layout, 'OBJECT_DATA')
                    row.prop(item, "name", text="")
                    found = True

        if not found:
            row = row_with_icon(layout, 'ERROR')
            row.label(text="No active item")


classes = (
    TOPBAR_HT_upper_bar,
    TOPBAR_MT_file_context_menu,
    TOPBAR_MT_workspace_menu,
    TOPBAR_MT_editor_menus,
    TOPBAR_MT_file,
    TOPBAR_MT_file_new,
    TOPBAR_MT_templates_more,
    TOPBAR_MT_file_import,
    TOPBAR_MT_file_export,
    TOPBAR_MT_file_external_data,
    TOPBAR_MT_file_cleanup,
    TOPBAR_MT_file_previews,
    TOPBAR_MT_edit,
    TOPBAR_MT_render,
    TOPBAR_MT_window,
    TOPBAR_MT_edit_no_prefsfolder,
    TOPBAR_MT_help,
    TOPBAR_PT_tool_fallback,
    TOPBAR_PT_tool_settings_extra,
    TOPBAR_PT_gpencil_layers,
    TOPBAR_PT_gpencil_primitive,
    TOPBAR_PT_name,
)

if __name__ == "__main__":  # only for live edit.
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
