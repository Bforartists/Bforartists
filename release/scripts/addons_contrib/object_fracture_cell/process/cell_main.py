if "bpy" in locals():
    import importlib
    importlib.reload(cell_functions)

else:
    from . import cell_functions

import bpy


def main_object(context, original, level, **kw):
    import random

    # pull out some args
    kw_copy = kw.copy()
    source_vert_own = kw_copy.pop("source_vert_own")
    source_vert_child = kw_copy.pop("source_vert_child")
    source_particle_own = kw_copy.pop("source_particle_own")
    source_particle_child = kw_copy.pop("source_particle_child")
    source_pencil = kw_copy.pop("source_pencil")
    source_random = kw_copy.pop("source_random")
    
    use_recenter = kw_copy.pop("use_recenter")
    recursion = kw_copy.pop("recursion")
    recursion_source_limit = kw_copy.pop("recursion_source_limit")
    recursion_clamp = kw_copy.pop("recursion_clamp")
    recursion_chance = kw_copy.pop("recursion_chance")
    recursion_chance_select = kw_copy.pop("recursion_chance_select")
    use_island_split = kw_copy.pop("use_island_split")
    use_debug_bool = kw_copy.pop("use_debug_bool")
    use_interior_vgroup = kw_copy.pop("use_interior_vgroup")
    use_sharp_edges = kw_copy.pop("use_sharp_edges")
    use_sharp_edges_apply = kw_copy.pop("use_sharp_edges_apply")

    cell_relocate = kw_copy.pop("cell_relocate")

    collection = context.collection
    scene = context.scene

    if level != 0:
        kw_copy["source_limit"] = recursion_source_limit

    from . import cell_functions

    # not essential but selection is visual distraction.
    original.select_set(False)

    if kw_copy["use_debug_redraw"]:
        original_display_type_prev = original.display_type
        original.display_type = 'WIRE'
    
    original_mesh = original.data
    original_matrix = original.matrix_world.copy()
    original_verts = [original_matrix @ v.co for v in original_mesh.vertices]    
    original_xyz_minmax = cell_functions.original_minmax(original_verts)
    
    cells = []
    points = cell_functions.points_from_object(original, original_xyz_minmax,
                                               source_vert_own=source_vert_own,
                                               source_vert_child=source_vert_child,
                                               source_particle_own=source_particle_own,
                                               source_particle_child=source_particle_child,
                                               source_pencil=source_pencil,
                                               source_random=source_random)        

    cells = cell_functions.points_to_cells(context, original, original_xyz_minmax, points, **kw_copy)        
    cells = cell_functions.cell_boolean(context, original, cells,
                                        use_island_split=use_island_split,
                                        use_interior_hide=(use_interior_vgroup or use_sharp_edges),
                                        use_debug_bool=use_debug_bool,
                                        use_debug_redraw=kw_copy["use_debug_redraw"],
                                        level=level,
                                        )

    # must apply after boolean.
    if use_recenter:
        bpy.ops.object.origin_set({"selected_editable_objects": cells},
                                  type='ORIGIN_GEOMETRY', center='MEDIAN')
                                  
    #--------------
    # Recursion.
    if level == 0:
        for level_sub in range(1, recursion + 1):

            objects_recurse_input = [(i, o) for i, o in enumerate(cells)]
            if recursion_chance != 1.0:
                from mathutils import Vector
                if recursion_chance_select == 'RANDOM':
                    random.shuffle(objects_recurse_input)
                elif recursion_chance_select in {'SIZE_MIN', 'SIZE_MAX'}:
                    objects_recurse_input.sort(key=lambda ob_pair:
                        (Vector(ob_pair[1].bound_box[0]) -
                         Vector(ob_pair[1].bound_box[6])).length_squared)
                    if recursion_chance_select == 'SIZE_MAX':
                        objects_recurse_input.reverse()
                elif recursion_chance_select in {'CURSOR_MIN', 'CURSOR_MAX'}:
                    c = scene.cursor.location.copy()
                    objects_recurse_input.sort(key=lambda ob_pair:
                        (ob_pair[1].location - c).length_squared)
                    if recursion_chance_select == 'CURSOR_MAX':
                        objects_recurse_input.reverse()
            
                objects_recurse_input[int(recursion_chance * len(objects_recurse_input)):] = []
                objects_recurse_input.sort()
            
            # reverse index values so we can remove from original list.
            objects_recurse_input.reverse()

            objects_recursive = []
            for i, obj_cell in objects_recurse_input:
                assert(cells[i] is obj_cell)
                # Repeat main_object() here.
                objects_recursive += main_object(context, obj_cell, level_sub, **kw)
                #if original_remove:
                collection.objects.unlink(obj_cell)
                del cells[i]
                if recursion_clamp and len(cells) + len(objects_recursive) >= recursion_clamp:
                    break
            cells.extend(objects_recursive)

            if recursion_clamp and len(cells) > recursion_clamp:
                break
    
    #--------------
    # Level Options
    if level == 0:
        # import pdb; pdb.set_trace()
        if use_interior_vgroup or use_sharp_edges:
            cell_functions.interior_handle(cells,
                                           use_interior_vgroup=use_interior_vgroup,
                                           use_sharp_edges=use_sharp_edges,
                                           use_sharp_edges_apply=use_sharp_edges_apply,
                                           )
    
    if cell_relocate:
        for cell in cells:
            cell.location.x += (original_xyz_minmax["x"][1] - original_xyz_minmax["x"][0]) + 1
    
    if kw_copy["use_debug_redraw"]:
        original.display_type = original_display_type_prev
    
    return cells

            
def main(context, original, **kw):
    '''
    import time
    t = time.time()
    '''    

    kw_copy = kw.copy()
    
    # Pre_Simplify
    pre_simplify = kw_copy.pop("pre_simplify")
    # collection
    use_collection = kw_copy.pop("use_collection")
    new_collection = kw_copy.pop("new_collection")
    collection_name = kw_copy.pop("collection_name")
    # object visibility
    original_hide = kw_copy.pop("original_hide")    
    # mass
    use_mass = kw_copy.pop("use_mass")
    mass_name = kw_copy.pop("mass_name")
    mass_mode = kw_copy.pop("mass_mode")
    mass = kw_copy.pop("mass")
    
    cells = []
    
    if original.type == 'MESH':
        if pre_simplify > 0.0:
            cell_functions.simplify_original(original=original, pre_simplify=pre_simplify)
        
        cells += main_object(context, original, 0, **kw_copy)
        
        if pre_simplify > 0.0:
            cell_functions.desimplify_original(original=original)
    else:
        assert obj.type == 'MESH', "No MESH object selected."

    bpy.ops.object.select_all(action='DESELECT')
    
    for cell in cells:
        cell.select_set(True)
    
    cell_functions.post_process(cells,
                                use_collection=use_collection,
                                new_collection=new_collection,
                                collection_name=collection_name,
                                use_mass=use_mass,
                                mass=mass,
                                mass_mode=mass_mode,
                                mass_name=mass_name,
                                )          

    # To avoid select both original object and cells in EDIT mode.
    bpy.context.view_layer.objects.active = cells[0]
    
    # de-hide all objects and meshes.
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.reveal()    
    bpy.ops.object.mode_set(mode='OBJECT')
        
    if original_hide:
        original.hide_set(True)

    #print("Done! %d objects in %.4f sec" % (len(cells), time.time() - t))
    #print("Done!")    
    return (original, cells)