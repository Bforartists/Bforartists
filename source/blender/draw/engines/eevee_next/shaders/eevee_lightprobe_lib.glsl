/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(gpu_shader_utildefines_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_math_vector_lib.glsl)

vec3 lightprobe_irradiance_grid_sample_position(mat4 grid_local_to_world_mat,
                                                ivec3 grid_res,
                                                ivec3 cell_coord)
{
  vec3 ls_cell_pos = (vec3(cell_coord) + vec3(0.5)) / vec3(grid_res);
  ls_cell_pos = ls_cell_pos * 2.0 - 1.0;
  vec3 ws_cell_pos = (grid_local_to_world_mat * vec4(ls_cell_pos, 1.0)).xyz;
  return ws_cell_pos;
}

/**
 * Return true if sample position is valid.
 * \a r_lP is the local position in grid units [0..grid_size).
 */
bool lightprobe_irradiance_grid_local_coord(IrradianceGridData grid_data, vec3 P, out vec3 r_lP)
{
  /* Position in cell units. */
  /* NOTE: The vector-matrix multiplication swapped on purpose to cancel the matrix transpose. */
  vec3 lP = (vec4(P, 1.0) * grid_data.world_to_grid_transposed).xyz;
  r_lP = clamp(lP, vec3(0.0), vec3(grid_data.grid_size) - 1e-5);
  /* Sample is valid if position wasn't clamped. */
  return all(equal(lP, r_lP));
}

int lightprobe_irradiance_grid_brick_index_get(IrradianceGridData grid_data, ivec3 brick_coord)
{
  int3 grid_size_in_bricks = divide_ceil(grid_data.grid_size,
                                         int3(IRRADIANCE_GRID_BRICK_SIZE - 1));
  int brick_index = grid_data.brick_offset;
  brick_index += brick_coord.x;
  brick_index += brick_coord.y * grid_size_in_bricks.x;
  brick_index += brick_coord.z * grid_size_in_bricks.x * grid_size_in_bricks.y;
  return brick_index;
}

/* Return cell corner from a corner ID [0..7]. */
ivec3 lightprobe_irradiance_grid_cell_corner(int cell_corner_id)
{
  return (ivec3(cell_corner_id) >> ivec3(0, 1, 2)) & 1;
}

float lightprobe_planar_score(ProbePlanarData planar, vec3 P, vec3 V, vec3 L)
{
  vec3 lP = vec4(P, 1.0) * planar.world_to_object_transposed;
  if (any(greaterThan(abs(lP), vec3(1.0)))) {
    /* TODO: Transition in Z. Dither? */
    return 0.0;
  }
  /* Return how much the ray is lined up with the captured ray. */
  vec3 R = -reflect(V, planar.normal);
  return saturate(dot(L, R));
}

#ifdef PLANAR_PROBES
/**
 * Return the best planar probe index for a given light direction vector and position.
 */
int lightprobe_planar_select(vec3 P, vec3 V, vec3 L)
{
  /* Initialize to the score of a camera ray. */
  float best_score = saturate(dot(L, -V));
  int best_index = -1;

  for (int index = 0; index < PLANAR_PROBES_MAX; index++) {
    if (probe_planar_buf[index].layer_id == -1) {
      /* ProbePlanarData doesn't contain any gap, exit at first item that is invalid. */
      break;
    }
    float score = lightprobe_planar_score(probe_planar_buf[index], P, V, L);
    if (score > best_score) {
      best_score = score;
      best_index = index;
    }
  }
  return best_index;
}
#endif
