/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <fstream>
#include <iomanip>
#include <random>

#include "BLI_endian_defines.h"
#include "BLI_endian_switch.h"
#include "BLI_fileops.hh"
#include "BLI_path_util.h"
#include "BLI_serialize.hh"
#include "BLI_string.h"
#include "BLI_string_utils.hh"
#include "BLI_vector.hh"

#include "PIL_time.h"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_screen.hh"

#include "DNA_curves_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_pointcloud_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_bake_geometry_nodes_modifier.hh"
#include "BKE_context.h"
#include "BKE_curves.hh"
#include "BKE_global.h"
#include "BKE_instances.hh"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_mesh.hh"
#include "BKE_modifier.h"
#include "BKE_node_runtime.hh"
#include "BKE_object.hh"
#include "BKE_pointcloud.h"
#include "BKE_report.h"
#include "BKE_scene.h"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_build.hh"

#include "MOD_nodes.hh"

#include "object_intern.h"

#include "WM_api.hh"

#include "UI_interface.hh"

namespace bake = blender::bke::bake;

namespace blender::ed::object::bake_simulation {

static bool calculate_to_frame_poll(bContext *C)
{
  if (!ED_operator_object_active(C)) {
    return false;
  }
  return true;
}

struct CalculateSimulationJob {
  wmWindowManager *wm;
  Main *bmain;
  Depsgraph *depsgraph;
  Scene *scene;
  Vector<Object *> objects;
  int start_frame;
  int end_frame;
};

static void calculate_simulation_job_startjob(void *customdata, wmJobWorkerStatus *worker_status)
{
  CalculateSimulationJob &job = *static_cast<CalculateSimulationJob *>(customdata);
  G.is_rendering = true;
  G.is_break = false;
  WM_set_locked_interface(job.wm, true);

  Vector<Object *> objects_to_calc;
  for (Object *object : job.objects) {
    if (!BKE_id_is_editable(job.bmain, &object->id)) {
      continue;
    }
    LISTBASE_FOREACH (ModifierData *, md, &object->modifiers) {
      if (md->type != eModifierType_Nodes) {
        continue;
      }
      NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
      if (!nmd->runtime->cache) {
        continue;
      }
      for (auto item : nmd->runtime->cache->cache_by_id.items()) {
        if (item.value->cache_status != bake::CacheStatus::Baked) {
          item.value->reset();
        }
      }
    }
    objects_to_calc.append(object);
  }

  worker_status->progress = 0.0f;
  worker_status->do_update = true;

  const float frame_step_size = 1.0f;
  const float progress_per_frame = 1.0f /
                                   (float(job.end_frame - job.start_frame + 1) / frame_step_size);
  const int old_frame = job.scene->r.cfra;

  for (float frame_f = job.start_frame; frame_f <= job.end_frame; frame_f += frame_step_size) {
    const SubFrame frame{frame_f};

    if (G.is_break || worker_status->stop) {
      break;
    }

    job.scene->r.cfra = frame.frame();
    job.scene->r.subframe = frame.subframe();

    BKE_scene_graph_update_for_newframe(job.depsgraph);

    worker_status->progress += progress_per_frame;
    worker_status->do_update = true;
  }

  job.scene->r.cfra = old_frame;
  DEG_time_tag_update(job.bmain);

  worker_status->progress = 1.0f;
  worker_status->do_update = true;
}

static void calculate_simulation_job_endjob(void *customdata)
{
  CalculateSimulationJob &job = *static_cast<CalculateSimulationJob *>(customdata);
  WM_set_locked_interface(job.wm, false);
  G.is_rendering = false;
  WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, nullptr);
}

static int calculate_to_frame_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  Scene *scene = CTX_data_scene(C);
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);
  Main *bmain = CTX_data_main(C);

  CalculateSimulationJob *job = MEM_new<CalculateSimulationJob>(__func__);
  job->wm = wm;
  job->bmain = bmain;
  job->depsgraph = depsgraph;
  job->scene = scene;
  job->start_frame = scene->r.sfra;
  job->end_frame = scene->r.cfra;

  if (RNA_boolean_get(op->ptr, "selected")) {
    CTX_DATA_BEGIN (C, Object *, object, selected_objects) {
      job->objects.append(object);
    }
    CTX_DATA_END;
  }
  else {
    if (Object *object = CTX_data_active_object(C)) {
      job->objects.append(object);
    }
  }

  wmJob *wm_job = WM_jobs_get(wm,
                              CTX_wm_window(C),
                              CTX_data_scene(C),
                              "Calculate Simulation",
                              WM_JOB_PROGRESS,
                              WM_JOB_TYPE_CALCULATE_SIMULATION_NODES);

  WM_jobs_customdata_set(
      wm_job, job, [](void *job) { MEM_delete(static_cast<CalculateSimulationJob *>(job)); });
  WM_jobs_timer(wm_job, 0.1, NC_OBJECT | ND_MODIFIER, NC_OBJECT | ND_MODIFIER);
  WM_jobs_callbacks(wm_job,
                    calculate_simulation_job_startjob,
                    nullptr,
                    nullptr,
                    calculate_simulation_job_endjob);

  WM_jobs_start(CTX_wm_manager(C), wm_job);
  WM_event_add_modal_handler(C, op);
  return OPERATOR_RUNNING_MODAL;
}

static int calculate_to_frame_modal(bContext *C, wmOperator * /*op*/, const wmEvent * /*event*/)
{
  if (!WM_jobs_test(CTX_wm_manager(C), CTX_data_scene(C), WM_JOB_TYPE_CALCULATE_SIMULATION_NODES))
  {
    return OPERATOR_FINISHED | OPERATOR_PASS_THROUGH;
  }
  return OPERATOR_PASS_THROUGH;
}

static bool bake_simulation_poll(bContext *C)
{
  if (!ED_operator_object_active(C)) {
    return false;
  }
  Main *bmain = CTX_data_main(C);
  const StringRefNull path = BKE_main_blendfile_path(bmain);
  if (path.is_empty()) {
    CTX_wm_operator_poll_msg_set(C, "File has to be saved");
    return false;
  }
  return true;
}

struct NodeBakeData {
  int id;
  bake::BakePath path;
  int frame_start;
  int frame_end;
  std::unique_ptr<bake::BlobSharing> blob_sharing;
};

struct ModifierBakeData {
  NodesModifierData *nmd;
  Vector<NodeBakeData> nodes;
};

struct ObjectBakeData {
  Object *object;
  Vector<ModifierBakeData> modifiers;
};

struct BakeSimulationJob {
  wmWindowManager *wm;
  Main *bmain;
  Depsgraph *depsgraph;
  Scene *scene;
  Vector<ObjectBakeData> objects;
};

static void bake_simulation_job_startjob(void *customdata, wmJobWorkerStatus *worker_status)
{
  BakeSimulationJob &job = *static_cast<BakeSimulationJob *>(customdata);
  G.is_rendering = true;
  G.is_break = false;
  WM_set_locked_interface(job.wm, true);

  int global_bake_start_frame = INT32_MAX;
  int global_bake_end_frame = INT32_MIN;

  for (ObjectBakeData &object_bake : job.objects) {
    for (ModifierBakeData &modifier_bake : object_bake.modifiers) {
      for (NodeBakeData &node_bake : modifier_bake.nodes) {
        global_bake_start_frame = std::min(global_bake_start_frame, node_bake.frame_start);
        global_bake_end_frame = std::max(global_bake_end_frame, node_bake.frame_end);
      }
    }
  }

  worker_status->progress = 0.0f;
  worker_status->do_update = true;

  const int frames_to_bake = global_bake_end_frame - global_bake_start_frame + 1;

  const float frame_step_size = 1.0f;
  const float progress_per_frame = frame_step_size / frames_to_bake;
  const int old_frame = job.scene->r.cfra;

  for (float frame_f = global_bake_start_frame; frame_f <= global_bake_end_frame;
       frame_f += frame_step_size)
  {
    const SubFrame frame{frame_f};

    if (G.is_break || worker_status->stop) {
      break;
    }

    job.scene->r.cfra = frame.frame();
    job.scene->r.subframe = frame.subframe();

    BKE_scene_graph_update_for_newframe(job.depsgraph);

    const std::string frame_file_name = bake::frame_to_file_name(frame);

    for (ObjectBakeData &object_bake_data : job.objects) {
      for (ModifierBakeData &modifier_bake_data : object_bake_data.modifiers) {
        NodesModifierData &nmd = *modifier_bake_data.nmd;
        const bake::ModifierCache &modifier_cache = *nmd.runtime->cache;
        for (NodeBakeData &node_bake_data : modifier_bake_data.nodes) {
          if (!modifier_cache.cache_by_id.contains(node_bake_data.id)) {
            continue;
          }
          const bake::NodeCache &node_cache = *modifier_cache.cache_by_id.lookup(
              node_bake_data.id);
          if (node_cache.frame_caches.is_empty()) {
            continue;
          }
          const bake::FrameCache &frame_cache = *node_cache.frame_caches.last();
          if (frame_cache.frame != frame) {
            continue;
          }

          const bake::BakePath path = node_bake_data.path;

          const std::string blob_file_name = frame_file_name + ".blob";

          char blob_path[FILE_MAX];
          BLI_path_join(
              blob_path, sizeof(blob_path), path.blobs_dir.c_str(), blob_file_name.c_str());
          char meta_path[FILE_MAX];
          BLI_path_join(meta_path,
                        sizeof(meta_path),
                        path.meta_dir.c_str(),
                        (frame_file_name + ".json").c_str());
          BLI_file_ensure_parent_dir_exists(meta_path);
          BLI_file_ensure_parent_dir_exists(blob_path);
          fstream blob_file{blob_path, std::ios::out | std::ios::binary};
          bake::DiskBlobWriter blob_writer{blob_file_name, blob_file, 0};
          fstream meta_file{meta_path, std::ios::out};
          bake::serialize_bake(
              frame_cache.state, blob_writer, *node_bake_data.blob_sharing, meta_file);
        }
      }
    }

    worker_status->progress += progress_per_frame;
    worker_status->do_update = true;
  }

  for (ObjectBakeData &object_bake_data : job.objects) {
    for (ModifierBakeData &modifier_bake_data : object_bake_data.modifiers) {
      NodesModifierData &nmd = *modifier_bake_data.nmd;
      for (NodeBakeData &node_bake_data : modifier_bake_data.nodes) {
        if (std::unique_ptr<bake::NodeCache> *node_cache_ptr =
                nmd.runtime->cache->cache_by_id.lookup_ptr(node_bake_data.id))
        {
          bake::NodeCache &node_cache = **node_cache_ptr;
          if (!node_cache.frame_caches.is_empty()) {
            /* Tag the caches as being baked so that they are not changed anymore. */
            node_cache.cache_status = bake::CacheStatus::Baked;
          }
        }
      }
    }
    DEG_id_tag_update(&object_bake_data.object->id, ID_RECALC_GEOMETRY);
  }

  job.scene->r.cfra = old_frame;
  DEG_time_tag_update(job.bmain);

  worker_status->progress = 1.0f;
  worker_status->do_update = true;
}

static void bake_simulation_job_endjob(void *customdata)
{
  BakeSimulationJob &job = *static_cast<BakeSimulationJob *>(customdata);
  WM_set_locked_interface(job.wm, false);
  G.is_rendering = false;
  WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, nullptr);
}

static int start_bake_job(bContext *C, Vector<ObjectBakeData> objects_to_bake, wmOperator *op)
{
  BakeSimulationJob *job = MEM_new<BakeSimulationJob>(__func__);
  job->wm = CTX_wm_manager(C);
  job->bmain = CTX_data_main(C);
  job->depsgraph = CTX_data_depsgraph_pointer(C);
  job->scene = CTX_data_scene(C);
  job->objects = std::move(objects_to_bake);

  wmJob *wm_job = WM_jobs_get(job->wm,
                              CTX_wm_window(C),
                              job->scene,
                              "Bake Simulation Nodes",
                              WM_JOB_PROGRESS,
                              WM_JOB_TYPE_BAKE_SIMULATION_NODES);

  WM_jobs_customdata_set(
      wm_job, job, [](void *job) { MEM_delete(static_cast<BakeSimulationJob *>(job)); });
  WM_jobs_timer(wm_job, 0.1, NC_OBJECT | ND_MODIFIER, NC_OBJECT | ND_MODIFIER);
  WM_jobs_callbacks(
      wm_job, bake_simulation_job_startjob, nullptr, nullptr, bake_simulation_job_endjob);

  WM_jobs_start(CTX_wm_manager(C), wm_job);
  WM_event_add_modal_handler(C, op);
  return OPERATOR_RUNNING_MODAL;
}

static Vector<ObjectBakeData> collect_nodes_to_bake(Main &bmain,
                                                    Scene &scene,
                                                    const Span<Object *> objects)
{
  Vector<ObjectBakeData> objects_to_bake;
  for (Object *object : objects) {
    if (!BKE_id_is_editable(&bmain, &object->id)) {
      continue;
    }

    ObjectBakeData bake_data;
    bake_data.object = object;
    LISTBASE_FOREACH (ModifierData *, md, &object->modifiers) {
      if (md->type != eModifierType_Nodes) {
        continue;
      }
      NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
      if (!nmd->node_group) {
        continue;
      }
      if (!nmd->runtime->cache) {
        continue;
      }
      ModifierBakeData modifier_bake_data;
      modifier_bake_data.nmd = nmd;

      for (auto item : nmd->runtime->cache->cache_by_id.items()) {
        item.value->reset();
      }

      for (const bNestedNodeRef &nested_node_ref : nmd->node_group->nested_node_refs_span()) {
        NodeBakeData node_bake_data;
        node_bake_data.id = nested_node_ref.id;
        node_bake_data.blob_sharing = std::make_unique<bake::BlobSharing>();
        std::optional<bake::BakePath> path = bake::get_node_bake_path(
            bmain, *object, *nmd, nested_node_ref.id);
        if (!path) {
          continue;
        }
        std::optional<IndexRange> frame_range = bake::get_node_bake_frame_range(
            scene, *object, *nmd, nested_node_ref.id);
        if (!frame_range) {
          continue;
        }
        node_bake_data.path = std::move(*path);
        node_bake_data.frame_start = frame_range->first();
        node_bake_data.frame_end = frame_range->last();

        modifier_bake_data.nodes.append(std::move(node_bake_data));
      }
      if (modifier_bake_data.nodes.is_empty()) {
        continue;
      }
      bake_data.modifiers.append(std::move(modifier_bake_data));
    }
    if (bake_data.modifiers.is_empty()) {
      continue;
    }
    objects_to_bake.append(std::move(bake_data));
  }
  return objects_to_bake;
}

static int bake_simulation_exec(bContext *C, wmOperator *op)
{
  Scene *scene = CTX_data_scene(C);
  Main *bmain = CTX_data_main(C);

  Vector<Object *> objects;
  if (RNA_boolean_get(op->ptr, "selected")) {
    CTX_DATA_BEGIN (C, Object *, object, selected_objects) {
      objects.append(object);
    }
    CTX_DATA_END;
  }
  else {
    if (Object *object = CTX_data_active_object(C)) {
      objects.append(object);
    }
  }

  Vector<ObjectBakeData> objects_to_bake = collect_nodes_to_bake(*bmain, *scene, objects);
  return start_bake_job(C, std::move(objects_to_bake), op);
}

struct PathStringHash {
  uint64_t operator()(const StringRef s) const
  {
    /* Normalize the paths so we can compare them. */
    DynamicStackBuffer<256> norm_buf(s.size() + 1, 8);
    memcpy(norm_buf.buffer(), s.data(), s.size() + 1);
    char *norm = static_cast<char *>(norm_buf.buffer());

    BLI_path_slash_native(norm);

    /* Strip ending slash. */
    BLI_path_slash_rstrip(norm);

    BLI_path_normalize(norm);
    return get_default_hash(norm);
  }
};

struct PathStringEquality {
  bool operator()(const StringRef a, const StringRef b) const
  {
    return BLI_path_cmp_normalized(a.data(), b.data()) == 0;
  }
};

static bool bake_directory_has_data(const StringRefNull absolute_bake_dir)
{
  char meta_dir[FILE_MAX];
  BLI_path_join(meta_dir, sizeof(meta_dir), absolute_bake_dir.c_str(), "meta");
  char blobs_dir[FILE_MAX];
  BLI_path_join(blobs_dir, sizeof(blobs_dir), absolute_bake_dir.c_str(), "blobs");

  if (!BLI_is_dir(meta_dir) || !BLI_is_dir(blobs_dir)) {
    return false;
  }

  return true;
}

static void bake_simulation_validate_paths(bContext *C,
                                           wmOperator *op,
                                           const Span<Object *> objects)
{
  Main *bmain = CTX_data_main(C);

  for (Object *object : objects) {
    if (!BKE_id_is_editable(bmain, &object->id)) {
      continue;
    }

    LISTBASE_FOREACH (ModifierData *, md, &object->modifiers) {
      if (md->type != eModifierType_Nodes) {
        continue;
      }

      NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
      if (StringRef(nmd->simulation_bake_directory).is_empty()) {
        BKE_reportf(op->reports,
                    RPT_INFO,
                    "Bake directory of object %s, modifier %s is empty, setting default path",
                    object->id.name + 2,
                    md->name);

        nmd->simulation_bake_directory = BLI_strdup(
            bake::get_default_modifier_bake_directory(*bmain, *object, *nmd).c_str());
      }
    }
  }
}

/* Map for counting path references. */
using PathUsersMap = Map<std::string,
                         int,
                         default_inline_buffer_capacity(sizeof(std::string)),
                         DefaultProbingStrategy,
                         PathStringHash,
                         PathStringEquality>;

static PathUsersMap bake_simulation_get_path_users(bContext *C, const Span<Object *> objects)
{
  Main *bmain = CTX_data_main(C);

  PathUsersMap path_users;
  for (const Object *object : objects) {
    const char *base_path = ID_BLEND_PATH(bmain, &object->id);

    LISTBASE_FOREACH (const ModifierData *, md, &object->modifiers) {
      if (md->type != eModifierType_Nodes) {
        continue;
      }
      const NodesModifierData *nmd = reinterpret_cast<const NodesModifierData *>(md);
      if (StringRef(nmd->simulation_bake_directory).is_empty()) {
        continue;
      }

      char absolute_bake_dir[FILE_MAX];
      STRNCPY(absolute_bake_dir, nmd->simulation_bake_directory);
      BLI_path_abs(absolute_bake_dir, base_path);
      path_users.add_or_modify(
          absolute_bake_dir, [](int *value) { *value = 1; }, [](int *value) { ++(*value); });
    }
  }

  return path_users;
}

static int bake_simulation_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  Vector<Object *> objects;
  if (RNA_boolean_get(op->ptr, "selected")) {
    CTX_DATA_BEGIN (C, Object *, object, selected_objects) {
      objects.append(object);
    }
    CTX_DATA_END;
  }
  else {
    if (Object *object = CTX_data_active_object(C)) {
      objects.append(object);
    }
  }

  /* Set empty paths to default. */
  bake_simulation_validate_paths(C, op, objects);

  PathUsersMap path_users = bake_simulation_get_path_users(C, objects);
  bool has_path_conflict = false;
  bool has_existing_bake_data = false;
  for (const auto &item : path_users.items()) {
    /* Check if multiple caches are writing to the same bake directory. */
    if (item.value > 1) {
      BKE_reportf(op->reports,
                  RPT_ERROR,
                  "Path conflict: %d caches set to path %s",
                  item.value,
                  item.key.data());
      has_path_conflict = true;
    }

    /* Check if path exists and contains bake data already. */
    if (bake_directory_has_data(item.key.data())) {
      has_existing_bake_data = true;
    }
  }

  if (has_path_conflict) {
    UI_popup_menu_reports(C, op->reports);
    return OPERATOR_CANCELLED;
  }
  if (has_existing_bake_data) {
    return WM_operator_confirm_message(C, op, "Overwrite existing bake data");
  }
  return bake_simulation_exec(C, op);
}

static int bake_simulation_modal(bContext *C, wmOperator * /*op*/, const wmEvent * /*event*/)
{
  if (!WM_jobs_test(CTX_wm_manager(C), CTX_data_scene(C), WM_JOB_TYPE_BAKE_SIMULATION_NODES)) {
    return OPERATOR_FINISHED | OPERATOR_PASS_THROUGH;
  }
  return OPERATOR_PASS_THROUGH;
}

static void try_delete_bake(
    bContext *C, Object &object, NodesModifierData &nmd, const int bake_id, ReportList *reports)
{
  Main *bmain = CTX_data_main(C);
  if (!nmd.runtime->cache) {
    return;
  }
  bake::ModifierCache &modifier_cache = *nmd.runtime->cache;
  std::lock_guard lock{modifier_cache.mutex};
  if (!modifier_cache.cache_by_id.contains(bake_id)) {
    return;
  }
  bake::NodeCache &node_cache = *modifier_cache.cache_by_id.lookup(bake_id);
  node_cache.reset();
  const std::optional<bake::BakePath> bake_path = bake::get_node_bake_path(
      *bmain, object, nmd, bake_id);
  if (!bake_path) {
    return;
  }
  const char *meta_dir = bake_path->meta_dir.c_str();
  if (BLI_exists(meta_dir)) {
    if (BLI_delete(meta_dir, true, true)) {
      BKE_reportf(reports, RPT_ERROR, "Failed to remove metadata directory %s", meta_dir);
    }
  }
  const char *blobs_dir = bake_path->blobs_dir.c_str();
  if (BLI_exists(blobs_dir)) {
    if (BLI_delete(blobs_dir, true, true)) {
      BKE_reportf(reports, RPT_ERROR, "Failed to remove blobs directory %s", blobs_dir);
    }
  }
  if (bake_path->bake_dir.has_value()) {
    const char *zone_bake_dir = bake_path->bake_dir->c_str();
    /* Try to delete zone bake directory if it is empty. */
    BLI_delete(zone_bake_dir, true, false);
  }
  if (const std::optional<std::string> modifier_bake_dir = bake::get_modifier_bake_path(
          *bmain, object, nmd))
  {
    /* Try to delete modifier bake directory if it is empty. */
    BLI_delete(modifier_bake_dir->c_str(), true, false);
  }
}

static int delete_baked_simulation_exec(bContext *C, wmOperator *op)
{
  Vector<Object *> objects;
  if (RNA_boolean_get(op->ptr, "selected")) {
    CTX_DATA_BEGIN (C, Object *, object, selected_objects) {
      objects.append(object);
    }
    CTX_DATA_END;
  }
  else {
    if (Object *object = CTX_data_active_object(C)) {
      objects.append(object);
    }
  }

  if (objects.is_empty()) {
    return OPERATOR_CANCELLED;
  }

  for (Object *object : objects) {
    LISTBASE_FOREACH (ModifierData *, md, &object->modifiers) {
      if (md->type == eModifierType_Nodes) {
        NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
        for (const NodesModifierBake &bake : Span(nmd->bakes, nmd->bakes_num)) {
          try_delete_bake(C, *object, *nmd, bake.id, op->reports);
        }
      }
    }

    DEG_id_tag_update(&object->id, ID_RECALC_GEOMETRY);
  }

  WM_event_add_notifier(C, NC_OBJECT | ND_MODIFIER, nullptr);

  return OPERATOR_FINISHED;
}

static int bake_single_simulation_exec(bContext *C, wmOperator *op)
{
  Main *bmain = CTX_data_main(C);
  Scene *scene = CTX_data_scene(C);
  Object *object = reinterpret_cast<Object *>(
      WM_operator_properties_id_lookup_from_name_or_session_uuid(bmain, op->ptr, ID_OB));
  if (object == nullptr) {
    return OPERATOR_CANCELLED;
  }
  char *modifier_name = RNA_string_get_alloc(op->ptr, "modifier_name", nullptr, 0, nullptr);
  if (modifier_name == nullptr) {
    return OPERATOR_CANCELLED;
  }
  BLI_SCOPED_DEFER([&]() { MEM_SAFE_FREE(modifier_name); });

  ModifierData *md = BKE_modifiers_findby_name(object, modifier_name);
  if (md == nullptr) {
    return OPERATOR_CANCELLED;
  }
  NodesModifierData &nmd = *reinterpret_cast<NodesModifierData *>(md);

  if (StringRef(nmd.simulation_bake_directory).is_empty()) {
    const std::string directory = bake::get_default_modifier_bake_directory(*bmain, *object, nmd);
    nmd.simulation_bake_directory = BLI_strdup(directory.c_str());
  }

  const int bake_id = RNA_int_get(op->ptr, "bake_id");
  const std::optional<bake::BakePath> bake_path = bake::get_node_bake_path(
      *bmain, *object, nmd, bake_id);
  if (!bake_path.has_value()) {
    return OPERATOR_CANCELLED;
  }
  const std::optional<IndexRange> frame_range = bake::get_node_bake_frame_range(
      *scene, *object, nmd, bake_id);
  if (!frame_range.has_value()) {
    return OPERATOR_CANCELLED;
  }
  if (frame_range->is_empty()) {
    return OPERATOR_CANCELLED;
  }

  NodeBakeData node_bake_data;
  node_bake_data.id = bake_id;
  node_bake_data.path = std::move(*bake_path);
  node_bake_data.frame_start = frame_range->first();
  node_bake_data.frame_end = frame_range->last();
  node_bake_data.blob_sharing = std::make_unique<bake::BlobSharing>();

  ModifierBakeData modifier_bake_data;
  modifier_bake_data.nmd = &nmd;
  modifier_bake_data.nodes.append(std::move(node_bake_data));

  ObjectBakeData object_bake_data;
  object_bake_data.object = object;
  object_bake_data.modifiers.append(std::move(modifier_bake_data));

  Vector<ObjectBakeData> objects_to_bake;
  objects_to_bake.append(std::move(object_bake_data));
  return start_bake_job(C, std::move(objects_to_bake), op);
}

static int bake_single_simulation_modal(bContext *C,
                                        wmOperator * /*op*/,
                                        const wmEvent * /*event*/)
{
  if (!WM_jobs_test(CTX_wm_manager(C), CTX_data_scene(C), WM_JOB_TYPE_BAKE_SIMULATION_NODES)) {
    return OPERATOR_FINISHED | OPERATOR_PASS_THROUGH;
  }
  return OPERATOR_PASS_THROUGH;
}

static int delete_baked_simulation_single_exec(bContext *C, wmOperator *op)
{
  Main *bmain = CTX_data_main(C);
  Object *object = reinterpret_cast<Object *>(
      WM_operator_properties_id_lookup_from_name_or_session_uuid(bmain, op->ptr, ID_OB));
  if (object == nullptr) {
    return OPERATOR_CANCELLED;
  }
  char *modifier_name = RNA_string_get_alloc(op->ptr, "modifier_name", nullptr, 0, nullptr);
  if (modifier_name == nullptr) {
    return OPERATOR_CANCELLED;
  }
  BLI_SCOPED_DEFER([&]() { MEM_SAFE_FREE(modifier_name); });

  ModifierData *md = BKE_modifiers_findby_name(object, modifier_name);
  if (md == nullptr) {
    return OPERATOR_CANCELLED;
  }
  NodesModifierData &nmd = *reinterpret_cast<NodesModifierData *>(md);
  const int bake_id = RNA_int_get(op->ptr, "bake_id");

  try_delete_bake(C, *object, nmd, bake_id, op->reports);
  return OPERATOR_FINISHED;
}

}  // namespace blender::ed::object::bake_simulation

void OBJECT_OT_simulation_nodes_cache_calculate_to_frame(wmOperatorType *ot)
{
  using namespace blender::ed::object::bake_simulation;

  ot->name = "Calculate Simulation to Frame";
  ot->description =
      "Calculate simulations in geometry nodes modifiers from the start to current frame";
  ot->idname = __func__;

  ot->invoke = calculate_to_frame_invoke;
  ot->modal = calculate_to_frame_modal;
  ot->poll = calculate_to_frame_poll;

  RNA_def_boolean(ot->srna,
                  "selected",
                  false,
                  "Selected",
                  "Calculate all selected objects instead of just the active object");
}

void OBJECT_OT_simulation_nodes_cache_bake(wmOperatorType *ot)
{
  using namespace blender::ed::object::bake_simulation;

  ot->name = "Bake Simulation";
  ot->description = "Bake simulations in geometry nodes modifiers";
  ot->idname = __func__;

  ot->exec = bake_simulation_exec;
  ot->invoke = bake_simulation_invoke;
  ot->modal = bake_simulation_modal;
  ot->poll = bake_simulation_poll;

  RNA_def_boolean(ot->srna, "selected", false, "Selected", "Bake cache on all selected objects");
}

void OBJECT_OT_simulation_nodes_cache_delete(wmOperatorType *ot)
{
  using namespace blender::ed::object::bake_simulation;

  ot->name = "Delete Cached Simulation";
  ot->description = "Delete cached/baked simulations in geometry nodes modifiers";
  ot->idname = __func__;

  ot->exec = delete_baked_simulation_exec;
  ot->poll = ED_operator_object_active;

  RNA_def_boolean(ot->srna, "selected", false, "Selected", "Delete cache on all selected objects");
}

void OBJECT_OT_simulation_nodes_cache_bake_single(wmOperatorType *ot)
{
  using namespace blender::ed::object::bake_simulation;

  ot->name = "Bake Single Simulation Zone";
  ot->description = "Bake a single simulation zone";
  ot->idname = "OBJECT_OT_simulation_nodes_cache_bake_single";

  ot->exec = bake_single_simulation_exec;
  ot->modal = bake_single_simulation_modal;

  WM_operator_properties_id_lookup(ot, false);

  RNA_def_string(ot->srna,
                 "modifier_name",
                 nullptr,
                 0,
                 "Modifier Name",
                 "Name of the modifier that contains the node to bake");
  RNA_def_int(ot->srna,
              "bake_id",
              0,
              0,
              INT32_MAX,
              "Bake ID",
              "Nested node id of the node to bake",
              0,
              INT32_MAX);
}

void OBJECT_OT_simulation_nodes_cache_delete_single(wmOperatorType *ot)
{
  using namespace blender::ed::object::bake_simulation;

  ot->name = "Delete Single Cached Simulation";
  ot->description = "Delete simulation data of a single simulation zone";
  ot->idname = "OBJECT_OT_simulation_nodes_cache_delete_single";

  ot->exec = delete_baked_simulation_single_exec;

  WM_operator_properties_id_lookup(ot, false);

  RNA_def_string(ot->srna,
                 "modifier_name",
                 nullptr,
                 0,
                 "Modifier Name",
                 "Name of the modifier that contains the node");
  RNA_def_int(ot->srna,
              "bake_id",
              0,
              0,
              INT32_MAX,
              "Bake ID",
              "Nested node id of the bake to delete",
              0,
              INT32_MAX);
}
