/* SPDX-FileCopyrightText: 2016 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup draw
 */

/* This is the Render Functions used by Realtime engines to draw with OpenGL */

#pragma once

#include "BLI_listbase.h"
#include "BLI_math_matrix.h"
#include "BLI_string.h"

#include "BKE_context.hh"
#include "BKE_layer.hh"
#include "BKE_material.h"
#include "BKE_scene.hh"

#include "BLT_translation.hh"

#include "DNA_light_types.h"
#include "DNA_material_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_world_types.h"

#include "GPU_framebuffer.hh"
#include "GPU_material.hh"
#include "GPU_primitive.hh"
#include "GPU_shader.hh"
#include "GPU_storage_buffer.hh"
#include "GPU_texture.hh"
#include "GPU_uniform_buffer.hh"

#include "draw_cache.hh"
#include "draw_common_c.hh"
#include "draw_view_c.hh"

#include "draw_debug_c.hh"
#include "draw_manager_profiling.hh"
#include "draw_state.hh"
#include "draw_view_data.hh"

#include "MEM_guardedalloc.h"

#include "RE_engine.h"

#include "DEG_depsgraph.hh"

/* Uncomment to track unused resource bindings. */
// #define DRW_UNUSED_RESOURCE_TRACKING

#ifdef DRW_UNUSED_RESOURCE_TRACKING
#  define DRW_DEBUG_FILE_LINE_ARGS , const char *file, int line
#else
#  define DRW_DEBUG_FILE_LINE_ARGS
#endif

namespace blender::gpu {
class Batch;
}
struct GPUMaterial;
struct GPUShader;
struct GPUTexture;
struct GPUUniformBuf;
struct Object;
struct ParticleSystem;
struct RenderEngineType;
struct bContext;
struct rcti;
struct TaskGraph;
namespace blender::draw {
class TextureFromPool;
}  // namespace blender::draw

typedef struct DRWPass DRWPass;
typedef struct DRWShadingGroup DRWShadingGroup;
typedef struct DRWUniform DRWUniform;

/* TODO: Put it somewhere else? */
struct BoundSphere {
  float center[3], radius;
};

/* declare members as empty (unused) */
typedef char DRWViewportEmptyList;

#define DRW_VIEWPORT_LIST_SIZE(list) \
  (sizeof(list) == sizeof(DRWViewportEmptyList) ? 0 : (sizeof(list) / sizeof(void *)))

/* Unused members must be either pass list or 'char *' when not used. */
#define DRW_VIEWPORT_DATA_SIZE(ty) \
  { \
    DRW_VIEWPORT_LIST_SIZE(*(((ty *)nullptr)->fbl)), \
        DRW_VIEWPORT_LIST_SIZE(*(((ty *)nullptr)->txl)), \
        DRW_VIEWPORT_LIST_SIZE(*(((ty *)nullptr)->psl)), \
        DRW_VIEWPORT_LIST_SIZE(*(((ty *)nullptr)->stl)), \
  }

struct DrawEngineDataSize {
  int fbl_len;
  int txl_len;
  int psl_len;
  int stl_len;
};

struct DrawEngineType {
  DrawEngineType *next, *prev;

  char idname[32];

  const DrawEngineDataSize *vedata_size;

  void (*engine_init)(void *vedata);
  void (*engine_free)();

  void (*instance_free)(void *instance_data);

  void (*cache_init)(void *vedata);
  void (*cache_populate)(void *vedata, Object *ob);
  void (*cache_finish)(void *vedata);

  void (*draw_scene)(void *vedata);

  void (*view_update)(void *vedata);
  void (*id_update)(void *vedata, ID *id);

  void (*render_to_image)(void *vedata,
                          RenderEngine *engine,
                          RenderLayer *layer,
                          const rcti *rect);
  void (*store_metadata)(void *vedata, RenderResult *render_result);
};

/* Shaders */
void DRW_shader_init();
void DRW_shader_exit();

GPUMaterial *DRW_shader_from_world(World *wo,
                                   bNodeTree *ntree,
                                   eGPUMaterialEngine engine,
                                   const uint64_t shader_id,
                                   const bool is_volume_shader,
                                   bool deferred,
                                   GPUCodegenCallbackFn callback,
                                   void *thunk);
GPUMaterial *DRW_shader_from_material(
    Material *ma,
    bNodeTree *ntree,
    eGPUMaterialEngine engine,
    const uint64_t shader_id,
    const bool is_volume_shader,
    bool deferred,
    GPUCodegenCallbackFn callback,
    void *thunk,
    GPUMaterialPassReplacementCallbackFn pass_replacement_cb = nullptr);
void DRW_shader_queue_optimize_material(GPUMaterial *mat);

/* Viewport. */

const float *DRW_viewport_size_get();
const float *DRW_viewport_invert_size_get();
const float *DRW_viewport_pixelsize_get();

DefaultFramebufferList *DRW_viewport_framebuffer_list_get();
DefaultTextureList *DRW_viewport_texture_list_get();

/* See DRW_viewport_pass_texture_get. */
blender::draw::TextureFromPool &DRW_viewport_pass_texture_get(const char *pass_name);

void DRW_viewport_request_redraw();

void DRW_render_to_image(RenderEngine *engine, Depsgraph *depsgraph);
void DRW_render_object_iter(
    void *vedata,
    RenderEngine *engine,
    Depsgraph *depsgraph,
    void (*callback)(void *vedata, Object *ob, RenderEngine *engine, Depsgraph *depsgraph));

/**
 * \warning Changing frame might free the #ViewLayerEngineData.
 */
void DRW_render_set_time(RenderEngine *engine, Depsgraph *depsgraph, int frame, float subframe);

/**
 * Assume a valid GL context is bound (and that the gl_context_mutex has been acquired).
 * This function only setup DST and execute the given function.
 * \warning similar to DRW_render_to_image you cannot use default lists (`dfbl` & `dtxl`).
 */
void DRW_custom_pipeline(DrawEngineType *draw_engine_type,
                         Depsgraph *depsgraph,
                         void (*callback)(void *vedata, void *user_data),
                         void *user_data);
/**
 * Same as `DRW_custom_pipeline` but allow better code-flow than a callback.
 */
void DRW_custom_pipeline_begin(DrawEngineType *draw_engine_type, Depsgraph *depsgraph);
void DRW_custom_pipeline_end();

/**
 * Used when the render engine want to redo another cache populate inside the same render frame.
 */
void DRW_cache_restart();

/* ViewLayers */

void *DRW_view_layer_engine_data_get(DrawEngineType *engine_type);
void **DRW_view_layer_engine_data_ensure_ex(ViewLayer *view_layer,
                                            DrawEngineType *engine_type,
                                            void (*callback)(void *storage));
void **DRW_view_layer_engine_data_ensure(DrawEngineType *engine_type,
                                         void (*callback)(void *storage));

/* DrawData */

DrawData *DRW_drawdata_get(ID *id, DrawEngineType *engine_type);
DrawData *DRW_drawdata_ensure(ID *id,
                              DrawEngineType *engine_type,
                              size_t size,
                              DrawDataInitCb init_cb,
                              DrawDataFreeCb free_cb);
/**
 * Return nullptr if not a dupli or a pointer of pointer to the engine data.
 */
void **DRW_duplidata_get(void *vedata);

/* Settings. */

bool DRW_object_is_renderable(const Object *ob);
/**
 * Does `ob` needs to be rendered in edit mode.
 *
 * When using duplicate linked meshes, objects that are not in edit-mode will be drawn as
 * it is in edit mode, when another object with the same mesh is in edit mode.
 * This will not be the case when one of the objects are influenced by modifiers.
 */
bool DRW_object_is_in_edit_mode(const Object *ob);
/**
 * Return whether this object is visible depending if
 * we are rendering or drawing in the viewport.
 */
int DRW_object_visibility_in_active_context(const Object *ob);
bool DRW_object_use_hide_faces(const Object *ob);

bool DRW_object_is_visible_psys_in_active_context(const Object *object,
                                                  const ParticleSystem *psys);

Object *DRW_object_get_dupli_parent(const Object *ob);
DupliObject *DRW_object_get_dupli(const Object *ob);

void DRW_draw_callbacks_pre_scene();
void DRW_draw_callbacks_post_scene();

/* Draw State. */

/**
 * When false, drawing doesn't output to a pixel buffer
 * eg: Occlusion queries, or when we have setup a context to draw in already.
 */
bool DRW_state_is_fbo();
/**
 * For when engines need to know if this is drawing for selection or not.
 */
bool DRW_state_is_select();
bool DRW_state_is_material_select();
bool DRW_state_is_depth();
/**
 * Whether we are rendering for an image
 */
bool DRW_state_is_image_render();
/**
 * Whether we are rendering only the render engine,
 * or if we should also render the mode engines.
 */
bool DRW_state_is_scene_render();
/**
 * Whether we are rendering simple opengl render
 */
bool DRW_state_is_viewport_image_render();
bool DRW_state_is_playback();
/**
 * Is the user navigating or painting the region.
 */
bool DRW_state_is_navigating();
/**
 * Is the user painting?
 */
bool DRW_state_is_painting();
/**
 * Should text draw in this mode?
 */
bool DRW_state_show_text();
/**
 * Should draw support elements
 * Objects center, selection outline, probe data, ...
 */
bool DRW_state_draw_support();
/**
 * Whether we should render the background
 */
bool DRW_state_draw_background();

/* Avoid too many lookups while drawing */
struct DRWContextState {
  ARegion *region;       /* 'CTX_wm_region(C)' */
  RegionView3D *rv3d;    /* 'CTX_wm_region_view3d(C)' */
  View3D *v3d;           /* 'CTX_wm_view3d(C)' */
  SpaceLink *space_data; /* 'CTX_wm_space_data(C)' */

  Scene *scene;          /* 'CTX_data_scene(C)' */
  ViewLayer *view_layer; /* 'CTX_data_view_layer(C)' */

  /* Use 'object_edit' for edit-mode */
  Object *obact;

  RenderEngineType *engine_type;

  Depsgraph *depsgraph;

  TaskGraph *task_graph;

  eObjectMode object_mode;

  eGPUShaderConfig sh_cfg;

  /** Last resort (some functions take this as an arg so we can't easily avoid).
   * May be nullptr when used for selection or depth buffer. */
  const bContext *evil_C;

  /* ---- */

  /* Cache: initialized by 'drw_context_state_init'. */
  Object *object_pose;
  Object *object_edit;
};

const DRWContextState *DRW_context_state_get();

bool DRW_is_viewport_compositor_enabled();
