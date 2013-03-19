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

/** \file blender/editors/space_node/node_edit.c
 *  \ingroup spnode
 */

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_anim_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_text_types.h"
#include "DNA_world_types.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"

#include "BKE_blender.h"
#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_paint.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_texture.h"

#include "RE_engine.h"
#include "RE_pipeline.h"


#include "ED_node.h"  /* own include */
#include "ED_screen.h"
#include "ED_render.h"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_view2d.h"

#include "GPU_material.h"

#include "IMB_imbuf_types.h"

#include "node_intern.h"  /* own include */
#include "NOD_common.h"
#include "NOD_socket.h"
#include "NOD_composite.h"
#include "NOD_shader.h"
#include "NOD_texture.h"


#define USE_ESC_COMPO

/* ***************** composite job manager ********************** */

typedef struct CompoJob {
	Scene *scene;
	bNodeTree *ntree;
	bNodeTree *localtree;
	short *stop;
	short *do_update;
	float *progress;
	short need_sync;
} CompoJob;

/* called by compo, only to check job 'stop' value */
static int compo_breakjob(void *cjv)
{
	CompoJob *cj = cjv;
	
	/* without G.is_break 'ESC' wont quit - which annoys users */
	return (*(cj->stop)
#ifdef USE_ESC_COMPO
	        ||
	        G.is_break
#endif
	        );
}

/* called by compo, wmJob sends notifier, old compositor system only */
static void compo_statsdrawjob(void *cjv, char *UNUSED(str))
{
	CompoJob *cj = cjv;
	
	*(cj->do_update) = TRUE;
	cj->need_sync = TRUE;
}

/* called by compo, wmJob sends notifier */
static void compo_redrawjob(void *cjv)
{
	CompoJob *cj = cjv;
	
	*(cj->do_update) = TRUE;
}

static void compo_freejob(void *cjv)
{
	CompoJob *cj = cjv;

	if (cj->localtree) {
		ntreeLocalMerge(cj->localtree, cj->ntree);
	}
	MEM_freeN(cj);
}

/* only now we copy the nodetree, so adding many jobs while
 * sliding buttons doesn't frustrate */
static void compo_initjob(void *cjv)
{
	CompoJob *cj = cjv;

	cj->localtree = ntreeLocalize(cj->ntree);
}

/* called before redraw notifiers, it moves finished previews over */
static void compo_updatejob(void *cjv)
{
	CompoJob *cj = cjv;

	if (cj->need_sync) {
		/* was used by old compositor system only */
		ntreeLocalSync(cj->localtree, cj->ntree);

		cj->need_sync = FALSE;
	}

	WM_main_add_notifier(NC_WINDOW | ND_DRAW, NULL);
}

static void compo_progressjob(void *cjv, float progress)
{
	CompoJob *cj = cjv;
	
	*(cj->progress) = progress;
}


/* only this runs inside thread */
static void compo_startjob(void *cjv, short *stop, short *do_update, float *progress)
{
	CompoJob *cj = cjv;
	bNodeTree *ntree = cj->localtree;
	Scene *scene = cj->scene;

	if (scene->use_nodes == FALSE)
		return;
	
	cj->stop = stop;
	cj->do_update = do_update;
	cj->progress = progress;

	ntree->test_break = compo_breakjob;
	ntree->tbh = cj;
	ntree->stats_draw = compo_statsdrawjob;
	ntree->sdh = cj;
	ntree->progress = compo_progressjob;
	ntree->prh = cj;
	ntree->update_draw = compo_redrawjob;
	ntree->udh = cj;

	// XXX BIF_store_spare();
	
	ntreeCompositExecTree(ntree, &cj->scene->r, 0, 1, &scene->view_settings, &scene->display_settings);  /* 1 is do_previews */

	ntree->test_break = NULL;
	ntree->stats_draw = NULL;
	ntree->progress = NULL;

}

/**
 * \param scene_owner is the owner of the job,
 * we don't use it for anything else currently so could also be a void pointer,
 * but for now keep it an 'Scene' for consistency.
 *
 * \note only call from spaces `refresh` callbacks, not direct! - use with care.
 */
void ED_node_composite_job(const bContext *C, struct bNodeTree *nodetree, Scene *scene_owner)
{
	wmJob *wm_job;
	CompoJob *cj;

	/* to fix bug: [#32272] */
	if (G.is_rendering) {
		return;
	}

#ifdef USE_ESC_COMPO
	G.is_break = FALSE;
#endif

	wm_job = WM_jobs_get(CTX_wm_manager(C), CTX_wm_window(C), scene_owner, "Compositing",
	                     WM_JOB_EXCL_RENDER | WM_JOB_PROGRESS, WM_JOB_TYPE_COMPOSITE);
	cj = MEM_callocN(sizeof(CompoJob), "compo job");

	/* customdata for preview thread */
	cj->scene = CTX_data_scene(C);
	cj->ntree = nodetree;

	/* setup job */
	WM_jobs_customdata_set(wm_job, cj, compo_freejob);
	WM_jobs_timer(wm_job, 0.1, NC_SCENE, NC_SCENE | ND_COMPO_RESULT);
	WM_jobs_callbacks(wm_job, compo_startjob, compo_initjob, compo_updatejob, NULL);

	WM_jobs_start(CTX_wm_manager(C), wm_job);
}

/* ***************************************** */

/* operator poll callback */
int composite_node_active(bContext *C)
{
	if (ED_operator_node_active(C)) {
		SpaceNode *snode = CTX_wm_space_node(C);
		if (ED_node_is_compositor(snode))
			return 1;
	}
	return 0;
}

static int has_nodetree(bNodeTree *ntree, bNodeTree *lookup)
{
	bNode *node;
	
	if (ntree == lookup)
		return 1;
	
	for (node = ntree->nodes.first; node; node = node->next)
		if (node->type == NODE_GROUP && node->id)
			if (has_nodetree((bNodeTree *)node->id, lookup))
				return 1;
	
	return 0;
}

void snode_dag_update(bContext *C, SpaceNode *snode)
{
	Main *bmain = CTX_data_main(C);

	/* for groups, update all ID's using this */
	if (snode->edittree != snode->nodetree) {
		FOREACH_NODETREE(bmain, tntree, id) {
			if (has_nodetree(tntree, snode->edittree))
				DAG_id_tag_update(id, 0);
		} FOREACH_NODETREE_END
	}

	DAG_id_tag_update(snode->id, 0);
}

void snode_notify(bContext *C, SpaceNode *snode)
{
	WM_event_add_notifier(C, NC_NODE | NA_EDITED, NULL);

	if (ED_node_is_shader(snode))
		WM_event_add_notifier(C, NC_MATERIAL | ND_NODES, snode->id);
	else if (ED_node_is_compositor(snode))
		WM_event_add_notifier(C, NC_SCENE | ND_NODES, snode->id);
	else if (ED_node_is_texture(snode))
		WM_event_add_notifier(C, NC_TEXTURE | ND_NODES, snode->id);
}

void ED_node_set_tree_type(SpaceNode *snode, bNodeTreeType *typeinfo)
{
	if (typeinfo)
		BLI_strncpy(snode->tree_idname, typeinfo->idname, sizeof(snode->tree_idname));
	else
		snode->tree_idname[0] = '\0';
}

int ED_node_is_compositor(struct SpaceNode *snode)
{
	return STREQ(snode->tree_idname, ntreeType_Composite->idname);
}

int ED_node_is_shader(struct SpaceNode *snode)
{
	return STREQ(snode->tree_idname, ntreeType_Shader->idname);
}

int ED_node_is_texture(struct SpaceNode *snode)
{
	return STREQ(snode->tree_idname, ntreeType_Texture->idname);
}

/* assumes nothing being done in ntree yet, sets the default in/out node */
/* called from shading buttons or header */
void ED_node_shader_default(const bContext *C, ID *id)
{
	Scene *scene = CTX_data_scene(C);
	bNode *in, *out;
	bNodeSocket *fromsock, *tosock, *sock;
	bNodeTree *ntree;
	PointerRNA ptr;
	int output_type, shader_type;
	float color[4] = { 0.0f, 0.0f, 0.0f, 1.0f }, strength = 1.0f;
	
	ntree = ntreeAddTree(NULL, "Shader Nodetree", ntreeType_Shader->idname);

	RNA_id_pointer_create((ID *)ntree, &ptr);
	RNA_boolean_set(&ptr, "is_local_tree", TRUE);

	switch (GS(id->name)) {
		case ID_MA:
		{
			Material *ma = (Material *)id;
			ma->nodetree = ntree;

			if (BKE_scene_use_new_shading_nodes(scene)) {
				output_type = SH_NODE_OUTPUT_MATERIAL;
				shader_type = SH_NODE_BSDF_DIFFUSE;
			}
			else {
				output_type = SH_NODE_OUTPUT;
				shader_type = SH_NODE_MATERIAL;
			}

			copy_v3_v3(color, &ma->r);
			strength = 0.0f;
			break;
		}
		case ID_WO:
		{
			World *wo = (World *)id;
			wo->nodetree = ntree;

			output_type = SH_NODE_OUTPUT_WORLD;
			shader_type = SH_NODE_BACKGROUND;

			copy_v3_v3(color, &wo->horr);
			strength = 1.0f;
			break;
		}
		case ID_LA:
		{
			Lamp *la = (Lamp *)id;
			la->nodetree = ntree;

			output_type = SH_NODE_OUTPUT_LAMP;
			shader_type = SH_NODE_EMISSION;

			copy_v3_v3(color, &la->r);
			if (la->type == LA_LOCAL || la->type == LA_SPOT || la->type == LA_AREA)
				strength = 100.0f;
			else
				strength = 1.0f;
			break;
		}
		default:
			printf("ED_node_shader_default called on wrong ID type.\n");
			return;
	}
	
	out = nodeAddStaticNode(C, ntree, output_type);
	out->locx = 300.0f; out->locy = 300.0f;
	
	in = nodeAddStaticNode(C, ntree, shader_type);
	in->locx = 10.0f; in->locy = 300.0f;
	nodeSetActive(ntree, in);
	
	/* only a link from color to color */
	fromsock = in->outputs.first;
	tosock = out->inputs.first;
	nodeAddLink(ntree, in, fromsock, out, tosock);

	/* default values */
	if (BKE_scene_use_new_shading_nodes(scene)) {
		PointerRNA sockptr;
		sock = in->inputs.first;
		RNA_pointer_create((ID *)ntree, &RNA_NodeSocket, sock, &sockptr);
		
		RNA_float_set_array(&sockptr, "default_value", color);

		if (strength != 0.0f) {
			sock = in->inputs.last;
			RNA_pointer_create((ID *)ntree, &RNA_NodeSocket, sock, &sockptr);
			RNA_float_set(&sockptr, "default_value", strength);
		}
	}
	
	ntreeUpdateTree(ntree);
}

/* assumes nothing being done in ntree yet, sets the default in/out node */
/* called from shading buttons or header */
void ED_node_composit_default(const bContext *C, struct Scene *sce)
{
	bNode *in, *out;
	bNodeSocket *fromsock, *tosock;
	PointerRNA ptr;
	
	/* but lets check it anyway */
	if (sce->nodetree) {
		if (G.debug & G_DEBUG)
			printf("error in composite initialize\n");
		return;
	}
	
	sce->nodetree = ntreeAddTree(NULL, "Compositing Nodetree", ntreeType_Composite->idname);
	
	RNA_id_pointer_create((ID *)sce->nodetree, &ptr);
	RNA_boolean_set(&ptr, "is_local_tree", TRUE);
	
	sce->nodetree->chunksize = 256;
	sce->nodetree->edit_quality = NTREE_QUALITY_HIGH;
	sce->nodetree->render_quality = NTREE_QUALITY_HIGH;
	
	out = nodeAddStaticNode(C, sce->nodetree, CMP_NODE_COMPOSITE);
	out->locx = 300.0f; out->locy = 400.0f;
	out->id = &sce->id;
	id_us_plus(out->id);
	
	in = nodeAddStaticNode(C, sce->nodetree, CMP_NODE_R_LAYERS);
	in->locx = 10.0f; in->locy = 400.0f;
	in->id = &sce->id;
	id_us_plus(in->id);
	nodeSetActive(sce->nodetree, in);
	
	/* links from color to color */
	fromsock = in->outputs.first;
	tosock = out->inputs.first;
	nodeAddLink(sce->nodetree, in, fromsock, out, tosock);
	
	ntreeUpdateTree(sce->nodetree);
	
	// XXX ntreeCompositForceHidden(sce->nodetree);
}

/* assumes nothing being done in ntree yet, sets the default in/out node */
/* called from shading buttons or header */
void ED_node_texture_default(const bContext *C, Tex *tx)
{
	bNode *in, *out;
	bNodeSocket *fromsock, *tosock;
	PointerRNA ptr;
	
	/* but lets check it anyway */
	if (tx->nodetree) {
		if (G.debug & G_DEBUG)
			printf("error in texture initialize\n");
		return;
	}
	
	tx->nodetree = ntreeAddTree(NULL, "Texture Nodetree", ntreeType_Texture->idname);
	
	RNA_id_pointer_create((ID *)tx->nodetree, &ptr);
	RNA_boolean_set(&ptr, "is_local_tree", TRUE);
	
	out = nodeAddStaticNode(C, tx->nodetree, TEX_NODE_OUTPUT);
	out->locx = 300.0f; out->locy = 300.0f;
	
	in = nodeAddStaticNode(C, tx->nodetree, TEX_NODE_CHECKER);
	in->locx = 10.0f; in->locy = 300.0f;
	nodeSetActive(tx->nodetree, in);
	
	fromsock = in->outputs.first;
	tosock = out->inputs.first;
	nodeAddLink(tx->nodetree, in, fromsock, out, tosock);
	
	ntreeUpdateTree(tx->nodetree);
}

/* Here we set the active tree(s), even called for each redraw now, so keep it fast :) */
void snode_set_context(const bContext *C)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTreeType *treetype = ntreeTypeFind(snode->tree_idname);
	bNodeTree *ntree = snode->nodetree;
	ID *id = snode->id, *from = snode->from;
	
	/* we use this to signal warnings, when node shaders are drawn in wrong render engine */
	if (BKE_scene_use_new_shading_nodes(CTX_data_scene(C)))
		snode->flag |= SNODE_NEW_SHADERS;
	else
		snode->flag &= ~SNODE_NEW_SHADERS;
	
	/* check the tree type */
	if (!treetype ||
	    (treetype->poll && !treetype->poll(C, treetype)))
	{
		/* invalid tree type, disable */
		snode->tree_idname[0] = '\0';
		ED_node_tree_start(snode, NULL, NULL, NULL);
		return;
	}
	
	if (snode->nodetree && strcmp(snode->nodetree->idname, snode->tree_idname) != 0) {
		/* current tree does not match selected type, clear tree path */
		ntree = NULL;
		id = NULL;
		from = NULL;
	}
	
	if (!(snode->flag & SNODE_PIN) || ntree == NULL) {
		if (treetype->get_from_context) {
			/* reset and update from context */
			ntree = NULL;
			id = NULL;
			from = NULL;
			
			treetype->get_from_context(C, treetype, &ntree, &id, &from);
		}
	}
	
	if (snode->nodetree != ntree || snode->id != id || snode->from != from) {
		ED_node_tree_start(snode, ntree, id, from);
	}
}

void snode_update(SpaceNode *snode, bNode *node)
{
	bNodeTreePath *path;
	
	/* XXX this only updates nodes in the current node space tree path.
	 * The function supposedly should update any potential group node linking to changed tree,
	 * this really requires a working depsgraph ...
	 */
	
	/* update all edited group nodes */
	path = snode->treepath.last;
	if (path) {
		bNodeTree *ngroup = path->nodetree;
		for (path = path->prev; path; path = path->prev) {
			nodeUpdateID(path->nodetree, (ID *)ngroup);
			ngroup = path->nodetree;
		}
	}

	if (node)
		nodeUpdate(snode->edittree, node);
}

void ED_node_set_active(Main *bmain, bNodeTree *ntree, bNode *node)
{
	int was_active_texture = (node->flag & NODE_ACTIVE_TEXTURE);

	nodeSetActive(ntree, node);
	
	if (node->type != NODE_GROUP) {
		int was_output = (node->flag & NODE_DO_OUTPUT);
		int do_update = 0;
		
		/* generic node group output: set node as active output */
		if (node->type == NODE_GROUP_OUTPUT) {
			bNode *tnode;
			for (tnode = ntree->nodes.first; tnode; tnode = tnode->next)
				if (tnode->type == NODE_GROUP_OUTPUT)
					tnode->flag &= ~NODE_DO_OUTPUT;
			
			node->flag |= NODE_DO_OUTPUT;
			if (!was_output)
				do_update = 1;
		}
		
		/* tree specific activate calls */
		if (ntree->type == NTREE_SHADER) {
			/* when we select a material, active texture is cleared, for buttons */
			if (node->id && ELEM3(GS(node->id->name), ID_MA, ID_LA, ID_WO))
				nodeClearActiveID(ntree, ID_TE);
			
			if (node->type == SH_NODE_OUTPUT) {
				bNode *tnode;
				
				for (tnode = ntree->nodes.first; tnode; tnode = tnode->next)
					if (tnode->type == SH_NODE_OUTPUT)
						tnode->flag &= ~NODE_DO_OUTPUT;
				
				node->flag |= NODE_DO_OUTPUT;
				if (was_output == 0)
					ED_node_tag_update_nodetree(bmain, ntree);
			}
			else if (do_update)
				ED_node_tag_update_nodetree(bmain, ntree);

			/* if active texture changed, free glsl materials */
			if ((node->flag & NODE_ACTIVE_TEXTURE) && !was_active_texture) {
				Material *ma;

				for (ma = bmain->mat.first; ma; ma = ma->id.next)
					if (ma->nodetree && ma->use_nodes && has_nodetree(ma->nodetree, ntree))
						GPU_material_free(ma);

				WM_main_add_notifier(NC_IMAGE, NULL);
			}

			WM_main_add_notifier(NC_MATERIAL | ND_NODES, node->id);
		}
		else if (ntree->type == NTREE_COMPOSIT) {
			/* make active viewer, currently only 1 supported... */
			if (ELEM(node->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER)) {
				bNode *tnode;
				

				for (tnode = ntree->nodes.first; tnode; tnode = tnode->next)
					if (ELEM(tnode->type, CMP_NODE_VIEWER, CMP_NODE_SPLITVIEWER))
						tnode->flag &= ~NODE_DO_OUTPUT;
				
				node->flag |= NODE_DO_OUTPUT;
				if (was_output == 0)
					ED_node_tag_update_nodetree(bmain, ntree);
				
				/* addnode() doesnt link this yet... */
				node->id = (ID *)BKE_image_verify_viewer(IMA_TYPE_COMPOSITE, "Viewer Node");
			}
			else if (node->type == CMP_NODE_R_LAYERS) {
				Scene *scene;

				for (scene = bmain->scene.first; scene; scene = scene->id.next) {
					if (scene->nodetree && scene->use_nodes && has_nodetree(scene->nodetree, ntree)) {
						if (node->id == NULL || node->id == (ID *)scene) {
							scene->r.actlay = node->custom1;
						}
					}
				}
			}
			else if (node->type == CMP_NODE_COMPOSITE) {
				if (was_output == 0) {
					bNode *tnode;
					
					for (tnode = ntree->nodes.first; tnode; tnode = tnode->next)
						if (tnode->type == CMP_NODE_COMPOSITE)
							tnode->flag &= ~NODE_DO_OUTPUT;
					
					node->flag |= NODE_DO_OUTPUT;
					ED_node_tag_update_nodetree(bmain, ntree);
				}
			}
			else if (do_update)
				ED_node_tag_update_nodetree(bmain, ntree);
		}
		else if (ntree->type == NTREE_TEXTURE) {
			// XXX
#if 0
			if (node->id)
				;  // XXX BIF_preview_changed(-1);
			// allqueue(REDRAWBUTSSHADING, 1);
			// allqueue(REDRAWIPO, 0);
#endif
		}
	}
}

void ED_node_post_apply_transform(bContext *UNUSED(C), bNodeTree *UNUSED(ntree))
{
	/* XXX This does not work due to layout functions relying on node->block,
	 * which only exists during actual drawing. Can we rely on valid totr rects?
	 */
	/* make sure nodes have correct bounding boxes after transform */
	/* node_update_nodetree(C, ntree, 0.0f, 0.0f); */
}

/* ***************** generic operator functions for nodes ***************** */

#if 0 /* UNUSED */

static int edit_node_poll(bContext *C)
{
	return ED_operator_node_active(C);
}

static void edit_node_properties(wmOperatorType *ot)
{
	/* XXX could node be a context pointer? */
	RNA_def_string(ot->srna, "node", "", MAX_NAME, "Node", "");
	RNA_def_int(ot->srna, "socket", 0, 0, MAX_SOCKET, "Socket", "", 0, MAX_SOCKET);
	RNA_def_enum(ot->srna, "in_out", node_socket_in_out_items, SOCK_IN, "Socket Side", "");
}

static int edit_node_invoke_properties(bContext *C, wmOperator *op)
{
	if (!RNA_struct_property_is_set(op->ptr, "node")) {
		bNode *node = CTX_data_pointer_get_type(C, "node", &RNA_Node).data;
		if (!node)
			return 0;
		else
			RNA_string_set(op->ptr, "node", node->name);
	}
	
	if (!RNA_struct_property_is_set(op->ptr, "in_out"))
		RNA_enum_set(op->ptr, "in_out", SOCK_IN);
	
	if (!RNA_struct_property_is_set(op->ptr, "socket"))
		RNA_int_set(op->ptr, "socket", 0);
	
	return 1;
}

static void edit_node_properties_get(wmOperator *op, bNodeTree *ntree, bNode **rnode, bNodeSocket **rsock, int *rin_out)
{
	bNode *node;
	bNodeSocket *sock = NULL;
	char nodename[MAX_NAME];
	int sockindex;
	int in_out;
	
	RNA_string_get(op->ptr, "node", nodename);
	node = nodeFindNodebyName(ntree, nodename);
	
	in_out = RNA_enum_get(op->ptr, "in_out");
	
	sockindex = RNA_int_get(op->ptr, "socket");
	switch (in_out) {
		case SOCK_IN:   sock = BLI_findlink(&node->inputs, sockindex);  break;
		case SOCK_OUT:  sock = BLI_findlink(&node->outputs, sockindex); break;
	}
	
	if (rnode)
		*rnode = node;
	if (rsock)
		*rsock = sock;
	if (rin_out)
		*rin_out = in_out;
}
#endif

/* ************************** Node generic ************** */

/* is rct in visible part of node? */
static bNode *visible_node(SpaceNode *snode, const rctf *rct)
{
	bNode *node;
	
	for (node = snode->edittree->nodes.last; node; node = node->prev) {
		if (BLI_rctf_isect(&node->totr, rct, NULL))
			break;
	}
	return node;
}

/* ********************** size widget operator ******************** */

typedef struct NodeSizeWidget {
	float mxstart, mystart;
	float oldlocx, oldlocy;
	float oldoffsetx, oldoffsety;
	float oldwidth, oldheight;
	float oldminiwidth;
	int directions;
} NodeSizeWidget;

static void node_resize_init(bContext *C, wmOperator *op, const wmEvent *UNUSED(event), bNode *node, int dir)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	
	NodeSizeWidget *nsw = MEM_callocN(sizeof(NodeSizeWidget), "size widget op data");
	
	op->customdata = nsw;
	nsw->mxstart = snode->cursor[0];
	nsw->mystart = snode->cursor[1];
	
	/* store old */
	nsw->oldlocx = node->locx;
	nsw->oldlocy = node->locy;
	nsw->oldoffsetx = node->offsetx;
	nsw->oldoffsety = node->offsety;
	nsw->oldwidth = node->width;
	nsw->oldheight = node->height;
	nsw->oldminiwidth = node->miniwidth;
	nsw->directions = dir;
	
	WM_cursor_modal(CTX_wm_window(C), node_get_resize_cursor(dir));
	/* add modal handler */
	WM_event_add_modal_handler(C, op);
}

static void node_resize_exit(bContext *C, wmOperator *op, int UNUSED(cancel))
{
	WM_cursor_restore(CTX_wm_window(C));
	
	MEM_freeN(op->customdata);
	op->customdata = NULL;
}

static int node_resize_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	ARegion *ar = CTX_wm_region(C);
	bNode *node = nodeGetActive(snode->edittree);
	NodeSizeWidget *nsw = op->customdata;
	float mx, my, dx, dy;
	
	switch (event->type) {
		case MOUSEMOVE:
			
			UI_view2d_region_to_view(&ar->v2d, event->mval[0], event->mval[1], &mx, &my);
			dx = (mx - nsw->mxstart) / UI_DPI_FAC;
			dy = (my - nsw->mystart) / UI_DPI_FAC;
			
			if (node) {
				if (node->flag & NODE_HIDDEN) {
					float widthmin = 0.0f;
					float widthmax = 100.0f;
					if (nsw->directions & NODE_RESIZE_RIGHT) {
						node->miniwidth = nsw->oldminiwidth + dx;
						CLAMP(node->miniwidth, widthmin, widthmax);
					}
					if (nsw->directions & NODE_RESIZE_LEFT) {
						float locmax = nsw->oldlocx + nsw->oldminiwidth;
						
						node->locx = nsw->oldlocx + dx;
						CLAMP(node->locx, locmax - widthmax, locmax - widthmin);
						node->miniwidth = locmax - node->locx;
					}
				}
				else {
					float widthmin = node->typeinfo->minwidth;
					float widthmax = node->typeinfo->maxwidth;
					if (nsw->directions & NODE_RESIZE_RIGHT) {
						node->width = nsw->oldwidth + dx;
						CLAMP(node->width, widthmin, widthmax);
					}
					if (nsw->directions & NODE_RESIZE_LEFT) {
						float locmax = nsw->oldlocx + nsw->oldwidth;
						
						node->locx = nsw->oldlocx + dx;
						CLAMP(node->locx, locmax - widthmax, locmax - widthmin);
						node->width = locmax - node->locx;
					}
				}
			
				/* height works the other way round ... */
				{
					float heightmin = UI_DPI_FAC * node->typeinfo->minheight;
					float heightmax = UI_DPI_FAC * node->typeinfo->maxheight;
					if (nsw->directions & NODE_RESIZE_TOP) {
						float locmin = nsw->oldlocy - nsw->oldheight;
						
						node->locy = nsw->oldlocy + dy;
						CLAMP(node->locy, locmin + heightmin, locmin + heightmax);
						node->height = node->locy - locmin;
					}
					if (nsw->directions & NODE_RESIZE_BOTTOM) {
						node->height = nsw->oldheight - dy;
						CLAMP(node->height, heightmin, heightmax);
					}
				}
				
				/* XXX make callback? */
				if (node->type == NODE_FRAME) {
					/* keep the offset symmetric around center point */
					if (nsw->directions & NODE_RESIZE_LEFT) {
						node->locx = nsw->oldlocx + 0.5f * dx;
						node->offsetx = nsw->oldoffsetx + 0.5f * dx;
					}
					if (nsw->directions & NODE_RESIZE_RIGHT) {
						node->locx = nsw->oldlocx + 0.5f * dx;
						node->offsetx = nsw->oldoffsetx - 0.5f * dx;
					}
					if (nsw->directions & NODE_RESIZE_TOP) {
						node->locy = nsw->oldlocy + 0.5f * dy;
						node->offsety = nsw->oldoffsety + 0.5f * dy;
					}
					if (nsw->directions & NODE_RESIZE_BOTTOM) {
						node->locy = nsw->oldlocy + 0.5f * dy;
						node->offsety = nsw->oldoffsety - 0.5f * dy;
					}
				}
			}
				
			ED_region_tag_redraw(ar);

			break;
			
		case LEFTMOUSE:
		case MIDDLEMOUSE:
		case RIGHTMOUSE:
			
			node_resize_exit(C, op, 0);
			ED_node_post_apply_transform(C, snode->edittree);
			
			return OPERATOR_FINISHED;
	}
	
	return OPERATOR_RUNNING_MODAL;
}

static int node_resize_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	ARegion *ar = CTX_wm_region(C);
	bNode *node = nodeGetActive(snode->edittree);
	int dir;
	
	if (node) {
		/* convert mouse coordinates to v2d space */
		UI_view2d_region_to_view(&ar->v2d, event->mval[0], event->mval[1],
		                         &snode->cursor[0], &snode->cursor[1]);
		dir = node->typeinfo->resize_area_func(node, snode->cursor[0], snode->cursor[1]);
		if (dir != 0) {
			node_resize_init(C, op, event, node, dir);
			return OPERATOR_RUNNING_MODAL;
		}
	}
	return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
}

static int node_resize_cancel(bContext *C, wmOperator *op)
{
	node_resize_exit(C, op, 1);

	return OPERATOR_CANCELLED;
}

void NODE_OT_resize(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Resize Node";
	ot->idname = "NODE_OT_resize";
	ot->description = "Resize a node";
	
	/* api callbacks */
	ot->invoke = node_resize_invoke;
	ot->modal = node_resize_modal;
	ot->poll = ED_operator_node_active;
	ot->cancel = node_resize_cancel;
	
	/* flags */
	ot->flag = OPTYPE_BLOCKING;
}


/* ********************** hidden sockets ******************** */

int node_has_hidden_sockets(bNode *node)
{
	bNodeSocket *sock;
	
	for (sock = node->inputs.first; sock; sock = sock->next)
		if (sock->flag & SOCK_HIDDEN)
			return 1;
	for (sock = node->outputs.first; sock; sock = sock->next)
		if (sock->flag & SOCK_HIDDEN)
			return 1;
	return 0;
}

void node_set_hidden_sockets(SpaceNode *snode, bNode *node, int set)
{
	bNodeSocket *sock;

	if (set == 0) {
		for (sock = node->inputs.first; sock; sock = sock->next)
			sock->flag &= ~SOCK_HIDDEN;
		for (sock = node->outputs.first; sock; sock = sock->next)
			sock->flag &= ~SOCK_HIDDEN;
	}
	else {
		/* hide unused sockets */
		for (sock = node->inputs.first; sock; sock = sock->next) {
			if (sock->link == NULL)
				sock->flag |= SOCK_HIDDEN;
		}
		for (sock = node->outputs.first; sock; sock = sock->next) {
			if (nodeCountSocketLinks(snode->edittree, sock) == 0)
				sock->flag |= SOCK_HIDDEN;
		}
	}
}


/* checks snode->mouse position, and returns found node/socket */
/* type is SOCK_IN and/or SOCK_OUT */
int node_find_indicated_socket(SpaceNode *snode, bNode **nodep, bNodeSocket **sockp, int in_out)
{
	bNode *node;
	bNodeSocket *sock;
	rctf rect;
	
	*nodep = NULL;
	*sockp = NULL;
	
	/* check if we click in a socket */
	for (node = snode->edittree->nodes.first; node; node = node->next) {
		
		rect.xmin = snode->cursor[0] - (NODE_SOCKSIZE + 4);
		rect.ymin = snode->cursor[1] - (NODE_SOCKSIZE + 4);
		rect.xmax = snode->cursor[0] + (NODE_SOCKSIZE + 4);
		rect.ymax = snode->cursor[1] + (NODE_SOCKSIZE + 4);
		
		if (!(node->flag & NODE_HIDDEN)) {
			/* extra padding inside and out - allow dragging on the text areas too */
			if (in_out == SOCK_IN) {
				rect.xmax += NODE_SOCKSIZE;
				rect.xmin -= NODE_SOCKSIZE * 4;
			}
			else if (in_out == SOCK_OUT) {
				rect.xmax += NODE_SOCKSIZE * 4;
				rect.xmin -= NODE_SOCKSIZE;
			}
		}
		
		if (in_out & SOCK_IN) {
			for (sock = node->inputs.first; sock; sock = sock->next) {
				if (!nodeSocketIsHidden(sock)) {
					if (BLI_rctf_isect_pt(&rect, sock->locx, sock->locy)) {
						if (node == visible_node(snode, &rect)) {
							*nodep = node;
							*sockp = sock;
							return 1;
						}
					}
				}
			}
		}
		if (in_out & SOCK_OUT) {
			for (sock = node->outputs.first; sock; sock = sock->next) {
				if (!nodeSocketIsHidden(sock)) {
					if (BLI_rctf_isect_pt(&rect, sock->locx, sock->locy)) {
						if (node == visible_node(snode, &rect)) {
							*nodep = node;
							*sockp = sock;
							return 1;
						}
					}
				}
			}
		}
	}
	
	return 0;
}

/* ****************** Duplicate *********************** */

static void node_duplicate_reparent_recursive(bNode *node)
{
	bNode *parent;
	
	node->flag |= NODE_TEST;
	
	/* find first selected parent */
	for (parent = node->parent; parent; parent = parent->parent) {
		if (parent->flag & SELECT) {
			if (!(parent->flag & NODE_TEST))
				node_duplicate_reparent_recursive(parent);
			break;
		}
	}
	/* reparent node copy to parent copy */
	if (parent) {
		nodeDetachNode(node->new_node);
		nodeAttachNode(node->new_node, parent->new_node);
	}
}

static int node_duplicate_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *node, *newnode, *lastnode;
	bNodeLink *link, *newlink, *lastlink;
	int keep_inputs = RNA_boolean_get(op->ptr, "keep_inputs");
	
	ED_preview_kill_jobs(C);
	
	lastnode = ntree->nodes.last;
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			newnode = nodeCopyNode(ntree, node);
			
			if (newnode->id) {
				/* simple id user adjustment, node internal functions don't touch this
				 * but operators and readfile.c do. */
				id_us_plus(newnode->id);
				/* to ensure redraws or rerenders happen */
				ED_node_tag_update_id(snode->id);
			}
		}
		
		/* make sure we don't copy new nodes again! */
		if (node == lastnode)
			break;
	}
	
	/* copy links between selected nodes
	 * NB: this depends on correct node->new_node and sock->new_sock pointers from above copy!
	 */
	lastlink = ntree->links.last;
	for (link = ntree->links.first; link; link = link->next) {
		/* This creates new links between copied nodes.
		 * If keep_inputs is set, also copies input links from unselected (when fromnode==NULL)!
		 */
		if (link->tonode && (link->tonode->flag & NODE_SELECT) &&
		    (keep_inputs || (link->fromnode && (link->fromnode->flag & NODE_SELECT))))
		{
			newlink = MEM_callocN(sizeof(bNodeLink), "bNodeLink");
			newlink->flag = link->flag;
			newlink->tonode = link->tonode->new_node;
			newlink->tosock = link->tosock->new_sock;
			if (link->fromnode && (link->fromnode->flag & NODE_SELECT)) {
				newlink->fromnode = link->fromnode->new_node;
				newlink->fromsock = link->fromsock->new_sock;
			}
			else {
				/* input node not copied, this keeps the original input linked */
				newlink->fromnode = link->fromnode;
				newlink->fromsock = link->fromsock;
			}
			
			BLI_addtail(&ntree->links, newlink);
		}
		
		/* make sure we don't copy new links again! */
		if (link == lastlink)
			break;
	}
	
	/* clear flags for recursive depth-first iteration */
	for (node = ntree->nodes.first; node; node = node->next)
		node->flag &= ~NODE_TEST;
	/* reparent copied nodes */
	for (node = ntree->nodes.first; node; node = node->next) {
		if ((node->flag & SELECT) && !(node->flag & NODE_TEST))
			node_duplicate_reparent_recursive(node);
		
		/* only has to check old nodes */
		if (node == lastnode)
			break;
	}
	
	/* deselect old nodes, select the copies instead */
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			/* has been set during copy above */
			newnode = node->new_node;
			
			nodeSetSelected(node, FALSE);
			node->flag &= ~NODE_ACTIVE;
			nodeSetSelected(newnode, TRUE);
		}
		
		/* make sure we don't copy new nodes again! */
		if (node == lastnode)
			break;
	}
	
	ntreeUpdateTree(snode->edittree);
	
	snode_notify(C, snode);
	snode_dag_update(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_duplicate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Duplicate Nodes";
	ot->description = "Duplicate selected nodes";
	ot->idname = "NODE_OT_duplicate";
	
	/* api callbacks */
	ot->exec = node_duplicate_exec;
	ot->poll = ED_operator_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_boolean(ot->srna, "keep_inputs", 0, "Keep Inputs", "Keep the input links to duplicated nodes");
}

int ED_node_select_check(ListBase *lb)


{
	bNode *node;

	for (node = lb->first; node; node = node->next) {
		if (node->flag & NODE_SELECT) {
			return TRUE;
		}
	}

	return FALSE;
}

/* ******************************** */
// XXX some code needing updating to operators...


/* goes over all scenes, reads render layers */
static int node_read_renderlayers_exec(bContext *C, wmOperator *UNUSED(op))
{
	Main *bmain = CTX_data_main(C);
	SpaceNode *snode = CTX_wm_space_node(C);
	Scene *curscene = CTX_data_scene(C), *scene;
	bNode *node;

	ED_preview_kill_jobs(C);

	/* first tag scenes unread */
	for (scene = bmain->scene.first; scene; scene = scene->id.next)
		scene->id.flag |= LIB_DOIT;

	for (node = snode->edittree->nodes.first; node; node = node->next) {
		if (node->type == CMP_NODE_R_LAYERS) {
			ID *id = node->id;
			if (id->flag & LIB_DOIT) {
				RE_ReadRenderResult(curscene, (Scene *)id);
				ntreeCompositTagRender((Scene *)id);
				id->flag &= ~LIB_DOIT;
			}
		}
	}
	
	snode_notify(C, snode);
	snode_dag_update(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_read_renderlayers(wmOperatorType *ot)
{
	
	ot->name = "Read Render Layers";
	ot->idname = "NODE_OT_read_renderlayers";
	ot->description = "Read all render layers of all used scenes";
	
	ot->exec = node_read_renderlayers_exec;
	
	ot->poll = composite_node_active;
	
	/* flags */
	ot->flag = 0;
}

static int node_read_fullsamplelayers_exec(bContext *C, wmOperator *UNUSED(op))
{
	Main *bmain = CTX_data_main(C);
	SpaceNode *snode = CTX_wm_space_node(C);
	Scene *curscene = CTX_data_scene(C);
	Render *re = RE_NewRender(curscene->id.name);

	WM_cursor_wait(1);
	RE_MergeFullSample(re, bmain, curscene, snode->nodetree);
	WM_cursor_wait(0);

	/* note we are careful to send the right notifier, as otherwise the
	 * compositor would reexecute and overwrite the full sample result */
	WM_event_add_notifier(C, NC_SCENE | ND_COMPO_RESULT, NULL);

	return OPERATOR_FINISHED;
}


void NODE_OT_read_fullsamplelayers(wmOperatorType *ot)
{
	
	ot->name = "Read Full Sample Layers";
	ot->idname = "NODE_OT_read_fullsamplelayers";
	ot->description = "Read all render layers of current scene, in full sample";
	
	ot->exec = node_read_fullsamplelayers_exec;
	
	ot->poll = composite_node_active;
	
	/* flags */
	ot->flag = 0;
}

int node_render_changed_exec(bContext *C, wmOperator *UNUSED(op))
{
	Scene *sce = CTX_data_scene(C);
	bNode *node;
	
	for (node = sce->nodetree->nodes.first; node; node = node->next) {
		if (node->id == (ID *)sce && node->need_exec) {
			break;
		}
	}
	if (node) {
		SceneRenderLayer *srl = BLI_findlink(&sce->r.layers, node->custom1);
		
		if (srl) {
			PointerRNA op_ptr;
			
			WM_operator_properties_create(&op_ptr, "RENDER_OT_render");
			RNA_string_set(&op_ptr, "layer", srl->name);
			RNA_string_set(&op_ptr, "scene", sce->id.name + 2);
			
			/* to keep keypositions */
			sce->r.scemode |= R_NO_FRAME_UPDATE;
			
			WM_operator_name_call(C, "RENDER_OT_render", WM_OP_INVOKE_DEFAULT, &op_ptr);

			WM_operator_properties_free(&op_ptr);
			
			return OPERATOR_FINISHED;
		}
		   
	}
	return OPERATOR_CANCELLED;
}

void NODE_OT_render_changed(wmOperatorType *ot)
{
	ot->name = "Render Changed Layer";
	ot->idname = "NODE_OT_render_changed";
	ot->description = "Render current scene, when input node's layer has been changed";
	
	ot->exec = node_render_changed_exec;
	
	ot->poll = composite_node_active;
	
	/* flags */
	ot->flag = 0;
}


/* ****************** Hide operator *********************** */

static void node_flag_toggle_exec(SpaceNode *snode, int toggle_flag)
{
	bNode *node;
	int tot_eq = 0, tot_neq = 0;

	/* Toggles the flag on all selected nodes.
	 * If the flag is set on all nodes it is unset.
	 * If the flag is not set on all nodes, it is set.
	 */
	for (node = snode->edittree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			
			if (toggle_flag == NODE_PREVIEW && (node->typeinfo->flag & NODE_PREVIEW) == 0)
				continue;
			if (toggle_flag == NODE_OPTIONS && (node->typeinfo->flag & NODE_OPTIONS) == 0)
				continue;
			
			if (node->flag & toggle_flag)
				tot_eq++;
			else
				tot_neq++;
		}
	}
	for (node = snode->edittree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			
			if (toggle_flag == NODE_PREVIEW && (node->typeinfo->flag & NODE_PREVIEW) == 0)
				continue;
			if (toggle_flag == NODE_OPTIONS && (node->typeinfo->flag & NODE_OPTIONS) == 0)
				continue;
			
			if ((tot_eq && tot_neq) || tot_eq == 0)
				node->flag |= toggle_flag;
			else
				node->flag &= ~toggle_flag;
		}
	}
}

static int node_hide_toggle_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	
	/* sanity checking (poll callback checks this already) */
	if ((snode == NULL) || (snode->edittree == NULL))
		return OPERATOR_CANCELLED;
	
	node_flag_toggle_exec(snode, NODE_HIDDEN);

	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_hide_toggle(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Hide";
	ot->description = "Toggle hiding of selected nodes";
	ot->idname = "NODE_OT_hide_toggle";
	
	/* callbacks */
	ot->exec = node_hide_toggle_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int node_preview_toggle_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);

	/* sanity checking (poll callback checks this already) */
	if ((snode == NULL) || (snode->edittree == NULL))
		return OPERATOR_CANCELLED;

	ED_preview_kill_jobs(C);

	node_flag_toggle_exec(snode, NODE_PREVIEW);

	snode_notify(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_preview_toggle(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Toggle Node Preview";
	ot->description = "Toggle preview display for selected nodes";
	ot->idname = "NODE_OT_preview_toggle";

	/* callbacks */
	ot->exec = node_preview_toggle_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int node_options_toggle_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);

	/* sanity checking (poll callback checks this already) */
	if ((snode == NULL) || (snode->edittree == NULL))
		return OPERATOR_CANCELLED;

	node_flag_toggle_exec(snode, NODE_OPTIONS);

	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_options_toggle(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Toggle Node Options";
	ot->description = "Toggle option buttons display for selected nodes";
	ot->idname = "NODE_OT_options_toggle";

	/* callbacks */
	ot->exec = node_options_toggle_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int node_socket_toggle_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNode *node;
	int hidden;

	/* sanity checking (poll callback checks this already) */
	if ((snode == NULL) || (snode->edittree == NULL))
		return OPERATOR_CANCELLED;

	ED_preview_kill_jobs(C);

	/* Toggle for all selected nodes */
	hidden = 0;
	for (node = snode->edittree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			if (node_has_hidden_sockets(node)) {
				hidden = 1;
				break;
			}
		}
	}
	
	for (node = snode->edittree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			node_set_hidden_sockets(snode, node, !hidden);
		}
	}

	ntreeUpdateTree(snode->edittree);

	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_hide_socket_toggle(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Toggle Hidden Node Sockets";
	ot->description = "Toggle unused node socket display";
	ot->idname = "NODE_OT_hide_socket_toggle";

	/* callbacks */
	ot->exec = node_socket_toggle_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Mute operator *********************** */

static int node_mute_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNode *node;

	ED_preview_kill_jobs(C);

	for (node = snode->edittree->nodes.first; node; node = node->next) {
		/* Only allow muting of nodes having a mute func! */
		if ((node->flag & SELECT) && node->typeinfo->update_internal_links) {
			node->flag ^= NODE_MUTED;
			snode_update(snode, node);
		}
	}
	
	snode_notify(C, snode);
	snode_dag_update(C, snode);
	
	return OPERATOR_FINISHED;
}

void NODE_OT_mute_toggle(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Toggle Node Mute";
	ot->description = "Toggle muting of the nodes";
	ot->idname = "NODE_OT_mute_toggle";
	
	/* callbacks */
	ot->exec = node_mute_exec;
	ot->poll = ED_operator_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Delete operator ******************* */

static int node_delete_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNode *node, *next;
	
	ED_preview_kill_jobs(C);

	for (node = snode->edittree->nodes.first; node; node = next) {
		next = node->next;
		if (node->flag & SELECT) {
			/* check id user here, nodeFreeNode is called for free dbase too */
			if (node->id)
				node->id->us--;
			nodeFreeNode(snode->edittree, node);
		}
	}
	
	ntreeUpdateTree(snode->edittree);

	snode_notify(C, snode);
	snode_dag_update(C, snode);
	
	return OPERATOR_FINISHED;
}

void NODE_OT_delete(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Delete";
	ot->description = "Delete selected nodes";
	ot->idname = "NODE_OT_delete";
	
	/* api callbacks */
	ot->exec = node_delete_exec;
	ot->poll = ED_operator_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Delete with reconnect ******************* */
static int node_delete_reconnect_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNode *node, *next;

	ED_preview_kill_jobs(C);

	for (node = snode->edittree->nodes.first; node; node = next) {
		next = node->next;
		if (node->flag & SELECT) {
			nodeInternalRelink(snode->edittree, node);
			
			/* check id user here, nodeFreeNode is called for free dbase too */
			if (node->id)
				node->id->us--;
			nodeFreeNode(snode->edittree, node);
		}
	}

	ntreeUpdateTree(snode->edittree);

	snode_notify(C, snode);
	snode_dag_update(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_delete_reconnect(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Delete with Reconnect";
	ot->description = "Delete nodes; will reconnect nodes as if deletion was muted";
	ot->idname = "NODE_OT_delete_reconnect";

	/* api callbacks */
	ot->exec = node_delete_reconnect_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}


/* ****************** File Output Add Socket  ******************* */

static int node_output_file_add_socket_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	SpaceNode *snode = CTX_wm_space_node(C);
	PointerRNA ptr;
	bNodeTree *ntree;
	bNode *node;
	char file_path[MAX_NAME];

	ptr = CTX_data_pointer_get(C, "node");
	if (!ptr.data)
		return OPERATOR_CANCELLED;
	node = ptr.data;
	ntree = ptr.id.data;

	RNA_string_get(op->ptr, "file_path", file_path);
	ntreeCompositOutputFileAddSocket(ntree, node, file_path, &scene->r.im_format);

	snode_notify(C, snode);

	return OPERATOR_FINISHED;
}

void NODE_OT_output_file_add_socket(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Add File Node Socket";
	ot->description = "Add a new input to a file output node";
	ot->idname = "NODE_OT_output_file_add_socket";

	/* callbacks */
	ot->exec = node_output_file_add_socket_exec;
	ot->poll = composite_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	RNA_def_string(ot->srna, "file_path", "Image", MAX_NAME, "File Path", "Sub-path of the output file");
}

/* ****************** Multi File Output Remove Socket  ******************* */

static int node_output_file_remove_active_socket_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	PointerRNA ptr = CTX_data_pointer_get(C, "node");
	bNodeTree *ntree;
	bNode *node;
	
	if (!ptr.data)
		return OPERATOR_CANCELLED;
	node = ptr.data;
	ntree = ptr.id.data;
	
	if (!ntreeCompositOutputFileRemoveActiveSocket(ntree, node))
		return OPERATOR_CANCELLED;
	
	snode_notify(C, snode);
	
	return OPERATOR_FINISHED;
}

void NODE_OT_output_file_remove_active_socket(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Remove File Node Socket";
	ot->description = "Remove active input from a file output node";
	ot->idname = "NODE_OT_output_file_remove_active_socket";
	
	/* callbacks */
	ot->exec = node_output_file_remove_active_socket_exec;
	ot->poll = composite_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Multi File Output Move Socket  ******************* */

static int node_output_file_move_active_socket_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	PointerRNA ptr = CTX_data_pointer_get(C, "node");
	bNode *node;
	NodeImageMultiFile *nimf;
	bNodeSocket *sock;
	int direction;
	
	if (!ptr.data)
		return OPERATOR_CANCELLED;
	node = ptr.data;
	nimf = node->storage;
	
	sock = BLI_findlink(&node->inputs, nimf->active_input);
	if (!sock)
		return OPERATOR_CANCELLED;
	
	direction = RNA_enum_get(op->ptr, "direction");
	
	if (direction == 1) {
		bNodeSocket *before = sock->prev;
		if (!before)
			return OPERATOR_CANCELLED;
		BLI_remlink(&node->inputs, sock);
		BLI_insertlinkbefore(&node->inputs, before, sock);
		nimf->active_input--;
	}
	else {
		bNodeSocket *after = sock->next;
		if (!after)
			return OPERATOR_CANCELLED;
		BLI_remlink(&node->inputs, sock);
		BLI_insertlinkafter(&node->inputs, after, sock);
		nimf->active_input++;
	}
	
	snode_notify(C, snode);
	
	return OPERATOR_FINISHED;
}

void NODE_OT_output_file_move_active_socket(wmOperatorType *ot)
{
	static EnumPropertyItem direction_items[] = {
		{1, "UP", 0, "Up", ""},
		{2, "DOWN", 0, "Down", ""},
		{ 0, NULL, 0, NULL, NULL }
	};
	
	/* identifiers */
	ot->name = "Move File Node Socket";
	ot->description = "Move the active input of a file output node up or down the list";
	ot->idname = "NODE_OT_output_file_move_active_socket";
	
	/* callbacks */
	ot->exec = node_output_file_move_active_socket_exec;
	ot->poll = composite_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "direction", direction_items, 2, "Direction", "");
}

/* ****************** Copy Node Color ******************* */

static int node_copy_color_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *node, *tnode;
	
	if (!ntree)
		return OPERATOR_CANCELLED;
	node = nodeGetActive(ntree);
	if (!node)
		return OPERATOR_CANCELLED;
	
	for (tnode = ntree->nodes.first; tnode; tnode = tnode->next) {
		if (tnode->flag & NODE_SELECT && tnode != node) {
			if (node->flag & NODE_CUSTOM_COLOR) {
				tnode->flag |= NODE_CUSTOM_COLOR;
				copy_v3_v3(tnode->color, node->color);
			}
			else
				tnode->flag &= ~NODE_CUSTOM_COLOR;
		}
	}

	ED_node_sort(ntree);
	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);

	return OPERATOR_FINISHED;
}

void NODE_OT_node_copy_color(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Copy Color";
	ot->description = "Copy color to all selected nodes";
	ot->idname = "NODE_OT_node_copy_color";

	/* api callbacks */
	ot->exec = node_copy_color_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Copy to clipboard ******************* */

static int node_clipboard_copy_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNode *node;
	bNodeLink *link, *newlink;

	ED_preview_kill_jobs(C);

	/* clear current clipboard */
	BKE_node_clipboard_clear();
	BKE_node_clipboard_init(ntree);

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			bNode *new_node;
			new_node = nodeCopyNode(NULL, node);
			BKE_node_clipboard_add_node(new_node);
		}
	}

	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->flag & SELECT) {
			bNode *new_node = node->new_node;
			
			/* ensure valid pointers */
			if (new_node->parent) {
				/* parent pointer must be redirected to new node or detached if parent is not copied */
				if (new_node->parent->flag & NODE_SELECT) {
					new_node->parent = new_node->parent->new_node;
				}
				else {
					nodeDetachNode(new_node);
				}
			}
		}
	}

	/* copy links between selected nodes
	 * NB: this depends on correct node->new_node and sock->new_sock pointers from above copy!
	 */
	for (link = ntree->links.first; link; link = link->next) {
		/* This creates new links between copied nodes. */
		if (link->tonode && (link->tonode->flag & NODE_SELECT) &&
		    link->fromnode && (link->fromnode->flag & NODE_SELECT))
		{
			newlink = MEM_callocN(sizeof(bNodeLink), "bNodeLink");
			newlink->flag = link->flag;
			newlink->tonode = link->tonode->new_node;
			newlink->tosock = link->tosock->new_sock;
			newlink->fromnode = link->fromnode->new_node;
			newlink->fromsock = link->fromsock->new_sock;

			BKE_node_clipboard_add_link(newlink);
		}
	}

	return OPERATOR_FINISHED;
}

void NODE_OT_clipboard_copy(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Copy to Clipboard";
	ot->description = "Copies selected nodes to the clipboard";
	ot->idname = "NODE_OT_clipboard_copy";

	/* api callbacks */
	ot->exec = node_clipboard_copy_exec;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ****************** Paste from clipboard ******************* */

static int node_clipboard_paste_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	const ListBase *clipboard_nodes_lb;
	const ListBase *clipboard_links_lb;
	bNode *node;
	bNodeLink *link;
	int num_nodes;
	float center[2];
	int is_clipboard_valid;

	/* validate pointers in the clipboard */
	is_clipboard_valid = BKE_node_clipboard_validate();
	clipboard_nodes_lb = BKE_node_clipboard_get_nodes();
	clipboard_links_lb = BKE_node_clipboard_get_links();

	if (clipboard_nodes_lb->first == NULL) {
		BKE_report(op->reports, RPT_ERROR, "Clipboard is empty");
		return OPERATOR_CANCELLED;
	}

	if (BKE_node_clipboard_get_type() != ntree->type) {
		BKE_report(op->reports, RPT_ERROR, "Clipboard nodes are an incompatible type");
		return OPERATOR_CANCELLED;
	}

	/* only warn */
	if (is_clipboard_valid == FALSE) {
		BKE_report(op->reports, RPT_WARNING, "Some nodes references could not be restored, will be left empty");
	}

	ED_preview_kill_jobs(C);

	/* deselect old nodes */
	node_deselect_all(snode);

	/* calculate "barycenter" for placing on mouse cursor */
	zero_v2(center);
	for (node = clipboard_nodes_lb->first, num_nodes = 0; node; node = node->next, num_nodes++) {
		center[0] += BLI_rctf_cent_x(&node->totr);
		center[1] += BLI_rctf_cent_y(&node->totr);
	}
	mul_v2_fl(center, 1.0 / num_nodes);

	/* copy nodes from clipboard */
	for (node = clipboard_nodes_lb->first; node; node = node->next) {
		bNode *new_node = nodeCopyNode(ntree, node);

		/* needed since nodeCopyNode() doesn't increase ID's */
		id_us_plus(node->id);

		/* pasted nodes are selected */
		nodeSetSelected(new_node, TRUE);
	}
	
	/* reparent copied nodes */
	for (node = clipboard_nodes_lb->first; node; node = node->next) {
		bNode *new_node = node->new_node;
		if (new_node->parent)
			new_node->parent = new_node->parent->new_node;
	}

	for (link = clipboard_links_lb->first; link; link = link->next) {
		nodeAddLink(ntree, link->fromnode->new_node, link->fromsock->new_sock,
		            link->tonode->new_node, link->tosock->new_sock);
	}

	ntreeUpdateTree(snode->edittree);

	snode_notify(C, snode);
	snode_dag_update(C, snode);

	return OPERATOR_FINISHED;
}

static int node_clipboard_paste_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
	ARegion *ar = CTX_wm_region(C);
	SpaceNode *snode = CTX_wm_space_node(C);

	/* convert mouse coordinates to v2d space */
	UI_view2d_region_to_view(&ar->v2d, event->mval[0], event->mval[1], &snode->cursor[0], &snode->cursor[1]);

	return node_clipboard_paste_exec(C, op);
}

void NODE_OT_clipboard_paste(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Paste from Clipboard";
	ot->description = "Pastes nodes from the clipboard to the active node tree";
	ot->idname = "NODE_OT_clipboard_paste";

	/* api callbacks */
	ot->exec = node_clipboard_paste_exec;
	ot->invoke = node_clipboard_paste_invoke;
	ot->poll = ED_operator_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/********************** Add interface socket operator *********************/

static bNodeSocket *ntree_get_active_interface_socket(ListBase *lb)
{
	bNodeSocket *sock;
	for (sock = lb->first; sock; sock = sock->next)
		if (sock->flag & SELECT)
			return sock;
	return NULL;
}

static int ntree_socket_add_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	int in_out = RNA_enum_get(op->ptr, "in_out");
	PointerRNA ntree_ptr;
	bNodeSocket *sock, *tsock, *active_sock;
	const char *default_name;
	
	RNA_id_pointer_create((ID *)ntree, &ntree_ptr);
	
	if (in_out == SOCK_IN) {
		active_sock = ntree_get_active_interface_socket(&ntree->inputs);
		default_name = "Input";
	}
	else {
		active_sock = ntree_get_active_interface_socket(&ntree->outputs);
		default_name = "Output";
	}
	
	if (active_sock) {
		/* insert a copy of the active socket right after it */
		sock = ntreeInsertSocketInterface(ntree, in_out, active_sock->idname, active_sock->next, active_sock->name);
		/* XXX this only works for actual sockets, not interface templates! */
		/*nodeSocketCopyValue(sock, &ntree_ptr, active_sock, &ntree_ptr);*/
	}
	else {
		/* XXX TODO define default socket type for a tree! */
		sock = ntreeAddSocketInterface(ntree, in_out, "NodeSocketFloat", default_name);
	}
	
	/* deactivate sockets (has to check both lists) */
	for (tsock = ntree->inputs.first; tsock; tsock = tsock->next)
		tsock->flag &= ~SELECT;
	for (tsock = ntree->outputs.first; tsock; tsock = tsock->next)
		tsock->flag &= ~SELECT;
	/* make the new socket active */
	sock->flag |= SELECT;
	
	ntreeUpdateTree(ntree);

	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);
	
	return OPERATOR_FINISHED;
}

void NODE_OT_tree_socket_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Add Node Tree Interface Socket";
	ot->description = "Add an input or output socket to the current node tree";
	ot->idname = "NODE_OT_tree_socket_add";
	
	/* api callbacks */
	ot->exec = ntree_socket_add_exec;
	ot->poll = ED_operator_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "in_out", node_socket_in_out_items, SOCK_IN, "Socket Type", "");
}

/********************** Remove interface socket operator *********************/

static int ntree_socket_remove_exec(bContext *C, wmOperator *UNUSED(op))
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	bNodeSocket *iosock, *active_sock;
	
	iosock = ntree_get_active_interface_socket(&ntree->inputs);
	if (!iosock)
		iosock = ntree_get_active_interface_socket(&ntree->outputs);
	if (!iosock)
		return OPERATOR_CANCELLED;
	
	/* preferably next socket becomes active, otherwise try previous socket */
	active_sock = (iosock->next ? iosock->next : iosock->prev);
	ntreeRemoveSocketInterface(ntree, iosock);
	
	/* set active socket */
	if (active_sock)
		active_sock->flag |= SELECT;
	
	ntreeUpdateTree(ntree);

	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);
	
	return OPERATOR_FINISHED;
}

void NODE_OT_tree_socket_remove(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Remove Node Tree Interface Socket";
	ot->description = "Remove an input or output socket to the current node tree";
	ot->idname = "NODE_OT_tree_socket_remove";
	
	/* api callbacks */
	ot->exec = ntree_socket_remove_exec;
	ot->poll = ED_operator_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/********************** Move interface socket operator *********************/

static EnumPropertyItem move_direction_items[] = {
	{ 1, "UP", 0, "Up", "" },
	{ 2, "DOWN", 0, "Down", "" },
	{ 0, NULL, 0, NULL, NULL },
};

static int ntree_socket_move_exec(bContext *C, wmOperator *op)
{
	SpaceNode *snode = CTX_wm_space_node(C);
	bNodeTree *ntree = snode->edittree;
	int direction = RNA_enum_get(op->ptr, "direction");
	bNodeSocket *iosock;
	ListBase *lb;
	
	lb = &ntree->inputs;
	iosock = ntree_get_active_interface_socket(lb);
	if (!iosock) {
		lb = &ntree->outputs;
		iosock = ntree_get_active_interface_socket(lb);
	}
	if (!iosock)
		return OPERATOR_CANCELLED;
	
	switch (direction) {
	case 1: {	/* up */
		bNodeSocket *before = iosock->prev;
		BLI_remlink(lb, iosock);
		if (before)
			BLI_insertlinkbefore(lb, before, iosock);
		else
			BLI_addhead(lb, iosock);
		break;
	}
	case 2: {	/* down */
		bNodeSocket *after = iosock->next;
		BLI_remlink(lb, iosock);
		if (after)
			BLI_insertlinkafter(lb, after, iosock);
		else
			BLI_addtail(lb, iosock);
		break;
	}
	}
	
	ntreeUpdateTree(ntree);

	WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);
	
	return OPERATOR_FINISHED;
}

void NODE_OT_tree_socket_move(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Move Node Tree Socket";
	ot->description = "Move a socket up or down in the current node tree's sockets stack";
	ot->idname = "NODE_OT_tree_socket_move";
	
	/* api callbacks */
	ot->exec = ntree_socket_move_exec;
	ot->poll = ED_operator_node_active;
	
	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
	
	RNA_def_enum(ot->srna, "direction", move_direction_items, 1, "Direction", "");
}

/* ********************** Shader Script Update ******************/

static int node_shader_script_update_poll(bContext *C)
{
	Scene *scene = CTX_data_scene(C);
	RenderEngineType *type = RE_engines_find(scene->r.engine);
	bNode *node;
	Text *text;

	/* test if we have a render engine that supports shaders scripts */
	if (!(type && type->update_script_node))
		return 0;

	/* see if we have a shader script node in context */
	node = CTX_data_pointer_get_type(C, "node", &RNA_ShaderNodeScript).data;
	if (node && node->type == SH_NODE_SCRIPT) {
		NodeShaderScript *nss = node->storage;

		if (node->id || nss->filepath[0]) {
			return 1;
		}
	}

	/* see if we have a text datablock in context */
	text = CTX_data_pointer_get_type(C, "edit_text", &RNA_Text).data;
	if (text)
		return 1;

	/* we don't check if text datablock is actually in use, too slow for poll */

	return 0;
}

/* recursively check for script nodes in groups using this text and update */
static int node_shader_script_update_text_recursive(RenderEngine *engine, RenderEngineType *type, bNodeTree *ntree, Text *text)
{
	int found = FALSE;
	bNode *node;
	
	ntree->done = TRUE;
	
	/* update each script that is using this text datablock */
	for (node = ntree->nodes.first; node; node = node->next) {
		if (node->type == NODE_GROUP) {
			bNodeTree *ngroup = (bNodeTree *)node->id;
			if (ngroup && !ngroup->done)
				found |= node_shader_script_update_text_recursive(engine, type, ngroup, text);
		}
		else if (node->type == SH_NODE_SCRIPT && node->id == &text->id) {
			type->update_script_node(engine, ntree, node);
			found = TRUE;
		}
	}
	
	return found;
}

static int node_shader_script_update_exec(bContext *C, wmOperator *op)
{
	Main *bmain = CTX_data_main(C);
	Scene *scene = CTX_data_scene(C);
	PointerRNA nodeptr = CTX_data_pointer_get_type(C, "node", &RNA_ShaderNodeScript);
	RenderEngine *engine;
	RenderEngineType *type;
	int found = FALSE;

	/* setup render engine */
	type = RE_engines_find(scene->r.engine);
	engine = RE_engine_create(type);
	engine->reports = op->reports;

	if (nodeptr.data) {
		/* update single node */
		bNodeTree *ntree = nodeptr.id.data;
		bNode *node = nodeptr.data;

		type->update_script_node(engine, ntree, node);

		found = TRUE;
	}
	else {
		/* update all nodes using text datablock */
		Text *text = CTX_data_pointer_get_type(C, "edit_text", &RNA_Text).data;

		if (text) {
			/* clear flags for recursion check */
			FOREACH_NODETREE(bmain, ntree, id) {
				if (ntree->type == NTREE_SHADER)
					ntree->done = FALSE;
			} FOREACH_NODETREE_END
			
			FOREACH_NODETREE(bmain, ntree, id) {
				if (ntree->type == NTREE_SHADER) {
					if (!ntree->done)
						found |= node_shader_script_update_text_recursive(engine, type, ntree, text);
				}
			} FOREACH_NODETREE_END

			if (!found)
				BKE_report(op->reports, RPT_INFO, "Text not used by any node, no update done");
		}
	}

	RE_engine_free(engine);

	return (found)? OPERATOR_FINISHED: OPERATOR_CANCELLED;
}

void NODE_OT_shader_script_update(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Script Node Update";
	ot->description = "Update shader script node with new sockets and options from the script";
	ot->idname = "NODE_OT_shader_script_update";

	/* api callbacks */
	ot->exec = node_shader_script_update_exec;
	ot->poll = node_shader_script_update_poll;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/* ********************** Viewer border ******************/

static void viewer_border_corner_to_backdrop(SpaceNode *snode, ARegion *ar, int x, int y,
                                             int backdrop_width, int backdrop_height,
                                             float *fx, float *fy)
{
	float bufx, bufy;

	bufx = backdrop_width * snode->zoom;
	bufy = backdrop_height * snode->zoom;

	*fx = (bufx > 0.0f ? ((float) x - 0.5f * ar->winx - snode->xof) / bufx + 0.5f : 0.0f);
	*fy = (bufy > 0.0f ? ((float) y - 0.5f * ar->winy - snode->yof) / bufy + 0.5f : 0.0f);
}

static int viewer_border_exec(bContext *C, wmOperator *op)
{
	Image *ima;
	void *lock;
	ImBuf *ibuf;

	ED_preview_kill_jobs(C);

	ima = BKE_image_verify_viewer(IMA_TYPE_COMPOSITE, "Viewer Node");
	ibuf = BKE_image_acquire_ibuf(ima, NULL, &lock);

	if (ibuf) {
		ARegion *ar = CTX_wm_region(C);
		SpaceNode *snode = CTX_wm_space_node(C);
		bNodeTree *btree = snode->edittree;
		rcti rect;
		rctf rectf;

		/* get border from operator */
		WM_operator_properties_border_to_rcti(op, &rect);

		/* convert border to unified space within backdrop image */
		viewer_border_corner_to_backdrop(snode, ar, rect.xmin, rect.ymin, ibuf->x, ibuf->y,
		                                 &rectf.xmin, &rectf.ymin);

		viewer_border_corner_to_backdrop(snode, ar, rect.xmax, rect.ymax, ibuf->x, ibuf->y,
		                                 &rectf.xmax, &rectf.ymax);

		/* clamp coordinates */
		rectf.xmin = max_ff(rectf.xmin, 0.0f);
		rectf.ymin = max_ff(rectf.ymin, 0.0f);
		rectf.xmax = min_ff(rectf.xmax, 1.0f);
		rectf.ymax = min_ff(rectf.ymax, 1.0f);

		if (rectf.xmin < rectf.xmax && rectf.ymin < rectf.ymax) {
			btree->viewer_border = rectf;

			if (rectf.xmin == 0.0f && rectf.ymin == 0.0f &&
			    rectf.xmax == 1.0f && rectf.ymax == 1.0f)
			{
				btree->flag &= ~NTREE_VIEWER_BORDER;
			}
			else {
				if (ibuf->rect)
					memset(ibuf->rect, 0, 4 * ibuf->x * ibuf->y);

				if (ibuf->rect_float)
					memset(ibuf->rect_float, 0, 4 * ibuf->x * ibuf->y * sizeof(float));

				ibuf->userflags |= IB_DISPLAY_BUFFER_INVALID;

				btree->flag |= NTREE_VIEWER_BORDER;
			}

			snode_notify(C, snode);
			WM_event_add_notifier(C, NC_NODE | ND_DISPLAY, NULL);
		}
		else {
			btree->flag &= ~NTREE_VIEWER_BORDER;
		}
	}

	BKE_image_release_ibuf(ima, ibuf, lock);

	return OPERATOR_FINISHED;
}

void NODE_OT_viewer_border(wmOperatorType *ot)
{
	/* identifiers */
	ot->name = "Viewer Border";
	ot->description = "Set the boundaries for viewer operations";
	ot->idname = "NODE_OT_viewer_border";

	/* api callbacks */
	ot->invoke = WM_border_select_invoke;
	ot->exec = viewer_border_exec;
	ot->modal = WM_border_select_modal;
	ot->cancel = WM_border_select_cancel;
	ot->poll = composite_node_active;

	/* flags */
	ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

	/* properties */
	WM_operator_properties_gesture_border(ot, TRUE);
}
