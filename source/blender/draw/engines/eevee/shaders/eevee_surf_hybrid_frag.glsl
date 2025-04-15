/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Deferred lighting evaluation: Lighting is evaluated in a separate pass.
 *
 * Outputs shading parameter per pixel using a randomized set of BSDFs.
 * Some render-pass are written during this pass.
 */

#include "infos/eevee_material_info.hh"

FRAGMENT_SHADER_CREATE_INFO(eevee_node_tree)
FRAGMENT_SHADER_CREATE_INFO(eevee_geom_mesh)
FRAGMENT_SHADER_CREATE_INFO(eevee_surf_deferred_hybrid)
FRAGMENT_SHADER_CREATE_INFO(eevee_render_pass_out)
FRAGMENT_SHADER_CREATE_INFO(eevee_cryptomatte_out)

#include "common_hair_lib.glsl"
#include "draw_view_lib.glsl"
#include "eevee_ambient_occlusion_lib.glsl"
#include "eevee_forward_lib.glsl"
#include "eevee_gbuffer_lib.glsl"
#include "eevee_nodetree_lib.glsl"
#include "eevee_sampling_lib.glsl"
#include "eevee_surf_lib.glsl"

/* Global thickness because it is needed for closure_to_rgba. */
float g_thickness;

float4 closure_to_rgba(Closure cl_unused)
{
  float3 radiance, transmittance;
  forward_lighting_eval(g_thickness, radiance, transmittance);

  /* Reset for the next closure tree. */
  float noise = utility_tx_fetch(utility_tx, gl_FragCoord.xy, UTIL_BLUE_NOISE_LAYER).r;
  float closure_rand = fract(noise + sampling_rng_1D_get(SAMPLING_CLOSURE));
  closure_weights_reset(closure_rand);

  return float4(radiance, saturate(1.0f - average(transmittance)));
}

void main()
{
  /* Clear AOVs first. In case the material renders to them. */
  clear_aovs();

  init_globals();

  float noise = utility_tx_fetch(utility_tx, gl_FragCoord.xy, UTIL_BLUE_NOISE_LAYER).r;
  float closure_rand = fract(noise + sampling_rng_1D_get(SAMPLING_CLOSURE));

  g_thickness = nodetree_thickness() * thickness_mode;

  fragment_displacement();

  nodetree_surface(closure_rand);

  g_holdout = saturate(g_holdout);

  /** Transparency weight is already applied through dithering, remove it from other closures. */
  float alpha = 1.0f - average(g_transmittance);
  float alpha_rcp = safe_rcp(alpha);

  /* Object holdout. */
  eObjectInfoFlag ob_flag = drw_object_infos().flag;
  if (flag_test(ob_flag, OBJECT_HOLDOUT)) {
    /* alpha is set from rejected pixels / dithering. */
    g_holdout = 1.0f;

    /* Set alpha to 0.0 so that lighting is not computed. */
    alpha_rcp = 0.0f;
  }

  g_emission *= alpha_rcp;

  int2 out_texel = int2(gl_FragCoord.xy);

#ifdef MAT_SUBSURFACE
  constexpr bool use_sss = true;
#else
  constexpr bool use_sss = false;
#endif

  ObjectInfos object_infos = drw_infos[drw_resource_id()];
  bool use_light_linking = receiver_light_set_get(object_infos) != 0;

  /* ----- Render Passes output ----- */

#ifdef MAT_RENDER_PASS_SUPPORT /* Needed because node_tree isn't present in test shaders. */
  /* Some render pass can be written during the gbuffer pass. Light passes are written later. */
  if (imageSize(rp_cryptomatte_img).x > 1) {
    float4 cryptomatte_output = float4(
        cryptomatte_object_buf[drw_resource_id()], node_tree.crypto_hash, 0.0f);
    imageStoreFast(rp_cryptomatte_img, out_texel, cryptomatte_output);
  }
  output_renderpass_color(uniform_buf.render_pass.position_id, float4(g_data.P, 1.0f));
  output_renderpass_color(uniform_buf.render_pass.emission_id, float4(g_emission, 1.0f));
#endif

  /* ----- GBuffer output ----- */

  GBufferData gbuf_data;
  gbuf_data.closure[0] = g_closure_get_resolved(0, alpha_rcp);
#if CLOSURE_BIN_COUNT > 1
  gbuf_data.closure[1] = g_closure_get_resolved(1, alpha_rcp);
#endif
#if CLOSURE_BIN_COUNT > 2
  gbuf_data.closure[2] = g_closure_get_resolved(2, alpha_rcp);
#endif
  gbuf_data.surface_N = g_data.N;
  gbuf_data.thickness = g_thickness;
  gbuf_data.use_light_linking = use_light_linking;

  GBufferWriter gbuf = gbuffer_pack(gbuf_data, g_data.Ng);

  /* Output header and first closure using frame-buffer attachment. */
  out_gbuf_header = gbuf.header;
  out_gbuf_closure1 = gbuf.data[0];
  out_gbuf_closure2 = gbuf.data[1];
  out_gbuf_normal = gbuf.N[0];

  /* Output remaining closures using image store. */
  for (int layer = GBUF_CLOSURE_FB_LAYER_COUNT; layer < GBUFFER_DATA_MAX && layer < gbuf.data_len;
       layer++)
  {
    /* NOTE: The image view start at layer GBUF_CLOSURE_FB_LAYER_COUNT so all destination layer is
     * `layer - GBUF_CLOSURE_FB_LAYER_COUNT`. */
    imageStoreFast(out_gbuf_closure_img,
                   int3(out_texel, layer - GBUF_CLOSURE_FB_LAYER_COUNT),
                   gbuf.data[layer]);
  }
  for (int layer = GBUF_NORMAL_FB_LAYER_COUNT;
       layer < GBUFFER_NORMAL_MAX && layer < gbuf.normal_len;
       layer++)
  {
    /* NOTE: The image view start at layer GBUF_NORMAL_FB_LAYER_COUNT so all destination layer is
     * `layer - GBUF_NORMAL_FB_LAYER_COUNT`. */
    imageStoreFast(out_gbuf_normal_img,
                   int3(out_texel, layer - GBUF_NORMAL_FB_LAYER_COUNT),
                   gbuf.N[layer].xyyy);
  }
  if (use_sss || use_light_linking) {
    constexpr int layer = GBUF_HEADER_FB_LAYER_COUNT;
    /* NOTE: The image view start at layer GBUF_HEADER_FB_LAYER_COUNT so all destination layer is
     * `layer - GBUF_HEADER_FB_LAYER_COUNT`. */
    imageStoreFast(out_gbuf_header_img,
                   int3(out_texel, layer - GBUF_HEADER_FB_LAYER_COUNT),
                   uint4(drw_resource_id()));
  }

  /* ----- Radiance output ----- */

  /* Only output emission during the gbuffer pass. */
  out_radiance = float4(g_emission, 0.0f);
  out_radiance.rgb *= 1.0f - g_holdout;
  out_radiance.a = g_holdout;
}
