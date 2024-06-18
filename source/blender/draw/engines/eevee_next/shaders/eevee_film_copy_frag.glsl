/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * `eevee_film_copy_frag` is used to work around Metal/Intel iGPU issues.
 *
 * Caches are not flushed in the eevee_film_frag shader due to unsupported read/write access.
 * We schedule the eevee_film_comp shader instead. Resources are attached read only and does the
 * part that is missing from the eevee_film_frag shader.
 *
 * Code is duplicated here to ensure that the compiler will pass read/write resource checks.
 */
#pragma BLENDER_REQUIRE(draw_view_lib.glsl)
#pragma BLENDER_REQUIRE(common_math_lib.glsl)

vec4 cryptomatte_false_color(float hash)
{
  uint m3hash = floatBitsToUint(hash);
  return vec4(hash,
              float(m3hash << 8) / float(0xFFFFFFFFu),
              float(m3hash << 16) / float(0xFFFFFFFFu),
              1.0);
}

void main()
{
  ivec2 texel = ivec2(gl_FragCoord.xy);

  if (display_id == -1) {
    out_color = texelFetch(in_combined_tx, texel, 0);
  }
  else if (uniform_buf.film.display_storage_type == PASS_STORAGE_VALUE) {
    out_color.rgb = imageLoad(value_accum_img, ivec3(texel, display_id)).rrr;
    out_color.a = 1.0;
  }
  else if (uniform_buf.film.display_storage_type == PASS_STORAGE_COLOR) {
    out_color = imageLoad(color_accum_img, ivec3(texel, display_id));
  }
  else /* PASS_STORAGE_CRYPTOMATTE */ {
    out_color = cryptomatte_false_color(imageLoad(cryptomatte_img, ivec3(texel, display_id)).r);
  }

  float out_depth = imageLoad(depth_img, texel).r;
  out_depth = drw_depth_view_to_screen(-out_depth);
  out_depth += 2.4e-7 * 4.0 + fwidth(out_depth);
  gl_FragDepth = saturate(out_depth);
}
