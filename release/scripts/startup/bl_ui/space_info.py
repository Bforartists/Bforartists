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
from bpy.types import Header, Menu


class INFO_HT_header(Header):
    bl_space_type = 'INFO'

    def draw(self, context):
        layout = self.layout

        window = context.window
        scene = context.scene
        rd = scene.render

        row = layout.row(align=True)
        row.template_header()

        if context.area.show_menus:
            sub = row.row(align=True)
            sub.menu("INFO_MT_file")
            if rd.use_game_engine:
                sub.menu("INFO_MT_game")
            else:
                sub.menu("INFO_MT_render")
            sub.menu("INFO_MT_window")
            sub.menu("INFO_MT_help")

        if window.screen.show_fullscreen:
            layout.operator("screen.back_to_previous", icon='SCREEN_BACK', text="Back to Previous")
            layout.separator()
        else:
            layout.template_ID(context.window, "screen", new="screen.new", unlink="screen.delete")
            layout.template_ID(context.screen, "scene", new="scene.new", unlink="scene.delete")

        layout.separator()

        if rd.has_multiple_engines:
            layout.prop(rd, "engine", text="")

        layout.separator()

        layout.template_running_jobs()

        layout.template_reports_banner()

        row = layout.row(align=True)

        if bpy.app.autoexec_fail is True and bpy.app.autoexec_fail_quiet is False:
            layout.operator_context = 'EXEC_DEFAULT'
            row.label("Auto-run disabled: %s" % bpy.app.autoexec_fail_message, icon='ERROR')
            if bpy.data.is_saved:
                props = row.operator("wm.open_mainfile", icon='SCREEN_BACK', text="Reload Trusted")
                props.filepath = bpy.data.filepath
                props.use_scripts = True

            row.operator("script.autoexec_warn_clear", text="Ignore")
            return

        row.operator("wm.splash", text="", icon='BLENDER', emboss=False)
        row.label(text=scene.statistics(), translate=False)


class INFO_MT_file(Menu):
    bl_label = "File"

    def draw(self, context):
        layout = self.layout

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.read_homefile", text="New", icon='NEW')
        layout.operator("wm.open_mainfile", text="Open...", icon='FILE_FOLDER')
        layout.menu("INFO_MT_file_open_recent", icon='OPEN_RECENT')
        layout.operator("wm.recover_last_session", icon='RECOVER_LAST')
        layout.operator("wm.recover_auto_save", text="Recover Auto Save...", icon='RECOVER_AUTO')

        layout.separator()

        layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
        layout.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="Save As...", icon='SAVE_AS')
        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_as_mainfile", text="Save Copy...", icon='SAVE_COPY').copy = True

        layout.separator()

        layout.operator("screen.userpref_show", text="User Preferences...", icon='PREFERENCES')

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.save_homefile", icon='SAVE_PREFS')
        layout.operator_context = 'EXEC_AREA'
        layout.operator("wm.read_factory_settings", icon='LOAD_FACTORY')

        layout.separator()

        layout.operator_context = 'INVOKE_AREA'
        layout.operator("wm.link_append", text="Link", icon='LINK_BLEND')
        props = layout.operator("wm.link_append", text="Append", icon='APPEND_BLEND')
        props.link = False
        props.instance_groups = False

        layout.separator()

        layout.menu("INFO_MT_file_import", icon='IMPORT')
        layout.menu("INFO_MT_file_export", icon='EXPORT')

        layout.separator()

        layout.menu("INFO_MT_file_external_data", icon='EXTERNAL_DATA')

        layout.separator()

        layout.operator_context = 'EXEC_AREA'
        layout.operator("wm.quit_blender", text="Quit", icon='QUIT')


class INFO_MT_file_import(Menu):
    bl_idname = "INFO_MT_file_import"
    bl_label = "Import"

    def draw(self, context):
        if bpy.app.build_options.collada:
            self.layout.operator("wm.collada_import", text="Collada (Default) (.dae)")


class INFO_MT_file_export(Menu):
    bl_idname = "INFO_MT_file_export"
    bl_label = "Export"

    def draw(self, context):
        if bpy.app.build_options.collada:
            self.layout.operator("wm.collada_export", text="Collada (Default) (.dae)")


class INFO_MT_file_external_data(Menu):
    bl_label = "External Data"

    def draw(self, context):
        layout = self.layout

        layout.operator("file.pack_all", text="Pack into .blend file")
        layout.operator("file.unpack_all", text="Unpack into Files")

        layout.separator()

        layout.operator("file.make_paths_relative")
        layout.operator("file.make_paths_absolute")
        layout.operator("file.report_missing_files")
        layout.operator("file.find_missing_files")


class INFO_MT_game(Menu):
    bl_label = "Game"

    def draw(self, context):
        layout = self.layout

        gs = context.scene.game_settings

        layout.operator("view3d.game_start")

        layout.separator()

        layout.prop(gs, "show_debug_properties")
        layout.prop(gs, "show_framerate_profile")
        layout.prop(gs, "show_physics_visualization")
        layout.prop(gs, "use_deprecation_warnings")
        layout.prop(gs, "use_animation_record")
        layout.separator()
        layout.prop(gs, "use_auto_start")


class INFO_MT_render(Menu):
    bl_label = "Render"

    def draw(self, context):
        layout = self.layout

        layout.operator("render.render", text="Render Image", icon='RENDER_STILL')
        layout.operator("render.render", text="Render Animation", icon='RENDER_ANIMATION').animation = True

        layout.separator()

        layout.operator("render.opengl", text="OpenGL Render Image")
        layout.operator("render.opengl", text="OpenGL Render Animation").animation = True

        layout.separator()

        layout.operator("render.view_show")
        layout.operator("render.play_rendered_anim")


class INFO_MT_window(Menu):
    bl_label = "Window"

    def draw(self, context):
        import sys

        layout = self.layout

        layout.operator("wm.window_duplicate")
        layout.operator("wm.window_fullscreen_toggle", icon='FULLSCREEN_ENTER')

        layout.separator()

        layout.operator("screen.screenshot").full = True
        layout.operator("screen.screencast").full = True

        if sys.platform[:3] == "win":
            layout.separator()
            layout.operator("wm.console_toggle", icon='CONSOLE')


class INFO_MT_help(Menu):
    bl_label = "Help"

    def draw(self, context):
        layout = self.layout

        layout.operator("wm.url_open", text="Manual", icon='HELP').url = "http://wiki.blender.org/index.php/Doc:2.6/Manual"
        layout.operator("wm.url_open", text="Release Log", icon='URL').url = "http://wiki.blender.org/index.php/Dev:Ref/Release_Notes/2.70"
        layout.separator()

        layout.operator("wm.url_open", text="Blender Website", icon='URL').url = "http://www.blender.org"
        layout.operator("wm.url_open", text="Blender e-Shop", icon='URL').url = "http://www.blender.org/e-shop"
        layout.operator("wm.url_open", text="Developer Community", icon='URL').url = "http://www.blender.org/get-involved/"
        layout.operator("wm.url_open", text="User Community", icon='URL').url = "http://www.blender.org/community/user-community"
        layout.separator()
        layout.operator("wm.url_open", text="Report a Bug", icon='URL').url = "http://developer.blender.org/maniphest/task/create/?project=2&type=Bug"
        layout.separator()

        layout.operator("wm.url_open", text="Python API Reference", icon='URL').url = bpy.types.WM_OT_doc_view._prefix
        layout.operator("wm.operator_cheat_sheet", icon='TEXT')
        layout.operator("wm.sysinfo", icon='TEXT')
        layout.separator()
        layout.operator("logic.texface_convert", text="TexFace to Material Convert", icon='GAME')
        layout.separator()

        layout.operator("wm.splash", icon='BLENDER')

if __name__ == "__main__":  # only for live edit.
    bpy.utils.register_module(__name__)
