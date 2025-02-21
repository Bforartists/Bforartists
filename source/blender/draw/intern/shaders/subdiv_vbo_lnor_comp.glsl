/* SPDX-FileCopyrightText: 2021-2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "subdiv_lib.glsl"

COMPUTE_SHADER_CREATE_INFO(subdiv_loop_normals)

bool is_face_selected(uint coarse_quad_index)
{
  return (extra_coarse_face_data[coarse_quad_index] & shader_data.coarse_face_select_mask) != 0;
}

bool is_face_hidden(uint coarse_quad_index)
{
  return (extra_coarse_face_data[coarse_quad_index] & shader_data.coarse_face_hidden_mask) != 0;
}

/* Flag for paint mode overlay and normals drawing in edit-mode. */
float get_loop_flag(uint coarse_quad_index, int vert_origindex)
{
  if (is_face_hidden(coarse_quad_index) || (shader_data.is_edit_mode && vert_origindex == -1)) {
    return -1.0;
  }
  if (is_face_selected(coarse_quad_index)) {
    return 1.0;
  }
  return 0.0;
}

void main()
{
  /* We execute for each quad. */
  uint quad_index = get_global_invocation_index();
  if (quad_index >= shader_data.total_dispatch_size) {
    return;
  }

  /* The start index of the loop is quad_index * 4. */
  uint start_loop_index = quad_index * 4;

  uint coarse_quad_index = coarse_face_index_from_subdiv_quad_index(quad_index,
                                                                    shader_data.coarse_face_count);

  if ((extra_coarse_face_data[coarse_quad_index] & shader_data.coarse_face_smooth_mask) != 0) {
    /* Face is smooth, use vertex normals. */
    for (int i = 0; i < 4; i++) {
      PosNorLoop pos_nor_loop = pos_nor[start_loop_index + i];
      int origindex = input_vert_origindex[start_loop_index + i];
      LoopNormal loop_normal = subdiv_get_normal_and_flag(pos_nor_loop);
      loop_normal.flag = get_loop_flag(coarse_quad_index, origindex);

      output_lnor[start_loop_index + i] = loop_normal;
    }
  }
  else {
    PosNorLoop pos_nor0 = pos_nor[start_loop_index + 0];
    PosNorLoop pos_nor1 = pos_nor[start_loop_index + 1];
    PosNorLoop pos_nor2 = pos_nor[start_loop_index + 2];
    PosNorLoop pos_nor3 = pos_nor[start_loop_index + 3];
    vec3 v0 = subdiv_get_vertex_pos(pos_nor0);
    vec3 v1 = subdiv_get_vertex_pos(pos_nor1);
    vec3 v2 = subdiv_get_vertex_pos(pos_nor2);
    vec3 v3 = subdiv_get_vertex_pos(pos_nor3);

    vec3 face_normal = vec3(0.0);
    add_newell_cross_v3_v3v3(face_normal, v0, v1);
    add_newell_cross_v3_v3v3(face_normal, v1, v2);
    add_newell_cross_v3_v3v3(face_normal, v2, v3);
    add_newell_cross_v3_v3v3(face_normal, v3, v0);

    face_normal = normalize(face_normal);

    LoopNormal loop_normal;
    loop_normal.nx = face_normal.x;
    loop_normal.ny = face_normal.y;
    loop_normal.nz = face_normal.z;

    for (int i = 0; i < 4; i++) {
      int origindex = input_vert_origindex[start_loop_index + i];
      loop_normal.flag = get_loop_flag(coarse_quad_index, origindex);

      output_lnor[start_loop_index + i] = loop_normal;
    }
  }
}
