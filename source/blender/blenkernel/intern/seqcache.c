/**
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
 * Peter Schlaile <peter [at] schlaile [dot] de> 2010
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"
#include "MEM_CacheLimiterC-Api.h"

#include "DNA_sequence_types.h"
#include "BKE_sequencer.h"
#include "BLI_ghash.h"
#include "BLI_mempool.h"
#include <pthread.h>

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

typedef struct seqCacheKey 
{
	struct Sequence * seq;
	int rectx;
	int recty;
	float cfra;
	seq_stripelem_ibuf_t type;
} seqCacheKey;

typedef struct seqCacheEntry
{
	ImBuf * ibuf;
	MEM_CacheLimiterHandleC * c_handle;
} seqCacheEntry;

static GHash * hash = 0;
static MEM_CacheLimiterC * limitor = 0;
static struct BLI_mempool * entrypool = 0;
static struct BLI_mempool * keypool = 0;
static int ibufs_in  = 0;
static int ibufs_rem = 0;

static unsigned int HashHash(void *key_)
{
	seqCacheKey * key = (seqCacheKey*) key_;
	unsigned int rval = key->rectx + key->recty;

	rval ^= *(unsigned int*) &key->cfra;
	rval += key->type;
	rval ^= ((intptr_t) key->seq) << 6;

	return rval;
}

static int HashCmp(void *a_, void *b_)
{
	seqCacheKey * a = (seqCacheKey*) a_;
	seqCacheKey * b = (seqCacheKey*) b_;

	if (a->seq < b->seq) {
		return -1;		
	}
	if (a->seq > b->seq) {
		return 1;
	}

	if (a->cfra < b->cfra) {
		return -1;
	}
	if (a->cfra > b->cfra) {
		return 1;
	}

	if (a->type < b->type) {
		return -1;
	}
	if (a->type > b->type) {
		return 1;
	}

	if (a->rectx < b->rectx) {
		return -1;
	}
	if (a->rectx > b->rectx) {
		return 1;
	}

	if (a->recty < b->recty) {
		return -1;
	}
	if (a->recty > b->recty) {
		return 1;
	}

	return 0;
}

static void HashKeyFree(void *key)
{
	BLI_mempool_free(keypool, key);
}

static void HashValFree(void *val)
{
	seqCacheEntry* e = (seqCacheEntry*) val;

	if (e->ibuf) {
		/* fprintf(stderr, "Removing: %p, cnt: %d\n", e->ibuf, 
		   e->ibuf->refcounter); */
		IMB_freeImBuf(e->ibuf);
		MEM_CacheLimiter_unmanage(e->c_handle);
		ibufs_rem++;
	}

	e->ibuf = 0;
	e->c_handle = 0;

	BLI_mempool_free(entrypool, e);
}

static void IMB_seq_cache_destructor(void * p)
{
	seqCacheEntry* e = (seqCacheEntry*) p;
	
	if (e && e->ibuf) {
		/* fprintf(stderr, "Removing: %p, cnt: %d\n", e->ibuf,
		   e->ibuf->refcounter); */
		IMB_freeImBuf(e->ibuf);
		ibufs_rem++;

		e->ibuf = 0;
		e->c_handle = 0;
	}
}

void seq_stripelem_cache_init()
{
	hash = BLI_ghash_new(HashHash, HashCmp, "seq stripelem cache hash");
	limitor = new_MEM_CacheLimiter( IMB_seq_cache_destructor );

	entrypool = BLI_mempool_create(sizeof(seqCacheEntry), 64, 64, 0);
	keypool = BLI_mempool_create(sizeof(seqCacheKey), 64, 64, 0);
}

void seq_stripelem_cache_destruct()
{
	if (!entrypool) {
		return;
	}
	BLI_ghash_free(hash, HashKeyFree, HashValFree);
	delete_MEM_CacheLimiter(limitor);
	BLI_mempool_destroy(entrypool);
	BLI_mempool_destroy(keypool);
}

void seq_stripelem_cache_cleanup()
{
	if (!entrypool) {
		seq_stripelem_cache_init();
	}

	/* fprintf(stderr, "Stats before cleanup: in: %d rem: %d\n",
	   ibufs_in, ibufs_rem); */

	BLI_ghash_free(hash, HashKeyFree, HashValFree);
	hash = BLI_ghash_new(HashHash, HashCmp, "seq stripelem cache hash");

	/* fprintf(stderr, "Stats after cleanup: in: %d rem: %d\n",
	   ibufs_in, ibufs_rem); */

}

struct ImBuf * seq_stripelem_cache_get(
	struct Sequence * seq, int rectx, int recty, 
	float cfra, seq_stripelem_ibuf_t type)
{
	seqCacheKey key;
	seqCacheEntry * e;

	if (!seq) {
		return 0;
	}

	if (!entrypool) {
		seq_stripelem_cache_init();
	}

	key.seq = seq;
	key.rectx = rectx;
	key.recty = recty;
	key.cfra = cfra - seq->start;
	key.type = type;
	
	e = (seqCacheEntry*) BLI_ghash_lookup(hash, &key);

	if (e && e->ibuf) {
		IMB_refImBuf(e->ibuf);

		MEM_CacheLimiter_touch(e->c_handle);
		return e->ibuf;
	}
	return 0;
}

void seq_stripelem_cache_put(
	struct Sequence * seq, int rectx, int recty, 
	float cfra, seq_stripelem_ibuf_t type, struct ImBuf * i)
{
	seqCacheKey * key;
	seqCacheEntry * e;

	if (!i) {
		return;
	}

	ibufs_in++;

	if (!entrypool) {
		seq_stripelem_cache_init();
	}

	key = (seqCacheKey*) BLI_mempool_alloc(keypool);

	key->seq = seq;
	key->rectx = rectx;
	key->recty = recty;
	key->cfra = cfra - seq->start;
	key->type = type;

	/* we want our own version */
	IMB_refImBuf(i);

	e = (seqCacheEntry*) BLI_mempool_alloc(entrypool);

	e->ibuf = i;
	e->c_handle = 0;

	BLI_ghash_remove(hash, key, HashKeyFree, HashValFree);
	BLI_ghash_insert(hash, key, e);

	e->c_handle = MEM_CacheLimiter_insert(limitor, e);

	MEM_CacheLimiter_ref(e->c_handle);
	MEM_CacheLimiter_enforce_limits(limitor);
	MEM_CacheLimiter_unref(e->c_handle);
}
