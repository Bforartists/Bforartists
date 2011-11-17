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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/blenkernel/intern/subsurf_ccg.c
 *  \ingroup bke
 */


#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BLI_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_edgehash.h"
#include "BLI_math.h"
#include "BLI_memarena.h"
#include "BLI_pbvh.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_modifier.h"
#include "BKE_paint.h"
#include "BKE_scene.h"
#include "BKE_subsurf.h"
#include "BKE_tessmesh.h"

#include "PIL_time.h"
#include "BLI_array.h"

#include "GL/glew.h"

#include "GPU_draw.h"
#include "GPU_extensions.h"
#include "GPU_material.h"

#include "CCGSubSurf.h"

extern GLubyte stipple_quarttone[128]; /* glutil.c, bad level data */

static CCGDerivedMesh *getCCGDerivedMesh(CCGSubSurf *ss,
                                         int drawInteriorEdges,
                                         int useSubsurfUv,
                                         DerivedMesh *dm);
static int ccgDM_use_grid_pbvh(CCGDerivedMesh *ccgdm);

///

static void *arena_alloc(CCGAllocatorHDL a, int numBytes) {
	return BLI_memarena_alloc(a, numBytes);
}
static void *arena_realloc(CCGAllocatorHDL a, void *ptr, int newSize, int oldSize) {
	void *p2 = BLI_memarena_alloc(a, newSize);
	if (ptr) {
		memcpy(p2, ptr, oldSize);
	}
	return p2;
}
static void arena_free(CCGAllocatorHDL UNUSED(a), void *UNUSED(ptr)) {
}
static void arena_release(CCGAllocatorHDL a) {
	BLI_memarena_free(a);
}

static CCGSubSurf *_getSubSurf(CCGSubSurf *prevSS, int subdivLevels, int useAging, int useArena, int UNUSED(useFlatSubdiv)) {
	CCGMeshIFC ifc;
	CCGSubSurf *ccgSS;

		/* subdivLevels==0 is not allowed */
	subdivLevels = MAX2(subdivLevels, 1);

	if (prevSS) {
		int oldUseAging;

		useAging = !!useAging;
		ccgSubSurf_getUseAgeCounts(prevSS, &oldUseAging, NULL, NULL, NULL);

		if (oldUseAging!=useAging) {
			ccgSubSurf_free(prevSS);
		} else {
			ccgSubSurf_setSubdivisionLevels(prevSS, subdivLevels);

			return prevSS;
		}
	}

	if (useAging) {
		ifc.vertUserSize = ifc.edgeUserSize = ifc.faceUserSize = 12;
	} else {
		ifc.vertUserSize = ifc.edgeUserSize = ifc.faceUserSize = 8;
	}
	ifc.vertDataSize = sizeof(DMGridData);

	if (useArena) {
		CCGAllocatorIFC allocatorIFC;
		CCGAllocatorHDL allocator = BLI_memarena_new((1<<16), "subsurf arena");

		allocatorIFC.alloc = arena_alloc;
		allocatorIFC.realloc = arena_realloc;
		allocatorIFC.free = arena_free;
		allocatorIFC.release = arena_release;

		ccgSS = ccgSubSurf_new(&ifc, subdivLevels, &allocatorIFC, allocator);
	} else {
		ccgSS = ccgSubSurf_new(&ifc, subdivLevels, NULL, NULL);
	}

	if (useAging) {
		ccgSubSurf_setUseAgeCounts(ccgSS, 1, 8, 8, 8);
	}

	ccgSubSurf_setCalcVertexNormals(ccgSS, 1, offsetof(DMGridData, no));

	return ccgSS;
}

static int getEdgeIndex(CCGSubSurf *ss, CCGEdge *e, int x, int edgeSize) {
	CCGVert *v0 = ccgSubSurf_getEdgeVert0(e);
	CCGVert *v1 = ccgSubSurf_getEdgeVert1(e);
	int v0idx = *((int*) ccgSubSurf_getVertUserData(ss, v0));
	int v1idx = *((int*) ccgSubSurf_getVertUserData(ss, v1));
	int edgeBase = *((int*) ccgSubSurf_getEdgeUserData(ss, e));

	if (x==0) {
		return v0idx;
	} else if (x==edgeSize-1) {
		return v1idx;
	} else {
		return edgeBase + x-1;
	}
}

BM_INLINE int getFaceIndex(CCGSubSurf *ss, CCGFace *f, int S, int x, int y, int edgeSize, int gridSize) {
	int faceBase = *((int*) ccgSubSurf_getFaceUserData(ss, f));
	int numVerts = ccgSubSurf_getFaceNumVerts(f);

	if (x==gridSize-1 && y==gridSize-1) {
		CCGVert *v = ccgSubSurf_getFaceVert(ss, f, S);
		return *((int*) ccgSubSurf_getVertUserData(ss, v));
	} else if (x==gridSize-1) {
		CCGVert *v = ccgSubSurf_getFaceVert(ss, f, S);
		CCGEdge *e = ccgSubSurf_getFaceEdge(ss, f, S);
		int edgeBase = *((int*) ccgSubSurf_getEdgeUserData(ss, e));
		if (v==ccgSubSurf_getEdgeVert0(e)) {
			return edgeBase + (gridSize-1-y)-1;
		} else {
			return edgeBase + (edgeSize-2-1)-((gridSize-1-y)-1);
		}
	} else if (y==gridSize-1) {
		CCGVert *v = ccgSubSurf_getFaceVert(ss, f, S);
		CCGEdge *e = ccgSubSurf_getFaceEdge(ss, f, (S+numVerts-1)%numVerts);
		int edgeBase = *((int*) ccgSubSurf_getEdgeUserData(ss, e));
		if (v==ccgSubSurf_getEdgeVert0(e)) {
			return edgeBase + (gridSize-1-x)-1;
		} else {
			return edgeBase + (edgeSize-2-1)-((gridSize-1-x)-1);
		}
	} else if (x==0 && y==0) {
		return faceBase;
	} else if (x==0) {
		S = (S+numVerts-1)%numVerts;
		return faceBase + 1 + (gridSize-2)*S + (y-1);
	} else if (y==0) {
		return faceBase + 1 + (gridSize-2)*S + (x-1);
	} else {
		return faceBase + 1 + (gridSize-2)*numVerts + S*(gridSize-2)*(gridSize-2) + (y-1)*(gridSize-2) + (x-1);
	}
}

static void get_face_uv_map_vert(UvVertMap *vmap, struct MPoly *mp, struct MLoop *ml, int fi, CCGVertHDL *fverts) {
	UvMapVert *v, *nv;
	int j, nverts= mp->totloop;

	for (j=0; j<nverts; j++) {
		for (nv=v=get_uv_map_vert(vmap, ml[j].v); v; v=v->next) {
			if (v->separate)
				nv= v;
			if (v->f == fi)
				break;
		}

		fverts[j]= SET_INT_IN_POINTER(nv->f*4 + nv->tfindex);
	}
}

static int ss_sync_from_uv(CCGSubSurf *ss, CCGSubSurf *origss, DerivedMesh *dm, MLoopUV *mloopuv) {
	MPoly *mpoly = dm->getPolyArray(dm);
	MLoop *mloop = dm->getLoopArray(dm);
	MVert *mvert = dm->getVertArray(dm);
	int totvert = dm->getNumVerts(dm);
	int totface = dm->getNumFaces(dm);
	int i, j, seam;
	UvMapVert *v;
	UvVertMap *vmap;
	float limit[2];
	CCGVertHDL *fverts= NULL;
	BLI_array_declare(fverts);
	EdgeHash *ehash;
	float creaseFactor = (float)ccgSubSurf_getSubdivisionLevels(ss);

	limit[0]= limit[1]= STD_UV_CONNECT_LIMIT;
	vmap= make_uv_vert_map(mpoly, mloop, mloopuv, totface, totvert, 0, limit);
	if (!vmap)
		return 0;
	
	ccgSubSurf_initFullSync(ss);

	/* create vertices */
	for (i=0; i<totvert; i++) {
		if (!get_uv_map_vert(vmap, i))
			continue;

		for (v=get_uv_map_vert(vmap, i)->next; v; v=v->next)
			if (v->separate)
				break;

		seam = (v != NULL) || ((mvert+i)->flag & ME_VERT_MERGED);

		for (v=get_uv_map_vert(vmap, i); v; v=v->next) {
			if (v->separate) {
				CCGVert *ssv;
				CCGVertHDL vhdl = SET_INT_IN_POINTER(v->f*4 + v->tfindex);
				float uv[3];

				uv[0]= mloopuv[mpoly[v->f].loopstart + v->tfindex].uv[0];
				uv[1]= mloopuv[mpoly[v->f].loopstart + v->tfindex].uv[1];
				uv[2]= 0.0f;

				ccgSubSurf_syncVert(ss, vhdl, uv, seam, &ssv);
			}
		}
	}

	/* create edges */
	ehash = BLI_edgehash_new();

	for (i=0; i<totface; i++) {
		MPoly *mp = &((MPoly*) mpoly)[i];
		int nverts= mp->totloop;
		CCGFace *origf= ccgSubSurf_getFace(origss, SET_INT_IN_POINTER(i));
		/* unsigned int *fv = &mp->v1; */
		MLoop *ml= mloop + mp->loopstart;

		BLI_array_empty(fverts);
		BLI_array_growitems(fverts, nverts);

		get_face_uv_map_vert(vmap, mp, ml, i, fverts);

		for (j=0; j<nverts; j++) {
			int v0 = GET_INT_FROM_POINTER(fverts[j]);
			int v1 = GET_INT_FROM_POINTER(fverts[(j+1)%nverts]);
			MVert *mv0 = mvert + (ml[ j ]. v);
			MVert *mv1 = mvert + (ml[ ((j+1)%nverts) ].v);

			if (!BLI_edgehash_haskey(ehash, v0, v1)) {
				CCGEdge *e, *orige= ccgSubSurf_getFaceEdge(origss, origf, j);
				CCGEdgeHDL ehdl= SET_INT_IN_POINTER(i*4 + j);
				float crease;

				if ((mv0->flag&mv1->flag) & ME_VERT_MERGED)
					crease = creaseFactor;
				else
					crease = ccgSubSurf_getEdgeCrease(orige);

				ccgSubSurf_syncEdge(ss, ehdl, fverts[j], fverts[(j+1)%nverts], crease, &e);
				BLI_edgehash_insert(ehash, v0, v1, NULL);
			}
		}
	}

	BLI_edgehash_free(ehash, NULL);

	/* create faces */
	for (i=0; i<totface; i++) {
		MPoly *mp = &((MPoly*) mpoly)[i];
		MLoop *ml= mloop + mp->loopstart;
		int nverts= mp->totloop;
		CCGFace *f;

		BLI_array_empty(fverts);
		BLI_array_growitems(fverts, nverts);

		get_face_uv_map_vert(vmap, mp, ml, i, fverts);
		ccgSubSurf_syncFace(ss, SET_INT_IN_POINTER(i), nverts, fverts, &f);
	}

	BLI_array_free(fverts);

	free_uv_vert_map(vmap);
	ccgSubSurf_processSync(ss);

	return 1;
}

static void set_subsurf_uv(CCGSubSurf *ss, DerivedMesh *dm, DerivedMesh *result, int n)
{
	CCGSubSurf *uvss;
	CCGFace **faceMap;
	MTFace *tf;
	MLoopUV *mluv;
	CCGFaceIterator *fi;
	int index, gridSize, gridFaces, /*edgeSize,*/ totface, x, y, S;
	MLoopUV *dmloopuv = CustomData_get_layer_n(&dm->loopData, CD_MLOOPUV, n);
	/* need to update both CD_MTFACE & CD_MLOOPUV, hrmf, we could get away with
	 * just tface except applying the modifier then looses subsurf UV */
	MTFace *tface = CustomData_get_layer_n(&result->faceData, CD_MTFACE, n);
	MLoopUV *mloopuv = CustomData_get_layer_n(&result->loopData, CD_MLOOPUV, n);

	if(!dmloopuv || (!tface && !mloopuv))
		return;

	/* create a CCGSubSurf from uv's */
	uvss = _getSubSurf(NULL, ccgSubSurf_getSubdivisionLevels(ss), 0, 1, 0);

	if(!ss_sync_from_uv(uvss, ss, dm, dmloopuv)) {
		ccgSubSurf_free(uvss);
		return;
	}

	/* get some info from CCGSubSurf */
	totface = ccgSubSurf_getNumFaces(uvss);
	/* edgeSize = ccgSubSurf_getEdgeSize(uvss); */ /*UNUSED*/
	gridSize = ccgSubSurf_getGridSize(uvss);
	gridFaces = gridSize - 1;

	/* make a map from original faces to CCGFaces */
	faceMap = MEM_mallocN(totface*sizeof(*faceMap), "facemapuv");

	fi = ccgSubSurf_getFaceIterator(uvss);
	for(; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);
		faceMap[GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(uvss, f))] = f;
	}
	ccgFaceIterator_free(fi);

	/* load coordinates from uvss into tface */
	tf= tface;
	mluv= mloopuv;

	for(index = 0; index < totface; index++) {
		CCGFace *f = faceMap[index];
		int numVerts = ccgSubSurf_getFaceNumVerts(f);

		for (S=0; S<numVerts; S++) {
			DMGridData *faceGridData= ccgSubSurf_getFaceGridDataArray(uvss, f, S);

			for(y = 0; y < gridFaces; y++) {
				for(x = 0; x < gridFaces; x++) {
					float *a = faceGridData[(y + 0)*gridSize + x + 0].co;
					float *b = faceGridData[(y + 0)*gridSize + x + 1].co;
					float *c = faceGridData[(y + 1)*gridSize + x + 1].co;
					float *d = faceGridData[(y + 1)*gridSize + x + 0].co;

					if (tface) {
						tf->uv[0][0] = a[0]; tf->uv[0][1] = a[1];
						tf->uv[1][0] = d[0]; tf->uv[1][1] = d[1];
						tf->uv[2][0] = c[0]; tf->uv[2][1] = c[1];
						tf->uv[3][0] = b[0]; tf->uv[3][1] = b[1];
					}

					if (mloopuv) {
						mluv[0].uv[0] = a[0]; mluv[0].uv[1] = a[1];
						mluv[1].uv[0] = d[0]; mluv[1].uv[1] = d[1];
						mluv[2].uv[0] = c[0]; mluv[2].uv[1] = c[1];
						mluv[3].uv[0] = b[0]; mluv[3].uv[1] = b[1];
					}

					tf++;
					mluv+=4;
				}
			}
		}
	}

	ccgSubSurf_free(uvss);
	MEM_freeN(faceMap);
}

/* face weighting */
typedef struct FaceVertWeightEntry {
	FaceVertWeight *weight;
	float *w;
	int valid;
} FaceVertWeightEntry;

typedef struct WeightTable {
	FaceVertWeightEntry *weight_table;
	int len;
} WeightTable;

static float *get_ss_weights(WeightTable *wtable, int gridCuts, int faceLen)
{
	int x, y, i, j;
	float *w, w1, w2, w4, fac, fac2, fx, fy;

	if (wtable->len <= faceLen) {
		void *tmp = MEM_callocN(sizeof(FaceVertWeightEntry)*(faceLen+1), "weight table alloc 2");
		
		if (wtable->len) {
			memcpy(tmp, wtable->weight_table, sizeof(FaceVertWeightEntry)*wtable->len);
			MEM_freeN(wtable->weight_table);
		}
		
		wtable->weight_table = tmp;
		wtable->len = faceLen+1;
	}

	if (!wtable->weight_table[faceLen].valid) {
		wtable->weight_table[faceLen].valid = 1;
		wtable->weight_table[faceLen].w = w = MEM_callocN(sizeof(float)*faceLen*faceLen*(gridCuts+2)*(gridCuts+2), "weight table alloc");
		fac = 1.0f / (float)faceLen;

		for (i=0; i<faceLen; i++) {
			for (x=0; x<gridCuts+2; x++) {
				for (y=0; y<gridCuts+2; y++) {
					fx = 0.5f - (float)x / (float)(gridCuts+1) / 2.0f;
					fy = 0.5f - (float)y / (float)(gridCuts+1) / 2.0f;
				
					fac2 = faceLen - 4;
					w1 = (1.0f - fx) * (1.0f - fy) + (-fac2*fx*fy*fac);
					w2 = (1.0f - fx + fac2*fx*-fac) * (fy);
					w4 = (fx) * (1.0f - fy + -fac2*fy*fac);
					
					fac2 = 1.0f - (w1+w2+w4);
					fac2 = fac2 / (float)(faceLen-3);
					for (j=0; j<faceLen; j++)
						w[j] = fac2;
					
					w[i] = w1;
					w[(i-1+faceLen)%faceLen] = w2;
					w[(i+1)%faceLen] = w4;

					w += faceLen;
				}
			}
		}
	}

	return wtable->weight_table[faceLen].w;
}

static void free_ss_weights(WeightTable *wtable)
{
	int i;

	for (i=0; i<wtable->len; i++) {
		if (wtable->weight_table[i].valid)
			MEM_freeN(wtable->weight_table[i].w);
	}
	
	if (wtable->weight_table)
		MEM_freeN(wtable->weight_table);
}

#if 0
static DerivedMesh *ss_to_cdderivedmesh(CCGSubSurf *ss, int ssFromEditmesh,
								 int drawInteriorEdges, int useSubsurfUv,
								 DerivedMesh *dm, struct MultiresSubsurf *ms)
{
	DerivedMesh *cgdm, *result;
	double curt = PIL_check_seconds_timer();

	cgdm = getCCGDerivedMesh(ss, drawInteriorEdges, useSubsurfUv, dm);
	result = CDDM_copy(cgdm, 1);

	printf("subsurf conversion time: %.6lf\n", PIL_check_seconds_timer() - curt);

	cgdm->needsFree = 1;
	cgdm->release(cgdm);

	CDDM_calc_normals(result);

	return result;
}
#endif

static int ss_sync_from_derivedmesh(CCGSubSurf *ss, DerivedMesh *dm,
									 float (*vertexCos)[3], int useFlatSubdiv)
{
	float creaseFactor = (float) ccgSubSurf_getSubdivisionLevels(ss);
	CCGVertHDL *fVerts = NULL;
	BLI_array_declare(fVerts);
	MVert *mvert = dm->getVertArray(dm);
	MEdge *medge = dm->getEdgeArray(dm);
	/* MFace *mface = dm->getTessFaceArray(dm); */ /* UNUSED */
	MVert *mv;
	MEdge *me;
	MLoop *mloop = dm->getLoopArray(dm), *ml;
	MPoly *mpoly = dm->getPolyArray(dm), *mp;
	/*MFace *mf;*/ /*UNUSED*/
	int totvert = dm->getNumVerts(dm);
	int totedge = dm->getNumEdges(dm);
	/*int totface = dm->getNumTessFaces(dm);*/ /*UNUSED*/
	/*int totpoly = dm->getNumFaces(dm);*/ /*UNUSED*/
	int i, j;
	int *index;

	ccgSubSurf_initFullSync(ss);

	mv = mvert;
	index = (int *)dm->getVertDataArray(dm, CD_ORIGINDEX);
	for(i = 0; i < totvert; i++, mv++) {
		CCGVert *v;

		if(vertexCos) {
			ccgSubSurf_syncVert(ss, SET_INT_IN_POINTER(i), vertexCos[i], 0, &v);
		} else {
			ccgSubSurf_syncVert(ss, SET_INT_IN_POINTER(i), mv->co, 0, &v);
		}

		((int*)ccgSubSurf_getVertUserData(ss, v))[1] = (index)? *index++: i;
	}

	me = medge;
	index = (int *)dm->getEdgeDataArray(dm, CD_ORIGINDEX);
	for(i = 0; i < totedge; i++, me++) {
		CCGEdge *e;
		float crease;

		crease = useFlatSubdiv ? creaseFactor :
								 me->crease * creaseFactor / 255.0f;

		ccgSubSurf_syncEdge(ss, SET_INT_IN_POINTER(i), SET_INT_IN_POINTER(me->v1),
							SET_INT_IN_POINTER(me->v2), crease, &e);

		((int*)ccgSubSurf_getEdgeUserData(ss, e))[1] = (index)? *index++: i;
	}

	mp = mpoly;
	index = DM_get_face_data_layer(dm, CD_ORIGINDEX);
	for (i=0; i<dm->numPolyData; i++, mp++) {
		CCGFace *f=NULL;

		BLI_array_empty(fVerts);

		ml = mloop + mp->loopstart;
		for (j=0; j<mp->totloop; j++, ml++) {
			BLI_array_append(fVerts, SET_INT_IN_POINTER(ml->v));
		}

		/* this is very bad, means mesh is internally inconsistent.
		 * it is not really possible to continue without modifying
		 * other parts of code significantly to handle missing faces.
		 * since this really shouldn't even be possible we just bail.*/
		if(ccgSubSurf_syncFace(ss, SET_INT_IN_POINTER(i), mp->totloop,
							   fVerts, &f) == eCCGError_InvalidValue) {
			static int hasGivenError = 0;

			if(!hasGivenError) {
				printf("Unrecoverable error in SubSurf calculation,"
					   " mesh is inconsistent.\n");

				hasGivenError = 1;
			}

			return 0;
		}

		((int*)ccgSubSurf_getFaceUserData(ss, f))[1] = index ? *index++: i;
	}

	ccgSubSurf_processSync(ss);

	BLI_array_free(fVerts);
	return 1;
}

/***/

static int ccgDM_getVertMapIndex(CCGSubSurf *ss, CCGVert *v) {
	return ((int*) ccgSubSurf_getVertUserData(ss, v))[1];
}

static int ccgDM_getEdgeMapIndex(CCGSubSurf *ss, CCGEdge *e) {
	return ((int*) ccgSubSurf_getEdgeUserData(ss, e))[1];
}

static int ccgDM_getFaceMapIndex(CCGSubSurf *ss, CCGFace *f) {
	return ((int*) ccgSubSurf_getFaceUserData(ss, f))[1];
}

static void cgdm_getMinMax(DerivedMesh *dm, float min_r[3], float max_r[3]) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGVertIterator *vi = ccgSubSurf_getVertIterator(ss);
	CCGEdgeIterator *ei = ccgSubSurf_getEdgeIterator(ss);
	CCGFaceIterator *fi = ccgSubSurf_getFaceIterator(ss);
	int i, edgeSize = ccgSubSurf_getEdgeSize(ss);
	int gridSize = ccgSubSurf_getGridSize(ss);

	if (!ccgSubSurf_getNumVerts(ss))
		min_r[0] = min_r[1] = min_r[2] = max_r[0] = max_r[1] = max_r[2] = 0.0;

	for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
		CCGVert *v = ccgVertIterator_getCurrent(vi);
		float *co = ccgSubSurf_getVertData(ss, v);

		DO_MINMAX(co, min_r, max_r);
	}

	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);
		DMGridData *edgeData = ccgSubSurf_getEdgeDataArray(ss, e);

		for (i=0; i<edgeSize; i++)
			DO_MINMAX(edgeData[i].co, min_r, max_r);
	}

	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);
		int S, x, y, numVerts = ccgSubSurf_getFaceNumVerts(f);

		for (S=0; S<numVerts; S++) {
			DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);

			for (y=0; y<gridSize; y++)
				for (x=0; x<gridSize; x++)
					DO_MINMAX(faceGridData[y*gridSize + x].co, min_r, max_r);
		}
	}

	ccgFaceIterator_free(fi);
	ccgEdgeIterator_free(ei);
	ccgVertIterator_free(vi);
}
static int cgdm_getNumVerts(DerivedMesh *dm) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;

	return ccgSubSurf_getNumFinalVerts(cgdm->ss);
}
static int cgdm_getNumEdges(DerivedMesh *dm) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;

	return ccgSubSurf_getNumFinalEdges(cgdm->ss);
}
static int cgdm_getNumTessFaces(DerivedMesh *dm) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;

	return ccgSubSurf_getNumFinalFaces(cgdm->ss);
}

static void ccgDM_getFinalVert(DerivedMesh *dm, int vertNum, MVert *mv)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	DMGridData *vd;
	int i;

	memset(mv, 0, sizeof(*mv));

	if((vertNum < cgdm->edgeMap[0].startVert) && (ccgSubSurf_getNumFaces(ss) > 0)) {
		/* this vert comes from face data */
		int lastface = ccgSubSurf_getNumFaces(ss) - 1;
		CCGFace *f;
		int x, y, grid, numVerts;
		int offset;
		int gridSize = ccgSubSurf_getGridSize(ss);
		int gridSideVerts;
		int gridInternalVerts;
		int gridSideEnd;
		int gridInternalEnd;

		i = 0;
		while(i < lastface && vertNum >= cgdm->faceMap[i + 1].startVert)
			++i;

		f = cgdm->faceMap[i].face;
		numVerts = ccgSubSurf_getFaceNumVerts(f);

		gridSideVerts = gridSize - 2;
		gridInternalVerts = gridSideVerts * gridSideVerts;

		gridSideEnd = 1 + numVerts * gridSideVerts;
		gridInternalEnd = gridSideEnd + numVerts * gridInternalVerts;

		offset = vertNum - cgdm->faceMap[i].startVert;
		if(offset < 1) {
			vd = ccgSubSurf_getFaceCenterData(f);
			copy_v3_v3(mv->co, vd->co);
			normal_float_to_short_v3(mv->no, vd->no);
		} else if(offset < gridSideEnd) {
			offset -= 1;
			grid = offset / gridSideVerts;
			x = offset % gridSideVerts + 1;
			vd = ccgSubSurf_getFaceGridEdgeData(ss, f, grid, x);
			copy_v3_v3(mv->co, vd->co);
			normal_float_to_short_v3(mv->no, vd->no);
		} else if(offset < gridInternalEnd) {
			offset -= gridSideEnd;
			grid = offset / gridInternalVerts;
			offset %= gridInternalVerts;
			y = offset / gridSideVerts + 1;
			x = offset % gridSideVerts + 1;
			vd = ccgSubSurf_getFaceGridData(ss, f, grid, x, y);
			copy_v3_v3(mv->co, vd->co);
			normal_float_to_short_v3(mv->no, vd->no);
		}
	} else if((vertNum < cgdm->vertMap[0].startVert) && (ccgSubSurf_getNumEdges(ss) > 0)) {
		/* this vert comes from edge data */
		CCGEdge *e;
		int lastedge = ccgSubSurf_getNumEdges(ss) - 1;
		int x;

		i = 0;
		while(i < lastedge && vertNum >= cgdm->edgeMap[i + 1].startVert)
			++i;

		e = cgdm->edgeMap[i].edge;

		x = vertNum - cgdm->edgeMap[i].startVert + 1;
		vd = ccgSubSurf_getEdgeData(ss, e, x);
		copy_v3_v3(mv->co, vd->co);
		normal_float_to_short_v3(mv->no, vd->no);
	} else {
		/* this vert comes from vert data */
		CCGVert *v;
		i = vertNum - cgdm->vertMap[0].startVert;

		v = cgdm->vertMap[i].vert;
		vd = ccgSubSurf_getVertData(ss, v);
		copy_v3_v3(mv->co, vd->co);
		normal_float_to_short_v3(mv->no, vd->no);
	}
}

static void ccgDM_getFinalVertCo(DerivedMesh *dm, int vertNum, float co_r[3])
{
	MVert mvert;

	ccgDM_getFinalVert(dm, vertNum, &mvert);
	copy_v3_v3(co_r, mvert.co);
}

static void ccgDM_getFinalVertNo(DerivedMesh *dm, int vertNum, float no_r[3])
{
	MVert mvert;

	ccgDM_getFinalVert(dm, vertNum, &mvert);
	normal_short_to_float_v3(no_r, mvert.no);
}

static void ccgDM_getFinalEdge(DerivedMesh *dm, int edgeNum, MEdge *med)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int i;

	memset(med, 0, sizeof(*med));

	if(edgeNum < cgdm->edgeMap[0].startEdge) {
		/* this edge comes from face data */
		int lastface = ccgSubSurf_getNumFaces(ss) - 1;
		CCGFace *f;
		int x, y, grid /*, numVerts*/;
		int offset;
		int gridSize = ccgSubSurf_getGridSize(ss);
		int edgeSize = ccgSubSurf_getEdgeSize(ss);
		int gridSideEdges;
		int gridInternalEdges;
				int lasti, previ;

				i = lastface;
				lasti = 0;
				while (1) {
					previ = i;
					if (cgdm->faceMap[i].startEdge >= edgeNum) {
						i -= fabsf(i-lasti)/2.0f;
					} else if (cgdm->faceMap[i].startEdge < edgeNum) {
						i += fabsf(i-lasti)/2.0f;
					} else {
						break;
					}

					if (i < 0) {
						i = 0;
						break;
					}

					if (i > lastface) {
						i = lastface;
						break;

					}

					if (i == lasti)
					   break;

					lasti = previ;
				}

				i = i > 0 ? i - 1 : i;
		while(i < lastface && edgeNum >= cgdm->faceMap[i + 1].startEdge)
			++i;

		f = cgdm->faceMap[i].face;
		/* numVerts = ccgSubSurf_getFaceNumVerts(f); */ /*UNUSED*/

		gridSideEdges = gridSize - 1;
		gridInternalEdges = (gridSideEdges - 1) * gridSideEdges * 2; 

		offset = edgeNum - cgdm->faceMap[i].startEdge;
		grid = offset / (gridSideEdges + gridInternalEdges);
		offset %= (gridSideEdges + gridInternalEdges);

		if(offset < gridSideEdges) {
			x = offset;
			med->v1 = getFaceIndex(ss, f, grid, x, 0, edgeSize, gridSize);
			med->v2 = getFaceIndex(ss, f, grid, x+1, 0, edgeSize, gridSize);
		} else {
			offset -= gridSideEdges;
			x = (offset / 2) / gridSideEdges + 1;
			y = (offset / 2) % gridSideEdges;
			if(offset % 2 == 0) {
				med->v1 = getFaceIndex(ss, f, grid, x, y, edgeSize, gridSize);
				med->v2 = getFaceIndex(ss, f, grid, x, y+1, edgeSize, gridSize);
			} else {
				med->v1 = getFaceIndex(ss, f, grid, y, x, edgeSize, gridSize);
				med->v2 = getFaceIndex(ss, f, grid, y+1, x, edgeSize, gridSize);
			}
		}
	} else {
		/* this vert comes from edge data */
		CCGEdge *e;
		int edgeSize = ccgSubSurf_getEdgeSize(ss);
		int x;
		short *edgeFlag;
		unsigned int flags = 0;

		i = (edgeNum - cgdm->edgeMap[0].startEdge) / (edgeSize - 1);

		e = cgdm->edgeMap[i].edge;

		if(!ccgSubSurf_getEdgeNumFaces(e)) flags |= ME_LOOSEEDGE;

		x = edgeNum - cgdm->edgeMap[i].startEdge;

		med->v1 = getEdgeIndex(ss, e, x, edgeSize);
		med->v2 = getEdgeIndex(ss, e, x+1, edgeSize);

		edgeFlag = (cgdm->edgeFlags)? &cgdm->edgeFlags[i]: NULL;
		if(edgeFlag)
			flags |= (*edgeFlag & (ME_SEAM | ME_SHARP))
					 | ME_EDGEDRAW | ME_EDGERENDER;
		else
			flags |= ME_EDGEDRAW | ME_EDGERENDER;

		med->flag = flags;
	}
}

static void ccgDM_getFinalFace(DerivedMesh *dm, int faceNum, MFace *mf)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int gridSize = ccgSubSurf_getGridSize(ss);
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	int gridSideEdges = gridSize - 1;
	int gridFaces = gridSideEdges * gridSideEdges;
	int i;
	CCGFace *f;
	/*int numVerts;*/
	int offset;
	int grid;
	int x, y;
	/*int lastface = ccgSubSurf_getNumFaces(ss) - 1;*/ /*UNUSED*/
	char *faceFlags = cgdm->faceFlags;

	memset(mf, 0, sizeof(*mf));
	if (faceNum >= cgdm->dm.numFaceData)
		return;

	i = cgdm->reverseFaceMap[faceNum];

	f = cgdm->faceMap[i].face;
	/*numVerts = ccgSubSurf_getFaceNumVerts(f);*/ /*UNUSED*/

	offset = faceNum - cgdm->faceMap[i].startFace;
	grid = offset / gridFaces;
	offset %= gridFaces;
	y = offset / gridSideEdges;
	x = offset % gridSideEdges;

	mf->v1 = getFaceIndex(ss, f, grid, x+0, y+0, edgeSize, gridSize);
	mf->v2 = getFaceIndex(ss, f, grid, x+0, y+1, edgeSize, gridSize);
	mf->v3 = getFaceIndex(ss, f, grid, x+1, y+1, edgeSize, gridSize);
	mf->v4 = getFaceIndex(ss, f, grid, x+1, y+0, edgeSize, gridSize);

	if(faceFlags) {
		mf->flag = faceFlags[i*2];
		mf->mat_nr = faceFlags[i*2+1];
	}
	else mf->flag = ME_SMOOTH;
}

static void ccgDM_copyFinalVertArray(DerivedMesh *dm, MVert *mvert)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	DMGridData *vd;
	int index;
	int totvert, totedge, totface;
	int gridSize = ccgSubSurf_getGridSize(ss);
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	int i = 0;

	totface = ccgSubSurf_getNumFaces(ss);
	for(index = 0; index < totface; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		int x, y, S, numVerts = ccgSubSurf_getFaceNumVerts(f);

		vd= ccgSubSurf_getFaceCenterData(f);
		copy_v3_v3(mvert[i].co, vd->co);
		normal_float_to_short_v3(mvert[i].no, vd->no);
		i++;
		
		for(S = 0; S < numVerts; S++) {
			for(x = 1; x < gridSize - 1; x++, i++) {
				vd= ccgSubSurf_getFaceGridEdgeData(ss, f, S, x);
				copy_v3_v3(mvert[i].co, vd->co);
				normal_float_to_short_v3(mvert[i].no, vd->no);
			}
		}

		for(S = 0; S < numVerts; S++) {
			for(y = 1; y < gridSize - 1; y++) {
				for(x = 1; x < gridSize - 1; x++, i++) {
					vd= ccgSubSurf_getFaceGridData(ss, f, S, x, y);
					copy_v3_v3(mvert[i].co, vd->co);
					normal_float_to_short_v3(mvert[i].no, vd->no);
				}
			}
		}
	}

	totedge = ccgSubSurf_getNumEdges(ss);
	for(index = 0; index < totedge; index++) {
		CCGEdge *e = cgdm->edgeMap[index].edge;
		int x;

		for(x = 1; x < edgeSize - 1; x++, i++) {
			vd= ccgSubSurf_getEdgeData(ss, e, x);
			copy_v3_v3(mvert[i].co, vd->co);
			/* This gives errors with -debug-fpe
			 * the normals dont seem to be unit length.
			 * this is most likely caused by edges with no
			 * faces which are now zerod out, see comment in:
			 * ccgSubSurf__calcVertNormals(), - campbell */
			normal_float_to_short_v3(mvert[i].no, vd->no);
		}
	}

	totvert = ccgSubSurf_getNumVerts(ss);
	for(index = 0; index < totvert; index++) {
		CCGVert *v = cgdm->vertMap[index].vert;

		vd= ccgSubSurf_getVertData(ss, v);
		copy_v3_v3(mvert[i].co, vd->co);
		normal_float_to_short_v3(mvert[i].no, vd->no);
		i++;
	}
}

static void ccgDM_copyFinalEdgeArray(DerivedMesh *dm, MEdge *medge)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int index;
	int totedge, totface;
	int gridSize = ccgSubSurf_getGridSize(ss);
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	int i = 0;
	short *edgeFlags = cgdm->edgeFlags;

	totface = ccgSubSurf_getNumFaces(ss);
	for(index = 0; index < totface; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		int x, y, S, numVerts = ccgSubSurf_getFaceNumVerts(f);

		for(S = 0; S < numVerts; S++) {
			for(x = 0; x < gridSize - 1; x++) {
				MEdge *med = &medge[i];

				if(cgdm->drawInteriorEdges)
					med->flag = ME_EDGEDRAW | ME_EDGERENDER;
				med->v1 = getFaceIndex(ss, f, S, x, 0, edgeSize, gridSize);
				med->v2 = getFaceIndex(ss, f, S, x + 1, 0, edgeSize, gridSize);
				i++;
			}

			for(x = 1; x < gridSize - 1; x++) {
				for(y = 0; y < gridSize - 1; y++) {
					MEdge *med;

					med = &medge[i];
					if(cgdm->drawInteriorEdges)
						med->flag = ME_EDGEDRAW | ME_EDGERENDER;
					med->v1 = getFaceIndex(ss, f, S, x, y,
										   edgeSize, gridSize);
					med->v2 = getFaceIndex(ss, f, S, x, y + 1,
										   edgeSize, gridSize);
					i++;

					med = &medge[i];
					if(cgdm->drawInteriorEdges)
						med->flag = ME_EDGEDRAW | ME_EDGERENDER;
					med->v1 = getFaceIndex(ss, f, S, y, x,
										   edgeSize, gridSize);
					med->v2 = getFaceIndex(ss, f, S, y + 1, x,
										   edgeSize, gridSize);
					i++;
				}
			}
		}
	}

	totedge = ccgSubSurf_getNumEdges(ss);
	for(index = 0; index < totedge; index++) {
		CCGEdge *e = cgdm->edgeMap[index].edge;
		unsigned int flags = 0;
		int x;
		int edgeIdx = GET_INT_FROM_POINTER(ccgSubSurf_getEdgeEdgeHandle(e));

		if(!ccgSubSurf_getEdgeNumFaces(e)) flags |= ME_LOOSEEDGE;

		if(edgeFlags) {
			if(edgeIdx != -1) {
				flags |= (edgeFlags[index] & (ME_SEAM | ME_SHARP))
						 | ME_EDGEDRAW | ME_EDGERENDER;
			}
		} else {
			flags |= ME_EDGEDRAW | ME_EDGERENDER;
		}

		for(x = 0; x < edgeSize - 1; x++) {
			MEdge *med = &medge[i];
			med->v1 = getEdgeIndex(ss, e, x, edgeSize);
			med->v2 = getEdgeIndex(ss, e, x + 1, edgeSize);
			med->flag = flags;
			i++;
		}
	}
}

static void ccgDM_copyFinalFaceArray(DerivedMesh *dm, MFace *mface)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int index;
	int totface;
	int gridSize = ccgSubSurf_getGridSize(ss);
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	int i = 0;
	char *faceFlags = cgdm->faceFlags;

	totface = ccgSubSurf_getNumFaces(ss);
	for(index = 0; index < totface; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		int x, y, S, numVerts = ccgSubSurf_getFaceNumVerts(f);
		/* keep types in sync with MFace, avoid many conversions */
		char flag = (faceFlags)? faceFlags[index*2]: ME_SMOOTH;
		short mat_nr = (faceFlags)? faceFlags[index*2+1]: 0;

		for(S = 0; S < numVerts; S++) {
			for(y = 0; y < gridSize - 1; y++) {
				for(x = 0; x < gridSize - 1; x++) {
					MFace *mf = &mface[i];
					mf->v1 = getFaceIndex(ss, f, S, x + 0, y + 0,
										  edgeSize, gridSize);
					mf->v2 = getFaceIndex(ss, f, S, x + 0, y + 1,
										  edgeSize, gridSize);
					mf->v3 = getFaceIndex(ss, f, S, x + 1, y + 1,
										  edgeSize, gridSize);
					mf->v4 = getFaceIndex(ss, f, S, x + 1, y + 0,
										  edgeSize, gridSize);
					if (faceFlags) {
						mat_nr = faceFlags[index*2+1];
						mf->flag = faceFlags[index*2];
					} else mf->flag = flag;

					mf->mat_nr = mat_nr;
					mf->flag = flag;

					i++;
				}
			}
		}
	}
}

static void ccgDM_copyFinalLoopArray(DerivedMesh *dm, MLoop *mloop)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int index;
	int totface;
	int gridSize = ccgSubSurf_getGridSize(ss);
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	int i = 0;
	MLoop *mv;
	/* char *faceFlags = cgdm->faceFlags; */ /* UNUSED */

	if (!cgdm->ehash) {
		MEdge *medge;

		cgdm->ehash = BLI_edgehash_new();
		medge = cgdm->dm.getEdgeArray((DerivedMesh*)cgdm);

		for (i=0; i<cgdm->dm.numEdgeData; i++) {
			BLI_edgehash_insert(cgdm->ehash, medge[i].v1, medge[i].v2, SET_INT_IN_POINTER(i));
		}
	}

	totface = ccgSubSurf_getNumFaces(ss);
	mv = mloop;
	for(index = 0; index < totface; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		int x, y, S, numVerts = ccgSubSurf_getFaceNumVerts(f);
		/* int flag = (faceFlags)? faceFlags[index*2]: ME_SMOOTH; */ /* UNUSED */
		/* int mat_nr = (faceFlags)? faceFlags[index*2+1]: 0; */ /* UNUSED */

		for(S = 0; S < numVerts; S++) {
			for(y = 0; y < gridSize - 1; y++) {
				for(x = 0; x < gridSize - 1; x++) {
					int v1, v2, v3, v4;

					v1 = getFaceIndex(ss, f, S, x + 0, y + 0,
										  edgeSize, gridSize);

					v2 = getFaceIndex(ss, f, S, x + 0, y + 1,
										  edgeSize, gridSize);
					v3 = getFaceIndex(ss, f, S, x + 1, y + 1,
										  edgeSize, gridSize);
					v4 = getFaceIndex(ss, f, S, x + 1, y + 0,
										  edgeSize, gridSize);

					mv->v = v1;
					mv->e = GET_INT_FROM_POINTER(BLI_edgehash_lookup(cgdm->ehash, v1, v2));
					mv++, i++;

					mv->v = v2;
					mv->e = GET_INT_FROM_POINTER(BLI_edgehash_lookup(cgdm->ehash, v2, v3));
					mv++, i++;

					mv->v = v3;
					mv->e = GET_INT_FROM_POINTER(BLI_edgehash_lookup(cgdm->ehash, v3, v4));
					mv++, i++;

					mv->v = v4;
					mv->e = GET_INT_FROM_POINTER(BLI_edgehash_lookup(cgdm->ehash, v4, v1));
					mv++, i++;
				}
			}
		}
	}
}


static void ccgDM_copyFinalPolyArray(DerivedMesh *dm, MPoly *mface)
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int index;
	int totface;
	int gridSize = ccgSubSurf_getGridSize(ss);
	/* int edgeSize = ccgSubSurf_getEdgeSize(ss); */ /* UNUSED */
	int i = 0, k = 0;
	char *faceFlags = cgdm->faceFlags;

	totface = ccgSubSurf_getNumFaces(ss);
	for(index = 0; index < totface; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		int x, y, S, numVerts = ccgSubSurf_getFaceNumVerts(f);
		int flag = (faceFlags)? faceFlags[index*2]: ME_SMOOTH;
		int mat_nr = (faceFlags)? faceFlags[index*2+1]: 0;

		for(S = 0; S < numVerts; S++) {
			for(y = 0; y < gridSize - 1; y++) {
				for(x = 0; x < gridSize - 1; x++) {
					MPoly *mf = &mface[i];

					if (faceFlags) {
						mat_nr = faceFlags[index*2+1];
						mf->flag = faceFlags[index*2];
					} else mf->flag = flag;

					mf->mat_nr = mat_nr;
					mf->flag = flag;
					mf->loopstart = k;
					mf->totloop = 4;

					k += 4;
					i++;
				}
			}
		}
	}
}

static void cgdm_getVertCos(DerivedMesh *dm, float (*cos)[3]) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	int gridSize = ccgSubSurf_getGridSize(ss);
	int i;
	CCGVertIterator *vi;
	CCGEdgeIterator *ei;
	CCGFaceIterator *fi;
	CCGFace **faceMap2;
	CCGEdge **edgeMap2;
	CCGVert **vertMap2;
	int index, totvert, totedge, totface;
	
	totvert = ccgSubSurf_getNumVerts(ss);
	vertMap2 = MEM_mallocN(totvert*sizeof(*vertMap2), "vertmap");
	vi = ccgSubSurf_getVertIterator(ss);
	for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
		CCGVert *v = ccgVertIterator_getCurrent(vi);

		vertMap2[GET_INT_FROM_POINTER(ccgSubSurf_getVertVertHandle(v))] = v;
	}
	ccgVertIterator_free(vi);

	totedge = ccgSubSurf_getNumEdges(ss);
	edgeMap2 = MEM_mallocN(totedge*sizeof(*edgeMap2), "edgemap");
	ei = ccgSubSurf_getEdgeIterator(ss);
	for (i=0; !ccgEdgeIterator_isStopped(ei); i++,ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);

		edgeMap2[GET_INT_FROM_POINTER(ccgSubSurf_getEdgeEdgeHandle(e))] = e;
	}

	totface = ccgSubSurf_getNumFaces(ss);
	faceMap2 = MEM_mallocN(totface*sizeof(*faceMap2), "facemap");
	fi = ccgSubSurf_getFaceIterator(ss);
	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);

		faceMap2[GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f))] = f;
	}
	ccgFaceIterator_free(fi);

	i = 0;
	for (index=0; index<totface; index++) {
		CCGFace *f = faceMap2[index];
		int x, y, S, numVerts = ccgSubSurf_getFaceNumVerts(f);

		copy_v3_v3(cos[i++], ccgSubSurf_getFaceCenterData(f));
		
		for (S=0; S<numVerts; S++) {
			for (x=1; x<gridSize-1; x++) {
				copy_v3_v3(cos[i++], ccgSubSurf_getFaceGridEdgeData(ss, f, S, x));
			}
		}

		for (S=0; S<numVerts; S++) {
			for (y=1; y<gridSize-1; y++) {
				for (x=1; x<gridSize-1; x++) {
					copy_v3_v3(cos[i++], ccgSubSurf_getFaceGridData(ss, f, S, x, y));
				}
			}
		}
	}

	for (index=0; index<totedge; index++) {
		CCGEdge *e= edgeMap2[index];
		int x;

		for (x=1; x<edgeSize-1; x++) {
			copy_v3_v3(cos[i++], ccgSubSurf_getEdgeData(ss, e, x));
		}
	}

	for (index=0; index<totvert; index++) {
		CCGVert *v = vertMap2[index];
		copy_v3_v3(cos[i++], ccgSubSurf_getVertData(ss, v));
	}

	MEM_freeN(vertMap2);
	MEM_freeN(edgeMap2);
	MEM_freeN(faceMap2);
}
static void cgdm_foreachMappedVert(DerivedMesh *dm, void (*func)(void *userData, int index, float *co, float *no_f, short *no_s), void *userData) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGVertIterator *vi = ccgSubSurf_getVertIterator(cgdm->ss);

	for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
		CCGVert *v = ccgVertIterator_getCurrent(vi);
		DMGridData *vd = ccgSubSurf_getVertData(cgdm->ss, v);
		int index = ccgDM_getVertMapIndex(cgdm->ss, v);

		if (index!=-1)
			func(userData, index, vd->co, vd->no, NULL);
	}

	ccgVertIterator_free(vi);
}
static void cgdm_foreachMappedEdge(DerivedMesh *dm, void (*func)(void *userData, int index, float *v0co, float *v1co), void *userData) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGEdgeIterator *ei = ccgSubSurf_getEdgeIterator(ss);
	int i, edgeSize = ccgSubSurf_getEdgeSize(ss);

	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);
		DMGridData *edgeData = ccgSubSurf_getEdgeDataArray(ss, e);
		int index = ccgDM_getEdgeMapIndex(ss, e);

		if (index!=-1) {
			for (i=0; i<edgeSize-1; i++)
				func(userData, index, edgeData[i].co, edgeData[i+1].co);
		}
	}

	ccgEdgeIterator_free(ei);
}

static void ccgDM_drawVerts(DerivedMesh *dm) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	int gridSize = ccgSubSurf_getGridSize(ss);
	CCGVertIterator *vi;
	CCGEdgeIterator *ei;
	CCGFaceIterator *fi;

	glBegin(GL_POINTS);
	vi = ccgSubSurf_getVertIterator(ss);
	for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
		CCGVert *v = ccgVertIterator_getCurrent(vi);
		glVertex3fv(ccgSubSurf_getVertData(ss, v));
	}
	ccgVertIterator_free(vi);

	ei = ccgSubSurf_getEdgeIterator(ss);
	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);
		int x;

		for (x=1; x<edgeSize-1; x++)
			glVertex3fv(ccgSubSurf_getEdgeData(ss, e, x));
	}
	ccgEdgeIterator_free(ei);

	fi = ccgSubSurf_getFaceIterator(ss);
	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);
		int x, y, S, numVerts = ccgSubSurf_getFaceNumVerts(f);

		glVertex3fv(ccgSubSurf_getFaceCenterData(f));
		for (S=0; S<numVerts; S++)
			for (x=1; x<gridSize-1; x++)
				glVertex3fv(ccgSubSurf_getFaceGridEdgeData(ss, f, S, x));
		for (S=0; S<numVerts; S++)
			for (y=1; y<gridSize-1; y++)
				for (x=1; x<gridSize-1; x++)
					glVertex3fv(ccgSubSurf_getFaceGridData(ss, f, S, x, y));
	}
	ccgFaceIterator_free(fi);
	glEnd();
}

static void ccgdm_pbvh_update(CCGDerivedMesh *ccgdm)
{
	if(ccgdm->pbvh && ccgDM_use_grid_pbvh(ccgdm)) {
		CCGFace **faces;
		int totface;

		BLI_pbvh_get_grid_updates(ccgdm->pbvh, 1, (void***)&faces, &totface);
		if(totface) {
			ccgSubSurf_updateFromFaces(ccgdm->ss, 0, faces, totface);
			ccgSubSurf_updateNormals(ccgdm->ss, faces, totface);
			MEM_freeN(faces);
		}
	}
}

static void ccgDM_drawEdges(DerivedMesh *dm, int drawLooseEdges, int UNUSED(drawAllEdges)) {
	CCGDerivedMesh *ccgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = ccgdm->ss;
	CCGEdgeIterator *ei = ccgSubSurf_getEdgeIterator(ss);
	CCGFaceIterator *fi = ccgSubSurf_getFaceIterator(ss);
	int i, j, edgeSize = ccgSubSurf_getEdgeSize(ss);
	int totedge = ccgSubSurf_getNumEdges(ss);
	int gridSize = ccgSubSurf_getGridSize(ss);
	int useAging;

	ccgdm_pbvh_update(ccgdm);

	ccgSubSurf_getUseAgeCounts(ss, &useAging, NULL, NULL, NULL);

	for (j=0; j< totedge; j++) {
		CCGEdge *e = ccgdm->edgeMap[j].edge;
		DMGridData *edgeData = ccgSubSurf_getEdgeDataArray(ss, e);

		if (!drawLooseEdges && !ccgSubSurf_getEdgeNumFaces(e))
			continue;

		if(ccgdm->edgeFlags && !(ccgdm->edgeFlags[j] & ME_EDGEDRAW))
			continue;

		if (useAging && !(G.f&G_BACKBUFSEL)) {
			int ageCol = 255-ccgSubSurf_getEdgeAge(ss, e)*4;
			glColor3ub(0, ageCol>0?ageCol:0, 0);
		}

		glBegin(GL_LINE_STRIP);
		for (i=0; i<edgeSize-1; i++) {
			glVertex3fv(edgeData[i].co);
			glVertex3fv(edgeData[i+1].co);
		}
		glEnd();
	}

	if (useAging && !(G.f&G_BACKBUFSEL)) {
		glColor3ub(0, 0, 0);
	}

	if (ccgdm->drawInteriorEdges) {
		for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
			CCGFace *f = ccgFaceIterator_getCurrent(fi);
			int S, x, y, numVerts = ccgSubSurf_getFaceNumVerts(f);

			for (S=0; S<numVerts; S++) {
				DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);

				glBegin(GL_LINE_STRIP);
				for (x=0; x<gridSize; x++)
					glVertex3fv(faceGridData[x].co);
				glEnd();
				for (y=1; y<gridSize-1; y++) {
					glBegin(GL_LINE_STRIP);
					for (x=0; x<gridSize; x++)
						glVertex3fv(faceGridData[y*gridSize + x].co);
					glEnd();
				}
				for (x=1; x<gridSize-1; x++) {
					glBegin(GL_LINE_STRIP);
					for (y=0; y<gridSize; y++)
						glVertex3fv(faceGridData[y*gridSize + x].co);
					glEnd();
				}
			}
		}
	}

	ccgFaceIterator_free(fi);
	ccgEdgeIterator_free(ei);
}
static void ccgDM_drawLooseEdges(DerivedMesh *dm) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGEdgeIterator *ei = ccgSubSurf_getEdgeIterator(ss);
	int i, edgeSize = ccgSubSurf_getEdgeSize(ss);

	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);
		DMGridData *edgeData = ccgSubSurf_getEdgeDataArray(ss, e);

		if (!ccgSubSurf_getEdgeNumFaces(e)) {
			glBegin(GL_LINE_STRIP);
			for (i=0; i<edgeSize-1; i++) {
				glVertex3fv(edgeData[i].co);
				glVertex3fv(edgeData[i+1].co);
			}
			glEnd();
		}
	}

	ccgEdgeIterator_free(ei);
}

static void ccgDM_glNormalFast(float *a, float *b, float *c, float *d)
{
	float a_cX = c[0]-a[0], a_cY = c[1]-a[1], a_cZ = c[2]-a[2];
	float b_dX = d[0]-b[0], b_dY = d[1]-b[1], b_dZ = d[2]-b[2];
	float no[3];

	no[0] = b_dY*a_cZ - b_dZ*a_cY;
	no[1] = b_dZ*a_cX - b_dX*a_cZ;
	no[2] = b_dX*a_cY - b_dY*a_cX;

	/* don't normalize, GL_NORMALIZE is enabled */
	glNormal3fv(no);
}

	/* Only used by non-editmesh types */
static void ccgDM_drawFacesSolid(DerivedMesh *dm, float (*partial_redraw_planes)[4], int fast, int (*setMaterial)(int, void *attribs)) {
	CCGDerivedMesh *ccgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = ccgdm->ss;
	CCGFaceIterator *fi;
	int gridSize = ccgSubSurf_getGridSize(ss);
	char *faceFlags = ccgdm->faceFlags;
	int step = (fast)? gridSize-1: 1;

	ccgdm_pbvh_update(ccgdm);

	if(ccgdm->pbvh && ccgdm->multires.mmd && !fast) {
		if(dm->numFaceData) {
			/* should be per face */
			if(!setMaterial(faceFlags[1]+1, NULL))
				return;

			glShadeModel((faceFlags[0] & ME_SMOOTH)? GL_SMOOTH: GL_FLAT);
			BLI_pbvh_draw(ccgdm->pbvh, partial_redraw_planes, NULL, (faceFlags[0] & ME_SMOOTH));
			glShadeModel(GL_FLAT);
		}

		return;
	}

	fi = ccgSubSurf_getFaceIterator(ss);
	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);
		int S, x, y, numVerts = ccgSubSurf_getFaceNumVerts(f);
		int index = GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f));
		int drawSmooth, mat_nr;

		if(faceFlags) {
			drawSmooth = (faceFlags[index*2] & ME_SMOOTH);
			mat_nr= faceFlags[index*2 + 1];
		}
		else {
			drawSmooth = 1;
			mat_nr= 0;
		}
		
		if (!setMaterial(mat_nr+1, NULL))
			continue;

		glShadeModel(drawSmooth? GL_SMOOTH: GL_FLAT);
		for (S=0; S<numVerts; S++) {
			DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);

			if (drawSmooth) {
				for (y=0; y<gridSize-1; y+=step) {
					glBegin(GL_QUAD_STRIP);
					for (x=0; x<gridSize; x+=step) {
						DMGridData *a = &faceGridData[(y+0)*gridSize + x];
						DMGridData *b = &faceGridData[(y+step)*gridSize + x];

						glNormal3fv(a->no);
						glVertex3fv(a->co);
						glNormal3fv(b->no);
						glVertex3fv(b->co);
					}
					glEnd();
				}
			} else {
				glBegin(GL_QUADS);
				for (y=0; y<gridSize-1; y+=step) {
					for (x=0; x<gridSize-1; x+=step) {
						float *a = faceGridData[(y+0)*gridSize + x].co;
						float *b = faceGridData[(y+0)*gridSize + x + step].co;
						float *c = faceGridData[(y+step)*gridSize + x + step].co;
						float *d = faceGridData[(y+step)*gridSize + x].co;

						ccgDM_glNormalFast(a, b, c, d);

						glVertex3fv(d);
						glVertex3fv(c);
						glVertex3fv(b);
						glVertex3fv(a);
					}
				}
				glEnd();
			}
		}
	}

	ccgFaceIterator_free(fi);
}

	/* Only used by non-editmesh types */
static void cgdm_drawMappedFacesGLSL(DerivedMesh *dm, int (*setMaterial)(int, void *attribs), int (*setDrawOptions)(void *userData, int index), void *userData) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGFaceIterator *fi = ccgSubSurf_getFaceIterator(ss);
	GPUVertexAttribs gattribs;
	DMVertexAttribs attribs= {{{NULL}}};
	/* MTFace *tf = dm->getTessFaceDataArray(dm, CD_MTFACE); */ /* UNUSED */
	int gridSize = ccgSubSurf_getGridSize(ss);
	int gridFaces = gridSize - 1;
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	char *faceFlags = cgdm->faceFlags;
	int a, b, i, doDraw, numVerts, matnr, new_matnr, totface;

	ccgdm_pbvh_update(cgdm);

	doDraw = 0;
	matnr = -1;

#define PASSATTRIB(dx, dy, vert) {												\
	if(attribs.totorco) {														\
		index = getFaceIndex(ss, f, S, x+dx, y+dy, edgeSize, gridSize); 		\
		glVertexAttrib3fvARB(attribs.orco.glIndex, attribs.orco.array[index]);	\
	}																			\
	for(b = 0; b < attribs.tottface; b++) {										\
		MTFace *tf = &attribs.tface[b].array[a];								\
		glVertexAttrib2fvARB(attribs.tface[b].glIndex, tf->uv[vert]);			\
	}																			\
	for(b = 0; b < attribs.totmcol; b++) {										\
		MCol *cp = &attribs.mcol[b].array[a*4 + vert];							\
		GLubyte col[4];															\
		col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;				\
		glVertexAttrib4ubvARB(attribs.mcol[b].glIndex, col);					\
	}																			\
	if(attribs.tottang) {														\
		float *tang = attribs.tang.array[a*4 + vert];							\
		glVertexAttrib4fvARB(attribs.tang.glIndex, tang);						\
	}																			\
}

	totface = ccgSubSurf_getNumFaces(ss);
	for(a = 0, i = 0; i < totface; i++) {
		CCGFace *f = cgdm->faceMap[i].face;
		int S, x, y, drawSmooth;
		int index = GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f));
		int origIndex = ccgDM_getFaceMapIndex(ss, f);
		
		numVerts = ccgSubSurf_getFaceNumVerts(f);

		if(faceFlags) {
			drawSmooth = (faceFlags[index*2] & ME_SMOOTH);
			new_matnr= faceFlags[index*2 + 1] + 1;
		}
		else {
			drawSmooth = 1;
			new_matnr= 1;
		}

		if(new_matnr != matnr) {
			doDraw = setMaterial(matnr = new_matnr, &gattribs);
			if(doDraw)
				DM_vertex_attributes_from_gpu(dm, &gattribs, &attribs);
		}

		if(!doDraw || (setDrawOptions && (origIndex != ORIGINDEX_NONE) && !setDrawOptions(userData, origIndex))) {
			a += gridFaces*gridFaces*numVerts;
			continue;
		}

		glShadeModel(drawSmooth? GL_SMOOTH: GL_FLAT);
		for (S=0; S<numVerts; S++) {
			DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);
			DMGridData *vda, *vdb;

			if (drawSmooth) {
				for (y=0; y<gridFaces; y++) {
					glBegin(GL_QUAD_STRIP);
					for (x=0; x<gridFaces; x++) {
						vda = &faceGridData[(y+0)*gridSize + x];
						vdb = &faceGridData[(y+1)*gridSize + x];
						
						PASSATTRIB(0, 0, 0);
						glNormal3fv(vda->no);
						glVertex3fv(vda->co);

						PASSATTRIB(0, 1, 1);
						glNormal3fv(vdb->no);
						glVertex3fv(vdb->co);

						if(x != gridFaces-1)
							a++;
					}

					vda = &faceGridData[(y+0)*gridSize + x];
					vdb = &faceGridData[(y+1)*gridSize + x];

					PASSATTRIB(0, 0, 3);
					glNormal3fv(vda->no);
					glVertex3fv(vda->co);

					PASSATTRIB(0, 1, 2);
					glNormal3fv(vdb->no);
					glVertex3fv(vdb->co);

					glEnd();

					a++;
				}
			} else {
				glBegin(GL_QUADS);
				for (y=0; y<gridFaces; y++) {
					for (x=0; x<gridFaces; x++) {
						float *aco = faceGridData[(y+0)*gridSize + x].co;
						float *bco = faceGridData[(y+0)*gridSize + x + 1].co;
						float *cco = faceGridData[(y+1)*gridSize + x + 1].co;
						float *dco = faceGridData[(y+1)*gridSize + x].co;

						ccgDM_glNormalFast(aco, bco, cco, dco);

						PASSATTRIB(0, 1, 1);
						glVertex3fv(dco);
						PASSATTRIB(1, 1, 2);
						glVertex3fv(cco);
						PASSATTRIB(1, 0, 3);
						glVertex3fv(bco);
						PASSATTRIB(0, 0, 0);
						glVertex3fv(aco);
						
						a++;
					}
				}
				glEnd();
			}
		}
	}

#undef PASSATTRIB

	ccgFaceIterator_free(fi);
}

static void cgdm_drawFacesGLSL(DerivedMesh *dm, int (*setMaterial)(int, void *attribs)) {
	dm->drawMappedFacesGLSL(dm, setMaterial, NULL, NULL);
}

	/* Only used by non-editmesh types */
static void cgdm_drawMappedFacesMat(DerivedMesh *dm, void (*setMaterial)(void *userData, int, void *attribs), int (*setFace)(void *userData, int index), void *userData) {
	CCGDerivedMesh *ccgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = ccgdm->ss;
	CCGFaceIterator *fi = ccgSubSurf_getFaceIterator(ss);
	GPUVertexAttribs gattribs;
	DMVertexAttribs attribs= {{{NULL}}};
	int gridSize = ccgSubSurf_getGridSize(ss);
	int gridFaces = gridSize - 1;
	int edgeSize = ccgSubSurf_getEdgeSize(ss);
	char *faceFlags = ccgdm->faceFlags;
	int a, b, i, numVerts, matnr, new_matnr, totface;

	ccgdm_pbvh_update(ccgdm);

	matnr = -1;

#define PASSATTRIB(dx, dy, vert) {												\
	if(attribs.totorco) {														\
		index = getFaceIndex(ss, f, S, x+dx, y+dy, edgeSize, gridSize); 		\
		if(attribs.orco.glTexco)												\
			glTexCoord3fv(attribs.orco.array[index]);							\
		else																	\
			glVertexAttrib3fvARB(attribs.orco.glIndex, attribs.orco.array[index]);	\
	}																			\
	for(b = 0; b < attribs.tottface; b++) {										\
		MTFace *tf = &attribs.tface[b].array[a];								\
		if(attribs.tface[b].glTexco)											\
			glTexCoord2fv(tf->uv[vert]);										\
		else																	\
			glVertexAttrib2fvARB(attribs.tface[b].glIndex, tf->uv[vert]);		\
	}																			\
	for(b = 0; b < attribs.totmcol; b++) {										\
		MCol *cp = &attribs.mcol[b].array[a*4 + vert];							\
		GLubyte col[4];															\
		col[0]= cp->b; col[1]= cp->g; col[2]= cp->r; col[3]= cp->a;				\
		glVertexAttrib4ubvARB(attribs.mcol[b].glIndex, col);					\
	}																			\
	if(attribs.tottang) {														\
		float *tang = attribs.tang.array[a*4 + vert];							\
		glVertexAttrib4fvARB(attribs.tang.glIndex, tang);						\
	}																			\
}

	totface = ccgSubSurf_getNumFaces(ss);
	for(a = 0, i = 0; i < totface; i++) {
		CCGFace *f = ccgdm->faceMap[i].face;
		int S, x, y, drawSmooth;
		int index = GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f));
		int origIndex = ccgDM_getFaceMapIndex(ss, f);
		
		numVerts = ccgSubSurf_getFaceNumVerts(f);

		/* get flags */
		if(faceFlags) {
			drawSmooth = (faceFlags[index*2] & ME_SMOOTH);
			new_matnr= faceFlags[index*2 + 1] + 1;
		}
		else {
			drawSmooth = 1;
			new_matnr= 1;
		}

		/* material */
		if(new_matnr != matnr) {
			setMaterial(userData, matnr = new_matnr, &gattribs);
			DM_vertex_attributes_from_gpu(dm, &gattribs, &attribs);
		}

		/* face hiding */
		if((setFace && (origIndex != ORIGINDEX_NONE) && !setFace(userData, origIndex))) {
			a += gridFaces*gridFaces*numVerts;
			continue;
		}

		/* draw face*/
		glShadeModel(drawSmooth? GL_SMOOTH: GL_FLAT);
		for (S=0; S<numVerts; S++) {
			DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);
			DMGridData *vda, *vdb;

			if (drawSmooth) {
				for (y=0; y<gridFaces; y++) {
					glBegin(GL_QUAD_STRIP);
					for (x=0; x<gridFaces; x++) {
						vda = &faceGridData[(y+0)*gridSize + x];
						vdb = &faceGridData[(y+1)*gridSize + x];
						
						PASSATTRIB(0, 0, 0);
						glNormal3fv(vda->no);
						glVertex3fv(vda->co);

						PASSATTRIB(0, 1, 1);
						glNormal3fv(vdb->no);
						glVertex3fv(vdb->co);

						if(x != gridFaces-1)
							a++;
					}

					vda = &faceGridData[(y+0)*gridSize + x];
					vdb = &faceGridData[(y+1)*gridSize + x];

					PASSATTRIB(0, 0, 3);
					glNormal3fv(vda->no);
					glVertex3fv(vda->co);

					PASSATTRIB(0, 1, 2);
					glNormal3fv(vdb->no);
					glVertex3fv(vdb->co);

					glEnd();

					a++;
				}
			} else {
				glBegin(GL_QUADS);
				for (y=0; y<gridFaces; y++) {
					for (x=0; x<gridFaces; x++) {
						float *aco = faceGridData[(y+0)*gridSize + x].co;
						float *bco = faceGridData[(y+0)*gridSize + x + 1].co;
						float *cco = faceGridData[(y+1)*gridSize + x + 1].co;
						float *dco = faceGridData[(y+1)*gridSize + x].co;

						ccgDM_glNormalFast(aco, bco, cco, dco);

						PASSATTRIB(0, 1, 1);
						glVertex3fv(dco);
						PASSATTRIB(1, 1, 2);
						glVertex3fv(cco);
						PASSATTRIB(1, 0, 3);
						glVertex3fv(bco);
						PASSATTRIB(0, 0, 0);
						glVertex3fv(aco);
						
						a++;
					}
				}
				glEnd();
			}
		}
	}

#undef PASSATTRIB

	ccgFaceIterator_free(fi);
}


static void cgdm_drawFacesColored(DerivedMesh *dm, int UNUSED(useTwoSided), unsigned char *col1, unsigned char *col2) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGFaceIterator *fi = ccgSubSurf_getFaceIterator(ss);
	int gridSize = ccgSubSurf_getGridSize(ss);
	unsigned char *cp1, *cp2;
	int useTwoSide=1;

	ccgdm_pbvh_update(cgdm);

	cp1= col1;
	if(col2) {
		cp2= col2;
	} else {
		cp2= NULL;
		useTwoSide= 0;
	}

	glShadeModel(GL_SMOOTH);

	if(col2) {
		glEnable(GL_CULL_FACE);
	}

	glBegin(GL_QUADS);
	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);
		int S, x, y, numVerts = ccgSubSurf_getFaceNumVerts(f);

		for (S=0; S<numVerts; S++) {
			DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);
			for (y=0; y<gridSize-1; y++) {
				for (x=0; x<gridSize-1; x++) {
					float *a = faceGridData[(y+0)*gridSize + x].co;
					float *b = faceGridData[(y+0)*gridSize + x + 1].co;
					float *c = faceGridData[(y+1)*gridSize + x + 1].co;
					float *d = faceGridData[(y+1)*gridSize + x].co;

					glColor3ub(cp1[3], cp1[2], cp1[1]);
					glVertex3fv(d);
					glColor3ub(cp1[7], cp1[6], cp1[5]);
					glVertex3fv(c);
					glColor3ub(cp1[11], cp1[10], cp1[9]);
					glVertex3fv(b);
					glColor3ub(cp1[15], cp1[14], cp1[13]);
					glVertex3fv(a);

					if (useTwoSide) {
						glColor3ub(cp2[15], cp2[14], cp2[13]);
						glVertex3fv(a);
						glColor3ub(cp2[11], cp2[10], cp2[9]);
						glVertex3fv(b);
						glColor3ub(cp2[7], cp2[6], cp2[5]);
						glVertex3fv(c);
						glColor3ub(cp2[3], cp2[2], cp2[1]);
						glVertex3fv(d);
					}

					if (cp2) cp2+=16;
					cp1+=16;
				}
			}
		}
	}
	glEnd();

	ccgFaceIterator_free(fi);
}

static void cgdm_drawFacesTex_common(DerivedMesh *dm,
	int (*drawParams)(MTFace *tface, int has_mcol, int matnr),
	int (*drawParamsMapped)(void *userData, int index),
	void *userData) 
{
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	MCol *mcol = dm->getTessFaceDataArray(dm, CD_WEIGHT_MCOL);
	MTFace *tf = DM_get_tessface_data_layer(dm, CD_MTFACE);
	char *faceFlags = cgdm->faceFlags;
	int i, totface, flag, gridSize = ccgSubSurf_getGridSize(ss);
	int gridFaces = gridSize - 1;

	ccgdm_pbvh_update(cgdm);

	if(!mcol)
		mcol = dm->getTessFaceDataArray(dm, CD_MCOL);

	if(!mcol)
		mcol = dm->getTessFaceDataArray(dm, CD_TEXTURE_MCOL);

	totface = ccgSubSurf_getNumFaces(ss);
	for(i = 0; i < totface; i++) {
		CCGFace *f = cgdm->faceMap[i].face;
		int S, x, y, numVerts = ccgSubSurf_getFaceNumVerts(f);
		int drawSmooth, index = ccgDM_getFaceMapIndex(ss, f);
		int origIndex = GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f));
		unsigned char *cp= NULL;
		int mat_nr;

		if(faceFlags) {
			drawSmooth = (faceFlags[origIndex*2] & ME_SMOOTH);
			mat_nr= faceFlags[origIndex*2 + 1];
		}
		else {
			drawSmooth = 1;
			mat_nr= 0;
		}

		if(drawParams)
			flag = drawParams(tf, (mcol != NULL), mat_nr);
		else if (index != ORIGINDEX_NONE)
			flag= (drawParamsMapped)? drawParamsMapped(userData, index): 1;
		else
			flag= GPU_enable_material(mat_nr, NULL) ? 1:0;


		if (flag == 0) { /* flag 0 == the face is hidden or invisible */
			if(tf) tf += gridFaces*gridFaces*numVerts;
			if(mcol) mcol += gridFaces*gridFaces*numVerts*4;
			continue;
		}

		/* flag 1 == use vertex colors */
		if(mcol) {
			if(flag==1) cp= (unsigned char*)mcol;
			mcol += gridFaces*gridFaces*numVerts*4;
		}

		for (S=0; S<numVerts; S++) {
			DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);
			DMGridData *a, *b;

			if (drawSmooth) {
				glShadeModel(GL_SMOOTH);
				for (y=0; y<gridFaces; y++) {
					glBegin(GL_QUAD_STRIP);
					for (x=0; x<gridFaces; x++) {
						a = &faceGridData[(y+0)*gridSize + x];
						b = &faceGridData[(y+1)*gridSize + x];

						if(tf) glTexCoord2fv(tf->uv[0]);
						if(cp) glColor3ub(cp[3], cp[2], cp[1]);
						glNormal3fv(a->no);
						glVertex3fv(a->co);

						if(tf) glTexCoord2fv(tf->uv[1]);
						if(cp) glColor3ub(cp[7], cp[6], cp[5]);
						glNormal3fv(b->no);
						glVertex3fv(b->co);
						
						if(x != gridFaces-1) {
							if(tf) tf++;
							if(cp) cp += 16;
						}
					}

					a = &faceGridData[(y+0)*gridSize + x];
					b = &faceGridData[(y+1)*gridSize + x];

					if(tf) glTexCoord2fv(tf->uv[3]);
					if(cp) glColor3ub(cp[15], cp[14], cp[13]);
					glNormal3fv(a->no);
					glVertex3fv(a->co);

					if(tf) glTexCoord2fv(tf->uv[2]);
					if(cp) glColor3ub(cp[11], cp[10], cp[9]);
					glNormal3fv(b->no);
					glVertex3fv(b->co);

					if(tf) tf++;
					if(cp) cp += 16;

					glEnd();
				}
			} else {
				glShadeModel(GL_FLAT);
				glBegin(GL_QUADS);
				for (y=0; y<gridFaces; y++) {
					for (x=0; x<gridFaces; x++) {
						float *a_co = faceGridData[(y+0)*gridSize + x].co;
						float *b_co = faceGridData[(y+0)*gridSize + x + 1].co;
						float *c_co = faceGridData[(y+1)*gridSize + x + 1].co;
						float *d_co = faceGridData[(y+1)*gridSize + x].co;

						ccgDM_glNormalFast(a_co, b_co, c_co, d_co);

						if(tf) glTexCoord2fv(tf->uv[1]);
						if(cp) glColor3ub(cp[7], cp[6], cp[5]);
						glVertex3fv(d_co);

						if(tf) glTexCoord2fv(tf->uv[2]);
						if(cp) glColor3ub(cp[11], cp[10], cp[9]);
						glVertex3fv(c_co);

						if(tf) glTexCoord2fv(tf->uv[3]);
						if(cp) glColor3ub(cp[15], cp[14], cp[13]);
						glVertex3fv(b_co);

						if(tf) glTexCoord2fv(tf->uv[0]);
						if(cp) glColor3ub(cp[3], cp[2], cp[1]);
						glVertex3fv(a_co);

						if(tf) tf++;
						if(cp) cp += 16;
					}
				}
				glEnd();
			}
		}
	}
}

static void cgdm_drawFacesTex(DerivedMesh *dm, int (*setDrawOptions)(MTFace *tface, int has_vcol, int matnr))
{
	cgdm_drawFacesTex_common(dm, setDrawOptions, NULL, NULL);
}

static void cgdm_drawMappedFacesTex(DerivedMesh *dm, int (*setDrawOptions)(void *userData, int index), void *userData)
{
	cgdm_drawFacesTex_common(dm, NULL, setDrawOptions, userData);
}

static void cgdm_drawUVEdges(DerivedMesh *dm)
{

	MFace *mf = dm->getTessFaceArray(dm);
	MTFace *tf = DM_get_tessface_data_layer(dm, CD_MTFACE);
	int i;
	
	if (tf) {
		glBegin(GL_LINES);
		for(i = 0; i < dm->numFaceData; i++, mf++, tf++) {
			if(!(mf->flag&ME_HIDE)) {
				glVertex2fv(tf->uv[0]);
				glVertex2fv(tf->uv[1]);
	
				glVertex2fv(tf->uv[1]);
				glVertex2fv(tf->uv[2]);
	
				if(!mf->v4) {
					glVertex2fv(tf->uv[2]);
					glVertex2fv(tf->uv[0]);
				} else {
					glVertex2fv(tf->uv[2]);
					glVertex2fv(tf->uv[3]);
	
					glVertex2fv(tf->uv[3]);
					glVertex2fv(tf->uv[0]);
				}
			}
		}
		glEnd();
	}
}

static void ccgDM_drawMappedFaces(DerivedMesh *dm, int (*setDrawOptions)(void *userData, int index, int *drawSmooth_r), void *userData, int useColors, int (*setMaterial)(int, void *attribs),
			int (*compareDrawOptions)(void *userData, int cur_index, int next_index)) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	MCol *mcol= NULL;
	int i, gridSize = ccgSubSurf_getGridSize(ss);
	char *faceFlags = cgdm->faceFlags;
	int gridFaces = gridSize - 1, totface;

	/* currently unused -- each original face is handled separately */
	(void)compareDrawOptions;

	if(useColors) {
		mcol = dm->getTessFaceDataArray(dm, CD_WEIGHT_MCOL);
		if(!mcol)
			mcol = dm->getTessFaceDataArray(dm, CD_MCOL);
	}

	totface = ccgSubSurf_getNumFaces(ss);
	for(i = 0; i < totface; i++) {
		CCGFace *f = cgdm->faceMap[i].face;
		int S, x, y, numVerts = ccgSubSurf_getFaceNumVerts(f);
		int drawSmooth, index = ccgDM_getFaceMapIndex(ss, f);
		int origIndex;
		unsigned char *cp= NULL;

		origIndex = GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f));

		if(faceFlags) drawSmooth = (faceFlags[origIndex*2] & ME_SMOOTH);
		else drawSmooth = 1;

		if(mcol) {
			cp= (unsigned char*)mcol;
			mcol += gridFaces*gridFaces*numVerts*4;
		}

		{
			int draw= 1;

			if(index == ORIGINDEX_NONE)
				draw= setMaterial(faceFlags ? faceFlags[origIndex*2 + 1] + 1: 1, NULL); /* XXX, no faceFlags no material */
			else if (setDrawOptions)
				draw= setDrawOptions(userData, index, &drawSmooth);

			if (draw) {
				if (draw==2) {
					  glEnable(GL_POLYGON_STIPPLE);
					  glPolygonStipple(stipple_quarttone);
				}

				/* no need to set shading mode to flat because
				*  normals are already used to change shading */
				glShadeModel(GL_SMOOTH);
				
				for (S=0; S<numVerts; S++) {
					DMGridData *faceGridData = ccgSubSurf_getFaceGridDataArray(ss, f, S);
					if (drawSmooth) {
						for (y=0; y<gridFaces; y++) {
							DMGridData *a, *b;
							glBegin(GL_QUAD_STRIP);
							for (x=0; x<gridFaces; x++) {
								a = &faceGridData[(y+0)*gridSize + x];
								b = &faceGridData[(y+1)*gridSize + x];
	
								if(cp) glColor3ub(cp[3], cp[2], cp[1]);
								glNormal3fv(a->no);
								glVertex3fv(a->co);
								if(cp) glColor3ub(cp[7], cp[6], cp[5]);
								glNormal3fv(b->no);
								glVertex3fv(b->co);

								if(x != gridFaces-1) {
									if(cp) cp += 16;
								}
							}

							a = &faceGridData[(y+0)*gridSize + x];
							b = &faceGridData[(y+1)*gridSize + x];

							if(cp) glColor3ub(cp[15], cp[14], cp[13]);
							glNormal3fv(a->no);
							glVertex3fv(a->co);
							if(cp) glColor3ub(cp[11], cp[10], cp[9]);
							glNormal3fv(b->no);
							glVertex3fv(b->co);

							if(cp) cp += 16;

							glEnd();
						}
					} else {
						glBegin(GL_QUADS);
						for (y=0; y<gridFaces; y++) {
							for (x=0; x<gridFaces; x++) {
								float *a = faceGridData[(y+0)*gridSize + x].co;
								float *b = faceGridData[(y+0)*gridSize + x + 1].co;
								float *c = faceGridData[(y+1)*gridSize + x + 1].co;
								float *d = faceGridData[(y+1)*gridSize + x].co;

								ccgDM_glNormalFast(a, b, c, d);
	
								if(cp) glColor3ub(cp[7], cp[6], cp[5]);
								glVertex3fv(d);
								if(cp) glColor3ub(cp[11], cp[10], cp[9]);
								glVertex3fv(c);
								if(cp) glColor3ub(cp[15], cp[14], cp[13]);
								glVertex3fv(b);
								if(cp) glColor3ub(cp[3], cp[2], cp[1]);
								glVertex3fv(a);

								if(cp) cp += 16;
							}
						}
						glEnd();
					}
				}
				if (draw==2)
					glDisable(GL_POLYGON_STIPPLE);
			}
		}
	}
}
static void cgdm_drawMappedEdges(DerivedMesh *dm, int (*setDrawOptions)(void *userData, int index), void *userData) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGEdgeIterator *ei = ccgSubSurf_getEdgeIterator(ss);
	int i, useAging, edgeSize = ccgSubSurf_getEdgeSize(ss);

	ccgSubSurf_getUseAgeCounts(ss, &useAging, NULL, NULL, NULL);

	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);
		DMGridData *edgeData = ccgSubSurf_getEdgeDataArray(ss, e);
		int index = ccgDM_getEdgeMapIndex(ss, e);

		glBegin(GL_LINE_STRIP);
		if (index!=-1 && (!setDrawOptions || setDrawOptions(userData, index))) {
			if (useAging && !(G.f&G_BACKBUFSEL)) {
				int ageCol = 255-ccgSubSurf_getEdgeAge(ss, e)*4;
				glColor3ub(0, ageCol>0?ageCol:0, 0);
			}

			for (i=0; i<edgeSize-1; i++) {
				glVertex3fv(edgeData[i].co);
				glVertex3fv(edgeData[i+1].co);
			}
		}
		glEnd();
	}

	ccgEdgeIterator_free(ei);
}
static void cgdm_drawMappedEdgesInterp(DerivedMesh *dm, int (*setDrawOptions)(void *userData, int index), void (*setDrawInterpOptions)(void *userData, int index, float t), void *userData) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGEdgeIterator *ei = ccgSubSurf_getEdgeIterator(ss);
	int i, useAging, edgeSize = ccgSubSurf_getEdgeSize(ss);

	ccgSubSurf_getUseAgeCounts(ss, &useAging, NULL, NULL, NULL);

	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);
		DMGridData *edgeData = ccgSubSurf_getEdgeDataArray(ss, e);
		int index = ccgDM_getEdgeMapIndex(ss, e);

		glBegin(GL_LINE_STRIP);
		if (index!=-1 && (!setDrawOptions || setDrawOptions(userData, index))) {
			for (i=0; i<edgeSize; i++) {
				setDrawInterpOptions(userData, index, (float) i/(edgeSize-1));

				if (useAging && !(G.f&G_BACKBUFSEL)) {
					int ageCol = 255-ccgSubSurf_getEdgeAge(ss, e)*4;
					glColor3ub(0, ageCol>0?ageCol:0, 0);
				}

				glVertex3fv(edgeData[i].co);
			}
		}
		glEnd();
	}

	ccgEdgeIterator_free(ei);
}
static void cgdm_foreachMappedFaceCenter(DerivedMesh *dm, void (*func)(void *userData, int index, float *co, float *no), void *userData) {
	CCGDerivedMesh *cgdm = (CCGDerivedMesh*) dm;
	CCGSubSurf *ss = cgdm->ss;
	CCGFaceIterator *fi = ccgSubSurf_getFaceIterator(ss);

	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);
		int index = ccgDM_getFaceMapIndex(ss, f);

		if (index!=-1) {
				/* Face center data normal isn't updated atm. */
			DMGridData *vd = ccgSubSurf_getFaceGridData(ss, f, 0, 0, 0);

			func(userData, index, vd->co, vd->no);
		}
	}

	ccgFaceIterator_free(fi);
}

static void cgdm_release(DerivedMesh *dm) {
	CCGDerivedMesh *ccgdm = (CCGDerivedMesh*) dm;

	if (DM_release(dm)) {
		/* Before freeing, need to update the displacement map */
		if(ccgdm->multires.modified) {
			/* Check that mmd still exists */
			if(!ccgdm->multires.local_mmd && BLI_findindex(&ccgdm->multires.ob->modifiers, ccgdm->multires.mmd) < 0)
				ccgdm->multires.mmd = NULL;
			if(ccgdm->multires.mmd)
				ccgdm->multires.update(dm);
		}

		if (ccgdm->ehash)
			BLI_edgehash_free(ccgdm->ehash, NULL);

		if(ccgdm->reverseFaceMap) MEM_freeN(ccgdm->reverseFaceMap);
		if(ccgdm->gridFaces) MEM_freeN(ccgdm->gridFaces);
		if(ccgdm->gridData) MEM_freeN(ccgdm->gridData);
		if(ccgdm->gridAdjacency) MEM_freeN(ccgdm->gridAdjacency);
		if(ccgdm->gridOffset) MEM_freeN(ccgdm->gridOffset);
		if(ccgdm->freeSS) ccgSubSurf_free(ccgdm->ss);
		if(ccgdm->fmap) MEM_freeN(ccgdm->fmap);
		if(ccgdm->fmap_mem) MEM_freeN(ccgdm->fmap_mem);
		MEM_freeN(ccgdm->edgeFlags);
		MEM_freeN(ccgdm->faceFlags);
		MEM_freeN(ccgdm->vertMap);
		MEM_freeN(ccgdm->edgeMap);
		MEM_freeN(ccgdm->faceMap);
		MEM_freeN(ccgdm);
	}
}

static void ccg_loops_to_corners(CustomData *fdata, CustomData *ldata, 
			  CustomData *pdata, int loopstart, int findex, 
			  int polyindex, int numTex, int numCol) 
{
	MTFace *texface;
	MTexPoly *texpoly;
	MCol *mcol;
	MLoopCol *mloopcol;
	MLoopUV *mloopuv;
	int i, j, hasWCol = CustomData_has_layer(ldata, CD_WEIGHT_MLOOPCOL);

	for(i=0; i < numTex; i++){
		texface = CustomData_get_n(fdata, CD_MTFACE, findex, i);
		texpoly = CustomData_get_n(pdata, CD_MTEXPOLY, polyindex, i);
		
		texface->tpage = texpoly->tpage;
		texface->flag = texpoly->flag;
		texface->transp = texpoly->transp;
		texface->mode = texpoly->mode;
		texface->tile = texpoly->tile;
		texface->unwrap = texpoly->unwrap;

		mloopuv = CustomData_get_n(ldata, CD_MLOOPUV, loopstart, i);
		for (j=0; j<4; j++, mloopuv++) {
			texface->uv[j][0] = mloopuv->uv[0];
			texface->uv[j][1] = mloopuv->uv[1];
		}
	}

	for(i=0; i < numCol; i++){
		mloopcol = CustomData_get_n(ldata, CD_MLOOPCOL, loopstart, i);
		mcol = CustomData_get_n(fdata, CD_MCOL, findex, i);

		for (j=0; j<4; j++, mloopcol++) {
			mcol[j].r = mloopcol->r;
			mcol[j].g = mloopcol->g;
			mcol[j].b = mloopcol->b;
			mcol[j].a = mloopcol->a;
		}
	}
	
	if (hasWCol) {
		mloopcol = CustomData_get(ldata, loopstart, CD_WEIGHT_MLOOPCOL);
		mcol = CustomData_get(fdata, findex, CD_WEIGHT_MCOL);

		for (j=0; j<4; j++, mloopcol++) {
			mcol[j].r = mloopcol->r;
			mcol[j].g = mloopcol->g;
			mcol[j].b = mloopcol->b;
			mcol[j].a = mloopcol->a;
		}
	}
}

static void *ccgDM_get_vert_data_layer(DerivedMesh *dm, int type)
{
	if(type == CD_ORIGINDEX) {
		/* create origindex on demand to save memory */
		CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;
		CCGSubSurf *ss= cgdm->ss;
		int *origindex;
		int a, index, totnone, totorig;

		DM_add_vert_layer(dm, CD_ORIGINDEX, CD_CALLOC, NULL);
		origindex= DM_get_vert_data_layer(dm, CD_ORIGINDEX);

		totorig = ccgSubSurf_getNumVerts(ss);
		totnone= dm->numVertData - totorig;

		/* original vertices are at the end */
		for(a=0; a<totnone; a++)
			origindex[a]= ORIGINDEX_NONE;

		for(index=0; index<totorig; index++, a++) {
			CCGVert *v = cgdm->vertMap[index].vert;
			origindex[a] = ccgDM_getVertMapIndex(cgdm->ss, v);
		}

		return origindex;
	}

	return DM_get_vert_data_layer(dm, type);
}

static void *ccgDM_get_edge_data_layer(DerivedMesh *dm, int type)
{
	if(type == CD_ORIGINDEX) {
		/* create origindex on demand to save memory */
		CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;
		CCGSubSurf *ss= cgdm->ss;
		int *origindex;
		int a, i, index, totnone, totorig, totedge;
		int edgeSize= ccgSubSurf_getEdgeSize(ss);

		DM_add_edge_layer(dm, CD_ORIGINDEX, CD_CALLOC, NULL);
		origindex= DM_get_edge_data_layer(dm, CD_ORIGINDEX);

		totedge= ccgSubSurf_getNumEdges(ss);
		totorig= totedge*(edgeSize - 1);
		totnone= dm->numEdgeData - totorig;

		/* original edges are at the end */
		for(a=0; a<totnone; a++)
			origindex[a]= ORIGINDEX_NONE;

		for(index=0; index<totedge; index++) {
			CCGEdge *e= cgdm->edgeMap[index].edge;
			int mapIndex= ccgDM_getEdgeMapIndex(ss, e);

			for(i = 0; i < edgeSize - 1; i++, a++)
				origindex[a]= mapIndex;
		}

		return origindex;
	}

	return DM_get_edge_data_layer(dm, type);
}

static void *ccgDM_get_face_data_layer(DerivedMesh *dm, int type)
{
	if(type == CD_ORIGINDEX) {
		/* create origindex on demand to save memory */
		CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;
		CCGSubSurf *ss= cgdm->ss;
		int *origindex;
		int a, i, index, totface;
		int gridFaces = ccgSubSurf_getGridSize(ss) - 1;

		DM_add_tessface_layer(dm, CD_ORIGINDEX, CD_CALLOC, NULL);
		origindex= DM_get_tessface_data_layer(dm, CD_ORIGINDEX);

		totface= ccgSubSurf_getNumFaces(ss);

		for(a=0, index=0; index<totface; index++) {
			CCGFace *f = cgdm->faceMap[index].face;
			int numVerts = ccgSubSurf_getFaceNumVerts(f);
			int mapIndex = ccgDM_getFaceMapIndex(ss, f);

			for(i=0; i<gridFaces*gridFaces*numVerts; i++, a++)
				origindex[a]= mapIndex;
		}

		return origindex;
	}

	return DM_get_tessface_data_layer(dm, type);
}

static int ccgDM_getNumGrids(DerivedMesh *dm)
{
	CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;
	int index, numFaces, numGrids;

	numFaces= ccgSubSurf_getNumFaces(cgdm->ss);
	numGrids= 0;

	for(index=0; index<numFaces; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		numGrids += ccgSubSurf_getFaceNumVerts(f);
	}

	return numGrids;
}

static int ccgDM_getGridSize(DerivedMesh *dm)
{
	CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;
	return ccgSubSurf_getGridSize(cgdm->ss);
}

static int cgdm_adjacent_grid(CCGSubSurf *ss, int *gridOffset, CCGFace *f, int S, int offset)
{
	CCGFace *adjf;
	CCGEdge *e;
	int i, j= 0, numFaces, fIndex, numEdges= 0;

	e = ccgSubSurf_getFaceEdge(ss, f, S);
	numFaces = ccgSubSurf_getEdgeNumFaces(e);

	if(numFaces != 2)
		return -1;

	for(i = 0; i < numFaces; i++) {
		adjf = ccgSubSurf_getEdgeFace(e, i);

		if(adjf != f) {
			numEdges = ccgSubSurf_getFaceNumVerts(adjf);
			for(j = 0; j < numEdges; j++)
				if(ccgSubSurf_getFaceEdge(ss, adjf, j) == e)
					break;

			if(j != numEdges)
				break;
		}
	}
	
	fIndex = GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, adjf));

	return gridOffset[fIndex] + (j + offset)%numEdges;
}

static void ccgdm_create_grids(DerivedMesh *dm)
{
	CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;
	CCGSubSurf *ss= cgdm->ss;
	DMGridData **gridData;
	DMGridAdjacency *gridAdjacency, *adj;
	CCGFace **gridFaces;
	int *gridOffset;
	int index, numFaces, numGrids, S, gIndex /*, gridSize*/;

	if(cgdm->gridData)
		return;
	
	numGrids = ccgDM_getNumGrids(dm);
	numFaces = ccgSubSurf_getNumFaces(ss);
	/*gridSize = ccgDM_getGridSize(dm);*/  /*UNUSED*/

	/* compute offset into grid array for each face */
	gridOffset = MEM_mallocN(sizeof(int)*numFaces, "cgdm.gridOffset");

	for(gIndex = 0, index = 0; index < numFaces; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		int numVerts = ccgSubSurf_getFaceNumVerts(f);

		gridOffset[index] = gIndex;
		gIndex += numVerts;
	}

	/* compute grid data */
	gridData = MEM_mallocN(sizeof(DMGridData*)*numGrids, "cgdm.gridData");
	gridAdjacency = MEM_mallocN(sizeof(DMGridAdjacency)*numGrids, "cgdm.gridAdjacency");
	gridFaces = MEM_mallocN(sizeof(CCGFace*)*numGrids, "cgdm.gridFaces");

	for(gIndex = 0, index = 0; index < numFaces; index++) {
		CCGFace *f = cgdm->faceMap[index].face;
		int numVerts = ccgSubSurf_getFaceNumVerts(f);

		for(S = 0; S < numVerts; S++, gIndex++) {
			int prevS = (S - 1 + numVerts) % numVerts;
			int nextS = (S + 1 + numVerts) % numVerts;

			gridData[gIndex] = ccgSubSurf_getFaceGridDataArray(ss, f, S);
			gridFaces[gIndex] = f;

			adj = &gridAdjacency[gIndex];

			adj->index[0] = gIndex - S + nextS;
			adj->rotation[0] = 3;
			adj->index[1] = cgdm_adjacent_grid(ss, gridOffset, f, prevS, 0);
			adj->rotation[1] = 1;
			adj->index[2] = cgdm_adjacent_grid(ss, gridOffset, f, S, 1);
			adj->rotation[2] = 3;
			adj->index[3] = gIndex - S + prevS;
			adj->rotation[3] = 1;
		}
	}

	cgdm->gridData = gridData;
	cgdm->gridFaces = gridFaces;
	cgdm->gridAdjacency = gridAdjacency;
	cgdm->gridOffset = gridOffset;
}

static DMGridData **ccgDM_getGridData(DerivedMesh *dm)
{
	CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;

	ccgdm_create_grids(dm);
	return cgdm->gridData;
}

static DMGridAdjacency *ccgDM_getGridAdjacency(DerivedMesh *dm)
{
	CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;

	ccgdm_create_grids(dm);
	return cgdm->gridAdjacency;
}

static int *ccgDM_getGridOffset(DerivedMesh *dm)
{
	CCGDerivedMesh *cgdm= (CCGDerivedMesh*)dm;

	ccgdm_create_grids(dm);
	return cgdm->gridOffset;
}

static ListBase *ccgDM_getFaceMap(Object *ob, DerivedMesh *dm)
{
	CCGDerivedMesh *ccgdm= (CCGDerivedMesh*)dm;

	if(!ccgdm->multires.mmd && !ccgdm->fmap && ob->type == OB_MESH) {
		Mesh *me= ob->data;

		create_vert_face_map(&ccgdm->fmap, &ccgdm->fmap_mem, me->mface,
				     me->totvert, me->totface);
	}

	return ccgdm->fmap;
}

static int ccgDM_use_grid_pbvh(CCGDerivedMesh *ccgdm)
{
	MultiresModifierData *mmd= ccgdm->multires.mmd;

	/* both of multires and subsurm modifiers are CCG, but
	   grids should only be used when sculpting on multires */
	if(!mmd)
		return 0;

	return 1;
}

static struct PBVH *ccgDM_getPBVH(Object *ob, DerivedMesh *dm)
{
	CCGDerivedMesh *ccgdm= (CCGDerivedMesh*)dm;
	int gridSize, numGrids, grid_pbvh;

	if(!ob) {
		ccgdm->pbvh= NULL;
		return NULL;
	}

	if(!ob->sculpt)
		return NULL;

	grid_pbvh= ccgDM_use_grid_pbvh(ccgdm);

	if(ob->sculpt->pbvh) {
		if(grid_pbvh) {
			/* pbvh's grids, gridadj and gridfaces points to data inside ccgdm
			   but this can be freed on ccgdm release, this updates the pointers
			   when the ccgdm gets remade, the assumption is that the topology
			   does not change. */
			ccgdm_create_grids(dm);
			BLI_pbvh_grids_update(ob->sculpt->pbvh, ccgdm->gridData, ccgdm->gridAdjacency, (void**)ccgdm->gridFaces);
		}

		ccgdm->pbvh = ob->sculpt->pbvh;
	}

	if(ccgdm->pbvh)
		return ccgdm->pbvh;

	/* no pbvh exists yet, we need to create one. only in case of multires
	   we build a pbvh over the modified mesh, in other cases the base mesh
	   is being sculpted, so we build a pbvh from that. */
	if(grid_pbvh) {
		ccgdm_create_grids(dm);

		gridSize = ccgDM_getGridSize(dm);
		numGrids = ccgDM_getNumGrids(dm);

		ob->sculpt->pbvh= ccgdm->pbvh = BLI_pbvh_new();
		BLI_pbvh_build_grids(ccgdm->pbvh, ccgdm->gridData, ccgdm->gridAdjacency,
			numGrids, gridSize, (void**)ccgdm->gridFaces);
	} else if(ob->type == OB_MESH) {
		Mesh *me= ob->data;
		ob->sculpt->pbvh= ccgdm->pbvh = BLI_pbvh_new();
		BLI_pbvh_build_mesh(ccgdm->pbvh, me->mface, me->mvert,
				   me->totface, me->totvert);
	}

	return ccgdm->pbvh;
}

static void ccgDM_recalcTesselection(DerivedMesh *UNUSED(dm))
{
	/* Nothing to do: CCG handles creating its own tessfaces */
}

static void ccgDM_calcNormals(DerivedMesh *UNUSED(dm))
{
	/* Nothing to do: CCG calculates normals during drawing */
}

static CCGDerivedMesh *getCCGDerivedMesh(CCGSubSurf *ss,
										 int drawInteriorEdges,
										 int useSubsurfUv,
										 DerivedMesh *dm)
{
	CCGDerivedMesh *ccgdm = MEM_callocN(sizeof(*ccgdm), "cgdm");
	CCGVertIterator *vi;
	CCGEdgeIterator *ei;
	CCGFaceIterator *fi;
	int index, totvert, totedge, totface;
	int i;
	int vertNum, edgeNum, faceNum;
	int *vertOrigIndex, *faceOrigIndex, *polyOrigIndex, *base_polyOrigIndex; /* *edgeOrigIndex - as yet, unused  */
	short *edgeFlags;
	char *faceFlags;
	int *loopidx = NULL, *vertidx = NULL;
	BLI_array_declare(loopidx);
	BLI_array_declare(vertidx);
	int loopindex, loopindex2;
	int edgeSize, has_edge_origindex;
	int gridSize;
	int gridFaces, gridCuts;
	/*int gridSideVerts;*/
	int gridSideEdges;
	int numTex, numCol;
	int gridInternalEdges;
	float *w = NULL;
	WeightTable wtable = {0};
	/* MCol *mcol; */ /* UNUSED */
	MEdge *medge = NULL;
	/* MFace *mface = NULL; */
	MPoly *mpoly = NULL;

	DM_from_template(&ccgdm->dm, dm, DM_TYPE_CCGDM,
					 ccgSubSurf_getNumFinalVerts(ss),
					 ccgSubSurf_getNumFinalEdges(ss),
					 ccgSubSurf_getNumFinalFaces(ss),
					 ccgSubSurf_getNumFinalFaces(ss)*4, 
					 ccgSubSurf_getNumFinalFaces(ss));
	
	numTex = CustomData_number_of_layers(&ccgdm->dm.loopData, CD_MLOOPUV);
	numCol = CustomData_number_of_layers(&ccgdm->dm.loopData, CD_MLOOPCOL);
	
	if (numTex && CustomData_number_of_layers(&ccgdm->dm.faceData, CD_MTFACE) != numTex)
		CustomData_from_bmeshpoly(&ccgdm->dm.faceData, &ccgdm->dm.polyData, &ccgdm->dm.loopData, ccgSubSurf_getNumFinalFaces(ss));
	else if (numCol && CustomData_number_of_layers(&ccgdm->dm.faceData, CD_MCOL) != numCol)
		CustomData_from_bmeshpoly(&ccgdm->dm.faceData, &ccgdm->dm.polyData, &ccgdm->dm.loopData, ccgSubSurf_getNumFinalFaces(ss));

	ccgdm->dm.getMinMax = cgdm_getMinMax;
	ccgdm->dm.getNumVerts = cgdm_getNumVerts;
	ccgdm->dm.getNumEdges = cgdm_getNumEdges;
	ccgdm->dm.getNumTessFaces = cgdm_getNumTessFaces;
	ccgdm->dm.getNumFaces = cgdm_getNumTessFaces;

	ccgdm->dm.getNumGrids = ccgDM_getNumGrids;
	ccgdm->dm.getPBVH = ccgDM_getPBVH;

	ccgdm->dm.getVert = ccgDM_getFinalVert;
	ccgdm->dm.getEdge = ccgDM_getFinalEdge;
	ccgdm->dm.getTessFace = ccgDM_getFinalFace;
	ccgdm->dm.getVertCo = ccgDM_getFinalVertCo;
	ccgdm->dm.getVertNo = ccgDM_getFinalVertNo;
	ccgdm->dm.copyVertArray = ccgDM_copyFinalVertArray;
	ccgdm->dm.copyEdgeArray = ccgDM_copyFinalEdgeArray;
	ccgdm->dm.copyTessFaceArray = ccgDM_copyFinalFaceArray;
	ccgdm->dm.copyLoopArray = ccgDM_copyFinalLoopArray;
	ccgdm->dm.copyPolyArray = ccgDM_copyFinalPolyArray;
	ccgdm->dm.getVertData = DM_get_vert_data;
	ccgdm->dm.getEdgeData = DM_get_edge_data;
	ccgdm->dm.getTessFaceData = DM_get_face_data;
	ccgdm->dm.getVertDataArray = ccgDM_get_vert_data_layer;
	ccgdm->dm.getEdgeDataArray = ccgDM_get_edge_data_layer;
	ccgdm->dm.getTessFaceDataArray = ccgDM_get_face_data_layer;
	ccgdm->dm.getNumGrids = ccgDM_getNumGrids;
	ccgdm->dm.getGridSize = ccgDM_getGridSize;
	ccgdm->dm.getGridData = ccgDM_getGridData;
	ccgdm->dm.getGridAdjacency = ccgDM_getGridAdjacency;
	ccgdm->dm.getGridOffset = ccgDM_getGridOffset;
	ccgdm->dm.getFaceMap = ccgDM_getFaceMap;
	ccgdm->dm.getPBVH = ccgDM_getPBVH;

	ccgdm->dm.getTessFace = ccgDM_getFinalFace;
	ccgdm->dm.copyVertArray = ccgDM_copyFinalVertArray;
	ccgdm->dm.copyEdgeArray = ccgDM_copyFinalEdgeArray;
	ccgdm->dm.copyTessFaceArray = ccgDM_copyFinalFaceArray;
	ccgdm->dm.getVertData = DM_get_vert_data;
	ccgdm->dm.getEdgeData = DM_get_edge_data;
	ccgdm->dm.getTessFaceData = DM_get_face_data;

	ccgdm->dm.calcNormals = ccgDM_calcNormals;
	ccgdm->dm.recalcTesselation = ccgDM_recalcTesselection;

	ccgdm->dm.getVertCos = cgdm_getVertCos;
	ccgdm->dm.foreachMappedVert = cgdm_foreachMappedVert;
	ccgdm->dm.foreachMappedEdge = cgdm_foreachMappedEdge;
	ccgdm->dm.foreachMappedFaceCenter = cgdm_foreachMappedFaceCenter;
	
	ccgdm->dm.drawVerts = ccgDM_drawVerts;
	ccgdm->dm.drawEdges = ccgDM_drawEdges;
	ccgdm->dm.drawLooseEdges = ccgDM_drawLooseEdges;
	ccgdm->dm.drawFacesSolid = ccgDM_drawFacesSolid;
	ccgdm->dm.drawFacesColored = cgdm_drawFacesColored;
	ccgdm->dm.drawFacesTex = cgdm_drawFacesTex;
	ccgdm->dm.drawFacesGLSL = cgdm_drawFacesGLSL;
	ccgdm->dm.drawMappedFaces = ccgDM_drawMappedFaces;
	ccgdm->dm.drawMappedFacesTex = cgdm_drawMappedFacesTex;
	ccgdm->dm.drawMappedFacesGLSL = cgdm_drawMappedFacesGLSL;
	ccgdm->dm.drawMappedFacesMat = cgdm_drawMappedFacesMat;
	ccgdm->dm.drawUVEdges = cgdm_drawUVEdges;

	ccgdm->dm.drawMappedEdgesInterp = cgdm_drawMappedEdgesInterp;
	ccgdm->dm.drawMappedEdges = cgdm_drawMappedEdges;

	ccgdm->dm.release = cgdm_release;
	
	ccgdm->ss = ss;
	ccgdm->drawInteriorEdges = drawInteriorEdges;
	ccgdm->useSubsurfUv = useSubsurfUv;

	totvert = ccgSubSurf_getNumVerts(ss);
	ccgdm->vertMap = MEM_callocN(totvert * sizeof(*ccgdm->vertMap), "vertMap");
	vi = ccgSubSurf_getVertIterator(ss);
	for(; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
		CCGVert *v = ccgVertIterator_getCurrent(vi);

		ccgdm->vertMap[GET_INT_FROM_POINTER(ccgSubSurf_getVertVertHandle(v))].vert = v;
	}
	ccgVertIterator_free(vi);

	totedge = ccgSubSurf_getNumEdges(ss);
	ccgdm->edgeMap = MEM_callocN(totedge * sizeof(*ccgdm->edgeMap), "edgeMap");
	ei = ccgSubSurf_getEdgeIterator(ss);
	for(; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e = ccgEdgeIterator_getCurrent(ei);

		ccgdm->edgeMap[GET_INT_FROM_POINTER(ccgSubSurf_getEdgeEdgeHandle(e))].edge = e;
	}

	totface = ccgSubSurf_getNumFaces(ss);
	ccgdm->faceMap = MEM_callocN(totface * sizeof(*ccgdm->faceMap), "faceMap");
	fi = ccgSubSurf_getFaceIterator(ss);
	for(; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f = ccgFaceIterator_getCurrent(fi);

		ccgdm->faceMap[GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f))].face = f;
	}
	ccgFaceIterator_free(fi);

	ccgdm->reverseFaceMap = MEM_callocN(sizeof(int)*ccgSubSurf_getNumFinalFaces(ss), "reverseFaceMap");

	edgeSize = ccgSubSurf_getEdgeSize(ss);
	gridSize = ccgSubSurf_getGridSize(ss);
	gridFaces = gridSize - 1;
	gridCuts = gridSize - 2;
	/*gridInternalVerts = gridSideVerts * gridSideVerts; - as yet, unused */
	gridSideEdges = gridSize - 1;
	gridInternalEdges = (gridSideEdges - 1) * gridSideEdges * 2; 

	vertNum = 0;
	edgeNum = 0;
	faceNum = 0;

	/* mvert = dm->getVertArray(dm); */ /* UNUSED */
	medge = dm->getEdgeArray(dm);
	/* mface = dm->getTessFaceArray(dm); */ /* UNUSED */

	mpoly = CustomData_get_layer(&dm->polyData, CD_MPOLY);
	base_polyOrigIndex = CustomData_get_layer(&dm->polyData, CD_ORIGINDEX);
	
	/*CDDM hack*/
	edgeFlags = ccgdm->edgeFlags = MEM_callocN(sizeof(short)*totedge, "faceFlags");
	faceFlags = ccgdm->faceFlags = MEM_callocN(sizeof(char)*2*totface, "faceFlags");

	vertOrigIndex = DM_get_vert_data_layer(&ccgdm->dm, CD_ORIGINDEX);
	/*edgeOrigIndex = DM_get_edge_data_layer(&cgdm->dm, CD_ORIGINDEX);*/
	faceOrigIndex = DM_get_tessface_data_layer(&ccgdm->dm, CD_ORIGINDEX);

	polyOrigIndex = DM_get_face_data_layer(&ccgdm->dm, CD_ORIGINDEX);

#if 0
	/* this is not in trunk, can gives problems because colors initialize
	 * as black, just dont do it!, it works fine - campbell */
	if (!CustomData_has_layer(&ccgdm->dm.faceData, CD_MCOL))
		DM_add_tessface_layer(&ccgdm->dm, CD_MCOL, CD_CALLOC, NULL);
	mcol = DM_get_tessface_data_layer(&ccgdm->dm, CD_MCOL);
#endif

	has_edge_origindex = CustomData_has_layer(&ccgdm->dm.edgeData, CD_ORIGINDEX);

	faceNum = 0;
	loopindex = loopindex2 = 0; //current loop index
	for (index = 0; index < totface; index++) {
		CCGFace *f = ccgdm->faceMap[index].face;
		int numVerts = ccgSubSurf_getFaceNumVerts(f);
		int numFinalEdges = numVerts * (gridSideEdges + gridInternalEdges);
		int origIndex = GET_INT_FROM_POINTER(ccgSubSurf_getFaceFaceHandle(ss, f));
		int g2_wid = gridCuts+2;
		float *w2;
		int s, x, y;
		
		origIndex = base_polyOrigIndex ? base_polyOrigIndex[origIndex] : origIndex;
		
		w = get_ss_weights(&wtable, gridCuts, numVerts);

		ccgdm->faceMap[index].startVert = vertNum;
		ccgdm->faceMap[index].startEdge = edgeNum;
		ccgdm->faceMap[index].startFace = faceNum;
		
		faceFlags[0] = mpoly ?  mpoly[origIndex].flag : 0;
		faceFlags[1] = mpoly ? mpoly[origIndex].mat_nr : 0;
		faceFlags += 2;

		/* set the face base vert */
		*((int*)ccgSubSurf_getFaceUserData(ss, f)) = vertNum;

		BLI_array_empty(loopidx);		
		for (s=0; s<numVerts; s++) {
			BLI_array_growone(loopidx);
			loopidx[s] = loopindex++;
		}
		
		BLI_array_empty(vertidx);
				for(s = 0; s < numVerts; s++) {
			CCGVert *v = ccgSubSurf_getFaceVert(ss, f, s);
			
			BLI_array_growone(vertidx);
			vertidx[s] = GET_INT_FROM_POINTER(ccgSubSurf_getVertVertHandle(v));
		}
		

		/*I think this is for interpolating the center vert?*/
		w2 = w; // + numVerts*(g2_wid-1)*(g2_wid-1); //numVerts*((g2_wid-1)*g2_wid+g2_wid-1);
		DM_interp_vert_data(dm, &ccgdm->dm, vertidx, w2,
		                    numVerts, vertNum);
		if (vertOrigIndex) {
			*vertOrigIndex = ORIGINDEX_NONE;
			++vertOrigIndex;
		}

		++vertNum;

		/*interpolate per-vert data*/
		for(s = 0; s < numVerts; s++) {
			for(x = 1; x < gridFaces; x++) {
				w2 = w + s*numVerts*g2_wid*g2_wid + x*numVerts;
				DM_interp_vert_data(dm, &ccgdm->dm, vertidx, w2,
						    numVerts, vertNum);

				if (vertOrigIndex) {
					*vertOrigIndex = ORIGINDEX_NONE;
					++vertOrigIndex;
				}

				++vertNum;
			}
		}

		/*interpolate per-vert data*/
		for(s = 0; s < numVerts; s++) {
			for(y = 1; y < gridFaces; y++) {
				for(x = 1; x < gridFaces; x++) {
					w2 = w + s*numVerts*g2_wid*g2_wid + (y*g2_wid+x)*numVerts;
					DM_interp_vert_data(dm, &ccgdm->dm, vertidx, w2,
							    numVerts, vertNum);

					if (vertOrigIndex) {
						*vertOrigIndex = ORIGINDEX_NONE;
						++vertOrigIndex;
					}

					++vertNum;
				}
			}
		}

		if (has_edge_origindex) {
			for(i = 0; i < numFinalEdges; ++i)
				*(int *)DM_get_edge_data(&ccgdm->dm, edgeNum + i,
							 CD_ORIGINDEX) = ORIGINDEX_NONE;
		}

		for (s=0; s<numVerts; s++) {
			/*interpolate per-face data*/
			for (y=0; y<gridFaces; y++) {
				for (x=0; x<gridFaces; x++) {
					w2 = w + s*numVerts*g2_wid*g2_wid + (y*g2_wid+x)*numVerts;
					CustomData_interp(&dm->loopData, &ccgdm->dm.loopData,
					                  loopidx, w2, NULL, numVerts, loopindex2);
					loopindex2++;

					w2 = w + s*numVerts*g2_wid*g2_wid + ((y+1)*g2_wid+(x))*numVerts;
					CustomData_interp(&dm->loopData, &ccgdm->dm.loopData,
					                  loopidx, w2, NULL, numVerts, loopindex2);
					loopindex2++;

					w2 = w + s*numVerts*g2_wid*g2_wid + ((y+1)*g2_wid+(x+1))*numVerts;
					CustomData_interp(&dm->loopData, &ccgdm->dm.loopData,
					                  loopidx, w2, NULL, numVerts, loopindex2);
					loopindex2++;
					
					w2 = w + s*numVerts*g2_wid*g2_wid + ((y)*g2_wid+(x+1))*numVerts;
					CustomData_interp(&dm->loopData, &ccgdm->dm.loopData,
					                  loopidx, w2, NULL, numVerts, loopindex2);
					loopindex2++;

					/*copy over poly data, e.g. mtexpoly*/
					CustomData_copy_data(&dm->polyData, &ccgdm->dm.polyData, origIndex, faceNum, 1);

					/*generate tesselated face data used for drawing*/
					ccg_loops_to_corners(&ccgdm->dm.faceData, &ccgdm->dm.loopData,
						&ccgdm->dm.polyData, loopindex2-4, faceNum, faceNum, numTex, numCol);
					
					/*set original index data*/
					if (faceOrigIndex) {
						*faceOrigIndex = origIndex;
						faceOrigIndex++;
					}
					if (polyOrigIndex) {
						*polyOrigIndex = origIndex;
						polyOrigIndex++;
					}

					ccgdm->reverseFaceMap[faceNum] = index;

					faceNum++;
				}
			}
		}

		edgeNum += numFinalEdges;
	}

	for(index = 0; index < totedge; ++index) {
		CCGEdge *e = ccgdm->edgeMap[index].edge;
		int numFinalEdges = edgeSize - 1;
		int mapIndex = ccgDM_getEdgeMapIndex(ss, e);
		int x;
		int vertIdx[2];
		int edgeIdx = GET_INT_FROM_POINTER(ccgSubSurf_getEdgeEdgeHandle(e));

		CCGVert *v;
		v = ccgSubSurf_getEdgeVert0(e);
		vertIdx[0] = GET_INT_FROM_POINTER(ccgSubSurf_getVertVertHandle(v));
		v = ccgSubSurf_getEdgeVert1(e);
		vertIdx[1] = GET_INT_FROM_POINTER(ccgSubSurf_getVertVertHandle(v));

		ccgdm->edgeMap[index].startVert = vertNum;
		ccgdm->edgeMap[index].startEdge = edgeNum;

		if(edgeIdx >= 0 && edgeFlags)
			edgeFlags[edgeIdx] = medge[edgeIdx].flag;

		/* set the edge base vert */
		*((int*)ccgSubSurf_getEdgeUserData(ss, e)) = vertNum;

		for(x = 1; x < edgeSize - 1; x++) {
			float w[2];
			w[1] = (float) x / (edgeSize - 1);
			w[0] = 1 - w[1];
			DM_interp_vert_data(dm, &ccgdm->dm, vertIdx, w, 2, vertNum);
			if (vertOrigIndex) {
				*vertOrigIndex = ORIGINDEX_NONE;
				++vertOrigIndex;
			}
			++vertNum;
		}

		for(i = 0; i < numFinalEdges; ++i) {
			if (has_edge_origindex) {
				*(int *)DM_get_edge_data(&ccgdm->dm, edgeNum + i,
			                         CD_ORIGINDEX) = mapIndex;
			}
		}

		edgeNum += numFinalEdges;
	}

	if(useSubsurfUv) {
		CustomData *ldata = &ccgdm->dm.loopData;
		CustomData *dmldata = &dm->loopData;
		int numlayer = CustomData_number_of_layers(ldata, CD_MLOOPUV);
		int dmnumlayer = CustomData_number_of_layers(dmldata, CD_MLOOPUV);

		for (i=0; i<numlayer && i<dmnumlayer; i++)
			set_subsurf_uv(ss, dm, &ccgdm->dm, i);
	}

	for(index = 0; index < totvert; ++index) {
		CCGVert *v = ccgdm->vertMap[index].vert;
		int mapIndex = ccgDM_getVertMapIndex(ccgdm->ss, v);
		int vidx;

		vidx = GET_INT_FROM_POINTER(ccgSubSurf_getVertVertHandle(v));

		ccgdm->vertMap[index].startVert = vertNum;

		/* set the vert base vert */
		*((int*) ccgSubSurf_getVertUserData(ss, v)) = vertNum;

		DM_copy_vert_data(dm, &ccgdm->dm, vidx, vertNum, 1);

		if (vertOrigIndex) {
			*vertOrigIndex = mapIndex;
			++vertOrigIndex;
		}
		++vertNum;
	}

	ccgdm->dm.numVertData = vertNum;
	ccgdm->dm.numEdgeData = edgeNum;
	ccgdm->dm.numFaceData = faceNum;
	ccgdm->dm.numLoopData = loopindex2;
	ccgdm->dm.numPolyData = faceNum;

	BLI_array_free(vertidx);
	BLI_array_free(loopidx);
	free_ss_weights(&wtable);

	return ccgdm;
}

/***/

struct DerivedMesh *subsurf_make_derived_from_derived(
						struct DerivedMesh *dm,
						struct SubsurfModifierData *smd,
						int useRenderParams, float (*vertCos)[3],
						int isFinalCalc, int forEditMode, int inEditMode)
{
	int useSimple = smd->subdivType == ME_SIMPLE_SUBSURF;
	int useAging = smd->flags & eSubsurfModifierFlag_DebugIncr;
	int useSubsurfUv = smd->flags & eSubsurfModifierFlag_SubsurfUv;
	int drawInteriorEdges = !(smd->flags & eSubsurfModifierFlag_ControlEdges);
	CCGDerivedMesh *result = NULL;

	if(forEditMode) {
		int levels= (smd->modifier.scene)? get_render_subsurf_level(&smd->modifier.scene->r, smd->levels): smd->levels;

		smd->emCache = _getSubSurf(smd->emCache, levels, useAging, 0,
								   useSimple);
		ss_sync_from_derivedmesh(smd->emCache, dm, vertCos, useSimple);

		result = getCCGDerivedMesh(smd->emCache,
								   drawInteriorEdges,
								   useSubsurfUv, dm);
	} else if(useRenderParams) {
		/* Do not use cache in render mode. */
		CCGSubSurf *ss;
		int levels= (smd->modifier.scene)? get_render_subsurf_level(&smd->modifier.scene->r, smd->renderLevels): smd->renderLevels;

		if(levels == 0)
			return dm;
		
		ss = _getSubSurf(NULL, levels, 0, 1, useSimple);

		ss_sync_from_derivedmesh(ss, dm, vertCos, useSimple);

		result = getCCGDerivedMesh(ss,
			drawInteriorEdges, useSubsurfUv, dm);

		result->freeSS = 1;
	} else {
		int useIncremental = 1; //(smd->flags & eSubsurfModifierFlag_Incremental);
		int useAging = smd->flags & eSubsurfModifierFlag_DebugIncr;
		int levels= (smd->modifier.scene)? get_render_subsurf_level(&smd->modifier.scene->r, smd->levels): smd->levels;
		CCGSubSurf *ss;

		/* It is quite possible there is a much better place to do this. It
		 * depends a bit on how rigourously we expect this function to never
		 * be called in editmode. In semi-theory we could share a single
		 * cache, but the handles used inside and outside editmode are not
		 * the same so we would need some way of converting them. Its probably
		 * not worth the effort. But then why am I even writing this long
		 * comment that no one will read? Hmmm. - zr
		 *
		 * Addendum: we can't really ensure that this is never called in edit
		 * mode, so now we have a parameter to verify it. - brecht
		 */
		if(!inEditMode && smd->emCache) {
			ccgSubSurf_free(smd->emCache);
			smd->emCache = NULL;
		}

		if(useIncremental && isFinalCalc) {
			smd->mCache = ss = _getSubSurf(smd->mCache, levels,
										   useAging, 0, useSimple);

			if (!ss_sync_from_derivedmesh(ss, dm, vertCos, useSimple)) {
				//ccgSubSurf_free(smd->mCache);
				smd->mCache = ss = _getSubSurf(NULL, levels,
											   useAging, 0, useSimple);
				
				ss_sync_from_derivedmesh(ss, dm, vertCos, useSimple);
	
			}

			result = getCCGDerivedMesh(smd->mCache,
									   drawInteriorEdges,
									   useSubsurfUv, dm);
		} else {
			if (smd->mCache && isFinalCalc) {
				ccgSubSurf_free(smd->mCache);
				smd->mCache = NULL;
			}

			ss = _getSubSurf(NULL, levels, 0, 1, useSimple);
			ss_sync_from_derivedmesh(ss, dm, vertCos, useSimple);

			result = getCCGDerivedMesh(ss, drawInteriorEdges, useSubsurfUv, dm);

			if(isFinalCalc)
				smd->mCache = ss;
			else
				result->freeSS = 1;
		}
	}

	return (DerivedMesh*)result;
}

void subsurf_calculate_limit_positions(Mesh *me, float (*positions_r)[3]) 
{
	/* Finds the subsurf limit positions for the verts in a mesh 
	 * and puts them in an array of floats. Please note that the 
	 * calculated vert positions is incorrect for the verts 
	 * on the boundary of the mesh.
	 */
	CCGSubSurf *ss = _getSubSurf(NULL, 1, 0, 1, 0);
	float edge_sum[3], face_sum[3];
	CCGVertIterator *vi;
	DerivedMesh *dm = CDDM_from_mesh(me, NULL);

	ss_sync_from_derivedmesh(ss, dm, NULL, 0);

	vi = ccgSubSurf_getVertIterator(ss);
	for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
		CCGVert *v = ccgVertIterator_getCurrent(vi);
		int idx = GET_INT_FROM_POINTER(ccgSubSurf_getVertVertHandle(v));
		int N = ccgSubSurf_getVertNumEdges(v);
		int numFaces = ccgSubSurf_getVertNumFaces(v);
		float *co;
		int i;

		edge_sum[0]= edge_sum[1]= edge_sum[2]= 0.0;
		face_sum[0]= face_sum[1]= face_sum[2]= 0.0;

		for (i=0; i<N; i++) {
			CCGEdge *e = ccgSubSurf_getVertEdge(v, i);
			add_v3_v3v3(edge_sum, edge_sum, ccgSubSurf_getEdgeData(ss, e, 1));
		}
		for (i=0; i<numFaces; i++) {
			CCGFace *f = ccgSubSurf_getVertFace(v, i);
			add_v3_v3(face_sum, ccgSubSurf_getFaceCenterData(f));
		}

		/* ad-hoc correction for boundary vertices, to at least avoid them
		   moving completely out of place (brecht) */
		if(numFaces && numFaces != N)
			mul_v3_fl(face_sum, (float)N/(float)numFaces);

		co = ccgSubSurf_getVertData(ss, v);
		positions_r[idx][0] = (co[0]*N*N + edge_sum[0]*4 + face_sum[0])/(N*(N+5));
		positions_r[idx][1] = (co[1]*N*N + edge_sum[1]*4 + face_sum[1])/(N*(N+5));
		positions_r[idx][2] = (co[2]*N*N + edge_sum[2]*4 + face_sum[2])/(N*(N+5));
	}
	ccgVertIterator_free(vi);

	ccgSubSurf_free(ss);

	dm->release(dm);
}

