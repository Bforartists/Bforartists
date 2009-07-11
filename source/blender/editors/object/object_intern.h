/**
 * $Id:
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. 
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */
#ifndef ED_OBJECT_INTERN_H
#define ED_OBJECT_INTERN_H

struct wmOperatorType;
struct KeyBlock;
struct Lattice;
struct Curve;
struct Object;
struct Mesh;

/* internal exports only */


/* object_edit.c */
void OBJECT_OT_editmode_toggle(struct wmOperatorType *ot);
void OBJECT_OT_parent_set(struct wmOperatorType *ot);
void OBJECT_OT_parent_clear(struct wmOperatorType *ot);
void OBJECT_OT_track_set(struct wmOperatorType *ot);
void OBJECT_OT_track_clear(struct wmOperatorType *ot);
void OBJECT_OT_select_all_toggle(struct wmOperatorType *ot);
void OBJECT_OT_select_inverse(struct wmOperatorType *ot);
void OBJECT_OT_select_random(struct wmOperatorType *ot);
void OBJECT_OT_select_by_type(struct wmOperatorType *ot);
void OBJECT_OT_select_by_layer(struct wmOperatorType *ot);
void OBJECT_OT_select_linked(struct wmOperatorType *ot);
void OBJECT_OT_select_grouped(struct wmOperatorType *ot);
void OBJECT_OT_location_clear(struct wmOperatorType *ot);
void OBJECT_OT_rotation_clear(struct wmOperatorType *ot);
void OBJECT_OT_scale_clear(struct wmOperatorType *ot);
void OBJECT_OT_origin_clear(struct wmOperatorType *ot);
void OBJECT_OT_restrictview_set(struct wmOperatorType *ot);
void OBJECT_OT_restrictview_clear(struct wmOperatorType *ot);
void OBJECT_OT_slowparent_set(struct wmOperatorType *ot);
void OBJECT_OT_slowparent_clear(struct wmOperatorType *ot);
void OBJECT_OT_center_set(struct wmOperatorType *ot);
void OBJECT_OT_duplicates_make_real(struct wmOperatorType *ot);
void OBJECT_OT_object_add(struct wmOperatorType *ot);
void OBJECT_OT_duplicate(struct wmOperatorType *ot);
void OBJECT_OT_delete(struct wmOperatorType *ot);

void OBJECT_OT_mesh_add(struct wmOperatorType *ot);
void OBJECT_OT_curve_add(struct wmOperatorType *ot);
void OBJECT_OT_surface_add(struct wmOperatorType *ot);
void OBJECT_OT_text_add(struct wmOperatorType *ot);
void OBJECT_OT_armature_add(struct wmOperatorType *ot);
	/* only used as menu */
void OBJECT_OT_primitive_add(struct wmOperatorType *ot);

/* editlattice.c */
void free_editLatt(Object *ob);
void make_editLatt(Object *obedit);
void load_editLatt(Object *obedit);
void remake_editLatt(Object *obedit);

void LATTICE_OT_select_all_toggle(struct wmOperatorType *ot);
void LATTICE_OT_make_regular(struct wmOperatorType *ot);

/* editgroup.c */
void GROUP_OT_group_create(struct wmOperatorType *ot);
void GROUP_OT_objects_remove(struct wmOperatorType *ot);
void GROUP_OT_objects_add_active(struct wmOperatorType *ot);
void GROUP_OT_objects_remove_active(struct wmOperatorType *ot);

/* object_modifier.c */
void OBJECT_OT_modifier_add(struct wmOperatorType *ot);
void OBJECT_OT_modifier_remove(struct wmOperatorType *ot);
void OBJECT_OT_modifier_move_up(struct wmOperatorType *ot);
void OBJECT_OT_modifier_move_down(struct wmOperatorType *ot);
void OBJECT_OT_modifier_apply(struct wmOperatorType *ot);
void OBJECT_OT_modifier_convert(struct wmOperatorType *ot);
void OBJECT_OT_modifier_copy(struct wmOperatorType *ot);
void OBJECT_OT_multires_subdivide(struct wmOperatorType *ot);
void OBJECT_OT_modifier_mdef_bind(struct wmOperatorType *ot);

/* editconstraint.c */
void OBJECT_OT_constraint_add(struct wmOperatorType *ot);

/* object_vgroup.c */
void OBJECT_OT_vertex_group_add(struct wmOperatorType *ot);
void OBJECT_OT_vertex_group_remove(struct wmOperatorType *ot);
void OBJECT_OT_vertex_group_assign(struct wmOperatorType *ot);
void OBJECT_OT_vertex_group_remove_from(struct wmOperatorType *ot);
void OBJECT_OT_vertex_group_select(struct wmOperatorType *ot);
void OBJECT_OT_vertex_group_deselect(struct wmOperatorType *ot);
void OBJECT_OT_vertex_group_copy_to_linked(struct wmOperatorType *ot);
void OBJECT_OT_vertex_group_copy(struct wmOperatorType *ot);

/* editkey.c */
void OBJECT_OT_shape_key_add(struct wmOperatorType *ot);
void OBJECT_OT_shape_key_remove(struct wmOperatorType *ot);

#endif /* ED_OBJECT_INTERN_H */

