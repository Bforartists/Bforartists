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
 * \ingroup bke
 */

#pragma once

#ifndef __cplusplus
#  error This is a C++-only header file. Use BKE_asset_library.h instead.
#endif

#include "BKE_asset_library.h"

#include "BKE_asset_catalog.hh"
#include "BKE_callbacks.h"

#include <memory>

namespace blender::bke {

struct AssetLibrary {
  std::unique_ptr<AssetCatalogService> catalog_service;

  void load(StringRefNull library_root_directory);

  void on_save_handler_register();
  void on_save_handler_unregister();

  void on_save_post(struct Main *, struct PointerRNA **pointers, const int num_pointers);

 private:
  bCallbackFuncStore on_save_callback_store_;
};

}  // namespace blender::bke
