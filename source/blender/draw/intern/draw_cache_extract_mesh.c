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
 *
 * The Original Code is Copyright (C) 2017 by Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup draw
 *
 * \brief Extraction of Mesh data into VBO to feed to GPU.
 */
#include "MEM_guardedalloc.h"

#include "atomic_ops.h"

#include "DNA_mesh_types.h"
#include "DNA_scene_types.h"

#include "BLI_task.h"

#include "BKE_editmesh.h"

#include "GPU_capabilities.h"

#include "draw_cache_extract.h"
#include "draw_cache_extract_mesh_private.h"
#include "draw_cache_inline.h"

// #define DEBUG_TIME

#ifdef DEBUG_TIME
#  include "PIL_time_utildefines.h"
#endif

#define CHUNK_SIZE 8192

/* ---------------------------------------------------------------------- */
/** \name Mesh Elements Extract Struct
 * \{ */

typedef struct MeshExtractRunData {
  const MeshExtract *extractor;
  void *buffer;
  void *user_data;
} MeshExtractRunData;

typedef struct MeshExtractRunDataArray {
  int len;
  MeshExtractRunData items[M_EXTRACT_LEN];
} MeshExtractRunDataArray;

static void mesh_extract_run_data_array_init(MeshExtractRunDataArray *array)
{
  array->len = 0;
}

static void mesh_extract_run_data_array_add_ex(MeshExtractRunDataArray *array,
                                               const MeshExtractRunData *run_data)
{
  array->items[array->len] = *run_data;
  array->len++;
}

static void mesh_extract_run_data_array_add(MeshExtractRunDataArray *array,
                                            const MeshExtract *extractor)
{
  MeshExtractRunData run_data;
  run_data.extractor = extractor;
  run_data.buffer = NULL;
  run_data.user_data = NULL;
  mesh_extract_run_data_array_add_ex(array, &run_data);
}

static void mesh_extract_run_data_array_filter_iter_type(const MeshExtractRunDataArray *src,
                                                         MeshExtractRunDataArray *dst,
                                                         eMRIterType iter_type)
{
  for (int i = 0; i < src->len; i++) {

    const MeshExtractRunData *data = &src->items[i];
    const MeshExtract *extractor = data->extractor;
    if ((iter_type & MR_ITER_LOOPTRI) && extractor->iter_looptri_bm) {
      BLI_assert(extractor->iter_looptri_mesh);
      mesh_extract_run_data_array_add_ex(dst, data);
      continue;
    }
    if ((iter_type & MR_ITER_POLY) && extractor->iter_poly_bm) {
      BLI_assert(extractor->iter_poly_mesh);
      mesh_extract_run_data_array_add_ex(dst, data);
      continue;
    }
    if ((iter_type & MR_ITER_LEDGE) && extractor->iter_ledge_bm) {
      BLI_assert(extractor->iter_ledge_mesh);
      mesh_extract_run_data_array_add_ex(dst, data);
      continue;
    }
    if ((iter_type & MR_ITER_LVERT) && extractor->iter_lvert_bm) {
      BLI_assert(extractor->iter_lvert_mesh);
      mesh_extract_run_data_array_add_ex(dst, data);
      continue;
    }
  }
}

static void mesh_extract_run_data_array_filter_threading(
    const MeshExtractRunDataArray *src, MeshExtractRunDataArray *dst_multi_threaded)
{
  for (int i = 0; i < src->len; i++) {
    const MeshExtract *extractor = src->items[i].extractor;
    if (extractor->use_threading) {
      mesh_extract_run_data_array_add(dst_multi_threaded, extractor);
    }
  }
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Extract
 * \{ */

static void extracts_flags_get(const MeshExtractRunDataArray *extractors,
                               eMRIterType *r_iter_type,
                               eMRDataType *r_data_flag)
{
  eMRIterType iter_type = 0;
  eMRDataType data_flag = 0;

  for (int i = 0; i < extractors->len; i++) {
    const MeshExtract *extractor = extractors->items[i].extractor;
    iter_type |= mesh_extract_iter_type(extractor);
    data_flag |= extractor->data_flag;
  }

  if (r_iter_type) {
    *r_iter_type = iter_type;
  }
  if (r_data_flag) {
    *r_data_flag = data_flag;
  }
}

BLI_INLINE void extract_init(const MeshRenderData *mr,
                             struct MeshBatchCache *cache,
                             MeshExtractRunDataArray *extractors,
                             MeshBufferCache *mbc)
{
  /* Multi thread. */
  for (int i = 0; i < extractors->len; i++) {
    MeshExtractRunData *run_data = &extractors->items[i];
    const MeshExtract *extractor = run_data->extractor;
    run_data->buffer = mesh_extract_buffer_get(extractor, mbc);
    run_data->user_data = extractor->init(mr, cache, run_data->buffer);
  }
}

BLI_INLINE void extract_iter_looptri_bm(const MeshRenderData *mr,
                                        const ExtractTriBMesh_Params *params,
                                        const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_LOOPTRI);

  EXTRACT_TRIS_LOOPTRI_FOREACH_BM_BEGIN(elt, elt_index, params)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_looptri_bm(mr, elt, elt_index, run_data->user_data);
    }
  }
  EXTRACT_TRIS_LOOPTRI_FOREACH_BM_END;
}

BLI_INLINE void extract_iter_looptri_mesh(const MeshRenderData *mr,
                                          const ExtractTriMesh_Params *params,
                                          const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_LOOPTRI);

  EXTRACT_TRIS_LOOPTRI_FOREACH_MESH_BEGIN(mlt, mlt_index, params)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_looptri_mesh(mr, mlt, mlt_index, run_data->user_data);
    }
  }
  EXTRACT_TRIS_LOOPTRI_FOREACH_MESH_END;
}

BLI_INLINE void extract_iter_poly_bm(const MeshRenderData *mr,
                                     const ExtractPolyBMesh_Params *params,
                                     const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_POLY);

  EXTRACT_POLY_FOREACH_BM_BEGIN(f, f_index, params, mr)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_poly_bm(mr, f, f_index, run_data->user_data);
    }
  }
  EXTRACT_POLY_FOREACH_BM_END;
}

BLI_INLINE void extract_iter_poly_mesh(const MeshRenderData *mr,
                                       const ExtractPolyMesh_Params *params,
                                       const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_POLY);

  EXTRACT_POLY_FOREACH_MESH_BEGIN(mp, mp_index, params, mr)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_poly_mesh(mr, mp, mp_index, run_data->user_data);
    }
  }
  EXTRACT_POLY_FOREACH_MESH_END;
}

BLI_INLINE void extract_iter_ledge_bm(const MeshRenderData *mr,
                                      const ExtractLEdgeBMesh_Params *params,
                                      const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_LEDGE);

  EXTRACT_LEDGE_FOREACH_BM_BEGIN(eed, ledge_index, params)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_ledge_bm(mr, eed, ledge_index, run_data->user_data);
    }
  }
  EXTRACT_LEDGE_FOREACH_BM_END;
}

BLI_INLINE void extract_iter_ledge_mesh(const MeshRenderData *mr,
                                        const ExtractLEdgeMesh_Params *params,
                                        const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_LEDGE);

  EXTRACT_LEDGE_FOREACH_MESH_BEGIN(med, ledge_index, params, mr)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_ledge_mesh(mr, med, ledge_index, run_data->user_data);
    }
  }
  EXTRACT_LEDGE_FOREACH_MESH_END;
}

BLI_INLINE void extract_iter_lvert_bm(const MeshRenderData *mr,
                                      const ExtractLVertBMesh_Params *params,
                                      const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_LVERT);

  EXTRACT_LVERT_FOREACH_BM_BEGIN(eve, lvert_index, params)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_lvert_bm(mr, eve, lvert_index, run_data->user_data);
    }
  }
  EXTRACT_LVERT_FOREACH_BM_END;
}

BLI_INLINE void extract_iter_lvert_mesh(const MeshRenderData *mr,
                                        const ExtractLVertMesh_Params *params,
                                        const MeshExtractRunDataArray *_extractors)
{
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);
  mesh_extract_run_data_array_filter_iter_type(_extractors, &extractors, MR_ITER_LVERT);

  EXTRACT_LVERT_FOREACH_MESH_BEGIN(mv, lvert_index, params, mr)
  {
    for (int i = 0; i < extractors.len; i++) {
      MeshExtractRunData *run_data = &extractors.items[i];
      run_data->extractor->iter_lvert_mesh(mr, mv, lvert_index, run_data->user_data);
    }
  }
  EXTRACT_LVERT_FOREACH_MESH_END;
}

BLI_INLINE void extract_finish(const MeshRenderData *mr,
                               struct MeshBatchCache *cache,
                               const MeshExtractRunDataArray *extractors)
{
  for (int i = 0; i < extractors->len; i++) {
    const MeshExtractRunData *run_data = &extractors->items[i];
    const MeshExtract *extractor = run_data->extractor;
    if (extractor->finish) {
      extractor->finish(mr, cache, run_data->buffer, run_data->user_data);
    }
  }
}

/* Single Thread. */
BLI_INLINE void extract_run_and_finish_init(const MeshRenderData *mr,
                                            struct MeshBatchCache *cache,
                                            MeshExtractRunDataArray *extractors,
                                            eMRIterType iter_type,
                                            MeshBufferCache *mbc)
{
  extract_init(mr, cache, extractors, mbc);

  bool is_mesh = mr->extract_type != MR_EXTRACT_BMESH;
  if (iter_type & MR_ITER_LOOPTRI) {
    if (is_mesh) {
      extract_iter_looptri_mesh(mr,
                                &(const ExtractTriMesh_Params){
                                    .mlooptri = mr->mlooptri,
                                    .tri_range = {0, mr->tri_len},
                                },
                                extractors);
    }
    else {
      extract_iter_looptri_bm(mr,
                              &(const ExtractTriBMesh_Params){
                                  .looptris = mr->edit_bmesh->looptris,
                                  .tri_range = {0, mr->tri_len},
                              },
                              extractors);
    }
  }
  if (iter_type & MR_ITER_POLY) {
    if (is_mesh) {
      extract_iter_poly_mesh(mr,
                             &(const ExtractPolyMesh_Params){
                                 .poly_range = {0, mr->poly_len},
                             },
                             extractors);
    }
    else {
      extract_iter_poly_bm(mr,
                           &(const ExtractPolyBMesh_Params){
                               .poly_range = {0, mr->poly_len},
                           },
                           extractors);
    }
  }
  if (iter_type & MR_ITER_LEDGE) {
    if (is_mesh) {
      extract_iter_ledge_mesh(mr,
                              &(const ExtractLEdgeMesh_Params){
                                  .ledge = mr->ledges,
                                  .ledge_range = {0, mr->edge_loose_len},
                              },
                              extractors);
    }
    else {
      extract_iter_ledge_bm(mr,
                            &(const ExtractLEdgeBMesh_Params){
                                .ledge = mr->ledges,
                                .ledge_range = {0, mr->edge_loose_len},
                            },
                            extractors);
    }
  }
  if (iter_type & MR_ITER_LVERT) {
    if (is_mesh) {
      extract_iter_lvert_mesh(mr,
                              &(const ExtractLVertMesh_Params){
                                  .lvert = mr->lverts,
                                  .lvert_range = {0, mr->vert_loose_len},
                              },
                              extractors);
    }
    else {
      extract_iter_lvert_bm(mr,
                            &(const ExtractLVertBMesh_Params){
                                .lvert = mr->lverts,
                                .lvert_range = {0, mr->vert_loose_len},
                            },
                            extractors);
    }
  }
  extract_finish(mr, cache, extractors);
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name ExtractTaskData
 * \{ */
typedef struct ExtractTaskData {
  void *next, *prev;
  const MeshRenderData *mr;
  struct MeshBatchCache *cache;
  MeshExtractRunDataArray *extractors;
  eMRIterType iter_type;
  int start, end;
  /** Decremented each time a task is finished. */
  int32_t *task_counter;
  MeshBufferCache *mbc;
} ExtractTaskData;

static ExtractTaskData *extract_extract_iter_task_data_create_mesh(
    const MeshRenderData *mr,
    struct MeshBatchCache *cache,
    MeshExtractRunDataArray *extractors,
    MeshBufferCache *mbc,
    int32_t *task_counter)
{
  ExtractTaskData *taskdata = MEM_mallocN(sizeof(*taskdata), __func__);
  taskdata->next = NULL;
  taskdata->prev = NULL;
  taskdata->mr = mr;
  taskdata->cache = cache;
  taskdata->mbc = mbc;

  /* #UserData is shared between the iterations as it holds counters to detect if the
   * extraction is finished. To make sure the duplication of the user_data does not create a new
   * instance of the counters we allocate the user_data in its own container.
   *
   * This structure makes sure that when extract_init is called, that the user data of all
   * iterations are updated. */
  taskdata->extractors = extractors;
  taskdata->task_counter = task_counter;

  extracts_flags_get(extractors, &taskdata->iter_type, NULL);
  taskdata->start = 0;
  taskdata->end = INT_MAX;
  return taskdata;
}

static void extract_task_data_free(void *data)
{
  ExtractTaskData *task_data = data;
  MEM_SAFE_FREE(task_data->extractors);
  MEM_freeN(task_data);
}

BLI_INLINE void mesh_extract_iter(const MeshRenderData *mr,
                                  const eMRIterType iter_type,
                                  int start,
                                  int end,
                                  MeshExtractRunDataArray *extractors)
{
  switch (mr->extract_type) {
    case MR_EXTRACT_BMESH:
      if (iter_type & MR_ITER_LOOPTRI) {
        extract_iter_looptri_bm(mr,
                                &(const ExtractTriBMesh_Params){
                                    .looptris = mr->edit_bmesh->looptris,
                                    .tri_range = {start, min_ii(mr->tri_len, end)},
                                },
                                extractors);
      }
      if (iter_type & MR_ITER_POLY) {
        extract_iter_poly_bm(mr,
                             &(const ExtractPolyBMesh_Params){
                                 .poly_range = {start, min_ii(mr->poly_len, end)},
                             },
                             extractors);
      }
      if (iter_type & MR_ITER_LEDGE) {
        extract_iter_ledge_bm(mr,
                              &(const ExtractLEdgeBMesh_Params){
                                  .ledge = mr->ledges,
                                  .ledge_range = {start, min_ii(mr->edge_loose_len, end)},
                              },
                              extractors);
      }
      if (iter_type & MR_ITER_LVERT) {
        extract_iter_lvert_bm(mr,
                              &(const ExtractLVertBMesh_Params){
                                  .lvert = mr->lverts,
                                  .lvert_range = {start, min_ii(mr->vert_loose_len, end)},
                              },
                              extractors);
      }
      break;
    case MR_EXTRACT_MAPPED:
    case MR_EXTRACT_MESH:
      if (iter_type & MR_ITER_LOOPTRI) {
        extract_iter_looptri_mesh(mr,
                                  &(const ExtractTriMesh_Params){
                                      .mlooptri = mr->mlooptri,
                                      .tri_range = {start, min_ii(mr->tri_len, end)},
                                  },
                                  extractors);
      }
      if (iter_type & MR_ITER_POLY) {
        extract_iter_poly_mesh(mr,
                               &(const ExtractPolyMesh_Params){
                                   .poly_range = {start, min_ii(mr->poly_len, end)},
                               },
                               extractors);
      }
      if (iter_type & MR_ITER_LEDGE) {
        extract_iter_ledge_mesh(mr,
                                &(const ExtractLEdgeMesh_Params){
                                    .ledge = mr->ledges,
                                    .ledge_range = {start, min_ii(mr->edge_loose_len, end)},
                                },
                                extractors);
      }
      if (iter_type & MR_ITER_LVERT) {
        extract_iter_lvert_mesh(mr,
                                &(const ExtractLVertMesh_Params){
                                    .lvert = mr->lverts,
                                    .lvert_range = {start, min_ii(mr->vert_loose_len, end)},
                                },
                                extractors);
      }
      break;
  }
}

static void extract_task_init(ExtractTaskData *data)
{
  extract_init(data->mr, data->cache, data->extractors, data->mbc);
}

static void extract_task_run(void *__restrict taskdata)
{
  ExtractTaskData *data = (ExtractTaskData *)taskdata;
  mesh_extract_iter(data->mr, data->iter_type, data->start, data->end, data->extractors);

  /* If this is the last task, we do the finish function. */
  int remainin_tasks = atomic_sub_and_fetch_int32(data->task_counter, 1);
  if (remainin_tasks == 0) {
    extract_finish(data->mr, data->cache, data->extractors);
  }
}

static void extract_task_init_and_run(void *__restrict taskdata)
{
  ExtractTaskData *data = (ExtractTaskData *)taskdata;
  extract_run_and_finish_init(data->mr, data->cache, data->extractors, data->iter_type, data->mbc);
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Task Node - Update Mesh Render Data
 * \{ */
typedef struct MeshRenderDataUpdateTaskData {
  MeshRenderData *mr;
  eMRIterType iter_type;
  eMRDataType data_flag;
} MeshRenderDataUpdateTaskData;

static void mesh_render_data_update_task_data_free(MeshRenderDataUpdateTaskData *taskdata)
{
  BLI_assert(taskdata);
  MeshRenderData *mr = taskdata->mr;
  mesh_render_data_free(mr);
  MEM_freeN(taskdata);
}

static void mesh_extract_render_data_node_exec(void *__restrict task_data)
{
  MeshRenderDataUpdateTaskData *update_task_data = task_data;
  MeshRenderData *mr = update_task_data->mr;
  const eMRIterType iter_type = update_task_data->iter_type;
  const eMRDataType data_flag = update_task_data->data_flag;

  mesh_render_data_update_normals(mr, iter_type, data_flag);
  mesh_render_data_update_looptris(mr, iter_type, data_flag);
}

static struct TaskNode *mesh_extract_render_data_node_create(struct TaskGraph *task_graph,
                                                             MeshRenderData *mr,
                                                             const eMRIterType iter_type,
                                                             const eMRDataType data_flag)
{
  MeshRenderDataUpdateTaskData *task_data = MEM_mallocN(sizeof(MeshRenderDataUpdateTaskData),
                                                        __func__);
  task_data->mr = mr;
  task_data->iter_type = iter_type;
  task_data->data_flag = data_flag;

  struct TaskNode *task_node = BLI_task_graph_node_create(
      task_graph,
      mesh_extract_render_data_node_exec,
      task_data,
      (TaskGraphNodeFreeFunction)mesh_render_data_update_task_data_free);
  return task_node;
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Task Node - Extract Single Threaded
 * \{ */

static struct TaskNode *extract_single_threaded_task_node_create(struct TaskGraph *task_graph,
                                                                 ExtractTaskData *task_data)
{
  struct TaskNode *task_node = BLI_task_graph_node_create(
      task_graph,
      extract_task_init_and_run,
      task_data,
      (TaskGraphNodeFreeFunction)extract_task_data_free);
  return task_node;
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Task Node - UserData Initializer
 * \{ */
typedef struct UserDataInitTaskData {
  ExtractTaskData *td;
  int32_t task_counter;

} UserDataInitTaskData;

static void user_data_init_task_data_free(UserDataInitTaskData *taskdata)
{
  BLI_assert(taskdata);
  extract_task_data_free(taskdata->td);
  MEM_freeN(taskdata);
}

static void user_data_init_task_data_exec(void *__restrict task_data)
{
  UserDataInitTaskData *extract_task_data = task_data;
  ExtractTaskData *taskdata_base = extract_task_data->td;
  extract_task_init(taskdata_base);
}

static struct TaskNode *user_data_init_task_node_create(struct TaskGraph *task_graph,
                                                        UserDataInitTaskData *task_data)
{
  struct TaskNode *task_node = BLI_task_graph_node_create(
      task_graph,
      user_data_init_task_data_exec,
      task_data,
      (TaskGraphNodeFreeFunction)user_data_init_task_data_free);
  return task_node;
}

/** \} */

/* ---------------------------------------------------------------------- */
/** \name Extract Loop
 * \{ */

static void extract_range_task_create(struct TaskGraph *task_graph,
                                      struct TaskNode *task_node_user_data_init,
                                      ExtractTaskData *taskdata,
                                      const eMRIterType type,
                                      int start,
                                      int length)
{
  taskdata = MEM_dupallocN(taskdata);
  atomic_add_and_fetch_int32(taskdata->task_counter, 1);
  taskdata->iter_type = type;
  taskdata->start = start;
  taskdata->end = start + length;
  struct TaskNode *task_node = BLI_task_graph_node_create(
      task_graph, extract_task_run, taskdata, MEM_freeN);
  BLI_task_graph_edge_create(task_node_user_data_init, task_node);
}

static int extract_range_task_num_elements_get(const MeshRenderData *mr,
                                               const eMRIterType iter_type)
{
  /* Divide task into sensible chunks. */
  int iter_len = 0;
  if (iter_type & MR_ITER_LOOPTRI) {
    iter_len += mr->tri_len;
  }
  if (iter_type & MR_ITER_POLY) {
    iter_len += mr->poly_len;
  }
  if (iter_type & MR_ITER_LEDGE) {
    iter_len += mr->edge_loose_len;
  }
  if (iter_type & MR_ITER_LVERT) {
    iter_len += mr->vert_loose_len;
  }
  return iter_len;
}

static int extract_range_task_chunk_size_get(const MeshRenderData *mr,
                                             const eMRIterType iter_type,
                                             const int num_threads)
{
  /* Divide task into sensible chunks. */
  const int num_elements = extract_range_task_num_elements_get(mr, iter_type);
  int range_len = (num_elements + num_threads) / num_threads;
  CLAMP_MIN(range_len, CHUNK_SIZE);
  return range_len;
}

static void extract_task_in_ranges_create(struct TaskGraph *task_graph,
                                          struct TaskNode *task_node_user_data_init,
                                          ExtractTaskData *taskdata_base,
                                          const int num_threads)
{
  const MeshRenderData *mr = taskdata_base->mr;
  const int range_len = extract_range_task_chunk_size_get(
      mr, taskdata_base->iter_type, num_threads);

  if (taskdata_base->iter_type & MR_ITER_LOOPTRI) {
    for (int i = 0; i < mr->tri_len; i += range_len) {
      extract_range_task_create(
          task_graph, task_node_user_data_init, taskdata_base, MR_ITER_LOOPTRI, i, range_len);
    }
  }
  if (taskdata_base->iter_type & MR_ITER_POLY) {
    for (int i = 0; i < mr->poly_len; i += range_len) {
      extract_range_task_create(
          task_graph, task_node_user_data_init, taskdata_base, MR_ITER_POLY, i, range_len);
    }
  }
  if (taskdata_base->iter_type & MR_ITER_LEDGE) {
    for (int i = 0; i < mr->edge_loose_len; i += range_len) {
      extract_range_task_create(
          task_graph, task_node_user_data_init, taskdata_base, MR_ITER_LEDGE, i, range_len);
    }
  }
  if (taskdata_base->iter_type & MR_ITER_LVERT) {
    for (int i = 0; i < mr->vert_loose_len; i += range_len) {
      extract_range_task_create(
          task_graph, task_node_user_data_init, taskdata_base, MR_ITER_LVERT, i, range_len);
    }
  }
}

void mesh_buffer_cache_create_requested(struct TaskGraph *task_graph,
                                        MeshBatchCache *cache,
                                        MeshBufferCache *mbc,
                                        MeshBufferExtractionCache *extraction_cache,
                                        Mesh *me,

                                        const bool is_editmode,
                                        const bool is_paint_mode,
                                        const bool is_mode_active,
                                        const float obmat[4][4],
                                        const bool do_final,
                                        const bool do_uvedit,
                                        const bool use_subsurf_fdots,
                                        const DRW_MeshCDMask *cd_layer_used,
                                        const Scene *scene,
                                        const ToolSettings *ts,
                                        const bool use_hide)
{
  /* For each mesh where batches needs to be updated a sub-graph will be added to the task_graph.
   * This sub-graph starts with an extract_render_data_node. This fills/converts the required
   * data from Mesh.
   *
   * Small extractions and extractions that can't be multi-threaded are grouped in a single
   * `extract_single_threaded_task_node`.
   *
   * Other extractions will create a node for each loop exceeding 8192 items. these nodes are
   * linked to the `user_data_init_task_node`. the `user_data_init_task_node` prepares the
   * user_data needed for the extraction based on the data extracted from the mesh.
   * counters are used to check if the finalize of a task has to be called.
   *
   *                           Mesh extraction sub graph
   *
   *                                                       +----------------------+
   *                                               +-----> | extract_task1_loop_1 |
   *                                               |       +----------------------+
   * +------------------+     +----------------------+     +----------------------+
   * | mesh_render_data | --> |                      | --> | extract_task1_loop_2 |
   * +------------------+     |                      |     +----------------------+
   *   |                      |                      |     +----------------------+
   *   |                      |    user_data_init    | --> | extract_task2_loop_1 |
   *   v                      |                      |     +----------------------+
   * +------------------+     |                      |     +----------------------+
   * | single_threaded  |     |                      | --> | extract_task2_loop_2 |
   * +------------------+     +----------------------+     +----------------------+
   *                                               |       +----------------------+
   *                                               +-----> | extract_task2_loop_3 |
   *                                                       +----------------------+
   */
  const bool do_lines_loose_subbuffer = mbc->ibo.lines_loose != NULL;
  const bool do_hq_normals = (scene->r.perf_flag & SCE_PERF_HQ_NORMALS) != 0 ||
                             GPU_use_hq_normals_workaround();

  /* Create an array containing all the extractors that needs to be executed. */
  MeshExtractRunDataArray extractors;
  mesh_extract_run_data_array_init(&extractors);

#define EXTRACT_ADD_REQUESTED(type, type_lowercase, name) \
  do { \
    if (DRW_##type_lowercase##_requested(mbc->type_lowercase.name)) { \
      const MeshExtract *extractor = mesh_extract_override_get( \
          &extract_##name, do_hq_normals, do_lines_loose_subbuffer); \
      mesh_extract_run_data_array_add(&extractors, extractor); \
    } \
  } while (0)

  EXTRACT_ADD_REQUESTED(VBO, vbo, pos_nor);
  EXTRACT_ADD_REQUESTED(VBO, vbo, lnor);
  EXTRACT_ADD_REQUESTED(VBO, vbo, uv);
  EXTRACT_ADD_REQUESTED(VBO, vbo, tan);
  EXTRACT_ADD_REQUESTED(VBO, vbo, vcol);
  EXTRACT_ADD_REQUESTED(VBO, vbo, sculpt_data);
  EXTRACT_ADD_REQUESTED(VBO, vbo, orco);
  EXTRACT_ADD_REQUESTED(VBO, vbo, edge_fac);
  EXTRACT_ADD_REQUESTED(VBO, vbo, weights);
  EXTRACT_ADD_REQUESTED(VBO, vbo, edit_data);
  EXTRACT_ADD_REQUESTED(VBO, vbo, edituv_data);
  EXTRACT_ADD_REQUESTED(VBO, vbo, edituv_stretch_area);
  EXTRACT_ADD_REQUESTED(VBO, vbo, edituv_stretch_angle);
  EXTRACT_ADD_REQUESTED(VBO, vbo, mesh_analysis);
  EXTRACT_ADD_REQUESTED(VBO, vbo, fdots_pos);
  EXTRACT_ADD_REQUESTED(VBO, vbo, fdots_nor);
  EXTRACT_ADD_REQUESTED(VBO, vbo, fdots_uv);
  EXTRACT_ADD_REQUESTED(VBO, vbo, fdots_edituv_data);
  EXTRACT_ADD_REQUESTED(VBO, vbo, poly_idx);
  EXTRACT_ADD_REQUESTED(VBO, vbo, edge_idx);
  EXTRACT_ADD_REQUESTED(VBO, vbo, vert_idx);
  EXTRACT_ADD_REQUESTED(VBO, vbo, fdot_idx);
  EXTRACT_ADD_REQUESTED(VBO, vbo, skin_roots);

  EXTRACT_ADD_REQUESTED(IBO, ibo, tris);
  EXTRACT_ADD_REQUESTED(IBO, ibo, lines);
  EXTRACT_ADD_REQUESTED(IBO, ibo, points);
  EXTRACT_ADD_REQUESTED(IBO, ibo, fdots);
  EXTRACT_ADD_REQUESTED(IBO, ibo, lines_paint_mask);
  EXTRACT_ADD_REQUESTED(IBO, ibo, lines_adjacency);
  EXTRACT_ADD_REQUESTED(IBO, ibo, edituv_tris);
  EXTRACT_ADD_REQUESTED(IBO, ibo, edituv_lines);
  EXTRACT_ADD_REQUESTED(IBO, ibo, edituv_points);
  EXTRACT_ADD_REQUESTED(IBO, ibo, edituv_fdots);

#undef EXTRACT_ADD_REQUESTED

  if (extractors.len == 0) {
    return;
  }

#ifdef DEBUG_TIME
  double rdata_start = PIL_check_seconds_timer();
#endif

  eMRIterType iter_type;
  eMRDataType data_flag;
  extracts_flags_get(&extractors, &iter_type, &data_flag);

  MeshRenderData *mr = mesh_render_data_create(me,
                                               extraction_cache,
                                               is_editmode,
                                               is_paint_mode,
                                               is_mode_active,
                                               obmat,
                                               do_final,
                                               do_uvedit,
                                               cd_layer_used,
                                               ts,
                                               iter_type);
  mr->use_hide = use_hide;
  mr->use_subsurf_fdots = use_subsurf_fdots;
  mr->use_final_mesh = do_final;

#ifdef DEBUG_TIME
  double rdata_end = PIL_check_seconds_timer();
#endif

  struct TaskNode *task_node_mesh_render_data = mesh_extract_render_data_node_create(
      task_graph, mr, iter_type, data_flag);

  /* Simple heuristic. */
  const bool use_thread = (mr->loop_len + mr->loop_loose_len) > CHUNK_SIZE;

  if (use_thread) {
    uint threads_to_use = 0;

    /* First run the requested extractors that do not support asynchronous ranges. */
    for (int i = 0; i < extractors.len; i++) {
      const MeshExtract *extractor = extractors.items[i].extractor;
      if (!extractor->use_threading) {
        MeshExtractRunDataArray *single_threaded_extractors = MEM_callocN(
            sizeof(MeshExtractRunDataArray),
            "mesh_buffer_cache_create_requested.single_threaded_extractors");
        mesh_extract_run_data_array_add(single_threaded_extractors, extractor);
        ExtractTaskData *taskdata = extract_extract_iter_task_data_create_mesh(
            mr, cache, single_threaded_extractors, mbc, NULL);
        struct TaskNode *task_node = extract_single_threaded_task_node_create(task_graph,
                                                                              taskdata);
        BLI_task_graph_edge_create(task_node_mesh_render_data, task_node);
      }
      threads_to_use++;
    }

    /* Distribute the remaining extractors into ranges per core. */
    MeshExtractRunDataArray *multi_threaded_extractors = MEM_callocN(
        sizeof(MeshExtractRunDataArray),
        "mesh_buffer_cache_create_requested.multi_threaded_extractors");
    mesh_extract_run_data_array_filter_threading(&extractors, multi_threaded_extractors);
    if (multi_threaded_extractors->len) {
      /*
       * Determine the number of thread to use for multithreading.
       * Thread can be used for single threaded tasks. These typically take longer to execute so
       * fill the rest of the threads for range operations.
       */
      int num_threads = BLI_task_scheduler_num_threads();
      if (threads_to_use < num_threads) {
        num_threads -= threads_to_use;
      }

      UserDataInitTaskData *user_data_init_task_data = MEM_callocN(
          sizeof(UserDataInitTaskData),
          "mesh_buffer_cache_create_requested.user_data_init_task_data");
      struct TaskNode *task_node_user_data_init = user_data_init_task_node_create(
          task_graph, user_data_init_task_data);

      user_data_init_task_data->td = extract_extract_iter_task_data_create_mesh(
          mr, cache, multi_threaded_extractors, mbc, &user_data_init_task_data->task_counter);

      extract_task_in_ranges_create(
          task_graph, task_node_user_data_init, user_data_init_task_data->td, num_threads);

      BLI_task_graph_edge_create(task_node_mesh_render_data, task_node_user_data_init);
    }
    else {
      /* No tasks created freeing extractors list. */
      MEM_freeN(multi_threaded_extractors);
    }
  }
  else {
    /* Run all requests on the same thread. */
    MeshExtractRunDataArray *extractors_copy = MEM_mallocN(
        sizeof(MeshExtractRunDataArray), "mesh_buffer_cache_create_requested.extractors_copy");
    memcpy(extractors_copy, &extractors, sizeof(MeshExtractRunDataArray));
    ExtractTaskData *taskdata = extract_extract_iter_task_data_create_mesh(
        mr, cache, extractors_copy, mbc, NULL);

    struct TaskNode *task_node = extract_single_threaded_task_node_create(task_graph, taskdata);
    BLI_task_graph_edge_create(task_node_mesh_render_data, task_node);
  }

  /* Trigger the sub-graph for this mesh. */
  BLI_task_graph_node_push_work(task_node_mesh_render_data);

#ifdef DEBUG_TIME
  BLI_task_graph_work_and_wait(task_graph);
  double end = PIL_check_seconds_timer();

  static double avg = 0;
  static double avg_fps = 0;
  static double avg_rdata = 0;
  static double end_prev = 0;

  if (end_prev == 0) {
    end_prev = end;
  }

  avg = avg * 0.95 + (end - rdata_end) * 0.05;
  avg_fps = avg_fps * 0.95 + (end - end_prev) * 0.05;
  avg_rdata = avg_rdata * 0.95 + (rdata_end - rdata_start) * 0.05;

  printf(
      "rdata %.0fms iter %.0fms (frame %.0fms)\n", avg_rdata * 1000, avg * 1000, avg_fps * 1000);

  end_prev = end;
#endif
}

/** \} */
