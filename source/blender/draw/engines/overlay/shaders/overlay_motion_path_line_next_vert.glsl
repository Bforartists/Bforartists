/* SPDX-FileCopyrightText: 2018-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "common_view_clipping_lib.glsl"
#include "draw_view_lib.glsl"

#include "gpu_shader_attribute_load_lib.glsl"
#include "gpu_shader_index_load_lib.glsl"
#include "gpu_shader_math_matrix_lib.glsl"
#include "gpu_shader_math_vector_lib.glsl"
#include "gpu_shader_utildefines_lib.glsl"

struct VertIn {
  vec3 P;
  uint vert_id;
};

VertIn input_assembly(uint in_vertex_id)
{
  uint v_i = gpu_index_load(in_vertex_id);

  VertIn vert_in;
  vert_in.P = gpu_attr_load_float3(pos, gpu_attr_0, v_i);
  vert_in.vert_id = v_i;
  return vert_in;
}

struct VertOut {
  vec3 ws_P;
  vec4 hs_P;
  vec2 ss_P;
  vec4 color;
};

#define frameCurrent mpathLineSettings.x
#define frameStart mpathLineSettings.y
#define frameEnd mpathLineSettings.z
#define cacheStart mpathLineSettings.w

VertOut vertex_main(VertIn vert_in)
{
  VertOut vert_out;
  /* Optionally transform from view space to world space for screen space motion paths. */
  vert_out.ws_P = transform_point(camera_space_matrix, vert_in.P);
  vert_out.hs_P = drw_point_world_to_homogenous(vert_out.ws_P);
  vert_out.ss_P = drw_ndc_to_screen(drw_perspective_divide(vert_out.hs_P)).xy * sizeViewport.xy;

  int frame = int(vert_in.vert_id) + cacheStart;

  vec3 blend_base = (abs(frame - frameCurrent) == 0) ?
                        colorCurrentFrame.rgb :
                        colorBackground.rgb; /* "bleed" CFRAME color to ease color blending */
  bool use_custom_color = customColorPre.x >= 0.0;

  if (frame < frameCurrent) {
    vert_out.color.rgb = use_custom_color ? customColorPre : colorBeforeFrame.rgb;
  }
  else if (frame > frameCurrent) {
    vert_out.color.rgb = use_custom_color ? customColorPost : colorAfterFrame.rgb;
  }
  else /* if (frame == frameCurrent) */ {
    vert_out.color.rgb = use_custom_color ? colorCurrentFrame.rgb : blend_base;
  }
  vert_out.color.a = 1.0;

  return vert_out;
}

struct GeomOut {
  vec4 gpu_position;
  vec4 color;
  vec3 ws_P;
};

void strip_EmitVertex(const uint strip_index,
                      uint out_vertex_id,
                      uint out_primitive_id,
                      GeomOut geom_out)
{
  bool is_odd_primitive = (out_primitive_id & 1u) != 0u;
  /* Maps triangle list primitives to triangle strip indices. */
  uint out_strip_index = (is_odd_primitive ? (2u - out_vertex_id) : out_vertex_id) +
                         out_primitive_id;

  if (out_strip_index != strip_index) {
    return;
  }

  interp.color = geom_out.color;
  gl_Position = geom_out.gpu_position;

  view_clipping_distances(geom_out.ws_P);
}

void geometry_main(VertOut geom_in[2],
                   uint out_vertex_id,
                   uint out_primitive_id,
                   uint out_invocation_id)
{
  vec2 ss_P0 = geom_in[0].ss_P;
  vec2 ss_P1 = geom_in[1].ss_P;

  vec2 edge_dir = orthogonal(normalize(ss_P1 - ss_P0 + 1e-8)) * sizeViewportInv;

  bool is_persp = (drw_view.winmat[3][3] == 0.0);
  float line_size = float(lineThickness) * sizePixel;

  GeomOut geom_out;

  vec2 t0 = edge_dir * (line_size * (is_persp ? geom_in[0].hs_P.w : 1.0));
  geom_out.gpu_position = geom_in[0].hs_P + vec4(t0, 0.0, 0.0);
  geom_out.color = geom_in[0].color;
  geom_out.ws_P = geom_in[0].ws_P;
  strip_EmitVertex(0, out_vertex_id, out_primitive_id, geom_out);

  geom_out.gpu_position = geom_in[0].hs_P - vec4(t0, 0.0, 0.0);
  strip_EmitVertex(1, out_vertex_id, out_primitive_id, geom_out);

  vec2 t1 = edge_dir * (line_size * (is_persp ? geom_in[1].hs_P.w : 1.0));
  geom_out.gpu_position = geom_in[1].hs_P + vec4(t1, 0.0, 0.0);
  geom_out.ws_P = geom_in[1].ws_P;
  geom_out.color = geom_in[1].color;
  strip_EmitVertex(2, out_vertex_id, out_primitive_id, geom_out);

  geom_out.gpu_position = geom_in[1].hs_P - vec4(t1, 0.0, 0.0);
  strip_EmitVertex(3, out_vertex_id, out_primitive_id, geom_out);
}

void main()
{
  /* Point list primitive. */
  const uint input_primitive_vertex_count = 1u;
  /* Triangle list primitive. */
  const uint ouput_primitive_vertex_count = 3u;
  const uint ouput_primitive_count = 2u;
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

  /* Read current and next point. */
  VertIn vert_in[2];
  vert_in[0] = input_assembly(in_primitive_first_vertex + 0u);
  vert_in[1] = input_assembly(in_primitive_first_vertex + 1u);

  VertOut vert_out[2];
  vert_out[0] = vertex_main(vert_in[0]);
  vert_out[1] = vertex_main(vert_in[1]);

  /* Discard by default. */
  gl_Position = vec4(NAN_FLT);
  geometry_main(vert_out, out_vertex_id, out_primitive_id, out_invocation_id);
}
