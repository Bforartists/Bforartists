# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Translate complex shaders to exported POV textures."""

import bpy

# WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
def write_nodes(pov_mat_name, ntree, file):
    """Translate Blender node trees to pov and write them to file."""
    # such function local inlined import are official guidelines
    # of Blender Foundation to lighten addons footprint at startup
    from os import path
    from .render import string_strip_hyphen

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
                        file.write("    <%.4g,%.4g,%.4g>\n" % (color[0], color[1], color[2]))

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
                file.write("#declare %s = pigment { color rgb 0.8}\n" % pov_node_name)
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
                        file.write("    map_type %s\n" % node.map_type)
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
                        file.write("    map_type %s\n" % node.map_type)
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
                        file.write("    map_type %s\n" % node.map_type)
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
