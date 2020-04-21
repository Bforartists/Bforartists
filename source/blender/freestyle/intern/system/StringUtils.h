/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

#ifndef __FREESTYLE_STRING_UTILS_H__
#define __FREESTYLE_STRING_UTILS_H__

/** \file
 * \ingroup freestyle
 * \brief String utilities
 */

#include <cstring>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

extern "C" {
#include "BLI_path_util.h"
#include "BLI_string.h"
}

using namespace std;

namespace Freestyle {

namespace StringUtils {

void getPathName(const string &path, const string &base, vector<string> &pathnames);

// STL related
struct ltstr {
  bool operator()(const char *s1, const char *s2) const
  {
    return strcmp(s1, s2) < 0;
  }
};

}  // end of namespace StringUtils

} /* namespace Freestyle */

#endif  // __FREESTYLE_STRING_UTILS_H__
