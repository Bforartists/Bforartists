
def _cell_props_to_dict(fracture_cell_props):
    cell_keywords = {        
        'source_vert_own': fracture_cell_props.source_vert_own,
        'source_vert_child': fracture_cell_props.source_vert_child,
        'source_particle_own': fracture_cell_props.source_particle_own,
        'source_particle_child': fracture_cell_props.source_particle_child,
        'source_pencil': fracture_cell_props.source_pencil,
        'source_random': fracture_cell_props.source_random,
        'source_noise': fracture_cell_props.source_noise,
        'margin': fracture_cell_props.margin,
        'cell_scale': fracture_cell_props.cell_scale,
        'pre_simplify': fracture_cell_props.pre_simplify,
        'use_recenter': fracture_cell_props.use_recenter,
        'use_island_split': fracture_cell_props.use_island_split,
        'recursion': fracture_cell_props.recursion,
        'recursion_source_limit': fracture_cell_props.recursion_source_limit,
        'recursion_clamp': fracture_cell_props.recursion_clamp,
        'recursion_chance': fracture_cell_props.recursion_chance,
        'recursion_chance_select': fracture_cell_props.recursion_chance_select,
        'use_smooth_faces': fracture_cell_props.use_smooth_faces,
        'use_sharp_edges': fracture_cell_props.use_sharp_edges,
        'use_sharp_edges_apply': fracture_cell_props.use_sharp_edges_apply,
        'use_data_match': fracture_cell_props.use_data_match,
        'material_index': fracture_cell_props.material_index,
        'use_interior_vgroup': fracture_cell_props.use_interior_vgroup,
        
        'use_collection': fracture_cell_props.use_collection,
        'new_collection': fracture_cell_props.new_collection,
        'collection_name': fracture_cell_props.collection_name,
        'original_hide': fracture_cell_props.original_hide,
        'cell_relocate': fracture_cell_props.cell_relocate,
        'use_mass': fracture_cell_props.use_mass,
        'mass_name': fracture_cell_props.mass_name,
        'mass_mode': fracture_cell_props.mass_mode,
        'mass': fracture_cell_props.mass,
        
        'use_debug_points': fracture_cell_props.use_debug_points,
        'use_debug_redraw': fracture_cell_props.use_debug_redraw,
        'use_debug_bool': fracture_cell_props.use_debug_bool   
    }
    return cell_keywords
