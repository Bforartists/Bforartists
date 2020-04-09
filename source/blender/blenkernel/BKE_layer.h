/*
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
 */

#ifndef __BKE_LAYER_H__
#define __BKE_LAYER_H__

/** \file
 * \ingroup bke
 */

#include "BKE_collection.h"

#include "DNA_listBase.h"
#include "DNA_scene_types.h"

#ifdef __cplusplus
extern "C" {
#endif

#define TODO_LAYER_OVERRIDE  /* CollectionOverride */
#define TODO_LAYER_OPERATORS /* collection mamanger and property panel operators */
#define TODO_LAYER           /* generic todo */

struct Base;
struct Collection;
struct Depsgraph;
struct LayerCollection;
struct Main;
struct Object;
struct Scene;
struct View3D;
struct ViewLayer;

typedef enum eViewLayerCopyMethod {
  VIEWLAYER_ADD_NEW = 0,
  VIEWLAYER_ADD_EMPTY = 1,
  VIEWLAYER_ADD_COPY = 2,
} eViewLayerCopyMethod;

struct ViewLayer *BKE_view_layer_default_view(const struct Scene *scene);
struct ViewLayer *BKE_view_layer_default_render(const struct Scene *scene);
struct ViewLayer *BKE_view_layer_find(const struct Scene *scene, const char *layer_name);
struct ViewLayer *BKE_view_layer_add(Scene *scene,
                                     const char *name,
                                     ViewLayer *view_layer_source,
                                     const int type);

/* DEPRECATED */
struct ViewLayer *BKE_view_layer_context_active_PLACEHOLDER(const struct Scene *scene);

void BKE_view_layer_free(struct ViewLayer *view_layer);
void BKE_view_layer_free_ex(struct ViewLayer *view_layer, const bool do_id_user);

void BKE_view_layer_selected_objects_tag(struct ViewLayer *view_layer, const int tag);

struct Object *BKE_view_layer_camera_find(struct ViewLayer *view_layer);
struct ViewLayer *BKE_view_layer_find_from_collection(const struct Scene *scene,
                                                      struct LayerCollection *lc);
struct Base *BKE_view_layer_base_find(struct ViewLayer *view_layer, struct Object *ob);
void BKE_view_layer_base_deselect_all(struct ViewLayer *view_layer);

void BKE_view_layer_base_select_and_set_active(struct ViewLayer *view_layer, struct Base *selbase);

void BKE_view_layer_copy_data(struct Scene *scene_dst,
                              const struct Scene *scene_src,
                              struct ViewLayer *view_layer_dst,
                              const struct ViewLayer *view_layer_src,
                              const int flag);

void BKE_view_layer_rename(struct Main *bmain,
                           struct Scene *scene,
                           struct ViewLayer *view_layer,
                           const char *name);

struct LayerCollection *BKE_layer_collection_get_active(struct ViewLayer *view_layer);
bool BKE_layer_collection_activate(struct ViewLayer *view_layer, struct LayerCollection *lc);
struct LayerCollection *BKE_layer_collection_activate_parent(struct ViewLayer *view_layer,
                                                             struct LayerCollection *lc);

int BKE_layer_collection_count(struct ViewLayer *view_layer);

struct LayerCollection *BKE_layer_collection_from_index(struct ViewLayer *view_layer,
                                                        const int index);
int BKE_layer_collection_findindex(struct ViewLayer *view_layer, const struct LayerCollection *lc);

void BKE_main_collection_sync(const struct Main *bmain);
void BKE_scene_collection_sync(const struct Scene *scene);
void BKE_layer_collection_sync(const struct Scene *scene, struct ViewLayer *view_layer);
void BKE_layer_collection_local_sync(struct ViewLayer *view_layer, struct View3D *v3d);

void BKE_main_collection_sync_remap(const struct Main *bmain);

struct LayerCollection *BKE_layer_collection_first_from_scene_collection(
    struct ViewLayer *view_layer, const struct Collection *collection);
bool BKE_view_layer_has_collection(struct ViewLayer *view_layer,
                                   const struct Collection *collection);
bool BKE_scene_has_object(struct Scene *scene, struct Object *ob);

/* selection and hiding */

bool BKE_layer_collection_objects_select(struct ViewLayer *view_layer,
                                         struct LayerCollection *lc,
                                         bool deselect);
bool BKE_layer_collection_has_selected_objects(struct ViewLayer *view_layer,
                                               struct LayerCollection *lc);
bool BKE_layer_collection_has_layer_collection(struct LayerCollection *lc_parent,
                                               struct LayerCollection *lc_child);

void BKE_base_set_visible(struct Scene *scene,
                          struct ViewLayer *view_layer,
                          struct Base *base,
                          bool extend);
bool BKE_base_is_visible(const struct View3D *v3d, const struct Base *base);
bool BKE_object_is_visible_in_viewport(const struct View3D *v3d, const struct Object *ob);
void BKE_layer_collection_isolate_global(struct Scene *scene,
                                         struct ViewLayer *view_layer,
                                         struct LayerCollection *lc,
                                         bool extend);
void BKE_layer_collection_isolate_local(struct ViewLayer *view_layer,
                                        struct View3D *v3d,
                                        struct LayerCollection *lc,
                                        bool extend);
void BKE_layer_collection_set_visible(struct ViewLayer *view_layer,
                                      struct LayerCollection *lc,
                                      const bool visible,
                                      const bool hierarchy);
void BKE_layer_collection_set_flag(struct LayerCollection *lc, const int flag, const bool value);

/* evaluation */

void BKE_base_eval_flags(struct Base *base);

void BKE_layer_eval_view_layer_indexed(struct Depsgraph *depsgraph,
                                       struct Scene *scene,
                                       int view_layer_index);

/* iterators */

typedef struct ObjectsVisibleIteratorData {
  struct ViewLayer *view_layer;
  struct View3D *v3d;
} ObjectsVisibleIteratorData;

void BKE_view_layer_selected_objects_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_view_layer_selected_objects_iterator_next(BLI_Iterator *iter);
void BKE_view_layer_selected_objects_iterator_end(BLI_Iterator *iter);

void BKE_view_layer_visible_objects_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_view_layer_visible_objects_iterator_next(BLI_Iterator *iter);
void BKE_view_layer_visible_objects_iterator_end(BLI_Iterator *iter);

void BKE_view_layer_selected_editable_objects_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_view_layer_selected_editable_objects_iterator_next(BLI_Iterator *iter);
void BKE_view_layer_selected_editable_objects_iterator_end(BLI_Iterator *iter);

struct ObjectsInModeIteratorData {
  int object_mode;
  int object_type;
  struct ViewLayer *view_layer;
  struct View3D *v3d;
  struct Base *base_active;
};

void BKE_view_layer_bases_in_mode_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_view_layer_bases_in_mode_iterator_next(BLI_Iterator *iter);
void BKE_view_layer_bases_in_mode_iterator_end(BLI_Iterator *iter);

void BKE_view_layer_selected_bases_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_view_layer_selected_bases_iterator_next(BLI_Iterator *iter);
void BKE_view_layer_selected_bases_iterator_end(BLI_Iterator *iter);

void BKE_view_layer_visible_bases_iterator_begin(BLI_Iterator *iter, void *data_in);
void BKE_view_layer_visible_bases_iterator_next(BLI_Iterator *iter);
void BKE_view_layer_visible_bases_iterator_end(BLI_Iterator *iter);

#define FOREACH_SELECTED_OBJECT_BEGIN(_view_layer, _v3d, _instance) \
  { \
    struct ObjectsVisibleIteratorData data_ = { \
        .view_layer = _view_layer, \
        .v3d = _v3d, \
    }; \
    ITER_BEGIN (BKE_view_layer_selected_objects_iterator_begin, \
                BKE_view_layer_selected_objects_iterator_next, \
                BKE_view_layer_selected_objects_iterator_end, \
                &data_, \
                Object *, \
                _instance)

#define FOREACH_SELECTED_OBJECT_END \
  ITER_END; \
  } \
  ((void)0)

#define FOREACH_SELECTED_EDITABLE_OBJECT_BEGIN(_view_layer, _v3d, _instance) \
  { \
    struct ObjectsVisibleIteratorData data_ = { \
        .view_layer = _view_layer, \
        .v3d = _v3d, \
    }; \
    ITER_BEGIN (BKE_view_layer_selected_editable_objects_iterator_begin, \
                BKE_view_layer_selected_editable_objects_iterator_next, \
                BKE_view_layer_selected_editable_objects_iterator_end, \
                &data_, \
                Object *, \
                _instance)

#define FOREACH_SELECTED_EDITABLE_OBJECT_END \
  ITER_END; \
  } \
  ((void)0)

#define FOREACH_VISIBLE_OBJECT_BEGIN(_view_layer, _v3d, _instance) \
  { \
    struct ObjectsVisibleIteratorData data_ = { \
        .view_layer = _view_layer, \
        .v3d = _v3d, \
    }; \
    ITER_BEGIN (BKE_view_layer_visible_objects_iterator_begin, \
                BKE_view_layer_visible_objects_iterator_next, \
                BKE_view_layer_visible_objects_iterator_end, \
                &data_, \
                Object *, \
                _instance)

#define FOREACH_VISIBLE_OBJECT_END \
  ITER_END; \
  } \
  ((void)0)

#define FOREACH_BASE_IN_MODE_BEGIN(_view_layer, _v3d, _object_type, _object_mode, _instance) \
  { \
    struct ObjectsInModeIteratorData data_ = { \
        .object_mode = _object_mode, \
        .object_type = _object_type, \
        .view_layer = _view_layer, \
        .v3d = _v3d, \
        .base_active = _view_layer->basact, \
    }; \
    ITER_BEGIN (BKE_view_layer_bases_in_mode_iterator_begin, \
                BKE_view_layer_bases_in_mode_iterator_next, \
                BKE_view_layer_bases_in_mode_iterator_end, \
                &data_, \
                Base *, \
                _instance)

#define FOREACH_BASE_IN_MODE_END \
  ITER_END; \
  } \
  ((void)0)

#define FOREACH_BASE_IN_EDIT_MODE_BEGIN(_view_layer, _v3d, _instance) \
  FOREACH_BASE_IN_MODE_BEGIN (_view_layer, _v3d, -1, OB_MODE_EDIT, _instance)

#define FOREACH_BASE_IN_EDIT_MODE_END FOREACH_BASE_IN_MODE_END

#define FOREACH_OBJECT_IN_MODE_BEGIN(_view_layer, _v3d, _object_type, _object_mode, _instance) \
  FOREACH_BASE_IN_MODE_BEGIN (_view_layer, _v3d, _object_type, _object_mode, _base) { \
    Object *_instance = _base->object;

#define FOREACH_OBJECT_IN_MODE_END \
  } \
  FOREACH_BASE_IN_MODE_END

#define FOREACH_OBJECT_IN_EDIT_MODE_BEGIN(_view_layer, _v3d, _instance) \
  FOREACH_BASE_IN_EDIT_MODE_BEGIN (_view_layer, _v3d, _base) { \
    Object *_instance = _base->object;

#define FOREACH_OBJECT_IN_EDIT_MODE_END \
  } \
  FOREACH_BASE_IN_EDIT_MODE_END

#define FOREACH_SELECTED_BASE_BEGIN(view_layer, _instance) \
  ITER_BEGIN (BKE_view_layer_selected_bases_iterator_begin, \
              BKE_view_layer_selected_bases_iterator_next, \
              BKE_view_layer_selected_bases_iterator_end, \
              view_layer, \
              Base *, \
              _instance)

#define FOREACH_SELECTED_BASE_END ITER_END

#define FOREACH_VISIBLE_BASE_BEGIN(_view_layer, _v3d, _instance) \
  { \
    struct ObjectsVisibleIteratorData data_ = { \
        .view_layer = _view_layer, \
        .v3d = _v3d, \
    }; \
    ITER_BEGIN (BKE_view_layer_visible_bases_iterator_begin, \
                BKE_view_layer_visible_bases_iterator_next, \
                BKE_view_layer_visible_bases_iterator_end, \
                &data_, \
                Base *, \
                _instance)

#define FOREACH_VISIBLE_BASE_END \
  ITER_END; \
  } \
  ((void)0)

#define FOREACH_OBJECT_BEGIN(view_layer, _instance) \
  { \
    Object *_instance; \
    Base *_base; \
    for (_base = (view_layer)->object_bases.first; _base; _base = _base->next) { \
      _instance = _base->object;

#define FOREACH_OBJECT_END \
  } \
  } \
  ((void)0)

#define FOREACH_OBJECT_FLAG_BEGIN(scene, _view_layer, _v3d, flag, _instance) \
  { \
    IteratorBeginCb func_begin; \
    IteratorCb func_next, func_end; \
    void *data_in; \
    struct ObjectsVisibleIteratorData data_ = { \
        .view_layer = _view_layer, \
        .v3d = _v3d, \
    }; \
\
    if (flag == SELECT) { \
      func_begin = &BKE_view_layer_selected_objects_iterator_begin; \
      func_next = &BKE_view_layer_selected_objects_iterator_next; \
      func_end = &BKE_view_layer_selected_objects_iterator_end; \
      data_in = &data_; \
    } \
    else { \
      func_begin = BKE_scene_objects_iterator_begin; \
      func_next = BKE_scene_objects_iterator_next; \
      func_end = BKE_scene_objects_iterator_end; \
      data_in = (scene); \
    } \
    ITER_BEGIN (func_begin, func_next, func_end, data_in, Object *, _instance)

#define FOREACH_OBJECT_FLAG_END \
  ITER_END; \
  } \
  ((void)0)

/* layer_utils.c */

struct ObjectsInModeParams {
  int object_mode;
  uint no_dup_data : 1;

  bool (*filter_fn)(struct Object *ob, void *user_data);
  void *filter_userdata;
};

Base **BKE_view_layer_array_from_bases_in_mode_params(struct ViewLayer *view_layer,
                                                      struct View3D *v3d,
                                                      uint *r_len,
                                                      const struct ObjectsInModeParams *params);

struct Object **BKE_view_layer_array_from_objects_in_mode_params(
    struct ViewLayer *view_layer,
    struct View3D *v3d,
    uint *len,
    const struct ObjectsInModeParams *params);

#define BKE_view_layer_array_from_objects_in_mode(view_layer, v3d, r_len, ...) \
  BKE_view_layer_array_from_objects_in_mode_params( \
      view_layer, v3d, r_len, &(const struct ObjectsInModeParams)__VA_ARGS__)

#define BKE_view_layer_array_from_bases_in_mode(view_layer, v3d, r_len, ...) \
  BKE_view_layer_array_from_bases_in_mode_params( \
      view_layer, v3d, r_len, &(const struct ObjectsInModeParams)__VA_ARGS__)

bool BKE_view_layer_filter_edit_mesh_has_uvs(struct Object *ob, void *user_data);
bool BKE_view_layer_filter_edit_mesh_has_edges(struct Object *ob, void *user_data);

/* Utility macros that wrap common args (add more as needed). */

#define BKE_view_layer_array_from_objects_in_edit_mode(view_layer, v3d, r_len) \
  BKE_view_layer_array_from_objects_in_mode(view_layer, v3d, r_len, {.object_mode = OB_MODE_EDIT})

#define BKE_view_layer_array_from_bases_in_edit_mode(view_layer, v3d, r_len) \
  BKE_view_layer_array_from_bases_in_mode(view_layer, v3d, r_len, {.object_mode = OB_MODE_EDIT})

#define BKE_view_layer_array_from_objects_in_edit_mode_unique_data(view_layer, v3d, r_len) \
  BKE_view_layer_array_from_objects_in_mode( \
      view_layer, v3d, r_len, {.object_mode = OB_MODE_EDIT, .no_dup_data = true})

#define BKE_view_layer_array_from_bases_in_edit_mode_unique_data(view_layer, v3d, r_len) \
  BKE_view_layer_array_from_bases_in_mode( \
      view_layer, v3d, r_len, {.object_mode = OB_MODE_EDIT, .no_dup_data = true})

#define BKE_view_layer_array_from_objects_in_edit_mode_unique_data_with_uvs( \
    view_layer, v3d, r_len) \
  BKE_view_layer_array_from_objects_in_mode( \
      view_layer, \
      v3d, \
      r_len, \
      {.object_mode = OB_MODE_EDIT, \
       .no_dup_data = true, \
       .filter_fn = BKE_view_layer_filter_edit_mesh_has_uvs})

#define BKE_view_layer_array_from_objects_in_mode_unique_data(view_layer, v3d, r_len, mode) \
  BKE_view_layer_array_from_objects_in_mode( \
      view_layer, v3d, r_len, {.object_mode = mode, .no_dup_data = true})

#ifdef __cplusplus
}
#endif

#endif /* __BKE_LAYER_H__ */
