/**
 * BME_mesh.c    jan 2007
 *
 *	BM mesh level functions.
 *
 * $Id: BME_eulers.c,v 1.00 2007/01/17 17:42:01 Briggs Exp $
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 * about this.	
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2007 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Geoffrey Bantle.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"
#include "DNA_object_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_mesh_types.h"

#include "BLI_blenlib.h"
#include "BLI_math.h"
#include "BLI_utildefines.h"
#include "BLI_cellalloc.h"

#include "BKE_utildefines.h"
#include "BKE_cdderivedmesh.h"
#include "BKE_tessmesh.h"
#include "BKE_customdata.h"
#include "BKE_DerivedMesh.h"
#include "BKE_multires.h"

#include "bmesh.h"
#include "bmesh_private.h"

void BME_error(void);

/*bmesh_error stub*/
void bmesh_error(void)
{
	printf("BM modelling error!");
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
	/*allocate the structure*/
	BMesh *bm = MEM_callocN(sizeof(BMesh),"BM");
	int vsize, esize, lsize, fsize, lstsize;

	vsize = sizeof(BMVert);
	esize = sizeof(BMEdge);
	lsize = sizeof(BMLoop);
	fsize = sizeof(BMFace);
	lstsize = sizeof(BMLoopList);

	bm->ob = ob;
	
/*allocate the memory pools for the mesh elements*/
	bm->vpool = BLI_mempool_create(vsize, allocsize[0], allocsize[0], 0, 1);
	bm->epool = BLI_mempool_create(esize, allocsize[1], allocsize[1], 0, 1);
	bm->lpool = BLI_mempool_create(lsize, allocsize[2], allocsize[2], 0, 0);
	bm->looplistpool = BLI_mempool_create(lstsize, allocsize[3], allocsize[3], 0, 0);
	bm->fpool = BLI_mempool_create(fsize, allocsize[3], allocsize[3], 0, 1);

	/*allocate one flag pool that we dont get rid of.*/
	bm->toolflagpool = BLI_mempool_create(sizeof(BMFlagLayer), 512, 512, 0, 0);
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
	
	for(v = BMIter_New(&verts, bm, BM_VERTS_OF_MESH, bm ); v; v = BMIter_Step(&verts)) CustomData_bmesh_free_block( &(bm->vdata), &(v->head.data) );
	for(e = BMIter_New(&edges, bm, BM_EDGES_OF_MESH, bm ); e; e = BMIter_Step(&edges)) CustomData_bmesh_free_block( &(bm->edata), &(e->head.data) );
	for(f = BMIter_New(&faces, bm, BM_FACES_OF_MESH, bm ); f; f = BMIter_Step(&faces)){
		CustomData_bmesh_free_block( &(bm->pdata), &(f->head.data) );
		for(l = BMIter_New(&loops, bm, BM_LOOPS_OF_FACE, f ); l; l = BMIter_Step(&loops)) CustomData_bmesh_free_block( &(bm->ldata), &(l->head.data) );
	}

	/*Free custom data pools, This should probably go in CustomData_free?*/
	if(bm->vdata.totlayer) BLI_mempool_destroy(bm->vdata.pool);
	if(bm->edata.totlayer) BLI_mempool_destroy(bm->edata.pool);
	if(bm->ldata.totlayer) BLI_mempool_destroy(bm->ldata.pool);
	if(bm->pdata.totlayer) BLI_mempool_destroy(bm->pdata.pool);

 	/*free custom data*/
	CustomData_free(&bm->vdata,0);
	CustomData_free(&bm->edata,0);
	CustomData_free(&bm->ldata,0);
	CustomData_free(&bm->pdata,0);

	/*destroy element pools*/
	BLI_mempool_destroy(bm->vpool);
	BLI_mempool_destroy(bm->epool);
	BLI_mempool_destroy(bm->lpool);
	BLI_mempool_destroy(bm->fpool);

	/*destroy flag pool*/
	BLI_mempool_destroy(bm->toolflagpool);
	BLI_mempool_destroy(bm->looplistpool);

	BLI_freelistN(&bm->selected);

	BMO_ClearStack(bm);
}

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
	BMIter verts;
	BMIter faces;
	BMIter loops;
	unsigned int maxlength = 0;
	float (*projectverts)[3];
	
	/*first, find out the largest face in mesh*/
	BM_ITER(f, &faces, bm, BM_FACES_OF_MESH, NULL) {
		if (BM_TestHFlag(f, BM_HIDDEN))
			continue;

		if(f->len > maxlength) maxlength = f->len;
	}
	
	/*make sure we actually have something to do*/
	if(maxlength < 3) return; 
	
	/*allocate projectverts array*/
	projectverts = MEM_callocN(sizeof(float) * maxlength * 3, "BM normal computation array");
	
	/*calculate all face normals*/
	BM_ITER(f, &faces, bm, BM_FACES_OF_MESH, NULL) {
		if (BM_TestHFlag(f, BM_HIDDEN))
			continue;
		if (f->head.flag & BM_NONORMCALC)
			continue;

		bmesh_update_face_normal(bm, f, projectverts);		
	}
	
	/*Zero out vertex normals*/
	BM_ITER(v, &verts, bm, BM_VERTS_OF_MESH, NULL) {
		if (BM_TestHFlag(v, BM_HIDDEN))
			continue;

		v->no[0] = v->no[1] = v->no[2] = 0.0;
	}

	/*add face normals to vertices*/
	BM_ITER(f, &faces, bm, BM_FACES_OF_MESH, NULL) {

		if (BM_TestHFlag(f, BM_HIDDEN))
			continue;

		for(l = BMIter_New(&loops, bm, BM_LOOPS_OF_FACE, f ); l; l = BMIter_Step(&loops)) 
			add_v3_v3v3(l->v->no, l->v->no, f->no);
	}
	
	/*average the vertex normals*/
	BM_ITER(v, &verts, bm, BM_VERTS_OF_MESH, NULL) {
		if (BM_TestHFlag(v, BM_HIDDEN))
			continue;

		if (normalize_v3(v->no) == 0.0f) {
			copy_v3_v3(v->no, v->co);
			normalize_v3(v->no);
		}
	}
	
	MEM_freeN(projectverts);
}

/*
 This function ensures correct normals for the mesh, but
 sets the flag BM_FLIPPED in flipped faces, to allow restoration
 of original normals.
 
 if undo is 0: calculate right normals
 if undo is 1: restore original normals
*/
//keep in sycn with utils.c!
#define FACE_FLIP	8
static void bmesh_rationalize_normals(BMesh *bm, int undo) {
	BMOperator bmop;
	BMFace *f;
	BMIter iter;
	
	if (undo) {
		BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
			if (BM_TestHFlag(f, BM_FLIPPED)) {
				BM_flip_normal(bm, f);
			}
			BM_ClearHFlag(f, BM_FLIPPED);
		}
		
		return;
	}
	
	BMO_InitOpf(bm, &bmop, "righthandfaces faces=%af doflip=%d", 0);
	
	BMO_push(bm, &bmop);
	bmesh_righthandfaces_exec(bm, &bmop);
	
	BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
		if (BMO_TestFlag(bm, f, FACE_FLIP))
			BM_SetHFlag(f, BM_FLIPPED);
		else BM_ClearHFlag(f, BM_FLIPPED);
	}

	BMO_pop(bm);
	BMO_Finish_Op(bm, &bmop);
}

static void bmesh_set_mdisps_space(BMesh *bm, int from, int to)
{
	/*switch multires data out of tangent space*/
	if (CustomData_has_layer(&bm->ldata, CD_MDISPS)) {
		Object *ob = bm->ob;
		BMEditMesh *em = BMEdit_Create(bm);
		DerivedMesh *dm = CDDM_from_BMEditMesh(em, NULL, 1);
		MDisps *mdisps;
		BMFace *f;
		BMIter iter;
		// int i= 0; // UNUSED
		
		multires_set_space(dm, ob, from, to);
		
		mdisps = CustomData_get_layer(&dm->loopData, CD_MDISPS);
		
		BM_ITER(f, &iter, bm, BM_FACES_OF_MESH, NULL) {
			BMLoop *l;
			BMIter liter;
			BM_ITER(l, &liter, bm, BM_LOOPS_OF_FACE, f) {
				MDisps *lmd = CustomData_bmesh_get(&bm->ldata, l->head.data, CD_MDISPS);
				
				if (!lmd->disps) {
					printf("eck!\n");
				}
				
				if (lmd->disps && lmd->totdisp == mdisps->totdisp) {
					memcpy(lmd->disps, mdisps->disps, sizeof(float)*3*lmd->totdisp);
				} else if (mdisps->disps) {
					if (lmd->disps)
						BLI_cellalloc_free(lmd->disps);
					
					lmd->disps = BLI_cellalloc_dupalloc(mdisps->disps);
					lmd->totdisp = mdisps->totdisp;
				}
				
				mdisps++;
				// i += 1;
			}
		}
		
		dm->needsFree = 1;
		dm->release(dm);
		
		/*setting this to NULL prevents BMEdit_Free from freeing it*/
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
 *
 *  Returns -
 *  Nothing
 *
*/
void bmesh_begin_edit(BMesh *bm, int flag) {
	bm->opflag = flag;
	
	/*switch multires data out of tangent space*/
	if ((flag & BMOP_UNTAN_MULTIRES) && CustomData_has_layer(&bm->ldata, CD_MDISPS)) {
		bmesh_set_mdisps_space(bm, MULTIRES_SPACE_TANGENT, MULTIRES_SPACE_ABSOLUTE);

		/*ensure correct normals, if possible*/
		bmesh_rationalize_normals(bm, 0);
		BM_Compute_Normals(bm);
	} else if (flag & BMOP_RATIONALIZE_NORMALS) {
		bmesh_rationalize_normals(bm, 0);
	}
}

void bmesh_end_edit(BMesh *bm, int flag){
	/*switch multires data into tangent space*/
	if ((flag & BMOP_UNTAN_MULTIRES) && CustomData_has_layer(&bm->ldata, CD_MDISPS)) {
		/*set normals to their previous winding*/
		bmesh_rationalize_normals(bm, 1);
		bmesh_set_mdisps_space(bm, MULTIRES_SPACE_ABSOLUTE, MULTIRES_SPACE_TANGENT);
	} else if (flag & BMOP_RATIONALIZE_NORMALS) {
		bmesh_rationalize_normals(bm, 1);
	}

	bm->opflag = 0;

	/*compute normals, clear temp flags and flush selections*/
	BM_Compute_Normals(bm);
	BM_SelectMode_Flush(bm);
}
