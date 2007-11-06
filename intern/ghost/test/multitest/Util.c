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

#include <stdlib.h>

#include <string.h>
#include <stdarg.h>
#include <stdio.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "Util.h"

void* memdbl(void *mem, int *size_pr, int item_size) {
	int cur_size= *size_pr;
	int new_size= cur_size?(cur_size*2):1;
	void *nmem= MEM_mallocN(new_size*item_size, "memdbl");
	
	memcpy(nmem, mem, cur_size*item_size);
	MEM_freeN(mem);
		
	*size_pr= new_size;
	return nmem;
}

char* string_dup(char *str) {
	int len= strlen(str);
	char *nstr= MEM_mallocN(len + 1, "string_dup");

	memcpy(nstr, str, len+1);
	
	return nstr;
}

void fatal(char *fmt, ...) {
	va_list ap;
	
	fprintf(stderr, "FATAL: ");
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fprintf(stderr, "\n");
	
	exit(1);
}
