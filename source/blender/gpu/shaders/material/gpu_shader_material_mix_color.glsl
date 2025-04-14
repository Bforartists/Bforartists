/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "gpu_shader_common_color_utils.glsl"

void node_mix_blend(float fac,
                    float3 facvec,
                    float f1,
                    float f2,
                    float3 v1,
                    float3 v2,
                    float4 col1,
                    float4 col2,
                    out float outfloat,
                    out float3 outvec,
                    out float4 outcol)
{
  outcol = mix(col1, col2, fac);
  outcol.a = col1.a;
}

void node_mix_add(float fac,
                  float3 facvec,
                  float f1,
                  float f2,
                  float3 v1,
                  float3 v2,
                  float4 col1,
                  float4 col2,
                  out float outfloat,
                  out float3 outvec,
                  out float4 outcol)
{

  outcol = mix(col1, col1 + col2, fac);
  outcol.a = col1.a;
}

void node_mix_mult(float fac,
                   float3 facvec,
                   float f1,
                   float f2,
                   float3 v1,
                   float3 v2,
                   float4 col1,
                   float4 col2,
                   out float outfloat,
                   out float3 outvec,
                   out float4 outcol)
{

  outcol = mix(col1, col1 * col2, fac);
  outcol.a = col1.a;
}

void node_mix_screen(float fac,
                     float3 facvec,
                     float f1,
                     float f2,
                     float3 v1,
                     float3 v2,
                     float4 col1,
                     float4 col2,
                     out float outfloat,
                     out float3 outvec,
                     out float4 outcol)
{

  float facm = 1.0f - fac;

  outcol = float4(1.0f) - (float4(facm) + fac * (float4(1.0f) - col2)) * (float4(1.0f) - col1);
  outcol.a = col1.a;
}

void node_mix_overlay(float fac,
                      float3 facvec,
                      float f1,
                      float f2,
                      float3 v1,
                      float3 v2,
                      float4 col1,
                      float4 col2,
                      out float outfloat,
                      out float3 outvec,
                      out float4 outcol)
{

  float facm = 1.0f - fac;

  outcol = col1;

  if (outcol.r < 0.5f) {
    outcol.r *= facm + 2.0f * fac * col2.r;
  }
  else {
    outcol.r = 1.0f - (facm + 2.0f * fac * (1.0f - col2.r)) * (1.0f - outcol.r);
  }

  if (outcol.g < 0.5f) {
    outcol.g *= facm + 2.0f * fac * col2.g;
  }
  else {
    outcol.g = 1.0f - (facm + 2.0f * fac * (1.0f - col2.g)) * (1.0f - outcol.g);
  }

  if (outcol.b < 0.5f) {
    outcol.b *= facm + 2.0f * fac * col2.b;
  }
  else {
    outcol.b = 1.0f - (facm + 2.0f * fac * (1.0f - col2.b)) * (1.0f - outcol.b);
  }
}

void node_mix_sub(float fac,
                  float3 facvec,
                  float f1,
                  float f2,
                  float3 v1,
                  float3 v2,
                  float4 col1,
                  float4 col2,
                  out float outfloat,
                  out float3 outvec,
                  out float4 outcol)
{

  outcol = mix(col1, col1 - col2, fac);
  outcol.a = col1.a;
}

/* A variant of mix_div that fallback to the first color upon zero division. */
void node_mix_div_fallback(float fac,
                           float3 facvec,
                           float f1,
                           float f2,
                           float3 v1,
                           float3 v2,
                           float4 col1,
                           float4 col2,
                           out float outfloat,
                           out float3 outvec,
                           out float4 outcol)
{

  float facm = 1.0f - fac;

  outcol = col1;

  if (col2.r != 0.0f) {
    outcol.r = facm * outcol.r + fac * outcol.r / col2.r;
  }
  if (col2.g != 0.0f) {
    outcol.g = facm * outcol.g + fac * outcol.g / col2.g;
  }
  if (col2.b != 0.0f) {
    outcol.b = facm * outcol.b + fac * outcol.b / col2.b;
  }
}

void node_mix_diff(float fac,
                   float3 facvec,
                   float f1,
                   float f2,
                   float3 v1,
                   float3 v2,
                   float4 col1,
                   float4 col2,
                   out float outfloat,
                   out float3 outvec,
                   out float4 outcol)
{

  outcol = mix(col1, abs(col1 - col2), fac);
  outcol.a = col1.a;
}

void node_mix_exclusion(float fac,
                        float3 facvec,
                        float f1,
                        float f2,
                        float3 v1,
                        float3 v2,
                        float4 col1,
                        float4 col2,
                        out float outfloat,
                        out float3 outvec,
                        out float4 outcol)
{

  outcol = max(mix(col1, col1 + col2 - 2.0f * col1 * col2, fac), 0.0f);
  outcol.a = col1.a;
}

void node_mix_dark(float fac,
                   float3 facvec,
                   float f1,
                   float f2,
                   float3 v1,
                   float3 v2,
                   float4 col1,
                   float4 col2,
                   out float outfloat,
                   out float3 outvec,
                   out float4 outcol)
{

  outcol.rgb = mix(col1.rgb, min(col1.rgb, col2.rgb), fac);
  outcol.a = col1.a;
}

void node_mix_light(float fac,
                    float3 facvec,
                    float f1,
                    float f2,
                    float3 v1,
                    float3 v2,
                    float4 col1,
                    float4 col2,
                    out float outfloat,
                    out float3 outvec,
                    out float4 outcol)
{
  outcol.rgb = mix(col1.rgb, max(col1.rgb, col2.rgb), fac);
  outcol.a = col1.a;
}

void node_mix_dodge(float fac,
                    float3 facvec,
                    float f1,
                    float f2,
                    float3 v1,
                    float3 v2,
                    float4 col1,
                    float4 col2,
                    out float outfloat,
                    out float3 outvec,
                    out float4 outcol)
{
  outcol = col1;

  if (outcol.r != 0.0f) {
    float tmp = 1.0f - fac * col2.r;
    if (tmp <= 0.0f) {
      outcol.r = 1.0f;
    }
    else if ((tmp = outcol.r / tmp) > 1.0f) {
      outcol.r = 1.0f;
    }
    else {
      outcol.r = tmp;
    }
  }
  if (outcol.g != 0.0f) {
    float tmp = 1.0f - fac * col2.g;
    if (tmp <= 0.0f) {
      outcol.g = 1.0f;
    }
    else if ((tmp = outcol.g / tmp) > 1.0f) {
      outcol.g = 1.0f;
    }
    else {
      outcol.g = tmp;
    }
  }
  if (outcol.b != 0.0f) {
    float tmp = 1.0f - fac * col2.b;
    if (tmp <= 0.0f) {
      outcol.b = 1.0f;
    }
    else if ((tmp = outcol.b / tmp) > 1.0f) {
      outcol.b = 1.0f;
    }
    else {
      outcol.b = tmp;
    }
  }
}

void node_mix_burn(float fac,
                   float3 facvec,
                   float f1,
                   float f2,
                   float3 v1,
                   float3 v2,
                   float4 col1,
                   float4 col2,
                   out float outfloat,
                   out float3 outvec,
                   out float4 outcol)
{

  float tmp, facm = 1.0f - fac;

  outcol = col1;

  tmp = facm + fac * col2.r;
  if (tmp <= 0.0f) {
    outcol.r = 0.0f;
  }
  else if ((tmp = (1.0f - (1.0f - outcol.r) / tmp)) < 0.0f) {
    outcol.r = 0.0f;
  }
  else if (tmp > 1.0f) {
    outcol.r = 1.0f;
  }
  else {
    outcol.r = tmp;
  }

  tmp = facm + fac * col2.g;
  if (tmp <= 0.0f) {
    outcol.g = 0.0f;
  }
  else if ((tmp = (1.0f - (1.0f - outcol.g) / tmp)) < 0.0f) {
    outcol.g = 0.0f;
  }
  else if (tmp > 1.0f) {
    outcol.g = 1.0f;
  }
  else {
    outcol.g = tmp;
  }

  tmp = facm + fac * col2.b;
  if (tmp <= 0.0f) {
    outcol.b = 0.0f;
  }
  else if ((tmp = (1.0f - (1.0f - outcol.b) / tmp)) < 0.0f) {
    outcol.b = 0.0f;
  }
  else if (tmp > 1.0f) {
    outcol.b = 1.0f;
  }
  else {
    outcol.b = tmp;
  }
}

void node_mix_hue(float fac,
                  float3 facvec,
                  float f1,
                  float f2,
                  float3 v1,
                  float3 v2,
                  float4 col1,
                  float4 col2,
                  out float outfloat,
                  out float3 outvec,
                  out float4 outcol)
{

  float facm = 1.0f - fac;

  outcol = col1;

  float4 hsv, hsv2, tmp;
  rgb_to_hsv(col2, hsv2);

  if (hsv2.y != 0.0f) {
    rgb_to_hsv(outcol, hsv);
    hsv.x = hsv2.x;
    hsv_to_rgb(hsv, tmp);

    outcol = mix(outcol, tmp, fac);
    outcol.a = col1.a;
  }
}

void node_mix_sat(float fac,
                  float3 facvec,
                  float f1,
                  float f2,
                  float3 v1,
                  float3 v2,
                  float4 col1,
                  float4 col2,
                  out float outfloat,
                  out float3 outvec,
                  out float4 outcol)
{

  float facm = 1.0f - fac;

  outcol = col1;

  float4 hsv, hsv2;
  rgb_to_hsv(outcol, hsv);

  if (hsv.y != 0.0f) {
    rgb_to_hsv(col2, hsv2);

    hsv.y = facm * hsv.y + fac * hsv2.y;
    hsv_to_rgb(hsv, outcol);
  }
}

void node_mix_val(float fac,
                  float3 facvec,
                  float f1,
                  float f2,
                  float3 v1,
                  float3 v2,
                  float4 col1,
                  float4 col2,
                  out float outfloat,
                  out float3 outvec,
                  out float4 outcol)
{

  float facm = 1.0f - fac;

  float4 hsv, hsv2;
  rgb_to_hsv(col1, hsv);
  rgb_to_hsv(col2, hsv2);

  hsv.z = facm * hsv.z + fac * hsv2.z;
  hsv_to_rgb(hsv, outcol);
}

void node_mix_color(float fac,
                    float3 facvec,
                    float f1,
                    float f2,
                    float3 v1,
                    float3 v2,
                    float4 col1,
                    float4 col2,
                    out float outfloat,
                    out float3 outvec,
                    out float4 outcol)
{

  float facm = 1.0f - fac;

  outcol = col1;

  float4 hsv, hsv2, tmp;
  rgb_to_hsv(col2, hsv2);

  if (hsv2.y != 0.0f) {
    rgb_to_hsv(outcol, hsv);
    hsv.x = hsv2.x;
    hsv.y = hsv2.y;
    hsv_to_rgb(hsv, tmp);

    outcol = mix(outcol, tmp, fac);
    outcol.a = col1.a;
  }
}

void node_mix_soft(float fac,
                   float3 facvec,
                   float f1,
                   float f2,
                   float3 v1,
                   float3 v2,
                   float4 col1,
                   float4 col2,
                   out float outfloat,
                   out float3 outvec,
                   out float4 outcol)
{

  float facm = 1.0f - fac;

  float4 one = float4(1.0f);
  float4 scr = one - (one - col2) * (one - col1);
  outcol = facm * col1 + fac * ((one - col1) * col2 * col1 + col1 * scr);
  outcol.a = col1.a;
}

void node_mix_linear(float fac,
                     float3 facvec,
                     float f1,
                     float f2,
                     float3 v1,
                     float3 v2,
                     float4 col1,
                     float4 col2,
                     out float outfloat,
                     out float3 outvec,
                     out float4 outcol)
{

  outcol = col1 + fac * (2.0f * (col2 - float4(0.5f)));
  outcol.a = col1.a;
}

void node_mix_float(float fac,
                    float3 facvec,
                    float f1,
                    float f2,
                    float3 v1,
                    float3 v2,
                    float4 col1,
                    float4 col2,
                    out float outfloat,
                    out float3 outvec,
                    out float4 outcol)
{

  outfloat = mix(f1, f2, fac);
}

void node_mix_vector(float fac,
                     float3 facvec,
                     float f1,
                     float f2,
                     float3 v1,
                     float3 v2,
                     float4 col1,
                     float4 col2,
                     out float outfloat,
                     out float3 outvec,
                     out float4 outcol)
{

  outvec = mix(v1, v2, fac);
}

void node_mix_vector_non_uniform(float fac,
                                 float3 facvec,
                                 float f1,
                                 float f2,
                                 float3 v1,
                                 float3 v2,
                                 float4 col1,
                                 float4 col2,
                                 out float outfloat,
                                 out float3 outvec,
                                 out float4 outcol)
{
  outvec = mix(v1, v2, facvec);
}

void node_mix_rgba(float fac,
                   float3 facvec,
                   float f1,
                   float f2,
                   float3 v1,
                   float3 v2,
                   float4 col1,
                   float4 col2,
                   out float outfloat,
                   out float3 outvec,
                   out float4 outcol)
{
  outcol = mix(col1, col2, fac);
}

void node_mix_clamp_color(float4 col, float4 min, float4 max, out float4 out_col)
{
  out_col = clamp(col, min, max);
}

void node_mix_clamp_vector(float3 vec, float3 min, float3 max, out float3 outvec)
{
  outvec = clamp(vec, min, max);
}

void node_mix_clamp_value(float value, float min, float max, out float outfloat)
{
  outfloat = clamp(value, min, max);
}
