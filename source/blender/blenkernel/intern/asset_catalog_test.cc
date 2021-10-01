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
 * The Original Code is Copyright (C) 2020 Blender Foundation
 * All rights reserved.
 */

#include "BKE_appdir.h"
#include "BKE_asset_catalog.hh"
#include "BKE_preferences.h"

#include "BLI_fileops.h"
#include "BLI_path_util.h"

#include "DNA_userdef_types.h"

#include "testing/testing.h"

namespace blender::bke::tests {

/* UUIDs from lib/tests/asset_library/blender_assets.cats.txt */
const bUUID UUID_ID_WITHOUT_PATH("e34dd2c5-5d2e-4668-9794-1db5de2a4f71");
const bUUID UUID_POSES_ELLIE("df60e1f6-2259-475b-93d9-69a1b4a8db78");
const bUUID UUID_POSES_ELLIE_WHITESPACE("b06132f6-5687-4751-a6dd-392740eb3c46");
const bUUID UUID_POSES_ELLIE_TRAILING_SLASH("3376b94b-a28d-4d05-86c1-bf30b937130d");
const bUUID UUID_POSES_RUZENA("79a4f887-ab60-4bd4-94da-d572e27d6aed");
const bUUID UUID_POSES_RUZENA_HAND("81811c31-1a88-4bd7-bb34-c6fc2607a12e");
const bUUID UUID_POSES_RUZENA_FACE("82162c1f-06cc-4d91-a9bf-4f72c104e348");
const bUUID UUID_WITHOUT_SIMPLENAME("d7916a31-6ca9-4909-955f-182ca2b81fa3");

/* UUIDs from lib/tests/asset_library/modified_assets.cats.txt */
const bUUID UUID_AGENT_47("c5744ba5-43f5-4f73-8e52-010ad4a61b34");

/* Subclass that adds accessors such that protected fields can be used in tests. */
class TestableAssetCatalogService : public AssetCatalogService {
 public:
  TestableAssetCatalogService() = default;

  explicit TestableAssetCatalogService(const CatalogFilePath &asset_library_root)
      : AssetCatalogService(asset_library_root)
  {
  }

  AssetCatalogDefinitionFile *get_catalog_definition_file()
  {
    return catalog_definition_file_.get();
  }

  void create_missing_catalogs()
  {
    AssetCatalogService::create_missing_catalogs();
  }

  int64_t count_catalogs_with_path(const CatalogFilePath &path)
  {
    int64_t count = 0;
    for (auto &catalog_uptr : catalogs_.values()) {
      if (catalog_uptr->path == path) {
        count++;
      }
    }
    return count;
  }
};

class AssetCatalogTest : public testing::Test {
 protected:
  CatalogFilePath asset_library_root_;
  CatalogFilePath temp_library_path_;

  void SetUp() override
  {
    const std::string test_files_dir = blender::tests::flags_test_asset_dir();
    if (test_files_dir.empty()) {
      FAIL();
    }

    asset_library_root_ = test_files_dir + "/" + "asset_library";
    temp_library_path_ = "";
  }

  /* Register a temporary path, which will be removed at the end of the test.
   * The returned path ends in a slash. */
  CatalogFilePath use_temp_path()
  {
    BKE_tempdir_init("");
    const CatalogFilePath tempdir = BKE_tempdir_session();
    temp_library_path_ = tempdir + "test-temporary-path/";
    return temp_library_path_;
  }

  CatalogFilePath create_temp_path()
  {
    CatalogFilePath path = use_temp_path();
    BLI_dir_create_recursive(path.c_str());
    return path;
  }

  struct CatalogPathInfo {
    StringRef name;
    int parent_count;
  };

  void assert_expected_item(const CatalogPathInfo &expected_path,
                            const AssetCatalogTreeItem &actual_item)
  {
    char expected_filename[FILE_MAXFILE];
    /* Is the catalog name as expected? "character", "Ellie", ... */
    BLI_split_file_part(expected_path.name.data(), expected_filename, sizeof(expected_filename));
    EXPECT_EQ(expected_filename, actual_item.get_name());
    /* Does the computed number of parents match? */
    EXPECT_EQ(expected_path.parent_count, actual_item.count_parents());
    EXPECT_EQ(expected_path.name, actual_item.catalog_path().str());
  }

  /**
   * Recursively iterate over all tree items using #AssetCatalogTree::foreach_item() and check if
   * the items map exactly to \a expected_paths.
   */
  void assert_expected_tree_items(AssetCatalogTree *tree,
                                  const std::vector<CatalogPathInfo> &expected_paths)
  {
    int i = 0;
    tree->foreach_item([&](const AssetCatalogTreeItem &actual_item) {
      ASSERT_LT(i, expected_paths.size())
          << "More catalogs in tree than expected; did not expect " << actual_item.catalog_path();
      assert_expected_item(expected_paths[i], actual_item);
      i++;
    });
  }

  /**
   * Iterate over the root items of \a tree and check if the items map exactly to \a
   * expected_paths. Similar to #assert_expected_tree_items() but calls
   * #AssetCatalogTree::foreach_root_item() instead of #AssetCatalogTree::foreach_item().
   */
  void assert_expected_tree_root_items(AssetCatalogTree *tree,
                                       const std::vector<CatalogPathInfo> &expected_paths)
  {
    int i = 0;
    tree->foreach_root_item([&](const AssetCatalogTreeItem &actual_item) {
      ASSERT_LT(i, expected_paths.size())
          << "More catalogs in tree root than expected; did not expect "
          << actual_item.catalog_path();
      assert_expected_item(expected_paths[i], actual_item);
      i++;
    });
  }

  /**
   * Iterate over the child items of \a parent_item and check if the items map exactly to \a
   * expected_paths. Similar to #assert_expected_tree_items() but calls
   * #AssetCatalogTreeItem::foreach_child() instead of #AssetCatalogTree::foreach_item().
   */
  void assert_expected_tree_item_child_items(AssetCatalogTreeItem *parent_item,
                                             const std::vector<CatalogPathInfo> &expected_paths)
  {
    int i = 0;
    parent_item->foreach_child([&](const AssetCatalogTreeItem &actual_item) {
      ASSERT_LT(i, expected_paths.size())
          << "More catalogs in tree item than expected; did not expect "
          << actual_item.catalog_path();
      assert_expected_item(expected_paths[i], actual_item);
      i++;
    });
  }

  void TearDown() override
  {
    if (!temp_library_path_.empty()) {
      BLI_delete(temp_library_path_.c_str(), true, true);
      temp_library_path_ = "";
    }
  }
};

TEST_F(AssetCatalogTest, load_single_file)
{
  AssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" + "blender_assets.cats.txt");

  /* Test getting a non-existent catalog ID. */
  EXPECT_EQ(nullptr, service.find_catalog(BLI_uuid_generate_random()));

  /* Test getting an invalid catalog (without path definition). */
  AssetCatalog *cat_without_path = service.find_catalog(UUID_ID_WITHOUT_PATH);
  ASSERT_EQ(nullptr, cat_without_path);

  /* Test getting a regular catalog. */
  AssetCatalog *poses_ellie = service.find_catalog(UUID_POSES_ELLIE);
  ASSERT_NE(nullptr, poses_ellie);
  EXPECT_EQ(UUID_POSES_ELLIE, poses_ellie->catalog_id);
  EXPECT_EQ("character/Ellie/poselib", poses_ellie->path.str());
  EXPECT_EQ("POSES_ELLIE", poses_ellie->simple_name);

  /* Test white-space stripping and support in the path. */
  AssetCatalog *poses_whitespace = service.find_catalog(UUID_POSES_ELLIE_WHITESPACE);
  ASSERT_NE(nullptr, poses_whitespace);
  EXPECT_EQ(UUID_POSES_ELLIE_WHITESPACE, poses_whitespace->catalog_id);
  EXPECT_EQ("character/Ellie/poselib/white space", poses_whitespace->path.str());
  EXPECT_EQ("POSES_ELLIE WHITESPACE", poses_whitespace->simple_name);

  /* Test getting a UTF-8 catalog ID. */
  AssetCatalog *poses_ruzena = service.find_catalog(UUID_POSES_RUZENA);
  ASSERT_NE(nullptr, poses_ruzena);
  EXPECT_EQ(UUID_POSES_RUZENA, poses_ruzena->catalog_id);
  EXPECT_EQ("character/Ružena/poselib", poses_ruzena->path.str());
  EXPECT_EQ("POSES_RUŽENA", poses_ruzena->simple_name);
}

TEST_F(AssetCatalogTest, insert_item_into_tree)
{
  {
    AssetCatalogTree tree;
    std::unique_ptr<AssetCatalog> catalog_empty_path = AssetCatalog::from_path("");
    tree.insert_item(*catalog_empty_path);

    assert_expected_tree_items(&tree, {});
  }

  {
    AssetCatalogTree tree;

    std::unique_ptr<AssetCatalog> catalog = AssetCatalog::from_path("item");
    tree.insert_item(*catalog);
    assert_expected_tree_items(&tree, {{"item", 0}});

    /* Insert child after parent already exists. */
    std::unique_ptr<AssetCatalog> child_catalog = AssetCatalog::from_path("item/child");
    tree.insert_item(*catalog);
    assert_expected_tree_items(&tree, {{"item", 0}, {"item/child", 1}});

    std::vector<CatalogPathInfo> expected_paths;

    /* Test inserting multi-component sub-path. */
    std::unique_ptr<AssetCatalog> grandgrandchild_catalog = AssetCatalog::from_path(
        "item/child/grandchild/grandgrandchild");
    tree.insert_item(*catalog);
    expected_paths = {{"item", 0},
                      {"item/child", 1},
                      {"item/child/grandchild", 2},
                      {"item/child/grandchild/grandgrandchild", 3}};
    assert_expected_tree_items(&tree, expected_paths);

    std::unique_ptr<AssetCatalog> root_level_catalog = AssetCatalog::from_path("root level");
    tree.insert_item(*catalog);
    expected_paths = {{"item", 0},
                      {"item/child", 1},
                      {"item/child/grandchild", 2},
                      {"item/child/grandchild/grandgrandchild", 3},
                      {"root level", 0}};
    assert_expected_tree_items(&tree, expected_paths);
  }

  {
    AssetCatalogTree tree;

    std::unique_ptr<AssetCatalog> catalog = AssetCatalog::from_path("item/child");
    tree.insert_item(*catalog);
    assert_expected_tree_items(&tree, {{"item", 0}, {"item/child", 1}});
  }

  {
    AssetCatalogTree tree;

    std::unique_ptr<AssetCatalog> catalog = AssetCatalog::from_path("white space");
    tree.insert_item(*catalog);
    assert_expected_tree_items(&tree, {{"white space", 0}});
  }

  {
    AssetCatalogTree tree;

    std::unique_ptr<AssetCatalog> catalog = AssetCatalog::from_path("/item/white space");
    tree.insert_item(*catalog);
    assert_expected_tree_items(&tree, {{"item", 0}, {"item/white space", 1}});
  }

  {
    AssetCatalogTree tree;

    std::unique_ptr<AssetCatalog> catalog_unicode_path = AssetCatalog::from_path("Ružena");
    tree.insert_item(*catalog_unicode_path);
    assert_expected_tree_items(&tree, {{"Ružena", 0}});

    catalog_unicode_path = AssetCatalog::from_path("Ružena/Ružena");
    tree.insert_item(*catalog_unicode_path);
    assert_expected_tree_items(&tree, {{"Ružena", 0}, {"Ružena/Ružena", 1}});
  }
}

TEST_F(AssetCatalogTest, load_single_file_into_tree)
{
  AssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" + "blender_assets.cats.txt");

  /* Contains not only paths from the CDF but also the missing parents (implicitly defined
   * catalogs). */
  std::vector<CatalogPathInfo> expected_paths{
      {"character", 0},
      {"character/Ellie", 1},
      {"character/Ellie/poselib", 2},
      {"character/Ellie/poselib/tailslash", 3},
      {"character/Ellie/poselib/white space", 3},
      {"character/Ružena", 1},
      {"character/Ružena/poselib", 2},
      {"character/Ružena/poselib/face", 3},
      {"character/Ružena/poselib/hand", 3},
      {"path", 0},                    /* Implicit. */
      {"path/without", 1},            /* Implicit. */
      {"path/without/simplename", 2}, /* From CDF. */
  };

  AssetCatalogTree *tree = service.get_catalog_tree();
  assert_expected_tree_items(tree, expected_paths);
}

TEST_F(AssetCatalogTest, foreach_in_tree)
{
  {
    AssetCatalogTree tree{};
    const std::vector<CatalogPathInfo> no_catalogs{};

    assert_expected_tree_items(&tree, no_catalogs);
    assert_expected_tree_root_items(&tree, no_catalogs);
    /* Need a root item to check child items. */
    std::unique_ptr<AssetCatalog> catalog = AssetCatalog::from_path("something");
    tree.insert_item(*catalog);
    tree.foreach_root_item([&no_catalogs, this](AssetCatalogTreeItem &item) {
      assert_expected_tree_item_child_items(&item, no_catalogs);
    });
  }

  AssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" + "blender_assets.cats.txt");

  std::vector<CatalogPathInfo> expected_root_items{{"character", 0}, {"path", 0}};
  AssetCatalogTree *tree = service.get_catalog_tree();
  assert_expected_tree_root_items(tree, expected_root_items);

  /* Test if the direct children of the root item are what's expected. */
  std::vector<std::vector<CatalogPathInfo>> expected_root_child_items = {
      /* Children of the "character" root item. */
      {{"character/Ellie", 1}, {"character/Ružena", 1}},
      /* Children of the "path" root item. */
      {{"path/without", 1}},
  };
  int i = 0;
  tree->foreach_root_item([&expected_root_child_items, &i, this](AssetCatalogTreeItem &item) {
    assert_expected_tree_item_child_items(&item, expected_root_child_items[i]);
    i++;
  });
}

TEST_F(AssetCatalogTest, find_catalog_by_path)
{
  TestableAssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" +
                         AssetCatalogService::DEFAULT_CATALOG_FILENAME);

  AssetCatalog *catalog;

  EXPECT_EQ(nullptr, service.find_catalog_by_path(""));
  catalog = service.find_catalog_by_path("character/Ellie/poselib/white space");
  EXPECT_NE(nullptr, catalog);
  EXPECT_EQ(UUID_POSES_ELLIE_WHITESPACE, catalog->catalog_id);
  catalog = service.find_catalog_by_path("character/Ružena/poselib");
  EXPECT_NE(nullptr, catalog);
  EXPECT_EQ(UUID_POSES_RUZENA, catalog->catalog_id);

  /* "character/Ellie/poselib" is used by two catalogs. Check if it's using the first one. */
  catalog = service.find_catalog_by_path("character/Ellie/poselib");
  EXPECT_NE(nullptr, catalog);
  EXPECT_EQ(UUID_POSES_ELLIE, catalog->catalog_id);
  EXPECT_NE(UUID_POSES_ELLIE_TRAILING_SLASH, catalog->catalog_id);
}

TEST_F(AssetCatalogTest, write_single_file)
{
  TestableAssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" +
                         AssetCatalogService::DEFAULT_CATALOG_FILENAME);

  const CatalogFilePath save_to_path = use_temp_path() +
                                       AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  AssetCatalogDefinitionFile *cdf = service.get_catalog_definition_file();
  cdf->write_to_disk(save_to_path);

  AssetCatalogService loaded_service(save_to_path);
  loaded_service.load_from_disk();

  /* Test that the expected catalogs are there. */
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_WHITESPACE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_TRAILING_SLASH));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_HAND));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_FACE));

  /* Test that the invalid catalog definition wasn't copied. */
  EXPECT_EQ(nullptr, loaded_service.find_catalog(UUID_ID_WITHOUT_PATH));

  /* TODO(@sybren): test ordering of catalogs in the file. */
}

TEST_F(AssetCatalogTest, no_writing_empty_files)
{
  const CatalogFilePath temp_lib_root = create_temp_path();
  AssetCatalogService service(temp_lib_root);
  service.write_to_disk_on_blendfile_save(temp_lib_root + "phony.blend");

  const CatalogFilePath default_cdf_path = temp_lib_root +
                                           AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  EXPECT_FALSE(BLI_exists(default_cdf_path.c_str()));
}

/* Already loaded a CDF, saving to some unrelated directory. */
TEST_F(AssetCatalogTest, on_blendfile_save__with_existing_cdf)
{
  const CatalogFilePath top_level_dir = create_temp_path(); /* Has trailing slash. */

  /* Create a copy of the CDF in SVN, so we can safely write to it. */
  const CatalogFilePath original_cdf_file = asset_library_root_ + "/blender_assets.cats.txt";
  const CatalogFilePath cdf_dirname = top_level_dir + "other_dir/";
  const CatalogFilePath cdf_filename = cdf_dirname + AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  ASSERT_TRUE(BLI_dir_create_recursive(cdf_dirname.c_str()));
  ASSERT_EQ(0, BLI_copy(original_cdf_file.c_str(), cdf_filename.c_str()))
      << "Unable to copy " << original_cdf_file << " to " << cdf_filename;

  /* Load the CDF, add a catalog, and trigger a write. This should write to the loaded CDF. */
  TestableAssetCatalogService service(cdf_filename);
  service.load_from_disk();
  const AssetCatalog *cat = service.create_catalog("some/catalog/path");

  const CatalogFilePath blendfilename = top_level_dir + "subdir/some_file.blend";
  ASSERT_TRUE(service.write_to_disk_on_blendfile_save(blendfilename));
  EXPECT_EQ(cdf_filename, service.get_catalog_definition_file()->file_path);

  /* Test that the CDF was created in the expected location. */
  const CatalogFilePath backup_filename = cdf_filename + "~";
  EXPECT_TRUE(BLI_exists(cdf_filename.c_str()));
  EXPECT_TRUE(BLI_exists(backup_filename.c_str()))
      << "Overwritten CDF should have been backed up.";

  /* Test that the on-disk CDF contains the expected catalogs. */
  AssetCatalogService loaded_service(cdf_filename);
  loaded_service.load_from_disk();
  EXPECT_NE(nullptr, loaded_service.find_catalog(cat->catalog_id))
      << "Expected to see the newly-created catalog.";
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE))
      << "Expected to see the already-existing catalog.";
}

/* Create some catalogs in memory, save to directory that doesn't contain anything else. */
TEST_F(AssetCatalogTest, on_blendfile_save__from_memory_into_empty_directory)
{
  const CatalogFilePath target_dir = create_temp_path(); /* Has trailing slash. */

  TestableAssetCatalogService service;
  const AssetCatalog *cat = service.create_catalog("some/catalog/path");

  const CatalogFilePath blendfilename = target_dir + "some_file.blend";
  ASSERT_TRUE(service.write_to_disk_on_blendfile_save(blendfilename));

  /* Test that the CDF was created in the expected location. */
  const CatalogFilePath expected_cdf_path = target_dir +
                                            AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  EXPECT_TRUE(BLI_exists(expected_cdf_path.c_str()));

  /* Test that the in-memory CDF has been created, and contains the expected catalog. */
  AssetCatalogDefinitionFile *cdf = service.get_catalog_definition_file();
  ASSERT_NE(nullptr, cdf);
  EXPECT_TRUE(cdf->contains(cat->catalog_id));

  /* Test that the on-disk CDF contains the expected catalog. */
  AssetCatalogService loaded_service(expected_cdf_path);
  loaded_service.load_from_disk();
  EXPECT_NE(nullptr, loaded_service.find_catalog(cat->catalog_id));
}

/* Create some catalogs in memory, save to directory that contains a default CDF. */
TEST_F(AssetCatalogTest, on_blendfile_save__from_memory_into_existing_cdf_and_merge)
{
  const CatalogFilePath target_dir = create_temp_path(); /* Has trailing slash. */
  const CatalogFilePath original_cdf_file = asset_library_root_ + "/blender_assets.cats.txt";
  const CatalogFilePath writable_cdf_file = target_dir +
                                            AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  ASSERT_EQ(0, BLI_copy(original_cdf_file.c_str(), writable_cdf_file.c_str()));

  /* Create the catalog service without loading the already-existing CDF. */
  TestableAssetCatalogService service;
  const AssetCatalog *cat = service.create_catalog("some/catalog/path");

  /* Mock that the blend file is written to a subdirectory of the asset library. */
  const CatalogFilePath blendfilename = target_dir + "some_file.blend";
  ASSERT_TRUE(service.write_to_disk_on_blendfile_save(blendfilename));

  /* Test that the CDF still exists in the expected location. */
  const CatalogFilePath backup_filename = writable_cdf_file + "~";
  EXPECT_TRUE(BLI_exists(writable_cdf_file.c_str()));
  EXPECT_TRUE(BLI_exists(backup_filename.c_str()))
      << "Overwritten CDF should have been backed up.";

  /* Test that the in-memory CDF has the expected file path. */
  AssetCatalogDefinitionFile *cdf = service.get_catalog_definition_file();
  ASSERT_NE(nullptr, cdf);
  EXPECT_EQ(writable_cdf_file, cdf->file_path);

  /* Test that the in-memory catalogs have been merged with the on-disk one. */
  AssetCatalogService loaded_service(writable_cdf_file);
  loaded_service.load_from_disk();
  EXPECT_NE(nullptr, loaded_service.find_catalog(cat->catalog_id));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE));
}

/* Create some catalogs in memory, save to subdirectory of a registered asset library. */
TEST_F(AssetCatalogTest, on_blendfile_save__from_memory_into_existing_asset_lib)
{
  const CatalogFilePath target_dir = create_temp_path(); /* Has trailing slash. */
  const CatalogFilePath original_cdf_file = asset_library_root_ + "/blender_assets.cats.txt";
  const CatalogFilePath registered_asset_lib = target_dir + "my_asset_library/";
  CatalogFilePath writable_cdf_file = registered_asset_lib +
                                      AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  BLI_path_slash_native(writable_cdf_file.data());

  /* Set up a temporary asset library for testing. */
  bUserAssetLibrary *asset_lib_pref = BKE_preferences_asset_library_add(
      &U, "Test", registered_asset_lib.c_str());
  ASSERT_NE(nullptr, asset_lib_pref);
  ASSERT_TRUE(BLI_dir_create_recursive(registered_asset_lib.c_str()));
  ASSERT_EQ(0, BLI_copy(original_cdf_file.c_str(), writable_cdf_file.c_str()));

  /* Create the catalog service without loading the already-existing CDF. */
  TestableAssetCatalogService service;
  const CatalogFilePath blenddirname = registered_asset_lib + "subdirectory/";
  const CatalogFilePath blendfilename = blenddirname + "some_file.blend";
  ASSERT_TRUE(BLI_dir_create_recursive(blenddirname.c_str()));
  const AssetCatalog *cat = service.create_catalog("some/catalog/path");

  /* Mock that the blend file is written to the directory already containing a CDF. */
  ASSERT_TRUE(service.write_to_disk_on_blendfile_save(blendfilename));

  /* Test that the CDF still exists in the expected location. */
  EXPECT_TRUE(BLI_exists(writable_cdf_file.c_str()));
  const CatalogFilePath backup_filename = writable_cdf_file + "~";
  EXPECT_TRUE(BLI_exists(backup_filename.c_str()))
      << "Overwritten CDF should have been backed up.";

  /* Test that the in-memory CDF has the expected file path. */
  AssetCatalogDefinitionFile *cdf = service.get_catalog_definition_file();
  BLI_path_slash_native(cdf->file_path.data());
  EXPECT_EQ(writable_cdf_file, cdf->file_path);

  /* Test that the in-memory catalogs have been merged with the on-disk one. */
  AssetCatalogService loaded_service(writable_cdf_file);
  loaded_service.load_from_disk();
  EXPECT_NE(nullptr, loaded_service.find_catalog(cat->catalog_id));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE));

  BKE_preferences_asset_library_remove(&U, asset_lib_pref);
}

TEST_F(AssetCatalogTest, create_first_catalog_from_scratch)
{
  /* Even from scratch a root directory should be known. */
  const CatalogFilePath temp_lib_root = use_temp_path();
  AssetCatalogService service;

  /* Just creating the service should NOT create the path. */
  EXPECT_FALSE(BLI_exists(temp_lib_root.c_str()));

  AssetCatalog *cat = service.create_catalog("some/catalog/path");
  ASSERT_NE(nullptr, cat);
  EXPECT_EQ(cat->path, "some/catalog/path");
  EXPECT_EQ(cat->simple_name, "some-catalog-path");

  /* Creating a new catalog should not save anything to disk yet. */
  EXPECT_FALSE(BLI_exists(temp_lib_root.c_str()));

  /* Writing to disk should create the directory + the default file. */
  service.write_to_disk_on_blendfile_save(temp_lib_root + "phony.blend");
  EXPECT_TRUE(BLI_is_dir(temp_lib_root.c_str()));

  const CatalogFilePath definition_file_path = temp_lib_root + "/" +
                                               AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  EXPECT_TRUE(BLI_is_file(definition_file_path.c_str()));

  AssetCatalogService loaded_service(temp_lib_root);
  loaded_service.load_from_disk();

  /* Test that the expected catalog is there. */
  AssetCatalog *written_cat = loaded_service.find_catalog(cat->catalog_id);
  ASSERT_NE(nullptr, written_cat);
  EXPECT_EQ(written_cat->catalog_id, cat->catalog_id);
  EXPECT_EQ(written_cat->path, cat->path.str());
}

TEST_F(AssetCatalogTest, create_catalog_after_loading_file)
{
  const CatalogFilePath temp_lib_root = create_temp_path();

  /* Copy the asset catalog definition files to a separate location, so that we can test without
   * overwriting the test file in SVN. */
  const CatalogFilePath default_catalog_path = asset_library_root_ + "/" +
                                               AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  const CatalogFilePath writable_catalog_path = temp_lib_root +
                                                AssetCatalogService::DEFAULT_CATALOG_FILENAME;
  ASSERT_EQ(0, BLI_copy(default_catalog_path.c_str(), writable_catalog_path.c_str()));
  EXPECT_TRUE(BLI_is_dir(temp_lib_root.c_str()));
  EXPECT_TRUE(BLI_is_file(writable_catalog_path.c_str()));

  TestableAssetCatalogService service(temp_lib_root);
  service.load_from_disk();
  EXPECT_EQ(writable_catalog_path, service.get_catalog_definition_file()->file_path);
  EXPECT_NE(nullptr, service.find_catalog(UUID_POSES_ELLIE)) << "expected catalogs to be loaded";

  /* This should create a new catalog but not write to disk. */
  const AssetCatalog *new_catalog = service.create_catalog("new/catalog");
  const bUUID new_catalog_id = new_catalog->catalog_id;

  /* Reload the on-disk catalog file. */
  TestableAssetCatalogService loaded_service(temp_lib_root);
  loaded_service.load_from_disk();
  EXPECT_EQ(writable_catalog_path, loaded_service.get_catalog_definition_file()->file_path);

  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE))
      << "expected pre-existing catalogs to be kept in the file";
  EXPECT_EQ(nullptr, loaded_service.find_catalog(new_catalog_id))
      << "expecting newly added catalog to not yet be saved to " << temp_lib_root;

  /* Write and reload the catalog file. */
  service.write_to_disk_on_blendfile_save(temp_lib_root + "phony.blend");
  AssetCatalogService reloaded_service(temp_lib_root);
  reloaded_service.load_from_disk();
  EXPECT_NE(nullptr, reloaded_service.find_catalog(UUID_POSES_ELLIE))
      << "expected pre-existing catalogs to be kept in the file";
  EXPECT_NE(nullptr, reloaded_service.find_catalog(new_catalog_id))
      << "expecting newly added catalog to exist in the file";
}

TEST_F(AssetCatalogTest, create_catalog_path_cleanup)
{
  AssetCatalogService service;
  AssetCatalog *cat = service.create_catalog(" /some/path  /  ");

  EXPECT_FALSE(BLI_uuid_is_nil(cat->catalog_id));
  EXPECT_EQ("some/path", cat->path.str());
  EXPECT_EQ("some-path", cat->simple_name);
}

TEST_F(AssetCatalogTest, create_catalog_simple_name)
{
  AssetCatalogService service;
  AssetCatalog *cat = service.create_catalog(
      "production/Spite Fright/Characters/Victora/Pose Library/Approved/Body Parts/Hands");

  EXPECT_FALSE(BLI_uuid_is_nil(cat->catalog_id));
  EXPECT_EQ("production/Spite Fright/Characters/Victora/Pose Library/Approved/Body Parts/Hands",
            cat->path.str());
  EXPECT_EQ("...ht-Characters-Victora-Pose Library-Approved-Body Parts-Hands", cat->simple_name);
}

TEST_F(AssetCatalogTest, delete_catalog_leaf)
{
  AssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" + "blender_assets.cats.txt");

  /* Delete a leaf catalog, i.e. one that is not a parent of another catalog.
   * This keeps this particular test easy. */
  service.delete_catalog(UUID_POSES_RUZENA_HAND);
  EXPECT_EQ(nullptr, service.find_catalog(UUID_POSES_RUZENA_HAND));

  /* Contains not only paths from the CDF but also the missing parents (implicitly defined
   * catalogs). This is why a leaf catalog was deleted. */
  std::vector<CatalogPathInfo> expected_paths{
      {"character", 0},
      {"character/Ellie", 1},
      {"character/Ellie/poselib", 2},
      {"character/Ellie/poselib/tailslash", 3},
      {"character/Ellie/poselib/white space", 3},
      {"character/Ružena", 1},
      {"character/Ružena/poselib", 2},
      {"character/Ružena/poselib/face", 3},
      // {"character/Ružena/poselib/hand", 3}, /* This is the deleted one. */
      {"path", 0},
      {"path/without", 1},
      {"path/without/simplename", 2},
  };

  AssetCatalogTree *tree = service.get_catalog_tree();
  assert_expected_tree_items(tree, expected_paths);
}

TEST_F(AssetCatalogTest, delete_catalog_write_to_disk)
{
  TestableAssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" +
                         AssetCatalogService::DEFAULT_CATALOG_FILENAME);

  service.delete_catalog(UUID_POSES_ELLIE);

  const CatalogFilePath save_to_path = use_temp_path();
  AssetCatalogDefinitionFile *cdf = service.get_catalog_definition_file();
  cdf->write_to_disk(save_to_path + "/" + AssetCatalogService::DEFAULT_CATALOG_FILENAME);

  AssetCatalogService loaded_service(save_to_path);
  loaded_service.load_from_disk();

  /* Test that the expected catalogs are there, except the deleted one. */
  EXPECT_EQ(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_WHITESPACE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_TRAILING_SLASH));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_HAND));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_FACE));
}

TEST_F(AssetCatalogTest, update_catalog_path)
{
  AssetCatalogService service(asset_library_root_);
  service.load_from_disk(asset_library_root_ + "/" +
                         AssetCatalogService::DEFAULT_CATALOG_FILENAME);

  const AssetCatalog *orig_cat = service.find_catalog(UUID_POSES_RUZENA);
  const AssetCatalogPath orig_path = orig_cat->path;

  service.update_catalog_path(UUID_POSES_RUZENA, "charlib/Ružena");

  EXPECT_EQ(nullptr, service.find_catalog_by_path(orig_path))
      << "The original (pre-rename) path should not be associated with a catalog any more.";

  const AssetCatalog *renamed_cat = service.find_catalog(UUID_POSES_RUZENA);
  ASSERT_NE(nullptr, renamed_cat);
  ASSERT_EQ(orig_cat, renamed_cat) << "Changing the path should not reallocate the catalog.";
  EXPECT_EQ(orig_cat->simple_name, renamed_cat->simple_name)
      << "Changing the path should not change the simple name.";
  EXPECT_EQ(orig_cat->catalog_id, renamed_cat->catalog_id)
      << "Changing the path should not change the catalog ID.";

  EXPECT_EQ("charlib/Ružena", renamed_cat->path.str())
      << "Changing the path should change the path. Surprise.";

  EXPECT_EQ("charlib/Ružena/hand", service.find_catalog(UUID_POSES_RUZENA_HAND)->path.str())
      << "Changing the path should update children.";
  EXPECT_EQ("charlib/Ružena/face", service.find_catalog(UUID_POSES_RUZENA_FACE)->path.str())
      << "Changing the path should update children.";
}

TEST_F(AssetCatalogTest, merge_catalog_files)
{
  const CatalogFilePath cdf_dir = create_temp_path();
  const CatalogFilePath original_cdf_file = asset_library_root_ + "/blender_assets.cats.txt";
  const CatalogFilePath modified_cdf_file = asset_library_root_ + "/modified_assets.cats.txt";
  const CatalogFilePath temp_cdf_file = cdf_dir + "blender_assets.cats.txt";
  ASSERT_EQ(0, BLI_copy(original_cdf_file.c_str(), temp_cdf_file.c_str()));

  /* Load the unmodified, original CDF. */
  TestableAssetCatalogService service(asset_library_root_);
  service.load_from_disk(cdf_dir);

  /* Copy a modified file, to mimic a situation where someone changed the
   * CDF after we loaded it. */
  ASSERT_EQ(0, BLI_copy(modified_cdf_file.c_str(), temp_cdf_file.c_str()));

  /* Overwrite the modified file. This should merge the on-disk file with our catalogs. */
  service.write_to_disk_on_blendfile_save(cdf_dir + "phony.blend");

  AssetCatalogService loaded_service(cdf_dir);
  loaded_service.load_from_disk();

  /* Test that the expected catalogs are there. */
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_WHITESPACE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_TRAILING_SLASH));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_HAND));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_FACE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_AGENT_47)); /* New in the modified file. */

  /* When there are overlaps, the in-memory (i.e. last-saved) paths should win. */
  const AssetCatalog *ruzena_face = loaded_service.find_catalog(UUID_POSES_RUZENA_FACE);
  EXPECT_EQ("character/Ružena/poselib/face", ruzena_face->path.str());
}

TEST_F(AssetCatalogTest, backups)
{
  const CatalogFilePath cdf_dir = create_temp_path();
  const CatalogFilePath original_cdf_file = asset_library_root_ + "/blender_assets.cats.txt";
  const CatalogFilePath writable_cdf_file = cdf_dir + "/blender_assets.cats.txt";
  ASSERT_EQ(0, BLI_copy(original_cdf_file.c_str(), writable_cdf_file.c_str()));

  /* Read a CDF, modify, and write it. */
  AssetCatalogService service(cdf_dir);
  service.load_from_disk();
  service.delete_catalog(UUID_POSES_ELLIE);
  service.write_to_disk_on_blendfile_save(cdf_dir + "phony.blend");

  const CatalogFilePath backup_path = writable_cdf_file + "~";
  ASSERT_TRUE(BLI_is_file(backup_path.c_str()));

  AssetCatalogService loaded_service;
  loaded_service.load_from_disk(backup_path);

  /* Test that the expected catalogs are there, including the deleted one.
   * This is the backup, after all. */
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_WHITESPACE));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_ELLIE_TRAILING_SLASH));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_HAND));
  EXPECT_NE(nullptr, loaded_service.find_catalog(UUID_POSES_RUZENA_FACE));
}

TEST_F(AssetCatalogTest, order_by_path)
{
  const bUUID cat2_uuid("22222222-b847-44d9-bdca-ff04db1c24f5");
  const bUUID cat4_uuid("11111111-b847-44d9-bdca-ff04db1c24f5"); /* Sorts earlier than above. */
  const AssetCatalog cat1(BLI_uuid_generate_random(), "simple/path/child", "");
  const AssetCatalog cat2(cat2_uuid, "simple/path", "");
  const AssetCatalog cat3(BLI_uuid_generate_random(), "complex/path/...or/is/it?", "");
  const AssetCatalog cat4(
      cat4_uuid, "simple/path", "different ID, same path");                /* should be kept */
  const AssetCatalog cat5(cat4_uuid, "simple/path", "same ID, same path"); /* disappears */

  AssetCatalogOrderedSet by_path;
  by_path.insert(&cat1);
  by_path.insert(&cat2);
  by_path.insert(&cat3);
  by_path.insert(&cat4);
  by_path.insert(&cat5);

  AssetCatalogOrderedSet::const_iterator set_iter = by_path.begin();

  EXPECT_EQ(1, by_path.count(&cat1));
  EXPECT_EQ(1, by_path.count(&cat2));
  EXPECT_EQ(1, by_path.count(&cat3));
  EXPECT_EQ(1, by_path.count(&cat4));
  ASSERT_EQ(4, by_path.size()) << "Expecting cat5 to not be stored in the set, as it duplicates "
                                  "an already-existing path + UUID";

  EXPECT_EQ(cat3.catalog_id, (*(set_iter++))->catalog_id); /* complex/path */
  EXPECT_EQ(cat4.catalog_id, (*(set_iter++))->catalog_id); /* simple/path with 111.. ID */
  EXPECT_EQ(cat2.catalog_id, (*(set_iter++))->catalog_id); /* simple/path with 222.. ID */
  EXPECT_EQ(cat1.catalog_id, (*(set_iter++))->catalog_id); /* simple/path/child */

  if (set_iter != by_path.end()) {
    const AssetCatalog *next_cat = *set_iter;
    FAIL() << "Did not expect more items in the set, had at least " << next_cat->catalog_id << ":"
           << next_cat->path;
  }
}

TEST_F(AssetCatalogTest, create_missing_catalogs)
{
  TestableAssetCatalogService new_service;
  new_service.create_catalog("path/with/missing/parents");

  EXPECT_EQ(nullptr, new_service.find_catalog_by_path("path/with/missing"))
      << "Missing parents should not be immediately created.";
  EXPECT_EQ(nullptr, new_service.find_catalog_by_path("")) << "Empty path should never be valid";

  new_service.create_missing_catalogs();

  EXPECT_NE(nullptr, new_service.find_catalog_by_path("path/with/missing"));
  EXPECT_NE(nullptr, new_service.find_catalog_by_path("path/with"));
  EXPECT_NE(nullptr, new_service.find_catalog_by_path("path"));
  EXPECT_EQ(nullptr, new_service.find_catalog_by_path(""))
      << "Empty path should never be valid, even when after missing catalogs";
}

TEST_F(AssetCatalogTest, create_missing_catalogs_after_loading)
{
  TestableAssetCatalogService loaded_service(asset_library_root_);
  loaded_service.load_from_disk();

  const AssetCatalog *cat_char = loaded_service.find_catalog_by_path("character");
  const AssetCatalog *cat_ellie = loaded_service.find_catalog_by_path("character/Ellie");
  const AssetCatalog *cat_ruzena = loaded_service.find_catalog_by_path("character/Ružena");
  ASSERT_NE(nullptr, cat_char) << "Missing parents should be created immediately after loading.";
  ASSERT_NE(nullptr, cat_ellie) << "Missing parents should be created immediately after loading.";
  ASSERT_NE(nullptr, cat_ruzena) << "Missing parents should be created immediately after loading.";

  AssetCatalogDefinitionFile *cdf = loaded_service.get_catalog_definition_file();
  ASSERT_NE(nullptr, cdf);
  EXPECT_TRUE(cdf->contains(cat_char->catalog_id)) << "Missing parents should be saved to a CDF.";
  EXPECT_TRUE(cdf->contains(cat_ellie->catalog_id)) << "Missing parents should be saved to a CDF.";
  EXPECT_TRUE(cdf->contains(cat_ruzena->catalog_id))
      << "Missing parents should be saved to a CDF.";

  /* Check that each missing parent is only created once. The CDF contains multiple paths that
   * could trigger the creation of missing parents, so this test makes sense. */
  EXPECT_EQ(1, loaded_service.count_catalogs_with_path("character"));
  EXPECT_EQ(1, loaded_service.count_catalogs_with_path("character/Ellie"));
  EXPECT_EQ(1, loaded_service.count_catalogs_with_path("character/Ružena"));
}

TEST_F(AssetCatalogTest, create_catalog_filter)
{
  AssetCatalogService service(asset_library_root_);
  service.load_from_disk();

  /* Alias for the same catalog as the main one. */
  AssetCatalog *alias_ruzena = service.create_catalog("character/Ružena/poselib");
  /* Alias for a sub-catalog. */
  AssetCatalog *alias_ruzena_hand = service.create_catalog("character/Ružena/poselib/hand");

  AssetCatalogFilter filter = service.create_catalog_filter(UUID_POSES_RUZENA);

  /* Positive test for loaded-from-disk catalogs. */
  EXPECT_TRUE(filter.contains(UUID_POSES_RUZENA))
      << "Main catalog should be included in the filter.";
  EXPECT_TRUE(filter.contains(UUID_POSES_RUZENA_HAND))
      << "Sub-catalog should be included in the filter.";
  EXPECT_TRUE(filter.contains(UUID_POSES_RUZENA_FACE))
      << "Sub-catalog should be included in the filter.";

  /* Positive test for newly-created catalogs. */
  EXPECT_TRUE(filter.contains(alias_ruzena->catalog_id))
      << "Alias of main catalog should be included in the filter.";
  EXPECT_TRUE(filter.contains(alias_ruzena_hand->catalog_id))
      << "Alias of sub-catalog should be included in the filter.";

  /* Negative test for unrelated catalogs. */
  EXPECT_FALSE(filter.contains(BLI_uuid_nil())) << "Nil catalog should not be included.";
  EXPECT_FALSE(filter.contains(UUID_ID_WITHOUT_PATH));
  EXPECT_FALSE(filter.contains(UUID_POSES_ELLIE));
  EXPECT_FALSE(filter.contains(UUID_POSES_ELLIE_WHITESPACE));
  EXPECT_FALSE(filter.contains(UUID_POSES_ELLIE_TRAILING_SLASH));
  EXPECT_FALSE(filter.contains(UUID_WITHOUT_SIMPLENAME));
}

TEST_F(AssetCatalogTest, create_catalog_filter_for_unknown_uuid)
{
  AssetCatalogService service;
  const bUUID unknown_uuid = BLI_uuid_generate_random();

  AssetCatalogFilter filter = service.create_catalog_filter(unknown_uuid);
  EXPECT_TRUE(filter.contains(unknown_uuid));

  EXPECT_FALSE(filter.contains(BLI_uuid_nil())) << "Nil catalog should not be included.";
  EXPECT_FALSE(filter.contains(UUID_POSES_ELLIE));
}

TEST_F(AssetCatalogTest, create_catalog_filter_for_unassigned_assets)
{
  AssetCatalogService service;

  AssetCatalogFilter filter = service.create_catalog_filter(BLI_uuid_nil());
  EXPECT_TRUE(filter.contains(BLI_uuid_nil()));
  EXPECT_FALSE(filter.contains(UUID_POSES_ELLIE));
}

}  // namespace blender::bke::tests
