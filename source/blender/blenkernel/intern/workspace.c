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

#include "BLI_utildefines.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"
#include "BLI_string_utils.h"
#include "BLI_listbase.h"

#include "BKE_global.h"
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

static void workspace_relation_remove_from_value(
        ListBase *relation_list, const void *value)
{
	for (WorkSpaceDataRelation *relation = relation_list->first, *relation_next; relation; relation = relation_next) {
		relation_next = relation->next;

		if (relation->value == value) {
			workspace_relation_remove(relation_list, relation);
		}
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
	BKE_workspace_relations_free(&workspace->scene_viewlayer_relations);

	BLI_freelistN(&workspace->owner_ids);
	BLI_freelistN(&workspace->layouts);
	BLI_freelistN(&workspace->transform_orientations);

	BKE_viewrender_free(&workspace->view_render);
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
        WorkSpace *workspace,
        bScreen *screen,
        const char *name)
{
	WorkSpaceLayout *layout = MEM_callocN(sizeof(*layout), __func__);

	BLI_assert(!workspaces_is_screen_used(G.main, screen));
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


/* -------------------------------------------------------------------- */
/* General Utils */

void BKE_workspace_view_layer_remove_references(
        const Main *bmain,
        const ViewLayer *view_layer)
{
	for (WorkSpace *workspace = bmain->workspaces.first; workspace; workspace = workspace->id.next) {
		workspace_relation_remove_from_value(&workspace->scene_viewlayer_relations, view_layer);
	}
}

void BKE_workspace_transform_orientation_remove(
        WorkSpace *workspace, TransformOrientation *orientation)
{
	for (WorkSpaceLayout *layout = workspace->layouts.first; layout; layout = layout->next) {
		BKE_screen_transform_orientation_remove(BKE_workspace_layout_screen_get(layout), workspace, orientation);
	}

	BLI_freelinkN(&workspace->transform_orientations, orientation);
}

TransformOrientation *BKE_workspace_transform_orientation_find(
        const WorkSpace *workspace, const int index)
{
	return BLI_findlink(&workspace->transform_orientations, index);
}

/**
 * \return the index that \a orientation has within \a workspace's transform-orientation list or -1 if not found.
 */
int BKE_workspace_transform_orientation_get_index(
        const WorkSpace *workspace, const TransformOrientation *orientation)
{
	return BLI_findindex(&workspace->transform_orientations, orientation);
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

ListBase *BKE_workspace_transform_orientations_get(WorkSpace *workspace)
{
	return &workspace->transform_orientations;
}

ViewLayer *BKE_workspace_view_layer_get(const WorkSpace *workspace, const Scene *scene)
{
	return workspace_relation_get_data_matching_parent(&workspace->scene_viewlayer_relations, scene);
}
void BKE_workspace_view_layer_set(WorkSpace *workspace, ViewLayer *layer, Scene *scene)
{
	workspace_relation_ensure_updated(&workspace->scene_viewlayer_relations, scene, layer);
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

/**
 * Get the render engine of a workspace, to be used in the viewport.
 */
ViewRender *BKE_workspace_view_render_get(WorkSpace *workspace)
{
	return &workspace->view_render;
}

/* Flags */
bool BKE_workspace_use_scene_settings_get(const WorkSpace *workspace)
{
	return (workspace->flags & WORKSPACE_USE_SCENE_SETTINGS) != 0;
}

void BKE_workspace_use_scene_settings_set(WorkSpace *workspace, bool value)
{
	if (value) {
		workspace->flags |= WORKSPACE_USE_SCENE_SETTINGS;
	}
	else {
		workspace->flags &= ~WORKSPACE_USE_SCENE_SETTINGS;
	}
}

/* Update / evaluate */

void BKE_workspace_update_tagged(struct EvaluationContext *eval_ctx,
                                 Main *bmain,
                                 WorkSpace *workspace,
                                 Scene *scene)
{
	ViewLayer *view_layer = BKE_workspace_view_layer_get(workspace, scene);
	struct Depsgraph *depsgraph = BKE_scene_get_depsgraph(scene,
	                                                      view_layer,
	                                                      true);
	BKE_scene_graph_update_tagged(eval_ctx, depsgraph, bmain, scene, view_layer);
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

