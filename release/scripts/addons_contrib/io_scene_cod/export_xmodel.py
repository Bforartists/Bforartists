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

"""
Blender-CoD: Blender Add-On for Call of Duty modding
Version: alpha 3

Copyright (c) 2011 CoDEmanX, Flybynyt -- blender-cod@online.de

http://code.google.com/p/blender-cod/

"""

import bpy
import os
from datetime import datetime

def save(self, context, filepath="",
         use_version='6',
         use_selection=False,
         use_apply_modifiers=True,
         use_armature=True,
         use_vertex_colors=True,
         use_vertex_colors_alpha=False,
         use_vertex_cleanup=False,
         use_armature_pose=False,
         use_frame_start=1,
         use_frame_end=250,
         use_weight_min=False,
         use_weight_min_threshold=0.010097):

    # There's no context object right after object deletion, need to set one
    if context.object:
        last_mode = context.object.mode
    else:
        last_mode = 'OBJECT'

        for ob in bpy.data.objects:
            if ob.type == 'MESH':
                context.scene.objects.active = ob
                break
        else:
            return "No mesh to export."

    # HACK: Force an update, so that bone tree is properly sorted for hierarchy table export
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)

    # Remember frame to set it back after export
    last_frame_current = context.scene.frame_current

    # Disable Armature for Pose animation export, bone.tail_local not available for PoseBones
    if use_armature and use_armature_pose:
        use_armature = False

    # Don't iterate for a single frame
    if not use_armature_pose or (use_armature_pose and use_frame_start == use_frame_end):
        context.scene.frame_set(use_frame_start)

        result = _write(self, context, filepath,
                        use_version,
                        use_selection,
                        use_apply_modifiers,
                        use_armature,
                        use_vertex_colors,
                        use_vertex_colors_alpha,
                        use_vertex_cleanup,
                        use_armature_pose,
                        use_weight_min,
                        use_weight_min_threshold)
    else:

        if use_frame_start < use_frame_end:
            frame_order = 1
            frame_min = use_frame_start
            frame_max = use_frame_end
        else:
            frame_order = -1
            frame_min = use_frame_end
            frame_max = use_frame_start

        # String length of highest frame number for filename padding
        frame_strlen = len(str(frame_max))

        filepath_split = os.path.splitext(filepath)

        for i_frame, frame in enumerate(range(use_frame_start,
                                              use_frame_end + frame_order,
                                              frame_order
                                              ),
                                        frame_min):

            # Set frame for export
            # Don't do it directly to frame_current, as to_mesh() won't use updated frame!
            context.scene.frame_set(frame)

            # Generate filename including padded frame number
            filepath_frame = "%s_%.*i%s" % (filepath_split[0], frame_strlen, i_frame, filepath_split[1])

            result = _write(self, context, filepath_frame,
                            use_version,
                            use_selection,
                            use_apply_modifiers,
                            use_armature,
                            use_vertex_colors,
                            use_vertex_colors_alpha,
                            use_vertex_cleanup,
                            use_armature_pose,
                            use_weight_min,
                            use_weight_min_threshold
                            )

            # Quit iteration on error
            if result:
                context.scene.frame_set(last_frame_current)
                return result

    # Set frame back
    context.scene.frame_set(last_frame_current)

    # Set mode back
    bpy.ops.object.mode_set(mode=last_mode, toggle=False)

    # Handle possible error result of single frame export
    return result

def _write(self, context, filepath,
           use_version,
           use_selection,
           use_apply_modifiers,
           use_armature,
           use_vertex_colors,
           use_vertex_colors_alpha,
           use_vertex_cleanup,
           use_armature_pose,
           use_weight_min,
           use_weight_min_threshold):

    num_verts = 0
    num_verts_unique = 0
    verts_unique = []
    num_faces = 0
    meshes = []
    meshes_matrix = []
    meshes_vgroup = []
    objects = []
    armature = None
    bone_mapping = {}
    materials = []

    ob_count = 0
    v_count = 0

    # Check input objects, count them and convert mesh objects
    for ob in bpy.data.objects:

        # Take the first armature
        if ob.type == 'ARMATURE' and use_armature and armature is None and len(ob.data.bones) > 0:
            armature = ob
            continue

        if ob.type != 'MESH':
            continue

        # Skip meshes, which are unselected
        if use_selection and not ob.select:
            continue

        # Set up modifiers whether to apply deformation or not
        mod_states = []
        for mod in ob.modifiers:
            mod_states.append(mod.show_viewport)
            if mod.type == 'ARMATURE':
                mod.show_viewport = mod.show_viewport and use_armature_pose
            else:
                mod.show_viewport = mod.show_viewport and use_apply_modifiers

        # to_mesh() applies enabled modifiers only
        mesh = ob.to_mesh(scene=context.scene, apply_modifiers=True, settings='PREVIEW')

        # Restore modifier settings
        for i, mod in enumerate(ob.modifiers):
            mod.show_viewport = mod_states[i]

        # Skip invalid meshes
        if len(mesh.vertices) < 3:
            _skip_notice(ob.name, mesh.name, "Less than 3 vertices")
            continue
        if len(mesh.tessfaces) < 1:
            _skip_notice(ob.name, mesh.name, "No faces")
            continue
        if len(ob.material_slots) < 1:
            _skip_notice(ob.name, mesh.name, "No material")
            continue
        if not mesh.tessface_uv_textures:
            _skip_notice(ob.name, mesh.name, "No UV texture, not unwrapped?")
            continue

        meshes.append(mesh)
        meshes_matrix.append(ob.matrix_world)

        if ob.vertex_groups:
            meshes_vgroup.append(ob.vertex_groups)
        else:
            meshes_vgroup.append(None)

        if use_vertex_cleanup:

            # Retrieve verts which belong to a face
            verts = []
            for f in mesh.tessfaces:
                for v in f.vertices:
                    verts.append(v)

            # Uniquify & sort
            keys = {}
            for e in verts:
                keys[e] = 1
            verts = list(keys.keys())

        else:
            verts = [v.index for v in mesh.vertices]

        # Store vert sets, aligned to mesh objects
        verts_unique.append(verts)

        # As len(mesh.vertices) doesn't take unused verts into account, already count here
        num_verts_unique += len(verts)

        # Take quads into account!
        for f in mesh.tessfaces:
            if len(f.vertices) == 3:
                num_faces += 1
            else:
                num_faces += 2

        objects.append(ob.name)

    if (num_verts or num_faces or len(objects)) == 0:
        return "Nothing to export.\n" \
               "Meshes must have at least:\n" \
               "    3 vertices\n" \
               "    1 face\n" \
               "    1 material\n" \
               "    UV mapping"

    # There's valid data for export, create output file
    try:
        file = open(filepath, "w")
    except IOError:
        return "Could not open file for writing:\n%s" % filepath

    # Write header
    file.write("// XMODEL_EXPORT file in CoD model v%i format created with Blender v%s\n" \
               % (int(use_version), bpy.app.version_string))

    file.write("// Source file: %s\n" % bpy.data.filepath)
    file.write("// Export time: %s\n\n" % datetime.now().strftime("%d-%b-%Y %H:%M:%S"))

    if use_armature_pose:
        file.write("// Posed model of frame %i\n\n" % bpy.context.scene.frame_current)

    if use_weight_min:
        file.write("// Minimum bone weight: %f\n\n" % use_weight_min_threshold)

    file.write("MODEL\n")
    file.write("VERSION %i\n" % int(use_version))

    # Write armature data
    if armature is None:

        # Default rig
        file.write("\nNUMBONES 1\n")
        file.write("BONE 0 -1 \"tag_origin\"\n")

        file.write("\nBONE 0\n")

        if use_version == '5':
            file.write("OFFSET 0.000000 0.000000 0.000000\n")
            file.write("SCALE 1.000000 1.000000 1.000000\n")
            file.write("X 1.000000 0.000000 0.000000\n")
            file.write("Y 0.000000 1.000000 0.000000\n")
            file.write("Z 0.000000 0.000000 1.000000\n")
        else:
            # Model format v6 has commas
            file.write("OFFSET 0.000000, 0.000000, 0.000000\n")
            file.write("SCALE 1.000000, 1.000000, 1.000000\n")
            file.write("X 1.000000, 0.000000, 0.000000\n")
            file.write("Y 0.000000, 1.000000, 0.000000\n")
            file.write("Z 0.000000, 0.000000, 1.000000\n")

    else:

        # Either use posed armature bones for animation to model sequence export
        if use_armature_pose:
            bones = armature.pose.bones
        # Or armature bones in rest pose for regular rigged models
        else:
            bones = armature.data.bones

        file.write("\nNUMBONES %i\n" % len(bones))

        # Get the armature object's orientation
        a_matrix = armature.matrix_world

        # Check for multiple roots, armature should have exactly one
        roots = 0
        for bone in bones:
            if not bone.parent:
                roots += 1
        if roots != 1:
            warning_string = "Warning: %i root bones found in armature object '%s'\n" \
                             % (roots, armature.name)
            print(warning_string)
            file.write("// %s" % warning_string)

        # Look up table for bone indices
        bone_table = [b.name for b in bones]

        # Write bone hierarchy table and create bone_mapping array for later use (vertex weights)
        for i, bone in enumerate(bones):

            if bone.parent:
                try:
                    bone_parent_index = bone_table.index(bone.parent.name)
                except (ValueError):
                    bone_parent_index = 0
                    file.write("// Warning: \"%s\" not found in bone table, binding to root...\n"
                               % bone.parent.name)
            else:
                bone_parent_index = -1

            file.write("BONE %i %i \"%s\"\n" % (i, bone_parent_index, bone.name))
            bone_mapping[bone.name] = i

        # Write bone orientations
        for i, bone in enumerate(bones):
            file.write("\nBONE %i\n" % i)

            # Using local tail for proper coordinates
            b_tail = a_matrix * bone.tail_local

            # TODO: Fix calculation/error: pose animation will use posebones, but they don't have tail_local!

            # TODO: Fix rotation matrix calculation, calculation seems to be wrong...
            #b_matrix = bone.matrix_local * a_matrix
            #b_matrix = bone.matrix * a_matrix * bones[0].matrix.inverted()
            #from mathutils import Matrix

            # Is this the way to go? Or will it fix the root only, but mess up all other roll angles?
            if i == 0:
                b_matrix = ((1,0,0),(0,1,0),(0,0,1))
            else:
                b_matrix = a_matrix * bone.matrix_local
                #from mathutils import Matrix
                #b_matrix = bone.matrix_local * a_matrix * Matrix(((1,-0,0),(0,0,-1),(-0,1,0)))
                
            if use_version == '5':
                file.write("OFFSET %.6f %.6f %.6f\n" % (b_tail[0], b_tail[1], b_tail[2]))
                file.write("SCALE 1.000000 1.000000 1.000000\n") # Is this even supported by CoD?
                file.write("X %.6f %.6f %.6f\n" % (b_matrix[0][0], b_matrix[1][0], b_matrix[2][0]))
                file.write("Y %.6f %.6f %.6f\n" % (b_matrix[0][1], b_matrix[1][1], b_matrix[2][1]))
                file.write("Z %.6f %.6f %.6f\n" % (b_matrix[0][2], b_matrix[1][2], b_matrix[2][2]))
            else:
                file.write("OFFSET %.6f, %.6f, %.6f\n" % (b_tail[0], b_tail[1], b_tail[2]))
                file.write("SCALE 1.000000, 1.000000, 1.000000\n")
                file.write("X %.6f, %.6f, %.6f\n" % (b_matrix[0][0], b_matrix[1][0], b_matrix[2][0]))
                file.write("Y %.6f, %.6f, %.6f\n" % (b_matrix[0][1], b_matrix[1][1], b_matrix[2][1]))
                file.write("Z %.6f, %.6f, %.6f\n" % (b_matrix[0][2], b_matrix[1][2], b_matrix[2][2]))

    # Write vertex data
    file.write("\nNUMVERTS %i\n" % num_verts_unique)

    for i, me in enumerate(meshes):

        # Get the right object matrix for mesh
        mesh_matrix = meshes_matrix[i]

        # Get bone influences per vertex
        if armature is not None and meshes_vgroup[i] is not None:

            groupNames, vWeightList = meshNormalizedWeights(meshes_vgroup[i],
                                                            me,
                                                            use_weight_min,
                                                            use_weight_min_threshold
                                                            )
            # Get bones by vertex_group names, bind to root if can't find one 
            groupIndices = [bone_mapping.get(g, -1) for g in groupNames]

            weight_group_list = []
            for weights in vWeightList:
                weight_group_list.append(sorted(zip(weights, groupIndices), reverse=True))

        # Use uniquified vert sets and count the verts
        for i_vert, vert in enumerate(verts_unique[i]):
            v = me.vertices[vert]

            # Calculate global coords
            x = mesh_matrix[0][0] * v.co[0] + \
                mesh_matrix[0][1] * v.co[1] + \
                mesh_matrix[0][2] * v.co[2] + \
                mesh_matrix[0][3]

            y = mesh_matrix[1][0] * v.co[0] + \
                mesh_matrix[1][1] * v.co[1] + \
                mesh_matrix[1][2] * v.co[2] + \
                mesh_matrix[1][3]

            z = mesh_matrix[2][0] * v.co[0] + \
                mesh_matrix[2][1] * v.co[1] + \
                mesh_matrix[2][2] * v.co[2] + \
                mesh_matrix[2][3]
                
            #print("%.6f %.6f %.6f single calced xyz\n%.6f %.6f %.6f mat mult" % (x, y, z, ))

            file.write("VERT %i\n" % (i_vert + v_count))

            if use_version == '5':
                file.write("OFFSET %.6f %.6f %.6f\n" % (x, y, z))
            else:
                file.write("OFFSET %.6f, %.6f, %.6f\n" % (x, y, z))

            # Write bone influences
            if armature is None or meshes_vgroup[i] is None:
                file.write("BONES 1\n")
                file.write("BONE 0 1.000000\n\n")
            else:
                cache = ""
                c_bones = 0

                for weight, bone_index in weight_group_list[v.index]:
                    if (use_weight_min and round(weight, 6) < use_weight_min_threshold) or \
                       (not use_weight_min and round(weight, 6) == 0):
                        # No (more) bones with enough weight, totalweight of 0 would lead to error
                        break
                    cache += "BONE %i %.6f\n" % (bone_index, weight)
                    c_bones += 1

                if c_bones == 0:
                    warning_string = "Warning: No bone influence found for vertex %i, binding to bone %i\n" \
                                     % (v.index, bone_index)
                    print(warning_string)
                    file.write("// %s" % warning_string)
                    file.write("BONES 1\n")
                    file.write("BONE %i 0.000001\n\n" % bone_index) # HACK: Is a minimum weight a good idea?
                else:
                    file.write("BONES %i\n%s\n" % (c_bones, cache))

        v_count += len(verts_unique[i]);

    # TODO: Find a better way to keep track of the vertex index?
    v_count = 0

    # Prepare material array
    for me in meshes:
        for f in me.tessfaces:
            try:
                mat = me.materials[f.material_index]
            except (IndexError):
                # Mesh has no material with this index
                # Note: material_index is never None (will be 0 instead)
                continue
            else:
                if mat not in materials:
                    materials.append(mat)

    # Write face data
    file.write("\nNUMFACES %i\n" % num_faces)

    for i_me, me in enumerate(meshes):

        #file.write("// Verts:\n%s\n" % list(enumerate(verts_unique[i_me])))

        for f in me.tessfaces:

            try:
                mat = me.materials[f.material_index]

            except (IndexError):
                mat_index = 0

                warning_string = "Warning: Assigned material with index %i not found, falling back to first\n" \
                                  % f.material_index
                print(warning_string)
                file.write("// %s" % warning_string)

            else:
                try:
                    mat_index = materials.index(mat)

                except (ValueError):
                    mat_index = 0

                    warning_string = "Warning: Material \"%s\" not mapped, falling back to first\n" \
                                      % mat.name
                    print(warning_string)
                    file.write("// %s" % warning_string)

            # Support for vertex colors
            if me.tessface_vertex_colors:
                col = me.tessface_vertex_colors.active.data[f.index]

            # Automatic triangulation support
            f_v_orig = [v for v in enumerate(f.vertices)]

            if len(f_v_orig) == 3:
                f_v_iter = (f_v_orig[2], f_v_orig[1], f_v_orig[0]), # HACK: trailing comma to force a tuple
            else:
                f_v_iter = (f_v_orig[2], f_v_orig[1], f_v_orig[0]), (f_v_orig[3], f_v_orig[2], f_v_orig[0])

            for iter in f_v_iter:

                # TODO: Test material# export (v5 correct?)
                if use_version == '5':
                    file.write("TRI %i %i 0 1\n" % (ob_count, mat_index))
                else:
                    file.write("TRI %i %i 0 0\n" % (ob_count, mat_index))

                for vi, v in iter:

                    no = me.vertices[v].normal # Invert? Orientation seems to have no effect...

                    uv = me.tessface_uv_textures.active
                    uv1 = uv.data[f.index].uv[vi][0]
                    uv2 = 1 - uv.data[f.index].uv[vi][1] # Flip!

                    #if 0 > uv1 > 1 
                    # TODO: Warn if accidentally tiling ( uv <0 or >1 )

                    # Remap vert indices used by face
                    if use_vertex_cleanup:
                        vert_new = verts_unique[i_me].index(v) + v_count
                        #file.write("// %i (%i) --> %i\n" % (v+v_count, v, vert_new))
                    else:
                        vert_new = v + v_count

                    if use_version == '5':
                        file.write("VERT %i %.6f %.6f %.6f %.6f %.6f\n" \
                                   % (vert_new, uv1, uv2, no[0], no[1], no[2]))
                    else:
                        file.write("VERT %i\n" % vert_new)
                        file.write("NORMAL %.6f %.6f %.6f\n" % (no[0], no[1], no[2]))

                        if me.tessface_vertex_colors and use_vertex_colors:

                            if vi == 0:
                                c = col.color1
                            elif vi == 1:
                                c = col.color2
                            elif vi == 2:
                                c = col.color3
                            else:
                                c = col.color4

                            if use_vertex_colors_alpha:

                                # Turn RGB into grayscale (luminance conversion)
                                c_lum = c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11
                                file.write("COLOR 1.000000 1.000000 1.000000 %.6f\n" % c_lum)
                            else:
                                file.write("COLOR %.6f %.6f %.6f 1.000000\n" % (c[0], c[1], c[2]))

                        else:
                            file.write("COLOR 1.000000 1.000000 1.000000 1.000000\n")

                        file.write("UV 1 %.6f %.6f\n" % (uv1, uv2))

        # Note: Face types (tris/quads) have nothing to do with vert indices!
        if use_vertex_cleanup:
            v_count += len(verts_unique[i_me])
        else:
            v_count += len(me.vertices)

        ob_count += 1

    # Write object data
    file.write("\nNUMOBJECTS %i\n" % len(objects))

    for i_ob, ob in enumerate(objects):
        file.write("OBJECT %i \"%s\"\n" % (i_ob, ob))

    # Static material string
    material_string = ("COLOR 0.000000 0.000000 0.000000 1.000000\n"
                       "TRANSPARENCY 0.000000 0.000000 0.000000 1.000000\n"
                       "AMBIENTCOLOR 0.000000 0.000000 0.000000 1.000000\n"
                       "INCANDESCENCE 0.000000 0.000000 0.000000 1.000000\n"
                       "COEFFS 0.800000 0.000000\n"
                       "GLOW 0.000000 0\n"
                       "REFRACTIVE 6 1.000000\n"
                       "SPECULARCOLOR -1.000000 -1.000000 -1.000000 1.000000\n"
                       "REFLECTIVECOLOR -1.000000 -1.000000 -1.000000 1.000000\n"
                       "REFLECTIVE -1 -1.000000\n"
                       "BLINN -1.000000 -1.000000\n"
                       "PHONG -1.000000\n\n"
                       )

    if len(materials) > 0:
        file.write("\nNUMMATERIALS %i\n" % len(materials))

        for i_mat, mat in enumerate(materials):

            try:
                for i_ts, ts in enumerate(mat.texture_slots):

                    # Skip empty slots and disabled textures
                    if not ts or not mat.use_textures[i_ts]:
                        continue

                    # Image type and Color map? If yes, add to material array and index
                    if ts.texture.type == 'IMAGE' and ts.use_map_color_diffuse:

                        # Pick filename of the first color map
                        imagepath = ts.texture.image.filepath
                        imagename = os.path.split(imagepath)[1]
                        if len(imagename) == 0:
                            imagename = "untitled"
                        break
                else:
                    raise(ValueError)

            except:
                imagename = "no color diffuse map found"

            # Material can be assigned and None
            if mat:
                mat_name = mat.name
                mat_shader = mat.diffuse_shader.capitalize()
            else:
                mat_name = "None"
                mat_shader = "Lambert"

            if use_version == '5':
                file.write("MATERIAL %i \"%s\"\n" % (i_mat, imagename))
                # or is it mat.name@filename?
            else:
                file.write("MATERIAL %i \"%s\" \"%s\" \"%s\"\n" % (
                           i_mat,
                           mat_name,
                           mat_shader,
                           imagename
                           ))
                file.write(material_string)
    else:
        # Write a default material
        # Should never happen, nothing to export / mesh without material exceptions already caught
        file.write("\nNUMMATERIALS 1\n")
        if use_version == '5':
            file.write("MATERIAL 0 \"default.tga\"\n")
        else:
            file.write("MATERIAL 0 \"$default\" \"Lambert\" \"untitled\"\n")
            file.write(material_string)

    # Close to flush buffers!
    file.close()

    # Remove meshes, which were made by to_mesh()
    for mesh in meshes:
        mesh.user_clear()
        bpy.data.meshes.remove(mesh)    

    # Quit with no errors
    return

# Taken from export_fbx.py by Campbell Barton
# Modified to accept vertex_groups directly instead of mesh object
def BPyMesh_meshWeight2List(vgroup, me):

    """ Takes a mesh and return its group names and a list of lists, one list per vertex.
    aligning the each vert list with the group names, each list contains float value for the weight.
    These 2 lists can be modified and then used with list2MeshWeight to apply the changes.
    """

    # Clear the vert group.
    groupNames = [g.name for g in vgroup]
    len_groupNames = len(groupNames)

    if not len_groupNames:
        # no verts? return a vert aligned empty list
        #return [[] for i in range(len(me.vertices))], []
        return [], []

    else:
        vWeightList = [[0.0] * len_groupNames for i in range(len(me.vertices))]

    for i, v in enumerate(me.vertices):
        for g in v.groups:
            # possible weights are out of range
            index = g.group
            if index < len_groupNames:
                vWeightList[i][index] = g.weight

    return groupNames, vWeightList

def meshNormalizedWeights(vgroup, me, weight_min, weight_min_threshold):

    groupNames, vWeightList = BPyMesh_meshWeight2List(vgroup, me)

    if not groupNames:
        return [], []

    for vWeights in vWeightList:
        tot = 0.0
        for w in vWeights:
            if weight_min and w < weight_min_threshold:
                w = 0.0
            tot += w

        if tot:
            for j, w in enumerate(vWeights):
                vWeights[j] = w / tot

    return groupNames, vWeightList

def _skip_notice(ob_name, mesh_name, notice):
    print("\nSkipped object \"%s\" (mesh \"%s\"): %s" % (ob_name, mesh_name, notice))
