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

"""Translate complex shaders to exported POV textures."""

import bpy


def write_object_material_interior(material, ob, tab_write):
    """Translate some object level material from Blender UI (VS data level)

    to POV interior{} syntax and write it to exported file.
    This is called in object_mesh_topology.export_meshes
    """
    # DH - modified some variables to be function local, avoiding RNA write
    # this should be checked to see if it is functionally correct

    # Commented out: always write IOR to be able to use it for SSS, Fresnel reflections...
    # if material and material.transparency_method == 'RAYTRACE':
    if material:
        # But there can be only one!
        if material.pov_subsurface_scattering.use:  # SSS IOR get highest priority
            tab_write("interior {\n")
            tab_write("ior %.6f\n" % material.pov_subsurface_scattering.ior)
        # Then the raytrace IOR taken from raytrace transparency properties and used for
        # reflections if IOR Mirror option is checked.
        elif material.pov.mirror_use_IOR:
            tab_write("interior {\n")
            tab_write("ior %.6f\n" % material.pov_raytrace_transparency.ior)
        elif material.pov.transparency_method == 'Z_TRANSPARENCY':
            tab_write("interior {\n")
            tab_write("ior 1.0\n")
        else:
            tab_write("interior {\n")
            tab_write("ior %.6f\n" % material.pov_raytrace_transparency.ior)

        pov_fake_caustics = False
        pov_photons_refraction = False
        pov_photons_reflection = False

        if material.pov.photons_reflection:
            pov_photons_reflection = True
        if not material.pov.refraction_caustics:
            pov_fake_caustics = False
            pov_photons_refraction = False
        elif material.pov.refraction_type == "1":
            pov_fake_caustics = True
            pov_photons_refraction = False
        elif material.pov.refraction_type == "2":
            pov_fake_caustics = False
            pov_photons_refraction = True

        # If only Raytrace transparency is set, its IOR will be used for refraction, but user
        # can set up 'un-physical' fresnel reflections in raytrace mirror parameters.
        # Last, if none of the above is specified, user can set up 'un-physical' fresnel
        # reflections in raytrace mirror parameters. And pov IOR defaults to 1.
        if material.pov.caustics_enable:
            if pov_fake_caustics:
                tab_write("caustics %.3g\n" % material.pov.fake_caustics_power)
            if pov_photons_refraction:
                # Default of 1 means no dispersion
                tab_write("dispersion %.6f\n" % material.pov.photons_dispersion)
                tab_write("dispersion_samples %.d\n" % material.pov.photons_dispersion_samples)
        # TODO
        # Other interior args
        if material.pov.use_transparency and material.pov.transparency_method == 'RAYTRACE':
            # fade_distance
            # In Blender this value has always been reversed compared to what tooltip says.
            # 100.001 rather than 100 so that it does not get to 0
            # which deactivates the feature in POV
            tab_write(
                "fade_distance %.3g\n" % (100.001 - material.pov_raytrace_transparency.depth_max)
            )
            # fade_power
            tab_write("fade_power %.3g\n" % material.pov_raytrace_transparency.falloff)
            # fade_color
            tab_write("fade_color <%.3g, %.3g, %.3g>\n" % material.pov.interior_fade_color[:])

        # (variable) dispersion_samples (constant count for now)
        tab_write("}\n")
        if material.pov.photons_reflection or material.pov.refraction_type == "2":
            tab_write("photons{")
            tab_write("target %.3g\n" % ob.pov.spacing_multiplier)
            if not ob.pov.collect_photons:
                tab_write("collect off\n")
            if pov_photons_refraction:
                tab_write("refraction on\n")
            if pov_photons_reflection:
                tab_write("reflection on\n")
            tab_write("}\n")


def write_material(
    using_uberpov,
    DEF_MAT_NAME,
    tab_write,
    safety,
    comments,
    unique_name,
    material_names_dictionary,
    material
):
    """Translate Blender material to POV texture{} block and write in exported file."""
    # Assumes only called once on each material
    if material:
        name_orig = material.name
        name = material_names_dictionary[name_orig] = unique_name(
            bpy.path.clean_name(name_orig), material_names_dictionary
        )
        # If saturation(.s) is not zero, then color is not grey, and has a tint
        colored_specular_found = (material.pov.specular_color.s > 0.0) and (
            material.pov.diffuse_shader != "MINNAERT"
        )
    else:
        name = name_orig = DEF_MAT_NAME

    ##################
    # Several versions of the finish: ref_level_bound conditions are variations for specular/Mirror
    # texture channel map with alternative finish of 0 specular and no mirror reflection.
    # ref_level_bound=1 Means No specular nor Mirror reflection
    # ref_level_bound=2 Means translation of spec and mir levels for when no map influences them
    # ref_level_bound=3 Means Maximum Spec and Mirror

    def pov_has_no_specular_maps(ref_level_bound):
        """Translate Blender specular map influence to POV finish map trick and write to file."""
        if ref_level_bound == 1:
            if comments:
                tab_write("//--No specular nor Mirror reflection--\n")
            else:
                tab_write("\n")
            tab_write("#declare %s = finish {\n" % safety(name, ref_level_bound=1))

        elif ref_level_bound == 2:
            if comments:
                tab_write(
                    "//--translation of spec and mir levels for when no map " "influences them--\n"
                )
            else:
                tab_write("\n")
            tab_write("#declare %s = finish {\n" % safety(name, ref_level_bound=2))

        elif ref_level_bound == 3:
            if comments:
                tab_write("//--Maximum Spec and Mirror--\n")
            else:
                tab_write("\n")
            tab_write("#declare %s = finish {\n" % safety(name, ref_level_bound=3))
        if material:
            # POV-Ray 3.7 now uses two diffuse values respectively for front and back shading
            # (the back diffuse is like blender translucency)
            front_diffuse = material.pov.diffuse_intensity
            back_diffuse = material.pov.translucency

            if material.pov.conserve_energy:

                # Total should not go above one
                if (front_diffuse + back_diffuse) <= 1.0:
                    pass
                elif front_diffuse == back_diffuse:
                    # Try to respect the user's 'intention' by comparing the two values but
                    # bringing the total back to one.
                    front_diffuse = back_diffuse = 0.5
                # Let the highest value stay the highest value.
                elif front_diffuse > back_diffuse:
                    # clamps the sum below 1
                    back_diffuse = min(back_diffuse, (1.0 - front_diffuse))
                else:
                    front_diffuse = min(front_diffuse, (1.0 - back_diffuse))

            # map hardness between 0.0 and 1.0
            roughness = 1.0 - ((material.pov.specular_hardness - 1.0) / 510.0)
            ## scale from 0.0 to 0.1
            roughness *= 0.1
            # add a small value because 0.0 is invalid.
            roughness += 1.0 / 511.0

            # ------------------------------ Diffuse Shader ------------------------------ #
            # Not used for Full spec (ref_level_bound=3) of the shader.
            if material.pov.diffuse_shader == "OREN_NAYAR" and ref_level_bound != 3:
                # Blender roughness is what is generally called oren nayar Sigma,
                # and brilliance in POV-Ray.
                tab_write("brilliance %.3g\n" % (0.9 + material.roughness))

            if material.pov.diffuse_shader == "TOON" and ref_level_bound != 3:
                tab_write("brilliance %.3g\n" % (0.01 + material.diffuse_toon_smooth * 0.25))
                # Lower diffuse and increase specular for toon effect seems to look better
                # in POV-Ray.
                front_diffuse *= 0.5

            if material.pov.diffuse_shader == "MINNAERT" and ref_level_bound != 3:
                # tab_write("aoi %.3g\n" % material.darkness)
                pass  # let's keep things simple for now
            if material.pov.diffuse_shader == "FRESNEL" and ref_level_bound != 3:
                # tab_write("aoi %.3g\n" % material.diffuse_fresnel_factor)
                pass  # let's keep things simple for now
            if material.pov.diffuse_shader == "LAMBERT" and ref_level_bound != 3:
                # trying to best match lambert attenuation by that constant brilliance value
                tab_write("brilliance 1\n")

            if ref_level_bound == 2:
                # ------------------------------ Specular Shader ------------------------------ #
                # No difference between phong and cook torrence in blender HaHa!
                if (
                    material.pov.specular_shader == "COOKTORR"
                    or material.pov.specular_shader == "PHONG"
                ):
                    tab_write("phong %.3g\n" % (material.pov.specular_intensity))
                    tab_write("phong_size %.3g\n" % (material.pov.specular_hardness / 3.14))

                # POV-Ray 'specular' keyword corresponds to a Blinn model, without the ior.
                elif material.pov.specular_shader == "BLINN":
                    # Use blender Blinn's IOR just as some factor for spec intensity
                    tab_write(
                        "specular %.3g\n"
                        % (material.pov.specular_intensity * (material.pov.specular_ior / 4.0))
                    )
                    tab_write("roughness %.3g\n" % roughness)
                    # Could use brilliance 2(or varying around 2 depending on ior or factor) too.

                elif material.pov.specular_shader == "TOON":
                    tab_write("phong %.3g\n" % (material.pov.specular_intensity * 2.0))
                    # use extreme phong_size
                    tab_write("phong_size %.3g\n" % (0.1 + material.pov.specular_toon_smooth / 2.0))

                elif material.pov.specular_shader == "WARDISO":
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(
                        "specular %.3g\n"
                        % (material.pov.specular_intensity / (material.pov.specular_slope + 0.0005))
                    )
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write("roughness %.4g\n" % (0.0005 + material.pov.specular_slope / 10.0))
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write("brilliance %.4g\n" % (1.8 - material.pov.specular_slope * 1.8))

            # -------------------------------------------------------------------------------- #
            elif ref_level_bound == 1:
                if (
                    material.pov.specular_shader == "COOKTORR"
                    or material.pov.specular_shader == "PHONG"
                ):
                    tab_write("phong 0\n")  #%.3g\n" % (material.pov.specular_intensity/5))
                    tab_write("phong_size %.3g\n" % (material.pov.specular_hardness / 3.14))

                # POV-Ray 'specular' keyword corresponds to a Blinn model, without the ior.
                elif material.pov.specular_shader == "BLINN":
                    # Use blender Blinn's IOR just as some factor for spec intensity
                    tab_write(
                        "specular %.3g\n"
                        % (material.pov.specular_intensity * (material.pov.specular_ior / 4.0))
                    )
                    tab_write("roughness %.3g\n" % roughness)
                    # Could use brilliance 2(or varying around 2 depending on ior or factor) too.

                elif material.pov.specular_shader == "TOON":
                    tab_write("phong %.3g\n" % (material.pov.specular_intensity * 2.0))
                    # use extreme phong_size
                    tab_write("phong_size %.3g\n" % (0.1 + material.pov.specular_toon_smooth / 2.0))

                elif material.pov.specular_shader == "WARDISO":
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(
                        "specular %.3g\n"
                        % (material.pov.specular_intensity / (material.pov.specular_slope + 0.0005))
                    )
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write("roughness %.4g\n" % (0.0005 + material.pov.specular_slope / 10.0))
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write("brilliance %.4g\n" % (1.8 - material.pov.specular_slope * 1.8))
            elif ref_level_bound == 3:
                # Spec must be Max at ref_level_bound 3 so that white of mixing texture always shows specularity
                # That's why it's multiplied by 255. maybe replace by texture's brightest pixel value?
                tab_write(
                    "specular %.3g\n"
                    % (
                        (material.pov.specular_intensity * material.pov.specular_color.v)
                        * (255 * slot.specular_factor)
                    )
                )
                tab_write("roughness %.3g\n" % (1 / material.pov.specular_hardness))
            tab_write("diffuse %.3g %.3g\n" % (front_diffuse, back_diffuse))

            tab_write("ambient %.3g\n" % material.pov.ambient)
            # POV-Ray blends the global value
            # tab_write("ambient rgb <%.3g, %.3g, %.3g>\n" % \
            #         tuple([c*material.pov.ambient for c in world.ambient_color]))
            tab_write("emission %.3g\n" % material.pov.emit)  # New in POV-Ray 3.7

            # POV-Ray just ignores roughness if there's no specular keyword
            # tab_write("roughness %.3g\n" % roughness)

            if material.pov.conserve_energy:
                # added for more realistic shading. Needs some checking to see if it
                # really works. --Maurice.
                tab_write("conserve_energy\n")

            if colored_specular_found:
                tab_write("metallic\n")

            # 'phong 70.0 '
            if ref_level_bound != 1:
                if material.pov_raytrace_mirror.use:
                    raytrace_mirror = material.pov_raytrace_mirror
                    if raytrace_mirror.reflect_factor:
                        tab_write("reflection {\n")
                        tab_write("rgb <%.3g, %.3g, %.3g>\n" % material.pov.mirror_color[:])
                        if material.pov.mirror_metallic:
                            tab_write("metallic %.3g\n" % (raytrace_mirror.reflect_factor))
                        # Blurry reflections for UberPOV
                        if using_uberpov and raytrace_mirror.gloss_factor < 1.0:
                            # tab_write("#ifdef(unofficial) #if(unofficial = \"patch\") #if(patch(\"upov-reflection-roughness\") > 0)\n")
                            tab_write(
                                "roughness %.6f\n" % (0.000001 / raytrace_mirror.gloss_factor)
                            )
                            # tab_write("#end #end #end\n") # This and previous comment for backward compatibility, messier pov code
                        if material.pov.mirror_use_IOR:  # WORKING ?
                            # Removed from the line below: gives a more physically correct
                            # material but needs proper IOR. --Maurice
                            tab_write("fresnel 1 ")
                        tab_write(
                            "falloff %.3g exponent %.3g} "
                            % (raytrace_mirror.fresnel, raytrace_mirror.fresnel_factor)
                        )

            if material.pov_subsurface_scattering.use:
                subsurface_scattering = material.pov_subsurface_scattering
                tab_write(
                    "subsurface { translucency <%.3g, %.3g, %.3g> }\n"
                    % (
                        (subsurface_scattering.radius[0]),
                        (subsurface_scattering.radius[1]),
                        (subsurface_scattering.radius[2]),
                    )
                )

            if material.pov.irid_enable:
                tab_write(
                    "irid { %.4g thickness %.4g turbulence %.4g }"
                    % (
                        material.pov.irid_amount,
                        material.pov.irid_thickness,
                        material.pov.irid_turbulence,
                    )
                )

        else:
            tab_write("diffuse 0.8\n")
            tab_write("phong 70.0\n")

            # tab_write("specular 0.2\n")

        # This is written into the object
        """
        if material and material.pov.transparency_method=='RAYTRACE':
            'interior { ior %.3g} ' % material.raytrace_transparency.ior
        """

        # tab_write("crand 1.0\n") # Sand granyness
        # tab_write("metallic %.6f\n" % material.spec)
        # tab_write("phong %.6f\n" % material.spec)
        # tab_write("phong_size %.6f\n" % material.spec)
        # tab_write("brilliance %.6f " % (material.pov.specular_hardness/256.0) # Like hardness

        tab_write("}\n\n")

    # ref_level_bound=2 Means translation of spec and mir levels for when no map influences them
    pov_has_no_specular_maps(ref_level_bound=2)

    if material:
        special_texture_found = False
        tmpidx = -1
        for t in material.pov_texture_slots:
            tmpidx += 1
            # index = material.pov.active_texture_index
            slot = material.pov_texture_slots[tmpidx]  # [index]
            povtex = slot.texture  # slot.name
            tex = bpy.data.textures[povtex]

            if t and t.use and tex is not None:

                if (tex.type == "IMAGE" and tex.image) or tex.type != "IMAGE":
                    # validPath
                    if (
                        t
                        and t.use
                        and (
                            t.use_map_specular
                            or t.use_map_raymir
                            or t.use_map_normal
                            or t.use_map_alpha
                        )
                    ):
                        special_texture_found = True
                        continue  # Some texture found

        if special_texture_found or colored_specular_found:
            # ref_level_bound=1 Means No specular nor Mirror reflection
            pov_has_no_specular_maps(ref_level_bound=1)

            # ref_level_bound=3 Means Maximum Spec and Mirror
            pov_has_no_specular_maps(ref_level_bound=3)


def export_pattern(texture):
    """Translate Blender procedural textures to POV patterns and write to pov file.

    Function Patterns can be used to better access sub components of a pattern like
    grey values for influence mapping
    """
    tex = texture
    pat = tex.pov
    pat_name = "PAT_%s" % string_strip_hyphen(bpy.path.clean_name(tex.name))
    mapping_dif = "translate <%.4g,%.4g,%.4g> scale <%.4g,%.4g,%.4g>" % (
        pat.tex_mov_x,
        pat.tex_mov_y,
        pat.tex_mov_z,
        1.0 / pat.tex_scale_x,
        1.0 / pat.tex_scale_y,
        1.0 / pat.tex_scale_z,
    )
    text_strg = ""

    def export_color_ramp(texture):
        tex = texture
        pat = tex.pov
        col_ramp_strg = "color_map {\n"
        num_color = 0
        for el in tex.color_ramp.elements:
            num_color += 1
            pos = el.position
            col = el.color
            col_r, col_g, col_b, col_a = col[0], col[1], col[2], 1 - col[3]
            if pat.tex_pattern_type not in {"checker", "hexagon", "square", "triangular", "brick"}:
                col_ramp_strg += "[%.4g color rgbf<%.4g,%.4g,%.4g,%.4g>] \n" % (
                    pos,
                    col_r,
                    col_g,
                    col_b,
                    col_a,
                )
            if pat.tex_pattern_type in {"brick", "checker"} and num_color < 3:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)
            if pat.tex_pattern_type == "hexagon" and num_color < 4:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)
            if pat.tex_pattern_type == "square" and num_color < 5:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)
            if pat.tex_pattern_type == "triangular" and num_color < 7:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)

        col_ramp_strg += "} \n"
        # end color map
        return col_ramp_strg

    # much work to be done here only defaults translated for now:
    # pov noise_generator 3 means perlin noise
    if tex.type not in {"NONE", "IMAGE"} and pat.tex_pattern_type == "emulator":
        text_strg += "pigment {\n"
        # ------------------------- EMULATE BLENDER VORONOI TEXTURE ------------------------- #
        if tex.type == "VORONOI":
            text_strg += "crackle\n"
            text_strg += "    offset %.4g\n" % tex.nabla
            text_strg += "    form <%.4g,%.4g,%.4g>\n" % (tex.weight_1, tex.weight_2, tex.weight_3)
            if tex.distance_metric == "DISTANCE":
                text_strg += "    metric 2.5\n"
            if tex.distance_metric == "DISTANCE_SQUARED":
                text_strg += "    metric 2.5\n"
                text_strg += "    poly_wave 2\n"
            if tex.distance_metric == "MINKOVSKY":
                text_strg += "    metric %s\n" % tex.minkovsky_exponent
            if tex.distance_metric == "MINKOVSKY_FOUR":
                text_strg += "    metric 4\n"
            if tex.distance_metric == "MINKOVSKY_HALF":
                text_strg += "    metric 0.5\n"
            if tex.distance_metric == "CHEBYCHEV":
                text_strg += "    metric 10\n"
            if tex.distance_metric == "MANHATTAN":
                text_strg += "    metric 1\n"

            if tex.color_mode == "POSITION":
                text_strg += "solid\n"
            text_strg += "scale 0.25\n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += "color_map {\n"
                text_strg += "[0 color rgbt<0,0,0,1>]\n"
                text_strg += "[1 color rgbt<1,1,1,0>]\n"
                text_strg += "}\n"

        # ------------------------- EMULATE BLENDER CLOUDS TEXTURE ------------------------- #
        if tex.type == "CLOUDS":
            if tex.noise_type == "SOFT_NOISE":
                text_strg += "wrinkles\n"
                text_strg += "scale 0.25\n"
            else:
                text_strg += "granite\n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += "color_map {\n"
                text_strg += "[0 color rgbt<0,0,0,1>]\n"
                text_strg += "[1 color rgbt<1,1,1,0>]\n"
                text_strg += "}\n"

        # ------------------------- EMULATE BLENDER WOOD TEXTURE ------------------------- #
        if tex.type == "WOOD":
            if tex.wood_type == "RINGS":
                text_strg += "wood\n"
                text_strg += "scale 0.25\n"
            if tex.wood_type == "RINGNOISE":
                text_strg += "wood\n"
                text_strg += "scale 0.25\n"
                text_strg += "turbulence %.4g\n" % (tex.turbulence / 100)
            if tex.wood_type == "BANDS":
                text_strg += "marble\n"
                text_strg += "scale 0.25\n"
                text_strg += "rotate <45,-45,45>\n"
            if tex.wood_type == "BANDNOISE":
                text_strg += "marble\n"
                text_strg += "scale 0.25\n"
                text_strg += "rotate <45,-45,45>\n"
                text_strg += "turbulence %.4g\n" % (tex.turbulence / 10)

            if tex.noise_basis_2 == "SIN":
                text_strg += "sine_wave\n"
            if tex.noise_basis_2 == "TRI":
                text_strg += "triangle_wave\n"
            if tex.noise_basis_2 == "SAW":
                text_strg += "ramp_wave\n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += "color_map {\n"
                text_strg += "[0 color rgbt<0,0,0,0>]\n"
                text_strg += "[1 color rgbt<1,1,1,0>]\n"
                text_strg += "}\n"

        # ------------------------- EMULATE BLENDER STUCCI TEXTURE ------------------------- #
        if tex.type == "STUCCI":
            text_strg += "bozo\n"
            text_strg += "scale 0.25\n"
            if tex.noise_type == "HARD_NOISE":
                text_strg += "triangle_wave\n"
                if tex.use_color_ramp:
                    text_strg += export_color_ramp(tex)
                else:
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbf<1,1,1,0>]\n"
                    text_strg += "[1 color rgbt<0,0,0,1>]\n"
                    text_strg += "}\n"
            else:
                if tex.use_color_ramp:
                    text_strg += export_color_ramp(tex)
                else:
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbf<0,0,0,1>]\n"
                    text_strg += "[1 color rgbt<1,1,1,0>]\n"
                    text_strg += "}\n"

        # ------------------------- EMULATE BLENDER MAGIC TEXTURE ------------------------- #
        if tex.type == "MAGIC":
            text_strg += "leopard\n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += "color_map {\n"
                text_strg += "[0 color rgbt<1,1,1,0.5>]\n"
                text_strg += "[0.25 color rgbf<0,1,0,0.75>]\n"
                text_strg += "[0.5 color rgbf<0,0,1,0.75>]\n"
                text_strg += "[0.75 color rgbf<1,0,1,0.75>]\n"
                text_strg += "[1 color rgbf<0,1,0,0.75>]\n"
                text_strg += "}\n"
            text_strg += "scale 0.1\n"

        # ------------------------- EMULATE BLENDER MARBLE TEXTURE ------------------------- #
        if tex.type == "MARBLE":
            text_strg += "marble\n"
            text_strg += "turbulence 0.5\n"
            text_strg += "noise_generator 3\n"
            text_strg += "scale 0.75\n"
            text_strg += "rotate <45,-45,45>\n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                if tex.marble_type == "SOFT":
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbt<0,0,0,0>]\n"
                    text_strg += "[0.05 color rgbt<0,0,0,0>]\n"
                    text_strg += "[1 color rgbt<0.9,0.9,0.9,0>]\n"
                    text_strg += "}\n"
                elif tex.marble_type == "SHARP":
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbt<0,0,0,0>]\n"
                    text_strg += "[0.025 color rgbt<0,0,0,0>]\n"
                    text_strg += "[1 color rgbt<0.9,0.9,0.9,0>]\n"
                    text_strg += "}\n"
                else:
                    text_strg += "[0 color rgbt<0,0,0,0>]\n"
                    text_strg += "[1 color rgbt<1,1,1,0>]\n"
                    text_strg += "}\n"
            if tex.noise_basis_2 == "SIN":
                text_strg += "sine_wave\n"
            if tex.noise_basis_2 == "TRI":
                text_strg += "triangle_wave\n"
            if tex.noise_basis_2 == "SAW":
                text_strg += "ramp_wave\n"

        # ------------------------- EMULATE BLENDER BLEND TEXTURE ------------------------- #
        if tex.type == "BLEND":
            if tex.progression == "RADIAL":
                text_strg += "radial\n"
                if tex.use_flip_axis == "HORIZONTAL":
                    text_strg += "rotate x*90\n"
                else:
                    text_strg += "rotate <-90,0,90>\n"
                text_strg += "ramp_wave\n"
            elif tex.progression == "SPHERICAL":
                text_strg += "spherical\n"
                text_strg += "scale 3\n"
                text_strg += "poly_wave 1\n"
            elif tex.progression == "QUADRATIC_SPHERE":
                text_strg += "spherical\n"
                text_strg += "scale 3\n"
                text_strg += "    poly_wave 2\n"
            elif tex.progression == "DIAGONAL":
                text_strg += "gradient <1,1,0>\n"
                text_strg += "scale 3\n"
            elif tex.use_flip_axis == "HORIZONTAL":
                text_strg += "gradient x\n"
                text_strg += "scale 2.01\n"
            elif tex.use_flip_axis == "VERTICAL":
                text_strg += "gradient y\n"
                text_strg += "scale 2.01\n"
            # text_strg+="ramp_wave\n"
            # text_strg+="frequency 0.5\n"
            text_strg += "phase 0.5\n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += "color_map {\n"
                text_strg += "[0 color rgbt<1,1,1,0>]\n"
                text_strg += "[1 color rgbf<0,0,0,1>]\n"
                text_strg += "}\n"
            if tex.progression == "LINEAR":
                text_strg += "    poly_wave 1\n"
            if tex.progression == "QUADRATIC":
                text_strg += "    poly_wave 2\n"
            if tex.progression == "EASING":
                text_strg += "    poly_wave 1.5\n"

        # ------------------------- EMULATE BLENDER MUSGRAVE TEXTURE ------------------------- #
        # if tex.type == 'MUSGRAVE':
        # text_strg+="function{ f_ridged_mf( x, y, 0, 1, 2, 9, -0.5, 3,3 )*0.5}\n"
        # text_strg+="color_map {\n"
        # text_strg+="[0 color rgbf<0,0,0,1>]\n"
        # text_strg+="[1 color rgbf<1,1,1,0>]\n"
        # text_strg+="}\n"
        # simplified for now:

        if tex.type == "MUSGRAVE":
            text_strg += "bozo scale 0.25 \n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += (
                    "color_map {[0.5 color rgbf<0,0,0,1>][1 color rgbt<1,1,1,0>]}ramp_wave \n"
                )

        # ------------------------- EMULATE BLENDER DISTORTED NOISE TEXTURE ------------------------- #
        if tex.type == "DISTORTED_NOISE":
            text_strg += "average\n"
            text_strg += "  pigment_map {\n"
            text_strg += "  [1 bozo scale 0.25 turbulence %.4g\n" % tex.distortion
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += "color_map {\n"
                text_strg += "[0 color rgbt<1,1,1,0>]\n"
                text_strg += "[1 color rgbf<0,0,0,1>]\n"
                text_strg += "}\n"
            text_strg += "]\n"

            if tex.noise_distortion == "CELL_NOISE":
                text_strg += "  [1 cells scale 0.1\n"
                if tex.use_color_ramp:
                    text_strg += export_color_ramp(tex)
                else:
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbt<1,1,1,0>]\n"
                    text_strg += "[1 color rgbf<0,0,0,1>]\n"
                    text_strg += "}\n"
                text_strg += "]\n"
            if tex.noise_distortion == "VORONOI_CRACKLE":
                text_strg += "  [1 crackle scale 0.25\n"
                if tex.use_color_ramp:
                    text_strg += export_color_ramp(tex)
                else:
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbt<1,1,1,0>]\n"
                    text_strg += "[1 color rgbf<0,0,0,1>]\n"
                    text_strg += "}\n"
                text_strg += "]\n"
            if tex.noise_distortion in [
                "VORONOI_F1",
                "VORONOI_F2",
                "VORONOI_F3",
                "VORONOI_F4",
                "VORONOI_F2_F1",
            ]:
                text_strg += "  [1 crackle metric 2.5 scale 0.25 turbulence %.4g\n" % (
                    tex.distortion / 2
                )
                if tex.use_color_ramp:
                    text_strg += export_color_ramp(tex)
                else:
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbt<1,1,1,0>]\n"
                    text_strg += "[1 color rgbf<0,0,0,1>]\n"
                    text_strg += "}\n"
                text_strg += "]\n"
            else:
                text_strg += "  [1 wrinkles scale 0.25\n"
                if tex.use_color_ramp:
                    text_strg += export_color_ramp(tex)
                else:
                    text_strg += "color_map {\n"
                    text_strg += "[0 color rgbt<1,1,1,0>]\n"
                    text_strg += "[1 color rgbf<0,0,0,1>]\n"
                    text_strg += "}\n"
                text_strg += "]\n"
            text_strg += "  }\n"

        # ------------------------- EMULATE BLENDER NOISE TEXTURE ------------------------- #
        if tex.type == "NOISE":
            text_strg += "cells\n"
            text_strg += "turbulence 3\n"
            text_strg += "omega 3\n"
            if tex.use_color_ramp:
                text_strg += export_color_ramp(tex)
            else:
                text_strg += "color_map {\n"
                text_strg += "[0.75 color rgb<0,0,0,>]\n"
                text_strg += "[1 color rgb<1,1,1,>]\n"
                text_strg += "}\n"

        # ------------------------- IGNORE OTHER BLENDER TEXTURE ------------------------- #
        else:  # non translated textures
            pass
        text_strg += "}\n\n"

        text_strg += "#declare f%s=\n" % pat_name
        text_strg += "function{pigment{%s}}\n" % pat_name
        text_strg += "\n"

    elif pat.tex_pattern_type != "emulator":
        text_strg += "pigment {\n"
        text_strg += "%s\n" % pat.tex_pattern_type
        if pat.tex_pattern_type == "agate":
            text_strg += "agate_turb %.4g\n" % pat.modifier_turbulence
        if pat.tex_pattern_type in {"spiral1", "spiral2", "tiling"}:
            text_strg += "%s\n" % pat.modifier_numbers
        if pat.tex_pattern_type == "quilted":
            text_strg += "control0 %s control1 %s\n" % (
                pat.modifier_control0,
                pat.modifier_control1,
            )
        if pat.tex_pattern_type == "mandel":
            text_strg += "%s exponent %s \n" % (pat.f_iter, pat.f_exponent)
        if pat.tex_pattern_type == "julia":
            text_strg += "<%.4g, %.4g> %s exponent %s \n" % (
                pat.julia_complex_1,
                pat.julia_complex_2,
                pat.f_iter,
                pat.f_exponent,
            )
        if pat.tex_pattern_type == "magnet" and pat.magnet_style == "mandel":
            text_strg += "%s mandel %s \n" % (pat.magnet_type, pat.f_iter)
        if pat.tex_pattern_type == "magnet" and pat.magnet_style == "julia":
            text_strg += "%s julia <%.4g, %.4g> %s\n" % (
                pat.magnet_type,
                pat.julia_complex_1,
                pat.julia_complex_2,
                pat.f_iter,
            )
        if pat.tex_pattern_type in {"mandel", "julia", "magnet"}:
            text_strg += "interior %s, %.4g\n" % (pat.f_ior, pat.f_ior_fac)
            text_strg += "exterior %s, %.4g\n" % (pat.f_eor, pat.f_eor_fac)
        if pat.tex_pattern_type == "gradient":
            text_strg += "<%s, %s, %s> \n" % (
                pat.grad_orient_x,
                pat.grad_orient_y,
                pat.grad_orient_z,
            )
        if pat.tex_pattern_type == "pavement":
            num_tiles = pat.pave_tiles
            num_pattern = 1
            if pat.pave_sides == "4" and pat.pave_tiles == 3:
                num_pattern = pat.pave_pat_2
            if pat.pave_sides == "6" and pat.pave_tiles == 3:
                num_pattern = pat.pave_pat_3
            if pat.pave_sides == "3" and pat.pave_tiles == 4:
                num_pattern = pat.pave_pat_3
            if pat.pave_sides == "3" and pat.pave_tiles == 5:
                num_pattern = pat.pave_pat_4
            if pat.pave_sides == "4" and pat.pave_tiles == 4:
                num_pattern = pat.pave_pat_5
            if pat.pave_sides == "6" and pat.pave_tiles == 4:
                num_pattern = pat.pave_pat_7
            if pat.pave_sides == "4" and pat.pave_tiles == 5:
                num_pattern = pat.pave_pat_12
            if pat.pave_sides == "3" and pat.pave_tiles == 6:
                num_pattern = pat.pave_pat_12
            if pat.pave_sides == "6" and pat.pave_tiles == 5:
                num_pattern = pat.pave_pat_22
            if pat.pave_sides == "4" and pat.pave_tiles == 6:
                num_pattern = pat.pave_pat_35
            if pat.pave_sides == "6" and pat.pave_tiles == 6:
                num_tiles = 5
            text_strg += "number_of_sides %s number_of_tiles %s pattern %s form %s \n" % (
                pat.pave_sides,
                num_tiles,
                num_pattern,
                pat.pave_form,
            )
        # ------------------------- functions ------------------------- #
        if pat.tex_pattern_type == "function":
            text_strg += "{ %s" % pat.func_list
            text_strg += "(x"
            if pat.func_plus_x != "NONE":
                if pat.func_plus_x == "increase":
                    text_strg += "*"
                if pat.func_plus_x == "plus":
                    text_strg += "+"
                text_strg += "%.4g" % pat.func_x
            text_strg += ",y"
            if pat.func_plus_y != "NONE":
                if pat.func_plus_y == "increase":
                    text_strg += "*"
                if pat.func_plus_y == "plus":
                    text_strg += "+"
                text_strg += "%.4g" % pat.func_y
            text_strg += ",z"
            if pat.func_plus_z != "NONE":
                if pat.func_plus_z == "increase":
                    text_strg += "*"
                if pat.func_plus_z == "plus":
                    text_strg += "+"
                text_strg += "%.4g" % pat.func_z
            sort = -1
            if pat.func_list in {
                "f_comma",
                "f_crossed_trough",
                "f_cubic_saddle",
                "f_cushion",
                "f_devils_curve",
                "f_enneper",
                "f_glob",
                "f_heart",
                "f_hex_x",
                "f_hex_y",
                "f_hunt_surface",
                "f_klein_bottle",
                "f_kummer_surface_v1",
                "f_lemniscate_of_gerono",
                "f_mitre",
                "f_nodal_cubic",
                "f_noise_generator",
                "f_odd",
                "f_paraboloid",
                "f_pillow",
                "f_piriform",
                "f_quantum",
                "f_quartic_paraboloid",
                "f_quartic_saddle",
                "f_sphere",
                "f_steiners_roman",
                "f_torus_gumdrop",
                "f_umbrella",
            }:
                sort = 0
            if pat.func_list in {
                "f_bicorn",
                "f_bifolia",
                "f_boy_surface",
                "f_superellipsoid",
                "f_torus",
            }:
                sort = 1
            if pat.func_list in {
                "f_ellipsoid",
                "f_folium_surface",
                "f_hyperbolic_torus",
                "f_kampyle_of_eudoxus",
                "f_parabolic_torus",
                "f_quartic_cylinder",
                "f_torus2",
            }:
                sort = 2
            if pat.func_list in {
                "f_blob2",
                "f_cross_ellipsoids",
                "f_flange_cover",
                "f_isect_ellipsoids",
                "f_kummer_surface_v2",
                "f_ovals_of_cassini",
                "f_rounded_box",
                "f_spikes_2d",
                "f_strophoid",
            }:
                sort = 3
            if pat.func_list in {
                "f_algbr_cyl1",
                "f_algbr_cyl2",
                "f_algbr_cyl3",
                "f_algbr_cyl4",
                "f_blob",
                "f_mesh1",
                "f_poly4",
                "f_spikes",
            }:
                sort = 4
            if pat.func_list in {
                "f_devils_curve_2d",
                "f_dupin_cyclid",
                "f_folium_surface_2d",
                "f_hetero_mf",
                "f_kampyle_of_eudoxus_2d",
                "f_lemniscate_of_gerono_2d",
                "f_polytubes",
                "f_ridge",
                "f_ridged_mf",
                "f_spiral",
                "f_witch_of_agnesi",
            }:
                sort = 5
            if pat.func_list in {"f_helix1", "f_helix2", "f_piriform_2d", "f_strophoid_2d"}:
                sort = 6
            if pat.func_list == "f_helical_torus":
                sort = 7
            if sort > -1:
                text_strg += ",%.4g" % pat.func_P0
            if sort > 0:
                text_strg += ",%.4g" % pat.func_P1
            if sort > 1:
                text_strg += ",%.4g" % pat.func_P2
            if sort > 2:
                text_strg += ",%.4g" % pat.func_P3
            if sort > 3:
                text_strg += ",%.4g" % pat.func_P4
            if sort > 4:
                text_strg += ",%.4g" % pat.func_P5
            if sort > 5:
                text_strg += ",%.4g" % pat.func_P6
            if sort > 6:
                text_strg += ",%.4g" % pat.func_P7
                text_strg += ",%.4g" % pat.func_P8
                text_strg += ",%.4g" % pat.func_P9
            text_strg += ")}\n"
        # ------------------------- end functions ------------------------- #
        if pat.tex_pattern_type not in {"checker", "hexagon", "square", "triangular", "brick"}:
            text_strg += "color_map {\n"
        num_color = 0
        if tex.use_color_ramp:
            for el in tex.color_ramp.elements:
                num_color += 1
                pos = el.position
                col = el.color
                col_r, col_g, col_b, col_a = col[0], col[1], col[2], 1 - col[3]
                if pat.tex_pattern_type not in {
                    "checker",
                    "hexagon",
                    "square",
                    "triangular",
                    "brick",
                }:
                    text_strg += "[%.4g color rgbf<%.4g,%.4g,%.4g,%.4g>] \n" % (
                        pos,
                        col_r,
                        col_g,
                        col_b,
                        col_a,
                    )
                if pat.tex_pattern_type in {"brick", "checker"} and num_color < 3:
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)
                if pat.tex_pattern_type == "hexagon" and num_color < 4:
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)
                if pat.tex_pattern_type == "square" and num_color < 5:
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)
                if pat.tex_pattern_type == "triangular" and num_color < 7:
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (col_r, col_g, col_b, col_a)
        else:
            text_strg += "[0 color rgbf<0,0,0,1>]\n"
            text_strg += "[1 color rgbf<1,1,1,0>]\n"
        if pat.tex_pattern_type not in {"checker", "hexagon", "square", "triangular", "brick"}:
            text_strg += "} \n"
        if pat.tex_pattern_type == "brick":
            text_strg += "brick_size <%.4g, %.4g, %.4g> mortar %.4g \n" % (
                pat.brick_size_x,
                pat.brick_size_y,
                pat.brick_size_z,
                pat.brick_mortar,
            )
        text_strg += "%s \n" % mapping_dif
        text_strg += "rotate <%.4g,%.4g,%.4g> \n" % (pat.tex_rot_x, pat.tex_rot_y, pat.tex_rot_z)
        text_strg += "turbulence <%.4g,%.4g,%.4g> \n" % (
            pat.warp_turbulence_x,
            pat.warp_turbulence_y,
            pat.warp_turbulence_z,
        )
        text_strg += "octaves %s \n" % pat.modifier_octaves
        text_strg += "lambda %.4g \n" % pat.modifier_lambda
        text_strg += "omega %.4g \n" % pat.modifier_omega
        text_strg += "frequency %.4g \n" % pat.modifier_frequency
        text_strg += "phase %.4g \n" % pat.modifier_phase
        text_strg += "}\n\n"
        text_strg += "#declare f%s=\n" % pat_name
        text_strg += "function{pigment{%s}}\n" % pat_name
        text_strg += "\n"
    return text_strg


def string_strip_hyphen(name):
    """POV naming schemes like to conform to most restrictive charsets."""
    return name.replace("-", "")


# WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def write_nodes(scene, pov_mat_name, ntree, file):
    """Translate Blender node trees to pov and write them to file."""
    # such function local inlined import are official guidelines
    # of Blender Foundation to lighten addons footprint at startup
    from os import path

    declare_nodes = []
    scene = bpy.context.scene
    for node in ntree.nodes:
        pov_node_name = string_strip_hyphen(bpy.path.clean_name(node.name)) + "_%s" % pov_mat_name
        if node.bl_idname == "PovrayFinishNode" and node.outputs["Finish"].is_linked:
            file.write("#declare %s = finish {\n" % pov_node_name)
            emission = node.inputs["Emission"].default_value
            if node.inputs["Emission"].is_linked:
                pass
            file.write("    emission %.4g\n" % emission)
            for link in ntree.links:
                if link.to_node == node:

                    if link.from_node.bl_idname == "PovrayDiffuseNode":
                        intensity = 0
                        albedo = ""
                        brilliance = 0
                        crand = 0
                        if link.from_node.inputs["Intensity"].is_linked:
                            pass
                        else:
                            intensity = link.from_node.inputs["Intensity"].default_value
                        if link.from_node.inputs["Albedo"].is_linked:
                            pass
                        else:
                            if link.from_node.inputs["Albedo"].default_value:
                                albedo = "albedo"
                        file.write("    diffuse %s %.4g\n" % (albedo, intensity))
                        if link.from_node.inputs["Brilliance"].is_linked:
                            pass
                        else:
                            brilliance = link.from_node.inputs["Brilliance"].default_value
                        file.write("    brilliance %.4g\n" % brilliance)
                        if link.from_node.inputs["Crand"].is_linked:
                            pass
                        else:
                            crand = link.from_node.inputs["Crand"].default_value
                        if crand > 0:
                            file.write("    crand %.4g\n" % crand)

                    if link.from_node.bl_idname == "PovraySubsurfaceNode":
                        if scene.povray.sslt_enable:
                            energy = 0
                            r = g = b = 0
                            if link.from_node.inputs["Translucency"].is_linked:
                                pass
                            else:
                                r, g, b, a = link.from_node.inputs["Translucency"].default_value[:]
                            if link.from_node.inputs["Energy"].is_linked:
                                pass
                            else:
                                energy = link.from_node.inputs["Energy"].default_value
                            file.write(
                                "    subsurface { translucency <%.4g,%.4g,%.4g>*%s }\n"
                                % (r, g, b, energy)
                            )

                    if link.from_node.bl_idname in {"PovraySpecularNode", "PovrayPhongNode"}:
                        intensity = 0
                        albedo = ""
                        roughness = 0
                        metallic = 0
                        phong_size = 0
                        highlight = "specular"
                        if link.from_node.inputs["Intensity"].is_linked:
                            pass
                        else:
                            intensity = link.from_node.inputs["Intensity"].default_value

                        if link.from_node.inputs["Albedo"].is_linked:
                            pass
                        else:
                            if link.from_node.inputs["Albedo"].default_value:
                                albedo = "albedo"
                        if link.from_node.bl_idname in {"PovrayPhongNode"}:
                            highlight = "phong"
                        file.write("    %s %s %.4g\n" % (highlight, albedo, intensity))

                        if link.from_node.bl_idname in {"PovraySpecularNode"}:
                            if link.from_node.inputs["Roughness"].is_linked:
                                pass
                            else:
                                roughness = link.from_node.inputs["Roughness"].default_value
                            file.write("    roughness %.6g\n" % roughness)

                        if link.from_node.bl_idname in {"PovrayPhongNode"}:
                            if link.from_node.inputs["Size"].is_linked:
                                pass
                            else:
                                phong_size = link.from_node.inputs["Size"].default_value
                            file.write("    phong_size %s\n" % phong_size)

                        if link.from_node.inputs["Metallic"].is_linked:
                            pass
                        else:
                            metallic = link.from_node.inputs["Metallic"].default_value
                        file.write("    metallic %.4g\n" % metallic)

                    if link.from_node.bl_idname in {"PovrayMirrorNode"}:
                        file.write("    reflection {\n")
                        color = None
                        exponent = 0
                        metallic = 0
                        falloff = 0
                        fresnel = ""
                        conserve = ""
                        if link.from_node.inputs["Color"].is_linked:
                            pass
                        else:
                            color = link.from_node.inputs["Color"].default_value[:]
                        file.write("    <%.4g,%.4g,%.4g>\n" % color)

                        if link.from_node.inputs["Exponent"].is_linked:
                            pass
                        else:
                            exponent = link.from_node.inputs["Exponent"].default_value
                        file.write("    exponent %.4g\n" % exponent)

                        if link.from_node.inputs["Falloff"].is_linked:
                            pass
                        else:
                            falloff = link.from_node.inputs["Falloff"].default_value
                        file.write("    falloff %.4g\n" % falloff)

                        if link.from_node.inputs["Metallic"].is_linked:
                            pass
                        else:
                            metallic = link.from_node.inputs["Metallic"].default_value
                        file.write("    metallic %.4g" % metallic)

                        if link.from_node.inputs["Fresnel"].is_linked:
                            pass
                        else:
                            if link.from_node.inputs["Fresnel"].default_value:
                                fresnel = "fresnel"

                        if link.from_node.inputs["Conserve energy"].is_linked:
                            pass
                        else:
                            if link.from_node.inputs["Conserve energy"].default_value:
                                conserve = "conserve_energy"

                        file.write("    %s}\n    %s\n" % (fresnel, conserve))

                    if link.from_node.bl_idname == "PovrayAmbientNode":
                        ambient = (0, 0, 0)
                        if link.from_node.inputs["Ambient"].is_linked:
                            pass
                        else:
                            ambient = link.from_node.inputs["Ambient"].default_value[:]
                        file.write("    ambient <%.4g,%.4g,%.4g>\n" % ambient)

                    if link.from_node.bl_idname in {"PovrayIridescenceNode"}:
                        file.write("    irid {\n")
                        amount = 0
                        thickness = 0
                        turbulence = 0
                        if link.from_node.inputs["Amount"].is_linked:
                            pass
                        else:
                            amount = link.from_node.inputs["Amount"].default_value
                        file.write("    %.4g\n" % amount)

                        if link.from_node.inputs["Thickness"].is_linked:
                            pass
                        else:
                            exponent = link.from_node.inputs["Thickness"].default_value
                        file.write("    thickness %.4g\n" % thickness)

                        if link.from_node.inputs["Turbulence"].is_linked:
                            pass
                        else:
                            falloff = link.from_node.inputs["Turbulence"].default_value
                        file.write("    turbulence %.4g}\n" % turbulence)

            file.write("}\n")

    for node in ntree.nodes:
        pov_node_name = string_strip_hyphen(bpy.path.clean_name(node.name)) + "_%s" % pov_mat_name
        if node.bl_idname == "PovrayTransformNode" and node.outputs["Transform"].is_linked:
            tx = node.inputs["Translate x"].default_value
            ty = node.inputs["Translate y"].default_value
            tz = node.inputs["Translate z"].default_value
            rx = node.inputs["Rotate x"].default_value
            ry = node.inputs["Rotate y"].default_value
            rz = node.inputs["Rotate z"].default_value
            sx = node.inputs["Scale x"].default_value
            sy = node.inputs["Scale y"].default_value
            sz = node.inputs["Scale z"].default_value
            file.write(
                "#declare %s = transform {\n"
                "    translate<%.4g,%.4g,%.4g>\n"
                "    rotate<%.4g,%.4g,%.4g>\n"
                "    scale<%.4g,%.4g,%.4g>}\n" % (pov_node_name, tx, ty, tz, rx, ry, rz, sx, sy, sz)
            )

    for node in ntree.nodes:
        pov_node_name = string_strip_hyphen(bpy.path.clean_name(node.name)) + "_%s" % pov_mat_name
        if node.bl_idname == "PovrayColorImageNode" and node.outputs["Pigment"].is_linked:
            declare_nodes.append(node.name)
            if node.image == "":
                file.write("#declare %s = pigment { color rgb 0.8}\n" % (pov_node_name))
            else:
                im = bpy.data.images[node.image]
                if im.filepath and path.exists(bpy.path.abspath(im.filepath)):  # (os.path)
                    transform = ""
                    for link in ntree.links:
                        if (
                            link.from_node.bl_idname == "PovrayTransformNode"
                            and link.to_node == node
                        ):
                            pov_trans_name = (
                                string_strip_hyphen(bpy.path.clean_name(link.from_node.name))
                                + "_%s" % pov_mat_name
                            )
                            transform = "transform {%s}" % pov_trans_name
                    uv = ""
                    if node.map_type == "uv_mapping":
                        uv = "uv_mapping"
                    filepath = bpy.path.abspath(im.filepath)
                    file.write("#declare %s = pigment {%s image_map {\n" % (pov_node_name, uv))
                    premul = "off"
                    if node.premultiplied:
                        premul = "on"
                    once = ""
                    if node.once:
                        once = "once"
                    file.write(
                        '    "%s"\n    gamma %.6g\n    premultiplied %s\n'
                        % (filepath, node.inputs["Gamma"].default_value, premul)
                    )
                    file.write("    %s\n" % once)
                    if node.map_type != "uv_mapping":
                        file.write("    map_type %s\n" % (node.map_type))
                    file.write(
                        "    interpolate %s\n    filter all %.4g\n    transmit all %.4g\n"
                        % (
                            node.interpolate,
                            node.inputs["Filter"].default_value,
                            node.inputs["Transmit"].default_value,
                        )
                    )
                    file.write("    }\n")
                    file.write("    %s\n" % transform)
                    file.write("    }\n")

    for node in ntree.nodes:
        pov_node_name = string_strip_hyphen(bpy.path.clean_name(node.name)) + "_%s" % pov_mat_name
        if node.bl_idname == "PovrayImagePatternNode" and node.outputs["Pattern"].is_linked:
            declare_nodes.append(node.name)
            if node.image != "":
                im = bpy.data.images[node.image]
                if im.filepath and path.exists(bpy.path.abspath(im.filepath)):
                    transform = ""
                    for link in ntree.links:
                        if (
                            link.from_node.bl_idname == "PovrayTransformNode"
                            and link.to_node == node
                        ):
                            pov_trans_name = (
                                string_strip_hyphen(bpy.path.clean_name(link.from_node.name))
                                + "_%s" % pov_mat_name
                            )
                            transform = "transform {%s}" % pov_trans_name
                    uv = ""
                    if node.map_type == "uv_mapping":
                        uv = "uv_mapping"
                    filepath = bpy.path.abspath(im.filepath)
                    file.write("#macro %s() %s image_pattern {\n" % (pov_node_name, uv))
                    premul = "off"
                    if node.premultiplied:
                        premul = "on"
                    once = ""
                    if node.once:
                        once = "once"
                    file.write(
                        '    "%s"\n    gamma %.6g\n    premultiplied %s\n'
                        % (filepath, node.inputs["Gamma"].default_value, premul)
                    )
                    file.write("    %s\n" % once)
                    if node.map_type != "uv_mapping":
                        file.write("    map_type %s\n" % (node.map_type))
                    file.write("    interpolate %s\n" % node.interpolate)
                    file.write("    }\n")
                    file.write("    %s\n" % transform)
                    file.write("#end\n")

    for node in ntree.nodes:
        pov_node_name = string_strip_hyphen(bpy.path.clean_name(node.name)) + "_%s" % pov_mat_name
        if node.bl_idname == "PovrayBumpMapNode" and node.outputs["Normal"].is_linked:
            if node.image != "":
                im = bpy.data.images[node.image]
                if im.filepath and path.exists(bpy.path.abspath(im.filepath)):
                    transform = ""
                    for link in ntree.links:
                        if (
                            link.from_node.bl_idname == "PovrayTransformNode"
                            and link.to_node == node
                        ):
                            pov_trans_name = (
                                string_strip_hyphen(bpy.path.clean_name(link.from_node.name))
                                + "_%s" % pov_mat_name
                            )
                            transform = "transform {%s}" % pov_trans_name
                    uv = ""
                    if node.map_type == "uv_mapping":
                        uv = "uv_mapping"
                    filepath = bpy.path.abspath(im.filepath)
                    file.write("#declare %s = normal {%s bump_map {\n" % (pov_node_name, uv))
                    once = ""
                    if node.once:
                        once = "once"
                    file.write('    "%s"\n' % filepath)
                    file.write("    %s\n" % once)
                    if node.map_type != "uv_mapping":
                        file.write("    map_type %s\n" % (node.map_type))
                    bump_size = node.inputs["Normal"].default_value
                    if node.inputs["Normal"].is_linked:
                        pass
                    file.write(
                        "    interpolate %s\n    bump_size %.4g\n" % (node.interpolate, bump_size)
                    )
                    file.write("    }\n")
                    file.write("    %s\n" % transform)
                    file.write("    }\n")
                    declare_nodes.append(node.name)

    for node in ntree.nodes:
        pov_node_name = string_strip_hyphen(bpy.path.clean_name(node.name)) + "_%s" % pov_mat_name
        if node.bl_idname == "PovrayPigmentNode" and node.outputs["Pigment"].is_linked:
            declare_nodes.append(node.name)
            r, g, b = node.inputs["Color"].default_value[:]
            f = node.inputs["Filter"].default_value
            t = node.inputs["Transmit"].default_value
            if node.inputs["Color"].is_linked:
                pass
            file.write(
                "#declare %s = pigment{color srgbft <%.4g,%.4g,%.4g,%.4g,%.4g>}\n"
                % (pov_node_name, r, g, b, f, t)
            )

    for node in ntree.nodes:
        pov_node_name = string_strip_hyphen(bpy.path.clean_name(node.name)) + "_%s" % pov_mat_name
        if node.bl_idname == "PovrayTextureNode" and node.outputs["Texture"].is_linked:
            declare_nodes.append(node.name)
            r, g, b = node.inputs["Pigment"].default_value[:]
            pov_col_name = "color rgb <%.4g,%.4g,%.4g>" % (r, g, b)
            if node.inputs["Pigment"].is_linked:
                for link in ntree.links:
                    if link.to_node == node and link.to_socket.name == "Pigment":
                        pov_col_name = (
                            string_strip_hyphen(bpy.path.clean_name(link.from_node.name))
                            + "_%s" % pov_mat_name
                        )
            file.write("#declare %s = texture{\n    pigment{%s}\n" % (pov_node_name, pov_col_name))
            if node.inputs["Normal"].is_linked:
                for link in ntree.links:
                    if (
                        link.to_node == node
                        and link.to_socket.name == "Normal"
                        and link.from_node.name in declare_nodes
                    ):
                        pov_nor_name = (
                            string_strip_hyphen(bpy.path.clean_name(link.from_node.name))
                            + "_%s" % pov_mat_name
                        )
                        file.write("    normal{%s}\n" % pov_nor_name)
            if node.inputs["Finish"].is_linked:
                for link in ntree.links:
                    if link.to_node == node and link.to_socket.name == "Finish":
                        pov_fin_name = (
                            string_strip_hyphen(bpy.path.clean_name(link.from_node.name))
                            + "_%s" % pov_mat_name
                        )
                        file.write("    finish{%s}\n" % pov_fin_name)
            file.write("}\n")
            declare_nodes.append(node.name)

    for i in range(0, len(ntree.nodes)):
        for node in ntree.nodes:
            if node.bl_idname in {"ShaderNodeGroup", "ShaderTextureMapNode"}:
                for output in node.outputs:
                    if (
                        output.name == "Texture"
                        and output.is_linked
                        and (node.name not in declare_nodes)
                    ):
                        declare = True
                        for link in ntree.links:
                            if link.to_node == node and link.to_socket.name not in {
                                "",
                                "Color ramp",
                                "Mapping",
                                "Transform",
                                "Modifier",
                            }:
                                if link.from_node.name not in declare_nodes:
                                    declare = False
                        if declare:
                            pov_node_name = (
                                string_strip_hyphen(bpy.path.clean_name(node.name))
                                + "_%s" % pov_mat_name
                            )
                            uv = ""
                            warp = ""
                            for link in ntree.links:
                                if (
                                    link.to_node == node
                                    and link.from_node.bl_idname == "PovrayMappingNode"
                                    and link.from_node.warp_type != "NONE"
                                ):
                                    w_type = link.from_node.warp_type
                                    if w_type == "uv_mapping":
                                        uv = "uv_mapping"
                                    else:
                                        tor = ""
                                        if w_type == "toroidal":
                                            tor = (
                                                "major_radius %.4g"
                                                % link.from_node.warp_tor_major_radius
                                            )
                                        orient = link.from_node.warp_orientation
                                        exp = link.from_node.warp_dist_exp
                                        warp = "warp{%s orientation %s dist_exp %.4g %s}" % (
                                            w_type,
                                            orient,
                                            exp,
                                            tor,
                                        )
                                        if link.from_node.warp_type == "planar":
                                            warp = "warp{%s %s %.4g}" % (w_type, orient, exp)
                                        if link.from_node.warp_type == "cubic":
                                            warp = "warp{%s}" % w_type
                            file.write("#declare %s = texture {%s\n" % (pov_node_name, uv))
                            pattern = node.inputs[0].default_value
                            advanced = ""
                            if node.inputs[0].is_linked:
                                for link in ntree.links:
                                    if (
                                        link.to_node == node
                                        and link.from_node.bl_idname == "ShaderPatternNode"
                                    ):
                                        # ------------ advanced ------------------------- #
                                        lfn = link.from_node
                                        pattern = lfn.pattern
                                        if pattern == "agate":
                                            advanced = "agate_turb %.4g" % lfn.agate_turb
                                        if pattern == "crackle":
                                            advanced = "form <%.4g,%.4g,%.4g>" % (
                                                lfn.crackle_form_x,
                                                lfn.crackle_form_y,
                                                lfn.crackle_form_z,
                                            )
                                            advanced += " metric %.4g" % lfn.crackle_metric
                                            if lfn.crackle_solid:
                                                advanced += " solid"
                                        if pattern in {"spiral1", "spiral2"}:
                                            advanced = "%.4g" % lfn.spiral_arms
                                        if pattern in {"tiling"}:
                                            advanced = "%.4g" % lfn.tiling_number
                                        if pattern in {"gradient"}:
                                            advanced = "%s" % lfn.gradient_orient
                                    if (
                                        link.to_node == node
                                        and link.from_node.bl_idname == "PovrayImagePatternNode"
                                    ):
                                        pov_macro_name = (
                                            string_strip_hyphen(
                                                bpy.path.clean_name(link.from_node.name)
                                            )
                                            + "_%s" % pov_mat_name
                                        )
                                        pattern = "%s()" % pov_macro_name
                            file.write("    %s %s %s\n" % (pattern, advanced, warp))

                            repeat = ""
                            for link in ntree.links:
                                if (
                                    link.to_node == node
                                    and link.from_node.bl_idname == "PovrayMultiplyNode"
                                ):
                                    if link.from_node.amount_x > 1:
                                        repeat += "warp{repeat %.4g * x}" % link.from_node.amount_x
                                    if link.from_node.amount_y > 1:
                                        repeat += " warp{repeat %.4g * y}" % link.from_node.amount_y
                                    if link.from_node.amount_z > 1:
                                        repeat += " warp{repeat %.4g * z}" % link.from_node.amount_z

                            transform = ""
                            for link in ntree.links:
                                if (
                                    link.to_node == node
                                    and link.from_node.bl_idname == "PovrayTransformNode"
                                ):
                                    pov_trans_name = (
                                        string_strip_hyphen(
                                            bpy.path.clean_name(link.from_node.name)
                                        )
                                        + "_%s" % pov_mat_name
                                    )
                                    transform = "transform {%s}" % pov_trans_name
                            x = 0
                            y = 0
                            z = 0
                            d = 0
                            e = 0
                            f = 0
                            g = 0
                            h = 0
                            modifier = False
                            for link in ntree.links:
                                if (
                                    link.to_node == node
                                    and link.from_node.bl_idname == "PovrayModifierNode"
                                ):
                                    modifier = True
                                    if link.from_node.inputs["Turb X"].is_linked:
                                        pass
                                    else:
                                        x = link.from_node.inputs["Turb X"].default_value

                                    if link.from_node.inputs["Turb Y"].is_linked:
                                        pass
                                    else:
                                        y = link.from_node.inputs["Turb Y"].default_value

                                    if link.from_node.inputs["Turb Z"].is_linked:
                                        pass
                                    else:
                                        z = link.from_node.inputs["Turb Z"].default_value

                                    if link.from_node.inputs["Octaves"].is_linked:
                                        pass
                                    else:
                                        d = link.from_node.inputs["Octaves"].default_value

                                    if link.from_node.inputs["Lambda"].is_linked:
                                        pass
                                    else:
                                        e = link.from_node.inputs["Lambda"].default_value

                                    if link.from_node.inputs["Omega"].is_linked:
                                        pass
                                    else:
                                        f = link.from_node.inputs["Omega"].default_value

                                    if link.from_node.inputs["Frequency"].is_linked:
                                        pass
                                    else:
                                        g = link.from_node.inputs["Frequency"].default_value

                                    if link.from_node.inputs["Phase"].is_linked:
                                        pass
                                    else:
                                        h = link.from_node.inputs["Phase"].default_value

                            turb = "turbulence <%.4g,%.4g,%.4g>" % (x, y, z)
                            octv = "octaves %s" % d
                            lmbd = "lambda %.4g" % e
                            omg = "omega %.4g" % f
                            freq = "frequency %.4g" % g
                            pha = "phase %.4g" % h

                            file.write("\n")
                            if pattern not in {
                                "checker",
                                "hexagon",
                                "square",
                                "triangular",
                                "brick",
                            }:
                                file.write("    texture_map {\n")
                            if node.inputs["Color ramp"].is_linked:
                                for link in ntree.links:
                                    if (
                                        link.to_node == node
                                        and link.from_node.bl_idname == "ShaderNodeValToRGB"
                                    ):
                                        els = link.from_node.color_ramp.elements
                                        n = -1
                                        for el in els:
                                            n += 1
                                            pov_in_mat_name = string_strip_hyphen(
                                                bpy.path.clean_name(link.from_node.name)
                                            ) + "_%s_%s" % (n, pov_mat_name)
                                            default = True
                                            for ilink in ntree.links:
                                                if (
                                                    ilink.to_node == node
                                                    and ilink.to_socket.name == str(n)
                                                ):
                                                    default = False
                                                    pov_in_mat_name = (
                                                        string_strip_hyphen(
                                                            bpy.path.clean_name(
                                                                ilink.from_node.name
                                                            )
                                                        )
                                                        + "_%s" % pov_mat_name
                                                    )
                                            if default:
                                                r, g, b, a = el.color[:]
                                                file.write(
                                                    "    #declare %s = texture{"
                                                    "pigment{"
                                                    "color srgbt <%.4g,%.4g,%.4g,%.4g>}};\n"
                                                    % (pov_in_mat_name, r, g, b, 1 - a)
                                                )
                                            file.write(
                                                "    [%s %s]\n" % (el.position, pov_in_mat_name)
                                            )
                            else:
                                els = [[0, 0, 0, 0], [1, 1, 1, 1]]
                                for t in range(0, 2):
                                    pov_in_mat_name = string_strip_hyphen(
                                        bpy.path.clean_name(link.from_node.name)
                                    ) + "_%s_%s" % (t, pov_mat_name)
                                    default = True
                                    for ilink in ntree.links:
                                        if ilink.to_node == node and ilink.to_socket.name == str(t):
                                            default = False
                                            pov_in_mat_name = (
                                                string_strip_hyphen(
                                                    bpy.path.clean_name(ilink.from_node.name)
                                                )
                                                + "_%s" % pov_mat_name
                                            )
                                    if default:
                                        r, g, b = els[t][1], els[t][2], els[t][3]
                                        if pattern not in {
                                            "checker",
                                            "hexagon",
                                            "square",
                                            "triangular",
                                            "brick",
                                        }:
                                            file.write(
                                                "    #declare %s = texture{pigment{color rgb <%.4g,%.4g,%.4g>}};\n"
                                                % (pov_in_mat_name, r, g, b)
                                            )
                                        else:
                                            file.write(
                                                "    texture{pigment{color rgb <%.4g,%.4g,%.4g>}}\n"
                                                % (r, g, b)
                                            )
                                    if pattern not in {
                                        "checker",
                                        "hexagon",
                                        "square",
                                        "triangular",
                                        "brick",
                                    }:
                                        file.write("    [%s %s]\n" % (els[t][0], pov_in_mat_name))
                                    else:
                                        if not default:
                                            file.write("    texture{%s}\n" % pov_in_mat_name)
                            if pattern not in {
                                "checker",
                                "hexagon",
                                "square",
                                "triangular",
                                "brick",
                            }:
                                file.write("}\n")
                            if pattern == "brick":
                                file.write(
                                    "brick_size <%.4g, %.4g, %.4g> mortar %.4g \n"
                                    % (
                                        node.brick_size_x,
                                        node.brick_size_y,
                                        node.brick_size_z,
                                        node.brick_mortar,
                                    )
                                )
                            file.write("    %s %s" % (repeat, transform))
                            if modifier:
                                file.write(
                                    " %s %s %s %s %s %s" % (turb, octv, lmbd, omg, freq, pha)
                                )
                            file.write("}\n")
                            declare_nodes.append(node.name)

    for link in ntree.links:
        if link.to_node.bl_idname == "PovrayOutputNode" and link.from_node.name in declare_nodes:
            pov_mat_node_name = (
                string_strip_hyphen(bpy.path.clean_name(link.from_node.name)) + "_%s" % pov_mat_name
            )
            file.write("#declare %s = %s\n" % (pov_mat_name, pov_mat_node_name))
