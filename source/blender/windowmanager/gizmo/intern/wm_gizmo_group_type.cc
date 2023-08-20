/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup wm
 */

#include <cstdio>

#include "BLI_ghash.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"

#include "MEM_guardedalloc.h"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_prototypes.h"

#include "WM_api.hh"
#include "WM_types.hh"

/* only for own init/exit calls (wm_gizmogrouptype_init/wm_gizmogrouptype_free) */
#include "wm.hh"

/* own includes */
#include "wm_gizmo_intern.h"
#include "wm_gizmo_wmapi.h"

/* -------------------------------------------------------------------- */
/** \name GizmoGroup Type Append
 *
 * \note This follows conventions from #WM_operatortype_find #WM_operatortype_append & friends.
 * \{ */

static GHash *global_gizmogrouptype_hash = nullptr;

wmGizmoGroupType *WM_gizmogrouptype_find(const char *idname, bool quiet)
{
  if (idname[0]) {
    wmGizmoGroupType *gzgt;

    gzgt = static_cast<wmGizmoGroupType *>(BLI_ghash_lookup(global_gizmogrouptype_hash, idname));
    if (gzgt) {
      return gzgt;
    }

    if (!quiet) {
      printf("search for unknown gizmo group '%s'\n", idname);
    }
  }
  else {
    if (!quiet) {
      printf("search for empty gizmo group\n");
    }
  }

  return nullptr;
}

void WM_gizmogrouptype_iter(GHashIterator *ghi)
{
  BLI_ghashIterator_init(ghi, global_gizmogrouptype_hash);
}

static wmGizmoGroupType *wm_gizmogrouptype_append__begin()
{
  wmGizmoGroupType *gzgt = static_cast<wmGizmoGroupType *>(
      MEM_callocN(sizeof(wmGizmoGroupType), "gizmogrouptype"));
  gzgt->srna = RNA_def_struct_ptr(&BLENDER_RNA, "", &RNA_GizmoGroupProperties);
#if 0
  /* Set the default i18n context now, so that opfunc can redefine it if needed! */
  RNA_def_struct_translation_context(ot->srna, BLT_I18NCONTEXT_OPERATOR_DEFAULT);
  ot->translation_context = BLT_I18NCONTEXT_OPERATOR_DEFAULT;
#endif
  return gzgt;
}
static void wm_gizmogrouptype_append__end(wmGizmoGroupType *gzgt)
{
  BLI_assert(gzgt->name != nullptr);
  BLI_assert(gzgt->idname != nullptr);

  RNA_def_struct_identifier(&BLENDER_RNA, gzgt->srna, gzgt->idname);

  gzgt->type_update_flag |= WM_GIZMOMAPTYPE_KEYMAP_INIT;

  /* if not set, use default */
  if (gzgt->setup_keymap == nullptr) {
    if (gzgt->flag & WM_GIZMOGROUPTYPE_SELECT) {
      gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_select;
    }
    else {
      gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic;
    }
  }

  BLI_ghash_insert(global_gizmogrouptype_hash, (void *)gzgt->idname, gzgt);
}

wmGizmoGroupType *WM_gizmogrouptype_append(void (*wtfunc)(wmGizmoGroupType *))
{
  wmGizmoGroupType *gzgt = wm_gizmogrouptype_append__begin();
  wtfunc(gzgt);
  wm_gizmogrouptype_append__end(gzgt);
  return gzgt;
}

wmGizmoGroupType *WM_gizmogrouptype_append_ptr(void (*wtfunc)(wmGizmoGroupType *, void *),
                                               void *userdata)
{
  wmGizmoGroupType *gzgt = wm_gizmogrouptype_append__begin();
  wtfunc(gzgt, userdata);
  wm_gizmogrouptype_append__end(gzgt);
  return gzgt;
}

wmGizmoGroupTypeRef *WM_gizmogrouptype_append_and_link(wmGizmoMapType *gzmap_type,
                                                       void (*wtfunc)(wmGizmoGroupType *))
{
  wmGizmoGroupType *gzgt = WM_gizmogrouptype_append(wtfunc);

  gzgt->gzmap_params.spaceid = gzmap_type->spaceid;
  gzgt->gzmap_params.regionid = gzmap_type->regionid;

  return WM_gizmomaptype_group_link_ptr(gzmap_type, gzgt);
}

/**
 * Free but don't remove from #GHash.
 */
static void gizmogrouptype_free(wmGizmoGroupType *gzgt)
{
  /* Python gizmo group, allocates its own string. */
  if (gzgt->rna_ext.srna) {
    MEM_freeN((void *)gzgt->idname);
  }

  MEM_freeN(gzgt);
}

void WM_gizmo_group_type_free_ptr(wmGizmoGroupType *gzgt)
{
  BLI_assert(gzgt == WM_gizmogrouptype_find(gzgt->idname, false));

  BLI_ghash_remove(global_gizmogrouptype_hash, gzgt->idname, nullptr, nullptr);

  gizmogrouptype_free(gzgt);

  /* XXX, TODO: update the world! */
}

bool WM_gizmo_group_type_free(const char *idname)
{
  wmGizmoGroupType *gzgt = static_cast<wmGizmoGroupType *>(
      BLI_ghash_lookup(global_gizmogrouptype_hash, idname));

  if (gzgt == nullptr) {
    return false;
  }

  WM_gizmo_group_type_free_ptr(gzgt);

  return true;
}

static void wm_gizmogrouptype_ghash_free_cb(wmGizmoGroupType *gzgt)
{
  gizmogrouptype_free(gzgt);
}

void wm_gizmogrouptype_free()
{
  BLI_ghash_free(
      global_gizmogrouptype_hash, nullptr, (GHashValFreeFP)wm_gizmogrouptype_ghash_free_cb);
  global_gizmogrouptype_hash = nullptr;
}

void wm_gizmogrouptype_init()
{
  /* reserve size is set based on blender default setup */
  global_gizmogrouptype_hash = BLI_ghash_str_new_ex("wm_gizmogrouptype_init gh", 128);
}

/** \} */
