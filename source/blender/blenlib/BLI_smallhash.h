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
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Joseph Eagar.
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
#ifndef __BLI_SMALLHASH_H__
#define __BLI_SMALLHASH_H__

/** \file BLI_smallhash.h
 *  \ingroup bli
 */

#include "BLI_compiler_attrs.h"

typedef struct {
	uintptr_t key;
	void *val;
} SmallHashEntry;

/*how much stack space to use before dynamically allocating memory*/
#define SMSTACKSIZE 64
typedef struct SmallHash {
	SmallHashEntry *buckets;
	SmallHashEntry *buckets_stack;
	SmallHashEntry *buckets_copy;
	SmallHashEntry _buckets_stack[SMSTACKSIZE];
	SmallHashEntry _buckets_copy[SMSTACKSIZE];
	unsigned int nbuckets;
	unsigned int nentries;
	unsigned int cursize;
} SmallHash;

typedef struct {
	SmallHash *sh;
	unsigned int i;
} SmallHashIter;

void    BLI_smallhash_init(SmallHash *sh) ATTR_NONNULL(1);
void    BLI_smallhash_release(SmallHash *sh) ATTR_NONNULL(1);
void    BLI_smallhash_insert(SmallHash *sh, uintptr_t key, void *item) ATTR_NONNULL(1);
bool    BLI_smallhash_remove(SmallHash *sh, uintptr_t key) ATTR_NONNULL(1);
void   *BLI_smallhash_lookup(SmallHash *sh, uintptr_t key) ATTR_NONNULL(1) ATTR_WARN_UNUSED_RESULT;
void  **BLI_smallhash_lookup_p(SmallHash *sh, uintptr_t key) ATTR_NONNULL(1) ATTR_WARN_UNUSED_RESULT;
bool    BLI_smallhash_haskey(SmallHash *sh, uintptr_t key) ATTR_NONNULL(1);
int     BLI_smallhash_count(SmallHash *sh)  ATTR_NONNULL(1);
void   *BLI_smallhash_iternext(SmallHashIter *iter, uintptr_t *key)  ATTR_NONNULL(1) ATTR_WARN_UNUSED_RESULT;
void   *BLI_smallhash_iternew(SmallHash *sh, SmallHashIter *iter, uintptr_t *key) ATTR_NONNULL(1) ATTR_WARN_UNUSED_RESULT;
/* void BLI_smallhash_print(SmallHash *sh); */ /* UNUSED */

#endif /* __BLI_SMALLHASH_H__ */
