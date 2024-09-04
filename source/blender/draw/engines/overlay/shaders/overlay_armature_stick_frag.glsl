/* SPDX-FileCopyrightText: 2018-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma BLENDER_REQUIRE(select_lib.glsl)

void main()
{
  float fac = smoothstep(1.0, 0.2, colorFac);
  fragColor.rgb = mix(finalInnerColor.rgb, finalWireColor.rgb, fac);
  fragColor.a = alpha;
  lineOutput = vec4(0.0);
  select_id_output(select_id);
}
