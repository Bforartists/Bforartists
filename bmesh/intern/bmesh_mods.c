#include <limits.h>
#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"
#include "BKE_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_linklist.h"
#include "BLI_ghash.h"
#include "BLI_arithb.h"

#include "bmesh.h"
#include "bmesh_private.h"


/*
 * BME_MODS.C
 *
 * This file contains functions for locally modifying
 * the topology of existing mesh data. (split, join, flip ect).
 *
*/

/**
 *			bmesh_dissolve_disk
 *
 *  Turns the face region surrounding a manifold vertex into 
 *  A single polygon.
 *
 * 
 * Example:
 * 
 *          |=========|             |=========|
 *          |  \   /  |             |         |
 * Before:  |    V    |      After: |         |
 *          |  /   \  |             |         |
 *          |=========|             |=========|
 * 
 * 
 *  Returns -
 *	1 for success, 0 for failure.
 */

void BM_Dissolve_Disk(BMesh *bm, BMVert *v){
	BMFace *f, *f2;
	BMEdge *e, *keepedge=NULL, *baseedge=NULL;
	int done, len;

	if(BM_Nonmanifold_Vert(bm, v)) return;
	
	if(v->edge){
		/*v->edge we keep, what else?*/
		e = v->edge;
		do{
			e = bmesh_disk_nextedge(e,v);
			if(!(BM_Edge_Share_Faces(e, v->edge))){
				keepedge = e;
				baseedge = v->edge;
				break;
			}
		}while(e != v->edge);
	}
	
	if(keepedge){
		done = 0;
		while(!done){
			done = 1;
			e = v->edge;
			do{
				f = NULL;
				len = bmesh_cycle_length(&(e->loop->radial));
				if(len == 2 && (e!=baseedge) && (e!=keepedge))
					f = BM_Join_Faces(bm, e->loop->f, ((BMLoop*)(e->loop->radial.next->data))->f, e, 0, 0); 
				if(f){
					done = 0;
					break;
				}
			}while(e != v->edge);
		}

		/*get remaining two faces*/
		f = v->edge->loop->f;
		f2 = ((BMLoop*)f->loopbase->radial.next->data)->f;
		/*collapse the vertex*/
		BM_Collapse_Vert(bm, baseedge, v, 1.0, 0);
	}
}

/**
 *			bmesh_join_faces
 *
 *  joins two adjacenct faces togather. If weldUVs == 1
 *  and the uv/vcols of the two faces are non-contigous, the
 *  per-face properties of f2 will be transformed into place
 *  around f1.
 * 
 *  Returns -
 *	BMFace pointer
 */
 
BMFace *BM_Join_Faces(BMesh *bm, BMFace *f1, BMFace *f2, BMEdge *e, int calcnorm, int weldUVs) {

	BMLoop *l1, *l2;
	BMEdge *jed=NULL;
	
	jed = e;
	if(!jed){
		/*search for an edge that has both these faces in its radial cycle*/
		l1 = f1->loopbase;
		do{
			if( ((BMLoop*)l1->radial.next->data)->f == f2 ){
				jed = l1->e;
				break;
			}
			l1 = ((BMLoop*)(l1->head.next));
		}while(l1!=f1->loopbase);
	}

	l1 = jed->loop;
	l2 = l1->radial.next->data;
	if (l1->v == l2->v) {
		bmesh_loop_reverse(bm, f2);
	}

	return bmesh_jfke(bm, f1, f2, jed);
}

/**
 *			BM_split_face
 *
 *  Splits a single face into two.
 * 
 *  Returns -
 *	BMFace pointer
 */
 
BMFace *BM_Split_Face(BMesh *bm, BMFace *f, BMVert *v1, BMVert *v2, BMLoop **nl, BMEdge *example, int calcnorm)
{
	BMFace *nf;
	nf = bmesh_sfme(bm,f,v1,v2,nl);
	
	/*
	nf->flag = f->flag;
	if (example->flag & SELECT) f->flag |= BMESH_SELECT;
	nf->h = f->h;
	nf->mat_nr = f->mat_nr;
	if (nl && example) {
		(*nl)->e->flag = example->flag;
		(*nl)->e->h = example->h;
		(*nl)->e->crease = example->crease;
		(*nl)->e->bweight = example->bweight;
	}
	*/
	return nf;
}

/**
 *			bmesh_collapse_vert
 *
 *  Collapses a vertex that has only two manifold edges
 *  onto a vertex it shares an edge with. Fac defines
 *  the amount of interpolation for Custom Data.
 *
 *  Note that this is not a general edge collapse function. For
 *  that see BM_manifold_edge_collapse 
 *
 *  TODO:
 *    Insert error checking for KV valance.
 *
 *  Returns -
 *	Nothing
 */
 
void BM_Collapse_Vert(BMesh *bm, BMEdge *ke, BMVert *kv, float fac, int calcnorm){
	void *src[2];
	float w[2];
	BMLoop *l=NULL, *kvloop=NULL, *tvloop=NULL;
	BMVert *tv = bmesh_edge_getothervert(ke,kv);

	w[0] = 1.0f - fac;
	w[1] = fac;

	if(ke->loop){
		l = ke->loop;
		do{
			if(l->v == tv && ((BMLoop*)(l->head.next))->v == kv){
				tvloop = l;
				kvloop = ((BMLoop*)(l->head.next));

				src[0] = kvloop->data;
				src[1] = tvloop->data;
				CustomData_bmesh_interp(&bm->ldata, src,w, NULL, 2, kvloop->data); 								
			}
			l=l->radial.next->data;
		}while(l!=ke->loop);
	}
	BM_Data_Interp_From_Verts(bm, kv, tv, kv, fac);   
	bmesh_jekv(bm,ke,kv);
}

/**
 *			BM_split_edge
 *	
 *	Splits an edge. v should be one of the vertices in e and
 *  defines the direction of the splitting operation for interpolation
 *  purposes.
 *
 *  Returns -
 *	Nothing
 */

BMVert *BM_Split_Edge(BMesh *bm, BMVert *v, BMEdge *e, BMEdge **ne, float percent, int calcnorm) {
	BMVert *nv, *v2;
	float len;

	v2 = bmesh_edge_getothervert(e,v);
	nv = bmesh_semv(bm,v,e,ne);
	if (nv == NULL) return NULL;
	VECSUB(nv->co,v2->co,v->co);
	len = VecLength(nv->co);
	VECADDFAC(nv->co,v->co,nv->co,len*percent);
	if (ne) {
		if(bmesh_test_sysflag(&(e->head), BMESH_SELECT)) bmesh_set_sysflag(&((*ne)->head), BMESH_SELECT);
		if(bmesh_test_sysflag(&(e->head), BMESH_HIDDEN)) bmesh_set_sysflag(&((*ne)->head), BMESH_HIDDEN);
	}
	/*v->nv->v2*/
	BM_Data_Facevert_Edgeinterp(bm,v2, v, nv, e, percent);	
	BM_Data_Interp_From_Verts(bm, v2, v, nv, percent);
	return nv;
}

BMVert  *BM_Split_Edge_Multi(BMesh *bm, BMEdge *e, int numcuts)
{
	int i;
	float percent, step,length, vt1[3], v2[3];
	BMVert *nv = NULL;
	
	percent = 0.0;
	step = (1.0/((float)numcuts+1));
	
	length = VecLenf(e->v1->co,e->v2->co);
	VECCOPY(v2,e->v2->co);
	VecSubf(vt1, e->v1->co,  e->v2->co);
	
	for(i=0; i < numcuts; i++){
		percent += step;
		nv = BM_Split_Edge(bm, e->v2, e, NULL, percent, 0);
		VECCOPY(nv->co,vt1);
		VecMulf(nv->co,percent);
		VecAddf(nv->co,v2,nv->co);
	}
	return nv;
}
