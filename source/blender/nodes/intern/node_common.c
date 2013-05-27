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
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Lukas Toenne.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/nodes/intern/node_common.c
 *  \ingroup nodes
 */


#include <string.h>
#include <stddef.h>

#include "DNA_node_types.h"

#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "BLF_translation.h"

#include "BKE_global.h"
#include "BKE_idprop.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"

#include "RNA_access.h"
#include "RNA_types.h"

#include "MEM_guardedalloc.h"

#include "node_common.h"
#include "node_util.h"
#include "node_exec.h"
#include "NOD_socket.h"
#include "NOD_common.h"


/**** Group ****/

bNodeSocket *node_group_find_input_socket(bNode *groupnode, const char *identifier)
{
	bNodeSocket *sock;
	for (sock = groupnode->inputs.first; sock; sock = sock->next)
		if (STREQ(sock->identifier, identifier))
			return sock;
	return NULL;
}

bNodeSocket *node_group_find_output_socket(bNode *groupnode, const char *identifier)
{
	bNodeSocket *sock;
	for (sock = groupnode->outputs.first; sock; sock = sock->next)
		if (STREQ(sock->identifier, identifier))
			return sock;
	return NULL;
}

/* groups display their internal tree name as label */
const char *node_group_label(bNode *node)
{
	return (node->id) ? node->id->name + 2 : IFACE_("Missing Datablock");
}

int node_group_poll_instance(bNode *node, bNodeTree *nodetree)
{
	if (node->typeinfo->poll(node->typeinfo, nodetree)) {
		bNodeTree *grouptree = (bNodeTree *)node->id;
		if (grouptree)
			return nodeGroupPoll(nodetree, grouptree);
		else
			return TRUE;    /* without a linked node tree, group node is always ok */
	}
	else
		return FALSE;
}

int nodeGroupPoll(bNodeTree *nodetree, bNodeTree *grouptree)
{
	bNode *node;
	int valid = 1;
	
	if (nodetree == grouptree)
		return 0;
	
	for (node = grouptree->nodes.first; node; node = node->next) {
		if (node->typeinfo->poll_instance && !node->typeinfo->poll_instance(node, nodetree)) {
			valid = 0;
			break;
		}
	}
	return valid;
}

/* used for both group nodes and interface nodes */
static bNodeSocket *group_verify_socket(bNodeTree *ntree, bNode *gnode, bNodeSocket *iosock, ListBase *verify_lb, int in_out)
{
	bNodeSocket *sock;
	
	for (sock = verify_lb->first; sock; sock = sock->next) {
		if (STREQ(sock->identifier, iosock->identifier))
			break;
	}
	if (sock) {
		strcpy(sock->name, iosock->name);
		
		if (iosock->typeinfo->interface_verify_socket)
			iosock->typeinfo->interface_verify_socket(ntree, iosock, gnode, sock, "interface");
	}
	else {
		sock = nodeAddSocket(ntree, gnode, in_out, iosock->idname, iosock->identifier, iosock->name);
		
		if (iosock->typeinfo->interface_init_socket)
			iosock->typeinfo->interface_init_socket(ntree, iosock, gnode, sock, "interface");
	}
	
	/* remove from list temporarily, to distinguish from orphaned sockets */
	BLI_remlink(verify_lb, sock);
	
	return sock;
}

/* used for both group nodes and interface nodes */
static void group_verify_socket_list(bNodeTree *ntree, bNode *gnode,
                                     ListBase *iosock_lb, ListBase *verify_lb, int in_out)
{
	bNodeSocket *iosock, *sock, *nextsock;
	
	/* step by step compare */
	
	iosock = iosock_lb->first;
	for (; iosock; iosock = iosock->next) {
		/* abusing new_sock pointer for verification here! only used inside this function */
		iosock->new_sock = group_verify_socket(ntree, gnode, iosock, verify_lb, in_out);
	}
	/* leftovers are removed */
	for (sock = verify_lb->first; sock; sock = nextsock) {
		nextsock = sock->next;
		nodeRemoveSocket(ntree, gnode, sock);
	}
	/* and we put back the verified sockets */
	iosock = iosock_lb->first;
	for (; iosock; iosock = iosock->next) {
		if (iosock->new_sock) {
			BLI_addtail(verify_lb, iosock->new_sock);
			iosock->new_sock = NULL;
		}
	}
}

/* make sure all group node in ntree, which use ngroup, are sync'd */
void node_group_verify(struct bNodeTree *ntree, struct bNode *node, struct ID *id)
{
	/* check inputs and outputs, and remove or insert them */
	if (id == node->id) {
		bNodeTree *ngroup = (bNodeTree *)node->id;
		group_verify_socket_list(ntree, node, &ngroup->inputs, &node->inputs, SOCK_IN);
		group_verify_socket_list(ntree, node, &ngroup->outputs, &node->outputs, SOCK_OUT);
	}
}

/**** FRAME ****/

static void node_frame_init(bNodeTree *UNUSED(ntree), bNode *node)
{
	NodeFrame *data = (NodeFrame *)MEM_callocN(sizeof(NodeFrame), "frame node storage");
	node->storage = data;
	
	data->flag |= NODE_FRAME_SHRINK;
	
	data->label_size = 20;
}

void register_node_type_frame(void)
{
	/* frame type is used for all tree types, needs dynamic allocation */
	bNodeType *ntype = MEM_callocN(sizeof(bNodeType), "frame node type");

	node_type_base(ntype, NODE_FRAME, "Frame", NODE_CLASS_LAYOUT, NODE_BACKGROUND | NODE_OPTIONS);
	node_type_init(ntype, node_frame_init);
	node_type_storage(ntype, "NodeFrame", node_free_standard_storage, node_copy_standard_storage);
	node_type_size(ntype, 150, 100, 0);
	node_type_compatibility(ntype, NODE_OLD_SHADING | NODE_NEW_SHADING);
	
	ntype->needs_free = 1;
	nodeRegisterType(ntype);
}


/* **************** REROUTE ******************** */

/* simple, only a single input and output here */
static void node_reroute_update_internal_links(bNodeTree *ntree, bNode *node)
{
	bNodeLink *link;

	/* Security check! */
	if (!ntree)
		return;

	link = MEM_callocN(sizeof(bNodeLink), "internal node link");
	link->fromnode = node;
	link->fromsock = node->inputs.first;
	link->tonode = node;
	link->tosock = node->outputs.first;
	/* internal link is always valid */
	link->flag |= NODE_LINK_VALID;
	BLI_addtail(&node->internal_links, link);
}

static void node_reroute_init(bNodeTree *ntree, bNode *node)
{
	/* Note: Cannot use socket templates for this, since it would reset the socket type
	 * on each file read via the template verification procedure.
	 */
	nodeAddStaticSocket(ntree, node, SOCK_IN, SOCK_RGBA, PROP_NONE, "Input", "Input");
	nodeAddStaticSocket(ntree, node, SOCK_OUT, SOCK_RGBA, PROP_NONE, "Output", "Output");
}

void register_node_type_reroute(void)
{
	/* frame type is used for all tree types, needs dynamic allocation */
	bNodeType *ntype = MEM_callocN(sizeof(bNodeType), "frame node type");
	
	node_type_base(ntype, NODE_REROUTE, "Reroute", NODE_CLASS_LAYOUT, 0);
	node_type_init(ntype, node_reroute_init);
	node_type_internal_links(ntype, node_reroute_update_internal_links);
	
	ntype->needs_free = 1;
	nodeRegisterType(ntype);
}

static void node_reroute_inherit_type_recursive(bNodeTree *ntree, bNode *node)
{
	bNodeSocket *input = node->inputs.first;
	bNodeSocket *output = node->outputs.first;
	bNodeLink *link;
	int type = SOCK_FLOAT;
	
	/* XXX it would be a little bit more efficient to restrict actual updates
	 * to rerout nodes connected to an updated node, but there's no reliable flag
	 * to indicate updated nodes (node->update is not set on linking).
	 */
	
	node->done = 1;
	
	/* recursive update */
	for (link = ntree->links.first; link; link = link->next) {
		bNode *fromnode = link->fromnode;
		bNode *tonode = link->tonode;
		if (!tonode || !fromnode)
			continue;
		if (nodeLinkIsHidden(link))
			continue;
		
		if (tonode == node && fromnode->type == NODE_REROUTE && !fromnode->done)
			node_reroute_inherit_type_recursive(ntree, fromnode);
		
		if (fromnode == node && tonode->type == NODE_REROUTE && !tonode->done)
			node_reroute_inherit_type_recursive(ntree, tonode);
	}
	
	/* determine socket type from unambiguous input/output connection if possible */
	if (input->limit == 1 && input->link)
		type = input->link->fromsock->type;
	else if (output->limit == 1 && output->link)
		type = output->link->tosock->type;
	
	/* arbitrary, could also test output->type, both are the same */
	if (input->type != type) {
		PointerRNA input_ptr, output_ptr;
		/* same type for input/output */
		RNA_pointer_create((ID *)ntree, &RNA_NodeSocket, input, &input_ptr);
		RNA_pointer_create((ID *)ntree, &RNA_NodeSocket, output, &output_ptr);
		
		RNA_enum_set(&input_ptr, "type", type);
		RNA_enum_set(&output_ptr, "type", type);
	}
}

/* Global update function for Reroute node types.
 * This depends on connected nodes, so must be done as a tree-wide update.
 */
void ntree_update_reroute_nodes(bNodeTree *ntree)
{
	bNode *node;
	
	/* clear tags */
	for (node = ntree->nodes.first; node; node = node->next)
		node->done = 0;
	
	for (node = ntree->nodes.first; node; node = node->next)
		if (node->type == NODE_REROUTE && !node->done)
			node_reroute_inherit_type_recursive(ntree, node);
}

void BKE_node_tree_unlink_id(ID *id, struct bNodeTree *ntree)
{
	bNode *node;

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->id == id) {
			node->id = NULL;
		}
	}
}

/**** GROUP_INPUT / GROUP_OUTPUT ****/

static void node_group_input_init(bNodeTree *ntree, bNode *node)
{
	node_group_input_verify(ntree, node, (ID *)ntree);
}

bNodeSocket *node_group_input_find_socket(bNode *node, const char *identifier)
{
	bNodeSocket *sock;
	for (sock = node->outputs.first; sock; sock = sock->next)
		if (STREQ(sock->identifier, identifier))
			return sock;
	return NULL;
}

void node_group_input_verify(bNodeTree *ntree, bNode *node, ID *id)
{
	/* check inputs and outputs, and remove or insert them */
	if (id == (ID *)ntree) {
		/* value_in_out inverted for interface nodes to get correct socket value_property */
		group_verify_socket_list(ntree, node, &ntree->inputs, &node->outputs, SOCK_OUT);
		
		/* add virtual extension socket */
		nodeAddSocket(ntree, node, SOCK_OUT, "NodeSocketVirtual", "__extend__", "");
	}
}

static void node_group_input_update(bNodeTree *ntree, bNode *node)
{
	bNodeSocket *extsock = node->outputs.last;
	bNodeLink *link;
	/* Adding a tree socket and verifying will remove the extension socket!
	 * This list caches the existing links from the extension socket
	 * so they can be recreated after verification.
	 */
	ListBase tmplinks;
	
	/* find links from the extension socket and store them */
	tmplinks.first = tmplinks.last = NULL;
	for (link = ntree->links.first; link; link = link->next) {
		if (nodeLinkIsHidden(link))
			continue;
		if (link->fromsock == extsock) {
			bNodeLink *tlink = MEM_callocN(sizeof(bNodeLink), "temporary link");
			*tlink = *link;
			BLI_addtail(&tmplinks, tlink);
		}
	}
	
	if (tmplinks.first) {
		bNodeSocket *gsock, *newsock;
		/* XXX Multiple sockets can be connected to the extension socket at once,
		 * in that case the arbitrary first link determines name and type.
		 * This could be improved by choosing the "best" type among all links,
		 * whatever that means.
		 */
		bNodeLink *exposelink = tmplinks.first;
		
		/* XXX what if connecting virtual to virtual socket?? */
		gsock = ntreeAddSocketInterfaceFromSocket(ntree, exposelink->tonode, exposelink->tosock);
		
		node_group_input_verify(ntree, node, (ID *)ntree);
		newsock = node_group_input_find_socket(node, gsock->identifier);
		
		/* redirect links from the extension socket */
		for (link = tmplinks.first; link; link = link->next) {
			nodeAddLink(ntree, node, newsock, link->tonode, link->tosock);
		}
		
		BLI_freelistN(&tmplinks);
	}
}

void register_node_type_group_input(void)
{
	/* used for all tree types, needs dynamic allocation */
	bNodeType *ntype = MEM_callocN(sizeof(bNodeType), "node type");
	
	node_type_base(ntype, NODE_GROUP_INPUT, "Group Input", NODE_CLASS_INTERFACE, NODE_OPTIONS);
	node_type_size(ntype, 140, 80, 200);
	node_type_init(ntype, node_group_input_init);
	node_type_update(ntype, node_group_input_update, node_group_input_verify);
	node_type_compatibility(ntype, NODE_OLD_SHADING | NODE_NEW_SHADING);
	
	ntype->needs_free = 1;
	nodeRegisterType(ntype);
}

static void node_group_output_init(bNodeTree *ntree, bNode *node)
{
	node_group_output_verify(ntree, node, (ID *)ntree);
}

bNodeSocket *node_group_output_find_socket(bNode *node, const char *identifier)
{
	bNodeSocket *sock;
	for (sock = node->inputs.first; sock; sock = sock->next)
		if (STREQ(sock->identifier, identifier))
			return sock;
	return NULL;
}

void node_group_output_verify(bNodeTree *ntree, bNode *node, ID *id)
{
	/* check inputs and outputs, and remove or insert them */
	if (id == (ID *)ntree) {
		/* value_in_out inverted for interface nodes to get correct socket value_property */
		group_verify_socket_list(ntree, node, &ntree->outputs, &node->inputs, SOCK_IN);
		
		/* add virtual extension socket */
		nodeAddSocket(ntree, node, SOCK_IN, "NodeSocketVirtual", "__extend__", "");
	}
}

static void node_group_output_update(bNodeTree *ntree, bNode *node)
{
	bNodeSocket *extsock = node->inputs.last;
	bNodeLink *link;
	/* Adding a tree socket and verifying will remove the extension socket!
	 * This list caches the existing links to the extension socket
	 * so they can be recreated after verification.
	 */
	ListBase tmplinks;
	
	/* find links to the extension socket and store them */
	tmplinks.first = tmplinks.last = NULL;
	for (link = ntree->links.first; link; link = link->next) {
		if (nodeLinkIsHidden(link))
			continue;
		if (link->tosock == extsock) {
			bNodeLink *tlink = MEM_callocN(sizeof(bNodeLink), "temporary link");
			*tlink = *link;
			BLI_addtail(&tmplinks, tlink);
		}
	}
	
	if (tmplinks.first) {
		bNodeSocket *gsock, *newsock;
		/* XXX Multiple sockets can be connected to the extension socket at once,
		 * in that case the arbitrary first link determines name and type.
		 * This could be improved by choosing the "best" type among all links,
		 * whatever that means.
		 */
		bNodeLink *exposelink = tmplinks.first;
		
		/* XXX what if connecting virtual to virtual socket?? */
		gsock = ntreeAddSocketInterfaceFromSocket(ntree, exposelink->fromnode, exposelink->fromsock);
		
		node_group_output_verify(ntree, node, (ID *)ntree);
		newsock = node_group_output_find_socket(node, gsock->identifier);
		
		/* redirect links to the extension socket */
		for (link = tmplinks.first; link; link = link->next) {
			nodeAddLink(ntree, link->fromnode, link->fromsock, node, newsock);
		}
		
		BLI_freelistN(&tmplinks);
	}
}

void register_node_type_group_output(void)
{
	/* used for all tree types, needs dynamic allocation */
	bNodeType *ntype = MEM_callocN(sizeof(bNodeType), "node type");
	
	node_type_base(ntype, NODE_GROUP_OUTPUT, "Group Output", NODE_CLASS_INTERFACE, NODE_OPTIONS);
	node_type_size(ntype, 140, 80, 200);
	node_type_init(ntype, node_group_output_init);
	node_type_update(ntype, node_group_output_update, node_group_output_verify);
	node_type_compatibility(ntype, NODE_OLD_SHADING | NODE_NEW_SHADING);
	
	ntype->needs_free = 1;
	nodeRegisterType(ntype);
}
