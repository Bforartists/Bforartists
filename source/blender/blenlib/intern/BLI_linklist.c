/**
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
 * Support for linked lists.
 */

#include "MEM_guardedalloc.h"
#include "BLI_blenlib.h"
#include "BLI_linklist.h"
#include "BLI_memarena.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

int BLI_linklist_length(LinkNode *list) {
	if (0) {
		return list?(1+BLI_linklist_length(list->next)):0;
	} else {
		int len;

		for (len=0; list; list= list->next)
			len++;
	
		return len;
	}
}

void BLI_linklist_reverse(LinkNode **listp) {
	LinkNode *rhead= NULL, *cur= *listp;
	
	while (cur) {
		LinkNode *next= cur->next;
		
		cur->next= rhead;
		rhead= cur;
		
		cur= next;
	}
	
	*listp= rhead;
}

void BLI_linklist_prepend(LinkNode **listp, void *ptr) {
	LinkNode *nlink= MEM_mallocN(sizeof(*nlink), "nlink");
	nlink->link= ptr;
	
	nlink->next= *listp;
	*listp= nlink;
}

void BLI_linklist_prepend_arena(LinkNode **listp, void *ptr, MemArena *ma) {
	LinkNode *nlink= BLI_memarena_alloc(ma, sizeof(*nlink));
	nlink->link= ptr;
	
	nlink->next= *listp;
	*listp= nlink;
}

void BLI_linklist_free(LinkNode *list, LinkNodeFreeFP freefunc) {
	while (list) {
		LinkNode *next= list->next;
		
		if (freefunc)
			freefunc(list->link);
		MEM_freeN(list);
		
		list= next;
	}
}

void BLI_linklist_apply(LinkNode *list, LinkNodeApplyFP applyfunc) {
	for (; list; list= list->next)
		applyfunc(list->link);
}
