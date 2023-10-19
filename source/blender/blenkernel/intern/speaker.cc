/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#include "DNA_defaults.h"
#include "DNA_object_types.h"
#include "DNA_sound_types.h"
#include "DNA_speaker_types.h"

#include "BLI_utildefines.h"

#include "BLT_translation.h"

#include "BKE_anim_data.h"
#include "BKE_idtype.h"
#include "BKE_lib_id.h"
#include "BKE_lib_query.h"
#include "BKE_main.h"
#include "BKE_speaker.h"

#include "BLO_read_write.hh"

#include <cstring>

static void speaker_init_data(ID *id)
{
  Speaker *speaker = (Speaker *)id;

  BLI_assert(MEMCMP_STRUCT_AFTER_IS_ZERO(speaker, id));

  MEMCPY_STRUCT_AFTER(speaker, DNA_struct_default_get(Speaker), id);
}

static void speaker_foreach_id(ID *id, LibraryForeachIDData *data)
{
  Speaker *speaker = (Speaker *)id;

  BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, speaker->sound, IDWALK_CB_USER);
}

static void speaker_blend_write(BlendWriter *writer, ID *id, const void *id_address)
{
  Speaker *spk = (Speaker *)id;

  /* write LibData */
  BLO_write_id_struct(writer, Speaker, id_address, &spk->id);
  BKE_id_blend_write(writer, &spk->id);
}

IDTypeInfo IDType_ID_SPK = {
    /*id_code*/ ID_SPK,
    /*id_filter*/ FILTER_ID_SPK,
    /*main_listbase_index*/ INDEX_ID_SPK,
    /*struct_size*/ sizeof(Speaker),
    /*name*/ "Speaker",
    /*name_plural*/ N_("speakers"),
    /*translation_context*/ BLT_I18NCONTEXT_ID_SPEAKER,
    /*flags*/ IDTYPE_FLAGS_APPEND_IS_REUSABLE,
    /*asset_type_info*/ nullptr,

    /*init_data*/ speaker_init_data,
    /*copy_data*/ nullptr,
    /*free_data*/ nullptr,
    /*make_local*/ nullptr,
    /*foreach_id*/ speaker_foreach_id,
    /*foreach_cache*/ nullptr,
    /*foreach_path*/ nullptr,
    /*owner_pointer_get*/ nullptr,

    /*blend_write*/ speaker_blend_write,
    /*blend_read_data*/ nullptr,
    /*blend_read_after_liblink*/ nullptr,

    /*blend_read_undo_preserve*/ nullptr,

    /*lib_override_apply_post*/ nullptr,
};

void *BKE_speaker_add(Main *bmain, const char *name)
{
  Speaker *spk;

  spk = static_cast<Speaker *>(BKE_id_new(bmain, ID_SPK, name));

  return spk;
}
