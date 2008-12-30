#include <string.h>
#include "bmesh.h"
#include "bmesh_private.h"


/*
 * BMESH_MARK.C
 *
 * Selection routines for bmesh structures.
 * This is actually all old code ripped from
 * editmesh_lib.c and slightly modified to work
 * for bmesh's. This also means that it has some
 * of the same problems.... something that
 * that should be addressed eventually.
 *
*/


/*
 * BMESH SELECTMODE FLUSH
 *
 * Makes sure to flush selections 
 * 'upwards' (ie: all verts of an edge
 * selects the edge and so on). This 
 * should only be called by system and not
 * tool authors.
 *
*/

void bmesh_selectmode_flush(BMesh *bm)
{
	BMEdge *e;
	BMLoop *l;
	BMFace *f;

	BMIter edges;
	BMIter faces;

	int totsel;

	if(bm->selectmode & BMESH_VERT){
		for(e = BMIter_New(&edges, bm, BM_EDGES, bm ); e; e= BMIter_Step(&edges)){
			if(bmesh_test_sysflag(&(e->v1->head), BMESH_SELECT) && bmesh_test_sysflag(&(e->v2->head), BMESH_SELECT)) bmesh_set_sysflag(&(e->head), BMESH_SELECT);
			else bmesh_clear_sysflag(&(e->head), BMESH_SELECT);
		}
		for(f = BMIter_New(&faces, bm, BM_FACES, bm ); f; f= BMIter_Step(&faces)){
			totsel = 0;
			l=f->loopbase;
			do{
				if(bmesh_test_sysflag(&(l->v->head), BMESH_SELECT)) 
					totsel++;
				l = ((BMLoop*)(l->head.next));
			}while(l!=f->loopbase);
			
			if(totsel == f->len) 
				bmesh_set_sysflag(&(f->head), BMESH_SELECT);
			else
				bmesh_clear_sysflag(&(f->head), BMESH_SELECT);
		}
	}
	else if(bm->selectmode & BMESH_EDGE) {
		for(f = BMIter_New(&faces, bm, BM_FACES, bm ); f; f= BMIter_Step(&faces)){
			totsel = 0;
			l=f->loopbase;
			do{
				if(bmesh_test_sysflag(&(l->e->head), BMESH_SELECT)) 
					totsel++;
				l = ((BMLoop*)(l->head.next));
			}while(l!=f->loopbase);
			
			if(totsel == f->len) 
				bmesh_set_sysflag(&(f->head), BMESH_SELECT);
			else 
				bmesh_clear_sysflag(&(f->head), BMESH_SELECT);
		}
	}	
}

/*
 * BMESH SELECT VERT
 *
 * Changes selection state of a single vertex 
 * in a mesh
 *
*/

void BM_Select_Vert(BMesh *bm, BMVert *v, int select)
{
	if(select)
		bmesh_set_sysflag(&(v->head), BMESH_SELECT);
	else 
		bmesh_clear_sysflag(&(v->head), BMESH_SELECT);
}

/*
 * BMESH SELECT EDGE
 *
 * Changes selection state of a single edge
 * in a mesh. Note that this is actually not
 * 100 percent reliable. Deselecting an edge
 * will also deselect both its vertices
 * regardless of the selection state of
 * other edges incident upon it. Fixing this
 * issue breaks multi-select mode though...
 *
*/

void BM_Select_Edge(BMesh *bm, BMEdge *e, int select)
{
	if(select){ 
		bmesh_set_sysflag(&(e->head), BMESH_SELECT);
		bmesh_set_sysflag(&(e->v1->head), BMESH_SELECT);
		bmesh_set_sysflag(&(e->v2->head), BMESH_SELECT);
	}
	else{ 
		bmesh_clear_sysflag(&(e->head), BMESH_SELECT);
		bmesh_clear_sysflag(&(e->v1->head), BMESH_SELECT);
		bmesh_clear_sysflag(&(e->v2->head), BMESH_SELECT);
	}
}

/*
 *
 * BMESH SELECT FACE
 *
 * Changes selection state of a single
 * face in a mesh. This (might) suffer
 * from same problems as edge select
 * code...
 *
*/

void BM_Select_Face(BMesh *bm, BMFace *f, int select)
{
	BMLoop *l;

	if(select){ 
		bmesh_set_sysflag(&(f->head), BMESH_SELECT);
		l = f->loopbase;
		do{
			bmesh_set_sysflag(&(l->v->head), BMESH_SELECT);
			bmesh_set_sysflag(&(l->e->head), BMESH_SELECT);
			l = ((BMLoop*)(l->head.next));
		}while(l != f->loopbase);
	}
	else{ 
		bmesh_clear_sysflag(&(f->head), BMESH_SELECT);
		l = f->loopbase;
		do{
			bmesh_clear_sysflag(&(l->v->head), BMESH_SELECT);
			bmesh_clear_sysflag(&(l->e->head), BMESH_SELECT);
			l = ((BMLoop*)(l->head.next));
		}while(l != f->loopbase);
	}
}

/*
 * BMESH SELECTMODE SET
 *
 * Sets the selection mode for the bmesh
 *
*/

void BM_Selectmode_Set(BMesh *bm, int selectmode)
{
	BMVert *v;
	BMEdge *e;
	BMFace *f;
	
	BMIter verts;
	BMIter edges;
	BMIter faces;
	
	bm->selectmode = selectmode;

	if(bm->selectmode & BMESH_VERT){
		for(e = BMIter_New(&edges, bm, BM_EDGES, bm ); e; e= BMIter_Step(&edges))
			BM_Select_Edge(bm, e, 0);
		for(f = BMIter_New(&faces, bm, BM_FACES, bm ); f; f= BMIter_Step(&faces))
			bmesh_clear_sysflag(&(f->head), 0);
		bmesh_selectmode_flush(bm);
	}
	else if(bm->selectmode & BMESH_EDGE){
		for(v= BMIter_New(&verts, bm, BM_VERTS, bm ); v; v= BMIter_Step(&verts))
			BM_Select_Vert(bm, v, 0);
		for(e= BMIter_New(&edges, bm, BM_EDGES, bm ); e; e= BMIter_Step(&edges)){
			if(bmesh_test_sysflag(&(e->head), BMESH_SELECT))
				BM_Select_Edge(bm, e, 1);
		}
		bmesh_selectmode_flush(bm);
	}
	else if(bm->selectmode & BMESH_FACE){
		for(e = BMIter_New(&edges, bm, BM_EDGES, bm ); e; e= BMIter_Step(&edges))
			BM_Select_Edge(bm, e, 0);
		for(f = BMIter_New(&faces, bm, BM_FACES, bm ); f; f= BMIter_Step(&faces)){
			if(bmesh_test_sysflag(&(f->head), BMESH_SELECT))
				BM_Select_Face(bm, f, 1);
		}
	}
}

int BM_Is_Selected(BMesh *bm, BMHeader *h)
{
	return bmesh_test_sysflag(h, BMESH_SELECT);
}
