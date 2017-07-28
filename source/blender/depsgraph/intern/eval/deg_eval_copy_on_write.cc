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
 * The Original Code is Copyright (C) 20137Blender Foundation.
 * All rights reserved.
 *
 * Original Author: Sergey Sharybin
 * Contributor(s): None Yet
 *
 * ***** END GPL LICENSE BLOCK *****
 */


/** \file blender/depsgraph/intern/eval/deg_eval_copy_on_write.h
 *  \ingroup depsgraph
 */

/* Enable special; trickery to treat nested owned IDs (such as nodetree of
 * material) to be handled in same way as "real" datablocks, even tho some
 * internal BKE routines doesn't treat them like that.
 *
 * TODO(sergey): Re-evaluate that after new ID handling is in place.
 */
#define NESTED_ID_NASTY_WORKAROUND

#include "intern/eval/deg_eval_copy_on_write.h"

#include <cstring>

#include "BLI_utildefines.h"
#include "BLI_threads.h"

#include "BKE_global.h"
#include "BKE_layer.h"
#include "BKE_library.h"
#include "BKE_main.h"
#include "BKE_scene.h"

#include "DEG_depsgraph.h"

#include "MEM_guardedalloc.h"

extern "C" {
#include "DNA_ID.h"
#include "DNA_mesh_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#ifdef NESTED_ID_NASTY_WORKAROUND
#  include "DNA_key_types.h"
#  include "DNA_lamp_types.h"
#  include "DNA_linestyle_types.h"
#  include "DNA_material_types.h"
#  include "DNA_mesh_types.h"
#  include "DNA_node_types.h"
#  include "DNA_scene_types.h"
#  include "DNA_texture_types.h"
#  include "DNA_world_types.h"
#endif

#include "BKE_action.h"
#include "BKE_editmesh.h"
#include "BKE_library_query.h"
#include "BKE_object.h"
}

#include "intern/depsgraph.h"
#include "intern/builder/deg_builder_nodes.h"
#include "intern/nodes/deg_node.h"

namespace DEG {

#define DEBUG_PRINT if (G.debug & G_DEBUG_DEPSGRAPH) printf

namespace {

#ifdef NESTED_ID_NASTY_WORKAROUND
union NestedIDHackTempStorage {
	FreestyleLineStyle linestyle;
	Lamp lamp;
	Material material;
	Mesh mesh;
	Scene scene;
	Tex tex;
	World world;
};

/* Set nested owned ID pointers to NULL. */
void nested_id_hack_discard_pointers(ID *id_cow)
{
	switch (GS(id_cow->name)) {
#  define SPECIAL_CASE(id_type, dna_type, field)  \
		case id_type:                             \
		{                                         \
			((dna_type *)id_cow)->field = NULL;   \
			break;                                \
		}

		SPECIAL_CASE(ID_LS, FreestyleLineStyle, nodetree)
		SPECIAL_CASE(ID_LA, Lamp, nodetree)
		SPECIAL_CASE(ID_MA, Material, nodetree)
#if 0
		SPECIAL_CASE(ID_SCE, Scene, nodetree)
#else
		case ID_SCE:
		{
			Scene *scene_cow = (Scene *)id_cow;
			scene_cow->nodetree = NULL;
			BLI_listbase_clear(&scene_cow->base);
			break;
		}
#endif
		SPECIAL_CASE(ID_TE, Tex, nodetree)
		SPECIAL_CASE(ID_WO, World, nodetree)

		SPECIAL_CASE(ID_ME, Mesh, key)

#  undef SPECIAL_CASE

		default:
			break;
	}
}

/* Set ID pointer of nested owned IDs (nodetree, key) to NULL.
 *
 * Return pointer to a new ID to be used.
 */
const ID *nested_id_hack_get_discarded_pointers(NestedIDHackTempStorage *storage,
                                                const ID *id)
{
	switch (GS(id->name)) {
#  define SPECIAL_CASE(id_type, dna_type, field, variable)  \
		case id_type:                                       \
		{                                                   \
			storage->variable = *(dna_type *)id;            \
			storage->variable.field = NULL;                 \
			return &storage->variable.id;                   \
		}

		SPECIAL_CASE(ID_LS, FreestyleLineStyle, nodetree, linestyle)
		SPECIAL_CASE(ID_LA, Lamp, nodetree, lamp)
		SPECIAL_CASE(ID_MA, Material, nodetree, material)
#if 0
		SPECIAL_CASE(ID_SCE, Scene, nodetree, scene)
#else
		case ID_SCE:
		{
			storage->scene = *(Scene *)id;
			storage->scene.nodetree = NULL;
			BLI_listbase_clear(&storage->scene.base);
			return &storage->scene.id;
		}
#endif
		SPECIAL_CASE(ID_TE, Tex, nodetree, tex)
		SPECIAL_CASE(ID_WO, World, nodetree, world)

		SPECIAL_CASE(ID_ME, Mesh, key, mesh)

#  undef SPECIAL_CASE

		default:
			break;
	}
	return id;
}

/* Set ID pointer of nested owned IDs (nodetree, key) to the original value. */
void nested_id_hack_restore_pointers(const ID *old_id, ID *new_id)
{
	if (new_id == NULL) {
		return;
	}
	switch (GS(old_id->name)) {
#  define SPECIAL_CASE(id_type, dna_type, field)    \
		case id_type:                               \
		{                                           \
			((dna_type *)(new_id))->field =         \
			        ((dna_type *)(old_id))->field;  \
			break;                                  \
		}

		SPECIAL_CASE(ID_LS, FreestyleLineStyle, nodetree)
		SPECIAL_CASE(ID_LA, Lamp, nodetree)
		SPECIAL_CASE(ID_MA, Material, nodetree)
		SPECIAL_CASE(ID_SCE, Scene, nodetree)
		SPECIAL_CASE(ID_TE, Tex, nodetree)
		SPECIAL_CASE(ID_WO, World, nodetree)

		SPECIAL_CASE(ID_ME, Mesh, key)

#undef SPECIAL_CASE
		default:
			break;
	}
}

/* Remap pointer of nested owned IDs (nodetree. key) to the new ID values. */
void ntree_hack_remap_pointers(const Depsgraph *depsgraph, ID *id_cow)
{
	switch (GS(id_cow->name)) {
#  define SPECIAL_CASE(id_type, dna_type, field, field_type)                   \
		case id_type:                                                          \
		{                                                                      \
			dna_type *data = (dna_type *)id_cow;                               \
			if (data->field != NULL) {                                         \
				ID *ntree_id_cow = depsgraph->get_cow_id(&data->field->id);    \
				if (ntree_id_cow != NULL) {                                    \
					DEG_COW_PRINT("    Remapping datablock for %s: id_orig=%p id_cow=%p\n", \
					              data->field->id.name,                        \
					              data->field,                                 \
					              ntree_id_cow);                               \
					data->field = (field_type *)ntree_id_cow;                  \
				}                                                              \
			}                                                                  \
			break;                                                             \
		}

		SPECIAL_CASE(ID_LS, FreestyleLineStyle, nodetree, bNodeTree)
		SPECIAL_CASE(ID_LA, Lamp, nodetree, bNodeTree)
		SPECIAL_CASE(ID_MA, Material, nodetree, bNodeTree)
		SPECIAL_CASE(ID_SCE, Scene, nodetree, bNodeTree)
		SPECIAL_CASE(ID_TE, Tex, nodetree, bNodeTree)
		SPECIAL_CASE(ID_WO, World, nodetree, bNodeTree)

		SPECIAL_CASE(ID_ME, Mesh, key, Key)

#undef SPECIAL_CASE
		default:
			break;
	}
}
#endif  /* NODETREE_NASTY_WORKAROUND */

struct ValidateData {
	bool is_valid;
};

/* Similar to generic id_copy() but does not require main.
 *
 * TODO(sergey): Get rid of this once T51804 is handled.
 */
bool id_copy_no_main(const ID *id, ID **newid)
{
	const ID *id_for_copy = id;
	Main temp_bmain = {0};
	SpinLock lock;
	temp_bmain.lock = (MainLock *)&lock;
	BLI_spin_init(&lock);

#ifdef NESTED_ID_NASTY_WORKAROUND
	NestedIDHackTempStorage id_hack_storage;
	id_for_copy = nested_id_hack_get_discarded_pointers(&id_hack_storage, id);
#endif

	bool result = id_copy(&temp_bmain, (ID *)id_for_copy, newid, false);

#ifdef NESTED_ID_NASTY_WORKAROUND
	if (result) {
		nested_id_hack_restore_pointers(id, *newid);
	}
#endif

	BLI_spin_end(&lock);
	return result;
}

void layer_collections_sync_flags(ListBase *layer_collections_dst,
                                  const ListBase *layer_collections_src)
{
	LayerCollection *layer_collection_dst = (LayerCollection *)layer_collections_dst->first;
	const LayerCollection *layer_collection_src = (const LayerCollection *)layer_collections_src->first;
	while (layer_collection_dst != NULL) {
		layer_collection_dst->flag = layer_collection_src->flag;
		layer_collections_sync_flags(&layer_collection_dst->layer_collections,
		                             &layer_collection_src->layer_collections);
		/* TODO(sergey): Overrides. */
		layer_collection_dst = layer_collection_dst->next;
		layer_collection_src = layer_collection_src->next;
	}
}

/* Similar to BKE_scene_copy() but does not require main.
 *
 * TODO(sergey): Get rid of this once T51804 is handled.
 */
Scene *scene_copy_no_main(Scene *scene)
{
	const ID *id_for_copy = &scene->id;
	Main temp_bmain = {0};
	SpinLock lock;
	temp_bmain.lock = (MainLock *)&lock;
	BLI_spin_init(&lock);

#ifdef NESTED_ID_NASTY_WORKAROUND
	NestedIDHackTempStorage id_hack_storage;
	id_for_copy = nested_id_hack_get_discarded_pointers(&id_hack_storage,
	                                                    &scene->id);
#endif

	Scene *new_scene = BKE_scene_copy(&temp_bmain,
	                                  (Scene *)id_for_copy,
	                                  SCE_COPY_LINK_OB);

	/* TODO(sergey): Make this part of BKE_scene_copy(). */
	{
		SceneLayer *new_scene_layer = (SceneLayer *)new_scene->render_layers.first;
		const SceneLayer *scene_layer = (const SceneLayer *)scene->render_layers.first;
		while (new_scene_layer != NULL) {
			layer_collections_sync_flags(&new_scene_layer->layer_collections,
			                             &scene_layer->layer_collections);
			new_scene_layer = new_scene_layer->next;
			scene_layer = scene_layer->next;
		}
	}

#ifdef NESTED_ID_NASTY_WORKAROUND
	nested_id_hack_restore_pointers(&scene->id, &new_scene->id);
#endif

	BLI_spin_end(&lock);
	return new_scene;
}

/* Check whether given ID is expanded or still a shallow copy. */
BLI_INLINE bool check_datablock_expanded(const ID *id_cow)
{
	return (id_cow->name[0] != '\0');
}

/* Check whether datablock was already expanded during depsgraph
 * construction.
 */
static bool check_datablock_expanded_at_construction(const ID *id_orig)
{
	const short id_type = GS(id_orig->name);
	return (id_type == ID_SCE) ||
	       (id_type == ID_OB && ((Object *)id_orig)->type == OB_ARMATURE) ||
	       (id_type == ID_AR);
}

/* Those are datablocks which are not covered by dependency graph and hence
 * does not need any remapping or anything.
 *
 * TODO(sergey): How to make it more robust for the future, so we don't have
 * to maintain exception lists all over the code?
 */
static bool check_datablocks_copy_on_writable(const ID *id_orig)
{
	const short id_type = GS(id_orig->name);
	/* We shouldn't bother if copied ID is same as original one. */
	if (!deg_copy_on_write_is_needed(id_orig)) {
		return false;
	}
	return !ELEM(id_type, ID_BR,
	                      ID_LS,
	                      ID_AC,
	                      ID_GR,
	                      ID_PAL);
}

/* Callback for BKE_library_foreach_ID_link which remaps original ID pointer
 * with the one created by CoW system.
 */

struct RemapCallbackUserData {
	/* Dependency graph for which remapping is happening. */
	const Depsgraph *depsgraph;
	/* Temporarily allocated memory for copying purposes. This ID will
	 * be discarded after expanding is done, so need to make sure temp_id
	 * is replaced with proper real_id.
	 *
	 * NOTE: This is due to our logic of "inplace" duplication, where we
	 * use generic duplication routines (which gives us new ID) which then
	 * is followed with copying data to a placeholder we prepared before and
	 * discarding pointer returned by duplication routines.
	 */
	const ID *temp_id;
	ID *real_id;
	/* Create placeholder for ID nodes for cases when we need to remap original
	 * ID to it[s CoW version but we don't have required ID node yet.
	 *
	 * This happens when expansion happens a ta construction time.
	 */
	DepsgraphNodeBuilder *node_builder;
	bool create_placeholders;
};

int foreach_libblock_remap_callback(void *user_data_v,
                                    ID *id_self,
                                    ID **id_p,
                                    int /*cb_flag*/)
{
	RemapCallbackUserData *user_data = (RemapCallbackUserData *)user_data_v;
	const Depsgraph *depsgraph = user_data->depsgraph;
	if (*id_p != NULL) {
		ID *id_orig = *id_p;
		if (id_orig == user_data->temp_id) {
			DEG_COW_PRINT("    Remapping datablock for %s: id_temp=%p id_cow=%p\n",
			              id_orig->name, id_orig, user_data->real_id);
			*id_p = user_data->real_id;
		}
		else if (check_datablocks_copy_on_writable(id_orig)) {
			ID *id_cow;
			if (user_data->create_placeholders) {
				/* Special workaround to stop creating temp datablocks for
				 * objects which are coming from scene's collection and which
				 * are never linked to any of layers.
				 *
				 * TODO(sergey): Ideally we need to tell ID looper to ignore
				 * those or at least make it more reliable check where the
				 * pointer is coming from.
				 */
				const short id_type = GS(id_orig->name);
				const short id_type_self = GS(id_self->name);
				if (id_type == ID_OB && id_type_self == ID_SCE) {
					IDDepsNode *id_node = depsgraph->find_id_node(id_orig);
					if (id_node == NULL) {
						id_cow = id_orig;
					}
					else {
						id_cow = id_node->id_cow;
					}
				}
				else {
					id_cow = user_data->node_builder->ensure_cow_id(id_orig);
				}
			}
			else {
				id_cow = depsgraph->get_cow_id(id_orig);
			}
			BLI_assert(id_cow != NULL);
			DEG_COW_PRINT("    Remapping datablock for %s: id_orig=%p id_cow=%p\n",
			              id_orig->name, id_orig, id_cow);
			*id_p = id_cow;
		}
	}
	return IDWALK_RET_NOP;
}

/* Do some special treatment of data transfer from original ID to it's
 * CoW complementary part.
 *
 * Only use for the newly created CoW datablocks.
 */
void update_special_pointers(const Depsgraph *depsgraph,
                             const ID *id_orig, ID *id_cow)
{
	const short type = GS(id_orig->name);
	switch (type) {
		case ID_OB:
		{
			/* Ensure we don't drag someone's else derived mesh to the
			 * new copy of the object.
			 */
			Object *object_cow = (Object *)id_cow;
			const Object *object_orig = (const Object *)id_orig;
			(void) object_cow;  /* Ignored for release builds. */
			BLI_assert(object_cow->derivedFinal == NULL);
			BLI_assert(object_cow->derivedDeform == NULL);
			object_cow->mode = object_orig->mode;
			break;
		}
		case ID_ME:
		{
			/* For meshes we need to update edit_brtmesh to make it to point
			 * to the CoW version of object.
			 *
			 * This is kind of confusing, because actual bmesh is not owned by
			 * the CoW object, so need to be accurate about using link from
			 * edit_btmesh to object.
			 */
			const Mesh *mesh_orig = (const Mesh *)id_orig;
			Mesh *mesh_cow = (Mesh *)id_cow;
			if (mesh_orig->edit_btmesh != NULL) {
				mesh_cow->edit_btmesh = (BMEditMesh *)MEM_dupallocN(mesh_orig->edit_btmesh);
				mesh_cow->edit_btmesh->ob =
				        (Object *)depsgraph->get_cow_id(&mesh_orig->edit_btmesh->ob->id);
				mesh_cow->edit_btmesh->derivedFinal = NULL;
				mesh_cow->edit_btmesh->derivedCage = NULL;
			}
			break;
		}
		case ID_SCE:
		{
			const Scene *scene_orig = (const Scene *)id_orig;
			Scene *scene_cow = (Scene *)id_cow;
			if (scene_orig->obedit != NULL) {
				scene_cow->obedit = (Object *)depsgraph->get_cow_id(&scene_orig->obedit->id);
			}
			else {
				scene_cow->obedit = NULL;
			}
			break;
		}
	}
}

/* Update copy-on-write version of scene from original scene. */
void update_copy_on_write_scene(const Depsgraph *depsgraph,
                                Scene *scene_cow,
                                const Scene *scene_orig)
{
	// Some non-pointer data sync, current frame for now.
	// TODO(sergey): Are we missing something here?
	scene_cow->r.cfra = scene_orig->r.cfra;
	scene_cow->r.subframe = scene_orig->r.subframe;
	// Update bases.
	const SceneLayer *sl_orig = (SceneLayer *)scene_orig->render_layers.first;
	SceneLayer *sl_cow = (SceneLayer *)scene_cow->render_layers.first;
	while (sl_orig != NULL) {
		// Update pointers to active base.
		if (sl_orig->basact == NULL) {
			sl_cow->basact = NULL;
		}
		else {
			const Object *obact_orig = sl_orig->basact->object;
			Object *obact_cow = (Object *)depsgraph->get_cow_id(&obact_orig->id);
			sl_cow->basact = BKE_scene_layer_base_find(sl_cow, obact_cow);
		}
		// Update base flags.
		//
		// TODO(sergey): We should probably check visibled/selectabled
		// flag here?
		const Base *base_orig = (Base *)sl_orig->object_bases.first;
		Base *base_cow = (Base *)sl_cow->object_bases.first;;
		while (base_orig != NULL) {
			base_cow->flag = base_orig->flag;
			base_orig = base_orig->next;
			base_cow = base_cow->next;
		}
		sl_orig = sl_orig->next;
		sl_cow = sl_cow->next;
	}
	// Update edit object pointer.
	if (scene_orig->obedit != NULL) {
		scene_cow->obedit = (Object *)depsgraph->get_cow_id(&scene_orig->obedit->id);
	}
	else {
		scene_cow->obedit = NULL;
	}
	/* Synchronize active render engine. */
	BLI_strncpy_utf8(scene_cow->r.engine,
	                 scene_orig->r.engine,
	                 sizeof(scene_cow->r.engine));
	/* TODO(sergey): What else do we need here? */
}

/* Update copy-on-write version of armature object from original scene. */
void update_copy_on_write_object(const Depsgraph * /*depsgraph*/,
                                 Object *object_cow,
                                 const Object *object_orig)
{
	/* TODO(sergey): This function might be split into a smaller ones,
	 * reused for different updates. And maybe even moved to BKE.
	 */
	/* Update armature/pose related flags. */
	bPose *pose_cow = object_cow->pose;
	const bPose *pose_orig = object_orig->pose;
	extract_pose_from_pose(pose_cow, pose_orig);
	/* Update object itself. */
	BKE_object_transform_copy(object_cow, object_orig);
	object_cow->mode = object_orig->mode;
}

/* Update copy-on-write version of datablock from it's original ID without re-building
 * the whole datablock from scratch.
 *
 * Used for such special cases as scene collections and armatures, which can not use full
 * re-alloc due to pointers used as function bindings.
 */
void update_copy_on_write_datablock(const Depsgraph *depsgraph,
                                    const ID *id_orig, ID *id_cow)
{
	bool ok = false;
	const short id_type = GS(id_orig->name);
	switch (id_type) {
		case ID_SCE: {
			const Scene *scene_orig = (const Scene *)id_orig;
			Scene *scene_cow = (Scene *)id_cow;
			update_copy_on_write_scene(depsgraph, scene_cow, scene_orig);
			ok = true;
			break;
		}
		case ID_OB: {
			const Object *object_orig = (const Object *)id_orig;
			Object *object_cow = (Object *)id_cow;
			if (object_orig->type == OB_ARMATURE) {
				update_copy_on_write_object(depsgraph,
				                            object_cow,
				                            object_orig);
				ok = true;
			}
			break;
		}
		case ID_AR:
			/* Nothing to do currently. */
			ok = true;
			break;
	}
	// TODO(sergey): Other ID types here.
	if (!ok) {
		BLI_assert(!"Missing update logic of expanded datablock");
	}
}

/* This callback is used to validate that all nested ID datablocks are
 * properly expanded.
 */
int foreach_libblock_validate_callback(void *user_data,
                                       ID * /*id_self*/,
                                       ID **id_p,
                                       int /*cb_flag*/)
{
	ValidateData *data = (ValidateData *)user_data;
	if (*id_p != NULL) {
		if (!check_datablock_expanded(*id_p)) {
			data->is_valid = false;
			/* TODO(sergey): Store which is is not valid? */
		}
	}
	return IDWALK_RET_NOP;
}

}  // namespace

/* Actual implementation of logic which "expands" all the data which was not
 * yet copied-on-write.
 *
 * NOTE: Expects that CoW datablock is empty.
 */
ID *deg_expand_copy_on_write_datablock(const Depsgraph *depsgraph,
                                       const IDDepsNode *id_node,
                                       DepsgraphNodeBuilder *node_builder,
                                       bool create_placeholders)
{
	BLI_assert(!create_placeholders ||
	           check_datablock_expanded_at_construction(id_node->id_orig));
	const ID *id_orig = id_node->id_orig;
	ID *id_cow = id_node->id_cow;
	/* No need to expand such datablocks, their copied ID is same as original
	 * one already.
	 */
	if (!deg_copy_on_write_is_needed(id_orig)) {
		return id_cow;
	}
	DEG_COW_PRINT("Expanding datablock for %s: id_orig=%p id_cow=%p\n",
	              id_orig->name, id_orig, id_cow);
	/* Sanity checks. */
	/* NOTE: Disabled for now, conflicts when re-using evaluated datablock when
	 * rebuilding dependencies.
	 */
	if (check_datablock_expanded(id_cow) && create_placeholders) {
		deg_free_copy_on_write_datablock(id_cow);
	}
	// BLI_assert(check_datablock_expanded(id_cow) == false);
	/* Copy data from original ID to a copied version. */
	/* TODO(sergey): Avoid doing full ID copy somehow, make Mesh to reference
	 * original geometry arrays for until those are modified.
	 */
	/* TODO(sergey): We do some trickery with temp bmain and extra ID pointer
	 * just to be able to use existing API. Ideally we need to replace this with
	 * in-place copy from existing datablock to a prepared memory.
	 *
	 * NOTE: We don't use BKE_main_{new,free} because:
	 * - We don't want heap-allocations here.
	 * - We don't want bmain's content to be freed when main is freed.
	 */
	bool done = false;
	/* Need to make sure the possibly temporary allocated memory is correct for
	 * until we are fully done with remapping original pointers with copied on
	 * write ones.
	 */
	ID *newid = NULL;
	/* First we handle special cases which are not covered by id_copy() yet.
	 * or cases where we want to do something smarter than simple datablock
	 * copy.
	 */
	const short id_type = GS(id_orig->name);
	switch (id_type) {
		case ID_SCE:
		{
			Scene *new_scene = scene_copy_no_main((Scene *)id_orig);
			*(Scene *)id_cow = *new_scene;
			MEM_freeN(new_scene);
			done = true;
			break;
		}
		case ID_ME:
		{
			/* TODO(sergey): Ideally we want to handle meshes in a special
			 * manner here to avoid initial copy of all the geometry arrays.
			 */
			break;
		}
	}
	if (!done) {
		if (id_copy_no_main(id_orig, &newid)) {
			/* We copy contents of new ID to our CoW placeholder and free ID memory
			 * returned by id_copy().
			 *
			 * TODO(sergey): We can avoid having extra ID allocation here if we'll
			 * have some smarter id_copy() which can use externally allocated memory.
			 */
			const size_t size = BKE_libblock_get_alloc_info(GS(newid->name), NULL);
			memcpy(id_cow, newid, size);
			done = true;
		}
	}
	if (!done) {
		BLI_assert(!"No idea how to perform CoW on datablock");
	}
	/* Update pointers to nested ID datablocks. */
	DEG_COW_PRINT("  Remapping ID links for %s: id_orig=%p id_cow=%p\n",
	              id_orig->name, id_orig, id_cow);

#ifdef NESTED_ID_NASTY_WORKAROUND
	ntree_hack_remap_pointers(depsgraph, id_cow);
#endif
	/* Do it now, so remapping will understand that possibly remapped self ID
	 * is not to be remapped again.
	 */
	deg_tag_copy_on_write_id(id_cow, id_orig);
	/* Perform remapping of the nodes. */
	RemapCallbackUserData user_data;
	user_data.depsgraph = depsgraph;
	user_data.temp_id = newid;
	user_data.real_id = id_cow;
	user_data.node_builder = node_builder;
	user_data.create_placeholders = create_placeholders;
	BKE_library_foreach_ID_link(NULL,
	                            id_cow,
	                            foreach_libblock_remap_callback,
	                            (void *)&user_data,
	                            IDWALK_NOP);
	/* Correct or tweak some pointers which are not taken care by foreach
	 * from above.
	 */
	update_special_pointers(depsgraph, id_orig, id_cow);
	/* Now we can safely discard temporary memory used for copying. */
	if (newid != NULL) {
		MEM_freeN(newid);
	}
	return id_cow;
}

/* NOTE: Depsgraph is supposed to have ID node already. */
ID *deg_expand_copy_on_write_datablock(const Depsgraph *depsgraph,
                                       ID *id_orig,
                                       DepsgraphNodeBuilder *node_builder,
                                       bool create_placeholders)
{
	DEG::IDDepsNode *id_node = depsgraph->find_id_node(id_orig);
	BLI_assert(id_node != NULL);
	return deg_expand_copy_on_write_datablock(depsgraph,
	                                          id_node,
	                                          node_builder,
	                                          create_placeholders);
}

ID *deg_update_copy_on_write_datablock(const Depsgraph *depsgraph,
                                       const IDDepsNode *id_node)
{
	const ID *id_orig = id_node->id_orig;
	const short id_type = GS(id_orig->name);
	ID *id_cow = id_node->id_cow;
	/* Similar to expansion, no need to do anything here. */
	if (!deg_copy_on_write_is_needed(id_orig)) {
		return id_cow;
	}
	/* Special case for datablocks which are expanded at the dependency graph
	 * construction time. This datablocks must never change pointers of their
	 * nested data since it is used for function bindings.
	 */
	if (check_datablock_expanded_at_construction(id_orig)) {
		BLI_assert(check_datablock_expanded(id_cow) == true);
		update_copy_on_write_datablock(depsgraph, id_orig, id_cow);
		return id_cow;
	}
	/* For the rest if datablock types we use simple logic:
	 * - Free previously expanded data, if any.
	 * - Perform full datablock copy.
	 *
	 * Note that we never free GPU materials from here since that's not
	 * safe for threading and GPU materials are likely to be re-used.
	 */
	ListBase gpumaterial_backup;
	ListBase *gpumaterial_ptr = NULL;
	Mesh *mesh_evaluated = NULL;
	if (check_datablock_expanded(id_cow)) {
		switch (id_type) {
			case ID_MA:
			{
				Material *material = (Material *)id_cow;
				gpumaterial_ptr = &material->gpumaterial;
				break;
			}
			case ID_WO:
			{
				World *world = (World *)id_cow;
				gpumaterial_ptr = &world->gpumaterial;
				break;
			}
			case ID_OB:
			{
				Object *object = (Object *)id_cow;
				/* Store evaluated mesh, make sure we don't free it. */
				mesh_evaluated = object->mesh_evaluated;
				object->mesh_evaluated = NULL;
				/* Currently object update will override actual object->data
				 * to an evaluated version. Need to make sure we don't have
				 * data set to evaluated one before free anything.
				 */
				if (mesh_evaluated != NULL) {
					if (object->data == mesh_evaluated) {
						object->data = mesh_evaluated->id.newid;
					}
				}
				break;
			}
		}
		if (gpumaterial_ptr != NULL) {
			gpumaterial_backup = *gpumaterial_ptr;
			gpumaterial_ptr->first = gpumaterial_ptr->last = NULL;
		}
	}
	deg_free_copy_on_write_datablock(id_cow);
	deg_expand_copy_on_write_datablock(depsgraph, id_node);
	/* Restore GPU materials. */
	if (gpumaterial_ptr != NULL) {
		*gpumaterial_ptr = gpumaterial_backup;
	}
	if (id_type == ID_OB) {
		if (mesh_evaluated != NULL) {
			Object *object = (Object *)id_cow;
			object->mesh_evaluated = mesh_evaluated;
			/* Do same thing as object update: override actual object data
			 * pointer with evaluated datablock.
			 */
			if (object->type == OB_MESH) {
				object->data = mesh_evaluated;
			}
		}
	}
	return id_cow;
}

/* NOTE: Depsgraph is supposed to have ID node already. */
ID *deg_update_copy_on_write_datablock(const Depsgraph *depsgraph,
                                       ID *id_orig)
{
	DEG::IDDepsNode *id_node = depsgraph->find_id_node(id_orig);
	BLI_assert(id_node != NULL);
	return deg_update_copy_on_write_datablock(depsgraph, id_node);
}

/* Free content of the CoW datablock
 * Notes:
 * - Does not recurs into nested ID datablocks.
 * - Does not free datablock itself.
 */
void deg_free_copy_on_write_datablock(ID *id_cow)
{
	if (!check_datablock_expanded(id_cow)) {
		/* Actual content was never copied on top of CoW block, we have
		 * nothing to free.
		 */
		return;
	}
	const short type = GS(id_cow->name);
#ifdef NESTED_ID_NASTY_WORKAROUND
	nested_id_hack_discard_pointers(id_cow);
#endif
	switch (type) {
		case ID_OB:
		{
			/* TODO(sergey): This workaround is only to prevent free derived
			 * caches from modifying object->data. This is currently happening
			 * due to mesh/curve datablock boundbox tagging dirty.
			 */
			Object *ob_cow = (Object *)id_cow;
			ob_cow->data = NULL;
			break;
		}
		case ID_ME:
		{
			Mesh *mesh_cow = (Mesh *)id_cow;
			if (mesh_cow->edit_btmesh != NULL) {
				BKE_editmesh_free_derivedmesh(mesh_cow->edit_btmesh);
				MEM_freeN(mesh_cow->edit_btmesh);
				mesh_cow->edit_btmesh = NULL;
			}
			break;
		}
		case ID_SCE:
		{
			/* Special case for scene: we use explicit function call which
			 * ensures no access to other datablocks is done.
			 */
			Scene *scene = (Scene *)id_cow;
			BKE_scene_free_ex(scene, false);
			BKE_libblock_free_data(id_cow, false);
			id_cow->name[0] = '\0';
			return;
		}
	}
	BKE_libblock_free_datablock(id_cow);
	BKE_libblock_free_data(id_cow, false);
	/* Signal datablock as not being expanded. */
	id_cow->name[0] = '\0';
}

void deg_evaluate_copy_on_write(const EvaluationContext * /*eval_ctx*/,
                                const Depsgraph *depsgraph,
                                const IDDepsNode *id_node)
{
	DEBUG_PRINT("%s on %s\n", __func__, id_node->id_orig->name);
	deg_update_copy_on_write_datablock(depsgraph, id_node);
}

bool deg_validate_copy_on_write_datablock(ID *id_cow)
{
	if (id_cow == NULL) {
		return false;
	}
	ValidateData data;
	data.is_valid = true;
	BKE_library_foreach_ID_link(NULL,
	                            id_cow,
	                            foreach_libblock_validate_callback,
	                            &data,
	                            IDWALK_NOP);
	return data.is_valid;
}

void deg_tag_copy_on_write_id(ID *id_cow, const ID *id_orig)
{
	id_cow->tag |= LIB_TAG_COPY_ON_WRITE;
	/* TODO(sergey): Is it safe to re-use newid for original ID link? */
	id_cow->newid = (ID *)id_orig;
}

bool deg_copy_on_write_is_expanded(const ID *id_cow)
{
	return check_datablock_expanded(id_cow);
}

bool deg_copy_on_write_is_needed(const ID *id_orig)
{
	const short id_type = GS(id_orig->name);
	return !ELEM(id_type, ID_IM);
}

}  // namespace DEG
