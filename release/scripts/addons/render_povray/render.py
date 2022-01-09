# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# #**** END GPL LICENSE BLOCK #****

# <pep8 compliant>

"""Write the POV file using this file's functions and some from other modules then render it."""

import bpy
import subprocess
import os
from sys import platform
import time
from math import (
    pi,
)  # maybe move to scenography.py and topology_*****_data.py respectively with smoke and matrix

import re
import tempfile  # generate temporary files with random names
from bpy.types import Operator
from bpy.utils import register_class, unregister_class

from . import (
    scripting,
)  # for writing, importing and rendering directly POV Scene Description Language items
from . import scenography  # for atmosphere, environment, effects, lighting, camera
from . import shading  # for BI POV shaders emulation
from . import object_mesh_topology  # for mesh based geometry
from . import object_curve_topology  # for curves based geometry

# from . import object_primitives  # for import and export of POV specific primitives


from .scenography import image_format, img_map, img_map_transforms, path_image

from .shading import write_object_material_interior
from .object_primitives import write_object_modifiers


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


def renderable_objects(scene):
    """test for non hidden, non boolean operands objects to render"""
    return [ob for ob in bpy.data.objects if is_renderable(ob)]


def no_renderable_objects():
    """Boolean operands only. Not to render"""
    return list(csg_list)


tab_level = 0
unpacked_images = []

user_dir = bpy.utils.resource_path('USER')
preview_dir = os.path.join(user_dir, "preview")

# Make sure Preview directory exists and is empty
smoke_path = os.path.join(preview_dir, "smoke.df3")

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


# def write_object_modifiers(scene, ob, File):
# """Translate some object level POV statements from Blender UI
# to POV syntax and write to exported file """

# # Maybe return that string to be added instead of directly written.

# '''XXX WIP
# onceCSG = 0
# for mod in ob.modifiers:
# if onceCSG == 0:
# if mod :
# if mod.type == 'BOOLEAN':
# if ob.pov.boolean_mod == "POV":
# File.write("\tinside_vector <%.6g, %.6g, %.6g>\n" %
# (ob.pov.inside_vector[0],
# ob.pov.inside_vector[1],
# ob.pov.inside_vector[2]))
# onceCSG = 1
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


def write_pov(filename, scene=None, info_callback=None):
    """Main export process from Blender UI to POV syntax and write to exported file """

    import mathutils

    # file = filename
    file = open(filename, "w")

    # Only for testing
    if not scene:
        scene = bpy.data.scenes[0]

    render = scene.render
    world = scene.world
    global_matrix = mathutils.Matrix.Rotation(-pi / 2.0, 4, 'X')
    comments = scene.pov.comments_enable and not scene.pov.tempfiles_enable
    linebreaksinlists = scene.pov.list_lf_enable and not scene.pov.tempfiles_enable
    feature_set = bpy.context.preferences.addons[__package__].preferences.branch_feature_set_povray
    using_uberpov = feature_set == 'uberpov'
    pov_binary = PovrayRender._locate_binary()

    if using_uberpov:
        print("Unofficial UberPOV feature set chosen in preferences")
    else:
        print("Official POV-Ray 3.7 feature set chosen in preferences")
    if 'uber' in pov_binary:
        print("The name of the binary suggests you are probably rendering with Uber POV engine")
    else:
        print("The name of the binary suggests you are probably rendering with standard POV engine")

    def set_tab(tabtype, spaces):
        tab_str = ""
        if tabtype == 'NONE':
            tab_str = ""
        elif tabtype == 'TAB':
            tab_str = "\t"
        elif tabtype == 'SPACE':
            tab_str = spaces * " "
        return tab_str

    tab = set_tab(scene.pov.indentation_character, scene.pov.indentation_spaces)
    if not scene.pov.tempfiles_enable:

        def tab_write(str_o):
            """Indent POV syntax from brackets levels and write to exported file """
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

    else:

        def tab_write(str_o):
            """write directly to exported file if user checked autonamed temp files (faster)."""

            file.write(str_o)

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

    def write_matrix(matrix):
        """Translate some transform matrix from Blender UI
        to POV syntax and write to exported file """
        tab_write(
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

    material_names_dictionary = {}
    DEF_MAT_NAME = ""  # or "Default"?

    # -----------------------------------------------------------------------------

    def export_meta(metas):
        """write all POV blob primitives and Blender Metas to exported file """
        # TODO - blenders 'motherball' naming is not supported.

        if comments and len(metas) >= 1:
            file.write("//--Blob objects--\n\n")
        # Get groups of metaballs by blender name prefix.
        meta_group = {}
        meta_elems = {}
        for ob in metas:
            prefix = ob.name.split(".")[0]
            if prefix not in meta_group:
                meta_group[prefix] = ob  # .data.threshold
            elems = [
                (elem, ob)
                for elem in ob.data.elements
                if elem.type in {'BALL', 'ELLIPSOID', 'CAPSULE', 'CUBE', 'PLANE'}
            ]
            if prefix in meta_elems:
                meta_elems[prefix].extend(elems)
            else:
                meta_elems[prefix] = elems

            # empty metaball
            if len(elems) == 0:
                tab_write("\n//dummy sphere to represent empty meta location\n")
                tab_write(
                    "sphere {<%.6g, %.6g, %.6g>,0 pigment{rgbt 1} "
                    "no_image no_reflection no_radiosity "
                    "photons{pass_through collect off} hollow}\n\n"
                    % (ob.location.x, ob.location.y, ob.location.z)
                )  # ob.name > povdataname)
            # other metaballs
            else:
                for mg, mob in meta_group.items():
                    if len(meta_elems[mg]) != 0:
                        tab_write("blob{threshold %.4g // %s \n" % (mob.data.threshold, mg))
                        for elems in meta_elems[mg]:
                            elem = elems[0]
                            loc = elem.co
                            stiffness = elem.stiffness
                            if elem.use_negative:
                                stiffness = -stiffness
                            if elem.type == 'BALL':
                                tab_write(
                                    "sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g "
                                    % (loc.x, loc.y, loc.z, elem.radius, stiffness)
                                )
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")
                            elif elem.type == 'ELLIPSOID':
                                tab_write(
                                    "sphere{ <%.6g, %.6g, %.6g>,%.4g,%.4g "
                                    % (
                                        loc.x / elem.size_x,
                                        loc.y / elem.size_y,
                                        loc.z / elem.size_z,
                                        elem.radius,
                                        stiffness,
                                    )
                                )
                                tab_write(
                                    "scale <%.6g, %.6g, %.6g>"
                                    % (elem.size_x, elem.size_y, elem.size_z)
                                )
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")
                            elif elem.type == 'CAPSULE':
                                tab_write(
                                    "cylinder{ <%.6g, %.6g, %.6g>,<%.6g, %.6g, %.6g>,%.4g,%.4g "
                                    % (
                                        (loc.x - elem.size_x),
                                        (loc.y),
                                        (loc.z),
                                        (loc.x + elem.size_x),
                                        (loc.y),
                                        (loc.z),
                                        elem.radius,
                                        stiffness,
                                    )
                                )
                                # tab_write("scale <%.6g, %.6g, %.6g>" % (elem.size_x, elem.size_y, elem.size_z))
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")

                            elif elem.type == 'CUBE':
                                tab_write(
                                    "cylinder { -x*8, +x*8,%.4g,%.4g translate<%.6g,%.6g,%.6g> scale  <1/4,1,1> scale <%.6g, %.6g, %.6g>\n"
                                    % (
                                        elem.radius * 2.0,
                                        stiffness / 4.0,
                                        loc.x,
                                        loc.y,
                                        loc.z,
                                        elem.size_x,
                                        elem.size_y,
                                        elem.size_z,
                                    )
                                )
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")
                                tab_write(
                                    "cylinder { -y*8, +y*8,%.4g,%.4g translate<%.6g,%.6g,%.6g> scale <1,1/4,1> scale <%.6g, %.6g, %.6g>\n"
                                    % (
                                        elem.radius * 2.0,
                                        stiffness / 4.0,
                                        loc.x,
                                        loc.y,
                                        loc.z,
                                        elem.size_x,
                                        elem.size_y,
                                        elem.size_z,
                                    )
                                )
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")
                                tab_write(
                                    "cylinder { -z*8, +z*8,%.4g,%.4g translate<%.6g,%.6g,%.6g> scale <1,1,1/4> scale <%.6g, %.6g, %.6g>\n"
                                    % (
                                        elem.radius * 2.0,
                                        stiffness / 4.0,
                                        loc.x,
                                        loc.y,
                                        loc.z,
                                        elem.size_x,
                                        elem.size_y,
                                        elem.size_z,
                                    )
                                )
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")

                            elif elem.type == 'PLANE':
                                tab_write(
                                    "cylinder { -x*8, +x*8,%.4g,%.4g translate<%.6g,%.6g,%.6g> scale  <1/4,1,1> scale <%.6g, %.6g, %.6g>\n"
                                    % (
                                        elem.radius * 2.0,
                                        stiffness / 4.0,
                                        loc.x,
                                        loc.y,
                                        loc.z,
                                        elem.size_x,
                                        elem.size_y,
                                        elem.size_z,
                                    )
                                )
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")
                                tab_write(
                                    "cylinder { -y*8, +y*8,%.4g,%.4g translate<%.6g,%.6g,%.6g> scale <1,1/4,1> scale <%.6g, %.6g, %.6g>\n"
                                    % (
                                        elem.radius * 2.0,
                                        stiffness / 4.0,
                                        loc.x,
                                        loc.y,
                                        loc.z,
                                        elem.size_x,
                                        elem.size_y,
                                        elem.size_z,
                                    )
                                )
                                write_matrix(global_matrix @ elems[1].matrix_world)
                                tab_write("}\n")

                        try:
                            material = elems[1].data.materials[
                                0
                            ]  # lame! - blender cant do enything else.
                        except BaseException as e:
                            print(e.__doc__)
                            print('An exception occurred: {}'.format(e))
                            material = None
                        if material:
                            diffuse_color = material.diffuse_color
                            trans = 1.0 - material.pov.alpha
                            if (
                                material.use_transparency
                                and material.transparency_method == 'RAYTRACE'
                            ):
                                pov_filter = material.pov_raytrace_transparency.filter * (
                                    1.0 - material.alpha
                                )
                                trans = (1.0 - material.pov.alpha) - pov_filter
                            else:
                                pov_filter = 0.0
                            material_finish = material_names_dictionary[material.name]
                            tab_write(
                                "pigment {srgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} \n"
                                % (
                                    diffuse_color[0],
                                    diffuse_color[1],
                                    diffuse_color[2],
                                    pov_filter,
                                    trans,
                                )
                            )
                            tab_write("finish{%s} " % safety(material_finish, ref_level_bound=2))
                        else:
                            material_finish = DEF_MAT_NAME
                            trans = 0.0
                            tab_write(
                                "pigment{srgbt<1,1,1,%.3g} finish{%s} "
                                % (trans, safety(material_finish, ref_level_bound=2))
                            )

                            write_object_material_interior(material, mob, tab_write)
                            # write_object_material_interior(material, elems[1])
                            tab_write("radiosity{importance %3g}\n" % mob.pov.importance_value)
                            tab_write("}\n\n")  # End of Metaball block

    '''
            meta = ob.data

            # important because no elements will break parsing.
            elements = [elem for elem in meta.elements if elem.type in {'BALL', 'ELLIPSOID'}]

            if elements:
                tab_write("blob {\n")
                tab_write("threshold %.4g\n" % meta.threshold)
                importance = ob.pov.importance_value

                try:
                    material = meta.materials[0]  # lame! - blender cant do enything else.
                except:
                    material = None

                for elem in elements:
                    loc = elem.co

                    stiffness = elem.stiffness
                    if elem.use_negative:
                        stiffness = - stiffness

                    if elem.type == 'BALL':

                        tab_write("sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" %
                                 (loc.x, loc.y, loc.z, elem.radius, stiffness))

                        # After this wecould do something simple like...
                        #     "pigment {Blue} }"
                        # except we'll write the color

                    elif elem.type == 'ELLIPSOID':
                        # location is modified by scale
                        tab_write("sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" %
                                 (loc.x / elem.size_x,
                                  loc.y / elem.size_y,
                                  loc.z / elem.size_z,
                                  elem.radius, stiffness))
                        tab_write("scale <%.6g, %.6g, %.6g> \n" %
                                 (elem.size_x, elem.size_y, elem.size_z))

                if material:
                    diffuse_color = material.diffuse_color
                    trans = 1.0 - material.pov.alpha
                    if material.use_transparency and material.transparency_method == 'RAYTRACE':
                        pov_filter = material.pov_raytrace_transparency.filter * (1.0 - material.alpha)
                        trans = (1.0 - material.pov.alpha) - pov_filter
                    else:
                        pov_filter = 0.0

                    material_finish = material_names_dictionary[material.name]

                    tab_write("pigment {srgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} \n" %
                             (diffuse_color[0], diffuse_color[1], diffuse_color[2],
                              pov_filter, trans))
                    tab_write("finish {%s}\n" % safety(material_finish, ref_level_bound=2))

                else:
                    tab_write("pigment {srgb 1} \n")
                    # Write the finish last.
                    tab_write("finish {%s}\n" % (safety(DEF_MAT_NAME, ref_level_bound=2)))

                write_object_material_interior(material, elems[1])

                write_matrix(global_matrix @ ob.matrix_world)
                # Importance for radiosity sampling added here
                tab_write("radiosity { \n")
                # importance > ob.pov.importance_value
                tab_write("importance %3g \n" % importance)
                tab_write("}\n")

                tab_write("}\n")  # End of Metaball block

                if comments and len(metas) >= 1:
                    file.write("\n")
    '''

    def export_global_settings(scene):
        """write all POV global settings to exported file """
        tab_write("global_settings {\n")
        tab_write("assumed_gamma 1.0\n")
        tab_write("max_trace_level %d\n" % scene.pov.max_trace_level)

        if scene.pov.global_settings_advanced:
            if not scene.pov.radio_enable:
                file.write("    adc_bailout %.6f\n" % scene.pov.adc_bailout)
            file.write("    ambient_light <%.6f,%.6f,%.6f>\n" % scene.pov.ambient_light[:])
            file.write("    irid_wavelength <%.6f,%.6f,%.6f>\n" % scene.pov.irid_wavelength[:])
            file.write("    number_of_waves %s\n" % scene.pov.number_of_waves)
            file.write("    noise_generator %s\n" % scene.pov.noise_generator)
        if scene.pov.radio_enable:
            tab_write("radiosity {\n")
            tab_write("adc_bailout %.4g\n" % scene.pov.radio_adc_bailout)
            tab_write("brightness %.4g\n" % scene.pov.radio_brightness)
            tab_write("count %d\n" % scene.pov.radio_count)
            tab_write("error_bound %.4g\n" % scene.pov.radio_error_bound)
            tab_write("gray_threshold %.4g\n" % scene.pov.radio_gray_threshold)
            tab_write("low_error_factor %.4g\n" % scene.pov.radio_low_error_factor)
            tab_write("maximum_reuse %.4g\n" % scene.pov.radio_maximum_reuse)
            tab_write("minimum_reuse %.4g\n" % scene.pov.radio_minimum_reuse)
            tab_write("nearest_count %d\n" % scene.pov.radio_nearest_count)
            tab_write("pretrace_start %.3g\n" % scene.pov.radio_pretrace_start)
            tab_write("pretrace_end %.3g\n" % scene.pov.radio_pretrace_end)
            tab_write("recursion_limit %d\n" % scene.pov.radio_recursion_limit)
            tab_write("always_sample %d\n" % scene.pov.radio_always_sample)
            tab_write("normal %d\n" % scene.pov.radio_normal)
            tab_write("media %d\n" % scene.pov.radio_media)
            tab_write("subsurface %d\n" % scene.pov.radio_subsurface)
            tab_write("}\n")
        once_sss = 1
        once_ambient = 1
        once_photons = 1
        for material in bpy.data.materials:
            if material.pov_subsurface_scattering.use and once_sss:
                # In pov, the scale has reversed influence compared to blender. these number
                # should correct that
                tab_write(
                    "mm_per_unit %.6f\n" % (material.pov_subsurface_scattering.scale * 1000.0)
                )
                # 1000 rather than scale * (-100.0) + 15.0))

                # In POV-Ray, the scale factor for all subsurface shaders needs to be the same

                # formerly sslt_samples were multiplied by 100 instead of 10
                sslt_samples = (11 - material.pov_subsurface_scattering.error_threshold) * 10

                tab_write("subsurface { samples %d, %d }\n" % (sslt_samples, sslt_samples / 10))
                once_sss = 0

            if world and once_ambient:
                tab_write("ambient_light rgb<%.3g, %.3g, %.3g>\n" % world.pov.ambient_color[:])
                once_ambient = 0

            if scene.pov.photon_enable:
                if once_photons and (
                    material.pov.refraction_type == "2" or material.pov.photons_reflection
                ):
                    tab_write("photons {\n")
                    tab_write("spacing %.6f\n" % scene.pov.photon_spacing)
                    tab_write("max_trace_level %d\n" % scene.pov.photon_max_trace_level)
                    tab_write("adc_bailout %.3g\n" % scene.pov.photon_adc_bailout)
                    tab_write(
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
                        tab_write('save_file "%s"\n' % full_file_name)
                        scene.pov.photon_map_file = full_file_name
                    if scene.pov.photon_map_file_save_load in {'load'}:
                        full_file_name = bpy.path.abspath(scene.pov.photon_map_file)
                        if os.path.exists(full_file_name):
                            tab_write('load_file "%s"\n' % full_file_name)
                    tab_write("}\n")
                    once_photons = 0

        tab_write("}\n")

    # sel = renderable_objects(scene) #removed for booleans
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
                file.write(shading.export_pattern(texture))
            file.write("\n")
    if comments:
        file.write("\n//--Background--\n\n")

    scenography.export_world(scene.world, scene, global_matrix, tab_write)

    if comments:
        file.write("\n//--Cameras--\n\n")

    scenography.export_camera(scene, global_matrix, render, tab_write)

    if comments:
        file.write("\n//--Lamps--\n\n")

    for ob in bpy.data.objects:
        if ob.type == 'MESH':
            for mod in ob.modifiers:
                if mod.type == 'BOOLEAN' and mod.object not in csg_list:
                        csg_list.append(mod.object)
    if csg_list != []:
        csg = False
        sel = no_renderable_objects()
        #export non rendered boolean objects operands
        object_mesh_topology.export_meshes(
            preview_dir,
            file,
            scene,
            sel,
            csg,
            string_strip_hyphen,
            safety,
            write_object_modifiers,
            material_names_dictionary,
            write_object_material_interior,
            scenography.exported_lights_count,
            unpacked_images,
            image_format,
            img_map,
            img_map_transforms,
            path_image,
            smoke_path,
            global_matrix,
            write_matrix,
            using_uberpov,
            comments,
            linebreaksinlists,
            tab,
            tab_level,
            tab_write,
            info_callback,
        )

    csg = True
    sel = renderable_objects(scene)

    scenography.export_lights(
        [L for L in sel if (L.type == 'LIGHT' and L.pov.object_as != 'RAINBOW')],
        file,
        scene,
        global_matrix,
        write_matrix,
        tab_write,
    )

    if comments:
        file.write("\n//--Rainbows--\n\n")
    scenography.export_rainbows(
        [L for L in sel if (L.type == 'LIGHT' and L.pov.object_as == 'RAINBOW')],
        file,
        scene,
        global_matrix,
        write_matrix,
        tab_write,
    )

    if comments:
        file.write("\n//--Special Curves--\n\n")
    for c in sel:
        if c.is_modified(scene, 'RENDER'):
            continue  # don't export as pov curves objects with modifiers, but as mesh
        # Implicit else-if (as not skipped by previous "continue")
        if c.type == 'CURVE' and (c.pov.curveshape in {'lathe', 'sphere_sweep', 'loft', 'birail'}):
            object_curve_topology.export_curves(file, c, string_strip_hyphen, global_matrix, tab_write)

    if comments:
        file.write("\n//--Material Definitions--\n\n")
    # write a default pigment for objects with no material (comment out to show black)
    file.write("#default{ pigment{ color srgb 0.8 }}\n")
    # Convert all materials to strings we can access directly per vertex.
    # exportMaterials()
    shading.write_material(
        using_uberpov,
        DEF_MAT_NAME,
        tab_write,
        safety,
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
                    shading.write_nodes(scene, pov_mat_name, ntree, file)

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
                    using_uberpov,
                    DEF_MAT_NAME,
                    tab_write,
                    safety,
                    comments,
                    unique_name,
                    material_names_dictionary,
                    material,
                )
            # attributes are all the variables needed by the other python file...
    if comments:
        file.write("\n")

    export_meta([m for m in sel if m.type == 'META'])

    if comments:
        file.write("//--Mesh objects--\n")

    # tbefore = time.time()
    object_mesh_topology.export_meshes(
        preview_dir,
        file,
        scene,
        sel,
        csg,
        string_strip_hyphen,
        safety,
        write_object_modifiers,
        material_names_dictionary,
        write_object_material_interior,
        scenography.exported_lights_count,
        unpacked_images,
        image_format,
        img_map,
        img_map_transforms,
        path_image,
        smoke_path,
        global_matrix,
        write_matrix,
        using_uberpov,
        comments,
        linebreaksinlists,
        tab,
        tab_level,
        tab_write,
        info_callback,
    )
    # totime = time.time() - tbefore
    # print("export_meshes took" + str(totime))

    # What follow used to happen here:
    # export_camera()
    # scenography.export_world(scene.world, scene, global_matrix, tab_write)
    # export_global_settings(scene)
    # MR:..and the order was important for implementing pov 3.7 baking
    #      (mesh camera) comment for the record
    # CR: Baking should be a special case than. If "baking", than we could change the order.

    # print("pov file closed %s" % file.closed)
    file.close()
    # print("pov file closed %s" % file.closed)


def write_pov_ini(scene, filename_ini, filename_log, filename_pov, filename_image):
    """Write ini file."""
    feature_set = bpy.context.preferences.addons[__package__].preferences.branch_feature_set_povray
    using_uberpov = feature_set == 'uberpov'
    # scene = bpy.data.scenes[0]
    scene = bpy.context.scene
    render = scene.render

    x = int(render.resolution_x * render.resolution_percentage * 0.01)
    y = int(render.resolution_y * render.resolution_percentage * 0.01)

    file = open(filename_ini, "w")
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
        file.write("End_Column=%4g\n" % (render.border_max_x))

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
    # print("ini file closed %s" % file.closed)
    file.close()
    # print("ini file closed %s" % file.closed)


class PovrayRender(bpy.types.RenderEngine):
    """Define the external renderer"""

    bl_idname = 'POVRAY_RENDER'
    bl_label = "Persitence Of Vision"
    bl_use_shading_nodes_custom = False
    DELAY = 0.5

    @staticmethod
    def _locate_binary():
        """Identify POV engine"""
        addon_prefs = bpy.context.preferences.addons[__package__].preferences

        # Use the system preference if its set.
        pov_binary = addon_prefs.filepath_povray
        if pov_binary:
            if os.path.exists(pov_binary):
                return pov_binary
            # Implicit else, as here return was still not triggered:
            print("User Preferences path to povray %r NOT FOUND, checking $PATH" % pov_binary)

        # Windows Only
        # assume if there is a 64bit binary that the user has a 64bit capable OS
        if platform.startswith('win'):
            import winreg

            win_reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, "Software\\POV-Ray\\v3.7\\Windows"
            )
            win_home = winreg.QueryValueEx(win_reg_key, "Home")[0]

            # First try 64bits UberPOV
            pov_binary = os.path.join(win_home, "bin", "uberpov64.exe")
            if os.path.exists(pov_binary):
                return pov_binary

            # Then try 64bits POV
            pov_binary = os.path.join(win_home, "bin", "pvengine64.exe")
            if os.path.exists(pov_binary):
                return pov_binary

        # search the path all os's
        pov_binary_default = "povray"

        os_path_ls = os.getenv("PATH").split(':') + [""]

        for dir_name in os_path_ls:
            pov_binary = os.path.join(dir_name, pov_binary_default)
            if os.path.exists(pov_binary):
                return pov_binary
        return ""

    def _export(self, depsgraph, pov_path, image_render_path):
        """gather all necessary output files paths user defined and auto generated and export there"""

        scene = bpy.context.scene
        if scene.pov.tempfiles_enable:
            self._temp_file_in = tempfile.NamedTemporaryFile(suffix=".pov", delete=False).name
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
            # self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".tga", delete=False).name
            self._temp_file_ini = tempfile.NamedTemporaryFile(suffix=".ini", delete=False).name
            self._temp_file_log = os.path.join(tempfile.gettempdir(), "alltext.out")
        else:
            self._temp_file_in = pov_path + ".pov"
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = image_render_path + ".png"
            # self._temp_file_out = image_render_path + ".tga"
            self._temp_file_ini = pov_path + ".ini"
            log_path = bpy.path.abspath(scene.pov.scene_path).replace('\\', '/')
            self._temp_file_log = os.path.join(log_path, "alltext.out")
            '''
            self._temp_file_in = "/test.pov"
            # PNG with POV 3.7, can show the background color with alpha. In the long run using the
            # POV-Ray interactive preview like bishop 3D could solve the preview for all formats.
            self._temp_file_out = "/test.png"
            #self._temp_file_out = "/test.tga"
            self._temp_file_ini = "/test.ini"
            '''
        if scene.pov.text_block == "":

            def info_callback(txt):
                self.update_stats("", "POV-Ray 3.7: " + txt)

            # os.makedirs(user_dir, exist_ok=True)  # handled with previews
            os.makedirs(preview_dir, exist_ok=True)

            write_pov(self._temp_file_in, scene, info_callback)
        else:
            pass

    def _render(self, depsgraph):
        """Export necessary files and render image."""
        scene = bpy.context.scene
        try:
            os.remove(self._temp_file_out)  # so as not to load the old file
        except OSError:
            pass

        pov_binary = PovrayRender._locate_binary()
        if not pov_binary:
            print("POV-Ray 3.7: could not execute povray, possibly POV-Ray isn't installed")
            return False

        write_pov_ini(
            scene, self._temp_file_ini, self._temp_file_log, self._temp_file_in, self._temp_file_out
        )

        print("***-STARTING-***")

        extra_args = []

        if scene.pov.command_line_switches != "":
            for new_arg in scene.pov.command_line_switches.split(" "):
                extra_args.append(new_arg)

        self._is_windows = False
        if platform.startswith('win'):
            self._is_windows = True
            if "/EXIT" not in extra_args and not scene.pov.pov_editor:
                extra_args.append("/EXIT")
        else:
            # added -d option to prevent render window popup which leads to segfault on linux
            extra_args.append("-d")

        # Start Rendering!
        try:
            self._process = subprocess.Popen(
                [pov_binary, self._temp_file_ini] + extra_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        except OSError:
            # TODO, report api
            print("POV-Ray 3.7: could not execute '%s'" % pov_binary)
            import traceback

            traceback.print_exc()
            print("***-DONE-***")
            return False

        else:
            print("Engine ready!...")
            print("Command line arguments passed: " + str(extra_args))
            return True

        # Now that we have a valid process

    def _cleanup(self):
        """Delete temp files and unpacked ones"""
        for f in (self._temp_file_in, self._temp_file_ini, self._temp_file_out):
            for i in range(5):
                try:
                    os.unlink(f)
                    break
                except OSError:
                    # Wait a bit before retrying file might be still in use by Blender,
                    # and Windows does not know how to delete a file in use!
                    time.sleep(self.DELAY)
        for i in unpacked_images:
            for j in range(5):
                try:
                    os.unlink(i)
                    break
                except OSError:
                    # Wait a bit before retrying file might be still in use by Blender,
                    # and Windows does not know how to delete a file in use!
                    time.sleep(self.DELAY)

    def render(self, depsgraph):
        """Export necessary files from text editor and render image."""

        scene = bpy.context.scene
        r = scene.render
        x = int(r.resolution_x * r.resolution_percentage * 0.01)
        y = int(r.resolution_y * r.resolution_percentage * 0.01)
        print("***INITIALIZING***")

        # This makes some tests on the render, returning True if all goes good, and False if
        # it was finished one way or the other.
        # It also pauses the script (time.sleep())
        def _test_wait():
            time.sleep(self.DELAY)

            # User interrupts the rendering
            if self.test_break():
                try:
                    self._process.terminate()
                    print("***POV INTERRUPTED***")
                except OSError:
                    pass
                return False
            try:
                poll_result = self._process.poll()
            except AttributeError:
                print("***CHECK POV PATH IN PREFERENCES***")
                return False
            # POV process is finisehd, one way or the other
            if poll_result is not None:
                if poll_result < 0:
                    print("***POV PROCESS FAILED : %s ***" % poll_result)
                    self.update_stats("", "POV-Ray 3.7: Failed")
                return False

            return True

        if bpy.context.scene.pov.text_block != "":
            if scene.pov.tempfiles_enable:
                self._temp_file_in = tempfile.NamedTemporaryFile(suffix=".pov", delete=False).name
                self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".png", delete=False).name
                # self._temp_file_out = tempfile.NamedTemporaryFile(suffix=".tga", delete=False).name
                self._temp_file_ini = tempfile.NamedTemporaryFile(suffix=".ini", delete=False).name
                self._temp_file_log = os.path.join(tempfile.gettempdir(), "alltext.out")
            else:
                pov_path = scene.pov.text_block
                image_render_path = os.path.splitext(pov_path)[0]
                self._temp_file_out = os.path.join(preview_dir, image_render_path)
                self._temp_file_in = os.path.join(preview_dir, pov_path)
                self._temp_file_ini = os.path.join(
                    preview_dir, (os.path.splitext(self._temp_file_in)[0] + ".INI")
                )
                self._temp_file_log = os.path.join(preview_dir, "alltext.out")

            '''
            try:
                os.remove(self._temp_file_in)  # so as not to load the old file
            except OSError:
                pass
            '''
            print(scene.pov.text_block)
            text = bpy.data.texts[scene.pov.text_block]
            file = open("%s" % self._temp_file_in, "w")
            # Why are the newlines needed?
            file.write("\n")
            file.write(text.as_string())
            file.write("\n")
            file.close()

            # has to be called to update the frame on exporting animations
            scene.frame_set(scene.frame_current)

            pov_binary = PovrayRender._locate_binary()

            if not pov_binary:
                print("POV-Ray 3.7: could not execute povray, possibly POV-Ray isn't installed")
                return False

            # start ini UI options export
            self.update_stats("", "POV-Ray 3.7: Exporting ini options from Blender")

            write_pov_ini(
                scene,
                self._temp_file_ini,
                self._temp_file_log,
                self._temp_file_in,
                self._temp_file_out,
            )

            print("***-STARTING-***")

            extra_args = []

            if scene.pov.command_line_switches != "":
                for new_arg in scene.pov.command_line_switches.split(" "):
                    extra_args.append(new_arg)

            if platform.startswith('win'):
                if "/EXIT" not in extra_args and not scene.pov.pov_editor:
                    extra_args.append("/EXIT")
            else:
                # added -d option to prevent render window popup which leads to segfault on linux
                extra_args.append("-d")

            # Start Rendering!
            try:
                if scene.pov.sdl_window_enable and not platform.startswith(
                    'win'
                ):  # segfault on linux == False !!!
                    env = {'POV_DISPLAY_SCALED': 'off'}
                    env.update(os.environ)
                    self._process = subprocess.Popen(
                        [pov_binary, self._temp_file_ini],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        env=env,
                    )
                else:
                    self._process = subprocess.Popen(
                        [pov_binary, self._temp_file_ini] + extra_args,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                    )
            except OSError:
                # TODO, report api
                print("POV-Ray 3.7: could not execute '%s'" % pov_binary)
                import traceback

                traceback.print_exc()
                print("***-DONE-***")
                return False

            else:
                print("Engine ready!...")
                print("Command line arguments passed: " + str(extra_args))
                # return True
                self.update_stats("", "POV-Ray 3.7: Parsing File")

            # Indented in main function now so repeated here but still not working
            # to bring back render result to its buffer

            if os.path.exists(self._temp_file_out):
                xmin = int(r.border_min_x * x)
                ymin = int(r.border_min_y * y)
                xmax = int(r.border_max_x * x)
                ymax = int(r.border_max_y * y)
                result = self.begin_result(0, 0, x, y)
                lay = result.layers[0]

                time.sleep(self.DELAY)
                try:
                    lay.load_from_file(self._temp_file_out)
                except RuntimeError:
                    print("***POV ERROR WHILE READING OUTPUT FILE***")
                self.end_result(result)
            # print(self._temp_file_log) #bring the pov log to blender console with proper path?
            with open(
                self._temp_file_log
            ) as f:  # The with keyword automatically closes the file when you are done
                print(f.read())

            self.update_stats("", "")

            if scene.pov.tempfiles_enable or scene.pov.deletefiles_enable:
                self._cleanup()
        else:

            # WIP output format
            #         if r.image_settings.file_format == 'OPENEXR':
            #             fformat = 'EXR'
            #             render.image_settings.color_mode = 'RGBA'
            #         else:
            #             fformat = 'TGA'
            #             r.image_settings.file_format = 'TARGA'
            #             r.image_settings.color_mode = 'RGBA'

            blend_scene_name = bpy.data.filepath.split(os.path.sep)[-1].split(".")[0]
            pov_scene_name = ""
            pov_path = ""
            image_render_path = ""

            # has to be called to update the frame on exporting animations
            scene.frame_set(scene.frame_current)

            if not scene.pov.tempfiles_enable:

                # check paths
                pov_path = bpy.path.abspath(scene.pov.scene_path).replace('\\', '/')
                if pov_path == "":
                    if bpy.data.is_saved:
                        pov_path = bpy.path.abspath("//")
                    else:
                        pov_path = tempfile.gettempdir()
                elif pov_path.endswith("/"):
                    if pov_path == "/":
                        pov_path = bpy.path.abspath("//")
                    else:
                        pov_path = bpy.path.abspath(scene.pov.scene_path)

                if not os.path.exists(pov_path):
                    try:
                        os.makedirs(pov_path)
                    except BaseException as e:
                        print(e.__doc__)
                        print('An exception occurred: {}'.format(e))
                        import traceback

                        traceback.print_exc()

                        print("POV-Ray 3.7: Cannot create scenes directory: %r" % pov_path)
                        self.update_stats(
                            "", "POV-Ray 3.7: Cannot create scenes directory %r" % pov_path
                        )
                        time.sleep(2.0)
                        # return

                '''
                # Bug in POV-Ray RC3
                image_render_path = bpy.path.abspath(scene.pov.renderimage_path).replace('\\','/')
                if image_render_path == "":
                    if bpy.data.is_saved:
                        image_render_path = bpy.path.abspath("//")
                    else:
                        image_render_path = tempfile.gettempdir()
                    #print("Path: " + image_render_path)
                elif path.endswith("/"):
                    if image_render_path == "/":
                        image_render_path = bpy.path.abspath("//")
                    else:
                        image_render_path = bpy.path.abspath(scene.pov.)
                if not os.path.exists(path):
                    print("POV-Ray 3.7: Cannot find render image directory")
                    self.update_stats("", "POV-Ray 3.7: Cannot find render image directory")
                    time.sleep(2.0)
                    return
                '''

                # check name
                if scene.pov.scene_name == "":
                    if blend_scene_name != "":
                        pov_scene_name = blend_scene_name
                    else:
                        pov_scene_name = "untitled"
                else:
                    pov_scene_name = scene.pov.scene_name
                    if os.path.isfile(pov_scene_name):
                        pov_scene_name = os.path.basename(pov_scene_name)
                    pov_scene_name = pov_scene_name.split('/')[-1].split('\\')[-1]
                    if not pov_scene_name:
                        print("POV-Ray 3.7: Invalid scene name")
                        self.update_stats("", "POV-Ray 3.7: Invalid scene name")
                        time.sleep(2.0)
                        # return
                    pov_scene_name = os.path.splitext(pov_scene_name)[0]

                print("Scene name: " + pov_scene_name)
                print("Export path: " + pov_path)
                pov_path = os.path.join(pov_path, pov_scene_name)
                pov_path = os.path.realpath(pov_path)

                image_render_path = pov_path
                # print("Render Image path: " + image_render_path)

            # start export
            self.update_stats("", "POV-Ray 3.7: Exporting data from Blender")
            self._export(depsgraph, pov_path, image_render_path)
            self.update_stats("", "POV-Ray 3.7: Parsing File")

            if not self._render(depsgraph):
                self.update_stats("", "POV-Ray 3.7: Not found")
                # return

            # r = scene.render
            # compute resolution
            # x = int(r.resolution_x * r.resolution_percentage * 0.01)
            # y = int(r.resolution_y * r.resolution_percentage * 0.01)

            # Wait for the file to be created
            # XXX This is no more valid, as 3.7 always creates output file once render is finished!
            parsing = re.compile(br"= \[Parsing\.\.\.\] =")
            rendering = re.compile(br"= \[Rendering\.\.\.\] =")
            percent = re.compile(r"\(([0-9]{1,3})%\)")
            # print("***POV WAITING FOR FILE***")

            data = b""
            last_line = ""
            while _test_wait():
                # POV in Windows did not output its stdout/stderr, it displayed them in its GUI
                # But now writes file
                if self._is_windows:
                    self.update_stats("", "POV-Ray 3.7: Rendering File")
                else:
                    t_data = self._process.stdout.read(10000)
                    if not t_data:
                        continue

                    data += t_data
                    # XXX This is working for UNIX, not sure whether it might need adjustments for
                    #     other OSs
                    # First replace is for windows
                    t_data = str(t_data).replace('\\r\\n', '\\n').replace('\\r', '\r')
                    lines = t_data.split('\\n')
                    last_line += lines[0]
                    lines[0] = last_line
                    print('\n'.join(lines), end="")
                    last_line = lines[-1]

                    if rendering.search(data):
                        _pov_rendering = True
                        match = percent.findall(str(data))
                        if match:
                            self.update_stats("", "POV-Ray 3.7: Rendering File (%s%%)" % match[-1])
                        else:
                            self.update_stats("", "POV-Ray 3.7: Rendering File")

                    elif parsing.search(data):
                        self.update_stats("", "POV-Ray 3.7: Parsing File")

            if os.path.exists(self._temp_file_out):
                # print("***POV FILE OK***")
                # self.update_stats("", "POV-Ray 3.7: Rendering")

                # prev_size = -1

                xmin = int(r.border_min_x * x)
                ymin = int(r.border_min_y * y)
                xmax = int(r.border_max_x * x)
                ymax = int(r.border_max_y * y)

                # print("***POV UPDATING IMAGE***")
                result = self.begin_result(0, 0, x, y)
                # XXX, tests for border render.
                # result = self.begin_result(xmin, ymin, xmax - xmin, ymax - ymin)
                # result = self.begin_result(0, 0, xmax - xmin, ymax - ymin)
                lay = result.layers[0]

                # This assumes the file has been fully written We wait a bit, just in case!
                time.sleep(self.DELAY)
                try:
                    lay.load_from_file(self._temp_file_out)
                    # XXX, tests for border render.
                    # lay.load_from_file(self._temp_file_out, xmin, ymin)
                except RuntimeError:
                    print("***POV ERROR WHILE READING OUTPUT FILE***")

                # Not needed right now, might only be useful if we find a way to use temp raw output of
                # pov 3.7 (in which case it might go under _test_wait()).
                '''
                def update_image():
                    # possible the image wont load early on.
                    try:
                        lay.load_from_file(self._temp_file_out)
                        # XXX, tests for border render.
                        #lay.load_from_file(self._temp_file_out, xmin, ymin)
                        #lay.load_from_file(self._temp_file_out, xmin, ymin)
                    except RuntimeError:
                        pass

                # Update while POV-Ray renders
                while True:
                    # print("***POV RENDER LOOP***")

                    # test if POV-Ray exists
                    if self._process.poll() is not None:
                        print("***POV PROCESS FINISHED***")
                        update_image()
                        break

                    # user exit
                    if self.test_break():
                        try:
                            self._process.terminate()
                            print("***POV PROCESS INTERRUPTED***")
                        except OSError:
                            pass

                        break

                    # Would be nice to redirect the output
                    # stdout_value, stderr_value = self._process.communicate() # locks

                    # check if the file updated
                    new_size = os.path.getsize(self._temp_file_out)

                    if new_size != prev_size:
                        update_image()
                        prev_size = new_size

                    time.sleep(self.DELAY)
                '''

                self.end_result(result)

            else:
                print("***POV FILE NOT FOUND***")

            print("***POV FILE FINISHED***")

            # print(filename_log) #bring the pov log to blender console with proper path?
            with open(
                self._temp_file_log, encoding='utf-8'
            ) as f:  # The with keyword automatically closes the file when you are done
                msg = f.read()
                # if isinstance(msg, str):
                # stdmsg = msg
                # decoded = False
                # else:
                # if type(msg) == bytes:
                # stdmsg = msg.split('\n')
                # stdmsg = msg.encode('utf-8', "replace")
                # stdmsg = msg.encode("utf-8", "replace")

                # stdmsg = msg.decode(encoding)
                # decoded = True
                # msg.encode('utf-8').decode('utf-8')
                msg.replace("\t", "    ")
                print(msg)
                # Also print to the interactive console used in POV centric workspace
                # To do: get a grip on new line encoding
                # and make this a function to be used elsewhere
                for win in bpy.context.window_manager.windows:
                    if win.screen is not None:
                        scr = win.screen
                        for area in scr.areas:
                            if area.type == 'CONSOLE':
                                # pass # XXX temp override
                                # context override
                                # ctx = {'window': win, 'screen': scr, 'area':area}#bpy.context.copy()
                                try:
                                    ctx = {}
                                    ctx['area'] = area
                                    ctx['region'] = area.regions[-1]
                                    ctx['space_data'] = area.spaces.active
                                    ctx['screen'] = scr  # C.screen
                                    ctx['window'] = win

                                    # bpy.ops.console.banner(ctx, text = "Hello world")
                                    bpy.ops.console.clear_line(ctx)
                                    stdmsg = msg.split('\n')  # XXX todo , test and see segfault crash?
                                    for i in stdmsg:
                                        # Crashes if no Terminal displayed on Windows
                                        bpy.ops.console.scrollback_append(ctx, text=i, type='INFO')
                                        # bpy.ops.console.insert(ctx, text=(i + "\n"))
                                except BaseException as e:
                                    print(e.__doc__)
                                    print('An exception occurred: {}'.format(e))
                                    pass

            self.update_stats("", "")

            if scene.pov.tempfiles_enable or scene.pov.deletefiles_enable:
                self._cleanup()

            sound_on = bpy.context.preferences.addons[__package__].preferences.use_sounds
            finished_render_message = "\'Render completed\'"

            if platform.startswith('win') and sound_on:
                # Could not find tts Windows command so playing beeps instead :-)
                # "Korobeiniki"(Коробе́йники)
                # aka "A-Type" Tetris theme
                import winsound

                winsound.Beep(494, 250)  # B
                winsound.Beep(370, 125)  # F
                winsound.Beep(392, 125)  # G
                winsound.Beep(440, 250)  # A
                winsound.Beep(392, 125)  # G
                winsound.Beep(370, 125)  # F#
                winsound.Beep(330, 275)  # E
                winsound.Beep(330, 125)  # E
                winsound.Beep(392, 125)  # G
                winsound.Beep(494, 275)  # B
                winsound.Beep(440, 125)  # A
                winsound.Beep(392, 125)  # G
                winsound.Beep(370, 275)  # F
                winsound.Beep(370, 125)  # F
                winsound.Beep(392, 125)  # G
                winsound.Beep(440, 250)  # A
                winsound.Beep(494, 250)  # B
                winsound.Beep(392, 250)  # G
                winsound.Beep(330, 350)  # E
                time.sleep(0.5)
                winsound.Beep(440, 250)  # A
                winsound.Beep(440, 150)  # A
                winsound.Beep(523, 125)  # D8
                winsound.Beep(659, 250)  # E8
                winsound.Beep(587, 125)  # D8
                winsound.Beep(523, 125)  # C8
                winsound.Beep(494, 250)  # B
                winsound.Beep(494, 125)  # B
                winsound.Beep(392, 125)  # G
                winsound.Beep(494, 250)  # B
                winsound.Beep(440, 150)  # A
                winsound.Beep(392, 125)  # G
                winsound.Beep(370, 250)  # F#
                winsound.Beep(370, 125)  # F#
                winsound.Beep(392, 125)  # G
                winsound.Beep(440, 250)  # A
                winsound.Beep(494, 250)  # B
                winsound.Beep(392, 250)  # G
                winsound.Beep(330, 300)  # E

            # Mac supports natively say command
            elif platform == "darwin":
                # We don't want the say command to block Python,
                # so we add an ampersand after the message
                os.system("say %s &" % (finished_render_message))

            # While Linux frequently has espeak installed or at least can suggest
            # Maybe windows could as well ?
            elif platform == "linux":
                # We don't want the say command to block Python,
                # so we add an ampersand after the message
                os.system("echo %s | espeak &" % (finished_render_message))


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
        file_ini = open("%s" % ini_prev_file, "w")
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
        file_ini.close()
        # ---------------------------------- pov ---------------------------------- #
        file_pov = open("%s" % input_prev_file, "w")
        pat_name = "PAT_" + string_strip_hyphen(bpy.path.clean_name(tex.name))
        file_pov.write("#declare %s = \n" % pat_name)
        file_pov.write(shading.export_pattern(tex))

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
        file_pov.close()
        # ------------------------------- end write ------------------------------- #

        pov_binary = PovrayRender._locate_binary()

        if platform.startswith('win'):
            p1 = subprocess.Popen(
                ["%s" % pov_binary, "/EXIT", "%s" % ini_prev_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
        else:
            p1 = subprocess.Popen(
                ["%s" % pov_binary, "-d", "%s" % ini_prev_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
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

        # empty text name property engain
        scene.pov.text_block = ""
        return {'FINISHED'}


classes = (
    PovrayRender,
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
