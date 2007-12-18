/**
 * blenlib/BLI_listBase.h    mar 2001 Nzc
 *
 * $Id$ 
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 *
 * These structs are the foundation for all linked lists in the
 * library system.
 *
 */

#ifndef DNA_LISTBASE_H
#define DNA_LISTBASE_H

#ifdef __cplusplus
extern "C" {
#endif

/* generic - all structs which are used in linked-lists used this */
typedef struct Link
{
	struct Link *next,*prev;
} Link;


/* use this when it is not worth defining a custom one... */
typedef struct LinkData
{
	struct LinkData *next, *prev;
	void *data;
} LinkData;

/* never change the size of this! genfile.c detects pointerlen with it */
typedef struct ListBase 
{
	void *first, *last;
} ListBase;

/* 8 byte alignment! */

#ifdef __cplusplus
}
#endif

#endif

