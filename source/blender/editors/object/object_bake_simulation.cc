/* SPDX-FileCopyrightText: 2023 Blender Foundation
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
#include "BLI_string_utils.h"
#include "BLI_vector.hh"

#include "PIL_time.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_screen.h"

#include "DNA_curves_types.h"
#include "DNA_material_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_pointcloud_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_context.h"
#include "BKE_curves.hh"
#include "BKE_global.h"
#include "BKE_instances.hh"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_mesh.hh"
#include "BKE_object.h"
#include "BKE_pointcloud.h"
#include "BKE_report.h"
#include "BKE_scene.h"
#include "BKE_simulation_state.hh"
#include "BKE_simulation_state_serialize.hh"

#include "RNA_access.h"
#include "RNA_define.h"
#include "RNA_enum_types.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"

#include "MOD_nodes.hh"

#include "object_intern.h"

#include "WM_api.h"

#include "UI_interface.h"

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

static void calculate_simulation_job_startjob(void *customdata,
                                              bool *stop,
                                              bool *do_update,
                                              float *progress)
{
  using namespace bke::sim;

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
      if (md->type == eModifierType_Nodes) {
        NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
        nmd->runtime->simulation_cache->reset();
      }
    }
    objects_to_calc.append(object);
  }

  *progress = 0.0f;
  *do_update = true;

  const float frame_step_size = 1.0f;
  const float progress_per_frame = 1.0f /
                                   (float(job.end_frame - job.start_frame + 1) / frame_step_size);
  const int old_frame = job.scene->r.cfra;

  for (float frame_f = job.start_frame; frame_f <= job.end_frame; frame_f += frame_step_size) {
    const SubFrame frame{frame_f};

    if (G.is_break || (stop != nullptr && *stop)) {
      break;
    }

    job.scene->r.cfra = frame.frame();
    job.scene->r.subframe = frame.subframe();

    BKE_scene_graph_update_for_newframe(job.depsgraph);

    *progress += progress_per_frame;
    *do_update = true;
  }

  job.scene->r.cfra = old_frame;
  DEG_time_tag_update(job.bmain);

  *progress = 1.0f;
  *do_update = true;
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

struct ModifierBakeData {
  NodesModifierData *nmd;
  std::string absolute_bake_dir;
  std::unique_ptr<bke::sim::BDataSharing> bdata_sharing;
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
  Vector<Object *> objects;
};

static void bake_simulation_job_startjob(void *customdata,
                                         bool *stop,
                                         bool *do_update,
                                         float *progress)
{
  using namespace bke::sim;

  BakeSimulationJob &job = *static_cast<BakeSimulationJob *>(customdata);
  G.is_rendering = true;
  G.is_break = false;
  WM_set_locked_interface(job.wm, true);

  Vector<ObjectBakeData> objects_to_bake;
  for (Object *object : job.objects) {
    if (!BKE_id_is_editable(job.bmain, &object->id)) {
      continue;
    }

    const char *base_path = ID_BLEND_PATH(job.bmain, &object->id);

    ObjectBakeData bake_data;
    bake_data.object = object;
    LISTBASE_FOREACH (ModifierData *, md, &object->modifiers) {
      if (md->type == eModifierType_Nodes) {
        NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
        nmd->runtime->simulation_cache->reset();
        char absolute_bake_dir[FILE_MAX];
        STRNCPY(absolute_bake_dir, nmd->simulation_bake_directory);
        BLI_path_abs(absolute_bake_dir, base_path);
        bake_data.modifiers.append({nmd, absolute_bake_dir, std::make_unique<BDataSharing>()});
      }
    }
    objects_to_bake.append(std::move(bake_data));
  }

  *progress = 0.0f;
  *do_update = true;

  const float frame_step_size = 1.0f;
  const float progress_per_frame = 1.0f / (float(job.scene->r.efra - job.scene->r.sfra + 1) /
                                           frame_step_size);
  const int old_frame = job.scene->r.cfra;

  for (float frame_f = job.scene->r.sfra; frame_f <= job.scene->r.efra; frame_f += frame_step_size)
  {
    const SubFrame frame{frame_f};

    if (G.is_break || (stop != nullptr && *stop)) {
      break;
    }

    job.scene->r.cfra = frame.frame();
    job.scene->r.subframe = frame.subframe();

    char frame_file_c_str[64];
    SNPRINTF(frame_file_c_str, "%011.5f", double(frame));
    BLI_string_replace_char(frame_file_c_str, '.', '_');
    const StringRefNull frame_file_str = frame_file_c_str;

    BKE_scene_graph_update_for_newframe(job.depsgraph);

    for (ObjectBakeData &object_bake_data : objects_to_bake) {
      for (ModifierBakeData &modifier_bake_data : object_bake_data.modifiers) {
        NodesModifierData &nmd = *modifier_bake_data.nmd;
        if (!nmd.runtime->simulation_cache) {
          continue;
        }
        ModifierSimulationCache &sim_cache = *nmd.runtime->simulation_cache;
        const ModifierSimulationState *sim_state = sim_cache.get_state_at_exact_frame(frame);
        if (sim_state == nullptr || sim_state->zone_states_.is_empty()) {
          continue;
        }

        const std::string bdata_file_name = frame_file_str + ".bdata";
        const std::string meta_file_name = frame_file_str + ".json";

        char bdata_path[FILE_MAX];
        BLI_path_join(bdata_path,
                      sizeof(bdata_path),
                      modifier_bake_data.absolute_bake_dir.c_str(),
                      "bdata",
                      bdata_file_name.c_str());
        char meta_path[FILE_MAX];
        BLI_path_join(meta_path,
                      sizeof(meta_path),
                      modifier_bake_data.absolute_bake_dir.c_str(),
                      "meta",
                      meta_file_name.c_str());

        BLI_file_ensure_parent_dir_exists(bdata_path);
        fstream bdata_file{bdata_path, std::ios::out | std::ios::binary};
        bke::sim::DiskBDataWriter bdata_writer{bdata_file_name, bdata_file, 0};

        io::serialize::DictionaryValue io_root;
        bke::sim::serialize_modifier_simulation_state(
            *sim_state, bdata_writer, *modifier_bake_data.bdata_sharing, io_root);

        BLI_file_ensure_parent_dir_exists(meta_path);
        io::serialize::write_json_file(meta_path, io_root);
      }
    }

    *progress += progress_per_frame;
    *do_update = true;
  }

  for (ObjectBakeData &object_bake_data : objects_to_bake) {
    for (ModifierBakeData &modifier_bake_data : object_bake_data.modifiers) {
      NodesModifierData &nmd = *modifier_bake_data.nmd;
      if (nmd.runtime->simulation_cache) {
        /* Tag the caches as being baked so that they are not changed anymore. */
        nmd.runtime->simulation_cache->cache_state = CacheState::Baked;
      }
    }
    DEG_id_tag_update(&object_bake_data.object->id, ID_RECALC_GEOMETRY);
  }

  job.scene->r.cfra = old_frame;
  DEG_time_tag_update(job.bmain);

  *progress = 1.0f;
  *do_update = true;
}

static void bake_simulation_job_endjob(void *customdata)
{
  BakeSimulationJob &job = *static_cast<BakeSimulationJob *>(customdata);
  WM_set_locked_interface(job.wm, false);
  G.is_rendering = false;
  WM_main_add_notifier(NC_OBJECT | ND_MODIFIER, nullptr);
}

static int bake_simulation_exec(bContext *C, wmOperator *op)
{
  wmWindowManager *wm = CTX_wm_manager(C);
  Scene *scene = CTX_data_scene(C);
  Depsgraph *depsgraph = CTX_data_depsgraph_pointer(C);
  Main *bmain = CTX_data_main(C);

  BakeSimulationJob *job = MEM_new<BakeSimulationJob>(__func__);
  job->wm = wm;
  job->bmain = bmain;
  job->depsgraph = depsgraph;
  job->scene = scene;

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
  char bdata_dir[FILE_MAX];
  BLI_path_join(bdata_dir, sizeof(bdata_dir), absolute_bake_dir.c_str(), "bdata");

  if (!BLI_is_dir(meta_dir) || !BLI_is_dir(bdata_dir)) {
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
            bke::sim::get_default_modifier_bake_directory(*bmain, *object, *md).c_str());
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

static int delete_baked_simulation_exec(bContext *C, wmOperator *op)
{
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

  if (objects.is_empty()) {
    return OPERATOR_CANCELLED;
  }

  for (Object *object : objects) {
    const char *base_path = ID_BLEND_PATH(bmain, &object->id);
    LISTBASE_FOREACH (ModifierData *, md, &object->modifiers) {
      if (md->type == eModifierType_Nodes) {
        NodesModifierData *nmd = reinterpret_cast<NodesModifierData *>(md);
        nmd->runtime->simulation_cache->reset();
        if (StringRef(nmd->simulation_bake_directory).is_empty()) {
          continue;
        }
        char absolute_bake_dir[FILE_MAX];
        STRNCPY(absolute_bake_dir, nmd->simulation_bake_directory);
        BLI_path_abs(absolute_bake_dir, base_path);
        if (BLI_exists(absolute_bake_dir)) {
          if (BLI_delete(absolute_bake_dir, true, true)) {
            BKE_reportf(
                op->reports, RPT_ERROR, "Failed to remove bake directory %s", absolute_bake_dir);
          }
        }
      }
    }

    DEG_id_tag_update(&object->id, ID_RECALC_GEOMETRY);
  }

  WM_event_add_notifier(C, NC_OBJECT | ND_MODIFIER, nullptr);

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
