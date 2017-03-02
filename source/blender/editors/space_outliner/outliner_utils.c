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
 * The Original Code is Copyright (C) 2017 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_outliner/outliner_utils.c
 *  \ingroup spoutliner
 */

#include "BKE_outliner_treehash.h"

#include "BLI_utildefines.h"

#include "DNA_action_types.h"
#include "DNA_space_types.h"

#include "ED_armature.h"

#include "UI_interface.h"

#include "outliner_intern.h"


/**
 * Try to find an item under y-coordinate \a view_co_y (view-space).
 * \note Recursive
 */
TreeElement *outliner_find_item_at_y(const SpaceOops *soops, const ListBase *tree, float view_co_y)
{
	for (TreeElement *te_iter = tree->first; te_iter; te_iter = te_iter->next) {
		if (view_co_y < (te_iter->ys + UI_UNIT_Y)) {
			if (view_co_y >= te_iter->ys) {
				/* co_y is inside this element */
				return te_iter;
			}
			else if (TSELEM_OPEN(te_iter->store_elem, soops)) {
				/* co_y is lower than current element, possibly inside children */
				TreeElement *te_sub = outliner_find_item_at_y(soops, &te_iter->subtree, view_co_y);
				if (te_sub) {
					return te_sub;
				}
			}
		}
	}

	return NULL;
}

/**
 * Collapsed items can show their children as click-able icons. This function tries to find
 * such an icon that represents the child item at x-coordinate \a view_co_x (view-space).
 *
 * \return a hovered child item or \a parent_te (if no hovered child found).
 */
TreeElement *outliner_find_item_at_x_in_row(const SpaceOops *soops, const TreeElement *parent_te, float view_co_x)
{
	if (!TSELEM_OPEN(TREESTORE(parent_te), soops)) { /* if parent_te is opened, it doesn't show childs in row */
		/* no recursion, items can only display their direct children in the row */
		for (TreeElement *child_te = parent_te->subtree.first;
		     child_te && view_co_x >= child_te->xs; /* don't look further if co_x is smaller than child position*/
		     child_te = child_te->next)
		{
			if ((child_te->flag & TE_ICONROW) && (view_co_x > child_te->xs) && (view_co_x < child_te->xend)) {
				return child_te;
			}
		}
	}

	/* return parent if no child is hovered */
	return (TreeElement *)parent_te;
}

/* Find specific item from the treestore */
TreeElement *outliner_find_tree_element(ListBase *lb, const TreeStoreElem *store_elem)
{
	TreeElement *te, *tes;
	for (te = lb->first; te; te = te->next) {
		if (te->store_elem == store_elem) return te;
		tes = outliner_find_tree_element(&te->subtree, store_elem);
		if (tes) return tes;
	}
	return NULL;
}

/* tse is not in the treestore, we use its contents to find a match */
TreeElement *outliner_find_tse(SpaceOops *soops, const TreeStoreElem *tse)
{
	TreeStoreElem *tselem;

	if (tse->id == NULL) return NULL;

	/* check if 'tse' is in treestore */
	tselem = BKE_outliner_treehash_lookup_any(soops->treehash, tse->type, tse->nr, tse->id);
	if (tselem)
		return outliner_find_tree_element(&soops->tree, tselem);

	return NULL;
}

/* Find treestore that refers to given ID */
TreeElement *outliner_find_id(SpaceOops *soops, ListBase *lb, const ID *id)
{
	for (TreeElement *te = lb->first; te; te = te->next) {
		TreeStoreElem *tselem = TREESTORE(te);
		if (tselem->type == 0) {
			if (tselem->id == id) {
				return te;
			}
			/* only deeper on scene or object */
			if (ELEM(te->idcode, ID_OB, ID_SCE) ||
			    ((soops->outlinevis == SO_GROUPS) && (te->idcode == ID_GR)))
			{
				TreeElement *tes = outliner_find_id(soops, &te->subtree, id);
				if (tes) {
					return tes;
				}
			}
		}
	}
	return NULL;
}

TreeElement *outliner_find_posechannel(ListBase *lb, const bPoseChannel *pchan)
{
	for (TreeElement *te = lb->first; te; te = te->next) {
		if (te->directdata == pchan) {
			return te;
		}

		TreeStoreElem *tselem = TREESTORE(te);
		if (ELEM(tselem->type, TSE_POSE_BASE, TSE_POSE_CHANNEL)) {
			TreeElement *tes = outliner_find_posechannel(&te->subtree, pchan);
			if (tes) {
				return tes;
			}
		}
	}
	return NULL;
}

TreeElement *outliner_find_editbone(ListBase *lb, const EditBone *ebone)
{
	for (TreeElement *te = lb->first; te; te = te->next) {
		if (te->directdata == ebone) {
			return te;
		}

		TreeStoreElem *tselem = TREESTORE(te);
		if (ELEM(tselem->type, 0, TSE_EBONE)) {
			TreeElement *tes = outliner_find_editbone(&te->subtree, ebone);
			if (tes) {
				return tes;
			}
		}
	}
	return NULL;
}

ID *outliner_search_back(SpaceOops *UNUSED(soops), TreeElement *te, short idcode)
{
	TreeStoreElem *tselem;
	te = te->parent;

	while (te) {
		tselem = TREESTORE(te);
		if (tselem->type == 0 && te->idcode == idcode) return tselem->id;
		te = te->parent;
	}
	return NULL;
}

/**
 * Iterate over all tree elements (pre-order traversal), executing \a func callback for
 * each tree element matching the optional filters.
 *
 * \param filter_te_flag: If not 0, only TreeElements with this flag will be visited.
 * \param filter_tselem_flag: Same as \a filter_te_flag, but for the TreeStoreElem.
 * \param func: Custom callback to execute for each visited item.
 */
bool outliner_tree_traverse(const SpaceOops *soops, ListBase *tree, int filter_te_flag, int filter_tselem_flag,
                            TreeTraversalFunc func, void *customdata)
{
	for (TreeElement *te = tree->first, *te_next; te; te = te_next) {
		TreeTraversalAction func_retval = TRAVERSE_CONTINUE;
		/* in case te is freed in callback */
		TreeStoreElem *tselem = TREESTORE(te);
		ListBase subtree = te->subtree;
		te_next = te->next;

		if (filter_te_flag && (te->flag & filter_te_flag) == 0) {
			/* skip */
		}
		else if (filter_tselem_flag && (tselem->flag & filter_tselem_flag) == 0) {
			/* skip */
		}
		else {
			func_retval = func(te, customdata);
		}
		/* Don't access te or tselem from now on! Might've been freed... */

		if (func_retval == TRAVERSE_BREAK) {
			return false;
		}

		if (func_retval == TRAVERSE_SKIP_CHILDS) {
			/* skip */
		}
		else if (!outliner_tree_traverse(soops, &subtree, filter_te_flag, filter_tselem_flag, func, customdata)) {
			return false;
		}
	}

	return true;
}
