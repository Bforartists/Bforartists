/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2016 by Mike Erwin. All rights reserved. */

/** \file
 * \ingroup gpu
 *
 * Manage GL vertex array IDs in a thread-safe way
 * Use these instead of glGenBuffers & its friends
 * - alloc must be called from a thread that is bound
 *   to the context that will be used for drawing with
 *   this VAO.
 * - free can be called from any thread
 */

/* TODO: Create cmake option. */
#define WITH_OPENGL_BACKEND 1

#include "BLI_assert.h"
#include "BLI_utildefines.h"

#include "GPU_context.h"
#include "GPU_framebuffer.h"

#include "GHOST_C-api.h"

#include "gpu_backend.hh"
#include "gpu_batch_private.hh"
#include "gpu_context_private.hh"
#include "gpu_matrix_private.h"

#ifdef WITH_OPENGL_BACKEND
#  include "gl_backend.hh"
#  include "gl_context.hh"
#endif

#include <mutex>
#include <vector>

using namespace blender::gpu;

static thread_local Context *active_ctx = nullptr;

/* -------------------------------------------------------------------- */
/** \name gpu::Context methods
 * \{ */

namespace blender::gpu {

Context::Context()
{
  thread_ = pthread_self();
  is_active_ = false;
  matrix_state = GPU_matrix_state_create();
}

Context::~Context()
{
  GPU_matrix_state_discard(matrix_state);
  delete state_manager;
  delete front_left;
  delete back_left;
  delete front_right;
  delete back_right;
  delete imm;
}

bool Context::is_active_on_thread()
{
  return (this == active_ctx) && pthread_equal(pthread_self(), thread_);
}

Context *Context::get()
{
  return active_ctx;
}

}  // namespace blender::gpu

/** \} */

/* -------------------------------------------------------------------- */

GPUContext *GPU_context_create(void *ghost_window)
{
  if (GPUBackend::get() == nullptr) {
    /* TODO: move where it make sense. */
    GPU_backend_init(GPU_BACKEND_OPENGL);
  }

  Context *ctx = GPUBackend::get()->context_alloc(ghost_window);

  GPU_context_active_set(wrap(ctx));
  return wrap(ctx);
}

void GPU_context_discard(GPUContext *ctx_)
{
  Context *ctx = unwrap(ctx_);
  delete ctx;
  active_ctx = nullptr;
}

void GPU_context_active_set(GPUContext *ctx_)
{
  Context *ctx = unwrap(ctx_);

  if (active_ctx) {
    active_ctx->deactivate();
  }

  active_ctx = ctx;

  if (ctx) {
    ctx->activate();
  }
}

GPUContext *GPU_context_active_get()
{
  return wrap(Context::get());
}

/* -------------------------------------------------------------------- */
/** \name Main context global mutex
 *
 * Used to avoid crash on some old drivers.
 * \{ */

static std::mutex main_context_mutex;

void GPU_context_main_lock()
{
  main_context_mutex.lock();
}

void GPU_context_main_unlock()
{
  main_context_mutex.unlock();
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Backend selection
 * \{ */

static GPUBackend *g_backend;

void GPU_backend_init(eGPUBackendType backend_type)
{
  BLI_assert(g_backend == nullptr);

  switch (backend_type) {
#if WITH_OPENGL_BACKEND
    case GPU_BACKEND_OPENGL:
      g_backend = new GLBackend;
      break;
#endif
    default:
      BLI_assert(0);
      break;
  }
}

void GPU_backend_exit()
{
  /* TODO: assert no resource left. Currently UI textures are still not freed in their context
   * correctly. */
  delete g_backend;
  g_backend = nullptr;
}

eGPUBackendType GPU_backend_get_type()
{
  if (g_backend && dynamic_cast<GLBackend *>(g_backend) != nullptr) {
    return GPU_BACKEND_OPENGL;
  }

  return GPU_BACKEND_NONE;
}

GPUBackend *GPUBackend::get()
{
  return g_backend;
}

/** \} */
