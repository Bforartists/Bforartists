# SPDX-License-Identifier: GPL-2.0-or-later

"""Write the POV file using this file's functions and some from other modules then render it."""

import bpy
import subprocess
import os
from sys import platform
#import time
from math import (
    pi,
)  # maybe move to scenography.py and topology_*****_data.py respectively with smoke and matrix
import mathutils #import less than full
import tempfile  # generate temporary files with random names
from bpy.types import Operator
from bpy.utils import register_class, unregister_class

from . import (
    scripting,
)  # for writing, importing and rendering directly POV Scene Description Language items
from . import render_core
from . import scenography  # for atmosphere, environment, effects, lighting, camera
from . import shading  # for BI POV shaders emulation
from . import nodes_fn
from . import texturing_procedural # for Blender procedurals to POV patterns emulation
from . import model_all  # for mesh based geometry
from . import model_meta_topology  # for mesh based geometry
from . import model_curve_topology  # for curves based geometry

# from . import model_primitives  # for import and export of POV specific primitives


from .scenography import image_format, img_map, img_map_transforms, path_image

from .shading import write_object_material_interior
from .model_primitives import write_object_modifiers


tab_level = 0
tab=""
comments = False
using_uberpov = False
unpacked_images = []

from .render_core import (
    preview_dir,
    PovRender,
)

def string_strip_hyphen(name):

    """Remove hyphen characters from a string to avoid POV errors."""

    return name.replace("-", "")


def safety(name, ref_level_bound):
    """append suffix characters to names of various material declinations.

    Material declinations are necessary to POV syntax and used in shading.py
    by the pov_has_no_specular_maps function to create the finish map trick and
    the suffixes avoid name collisions.
    Keyword arguments:
    name -- the initial material name as a string
    ref_level_bound -- the enum number of the ref_level_bound being written:
        ref_level_bound=1 is for texture with No specular nor Mirror reflection
        ref_level_bound=2 is for texture with translation of spec and mir levels
        for when no map influences them
        ref_level_bound=3 is for texture with Maximum Spec and Mirror
    """
    # All the try except clause below seems useless as each time
    # prefix rewritten even after and outside of it what was the point?
    # It may not even be any longer possible to feed no arg from Blender UI
    # try:
    # if name: # if int(name) > 0: # could be zero if no argument provided
    # # and always triggered exception so is this similar ?
    # prefix = "shader"
    # except BaseException as e:
    # print(e.__doc__)
    # print('An exception occurred: {}'.format(e))
    # prefix = "" # rewritten below...
    prefix = "shader_"
    name = string_strip_hyphen(name)
    if ref_level_bound == 2:
        return prefix + name
    # implicit else-if (no return yet)
    if ref_level_bound == 1:
        return prefix + name + "0"  # used for 0 of specular map
    # implicit else-if (no return yet)
    if ref_level_bound == 3:
        return prefix + name + "1"  # used for 1 of specular map


# -------- end safety string name material


csg_list = []


def is_renderable(ob):
    """test for objects flagged as hidden or boolean operands not to render"""
    return not ob.hide_render and ob not in csg_list


def renderable_objects():
    """test for non hidden, non boolean operands objects to render"""
    return [ob for ob in bpy.data.objects if is_renderable(ob)]


def non_renderable_objects():
    """Boolean operands only. Not to render"""
    return list(csg_list)


def set_tab(tabtype, spaces):
    """Apply the configured indentation all along the exported POV file

    Arguments:
        tabtype -- Specifies user preference between tabs or spaces indentation
        spaces -- If using spaces, sets the number of space characters to use
    Returns:
        The beginning blank space for each line of the generated pov file
    """
    tab_str = ""
    match tabtype:
        case 'SPACE':
            tab_str = spaces * " "
        case 'NONE':
            tab_str = ""
        case 'TAB':
            tab_str = "\t"
    return tab_str



'''

# below properties not added to __init__ yet to avoid conflicts with material sss scale
# unless it would override then should be interfaced also in scene units property tab

# if scene.pov.sslt_enable:
    # file.write("    mm_per_unit %s\n"%scene.pov.mm_per_unit)
    # file.write("    subsurface {\n")
    # file.write("        samples %s, %s\n"%(scene.pov.sslt_samples_max,scene.pov.sslt_samples_min))
    # if scene.pov.sslt_radiosity:
        # file.write("        radiosity on\n")
    # file.write("}\n")

'''


# def write_object_modifiers(ob, File):
# """Translate some object level POV statements from Blender UI
# to POV syntax and write to exported file """

# # Maybe return that string to be added instead of directly written.

# '''XXX WIP
# import .model_all.write_object_csg_inside_vector
# write_object_csg_inside_vector(ob, file)
# '''

# if ob.pov.hollow:
# File.write("\thollow\n")
# if ob.pov.double_illuminate:
# File.write("\tdouble_illuminate\n")
# if ob.pov.sturm:
# File.write("\tsturm\n")
# if ob.pov.no_shadow:
# File.write("\tno_shadow\n")
# if ob.pov.no_image:
# File.write("\tno_image\n")
# if ob.pov.no_reflection:
# File.write("\tno_reflection\n")
# if ob.pov.no_radiosity:
# File.write("\tno_radiosity\n")
# if ob.pov.inverse:
# File.write("\tinverse\n")
# if ob.pov.hierarchy:
# File.write("\thierarchy\n")

# # XXX, Commented definitions
# '''
# if scene.pov.photon_enable:
# File.write("photons {\n")
# if ob.pov.target:
# File.write("target %.4g\n"%ob.pov.target_value)
# if ob.pov.refraction:
# File.write("refraction on\n")
# if ob.pov.reflection:
# File.write("reflection on\n")
# if ob.pov.pass_through:
# File.write("pass_through\n")
# File.write("}\n")
# if ob.pov.object_ior > 1:
# File.write("interior {\n")
# File.write("ior %.4g\n"%ob.pov.object_ior)
# if scene.pov.photon_enable and ob.pov.target and ob.pov.refraction and ob.pov.dispersion:
# File.write("ior %.4g\n"%ob.pov.dispersion_value)
# File.write("ior %s\n"%ob.pov.dispersion_samples)
# if scene.pov.photon_enable == False:
# File.write("caustics %.4g\n"%ob.pov.fake_caustics_power)
# '''

def tab_write(file, str_o, scene=None):
    """write directly to exported file if user checked autonamed temp files (faster).
    Otherwise, indent POV syntax from brackets levels and write to exported file"""

    if not scene:
        scene = bpy.data.scenes[0]
    global tab
    tab = set_tab(scene.pov.indentation_character, scene.pov.indentation_spaces)
    if scene.pov.tempfiles_enable:
        file.write(str_o)
    else:
        global tab_level
        brackets = str_o.count("{") - str_o.count("}") + str_o.count("[") - str_o.count("]")
        if brackets < 0:
            tab_level = tab_level + brackets
        if tab_level < 0:
            print("Indentation Warning: tab_level = %s" % tab_level)
            tab_level = 0
        if tab_level >= 1:
            file.write("%s" % tab * tab_level)
        file.write(str_o)
        if brackets > 0:
            tab_level = tab_level + brackets

def write_matrix(file, matrix):
    """Translate some transform matrix from Blender UI
    to POV syntax and write to exported file """
    tab_write(file,
        "matrix <%.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f,  %.6f, %.6f, %.6f>\n"
        % (
            matrix[0][0],
            matrix[1][0],
            matrix[2][0],
            matrix[0][1],
            matrix[1][1],
            matrix[2][1],
            matrix[0][2],
            matrix[1][2],
            matrix[2][2],
            matrix[0][3],
            matrix[1][3],
            matrix[2][3],
        )
    )
global_matrix = mathutils.Matrix.Rotation(-pi / 2.0, 4, 'X')

def write_pov(filename, scene=None, info_callback=None):
    """Main export process from Blender UI to POV syntax and write to exported file """

    with open(filename, "w") as file:
        # Only for testing
        if not scene:
            scene = bpy.data.scenes[0]

        render = scene.render
        world = scene.world
        global comments
        comments = scene.pov.comments_enable and not scene.pov.tempfiles_enable

        feature_set = bpy.context.preferences.addons[__package__].preferences.branch_feature_set_povray
        global using_uberpov
        using_uberpov = feature_set == 'uberpov'
        pov_binary = PovRender._locate_binary()

        if using_uberpov:
            print("Unofficial UberPOV feature set chosen in preferences")
        else:
            print("Official POV-Ray 3.7 feature set chosen in preferences")
        if 'uber' in pov_binary:
            print("The name of the binary suggests you are probably rendering with Uber POV engine")
        else:
            print("The name of the binary suggests you are probably rendering with standard POV engine")


        def unique_name(name, name_seq):
            """Increment any generated POV name that could get identical to avoid collisions"""

            if name not in name_seq:
                name = string_strip_hyphen(name)
                return name

            name_orig = name
            i = 1
            while name in name_seq:
                name = "%s_%.3d" % (name_orig, i)
                i += 1
            name = string_strip_hyphen(name)
            return name

        material_names_dictionary = {}
        DEF_MAT_NAME = ""  # or "Default"?

        # -----------------------------------------------------------------------------

        def export_global_settings(scene):
            """write all POV global settings to exported file """
            # Imperial units warning
            if scene.unit_settings.system == "IMPERIAL":
                print("Warning: Imperial units not supported")

            tab_write(file, "global_settings {\n")
            tab_write(file, "assumed_gamma 1.0\n")
            tab_write(file, "max_trace_level %d\n" % scene.pov.max_trace_level)

            if scene.pov.global_settings_advanced:
                if not scene.pov.radio_enable:
                    file.write("    adc_bailout %.6f\n" % scene.pov.adc_bailout)
                file.write("    ambient_light <%.6f,%.6f,%.6f>\n" % scene.pov.ambient_light[:])
                file.write("    irid_wavelength <%.6f,%.6f,%.6f>\n" % scene.pov.irid_wavelength[:])
                file.write("    number_of_waves %s\n" % scene.pov.number_of_waves)
                file.write("    noise_generator %s\n" % scene.pov.noise_generator)
            if scene.pov.radio_enable:
                tab_write(file, "radiosity {\n")
                tab_write(file, "adc_bailout %.4g\n" % scene.pov.radio_adc_bailout)
                tab_write(file, "brightness %.4g\n" % scene.pov.radio_brightness)
                tab_write(file, "count %d\n" % scene.pov.radio_count)
                tab_write(file, "error_bound %.4g\n" % scene.pov.radio_error_bound)
                tab_write(file, "gray_threshold %.4g\n" % scene.pov.radio_gray_threshold)
                tab_write(file, "low_error_factor %.4g\n" % scene.pov.radio_low_error_factor)
                tab_write(file, "maximum_reuse %.4g\n" % scene.pov.radio_maximum_reuse)
                tab_write(file, "minimum_reuse %.4g\n" % scene.pov.radio_minimum_reuse)
                tab_write(file, "nearest_count %d\n" % scene.pov.radio_nearest_count)
                tab_write(file, "pretrace_start %.3g\n" % scene.pov.radio_pretrace_start)
                tab_write(file, "pretrace_end %.3g\n" % scene.pov.radio_pretrace_end)
                tab_write(file, "recursion_limit %d\n" % scene.pov.radio_recursion_limit)
                tab_write(file, "always_sample %d\n" % scene.pov.radio_always_sample)
                tab_write(file, "normal %d\n" % scene.pov.radio_normal)
                tab_write(file, "media %d\n" % scene.pov.radio_media)
                tab_write(file, "subsurface %d\n" % scene.pov.radio_subsurface)
                tab_write(file, "}\n")
            once_sss = 1
            once_ambient = 1
            once_photons = 1
            for material in bpy.data.materials:
                if material.pov_subsurface_scattering.use and once_sss:
                    # In pov, the scale has reversed influence compared to blender. these number
                    # should correct that
                    tab_write(file,
                        "mm_per_unit %.6f\n" % (material.pov_subsurface_scattering.scale * 1000.0)
                    )
                    # 1000 rather than scale * (-100.0) + 15.0))

                    # In POV-Ray, the scale factor for all subsurface shaders needs to be the same

                    # formerly sslt_samples were multiplied by 100 instead of 10
                    sslt_samples = (11 - material.pov_subsurface_scattering.error_threshold) * 10

                    tab_write(file, "subsurface { samples %d, %d }\n" % (sslt_samples, sslt_samples / 10))
                    once_sss = 0

                if world and once_ambient:
                    tab_write(file, "ambient_light rgb<%.3g, %.3g, %.3g>\n" % world.pov.ambient_color[:])
                    once_ambient = 0

                if (
                    scene.pov.photon_enable
                    and once_photons
                    and (
                        material.pov.refraction_type == "2"
                        or material.pov.photons_reflection
                    )
                ):
                    tab_write(file, "photons {\n")
                    tab_write(file, "spacing %.6f\n" % scene.pov.photon_spacing)
                    tab_write(file, "max_trace_level %d\n" % scene.pov.photon_max_trace_level)
                    tab_write(file, "adc_bailout %.3g\n" % scene.pov.photon_adc_bailout)
                    tab_write(file,
                        "gather %d, %d\n"
                        % (scene.pov.photon_gather_min, scene.pov.photon_gather_max)
                    )
                    if scene.pov.photon_map_file_save_load in {'save'}:
                        ph_file_name = 'Photon_map_file.ph'
                        if scene.pov.photon_map_file != '':
                            ph_file_name = scene.pov.photon_map_file + '.ph'
                        ph_file_dir = tempfile.gettempdir()
                        path = bpy.path.abspath(scene.pov.photon_map_dir)
                        if os.path.exists(path):
                            ph_file_dir = path
                        full_file_name = os.path.join(ph_file_dir, ph_file_name)
                        tab_write(file, 'save_file "%s"\n' % full_file_name)
                        scene.pov.photon_map_file = full_file_name
                    if scene.pov.photon_map_file_save_load in {'load'}:
                        full_file_name = bpy.path.abspath(scene.pov.photon_map_file)
                        if os.path.exists(full_file_name):
                            tab_write(file, 'load_file "%s"\n' % full_file_name)
                    tab_write(file, "}\n")
                    once_photons = 0

            tab_write(file, "}\n")

        # sel = renderable_objects() #removed for booleans
        if comments:
            file.write(
                "//----------------------------------------------\n"
                "//--Exported with POV-Ray exporter for Blender--\n"
                "//----------------------------------------------\n\n"
            )
        file.write("#version 3.7;\n")  # Switch below as soon as 3.8 beta gets easy linked
        # file.write("#version 3.8;\n")
        file.write(
            "#declare Default_texture = texture{pigment {rgb 0.8} " "finish {brilliance 3.8} }\n\n"
        )
        if comments:
            file.write("\n//--Global settings--\n\n")

        export_global_settings(scene)

        if comments:
            file.write("\n//--Custom Code--\n\n")
        scripting.export_custom_code(file)

        if comments:
            file.write("\n//--Patterns Definitions--\n\n")
        local_pattern_names = []
        for texture in bpy.data.textures:  # ok?
            if texture.users > 0:
                current_pat_name = string_strip_hyphen(bpy.path.clean_name(texture.name))
                # string_strip_hyphen(patternNames[texture.name]) #maybe instead of the above
                local_pattern_names.append(current_pat_name)
                # use above list to prevent writing texture instances several times and assign in mats?
                if (
                    texture.type not in {'NONE', 'IMAGE'} and texture.pov.tex_pattern_type == 'emulator'
                ) or (texture.type in {'NONE', 'IMAGE'} and texture.pov.tex_pattern_type != 'emulator'):
                    file.write("\n#declare PAT_%s = \n" % current_pat_name)
                    file.write(texturing_procedural.export_pattern(texture))
                file.write("\n")
        if comments:
            file.write("\n//--Background--\n\n")

        scenography.export_world(file, scene.world, scene, global_matrix, tab_write)

        if comments:
            file.write("\n//--Cameras--\n\n")

        scenography.export_camera(file, scene, global_matrix, render, tab_write)

        if comments:
            file.write("\n//--Lamps--\n\n")

        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                for mod in ob.modifiers:
                    if mod.type == 'BOOLEAN' and mod.object not in csg_list:
                        csg_list.append(mod.object)
        if csg_list:
            csg = False
            sel = non_renderable_objects()
            # export non rendered boolean objects operands
            model_all.objects_loop(
                file,
                scene,
                sel,
                csg,
                material_names_dictionary,
                unpacked_images,
                tab_level,
                tab_write,
                info_callback,
            )

        csg = True
        sel = renderable_objects()

        scenography.export_lights(
            [L for L in sel if (L.type == 'LIGHT' and L.pov.object_as != 'RAINBOW')],
            file,
            scene,
            global_matrix,
            tab_write,
        )

        if comments:
            file.write("\n//--Rainbows--\n\n")
        scenography.export_rainbows(
            [L for L in sel if (L.type == 'LIGHT' and L.pov.object_as == 'RAINBOW')],
            file,
            scene,
            global_matrix,
            tab_write,
        )

        if comments:
            file.write("\n//--Special Curves--\n\n")
        for c in sel:
            if c.is_modified(scene, 'RENDER'):
                continue  # don't export as pov curves objects with modifiers, but as mesh
            # Implicit else-if (as not skipped by previous "continue")
            if c.type == 'CURVE' and (c.pov.curveshape in {'lathe', 'sphere_sweep', 'loft', 'birail'}):
                model_curve_topology.export_curves(file, c, tab_write)

        if comments:
            file.write("\n//--Material Definitions--\n\n")
        # write a default pigment for objects with no material (comment out to show black)
        file.write("#default{ pigment{ color srgb 0.8 }}\n")
        # Convert all materials to strings we can access directly per vertex.
        # exportMaterials()
        shading.write_material(
            file,
            using_uberpov,
            DEF_MAT_NAME,
            tab_write,
            comments,
            unique_name,
            material_names_dictionary,
            None,
        )  # default material
        for material in bpy.data.materials:
            if material.users > 0:
                r, g, b, a = material.diffuse_color[:]
                pigment_color = "pigment {rgbt <%.4g,%.4g,%.4g,%.4g>}" % (r, g, b, 1 - a)
                if material.pov.material_use_nodes:
                    # Also make here other pigment_color fallback using BSDF node main color ?
                    ntree = material.node_tree
                    pov_mat_name = string_strip_hyphen(bpy.path.clean_name(material.name))
                    if len(ntree.nodes) == 0:
                        file.write('#declare %s = texture {%s}\n' % (pov_mat_name, pigment_color))
                    else:
                        nodes_fn.write_nodes(pov_mat_name, ntree, file)

                    for node in ntree.nodes:
                        if node:
                            if node.bl_idname == "PovrayOutputNode":
                                if node.inputs["Texture"].is_linked:
                                    for link in ntree.links:
                                        if link.to_node.bl_idname == "PovrayOutputNode":
                                            pov_mat_name = (
                                                string_strip_hyphen(
                                                    bpy.path.clean_name(link.from_node.name)
                                                )
                                                + "_%s" % pov_mat_name
                                            )
                                else:
                                    file.write(
                                        '#declare %s = texture {%s}\n' % (pov_mat_name, pigment_color)
                                    )
                else:
                    shading.write_material(
                        file,
                        using_uberpov,
                        DEF_MAT_NAME,
                        tab_write,
                        comments,
                        unique_name,
                        material_names_dictionary,
                        material,
                    )
                # attributes are all the variables needed by the other python file...
        if comments:
            file.write("\n")

        model_meta_topology.export_meta(file,
                                         [m for m in sel if m.type == 'META'],
                                         material_names_dictionary,
                                         tab_write,
                                         DEF_MAT_NAME,)

        if comments:
            file.write("//--Mesh objects--\n")

        # tbefore = time.time()
        model_all.objects_loop(
            file,
            scene,
            sel,
            csg,
            material_names_dictionary,
            unpacked_images,
            tab_level,
            tab_write,
            info_callback,
        )
        # totime = time.time() - tbefore
        # print("objects_loop took" + str(totime))

        # What follow used to happen here:
        # export_camera()
        # scenography.export_world(file, scene.world, scene, global_matrix, tab_write)
        # export_global_settings(scene)
        # MR:..and the order was important for implementing pov 3.7 baking
        #      (mesh camera) comment for the record
        # CR: Baking should be a special case than. If "baking", than we could change the order.

    if not file.closed:
        file.close()

def write_pov_ini(filename_ini, filename_log, filename_pov, filename_image):
    """Write ini file."""
    feature_set = bpy.context.preferences.addons[__package__].preferences.branch_feature_set_povray
    global using_uberpov
    using_uberpov = feature_set == 'uberpov'
    # scene = bpy.data.scenes[0]
    scene = bpy.context.scene
    render = scene.render

    x = int(render.resolution_x * render.resolution_percentage * 0.01)
    y = int(render.resolution_y * render.resolution_percentage * 0.01)

    with open(filename_ini, "w") as file:
        file.write("Version=3.7\n")
        # write povray text stream to temporary file of same name with _log suffix
        # file.write("All_File='%s'\n" % filename_log)
        # DEBUG.OUT log if none specified:
        file.write("All_File=1\n")

        file.write("Input_File_Name='%s'\n" % filename_pov)
        file.write("Output_File_Name='%s'\n" % filename_image)

        file.write("Width=%d\n" % x)
        file.write("Height=%d\n" % y)

        # Border render.
        if render.use_border:
            file.write("Start_Column=%4g\n" % render.border_min_x)
            file.write("End_Column=%4g\n" % render.border_max_x)

            file.write("Start_Row=%4g\n" % (1.0 - render.border_max_y))
            file.write("End_Row=%4g\n" % (1.0 - render.border_min_y))

        file.write("Bounding_Method=2\n")  # The new automatic BSP is faster in most scenes

        # Activated (turn this back off when better live exchange is done between the two programs
        # (see next comment)
        file.write("Display=1\n")
        file.write("Pause_When_Done=0\n")
        # PNG, with POV-Ray 3.7, can show background color with alpha. In the long run using the
        # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
        file.write("Output_File_Type=N\n")
        # file.write("Output_File_Type=T\n") # TGA, best progressive loading
        file.write("Output_Alpha=1\n")

        if scene.pov.antialias_enable:
            # method 2 (recursive) with higher max subdiv forced because no mipmapping in POV-Ray
            # needs higher sampling.
            # aa_mapping = {"5": 2, "8": 3, "11": 4, "16": 5}
            if using_uberpov:
                method = {"0": 1, "1": 2, "2": 3}
            else:
                method = {"0": 1, "1": 2, "2": 2}
            file.write("Antialias=on\n")
            file.write("Antialias_Depth=%d\n" % scene.pov.antialias_depth)
            file.write("Antialias_Threshold=%.3g\n" % scene.pov.antialias_threshold)
            if using_uberpov and scene.pov.antialias_method == '2':
                file.write("Sampling_Method=%s\n" % method[scene.pov.antialias_method])
                file.write("Antialias_Confidence=%.3g\n" % scene.pov.antialias_confidence)
            else:
                file.write("Sampling_Method=%s\n" % method[scene.pov.antialias_method])
            file.write("Antialias_Gamma=%.3g\n" % scene.pov.antialias_gamma)
            if scene.pov.jitter_enable:
                file.write("Jitter=on\n")
                file.write("Jitter_Amount=%3g\n" % scene.pov.jitter_amount)
            else:
                file.write("Jitter=off\n")  # prevent animation flicker

        else:
            file.write("Antialias=off\n")
    if not file.closed:
        file.close()


# --------------------------------------------------------------------------------- #
# ----------------------------------- Operators ----------------------------------- #
# --------------------------------------------------------------------------------- #
class RenderPovTexturePreview(Operator):
    """Export only files necessary to texture preview and render image"""

    bl_idname = "tex.preview_update"
    bl_label = "Update preview"

    def execute(self, context):
        tex = bpy.context.object.active_material.active_texture  # context.texture
        tex_prev_name = string_strip_hyphen(bpy.path.clean_name(tex.name)) + "_prev"

        # Make sure Preview directory exists and is empty
        if not os.path.isdir(preview_dir):
            os.mkdir(preview_dir)

        ini_prev_file = os.path.join(preview_dir, "Preview.ini")
        input_prev_file = os.path.join(preview_dir, "Preview.pov")
        output_prev_file = os.path.join(preview_dir, tex_prev_name)
        # ---------------------------------- ini ---------------------------------- #
        with open(ini_prev_file, "w") as file_ini:
            file_ini.write('Version=3.8\n')
            file_ini.write('Input_File_Name="%s"\n' % input_prev_file)
            file_ini.write('Output_File_Name="%s.png"\n' % output_prev_file)
            file_ini.write('Library_Path="%s"\n' % preview_dir)
            file_ini.write('Width=256\n')
            file_ini.write('Height=256\n')
            file_ini.write('Pause_When_Done=0\n')
            file_ini.write('Output_File_Type=N\n')
            file_ini.write('Output_Alpha=1\n')
            file_ini.write('Antialias=on\n')
            file_ini.write('Sampling_Method=2\n')
            file_ini.write('Antialias_Depth=3\n')
            file_ini.write('-d\n')
        if not file_ini.closed:
            file_ini.close()
        # ---------------------------------- pov ---------------------------------- #
        with open(input_prev_file, "w") as file_pov:
            pat_name = "PAT_" + string_strip_hyphen(bpy.path.clean_name(tex.name))
            file_pov.write("#declare %s = \n" % pat_name)
            file_pov.write(texturing_procedural.export_pattern(tex))

            file_pov.write("#declare Plane =\n")
            file_pov.write("mesh {\n")
            file_pov.write(
                "    triangle {<-2.021,-1.744,2.021>,<-2.021,-1.744,-2.021>,<2.021,-1.744,2.021>}\n"
            )
            file_pov.write(
                "    triangle {<-2.021,-1.744,-2.021>,<2.021,-1.744,-2.021>,<2.021,-1.744,2.021>}\n"
            )
            file_pov.write("    texture{%s}\n" % pat_name)
            file_pov.write("}\n")
            file_pov.write("object {Plane}\n")
            file_pov.write("light_source {\n")
            file_pov.write("    <0,4.38,-1.92e-07>\n")
            file_pov.write("    color rgb<4, 4, 4>\n")
            file_pov.write("    parallel\n")
            file_pov.write("    point_at  <0, 0, -1>\n")
            file_pov.write("}\n")
            file_pov.write("camera {\n")
            file_pov.write("    location  <0, 0, 0>\n")
            file_pov.write("    look_at  <0, 0, -1>\n")
            file_pov.write("    right <-1.0, 0, 0>\n")
            file_pov.write("    up <0, 1, 0>\n")
            file_pov.write("    angle  96.805211\n")
            file_pov.write("    rotate  <-90.000003, -0.000000, 0.000000>\n")
            file_pov.write("    translate <0.000000, 0.000000, 0.000000>\n")
            file_pov.write("}\n")
        if not file_pov.closed:
            file_pov.close()
        # ------------------------------- end write ------------------------------- #

        pov_binary = PovRender._locate_binary()

        if platform.startswith('win'):
            with subprocess.Popen(
                ["%s" % pov_binary, "/EXIT", "%s" % ini_prev_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ) as p1:
                p1.wait()
        else:
            with subprocess.Popen(
                ["%s" % pov_binary, "-d", "%s" % ini_prev_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            ) as p1:
                p1.wait()

        tex.use_nodes = True
        tree = tex.node_tree
        links = tree.links
        for n in tree.nodes:
            tree.nodes.remove(n)
        im = tree.nodes.new("TextureNodeImage")
        path_prev = "%s.png" % output_prev_file
        im.image = bpy.data.images.load(path_prev)
        name = path_prev
        name = name.split("/")
        name = name[len(name) - 1]
        im.name = name
        im.location = 200, 200
        previewer = tree.nodes.new('TextureNodeOutput')
        previewer.label = "Preview"
        previewer.location = 400, 400
        links.new(im.outputs[0], previewer.inputs[0])
        # tex.type="IMAGE" # makes clip extend possible
        # tex.extension="CLIP"
        return {'FINISHED'}


class RunPovTextRender(Operator):
    """Export files depending on text editor options and render image."""

    bl_idname = "text.run"
    bl_label = "Run"
    bl_context = "text"
    bl_description = "Run a render with this text only"

    def execute(self, context):
        scene = context.scene
        scene.pov.text_block = context.space_data.text.name

        bpy.ops.render.render()

        # empty text name property again
        scene.pov.text_block = ""
        return {'FINISHED'}


classes = (
    #PovRender,
    RenderPovTexturePreview,
    RunPovTextRender,
)


def register():
    for cls in classes:
        register_class(cls)
    scripting.register()


def unregister():
    scripting.unregister()
    for cls in reversed(classes):
        unregister_class(cls)
