/*
 * Routines for working with singly linked lists
 * of 'links' - pointers to other data.
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
 */
 
#ifndef BLI_LINKLIST_H
#define BLI_LINKLIST_H

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

struct MemArena;

typedef void (*LinkNodeFreeFP)(void *link);
typedef void (*LinkNodeApplyFP)(void *link);

struct LinkNode;
typedef struct LinkNode {
	struct LinkNode *next;
	void *link;
} LinkNode;

int		BLI_linklist_length		(struct LinkNode *list);

void	BLI_linklist_reverse	(struct LinkNode **listp);

void	BLI_linklist_prepend		(struct LinkNode **listp, void *ptr);
void	BLI_linklist_prepend_arena	(struct LinkNode **listp, void *ptr, struct MemArena *ma);

void	BLI_linklist_free		(struct LinkNode *list, LinkNodeFreeFP freefunc);
void	BLI_linklist_apply		(struct LinkNode *list, LinkNodeApplyFP applyfunc);

#endif

