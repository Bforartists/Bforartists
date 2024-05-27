# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Use Blender procedural textures exported to POV patterns."""

import bpy


def export_pattern(texture):
    """Translate Blender procedural textures to POV patterns and write to pov file.

    Function Patterns can be used to better access sub components of a pattern like
    grey values for influence mapping
    """
    from .render import string_strip_hyphen

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
        for num_color, el in enumerate(tex.color_ramp.elements, start=1):
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
                col_ramp_strg += "[%.4g color rgbf<%.4g,%.4g,%.4g,%.4g>] \n" % (
                    pos,
                    col_r,
                    col_g,
                    col_b,
                    col_a,
                )
            if pat.tex_pattern_type in {"brick", "checker"} and num_color < 3:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                    col_r,
                    col_g,
                    col_b,
                    col_a,
                )
            if pat.tex_pattern_type == "hexagon" and num_color < 4:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                    col_r,
                    col_g,
                    col_b,
                    col_a,
                )
            if pat.tex_pattern_type == "square" and num_color < 5:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                    col_r,
                    col_g,
                    col_b,
                    col_a,
                )
            if pat.tex_pattern_type == "triangular" and num_color < 7:
                col_ramp_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                    col_r,
                    col_g,
                    col_b,
                    col_a,
                )

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
            text_strg += "    form <%.4g,%.4g,%.4g>\n" % (
                tex.weight_1,
                tex.weight_2,
                tex.weight_3,
            )
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
            if pat.func_list in {
                "f_helix1",
                "f_helix2",
                "f_piriform_2d",
                "f_strophoid_2d",
            }:
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
        if pat.tex_pattern_type not in {
            "checker",
            "hexagon",
            "square",
            "triangular",
            "brick",
        }:
            text_strg += "color_map {\n"
        if tex.use_color_ramp:
            for num_color, el in enumerate(tex.color_ramp.elements, start=1):
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
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                        col_r,
                        col_g,
                        col_b,
                        col_a,
                    )
                if pat.tex_pattern_type == "hexagon" and num_color < 4:
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                        col_r,
                        col_g,
                        col_b,
                        col_a,
                    )
                if pat.tex_pattern_type == "square" and num_color < 5:
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                        col_r,
                        col_g,
                        col_b,
                        col_a,
                    )
                if pat.tex_pattern_type == "triangular" and num_color < 7:
                    text_strg += "color rgbf<%.4g,%.4g,%.4g,%.4g> \n" % (
                        col_r,
                        col_g,
                        col_b,
                        col_a,
                    )
        else:
            text_strg += "[0 color rgbf<0,0,0,1>]\n"
            text_strg += "[1 color rgbf<1,1,1,0>]\n"
        if pat.tex_pattern_type not in {
            "checker",
            "hexagon",
            "square",
            "triangular",
            "brick",
        }:
            text_strg += "} \n"
        if pat.tex_pattern_type == "brick":
            text_strg += "brick_size <%.4g, %.4g, %.4g> mortar %.4g \n" % (
                pat.brick_size_x,
                pat.brick_size_y,
                pat.brick_size_z,
                pat.brick_mortar,
            )
        text_strg += "%s \n" % mapping_dif
        text_strg += "rotate <%.4g,%.4g,%.4g> \n" % (
            pat.tex_rot_x,
            pat.tex_rot_y,
            pat.tex_rot_z,
        )
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
