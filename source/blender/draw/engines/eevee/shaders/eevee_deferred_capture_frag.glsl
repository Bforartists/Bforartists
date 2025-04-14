/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Compute light objects lighting contribution using captured Gbuffer data.
 */

#include "infos/eevee_deferred_info.hh"

FRAGMENT_SHADER_CREATE_INFO(eevee_deferred_capture_eval)

#include "draw_view_lib.glsl"
#include "eevee_gbuffer_lib.glsl"
#include "eevee_light_eval_lib.glsl"
#include "eevee_lightprobe_eval_lib.glsl"

void main()
{
  int2 texel = int2(gl_FragCoord.xy);

  float depth = texelFetch(hiz_tx, texel, 0).r;

  GBufferReader gbuf = gbuffer_read(gbuf_header_tx, gbuf_closure_tx, gbuf_normal_tx, texel);

  if (gbuf.closure_count == 0) {
    out_radiance = float4(0.0f);
    return;
  }

  float3 albedo_front = float3(0.0f);
  float3 albedo_back = float3(0.0f);

  for (uchar i = 0; i < GBUFFER_LAYER_MAX && i < gbuf.closure_count; i++) {
    ClosureUndetermined cl = gbuffer_closure_get(gbuf, i);
    switch (cl.type) {
      case CLOSURE_BSSRDF_BURLEY_ID:
      case CLOSURE_BSDF_DIFFUSE_ID:
      case CLOSURE_BSDF_MICROFACET_GGX_REFLECTION_ID:
        albedo_front += cl.color;
        break;
      case CLOSURE_BSDF_TRANSLUCENT_ID:
      case CLOSURE_BSDF_MICROFACET_GGX_REFRACTION_ID:
        albedo_back += (gbuf.thickness != 0.0f) ? square(cl.color) : cl.color;
        break;
      case CLOSURE_NONE_ID:
        /* TODO(fclem): Assert. */
        break;
    }
  }

  float3 P = drw_point_screen_to_world(float3(uvcoordsvar.xy, depth));
  float3 Ng = gbuffer_geometry_normal_unpack(gbuf.header, gbuf.surface_N);
  float3 V = drw_world_incident_vector(P);
  float vPz = dot(drw_view_forward(), P) - dot(drw_view_forward(), drw_view_position());

  ClosureUndetermined cl;
  cl.N = gbuf.surface_N;
  cl.type = CLOSURE_BSDF_DIFFUSE_ID;

  ClosureUndetermined cl_transmit;
  cl_transmit.N = gbuf.surface_N;
  cl_transmit.type = CLOSURE_BSDF_TRANSLUCENT_ID;

  uint object_id = texelFetch(gbuf_header_tx, int3(texel, 1), 0).x;
  ObjectInfos object_infos = drw_infos[object_id];
  uchar receiver_light_set = receiver_light_set_get(object_infos);

  /* Direct light. */
  ClosureLightStack stack;
  stack.cl[0] = closure_light_new(cl, V);
  light_eval_reflection(stack, P, Ng, V, vPz, receiver_light_set);

  float3 radiance_front = stack.cl[0].light_shadowed;

  stack.cl[0] = closure_light_new(cl_transmit, V, gbuf.thickness);
  light_eval_transmission(stack, P, Ng, V, vPz, gbuf.thickness, receiver_light_set);

  float3 radiance_back = stack.cl[0].light_shadowed;

  /* Indirect light. */
  /* Can only load irradiance to avoid dependency loop with the reflection probe. */
  SphericalHarmonicL1 sh = lightprobe_volume_sample(P, V, Ng);

  radiance_front += spherical_harmonics_evaluate_lambert(Ng, sh);
  /* TODO(fclem): Correct transmission eval. */
  radiance_back += spherical_harmonics_evaluate_lambert(-Ng, sh);

  out_radiance = float4(radiance_front * albedo_front + radiance_back * albedo_back, 0.0f);
}
