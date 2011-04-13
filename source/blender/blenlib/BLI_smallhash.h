/**
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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
 
#ifndef BLI_SMALLHASH_H
#define BLI_SMALLHASH_H

/*******a light stack-friendly hash library******
 *      (it uses stack space for smallish hash tables)     */

/*based on a doubling non-chaining approach */

#include "MEM_guardedalloc.h"
#include "BLO_sys_types.h"
#include "BLI_utildefines.h"
#include <string.h>

extern unsigned int hashsizes[];
#define NONHASH	-25436536
typedef struct entry {uintptr_t key; void *val;} entry;

/*how much stack space to use before dynamically allocating memory*/
#define SMSTACKSIZE	521
typedef struct SmallHash {
	entry *table, _stacktable[SMSTACKSIZE], _copytable[SMSTACKSIZE];
	entry *stacktable, *copytable;
	int used;
	int curhash;
	int size;
} SmallHash;

typedef struct SmallHashIter {
	SmallHash *hash;
	int i;
} SmallHashIter;

/*CELL_UNUSED means this cell is inside a key series, while CELL_FREE
  means this cell terminates a key series.
  
  no chance of anyone shoving INT32_MAX-2 into a *val pointer, I
  imagine.  hopefully. */
#define CELL_UNUSED	((void*)0x7FFFFFFF)
#define CELL_FREE	((void*)0x7FFFFFFD)

#define NONZERO(n) ((n) + !(n))
#define HASHNEXT(h, hoff) ABS(((h) + ((hoff=NONZERO(hoff*2)+1), hoff)))

BM_INLINE void BLI_smallhash_init(SmallHash *hash)
{
	int i;
	
	memset(hash, 0, sizeof(*hash));
	
	hash->table = hash->_stacktable;
	hash->curhash = 2;
	hash->size = hashsizes[hash->curhash];
	
	hash->copytable = hash->_copytable;
	hash->stacktable = hash->_stacktable;
	
	for (i=0; i<hash->size; i++) {
		hash->table[i].val = CELL_FREE;
	}
}

/*NOTE: does *not* free *hash itself!  only the direct data!*/
BM_INLINE void BLI_smallhash_release(SmallHash *hash)
{
	if (!hash)
		return;
	
	if (hash->table != hash->stacktable)
		MEM_freeN(hash->table);
}

BM_INLINE void BLI_smallhash_insert(SmallHash *hash, uintptr_t key, void *item) 
{
	int h, hoff=1;

	key = ABS(key);

	if (hash->size < hash->used*3) {
		int newsize = hashsizes[++hash->curhash];
		entry *tmp;
		int i = 0;
		
		if (hash->table != hash->stacktable || newsize > SMSTACKSIZE) {
			tmp = MEM_callocN(sizeof(*hash->table)*newsize, "new hashkeys");
		} else {
			SWAP(entry*, hash->stacktable, hash->copytable);
			tmp = hash->stacktable;
		}
		
		SWAP(entry*, tmp, hash->table);
		
		hash->size = newsize;
		
		for (i=0; i<hash->size; i++) {
			hash->table[i].val = CELL_FREE;
		}
		
		for (i=0; i<hashsizes[hash->curhash-1]; i++) {
			if (ELEM(tmp[i].val, CELL_UNUSED, CELL_FREE))
				continue;
			
			h = tmp[i].key; hoff = 1;
			while (!ELEM(hash->table[h % newsize].val, CELL_UNUSED, CELL_FREE))
				h = HASHNEXT(h, hoff);
			
			h %= newsize;
			
			hash->table[h].key = tmp[i].key;
			hash->table[h].val = tmp[i].val;
		}
		
		if (tmp != hash->stacktable && tmp != hash->copytable) {
			MEM_freeN(tmp);
		}
	}
	
	h = key; hoff = 1;
	while (!ELEM(hash->table[h % hash->size].val, CELL_UNUSED, CELL_FREE))
		h = HASHNEXT(h, hoff);
	
	h %= hash->size;
	hash->table[h].key = key;
	hash->table[h].val = item;
	
	hash->used++;
}

BM_INLINE void BLI_smallhash_remove(SmallHash *hash, uintptr_t key)
{
	int h, hoff=1;

	key = ABS(key);
	h = key;
	
	while (hash->table[h % hash->size].key != key 
	      || hash->table[h % hash->size].val == CELL_UNUSED)
	{
		if (hash->table[h % hash->size].val == CELL_FREE)
			return;
		h = HASHNEXT(h, hoff);
	}
	
	h %= hash->size;
	hash->table[h].key = 0;
	hash->table[h].val = CELL_UNUSED;
}

BM_INLINE void *BLI_smallhash_lookup(SmallHash *hash, uintptr_t key)
{
	int h, hoff=1;

	key = ABS(key);
	h = key;
	
	if (!hash->table)
		return NULL;
	
	while (hash->table[h % hash->size].key != key 
	      || hash->table[h % hash->size].val == CELL_UNUSED)
	{
		if (hash->table[h % hash->size].val == CELL_FREE)
			return NULL;
		h = HASHNEXT(h, hoff);
	}
	
	return hash->table[h % hash->size].val;
}


BM_INLINE int BLI_smallhash_haskey(SmallHash *hash, uintptr_t key)
{
	int h = ABS(key), hoff=1;
	key = ABS(key);
	
	if (!hash->table)
		return 0;
	
	while (hash->table[h % hash->size].key != key 
	      || hash->table[h % hash->size].val == CELL_UNUSED)
	{
		if (hash->table[h % hash->size].val == CELL_FREE)
			return 0;
		h = HASHNEXT(h, hoff);
	}
	
	return 1;
}

BM_INLINE int BLI_smallhash_count(SmallHash *hash)
{
	return hash->used;
}

BM_INLINE void *BLI_smallhash_iternext(SmallHashIter *iter, uintptr_t *key)
{
	while (iter->i < iter->hash->size) {
		if (iter->hash->table[iter->i].val != CELL_UNUSED && iter->hash->table[iter->i].val != CELL_FREE) {
			if (key)
				*key = iter->hash->table[iter->i].key;
			
			iter->i++;
			return iter->hash->table[iter->i-1].val;
		}
		
		iter->i++;
	}
	
	return NULL;
}

BM_INLINE void *BLI_smallhash_iternew(SmallHash *hash, SmallHashIter *iter, uintptr_t *key) 
{
	iter->hash = hash;
	iter->i = 0;
	
	return BLI_smallhash_iternext(iter, key);
}

#endif // BLI_SMALLHASH_H
