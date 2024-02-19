/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eevee
 *
 * Gbuffer layout used for deferred shading pipeline.
 */

#pragma once

#include "DRW_render.hh"

#include "eevee_material.hh"
#include "eevee_shader_shared.hh"

namespace blender::eevee {

class Instance;

/**
 * Full-screen textures containing geometric and surface data.
 * Used by deferred shading passes. Only one g-buffer is allocated per view
 * and is reused for each deferred layer. This is why there can only be temporary
 * texture inside it.
 *
 * Everything is stored inside two array texture, one for each format. This is to fit the
 * limitation of the number of images we can bind on a single shader.
 *
 * The content of the g-buffer is polymorphic. A 8bit header specify the layout of the data.
 * The first layer is always written to while others are written only if needed using imageStore
 * operations reducing the bandwidth needed.
 * Except for some special configurations, the g-buffer holds up to 3 closures.
 *
 * For each output closure, we also output the color to apply after the lighting computation.
 * The color is stored with a 2 exponent that allows input color with component higher than 1.
 * Color degradation is expected to happen in this case.
 *
 * Here are special configurations:
 *
 * - Opaque Dielectric:
 *   - 1 Diffuse lobe and 1 Reflection lobe without anisotropy.
 *   - Share a single normal.
 *   - Reflection is not colored.
 *   - Layout:
 *     - Color 1 : Diffuse color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Roughness (isotropic)
 *     - Closure 1 A : Reflection intensity
 *
 * - Simple Car-paint: (TODO)
 *   - 2 Reflection lobe without anisotropy.
 *   - Share a single normal.
 *   - Coat layer is not colored.
 *   - Layout:
 *     - Color 1 : Bottom layer color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Roughness (isotropic)
 *     - Closure 1 A : Coat layer intensity
 *
 * - Simple Glass: (TODO)
 *   - 1 Refraction lobe and 1 Reflection lobe without anisotropy.
 *   - Share a single normal.
 *   - Reflection intensity is derived from IOR.
 *   - Layout:
 *     - Color 1 : Refraction color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Roughness (isotropic)
 *     - Closure 1 A : IOR
 *
 * Here are Closure configurations:
 *
 * - Reflection (Isotropic):
 *   - Layout:
 *     - Color : Reflection color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Roughness
 *     - Closure 1 A : Unused
 *
 * - Reflection (Anisotropic): (TODO)
 *   - Layout:
 *     - Color : Reflection color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Tangent packed X
 *     - Closure 1 A : Tangent packed Y
 *     - Closure 2 R : Roughness X
 *     - Closure 2 G : Roughness Y
 *     - Closure 2 B : Unused
 *     - Closure 2 A : Unused
 *
 * - Refraction (Isotropic):
 *   - Layout:
 *     - Color : Refraction color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Roughness
 *     - Closure 1 A : IOR
 *
 * - Diffuse:
 *   - Layout:
 *     - Color : Diffuse color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Unused
 *     - Closure 1 A : Unused (Could be used for diffuse roughness)
 *
 * - Sub-Surface Scattering:
 *   - Layout:
 *     - Color : Diffuse color
 *     - Closure 1 R : Normal packed X
 *     - Closure 1 G : Normal packed Y
 *     - Closure 1 B : Thickness
 *     - Closure 1 A : Unused (Could be used for diffuse roughness)
 *     - Closure 2 R : Scattering radius R
 *     - Closure 2 G : Scattering radius G
 *     - Closure 2 B : Scattering radius B
 *     - Closure 2 A : Object ID
 *
 */
struct GBuffer {
  /* TODO(fclem): Use texture from pool once they support texture array and layer views. */
  Texture header_tx = {"GBufferHeader"};
  Texture closure_tx = {"GBufferClosure"};
  Texture normal_tx = {"GBufferNormal"};
  /* References to the GBuffer layer range [1..max]. */
  GPUTexture *closure_img_tx = nullptr;
  GPUTexture *normal_img_tx = nullptr;

  void acquire(int2 extent, int data_count, int normal_count)
  {
    /* Always allocating enough layers so that the image view is always valid. */
    data_count = max_ii(3, data_count);
    normal_count = max_ii(2, normal_count);

    eGPUTextureUsage usage = GPU_TEXTURE_USAGE_SHADER_READ | GPU_TEXTURE_USAGE_SHADER_WRITE |
                             GPU_TEXTURE_USAGE_ATTACHMENT;
    header_tx.ensure_2d(GPU_R16UI, extent, usage);
    closure_tx.ensure_2d_array(GPU_RGB10_A2, extent, data_count, usage);
    normal_tx.ensure_2d_array(GPU_RG16, extent, normal_count, usage);
    /* Ensure layer view for frame-buffer attachment. */
    closure_tx.ensure_layer_views();
    normal_tx.ensure_layer_views();
    /* Ensure layer view for image store. */
    closure_img_tx = closure_tx.layer_range_view(2, data_count - 2);
    normal_img_tx = normal_tx.layer_range_view(1, normal_count - 1);
  }

  void release()
  {
    /* TODO(fclem): Use texture from pool once they support texture array. */
    // header_tx.release();
    // closure_tx.release();
    // normal_tx.release();

    closure_img_tx = nullptr;
    normal_img_tx = nullptr;
  }

  template<typename PassType> void bind_resources(PassType &pass)
  {
    pass.bind_texture("gbuf_header_tx", &header_tx);
    pass.bind_texture("gbuf_closure_tx", &closure_tx);
    pass.bind_texture("gbuf_normal_tx", &normal_tx);
  }
};

}  // namespace blender::eevee
