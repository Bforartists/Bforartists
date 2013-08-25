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
 * Contributor(s): Daniel Dunbar, Joseph Eagar
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenlib/intern/edgehash.c
 *  \ingroup bli
 *
 * A general (pointer -> pointer) hash table ADT
 *
 * \note Based on 'BLI_ghash.c', make sure these stay in sync.
 */


#include <stdlib.h>
#include <string.h>
#include <limits.h>

#include "MEM_guardedalloc.h"

#include "BLI_utildefines.h"
#include "BLI_edgehash.h"
#include "BLI_mempool.h"

#ifdef __GNUC__
#  pragma GCC diagnostic error "-Wsign-conversion"
#  if (__GNUC__ * 100 + __GNUC_MINOR__) >= 406  /* gcc4.6+ only */
#    pragma GCC diagnostic error "-Wsign-compare"
#    pragma GCC diagnostic error "-Wconversion"
#  endif
#endif

/**************inlined code************/
static const unsigned int _ehash_hashsizes[] = {
	1, 3, 5, 11, 17, 37, 67, 131, 257, 521, 1031, 2053, 4099, 8209,
	16411, 32771, 65537, 131101, 262147, 524309, 1048583, 2097169,
	4194319, 8388617, 16777259, 33554467, 67108879, 134217757,
	268435459
};

/* ensure v0 is smaller */
#define EDGE_ORD(v0, v1) \
	if (v0 > v1) {       \
		v0 ^= v1;        \
		v1 ^= v0;        \
		v0 ^= v1;        \
	} (void)0

/***/

typedef struct EdgeEntry {
	struct EdgeEntry *next;
	unsigned int v0, v1;
	void *val;
} EdgeEntry;

struct EdgeHash {
	EdgeEntry **buckets;
	BLI_mempool *epool;
	unsigned int nbuckets, nentries;
	unsigned int cursize, flag;
};


/* -------------------------------------------------------------------- */
/* EdgeHash API */

/** \name Internal Utility API
 * \{ */

BLI_INLINE bool edgehash_test_expand_buckets(const unsigned int nentries, const unsigned int nbuckets)
{
	return (nentries > nbuckets * 3);
}

/**
 * Increase initial bucket size to match a reserved ammount.
 */
BLI_INLINE void edgehash_buckets_reserve(EdgeHash *eh, const unsigned int nentries_reserve)
{
	while (edgehash_test_expand_buckets(nentries_reserve, eh->nbuckets)) {
		eh->nbuckets = _ehash_hashsizes[++eh->cursize];
	}
}

BLI_INLINE unsigned int edgehash_keyhash(EdgeHash *eh, unsigned int v0, unsigned int v1)
{
	BLI_assert(v0 < v1);

	return ((v0 * 39) ^ (v1 * 31)) % eh->nbuckets;
}

BLI_INLINE EdgeEntry *edgehash_lookup_entry_ex(EdgeHash *eh, unsigned int v0, unsigned int v1,
                                               const unsigned int hash)
{
	EdgeEntry *e;
	BLI_assert(v0 < v1);
	for (e = eh->buckets[hash]; e; e = e->next) {
		if (v0 == e->v0 && v1 == e->v1) {
			return e;
		}
	}
	return NULL;
}

BLI_INLINE EdgeEntry *edgehash_lookup_entry(EdgeHash *eh, unsigned int v0, unsigned int v1)
{
	unsigned int hash;
	EDGE_ORD(v0, v1); /* ensure v0 is smaller */
	hash = edgehash_keyhash(eh, v0, v1);
	return edgehash_lookup_entry_ex(eh, v0, v1, hash);
}

static void edgehash_insert_ex(EdgeHash *eh, unsigned int v0, unsigned int v1, void *val,
                               unsigned int hash)
{
	EdgeEntry *e = BLI_mempool_alloc(eh->epool);

	BLI_assert((eh->flag & EDGEHASH_FLAG_ALLOW_DUPES) || (BLI_edgehash_haskey(eh, v0, v1) == 0));

	/* this helps to track down errors with bad edge data */
	BLI_assert(v0 < v1);
	BLI_assert(v0 != v1);

	e->next = eh->buckets[hash];
	e->v0 = v0;
	e->v1 = v1;
	e->val = val;
	eh->buckets[hash] = e;

	if (UNLIKELY(edgehash_test_expand_buckets(++eh->nentries, eh->nbuckets))) {
		EdgeEntry **old = eh->buckets;
		const unsigned int nold = eh->nbuckets;
		unsigned int i;

		eh->nbuckets = _ehash_hashsizes[++eh->cursize];
		eh->buckets = MEM_callocN(eh->nbuckets * sizeof(*eh->buckets), "eh buckets");

		for (i = 0; i < nold; i++) {
			EdgeEntry *e_next;
			for (e = old[i]; e; e = e_next) {
				e_next = e->next;
				hash = edgehash_keyhash(eh, e->v0, e->v1);
				e->next = eh->buckets[hash];
				eh->buckets[hash] = e;
			}
		}

		MEM_freeN(old);
	}
}
/** \} */


/** \name Public API
 * \{ */

/* Public API */

EdgeHash *BLI_edgehash_new_ex(const char *info,
                              const unsigned int nentries_reserve)
{
	EdgeHash *eh = MEM_mallocN(sizeof(*eh), info);

	eh->nbuckets = _ehash_hashsizes[0];  /* eh->cursize */
	eh->nentries = 0;
	eh->cursize = 0;
	eh->flag = 0;

	/* if we have reserved the number of elements that this hash will contain */
	if (nentries_reserve) {
		edgehash_buckets_reserve(eh, nentries_reserve);
	}

	eh->buckets = MEM_callocN(eh->nbuckets * sizeof(*eh->buckets), "eh buckets 2");
	eh->epool = BLI_mempool_create(sizeof(EdgeEntry), 512, 512, BLI_MEMPOOL_SYSMALLOC);

	return eh;
}

EdgeHash *BLI_edgehash_new(const char *info)
{
	return BLI_edgehash_new_ex(info, 0);
}

/**
 * Insert edge (\a v0, \a v1) into hash with given value, does
 * not check for duplicates.
 */
void BLI_edgehash_insert(EdgeHash *eh, unsigned int v0, unsigned int v1, void *val)
{
	unsigned int hash;
	EDGE_ORD(v0, v1); /* ensure v0 is smaller */
	hash = edgehash_keyhash(eh, v0, v1);
	edgehash_insert_ex(eh, v0, v1, val, hash);
}

/**
 * Assign a new value to a key that may already be in edgehash.
 */
void BLI_edgehash_reinsert(EdgeHash *eh, unsigned int v0, unsigned int v1, void *val)
{
	unsigned int hash;
	EdgeEntry *e;

	EDGE_ORD(v0, v1); /* ensure v0 is smaller */
	hash = edgehash_keyhash(eh, v0, v1);

	e = edgehash_lookup_entry_ex(eh, v0, v1, hash);
	if (e) {
		e->val = val;
	}
	else {
		edgehash_insert_ex(eh, v0, v1, val, hash);
	}
}

/**
 * Return pointer to value for given edge (\a v0, \a v1),
 * or NULL if key does not exist in hash.
 */
void **BLI_edgehash_lookup_p(EdgeHash *eh, unsigned int v0, unsigned int v1)
{
	EdgeEntry *e = edgehash_lookup_entry(eh, v0, v1);
	return e ? &e->val : NULL;
}

/**
 * Return value for given edge (\a v0, \a v1), or NULL if
 * if key does not exist in hash. (If need exists
 * to differentiate between key-value being NULL and
 * lack of key then see BLI_edgehash_lookup_p().
 */
void *BLI_edgehash_lookup(EdgeHash *eh, unsigned int v0, unsigned int v1)
{
	EdgeEntry *e = edgehash_lookup_entry(eh, v0, v1);
	return e ? e->val : NULL;
}

/**
 * Return boolean true/false if edge (v0,v1) in hash.
 */
bool BLI_edgehash_haskey(EdgeHash *eh, unsigned int v0, unsigned int v1)
{
	return (edgehash_lookup_entry(eh, v0, v1) != NULL);
}

/**
 * Return number of keys in hash.
 */
int BLI_edgehash_size(EdgeHash *eh)
{
	return (int)eh->nentries;
}

/**
 * Remove all edges from hash.
 */
void BLI_edgehash_clear(EdgeHash *eh, EdgeHashFreeFP valfreefp)
{
	unsigned int i;
	
	for (i = 0; i < eh->nbuckets; i++) {
		EdgeEntry *e;
		
		for (e = eh->buckets[i]; e; ) {
			EdgeEntry *n = e->next;
			
			if (valfreefp) valfreefp(e->val);
			BLI_mempool_free(eh->epool, e);
			
			e = n;
		}
		eh->buckets[i] = NULL;
	}

	eh->nentries = 0;
}

void BLI_edgehash_free(EdgeHash *eh, EdgeHashFreeFP valfreefp)
{
	BLI_edgehash_clear(eh, valfreefp);

	BLI_mempool_destroy(eh->epool);

	MEM_freeN(eh->buckets);
	MEM_freeN(eh);
}


void BLI_edgehash_flag_set(EdgeHash *eh, unsigned int flag)
{
	eh->flag |= flag;
}

void BLI_edgehash_flag_clear(EdgeHash *eh, unsigned int flag)
{
	eh->flag &= ~flag;
}

/** \} */


/* -------------------------------------------------------------------- */
/* EdgeHash Iterator API */

/** \name Iterator API
 * \{ */

struct EdgeHashIterator {
	EdgeHash *eh;
	unsigned int curBucket;
	EdgeEntry *curEntry;
};


/**
 * Create a new EdgeHashIterator. The hash table must not be mutated
 * while the iterator is in use, and the iterator will step exactly
 * BLI_edgehash_size(gh) times before becoming done.
 */
EdgeHashIterator *BLI_edgehashIterator_new(EdgeHash *eh)
{
	EdgeHashIterator *ehi = MEM_mallocN(sizeof(*ehi), "eh iter");
	ehi->eh = eh;
	ehi->curEntry = NULL;
	ehi->curBucket = UINT_MAX;  /* wraps to zero */
	while (!ehi->curEntry) {
		ehi->curBucket++;
		if (ehi->curBucket == ehi->eh->nbuckets)
			break;
		ehi->curEntry = ehi->eh->buckets[ehi->curBucket];
	}
	return ehi;
}

/**
 * Free an EdgeHashIterator.
 */
void BLI_edgehashIterator_free(EdgeHashIterator *ehi)
{
	MEM_freeN(ehi);
}

/**
 * Retrieve the key from an iterator.
 */
void BLI_edgehashIterator_getKey(EdgeHashIterator *ehi, unsigned int *v0_r, unsigned int *v1_r)
{
	if (ehi->curEntry) {
		*v0_r = ehi->curEntry->v0;
		*v1_r = ehi->curEntry->v1;
	}
}

/**
 * Retrieve the value from an iterator.
 */
void *BLI_edgehashIterator_getValue(EdgeHashIterator *ehi)
{
	return ehi->curEntry ? ehi->curEntry->val : NULL;
}

/**
 * Set the value for an iterator.
 */
void BLI_edgehashIterator_setValue(EdgeHashIterator *ehi, void *val)
{
	if (ehi->curEntry) {
		ehi->curEntry->val = val;
	}
}

/**
 * Steps the iterator to the next index.
 */
void BLI_edgehashIterator_step(EdgeHashIterator *ehi)
{
	if (ehi->curEntry) {
		ehi->curEntry = ehi->curEntry->next;
		while (!ehi->curEntry) {
			ehi->curBucket++;
			if (ehi->curBucket == ehi->eh->nbuckets) {
				break;
			}

			ehi->curEntry = ehi->eh->buckets[ehi->curBucket];
		}
	}
}

/**
 * Determine if an iterator is done.
 */
bool BLI_edgehashIterator_isDone(EdgeHashIterator *ehi)
{
	return (ehi->curEntry == NULL);
}

/** \} */
