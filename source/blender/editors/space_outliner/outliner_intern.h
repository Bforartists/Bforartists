/**
 * $Id$
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

#ifndef ED_OUTLINER_INTERN_H
#define ED_OUTLINER_INTERN_H

#include "RNA_types.h"

/* internal exports only */

struct wmWindowManager;
struct wmOperatorType;
struct TreeStoreElem;
struct bContext;
struct Scene;
struct ARegion;

typedef struct TreeElement {
	struct TreeElement *next, *prev, *parent;
	ListBase subtree;
	float xs, ys;		// do selection
	int store_index;	// offset in tree store
	short flag;			// flag for non-saved stuff
	short index;		// index for data arrays
	short idcode;		// from TreeStore id
	short xend;			// width of item display, for select
	const char *name;
	void *directdata;	// Armature Bones, Base, Sequence, Strip...
	PointerRNA rnaptr;	// RNA Pointer
}  TreeElement;

/* TreeElement->flag */
#define TE_ACTIVE		1
#define TE_ICONROW		2
#define TE_LAZY_CLOSED	4
#define TE_FREE_NAME	8

/* TreeStoreElem types */
#define TSE_NLA				1	
#define TSE_NLA_ACTION		2
#define TSE_DEFGROUP_BASE	3
#define TSE_DEFGROUP		4
#define TSE_BONE			5
#define TSE_EBONE			6
#define TSE_CONSTRAINT_BASE	7
#define TSE_CONSTRAINT		8
#define TSE_MODIFIER_BASE	9
#define TSE_MODIFIER		10
#define TSE_LINKED_OB		11
#define TSE_SCRIPT_BASE		12
#define TSE_POSE_BASE		13
#define TSE_POSE_CHANNEL	14
#define TSE_ANIM_DATA		15
#define TSE_DRIVER_BASE		16
#define TSE_DRIVER			17

#define TSE_PROXY			18
#define TSE_R_LAYER_BASE	19
#define TSE_R_LAYER			20
#define TSE_R_PASS			21
#define TSE_LINKED_MAT		22
/* NOTE, is used for light group */
#define TSE_LINKED_LAMP		23
#define TSE_POSEGRP_BASE	24
#define TSE_POSEGRP			25
#define TSE_SEQUENCE		26
#define TSE_SEQ_STRIP		27
#define TSE_SEQUENCE_DUP	28
#define TSE_LINKED_PSYS     29
#define TSE_RNA_STRUCT		30
#define TSE_RNA_PROPERTY	31
#define TSE_RNA_ARRAY_ELEM	32
#define TSE_NLA_TRACK		33
#define TSE_KEYMAP			34
#define TSE_KEYMAP_ITEM		35

/* button events */
#define OL_NAMEBUTTON		1


/* outliner_ops.c */
void outliner_operatortypes(void);
void outliner_keymap(struct wmKeyConfig *keyconf);

/* outliner_header.c */
void outliner_header_buttons(const struct bContext *C, struct ARegion *ar);

/* outliner.c */
void outliner_free_tree(struct ListBase *lb);
void outliner_select(struct SpaceOops *soops, struct ListBase *lb, int *index, short *selecting);
void draw_outliner(const struct bContext *C);

void OUTLINER_OT_item_activate(struct wmOperatorType *ot);
void OUTLINER_OT_item_openclose(struct wmOperatorType *ot);
void OUTLINER_OT_item_rename(struct wmOperatorType *ot);
void OUTLINER_OT_operation(struct wmOperatorType *ot);
void OUTLINER_OT_object_operation(struct wmOperatorType *ot);
void OUTLINER_OT_group_operation(struct wmOperatorType *ot);
void OUTLINER_OT_id_operation(struct wmOperatorType *ot);
void OUTLINER_OT_data_operation(struct wmOperatorType *ot);

void OUTLINER_OT_show_one_level(struct wmOperatorType *ot);
void OUTLINER_OT_show_active(struct wmOperatorType *ot);
void OUTLINER_OT_show_hierarchy(struct wmOperatorType *ot);

void OUTLINER_OT_selected_toggle(struct wmOperatorType *ot);
void OUTLINER_OT_expanded_toggle(struct wmOperatorType *ot);

void OUTLINER_OT_renderability_toggle(struct wmOperatorType *ot);
void OUTLINER_OT_selectability_toggle(struct wmOperatorType *ot);
void OUTLINER_OT_visibility_toggle(struct wmOperatorType *ot);

void OUTLINER_OT_keyingset_add_selected(struct wmOperatorType *ot);
void OUTLINER_OT_keyingset_remove_selected(struct wmOperatorType *ot);

void OUTLINER_OT_drivers_add_selected(struct wmOperatorType *ot);
void OUTLINER_OT_drivers_delete_selected(struct wmOperatorType *ot);

#endif /* ED_OUTLINER_INTERN_H */

