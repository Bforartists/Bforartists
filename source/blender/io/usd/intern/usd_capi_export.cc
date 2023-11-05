/* SPDX-FileCopyrightText: 2019 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "usd.h"
#include "usd.hh"
#include "usd_hierarchy_iterator.h"
#include "usd_hook.h"

#include <pxr/base/plug/registry.h>
#include <pxr/base/tf/token.h>
#include <pxr/pxr.h>
#include <pxr/usd/usd/prim.h>
#include <pxr/usd/usd/primRange.h>
#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usdGeom/tokens.h>
#include <pxr/usd/usdGeom/xform.h>
#include <pxr/usd/usdUtils/dependencies.h>

#include "MEM_guardedalloc.h"

#include "DEG_depsgraph.hh"
#include "DEG_depsgraph_build.hh"
#include "DEG_depsgraph_query.hh"

#include "DNA_scene_types.h"

#include "BKE_appdir.h"
#include "BKE_blender_version.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_report.h"
#include "BKE_scene.h"

#include "BLI_fileops.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_timeit.hh"

#include "WM_api.hh"
#include "WM_types.hh"

namespace blender::io::usd {

struct ExportJobData {
  Main *bmain;
  Depsgraph *depsgraph;
  wmWindowManager *wm;

  /** Unarchived_filepath is used for USDA/USDC/USD export. */
  char unarchived_filepath[FILE_MAX];
  char usdz_filepath[FILE_MAX];
  USDExportParams params;

  bool export_ok;
  timeit::TimePoint start_time;

  bool targets_usdz() const
  {
    return usdz_filepath[0] != '\0';
  }

  const char *export_filepath() const
  {
    if (targets_usdz()) {
      return usdz_filepath;
    }
    return unarchived_filepath;
  }
};

/* Returns true if the given prim path is valid, per
 * the requirements of the prim path manipulation logic
 * of the exporter. Also returns true if the path is
 * the empty string. Returns false otherwise. */
static bool prim_path_valid(const char *path)
{
  BLI_assert(path);

  if (path[0] == '\0') {
    /* Empty paths are ignored in the code,
     * so they can be passed through. */
    return true;
  }

  /* Check path syntax. */
  std::string errMsg;
  if (!pxr::SdfPath::IsValidPathString(path, &errMsg)) {
    WM_reportf(RPT_ERROR, "USD Export: invalid path string '%s': %s", path, errMsg.c_str());
    return false;
  }

  /* Verify that an absolute prim path can be constructed
   * from this path string. */

  pxr::SdfPath sdf_path(path);
  if (!sdf_path.IsAbsolutePath()) {
    WM_reportf(RPT_ERROR, "USD Export: path '%s' is not an absolute path", path);
    return false;
  }

  if (!sdf_path.IsPrimPath()) {
    WM_reportf(RPT_ERROR, "USD Export: path string '%s' is not a prim path", path);
    return false;
  }

  return true;
}

/**
 * Perform validation of export parameter settings.
 * \return true if the parameters are valid; returns false otherwise.
 *
 * \warning Do not call from worker thread, only from main thread (i.e. before starting the wmJob).
 */
static bool export_params_valid(const USDExportParams &params)
{
  bool valid = true;

  if (!prim_path_valid(params.root_prim_path)) {
    valid = false;
  }

  return valid;
}

/**
 * Create the root Xform primitive, if the Root Prim path has been set
 * in the export options. In the future, this function can be extended
 * to author transforms and additional schema data (e.g., model Kind)
 * on the root prim.
 */
static void ensure_root_prim(pxr::UsdStageRefPtr stage, const USDExportParams &params)
{
  if (params.root_prim_path[0] == '\0') {
    return;
  }

  for (auto path : pxr::SdfPath(params.root_prim_path).GetPrefixes()) {
    auto xform = pxr::UsdGeomXform::Define(stage, path);
    /* Tag generated prims to allow filtering on import */
    xform.GetPrim().SetCustomDataByKey(pxr::TfToken("Blender:generated"), pxr::VtValue(true));
  }
}

static void report_job_duration(const ExportJobData *data)
{
  timeit::Nanoseconds duration = timeit::Clock::now() - data->start_time;
  const char *export_filepath = data->export_filepath();
  std::cout << "USD export of '" << export_filepath << "' took ";
  timeit::print_duration(duration);
  std::cout << '\n';
}

/**
 * For usdz export, we must first create a usd/a/c file and then covert it to usdz. In Blender's
 * case, we first create a usdc file in Blender's temporary working directory, and store the path
 * to the usdc file in `unarchived_filepath`. This function then does the conversion of that usdc
 * file into usdz.
 *
 * \return true when the conversion from usdc to usdz is successful.
 */
static bool perform_usdz_conversion(const ExportJobData *data)
{
  char usdc_temp_dir[FILE_MAX], usdc_file[FILE_MAX];
  BLI_path_split_dir_file(data->unarchived_filepath,
                          usdc_temp_dir,
                          sizeof(usdc_temp_dir),
                          usdc_file,
                          sizeof(usdc_file));

  char usdz_file[FILE_MAX];
  BLI_path_split_file_part(data->usdz_filepath, usdz_file, FILE_MAX);

  char original_working_dir_buff[FILE_MAX];
  char *original_working_dir = BLI_current_working_dir(original_working_dir_buff,
                                                       sizeof(original_working_dir_buff));
  /* Buffer is expected to be returned by #BLI_current_working_dir, although in theory other
   * returns are possible on some platforms, this is not handled by this code. */
  BLI_assert(original_working_dir == original_working_dir_buff);

  BLI_change_working_dir(usdc_temp_dir);

  pxr::UsdUtilsCreateNewUsdzPackage(pxr::SdfAssetPath(usdc_file), usdz_file);
  BLI_change_working_dir(original_working_dir);

  char usdz_temp_full_path[FILE_MAX];
  BLI_path_join(usdz_temp_full_path, FILE_MAX, usdc_temp_dir, usdz_file);

  int result = 0;
  if (BLI_exists(data->usdz_filepath)) {
    result = BLI_delete(data->usdz_filepath, false, false);
    if (result != 0) {
      BKE_reportf(data->params.worker_status->reports,
                  RPT_ERROR,
                  "USD Export: Unable to delete existing usdz file %s",
                  data->usdz_filepath);
      return false;
    }
  }
  result = BLI_path_move(usdz_temp_full_path, data->usdz_filepath);
  if (result != 0) {
    BKE_reportf(data->params.worker_status->reports,
                RPT_ERROR,
                "USD Export: Couldn't move new usdz file from temporary location %s to %s",
                usdz_temp_full_path,
                data->usdz_filepath);
    return false;
  }

  return true;
}

pxr::UsdStageRefPtr export_to_stage(const USDExportParams &params,
                                    Depsgraph *depsgraph,
                                    const char *filepath)
{
  pxr::UsdStageRefPtr usd_stage = pxr::UsdStage::CreateNew(filepath);
  if (!usd_stage) {
    return usd_stage;
  }

  wmJobWorkerStatus *worker_status = params.worker_status;
  Scene *scene = DEG_get_input_scene(depsgraph);
  Main *bmain = DEG_get_bmain(depsgraph);

  /* This whole `export_to_stage` function is assumed to cover about 80% of the whole export
   * process, from 0.1f to 0.9f. */
  worker_status->progress = 0.10f;
  worker_status->do_update = true;

  usd_stage->SetMetadata(pxr::UsdGeomTokens->metersPerUnit, double(scene->unit.scale_length));
  usd_stage->GetRootLayer()->SetDocumentation(std::string("Blender v") +
                                              BKE_blender_version_string());

  /* Set up the stage for animated data. */
  if (params.export_animation) {
    usd_stage->SetTimeCodesPerSecond(FPS);
    usd_stage->SetStartTimeCode(scene->r.sfra);
    usd_stage->SetEndTimeCode(scene->r.efra);
  }

  /* For restoring the current frame after exporting animation is done. */
  const int orig_frame = scene->r.cfra;

  /* Ensure Python types for invoking export hooks are registered. */
  register_export_hook_converters();

  usd_stage->SetMetadata(pxr::UsdGeomTokens->upAxis, pxr::VtValue(pxr::UsdGeomTokens->z));
  ensure_root_prim(usd_stage, params);

  USDHierarchyIterator iter(bmain, depsgraph, usd_stage, params);

  worker_status->progress = 0.11f;
  worker_status->do_update = true;

  if (params.export_animation) {
    /* Writing the animated frames is not 100% of the work, here it's assumed to be 75% of it. */
    float progress_per_frame = 0.75f / std::max(1, (scene->r.efra - scene->r.sfra + 1));

    for (float frame = scene->r.sfra; frame <= scene->r.efra; frame++) {
      if (G.is_break || worker_status->stop) {
        break;
      }

      /* Update the scene for the next frame to render. */
      scene->r.cfra = int(frame);
      scene->r.subframe = frame - scene->r.cfra;
      BKE_scene_graph_update_for_newframe(depsgraph);

      iter.set_export_frame(frame);
      iter.iterate_and_write();

      worker_status->progress += progress_per_frame;
      worker_status->do_update = true;
    }
  }
  else {
    /* If we're not animating, a single iteration over all objects is enough. */
    iter.iterate_and_write();
  }

  worker_status->progress = 0.86f;
  worker_status->do_update = true;

  iter.release_writers();

  /* Set the default prim if it doesn't exist */
  if (!usd_stage->GetDefaultPrim()) {
    /* Use TraverseAll since it's guaranteed to be depth first and will get the first top level
     * prim, and is less verbose than getting the PseudoRoot + iterating its children. */
    for (auto prim : usd_stage->TraverseAll()) {
      usd_stage->SetDefaultPrim(prim);
      break;
    }
  }

  call_export_hooks(usd_stage, depsgraph, params.worker_status->reports);

  worker_status->progress = 0.88f;
  worker_status->do_update = true;

  /* Finish up by going back to the keyframe that was current before we started. */
  if (scene->r.cfra != orig_frame) {
    scene->r.cfra = orig_frame;
    BKE_scene_graph_update_for_newframe(depsgraph);
  }

  worker_status->progress = 0.9f;
  worker_status->do_update = true;

  return usd_stage;
}

static void export_startjob(void *customdata, wmJobWorkerStatus *worker_status)
{
  ExportJobData *data = static_cast<ExportJobData *>(customdata);
  data->export_ok = false;
  data->start_time = timeit::Clock::now();

  G.is_rendering = true;
  if (data->wm) {
    WM_set_locked_interface(data->wm, true);
  }
  G.is_break = false;

  worker_status->progress = 0.01f;
  worker_status->do_update = true;

  /* Evaluate the depsgraph for exporting.
   *
   * Note that, unlike with its building, this is expected to be safe to perform from worker
   * thread, since UI is locked during export, so there should not be any more changes in the Main
   * original data concurrently done from the main thread at this point. All necessary (deferred)
   * changes are expected to have been triggered and processed during depsgraph building in
   * #USD_export. */
  BKE_scene_graph_update_tagged(data->depsgraph, data->bmain);

  worker_status->progress = 0.1f;
  worker_status->do_update = true;
  data->params.worker_status = worker_status;

  pxr::UsdStageRefPtr usd_stage = export_to_stage(
      data->params, data->depsgraph, data->unarchived_filepath);
  if (!usd_stage) {
    /* This happens when the USD JSON files cannot be found. When that happens,
     * the USD library doesn't know it has the functionality to write USDA and
     * USDC files, and creating a new UsdStage fails. */
    BKE_reportf(worker_status->reports,
                RPT_ERROR,
                "USD Export: unable to find suitable USD plugin to write %s",
                data->unarchived_filepath);
    return;
  }

  usd_stage->GetRootLayer()->Save();

  data->export_ok = true;
  worker_status->progress = 1.0f;
  worker_status->do_update = true;
}

static void export_endjob_usdz_cleanup(const ExportJobData *data)
{
  if (!BLI_exists(data->unarchived_filepath)) {
    return;
  }

  char dir[FILE_MAX];
  BLI_path_split_dir_part(data->unarchived_filepath, dir, FILE_MAX);

  char usdc_temp_dir[FILE_MAX];
  BLI_path_join(usdc_temp_dir, FILE_MAX, BKE_tempdir_session(), "USDZ", SEP_STR);

  BLI_assert_msg(BLI_strcasecmp(dir, usdc_temp_dir) == 0,
                 "USD Export: Attempting to delete directory that doesn't match the expected "
                 "temporary directory for usdz export.");
  BLI_delete(usdc_temp_dir, true, true);
}

static void export_endjob(void *customdata)
{
  ExportJobData *data = static_cast<ExportJobData *>(customdata);

  DEG_graph_free(data->depsgraph);

  if (data->targets_usdz()) {
    /* NOTE: call to #perform_usdz_conversion has to be done here instead of the main threaded
     * worker callback (#export_startjob) because USDZ conversion requires changing the current
     * working directory. This is not safe to do from a non-main thread. Once the USD library fix
     * this weird requirement, this call can be moved back at the end of #export_startjob, and not
     * block the main user interface anymore. */
    bool usd_conversion_success = perform_usdz_conversion(data);
    if (!usd_conversion_success) {
      data->export_ok = false;
    }

    export_endjob_usdz_cleanup(data);
  }

  if (!data->export_ok && BLI_exists(data->unarchived_filepath)) {
    BLI_delete(data->unarchived_filepath, false, false);
  }

  G.is_rendering = false;
  if (data->wm) {
    WM_set_locked_interface(data->wm, false);
  }
  report_job_duration(data);
}

}  // namespace blender::io::usd

/* To create a usdz file, we must first create a .usd/a/c file and then covert it to .usdz. The
 * temporary files will be created in Blender's temporary session storage. The .usdz file will then
 * be moved to job->usdz_filepath. */
static void create_temp_path_for_usdz_export(const char *filepath,
                                             blender::io::usd::ExportJobData *job)
{
  char usdc_file[FILE_MAX];
  STRNCPY(usdc_file, BLI_path_basename(filepath));

  if (BLI_path_extension_check(usdc_file, ".usdz")) {
    BLI_path_extension_replace(usdc_file, sizeof(usdc_file), ".usdc");
  }

  char usdc_temp_filepath[FILE_MAX];
  BLI_path_join(usdc_temp_filepath, FILE_MAX, BKE_tempdir_session(), "USDZ", usdc_file);

  STRNCPY(job->unarchived_filepath, usdc_temp_filepath);
  STRNCPY(job->usdz_filepath, filepath);
}

static void set_job_filepath(blender::io::usd::ExportJobData *job, const char *filepath)
{
  if (BLI_path_extension_check_n(filepath, ".usdz", nullptr)) {
    create_temp_path_for_usdz_export(filepath, job);
    return;
  }

  STRNCPY(job->unarchived_filepath, filepath);
  job->usdz_filepath[0] = '\0';
}

bool USD_export(bContext *C,
                const char *filepath,
                const USDExportParams *params,
                bool as_background_job,
                ReportList *reports)
{
  if (!blender::io::usd::export_params_valid(*params)) {
    return false;
  }

  ViewLayer *view_layer = CTX_data_view_layer(C);
  Scene *scene = CTX_data_scene(C);

  blender::io::usd::ExportJobData *job = static_cast<blender::io::usd::ExportJobData *>(
      MEM_mallocN(sizeof(blender::io::usd::ExportJobData), "ExportJobData"));

  job->bmain = CTX_data_main(C);
  job->wm = CTX_wm_manager(C);
  job->export_ok = false;
  set_job_filepath(job, filepath);

  job->depsgraph = DEG_graph_new(job->bmain, scene, view_layer, params->evaluation_mode);
  job->params = *params;

  /* Construct the depsgraph for exporting.
   *
   * Has to be done from main thread currently, as it may affect Main original data (e.g. when
   * doing deferred update of the view-layers, see #112534 for details). */
  if (job->params.visible_objects_only) {
    DEG_graph_build_from_view_layer(job->depsgraph);
  }
  else {
    DEG_graph_build_for_all_objects(job->depsgraph);
  }

  bool export_ok = false;
  if (as_background_job) {
    wmJob *wm_job = WM_jobs_get(
        job->wm, CTX_wm_window(C), scene, "USD Export", WM_JOB_PROGRESS, WM_JOB_TYPE_ALEMBIC);

    /* setup job */
    WM_jobs_customdata_set(wm_job, job, MEM_freeN);
    WM_jobs_timer(wm_job, 0.1, NC_SCENE | ND_FRAME, NC_SCENE | ND_FRAME);
    WM_jobs_callbacks(wm_job,
                      blender::io::usd::export_startjob,
                      nullptr,
                      nullptr,
                      blender::io::usd::export_endjob);

    WM_jobs_start(CTX_wm_manager(C), wm_job);
  }
  else {
    wmJobWorkerStatus worker_status = {};
    /* Use the operator's reports in non-background case. */
    worker_status.reports = reports;

    blender::io::usd::export_startjob(job, &worker_status);
    blender::io::usd::export_endjob(job);
    export_ok = job->export_ok;

    MEM_freeN(job);
  }

  return export_ok;
}

int USD_get_version()
{
  /* USD 19.11 defines:
   *
   * #define PXR_MAJOR_VERSION 0
   * #define PXR_MINOR_VERSION 19
   * #define PXR_PATCH_VERSION 11
   * #define PXR_VERSION 1911
   *
   * So the major version is implicit/invisible in the public version number.
   */
  return PXR_VERSION;
}
