# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import os

import bpy
from mathutils import Matrix, Vector, Color
from bpy_extras import io_utils, node_shader_utils

from bpy_extras.wm_utils.progress_report import (
    ProgressReport,
    ProgressReportSubstep,
)


def name_compat(name):
    if name is None:
        return 'None'
    else:
        return name.replace(' ', '_')


def mesh_triangulate(me):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()


def write_mtl(scene, filepath, path_mode, copy_set, mtl_dict):
    source_dir = os.path.dirname(bpy.data.filepath)
    dest_dir = os.path.dirname(filepath)

    with open(filepath, "w", encoding="utf8", newline="\n") as f:
        fw = f.write

        fw('# Blender MTL File: %r\n' % (os.path.basename(bpy.data.filepath) or "None"))
        fw('# Material Count: %i\n' % len(mtl_dict))

        mtl_dict_values = list(mtl_dict.values())
        mtl_dict_values.sort(key=lambda m: m[0])

        # Write material/image combinations we have used.
        # Using mtl_dict.values() directly gives un-predictable order.
        for mtl_mat_name, mat in mtl_dict_values:
            # Get the Blender data for the material and the image.
            # Having an image named None will make a bug, dont do it :)

            fw('\nnewmtl %s\n' % mtl_mat_name)  # Define a new material: matname_imgname

            mat_wrap = node_shader_utils.PrincipledBSDFWrapper(mat) if mat else None

            if mat_wrap:
                use_mirror = mat_wrap.metallic != 0.0
                use_transparency = mat_wrap.alpha != 1.0

                # XXX Totally empirical conversion, trying to adapt it
                #     (from 1.0 - 0.0 Principled BSDF range to 0.0 - 900.0 OBJ specular exponent range)...
                spec = (1.0 - mat_wrap.roughness) * 30
                spec *= spec
                fw('Ns %.6f\n' % spec)

                # Ambient
                if use_mirror:
                    fw('Ka %.6f %.6f %.6f\n' % (mat_wrap.metallic, mat_wrap.metallic, mat_wrap.metallic))
                else:
                    fw('Ka %.6f %.6f %.6f\n' % (1.0, 1.0, 1.0))
                fw('Kd %.6f %.6f %.6f\n' % mat_wrap.base_color[:3])  # Diffuse
                # XXX TODO Find a way to handle tint and diffuse color, in a consistent way with import...
                fw('Ks %.6f %.6f %.6f\n' % (mat_wrap.specular, mat_wrap.specular, mat_wrap.specular))  # Specular
                # Emission, not in original MTL standard but seems pretty common, see T45766.
                fw('Ke %.6f %.6f %.6f\n' % mat_wrap.emission_color[:3])
                fw('Ni %.6f\n' % mat_wrap.ior)  # Refraction index
                fw('d %.6f\n' % mat_wrap.alpha)  # Alpha (obj uses 'd' for dissolve)

                # See http://en.wikipedia.org/wiki/Wavefront_.obj_file for whole list of values...
                # Note that mapping is rather fuzzy sometimes, trying to do our best here.
                if mat_wrap.specular == 0:
                    fw('illum 1\n')  # no specular.
                elif use_mirror:
                    if use_transparency:
                        fw('illum 6\n')  # Reflection, Transparency, Ray trace
                    else:
                        fw('illum 3\n')  # Reflection and Ray trace
                elif use_transparency:
                    fw('illum 9\n')  # 'Glass' transparency and no Ray trace reflection... fuzzy matching, but...
                else:
                    fw('illum 2\n')  # light normally

                #### And now, the image textures...
                image_map = {
                        "map_Kd": "base_color_texture",
                        "map_Ka": None,  # ambient...
                        "map_Ks": "specular_texture",
                        "map_Ns": "roughness_texture",
                        "map_d": "alpha_texture",
                        "map_Tr": None,  # transmission roughness?
                        "map_Bump": "normalmap_texture",
                        "disp": None,  # displacement...
                        "refl": "metallic_texture",
                        "map_Ke": "emission_color_texture",
                        }

                for key, mat_wrap_key in sorted(image_map.items()):
                    if mat_wrap_key is None:
                        continue
                    tex_wrap = getattr(mat_wrap, mat_wrap_key, None)
                    if tex_wrap is None:
                        continue
                    image = tex_wrap.image
                    if image is None:
                        continue

                    filepath = io_utils.path_reference(image.filepath, source_dir, dest_dir,
                                                       path_mode, "", copy_set, image.library)
                    options = []
                    if key == "map_Bump":
                        if mat_wrap.normalmap_strength != 1.0:
                            options.append('-bm %.6f' % mat_wrap.normalmap_strength)
                    if tex_wrap.translation != Vector((0.0, 0.0, 0.0)):
                        options.append('-o %.6f %.6f %.6f' % tex_wrap.translation[:])
                    if tex_wrap.scale != Vector((1.0, 1.0, 1.0)):
                        options.append('-s %.6f %.6f %.6f' % tex_wrap.scale[:])
                    if options:
                        fw('%s %s %s\n' % (key, " ".join(options), repr(filepath)[1:-1]))
                    else:
                        fw('%s %s\n' % (key, repr(filepath)[1:-1]))

            else:
                # Write a dummy material here?
                fw('Ns 500\n')
                fw('Ka 0.8 0.8 0.8\n')
                fw('Kd 0.8 0.8 0.8\n')
                fw('Ks 0.8 0.8 0.8\n')
                fw('d 1\n')  # No alpha
                fw('illum 2\n')  # light normally


def test_nurbs_compat(ob):
    if ob.type != 'CURVE':
        return False

    for nu in ob.data.splines:
        if nu.point_count_v == 1 and nu.type != 'BEZIER':  # not a surface and not bezier
            return True

    return False


def write_nurb(fw, ob, ob_mat):
    tot_verts = 0
    cu = ob.data

    # use negative indices
    for nu in cu.splines:
        if nu.type == 'POLY':
            DEG_ORDER_U = 1
        else:
            DEG_ORDER_U = nu.order_u - 1  # odd but tested to be correct

        if nu.type == 'BEZIER':
            print("\tWarning, bezier curve:", ob.name, "only poly and nurbs curves supported")
            continue

        if nu.point_count_v > 1:
            print("\tWarning, surface:", ob.name, "only poly and nurbs curves supported")
            continue

        if len(nu.points) <= DEG_ORDER_U:
            print("\tWarning, order_u is lower then vert count, skipping:", ob.name)
            continue

        pt_num = 0
        do_closed = nu.use_cyclic_u
        do_endpoints = (do_closed == 0) and nu.use_endpoint_u

        for pt in nu.points:
            fw('v %.6f %.6f %.6f\n' % (ob_mat @ pt.co.to_3d())[:])
            pt_num += 1
        tot_verts += pt_num

        fw('g %s\n' % (name_compat(ob.name)))  # name_compat(ob.getData(1)) could use the data name too
        fw('cstype bspline\n')  # not ideal, hard coded
        fw('deg %d\n' % DEG_ORDER_U)  # not used for curves but most files have it still

        curve_ls = [-(i + 1) for i in range(pt_num)]

        # 'curv' keyword
        if do_closed:
            if DEG_ORDER_U == 1:
                pt_num += 1
                curve_ls.append(-1)
            else:
                pt_num += DEG_ORDER_U
                curve_ls = curve_ls + curve_ls[0:DEG_ORDER_U]

        fw('curv 0.0 1.0 %s\n' % (" ".join([str(i) for i in curve_ls])))  # Blender has no U and V values for the curve

        # 'parm' keyword
        tot_parm = (DEG_ORDER_U + 1) + pt_num
        tot_parm_div = float(tot_parm - 1)
        parm_ls = [(i / tot_parm_div) for i in range(tot_parm)]

        if do_endpoints:  # end points, force param
            for i in range(DEG_ORDER_U + 1):
                parm_ls[i] = 0.0
                parm_ls[-(1 + i)] = 1.0

        fw("parm u %s\n" % " ".join(["%.6f" % i for i in parm_ls]))

        fw('end\n')

    return tot_verts


def write_file(filepath, objects, depsgraph, scene,
               EXPORT_TRI=False,
               EXPORT_EDGES=False,
               EXPORT_SMOOTH_GROUPS=False,
               EXPORT_SMOOTH_GROUPS_BITFLAGS=False,
               EXPORT_NORMALS=False,
               EXPORT_UV=True,
               EXPORT_MTL=True,
               EXPORT_APPLY_MODIFIERS=True,
               EXPORT_APPLY_MODIFIERS_RENDER=False,
               EXPORT_BLEN_OBS=True,
               EXPORT_GROUP_BY_OB=False,
               EXPORT_GROUP_BY_MAT=False,
               EXPORT_KEEP_VERT_ORDER=False,
               EXPORT_POLYGROUPS=False,
               EXPORT_CURVE_AS_NURBS=True,
               EXPORT_GLOBAL_MATRIX=None,
               EXPORT_PATH_MODE='AUTO',
               progress=ProgressReport(),
               ):
    """
    Basic write function. The context and options must be already set
    This can be accessed externaly
    eg.
    write( 'c:\\test\\foobar.obj', Blender.Object.GetSelected() ) # Using default options.
    """
    if EXPORT_GLOBAL_MATRIX is None:
        EXPORT_GLOBAL_MATRIX = Matrix()

    def veckey3d(v):
        return round(v.x, 4), round(v.y, 4), round(v.z, 4)

    def veckey2d(v):
        return round(v[0], 4), round(v[1], 4)

    def findVertexGroupName(face, vWeightMap):
        """
        Searches the vertexDict to see what groups is assigned to a given face.
        We use a frequency system in order to sort out the name because a given vertex can
        belong to two or more groups at the same time. To find the right name for the face
        we list all the possible vertex group names with their frequency and then sort by
        frequency in descend order. The top element is the one shared by the highest number
        of vertices is the face's group
        """
        weightDict = {}
        for vert_index in face.vertices:
            vWeights = vWeightMap[vert_index]
            for vGroupName, weight in vWeights:
                weightDict[vGroupName] = weightDict.get(vGroupName, 0.0) + weight

        if weightDict:
            return max((weight, vGroupName) for vGroupName, weight in weightDict.items())[1]
        else:
            return '(null)'

    with ProgressReportSubstep(progress, 2, "OBJ Export path: %r" % filepath, "OBJ Export Finished") as subprogress1:
        with open(filepath, "w", encoding="utf8", newline="\n") as f:
            fw = f.write

            # Write Header
            fw('# Blender v%s OBJ File: %r\n' % (bpy.app.version_string, os.path.basename(bpy.data.filepath)))
            fw('# www.blender.org\n')

            # Tell the obj file what material file to use.
            if EXPORT_MTL:
                mtlfilepath = os.path.splitext(filepath)[0] + ".mtl"
                # filepath can contain non utf8 chars, use repr
                fw('mtllib %s\n' % repr(os.path.basename(mtlfilepath))[1:-1])

            # Initialize totals, these are updated each object
            totverts = totuvco = totno = 1

            face_vert_index = 1

            # A Dict of Materials
            # (material.name, image.name):matname_imagename # matname_imagename has gaps removed.
            mtl_dict = {}
            # Used to reduce the usage of matname_texname materials, which can become annoying in case of
            # repeated exports/imports, yet keeping unique mat names per keys!
            # mtl_name: (material.name, image.name)
            mtl_rev_dict = {}

            copy_set = set()

            # Get all meshes
            subprogress1.enter_substeps(len(objects))
            for i, ob_main in enumerate(objects):
                # ignore dupli children
                if ob_main.parent and ob_main.parent.instance_type in {'VERTS', 'FACES'}:
                    subprogress1.step("Ignoring %s, dupli child..." % ob_main.name)
                    continue

                obs = [(ob_main, ob_main.matrix_world)]
                if ob_main.is_instancer:
                    obs += [(dup.instance_object.original, dup.matrix_world.copy())
                            for dup in depsgraph.object_instances
                            if dup.parent and dup.parent.original == ob_main]
                    # ~ print(ob_main.name, 'has', len(obs) - 1, 'dupli children')

                subprogress1.enter_substeps(len(obs))
                for ob, ob_mat in obs:
                    with ProgressReportSubstep(subprogress1, 6) as subprogress2:
                        uv_unique_count = no_unique_count = 0

                        # Nurbs curve support
                        if EXPORT_CURVE_AS_NURBS and test_nurbs_compat(ob):
                            ob_mat = EXPORT_GLOBAL_MATRIX @ ob_mat
                            totverts += write_nurb(fw, ob, ob_mat)
                            continue
                        # END NURBS

                        ob_for_convert = ob.evaluated_get(depsgraph) if EXPORT_APPLY_MODIFIERS else ob.original

                        try:
                            me = ob_for_convert.to_mesh()
                        except RuntimeError:
                            me = None

                        if me is None:
                            continue

                        # _must_ do this before applying transformation, else tessellation may differ
                        if EXPORT_TRI:
                            # _must_ do this first since it re-allocs arrays
                            mesh_triangulate(me)

                        me.transform(EXPORT_GLOBAL_MATRIX @ ob_mat)
                        # If negative scaling, we have to invert the normals...
                        if ob_mat.determinant() < 0.0:
                            me.flip_normals()

                        if EXPORT_UV:
                            faceuv = len(me.uv_layers) > 0
                            if faceuv:
                                uv_layer = me.uv_layers.active.data[:]
                        else:
                            faceuv = False

                        me_verts = me.vertices[:]

                        # Make our own list so it can be sorted to reduce context switching
                        face_index_pairs = [(face, index) for index, face in enumerate(me.polygons)]

                        if EXPORT_EDGES:
                            edges = me.edges
                        else:
                            edges = []

                        if not (len(face_index_pairs) + len(edges) + len(me.vertices)):  # Make sure there is something to write
                            # clean up
                            ob_for_convert.to_mesh_clear()
                            continue  # dont bother with this mesh.

                        if EXPORT_NORMALS and face_index_pairs:
                            me.calc_normals_split()
                            # No need to call me.free_normals_split later, as this mesh is deleted anyway!

                        loops = me.loops

                        if (EXPORT_SMOOTH_GROUPS or EXPORT_SMOOTH_GROUPS_BITFLAGS) and face_index_pairs:
                            smooth_groups, smooth_groups_tot = me.calc_smooth_groups(use_bitflags=EXPORT_SMOOTH_GROUPS_BITFLAGS)
                            if smooth_groups_tot <= 1:
                                smooth_groups, smooth_groups_tot = (), 0
                        else:
                            smooth_groups, smooth_groups_tot = (), 0

                        materials = me.materials[:]
                        material_names = [m.name if m else None for m in materials]

                        # avoid bad index errors
                        if not materials:
                            materials = [None]
                            material_names = [name_compat(None)]

                        # Sort by Material, then images
                        # so we dont over context switch in the obj file.
                        if EXPORT_KEEP_VERT_ORDER:
                            pass
                        else:
                            if len(materials) > 1:
                                if smooth_groups:
                                    sort_func = lambda a: (a[0].material_index,
                                                           smooth_groups[a[1]] if a[0].use_smooth else False)
                                else:
                                    sort_func = lambda a: (a[0].material_index,
                                                           a[0].use_smooth)
                            else:
                                # no materials
                                if smooth_groups:
                                    sort_func = lambda a: smooth_groups[a[1] if a[0].use_smooth else False]
                                else:
                                    sort_func = lambda a: a[0].use_smooth

                            face_index_pairs.sort(key=sort_func)

                            del sort_func

                        # Set the default mat to no material and no image.
                        contextMat = 0, 0  # Can never be this, so we will label a new material the first chance we get.
                        contextSmooth = None  # Will either be true or false,  set bad to force initialization switch.

                        if EXPORT_BLEN_OBS or EXPORT_GROUP_BY_OB:
                            name1 = ob.name
                            name2 = ob.data.name
                            if name1 == name2:
                                obnamestring = name_compat(name1)
                            else:
                                obnamestring = '%s_%s' % (name_compat(name1), name_compat(name2))

                            if EXPORT_BLEN_OBS:
                                fw('o %s\n' % obnamestring)  # Write Object name
                            else:  # if EXPORT_GROUP_BY_OB:
                                fw('g %s\n' % obnamestring)

                        subprogress2.step()

                        # Vert
                        for v in me_verts:
                            fw('v %.6f %.6f %.6f\n' % v.co[:])

                        subprogress2.step()

                        # UV
                        if faceuv:
                            # in case removing some of these dont get defined.
                            uv = f_index = uv_index = uv_key = uv_val = uv_ls = None

                            uv_face_mapping = [None] * len(face_index_pairs)

                            uv_dict = {}
                            uv_get = uv_dict.get
                            for f, f_index in face_index_pairs:
                                uv_ls = uv_face_mapping[f_index] = []
                                for uv_index, l_index in enumerate(f.loop_indices):
                                    uv = uv_layer[l_index].uv
                                    # include the vertex index in the key so we don't share UV's between vertices,
                                    # allowed by the OBJ spec but can cause issues for other importers, see: T47010.

                                    # this works too, shared UV's for all verts
                                    #~ uv_key = veckey2d(uv)
                                    uv_key = loops[l_index].vertex_index, veckey2d(uv)

                                    uv_val = uv_get(uv_key)
                                    if uv_val is None:
                                        uv_val = uv_dict[uv_key] = uv_unique_count
                                        fw('vt %.6f %.6f\n' % uv[:])
                                        uv_unique_count += 1
                                    uv_ls.append(uv_val)

                            del uv_dict, uv, f_index, uv_index, uv_ls, uv_get, uv_key, uv_val
                            # Only need uv_unique_count and uv_face_mapping

                        subprogress2.step()

                        # NORMAL, Smooth/Non smoothed.
                        if EXPORT_NORMALS:
                            no_key = no_val = None
                            normals_to_idx = {}
                            no_get = normals_to_idx.get
                            loops_to_normals = [0] * len(loops)
                            for f, f_index in face_index_pairs:
                                for l_idx in f.loop_indices:
                                    no_key = veckey3d(loops[l_idx].normal)
                                    no_val = no_get(no_key)
                                    if no_val is None:
                                        no_val = normals_to_idx[no_key] = no_unique_count
                                        fw('vn %.4f %.4f %.4f\n' % no_key)
                                        no_unique_count += 1
                                    loops_to_normals[l_idx] = no_val
                            del normals_to_idx, no_get, no_key, no_val
                        else:
                            loops_to_normals = []

                        subprogress2.step()

                        # XXX
                        if EXPORT_POLYGROUPS:
                            # Retrieve the list of vertex groups
                            vertGroupNames = ob.vertex_groups.keys()
                            if vertGroupNames:
                                currentVGroup = ''
                                # Create a dictionary keyed by face id and listing, for each vertex, the vertex groups it belongs to
                                vgroupsMap = [[] for _i in range(len(me_verts))]
                                for v_idx, v_ls in enumerate(vgroupsMap):
                                    v_ls[:] = [(vertGroupNames[g.group], g.weight) for g in me_verts[v_idx].groups]

                        for f, f_index in face_index_pairs:
                            f_smooth = f.use_smooth
                            if f_smooth and smooth_groups:
                                f_smooth = smooth_groups[f_index]
                            f_mat = min(f.material_index, len(materials) - 1)

                            # MAKE KEY
                            key = material_names[f_mat], None  # No image, use None instead.

                            # Write the vertex group
                            if EXPORT_POLYGROUPS:
                                if vertGroupNames:
                                    # find what vertext group the face belongs to
                                    vgroup_of_face = findVertexGroupName(f, vgroupsMap)
                                    if vgroup_of_face != currentVGroup:
                                        currentVGroup = vgroup_of_face
                                        fw('g %s\n' % vgroup_of_face)

                            # CHECK FOR CONTEXT SWITCH
                            if key == contextMat:
                                pass  # Context already switched, dont do anything
                            else:
                                if key[0] is None and key[1] is None:
                                    # Write a null material, since we know the context has changed.
                                    if EXPORT_GROUP_BY_MAT:
                                        # can be mat_image or (null)
                                        fw("g %s_%s\n" % (name_compat(ob.name), name_compat(ob.data.name)))
                                    if EXPORT_MTL:
                                        fw("usemtl (null)\n")  # mat, image

                                else:
                                    mat_data = mtl_dict.get(key)
                                    if not mat_data:
                                        # First add to global dict so we can export to mtl
                                        # Then write mtl

                                        # Make a new names from the mat and image name,
                                        # converting any spaces to underscores with name_compat.

                                        # If none image dont bother adding it to the name
                                        # Try to avoid as much as possible adding texname (or other things)
                                        # to the mtl name (see [#32102])...
                                        mtl_name = "%s" % name_compat(key[0])
                                        if mtl_rev_dict.get(mtl_name, None) not in {key, None}:
                                            if key[1] is None:
                                                tmp_ext = "_NONE"
                                            else:
                                                tmp_ext = "_%s" % name_compat(key[1])
                                            i = 0
                                            while mtl_rev_dict.get(mtl_name + tmp_ext, None) not in {key, None}:
                                                i += 1
                                                tmp_ext = "_%3d" % i
                                            mtl_name += tmp_ext
                                        mat_data = mtl_dict[key] = mtl_name, materials[f_mat]
                                        mtl_rev_dict[mtl_name] = key

                                    if EXPORT_GROUP_BY_MAT:
                                        # can be mat_image or (null)
                                        fw("g %s_%s_%s\n" % (name_compat(ob.name), name_compat(ob.data.name), mat_data[0]))
                                    if EXPORT_MTL:
                                        fw("usemtl %s\n" % mat_data[0])  # can be mat_image or (null)

                            contextMat = key
                            if f_smooth != contextSmooth:
                                if f_smooth:  # on now off
                                    if smooth_groups:
                                        f_smooth = smooth_groups[f_index]
                                        fw('s %d\n' % f_smooth)
                                    else:
                                        fw('s 1\n')
                                else:  # was off now on
                                    fw('s off\n')
                                contextSmooth = f_smooth

                            f_v = [(vi, me_verts[v_idx], l_idx)
                                   for vi, (v_idx, l_idx) in enumerate(zip(f.vertices, f.loop_indices))]

                            fw('f')
                            if faceuv:
                                if EXPORT_NORMALS:
                                    for vi, v, li in f_v:
                                        fw(" %d/%d/%d" % (totverts + v.index,
                                                          totuvco + uv_face_mapping[f_index][vi],
                                                          totno + loops_to_normals[li],
                                                          ))  # vert, uv, normal
                                else:  # No Normals
                                    for vi, v, li in f_v:
                                        fw(" %d/%d" % (totverts + v.index,
                                                       totuvco + uv_face_mapping[f_index][vi],
                                                       ))  # vert, uv

                                face_vert_index += len(f_v)

                            else:  # No UV's
                                if EXPORT_NORMALS:
                                    for vi, v, li in f_v:
                                        fw(" %d//%d" % (totverts + v.index, totno + loops_to_normals[li]))
                                else:  # No Normals
                                    for vi, v, li in f_v:
                                        fw(" %d" % (totverts + v.index))

                            fw('\n')

                        subprogress2.step()

                        # Write edges.
                        if EXPORT_EDGES:
                            for ed in edges:
                                if ed.is_loose:
                                    fw('l %d %d\n' % (totverts + ed.vertices[0], totverts + ed.vertices[1]))

                        # Make the indices global rather then per mesh
                        totverts += len(me_verts)
                        totuvco += uv_unique_count
                        totno += no_unique_count

                        # clean up
                        ob_for_convert.to_mesh_clear()

                subprogress1.leave_substeps("Finished writing geometry of '%s'." % ob_main.name)
            subprogress1.leave_substeps()

        subprogress1.step("Finished exporting geometry, now exporting materials")

        # Now we have all our materials, save them
        if EXPORT_MTL:
            write_mtl(scene, mtlfilepath, EXPORT_PATH_MODE, copy_set, mtl_dict)

        # copy all collected files.
        io_utils.path_reference_copy(copy_set)


def _write(context, filepath,
           EXPORT_TRI,  # ok
           EXPORT_EDGES,
           EXPORT_SMOOTH_GROUPS,
           EXPORT_SMOOTH_GROUPS_BITFLAGS,
           EXPORT_NORMALS,  # ok
           EXPORT_UV,  # ok
           EXPORT_MTL,
           EXPORT_APPLY_MODIFIERS,  # ok
           EXPORT_APPLY_MODIFIERS_RENDER,  # ok
           EXPORT_BLEN_OBS,
           EXPORT_GROUP_BY_OB,
           EXPORT_GROUP_BY_MAT,
           EXPORT_KEEP_VERT_ORDER,
           EXPORT_POLYGROUPS,
           EXPORT_CURVE_AS_NURBS,
           EXPORT_SEL_ONLY,  # ok
           EXPORT_ANIMATION,
           EXPORT_GLOBAL_MATRIX,
           EXPORT_PATH_MODE,  # Not used
           ):

    with ProgressReport(context.window_manager) as progress:
        base_name, ext = os.path.splitext(filepath)
        context_name = [base_name, '', '', ext]  # Base name, scene name, frame number, extension

        depsgraph = context.evaluated_depsgraph_get()
        scene = context.scene

        # Exit edit mode before exporting, so current object states are exported properly.
        if bpy.ops.object.mode_set.poll():
            bpy.ops.object.mode_set(mode='OBJECT')

        orig_frame = scene.frame_current

        # Export an animation?
        if EXPORT_ANIMATION:
            scene_frames = range(scene.frame_start, scene.frame_end + 1)  # Up to and including the end frame.
        else:
            scene_frames = [orig_frame]  # Dont export an animation.

        # Loop through all frames in the scene and export.
        progress.enter_substeps(len(scene_frames))
        for frame in scene_frames:
            if EXPORT_ANIMATION:  # Add frame to the filepath.
                context_name[2] = '_%.6d' % frame

            scene.frame_set(frame, subframe=0.0)
            if EXPORT_SEL_ONLY:
                objects = context.selected_objects
            else:
                objects = scene.objects

            full_path = ''.join(context_name)

            # erm... bit of a problem here, this can overwrite files when exporting frames. not too bad.
            # EXPORT THE FILE.
            progress.enter_substeps(1)
            write_file(full_path, objects, depsgraph, scene,
                       EXPORT_TRI,
                       EXPORT_EDGES,
                       EXPORT_SMOOTH_GROUPS,
                       EXPORT_SMOOTH_GROUPS_BITFLAGS,
                       EXPORT_NORMALS,
                       EXPORT_UV,
                       EXPORT_MTL,
                       EXPORT_APPLY_MODIFIERS,
                       EXPORT_APPLY_MODIFIERS_RENDER,
                       EXPORT_BLEN_OBS,
                       EXPORT_GROUP_BY_OB,
                       EXPORT_GROUP_BY_MAT,
                       EXPORT_KEEP_VERT_ORDER,
                       EXPORT_POLYGROUPS,
                       EXPORT_CURVE_AS_NURBS,
                       EXPORT_GLOBAL_MATRIX,
                       EXPORT_PATH_MODE,
                       progress,
                       )
            progress.leave_substeps()

        scene.frame_set(orig_frame, subframe=0.0)
        progress.leave_substeps()


"""
Currently the exporter lacks these features:
* multiple scene export (only active scene is written)
* particles
"""


def save(context,
         filepath,
         *,
         use_triangles=False,
         use_edges=True,
         use_normals=False,
         use_smooth_groups=False,
         use_smooth_groups_bitflags=False,
         use_uvs=True,
         use_materials=True,
         use_mesh_modifiers=True,
         use_mesh_modifiers_render=False,
         use_blen_objects=True,
         group_by_object=False,
         group_by_material=False,
         keep_vertex_order=False,
         use_vertex_groups=False,
         use_nurbs=True,
         use_selection=True,
         use_animation=False,
         global_matrix=None,
         path_mode='AUTO'
         ):

    _write(context, filepath,
           EXPORT_TRI=use_triangles,
           EXPORT_EDGES=use_edges,
           EXPORT_SMOOTH_GROUPS=use_smooth_groups,
           EXPORT_SMOOTH_GROUPS_BITFLAGS=use_smooth_groups_bitflags,
           EXPORT_NORMALS=use_normals,
           EXPORT_UV=use_uvs,
           EXPORT_MTL=use_materials,
           EXPORT_APPLY_MODIFIERS=use_mesh_modifiers,
           EXPORT_APPLY_MODIFIERS_RENDER=use_mesh_modifiers_render,
           EXPORT_BLEN_OBS=use_blen_objects,
           EXPORT_GROUP_BY_OB=group_by_object,
           EXPORT_GROUP_BY_MAT=group_by_material,
           EXPORT_KEEP_VERT_ORDER=keep_vertex_order,
           EXPORT_POLYGROUPS=use_vertex_groups,
           EXPORT_CURVE_AS_NURBS=use_nurbs,
           EXPORT_SEL_ONLY=use_selection,
           EXPORT_ANIMATION=use_animation,
           EXPORT_GLOBAL_MATRIX=global_matrix,
           EXPORT_PATH_MODE=path_mode,
           )

    return {'FINISHED'}
