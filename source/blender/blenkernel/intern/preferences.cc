/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 *
 * User defined asset library API.
 */

#include <cstring>

#include "MEM_guardedalloc.h"

#include "BLI_fileops.h"
#include "BLI_listbase.h"
#include "BLI_path_util.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"
#include "BLI_string_utils.hh"

#include "BKE_appdir.hh"
#include "BKE_preferences.h"

#include "BLT_translation.hh"

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
                                                       const char *custom_dirpath)
{
  bUserExtensionRepo *repo = DNA_struct_default_alloc(bUserExtensionRepo);
  BLI_addtail(&userdef->extension_repos, repo);

  /* Set the unique ID-name. */
  BKE_preferences_extension_repo_name_set(userdef, repo, name);

  /* Set the unique module-name. */
  BKE_preferences_extension_repo_module_set(userdef, repo, module);

  /* Set the directory. */
  STRNCPY(repo->custom_dirpath, custom_dirpath);
  BLI_path_normalize(repo->custom_dirpath);
  BLI_path_slash_rstrip(repo->custom_dirpath);

  /* While not a strict rule, ignored paths that already exist, *
   * pointing to the same path is going to logical problems with package-management. */
  LISTBASE_FOREACH (const bUserExtensionRepo *, repo_iter, &userdef->extension_repos) {
    if (repo == repo_iter) {
      continue;
    }
    if (BLI_path_cmp(repo->custom_dirpath, repo_iter->custom_dirpath) == 0) {
      repo->custom_dirpath[0] = '\0';
      break;
    }
  }

  return repo;
}

void BKE_preferences_extension_repo_remove(UserDef *userdef, bUserExtensionRepo *repo)
{
  BLI_freelinkN(&userdef->extension_repos, repo);
}

bUserExtensionRepo *BKE_preferences_extension_repo_add_default(UserDef *userdef)
{
  bUserExtensionRepo *repo = BKE_preferences_extension_repo_add(
      userdef, "extensions.blender.org", "blender_org", "");
  STRNCPY(repo->remote_path, "https://extensions.blender.org");
  repo->flag |= USER_EXTENSION_REPO_FLAG_USE_REMOTE_PATH;
  return repo;
}

bUserExtensionRepo *BKE_preferences_extension_repo_add_default_user(UserDef *userdef)
{
  bUserExtensionRepo *repo = BKE_preferences_extension_repo_add(
      userdef, "User Default", "user_default", "");
  return repo;
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

void BKE_preferences_extension_repo_custom_dirpath_set(bUserExtensionRepo *repo, const char *path)
{
  STRNCPY(repo->custom_dirpath, path);
}

size_t BKE_preferences_extension_repo_dirpath_get(const bUserExtensionRepo *repo,
                                                  char *dirpath,
                                                  const int dirpath_maxncpy)
{
  if (repo->flag & USER_EXTENSION_REPO_FLAG_USE_CUSTOM_DIRECTORY) {
    return BLI_strncpy_rlen(dirpath, repo->custom_dirpath, dirpath_maxncpy);
  }

  /* TODO: support `BLENDER_USER_EXTENSIONS`, until then add to user resource. */
  std::optional<std::string> path = BKE_appdir_resource_path_id(BLENDER_RESOURCE_PATH_USER, false);
  /* Highly unlikely to fail as the directory doesn't have to exist. */
  if (!path) {
    dirpath[0] = '\0';
    return 0;
  }
  return BLI_path_join(dirpath, dirpath_maxncpy, path.value().c_str(), "extensions", repo->module);
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

static bool url_char_is_delimiter(const char ch)
{
  /* Punctuation (space to comma). */
  if (ch >= 32 && ch <= 44) {
    return true;
  }
  /* Other characters (colon to at-sign). */
  if (ch >= 58 && ch <= 64) {
    return true;
  }
  if (ELEM(ch, '/', '\\')) {
    return true;
  }
  return false;
}

bUserExtensionRepo *BKE_preferences_extension_repo_find_by_remote_path_prefix(
    const UserDef *userdef, const char *path_full, const bool only_enabled)
{
  const int path_full_len = strlen(path_full);
  const int path_full_offset = BKE_preferences_extension_repo_remote_scheme_end(path_full);

  LISTBASE_FOREACH (bUserExtensionRepo *, repo, &userdef->extension_repos) {
    if (only_enabled && (repo->flag & USER_EXTENSION_REPO_FLAG_DISABLED)) {
      continue;
    }

    /* Has a valid remote path to check. */
    if ((repo->flag & USER_EXTENSION_REPO_FLAG_USE_REMOTE_PATH) == 0) {
      continue;
    }
    if (repo->remote_path[0] == '\0') {
      continue;
    }

    /* Set path variables which may be offset by the "scheme". */
    const char *path_repo = repo->remote_path;
    const char *path_test = path_full;
    int path_test_len = path_full_len;

    /* Allow paths beginning with both `http` & `https` to be considered equivalent.
     * This is done by skipping the "scheme" prefix both have a scheme. */
    if (path_full_offset) {
      const int path_repo_offset = BKE_preferences_extension_repo_remote_scheme_end(path_repo);
      if (path_repo_offset) {
        path_repo += path_repo_offset;
        path_test += path_full_offset;
        path_test_len -= path_full_offset;
      }
    }

    /* The length of the path without trailing slashes. */
    int path_repo_len = strlen(path_repo);
    while (path_repo_len && ELEM(path_repo[path_repo_len - 1], '/', '\\')) {
      path_repo_len--;
    }

    if (path_test_len <= path_repo_len) {
      continue;
    }
    if (memcmp(path_repo, path_test, path_repo_len) != 0) {
      continue;
    }

    /* A delimiter must follow to ensure `path_test` doesn't reference a longer host-name.
     * Will typically be a `/` or a `:`. */
    if (!url_char_is_delimiter(path_test[path_repo_len])) {
      continue;
    }
    return repo;
  }
  return nullptr;
}

int BKE_preferences_extension_repo_remote_scheme_end(const char *url)
{
  /* Technically the "://" are not part of the scheme, so subtract 3 from the return value. */
  const char *scheme_check[] = {
      "http://",
      "https://",
      "file://",
  };
  for (int i = 0; i < ARRAY_SIZE(scheme_check); i++) {
    const char *scheme = scheme_check[i];
    int scheme_len = strlen(scheme);
    if (strncmp(url, scheme, scheme_len) == 0) {
      return scheme_len - 3;
    }
  }
  return 0;
}

void BKE_preferences_extension_remote_to_name(const char *remote_path,
                                              char name[sizeof(bUserExtensionRepo::name)])
{
  name[0] = '\0';
  if (int offset = BKE_preferences_extension_repo_remote_scheme_end(remote_path)) {
    remote_path += (offset + 3);
  }
  if (UNLIKELY(remote_path[0] == '\0')) {
    return;
  }

  const char *c = remote_path;
  /* Skip any delimiters (likely forward slashes for `file:///` on UNIX). */
  while (*c && url_char_is_delimiter(*c)) {
    c++;
  }
  /* Skip the domain name. */
  while (*c && !url_char_is_delimiter(*c)) {
    c++;
  }

  BLI_strncpy_utf8(
      name, remote_path, std::min(size_t(c - remote_path) + 1, sizeof(bUserExtensionRepo::name)));
}

int BKE_preferences_extension_repo_get_index(const UserDef *userdef,
                                             const bUserExtensionRepo *repo)
{
  return BLI_findindex(&userdef->extension_repos, repo);
}

/** \} */
