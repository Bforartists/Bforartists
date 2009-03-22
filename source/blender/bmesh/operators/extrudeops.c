#include "MEM_guardedalloc.h"

#include "BKE_utildefines.h"

#include "BLI_ghash.h"
#include "BLI_memarena.h"
#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "bmesh.h"
#include "bmesh_operators_private.h"

#define EXT_INPUT	1
#define EXT_KEEP	2
#define EXT_DEL		4

void extrude_edge_context_exec(BMesh *bm, BMOperator *op)
{
	BMOperator dupeop, delop;
	BMOIter siter;
	BMIter iter, fiter, viter;
	BMEdge *e, *newedge, *e2, *ce;
	BMLoop *l, *l2;
	BMVert *verts[4], *v, *v2;
	BMFace *f;
	int rlen, found, delorig=0, i, reverse;

	/*initialize our sub-operators*/
	BMO_Init_Op(&dupeop, "dupe");
	
	BMO_Flag_Buffer(bm, op, "edgefacein", EXT_INPUT);
	
	/*if one flagged face is bordered by an unflagged face, then we delete
	  original geometry.*/
	for (e=BMIter_New(&iter, bm, BM_EDGES_OF_MESH, NULL);e;e=BMIter_Step(&iter)) {
		if (!BMO_TestFlag(bm, e, EXT_INPUT)) continue;

		found = 0;
		f = BMIter_New(&fiter, bm, BM_FACES_OF_MESH_OF_EDGE, e);
		for (rlen=0; f; f=BMIter_Step(&fiter), rlen++) {
			if (!BMO_TestFlag(bm, f, EXT_INPUT)) {
				found = 1;
				delorig = 1;
				break;
			}
		}
		
		if (!found && (rlen > 1)) BMO_SetFlag(bm, e, EXT_DEL);
	}

	/*calculate verts to delete*/
	for (v = BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL); v; v=BMIter_Step(&iter)) {
		found = 0;

		l = BMIter_New(&viter, bm, BM_LOOPS_OF_VERT, v);
		for (; l; l=BMIter_Step(&viter)) {
			if (!BMO_TestFlag(bm, l->e, EXT_INPUT)) {
				found = 1;
				break;
			}
			if (!BMO_TestFlag(bm, l->f, EXT_INPUT)) {
				found = 1;
				break;
			}

			if (found) break;
		}

		if (!found) {
			BMO_SetFlag(bm, v, EXT_DEL);
		}
	}
	
	for (f=BMIter_New(&fiter, bm, BM_FACES_OF_MESH, NULL); f; f=BMIter_Step(&fiter)) {
		if (BMO_TestFlag(bm, f, EXT_INPUT))
			BMO_SetFlag(bm, f, EXT_DEL);
	}
	if (delorig) BMO_InitOpf(bm, &delop, "del geom=%fvef context=%d", 
	                         EXT_DEL, DEL_ONLYTAGGED);

	BMO_CopySlot(op, &dupeop, "edgefacein", "geom");
	
	BMO_Exec_Op(bm, &dupeop);
	if (delorig) BMO_Exec_Op(bm, &delop);
	
	/*if not delorig, reverse loops of original faces*/
	if (!delorig) {
		for (f=BMIter_New(&iter, bm, BM_FACES_OF_MESH, NULL); f; f=BMIter_Step(&iter)) {
			if (BMO_TestFlag(bm, f, EXT_INPUT)) {
				BM_flip_normal(bm, f);
			}
		}
	}

	BMO_CopySlot(&dupeop, op, "newout", "geomout");
	e = BMO_IterNew(&siter, bm, &dupeop, "boundarymap");
	for (; e; e=BMO_IterStep(&siter)) {
		if (BMO_InMap(bm, op, "exclude", e)) continue;

		newedge = BMO_IterMapVal(&siter);
		newedge = *(BMEdge**)newedge;
		if (!newedge) continue;
		if (!newedge->loop) ce = e;
		else ce = newedge;
		
		if (ce->loop && (ce->loop->v == ce->v1)) {
			verts[0] = e->v1;
			verts[1] = e->v2;
			verts[2] = newedge->v2;
			verts[3] = newedge->v1;
		} else {
			verts[3] = e->v1;
			verts[2] = e->v2;
			verts[1] = newedge->v2;
			verts[0] = newedge->v1;
		}

		/*not sure what to do about example face, pass NULL for now.*/
		f = BM_Make_Quadtriangle(bm, verts, NULL, 4, NULL, 0);		

		/*copy attributes*/
		l=BMIter_New(&iter, bm, BM_LOOPS_OF_FACE, f);
		for (; l; l=BMIter_Step(&iter)) {
			if (l->e != e && l->e != newedge) continue;
			l2 = l->radial.next->data;
			
			if (l2 == l) {
				l2 = newedge->loop;
				BM_Copy_Attributes(bm, bm, l2->f, l->f);

				BM_Copy_Attributes(bm, bm, l2, l);
				l2 = (BMLoop*) l2->head.next;
				l = (BMLoop*) l->head.next;
				BM_Copy_Attributes(bm, bm, l2, l);
			} else {
				BM_Copy_Attributes(bm, bm, l2->f, l->f);

				/*copy data*/
				if (l2->v == l->v) {
					BM_Copy_Attributes(bm, bm, l2, l);
					l2 = (BMLoop*) l2->head.next;
					l = (BMLoop*) l->head.next;
					BM_Copy_Attributes(bm, bm, l2, l);
				} else {
					l2 = (BMLoop*) l2->head.next;
					BM_Copy_Attributes(bm, bm, l2, l);
					l2 = (BMLoop*) l2->head.prev;
					l = (BMLoop*) l->head.next;
					BM_Copy_Attributes(bm, bm, l2, l);
				}
			}
		}
	}

	/*link isolated verts*/
	v = BMO_IterNew(&siter, bm, &dupeop, "isovertmap");
	for (; v; v=BMO_IterStep(&siter)) {
		v2 = *((void**)BMO_IterMapVal(&siter));
		BM_Make_Edge(bm, v, v2, v->edge, 1);
	}

	/*cleanup*/
	if (delorig) BMO_Finish_Op(bm, &delop);
	BMO_Finish_Op(bm, &dupeop);
}
