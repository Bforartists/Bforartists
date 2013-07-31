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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * A general (pointer -> pointer) hash table ADT
 */

/** \file blender/blenlib/intern/BLI_ghash.c
 *  \ingroup bli
 *
 * \note edgehash.c is based on this, make sure they stay in sync.
 */

#include <string.h>
#include <stdlib.h>
#include <limits.h>

#include "MEM_guardedalloc.h"

#include "BLI_sys_types.h"  /* for intptr_t support */
#include "BLI_utildefines.h"
#include "BLI_mempool.h"
#include "BLI_ghash.h"

/***/

#ifdef __GNUC__
#  pragma GCC diagnostic error "-Wsign-conversion"
#  if (__GNUC__ * 100 + __GNUC_MINOR__) >= 406  /* gcc4.6+ only */
#    pragma GCC diagnostic error "-Wsign-compare"
#    pragma GCC diagnostic error "-Wconversion"
#  endif
#endif

const unsigned int hashsizes[] = {
	5, 11, 17, 37, 67, 131, 257, 521, 1031, 2053, 4099, 8209, 
	16411, 32771, 65537, 131101, 262147, 524309, 1048583, 2097169, 
	4194319, 8388617, 16777259, 33554467, 67108879, 134217757, 
	268435459
};

/***/

GHash *BLI_ghash_new(GHashHashFP hashfp, GHashCmpFP cmpfp, const char *info)
{
	GHash *gh = MEM_mallocN(sizeof(*gh), info);
	gh->hashfp = hashfp;
	gh->cmpfp = cmpfp;
	gh->entrypool = BLI_mempool_create(sizeof(Entry), 64, 64, 0);

	gh->cursize = 0;
	gh->nentries = 0;
	gh->nbuckets = hashsizes[gh->cursize];

	gh->buckets = MEM_callocN(gh->nbuckets * sizeof(*gh->buckets), "buckets");

	return gh;
}

int BLI_ghash_size(GHash *gh)
{
	return (int)gh->nentries;
}

void BLI_ghash_insert(GHash *gh, void *key, void *val)
{
	unsigned int hash = gh->hashfp(key) % gh->nbuckets;
	Entry *e = (Entry *)BLI_mempool_alloc(gh->entrypool);

	e->next = gh->buckets[hash];
	e->key = key;
	e->val = val;
	gh->buckets[hash] = e;

	if (UNLIKELY(++gh->nentries > gh->nbuckets / 2)) {
		Entry **old = gh->buckets;
		const unsigned nold = gh->nbuckets;
		unsigned int i;

		gh->nbuckets = hashsizes[++gh->cursize];
		gh->buckets = (Entry **)MEM_callocN(gh->nbuckets * sizeof(*gh->buckets), "buckets");

		for (i = 0; i < nold; i++) {
			Entry *e_next;
			for (e = old[i]; e; e = e_next) {
				e_next = e->next;
				hash = gh->hashfp(e->key) % gh->nbuckets;
				e->next = gh->buckets[hash];
				gh->buckets[hash] = e;
			}
		}

		MEM_freeN(old);
	}
}

void *BLI_ghash_lookup(GHash *gh, const void *key)
{
	const unsigned int hash = gh->hashfp(key) % gh->nbuckets;
	Entry *e;

	for (e = gh->buckets[hash]; e; e = e->next) {
		if (gh->cmpfp(key, e->key) == 0) {
			return e->val;
		}
	}
	return NULL;
}

bool BLI_ghash_remove(GHash *gh, void *key, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp)
{
	unsigned int hash = gh->hashfp(key) % gh->nbuckets;
	Entry *e;
	Entry *p = NULL;

	for (e = gh->buckets[hash]; e; e = e->next) {
		if (gh->cmpfp(key, e->key) == 0) {
			Entry *n = e->next;

			if (keyfreefp) keyfreefp(e->key);
			if (valfreefp) valfreefp(e->val);
			BLI_mempool_free(gh->entrypool, e);

			/* correct but 'e' isn't used before return */
			/* e = n; *//*UNUSED*/
			if (p) p->next = n;
			else   gh->buckets[hash] = n;

			gh->nentries--;
			return true;
		}
		p = e;
	}

	return false;
}

void BLI_ghash_clear(GHash *gh, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp)
{
	unsigned int i;

	if (keyfreefp || valfreefp) {
		for (i = 0; i < gh->nbuckets; i++) {
			Entry *e;

			for (e = gh->buckets[i]; e; ) {
				Entry *n = e->next;

				if (keyfreefp) keyfreefp(e->key);
				if (valfreefp) valfreefp(e->val);

				e = n;
			}
		}
	}

	gh->cursize = 0;
	gh->nentries = 0;
	gh->nbuckets = hashsizes[gh->cursize];

	MEM_freeN(gh->buckets);
	gh->buckets = MEM_callocN(gh->nbuckets * sizeof(*gh->buckets), "buckets");
}

/* same as above but return the value,
 * no free value argument since it will be returned */
void *BLI_ghash_pop(GHash *gh, void *key, GHashKeyFreeFP keyfreefp)
{
	unsigned int hash = gh->hashfp(key) % gh->nbuckets;
	Entry *e;
	Entry *p = NULL;

	for (e = gh->buckets[hash]; e; e = e->next) {
		if (gh->cmpfp(key, e->key) == 0) {
			Entry *n = e->next;
			void *value = e->val;

			if (keyfreefp) keyfreefp(e->key);
			BLI_mempool_free(gh->entrypool, e);

			/* correct but 'e' isn't used before return */
			/* e = n; *//*UNUSED*/
			if (p) p->next = n;
			else   gh->buckets[hash] = n;

			gh->nentries--;
			return value;
		}
		p = e;
	}

	return NULL;
}

bool BLI_ghash_haskey(GHash *gh, const void *key)
{
	unsigned int hash = gh->hashfp(key) % gh->nbuckets;
	Entry *e;

	for (e = gh->buckets[hash]; e; e = e->next)
		if (gh->cmpfp(key, e->key) == 0)
			return true;

	return false;
}

void BLI_ghash_free(GHash *gh, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp)
{
	unsigned int i;

	if (keyfreefp || valfreefp) {
		for (i = 0; i < gh->nbuckets; i++) {
			Entry *e;

			for (e = gh->buckets[i]; e; ) {
				Entry *n = e->next;

				if (keyfreefp) keyfreefp(e->key);
				if (valfreefp) valfreefp(e->val);

				e = n;
			}
		}
	}

	MEM_freeN(gh->buckets);
	BLI_mempool_destroy(gh->entrypool);
	gh->buckets = NULL;
	gh->nentries = 0;
	gh->nbuckets = 0;
	MEM_freeN(gh);
}

/***/

GHashIterator *BLI_ghashIterator_new(GHash *gh)
{
	GHashIterator *ghi = MEM_mallocN(sizeof(*ghi), "ghash iterator");
	BLI_ghashIterator_init(ghi, gh);
	return ghi;
}
void BLI_ghashIterator_init(GHashIterator *ghi, GHash *gh)
{
	ghi->gh = gh;
	ghi->curEntry = NULL;
	ghi->curBucket = UINT_MAX;  /* wraps to zero */
	while (!ghi->curEntry) {
		ghi->curBucket++;
		if (ghi->curBucket == ghi->gh->nbuckets)
			break;
		ghi->curEntry = ghi->gh->buckets[ghi->curBucket];
	}
}
void BLI_ghashIterator_free(GHashIterator *ghi)
{
	MEM_freeN(ghi);
}

void *BLI_ghashIterator_getKey(GHashIterator *ghi)
{
	return ghi->curEntry ? ghi->curEntry->key : NULL;
}
void *BLI_ghashIterator_getValue(GHashIterator *ghi)
{
	return ghi->curEntry ? ghi->curEntry->val : NULL;
}

void BLI_ghashIterator_step(GHashIterator *ghi)
{
	if (ghi->curEntry) {
		ghi->curEntry = ghi->curEntry->next;
		while (!ghi->curEntry) {
			ghi->curBucket++;
			if (ghi->curBucket == ghi->gh->nbuckets)
				break;
			ghi->curEntry = ghi->gh->buckets[ghi->curBucket];
		}
	}
}
bool BLI_ghashIterator_done(GHashIterator *ghi)
{
	return ghi->curEntry == NULL;
}

/***/

unsigned int BLI_ghashutil_ptrhash(const void *key)
{
	return (unsigned int)(intptr_t)key;
}
int BLI_ghashutil_ptrcmp(const void *a, const void *b)
{
	if (a == b)
		return 0;
	else
		return (a < b) ? -1 : 1;
}

unsigned int BLI_ghashutil_inthash(const void *ptr)
{
	uintptr_t key = (uintptr_t)ptr;

	key += ~(key << 16);
	key ^=  (key >>  5);
	key +=  (key <<  3);
	key ^=  (key >> 13);
	key += ~(key <<  9);
	key ^=  (key >> 17);

	return (unsigned int)(key & 0xffffffff);
}

int BLI_ghashutil_intcmp(const void *a, const void *b)
{
	if (a == b)
		return 0;
	else
		return (a < b) ? -1 : 1;
}

/**
 * This function implements the widely used "djb" hash apparently posted
 * by Daniel Bernstein to comp.lang.c some time ago.  The 32 bit
 * unsigned hash value starts at 5381 and for each byte 'c' in the
 * string, is updated: <literal>hash = hash * 33 + c</literal>.  This
 * function uses the signed value of each byte.
 *
 * note: this is the same hash method that glib 2.34.0 uses.
 */
unsigned int BLI_ghashutil_strhash(const void *ptr)
{
	const signed char *p;
	unsigned int h = 5381;

	for (p = ptr; *p != '\0'; p++) {
		h = (h << 5) + h + (unsigned int)*p;
	}

	return h;
}
int BLI_ghashutil_strcmp(const void *a, const void *b)
{
	return strcmp(a, b);
}

GHash *BLI_ghash_ptr_new(const char *info)
{
	return BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, info);
}
GHash *BLI_ghash_str_new(const char *info)
{
	return BLI_ghash_new(BLI_ghashutil_strhash, BLI_ghashutil_strcmp, info);
}
GHash *BLI_ghash_int_new(const char *info)
{
	return BLI_ghash_new(BLI_ghashutil_inthash, BLI_ghashutil_intcmp, info);
}
GHash *BLI_ghash_pair_new(const char *info)
{
	return BLI_ghash_new(BLI_ghashutil_pairhash, BLI_ghashutil_paircmp, info);
}

GHashPair *BLI_ghashutil_pairalloc(const void *first, const void *second)
{
	GHashPair *pair = MEM_mallocN(sizeof(GHashPair), "GHashPair");
	pair->first = first;
	pair->second = second;
	return pair;
}

unsigned int BLI_ghashutil_pairhash(const void *ptr)
{
	const GHashPair *pair = ptr;
	unsigned int hash = BLI_ghashutil_ptrhash(pair->first);
	return hash ^ BLI_ghashutil_ptrhash(pair->second);
}

int BLI_ghashutil_paircmp(const void *a, const void *b)
{
	const GHashPair *A = a;
	const GHashPair *B = b;

	int cmp = BLI_ghashutil_ptrcmp(A->first, B->first);
	if (cmp == 0)
		return BLI_ghashutil_ptrcmp(A->second, B->second);
	return cmp;
}

void BLI_ghashutil_pairfree(void *ptr)
{
	MEM_freeN(ptr);
}
