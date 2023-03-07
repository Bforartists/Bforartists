/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_editmesh.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_paint.h"
#include "BKE_particle.h"
#include "BKE_pbvh.h"
#include "BKE_report.h"
#include "DEG_depsgraph_query.h"
#include "DNA_fluid_types.h"
#include "ED_paint.h"
#include "ED_view3d.h"
#include "GPU_capabilities.h"

#include "workbench_private.hh"

#include "workbench_engine.h" /* Own include. */

namespace blender::workbench {

using namespace draw;

class Instance {
 public:
  View view = {"DefaultView"};

  SceneState scene_state;

  SceneResources resources;

  OpaquePass opaque_ps;
  TransparentPass transparent_ps;
  TransparentDepthPass transparent_depth_ps;

  ShadowPass shadow_ps;
  OutlinePass outline_ps;
  DofPass dof_ps;
  AntiAliasingPass anti_aliasing_ps;

  /* An array of nullptr GPUMaterial pointers so we can call DRW_cache_object_surface_material_get.
   * They never get actually used. */
  Vector<GPUMaterial *> dummy_gpu_materials = {1, nullptr, {}};
  GPUMaterial **get_dummy_gpu_materials(int material_count)
  {
    if (material_count > dummy_gpu_materials.size()) {
      dummy_gpu_materials.resize(material_count, nullptr);
    }
    return dummy_gpu_materials.begin();
  };

  void init(Object *camera_ob = nullptr)
  {
    scene_state.init(camera_ob);
    shadow_ps.init(scene_state, resources);
    resources.init(scene_state);

    outline_ps.init(scene_state);
    dof_ps.init(scene_state);
    anti_aliasing_ps.init(scene_state);
  }

  void begin_sync()
  {
    const float2 viewport_size = DRW_viewport_size_get();
    const int2 resolution = {int(viewport_size.x), int(viewport_size.y)};
    resources.depth_tx.ensure_2d(GPU_DEPTH24_STENCIL8,
                                 resolution,
                                 GPU_TEXTURE_USAGE_SHADER_READ | GPU_TEXTURE_USAGE_ATTACHMENT |
                                     GPU_TEXTURE_USAGE_MIP_SWIZZLE_VIEW);
    resources.material_buf.clear();

    opaque_ps.sync(scene_state, resources);
    transparent_ps.sync(scene_state, resources);
    transparent_depth_ps.sync(scene_state, resources);

    shadow_ps.sync();
    outline_ps.sync(resources);
    dof_ps.sync(resources);
    anti_aliasing_ps.sync(resources, scene_state.resolution);
  }

  void end_sync()
  {
    resources.material_buf.push_update();
  }

  void object_sync(Manager &manager, ObjectRef &ob_ref)
  {
    if (scene_state.render_finished) {
      return;
    }

    Object *ob = ob_ref.object;
    if (!DRW_object_is_renderable(ob)) {
      return;
    }

    const ObjectState object_state = ObjectState(scene_state, ob);

    /* Needed for mesh cache validation, to prevent two copies of
     * of vertex color arrays from being sent to the GPU (e.g.
     * when switching from eevee to workbench).
     */
    if (ob_ref.object->sculpt && ob_ref.object->sculpt->pbvh) {
      BKE_pbvh_is_drawing_set(ob_ref.object->sculpt->pbvh, object_state.sculpt_pbvh);
    }

    if (ob->type == OB_MESH && ob->modifiers.first != nullptr) {

      LISTBASE_FOREACH (ModifierData *, md, &ob->modifiers) {
        if (md->type != eModifierType_ParticleSystem) {
          continue;
        }
        ParticleSystem *psys = ((ParticleSystemModifierData *)md)->psys;
        if (!DRW_object_is_visible_psys_in_active_context(ob, psys)) {
          continue;
        }
        ParticleSettings *part = psys->part;
        const int draw_as = (part->draw_as == PART_DRAW_REND) ? part->ren_as : part->draw_as;

        if (draw_as == PART_DRAW_PATH) {
#if 0 /* TODO(@pragma37): */
          workbench_cache_hair_populate(wpd,
                                        ob,
                                        psys,
                                        md,
                                        object_state.color_type,
                                        object_state.texture_paint_mode,
                                        part->omat);
#endif
        }
      }
    }

    if (!(ob->base_flag & BASE_FROM_DUPLI)) {
      ModifierData *md = BKE_modifiers_findby_type(ob, eModifierType_Fluid);
      if (md && BKE_modifier_is_enabled(scene_state.scene, md, eModifierMode_Realtime)) {
        FluidModifierData *fmd = (FluidModifierData *)md;
        if (fmd->domain) {
#if 0 /* TODO(@pragma37): */
          workbench_volume_cache_populate(vedata, wpd->scene, ob, md, V3D_SHADING_SINGLE_COLOR);
#endif
          if (fmd->domain->type == FLUID_DOMAIN_TYPE_GAS) {
            return; /* Do not draw solid in this case. */
          }
        }
      }
    }

    if (!(DRW_object_visibility_in_active_context(ob) & OB_VISIBLE_SELF)) {
      return;
    }

    if ((ob->dt < OB_SOLID) && !DRW_state_is_scene_render()) {
      return;
    }

    if (ELEM(ob->type, OB_MESH, OB_POINTCLOUD)) {
      mesh_sync(manager, ob_ref, object_state);
    }
    else if (ob->type == OB_CURVES) {
#if 0 /* TODO(@pragma37): */
      DRWShadingGroup *grp = workbench_material_hair_setup(
          wpd, ob, CURVES_MATERIAL_NR, object_state.color_type);
      DRW_shgroup_curves_create_sub(ob, grp, NULL);
#endif
    }
    else if (ob->type == OB_VOLUME) {
      if (scene_state.shading.type != OB_WIRE) {
#if 0 /* TODO(@pragma37): */
        workbench_volume_cache_populate(vedata, wpd->scene, ob, NULL, object_state.color_type);
#endif
      }
    }
  }

  void mesh_sync(Manager &manager, ObjectRef &ob_ref, const ObjectState &object_state)
  {
    ResourceHandle handle = manager.resource_handle(ob_ref);
    bool has_transparent_material = false;

    if (object_state.sculpt_pbvh) {
#if 0 /* TODO(@pragma37): */
      workbench_cache_sculpt_populate(wpd, ob, object_state.color_type);
#endif
    }
    else {
      if (object_state.use_per_material_batches) {
        const int material_count = DRW_cache_object_material_count_get(ob_ref.object);

        struct GPUBatch **batches;
        if (object_state.color_type == V3D_SHADING_TEXTURE_COLOR) {
          batches = DRW_cache_mesh_surface_texpaint_get(ob_ref.object);
        }
        else {
          batches = DRW_cache_object_surface_material_get(
              ob_ref.object, get_dummy_gpu_materials(material_count), material_count);
        }

        if (batches) {
          for (auto i : IndexRange(material_count)) {
            if (batches[i] == nullptr) {
              continue;
            }

            Material mat;

            if (::Material *_mat = BKE_object_material_get_eval(ob_ref.object, i + 1)) {
              mat = Material(*_mat);
            }
            else {
              mat = Material(*BKE_material_default_empty());
            }

            has_transparent_material = has_transparent_material || mat.is_transparent();

            ::Image *image = nullptr;
            ImageUser *iuser = nullptr;
            eGPUSamplerState sampler_state = eGPUSamplerState::GPU_SAMPLER_DEFAULT;
            if (object_state.color_type == V3D_SHADING_TEXTURE_COLOR) {
              get_material_image(ob_ref.object, i + 1, image, iuser, sampler_state);
            }

            draw_mesh(ob_ref, mat, batches[i], handle, image, sampler_state, iuser);
          }
        }
      }
      else {
        struct GPUBatch *batch;
        if (object_state.color_type == V3D_SHADING_TEXTURE_COLOR) {
          batch = DRW_cache_mesh_surface_texpaint_single_get(ob_ref.object);
        }
        else if (object_state.color_type == V3D_SHADING_VERTEX_COLOR) {
          if (ob_ref.object->mode & OB_MODE_VERTEX_PAINT) {
            batch = DRW_cache_mesh_surface_vertpaint_get(ob_ref.object);
          }
          else {
            batch = DRW_cache_mesh_surface_sculptcolors_get(ob_ref.object);
          }
        }
        else {
          batch = DRW_cache_object_surface_get(ob_ref.object);
        }

        if (batch) {
          Material mat;

          if (object_state.color_type == V3D_SHADING_OBJECT_COLOR) {
            mat = Material(*ob_ref.object);
          }
          else if (object_state.color_type == V3D_SHADING_RANDOM_COLOR) {
            mat = Material(*ob_ref.object, true);
          }
          else if (object_state.color_type == V3D_SHADING_SINGLE_COLOR) {
            mat = scene_state.material_override;
          }
          else if (object_state.color_type == V3D_SHADING_VERTEX_COLOR) {
            mat = scene_state.material_attribute_color;
          }
          else {
            mat = Material(*BKE_material_default_empty());
          }

          has_transparent_material = has_transparent_material || mat.is_transparent();

          draw_mesh(ob_ref,
                    mat,
                    batch,
                    handle,
                    object_state.image_paint_override,
                    object_state.override_sampler_state);
        }
      }
    }

    if (object_state.draw_shadow) {
      shadow_ps.object_sync(scene_state, ob_ref, handle, has_transparent_material);
    }
  }

  void draw_mesh(ObjectRef &ob_ref,
                 Material &material,
                 GPUBatch *batch,
                 ResourceHandle handle,
                 ::Image *image = nullptr,
                 eGPUSamplerState sampler_state = GPU_SAMPLER_DEFAULT,
                 ImageUser *iuser = nullptr)
  {
    const bool in_front = (ob_ref.object->dtx & OB_DRAW_IN_FRONT) != 0;
    resources.material_buf.append(material);
    int material_index = resources.material_buf.size() - 1;

    auto draw = [&](MeshPass &pass) {
      pass.draw(ob_ref, batch, handle, material_index, image, sampler_state, iuser);
    };

    if (scene_state.xray_mode || material.is_transparent()) {
      if (in_front) {
        draw(transparent_ps.accumulation_in_front_ps_);
        if (scene_state.draw_transparent_depth) {
          draw(transparent_depth_ps.in_front_ps_);
        }
      }
      else {
        draw(transparent_ps.accumulation_ps_);
        if (scene_state.draw_transparent_depth) {
          draw(transparent_depth_ps.main_ps_);
        }
      }
    }
    else {
      if (in_front) {
        draw(opaque_ps.gbuffer_in_front_ps_);
      }
      else {
        draw(opaque_ps.gbuffer_ps_);
      }
    }
  }

  void draw(Manager &manager, GPUTexture *depth_tx, GPUTexture *color_tx)
  {
    view.sync(DRW_view_default_get());

    int2 resolution = scene_state.resolution;

    if (scene_state.render_finished) {
      /* Just copy back the already rendered result */
      anti_aliasing_ps.draw(manager, view, resources, resolution, depth_tx, color_tx);
      return;
    }

    anti_aliasing_ps.setup_view(view, resolution);

    resources.color_tx.acquire(
        resolution, GPU_RGBA16F, GPU_TEXTURE_USAGE_SHADER_READ | GPU_TEXTURE_USAGE_ATTACHMENT);
    resources.color_tx.clear(resources.world_buf.background_color);
    if (scene_state.draw_object_id) {
      resources.object_id_tx.acquire(
          resolution, GPU_R16UI, GPU_TEXTURE_USAGE_SHADER_READ | GPU_TEXTURE_USAGE_ATTACHMENT);
      resources.object_id_tx.clear(uint4(0));
    }

    Framebuffer fb = Framebuffer("Workbench.Clear");
    fb.ensure(GPU_ATTACHMENT_TEXTURE(resources.depth_tx));
    fb.bind();
    GPU_framebuffer_clear_depth_stencil(fb, 1.0f, 0x00);

    if (!transparent_ps.accumulation_in_front_ps_.is_empty()) {
      resources.depth_in_front_tx.acquire(resolution,
                                          GPU_DEPTH24_STENCIL8,
                                          GPU_TEXTURE_USAGE_SHADER_READ |
                                              GPU_TEXTURE_USAGE_ATTACHMENT);
      if (opaque_ps.gbuffer_in_front_ps_.is_empty()) {
        /* Clear only if it wont be overwritten by `opaque_ps`. */
        Framebuffer fb = Framebuffer("Workbench.Clear");
        fb.ensure(GPU_ATTACHMENT_TEXTURE(resources.depth_in_front_tx));
        fb.bind();
        GPU_framebuffer_clear_depth_stencil(fb, 1.0f, 0x00);
      }
    }

    opaque_ps.draw(manager,
                   view,
                   resources,
                   resolution,
                   &shadow_ps,
                   transparent_ps.accumulation_ps_.is_empty());
    transparent_ps.draw(manager, view, resources, resolution);
    transparent_depth_ps.draw(manager, view, resources);

    // volume_ps.draw_prepass(manager, view, resources.depth_tx);

    outline_ps.draw(manager, resources);
    dof_ps.draw(manager, view, resources, resolution);
    anti_aliasing_ps.draw(manager, view, resources, resolution, depth_tx, color_tx);

    resources.color_tx.release();
    resources.object_id_tx.release();
    resources.depth_in_front_tx.release();
  }

  void draw_viewport(Manager &manager, GPUTexture *depth_tx, GPUTexture *color_tx)
  {
    this->draw(manager, depth_tx, color_tx);

    if (scene_state.sample + 1 < scene_state.samples_len) {
      DRW_viewport_request_redraw();
    }
  }
};

}  // namespace blender::workbench

/* -------------------------------------------------------------------- */
/** \name Interface with legacy C DRW manager
 * \{ */

using namespace blender;

struct WORKBENCH_Data {
  DrawEngineType *engine_type;
  DRWViewportEmptyList *fbl;
  DRWViewportEmptyList *txl;
  DRWViewportEmptyList *psl;
  DRWViewportEmptyList *stl;
  workbench::Instance *instance;

  char info[GPU_INFO_SIZE];
};

static void workbench_engine_init(void *vedata)
{
  /* TODO(fclem): Remove once it is minimum required. */
  if (!GPU_shader_storage_buffer_objects_support()) {
    return;
  }

  WORKBENCH_Data *ved = reinterpret_cast<WORKBENCH_Data *>(vedata);
  if (ved->instance == nullptr) {
    ved->instance = new workbench::Instance();
  }

  ved->instance->init();
}

static void workbench_cache_init(void *vedata)
{
  if (!GPU_shader_storage_buffer_objects_support()) {
    return;
  }
  reinterpret_cast<WORKBENCH_Data *>(vedata)->instance->begin_sync();
}

static void workbench_cache_populate(void *vedata, Object *object)
{
  if (!GPU_shader_storage_buffer_objects_support()) {
    return;
  }
  draw::Manager *manager = DRW_manager_get();

  draw::ObjectRef ref;
  ref.object = object;
  ref.dupli_object = DRW_object_get_dupli(object);
  ref.dupli_parent = DRW_object_get_dupli_parent(object);

  reinterpret_cast<WORKBENCH_Data *>(vedata)->instance->object_sync(*manager, ref);
}

static void workbench_cache_finish(void *vedata)
{
  if (!GPU_shader_storage_buffer_objects_support()) {
    return;
  }
  reinterpret_cast<WORKBENCH_Data *>(vedata)->instance->end_sync();
}

static void workbench_draw_scene(void *vedata)
{
  WORKBENCH_Data *ved = reinterpret_cast<WORKBENCH_Data *>(vedata);
  if (!GPU_shader_storage_buffer_objects_support()) {
    STRNCPY(ved->info, "Error: No shader storage buffer support");
    return;
  }
  DefaultTextureList *dtxl = DRW_viewport_texture_list_get();
  draw::Manager *manager = DRW_manager_get();
  ved->instance->draw_viewport(*manager, dtxl->depth, dtxl->color);
}

static void workbench_instance_free(void *instance)
{
  if (!GPU_shader_storage_buffer_objects_support()) {
    return;
  }
  delete reinterpret_cast<workbench::Instance *>(instance);
}

static void workbench_view_update(void *vedata)
{
  WORKBENCH_Data *ved = reinterpret_cast<WORKBENCH_Data *>(vedata);
  if (ved->instance) {
    ved->instance->scene_state.reset_taa_next_sample = true;
  }
}

static void workbench_id_update(void *vedata, struct ID *id)
{
  UNUSED_VARS(vedata, id);
}

/* RENDER */

static bool workbench_render_framebuffers_init(void)
{
  /* For image render, allocate own buffers because we don't have a viewport. */
  const float2 viewport_size = DRW_viewport_size_get();
  const int2 size = {int(viewport_size.x), int(viewport_size.y)};

  DefaultTextureList *dtxl = DRW_viewport_texture_list_get();

  /* When doing a multi view rendering the first view will allocate the buffers
   * the other views will reuse these buffers */
  if (dtxl->color == nullptr) {
    BLI_assert(dtxl->depth == nullptr);
    eGPUTextureUsage usage = GPU_TEXTURE_USAGE_GENERAL;
    dtxl->color = GPU_texture_create_2d(
        "txl.color", size.x, size.y, 1, GPU_RGBA16F, usage, nullptr);
    dtxl->depth = GPU_texture_create_2d(
        "txl.depth", size.x, size.y, 1, GPU_DEPTH24_STENCIL8, usage, nullptr);
  }

  if (!(dtxl->depth && dtxl->color)) {
    return false;
  }

  DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();

  GPU_framebuffer_ensure_config(
      &dfbl->default_fb,
      {GPU_ATTACHMENT_TEXTURE(dtxl->depth), GPU_ATTACHMENT_TEXTURE(dtxl->color)});

  GPU_framebuffer_ensure_config(&dfbl->depth_only_fb,
                                {GPU_ATTACHMENT_TEXTURE(dtxl->depth), GPU_ATTACHMENT_NONE});

  GPU_framebuffer_ensure_config(&dfbl->color_only_fb,
                                {GPU_ATTACHMENT_NONE, GPU_ATTACHMENT_TEXTURE(dtxl->color)});

  return GPU_framebuffer_check_valid(dfbl->default_fb, nullptr) &&
         GPU_framebuffer_check_valid(dfbl->color_only_fb, nullptr) &&
         GPU_framebuffer_check_valid(dfbl->depth_only_fb, nullptr);
}

#ifdef DEBUG
/* This is just to ease GPU debugging when the frame delimiter is set to Finish */
#  define GPU_FINISH_DELIMITER() GPU_finish()
#else
#  define GPU_FINISH_DELIMITER()
#endif

static void write_render_color_output(struct RenderLayer *layer,
                                      const char *viewname,
                                      GPUFrameBuffer *fb,
                                      const struct rcti *rect)
{
  RenderPass *rp = RE_pass_find_by_name(layer, RE_PASSNAME_COMBINED, viewname);
  if (rp) {
    GPU_framebuffer_bind(fb);
    GPU_framebuffer_read_color(fb,
                               rect->xmin,
                               rect->ymin,
                               BLI_rcti_size_x(rect),
                               BLI_rcti_size_y(rect),
                               4,
                               0,
                               GPU_DATA_FLOAT,
                               rp->rect);
  }
}

static void write_render_z_output(struct RenderLayer *layer,
                                  const char *viewname,
                                  GPUFrameBuffer *fb,
                                  const struct rcti *rect,
                                  float4x4 winmat)
{
  RenderPass *rp = RE_pass_find_by_name(layer, RE_PASSNAME_Z, viewname);
  if (rp) {
    GPU_framebuffer_bind(fb);
    GPU_framebuffer_read_depth(fb,
                               rect->xmin,
                               rect->ymin,
                               BLI_rcti_size_x(rect),
                               BLI_rcti_size_y(rect),
                               GPU_DATA_FLOAT,
                               rp->rect);

    int pix_num = BLI_rcti_size_x(rect) * BLI_rcti_size_y(rect);

    /* Convert GPU depth [0..1] to view Z [near..far] */
    if (DRW_view_is_persp_get(nullptr)) {
      for (float &z : MutableSpan(rp->rect, pix_num)) {
        if (z == 1.0f) {
          z = 1e10f; /* Background */
        }
        else {
          z = z * 2.0f - 1.0f;
          z = winmat[3][2] / (z + winmat[2][2]);
        }
      }
    }
    else {
      /* Keep in mind, near and far distance are negatives. */
      float near = DRW_view_near_distance_get(nullptr);
      float far = DRW_view_far_distance_get(nullptr);
      float range = fabsf(far - near);

      for (float &z : MutableSpan(rp->rect, pix_num)) {
        if (z == 1.0f) {
          z = 1e10f; /* Background */
        }
        else {
          z = z * range - near;
        }
      }
    }
  }
}

static void workbench_render_to_image(void *vedata,
                                      struct RenderEngine *engine,
                                      struct RenderLayer *layer,
                                      const struct rcti *rect)
{
  /* TODO(fclem): Remove once it is minimum required. */
  if (!GPU_shader_storage_buffer_objects_support()) {
    return;
  }

  if (!workbench_render_framebuffers_init()) {
    RE_engine_report(engine, RPT_ERROR, "Failed to allocate GPU buffers");
    return;
  }

  GPU_FINISH_DELIMITER();

  /* Setup */

  DefaultFramebufferList *dfbl = DRW_viewport_framebuffer_list_get();
  const DRWContextState *draw_ctx = DRW_context_state_get();
  Depsgraph *depsgraph = draw_ctx->depsgraph;

  WORKBENCH_Data *ved = reinterpret_cast<WORKBENCH_Data *>(vedata);
  if (ved->instance == nullptr) {
    ved->instance = new workbench::Instance();
  }

  /* TODO(sergey): Shall render hold pointer to an evaluated camera instead? */
  Object *camera_ob = DEG_get_evaluated_object(depsgraph, RE_GetCamera(engine->re));

  /* Set the perspective, view and window matrix. */
  float4x4 winmat, viewmat, viewinv;
  RE_GetCameraWindow(engine->re, camera_ob, winmat.ptr());
  RE_GetCameraModelMatrix(engine->re, camera_ob, viewinv.ptr());
  viewmat = math::invert(viewinv);

  DRWView *view = DRW_view_create(viewmat.ptr(), winmat.ptr(), nullptr, nullptr, nullptr);
  DRW_view_default_set(view);
  DRW_view_set_active(view);

  /* Render */
  do {
    if (RE_engine_test_break(engine)) {
      break;
    }

    ved->instance->init(camera_ob);

    DRW_manager_get()->begin_sync();

    workbench_cache_init(vedata);
    auto workbench_render_cache = [](void *vedata,
                                     struct Object *ob,
                                     struct RenderEngine * /*engine*/,
                                     struct Depsgraph * /*depsgraph*/) {
      workbench_cache_populate(vedata, ob);
    };
    DRW_render_object_iter(vedata, engine, depsgraph, workbench_render_cache);
    workbench_cache_finish(vedata);

    DRW_manager_get()->end_sync();

    /* Also we weed to have a correct FBO bound for #DRW_curves_update */
    // GPU_framebuffer_bind(dfbl->default_fb);
    // DRW_curves_update(); /* TODO(@pragma37): Check this once curves are implemented */

    workbench_draw_scene(vedata);

    /* Perform render step between samples to allow
     * flushing of freed GPUBackend resources. */
    GPU_render_step();
    GPU_FINISH_DELIMITER();
  } while (ved->instance->scene_state.sample + 1 < ved->instance->scene_state.samples_len);

  const char *viewname = RE_GetActiveRenderView(engine->re);
  write_render_color_output(layer, viewname, dfbl->default_fb, rect);
  write_render_z_output(layer, viewname, dfbl->default_fb, rect, winmat);
}

static void workbench_render_update_passes(RenderEngine *engine,
                                           Scene *scene,
                                           ViewLayer *view_layer)
{
  if (view_layer->passflag & SCE_PASS_COMBINED) {
    RE_engine_register_pass(engine, scene, view_layer, RE_PASSNAME_COMBINED, 4, "RGBA", SOCK_RGBA);
  }
  if (view_layer->passflag & SCE_PASS_Z) {
    RE_engine_register_pass(engine, scene, view_layer, RE_PASSNAME_Z, 1, "Z", SOCK_FLOAT);
  }
}

extern "C" {

static const DrawEngineDataSize workbench_data_size = DRW_VIEWPORT_DATA_SIZE(WORKBENCH_Data);

DrawEngineType draw_engine_workbench_next = {
    nullptr,
    nullptr,
    N_("Workbench"),
    &workbench_data_size,
    &workbench_engine_init,
    nullptr,
    &workbench_instance_free,
    &workbench_cache_init,
    &workbench_cache_populate,
    &workbench_cache_finish,
    &workbench_draw_scene,
    &workbench_view_update,
    &workbench_id_update,
    &workbench_render_to_image,
    nullptr,
};

RenderEngineType DRW_engine_viewport_workbench_next_type = {
    nullptr,
    nullptr,
    "BLENDER_WORKBENCH_NEXT",
    N_("Workbench Next"),
    RE_INTERNAL | RE_USE_STEREO_VIEWPORT | RE_USE_GPU_CONTEXT,
    nullptr,
    &DRW_render_to_image,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    nullptr,
    &workbench_render_update_passes,
    &draw_engine_workbench_next,
    {nullptr, nullptr, nullptr},
};
}

/** \} */
