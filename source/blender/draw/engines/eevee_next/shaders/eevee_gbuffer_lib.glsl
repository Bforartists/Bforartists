/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * G-buffer: Packing and unpacking of G-buffer data.
 *
 * See #GBuffer for a breakdown of the G-buffer layout.
 */

#pragma BLENDER_REQUIRE(gpu_shader_math_vector_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_utildefines_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_codegen_lib.glsl)

vec2 gbuffer_normal_pack(vec3 N)
{
  N /= length_manhattan(N);
  vec2 _sign = sign(N.xy);
  _sign.x = _sign.x == 0.0 ? 1.0 : _sign.x;
  _sign.y = _sign.y == 0.0 ? 1.0 : _sign.y;
  N.xy = (N.z >= 0.0) ? N.xy : ((1.0 - abs(N.yx)) * _sign);
  N.xy = N.xy * 0.5 + 0.5;
  return N.xy;
}

vec3 gbuffer_normal_unpack(vec2 N_packed)
{
  N_packed = N_packed * 2.0 - 1.0;
  vec3 N = vec3(N_packed.x, N_packed.y, 1.0 - abs(N_packed.x) - abs(N_packed.y));
  float t = clamp(-N.z, 0.0, 1.0);
  N.x += (N.x >= 0.0) ? -t : t;
  N.y += (N.y >= 0.0) ? -t : t;
  return normalize(N);
}

float gbuffer_ior_pack(float ior)
{
  return (ior > 1.0) ? (1.0 - 0.5 / ior) : (0.5 * ior);
}

float gbuffer_ior_unpack(float ior_packed)
{
  return (ior_packed > 0.5) ? (0.5 / (1.0 - ior_packed)) : (2.0 * ior_packed);
}

float gbuffer_thickness_pack(float thickness)
{
  /* TODO(fclem): Something better. */
  return gbuffer_ior_pack(thickness);
}

float gbuffer_thickness_unpack(float thickness_packed)
{
  /* TODO(fclem): Something better. */
  return gbuffer_ior_unpack(thickness_packed);
}

vec3 gbuffer_sss_radii_pack(vec3 sss_radii)
{
  /* TODO(fclem): Something better. */
  return vec3(
      gbuffer_ior_pack(sss_radii.x), gbuffer_ior_pack(sss_radii.y), gbuffer_ior_pack(sss_radii.z));
}

vec3 gbuffer_sss_radii_unpack(vec3 sss_radii_packed)
{
  /* TODO(fclem): Something better. */
  return vec3(gbuffer_ior_unpack(sss_radii_packed.x),
              gbuffer_ior_unpack(sss_radii_packed.y),
              gbuffer_ior_unpack(sss_radii_packed.z));
}

vec4 gbuffer_color_pack(vec3 color)
{
  float max_comp = max(color.x, max(color.y, color.z));
  /* Store 2bit exponent inside Alpha. Allows values up to 8 with some color degradation.
   * Above 8, the result will be clamped when writing the data to the output buffer. */
  float exponent = (max_comp > 1) ? ((max_comp > 2) ? ((max_comp > 4) ? 3.0 : 2.0) : 1.0) : 0.0;
  /* TODO(fclem): Could try dithering to avoid banding artifacts on higher exponents. */
  return vec4(color / exp2(exponent), exponent / 3.0);
}

vec3 gbuffer_color_unpack(vec4 color_packed)
{
  float exponent = color_packed.a * 3.0;
  return color_packed.rgb * exp2(exponent);
}

float gbuffer_object_id_unorm16_pack(uint object_id)
{
  return float(object_id & 0xFFFFu) / float(0xFFFF);
}

uint gbuffer_object_id_unorm16_unpack(float object_id_packed)
{
  return uint(object_id_packed * float(0xFFFF));
}

float gbuffer_object_id_f16_pack(uint object_id)
{
  /* TODO(fclem): Make use of all the 16 bits in a half float.
   * This here only correctly represent values up to 1024. */
  return float(object_id);
}

uint gbuffer_object_id_f16_unpack(float object_id_packed)
{
  return uint(object_id_packed);
}

bool gbuffer_is_refraction(vec4 gbuffer)
{
  return gbuffer.w < 1.0;
}

struct GBufferData {
  ClosureDiffuse diffuse;
  ClosureReflection reflection;
  ClosureRefraction refraction;
  float thickness;
  bool has_diffuse;
  bool has_reflection;
  bool has_refraction;
};

GBufferData gbuffer_read(usampler2D header_tx,
                         sampler2DArray closure_tx,
                         sampler2DArray color_tx,
                         ivec2 texel)
{
  GBufferData gbuf;

  uint header = texelFetch(header_tx, texel, 0).r;

  gbuf.thickness = 0.0;
  gbuf.has_diffuse = flag_test(header, CLOSURE_DIFFUSE);
  gbuf.has_reflection = flag_test(header, CLOSURE_REFLECTION);
  gbuf.has_refraction = flag_test(header, CLOSURE_REFRACTION);

  if (gbuf.has_reflection) {
    int layer = 0;
    vec4 closure_packed = texelFetch(closure_tx, ivec3(texel, layer), 0);
    gbuf.reflection.N = gbuffer_normal_unpack(closure_packed.xy);
    gbuf.reflection.roughness = closure_packed.z;

    vec4 color_packed = texelFetch(color_tx, ivec3(texel, layer), 0);
    gbuf.reflection.color = gbuffer_color_unpack(color_packed);
  }
  else {
    gbuf.reflection.N = vec3(0.0, 0.0, 1.0);
    gbuf.reflection.roughness = 0.0;
    gbuf.reflection.color = vec3(0.0);
  }

  if (gbuf.has_diffuse) {
    int layer = 1;
    vec4 closure_packed = texelFetch(closure_tx, ivec3(texel, layer), 0);
    gbuf.diffuse.N = gbuffer_normal_unpack(closure_packed.xy);
    gbuf.diffuse.sss_id = 0u;
    gbuf.thickness = gbuffer_thickness_unpack(closure_packed.z);

    vec4 color_packed = texelFetch(color_tx, ivec3(texel, layer), 0);
    gbuf.diffuse.color = gbuffer_color_unpack(color_packed);

    if (flag_test(header, CLOSURE_SSS)) {
      int layer = 2;
      vec4 closure_packed = texelFetch(closure_tx, ivec3(texel, layer), 0);
      gbuf.diffuse.sss_radius = gbuffer_sss_radii_unpack(closure_packed.xyz);
      gbuf.diffuse.sss_id = gbuffer_object_id_unorm16_unpack(closure_packed.w);
    }
  }
  else {
    gbuf.diffuse.N = vec3(0.0, 0.0, 1.0);
    gbuf.diffuse.sss_id = 0u;
    gbuf.diffuse.color = vec3(0.0);
  }

  if (gbuf.has_refraction) {
    int layer = 1;
    vec4 closure_packed = texelFetch(closure_tx, ivec3(texel, layer), 0);
    gbuf.refraction.N = gbuffer_normal_unpack(closure_packed.xy);
    gbuf.refraction.roughness = closure_packed.z;
    gbuf.refraction.ior = gbuffer_ior_unpack(closure_packed.w);

    vec4 color_packed = texelFetch(color_tx, ivec3(texel, layer), 0);
    gbuf.refraction.color = gbuffer_color_unpack(color_packed);
  }
  else {
    gbuf.refraction.N = vec3(0.0, 0.0, 1.0);
    gbuf.refraction.ior = 1.1;
    gbuf.refraction.roughness = 0.0;
    gbuf.refraction.color = vec3(0.0);
  }

  return gbuf;
}
