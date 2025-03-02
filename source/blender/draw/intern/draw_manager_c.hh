/* SPDX-FileCopyrightText: 2016 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup draw
 */

/* Private functions / structs of the draw manager */

#pragma once

#include "DRW_engine.hh"
#include "DRW_render.hh"

#include "BLI_task.h"
#include "BLI_threads.h"

#include "GPU_batch.hh"
#include "GPU_context.hh"
#include "GPU_framebuffer.hh"
#include "GPU_viewport.hh"

struct DRWDebugModule;
struct DRWUniformChunk;
struct DRWViewData;
struct DRWTextStore;
struct DupliObject;
struct Object;
struct Mesh;
namespace blender::draw {
struct CurvesModule;
struct VolumeModule;
struct PointCloudModule;
struct DRW_Attributes;
struct DRW_MeshCDMask;
class CurveRefinePass;
class View;
}  // namespace blender::draw
struct GPUMaterial;
struct GSet;

/* -------------------------------------------------------------------- */
/** \name Data Structure
 *
 * Data structure to for registered draw engines that can store draw manager
 * specific data.
 * \{ */

typedef struct DRWRegisteredDrawEngine {
  void /*DRWRegisteredDrawEngine*/ *next, *prev;
  DrawEngineType *draw_engine;
  /** Index of the type in the lists. Index is used for dupli data. */
  int index;
} DRWRegisteredDrawEngine;

/** \} */

/* -------------------------------------------------------------------- */
/** \name Memory Pools
 * \{ */

/** Contains memory pools information. */
struct DRWData {
  /** Instance data. */
  DRWInstanceDataList *idatalist;
  /** List of smoke textures to free after drawing. */
  ListBase smoke_textures;
  /** Per stereo view data. Contains engine data and default frame-buffers. */
  DRWViewData *view_data[2];
  /** Module storage. */
  blender::draw::CurvesModule *curves_module;
  blender::draw::VolumeModule *volume_module;
  blender::draw::PointCloudModule *pointcloud_module;
  /** Default view that feeds every engine. */
  blender::draw::View *default_view;
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name Draw Manager
 * \{ */

struct DupliKey {
  Object *ob;
  ID *ob_data;
};

struct DRWContext {
  /* TODO: clean up this struct a bit. */
  /* Cache generation */
  DRWData *data = nullptr;
  /** Active view data structure for one of the 2 stereo view. */
  DRWViewData *view_data_active = nullptr;

  /** Dupli object that corresponds to the current object. */
  DupliObject *dupli_source = nullptr;
  /** Object that created the dupli-list the current object is part of. */
  Object *dupli_parent = nullptr;
  /** Object referenced by the current dupli object. */
  Object *dupli_origin = nullptr;
  /** Object-data referenced by the current dupli object. */
  ID *dupli_origin_data = nullptr;
  /** Hash-map: #DupliKey -> void pointer for each enabled engine. */
  GHash *dupli_ghash = nullptr;
  /* Dupli data for the current dupli for each enabled engine. */
  void **dupli_datas = nullptr;

  /* Optional associated viewport. Can be nullptr. */
  GPUViewport *viewport = nullptr;
  /* Size of the viewport or the final render frame. */
  blender::float2 size = {0, 0};
  blender::float2 inv_size = {0, 0};

  /* Returns the viewport's default framebuffer. */
  GPUFrameBuffer *default_framebuffer();

  struct {
    uint is_select : 1;
    uint is_material_select : 1;
    uint is_depth : 1;
    uint is_image_render : 1;
    uint is_scene_render : 1;
    uint draw_background : 1;
    uint draw_text : 1;
  } options;

  /* Current rendering context */
  DRWContextState draw_ctx = {};

  /* Convenience pointer to text_store owned by the viewport */
  DRWTextStore **text_store_p = nullptr;

  /** True, when drawing is in progress, see #DRW_draw_in_progress. */
  bool in_progress = false;

  TaskGraph *task_graph = nullptr;
  /* Contains list of objects that needs to be extracted from other objects. */
  GSet *delayed_extraction = nullptr;

  DRWDebugModule *debug = nullptr;

  /* Reset all members before drawing in order to avoid undefined state. */
  void prepare_clean_for_draw();
  /* Poison all members to detect missing `prepare_clean_for_draw()`. */
  void state_ensure_not_reused();
};

/** \} */

/* -------------------------------------------------------------------- */
/** \name Functions
 * \{ */

/* Get thread local draw context. */
DRWContext &drw_get();

void drw_debug_draw();
void drw_debug_init();
void drw_debug_module_free(DRWDebugModule *module);
GPUStorageBuf *drw_debug_gpu_draw_buf_get();

void drw_batch_cache_validate(Object *ob);
void drw_batch_cache_generate_requested(Object *ob);

/**
 * \warning Only evaluated mesh data is handled by this delayed generation.
 */
void drw_batch_cache_generate_requested_delayed(Object *ob);
void drw_batch_cache_generate_requested_evaluated_mesh_or_curve(Object *ob);

namespace blender::draw {

void DRW_mesh_get_attributes(const Object &object,
                             const Mesh &mesh,
                             Span<const GPUMaterial *> materials,
                             DRW_Attributes *r_attrs,
                             DRW_MeshCDMask *r_cd_needed);

}  // namespace blender::draw

void DRW_manager_begin_sync();
void DRW_manager_end_sync();

/** \} */
