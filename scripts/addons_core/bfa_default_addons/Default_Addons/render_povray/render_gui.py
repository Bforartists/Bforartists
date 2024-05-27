# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""User interface for rendering parameters"""


import bpy
from sys import platform  # really import here, as in render.py?

# Or todo: handle this more crossplatform using QTpovray for Linux for instance
# from os.path import isfile
from bl_operators.presets import AddPresetBase
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Menu, Panel


# Example of wrapping every class 'as is'
from bl_ui import properties_output

for member in dir(properties_output):
    subclass = getattr(properties_output, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_output

from bl_ui import properties_freestyle

for member in dir(properties_freestyle):
    subclass = getattr(properties_freestyle, member)
    if hasattr(subclass, "COMPAT_ENGINES") and (
        subclass.bl_space_type != "PROPERTIES" or subclass.bl_context != "render"
    ):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
        # subclass.bl_parent_id = "RENDER_PT_POV_filter"
del properties_freestyle

from bl_ui import properties_view_layer

for member in dir(properties_view_layer):
    subclass = getattr(properties_view_layer, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_view_layer

# Use some of the existing buttons.
# from bl_ui import properties_render

# DEPRECATED#properties_render.RENDER_PT_render.COMPAT_ENGINES.add('POVRAY_RENDER')
# DEPRECATED#properties_render.RENDER_PT_format.COMPAT_ENGINES.add('POVRAY_RENDER')
# properties_render.RENDER_PT_antialiasing.COMPAT_ENGINES.add('POVRAY_RENDER')
# TORECREATE##DEPRECATED#properties_render.RENDER_PT_shading.COMPAT_ENGINES.add('POVRAY_RENDER')
# DEPRECATED#properties_render.RENDER_PT_output.COMPAT_ENGINES.add('POVRAY_RENDER')
# del properties_render


def check_render_freestyle_svg():
    """Test if Freestyle SVG Exporter addon is activated

    This addon is currently used to generate the SVG lines file
    when Freestyle is enabled alongside POV
    """
    return "render_freestyle_svg" in bpy.context.preferences.addons.keys()


class RenderButtonsPanel:
    """Use this class to define buttons from the render tab of
    properties window."""

    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return rd.engine in cls.COMPAT_ENGINES


class RENDER_PT_POV_export_settings(RenderButtonsPanel, Panel):
    """Use this class to define pov ini settings buttons."""

    bl_options = {"DEFAULT_CLOSED"}
    bl_label = "Auto Start"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        scene = context.scene
        if scene.pov.tempfiles_enable:
            self.layout.prop(scene.pov, "tempfiles_enable", text="", icon="AUTO")
        else:
            self.layout.prop(scene.pov, "tempfiles_enable", text="", icon="CONSOLE")

    def draw(self, context):

        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.max_trace_level != 0
        split = layout.split()

        col = split.column()
        col.label(text="Command line options:")
        col.prop(scene.pov, "command_line_switches", text="", icon="RIGHTARROW")
        split = layout.split()

        # layout.active = not scene.pov.tempfiles_enable
        if not scene.pov.tempfiles_enable:
            split.prop(scene.pov, "deletefiles_enable", text="Delete")
            if not platform.startswith("win"):
                split.prop(scene.pov, "sdl_window_enable", text="Show")
            split.prop(scene.pov, "pov_editor", text="Edit")

            col = layout.column()
            col.prop(scene.pov, "scene_name", text="Name")
            col.prop(scene.pov, "scene_path", text="Path to files")
            # col.prop(scene.pov, "scene_path", text="Path to POV-file")
            # col.prop(scene.pov, "renderimage_path", text="Path to image")

            split = layout.split()
            split.prop(scene.pov, "indentation_character", text="Indent")
            if scene.pov.indentation_character == "SPACE":
                split.prop(scene.pov, "indentation_spaces", text="Spaces")

            row = layout.row()
            row.prop(scene.pov, "comments_enable", text="Comments")
            row.prop(scene.pov, "list_lf_enable", text="Line breaks in lists")


class RENDER_PT_POV_render_settings(RenderButtonsPanel, Panel):
    """Use this class to host pov render settings buttons from other sub panels."""

    bl_label = "Global Settings"
    bl_icon = "SETTINGS"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        scene = context.scene
        if scene.pov.global_settings_advanced:
            self.layout.prop(scene.pov, "global_settings_advanced", text="", icon="PREFERENCES")
        else:
            self.layout.prop(scene.pov, "global_settings_advanced", text="", icon="SETTINGS")

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.global_settings_advanced


class RENDER_PT_POV_light_paths(RenderButtonsPanel, Panel):
    """Use this class to define pov's main light ray relative settings buttons."""

    bl_label = "Light Paths Tracing"
    bl_parent_id = "RENDER_PT_POV_render_settings"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        # rd = context.scene.render
        # layout.active = (scene.pov.max_trace_level != 0)
        layout.active = scene.pov.global_settings_advanced
        if scene.pov.use_shadows:
            layout.prop(scene.pov, "use_shadows", icon="COMMUNITY")
        else:
            layout.prop(scene.pov, "use_shadows", icon="USER")
        col = layout.column()
        col.prop(scene.pov, "max_trace_level", text="Ray Depth")
        row = layout.row(align=True)
        row.prop(scene.pov, "adc_bailout")


class RENDER_PT_POV_film(RenderButtonsPanel, Panel):
    """Use this class to define pov film settings buttons."""

    bl_label = "Film"
    bl_parent_id = "RENDER_PT_POV_render_settings"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        povprops = context.scene.pov
        agnosticprops = context.scene.render

        layout.active = povprops.global_settings_advanced
        col = layout.column()
        col.label(text="Background")
        row = layout.row(align=True)
        if agnosticprops.film_transparent:
            row.prop(
                agnosticprops,
                "film_transparent",
                text="Blender alpha",
                icon="NODE_COMPOSITING",
                invert_checkbox=True,
            )
        else:
            row.prop(
                agnosticprops,
                "film_transparent",
                text="POV alpha",
                icon="IMAGE_ALPHA",
                invert_checkbox=True,
            )
            row.prop(povprops, "alpha_mode", text="")
            if povprops.alpha_mode == "SKY":
                row.label(text=" (color only)")
            elif povprops.alpha_mode == "TRANSPARENT":
                row.prop(povprops, "alpha_filter", text="(premultiplied)", slider=True)
            else:
                # povprops.alpha_mode == 'STRAIGHT'
                row.label(text=" (unassociated)")


class RENDER_PT_POV_hues(RenderButtonsPanel, Panel):
    """Use this class to define pov RGB tweaking buttons."""

    bl_label = "Hues"
    bl_parent_id = "RENDER_PT_POV_render_settings"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.global_settings_advanced

        row = layout.row(align=True)
        row.prop(scene.pov, "ambient_light")
        row = layout.row(align=True)
        row.prop(scene.pov, "irid_wavelength")
        row = layout.row(align=True)


class RENDER_PT_POV_pattern_rules(RenderButtonsPanel, Panel):
    """Use this class to change pov sets of texture generating algorithms."""

    bl_label = "Pattern Rules"
    bl_parent_id = "RENDER_PT_POV_render_settings"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.global_settings_advanced

        row = layout.row(align=True)
        row.prop(scene.pov, "number_of_waves")
        row = layout.row(align=True)
        row.prop(scene.pov, "noise_generator")


class RENDER_PT_POV_photons(RenderButtonsPanel, Panel):
    """Use this class to define pov photons buttons."""

    bl_label = "Photons"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    # def draw_header(self, context):
    # self.layout.label(icon='SETTINGS')

    def draw_header(self, context):
        scene = context.scene
        if scene.pov.photon_enable:
            self.layout.prop(scene.pov, "photon_enable", text="", icon="PARTICLES")
        else:
            self.layout.prop(scene.pov, "photon_enable", text="", icon="MOD_PARTICLES")

    def draw(self, context):
        scene = context.scene
        layout = self.layout
        layout.active = scene.pov.photon_enable
        col = layout.column()
        # col.label(text="Global Photons:")
        col.prop(scene.pov, "photon_max_trace_level", text="Photon Depth")

        split = layout.split()

        col = split.column()
        col.prop(scene.pov, "photon_spacing", text="Spacing")
        col.prop(scene.pov, "photon_gather_min")

        col = split.column()
        col.prop(scene.pov, "photon_adc_bailout", text="Photon ADC")
        col.prop(scene.pov, "photon_gather_max")

        box = layout.box()
        box.label(text="Photon Map File:")
        row = box.row()
        row.prop(scene.pov, "photon_map_file_save_load", expand=True)
        if scene.pov.photon_map_file_save_load in {"save"}:
            box.prop(scene.pov, "photon_map_dir")
            box.prop(scene.pov, "photon_map_filename")
        if scene.pov.photon_map_file_save_load in {"load"}:
            box.prop(scene.pov, "photon_map_file")
        # end main photons


def uberpov_only_qmc_til_pov38release(layout):
    col = layout.column()
    col.alignment = "CENTER"
    col.label(text="Stochastic Anti Aliasing is")
    col.label(text="Only Available with UberPOV")
    col.label(text="Feature Set in User Preferences.")
    col.label(text="Using Type 2 (recursive) instead")


def no_qmc_fallbacks(row, scene, layout):
    row.prop(scene.pov, "jitter_enable", text="Jitter")

    split = layout.split()
    col = split.column()
    col.prop(scene.pov, "antialias_depth", text="AA Depth")
    sub = split.column()
    sub.prop(scene.pov, "jitter_amount", text="Jitter Amount")
    sub.enabled = bool(scene.pov.jitter_enable)
    row = layout.row()
    row.prop(scene.pov, "antialias_threshold", text="AA Threshold")
    row.prop(scene.pov, "antialias_gamma", text="AA Gamma")


class RENDER_PT_POV_antialias(RenderButtonsPanel, Panel):
    """Use this class to define pov antialiasing buttons."""

    bl_label = "Anti-Aliasing"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        scene = context.scene
        if prefs.branch_feature_set_povray != "uberpov" and scene.pov.antialias_method == "2":
            self.layout.prop(scene.pov, "antialias_enable", text="", icon="ERROR")
        elif scene.pov.antialias_enable:
            self.layout.prop(scene.pov, "antialias_enable", text="", icon="ANTIALIASED")
        else:
            self.layout.prop(scene.pov, "antialias_enable", text="", icon="ALIASED")

    def draw(self, context):
        prefs = bpy.context.preferences.addons[__package__].preferences
        layout = self.layout
        scene = context.scene

        layout.active = scene.pov.antialias_enable

        row = layout.row()
        row.prop(scene.pov, "antialias_method", text="")

        if prefs.branch_feature_set_povray != "uberpov" and scene.pov.antialias_method == "2":
            uberpov_only_qmc_til_pov38release(layout)
        else:
            no_qmc_fallbacks(row, scene, layout)
        if prefs.branch_feature_set_povray == "uberpov":
            row = layout.row()
            row.prop(scene.pov, "antialias_confidence", text="AA Confidence")
            row.enabled = scene.pov.antialias_method == "2"


class RENDER_PT_POV_radiosity(RenderButtonsPanel, Panel):
    """Use this class to define pov radiosity buttons."""

    bl_label = "Diffuse Radiosity"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw_header(self, context):
        scene = context.scene
        if scene.pov.radio_enable:
            self.layout.prop(scene.pov, "radio_enable", text="", icon="OUTLINER_OB_LIGHTPROBE")
        else:
            self.layout.prop(scene.pov, "radio_enable", text="", icon="LIGHTPROBE_CUBEMAP")

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.radio_enable

        split = layout.split()

        col = split.column()
        col.prop(scene.pov, "radio_count", text="Rays")
        col.prop(scene.pov, "radio_recursion_limit", text="Recursions")

        split.prop(scene.pov, "radio_error_bound", text="Error Bound")

        layout.prop(scene.pov, "radio_display_advanced")

        if scene.pov.radio_display_advanced:
            split = layout.split()

            col = split.column()
            col.prop(scene.pov, "radio_adc_bailout", slider=True)
            col.prop(scene.pov, "radio_minimum_reuse", text="Min Reuse")
            col.prop(scene.pov, "radio_gray_threshold", slider=True)
            col.prop(scene.pov, "radio_pretrace_start", slider=True)
            col.prop(scene.pov, "radio_low_error_factor", slider=True)

            col = split.column()
            col.prop(scene.pov, "radio_brightness")
            col.prop(scene.pov, "radio_maximum_reuse", text="Max Reuse")
            col.prop(scene.pov, "radio_nearest_count")
            col.prop(scene.pov, "radio_pretrace_end", slider=True)

            col = layout.column()
            col.label(text="Estimation Influence:")
            col.prop(scene.pov, "radio_always_sample")
            col.prop(scene.pov, "radio_normal")
            col.prop(scene.pov, "radio_media")
            col.prop(scene.pov, "radio_subsurface")


class RADIOSITY_MT_POV_presets(Menu):
    """Use this class to define pov radiosity presets menu."""

    bl_label = "Radiosity Presets"
    preset_subdir = "pov/radiosity"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class RENDER_OT_POV_radiosity_add_preset(AddPresetBase, Operator):
    """Use this class to define pov radiosity add presets button"""

    """Add a Radiosity Preset"""
    bl_idname = "scene.radiosity_preset_add"
    bl_label = "Add Radiosity Preset"
    preset_menu = "RADIOSITY_MT_POV_presets"

    # variable used for all preset values
    preset_defines = ["scene = bpy.context.scene"]

    # properties to store in the preset
    preset_values = [
        "scene.pov.radio_display_advanced",
        "scene.pov.radio_adc_bailout",
        "scene.pov.radio_always_sample",
        "scene.pov.radio_brightness",
        "scene.pov.radio_count",
        "scene.pov.radio_error_bound",
        "scene.pov.radio_gray_threshold",
        "scene.pov.radio_low_error_factor",
        "scene.pov.radio_media",
        "scene.pov.radio_subsurface",
        "scene.pov.radio_minimum_reuse",
        "scene.pov.radio_maximum_reuse",
        "scene.pov.radio_nearest_count",
        "scene.pov.radio_normal",
        "scene.pov.radio_recursion_limit",
        "scene.pov.radio_pretrace_start",
        "scene.pov.radio_pretrace_end",
    ]

    # where to store the preset
    preset_subdir = "pov/radiosity"


# Draw into an existing panel
def rad_panel_func(self, context):
    """Display radiosity presets rolldown menu"""
    layout = self.layout

    row = layout.row(align=True)
    row.menu(RADIOSITY_MT_POV_presets.__name__, text=RADIOSITY_MT_POV_presets.bl_label)
    row.operator(RENDER_OT_POV_radiosity_add_preset.bl_idname, text="", icon="ADD")
    row.operator(
        RENDER_OT_POV_radiosity_add_preset.bl_idname, text="", icon="REMOVE"
    ).remove_active = True


# ---------------------------------------------------------------- #
# Freestyle
# ---------------------------------------------------------------- #
# import addon_utils
# addon_utils.paths()[0]
# addon_utils.modules()
# mod.bl_info['name'] == 'Freestyle SVG Exporter':
bpy.utils.script_paths(subdir="addons")
# render_freestyle_svg = os.path.join(bpy.utils.script_paths(subdir="addons"), "render_freestyle_svg.py")

render_freestyle_svg = bpy.context.preferences.addons.get("render_freestyle_svg")
# mpath=addon_utils.paths()[0].render_freestyle_svg
# import mpath
# from mpath import render_freestyle_svg #= addon_utils.modules(module_cache=['Freestyle SVG Exporter'])
# from scripts\\addons import render_freestyle_svg
if check_render_freestyle_svg():
    """
    snippetsWIP
    import myscript
    import importlib

    importlib.reload(myscript)
    myscript.main()
    """
    for member in dir(render_freestyle_svg):
        subclass = getattr(render_freestyle_svg, member)
        if hasattr(subclass, "COMPAT_ENGINES"):
            subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
            if subclass.bl_idname == "RENDER_PT_SVGExporterPanel":
                subclass.bl_parent_id = "RENDER_PT_POV_filter"
                subclass.bl_options = {"HIDE_HEADER"}
                # subclass.bl_order = 11
                print(subclass.bl_info)

    # del render_freestyle_svg.RENDER_PT_SVGExporterPanel.bl_parent_id


class RENDER_PT_POV_filter(RenderButtonsPanel, Panel):
    """Use this class to invoke stuff like Freestyle UI."""

    bl_label = "Freestyle"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        with_freestyle = bpy.app.build_options.freestyle
        engine = context.scene.render.engine
        return with_freestyle and engine == "POVRAY_RENDER"

    def draw_header(self, context):

        # scene = context.scene
        rd = context.scene.render
        layout = self.layout

        if rd.use_freestyle:
            layout.prop(rd, "use_freestyle", text="", icon="LINE_DATA")

        else:
            layout.prop(rd, "use_freestyle", text="", icon="MOD_LINEART")

    def draw(self, context):
        rd = context.scene.render
        layout = self.layout
        layout.active = rd.use_freestyle
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        flow = layout.grid_flow(
            row_major=True, columns=0, even_columns=True, even_rows=False, align=True
        )

        flow.prop(rd, "line_thickness_mode", expand=True)

        if rd.line_thickness_mode == "ABSOLUTE":
            flow.prop(rd, "line_thickness")

        # Warning if the Freestyle SVG Exporter addon is not enabled
        if not check_render_freestyle_svg():
            # col = box.column()
            layout.label(text="Please enable Freestyle SVG Exporter addon", icon="INFO")
            # layout.separator()
            layout.operator(
                "preferences.addon_show",
                text="Go to Render: Freestyle SVG Exporter addon",
                icon="PREFERENCES",
            ).module = "render_freestyle_svg"


##class RENDER_PT_povray_baking(RenderButtonsPanel, Panel):
##    bl_label = "Baking"
##    COMPAT_ENGINES = {'POVRAY_RENDER'}
##
##    def draw_header(self, context):
##        scene = context.scene
##
##        self.layout.prop(scene.pov, "baking_enable", text="")
##
##    def draw(self, context):
##        layout = self.layout
##
##        scene = context.scene
##        rd = scene.render
##
##        layout.active = scene.pov.baking_enable


classes = (
    RENDER_PT_POV_export_settings,
    RENDER_PT_POV_render_settings,
    RENDER_PT_POV_light_paths,
    RENDER_PT_POV_film,
    RENDER_PT_POV_hues,
    RENDER_PT_POV_pattern_rules,
    RENDER_PT_POV_photons,
    RENDER_PT_POV_antialias,
    RENDER_PT_POV_radiosity,
    RENDER_PT_POV_filter,
    # RENDER_PT_povray_baking,
    RADIOSITY_MT_POV_presets,
    RENDER_OT_POV_radiosity_add_preset,
)


def register():
    for cls in classes:
        register_class(cls)
    RENDER_PT_POV_radiosity.prepend(rad_panel_func)


def unregister():
    RENDER_PT_POV_radiosity.remove(rad_panel_func)
    for cls in reversed(classes):
        unregister_class(cls)
