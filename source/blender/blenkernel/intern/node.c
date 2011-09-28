/*
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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Bob Holcomb.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/node.c
 *  \ingroup bke
 */


#if 0 /* pynodes commented for now */
#  ifdef WITH_PYTHON
#    include <Python.h>
#  endif
#endif

#include "MEM_guardedalloc.h"

#include <stdlib.h>
#include <stddef.h>
#include <string.h>
#include <limits.h>

#include "DNA_anim_types.h"
#include "DNA_node_types.h"
#include "DNA_scene_types.h"
#include "DNA_action_types.h"

#include "BLI_string.h"
#include "BLI_math.h"
#include "BLI_listbase.h"
#include "BLI_path_util.h"
#include "BLI_utildefines.h"

#include "BKE_animsys.h"
#include "BKE_action.h"
#include "BKE_fcurve.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_utildefines.h"
#include "BKE_utildefines.h"

#include "BLI_listbase.h"

#include "RNA_access.h"

#include "NOD_socket.h"
#include "NOD_composite.h"
#include "NOD_shader.h"
#include "NOD_texture.h"


bNodeTreeType *ntreeGetType(int type)
{
	static bNodeTreeType *types[NUM_NTREE_TYPES];
	static int types_init = 1;
	if (types_init) {
		types[NTREE_SHADER] = &ntreeType_Shader;
		types[NTREE_COMPOSIT] = &ntreeType_Composite;
		types[NTREE_TEXTURE] = &ntreeType_Texture;
		types_init = 0;
	}
	
	if(type >= 0 && type < NUM_NTREE_TYPES) {
		return types[type];
	}
	else {
		return NULL;
	}
}

static bNodeType *node_get_type(bNodeTree *ntree, int type)
{
	bNodeType *ntype = ntreeGetType(ntree->type)->node_types.first;
	for(; ntype; ntype= ntype->next)
		if(ntype->type==type)
			return ntype;
	
	return NULL;
}

bNodeType *ntreeGetNodeType(bNodeTree *ntree)
{
	return node_get_type(ntree, ntree->nodetype);
}

bNodeSocketType *ntreeGetSocketType(int type)
{
	static bNodeSocketType *types[NUM_SOCKET_TYPES]= {NULL};
	static int types_init = 1;

	if (types_init) {
		node_socket_type_init(types);
		types_init= 0;
	}

	if(type < NUM_SOCKET_TYPES) {
		return types[type];
	}
	else {
		return NULL;
	}
}

void ntreeInitTypes(bNodeTree *ntree)
{
	bNode *node, *next;
	
	for(node= ntree->nodes.first; node; node= next) {
		next= node->next;
		
		node->typeinfo= node_get_type(ntree, node->type);
		
		if(node->type==NODE_DYNAMIC) {
			/* needed info if the pynode script fails now: */
			node->storage= ntree;
			if(node->id!=NULL) { /* not an empty script node */
				node->custom1= 0;
				node->custom1= BSET(node->custom1,NODE_DYNAMIC_ADDEXIST);
			}
//			if(node->typeinfo)
//				node->typeinfo->initfunc(node);
		}

		if(node->typeinfo==NULL) {
			printf("Error: Node type %s doesn't exist anymore, removed\n", node->name);
			nodeFreeNode(ntree, node);
		}
	}
			
	ntree->init |= NTREE_TYPE_INIT;
}

static bNodeSocket *make_socket(bNodeTree *UNUSED(ntree), int in_out, const char *name, int type)
{
	bNodeSocketType *stype= ntreeGetSocketType(type);
	bNodeSocket *sock;
	
	sock= MEM_callocN(sizeof(bNodeSocket), "sock");
	
	BLI_strncpy(sock->name, name, NODE_MAXSTR);
	sock->limit = (in_out==SOCK_IN ? 1 : 0xFFF);
	sock->type= type;
	sock->storage = NULL;
	
	if (stype->value_structsize > 0)
		sock->default_value = MEM_callocN(stype->value_structsize, "default socket value");
	
	return sock;
}

bNodeSocket *nodeAddSocket(bNodeTree *ntree, bNode *node, int in_out, const char *name, int type)
{
	bNodeSocket *sock = make_socket(ntree, in_out, name, type);
	if (in_out==SOCK_IN)
		BLI_addtail(&node->inputs, sock);
	else if (in_out==SOCK_OUT)
		BLI_addtail(&node->outputs, sock);
	
	ntree->update |= NTREE_UPDATE_NODES;
	
	return sock;
}

bNodeSocket *nodeInsertSocket(bNodeTree *ntree, bNode *node, int in_out, bNodeSocket *next_sock, const char *name, int type)
{
	bNodeSocket *sock = make_socket(ntree, in_out, name, type);
	if (in_out==SOCK_IN)
		BLI_insertlinkbefore(&node->inputs, next_sock, sock);
	else if (in_out==SOCK_OUT)
		BLI_insertlinkbefore(&node->outputs, next_sock, sock);
	
	ntree->update |= NTREE_UPDATE_NODES;
	
	return sock;
}

void nodeRemoveSocket(bNodeTree *ntree, bNode *node, bNodeSocket *sock)
{
	bNodeLink *link, *next;
	
	for(link= ntree->links.first; link; link= next) {
		next= link->next;
		if(link->fromsock==sock || link->tosock==sock) {
			nodeRemLink(ntree, link);
		}
	}
	
	/* this is fast, this way we don't need an in_out argument */
	BLI_remlink(&node->inputs, sock);
	BLI_remlink(&node->outputs, sock);
	
	if (sock->default_value)
		MEM_freeN(sock->default_value);
	MEM_freeN(sock);
	
	ntree->update |= NTREE_UPDATE_NODES;
}

void nodeRemoveAllSockets(bNodeTree *ntree, bNode *node)
{
	bNodeSocket *sock;
	bNodeLink *link, *next;
	
	for(link= ntree->links.first; link; link= next) {
		next= link->next;
		if(link->fromnode==node || link->tonode==node) {
			nodeRemLink(ntree, link);
		}
	}
	
	for (sock=node->inputs.first; sock; sock=sock->next)
		if (sock->default_value)
			MEM_freeN(sock->default_value);
	BLI_freelistN(&node->inputs);
	for (sock=node->outputs.first; sock; sock=sock->next)
		if (sock->default_value)
			MEM_freeN(sock->default_value);
	
	BLI_freelistN(&node->outputs);
	
	ntree->update |= NTREE_UPDATE_NODES;
}

/* finds a node based on its name */
bNode *nodeFindNodebyName(bNodeTree *ntree, const char *name)
{
	return BLI_findstring(&ntree->nodes, name, offsetof(bNode, name));
}

/* finds a node based on given socket */
int nodeFindNode(bNodeTree *ntree, bNodeSocket *sock, bNode **nodep, int *sockindex, int *in_out)
{
	bNode *node;
	bNodeSocket *tsock;
	int index= 0;
	
	for(node= ntree->nodes.first; node; node= node->next) {
		for(index=0, tsock= node->inputs.first; tsock; tsock= tsock->next, index++) {
			if(tsock==sock) {
				if (in_out) *in_out= SOCK_IN;
				break;
			}
		}
		if(tsock)
			break;
		for(index=0, tsock= node->outputs.first; tsock; tsock= tsock->next, index++) {
			if(tsock==sock) {
				if (in_out) *in_out= SOCK_OUT;
				break;
			}
		}
		if(tsock)
			break;
	}

	if(node) {
		*nodep= node;
		if(sockindex) *sockindex= index;
		return 1;
	}
	
	*nodep= NULL;
	return 0;
}

/* ************** Add stuff ********** */
static void node_add_sockets_from_type(bNodeTree *ntree, bNode *node, bNodeType *ntype)
{
	bNodeSocketTemplate *sockdef;
	/* bNodeSocket *sock; */ /* UNUSED */

	if(ntype->inputs) {
		sockdef= ntype->inputs;
		while(sockdef->type != -1) {
			/* sock = */ node_add_input_from_template(ntree, node, sockdef);
			
			sockdef++;
		}
	}
	if(ntype->outputs) {
		sockdef= ntype->outputs;
		while(sockdef->type != -1) {
			/* sock = */ node_add_output_from_template(ntree, node, sockdef);
			
			sockdef++;
		}
	}
}

/* Find the first available, non-duplicate name for a given node */
void nodeUniqueName(bNodeTree *ntree, bNode *node)
{
	BLI_uniquename(&ntree->nodes, node, "Node", '.', offsetof(bNode, name), sizeof(node->name));
}

bNode *nodeAddNode(bNodeTree *ntree, struct bNodeTemplate *ntemp)
{
	bNode *node;
	bNodeType *ntype;
	
	ntype= node_get_type(ntree, ntemp->type);
	if(ntype == NULL) {
		printf("nodeAddNodeType() error: '%d' type invalid\n", ntemp->type);
		return NULL;
	}
	/* validity check */
	if (!nodeValid(ntree, ntemp))
		return NULL;
	
	node= MEM_callocN(sizeof(bNode), "new node");
	node->type= ntype->type;
	node->typeinfo= ntype;
	node->flag= NODE_SELECT|ntype->flag;
	node->width= ntype->width;
	node->miniwidth= 42.0f;
	node->height= ntype->height;
	
	node_add_sockets_from_type(ntree, node, ntype);
	
	if(ntype->initfunc!=NULL)
		ntype->initfunc(ntree, node, ntemp);
	
	/* initialize the node name with the node label */
	BLI_strncpy(node->name, nodeLabel(node), NODE_MAXSTR);
	nodeUniqueName(ntree, node);
	
	BLI_addtail(&ntree->nodes, node);
	
	ntree->update |= NTREE_UPDATE_NODES;
	
	return node;
}

void nodeMakeDynamicType(bNode *node)
{
	/* find SH_DYNAMIC_NODE ntype */
	bNodeType *ntype= ntreeGetType(NTREE_SHADER)->node_types.first;
	while(ntype) {
		if(ntype->type==NODE_DYNAMIC)
			break;
		ntype= ntype->next;
	}

	/* make own type struct to fill */
	if(ntype) {
		/*node->typeinfo= MEM_dupallocN(ntype);*/
		bNodeType *newtype= MEM_callocN(sizeof(bNodeType), "dynamic bNodeType");
		*newtype= *ntype;
		strcpy(newtype->name, ntype->name);
		node->typeinfo= newtype;
	}
}

/* keep socket listorder identical, for copying links */
/* ntree is the target tree */
bNode *nodeCopyNode(struct bNodeTree *ntree, struct bNode *node)
{
	bNode *nnode= MEM_callocN(sizeof(bNode), "dupli node");
	bNodeSocket *sock, *oldsock;

	*nnode= *node;
	nodeUniqueName(ntree, nnode);
	
	BLI_addtail(&ntree->nodes, nnode);

	BLI_duplicatelist(&nnode->inputs, &node->inputs);
	oldsock= node->inputs.first;
	for(sock= nnode->inputs.first; sock; sock= sock->next, oldsock= oldsock->next) {
		oldsock->new_sock= sock;
		sock->stack_index= 0;
		
		sock->default_value = (oldsock->default_value ? MEM_dupallocN(oldsock->default_value) : NULL);
		
		/* XXX some compositor node (e.g. image, render layers) still store
		 * some persistent buffer data here, need to clear this to avoid dangling pointers.
		 */
		sock->cache = NULL;
	}
	
	BLI_duplicatelist(&nnode->outputs, &node->outputs);
	oldsock= node->outputs.first;
	for(sock= nnode->outputs.first; sock; sock= sock->next, oldsock= oldsock->next) {
		oldsock->new_sock= sock;
		sock->stack_index= 0;
		
		sock->default_value = (oldsock->default_value ? MEM_dupallocN(oldsock->default_value) : NULL);
		
		/* XXX some compositor node (e.g. image, render layers) still store
		 * some persistent buffer data here, need to clear this to avoid dangling pointers.
		 */
		sock->cache = NULL;
	}
	
	/* don't increase node->id users, freenode doesn't decrement either */
	
	if(node->typeinfo->copystoragefunc)
		node->typeinfo->copystoragefunc(node, nnode);
	
	node->new_node= nnode;
	nnode->new_node= NULL;
	nnode->preview= NULL;
	
	ntree->update |= NTREE_UPDATE_NODES;
	
	return nnode;
}

/* also used via rna api, so we check for proper input output direction */
bNodeLink *nodeAddLink(bNodeTree *ntree, bNode *fromnode, bNodeSocket *fromsock, bNode *tonode, bNodeSocket *tosock)
{
	bNodeSocket *sock;
	bNodeLink *link= NULL; 
	int from= 0, to= 0;
	
	if(fromnode) {
		/* test valid input */
		for(sock= fromnode->outputs.first; sock; sock= sock->next)
			if(sock==fromsock)
				break;
		if(sock)
			from= 1; /* OK */
		else {
			for(sock= fromnode->inputs.first; sock; sock= sock->next)
				if(sock==fromsock)
					break;
			if(sock)
				from= -1; /* OK but flip */
		}
	}
	else {
		/* check tree sockets */
		for(sock= ntree->inputs.first; sock; sock= sock->next)
			if(sock==fromsock)
				break;
		if(sock)
			from= 1; /* OK */
		else {
			for(sock= ntree->outputs.first; sock; sock= sock->next)
				if(sock==fromsock)
					break;
			if(sock)
				from= -1; /* OK but flip */
		}
	}
	if(tonode) {
		for(sock= tonode->inputs.first; sock; sock= sock->next)
			if(sock==tosock)
				break;
		if(sock)
			to= 1; /* OK */
		else {
			for(sock= tonode->outputs.first; sock; sock= sock->next)
				if(sock==tosock)
					break;
			if(sock)
				to= -1; /* OK but flip */
		}
	}
	else {
		/* check tree sockets */
		for(sock= ntree->outputs.first; sock; sock= sock->next)
			if(sock==tosock)
				break;
		if(sock)
			to= 1; /* OK */
		else {
			for(sock= ntree->inputs.first; sock; sock= sock->next)
				if(sock==tosock)
					break;
			if(sock)
				to= -1; /* OK but flip */
		}
	}
	
	if(from >= 0 && to >= 0) {
		link= MEM_callocN(sizeof(bNodeLink), "link");
		BLI_addtail(&ntree->links, link);
		link->fromnode= fromnode;
		link->fromsock= fromsock;
		link->tonode= tonode;
		link->tosock= tosock;
	}
	else if(from <= 0 && to <= 0) {
		link= MEM_callocN(sizeof(bNodeLink), "link");
		BLI_addtail(&ntree->links, link);
		link->fromnode= tonode;
		link->fromsock= tosock;
		link->tonode= fromnode;
		link->tosock= fromsock;
	}
	
	ntree->update |= NTREE_UPDATE_LINKS;
	
	return link;
}

void nodeRemLink(bNodeTree *ntree, bNodeLink *link)
{
	BLI_remlink(&ntree->links, link);
	if(link->tosock)
		link->tosock->link= NULL;
	MEM_freeN(link);
	
	ntree->update |= NTREE_UPDATE_LINKS;
}

void nodeRemSocketLinks(bNodeTree *ntree, bNodeSocket *sock)
{
	bNodeLink *link, *next;
	
	for(link= ntree->links.first; link; link= next) {
		next= link->next;
		if(link->fromsock==sock || link->tosock==sock) {
			nodeRemLink(ntree, link);
		}
	}
	
	ntree->update |= NTREE_UPDATE_LINKS;
}

/* transforms node location to area coords */
void nodeSpaceCoords(bNode *node, float *locx, float *locy)
{
	if (node->parent) {
		nodeSpaceCoords(node->parent, locx, locy);
		*locx += node->locx;
		*locy += node->locy;
	}
	else {
		*locx = node->locx;
		*locy = node->locy;
	}
}

void nodeAttachNode(bNode *node, bNode *parent)
{
	float parentx, parenty;
	
	node->parent = parent;
	/* transform to parent space */
	nodeSpaceCoords(parent, &parentx, &parenty);
	node->locx -= parentx;
	node->locy -= parenty;
}

void nodeDetachNode(struct bNode *node)
{
	float parentx, parenty;
	
	if (node->parent) {
		/* transform to "global" (area) space */
		nodeSpaceCoords(node->parent, &parentx, &parenty);
		node->locx += parentx;
		node->locy += parenty;
		node->parent = NULL;
	}
}

bNodeTree *ntreeAddTree(const char *name, int type, int nodetype)
{
	bNodeTree *ntree;
	bNodeType *ntype;
	
	/* trees are created as local trees if they of compositor, material or texture type,
	 * node groups and other tree types are created as library data.
	 */
	if (ELEM3(type, NTREE_COMPOSIT, NTREE_SHADER, NTREE_TEXTURE) && nodetype==0) {
		ntree= MEM_callocN(sizeof(bNodeTree), "new node tree");
		*( (short *)ntree->id.name )= ID_NT; /* not "type", as that is ntree->type */
		BLI_strncpy(ntree->id.name+2, name, sizeof(ntree->id.name));
	}
	else
		ntree= alloc_libblock(&G.main->nodetree, ID_NT, name);
	
	ntree->type= type;
	ntree->nodetype = nodetype;
	
	ntreeInitTypes(ntree);
	
	ntype = node_get_type(ntree, ntree->nodetype);
	if (ntype && ntype->inittreefunc)
		ntype->inittreefunc(ntree);
	
	return ntree;
}

/* Warning: this function gets called during some rather unexpected times
 *	- this gets called when executing compositing updates (for threaded previews)
 *	- when the nodetree datablock needs to be copied (i.e. when users get copied)
 *	- for scene duplication use ntreeSwapID() after so we dont have stale pointers.
 */
bNodeTree *ntreeCopyTree(bNodeTree *ntree)
{
	bNodeTree *newtree;
	bNode *node /*, *nnode */ /* UNUSED */, *last;
	bNodeLink *link;
	bNodeSocket *gsock, *oldgsock;
	
	if(ntree==NULL) return NULL;
	
	/* is ntree part of library? */
	for(newtree=G.main->nodetree.first; newtree; newtree= newtree->id.next)
		if(newtree==ntree) break;
	if(newtree) {
		newtree= copy_libblock(ntree);
	} else {
		newtree= MEM_dupallocN(ntree);
		copy_libblock_data(&newtree->id, &ntree->id, TRUE); /* copy animdata and ID props */
	}

	id_us_plus((ID *)newtree->gpd);

	/* in case a running nodetree is copied */
	newtree->execdata= NULL;
	
	newtree->nodes.first= newtree->nodes.last= NULL;
	newtree->links.first= newtree->links.last= NULL;
	
	last = ntree->nodes.last;
	for(node= ntree->nodes.first; node; node= node->next) {
		node->new_node= NULL;
		/* nnode= */ nodeCopyNode(newtree, node);	/* sets node->new */
		
		/* make sure we don't copy new nodes again! */
		if (node==last)
			break;
	}
	
	/* socket definition for group usage */
	BLI_duplicatelist(&newtree->inputs, &ntree->inputs);
	for(gsock= newtree->inputs.first, oldgsock= ntree->inputs.first; gsock; gsock=gsock->next, oldgsock=oldgsock->next) {
		oldgsock->new_sock= gsock;
		gsock->groupsock = (oldgsock->groupsock ? oldgsock->groupsock->new_sock : NULL);
		gsock->default_value = (oldgsock->default_value ? MEM_dupallocN(oldgsock->default_value) : NULL);
	}
	BLI_duplicatelist(&newtree->outputs, &ntree->outputs);
	for(gsock= newtree->outputs.first, oldgsock= ntree->outputs.first; gsock; gsock=gsock->next, oldgsock=oldgsock->next) {
		oldgsock->new_sock= gsock;
		gsock->groupsock = (oldgsock->groupsock ? oldgsock->groupsock->new_sock : NULL);
		gsock->default_value = (oldgsock->default_value ? MEM_dupallocN(oldgsock->default_value) : NULL);
	}
	
	/* copy links */
	BLI_duplicatelist(&newtree->links, &ntree->links);
	for(link= newtree->links.first; link; link= link->next) {
		link->fromnode = (link->fromnode ? link->fromnode->new_node : NULL);
		link->fromsock = (link->fromsock ? link->fromsock->new_sock : NULL);
		link->tonode = (link->tonode ? link->tonode->new_node : NULL);
		link->tosock = (link->tosock ? link->tosock->new_sock : NULL);
		/* update the link socket's pointer */
		if (link->tosock)
			link->tosock->link = link;
	}
	
	/* update node->parent pointers */
	for (node=newtree->nodes.first; node; node=node->next) {
		if (node->parent)
			node->parent = node->parent->new_node;
	}
	
	return newtree;
}

/* use when duplicating scenes */
void ntreeSwitchID(bNodeTree *ntree, ID *id_from, ID *id_to)
{
	bNode *node;
	/* for scene duplication only */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->id==id_from) {
			node->id= id_to;
		}
	}
}

/* *************** preview *********** */
/* if node->preview, then we assume the rect to exist */

void nodeFreePreview(bNode *node)
{
	if(node->preview) {
		if(node->preview->rect)
			MEM_freeN(node->preview->rect);
		MEM_freeN(node->preview);
		node->preview= NULL;
	}	
}

static void node_init_preview(bNode *node, int xsize, int ysize)
{
	
	if(node->preview==NULL) {
		node->preview= MEM_callocN(sizeof(bNodePreview), "node preview");
		//		printf("added preview %s\n", node->name);
	}
	
	/* node previews can get added with variable size this way */
	if(xsize==0 || ysize==0)
		return;
	
	/* sanity checks & initialize */
	if(node->preview->rect) {
		if(node->preview->xsize!=xsize && node->preview->ysize!=ysize) {
			MEM_freeN(node->preview->rect);
			node->preview->rect= NULL;
		}
	}
	
	if(node->preview->rect==NULL) {
		node->preview->rect= MEM_callocN(4*xsize + xsize*ysize*sizeof(char)*4, "node preview rect");
		node->preview->xsize= xsize;
		node->preview->ysize= ysize;
	}
	/* no clear, makes nicer previews */
}

void ntreeInitPreview(bNodeTree *ntree, int xsize, int ysize)
{
	bNode *node;
	
	if(ntree==NULL)
		return;
	
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->typeinfo->flag & NODE_PREVIEW)	/* hrms, check for closed nodes? */
			node_init_preview(node, xsize, ysize);
		if(node->type==NODE_GROUP && (node->flag & NODE_GROUP_EDIT))
			ntreeInitPreview((bNodeTree *)node->id, xsize, ysize);
	}		
}

static void nodeClearPreview(bNode *node)
{
	if(node->preview && node->preview->rect)
		memset(node->preview->rect, 0, MEM_allocN_len(node->preview->rect));
}

/* use it to enforce clear */
void ntreeClearPreview(bNodeTree *ntree)
{
	bNode *node;
	
	if(ntree==NULL)
		return;
	
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->typeinfo->flag & NODE_PREVIEW)
			nodeClearPreview(node);
		if(node->type==NODE_GROUP && (node->flag & NODE_GROUP_EDIT))
			ntreeClearPreview((bNodeTree *)node->id);
	}		
}

/* hack warning! this function is only used for shader previews, and 
since it gets called multiple times per pixel for Ztransp we only
add the color once. Preview gets cleared before it starts render though */
void nodeAddToPreview(bNode *node, float *col, int x, int y, int do_manage)
{
	bNodePreview *preview= node->preview;
	if(preview) {
		if(x>=0 && y>=0) {
			if(x<preview->xsize && y<preview->ysize) {
				unsigned char *tar= preview->rect+ 4*((preview->xsize*y) + x);
				
				if(do_manage) {
					tar[0]= FTOCHAR(linearrgb_to_srgb(col[0]));
					tar[1]= FTOCHAR(linearrgb_to_srgb(col[1]));
					tar[2]= FTOCHAR(linearrgb_to_srgb(col[2]));
				}
				else {
					tar[0]= FTOCHAR(col[0]);
					tar[1]= FTOCHAR(col[1]);
					tar[2]= FTOCHAR(col[2]);
				}
				tar[3]= FTOCHAR(col[3]);
			}
			//else printf("prv out bound x y %d %d\n", x, y);
		}
		//else printf("prv out bound x y %d %d\n", x, y);
	}
}

/* ************** Free stuff ********** */

/* goes over entire tree */
void nodeUnlinkNode(bNodeTree *ntree, bNode *node)
{
	bNodeLink *link, *next;
	bNodeSocket *sock;
	ListBase *lb;
	
	for(link= ntree->links.first; link; link= next) {
		next= link->next;
		
		if(link->fromnode==node) {
			lb= &node->outputs;
			if (link->tonode)
				NodeTagChanged(ntree, link->tonode);
		}
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
				nodeRemLink(ntree, link);
			}
		}
	}
}

static void node_unlink_attached(bNodeTree *ntree, bNode *parent)
{
	bNode *node;
	for (node=ntree->nodes.first; node; node=node->next) {
		if (node->parent == parent)
			nodeDetachNode(node);
	}
}

void nodeFreeNode(bNodeTree *ntree, bNode *node)
{
	bNodeTreeType *treetype= ntreeGetType(ntree->type);
	bNodeSocket *sock, *nextsock;
	
	/* remove all references to this node */
	nodeUnlinkNode(ntree, node);
	node_unlink_attached(ntree, node);
	
	BLI_remlink(&ntree->nodes, node);

	/* since it is called while free database, node->id is undefined */
	
	if (treetype->free_node_cache)
		treetype->free_node_cache(ntree, node);
	
	for (sock=node->inputs.first; sock; sock = nextsock) {
		nextsock = sock->next;
		if (sock->default_value)
			MEM_freeN(sock->default_value);
		MEM_freeN(sock);
	}
	for (sock=node->outputs.first; sock; sock = nextsock) {
		nextsock = sock->next;
		if (sock->default_value)
			MEM_freeN(sock->default_value);
		MEM_freeN(sock);
	}

	nodeFreePreview(node);

	if(node->typeinfo && node->typeinfo->freestoragefunc) {
		node->typeinfo->freestoragefunc(node);
	}

	MEM_freeN(node);
	
	ntree->update |= NTREE_UPDATE_NODES;
}

/* do not free ntree itself here, free_libblock calls this function too */
void ntreeFreeTree(bNodeTree *ntree)
{
	bNode *node, *next;
	bNodeSocket *sock;
	
	if(ntree==NULL) return;
	
	/* XXX hack! node trees should not store execution graphs at all.
	 * This should be removed when old tree types no longer require it.
	 * Currently the execution data for texture nodes remains in the tree
	 * after execution, until the node tree is updated or freed.
	 */
	if (ntree->execdata) {
		switch (ntree->type) {
		case NTREE_COMPOSIT:
			ntreeCompositEndExecTree(ntree->execdata, 1);
			break;
		case NTREE_SHADER:
			ntreeShaderEndExecTree(ntree->execdata, 1);
			break;
		case NTREE_TEXTURE:
			ntreeTexEndExecTree(ntree->execdata, 1);
			break;
		}
	}
	
	BKE_free_animdata((ID *)ntree);
	
	id_us_min((ID *)ntree->gpd);

	BLI_freelistN(&ntree->links);	/* do first, then unlink_node goes fast */
	
	for(node= ntree->nodes.first; node; node= next) {
		next= node->next;
		nodeFreeNode(ntree, node);
	}
	
	for (sock=ntree->inputs.first; sock; sock=sock->next)
		if (sock->default_value)
			MEM_freeN(sock->default_value);
	BLI_freelistN(&ntree->inputs);
	for (sock=ntree->outputs.first; sock; sock=sock->next)
		if (sock->default_value)
			MEM_freeN(sock->default_value);
	BLI_freelistN(&ntree->outputs);
}

void ntreeFreeCache(bNodeTree *ntree)
{
	bNodeTreeType *treetype;
	
	if(ntree==NULL) return;
	
	treetype= ntreeGetType(ntree->type);
	if (treetype->free_cache)
		treetype->free_cache(ntree);
}

void ntreeSetOutput(bNodeTree *ntree)
{
	bNode *node;

	/* find the active outputs, might become tree type dependant handler */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->typeinfo->nclass==NODE_CLASS_OUTPUT) {
			bNode *tnode;
			int output= 0;
			
			/* we need a check for which output node should be tagged like this, below an exception */
			if(node->type==CMP_NODE_OUTPUT_FILE)
			   continue;
			   
			/* there is more types having output class, each one is checked */
			for(tnode= ntree->nodes.first; tnode; tnode= tnode->next) {
				if(tnode->typeinfo->nclass==NODE_CLASS_OUTPUT) {
					
					if(ntree->type==NTREE_COMPOSIT) {
							
						/* same type, exception for viewer */
						if(tnode->type==node->type ||
						   (ELEM(tnode->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER) &&
							ELEM(node->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER))) {
							if(tnode->flag & NODE_DO_OUTPUT) {
								output++;
								if(output>1)
									tnode->flag &= ~NODE_DO_OUTPUT;
							}
						}
					}
					else {
						/* same type */
						if(tnode->type==node->type) {
							if(tnode->flag & NODE_DO_OUTPUT) {
								output++;
								if(output>1)
									tnode->flag &= ~NODE_DO_OUTPUT;
							}
						}
					}
				}
			}
			if(output==0)
				node->flag |= NODE_DO_OUTPUT;
		}
	}
	
	/* here we could recursively set which nodes have to be done,
		might be different for editor or for "real" use... */
}

typedef struct MakeLocalCallData {
	ID *group_id;
	ID *new_id;
	int lib, local;
} MakeLocalCallData;

static void ntreeMakeLocal_CheckLocal(void *calldata, ID *owner_id, bNodeTree *ntree)
{
	MakeLocalCallData *cd= (MakeLocalCallData*)calldata;
	bNode *node;
	
	/* find if group is in tree */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->id == cd->group_id) {
			if(owner_id->lib) cd->lib= 1;
			else cd->local= 1;
		}
	}
}

static void ntreeMakeLocal_LinkNew(void *calldata, ID *owner_id, bNodeTree *ntree)
{
	MakeLocalCallData *cd= (MakeLocalCallData*)calldata;
	bNode *node;
	
	/* find if group is in tree */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->id == cd->group_id) {
			if(owner_id->lib==NULL) {
				node->id= cd->new_id;
				cd->new_id->us++;
				cd->group_id->us--;
			}
		}
	}
}

void ntreeMakeLocal(bNodeTree *ntree)
{
	bNodeTreeType *treetype= ntreeGetType(ntree->type);
	MakeLocalCallData cd;
	
	/* - only lib users: do nothing
		* - only local users: set flag
		* - mixed: make copy
		*/
	
	if(ntree->id.lib==NULL) return;
	if(ntree->id.us==1) {
		ntree->id.lib= NULL;
		ntree->id.flag= LIB_LOCAL;
		new_id(NULL, (ID *)ntree, NULL);
		return;
	}
	
	/* now check users of groups... again typedepending, callback... */
	cd.group_id = &ntree->id;
	cd.new_id = NULL;
	cd.local = 0;
	cd.lib = 0;
	
	treetype->foreach_nodetree(G.main, &cd, &ntreeMakeLocal_CheckLocal);
	
	/* if all users are local, we simply make tree local */
	if(cd.local && cd.lib==0) {
		ntree->id.lib= NULL;
		ntree->id.flag= LIB_LOCAL;
		new_id(NULL, (ID *)ntree, NULL);
	}
	else if(cd.local && cd.lib) {
		/* this is the mixed case, we copy the tree and assign it to local users */
		bNodeTree *newtree= ntreeCopyTree(ntree);
		
		newtree->id.us= 0;
		

		cd.new_id = &newtree->id;
		treetype->foreach_nodetree(G.main, &cd, &ntreeMakeLocal_LinkNew);
	}
}

int ntreeNodeExists(bNodeTree *ntree, bNode *testnode)
{
	bNode *node= ntree->nodes.first;
	for(; node; node= node->next)
		if(node==testnode)
			return 1;
	return 0;
}

int ntreeOutputExists(bNode *node, bNodeSocket *testsock)
{
	bNodeSocket *sock= node->outputs.first;
	for(; sock; sock= sock->next)
		if(sock==testsock)
			return 1;
	return 0;
}

/* returns localized tree for execution in threads */
bNodeTree *ntreeLocalize(bNodeTree *ntree)
{
	bNodeTreeType *ntreetype= ntreeGetType(ntree->type);

	bNodeTree *ltree;
	bNode *node;
	
	bAction *action_backup= NULL, *tmpact_backup= NULL;
	
	/* Workaround for copying an action on each render!
	 * set action to NULL so animdata actions dont get copied */
	AnimData *adt= BKE_animdata_from_id(&ntree->id);

	if(adt) {
		action_backup= adt->action;
		tmpact_backup= adt->tmpact;

		adt->action= NULL;
		adt->tmpact= NULL;
	}

	/* node copy func */
	ltree= ntreeCopyTree(ntree);

	if(adt) {
		AnimData *ladt= BKE_animdata_from_id(&ltree->id);

		adt->action= ladt->action= action_backup;
		adt->tmpact= ladt->tmpact= tmpact_backup;

		if(action_backup) action_backup->id.us++;
		if(tmpact_backup) tmpact_backup->id.us++;
		
	}
	/* end animdata uglyness */

	/* ensures only a single output node is enabled */
	ntreeSetOutput(ntree);

	for(node= ntree->nodes.first; node; node= node->next) {
		/* store new_node pointer to original */
		node->new_node->new_node= node;
	}

	if (ntreetype->localize)
		ntreetype->localize(ltree, ntree);

	return ltree;
}

/* sync local composite with real tree */
/* local tree is supposed to be running, be careful moving previews! */
/* is called by jobs manager, outside threads, so it doesnt happen during draw */
void ntreeLocalSync(bNodeTree *localtree, bNodeTree *ntree)
{
	bNodeTreeType *ntreetype= ntreeGetType(ntree->type);

	if (ntreetype->local_sync)
		ntreetype->local_sync(localtree, ntree);
}

/* merge local tree results back, and free local tree */
/* we have to assume the editor already changed completely */
void ntreeLocalMerge(bNodeTree *localtree, bNodeTree *ntree)
{
	bNodeTreeType *ntreetype= ntreeGetType(ntree->type);
	bNode *lnode;
	
	/* move over the compbufs and previews */
	for(lnode= localtree->nodes.first; lnode; lnode= lnode->next) {
		if(ntreeNodeExists(ntree, lnode->new_node)) {
			if(lnode->preview && lnode->preview->rect) {
				nodeFreePreview(lnode->new_node);
				lnode->new_node->preview= lnode->preview;
				lnode->preview= NULL;
			}
		}
	}

	if (ntreetype->local_merge)
		ntreetype->local_merge(localtree, ntree);

	ntreeFreeTree(localtree);
	MEM_freeN(localtree);
}

/* ************ find stuff *************** */

int ntreeHasType(bNodeTree *ntree, int type)
{
	bNode *node;
	
	if(ntree)
		for(node= ntree->nodes.first; node; node= node->next)
			if(node->type == type)
				return 1;
	return 0;
}

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

bNode *nodeGetActive(bNodeTree *ntree)
{
	bNode *node;
	
	if(ntree==NULL) return NULL;
	
	for(node= ntree->nodes.first; node; node= node->next)
		if(node->flag & NODE_ACTIVE)
			break;
	return node;
}

/* two active flags, ID nodes have special flag for buttons display */
bNode *nodeGetActiveID(bNodeTree *ntree, short idtype)
{
	bNode *node;
	
	if(ntree==NULL) return NULL;

	/* check for group edit */
	for(node= ntree->nodes.first; node; node= node->next)
		if(node->flag & NODE_GROUP_EDIT)
			break;

	if(node)
		ntree= (bNodeTree*)node->id;
	
	/* now find active node with this id */
	for(node= ntree->nodes.first; node; node= node->next)
		if(node->id && GS(node->id->name)==idtype)
			if(node->flag & NODE_ACTIVE_ID)
				break;

	return node;
}

int nodeSetActiveID(bNodeTree *ntree, short idtype, ID *id)
{
	bNode *node;
	int ok= FALSE;

	if(ntree==NULL) return ok;

	/* check for group edit */
	for(node= ntree->nodes.first; node; node= node->next)
		if(node->flag & NODE_GROUP_EDIT)
			break;

	if(node)
		ntree= (bNodeTree*)node->id;

	/* now find active node with this id */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->id && GS(node->id->name)==idtype) {
			if(id && ok==FALSE && node->id==id) {
				node->flag |= NODE_ACTIVE_ID;
				ok= TRUE;
			} else {
				node->flag &= ~NODE_ACTIVE_ID;
			}
		}
	}

	return ok;
}


/* two active flags, ID nodes have special flag for buttons display */
void nodeClearActiveID(bNodeTree *ntree, short idtype)
{
	bNode *node;
	
	if(ntree==NULL) return;
	
	for(node= ntree->nodes.first; node; node= node->next)
		if(node->id && GS(node->id->name)==idtype)
			node->flag &= ~NODE_ACTIVE_ID;
}

/* two active flags, ID nodes have special flag for buttons display */
void nodeSetActive(bNodeTree *ntree, bNode *node)
{
	bNode *tnode;
	
	/* make sure only one node is active, and only one per ID type */
	for(tnode= ntree->nodes.first; tnode; tnode= tnode->next) {
		tnode->flag &= ~NODE_ACTIVE;
		
		if(node->id && tnode->id) {
			if(GS(node->id->name) == GS(tnode->id->name))
				tnode->flag &= ~NODE_ACTIVE_ID;
		}
	}
	
	node->flag |= NODE_ACTIVE;
	if(node->id)
		node->flag |= NODE_ACTIVE_ID;
}

/* use flags are not persistant yet, groups might need different tagging, so we do it each time
   when we need to get this info */
void ntreeSocketUseFlags(bNodeTree *ntree)
{
	bNode *node;
	bNodeSocket *sock;
	bNodeLink *link;
	
	/* clear flags */
	for(node= ntree->nodes.first; node; node= node->next) {
		for(sock= node->inputs.first; sock; sock= sock->next)
			sock->flag &= ~SOCK_IN_USE;
		for(sock= node->outputs.first; sock; sock= sock->next)
			sock->flag &= ~SOCK_IN_USE;
	}
	
	/* tag all thats in use */
	for(link= ntree->links.first; link; link= link->next) {
	
		if(link->fromsock) // FIXME, see below
			link->fromsock->flag |= SOCK_IN_USE;
		if(link->tosock) // FIXME This can be NULL, when dragging a new link in the UI, should probably copy the node tree for preview render - campbell
			link->tosock->flag |= SOCK_IN_USE;
	}
}

/* ************** dependency stuff *********** */

/* node is guaranteed to be not checked before */
static int node_get_deplist_recurs(bNode *node, bNode ***nsort)
{
	bNode *fromnode;
	bNodeSocket *sock;
	int level = 0xFFF;
	
	node->done= 1;
	
	/* check linked nodes */
	for(sock= node->inputs.first; sock; sock= sock->next) {
		if(sock->link) {
			fromnode= sock->link->fromnode;
			if(fromnode) {
				if (fromnode->done==0)
					fromnode->level= node_get_deplist_recurs(fromnode, nsort);
				if (fromnode->level <= level)
					level = fromnode->level - 1;
			}
		}
	}
	
	/* check parent node */
	if (node->parent) {
		if (node->parent->done==0)
			node->parent->level= node_get_deplist_recurs(node->parent, nsort);
		if (node->parent->level <= level)
			level = node->parent->level - 1;
	}
	
	if (nsort) {
		**nsort= node;
		(*nsort)++;
	}
	
	return level;
}

void ntreeGetDependencyList(struct bNodeTree *ntree, struct bNode ***deplist, int *totnodes)
{
	bNode *node, **nsort;
	
	*totnodes=0;
	
	/* first clear data */
	for(node= ntree->nodes.first; node; node= node->next) {
		node->done= 0;
		(*totnodes)++;
	}
	if(*totnodes==0) {
		*deplist = NULL;
		return;
	}
	
	nsort= *deplist= MEM_callocN((*totnodes)*sizeof(bNode*), "sorted node array");
	
	/* recursive check */
	for(node= ntree->nodes.first; node; node= node->next) {
		if(node->done==0) {
			node->level= node_get_deplist_recurs(node, &nsort);
		}
	}
}

static void ntree_update_link_pointers(bNodeTree *ntree)
{
	bNode *node;
	bNodeSocket *sock;
	bNodeLink *link;
	
	/* first clear data */
	for(node= ntree->nodes.first; node; node= node->next) {
		for(sock= node->inputs.first; sock; sock= sock->next)
			sock->link= NULL;
	}
	/* clear socket links */
	for(sock= ntree->outputs.first; sock; sock= sock->next)
		sock->link= NULL;

	for(link= ntree->links.first; link; link= link->next) {
		if (link->tosock)
			link->tosock->link= link;
	}
}

static void ntree_validate_links(bNodeTree *ntree)
{
	bNodeTreeType *ntreetype = ntreeGetType(ntree->type);
	bNodeLink *link;
	
	for (link = ntree->links.first; link; link = link->next) {
		link->flag |= NODE_LINK_VALID;
		if (link->fromnode && link->tonode && link->fromnode->level <= link->tonode->level)
			link->flag &= ~NODE_LINK_VALID;
		else if (ntreetype->validate_link) {
			if (!ntreetype->validate_link(ntree, link))
				link->flag &= ~NODE_LINK_VALID;
		}
	}
}

static void ntree_verify_nodes_cb(void *calldata, struct ID *UNUSED(owner_id), struct bNodeTree *ntree)
{
	ID *id= (ID*)calldata;
	bNode *node;
	
	for (node=ntree->nodes.first; node; node=node->next)
		if (node->typeinfo->verifyfunc)
			node->typeinfo->verifyfunc(ntree, node, id);
}

void ntreeVerifyNodes(struct Main *main, struct ID *id)
{
	bNodeTreeType *ntreetype;
	bNodeTree *ntree;
	int n;
	
	for (n=0; n < NUM_NTREE_TYPES; ++n) {
		ntreetype= ntreeGetType(n);
		if (ntreetype && ntreetype->foreach_nodetree)
			ntreetype->foreach_nodetree(main, id, ntree_verify_nodes_cb);
	}
	for (ntree=main->nodetree.first; ntree; ntree=ntree->id.next)
		ntree_verify_nodes_cb(id, NULL, ntree);
}

void ntreeUpdateTree(bNodeTree *ntree)
{
	bNodeTreeType *ntreetype= ntreeGetType(ntree->type);
	bNode *node;
	bNode **deplist;
	int totnodes, n;
	
	ntree_update_link_pointers(ntree);
	
	/* also updates the node level! */
	ntreeGetDependencyList(ntree, &deplist, &totnodes);
	
	if (deplist) {
		/* update individual nodes */
		for (n=0; n < totnodes; ++n) {
			node = deplist[n];
			if (ntreetype->update_node)
				ntreetype->update_node(ntree, node);
			else if (node->typeinfo->updatefunc)
				node->typeinfo->updatefunc(ntree, node);
		}
		
		MEM_freeN(deplist);
		
		/* ensures only a single output node is enabled, texnode allows multiple though */
		if(ntree->type!=NTREE_TEXTURE)
			ntreeSetOutput(ntree);
		
	}
	
	/* general tree updates */
	if (ntree->update & (NTREE_UPDATE_LINKS|NTREE_UPDATE_NODES)) {
		ntree_validate_links(ntree);
	}
	
	/* update tree */
	if (ntreetype->update)
		ntreetype->update(ntree);
	else {
		bNodeType *ntype= node_get_type(ntree, ntree->nodetype);
		if (ntype && ntype->updatetreefunc)
			ntype->updatetreefunc(ntree);
	}
	
	/* XXX hack, should be done by depsgraph!! */
	ntreeVerifyNodes(G.main, &ntree->id);
	
	/* clear the update flag */
	ntree->update = 0;
}

void NodeTagChanged(bNodeTree *ntree, bNode *node)
{
	bNodeTreeType *ntreetype = ntreeGetType(ntree->type);
	
	/* extra null pointer checks here because this is called when unlinking
	   unknown nodes on file load, so typeinfo pointers may not be set */
	if (ntreetype && ntreetype->update_node)
		ntreetype->update_node(ntree, node);
	else if (node->typeinfo && node->typeinfo->updatefunc)
		node->typeinfo->updatefunc(ntree, node);
}

int NodeTagIDChanged(bNodeTree *ntree, ID *id)
{
	bNodeTreeType *ntreetype;
	bNode *node;
	int change = FALSE;

	if(ELEM(NULL, id, ntree))
		return change;
	
	ntreetype = ntreeGetType(ntree->type);
	
	if (ntreetype->update_node) {
		for(node= ntree->nodes.first; node; node= node->next) {
			if(node->id==id) {
				change = TRUE;
				ntreetype->update_node(ntree, node);
			}
		}
	}
	else {
		for(node= ntree->nodes.first; node; node= node->next) {
			if(node->id==id) {
				change = TRUE;
				if (node->typeinfo->updatefunc)
					node->typeinfo->updatefunc(ntree, node);
			}
		}
	}
	
	return change;
}


/* ************* node type access ********** */

int nodeValid(bNodeTree *ntree, bNodeTemplate *ntemp)
{
	bNodeType *ntype= node_get_type(ntree, ntemp->type);
	if (ntype) {
		if (ntype->validfunc)
			return ntype->validfunc(ntree, ntemp);
		else
			return 1;
	}
	else
		return 0;
}

const char* nodeLabel(bNode *node)
{
	if (node->label[0]!='\0')
		return node->label;
	else if (node->typeinfo->labelfunc)
		return node->typeinfo->labelfunc(node);
	else
		return node->typeinfo->name;
}

struct bNodeTree *nodeGroupEditGet(struct bNode *node)
{
	if (node->typeinfo->group_edit_get)
		return node->typeinfo->group_edit_get(node);
	else
		return NULL;
}

struct bNodeTree *nodeGroupEditSet(struct bNode *node, int edit)
{
	if (node->typeinfo->group_edit_set)
		return node->typeinfo->group_edit_set(node, edit);
	else if (node->typeinfo->group_edit_get)
		return node->typeinfo->group_edit_get(node);
	else
		return NULL;
}

void nodeGroupEditClear(struct bNode *node)
{
	if (node->typeinfo->group_edit_clear)
		node->typeinfo->group_edit_clear(node);
}

struct bNodeTemplate nodeMakeTemplate(struct bNode *node)
{
	bNodeTemplate ntemp;
	if (node->typeinfo->templatefunc)
		return node->typeinfo->templatefunc(node);
	else {
		ntemp.type = node->type;
		return ntemp;
	}
}

void node_type_base(bNodeType *ntype, int type, const char *name, short nclass, short flag)
{
	memset(ntype, 0, sizeof(bNodeType));
	
	ntype->type = type;
	BLI_strncpy(ntype->name, name, sizeof(ntype->name));
	ntype->nclass = nclass;
	ntype->flag = flag;
	
	/* default size values */
	ntype->width = 140;
	ntype->minwidth = 100;
	ntype->maxwidth = 320;
	ntype->height = 100;
	ntype->minheight = 30;
	ntype->maxheight = FLT_MAX;
}

void node_type_socket_templates(struct bNodeType *ntype, struct bNodeSocketTemplate *inputs, struct bNodeSocketTemplate *outputs)
{
	ntype->inputs = inputs;
	ntype->outputs = outputs;
}

void node_type_init(struct bNodeType *ntype, void (*initfunc)(struct bNodeTree *ntree, struct bNode *node, struct bNodeTemplate *ntemp))
{
	ntype->initfunc = initfunc;
}

void node_type_valid(struct bNodeType *ntype, int (*validfunc)(struct bNodeTree *ntree, struct bNodeTemplate *ntemp))
{
	ntype->validfunc = validfunc;
}

void node_type_size(struct bNodeType *ntype, int width, int minwidth, int maxwidth)
{
	ntype->width = width;
	ntype->minwidth = minwidth;
	if (maxwidth <= minwidth)
		ntype->maxwidth = FLT_MAX;
	else
		ntype->maxwidth = maxwidth;
}

void node_type_storage(bNodeType *ntype, const char *storagename, void (*freestoragefunc)(struct bNode *), void (*copystoragefunc)(struct bNode *, struct bNode *))
{
	if (storagename)
		BLI_strncpy(ntype->storagename, storagename, sizeof(ntype->storagename));
	else
		ntype->storagename[0] = '\0';
	ntype->copystoragefunc = copystoragefunc;
	ntype->freestoragefunc = freestoragefunc;
}

void node_type_label(struct bNodeType *ntype, const char *(*labelfunc)(struct bNode *))
{
	ntype->labelfunc = labelfunc;
}

void node_type_template(struct bNodeType *ntype, struct bNodeTemplate (*templatefunc)(struct bNode *))
{
	ntype->templatefunc = templatefunc;
}

void node_type_update(struct bNodeType *ntype,
					  void (*updatefunc)(struct bNodeTree *ntree, struct bNode *node),
					  void (*verifyfunc)(struct bNodeTree *ntree, struct bNode *node, struct ID *id))
{
	ntype->updatefunc = updatefunc;
	ntype->verifyfunc = verifyfunc;
}

void node_type_tree(struct bNodeType *ntype, void (*inittreefunc)(struct bNodeTree *), void (*updatetreefunc)(struct bNodeTree *))
{
	ntype->inittreefunc = inittreefunc;
	ntype->updatetreefunc = updatetreefunc;
}

void node_type_group_edit(struct bNodeType *ntype,
						  struct bNodeTree *(*group_edit_get)(struct bNode *node),
						  struct bNodeTree *(*group_edit_set)(struct bNode *node, int edit),
						  void (*group_edit_clear)(struct bNode *node))
{
	ntype->group_edit_get = group_edit_get;
	ntype->group_edit_set = group_edit_set;
	ntype->group_edit_clear = group_edit_clear;
}

void node_type_exec(struct bNodeType *ntype, void (*execfunc)(void *data, struct bNode *, struct bNodeStack **, struct bNodeStack **))
{
	ntype->execfunc = execfunc;
}

void node_type_exec_new(struct bNodeType *ntype,
						void *(*initexecfunc)(struct bNode *node),
						void (*freeexecfunc)(struct bNode *node, void *nodedata),
						void (*newexecfunc)(void *data, int thread, struct bNode *, void *nodedata, struct bNodeStack **, struct bNodeStack **))
{
	ntype->initexecfunc = initexecfunc;
	ntype->freeexecfunc = freeexecfunc;
	ntype->newexecfunc = newexecfunc;
}

void node_type_gpu(struct bNodeType *ntype, int (*gpufunc)(struct GPUMaterial *mat, struct bNode *node, struct GPUNodeStack *in, struct GPUNodeStack *out))
{
	ntype->gpufunc = gpufunc;
}

void node_type_gpu_ext(struct bNodeType *ntype, int (*gpuextfunc)(struct GPUMaterial *mat, struct bNode *node, void *nodedata, struct GPUNodeStack *in, struct GPUNodeStack *out))
{
	ntype->gpuextfunc = gpuextfunc;
}


static bNodeType *is_nodetype_registered(ListBase *typelist, int type) 
{
	bNodeType *ntype= typelist->first;
	
	for(;ntype; ntype= ntype->next )
		if(ntype->type==type)
			return ntype;
	
	return NULL;
}

void nodeRegisterType(ListBase *typelist, bNodeType *ntype) 
{
	bNodeType *found= is_nodetype_registered(typelist, ntype->type);
	
	if(found==NULL)
		BLI_addtail(typelist, ntype);
}

static void registerCompositNodes(ListBase *ntypelist)
{
	register_node_type_frame(ntypelist);
	
	register_node_type_cmp_group(ntypelist);
//	register_node_type_cmp_forloop(ntypelist);
//	register_node_type_cmp_whileloop(ntypelist);
	
	register_node_type_cmp_rlayers(ntypelist);
	register_node_type_cmp_image(ntypelist);
	register_node_type_cmp_texture(ntypelist);
	register_node_type_cmp_value(ntypelist);
	register_node_type_cmp_rgb(ntypelist);
	register_node_type_cmp_curve_time(ntypelist);
	register_node_type_cmp_movieclip(ntypelist);
	
	register_node_type_cmp_composite(ntypelist);
	register_node_type_cmp_viewer(ntypelist);
	register_node_type_cmp_splitviewer(ntypelist);
	register_node_type_cmp_output_file(ntypelist);
	register_node_type_cmp_view_levels(ntypelist);
	
	register_node_type_cmp_curve_rgb(ntypelist);
	register_node_type_cmp_mix_rgb(ntypelist);
	register_node_type_cmp_hue_sat(ntypelist);
	register_node_type_cmp_brightcontrast(ntypelist);
	register_node_type_cmp_gamma(ntypelist);
	register_node_type_cmp_invert(ntypelist);
	register_node_type_cmp_alphaover(ntypelist);
	register_node_type_cmp_zcombine(ntypelist);
	register_node_type_cmp_colorbalance(ntypelist);
	register_node_type_cmp_huecorrect(ntypelist);
	
	register_node_type_cmp_normal(ntypelist);
	register_node_type_cmp_curve_vec(ntypelist);
	register_node_type_cmp_map_value(ntypelist);
	register_node_type_cmp_normalize(ntypelist);
	
	register_node_type_cmp_filter(ntypelist);
	register_node_type_cmp_blur(ntypelist);
	register_node_type_cmp_dblur(ntypelist);
	register_node_type_cmp_bilateralblur(ntypelist);
	register_node_type_cmp_vecblur(ntypelist);
	register_node_type_cmp_dilateerode(ntypelist);
	register_node_type_cmp_defocus(ntypelist);
	
	register_node_type_cmp_valtorgb(ntypelist);
	register_node_type_cmp_rgbtobw(ntypelist);
	register_node_type_cmp_setalpha(ntypelist);
	register_node_type_cmp_idmask(ntypelist);
	register_node_type_cmp_math(ntypelist);
	register_node_type_cmp_seprgba(ntypelist);
	register_node_type_cmp_combrgba(ntypelist);
	register_node_type_cmp_sephsva(ntypelist);
	register_node_type_cmp_combhsva(ntypelist);
	register_node_type_cmp_sepyuva(ntypelist);
	register_node_type_cmp_combyuva(ntypelist);
	register_node_type_cmp_sepycca(ntypelist);
	register_node_type_cmp_combycca(ntypelist);
	register_node_type_cmp_premulkey(ntypelist);
	
	register_node_type_cmp_diff_matte(ntypelist);
	register_node_type_cmp_distance_matte(ntypelist);
	register_node_type_cmp_chroma_matte(ntypelist);
	register_node_type_cmp_color_matte(ntypelist);
	register_node_type_cmp_channel_matte(ntypelist);
	register_node_type_cmp_color_spill(ntypelist);
	register_node_type_cmp_luma_matte(ntypelist);
	
	register_node_type_cmp_translate(ntypelist);
	register_node_type_cmp_rotate(ntypelist);
	register_node_type_cmp_scale(ntypelist);
	register_node_type_cmp_flip(ntypelist);
	register_node_type_cmp_crop(ntypelist);
	register_node_type_cmp_displace(ntypelist);
	register_node_type_cmp_mapuv(ntypelist);
	register_node_type_cmp_glare(ntypelist);
	register_node_type_cmp_tonemap(ntypelist);
	register_node_type_cmp_lensdist(ntypelist);
	register_node_type_cmp_transform(ntypelist);
	register_node_type_cmp_stabilize2d(ntypelist);
	register_node_type_cmp_moviedistortion(ntypelist);
}

static void registerShaderNodes(ListBase *ntypelist) 
{
	register_node_type_frame(ntypelist);
	
	register_node_type_sh_group(ntypelist);
//	register_node_type_sh_forloop(ntypelist);
//	register_node_type_sh_whileloop(ntypelist);
	
	register_node_type_sh_output(ntypelist);
	register_node_type_sh_mix_rgb(ntypelist);
	register_node_type_sh_valtorgb(ntypelist);
	register_node_type_sh_rgbtobw(ntypelist);
	register_node_type_sh_normal(ntypelist);
	register_node_type_sh_geom(ntypelist);
	register_node_type_sh_mapping(ntypelist);
	register_node_type_sh_curve_vec(ntypelist);
	register_node_type_sh_curve_rgb(ntypelist);
	register_node_type_sh_math(ntypelist);
	register_node_type_sh_vect_math(ntypelist);
	register_node_type_sh_squeeze(ntypelist);
	register_node_type_sh_camera(ntypelist);
	register_node_type_sh_material(ntypelist);
	register_node_type_sh_material_ext(ntypelist);
	register_node_type_sh_value(ntypelist);
	register_node_type_sh_rgb(ntypelist);
	register_node_type_sh_texture(ntypelist);
//	register_node_type_sh_dynamic(ntypelist);
	register_node_type_sh_invert(ntypelist);
	register_node_type_sh_seprgb(ntypelist);
	register_node_type_sh_combrgb(ntypelist);
	register_node_type_sh_hue_sat(ntypelist);
}

static void registerTextureNodes(ListBase *ntypelist)
{
	register_node_type_frame(ntypelist);
	
	register_node_type_tex_group(ntypelist);
//	register_node_type_tex_forloop(ntypelist);
//	register_node_type_tex_whileloop(ntypelist);
	
	register_node_type_tex_math(ntypelist);
	register_node_type_tex_mix_rgb(ntypelist);
	register_node_type_tex_valtorgb(ntypelist);
	register_node_type_tex_rgbtobw(ntypelist);
	register_node_type_tex_valtonor(ntypelist);
	register_node_type_tex_curve_rgb(ntypelist);
	register_node_type_tex_curve_time(ntypelist);
	register_node_type_tex_invert(ntypelist);
	register_node_type_tex_hue_sat(ntypelist);
	register_node_type_tex_coord(ntypelist);
	register_node_type_tex_distance(ntypelist);
	register_node_type_tex_compose(ntypelist);
	register_node_type_tex_decompose(ntypelist);
	
	register_node_type_tex_output(ntypelist);
	register_node_type_tex_viewer(ntypelist);
	
	register_node_type_tex_checker(ntypelist);
	register_node_type_tex_texture(ntypelist);
	register_node_type_tex_bricks(ntypelist);
	register_node_type_tex_image(ntypelist);
	
	register_node_type_tex_rotate(ntypelist);
	register_node_type_tex_translate(ntypelist);
	register_node_type_tex_scale(ntypelist);
	register_node_type_tex_at(ntypelist);
	
	register_node_type_tex_proc_voronoi(ntypelist);
	register_node_type_tex_proc_blend(ntypelist);
	register_node_type_tex_proc_magic(ntypelist);
	register_node_type_tex_proc_marble(ntypelist);
	register_node_type_tex_proc_clouds(ntypelist);
	register_node_type_tex_proc_wood(ntypelist);
	register_node_type_tex_proc_musgrave(ntypelist);
	register_node_type_tex_proc_noise(ntypelist);
	register_node_type_tex_proc_stucci(ntypelist);
	register_node_type_tex_proc_distnoise(ntypelist);
}

static void free_dynamic_typeinfo(bNodeType *ntype)
{
	if(ntype->type==NODE_DYNAMIC) {
		if(ntype->inputs) {
			MEM_freeN(ntype->inputs);
		}
		if(ntype->outputs) {
			MEM_freeN(ntype->outputs);
		}
		if(ntype->name) {
			MEM_freeN((void *)ntype->name);
		}
	}
}

static void free_typeinfos(ListBase *list)
{
	bNodeType *ntype, *next;
	for(ntype=list->first; ntype; ntype=next) {
		next = ntype->next;
		
		if(ntype->type==NODE_DYNAMIC)
			free_dynamic_typeinfo(ntype);
		
		if(ntype->needs_free)
			MEM_freeN(ntype);
	}
}

void init_nodesystem(void) 
{
	registerCompositNodes(&ntreeGetType(NTREE_COMPOSIT)->node_types);
	registerShaderNodes(&ntreeGetType(NTREE_SHADER)->node_types);
	registerTextureNodes(&ntreeGetType(NTREE_TEXTURE)->node_types);
}

void free_nodesystem(void) 
{
	free_typeinfos(&ntreeGetType(NTREE_COMPOSIT)->node_types);
	free_typeinfos(&ntreeGetType(NTREE_SHADER)->node_types);
	free_typeinfos(&ntreeGetType(NTREE_TEXTURE)->node_types);
}

/* called from unlink_scene, when deleting a scene goes over all scenes
 * other than the input, checks if they have render layer nodes referencing
 * the to-be-deleted scene, and resets them to NULL. */

/* XXX needs to get current scene then! */
void clear_scene_in_nodes(Main *bmain, Scene *sce)
{
	Scene *sce1;
	bNode *node;

	for(sce1= bmain->scene.first; sce1; sce1=sce1->id.next) {
		if(sce1!=sce) {
			if(sce1->nodetree) {
				for(node= sce1->nodetree->nodes.first; node; node= node->next) {
					if(node->type==CMP_NODE_R_LAYERS) {
						Scene *nodesce= (Scene *)node->id;
						
						if (nodesce==sce) node->id = NULL;
					}
				}
			}
		}
	}
}

