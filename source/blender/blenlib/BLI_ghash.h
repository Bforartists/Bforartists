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
 */
 
#ifndef __BLI_GHASH_H__
#define __BLI_GHASH_H__

/** \file BLI_ghash.h
 *  \ingroup bli
 *  \brief A general (pointer -> pointer) hash table ADT
 */

#include "BLI_sys_types.h" /* for bool */

#ifdef __cplusplus
extern "C" {
#endif

typedef unsigned int  (*GHashHashFP)     (const void *key);
typedef int           (*GHashCmpFP)      (const void *a, const void *b);
typedef void          (*GHashKeyFreeFP)  (void *key);
typedef void          (*GHashValFreeFP)  (void *val);

typedef struct GHash GHash;

typedef struct GHashIterator {
	GHash *gh;
	struct Entry *curEntry;
	unsigned int curBucket;
} GHashIterator;

enum {
	GHASH_FLAG_ALLOW_DUPES = (1 << 0),  /* only checked for in debug mode */
};

/* *** */

GHash *BLI_ghash_new_ex(GHashHashFP hashfp, GHashCmpFP cmpfp, const char *info,
                        const unsigned int nentries_reserve);
GHash *BLI_ghash_new(GHashHashFP hashfp, GHashCmpFP cmpfp, const char *info);
void   BLI_ghash_free(GHash *gh, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp);
void   BLI_ghash_insert(GHash *gh, void *key, void *val);
bool   BLI_ghash_reinsert(GHash *gh, void *key, void *val, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp);
void  *BLI_ghash_lookup(GHash *gh, const void *key);
void **BLI_ghash_lookup_p(GHash *gh, const void *key);
bool   BLI_ghash_remove(GHash *gh, void *key, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp);
void   BLI_ghash_clear(GHash *gh, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp);
void   BLI_ghash_clear_ex(GHash *gh, GHashKeyFreeFP keyfreefp, GHashValFreeFP valfreefp,
                          const unsigned int nentries_reserve);
void  *BLI_ghash_pop(GHash *gh, void *key, GHashKeyFreeFP keyfreefp);
bool   BLI_ghash_haskey(GHash *gh, const void *key);
int    BLI_ghash_size(GHash *gh);
void   BLI_ghash_flag_set(GHash *gh, unsigned int flag);
void   BLI_ghash_flag_clear(GHash *gh, unsigned int flag);

/* *** */

GHashIterator *BLI_ghashIterator_new(GHash *gh);

void           BLI_ghashIterator_init(GHashIterator *ghi, GHash *gh);
void           BLI_ghashIterator_free(GHashIterator *ghi);

void          *BLI_ghashIterator_getKey(GHashIterator *ghi);
void          *BLI_ghashIterator_getValue(GHashIterator *ghi);

void           BLI_ghashIterator_step(GHashIterator *ghi);
bool           BLI_ghashIterator_done(GHashIterator *ghi);

#define GHASH_ITER(gh_iter_, ghash_)                                          \
	for (BLI_ghashIterator_init(&gh_iter_, ghash_);                           \
	     BLI_ghashIterator_done(&gh_iter_) == false;                          \
	     BLI_ghashIterator_step(&gh_iter_))

#define GHASH_ITER_INDEX(gh_iter_, ghash_, i_)                                \
	for (BLI_ghashIterator_init(&gh_iter_, ghash_), i_ = 0;                   \
	     BLI_ghashIterator_done(&gh_iter_) == false;                          \
	     BLI_ghashIterator_step(&gh_iter_), i_++)

/* *** */

unsigned int    BLI_ghashutil_ptrhash(const void *key);
int             BLI_ghashutil_ptrcmp(const void *a, const void *b);

unsigned int    BLI_ghashutil_strhash(const void *key);
int             BLI_ghashutil_strcmp(const void *a, const void *b);

unsigned int    BLI_ghashutil_inthash(const void *ptr);
int             BLI_ghashutil_intcmp(const void *a, const void *b);

GHash          *BLI_ghash_ptr_new_ex(const char *info,
                                     const unsigned int nentries_reserve);
GHash          *BLI_ghash_ptr_new(const char *info);
GHash          *BLI_ghash_str_new_ex(const char *info,
                                     const unsigned int nentries_reserve);
GHash          *BLI_ghash_str_new(const char *info);
GHash          *BLI_ghash_int_new_ex(const char *info,
                                     const unsigned int nentries_reserve);
GHash          *BLI_ghash_int_new(const char *info);
GHash          *BLI_ghash_pair_new_ex(const char *info,
                                      const unsigned int nentries_reserve);
GHash          *BLI_ghash_pair_new(const char *info);

typedef struct GHashPair {
	const void *first;
	const void *second;
} GHashPair;

GHashPair      *BLI_ghashutil_pairalloc(const void *first, const void *second);
unsigned int    BLI_ghashutil_pairhash(const void *ptr);
int             BLI_ghashutil_paircmp(const void *a, const void *b);
void            BLI_ghashutil_pairfree(void *ptr);


/* *** */

typedef struct GSet GSet;

typedef GHashHashFP GSetHashFP;
typedef GHashCmpFP GSetCmpFP;
typedef GHashKeyFreeFP GSetKeyFreeFP;

/* so we can cast but compiler sees as different */
typedef struct GSetIterator {
	GHashIterator _ghi
#ifdef __GNUC__
	__attribute__ ((deprecated))
#endif
	;
} GSetIterator;

GSet  *BLI_gset_new_ex(GSetHashFP hashfp, GSetCmpFP cmpfp, const char *info,
                       const unsigned int nentries_reserve);
GSet  *BLI_gset_new(GSetHashFP hashfp, GSetCmpFP cmpfp, const char *info);
int    BLI_gset_size(GSet *gs);
void   BLI_gset_free(GSet *gs, GSetKeyFreeFP keyfreefp);
void   BLI_gset_insert(GSet *gh, void *key);
bool   BLI_gset_reinsert(GSet *gh, void *key, GSetKeyFreeFP keyfreefp);
bool   BLI_gset_haskey(GSet *gs, const void *key);
bool   BLI_gset_remove(GSet *gs, void *key, GSetKeyFreeFP keyfreefp);
void   BLI_gset_clear_ex(GSet *gs, GSetKeyFreeFP keyfreefp,
                         const unsigned int nentries_reserve);
void  BLI_gset_clear(GSet *gs, GSetKeyFreeFP keyfreefp);

GSet *BLI_gset_ptr_new_ex(const char *info,
                          const unsigned int nentries_reserve);
GSet *BLI_gset_ptr_new(const char *info);
GSet *BLI_gset_pair_new_ex(const char *info,
                            const unsigned int nentries_reserve);
GSet *BLI_gset_pair_new(const char *info);

/* rely on inline api for now */
BLI_INLINE GSetIterator *BLI_gsetIterator_new(GSet *gs) { return (GSetIterator *)BLI_ghashIterator_new((GHash *)gs); }
BLI_INLINE void BLI_gsetIterator_init(GSetIterator *gsi, GSet *gs) { BLI_ghashIterator_init((GHashIterator *)gsi, (GHash *)gs); }
BLI_INLINE void BLI_gsetIterator_free(GSetIterator *gsi) { BLI_ghashIterator_free((GHashIterator *)gsi); }
BLI_INLINE void *BLI_gsetIterator_getKey(GSetIterator *gsi) { return BLI_ghashIterator_getKey((GHashIterator *)gsi); }
BLI_INLINE void BLI_gsetIterator_step(GSetIterator *gsi) { BLI_ghashIterator_step((GHashIterator *)gsi); }
BLI_INLINE bool BLI_gsetIterator_done(GSetIterator *gsi) { return BLI_ghashIterator_done((GHashIterator *)gsi); }

#define GSET_ITER(gs_iter_, gset_)                                            \
	for (BLI_gsetIterator_init(&gs_iter_, gset_);                             \
	     BLI_gsetIterator_done(&gs_iter_) == false;                           \
	     BLI_gsetIterator_step(&gs_iter_))

#define GSET_ITER_INDEX(gs_iter_, gset_, i_)                                  \
	for (BLI_gsetIterator_init(&gs_iter_, gset_), i_ = 0;                     \
	     BLI_gsetIterator_done(&gs_iter_) == false;                           \
	     BLI_gsetIterator_step(&gs_iter_), i_++)

#ifdef __cplusplus
}
#endif

#endif /* __BLI_GHASH_H__ */
