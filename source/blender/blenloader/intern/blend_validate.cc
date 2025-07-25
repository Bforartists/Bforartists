/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup blenloader
 *
 * Utils to check/validate a Main is in sane state,
 * only checks relations between data-blocks and libraries for now.
 *
 * \note Does not *fix* anything, only reports found errors.
 */

#include "CLG_log.h"

#include "BLI_listbase.h"
#include "BLI_utildefines.h"

#include "BLI_linklist.h"

#include "DNA_collection_types.h"
#include "DNA_key_types.h"
#include "DNA_node_types.h"
#include "DNA_windowmanager_types.h"

#include "BKE_key.hh"
#include "BKE_lib_id.hh"
#include "BKE_lib_remap.hh"
#include "BKE_library.hh"
#include "BKE_main.hh"
#include "BKE_node.hh"
#include "BKE_report.hh"

#include "BLO_blend_validate.hh"
#include "BLO_readfile.hh"

#include "readfile.hh"

static CLG_LogRef LOG = {"blend.validate"};

bool BLO_main_validate_libraries(Main *bmain, ReportList *reports)
{
  blo_split_main(bmain);
  BLI_assert(bmain->split_mains);
  blender::VectorSet<Main *> &split_mains = *bmain->split_mains;
  BLI_assert(split_mains[0] == bmain);
  bool is_valid = true;

  BKE_main_lock(bmain);

  MainListsArray lbarray = BKE_main_lists_get(*bmain);
  int i = lbarray.size();
  while (i--) {
    for (ID *id = static_cast<ID *>(lbarray[i]->first); id != nullptr;
         id = static_cast<ID *>(id->next))
    {
      if (ID_IS_LINKED(id)) {
        is_valid = false;
        BKE_reportf(reports,
                    RPT_ERROR,
                    "ID %s is in local database while being linked from library %s!",
                    id->name,
                    id->lib->filepath);
      }
    }
  }

  for (Main *curmain : split_mains) {
    if (curmain == bmain) {
      continue;
    }
    Library *curlib = curmain->curlib;
    if (curlib == nullptr) {
      BKE_report(reports, RPT_ERROR, "Library database with null library data pointer!"); /* BFA */
      continue;
    }

    BKE_library_filepath_set(bmain, curlib, curlib->filepath);
    BlendFileReadReport bf_reports{};
    bf_reports.reports = reports;
    BlendHandle *bh = BLO_blendhandle_from_file(curlib->runtime->filepath_abs, &bf_reports);

    if (bh == nullptr) {
      BKE_reportf(reports,
                  RPT_ERROR,
                  "Library ID %s not found at expected path %s!",
                  curlib->id.name,
                  curlib->runtime->filepath_abs);
      continue;
    }

    lbarray = BKE_main_lists_get(*curmain);
    i = lbarray.size();
    while (i--) {
      ID *id = static_cast<ID *>(lbarray[i]->first);
      if (id == nullptr) {
        continue;
      }

      if (GS(id->name) == ID_LI) {
        is_valid = false;
        BKE_reportf(reports,
                    RPT_ERROR,
                    "Library ID %s in library %s, this should not happen!",
                    id->name,
                    curlib->filepath);
        continue;
      }

      int totnames = 0;
      LinkNode *names = BLO_blendhandle_get_datablock_names(bh, GS(id->name), false, &totnames);
      for (; id != nullptr; id = static_cast<ID *>(id->next)) {
        if (!ID_IS_LINKED(id)) {
          is_valid = false;
          BKE_reportf(reports,
                      RPT_ERROR,
                      "ID %s has null lib pointer while being in library %s!",
                      id->name,
                      curlib->filepath);
          continue;
        }
        if (id->lib != curlib) {
          is_valid = false;
          BKE_reportf(reports, RPT_ERROR, "ID %s has mismatched lib pointer!", id->name);
          continue;
        }

        LinkNode *name = names;
        for (; name; name = name->next) {
          const char *str_name = (const char *)name->link;
          if (id->name[2] == str_name[0] && STREQ(str_name, id->name + 2)) {
            break;
          }
        }

        if (name == nullptr) {
          is_valid = false;
          BKE_reportf(reports,
                      RPT_ERROR,
                      "ID %s not found in library %s anymore!",
                      id->name,
                      id->lib->filepath);
          continue;
        }
      }

      BLI_linklist_freeN(names);
    }

    BLO_blendhandle_close(bh);
  }

  blo_join_main(bmain);
  BLI_assert(!bmain->split_mains);

  BKE_main_unlock(bmain);

  return is_valid;
}

bool BLO_main_validate_shapekeys(Main *bmain, ReportList *reports)
{
  ListBase *lb;
  ID *id;
  bool is_valid = true;

  BKE_main_lock(bmain);

  FOREACH_MAIN_LISTBASE_BEGIN (bmain, lb) {
    FOREACH_MAIN_LISTBASE_ID_BEGIN (lb, id) {
      if (!BKE_key_idtype_support(GS(id->name))) {
        break;
      }
      if (!ID_IS_LINKED(id)) {
        /* We assume lib data is valid... */
        Key *shapekey = BKE_key_from_id(id);
        if (shapekey != nullptr && shapekey->from != id) {
          is_valid = false;
          BKE_reportf(reports,
                      RPT_ERROR,
                      "ID %s uses shapekey %s, but its 'from' pointer is invalid (%p), fixing...",
                      id->name,
                      shapekey->id.name,
                      shapekey->from);
          shapekey->from = id;
        }
      }
    }
    FOREACH_MAIN_LISTBASE_ID_END;
  }
  FOREACH_MAIN_LISTBASE_END;

  BKE_main_unlock(bmain);

  /* NOTE: #BKE_id_delete also locks `bmain`, so we need to do this loop outside of the lock here.
   */
  LISTBASE_FOREACH_MUTABLE (Key *, shapekey, &bmain->shapekeys) {
    if (shapekey->from != nullptr) {
      continue;
    }

    BKE_reportf(reports,
                RPT_ERROR,
                "ShapeKey %s has an invalid 'from' pointer (%p), it will be deleted",
                shapekey->id.name,
                shapekey->from);
    /* NOTE: also need to remap UI data ID pointers here, since `bmain` is not the current
     * `G_MAIN`, default UI-handling remapping callback (defined by call to
     * `BKE_library_callback_remap_editor_id_reference_set`) won't work on expected data here. */
    BKE_id_delete_ex(bmain, shapekey, ID_REMAP_FORCE_UI_POINTERS);
  }

  return is_valid;
}

void BLO_main_validate_embedded_liboverrides(Main *bmain, ReportList * /*reports*/)
{
  ID *id_iter;
  FOREACH_MAIN_ID_BEGIN (bmain, id_iter) {
    bNodeTree *node_tree = blender::bke::node_tree_from_id(id_iter);
    if (node_tree) {
      if (node_tree->id.flag & ID_FLAG_EMBEDDED_DATA_LIB_OVERRIDE) {
        if (!ID_IS_OVERRIDE_LIBRARY(id_iter)) {
          node_tree->id.flag &= ~ID_FLAG_EMBEDDED_DATA_LIB_OVERRIDE;
        }
      }
    }

    if (GS(id_iter->name) == ID_SCE) {
      Scene *scene = reinterpret_cast<Scene *>(id_iter);
      if (scene->master_collection &&
          (scene->master_collection->id.flag & ID_FLAG_EMBEDDED_DATA_LIB_OVERRIDE))
      {
        scene->master_collection->id.flag &= ~ID_FLAG_EMBEDDED_DATA_LIB_OVERRIDE;
      }
    }
  }
  FOREACH_MAIN_ID_END;
}

void BLO_main_validate_embedded_flag(Main *bmain, ReportList * /*reports*/)
{
  ID *id_iter;
  FOREACH_MAIN_ID_BEGIN (bmain, id_iter) {
    if (id_iter->flag & ID_FLAG_EMBEDDED_DATA) {
      CLOG_ERROR(
          &LOG, "ID %s is flagged as embedded, while existing in Main data-base", id_iter->name);
      id_iter->flag &= ~ID_FLAG_EMBEDDED_DATA;
    }

    bNodeTree *node_tree = blender::bke::node_tree_from_id(id_iter);
    if (node_tree) {
      if ((node_tree->id.flag & ID_FLAG_EMBEDDED_DATA) == 0) {
        CLOG_ERROR(&LOG,
                   "ID %s has an embedded nodetree which is not flagged as embedded",
                   id_iter->name);
        node_tree->id.flag |= ID_FLAG_EMBEDDED_DATA;
      }
    }

    if (GS(id_iter->name) == ID_SCE) {
      Scene *scene = reinterpret_cast<Scene *>(id_iter);
      if (scene->master_collection &&
          (scene->master_collection->id.flag & ID_FLAG_EMBEDDED_DATA) == 0)
      {
        CLOG_ERROR(&LOG,
                   "ID %s has an embedded Collection which is not flagged as embedded",
                   id_iter->name);
        scene->master_collection->id.flag |= ID_FLAG_EMBEDDED_DATA;
      }
    }
  }
  FOREACH_MAIN_ID_END;
}
