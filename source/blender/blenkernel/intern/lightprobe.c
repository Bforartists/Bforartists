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

#include "DNA_collection_types.h"
#include "DNA_defaults.h"
#include "DNA_lightprobe_types.h"
#include "DNA_object_types.h"

#include "BLI_utildefines.h"

#include "BKE_idtype.h"
#include "BKE_lib_id.h"
#include "BKE_lib_query.h"
#include "BKE_lightprobe.h"
#include "BKE_main.h"

#include "BLT_translation.h"

static void lightprobe_init_data(ID *id)
{
  LightProbe *probe = (LightProbe *)id;
  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(probe, id));

  MEMCPY_STRUCT_AFTER(probe, DNA_struct_default_get(LightProbe), id);
}

static void lightprobe_foreach_id(ID *id, LibraryForeachIDData *data)
{
  LightProbe *probe = (LightProbe *)id;

  BKE_LIB_FOREACHID_PROCESS(data, probe->image, IDWALK_CB_USER);
  BKE_LIB_FOREACHID_PROCESS(data, probe->visibility_grp, IDWALK_CB_NOP);
}

IDTypeInfo IDType_ID_LP = {
    .id_code = ID_LP,
    .id_filter = FILTER_ID_LP,
    .main_listbase_index = INDEX_ID_LP,
    .struct_size = sizeof(LightProbe),
    .name = "LightProbe",
    .name_plural = "lightprobes",
    .translation_context = BLT_I18NCONTEXT_ID_LIGHTPROBE,
    .flags = 0,

    .init_data = lightprobe_init_data,
    .copy_data = NULL,
    .free_data = NULL,
    .make_local = NULL,
    .foreach_id = lightprobe_foreach_id,
};

void BKE_lightprobe_type_set(LightProbe *probe, const short lightprobe_type)
{
  probe->type = lightprobe_type;

  switch (probe->type) {
    case LIGHTPROBE_TYPE_GRID:
      probe->distinf = 0.3f;
      probe->falloff = 1.0f;
      probe->clipsta = 0.01f;
      break;
    case LIGHTPROBE_TYPE_PLANAR:
      probe->distinf = 0.1f;
      probe->falloff = 0.5f;
      probe->clipsta = 0.001f;
      break;
    case LIGHTPROBE_TYPE_CUBE:
      probe->attenuation_type = LIGHTPROBE_SHAPE_ELIPSOID;
      break;
    default:
      BLI_assert(!"LightProbe type not configured.");
      break;
  }
}

void *BKE_lightprobe_add(Main *bmain, const char *name)
{
  LightProbe *probe;

  probe = BKE_libblock_alloc(bmain, ID_LP, name, 0);

  lightprobe_init_data(&probe->id);

  return probe;
}

LightProbe *BKE_lightprobe_copy(Main *bmain, const LightProbe *probe)
{
  LightProbe *probe_copy;
  BKE_id_copy(bmain, &probe->id, (ID **)&probe_copy);
  return probe_copy;
}
