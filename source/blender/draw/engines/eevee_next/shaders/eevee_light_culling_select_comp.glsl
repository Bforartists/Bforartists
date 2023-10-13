/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/**
 * Select the visible items inside the active view and put them inside the sorting buffer.
 */

#pragma BLENDER_REQUIRE(draw_view_lib.glsl)
#pragma BLENDER_REQUIRE(draw_math_geom_lib.glsl)
#pragma BLENDER_REQUIRE(draw_intersect_lib.glsl)

void main()
{
  uint l_idx = gl_GlobalInvocationID.x;
  if (l_idx >= light_cull_buf.items_count) {
    return;
  }

  LightData light = in_light_buf[l_idx];

  /* Do not select 0 power lights. */
  if (light.influence_radius_max < 1e-8) {
    return;
  }

  /* Sun lights are packed at the end of the array. Perform early copy. */
  if (is_sun_light(light.type)) {
    /* NOTE: We know the index because sun lights are packed at the start of the input buffer. */
    out_light_buf[light_cull_buf.local_lights_len + l_idx] = light;
    return;
  }

  Sphere sphere;
  switch (light.type) {
    case LIGHT_SPOT:
      /* Only for < ~170 degree Cone due to plane extraction precision. */
      if (light.spot_tan < 10.0) {
        Pyramid pyramid = shape_pyramid_non_oblique(
            light._position,
            light._position - light._back * light.influence_radius_max,
            light._right * light.influence_radius_max * light.spot_tan / light.spot_size_inv.x,
            light._up * light.influence_radius_max * light.spot_tan / light.spot_size_inv.y);
        if (!intersect_view(pyramid)) {
          return;
        }
      }
    case LIGHT_RECT:
    case LIGHT_ELLIPSE:
    case LIGHT_POINT:
      sphere.center = light._position;
      sphere.radius = light.influence_radius_max;
      break;
    default:
      break;
  }

  /* TODO(fclem): HiZ culling? Could be quite beneficial given the nature of the 2.5D culling. */

  /* TODO(fclem): Small light culling / fading? */

  if (intersect_view(sphere)) {
    uint index = atomicAdd(light_cull_buf.visible_count, 1u);

    float z_dist = dot(drw_view_forward(), light._position) -
                   dot(drw_view_forward(), drw_view_position());
    out_zdist_buf[index] = z_dist;
    out_key_buf[index] = l_idx;
  }
}
