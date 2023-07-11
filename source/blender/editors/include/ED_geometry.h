/* SPDX-FileCopyrightText: 2020 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup editors
 */

#pragma once

#include "DNA_customdata_types.h"

#include "BKE_attribute.h"
#include "BKE_screen.h"

#ifdef __cplusplus
#  include "BLI_string_ref.hh"
#endif

#ifdef __cplusplus
extern "C" {
#endif

struct Mesh;
struct ReportList;

void ED_operatortypes_geometry(void);

/**
 * Convert an attribute with the given name to a new type and domain.
 * The attribute must already exist.
 *
 * \note Does not support meshes in edit mode.
 */
bool ED_geometry_attribute_convert(struct Mesh *mesh,
                                   const char *name,
                                   eCustomDataType dst_type,
                                   eAttrDomain dst_domain,
                                   ReportList *reports);
#ifdef __cplusplus
}
#endif

#ifdef __cplusplus

namespace blender::ed::geometry {

MenuType node_group_operator_assets_menu();

void ui_template_node_operator_asset_menu_items(uiLayout &layout,
                                                bContext &C,
                                                StringRef catalog_path);
void ui_template_node_operator_asset_root_items(uiLayout &layout, bContext &C);

}  // namespace blender::ed::geometry

#endif
