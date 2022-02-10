/* SPDX-License-Identifier: GPL-2.0-or-later
 * Copyright 2017 Blender Foundation. All rights reserved. */

/** \file
 * \ingroup spoutliner
 */

#include "BLI_listbase.h"

#include "BKE_context.h"

#include "DNA_space_types.h"

#include "outliner_intern.hh"

static void outliner_context_selected_ids_recursive(const ListBase *subtree,
                                                    bContextDataResult *result)
{
  LISTBASE_FOREACH (const TreeElement *, te, subtree) {
    const TreeStoreElem *tse = TREESTORE(te);
    if ((tse->flag & TSE_SELECTED) && (ELEM(tse->type, TSE_SOME_ID, TSE_LAYER_COLLECTION))) {
      CTX_data_id_list_add(result, tse->id);
    }
    outliner_context_selected_ids_recursive(&te->subtree, result);
  }
}

static void outliner_context_selected_ids(const SpaceOutliner *space_outliner,
                                          bContextDataResult *result)
{
  outliner_context_selected_ids_recursive(&space_outliner->tree, result);
  CTX_data_type_set(result, CTX_DATA_TYPE_COLLECTION);
}

static const char *outliner_context_dir[] = {"selected_ids", nullptr};

int /*eContextResult*/ outliner_context(const bContext *C,
                                        const char *member,
                                        bContextDataResult *result)
{
  SpaceOutliner *space_outliner = CTX_wm_space_outliner(C);

  if (CTX_data_dir(member)) {
    CTX_data_dir_set(result, outliner_context_dir);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "selected_ids")) {
    outliner_context_selected_ids(space_outliner, result);
    return CTX_RESULT_OK;
  }
  /* NOTE: Querying non-ID selection could also work if tree elements stored their matching RNA
   * struct type. */

  return CTX_RESULT_MEMBER_NOT_FOUND;
}
