# SPDX-FileCopyrightText: 2021-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

""""User interface for shaders exported to POV textures."""

import bpy
from bpy.utils import register_class, unregister_class
from bpy.types import Operator, Menu, Panel
from bl_operators.presets import AddPresetBase

# Example of wrapping every class 'as is' except some
from bl_ui import properties_material

for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    if hasattr(subclass, "COMPAT_ENGINES"):
        subclass.COMPAT_ENGINES.add("POVRAY_RENDER")
del properties_material

from .shading_properties import check_material


def simple_material(mat):
    """Test if a material uses nodes"""
    return (mat is not None) and (not mat.use_nodes)


class MaterialButtonsPanel:
    """Use this class to define buttons from the material tab of properties window."""

    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        rd = context.scene.render
        return mat and (rd.engine in cls.COMPAT_ENGINES)


class MATERIAL_PT_POV_shading(MaterialButtonsPanel, Panel):
    bl_label = "Shading"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        engine = context.scene.render.engine
        return (
            check_material(mat)
            and (mat.pov.type in {"SURFACE", "WIRE"})
            and (engine in cls.COMPAT_ENGINES)
        )

    def draw(self, context):
        layout = self.layout

        mat = context.material  # FORMERLY : #active_node_mat(context.material)

        if mat.pov.type in {"SURFACE", "WIRE"}:
            split = layout.split()

            col = split.column()
            sub = col.column()
            sub.active = not mat.pov.use_shadeless
            sub.prop(mat.pov, "emit")
            sub.prop(mat.pov, "ambient")
            sub = col.column()
            sub.prop(mat.pov, "translucency")

            col = split.column()
            col.prop(mat.pov, "use_shadeless")
            sub = col.column()
            sub.active = not mat.pov.use_shadeless
            sub.prop(mat.pov, "use_tangent_shading")
            sub.prop(mat.pov, "use_cubic")


class MATERIAL_MT_POV_sss_presets(Menu):
    """Use this class to define pov sss preset menu."""

    bl_label = "SSS Presets"
    preset_subdir = "pov/material/sss"
    preset_operator = "script.execute_preset"
    draw = bpy.types.Menu.draw_preset


class MATERIAL_OT_POV_sss_add_preset(AddPresetBase, Operator):
    """Add an SSS Preset"""

    bl_idname = "material.sss_preset_add"
    bl_label = "Add SSS Preset"
    preset_menu = "MATERIAL_MT_POV_sss_presets"

    # variable used for all preset values
    preset_defines = ["material = bpy.context.material"]

    # properties to store in the preset
    preset_values = [
        "material.pov_subsurface_scattering.radius",
        "material.pov_subsurface_scattering.color",
    ]

    # where to store the preset
    preset_subdir = "pov/material/sss"


class MATERIAL_PT_POV_sss(MaterialButtonsPanel, Panel):
    """Use this class to define pov sss buttons panel."""

    bl_label = "Subsurface Scattering"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        engine = context.scene.render.engine
        return (
            check_material(mat)
            and (mat.pov.type in {"SURFACE", "WIRE"})
            and (engine in cls.COMPAT_ENGINES)
        )

    def draw_header(self, context):
        mat = context.material  # FORMERLY : #active_node_mat(context.material)
        sss = mat.pov_subsurface_scattering

        self.layout.active = not mat.pov.use_shadeless
        self.layout.prop(sss, "use", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material  # FORMERLY : #active_node_mat(context.material)
        sss = mat.pov_subsurface_scattering

        layout.active = sss.use and (not mat.pov.use_shadeless)

        row = layout.row().split()
        sub = row.row(align=True).split(align=True, factor=0.75)
        sub.menu(MATERIAL_MT_POV_sss_presets.__name__, text=MATERIAL_MT_POV_sss_presets.bl_label)
        sub.operator(MATERIAL_OT_POV_sss_add_preset.bl_idname, text="", icon="ADD")
        sub.operator(
            MATERIAL_OT_POV_sss_add_preset.bl_idname, text="", icon="REMOVE"
        ).remove_active = True

        split = layout.split()

        col = split.column()
        col.prop(sss, "ior")
        col.prop(sss, "scale")
        col.prop(sss, "color", text="")
        col.prop(sss, "radius", text="RGB Radius", expand=True)

        col = split.column()
        sub = col.column(align=True)
        sub.label(text="Blend:")
        sub.prop(sss, "color_factor", text="Color")
        sub.prop(sss, "texture_factor", text="Texture")
        sub.label(text="Scattering Weight:")
        sub.prop(sss, "front")
        sub.prop(sss, "back")
        col.separator()
        col.prop(sss, "error_threshold", text="Error")


class MATERIAL_PT_POV_activate_node(MaterialButtonsPanel, Panel):
    """Use this class to define an activate pov nodes button."""

    bl_label = "Activate Node Settings"
    bl_context = "material"
    bl_options = {"HIDE_HEADER"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        mat = context.material
        return (
            mat
            and mat.pov.type == "SURFACE"
            and engine in cls.COMPAT_ENGINES
            and not mat.pov.material_use_nodes
            and not mat.use_nodes
        )

    def draw(self, context):
        layout = self.layout
        # layout.operator("pov.material_use_nodes", icon='SOUND')#'NODETREE')
        # the above replaced with a context hook below:
        layout.operator(
            "WM_OT_context_toggle", text="Use POV-Ray Nodes", icon="NODETREE"
        ).data_path = "material.pov.material_use_nodes"


class MATERIAL_PT_POV_active_node(MaterialButtonsPanel, Panel):
    """Use this class to show pov active node properties buttons."""

    bl_label = "Active Node Settings"
    bl_context = "material"
    bl_options = {"HIDE_HEADER"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        mat = context.material
        return (
            mat
            and mat.pov.type == "SURFACE"
            and (engine in cls.COMPAT_ENGINES)
            and mat.pov.material_use_nodes
        )

    def draw(self, context):
        mat = context.material
        node_tree = mat.node_tree
        if node_tree and mat.use_nodes:
            layout = self.layout
            if node := node_tree.nodes.active:
                layout.prop(mat.pov, "material_active_node")
                layout.context_pointer_set("node", node)
                if hasattr(node, "draw_buttons_ext"):
                    node.draw_buttons_ext(context, layout)
                elif hasattr(node, "draw_buttons"):
                    node.draw_buttons(context, layout)
                if value_inputs := [
                    socket for socket in node.inputs if socket.enabled and not socket.is_linked
                ]:
                    layout.separator()
                    layout.label(text="Inputs:")
                    for socket in value_inputs:
                        row = layout.row()
                        socket.draw(context, row, node, socket.name)
            else:
                layout.label(text="No active nodes!")


class MATERIAL_PT_POV_specular(MaterialButtonsPanel, Panel):
    """Use this class to define standard material specularity (highlights) buttons."""

    bl_label = "Specular"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        engine = context.scene.render.engine
        return (
            check_material(mat)
            and (mat.pov.type in {"SURFACE", "WIRE"})
            and (engine in cls.COMPAT_ENGINES)
        )

    def draw(self, context):
        layout = self.layout

        mat = context.material

        layout.active = not mat.pov.use_shadeless

        split = layout.split()

        col = split.column()
        col.prop(mat, "specular_color", text="")
        col.prop(mat, "specular_intensity", text="Intensity")

        col = split.column()
        col.prop(mat.pov, "specular_shader", text="")
        col.prop(mat.pov, "use_specular_ramp", text="Ramp")

        col = layout.column()
        if mat.pov.specular_shader in {"COOKTORR", "PHONG"}:
            col.prop(mat.pov, "specular_hardness", text="Hardness")
        elif mat.pov.specular_shader == "BLINN":
            row = col.row()
            row.prop(mat.pov, "specular_hardness", text="Hardness")
            row.prop(mat.pov, "specular_ior", text="IOR")
        elif mat.pov.specular_shader == "WARDISO":
            col.prop(mat.pov, "specular_slope", text="Slope")
        elif mat.pov.specular_shader == "TOON":
            row = col.row()
            row.prop(mat.pov, "specular_toon_size", text="Size")
            row.prop(mat.pov, "specular_toon_smooth", text="Smooth")

        if mat.pov.use_specular_ramp:
            layout.separator()
            layout.template_color_ramp(mat.pov, "specular_ramp", expand=True)
            layout.separator()

            row = layout.row()
            row.prop(mat, "specular_ramp_input", text="Input")
            row.prop(mat, "specular_ramp_blend", text="Blend")

            layout.prop(mat, "specular_ramp_factor", text="Factor")


class MATERIAL_PT_POV_mirror(MaterialButtonsPanel, Panel):
    """Use this class to define standard material reflectivity (mirror) buttons."""

    bl_label = "Mirror"
    bl_options = {"DEFAULT_CLOSED"}
    bl_idname = "MATERIAL_PT_POV_raytrace_mirror"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        engine = context.scene.render.engine
        return (
            check_material(mat)
            and (mat.pov.type in {"SURFACE", "WIRE"})
            and (engine in cls.COMPAT_ENGINES)
        )

    def draw_header(self, context):
        mat = context.material
        raym = mat.pov_raytrace_mirror

        self.layout.prop(raym, "use", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material  # Formerly : #mat = active_node_mat(context.material)
        raym = mat.pov_raytrace_mirror

        layout.active = raym.use

        split = layout.split()

        col = split.column()
        col.prop(raym, "reflect_factor")
        col.prop(raym, "mirror_color", text="")

        col = split.column()
        col.prop(raym, "fresnel")
        sub = col.column()
        sub.active = raym.fresnel > 0.0
        sub.prop(raym, "fresnel_factor", text="Blend")

        split = layout.split()

        col = split.column()
        col.separator()
        col.prop(raym, "depth")
        col.prop(raym, "distance", text="Max Dist")
        col.separator()
        sub = col.split(factor=0.4)
        sub.active = raym.distance > 0.0
        sub.label(text="Fade To:")
        sub.prop(raym, "fade_to", text="")

        col = split.column()
        col.label(text="Gloss:")
        col.prop(raym, "gloss_factor", text="Amount")
        sub = col.column()
        sub.active = raym.gloss_factor < 1.0
        sub.prop(raym, "gloss_threshold", text="Threshold")
        sub.prop(raym, "gloss_samples", text="Noise")
        sub.prop(raym, "gloss_anisotropic", text="Anisotropic")


class MATERIAL_PT_POV_transp(MaterialButtonsPanel, Panel):
    """Use this class to define pov material transparency (alpha) buttons."""

    bl_label = "Transparency"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        engine = context.scene.render.engine
        return (
            check_material(mat)
            and (mat.pov.type in {"SURFACE", "WIRE"})
            and (engine in cls.COMPAT_ENGINES)
        )

    def draw_header(self, context):
        mat = context.material

        if simple_material(mat):
            self.layout.prop(mat.pov, "use_transparency", text="")

    def draw(self, context):
        layout = self.layout

        base_mat = context.material
        mat = context.material  # FORMERLY active_node_mat(context.material)
        rayt = mat.pov_raytrace_transparency

        if simple_material(base_mat):
            row = layout.row()
            row.active = mat.pov.use_transparency
            row.prop(mat.pov, "transparency_method", expand=True)

        split = layout.split()
        split.active = base_mat.pov.use_transparency

        col = split.column()
        col.prop(mat.pov, "alpha")
        row = col.row()
        row.active = (base_mat.pov.transparency_method != "MASK") and (not mat.pov.use_shadeless)
        row.prop(mat.pov, "specular_alpha", text="Specular")

        col = split.column()
        col.active = not mat.pov.use_shadeless
        col.prop(rayt, "fresnel")
        sub = col.column()
        sub.active = rayt.fresnel > 0.0
        sub.prop(rayt, "fresnel_factor", text="Blend")

        if base_mat.pov.transparency_method == "RAYTRACE":
            layout.separator()
            split = layout.split()
            split.active = base_mat.pov.use_transparency

            col = split.column()
            col.prop(rayt, "ior")
            col.prop(rayt, "filter")
            col.prop(rayt, "falloff")
            col.prop(rayt, "depth_max")
            col.prop(rayt, "depth")

            col = split.column()
            col.label(text="Gloss:")
            col.prop(rayt, "gloss_factor", text="Amount")
            sub = col.column()
            sub.active = rayt.gloss_factor < 1.0
            sub.prop(rayt, "gloss_threshold", text="Threshold")
            sub.prop(rayt, "gloss_samples", text="Samples")


class MATERIAL_PT_POV_reflection(MaterialButtonsPanel, Panel):
    """Use this class to define more pov specific reflectivity buttons."""

    bl_label = "POV-Ray Reflection"
    bl_parent_id = "MATERIAL_PT_POV_raytrace_mirror"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        mat = context.material
        return (
            mat
            and mat.pov.type == "SURFACE"
            and engine in cls.COMPAT_ENGINES
            and not mat.pov.material_use_nodes
            and not mat.use_nodes
        )

    def draw(self, context):
        layout = self.layout
        mat = context.material
        col = layout.column()
        col.prop(mat.pov, "irid_enable")
        if mat.pov.irid_enable:
            col = layout.column()
            col.prop(mat.pov, "irid_amount", slider=True)
            col.prop(mat.pov, "irid_thickness", slider=True)
            col.prop(mat.pov, "irid_turbulence", slider=True)
        col.prop(mat.pov, "conserve_energy")
        col2 = col.split().column()

        if not mat.pov_raytrace_mirror.use:
            col2.label(text="Please Check Mirror settings :")
        col2.active = mat.pov_raytrace_mirror.use
        col2.prop(mat.pov, "mirror_use_IOR")
        if mat.pov.mirror_use_IOR:
            col2.alignment = "CENTER"
            col2.label(text="The current Raytrace ")
            col2.label(text="Transparency IOR is: " + str(mat.pov_raytrace_transparency.ior))



"""
#group some native Blender (SSS) and POV (Fade)settings under such a parent panel?
class MATERIAL_PT_POV_interior(MaterialButtonsPanel, Panel):
    bl_label = "POV-Ray Interior"
    bl_idname = "material.pov_interior"
    #bl_parent_id = "material.absorption"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        mat=context.material
        return mat and mat.pov.type == "SURFACE"
                    and (engine in cls.COMPAT_ENGINES)
                    and not (mat.pov.material_use_nodes or mat.use_nodes)


    def draw_header(self, context):
        mat = context.material
"""


class MATERIAL_PT_POV_fade_color(MaterialButtonsPanel, Panel):
    """Use this class to define pov fading (absorption) color buttons."""

    bl_label = "POV-Ray Absorption"
    COMPAT_ENGINES = {"POVRAY_RENDER"}
    # bl_parent_id = "material.pov_interior"

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        mat = context.material
        return (
            mat
            and mat.pov.type == "SURFACE"
            and engine in cls.COMPAT_ENGINES
            and not mat.pov.material_use_nodes
            and not mat.use_nodes
        )

    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat.pov, "interior_fade_color", text="")

    def draw(self, context):
        mat = context.material
        if mat.pov.interior_fade_color != (0.0, 0.0, 0.0):
            layout = self.layout
            # layout.active = mat.pov.interior_fade_color
            layout.label(text="Raytrace transparency")
            layout.label(text="depth max Limit needs")
            layout.label(text="to be non zero to fade")


class MATERIAL_PT_POV_caustics(MaterialButtonsPanel, Panel):
    """Use this class to define pov caustics buttons."""

    bl_label = "Caustics"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        mat = context.material
        return (
            mat
            and mat.pov.type == "SURFACE"
            and engine in cls.COMPAT_ENGINES
            and not mat.pov.material_use_nodes
            and not mat.use_nodes
        )

    def draw_header(self, context):
        mat = context.material
        if mat.pov.caustics_enable:
            self.layout.prop(mat.pov, "caustics_enable", text="", icon="PMARKER_SEL")
        else:
            self.layout.prop(mat.pov, "caustics_enable", text="", icon="PMARKER")

    def draw(self, context):

        layout = self.layout

        mat = context.material
        layout.active = mat.pov.caustics_enable
        col = layout.column()
        if mat.pov.caustics_enable:
            col.prop(mat.pov, "refraction_caustics")
            if mat.pov.refraction_caustics:

                col.prop(mat.pov, "refraction_type", text="")

                if mat.pov.refraction_type == "1":
                    col.prop(mat.pov, "fake_caustics_power", slider=True)
                elif mat.pov.refraction_type == "2":
                    col.prop(mat.pov, "photons_dispersion", slider=True)
                    col.prop(mat.pov, "photons_dispersion_samples", slider=True)
            col.prop(mat.pov, "photons_reflection")

            if not mat.pov.refraction_caustics and not mat.pov.photons_reflection:
                col = layout.column()
                col.alignment = "CENTER"
                col.label(text="Caustics override is on, ")
                col.label(text="but you didn't chose any !")


class MATERIAL_PT_strand(MaterialButtonsPanel, Panel):
    """Use this class to define Blender strand antialiasing buttons."""

    bl_label = "Strand"
    bl_options = {"DEFAULT_CLOSED"}
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    @classmethod
    def poll(cls, context):
        mat = context.material
        engine = context.scene.render.engine
        return (
            mat and (mat.pov.type in {"SURFACE", "WIRE", "HALO"}) and (engine in cls.COMPAT_ENGINES)
        )

    def draw(self, context):
        layout = self.layout

        mat = context.material  # don't use node material
        tan = mat.strand

        split = layout.split()

        col = split.column()
        sub = col.column(align=True)
        sub.label(text="Size:")
        sub.prop(tan, "root_size", text="Root")
        sub.prop(tan, "tip_size", text="Tip")
        sub.prop(tan, "size_min", text="Minimum")
        sub.prop(tan, "use_blender_units")
        sub = col.column()
        sub.active = not mat.pov.use_shadeless
        sub.prop(tan, "use_tangent_shading")
        col.prop(tan, "shape")

        col = split.column()
        col.label(text="Shading:")
        col.prop(tan, "width_fade")
        ob = context.object
        if ob and ob.type == "MESH":
            col.prop_search(tan, "uv_layer", ob.data, "uv_layers", text="")
        else:
            col.prop(tan, "uv_layer", text="")
        col.separator()
        sub = col.column()
        sub.active = not mat.pov.use_shadeless
        sub.label(text="Surface diffuse:")
        sub = col.column()
        sub.prop(tan, "blend_distance", text="Distance")


class MATERIAL_PT_POV_replacement_text(MaterialButtonsPanel, Panel):
    """Use this class to define pov custom code declared name field."""

    bl_label = "Custom POV Code"
    COMPAT_ENGINES = {"POVRAY_RENDER"}

    def draw(self, context):
        layout = self.layout
        mat = context.material
        col = layout.column()
        col.alignment = "RIGHT"
        col.label(text="Override properties with this")
        col.label(text="text editor {pov code} block")
        layout.prop(mat.pov, "replacement_text", text="#declare name", icon="SYNTAX_ON")


classes = (
    MATERIAL_PT_POV_shading,
    MATERIAL_PT_POV_sss,
    MATERIAL_MT_POV_sss_presets,
    MATERIAL_OT_POV_sss_add_preset,
    MATERIAL_PT_strand,
    MATERIAL_PT_POV_activate_node,
    MATERIAL_PT_POV_active_node,
    MATERIAL_PT_POV_specular,
    MATERIAL_PT_POV_mirror,
    MATERIAL_PT_POV_transp,
    MATERIAL_PT_POV_reflection,
    # MATERIAL_PT_POV_interior,
    MATERIAL_PT_POV_fade_color,
    MATERIAL_PT_POV_caustics,
    MATERIAL_PT_POV_replacement_text,
)


def register():
    for cls in classes:
        register_class(cls)


def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
