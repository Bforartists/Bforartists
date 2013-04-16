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

/** \file blender/blenkernel/intern/editmesh.c
 *  \ingroup bke
 */

#include "BLI_math.h"

#include "BKE_cdderivedmesh.h"

#include "MEM_guardedalloc.h"

#include "BKE_editmesh.h"
#include "BLI_scanfill.h"


BMEditMesh *BMEdit_Create(BMesh *bm, const bool do_tessellate)
{
	BMEditMesh *em = MEM_callocN(sizeof(BMEditMesh), __func__);

	em->bm = bm;
	if (do_tessellate) {
		BMEdit_RecalcTessellation(em);
	}

	return em;
}

BMEditMesh *BMEdit_Copy(BMEditMesh *em)
{
	BMEditMesh *em_copy = MEM_callocN(sizeof(BMEditMesh), __func__);
	*em_copy = *em;

	em_copy->derivedCage = em_copy->derivedFinal = NULL;
	em_copy->derivedVertColor = NULL;

	em_copy->bm = BM_mesh_copy(em->bm);

	/* The tessellation is NOT calculated on the copy here,
	 * because currently all the callers of this function use
	 * it to make a backup copy of the BMEditMesh to restore
	 * it in the case of errors in an operation. For perf
	 * reasons, in that case it makes more sense to do the
	 * tessellation only when/if that copy ends up getting
	 * used.*/
	em_copy->looptris = NULL;

	em_copy->vert_index = NULL;
	em_copy->edge_index = NULL;
	em_copy->face_index = NULL;

	return em_copy;
}

static void BMEdit_RecalcTessellation_intern(BMEditMesh *em)
{
	/* use this to avoid locking pthread for _every_ polygon
	 * and calling the fill function */
#define USE_TESSFACE_SPEEDUP

	BMesh *bm = em->bm;

	/* this assumes all faces can be scan-filled, which isn't always true,
	 * worst case we over alloc a little which is acceptable */
	const int looptris_tot = poly_to_tri_count(bm->totface, bm->totloop);
	const int looptris_tot_prev_alloc = em->looptris ? (MEM_allocN_len(em->looptris) / sizeof(*em->looptris)) : 0;

	BMLoop *(*looptris)[3];
	BMIter iter;
	BMFace *efa;
	BMLoop *l;
	int i = 0;

	ScanFillContext sf_ctx;

#if 0
	/* note, we could be clever and re-use this array but would need to ensure
	 * its realloced at some point, for now just free it */
	if (em->looptris) MEM_freeN(em->looptris);

	/* Use em->tottri when set, this means no reallocs while transforming,
	 * (unless scanfill fails), otherwise... */
	/* allocate the length of totfaces, avoid many small reallocs,
	 * if all faces are tri's it will be correct, quads == 2x allocs */
	BLI_array_reserve(looptris, (em->tottri && em->tottri < bm->totface * 3) ? em->tottri : bm->totface);
#else

	/* this means no reallocs for quad dominant models, for */
	if ((em->looptris != NULL) &&
	    /* (em->tottri >= looptris_tot)) */
	    /* check against alloc'd size incase we over alloc'd a little */
	    ((looptris_tot_prev_alloc >= looptris_tot) && (looptris_tot_prev_alloc <= looptris_tot * 2)))
	{
		looptris = em->looptris;
	}
	else {
		if (em->looptris) MEM_freeN(em->looptris);
		looptris = MEM_mallocN(sizeof(*looptris) * looptris_tot, __func__);
	}

#endif

	BM_ITER_MESH (efa, &iter, bm, BM_FACES_OF_MESH) {
		/* don't consider two-edged faces */
		if (UNLIKELY(efa->len < 3)) {
			/* do nothing */
		}

#ifdef USE_TESSFACE_SPEEDUP

		/* no need to ensure the loop order, we know its ok */

		else if (efa->len == 3) {
#if 0
			int j;
			BM_ITER_ELEM_INDEX (l, &liter, efa, BM_LOOPS_OF_FACE, j) {
				looptris[i][j] = l;
			}
			i += 1;
#else
			/* more cryptic but faster */
			BMLoop **l_ptr = looptris[i++];
			l_ptr[0] = l = BM_FACE_FIRST_LOOP(efa);
			l_ptr[1] = l = l->next;
			l_ptr[2] = l->next;
#endif
		}
		else if (efa->len == 4) {
#if 0
			BMLoop *ltmp[4];
			int j;
			BLI_array_grow_items(looptris, 2);
			BM_ITER_ELEM_INDEX (l, &liter, efa, BM_LOOPS_OF_FACE, j) {
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
#else
			/* more cryptic but faster */
			BMLoop **l_ptr_a = looptris[i++];
			BMLoop **l_ptr_b = looptris[i++];
			(l_ptr_a[0] = l_ptr_b[0] = l = BM_FACE_FIRST_LOOP(efa));
			(l_ptr_a[1]              = l = l->next);
			(l_ptr_a[2] = l_ptr_b[1] = l = l->next);
			(             l_ptr_b[2] = l->next);
#endif
		}

#endif /* USE_TESSFACE_SPEEDUP */

		else {
			int j;
			BMLoop *l_iter;
			BMLoop *l_first;

			ScanFillVert *sf_vert, *sf_vert_last = NULL, *sf_vert_first = NULL;
			/* ScanFillEdge *e; */ /* UNUSED */
			ScanFillFace *sf_tri;
			int totfilltri;

			BLI_scanfill_begin(&sf_ctx);

			/* scanfill time */
			j = 0;
			l_iter = l_first = BM_FACE_FIRST_LOOP(efa);
			do {
				sf_vert = BLI_scanfill_vert_add(&sf_ctx, l_iter->v->co);
				sf_vert->tmp.p = l_iter;

				if (sf_vert_last) {
					/* e = */ BLI_scanfill_edge_add(&sf_ctx, sf_vert_last, sf_vert);
				}

				sf_vert_last = sf_vert;
				if (sf_vert_first == NULL) {
					sf_vert_first = sf_vert;
				}

				/*mark order */
				BM_elem_index_set(l_iter, j++); /* set_loop */

			} while ((l_iter = l_iter->next) != l_first);

			/* complete the loop */
			BLI_scanfill_edge_add(&sf_ctx, sf_vert_first, sf_vert);

			totfilltri = BLI_scanfill_calc_ex(&sf_ctx, 0, efa->no);
			BLI_assert(totfilltri <= efa->len - 2);
			(void)totfilltri;

			for (sf_tri = sf_ctx.fillfacebase.first; sf_tri; sf_tri = sf_tri->next) {
				BMLoop **l_ptr = looptris[i++];
				BMLoop *l1 = sf_tri->v1->tmp.p;
				BMLoop *l2 = sf_tri->v2->tmp.p;
				BMLoop *l3 = sf_tri->v3->tmp.p;

				if (BM_elem_index_get(l1) > BM_elem_index_get(l2)) { SWAP(BMLoop *, l1, l2); }
				if (BM_elem_index_get(l2) > BM_elem_index_get(l3)) { SWAP(BMLoop *, l2, l3); }
				if (BM_elem_index_get(l1) > BM_elem_index_get(l2)) { SWAP(BMLoop *, l1, l2); }

				l_ptr[0] = l1;
				l_ptr[1] = l2;
				l_ptr[2] = l3;
			}

			BLI_scanfill_end(&sf_ctx);
		}
	}

	em->tottri = i;
	em->looptris = looptris;

	BLI_assert(em->tottri <= looptris_tot);

#undef USE_TESSFACE_SPEEDUP

}

void BMEdit_RecalcTessellation(BMEditMesh *em)
{
	BMEdit_RecalcTessellation_intern(em);

	/* commented because editbmesh_build_data() ensures we get tessfaces */
#if 0
	if (em->derivedFinal && em->derivedFinal == em->derivedCage) {
		if (em->derivedFinal->recalcTessellation)
			em->derivedFinal->recalcTessellation(em->derivedFinal);
	}
	else if (em->derivedFinal) {
		if (em->derivedCage->recalcTessellation)
			em->derivedCage->recalcTessellation(em->derivedCage);
		if (em->derivedFinal->recalcTessellation)
			em->derivedFinal->recalcTessellation(em->derivedFinal);
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
		if (em->derivedFinal != em->derivedCage) {
			em->derivedFinal->needsFree = 1;
			em->derivedFinal->release(em->derivedFinal);
		}
		em->derivedFinal = NULL;
	}
	if (em->derivedCage) {
		em->derivedCage->needsFree = 1;
		em->derivedCage->release(em->derivedCage);
		em->derivedCage = NULL;
	}

	if (em->derivedVertColor) MEM_freeN(em->derivedVertColor);

	if (em->looptris) MEM_freeN(em->looptris);

	if (em->vert_index) MEM_freeN(em->vert_index);
	if (em->edge_index) MEM_freeN(em->edge_index);
	if (em->face_index) MEM_freeN(em->face_index);

	if (em->bm)
		BM_mesh_free(em->bm);
}
