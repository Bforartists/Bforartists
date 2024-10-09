/* SPDX-FileCopyrightText: 2018-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "common_view_clipping_lib.glsl"
#include "draw_model_lib.glsl"
#include "draw_view_lib.glsl"
#include "gpu_shader_attribute_load_lib.glsl"
#include "gpu_shader_index_load_lib.glsl"
#include "gpu_shader_utildefines_lib.glsl"

uint outline_colorid_get()
{
  eObjectInfoFlag ob_flag = eObjectInfoFlag(floatBitsToUint(drw_infos[resource_id].infos.w));
  bool is_active = flag_test(ob_flag, OBJECT_ACTIVE);

  if (isTransform) {
    return 0u; /* colorTransform */
  }
  else if (is_active) {
    return 3u; /* colorActive */
  }
  else {
    return 1u; /* colorSelect */
  }

  return 0u;
}

struct VertIn {
  vec3 ls_P;
};

VertIn input_assembly(uint in_vertex_id)
{
  uint v_i = gpu_index_load(in_vertex_id);

  VertIn vert_in;
  vert_in.ls_P = gpu_attr_load_float3(pos, gpu_attr_0, v_i);
  return vert_in;
}

/* Replace top 2 bits (of the 16bit output) by outlineId.
 * This leaves 16K different IDs to create outlines between objects.
 * SHIFT = (32 - (16 - 2)) */
#define SHIFT 18u

struct VertOut {
  vec3 ws_P;
  vec4 hs_P;
  vec3 vs_P;
  uint ob_id;
};

VertOut vertex_main(VertIn v_in)
{
  VertOut vert_out;
  vert_out.ws_P = drw_point_object_to_world(v_in.ls_P);
  vert_out.hs_P = drw_point_world_to_homogenous(vert_out.ws_P);
  vert_out.vs_P = drw_point_world_to_view(vert_out.ws_P);

  /* Small bias to always be on top of the geom. */
  vert_out.hs_P.z -= 1e-3;

  /* ID 0 is nothing (background) */
  vert_out.ob_id = uint(resource_handle + 1);

  /* Should be 2 bits only [0..3]. */
  uint outline_id = outline_colorid_get();

  /* Combine for 16bit uint target. */
  vert_out.ob_id = (outline_id << 14u) | ((vert_out.ob_id << SHIFT) >> SHIFT);

  return vert_out;
}

void geometry_main(VertOut geom_in[4],
                   uint out_vertex_id,
                   uint out_primitive_id,
                   uint out_invocation_id)
{
  vec3 view_vec = -drw_view_incident_vector(geom_in[1].vs_P);

  vec3 v10 = geom_in[0].vs_P - geom_in[1].vs_P;
  vec3 v12 = geom_in[2].vs_P - geom_in[1].vs_P;
  vec3 v13 = geom_in[3].vs_P - geom_in[1].vs_P;

  vec3 n0 = cross(v12, v10);
  vec3 n3 = cross(v13, v12);

  float fac0 = dot(view_vec, n0);
  float fac3 = dot(view_vec, n3);

  /* If both adjacent verts are facing the camera the same way,
   * then it isn't an outline edge. */
  if (sign(fac0) == sign(fac3)) {
    return;
  }

  VertOut export_vert = (out_vertex_id == 0) ? geom_in[1] : geom_in[2];

  gl_Position = export_vert.hs_P;
  interp.ob_id = export_vert.ob_id;
  view_clipping_distances(export_vert.ws_P);
}

void main()
{
  /* Line adjacency list primitive. */
  const uint input_primitive_vertex_count = 4u;
  /* Line list primitive. */
  const uint ouput_primitive_vertex_count = 2u;
  const uint ouput_primitive_count = 1u;
  const uint ouput_invocation_count = 1u;
  const uint output_vertex_count_per_invocation = ouput_primitive_count *
                                                  ouput_primitive_vertex_count;
  const uint output_vertex_count_per_input_primitive = output_vertex_count_per_invocation *
                                                       ouput_invocation_count;

  uint in_primitive_id = uint(gl_VertexID) / output_vertex_count_per_input_primitive;
  uint in_primitive_first_vertex = in_primitive_id * input_primitive_vertex_count;

  uint out_vertex_id = uint(gl_VertexID) % ouput_primitive_vertex_count;
  uint out_primitive_id = (uint(gl_VertexID) / ouput_primitive_vertex_count) %
                          ouput_primitive_count;
  uint out_invocation_id = (uint(gl_VertexID) / output_vertex_count_per_invocation) %
                           ouput_invocation_count;

  VertIn vert_in[input_primitive_vertex_count];
  vert_in[0] = input_assembly(in_primitive_first_vertex + 0u);
  vert_in[1] = input_assembly(in_primitive_first_vertex + 1u);
  vert_in[2] = input_assembly(in_primitive_first_vertex + 2u);
  vert_in[3] = input_assembly(in_primitive_first_vertex + 3u);

  VertOut vert_out[input_primitive_vertex_count];
  vert_out[0] = vertex_main(vert_in[0]);
  vert_out[1] = vertex_main(vert_in[1]);
  vert_out[2] = vertex_main(vert_in[2]);
  vert_out[3] = vertex_main(vert_in[3]);

  /* Discard by default. */
  gl_Position = vec4(NAN_FLT);
  geometry_main(vert_out, out_vertex_id, out_primitive_id, out_invocation_id);
}
