/**
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
 * The Original Code is Copyright (C) 2010 by Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef	GHOST_PATH_API_H
#define GHOST_PATH_API_H

#include "GHOST_Types.h"

#ifdef __cplusplus
extern "C" { 
#endif

/**
 * Determine the base dir in which shared resources are located. It will first try to use
 * "unpack and run" path, then look for properly installed path, not including versioning.
 * @return Unsigned char string pointing to system dir (eg /usr/share/blender/).
 */
extern const GHOST_TUns8* GHOST_getSystemDir();

/**
 * Determine the base dir in which user configuration is stored, not including versioning.
 * @return Unsigned char string pointing to user dir (eg ~).
 */
extern const GHOST_TUns8* GHOST_getUserDir();


/**
 * Determine the dir in which the binary file is found.
 * @return Unsigned char string pointing to binary dir (eg ~/usr/local/bin/).
 */
extern const GHOST_TUns8* GHOST_getBinaryDir();

#ifdef __cplusplus
} 
#endif

#endif
