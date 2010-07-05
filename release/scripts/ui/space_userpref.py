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
import os
import shutil


def ui_items_general(col, context):
    """ General UI Theme Settings (User Interface)
    """

    row = col.row()

    subsplit = row.split(percentage=0.95)

    padding = subsplit.split(percentage=0.15)
    colsub = padding.column()
    colsub = padding.column()
    colsub.row().prop(context, "outline")
    colsub.row().prop(context, "item", slider=True)
    colsub.row().prop(context, "inner", slider=True)
    colsub.row().prop(context, "inner_sel", slider=True)

    subsplit = row.split(percentage=0.85)

    padding = subsplit.split(percentage=0.15)
    colsub = padding.column()
    colsub = padding.column()
    colsub.row().prop(context, "text")
    colsub.row().prop(context, "text_sel")
    colsub.prop(context, "shaded")
    subsub = colsub.column(align=True)
    subsub.active = context.shaded
    subsub.prop(context, "shadetop")
    subsub.prop(context, "shadedown")

    col.separator()


def opengl_lamp_buttons(column, lamp):
    split = column.split(percentage=0.1)

    if lamp.enabled == True:
        split.prop(lamp, "enabled", text="", icon='OUTLINER_OB_LAMP')
    else:
        split.prop(lamp, "enabled", text="", icon='LAMP_DATA')

    col = split.column()
    col.active = lamp.enabled
    row = col.row()
    row.label(text="Diffuse:")
    row.prop(lamp, "diffuse_color", text="")
    row = col.row()
    row.label(text="Specular:")
    row.prop(lamp, "specular_color", text="")

    col = split.column()
    col.active = lamp.enabled
    col.prop(lamp, "direction", text="")


class USERPREF_HT_header(bpy.types.Header):
    bl_space_type = 'USER_PREFERENCES'

    def draw(self, context):
        layout = self.layout
        layout.template_header(menus=False)

        userpref = context.user_preferences

        layout.operator_context = 'EXEC_AREA'
        layout.operator("wm.save_homefile", text="Save As Default")

        layout.operator_context = 'INVOKE_DEFAULT'

        if userpref.active_section == 'INPUT':
            op = layout.operator("wm.keyconfig_export")
            op.filepath = "keymap.py"
            op = layout.operator("wm.keyconfig_import")
            op.filepath = "keymap.py"
        elif userpref.active_section == 'ADDONS':
            op = layout.operator("wm.addon_install")
            op.filepath = "*.py"
        elif userpref.active_section == 'THEMES':
            op = layout.operator("ui.reset_default_theme")


class USERPREF_PT_tabs(bpy.types.Panel):
    bl_label = ""
    bl_space_type = 'USER_PREFERENCES'
    bl_region_type = 'WINDOW'
    bl_show_header = False

    def draw(self, context):
        layout = self.layout

        userpref = context.user_preferences

        layout.prop(userpref, "active_section", expand=True)


class USERPREF_MT_interaction_presets(bpy.types.Menu):
    bl_label = "Presets"
    preset_subdir = "interaction"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class USERPREF_MT_splash(bpy.types.Menu):
    bl_label = "Splash"

    def draw(self, context):
        layout = self.layout
        split = layout.split()
        row = split.row()
        row.label("")
        row = split.row()
        row.label("Interaction:")
        row.menu("USERPREF_MT_interaction_presets", text=bpy.types.USERPREF_MT_interaction_presets.bl_label)


class USERPREF_PT_interface(bpy.types.Panel):
    bl_space_type = 'USER_PREFERENCES'
    bl_label = "Interface"
    bl_region_type = 'WINDOW'
    bl_show_header = False

    def poll(self, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'INTERFACE')

    def draw(self, context):
        layout = self.layout

        userpref = context.user_preferences
        view = userpref.view

        row = layout.row()

        col = row.column()
        col.label(text="Display:")
        col.prop(view, "tooltips")
        col.prop(view, "display_object_info", text="Object Info")
        col.prop(view, "use_large_cursors")
        col.prop(view, "show_view_name", text="View Name")
        col.prop(view, "show_playback_fps", text="Playback FPS")
        col.prop(view, "global_scene")
        col.prop(view, "pin_floating_panels")
        col.prop(view, "object_origin_size")

        col.separator()
        col.separator()
        col.separator()

        col.prop(view, "show_mini_axis", text="Display Mini Axis")
        sub = col.column()
        sub.enabled = view.show_mini_axis
        sub.prop(view, "mini_axis_size", text="Size")
        sub.prop(view, "mini_axis_brightness", text="Brightness")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="Properties Window:")
        col.prop(view, "properties_width_check")

        row.separator()
        row.separator()

        col = row.column()
        col.label(text="View Manipulation:")
        col.prop(view, "auto_depth")
        col.prop(view, "zoom_to_mouse")
        col.prop(view, "rotate_around_selection")
        col.prop(view, "global_pivot")

        col.separator()

        col.prop(view, "auto_perspective")
        col.prop(view, "smooth_view")
        col.prop(view, "rotation_angle")

        col.separator()
        col.separator()

        col.label(text="2D Viewports:")
        col.prop(view, "view2d_grid_minimum_spacing", text="Minimum Grid Spacing")
        col.prop(view, "timecode_style")

        row.separator()
        row.separator()

        col = row.column()
        #Toolbox doesn't exist yet
        #col.label(text="Toolbox:")
        #col.prop(view, "use_column_layout")
        #col.label(text="Open Toolbox Delay:")
        #col.prop(view, "open_left_mouse_delay", text="Hold LMB")
        #col.prop(view, "open_right_mouse_delay", text="Hold RMB")
        col.prop(view, "use_manipulator")
        sub = col.column()
        sub.enabled = view.use_manipulator
        sub.prop(view, "manipulator_size", text="Size")
        sub.prop(view, "manipulator_handle_size", text="Handle Size")
        sub.prop(view, "manipulator_hotspot", text="Hotspot")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="Menus:")
        col.prop(view, "open_mouse_over")
        col.label(text="Menu Open Delay:")
        col.prop(view, "open_toplevel_delay", text="Top Level")
        col.prop(view, "open_sublevel_delay", text="Sub Level")

        col.separator()

        col.prop(view, "show_splash")


class USERPREF_PT_edit(bpy.types.Panel):
    bl_space_type = 'USER_PREFERENCES'
    bl_label = "Edit"
    bl_region_type = 'WINDOW'
    bl_show_header = False

    def poll(self, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'EDITING')

    def draw(self, context):
        layout = self.layout

        userpref = context.user_preferences
        edit = userpref.edit

        row = layout.row()

        col = row.column()
        col.label(text="Link Materials To:")
        col.prop(edit, "material_link", text="")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="New Objects:")
        col.prop(edit, "enter_edit_mode")
        col.label(text="Align To:")
        col.prop(edit, "object_align", text="")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="Undo:")
        col.prop(edit, "global_undo")
        col.prop(edit, "undo_steps", text="Steps")
        col.prop(edit, "undo_memory_limit", text="Memory Limit")

        row.separator()
        row.separator()

        col = row.column()
        col.label(text="Snap:")
        col.prop(edit, "snap_translate", text="Translate")
        col.prop(edit, "snap_rotate", text="Rotate")
        col.prop(edit, "snap_scale", text="Scale")
        col.separator()
        col.separator()
        col.separator()
        col.label(text="Grease Pencil:")
        col.prop(edit, "grease_pencil_manhattan_distance", text="Manhattan Distance")
        col.prop(edit, "grease_pencil_euclidean_distance", text="Euclidean Distance")
        #col.prop(edit, "grease_pencil_simplify_stroke", text="Simplify Stroke")
        col.prop(edit, "grease_pencil_eraser_radius", text="Eraser Radius")
        col.prop(edit, "grease_pencil_smooth_stroke", text="Smooth Stroke")
        col.separator()
        col.separator()
        col.separator()
        col.label(text="Playback:")
        col.prop(edit, "use_negative_frames")

        row.separator()
        row.separator()

        col = row.column()
        col.label(text="Keyframing:")
        col.prop(edit, "use_visual_keying")
        col.prop(edit, "keyframe_insert_needed", text="Only Insert Needed")

        col.separator()

        col.prop(edit, "use_auto_keying", text="Auto Keyframing:")

        sub = col.column()

        # sub.active = edit.use_auto_keying # incorrect, timeline can enable
        sub.prop(edit, "auto_keyframe_insert_keyingset", text="Only Insert for Keying Set")
        sub.prop(edit, "auto_keyframe_insert_available", text="Only Insert Available")

        col.separator()

        col.label(text="New F-Curve Defaults:")
        col.prop(edit, "keyframe_new_interpolation_type", text="Interpolation")
        col.prop(edit, "keyframe_new_handle_type", text="Handles")
        col.prop(edit, "insertkey_xyz_to_rgb", text="XYZ to RGB")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="Transform:")
        col.prop(edit, "drag_immediately")

        row.separator()
        row.separator()

        col = row.column()
        col.label(text="Duplicate Data:")
        col.prop(edit, "duplicate_mesh", text="Mesh")
        col.prop(edit, "duplicate_surface", text="Surface")
        col.prop(edit, "duplicate_curve", text="Curve")
        col.prop(edit, "duplicate_text", text="Text")
        col.prop(edit, "duplicate_metaball", text="Metaball")
        col.prop(edit, "duplicate_armature", text="Armature")
        col.prop(edit, "duplicate_lamp", text="Lamp")
        col.prop(edit, "duplicate_material", text="Material")
        col.prop(edit, "duplicate_texture", text="Texture")
        col.prop(edit, "duplicate_fcurve", text="F-Curve")
        col.prop(edit, "duplicate_action", text="Action")
        col.prop(edit, "duplicate_particle", text="Particle")


class USERPREF_PT_system(bpy.types.Panel):
    bl_space_type = 'USER_PREFERENCES'
    bl_label = "System"
    bl_region_type = 'WINDOW'
    bl_show_header = False

    def poll(self, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'SYSTEM')

    def draw(self, context):
        layout = self.layout

        userpref = context.user_preferences
        system = userpref.system

        split = layout.split()


        # 1. Column
        column = split.column()
        colsplit = column.split(percentage=0.85)

        col = colsplit.column()
        col.label(text="General:")
        col.prop(system, "dpi")
        col.prop(system, "frame_server_port")
        col.prop(system, "scrollback", text="Console Scrollback")
        col.prop(system, "auto_execute_scripts")
        col.prop(system, "tabs_as_spaces")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="Sound:")
        col.row().prop(system, "audio_device", expand=True)
        sub = col.column()
        sub.active = system.audio_device != 'NONE'
        #sub.prop(system, "enable_all_codecs")
        sub.prop(system, "audio_channels", text="Channels")
        sub.prop(system, "audio_mixing_buffer", text="Mixing Buffer")
        sub.prop(system, "audio_sample_rate", text="Sample Rate")
        sub.prop(system, "audio_sample_format", text="Sample Format")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="Screencast:")
        col.prop(system, "screencast_fps")
        col.prop(system, "screencast_wait_time")
        col.separator()
        col.separator()
        col.separator()

        #column = split.column()
        #colsplit = column.split(percentage=0.85)

        # No translation in 2.5 yet
        #col.prop(system, "language")
        #col.label(text="Translate:")
        #col.prop(system, "translate_tooltips", text="Tooltips")
        #col.prop(system, "translate_buttons", text="Labels")
        #col.prop(system, "translate_toolbox", text="Toolbox")

        #col.separator()

        #col.prop(system, "use_textured_fonts")


        # 2. Column
        column = split.column()
        colsplit = column.split(percentage=0.85)

        col = colsplit.column()
        col.label(text="OpenGL:")
        col.prop(system, "clip_alpha", slider=True)
        col.prop(system, "use_mipmaps")
        col.prop(system, "use_vbos")
        #Anti-aliasing is disabled as it breaks broder/lasso select
        #col.prop(system, "use_antialiasing")
        col.label(text="Window Draw Method:")
        col.prop(system, "window_draw_method", text="")
        col.label(text="Textures:")
        col.prop(system, "gl_texture_limit", text="Limit Size")
        col.prop(system, "texture_time_out", text="Time Out")
        col.prop(system, "texture_collection_rate", text="Collection Rate")

        col.separator()
        col.separator()
        col.separator()

        col.label(text="Sequencer:")
        col.prop(system, "prefetch_frames")
        col.prop(system, "memory_cache_limit")


        # 3. Column
        column = split.column()

        column.label(text="Solid OpenGL lights:")

        split = column.split(percentage=0.1)
        split.label()
        split.label(text="Colors:")
        split.label(text="Direction:")

        lamp = system.solid_lights[0]
        opengl_lamp_buttons(column, lamp)

        lamp = system.solid_lights[1]
        opengl_lamp_buttons(column, lamp)

        lamp = system.solid_lights[2]
        opengl_lamp_buttons(column, lamp)

        column.separator()
        column.separator()
        column.separator()

        column.label(text="Color Picker Type:")
        column.row().prop(system, "color_picker_type", text="")

        column.separator()
        column.separator()
        column.separator()

        column.prop(system, "use_weight_color_range", text="Custom Weight Paint Range")
        sub = column.column()
        sub.active = system.use_weight_color_range
        sub.template_color_ramp(system, "weight_color_range", expand=True)


class USERPREF_PT_theme(bpy.types.Panel):
    bl_space_type = 'USER_PREFERENCES'
    bl_label = "Themes"
    bl_region_type = 'WINDOW'
    bl_show_header = False

    @staticmethod
    def _theme_generic(split, themedata):

        row = split.row()

        subsplit = row.split(percentage=0.95)

        padding1 = subsplit.split(percentage=0.15)
        padding1.column()

        subsplit = row.split(percentage=0.85)

        padding2 = subsplit.split(percentage=0.15)
        padding2.column()

        colsub_pair = padding1.column(), padding2.column()

        props_type = {}

        for i, prop in enumerate(themedata.rna_type.properties):
            attr = prop.identifier
            if attr == "rna_type":
                continue

            props_type.setdefault((prop.type, prop.subtype), []).append(prop.identifier)

        for props_type, props_ls in sorted(props_type.items()):
            for i, attr in enumerate(props_ls):
                colsub_pair[i % 2].row().prop(themedata, attr)

    def poll(self, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'THEMES')

    def draw(self, context):
        layout = self.layout

        theme = context.user_preferences.themes[0]

        split_themes = layout.split(percentage=0.2)
        split_themes.prop(theme, "theme_area", expand=True)

        split = layout.split(percentage=0.4)


        layout.separator()
        layout.separator()

        split = split_themes.split()

        if theme.theme_area == 'USER_INTERFACE':
            col = split.column()

            ui = theme.user_interface.wcol_regular
            col.label(text="Regular:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_tool
            col.label(text="Tool:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_radio
            col.label(text="Radio Buttons:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_text
            col.label(text="Text:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_option
            col.label(text="Option:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_toggle
            col.label(text="Toggle:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_num
            col.label(text="Number Field:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_numslider
            col.label(text="Value Slider:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_box
            col.label(text="Box:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_menu
            col.label(text="Menu:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_pulldown
            col.label(text="Pulldown:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_menu_back
            col.label(text="Menu Back:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_menu_item
            col.label(text="Menu Item:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_scroll
            col.label(text="Scroll Bar:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_progress
            col.label(text="Progress Bar:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_list_item
            col.label(text="List Item:")
            ui_items_general(col, ui)

            ui = theme.user_interface.wcol_state
            col.label(text="State:")

            row = col.row()

            subsplit = row.split(percentage=0.95)

            padding = subsplit.split(percentage=0.15)
            colsub = padding.column()
            colsub = padding.column()
            colsub.row().prop(ui, "inner_anim")
            colsub.row().prop(ui, "inner_anim_sel")
            colsub.row().prop(ui, "inner_driven")
            colsub.row().prop(ui, "inner_driven_sel")

            subsplit = row.split(percentage=0.85)

            padding = subsplit.split(percentage=0.15)
            colsub = padding.column()
            colsub = padding.column()
            colsub.row().prop(ui, "inner_key")
            colsub.row().prop(ui, "inner_key_sel")
            colsub.row().prop(ui, "blend")


            ui = theme.user_interface
            col.separator()
            col.separator()

            split = col.split(percentage=0.93)
            split.prop(ui, "icon_file")

            layout.separator()
            layout.separator()

        else:
            self._theme_generic(split, getattr(theme, theme.theme_area.lower()))


class USERPREF_PT_file(bpy.types.Panel):
    bl_space_type = 'USER_PREFERENCES'
    bl_label = "Files"
    bl_region_type = 'WINDOW'
    bl_show_header = False

    def poll(self, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'FILES')

    def draw(self, context):
        layout = self.layout

        userpref = context.user_preferences
        paths = userpref.filepaths

        split = layout.split(percentage=0.7)

        col = split.column()
        col.label(text="File Paths:")

        colsplit = col.split(percentage=0.95)
        col1 = colsplit.split(percentage=0.3)

        sub = col1.column()
        sub.label(text="Fonts:")
        sub.label(text="Textures:")
        sub.label(text="Texture Plugins:")
        sub.label(text="Sequence Plugins:")
        sub.label(text="Render Output:")
        sub.label(text="Scripts:")
        sub.label(text="Sounds:")
        sub.label(text="Temp:")
        sub.label(text="Image Editor:")
        sub.label(text="Animation Player:")

        sub = col1.column()
        sub.prop(paths, "fonts_directory", text="")
        sub.prop(paths, "textures_directory", text="")
        sub.prop(paths, "texture_plugin_directory", text="")
        sub.prop(paths, "sequence_plugin_directory", text="")
        sub.prop(paths, "render_output_directory", text="")
        sub.prop(paths, "python_scripts_directory", text="")
        sub.prop(paths, "sounds_directory", text="")
        sub.prop(paths, "temporary_directory", text="")
        sub.prop(paths, "image_editor", text="")
        subsplit = sub.split(percentage=0.3)
        subsplit.prop(paths, "animation_player_preset", text="")
        subsplit.prop(paths, "animation_player", text="")

        col = split.column()
        col.label(text="Save & Load:")
        col.prop(paths, "use_relative_paths")
        col.prop(paths, "compress_file")
        col.prop(paths, "load_ui")
        col.prop(paths, "filter_file_extensions")
        col.prop(paths, "hide_dot_files_datablocks")

        col.separator()
        col.separator()

        col.label(text="Auto Save:")
        col.prop(paths, "save_version")
        col.prop(paths, "recent_files")
        col.prop(paths, "save_preview_images")
        col.prop(paths, "auto_save_temporary_files")
        sub = col.column()
        sub.enabled = paths.auto_save_temporary_files
        sub.prop(paths, "auto_save_time", text="Timer (mins)")

from space_userpref_keymap import InputKeyMapPanel


class USERPREF_PT_input(InputKeyMapPanel):
    bl_space_type = 'USER_PREFERENCES'
    bl_label = "Input"

    def poll(self, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'INPUT')

    def draw_input_prefs(self, inputs, layout):
        # General settings
        row = layout.row()
        col = row.column()

        sub = col.column()
        sub.label(text="Presets:")
        subrow = sub.row(align=True)
        subrow.menu("USERPREF_MT_interaction_presets", text=bpy.types.USERPREF_MT_interaction_presets.bl_label)
        subrow.operator("wm.interaction_preset_add", text="", icon='ZOOMIN')
        sub.separator()

        sub.label(text="Mouse:")
        sub1 = sub.column()
        sub1.enabled = (inputs.select_mouse == 'RIGHT')
        sub1.prop(inputs, "emulate_3_button_mouse")
        sub.prop(inputs, "continuous_mouse")

        sub.label(text="Select With:")
        sub.row().prop(inputs, "select_mouse", expand=True)

        sub = col.column()
        sub.label(text="Double Click:")
        sub.prop(inputs, "double_click_time", text="Speed")

        sub.separator()

        sub.prop(inputs, "emulate_numpad")

        sub.separator()

        sub.label(text="Orbit Style:")
        sub.row().prop(inputs, "view_rotation", expand=True)

        sub.label(text="Zoom Style:")
        sub.row().prop(inputs, "zoom_style", text="")
        if inputs.zoom_style == 'DOLLY':
            sub.row().prop(inputs, "zoom_axis", expand=True)
            sub.prop(inputs, "invert_zoom_direction")

        #sub.prop(inputs, "use_middle_mouse_paste")

        #col.separator()

        #sub = col.column()
        #sub.label(text="Mouse Wheel:")
        #sub.prop(view, "wheel_scroll_lines", text="Scroll Lines")

        col.separator()
        ''' not implemented yet
        sub = col.column()
        sub.label(text="NDOF Device:")
        sub.prop(inputs, "ndof_pan_speed", text="Pan Speed")
        sub.prop(inputs, "ndof_rotate_speed", text="Orbit Speed")
        '''

        row.separator()

    def draw(self, context):
        layout = self.layout

        #import time

        #start = time.time()

        userpref = context.user_preferences
        wm = context.manager

        inputs = userpref.inputs

        split = layout.split(percentage=0.25)

        # Input settings
        self.draw_input_prefs(inputs, split)

        # Keymap Settings
        self.draw_keymaps(context, split)

        #print("runtime", time.time() - start)


class USERPREF_PT_addons(bpy.types.Panel):
    bl_space_type = 'USER_PREFERENCES'
    bl_label = "Addons"
    bl_region_type = 'WINDOW'
    bl_show_header = False

    def poll(self, context):
        userpref = context.user_preferences
        return (userpref.active_section == 'ADDONS')

    @staticmethod
    def _addon_list():
        import sys
        modules = []
        loaded_modules = set()
        paths = bpy.utils.script_paths("addons")
        # sys.path.insert(0, None)
        for path in paths:
            # sys.path[0] = path
            modules.extend(bpy.utils.modules_from_path(path, loaded_modules))

        # del sys.path[0]
        return modules

    def draw(self, context):
        layout = self.layout

        userpref = context.user_preferences
        used_ext = {ext.module for ext in userpref.addons}

        # collect the categories that can be filtered on
        addons = [(mod, addon_info_get(mod)) for mod in self._addon_list()]

        cats = {info["category"] for mod, info in addons}
        cats.discard("")

        cats = ["All", "Enabled", "Disabled"] + sorted(cats)

        bpy.types.Scene.EnumProperty(items=[(cat, cat, str(i)) for i, cat in enumerate(cats)],
            name="Category", attr="addon_filter", description="Filter add-ons by category")
        bpy.types.Scene.StringProperty(name="Search", attr="addon_search",
            description="Search within the selected filter")

        split = layout.split(percentage=0.2)
        col = split.column()
        col.prop(context.scene, "addon_filter", text="Filter", expand=True)
        col.prop(context.scene, "addon_search", text="", icon='VIEWZOOM')

        col = split.column()

        filter = context.scene.addon_filter
        search = context.scene.addon_search.lower()

        for mod, info in addons:
            module_name = mod.__name__

            is_enabled = module_name in used_ext

            # check if add-on should be visible with current filters
            if (filter == "All") or \
                    (filter == info["category"]) or \
                    (filter == "Enabled" and is_enabled) or \
                    (filter == "Disabled" and not is_enabled):


                if search and search not in info["name"].lower():
                    if info["author"]:
                        if search not in info["author"].lower():
                            continue
                    else:
                        continue

                # Addon UI Code
                box = col.column().box()
                colsub = box.column()
                row = colsub.row()

                row.operator("wm.addon_expand", icon='TRIA_DOWN' if info["expanded"] else 'TRIA_RIGHT', emboss=False).module = module_name

                rowsub = row.row()
                rowsub.active = is_enabled
                rowsub.label(text=info["name"], icon='ERROR' if info["warning"] else 'BLENDER')

                if is_enabled:
                    row.operator("wm.addon_disable", icon='CHECKBOX_HLT', text="", emboss=False).module = module_name
                else:
                    row.operator("wm.addon_enable", icon='CHECKBOX_DEHLT', text="", emboss=False).module = module_name

                # Expanded UI (only if additional infos are available)
                if info["expanded"]:
                    if info["description"]:
                        split = colsub.row().split(percentage=0.15)
                        split.label(text='Description:')
                        split.label(text=info["description"])
                    if info["location"]:
                        split = colsub.row().split(percentage=0.15)
                        split.label(text='Location:')
                        split.label(text=info["location"])
                    if info["author"]:
                        split = colsub.row().split(percentage=0.15)
                        split.label(text='Author:')
                        split.label(text=info["author"])
                    if info["version"]:
                        split = colsub.row().split(percentage=0.15)
                        split.label(text='Version:')
                        split.label(text=info["version"])
                    if info["warning"]:
                        split = colsub.row().split(percentage=0.15)
                        split.label(text="Warning:")
                        split.label(text='  ' + info["warning"], icon='ERROR')
                    if info["wiki_url"] or info["tracker_url"]:
                        split = colsub.row().split(percentage=0.15)
                        split.label(text="Internet:")
                        if info["wiki_url"]:
                            split.operator("wm.url_open", text="Link to the Wiki", icon='HELP').url = info["wiki_url"]
                        if info["tracker_url"]:
                            split.operator("wm.url_open", text="Report a Bug", icon='URL').url = info["tracker_url"]

                        if info["wiki_url"] and info["tracker_url"]:
                            split.separator()
                        else:
                            split.separator()
                            split.separator()

        # Append missing scripts
        # First collect scripts that are used but have no script file.
        module_names = {mod.__name__ for mod, info in addons}
        missing_modules = {ext for ext in used_ext if ext not in module_names}

        if missing_modules and filter in ("All", "Enabled"):
            col.column().separator()
            col.column().label(text="Missing script files")

            module_names = {mod.__name__ for mod, info in addons}
            for ext in sorted(missing_modules):
                # Addon UI Code
                box = col.column().box()
                colsub = box.column()
                row = colsub.row()

                row.label(text=ext, icon='ERROR')
                row.operator("wm.addon_disable").module = ext

from bpy.props import *


def addon_info_get(mod, info_basis={"name": "", "author": "", "version": "", "blender": "", "location": "", "description": "", "wiki_url": "", "tracker_url": "", "category": "", "warning": "", "expanded": False}):
    addon_info = getattr(mod, "bl_addon_info", {})

    # avoid re-initializing
    if "_init" in addon_info:
        return addon_info

    if not addon_info:
        mod.bl_addon_info = addon_info

    for key, value in info_basis.items():
        addon_info.setdefault(key, value)

    if not addon_info["name"]:
        addon_info["name"] = mod.__name__

    addon_info["_init"] = None
    return addon_info


class WM_OT_addon_enable(bpy.types.Operator):
    "Enable an addon"
    bl_idname = "wm.addon_enable"
    bl_label = "Enable Add-On"

    module = StringProperty(name="Module", description="Module name of the addon to enable")

    def execute(self, context):
        module_name = self.properties.module

        try:
            mod = __import__(module_name)
            mod.register()
        except:
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

        ext = context.user_preferences.addons.new()
        ext.module = module_name

        # check if add-on is written for current blender version, or raise a warning
        info = addon_info_get(mod)

        if info.get("blender", (0, 0, 0)) > bpy.app.version:
            self.report("WARNING','This script was written for a newer version of Blender and might not function (correctly).\nThe script is enabled though.")

        return {'FINISHED'}


class WM_OT_addon_disable(bpy.types.Operator):
    "Disable an addon"
    bl_idname = "wm.addon_disable"
    bl_label = "Disable Add-On"

    module = StringProperty(name="Module", description="Module name of the addon to disable")

    def execute(self, context):
        import traceback
        module_name = self.properties.module

        try:
            mod = __import__(module_name)
            mod.unregister()
        except:
            traceback.print_exc()

        addons = context.user_preferences.addons
        ok = True
        while ok: # incase its in more then once.
            ok = False
            for ext in addons:
                if ext.module == module_name:
                    addons.remove(ext)
                    ok = True
                    break

        return {'FINISHED'}


class WM_OT_addon_install(bpy.types.Operator):
    "Install an addon"
    bl_idname = "wm.addon_install"
    bl_label = "Install Add-On..."

    module = StringProperty(name="Module", description="Module name of the addon to disable")

    filepath = StringProperty(name="File Path", description="File path to write file to")
    filter_folder = BoolProperty(name="Filter folders", description="", default=True, options={'HIDDEN'})
    filter_python = BoolProperty(name="Filter python", description="", default=True, options={'HIDDEN'})

    def execute(self, context):
        import traceback
        import zipfile
        pyfile = self.properties.filepath

        path_addons = bpy.utils.script_paths("addons")[-1]

        #check to see if the file is in compressed format (.zip)
        if zipfile.is_zipfile(pyfile):
            try:
                file_to_extract = zipfile.ZipFile(pyfile, 'r')

                #extract the file to "addons"
                file_to_extract.extractall(path_addons)

            except:
                traceback.print_exc()
                return {'CANCELLED'}

        else:
            path_dest = os.path.join(path_addons, os.path.basename(pyfile))

            if os.path.exists(path_dest):
                self.report({'WARNING'}, "File already installed to '%s'\n" % path_dest)
                return {'CANCELLED'}

            #if not compressed file just copy into the addon path
            try:
                shutil.copyfile(pyfile, path_dest)

            except:
                traceback.print_exc()
                return {'CANCELLED'}

        # TODO, should not be a warning.
        # self.report({'WARNING'}, "File installed to '%s'\n" % path_dest)
        return {'FINISHED'}

    def invoke(self, context, event):
        paths = bpy.utils.script_paths("addons")
        if not paths:
            self.report({'ERROR'}, "No 'addons' path could be found in " + str(bpy.utils.script_paths()))
            return {'CANCELLED'}

        wm = context.manager
        wm.add_fileselect(self)
        return {'RUNNING_MODAL'}


class WM_OT_addon_expand(bpy.types.Operator):
    "Display more information on this add-on"
    bl_idname = "wm.addon_expand"
    bl_label = ""

    module = StringProperty(name="Module", description="Module name of the addon to expand")

    def execute(self, context):
        module_name = self.properties.module

        # unlikely to fail, module should have alredy been imported
        try:
            mod = __import__(module_name)
        except:
            import traceback
            traceback.print_exc()
            return {'CANCELLED'}

        info = addon_info_get(mod)
        info["expanded"] = not info["expanded"]
        return {'FINISHED'}


classes = [
    USERPREF_HT_header,
    USERPREF_PT_tabs,
    USERPREF_PT_interface,
    USERPREF_PT_theme,
    USERPREF_PT_edit,
    USERPREF_PT_system,
    USERPREF_PT_file,
    USERPREF_PT_input,
    USERPREF_PT_addons,

    USERPREF_MT_interaction_presets,
    USERPREF_MT_splash,

    WM_OT_addon_enable,
    WM_OT_addon_disable,
    WM_OT_addon_install,
    WM_OT_addon_expand]


def register():
    register = bpy.types.register
    for cls in classes:
        register(cls)


def unregister():
    unregister = bpy.types.unregister
    for cls in classes:
        unregister(cls)

if __name__ == "__main__":
    register()
