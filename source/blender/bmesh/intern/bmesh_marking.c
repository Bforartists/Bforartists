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
 * Contributor(s): Joseph Eagar, Geoffrey Bantle, Campbell Barton
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/intern/bmesh_marking.c
 *  \ingroup bmesh
 *
 * Selection routines for bmesh structures.
 * This is actually all old code ripped from
 * editmesh_lib.c and slightly modified to work
 * for bmesh's. This also means that it has some
 * of the same problems.... something that
 * that should be addressed eventually.
 */

#include "MEM_guardedalloc.h"

#include "BKE_utildefines.h"

#include "BLI_math.h"
#include "BLI_blenlib.h"
#include "BLI_array.h"

#include "bmesh.h"
#include "bmesh_private.h"

#include <string.h>

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

static void recount_totsels(BMesh *bm)
{
	BMIter iter;
	BMHeader *ele;
	int types[3] = {BM_VERTS_OF_MESH, BM_EDGES_OF_MESH, BM_FACES_OF_MESH};
	int *tots[3];
	int i;

	/*recount tot*sel variables*/
	bm->totvertsel = bm->totedgesel = bm->totfacesel = 0;
	tots[0] = &bm->totvertsel;
	tots[1] = &bm->totedgesel;
	tots[2] = &bm->totfacesel;

	for (i=0; i<3; i++) {
		ele = BMIter_New(&iter, bm, types[i], NULL);
		for ( ; ele; ele=BMIter_Step(&iter)) {
			if (BM_TestHFlag(ele, BM_SELECT)) *tots[i] += 1;
		}
	}
}

void BM_SelectMode_Flush(BMesh *bm)
{
	BMEdge *e;
	BMLoop *l;
	BMFace *f;

	BMIter edges;
	BMIter faces;

	int totsel;

	if(bm->selectmode & SCE_SELECT_VERTEX) {
		for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm ); e; e= BMIter_Step(&edges)) {
			if(BM_TestHFlag(e->v1, BM_SELECT) && BM_TestHFlag(e->v2, BM_SELECT) && !BM_TestHFlag(e, BM_HIDDEN)) {
				BM_SetHFlag(e, BM_SELECT);
			}
			else {
				BM_ClearHFlag(e, BM_SELECT);
			}
		}
		for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm ); f; f= BMIter_Step(&faces)) {
			totsel = 0;
			l=(BMLoop*) bm_firstfaceloop(f);
			do{
				if(BM_TestHFlag(l->v, BM_SELECT)) 
					totsel++;
				l = l->next;
			} while(l != bm_firstfaceloop(f));
			
			if(totsel == f->len && !BM_TestHFlag(f, BM_HIDDEN)) {
				BM_SetHFlag(f, BM_SELECT);
			}
			else {
				BM_ClearHFlag(f, BM_SELECT);
			}
		}
	}
	else if(bm->selectmode & SCE_SELECT_EDGE) {
		for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm ); f; f= BMIter_Step(&faces)) {
			totsel = 0;
			l = bm_firstfaceloop(f);
			do{
				if(BM_TestHFlag(&(l->e->head), BM_SELECT)) 
					totsel++;
				l = l->next;
			}while(l!=bm_firstfaceloop(f));
			
			if(totsel == f->len && !BM_TestHFlag(f, BM_HIDDEN)) {
				BM_SetHFlag(f, BM_SELECT);
			}
			else {
				BM_ClearHFlag(f, BM_SELECT);
			}
		}
	}

	/*Remove any deselected elements from the BMEditSelection*/
	BM_validate_selections(bm);

	recount_totsels(bm);
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
	/* BMIter iter; */
	/* BMEdge *e; */

	if (BM_TestHFlag(v, BM_HIDDEN)) {
		return;
	}

	if(select) {
		if (!BM_TestHFlag(v, BM_SELECT)) {
			bm->totvertsel += 1;
			BM_SetHFlag(v, BM_SELECT);
		}
	} else {
		if (BM_TestHFlag(v, BM_SELECT)) {
			bm->totvertsel -= 1;
			BM_ClearHFlag(v, BM_SELECT);
		}
	}
}

/*
 * BMESH SELECT EDGE
 *
 * Changes selection state of a single edge
 * in a mesh.
 *
*/

void BM_Select_Edge(BMesh *bm, BMEdge *e, int select)
{
	if (BM_TestHFlag(e, BM_HIDDEN)) {
		return;
	}

	if(select){
		if (!BM_TestHFlag(e, BM_SELECT)) bm->totedgesel += 1;

		BM_SetHFlag(&(e->head), BM_SELECT);
		BM_Select(bm, e->v1, 1);
		BM_Select(bm, e->v2, 1);
	}else{ 
		if (BM_TestHFlag(e, BM_SELECT)) bm->totedgesel -= 1;
		BM_ClearHFlag(&(e->head), BM_SELECT);

		if(
		        bm->selectmode == SCE_SELECT_EDGE ||
		        bm->selectmode == SCE_SELECT_FACE ||
		        bm->selectmode == (SCE_SELECT_EDGE | SCE_SELECT_FACE)){

			BMIter iter;
			BMVert *verts[2] = {e->v1, e->v2};
			BMEdge *e2;
			int i;

			for(i = 0; i < 2; i++){
				int deselect = 1;

				for(e2 = BMIter_New(&iter, bm, BM_EDGES_OF_VERT, verts[i]);
				    e2; e2 = BMIter_Step(&iter)){
					if(e2 == e){
						continue;
					}

					if (BM_TestHFlag(e2, BM_SELECT)){
						deselect = 0;
						break;
					}
				}

				if(deselect) BM_Select_Vert(bm, verts[i], 0);
			}
		}else{
			BM_Select(bm, e->v1, 0);
			BM_Select(bm, e->v2, 0);
		}

	}
}

/*
 *
 * BMESH SELECT FACE
 *
 * Changes selection state of a single
 * face in a mesh.
 *
*/

void BM_Select_Face(BMesh *bm, BMFace *f, int select)
{
	BMLoop *l;

	if (BM_TestHFlag(f, BM_HIDDEN)) {
		return;
	}

	if(select){ 
		if (!BM_TestHFlag(f, BM_SELECT)) bm->totfacesel += 1;

		BM_SetHFlag(&(f->head), BM_SELECT);
		l=(BMLoop*) bm_firstfaceloop(f);
		do{
			BM_Select_Vert(bm, l->v, 1);
			BM_Select_Edge(bm, l->e, 1);
			l = l->next;
		}while(l != bm_firstfaceloop(f));
	}
	else{ 
		BMIter liter;
		BMLoop *l;

		if (BM_TestHFlag(f, BM_SELECT)) bm->totfacesel -= 1;
		BM_ClearHFlag(&(f->head), BM_SELECT);

		/*flush down to edges*/
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
			BMIter fiter;
			BMFace *f2;
			BM_ITER(f2, &fiter, bm, BM_FACES_OF_EDGE, l->e) {
				if (BM_TestHFlag(f2, BM_SELECT))
					break;
			}

			if (!f2)
			{
				BM_Select(bm, l->e, 0);
			}
		}

		/*flush down to verts*/
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
			BMIter eiter;
			BMEdge *e;
			BM_ITER(e, &eiter, bm, BM_EDGES_OF_VERT, l->v) {
				if (BM_TestHFlag(e, BM_SELECT))
					break;
			}

			if (!e)
			{
				BM_Select(bm, l->v, 0);
			}
		}
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

	if(bm->selectmode & SCE_SELECT_VERTEX) {
		for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm ); e; e= BMIter_Step(&edges))
			BM_ClearHFlag(e, 0);
		for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm ); f; f= BMIter_Step(&faces))
			BM_ClearHFlag(f, 0);
		BM_SelectMode_Flush(bm);
	}
	else if(bm->selectmode & SCE_SELECT_EDGE) {
		for(v= BMIter_New(&verts, bm, BM_VERTS_OF_MESH, bm ); v; v= BMIter_Step(&verts))
			BM_ClearHFlag(v, 0);
		for(e= BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm ); e; e= BMIter_Step(&edges)){
			if(BM_TestHFlag(&(e->head), BM_SELECT))
				BM_Select_Edge(bm, e, 1);
		}
		BM_SelectMode_Flush(bm);
	}
	else if(bm->selectmode & SCE_SELECT_FACE) {
		for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm ); e; e= BMIter_Step(&edges))
			BM_ClearHFlag(e, 0);
		for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm ); f; f= BMIter_Step(&faces)){
			if(BM_TestHFlag(&(f->head), BM_SELECT))
				BM_Select_Face(bm, f, 1);
		}
		BM_SelectMode_Flush(bm);
	}
}


int BM_CountFlag(struct BMesh *bm, const char htype, const char hflag, int respecthide)
{
	BMHeader *head;
	BMIter iter;
	int tot = 0;

	if (htype & BM_VERT) {
		for (head = BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL); head; head=BMIter_Step(&iter)) {
			if (respecthide && BM_TestHFlag(head, BM_HIDDEN)) continue;
			if (BM_TestHFlag(head, hflag)) tot++;
		}
	}
	if (htype & BM_EDGE) {
		for (head = BMIter_New(&iter, bm, BM_EDGES_OF_MESH, NULL); head; head=BMIter_Step(&iter)) {
			if (respecthide && BM_TestHFlag(head, BM_HIDDEN)) continue;
			if (BM_TestHFlag(head, hflag)) tot++;
		}
	}
	if (htype & BM_FACE) {
		for (head = BMIter_New(&iter, bm, BM_FACES_OF_MESH, NULL); head; head=BMIter_Step(&iter)) {
			if (respecthide && BM_TestHFlag(head, BM_HIDDEN)) continue;
			if (BM_TestHFlag(head, hflag)) tot++;
		}
	}

	return tot;
}

/*note: by design, this will not touch the editselection history stuff*/
void BM_Select(struct BMesh *bm, void *element, int select)
{
	BMHeader *head = element;

	if     (head->htype == BM_VERT) BM_Select_Vert(bm, (BMVert*)element, select);
	else if(head->htype == BM_EDGE) BM_Select_Edge(bm, (BMEdge*)element, select);
	else if(head->htype == BM_FACE) BM_Select_Face(bm, (BMFace*)element, select);
}

int BM_Selected(BMesh *UNUSED(bm), const void *element)
{
	const BMHeader *head = element;
	int selected = BM_TestHFlag(head, BM_SELECT);
	BLI_assert(!selected || !BM_TestHFlag(head, BM_HIDDEN));
	return selected;
}

/* this replaces the active flag used in uv/face mode */
void BM_set_actFace(BMesh *bm, BMFace *efa)
{
	bm->act_face = efa;
}

BMFace *BM_get_actFace(BMesh *bm, int sloppy)
{
	if (bm->act_face) {
		return bm->act_face;
	} else if (sloppy) {
		BMIter iter;
		BMFace *f= NULL;
		BMEditSelection *ese;
		
		/* Find the latest non-hidden face from the BMEditSelection */
		ese = bm->selected.last;
		for (; ese; ese=ese->prev){
			if(ese->htype == BM_FACE) {
				f= (BMFace *)ese->data;
				
				if (BM_TestHFlag(f, BM_HIDDEN)) {
					f= NULL;
				}
				else {
					break;
				}
			}
		}
		/* Last attempt: try to find any selected face */
		if (f==NULL) {
			BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
				if (BM_TestHFlag(f, BM_SELECT)) {
					break;
				}
			}
		}
		return f; /* can still be null */
	}
	return NULL;
}

/* generic way to get data from an EditSelection type 
These functions were written to be used by the Modifier widget when in Rotate about active mode,
but can be used anywhere.
EM_editselection_center
EM_editselection_normal
EM_editselection_plane
*/
void BM_editselection_center(BMesh *bm, float *center, BMEditSelection *ese)
{
	if (ese->htype == BM_VERT) {
		BMVert *eve= ese->data;
		copy_v3_v3(center, eve->co);
	}
	else if (ese->htype == BM_EDGE) {
		BMEdge *eed= ese->data;
		add_v3_v3v3(center, eed->v1->co, eed->v2->co);
		mul_v3_fl(center, 0.5);
	}
	else if (ese->htype == BM_FACE) {
		BMFace *efa= ese->data;
		BM_Compute_Face_CenterBounds(bm, efa, center);
	}
}

void BM_editselection_normal(float *normal, BMEditSelection *ese)
{
	if (ese->htype == BM_VERT) {
		BMVert *eve= ese->data;
		copy_v3_v3(normal, eve->no);
	}
	else if (ese->htype == BM_EDGE) {
		BMEdge *eed= ese->data;
		float plane[3]; /* need a plane to correct the normal */
		float vec[3]; /* temp vec storage */
		
		add_v3_v3v3(normal, eed->v1->no, eed->v2->no);
		sub_v3_v3v3(plane, eed->v2->co, eed->v1->co);
		
		/* the 2 vertex normals will be close but not at rightangles to the edge
		for rotate about edge we want them to be at right angles, so we need to
		do some extra colculation to correct the vert normals,
		we need the plane for this */
		cross_v3_v3v3(vec, normal, plane);
		cross_v3_v3v3(normal, plane, vec); 
		normalize_v3(normal);
		
	}
	else if (ese->htype == BM_FACE) {
		BMFace *efa= ese->data;
		copy_v3_v3(normal, efa->no);
	}
}

/* ref - editmesh_lib.cL:EM_editselection_plane() */

/* Calculate a plane that is rightangles to the edge/vert/faces normal
also make the plane run along an axis that is related to the geometry,
because this is used for the manipulators Y axis.*/
void BM_editselection_plane(BMesh *bm, float *plane, BMEditSelection *ese)
{
	if (ese->htype == BM_VERT) {
		BMVert *eve= ese->data;
		float vec[3]={0,0,0};
		
		if (ese->prev) { /*use previously selected data to make a useful vertex plane */
			BM_editselection_center(bm, vec, ese->prev);
			sub_v3_v3v3(plane, vec, eve->co);
		} else {
			/* make a fake  plane thats at rightangles to the normal
			we cant make a crossvec from a vec thats the same as the vec
			unlikely but possible, so make sure if the normal is (0,0,1)
			that vec isnt the same or in the same direction even.*/
			if (eve->no[0] < 0.5f)		vec[0]= 1.0f;
			else if (eve->no[1] < 0.5f)	vec[1]= 1.0f;
			else						vec[2]= 1.0f;
			cross_v3_v3v3(plane, eve->no, vec);
		}
	}
	else if (ese->htype == BM_EDGE) {
		BMEdge *eed= ese->data;

		/* the plane is simple, it runs along the edge
		however selecting different edges can swap the direction of the y axis.
		this makes it less likely for the y axis of the manipulator
		(running along the edge).. to flip less often.
		at least its more pradictable */
		if (eed->v2->co[1] > eed->v1->co[1]) /*check which to do first */
			sub_v3_v3v3(plane, eed->v2->co, eed->v1->co);
		else
			sub_v3_v3v3(plane, eed->v1->co, eed->v2->co);
		
	}
	else if (ese->htype == BM_FACE) {
		BMFace *efa= ese->data;
		float vec[3] = {0.0f, 0.0f, 0.0f};
		
		/*for now, use face normal*/

		/* make a fake plane thats at rightangles to the normal
		we cant make a crossvec from a vec thats the same as the vec
		unlikely but possible, so make sure if the normal is (0,0,1)
		that vec isnt the same or in the same direction even.*/
		if (efa->len < 3) {
			/* crappy fallback method */
			if      (efa->no[0] < 0.5f)	vec[0]= 1.0f;
			else if (efa->no[1] < 0.5f)	vec[1]= 1.0f;
			else                        vec[2]= 1.0f;
			cross_v3_v3v3(plane, efa->no, vec);
		}
		else {
			BMVert *verts[4]= {NULL};

			BMIter_AsArray(bm, BM_VERTS_OF_FACE, efa, (void **)verts, 4);

			if (efa->len == 4) {
				float vecA[3], vecB[3];
				sub_v3_v3v3(vecA, verts[3]->co, verts[2]->co);
				sub_v3_v3v3(vecB, verts[0]->co, verts[1]->co);
				add_v3_v3v3(plane, vecA, vecB);

				sub_v3_v3v3(vecA, verts[0]->co, verts[3]->co);
				sub_v3_v3v3(vecB, verts[1]->co, verts[2]->co);
				add_v3_v3v3(vec, vecA, vecB);
				/*use the biggest edge length*/
				if (dot_v3v3(plane, plane) < dot_v3v3(vec, vec)) {
					copy_v3_v3(plane, vec);
				}
			}
			else {
				/* BMESH_TODO (not urgent, use longest ngon edge for alignment) */

				/*start with v1-2 */
				sub_v3_v3v3(plane, verts[0]->co, verts[1]->co);

				/*test the edge between v2-3, use if longer */
				sub_v3_v3v3(vec, verts[1]->co, verts[2]->co);
				if (dot_v3v3(plane, plane) < dot_v3v3(vec, vec))
					copy_v3_v3(plane, vec);

				/*test the edge between v1-3, use if longer */
				sub_v3_v3v3(vec, verts[2]->co, verts[0]->co);
				if (dot_v3v3(plane, plane) < dot_v3v3(vec, vec)) {
					copy_v3_v3(plane, vec);
				}
			}

		}
	}
	normalize_v3(plane);
}

static int BM_check_selection(BMesh *bm, void *data)
{
	BMEditSelection *ese;
	
	for(ese = bm->selected.first; ese; ese = ese->next){
		if(ese->data == data) return 1;
	}
	
	return 0;
}

void BM_remove_selection(BMesh *bm, void *data)
{
	BMEditSelection *ese;
	for(ese=bm->selected.first; ese; ese = ese->next){
		if(ese->data == data){
			BLI_freelinkN(&(bm->selected),ese);
			break;
		}
	}
}

void BM_clear_selection_history(BMesh *bm)
{
	BLI_freelistN(&bm->selected);
	bm->selected.first = bm->selected.last = NULL;
}

void BM_store_selection(BMesh *bm, void *data)
{
	BMEditSelection *ese;
	if(!BM_check_selection(bm, data)){
		ese = (BMEditSelection*) MEM_callocN( sizeof(BMEditSelection), "BMEdit Selection");
		ese->htype = ((BMHeader*)data)->htype;
		ese->data = data;
		BLI_addtail(&(bm->selected),ese);
	}
}

void BM_validate_selections(BMesh *bm)
{
	BMEditSelection *ese, *nextese;

	ese = bm->selected.first;

	while(ese) {
		nextese = ese->next;
		if (!BM_TestHFlag(ese->data, BM_SELECT)) {
			BLI_freelinkN(&(bm->selected), ese);
		}
		ese = nextese;
	}
}

void BM_clear_flag_all(BMesh *bm, const char hflag)
{
	int types[3] = {BM_VERTS_OF_MESH, BM_EDGES_OF_MESH, BM_FACES_OF_MESH};
	BMIter iter;
	BMHeader *ele;
	int i;

	if (hflag & BM_SELECT)
		BM_clear_selection_history(bm);

	for (i=0; i<3; i++) {		
		ele = BMIter_New(&iter, bm, types[i], NULL);
		for ( ; ele; ele=BMIter_Step(&iter)) {
			if (hflag & BM_SELECT) BM_Select(bm, ele, 0);
			BM_ClearHFlag(ele, hflag);
		}
	}
}


/***************** Mesh Hiding stuff *************/

#define SETHIDE(ele) hide ? BM_SetHFlag(ele, BM_HIDDEN) : BM_ClearHFlag(ele, BM_HIDDEN);

static void vert_flush_hide(BMesh *bm, BMVert *v)
{
	BMIter iter;
	BMEdge *e;
	int hide = 1;

	BM_ITER(e, &iter, bm, BM_EDGES_OF_VERT, v) {
		hide = hide && BM_TestHFlag(e, BM_HIDDEN);
	}

	SETHIDE(v);
}

static void edge_flush_hide(BMesh *bm, BMEdge *e)
{
	BMIter iter;
	BMFace *f;
	int hide = 1;

	BM_ITER(f, &iter, bm, BM_FACES_OF_EDGE, e) {
		hide = hide && BM_TestHFlag(f, BM_HIDDEN);
	}

	SETHIDE(e);
}

void BM_Hide_Vert(BMesh *bm, BMVert *v, int hide)
{
	/*vert hiding: vert + surrounding edges and faces*/
	BMIter iter, fiter;
	BMEdge *e;
	BMFace *f;

	SETHIDE(v);

	BM_ITER(e, &iter, bm, BM_EDGES_OF_VERT, v) {
		SETHIDE(e);

		BM_ITER(f, &fiter, bm, BM_FACES_OF_EDGE, e) {
			SETHIDE(f);
		}
	}
}

void BM_Hide_Edge(BMesh *bm, BMEdge *e, int hide)
{
	BMIter iter;
	BMFace *f;
	/* BMVert *v; */

	/*edge hiding: faces around the edge*/
	BM_ITER(f, &iter, bm, BM_FACES_OF_EDGE, e) {
		SETHIDE(f);
	}
	
	SETHIDE(e);

	/*hide vertices if necassary*/
	vert_flush_hide(bm, e->v1);
	vert_flush_hide(bm, e->v2);
}

void BM_Hide_Face(BMesh *bm, BMFace *f, int hide)
{
	BMIter iter;
	BMLoop *l;

	/**/
	SETHIDE(f);

	BM_ITER(l, &iter, bm, BM_LOOPS_OF_FACE, f) {
		edge_flush_hide(bm, l->e);
	}

	BM_ITER(l, &iter, bm, BM_LOOPS_OF_FACE, f) {
		vert_flush_hide(bm, l->v);
	}
}

void BM_Hide(BMesh *bm, void *element, int hide)
{
	BMHeader *h = element;

	/*Follow convention of always deselecting before
	  hiding an element*/
	if (hide)
		BM_Select(bm, element, 0);

	switch (h->htype) {
		case BM_VERT:
			BM_Hide_Vert(bm, element, hide);
			break;
		case BM_EDGE:
			BM_Hide_Edge(bm, element, hide);
			break;
		case BM_FACE:
			BM_Hide_Face(bm, element, hide);
			break;
	}
}
