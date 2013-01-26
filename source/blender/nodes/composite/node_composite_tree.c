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
 * Contributor(s):
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/nodes/composite/node_composite_tree.c
 *  \ingroup nodes
 */


#include <stdio.h>

#include "DNA_anim_types.h"
#include "DNA_color_types.h"
#include "DNA_scene_types.h"
#include "DNA_node_types.h"

#include "BLI_listbase.h"
#include "BLI_threads.h"

#include "BLF_translation.h"

#include "BKE_animsys.h"
#include "BKE_colortools.h"
#include "BKE_fcurve.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_tracking.h"

#include "node_common.h"
#include "node_util.h"

#include "PIL_time.h"

#include "RNA_access.h"

#include "NOD_composite.h"
#include "node_composite_util.h"

#ifdef WITH_COMPOSITOR
	#include "COM_compositor.h"
#endif

static void foreach_nodetree(Main *main, void *calldata, bNodeTreeCallback func)
{
	Scene *sce;
	for (sce= main->scene.first; sce; sce= sce->id.next) {
		if (sce->nodetree) {
			func(calldata, &sce->id, sce->nodetree);
		}
	}
}

static void foreach_nodeclass(Scene *UNUSED(scene), void *calldata, bNodeClassCallback func)
{
	func(calldata, NODE_CLASS_INPUT, N_("Input"));
	func(calldata, NODE_CLASS_OUTPUT, N_("Output"));
	func(calldata, NODE_CLASS_OP_COLOR, N_("Color"));
	func(calldata, NODE_CLASS_OP_VECTOR, N_("Vector"));
	func(calldata, NODE_CLASS_OP_FILTER, N_("Filter"));
	func(calldata, NODE_CLASS_CONVERTOR, N_("Convertor"));
	func(calldata, NODE_CLASS_MATTE, N_("Matte"));
	func(calldata, NODE_CLASS_DISTORT, N_("Distort"));
	func(calldata, NODE_CLASS_GROUP, N_("Group"));
	func(calldata, NODE_CLASS_LAYOUT, N_("Layout"));
}

static void free_node_cache(bNodeTree *UNUSED(ntree), bNode *node)
{
	bNodeSocket *sock;
	
	for (sock= node->outputs.first; sock; sock= sock->next) {
		if (sock->cache) {
			sock->cache= NULL;
		}
	}
}

static void free_cache(bNodeTree *ntree)
{
	bNode *node;
	for (node= ntree->nodes.first; node; node= node->next)
		free_node_cache(ntree, node);
}

static void update_node(bNodeTree *ntree, bNode *node)
{
	bNodeSocket *sock;

	for (sock= node->outputs.first; sock; sock= sock->next) {
		if (sock->cache) {
			//free_compbuf(sock->cache);
			//sock->cache= NULL;
		}
	}
	node->need_exec= 1;
	/* individual node update call */
	if (node->typeinfo->updatefunc)
		node->typeinfo->updatefunc(ntree, node);
}

/* local tree then owns all compbufs */
static void localize(bNodeTree *localtree, bNodeTree *ntree)
{
	bNode *node, *node_next;
	bNodeSocket *sock;
	
	for (node= ntree->nodes.first; node; node= node->next) {
		/* ensure new user input gets handled ok */
		node->need_exec= 0;
		node->new_node->original = node;
		
		/* move over the compbufs */
		/* right after ntreeCopyTree() oldsock pointers are valid */
		
		if (ELEM(node->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER)) {
			if (node->id) {
				if (node->flag & NODE_DO_OUTPUT)
					node->new_node->id= (ID *)node->id;
				else
					node->new_node->id= NULL;
			}
		}
		
		/* copy over the preview buffers to update graduatly */
		if (node->preview) {
			bNodePreview *preview = MEM_callocN(sizeof(bNodePreview), "Preview");
			preview->pad = node->preview->pad;
			preview->xsize = node->preview->xsize;
			preview->ysize = node->preview->ysize;
			preview->rect = MEM_dupallocN(node->preview->rect);
			node->new_node->preview = preview;
		}
		
		for (sock= node->outputs.first; sock; sock= sock->next) {
			sock->new_sock->cache= sock->cache;
			sock->cache= NULL;
			sock->new_sock->new_sock= sock;
		}
	}
	
	/* replace muted nodes and reroute nodes by internal links */
	for (node= localtree->nodes.first; node; node= node_next) {
		node_next = node->next;
		
		if (node->flag & NODE_MUTED || node->type == NODE_REROUTE) {
			/* make sure the update tag isn't lost when removing the muted node.
			 * propagate this to all downstream nodes.
			 */
			if (node->need_exec) {
				bNodeLink *link;
				for (link=localtree->links.first; link; link=link->next)
					if (link->fromnode==node && link->tonode)
						link->tonode->need_exec = 1;
			}
			
			nodeInternalRelink(localtree, node);
			nodeFreeNode(localtree, node);
		}
	}
}

static void local_sync(bNodeTree *localtree, bNodeTree *ntree)
{
	bNode *lnode;
	
	/* move over the compbufs and previews */
	for (lnode= localtree->nodes.first; lnode; lnode= lnode->next) {
		if ( (lnode->exec & NODE_READY) && !(lnode->exec & NODE_SKIPPED) ) {
			if (ntreeNodeExists(ntree, lnode->new_node)) {
				
				if (lnode->preview && lnode->preview->rect) {
					nodeFreePreview(lnode->new_node);
					lnode->new_node->preview= lnode->preview;
					lnode->preview= NULL;
				}
				
			}
		}
	}
}

static void local_merge(bNodeTree *localtree, bNodeTree *ntree)
{
	bNode *lnode;
	bNodeSocket *lsock;
	
	/* move over the compbufs and previews */
	for (lnode= localtree->nodes.first; lnode; lnode= lnode->next) {
		if (ntreeNodeExists(ntree, lnode->new_node)) {
			if (ELEM(lnode->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER)) {
				if (lnode->id && (lnode->flag & NODE_DO_OUTPUT)) {
					/* image_merge does sanity check for pointers */
					BKE_image_merge((Image *)lnode->new_node->id, (Image *)lnode->id);
				}
			}
			else if (lnode->type==CMP_NODE_MOVIEDISTORTION) {
				/* special case for distortion node: distortion context is allocating in exec function
				 * and to achieve much better performance on further calls this context should be
				 * copied back to original node */
				if (lnode->storage) {
					if (lnode->new_node->storage)
						BKE_tracking_distortion_free(lnode->new_node->storage);

					lnode->new_node->storage= BKE_tracking_distortion_copy(lnode->storage);
				}
			}
			
			for (lsock= lnode->outputs.first; lsock; lsock= lsock->next) {
				if (ntreeOutputExists(lnode->new_node, lsock->new_sock)) {
					lsock->new_sock->cache= lsock->cache;
					lsock->cache= NULL;
					lsock->new_sock= NULL;
				}
			}
		}
	}
}

static void update(bNodeTree *ntree)
{
	ntreeSetOutput(ntree);
	
	ntree_update_reroute_nodes(ntree);
}

bNodeTreeType ntreeType_Composite = {
	/* type */				NTREE_COMPOSIT,
	/* idname */			"NTCompositing Nodetree",
	
	/* node_types */		{ NULL, NULL },
	
	/* free_cache */		free_cache,
	/* free_node_cache */	free_node_cache,
	/* foreach_nodetree */	foreach_nodetree,
	/* foreach_nodeclass */	foreach_nodeclass,
	/* localize */			localize,
	/* local_sync */		local_sync,
	/* local_merge */		local_merge,
	/* update */			update,
	/* update_node */		update_node,
	/* validate_link */		NULL,
	/* update_internal_links */	node_update_internal_links_default
};


void *COM_linker_hack = NULL;

void ntreeCompositExecTree(bNodeTree *ntree, RenderData *rd, int rendering, int do_preview,
                           const ColorManagedViewSettings *view_settings,
                           const ColorManagedDisplaySettings *display_settings)
{
#ifdef WITH_COMPOSITOR
	COM_execute(rd, ntree, rendering, view_settings, display_settings);
#else
	(void)ntree, (void)rd, (void)rendering, (void)do_preview;
	(void)view_settings, (void)display_settings;
#endif

	(void)do_preview;
}

/* *********************************************** */

static void set_output_visible(bNode *node, int passflag, int index, int pass)
{
	bNodeSocket *sock = BLI_findlink(&node->outputs, index);
	/* clear the SOCK_HIDDEN flag as well, in case a socket was hidden before */
	if (passflag & pass)
		sock->flag &= ~(SOCK_HIDDEN | SOCK_UNAVAIL);
	else
		sock->flag |= SOCK_UNAVAIL;
}

/* clumsy checking... should do dynamic outputs once */
static void force_hidden_passes(bNode *node, int passflag)
{
	bNodeSocket *sock;
	
	for (sock= node->outputs.first; sock; sock= sock->next)
		sock->flag &= ~SOCK_UNAVAIL;
	
	set_output_visible(node, passflag, RRES_OUT_IMAGE,            SCE_PASS_COMBINED);
	set_output_visible(node, passflag, RRES_OUT_ALPHA,            SCE_PASS_COMBINED);
	
	set_output_visible(node, passflag, RRES_OUT_Z,                SCE_PASS_Z);
	set_output_visible(node, passflag, RRES_OUT_NORMAL,           SCE_PASS_NORMAL);
	set_output_visible(node, passflag, RRES_OUT_VEC,              SCE_PASS_VECTOR);
	set_output_visible(node, passflag, RRES_OUT_UV,               SCE_PASS_UV);
	set_output_visible(node, passflag, RRES_OUT_RGBA,             SCE_PASS_RGBA);
	set_output_visible(node, passflag, RRES_OUT_DIFF,             SCE_PASS_DIFFUSE);
	set_output_visible(node, passflag, RRES_OUT_SPEC,             SCE_PASS_SPEC);
	set_output_visible(node, passflag, RRES_OUT_SHADOW,           SCE_PASS_SHADOW);
	set_output_visible(node, passflag, RRES_OUT_AO,               SCE_PASS_AO);
	set_output_visible(node, passflag, RRES_OUT_REFLECT,          SCE_PASS_REFLECT);
	set_output_visible(node, passflag, RRES_OUT_REFRACT,          SCE_PASS_REFRACT);
	set_output_visible(node, passflag, RRES_OUT_INDIRECT,         SCE_PASS_INDIRECT);
	set_output_visible(node, passflag, RRES_OUT_INDEXOB,          SCE_PASS_INDEXOB);
	set_output_visible(node, passflag, RRES_OUT_INDEXMA,          SCE_PASS_INDEXMA);
	set_output_visible(node, passflag, RRES_OUT_MIST,             SCE_PASS_MIST);
	set_output_visible(node, passflag, RRES_OUT_EMIT,             SCE_PASS_EMIT);
	set_output_visible(node, passflag, RRES_OUT_ENV,              SCE_PASS_ENVIRONMENT);
	set_output_visible(node, passflag, RRES_OUT_DIFF_DIRECT,      SCE_PASS_DIFFUSE_DIRECT);
	set_output_visible(node, passflag, RRES_OUT_DIFF_INDIRECT,    SCE_PASS_DIFFUSE_INDIRECT);
	set_output_visible(node, passflag, RRES_OUT_DIFF_COLOR,       SCE_PASS_DIFFUSE_COLOR);
	set_output_visible(node, passflag, RRES_OUT_GLOSSY_DIRECT,    SCE_PASS_GLOSSY_DIRECT);
	set_output_visible(node, passflag, RRES_OUT_GLOSSY_INDIRECT,  SCE_PASS_GLOSSY_INDIRECT);
	set_output_visible(node, passflag, RRES_OUT_GLOSSY_COLOR,     SCE_PASS_GLOSSY_COLOR);
	set_output_visible(node, passflag, RRES_OUT_TRANSM_DIRECT,    SCE_PASS_TRANSM_DIRECT);
	set_output_visible(node, passflag, RRES_OUT_TRANSM_INDIRECT,  SCE_PASS_TRANSM_INDIRECT);
	set_output_visible(node, passflag, RRES_OUT_TRANSM_COLOR,     SCE_PASS_TRANSM_COLOR);
}

/* based on rules, force sockets hidden always */
void ntreeCompositForceHidden(bNodeTree *ntree, Scene *curscene)
{
	bNode *node;

	if (ntree == NULL) return;

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->type == CMP_NODE_R_LAYERS) {
			Scene *sce = node->id ? (Scene *)node->id : curscene;
			SceneRenderLayer *srl = BLI_findlink(&sce->r.layers, node->custom1);
			if (srl)
				force_hidden_passes(node, srl->passflag);
		}
		/* XXX this stuff is called all the time, don't want that.
		 * Updates should only happen when actually necessary.
		 */
		#if 0
		else if (node->type == CMP_NODE_IMAGE) {
			nodeUpdate(ntree, node);
		}
		#endif
	}

}

/* called from render pipeline, to tag render input and output */
/* need to do all scenes, to prevent errors when you re-render 1 scene */
void ntreeCompositTagRender(Scene *curscene)
{
	Scene *sce;

	for (sce = G.main->scene.first; sce; sce = sce->id.next) {
		if (sce->nodetree) {
			bNode *node;

			for (node = sce->nodetree->nodes.first; node; node = node->next) {
				if (node->id == (ID *)curscene || node->type == CMP_NODE_COMPOSITE)
					nodeUpdate(sce->nodetree, node);
				else if (node->type == CMP_NODE_TEXTURE) /* uses scene sizex/sizey */
					nodeUpdate(sce->nodetree, node);
			}
		}
	}
}

static int node_animation_properties(bNodeTree *ntree, bNode *node)
{
	bNodeSocket *sock;
	const ListBase *lb;
	Link *link;
	PointerRNA ptr;
	PropertyRNA *prop;

	/* check to see if any of the node's properties have fcurves */
	RNA_pointer_create((ID *)ntree, &RNA_Node, node, &ptr);
	lb = RNA_struct_type_properties(ptr.type);

	for (link = lb->first; link; link = link->next) {
		int driven, len = 1, index;
		prop = (PropertyRNA *)link;

		if (RNA_property_array_check(prop))
			len = RNA_property_array_length(&ptr, prop);

		for (index = 0; index < len; index++) {
			if (rna_get_fcurve(&ptr, prop, index, NULL, &driven)) {
				nodeUpdate(ntree, node);
				return 1;
			}
		}
	}

	/* now check node sockets */
	for (sock = node->inputs.first; sock; sock = sock->next) {
		int driven, len = 1, index;

		RNA_pointer_create((ID *)ntree, &RNA_NodeSocket, sock, &ptr);
		prop = RNA_struct_find_property(&ptr, "default_value");
		if (prop) {
			if (RNA_property_array_check(prop))
				len = RNA_property_array_length(&ptr, prop);

			for (index = 0; index < len; index++) {
				if (rna_get_fcurve(&ptr, prop, index, NULL, &driven)) {
					nodeUpdate(ntree, node);
					return 1;
				}
			}
		}
	}

	return 0;
}

/* tags nodes that have animation capabilities */
int ntreeCompositTagAnimated(bNodeTree *ntree)
{
	bNode *node;
	int tagged = 0;

	if (ntree == NULL) return 0;

	for (node = ntree->nodes.first; node; node = node->next) {

		tagged = node_animation_properties(ntree, node);

		/* otherwise always tag these node types */
		if (node->type == CMP_NODE_IMAGE) {
			Image *ima = (Image *)node->id;
			if (ima && ELEM(ima->source, IMA_SRC_MOVIE, IMA_SRC_SEQUENCE)) {
				nodeUpdate(ntree, node);
				tagged = 1;
			}
		}
		else if (node->type == CMP_NODE_TIME) {
			nodeUpdate(ntree, node);
			tagged = 1;
		}
		/* here was tag render layer, but this is called after a render, so re-composites fail */
		else if (node->type == NODE_GROUP) {
			if (ntreeCompositTagAnimated((bNodeTree *)node->id) ) {
				nodeUpdate(ntree, node);
			}
		}
		else if (ELEM(node->type, CMP_NODE_MOVIECLIP, CMP_NODE_TRANSFORM)) {
			nodeUpdate(ntree, node);
			tagged = 1;
		}
		else if (node->type == CMP_NODE_MASK) {
			nodeUpdate(ntree, node);
			tagged = 1;
		}
	}

	return tagged;
}


/* called from image window preview */
void ntreeCompositTagGenerators(bNodeTree *ntree)
{
	bNode *node;

	if (ntree == NULL) return;

	for (node = ntree->nodes.first; node; node = node->next) {
		if (ELEM(node->type, CMP_NODE_R_LAYERS, CMP_NODE_IMAGE))
			nodeUpdate(ntree, node);
	}
}

/* XXX after render animation system gets a refresh, this call allows composite to end clean */
void ntreeCompositClearTags(bNodeTree *ntree)
{
	bNode *node;

	if (ntree == NULL) return;

	for (node = ntree->nodes.first; node; node = node->next) {
		node->need_exec = 0;
		if (node->type == NODE_GROUP)
			ntreeCompositClearTags((bNodeTree *)node->id);
	}
}
