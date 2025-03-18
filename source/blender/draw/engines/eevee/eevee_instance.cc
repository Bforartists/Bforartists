/* SPDX-FileCopyrightText: 2021 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eevee
 *
 * An instance contains all structures needed to do a complete render.
 */

#include "BKE_global.hh"
#include "BKE_object.hh"

#include "BLI_rect.h"
#include "BLI_time.h"

#include "BLT_translation.hh"

#include "DEG_depsgraph_query.hh"

#include "DNA_ID.h"
#include "DNA_lightprobe_types.h"
#include "DNA_modifier_types.h"

#include "ED_screen.hh"
#include "ED_view3d.hh"
#include "GPU_context.hh"
#include "IMB_imbuf_types.hh"

#include "RE_pipeline.h"

#include "eevee_engine.h"
#include "eevee_instance.hh"

#include "DNA_particle_types.h"

#include "draw_common.hh"
#include "draw_context_private.hh"
#include "draw_view_data.hh"

namespace blender::eevee {

void *Instance::debug_scope_render_sample = nullptr;
void *Instance::debug_scope_irradiance_setup = nullptr;
void *Instance::debug_scope_irradiance_sample = nullptr;

/* -------------------------------------------------------------------- */
/** \name Initialization
 *
 * Initialization functions need to be called once at the start of a frame.
 * Active camera, render extent and enabled render passes are immutable until next init.
 * This takes care of resizing output buffers and view in case a parameter changed.
 * IMPORTANT: xxx.init() functions are NOT meant to acquire and allocate DRW resources.
 * Any attempt to do so will likely produce use after free situations.
 * \{ */

void Instance::init()
{
  this->draw_ctx = DRW_context_get();

  Depsgraph *depsgraph = draw_ctx->depsgraph;
  Scene *scene = draw_ctx->scene;
  View3D *v3d = draw_ctx->v3d;
  ARegion *region = draw_ctx->region;
  RegionView3D *rv3d = draw_ctx->rv3d;

  DefaultTextureList *dtxl = draw_ctx->viewport_texture_list_get();
  int2 size = int2(GPU_texture_width(dtxl->color), GPU_texture_height(dtxl->color));

  draw::View &default_view = draw::View::default_get();

  Object *camera = nullptr;
  /* Get render borders. */
  rcti rect;
  BLI_rcti_init(&rect, 0, size[0], 0, size[1]);
  rcti visible_rect = rect;
  if (v3d) {
    if (rv3d && (rv3d->persp == RV3D_CAMOB)) {
      camera = v3d->camera;
    }

    if (camera) {
      rctf default_border;
      BLI_rctf_init(&default_border, 0.0f, 1.0f, 0.0f, 1.0f);
      bool is_default_border = BLI_rctf_compare(&scene->r.border, &default_border, 0.0f);
      bool use_border = scene->r.mode & R_BORDER;
      if (!is_default_border && use_border) {
        rctf viewborder;
        /* TODO(fclem) Might be better to get it from DRW. */
        ED_view3d_calc_camera_border(scene, depsgraph, region, v3d, rv3d, false, &viewborder);
        float viewborder_sizex = BLI_rctf_size_x(&viewborder);
        float viewborder_sizey = BLI_rctf_size_y(&viewborder);
        rect.xmin = floorf(viewborder.xmin + (scene->r.border.xmin * viewborder_sizex));
        rect.ymin = floorf(viewborder.ymin + (scene->r.border.ymin * viewborder_sizey));
        rect.xmax = floorf(viewborder.xmin + (scene->r.border.xmax * viewborder_sizex));
        rect.ymax = floorf(viewborder.ymin + (scene->r.border.ymax * viewborder_sizey));
      }
    }
    else if (v3d->flag2 & V3D_RENDER_BORDER) {
      rect.xmin = v3d->render_border.xmin * size[0];
      rect.ymin = v3d->render_border.ymin * size[1];
      rect.xmax = v3d->render_border.xmax * size[0];
      rect.ymax = v3d->render_border.ymax * size[1];
    }

    if (draw_ctx->is_viewport_image_render()) {
      const float2 vp_size = draw_ctx->viewport_size_get();
      visible_rect.xmax = vp_size[0];
      visible_rect.ymax = vp_size[1];
      visible_rect.xmin = visible_rect.ymin = 0;
    }
    else {
      visible_rect = *ED_region_visible_rect(region);
    }
  }

  init(size, &rect, &visible_rect, nullptr, depsgraph, camera, nullptr, &default_view, v3d, rv3d);
}

void Instance::init(const int2 &output_res,
                    const rcti *output_rect,
                    const rcti *visible_rect,
                    RenderEngine *render_,
                    Depsgraph *depsgraph_,
                    Object *camera_object_,
                    const RenderLayer *render_layer_,
                    View *drw_view_,
                    const View3D *v3d_,
                    const RegionView3D *rv3d_)
{
  this->draw_ctx = DRW_context_get();

  render = render_;
  depsgraph = depsgraph_;
  camera_orig_object = camera_object_;
  render_layer = render_layer_;
  drw_view = drw_view_;
  v3d = v3d_;
  rv3d = rv3d_;
  manager = DRW_manager_get();
  update_eval_members();

  info_ = "";

  if (is_viewport()) {
    is_image_render = draw_ctx->is_image_render();
    is_viewport_image_render = draw_ctx->is_viewport_image_render();
    is_viewport_compositor_enabled = draw_ctx->is_viewport_compositor_enabled();
    is_playback = draw_ctx->is_playback();
    is_navigating = draw_ctx->is_navigating();
    is_painting = draw_ctx->is_painting();
    is_transforming = draw_ctx->is_transforming();
    draw_overlays = v3d && (v3d->flag2 & V3D_HIDE_OVERLAYS) == 0;

    /* Note: Do not update the value here as we use it during sync for checking ID updates. */
    if (depsgraph_last_update_ != DEG_get_update_count(depsgraph)) {
      sampling.reset();
    }
    if (assign_if_different(debug_mode, (eDebugMode)G.debug_value)) {
      sampling.reset();
    }
    if (output_res != film.display_extent_get()) {
      sampling.reset();
    }
    if (output_rect) {
      int2 offset = int2(output_rect->xmin, output_rect->ymin);
      int2 extent = int2(BLI_rcti_size_x(output_rect), BLI_rcti_size_y(output_rect));
      if (offset != film.get_data().offset || extent != film.get_data().extent) {
        sampling.reset();
      }
    }
    if (assign_if_different(overlays_enabled_, v3d && !(v3d->flag2 & V3D_HIDE_OVERLAYS))) {
      sampling.reset();
    }
    if (is_painting) {
      sampling.reset();
    }
    if (is_navigating && scene->eevee.flag & SCE_EEVEE_SHADOW_JITTERED_VIEWPORT) {
      sampling.reset();
    }
  }
  else {
    is_image_render = true;
  }

  shaders_are_ready_ = shaders.static_shaders_are_ready(is_image_render);
  if (!shaders_are_ready_) {
    skip_render_ = true;
    return;
  }

  sampling.init(scene);
  camera.init();
  film.init(output_res, output_rect);
  render_buffers.init();
  ambient_occlusion.init();
  velocity.init();
  raytracing.init();
  depth_of_field.init();
  shadows.init();
  motion_blur.init();
  main_view.init();
  light_probes.init();
  planar_probes.init();
  /* Irradiance Cache needs reflection probes to be initialized. */
  sphere_probes.init();
  volume_probes.init();
  volume.init();
  lookdev.init(visible_rect);

  shaders_are_ready_ = shaders.static_shaders_are_ready(is_image_render) &&
                       shaders.request_specializations(is_image_render,
                                                       render_buffers.data.shadow_id,
                                                       shadows.get_data().ray_count,
                                                       shadows.get_data().step_count);
  skip_render_ = !shaders_are_ready_ || !film.is_valid_render_extent();
}

void Instance::init_light_bake(Depsgraph *depsgraph, draw::Manager *manager)
{
  this->depsgraph = depsgraph;
  this->manager = manager;
  camera_orig_object = nullptr;
  render = nullptr;
  render_layer = nullptr;
  drw_view = nullptr;
  v3d = nullptr;
  rv3d = nullptr;
  update_eval_members();

  is_light_bake = true;
  debug_mode = (eDebugMode)G.debug_value;
  info_ = "";

  shaders.static_shaders_are_ready(true);

  sampling.init(scene);
  camera.init();
  /* Film isn't used but init to avoid side effects in other module. */
  rcti empty_rect{0, 0, 0, 0};
  film.init(int2(1), &empty_rect);
  render_buffers.init();
  velocity.init();
  depth_of_field.init();
  shadows.init();
  main_view.init();
  light_probes.init();
  planar_probes.init();
  /* Irradiance Cache needs reflection probes to be initialized. */
  sphere_probes.init();
  volume_probes.init();
  volume.init();
  lookdev.init(&empty_rect);

  shaders.request_specializations(true,
                                  render_buffers.data.shadow_id,
                                  shadows.get_data().ray_count,
                                  shadows.get_data().step_count);
}

void Instance::set_time(float time)
{
  BLI_assert(render);
  DRW_render_set_time(render, depsgraph, floorf(time), fractf(time));
  update_eval_members();
}

void Instance::update_eval_members()
{
  scene = DEG_get_evaluated_scene(depsgraph);
  view_layer = DEG_get_evaluated_view_layer(depsgraph);
  camera_eval_object = (camera_orig_object) ?
                           DEG_get_evaluated_object(depsgraph, camera_orig_object) :
                           nullptr;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Sync
 *
 * Sync will gather data from the scene that can change over a time step (i.e: motion steps).
 * IMPORTANT: xxx.sync() functions area responsible for creating DRW resources as
 * well as querying temp texture pool. All DRWPasses should be ready by the end end_sync().
 * \{ */

void Instance::begin_sync()
{
  if (skip_render_) {
    return;
  }

  /* Needs to be first for sun light parameters. */
  world.sync();

  materials.begin_sync();
  velocity.begin_sync(); /* NOTE: Also syncs camera. */
  lights.begin_sync();
  shadows.begin_sync();
  volume.begin_sync();
  pipelines.begin_sync();
  cryptomatte.begin_sync();
  sphere_probes.begin_sync();
  light_probes.begin_sync();

  depth_of_field.sync();
  raytracing.sync();
  motion_blur.sync();
  hiz_buffer.sync();
  main_view.sync();
  film.sync();
  ambient_occlusion.sync();
  volume_probes.sync();
  lookdev.sync();

  use_surfaces = (view_layer->layflag & SCE_LAY_SOLID) != 0;
  use_curves = (view_layer->layflag & SCE_LAY_STRAND) != 0;
  use_volumes = (view_layer->layflag & SCE_LAY_VOLUMES) != 0;

  if (is_light_bake) {
    /* Do not use render layer visibility during bake.
     * NOTE: This is arbitrary and could be changed if needed. */
    use_surfaces = use_curves = use_volumes = true;
  }

  if (is_viewport() && velocity.camera_has_motion()) {
    sampling.reset();
  }
}

void Instance::object_sync(ObjectRef &ob_ref, Manager & /*manager*/)
{
  if (skip_render_) {
    return;
  }

  Object *ob = ob_ref.object;
  const bool is_renderable_type = ELEM(ob->type,
                                       OB_CURVES,
                                       OB_GREASE_PENCIL,
                                       OB_MESH,
                                       OB_POINTCLOUD,
                                       OB_VOLUME,
                                       OB_LAMP,
                                       OB_LIGHTPROBE);
  const int ob_visibility = DRW_object_visibility_in_active_context(ob);
  const bool partsys_is_visible = (ob_visibility & OB_VISIBLE_PARTICLES) != 0 &&
                                  (ob->type == OB_MESH);
  const bool object_is_visible = DRW_object_is_renderable(ob) &&
                                 (ob_visibility & OB_VISIBLE_SELF) != 0;

  if (!is_renderable_type || (!partsys_is_visible && !object_is_visible)) {
    return;
  }

  ObjectHandle &ob_handle = sync.sync_object(ob_ref);

  if (partsys_is_visible && ob != draw_ctx->object_edit) {
    auto sync_hair =
        [&](ObjectHandle hair_handle, ModifierData &md, ParticleSystem &particle_sys) {
          ResourceHandle _res_handle = manager->resource_handle_for_psys(ob_ref,
                                                                         ob->object_to_world());
          sync.sync_curves(ob, hair_handle, ob_ref, _res_handle, &md, &particle_sys);
        };
    foreach_hair_particle_handle(ob, ob_handle, sync_hair);
  }

  if (object_is_visible) {
    switch (ob->type) {
      case OB_LAMP:
        lights.sync_light(ob, ob_handle);
        break;
      case OB_MESH:
        if (!sync.sync_sculpt(ob, ob_handle, ob_ref)) {
          sync.sync_mesh(ob, ob_handle, ob_ref);
        }
        break;
      case OB_POINTCLOUD:
        sync.sync_pointcloud(ob, ob_handle, ob_ref);
        break;
      case OB_VOLUME:
        sync.sync_volume(ob, ob_handle, ob_ref);
        break;
      case OB_CURVES:
        sync.sync_curves(ob, ob_handle, ob_ref);
        break;
      case OB_LIGHTPROBE:
        light_probes.sync_probe(ob, ob_handle);
        break;
      default:
        break;
    }
  }
}

void Instance::end_sync()
{
  if (skip_render_) {
    return;
  }

  velocity.end_sync();
  volume.end_sync();  /* Needs to be before shadows. */
  shadows.end_sync(); /* Needs to be before lights. */
  lights.end_sync();
  sampling.end_sync();
  subsurface.end_sync();
  film.end_sync();
  cryptomatte.end_sync();
  pipelines.end_sync();
  light_probes.end_sync();
  sphere_probes.end_sync();
  planar_probes.end_sync();

  uniform_data.push_update();

  depsgraph_last_update_ = DEG_get_update_count(depsgraph);
}

void Instance::render_sync()
{
  manager->begin_sync();

  begin_sync();

  DRW_render_object_iter(
      render, depsgraph, [this](blender::draw::ObjectRef &ob_ref, RenderEngine *, Depsgraph *) {
        this->object_sync(ob_ref, *this->manager);
      });

  velocity.geometry_steps_fill();

  end_sync();

  manager->end_sync();
}

bool Instance::needs_lightprobe_sphere_passes() const
{
  return sphere_probes.update_probes_this_sample_;
}

bool Instance::do_lightprobe_sphere_sync() const
{
  return (materials.queued_shaders_count == 0) && needs_lightprobe_sphere_passes();
}

bool Instance::needs_planar_probe_passes() const
{
  return planar_probes.update_probes_;
}

bool Instance::do_planar_probe_sync() const
{
  return (materials.queued_shaders_count == 0) && needs_planar_probe_passes();
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Rendering
 * \{ */

void Instance::render_sample()
{
  if (sampling.finished_viewport()) {
    DRW_submission_start();
    film.display();
    lookdev.display();
    DRW_submission_end();
    return;
  }

  /* Motion blur may need to do re-sync after a certain number of sample. */
  if (!is_viewport() && sampling.do_render_sync()) {
    render_sync();
    while (materials.queued_shaders_count > 0) {
      /* Leave some time for shaders to compile. */
      BLI_time_sleep_ms(50);
      /** WORKAROUND: Re-sync to check if all shaders are already compiled. */
      render_sync();
    }
  }

  DebugScope debug_scope(debug_scope_render_sample, "EEVEE.render_sample");

  {
    /* Critical section. Potential GPUShader concurrent usage. */
    DRW_submission_start();

    sampling.step();

    capture_view.render_world();
    capture_view.render_probes();

    main_view.render();

    lookdev_view.render();

    DRW_submission_end();
  }
  motion_blur.step();
}

void Instance::render_read_result(RenderLayer *render_layer, const char *view_name)
{
  eViewLayerEEVEEPassType pass_bits = film.enabled_passes_get();

  for (auto i : IndexRange(EEVEE_RENDER_PASS_MAX_BIT + 1)) {
    eViewLayerEEVEEPassType pass_type = eViewLayerEEVEEPassType(pass_bits & (1 << i));
    if (pass_type == 0) {
      continue;
    }

    Vector<std::string> pass_names = Film::pass_to_render_pass_names(pass_type, view_layer);
    for (int64_t pass_offset : IndexRange(pass_names.size())) {
      RenderPass *rp = RE_pass_find_by_name(
          render_layer, pass_names[pass_offset].c_str(), view_name);
      if (!rp) {
        continue;
      }
      float *result = film.read_pass(pass_type, pass_offset);

      if (result) {
        BLI_mutex_lock(&render->update_render_passes_mutex);
        /* WORKAROUND: We use texture read to avoid using a frame-buffer to get the render result.
         * However, on some implementation, we need a buffer with a few extra bytes for the read to
         * happen correctly (see #GLTexture::read()). So we need a custom memory allocation. */
        /* Avoid `memcpy()`, replace the pointer directly. */
        RE_pass_set_buffer_data(rp, result);
        BLI_mutex_unlock(&render->update_render_passes_mutex);
      }
    }
  }

  /* AOVs. */
  LISTBASE_FOREACH (ViewLayerAOV *, aov, &view_layer->aovs) {
    if ((aov->flag & AOV_CONFLICT) != 0) {
      continue;
    }
    RenderPass *rp = RE_pass_find_by_name(render_layer, aov->name, view_name);
    if (!rp) {
      continue;
    }
    float *result = film.read_aov(aov);

    if (result) {
      BLI_mutex_lock(&render->update_render_passes_mutex);
      /* WORKAROUND: We use texture read to avoid using a frame-buffer to get the render result.
       * However, on some implementation, we need a buffer with a few extra bytes for the read to
       * happen correctly (see #GLTexture::read()). So we need a custom memory allocation. */
      /* Avoid #memcpy(), replace the pointer directly. */
      RE_pass_set_buffer_data(rp, result);
      BLI_mutex_unlock(&render->update_render_passes_mutex);
    }
  }

  /* The vector pass is initialized to weird values. Set it to neutral value if not rendered. */
  if ((pass_bits & EEVEE_RENDER_PASS_VECTOR) == 0) {
    for (const std::string &vector_pass_name :
         Film::pass_to_render_pass_names(EEVEE_RENDER_PASS_VECTOR, view_layer))
    {
      RenderPass *vector_rp = RE_pass_find_by_name(
          render_layer, vector_pass_name.c_str(), view_name);
      if (vector_rp) {
        memset(vector_rp->ibuf->float_buffer.data,
               0,
               sizeof(float) * 4 * vector_rp->rectx * vector_rp->recty);
      }
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Interface
 * \{ */

void Instance::render_frame(RenderEngine *engine, RenderLayer *render_layer, const char *view_name)
{
  if (skip_render_) {
    if (!info_.empty()) {
      RE_engine_set_error_message(engine, info_.c_str());
      info_ = "";
    }
    return;
  }
  /* TODO: Break on RE_engine_test_break(engine) */
  while (!sampling.finished()) {
    this->render_sample();

    if ((sampling.sample_index() == 1) || ((sampling.sample_index() % 25) == 0) ||
        sampling.finished())
    {
      /* TODO: Use `fmt`. */
      std::string re_info = "Rendering " + std::to_string(sampling.sample_index()) + " / " +
                            std::to_string(sampling.sample_count()) + " samples";
      RE_engine_update_stats(engine, nullptr, re_info.c_str());
    }

    /* Perform render step between samples to allow
     * flushing of freed GPUBackend resources. */
    if (GPU_backend_get_type() == GPU_BACKEND_METAL) {
      GPU_flush();
    }
    GPU_render_step();

#if 0
    /* TODO(fclem) print progression. */
    RE_engine_update_progress(engine, float(sampling.sample_index()) / float(sampling.sample_count()));
    /* TODO(fclem): Does not currently work. But would be better to just display to 2D view like
     * cycles does. */
    if (G.background == false && first_read) {
      /* Allow to preview the first sample. */
      /* TODO(fclem): Might want to not do this during animation render to avoid too much stall. */
      this->render_read_result(render_layer, view_name);
      first_read = false;
      DRW_render_context_disable(render->re);
      /* Allow the 2D viewport to grab the ticket mutex to display the render. */
      DRW_render_context_enable(render->re);
    }
#endif
  }

  this->film.cryptomatte_sort();

  this->render_read_result(render_layer, view_name);

  if (!info_.empty()) {
    RE_engine_set_error_message(
        engine, RPT_("Errors during render. See the System Console for more info."));
    printf("%s", info_.c_str());
    info_ = "";
  }
}

void Instance::draw_viewport()
{
  if (skip_render_) {
    DefaultFramebufferList *dfbl = draw_ctx->viewport_framebuffer_list_get();
    GPU_framebuffer_clear_color_depth(dfbl->default_fb, float4(0.0f), 1.0f);
    if (!shaders_are_ready_) {
      info_append_i18n("Compiling EEVEE engine shaders");
      DRW_viewport_request_redraw();
    }
    return;
  }

  render_sample();
  velocity.step_swap();

  if (is_viewport_compositor_enabled) {
    this->film.write_viewport_compositor_passes();
  }

  /* Do not request redraw during viewport animation to lock the frame-rate to the animation
   * playback rate. This is in order to preserve motion blur aspect and also to avoid TAA reset
   * that can show flickering. */
  if (!sampling.finished_viewport() && !is_playback) {
    DRW_viewport_request_redraw();
  }

  if (materials.queued_shaders_count > 0) {
    info_append_i18n("Compiling shaders ({} remaining)", materials.queued_shaders_count);

    if (!GPU_use_parallel_compilation() &&
        GPU_type_matches_ex(GPU_DEVICE_ANY, GPU_OS_ANY, GPU_DRIVER_ANY, GPU_BACKEND_OPENGL))
    {
      info_append_i18n(
          "Increasing Preferences > System > Max Shader Compilation Subprocesses may improve "
          "compilation time.");
    }
    DRW_viewport_request_redraw();
  }
  else if (materials.queued_optimize_shaders_count > 0) {
    info_append_i18n("Optimizing shaders ({} remaining)", materials.queued_optimize_shaders_count);
  }
}

void Instance::draw_viewport_image_render()
{
  if (skip_render_) {
    return;
  }
  while (!sampling.finished_viewport()) {
    this->render_sample();
  }
  velocity.step_swap();

  if (is_viewport_compositor_enabled) {
    this->film.write_viewport_compositor_passes();
  }
}

void Instance::draw(Manager & /*manager*/)
{
  if (is_viewport_image_render) {
    draw_viewport_image_render();
  }
  else {
    draw_viewport();
  }
  STRNCPY(info, info_get());
  DefaultFramebufferList *dfbl = draw_ctx->viewport_framebuffer_list_get();
  GPU_framebuffer_viewport_reset(dfbl->default_fb);
}

void Instance::store_metadata(RenderResult *render_result)
{
  if (skip_render_) {
    return;
  }
  cryptomatte.store_metadata(render_result);
}

void Instance::update_passes(RenderEngine *engine, Scene *scene, ViewLayer *view_layer)
{
  RE_engine_register_pass(engine, scene, view_layer, RE_PASSNAME_COMBINED, 4, "RGBA", SOCK_RGBA);

#define CHECK_PASS_LEGACY(name, type, channels, chanid) \
  if (view_layer->passflag & (SCE_PASS_##name)) { \
    RE_engine_register_pass( \
        engine, scene, view_layer, RE_PASSNAME_##name, channels, chanid, type); \
  } \
  ((void)0)
#define CHECK_PASS_EEVEE(name, type, channels, chanid) \
  if (view_layer->eevee.render_passes & (EEVEE_RENDER_PASS_##name)) { \
    RE_engine_register_pass( \
        engine, scene, view_layer, RE_PASSNAME_##name, channels, chanid, type); \
  } \
  ((void)0)

  CHECK_PASS_LEGACY(Z, SOCK_FLOAT, 1, "Z");
  CHECK_PASS_LEGACY(MIST, SOCK_FLOAT, 1, "Z");
  CHECK_PASS_LEGACY(NORMAL, SOCK_VECTOR, 3, "XYZ");
  CHECK_PASS_LEGACY(POSITION, SOCK_VECTOR, 3, "XYZ");
  CHECK_PASS_LEGACY(VECTOR, SOCK_VECTOR, 4, "XYZW");
  CHECK_PASS_LEGACY(DIFFUSE_DIRECT, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_LEGACY(DIFFUSE_COLOR, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_LEGACY(GLOSSY_DIRECT, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_LEGACY(GLOSSY_COLOR, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_EEVEE(VOLUME_LIGHT, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_LEGACY(EMIT, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_LEGACY(ENVIRONMENT, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_LEGACY(SHADOW, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_LEGACY(AO, SOCK_RGBA, 3, "RGB");
  CHECK_PASS_EEVEE(TRANSPARENT, SOCK_RGBA, 4, "RGBA");

  LISTBASE_FOREACH (ViewLayerAOV *, aov, &view_layer->aovs) {
    if ((aov->flag & AOV_CONFLICT) != 0) {
      continue;
    }
    switch (aov->type) {
      case AOV_TYPE_COLOR:
        RE_engine_register_pass(engine, scene, view_layer, aov->name, 4, "RGBA", SOCK_RGBA);
        break;
      case AOV_TYPE_VALUE:
        RE_engine_register_pass(engine, scene, view_layer, aov->name, 1, "X", SOCK_FLOAT);
        break;
      default:
        break;
    }
  }

  /* NOTE: Name channels lowercase `rgba` so that compression rules check in OpenEXR DWA code uses
   * lossless compression. Reportedly this naming is the only one which works good from the
   * interoperability point of view. Using `xyzw` naming is not portable. */
  auto register_cryptomatte_passes = [&](eViewLayerCryptomatteFlags cryptomatte_layer,
                                         eViewLayerEEVEEPassType eevee_pass) {
    if (view_layer->cryptomatte_flag & cryptomatte_layer) {
      for (const std::string &pass_name : Film::pass_to_render_pass_names(eevee_pass, view_layer))
      {
        RE_engine_register_pass(
            engine, scene, view_layer, pass_name.c_str(), 4, "rgba", SOCK_RGBA);
      }
    }
  };
  register_cryptomatte_passes(VIEW_LAYER_CRYPTOMATTE_OBJECT, EEVEE_RENDER_PASS_CRYPTOMATTE_OBJECT);
  register_cryptomatte_passes(VIEW_LAYER_CRYPTOMATTE_ASSET, EEVEE_RENDER_PASS_CRYPTOMATTE_ASSET);
  register_cryptomatte_passes(VIEW_LAYER_CRYPTOMATTE_MATERIAL,
                              EEVEE_RENDER_PASS_CRYPTOMATTE_MATERIAL);
}

void Instance::light_bake_irradiance(
    Object &probe,
    FunctionRef<void()> context_enable,
    FunctionRef<void()> context_disable,
    FunctionRef<bool()> stop,
    FunctionRef<void(LightProbeGridCacheFrame *, float progress)> result_update)
{
  BLI_assert(is_baking());

  DRWContext draw_ctx(DRWContext::CUSTOM, depsgraph);
  this->draw_ctx = &draw_ctx;

  auto custom_pipeline_wrapper = [&](FunctionRef<void()> callback) {
    context_enable();
    DRW_custom_pipeline_begin(draw_ctx, depsgraph);
    callback();
    DRW_custom_pipeline_end(draw_ctx);
    context_disable();
  };

  auto context_wrapper = [&](FunctionRef<void()> callback) {
    context_enable();
    callback();
    context_disable();
  };

  volume_probes.bake.init(probe);

  custom_pipeline_wrapper([&]() {
    this->render_sync();
    while (materials.queued_shaders_count > 0) {
      /* Leave some time for shaders to compile. */
      BLI_time_sleep_ms(50);
      /** WORKAROUND: Re-sync to check if all shaders are already compiled. */
      this->render_sync();
    }
    /* Sampling module needs to be initialized to computing lighting. */
    sampling.init(probe);
    sampling.step();

    {
      /* Critical section. Potential GPUShader concurrent usage. */
      DRW_submission_start();

      DebugScope debug_scope(debug_scope_irradiance_setup, "EEVEE.irradiance_setup");

      capture_view.render_world();

      volume_probes.bake.surfels_create(probe);

      if (volume_probes.bake.should_break()) {
        DRW_submission_end();
        return;
      }

      volume_probes.bake.surfels_lights_eval();

      volume_probes.bake.clusters_build();
      volume_probes.bake.irradiance_offset();

      DRW_submission_end();
    }
  });

  if (volume_probes.bake.should_break()) {
    return;
  }

  sampling.init(probe);
  while (!sampling.finished()) {
    context_wrapper([&]() {
      DebugScope debug_scope(debug_scope_irradiance_sample, "EEVEE.irradiance_sample");

      /* Batch ray cast by pack of 16. Avoids too much overhead of the update function & context
       * switch. */
      /* TODO(fclem): Could make the number of iteration depend on the computation time. */
      for (int i = 0; i < 16 && !sampling.finished(); i++) {
        sampling.step();
        {
          /* Critical section. Potential GPUShader concurrent usage. */
          DRW_submission_start();

          volume_probes.bake.raylists_build();
          volume_probes.bake.propagate_light();
          volume_probes.bake.irradiance_capture();

          DRW_submission_end();
        }
      }

      LightProbeGridCacheFrame *cache_frame;
      if (sampling.finished()) {
        cache_frame = volume_probes.bake.read_result_packed();
      }
      else {
        /* TODO(fclem): Only do this read-back if needed. But it might be tricky to know when. */
        cache_frame = volume_probes.bake.read_result_unpacked();
      }

      float progress = sampling.sample_index() / float(sampling.sample_count());
      result_update(cache_frame, progress);
    });

    if (stop()) {
      return;
    }
  }
}

/** \} */

}  // namespace blender::eevee
