/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Deferred lighting evaluation: Lighting is evaluated in a separate pass.
 *
 * Outputs shading parameter per pixel using a randomized set of BSDFs.
 * Some render-pass are written during this pass.
 */

#pragma BLENDER_REQUIRE(draw_view_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_gbuffer_lib.glsl)
#pragma BLENDER_REQUIRE(common_hair_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_ambient_occlusion_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_surf_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_forward_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_nodetree_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)

/* Global thickness because it is needed for closure_to_rgba. */
float g_thickness;

vec4 closure_to_rgba(Closure cl_unused)
{
  vec3 radiance, transmittance;
  forward_lighting_eval(g_thickness, radiance, transmittance);

  /* Reset for the next closure tree. */
  closure_weights_reset();

  return vec4(radiance, saturate(1.0 - average(transmittance)));
}

void main()
{
  /* Clear AOVs first. In case the material renders to them. */
  clear_aovs();

  init_globals();

  float noise = utility_tx_fetch(utility_tx, gl_FragCoord.xy, UTIL_BLUE_NOISE_LAYER).r;
  g_closure_rand = fract(noise + sampling_rng_1D_get(SAMPLING_CLOSURE));

  fragment_displacement();

  nodetree_surface();

  g_holdout = saturate(g_holdout);

  g_thickness = max(0.0, nodetree_thickness());

  g_diffuse_data.color *= g_diffuse_data.weight;
  g_reflection_data.color *= g_reflection_data.weight;
  g_refraction_data.color *= g_refraction_data.weight;

  /* TODO(fclem): This feels way too complex for what is it. */
  bool has_any_bsdf_weight = g_diffuse_data.weight != 0.0 || g_reflection_data.weight != 0.0 ||
                             g_refraction_data.weight != 0.0;
  vec3 out_normal = has_any_bsdf_weight ? vec3(0.0) : g_data.N;
  out_normal += g_diffuse_data.N * g_diffuse_data.weight;
  out_normal += g_reflection_data.N * g_reflection_data.weight;
  out_normal += g_refraction_data.N * g_refraction_data.weight;
  out_normal = safe_normalize(out_normal);

  vec3 specular_color = g_reflection_data.color + g_refraction_data.color;

  /* ----- Render Passes output ----- */

  ivec2 out_texel = ivec2(gl_FragCoord.xy);
#ifdef MAT_RENDER_PASS_SUPPORT /* Needed because node_tree isn't present in test shaders. */
  /* Some render pass can be written during the gbuffer pass. Light passes are written later. */
  if (imageSize(rp_cryptomatte_img).x > 1) {
    vec4 cryptomatte_output = vec4(
        cryptomatte_object_buf[resource_id], node_tree.crypto_hash, 0.0);
    imageStore(rp_cryptomatte_img, out_texel, cryptomatte_output);
  }
  output_renderpass_color(uniform_buf.render_pass.normal_id, vec4(out_normal, 1.0));
  output_renderpass_color(uniform_buf.render_pass.position_id, vec4(g_data.P, 1.0));
  output_renderpass_color(uniform_buf.render_pass.diffuse_color_id,
                          vec4(g_diffuse_data.color, 1.0));
  output_renderpass_color(uniform_buf.render_pass.specular_color_id, vec4(specular_color, 1.0));
  output_renderpass_color(uniform_buf.render_pass.emission_id, vec4(g_emission, 1.0));
#endif

  /* ----- GBuffer output ----- */

  GBufferDataUndetermined gbuf_data;
  gbuf_data.diffuse = g_diffuse_data;
  gbuf_data.translucent = g_translucent_data;
  gbuf_data.reflection = g_reflection_data;
  gbuf_data.refraction = g_refraction_data;
  gbuf_data.surface_N = g_data.N;
  gbuf_data.thickness = g_thickness;
  gbuf_data.object_id = resource_id;

  GBufferWriter gbuf = gbuffer_pack(gbuf_data);

  /* Output header and first closure using frame-buffer attachment. */
  out_gbuf_header = gbuf.header;
  out_gbuf_closure1 = gbuf.data[0];
  out_gbuf_closure2 = gbuf.data[1];
  out_gbuf_normal = gbuf.N[0];

  /* Output remaining closures using image store. */
  /* NOTE: The image view start at layer 2 so all destination layer is `layer - 2`. */
  for (int layer = 2; layer < GBUFFER_DATA_MAX && layer < gbuf.layer_data; layer++) {
    imageStore(out_gbuf_closure_img, ivec3(out_texel, layer - 2), gbuf.data[layer]);
  }
  /* NOTE: The image view start at layer 1 so all destination layer is `layer - 1`. */
  for (int layer = 1; layer < GBUFFER_NORMAL_MAX && layer < gbuf.layer_normal; layer++) {
    imageStore(out_gbuf_normal_img, ivec3(out_texel, layer - 1), gbuf.N[layer].xyyy);
  }

  /* ----- Radiance output ----- */

  /* Only output emission during the gbuffer pass. */
  out_radiance = vec4(g_emission, 0.0);
  out_radiance.rgb *= 1.0 - g_holdout;
  out_radiance.a = g_holdout;
}
