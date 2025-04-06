/* SPDX-FileCopyrightText: 2021 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eevee
 *
 * Postprocess diffuse radiance output from the diffuse evaluation pass to mimic subsurface
 * transmission.
 *
 * This implementation follows the technique described in the SIGGRAPH presentation:
 * "Efficient screen space subsurface scattering SIGGRAPH 2018"
 * by Evgenii Golubev
 *
 * But, instead of having all the precomputed weights for all three color primaries,
 * we precompute a weight profile texture to be able to support per pixel AND per channel radius.
 */

#pragma once

#include "eevee_shader.hh"
#include "eevee_shader_shared.hh"

namespace blender::eevee {

/* -------------------------------------------------------------------- */
/** \name Subsurface
 *
 * \{ */

class Instance;

struct SubsurfaceModule {
 private:
  Instance &inst_;
  /** Contains samples locations. */
  SubsurfaceData &data_;
  /** Scene diffuse irradiance. Pointer binded at sync time, set at render time. */
  GPUTexture *direct_light_tx_;
  GPUTexture *indirect_light_tx_;
  /** Input radiance packed with surface ID. */
  TextureFromPool radiance_tx_;
  TextureFromPool object_id_tx_;
  /** Setup pass fill the radiance_id_tx_ for faster convolution. */
  PassSimple setup_ps_ = {"Subsurface.Prepare"};
  int3 setup_dispatch_size_ = {1, 1, 1};

  /** Screen space convolution pass. */
  PassSimple convolve_ps_ = {"Subsurface.Convolve"};
  SubsurfaceTileBuf convolve_tile_buf_;
  DispatchIndirectBuf convolve_dispatch_buf_;

 public:
  SubsurfaceModule(Instance &inst, SubsurfaceData &data) : inst_(inst), data_(data)
  {
    /* Force first update. */
    data_.sample_len = -1;
  };

  ~SubsurfaceModule(){};

  void end_sync();

  /* Process the direct & indirect diffuse light buffers using screen space subsurface scattering.
   * Result is stored in the direct light texture. */
  void render(GPUTexture *direct_diffuse_light_tx,
              GPUTexture *indirect_diffuse_light_tx,
              eClosureBits active_closures,
              View &view);

 private:
  void precompute_samples_location();

  /** Christensen-Burley implementation. */
  static float burley_sample(float d, float x_rand);
  static float burley_eval(float d, float r);
  static float burley_pdf(float d, float r);
};

/** \} */

}  // namespace blender::eevee
