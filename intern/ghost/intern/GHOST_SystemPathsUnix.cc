/* SPDX-FileCopyrightText: 2010 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup GHOST
 */

#include <sstream>

#include "GHOST_SystemPathsUnix.hh"

#include "GHOST_Debug.hh"

/* For timing. */
#include <sys/time.h>
#include <unistd.h>

#include <pwd.h> /* For get home without use `getenv()`. */
#include <string>

using std::string;

#ifdef PREFIX
static const char *static_path = PREFIX "/share";
#else
static const char *static_path = nullptr;
#endif

GHOST_SystemPathsUnix::GHOST_SystemPathsUnix() = default;

GHOST_SystemPathsUnix::~GHOST_SystemPathsUnix() = default;

const char *GHOST_SystemPathsUnix::getSystemDir(int /*version*/, const char *versionstr) const
{
  /* no prefix assumes a portable build which only uses bundled scripts */
  if (static_path) {
    static string system_path = string(static_path) + "/blender/" + versionstr;
    return system_path.c_str();
  }

  return nullptr;
}

static const char *home_dir_get()
{
  const char *home_dir = getenv("HOME");
  if (home_dir == nullptr) {
    if (const passwd *pwuser = getpwuid(getuid())) {
      home_dir = pwuser->pw_dir;
    }
  }
  return home_dir;
}

const char *GHOST_SystemPathsUnix::getUserDir(int version, const char *versionstr) const
{
  static string user_path = "";
  static int last_version = 0;

  /* in blender 2.64, we migrate to XDG. to ensure the copy previous settings
   * operator works we give a different path depending on the requested version */
  if (version < 264) {
    if (user_path.empty() || last_version != version) {
      const char *home = home_dir_get();

      last_version = version;

      if (home) {
        user_path = string(home) + "/.blender/" + versionstr;
      }
      else {
        return nullptr;
      }
    }
    return user_path.c_str();
  }
  if (user_path.empty() || last_version != version) {
    const char *home = getenv("XDG_CONFIG_HOME");

    last_version = version;

    if (home) {
      user_path = string(home) + "/blender/" + versionstr;
    }
    else {
      home = home_dir_get();
      if (home) {
        user_path = string(home) + "/.config/blender/" + versionstr;
      }
      else {
        return nullptr;
      }
    }
  }

  return user_path.c_str();
}

const char *GHOST_SystemPathsUnix::getUserSpecialDir(GHOST_TUserSpecialDirTypes type) const
{
  const char *type_str;
  static string path = "";

  switch (type) {
    case GHOST_kUserSpecialDirDesktop:
      type_str = "DESKTOP";
      break;
    case GHOST_kUserSpecialDirDocuments:
      type_str = "DOCUMENTS";
      break;
    case GHOST_kUserSpecialDirDownloads:
      type_str = "DOWNLOAD";
      break;
    case GHOST_kUserSpecialDirMusic:
      type_str = "MUSIC";
      break;
    case GHOST_kUserSpecialDirPictures:
      type_str = "PICTURES";
      break;
    case GHOST_kUserSpecialDirVideos:
      type_str = "VIDEOS";
      break;
    case GHOST_kUserSpecialDirCaches: {
      const char *cache_dir = getenv("XDG_CACHE_HOME");
      if (cache_dir) {
        return cache_dir;
      }

      /* If `XDG_CACHE_HOME` is not set, then `$HOME/.cache is used`. */
      const char *home_dir = getenv("HOME");
      path = string(home_dir) + "/.cache";
      return path.c_str();
    }
    default:
      GHOST_ASSERT(
          false,
          "GHOST_SystemPathsUnix::getUserSpecialDir(): Invalid enum value for type parameter");
      return nullptr;
  }

  /* Pipe `stderr` to `/dev/null` to avoid error prints. We will fail gracefully still. */
  string command = string("xdg-user-dir ") + type_str + " 2> /dev/null";

  FILE *fstream = popen(command.c_str(), "r");
  if (fstream == nullptr) {
    return nullptr;
  }
  std::stringstream path_stream;
  while (!feof(fstream)) {
    char c = fgetc(fstream);
    /* `xdg-user-dir` ends the path with '\n'. */
    if (c == '\n') {
      break;
    }
    path_stream << c;
  }
  if (pclose(fstream) == -1) {
    perror("GHOST_SystemPathsUnix::getUserSpecialDir failed at pclose()");
    return nullptr;
  }

  path = path_stream.str();
  return path[0] ? path.c_str() : nullptr;
}

const char *GHOST_SystemPathsUnix::getBinaryDir() const
{
  return nullptr;
}

void GHOST_SystemPathsUnix::addToSystemRecentFiles(const char * /*filename*/) const
{
  /* TODO: implement for X11 */
}
