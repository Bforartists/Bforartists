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
 * The Original Code is Copyright (C) 2006 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Campbell Barton, Alfredo de Greef, David Millan Escriva,
 * Juho Vepsäläinen
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/nodes/texture/nodes/node_texture_common.c
 *  \ingroup texnodes
 */


#include "DNA_node_types.h"

#include "BLI_utildefines.h"

#include "BKE_node.h"

#include "node_texture_util.h"
#include "node_common.h"
#include "node_exec.h"

static void copy_stack(bNodeStack *to, bNodeStack *from)
{
	if (to != from) {
		copy_v4_v4(to->vec, from->vec);
		to->data = from->data;
		to->datatype = from->datatype;
		
		/* tag as copy to prevent freeing */
		to->is_copy = 1;
	}
}

/**** GROUP ****/

static void *group_initexec(bNode *node)
{
	bNodeTree *ngroup= (bNodeTree*)node->id;
	void *exec;
	
	if (!ngroup)
		return NULL;
	
	/* initialize the internal node tree execution */
	exec = ntreeTexBeginExecTree(ngroup, 0);
	
	return exec;
}

static void group_freeexec(bNode *UNUSED(node), void *nodedata)
{
	bNodeTreeExec*gexec= (bNodeTreeExec*)nodedata;
	
	ntreeTexEndExecTree(gexec, 0);
}

/* Copy inputs to the internal stack.
 * This is a shallow copy, no buffers are duplicated here!
 */
static void group_copy_inputs(bNode *node, bNodeStack **in, bNodeStack *gstack)
{
	bNodeSocket *sock;
	bNodeStack *ns;
	int a;
	for (sock=node->inputs.first, a=0; sock; sock=sock->next, ++a) {
		if (sock->groupsock) {
			ns = node_get_socket_stack(gstack, sock->groupsock);
			copy_stack(ns, in[a]);
		}
	}
}

/* Copy internal results to the external outputs.
 */
static void group_copy_outputs(bNode *node, bNodeStack **out, bNodeStack *gstack)
{
	bNodeSocket *sock;
	bNodeStack *ns;
	int a;
	for (sock=node->outputs.first, a=0; sock; sock=sock->next, ++a) {
		if (sock->groupsock) {
			ns = node_get_socket_stack(gstack, sock->groupsock);
			copy_stack(out[a], ns);
		}
	}
}

static void group_execute(void *data, int thread, struct bNode *node, void *nodedata, struct bNodeStack **in, struct bNodeStack **out)
{
	bNodeTreeExec *exec= (bNodeTreeExec*)nodedata;
	bNodeThreadStack *nts;
	
	if (!exec)
		return;
	
	/* XXX same behavior as trunk: all nodes inside group are executed.
	 * it's stupid, but just makes it work. compo redesign will do this better.
	 */
	{
		bNode *inode;
		for (inode=exec->nodetree->nodes.first; inode; inode=inode->next)
			inode->need_exec = 1;
	}
	
	nts = ntreeGetThreadStack(exec, thread);
	
	group_copy_inputs(node, in, nts->stack);
	ntreeExecThreadNodes(exec, nts, data, thread);
	group_copy_outputs(node, out, nts->stack);
	
	ntreeReleaseThreadStack(nts);
}

void register_node_type_tex_group(bNodeTreeType *ttype)
{
	static bNodeType ntype;

	node_type_base(ttype, &ntype, NODE_GROUP, "Group", NODE_CLASS_GROUP, NODE_OPTIONS|NODE_CONST_OUTPUT);
	node_type_socket_templates(&ntype, NULL, NULL);
	node_type_size(&ntype, 120, 60, 200);
	node_type_label(&ntype, node_group_label);
	node_type_init(&ntype, node_group_init);
	node_type_valid(&ntype, node_group_valid);
	node_type_template(&ntype, node_group_template);
	node_type_update(&ntype, NULL, node_group_verify);
	node_type_group_edit(&ntype, node_group_edit_get, node_group_edit_set, node_group_edit_clear);
	node_type_exec_new(&ntype, group_initexec, group_freeexec, group_execute);
	
	nodeRegisterType(ttype, &ntype);
}
