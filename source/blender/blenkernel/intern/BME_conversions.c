/**
 * BME_mesh.c    jan 2007
 *
 *	BMesh mesh level functions.
 *
 * $Id: BME_eulers.c,v 1.00 2007/01/17 17:42:01 Briggs Exp $
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
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
 * Contributor(s): Geoffrey Bantle, Levi Schooley.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include "MEM_guardedalloc.h"

#include "DNA_listBase.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"

#include "BKE_utildefines.h"
#include "BKE_mesh.h"
#include "BKE_bmesh.h"
#include "BKE_global.h"
#include "BKE_DerivedMesh.h"
#include "BKE_cdderivedmesh.h"

#include "BLI_blenlib.h"
#include "BLI_editVert.h"
#include "BLI_edgehash.h"
#include "BIF_editmesh.h"
#include "editmesh.h"
#include "bmesh_private.h"

#include "BSE_edit.h"

BME_Mesh *BME_editmesh_to_bmesh(EditMesh *em, BME_Mesh *bm) {
	BME_Vert *v1, *v2;
	BME_Edge *e, *edar[4];
	BME_Poly *f;

	EditVert *eve;
	EditEdge *eed;
	EditFace *efa;

	int len;

	BME_model_begin(bm);
	/*custom data*/
	
	/*add verts*/
	CustomData_copy(&em->vdata, &bm->vdata, CD_MASK_EDITMESH, CD_CALLOC, 0);
	eve= em->verts.first;
	while(eve) {
		v1 = BME_MV(bm,eve->co);
		VECCOPY(v1->no,eve->no);
		v1->flag = eve->f;
		v1->h = eve->h;
		v1->bweight = eve->bweight;

		/* link the verts for edge and face construction;
		 * kind of a dangerous thing - remember to cast back to BME_Vert before using! */
		eve->tmp.v = (EditVert*)v1;

		CustomData_em_copy_data(&em->vdata, &bm->vdata, eve->data, &v1->data);
		
		eve = eve->next;
	}
	
	/*add edges*/
	CustomData_copy(&em->edata, &bm->edata, CD_MASK_EDITMESH, CD_CALLOC, 0);
	eed= em->edges.first;
	while(eed) {
		v1 = (BME_Vert*)eed->v1->tmp.v;
		v2 = (BME_Vert*)eed->v2->tmp.v;
		e = BME_ME(bm, v1, v2);
		e->crease = eed->crease;
		e->bweight = eed->bweight;
		e->flag = eed->f & SELECT;
		if(eed->sharp) e->flag |= ME_SHARP;
		if(eed->seam) e->flag |= ME_SEAM;
		if(eed->h & EM_FGON) e->flag |= ME_FGON;
		if(eed->h & 1) e->flag |= ME_HIDE;
		CustomData_em_copy_data(&em->edata, &bm->edata, eed->data, &e->data);

		/* link the edges for face construction;
		 * kind of a dangerous thing - remember to cast back to BME_Edge before using! */
		eed->tmp.e = (EditEdge*)e;
		eed = eed->next;
	}

	/*add faces.*/
	CustomData_copy(&em->fdata, &bm->pdata, CD_MASK_EDITMESH, CD_CALLOC, 0);
	efa= em->faces.first;
	while(efa) {
		if(efa->v4) len = 4;
		else len = 3;
		
		edar[0] = (BME_Edge*)efa->e1->tmp.e;
		edar[1] = (BME_Edge*)efa->e2->tmp.e;
		edar[2] = (BME_Edge*)efa->e3->tmp.e;
		if(len == 4){
			edar[3] = (BME_Edge*)efa->e4->tmp.e;
		}
		
		/*find v1 and v2*/
		v1 = (BME_Vert*)efa->v1->tmp.v;
		v2 = (BME_Vert*)efa->v2->tmp.v;
		
		f = BME_MF(bm,v1,v2,edar,len);
		f->mat_nr = efa->mat_nr;
		f->flag = efa->flag;
		if(efa->h) {
			f->flag |= ME_HIDE;
			f->flag &= ~ME_FACE_SEL;
		}
		else {
			if(efa->f & 1) f->flag |= ME_FACE_SEL;
			else f->flag &= ~ME_FACE_SEL;
		}
		CustomData_em_copy_data(&em->fdata, &bm->pdata, efa->data, &f->data);
		
		efa = efa->next;
	}
	BME_model_end(bm);
	return bm;
}

/* adds the geometry in the bmesh to G.editMesh (does not free G.editMesh)
 * if td != NULL, the transdata will be mapped to the EditVert's co */
EditMesh *BME_bmesh_to_editmesh(BME_Mesh *bm, BME_TransData_Head *td) {
	BME_Vert *v1;
	BME_Edge *e;
	BME_Poly *f;
	
	BME_TransData *vtd;

	EditMesh *em;
	EditVert *eve1, *eve2, *eve3, *eve4, **evlist;
	EditEdge *eed;
	EditFace *efa;

	int totvert, len, i;

	em = G.editMesh;

	if (em == NULL) return NULL;

	/* convert to EditMesh */
	/* make editverts */
	CustomData_copy(&bm->vdata, &em->vdata, CD_MASK_EDITMESH, CD_CALLOC, 0);
	totvert = BLI_countlist(&(bm->verts));
	evlist= (EditVert **)MEM_mallocN(totvert*sizeof(void *),"evlist");
	for (i=0,v1=bm->verts.first;v1;v1=v1->next,i++) {
		v1->tflag1 = i;
		eve1 = addvertlist(v1->co,NULL);
		if (td && (vtd = BME_get_transdata(td,v1))) {
			vtd->loc = eve1->co;
		}
		eve1->keyindex = i;
		evlist[i]= eve1;
		eve1->f = (unsigned char)v1->flag;
		eve1->h = (unsigned char)v1->h;
		eve1->bweight = v1->bweight;
		CustomData_em_copy_data(&bm->vdata, &em->vdata, v1->data, &eve1->data);
	}
	
	/* make edges */
	CustomData_copy(&bm->edata, &em->edata, CD_MASK_EDITMESH, CD_CALLOC, 0);
	for (e=bm->edges.first;e;e=e->next) {
		eed= addedgelist(evlist[e->v1->tflag1], evlist[e->v2->tflag1], NULL);
		eed->crease = e->crease;
		eed->bweight = e->bweight;
		if(e->flag & ME_SEAM) eed->seam = 1;
		if(e->flag & ME_SHARP) eed->sharp = 1;
		if(e->flag & SELECT) eed->f |= SELECT;
		if(e->flag & ME_FGON) eed->h= EM_FGON; // 2 different defines!
		if(e->flag & ME_HIDE) eed->h |= 1;
		if(G.scene->selectmode==SCE_SELECT_EDGE) 
			EM_select_edge(eed, eed->f & SELECT);
		CustomData_em_copy_data(&bm->edata, &em->edata, e->data, &eed->data);
	}

	/* make faces */
	CustomData_copy(&bm->pdata, &em->fdata, CD_MASK_EDITMESH, CD_CALLOC, 0);
	for (f=bm->polys.first;f;f=f->next) {
		len = BME_cycle_length(f->loopbase);
		if (len==3 || len==4) {
			eve1= evlist[f->loopbase->v->tflag1];
			eve2= evlist[f->loopbase->next->v->tflag1];
			eve3= evlist[f->loopbase->next->next->v->tflag1];
			if (len == 4) {
				eve4= evlist[f->loopbase->prev->v->tflag1];
			}
			else {
				eve4= NULL;
			}

			efa = addfacelist(eve1, eve2, eve3, eve4, NULL, NULL);
			CustomData_em_copy_data(&bm->pdata, &em->fdata, f->data, &efa->data);
			efa->mat_nr = (unsigned char)f->mat_nr;
			efa->flag= f->flag & ~ME_HIDE;
			if(f->flag & ME_FACE_SEL) {
				efa->f |= SELECT;
			}
			if(f->flag & ME_HIDE) efa->h= 1;
			if((G.f & G_FACESELECT) && (efa->f & SELECT))
				EM_select_face(efa, 1); /* flush down */
		}
	}

	MEM_freeN(evlist);

	countall();

	return em;
}

/* Adds the geometry found in dm to bm
 * NOTE: it does not allocate a new BME_Mesh!
 */
BME_Mesh *BME_derivedmesh_to_bmesh(DerivedMesh *dm, BME_Mesh *bm)
{
	MVert *mvert, *mv;
	MEdge *medge, *me;
	MFace *mface, *mf;
	int totface,totedge,totvert,i,len;

	BME_Vert *v1=NULL,*v2=NULL, **vert_array;
	BME_Edge *e=NULL;
	BME_Poly *f=NULL;
	
	EdgeHash *edge_hash = BLI_edgehash_new();
	
	totvert = dm->getNumVerts(dm);
	totedge = dm->getNumEdges(dm);
	totface = dm->getNumFaces(dm);
	mvert = dm->getVertArray(dm);
	medge = dm->getEdgeArray(dm);
	mface = dm->getFaceArray(dm);

	vert_array = MEM_mallocN(sizeof(*vert_array)*totvert,"BME_derivedmesh_to_bmesh BME_Vert* array");

	/*custom data*/
	/* NOTE: I haven't tested whether or not custom data is being copied correctly */
	CustomData_copy(&dm->vertData, &bm->vdata, CD_MASK_DERIVEDMESH,
	                CD_CALLOC, 0);
	CustomData_copy(&dm->edgeData, &bm->edata, CD_MASK_DERIVEDMESH,
	                CD_CALLOC, 0);
	CustomData_copy(&dm->faceData, &bm->pdata, CD_MASK_DERIVEDMESH,
	                CD_CALLOC, 0);
	/*add verts*/
	for(i=0,mv = mvert; i < totvert;i++,mv++){
		v1 = BME_MV(bm,mv->co);
		vert_array[i] = v1;
		v1->flag = mv->flag;
		v1->bweight = mv->bweight/255.0f;
		CustomData_to_em_block(&dm->vertData, &bm->vdata, i, &v1->data);
	}
	/*add edges*/
	for(i=0,me = medge; i < totedge;i++,me++){
		v1 = vert_array[me->v1];
		v2 = vert_array[me->v2];
		e = BME_ME(bm, v1, v2);
		e->crease = me->crease/255.0f;
		e->bweight = me->bweight/255.0f;
		e->flag = (unsigned char)me->flag;
		BLI_edgehash_insert(edge_hash,me->v1,me->v2,e);
		CustomData_to_em_block(&dm->edgeData, &bm->edata, i, &e->data);
	}
	/*add faces.*/
	for(i=0,mf = mface; i < totface;i++,mf++){
		BME_Edge *edar[4];
		if(mf->v4) len = 4;
		else len = 3;
		
		edar[0] = BLI_edgehash_lookup(edge_hash,mf->v1,mf->v2);
		edar[1] = BLI_edgehash_lookup(edge_hash,mf->v2,mf->v3);
		if(len == 4){
			edar[2] = BLI_edgehash_lookup(edge_hash,mf->v3,mf->v4);
			edar[3] = BLI_edgehash_lookup(edge_hash,mf->v4,mf->v1);
		}
		else
			edar[2] = BLI_edgehash_lookup(edge_hash,mf->v3,mf->v1);
		
		/*find v1 and v2*/
		v1 = vert_array[mf->v1];
		v2 = vert_array[mf->v2];
		
		f = BME_MF(bm,v1,v2,edar,len);
		f->mat_nr = mf->mat_nr;
		f->flag = mf->flag;
		CustomData_to_em_block(&dm->faceData, &bm->pdata, i, &f->data);
	}
	
	BLI_edgehash_free(edge_hash, NULL);
	MEM_freeN(vert_array);
	return bm;
}

DerivedMesh *BME_bmesh_to_derivedmesh(BME_Mesh *bm, DerivedMesh *dm)
{
	MFace *mface, *mf;
	MEdge *medge, *me;
	MVert *mvert, *mv;
	int totface,totedge,totvert,i,bmeshok,len;

	BME_Vert *v1=NULL;
	BME_Edge *e=NULL;
	BME_Poly *f=NULL;
	
	DerivedMesh *result;
	
	totvert = BLI_countlist(&(bm->verts));
	totedge = BLI_countlist(&(bm->edges));
	/*count quads and tris*/
	totface = 0;
	bmeshok = 1;
	for(f=bm->polys.first;f;f=f->next){
		len = BME_cycle_length(f->loopbase);
		if(len == 3 || len == 4) totface++;
	}
	
	/*convert back to mesh*/
	result = CDDM_from_template(dm,totvert,totedge,totface);
	/*custom data*/
	/* NOTE: I haven't tested whether or not custom data is being copied correctly */
	CustomData_merge(&bm->vdata, &result->vertData, CD_MASK_DERIVEDMESH,
	                CD_CALLOC, totvert);
	CustomData_merge(&bm->edata, &result->edgeData, CD_MASK_DERIVEDMESH,
	                CD_CALLOC, totedge);
	CustomData_merge(&bm->pdata, &result->faceData, CD_MASK_DERIVEDMESH,
	                CD_CALLOC, totface);
	/*Make Verts*/
	mvert = CDDM_get_verts(result);
	for(i=0,v1=bm->verts.first,mv=mvert;v1;v1=v1->next,i++,mv++){
		v1->tflag1 = i;
		VECCOPY(mv->co,v1->co);
		mv->flag = (unsigned char)v1->flag;
		mv->bweight = (char)(255.0*v1->bweight);
		CustomData_from_em_block(&bm->vdata, &result->vertData, v1->data, i);
	}
	medge = CDDM_get_edges(result);
	for(i=0,e=bm->edges.first,me=medge;e;e=e->next,me++,i++){
		if(e->v1->tflag1 < e->v2->tflag1){
			me->v1 = e->v1->tflag1;
			me->v2 = e->v2->tflag1;
		}
		else{
			me->v1 = e->v2->tflag1;
			me->v2 = e->v1->tflag1;
		}
		me->crease = (char)(255.0*e->crease);
		me->bweight = (char)(255.0*e->bweight);
		me->flag = e->flag;
		CustomData_from_em_block(&bm->edata, &result->edgeData, e->data, i);
	}
	if(totface){
		mface = CDDM_get_faces(result);
		/*make faces*/
		for(i=0,f=bm->polys.first;f;f=f->next,i++){
			mf = &mface[i];
			len = BME_cycle_length(f->loopbase);
			if(len==3 || len==4){
				mf->v1 = f->loopbase->v->tflag1;
				mf->v2 = f->loopbase->next->v->tflag1;
				mf->v3 = f->loopbase->next->next->v->tflag1;
				if(len == 4){
					mf->v4 = f->loopbase->prev->v->tflag1;
				}
				/* test and rotate indexes if necessary so that verts 3 and 4 aren't index 0 */
				if(mf->v3 == 0 || (len == 4 && mf->v4 == 0)){
					test_index_face(mf, NULL, i, len);
				}
			}
			mf->mat_nr = (unsigned char)f->mat_nr;
			mf->flag = (unsigned char)f->flag;
			CustomData_from_em_block(&bm->pdata, &result->faceData, f->data, i);
		}
	}

	return result;
}
