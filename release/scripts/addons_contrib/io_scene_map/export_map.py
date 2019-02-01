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

#http://www.pasteall.org/47943/python

# <pep8-80 compliant>

import bpy
import os
import mathutils
from mathutils import Vector

from contextlib import redirect_stdout
import io
stdout = io.StringIO()

# TODO, make options
PREF_SCALE = 1
PREF_FACE_THICK = 0.1
PREF_GRID_SNAP = False
# Quake 1/2?
# Quake 3+?
PREF_DEF_TEX_OPTS = '0 0 0 1 1 0 0 0'  # not user settable yet

PREF_NULL_TEX = 'NULL'  # not user settable yet
PREF_INVIS_TEX = 'common/caulk'
PREF_DOOM3_FORMAT = True


def face_uv_image_get(me, face):
    uv_faces = me.uv_textures.active
    if uv_faces:
        return uv_faces.data[face.index].image
    else:
        return None


def face_uv_coords_get(me, face):
    tf_uv_faces = me.tessface_uv_textures.active
    if tf_uv_faces:
        return tf_uv_faces.data[face.index].uv_raw[:]
    else:
        return None


def face_material_get(me, face):
    idx = face.material_index
    return me.materials[idx] if idx < len(me.materials) else None


def poly_to_doom(me, p, radius):
    """
    Convert a face into Doom3 representation (infinite plane defined by its normal
    and distance from origin along that normal).
    """
    # Compute the distance to the mesh from the origin to the plane.
    # Line from origin in the direction of the face normal.
    origin = Vector((0, 0, 0))
    target = Vector(p.normal) * radius
    # Find the target point.
    intersect = mathutils.geometry.intersect_line_plane(origin, target, Vector(p.center), Vector(p.normal))
    # We have to handle cases where intersection with face happens on the "negative" part of the vector!
    length = intersect.length
    nor = p.normal.copy()
    if (nor.dot(intersect.normalized()) > 0):
        length *= -1
    nor.resize_4d()
    nor.w = length
    return nor


def doom_are_same_planes(p1, p2):
    """
    To avoid writing two planes that are nearly the same!
    """
    # XXX Is sign of the normal/length important in Doom for plane definition??? For now, assume that no!
    if p1.w < 0:
        p1 = p1 * -1.0
    if p2.w < 0:
        p2 = p2 * -1.0

    threshold = 0.0001

    if abs(p1.w - p2.w) > threshold:
        return False

    # Distances are the same, check orientations!
    if p1.xyz.normalized().dot(p2.xyz.normalized()) < (1 - threshold):
        return False

    # Same plane!
    return True


def doom_check_plane(done_planes, plane):
    """
    Check if plane as already been handled, or is similar enough to an already handled one.
    Return True if it has already been handled somehow.
    done_planes is expected to be a dict {written_plane: {written_plane, similar_plane_1, similar_plane_2, ...}, ...}.
    """
    p_key = tuple(plane)
    if p_key in done_planes:
        return True
    for p, dp in done_planes.items():
        if p_key in dp:
            return True
        elif doom_are_same_planes(Vector(p), plane):
            done_planes[p].add(p_key)
            return True
    done_planes[p_key] = {p_key}
    return False


def ob_to_radius(ob):
    radius = max(Vector(pt).length for pt in ob.bound_box)

    # Make the ray casts, go just outside the bounding sphere.
    return radius * 1.1


def is_cube_facegroup(faces):
    """
    Returns a bool, true if the faces make up a cube
    """
    # cube must have 6 faces
    if len(faces) != 6:
        # print('1')
        return False

    # Check for quads and that there are 6 unique verts
    verts = {}
    for f in faces:
        f_v = f.vertices[:]
        if len(f_v) != 4:
            return False

        for v in f_v:
            verts[v] = 0

    if len(verts) != 8:
        return False

    # Now check that each vert has 3 face users
    for f in faces:
        f_v = f.vertices[:]
        for v in f_v:
            verts[v] += 1

    for v in verts.values():
        if v != 3:  # vert has 3 users?
            return False

    # Could we check for 12 unique edges??, probably not needed.
    return True


def is_tricyl_facegroup(faces):
    """
    is the face group a tri cylinder
    Returns a bool, true if the faces make an extruded tri solid
    """

    # tricyl must have 5 faces
    if len(faces) != 5:
        #  print('1')
        return False

    # Check for quads and that there are 6 unique verts
    verts = {}
    tottri = 0
    for f in faces:
        if len(f.vertices) == 3:
            tottri += 1

        for vi in f.vertices:
            verts[vi] = 0

    if len(verts) != 6 or tottri != 2:
        return False

    # Now check that each vert has 3 face users
    for f in faces:
        for vi in f.vertices:
            verts[vi] += 1

    for v in verts.values():
        if v != 3:  # vert has 3 users?
            return False

    # Could we check for 9 unique edges??, probably not needed.
    return True


def split_mesh_in_convex_parts(me):
    """
    Not implemented yet. Should split given mesh into manifold convex meshes.
    For now simply always returns the given mesh.
    """
    # TODO.
    return (me,)


def round_vec(v):
    if PREF_GRID_SNAP:
        return v.to_tuple(0)
    else:
        return v[:]


def write_quake_brush_cube(fw, ob, faces):
    """
    Takes 6 faces and writes a brush,
    these faces can be from 1 mesh, 1 cube within a mesh of larger cubes
    Faces could even come from different meshes or be contrived.
    """
    format_vec = '( %d %d %d ) ' if PREF_GRID_SNAP else '( %.9g %.9g %.9g ) '

    fw('// brush from cube\n{\n')

    for f in faces:
        # from 4 verts this gets them in reversed order and only 3 of them
        # 0,1,2,3 -> 2,1,0
        me = f.id_data  # XXX25

        for v in f.vertices[:][2::-1]:
            fw(format_vec % round_vec(me.vertices[v].co))

        material = face_material_get(me, f)

        if material and material.game_settings.invisible:
            fw(PREF_INVIS_TEX)
        else:
            image = face_uv_image_get(me, f)
            if image:
                fw(os.path.splitext(bpy.path.basename(image.filepath))[0])
            else:
                fw(PREF_NULL_TEX)
        fw(" %s\n" % PREF_DEF_TEX_OPTS)  # Texture stuff ignored for now

    fw('}\n')


def write_quake_brush_face(fw, ob, face):
    """
    takes a face and writes it as a brush
    each face is a cube/brush.
    """
    format_vec = '( %d %d %d ) ' if PREF_GRID_SNAP else '( %.9g %.9g %.9g ) '

    image_text = PREF_NULL_TEX

    me = face.id_data
    material = face_material_get(me, face)

    if material and material.game_settings.invisible:
        image_text = PREF_INVIS_TEX
    else:
        image = face_uv_image_get(me, face)
        if image:
            image_text = os.path.splitext(bpy.path.basename(image.filepath))[0]

    # reuse face vertices
    f_vertices = [me.vertices[vi] for vi in face.vertices]

    # original verts as tuples for writing
    orig_vco = tuple(round_vec(v.co) for v in f_vertices)

    # new verts that give the face a thickness
    dist = PREF_SCALE * PREF_FACE_THICK
    new_vco = tuple(round_vec(v.co - (v.normal * dist)) for v in f_vertices)
    #new_vco = [round_vec(v.co - (face.no * dist)) for v in face]

    fw('// brush from face\n{\n')
    # front
    for co in orig_vco[2::-1]:
        fw(format_vec % co)

    fw(image_text)
    fw(" %s\n" % PREF_DEF_TEX_OPTS)  # Texture stuff ignored for now

    for co in new_vco[:3]:
        fw(format_vec % co)
    if image and not material.game_settings.use_backface_culling: #uf.use_twoside:
        fw(image_text)
    else:
        fw(PREF_INVIS_TEX)
    fw(" %s\n" % PREF_DEF_TEX_OPTS)  # Texture stuff ignored for now

    # sides.
    if len(orig_vco) == 3:  # Tri, it seemms tri brushes are supported.
        index_pairs = ((0, 1), (1, 2), (2, 0))
    else:
        index_pairs = ((0, 1), (1, 2), (2, 3), (3, 0))

    for i1, i2 in index_pairs:
        for co in orig_vco[i1], orig_vco[i2], new_vco[i2]:
            fw(format_vec % co)
        fw(PREF_INVIS_TEX)
        fw(" %s\n" % PREF_DEF_TEX_OPTS)  # Texture stuff ignored for now

    fw('}\n')


def write_doom_brush(fw, ob, me):
    """
    Takes a mesh object and writes its convex parts.
    """
    format_vec = '( {} {} {} {} ) '
    format_vec_uv = '( ( {} {} {} ) ( {} {} {} ) ) '
    # Get the bounding sphere for the object for ray-casting
    radius = ob_to_radius(ob)

    fw('// brush from faces\n{\n'
       'brushDef3\n{\n'
      )

    done_planes = {}  # Store already written plane, to avoid writing the same one (or a similar-enough one) again.

    for p in me.polygons:
        image_text = PREF_NULL_TEX
        material = face_material_get(me, p)

        if material:
            if material.game_settings.invisible:
                image_text = PREF_INVIS_TEX
            else:
                image_text = material.name

        # reuse face vertices
        plane = poly_to_doom(me, p, radius)
        if plane is None:
            print("    ERROR: Could not create the plane from polygon!");
        elif doom_check_plane(done_planes, plane):
            #print("    WARNING: Polygon too similar to another one!");
            pass
        else:
            fw(format_vec.format(*plane.to_tuple(6)))
            fw(format_vec_uv.format(0.015625, 0, 1, 0, 0.015625, 1)) # TODO insert UV stuff here
            fw('"%s" ' % image_text)
            fw("%s\n" % PREF_DEF_TEX_OPTS)  # Texture stuff ignored for now

    fw('}\n}\n')


def write_node_map(fw, ob):
    """
    Writes the properties of an object (empty in this case)
    as a MAP node as long as it has the property name - classname
    returns True/False based on weather a node was written
    """
    props = [(p.name, p.value) for p in ob.game.properties]

    IS_MAP_NODE = False
    for name, value in props:
        if name == "classname":
            IS_MAP_NODE = True
            break

    if not IS_MAP_NODE:
        return False

    # Write a node
    fw('{\n')
    for name_value in props:
        fw('"%s" "%s"\n' % name_value)
    fw('"origin" "%.9g %.9g %.9g"\n' % round_vec(ob.matrix_world.to_translation()))

    fw('}\n')
    return True


def split_objects(context, objects):
    scene = context.scene
    view_layer = context.view_layer
    final_objects = []

    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)

    bpy.ops.object.duplicate()
    objects = bpy.context.selected_objects

    bpy.ops.object.select_all(action='DESELECT')

    tot_ob = len(objects)
    for i, ob in enumerate(objects):
        print("Splitting object: %d/%d" % (i, tot_ob))
        ob.select_set(True)

        if ob.type == "MESH":
            view_layer.objects.active = ob
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.object.mode_set(mode='OBJECT')
            for edge in ob.data.edges:
                if edge.use_seam:
                    edge.select = True
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.edge_split()
            bpy.ops.mesh.separate(type='LOOSE')
            bpy.ops.object.mode_set(mode='OBJECT')

            split_objects = context.selected_objects
            for split_ob in split_objects:
                assert(split_ob.type == "MESH")

                view_layer.objects.active = split_ob
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_mode(type='EDGE')
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.region_to_loop()
                bpy.ops.mesh.fill_holes(sides=8)
                slot_idx = 0
                for slot_idx, m in enumerate(split_ob.material_slots):
                   if m.name == "textures/common/caulk":
                      break
                   #if m.name != "textures/common/caulk":
                   #   mat = bpy.data.materials.new("textures/common/caulk")
                   #   bpy.context.object.data.materials.append(mat)
                split_ob.active_material_index = slot_idx  # we need to use either actual material name or custom property instead of index
                bpy.ops.object.material_slot_assign()
                with redirect_stdout(stdout):
                   bpy.ops.mesh.remove_doubles()
                bpy.ops.mesh.quads_convert_to_tris()
                bpy.ops.mesh.tris_convert_to_quads()
                bpy.ops.object.mode_set(mode='OBJECT')
            final_objects += split_objects

        ob.select_set(False)

    print(final_objects)
    return final_objects


def export_map(context, filepath):
    """
    pup_block = [\
    ('Scale:', PREF_SCALE, 1, 1000,
            'Scale the blender scene by this value.'),\
    ('Face Width:', PREF_FACE_THICK, 0.01, 10,
            'Thickness of faces exported as brushes.'),\
    ('Grid Snap', PREF_GRID_SNAP,
            'snaps floating point values to whole numbers.'),\
    'Null Texture',\
    ('', PREF_NULL_TEX, 1, 128,
            'Export textureless faces with this texture'),\
    'Unseen Texture',\
    ('', PREF_INVIS_TEX, 1, 128,
            'Export invisible faces with this texture'),\
    ]

    if not Draw.PupBlock('map export', pup_block):
        return
    """
    import time
    from mathutils import Matrix
    from bpy_extras import mesh_utils

    t = time.time()
    print("Map Exporter 0.0")

    scene = context.scene
    collection = context.collection
    objects = context.selected_objects

    obs_mesh = []
    obs_lamp = []
    obs_surf = []
    obs_empty = []

    SCALE_MAT = Matrix()
    SCALE_MAT[0][0] = SCALE_MAT[1][1] = SCALE_MAT[2][2] = PREF_SCALE

    TOTBRUSH = TOTLAMP = TOTNODE = 0

    for ob in objects:
        type = ob.type
        if type == 'MESH':
            obs_mesh.append(ob)
        elif type == 'SURFACE':
            obs_surf.append(ob)
        elif type == 'LAMP':
            obs_lamp.append(ob)
        elif type == 'EMPTY':
            obs_empty.append(ob)

    obs_mesh = split_objects(context, obs_mesh)

    with open(filepath, 'w') as fl:
        fw = fl.write

        if obs_mesh or obs_surf:
            if PREF_DOOM3_FORMAT:
                fw('Version 2')

            # brushes and surf's must be under worldspan
            fw('\n// entity 0\n')
            fw('{\n')
            fw('"classname" "worldspawn"\n')

        print("\twriting cubes from meshes")

        tot_ob = len(obs_mesh)
        for i, ob in enumerate(obs_mesh):
            print("Exporting object: %d/%d" % (i, tot_ob))

            dummy_mesh = ob.to_mesh(scene, True, 'PREVIEW')

            #print len(mesh_split2connected(dummy_mesh))

            # 1 to tx the normals also
            dummy_mesh.transform(ob.matrix_world * SCALE_MAT)

            # High quality normals
            #XXX25: BPyMesh.meshCalcNormals(dummy_mesh)

            if PREF_DOOM3_FORMAT:
                for me in split_mesh_in_convex_parts(dummy_mesh):
                    write_doom_brush(fw, ob, me)
                    TOTBRUSH += 1
                    if (me is not dummy_mesh):
                        bpy.data.meshes.remove(me)
            else:
                # We need tessfaces
                dummy_mesh.update(calc_tessface=True)
                # Split mesh into connected regions
                for face_group in mesh_utils.mesh_linked_tessfaces(dummy_mesh):
                    if is_cube_facegroup(face_group):
                        write_quake_brush_cube(fw, ob, face_group)
                        TOTBRUSH += 1
                    elif is_tricyl_facegroup(face_group):
                        write_quake_brush_cube(fw, ob, face_group)
                        TOTBRUSH += 1
                    else:
                        for f in face_group:
                            write_quake_brush_face(fw, ob, f)
                            TOTBRUSH += 1

                #print 'warning, not exporting "%s" it is not a cube' % ob.name
                bpy.data.meshes.remove(dummy_mesh)

        valid_dims = 3, 5, 7, 9, 11, 13, 15
        for ob in obs_surf:
            '''
            Surf, patches
            '''
            data = ob.data
            surf_name = data.name
            mat = ob.matrix_world * SCALE_MAT

            # This is what a valid patch looks like
            """
            // brush 0
            {
            patchDef2
            {
            NULL
            ( 3 3 0 0 0 )
            (
            ( ( -64 -64 0 0 0 ) ( -64 0 0 0 -2 ) ( -64 64 0 0 -4 ) )
            ( ( 0 -64 0 2 0 ) ( 0 0 0 2 -2 ) ( 0 64 0 2 -4 ) )
            ( ( 64 -64 0 4 0 ) ( 64 0 0 4 -2 ) ( 80 88 0 4 -4 ) )
            )
            }
            }
            """
            for i, nurb in enumerate(data.splines):
                u = nurb.point_count_u
                v = nurb.point_count_v
                if u in valid_dims and v in valid_dims:

                    fw('// brush %d surf_name\n' % i)
                    fw('{\n')
                    fw('patchDef2\n')
                    fw('{\n')
                    fw('NULL\n')
                    fw('( %d %d 0 0 0 )\n' % (u, v))
                    fw('(\n')

                    u_iter = 0
                    for p in nurb.points:

                        if u_iter == 0:
                            fw('(')

                        u_iter += 1

                        # add nmapping 0 0 ?
                        if PREF_GRID_SNAP:
                            fw(" ( %d %d %d 0 0 )" %
                                       round_vec(mat * p.co.xyz))
                        else:
                            fw(' ( %.6f %.6f %.6f 0 0 )' %
                                       (mat * p.co.xyz)[:])

                        # Move to next line
                        if u_iter == u:
                            fw(' )\n')
                            u_iter = 0

                    fw(')\n')
                    fw('}\n')
                    fw('}\n')
                    # Debugging
                    # for p in nurb: print 'patch', p

                else:
                    print("Warning: not exporting patch",
                          surf_name, u, v, 'Unsupported')

        if obs_mesh or obs_surf:
            fw('}\n')  # end worldspan

        print("\twriting lamps")
        for ob in obs_lamp:
            print("\t\t%s" % ob.name)
            lamp = ob.data
            fw('{\n')
            fw('"classname" "light"\n')
            fw('"light" "%.6f"\n' % (lamp.distance * PREF_SCALE))
            if PREF_GRID_SNAP:
                fw('"origin" "%d %d %d"\n' %
                           tuple([round(axis * PREF_SCALE)
                                  for axis in ob.matrix_world.to_translation()]))
            else:
                fw('"origin" "%.6f %.6f %.6f"\n' %
                           tuple([axis * PREF_SCALE
                                  for axis in ob.matrix_world.to_translation()]))

            fw('"_color" "%.6f %.6f %.6f"\n' % tuple(lamp.color))
            fw('"style" "0"\n')
            fw('}\n')
            TOTLAMP += 1

        print("\twriting empty objects as nodes")
        for ob in obs_empty:
            if write_node_map(fw, ob):
                print("\t\t%s" % ob.name)
                TOTNODE += 1
            else:
                print("\t\tignoring %s" % ob.name)

    for ob in obs_mesh:
        collection.objects.unlink(ob)
        bpy.data.objects.remove(ob)

    print("Exported Map in %.4fsec" % (time.time() - t))
    print("Brushes: %d  Nodes: %d  Lamps %d\n" % (TOTBRUSH, TOTNODE, TOTLAMP))


def save(operator,
         context,
         filepath=None,
         global_scale=1.0,
         face_thickness=0.1,
         texture_null="NULL",
         texture_opts='0 0 0 1 1 0 0 0',
         grid_snap=False,
         doom3_format=True,
         ):

    global PREF_SCALE
    global PREF_FACE_THICK
    global PREF_NULL_TEX
    global PREF_DEF_TEX_OPTS
    global PREF_GRID_SNAP
    global PREF_DOOM3_FORMAT

    PREF_SCALE = global_scale
    PREF_FACE_THICK = face_thickness
    PREF_NULL_TEX = texture_null
    PREF_DEF_TEX_OPTS = texture_opts
    PREF_GRID_SNAP = grid_snap
    PREF_DOOM3_FORMAT = doom3_format

    if (PREF_DOOM3_FORMAT):
        PREF_DEF_TEX_OPTS = '0 0 0'
    else:
        PREF_DEF_TEX_OPTS = '0 0 0 1 1 0 0 0'

    export_map(context, filepath)

    return {'FINISHED'}
