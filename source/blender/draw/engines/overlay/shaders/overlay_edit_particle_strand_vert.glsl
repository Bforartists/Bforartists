/* SPDX-FileCopyrightText: 2016-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "common_view_clipping_lib.glsl"
#include "common_view_lib.glsl"

#define no_active_weight 666.0

vec3 weight_to_rgb(float t)
{
  if (t == no_active_weight) {
    /* No weight. */
    return colorWire.rgb;
  }
  if (t > 1.0 || t < 0.0) {
    /* Error color */
    return vec3(1.0, 0.0, 1.0);
  }
  else {
    return texture(weightTex, t).rgb;
  }
}

void main()
{
  vec3 world_pos = point_object_to_world(pos);
  gl_Position = point_world_to_ndc(world_pos);

  if (useWeight) {
    finalColor = vec4(weight_to_rgb(selection), 1.0);
  }
  else {
    vec4 use_color = useGreasePencil ? colorGpencilVertexSelect : colorVertexSelect;
    finalColor = mix(colorWireEdit, use_color, selection);
  }

  view_clipping_distances(world_pos);
}
