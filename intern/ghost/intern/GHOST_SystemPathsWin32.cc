/* SPDX-FileCopyrightText: 2011 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 */

#include "GHOST_SystemPathsWin32.hh"
#include "GHOST_Debug.hh"

#ifndef _WIN32_IE
#  define _WIN32_IE 0x0501
#endif
#include "utfconv.hh"
#include <shlobj.h>

GHOST_SystemPathsWin32::GHOST_SystemPathsWin32() {}

GHOST_SystemPathsWin32::~GHOST_SystemPathsWin32() {}

const char *GHOST_SystemPathsWin32::getSystemDir(int, const char *versionstr) const
{
  const char *system_dir = nullptr;

  /* 1 utf-16 might translate into 3 utf-8. 2 utf-16 translates into 4 utf-8. */
  static char knownpath[MAX_PATH * 3 + 128] = {0};
  PWSTR knownpath_16 = nullptr;

  HRESULT hResult = SHGetKnownFolderPath(
      FOLDERID_ProgramData, KF_FLAG_DEFAULT, nullptr, &knownpath_16);

  if (hResult == S_OK) {
    conv_utf_16_to_8(knownpath_16, knownpath, MAX_PATH * 3);
    strcat(knownpath, "\\Blender Foundation\\Blender\\");
    strcat(knownpath, versionstr);
    system_dir = knownpath;
  }

  CoTaskMemFree(knownpath_16);
  return system_dir;
}

const char *GHOST_SystemPathsWin32::getUserDir(int, const char *versionstr) const
{
  const char *user_dir = nullptr;

  static char knownpath[MAX_PATH * 3 + 128] = {0};
  PWSTR knownpath_16 = nullptr;

  HRESULT hResult = SHGetKnownFolderPath(
      FOLDERID_RoamingAppData, KF_FLAG_DEFAULT, nullptr, &knownpath_16);

  if (hResult == S_OK) {
    conv_utf_16_to_8(knownpath_16, knownpath, MAX_PATH * 3);
    strcat(knownpath, "\\Blender Foundation\\Blender\\");
    strcat(knownpath, versionstr);
    user_dir = knownpath;
  }

  CoTaskMemFree(knownpath_16);
  return user_dir;
}

const char *GHOST_SystemPathsWin32::getUserSpecialDir(GHOST_TUserSpecialDirTypes type) const
{
  const char *special_dir = nullptr;

  GUID folderid;
  switch (type) {
    case GHOST_kUserSpecialDirDesktop:
      folderid = FOLDERID_Desktop;
      break;
    case GHOST_kUserSpecialDirDocuments:
      folderid = FOLDERID_Documents;
      break;
    case GHOST_kUserSpecialDirDownloads:
      folderid = FOLDERID_Downloads;
      break;
    case GHOST_kUserSpecialDirMusic:
      folderid = FOLDERID_Music;
      break;
    case GHOST_kUserSpecialDirPictures:
      folderid = FOLDERID_Pictures;
      break;
    case GHOST_kUserSpecialDirVideos:
      folderid = FOLDERID_Videos;
      break;
    case GHOST_kUserSpecialDirCaches:
      folderid = FOLDERID_LocalAppData;
      break;
    default:
      GHOST_ASSERT(
          false,
          "GHOST_SystemPathsWin32::getUserSpecialDir(): Invalid enum value for type parameter");
      return nullptr;
  }

  static char knownpath[MAX_PATH * 3] = {0};
  PWSTR knownpath_16 = nullptr;
  HRESULT hResult = SHGetKnownFolderPath(folderid, KF_FLAG_DEFAULT, nullptr, &knownpath_16);

  if (hResult == S_OK) {
    conv_utf_16_to_8(knownpath_16, knownpath, MAX_PATH * 3);
    special_dir = knownpath;
  }

  CoTaskMemFree(knownpath_16);
  return special_dir;
}

const char *GHOST_SystemPathsWin32::getBinaryDir() const
{
  static char fullname[MAX_PATH * 3] = {0};
  wchar_t fullname_16[MAX_PATH * 3];

  if (GetModuleFileNameW(0, fullname_16, MAX_PATH)) {
    conv_utf_16_to_8(fullname_16, fullname, MAX_PATH * 3);
    return fullname;
  }

  return nullptr;
}

void GHOST_SystemPathsWin32::addToSystemRecentFiles(const char *filepath) const
{
  UTF16_ENCODE(filepath);
  UTF16_ENCODE(BLENDER_WIN_APPID);
  SHARDAPPIDINFO info;
  IShellItem *shell_item;

  HRESULT hr = CoInitializeEx(nullptr, COINIT_APARTMENTTHREADED | COINIT_DISABLE_OLE1DDE);
  if (!SUCCEEDED(hr)) {
    return;
  }

  hr = SHCreateItemFromParsingName(filepath_16, nullptr, IID_PPV_ARGS(&shell_item));
  if (SUCCEEDED(hr)) {
    info.psi = shell_item;
    info.pszAppID = BLENDER_WIN_APPID_16;
    SHAddToRecentDocs(SHARD_APPIDINFO, &info);
  }

  CoUninitialize();
  UTF16_UN_ENCODE(BLENDER_WIN_APPID);
  UTF16_UN_ENCODE(filepath);
}
