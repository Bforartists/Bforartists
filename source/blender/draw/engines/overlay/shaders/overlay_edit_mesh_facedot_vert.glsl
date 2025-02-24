/* SPDX-FileCopyrightText: 2017-2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/overlay_edit_mode_info.hh"

VERTEX_SHADER_CREATE_INFO(overlay_edit_mesh_facedot)

#ifdef GLSL_CPP_STUBS
#  define FACEDOT
#endif

#include "overlay_edit_mesh_lib.glsl"

void main()
{
  VertIn vert_in;
  vert_in.lP = pos;
  vert_in.lN = norAndFlag.xyz;
  vert_in.e_data = data;

  /* Vertex, Face-dot and Face case. */
  VertOut vert_out = vertex_main(vert_in);

  gl_Position = vert_out.gpu_position;
  finalColor = vert_out.final_color;
}
