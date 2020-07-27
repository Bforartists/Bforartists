import bpy
import bmesh


def _redraw_yasiamevil():
    _redraw_yasiamevil.opr(**_redraw_yasiamevil.arg)
_redraw_yasiamevil.opr = bpy.ops.wm.redraw_timer
_redraw_yasiamevil.arg = dict(type='DRAW_WIN_SWAP', iterations=1)

def _limit_source(points, source_limit):
    if source_limit != 0 and source_limit < len(points):
        import random
        random.shuffle(points)
        points[source_limit:] = []
        return points
    else:
        return points


def simplify_original(original, pre_simplify):
    bpy.context.view_layer.objects.active = original
    bpy.ops.object.modifier_add(type='DECIMATE')
    decimate = bpy.context.object.modifiers[-1]
    decimate.name = 'DECIMATE_crackit_original'
    decimate.ratio = 1-pre_simplify

def desimplify_original(original):
    bpy.context.view_layer.objects.active = original
    if 'DECIMATE_crackit_original' in bpy.context.object.modifiers.keys():
        bpy.ops.object.modifier_remove(modifier='DECIMATE_crackit_original')

def original_minmax(original_verts):
    xa = [v[0] for v in original_verts]
    ya = [v[1] for v in original_verts]
    za = [v[2] for v in original_verts]
    xmin, xmax = min(xa), max(xa)
    ymin, ymax = min(ya), max(ya)
    zmin, zmax = min(za), max(za)
    return {"x":(xmin,xmax), "y":(ymin,ymax), "z":(zmin,zmax)}

def points_from_object(original, original_xyz_minmax,
                       source_vert_own=100,
                       source_vert_child=0,
                       source_particle_own=0,
                       source_particle_child=0,
                       source_pencil=0,
                       source_random=0):

    points = []

    # This is not used by anywhere
    def edge_center(mesh, edge):
        v1, v2 = edge.vertices
        return (mesh.vertices[v1].co + mesh.vertices[v2].co) / 2.0

    # This is not used by anywhere
    def poly_center(mesh, poly):
        from mathutils import Vector
        co = Vector()
        tot = 0
        for i in poly.loop_indices:
            co += mesh.vertices[mesh.loops[i].vertex_index].co
            tot += 1
        return co / tot

    def points_from_verts(original):
        """Takes points from _any_ object with geometry"""
        if original.type == 'MESH':
            mesh = original.data
            matrix = original.matrix_world.copy()
            p = [(matrix @ v.co, 'VERTS') for v in mesh.vertices]
            return p
        else:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            ob_eval = original.evaluated_get(depsgraph)
            try:
                mesh = ob_eval.to_mesh()
            except:
                mesh = None

            if mesh is not None:
                matrix = original.matrix_world.copy()
                p =  [(matrix @ v.co, 'VERTS') for v in mesh.vertices]
                ob_eval.to_mesh_clear()
                return p

    def points_from_particles(original):
        depsgraph = bpy.context.evaluated_depsgraph_get()
        obj_eval = original.evaluated_get(depsgraph)

        p = [(particle.location.copy(), 'PARTICLE')
               for psys in obj_eval.particle_systems
               for particle in psys.particles]
        return p

    def points_from_random(original, original_xyz_minmax):
        xmin, xmax = original_xyz_minmax["x"]
        ymin, ymax = original_xyz_minmax["y"]
        zmin, zmax = original_xyz_minmax["z"]

        from random import uniform
        from mathutils import Vector

        p = []
        for i in range(source_random):
            new_pos = Vector( (uniform(xmin, xmax), uniform(ymin, ymax), uniform(zmin, zmax)) )
            p.append((new_pos, 'RANDOM'))
        return p

     # geom own
    if source_vert_own > 0:
        new_points = points_from_verts(original)
        new_points = _limit_source(new_points, source_vert_own)
        points.extend(new_points)

    # random
    if source_random > 0:
        new_points = points_from_random(original, original_xyz_minmax)
        points.extend(new_points)


    # geom children
    if source_vert_child > 0:
        for original_child in original.children:
            new_points  = points_from_verts(original_child)
            new_points = _limit_source(new_points, source_vert_child)
            points.extend(new_points)

    # geom particles
    if source_particle_own > 0:
        new_points = points_from_particles(original)
        new_points = _limit_source(new_points, source_particle_own)
        points.extend(new_points)

    if source_particle_child > 0:
        for original_child in original.children:
            new_points = points_from_particles(original_child)
            new_points = _limit_source(new_points, source_particle_child)
            points.extend(new_points)

    # grease pencil
    def get_points(stroke):
        return [point.co.copy() for point in stroke.points]

    def get_splines(gp):
        gpl = gp.layers.active
        if gpl:
            fr = gpl.active_frame
            if not fr:
                current = bpy.context.scene.frame_current
                gpl.frames.new(current)
                gpl.active_frame = current
                fr = gpl.active_frame

            return [get_points(stroke) for stroke in fr.strokes]
        else:
            return []

    if source_pencil > 0:
        gp = bpy.context.scene.grease_pencil
        if gp:
            line_points = []
            line_points = [(p, 'PENCIL') for spline in get_splines(gp)
                             for p in spline]
            if len(line_points) > 0:
                line_points = _limit_source(line_points, source_pencil)

                # Make New point between the line point and the closest point.
                if not points:
                    points.extend(line_points)

                else:
                    for lp in line_points:
                        # Make vector between the line point and its closest point.
                        points.sort(key=lambda p: (p[0] - lp[0]).length_squared)
                        closest_point = points[0]
                        normal = lp[0].xyz - closest_point[0].xyz

                        new_point = (lp[0], lp[1])
                        new_point[0].xyz +=  normal / 2

                        points.append(new_point)
    #print("Found %d points" % len(points))
    return points


def points_to_cells(context, original, original_xyz_minmax, points,
                    source_limit=0,
                    source_noise=0.0,
                    use_smooth_faces=False,
                    use_data_match=False,
                    use_debug_points=False,
                    margin=0.0,
                    material_index=0,
                    use_debug_redraw=False,
                    cell_scale=(1.0, 1.0, 1.0),
                    clean=True):

    from . import cell_calc
    collection = context.collection
    view_layer = context.view_layer

    # apply optional clamp
    if source_limit != 0 and source_limit < len(points):
        points = _limit_source(points, source_limit)

    # saddly we cant be sure there are no doubles
    from mathutils import Vector
    to_tuple = Vector.to_tuple

    # To remove doubles, round the values.
    points = [(Vector(to_tuple(p[0], 4)),p[1]) for p in points]
    del to_tuple
    del Vector

    if source_noise > 0.0:
        from random import random
        # boundbox approx of overall scale
        from mathutils import Vector
        matrix = original.matrix_world.copy()
        bb_world = [matrix @ Vector(v) for v in original.bound_box]
        scalar = source_noise * ((bb_world[0] - bb_world[6]).length / 2.0)

        from mathutils.noise import random_unit_vector
        points[:] = [(p[0] + (random_unit_vector() * (scalar * random())), p[1]) for p in points]

    if use_debug_points:
        bm = bmesh.new()
        for p in points:
            bm.verts.new(p[0])
        mesh_tmp = bpy.data.meshes.new(name="DebugPoints")
        bm.to_mesh(mesh_tmp)
        bm.free()
        obj_tmp = bpy.data.objects.new(name=mesh_tmp.name, object_data=mesh_tmp)
        collection.objects.link(obj_tmp)
        del obj_tmp, mesh_tmp

    cells_verts = cell_calc.points_to_verts(original_xyz_minmax,
                                            points,
                                            cell_scale,
                                            margin_cell=margin)
    # some hacks here :S
    cell_name = original.name + "_cell"
    cells = []
    for center_point, cell_verts in cells_verts:
        # ---------------------------------------------------------------------
        # BMESH
        # create the convex hulls
        bm = bmesh.new()

        # WORKAROUND FOR CONVEX HULL BUG/LIMIT
        # XXX small noise
        import random
        def R():
            return (random.random() - 0.5) * 0.001

        for i, co in enumerate(cell_verts):
            co.x += R()
            co.y += R()
            co.z += R()
            bm_vert = bm.verts.new(co)

        import mathutils
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.005)
        try:
            # Making cell meshes as convex full here!
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
        # smooth faces will remain only inner faces, after appling boolean modifier.
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
            mesh_src = original.data
            for mat in mesh_src.materials:
                mesh_dst.materials.append(mat)
            for lay_attr in ("vertex_colors", "uv_layers"):
                lay_src = getattr(mesh_src, lay_attr)
                lay_dst = getattr(mesh_dst, lay_attr)
                for key in lay_src.keys():
                    lay_dst.new(name=key)

        # ---------------------------------------------------------------------
        # OBJECT
        cell = bpy.data.objects.new(name=cell_name, object_data=mesh_dst)
        collection.objects.link(cell)
        cell.location = center_point
        cells.append(cell)

        # support for object materials
        if use_data_match:
            for i in range(len(mesh_dst.materials)):
                slot_src = original.material_slots[i]
                slot_dst = cell.material_slots[i]

                slot_dst.link = slot_src.link
                slot_dst.material = slot_src.material

        if use_debug_redraw:
            view_layer.update()
            _redraw_yasiamevil()

    view_layer.update()
    # move this elsewhere...
    # Blender 2.8: BGE integration was disabled, --
    # -- because BGE was deleted in Blender 2.8.
    '''
    for cell in cells:
        game = cell.game
        game.physics_type = 'RIGID_BODY'
        game.use_collision_bounds = True
        game.collision_bounds_type = 'CONVEX_HULL'
    '''
    return cells


def cell_boolean(context, original, cells,
                use_debug_bool=False,
                clean=True,
                use_island_split=False,
                use_interior_hide=False,
                use_debug_redraw=False,
                level=0,
                remove_doubles=True
                ):

    cells_boolean = []
    collection = context.collection
    scene = context.scene
    view_layer = context.view_layer

    if use_interior_hide and level == 0:
        # only set for level 0
        original.data.polygons.foreach_set("hide", [False] * len(original.data.polygons))

    # The first object can't be applied by bool, so it is used as a no-effect first straw-man.
    bpy.ops.mesh.primitive_cube_add(enter_editmode=False, location=(original.location.x+10000000000.0, 0, 0))
    temp_cell = bpy.context.active_object
    cells.insert(0, temp_cell)

    bpy.ops.object.select_all(action='DESELECT')
    for i, cell in enumerate(cells):
        mod = cell.modifiers.new(name="Boolean", type='BOOLEAN')
        mod.object = original
        mod.operation = 'INTERSECT'

        if not use_debug_bool:
            if use_interior_hide:
                cell.data.polygons.foreach_set("hide", [True] * len(cell.data.polygons))

            # mesh_old should be made before appling boolean modifier.
            mesh_old = cell.data

            original.select_set(True)
            cell.select_set(True)
            bpy.context.view_layer.objects.active = cell
            bpy.ops.object.modifier_apply(modifier="Boolean")

            if i == 0:
                bpy.data.objects.remove(cell, do_unlink=True)
                continue

            cell = bpy.context.active_object
            cell.select_set(False)

            # depsgraph sould be gotten after applied boolean modifier, for new_mesh.
            depsgraph = context.evaluated_depsgraph_get()
            cell_eval = cell.evaluated_get(depsgraph)

            mesh_new = bpy.data.meshes.new_from_object(cell_eval)
            cell.data = mesh_new

            '''
            check_hide = [11] * len(cell.data.polygons)
            cell.data.polygons.foreach_get("hide", check_hide)
            print(check_hide)
            '''

            # remove if not valid
            if not mesh_old.users:
                bpy.data.meshes.remove(mesh_old)
            if not mesh_new.vertices:
                collection.objects.unlink(cell)
                if not cell.users:
                    bpy.data.objects.remove(cell)
                    cell = None
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

        if cell is not None:
            cells_boolean.append(cell)

            if use_debug_redraw:
                _redraw_yasiamevil()

    bpy.context.view_layer.objects.active = original

    if (not use_debug_bool) and use_island_split:
        # this is ugly and Im not proud of this - campbell
        for ob in view_layer.objects:
            ob.select_set(False)
        for cell in cells_boolean:
            cell.select_set(True)
        # If new separated meshes are made, selected objects is increased.
        if cells_boolean:
            bpy.ops.mesh.separate(type='LOOSE')

        cells_boolean[:] = [cell for cell in scene.objects if cell.select_get()]

    context.view_layer.update()
    return cells_boolean


def interior_handle(cells,
                    use_interior_vgroup=False,
                    use_sharp_edges=False,
                    use_sharp_edges_apply=False,
                    ):
    """Run after doing _all_ booleans"""

    assert(use_interior_vgroup or use_sharp_edges or use_sharp_edges_apply)

    for cell in cells:
        mesh = cell.data
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
            cell.vertex_groups.new(name="Interior")

        if use_sharp_edges:
            bpy.context.space_data.overlay.show_edge_sharp = True

            for bm_edge in bm.edges:
                if len({bm_face.hide for bm_face in bm_edge.link_faces}) == 2:
                    bm_edge.smooth = False

            if use_sharp_edges_apply:
                bpy.context.view_layer.objects.active = cell
                bpy.ops.object.modifier_add(type='EDGE_SPLIT')

                edge_split = bpy.context.object.modifiers[-1]
                edge_split.name = 'EDGE_SPLIT_cell'
                edge_split.use_edge_angle = False

                '''
                edges = [edge for edge in bm.edges if edge.smooth is False]
                if edges:
                    bm.normal_update()
                    bmesh.ops.split_edges(bm, edges=edges)
                '''

        for bm_face in bm.faces:
            bm_face.hide = False

        bm.to_mesh(mesh)
        bm.free()


def post_process(cells,
                use_collection=False,
                new_collection=False,
                collection_name="Fracture",
                use_mass=False,
                mass=1.0,
                mass_mode='VOLUME', mass_name='mass',
                ):

    """Run after Interiro handle"""
    #--------------
    # Collection Options
    if use_collection:
        colle = None
        if not new_collection:
            colle = bpy.data.collections.get(collection_name)

        if colle is None:
            colle = bpy.data.collections.new(collection_name)

        # THe collection should be children of master collection to show in outliner.
        child_names = [m.name for m in bpy.context.scene.collection.children]
        if colle.name not in child_names:
            bpy.context.scene.collection.children.link(colle)

        # Cell objects are only link to the collection.
        bpy.ops.collection.objects_remove_all() # For all selected object.
        for colle_obj in cells:
            colle.objects.link(colle_obj)

    #--------------
    # Mass Options
    if use_mass:
        # Blender 2.8:  Mass for BGE was no more available.--
        # -- Instead, Mass values is used for custom properies on cell objects.
        if mass_mode == 'UNIFORM':
            for cell in cells:
                #cell.game.mass = mass
                cell[mass_name] = mass
        elif mass_mode == 'VOLUME':
            from mathutils import Vector
            def _get_volume(cell):
                def _getObjectBBMinMax():
                    min_co = Vector((1000000.0, 1000000.0, 1000000.0))
                    max_co = -min_co
                    matrix = cell.matrix_world
                    for i in range(0, 8):
                        bb_vec = cell.matrix_world @ Vector(cell.bound_box[i])
                        min_co[0] = min(bb_vec[0], min_co[0])
                        min_co[1] = min(bb_vec[1], min_co[1])
                        min_co[2] = min(bb_vec[2], min_co[2])
                        max_co[0] = max(bb_vec[0], max_co[0])
                        max_co[1] = max(bb_vec[1], max_co[1])
                        max_co[2] = max(bb_vec[2], max_co[2])
                    return (min_co, max_co)

                def _getObjectVolume():
                    min_co, max_co = _getObjectBBMinMax()
                    x = max_co[0] - min_co[0]
                    y = max_co[1] - min_co[1]
                    z = max_co[2] - min_co[2]
                    volume = x * y * z
                    return volume

                return _getObjectVolume()

            cell_volume_ls = [_get_volume(cell) for cell in cells]
            cell_volume_tot = sum(cell_volume_ls)
            if cell_volume_tot > 0.0:
                mass_fac = mass / cell_volume_tot
                for i, cell in enumerate(cells):
                    cell[mass_name] = cell_volume_ls[i] * mass_fac
        else:
            assert(0)
