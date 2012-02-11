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
 * Contributor(s): Geoffrey Bantle.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/bmesh/intern/bmesh_mesh.c
 *  \ingroup bmesh
 *
 * BM mesh level functions.
 */

#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"
#include "DNA_object_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"

#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"

#include "BKE_utildefines.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_tessmesh.h"
#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_multires.h"

#include "ED_mesh.h"

#include "bmesh.h"
#include "bmesh_private.h"

/* bmesh_error stub */
void bmesh_error(void)
{
	printf("BM modelling error!\n");

	/* This placeholder assert makes modelling errors easier to catch
	 * in the debugger, until bmesh_error is replaced with something
	 * better. */
	BLI_assert(0);
}

/*
 *	BMESH MAKE MESH
 *
 *  Allocates a new BMesh structure.
 *  Returns -
 *  Pointer to a BM
 *
 */

BMesh *BM_Make_Mesh(struct Object *ob, int allocsize[4])
{
	/* allocate the structure */
	BMesh *bm = MEM_callocN(sizeof(BMesh), __func__);
	int vsize, esize, lsize, fsize, lstsize;

	vsize = sizeof(BMVert);
	esize = sizeof(BMEdge);
	lsize = sizeof(BMLoop);
	fsize = sizeof(BMFace);
	lstsize = sizeof(BMLoopList);

	bm->ob = ob;
	
	/* allocate the memory pools for the mesh elements */
	bm->vpool = BLI_mempool_create(vsize, allocsize[0], allocsize[0], FALSE, TRUE);
	bm->epool = BLI_mempool_create(esize, allocsize[1], allocsize[1], FALSE, TRUE);
	bm->lpool = BLI_mempool_create(lsize, allocsize[2], allocsize[2], FALSE, FALSE);
	bm->looplistpool = BLI_mempool_create(lstsize, allocsize[3], allocsize[3], FALSE, FALSE);
	bm->fpool = BLI_mempool_create(fsize, allocsize[3], allocsize[3], FALSE, TRUE);

	/* allocate one flag pool that we dont get rid of. */
	bm->toolflagpool = BLI_mempool_create(sizeof(BMFlagLayer), 512, 512, FALSE, FALSE);
	bm->stackdepth = 1;
	bm->totflags = 1;

	return bm;
}

/*
 *	BMESH FREE MESH
 *
 *	Frees a BMesh structure.
 */

void BM_Free_Mesh_Data(BMesh *bm)
{
	BMVert *v;
	BMEdge *e;
	BMLoop *l;
	BMFace *f;
	

	BMIter verts;
	BMIter edges;
	BMIter faces;
	BMIter loops;
	
	for (v = BMIter_New(&verts, bm, BM_VERTS_OF_MESH, bm); v; v = BMIter_Step(&verts)) {
		CustomData_bmesh_free_block(&(bm->vdata), &(v->head.data));
	}
	for (e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm); e; e = BMIter_Step(&edges)) {
		CustomData_bmesh_free_block(&(bm->edata), &(e->head.data));
	}
	for (f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm); f; f = BMIter_Step(&faces)) {
		CustomData_bmesh_free_block(&(bm->pdata), &(f->head.data));
		for (l = BMIter_New(&loops, bm, BM_LOOPS_OF_FACE, f); l; l = BMIter_Step(&loops)) {
			CustomData_bmesh_free_block(&(bm->ldata), &(l->head.data));
		}
	}

	/* Free custom data pools, This should probably go in CustomData_free? */
	if (bm->vdata.totlayer) BLI_mempool_destroy(bm->vdata.pool);
	if (bm->edata.totlayer) BLI_mempool_destroy(bm->edata.pool);
	if (bm->ldata.totlayer) BLI_mempool_destroy(bm->ldata.pool);
	if (bm->pdata.totlayer) BLI_mempool_destroy(bm->pdata.pool);

	/* free custom data */
	CustomData_free(&bm->vdata, 0);
	CustomData_free(&bm->edata, 0);
	CustomData_free(&bm->ldata, 0);
	CustomData_free(&bm->pdata, 0);

	/* destroy element pools */
	BLI_mempool_destroy(bm->vpool);
	BLI_mempool_destroy(bm->epool);
	BLI_mempool_destroy(bm->lpool);
	BLI_mempool_destroy(bm->fpool);

	/* destroy flag pool */
	BLI_mempool_destroy(bm->toolflagpool);
	BLI_mempool_destroy(bm->looplistpool);

	/* These tables aren't used yet, so it's not stricly necessary
	 * to 'end' them (with 'e' param) but if someone tries to start
	 * using them, having these in place will save a lot of pain */
	mesh_octree_table(NULL, NULL, NULL, 'e');
	mesh_mirrtopo_table(NULL, 'e');

	BLI_freelistN(&bm->selected);

	BMO_ClearStack(bm);
}

void BM_Clear_Mesh(BMesh *bm)
{
	/* allocate the structure */
	int vsize, esize, lsize, fsize, lstsize;
	/* I really need to make the allocation sizes defines, there's no reason why the API
	 * should allow client code to mess around with this - joeedh */
	int allocsize[5] = {512, 512, 512, 2048, 512};
	Object *ob = bm->ob;
	
	/* free old mesh */
	BM_Free_Mesh_Data(bm);
	memset(bm, 0, sizeof(BMesh));
	
	/* re-initialize mesh */
	vsize = sizeof(BMVert);
	esize = sizeof(BMEdge);
	lsize = sizeof(BMLoop);
	fsize = sizeof(BMFace);
	lstsize = sizeof(BMLoopList);

	bm->ob = ob;
	
	/* allocate the memory pools for the mesh elements */
	bm->vpool = BLI_mempool_create(vsize, allocsize[0], allocsize[0], FALSE, TRUE);
	bm->epool = BLI_mempool_create(esize, allocsize[1], allocsize[1], FALSE, TRUE);
	bm->lpool = BLI_mempool_create(lsize, allocsize[2], allocsize[2], FALSE, FALSE);
	bm->looplistpool = BLI_mempool_create(lstsize, allocsize[3], allocsize[3], FALSE, FALSE);
	bm->fpool = BLI_mempool_create(fsize, allocsize[4], allocsize[4], FALSE, TRUE);

	/* allocate one flag pool that we dont get rid of. */
	bm->toolflagpool = BLI_mempool_create(sizeof(BMFlagLayer), 512, 512, FALSE, FALSE);
	bm->stackdepth = 1;
	bm->totflags = 1;
}

/*
 *	BMESH FREE MESH
 *
 *	Frees a BMesh structure.
 */

void BM_Free_Mesh(BMesh *bm)
{
	BM_Free_Mesh_Data(bm);
	MEM_freeN(bm);
}

/*
 *  BMESH COMPUTE NORMALS
 *
 *  Updates the normals of a mesh.
 *  Note that this can only be called
 *
 */

void BM_Compute_Normals(BMesh *bm)
{
	BMVert *v;
	BMFace *f;
	BMLoop *l;
	BMEdge *e;
	BMIter verts;
	BMIter faces;
	BMIter loops;
	BMIter edges;
	unsigned int maxlength = 0;
	int index;
	float (*projectverts)[3];
	float (*edgevec)[3];

	/* first, find out the largest face in mesh */
	BM_ITER(f, &faces, bm, BM_FACES_OF_MESH, NULL) {
		if (BM_TestHFlag(f, BM_HIDDEN))
			continue;

		if (f->len > maxlength) maxlength = f->len;
	}
	
	/* make sure we actually have something to do */
	if (maxlength < 3) return;

	/* allocate projectverts array */
	projectverts = MEM_callocN(sizeof(float) * maxlength * 3, "BM normal computation array");
	
	/* calculate all face normals */
	BM_ITER(f, &faces, bm, BM_FACES_OF_MESH, NULL) {
		if (BM_TestHFlag(f, BM_HIDDEN))
			continue;
#if 0	/* UNUSED */
		if (f->head.flag & BM_NONORMCALC)
			continue;
#endif

		bmesh_update_face_normal(bm, f, f->no, projectverts);
	}
	
	/* Zero out vertex normals */
	BM_ITER(v, &verts, bm, BM_VERTS_OF_MESH, NULL) {
		if (BM_TestHFlag(v, BM_HIDDEN))
			continue;

		zero_v3(v->no);
	}

	/* compute normalized direction vectors for each edge. directions will be
	 * used below for calculating the weights of the face normals on the vertex
	 * normals */
	index = 0;
	edgevec = MEM_callocN(sizeof(float) * 3 * bm->totedge, "BM normal computation array");
	BM_ITER(e, &edges, bm, BM_EDGES_OF_MESH, NULL) {
		BM_SetIndex(e, index); /* set_inline */

		if (e->l) {
			sub_v3_v3v3(edgevec[index], e->v2->co, e->v1->co);
			normalize_v3(edgevec[index]);
		}
		else {
			/* the edge vector will not be needed when the edge has no radial */
		}

		index++;
	}
	bm->elem_index_dirty &= ~BM_EDGE;

	/* add weighted face normals to vertices */
	BM_ITER(f, &faces, bm, BM_FACES_OF_MESH, NULL) {

		if (BM_TestHFlag(f, BM_HIDDEN))
			continue;

		BM_ITER(l, &loops, bm, BM_LOOPS_OF_FACE, f) {
			float *e1diff, *e2diff;
			float dotprod;
			float fac;

			/* calculate the dot product of the two edges that
			 * meet at the loop's vertex */
			e1diff = edgevec[BM_GetIndex(l->prev->e)];
			e2diff = edgevec[BM_GetIndex(l->e)];
			dotprod = dot_v3v3(e1diff, e2diff);

			/* edge vectors are calculated from e->v1 to e->v2, so
			 * adjust the dot product if one but not both loops
			 * actually runs from from e->v2 to e->v1 */
			if ((l->prev->e->v1 == l->prev->v) ^ (l->e->v1 == l->v)) {
				dotprod = -dotprod;
			}

			fac = saacos(-dotprod);

			/* accumulate weighted face normal into the vertex's normal */
			madd_v3_v3fl(l->v->no, f->no, fac);
		}
	}
	
	/* normalize the accumulated vertex normals */
	BM_ITER(v, &verts, bm, BM_VERTS_OF_MESH, NULL) {
		if (BM_TestHFlag(v, BM_HIDDEN))
			continue;

		if (normalize_v3(v->no) == 0.0f) {
			normalize_v3_v3(v->no, v->co);
		}
	}
	
	MEM_freeN(edgevec);
	MEM_freeN(projectverts);
}

/*
 This function ensures correct normals for the mesh, but
 sets the flag BM_TMP_TAG in flipped faces, to allow restoration
 of original normals.
 
 if undo is 0: calculate right normals
 if undo is 1: restore original normals
 */
//keep in sycn with utils.c!
#define FACE_FLIP	8
static void bmesh_rationalize_normals(BMesh *bm, int undo)
{
	BMOperator bmop;
	BMFace *f;
	BMIter iter;
	
	if (undo) {
		BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
			if (BM_TestHFlag(f, BM_TMP_TAG)) {
				BM_flip_normal(bm, f);
			}
			BM_ClearHFlag(f, BM_TMP_TAG);
		}
		
		return;
	}
	
	BMO_InitOpf(bm, &bmop, "righthandfaces faces=%af doflip=%d", FALSE);
	
	BMO_push(bm, &bmop);
	bmesh_righthandfaces_exec(bm, &bmop);
	
	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		if (BMO_TestFlag(bm, f, FACE_FLIP))
			BM_SetHFlag(f, BM_TMP_TAG);
		else BM_ClearHFlag(f, BM_TMP_TAG);
	}

	BMO_pop(bm);
	BMO_Finish_Op(bm, &bmop);
}

static void bmesh_set_mdisps_space(BMesh *bm, int from, int to)
{
	/* switch multires data out of tangent space */
	if (CustomData_has_layer(&bm->ldata, CD_MDISPS)) {
		Object *ob = bm->ob;
		BMEditMesh *em = BMEdit_Create(bm, FALSE);
		DerivedMesh *dm = CDDM_from_BMEditMesh(em, NULL, TRUE, FALSE);
		MDisps *mdisps;
		BMFace *f;
		BMIter iter;
		// int i = 0; // UNUSED
		
		multires_set_space(dm, ob, from, to);
		
		mdisps = CustomData_get_layer(&dm->loopData, CD_MDISPS);
		
		BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
			BMLoop *l;
			BMIter liter;
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
				MDisps *lmd = CustomData_bmesh_get(&bm->ldata, l->head.data, CD_MDISPS);
				
				if (!lmd->disps) {
					printf("%s: warning - 'lmd->disps' == NULL\n", __func__);
				}
				
				if (lmd->disps && lmd->totdisp == mdisps->totdisp) {
					memcpy(lmd->disps, mdisps->disps, sizeof(float) * 3 * lmd->totdisp);
				}
				else if (mdisps->disps) {
					if (lmd->disps)
						MEM_freeN(lmd->disps);
					
					lmd->disps = MEM_dupallocN(mdisps->disps);
					lmd->totdisp = mdisps->totdisp;
				}
				
				mdisps++;
				// i += 1;
			}
		}
		
		dm->needsFree = 1;
		dm->release(dm);
		
		/* setting this to NULL prevents BMEdit_Free from freeing it */
		em->bm = NULL;
		BMEdit_Free(em);
		MEM_freeN(em);
	}
}

/*
 *	BMESH BEGIN/END EDIT
 *
 *	Functions for setting up a mesh for editing and cleaning up after
 *  the editing operations are done. These are called by the tools/operator
 *  API for each time a tool is executed.
 */
void bmesh_begin_edit(BMesh *bm, int flag)
{
	bm->opflag = flag;
	
	/* Most operators seem to be using BMOP_UNTAN_MULTIRES to change the MDisps to
	 * absolute space during mesh edits. With this enabled, changes to the topology
	 * (loop cuts, edge subdivides, etc) are not reflected in the higher levels of
	 * the mesh at all, which doesn't seem right. Turning off completely for now,
	 * until this is shown to be better for certain types of mesh edits. */
#if BMOP_UNTAN_MULTIRES_ENABLED
	/* switch multires data out of tangent space */
	if ((flag & BMOP_UNTAN_MULTIRES) && CustomData_has_layer(&bm->ldata, CD_MDISPS)) {
		bmesh_set_mdisps_space(bm, MULTIRES_SPACE_TANGENT, MULTIRES_SPACE_ABSOLUTE);

		/* ensure correct normals, if possible */
		bmesh_rationalize_normals(bm, 0);
		BM_Compute_Normals(bm);
	}
	else if (flag & BMOP_RATIONALIZE_NORMALS) {
		bmesh_rationalize_normals(bm, 0);
	}
#else
	if (flag & BMOP_RATIONALIZE_NORMALS) {
		bmesh_rationalize_normals(bm, 0);
	}
#endif
}

void bmesh_end_edit(BMesh *bm, int flag)
{
	/* BMOP_UNTAN_MULTIRES disabled for now, see comment above in bmesh_begin_edit. */
#if BMOP_UNTAN_MULTIRES_ENABLED
	/* switch multires data into tangent space */
	if ((flag & BMOP_UNTAN_MULTIRES) && CustomData_has_layer(&bm->ldata, CD_MDISPS)) {
		/* set normals to their previous winding */
		bmesh_rationalize_normals(bm, 1);
		bmesh_set_mdisps_space(bm, MULTIRES_SPACE_ABSOLUTE, MULTIRES_SPACE_TANGENT);
	}
	else if (flag & BMOP_RATIONALIZE_NORMALS) {
		bmesh_rationalize_normals(bm, 1);
	}
#else
	if (flag & BMOP_RATIONALIZE_NORMALS) {
		bmesh_rationalize_normals(bm, 1);
	}
#endif

	bm->opflag = 0;

	/* compute normals, clear temp flags and flush selections */
	BM_Compute_Normals(bm);
	BM_SelectMode_Flush(bm);
}

void BM_ElemIndex_Ensure(BMesh *bm, const char hflag)
{
	BMIter iter;
	BMHeader *ele;

#ifdef DEBUG
	BM_ELEM_INDEX_VALIDATE(bm, "Should Never Fail!", __func__);
#endif

	if (hflag & BM_VERT) {
		if (bm->elem_index_dirty & BM_VERT) {
			int index = 0;
			BM_ITER(ele, &iter, bm, BM_VERTS_OF_MESH, NULL) {
				BM_SetIndex(ele, index); /* set_ok */
				index++;
			}
			bm->elem_index_dirty &= ~BM_VERT;
			BLI_assert(index == bm->totvert);
		}
		else {
			// printf("%s: skipping vert index calc!\n", __func__);
		}
	}

	if (hflag & BM_EDGE) {
		if (bm->elem_index_dirty & BM_EDGE) {
			int index = 0;
			BM_ITER(ele, &iter, bm, BM_EDGES_OF_MESH, NULL) {
				BM_SetIndex(ele, index); /* set_ok */
				index++;
			}
			bm->elem_index_dirty &= ~BM_EDGE;
			BLI_assert(index == bm->totedge);
		}
		else {
			// printf("%s: skipping edge index calc!\n", __func__);
		}
	}

	if (hflag & BM_FACE) {
		if (bm->elem_index_dirty & BM_FACE) {
			int index = 0;
			BM_ITER(ele, &iter, bm, BM_FACES_OF_MESH, NULL) {
				BM_SetIndex(ele, index); /* set_ok */
				index++;
			}
			bm->elem_index_dirty &= ~BM_FACE;
			BLI_assert(index == bm->totface);
		}
		else {
			// printf("%s: skipping face index calc!\n", __func__);
		}
	}
}


/* array checking/setting macros */
/* currently vert/edge/loop/face index data is being abused, but we should
 * eventually be able to rely on it being valid. To this end, there are macros
 * that validate them (so blender doesnt crash), but also print errors so we can
 * fix the offending parts of the code, this way after some months we can
 * confine this code for debug mode.
 *
 *
 */

void BM_ElemIndex_Validate(BMesh *bm, const char *location, const char *func, const char *msg_a, const char *msg_b)
{
	const char iter_types[3] = {BM_VERTS_OF_MESH,
	                            BM_EDGES_OF_MESH,
	                            BM_FACES_OF_MESH};

	const char flag_types[3] = {BM_VERT, BM_EDGE, BM_FACE};
	const char *type_names[3] = {"vert", "edge", "face"};

	BMIter iter;
	BMHeader *ele;
	int i;
	int is_any_error = 0;

	for (i = 0; i < 3; i++) {
		const int is_dirty = (flag_types[i] & bm->elem_index_dirty);
		int index = 0;
		int is_error = FALSE;
		int err_val = 0;
		int err_idx = 0;

		BM_ITER(ele, &iter, bm, iter_types[i], NULL) {
			if (!is_dirty) {
				if (BM_GetIndex(ele) != index) {
					err_val = BM_GetIndex(ele);
					err_idx = index;
					is_error = TRUE;
				}
			}

			BM_SetIndex(ele, index); /* set_ok */
			index++;
		}

		if ((is_error == TRUE) && (is_dirty == FALSE)) {
			is_any_error = TRUE;
			fprintf(stderr,
			        "Invalid Index: at %s, %s, %s[%d] invalid index %d, '%s', '%s'\n",
			        location, func, type_names[i], err_idx, err_val, msg_a, msg_b);
		}
		else if ((is_error == FALSE) && (is_dirty == TRUE)) {

#if 0		/* mostly annoying */

			/* dirty may have been incorrectly set */
			fprintf(stderr,
			        "Invalid Dirty: at %s, %s (%s), dirty flag was set but all index values are correct, '%s', '%s'\n",
			        location, func, type_names[i], msg_a, msg_b);
#endif
		}
	}

#if 0 /* mostly annoying, even in debug mode */
#ifdef DEBUG
	if (is_any_error == 0) {
		fprintf(stderr,
		        "Valid Index Success: at %s, %s, '%s', '%s'\n",
		        location, func, msg_a, msg_b);
	}
#endif
#endif
	(void) is_any_error; /* shut up the compiler */

}

BMVert *BM_Vert_AtIndex(BMesh *bm, const int index)
{
	return BLI_mempool_findelem(bm->vpool, index);
}

BMEdge *BM_Edge_AtIndex(BMesh *bm, const int index)
{
	return BLI_mempool_findelem(bm->epool, index);
}

BMFace *BM_Face_AtIndex(BMesh *bm, const int index)
{
	return BLI_mempool_findelem(bm->fpool, index);
}
