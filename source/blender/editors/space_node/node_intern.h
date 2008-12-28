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
#ifndef ED_NODE_INTERN_H
#define ED_NODE_INTERN_H

/* internal exports only */

struct ARegion;
struct View2D;
struct bContext;
struct wmWindowManager;

/* defines */

#define NODE_SELECT_MOUSE		1


/* node_header.c */
void node_header_buttons(const bContext *C, ARegion *ar);

/* node_draw.c */
void drawnodespace(const bContext *C, ARegion *ar, View2D *v2d);

/* node_ops.c */
void node_operatortypes(void);
void node_keymap(wmWindowManager *wm);

/* node_select.c */
void NODE_OT_select(struct wmOperatorType *ot);
void NODE_OT_extend_select(struct wmOperatorType *ot);

/* drawnode.c */
void node_draw_link(View2D *v2d, SpaceNode *snode, bNodeLink *link);
void node_draw_link_bezier(View2D *v2d, float vec[][3], int th_col1, int th_col2, int do_shaded);
void draw_nodespace_back_pix(ScrArea *sa, SpaceNode *snode);

/* node_edit.c */
void snode_set_context(SpaceNode *snode, Scene *scene);
void scale_node(SpaceNode *snode, bNode *node);
void snode_make_group_editable(SpaceNode *snode, bNode *gnode);
void node_set_active(SpaceNode *snode, bNode *node);
void node_deselectall(SpaceNode *snode, int swap);

#endif /* ED_NODE_INTERN_H */

