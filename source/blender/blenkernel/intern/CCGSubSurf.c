#ifdef USE_CCGSUBSURFLIB

/* $Id$ */

#include <stdlib.h>
#include <string.h>

#include "CCGSubSurf.h"

/***/

typedef unsigned char	byte;

/***/

static int kHashSizes[] = {
	1, 3, 5, 11, 17, 37, 67, 131, 257, 521, 1031, 2053, 4099, 8209, 
	16411, 32771, 65537, 131101, 262147, 524309, 1048583, 2097169, 
	4194319, 8388617, 16777259, 33554467, 67108879, 134217757, 268435459
};

typedef struct _EHEntry EHEntry;
struct _EHEntry {
	EHEntry *next;
	void *key;
};
typedef struct _EHash {
	EHEntry **buckets;
	int numEntries, curSize, curSizeIdx;

	CCGAllocatorIFC allocatorIFC;
	CCGAllocatorHDL allocator;
} EHash;

#define EHASH_alloc(eh, nb)			((eh)->allocatorIFC.alloc((eh)->allocator, nb))
#define EHASH_free(eh, ptr)			((eh)->allocatorIFC.free((eh)->allocator, ptr))

#define EHASH_hash(eh, item)	(((unsigned int) (item))%((unsigned int) (eh)->curSize))

static EHash *_ehash_new(int estimatedNumEntries, CCGAllocatorIFC *allocatorIFC, CCGAllocatorHDL allocator) {
	EHash *eh = allocatorIFC->alloc(allocator, sizeof(*eh));
	eh->allocatorIFC = *allocatorIFC;
	eh->allocator = allocator;
	eh->numEntries = 0;
	eh->curSizeIdx = 0;
	while (kHashSizes[eh->curSizeIdx]<estimatedNumEntries)
		eh->curSizeIdx++;
	eh->curSize = kHashSizes[eh->curSizeIdx];
	eh->buckets = EHASH_alloc(eh, eh->curSize*sizeof(*eh->buckets));
	memset(eh->buckets, 0, eh->curSize*sizeof(*eh->buckets));

	return eh;
}
typedef void (*EHEntryFreeFP)(EHEntry *, void *);
static void _ehash_free(EHash *eh, EHEntryFreeFP freeEntry, void *userData) {
	int numBuckets = eh->curSize;

	while (numBuckets--) {
		EHEntry *entry = eh->buckets[numBuckets];

		while (entry) {
			EHEntry *next = entry->next;

			freeEntry(entry, userData);

			entry = next;
		}
	}

	EHASH_free(eh, eh->buckets);
	EHASH_free(eh, eh);
}

static void _ehash_insert(EHash *eh, EHEntry *entry) {
	int numBuckets = eh->curSize;
	int hash = EHASH_hash(eh, entry->key);
	entry->next = eh->buckets[hash];
	eh->buckets[hash] = entry;
	eh->numEntries++;

	if (eh->numEntries > (numBuckets*3)) {
		EHEntry **oldBuckets = eh->buckets;
		eh->curSize = kHashSizes[++eh->curSizeIdx];
		
		eh->buckets = EHASH_alloc(eh, eh->curSize*sizeof(*eh->buckets));
		memset(eh->buckets, 0, eh->curSize*sizeof(*eh->buckets));

		while (numBuckets--) {
			for (entry = oldBuckets[numBuckets]; entry;) {
				EHEntry *next = entry->next;
				
				hash = EHASH_hash(eh, entry->key);
				entry->next = eh->buckets[hash];
				eh->buckets[hash] = entry;
				
				entry = next;
			}
		}

		EHASH_free(eh, oldBuckets);
	}
}

static void *_ehash_lookupWithPrev(EHash *eh, void *key, void ***prevp_r) {
	int hash = EHASH_hash(eh, key);
	EHEntry *entry, **prevp = &eh->buckets[hash];
	
	for (; (entry = *prevp); prevp = &entry->next) {
		if (entry->key==key) {
			*prevp_r = prevp;
			return entry;
		}
	}
	
	return NULL;
}

static void *_ehash_lookup(EHash *eh, void *key) {
	int hash = EHASH_hash(eh, key);
	EHEntry *entry;
	
	for (entry = eh->buckets[hash]; entry; entry = entry->next)
		if (entry->key==key)
			break;
	
	return entry;
}

/**/

typedef struct _EHashIterator {
	EHash *eh;
	int curBucket;
	EHEntry *curEntry;
} EHashIterator;

static EHashIterator *_ehashIterator_new(EHash *eh) {
	EHashIterator *ehi = EHASH_alloc(eh, sizeof(*ehi));
	ehi->eh = eh;
	ehi->curEntry = NULL;
	ehi->curBucket = -1;
	while (!ehi->curEntry) {
		ehi->curBucket++;
		if (ehi->curBucket==ehi->eh->curSize)
			break;
		ehi->curEntry = ehi->eh->buckets[ehi->curBucket];
	}
	return ehi;
}
static void _ehashIterator_free(EHashIterator *ehi) {
	EHASH_free(ehi->eh, ehi);
}

static void *_ehashIterator_getCurrent(EHashIterator *ehi) {
	return ehi->curEntry;
}

static void _ehashIterator_next(EHashIterator *ehi) {
	if (ehi->curEntry) {
        ehi->curEntry = ehi->curEntry->next;
		while (!ehi->curEntry) {
			ehi->curBucket++;
			if (ehi->curBucket==ehi->eh->curSize)
				break;
			ehi->curEntry = ehi->eh->buckets[ehi->curBucket];
		}
	}
}
static int _ehashIterator_isStopped(EHashIterator *ehi) {
	return !ehi->curEntry;
}

/***/

static void *_stdAllocator_alloc(CCGAllocatorHDL a, int numBytes) {
	return malloc(numBytes);
}
static void *_stdAllocator_realloc(CCGAllocatorHDL a, void *ptr, int newSize, int oldSize) {
	return realloc(ptr, newSize);
}
static void _stdAllocator_free(CCGAllocatorHDL a, void *ptr) {
	free(ptr);
}

static CCGAllocatorIFC *_getStandardAllocatorIFC(void) {
	static CCGAllocatorIFC ifc;

	ifc.alloc = _stdAllocator_alloc;
	ifc.realloc = _stdAllocator_realloc;
	ifc.free = _stdAllocator_free;
	ifc.release = NULL;

	return &ifc;
}

/***/

static int _edge_isBoundary(CCGEdge *e);

/***/

enum {
	Vert_eEffected=		(1<<0),
	Vert_eChanged=		(1<<1),
} VertFlags;
enum {
	Edge_eEffected=		(1<<0),
} CCGEdgeFlags;
enum {
	Face_eEffected=		(1<<0),
} FaceFlags;

struct _CCGVert {
	CCGVert		*next;	/* EHData.next */
	CCGVertHDL	vHDL;	/* EHData.key */

	short numEdges, numFaces, flags, pad;

	CCGEdge **edges;
	CCGFace **faces;
//	byte *levelData;
//	byte *userData;
};
#define VERT_getLevelData(v)		((byte*) &(v)[1])

struct _CCGEdge {
	CCGEdge		*next;	/* EHData.next */
	CCGEdgeHDL	eHDL;	/* EHData.key */

	short numFaces, flags;

	CCGVert *v0,*v1;
	CCGFace **faces;

//	byte *levelData;
//	byte *userData;
};
#define EDGE_getLevelData(e)		((byte*) &(e)[1])

struct _CCGFace {
	CCGFace		*next;	/* EHData.next */
	CCGFaceHDL	fHDL;	/* EHData.key */

	short numVerts, flags, pad1, pad2;

//	CCGVert **verts;
//	CCGEdge **edges;
//	byte *centerData;
//	byte **gridData;
//	byte *userData;
};
#define FACE_getVerts(f)		((CCGVert**) &(f)[1])
#define FACE_getEdges(f)		((CCGEdge**) &(FACE_getVerts(f)[(f)->numVerts]))
#define FACE_getCenterData(f)	((byte*) &(FACE_getEdges(f)[(f)->numVerts]))

typedef enum {
	eSyncState_None = 0,
	eSyncState_Vert,
	eSyncState_Edge,
	eSyncState_Face,
	eSyncState_Partial,
} SyncState;

struct _CCGSubSurf {
	EHash *vMap;	/* map of CCGVertHDL -> Vert */
	EHash *eMap;	/* map of CCGEdgeHDL -> Edge */
	EHash *fMap;	/* map of CCGFaceHDL -> Face */

	CCGMeshIFC meshIFC;
	void *meshData;

	CCGAllocatorIFC allocatorIFC;
	CCGAllocatorHDL allocator;

	int subdivLevels;
	int numGrids;
	int allowEdgeCreation;

	void *q, *r;

		// data for age'ing (to debug sync)
	int currentAge;
	int useAgeCounts;
	int vertUserAgeOffset;
	int edgeUserAgeOffset;
	int faceUserAgeOffset;

		// data used during syncing
	SyncState syncState;

	EHash *oldVMap, *oldEMap, *oldFMap;
	int lenTempArrays;
	CCGVert **tempVerts;
	CCGEdge **tempEdges;
};

#define CCGSUBSURF_alloc(ss, nb)			((ss)->allocatorIFC.alloc((ss)->allocator, nb))
#define CCGSUBSURF_realloc(ss, ptr, nb, ob)	((ss)->allocatorIFC.realloc((ss)->allocator, ptr, nb, ob))
#define CCGSUBSURF_free(ss, ptr)			((ss)->allocatorIFC.free((ss)->allocator, ptr))

/***/

static CCGVert *_vert_new(CCGVertHDL vHDL, int levels, int dataSize, CCGSubSurf *ss) {
	CCGVert *v = CCGSUBSURF_alloc(ss, sizeof(CCGVert) + ss->meshIFC.vertDataSize * (ss->subdivLevels+1) + ss->meshIFC.vertUserSize);
	byte *userData;

	v->vHDL = vHDL;
	v->edges = NULL;
	v->faces = NULL;
	v->numEdges = v->numFaces = 0;
	v->flags = 0;

	userData = ccgSubSurf_getVertUserData(ss, v);
	memset(userData, 0, ss->meshIFC.vertUserSize);
	if (ss->useAgeCounts) *((int*) &userData[ss->vertUserAgeOffset]) = ss->currentAge;

	return v;
}
static void _vert_remEdge(CCGVert *v, CCGEdge *e, CCGSubSurf *ss) {
	int i;
	for (i=0; i<v->numEdges; i++) {
		if (v->edges[i]==e) {
			v->edges[i] = v->edges[--v->numEdges];
			break;
		}
	}
}
static void _vert_remFace(CCGVert *v, CCGFace *f, CCGSubSurf *ss) {
	int i;
	for (i=0; i<v->numFaces; i++) {
		if (v->faces[i]==f) {
			v->faces[i] = v->faces[--v->numFaces];
			break;
		}
	}
}
static void _vert_addEdge(CCGVert *v, CCGEdge *e, CCGSubSurf *ss) {
	v->edges = CCGSUBSURF_realloc(ss, v->edges, (v->numEdges+1)*sizeof(*v->edges), v->numEdges*sizeof(*v->edges));
	v->edges[v->numEdges++] = e;
}
static void _vert_addFace(CCGVert *v, CCGFace *f, CCGSubSurf *ss) {
	v->faces = CCGSUBSURF_realloc(ss, v->faces, (v->numFaces+1)*sizeof(*v->faces), v->numFaces*sizeof(*v->faces));
	v->faces[v->numFaces++] = f;
}
static CCGEdge *_vert_findEdgeTo(CCGVert *v, CCGVert *vQ) {
	int i;
	for (i=0; i<v->numEdges; i++) {
		CCGEdge *e = v->edges[v->numEdges-1-i]; // XXX, note reverse
		if (	(e->v0==v && e->v1==vQ) ||
				(e->v1==v && e->v0==vQ))
			return e;
	}
	return 0;
}
static int _vert_isBoundary(CCGVert *v) {
	int i;
	for (i=0; i<v->numEdges; i++)
		if (_edge_isBoundary(v->edges[i]))
			return 1;
	return 0;
}
static int _vert_getEdgeIndex(CCGVert *v, CCGEdge *e) {
	int i;
	for (i=0; v->numEdges; i++)
		if (v->edges[i]==e)
			return i;
	return -1;
}
static int _vert_getFaceIndex(CCGVert *v, CCGFace *f) {
	int i;
	for (i=0; v->numFaces; i++)
		if (v->faces[i]==f)
			return i;
	return -1;
}

static void *_vert_getCo(CCGVert *v, int lvl, int dataSize) {
	return &VERT_getLevelData(v)[lvl*dataSize];
}

static void _vert_free(CCGVert *v, CCGSubSurf *ss) {
	CCGSUBSURF_free(ss, v->edges);
	CCGSUBSURF_free(ss, v->faces);
	CCGSUBSURF_free(ss, v);
}

/***/

static CCGEdge *_edge_new(CCGEdgeHDL eHDL, CCGVert *v0, CCGVert *v1, int levels, int dataSize, CCGSubSurf *ss) {
	CCGEdge *e = CCGSUBSURF_alloc(ss, sizeof(CCGEdge) + ss->meshIFC.vertDataSize *((ss->subdivLevels+1) + (1<<(ss->subdivLevels+1))-1) + ss->meshIFC.edgeUserSize);
	byte *userData;

	e->eHDL = eHDL;
	e->v0 = v0;
	e->v1 = v1;
	e->faces = NULL;
	e->numFaces = 0;
	e->flags = 0;
	_vert_addEdge(v0, e, ss);
	_vert_addEdge(v1, e, ss);

	userData = ccgSubSurf_getEdgeUserData(ss, e);
	memset(userData, 0, ss->meshIFC.edgeUserSize);
	if (ss->useAgeCounts) *((int*) &userData[ss->edgeUserAgeOffset]) = ss->currentAge;

	return e;
}
void _edge_remFace(CCGEdge *e, CCGFace *f, CCGSubSurf *ss) {
	int i;
	for (i=0; i<e->numFaces; i++) {
		if (e->faces[i]==f) {
			e->faces[i] = e->faces[--e->numFaces];
			break;
		}
	}
}
void _edge_addFace(CCGEdge *e, CCGFace *f, CCGSubSurf *ss) {
	e->faces = CCGSUBSURF_realloc(ss, e->faces, (e->numFaces+1)*sizeof(*e->faces), e->numFaces*sizeof(*e->faces));
	e->faces[e->numFaces++] = f;
}
static int _edge_getFaceIndex(CCGEdge *e, CCGFace *f) {
	int i;
	for (i=0; i<e->numFaces; i++)
		if (e->faces[i]==f)
			return i;
	return -1;
}
static int _edge_isBoundary(CCGEdge *e) {
	return e->numFaces<2;
}

static CCGVert *_edge_getOtherVert(CCGEdge *e, CCGVert *vQ) {
	if (vQ==e->v0) {
		return e->v1;
	} else {
		return e->v0;
	}
}

static void *_edge_getCo(CCGEdge *e, int lvl, int x, int dataSize) {
	int levelBase = lvl + (1<<lvl) - 1;
	return &EDGE_getLevelData(e)[dataSize*(levelBase + x)];
}
static void *_edge_getCoVert(CCGEdge *e, CCGVert *v, int lvl, int x, int dataSize) {
	int levelBase = lvl + (1<<lvl) - 1;
	if (v==e->v0) {
		return &EDGE_getLevelData(e)[dataSize*(levelBase + x)];
	} else {
		return &EDGE_getLevelData(e)[dataSize*(levelBase + (1<<lvl) - x)];		
	}
}

static void _edge_free(CCGEdge *e, CCGSubSurf *ss) {
	CCGSUBSURF_free(ss, e->faces);
	CCGSUBSURF_free(ss, e);
}
static void _edge_unlinkMarkAndFree(CCGEdge *e, CCGSubSurf *ss) {
	_vert_remEdge(e->v0, e, ss);
	_vert_remEdge(e->v1, e, ss);
	e->v0->flags |= Vert_eEffected;
	e->v1->flags |= Vert_eEffected;
	_edge_free(e, ss);
}

/***/

static CCGFace *_face_new(CCGFaceHDL fHDL, CCGVert **verts, CCGEdge **edges, int numVerts, int levels, int dataSize, CCGSubSurf *ss) {
	int maxGridSize = 1 + (1<<(ss->subdivLevels-1));
	CCGFace *f = CCGSUBSURF_alloc(ss, sizeof(CCGFace) + sizeof(CCGVert*)*numVerts + sizeof(CCGEdge*)*numVerts + ss->meshIFC.vertDataSize *(1 + numVerts*maxGridSize + numVerts*maxGridSize*maxGridSize) + ss->meshIFC.faceUserSize);
	CCGVert **fVerts = FACE_getVerts(f);
	byte *userData;
	int i;

	f->numVerts = numVerts;
	f->fHDL = fHDL;
	f->flags = 0;

	for (i=0; i<numVerts; i++) {
		FACE_getVerts(f)[i] = verts[i];
		FACE_getEdges(f)[i] = edges[i];
		_vert_addFace(verts[i], f, ss);
		_edge_addFace(edges[i], f, ss);
	}

	userData = ccgSubSurf_getFaceUserData(ss, f);
	memset(userData, 0, ss->meshIFC.faceUserSize);
	if (ss->useAgeCounts) *((int*) &userData[ss->faceUserAgeOffset]) = ss->currentAge;

	return f;
}

static void *_face_getIECo(CCGFace *f, int lvl, int S, int x, int levels, int dataSize) {
	int maxGridSize = 1 + (1<<(levels-1));
	int spacing = 1<<(levels-lvl);
	byte *gridBase = FACE_getCenterData(f) + dataSize*(1 + S*(maxGridSize + maxGridSize*maxGridSize));
	return &gridBase[dataSize*x*spacing];
}
static void *_face_getIFCo(CCGFace *f, int lvl, int S, int x, int y, int levels, int dataSize) {
	int maxGridSize = 1 + (1<<(levels-1));
	int spacing = 1<<(levels-lvl);
	byte *gridBase = FACE_getCenterData(f) + dataSize*(1 + S*(maxGridSize + maxGridSize*maxGridSize));
	return &gridBase[dataSize*(maxGridSize + (y*maxGridSize + x)*spacing)];
}
static int _face_getVertIndex(CCGFace *f, CCGVert *v) {
	int i;
	for (i=0; i<f->numVerts; i++)
		if (FACE_getVerts(f)[i]==v)
			return i;
	return -1;
}
static int _face_getEdgeIndex(CCGFace *f, CCGEdge *e) {
	int i;
	for (i=0; i<f->numVerts; i++)
		if (FACE_getEdges(f)[i]==e)
			return i;
	return -1;
}
static void *_face_getIFCoEdge(CCGFace *f, CCGEdge *e, int lvl, int eX, int eY, int levels, int dataSize) {
	int maxGridSize = 1 + (1<<(levels-1));
	int spacing = 1<<(levels-lvl);
	int S, x, y, cx, cy;

	for (S=0; S<f->numVerts; S++)
		if (FACE_getEdges(f)[S]==e)
			break;

	eX = eX*spacing;
	eY = eY*spacing;
	if (e->v0!=FACE_getVerts(f)[S]) {
		eX = (maxGridSize*2 - 1)-1 - eX;
	}
	y = maxGridSize - 1 - eX;
	x = maxGridSize - 1 - eY;
	if (x<0) {
		S = (S+f->numVerts-1)%f->numVerts;
		cx = y;
		cy = -x;
	} else if (y<0) {
		S = (S+1)%f->numVerts;
		cx = -y;
		cy = x;
	} else {
		cx = x;
		cy = y;
	}
	return _face_getIFCo(f, levels, S, cx, cy, levels, dataSize);
}

static void _face_free(CCGFace *f, CCGSubSurf *ss) {
	CCGSUBSURF_free(ss, f);
}
static void _face_unlinkMarkAndFree(CCGFace *f, CCGSubSurf *ss) {
	int j;
	for (j=0; j<f->numVerts; j++) {
		_vert_remFace(FACE_getVerts(f)[j], f, ss);
		_edge_remFace(FACE_getEdges(f)[j], f, ss);
		FACE_getVerts(f)[j]->flags |= Vert_eEffected;
	}
	_face_free(f, ss);
}

/***/

CCGSubSurf *ccgSubSurf_new(CCGMeshIFC *ifc, CCGMeshHDL meshData, int subdivLevels, CCGAllocatorIFC *allocatorIFC, CCGAllocatorHDL allocator) {
	if (!allocatorIFC) {
		allocatorIFC = _getStandardAllocatorIFC();
		allocator = NULL;
	}

	if (subdivLevels<1) {
		return NULL;
	} else {
		CCGSubSurf *ss = allocatorIFC->alloc(allocator, sizeof(*ss));

		ss->allocatorIFC = *allocatorIFC;
		ss->allocator = allocator;

		ss->vMap = _ehash_new(0, &ss->allocatorIFC, ss->allocator);
		ss->eMap = _ehash_new(0, &ss->allocatorIFC, ss->allocator);
		ss->fMap = _ehash_new(0, &ss->allocatorIFC, ss->allocator);

		ss->meshIFC = *ifc;
		ss->meshData = meshData;

		ss->subdivLevels = subdivLevels;
		ss->numGrids = 0;
		ss->allowEdgeCreation = 0;

		ss->useAgeCounts = 0;
		ss->vertUserAgeOffset = ss->edgeUserAgeOffset = ss->faceUserAgeOffset = 0;

		ss->q = CCGSUBSURF_alloc(ss, ss->meshIFC.vertDataSize);
		ss->r = CCGSUBSURF_alloc(ss, ss->meshIFC.vertDataSize);

		ss->currentAge = 0;

		ss->syncState = eSyncState_None;

		ss->oldVMap = ss->oldEMap = ss->oldFMap = NULL;
		ss->lenTempArrays = 0;
		ss->tempVerts = NULL;
		ss->tempEdges = NULL;	

		return ss;
	}
}

void ccgSubSurf_free(CCGSubSurf *ss) {
	CCGAllocatorIFC allocatorIFC = ss->allocatorIFC;
	CCGAllocatorHDL allocator = ss->allocator;

	if (ss->syncState) {
		_ehash_free(ss->oldFMap, (EHEntryFreeFP) _face_free, ss);
		_ehash_free(ss->oldEMap, (EHEntryFreeFP) _edge_free, ss);
		_ehash_free(ss->oldVMap, (EHEntryFreeFP) _vert_free, ss);

		CCGSUBSURF_free(ss, ss->tempVerts);
		CCGSUBSURF_free(ss, ss->tempEdges);
	}

	CCGSUBSURF_free(ss, ss->r);
	CCGSUBSURF_free(ss, ss->q);

	_ehash_free(ss->fMap, (EHEntryFreeFP) _face_free, ss);
	_ehash_free(ss->eMap, (EHEntryFreeFP) _edge_free, ss);
	_ehash_free(ss->vMap, (EHEntryFreeFP) _vert_free, ss);

	CCGSUBSURF_free(ss, ss);

	if (allocatorIFC.release) {
		allocatorIFC.release(allocator);
	}
}

CCGError ccgSubSurf_setAllowEdgeCreation(CCGSubSurf *ss, int allowEdgeCreation) {
	ss->allowEdgeCreation = !!allowEdgeCreation;

	return eCCGError_None;
}

CCGError ccgSubSurf_setSubdivisionLevels(CCGSubSurf *ss, int subdivisionLevels) {
	if (subdivisionLevels<=0) {
		return eCCGError_InvalidValue;
	} else if (subdivisionLevels!=ss->subdivLevels) {
		ss->numGrids = 0;
		ss->subdivLevels = subdivisionLevels;
		_ehash_free(ss->vMap, (EHEntryFreeFP) _vert_free, ss);
		_ehash_free(ss->eMap, (EHEntryFreeFP) _edge_free, ss);
		_ehash_free(ss->fMap, (EHEntryFreeFP) _face_free, ss);
		ss->vMap = _ehash_new(0, &ss->allocatorIFC, ss->allocator);
		ss->eMap = _ehash_new(0, &ss->allocatorIFC, ss->allocator);
		ss->fMap = _ehash_new(0, &ss->allocatorIFC, ss->allocator);
	}

	return eCCGError_None;
}

CCGError ccgSubSurf_setUseAgeCounts(CCGSubSurf *ss, int useAgeCounts, int vertUserOffset, int edgeUserOffset, int faceUserOffset) {
	if (useAgeCounts) {
		if (	(vertUserOffset+4>ss->meshIFC.vertUserSize) ||
				(edgeUserOffset+4>ss->meshIFC.edgeUserSize) ||
				(faceUserOffset+4>ss->meshIFC.faceUserSize)) {
			return eCCGError_InvalidValue;
		}  else {
			ss->useAgeCounts = 1;
			ss->vertUserAgeOffset = vertUserOffset;
			ss->edgeUserAgeOffset = edgeUserOffset;
			ss->faceUserAgeOffset = faceUserOffset;
		}
	} else {
		ss->useAgeCounts = 0;
		ss->vertUserAgeOffset = ss->edgeUserAgeOffset = ss->faceUserAgeOffset = 0;
	}

	return eCCGError_None;
}

/***/

CCGError ccgSubSurf_initFullSync(CCGSubSurf *ss) {
	if (ss->syncState!=eSyncState_None) {
		return eCCGError_InvalidSyncState;
	}

	ss->currentAge++;

	ss->oldVMap = ss->vMap; 
	ss->oldEMap = ss->eMap; 
	ss->oldFMap = ss->fMap;

	ss->vMap = _ehash_new(ss->oldVMap->numEntries, &ss->allocatorIFC, ss->allocator);
	ss->eMap = _ehash_new(ss->oldFMap->numEntries, &ss->allocatorIFC, ss->allocator);
	ss->fMap = _ehash_new(ss->oldEMap->numEntries, &ss->allocatorIFC, ss->allocator);

	ss->numGrids = 0;

	ss->lenTempArrays = 12;
	ss->tempVerts = CCGSUBSURF_alloc(ss, sizeof(*ss->tempVerts)*ss->lenTempArrays);
	ss->tempEdges = CCGSUBSURF_alloc(ss, sizeof(*ss->tempEdges)*ss->lenTempArrays);

	ss->syncState = eSyncState_Vert;

	return eCCGError_None;
}

CCGError ccgSubSurf_initPartialSync(CCGSubSurf *ss) {
	if (ss->syncState!=eSyncState_None) {
		return eCCGError_InvalidSyncState;
	}

	ss->currentAge++;

	ss->syncState = eSyncState_Partial;

	return eCCGError_None;
}

CCGError ccgSubSurf_syncVertDel(CCGSubSurf *ss, CCGVertHDL vHDL) {
	if (ss->syncState!=eSyncState_Partial) {
		return eCCGError_InvalidSyncState;
	} else {
		CCGVert **prevp, *v = _ehash_lookupWithPrev(ss->vMap, vHDL, &prevp);

		if (!v || v->numFaces || v->numEdges) {
			return eCCGError_InvalidValue;
		} else {
			*prevp = v->next;
			_vert_free(v, ss);
		}
	}

	return eCCGError_None;
}

CCGError ccgSubSurf_syncEdgeDel(CCGSubSurf *ss, CCGEdgeHDL eHDL) {
	if (ss->syncState!=eSyncState_Partial) {
		return eCCGError_InvalidSyncState;
	} else {
		CCGEdge **prevp, *e = _ehash_lookupWithPrev(ss->eMap, eHDL, &prevp);

		if (!e || e->numFaces) {
			return eCCGError_InvalidValue;
		} else {
			*prevp = e->next;
			_edge_unlinkMarkAndFree(e, ss);
		}
	}

	return eCCGError_None;
}

CCGError ccgSubSurf_syncFaceDel(CCGSubSurf *ss, CCGFaceHDL fHDL) {
	if (ss->syncState!=eSyncState_Partial) {
		return eCCGError_InvalidSyncState;
	} else {
		CCGFace **prevp, *f = _ehash_lookupWithPrev(ss->fMap, fHDL, &prevp);

		if (!f) {
			return eCCGError_InvalidValue;
		} else {
			*prevp = f->next;
			_face_unlinkMarkAndFree(f, ss);
		}
	}

	return eCCGError_None;
}

CCGError ccgSubSurf_syncVert(CCGSubSurf *ss, CCGVertHDL vHDL, void *vertData) {
	CCGVert **prevp, *v;
	
	if (ss->syncState==eSyncState_Partial) {
		v = _ehash_lookupWithPrev(ss->vMap, vHDL, &prevp);
		if (!v) {
			v = _vert_new(vHDL, ss->subdivLevels, ss->meshIFC.vertDataSize, ss);
			ss->meshIFC.vertDataCopy(ss->meshData, _vert_getCo(v,0,ss->meshIFC.vertDataSize), vertData);
			_ehash_insert(ss->vMap, (EHEntry*) v);
			v->flags = Vert_eEffected;
		} else if (!ss->meshIFC.vertDataEqual(ss->meshData, vertData, _vert_getCo(v, 0, ss->meshIFC.vertDataSize))) {
			int i, j;

			ss->meshIFC.vertDataCopy(ss->meshData, _vert_getCo(v,0,ss->meshIFC.vertDataSize), vertData);
			v->flags = Vert_eEffected;

			for (i=0; i<v->numEdges; i++) {
				CCGEdge *e = v->edges[i];
				e->v0->flags |= Vert_eEffected;
				e->v1->flags |= Vert_eEffected;
			}
			for (i=0; i<v->numFaces; i++) {
				CCGFace *f = v->faces[i];
				for (j=0; j<f->numVerts; j++) {
					FACE_getVerts(f)[j]->flags |= Vert_eEffected;
				}
			}
		}
	} else {
		if (ss->syncState!=eSyncState_Vert) { 
			return eCCGError_InvalidSyncState;
		}

		v = _ehash_lookupWithPrev(ss->oldVMap, vHDL, &prevp);
		if (!v) {
			v = _vert_new(vHDL, ss->subdivLevels, ss->meshIFC.vertDataSize, ss);
			ss->meshIFC.vertDataCopy(ss->meshData, _vert_getCo(v,0,ss->meshIFC.vertDataSize), vertData);
			_ehash_insert(ss->vMap, (EHEntry*) v);
			v->flags = Vert_eEffected;
		} else if (!ss->meshIFC.vertDataEqual(ss->meshData, vertData, _vert_getCo(v, 0, ss->meshIFC.vertDataSize))) {
			*prevp = v->next;
			_ehash_insert(ss->vMap, (EHEntry*) v);
			ss->meshIFC.vertDataCopy(ss->meshData, _vert_getCo(v,0,ss->meshIFC.vertDataSize), vertData);
			v->flags = Vert_eEffected|Vert_eChanged;
		} else {
			*prevp = v->next;
			_ehash_insert(ss->vMap, (EHEntry*) v);
			v->flags = 0;
		}
	}

	return eCCGError_None;
}

CCGError ccgSubSurf_syncEdge(CCGSubSurf *ss, CCGEdgeHDL eHDL, CCGVertHDL e_vHDL0, CCGVertHDL e_vHDL1) {
	CCGEdge **prevp, *e, *eNew;

	if (ss->syncState==eSyncState_Partial) {
		e = _ehash_lookupWithPrev(ss->eMap, eHDL, &prevp);
		if (!e || ((e->v0->vHDL!=e_vHDL0) || (e->v1->vHDL!=e_vHDL1))) {
			CCGVert *v0 = _ehash_lookup(ss->vMap, e_vHDL0);
			CCGVert *v1 = _ehash_lookup(ss->vMap, e_vHDL1);

			eNew = _edge_new(eHDL, v0, v1, ss->subdivLevels, ss->meshIFC.vertDataSize, ss);

			if (e) {
				*prevp = eNew;
				eNew->next = e->next;

				_edge_unlinkMarkAndFree(e, ss);
			} else {
				_ehash_insert(ss->eMap, (EHEntry*) eNew);
			}

			eNew->v0->flags |= Vert_eEffected;
			eNew->v1->flags |= Vert_eEffected;
		}
	} else {
		if (ss->syncState==eSyncState_Vert) {
			ss->syncState = eSyncState_Edge;
		} else if (ss->syncState!=eSyncState_Edge) {
			return eCCGError_InvalidSyncState;
		}

		e = _ehash_lookupWithPrev(ss->oldEMap, eHDL, &prevp);
		if (!e || ((e->v0->vHDL!=e_vHDL0) || (e->v1->vHDL!=e_vHDL1))) {
			CCGVert *v0 = _ehash_lookup(ss->vMap, e_vHDL0);
			CCGVert *v1 = _ehash_lookup(ss->vMap, e_vHDL1);
			e = _edge_new(eHDL, v0, v1, ss->subdivLevels, ss->meshIFC.vertDataSize, ss);
			_ehash_insert(ss->eMap, (EHEntry*) e);
			e->v0->flags |= Vert_eEffected;
			e->v1->flags |= Vert_eEffected;
		} else {
			*prevp = e->next;
			_ehash_insert(ss->eMap, (EHEntry*) e);
			e->flags = 0;
			if ((e->v0->flags|e->v1->flags)&Vert_eChanged) {
				e->v0->flags |= Vert_eEffected;
				e->v1->flags |= Vert_eEffected;
			}
		}
	}

	return eCCGError_None;
}

CCGError ccgSubSurf_syncFace(CCGSubSurf *ss, CCGFaceHDL fHDL, int numVerts, CCGVertHDL *vHDLs) {
	CCGFace **prevp, *f, *fNew;
	int j, k, topologyChanged = 0;

	if (numVerts>ss->lenTempArrays) {
		int oldLen = ss->lenTempArrays;
		ss->lenTempArrays = (numVerts<ss->lenTempArrays*2)?ss->lenTempArrays*2:numVerts;
		ss->tempVerts = CCGSUBSURF_realloc(ss, ss->tempVerts, sizeof(*ss->tempVerts)*ss->lenTempArrays, sizeof(*ss->tempVerts)*oldLen);
		ss->tempEdges = CCGSUBSURF_realloc(ss, ss->tempEdges, sizeof(*ss->tempEdges)*ss->lenTempArrays, sizeof(*ss->tempEdges)*oldLen);
	}

	if (ss->syncState==eSyncState_Partial) {
		f = _ehash_lookupWithPrev(ss->fMap, fHDL, &prevp);

		for (k=0; k<numVerts; k++) {
			ss->tempVerts[k] = _ehash_lookup(ss->vMap, vHDLs[k]);
		}
		for (k=0; k<numVerts; k++) {
			ss->tempEdges[k] = _vert_findEdgeTo(ss->tempVerts[k], ss->tempVerts[(k+1)%numVerts]);
		}

		if (f) {
			if (	f->numVerts!=numVerts ||
					memcmp(FACE_getVerts(f), ss->tempVerts, sizeof(*ss->tempVerts)*numVerts) ||
					memcmp(FACE_getEdges(f), ss->tempEdges, sizeof(*ss->tempEdges)*numVerts))
				topologyChanged = 1;
		}

		if (!f || topologyChanged) {
			fNew = _face_new(fHDL, ss->tempVerts, ss->tempEdges, numVerts, ss->subdivLevels, ss->meshIFC.vertDataSize, ss);

			if (f) {
				ss->numGrids += numVerts - f->numVerts;

				*prevp = fNew;
				fNew->next = f->next;

				_face_unlinkMarkAndFree(f, ss);
			} else {
				ss->numGrids += numVerts;
				_ehash_insert(ss->fMap, (EHEntry*) fNew);
			}

			for (k=0; k<numVerts; k++)
				FACE_getVerts(fNew)[k]->flags |= Vert_eEffected;
		}
	} else {
		if (ss->syncState==eSyncState_Vert || ss->syncState==eSyncState_Edge) {
			ss->syncState = eSyncState_Face;
		} else if (ss->syncState!=eSyncState_Face) {
			return eCCGError_InvalidSyncState;
		}

		f = _ehash_lookupWithPrev(ss->oldFMap, fHDL, &prevp);

		for (k=0; k<numVerts; k++) {
			ss->tempVerts[k] = _ehash_lookup(ss->vMap, vHDLs[k]);
		}
		for (k=0; k<numVerts; k++) {
			ss->tempEdges[k] = _vert_findEdgeTo(ss->tempVerts[k], ss->tempVerts[(k+1)%numVerts]);

			if (ss->allowEdgeCreation && !ss->tempEdges[k]) {
				CCGEdge *e = ss->tempEdges[k] = _edge_new((CCGEdgeHDL) -1, ss->tempVerts[k], ss->tempVerts[(k+1)%numVerts], ss->subdivLevels, ss->meshIFC.vertDataSize, ss);
				_ehash_insert(ss->eMap, (EHEntry*) e);
				e->v0->flags |= Vert_eEffected;
				e->v1->flags |= Vert_eEffected;
			}
		}

		if (f) {
			if (	f->numVerts!=numVerts ||
					memcmp(FACE_getVerts(f), ss->tempVerts, sizeof(*ss->tempVerts)*numVerts) ||
					memcmp(FACE_getEdges(f), ss->tempEdges, sizeof(*ss->tempEdges)*numVerts))
				topologyChanged = 1;
		}

		if (!f || topologyChanged) {
			f = _face_new(fHDL, ss->tempVerts, ss->tempEdges, numVerts, ss->subdivLevels, ss->meshIFC.vertDataSize, ss);
			_ehash_insert(ss->fMap, (EHEntry*) f);
			ss->numGrids += numVerts;

			for (k=0; k<numVerts; k++)
				FACE_getVerts(f)[k]->flags |= Vert_eEffected;
		} else {
			*prevp = f->next;
			_ehash_insert(ss->fMap, (EHEntry*) f);
			f->flags = 0;
			ss->numGrids += f->numVerts;

			for (j=0; j<f->numVerts; j++) {
				if (FACE_getVerts(f)[j]->flags&Vert_eChanged) {
					for (k=0; k<f->numVerts; k++)
						FACE_getVerts(f)[k]->flags |= Vert_eEffected;
					break;
				}
			}
		}
	}

	return eCCGError_None;
}

static void ccgSubSurf__sync(CCGSubSurf *ss);
CCGError ccgSubSurf_processSync(CCGSubSurf *ss) {
	if (ss->syncState==eSyncState_Partial) {
		ss->syncState = eSyncState_None;

		ccgSubSurf__sync(ss);
	} else if (ss->syncState) {
		_ehash_free(ss->oldFMap, (EHEntryFreeFP) _face_unlinkMarkAndFree, ss);
		_ehash_free(ss->oldEMap, (EHEntryFreeFP) _edge_unlinkMarkAndFree, ss);
		_ehash_free(ss->oldVMap, (EHEntryFreeFP) _vert_free, ss);
		CCGSUBSURF_free(ss, ss->tempEdges);
		CCGSUBSURF_free(ss, ss->tempVerts);

		ss->lenTempArrays = 0;

		ss->oldFMap = ss->oldEMap = ss->oldVMap = NULL;
		ss->tempVerts = NULL;
		ss->tempEdges = NULL;

		ss->syncState = eSyncState_None;

		ccgSubSurf__sync(ss);
	} else {
		return eCCGError_InvalidSyncState;
	}

	return eCCGError_None;
}

CCGError ccgSubSurf_sync2(CCGSubSurf *ss) {
	int numVerts = ss->meshIFC.getNumVerts(ss->meshData);
	int numEdges = ss->meshIFC.getNumEdges(ss->meshData);
	int numFaces = ss->meshIFC.getNumFaces(ss->meshData);
	CCGVertHDL *tmpVertHDLs =  CCGSUBSURF_alloc(ss, sizeof(*tmpVertHDLs)*20);
	void *tempData = CCGSUBSURF_alloc(ss, ss->meshIFC.vertDataSize);
	int i,j;

	ccgSubSurf_initFullSync(ss);

	for (i=0; i<numVerts; i++) {
		CCGVertHDL vHDL = ss->meshIFC.getVert(ss->meshData, i);

		ss->meshIFC.getVertData(ss->meshData, vHDL, tempData);

		ccgSubSurf_syncVert(ss, vHDL, tempData);
	}
	for (i=0; i<numEdges; i++) {
		CCGEdgeHDL eHDL = ss->meshIFC.getEdge(ss->meshData, i);
		CCGVertHDL e_vHDL0 = ss->meshIFC.getEdgeVert0(ss->meshData, eHDL);
		CCGVertHDL e_vHDL1 = ss->meshIFC.getEdgeVert1(ss->meshData, eHDL);

		ccgSubSurf_syncEdge(ss, eHDL, e_vHDL0, e_vHDL1);
	}
	for (i=0; i<numFaces; i++) {
		CCGFaceHDL fHDL = ss->meshIFC.getFace(ss->meshData, i);
		int numVerts = ss->meshIFC.getFaceNumVerts(ss->meshData, fHDL);

		for (j=0; j<numVerts; j++) {
			tmpVertHDLs[j] = ss->meshIFC.getFaceVert(ss->meshData, fHDL, j);
		}

		ccgSubSurf_syncFace(ss, fHDL, numVerts, tmpVertHDLs);
	}

	ccgSubSurf_processSync(ss);

	CCGSUBSURF_free(ss, tmpVertHDLs);
	CCGSUBSURF_free(ss, tempData);

	return eCCGError_None;
}

static void ccgSubSurf__sync(CCGSubSurf *ss) {
	CCGVert **effectedV;
	CCGEdge **effectedE;
	CCGFace **effectedF;
	int numEffectedV, numEffectedE, numEffectedF;
	int subdivLevels = ss->subdivLevels;
	int vertDataSize = ss->meshIFC.vertDataSize;
	int i,ptrIdx,cornerIdx;
	int S,x,y;
	void *q = ss->q, *r = ss->r;
	int curLvl, nextLvl;
	int j;

	effectedV = CCGSUBSURF_alloc(ss, sizeof(*effectedV)*ss->vMap->numEntries);
	effectedE = CCGSUBSURF_alloc(ss, sizeof(*effectedE)*ss->eMap->numEntries);
	effectedF = CCGSUBSURF_alloc(ss, sizeof(*effectedF)*ss->fMap->numEntries);
	numEffectedV = numEffectedE = numEffectedF = 0;
	for (i=0; i<ss->vMap->curSize; i++) {
		CCGVert *v = (CCGVert*) ss->vMap->buckets[i];
		for (; v; v = v->next) {
			if (v->flags&Vert_eEffected) {
				effectedV[numEffectedV++] = v;

				for (j=0; j<v->numEdges; j++) {
					CCGEdge *e = v->edges[j];
					if (!(e->flags&Edge_eEffected)) {
						effectedE[numEffectedE++] = e;
						e->flags |= Edge_eEffected;
					}
				}

				for (j=0; j<v->numFaces; j++) {
					CCGFace *f = v->faces[j];
					if (!(f->flags&Face_eEffected)) {
						effectedF[numEffectedF++] = f;
						f->flags |= Face_eEffected;
					}
				}
			}
		}
	}

#define VERT_getCo(v, lvl)				_vert_getCo(v, lvl, vertDataSize)
#define EDGE_getCo(e, lvl, x)			_edge_getCo(e, lvl, x, vertDataSize)
#define FACE_getIECo(f, lvl, S, x)		_face_getIECo(f, lvl, S, x, subdivLevels, vertDataSize)
#define FACE_getIFCo(f, lvl, S, x, y)	_face_getIFCo(f, lvl, S, x, y, subdivLevels, vertDataSize)
	curLvl = 0;
	nextLvl = curLvl+1;

	for (ptrIdx=0; ptrIdx<numEffectedF; ptrIdx++) {
		CCGFace *f = effectedF[ptrIdx];
		void *co = FACE_getCenterData(f);
		f->flags = 0;
		ss->meshIFC.vertDataZero(ss->meshData, co);
		for (i=0; i<f->numVerts; i++) {
			ss->meshIFC.vertDataAdd(ss->meshData, co, VERT_getCo(FACE_getVerts(f)[i], curLvl));
		}
		ss->meshIFC.vertDataMulN(ss->meshData, co, 1.0f/f->numVerts);
	}
	for (ptrIdx=0; ptrIdx<numEffectedE; ptrIdx++) {
		CCGEdge *e = effectedE[ptrIdx];
		void *co = EDGE_getCo(e, nextLvl, 1);
		e->flags = 0;
		if (_edge_isBoundary(e)) {
			ss->meshIFC.vertDataCopy(ss->meshData, co, VERT_getCo(e->v0, curLvl));
			ss->meshIFC.vertDataAdd(ss->meshData, co, VERT_getCo(e->v1, curLvl));
			ss->meshIFC.vertDataMulN(ss->meshData, co, 0.5f);
		} else {
			int numFaces = 0;
			ss->meshIFC.vertDataCopy(ss->meshData, co, VERT_getCo(e->v0, curLvl));
			ss->meshIFC.vertDataAdd(ss->meshData, co, VERT_getCo(e->v1, curLvl));
			for (i=0; i<e->numFaces; i++) {
				CCGFace *f = e->faces[i];
				ss->meshIFC.vertDataAdd(ss->meshData, co, FACE_getCenterData(f));
				numFaces++;
			}
			ss->meshIFC.vertDataMulN(ss->meshData, co, 1.0f/(2.0f+numFaces));
		}
	}
	for (ptrIdx=0; ptrIdx<numEffectedV; ptrIdx++) {
		CCGVert *v = effectedV[ptrIdx];
		void *co = VERT_getCo(v, curLvl);
		void *nCo = VERT_getCo(v, nextLvl);
		v->flags = 0;

		if (!v->numEdges) {
			ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
		} else if (_vert_isBoundary(v)) {
			int numBoundary = 0;

			ss->meshIFC.vertDataZero(ss->meshData, r);
			for (i=0; i<v->numEdges; i++) {
				CCGEdge *e = v->edges[i];
				if (_edge_isBoundary(e)) {
					ss->meshIFC.vertDataAdd(ss->meshData, r, VERT_getCo(_edge_getOtherVert(e, v), curLvl));
					numBoundary++;
				}
			}
			ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
			ss->meshIFC.vertDataMulN(ss->meshData, nCo, 0.75);
			ss->meshIFC.vertDataMulN(ss->meshData, r, 0.25f/numBoundary);
			ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
		} else {
			int numEdges = 0, numFaces = 0;

			ss->meshIFC.vertDataZero(ss->meshData, q);
			for (i=0; i<v->numFaces; i++) {
				CCGFace *f = v->faces[i];
				ss->meshIFC.vertDataAdd(ss->meshData, q, FACE_getCenterData(f));
				numFaces++;
			}
			ss->meshIFC.vertDataMulN(ss->meshData, q, 1.0f/numFaces);
			ss->meshIFC.vertDataZero(ss->meshData, r);
			for (i=0; i<v->numEdges; i++) {
				CCGEdge *e = v->edges[i];
				ss->meshIFC.vertDataAdd(ss->meshData, r, VERT_getCo(_edge_getOtherVert(e, v), curLvl));
				numEdges++;
			}
			ss->meshIFC.vertDataMulN(ss->meshData, r, 1.0f/numEdges);

			ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
			ss->meshIFC.vertDataMulN(ss->meshData, nCo, numEdges-2.0f);
			ss->meshIFC.vertDataAdd(ss->meshData, nCo, q);
			ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
			ss->meshIFC.vertDataMulN(ss->meshData, nCo, 1.0f/numEdges);
		}
	}

	if (ss->useAgeCounts) {
		for (i=0; i<numEffectedV; i++) {
			CCGVert *v = effectedV[i];
			byte *userData = ccgSubSurf_getVertUserData(ss, v);
			*((int*) &userData[ss->vertUserAgeOffset]) = ss->currentAge;
		}

		for (i=0; i<numEffectedE; i++) {
			CCGEdge *e = effectedE[i];
			byte *userData = ccgSubSurf_getEdgeUserData(ss, e);
			*((int*) &userData[ss->edgeUserAgeOffset]) = ss->currentAge;
		}

		for (i=0; i<numEffectedF; i++) {
			CCGFace *f = effectedF[i];
			byte *userData = ccgSubSurf_getFaceUserData(ss, f);
			*((int*) &userData[ss->faceUserAgeOffset]) = ss->currentAge;
		}
	}

	for (i=0; i<numEffectedE; i++) {
		CCGEdge *e = effectedE[i];
		ss->meshIFC.vertDataCopy(ss->meshData, EDGE_getCo(e, nextLvl, 0), VERT_getCo(e->v0, nextLvl));
		ss->meshIFC.vertDataCopy(ss->meshData, EDGE_getCo(e, nextLvl, 2), VERT_getCo(e->v1, nextLvl));
	}
	for (i=0; i<numEffectedF; i++) {
		CCGFace *f = effectedF[i];
		for (S=0; S<f->numVerts; S++) {
			CCGEdge *e = FACE_getEdges(f)[S];
			CCGEdge *prevE = FACE_getEdges(f)[(S+f->numVerts-1)%f->numVerts];

			ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, 0, 0), FACE_getCenterData(f));
			ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIECo(f, nextLvl, S, 0), FACE_getCenterData(f));
			ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, 1, 1), VERT_getCo(FACE_getVerts(f)[S], nextLvl));
			ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIECo(f, nextLvl, S, 1), EDGE_getCo(FACE_getEdges(f)[S], nextLvl, 1));

			ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, 1, 0), _edge_getCoVert(e, FACE_getVerts(f)[S], nextLvl, 1, vertDataSize));
			ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, 0, 1), _edge_getCoVert(prevE, FACE_getVerts(f)[S], nextLvl, 1, vertDataSize));
		}
	}

	for (curLvl=1; curLvl<subdivLevels; curLvl++) {
		int edgeSize = 1 + (1<<curLvl);
		int gridSize = 1 + (1<<(curLvl-1));
		nextLvl = curLvl+1;

		for (ptrIdx=0; ptrIdx<numEffectedF; ptrIdx++) {
			CCGFace *f = (CCGFace*) effectedF[ptrIdx];

				/* interior face midpoints
				 *  o old interior face points
				 */
			for (S=0; S<f->numVerts; S++) {
				for (y=0; y<gridSize-1; y++) {
					for (x=0; x<gridSize-1; x++) {
						int fx = 1 + 2*x;
						int fy = 1 + 2*y;
						void *co0 = FACE_getIFCo(f, curLvl, S, x+0, y+0);
						void *co1 = FACE_getIFCo(f, curLvl, S, x+1, y+0);
						void *co2 = FACE_getIFCo(f, curLvl, S, x+1, y+1);
						void *co3 = FACE_getIFCo(f, curLvl, S, x+0, y+1);
						void *co = FACE_getIFCo(f, nextLvl, S, fx, fy);

						ss->meshIFC.vertDataAvg4(ss->meshData, co, co0, co1, co2, co3);
					}
				}
			}

				/* interior edge midpoints
				 *  o old interior edge points
				 *  o new interior face midpoints
				 */
			for (S=0; S<f->numVerts; S++) {
				for (x=0; x<gridSize-1; x++) {
					int fx = x*2 + 1;
					void *co0 = FACE_getIECo(f, curLvl, S, x+0);
					void *co1 = FACE_getIECo(f, curLvl, S, x+1);
					void *co2 = FACE_getIFCo(f, nextLvl, (S+1)%f->numVerts, 1, fx);
					void *co3 = FACE_getIFCo(f, nextLvl, S, fx, 1);
					void *co = FACE_getIECo(f, nextLvl, S, fx);
					
					ss->meshIFC.vertDataAvg4(ss->meshData, co, co0, co1, co2, co3);
				}

						/* interior face interior edge midpoints
						 *  o old interior face points
						 *  o new interior face midpoints
						 */

					/* vertical */
				for (x=1; x<gridSize-1; x++) {
					for (y=0; y<gridSize-1; y++) {
						int fx = x*2;
						int fy = y*2+1;
						void *co0 = FACE_getIFCo(f, curLvl, S, x, y+0);
						void *co1 = FACE_getIFCo(f, curLvl, S, x, y+1);
						void *co2 = FACE_getIFCo(f, nextLvl, S, fx-1, fy);
						void *co3 = FACE_getIFCo(f, nextLvl, S, fx+1, fy);
						void *co = FACE_getIFCo(f, nextLvl, S, fx, fy);

						ss->meshIFC.vertDataAvg4(ss->meshData, co, co0, co1, co2, co3);
					}
				}

					/* horizontal */
				for (y=1; y<gridSize-1; y++) {
					for (x=0; x<gridSize-1; x++) {
						int fx = x*2+1;
						int fy = y*2;
						void *co0 = FACE_getIFCo(f, curLvl, S, x+0, y);
						void *co1 = FACE_getIFCo(f, curLvl, S, x+1, y);
						void *co2 = FACE_getIFCo(f, nextLvl, S, fx, fy-1);
						void *co3 = FACE_getIFCo(f, nextLvl, S, fx, fy+1);
						void *co = FACE_getIFCo(f, nextLvl, S, fx, fy);

						ss->meshIFC.vertDataAvg4(ss->meshData, co, co0, co1, co2, co3);
					}
				}
			}
		}

			/* exterior edge midpoints
			 *  o old exterior edge points
			 *  o new interior face midpoints
			 */
		for (ptrIdx=0; ptrIdx<numEffectedE; ptrIdx++) {
			CCGEdge *e = (CCGEdge*) effectedE[ptrIdx];

			if (_edge_isBoundary(e)) {
				for (x=0; x<edgeSize-1; x++) {
					int fx = x*2 + 1;
					void *co0 = EDGE_getCo(e, curLvl, x+0);
					void *co1 = EDGE_getCo(e, curLvl, x+1);
					void *co = EDGE_getCo(e, nextLvl, fx);

					ss->meshIFC.vertDataCopy(ss->meshData, co, co0);
					ss->meshIFC.vertDataAdd(ss->meshData, co, co1);
					ss->meshIFC.vertDataMulN(ss->meshData, co, 0.5);
				}
			} else {
				for (x=0; x<edgeSize-1; x++) {
					int fx = x*2 + 1;
					void *co0 = EDGE_getCo(e, curLvl, x+0);
					void *co1 = EDGE_getCo(e, curLvl, x+1);
					void *co = EDGE_getCo(e, nextLvl, fx);
					int numFaces = 0;

					ss->meshIFC.vertDataCopy(ss->meshData, co, co0);
					ss->meshIFC.vertDataAdd(ss->meshData, co, co1);

					for (i=0; i<e->numFaces; i++) {
						CCGFace *f = e->faces[i];
						ss->meshIFC.vertDataAdd(ss->meshData, co, _face_getIFCoEdge(f, e, nextLvl, fx, 1, subdivLevels, vertDataSize));
						numFaces++;
					}

					ss->meshIFC.vertDataMulN(ss->meshData, co, 1.0f/(2.0f+numFaces));
				}
			}
		}

			/* exterior vertex shift
			 *  o old vertex points (shifting)
			 *  o old exterior edge points
			 *  o new interior face midpoints
			 */
		for (ptrIdx=0; ptrIdx<numEffectedV; ptrIdx++) {
			CCGVert *v = (CCGVert*) effectedV[ptrIdx];
			void *co = VERT_getCo(v, curLvl);
			void *nCo = VERT_getCo(v, nextLvl);

			if (!v->numEdges) {
				ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
			} else if (_vert_isBoundary(v)) {
				int numBoundary = 0;

				ss->meshIFC.vertDataZero(ss->meshData, r);
				for (i=0; i<v->numEdges; i++) {
					CCGEdge *e = v->edges[i];
					if (_edge_isBoundary(e)) {
						ss->meshIFC.vertDataAdd(ss->meshData, r, _edge_getCoVert(e, v, curLvl, 1, vertDataSize));
						numBoundary++;
					}
				}

				ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
				ss->meshIFC.vertDataMulN(ss->meshData, nCo, 0.75);
				ss->meshIFC.vertDataMulN(ss->meshData, r, 0.25f/numBoundary);
				ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
			} else {
				int cornerIdx = (1 + (1<<(curLvl))) - 2;
				int numEdges = 0, numFaces = 0;

				ss->meshIFC.vertDataZero(ss->meshData, q);
				for (i=0; i<v->numFaces; i++) {
					CCGFace *f = v->faces[i];
					ss->meshIFC.vertDataAdd(ss->meshData, q, FACE_getIFCo(f, nextLvl, _face_getVertIndex(f,v), cornerIdx, cornerIdx));
					numFaces++;
				}
				ss->meshIFC.vertDataMulN(ss->meshData, q, 1.0f/numFaces);
				ss->meshIFC.vertDataZero(ss->meshData, r);
				for (i=0; i<v->numEdges; i++) {
					CCGEdge *e = v->edges[i];
					ss->meshIFC.vertDataAdd(ss->meshData, r, _edge_getCoVert(e, v, curLvl, 1,vertDataSize));
					numEdges++;
				}
				ss->meshIFC.vertDataMulN(ss->meshData, r, 1.0f/numEdges);

				ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
				ss->meshIFC.vertDataMulN(ss->meshData, nCo, numEdges-2.0f);
				ss->meshIFC.vertDataAdd(ss->meshData, nCo, q);
				ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
				ss->meshIFC.vertDataMulN(ss->meshData, nCo, 1.0f/numEdges);
			}
		}

			/* exterior edge interior shift
			 *  o old exterior edge midpoints (shifting)
			 *  o old exterior edge midpoints
			 *  o new interior face midpoints
			 */
		for (ptrIdx=0; ptrIdx<numEffectedE; ptrIdx++) {
			CCGEdge *e = (CCGEdge*) effectedE[ptrIdx];

			if (_edge_isBoundary(e)) {
				for (x=1; x<edgeSize-1; x++) {
					int fx = x*2;
					void *co = EDGE_getCo(e, curLvl, x);
					void *nCo = EDGE_getCo(e, nextLvl, fx);
					ss->meshIFC.vertDataCopy(ss->meshData, r, EDGE_getCo(e, curLvl, x-1));
					ss->meshIFC.vertDataAdd(ss->meshData, r, EDGE_getCo(e, curLvl, x+1));
					ss->meshIFC.vertDataMulN(ss->meshData, r, 0.5);
					ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
					ss->meshIFC.vertDataMulN(ss->meshData, nCo, 0.75);
					ss->meshIFC.vertDataMulN(ss->meshData, r, 0.25);
					ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
				}
			} else {
				for (x=1; x<edgeSize-1; x++) {
					int fx = x*2;
					void *co = EDGE_getCo(e, curLvl, x);
					void *nCo = EDGE_getCo(e, nextLvl, fx);
					int numFaces = 0;

					ss->meshIFC.vertDataZero(ss->meshData, q);
					ss->meshIFC.vertDataZero(ss->meshData, r);
					ss->meshIFC.vertDataAdd(ss->meshData, r, EDGE_getCo(e, curLvl, x-1));
					ss->meshIFC.vertDataAdd(ss->meshData, r, EDGE_getCo(e, curLvl, x+1));
					for (i=0; i<e->numFaces; i++) {
						CCGFace *f = e->faces[i];
						ss->meshIFC.vertDataAdd(ss->meshData, q, _face_getIFCoEdge(f, e, nextLvl, fx-1, 1, subdivLevels, vertDataSize));
						ss->meshIFC.vertDataAdd(ss->meshData, q, _face_getIFCoEdge(f, e, nextLvl, fx+1, 1, subdivLevels, vertDataSize));

						ss->meshIFC.vertDataAdd(ss->meshData, r, _face_getIFCoEdge(f, e, curLvl, x, 1, subdivLevels, vertDataSize));
						numFaces++;
					}
					ss->meshIFC.vertDataMulN(ss->meshData, q, 1.0/(numFaces*2.0f));
					ss->meshIFC.vertDataMulN(ss->meshData, r, 1.0/(2.0f + numFaces));

					ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
					ss->meshIFC.vertDataMulN(ss->meshData, nCo, (float) numFaces);
					ss->meshIFC.vertDataAdd(ss->meshData, nCo, q);
					ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
					ss->meshIFC.vertDataMulN(ss->meshData, nCo, 1.0f/(2+numFaces));
				}
			}
		}

		for (ptrIdx=0; ptrIdx<numEffectedF; ptrIdx++) {
			CCGFace *f = (CCGFace*) effectedF[ptrIdx];

				/* interior center point shift
				 *  o old face center point (shifting)
				 *  o old interior edge points
				 *  o new interior face midpoints
				 */
			ss->meshIFC.vertDataZero(ss->meshData, q);
			for (S=0; S<f->numVerts; S++) {
				ss->meshIFC.vertDataAdd(ss->meshData, q, FACE_getIFCo(f, nextLvl, S, 1, 1));
			}
			ss->meshIFC.vertDataMulN(ss->meshData, q, 1.0f/f->numVerts);
			ss->meshIFC.vertDataZero(ss->meshData, r);
			for (S=0; S<f->numVerts; S++) {
				ss->meshIFC.vertDataAdd(ss->meshData, r, FACE_getIECo(f, curLvl, S, 1));
			}
			ss->meshIFC.vertDataMulN(ss->meshData, r, 1.0f/f->numVerts);

			ss->meshIFC.vertDataMulN(ss->meshData, FACE_getCenterData(f), f->numVerts-2.0f);
			ss->meshIFC.vertDataAdd(ss->meshData, FACE_getCenterData(f), q);
			ss->meshIFC.vertDataAdd(ss->meshData, FACE_getCenterData(f), r);
			ss->meshIFC.vertDataMulN(ss->meshData, FACE_getCenterData(f), 1.0f/f->numVerts);

			for (S=0; S<f->numVerts; S++) {
					/* interior face shift
					 *  o old interior face point (shifting)
					 *  o new interior edge midpoints
					 *  o new interior face midpoints
					 */
				for (x=1; x<gridSize-1; x++) {
					for (y=1; y<gridSize-1; y++) {
						int fx = x*2;
						int fy = y*2;
						void *co = FACE_getIFCo(f, curLvl, S, x, y);
						void *nCo = FACE_getIFCo(f, nextLvl, S, fx, fy);
						
						ss->meshIFC.vertDataAvg4(ss->meshData, q, FACE_getIFCo(f, nextLvl, S, fx-1, fy-1),
							FACE_getIFCo(f, nextLvl, S, fx+1, fy-1),
							FACE_getIFCo(f, nextLvl, S, fx+1, fy+1),
							FACE_getIFCo(f, nextLvl, S, fx-1, fy+1));

						ss->meshIFC.vertDataAvg4(ss->meshData, r, FACE_getIFCo(f, nextLvl, S, fx-1, fy+0),
							FACE_getIFCo(f, nextLvl, S, fx+1, fy+0),
							FACE_getIFCo(f, nextLvl, S, fx+0, fy-1),
							FACE_getIFCo(f, nextLvl, S, fx+0, fy+1));

						ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
						ss->meshIFC.vertDataSub(ss->meshData, nCo, q);
						ss->meshIFC.vertDataMulN(ss->meshData, nCo, 0.25f);
						ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
					}
				}

					/* interior edge interior shift
					 *  o old interior edge point (shifting)
					 *  o new interior edge midpoints
					 *  o new interior face midpoints
					 */
				for (x=1; x<gridSize-1; x++) {
					int fx = x*2;
					void *co = FACE_getIECo(f, curLvl, S, x);
					void *nCo = FACE_getIECo(f, nextLvl, S, fx);
					
					ss->meshIFC.vertDataAvg4(ss->meshData, q, FACE_getIFCo(f, nextLvl, (S+1)%f->numVerts, 1, fx-1),
						FACE_getIFCo(f, nextLvl, (S+1)%f->numVerts, 1, fx+1),
						FACE_getIFCo(f, nextLvl, S, fx+1, +1),
						FACE_getIFCo(f, nextLvl, S, fx-1, +1));

					ss->meshIFC.vertDataAvg4(ss->meshData, r, FACE_getIECo(f, nextLvl, S, fx-1),
						FACE_getIECo(f, nextLvl, S, fx+1),
						FACE_getIFCo(f, nextLvl, (S+1)%f->numVerts, 1, fx),
						FACE_getIFCo(f, nextLvl, S, fx, 1));

					ss->meshIFC.vertDataCopy(ss->meshData, nCo, co);
					ss->meshIFC.vertDataSub(ss->meshData, nCo, q);
					ss->meshIFC.vertDataMulN(ss->meshData, nCo, 0.25f);
					ss->meshIFC.vertDataAdd(ss->meshData, nCo, r);
				}
			}
		}



			/* copy down */
		edgeSize = 1 + (1<<(nextLvl));
		gridSize = 1 + (1<<((nextLvl)-1));
		cornerIdx = gridSize-1;
		for (i=0; i<numEffectedE; i++) {
			CCGEdge *e = effectedE[i];
			ss->meshIFC.vertDataCopy(ss->meshData, EDGE_getCo(e, nextLvl, 0), VERT_getCo(e->v0, nextLvl));
			ss->meshIFC.vertDataCopy(ss->meshData, EDGE_getCo(e, nextLvl, edgeSize-1), VERT_getCo(e->v1, nextLvl));
		}
		for (i=0; i<numEffectedF; i++) {
			CCGFace *f = effectedF[i];
			for (S=0; S<f->numVerts; S++) {
				CCGEdge *e = FACE_getEdges(f)[S];
				CCGEdge *prevE = FACE_getEdges(f)[(S+f->numVerts-1)%f->numVerts];

				ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, 0, 0), FACE_getCenterData(f));
				ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIECo(f, nextLvl, S, 0), FACE_getCenterData(f));
				ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, cornerIdx, cornerIdx), VERT_getCo(FACE_getVerts(f)[S], nextLvl));
				ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIECo(f, nextLvl, S, cornerIdx), EDGE_getCo(FACE_getEdges(f)[S], nextLvl, cornerIdx));
				for (x=1; x<gridSize-1; x++) {
					void *co = FACE_getIECo(f, nextLvl, S, x);
					ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, x, 0), co);
					ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, (S+1)%f->numVerts, 0, x), co);
				}
				for (x=0; x<gridSize-1; x++) {
					int eI = gridSize-1-x;
					ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, cornerIdx, x), _edge_getCoVert(e, FACE_getVerts(f)[S], nextLvl, eI,vertDataSize));
					ss->meshIFC.vertDataCopy(ss->meshData, FACE_getIFCo(f, nextLvl, S, x, cornerIdx), _edge_getCoVert(prevE, FACE_getVerts(f)[S], nextLvl, eI,vertDataSize));
				}
			}
		}
	}
#undef VERT_getCo
#undef EDGE_getCo
#undef FACE_getIECo
#undef FACE_getIFCo

	CCGSUBSURF_free(ss, effectedF);
	CCGSUBSURF_free(ss, effectedE);
	CCGSUBSURF_free(ss, effectedV);
}

/*** External API accessor functions ***/

int ccgSubSurf_getNumVerts(CCGSubSurf *ss) {
	return ss->vMap->numEntries;
}
int ccgSubSurf_getNumEdges(CCGSubSurf *ss) {
	return ss->eMap->numEntries;
}
int ccgSubSurf_getNumFaces(CCGSubSurf *ss) {
	return ss->fMap->numEntries;
}

int ccgSubSurf_getSubdivisionLevels(CCGSubSurf *ss) {
	return ss->subdivLevels;
}
int ccgSubSurf_getEdgeSize(CCGSubSurf *ss) {
	return ccgSubSurf_getEdgeLevelSize(ss, ss->subdivLevels);
}
int ccgSubSurf_getEdgeLevelSize(CCGSubSurf *ss, int level) {
	if (level<1 || level>ss->subdivLevels) {
		return -1;
	} else {
		return 1 + (1<<level);
	}
}
int ccgSubSurf_getGridSize(CCGSubSurf *ss) {
	return ccgSubSurf_getGridLevelSize(ss, ss->subdivLevels);
}
int ccgSubSurf_getGridLevelSize(CCGSubSurf *ss, int level) {
	if (level<1 || level>ss->subdivLevels) {
		return -1;
	} else {
		return 1 + (1<<(level-1));
	}
}

/* Vert accessors */

CCGVertHDL ccgSubSurf_getVertVertHandle(CCGSubSurf *ss, CCGVert *v) {
	return v->vHDL;
}
int ccgSubSurf_getVertAge(CCGSubSurf *ss, CCGVert *v) {
	if (ss->useAgeCounts) {
		byte *userData = ccgSubSurf_getVertUserData(ss, v);
		return ss->currentAge - *((int*) &userData[ss->vertUserAgeOffset]);
	} else {
		return 0;
	}
}
void *ccgSubSurf_getVertUserData(CCGSubSurf *ss, CCGVert *v) {
	return VERT_getLevelData(v) + ss->meshIFC.vertDataSize*(ss->subdivLevels+1);
}
int ccgSubSurf_getVertNumFaces(CCGSubSurf *ss, CCGVert *v) {
	return v->numFaces;
}
CCGFace *ccgSubSurf_getVertFace(CCGSubSurf *ss, CCGVert *v, int index) {
	if (index<0 || index>=v->numFaces) {
		return NULL;
	} else {
		return v->faces[index];
	}
}
int ccgSubSurf_getVertNumEdges(CCGSubSurf *ss, CCGVert *v) {
	return v->numEdges;
}
CCGEdge *ccgSubSurf_getVertEdge(CCGSubSurf *ss, CCGVert *v, int index) {
	if (index<0 || index>=v->numEdges) {
		return NULL;
	} else {
		return v->edges[index];
	}
}
void *ccgSubSurf_getVertData(CCGSubSurf *ss, CCGVert *v) {
	return ccgSubSurf_getVertLevelData(ss, v, ss->subdivLevels);
}
void *ccgSubSurf_getVertLevelData(CCGSubSurf *ss, CCGVert *v, int level) {
	if (level<0 || level>ss->subdivLevels) {
		return NULL;
	} else {
		return _vert_getCo(v, level, ss->meshIFC.vertDataSize);
	}
}

/* Edge accessors */

CCGEdgeHDL ccgSubSurf_getEdgeEdgeHandle(CCGSubSurf *ss, CCGEdge *e) {
	return e->eHDL;
}
int ccgSubSurf_getEdgeAge(CCGSubSurf *ss, CCGEdge *e) {
	if (ss->useAgeCounts) {
		byte *userData = ccgSubSurf_getEdgeUserData(ss, e);
		return ss->currentAge - *((int*) &userData[ss->edgeUserAgeOffset]);
	} else {
		return 0;
	}
}
void *ccgSubSurf_getEdgeUserData(CCGSubSurf *ss, CCGEdge *e) {
	return EDGE_getLevelData(e) + ss->meshIFC.vertDataSize *((ss->subdivLevels+1) + (1<<(ss->subdivLevels+1))-1);
}
int ccgSubSurf_getEdgeNumFaces(CCGSubSurf *ss, CCGEdge *e) {
	return e->numFaces;
}
CCGFace *ccgSubSurf_getEdgeFace(CCGSubSurf *ss, CCGEdge *e, int index) {
	if (index<0 || index>=e->numFaces) {
		return NULL;
	} else {
		return e->faces[index];
	}
}
CCGVert *ccgSubSurf_getEdgeVert0(CCGSubSurf *ss, CCGEdge *e) {
	return e->v0;
}
CCGVert *ccgSubSurf_getEdgeVert1(CCGSubSurf *ss, CCGEdge *e) {
	return e->v1;
}
void *ccgSubSurf_getEdgeDataArray(CCGSubSurf *ss, CCGEdge *e) {
	return ccgSubSurf_getEdgeData(ss, e, 0);
}
void *ccgSubSurf_getEdgeData(CCGSubSurf *ss, CCGEdge *e, int x) {
	return ccgSubSurf_getEdgeLevelData(ss, e, x, ss->subdivLevels);
}
void *ccgSubSurf_getEdgeLevelData(CCGSubSurf *ss, CCGEdge *e, int x, int level) {
	if (level<0 || level>ss->subdivLevels) {
		return NULL;
	} else {
		return _edge_getCo(e, level, x, ss->meshIFC.vertDataSize);
	}
}

/* Face accessors */

CCGFaceHDL ccgSubSurf_getFaceFaceHandle(CCGSubSurf *ss, CCGFace *f) {
	return f->fHDL;
}
int ccgSubSurf_getFaceAge(CCGSubSurf *ss, CCGFace *f) {
	if (ss->useAgeCounts) {
		byte *userData = ccgSubSurf_getFaceUserData(ss, f);
		return ss->currentAge - *((int*) &userData[ss->faceUserAgeOffset]);
	} else {
		return 0;
	}
}
void *ccgSubSurf_getFaceUserData(CCGSubSurf *ss, CCGFace *f) {
	int maxGridSize = 1 + (1<<(ss->subdivLevels-1));
	return FACE_getCenterData(f) + ss->meshIFC.vertDataSize *(1 + f->numVerts*maxGridSize + f->numVerts*maxGridSize*maxGridSize);
}
int ccgSubSurf_getFaceNumVerts(CCGSubSurf *ss, CCGFace *f) {
	return f->numVerts;
}
CCGVert *ccgSubSurf_getFaceVert(CCGSubSurf *ss, CCGFace *f, int index) {
	if (index<0 || index>=f->numVerts) {
		return NULL;
	} else {
		return FACE_getVerts(f)[index];
	}
}
CCGEdge *ccgSubSurf_getFaceEdge(CCGSubSurf *ss, CCGFace *f, int index) {
	if (index<0 || index>=f->numVerts) {
		return NULL;
	} else {
		return FACE_getEdges(f)[index];
	}
}
void *ccgSubSurf_getFaceCenterData(CCGSubSurf *ss, CCGFace *f) {
	return FACE_getCenterData(f);
}
void *ccgSubSurf_getFaceGridEdgeDataArray(CCGSubSurf *ss, CCGFace *f, int gridIndex) {
	return ccgSubSurf_getFaceGridEdgeData(ss, f, gridIndex, 0);
}
void *ccgSubSurf_getFaceGridEdgeData(CCGSubSurf *ss, CCGFace *f, int gridIndex, int x) {
	return _face_getIECo(f, ss->subdivLevels, gridIndex, x, ss->subdivLevels, ss->meshIFC.vertDataSize);
}
void *ccgSubSurf_getFaceGridDataArray(CCGSubSurf *ss, CCGFace *f, int gridIndex) {
	return ccgSubSurf_getFaceGridData(ss, f, gridIndex, 0, 0);
}
void *ccgSubSurf_getFaceGridData(CCGSubSurf *ss, CCGFace *f, int gridIndex, int x, int y) {
	return _face_getIFCo(f, ss->subdivLevels, gridIndex, x, y, ss->subdivLevels, ss->meshIFC.vertDataSize);
}

/*** External API iterator functions ***/

typedef struct _CCGVertIterator CCGVertIterator;
typedef struct _CCGEdgeIterator CCGEdgeIterator;
typedef struct _CCGFaceIterator CCGFaceIterator;

CCGVertIterator *ccgSubSurf_getVertIterator(CCGSubSurf *ss) {
	return (CCGVertIterator*) _ehashIterator_new(ss->vMap);
}
CCGEdgeIterator *ccgSubSurf_getEdgeIterator(CCGSubSurf *ss) {
	return (CCGEdgeIterator*) _ehashIterator_new(ss->eMap);
}
CCGFaceIterator *ccgSubSurf_getFaceIterator(CCGSubSurf *ss) {
	return (CCGFaceIterator*) _ehashIterator_new(ss->fMap);
}

CCGVert *ccgVertIterator_getCurrent(CCGVertIterator *vi) {
	return (CCGVert*) _ehashIterator_getCurrent((EHashIterator*) vi);
}
int ccgVertIterator_isStopped(CCGVertIterator *vi) {
	return _ehashIterator_isStopped((EHashIterator*) vi);
}
void ccgVertIterator_next(CCGVertIterator *vi) {
	_ehashIterator_next((EHashIterator*) vi); 
}
void ccgVertIterator_free(CCGVertIterator *vi) {
	_ehashIterator_free((EHashIterator*) vi);
}

CCGEdge *ccgEdgeIterator_getCurrent(CCGEdgeIterator *vi) {
	return (CCGEdge*) _ehashIterator_getCurrent((EHashIterator*) vi);
}
int ccgEdgeIterator_isStopped(CCGEdgeIterator *vi) {
	return _ehashIterator_isStopped((EHashIterator*) vi);
}
void ccgEdgeIterator_next(CCGEdgeIterator *vi) {
	_ehashIterator_next((EHashIterator*) vi); 
}
void ccgEdgeIterator_free(CCGEdgeIterator *vi) {
	_ehashIterator_free((EHashIterator*) vi);
}

CCGFace *ccgFaceIterator_getCurrent(CCGFaceIterator *vi) {
	return (CCGFace*) _ehashIterator_getCurrent((EHashIterator*) vi);
}
int ccgFaceIterator_isStopped(CCGFaceIterator *vi) {
	return _ehashIterator_isStopped((EHashIterator*) vi);
}
void ccgFaceIterator_next(CCGFaceIterator *vi) {
	_ehashIterator_next((EHashIterator*) vi); 
}
void ccgFaceIterator_free(CCGFaceIterator *vi) {
	_ehashIterator_free((EHashIterator*) vi);
}

/*** Extern API final vert/edge/face interface ***/

int ccgSubSurf_getNumFinalVerts(CCGSubSurf *ss) {
	int edgeSize = 1 + (1<<ss->subdivLevels);
	int gridSize = 1 + (1<<(ss->subdivLevels-1));
	int numFinalVerts = ss->vMap->numEntries + ss->eMap->numEntries*(edgeSize-2) + ss->fMap->numEntries + ss->numGrids*((gridSize-2) + ((gridSize-2)*(gridSize-2)));
	return numFinalVerts;
}
int ccgSubSurf_getNumFinalEdges(CCGSubSurf *ss) {
	int edgeSize = 1 + (1<<ss->subdivLevels);
	int gridSize = 1 + (1<<(ss->subdivLevels-1));
	int numFinalEdges = ss->eMap->numEntries*(edgeSize-1) + ss->numGrids*((gridSize-1) + 2*((gridSize-2)*(gridSize-1)));
	return numFinalEdges;
}
int ccgSubSurf_getNumFinalFaces(CCGSubSurf *ss) {
	int gridSize = 1 + (1<<(ss->subdivLevels-1));
	int numFinalFaces = ss->numGrids*((gridSize-1)*(gridSize-1));
	return numFinalFaces;
}

#endif