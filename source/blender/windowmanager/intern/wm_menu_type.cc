/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup wm
 *
 * Menu Registry.
 */

#include <cstdio>

#include "BLI_sys_types.h"

#include "DNA_windowmanager_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_vector_set.hh"

#include "BKE_context.hh"
#include "BKE_screen.hh"
#include "BKE_workspace.hh"

#include "WM_api.hh"
#include "WM_types.hh"

using blender::StringRef;

struct MenuTypePointerHash {
  uint64_t operator()(const MenuType *value) const
  {
    return get_default_hash(StringRef(value->idname));
  }
  uint64_t operator()(const StringRef name) const
  {
    return get_default_hash(name);
  }
};

struct MenuTypePointerNameEqual {
  bool operator()(const MenuType *a, const MenuType *b) const
  {
    return STREQ(a->idname, b->idname);
  }
  bool operator()(const StringRef idname, const MenuType *a) const
  {
    return a->idname == idname;
  }
};

static auto &get_menu_type_map()
{
  static blender::VectorSet<MenuType *,
                            blender::DefaultProbingStrategy,
                            MenuTypePointerHash,
                            MenuTypePointerNameEqual>
      map;
  return map;
}

MenuType *WM_menutype_find(const char *idname, bool quiet)
{
  if (idname[0]) {
    if (MenuType *const *mt = get_menu_type_map().lookup_key_ptr_as(StringRef(idname))) {
      return *mt;
    }
  }

  if (!quiet) {
    printf("search for unknown menutype %s\n", idname);
  }

  return nullptr;
}

blender::Span<MenuType *> WM_menutypes_registered_get()
{
  return get_menu_type_map();
}

bool WM_menutype_add(MenuType *mt)
{
  BLI_assert((mt->description == nullptr) || (mt->description[0]));
  get_menu_type_map().add(mt);
  return true;
}

void WM_menutype_freelink(MenuType *mt)
{
  bool ok = get_menu_type_map().remove(mt);
  MEM_freeN(mt);

  BLI_assert(ok);
  UNUSED_VARS_NDEBUG(ok);
}

void WM_menutype_init()
{
  /* Reserve size is set based on blender default setup. */
  get_menu_type_map().reserve(512);
}

void WM_menutype_free()
{
  for (MenuType *mt : get_menu_type_map()) {
    if (mt->rna_ext.free) {
      mt->rna_ext.free(mt->rna_ext.data);
    }
    MEM_freeN(mt);
  }
  get_menu_type_map().clear();
}

bool WM_menutype_poll(bContext *C, MenuType *mt)
{
  /* If we're tagged, only use compatible. */
  if (mt->owner_id[0] != '\0') {
    const WorkSpace *workspace = CTX_wm_workspace(C);
    if (BKE_workspace_owner_id_check(workspace, mt->owner_id) == false) {
      return false;
    }
  }

  if (mt->poll != nullptr) {
    return mt->poll(C, mt);
  }
  return true;
}

void WM_menutype_idname_visit_for_search(
    const bContext * /*C*/,
    PointerRNA * /*ptr*/,
    PropertyRNA * /*prop*/,
    const char * /*edit_text*/,
    blender::FunctionRef<void(StringPropertySearchVisitParams)> visit_fn)
{
  for (MenuType *mt : get_menu_type_map()) {
    StringPropertySearchVisitParams visit_params{};
    visit_params.text = mt->idname;
    visit_params.info = mt->label;
    visit_fn(visit_params);
  }
}
