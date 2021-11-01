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
 */

/** \file
 * \ingroup edasset
 *
 * Functions for marking and clearing assets.
 */

#include <memory>
#include <string>

#include "DNA_ID.h"

#include "BKE_asset.h"
#include "BKE_context.h"
#include "BKE_icons.h"
#include "BKE_idtype.h"
#include "BKE_lib_id.h"
#include "BKE_main.h"

#include "BLO_readfile.h"

#include "UI_interface_icons.h"

#include "RNA_access.h"

#include "ED_asset_list.h"
#include "ED_asset_mark_clear.h"
#include "ED_asset_type.h"

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
  id->asset_data->local_type_info = id_type_info->asset_type_info;

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

  UI_icon_render_id(C, nullptr, id, ICON_SIZE_PREVIEW, true);
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

void ED_assets_pre_save(struct Main *bmain)
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
  /* Context needs a "id" pointer to be set for #ASSET_OT_mark()/#ASSET_OT_clear() to use. */
  const ID *id = static_cast<ID *>(CTX_data_pointer_get_type_silent(C, "id", &RNA_ID).data);
  if (!id) {
    return false;
  }
  return ED_asset_type_is_supported(id);
}
