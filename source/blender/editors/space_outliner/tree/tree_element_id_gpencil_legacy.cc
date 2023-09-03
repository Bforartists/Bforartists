/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spoutliner
 */

#include "DNA_ID.h"
#include "DNA_gpencil_legacy_types.h"
#include "DNA_listBase.h"
#include "DNA_outliner_types.h"

#include "BLI_listbase.h"

#include "../outliner_intern.hh"

#include "tree_element_id_gpencil_legacy.hh"

namespace blender::ed::outliner {

TreeElementIDGPLegacy::TreeElementIDGPLegacy(TreeElement &legacy_te, bGPdata &gpd)
    : TreeElementID(legacy_te, gpd.id), gpd_(gpd)
{
}

void TreeElementIDGPLegacy::expand(SpaceOutliner & /*space_outliner*/) const
{
  expand_animation_data(gpd_.adt);

  expand_layers();
}

void TreeElementIDGPLegacy::expand_layers() const
{
  int index = 0;
  LISTBASE_FOREACH_BACKWARD (bGPDlayer *, gpl, &gpd_.layers) {
    add_element(&legacy_te_.subtree, &gpd_.id, gpl, &legacy_te_, TSE_GP_LAYER, index);
    index++;
  }
}

}  // namespace blender::ed::outliner
