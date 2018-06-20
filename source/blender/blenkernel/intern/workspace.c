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
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/workspace.c
 *  \ingroup bke
 */

/* allow accessing private members of DNA_workspace_types.h */
#define DNA_PRIVATE_WORKSPACE_ALLOW

#include <stdlib.h>
#include <string.h>

#include "BLI_utildefines.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"
#include "BLI_string_utils.h"
#include "BLI_listbase.h"

#include "BKE_global.h"
#include "BKE_idprop.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_scene.h"
#include "BKE_screen.h"
#include "BKE_object.h"
#include "BKE_workspace.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_workspace_types.h"

#include "DEG_depsgraph.h"

#include "MEM_guardedalloc.h"


/* -------------------------------------------------------------------- */
/* Internal utils */

static void workspace_layout_name_set(
        WorkSpace *workspace, WorkSpaceLayout *layout, const char *new_name)
{
	BLI_strncpy(layout->name, new_name, sizeof(layout->name));
	BLI_uniquename(&workspace->layouts, layout, "Layout", '.', offsetof(WorkSpaceLayout, name), sizeof(layout->name));
}

/**
 * This should only be used directly when it is to be expected that there isn't
 * a layout within \a workspace that wraps \a screen. Usually - especially outside
 * of BKE_workspace - #BKE_workspace_layout_find should be used!
 */
static WorkSpaceLayout *workspace_layout_find_exec(
        const WorkSpace *workspace, const bScreen *screen)
{
	return BLI_findptr(&workspace->layouts, screen, offsetof(WorkSpaceLayout, screen));
}

static void workspace_relation_add(
        ListBase *relation_list, void *parent, void *data)
{
	WorkSpaceDataRelation *relation = MEM_callocN(sizeof(*relation), __func__);
	relation->parent = parent;
	relation->value = data;
	/* add to head, if we switch back to it soon we find it faster. */
	BLI_addhead(relation_list, relation);
}
static void workspace_relation_remove(
        ListBase *relation_list, WorkSpaceDataRelation *relation)
{
	BLI_remlink(relation_list, relation);
	MEM_freeN(relation);
}

static void workspace_relation_ensure_updated(
        ListBase *relation_list, void *parent, void *data)
{
	WorkSpaceDataRelation *relation = BLI_findptr(relation_list, parent, offsetof(WorkSpaceDataRelation, parent));
	if (relation != NULL) {
		relation->value = data;
		/* reinsert at the head of the list, so that more commonly used relations are found faster. */
		BLI_remlink(relation_list, relation);
		BLI_addhead(relation_list, relation);
	}
	else {
		/* no matching relation found, add new one */
		workspace_relation_add(relation_list, parent, data);
	}
}

static void *workspace_relation_get_data_matching_parent(
        const ListBase *relation_list, const void *parent)
{
	WorkSpaceDataRelation *relation = BLI_findptr(relation_list, parent, offsetof(WorkSpaceDataRelation, parent));
	if (relation != NULL) {
		return relation->value;
	}
	else {
		return NULL;
	}
}

/**
 * Checks if \a screen is already used within any workspace. A screen should never be assigned to multiple
 * WorkSpaceLayouts, but that should be ensured outside of the BKE_workspace module and without such checks.
 * Hence, this should only be used as assert check before assigining a screen to a workspace.
 */
#ifndef NDEBUG
static bool workspaces_is_screen_used
#else
static bool UNUSED_FUNCTION(workspaces_is_screen_used)
#endif
        (const Main *bmain, bScreen *screen)
{
	for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
		if (workspace_layout_find_exec(workspace, screen)) {
			return true;
		}
	}

	return false;
}

/* -------------------------------------------------------------------- */
/* Create, delete, init */

WorkSpace *BKE_workspace_add(Main *bmain, const char *name)
{
	WorkSpace *new_workspace = BKE_libblock_alloc(bmain, ID_WS, name, 0);
	return new_workspace;
}

/**
 * The function that actually frees the workspace data (not workspace itself). It shouldn't be called
 * directly, instead #BKE_workspace_remove should be, which calls this through #BKE_libblock_free then.
 *
 * Should something like a bke_internal.h be added, this should go there!
 */
void BKE_workspace_free(WorkSpace *workspace)
{
	BKE_workspace_relations_free(&workspace->hook_layout_relations);
	BLI_freelistN(&workspace->scene_layer_relations);

	BLI_freelistN(&workspace->owner_ids);
	BLI_freelistN(&workspace->layouts);

	for (bToolRef *tref = workspace->tools.first, *tref_next; tref; tref = tref_next) {
		tref_next = tref->next;
		if (tref->runtime) {
			MEM_freeN(tref->runtime);
			if (tref->properties) {
				IDP_FreeProperty(tref->properties);
				MEM_freeN(tref->properties);
			}
		}
	}
	BLI_freelistN(&workspace->tools);
}

/**
 * Remove \a workspace by freeing itself and its data. This is a higher-level wrapper that
 * calls #BKE_workspace_free (through #BKE_libblock_free) to free the workspace data, and frees
 * other data-blocks owned by \a workspace and its layouts (currently that is screens only).
 *
 * Always use this to remove (and free) workspaces. Don't free non-ID workspace members here.
 */
void BKE_workspace_remove(Main *bmain, WorkSpace *workspace)
{
	for (WorkSpaceLayout *layout = workspace->layouts.first, *layout_next; layout; layout = layout_next) {
		layout_next = layout->next;
		BKE_workspace_layout_remove(bmain, workspace, layout);
	}
	BKE_libblock_free(bmain, workspace);
}

WorkSpaceInstanceHook *BKE_workspace_instance_hook_create(const Main *bmain)
{
	WorkSpaceInstanceHook *hook = MEM_callocN(sizeof(WorkSpaceInstanceHook), __func__);

	/* set an active screen-layout for each possible window/workspace combination */
	for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
		BKE_workspace_hook_layout_for_workspace_set(hook, workspace, workspace->layouts.first);
	}

	return hook;
}
void BKE_workspace_instance_hook_free(const Main *bmain, WorkSpaceInstanceHook *hook)
{
	/* workspaces should never be freed before wm (during which we call this function) */
	BLI_assert(!BLI_listbase_is_empty(&bmain->workspaces));

	/* Free relations for this hook */
	for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
		for (WorkSpaceDataRelation *relation = workspace->hook_layout_relations.first, *relation_next;
		     relation;
		     relation = relation_next)
		{
			relation_next = relation->next;
			if (relation->parent == hook) {
				workspace_relation_remove(&workspace->hook_layout_relations, relation);
			}
		}
	}

	MEM_freeN(hook);
}

/**
 * Add a new layout to \a workspace for \a screen.
 */
WorkSpaceLayout *BKE_workspace_layout_add(
        Main *bmain,
        WorkSpace *workspace,
        bScreen *screen,
        const char *name)
{
	WorkSpaceLayout *layout = MEM_callocN(sizeof(*layout), __func__);

	BLI_assert(!workspaces_is_screen_used(bmain, screen));
	layout->screen = screen;
	workspace_layout_name_set(workspace, layout, name);
	BLI_addtail(&workspace->layouts, layout);

	return layout;
}

void BKE_workspace_layout_remove(
        Main *bmain,
        WorkSpace *workspace, WorkSpaceLayout *layout)
{
	BKE_libblock_free(bmain, BKE_workspace_layout_screen_get(layout));
	BLI_freelinkN(&workspace->layouts, layout);
}

void BKE_workspace_relations_free(
        ListBase *relation_list)
{
	for (WorkSpaceDataRelation *relation = relation_list->first, *relation_next; relation; relation = relation_next) {
		relation_next = relation->next;
		workspace_relation_remove(relation_list, relation);
	}
}

void BKE_workspace_scene_relations_free_invalid(
        WorkSpace *workspace)
{
	for (WorkSpaceSceneRelation *relation = workspace->scene_layer_relations.first, *relation_next; relation; relation = relation_next) {
		relation_next = relation->next;

		if (relation->scene == NULL) {
			BLI_freelinkN(&workspace->scene_layer_relations, relation);
		}
		else if (!BLI_findstring(&relation->scene->view_layers, relation->view_layer, offsetof(ViewLayer, name))) {
			BLI_freelinkN(&workspace->scene_layer_relations, relation);
		}
	}
}

/* -------------------------------------------------------------------- */
/* General Utils */

void BKE_workspace_view_layer_rename(
        const Main *bmain,
        const Scene *scene,
        const char *old_name,
        const char *new_name)
{
	for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
		for (WorkSpaceSceneRelation *relation = workspace->scene_layer_relations.first; relation; relation = relation->next) {
			if (relation->scene == scene && STREQ(relation->view_layer, old_name)) {
				STRNCPY(relation->view_layer, new_name);
			}
		}
	}
}

void BKE_workspace_view_layer_remove(
        const Main *bmain,
        const ViewLayer *UNUSED(view_layer))
{
	for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
		BKE_workspace_scene_relations_free_invalid(workspace);
	}
}

WorkSpaceLayout *BKE_workspace_layout_find(
        const WorkSpace *workspace, const bScreen *screen)
{
	WorkSpaceLayout *layout = workspace_layout_find_exec(workspace, screen);
	if (layout) {
		return layout;
	}

	printf("%s: Couldn't find layout in this workspace: '%s' screen: '%s'. "
	       "This should not happen!\n",
	       __func__, workspace->id.name + 2, screen->id.name + 2);

	return NULL;
}

/**
 * Find the layout for \a screen without knowing which workspace to look in.
 * Can also be used to find the workspace that contains \a screen.
 *
 * \param r_workspace: Optionally return the workspace that contains the looked up layout (if found).
 */
WorkSpaceLayout *BKE_workspace_layout_find_global(
        const Main *bmain, const bScreen *screen,
        WorkSpace **r_workspace)
{
	WorkSpaceLayout *layout;

	if (r_workspace) {
		*r_workspace = NULL;
	}

	for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
		if ((layout = workspace_layout_find_exec(workspace, screen))) {
			if (r_workspace) {
				*r_workspace = workspace;
			}

			return layout;
		}
	}

	return NULL;
}

/**
 * Circular workspace layout iterator.
 *
 * \param callback: Custom function which gets executed for each layout. Can return false to stop iterating.
 * \param arg: Custom data passed to each \a callback call.
 *
 * \return the layout at which \a callback returned false.
 */
WorkSpaceLayout *BKE_workspace_layout_iter_circular(
        const WorkSpace *workspace, WorkSpaceLayout *start,
        bool (*callback)(const WorkSpaceLayout *layout, void *arg),
        void *arg, const bool iter_backward)
{
	WorkSpaceLayout *iter_layout;

	if (iter_backward) {
		LISTBASE_CIRCULAR_BACKWARD_BEGIN(&workspace->layouts, iter_layout, start)
		{
			if (!callback(iter_layout, arg)) {
				return iter_layout;
			}
		}
		LISTBASE_CIRCULAR_BACKWARD_END(&workspace->layouts, iter_layout, start);
	}
	else {
		LISTBASE_CIRCULAR_FORWARD_BEGIN(&workspace->layouts, iter_layout, start)
		{
			if (!callback(iter_layout, arg)) {
				return iter_layout;
			}
		}
		LISTBASE_CIRCULAR_FORWARD_END(&workspace->layouts, iter_layout, start)
	}

	return NULL;
}


/* -------------------------------------------------------------------- */
/* Getters/Setters */

WorkSpace *BKE_workspace_active_get(WorkSpaceInstanceHook *hook)
{
	return hook->active;
}
void BKE_workspace_active_set(WorkSpaceInstanceHook *hook, WorkSpace *workspace)
{
	hook->active = workspace;
	if (workspace) {
		WorkSpaceLayout *layout = workspace_relation_get_data_matching_parent(&workspace->hook_layout_relations, hook);
		if (layout) {
			hook->act_layout = layout;
		}
	}
}

WorkSpaceLayout *BKE_workspace_active_layout_get(const WorkSpaceInstanceHook *hook)
{
	return hook->act_layout;
}
void BKE_workspace_active_layout_set(WorkSpaceInstanceHook *hook, WorkSpaceLayout *layout)
{
	hook->act_layout = layout;
}

bScreen *BKE_workspace_active_screen_get(const WorkSpaceInstanceHook *hook)
{
	return hook->act_layout->screen;
}
void BKE_workspace_active_screen_set(WorkSpaceInstanceHook *hook, WorkSpace *workspace, bScreen *screen)
{
	/* we need to find the WorkspaceLayout that wraps this screen */
	WorkSpaceLayout *layout = BKE_workspace_layout_find(hook->active, screen);
	BKE_workspace_hook_layout_for_workspace_set(hook, workspace, layout);
}

Base *BKE_workspace_active_base_get(const WorkSpace *workspace, const Scene *scene)
{
	ViewLayer *view_layer = BKE_workspace_view_layer_get(workspace, scene);
	return view_layer->basact;
}

ViewLayer *BKE_workspace_view_layer_exists(const WorkSpace *workspace, const Scene *scene)
{
	WorkSpaceSceneRelation *relation = BLI_findptr(&workspace->scene_layer_relations, scene, offsetof(WorkSpaceSceneRelation, scene));
	return (relation) ? BLI_findstring(&scene->view_layers, relation->view_layer, offsetof(ViewLayer, name)) : NULL;
}

ViewLayer *BKE_workspace_view_layer_get(const WorkSpace *workspace, const Scene *scene)
{
	ViewLayer *layer = BKE_workspace_view_layer_exists(workspace, scene);

	if (layer == NULL) {
		BKE_workspace_view_layer_set((WorkSpace *)workspace, scene->view_layers.first, (Scene *)scene);
		layer = scene->view_layers.first;
	}

	return layer;
}

void BKE_workspace_view_layer_set(WorkSpace *workspace, ViewLayer *layer, Scene *scene)
{
	WorkSpaceSceneRelation *relation = BLI_findptr(&workspace->scene_layer_relations, scene, offsetof(WorkSpaceSceneRelation, scene));
	if (relation == NULL) {
		relation = MEM_callocN(sizeof(*relation), __func__);
	}
	else {
		BLI_remlink(&workspace->scene_layer_relations, relation);
	}

	/* (Re)insert at the head of the list, for faster lookups. */
	relation->scene = scene;
	STRNCPY(relation->view_layer, layer->name);
	BLI_addhead(&workspace->scene_layer_relations, relation);
}

ListBase *BKE_workspace_layouts_get(WorkSpace *workspace)
{
	return &workspace->layouts;
}

const char *BKE_workspace_layout_name_get(const WorkSpaceLayout *layout)
{
	return layout->name;
}
void BKE_workspace_layout_name_set(WorkSpace *workspace, WorkSpaceLayout *layout, const char *new_name)
{
	workspace_layout_name_set(workspace, layout, new_name);
}

bScreen *BKE_workspace_layout_screen_get(const WorkSpaceLayout *layout)
{
	return layout->screen;
}
void BKE_workspace_layout_screen_set(WorkSpaceLayout *layout, bScreen *screen)
{
	layout->screen = screen;
}

WorkSpaceLayout *BKE_workspace_hook_layout_for_workspace_get(
        const WorkSpaceInstanceHook *hook, const WorkSpace *workspace)
{
	return workspace_relation_get_data_matching_parent(&workspace->hook_layout_relations, hook);
}
void BKE_workspace_hook_layout_for_workspace_set(
        WorkSpaceInstanceHook *hook, WorkSpace *workspace, WorkSpaceLayout *layout)
{
	hook->act_layout = layout;
	workspace_relation_ensure_updated(&workspace->hook_layout_relations, hook, layout);
}

/* Update / evaluate */

void BKE_workspace_update_tagged(Main *bmain,
                                 WorkSpace *workspace,
                                 Scene *scene)
{
	ViewLayer *view_layer = BKE_workspace_view_layer_get(workspace, scene);
	struct Depsgraph *depsgraph = BKE_scene_get_depsgraph(scene,
	                                                      view_layer,
	                                                      true);
	/* TODO(sergey): For now all dependency graphs which are evaluated from
	 * workspace are considered active. This will work all fine with "locked"
	 * view layer and time across windows. This is to be granted separately,
	 * and for until then we have to accept ambiguities when object is shared
	 * across visible view layers and has overrides on it.
	 */
	DEG_make_active(depsgraph);
	BKE_scene_graph_update_tagged(depsgraph, bmain);
}


bool BKE_workspace_owner_id_check(
        const WorkSpace *workspace, const char *owner_id)
{
	if ((*owner_id == '\0') ||
	    ((workspace->flags & WORKSPACE_USE_FILTER_BY_ORIGIN) == 0))
	{
		return true;
	}
	else {
		/* we could use hash lookup, for now this list is highly under < ~16 items. */
		return BLI_findstring(&workspace->owner_ids, owner_id, offsetof(wmOwnerID, name)) != NULL;
	}
}

