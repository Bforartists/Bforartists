/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup asset_system
 */

#pragma once

#include "BLI_string_ref.hh"

#include "on_disk_library.hh"
#include "remote_library.hh"

namespace blender::asset_system {

class EssentialsAssetLibrary : public OnDiskAssetLibrary {
 public:
  EssentialsAssetLibrary();

  void force_remote_listing_download() const override;
  std::optional<AssetLibraryReference> library_reference() const override;
  std::optional<eAssetImportMethod> import_method() const override;

  void refresh_catalogs() override;
};

class OnlineEssentialsLibrary : public RemoteAssetLibrary {
 public:
  OnlineEssentialsLibrary();

  /* Trailing slash matters! */
  /* BFA - Bforartists hosts its own Online Essentials, so it can ship its own and extra assets
   * independently of blender.org. It starts as a mirror of Blender's Online Essentials.
   * Blender's URL was: "https://cdn.extensions.blender.org/asset-libraries/essentials/". */
  static constexpr StringRefNull URL = "https://assets.bforartists.com/essentials/";

  std::optional<AssetLibraryReference> library_reference() const override;
};

}  // namespace blender::asset_system
