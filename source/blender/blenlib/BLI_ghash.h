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
 
#ifndef BLI_GHASH_H
#define BLI_GHASH_H

/** \file BLI_ghash.h
 *  \ingroup bli
 *  \brief A general (pointer -> pointer) hash table ADT
 */

#ifdef __cplusplus
extern "C" {
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "BLI_mempool.h"
#include "BLI_blenlib.h"

typedef unsigned int	(*GHashHashFP)		(const void *key);
typedef int				(*GHashCmpFP)		(const void *a, const void *b);
typedef	void			(*GHashKeyFreeFP)	(void *key);
typedef void			(*GHashValFreeFP)	(void *val);

typedef struct Entry {
	struct Entry *next;
	
	void *key, *val;
} Entry;

typedef struct GHash {
	GHashHashFP	hashfp;
	GHashCmpFP	cmpfp;
	
	Entry **buckets;
	struct BLI_mempool *entrypool;
	int nbuckets, nentries, cursize;
} GHash;

typedef struct GHashIterator {
	GHash *gh;
	int curBucket;
	struct Entry *curEntry;
} GHashIterator;

GHash*	BLI_ghash_new		(GHashHashFP hashfp, GHashCmpFP cmpfp, const char *info);
void	BLI_ghash_free		(GHash *gh, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp);

//BM_INLINE void	BLI_ghash_insert	(GHash *gh, void *key, void *val);
//BM_INLINE int		BLI_ghash_remove	(GHash *gh, void *key, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp);
//BM_INLINE void*	BLI_ghash_lookup	(GHash *gh, void *key);
//BM_INLINE int		BLI_ghash_haskey	(GHash *gh, void *key);

int		BLI_ghash_size		(GHash *gh);

/* *** */

	/**
	 * Create a new GHashIterator. The hash table must not be mutated
	 * while the iterator is in use, and the iterator will step exactly
	 * BLI_ghash_size(gh) times before becoming done.
	 * 
	 * @param gh The GHash to iterate over.
	 * @return Pointer to a new DynStr.
	 */
GHashIterator*	BLI_ghashIterator_new		(GHash *gh);
	/**
	 * Init an already allocated GHashIterator. The hash table must not
	 * be mutated while the iterator is in use, and the iterator will
	 * step exactly BLI_ghash_size(gh) times before becoming done.
	 * 
	 * @param ghi The GHashIterator to initialize.
	 * @param gh The GHash to iterate over.
	 */
void BLI_ghashIterator_init(GHashIterator *ghi, GHash *gh);
	/**
	 * Free a GHashIterator.
	 *
	 * @param ghi The iterator to free.
	 */
void			BLI_ghashIterator_free		(GHashIterator *ghi);

	/**
	 * Retrieve the key from an iterator.
	 *
	 * @param ghi The iterator.
	 * @return The key at the current index, or NULL if the 
	 * iterator is done.
	 */
void*			BLI_ghashIterator_getKey	(GHashIterator *ghi);
	/**
	 * Retrieve the value from an iterator.
	 *
	 * @param ghi The iterator.
	 * @return The value at the current index, or NULL if the 
	 * iterator is done.
	 */
void*			BLI_ghashIterator_getValue	(GHashIterator *ghi);
	/**
	 * Steps the iterator to the next index.
	 *
	 * @param ghi The iterator.
	 */
void			BLI_ghashIterator_step		(GHashIterator *ghi);
	/**
	 * Determine if an iterator is done (has reached the end of
	 * the hash table).
	 *
	 * @param ghi The iterator.
	 * @return True if done, False otherwise.
	 */
int				BLI_ghashIterator_isDone	(GHashIterator *ghi);

/* *** */

unsigned int	BLI_ghashutil_ptrhash	(const void *key);
int				BLI_ghashutil_ptrcmp	(const void *a, const void *b);

unsigned int	BLI_ghashutil_strhash	(const void *key);
int				BLI_ghashutil_strcmp	(const void *a, const void *b);

unsigned int	BLI_ghashutil_inthash	(const void *ptr);
int				BLI_ghashutil_intcmp(const void *a, const void *b);

/*begin of macro-inlined functions*/
extern unsigned int hashsizes[];

#if 0
#define BLI_ghash_insert(gh, _k, _v){\
	unsigned int _hash= (gh)->hashfp(_k)%gh->nbuckets;\
	Entry *_e= BLI_mempool_alloc((gh)->entrypool);\
	_e->key= _k;\
	_e->val= _v;\
	_e->next= (gh)->buckets[_hash];\
	(gh)->buckets[_hash]= _e;\
	if (++(gh)->nentries>(gh)->nbuckets*3) {\
		Entry *_e, **_old= (gh)->buckets;\
		int _i, _nold= (gh)->nbuckets;\
		(gh)->nbuckets= hashsizes[++(gh)->cursize];\
		(gh)->buckets= malloc((gh)->nbuckets*sizeof(*(gh)->buckets));\
		memset((gh)->buckets, 0, (gh)->nbuckets*sizeof(*(gh)->buckets));\
		for (_i=0; _i<_nold; _i++) {\
			for (_e= _old[_i]; _e;) {\
				Entry *_n= _e->next;\
				_hash= (gh)->hashfp(_e->key)%(gh)->nbuckets;\
				_e->next= (gh)->buckets[_hash];\
				(gh)->buckets[_hash]= _e;\
				_e= _n;\
			}\
		}\
		free(_old); } }
#endif

/*---------inlined functions---------*/
BM_INLINE void BLI_ghash_insert(GHash *gh, void *key, void *val) {
	unsigned int hash= gh->hashfp(key)%gh->nbuckets;
	Entry *e= (Entry*) BLI_mempool_alloc(gh->entrypool);

	e->key= key;
	e->val= val;
	e->next= gh->buckets[hash];
	gh->buckets[hash]= e;
	
	if (++gh->nentries>(float)gh->nbuckets/2) {
		Entry **old= gh->buckets;
		int i, nold= gh->nbuckets;
		
		gh->nbuckets= hashsizes[++gh->cursize];
		gh->buckets= (Entry**)MEM_mallocN(gh->nbuckets*sizeof(*gh->buckets), "buckets");
		memset(gh->buckets, 0, gh->nbuckets*sizeof(*gh->buckets));
		
		for (i=0; i<nold; i++) {
			for (e= old[i]; e;) {
				Entry *n= e->next;
				
				hash= gh->hashfp(e->key)%gh->nbuckets;
				e->next= gh->buckets[hash];
				gh->buckets[hash]= e;
				
				e= n;
			}
		}
		
		MEM_freeN(old);
	}
}

BM_INLINE void* BLI_ghash_lookup(GHash *gh, const void *key) 
{
	if(gh) {
		unsigned int hash= gh->hashfp(key)%gh->nbuckets;
		Entry *e;
		
		for (e= gh->buckets[hash]; e; e= e->next)
			if (gh->cmpfp(key, e->key)==0)
				return e->val;
	}	
	return NULL;
}

BM_INLINE int BLI_ghash_remove (GHash *gh, void *key, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp)
{
	unsigned int hash= gh->hashfp(key)%gh->nbuckets;
	Entry *e;
	Entry *p = NULL;

	for (e= gh->buckets[hash]; e; e= e->next) {
		if (gh->cmpfp(key, e->key)==0) {
			Entry *n= e->next;

			if (keyfreefp) keyfreefp(e->key);
			if (valfreefp) valfreefp(e->val);
			BLI_mempool_free(gh->entrypool, e);


			e= n;
			if (p)
				p->next = n;
			else
				gh->buckets[hash] = n;

			--gh->nentries;
			return 1;
		}
		p = e;
	}
 
	return 0;
}

BM_INLINE int BLI_ghash_haskey(GHash *gh, void *key) {
	unsigned int hash= gh->hashfp(key)%gh->nbuckets;
	Entry *e;
	
	for (e= gh->buckets[hash]; e; e= e->next)
		if (gh->cmpfp(key, e->key)==0)
			return 1;
	
	return 0;
}

#ifdef __cplusplus
}
#endif

#endif
