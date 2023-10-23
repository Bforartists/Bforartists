/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edasset
 *
 * Functions for marking and clearing assets.
 */

#include "DNA_ID.h"

#include "BKE_asset.h"
#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_idtype.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"
#include "BKE_preview_image.hh"

#include "UI_interface_icons.hh"

#include "RNA_access.hh"
#include "RNA_prototypes.h"

#include "ED_asset_list.h"
#include "ED_asset_mark_clear.h"
#include "ED_asset_type.h"

#include "WM_api.hh"
#include "WM_types.hh"

bool ED_asset_mark_id(ID *id)
{
  if (id->asset_data) {
    return false;
  }
  if (!BKE_id_can_be_asset(id)) {
    return false;
  }

  id_fake_user_set(id);

  const IDTypeInfo *id_type_info = BKE_idtype_get_info_from_id(id);
  id->asset_data = BKE_asset_metadata_create();
  if (AssetTypeInfo *type_info = id_type_info->asset_type_info) {
    id->asset_data->local_type_info = type_info;
    type_info->on_mark_asset_fn(id, id->asset_data);
  }

  /* Important for asset storage to update properly! */
  ED_assetlist_storage_tag_main_data_dirty();

  return true;
}

void ED_asset_generate_preview(const bContext *C, ID *id)
{
  PreviewImage *preview = BKE_previewimg_id_get(id);
  if (preview) {
    BKE_previewimg_clear(preview);
  }

  UI_icon_render_id(C, nullptr, id, ICON_SIZE_PREVIEW, !G.background);
}

bool ED_asset_clear_id(ID *id)
{
  if (!id->asset_data) {
    return false;
  }
  BKE_asset_metadata_free(&id->asset_data);
  id_fake_user_clear(id);

  /* Important for asset storage to update properly! */
  ED_assetlist_storage_tag_main_data_dirty();

  return true;
}

void ED_assets_pre_save(Main *bmain)
{
  ID *id;
  FOREACH_MAIN_ID_BEGIN (bmain, id) {
    if (!id->asset_data || !id->asset_data->local_type_info) {
      continue;
    }

    if (id->asset_data->local_type_info->pre_save_fn) {
      id->asset_data->local_type_info->pre_save_fn(id, id->asset_data);
    }
  }
  FOREACH_MAIN_ID_END;
}

bool ED_asset_can_mark_single_from_context(const bContext *C)
{
  /* Context needs a "id" pointer to be set for #ASSET_OT_mark()/#ASSET_OT_mark_single() and
   * #ASSET_OT_clear()/#ASSET_OT_clear_single() to use. */
  const ID *id = static_cast<ID *>(CTX_data_pointer_get_type_silent(C, "id", &RNA_ID).data);
  if (!id) {
    return false;
  }
  return ED_asset_type_is_supported(id);
}

bool ED_asset_copy_to_id(const AssetMetaData *asset_data, ID *destination)
{
  if (!BKE_id_can_be_asset(destination)) {
    return false;
  }

  if (destination->asset_data) {
    BKE_asset_metadata_free(&destination->asset_data);
  }
  destination->asset_data = BKE_asset_metadata_copy(asset_data);
  return true;
}
