/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "testing/testing.h"

#include "AS_essentials_library.hh"

namespace blender::asset_system::tests {

/* BFA - Online Essentials are hosted on assets.bforartists.com instead of blender.org. */
TEST(EssentialsLibraryTest, is_online_essentials_url)
{
  EXPECT_FALSE(is_online_essentials_url(""));
  EXPECT_FALSE(is_online_essentials_url("https://www.blender.org/asset-library/"));

  EXPECT_TRUE(is_online_essentials_url("https://assets.bforartists.com/essentials/"));
  EXPECT_TRUE(is_online_essentials_url(
      "https://assets.bforartists.com/essentials/_asset-library-meta.json"));

  EXPECT_FALSE(is_online_essentials_url("https://assets.bforartists.com/essentials"));
  EXPECT_FALSE(is_online_essentials_url(
      "https://assets.bforartists.com/essentials_asset-library-meta.json"));

  /* BFA - Blender's own Online Essentials URL is a regular remote library in Bforartists. */
  EXPECT_FALSE(
      is_online_essentials_url("https://cdn.extensions.blender.org/asset-libraries/essentials/"));

  /* http instead of https. */
  EXPECT_FALSE(is_online_essentials_url("http://assets.bforartists.com/essentials/"));
}

}  // namespace blender::asset_system::tests
