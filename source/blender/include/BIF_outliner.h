/**
 * $Id: BIF_outliner.h
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * The Original Code is Copyright (C) 2004 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef BIF_OUTLINER_H
#define BIF_OUTLINER_H

struct TreeStoreElem;

typedef struct TreeElement {
	struct TreeElement *next, *prev, *parent;
	ListBase subtree;
	float xs, ys;		// doe selection
	int store_index;	// offset in tree store
	short flag, index;	// flag for non-saved stuff, index for data arrays
	short idcode;		// from TreeStore id
	short xend;		// width of item display, for select
	char *name;
	void *directdata;	// Armature Bones, Base, ...
}  TreeElement;

/* TreeElement->flag */
#define TE_ACTIVE	1
#define TE_ICONROW	2

/* TreeStoreElem types */
#define TSE_NLA				1
#define TSE_NLA_ACTION		2
#define TSE_DEFGROUP_BASE	3
#define TSE_DEFGROUP			4
#define TSE_BONE				5
#define TSE_CONSTRAINT_BASE	6
#define TSE_CONSTRAINT		7
#define TSE_HOOKS_BASE		8
#define TSE_HOOK				9
#define TSE_SCRIPT_BASE		10

/* button events */
#define OL_NAMEBUTTON		1

extern void draw_outliner(struct ScrArea *sa, struct SpaceOops *so);
extern void outliner_free_tree(struct ListBase *lb);
extern void outliner_mouse_event(struct ScrArea *sa, short event);
extern void outliner_toggle_visible(struct ScrArea *sa);
extern void outliner_show_active(struct ScrArea *sa);
extern void outliner_show_hierarchy(struct ScrArea *sa);
extern void outliner_one_level(struct ScrArea *sa, int add);
extern void outliner_select(struct ScrArea *sa);
extern void outliner_toggle_selected(struct ScrArea *sa);
extern void outliner_operation_menu(struct ScrArea *sa);
extern void outliner_page_up_down(struct ScrArea *sa, int up);

#endif

