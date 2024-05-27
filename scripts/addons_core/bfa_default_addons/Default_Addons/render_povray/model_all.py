# SPDX-FileCopyrightText: 2022 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""Translate to POV the control point compound geometries.

Such as polygon meshes or curve based shapes.
"""

# --------
# -- Faster mesh export ...one day
# import numpy as np
# --------
import bpy
from . import texturing  # for how textures influence shaders
from . import model_poly_topology
# from .texturing import local_material_names
from .scenography import export_smoke


def matrix_as_pov_string(matrix):
    """Translate some transform matrix from Blender UI
    to POV syntax and return that string"""
    return (
        "matrix <"
        "%.6f, %.6f, %.6f, "
        "%.6f, %.6f, %.6f, "
        "%.6f, %.6f, %.6f, "
        "%.6f, %.6f, %.6f"
        ">\n"
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

#    objectNames = {}
DEF_OBJ_NAME = "Default"


def objects_loop(
    file,
    scene,
    sel,
    csg,
    material_names_dictionary,
    unpacked_images,
    tab_level,
    tab_write,
    info_callback,
):
    # global preview_dir
    # global smoke_path
    # global global_matrix
    # global comments

    # global tab
    """write all meshes as POV mesh2{} syntax to exported file"""
    # # some numpy functions to speed up mesh export NOT IN USE YET
    # # Current 2.93 beta numpy linking has troubles so definitions commented off for now

    # # TODO: also write a numpy function to read matrices at object level?
    # # feed below with mesh object.data, but only after doing data.calc_loop_triangles()
    # def read_verts_co(self, mesh):
    # #'float64' would be a slower 64-bit floating-point number numpy datatype
    # # using 'float32' vert coordinates for now until any issue is reported
    # mverts_co = np.zeros((len(mesh.vertices) * 3), dtype=np.float32)
    # mesh.vertices.foreach_get("co", mverts_co)
    # return np.reshape(mverts_co, (len(mesh.vertices), 3))

    # def read_verts_idx(self, mesh):
    # mverts_idx = np.zeros((len(mesh.vertices)), dtype=np.int64)
    # mesh.vertices.foreach_get("index", mverts_idx)
    # return np.reshape(mverts_idx, (len(mesh.vertices), 1))

    # def read_verts_norms(self, mesh):
    # #'float64' would be a slower 64-bit floating-point number numpy datatype
    # # using less accurate 'float16' normals for now until any issue is reported
    # mverts_no = np.zeros((len(mesh.vertices) * 3), dtype=np.float16)
    # mesh.vertices.foreach_get("normal", mverts_no)
    # return np.reshape(mverts_no, (len(mesh.vertices), 3))

    # def read_faces_idx(self, mesh):
    # mfaces_idx = np.zeros((len(mesh.loop_triangles)), dtype=np.int64)
    # mesh.loop_triangles.foreach_get("index", mfaces_idx)
    # return np.reshape(mfaces_idx, (len(mesh.loop_triangles), 1))

    # def read_faces_verts_indices(self, mesh):
    # mfaces_verts_idx = np.zeros((len(mesh.loop_triangles) * 3), dtype=np.int64)
    # mesh.loop_triangles.foreach_get("vertices", mfaces_verts_idx)
    # return np.reshape(mfaces_verts_idx, (len(mesh.loop_triangles), 3))

    # # Why is below different from vertex indices?
    # def read_faces_verts_loops(self, mesh):
    # mfaces_verts_loops = np.zeros((len(mesh.loop_triangles) * 3), dtype=np.int64)
    # mesh.loop_triangles.foreach_get("loops", mfaces_verts_loops)
    # return np.reshape(mfaces_verts_loops, (len(mesh.loop_triangles), 3))

    # def read_faces_norms(self, mesh):
    # #'float64' would be a slower 64-bit floating-point number numpy datatype
    # # using less accurate 'float16' normals for now until any issue is reported
    # mfaces_no = np.zeros((len(mesh.loop_triangles) * 3), dtype=np.float16)
    # mesh.loop_triangles.foreach_get("normal", mfaces_no)
    # return np.reshape(mfaces_no, (len(mesh.loop_triangles), 3))

    # def read_faces_smooth(self, mesh):
    # mfaces_smth = np.zeros((len(mesh.loop_triangles) * 1), dtype=np.bool)
    # mesh.loop_triangles.foreach_get("use_smooth", mfaces_smth)
    # return np.reshape(mfaces_smth, (len(mesh.loop_triangles), 1))

    # def read_faces_material_indices(self, mesh):
    # mfaces_mats_idx = np.zeros((len(mesh.loop_triangles)), dtype=np.int16)
    # mesh.loop_triangles.foreach_get("material_index", mfaces_mats_idx)
    # return np.reshape(mfaces_mats_idx, (len(mesh.loop_triangles), 1))

    #        obmatslist = []
    #        def hasUniqueMaterial():
    #            # Grab materials attached to object instances ...
    #            if hasattr(obj, 'material_slots'):
    #                for ms in obj.material_slots:
    #                    if ms.material is not None and ms.link == 'OBJECT':
    #                        if ms.material in obmatslist:
    #                            return False
    #                        else:
    #                            obmatslist.append(ms.material)
    #                            return True
    #        def hasObjectMaterial(obj):
    #            # Grab materials attached to object instances ...
    #            if hasattr(obj, 'material_slots'):
    #                for ms in obj.material_slots:
    #                    if ms.material is not None and ms.link == 'OBJECT':
    #                        # If there is at least one material slot linked to the object
    #                        # and not the data (mesh), always create a new, "private" data instance.
    #                        return True
    #            return False
    # For objects using local material(s) only!
    # This is a mapping between a tuple (dataname, material_names_dictionary, ...),
    # and the POV dataname.
    # As only objects using:
    #     * The same data.
    #     * EXACTLY the same materials, in EXACTLY the same sockets.
    # ... can share a same instance in POV export.
    from .render import (
        string_strip_hyphen,
        global_matrix,
        tab,
        comments,
    )
    from .render_core import (
        preview_dir,
        smoke_path,
    )
    from .model_primitives import write_object_modifiers
    from .shading import write_object_material_interior
    from .scenography import image_format, img_map, img_map_transforms

    linebreaksinlists = scene.pov.list_lf_enable and not scene.pov.tempfiles_enable
    obmats2data = {}


    def check_object_materials(obj, obj_name, dataname):
        """Compare other objects exported material slots to avoid rewriting duplicates"""
        if hasattr(obj, "material_slots"):
            has_local_mats = False
            key = [dataname]
            for ms in obj.material_slots:
                if ms.material is not None:
                    key.append(ms.material.name)
                    if ms.link == "OBJECT" and not has_local_mats:
                        has_local_mats = True
                else:
                    # Even if the slot is empty, it is important to grab it...
                    key.append("")
            if has_local_mats:
                # If this object uses local material(s), lets find if another object
                # using the same data and exactly the same list of materials
                # (in the same slots) has already been processed...
                # Note that here also, we use object name as new, unique dataname for Pov.
                key = tuple(key)  # Lists are not hashable...
                if key not in obmats2data:
                    obmats2data[key] = obj_name
                return obmats2data[key]
        return None

    data_ref = {}

    def store(scene, ob, name, dataname, matrix):
        # The Object needs to be written at least once but if its data is
        # already in data_ref this has already been done.
        # This func returns the "povray" name of the data, or None
        # if no writing is needed.
        if ob.is_modified(scene, "RENDER"):
            # Data modified.
            # Create unique entry in data_ref by using object name
            # (always unique in Blender) as data name.
            data_ref[name] = [(name, matrix_as_pov_string(matrix))]
            return name
        # Here, we replace dataname by the value returned by check_object_materials, only if
        # it is not evaluated to False (i.e. only if the object uses some local material(s)).
        dataname = check_object_materials(ob, name, dataname) or dataname
        if dataname in data_ref:
            # Data already known, just add the object instance.
            data_ref[dataname].append((name, matrix_as_pov_string(matrix)))
            # No need to write data
            return None
        # Else (no return yet): Data not yet processed, create a new entry in data_ref.
        data_ref[dataname] = [(name, matrix_as_pov_string(matrix))]
        return dataname

    ob_num = 0
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for ob in sel:
        # Using depsgraph
        ob = bpy.data.objects[ob.name].evaluated_get(depsgraph)

        # subtract original from the count of their instances as were not counted before 2.8
        if (ob.is_instancer and ob.original != ob):
            continue

        ob_num += 1

        # XXX I moved all those checks here, as there is no need to compute names
        #     for object we won't export here!
        if ob.type in {
            "LIGHT",
            "CAMERA",  # 'EMPTY', #empties can bear dupligroups
            "META",
            "ARMATURE",
            "LATTICE",
        }:
            continue
        fluid_found = False
        for mod in ob.modifiers:
            if mod and hasattr(mod, "fluid_type"):
                fluid_found = True
                if mod.fluid_type == "DOMAIN":
                    if mod.domain_settings.domain_type == "GAS":
                        export_smoke(file, ob.name, smoke_path, comments, global_matrix)
                    break  # don't render domain mesh, skip to next object.
                if mod.fluid_type == "FLOW":  # The domain contains all the smoke. so that's it.
                    if mod.flow_settings.flow_type == "SMOKE":  # Check how liquids behave
                        break  # don't render smoke flow emitter mesh either, skip to next object.
        if fluid_found:
            return
        # No fluid found
        if hasattr(ob, "particle_systems"):
            # Importing function Export Hair
            # here rather than at the top recommended for addons startup footprint
            from .particles import export_hair

            for p_sys in ob.particle_systems:
                for particle_mod in [
                    m
                    for m in ob.modifiers
                    if (m is not None) and (m.type == "PARTICLE_SYSTEM")
                ]:
                    if (
                        (p_sys.settings.render_type == "PATH")
                        and particle_mod.show_render
                        and (p_sys.name == particle_mod.particle_system.name)
                    ):
                        export_hair(file, ob, particle_mod, p_sys, global_matrix)
            if not ob.show_instancer_for_render:
                continue  # don't render emitter mesh, skip to next object.

        # ------------------------------------------------
        # Generating a name for object just like materials to be able to use it
        # (baking for now or anything else).
        # XXX I don't understand that if we are here, sel if a non-empty iterable,
        #     so this condition is always True, IMO -- mont29
        # EMPTY type objects treated  a little further below -- MR

        # modified elif to if below as non EMPTY objects can also be instancers
        if ob.is_instancer:
            if ob.instance_type == "COLLECTION":
                name_orig = "OB" + ob.name
                dataname_orig = "DATA" + ob.instance_collection.name
            else:
                # hoping only dupligroups have several source datablocks
                # ob_dupli_list_create(scene) #deprecated in 2.8
                for eachduplicate in depsgraph.object_instances:
                    # Real dupli instance filtered because
                    # original included in list since 2.8
                    if eachduplicate.is_instance:
                        dataname_orig = "DATA" + eachduplicate.object.name
                # obj.dupli_list_clear() #just don't store any reference to instance since 2.8
        elif ob.data:  # not an EMPTY type object
            name_orig = "OB" + ob.name
            dataname_orig = "DATA" + ob.data.name
        elif ob.type == "EMPTY":
            name_orig = "OB" + ob.name
            dataname_orig = "DATA" + ob.name
        else:
            name_orig = DEF_OBJ_NAME
            dataname_orig = DEF_OBJ_NAME
        name = string_strip_hyphen(bpy.path.clean_name(name_orig))
        dataname = string_strip_hyphen(bpy.path.clean_name(dataname_orig))
        #            for slot in obj.material_slots:
        #                if slot.material is not None and slot.link == 'OBJECT':
        #                    obmaterial = slot.material

        # ------------------------------------------------

        if info_callback:
            info_callback("Object %2.d of %2.d (%s)" % (ob_num, len(sel), ob.name))

        me = ob.data

        matrix = global_matrix @ ob.matrix_world
        povdataname = store(scene, ob, name, dataname, matrix)
        if povdataname is None:
            print("This is an instance of " + name)
            continue

        print("Writing Down First Occurrence of " + name)

        # ------------ Mesh Primitives ------------ #
        # special export_curves() function takes care of writing
        # lathe, sphere_sweep, birail, and loft except with modifiers
        # converted to mesh
        if not ob.is_modified(scene, "RENDER"):
            if ob.type == "CURVE" and (
                ob.pov.curveshape in {"lathe", "sphere_sweep", "loft"}
            ):
                continue  # Don't render proxy mesh, skip to next object
        # pov_mat_name = "Default_texture" # Not used...remove?

        # Implicit else-if (as not skipped by previous "continue")
        # which itself has no "continue" (to combine custom pov code)?, so Keep this last.
        # For originals, but not their instances, attempt to export mesh:
        if not ob.is_instancer:
            # except duplis which should be instances groups for now but all duplis later
            if ob.type == "EMPTY":
                # XXX Should we only write this once and instantiate the same for every
                # empty in the final matrix writing, or even no matrix and just a comment
                # with empty object transforms ?
                tab_write(file, "\n//dummy sphere to represent Empty location\n")
                tab_write(
                    file,
                    "#declare %s =sphere {<0, 0, 0>,0 pigment{rgbt 1} no_image no_reflection no_radiosity photons{pass_through collect off} hollow}\n"
                    % povdataname,
                )
                continue  # Don't render empty object but this is later addition, watch it.
            if ob.pov.object_as:
                pass
            else:
                model_poly_topology.export_mesh(file, ob, povdataname,
                                                                  material_names_dictionary,
                                                                  unpacked_images,
                                                                  tab_level, tab_write, linebreaksinlists)

        # ------------ Povray Primitives ------------ #
        #  Also implicit elif (continue) clauses and sorted after mesh
        #  as less often used.
        if ob.pov.object_as == "PLANE":
            tab_write(file, "#declare %s = plane{ <0,0,1>,0\n" % povdataname)
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            # tab_write(file, "rotate x*90\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "SPHERE":

            tab_write(
                file,
                "#declare %s = sphere { 0,%6f\n" % (povdataname, ob.pov.sphere_radius),
            )
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            # tab_write(file, "rotate x*90\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "BOX":
            tab_write(file, "#declare %s = box { -1,1\n" % povdataname)
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            # tab_write(file, "rotate x*90\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "CONE":
            br = ob.pov.cone_base_radius
            cr = ob.pov.cone_cap_radius
            bz = ob.pov.cone_base_z
            cz = ob.pov.cone_cap_z
            tab_write(
                file,
                "#declare %s = cone { <0,0,%.4f>,%.4f,<0,0,%.4f>,%.4f\n"
                % (povdataname, bz, br, cz, cr),
            )
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            # tab_write(file, "rotate x*90\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "CYLINDER":
            r = ob.pov.cylinder_radius
            x2 = ob.pov.cylinder_location_cap[0]
            y2 = ob.pov.cylinder_location_cap[1]
            z2 = ob.pov.cylinder_location_cap[2]
            tab_write(
                file,
                "#declare %s = cylinder { <0,0,0>,<%6f,%6f,%6f>,%6f\n"
                % (povdataname, x2, y2, z2, r),
            )
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            # cylinders written at origin, translated below
            write_object_modifiers(ob, file)
            # tab_write(file, "rotate x*90\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "HEIGHT_FIELD":
            data = ""
            filename = ob.pov.hf_filename
            data += '"%s"' % filename
            gamma = " gamma %.4f" % ob.pov.hf_gamma
            data += gamma
            if ob.pov.hf_premultiplied:
                data += " premultiplied on"
            if ob.pov.hf_smooth:
                data += " smooth"
            if ob.pov.hf_water > 0:
                data += " water_level %.4f" % ob.pov.hf_water
            # hierarchy = obj.pov.hf_hierarchy
            tab_write(file, "#declare %s = height_field { %s\n" % (povdataname, data))
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            tab_write(file, "rotate x*90\n")
            tab_write(file, "translate <-0.5,0.5,0>\n")
            tab_write(file, "scale <0,-1,0>\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "TORUS":
            tab_write(
                file,
                "#declare %s = torus { %.4f,%.4f\n"
                % (
                    povdataname,
                    ob.pov.torus_major_radius,
                    ob.pov.torus_minor_radius,
                ),
            )
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            tab_write(file, "rotate x*90\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "PARAMETRIC":
            tab_write(file, "#declare %s = parametric {\n" % povdataname)
            tab_write(file, "function { %s }\n" % ob.pov.x_eq)
            tab_write(file, "function { %s }\n" % ob.pov.y_eq)
            tab_write(file, "function { %s }\n" % ob.pov.z_eq)
            tab_write(
                file,
                "<%.4f,%.4f>, <%.4f,%.4f>\n"
                % (ob.pov.u_min, ob.pov.v_min, ob.pov.u_max, ob.pov.v_max),
            )
            # Previous to 3.8 default max_gradient 1.0 was too slow
            tab_write(file, "max_gradient 0.001\n")
            if ob.pov.contained_by == "sphere":
                tab_write(file, "contained_by { sphere{0, 2} }\n")
            else:
                tab_write(file, "contained_by { box{-2, 2} }\n")
            tab_write(file, "max_gradient %.6f\n" % ob.pov.max_gradient)
            tab_write(file, "accuracy %.6f\n" % ob.pov.accuracy)
            tab_write(file, "precompute 10 x,y,z\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "ISOSURFACE_NODE":
            tab_write(file, "#declare %s = isosurface{ \n" % povdataname)
            tab_write(file, "function{ \n")
            text_name = ob.pov.iso_function_text
            if text_name:
                node_tree = bpy.context.scene.node_tree
                for node in node_tree.nodes:
                    if node.bl_idname == "IsoPropsNode" and node.label == ob.name:
                        for inp in node.inputs:
                            if inp:
                                tab_write(
                                    file,
                                    "#declare %s = %.6g;\n" % (inp.name, inp.default_value),
                                )

                text = bpy.data.texts[text_name]
                for line in text.lines:
                    split = line.body.split()
                    if split[0] != "#declare":
                        tab_write(file, "%s\n" % line.body)
            else:
                tab_write(file, "abs(x) - 2 + y")
            tab_write(file, "}\n")
            tab_write(file, "threshold %.6g\n" % ob.pov.threshold)
            tab_write(file, "max_gradient %.6g\n" % ob.pov.max_gradient)
            tab_write(file, "accuracy  %.6g\n" % ob.pov.accuracy)
            tab_write(file, "contained_by { ")
            if ob.pov.contained_by == "sphere":
                tab_write(file, "sphere {0,%.6g}}\n" % ob.pov.container_scale)
            else:
                tab_write(
                    file,
                    "box {-%.6g,%.6g}}\n"
                    % (ob.pov.container_scale, ob.pov.container_scale),
                )
            if ob.pov.all_intersections:
                tab_write(file, "all_intersections\n")
            else:
                if ob.pov.max_trace > 1:
                    tab_write(file, "max_trace %.6g\n" % ob.pov.max_trace)
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            tab_write(file, "scale %.6g\n" % (1 / ob.pov.container_scale))
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "ISOSURFACE_VIEW":
            simple_isosurface_function = ob.pov.isosurface_eq
            if simple_isosurface_function:
                tab_write(file, "#declare %s = isosurface{ \n" % povdataname)
                tab_write(file, "function{ \n")
                tab_write(file, simple_isosurface_function)
                tab_write(file, "}\n")
                tab_write(file, "threshold %.6g\n" % ob.pov.threshold)
                tab_write(file, "max_gradient %.6g\n" % ob.pov.max_gradient)
                tab_write(file, "accuracy  %.6g\n" % ob.pov.accuracy)
                tab_write(file, "contained_by { ")
                if ob.pov.contained_by == "sphere":
                    tab_write(file, "sphere {0,%.6g}}\n" % ob.pov.container_scale)
                else:
                    tab_write(
                        file,
                        "box {-%.6g,%.6g}}\n"
                        % (ob.pov.container_scale, ob.pov.container_scale),
                    )
                if ob.pov.all_intersections:
                    tab_write(file, "all_intersections\n")
                else:
                    if ob.pov.max_trace > 1:
                        tab_write(file, "max_trace %.6g\n" % ob.pov.max_trace)
                if ob.active_material:
                    # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                    try:
                        material = ob.active_material
                        write_object_material_interior(file, material, ob, tab_write)
                    except IndexError:
                        print(me)
                # tab_write(file, "texture {%s}\n"%pov_mat_name)
                tab_write(file, "scale %.6g\n" % (1 / ob.pov.container_scale))
                tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "SUPERELLIPSOID":
            tab_write(
                file,
                "#declare %s = superellipsoid{ <%.4f,%.4f>\n"
                % (povdataname, ob.pov.se_n2, ob.pov.se_n1),
            )
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "SUPERTORUS":
            rad_maj = ob.pov.st_major_radius
            rad_min = ob.pov.st_minor_radius
            ring = ob.pov.st_ring
            cross = ob.pov.st_cross
            accuracy = ob.pov.st_accuracy
            gradient = ob.pov.st_max_gradient
            # --- Inline Supertorus macro
            file.write(
                "#macro Supertorus(RMj, RMn, MajorControl, MinorControl, Accuracy, MaxGradient)\n"
            )
            file.write("   #local CP = 2/MinorControl;\n")
            file.write("   #local RP = 2/MajorControl;\n")
            file.write("   isosurface {\n")
            file.write(
                "      function { pow( pow(abs(pow(pow(abs(x),RP) + pow(abs(z),RP), 1/RP) - RMj),CP) + pow(abs(y),CP) ,1/CP) - RMn }\n"
            )
            file.write("      threshold 0\n")
            file.write(
                "      contained_by {box {<-RMj-RMn,-RMn,-RMj-RMn>, < RMj+RMn, RMn, RMj+RMn>}}\n"
            )
            file.write("      #if(MaxGradient >= 1)\n")
            file.write("         max_gradient MaxGradient\n")
            file.write("      #else\n")
            file.write("         evaluate 1, 10, 0.1\n")
            file.write("      #end\n")
            file.write("      accuracy Accuracy\n")
            file.write("   }\n")
            file.write("#end\n")
            # ---
            tab_write(
                file,
                "#declare %s = object{ Supertorus( %.4g,%.4g,%.4g,%.4g,%.4g,%.4g)\n"
                % (
                    povdataname,
                    rad_maj,
                    rad_min,
                    ring,
                    cross,
                    accuracy,
                    gradient,
                ),
            )
            if ob.active_material:
                # pov_mat_name = string_strip_hyphen(bpy.path.clean_name(obj.active_material.name))
                try:
                    material = ob.active_material
                    write_object_material_interior(file, material, ob, tab_write)
                except IndexError:
                    print(me)
            # tab_write(file, "texture {%s}\n"%pov_mat_name)
            write_object_modifiers(ob, file)
            tab_write(file, "rotate x*90\n")
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object

        if ob.pov.object_as == "POLYCIRCLE":
            # TODO write below macro Once:
            # if write_polytocircle_macro_once == 0:
            file.write("/****************************\n")
            file.write("This macro was written by 'And'.\n")
            file.write("Link:(http://news.povray.org/povray.binaries.scene-files/)\n")
            file.write("****************************/\n")
            file.write("//from math.inc:\n")
            file.write("#macro VPerp_Adjust(V, Axis)\n")
            file.write("   vnormalize(vcross(vcross(Axis, V), Axis))\n")
            file.write("#end\n")
            file.write("//Then for the actual macro\n")
            file.write("#macro Shape_Slice_Plane_2P_1V(point1, point2, clip_direct)\n")
            file.write("#local p1 = point1 + <0,0,0>;\n")
            file.write("#local p2 = point2 + <0,0,0>;\n")
            file.write("#local clip_v = vnormalize(clip_direct + <0,0,0>);\n")
            file.write("#local direct_v1 = vnormalize(p2 - p1);\n")
            file.write("#if(vdot(direct_v1, clip_v) = 1)\n")
            file.write('    #error "Shape_Slice_Plane_2P_1V error: Can\'t decide plane"\n')
            file.write("#end\n\n")
            file.write(
                "#local norm = -vnormalize(clip_v - direct_v1*vdot(direct_v1,clip_v));\n"
            )
            file.write("#local d = vdot(norm, p1);\n")
            file.write("plane{\n")
            file.write("norm, d\n")
            file.write("}\n")
            file.write("#end\n\n")
            file.write("//polygon to circle\n")
            file.write(
                "#macro Shape_Polygon_To_Circle_Blending("
                "_polygon_n, _side_face, "
                "_polygon_circumscribed_radius, "
                "_circle_radius, "
                "_height)\n"
            )
            file.write("#local n = int(_polygon_n);\n")
            file.write("#if(n < 3)\n")
            file.write("    #error\n")
            file.write("#end\n\n")
            file.write("#local front_v = VPerp_Adjust(_side_face, z);\n")
            file.write("#if(vdot(front_v, x) >= 0)\n")
            file.write("    #local face_ang = acos(vdot(-y, front_v));\n")
            file.write("#else\n")
            file.write("    #local face_ang = -acos(vdot(-y, front_v));\n")
            file.write("#end\n")
            file.write("#local polyg_ext_ang = 2*pi/n;\n")
            file.write("#local polyg_outer_r = _polygon_circumscribed_radius;\n")
            file.write("#local polyg_inner_r = polyg_outer_r*cos(polyg_ext_ang/2);\n")
            file.write("#local cycle_r = _circle_radius;\n")
            file.write("#local h = _height;\n")
            file.write("#if(polyg_outer_r < 0 | cycle_r < 0 | h <= 0)\n")
            file.write('    #error "error: each side length must be positive"\n')
            file.write("#end\n\n")
            file.write("#local multi = 1000;\n")
            file.write("#local poly_obj =\n")
            file.write("polynomial{\n")
            file.write("4,\n")
            file.write("xyz(0,2,2): multi*1,\n")
            file.write("xyz(2,0,1): multi*2*h,\n")
            file.write("xyz(1,0,2): multi*2*(polyg_inner_r-cycle_r),\n")
            file.write("xyz(2,0,0): multi*(-h*h),\n")
            file.write("xyz(0,0,2): multi*(-pow(cycle_r - polyg_inner_r, 2)),\n")
            file.write("xyz(1,0,1): multi*2*h*(-2*polyg_inner_r + cycle_r),\n")
            file.write("xyz(1,0,0): multi*2*h*h*polyg_inner_r,\n")
            file.write("xyz(0,0,1): multi*2*h*polyg_inner_r*(polyg_inner_r - cycle_r),\n")
            file.write("xyz(0,0,0): multi*(-pow(polyg_inner_r*h, 2))\n")
            file.write("sturm\n")
            file.write("}\n\n")
            file.write("#local mockup1 =\n")
            file.write("difference{\n")
            file.write("    cylinder{\n")
            file.write("    <0,0,0.0>,<0,0,h>, max(polyg_outer_r, cycle_r)\n")
            file.write("    }\n\n")
            file.write("    #for(i, 0, n-1)\n")
            file.write("        object{\n")
            file.write("        poly_obj\n")
            file.write("        inverse\n")
            file.write("        rotate <0, 0, -90 + degrees(polyg_ext_ang*i)>\n")
            file.write("        }\n")
            file.write("        object{\n")
            file.write(
                "        Shape_Slice_Plane_2P_1V(<polyg_inner_r,0,0>,<cycle_r,0,h>,x)\n"
            )
            file.write("        rotate <0, 0, -90 + degrees(polyg_ext_ang*i)>\n")
            file.write("        }\n")
            file.write("    #end\n")
            file.write("}\n\n")
            file.write("object{\n")
            file.write("mockup1\n")
            file.write("rotate <0, 0, degrees(face_ang)>\n")
            file.write("}\n")
            file.write("#end\n")
            # Use the macro
            ngon = ob.pov.polytocircle_ngon
            ngonR = ob.pov.polytocircle_ngonR
            circleR = ob.pov.polytocircle_circleR
            tab_write(
                file,
                "#declare %s = object { Shape_Polygon_To_Circle_Blending("
                "%s, z, %.4f, %.4f, 2) rotate x*180 translate z*1\n"
                % (povdataname, ngon, ngonR, circleR),
            )
            tab_write(file, "}\n")
            continue  # Don't render proxy mesh, skip to next object
    if csg:
        # fluid_found early return no longer runs this
        # todo maybe make a function to run in that other branch
        duplidata_ref = []
        _dupnames_seen = {}  # avoid duplicate output during introspection
        for ob in sel:
            # matrix = global_matrix @ obj.matrix_world
            if ob.is_instancer:
                tab_write(file, "\n//--DupliObjects in %s--\n\n" % ob.name)
                # obj.dupli_list_create(scene) #deprecated in 2.8
                dup = ""
                if ob.is_modified(scene, "RENDER"):
                    # modified object always unique so using object name rather than data name
                    dup = "#declare OB%s = union{\n" % (
                        string_strip_hyphen(bpy.path.clean_name(ob.name))
                    )
                else:
                    dup = "#declare DATA%s = union{\n" % (
                        string_strip_hyphen(bpy.path.clean_name(ob.name))
                    )

                for eachduplicate in depsgraph.object_instances:
                    if (
                        eachduplicate.is_instance
                    ):  # Real dupli instance filtered because original included in list since 2.8
                        _dupname = eachduplicate.object.name
                        _dupobj = bpy.data.objects[_dupname]
                        # BEGIN introspection for troubleshooting purposes
                        if "name" not in dir(_dupobj.data):
                            if _dupname not in _dupnames_seen:
                                print(
                                    "WARNING: bpy.data.objects[%s].data (of type %s) has no 'name' attribute"
                                    % (_dupname, type(_dupobj.data))
                                )
                                for _thing in dir(_dupobj):
                                    print(
                                        "||  %s.%s = %s"
                                        % (_dupname, _thing, getattr(_dupobj, _thing))
                                    )
                                _dupnames_seen[_dupname] = 1
                                print("''=>  Unparseable objects so far: %s" % _dupnames_seen)
                            else:
                                _dupnames_seen[_dupname] += 1
                            continue  # don't try to parse data objects with no name attribute
                        # END introspection for troubleshooting purposes
                        duplidataname = "OB" + string_strip_hyphen(
                            bpy.path.clean_name(_dupobj.data.name)
                        )
                        dupmatrix = (
                            eachduplicate.matrix_world.copy()
                        )  # has to be copied to not store instance since 2.8
                        dup += "\tobject {\n\t\tDATA%s\n\t\t%s\t}\n" % (
                            string_strip_hyphen(bpy.path.clean_name(_dupobj.data.name)),
                            matrix_as_pov_string(ob.matrix_world.inverted() @ dupmatrix),
                        )
                        # add object to a list so that it is not rendered for some instance_types
                        if (
                            ob.instance_type != "COLLECTION"
                            and duplidataname not in duplidata_ref
                        ):
                            duplidata_ref.append(
                                duplidataname,
                            )  # older key [string_strip_hyphen(bpy.path.clean_name("OB"+obj.name))]
                dup += "}\n"
                # obj.dupli_list_clear()# just do not store any reference to instance since 2.8
                tab_write(file, dup)
            else:
                continue
        if _dupnames_seen:
            print("WARNING: Unparseable objects in current .blend file:\n''--> %s" % _dupnames_seen)
        if duplidata_ref:
            print("duplidata_ref = %s" % duplidata_ref)
        for data_name, inst in data_ref.items():
            for ob_name, matrix_str in inst:
                if ob_name not in duplidata_ref:  # .items() for a dictionary
                    tab_write(file, "\n//----Blender Object Name: %s----\n" %
                              ob_name.removeprefix("OB"))
                    if ob.pov.object_as == "":
                        tab_write(file, "object { \n")
                        tab_write(file, "%s\n" % data_name)
                        tab_write(file, "%s\n" % matrix_str)
                        tab_write(file, "}\n")
                    else:
                        no_boolean = True
                        for mod in ob.modifiers:
                            if mod.type == "BOOLEAN":
                                operation = None
                                no_boolean = False
                                if mod.operation == "INTERSECT":
                                    operation = "intersection"
                                else:
                                    operation = mod.operation.lower()
                                mod_ob_name = string_strip_hyphen(
                                    bpy.path.clean_name(mod.object.name)
                                )
                                mod_matrix = global_matrix @ mod.object.matrix_world
                                mod_ob_matrix = matrix_as_pov_string(mod_matrix)
                                tab_write(file, "%s { \n" % operation)
                                tab_write(file, "object { \n")
                                tab_write(file, "%s\n" % data_name)
                                tab_write(file, "%s\n" % matrix_str)
                                tab_write(file, "}\n")
                                tab_write(file, "object { \n")
                                tab_write(file, "%s\n" % ("DATA" + mod_ob_name))
                                tab_write(file, "%s\n" % mod_ob_matrix)
                                tab_write(file, "}\n")
                                tab_write(file, "}\n")
                                break
                        if no_boolean:
                            tab_write(file, "object { \n")
                            tab_write(file, "%s\n" % data_name)
                            tab_write(file, "%s\n" % matrix_str)
                            tab_write(file, "}\n")
