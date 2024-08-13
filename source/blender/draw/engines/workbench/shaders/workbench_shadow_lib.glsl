/* SPDX-FileCopyrightText: 2022-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(common_view_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_utildefines_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_math_vector_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_attribute_load_lib.glsl)
#pragma BLENDER_REQUIRE(gpu_shader_index_load_lib.glsl)

struct VertIn {
  /* Local position. */
  vec3 lP;
};

VertIn input_assembly(uint in_vertex_id)
{
  uint v_i = gpu_index_load(in_vertex_id);

  VertIn vert_in;
  vert_in.lP = gpu_attr_load_float3(pos, gpu_attr_3, v_i);
  return vert_in;
}

struct VertOut {
  /* Local position. */
  vec3 lP;
  /* Final NDC position. */
  vec4 frontPosition;
  vec4 backPosition;
};

VertOut vertex_main(VertIn vert_in)
{
  VertOut vert_out;
  vert_out.lP = vert_in.lP;
  vec3 L = pass_data.light_direction_ws;

  vec3 ws_P = point_object_to_world(vert_in.lP);
  float extrude_distance = 1e5f;
  float L_FP = dot(L, pass_data.far_plane.xyz);
  if (L_FP > 0.0) {
    float signed_distance = dot(pass_data.far_plane.xyz, ws_P) - pass_data.far_plane.w;
    extrude_distance = -signed_distance / L_FP;
    /* Ensure we don't overlap the far plane. */
    extrude_distance -= 1e-3;
  }
  vert_out.backPosition = point_world_to_ndc(ws_P + L * extrude_distance);
  vert_out.frontPosition = point_object_to_ndc(vert_in.lP);
  return vert_out;
}

struct GeomOut {
  vec4 gpu_position;
};

void export_vertex(GeomOut geom_out)
{
  gl_Position = geom_out.gpu_position;
#ifdef GPU_METAL
  /* Apply depth bias. Prevents Z-fighting artifacts when fast-math is enabled. */
  gl_Position.z += 0.00005;
#endif
}

void strip_EmitVertex(const uint strip_index,
                      uint out_vertex_id,
                      uint out_primitive_id,
                      GeomOut geom_out)
{
  bool is_odd_primitive = (out_primitive_id & 1u) != 0u;
  /* Maps triangle list primitives to triangle strip indices. */
  uint out_strip_index = (is_odd_primitive ? (2u - out_vertex_id) : out_vertex_id) +
                         out_primitive_id;

  if (out_strip_index == strip_index) {
    export_vertex(geom_out);
  }
}

void tri_EmitVertex(const uint tri_index, uint out_vertex_id, GeomOut geom_out)
{
  if (out_vertex_id == tri_index) {
    export_vertex(geom_out);
  }
}
