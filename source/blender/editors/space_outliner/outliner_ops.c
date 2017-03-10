/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * 
 * Contributor(s): Blender Foundation
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_outliner/outliner_ops.c
 *  \ingroup spoutliner
 */

#include "BKE_context.h"

#include "BLI_listbase.h"
#include "BLI_math.h"

#include "ED_screen.h"

#include "MEM_guardedalloc.h"

#include "RNA_access.h"

#include "UI_interface.h"
#include "UI_view2d.h"

#include "WM_api.h"
#include "WM_types.h"

#include "outliner_intern.h"


enum {
	OUTLINER_ITEM_DRAG_CANCEL,
	OUTLINER_ITEM_DRAG_CONFIRM,
};

static int outliner_item_drag_drop_poll(bContext *C)
{
	SpaceOops *soops = CTX_wm_space_outliner(C);
	return ED_operator_outliner_active(C) &&
	       /* Only collection display modes supported for now. Others need more design work */
	       ELEM(soops->outlinevis, SO_ACT_LAYER, SO_COLLECTIONS);
}

static TreeElement *outliner_item_drag_element_find(SpaceOops *soops, ARegion *ar, const wmEvent *event)
{
	/* note: using EVT_TWEAK_ events to trigger dragging is fine,
	 * it sends coordinates from where dragging was started */
	const float my = UI_view2d_region_to_view_y(&ar->v2d, event->mval[1]);
	return outliner_find_item_at_y(soops, &soops->tree, my);
}

static void outliner_item_drag_end(TreeElement *dragged_te)
{
	MEM_SAFE_FREE(dragged_te->drag_data);
}

static void outliner_item_drag_get_insert_data(
        const SpaceOops *soops, ARegion *ar, const wmEvent *event, TreeElement *te_dragged,
        TreeElement **r_te_insert_handle, TreeElementInsertType *r_insert_type)
{
	TreeElement *te_hovered;
	float view_mval[2];

	UI_view2d_region_to_view(&ar->v2d, event->mval[0], event->mval[1], &view_mval[0], &view_mval[1]);
	te_hovered = outliner_find_item_at_y(soops, &soops->tree, view_mval[1]);

	if (te_hovered) {
		/* mouse hovers an element (ignoring x-axis), now find out how to insert the dragged item exactly */

		if (te_hovered == te_dragged) {
			*r_te_insert_handle = te_dragged;
		}
		else if (te_hovered != te_dragged) {
			const float margin = UI_UNIT_Y * (1.0f / 4);

			*r_te_insert_handle = te_hovered;
			if (view_mval[1] < (te_hovered->ys + margin)) {
				if (TSELEM_OPEN(TREESTORE(te_hovered), soops)) {
					/* inserting after a open item means we insert into it, but as first child */
					if (BLI_listbase_is_empty(&te_hovered->subtree)) {
						*r_insert_type = TE_INSERT_INTO;
					}
					else {
						*r_insert_type = TE_INSERT_BEFORE;
						*r_te_insert_handle = te_hovered->subtree.first;
					}
				}
				else {
					*r_insert_type = TE_INSERT_AFTER;
				}
			}
			else if (view_mval[1] > (te_hovered->ys + (3 * margin))) {
				*r_insert_type = TE_INSERT_BEFORE;
			}
			else {
				*r_insert_type = TE_INSERT_INTO;
			}
		}
	}
	else {
		/* mouse doesn't hover any item (ignoring x-axis), so it's either above list bounds or below. */

		TreeElement *first = soops->tree.first;
		TreeElement *last = soops->tree.last;

		if (view_mval[1] < last->ys) {
			*r_te_insert_handle = last;
			*r_insert_type = TE_INSERT_AFTER;
		}
		else if (view_mval[1] > (first->ys + UI_UNIT_Y)) {
			*r_te_insert_handle = first;
			*r_insert_type = TE_INSERT_BEFORE;
		}
		else {
			BLI_assert(0);
		}
	}
}

static void outliner_item_drag_handle(
        const Scene *scene, SpaceOops *soops, ARegion *ar, const wmEvent *event, TreeElement *te_dragged)
{
	TreeElement *te_insert_handle;
	TreeElementInsertType insert_type;

	outliner_item_drag_get_insert_data(soops, ar, event, te_dragged, &te_insert_handle, &insert_type);

	if (!te_dragged->reinsert_poll &&
	    /* there is no reinsert_poll, so we do some generic checks (same types and reinsert callback is available) */
	    (TREESTORE(te_dragged)->type == TREESTORE(te_insert_handle)->type) &&
	    te_dragged->reinsert)
	{
		/* pass */
	}
	else if (te_dragged == te_insert_handle) {
		/* nothing will happen anyway, no need to do poll check */
	}
	else if (!te_dragged->reinsert_poll ||
	         !te_dragged->reinsert_poll(scene, te_dragged, &te_insert_handle, &insert_type))
	{
		te_insert_handle = NULL;
	}
	te_dragged->drag_data->insert_type = insert_type;
	te_dragged->drag_data->insert_handle = te_insert_handle;
}

static bool outliner_item_drag_drop_apply(const Scene *scene, TreeElement *dragged_te)
{
	TreeElement *insert_handle = dragged_te->drag_data->insert_handle;
	TreeElementInsertType insert_type = dragged_te->drag_data->insert_type;

	if ((insert_handle == dragged_te) || !insert_handle) {
		/* No need to do anything */
	}
	else if (dragged_te->reinsert) {
		BLI_assert(!dragged_te->reinsert_poll || dragged_te->reinsert_poll(scene, dragged_te, &insert_handle,
		                                                                   &insert_type));
		/* call of assert above should not have changed insert_handle and insert_type at this point */
		BLI_assert(dragged_te->drag_data->insert_handle == insert_handle &&
		           dragged_te->drag_data->insert_type == insert_type);
		dragged_te->reinsert(scene, dragged_te, insert_handle, insert_type);
		return true;
	}

	return false;
}

static int outliner_item_drag_drop_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
	Scene *scene = CTX_data_scene(C);
	ARegion *ar = CTX_wm_region(C);
	SpaceOops *soops = CTX_wm_space_outliner(C);
	TreeElement *te_dragged = op->customdata;
	int retval = OPERATOR_RUNNING_MODAL;
	bool redraw = false;
	bool skip_rebuild = true;

	switch (event->type) {
		case EVT_MODAL_MAP:
			if (event->val == OUTLINER_ITEM_DRAG_CONFIRM) {
				if (outliner_item_drag_drop_apply(scene, te_dragged)) {
					skip_rebuild = false;
				}
				retval = OPERATOR_FINISHED;
			}
			else if (event->val == OUTLINER_ITEM_DRAG_CANCEL) {
				retval = OPERATOR_CANCELLED;
			}
			else {
				BLI_assert(0);
			}
			WM_event_add_mousemove(C); /* update highlight */
			outliner_item_drag_end(te_dragged);
			redraw = true;
			break;
		case MOUSEMOVE:
			outliner_item_drag_handle(scene, soops, ar, event, te_dragged);
			redraw = true;
			break;
	}

	if (skip_rebuild) {
		soops->storeflag |= SO_TREESTORE_REDRAW; /* only needs to redraw, no rebuild */
	}
	if (redraw) {
		ED_region_tag_redraw(ar);
	}

	return retval;
}

static int outliner_item_drag_drop_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	ARegion *ar = CTX_wm_region(C);
	SpaceOops *soops = CTX_wm_space_outliner(C);
	TreeElement *te_dragged = outliner_item_drag_element_find(soops, ar, event);

	if (!te_dragged) {
		return (OPERATOR_FINISHED | OPERATOR_PASS_THROUGH);
	}

	op->customdata = te_dragged;
	te_dragged->drag_data = MEM_callocN(sizeof(*te_dragged->drag_data), __func__);
	/* by default we don't change the item position */
	te_dragged->drag_data->insert_handle = te_dragged;
	/* unset highlighted tree element, dragged one will be highlighted instead */
	outliner_set_flag(&soops->tree, TSE_HIGHLIGHTED, false);

	soops->storeflag |= SO_TREESTORE_REDRAW; /* only needs to redraw, no rebuild */
	ED_region_tag_redraw(ar);

	WM_event_add_modal_handler(C, op);

	return OPERATOR_RUNNING_MODAL;
}

/**
 * Notes about Outliner Item Drag 'n Drop:
 * Right now only collections display mode is supported. But ideally all/most modes would support this. There are
 * just some open design questions that have to be answered: do we want to allow mixing order of different data types
 * (like render-layers and objects)? Would that be a purely visual change or would that have any other effect? ...
 */
static void OUTLINER_OT_item_drag_drop(wmOperatorType *ot)
{
	ot->name = "Drag and Drop Item";
	ot->idname = "OUTLINER_OT_item_drag_drop";
	ot->description = "Change the hierarchical position of an item by repositioning it using drag and drop";

	ot->invoke = outliner_item_drag_drop_invoke;
	ot->modal = outliner_item_drag_drop_modal;

	ot->poll = outliner_item_drag_drop_poll;

	ot->flag = OPTYPE_UNDO;
}


/* ************************** registration **********************************/

void outliner_operatortypes(void)
{
	WM_operatortype_append(OUTLINER_OT_highlight_update);
	WM_operatortype_append(OUTLINER_OT_item_activate);
	WM_operatortype_append(OUTLINER_OT_select_border);
	WM_operatortype_append(OUTLINER_OT_item_openclose);
	WM_operatortype_append(OUTLINER_OT_item_rename);
	WM_operatortype_append(OUTLINER_OT_item_drag_drop);
	WM_operatortype_append(OUTLINER_OT_operation);
	WM_operatortype_append(OUTLINER_OT_scene_operation);
	WM_operatortype_append(OUTLINER_OT_object_operation);
	WM_operatortype_append(OUTLINER_OT_group_operation);
	WM_operatortype_append(OUTLINER_OT_lib_operation);
	WM_operatortype_append(OUTLINER_OT_lib_relocate);
	WM_operatortype_append(OUTLINER_OT_id_operation);
	WM_operatortype_append(OUTLINER_OT_id_delete);
	WM_operatortype_append(OUTLINER_OT_id_remap);
	WM_operatortype_append(OUTLINER_OT_data_operation);
	WM_operatortype_append(OUTLINER_OT_animdata_operation);
	WM_operatortype_append(OUTLINER_OT_action_set);
	WM_operatortype_append(OUTLINER_OT_constraint_operation);
	WM_operatortype_append(OUTLINER_OT_modifier_operation);
	WM_operatortype_append(OUTLINER_OT_collection_operation);

	WM_operatortype_append(OUTLINER_OT_show_one_level);
	WM_operatortype_append(OUTLINER_OT_show_active);
	WM_operatortype_append(OUTLINER_OT_show_hierarchy);
	WM_operatortype_append(OUTLINER_OT_scroll_page);
	
	WM_operatortype_append(OUTLINER_OT_selected_toggle);
	WM_operatortype_append(OUTLINER_OT_expanded_toggle);
	
	WM_operatortype_append(OUTLINER_OT_keyingset_add_selected);
	WM_operatortype_append(OUTLINER_OT_keyingset_remove_selected);
	
	WM_operatortype_append(OUTLINER_OT_drivers_add_selected);
	WM_operatortype_append(OUTLINER_OT_drivers_delete_selected);
	
	WM_operatortype_append(OUTLINER_OT_orphans_purge);

	WM_operatortype_append(OUTLINER_OT_parent_drop);
	WM_operatortype_append(OUTLINER_OT_parent_clear);
	WM_operatortype_append(OUTLINER_OT_scene_drop);
	WM_operatortype_append(OUTLINER_OT_material_drop);
	WM_operatortype_append(OUTLINER_OT_group_link);

	/* collections */
	WM_operatortype_append(OUTLINER_OT_collections_delete);
	WM_operatortype_append(OUTLINER_OT_collection_select);
	WM_operatortype_append(OUTLINER_OT_collection_link);
	WM_operatortype_append(OUTLINER_OT_collection_unlink);
	WM_operatortype_append(OUTLINER_OT_collection_new);
	WM_operatortype_append(OUTLINER_OT_collection_override_new);
	WM_operatortype_append(OUTLINER_OT_collection_objects_add);
	WM_operatortype_append(OUTLINER_OT_collection_objects_remove);
	WM_operatortype_append(OUTLINER_OT_collection_objects_select);
	WM_operatortype_append(OUTLINER_OT_collection_objects_deselect);
}

static wmKeyMap *outliner_item_drag_drop_modal_keymap(wmKeyConfig *keyconf)
{
	static EnumPropertyItem modal_items[] = {
		{OUTLINER_ITEM_DRAG_CANCEL,  "CANCEL",  0, "Cancel", ""},
		{OUTLINER_ITEM_DRAG_CONFIRM, "CONFIRM", 0, "Confirm/Drop", ""},
		{0, NULL, 0, NULL, NULL}
	};
	const char *map_name = "Outliner Item Drap 'n Drop Modal Map";

	wmKeyMap *keymap = WM_modalkeymap_get(keyconf, map_name);

	/* this function is called for each spacetype, only needs to add map once */
	if (keymap && keymap->modal_items)
		return NULL;

	keymap = WM_modalkeymap_add(keyconf, map_name, modal_items);

	/* items for modal map */
	WM_modalkeymap_add_item(keymap, ESCKEY, KM_PRESS, KM_ANY, 0, OUTLINER_ITEM_DRAG_CANCEL);
	WM_modalkeymap_add_item(keymap, RIGHTMOUSE, KM_PRESS, KM_ANY, 0, OUTLINER_ITEM_DRAG_CANCEL);

	WM_modalkeymap_add_item(keymap, LEFTMOUSE, KM_RELEASE, KM_ANY, 0, OUTLINER_ITEM_DRAG_CONFIRM);
	WM_modalkeymap_add_item(keymap, RETKEY, KM_RELEASE, KM_ANY, 0, OUTLINER_ITEM_DRAG_CONFIRM);
	WM_modalkeymap_add_item(keymap, PADENTER, KM_RELEASE, KM_ANY, 0, OUTLINER_ITEM_DRAG_CONFIRM);

	WM_modalkeymap_assign(keymap, "OUTLINER_OT_item_drag_drop");

	return keymap;
}

void outliner_keymap(wmKeyConfig *keyconf)
{
	wmKeyMap *keymap = WM_keymap_find(keyconf, "Outliner", SPACE_OUTLINER, 0);
	wmKeyMapItem *kmi;

	WM_keymap_add_item(keymap, "OUTLINER_OT_highlight_update", MOUSEMOVE, KM_ANY, KM_ANY, 0);

	WM_keymap_add_item(keymap, "OUTLINER_OT_item_rename", LEFTMOUSE, KM_DBL_CLICK, 0, 0);

	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_item_activate", LEFTMOUSE, KM_CLICK, 0, 0);
	RNA_boolean_set(kmi->ptr, "recursive", false);
	RNA_boolean_set(kmi->ptr, "extend", false);

	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_item_activate", LEFTMOUSE, KM_CLICK, KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "recursive", false);
	RNA_boolean_set(kmi->ptr, "extend", true);

	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_item_activate", LEFTMOUSE, KM_CLICK, KM_CTRL, 0);
	RNA_boolean_set(kmi->ptr, "recursive", true);
	RNA_boolean_set(kmi->ptr, "extend", false);

	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_item_activate", LEFTMOUSE, KM_CLICK, KM_CTRL | KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "recursive", true);
	RNA_boolean_set(kmi->ptr, "extend", true);


	WM_keymap_add_item(keymap, "OUTLINER_OT_select_border", BKEY, KM_PRESS, 0, 0);
	
	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_item_openclose", RETKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(kmi->ptr, "all", false);
	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_item_openclose", RETKEY, KM_PRESS, KM_SHIFT, 0);
	RNA_boolean_set(kmi->ptr, "all", true);
	
	WM_keymap_add_item(keymap, "OUTLINER_OT_item_rename", LEFTMOUSE, KM_PRESS, KM_CTRL, 0);
	WM_keymap_add_item(keymap, "OUTLINER_OT_operation", RIGHTMOUSE, KM_PRESS, 0, 0);

	WM_keymap_add_item(keymap, "OUTLINER_OT_item_drag_drop", EVT_TWEAK_L, KM_ANY, 0, 0);

	WM_keymap_add_item(keymap, "OUTLINER_OT_show_hierarchy", HOMEKEY, KM_PRESS, 0, 0);
	
	WM_keymap_add_item(keymap, "OUTLINER_OT_show_active", PERIODKEY, KM_PRESS, 0, 0);
	WM_keymap_add_item(keymap, "OUTLINER_OT_show_active", PADPERIOD, KM_PRESS, 0, 0);
	
	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_scroll_page", PAGEDOWNKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(kmi->ptr, "up", false);
	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_scroll_page", PAGEUPKEY, KM_PRESS, 0, 0);
	RNA_boolean_set(kmi->ptr, "up", true);
	
	WM_keymap_add_item(keymap, "OUTLINER_OT_show_one_level", PADPLUSKEY, KM_PRESS, 0, 0); /* open */
	kmi = WM_keymap_add_item(keymap, "OUTLINER_OT_show_one_level", PADMINUS, KM_PRESS, 0, 0);
	RNA_boolean_set(kmi->ptr, "open", false); /* close */
	
	WM_keymap_verify_item(keymap, "OUTLINER_OT_selected_toggle", AKEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "OUTLINER_OT_expanded_toggle", AKEY, KM_PRESS, KM_SHIFT, 0);
	
	/* keying sets - only for databrowse */
	WM_keymap_verify_item(keymap, "OUTLINER_OT_keyingset_add_selected", KKEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "OUTLINER_OT_keyingset_remove_selected", KKEY, KM_PRESS, KM_ALT, 0);
	
	WM_keymap_verify_item(keymap, "ANIM_OT_keyframe_insert", IKEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "ANIM_OT_keyframe_delete", IKEY, KM_PRESS, KM_ALT, 0);
	
	WM_keymap_verify_item(keymap, "OUTLINER_OT_drivers_add_selected", DKEY, KM_PRESS, 0, 0);
	WM_keymap_verify_item(keymap, "OUTLINER_OT_drivers_delete_selected", DKEY, KM_PRESS, KM_ALT, 0);

	outliner_item_drag_drop_modal_keymap(keyconf);
}

