/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BKE_toolshelf_runtime.h"

#include "BLI_ghash.h"
#include "MEM_guardedalloc.h"

#include "DNA_windowmanager_types.h"

namespace blender {

typedef struct ToolshelfRuntimeData {
  float category_tabs_offset;
} ToolshelfRuntimeData;

static GHash *g_toolshelf_runtime_data = NULL;

void BKE_toolshelf_runtime_init(void)
{
  if (!g_toolshelf_runtime_data) {
    g_toolshelf_runtime_data = BLI_ghash_ptr_new(__func__);
  }
}

void BKE_toolshelf_runtime_exit(void)
{
  if (g_toolshelf_runtime_data) {
    GHashIterator gh_iter;
    GHASH_ITER (gh_iter, g_toolshelf_runtime_data) {
      MEM_delete_void(BLI_ghashIterator_getValue(&gh_iter));
    }
    BLI_ghash_free(g_toolshelf_runtime_data, NULL, NULL);
    g_toolshelf_runtime_data = NULL;
  }
}

float BKE_toolshelf_category_tabs_offset_get(const ARegion *region)
{
  if (!g_toolshelf_runtime_data || !region) {
    return 0.0f;
  }

  ToolshelfRuntimeData *data = static_cast<ToolshelfRuntimeData *>(
      BLI_ghash_lookup(g_toolshelf_runtime_data, region));
  return data ? data->category_tabs_offset : 0.0f;
}

void BKE_toolshelf_category_tabs_offset_set(ARegion *region, float offset)
{
  if (!region) {
    return;
  }

  BKE_toolshelf_runtime_init(); /* Ensure the hash exists */

  ToolshelfRuntimeData *data = static_cast<ToolshelfRuntimeData *>(
      BLI_ghash_lookup(g_toolshelf_runtime_data, region));

  if (!data) {
    data = static_cast<ToolshelfRuntimeData *>(
        MEM_new_zeroed(sizeof(ToolshelfRuntimeData), __func__));
    BLI_ghash_insert(g_toolshelf_runtime_data, region, data);
  }

  data->category_tabs_offset = offset;
}

/**
 * Free runtime data for a specific region.
 *
 * This function removes and frees any toolshelf runtime data (such as stored
 * category tabs offsets) associated with the given region. Called during
 * region cleanup to prevent memory leaks.
 *
 * \param region: The region whose runtime data should be freed
 */
void BKE_toolshelf_region_free(ARegion *region)
{
  if (g_toolshelf_runtime_data && region) {
    ToolshelfRuntimeData *data = static_cast<ToolshelfRuntimeData *>(
        BLI_ghash_popkey(g_toolshelf_runtime_data, region, nullptr));
    if (data) {
      MEM_delete(data);
    }
  }
}
}  // namespace blender
