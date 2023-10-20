/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 *
 * User defined asset library API.
 */

#include <cstring>

#include "DNA_asset_types.h"

#include "MEM_guardedalloc.h"

#include "BLI_fileops.h"
#include "BLI_listbase.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"
#include "BLI_string_utils.hh"

#include "BKE_appdir.h"
#include "BKE_preferences.h"

#include "BLT_translation.h"

#include "DNA_defaults.h"
#include "DNA_userdef_types.h"

#define U BLI_STATIC_ASSERT(false, "Global 'U' not allowed, only use arguments passed in!")

/* -------------------------------------------------------------------- */
/** \name Asset Libraries
 * \{ */

bUserAssetLibrary *BKE_preferences_asset_library_add(UserDef *userdef,
                                                     const char *name,
                                                     const char *dirpath)
{
  bUserAssetLibrary *library = DNA_struct_default_alloc(bUserAssetLibrary);

  BLI_addtail(&userdef->asset_libraries, library);

  if (name) {
    BKE_preferences_asset_library_name_set(userdef, library, name);
  }
  if (dirpath) {
    STRNCPY(library->dirpath, dirpath);
  }

  return library;
}

void BKE_preferences_asset_library_remove(UserDef *userdef, bUserAssetLibrary *library)
{
  BLI_freelinkN(&userdef->asset_libraries, library);
}

void BKE_preferences_asset_library_name_set(UserDef *userdef,
                                            bUserAssetLibrary *library,
                                            const char *name)
{
  STRNCPY_UTF8(library->name, name);
  BLI_uniquename(&userdef->asset_libraries,
                 library,
                 name,
                 '.',
                 offsetof(bUserAssetLibrary, name),
                 sizeof(library->name));
}

void BKE_preferences_asset_library_path_set(bUserAssetLibrary *library, const char *path)
{
  STRNCPY(library->dirpath, path);
  if (BLI_is_file(library->dirpath)) {
    BLI_path_parent_dir(library->dirpath);
  }
}

bUserAssetLibrary *BKE_preferences_asset_library_find_index(const UserDef *userdef, int index)
{
  return static_cast<bUserAssetLibrary *>(BLI_findlink(&userdef->asset_libraries, index));
}

bUserAssetLibrary *BKE_preferences_asset_library_find_by_name(const UserDef *userdef,
                                                              const char *name)
{
  return static_cast<bUserAssetLibrary *>(
      BLI_findstring(&userdef->asset_libraries, name, offsetof(bUserAssetLibrary, name)));
}

bUserAssetLibrary *BKE_preferences_asset_library_containing_path(const UserDef *userdef,
                                                                 const char *path)
{
  LISTBASE_FOREACH (bUserAssetLibrary *, asset_lib_pref, &userdef->asset_libraries) {
    if (BLI_path_contains(asset_lib_pref->dirpath, path)) {
      return asset_lib_pref;
    }
  }
  return nullptr;
}

int BKE_preferences_asset_library_get_index(const UserDef *userdef,
                                            const bUserAssetLibrary *library)
{
  return BLI_findindex(&userdef->asset_libraries, library);
}

void BKE_preferences_asset_library_default_add(UserDef *userdef)
{
  char documents_path[FILE_MAXDIR];

  /* No home or documents path found, not much we can do. */
  if (!BKE_appdir_folder_documents(documents_path) || !documents_path[0]) {
    return;
  }

  bUserAssetLibrary *library = BKE_preferences_asset_library_add(
      userdef, DATA_(BKE_PREFS_ASSET_LIBRARY_DEFAULT_NAME), nullptr);

  /* Add new "Default" library under '[doc_path]/Blender/Assets'. */
  BLI_path_join(
      library->dirpath, sizeof(library->dirpath), documents_path, N_("Blender"), N_("Assets"));
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Extension Repositories
 * \{ */

/**
 * A string copy that ensures: `[A-Za-z]+[A-Za-z0-9_]*`.
 */
static size_t strncpy_py_module(char *dst, const char *src, const size_t dst_maxncpy)
{
  const size_t dst_len_max = dst_maxncpy - 1;
  dst[0] = '\0';
  size_t i_src = 0, i_dst = 0;
  while (src[i_src] && (i_dst < dst_len_max)) {
    const char c = src[i_src++];
    const bool is_alpha = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
    /* The first character must be `[a-zA-Z]`. */
    if (i_dst == 0 && !is_alpha) {
      continue;
    }
    const bool is_num = (is_alpha == false) && ((c >= '0' && c <= '9') || c == '_');
    if (!(is_alpha || is_num)) {
      continue;
    }
    dst[i_dst++] = c;
  }
  dst[i_dst] = '\0';
  return i_dst;
}

bUserExtensionRepo *BKE_preferences_extension_repo_add(UserDef *userdef,
                                                       const char *name,
                                                       const char *module,
                                                       const char *dirpath)
{
  bUserExtensionRepo *repo = DNA_struct_default_alloc(bUserExtensionRepo);
  BLI_addtail(&userdef->extension_repos, repo);

  /* Set the unique ID-name. */
  BKE_preferences_extension_repo_name_set(userdef, repo, name);

  /* Set the unique module-name. */
  BKE_preferences_extension_repo_module_set(userdef, repo, module);

  /* Set the directory. */
  STRNCPY(repo->dirpath, dirpath);
  BLI_path_normalize(repo->dirpath);
  BLI_path_slash_rstrip(repo->dirpath);

  /* While not a strict rule, ignored paths that already exist, *
   * pointing to the same path is going to logical problems with package-management. */
  LISTBASE_FOREACH (const bUserExtensionRepo *, repo_iter, &userdef->extension_repos) {
    if (repo == repo_iter) {
      continue;
    }
    if (BLI_path_cmp(repo->dirpath, repo_iter->dirpath) == 0) {
      repo->dirpath[0] = '\0';
      break;
    }
  }

  return repo;
}

void BKE_preferences_extension_repo_remove(UserDef *userdef, bUserExtensionRepo *repo)
{
  BLI_freelinkN(&userdef->extension_repos, repo);
}

void BKE_preferences_extension_repo_name_set(UserDef *userdef,
                                             bUserExtensionRepo *repo,
                                             const char *name)
{
  if (*name == '\0') {
    name = "User Repository";
  }
  STRNCPY_UTF8(repo->name, name);

  BLI_uniquename(&userdef->extension_repos,
                 repo,
                 name,
                 '.',
                 offsetof(bUserExtensionRepo, name),
                 sizeof(repo->name));
}

void BKE_preferences_extension_repo_module_set(UserDef *userdef,
                                               bUserExtensionRepo *repo,
                                               const char *module)
{
  if (strncpy_py_module(repo->module, module, sizeof(repo->module)) == 0) {
    STRNCPY(repo->module, "repository");
  }

  BLI_uniquename(&userdef->extension_repos,
                 repo,
                 module,
                 '_',
                 offsetof(bUserExtensionRepo, module),
                 sizeof(repo->module));
}

void BKE_preferences_extension_repo_path_set(bUserExtensionRepo *repo, const char *path)
{
  STRNCPY(repo->dirpath, path);
}

bUserExtensionRepo *BKE_preferences_extension_repo_find_index(const UserDef *userdef, int index)
{
  return static_cast<bUserExtensionRepo *>(BLI_findlink(&userdef->extension_repos, index));
}

bUserExtensionRepo *BKE_preferences_extension_repo_find_by_module(const UserDef *userdef,
                                                                  const char *module)
{
  return static_cast<bUserExtensionRepo *>(
      BLI_findstring(&userdef->extension_repos, module, offsetof(bUserExtensionRepo, module)));
}

int BKE_preferences_extension_repo_get_index(const UserDef *userdef,
                                             const bUserExtensionRepo *repo)
{
  return BLI_findindex(&userdef->extension_repos, repo);
}

/** \} */
