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
 * The Original Code is Copyright (C) 2013 Blender Foundation.
 * All rights reserved.
 *
 * Original Author: Joshua Leung
 * Contributor(s): None Yet
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/depsgraph/intern/depsgraph_tag.cc
 *  \ingroup depsgraph
 *
 * Core routines for how the Depsgraph works.
 */

#include <stdio.h>
#include <cstring>  /* required for memset */
#include <queue>

#include "BLI_utildefines.h"
#include "BLI_listbase.h"
#include "BLI_math_bits.h"
#include "BLI_task.h"

extern "C" {
#include "DNA_curve_types.h"
#include "DNA_key_types.h"
#include "DNA_lattice_types.h"
#include "DNA_mesh_types.h"
#include "DNA_object_types.h"
#include "DNA_particle_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_idcode.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_scene.h"
#include "BKE_workspace.h"

#define new new_
#include "BKE_screen.h"
#undef new
} /* extern "C" */

#include "DEG_depsgraph.h"

#include "intern/builder/deg_builder.h"
#include "intern/eval/deg_eval_flush.h"
#include "intern/nodes/deg_node.h"
#include "intern/nodes/deg_node_component.h"
#include "intern/nodes/deg_node_id.h"
#include "intern/nodes/deg_node_operation.h"

#include "intern/depsgraph_intern.h"
#include "util/deg_util_foreach.h"

/* *********************** */
/* Update Tagging/Flushing */

namespace DEG {

namespace {

void deg_graph_id_tag_update(Main *bmain, Depsgraph *graph, ID *id, int flag);

void depsgraph_geometry_tag_to_component(const ID *id,
                                         eDepsNode_Type *component_type)
{
	const ID_Type id_type = GS(id->name);
	switch (id_type) {
		case ID_OB:
		{
			const Object *object = (Object *)id;
			switch (object->type) {
				case OB_MESH:
				case OB_CURVE:
				case OB_SURF:
				case OB_FONT:
				case OB_LATTICE:
				case OB_MBALL:
					*component_type = DEG_NODE_TYPE_GEOMETRY;
					break;
				case OB_ARMATURE:
					*component_type = DEG_NODE_TYPE_EVAL_POSE;
					break;
					/* TODO(sergey): More cases here? */
			}
			break;
		}
		case ID_ME:
			*component_type = DEG_NODE_TYPE_GEOMETRY;
			break;
		case ID_PA:
			return;
		case ID_LP:
			*component_type = DEG_NODE_TYPE_PARAMETERS;
			break;
		default:
			break;
	}
}

void depsgraph_select_tag_to_component_opcode(
        const ID *id,
        eDepsNode_Type *component_type,
        eDepsOperation_Code *operation_code)
{
	const ID_Type id_type = GS(id->name);
	if (id_type == ID_SCE) {
		/* We need to flush base flags to all objects in a scene since we
		 * don't know which ones changed. However, we don't want to update
		 * the whole scene, so pick up some operation which will do as less
		 * as possible.
		 *
		 * TODO(sergey): We can introduce explicit exit operation which
		 * does nothing and which is only used to cascade flush down the
		 * road.
		 */
		*component_type = DEG_NODE_TYPE_LAYER_COLLECTIONS;
		*operation_code = DEG_OPCODE_VIEW_LAYER_DONE;
	}
	else if (id_type == ID_OB) {
		*component_type = DEG_NODE_TYPE_LAYER_COLLECTIONS;
		*operation_code = DEG_OPCODE_OBJECT_BASE_FLAGS;
	}
	else {
		*component_type = DEG_NODE_TYPE_BATCH_CACHE;
		*operation_code = DEG_OPCODE_GEOMETRY_SELECT_UPDATE;
	}
}

void depsgraph_base_flags_tag_to_component_opcode(
        const ID *id,
        eDepsNode_Type *component_type,
        eDepsOperation_Code *operation_code)
{
	const ID_Type id_type = GS(id->name);
	if (id_type == ID_SCE) {
		*component_type = DEG_NODE_TYPE_LAYER_COLLECTIONS;
		*operation_code = DEG_OPCODE_VIEW_LAYER_INIT;
	}
	else if (id_type == ID_OB) {
		*component_type = DEG_NODE_TYPE_LAYER_COLLECTIONS;
		*operation_code = DEG_OPCODE_OBJECT_BASE_FLAGS;
	}
}

void depsgraph_tag_to_component_opcode(const ID *id,
                                       eDepsgraph_Tag tag,
                                       eDepsNode_Type *component_type,
                                       eDepsOperation_Code *operation_code)
{
	const ID_Type id_type = GS(id->name);
	*component_type = DEG_NODE_TYPE_UNDEFINED;
	*operation_code = DEG_OPCODE_OPERATION;
	/* Special case for now, in the future we should get rid of this. */
	if (tag == 0) {
		*component_type = DEG_NODE_TYPE_ID_REF;
		*operation_code = DEG_OPCODE_OPERATION;
		return;
	}
	switch (tag) {
		case DEG_TAG_TRANSFORM:
			*component_type = DEG_NODE_TYPE_TRANSFORM;
			break;
		case DEG_TAG_GEOMETRY:
			depsgraph_geometry_tag_to_component(id, component_type);
			break;
		case DEG_TAG_TIME:
			*component_type = DEG_NODE_TYPE_ANIMATION;
			break;
		case DEG_TAG_PSYS_REDO:
		case DEG_TAG_PSYS_RESET:
		case DEG_TAG_PSYS_TYPE:
		case DEG_TAG_PSYS_CHILD:
		case DEG_TAG_PSYS_PHYS:
			if (id_type == ID_PA) {
				/* NOTES:
				 * - For particle settings node we need to use different
				 *   component. Will be nice to get this unified with object,
				 *   but we can survive for now with single exception here.
				 *   Particles needs reconsideration anyway,
				 * - We do direct injection of particle settings recalc flag
				 *   here. This is what we need to do for until particles
				 *   are switched away from own recalc flag and are using
				 *   ID->recalc flags instead.
				 */
				ParticleSettings *particle_settings = (ParticleSettings *)id;
				particle_settings->recalc |= (tag & DEG_TAG_PSYS_ALL);
				*component_type = DEG_NODE_TYPE_PARAMETERS;
			}
			else {
				*component_type = DEG_NODE_TYPE_EVAL_PARTICLES;
			}
			break;
		case DEG_TAG_COPY_ON_WRITE:
			*component_type = DEG_NODE_TYPE_COPY_ON_WRITE;
			break;
		case DEG_TAG_SHADING_UPDATE:
			if (id_type == ID_NT) {
				*component_type = DEG_NODE_TYPE_SHADING_PARAMETERS;
			}
			else {
				*component_type = DEG_NODE_TYPE_SHADING;
			}
			break;
		case DEG_TAG_SELECT_UPDATE:
			depsgraph_select_tag_to_component_opcode(id,
			                                         component_type,
			                                         operation_code);
			break;
		case DEG_TAG_BASE_FLAGS_UPDATE:
			depsgraph_base_flags_tag_to_component_opcode(id,
			                                             component_type,
			                                             operation_code);
		case DEG_TAG_EDITORS_UPDATE:
			/* There is no such node in depsgraph, this tag is to be handled
			 * separately.
			 */
			break;
		case DEG_TAG_PSYS_ALL:
			BLI_assert(!"Should not happen");
			break;
	}
}

void id_tag_update_ntree_special(Main *bmain, Depsgraph *graph, ID *id, int flag)
{
	bNodeTree *ntree = ntreeFromID(id);
	if (ntree == NULL) {
		return;
	}
	deg_graph_id_tag_update(bmain, graph, &ntree->id, flag);
}

void depsgraph_update_editors_tag(Main *bmain, Depsgraph *graph, ID *id)
{
	/* NOTE: We handle this immediately, without delaying anything, to be
	 * sure we don't cause threading issues with OpenGL.
	 */
	/* TODO(sergey): Make sure this works for CoW-ed datablocks as well. */
	DEGEditorUpdateContext update_ctx = {NULL};
	update_ctx.bmain = bmain;
	update_ctx.depsgraph = (::Depsgraph *)graph;
	update_ctx.scene = graph->scene;
	update_ctx.view_layer = graph->view_layer;
	deg_editors_id_update(&update_ctx, id);
}

void depsgraph_tag_component(Depsgraph *graph,
                             IDDepsNode *id_node,
                             eDepsNode_Type component_type,
                             eDepsOperation_Code operation_code)
{
	ComponentDepsNode *component_node =
	        id_node->find_component(component_type);
	if (component_node == NULL) {
		return;
	}
	if (operation_code == DEG_OPCODE_OPERATION) {
		component_node->tag_update(graph);
	}
	else {
		OperationDepsNode *operation_node =
		        component_node->find_operation(operation_code);
		if (operation_node != NULL) {
			operation_node->tag_update(graph);
		}
	}
}

/* This is a tag compatibility with legacy code.
 *
 * Mainly, old code was tagging object with OB_RECALC_DATA tag to inform
 * that object's data datablock changed. Now API expects that ID is given
 * explicitly, but not all areas are aware of this yet.
 */
void deg_graph_id_tag_legacy_compat(Main *bmain,
                                    ID *id,
                                    eDepsgraph_Tag tag)
{
	if (tag == DEG_TAG_GEOMETRY || tag == 0) {
		switch (GS(id->name)) {
			case ID_OB:
			{
				Object *object = (Object *)id;
				ID *data_id = (ID *)object->data;
				if (data_id != NULL) {
					DEG_id_tag_update_ex(bmain, data_id, 0);
				}
				break;
			}
			/* TODO(sergey): Shape keys are annoying, maybe we should find a
			 * way to chain geometry evaluation to them, so we don't need extra
			 * tagging here.
			 */
			case ID_ME:
			{
				Mesh *mesh = (Mesh *)id;
				ID *key_id = &mesh->key->id;
				if (key_id != NULL) {
					DEG_id_tag_update_ex(bmain, key_id, 0);
				}
				break;
			}
			case ID_LT:
			{
				Lattice *lattice = (Lattice *)id;
				ID *key_id = &lattice->key->id;
				if (key_id != NULL) {
					DEG_id_tag_update_ex(bmain, key_id, 0);
				}
				break;
			}
			case ID_CU:
			{
				Curve *curve = (Curve *)id;
				ID *key_id = &curve->key->id;
				if (key_id != NULL) {
					DEG_id_tag_update_ex(bmain, key_id, 0);
				}
				break;
			}
			default:
				break;
		}
	}
}

void deg_graph_id_tag_update_single_flag(Main *bmain,
                                         Depsgraph *graph,
                                         ID *id,
                                         IDDepsNode *id_node,
                                         eDepsgraph_Tag tag)
{
	if (tag == DEG_TAG_EDITORS_UPDATE) {
		if (graph != NULL) {
			depsgraph_update_editors_tag(bmain, graph, id);
		}
		return;
	}
	/* Get description of what is to be tagged. */
	eDepsNode_Type component_type;
	eDepsOperation_Code operation_code;
	depsgraph_tag_to_component_opcode(id,
	                                  tag,
	                                  &component_type,
	                                  &operation_code);
	/* Check whether we've got something to tag. */
	if (component_type == DEG_NODE_TYPE_UNDEFINED) {
		/* Given ID does not support tag. */
		/* TODO(sergey): Shall we raise some panic here? */
		return;
	}
	/* Tag ID recalc flag. */
	DepsNodeFactory *factory = deg_type_get_factory(component_type);
	BLI_assert(factory != NULL);
	id->recalc |= factory->id_recalc_tag();
	/* Some sanity checks before moving forward. */
	if (id_node == NULL) {
		/* Happens when object is tagged for update and not yet in the
		 * dependency graph (but will be after relations update).
		 */
		return;
	}
	/* Tag corresponding dependency graph operation for update. */
	if (component_type == DEG_NODE_TYPE_ID_REF) {
		id_node->tag_update(graph);
	}
	else {
		depsgraph_tag_component(graph, id_node, component_type, operation_code);
	}
	/* TODO(sergey): Get rid of this once all areas are using proper data ID
	 * for tagging.
	 */
	deg_graph_id_tag_legacy_compat(bmain, id, tag);

}

void deg_graph_id_tag_update(Main *bmain, Depsgraph *graph, ID *id, int flag)
{
	IDDepsNode *id_node = (graph != NULL) ? graph->find_id_node(id)
	                                      : NULL;
	DEG_id_type_tag(bmain, GS(id->name));
	if (flag == 0) {
		/* TODO(sergey): Which recalc flags to set here? */
		id->recalc |= ID_RECALC_ALL;
		if (id_node != NULL) {
			id_node->tag_update(graph);
		}
		deg_graph_id_tag_legacy_compat(bmain, id, (eDepsgraph_Tag)0);
	}
	int current_flag = flag;
	while (current_flag != 0) {
		eDepsgraph_Tag tag =
		        (eDepsgraph_Tag)(1 << bitscan_forward_clear_i(&current_flag));
		deg_graph_id_tag_update_single_flag(bmain,
		                                    graph,
		                                    id,
		                                    id_node,
		                                    tag);
	}
	/* Special case for nested node tree datablocks. */
	id_tag_update_ntree_special(bmain, graph, id, flag);
}

/* TODO(sergey): Consider storing scene and view layer at depsgraph allocation
 * time.
 */
void deg_ensure_scene_view_layer(Depsgraph *graph,
                                 Scene *scene,
                                 ViewLayer *view_layer)
{
	if (!graph->need_update) {
		return;
	}
	graph->scene = scene;
	graph->view_layer = view_layer;
}

void deg_id_tag_update(Main *bmain, ID *id, int flag)
{
	deg_graph_id_tag_update(bmain, NULL, id, flag);
	LISTBASE_FOREACH (Scene *, scene, &bmain->scene) {
		LISTBASE_FOREACH (ViewLayer *, view_layer, &scene->view_layers) {
			Depsgraph *depsgraph =
			        (Depsgraph *)BKE_scene_get_depsgraph(scene,
			                                             view_layer,
			                                             false);
			if (depsgraph != NULL) {
				/* Make sure depsgraph is pointing to a correct scene and
				 * view layer. This is mainly required in cases when depsgraph
				 * was not built yet.
				 */
				deg_ensure_scene_view_layer(depsgraph, scene, view_layer);
				deg_graph_id_tag_update(bmain, depsgraph, id, flag);
			}
		}
	}
}

void deg_graph_on_visible_update(Main *bmain, Depsgraph *graph)
{
	/* Make sure objects are up to date. */
	foreach (DEG::IDDepsNode *id_node, graph->id_nodes) {
		const ID_Type id_type = GS(id_node->id_orig->name);
		int flag = 0;
		/* We only tag components which needs an update. Tagging everything is
		 * not a good idea because that might reset particles cache (or any
		 * other type of cache).
		 *
		 * TODO(sergey): Need to generalize this somehow.
		 */
		if (id_type == ID_OB) {
			flag |= OB_RECALC_OB | OB_RECALC_DATA | DEG_TAG_COPY_ON_WRITE;
		}
		deg_graph_id_tag_update(bmain, graph, id_node->id_orig, flag);
	}
	/* Make sure collection properties are up to date. */
	for (Scene *scene_iter = graph->scene;
	     scene_iter != NULL;
	     scene_iter = scene_iter->set)
	{
		IDDepsNode *scene_id_node = graph->find_id_node(&scene_iter->id);
		if (scene_id_node != NULL) {
			scene_id_node->tag_update(graph);
		}
		else {
			BLI_assert(graph->need_update);
		}
	}
}

}  /* namespace */

}  // namespace DEG

/* Data-Based Tagging  */

/* Tag given ID for an update in all the dependency graphs. */
void DEG_id_tag_update(ID *id, int flag)
{
	DEG_id_tag_update_ex(G.main, id, flag);
}

void DEG_id_tag_update_ex(Main *bmain, ID *id, int flag)
{
	if (id == NULL) {
		/* Ideally should not happen, but old depsgraph allowed this. */
		return;
	}
	if (G.debug & G_DEBUG_DEPSGRAPH_TAG) {
		printf("%s: id=%s flag=%d\n", __func__, id->name, flag);
	}
	DEG::deg_id_tag_update(bmain, id, flag);
}

void DEG_graph_id_tag_update(struct Main *bmain,
                             struct Depsgraph *depsgraph,
                             struct ID *id,
                             int flag)
{
	DEG::Depsgraph *graph = (DEG::Depsgraph *)depsgraph;
	DEG::deg_graph_id_tag_update(bmain, graph, id, flag);
}

/* Mark a particular datablock type as having changing. */
void DEG_id_type_tag(Main *bmain, short id_type)
{
	if (id_type == ID_NT) {
		/* Stupid workaround so parent datablocks of nested nodetree get looped
		 * over when we loop over tagged datablock types.
		 */
		DEG_id_type_tag(bmain, ID_MA);
		DEG_id_type_tag(bmain, ID_TE);
		DEG_id_type_tag(bmain, ID_LA);
		DEG_id_type_tag(bmain, ID_WO);
		DEG_id_type_tag(bmain, ID_SCE);
	}

	bmain->id_tag_update[BKE_idcode_to_index(id_type)] = 1;
}

void DEG_graph_flush_update(Main *bmain, Depsgraph *depsgraph)
{
	if (depsgraph == NULL) {
		return;
	}
	DEG::deg_graph_flush_updates(bmain, (DEG::Depsgraph *)depsgraph);
}

/* Update dependency graph when visible scenes/layers changes. */
void DEG_graph_on_visible_update(Main *bmain, Depsgraph *depsgraph)
{
	DEG::Depsgraph *graph = (DEG::Depsgraph *)depsgraph;
	DEG::deg_graph_on_visible_update(bmain, graph);
}

void DEG_on_visible_update(Main *bmain, const bool UNUSED(do_time))
{
	LISTBASE_FOREACH (Scene *, scene, &bmain->scene) {
		LISTBASE_FOREACH (ViewLayer *, view_layer, &scene->view_layers) {
			Depsgraph *depsgraph =
			        (Depsgraph *)BKE_scene_get_depsgraph(scene,
			                                             view_layer,
			                                             false);
			if (depsgraph != NULL) {
				DEG_graph_on_visible_update(bmain, depsgraph);
			}
		}
	}
}

/* Check if something was changed in the database and inform
 * editors about this.
 */
void DEG_ids_check_recalc(Main *bmain,
                          Depsgraph *depsgraph,
                          Scene *scene,
                          ViewLayer *view_layer,
                          bool time)
{
	ListBase *lbarray[MAX_LIBARRAY];
	int a;
	bool updated = false;

	/* Loop over all ID types. */
	a  = set_listbasepointers(bmain, lbarray);
	while (a--) {
		ListBase *lb = lbarray[a];
		ID *id = (ID *)lb->first;

		if (id && bmain->id_tag_update[BKE_idcode_to_index(GS(id->name))]) {
			updated = true;
			break;
		}
	}

	DEGEditorUpdateContext update_ctx = {NULL};
	update_ctx.bmain = bmain;
	update_ctx.depsgraph = depsgraph;
	update_ctx.scene = scene;
	update_ctx.view_layer = view_layer;
	DEG::deg_editors_scene_update(&update_ctx, (updated || time));
}

void DEG_ids_clear_recalc(Main *bmain)
{
	ListBase *lbarray[MAX_LIBARRAY];
	bNodeTree *ntree;
	int a;

	/* TODO(sergey): Re-implement POST_UPDATE_HANDLER_WORKAROUND using entry_tags
	 * and id_tags storage from the new dependency graph.
	 */

	/* Loop over all ID types. */
	a  = set_listbasepointers(bmain, lbarray);
	while (a--) {
		ListBase *lb = lbarray[a];
		ID *id = (ID *)lb->first;

		if (id && bmain->id_tag_update[BKE_idcode_to_index(GS(id->name))]) {
			for (; id; id = (ID *)id->next) {
				id->recalc &= ~ID_RECALC_ALL;

				/* Some ID's contain semi-datablock nodetree */
				ntree = ntreeFromID(id);
				if (ntree != NULL) {
					ntree->id.recalc &= ~ID_RECALC_ALL;
				}
			}
		}
	}

	memset(bmain->id_tag_update, 0, sizeof(bmain->id_tag_update));
}
