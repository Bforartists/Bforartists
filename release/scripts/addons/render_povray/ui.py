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

# Use some of the existing buttons.
from bl_ui import properties_render
properties_render.RENDER_PT_render.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_dimensions.COMPAT_ENGINES.add('POVRAY_RENDER')
# properties_render.RENDER_PT_antialiasing.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_shading.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_render.RENDER_PT_output.COMPAT_ENGINES.add('POVRAY_RENDER')
del properties_render

# Use only a subset of the world panels
from bl_ui import properties_world
properties_world.WORLD_PT_preview.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_world.WORLD_PT_context_world.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_world.WORLD_PT_world.COMPAT_ENGINES.add('POVRAY_RENDER')
properties_world.WORLD_PT_mist.COMPAT_ENGINES.add('POVRAY_RENDER')
del properties_world

# Example of wrapping every class 'as is'
from bl_ui import properties_material
for member in dir(properties_material):
    subclass = getattr(properties_material, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_material

from bl_ui import properties_data_mesh
for member in dir(properties_data_mesh):
    subclass = getattr(properties_data_mesh, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_data_mesh

from bl_ui import properties_texture
from bl_ui.properties_texture import context_tex_datablock
for member in dir(properties_texture):
    subclass = getattr(properties_texture, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_texture


from bl_ui import properties_data_camera
for member in dir(properties_data_camera):
    subclass = getattr(properties_data_camera, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_data_camera

from bl_ui import properties_data_lamp
for member in dir(properties_data_lamp):
    subclass = getattr(properties_data_lamp, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_data_lamp

from bl_ui import properties_particle as properties_particle
for member in dir(properties_particle):  # add all "particle" panels from blender
    subclass = getattr(properties_particle, member)
    try:
        subclass.COMPAT_ENGINES.add('POVRAY_RENDER')
    except:
        pass
del properties_particle


class RenderButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "render"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        rd = context.scene.render
        return (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)


class MaterialButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        mat = context.material
        rd = context.scene.render
        return mat and (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)


class TextureButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "texture"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        tex = context.texture
        rd = context.scene.render
        return tex and (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)

# class TextureTypePanel(TextureButtonsPanel):

    # @classmethod
    # def poll(cls, context):
        # tex = context.texture
        # engine = context.scene.render.engine
        # return tex and ((tex.type == cls.tex_type and not tex.use_nodes) and (engine in cls.COMPAT_ENGINES))


class ObjectButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        obj = context.object
        rd = context.scene.render
        return obj and (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)


class CameraDataButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        cam = context.camera
        rd = context.scene.render
        return cam and (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)

class WorldButtonsPanel():
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "world"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        wld = context.world
        rd = context.scene.render
        return wld and (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)
        
class TextButtonsPanel():
    bl_space_type = 'TEXT_EDITOR'
    bl_region_type = 'UI'
    bl_label = "POV-Ray"
    # COMPAT_ENGINES must be defined in each subclass, external engines can add themselves here

    @classmethod
    def poll(cls, context):
        text = context.space_data
        rd = context.scene.render
        return text and (rd.use_game_engine is False) and (rd.engine in cls.COMPAT_ENGINES)


class RENDER_PT_povray_export_settings(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Export Settings"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        self.layout.label(icon='CONSOLE')
    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = (scene.pov.max_trace_level != 0)
        split = layout.split()

        col = split.column()
        col.label(text="Command line switches:")
        col.prop(scene.pov, "command_line_switches", text="")
        split = layout.split()
        split.prop(scene.pov, "tempfiles_enable", text="OS Tempfiles")
        split.prop(scene.pov, "pov_editor", text="POV Editor")
        if not scene.pov.tempfiles_enable:
            split.prop(scene.pov, "deletefiles_enable", text="Delete files")

        if not scene.pov.tempfiles_enable:
            col = layout.column()
            col.prop(scene.pov, "scene_name", text="Name")
            col.prop(scene.pov, "scene_path", text="Path to files")
            #col.prop(scene.pov, "scene_path", text="Path to POV-file")
            #col.prop(scene.pov, "renderimage_path", text="Path to image")

            split = layout.split()
            split.prop(scene.pov, "indentation_character", text="Indent")
            if scene.pov.indentation_character == 'SPACE':
                split.prop(scene.pov, "indentation_spaces", text="Spaces")

            row = layout.row()
            row.prop(scene.pov, "comments_enable", text="Comments")
            row.prop(scene.pov, "list_lf_enable", text="Line breaks in lists")


class RENDER_PT_povray_render_settings(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Render Settings"
    bl_icon = 'SETTINGS'
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        self.layout.label(icon='SETTINGS')
    def draw(self, context):
        layout = self.layout

        scene = context.scene
        layout.active = (scene.pov.max_trace_level != 0)

        col = layout.column()

        col.label(text="Global Settings:")
        col.prop(scene.pov, "max_trace_level", text="Ray Depth")

        col.label(text="Global Photons:")
        col.prop(scene.pov, "photon_max_trace_level", text="Photon Depth")

        split = layout.split()

        col = split.column()
        col.prop(scene.pov, "photon_spacing", text="Spacing")
        col.prop(scene.pov, "photon_gather_min")

        col = split.column()
        col.prop(scene.pov, "photon_adc_bailout", text="Photon ADC")
        col.prop(scene.pov, "photon_gather_max")


class RENDER_PT_povray_antialias(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Anti-Aliasing"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.scene
        if bpy.context.user_preferences.addons[__package__].preferences.branch_feature_set_povray != 'uberpov' and scene.pov.antialias_method =='2':
            self.layout.prop(scene.pov, "antialias_enable", text="", icon='ERROR')
        elif scene.pov.antialias_enable:
            self.layout.prop(scene.pov, "antialias_enable", text="", icon='ANTIALIASED')
        else:
            self.layout.prop(scene.pov, "antialias_enable", text="", icon='ALIASED')

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.antialias_enable


        row = layout.row()
        row.prop(scene.pov, "antialias_method", text="")
        if bpy.context.user_preferences.addons[__package__].preferences.branch_feature_set_povray != 'uberpov' and scene.pov.antialias_method =='2':
            col = layout.column()
            col.alignment = 'CENTER'
            col.label(text="Stochastic Anti Aliasing is")
            col.label(text="Only Available with UberPOV")
            col.label(text="Feature Set in User Preferences.")
            col.label(text="Using Type 2 (recursive) instead")             
        else:
            row.prop(scene.pov, "jitter_enable", text="Jitter")

            split = layout.split()
            col = split.column()
            col.prop(scene.pov, "antialias_depth", text="AA Depth")
            sub = split.column()
            sub.prop(scene.pov, "jitter_amount", text="Jitter Amount")
            if scene.pov.jitter_enable:
                sub.enabled = True
            else:
                sub.enabled = False

            row = layout.row()
            row.prop(scene.pov, "antialias_threshold", text="AA Threshold")
            row.prop(scene.pov, "antialias_gamma", text="AA Gamma")

            if bpy.context.user_preferences.addons[__package__].preferences.branch_feature_set_povray == 'uberpov':
                row = layout.row()
                row.prop(scene.pov, "antialias_confidence", text="AA Confidence")
                if scene.pov.antialias_method =='2':
                    row.enabled = True
                else:
                    row.enabled = False



class RENDER_PT_povray_radiosity(RenderButtonsPanel, bpy.types.Panel):
    bl_label = "Radiosity"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    def draw_header(self, context):
        scene = context.scene
        if scene.pov.radio_enable:
            self.layout.prop(scene.pov, "radio_enable", text="", icon='RADIO')
        else:
            self.layout.prop(scene.pov, "radio_enable", text="", icon='RADIOBUT_OFF')

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
            col.prop(scene.pov, "radio_gray_threshold", slider=True)
            col.prop(scene.pov, "radio_low_error_factor", slider=True)
            col.prop(scene.pov, "radio_pretrace_start", slider=True)

            col = split.column()
            col.prop(scene.pov, "radio_brightness")
            col.prop(scene.pov, "radio_minimum_reuse", text="Min Reuse")
            col.prop(scene.pov, "radio_nearest_count")
            col.prop(scene.pov, "radio_pretrace_end", slider=True)

            split = layout.split()

            col = split.column()
            col.label(text="Estimation Influence:")
            col.prop(scene.pov, "radio_media")
            col.prop(scene.pov, "radio_normal")

            split.prop(scene.pov, "radio_always_sample")


class RENDER_PT_povray_media(WorldButtonsPanel, bpy.types.Panel):
    bl_label = "Atmosphere Media"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.scene

        self.layout.prop(scene.pov, "media_enable", text="")

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        layout.active = scene.pov.media_enable

        row = layout.row()
        row.prop(scene.pov, "media_samples", text="Samples")
        row.prop(scene.pov, "media_color", text="")

##class RENDER_PT_povray_baking(RenderButtonsPanel, bpy.types.Panel):
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


class MATERIAL_PT_povray_mirrorIOR(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "IOR Mirror"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.material

        self.layout.prop(scene.pov, "mirror_use_IOR", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov.mirror_use_IOR

        if mat.pov.mirror_use_IOR:
            col = layout.column()
            col.alignment = 'CENTER'
            col.label(text="The current Raytrace ")
            col.label(text="Transparency IOR is: " + str(mat.raytrace_transparency.ior))


class MATERIAL_PT_povray_metallic(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "metallic Mirror"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        scene = context.material

        self.layout.prop(scene.pov, "mirror_metallic", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov.mirror_metallic


class MATERIAL_PT_povray_fade_color(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Interior Fade Color"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat.pov, "interior_fade_color", text="")

    def draw(self, context):
        # layout = self.layout
        # mat = context.material
        # layout.active = mat.pov.interior_fade_color
        pass


class MATERIAL_PT_povray_conserve_energy(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "conserve energy"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat.pov, "conserve_energy", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov.conserve_energy


class MATERIAL_PT_povray_iridescence(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "iridescence"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat.pov, "irid_enable", text="")

    def draw(self, context):
        layout = self.layout

        mat = context.material
        layout.active = mat.pov.irid_enable

        if mat.pov.irid_enable:
            col = layout.column()
            col.prop(mat.pov, "irid_amount", slider=True)
            col.prop(mat.pov, "irid_thickness", slider=True)
            col.prop(mat.pov, "irid_turbulence", slider=True)


class MATERIAL_PT_povray_caustics(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Caustics"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        mat = context.material

        self.layout.prop(mat.pov, "caustics_enable", text="")

    def draw(self, context):

        layout = self.layout

        mat = context.material
        layout.active = mat.pov.caustics_enable

        if mat.pov.caustics_enable:
            col = layout.column()
            col.prop(mat.pov, "refraction_type")

            if mat.pov.refraction_type == "1":
                col.prop(mat.pov, "fake_caustics_power", slider=True)
            elif mat.pov.refraction_type == "2":
                col.prop(mat.pov, "photons_dispersion", slider=True)
                col.prop(mat.pov, "photons_dispersion_samples", slider=True)
            col.prop(mat.pov, "photons_reflection")

            if mat.pov.refraction_type == "0" and not mat.pov.photons_reflection:
                col = layout.column()
                col.alignment = 'CENTER'
                col.label(text="Caustics override is on, ")
                col.label(text="but you didn't chose any !")


class MATERIAL_PT_povray_replacement_text(MaterialButtonsPanel, bpy.types.Panel):
    bl_label = "Custom POV Code"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        mat = context.material

        col = layout.column()
        col.label(text="Replace properties with:")
        col.prop(mat.pov, "replacement_text", text="")

class TEXTURE_PT_povray_type(TextureButtonsPanel, bpy.types.Panel):
    bl_label = "POV-ray Textures"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    bl_options = {'HIDE_HEADER'}

    def draw(self, context):
        layout = self.layout

        tex = context.texture

        split = layout.split(percentage=0.2)
        split.label(text="POV:")
        split.prop(tex.pov, "tex_pattern_type", text="")

class TEXTURE_PT_povray_preview(TextureButtonsPanel, bpy.types.Panel):
    bl_label = "Preview"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    bl_options = {'HIDE_HEADER'}
    
    @classmethod
    def poll(cls, context):
        engine = context.scene.render.engine
        if not hasattr(context, "texture_slot"):
            return False
        tex=context.texture
        mat=context.material
        return (tex and (tex.pov.tex_pattern_type != 'emulator') and (engine in cls.COMPAT_ENGINES))

    def draw(self, context):
        tex = context.texture
        slot = getattr(context, "texture_slot", None)
        idblock = context_tex_datablock(context)
        layout = self.layout
        # if idblock:
            # layout.template_preview(tex, parent=idblock, slot=slot)
        if tex.pov.tex_pattern_type != 'emulator':
            layout.operator("tex.preview_update")
        else:
            layout.template_preview(tex, slot=slot)


class TEXTURE_PT_povray_parameters(TextureButtonsPanel, bpy.types.Panel):
    bl_label = "POV-ray Pattern Options"
    COMPAT_ENGINES = {'POVRAY_RENDER'}
    def draw(self, context):
        mat = context.material
        layout = self.layout
        tex = context.texture
        align=True
        if tex is not None and tex.pov.tex_pattern_type != 'emulator':
            if tex.pov.tex_pattern_type == 'agate':
                layout.prop(tex.pov, "modifier_turbulence", text="Agate Turbulence")
            if tex.pov.tex_pattern_type in {'spiral1', 'spiral2'}:
                layout.prop(tex.pov, "modifier_numbers", text="Number of arms")
            if tex.pov.tex_pattern_type == 'tiling':
                layout.prop(tex.pov, "modifier_numbers", text="Pattern number")
            if tex.pov.tex_pattern_type == 'magnet':
                layout.prop(tex.pov, "magnet_style", text="Magnet style")
            if tex.pov.tex_pattern_type == 'quilted':
                row = layout.row(align=align)
                row.prop(tex.pov, "modifier_control0", text="Control0")
                row.prop(tex.pov, "modifier_control1", text="Control1")
            if tex.pov.tex_pattern_type == 'brick':
                col = layout.column(align=align)
                row = col.row()
                row.prop(tex.pov, "brick_size_x", text="Brick size X")
                row.prop(tex.pov, "brick_size_y", text="Brick size Y")
                row=col.row()
                row.prop(tex.pov, "brick_size_z", text="Brick size Z")
                row.prop(tex.pov, "brick_mortar", text="Brick mortar")
            if tex.pov.tex_pattern_type in {'julia','mandel','magnet'}:
                col = layout.column(align=align)
                if tex.pov.tex_pattern_type == 'julia':
                    row = col.row()
                    row.prop(tex.pov, "julia_complex_1", text="Complex 1")
                    row.prop(tex.pov, "julia_complex_2", text="Complex 2")
                if tex.pov.tex_pattern_type == 'magnet' and tex.pov.magnet_style == 'julia':
                    row = col.row()
                    row.prop(tex.pov, "julia_complex_1", text="Complex 1")
                    row.prop(tex.pov, "julia_complex_2", text="Complex 2")
                row=col.row()
                if tex.pov.tex_pattern_type in {'julia','mandel'}:            
                    row.prop(tex.pov, "f_exponent", text="Exponent")
                if tex.pov.tex_pattern_type == 'magnet':            
                    row.prop(tex.pov, "magnet_type", text="Type")
                row.prop(tex.pov, "f_iter", text="Iterations")
                row=col.row()
                row.prop(tex.pov, "f_ior", text="Interior")
                row.prop(tex.pov, "f_ior_fac", text="Factor I")
                row=col.row()
                row.prop(tex.pov, "f_eor", text="Exterior")
                row.prop(tex.pov, "f_eor_fac", text="Factor E")
            if tex.pov.tex_pattern_type == 'gradient':        
                layout.label(text="Gradient orientation:")
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.prop(tex.pov, "grad_orient_x", text="X")        
                column_flow.prop(tex.pov, "grad_orient_y", text="Y")
                column_flow.prop(tex.pov, "grad_orient_z", text="Z")
            if tex.pov.tex_pattern_type == 'pavement':
                layout.prop(tex.pov, "pave_sides", text="Pavement:number of sides")
                col = layout.column(align=align)
                column_flow = col.column_flow(columns=3, align=True)
                column_flow.prop(tex.pov, "pave_tiles", text="Tiles")        
                if tex.pov.pave_sides == '4' and tex.pov.pave_tiles == 6:
                    column_flow.prop(tex.pov, "pave_pat_35", text="Pattern")
                if tex.pov.pave_sides == '6' and tex.pov.pave_tiles == 5:
                    column_flow.prop(tex.pov, "pave_pat_22", text="Pattern")
                if tex.pov.pave_sides == '4' and tex.pov.pave_tiles == 5:
                    column_flow.prop(tex.pov, "pave_pat_12", text="Pattern")
                if tex.pov.pave_sides == '3' and tex.pov.pave_tiles == 6:
                    column_flow.prop(tex.pov, "pave_pat_12", text="Pattern")
                if tex.pov.pave_sides == '6' and tex.pov.pave_tiles == 4:
                    column_flow.prop(tex.pov, "pave_pat_7", text="Pattern")
                if tex.pov.pave_sides == '4' and tex.pov.pave_tiles == 4:
                    column_flow.prop(tex.pov, "pave_pat_5", text="Pattern")
                if tex.pov.pave_sides == '3' and tex.pov.pave_tiles == 5:
                    column_flow.prop(tex.pov, "pave_pat_4", text="Pattern")
                if tex.pov.pave_sides == '6' and tex.pov.pave_tiles == 3:
                    column_flow.prop(tex.pov, "pave_pat_3", text="Pattern")
                if tex.pov.pave_sides == '3' and tex.pov.pave_tiles == 4:
                    column_flow.prop(tex.pov, "pave_pat_3", text="Pattern")
                if tex.pov.pave_sides == '4' and tex.pov.pave_tiles == 3:
                    column_flow.prop(tex.pov, "pave_pat_2", text="Pattern")
                if tex.pov.pave_sides == '6' and tex.pov.pave_tiles == 6:
                    column_flow.label(text="!!! 5 tiles!")
                column_flow.prop(tex.pov, "pave_form", text="Form")
            if tex.pov.tex_pattern_type == 'function':
                layout.prop(tex.pov, "func_list", text="Functions") 
            if tex.pov.tex_pattern_type == 'function' and tex.pov.func_list != "NONE":
                func = None
                if tex.pov.func_list in {"f_noise3d", "f_ph", "f_r", "f_th"}:
                    func = 0
                if tex.pov.func_list in {"f_comma","f_crossed_trough","f_cubic_saddle",
                                         "f_cushion","f_devils_curve","f_enneper","f_glob",
                                         "f_heart","f_hex_x","f_hex_y","f_hunt_surface",
                                         "f_klein_bottle","f_kummer_surface_v1",
                                         "f_lemniscate_of_gerono","f_mitre","f_nodal_cubic",
                                         "f_noise_generator","f_odd","f_paraboloid","f_pillow",
                                         "f_piriform","f_quantum","f_quartic_paraboloid",
                                         "f_quartic_saddle","f_sphere","f_steiners_roman",
                                         "f_torus_gumdrop","f_umbrella"}:
                    func = 1
                if tex.pov.func_list in {"f_bicorn","f_bifolia","f_boy_surface","f_superellipsoid","f_torus"}:
                    func = 2
                if tex.pov.func_list in {"f_ellipsoid","f_folium_surface","f_hyperbolic_torus",
                                         "f_kampyle_of_eudoxus","f_parabolic_torus",
                                         "f_quartic_cylinder","f_torus2"}:
                    func = 3
                if tex.pov.func_list in {"f_blob2","f_cross_ellipsoids","f_flange_cover",
                                         "f_isect_ellipsoids","f_kummer_surface_v2","f_ovals_of_cassini",
                                         "f_rounded_box","f_spikes_2d","f_strophoid"}:
                    func = 4
                if tex.pov.func_list in {"f_algbr_cyl1","f_algbr_cyl2","f_algbr_cyl3","f_algbr_cyl4",
                                         "f_blob","f_mesh1","f_poly4","f_spikes"}:
                    func = 5
                if tex.pov.func_list in {"f_devils_curve_2d","f_dupin_cyclid","f_folium_surface_2d",
                                         "f_hetero_mf","f_kampyle_of_eudoxus_2d","f_lemniscate_of_gerono_2d",
                                         "f_polytubes","f_ridge","f_ridged_mf","f_spiral","f_witch_of_agnesi"}:
                    func = 6
                if tex.pov.func_list in {"f_helix1","f_helix2","f_piriform_2d","f_strophoid_2d"}:
                    func = 7
                if tex.pov.func_list == "f_helical_torus":
                    func = 8
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.label(text="X")        
                column_flow.prop(tex.pov, "func_plus_x", text="")
                column_flow.prop(tex.pov, "func_x", text="Value")
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.label(text="Y")        
                column_flow.prop(tex.pov, "func_plus_y", text="")
                column_flow.prop(tex.pov, "func_y", text="Value")
                column_flow = layout.column_flow(columns=3, align=True)
                column_flow.label(text="Z")        
                column_flow.prop(tex.pov, "func_plus_z", text="")
                column_flow.prop(tex.pov, "func_z", text="Value")
                row=layout.row(align=align)
                if func > 0:
                    row.prop(tex.pov, "func_P0", text="P0")
                if func > 1:
                    row.prop(tex.pov, "func_P1", text="P1")
                row=layout.row(align=align)
                if func > 2:
                    row.prop(tex.pov, "func_P2", text="P2")
                if func > 3:
                    row.prop(tex.pov, "func_P3", text="P3")
                row=layout.row(align=align)
                if func > 4:
                    row.prop(tex.pov, "func_P4", text="P4")
                if func > 5:
                    row.prop(tex.pov, "func_P5", text="P5")
                row=layout.row(align=align)
                if func > 6:
                    row.prop(tex.pov, "func_P6", text="P6")
                if func > 7:
                    row.prop(tex.pov, "func_P7", text="P7")
                    row=layout.row(align=align)
                    row.prop(tex.pov, "func_P8", text="P8")
                    row.prop(tex.pov, "func_P9", text="P9")
        ###################################################End Patterns############################


            layout.prop(tex.pov, "warp_types", text="Warp types") #warp
            if tex.pov.warp_types == "TOROIDAL":
                layout.prop(tex.pov, "warp_tor_major_radius", text="Major radius")
            if tex.pov.warp_types not in {"CUBIC","NONE"}:
                layout.prop(tex.pov, "warp_orientation", text="Warp orientation")
            col = layout.column(align=align)
            row = col.row()         
            row.prop(tex.pov, "warp_dist_exp", text="Distance exponent")        
            row = col.row()
            row.prop(tex.pov, "modifier_frequency", text="Frequency")
            row.prop(tex.pov, "modifier_phase", text="Phase")

            row=layout.row()

            row.label(text="Offset:")
            row.label(text="Scale:")
            row.label(text="Rotate:")
            col=layout.column(align=align) 
            row=col.row()
            row.prop(tex.pov, "tex_mov_x", text="X")
            row.prop(tex.pov, "tex_scale_x", text="X")
            row.prop(tex.pov, "tex_rot_x", text="X")
            row=col.row()
            row.prop(tex.pov, "tex_mov_y", text="Y")
            row.prop(tex.pov, "tex_scale_y", text="Y")
            row.prop(tex.pov, "tex_rot_y", text="Y")
            row=col.row()
            row.prop(tex.pov, "tex_mov_z", text="Z")
            row.prop(tex.pov, "tex_scale_z", text="Z")
            row.prop(tex.pov, "tex_rot_z", text="Z")
            row=layout.row()

            row.label(text="Turbulence:")
            col=layout.column(align=align) 
            row=col.row()
            row.prop(tex.pov, "warp_turbulence_x", text="X")
            row.prop(tex.pov, "modifier_octaves", text="Octaves")
            row=col.row()
            row.prop(tex.pov, "warp_turbulence_y", text="Y")
            row.prop(tex.pov, "modifier_lambda", text="Lambda")
            row=col.row()
            row.prop(tex.pov, "warp_turbulence_z", text="Z")
            row.prop(tex.pov, "modifier_omega", text="Omega")
        
class TEXTURE_PT_povray_tex_gamma(TextureButtonsPanel, bpy.types.Panel):
    bl_label = "Image Gamma"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        tex = context.texture

        self.layout.prop(tex.pov, "tex_gamma_enable", text="", icon='SEQ_LUMA_WAVEFORM')

    def draw(self, context):
        layout = self.layout

        tex = context.texture

        layout.active = tex.pov.tex_gamma_enable
        layout.prop(tex.pov, "tex_gamma_value", text="Gamma Value")

#commented out below UI for texture only custom code inside exported material:
# class TEXTURE_PT_povray_replacement_text(TextureButtonsPanel, bpy.types.Panel):
    # bl_label = "Custom POV Code"
    # COMPAT_ENGINES = {'POVRAY_RENDER'}

    # def draw(self, context):
        # layout = self.layout

        # tex = context.texture

        # col = layout.column()
        # col.label(text="Replace properties with:")
        # col.prop(tex.pov, "replacement_text", text="")


class OBJECT_PT_povray_obj_importance(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "POV-Ray"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()
        col.label(text="Radiosity:")
        col.prop(obj.pov, "importance_value", text="Importance")
        col.label(text="Photons:")
        col.prop(obj.pov, "collect_photons", text="Receive Photon Caustics")
        if obj.pov.collect_photons:
            col.prop(obj.pov, "spacing_multiplier", text="Photons Spacing Multiplier")


class OBJECT_PT_povray_replacement_text(ObjectButtonsPanel, bpy.types.Panel):
    bl_label = "Custom POV Code"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        obj = context.object

        col = layout.column()
        col.label(text="Replace properties with:")
        col.prop(obj.pov, "replacement_text", text="")


class CAMERA_PT_povray_cam_dof(CameraDataButtonsPanel, bpy.types.Panel):
    bl_label = "POV-Ray Depth Of Field"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw_header(self, context):
        cam = context.camera

        self.layout.prop(cam.pov, "dof_enable", text="")

    def draw(self, context):
        layout = self.layout

        cam = context.camera

        layout.active = cam.pov.dof_enable

        layout.prop(cam.pov, "dof_aperture")

        split = layout.split()

        col = split.column()
        col.prop(cam.pov, "dof_samples_min")
        col.prop(cam.pov, "dof_variance")

        col = split.column()
        col.prop(cam.pov, "dof_samples_max")
        col.prop(cam.pov, "dof_confidence")


class CAMERA_PT_povray_replacement_text(CameraDataButtonsPanel, bpy.types.Panel):
    bl_label = "Custom POV Code"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        cam = context.camera

        col = layout.column()
        col.label(text="Replace properties with:")
        col.prop(cam.pov, "replacement_text", text="")


class TEXT_PT_povray_custom_code(TextButtonsPanel, bpy.types.Panel):
    bl_label = "P.O.V-Ray"
    COMPAT_ENGINES = {'POVRAY_RENDER'}

    def draw(self, context):
        layout = self.layout

        text = context.space_data.text
        if text:
            layout.prop(text.pov, "custom_code", text="Add as POV code")
