/* SPDX-FileCopyrightText: 2016-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

void main()
{
  fragColor = simple_lighting_data.l_color;
  fragColor.xyz *= clamp(dot(normalize(normal), simple_lighting_data.light), 0.0, 1.0);
}
