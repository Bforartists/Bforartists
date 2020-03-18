/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2019 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup depsgraph
 */

#include "intern/eval/deg_eval_runtime_backup_volume.h"

#include "BLI_assert.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "DNA_volume_types.h"

#include "BKE_volume.h"

#include <stdio.h>

namespace DEG {

VolumeBackup::VolumeBackup(const Depsgraph * /*depsgraph*/) : grids(nullptr)
{
}

void VolumeBackup::init_from_volume(Volume *volume)
{
  STRNCPY(filepath, volume->filepath);
  BLI_STATIC_ASSERT(sizeof(filepath) == sizeof(volume->filepath),
                    "VolumeBackup filepath length wrong");

  grids = volume->runtime.grids;
  volume->runtime.grids = nullptr;
}

void VolumeBackup::restore_to_volume(Volume *volume)
{
  if (grids) {
    BKE_volume_grids_backup_restore(volume, grids, filepath);
    grids = nullptr;
  }
}

}  // namespace DEG
