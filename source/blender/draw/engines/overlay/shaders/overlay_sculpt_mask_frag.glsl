/* SPDX-FileCopyrightText: 2020-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "infos/overlay_sculpt_info.hh"

FRAGMENT_SHADER_CREATE_INFO(overlay_sculpt_mask)

void main()
{
  fragColor = vec4(faceset_color * mask_color, 1.0);
}
