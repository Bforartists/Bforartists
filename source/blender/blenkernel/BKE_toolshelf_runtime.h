/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup bke
 * \brief Runtime data management for toolshelf category tabs.
 */

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Initialize the toolshelf runtime data system.
 *
 * Sets up the global hash table for storing toolshelf runtime data.
 * Must be called during Blender startup.
 */
void BKE_toolshelf_runtime_init(void);

/**
 * Free all toolshelf runtime data.
 *
 * Cleans up the global hash table and all stored runtime data.
 * Called during Blender shutdown.
 */
void BKE_toolshelf_runtime_exit(void);

/**
 * Get the stored category tabs offset for a region.
 *
 * Retrieves the preferred toolbar width that was stored when category tabs
 * were last hidden. Used to restore the previous width when tabs are shown again.
 *
 * \param region: The region to get the offset for
 * \return: The stored offset value, or 0.0f if none is stored
 */
float BKE_toolshelf_category_tabs_offset_get(const ARegion *region);

/**
 * Set the category tabs offset for a region.
 *
 * Stores the current toolbar width as the preferred width for when category tabs
 * are shown. This value is restored when tabs are toggled back on.
 *
 * \param region: The region to store the offset for
 * \param offset: The offset value to store
 */
void BKE_toolshelf_category_tabs_offset_set(struct ARegion *region, float offset);

/**
 * Free runtime data for a specific region.
 *
 * Removes and frees any toolshelf runtime data associated with the given region.
 * Called during region cleanup to prevent memory leaks.
 *
 * \param region: The region whose runtime data should be freed
 */
void BKE_toolshelf_region_free(struct ARegion *region);

#ifdef __cplusplus
}
#endif
