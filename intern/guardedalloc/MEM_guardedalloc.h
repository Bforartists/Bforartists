/**
 * $Id$
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
 */

/**

 * $Id$
 * Copyright (C) 2001 NaN Technologies B.V.
 * Guarded memory (de)allocation
 *
 *
 * @mainpage MEM - c-style guarded memory allocation
 *
 * @section about About the MEM module
 *
 * MEM provides guarded malloc/calloc calls. All memory is enclosed by
 * pads, to detect out-of-bound writes. All blocks are placed in a
 * linked list, so they remain reachable at all times. There is no
 * back-up in case the linked-list related data is lost.
 *
 * @section issues Known issues with MEM
 *
 * There are currently no known issues with MEM. Note that there is a
 * second intern/ module with MEM_ prefix, for use in c++.
 * 
 * @section dependencies Dependencies
 *
 * - stdlib
 *
 * - stdio
 *
 * */

#ifndef MEM_MALLOCN_H
#define MEM_MALLOCN_H

/* Needed for FILE* */
#include "stdio.h"

#ifdef __cplusplus
extern "C" {
#endif

	/** Returns the lenght of the allocated memory segment pointed at
	 * by vmemh. If the pointer was not previously allocated by this
	 * module, the result is undefined.*/
	int MEM_allocN_len(void *vmemh);

	/**
	 * Release memory previously allocatred by this module. 
	 */
	short MEM_freeN(void *vmemh);

	/**
	 * Duplicates a block of memory, and returns a pointer to the
	 * newly allocated block.  */
	void *MEM_dupallocN(void *vmemh);

	/**
	 * Allocate a block of memory of size len, with tag name str. The
	 * memory is cleared. The name must be static, because only a
	 * pointer to it is stored ! */
	void *MEM_callocN(unsigned int len, char * str);
	
	/** Allocate a block of memory of size len, with tag name str. The
	 * name must be a static, because only a pointer to it is stored !
	 * */
	void *MEM_mallocN(unsigned int len, char * str);

	/** Print a list of the names and sizes of all allocated memory
	 * blocks. */ 
	void MEM_printmemlist(void);

	/** Set the stream for error output. */
	void MEM_set_error_stream(FILE*);

	/**
	 * Are the start/end block markers still correct ?
	 *
	 * @retval 0 for correct memory, 1 for corrupted memory. */
	int MEM_check_memory_integrity(void);

#ifdef __cplusplus
}
#endif

#endif

