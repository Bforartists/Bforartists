/*
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
 * Contributor(s): Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef DNA_DEFS_H
#define DNA_DEFS_H

/** \file DNA_defs.h
 *  \ingroup DNA
 */

/* makesdna ignores */
#ifdef DNA_DEPRECATED_ALLOW
   /* allow use of deprecated items */
#  define DNA_DEPRECATED
#else
#  ifndef DNA_DEPRECATED
#    ifdef __GNUC__
#      define DNA_DEPRECATED __attribute__ ((deprecated))
#    else
       /* TODO, msvc & others */
#      define DNA_DEPRECATED
#    endif
#  endif
#endif

/* hrmf, we need a better include then this */
#include "../blenloader/BLO_sys_types.h" /* needed for int64_t only! */

/* Must not be defined for BMesh, as this guards code for pre-BMesh code to load BMesh .blend files */
/* #define USE_BMESH_FORWARD_COMPAT */

#endif /* DNA_DEFS_H */
