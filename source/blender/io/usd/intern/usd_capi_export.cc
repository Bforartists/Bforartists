/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2019 Blender Foundation. All rights reserved. */

#include "usd.h"
#include "usd_common.h"
#include "usd_hierarchy_iterator.h"

#include <pxr/base/plug/registry.h>
#include <pxr/pxr.h>
#include <pxr/usd/usd/prim.h>
#include <pxr/usd/usd/primRange.h>
#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usdGeom/tokens.h>
#include <pxr/usd/usdUtils/dependencies.h>

#include "MEM_guardedalloc.h"

#include "DEG_depsgraph.h"
#include "DEG_depsgraph_build.h"
#include "DEG_depsgraph_query.h"

#include "DNA_scene_types.h"

#include "BKE_appdir.h"
#include "BKE_blender_version.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_scene.h"

#include "BLI_fileops.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_timeit.hh"

#include "WM_api.h"
#include "WM_types.h"

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
  BLI_split_dirfile(data->unarchived_filepath, usdc_temp_dir, usdc_file, FILE_MAX, FILE_MAX);

  char usdz_file[FILE_MAX];
  BLI_split_file_part(data->usdz_filepath, usdz_file, FILE_MAX);

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
      WM_reportf(
          RPT_ERROR, "USD Export: Unable to delete existing usdz file %s", data->usdz_filepath);
      return false;
    }
  }
  result = BLI_path_move(usdz_temp_full_path, data->usdz_filepath);
  if (result != 0) {
    WM_reportf(RPT_ERROR,
               "USD Export: Couldn't move new usdz file from temporary location %s to %s",
               usdz_temp_full_path,
               data->usdz_filepath);
    return false;
  }

  return true;
}

static void export_startjob(void *customdata,
                            /* Cannot be const, this function implements wm_jobs_start_callback.
                             * NOLINTNEXTLINE: readability-non-const-parameter. */
                            bool *stop,
                            bool *do_update,
                            float *progress)
{
  ExportJobData *data = static_cast<ExportJobData *>(customdata);
  data->export_ok = false;
  data->start_time = timeit::Clock::now();

  G.is_rendering = true;
  if (data->wm) {
    WM_set_locked_interface(data->wm, true);
  }
  G.is_break = false;

  /* Construct the depsgraph for exporting. */
  Scene *scene = DEG_get_input_scene(data->depsgraph);
  if (data->params.visible_objects_only) {
    DEG_graph_build_from_view_layer(data->depsgraph);
  }
  else {
    DEG_graph_build_for_all_objects(data->depsgraph);
  }
  BKE_scene_graph_update_tagged(data->depsgraph, data->bmain);

  *progress = 0.0f;
  *do_update = true;

  /* For restoring the current frame after exporting animation is done. */
  const int orig_frame = scene->r.cfra;

  pxr::UsdStageRefPtr usd_stage = pxr::UsdStage::CreateNew(data->unarchived_filepath);
  if (!usd_stage) {
    /* This happens when the USD JSON files cannot be found. When that happens,
     * the USD library doesn't know it has the functionality to write USDA and
     * USDC files, and creating a new UsdStage fails. */
    WM_reportf(RPT_ERROR,
               "USD Export: unable to find suitable USD plugin to write %s",
               data->unarchived_filepath);
    return;
  }

  usd_stage->SetMetadata(pxr::UsdGeomTokens->upAxis, pxr::VtValue(pxr::UsdGeomTokens->z));
  usd_stage->SetMetadata(pxr::UsdGeomTokens->metersPerUnit, double(scene->unit.scale_length));
  usd_stage->GetRootLayer()->SetDocumentation(std::string("Blender v") +
                                              BKE_blender_version_string());

  /* Set up the stage for animated data. */
  if (data->params.export_animation) {
    usd_stage->SetTimeCodesPerSecond(FPS);
    usd_stage->SetStartTimeCode(scene->r.sfra);
    usd_stage->SetEndTimeCode(scene->r.efra);
  }

  USDHierarchyIterator iter(data->bmain, data->depsgraph, usd_stage, data->params);

  if (data->params.export_animation) {
    /* Writing the animated frames is not 100% of the work, but it's our best guess. */
    float progress_per_frame = 1.0f / std::max(1, (scene->r.efra - scene->r.sfra + 1));

    for (float frame = scene->r.sfra; frame <= scene->r.efra; frame++) {
      if (G.is_break || (stop != nullptr && *stop)) {
        break;
      }

      /* Update the scene for the next frame to render. */
      scene->r.cfra = int(frame);
      scene->r.subframe = frame - scene->r.cfra;
      BKE_scene_graph_update_for_newframe(data->depsgraph);

      iter.set_export_frame(frame);
      iter.iterate_and_write();

      *progress += progress_per_frame;
      *do_update = true;
    }
  }
  else {
    /* If we're not animating, a single iteration over all objects is enough. */
    iter.iterate_and_write();
  }

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

  usd_stage->GetRootLayer()->Save();

  /* Finish up by going back to the keyframe that was current before we started. */
  if (scene->r.cfra != orig_frame) {
    scene->r.cfra = orig_frame;
    BKE_scene_graph_update_for_newframe(data->depsgraph);
  }

  if (data->targets_usdz()) {
    bool usd_conversion_success = perform_usdz_conversion(data);
    if (!usd_conversion_success) {
      data->export_ok = false;
      *progress = 1.0f;
      *do_update = true;
      return;
    }
  }

  data->export_ok = true;
  *progress = 1.0f;
  *do_update = true;
}

static void export_endjob_usdz_cleanup(const ExportJobData *data)
{
  if (!BLI_exists(data->unarchived_filepath)) {
    return;
  }

  char dir[FILE_MAX];
  BLI_split_dir_part(data->unarchived_filepath, dir, FILE_MAX);

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
  char file[FILE_MAX];
  BLI_split_file_part(filepath, file, FILE_MAX);
  char *usdc_file = BLI_str_replaceN(file, ".usdz", ".usdc");

  char usdc_temp_filepath[FILE_MAX];
  BLI_path_join(usdc_temp_filepath, FILE_MAX, BKE_tempdir_session(), "USDZ", usdc_file);

  BLI_strncpy(job->unarchived_filepath, usdc_temp_filepath, strlen(usdc_temp_filepath) + 1);
  BLI_strncpy(job->usdz_filepath, filepath, strlen(filepath) + 1);

  MEM_freeN(usdc_file);
}

static void set_job_filepath(blender::io::usd::ExportJobData *job, const char *filepath)
{
  if (BLI_path_extension_check_n(filepath, ".usdz", NULL)) {
    create_temp_path_for_usdz_export(filepath, job);
    return;
  }

  BLI_strncpy(job->unarchived_filepath, filepath, sizeof(job->unarchived_filepath));
  job->usdz_filepath[0] = '\0';
}

bool USD_export(bContext *C,
                const char *filepath,
                const USDExportParams *params,
                bool as_background_job)
{
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
    /* Fake a job context, so that we don't need NULL pointer checks while exporting. */
    bool stop = false, do_update = false;
    float progress = 0.0f;

    blender::io::usd::export_startjob(job, &stop, &do_update, &progress);
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
