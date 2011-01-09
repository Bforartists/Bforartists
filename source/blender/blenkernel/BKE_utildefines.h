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

/* This file shold contain blender format spesific macros
 * generic defines should go in BLI_utildefines.h */

#ifndef BKE_UTILDEFINES_H
#define BKE_UTILDEFINES_H

/* these values need to be hardcoded in structs, dna does not recognize defines */
/* also defined in DNA_space_types.h */
#ifndef FILE_MAXDIR
#define FILE_MAXDIR			160
#define FILE_MAXFILE		80
#define FILE_MAX			240
#endif

/* this weirdo pops up in two places ... */
#if !defined(WIN32)
#ifndef O_BINARY
#define O_BINARY 0
#endif
#endif

/* INTEGER CODES */
#if defined(__sgi) || defined (__sparc) || defined (__sparc__) || defined (__PPC__) || defined (__ppc__) || defined (__hppa__) || defined (__BIG_ENDIAN__)
	/* Big Endian */
#define MAKE_ID(a,b,c,d) ( (int)(a)<<24 | (int)(b)<<16 | (c)<<8 | (d) )
#else
	/* Little Endian */
#define MAKE_ID(a,b,c,d) ( (int)(d)<<24 | (int)(c)<<16 | (b)<<8 | (a) )
#endif

#define ID_NEW(a)		if( (a) && (a)->id.newid ) (a)= (void *)(a)->id.newid

#define DATA MAKE_ID('D','A','T','A')
#define GLOB MAKE_ID('G','L','O','B')
#define IMAG MAKE_ID('I','M','A','G')

#define DNA1 MAKE_ID('D','N','A','1')
#define TEST MAKE_ID('T','E','S','T') /* used as preview between 'REND' and 'GLOB' */
#define REND MAKE_ID('R','E','N','D')
#define USER MAKE_ID('U','S','E','R')

#define ENDB MAKE_ID('E','N','D','B')

/* Bit operations */
#define BTST(a,b)	( ( (a) & 1<<(b) )!=0 )   
#define BNTST(a,b)	( ( (a) & 1<<(b) )==0 )
#define BTST2(a,b,c)	( BTST( (a), (b) ) || BTST( (a), (c) ) )
#define BSET(a,b)	( (a) | 1<<(b) )
#define BCLR(a,b)	( (a) & ~(1<<(b)) )
/* bit-row */
#define BROW(min, max)	(((max)>=31? 0xFFFFFFFF: (1<<(max+1))-1) - ((min)? ((1<<(min))-1):0) )

#define BMEMSET(mem, val, size) {unsigned int _i; char *_c = (char*) mem; for (_i=0; _i<size; _i++) *_c++ = val;}

#endif // BKE_UTILDEFINES_H
