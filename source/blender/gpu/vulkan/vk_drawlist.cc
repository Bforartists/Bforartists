/* SPDX-FileCopyrightText: 2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup gpu
 */

#include "GPU_batch.h"

#include "vk_drawlist.hh"

namespace blender::gpu {

void VKDrawList::append(GPUBatch *batch, int instance_first, int instance_count)
{
  GPU_batch_draw_advanced(batch, 0, 0, instance_first, instance_count);
}

void VKDrawList::submit() {}

}  // namespace blender::gpu
