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

#include <stdlib.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"
#include "ED_object.h"

#include "object_intern.h"


/* ************************** registration **********************************/


void ED_operatortypes_object(void)
{
	WM_operatortype_append(OBJECT_OT_editmode_toggle);
	WM_operatortype_append(OBJECT_OT_posemode_toggle);
	WM_operatortype_append(OBJECT_OT_parent_set);
	WM_operatortype_append(OBJECT_OT_parent_clear);
	WM_operatortype_append(OBJECT_OT_track_set);
	WM_operatortype_append(OBJECT_OT_track_clear);
	WM_operatortype_append(OBJECT_OT_select_inverse);
	WM_operatortype_append(OBJECT_OT_select_random);
	WM_operatortype_append(OBJECT_OT_select_all_toggle);
	WM_operatortype_append(OBJECT_OT_select_by_type);
	WM_operatortype_append(OBJECT_OT_select_by_layer);
	WM_operatortype_append(OBJECT_OT_select_linked);
	WM_operatortype_append(OBJECT_OT_select_grouped);
	WM_operatortype_append(OBJECT_OT_location_clear);
	WM_operatortype_append(OBJECT_OT_rotation_clear);
	WM_operatortype_append(OBJECT_OT_scale_clear);
	WM_operatortype_append(OBJECT_OT_origin_clear);
	WM_operatortype_append(OBJECT_OT_restrictview_clear);
	WM_operatortype_append(OBJECT_OT_restrictview_set);
	WM_operatortype_append(OBJECT_OT_slowparent_set);
	WM_operatortype_append(OBJECT_OT_slowparent_clear);
	WM_operatortype_append(OBJECT_OT_center_set);
	WM_operatortype_append(OBJECT_OT_duplicates_make_real);
	WM_operatortype_append(OBJECT_OT_duplicate);
	WM_operatortype_append(OBJECT_OT_join);
	WM_operatortype_append(OBJECT_OT_proxy_make);
	WM_operatortype_append(OBJECT_OT_shade_smooth);
	WM_operatortype_append(OBJECT_OT_shade_flat);
	WM_operatortype_append(GROUP_OT_group_create);
	WM_operatortype_append(GROUP_OT_objects_remove);
	WM_operatortype_append(GROUP_OT_objects_add_active);
	WM_operatortype_append(GROUP_OT_objects_remove_active);

	WM_operatortype_append(OBJECT_OT_delete);
	WM_operatortype_append(OBJECT_OT_mesh_add);
	WM_operatortype_append(OBJECT_OT_curve_add);
	WM_operatortype_append(OBJECT_OT_text_add);
	WM_operatortype_append(OBJECT_OT_surface_add);
	WM_operatortype_append(OBJECT_OT_armature_add);
	WM_operatortype_append(OBJECT_OT_object_add);
	WM_operatortype_append(OBJECT_OT_primitive_add);

	WM_operatortype_append(OBJECT_OT_modifier_add);
	WM_operatortype_append(OBJECT_OT_modifier_remove);
	WM_operatortype_append(OBJECT_OT_modifier_move_up);
	WM_operatortype_append(OBJECT_OT_modifier_move_down);
	WM_operatortype_append(OBJECT_OT_modifier_apply);
	WM_operatortype_append(OBJECT_OT_modifier_convert);
	WM_operatortype_append(OBJECT_OT_modifier_copy);
	WM_operatortype_append(OBJECT_OT_multires_subdivide);
	WM_operatortype_append(OBJECT_OT_modifier_mdef_bind);

	WM_operatortype_append(OBJECT_OT_constraint_add);
	WM_operatortype_append(OBJECT_OT_constraint_add_with_targets);
	WM_operatortype_append(POSE_OT_constraint_add);
	WM_operatortype_append(POSE_OT_constraint_add_with_targets);
	WM_operatortype_append(OBJECT_OT_constraints_clear);
	WM_operatortype_append(POSE_OT_constraints_clear);
	WM_operatortype_append(POSE_OT_ik_add);
	WM_operatortype_append(POSE_OT_ik_clear);
	WM_operatortype_append(CONSTRAINT_OT_delete);
	WM_operatortype_append(CONSTRAINT_OT_move_up);
	WM_operatortype_append(CONSTRAINT_OT_move_down);
	WM_operatortype_append(CONSTRAINT_OT_stretchto_reset);
	WM_operatortype_append(CONSTRAINT_OT_limitdistance_reset);
	WM_operatortype_append(CONSTRAINT_OT_childof_set_inverse);
	WM_operatortype_append(CONSTRAINT_OT_childof_clear_inverse);

	WM_operatortype_append(OBJECT_OT_vertex_group_add);
	WM_operatortype_append(OBJECT_OT_vertex_group_remove);
	WM_operatortype_append(OBJECT_OT_vertex_group_assign);
	WM_operatortype_append(OBJECT_OT_vertex_group_remove_from);
	WM_operatortype_append(OBJECT_OT_vertex_group_select);
	WM_operatortype_append(OBJECT_OT_vertex_group_deselect);
	WM_operatortype_append(OBJECT_OT_vertex_group_copy_to_linked);
	WM_operatortype_append(OBJECT_OT_vertex_group_copy);

	WM_operatortype_append(OBJECT_OT_shape_key_add);
	WM_operatortype_append(OBJECT_OT_shape_key_remove);

	WM_operatortype_append(LATTICE_OT_select_all_toggle);
	WM_operatortype_append(LATTICE_OT_make_regular);
}

void ED_keymap_object(wmWindowManager *wm)
{
	ListBase *keymap= WM_keymap_listbase(wm, "Object Non-modal", 0, 0);
	
	/* Note: this keymap works disregarding mode */
	WM_keymap_add_item(keymap, "OBJECT_OT_editmode_toggle", TABKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_posemode_toggle", TABKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_center_set", CKEY, KM_PRESS, KM_ALT|KM_SHIFT|KM_CTRL, 0);

	/* Note: this keymap gets disabled in non-objectmode,  */
	keymap= WM_keymap_listbase(wm, "Object Mode", 0, 0);
	
	WM_keymap_add_item(keymap, "OBJECT_OT_select_all_toggle", AKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_select_inverse", IKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_select_linked", LKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_select_grouped", GKEY, KM_PRESS, KM_SHIFT, 0);
	
	WM_keymap_verify_item(keymap, "OBJECT_OT_parent_set", PKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_parent_clear", PKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_track_set", TKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_track_clear", TKEY, KM_PRESS, KM_ALT, 0);
	
	WM_keymap_verify_item(keymap, "OBJECT_OT_constraint_add_with_targets", CKEY, KM_PRESS, KM_CTRL|KM_SHIFT, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_constraints_clear", CKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	
	WM_keymap_verify_item(keymap, "OBJECT_OT_location_clear", GKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_rotation_clear", RKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_scale_clear", SKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_origin_clear", OKEY, KM_PRESS, KM_ALT, 0);
	
	WM_keymap_add_item(keymap, "OBJECT_OT_restrictview_clear", HKEY, KM_PRESS, KM_ALT, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_restrictview_set", HKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "OBJECT_OT_restrictview_set", HKEY, KM_PRESS, KM_SHIFT, 0)->ptr, "unselected", 1);
	
	WM_keymap_verify_item(keymap, "OBJECT_OT_delete", XKEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "OBJECT_OT_primitive_add", AKEY, KM_PRESS, KM_SHIFT, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_duplicate", DKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_boolean_set(WM_keymap_add_item(keymap, "OBJECT_OT_duplicate", DKEY, KM_PRESS, KM_ALT, 0)->ptr, "linked", 1);
	WM_keymap_add_item(keymap, "OBJECT_OT_join", JKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "OBJECT_OT_proxy_make", PKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	
	// XXX this should probably be in screen instead... here for testing purposes in the meantime... - Aligorith
	WM_keymap_verify_item(keymap, "ANIM_OT_insert_keyframe_menu", IKEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "ANIM_OT_delete_keyframe_v3d", IKEY, KM_PRESS, KM_ALT, 0);
	
	WM_keymap_verify_item(keymap, "GROUP_OT_group_create", GKEY, KM_PRESS, KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "GROUP_OT_objects_remove", GKEY, KM_PRESS, KM_CTRL|KM_ALT, 0);
	WM_keymap_verify_item(keymap, "GROUP_OT_objects_add_active", GKEY, KM_PRESS, KM_SHIFT|KM_CTRL, 0);
	WM_keymap_verify_item(keymap, "GROUP_OT_objects_remove_active", GKEY, KM_PRESS, KM_SHIFT|KM_ALT, 0);

	/* Lattice */
	keymap= WM_keymap_listbase(wm, "Lattice", 0, 0);

	WM_keymap_add_item(keymap, "LATTICE_OT_select_all_toggle", AKEY, KM_PRESS, 0, 0);
}

