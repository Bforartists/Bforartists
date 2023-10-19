/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(draw_model_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_math_base_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_math_vector_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_codegen_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_nodetree_lib.glsl)
#pragma BLENDER_REQUIRE(eevee_sampling_lib.glsl)

#if defined(USE_BARYCENTRICS) && defined(GPU_FRAGMENT_SHADER) && defined(MAT_GEOM_MESH)
vec3 barycentric_distances_get()
{
#  if defined(GPU_METAL)
  /* Calculate Barycentric distances from available parameters in Metal. */
  float wp_delta = length(dfdx(interp.P)) + length(dfdy(interp.P));
  float bc_delta = length(dfdx(gpu_BaryCoord)) + length(dfdy(gpu_BaryCoord));
  float rate_of_change = wp_delta / bc_delta;
  vec3 dists;
  dists.x = rate_of_change * (1.0 - gpu_BaryCoord.x);
  dists.y = rate_of_change * (1.0 - gpu_BaryCoord.y);
  dists.z = rate_of_change * (1.0 - gpu_BaryCoord.z);
#  else
  /* NOTE: No need to undo perspective divide since it has not been applied. */
  vec3 pos0 = (ProjectionMatrixInverse * gpu_position_at_vertex(0)).xyz;
  vec3 pos1 = (ProjectionMatrixInverse * gpu_position_at_vertex(1)).xyz;
  vec3 pos2 = (ProjectionMatrixInverse * gpu_position_at_vertex(2)).xyz;
  vec3 edge21 = pos2 - pos1;
  vec3 edge10 = pos1 - pos0;
  vec3 edge02 = pos0 - pos2;
  vec3 d21 = safe_normalize(edge21);
  vec3 d10 = safe_normalize(edge10);
  vec3 d02 = safe_normalize(edge02);
  vec3 dists;
  float d = dot(d21, edge02);
  dists.x = sqrt(dot(edge02, edge02) - d * d);
  d = dot(d02, edge10);
  dists.y = sqrt(dot(edge10, edge10) - d * d);
  d = dot(d10, edge21);
  dists.z = sqrt(dot(edge21, edge21) - d * d);
#  endif
  return dists;
}
#endif

void init_globals_mesh()
{
#if defined(USE_BARYCENTRICS) && defined(GPU_FRAGMENT_SHADER) && defined(MAT_GEOM_MESH)
  g_data.barycentric_coords = gpu_BaryCoord.xy;
  g_data.barycentric_dists = barycentric_distances_get();
#endif
}

void init_globals_curves()
{
#if defined(MAT_GEOM_CURVES)
  /* Shade as a cylinder. */
  float cos_theta = curve_interp.time_width / curve_interp.thickness;
#  if defined(GPU_FRAGMENT_SHADER)
  if (hairThicknessRes == 1) {
#    ifdef EEVEE_UTILITY_TX
    /* Random cosine normal distribution on the hair surface. */
    float noise = utility_tx_fetch(utility_tx, gl_FragCoord.xy, UTIL_BLUE_NOISE_LAYER).x;
#      ifdef EEVEE_SAMPLING_DATA
    /* Needs to check for SAMPLING_DATA,
     * otherwise Surfel and World (?!?!) shader validation fails. */
    noise = fract(noise + sampling_rng_1D_get(SAMPLING_CURVES_U));
#      endif
    cos_theta = noise * 2.0 - 1.0;
#    endif
  }
#  endif
  float sin_theta = sqrt(max(0.0, 1.0 - cos_theta * cos_theta));
  g_data.N = g_data.Ni = normalize(interp.N * sin_theta + curve_interp.binormal * cos_theta);

  /* Costly, but follows cycles per pixel tangent space (not following curve shape). */
  vec3 V = drw_world_incident_vector(g_data.P);
  g_data.curve_T = -curve_interp.tangent;
  g_data.curve_B = cross(V, g_data.curve_T);
  g_data.curve_N = safe_normalize(cross(g_data.curve_T, g_data.curve_B));

  g_data.is_strand = true;
  g_data.hair_time = curve_interp.time;
  g_data.hair_thickness = curve_interp.thickness;
  g_data.hair_strand_id = curve_interp_flat.strand_id;
#  if defined(USE_BARYCENTRICS) && defined(GPU_FRAGMENT_SHADER)
  g_data.barycentric_coords = hair_resolve_barycentric(curve_interp.barycentric_coords);
#  endif
#endif
}

void init_globals_gpencil()
{
  /* Undo back-face flip as the grease-pencil normal is already pointing towards the camera. */
  g_data.N = g_data.Ni = interp.N;
}

void init_globals()
{
  /* Default values. */
  g_data.P = interp.P;
  g_data.Ni = interp.N;
  g_data.N = safe_normalize(interp.N);
  g_data.Ng = g_data.N;
  g_data.is_strand = false;
  g_data.hair_time = 0.0;
  g_data.hair_thickness = 0.0;
  g_data.hair_strand_id = 0;
  g_data.ray_type = RAY_TYPE_CAMERA; /* TODO */
  g_data.ray_depth = 0.0;
  g_data.ray_length = distance(g_data.P, drw_view_position());
  g_data.barycentric_coords = vec2(0.0);
  g_data.barycentric_dists = vec3(0.0);

#ifdef GPU_FRAGMENT_SHADER
  g_data.N = (FrontFacing) ? g_data.N : -g_data.N;
  g_data.Ni = (FrontFacing) ? g_data.Ni : -g_data.Ni;
  g_data.Ng = safe_normalize(cross(dFdx(g_data.P), dFdy(g_data.P)));
#endif

#if defined(MAT_GEOM_MESH)
  init_globals_mesh();
#elif defined(MAT_GEOM_CURVES)
  init_globals_curves();
#elif defined(MAT_GEOM_GPENCIL)
  init_globals_gpencil();
#endif
}

/* Avoid some compiler issue with non set interface parameters. */
void init_interface()
{
#ifdef GPU_VERTEX_SHADER
  interp.P = vec3(0.0);
  interp.N = vec3(0.0);
  drw_ResourceID_iface.resource_index = resource_id;
#endif
}

#if defined(GPU_VERTEX_SHADER) && defined(MAT_SHADOW)
void shadow_viewport_layer_set(int view_id, int lod)
{
  /* We still render to a layered frame-buffer in the case of Metal + Tile Based Renderer.
   * Since it needs correct depth buffering, each view needs to not overlap each others.
   * It doesn't matter much for other platform, so we use that as a way to pass the view id. */
  gpu_Layer = view_id;
  gpu_ViewportIndex = lod;
}
#endif

#if defined(GPU_FRAGMENT_SHADER) && defined(MAT_SHADOW)
int shadow_view_id_get()
{
  return gpu_Layer;
}
#endif
