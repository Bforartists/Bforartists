#ifdef USE_CCGSUBSURFLIB

#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"

#include "BKE_bad_level_calls.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_subsurf.h"
#include "BKE_displist.h"

#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_arithb.h"
#include "BLI_linklist.h"
#include "BLI_memarena.h"

#include "CCGSubSurf.h"

typedef struct _SubSurf {
	CCGSubSurf *subSurf;

	int controlType;
#define SUBSURF_CONTROLTYPE_MESH		1
#define SUBSURF_CONTROLTYPE_EDITMESH	2

		/* used by editmesh control type */
	EditMesh *em;

		/* used by mesh control type */
	Mesh *me;
	float *extverts;
} SubSurf;

static void _subsurfNew_meshIFC_vertDataCopy(CCGMeshHDL mv, void *tv, void *av) {
	float *t= tv, *a= av;
	t[0]= a[0];
	t[1]= a[1];
	t[2]= a[2];
}
static int _subsurfNew_meshIFC_vertDataEqual(CCGMeshHDL mv, void *av, void *bv) {
	float *a= av, *b= bv;
	return (a[0]==b[0] && a[1]==b[1] && a[2]==b[2]);
}
static void _subsurfNew_meshIFC_vertDataZero(CCGMeshHDL mv, void *tv) {
	float *t= tv;
	t[0]= t[1]= t[2]= 0.0;
}
static void _subsurfNew_meshIFC_vertDataAdd(CCGMeshHDL mv, void *tav, void *bv) {
	float *ta= tav, *b= bv;
	ta[0]+= b[0];
	ta[1]+= b[1];
	ta[2]+= b[2];
}
static void _subsurfNew_meshIFC_vertDataSub(CCGMeshHDL mv, void *tav, void *bv) {
	float *ta= tav, *b= bv;
	ta[0]-= b[0];
	ta[1]-= b[1];
	ta[2]-= b[2];
}
static void _subsurfNew_meshIFC_vertDataMulN(CCGMeshHDL mv, void *tav, double n) {
	float *ta= tav;
	ta[0]*= (float) n;
	ta[1]*= (float) n;
	ta[2]*= (float) n;
}
static void _subsurfNew_meshIFC_ifc_vertDataAvg4(CCGMeshHDL mv, void *tv, void *av, void *bv, void *cv, void *dv) {
	float *t= tv, *a= av, *b= bv, *c= cv, *d= dv;
	t[0] = (a[0]+b[0]+c[0]+d[0])*0.25f;
	t[1] = (a[1]+b[1]+c[1]+d[1])*0.25f;
	t[2] = (a[2]+b[2]+c[2]+d[2])*0.25f;
}

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
static void arena_free(CCGAllocatorHDL a, void *ptr) {
}
static void arena_release(CCGAllocatorHDL a) {
	BLI_memarena_free(a);
}

static CCGSubSurf *_getSubSurf(SubSurf *ss, int subdivLevels) {
	CCGMeshIFC ifc;
	CCGAllocatorIFC allocatorIFC, *allocatorIFCp;
	CCGAllocatorHDL allocator;

	ifc.vertUserSize = 4;
	ifc.edgeUserSize = 4;
	ifc.faceUserSize = 0;
	ifc.vertDataSize= 12;
	ifc.vertDataZero= _subsurfNew_meshIFC_vertDataZero;
	ifc.vertDataEqual= _subsurfNew_meshIFC_vertDataEqual;
	ifc.vertDataCopy= _subsurfNew_meshIFC_vertDataCopy;
	ifc.vertDataAdd= _subsurfNew_meshIFC_vertDataAdd;
	ifc.vertDataSub= _subsurfNew_meshIFC_vertDataSub;
	ifc.vertDataMulN= _subsurfNew_meshIFC_vertDataMulN;
	ifc.vertDataAvg4= _subsurfNew_meshIFC_ifc_vertDataAvg4;

	allocatorIFC.alloc = arena_alloc;
	allocatorIFC.realloc = arena_realloc;
	allocatorIFC.free = arena_free;
	allocatorIFC.release = arena_release;
	allocatorIFCp = &allocatorIFC;
	allocator = BLI_memarena_new((1<<16));

	return ccgSubSurf_new(&ifc, ss, subdivLevels, allocatorIFCp, allocator);
}

static SubSurf *subSurf_fromEditmesh(EditMesh *em, int subdivLevels) {
	SubSurf *ss= MEM_mallocN(sizeof(*ss), "ss");

	ss->controlType= SUBSURF_CONTROLTYPE_EDITMESH;
	ss->subSurf= _getSubSurf(ss, subdivLevels);
	ss->em = em;

	return ss;
}

static SubSurf *subSurf_fromMesh(Mesh *me, float *extverts, int subdivLevels) {
	SubSurf *ss= MEM_mallocN(sizeof(*ss), "ss");

	ss->controlType= SUBSURF_CONTROLTYPE_MESH;
	ss->subSurf= _getSubSurf(ss, subdivLevels);
	ss->me= me;
	ss->extverts= extverts;

	ccgSubSurf_setAllowEdgeCreation(ss->subSurf, 1);

	return ss;
}

void subSurf_free(SubSurf *ss) {
	ccgSubSurf_free(ss->subSurf);
	MEM_freeN(ss);
}

static void Vec3Cpy(float *t, float *a) {
	t[0]= a[0];
	t[1]= a[1];
	t[2]= a[2];
}

static void VColAvgT(unsigned char *t, unsigned char *a, unsigned char *b) {
	t[0]= (a[0]+b[0])>>1;
	t[1]= (a[1]+b[1])>>1;
	t[2]= (a[2]+b[2])>>1;
	t[3]= (a[3]+b[3])>>1;
}

static int getEdgeIndex(CCGSubSurf *ss, CCGEdge *e, int x, int edgeSize) {
	CCGVert *v0 = ccgSubSurf_getEdgeVert0(ss, e);
	CCGVert *v1 = ccgSubSurf_getEdgeVert1(ss, e);
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
static int getFaceIndex(CCGSubSurf *ss, CCGFace *f, int S, int x, int y, int faceBase, int edgeSize, int gridSize) {
	int numVerts = ccgSubSurf_getFaceNumVerts(ss, f);

	if (x==gridSize-1 && y==gridSize-1) {
		CCGVert *v = ccgSubSurf_getFaceVert(ss, f, S);
		return *((int*) ccgSubSurf_getVertUserData(ss, v));
	} else if (x==gridSize-1) {
		CCGVert *v = ccgSubSurf_getFaceVert(ss, f, S);
		CCGEdge *e = ccgSubSurf_getFaceEdge(ss, f, S);
		int edgeBase = *((int*) ccgSubSurf_getEdgeUserData(ss, e));
		if (v==ccgSubSurf_getEdgeVert0(ss, e)) {
			return edgeBase + (gridSize-1-y)-1;
		} else {
			return edgeBase + (edgeSize-2-1)-((gridSize-1-y)-1);
		}
	} else if (y==gridSize-1) {
		CCGVert *v = ccgSubSurf_getFaceVert(ss, f, S);
		CCGEdge *e = ccgSubSurf_getFaceEdge(ss, f, (S+numVerts-1)%numVerts);
		int edgeBase = *((int*) ccgSubSurf_getEdgeUserData(ss, e));
		if (v==ccgSubSurf_getEdgeVert0(ss, e)) {
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
static DispListMesh *subSurf_createDispListMesh(SubSurf *ssm, int doOptEdges, int doHandles) {
	CCGSubSurf *ss= ssm->subSurf;
	DispListMesh *dlm= MEM_callocN(sizeof(*dlm), "dlm");
	int edgeSize= ccgSubSurf_getEdgeSize(ss);
	int gridSize= ccgSubSurf_getGridSize(ss);
	int edgeIndexBase, edgeBase, faceIndexBase, faceBase;
	int i, j, k, S, x, y;
	int vertBase= 0;
	MFace *mf;
	CCGVertIterator *vi;
	CCGEdgeIterator *ei;
	CCGFaceIterator *fi;
	
	if (doOptEdges) {
		dlm->flag= ME_OPT_EDGES;
	} else {
		dlm->flag= 0;
	}

	dlm->totvert= ccgSubSurf_getNumFinalVerts(ss);
	if (doHandles) {
		dlm->totvert+= ccgSubSurf_getNumVerts(ss);
	}

	dlm->totface= 0;
	ei= ccgSubSurf_getEdgeIterator(ss);
	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e= ccgEdgeIterator_getCurrent(ei);
		if (!ccgSubSurf_getEdgeNumFaces(ss, e)) {
			dlm->totface+= edgeSize-1;
		}
	}
	ccgEdgeIterator_free(ei);
	dlm->totface+= ccgSubSurf_getNumFinalFaces(ss);
	if (doHandles) {
		dlm->totface+= ccgSubSurf_getNumVerts(ss);
	}

	dlm->mvert= MEM_callocN(dlm->totvert*sizeof(*dlm->mvert), "dlm->mvert");
	dlm->mface= MEM_callocN(dlm->totface*sizeof(*dlm->mface), "dlm->mface");
	if ((ssm->controlType==SUBSURF_CONTROLTYPE_MESH) && ssm->me->tface) {
		dlm->tface= MEM_callocN(dlm->totface*sizeof(*dlm->tface), "dlm->tface");
		dlm->mcol= NULL;
	} else if ((ssm->controlType==SUBSURF_CONTROLTYPE_MESH) && ssm->me->mcol) {
		dlm->tface= NULL;
		dlm->mcol= MEM_mallocN(dlm->totface*4*sizeof(*dlm->mcol), "dlm->mcol");
	} else {
		dlm->tface= NULL;
		dlm->mcol= NULL;
	}

	i=0;
	if (doHandles) {
		vi= ccgSubSurf_getVertIterator(ss);
		for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
			CCGVert *v= ccgVertIterator_getCurrent(vi);
			Vec3Cpy(dlm->mvert[i].co, ccgSubSurf_getVertLevelData(ss, v, 0));
			i++;
		}
		ccgVertIterator_free(vi);
	}

		// load vertices

	vertBase = i;
	vi= ccgSubSurf_getVertIterator(ss);
	for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
		CCGVert *v = ccgVertIterator_getCurrent(vi);
		Vec3Cpy(dlm->mvert[i].co, ccgSubSurf_getVertData(ss, v));
		*((int*) ccgSubSurf_getVertUserData(ss, v)) = i++;
	}
	ccgVertIterator_free(vi);

	edgeIndexBase = edgeBase = i;
	ei= ccgSubSurf_getEdgeIterator(ss);
	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e= ccgEdgeIterator_getCurrent(ei);
		int x;

		for (x=1; x<edgeSize-1; x++) {
			Vec3Cpy(dlm->mvert[i++].co, ccgSubSurf_getEdgeData(ss, e, x));
		}

		*((int*) ccgSubSurf_getEdgeUserData(ss, e)) = edgeBase;
		edgeBase += edgeSize-2;
	}
	ccgEdgeIterator_free(ei);

	faceIndexBase = i;
	fi= ccgSubSurf_getFaceIterator(ss);
	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f= ccgFaceIterator_getCurrent(fi);
		int x, y, S, numVerts= ccgSubSurf_getFaceNumVerts(ss, f);

		Vec3Cpy(dlm->mvert[i++].co, ccgSubSurf_getFaceCenterData(ss, f));
		
		for (S=0; S<numVerts; S++) {
			for (x=1; x<gridSize-1; x++) {
				Vec3Cpy(dlm->mvert[i++].co, ccgSubSurf_getFaceGridEdgeData(ss, f, S, x));
			}
		}

		for (S=0; S<numVerts; S++) {
			for (y=1; y<gridSize-1; y++) {
				for (x=1; x<gridSize-1; x++) {
					Vec3Cpy(dlm->mvert[i++].co, ccgSubSurf_getFaceGridData(ss, f, S, x, y));
				}
			}
		}
	}
	ccgFaceIterator_free(fi);

		// load edges

	i=0;
	if (doHandles) {
		vi= ccgSubSurf_getVertIterator(ss);
		for (; !ccgVertIterator_isStopped(vi); ccgVertIterator_next(vi)) {
			CCGVert *v= ccgVertIterator_getCurrent(vi);
			mf= &dlm->mface[i];
			mf->v1= i;
			mf->v2= vertBase + i;
			mf->edcode= ME_V1V2;
			i++;
		}
		ccgVertIterator_free(vi);
	}
	ei= ccgSubSurf_getEdgeIterator(ss);
	for (; !ccgEdgeIterator_isStopped(ei); ccgEdgeIterator_next(ei)) {
		CCGEdge *e= ccgEdgeIterator_getCurrent(ei);
		if (!ccgSubSurf_getEdgeNumFaces(ss, e)) {
			for (x=0; x<edgeSize-1; x++) {
				mf= &dlm->mface[i];
				mf->v1= getEdgeIndex(ss, e, x, edgeSize);
				mf->v2= getEdgeIndex(ss, e, x+1, edgeSize);
				mf->edcode= ME_V1V2;
				i++;
			}
		}
	}
	ccgEdgeIterator_free(ei);

		// load faces

	fi= ccgSubSurf_getFaceIterator(ss);
	faceBase= faceIndexBase;
	for (; !ccgFaceIterator_isStopped(fi); ccgFaceIterator_next(fi)) {
		CCGFace *f= ccgFaceIterator_getCurrent(fi);
		int numVerts= ccgSubSurf_getFaceNumVerts(ss, f);
		float edge_data[4][6];
		float corner_data[4][6];
		float center_data[6]= {0};
		int numDataComponents;
		TFace *origTFace= NULL;
		MCol *origMCol= NULL;
		int mat_nr;
		int flag;

		if (ssm->controlType==SUBSURF_CONTROLTYPE_MESH) {
			int origIdx = (int) ccgSubSurf_getFaceFaceHandle(ss, f);
			MFace *origMFace= &((MFace*) ssm->me->mface)[origIdx];
			if (ssm->me->tface)
				origTFace= &((TFace*)ssm->me->tface)[origIdx];
			if (ssm->me->mcol)
				origMCol= &ssm->me->mcol[origIdx*4];
			mat_nr= origMFace->mat_nr;
			flag= origMFace->flag;
		} else {
			EditFace *ef= ccgSubSurf_getFaceFaceHandle(ss, f);
			mat_nr= ef->mat_nr;
			flag= ef->flag;
		}

		if (origTFace) {
			for (S=0; S<numVerts; S++) {
				unsigned char *col= (unsigned char*) &origTFace->col[S];
				corner_data[S][0]= col[0]/255.0f;
				corner_data[S][1]= col[1]/255.0f;
				corner_data[S][2]= col[2]/255.0f;
				corner_data[S][3]= col[3]/255.0f;
				corner_data[S][4]= origTFace->uv[S][0];
				corner_data[S][5]= origTFace->uv[S][1];
			}
			numDataComponents= 6;
		} else if (origMCol) {
			for (S=0; S<numVerts; S++) {
				unsigned char *col= (unsigned char*) &origMCol[S];
				corner_data[S][0]= col[0]/255.0f;
				corner_data[S][1]= col[1]/255.0f;
				corner_data[S][2]= col[2]/255.0f;
				corner_data[S][3]= col[3]/255.0f;
			}
			numDataComponents= 4;
		} else {
			numDataComponents= 0;
		}

		for (S=0; S<numVerts; S++) {
			for (k=0; k<numDataComponents; k++) {
				edge_data[S][k]= (corner_data[S][k] + corner_data[(S+1)%numVerts][k])*0.5f;
				center_data[k]+= corner_data[S][k];
			}
		}
		for (k=0; k<numDataComponents; k++) {
			center_data[k]/= numVerts;
		}

		for (S=0; S<numVerts; S++) {
			int prevS= (S-1+numVerts)%numVerts;
			for (y=0; y<gridSize-1; y++) {
				for (x=0; x<gridSize-1; x++) {
					mf= &dlm->mface[i];
					mf->v1= getFaceIndex(ss, f, S, x+0, y+1, faceBase, edgeSize, gridSize);
					mf->v2= getFaceIndex(ss, f, S, x+1, y+1, faceBase, edgeSize, gridSize);
					mf->v3= getFaceIndex(ss, f, S, x+1, y+0, faceBase, edgeSize, gridSize);
					mf->v4= getFaceIndex(ss, f, S, x+0, y+0, faceBase, edgeSize, gridSize);
					mf->mat_nr= mat_nr;
					mf->flag= flag;
					mf->edcode= 0;

					if (doOptEdges) {
						if (x+1==gridSize-1)
							mf->edcode|= ME_V2V3;
						if (y+1==gridSize-1)
							mf->edcode|= ME_V1V2;
					}

					for (j=0; j<4; j++) {
						int fx= x + (j==1||j==2);
						int fy= y + (j==0||j==1);
						float x_v= (float) fx/(gridSize-1);
						float y_v= (float) fy/(gridSize-1);
						float data[6];

						for (k=0; k<numDataComponents; k++) {
							data[k]= (center_data[k]*(1.0f-x_v) + edge_data[S][k]*x_v)*(1.0f-y_v) + 
									(edge_data[prevS][k]*(1.0f-x_v) + corner_data[S][k]*x_v)*y_v;
						}

						if (dlm->tface) {
							TFace *tf= &dlm->tface[i];
							unsigned char col[4];
							col[0]= (int) (data[0]*255);
							col[1]= (int) (data[1]*255);
							col[2]= (int) (data[2]*255);
							col[3]= (int) (data[3]*255);
							tf->col[j]= *((unsigned int*) col);
							tf->uv[j][0]= data[4];
							tf->uv[j][1]= data[5];
						} else if (dlm->mcol) {
							unsigned char *col= (unsigned char*) &dlm->mcol[i*4+j];
							col[0]= (int) (data[0]*255);
							col[1]= (int) (data[1]*255);
							col[2]= (int) (data[2]*255);
							col[3]= (int) (data[3]*255);
						}
					}
					if (dlm->tface) {
						TFace *tf= &dlm->tface[i];
						tf->tpage= origTFace->tpage;
						tf->flag= origTFace->flag;
						tf->transp= origTFace->transp;
						tf->mode= origTFace->mode;
						tf->tile= origTFace->tile;
					}

					i++;
				}
			}
		}

		faceBase += 1 + numVerts*((gridSize-2) + (gridSize-2)*(gridSize-2));
	}
	ccgFaceIterator_free(fi);

	displistmesh_calc_vert_normals(dlm);

	return dlm;
}

static void subSurf_sync(SubSurf *ss) {
	ccgSubSurf_initFullSync(ss->subSurf);

	if (ss->controlType==SUBSURF_CONTROLTYPE_MESH) {
		int i, fVerts[4];

		for (i=0; i<ss->me->totvert; i++) {
			if (ss->extverts) {
				ccgSubSurf_syncVert(ss->subSurf, (CCGVertHDL) i, &ss->extverts[i*3]);
			} else {
				ccgSubSurf_syncVert(ss->subSurf, (CCGVertHDL) i, ss->me->mvert[i].co);
			}
		}

		for (i=0; i<ss->me->totface; i++) {
			MFace *mf = &((MFace*) ss->me->mface)[i];

			if (!mf->v3) {
				ccgSubSurf_syncEdge(ss->subSurf, (CCGEdgeHDL) i, (CCGVertHDL) mf->v1, (CCGVertHDL) mf->v2);
			}
		}

		for (i=0; i<ss->me->totface; i++) {
			MFace *mf = &((MFace*) ss->me->mface)[i];

			if (mf->v3) {
				fVerts[0] = mf->v1;
				fVerts[1] = mf->v2;
				fVerts[2] = mf->v3;
				fVerts[3] = mf->v4;

				ccgSubSurf_syncFace(ss->subSurf, (CCGFaceHDL) i, fVerts[3]?4:3, (CCGVertHDL*) fVerts);
			}
		}
	} else {
		EditVert *v, *fVerts[4];
		EditEdge *e;
		EditFace *f;

		for (v=ss->em->verts.first; v; v=v->next) {
			ccgSubSurf_syncVert(ss->subSurf, v, v->co);
		}

		for (e=ss->em->edges.first; e; e=e->next) {
			ccgSubSurf_syncEdge(ss->subSurf, e, e->v1, e->v2);
		}

		for (f=ss->em->faces.first; f; f=f->next) {
			fVerts[0] = f->v1;
			fVerts[1] = f->v2;
			fVerts[2] = f->v3;
			fVerts[3] = f->v4;

			ccgSubSurf_syncFace(ss->subSurf, f, f->v4?4:3, fVerts);
		}
	}

	ccgSubSurf_processSync(ss->subSurf);
}

DispListMesh *subsurf_ccg_make_dispListMesh_from_editmesh(EditMesh *em, int subdivLevels, int flags) {
	SubSurf *ss= subSurf_fromEditmesh(em, subdivLevels);
	DispListMesh *dlm;

	subSurf_sync(ss);

	dlm= subSurf_createDispListMesh(ss, (flags&ME_OPT_EDGES)?1:0, (flags&ME_OPT_EDGES)?1:0);

	subSurf_free(ss);

	return dlm;
}

DispListMesh *subsurf_ccg_make_dispListMesh_from_mesh(Mesh *me, float *extverts, int subdivLevels, int flags) {
	SubSurf *ss= subSurf_fromMesh(me, extverts, subdivLevels);
	DispListMesh *dlm;

	subSurf_sync(ss);

	dlm= subSurf_createDispListMesh(ss, (flags&ME_OPT_EDGES)?1:0, 0);
	
	subSurf_free(ss);
	
	return dlm;
}

#endif
