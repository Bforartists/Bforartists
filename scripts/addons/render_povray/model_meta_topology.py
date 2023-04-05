# SPDX-License-Identifier: GPL-2.0-or-later

"""Translate Blender meta balls to POV blobs."""

import bpy
from .shading import write_object_material_interior

def export_meta(file, metas, material_names_dictionary, tab_write, DEF_MAT_NAME):
    """write all POV blob primitives and Blender Metas to exported file """
    # TODO - blenders 'motherball' naming is not supported.

    from .render import (
        safety,
        global_matrix,
        write_matrix,
        comments,
    )
    if comments and len(metas) >= 1:
        file.write("//--Blob objects--\n\n")
    # Get groups of metaballs by blender name prefix.
    meta_group = {}
    meta_elems = {}
    for meta_ob in metas:
        prefix = meta_ob.name.split(".")[0]
        if prefix not in meta_group:
            meta_group[prefix] = meta_ob  # .data.threshold
        elems = [
            (elem, meta_ob)
            for elem in meta_ob.data.elements
            if elem.type in {'BALL', 'ELLIPSOID', 'CAPSULE', 'CUBE', 'PLANE'}
        ]
        if prefix in meta_elems:
            meta_elems[prefix].extend(elems)
        else:
            meta_elems[prefix] = elems

        # empty metaball
        if not elems:
            tab_write(file, "\n//dummy sphere to represent empty meta location\n")
            tab_write(file,
                      "sphere {<%.6g, %.6g, %.6g>,0 pigment{rgbt 1} "
                      "no_image no_reflection no_radiosity "
                      "photons{pass_through collect off} hollow}\n\n"
                      % (meta_ob.location.x, meta_ob.location.y, meta_ob.location.z)
                      )  # meta_ob.name > povdataname)
            return

        # other metaballs

        for mg, mob in meta_group.items():
            if len(meta_elems[mg]) != 0:
                tab_write(file, "blob{threshold %.4g // %s \n" % (mob.data.threshold, mg))
                for elems in meta_elems[mg]:
                    elem = elems[0]
                    loc = elem.co
                    stiffness = elem.stiffness
                    if elem.use_negative:
                        stiffness = -stiffness
                    if elem.type == 'BALL':
                        tab_write(file,
                                  "sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g "
                                  % (loc.x, loc.y, loc.z, elem.radius, stiffness)
                                  )
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")
                    elif elem.type == 'ELLIPSOID':
                        tab_write(file,
                                  "sphere{ <%.6g, %.6g, %.6g>,%.4g,%.4g "
                                  % (
                                      loc.x / elem.size_x,
                                      loc.y / elem.size_y,
                                      loc.z / elem.size_z,
                                      elem.radius,
                                      stiffness,
                                  )
                                  )
                        tab_write(file,
                                  "scale <%.6g, %.6g, %.6g>"
                                  % (elem.size_x, elem.size_y, elem.size_z)
                                  )
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")
                    elif elem.type == 'CAPSULE':
                        tab_write(file,
                                  "cylinder{ <%.6g, %.6g, %.6g>,<%.6g, %.6g, %.6g>,%.4g,%.4g "
                                  % (
                                      (loc.x - elem.size_x),
                                      loc.y,
                                      loc.z,
                                      (loc.x + elem.size_x),
                                      loc.y,
                                      loc.z,
                                      elem.radius,
                                      stiffness,
                                  )
                                  )
                        # tab_write(file, "scale <%.6g, %.6g, %.6g>" % (elem.size_x, elem.size_y, elem.size_z))
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")

                    elif elem.type == 'CUBE':
                        tab_write(file,
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
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")
                        tab_write(file,
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
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")
                        tab_write(file,
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
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")

                    elif elem.type == 'PLANE':
                        tab_write(file,
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
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")
                        tab_write(file,
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
                        write_matrix(file, global_matrix @ elems[1].matrix_world)
                        tab_write(file, "}\n")

                try:
                    one_material = elems[1].data.materials[
                        0
                    ]  # lame! - blender can't do anything else.
                except BaseException as e:
                    print(e.__doc__)
                    print('An exception occurred: {}'.format(e))
                    one_material = None
                if one_material:
                    diffuse_color = one_material.diffuse_color
                    trans = 1.0 - one_material.pov.alpha
                    if (
                            one_material.pov.use_transparency
                            and one_material.pov.transparency_method == 'RAYTRACE'
                    ):
                        pov_filter = one_material.pov_raytrace_transparency.filter * (
                                1.0 - one_material.pov.alpha
                        )
                        trans = (1.0 - one_material.pov.alpha) - pov_filter
                    else:
                        pov_filter = 0.0
                    material_finish = material_names_dictionary[one_material.name]
                    tab_write(file,
                              "pigment {srgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} \n"
                              % (
                                  diffuse_color[0],
                                  diffuse_color[1],
                                  diffuse_color[2],
                                  pov_filter,
                                  trans,
                              )
                              )
                    tab_write(file, "finish{%s} " % safety(material_finish, ref_level_bound=2))
                else:
                    material_finish = DEF_MAT_NAME
                    trans = 0.0
                    tab_write(file,
                              "pigment{srgbt<1,1,1,%.3g>} finish{%s} "
                              % (trans, safety(material_finish, ref_level_bound=2))
                              )

                    write_object_material_interior(file, one_material, mob, tab_write)
                    # write_object_material_interior(file, one_material, elems[1])
                    tab_write(file, "radiosity{importance %3g}\n" % mob.pov.importance_value)

                tab_write(file, "}\n\n")  # End of Metaball block


'''
        meta = ob.data

        # important because no elements will break parsing.
        elements = [elem for elem in meta.elements if elem.type in {'BALL', 'ELLIPSOID'}]

        if elements:
            tab_write(file, "blob {\n")
            tab_write(file, "threshold %.4g\n" % meta.threshold)
            importance = ob.pov.importance_value

            try:
                material = meta.materials[0]  # lame! - blender can't do anything else.
            except:
                material = None

            for elem in elements:
                loc = elem.co

                stiffness = elem.stiffness
                if elem.use_negative:
                    stiffness = - stiffness

                if elem.type == 'BALL':

                    tab_write(file, "sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" %
                             (loc.x, loc.y, loc.z, elem.radius, stiffness))

                    # After this wecould do something simple like...
                    #     "pigment {Blue} }"
                    # except we'll write the color

                elif elem.type == 'ELLIPSOID':
                    # location is modified by scale
                    tab_write(file, "sphere { <%.6g, %.6g, %.6g>, %.4g, %.4g }\n" %
                             (loc.x / elem.size_x,
                              loc.y / elem.size_y,
                              loc.z / elem.size_z,
                              elem.radius, stiffness))
                    tab_write(file, "scale <%.6g, %.6g, %.6g> \n" %
                             (elem.size_x, elem.size_y, elem.size_z))

            if material:
                diffuse_color = material.diffuse_color
                trans = 1.0 - material.pov.alpha
                if material.pov.use_transparency and material.pov.transparency_method == 'RAYTRACE':
                    pov_filter = material.pov_raytrace_transparency.filter * (1.0 -
                    material.pov.alpha)
                    trans = (1.0 - material.pov.alpha) - pov_filter
                else:
                    pov_filter = 0.0

                material_finish = material_names_dictionary[material.name]

                tab_write(file, "pigment {srgbft<%.3g, %.3g, %.3g, %.3g, %.3g>} \n" %
                         (diffuse_color[0], diffuse_color[1], diffuse_color[2],
                          pov_filter, trans))
                tab_write(file, "finish {%s}\n" % safety(material_finish, ref_level_bound=2))

            else:
                tab_write(file, "pigment {srgb 1} \n")
                # Write the finish last.
                tab_write(file, "finish {%s}\n" % (safety(DEF_MAT_NAME, ref_level_bound=2)))

            write_object_material_interior(file, material, elems[1], tab_write)

            write_matrix(file, global_matrix @ ob.matrix_world)
            # Importance for radiosity sampling added here
            tab_write(file, "radiosity { \n")
            # importance > ob.pov.importance_value
            tab_write(file, "importance %3g \n" % importance)
            tab_write(file, "}\n")

            tab_write(file, "}\n")  # End of Metaball block

            if comments and len(metas) >= 1:
                file.write("\n")
'''
