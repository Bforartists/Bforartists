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
#include "BLI_task.h"
#include "BLI_listbase.h"

extern "C" {
#include "DNA_object_types.h"
#include "DNA_particle_types.h"
#include "DNA_screen_types.h"
#include "DNA_windowmanager_types.h"


#include "BKE_idcode.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_node.h"
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
#include "intern/nodes/deg_node_operation.h"

#include "intern/depsgraph_intern.h"
#include "util/deg_util_foreach.h"

/* Define this in order to have more strict sanitization of what tagging flags
 * are used for ID databnlocks. Ideally, we would always want this, but there
 * are cases in generic modules (like IR remapping) where we don't want to spent
 * lots of time trying to guess which components are to be updated.
 */
// #define STRICT_COMPONENT_TAGGING

/* *********************** */
/* Update Tagging/Flushing */

namespace DEG {

/* Data-Based Tagging ------------------------------- */

void lib_id_recalc_tag(Main *bmain, ID *id)
{
	id->tag |= LIB_TAG_ID_RECALC;
	DEG_id_type_tag(bmain, GS(id->name));
}

void lib_id_recalc_data_tag(Main *bmain, ID *id)
{
	id->tag |= LIB_TAG_ID_RECALC_DATA;
	DEG_id_type_tag(bmain, GS(id->name));
}

namespace {

void lib_id_recalc_tag_flag(Main *bmain, ID *id, int flag)
{
	/* This bit of code ensures legacy object->recalc flags are still filled in
	 * the same way as it was expected with the old dependency graph.
	 *
	 * This is because some areas like motion paths and likely some other
	 * physics baking process are doing manual scene update on all the frames,
	 * trying to minimize number of updates.
	 *
	 * But this flag will also let us to re-construct entry nodes for update
	 * after relations update and after layer visibility changes.
	 */
	if (flag) {
		short id_type = GS(id->name);
		if (id_type == ID_OB) {
			Object *object = (Object *)id;
			object->recalc |= (flag & OB_RECALC_ALL);
		}
		if (flag & OB_RECALC_OB) {
			lib_id_recalc_tag(bmain, id);
		}
		if (flag & (OB_RECALC_DATA | PSYS_RECALC)) {
			lib_id_recalc_data_tag(bmain, id);
		}
	}
	else {
		lib_id_recalc_tag(bmain, id);
	}
}

/* Special tagging  */
void id_tag_update_special_zero_flag(Depsgraph *graph, IDDepsNode *id_node)
{
	/* NOTE: Full ID node update for now, need to minimize that i9n the future. */
	id_node->tag_update(graph);
}

/* Tag corresponding to OB_RECALC_OB. */
void id_tag_update_object_transform(Depsgraph *graph, IDDepsNode *id_node)
{
	ComponentDepsNode *transform_comp =
	        id_node->find_component(DEG_NODE_TYPE_TRANSFORM);
	if (transform_comp == NULL) {
#ifdef STRICT_COMPONENT_TAGGING
		DEG_ERROR_PRINTF("ERROR: Unable to find transform component for %s\n",
		                 id_node->id_orig->name);
		BLI_assert(!"This is not supposed to happen!");
#endif
		return;
	}
	transform_comp->tag_update(graph);
}

/* Tag corresponding to OB_RECALC_DATA. */
void id_tag_update_object_data(Depsgraph *graph, IDDepsNode *id_node)
{
	const short id_type = GS(id_node->id_orig->name);
	ComponentDepsNode *data_comp = NULL;
	switch (id_type) {
		case ID_OB:
		{
			const Object *object = (Object *)id_node->id_orig;
			switch (object->type) {
				case OB_MESH:
				case OB_CURVE:
				case OB_SURF:
				case OB_FONT:
				case OB_MBALL:
					data_comp = id_node->find_component(DEG_NODE_TYPE_GEOMETRY);
					break;
				case OB_ARMATURE:
					data_comp = id_node->find_component(DEG_NODE_TYPE_EVAL_POSE);
					break;
				/* TODO(sergey): More cases here? */
			}
			break;
		}
		case ID_ME:
			data_comp = id_node->find_component(DEG_NODE_TYPE_GEOMETRY);
			break;
		case ID_PA:
			return;
	}
	if (data_comp == NULL) {
#ifdef STRICT_COMPONENT_TAGGING
		DEG_ERROR_PRINTF("ERROR: Unable to find data component for %s\n",
		                 id_node->id_orig->name);
		BLI_assert(!"This is not supposed to happen!");
#endif
		return;
	}
	data_comp->tag_update(graph);
	/* Special legacy compatibility code, tag data ID for update when object
	 * is tagged for data update.
	 */
	if (id_type == ID_OB) {
		Object *object = (Object *)id_node->id_orig;
		ID *data_id = (ID *)object->data;
		if (data_id != NULL) {
			IDDepsNode *data_id_node = graph->find_id_node(data_id);
			// BLI_assert(data_id_node != NULL);
			/* TODO(sergey): Do we want more granular tags here? */
			/* TODO(sergey): Hrm, during some operations it's possible to have
			 * object node existing but not it's data. For example, when making
			 * objects local. This is valid situation, but how can we distinguish
			 * that from someone trying to do stupid things with dependency
			 * graph?
			 */
			if (data_id_node != NULL) {
				data_id_node->tag_update(graph);
			}
		}
	}
}

/* Tag corresponding to OB_RECALC_TIME. */
void id_tag_update_object_time(Depsgraph *graph, IDDepsNode *id_node)
{
	ComponentDepsNode *animation_comp =
	        id_node->find_component(DEG_NODE_TYPE_ANIMATION);
	if (animation_comp == NULL) {
		/* It's not necessarily we've got animation component in cases when
		 * we are tagging for time updates.
		 */
		return;
	}
	animation_comp->tag_update(graph);
	/* TODO(sergey): More components to tag here? */
}

void id_tag_update_particle(Depsgraph *graph, IDDepsNode *id_node, int tag)
{
	ComponentDepsNode *particle_comp =
	        id_node->find_component(DEG_NODE_TYPE_PARAMETERS);
	ParticleSettings *particle_settings = (ParticleSettings *)id_node->id_orig;
	particle_settings->recalc |= (tag & PSYS_RECALC);
	if (particle_comp == NULL) {
#ifdef STRICT_COMPONENT_TAGGING
		DEG_ERROR_PRINTF("ERROR: Unable to find particle component for %s\n",
		                 id_node->id_orig->name);
		BLI_assert(!"This is not supposed to happen!");
#endif
		return;
	}
	particle_comp->tag_update(graph);
}

void id_tag_update_shading(Depsgraph *graph, IDDepsNode *id_node)
{
	ComponentDepsNode *shading_comp =
	        id_node->find_component(DEG_NODE_TYPE_SHADING);
	if (shading_comp == NULL) {
#ifdef STRICT_COMPONENT_TAGGING
		DEG_ERROR_PRINTF("ERROR: Unable to find shading component for %s\n",
		                 id_node->id_orig->name);
		BLI_assert(!"This is not supposed to happen!");
#endif
		return;
	}
	shading_comp->tag_update(graph);
}

#ifdef WITH_COPY_ON_WRITE
/* Tag corresponding to DEG_TAG_COPY_ON_WRITE. */
void id_tag_update_copy_on_write(Depsgraph *graph, IDDepsNode *id_node)
{
	ComponentDepsNode *cow_comp =
	        id_node->find_component(DEG_NODE_TYPE_COPY_ON_WRITE);
	OperationDepsNode *cow_node = cow_comp->get_entry_operation();
	cow_node->tag_update(graph);
}
#endif

void deg_graph_id_tag_update(Main *bmain, Depsgraph *graph, ID *id, int flag)
{
	Depsgraph *deg_graph = reinterpret_cast<DEG::Depsgraph *>(graph);
	IDDepsNode *id_node = deg_graph->find_id_node(id);
	/* Make sure legacy flags are all nicely update. */
	lib_id_recalc_tag_flag(bmain, id, flag);
	if (id_node == NULL) {
		/* Shouldn't happen, but better be sure here. */
		return;
	}
	/* Tag components based on flags. */
	if (flag == 0) {
		id_tag_update_special_zero_flag(graph, id_node);
		return;
	}
	if (flag & OB_RECALC_OB) {
		id_tag_update_object_transform(graph, id_node);
	}
	if (flag & OB_RECALC_DATA) {
		id_tag_update_object_data(graph, id_node);
#ifdef WITH_COPY_ON_WRITE
		if (flag & DEG_TAG_COPY_ON_WRITE) {
			const short id_type = GS(id_node->id_orig->name);
			if (id_type == ID_OB) {
				Object *object = (Object *)id_node->id_orig;
				ID *ob_data = (ID *)object->data;
				DEG_id_tag_update_ex(bmain, ob_data, flag);
			}
		}
#endif
	}
	if (flag & OB_RECALC_TIME) {
		id_tag_update_object_time(graph, id_node);
	}
	if (flag & PSYS_RECALC) {
		id_tag_update_particle(graph, id_node, flag);
	}
	if (flag & DEG_TAG_SHADING_UPDATE) {
		id_tag_update_shading(graph, id_node);
	}
#ifdef WITH_COPY_ON_WRITE
	if (flag & DEG_TAG_COPY_ON_WRITE) {
		id_tag_update_copy_on_write(graph, id_node);
	}
#endif
}

void deg_id_tag_update(Main *bmain, ID *id, int flag)
{
	lib_id_recalc_tag_flag(bmain, id, flag);
	for (Scene *scene = (Scene *)bmain->scene.first;
	     scene != NULL;
	     scene = (Scene *)scene->id.next)
	{
		if (scene->depsgraph_legacy != NULL) {
			Depsgraph *graph = (Depsgraph *)scene->depsgraph_legacy;
			deg_graph_id_tag_update(bmain, graph, id, flag);
		}
	}
}

void deg_graph_on_visible_update(Main *bmain, Scene *scene, Depsgraph *graph)
{
	/* Make sure objects are up to date. */
	GHASH_FOREACH_BEGIN(DEG::IDDepsNode *, id_node, graph->id_hash)
	{
		const short id_type = GS(id_node->id_orig->name);
		if (id_type != ID_OB) {
			/* Ignore non-object nodes on visibility changes. */
			continue;
		}
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
	GHASH_FOREACH_END();
	/* Make sure collection properties are up to date. */
	IDDepsNode *scene_id_node = graph->find_id_node(&scene->id);
	BLI_assert(scene_id_node != NULL);
	scene_id_node->tag_update(graph);
}

}  /* namespace */

}  // namespace DEG

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
	DEG_DEBUG_PRINTF("%s: id=%s flag=%d\n", __func__, id->name, flag);
	DEG::deg_id_tag_update(bmain, id, flag);
}

/* Tag given ID type for update. */
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

/* Recursively push updates out to all nodes dependent on this,
 * until all affected are tagged and/or scheduled up for eval
 */
void DEG_ids_flush_tagged(Main *bmain, Scene *scene)
{
	/* TODO(sergey): Only visible scenes? */
	if (scene->depsgraph_legacy != NULL) {
		DEG::deg_graph_flush_updates(
		        bmain,
		        reinterpret_cast<DEG::Depsgraph *>(scene->depsgraph_legacy));
	}
}

/* Update dependency graph when visible scenes/layers changes. */
void DEG_graph_on_visible_update(Main *bmain, Scene *scene)
{
	DEG::Depsgraph *graph = (DEG::Depsgraph *)scene->depsgraph_legacy;
	DEG::deg_graph_on_visible_update(bmain, scene, graph);
}

void DEG_on_visible_update(Main *bmain, const bool UNUSED(do_time))
{
	for (Scene *scene = (Scene *)bmain->scene.first;
	     scene != NULL;
	     scene = (Scene *)scene->id.next)
	{
		if (scene->depsgraph_legacy != NULL) {
			DEG_graph_on_visible_update(bmain, scene);
		}
	}
}

/* Check if something was changed in the database and inform
 * editors about this.
 */
void DEG_ids_check_recalc(Main *bmain, Scene *scene, bool time)
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

	DEG::deg_editors_scene_update(bmain, scene, (updated || time));
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
				id->tag &= ~(LIB_TAG_ID_RECALC | LIB_TAG_ID_RECALC_DATA);

				/* Some ID's contain semi-datablock nodetree */
				ntree = ntreeFromID(id);
				if (ntree != NULL) {
					ntree->id.tag &= ~(LIB_TAG_ID_RECALC | LIB_TAG_ID_RECALC_DATA);
				}
			}
		}
	}

	memset(bmain->id_tag_update, 0, sizeof(bmain->id_tag_update));
}
