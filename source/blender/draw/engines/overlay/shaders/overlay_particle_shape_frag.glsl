/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/overlay_extra_info.hh"

FRAGMENT_SHADER_CREATE_INFO(overlay_particle_shape_base)

#include "overlay_common_lib.glsl"
#include "select_lib.glsl"

void main()
{
  fragColor = finalColor;

  lineOutput = pack_line_data(gl_FragCoord.xy, edgeStart, edgePos);

  select_id_output(select_id);
}
