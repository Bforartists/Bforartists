# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Translate to POV the control point compound geometries.

Here polygon meshes as POV mesh2 objects.
"""

import bpy
from . import texturing
from .scenography import image_format, img_map, img_map_transforms
from .shading import write_object_material_interior
from .model_primitives import write_object_modifiers

def write_object_csg_inside_vector(ob, file):
    """Write inside vector for use by pov CSG, only once per object using boolean"""
    has_csg_inside_vector = False
    for modif in ob.modifiers:
        if not has_csg_inside_vector and modif.type == "BOOLEAN" and ob.pov.boolean_mod == "POV":
            file.write(
                "\tinside_vector <%.6g, %.6g, %.6g>\n"
                % (
                    ob.pov.inside_vector[0],
                    ob.pov.inside_vector[1],
                    ob.pov.inside_vector[2],
                )
            )
            has_csg_inside_vector = True

def export_mesh(file,
                ob,
                povdataname,
                material_names_dictionary,
                unpacked_images,
                tab_level,
                tab_write,
                linebreaksinlists):
    from .render import (
        string_strip_hyphen,
        tab,
        comments,
        preview_dir,
    )

    ob_eval = ob  # not sure this is needed in case to_mesh_clear could damage obj ?
    importance = ob.pov.importance_value

    try:
        me = ob_eval.to_mesh()

    # Here identify the exception for mesh object with no data: Runtime-Error ?
    # So we can write something for the dataname or maybe treated "if not me" below
    except BaseException as e:
        print(e.__doc__)
        print("An exception occurred: {}".format(e))
        # also happens when curves can't be made into meshes because of no-data
        return False  # To continue object loop
    if me:
        me.calc_loop_triangles()
        me_materials = me.materials
        me_faces = me.loop_triangles[:]
        # --- numpytest
        # me_looptris = me.loops

        # Below otypes = ['int32'] is a 32-bit signed integer number numpy datatype
        # get_v_index = np.vectorize(lambda l: l.vertex_index, otypes = ['int32'], cache = True)
        # faces_verts_idx = get_v_index(me_looptris)

    # if len(me_faces)==0:
    # tab_write(file, "\n//dummy sphere to represent empty mesh location\n")
    # tab_write(file, "#declare %s =sphere {<0, 0, 0>,0 pigment{rgbt 1} no_image no_reflection no_radiosity photons{pass_through collect off} hollow}\n" % povdataname)

    if not me or not me_faces:
        tab_write(file, "\n//dummy sphere to represent empty mesh location\n")
        tab_write(
            file,
            "#declare %s =sphere {<0, 0, 0>,0 pigment{rgbt 1} no_image no_reflection no_radiosity photons{pass_through collect off} hollow}\n"
            % povdataname,
        )
        return False  # To continue object loop

    uv_layers = me.uv_layers
    if len(uv_layers) > 0:
        if me.uv_layers.active and uv_layers.active.data:
            uv_layer = uv_layers.active.data
    else:
        uv_layer = None

    try:
        # vcol_layer = me.vertex_colors.active.data
        vcol_layer = me.vertex_colors.active.data
    except AttributeError:
        vcol_layer = None

    faces_verts = [f.vertices[:] for f in me_faces]
    faces_normals = [f.normal[:] for f in me_faces]
    verts_normals = [v.normal[:] for v in me.vertices]

    # Use named declaration to allow reference e.g. for baking. MR
    file.write("\n")
    tab_write(file, "#declare %s =\n" % povdataname)
    tab_write(file, "mesh2 {\n")
    tab_write(file, "vertex_vectors {\n")
    tab_write(file, "%d" % len(me.vertices))  # vert count

    tab_str = tab * tab_level
    for v in me.vertices:
        if linebreaksinlists:
            file.write(",\n")
            file.write(tab_str + "<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
        else:
            file.write(", ")
            file.write("<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
        # tab_write(file, "<%.6f, %.6f, %.6f>" % v.co[:])  # vert count
    file.write("\n")
    tab_write(file, "}\n")

    # Build unique Normal list
    uniqueNormals = {}
    for fi, f in enumerate(me_faces):
        fv = faces_verts[fi]
        # [-1] is a dummy index, use a list so we can modify in place
        if f.use_smooth:  # Use vertex normals
            for v in fv:
                key = verts_normals[v]
                uniqueNormals[key] = [-1]
        else:  # Use face normal
            key = faces_normals[fi]
            uniqueNormals[key] = [-1]

    tab_write(file, "normal_vectors {\n")
    tab_write(file, "%d" % len(uniqueNormals))  # vert count
    idx = 0
    tab_str = tab * tab_level
    for no, index in uniqueNormals.items():
        if linebreaksinlists:
            file.write(",\n")
            file.write(tab_str + "<%.6f, %.6f, %.6f>" % no)  # vert count
        else:
            file.write(", ")
            file.write("<%.6f, %.6f, %.6f>" % no)  # vert count
        index[0] = idx
        idx += 1
    file.write("\n")
    tab_write(file, "}\n")
    # Vertex colors
    vertCols = {}  # Use for material colors also.

    if uv_layer:
        # Generate unique UV's
        uniqueUVs = {}
        # n = 0
        for f in me_faces:  # me.faces in 2.7
            uvs = [uv_layer[loop_index].uv[:] for loop_index in f.loops]

            for uv in uvs:
                uniqueUVs[uv[:]] = [-1]

        tab_write(file, "uv_vectors {\n")
        # print unique_uvs
        tab_write(file, "%d" % len(uniqueUVs))  # vert count
        idx = 0
        tab_str = tab * tab_level
        for uv, index in uniqueUVs.items():
            if linebreaksinlists:
                file.write(",\n")
                file.write(tab_str + "<%.6f, %.6f>" % uv)
            else:
                file.write(", ")
                file.write("<%.6f, %.6f>" % uv)
            index[0] = idx
            idx += 1
        """
        else:
            # Just add 1 dummy vector, no real UV's
            tab_write(file, '1') # vert count
            file.write(',\n\t\t<0.0, 0.0>')
        """
        file.write("\n")
        tab_write(file, "}\n")
    if me.vertex_colors:
        # Write down vertex colors as a texture for each vertex
        tab_write(file, "texture_list {\n")
        tab_write(
            file, "%d\n" % (len(me_faces) * 3)
        )  # assumes we have only triangles
        VcolIdx = 0
        if comments:
            file.write(
                "\n  //Vertex colors: one simple pigment texture per vertex\n"
            )
        for fi, f in enumerate(me_faces):
            # annoying, index may be invalid
            material_index = f.material_index
            try:
                material = me_materials[material_index]
            except BaseException as e:
                print(e.__doc__)
                print("An exception occurred: {}".format(e))
                material = None
            if (
                material
                # and material.pov.use_vertex_color_paint
            ):  # Or maybe Always use vertex color when there is some for now

                cols = [vcol_layer[loop_index].color[:] for loop_index in f.loops]

                for col in cols:
                    key = (
                        col[0],
                        col[1],
                        col[2],
                        material_index,
                    )  # Material index!
                    VcolIdx += 1
                    vertCols[key] = [VcolIdx]
                    if linebreaksinlists:
                        tab_write(
                            file,
                            "texture {pigment{ color srgb <%6f,%6f,%6f> }}\n"
                            % (col[0], col[1], col[2]),
                        )
                    else:
                        tab_write(
                            file,
                            "texture {pigment{ color srgb <%6f,%6f,%6f> }}"
                            % (col[0], col[1], col[2]),
                        )
                        tab_str = tab * tab_level
            else:
                if material:
                    # Multiply diffuse with SSS Color
                    if material.pov_subsurface_scattering.use:
                        diffuse_color = [
                            i * j
                            for i, j in zip(
                                material.pov_subsurface_scattering.color[:],
                                material.diffuse_color[:],
                            )
                        ]
                        key = (
                            diffuse_color[0],
                            diffuse_color[1],
                            diffuse_color[2],
                            material_index,
                        )
                        vertCols[key] = [-1]
                    else:
                        diffuse_color = material.diffuse_color[:]
                        key = (
                            diffuse_color[0],
                            diffuse_color[1],
                            diffuse_color[2],
                            material_index,
                        )
                        vertCols[key] = [-1]

        tab_write(file, "\n}\n")
        # Face indices
        tab_write(file, "\nface_indices {\n")
        tab_write(file, "%d" % (len(me_faces)))  # faces count
        tab_str = tab * tab_level

        for fi, f in enumerate(me_faces):
            fv = faces_verts[fi]
            material_index = f.material_index

            if vcol_layer:
                cols = [vcol_layer[loop_index].color[:] for loop_index in f.loops]

            if not me_materials or (
                me_materials[material_index] is None
            ):  # No materials
                if linebreaksinlists:
                    file.write(",\n")
                    # vert count
                    file.write(tab_str + "<%d,%d,%d>" % (fv[0], fv[1], fv[2]))
                else:
                    file.write(", ")
                    file.write("<%d,%d,%d>" % (fv[0], fv[1], fv[2]))  # vert count
            else:
                material = me_materials[material_index]
                if me.vertex_colors:  # and material.pov.use_vertex_color_paint:
                    # Color per vertex - vertex color

                    col1 = cols[0]
                    col2 = cols[1]
                    col3 = cols[2]

                    ci1 = vertCols[col1[0], col1[1], col1[2], material_index][0]
                    ci2 = vertCols[col2[0], col2[1], col2[2], material_index][0]
                    ci3 = vertCols[col3[0], col3[1], col3[2], material_index][0]
                else:
                    # Color per material - flat material color
                    if material.pov_subsurface_scattering.use:
                        diffuse_color = [
                            i * j
                            for i, j in zip(
                                material.pov_subsurface_scattering.color[:],
                                material.diffuse_color[:],
                            )
                        ]
                    else:
                        diffuse_color = material.diffuse_color[:]
                    ci1 = ci2 = ci3 = vertCols[
                        diffuse_color[0],
                        diffuse_color[1],
                        diffuse_color[2],
                        f.material_index,
                    ][0]
                    # ci are zero based index so we'll subtract 1 from them
                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str
                        + "<%d,%d,%d>, %d,%d,%d"
                        % (
                            fv[0],
                            fv[1],
                            fv[2],
                            ci1 - 1,
                            ci2 - 1,
                            ci3 - 1,
                        )
                    )  # vert count
                else:
                    file.write(", ")
                    file.write(
                        "<%d,%d,%d>, %d,%d,%d"
                        % (
                            fv[0],
                            fv[1],
                            fv[2],
                            ci1 - 1,
                            ci2 - 1,
                            ci3 - 1,
                        )
                    )  # vert count

        file.write("\n")
        tab_write(file, "}\n")

        # normal_indices indices
        tab_write(file, "normal_indices {\n")
        tab_write(file, "%d" % (len(me_faces)))  # faces count
        tab_str = tab * tab_level
        for fi, fv in enumerate(faces_verts):

            if me_faces[fi].use_smooth:
                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str
                        + "<%d,%d,%d>"
                        % (
                            uniqueNormals[verts_normals[fv[0]]][0],
                            uniqueNormals[verts_normals[fv[1]]][0],
                            uniqueNormals[verts_normals[fv[2]]][0],
                        )
                    )  # vert count
                else:
                    file.write(", ")
                    file.write(
                        "<%d,%d,%d>"
                        % (
                            uniqueNormals[verts_normals[fv[0]]][0],
                            uniqueNormals[verts_normals[fv[1]]][0],
                            uniqueNormals[verts_normals[fv[2]]][0],
                        )
                    )  # vert count
            else:
                idx = uniqueNormals[faces_normals[fi]][0]
                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str + "<%d,%d,%d>" % (idx, idx, idx)
                    )  # vert count
                else:
                    file.write(", ")
                    file.write("<%d,%d,%d>" % (idx, idx, idx))  # vert count

        file.write("\n")
        tab_write(file, "}\n")

        if uv_layer:
            tab_write(file, "uv_indices {\n")
            tab_write(file, "%d" % (len(me_faces)))  # faces count
            tab_str = tab * tab_level
            for f in me_faces:
                uvs = [uv_layer[loop_index].uv[:] for loop_index in f.loops]

                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str
                        + "<%d,%d,%d>"
                        % (
                            uniqueUVs[uvs[0]][0],
                            uniqueUVs[uvs[1]][0],
                            uniqueUVs[uvs[2]][0],
                        )
                    )
                else:
                    file.write(", ")
                    file.write(
                        "<%d,%d,%d>"
                        % (
                            uniqueUVs[uvs[0]][0],
                            uniqueUVs[uvs[1]][0],
                            uniqueUVs[uvs[2]][0],
                        )
                    )

            file.write("\n")
            tab_write(file, "}\n")

        # XXX BOOLEAN MODIFIER
        write_object_csg_inside_vector(ob, file)

        if me.materials:
            try:
                material = me.materials[0]  # dodgy
                write_object_material_interior(file, material, ob, tab_write)
            except IndexError:
                print(me)

        # POV object modifiers such as
        # hollow / sturm / double_illuminate etc.
        write_object_modifiers(ob, file)

        # Importance for radiosity sampling added here:
        tab_write(file, "radiosity { \n")
        tab_write(file, "importance %3g \n" % importance)
        tab_write(file, "}\n")

        tab_write(file, "}\n")  # End of mesh block
    else:
        facesMaterials = []  # WARNING!!!!!!!!!!!!!!!!!!!!!!
        if me_materials:
            new_me_faces_mat_idx = (f for f in me_faces if f.material_index not in
                                       facesMaterials)
            for f in new_me_faces_mat_idx:
                facesMaterials.append(f.material_index)
        # No vertex colors, so write material colors as vertex colors

        for i, material in enumerate(me_materials):
            if (
                material and material.pov.material_use_nodes is False
            ):  # WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                # Multiply diffuse with SSS Color
                if material.pov_subsurface_scattering.use:
                    diffuse_color = [
                        i * j
                        for i, j in zip(
                            material.pov_subsurface_scattering.color[:],
                            material.diffuse_color[:],
                        )
                    ]
                    key = (
                        diffuse_color[0],
                        diffuse_color[1],
                        diffuse_color[2],
                        i,
                    )  # i == f.mat
                    vertCols[key] = [-1]
                else:
                    diffuse_color = material.diffuse_color[:]
                    key = (
                        diffuse_color[0],
                        diffuse_color[1],
                        diffuse_color[2],
                        i,
                    )  # i == f.mat
                    vertCols[key] = [-1]

                idx = 0
                texturing.local_material_names = []
                for col, index in vertCols.items():
                    # if me_materials:
                    mater = me_materials[col[3]]
                    if me_materials is not None:
                        texturing.write_texture_influence(
                            file,
                            mater,
                            material_names_dictionary,
                            image_format,
                            img_map,
                            img_map_transforms,
                            tab_write,
                            comments,
                            col,
                            preview_dir,
                            unpacked_images,
                        )
                    # ------------------------------------------------
                    index[0] = idx
                    idx += 1

        # Vert Colors
        tab_write(file, "texture_list {\n")
        # In case there's is no material slot, give at least one texture
        # (an empty one so it uses pov default)
        if len(vertCols) != 0:
            tab_write(
                file, "%s" % (len(vertCols))
            )  # vert count
        else:
            tab_write(file, "1")
        # below "material" alias, added check obj.active_material
        # to avoid variable referenced before assignment error
        try:
            material = ob.active_material
        except IndexError:
            # when no material slot exists,
            material = None

        # WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if (
            material
            and ob.active_material is not None
            and not material.pov.material_use_nodes
            and not material.use_nodes
        ):
            if material.pov.replacement_text != "":
                file.write("\n")
                file.write(" texture{%s}\n" % material.pov.replacement_text)

            else:
                # Loop through declared materials list
                # global local_material_names
                for cMN in texturing.local_material_names:
                    if material != "Default":
                        file.write("\n texture{MAT_%s}\n" % cMN)
                        # use string_strip_hyphen(material_names_dictionary[material]))
                        # or Something like that to clean up the above?
        elif material and material.pov.material_use_nodes:
            for index in facesMaterials:
                faceMaterial = string_strip_hyphen(
                    bpy.path.clean_name(me_materials[index].name)
                )
                file.write("\n texture{%s}\n" % faceMaterial)
        # END!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        elif vertCols:
            for cMN in vertCols: # or in texturing.local_material_names:
                # if possible write only one, though
                file.write(" texture{}\n")
        else:
            file.write(" texture{}\n")
        tab_write(file, "}\n")

        # Face indices
        tab_write(file, "face_indices {\n")
        tab_write(file, "%d" % (len(me_faces)))  # faces count
        tab_str = tab * tab_level

        for fi, f in enumerate(me_faces):
            fv = faces_verts[fi]
            material_index = f.material_index

            if vcol_layer:
                cols = [vcol_layer[loop_index].color[:] for loop_index in f.loops]

            if (
                not me_materials or me_materials[material_index] is None
            ):  # No materials
                if linebreaksinlists:
                    file.write(",\n")
                    # vert count
                    file.write(tab_str + "<%d,%d,%d>" % (fv[0], fv[1], fv[2]))
                else:
                    file.write(", ")
                    file.write("<%d,%d,%d>" % (fv[0], fv[1], fv[2]))  # vert count
            else:
                material = me_materials[material_index]
                ci1 = ci2 = ci3 = f.material_index
                if me.vertex_colors:  # and material.pov.use_vertex_color_paint:
                    # Color per vertex - vertex color

                    col1 = cols[0]
                    col2 = cols[1]
                    col3 = cols[2]

                    ci1 = vertCols[col1[0], col1[1], col1[2], material_index][0]
                    ci2 = vertCols[col2[0], col2[1], col2[2], material_index][0]
                    ci3 = vertCols[col3[0], col3[1], col3[2], material_index][0]
                elif material.pov.material_use_nodes:
                    ci1 = ci2 = ci3 = 0
                else:
                    # Color per material - flat material color
                    if material.pov_subsurface_scattering.use:
                        diffuse_color = [
                            i * j
                            for i, j in zip(
                                material.pov_subsurface_scattering.color[:],
                                material.diffuse_color[:],
                            )
                        ]
                    else:
                        diffuse_color = material.diffuse_color[:]
                    ci1 = ci2 = ci3 = vertCols[
                        diffuse_color[0],
                        diffuse_color[1],
                        diffuse_color[2],
                        f.material_index,
                    ][0]

                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str
                        + "<%d,%d,%d>, %d,%d,%d"
                        % (fv[0], fv[1], fv[2], ci1, ci2, ci3)
                    )  # vert count
                else:
                    file.write(", ")
                    file.write(
                        "<%d,%d,%d>, %d,%d,%d"
                        % (fv[0], fv[1], fv[2], ci1, ci2, ci3)
                    )  # vert count

        file.write("\n")
        tab_write(file, "}\n")

        # normal_indices indices
        tab_write(file, "normal_indices {\n")
        tab_write(file, "%d" % (len(me_faces)))  # faces count
        tab_str = tab * tab_level
        for fi, fv in enumerate(faces_verts):
            if me_faces[fi].use_smooth:
                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str
                        + "<%d,%d,%d>"
                        % (
                            uniqueNormals[verts_normals[fv[0]]][0],
                            uniqueNormals[verts_normals[fv[1]]][0],
                            uniqueNormals[verts_normals[fv[2]]][0],
                        )
                    )  # vert count
                else:
                    file.write(", ")
                    file.write(
                        "<%d,%d,%d>"
                        % (
                            uniqueNormals[verts_normals[fv[0]]][0],
                            uniqueNormals[verts_normals[fv[1]]][0],
                            uniqueNormals[verts_normals[fv[2]]][0],
                        )
                    )  # vert count
            else:
                idx = uniqueNormals[faces_normals[fi]][0]
                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str + "<%d,%d,%d>" % (idx, idx, idx)
                    )  # vertcount
                else:
                    file.write(", ")
                    file.write("<%d,%d,%d>" % (idx, idx, idx))  # vert count

        file.write("\n")
        tab_write(file, "}\n")

        if uv_layer:
            tab_write(file, "uv_indices {\n")
            tab_write(file, "%d" % (len(me_faces)))  # faces count
            tab_str = tab * tab_level
            for f in me_faces:
                uvs = [uv_layer[loop_index].uv[:] for loop_index in f.loops]

                if linebreaksinlists:
                    file.write(",\n")
                    file.write(
                        tab_str
                        + "<%d,%d,%d>"
                        % (
                            uniqueUVs[uvs[0]][0],
                            uniqueUVs[uvs[1]][0],
                            uniqueUVs[uvs[2]][0],
                        )
                    )
                else:
                    file.write(", ")
                    file.write(
                        "<%d,%d,%d>"
                        % (
                            uniqueUVs[uvs[0]][0],
                            uniqueUVs[uvs[1]][0],
                            uniqueUVs[uvs[2]][0],
                        )
                    )

            file.write("\n")
            tab_write(file, "}\n")

        # XXX BOOLEAN
        write_object_csg_inside_vector(ob, file)
        if me.materials:
            try:
                material = me.materials[0]  # dodgy
                write_object_material_interior(file, material, ob, tab_write)
            except IndexError:
                print(me)

        # POV object modifiers such as
        # hollow / sturm / double_illuminate etc.
        write_object_modifiers(ob, file)

        # Importance for radiosity sampling added here:
        tab_write(file, "radiosity { \n")
        tab_write(file, "importance %3g \n" % importance)
        tab_write(file, "}\n")

        tab_write(file, "}\n")  # End of mesh block

    ob_eval.to_mesh_clear()
    return True
