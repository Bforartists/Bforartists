/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spoutliner
 */

#include "DNA_ID.h"
#include "DNA_armature_types.h"
#include "DNA_listBase.h"
#include "DNA_object_types.h"
#include "DNA_outliner_types.h"

#include "BLI_listbase.h"

#include "BKE_armature.h"

#include "../outliner_intern.hh"
#include "tree_display.hh"

#include "tree_element_id_armature.hh"

namespace blender::ed::outliner {

TreeElementIDArmature::TreeElementIDArmature(TreeElement &legacy_te, bArmature &arm)
    : TreeElementID(legacy_te, arm.id), arm_(arm)
{
}

void TreeElementIDArmature::expand(SpaceOutliner &space_outliner) const
{
  expand_animation_data(arm_.adt);

  if (arm_.edbo) {
    expand_edit_bones();
  }
  else {
    /* Do not extend Armature when we have pose-mode. */
    TreeStoreElem *tselem = TREESTORE(legacy_te_.parent);
    if (TSE_IS_REAL_ID(tselem) && GS(tselem->id->name) == ID_OB &&
        ((Object *)tselem->id)->mode & OB_MODE_POSE)
    {
      /* pass */
    }
    else {
      expand_bones(space_outliner);
    }
  }

  if (!BLI_listbase_is_empty(&arm_.collections)) {
    add_element(&legacy_te_.subtree, &arm_.id, nullptr, &legacy_te_, TSE_BONE_COLLECTION_BASE, 0);
  }
}

void TreeElementIDArmature::expand_edit_bones() const
{
  int a = 0;
  LISTBASE_FOREACH_INDEX (EditBone *, ebone, arm_.edbo, a) {
    TreeElement *ten = add_element(
        &legacy_te_.subtree, &arm_.id, ebone, &legacy_te_, TSE_EBONE, a);
    ebone->temp.p = ten;
  }
  /* make hierarchy */
  TreeElement *ten = arm_.edbo->first ?
                         static_cast<TreeElement *>(((EditBone *)arm_.edbo->first)->temp.p) :
                         nullptr;
  while (ten) {
    TreeElement *nten = ten->next, *par;
    EditBone *ebone = (EditBone *)ten->directdata;
    if (ebone->parent) {
      BLI_remlink(&legacy_te_.subtree, ten);
      par = static_cast<TreeElement *>(ebone->parent->temp.p);
      BLI_addtail(&par->subtree, ten);
      ten->parent = par;
    }
    ten = nten;
  }
}

/* special handling of hierarchical non-lib data */
static void outliner_add_bone(SpaceOutliner *space_outliner,
                              ListBase *lb,
                              ID *id,
                              Bone *curBone,
                              TreeElement *parent,
                              int *a)
{
  TreeElement *te = AbstractTreeDisplay::add_element(
      space_outliner, lb, id, curBone, parent, TSE_BONE, *a);

  (*a)++;

  LISTBASE_FOREACH (Bone *, child_bone, &curBone->childbase) {
    outliner_add_bone(space_outliner, &te->subtree, id, child_bone, te, a);
  }
}

void TreeElementIDArmature::expand_bones(SpaceOutliner &space_outliner) const
{
  int a = 0;
  LISTBASE_FOREACH (Bone *, bone, &arm_.bonebase) {
    outliner_add_bone(&space_outliner, &legacy_te_.subtree, &arm_.id, bone, &legacy_te_, &a);
  }
}

}  // namespace blender::ed::outliner
