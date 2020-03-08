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
 * along with this program; if not, write to the Free Software  Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2005 by the Blender Foundation.
 * All rights reserved.
 * Modifier stack implementation.
 *
 * BKE_modifier.h contains the function prototypes for this file.
 */

/** \file
 * \ingroup bke
 */

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"

#include "CLG_log.h"

#include "BLT_translation.h"

#include "DNA_ID.h"

#include "BKE_idcode.h"

#include "BKE_idtype.h"

// static CLG_LogRef LOG = {"bke.idtype"};

static IDTypeInfo *id_types[INDEX_ID_MAX] = {NULL};

static void id_type_init(void)
{
#define INIT_TYPE(_id_code) \
  { \
    BLI_assert(IDType_##_id_code.main_listbase_index == INDEX_##_id_code); \
    id_types[INDEX_##_id_code] = &IDType_##_id_code; \
  } \
  (void)0

  INIT_TYPE(ID_SCE);
  INIT_TYPE(ID_LI);
  INIT_TYPE(ID_OB);
  INIT_TYPE(ID_ME);
  INIT_TYPE(ID_CU);
  INIT_TYPE(ID_MB);
  INIT_TYPE(ID_MA);
  INIT_TYPE(ID_TE);
  INIT_TYPE(ID_IM);
  INIT_TYPE(ID_LT);
  INIT_TYPE(ID_LA);
  INIT_TYPE(ID_CA);
  // INIT_TYPE(ID_IP);
  INIT_TYPE(ID_KE);
  INIT_TYPE(ID_WO);
  INIT_TYPE(ID_SCR);
  INIT_TYPE(ID_VF);
  INIT_TYPE(ID_TXT);
  INIT_TYPE(ID_SPK);
  INIT_TYPE(ID_SO);
  INIT_TYPE(ID_GR);
  INIT_TYPE(ID_AR);
  INIT_TYPE(ID_AC);
  INIT_TYPE(ID_NT);
  INIT_TYPE(ID_BR);
  // INIT_TYPE(ID_PA);
  // INIT_TYPE(ID_GD);
  // INIT_TYPE(ID_WM);
  // INIT_TYPE(ID_MC);
  // INIT_TYPE(ID_MSK);
  // INIT_TYPE(ID_LS);
  // INIT_TYPE(ID_PAL);
  // INIT_TYPE(ID_PC);
  // INIT_TYPE(ID_CF);
  // INIT_TYPE(ID_WS);
  INIT_TYPE(ID_LP);

#undef INIT_TYPE
}

void BKE_idtype_init(void)
{
  /* Initialize data-block types. */
  id_type_init();
}

const IDTypeInfo *BKE_idtype_get_info_from_idcode(const short id_code)
{
  int id_index = BKE_idcode_to_index(id_code);

  if (id_index >= 0 && id_index < INDEX_ID_MAX && id_types[id_index] != NULL &&
      id_types[id_index]->name[0] != '\0') {
    return id_types[id_index];
  }
  else {
    return NULL;
  }
}

const IDTypeInfo *BKE_idtype_get_info_from_id(const ID *id)
{
  return BKE_idtype_get_info_from_idcode(GS(id->name));
}
