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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdlib.h>

#include "DNA_ID.h"
#include "DNA_node_types.h"

#include "BKE_blender.h"
#include "BKE_node.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "MEM_guardedalloc.h"

/* ************** Add stuff ********** */

/* not very important, but the stack solver likes to know a maximum */
#define MAX_SOCKET	64

bNode *nodeAddNode(struct bNodeTree *ntree, char *name)
{
	bNode *node= MEM_callocN(sizeof(bNode), "new node");
	
	BLI_addtail(&ntree->nodes, node);
	BLI_strncpy(node->name, name, NODE_MAXSTR);
	return node;
}

/* keep listorder identical, for copying links */
bNode *nodeCopyNode(struct bNodeTree *ntree, struct bNode *node)
{
	bNode *nnode= MEM_callocN(sizeof(bNode), "dupli node");
	
	*nnode= *node;
	BLI_addtail(&ntree->nodes, nnode);
	
	duplicatelist(&nnode->inputs, &node->inputs);
	duplicatelist(&nnode->outputs, &node->outputs);
	if(nnode->id)
		nnode->id->us++;
	
	node->flag= NODE_SELECT;

	return nnode;
}

bNodeLink *nodeAddLink(bNodeTree *ntree, bNode *fromnode, bNodeSocket *fromsock, bNode *tonode, bNodeSocket *tosock)
{
	bNodeLink *link= MEM_callocN(sizeof(bNodeLink), "link");
	
	BLI_addtail(&ntree->links, link);
	link->fromnode= fromnode;
	link->fromsock= fromsock;
	link->tonode= tonode;
	link->tosock= tosock;
	
	return link;
}

bNodeSocket *nodeAddSocket(bNode *node, int type, int where, int limit, char *name)
{
	bNodeSocket *sock= MEM_callocN(sizeof(bNodeSocket), "sock");
	
	BLI_strncpy(sock->name, name, NODE_MAXSTR);
	sock->limit= limit;
	sock->type= type;
	if(where==SOCK_IN)
		BLI_addtail(&node->inputs, sock);
	else
		BLI_addtail(&node->outputs, sock);
		
	return sock;
}

/* ************** Free stuff ********** */

/* goes over entire tree */
static void node_unlink_node(bNodeTree *ntree, bNode *node)
{
	bNodeLink *link, *next;
	bNodeSocket *sock;
	ListBase *lb;
	
	for(link= ntree->links.first; link; link= next) {
		next= link->next;
		
		if(link->fromnode==node)
			lb= &node->outputs;
		else if(link->tonode==node)
			lb= &node->inputs;
		else
			lb= NULL;

		if(lb) {
			for(sock= lb->first; sock; sock= sock->next) {
				if(link->fromsock==sock || link->tosock==sock)
					break;
			}
			if(sock) {
				BLI_remlink(&ntree->links, link);
				MEM_freeN(link);
			}
		}
	}
}

void nodeFreeNode(bNodeTree *ntree, bNode *node)
{
	if(ntree) {
		node_unlink_node(ntree, node);
		BLI_remlink(&ntree->nodes, node);
	}
	if(node->id)
		node->id->us--;
	
	BLI_freelistN(&node->inputs);
	BLI_freelistN(&node->outputs);
	
	MEM_freeN(node);
}

void nodeFreeTree(bNodeTree *ntree)
{
	bNode *node, *next;
	
	for(node= ntree->nodes.first; node; node= next) {
		next= node->next;
		nodeFreeNode(NULL, node);		/* NULL -> no unlinking needed */
	}
	BLI_freelistN(&ntree->links);
	BLI_freelistN(&ntree->inputs);
	BLI_freelistN(&ntree->outputs);
	
	MEM_freeN(ntree);
}

/* ************ find stuff *************** */

bNodeLink *nodeFindLink(bNodeTree *ntree, bNodeSocket *from, bNodeSocket *to)
{
	bNodeLink *link;
	
	for(link= ntree->links.first; link; link= link->next) {
		if(link->fromsock==from && link->tosock==to)
			return link;
		if(link->fromsock==to && link->tosock==from)	/* hrms? */
			return link;
	}
	return NULL;
}

int nodeCountSocketLinks(bNodeTree *ntree, bNodeSocket *sock)
{
	bNodeLink *link;
	int tot= 0;
	
	for(link= ntree->links.first; link; link= link->next) {
		if(link->fromsock==sock || link->tosock==sock)
			tot++;
	}
	return tot;
}

/* ************** dependency stuff *********** */

/* node is guaranteed to be not checked before */
static int node_recurs_check(bNode *node, bNode ***nsort, int level)
{
	bNode *fromnode;
	bNodeSocket *sock;
	int has_inputlinks= 0;
	
	node->done= 1;
	level++;
	
	for(sock= node->inputs.first; sock; sock= sock->next) {
		if(sock->link) {
			has_inputlinks= 1;
			fromnode= sock->link->fromnode;
			if(fromnode->done==0) {
				fromnode->level= node_recurs_check(fromnode, nsort, level);
			}
		}
	}
//	printf("node sort %s level %d\n", node->name, level);
	**nsort= node;
	(*nsort)++;
	
	if(has_inputlinks)
		return level;
	else 
		return 0xFFF;
}

void nodeSolveOrder(bNodeTree *ntree)
{
	bNode *node, **nodesort, **nsort;
	bNodeSocket *sock;
	bNodeLink *link;
	int a, totnode=0;
	
	/* set links pointers the input sockets, to find dependencies */
	/* first clear data */
	for(node= ntree->nodes.first; node; node= node->next) {
		node->done= 0;
		totnode++;
		for(sock= node->inputs.first; sock; sock= sock->next)
			sock->link= NULL;
	}
	if(totnode==0)
		return;
	
	for(link= ntree->links.first; link; link= link->next) {
		link->tosock->link= link;
	}
	
	nsort= nodesort= MEM_callocN(totnode*sizeof(void *), "sorted node array");
	
	/* recursive check */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->done==0) {
			node->level= node_recurs_check(node, &nsort, 0);
		}
	}
	
	/* re-insert nodes in order, first a paranoia check */
	for(a=0; a<totnode; a++) {
		if(nodesort[a]==NULL)
			break;
	}
	if(a<totnode)
		printf("sort error in node tree");
	else {
		ntree->nodes.first= ntree->nodes.last= NULL;
		for(a=0; a<totnode; a++)
			BLI_addtail(&ntree->nodes, nodesort[a]);
	}
	
	MEM_freeN(nodesort);
	
}

/* ******************* executing ************* */


void nodeBeginExecTree(bNodeTree *ntree)
{
	bNode *node;
	bNodeSocket *sock;
	int index= 0;
	
	if((ntree->init & NTREE_EXEC_SET)==0) {
		for(node= ntree->nodes.first; node; node= node->next) {
			if(ntree->type==NTREE_SHADER)
				node_shader_set_execfunc(node);
		}
		ntree->init |= NTREE_EXEC_SET;
	}
	
	/* create indices for stack */
	for(node= ntree->nodes.first; node; node= node->next) {
		
		for(sock= node->outputs.first; sock; sock= sock->next) {
			sock->stack_index= index++;
		}
	}
	if(index) {
		ntree->stack= MEM_callocN(index*sizeof(bNodeStack), "node stack");
	}
}

void nodeEndExecTree(bNodeTree *ntree)
{
	if(ntree->stack) {
		MEM_freeN(ntree->stack);
		ntree->stack= NULL;
	}
}

static void node_get_stack(bNode *node, bNodeStack *stack, bNodeStack **spp)
{
	static bNodeStack empty= {{1.0f, 1.0f, 1.0f, 1.0f}, NULL};
	bNodeSocket *sock;
	
	/* build pointer stack */
	for(sock= node->inputs.first; sock; sock= sock->next) {
		if(sock->link)
			*(spp++)= stack + sock->link->fromsock->stack_index;
		else
			*(spp++)= &empty;	/* input is not written into */
	}
	
	for(sock= node->outputs.first; sock; sock= sock->next) {
		*(spp++)= stack + sock->stack_index;
	}
}

/* nodes are presorted, so exec is in order of list */
void nodeExecTree(bNodeTree *ntree)
{
	bNode *node;
	bNodeStack *ns[MAX_SOCKET];	/* arbitrary... watch this */
	
	nodeBeginExecTree(ntree);
	
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->execfunc) {
			node_get_stack(node, ntree->stack, ns);
			node->execfunc(node, ns);
		}
	}

	nodeEndExecTree(ntree);
}

