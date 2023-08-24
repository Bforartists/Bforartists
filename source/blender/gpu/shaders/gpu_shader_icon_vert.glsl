/* SPDX-FileCopyrightText: 2018-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Simple shader that just draw one icon at the specified location
 * does not need any vertex input (producing less call to immBegin/End)
 */

void main()
{
  vec2 uv;
  vec2 co;

  if (gl_VertexID == 0) {
    co = rect_geom.xw;
    uv = rect_icon.xw;
    mask_coord_interp = vec2(0, 1);
  }
  else if (gl_VertexID == 1) {
    co = rect_geom.xy;
    uv = rect_icon.xy;
    mask_coord_interp = vec2(0, 0);
  }
  else if (gl_VertexID == 2) {
    co = rect_geom.zw;
    uv = rect_icon.zw;
    mask_coord_interp = vec2(1, 1);
  }
  else {
    co = rect_geom.zy;
    uv = rect_icon.zy;
    mask_coord_interp = vec2(1, 0);
  }

  /* Put origin in lower right corner. */
  mask_coord_interp.x -= 1;

  gl_Position = ModelViewProjectionMatrix * vec4(co, 0.0f, 1.0f);
  texCoord_interp = uv;
}
