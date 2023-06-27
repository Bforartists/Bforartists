# SPDX-FileCopyrightText: 2012 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

import bpy
import bmesh

if bpy.app.background:
    def _redraw_yasiamevil():
        pass
else:
    def _redraw_yasiamevil():
        _redraw_yasiamevil.opr(**_redraw_yasiamevil.arg)
    _redraw_yasiamevil.opr = bpy.ops.wm.redraw_timer
    _redraw_yasiamevil.arg = dict(type='DRAW_WIN_SWAP', iterations=1)


def _points_from_object(depsgraph, scene, obj, source):

    _source_all = {
        'PARTICLE_OWN', 'PARTICLE_CHILD',
        'PENCIL',
        'VERT_OWN', 'VERT_CHILD',
    }

    # print(source - _source_all)
    # print(source)
    assert(len(source | _source_all) == len(_source_all))
    assert(len(source))

    points = []

    def edge_center(mesh, edge):
        v1, v2 = edge.vertices
        return (mesh.vertices[v1].co + mesh.vertices[v2].co) / 2.0

    def poly_center(mesh, poly):
        from mathutils import Vector
        co = Vector()
        tot = 0
        for i in poly.loop_indices:
            co += mesh.vertices[mesh.loops[i].vertex_index].co
            tot += 1
        return co / tot

    def points_from_verts(obj):
        """Takes points from _any_ object with geometry"""
        if obj.type == 'MESH':
            mesh = obj.data
            matrix = obj.matrix_world.copy()
            points.extend([matrix @ v.co for v in mesh.vertices])
        else:
            ob_eval = ob.evaluated_get(depsgraph)
            try:
                mesh = ob_eval.to_mesh()
            except:
                mesh = None

            if mesh is not None:
                matrix = obj.matrix_world.copy()
                points.extend([matrix @ v.co for v in mesh.vertices])
                ob_eval.to_mesh_clear()

    def points_from_particles(obj):
        obj_eval = obj.evaluated_get(depsgraph)
        points.extend([p.location.copy()
                       for psys in obj_eval.particle_systems
                       for p in psys.particles])

    # geom own
    if 'VERT_OWN' in source:
        points_from_verts(obj)

    # geom children
    if 'VERT_CHILD' in source:
        for obj_child in obj.children:
            points_from_verts(obj_child)

    # geom particles
    if 'PARTICLE_OWN' in source:
        points_from_particles(obj)

    if 'PARTICLE_CHILD' in source:
        for obj_child in obj.children:
            points_from_particles(obj_child)

    # grease pencil
    def get_points(stroke):
        return [point.co.copy() for point in stroke.points]

    def get_splines(gp):
        if gp.layers.active:
            frame = gp.layers.active.active_frame
            return [get_points(stroke) for stroke in frame.strokes]
        else:
            return []

    if 'PENCIL' in source:
        # Used to be from object in 2.7x, now from scene.
        gp = scene.grease_pencil
        if gp:
            points.extend([p for spline in get_splines(gp) for p in spline])

    print("Found %d points" % len(points))

    return points


def cell_fracture_objects(
        context, collection, obj,
        source={'PARTICLE_OWN'},
        source_limit=0,
        source_noise=0.0,
        clean=True,
        # operator options
        use_smooth_faces=False,
        use_data_match=False,
        use_debug_points=False,
        margin=0.0,
        material_index=0,
        use_debug_redraw=False,
        cell_scale=(1.0, 1.0, 1.0),
):
    from . import fracture_cell_calc
    depsgraph = context.evaluated_depsgraph_get()
    scene = context.scene
    view_layer = context.view_layer

    # -------------------------------------------------------------------------
    # GET POINTS

    points = _points_from_object(depsgraph, scene, obj, source)

    if not points:
        # print using fallback
        points = _points_from_object(depsgraph, scene, obj, {'VERT_OWN'})

    if not points:
        print("no points found")
        return []

    # apply optional clamp
    if source_limit != 0 and source_limit < len(points):
        import random
        random.shuffle(points)
        points[source_limit:] = []

    # sadly we can't be sure there are no doubles
    from mathutils import Vector
    to_tuple = Vector.to_tuple
    points = list({to_tuple(p, 4): p for p in points}.values())
    del to_tuple
    del Vector

    # end remove doubles
    # ------------------

    if source_noise > 0.0:
        from random import random
        # boundbox approx of overall scale
        from mathutils import Vector
        matrix = obj.matrix_world.copy()
        bb_world = [matrix @ Vector(v) for v in obj.bound_box]
        scalar = source_noise * ((bb_world[0] - bb_world[6]).length / 2.0)

        from mathutils.noise import random_unit_vector

        points[:] = [p + (random_unit_vector() * (scalar * random())) for p in points]

    if use_debug_points:
        bm = bmesh.new()
        for p in points:
            bm.verts.new(p)
        mesh_tmp = bpy.data.meshes.new(name="DebugPoints")
        bm.to_mesh(mesh_tmp)
        bm.free()
        obj_tmp = bpy.data.objects.new(name=mesh_tmp.name, object_data=mesh_tmp)
        collection.objects.link(obj_tmp)
        del obj_tmp, mesh_tmp

    mesh = obj.data
    matrix = obj.matrix_world.copy()
    verts = [matrix @ v.co for v in mesh.vertices]

    cells = fracture_cell_calc.points_as_bmesh_cells(
        verts,
        points,
        cell_scale,
        margin_cell=margin,
    )

    # some hacks here :S
    cell_name = obj.name + "_cell"

    objects = []

    for center_point, cell_points in cells:

        # ---------------------------------------------------------------------
        # BMESH

        # create the convex hulls
        bm = bmesh.new()

        # WORKAROUND FOR CONVEX HULL BUG/LIMIT
        # XXX small noise
        import random

        def R():
            return (random.random() - 0.5) * 0.001
        # XXX small noise

        for i, co in enumerate(cell_points):

            # XXX small noise
            co.x += R()
            co.y += R()
            co.z += R()
            # XXX small noise

            bm_vert = bm.verts.new(co)

        import mathutils
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.005)
        try:
            bmesh.ops.convex_hull(bm, input=bm.verts)
        except RuntimeError:
            import traceback
            traceback.print_exc()

        if clean:
            bm.normal_update()
            try:
                bmesh.ops.dissolve_limit(bm, verts=bm.verts, angle_limit=0.001)
            except RuntimeError:
                import traceback
                traceback.print_exc()
        # Smooth faces will remain only inner faces, after applying boolean modifier.
        if use_smooth_faces:
            for bm_face in bm.faces:
                bm_face.smooth = True

        if material_index != 0:
            for bm_face in bm.faces:
                bm_face.material_index = material_index

        # ---------------------------------------------------------------------
        # MESH
        mesh_dst = bpy.data.meshes.new(name=cell_name)

        bm.to_mesh(mesh_dst)
        bm.free()
        del bm

        if use_data_match:
            # match materials and data layers so boolean displays them
            # currently only materials + data layers, could do others...
            mesh_src = obj.data
            for mat in mesh_src.materials:
                mesh_dst.materials.append(mat)
            for lay_attr in ("vertex_colors", "uv_layers"):
                lay_src = getattr(mesh_src, lay_attr)
                lay_dst = getattr(mesh_dst, lay_attr)
                for key in lay_src.keys():
                    lay_dst.new(name=key)

        # ---------------------------------------------------------------------
        # OBJECT

        obj_cell = bpy.data.objects.new(name=cell_name, object_data=mesh_dst)
        collection.objects.link(obj_cell)
        # scene.objects.active = obj_cell
        obj_cell.location = center_point

        objects.append(obj_cell)

        # support for object materials
        if use_data_match:
            for i in range(len(mesh_dst.materials)):
                slot_src = obj.material_slots[i]
                slot_dst = obj_cell.material_slots[i]

                slot_dst.link = slot_src.link
                slot_dst.material = slot_src.material

        if use_debug_redraw:
            view_layer.update()
            _redraw_yasiamevil()

    view_layer.update()

    return objects


def cell_fracture_boolean(
        context, collection, obj, objects,
        use_debug_bool=False,
        clean=True,
        use_island_split=False,
        use_interior_hide=False,
        use_debug_redraw=False,
        level=0,
        remove_doubles=True
):

    objects_boolean = []
    scene = context.scene
    view_layer = context.view_layer

    if use_interior_hide and level == 0:
        # only set for level 0
        obj.data.polygons.foreach_set("hide", [False] * len(obj.data.polygons))

    for obj_cell in objects:
        mod = obj_cell.modifiers.new(name="Boolean", type='BOOLEAN')
        mod.object = obj
        mod.operation = 'INTERSECT'

        if not use_debug_bool:

            if use_interior_hide:
                obj_cell.data.polygons.foreach_set("hide", [True] * len(obj_cell.data.polygons))

    # Calculates all booleans at once (faster).
    depsgraph = context.evaluated_depsgraph_get()

    for obj_cell in objects:

        if not use_debug_bool:

            obj_cell_eval = obj_cell.evaluated_get(depsgraph)
            mesh_new = bpy.data.meshes.new_from_object(obj_cell_eval)
            mesh_old = obj_cell.data
            obj_cell.data = mesh_new
            obj_cell.modifiers.remove(obj_cell.modifiers[-1])

            # remove if not valid
            if not mesh_old.users:
                bpy.data.meshes.remove(mesh_old)
            if not mesh_new.vertices:
                collection.objects.unlink(obj_cell)
                if not obj_cell.users:
                    bpy.data.objects.remove(obj_cell)
                    obj_cell = None
                    if not mesh_new.users:
                        bpy.data.meshes.remove(mesh_new)
                        mesh_new = None

            # avoid unneeded bmesh re-conversion
            if mesh_new is not None:
                bm = None

                if clean:
                    if bm is None:  # ok this will always be true for now...
                        bm = bmesh.new()
                        bm.from_mesh(mesh_new)
                    bm.normal_update()
                    try:
                        bmesh.ops.dissolve_limit(bm, verts=bm.verts, edges=bm.edges, angle_limit=0.001)
                    except RuntimeError:
                        import traceback
                        traceback.print_exc()

                if remove_doubles:
                    if bm is None:
                        bm = bmesh.new()
                        bm.from_mesh(mesh_new)
                    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.005)

                if bm is not None:
                    bm.to_mesh(mesh_new)
                    bm.free()

            del mesh_new
            del mesh_old

        if obj_cell is not None:
            objects_boolean.append(obj_cell)

            if use_debug_redraw:
                _redraw_yasiamevil()

    if (not use_debug_bool) and use_island_split:
        # this is ugly and Im not proud of this - campbell
        for ob in view_layer.objects:
            ob.select_set(False)
        for obj_cell in objects_boolean:
            obj_cell.select_set(True)

        bpy.ops.mesh.separate(type='LOOSE')

        objects_boolean[:] = [obj_cell for obj_cell in view_layer.objects if obj_cell.select_get()]

    context.view_layer.update()

    return objects_boolean


def cell_fracture_interior_handle(
        objects,
        use_interior_vgroup=False,
        use_sharp_edges=False,
        use_sharp_edges_apply=False,
):
    """Run after doing _all_ booleans"""

    assert(use_interior_vgroup or use_sharp_edges or use_sharp_edges_apply)

    for obj_cell in objects:
        mesh = obj_cell.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        if use_interior_vgroup:
            for bm_vert in bm.verts:
                bm_vert.tag = True
            for bm_face in bm.faces:
                if not bm_face.hide:
                    for bm_vert in bm_face.verts:
                        bm_vert.tag = False

            # now add all vgroups
            defvert_lay = bm.verts.layers.deform.verify()
            for bm_vert in bm.verts:
                if bm_vert.tag:
                    bm_vert[defvert_lay][0] = 1.0

            # add a vgroup
            obj_cell.vertex_groups.new(name="Interior")

        if use_sharp_edges:
            for bm_edge in bm.edges:
                if len({bm_face.hide for bm_face in bm_edge.link_faces}) == 2:
                    bm_edge.smooth = False

            if use_sharp_edges_apply:
                edges = [edge for edge in bm.edges if edge.smooth is False]
                if edges:
                    bm.normal_update()
                    bmesh.ops.split_edges(bm, edges=edges)

        for bm_face in bm.faces:
            bm_face.hide = False

        bm.to_mesh(mesh)
        bm.free()
