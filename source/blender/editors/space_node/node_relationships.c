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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): David Millan Escriva, Juho Vepsäläinen, Nathan Letwory
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/editors/space_node/node_relationships.c
 *  \ingroup spnode
 */

#include "MEM_guardedalloc.h"

#include "DNA_node_types.h"
#include "DNA_object_types.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"

#include "BKE_context.h"
#include "BKE_main.h"
#include "BKE_node.h"

#include "ED_node.h"  /* own include */
#include "ED_screen.h"
#include "ED_render.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_view2d.h"

#include "node_intern.h"  /* own include */
#include "NOD_common.h"

/* ****************** Add *********************** */


typedef struct bNodeListItem {
	struct bNodeListItem *next, *prev;
	struct bNode *node;
} bNodeListItem;

static int sort_nodes_locx(void *a, void *b)
{
	bNodeListItem *nli1 = (bNodeListItem *)a;
	bNodeListItem *nli2 = (bNodeListItem *)b;
	bNode *node1 = nli1->node;
	bNode *node2 = nli2->node;

	if (node1->locx > node2->locx)
		return 1;
	else
		return 0;
}

static int socket_is_available(bNodeTree *UNUSED(ntree), bNodeSocket *sock, int allow_used)
{
	if (nodeSocketIsHidden(sock))
		return 0;

	if (!allow_used && (sock->flag & SOCK_IN_USE))
		return 0;

	return 1;
}

static bNodeSocket *best_socket_output(bNodeTree *ntree, bNode *node, bNodeSocket *sock_target, int allow_multiple)
{
	bNodeSocket *sock;

	/* first look for selected output */
	for (sock = node->outputs.first; sock; sock = sock->next) {
		if (!socket_is_available(ntree, sock, allow_multiple))
			continue;

		if (sock->flag & SELECT)
			return sock;
	}

	/* try to find a socket with a matching name */
	for (sock = node->outputs.first; sock; sock = sock->next) {
		if (!socket_is_available(ntree, sock, allow_multiple))
			continue;

		/* check for same types */
		if (sock->type == sock_target->type) {
			if (STREQ(sock->name, sock_target->name))
				return sock;
		}
	}

	/* otherwise settle for the first available socket of the right type */
	for (sock = node->outputs.first; sock; sock = sock->next) {

		if (!socket_is_available(ntree, sock, allow_multiple))
			continue;

		/* check for same types */
		if (sock->type == sock_target->type) {
			return sock;
		}
	}

	return NULL;
}

/* this is a bit complicated, but designed to prioritize finding
 * sockets of higher types, such as image, first */
static bNodeSocket *best_socket_input(bNodeTree *ntree, bNode *node, int num, int replace)
{
	bNodeSocket *sock;
	int socktype, maxtype = 0;
	int a = 0;

	for (sock = node->inputs.first; sock; sock = sock->next) {
		maxtype = max_ii(sock->type, maxtype);
	}

	/* find sockets of higher 'types' first (i.e. image) */
	for (socktype = maxtype; socktype >= 0; socktype--) {
		for (sock = node->inputs.first; sock; sock = sock->next) {

			if (!socket_is_available(ntree, sock, replace)) {
				a++;
				continue;
			}

			if (sock->type == socktype) {
				/* increment to make sure we don't keep finding
				 * the same socket on every attempt running this function */
				a++;
				if (a > num)
					return sock;
			}
		}
	}

	return NULL;
}

static int snode_autoconnect_input(SpaceNode *snode, bNode *node_fr, bNodeSocket *sock_fr, bNode *node_to, bNodeSocket *sock_to, int replace)
{
	bNodeTree *ntree = snode->edittree;
	bNodeLink *link;

	/* then we can connect */
	if (replace)
		nodeRemSocketLinks(ntree, sock_to);

	link = nodeAddLink(ntree, node_fr, sock_fr, node_to, sock_to);
	/* validate the new link */
	ntreeUpdateTree(ntree);
	if (!(link->flag & NODE_LINK_VALID)) {
		nodeRemLink(ntree, link);
		return 0;
	}

	snode_update(snode, node_to);
	return 1;
}

static void snode_autoconnect(SpaceNode *snode, int allow_multiple, int replace)
{
	bNodeTree *ntree = snode->edittree;
	ListBase *nodelist = MEM_callocN(sizeof(ListBase), "items_list");
	bNodeListItem *nli;
	bNode *node;
	int i, numlinks = 0;

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & NODE_SELECT) {
			nli = MEM_mallocN(sizeof(bNodeListItem), "temporary node list item");
			nli->node = node;
			BLI_addtail(nodelist, nli);
		}
	}

	/* sort nodes left to right */
	BLI_sortlist(nodelist, sort_nodes_locx);

	for (nli = nodelist->first; nli; nli = nli->next) {
		bNode *node_fr, *node_to;
		bNodeSocket *sock_fr, *sock_to;
		int has_selected_inputs = 0;

		if (nli->next == NULL) break;

		node_fr = nli->node;
		node_to = nli->next->node;

		/* if there are selected sockets, connect those */
		for (sock_to = node_to->inputs.first; sock_to; sock_to = sock_to->next) {
			if (sock_to->flag & SELECT) {
				has_selected_inputs = 1;

				if (!socket_is_available(ntree, sock_to, replace))
					continue;

				/* check for an appropriate output socket to connect from */
				sock_fr = best_socket_output(ntree, node_fr, sock_to, allow_multiple);
				if (!sock_fr)
					continue;

				if (snode_autoconnect_input(snode, node_fr, sock_fr, node_to, sock_to, replace)) {
					numlinks++;
				}
			}
		}

		if (!has_selected_inputs) {
			/* no selected inputs, connect by finding suitable match */
			int num_inputs = BLI_countlist(&node_to->inputs);

			for (i = 0; i < num_inputs; i++) {

				/* find the best guess input socket */
				sock_to = best_socket_input(ntree, node_to, i, replace);
				if (!sock_to)
					continue;

				/* check for an appropriate output socket to connect from */
				sock_fr = best_socket_output(ntree, node_fr, sock_to, allow_multiple);
				if (!sock_fr)
					continue;

				if (snode_autoconnect_input(snode, node_fr, sock_fr, node_to, sock_to, replace)) {
					numlinks++;
					break;
				}
			}
		}
	}

	if (numlinks > 0) {
		ntreeUpdateTree(ntree);
	}

	BLI_freelistN(nodelist);
	MEM_freeN(nodelist);
}

/* *************************** link viewer op ******************** */

static int node_link_viewer(const bContext *C, bNode *tonode)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNode *node;
	bNodeLink *link;
	bNodeSocket *sock;

	/* context check */
	if (tonode == NULL || tonode->outputs.first == NULL)
		return OPERATOR_CANCELLED;
	if (ELEM(tonode->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER))
		return OPERATOR_CANCELLED;

	/* get viewer */
	for (node = snode->edittree->nodes.first; node; node = node->next)
		if (ELEM(node->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER))
			if (node->flag & NODE_DO_OUTPUT)
				break;
	/* no viewer, we make one active */
	if (node == NULL) {
		for (node = snode->edittree->nodes.first; node; node = node->next) {
			if (ELEM(node->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER)) {
				node->flag |= NODE_DO_OUTPUT;
				break;
			}
		}
	}

	sock = NULL;

	/* try to find an already connected socket to cycle to the next */
	if (node) {
		link = NULL;
		for (link = snode->edittree->links.first; link; link = link->next)
			if (link->tonode == node && link->fromnode == tonode)
				if (link->tosock == node->inputs.first)
					break;
		if (link) {
			/* unlink existing connection */
			sock = link->fromsock;
			nodeRemLink(snode->edittree, link);

			/* find a socket after the previously connected socket */
			for (sock = sock->next; sock; sock = sock->next)
				if (!nodeSocketIsHidden(sock))
					break;
		}
	}

	/* find a socket starting from the first socket */
	if (!sock) {
		for (sock = tonode->outputs.first; sock; sock = sock->next)
			if (!nodeSocketIsHidden(sock))
				break;
	}

	if (sock) {
		/* add a new viewer if none exists yet */
		if (!node) {
			/* XXX location is a quick hack, just place it next to the linked socket */
			node = node_add_node(C, NULL, CMP_NODE_VIEWER, sock->locx + 100, sock->locy);
			if (!node)
				return OPERATOR_CANCELLED;

			link = NULL;
		}
		else {
			/* get link to viewer */
			for (link = snode->edittree->links.first; link; link = link->next)
				if (link->tonode == node && link->tosock == node->inputs.first)
					break;
		}

		if (link == NULL) {
			nodeAddLink(snode->edittree, tonode, sock, node, node->inputs.first);
		}
		else {
			link->fromnode = tonode;
			link->fromsock = sock;
			/* make sure the dependency sorting is updated */
			snode->edittree->update |= NTREE_UPDATE_LINKS;
		}
		ntreeUpdateTree(snode->edittree);
		snode_update(snode, node);
	}

	return OPERATOR_FINISHED;
}


static int node_active_link_viewer(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNode *node;

	node = nodeGetActive(snode->edittree);

	if (!node)
		return OPERATOR_CANCELLED;

	ED_preview_kill_jobs(C);

	if (node_link_viewer(C, node) == OPERATOR_CANCELLED)
		return OPERATOR_CANCELLED;

	snode_notify(C, snode);

	return OPERATOR_FINISHED;
}


void NODE_OT_link_viewer(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Link to Viewer Node";
	ot->description = "Link to viewer node";
	ot->idname = "NODE_OT_link_viewer";

	/* api callbacks */
	ot->exec = node_active_link_viewer;
	ot->poll = composite_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}


/* *************************** add link op ******************** */

static void node_remove_extra_links(SpaceNode *snode, bNodeSocket *tsock, bNodeLink *link)
{
	bNodeLink *tlink;
	bNodeSocket *sock;

	if (tsock && nodeCountSocketLinks(snode->edittree, link->tosock) > tsock->limit) {

		for (tlink = snode->edittree->links.first; tlink; tlink = tlink->next) {
			if (link != tlink && tlink->tosock == link->tosock)
				break;
		}
		if (tlink) {
			/* try to move the existing link to the next available socket */
			if (tlink->tonode) {
				/* is there a free input socket with the target type? */
				for (sock = tlink->tonode->inputs.first; sock; sock = sock->next) {
					if (sock->type == tlink->tosock->type)
						if (nodeCountSocketLinks(snode->edittree, sock) < sock->limit)
							break;
				}
				if (sock) {
					tlink->tosock = sock;
					sock->flag &= ~SOCK_HIDDEN;
				}
				else {
					nodeRemLink(snode->edittree, tlink);
				}
			}
			else
				nodeRemLink(snode->edittree, tlink);

			snode->edittree->update |= NTREE_UPDATE_LINKS;
		}
	}
}

/* loop that adds a nodelink, called by function below  */
/* in_out = starting socket */
static int node_link_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	ARegion *ar = CTX_wm_region(C);
	bNodeLinkDrag *nldrag = op->customdata;
	bNodeTree *ntree = snode->edittree;
	bNode *tnode;
	bNodeSocket *tsock = NULL;
	bNodeLink *link;
	LinkData *linkdata;
	int in_out;
	int expose;

	in_out = nldrag->in_out;
	
	UI_view2d_region_to_view(&ar->v2d, event->mval[0], event->mval[1],
	                         &snode->cursor[0], &snode->cursor[1]);

	expose = RNA_boolean_get(op->ptr, "expose");

	switch (event->type) {
		case MOUSEMOVE:
			
			if (in_out == SOCK_OUT) {
				if (node_find_indicated_socket(snode, &tnode, &tsock, SOCK_IN)) {
					for (linkdata = nldrag->links.first; linkdata; linkdata = linkdata->next) {
						link = linkdata->data;
						
						/* skip if this is already the target socket */
						if (link->tosock == tsock)
							continue;
						/* skip if socket is on the same node as the fromsock */
						if (tnode && link->fromnode == tnode)
							continue;
						
						/* attach links to the socket */
						link->tonode = tnode;
						link->tosock = tsock;
					}
				}
				else {
					for (linkdata = nldrag->links.first; linkdata; linkdata = linkdata->next) {
						link = linkdata->data;
						
						link->tonode = NULL;
						link->tosock = NULL;
					}
				}
			}
			else {
				if (node_find_indicated_socket(snode, &tnode, &tsock, SOCK_OUT)) {
					for (linkdata = nldrag->links.first; linkdata; linkdata = linkdata->next) {
						link = linkdata->data;
						
						/* skip if this is already the target socket */
						if (link->fromsock == tsock)
							continue;
						/* skip if socket is on the same node as the fromsock */
						if (tnode && link->tonode == tnode)
							continue;
						
						/* attach links to the socket */
						link->fromnode = tnode;
						link->fromsock = tsock;
					}
				}
				else {
					for (linkdata = nldrag->links.first; linkdata; linkdata = linkdata->next) {
						link = linkdata->data;
						
						link->fromnode = NULL;
						link->fromsock = NULL;
					}
				}
			}
			
			ED_region_tag_redraw(ar);
			break;
			
		case LEFTMOUSE:
		case RIGHTMOUSE:
		case MIDDLEMOUSE:
		{
			/* XXX expose + detach could have some ugly corner cases and is not great.
			 * The first link will define the exposed socket type, which is arbitrary.
			 * Some of the resulting links may turn out to be invalid.
			 */
			bNode *ionode = NULL;
			bNodeSocket *iosock = NULL, *gsock;
			for (linkdata = nldrag->links.first; linkdata; linkdata = linkdata->next) {
				link = linkdata->data;
				
				if (link->tosock && link->fromsock) {
					/* add link to the node tree */
					BLI_addtail(&ntree->links, link);
					
					ntree->update |= NTREE_UPDATE_LINKS;
					
					/* tag tonode for update */
					link->tonode->update |= NODE_UPDATE;
					
					/* we might need to remove a link */
					if (in_out == SOCK_OUT)
						node_remove_extra_links(snode, link->tosock, link);
				}
				else if (expose) {
					if (link->tosock) {
						if (!ionode) {
							ionode = nodeAddStaticNode(C, snode->edittree, NODE_GROUP_INPUT);
							gsock = ntreeAddSocketInterfaceFromSocket(snode->edittree, link->tonode, link->tosock);
							node_group_input_verify(snode->edittree, ionode, (ID *)snode->edittree);
							iosock = node_group_input_find_socket(ionode, gsock->identifier);
							
							{
								/* place the node at the mouse pointer */
								float sockx = 42.0f + 3 * HIDDEN_RAD;  /* XXX totally arbitrary initial hidden node size ... */
								float socky = -HIDDEN_RAD;
								
								ionode->locx = snode->cursor[0] - sockx;
								ionode->locy = snode->cursor[1] - socky;
							}
						}
						link->fromnode = ionode;
						link->fromsock = iosock;
						
						BLI_addtail(&ntree->links, link);
						
						ntree->update |= NTREE_UPDATE_GROUP_IN | NTREE_UPDATE_LINKS;
					}
					else if (link->fromsock) {
						if (!ionode) {
							ionode = nodeAddStaticNode(C, snode->edittree, NODE_GROUP_OUTPUT);
							gsock = ntreeAddSocketInterfaceFromSocket(snode->edittree, link->fromnode, link->fromsock);
							node_group_output_verify(snode->edittree, ionode, (ID *)snode->edittree);
							iosock = node_group_output_find_socket(ionode, gsock->identifier);
							
							{
								/* place the node at the mouse pointer */
								float sockx = 0;
								float socky = -HIDDEN_RAD;
								
								ionode->locx = snode->cursor[0] - sockx;
								ionode->locy = snode->cursor[1] - socky;
							}
						}
						link->tonode = ionode;
						link->tosock = iosock;
						
						BLI_addtail(&ntree->links, link);
						
						ntree->update |= NTREE_UPDATE_GROUP_OUT | NTREE_UPDATE_LINKS;
					}
					else {
						nodeRemLink(snode->edittree, link);
					}
				}
				else
					nodeRemLink(ntree, link);
			}
			
			ntreeUpdateTree(ntree);
			snode_notify(C, snode);
			snode_dag_update(C, snode);
			
			BLI_remlink(&snode->linkdrag, nldrag);
			/* links->data pointers are either held by the tree or freed already */
			BLI_freelistN(&nldrag->links);
			MEM_freeN(nldrag);
			
			return OPERATOR_FINISHED;
		}
	}
	
	return OPERATOR_RUNNING_MODAL;
}

/* return 1 when socket clicked */
static bNodeLinkDrag *node_link_init(SpaceNode *snode, int detach)
{
	bNode *node;
	bNodeSocket *sock;
	bNodeLink *link, *link_next, *oplink;
	bNodeLinkDrag *nldrag = NULL;
	LinkData *linkdata;
	int num_links;

	/* output indicated? */
	if (node_find_indicated_socket(snode, &node, &sock, SOCK_OUT)) {
		nldrag = MEM_callocN(sizeof(bNodeLinkDrag), "drag link op customdata");

		num_links = nodeCountSocketLinks(snode->edittree, sock);
		if (num_links > 0 && (num_links >= sock->limit || detach)) {
			/* dragged links are fixed on input side */
			nldrag->in_out = SOCK_IN;
			/* detach current links and store them in the operator data */
			for (link = snode->edittree->links.first; link; link = link_next) {
				link_next = link->next;
				if (link->fromsock == sock) {
					linkdata = MEM_callocN(sizeof(LinkData), "drag link op link data");
					linkdata->data = oplink = MEM_callocN(sizeof(bNodeLink), "drag link op link");
					*oplink = *link;
					oplink->next = oplink->prev = NULL;
					oplink->flag |= NODE_LINK_VALID;
					
					BLI_addtail(&nldrag->links, linkdata);
					nodeRemLink(snode->edittree, link);
				}
			}
		}
		else {
			/* dragged links are fixed on output side */
			nldrag->in_out = SOCK_OUT;
			/* create a new link */
			linkdata = MEM_callocN(sizeof(LinkData), "drag link op link data");
			linkdata->data = oplink = MEM_callocN(sizeof(bNodeLink), "drag link op link");
			oplink->fromnode = node;
			oplink->fromsock = sock;
			oplink->flag |= NODE_LINK_VALID;
			
			BLI_addtail(&nldrag->links, linkdata);
		}
	}
	/* or an input? */
	else if (node_find_indicated_socket(snode, &node, &sock, SOCK_IN)) {
		nldrag = MEM_callocN(sizeof(bNodeLinkDrag), "drag link op customdata");

		num_links = nodeCountSocketLinks(snode->edittree, sock);
		if (num_links > 0 && (num_links >= sock->limit || detach)) {
			/* dragged links are fixed on output side */
			nldrag->in_out = SOCK_OUT;
			/* detach current links and store them in the operator data */
			for (link = snode->edittree->links.first; link; link = link_next) {
				link_next = link->next;
				if (link->tosock == sock) {
					linkdata = MEM_callocN(sizeof(LinkData), "drag link op link data");
					linkdata->data = oplink = MEM_callocN(sizeof(bNodeLink), "drag link op link");
					*oplink = *link;
					oplink->next = oplink->prev = NULL;
					oplink->flag |= NODE_LINK_VALID;
					
					BLI_addtail(&nldrag->links, linkdata);
					nodeRemLink(snode->edittree, link);
					
					/* send changed event to original link->tonode */
					if (node)
						snode_update(snode, node);
				}
			}
		}
		else {
			/* dragged links are fixed on input side */
			nldrag->in_out = SOCK_IN;
			/* create a new link */
			linkdata = MEM_callocN(sizeof(LinkData), "drag link op link data");
			linkdata->data = oplink = MEM_callocN(sizeof(bNodeLink), "drag link op link");
			oplink->tonode = node;
			oplink->tosock = sock;
			oplink->flag |= NODE_LINK_VALID;
			
			BLI_addtail(&nldrag->links, linkdata);
		}
	}

	return nldrag;
}

static int node_link_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	ARegion *ar = CTX_wm_region(C);
	bNodeLinkDrag *nldrag;
	int detach = RNA_boolean_get(op->ptr, "detach");

	UI_view2d_region_to_view(&ar->v2d, event->mval[0], event->mval[1],
	                         &snode->cursor[0], &snode->cursor[1]);

	ED_preview_kill_jobs(C);

	nldrag = node_link_init(snode, detach);

	if (nldrag) {
		op->customdata = nldrag;
		BLI_addtail(&snode->linkdrag, nldrag);

		/* add modal handler */
		WM_event_add_modal_handler(C, op);

		return OPERATOR_RUNNING_MODAL;
	}
	else
		return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
}

static int node_link_cancel(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeLinkDrag *nldrag = op->customdata;

	BLI_remlink(&snode->linkdrag, nldrag);

	BLI_freelistN(&nldrag->links);
	MEM_freeN(nldrag);

	return OPERATOR_CANCELLED;
}

void NODE_OT_link(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Link Nodes";
	ot->idname = "NODE_OT_link";
	ot->description = "Use the mouse to create a link between two nodes";

	/* api callbacks */
	ot->invoke = node_link_invoke;
	ot->modal = node_link_modal;
//	ot->exec = node_link_exec;
	ot->poll = ED_operator_node_active;
	ot->cancel = node_link_cancel;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO | OPTYPE_BLOCKING;

	RNA_def_boolean(ot->srna, "detach", FALSE, "Detach", "Detach and redirect existing links");
	RNA_def_boolean(ot->srna, "expose", FALSE, "Expose", "Expose the socket as an interface node");
}

/* ********************** Make Link operator ***************** */

/* makes a link between selected output and input sockets */
static int node_make_link_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	int replace = RNA_boolean_get(op->ptr, "replace");

	ED_preview_kill_jobs(C);

	snode_autoconnect(snode, 1, replace);

	/* deselect sockets after linking */
	node_deselect_all_input_sockets(snode, 0);
	node_deselect_all_output_sockets(snode, 0);

	ntreeUpdateTree(snode->edittree);
	snode_notify(C, snode);
	snode_dag_update(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_link_make(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Make Links";
	ot->description = "Makes a link between selected output in input sockets";
	ot->idname = "NODE_OT_link_make";

	/* callbacks */
	ot->exec = node_make_link_exec;
	ot->poll = ED_operator_node_active; // XXX we need a special poll which checks that there are selected input/output sockets

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_boolean(ot->srna, "replace", 0, "Replace", "Replace socket connections with the new links");
}

/* ********************** Cut Link operator ***************** */
static int cut_links_intersect(bNodeLink *link, float mcoords[][2], int tot)
{
	float coord_array[NODE_LINK_RESOL + 1][2];
	int i, b;

	if (node_link_bezier_points(NULL, NULL, link, coord_array, NODE_LINK_RESOL)) {

		for (i = 0; i < tot - 1; i++)
			for (b = 0; b < NODE_LINK_RESOL; b++)
				if (isect_line_line_v2(mcoords[i], mcoords[i + 1], coord_array[b], coord_array[b + 1]) > 0)
					return 1;
	}
	return 0;
}

static int cut_links_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	ARegion *ar = CTX_wm_region(C);
	float mcoords[256][2];
	int i = 0;

	RNA_BEGIN(op->ptr, itemptr, "path")
	{
		float loc[2];

		RNA_float_get_array(&itemptr, "loc", loc);
		UI_view2d_region_to_view(&ar->v2d, (int)loc[0], (int)loc[1],
		                         &mcoords[i][0], &mcoords[i][1]);
		i++;
		if (i >= 256) break;
	}
	RNA_END;

	if (i > 1) {
		int found = FALSE;
		bNodeLink *link, *next;
		
		ED_preview_kill_jobs(C);
		
		for (link = snode->edittree->links.first; link; link = next) {
			next = link->next;
			if (nodeLinkIsHidden(link))
				continue;

			if (cut_links_intersect(link, mcoords, i)) {

				if (found == FALSE) {
					ED_preview_kill_jobs(C);
					found = TRUE;
				}

				snode_update(snode, link->tonode);
				nodeRemLink(snode->edittree, link);
			}
		}

		if (found) {
			ntreeUpdateTree(snode->edittree);
			snode_notify(C, snode);
			snode_dag_update(C, snode);

			return OPERATOR_FINISHED;
		}
		else {
			return OPERATOR_CANCELLED;
		}

	}

	return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
}

void NODE_OT_links_cut(wmOperatorType *ot)
{
	PropertyRNA *prop;

	ot->name = "Cut Links";
	ot->idname = "NODE_OT_links_cut";
	ot->description = "Use the mouse to cut (remove) some links";

	ot->invoke = WM_gesture_lines_invoke;
	ot->modal = WM_gesture_lines_modal;
	ot->exec = cut_links_exec;
	ot->cancel = WM_gesture_lines_cancel;

	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	prop = RNA_def_property(ot->srna, "path", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_runtime(prop, &RNA_OperatorMousePath);
	/* internal */
	RNA_def_int(ot->srna, "cursor", BC_KNIFECURSOR, 0, INT_MAX, "Cursor", "", 0, INT_MAX);
}

/* ********************** Detach links operator ***************** */

static int detach_links_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *node;

	ED_preview_kill_jobs(C);

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			nodeInternalRelink(ntree, node);
		}
	}

	ntreeUpdateTree(ntree);

	snode_notify(C, snode);
	snode_dag_update(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_links_detach(wmOperatorType *ot)
{
	ot->name = "Detach Links";
	ot->idname = "NODE_OT_links_detach";
	ot->description = "Remove all links to selected nodes, and try to connect neighbor nodes together";

	ot->exec = detach_links_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}


/* ****************** Show Cyclic Dependencies Operator  ******************* */

static int node_show_cycles_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);

	/* this is just a wrapper around this call... */
	ntreeUpdateTree(snode->nodetree);
	snode_notify(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_show_cyclic_dependencies(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Show Cyclic Dependencies";
	ot->description = "Sort the nodes and show the cyclic dependencies between the nodes";
	ot->idname = "NODE_OT_show_cyclic_dependencies";

	/* callbacks */
	ot->exec = node_show_cycles_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Set Parent ******************* */

static int node_parent_set_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *frame = nodeGetActive(ntree), *node;
	if (!frame || frame->type != NODE_FRAME)
		return OPERATOR_CANCELLED;

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node == frame)
			continue;
		if (node->flag & NODE_SELECT) {
			nodeDetachNode(node);
			nodeAttachNode(node, frame);
		}
	}

	ED_node_sort(ntree);
	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_parent_set(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Make Parent";
	ot->description = "Attach selected nodes";
	ot->idname = "NODE_OT_parent_set";

	/* api callbacks */
	ot->exec = node_parent_set_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Clear Parent ******************* */

static int node_parent_clear_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *node;

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & NODE_SELECT) {
			nodeDetachNode(node);
		}
	}

	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_parent_clear(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Clear Parent";
	ot->description = "Detach selected nodes";
	ot->idname = "NODE_OT_parent_clear";

	/* api callbacks */
	ot->exec = node_parent_clear_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Join Nodes ******************* */

/* tags for depth-first search */
#define NODE_JOIN_DONE          1
#define NODE_JOIN_IS_DESCENDANT 2

static void node_join_attach_recursive(bNode *node, bNode *frame)
{
	node->done |= NODE_JOIN_DONE;

	if (node == frame) {
		node->done |= NODE_JOIN_IS_DESCENDANT;
	}
	else if (node->parent) {
		/* call recursively */
		if (!(node->parent->done & NODE_JOIN_DONE))
			node_join_attach_recursive(node->parent, frame);

		/* in any case: if the parent is a descendant, so is the child */
		if (node->parent->done & NODE_JOIN_IS_DESCENDANT)
			node->done |= NODE_JOIN_IS_DESCENDANT;
		else if (node->flag & NODE_TEST) {
			/* if parent is not an decendant of the frame, reattach the node */
			nodeDetachNode(node);
			nodeAttachNode(node, frame);
			node->done |= NODE_JOIN_IS_DESCENDANT;
		}
	}
	else if (node->flag & NODE_TEST) {
		nodeAttachNode(node, frame);
		node->done |= NODE_JOIN_IS_DESCENDANT;
	}
}

static int node_join_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *node, *frame;

	/* XXX save selection: node_add_node call below sets the new frame as single active+selected node */
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & NODE_SELECT)
			node->flag |= NODE_TEST;
		else
			node->flag &= ~NODE_TEST;
	}

	frame = node_add_node(C, NULL, NODE_FRAME, 0.0f, 0.0f);

	/* reset tags */
	for (node = ntree->nodes.first; node; node = node->next)
		node->done = 0;

	for (node = ntree->nodes.first; node; node = node->next) {
		if (!(node->done & NODE_JOIN_DONE))
			node_join_attach_recursive(node, frame);
	}

	/* restore selection */
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & NODE_TEST)
			node->flag |= NODE_SELECT;
	}

	ED_node_sort(ntree);
	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_join(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Join Nodes";
	ot->description = "Attach selected nodes to a new common frame";
	ot->idname = "NODE_OT_join";

	/* api callbacks */
	ot->exec = node_join_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Attach ******************* */

static int node_attach_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *frame;

	/* check nodes front to back */
	for (frame = ntree->nodes.last; frame; frame = frame->prev) {
		/* skip selected, those are the nodes we want to attach */
		if ((frame->type != NODE_FRAME) || (frame->flag & NODE_SELECT))
			continue;
		if (BLI_rctf_isect_pt(&frame->totr, snode->cursor[0], snode->cursor[1]))
			break;
	}
	if (frame) {
		bNode *node, *parent;
		for (node = ntree->nodes.last; node; node = node->prev) {
			if (node->flag & NODE_SELECT) {
				if (node->parent == NULL) {
					/* disallow moving a parent into its child */
					if (nodeAttachNodeCheck(frame, node) == FALSE) {
						/* attach all unparented nodes */
						nodeAttachNode(node, frame);
					}
				}
				else {
					/* attach nodes which share parent with the frame */
					for (parent = frame->parent; parent; parent = parent->parent) {
						if (parent == node->parent) {
							break;
						}
					}

					if (parent) {
						/* disallow moving a parent into its child */
						if (nodeAttachNodeCheck(frame, node) == FALSE) {
							nodeDetachNode(node);
							nodeAttachNode(node, frame);
						}
					}
				}
			}
		}
	}

	ED_node_sort(ntree);
	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

static int node_attach_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	ARegion *ar = CTX_wm_region(C);
	SpaceNode *snode = CTX_wm_space_node(C);

	/* convert mouse coordinates to v2d space */
	UI_view2d_region_to_view(&ar->v2d, event->mval[0], event->mval[1], &snode->cursor[0], &snode->cursor[1]);

	return node_attach_exec(C, op);
}

void NODE_OT_attach(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Attach Nodes";
	ot->description = "Attach active node to a frame";
	ot->idname = "NODE_OT_attach";

	/* api callbacks */
	ot->exec = node_attach_exec;
	ot->invoke = node_attach_invoke;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Detach ******************* */

/* tags for depth-first search */
#define NODE_DETACH_DONE            1
#define NODE_DETACH_IS_DESCENDANT   2

static void node_detach_recursive(bNode *node)
{
	node->done |= NODE_DETACH_DONE;

	if (node->parent) {
		/* call recursively */
		if (!(node->parent->done & NODE_DETACH_DONE))
			node_detach_recursive(node->parent);

		/* in any case: if the parent is a descendant, so is the child */
		if (node->parent->done & NODE_DETACH_IS_DESCENDANT)
			node->done |= NODE_DETACH_IS_DESCENDANT;
		else if (node->flag & NODE_SELECT) {
			/* if parent is not a decendant of a selected node, detach */
			nodeDetachNode(node);
			node->done |= NODE_DETACH_IS_DESCENDANT;
		}
	}
	else if (node->flag & NODE_SELECT) {
		node->done |= NODE_DETACH_IS_DESCENDANT;
	}
}


/* detach the root nodes in the current selection */
static int node_detach_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *node;

	/* reset tags */
	for (node = ntree->nodes.first; node; node = node->next)
		node->done = 0;
	/* detach nodes recursively
	 * relative order is preserved here!
	 */
	for (node = ntree->nodes.first; node; node = node->next) {
		if (!(node->done & NODE_DETACH_DONE))
			node_detach_recursive(node);
	}

	ED_node_sort(ntree);
	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_detach(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Detach Nodes";
	ot->description = "Detach selected nodes from parents";
	ot->idname = "NODE_OT_detach";

	/* api callbacks */
	ot->exec = node_detach_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* *********************  automatic node insert on dragging ******************* */


/* prevent duplicate testing code below */
static SpaceNode *ed_node_link_conditions(ScrArea *sa, bNode **select)
{
	SpaceNode *snode = sa ? sa->spacedata.first : NULL;
	bNode *node;
	bNodeLink *link;

	/* no unlucky accidents */
	if (sa == NULL || sa->spacetype != SPACE_NODE) return NULL;

	*select = NULL;

	for (node = snode->edittree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			if (*select)
				break;
			else
				*select = node;
		}
	}
	/* only one selected */
	if (node || *select == NULL) return NULL;

	/* correct node */
	if ((*select)->inputs.first == NULL || (*select)->outputs.first == NULL) return NULL;

	/* test node for links */
	for (link = snode->edittree->links.first; link; link = link->next) {
		if (nodeLinkIsHidden(link))
			continue;
		
		if (link->tonode == *select || link->fromnode == *select)
			return NULL;
	}

	return snode;
}

/* test == 0, clear all intersect flags */
void ED_node_link_intersect_test(ScrArea *sa, int test)
{
	bNode *select;
	SpaceNode *snode = ed_node_link_conditions(sa, &select);
	bNodeLink *link, *selink = NULL;
	float mcoords[6][2];

	if (snode == NULL) return;

	/* clear flags */
	for (link = snode->edittree->links.first; link; link = link->next)
		link->flag &= ~NODE_LINKFLAG_HILITE;

	if (test == 0) return;

	/* okay, there's 1 node, without links, now intersect */
	mcoords[0][0] = select->totr.xmin;
	mcoords[0][1] = select->totr.ymin;
	mcoords[1][0] = select->totr.xmax;
	mcoords[1][1] = select->totr.ymin;
	mcoords[2][0] = select->totr.xmax;
	mcoords[2][1] = select->totr.ymax;
	mcoords[3][0] = select->totr.xmin;
	mcoords[3][1] = select->totr.ymax;
	mcoords[4][0] = select->totr.xmin;
	mcoords[4][1] = select->totr.ymin;
	mcoords[5][0] = select->totr.xmax;
	mcoords[5][1] = select->totr.ymax;

	/* we only tag a single link for intersect now */
	/* idea; use header dist when more? */
	for (link = snode->edittree->links.first; link; link = link->next) {
		if (nodeLinkIsHidden(link))
			continue;
		
		if (cut_links_intersect(link, mcoords, 5)) { /* intersect code wants edges */
			if (selink)
				break;
			selink = link;
		}
	}

	if (link == NULL && selink)
		selink->flag |= NODE_LINKFLAG_HILITE;
}

/* assumes sockets in list */
static bNodeSocket *socket_best_match(ListBase *sockets)
{
	bNodeSocket *sock;
	int type, maxtype = 0;

	/* find type range */
	for (sock = sockets->first; sock; sock = sock->next)
		maxtype = max_ii(sock->type, maxtype);

	/* try all types, starting from 'highest' (i.e. colors, vectors, values) */
	for (type = maxtype; type >= 0; --type) {
		for (sock = sockets->first; sock; sock = sock->next) {
			if (!nodeSocketIsHidden(sock) && type == sock->type) {
				return sock;
			}
		}
	}

	/* no visible sockets, unhide first of highest type */
	for (type = maxtype; type >= 0; --type) {
		for (sock = sockets->first; sock; sock = sock->next) {
			if (type == sock->type) {
				sock->flag &= ~SOCK_HIDDEN;
				return sock;
			}
		}
	}

	return NULL;
}

/* assumes link with NODE_LINKFLAG_HILITE set */
void ED_node_link_insert(ScrArea *sa)
{
	bNode *node, *select;
	SpaceNode *snode = ed_node_link_conditions(sa, &select);
	bNodeLink *link;
	bNodeSocket *sockto;

	if (snode == NULL) return;

	/* get the link */
	for (link = snode->edittree->links.first; link; link = link->next)
		if (link->flag & NODE_LINKFLAG_HILITE)
			break;

	if (link) {
		bNodeSocket *best_input = socket_best_match(&select->inputs);
		bNodeSocket *best_output = socket_best_match(&select->outputs);
		
		if (best_input && best_output) {
			node = link->tonode;
			sockto = link->tosock;
			
			link->tonode = select;
			link->tosock = best_input;
			node_remove_extra_links(snode, link->tosock, link);
			link->flag &= ~NODE_LINKFLAG_HILITE;
			
			nodeAddLink(snode->edittree, select, best_output, node, sockto);
			
			ntreeUpdateTree(snode->edittree);   /* needed for pointers */
			snode_update(snode, select);
			ED_node_tag_update_id(snode->id);
		}
	}
}
