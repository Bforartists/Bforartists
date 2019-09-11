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
 * The Original Code is Copyright (C) Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup bke
 */

#include <string.h>

#include "DNA_object_types.h"
#include "DNA_lightprobe_types.h"
#include "DNA_defaults.h"

#include "BLI_utildefines.h"

#include "BKE_animsys.h"
#include "BKE_library.h"
#include "BKE_lightprobe.h"
#include "BKE_main.h"

void BKE_lightprobe_init(LightProbe *probe)
{
  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(probe, id));

  MEMCPY_STRUCT_AFTER(probe, DNA_struct_default_get(LightProbe), id);
}

void *BKE_lightprobe_add(Main *bmain, const char *name)
{
  LightProbe *probe;

  probe = BKE_libblock_alloc(bmain, ID_LP, name, 0);

  BKE_lightprobe_init(probe);

  return probe;
}

/**
 * Only copy internal data of #LightProbe ID from source
 * to already allocated/initialized destination.
 * You probably never want to use that directly,
 * use #BKE_id_copy or #BKE_id_copy_ex for typical needs.
 *
 * WARNING! This function will not handle ID user count!
 *
 * \param flag: Copying options (see BKE_library.h's LIB_ID_COPY_... flags for more).
 */
void BKE_lightprobe_copy_data(Main *UNUSED(bmain),
                              LightProbe *UNUSED(probe_dst),
                              const LightProbe *UNUSED(probe_src),
                              const int UNUSED(flag))
{
  /* Nothing to do here. */
}

LightProbe *BKE_lightprobe_copy(Main *bmain, const LightProbe *probe)
{
  LightProbe *probe_copy;
  BKE_id_copy(bmain, &probe->id, (ID **)&probe_copy);
  return probe_copy;
}

void BKE_lightprobe_make_local(Main *bmain, LightProbe *probe, const bool lib_local)
{
  BKE_id_make_local_generic(bmain, &probe->id, true, lib_local);
}

void BKE_lightprobe_free(LightProbe *probe)
{
  BKE_animdata_free((ID *)probe, false);
}
