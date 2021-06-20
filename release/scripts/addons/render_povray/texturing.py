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

"""Translate blender texture influences into POV."""
import os
import bpy


def write_texture_influence(
    using_uberpov,
    mater,
    material_names_dictionary,
    local_material_names,
    path_image,
    exported_lights_count,
    image_format,
    img_map,
    img_map_transforms,
    tab_write,
    comments,
    string_strip_hyphen,
    safety,
    col,
    preview_dir,
    unpacked_images,
):
    """Translate Blender texture influences to various POV texture tricks and write to pov file."""
    material_finish = material_names_dictionary[mater.name]
    if mater.pov.use_transparency:
        trans = 1.0 - mater.pov.alpha
    else:
        trans = 0.0
    if (mater.pov.specular_color.s == 0.0) or (mater.pov.diffuse_shader == "MINNAERT"):
        # No layered texture because of aoi pattern used for minnaert and pov can't layer patterned
        colored_specular_found = False
    else:
        colored_specular_found = True

    if mater.pov.use_transparency and mater.pov.transparency_method == "RAYTRACE":
        pov_filter = mater.pov_raytrace_transparency.filter * (1.0 - mater.pov.alpha)
        trans = (1.0 - mater.pov.alpha) - pov_filter
    else:
        pov_filter = 0.0

    texture_dif = ""
    texture_spec = ""
    texture_norm = ""
    texture_alpha = ""
    # procedural_flag=False
    tmpidx = -1
    for t in mater.pov_texture_slots:

        tmpidx += 1
        # index = mater.pov.active_texture_index
        slot = mater.pov_texture_slots[tmpidx]  # [index]
        povtex = slot.texture  # slot.name
        tex = bpy.data.textures[povtex]

        if t and (t.use and (tex is not None)):
            # 'NONE' ('NONE' type texture is different from no texture covered above)
            if tex.type == "NONE" and tex.pov.tex_pattern_type == "emulator":
                continue  # move to next slot

            # Implicit else-if (as not skipped by previous "continue")
            # PROCEDURAL
            if tex.type != "IMAGE" and tex.type != "NONE":
                procedural_flag = True
                image_filename = "PAT_%s" % string_strip_hyphen(bpy.path.clean_name(tex.name))
                if image_filename:
                    if t.use_map_color_diffuse:
                        texture_dif = image_filename
                        # colvalue = t.default_value  # UNUSED
                        t_dif = t
                        if t_dif.texture.pov.tex_gamma_enable:
                            img_gamma = " gamma %.3g " % t_dif.texture.pov.tex_gamma_value
                    if t.use_map_specular or t.use_map_raymir:
                        texture_spec = image_filename
                        # colvalue = t.default_value  # UNUSED
                        t_spec = t
                    if t.use_map_normal:
                        texture_norm = image_filename
                        # colvalue = t.normal_factor/10 # UNUSED
                        # textNormName=tex.image.name + ".normal"
                        # was the above used? --MR
                        t_nor = t
                    if t.use_map_alpha:
                        texture_alpha = image_filename
                        # colvalue = t.alpha_factor * 10.0  # UNUSED
                        # textDispName=tex.image.name + ".displ"
                        # was the above used? --MR
                        t_alpha = t

            # RASTER IMAGE
            elif tex.type == "IMAGE" and tex.image and tex.pov.tex_pattern_type == "emulator":
                procedural_flag = False
                # PACKED
                if tex.image.packed_file:
                    orig_image_filename = tex.image.filepath_raw
                    unpackedfilename = os.path.join(
                        preview_dir,
                        ("unpacked_img_" + (string_strip_hyphen(bpy.path.clean_name(tex.name)))),
                    )
                    if not os.path.exists(unpackedfilename):
                        # record which images that were newly copied and can be safely
                        # cleaned up
                        unpacked_images.append(unpackedfilename)
                    tex.image.filepath_raw = unpackedfilename
                    tex.image.save()
                    image_filename = unpackedfilename.replace("\\", "/")
                    # .replace("\\","/") to get only forward slashes as it's what POV prefers,
                    # even on windows
                    tex.image.filepath_raw = orig_image_filename
                # FILE
                else:
                    image_filename = path_image(tex.image)
                # IMAGE SEQUENCE BEGINS
                if image_filename:
                    if bpy.data.images[tex.image.name].source == "SEQUENCE":
                        korvaa = "." + str(tex.image_user.frame_offset + 1).zfill(3) + "."
                        image_filename = image_filename.replace(".001.", korvaa)
                        print(" seq debug ")
                        print(image_filename)
                # IMAGE SEQUENCE ENDS
                img_gamma = ""
                if image_filename:
                    texdata = bpy.data.textures[t.texture]
                    if t.use_map_color_diffuse:
                        texture_dif = image_filename
                        # colvalue = t.default_value  # UNUSED
                        t_dif = t
                        print(texdata)
                        if texdata.pov.tex_gamma_enable:
                            img_gamma = " gamma %.3g " % t_dif.texture.pov.tex_gamma_value
                    if t.use_map_specular or t.use_map_raymir:
                        texture_spec = image_filename
                        # colvalue = t.default_value  # UNUSED
                        t_spec = t
                    if t.use_map_normal:
                        texture_norm = image_filename
                        # colvalue = t.normal_factor/10  # UNUSED
                        # textNormName=tex.image.name + ".normal"
                        # was the above used? --MR
                        t_nor = t
                    if t.use_map_alpha:
                        texture_alpha = image_filename
                        # colvalue = t.alpha_factor * 10.0  # UNUSED
                        # textDispName=tex.image.name + ".displ"
                        # was the above used? --MR
                        t_alpha = t

    # -----------------------------------------------------------------------------

    tab_write("\n")
    # THIS AREA NEEDS TO LEAVE THE TEXTURE OPEN UNTIL ALL MAPS ARE WRITTEN DOWN.
    # --MR
    current_material_name = string_strip_hyphen(material_names_dictionary[mater.name])
    local_material_names.append(current_material_name)
    tab_write("\n#declare MAT_%s = \ntexture{\n" % current_material_name)
    # -----------------------------------------------------------------------------

    if mater.pov.replacement_text != "":
        tab_write("%s\n" % mater.pov.replacement_text)
    # -----------------------------------------------------------------------------
    # XXX TODO: replace by new POV MINNAERT rather than aoi
    if mater.pov.diffuse_shader == "MINNAERT":
        tab_write("\n")
        tab_write("aoi\n")
        tab_write("texture_map {\n")
        tab_write("[%.3g finish {diffuse %.3g}]\n" % (mater.darkness / 2.0, 2.0 - mater.darkness))
        tab_write("[%.3g\n" % (1.0 - (mater.darkness / 2.0)))

    if mater.pov.diffuse_shader == "FRESNEL":
        # For FRESNEL diffuse in POV, we'll layer slope patterned textures
        # with lamp vector as the slope vector and nest one slope per lamp
        # into each texture map's entry.

        c = 1
        while c <= exported_lights_count:
            tab_write("slope { lampTarget%s }\n" % (c))
            tab_write("texture_map {\n")
            # Diffuse Fresnel value and factor go up to five,
            # other kind of values needed: used the number 5 below to remap
            tab_write(
                "[%.3g finish {diffuse %.3g}]\n"
                % (
                    (5.0 - mater.diffuse_fresnel) / 5,
                    (mater.diffuse_intensity * ((5.0 - mater.diffuse_fresnel_factor) / 5)),
                )
            )
            tab_write(
                "[%.3g\n" % ((mater.diffuse_fresnel_factor / 5) * (mater.diffuse_fresnel / 5.0))
            )
            c += 1

    # if shader is a 'FRESNEL' or 'MINNAERT': slope pigment pattern or aoi
    # and texture map above, the rest below as one of its entry

    if texture_spec != "" or texture_alpha != "":
        if texture_spec != "":
            # tab_write("\n")
            tab_write("pigment_pattern {\n")

            mapping_spec = img_map_transforms(t_spec)
            if texture_spec and texture_spec.startswith("PAT_"):
                tab_write("function{f%s(x,y,z).grey}\n" % texture_spec)
            else:

                tab_write(
                    'uv_mapping image_map{%s "%s" %s}\n'
                    % (image_format(texture_spec), texture_spec, img_map(t_spec))
                )
            tab_write("%s\n" % mapping_spec)
            tab_write("}\n")
            tab_write("texture_map {\n")
            tab_write("[0 \n")

        if texture_dif == "":
            if texture_alpha != "":
                tab_write("\n")

                mapping_alpha = img_map_transforms(t_alpha)

                if texture_alpha and texture_alpha.startswith("PAT_"):
                    tab_write("function{f%s(x,y,z).transmit}%s\n" % (texture_alpha, mapping_alpha))
                else:

                    tab_write(
                        "pigment {pigment_pattern {uv_mapping image_map"
                        '{%s "%s" %s}%s'
                        % (
                            image_format(texture_alpha),
                            texture_alpha,
                            img_map(t_alpha),
                            mapping_alpha,
                        )
                    )
                tab_write("}\n")
                tab_write("pigment_map {\n")
                tab_write("[0 color rgbft<0,0,0,1,1>]\n")
                tab_write(
                    "[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n"
                    % (col[0], col[1], col[2], pov_filter, trans)
                )
                tab_write("}\n")
                tab_write("}\n")

            else:

                tab_write(
                    "pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}\n"
                    % (col[0], col[1], col[2], pov_filter, trans)
                )

        else:
            mapping_dif = img_map_transforms(t_dif)

            if texture_alpha != "":
                mapping_alpha = img_map_transforms(t_alpha)

                tab_write("pigment {\n")
                tab_write("pigment_pattern {\n")
                if texture_alpha and texture_alpha.startswith("PAT_"):
                    tab_write("function{f%s(x,y,z).transmit}%s\n" % (texture_alpha, mapping_alpha))
                else:
                    tab_write(
                        'uv_mapping image_map{%s "%s" %s}%s}\n'
                        % (
                            image_format(texture_alpha),
                            texture_alpha,
                            img_map(t_alpha),
                            mapping_alpha,
                        )
                    )
                tab_write("pigment_map {\n")
                tab_write("[0 color rgbft<0,0,0,1,1>]\n")
                # if texture_alpha and texture_alpha.startswith("PAT_"):
                # tab_write("[1 pigment{%s}]\n" %texture_dif)
                if texture_dif and not texture_dif.startswith("PAT_"):
                    tab_write(
                        '[1 uv_mapping image_map {%s "%s" %s} %s]\n'
                        % (
                            image_format(texture_dif),
                            texture_dif,
                            (img_gamma + img_map(t_dif)),
                            mapping_dif,
                        )
                    )
                elif texture_dif and texture_dif.startswith("PAT_"):
                    tab_write("[1 %s]\n" % texture_dif)
                tab_write("}\n")
                tab_write("}\n")
                if texture_alpha and texture_alpha.startswith("PAT_"):
                    tab_write("}\n")

            else:
                if texture_dif and texture_dif.startswith("PAT_"):
                    tab_write("pigment{%s}\n" % texture_dif)
                else:
                    tab_write(
                        'pigment {uv_mapping image_map {%s "%s" %s}%s}\n'
                        % (
                            image_format(texture_dif),
                            texture_dif,
                            (img_gamma + img_map(t_dif)),
                            mapping_dif,
                        )
                    )

                    # scale 1 rotate y*0
                    # imageMap = ("{image_map {%s \"%s\" %s }\n" % \
                    #            (image_format(textures),textures,img_map(t_dif)))
                    # tab_write("uv_mapping pigment %s} %s finish {%s}\n" % \
                    #         (imageMap,mapping,safety(material_finish)))
                    # tab_write("pigment {uv_mapping image_map {%s \"%s\" %s}%s} " \
                    #         "finish {%s}\n" % \
                    #         (image_format(texture_dif), texture_dif, img_map(t_dif),
                    #          mapping_dif, safety(material_finish)))
        if texture_spec != "":
            # ref_level_bound 1 is no specular
            tab_write("finish {%s}\n" % (safety(material_finish, ref_level_bound=1)))

        else:
            # ref_level_bound 2 is translated spec
            tab_write("finish {%s}\n" % (safety(material_finish, ref_level_bound=2)))

        if texture_norm != "":
            # scale 1 rotate y*0

            mapping_normal = img_map_transforms(t_nor)

            if texture_norm and texture_norm.startswith("PAT_"):
                tab_write(
                    "normal{function{f%s(x,y,z).grey} bump_size %.4g %s}\n"
                    % (texture_norm, (-t_nor.normal_factor * 9.5), mapping_normal)
                )
            else:
                tab_write("normal {\n")
                # XXX TODO: fix and propagate the micro normals reflection blur below
                #  to non textured materials
                if (
                    mater.pov_raytrace_mirror.use
                    and mater.pov_raytrace_mirror.gloss_factor < 1.0
                    and not using_uberpov
                ):
                    tab_write("average\n")
                    tab_write("normal_map{\n")
                    # 0.5 for entries below means a 50 percent mix
                    # between the micro normal and user bump map
                    # order seems indifferent as commutative
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (10 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.1]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.15]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.2]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.25]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.3]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.35]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.4]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.45]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write(
                        "[0.025 bumps %.4g scale 0.1*%.4g phase 0.5]\n"
                        % (
                            (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                            (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                        )
                    )  # micronormals blurring
                    tab_write("[1.0 ")  # Proceed with user bump...
                tab_write(
                    "uv_mapping bump_map "
                    '{%s "%s" %s  bump_size %.4g }%s'
                    % (
                        image_format(texture_norm),
                        texture_norm,
                        img_map(t_nor),
                        (-t_nor.normal_factor * 9.5),
                        mapping_normal,
                    )
                )
                # ...Then close its last entry and the the normal_map itself
                if (
                    mater.pov_raytrace_mirror.use
                    and mater.pov_raytrace_mirror.gloss_factor < 1.0
                    and not using_uberpov
                ):
                    tab_write("]}}\n")
                else:
                    tab_write("]}\n")
    if texture_spec != "":
        tab_write("]\n")
        # -------- Second index for mapping specular max value -------- #
        tab_write("[1 \n")

    if texture_dif == "" and mater.pov.replacement_text == "":
        if texture_alpha != "":
            mapping_alpha = img_map_transforms(t_alpha)

            if texture_alpha and texture_alpha.startswith("PAT_"):
                tab_write("function{f%s(x,y,z).transmit %s}\n" % (texture_alpha, mapping_alpha))
            else:
                tab_write(
                    "pigment {pigment_pattern {uv_mapping image_map"
                    '{%s "%s" %s}%s}\n'
                    % (image_format(texture_alpha), texture_alpha, img_map(t_alpha), mapping_alpha)
                )
            tab_write("pigment_map {\n")
            tab_write("[0 color rgbft<0,0,0,1,1>]\n")
            tab_write(
                "[1 color rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>]\n"
                % (col[0], col[1], col[2], pov_filter, trans)
            )
            tab_write("}\n")
            tab_write("}\n")

        else:
            tab_write(
                "pigment {rgbft<%.3g, %.3g, %.3g, %.3g, %.3g>}\n"
                % (col[0], col[1], col[2], pov_filter, trans)
            )

        if texture_spec != "":
            # ref_level_bound 3 is full specular
            tab_write("finish {%s}\n" % (safety(material_finish, ref_level_bound=3)))

            if (
                mater.pov_raytrace_mirror.use
                and mater.pov_raytrace_mirror.gloss_factor < 1.0
                and not using_uberpov
            ):
                tab_write("normal {\n")
                tab_write("average\n")
                tab_write("normal_map{\n")
                # 0.5 for entries below means a 50 percent mix
                # between the micro normal and user bump map
                # order seems indifferent as commutative
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (10 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.1]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.15]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.2]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.25]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.3]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.35]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.4]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.45]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.5]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
            # XXX IF USER BUMP_MAP
            if texture_norm != "":
                tab_write(
                    "[1.0 "
                )  # Blurry reflection or not Proceed with user bump in either case...
                tab_write(
                    "uv_mapping bump_map "
                    '{%s "%s" %s  bump_size %.4g }%s]\n'
                    % (
                        image_format(texture_norm),
                        texture_norm,
                        img_map(t_nor),
                        (-t_nor.normal_factor * 9.5),
                        mapping_normal,
                    )
                )
            # ...Then close the normal_map itself if blurry reflection
            if (
                mater.pov_raytrace_mirror.use
                and mater.pov_raytrace_mirror.gloss_factor < 1.0
                and not using_uberpov
            ):
                tab_write("}}\n")
            else:
                tab_write("}\n")
        elif colored_specular_found:
            # ref_level_bound 1 is no specular
            tab_write("finish {%s}\n" % (safety(material_finish, ref_level_bound=1)))

        else:
            # ref_level_bound 2 is translated specular
            tab_write("finish {%s}\n" % (safety(material_finish, ref_level_bound=2)))

    elif mater.pov.replacement_text == "":
        mapping_dif = img_map_transforms(t_dif)

        if texture_alpha != "":

            mapping_alpha = img_map_transforms(t_alpha)

            if texture_alpha and texture_alpha.startswith("PAT_"):
                tab_write(
                    "pigment{pigment_pattern {function{f%s(x,y,z).transmit}%s}\n"
                    % (texture_alpha, mapping_alpha)
                )
            else:
                tab_write(
                    "pigment {pigment_pattern {uv_mapping image_map"
                    '{%s "%s" %s}%s}\n'
                    % (image_format(texture_alpha), texture_alpha, img_map(t_alpha), mapping_alpha)
                )
            tab_write("pigment_map {\n")
            tab_write("[0 color rgbft<0,0,0,1,1>]\n")
            if texture_alpha and texture_alpha.startswith("PAT_"):
                tab_write("[1 function{f%s(x,y,z).transmit}%s]\n" % (texture_alpha, mapping_alpha))
            elif texture_dif and not texture_dif.startswith("PAT_"):
                tab_write(
                    '[1 uv_mapping image_map {%s "%s" %s} %s]\n'
                    % (
                        image_format(texture_dif),
                        texture_dif,
                        (img_map(t_dif) + img_gamma),
                        mapping_dif,
                    )
                )
            elif texture_dif and texture_dif.startswith("PAT_"):
                tab_write("[1 %s %s]\n" % (texture_dif, mapping_dif))
            tab_write("}\n")
            tab_write("}\n")

        else:
            if texture_dif and texture_dif.startswith("PAT_"):
                tab_write("pigment{%s %s}\n" % (texture_dif, mapping_dif))
            else:
                tab_write("pigment {\n")
                tab_write("uv_mapping image_map {\n")
                # tab_write("%s \"%s\" %s}%s\n" % \
                #         (image_format(texture_dif), texture_dif,
                #         (img_gamma + img_map(t_dif)),mapping_dif))
                tab_write('%s "%s" \n' % (image_format(texture_dif), texture_dif))
                tab_write("%s\n" % (img_gamma + img_map(t_dif)))
                tab_write("}\n")
                tab_write("%s\n" % mapping_dif)
                tab_write("}\n")

        if texture_spec != "":
            # ref_level_bound 3 is full specular
            tab_write("finish {%s}\n" % (safety(material_finish, ref_level_bound=3)))
        else:
            # ref_level_bound 2 is translated specular
            tab_write("finish {%s}\n" % (safety(material_finish, ref_level_bound=2)))

        # scale 1 rotate y*0
        # imageMap = ("{image_map {%s \"%s\" %s }" % \
        #            (image_format(textures), textures,img_map(t_dif)))
        # tab_write("\n\t\t\tuv_mapping pigment %s} %s finish {%s}" % \
        #           (imageMap, mapping, safety(material_finish)))
        # tab_write("\n\t\t\tpigment {uv_mapping image_map " \
        #           "{%s \"%s\" %s}%s} finish {%s}" % \
        #           (image_format(texture_dif), texture_dif,img_map(t_dif),
        #            mapping_dif, safety(material_finish)))
    if texture_norm != "" and mater.pov.replacement_text == "":

        mapping_normal = img_map_transforms(t_nor)

        if texture_norm and texture_norm.startswith("PAT_"):
            tab_write(
                "normal{function{f%s(x,y,z).grey} bump_size %.4g %s}\n"
                % (texture_norm, (-t_nor.normal_factor * 9.5), mapping_normal)
            )
        else:
            tab_write("normal {\n")
            # XXX TODO: fix and propagate the micro normals reflection blur below
            #  to non textured materials
            if (
                mater.pov_raytrace_mirror.use
                and mater.pov_raytrace_mirror.gloss_factor < 1.0
                and not using_uberpov
            ):
                tab_write("average\n")
                tab_write("normal_map{\n")
                # 0.5 for entries below means a 50 percent mix
                # between the micro normal and user bump map
                # order seems indifferent as commutative
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (10 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.1]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.15]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.2]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.25]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.3]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.35]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.4]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.45]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[0.025 bumps %.4g scale 0.1*%.4g phase 0.5]\n"
                    % (
                        (10 / (mater.pov_raytrace_mirror.gloss_factor + 0.01)),
                        (1 / (mater.pov_raytrace_mirror.gloss_samples + 0.001)),
                    )
                )  # micronormals blurring
                tab_write(
                    "[1.0 "
                )  # Blurry reflection or not Proceed with user bump in either case...
            tab_write(
                "uv_mapping bump_map "
                '{%s "%s" %s  bump_size %.4g }%s]\n'
                % (
                    image_format(texture_norm),
                    texture_norm,
                    img_map(t_nor),
                    (-t_nor.normal_factor * 9.5),
                    mapping_normal,
                )
            )
            # ...Then close the normal_map itself if blurry reflection
            if (
                mater.pov_raytrace_mirror.use
                and mater.pov_raytrace_mirror.gloss_factor < 1.0
                and not using_uberpov
            ):
                tab_write("}}\n")
            else:
                tab_write("}\n")
    if texture_spec != "" and mater.pov.replacement_text == "":
        tab_write("]\n")

        tab_write("}\n")

    # End of slope/ior texture_map
    if mater.pov.diffuse_shader == "MINNAERT" and mater.pov.replacement_text == "":
        tab_write("]\n")
        tab_write("}\n")
    if mater.pov.diffuse_shader == "FRESNEL" and mater.pov.replacement_text == "":
        c = 1
        while c <= exported_lights_count:
            tab_write("]\n")
            tab_write("}\n")
            c += 1

    # Close first layer of POV "texture" (Blender material)
    tab_write("}\n")

    colored_specular_found = bool(
        (mater.pov.specular_color.s > 0.0) and (mater.pov.diffuse_shader != "MINNAERT")
    )

    # Write another layered texture using invisible diffuse and metallic trick
    # to emulate colored specular highlights
    special_texture_found = False
    tmpidx = -1
    for t in mater.pov_texture_slots:
        tmpidx += 1
        # index = mater.pov.active_texture_index
        slot = mater.pov_texture_slots[tmpidx]  # [index]
        povtex = slot.texture  # slot.name
        tex = bpy.data.textures[povtex]
        # Specular mapped textures would conflict with colored specular
        # because POV can't layer over or under pigment patterned textures
        special_texture_found = bool(
            t
            and t.use
            and ((tex.type == "IMAGE" and tex.image) or tex.type != "IMAGE")
            and (t.use_map_specular or t.use_map_raymir)
        )
    if colored_specular_found and not special_texture_found:
        if comments:
            tab_write("  // colored highlights with a stransparent metallic layer\n")
        else:
            tab_write("\n")

        tab_write("texture {\n")
        tab_write(
            "pigment {rgbft<%.3g, %.3g, %.3g, 0, 1>}\n"
            % (
                mater.pov.specular_color[0],
                mater.pov.specular_color[1],
                mater.pov.specular_color[2],
            )
        )
        tab_write(
            "finish {%s}\n" % (safety(material_finish, ref_level_bound=2))
        )  # ref_level_bound 2 is translated spec

        texture_norm = ""
        for t in mater.pov_texture_slots:

            if t and tex.pov.tex_pattern_type != "emulator":
                procedural_flag = True
                image_filename = string_strip_hyphen(bpy.path.clean_name(tex.name))
            if (
                t
                and tex.type == "IMAGE"
                and t.use
                and tex.image
                and tex.pov.tex_pattern_type == "emulator"
            ):
                procedural_flag = False
                image_filename = path_image(tex.image)
                img_gamma = ""
                if image_filename:
                    if t.use_map_normal:
                        texture_norm = image_filename
                        # colvalue = t.normal_factor/10  # UNUSED   XXX *-9.5 !
                        # textNormName=tex.image.name + ".normal"
                        # was the above used? --MR
                        t_nor = t
                        if procedural_flag:
                            tab_write(
                                "normal{function"
                                "{f%s(x,y,z).grey} bump_size %.4g}\n"
                                % (texture_norm, (-t_nor.normal_factor * 9.5))
                            )
                        else:
                            tab_write(
                                "normal {uv_mapping bump_map "
                                '{%s "%s" %s  bump_size %.4g }%s}\n'
                                % (
                                    image_format(texture_norm),
                                    texture_norm,
                                    img_map(t_nor),
                                    (-t_nor.normal_factor * 9.5),
                                    mapping_normal,
                                )
                            )

        tab_write("}\n")  # THEN IT CAN CLOSE LAST LAYER OF TEXTURE
