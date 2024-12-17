/* SPDX-FileCopyrightText: 2018-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "common_view_clipping_lib.glsl"
#include "common_view_lib.glsl"
#include "select_lib.glsl"

void main()
{
  select_id_set(in_select_buf[gl_InstanceID]);

  vec3 bone_vec = data_buf[gl_InstanceID].tail_sphere.xyz -
                  data_buf[gl_InstanceID].head_sphere.xyz;
  float bone_len = max(1e-8, sqrt(dot(bone_vec, bone_vec)));
  float bone_lenrcp = 1.0 / bone_len;
#ifdef SMOOTH_ENVELOPE
  float sinb = (data_buf[gl_InstanceID].tail_sphere.w - data_buf[gl_InstanceID].head_sphere.w) *
               bone_lenrcp;
#else
  const float sinb = 0.0;
#endif

  vec3 y_axis = bone_vec * bone_lenrcp;
  vec3 z_axis = normalize(cross(data_buf[gl_InstanceID].x_axis.xyz, -y_axis));
  vec3 x_axis = cross(
      y_axis, z_axis); /* cannot trust data_buf[gl_InstanceID].x_axis.xyz to be orthogonal. */

  vec3 sp, nor;
  nor = sp = pos.xyz;

  /* In bone space */
  bool is_head = (pos.z < -sinb);
  sp *= (is_head) ? data_buf[gl_InstanceID].head_sphere.w : data_buf[gl_InstanceID].tail_sphere.w;
  sp.z += (is_head) ? 0.0 : bone_len;

  /* Convert to world space */
  mat3 bone_mat = mat3(x_axis, y_axis, z_axis);
  sp = bone_mat * sp.xzy + data_buf[gl_InstanceID].head_sphere.xyz;
  nor = bone_mat * nor.xzy;

  normalView = to_float3x3(drw_view.viewmat) * nor;

  finalStateColor = data_buf[gl_InstanceID].state_color.xyz;
  finalBoneColor = data_buf[gl_InstanceID].state_color.xyz;

  view_clipping_distances(sp);

  vec4 pos_4d = vec4(sp, 1.0);
  gl_Position = drw_view.winmat * (drw_view.viewmat * pos_4d);
}
