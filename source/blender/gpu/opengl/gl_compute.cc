/* SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "gl_compute.hh"

#include "gl_debug.hh"

#include "glew-mx.h"

namespace blender::gpu {

void GLCompute::dispatch(int group_x_len, int group_y_len, int group_z_len)
{
  GL_CHECK_RESOURCES("Compute");

  GLContext::get()->state_manager->apply_state();

  glDispatchCompute(group_x_len, group_y_len, group_z_len);
}

}  // namespace blender::gpu
