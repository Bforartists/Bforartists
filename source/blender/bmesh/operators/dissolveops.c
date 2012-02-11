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
 * Contributor(s): Joseph Eagar.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "MEM_guardedalloc.h"

#include "BKE_utildefines.h"

#include "bmesh.h"
#include "mesh_intern.h"
#include "bmesh_private.h"
#include "BLI_math.h"
#include "BLI_array.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FACE_MARK	1
#define FACE_ORIG	2
#define FACE_NEW	4
#define EDGE_MARK	1

#define VERT_MARK	1

static int UNUSED_FUNCTION(check_hole_in_region)(BMesh *bm, BMFace *f)
{
	BMWalker regwalker;
	BMIter liter2;
	BMLoop *l2, *l3;
	BMFace *f2;

	/* checks if there are any unmarked boundary edges in the face regio */

	BMW_Init(&regwalker, bm, BMW_ISLAND,
	         BMW_MASK_NOP, BMW_MASK_NOP, BMW_MASK_NOP, FACE_MARK,
	         BMW_NIL_LAY);
	f2 = BMW_Begin(&regwalker, f);
	for ( ; f2; f2 = BMW_Step(&regwalker)) {
		l2 = BMIter_New(&liter2, bm, BM_LOOPS_OF_FACE, f2);
		for ( ; l2; l2 = BMIter_Step(&liter2)) {
			l3 = bmesh_radial_nextloop(l2);
			if ( BMO_TestFlag(bm, l3->f, FACE_MARK) !=
			     BMO_TestFlag(bm, l2->f, FACE_MARK))
			{
				if (!BMO_TestFlag(bm, l2->e, EDGE_MARK)) {
					return FALSE;
				}
			}
		}
	}
	BMW_End(&regwalker);

	return TRUE;
}

void dissolvefaces_exec(BMesh *bm, BMOperator *op)
{
	BMOIter oiter;
	BMFace *f, *f2 /* , *nf = NULL */;
	BLI_array_declare(faces);
	BLI_array_declare(regions);
	BMFace ***regions = NULL;
	BMFace **faces = NULL;
	BMWalker regwalker;
	int i;

	int use_verts = BMO_Get_Int(op, "use_verts");

	if (use_verts) {
		/* tag verts that start out with only 2 edges,
		 * don't remove these later */
		BMIter viter;
		BMVert *v;

		BM_ITER(v, &viter, bm, BM_VERTS_OF_MESH, NULL) {
			if (BM_Vert_EdgeCount(v) == 2) {
				BMO_ClearFlag(bm, v, VERT_MARK);
			}
			else {
				BMO_SetFlag(bm, v, VERT_MARK);
			}
		}
	}

	BMO_Flag_Buffer(bm, op, "faces", FACE_MARK, BM_FACE);
	
	/* collect region */
	BMO_ITER(f, &oiter, bm, op, "faces", BM_FACE) {
		if (!BMO_TestFlag(bm, f, FACE_MARK)) continue;

		BLI_array_empty(faces);
		faces = NULL; /* forces different allocatio */

		/* yay, walk */
		BMW_Init(&regwalker, bm, BMW_ISLAND,
		         BMW_MASK_NOP, BMW_MASK_NOP, BMW_MASK_NOP, FACE_MARK,
		         BMW_NIL_LAY);

		f2 = BMW_Begin(&regwalker, f);
		for ( ; f2; f2 = BMW_Step(&regwalker)) {
			BLI_array_append(faces, f2);
		}
		BMW_End(&regwalker);
		
		for (i = 0; i < BLI_array_count(faces); i++) {
			f2 = faces[i];
			BMO_ClearFlag(bm, f2, FACE_MARK);
			BMO_SetFlag(bm, f2, FACE_ORIG);
		}

		if (BMO_HasError(bm)) {
			BMO_ClearStack(bm);
			BMO_RaiseError(bm, op, BMERR_DISSOLVEFACES_FAILED, NULL);
			goto cleanup;
		}
		
		BLI_array_append(faces, NULL);
		BLI_array_append(regions, faces);
	}
	
	for (i = 0; i < BLI_array_count(regions); i++) {
		int tot = 0;
		
		faces = regions[i];
		if (!faces[0]) {
			BMO_RaiseError(bm, op, BMERR_DISSOLVEFACES_FAILED,
			               "Could not find boundary of dissolve region");
			goto cleanup;
		}
		
		while (faces[tot])
			tot++;
		
		f = BM_Join_Faces(bm, faces, tot);
		if (!f) {
			BMO_RaiseError(bm, op, BMERR_DISSOLVEFACES_FAILED,
			               "Could not create merged face");
			goto cleanup;
		}

		/* if making the new face failed (e.g. overlapping test)
		 * unmark the original faces for deletion */
		BMO_ClearFlag(bm, f, FACE_ORIG);
		BMO_SetFlag(bm, f, FACE_NEW);

	}

	BMO_CallOpf(bm, "del geom=%ff context=%d", FACE_ORIG, DEL_FACES);


	if (use_verts) {
		BMIter viter;
		BMVert *v;

		BM_ITER(v, &viter, bm, BM_VERTS_OF_MESH, NULL) {
			if (BMO_TestFlag(bm, v, VERT_MARK)) {
				if (BM_Vert_EdgeCount(v) == 2) {
					BM_Collapse_Vert_Edges(bm, v->e, v);
				}
			}
		}
	}

	if (BMO_HasError(bm)) goto cleanup;

	BMO_Flag_To_Slot(bm, op, "regionout", FACE_NEW, BM_FACE);

cleanup:
	/* free/cleanu */
	for (i = 0; i < BLI_array_count(regions); i++) {
		if (regions[i]) MEM_freeN(regions[i]);
	}

	BLI_array_free(regions);
}

/* almost identical to dissolve edge, except it cleans up vertice */
void dissolve_edgeloop_exec(BMesh *bm, BMOperator *op)
{
	/* BMOperator fop; */
	BMOIter oiter;
	BMIter iter;
	BMVert *v, **verts = NULL;
	BLI_array_declare(verts);
	BMEdge *e;
	/* BMFace *f; */
	int i;

	BMO_ITER(e, &oiter, bm, op, "edges", BM_EDGE) {
		if (BM_Edge_FaceCount(e) == 2) {
			BMO_SetFlag(bm, e->v1, VERT_MARK);
			BMO_SetFlag(bm, e->v2, VERT_MARK);

			BM_Join_TwoFaces(bm, e->l->f,
			                 e->l->radial_next->f,
			                 e);
		}
	}

	BM_ITER(v, &iter, bm, BM_VERTS_OF_MESH, NULL) {
		if (BMO_TestFlag(bm, v, VERT_MARK) && BM_Vert_EdgeCount(v) == 2) {
			BLI_array_append(verts, v);
		}
	}

	/* clean up extreneous 2-valence vertice */
	for (i = 0; i < BLI_array_count(verts); i++) {
		if (verts[i]->e) {
			BM_Collapse_Vert_Edges(bm, verts[i]->e, verts[i]);
		}
	}
	
	BLI_array_free(verts);

	//BMO_InitOpf(bm, &fop, "dissolvefaces faces=%ff", FACE_MARK);
	//BMO_Exec_Op(bm, &fop);

	//BMO_CopySlot(op, &fop, "regionout", "regionout");

	//BMO_Finish_Op(bm, &fop);
}


void dissolveedges_exec(BMesh *bm, BMOperator *op)
{
	/* might want to make this an option or mode - campbell */

	/* BMOperator fop; */
	BMOIter eiter;
	BMEdge *e;

	BMIter viter;
	BMVert *v;

	int use_verts = BMO_Get_Int(op, "use_verts");

	if (use_verts) {
		BM_ITER(v, &viter, bm, BM_VERTS_OF_MESH, NULL) {
			if (BM_Vert_EdgeCount(v) == 2) {
				BMO_ClearFlag(bm, v, VERT_MARK);
			}
			else {
				BMO_SetFlag(bm, v, VERT_MARK);
			}
		}
	}

	BMO_ITER(e, &eiter, bm, op, "edges", BM_EDGE) {
		const int edge_face_count = BM_Edge_FaceCount(e);
		if (edge_face_count == 2) {

			/* join faces */
			BM_Join_TwoFaces(bm, e->l->f,
			                 e->l->radial_next->f,
			                 e);
		}
	}

	if (use_verts) {
		BM_ITER(v, &viter, bm, BM_VERTS_OF_MESH, NULL) {
			if (BMO_TestFlag(bm, v, VERT_MARK)) {
				if (BM_Vert_EdgeCount(v) == 2) {
					BM_Collapse_Vert_Edges(bm, v->e, v);
				}
			}
		}
	}
}

static int test_extra_verts(BMesh *bm, BMVert *v)
{
	BMIter iter, liter, iter2, iter3;
	BMFace *f, *f2;
	BMLoop *l;
	BMEdge *e;
	int found;

	/* test faces around verts for verts that would be wronly killed
	 * by dissolve faces. */
	f = BMIter_New(&iter, bm, BM_FACES_OF_VERT, v);
	for ( ; f; f = BMIter_Step(&iter)) {
		l = BMIter_New(&liter, bm, BM_LOOPS_OF_FACE, f);
		for ( ; l; l = BMIter_Step(&liter)) {
			if (!BMO_TestFlag(bm, l->v, VERT_MARK)) {
				/* if an edge around a vert is a boundary edge,
				 * then dissolve faces won't destroy it.
				 * also if it forms a boundary with one
				 * of the face region */
				found = FALSE;
				e = BMIter_New(&iter2, bm, BM_EDGES_OF_VERT, l->v);
				for ( ; e; e = BMIter_Step(&iter2)) {
					if (BM_Edge_FaceCount(e) == 1) {
						found = TRUE;
					}
					f2 = BMIter_New(&iter3, bm, BM_FACES_OF_EDGE, e);
					for ( ; f2; f2 = BMIter_Step(&iter3)) {
						if (!BMO_TestFlag(bm, f2, FACE_MARK)) {
							found = TRUE;
							break;
						}
					}
					if (found == TRUE) {
						break;
					}
				}
				if (found == FALSE) {
					return FALSE;
				}
			}
		}
	}

	return TRUE;
}
void dissolveverts_exec(BMesh *bm, BMOperator *op)
{
	BMOpSlot *vinput;
	BMIter iter, fiter;
	BMVert *v;
	BMFace *f;
	/* int i; */
	
	vinput = BMO_GetSlot(op, "verts");
	BMO_Flag_Buffer(bm, op, "verts", VERT_MARK, BM_VERT);
	
	for (v = BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL); v; v = BMIter_Step(&iter)) {
		if (BMO_TestFlag(bm, v, VERT_MARK)) {
			/* check if it's a two-valence ver */
			if (BM_Vert_EdgeCount(v) == 2) {

				/* collapse the ver */
				BM_Collapse_Vert_Faces(bm, v->e, v, 1.0f, TRUE);
				continue;
			}

			f = BMIter_New(&fiter, bm, BM_FACES_OF_VERT, v);
			for ( ; f; f = BMIter_Step(&fiter)) {
				BMO_SetFlag(bm, f, FACE_ORIG);
				BMO_SetFlag(bm, f, FACE_MARK);
			}
			
			/* check if our additions to the input to face dissolve
			 * will destroy nonmarked vertices. */
			if (!test_extra_verts(bm, v)) {
				f = BMIter_New(&fiter, bm, BM_FACES_OF_VERT, v);
				for ( ; f; f = BMIter_Step(&fiter)) {
					if (BMO_TestFlag(bm, f, FACE_ORIG)) {
						BMO_ClearFlag(bm, f, FACE_MARK);
						BMO_ClearFlag(bm, f, FACE_ORIG);
					}
				}
			}
			else {
				f = BMIter_New(&fiter, bm, BM_FACES_OF_VERT, v);
				for ( ; f; f = BMIter_Step(&fiter)) {
					BMO_ClearFlag(bm, f, FACE_ORIG);
				}
			}
		}
	}

	BMO_CallOpf(bm, "dissolvefaces faces=%ff", FACE_MARK);
	if (BMO_HasError(bm)) {
		const char *msg;

		BMO_GetError(bm, &msg, NULL);
		BMO_ClearStack(bm);
		BMO_RaiseError(bm, op, BMERR_DISSOLVEVERTS_FAILED, msg);
	}
	
	/* clean up any remainin */
	for (v = BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL); v; v = BMIter_Step(&iter)) {
		if (BMO_TestFlag(bm, v, VERT_MARK)) {
			if (!BM_Dissolve_Vert(bm, v)) {
				BMO_RaiseError(bm, op, BMERR_DISSOLVEVERTS_FAILED, NULL);
				return;
			}
		}
	}

}

/* this code is for cleaning up two-edged faces, it shall become
 * it's own function one day */
#if 0
		/* clean up two-edged face */
		/* basic idea is to keep joining 2-edged faces until their
		 * gone.  this however relies on joining two 2-edged faces
		 * together to work, which doesn't */
		found3 = 1;
		while (found3) {
			found3 = 0;
			for (f = BMIter_New(&iter, bm, BM_FACES_OF_MESH, NULL); f; f = BMIter_Step(&iter)) {
				if (!BM_Validate_Face(bm, f, stderr)) {
					printf("error.\n");
				}

				if (f->len == 2) {
					//this design relies on join faces working
					//with two-edged faces properly.
					//commenting this line disables the
					//outermost loop.
					//found3 = 1;
					found2 = 0;
					l = BMIter_New(&liter, bm, BM_LOOPS_OF_FACE, f);
					fe = l->e;
					for ( ; l; l = BMIter_Step(&liter)) {
						f2 = BMIter_New(&fiter, bm,
								BM_FACES_OF_EDGE, l->e);
						for ( ; f2; f2 = BMIter_Step(&fiter)) {
							if (f2 != f) {
								BM_Join_TwoFaces(bm, f, f2, l->e);
								found2 = 1;
								break;
							}
						}
						if (found2) break;
					}

					if (!found2) {
						bmesh_kf(bm, f);
						bmesh_ke(bm, fe);
					}
				} /* else if (f->len == 3) {
					BMEdge *ed[3];
					BMVert *vt[3];
					BMLoop *lp[3];
					int i = 0;

					//check for duplicate edges
					l = BMIter_New(&liter, bm, BM_LOOPS_OF_FACE, f);
					for ( ; l; l = BMIter_Step(&liter)) {
						ed[i] = l->e;
						lp[i] = l;
						vt[i++] = l->v;
					}
					if (vt[0] == vt[1] || vt[0] == vt[2]) {
						i += 1;
					}
				 */
			}
		}
		if (oldlen == len) break;
		oldlen = len;

#endif
