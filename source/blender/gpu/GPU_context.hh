/* SPDX-FileCopyrightText: 2016 by Mike Erwin. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 *
 * This interface allow GPU to manage VAOs for multiple context and threads.
 */

#pragma once

#include "GPU_batch.hh"
#include "GPU_common.hh"
#include "GPU_platform.hh"

/* GPU back-ends abstract the differences between different APIs. #GPU_context_create
 * automatically initializes the back-end, and #GPU_context_discard frees it when there
 * are no more contexts. */
bool GPU_backend_supported();
void GPU_backend_type_selection_set(const eGPUBackendType backend);
eGPUBackendType GPU_backend_type_selection_get();
eGPUBackendType GPU_backend_get_type();

/**
 * Detect the most suited eGPUBackendType.
 *
 * - The detected backend will be set in `GPU_backend_type_selection_set`.
 * - When GPU_backend_type_selection_is_overridden it checks the overridden backend.
 *   When not overridden it checks a default list.
 * - OpenGL backend will be checked as fallback for Metal.
 *
 * Returns true when detection found a supported backend, otherwise returns false.
 * When no supported backend is found GPU_backend_type_selection_set is called with
 * GPU_BACKEND_NONE.
 */
bool GPU_backend_type_selection_detect();

/**
 * Alter the GPU_backend_type_selection_detect to only test a specific backend
 */
void GPU_backend_type_selection_set_override(eGPUBackendType backend_type);

/**
 * Check if the GPU_backend_type_selection_detect is overridden to only test a specific backend.
 */
bool GPU_backend_type_selection_is_overridden();

/** Opaque type hiding blender::gpu::Context. */
struct GPUContext;

GPUContext *GPU_context_create(void *ghost_window, void *ghost_context);
/**
 * To be called after #GPU_context_active_set(ctx_to_destroy).
 */
void GPU_context_discard(GPUContext *);

/**
 * Ctx can be null.
 */
void GPU_context_active_set(GPUContext *);
GPUContext *GPU_context_active_get();

/* Begin and end frame are used to mark the singular boundary representing the lifetime of a whole
 * frame. This also acts as a divisor for ensuring workload submission and flushing, especially for
 * background rendering when there is no call to present.
 * This is required by explicit-API's where there is no implicit workload flushing. */
void GPU_context_begin_frame(GPUContext *ctx);
void GPU_context_end_frame(GPUContext *ctx);

/* Legacy GPU (Intel HD4000 series) do not support sharing GPU objects between GPU
 * contexts. EEVEE/Workbench can create different contexts for image/preview rendering, baking or
 * compiling. When a legacy GPU is detected (`GPU_use_main_context_workaround()`) any worker
 * threads should use the draw manager opengl context and make sure that they are the only one
 * using it by locking the main context using these two functions. */
void GPU_context_main_lock();
void GPU_context_main_unlock();

/* GPU Begin/end work blocks */
void GPU_render_begin();
void GPU_render_end();

/* For operations which need to run exactly once per frame -- even if there are no render updates.
 */
void GPU_render_step();
