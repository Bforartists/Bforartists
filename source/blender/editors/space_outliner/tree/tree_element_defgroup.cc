/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spoutliner
 */

#include "BLI_listbase.h"

#include "DNA_object_types.h"
#include "DNA_outliner_types.h"

#include "BKE_deform.h"

#include "BLT_translation.h"

#include "../outliner_intern.hh"

#include "tree_element_defgroup.hh"

namespace blender::ed::outliner {

TreeElementDeformGroupBase::TreeElementDeformGroupBase(TreeElement &legacy_te, Object &object)
    : AbstractTreeElement(legacy_te), object_(object)
{
  BLI_assert(legacy_te.store_elem->type == TSE_DEFGROUP_BASE);
  legacy_te.name = IFACE_("Vertex Groups");
}

void TreeElementDeformGroupBase::expand(SpaceOutliner & /*space_outliner*/) const
{
  const ListBase *defbase = BKE_object_defgroup_list(&object_);

  int index;
  LISTBASE_FOREACH_INDEX (bDeformGroup *, defgroup, defbase, index) {
    add_element(&legacy_te_.subtree, &object_.id, defgroup, &legacy_te_, TSE_DEFGROUP, index);
  }
}

TreeElementDeformGroup::TreeElementDeformGroup(TreeElement &legacy_te,
                                               Object & /*object*/,
                                               bDeformGroup &defgroup)
    : AbstractTreeElement(legacy_te), /* object_(object), */ defgroup_(defgroup)
{
  BLI_assert(legacy_te.store_elem->type == TSE_DEFGROUP);
  legacy_te.name = defgroup_.name;
  legacy_te.directdata = &defgroup_;
}

}  // namespace blender::ed::outliner
