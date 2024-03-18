/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edasset
 */

#pragma once

struct ARegion;
struct ARegionType;
struct AssetShelfSettings;
struct AssetShelfType;
struct bContext;
struct bContextDataResult;
struct BlendDataReader;
struct BlendWriter;
struct Main;
struct wmWindowManager;
struct RegionPollParams;

namespace blender::ed::asset::shelf {

/* -------------------------------------------------------------------- */
/** \name Asset Shelf Regions
 *
 * Naming conventions:
 * - #regions_xxx(): Applies to both regions (#RGN_TYPE_ASSET_SHELF and
 *   #RGN_TYPE_ASSET_SHELF_HEADER).
 * - #region_xxx(): Applies to the main shelf region (#RGN_TYPE_ASSET_SHELF).
 * - #header_region_xxx(): Applies to the shelf header region
 *   (#RGN_TYPE_ASSET_SHELF_HEADER).
 *
 * \{ */

bool regions_poll(const RegionPollParams *params);

/** Only needed for #RGN_TYPE_ASSET_SHELF (not #RGN_TYPE_ASSET_SHELF_HEADER). */
void *region_duplicate(void *regiondata);
void region_free(ARegion *region);
void region_init(wmWindowManager *wm, ARegion *region);
int region_snap(const ARegion *region, int size, int axis);
void region_on_user_resize(const ARegion *region);
void region_listen(const wmRegionListenerParams *params);
void region_layout(const bContext *C, ARegion *region);
void region_draw(const bContext *C, ARegion *region);
void region_blend_read_data(BlendDataReader *reader, ARegion *region);
void region_blend_write(BlendWriter *writer, ARegion *region);
int region_prefsizey(void);

void header_region_init(wmWindowManager *wm, ARegion *region);
void header_region(const bContext *C, ARegion *region);
void header_region_listen(const wmRegionListenerParams *params);
int header_region_size(void);
void header_regiontype_register(ARegionType *region_type, const int space_type);

/** \} */

/* -------------------------------------------------------------------- */

void type_unlink(const Main &bmain, const AssetShelfType &shelf_type);

int tile_width(const AssetShelfSettings &settings);
int tile_height(const AssetShelfSettings &settings);

int context(const bContext *C, const char *member, bContextDataResult *result);

}  // namespace blender::ed::asset::shelf
