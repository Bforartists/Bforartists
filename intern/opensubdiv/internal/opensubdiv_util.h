// Copyright 2013 Blender Foundation. All rights reserved.
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software Foundation,
// Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

#ifndef OPENSUBDIV_UTIL_H_
#define OPENSUBDIV_UTIL_H_

#include <stdint.h>

#include <algorithm>
#include <cassert>
#include <vector>
#include <stack>
#include <string>
#include <unordered_map>
#include <utility>

namespace opensubdiv_capi {

using std::fill;
using std::make_pair;
using std::max;
using std::min;
using std::pair;
using std::stack;
using std::string;
using std::swap;
using std::unordered_map;
using std::vector;

#define foreach(x, y) for (x : y)

#define STRINGIFY_ARG(x) "" #x
#define STRINGIFY_APPEND(a, b) "" a #b
#define STRINGIFY(x) STRINGIFY_APPEND("", x)

void stringSplit(vector<string> *tokens,
                 const string &str,
                 const string &separators,
                 bool skip_empty);

}  // namespace opensubdiv_capi

#endif  // OPENSUBDIV_UTIL_H_
