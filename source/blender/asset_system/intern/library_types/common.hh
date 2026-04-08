/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup asset_system
 */

#pragma once

namespace blender {
struct bUserAssetLibrary;
}

namespace blender::asset_system {

/**
 * Wrapper to get the #bUserAssetLibrary from the preferences (if still valid).
 */
class UserAssetLibraryWrapper {
  /**
   * Pointer to the user's asset library entry in the preferences.

   * \warning This may be dangling or null! Only access this using #user_asset_library(), which
   * returns `nullptr` if the library is not found (meaning it was removed/freed). It will also
   * null the pointer in that case, to avoid holding on to the dangling pointer (that's why it's
   * mutable).
   */
  mutable const bUserAssetLibrary *user_asset_library_;

 public:
  explicit UserAssetLibraryWrapper(const bUserAssetLibrary &user_asset_library);

  /**
   * Returns a pointer to the user's asset library entry in the preferences, or `nullptr` if not
   * found (meaning it was removed/freed).
   */
  const bUserAssetLibrary *user_asset_library() const;
};

}  // namespace blender::asset_system
