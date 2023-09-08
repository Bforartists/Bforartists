/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eevee
 *
 * Ground Truth Ambient Occlusion
 *
 * Based on Practical Realtime Strategies for Accurate Indirect Occlusion
 * http://blog.selfshadow.com/publications/s2016-shading-course/activision/s2016_pbs_activision_occlusion.pdf
 * http://blog.selfshadow.com/publications/s2016-shading-course/activision/s2016_pbs_activision_occlusion.pptx
 */

#pragma once

#include "eevee_shader_shared.hh"

namespace blender::eevee {

class Instance;

/* -------------------------------------------------------------------- */
/** \name AmbientOcclusion
 * \{ */

class AmbientOcclusion {
 private:
  class Instance &inst_;

  bool render_pass_enabled_;

  AOData &data_;
  PassSimple render_pass_ps_ = {"AO Render Pass"};

 public:
  AmbientOcclusion(Instance &inst, AOData &data) : inst_(inst), data_(data){};
  ~AmbientOcclusion(){};

  void init();

  void sync();

  void render(View &view);
  void render_pass(View &view);
};

/** \} */

}  // namespace blender::eevee
