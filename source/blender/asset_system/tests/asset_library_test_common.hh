/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: Apache-2.0 */

#pragma once

#include <string>
#include <vector>

#include "asset_library_service.hh"

#include "BKE_appdir.h"
#include "BKE_callbacks.h"

#include "BLI_fileops.h"
#include "BLI_path_util.h"

#include "CLG_log.h"

#include "testing/testing.h"

namespace blender::asset_system {
class AssetCatalogTree;
class AssetCatalogTreeItem;
class AssetCatalogPath;
}  // namespace blender::asset_system

namespace blender::asset_system::tests {

/**
 * Functionality to setup and access directories on disk within which asset library related testing
 * can be done.
 */
class AssetLibraryTestBase : public testing::Test {
 protected:
  std::string asset_library_root_;
  std::string temp_library_path_;

  static void SetUpTestSuite()
  {
    testing::Test::SetUpTestSuite();
    CLG_init();
    /* Current File library needs this. */
    BKE_callback_global_init();
  }

  static void TearDownTestSuite()
  {
    BKE_callback_global_finalize();
    CLG_exit();
    testing::Test::TearDownTestSuite();
  }

  void SetUp() override
  {
    const std::string test_files_dir = blender::tests::flags_test_asset_dir();
    if (test_files_dir.empty()) {
      FAIL();
    }

    asset_library_root_ = test_files_dir + SEP_STR + "asset_library";
    temp_library_path_ = "";
  }

  void TearDown() override
  {
    AssetLibraryService::destroy();

    if (!temp_library_path_.empty()) {
      BLI_delete(temp_library_path_.c_str(), true, true);
      temp_library_path_ = "";
    }
  }

  /* Register a temporary path, which will be removed at the end of the test.
   * The returned path ends in a slash. */
  std::string use_temp_path()
  {
    BKE_tempdir_init("");
    const std::string tempdir = BKE_tempdir_session();
    temp_library_path_ = tempdir + "test-temporary-path" + SEP_STR;
    return temp_library_path_;
  }

  std::string create_temp_path()
  {
    std::string path = use_temp_path();
    BLI_dir_create_recursive(path.c_str());
    return path;
  }
};

class AssetCatalogTreeTestFunctions {
 public:
  /**
   * Recursively iterate over all tree items using #AssetCatalogTree::foreach_item() and check if
   * the items map exactly to \a expected_paths.
   */
  static void expect_tree_items(AssetCatalogTree *tree,
                                const std::vector<AssetCatalogPath> &expected_paths);

  /**
   * Iterate over the root items of \a tree and check if the items map exactly to \a
   * expected_paths. Similar to #assert_expected_tree_items() but calls
   * #AssetCatalogTree::foreach_root_item() instead of #AssetCatalogTree::foreach_item().
   */
  static void expect_tree_root_items(AssetCatalogTree *tree,
                                     const std::vector<AssetCatalogPath> &expected_paths);

  /**
   * Iterate over the child items of \a parent_item and check if the items map exactly to \a
   * expected_paths. Similar to #assert_expected_tree_items() but calls
   * #AssetCatalogTreeItem::foreach_child() instead of #AssetCatalogTree::foreach_item().
   */
  static void expect_tree_item_child_items(AssetCatalogTreeItem *parent_item,
                                           const std::vector<AssetCatalogPath> &expected_paths);
};

}  // namespace blender::asset_system::tests
