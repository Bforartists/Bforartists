// Copyright 2015 Blender Foundation. All rights reserved.
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
//
// Author: Sergey Sharybin

#ifndef OPENSUBDIV_INTERNAL_H_
#define OPENSUBDIV_INTERNAL_H_

// Perform full topology validation when exporting it to OpenSubdiv.
#ifdef NDEBUG
// Never do for release builds.
#  undef OPENSUBDIV_VALIDATE_TOPOLOGY
#else
#  define OPENSUBDIV_VALIDATE_TOPOLOGY
#endif

#endif  // OPENSUBDIV_INTERNAL_H_
