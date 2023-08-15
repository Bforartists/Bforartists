/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup asset_system
 */

#pragma once

#include <memory>

#include "AS_asset_catalog.hh"

#include "DNA_asset_types.h"

#include "BLI_set.hh"
#include "BLI_string_ref.hh"
#include "BLI_vector.hh"

#include "BKE_callbacks.h"

struct AssetLibrary;
struct IDRemapper;
struct Main;

namespace blender::asset_system {

class AssetIdentifier;
class AssetRepresentation;
class AssetStorage;

/**
 * AssetLibrary provides access to an asset library's data.
 *
 * The asset library contains catalogs and storage for asset representations. It could be extended
 * to also include asset indexes and more.
 */
class AssetLibrary {
  eAssetLibraryType library_type_;
  /**
   * The name this asset library will be displayed in the UI as. Will also be used as a weak way
   * to identify an asset library (e.g. by #AssetWeakReference).
   */
  std::string name_;
  /** If this is an asset library on disk, the top-level directory path. Normalized using
   * #normalize_directory_path(). Shared pointer so assets can safely point to it, and don't have
   * to hold a copy (which is the size of `std::string` + the allocated buffer, if no short string
   * optimization is used). With thousands of assets this might make a reasonable difference. */
  std::shared_ptr<std::string> root_path_;

  /**
   * Storage for assets (better said their representations) that are considered to be part of this
   * library. Assets are not automatically loaded into this when loading an asset library. Assets
   * have to be loaded externally and added to this storage via #add_external_asset() or
   * #add_local_id_asset(). So this really is arbitrary storage as far as #AssetLibrary is
   * concerned (allowing the API user to manage partial library storage and partial loading, so
   * only relevant parts of a library are kept in memory).
   *
   * For now, multiple parts of Blender just keep adding their own assets to this storage. E.g.
   * multiple asset browsers might load multiple representations for the same asset into this.
   * Currently there is just no way to properly identify assets, or keep track of which assets are
   * already in memory and which not. Neither do we keep track of how many parts of Blender are
   * using an asset or an asset library, which is needed to know when assets can be freed.
   */
  std::unique_ptr<AssetStorage> asset_storage_;

  std::function<void(AssetLibrary &self)> on_refresh_;

  std::optional<eAssetImportMethod> import_method_;
  /** Assets owned by this library may be imported with a different method than set in
   * #import_method_ above, it's just a default. */
  bool may_override_import_method_ = false;

  bool use_relative_path_ = true;

  bCallbackFuncStore on_save_callback_store_{};

 public:
  /* Controlled by #ED_asset_catalogs_set_save_catalogs_when_file_is_saved,
   * for managing the "Save Catalog Changes" in the quit-confirmation dialog box. */
  static bool save_catalogs_when_file_is_saved;

  std::unique_ptr<AssetCatalogService> catalog_service;

  friend class AssetLibraryService;
  friend class AssetRepresentation;

 public:
  /**
   * \param name: The name this asset library will be displayed in the UI as. Will also be used as
   *              a weak way to identify an asset library (e.g. by #AssetWeakReference). Make sure
   *              this is set for any custom (not builtin) asset library. That is,
   *              #ASSET_LIBRARY_CUSTOM ones.
   * \param root_path: If this is an asset library on disk, the top-level directory path.
   */
  AssetLibrary(eAssetLibraryType library_type, StringRef name = "", StringRef root_path = "");
  ~AssetLibrary();

  /**
   * Execute \a fn for every asset library that is loaded. The asset library is passed to the
   * \a fn call.
   *
   * \param skip_all_library: When true, the \a fn will also be executed for the "All" asset
   *                          library. This is just a combination of the other ones, so usually
   *                          iterating over it is redundant.
   */
  static void foreach_loaded(FunctionRef<void(AssetLibrary &)> fn, bool include_all_library);

  void load_catalogs();

  /** Load catalogs that have changed on disk. */
  void refresh();

  /**
   * Create a representation of an asset to be considered part of this library. Once the
   * representation is not needed anymore, it must be freed using #remove_asset(), or there will be
   * leaking that's only cleared when the library storage is destructed (typically on exit or
   * loading a different file).
   *
   * \param relative_asset_path: The path of the asset relative to the asset library root. With
   *                             this the asset must be uniquely identifiable within the asset
   *                             library.
   */
  AssetRepresentation &add_external_asset(StringRef relative_asset_path,
                                          StringRef name,
                                          int id_type,
                                          std::unique_ptr<AssetMetaData> metadata);
  /** See #AssetLibrary::add_external_asset(). */
  AssetRepresentation &add_local_id_asset(StringRef relative_asset_path, ID &id);
  /**
   * Remove an asset from the library that was added using #add_external_asset() or
   * #add_local_id_asset(). Can usually be expected to be constant time complexity (worst case may
   * differ).
   * \note This is save to call if \a asset is freed (dangling reference), will not perform any
   *       change then.
   * \return True on success, false if the asset couldn't be found inside the library (also the
   *         case when the reference is dangling).
   */
  bool remove_asset(AssetRepresentation &asset);

  /**
   * Remap ID pointers for local ID assets, see #BKE_lib_remap.h. When an ID pointer would be
   * mapped to null (typically when an ID gets removed), the asset is removed, because we don't
   * support such empty/null assets.
   */
  void remap_ids_and_remove_invalid(const IDRemapper &mappings);

  /**
   * Update `catalog_simple_name` by looking up the asset's catalog by its ID.
   *
   * No-op if the catalog cannot be found. This could be the kind of "the
   * catalog definition file is corrupt/lost" scenario that the simple name is
   * meant to help recover from.
   */
  void refresh_catalog_simplename(AssetMetaData *asset_data);

  void on_blend_save_handler_register();
  void on_blend_save_handler_unregister();

  void on_blend_save_post(Main *bmain, PointerRNA **pointers, int num_pointers);

  /**
   * Create an asset identifier from the root path of this asset library and the given relative
   * asset path (relative to the asset library root directory).
   */
  AssetIdentifier asset_identifier_from_library(StringRef relative_asset_path);

  std::string resolve_asset_weak_reference_to_full_path(const AssetWeakReference &asset_reference);

  eAssetLibraryType library_type() const;
  StringRefNull name() const;
  StringRefNull root_path() const;
};

Vector<AssetLibraryReference> all_valid_asset_library_refs();

AssetLibraryReference all_library_reference();

}  // namespace blender::asset_system

/**
 * Load the data for an asset library, but not the asset representations themselves (loading these
 * is currently not done in the asset system).
 *
 * For the "All" asset library (#ASSET_LIBRARY_ALL), every other known asset library will be
 * loaded as well. So a call to #AssetLibrary::foreach_loaded() can be expected to iterate over all
 * libraries.
 *
 * \warning Catalogs are reloaded, invalidating catalog pointers. Do not store catalog pointers,
 *          store CatalogIDs instead and lookup the catalog where needed.
 */
blender::asset_system::AssetLibrary *AS_asset_library_load(
    const Main *bmain, const AssetLibraryReference &library_reference);

std::string AS_asset_library_root_path_from_library_ref(
    const AssetLibraryReference &library_reference);

/**
 * Try to find an appropriate location for an asset library root from a file or directory path.
 * Does not check if \a input_path exists.
 *
 * The design is made to find an appropriate asset library path from a .blend file path, but
 * technically works with any file or directory as \a input_path.
 * Design is:
 * * If \a input_path lies within a known asset library path (i.e. an asset library registered in
 *   the Preferences), return the asset library path.
 * * Otherwise, if \a input_path has a parent path, return the parent path (e.g. to use the
 *   directory a .blend file is in as asset library root).
 * * If \a input_path is empty or doesn't have a parent path (e.g. because a .blend wasn't saved
 *   yet), there is no suitable path. The caller has to decide how to handle this case.
 *
 * \param r_library_path: The returned asset library path with a trailing slash, or an empty string
 *                        if no suitable path is found. Assumed to be a buffer of at least
 *                        #FILE_MAXDIR bytes.
 *
 * \return True if the function could find a valid, that is, a non-empty path to return in \a
 *         r_library_path.
 */
std::string AS_asset_library_find_suitable_root_path_from_path(blender::StringRefNull input_path);

/**
 * Uses the current location on disk of the file represented by \a bmain as input to
 * #AS_asset_library_find_suitable_root_path_from_path(). Refer to it for a design
 * description.
 *
 * \return True if the function could find a valid, that is, a non-empty path to return in \a
 *         r_library_path. If \a bmain wasn't saved into a file yet, the return value will be
 *         false.
 */
std::string AS_asset_library_find_suitable_root_path_from_main(const Main *bmain);

blender::asset_system::AssetCatalogService *AS_asset_library_get_catalog_service(
    const ::AssetLibrary *library);
blender::asset_system::AssetCatalogTree *AS_asset_library_get_catalog_tree(
    const ::AssetLibrary *library);
