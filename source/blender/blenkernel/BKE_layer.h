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
 * Contributor(s): Blender Foundation, Dalai Felinto
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef __BKE_LAYER_H__
#define __BKE_LAYER_H__

/** \file blender/blenkernel/BKE_layer.h
 *  \ingroup bke
 */

#include "BKE_collection.h"

#include "DNA_scene_types.h"

#ifdef __cplusplus
extern "C" {
#endif

#define TODO_LAYER_OVERRIDE /* CollectionOverride */
#define TODO_LAYER_OPERATORS /* collection mamanger and property panel operators */
#define TODO_LAYER /* generic todo */

#define ROOT_PROP "root"

struct Base;
struct EvaluationContext;
struct Group;
struct ID;
struct IDProperty;
struct LayerCollection;
struct ListBase;
struct Main;
struct Object;
struct RenderEngine;
struct Scene;
struct SceneCollection;
struct ViewLayer;
struct WorkSpace;

void BKE_layer_exit(void);

struct ViewLayer *BKE_view_layer_from_scene_get(const struct Scene *scene);
struct ViewLayer *BKE_view_layer_from_workspace_get(const struct Scene *scene, const struct WorkSpace *workspace);
struct ViewLayer *BKE_view_layer_add(struct Scene *scene, const char *name);
struct ViewLayer *BKE_view_layer_group_add(struct Group *group);

/* DEPRECATED */
struct ViewLayer *BKE_view_layer_context_active_PLACEHOLDER(const struct Scene *scene);

void BKE_view_layer_free(struct ViewLayer *view_layer);
void BKE_view_layer_free_ex(struct ViewLayer *view_layer, const bool do_id_user);

void BKE_view_layer_selected_objects_tag(struct ViewLayer *view_layer, const int tag);

struct Object *BKE_view_layer_camera_find(struct ViewLayer *view_layer);
struct ViewLayer *BKE_view_layer_first_from_id(const struct ID *owner_id);
struct ViewLayer *BKE_view_layer_find_from_collection(const struct ID *owner_id, struct LayerCollection *lc);
struct Base *BKE_view_layer_base_find(struct ViewLayer *view_layer, struct Object *ob);
void BKE_view_layer_base_deselect_all(struct ViewLayer *view_layer);
void BKE_view_layer_base_select(struct ViewLayer *view_layer, struct Base *selbase);

void BKE_layer_collection_sync_flags(
        struct ID *owner_id,
        struct SceneCollection *scene_collection_dst,
        struct SceneCollection *scene_collection_src);

void BKE_view_layer_copy_data(
        struct ViewLayer *view_layer_dst, struct ViewLayer *view_layer_src,
        struct SceneCollection *mc_dst, struct SceneCollection *mc_src,
        const int flag);

struct LayerCollection *BKE_layer_collection_duplicate(struct ID *owner_id, struct LayerCollection *layer_collection);

void BKE_layer_collection_free(struct ViewLayer *view_layer, struct LayerCollection *lc);

struct LayerCollection *BKE_layer_collection_get_active(struct ViewLayer *view_layer);
struct LayerCollection *BKE_layer_collection_get_active_ensure(struct Scene *scene, struct ViewLayer *view_layer);

int BKE_layer_collection_count(struct ViewLayer *view_layer);

struct LayerCollection *BKE_layer_collection_from_index(struct ViewLayer *view_layer, const int index);
int BKE_layer_collection_findindex(struct ViewLayer *view_layer, const struct LayerCollection *lc);

bool BKE_layer_collection_move_above(const struct ID *owner_id, struct LayerCollection *lc_dst, struct LayerCollection *lc_src);
bool BKE_layer_collection_move_below(const struct ID *owner_id, struct LayerCollection *lc_dst, struct LayerCollection *lc_src);
bool BKE_layer_collection_move_into(const struct ID *owner_id, struct LayerCollection *lc_dst, struct LayerCollection *lc_src);

void BKE_layer_collection_resync(const struct ID *owner_id, const struct SceneCollection *sc);

struct LayerCollection *BKE_collection_link(struct ViewLayer *view_layer, struct SceneCollection *sc);

void BKE_collection_unlink(struct ViewLayer *view_layer, struct LayerCollection *lc);

void BKE_collection_enable(struct ViewLayer *view_layer, struct LayerCollection *lc);

bool BKE_view_layer_has_collection(struct ViewLayer *view_layer, const struct SceneCollection *sc);
bool BKE_scene_has_object(struct Scene *scene, struct Object *ob);

void BKE_layer_collection_objects_select(struct LayerCollection *layer_collection);

/* syncing */

void BKE_layer_sync_new_scene_collection(struct ID *owner_id, const struct SceneCollection *sc_parent, struct SceneCollection *sc);
void BKE_layer_sync_object_link(const struct ID *owner_id, struct SceneCollection *sc, struct Object *ob);
void BKE_layer_sync_object_unlink(const struct ID *owner_id, struct SceneCollection *sc, struct Object *ob);

/* override */

void BKE_override_view_layer_datablock_add(struct ViewLayer *view_layer, int id_type, const char *data_path, const struct ID *owner_id);
void BKE_override_view_layer_int_add(struct ViewLayer *view_layer, int id_type, const char *data_path, const int value);

void BKE_override_layer_collection_boolean_add(struct LayerCollection *layer_collection, int id_type, const char *data_path, const bool value);

/* engine settings */
typedef void (*EngineSettingsCB)(struct RenderEngine *engine, struct IDProperty *props);

struct IDProperty *BKE_layer_collection_engine_evaluated_get(struct Object *ob, const int type, const char *engine_name);
struct IDProperty *BKE_layer_collection_engine_collection_get(struct LayerCollection *lc, const int type, const char *engine_name);
struct IDProperty *BKE_layer_collection_engine_scene_get(struct Scene *scene, const int type, const char *engine_name);
void BKE_layer_collection_engine_settings_callback_register(struct Main *bmain, const char *engine_name, EngineSettingsCB func);
void BKE_layer_collection_engine_settings_callback_free(void);
void BKE_layer_collection_engine_settings_create(struct IDProperty *root);
void BKE_layer_collection_engine_settings_validate_scene(struct Scene *scene);
void BKE_layer_collection_engine_settings_validate_collection(struct LayerCollection *lc);

struct IDProperty *BKE_view_layer_engine_evaluated_get(struct ViewLayer *view_layer, const int type, const char *engine_name);
struct IDProperty *BKE_view_layer_engine_layer_get(struct ViewLayer *view_layer, const int type, const char *engine_name);
struct IDProperty *BKE_view_layer_engine_scene_get(struct Scene *scene, const int type, const char *engine_name);
void BKE_view_layer_engine_settings_callback_register(struct Main *bmain, const char *engine_name, EngineSettingsCB func);
void BKE_view_layer_engine_settings_callback_free(void);
void BKE_view_layer_engine_settings_validate_scene(struct Scene *scene);
void BKE_view_layer_engine_settings_validate_layer(struct ViewLayer *view_layer);
void BKE_view_layer_engine_settings_create(struct IDProperty *root);

void BKE_collection_engine_property_add_float(struct IDProperty *props, const char *name, float value);
void BKE_collection_engine_property_add_float_array(
        struct IDProperty *props, const char *name, const float *values, const int array_length);
void BKE_collection_engine_property_add_int(struct IDProperty *props, const char *name, int value);
void BKE_collection_engine_property_add_bool(struct IDProperty *props, const char *name, bool value);

int BKE_collection_engine_property_value_get_int(struct IDProperty *props, const char *name);
float BKE_collection_engine_property_value_get_float(struct IDProperty *props, const char *name);
const float *BKE_collection_engine_property_value_get_float_array(struct IDProperty *props, const char *name);
bool BKE_collection_engine_property_value_get_bool(struct IDProperty *props, const char *name);
void BKE_collection_engine_property_value_set_int(struct IDProperty *props, const char *name, int value);
void BKE_collection_engine_property_value_set_float(struct IDProperty *props, const char *name, float value);
void BKE_collection_engine_property_value_set_float_array(struct IDProperty *props, const char *name, const float *values);
void BKE_collection_engine_property_value_set_bool(struct IDProperty *props, const char *name, bool value);

/* evaluation */

void BKE_layer_eval_layer_collection_pre(const struct EvaluationContext *eval_ctx,
                                         struct ID *owner_id,
                                         struct ViewLayer *view_layer);
void BKE_layer_eval_layer_collection(const struct EvaluationContext *eval_ctx,
                                     struct LayerCollection *layer_collection,
                                     struct LayerCollection *parent_layer_collection);
void BKE_layer_eval_layer_collection_post(const struct EvaluationContext *eval_ctx,
                                          struct ViewLayer *view_layer);

/* iterators */

void BKE_selected_objects_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_selected_objects_iterator_next(BLI_Iterator *iter);
void BKE_selected_objects_iterator_end(BLI_Iterator *iter);

void BKE_visible_objects_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_visible_objects_iterator_next(BLI_Iterator *iter);
void BKE_visible_objects_iterator_end(BLI_Iterator *iter);

void BKE_renderable_objects_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_renderable_objects_iterator_next(BLI_Iterator *iter);
void BKE_renderable_objects_iterator_end(BLI_Iterator *iter);

void BKE_selected_bases_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_selected_bases_iterator_next(BLI_Iterator *iter);
void BKE_selected_bases_iterator_end(BLI_Iterator *iter);

void BKE_visible_bases_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_visible_bases_iterator_next(BLI_Iterator *iter);
void BKE_visible_bases_iterator_end(BLI_Iterator *iter);

#define FOREACH_SELECTED_OBJECT(view_layer, _instance)                        \
	ITER_BEGIN(BKE_selected_objects_iterator_begin,                           \
	           BKE_selected_objects_iterator_next,                            \
	           BKE_selected_objects_iterator_end,                             \
	           view_layer, Object *, _instance)

#define FOREACH_SELECTED_OBJECT_END                                           \
	ITER_END

#define FOREACH_VISIBLE_OBJECT(view_layer, _instance)                         \
	ITER_BEGIN(BKE_visible_objects_iterator_begin,                            \
	           BKE_visible_objects_iterator_next,                             \
	           BKE_visible_objects_iterator_end,                              \
	           view_layer, Object *, _instance)

#define FOREACH_VISIBLE_OBJECT_END                                            \
	ITER_END

#define FOREACH_SELECTED_BASE(view_layer, _instance)                           \
	ITER_BEGIN(BKE_selected_bases_iterator_begin,                              \
	           BKE_selected_bases_iterator_next,                               \
	           BKE_selected_bases_iterator_end,                                \
	           view_layer, Base *, _instance)

#define FOREACH_SELECTED_BASE_END                                              \
	ITER_END

#define FOREACH_VISIBLE_BASE(view_layer, _instance)                           \
	ITER_BEGIN(BKE_visible_bases_iterator_begin,                              \
	           BKE_visible_bases_iterator_next,                               \
	           BKE_visible_bases_iterator_end,                                \
	           view_layer, Base *, _instance)

#define FOREACH_VISIBLE_BASE_END                                              \
	ITER_END


#define FOREACH_OBJECT(view_layer, _instance)                                 \
{                                                                             \
	Object *_instance;                                                        \
	Base *_base;                                                              \
	for (_base = (view_layer)->object_bases.first; _base; _base = _base->next) { \
		_instance = _base->object;

#define FOREACH_OBJECT_END                                                    \
    }                                                                         \
}

#define FOREACH_OBJECT_FLAG(scene, view_layer, flag, _instance)               \
{                                                                             \
	IteratorBeginCb func_begin;                                               \
	IteratorCb func_next, func_end;                                           \
	void *data_in;                                                            \
	                                                                          \
	if (flag == SELECT) {                                                     \
	    func_begin = &BKE_selected_objects_iterator_begin;                    \
	    func_next = &BKE_selected_objects_iterator_next;                      \
	    func_end = &BKE_selected_objects_iterator_end;                        \
	    data_in = (view_layer);                                               \
	}                                                                         \
	else {                                                                    \
	    func_begin = BKE_scene_objects_iterator_begin;                        \
	    func_next = BKE_scene_objects_iterator_next;                          \
	    func_end = BKE_scene_objects_iterator_end;                            \
	    data_in = (scene);                                                    \
	}                                                                         \
	ITER_BEGIN(func_begin, func_next, func_end, data_in, Object *, _instance)


#define FOREACH_OBJECT_FLAG_END                                               \
	ITER_END                                                                  \
}

typedef struct ObjectsRenderableIteratorData {
	struct Scene *scene;
	struct Base base_temp;
	struct Scene scene_temp;

	struct {
		struct ViewLayer *view_layer;
		struct Base *base;
		struct Scene *set;
	} iter;
} ObjectsRenderableIteratorData;

#define FOREACH_OBJECT_RENDERABLE(scene_, _instance)                          \
	ObjectsRenderableIteratorData data_ = {                                   \
	    .scene = (scene_),                                                    \
	};                                                                        \
	ITER_BEGIN(BKE_renderable_objects_iterator_begin,                         \
	           BKE_renderable_objects_iterator_next,                          \
	           BKE_renderable_objects_iterator_end,                           \
	           &data_, Object *, _instance)


#define FOREACH_OBJECT_RENDERABLE_END                                         \
	ITER_END

#ifdef __cplusplus
}
#endif

#endif /* __BKE_LAYER_H__ */
