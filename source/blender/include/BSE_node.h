/**
 * $Id:
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your opt ion) any later version. 
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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL BLOCK *****
 */

#ifndef BSE_NODE_H
#define BSE_NODE_H

/* ********** drawing sizes *********** */
#define NODE_DY		20
#define NODE_DYS	10
#define NODE_SOCKSIZE	5
#define BASIS_RAD	8.0f
#define HIDDEN_RAD	15.0f


struct SpaceNode;
struct bNode;
struct Material;


/* ************* API for editnode.c *********** */
void snode_tag_dirty(struct SpaceNode *snode);

void snode_set_context(struct SpaceNode *snode);

void node_deselectall(struct SpaceNode *snode, int swap);
void node_transform_ext(int mode, int unused);
void node_shader_default(struct Material *ma);

int node_has_hidden_sockets(struct bNode *node);

/* ************* drawnode.c *************** */
void node_draw_link(struct SpaceNode *snode, struct bNodeLink *link);

void init_node_butfuncs(void);

/* ************* Shader nodes ***************** */

struct bNode *node_add_shadernode(struct SpaceNode *snode, int type, float locx, float locy);

#endif

