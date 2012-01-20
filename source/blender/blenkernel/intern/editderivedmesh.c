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

/** \file blender/blenkernel/intern/editderivedmesh.c
 *  \ingroup bke
 */

#include <string.h>
#include <limits.h>
#include <math.h>

#include "GL/glew.h"

#include "BLI_utildefines.h"
#include "BLI_blenlib.h"
#include "BLI_edgehash.h"
#include "BLI_editVert.h"
#include "BLI_math.h"
#include "BLI_pbvh.h"

#include "BKE_cdderivedmesh.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_paint.h"


#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_curve_types.h" /* for Curve */

#include "MEM_guardedalloc.h"

#include "GPU_buffers.h"
#include "GPU_draw.h"
#include "GPU_extensions.h"
#include "GPU_material.h"

/* bmesh */
#include "BKE_tessmesh.h"
#include "BLI_array.h"
#include "BLI_scanfill.h"

#include "bmesh.h"
/* end bmesh */

extern GLubyte stipple_quarttone[128]; /* glutil.c, bad level data */


BMEditMesh *BMEdit_Create(BMesh *bm)
{
	BMEditMesh *tm = MEM_callocN(sizeof(BMEditMesh), __func__);

	tm->bm = bm;

	BMEdit_RecalcTesselation(tm);

	return tm;
}

BMEditMesh *BMEdit_Copy(BMEditMesh *tm)
{
	BMEditMesh *tm2 = MEM_callocN(sizeof(BMEditMesh), __func__);
	*tm2 = *tm;

	tm2->derivedCage = tm2->derivedFinal = NULL;

	tm2->bm = BM_Copy_Mesh(tm->bm);

	/*The tesselation is NOT calculated on the copy here,
	  because currently all the callers of this function use
	  it to make a backup copy of the BMEditMesh to restore
	  it in the case of errors in an operation. For perf
	  reasons, in that case it makes more sense to do the
	  tesselation only when/if that copy ends up getting
	  used.*/
	tm2->looptris = NULL;

	tm2->vert_index = NULL;
	tm2->edge_index = NULL;
	tm2->face_index = NULL;

	return tm2;
}

static void BMEdit_RecalcTesselation_intern(BMEditMesh *tm)
{
	/* use this to avoid locking pthread for _every_ polygon
	 * and calling the fill function */
#define USE_TESSFACE_SPEEDUP

	BMesh *bm = tm->bm;
	BMLoop *(*looptris)[3]= NULL;
	BLI_array_declare(looptris);
	BMIter iter, liter;
	BMFace *f;
	BMLoop *l;
	int i = 0, j;

	if (tm->looptris) MEM_freeN(tm->looptris);

	f = BMIter_New(&iter, bm, BM_FACES_OF_MESH, NULL);
	for ( ; f; f=BMIter_Step(&iter)) {
		/*don't consider two-edged faces*/
		if (f->len < 3) {
			/* do nothing */
		}

#ifdef USE_TESSFACE_SPEEDUP

		/* no need to ensure the loop order, we know its ok */

		else if (f->len == 3) {
			BLI_array_growone(looptris);
			l = BMIter_New(&liter, bm, BM_LOOPS_OF_FACE, f);
			for (j=0; l; l=BMIter_Step(&liter), j++) {
				looptris[i][j] = l;
			}
			i += 1;
		}
		else if (f->len == 4) {
			BMLoop *ltmp[4];
			BLI_array_growitems(looptris, 2);

			l = BMIter_New(&liter, bm, BM_LOOPS_OF_FACE, f);
			for (j=0; l; l=BMIter_Step(&liter), j++) {
				ltmp[j] = l;
			}

			looptris[i][0] = ltmp[0];
			looptris[i][1] = ltmp[1];
			looptris[i][2] = ltmp[2];
			i += 1;

			looptris[i][0] = ltmp[0];
			looptris[i][1] = ltmp[2];
			looptris[i][2] = ltmp[3];
			i += 1;
		}

#endif /* USE_TESSFACE_SPEEDUP */

		else {
			EditVert *v, *lastv=NULL, *firstv=NULL;
			EditEdge *e;
			EditFace *efa;

			BLI_begin_edgefill();
			/*scanfill time*/
			l = BMIter_New(&liter, bm, BM_LOOPS_OF_FACE, f);
			for (j=0; l; l=BMIter_Step(&liter), j++) {
				/*mark order*/
				BM_SetIndex(l, j); /* set_loop */

				v = BLI_addfillvert(l->v->co);
				v->tmp.p = l;

				if (lastv) {
					e = BLI_addfilledge(lastv, v);
				}

				lastv = v;
				if (firstv==NULL) firstv = v;
			}

			/*complete the loop*/
			BLI_addfilledge(firstv, v);

			BLI_edgefill(2);

			for (efa = fillfacebase.first; efa; efa=efa->next) {
				BMLoop *l1= efa->v1->tmp.p;
				BMLoop *l2= efa->v2->tmp.p;
				BMLoop *l3= efa->v3->tmp.p;

				BLI_array_growone(looptris);

				if (BM_GetIndex(l1) > BM_GetIndex(l2)) { SWAP(BMLoop*, l1, l2); }
				if (BM_GetIndex(l2) > BM_GetIndex(l3)) { SWAP(BMLoop*, l2, l3); }
				if (BM_GetIndex(l1) > BM_GetIndex(l2)) { SWAP(BMLoop*, l1, l2); }

				looptris[i][0] = l1;
				looptris[i][1] = l2;
				looptris[i][2] = l3;
				i += 1;
			}

			BLI_end_edgefill();
		}
	}

	tm->tottri = i;
	tm->looptris = looptris;

#undef USE_TESSFACE_SPEEDUP

}

void BMEdit_RecalcTesselation(BMEditMesh *em)
{
	BMEdit_RecalcTesselation_intern(em);

	/* commented because editbmesh_build_data() ensures we get tessfaces */
#if 0
	if (em->derivedFinal && em->derivedFinal == em->derivedCage) {
		if (em->derivedFinal->recalcTesselation)
			em->derivedFinal->recalcTesselation(em->derivedFinal);
	}
	else if (em->derivedFinal) {
		if (em->derivedCage->recalcTesselation)
			em->derivedCage->recalcTesselation(em->derivedCage);
		if (em->derivedFinal->recalcTesselation)
			em->derivedFinal->recalcTesselation(em->derivedFinal);
	}
#endif
}

void BMEdit_UpdateLinkedCustomData(BMEditMesh *em)
{
	BMesh *bm = em->bm;
	int act;

	if (CustomData_has_layer(&bm->pdata, CD_MTEXPOLY)) {
		act = CustomData_get_active_layer(&bm->pdata, CD_MTEXPOLY);
		CustomData_set_layer_active(&bm->ldata, CD_MLOOPUV, act);

		act = CustomData_get_render_layer(&bm->pdata, CD_MTEXPOLY);
		CustomData_set_layer_render(&bm->ldata, CD_MLOOPUV, act);

		act = CustomData_get_clone_layer(&bm->pdata, CD_MTEXPOLY);
		CustomData_set_layer_clone(&bm->ldata, CD_MLOOPUV, act);

		act = CustomData_get_stencil_layer(&bm->pdata, CD_MTEXPOLY);
		CustomData_set_layer_stencil(&bm->ldata, CD_MLOOPUV, act);
	}
}

/*does not free the BMEditMesh struct itself*/
void BMEdit_Free(BMEditMesh *em)
{
	if (em->derivedFinal) {
		if (em->derivedFinal!=em->derivedCage) {
			em->derivedFinal->needsFree= 1;
			em->derivedFinal->release(em->derivedFinal);
		}
		em->derivedFinal= NULL;
	}
	if (em->derivedCage) {
		em->derivedCage->needsFree= 1;
		em->derivedCage->release(em->derivedCage);
		em->derivedCage= NULL;
	}

	if (em->looptris) MEM_freeN(em->looptris);

	if (em->vert_index) MEM_freeN(em->vert_index);
	if (em->edge_index) MEM_freeN(em->edge_index);
	if (em->face_index) MEM_freeN(em->face_index);

	if (em->bm)
		BM_Free_Mesh(em->bm);
}

/*
ok, basic design:

the bmesh derivedmesh exposes the mesh as triangles.  it stores pointers
to three loops per triangle.  the derivedmesh stores a cache of tesselations
for each face.  this cache will smartly update as needed (though at first
it'll simply be more brute force).  keeping track of face/edge counts may
be a small problbm.

this won't be the most efficient thing, considering that internal edges and
faces of tesselations are exposed.  looking up an edge by index in particular
is likely to be a little slow.
*/

typedef struct EditDerivedBMesh {
	DerivedMesh dm;

	Object *ob;
	BMEditMesh *tc;

	float (*vertexCos)[3];
	float (*vertexNos)[3];
	float (*faceNos)[3];

	/*lookup caches; these are rebuilt on dm->RecalcTesselation()
	  (or when the derivedmesh is created, of course)*/
	GHash *vhash, *ehash, *fhash;
	BMVert **vtable;
	BMEdge **etable;
	BMFace **ftable;

	/*private variables, for number of verts/edges/faces
	  within the above hash/table members*/
	int tv, te, tf;
} EditDerivedBMesh;

static void bmdm_recalc_lookups(EditDerivedBMesh *bmdm)
{
	BMIter iter;
	BMHeader *h;
	int a, i, iters[3] = {BM_VERTS_OF_MESH, BM_EDGES_OF_MESH, BM_FACES_OF_MESH};

	bmdm->tv = bmdm->tc->bm->totvert;
	bmdm->te = bmdm->tc->bm->totedge;
	bmdm->tf = bmdm->tc->bm->totface;

	if (bmdm->vhash) BLI_ghash_free(bmdm->vhash, NULL, NULL);
	if (bmdm->ehash) BLI_ghash_free(bmdm->ehash, NULL, NULL);
	if (bmdm->fhash) BLI_ghash_free(bmdm->fhash, NULL, NULL);

	bmdm->vhash = BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "bmesh derived");
	bmdm->ehash = BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "bmesh derived");
	bmdm->fhash = BLI_ghash_new(BLI_ghashutil_ptrhash, BLI_ghashutil_ptrcmp, "bmesh derived");

	if (bmdm->vtable) MEM_freeN(bmdm->vtable);
	if (bmdm->etable) MEM_freeN(bmdm->etable);
	if (bmdm->ftable) MEM_freeN(bmdm->ftable);

	if (bmdm->tc->bm->totvert)
		bmdm->vtable = MEM_mallocN(sizeof(void**)*bmdm->tc->bm->totvert, "bmdm->vtable");
	else bmdm->vtable = NULL;

	if (bmdm->tc->bm->totedge)
		bmdm->etable = MEM_mallocN(sizeof(void**)*bmdm->tc->bm->totedge, "bmdm->etable");
	else bmdm->etable = NULL;

	if (bmdm->tc->bm->totface)
		bmdm->ftable = MEM_mallocN(sizeof(void**)*bmdm->tc->bm->totface, "bmdm->ftable");
	else bmdm->ftable = NULL;

	for (a=0; a<3; a++) {
		h = BMIter_New(&iter, bmdm->tc->bm, iters[a], NULL);
		for (i=0; h; h=BMIter_Step(&iter), i++) {
			switch (a) {
				case 0:
					bmdm->vtable[i] = (BMVert*) h;
					BLI_ghash_insert(bmdm->vhash, h, SET_INT_IN_POINTER(i));
					break;
				case 1:
					bmdm->etable[i] = (BMEdge*) h;
					BLI_ghash_insert(bmdm->ehash, h, SET_INT_IN_POINTER(i));
					break;
				case 2:
					bmdm->ftable[i] = (BMFace*) h;
					BLI_ghash_insert(bmdm->fhash, h, SET_INT_IN_POINTER(i));
					break;

			}
		}
	}
}

static void emDM_calcNormals(DerivedMesh *UNUSED(dm))
{
	/* Nothing to do: normals are already calculated and stored on the
	   BMVerts and BMFaces */
}

static void emDM_recalcTesselation(DerivedMesh *UNUSED(dm))
{
	//EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;

	//bmdm_recalc_lookups(bmdm);
}

static void emDM_foreachMappedVert(
		DerivedMesh *dm,
		void (*func)(void *userData, int index, float *co, float *no_f, short *no_s),
		void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMVert *eve;
	BMIter iter;
	int i;

	eve = BMIter_New(&iter, bmdm->tc->bm, BM_VERTS_OF_MESH, NULL);
	for (i=0; eve; i++, eve=BMIter_Step(&iter)) {
		if (bmdm->vertexCos) {
			func(userData, i, bmdm->vertexCos[i], bmdm->vertexNos[i], NULL);
		}
		else {
			func(userData, i, eve->co, eve->no, NULL);
		}
	}
}
static void emDM_foreachMappedEdge(
		DerivedMesh *dm,
		void (*func)(void *userData, int index, float *v0co, float *v1co),
		void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMEdge *eed;
	BMIter iter;
	int i;

	if (bmdm->vertexCos) {

		BM_ElemIndex_Ensure(bmdm->tc->bm, BM_VERT);

		eed = BMIter_New(&iter, bmdm->tc->bm, BM_EDGES_OF_MESH, NULL);
		for (i=0; eed; i++,eed=BMIter_Step(&iter))
			func(userData, i,
				 bmdm->vertexCos[BM_GetIndex(eed->v1)],
				 bmdm->vertexCos[BM_GetIndex(eed->v2)]);
	}
	else {
		eed = BMIter_New(&iter, bmdm->tc->bm, BM_EDGES_OF_MESH, NULL);
		for (i=0; eed; i++,eed=BMIter_Step(&iter))
			func(userData, i, eed->v1->co, eed->v2->co);
	}
}

static void emDM_drawMappedEdges(
		DerivedMesh *dm,
		int (*setDrawOptions)(void *userData, int index),
		void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMEdge *eed;
	BMIter iter;
	int i;

	if (bmdm->vertexCos) {

		BM_ElemIndex_Ensure(bmdm->tc->bm, BM_VERT);

		glBegin(GL_LINES);
		eed = BMIter_New(&iter, bmdm->tc->bm, BM_EDGES_OF_MESH, NULL);
		for (i=0; eed; i++,eed=BMIter_Step(&iter)) {
			if (!setDrawOptions || setDrawOptions(userData, i)) {
				glVertex3fv(bmdm->vertexCos[BM_GetIndex(eed->v1)]);
				glVertex3fv(bmdm->vertexCos[BM_GetIndex(eed->v2)]);
			}
		}
		glEnd();
	}
	else {
		glBegin(GL_LINES);
		eed = BMIter_New(&iter, bmdm->tc->bm, BM_EDGES_OF_MESH, NULL);
		for (i=0; eed; i++,eed=BMIter_Step(&iter)) {
			if (!setDrawOptions || setDrawOptions(userData, i)) {
				glVertex3fv(eed->v1->co);
				glVertex3fv(eed->v2->co);
			}
		}
		glEnd();
	}
}
static void emDM_drawEdges(
		DerivedMesh *dm,
		int UNUSED(drawLooseEdges),
		int UNUSED(drawAllEdges))
{
	emDM_drawMappedEdges(dm, NULL, NULL);
}

static void emDM_drawMappedEdgesInterp(
		DerivedMesh *dm,
		int (*setDrawOptions)(void *userData, int index),
		void (*setDrawInterpOptions)(void *userData, int index, float t),
		void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMEdge *eed;
	BMIter iter;
	int i;

	if (bmdm->vertexCos) {

		BM_ElemIndex_Ensure(bmdm->tc->bm, BM_VERT);

		glBegin(GL_LINES);
		eed = BMIter_New(&iter, bmdm->tc->bm, BM_EDGES_OF_MESH, NULL);
		for (i=0; eed; i++,eed=BMIter_Step(&iter)) {
			if (!setDrawOptions || setDrawOptions(userData, i)) {
				setDrawInterpOptions(userData, i, 0.0);
				glVertex3fv(bmdm->vertexCos[(int) BM_GetIndex(eed->v1)]);
				setDrawInterpOptions(userData, i, 1.0);
				glVertex3fv(bmdm->vertexCos[(int) BM_GetIndex(eed->v2)]);
			}
		}
		glEnd();
	}
	else {
		glBegin(GL_LINES);
		eed = BMIter_New(&iter, bmdm->tc->bm, BM_EDGES_OF_MESH, NULL);
		for (i=0; eed; i++,eed=BMIter_Step(&iter)) {
			if (!setDrawOptions || setDrawOptions(userData, i)) {
				setDrawInterpOptions(userData, i, 0.0);
				glVertex3fv(eed->v1->co);
				setDrawInterpOptions(userData, i, 1.0);
				glVertex3fv(eed->v2->co);
			}
		}
		glEnd();
	}
}

static void emDM_drawUVEdges(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMEditMesh *em = bmdm->tc;
	BMFace *efa;
	BMIter iter;

	glBegin(GL_LINES);
	BM_ITER(efa, &iter, em->bm, BM_FACES_OF_MESH, NULL) {
		BMIter liter;
		BMLoop *l;
		MLoopUV *lastluv = NULL, *firstluv = NULL;

		if (BM_TestHFlag(efa, BM_HIDDEN))
			continue;

		BM_ITER(l, &liter, em->bm, BM_LOOPS_OF_FACE, efa) {
			MLoopUV *luv = CustomData_bmesh_get(&em->bm->ldata, l->head.data, CD_MLOOPUV);

			if (luv) {
				if (lastluv)
					glVertex2fv(luv->uv);
				glVertex2fv(luv->uv);

				lastluv = luv;
				if (!firstluv)
					firstluv = luv;
			}
		}

		if (lastluv) {
			glVertex2fv(lastluv->uv);
			glVertex2fv(firstluv->uv);
		}
	}
	glEnd();
}

static void emDM__calcFaceCent(BMesh *bm, BMFace *efa, float cent[3], float (*vertexCos)[3])
{
	BMIter iter;
	BMLoop *l;
	int tot = 0;

	zero_v3(cent);

	/*simple (and stupid) median (average) based method :/ */

	if (vertexCos) {
		l = BMIter_New(&iter, bm, BM_LOOPS_OF_FACE, efa);
		for (; l; l=BMIter_Step(&iter)) {
			add_v3_v3(cent, vertexCos[BM_GetIndex(l->v)]);
			tot++;
		}
	}
	else {
		l = BMIter_New(&iter, bm, BM_LOOPS_OF_FACE, efa);
		for (; l; l=BMIter_Step(&iter)) {
			add_v3_v3(cent, l->v->co);
			tot++;
		}
	}

	if (tot==0) return;
	mul_v3_fl(cent, 1.0f/(float)tot);
}

static void emDM_foreachMappedFaceCenter(
		DerivedMesh *dm,
		void (*func)(void *userData, int index, float *co, float *no),
		void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMFace *efa;
	BMIter iter;
	float cent[3];
	int i;

	if (bmdm->vertexCos) {
		BM_ElemIndex_Ensure(bmdm->tc->bm, BM_VERT);
	}

	efa = BMIter_New(&iter, bmdm->tc->bm, BM_FACES_OF_MESH, NULL);
	for (i=0; efa; efa=BMIter_Step(&iter), i++) {
		emDM__calcFaceCent(bmdm->tc->bm, efa, cent, bmdm->vertexCos);
		func(userData, i, cent, bmdm->vertexCos?bmdm->faceNos[i]:efa->no);
	}
}

static void emDM_drawMappedFaces(
		DerivedMesh *dm,
		int (*setDrawOptions)(void *userData, int index, int *drawSmooth_r),
		int (*setMaterial)(int, void *attribs),
		int (*compareDrawOptions)(void *userData, int cur_index, int next_index),
		void *userData, int UNUSED(useColors))
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMFace *efa;
	struct BMLoop *(*looptris)[3]= bmdm->tc->looptris;
	const int tottri= bmdm->tc->tottri;
	const int lasttri= tottri - 1; /* compare agasint this a lot */
	int i, draw, flush;
	const int skip_normals= !glIsEnabled(GL_LIGHTING); /* could be passed as an arg */

	/* GL_ZERO is used to detect if drawing has started or not */
	GLenum poly_prev= GL_ZERO;
	GLenum shade_prev= GL_ZERO;

	(void)setMaterial; /* UNUSED */

	/* currently unused -- each original face is handled separately */
	(void)compareDrawOptions;

	if (bmdm->vertexCos) {
		/* add direct access */
		float (*vertexCos)[3]= bmdm->vertexCos;
		float (*vertexNos)[3]= bmdm->vertexNos;
		float (*faceNos)[3]=   bmdm->faceNos;

		BM_ElemIndex_Ensure(bmdm->tc->bm, BM_VERT | BM_FACE);

		for (i=0; i < tottri; i++) {
			BMLoop **l = looptris[i];
			int drawSmooth;

			efa = l[0]->f;
			drawSmooth= BM_TestHFlag(efa, BM_SMOOTH);

			draw = setDrawOptions==NULL ? 1 : setDrawOptions(userData, BM_GetIndex(efa), &drawSmooth);
			if (draw) {
				const GLenum poly_type= GL_TRIANGLES; /* BMESH NOTE, this is odd but keep it for now to match trunk */
				if (draw==2) { /* enabled with stipple */

					if (poly_prev != GL_ZERO) glEnd();
					poly_prev= GL_ZERO; /* force glBegin */

					glEnable(GL_POLYGON_STIPPLE);
					glPolygonStipple(stipple_quarttone);
				}

				if (skip_normals) {
					if (poly_type != poly_prev) {
						if (poly_prev != GL_ZERO) glEnd();
						glBegin((poly_prev= poly_type)); /* BMesh: will always be GL_TRIANGLES */
					}
					glVertex3fv(vertexCos[(int) BM_GetIndex(l[0]->v)]);
					glVertex3fv(vertexCos[(int) BM_GetIndex(l[1]->v)]);
					glVertex3fv(vertexCos[(int) BM_GetIndex(l[2]->v)]);
				}
				else {
					const GLenum shade_type= drawSmooth ? GL_SMOOTH : GL_FLAT;
					if (shade_type != shade_prev) {
						if (poly_prev != GL_ZERO) glEnd();
						glShadeModel((shade_prev= shade_type)); /* same as below but switch shading */
						glBegin((poly_prev= poly_type)); /* BMesh: will always be GL_TRIANGLES */
					}
					if (poly_type != poly_prev) {
						if (poly_prev != GL_ZERO) glEnd();
						glBegin((poly_prev= poly_type)); /* BMesh: will always be GL_TRIANGLES */
					}

					if (!drawSmooth) {
						glNormal3fv(faceNos[i]);
						glVertex3fv(vertexCos[(int) BM_GetIndex(l[0]->v)]);
						glVertex3fv(vertexCos[(int) BM_GetIndex(l[1]->v)]);
						glVertex3fv(vertexCos[(int) BM_GetIndex(l[2]->v)]);
					}
					else {
						glNormal3fv(vertexNos[(int) BM_GetIndex(l[0]->v)]);
						glVertex3fv(vertexCos[(int) BM_GetIndex(l[0]->v)]);
						glNormal3fv(vertexNos[(int) BM_GetIndex(l[1]->v)]);
						glVertex3fv(vertexCos[(int) BM_GetIndex(l[1]->v)]);
						glNormal3fv(vertexNos[(int) BM_GetIndex(l[2]->v)]);
						glVertex3fv(vertexCos[(int) BM_GetIndex(l[2]->v)]);
					}
				}

				flush= (draw==2);
				if (!skip_normals && !flush && (i != lasttri))
					flush|= efa->mat_nr != looptris[i + 1][0]->f->mat_nr; /* TODO, make this neater */

				if (flush) {
					glEnd();
					poly_prev= GL_ZERO; /* force glBegin */

					glDisable(GL_POLYGON_STIPPLE);
				}
			}
		}
	}
	else {
		BM_ElemIndex_Ensure(bmdm->tc->bm, BM_FACE);

		for (i=0; i < tottri; i++) {
			BMLoop **l = looptris[i];
			int drawSmooth;

			efa = l[0]->f;
			drawSmooth= BM_TestHFlag(efa, BM_SMOOTH);

			draw = setDrawOptions==NULL ? 1 : setDrawOptions(userData, BM_GetIndex(efa), &drawSmooth);
			if (draw) {
				const GLenum poly_type= GL_TRIANGLES; /* BMESH NOTE, this is odd but keep it for now to match trunk */
				if (draw==2) { /* enabled with stipple */

					if (poly_prev != GL_ZERO) glEnd();
					poly_prev= GL_ZERO; /* force glBegin */

					glEnable(GL_POLYGON_STIPPLE);
					glPolygonStipple(stipple_quarttone);
				}

				if (skip_normals) {
					if (poly_type != poly_prev) {
						if (poly_prev != GL_ZERO) glEnd();
						glBegin((poly_prev= poly_type)); /* BMesh: will always be GL_TRIANGLES */
					}
					glVertex3fv(l[0]->v->co);
					glVertex3fv(l[1]->v->co);
					glVertex3fv(l[2]->v->co);
				}
				else {
					const GLenum shade_type= drawSmooth ? GL_SMOOTH : GL_FLAT;
					if (shade_type != shade_prev) {
						if (poly_prev != GL_ZERO) glEnd();
						glShadeModel((shade_prev= shade_type)); /* same as below but switch shading */
						glBegin((poly_prev= poly_type)); /* BMesh: will always be GL_TRIANGLES */
					}
					if (poly_type != poly_prev) {
						if (poly_prev != GL_ZERO) glEnd();
						glBegin((poly_prev= poly_type)); /* BMesh: will always be GL_TRIANGLES */
					}

					if (!drawSmooth) {
						glNormal3fv(efa->no);
						glVertex3fv(l[0]->v->co);
						glVertex3fv(l[1]->v->co);
						glVertex3fv(l[2]->v->co);
					}
					else {
						glNormal3fv(l[0]->v->no);
						glVertex3fv(l[0]->v->co);
						glNormal3fv(l[1]->v->no);
						glVertex3fv(l[1]->v->co);
						glNormal3fv(l[2]->v->no);
						glVertex3fv(l[2]->v->co);
					}
				}

				flush= (draw==2);
				if (!skip_normals && !flush && (i != lasttri)) {
					flush|= efa->mat_nr != looptris[i + 1][0]->f->mat_nr; /* TODO, make this neater */
				}

				if (flush) {
					glEnd();
					poly_prev= GL_ZERO; /* force glBegin */

					glDisable(GL_POLYGON_STIPPLE);
				}
			}
		}
	}

	/* if non zero we know a face was rendered */
	if (poly_prev != GL_ZERO) glEnd();
}

static void bmdm_get_tri_tex(BMesh *bm, BMLoop **ls, MLoopUV *luv[3], MLoopCol *lcol[3],
				 int has_uv, int has_col)
{
	if (has_uv) {
		luv[0] = CustomData_bmesh_get(&bm->ldata, ls[0]->head.data, CD_MLOOPUV);
		luv[1] = CustomData_bmesh_get(&bm->ldata, ls[1]->head.data, CD_MLOOPUV);
		luv[2] = CustomData_bmesh_get(&bm->ldata, ls[2]->head.data, CD_MLOOPUV);
	}

	if (has_col) {
		lcol[0] = CustomData_bmesh_get(&bm->ldata, ls[0]->head.data, CD_MLOOPCOL);
		lcol[1] = CustomData_bmesh_get(&bm->ldata, ls[1]->head.data, CD_MLOOPCOL);
		lcol[2] = CustomData_bmesh_get(&bm->ldata, ls[2]->head.data, CD_MLOOPCOL);
	}


}

static void emDM_drawFacesTex_common(
		DerivedMesh *dm,
		int (*drawParams)(MTFace *tface, int has_vcol, int matnr),
		int (*drawParamsMapped)(void *userData, int index),
		int (*compareDrawOptions)(void *userData, int cur_index, int next_index),
		void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMEditMesh *em = bmdm->tc;
	BMesh *bm= bmdm->tc->bm;
	float (*vertexCos)[3]= bmdm->vertexCos;
	float (*vertexNos)[3]= bmdm->vertexNos;
	BMFace *efa;
	MLoopUV *luv[3], dummyluv = {{0}};
	MLoopCol *lcol[3], dummylcol = {0};
	int i, has_vcol = CustomData_has_layer(&bm->ldata, CD_MLOOPCOL);
	int has_uv = CustomData_has_layer(&bm->pdata, CD_MTEXPOLY);

	(void) compareDrawOptions;

	luv[0] = luv[1] = luv[2] = &dummyluv;
	lcol[0] = lcol[1] = lcol[2] = &dummylcol;

	dummylcol.a = dummylcol.r = dummylcol.g = dummylcol.b = 255;

	/* always use smooth shading even for flat faces, else vertex colors wont interpolate */
	glShadeModel(GL_SMOOTH);

	BM_ElemIndex_Ensure(bm, BM_FACE);

	if (vertexCos) {
		BM_ElemIndex_Ensure(bm, BM_VERT);

		glBegin(GL_TRIANGLES);
		for (i=0; i<em->tottri; i++) {
			BMLoop **ls = em->looptris[i];
			MTexPoly *tp= CustomData_bmesh_get(&bm->pdata, ls[0]->f->head.data, CD_MTEXPOLY);
			MTFace mtf = {{{0}}};
			/*unsigned char *cp= NULL;*/ /*UNUSED*/
			int drawSmooth= BM_TestHFlag(ls[0]->f, BM_SMOOTH);
			int flag;

			efa = ls[0]->f;

			if (has_uv) {
				mtf.flag = tp->flag;
				mtf.tpage = tp->tpage;
				mtf.transp = tp->transp;
				mtf.mode = tp->mode;
				mtf.tile = tp->tile;
				mtf.unwrap = tp->unwrap;
			}

			if (drawParams)
				flag= drawParams(&mtf, has_vcol, efa->mat_nr);
			else if (drawParamsMapped)
				flag= drawParamsMapped(userData, BM_GetIndex(efa));
			else
				flag= 1;

			if (flag != 0) { /* flag 0 == the face is hidden or invisible */

				/* we always want smooth here since otherwise vertex colors dont interpolate */
				if (!has_vcol) {
					glShadeModel(drawSmooth?GL_SMOOTH:GL_FLAT);
				}

				if (!drawSmooth) {
					glNormal3fv(bmdm->faceNos[i]);

					bmdm_get_tri_tex(bm, ls, luv, lcol, has_uv, has_vcol);

					glTexCoord2fv(luv[0]->uv);
					glColor3ub(lcol[0]->b, lcol[0]->g, lcol[0]->r);
					glVertex3fv(vertexCos[BM_GetIndex(ls[0]->v)]);

					glTexCoord2fv(luv[1]->uv);
					glColor3ub(lcol[1]->b, lcol[1]->g, lcol[1]->r);
					glVertex3fv(vertexCos[BM_GetIndex(ls[1]->v)]);

					glTexCoord2fv(luv[2]->uv);
					glColor3ub(lcol[2]->b, lcol[2]->g, lcol[2]->r);
					glVertex3fv(vertexCos[BM_GetIndex(ls[2]->v)]);
				}
				else {
					bmdm_get_tri_tex(bm, ls, luv, lcol, has_uv, has_vcol);

					glTexCoord2fv(luv[0]->uv);
					glColor3ub(lcol[0]->b, lcol[0]->g, lcol[0]->r);
					glNormal3fv(vertexNos[BM_GetIndex(ls[0]->v)]);
					glVertex3fv(vertexCos[BM_GetIndex(ls[0]->v)]);

					glTexCoord2fv(luv[1]->uv);
					glColor3ub(lcol[1]->b, lcol[1]->g, lcol[1]->r);
					glNormal3fv(vertexNos[BM_GetIndex(ls[1]->v)]);
					glVertex3fv(vertexCos[BM_GetIndex(ls[1]->v)]);

					glTexCoord2fv(luv[2]->uv);
					glColor3ub(lcol[2]->b, lcol[2]->g, lcol[2]->r);
					glNormal3fv(vertexNos[BM_GetIndex(ls[2]->v)]);
					glVertex3fv(vertexCos[BM_GetIndex(ls[2]->v)]);
				}
			}
		}
		glEnd();
	}
	else {
		BM_ElemIndex_Ensure(bm, BM_VERT);

		for (i=0; i<em->tottri; i++) {
			BMLoop **ls = em->looptris[i];
			MTexPoly *tp= CustomData_bmesh_get(&bm->pdata, ls[0]->f->head.data, CD_MTEXPOLY);
			MTFace mtf = {{{0}}};
			/*unsigned char *cp= NULL;*/ /*UNUSED*/
			int drawSmooth= BM_TestHFlag(ls[0]->f, BM_SMOOTH);
			int flag;

			efa = ls[0]->f;

			if (has_uv) {
				mtf.flag = tp->flag;
				mtf.tpage = tp->tpage;
				mtf.transp = tp->transp;
				mtf.mode = tp->mode;
				mtf.tile = tp->tile;
				mtf.unwrap = tp->unwrap;
			}

			if (drawParams)
				flag= drawParams(&mtf, has_vcol, efa->mat_nr);
			else if (drawParamsMapped)
				flag= drawParamsMapped(userData, BM_GetIndex(efa));
			else
				flag= 1;

			if (flag != 0) { /* flag 0 == the face is hidden or invisible */

				/* we always want smooth here since otherwise vertex colors dont interpolate */
				if (!has_vcol) {
					glShadeModel(drawSmooth?GL_SMOOTH:GL_FLAT);
				}

				glBegin(GL_TRIANGLES);
				if (!drawSmooth) {
					glNormal3fv(efa->no);

					bmdm_get_tri_tex(bm, ls, luv, lcol, has_uv, has_vcol);

					if (luv[0])
						glTexCoord2fv(luv[0]->uv);
					if (lcol[0])
						glColor3ub(lcol[0]->b, lcol[0]->g, lcol[0]->r);
					else glColor3ub(0, 0, 0);
					glVertex3fv(ls[0]->v->co);

					if (luv[1])
						glTexCoord2fv(luv[1]->uv);
					if (lcol[1])
						glColor3ub(lcol[1]->b, lcol[1]->g, lcol[1]->r);
					else glColor3ub(0, 0, 0);
					glVertex3fv(ls[1]->v->co);

					if (luv[2])
						glTexCoord2fv(luv[2]->uv);
					if (lcol[2])
						glColor3ub(lcol[2]->b, lcol[2]->g, lcol[2]->r);
					else glColor3ub(0, 0, 0);
					glVertex3fv(ls[2]->v->co);
				}
				else {
					bmdm_get_tri_tex(bm, ls, luv, lcol, has_uv, has_vcol);

					if (luv[0])
						glTexCoord2fv(luv[0]->uv);
					if (lcol[0])
						glColor3ub(lcol[0]->b, lcol[0]->g, lcol[0]->r);
					else glColor3ub(0, 0, 0);
					glNormal3fv(ls[0]->v->no);
					glVertex3fv(ls[0]->v->co);

					if (luv[1])
						glTexCoord2fv(luv[1]->uv);
					if (lcol[1])
						glColor3ub(lcol[1]->b, lcol[1]->g, lcol[1]->r);
					else glColor3ub(0, 0, 0);
					glNormal3fv(ls[1]->v->no);
					glVertex3fv(ls[1]->v->co);

					if (luv[2])
						glTexCoord2fv(luv[2]->uv);
					if (lcol[2])
						glColor3ub(lcol[2]->b, lcol[2]->g, lcol[2]->r);
					else glColor3ub(0, 0, 0);
					glNormal3fv(ls[2]->v->no);
					glVertex3fv(ls[2]->v->co);
				}
				glEnd();
			}
		}
	}
}

static void emDM_drawFacesTex(
		DerivedMesh *dm,
		int (*setDrawOptions)(MTFace *tface, int has_vcol, int matnr),
		int (*compareDrawOptions)(void *userData, int cur_index, int next_index),
		void *userData)
{
	emDM_drawFacesTex_common(dm, setDrawOptions, NULL, compareDrawOptions, userData);
}

static void emDM_drawMappedFacesTex(
		DerivedMesh *dm,
		int (*setDrawOptions)(void *userData, int index),
		int (*compareDrawOptions)(void *userData, int cur_index, int next_index),
		void *userData)
{
	emDM_drawFacesTex_common(dm, NULL, setDrawOptions, compareDrawOptions, userData);
}

static void emDM_drawMappedFacesGLSL(
		DerivedMesh *dm,
		int (*setMaterial)(int, void *attribs),
		int (*setDrawOptions)(void *userData, int index),
		void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMesh *bm= bmdm->tc->bm;
	BMEditMesh *em = bmdm->tc;
	float (*vertexCos)[3]= bmdm->vertexCos;
	float (*vertexNos)[3]= bmdm->vertexNos;
	BMFace *efa;
	BMLoop **ltri;
	DMVertexAttribs attribs;
	GPUVertexAttribs gattribs;

	int i, b, matnr, new_matnr, dodraw;

	dodraw = 0;
	matnr = -1;

	memset(&attribs, 0, sizeof(attribs));

	/* always use smooth shading even for flat faces, else vertex colors wont interpolate */
	glShadeModel(GL_SMOOTH);
	BM_ElemIndex_Ensure(bm, BM_VERT | BM_FACE);

#define PASSATTRIB(loop, eve, vert) {											\
	if (attribs.totorco) {														\
		float *orco = attribs.orco.array[BM_GetIndex(eve)];						\
		glVertexAttrib3fvARB(attribs.orco.glIndex, orco);						\
	}																			\
	for (b = 0; b < attribs.tottface; b++) {									\
		MLoopUV *_luv = CustomData_bmesh_get_n(&bm->ldata, loop->head.data, CD_MLOOPUV, b);\
		glVertexAttrib2fvARB(attribs.tface[b].glIndex, _luv->uv);				\
	}																			\
	for (b = 0; b < attribs.totmcol; b++) {										\
		MLoopCol *_cp = CustomData_bmesh_get_n(&bm->ldata, loop->head.data, CD_MLOOPCOL, b);\
		GLubyte _col[4];														\
		_col[0]= _cp->b; _col[1]= _cp->g; _col[2]= _cp->r; _col[3]= _cp->a;		\
		glVertexAttrib4ubvARB(attribs.mcol[b].glIndex, _col);					\
	}																			\
	if (attribs.tottang) {														\
		float *tang = attribs.tang.array[i*4 + vert];							\
		glVertexAttrib3fvARB(attribs.tang.glIndex, tang);						\
	}																			\
	}


	for (i=0, ltri=em->looptris[0]; i<em->tottri; i++, ltri += 3) {
		int drawSmooth;

		efa = ltri[0]->f;
		drawSmooth= BM_TestHFlag(efa, BM_SMOOTH);

		if (setDrawOptions && !setDrawOptions(userData, BM_GetIndex(efa)))
			continue;

		new_matnr = efa->mat_nr + 1;
		if (new_matnr != matnr) {
			dodraw = setMaterial(matnr = new_matnr, &gattribs);
			if (dodraw)
				DM_vertex_attributes_from_gpu(dm, &gattribs, &attribs);
		}

		if (dodraw) {
			glBegin(GL_TRIANGLES);
			if (!drawSmooth) {
				if (vertexCos) glNormal3fv(bmdm->faceNos[i]);
				else glNormal3fv(efa->no);

				PASSATTRIB(ltri[0], ltri[0]->v, 0);
				if (vertexCos) glVertex3fv(vertexCos[BM_GetIndex(ltri[0]->v)]);
				else glVertex3fv(ltri[0]->v->co);

				PASSATTRIB(ltri[1], ltri[1]->v, 1);
				if (vertexCos) glVertex3fv(vertexCos[BM_GetIndex(ltri[1]->v)]);
				else glVertex3fv(ltri[1]->v->co);

				PASSATTRIB(ltri[2], ltri[2]->v, 2);
				if (vertexCos) glVertex3fv(vertexCos[BM_GetIndex(ltri[2]->v)]);
				else glVertex3fv(ltri[2]->v->co);
			}
			else {
				PASSATTRIB(ltri[0], ltri[0]->v, 0);
				if (vertexCos) {
					glNormal3fv(vertexNos[BM_GetIndex(ltri[0]->v)]);
					glVertex3fv(vertexCos[BM_GetIndex(ltri[0]->v)]);
				}
				else {
					glNormal3fv(ltri[0]->v->no);
					glVertex3fv(ltri[0]->v->co);
				}

				PASSATTRIB(ltri[1], ltri[1]->v, 1);
				if (vertexCos) {
					glNormal3fv(vertexNos[BM_GetIndex(ltri[1]->v)]);
					glVertex3fv(vertexCos[BM_GetIndex(ltri[1]->v)]);
				}
				else {
					glNormal3fv(ltri[1]->v->no);
					glVertex3fv(ltri[1]->v->co);
				}

				PASSATTRIB(ltri[2], ltri[2]->v, 2);
				if (vertexCos) {
					glNormal3fv(vertexNos[BM_GetIndex(ltri[2]->v)]);
					glVertex3fv(vertexCos[BM_GetIndex(ltri[2]->v)]);
				}
				else {
					glNormal3fv(ltri[2]->v->no);
					glVertex3fv(ltri[2]->v->co);
				}
			}
			glEnd();
		}
	}
#undef PASSATTRIB
}

static void emDM_drawFacesGLSL(
		DerivedMesh *dm,
		int (*setMaterial)(int, void *attribs))
{
	dm->drawMappedFacesGLSL(dm, setMaterial, NULL, NULL);
}

static void emDM_drawMappedFacesMat(
		DerivedMesh *dm,
		void (*setMaterial)(void *userData, int, void *attribs),
		int (*setFace)(void *userData, int index), void *userData)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMesh *bm= bmdm->tc->bm;
	BMEditMesh *em = bmdm->tc;
	float (*vertexCos)[3]= bmdm->vertexCos;
	float (*vertexNos)[3]= bmdm->vertexNos;
	BMFace *efa;
	BMLoop **ltri;
	DMVertexAttribs attribs= {{{0}}};
	GPUVertexAttribs gattribs;
	int i, b, matnr, new_matnr;

	matnr = -1;

	/* always use smooth shading even for flat faces, else vertex colors wont interpolate */
	glShadeModel(GL_SMOOTH);

	BM_ElemIndex_Ensure(bm, BM_VERT);

#define PASSATTRIB(loop, eve, vert) {											\
	if (attribs.totorco) {														\
		float *orco = attribs.orco.array[BM_GetIndex(eve)];						\
		glVertexAttrib3fvARB(attribs.orco.glIndex, orco);						\
	}																			\
	for (b = 0; b < attribs.tottface; b++) {									\
		MLoopUV *_luv = CustomData_bmesh_get_n(&bm->ldata, loop->head.data, CD_MLOOPUV, b);\
		glVertexAttrib2fvARB(attribs.tface[b].glIndex, _luv->uv);				\
	}																			\
	for (b = 0; b < attribs.totmcol; b++) {										\
		MLoopCol *_cp = CustomData_bmesh_get_n(&bm->ldata, loop->head.data, CD_MLOOPCOL, b);\
		GLubyte _col[4];														\
		_col[0]= _cp->b; _col[1]= _cp->g; _col[2]= _cp->r; _col[3]= _cp->a;		\
		glVertexAttrib4ubvARB(attribs.mcol[b].glIndex, _col);					\
	}																			\
	if (attribs.tottang) {														\
		float *tang = attribs.tang.array[i*4 + vert];							\
		glVertexAttrib4fvARB(attribs.tang.glIndex, tang);						\
	}																			\
}

	for (i=0, ltri=em->looptris[0]; i<em->tottri; i++, ltri += 3) {
		int drawSmooth;

		efa = ltri[0]->f;
		drawSmooth = BM_TestHFlag(efa, BM_SMOOTH);

		/* face hiding */
		if (setFace && !setFace(userData, BM_GetIndex(efa)))
			continue;

		/* material */
		new_matnr = efa->mat_nr + 1;
		if (new_matnr != matnr) {
			setMaterial(userData, matnr = new_matnr, &gattribs);
			DM_vertex_attributes_from_gpu(dm, &gattribs, &attribs);
		}

		/* face */
		glBegin(GL_TRIANGLES);
		if (!drawSmooth) {
			if (vertexCos) glNormal3fv(bmdm->faceNos[i]);
			else glNormal3fv(efa->no);

			PASSATTRIB(ltri[0], ltri[0]->v, 0);
			if (vertexCos) glVertex3fv(vertexCos[BM_GetIndex(ltri[0]->v)]);
			else glVertex3fv(ltri[0]->v->co);

			PASSATTRIB(ltri[1], ltri[1]->v, 1);
			if (vertexCos) glVertex3fv(vertexCos[BM_GetIndex(ltri[1]->v)]);
			else glVertex3fv(ltri[1]->v->co);

			PASSATTRIB(ltri[2], ltri[2]->v, 2);
			if (vertexCos) glVertex3fv(vertexCos[BM_GetIndex(ltri[2]->v)]);
			else glVertex3fv(ltri[2]->v->co);

		}
		else {
			PASSATTRIB(ltri[0], ltri[0]->v, 0);
			if (vertexCos) {
				glNormal3fv(vertexNos[BM_GetIndex(ltri[0]->v)]);
				glVertex3fv(vertexCos[BM_GetIndex(ltri[0]->v)]);
			}
			else {
				glNormal3fv(ltri[0]->v->no);
				glVertex3fv(ltri[0]->v->co);
			}

			PASSATTRIB(ltri[1], ltri[1]->v, 1);
			if (vertexCos) {
				glNormal3fv(vertexNos[BM_GetIndex(ltri[1]->v)]);
				glVertex3fv(vertexCos[BM_GetIndex(ltri[1]->v)]);
			}
			else {
				glNormal3fv(ltri[1]->v->no);
				glVertex3fv(ltri[1]->v->co);
			}

			PASSATTRIB(ltri[2], ltri[2]->v, 2);
			if (vertexCos) {
				glNormal3fv(vertexNos[BM_GetIndex(ltri[2]->v)]);
				glVertex3fv(vertexCos[BM_GetIndex(ltri[2]->v)]);
			}
			else {
				glNormal3fv(ltri[2]->v->no);
				glVertex3fv(ltri[2]->v->co);
			}
		}
		glEnd();
	}
#undef PASSATTRIB
}

static void emDM_getMinMax(DerivedMesh *dm, float min_r[3], float max_r[3])
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMVert *eve;
	BMIter iter;
	int i;

	if (bmdm->tc->bm->totvert) {
		eve = BMIter_New(&iter, bmdm->tc->bm, BM_VERTS_OF_MESH, NULL);
		for (i=0; eve; eve=BMIter_Step(&iter), i++) {
			if (bmdm->vertexCos) {
				DO_MINMAX(bmdm->vertexCos[i], min_r, max_r);
			}
			else {
				DO_MINMAX(eve->co, min_r, max_r);
			}
		}
	}
	else {
		min_r[0] = min_r[1] = min_r[2] = max_r[0] = max_r[1] = max_r[2] = 0.0;
	}
}
static int emDM_getNumVerts(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;

	return bmdm->tc->bm->totvert;
}

static int emDM_getNumEdges(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;

	return bmdm->tc->bm->totedge;
}

static int emDM_getNumTessFaces(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;

	return bmdm->tc->tottri;
}

static int emDM_getNumLoops(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;

	return bmdm->tc->bm->totloop;
}

static int emDM_getNumPolys(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;

	return bmdm->tc->bm->totface;
}

static int bmvert_to_mvert(BMesh *bm, BMVert *ev, MVert *vert_r)
{
	copy_v3_v3(vert_r->co, ev->co);

	normal_float_to_short_v3(vert_r->no, ev->no);

	vert_r->flag = BM_Vert_Flag_To_MEFlag(ev);

	if (CustomData_has_layer(&bm->vdata, CD_BWEIGHT)) {
		vert_r->bweight = (unsigned char) (BM_GetCDf(&bm->vdata, ev, CD_BWEIGHT)*255.0f);
	}

	return 1;
}

static void emDM_getVert(DerivedMesh *dm, int index, MVert *vert_r)
{
	BMVert *ev;

	if (index < 0 || index >= ((EditDerivedBMesh *)dm)->tv) {
		printf("error in emDM_getVert.\n");
		return;
	}

	ev = ((EditDerivedBMesh *)dm)->vtable[index];
	bmvert_to_mvert(((EditDerivedBMesh *)dm)->tc->bm, ev, vert_r);
}

static void emDM_getEdge(DerivedMesh *dm, int index, MEdge *edge_r)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh *)dm;
	BMesh *bm = ((EditDerivedBMesh *)dm)->tc->bm;
	BMEdge *e;

	if (index < 0 || index >= ((EditDerivedBMesh *)dm)->te) {
		printf("error in emDM_getEdge.\n");
		return;
	}

	e = bmdm->etable[index];

	if (CustomData_has_layer(&bm->edata, CD_BWEIGHT)) {
		edge_r->bweight = (unsigned char) (BM_GetCDf(&bm->edata, e, CD_BWEIGHT)*255.0f);
	}

	if (CustomData_has_layer(&bm->edata, CD_CREASE)) {
		edge_r->crease = (unsigned char) (BM_GetCDf(&bm->edata, e, CD_CREASE)*255.0f);
	}

	edge_r->flag = BM_Edge_Flag_To_MEFlag(e);

	edge_r->v1 = GET_INT_FROM_POINTER(BLI_ghash_lookup(bmdm->vhash, e->v1));
	edge_r->v2 = GET_INT_FROM_POINTER(BLI_ghash_lookup(bmdm->vhash, e->v2));
}

static void emDM_getTessFace(DerivedMesh *dm, int index, MFace *face_r)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh *)dm;
	BMFace *ef;
	BMLoop **l;

	if (index < 0 || index >= ((EditDerivedBMesh *)dm)->tf) {
		printf("error in emDM_getTessFace.\n");
		return;
	}

	l = ((EditDerivedBMesh *)dm)->tc->looptris[index];

	ef = l[0]->f;

	face_r->mat_nr = (unsigned char) ef->mat_nr;
	face_r->flag = BM_Face_Flag_To_MEFlag(ef);

	face_r->v1 = GET_INT_FROM_POINTER(BLI_ghash_lookup(bmdm->vhash, l[0]->v));
	face_r->v2 = GET_INT_FROM_POINTER(BLI_ghash_lookup(bmdm->vhash, l[1]->v));
	face_r->v3 = GET_INT_FROM_POINTER(BLI_ghash_lookup(bmdm->vhash, l[2]->v));
	face_r->v4 = 0;

	test_index_face(face_r, NULL, 0, 3);
}

static void emDM_copyVertArray(DerivedMesh *dm, MVert *vert_r)
{
	BMesh *bm = ((EditDerivedBMesh *)dm)->tc->bm;
	BMVert *ev;
	BMIter iter;

	ev = BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL);
	for ( ; ev; ev = BMIter_Step(&iter), ++vert_r) {
		copy_v3_v3(vert_r->co, ev->co);

		normal_float_to_short_v3(vert_r->no, ev->no);

		vert_r->flag = BM_Vert_Flag_To_MEFlag(ev);

		if (CustomData_has_layer(&bm->vdata, CD_BWEIGHT)) {
			vert_r->bweight = (unsigned char) (BM_GetCDf(&bm->vdata, ev, CD_BWEIGHT)*255.0f);
		}
	}
}

static void emDM_copyEdgeArray(DerivedMesh *dm, MEdge *edge_r)
{
	BMesh *bm = ((EditDerivedBMesh *)dm)->tc->bm;
	BMEdge *ee;
	BMIter iter;
	int has_bweight = CustomData_has_layer(&bm->edata, CD_BWEIGHT);
	int has_crease = CustomData_has_layer(&bm->edata, CD_CREASE);

	BM_ElemIndex_Ensure(bm, BM_VERT);

	ee = BMIter_New(&iter, bm, BM_EDGES_OF_MESH, NULL);
	for ( ; ee; ee=BMIter_Step(&iter), edge_r++) {
		if (has_bweight) {
			edge_r->bweight = (unsigned char) (BM_GetCDf(&bm->edata, ee, CD_BWEIGHT)*255.0f);
		}

		if (has_crease) {
			edge_r->crease = (unsigned char) (BM_GetCDf(&bm->edata, ee, CD_CREASE)*255.0f);
		}

		edge_r->flag = BM_Edge_Flag_To_MEFlag(ee);

		edge_r->v1 = (int)BM_GetIndex(ee->v1);
		edge_r->v2 = (int)BM_GetIndex(ee->v2);
	}
}

static void emDM_copyTessFaceArray(DerivedMesh *dm, MFace *face_r)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh *)dm;
	BMesh *bm = ((EditDerivedBMesh *)dm)->tc->bm;
	BMFace *ef;
	BMLoop **l;
	int i;

	BM_ElemIndex_Ensure(bm, BM_VERT);

	for (i=0; i<bmdm->tc->tottri; i++, face_r++) {
		l = bmdm->tc->looptris[i];
		ef = l[0]->f;

		face_r->mat_nr = (unsigned char) ef->mat_nr;

		face_r->flag = BM_Face_Flag_To_MEFlag(ef);

		face_r->v1 = BM_GetIndex(l[0]->v);
		face_r->v2 = BM_GetIndex(l[1]->v);
		face_r->v3 = BM_GetIndex(l[2]->v);
		face_r->v4 = 0;

		test_index_face(face_r, NULL, 0, 3);
	}
}


static void emDM_copyLoopArray(DerivedMesh *dm, MLoop *loop_r)
{
	/* EditDerivedBMesh *bmdm = (EditDerivedBMesh *)dm; */ /* UNUSED */
	BMesh *bm = ((EditDerivedBMesh *)dm)->tc->bm;
	BMIter iter, liter;
	BMFace *f;
	BMLoop *l;

	BM_ElemIndex_Ensure(bm, BM_VERT | BM_EDGE);

	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
			loop_r->v = BM_GetIndex(l->v);
			loop_r->e = BM_GetIndex(l->e);
			loop_r++;
		}
	}
}

static void emDM_copyPolyArray(DerivedMesh *dm, MPoly *poly_r)
{
	/* EditDerivedBMesh *bmdm = (EditDerivedBMesh *)dm; */ /* UNUSED */
	BMesh *bm = ((EditDerivedBMesh *)dm)->tc->bm;
	BMIter iter;
	BMFace *f;
	int i;

	i = 0;
	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		poly_r->flag = BM_Face_Flag_To_MEFlag(f);
		poly_r->loopstart = i;
		poly_r->totloop = f->len;
		poly_r->mat_nr = f->mat_nr;

		poly_r++;
		i += f->len;
	}
}

static void *emDM_getTessFaceDataArray(DerivedMesh *dm, int type)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh*) dm;
	BMesh *bm= bmdm->tc->bm;
	BMFace *efa;
	char *data, *bmdata;
	void *datalayer;
	int index /*, offset*/ /*UNUSED */, size, i;

	datalayer = DM_get_tessface_data_layer(dm, type);
	if (datalayer)
		return datalayer;

	/* layers are store per face for editmesh, we convert to a tbmporary
	 * data layer array in the derivedmesh when these are requested */
	if (type == CD_MTFACE || type == CD_MCOL) {
		index = CustomData_get_layer_index(&bm->pdata, type);

		if (index != -1) {
			/* offset = bm->pdata.layers[index].offset; */ /* UNUSED */
			size = CustomData_sizeof(type);

			DM_add_tessface_layer(dm, type, CD_CALLOC, NULL);
			index = CustomData_get_layer_index(&dm->faceData, type);
			dm->faceData.layers[index].flag |= CD_FLAG_TEMPORARY;

			data = datalayer = DM_get_tessface_data_layer(dm, type);
			for (i=0; i<bmdm->tc->tottri; i++, data+=size) {
				efa = bmdm->tc->looptris[i][0]->f;
				/*BMESH_TODO: need to still add tface data,
				  derived from the loops.*/
				bmdata = CustomData_bmesh_get(&bm->pdata, efa->head.data, type);
				memcpy(data, bmdata, size);
			}
		}
	}

	return datalayer;
}

static void emDM_getVertCos(DerivedMesh *dm, float (*cos_r)[3])
{
	EditDerivedBMesh *emdm= (EditDerivedBMesh*) dm;
	BMVert *eve;
	BMIter iter;
	int i;

	i= 0;
	BM_ITER(eve, &iter, emdm->tc->bm, BM_VERTS_OF_MESH, NULL) {
		if (emdm->vertexCos) {
			copy_v3_v3(cos_r[i], emdm->vertexCos[i]);
		}
		else {
			copy_v3_v3(cos_r[i], eve->co);
		}

		i++;
	}
}

static void emDM_release(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm= (EditDerivedBMesh *)dm;

	if (DM_release(dm)) {
		if (bmdm->vertexCos) {
			MEM_freeN(bmdm->vertexCos);
			MEM_freeN(bmdm->vertexNos);
			MEM_freeN(bmdm->faceNos);
		}

		if (bmdm->fhash) BLI_ghash_free(bmdm->fhash, NULL, NULL);
		if (bmdm->ehash) BLI_ghash_free(bmdm->ehash, NULL, NULL);
		if (bmdm->vhash) BLI_ghash_free(bmdm->vhash, NULL, NULL);

		if (bmdm->vtable) MEM_freeN(bmdm->vtable);
		if (bmdm->etable) MEM_freeN(bmdm->etable);
		if (bmdm->ftable) MEM_freeN(bmdm->ftable);

		MEM_freeN(bmdm);
	}
}

static CustomData *bmDm_getVertDataLayout(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh*)dm;

	return &bmdm->tc->bm->vdata;
}

static CustomData *bmDm_getEdgeDataLayout(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh*)dm;

	return &bmdm->tc->bm->edata;
}

static CustomData *bmDm_getTessFaceDataLayout(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh*)dm;

	return &bmdm->dm.faceData;
}

static CustomData *bmDm_getLoopDataLayout(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh*)dm;

	return &bmdm->tc->bm->ldata;
}

static CustomData *bmDm_getPolyDataLayout(DerivedMesh *dm)
{
	EditDerivedBMesh *bmdm = (EditDerivedBMesh*)dm;

	return &bmdm->tc->bm->pdata;
}


DerivedMesh *getEditDerivedBMesh(
		BMEditMesh *em,
		Object *UNUSED(ob),
		float (*vertexCos)[3])
{
	EditDerivedBMesh *bmdm = MEM_callocN(sizeof(*bmdm), __func__);
	BMesh *bm = em->bm;

	bmdm->tc = em;

	DM_init((DerivedMesh*)bmdm, DM_TYPE_EDITBMESH, em->bm->totvert,
		 em->bm->totedge, em->tottri, em->bm->totloop, em->bm->totface);

	CustomData_from_bmeshpoly(&bmdm->dm.faceData, &em->bm->pdata, &em->bm->ldata, 0);

	bmdm->dm.getVertCos = emDM_getVertCos;
	bmdm->dm.getMinMax = emDM_getMinMax;

	bmdm->dm.getVertDataLayout = bmDm_getVertDataLayout;
	bmdm->dm.getEdgeDataLayout = bmDm_getEdgeDataLayout;
	bmdm->dm.getTessFaceDataLayout = bmDm_getTessFaceDataLayout;
	bmdm->dm.getLoopDataLayout = bmDm_getLoopDataLayout;
	bmdm->dm.getPolyDataLayout = bmDm_getPolyDataLayout;

	bmdm->dm.getNumVerts = emDM_getNumVerts;
	bmdm->dm.getNumEdges = emDM_getNumEdges;
	bmdm->dm.getNumTessFaces = emDM_getNumTessFaces;
	bmdm->dm.getNumLoops = emDM_getNumLoops;
	bmdm->dm.getNumPolys = emDM_getNumPolys;

	bmdm->dm.getVert = emDM_getVert;
	bmdm->dm.getEdge = emDM_getEdge;
	bmdm->dm.getTessFace = emDM_getTessFace;
	bmdm->dm.copyVertArray = emDM_copyVertArray;
	bmdm->dm.copyEdgeArray = emDM_copyEdgeArray;
	bmdm->dm.copyTessFaceArray = emDM_copyTessFaceArray;
	bmdm->dm.copyLoopArray = emDM_copyLoopArray;
	bmdm->dm.copyPolyArray = emDM_copyPolyArray;

	bmdm->dm.getTessFaceDataArray = emDM_getTessFaceDataArray;

	bmdm->dm.calcNormals = emDM_calcNormals;
	bmdm->dm.recalcTesselation = emDM_recalcTesselation;

	bmdm->dm.foreachMappedVert = emDM_foreachMappedVert;
	bmdm->dm.foreachMappedEdge = emDM_foreachMappedEdge;
	bmdm->dm.foreachMappedFaceCenter = emDM_foreachMappedFaceCenter;

	bmdm->dm.drawEdges = emDM_drawEdges;
	bmdm->dm.drawMappedEdges = emDM_drawMappedEdges;
	bmdm->dm.drawMappedEdgesInterp = emDM_drawMappedEdgesInterp;
	bmdm->dm.drawMappedFaces = emDM_drawMappedFaces;
	bmdm->dm.drawMappedFacesTex = emDM_drawMappedFacesTex;
	bmdm->dm.drawMappedFacesGLSL = emDM_drawMappedFacesGLSL;
	bmdm->dm.drawMappedFacesMat = emDM_drawMappedFacesMat;
	bmdm->dm.drawFacesTex = emDM_drawFacesTex;
	bmdm->dm.drawFacesGLSL = emDM_drawFacesGLSL;
	bmdm->dm.drawUVEdges = emDM_drawUVEdges;

	bmdm->dm.release = emDM_release;

	bmdm->vertexCos = vertexCos;

	if (CustomData_has_layer(&bm->vdata, CD_MDEFORMVERT)) {
		BMIter iter;
		BMVert *eve;
		int i;

		DM_add_vert_layer(&bmdm->dm, CD_MDEFORMVERT, CD_CALLOC, NULL);

		eve = BMIter_New(&iter, bmdm->tc->bm, BM_VERTS_OF_MESH, NULL);
		for (i=0; eve; eve=BMIter_Step(&iter), i++)
			DM_set_vert_data(&bmdm->dm, i, CD_MDEFORMVERT,
							 CustomData_bmesh_get(&bm->vdata, eve->head.data, CD_MDEFORMVERT));
	}

	if (vertexCos) {
		BMVert *eve;
		BMIter iter;
		int totface = bmdm->tc->tottri;
		int i;

		BM_ElemIndex_Ensure(bm, BM_VERT);

		bmdm->vertexNos = MEM_callocN(sizeof(*bmdm->vertexNos) * bm->totvert, "bmdm_vno");
		bmdm->faceNos = MEM_mallocN(sizeof(*bmdm->faceNos)*totface, "bmdm_vno");

		for (i=0; i<bmdm->tc->tottri; i++) {
			BMLoop **l = bmdm->tc->looptris[i];
			float *v1 = vertexCos[(int) BM_GetIndex(l[0]->v)];
			float *v2 = vertexCos[(int) BM_GetIndex(l[1]->v)];
			float *v3 = vertexCos[(int) BM_GetIndex(l[2]->v)];
			float *no = bmdm->faceNos[i];

			normal_tri_v3( no,v1, v2, v3);
			add_v3_v3v3(bmdm->vertexNos[BM_GetIndex(l[0]->v)], bmdm->vertexNos[BM_GetIndex(l[0]->v)], no);
			add_v3_v3v3(bmdm->vertexNos[BM_GetIndex(l[1]->v)], bmdm->vertexNos[BM_GetIndex(l[1]->v)], no);
			add_v3_v3v3(bmdm->vertexNos[BM_GetIndex(l[2]->v)], bmdm->vertexNos[BM_GetIndex(l[2]->v)], no);
		}

		eve=BMIter_New(&iter, bm, BM_VERTS_OF_MESH, NULL);
		for (i=0; eve; eve=BMIter_Step(&iter), i++) {
			float *no = bmdm->vertexNos[i];
			/* following Mesh convention; we use vertex coordinate itself
			 * for normal in this case */
			if (normalize_v3(no)==0.0) {
				copy_v3_v3(no, vertexCos[i]);
				normalize_v3(no);
			}
		}
	}

	//bmdm_recalc_lookups(bmdm);

	return (DerivedMesh*) bmdm;
}
