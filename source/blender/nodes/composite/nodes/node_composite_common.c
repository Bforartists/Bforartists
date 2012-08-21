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

/** \file blender/nodes/composite/nodes/node_composite_common.c
 *  \ingroup cmpnodes
 */

#include "DNA_node_types.h"

#include "BKE_node.h"

#include "node_composite_util.h"
#include "node_common.h"
#include "node_exec.h"

#if 0
static void PRINT_BUFFERS(bNodeTreeExec *exec)
{
	bNodeTree *ntree= exec->nodetree;
	bNode *node;
	bNodeSocket *sock;
	bNodeStack *ns;
	int i;
	
	printf("-------------- DEBUG --------------\n");
	for (sock=ntree->inputs.first, i=0; sock; sock=sock->next, ++i) {
		ns = node_get_socket_stack(exec->stack, sock);
		printf("%d. Tree Input %s", i, sock->name);
		if (ns->external)
			printf(" (external)");
		printf(": data=%p\n", ns->data);
	}
	for (sock=ntree->outputs.first, i=0; sock; sock=sock->next, ++i) {
		ns = node_get_socket_stack(exec->stack, sock);
		printf("%d. Tree Output %s", i, sock->name);
		if (ns->external)
			printf(" (external)");
		printf(": data=%p\n", ns->data);
	}
	for (node=ntree->nodes.first; node; node=node->next) {
		printf("Node %s:\n", node->name);
		for (sock=node->inputs.first, i=0; sock; sock=sock->next, ++i) {
			ns = node_get_socket_stack(exec->stack, sock);
			printf("\t%d. Input %s", i, sock->name);
			if (ns->external)
				printf(" (external)");
			printf(": data=%p\n", ns->data);
		}
		for (sock=node->outputs.first, i=0; sock; sock=sock->next, ++i) {
			ns = node_get_socket_stack(exec->stack, sock);
			printf("\t%d. Output %s", i, sock->name);
			if (ns->external)
				printf(" (external)");
			printf(": data=%p\n", ns->data);
		}
	}
}
#endif

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

static void move_stack(bNodeStack *to, bNodeStack *from)
{
	if (to != from) {
		copy_v4_v4(to->vec, from->vec);
		to->data = from->data;
		to->datatype = from->datatype;
		to->is_copy = from->is_copy;
		
		zero_v4(from->vec);
		from->data = NULL;
		from->datatype = 0;
		from->is_copy = 0;
	}
}

/**** GROUP ****/

static void *group_initexec(bNode *node)
{
	bNodeTree *ngroup= (bNodeTree *)node->id;
	bNodeTreeExec *exec;
	bNodeSocket *sock;
	bNodeStack *ns;
	
	if (!ngroup)
		return NULL;
	
	/* initialize the internal node tree execution */
	exec = ntreeCompositBeginExecTree(ngroup, 0);
	
	/* tag group outputs as external to prevent freeing */
	for (sock=ngroup->outputs.first; sock; sock=sock->next) {
		if (!(sock->flag & SOCK_INTERNAL)) {
			ns = node_get_socket_stack(exec->stack, sock);
			ns->external = 1;
		}
	}

	return exec;
}

static void group_freeexec(bNode *UNUSED(node), void *nodedata)
{
	bNodeTreeExec *gexec= (bNodeTreeExec *)nodedata;
	
	if (gexec)
		ntreeCompositEndExecTree(gexec, 0);
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
static void group_move_outputs(bNode *node, bNodeStack **out, bNodeStack *gstack)
{
	bNodeSocket *sock;
	bNodeStack *ns;
	int a;
	for (sock=node->outputs.first, a=0; sock; sock=sock->next, ++a) {
		if (sock->groupsock) {
			ns = node_get_socket_stack(gstack, sock->groupsock);
			move_stack(out[a], ns);
		}
	}
}

/* Free internal buffers */
static void group_free_internal(bNodeTreeExec *gexec)
{
	bNodeStack *ns;
	int i;
	
	for (i=0, ns=gexec->stack; i < gexec->stacksize; ++i, ++ns) {
		if (!ns->external && !ns->is_copy) {
			if (ns->data) {
#ifdef WITH_COMPOSITOR_LEGACY
				free_compbuf(ns->data);
#endif
				ns->data = NULL;
			}
		}
	}
}

static void group_execute(void *data, int thread, struct bNode *node, void *nodedata, struct bNodeStack **in, struct bNodeStack **out)
{
	bNodeTreeExec *exec= (bNodeTreeExec *)nodedata;
	
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
	
	group_copy_inputs(node, in, exec->stack);
	ntreeExecNodes(exec, data, thread);
	group_free_internal(exec);
	group_move_outputs(node, out, exec->stack);
}

void register_node_type_cmp_group(bNodeTreeType *ttype)
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

#ifdef WITH_COMPOSITOR_LEGACY

/**** FOR LOOP ****/

#if 0 /* XXX loop nodes don't work nicely with current trees */
/* Move the results from the previous iteration back to the input sockets. */
static void loop_iteration_reset(bNodeTree *ngroup, bNodeStack *gstack)
{
	bNodeSocket *gin, *gout;
	bNodeStack *nsin, *nsout;
	
	gin = ngroup->inputs.first;
	gout = ngroup->outputs.first;
	
	while (gin && gout) {
		/* skip static (non-looping) sockets */
		while (gin && !(gin->flag & SOCK_DYNAMIC))
			gin=gin->next;
		while (gout && !(gout->flag & SOCK_DYNAMIC))
			gout=gout->next;
		
		if (gin && gout) {
			nsin = node_get_socket_stack(gstack, gin);
			nsout = node_get_socket_stack(gstack, gout);
			
			move_stack(nsin, nsout);
			
			gin=gin->next;
			gout=gout->next;
		}
	}
}

static void forloop_execute(void *data, int thread, struct bNode *node, void *nodedata, struct bNodeStack **in, struct bNodeStack **out)
{
	bNodeTreeExec *exec= (bNodeTreeExec *)nodedata;
	int totiterations= (int)in[0]->vec[0];
	bNodeSocket *sock;
	bNodeStack *ns;
	int iteration;
	
	/* XXX same behavior as trunk: all nodes inside group are executed.
	 * it's stupid, but just makes it work. compo redesign will do this better.
	 */
	{
		bNode *inode;
		for (inode=exec->nodetree->nodes.first; inode; inode=inode->next)
			inode->need_exec = 1;
	}
	
	/* "Iteration" socket */
	sock = exec->nodetree->inputs.first;
	ns = node_get_socket_stack(exec->stack, sock);
	
	group_copy_inputs(node, in, exec->stack);
	for (iteration=0; iteration < totiterations; ++iteration) {
		/* first input contains current iteration counter */
		ns->vec[0] = (float)iteration;
		
		if (iteration > 0)
			loop_iteration_reset(exec->nodetree, exec->stack);
		ntreeExecNodes(exec, data, thread);
		group_free_internal(exec);
	}
	group_move_outputs(node, out, exec->stack);
}

void register_node_type_cmp_forloop(bNodeTreeType *ttype)
{
	static bNodeType ntype;

	node_type_base(ttype, &ntype, NODE_FORLOOP, "For", NODE_CLASS_GROUP, NODE_OPTIONS);
	node_type_socket_templates(&ntype, NULL, NULL);
	node_type_size(&ntype, 120, 60, 200);
	node_type_label(&ntype, node_group_label);
	node_type_init(&ntype, node_forloop_init);
	node_type_valid(&ntype, node_group_valid);
	node_type_template(&ntype, node_forloop_template);
	node_type_update(&ntype, NULL, node_group_verify);
	node_type_tree(&ntype, node_forloop_init_tree, node_loop_update_tree);
	node_type_group_edit(&ntype, node_group_edit_get, node_group_edit_set, node_group_edit_clear);
	node_type_exec_new(&ntype, group_initexec, group_freeexec, forloop_execute);
	
	nodeRegisterType(ttype, &ntype);
}
#endif


/**** WHILE LOOP ****/

#if 0 /* XXX loop nodes don't work nicely with current trees */
static void whileloop_execute(void *data, int thread, struct bNode *node, void *nodedata, struct bNodeStack **in, struct bNodeStack **out)
{
	bNodeTreeExec *exec= (bNodeTreeExec *)nodedata;
	int condition= (in[0]->vec[0] > 0.0f);
	bNodeSocket *sock;
	bNodeStack *ns;
	int iteration;
	
	/* XXX same behavior as trunk: all nodes inside group are executed.
	 * it's stupid, but just makes it work. compo redesign will do this better.
	 */
	{
		bNode *inode;
		for (inode=exec->nodetree->nodes.first; inode; inode=inode->next)
			inode->need_exec = 1;
	}
	
	/* "Condition" socket */
	sock = exec->nodetree->outputs.first;
	ns = node_get_socket_stack(exec->stack, sock);
	
	iteration = 0;
	group_copy_inputs(node, in, exec->stack);
	while (condition && iteration < node->custom1) {
		if (iteration > 0)
			loop_iteration_reset(exec->nodetree, exec->stack);
		ntreeExecNodes(exec, data, thread);
		group_free_internal(exec);
		
//		PRINT_BUFFERS(exec);
		
		condition = (ns->vec[0] > 0.0f);
		++iteration;
	}
	group_move_outputs(node, out, exec->stack);
}

void register_node_type_cmp_whileloop(bNodeTreeType *ttype)
{
	static bNodeType ntype;

	node_type_base(ttype, &ntype, NODE_WHILELOOP, "While", NODE_CLASS_GROUP, NODE_OPTIONS);
	node_type_socket_templates(&ntype, NULL, NULL);
	node_type_size(&ntype, 120, 60, 200);
	node_type_label(&ntype, node_group_label);
	node_type_init(&ntype, node_whileloop_init);
	node_type_valid(&ntype, node_group_valid);
	node_type_template(&ntype, node_whileloop_template);
	node_type_update(&ntype, NULL, node_group_verify);
	node_type_tree(&ntype, node_whileloop_init_tree, node_loop_update_tree);
	node_type_group_edit(&ntype, node_group_edit_get, node_group_edit_set, node_group_edit_clear);
	node_type_exec_new(&ntype, group_initexec, group_freeexec, whileloop_execute);
	
	nodeRegisterType(ttype, &ntype);
}
#endif

#endif  /* WITH_COMPOSITOR_LEGACY */
