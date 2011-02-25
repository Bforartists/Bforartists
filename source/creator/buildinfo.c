/*
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
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
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file creator/buildinfo.c
 *  \ingroup creator
 */


#ifdef WITH_BUILDINFO_HEADER
#include "buildinfo.h"
#endif

#ifdef BUILD_DATE

/* copied from BLI_utildefines.h */
#define STRINGIFY_ARG(x) #x
#define STRINGIFY(x) STRINGIFY_ARG(x)

/* currently only these are defined in the header */
char build_date[]= STRINGIFY(BUILD_DATE);
char build_time[]= STRINGIFY(BUILD_TIME);
char build_rev[]= STRINGIFY(BUILD_REV);

char build_platform[]= STRINGIFY(BUILD_PLATFORM);
char build_type[]= STRINGIFY(BUILD_TYPE);

#ifdef BUILD_CFLAGS
char build_cflags[]= STRINGIFY(BUILD_CFLAGS);
char build_cxxflags[]= STRINGIFY(BUILD_CXXFLAGS);
char build_linkflags[]= STRINGIFY(BUILD_LINKFLAGS);
char build_system[]= STRINGIFY(BUILD_SYSTEM);
#else
char build_cflags[]= "unmaintained buildsystem alert!";
char build_cxxflags[]= "unmaintained buildsystem alert!";
char build_linkflags[]= "unmaintained buildsystem alert!";
char build_system[]= "unmaintained buildsystem alert!";
#endif

#endif // BUILD_DATE
