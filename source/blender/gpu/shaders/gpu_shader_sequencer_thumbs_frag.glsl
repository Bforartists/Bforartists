/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(gpu_shader_sequencer_lib.glsl)

void main()
{
  SeqStripThumbData thumb = thumb_data[thumb_id];
  vec2 pos1, pos2, size, center, pos;
  float radius;
  strip_box(thumb.left,
            thumb.right,
            thumb.bottom,
            thumb.top,
            pos_interp,
            pos1,
            pos2,
            size,
            center,
            pos,
            radius);

  /* Sample thumbnail texture, modulate with color. */
  vec4 col = texture(image, texCoord_interp) * thumb.tint_color;

  /* Outside of strip rounded rectangle? */
  float sdf = sdf_rounded_box(pos - center, size, radius);
  if (sdf > 0.0) {
    col = vec4(0.0);
  }

  fragColor = col;
}
