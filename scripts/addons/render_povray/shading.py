# SPDX-FileCopyrightText: 2015-2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Translate complex shaders to exported POV textures."""

import bpy


def write_object_material_interior(file, material, ob, tab_write):
    """Translate some object level material from Blender UI (VS data level)

    to POV interior{} syntax and write it to exported file.
    This is called in model_all.objects_loop
    """
    # DH - modified some variables to be function local, avoiding RNA write
    # this should be checked to see if it is functionally correct

    # Commented out: always write IOR to be able to use it for SSS, Fresnel reflections...
    # if material and material.pov.transparency_method == 'RAYTRACE':
    if not material:
        return
    # implicit if material:
    # But there can be only one ior!
    if material.pov_subsurface_scattering.use:  # SSS IOR get highest priority
        tab_write(file, "interior {\n")
        tab_write(file, "ior %.6f\n" % material.pov_subsurface_scattering.ior)
    # Then the raytrace IOR taken from raytrace transparency properties and used for
    # reflections if IOR Mirror option is checked.
    elif material.pov.mirror_use_IOR or material.pov.transparency_method != "Z_TRANSPARENCY":
        tab_write(file, "interior {\n")
        tab_write(file, "ior %.6f\n" % material.pov_raytrace_transparency.ior)
    else:
        tab_write(file, "interior {\n")
        tab_write(file, "ior 1.0\n")

    pov_fake_caustics = False
    pov_photons_refraction = False
    pov_photons_reflection = bool(material.pov.photons_reflection)
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
            tab_write(file, "caustics %.3g\n" % material.pov.fake_caustics_power)
        if pov_photons_refraction:
            # Default of 1 means no dispersion
            tab_write(file, "dispersion %.6f\n" % material.pov.photons_dispersion)
            tab_write(file, "dispersion_samples %.d\n" % material.pov.photons_dispersion_samples)
    # TODO
    # Other interior args
    if material.pov.use_transparency and material.pov.transparency_method == "RAYTRACE":
        # fade_distance
        # In Blender this value has always been reversed compared to what tooltip says.
        # 100.001 rather than 100 so that it does not get to 0
        # which deactivates the feature in POV
        tab_write(
            file, "fade_distance %.3g\n" % (100.001 - material.pov_raytrace_transparency.depth_max)
        )
        # fade_power
        tab_write(file, "fade_power %.3g\n" % material.pov_raytrace_transparency.falloff)
        # fade_color
        tab_write(file, "fade_color <%.3g, %.3g, %.3g>\n" % material.pov.interior_fade_color[:])

    # (variable) dispersion_samples (constant count for now)
    tab_write(file, "}\n")
    if material.pov.photons_reflection or material.pov.refraction_type == "2":
        tab_write(file, "photons{")
        tab_write(file, "target %.3g\n" % ob.pov.spacing_multiplier)
        if not ob.pov.collect_photons:
            tab_write(file, "collect off\n")
        if pov_photons_refraction:
            tab_write(file, "refraction on\n")
        if pov_photons_reflection:
            tab_write(file, "reflection on\n")
        tab_write(file, "}\n")


def write_material(
    file,
    using_uberpov,
    DEF_MAT_NAME,
    tab_write,
    comments,
    unique_name,
    material_names_dictionary,
    material,
):
    """Translate Blender material to POV texture{} block and write in exported file."""
    # Assumes only called once on each material

    from .render import safety

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

    def pov_has_no_specular_maps(file, ref_level_bound):
        """Translate Blender specular map influence to POV finish map trick and write to file."""
        if ref_level_bound == 1:
            if comments:
                tab_write(file, "//--No specular nor Mirror reflection--\n")
            else:
                tab_write(file, "\n")
            tab_write(file, "#declare %s = finish {\n" % safety(name, ref_level_bound=1))

        elif ref_level_bound == 2:
            if comments:
                tab_write(
                    file,
                    "//--translation of spec and mir levels for when no map " "influences them--\n",
                )
            else:
                tab_write(file, "\n")
            tab_write(file, "#declare %s = finish {\n" % safety(name, ref_level_bound=2))

        elif ref_level_bound == 3:
            if comments:
                tab_write(file, "//--Maximum Spec and Mirror--\n")
            else:
                tab_write(file, "\n")
            tab_write(file, "#declare %s = finish {\n" % safety(name, ref_level_bound=3))
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
                tab_write(file, "brilliance %.3g\n" % (0.9 + material.roughness))

            if material.pov.diffuse_shader == "TOON" and ref_level_bound != 3:
                tab_write(file, "brilliance %.3g\n" % (0.01 + material.diffuse_toon_smooth * 0.25))
                # Lower diffuse and increase specular for toon effect seems to look better
                # in POV-Ray.
                front_diffuse *= 0.5

            if material.pov.diffuse_shader == "MINNAERT" and ref_level_bound != 3:
                # tab_write(file, "aoi %.3g\n" % material.pov.darkness)
                pass  # let's keep things simple for now
            if material.pov.diffuse_shader == "FRESNEL" and ref_level_bound != 3:
                # tab_write(file, "aoi %.3g\n" % material.pov.diffuse_fresnel_factor)
                pass  # let's keep things simple for now
            if material.pov.diffuse_shader == "LAMBERT" and ref_level_bound != 3:
                # trying to best match lambert attenuation by that constant brilliance value
                tab_write(file, "brilliance 1\n")

            if ref_level_bound == 2:
                # ------------------------------ Specular Shader ------------------------------ #
                # No difference between phong and cook torrence in blender HaHa!
                if material.pov.specular_shader in ["COOKTORR", "PHONG"]:
                    tab_write(file, "phong %.3g\n" % material.pov.specular_intensity)
                    tab_write(file, "phong_size %.3g\n" % (material.pov.specular_hardness / 3.14))

                # POV-Ray 'specular' keyword corresponds to a Blinn model, without the ior.
                elif material.pov.specular_shader == "BLINN":
                    # Use blender Blinn's IOR just as some factor for spec intensity
                    tab_write(
                        file,
                        "specular %.3g\n"
                        % (material.pov.specular_intensity * (material.pov.specular_ior / 4.0)),
                    )
                    tab_write(file, "roughness %.3g\n" % roughness)
                    # Could use brilliance 2(or varying around 2 depending on ior or factor) too.

                elif material.pov.specular_shader == "TOON":
                    tab_write(file, "phong %.3g\n" % (material.pov.specular_intensity * 2.0))
                    # use extreme phong_size
                    tab_write(
                        file, "phong_size %.3g\n" % (0.1 + material.pov.specular_toon_smooth / 2.0)
                    )

                elif material.pov.specular_shader == "WARDISO":
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(
                        file,
                        "specular %.3g\n"
                        % (
                            material.pov.specular_intensity / (material.pov.specular_slope + 0.0005)
                        ),
                    )
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(
                        file, "roughness %.4g\n" % (0.0005 + material.pov.specular_slope / 10.0)
                    )
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(file, "brilliance %.4g\n" % (1.8 - material.pov.specular_slope * 1.8))

            # -------------------------------------------------------------------------------- #
            elif ref_level_bound == 1:
                if material.pov.specular_shader in ["COOKTORR", "PHONG"]:
                    tab_write(file, "phong 0\n")  # %.3g\n" % (material.pov.specular_intensity/5))
                    tab_write(file, "phong_size %.3g\n" % (material.pov.specular_hardness / 3.14))

                # POV-Ray 'specular' keyword corresponds to a Blinn model, without the ior.
                elif material.pov.specular_shader == "BLINN":
                    # Use blender Blinn's IOR just as some factor for spec intensity
                    tab_write(
                        file,
                        "specular %.3g\n"
                        % (material.pov.specular_intensity * (material.pov.specular_ior / 4.0)),
                    )
                    tab_write(file, "roughness %.3g\n" % roughness)
                    # Could use brilliance 2(or varying around 2 depending on ior or factor) too.

                elif material.pov.specular_shader == "TOON":
                    tab_write(file, "phong %.3g\n" % (material.pov.specular_intensity * 2.0))
                    # use extreme phong_size
                    tab_write(
                        file, "phong_size %.3g\n" % (0.1 + material.pov.specular_toon_smooth / 2.0)
                    )

                elif material.pov.specular_shader == "WARDISO":
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(
                        file,
                        "specular %.3g\n"
                        % (
                            material.pov.specular_intensity / (material.pov.specular_slope + 0.0005)
                        ),
                    )
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(
                        file, "roughness %.4g\n" % (0.0005 + material.pov.specular_slope / 10.0)
                    )
                    # find best suited default constant for brilliance Use both phong and
                    # specular for some values.
                    tab_write(file, "brilliance %.4g\n" % (1.8 - material.pov.specular_slope * 1.8))
            elif ref_level_bound == 3:
                # Spec must be Max at ref_level_bound 3 so that white of mixing texture always shows specularity
                # That's why it's multiplied by 255. maybe replace by texture's brightest pixel value?
                if material.pov_texture_slots:
                    max_spec_factor = (
                        material.pov.specular_intensity
                        * material.pov.specular_color.v
                        * 255
                        * slot.specular_factor
                    )
                else:
                    max_spec_factor = (
                        material.pov.specular_intensity * material.pov.specular_color.v * 255
                    )
                tab_write(file, "specular %.3g\n" % max_spec_factor)
                tab_write(file, "roughness %.3g\n" % (1 / material.pov.specular_hardness))
            tab_write(file, "diffuse %.3g, %.3g\n" % (front_diffuse, back_diffuse))

            tab_write(file, "ambient %.3g\n" % material.pov.ambient)
            # POV-Ray blends the global value
            # tab_write(file, "ambient rgb <%.3g, %.3g, %.3g>\n" % \
            #         tuple([c*material.pov.ambient for c in world.ambient_color]))
            tab_write(file, "emission %.3g\n" % material.pov.emit)  # New in POV-Ray 3.7

            # POV-Ray just ignores roughness if there's no specular keyword
            # tab_write(file, "roughness %.3g\n" % roughness)

            if material.pov.conserve_energy:
                # added for more realistic shading. Needs some checking to see if it
                # really works. --Maurice.
                tab_write(file, "conserve_energy\n")

            if colored_specular_found:
                tab_write(file, "metallic\n")

            # 'phong 70.0 '
            if ref_level_bound != 1 and material.pov_raytrace_mirror.use:
                raytrace_mirror = material.pov_raytrace_mirror
                if raytrace_mirror.reflect_factor:
                    tab_write(file, "reflection {\n")
                    tab_write(file, "rgb <%.3g, %.3g, %.3g>\n" % material.pov.mirror_color[:])
                    if material.metallic:
                        tab_write(file, "metallic %.3g\n" % material.metallic)
                    # Blurry reflections for UberPOV
                    if using_uberpov and raytrace_mirror.gloss_factor < 1.0:
                        # tab_write(file, "#ifdef(unofficial) #if(unofficial = \"patch\") #if(patch(\"upov-reflection-roughness\") > 0)\n")
                        tab_write(
                            file, "roughness %.6f\n" % (0.000001 / raytrace_mirror.gloss_factor)
                        )
                        # tab_write(file, "#end #end #end\n") # This and previous comment for backward compatibility, messier pov code
                    if material.pov.mirror_use_IOR:  # WORKING ?
                        # Removed from the line below: gives a more physically correct
                        # material but needs proper IOR. --Maurice
                        tab_write(file, "fresnel 1 ")
                    tab_write(
                        file,
                        "falloff %.3g exponent %.3g} "
                        % (raytrace_mirror.fresnel, raytrace_mirror.fresnel_factor),
                    )

            if material.pov_subsurface_scattering.use:
                subsurface_scattering = material.pov_subsurface_scattering
                tab_write(
                    file,
                    "subsurface { translucency <%.3g, %.3g, %.3g> }\n"
                    % (
                        (subsurface_scattering.radius[0]),
                        (subsurface_scattering.radius[1]),
                        (subsurface_scattering.radius[2]),
                    ),
                )

            if material.pov.irid_enable:
                tab_write(
                    file,
                    "irid { %.4g thickness %.4g turbulence %.4g }"
                    % (
                        material.pov.irid_amount,
                        material.pov.irid_thickness,
                        material.pov.irid_turbulence,
                    ),
                )

        else:
            tab_write(file, "diffuse 0.8\n")
            tab_write(file, "phong 70.0\n")

            # tab_write(file, "specular 0.2\n")

        # This is written into the object
        """
        if material and material.pov.transparency_method=='RAYTRACE':
            'interior { ior %.3g} ' % material.raytrace_transparency.ior
        """

        # tab_write(file, "crand 1.0\n") # Sand granyness
        # tab_write(file, "metallic %.6f\n" % material.metallic)
        # tab_write(file, "phong %.6f\n" % material.spec)
        # tab_write(file, "phong_size %.6f\n" % material.spec)
        # tab_write(file, "brilliance %.6f " % (material.pov.specular_hardness/256.0) # Like hardness

        tab_write(file, "}\n\n")

    # ref_level_bound=2 Means translation of spec and mir levels for when no map influences them
    pov_has_no_specular_maps(file, ref_level_bound=2)

    if material:
        special_texture_found = False
        tmpidx = -1
        slot = None
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
            pov_has_no_specular_maps(file, ref_level_bound=1)

            # ref_level_bound=3 Means Maximum Spec and Mirror
            pov_has_no_specular_maps(file, ref_level_bound=3)
