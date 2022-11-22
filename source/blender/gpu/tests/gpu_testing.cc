/* SPDX-License-Identifier: Apache-2.0 */

#include "testing/testing.h"

#include "CLG_log.h"

#include "GPU_context.h"
#include "GPU_init_exit.h"
#include "gpu_testing.hh"

#include "GHOST_C-api.h"

namespace blender::gpu {

void GPUTest::SetUp()
{
  GPU_backend_type_selection_set(gpu_backend_type);
  GHOST_GLSettings glSettings = {0};
  glSettings.context_type = draw_context_type;
  CLG_init();
  ghost_system = GHOST_CreateSystem();
  ghost_context = GHOST_CreateOpenGLContext(ghost_system, glSettings);
  GHOST_ActivateOpenGLContext(ghost_context);
  context = GPU_context_create(nullptr, ghost_context);
  GPU_init();
}

void GPUTest::TearDown()
{
  GPU_exit();
  GPU_context_discard(context);
  GHOST_DisposeOpenGLContext(ghost_system, ghost_context);
  GHOST_DisposeSystem(ghost_system);
  CLG_exit();
}

}  // namespace blender::gpu
