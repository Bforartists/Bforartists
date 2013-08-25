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
 * Contributor(s): Daniel Dunbar
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
#ifndef __BLI_EDGEHASH_H__
#define __BLI_EDGEHASH_H__

/** \file BLI_edgehash.h
 *  \ingroup bli
 *  \author Daniel Dunbar
 *  \brief A general unordered 2-int pair hash table ADT.
 */

struct EdgeHash;
struct EdgeHashIterator;
typedef struct EdgeHash EdgeHash;
typedef struct EdgeHashIterator EdgeHashIterator;

typedef void (*EdgeHashFreeFP)(void *key);

enum {
	EDGEHASH_FLAG_ALLOW_DUPES = (1 << 0),  /* only checked for in debug mode */
};

EdgeHash       *BLI_edgehash_new_ex(const char *info,
                                    const unsigned int nentries_reserve);
EdgeHash       *BLI_edgehash_new(const char *info);
void            BLI_edgehash_free(EdgeHash *eh, EdgeHashFreeFP valfreefp);
void            BLI_edgehash_insert(EdgeHash *eh, unsigned int v0, unsigned int v1, void *val);
bool            BLI_edgehash_reinsert(EdgeHash *eh, unsigned int v0, unsigned int v1, void *val);
void           *BLI_edgehash_lookup(EdgeHash *eh, unsigned int v0, unsigned int v1);
void          **BLI_edgehash_lookup_p(EdgeHash *eh, unsigned int v0, unsigned int v1);
bool            BLI_edgehash_haskey(EdgeHash *eh, unsigned int v0, unsigned int v1);
int             BLI_edgehash_size(EdgeHash *eh);
void            BLI_edgehash_clear_ex(EdgeHash *eh, EdgeHashFreeFP valfreefp,
                                      const unsigned int nentries_reserve);
void            BLI_edgehash_clear(EdgeHash *eh, EdgeHashFreeFP valfreefp);
void            BLI_edgehash_flag_set(EdgeHash *eh, unsigned int flag);
void            BLI_edgehash_flag_clear(EdgeHash *eh, unsigned int flag);

EdgeHashIterator   *BLI_edgehashIterator_new(EdgeHash *eh);
void                BLI_edgehashIterator_free(EdgeHashIterator *ehi);
void                BLI_edgehashIterator_getKey(EdgeHashIterator *ehi, unsigned int *v0_r, unsigned int *v1_r);
void               *BLI_edgehashIterator_getValue(EdgeHashIterator *ehi);
void                BLI_edgehashIterator_setValue(EdgeHashIterator *ehi, void *val);
void                BLI_edgehashIterator_step(EdgeHashIterator *ehi);
bool                BLI_edgehashIterator_isDone(EdgeHashIterator *ehi);

#define BLI_EDGEHASH_SIZE_GUESS_FROM_LOOPS(totloop)  ((totloop) / 2)
#define BLI_EDGEHASH_SIZE_GUESS_FROM_POLYS(totpoly)  ((totpoly) * 2)

/* *** EdgeSet *** */

struct EdgeSet;
struct EdgeSetIterator;
typedef struct EdgeSet EdgeSet;
typedef struct EdgeSetIterator EdgeSetIterator;

EdgeSet *BLI_edgeset_new_ex(const char *info,
                            const unsigned int nentries_reserve);
EdgeSet *BLI_edgeset_new(const char *info);
int      BLI_edgeset_size(EdgeSet *es);
bool     BLI_edgeset_reinsert(EdgeSet *es, unsigned int v0, unsigned int v1);
void     BLI_edgeset_insert(EdgeSet *es, unsigned int v0, unsigned int v1);
bool     BLI_edgeset_haskey(EdgeSet *eh, unsigned int v0, unsigned int v1);
void     BLI_edgeset_free(EdgeSet *es);

/* rely on inline api for now */
BLI_INLINE EdgeSetIterator *BLI_edgesetIterator_new(EdgeSet *gs) { return (EdgeSetIterator *)BLI_edgehashIterator_new((EdgeHash *)gs); }
BLI_INLINE void BLI_edgesetIterator_free(EdgeSetIterator *esi) { BLI_edgehashIterator_free((EdgeHashIterator *)esi); }
BLI_INLINE void BLI_edgesetIterator_getKey(EdgeSetIterator *esi, unsigned int *v0_r, unsigned int *v1_r) { return BLI_edgehashIterator_getKey((EdgeHashIterator *)esi, v0_r, v1_r); }
BLI_INLINE void BLI_edgesetIterator_step(EdgeSetIterator *esi) { BLI_edgehashIterator_step((EdgeHashIterator *)esi); }
BLI_INLINE bool BLI_edgesetIterator_isDone(EdgeSetIterator *esi) { return BLI_edgehashIterator_isDone((EdgeHashIterator *)esi); }


#endif  /* __BLI_EDGEHASH_H__ */
