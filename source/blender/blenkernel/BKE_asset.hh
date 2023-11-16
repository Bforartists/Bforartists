/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#pragma once

#include "BLI_compiler_attrs.h"
#include "BLI_utildefines.h"

#include "DNA_asset_types.h"

struct AssetLibraryReference;
struct AssetMetaData;
struct AssetTag;
struct BlendDataReader;
struct BlendWriter;
struct ID;
struct IDProperty;
struct PreviewImage;

using PreSaveFn = void (*)(void *asset_ptr, AssetMetaData *asset_data);
using OnMarkAssetFn = void (*)(void *asset_ptr, AssetMetaData *asset_data);

struct AssetTypeInfo {
  /**
   * For local assets (assets in the current .blend file), a callback to execute before the file is
   * saved.
   */
  PreSaveFn pre_save_fn;
  OnMarkAssetFn on_mark_asset_fn;
};

AssetMetaData *BKE_asset_metadata_create(void);
void BKE_asset_metadata_free(AssetMetaData **asset_data);

/**
 * Create a copy of the #AssetMetaData so that it can be assigned to another asset.
 *
 * The caller becomes the owner of the returned pointer.
 */
AssetMetaData *BKE_asset_metadata_copy(const AssetMetaData *source);

struct AssetTagEnsureResult {
  AssetTag *tag;
  /* Set to false if a tag of this name was already present. */
  bool is_new;
};

AssetTag *BKE_asset_metadata_tag_add(AssetMetaData *asset_data, const char *name)
    ATTR_NONNULL(1, 2);
/**
 * Make sure there is a tag with name \a name, create one if needed.
 */
AssetTagEnsureResult BKE_asset_metadata_tag_ensure(AssetMetaData *asset_data, const char *name);
void BKE_asset_metadata_tag_remove(AssetMetaData *asset_data, AssetTag *tag);

/** Clean up the catalog ID (white-spaces removed, length reduced, etc.) and assign it. */
void BKE_asset_metadata_catalog_id_clear(AssetMetaData *asset_data);
void BKE_asset_metadata_catalog_id_set(AssetMetaData *asset_data,
                                       bUUID catalog_id,
                                       const char *catalog_simple_name);

void BKE_asset_library_reference_init_default(AssetLibraryReference *library_ref);

void BKE_asset_metadata_idprop_ensure(AssetMetaData *asset_data, IDProperty *prop);
IDProperty *BKE_asset_metadata_idprop_find(const AssetMetaData *asset_data,
                                           const char *name) ATTR_WARN_UNUSED_RESULT;

PreviewImage *BKE_asset_metadata_preview_get_from_id(const AssetMetaData *asset_data,
                                                     const ID *owner_id);

void BKE_asset_metadata_write(BlendWriter *writer, AssetMetaData *asset_data);
void BKE_asset_metadata_read(BlendDataReader *reader, AssetMetaData *asset_data);

/** Frees the weak reference and its data, and nulls the given pointer. */
void BKE_asset_weak_reference_free(AssetWeakReference **weak_ref);
AssetWeakReference *BKE_asset_weak_reference_copy(AssetWeakReference *weak_ref);
void BKE_asset_weak_reference_write(BlendWriter *writer, const AssetWeakReference *weak_ref);
void BKE_asset_weak_reference_read(BlendDataReader *reader, AssetWeakReference *weak_ref);
