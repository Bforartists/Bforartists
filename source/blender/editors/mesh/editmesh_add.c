/**
 * $Id: 
 *
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2004 by Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 */


#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"

#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_space_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"
#include "DNA_windowmanager_types.h"

#include "RNA_types.h"
#include "RNA_define.h"
#include "RNA_access.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "BKE_context.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_mesh.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"
#include "BKE_report.h"
#include "BKE_tessmesh.h"

#include "WM_api.h"
#include "WM_types.h"

#include "ED_mesh.h"
#include "ED_retopo.h"
#include "ED_screen.h"
#include "ED_transform.h"
#include "ED_util.h"
#include "ED_view3d.h"

#include "bmesh.h"

#include "mesh_intern.h"

/* bpymenu removed XXX */

/* XXX */
#define add_numbut(a, b, c, d, e, f, g) {}
/* XXX */

static float icovert[12][3] = {
	{0.0f,0.0f,-200.0f}, 
	{144.72f, -105.144f,-89.443f},
	{-55.277f, -170.128,-89.443f}, 
	{-178.885f,0.0f,-89.443f},
	{-55.277f,170.128f,-89.443f}, 
	{144.72f,105.144f,-89.443f},
	{55.277f,-170.128f,89.443f},
	{-144.72f,-105.144f,89.443f},
	{-144.72f,105.144f,89.443f},
	{55.277f,170.128f,89.443f},
	{178.885f,0.0f,89.443f},
	{0.0f,0.0f,200.0f}
};
static short icoface[20][3] = {
	{1,0,2},
	{1,0,5},
	{2,0,3},
	{3,0,4},
	{4,0,5},
	{1,5,10},
	{2,1,6},
	{3,2,7},
	{4,3,8},
	{5,4,9},
	{10,1,6},
	{6,2,7},
	{7,3,8},
	{8,4,9},
	{9,5,10},
	{6,10,11},
	{7,6,11},
	{8,7,11},
	{9,8,11},
	{10,9,11}
};


/* ********************** */

/* selected faces get hidden edges */
int make_fgon(EditMesh *em, wmOperator *op, int make)
{
	EditFace *efa;
	EditEdge *eed;
	EditVert *eve;
	float *nor=NULL;	// reference
	int done=0;
	
	if(make==0) {
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->f & SELECT) {
				efa->fgonf= 0;
				efa->e1->h &= ~EM_FGON;
				efa->e2->h &= ~EM_FGON;
				efa->e3->h &= ~EM_FGON;
				if(efa->e4) efa->e4->h &= ~EM_FGON;
				done= 1;
			}
		}
		EM_fgon_flags(em);	// redo flags and indices for fgons
		
		return done;
	}

	/* tagging edges. rule is:
	   - edge used by exactly 2 selected faces
	   - no vertices allowed with only tagged edges (return)
	   - face normals are allowed to difffer
	 
	*/
	for(eed= em->edges.first; eed; eed= eed->next) {
		eed->f1= 0;	// amount of selected
		eed->f2= 0; // amount of unselected
	}
	
	for(efa= em->faces.first; efa; efa= efa->next) {
		if(efa->f & SELECT) {
			if(nor==NULL) nor= efa->n;
			if(efa->e1->f1 < 3) efa->e1->f1++;
			if(efa->e2->f1 < 3) efa->e2->f1++;
			if(efa->e3->f1 < 3) efa->e3->f1++;
			if(efa->e4 && efa->e4->f1 < 3) efa->e4->f1++;
		}
		else {
			if(efa->e1->f2 < 3) efa->e1->f2++;
			if(efa->e2->f2 < 3) efa->e2->f2++;
			if(efa->e3->f2 < 3) efa->e3->f2++;
			if(efa->e4 && efa->e4->f2 < 3) efa->e4->f2++;
		}
	}
	// now eed->f1 becomes tagged edge
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->f1==2 && eed->f2==0) eed->f1= 1;
		else eed->f1= 0;
	}
	
	// no vertices allowed with only tagged edges
	for(eve= em->verts.first; eve; eve= eve->next) eve->f1= 0;
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->f1) {
			eed->v1->f1 |= 1;
			eed->v2->f1 |= 1;
		}
		else {
			eed->v1->f1 |= 2;
			eed->v2->f1 |= 2;
		}
	}
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->f1==1) break;
	}
	if(eve) {
		BKE_report(op->reports, RPT_ERROR, "Cannot make a polygon with interior vertices");
		return 0;
	}
	
	// check for faces
	if(nor==NULL) {
		BKE_report(op->reports, RPT_ERROR, "No faces were selected to make FGon");
		return 0;
	}

	// and there we go
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->f1) {
			eed->h |= EM_FGON;
			done= 1;
		}
	}
	
	if(done)
		EM_fgon_flags(em);	// redo flags and indices for fgons
	return done;
}

static int make_fgon_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh(((Mesh *)obedit->data));

	if( make_fgon(em, op, 1) ) {
		DAG_object_flush_update(CTX_data_scene(C), obedit, OB_RECALC_DATA);	
	
		WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);

		BKE_mesh_end_editmesh(obedit->data, em);
		return OPERATOR_FINISHED;
	}

	BKE_mesh_end_editmesh(obedit->data, em);
	return OPERATOR_CANCELLED;
}

void MESH_OT_fgon_make(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Make F-gon";
	ot->idname= "MESH_OT_fgon_make";
	
	/* api callbacks */
	ot->exec= make_fgon_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int clear_fgon_exec(bContext *C, wmOperator *op)
{
	Object *obedit= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh(((Mesh *)obedit->data));
	
	if( make_fgon(em, op, 0) ) {
		DAG_object_flush_update(CTX_data_scene(C), obedit, OB_RECALC_DATA);	
		
		WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
		
		BKE_mesh_end_editmesh(obedit->data, em);
		return OPERATOR_FINISHED;
	}

	BKE_mesh_end_editmesh(obedit->data, em);
	return OPERATOR_CANCELLED;
}

void MESH_OT_fgon_clear(struct wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Clear F-gon";
	ot->idname= "MESH_OT_fgon_clear";
	
	/* api callbacks */
	ot->exec= clear_fgon_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

/* precondition; 4 vertices selected, check for 4 edges and create face */
static EditFace *addface_from_edges(EditMesh *em)
{
	EditEdge *eed, *eedar[4]={NULL, NULL, NULL, NULL};
	EditVert *v1=NULL, *v2=NULL, *v3=NULL, *v4=NULL;
	int a;
	
	/* find the 4 edges */
	for(eed= em->edges.first; eed; eed= eed->next) {
		if( (eed->f & SELECT) || (eed->v1->f & eed->v2->f & SELECT) ) {
			if(eedar[0]==NULL) eedar[0]= eed;
			else if(eedar[1]==NULL) eedar[1]= eed;
			else if(eedar[2]==NULL) eedar[2]= eed;
			else eedar[3]= eed;
			
		}
	}
	
	
	if(eedar[3]) {
		/* first 2 points */
		v1= eedar[0]->v1;
		v2= eedar[0]->v2;
		
		/* find the 2 edges connected to first edge */
		for(a=1; a<4; a++) {
			if( eedar[a]->v1 == v2) v3= eedar[a]->v2;
			else if(eedar[a]->v2 == v2) v3= eedar[a]->v1;
			else if( eedar[a]->v1 == v1) v4= eedar[a]->v2;
			else if(eedar[a]->v2 == v1) v4= eedar[a]->v1;
		}
		
		/* verify if last edge exists */
		if(v3 && v4) {
			for(a=1; a<4; a++) {
				if( eedar[a]->v1==v3 && eedar[a]->v2==v4) break;
				if( eedar[a]->v2==v3 && eedar[a]->v1==v4) break;
			}
			if(a!=4) {
				return addfacelist(em, v1, v2, v3, v4, NULL, NULL);
			}
		}
	}
	return NULL;
}

/* ******************************* */

/* this also allows to prevent triangles being made in quads */
static int compareface_overlaps(EditFace *vl1, EditFace *vl2)
{
	EditVert *v1, *v2, *v3, *v4;
	int equal= 0;
	
	v1= vl2->v1;
	v2= vl2->v2;
	v3= vl2->v3;
	v4= vl2->v4;
	
	if(vl1==vl2) return 0;
	
	if(v4==NULL && vl1->v4==NULL) {
		if(vl1->v1==v1 || vl1->v2==v1 || vl1->v3==v1) equal++;
		if(vl1->v1==v2 || vl1->v2==v2 || vl1->v3==v2) equal++;
		if(vl1->v1==v3 || vl1->v2==v3 || vl1->v3==v3) equal++;
	}
	else {
		if(vl1->v1==v1 || vl1->v2==v1 || vl1->v3==v1 || vl1->v4==v1) equal++;
		if(vl1->v1==v2 || vl1->v2==v2 || vl1->v3==v2 || vl1->v4==v2) equal++;
		if(vl1->v1==v3 || vl1->v2==v3 || vl1->v3==v3 || vl1->v4==v3) equal++;
		if(vl1->v1==v4 || vl1->v2==v4 || vl1->v3==v4 || vl1->v4==v4) equal++;
	}

	if(v4 && vl1->v4) {
		if(equal==4) return 1;
	}
	else 
		if(equal>=3) return 1;
	
	return 0;
}

/* checks for existance, and for tria overlapping inside quad */
static EditFace *exist_face_overlaps(EditMesh *em, EditVert *v1, EditVert *v2, EditVert *v3, EditVert *v4)
{
	EditFace *efa, efatest;
	
	efatest.v1= v1;
	efatest.v2= v2;
	efatest.v3= v3;
	efatest.v4= v4;
	
	efa= em->faces.first;
	while(efa) {
		if(compareface_overlaps(&efatest, efa)) return efa;
		efa= efa->next;
	}
	return NULL;
}

/* will be new face smooth or solid? depends on smoothness of face neighbours
 * of new face, if function return 1, then new face will be smooth, when functio
 * will return zero, then new face will be solid */
static void fix_new_face(EditMesh *em, EditFace *eface)
{
	struct EditFace *efa;
	struct EditEdge *eed=NULL;
	struct EditVert *v1 = eface->v1, *v2 = eface->v2, *v3 = eface->v3, *v4 = eface->v4;
	struct EditVert *ev1=NULL, *ev2=NULL;
	short smooth=0; /* "total smoothnes" of faces in neighbourhood */
	short coef;	/* "weight" of smoothness */
	short count=0;	/* number of edges with same direction as eface */
	short vi00=0, vi01=0, vi10=0, vi11=0; /* vertex indexes */

	efa = em->faces.first;

	while(efa) {

		if(efa==eface) {
			efa = efa->next;
			continue;
		}

		coef = 0;
		ev1 = ev2 = NULL;
		eed = NULL;

		if(efa->v1==v1 || efa->v2==v1 || efa->v3==v1 || efa->v4==v1) {
			ev1 = v1;
			coef++;
		}
		if(efa->v1==v2 || efa->v2==v2 || efa->v3==v2 || efa->v4==v2) {
			if(ev1) ev2 = v2;
			else ev1 = v2;
			coef++;
		}
		if(efa->v1==v3 || efa->v2==v3 || efa->v3==v3 || efa->v4==v3) {
			if(coef<2) {
				if(ev1) ev2 = v3;
				else ev1 = v3;
			}
			coef++;
		}
		if((v4) && (efa->v1==v4 || efa->v2==v4 || efa->v3==v4 || efa->v4==v4)) {
			if(ev1 && coef<2) ev2 = v4;
			coef++;
		}

		/* "democracy" of smoothness */
		if(efa->flag & ME_SMOOTH)
			smooth += coef;
		else
			smooth -= coef;

		/* try to find edge using vertexes ev1 and ev2 */
		if((ev1) && (ev2) && (ev1!=ev2)) eed = findedgelist(em, ev1, ev2);

		/* has bordering edge of efa same direction as edge of eface ? */
		if(eed) {
			if(eed->v1==v1) vi00 = 1;
			else if(eed->v1==v2) vi00 = 2;
			else if(eed->v1==v3) vi00 = 3;
			else if(v4 && eed->v1==v4) vi00 = 4;

			if(eed->v2==v1) vi01 = 1;
			else if(eed->v2==v2) vi01 = 2;
			else if(eed->v2==v3) vi01 = 3;
			else if(v4 && eed->v2==v4) vi01 = 4;

			if(v4) {
				if(vi01==1 && vi00==4) vi00 = 0;
				if(vi01==4 && vi00==1) vi01 = 0;
			}
			else {
				if(vi01==1 && vi00==3) vi00 = 0;
				if(vi01==3 && vi00==1) vi01 = 0;
			}

			if(eed->v1==efa->v1) vi10 = 1;
			else if(eed->v1==efa->v2) vi10 = 2;
			else if(eed->v1==efa->v3) vi10 = 3;
			else if(efa->v4 && eed->v1==efa->v4) vi10 = 4;

			if(eed->v2==efa->v1) vi11 = 1;
			else if(eed->v2==efa->v2) vi11 = 2;
			else if(eed->v2==efa->v3) vi11 = 3;
			else if(efa->v4 && eed->v2==efa->v4) vi11 = 4;

			if(efa->v4) {
				if(vi11==1 && vi10==4) vi10 = 0;
				if(vi11==4 && vi10==1) vi11 = 0;
			}
			else {
				if(vi11==1 && vi10==3) vi10 = 0;
				if(vi11==3 && vi10==1) vi11 = 0;
			}

			if(((vi00>vi01) && (vi10>vi11)) ||
				((vi00<vi01) && (vi10<vi11)))
				count++;
			else
				count--;
		}

		efa = efa->next;
	}

	/* set up smoothness according voting of face in neighbourhood */
	if(smooth >= 0)
		eface->flag |= ME_SMOOTH;
	else
		eface->flag &= ~ME_SMOOTH;

	/* flip face, when too much "face normals" in neighbourhood is different */
	if(count > 0) {
		flipface(em, eface);
	}
}

/* only adds quads or trias when there's edges already */
void addfaces_from_edgenet(EditMesh *em)
{
	EditVert *eve1, *eve2, *eve3, *eve4;
	
	for(eve1= em->verts.first; eve1; eve1= eve1->next) {
		for(eve2= em->verts.first; (eve1->f & 1) && eve2; eve2= eve2->next) {
			if(findedgelist(em, eve1,eve2)) {
				for(eve3= em->verts.first; (eve2->f & 1) && eve3; eve3= eve3->next) {
					if((eve2!=eve3 && (eve3->f & 1) && findedgelist(em, eve1,eve3))) {
						EditEdge *sh_edge= NULL;
						EditVert *sh_vert= NULL;
						
						sh_edge= findedgelist(em, eve2,eve3);
						
						if(sh_edge) { /* Add a triangle */
							if(!exist_face_overlaps(em, eve1,eve2,eve3,NULL))
								fix_new_face(em, addfacelist(em, eve1,eve2,eve3,NULL,NULL,NULL));
						}
						else { /* Check for a shared vertex */
							for(eve4= em->verts.first; eve4; eve4= eve4->next) {
								if(eve4!=eve1 && eve4!=eve2 && eve4!=eve3 && (eve4->f & 1) &&
								   !findedgelist(em, eve1,eve4) && findedgelist(em, eve2,eve4) &&
								   findedgelist(em, eve3,eve4)) {
									sh_vert= eve4;
									break;
								}
							}
							
							if(sh_vert) {
								if(sh_vert) {
									if(!exist_face_overlaps(em, eve1,eve2,eve4,eve3))
										fix_new_face(em, addfacelist(em, eve1,eve2,eve4,eve3,NULL,NULL));
								}
							}
						}
					}
				}
			}
		}
	}

	EM_select_flush(em);
	
// XXX	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
}

static void addedgeface_mesh(Mesh *me, BMEditMesh *bem, wmOperator *op)
{
	EditMesh *em;
	EditVert *eve, *neweve[4];
	EditEdge *eed;
	EditFace *efa;
	short amount=0;
	
	/*return if bmesh vert connect does anything.*/
	if (bem->selectmode & SCE_SELECT_VERTEX) {
		BMesh *bm = bem->bm;
		BMOperator bmop;
		int len, ok;
		
		EDBM_InitOpf(bem, &bmop, op, "connectverts verts=%hv", BM_SELECT);
		BMO_Exec_Op(bem->bm, &bmop);

		len = BMO_GetSlot(&bmop, "edgeout")->len;		

		ok = EDBM_FinishOp(bem, &bmop, op, 1);
		if (!ok) return OPERATOR_CANCELLED;

		if (len) return;	
	}

	/*return if bmesh face dissolve finds stuff to
	  dissolve.  this entire tool should be
	  bmeshafied eventually, but until then
	  hacks like this to integrate with it
	  are necassary.*/
	if (bem->selectmode & SCE_SELECT_VERTEX) {
		BMesh *bm = bem->bm;
		BMOperator bmop;
		int len, ok;
		
		EDBM_InitOpf(bem, &bmop, op, "dissolvefaces faces=%hf", BM_SELECT);
		BMO_Exec_Op(bem->bm, &bmop);

		len = BMO_GetSlot(&bmop, "regionout")->len;		
		
		ok = EDBM_FinishOp(bem, &bmop, op, 1);
		if (!ok) return OPERATOR_CANCELLED;

		if (len) return;	
	}

	em = BKE_mesh_get_editmesh(me);

	/* how many selected ? */
	if(em->selectmode & SCE_SELECT_EDGE) {
		/* in edge mode finding selected vertices means flushing down edge codes... */
		/* can't make face with only edge selection info... */
		EM_selectmode_set(em);
	}
	
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->f & SELECT) {
			amount++;
			if(amount>4) break;			
			neweve[amount-1]= eve;
		}
	}

	if(amount==2) {
		eed= addedgelist(em, neweve[0], neweve[1], NULL);
		EM_select_edge(eed, 1);
		
		BKE_mesh_end_editmesh(me, em);
		// XXX		DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);	
		return;
	}
	else if(amount > 4) {
		addfaces_from_edgenet(em);
		BKE_mesh_end_editmesh(me, em);
		return;
	}
	else if(amount<2) {
		BKE_report(op->reports, RPT_ERROR, "More vertices are needed to make an edge/face");
		BKE_mesh_end_editmesh(me, em);
		return;
	}

	efa= NULL; // check later

	if(amount==3) {
		
		if(exist_face_overlaps(em, neweve[0], neweve[1], neweve[2], NULL)==0) {
			efa= addfacelist(em, neweve[0], neweve[1], neweve[2], 0, NULL, NULL);
			EM_select_face(efa, 1);
		}
		else BKE_report(op->reports, RPT_ERROR, "The selected vertices already form a face");
	}
	else if(amount==4) {
		/* this test survives when theres 2 triangles */
		if(exist_face(em, neweve[0], neweve[1], neweve[2], neweve[3])==0) {
			int tria= 0;
			
			/* remove trias if they exist, 4 cases.... */
			if(exist_face(em, neweve[0], neweve[1], neweve[2], NULL)) tria++;
			if(exist_face(em, neweve[0], neweve[1], neweve[3], NULL)) tria++;
			if(exist_face(em, neweve[0], neweve[2], neweve[3], NULL)) tria++;
			if(exist_face(em, neweve[1], neweve[2], neweve[3], NULL)) tria++;
		
			if(tria==2) join_triangles(em);
			else if(exist_face_overlaps(em, neweve[0], neweve[1], neweve[2], neweve[3])==0) {
				 /* If there are 4 Verts, But more selected edges, we need to call addfaces_from_edgenet */
					EditEdge *eedcheck;
					int count;
					count = 0;
					for(eedcheck= em->edges.first; eedcheck; eedcheck= eedcheck->next) {
						if(eedcheck->f & SELECT) {
							count++;
						}
					}	
				
				if(count++ > 4){
					addfaces_from_edgenet(em);
					BKE_mesh_end_editmesh(me, em);
					return;
				} else {
				/* if 4 edges exist, we just create the face, convex or not */
					efa= addface_from_edges(em);
					if(efa==NULL) {
						
						/* the order of vertices can be anything, 6 cases to check */
						if( convex(neweve[0]->co, neweve[1]->co, neweve[2]->co, neweve[3]->co) ) {
							efa= addfacelist(em, neweve[0], neweve[1], neweve[2], neweve[3], NULL, NULL);
						}
						else if( convex(neweve[0]->co, neweve[2]->co, neweve[3]->co, neweve[1]->co) ) {
							efa= addfacelist(em, neweve[0], neweve[2], neweve[3], neweve[1], NULL, NULL);
						}
						else if( convex(neweve[0]->co, neweve[2]->co, neweve[1]->co, neweve[3]->co) ) {
							efa= addfacelist(em, neweve[0], neweve[2], neweve[1], neweve[3], NULL, NULL);
						}
						else if( convex(neweve[0]->co, neweve[1]->co, neweve[3]->co, neweve[2]->co) ) {
							efa= addfacelist(em, neweve[0], neweve[1], neweve[3], neweve[2], NULL, NULL);
						}
						else if( convex(neweve[0]->co, neweve[3]->co, neweve[2]->co, neweve[1]->co) ) {
							efa= addfacelist(em, neweve[0], neweve[3], neweve[2], neweve[1], NULL, NULL);
						}
						else if( convex(neweve[0]->co, neweve[3]->co, neweve[1]->co, neweve[2]->co) ) {
							efa= addfacelist(em, neweve[0], neweve[3], neweve[1], neweve[2], NULL, NULL);
						}
						else printf("cannot find nice quad from concave set of vertices\n");
					}
				}
			}
			else BKE_report(op->reports, RPT_ERROR, "The selected vertices already form a face");
		}
		else BKE_report(op->reports, RPT_ERROR, "The selected vertices already form a face");
	}
	
	if(efa) {
		EM_select_face(efa, 1);

		fix_new_face(em, efa);
		
		recalc_editnormals(em);
	}

	BKE_mesh_end_editmesh(me, em);
}

/* ************************ primitives ******************* */

// HACK: these can also be found in cmoview.tga.c, but are here so that they can be found by linker
// this hack is only used so that scons+mingw + split-sources hack works
	// ------------------------------- start copied code
/* these are not the monkeys you are looking for */
int monkeyo= 4;
int monkeynv= 271;
int monkeynf= 250;
signed char monkeyv[271][3]= {
{-71,21,98},{-63,12,88},{-57,7,74},{-82,-3,79},{-82,4,92},
{-82,17,100},{-92,21,102},{-101,12,95},{-107,7,83},
{-117,31,84},{-109,31,95},{-96,31,102},{-92,42,102},
{-101,50,95},{-107,56,83},{-82,66,79},{-82,58,92},
{-82,46,100},{-71,42,98},{-63,50,88},{-57,56,74},
{-47,31,72},{-55,31,86},{-67,31,97},{-66,31,99},
{-70,43,100},{-82,48,103},{-93,43,105},{-98,31,105},
{-93,20,105},{-82,31,106},{-82,15,103},{-70,20,100},
{-127,55,95},{-127,45,105},{-127,-87,94},{-127,-41,100},
{-127,-24,102},{-127,-99,92},{-127,52,77},{-127,73,73},
{-127,115,-70},{-127,72,-109},{-127,9,-106},{-127,-49,-45},
{-101,-24,72},{-87,-56,73},{-82,-89,73},{-80,-114,68},
{-85,-121,67},{-104,-124,71},{-127,-126,74},{-71,-18,68},
{-46,-5,69},{-21,19,57},{-17,55,76},{-36,62,80},
{-64,77,88},{-86,97,94},{-107,92,97},{-119,63,96},
{-106,53,99},{-111,39,98},{-101,12,95},{-79,2,90},
{-64,8,86},{-47,24,83},{-45,38,83},{-50,48,85},
{-72,56,92},{-95,60,97},{-127,-98,94},{-113,-92,94},
{-112,-107,91},{-119,-113,89},{-127,-114,88},{-127,-25,96},
{-127,-18,95},{-114,-19,95},{-111,-29,96},{-116,-37,95},
{-76,-6,86},{-48,7,80},{-34,26,77},{-32,48,84},
{-39,53,93},{-71,70,102},{-87,82,107},{-101,79,109},
{-114,55,108},{-111,-13,104},{-100,-57,91},{-95,-90,88},
{-93,-105,85},{-97,-117,81},{-106,-119,81},{-127,-121,82},
{-127,6,93},{-127,27,98},{-85,61,95},{-106,18,96},
{-110,27,97},{-112,-88,94},{-117,-57,96},{-127,-57,96},
{-127,-42,95},{-115,-35,100},{-110,-29,102},{-113,-17,100},
{-122,-16,100},{-127,-26,106},{-121,-19,104},{-115,-20,104},
{-113,-29,106},{-117,-32,103},{-127,-37,103},{-94,-40,71},
{-106,-31,91},{-104,-40,91},{-97,-32,71},{-127,-112,88},
{-121,-111,88},{-115,-105,91},{-115,-95,93},{-127,-100,84},
{-115,-96,85},{-115,-104,82},{-121,-109,81},{-127,-110,81},
{-105,28,100},{-103,20,99},{-84,55,97},{-92,54,99},
{-73,51,99},{-55,45,89},{-52,37,88},{-53,25,87},
{-66,13,92},{-79,8,95},{-98,14,100},{-104,38,100},
{-100,48,100},{-97,46,97},{-102,38,97},{-96,16,97},
{-79,11,93},{-68,15,90},{-57,27,86},{-56,36,86},
{-59,43,87},{-74,50,96},{-91,51,98},{-84,52,96},
{-101,22,96},{-102,29,96},{-113,59,78},{-102,85,79},
{-84,88,76},{-65,71,71},{-40,58,63},{-25,52,59},
{-28,21,48},{-50,0,53},{-71,-12,60},{-127,115,37},
{-127,126,-10},{-127,-25,-86},{-127,-59,24},{-127,-125,59},
{-127,-103,44},{-127,-73,41},{-127,-62,36},{-18,30,7},
{-17,41,-6},{-28,34,-56},{-68,56,-90},{-33,-6,9},
{-51,-16,-21},{-45,-1,-55},{-84,7,-85},{-97,-45,52},
{-104,-53,33},{-90,-91,49},{-95,-64,50},{-85,-117,51},
{-109,-97,47},{-111,-69,46},{-106,-121,56},{-99,-36,55},
{-100,-29,60},{-101,-22,64},{-100,-50,21},{-89,-40,-34},
{-83,-19,-69},{-69,111,-49},{-69,119,-9},{-69,109,30},
{-68,67,55},{-34,52,43},{-46,58,36},{-45,90,7},
{-25,72,16},{-25,79,-15},{-45,96,-25},{-45,87,-57},
{-25,69,-46},{-48,42,-75},{-65,3,-70},{-22,42,-26},
{-75,-22,19},{-72,-25,-27},{-13,52,-30},{-28,-18,-16},
{6,-13,-42},{37,7,-55},{46,41,-54},{31,65,-54},
{4,61,-40},{3,53,-37},{25,56,-50},{35,37,-52},
{28,10,-52},{5,-5,-39},{-21,-9,-17},{-9,46,-28},
{-6,39,-37},{-14,-3,-27},{6,0,-47},{25,12,-57},
{31,32,-57},{23,46,-56},{4,44,-46},{-19,37,-27},
{-20,22,-35},{-30,12,-35},{-22,11,-35},{-19,2,-35},
{-23,-2,-35},{-34,0,-9},{-35,-3,-22},{-35,5,-24},
{-25,26,-27},{-13,31,-34},{-13,30,-41},{-23,-2,-41},
{-18,2,-41},{-21,10,-41},{-29,12,-41},{-19,22,-41},
{6,42,-53},{25,44,-62},{34,31,-63},{28,11,-62},
{7,0,-54},{-14,-2,-34},{-5,37,-44},{-13,14,-42},
{-7,8,-43},{1,16,-47},{-4,22,-45},{3,30,-48},
{8,24,-49},{15,27,-50},{12,35,-50},{4,56,-62},
{33,60,-70},{48,38,-64},{41,7,-68},{6,-11,-63},
{-26,-16,-42},{-17,49,-49},
};

signed char monkeyf[250][4]= {
{27,4,5,26}, {25,4,5,24}, {3,6,5,4}, {1,6,5,2}, {5,6,7,4}, 
{3,6,7,2}, {5,8,7,6}, {3,8,7,4}, {7,8,9,6}, 
{5,8,9,4}, {7,10,9,8}, {5,10,9,6}, {9,10,11,8}, 
{7,10,11,6}, {9,12,11,10}, {7,12,11,8}, {11,6,13,12}, 
{5,4,13,12}, {3,-2,13,12}, {-3,-4,13,12}, {-5,-10,13,12}, 
{-11,-12,14,12}, {-13,-18,14,13}, {-19,4,5,13}, {10,12,4,4}, 
{10,11,9,9}, {8,7,9,9}, {7,5,6,6}, {6,3,4,4}, 
{5,1,2,2}, {4,-1,0,0}, {3,-3,-2,-2}, {22,67,68,23}, 
{20,65,66,21}, {18,63,64,19}, {16,61,62,17}, {14,59,60,15}, 
{12,19,48,57}, {18,19,48,47}, {18,19,48,47}, {18,19,48,47}, 
{18,19,48,47}, {18,19,48,47}, {18,19,48,47}, {18,19,48,47}, 
{18,19,48,47}, {18,-9,-8,47}, {18,27,45,46}, {26,55,43,44}, 
{24,41,42,54}, {22,39,40,23}, {20,37,38,21}, {18,35,36,19}, 
{16,33,34,17}, {14,31,32,15}, {12,39,30,13}, {11,48,45,38}, 
{8,36,-19,9}, {8,-20,44,47}, {42,45,46,43}, {18,19,40,39}, 
{16,17,38,37}, {14,15,36,35}, {32,44,43,33}, {12,33,32,42}, 
{19,44,43,42}, {40,41,42,-27}, {8,9,39,-28}, {15,43,42,16}, 
{13,43,42,14}, {11,43,42,12}, {9,-30,42,10}, {37,12,38,-32}, 
{-33,37,45,46}, {-33,40,41,39}, {38,40,41,37}, {36,40,41,35}, 
{34,40,41,33}, {36,39,38,37}, {35,40,39,38}, {1,2,14,21}, 
{1,2,40,13}, {1,2,40,39}, {1,24,12,39}, {-34,36,38,11}, 
{35,38,36,37}, {-37,8,35,37}, {-11,-12,-45,40}, {-11,-12,39,38}, 
{-11,-12,37,36}, {-11,-12,35,34}, {33,34,40,41}, {33,34,38,39}, 
{33,34,36,37}, {33,-52,34,35}, {33,37,36,34}, {33,35,34,34}, 
{8,7,37,36}, {-32,7,35,46}, {-34,-33,45,46}, {4,-33,43,34}, 
{-34,-33,41,42}, {-34,-33,39,40}, {-34,-33,37,38}, {-34,-33,35,36}, 
{-34,-33,33,34}, {-34,-33,31,32}, {-34,-4,28,30}, {-5,-34,28,27}, 
{-35,-44,36,27}, {26,35,36,45}, {24,25,44,45}, {25,23,44,42}, 
{25,24,41,40}, {25,24,39,38}, {25,24,37,36}, {25,24,35,34}, 
{25,24,33,32}, {25,24,31,30}, {15,24,29,38}, {25,24,27,26}, 
{23,12,37,26}, {11,12,35,36}, {-86,-59,36,-80}, {-60,-61,36,35}, 
{-62,-63,36,35}, {-64,-65,36,35}, {-66,-67,36,35}, {-68,-69,36,35}, 
{-70,-71,36,35}, {-72,-73,36,35}, {-74,-75,36,35}, {42,43,53,58}, 
{40,41,57,56}, {38,39,55,57}, {-81,-80,37,56}, {-83,-82,55,52}, 
{-85,-84,51,49}, {-87,-86,48,49}, {47,50,51,48}, {46,48,51,49}, 
{43,46,49,44}, {-92,-91,45,42}, {-23,49,50,-20}, {-94,40,48,-24}, 
{-96,-22,48,49}, {-97,48,21,-90}, {-100,36,50,23}, {22,49,48,-100}, 
{-101,47,46,22}, {21,45,35,25}, {33,34,44,41}, {13,14,28,24}, 
{-107,26,30,-106}, {14,46,45,15}, {14,44,43,-110}, {-111,42,23,-110}, 
{6,7,45,46}, {45,44,47,46}, {45,46,47,48}, {47,46,49,48}, 
{17,49,47,48}, {17,36,46,48}, {35,36,44,45}, {35,36,40,43}, 
{35,36,38,39}, {-4,-3,37,35}, {-123,34,33,1}, {-9,-8,-7,-6}, 
{-10,-7,32,-125}, {-127,-11,-126,-126}, {-7,-6,5,31}, {4,5,33,30}, 
{4,39,33,32}, {4,35,32,38}, {20,21,39,38}, {4,37,38,5}, 
{-11,-10,36,3}, {-11,15,14,35}, {13,16,34,34}, {-13,14,13,13}, 
{-3,1,30,29}, {-3,28,29,1}, {-2,31,28,-1}, {12,13,27,30}, 
{-2,26,12,12}, {35,29,42,36}, {34,35,36,33}, {32,35,36,31}, 
{30,35,36,29}, {28,35,36,27}, {26,35,36,25}, {34,39,38,35}, 
{32,39,38,33}, {30,39,38,31}, {28,39,38,29}, {26,39,38,27}, 
{25,31,32,38}, {-18,-17,45,44}, {-18,17,28,44}, {-24,-20,42,-23}, 
{11,35,27,14}, {25,28,39,41}, {37,41,40,38}, {34,40,36,35}, 
{32,40,39,33}, {30,39,31,40}, {21,29,39,22}, {-31,37,28,4}, 
{-32,33,35,36}, {32,33,34,34}, {18,35,36,48}, {34,25,40,35}, 
{24,25,38,39}, {24,25,36,37}, {24,25,34,35}, {24,25,32,33}, 
{24,13,41,31}, {17,11,41,35}, {15,16,34,35}, {13,14,34,35}, 
{11,12,34,35}, {9,10,34,35}, {7,8,34,35}, {26,25,37,36}, 
{35,36,37,38}, {37,36,39,38}, {37,38,39,40}, {25,31,36,39}, 
{18,34,35,30}, {17,22,30,33}, {19,29,21,20}, {16,26,29,17}, 
{24,29,28,25}, {22,31,28,23}, {20,31,30,21}, {18,31,30,19}, 
{16,30,17,17}, {-21,-22,35,34}, {-21,-22,33,32}, {-21,-22,31,30}, 
{-21,-22,29,28}, {-21,-22,27,26}, {-28,-22,25,31}, {24,28,29,30}, 
{23,24,26,27}, {23,24,25,25}, {-69,-35,-32,27}, {-70,26,25,-66}, 
{-68,-67,24,-33}, 
};
	// ------------------------------- end copied code


#define PRIM_PLANE		0
#define PRIM_CUBE		1
#define PRIM_CIRCLE		4
#define PRIM_CYLINDER 	5
#define PRIM_CONE 		7
#define PRIM_GRID		10
#define PRIM_UVSPHERE	11
#define PRIM_ICOSPHERE 	12
#define PRIM_MONKEY		13

static void make_prim(Object *obedit, int type, float mat[4][4], int tot, int seg,
		int subdiv, float dia, float depth, int ext, int fill)
{
	/*
	 * type - for the type of shape
	 * dia - the radius for cone,sphere cylinder etc.
	 * depth - 
	 * ext - extrude
	 * fill - end capping, and option to fill in circle
	 * cent[3] - center of the data. 
	 * */
	EditMesh *em= BKE_mesh_get_editmesh(((Mesh *)obedit->data));
	EditVert *eve, *v1=NULL, *v2, *v3, *v4=NULL, *vtop, *vdown;
	float phi, phid, vec[3];
	float q[4], cmat[3][3], nor[3]= {0.0, 0.0, 0.0};
	short a, b;
	
	EM_clear_flag_all(em, SELECT);

	phid= 2.0f*(float)M_PI/tot;
	phi= .25f*(float)M_PI;

	switch(type) {
	case PRIM_GRID: /*  grid */
		/* clear flags */
		eve= em->verts.first;
		while(eve) {
			eve->f= 0;
			eve= eve->next;
		}
		/* one segment first: the X axis */
		phi= 1.0; 
		phid= 2.0/((float)tot-1);
		for(a=0;a<tot;a++) {
			vec[0]= dia*phi;
			vec[1]= - dia;
			vec[2]= 0.0f;
			Mat4MulVecfl(mat,vec);
			eve= addvertlist(em, vec, NULL);
			eve->f= 1+2+4;
			if (a) {
				addedgelist(em, eve->prev, eve, NULL);
			}
			phi-=phid;
		}
		/* extrude and translate */
		vec[0]= vec[2]= 0.0;
		vec[1]= dia*phid;
		Mat4Mul3Vecfl(mat, vec);
		
		for(a=0;a<seg-1;a++) {
			extrudeflag_vert(obedit, em, 2, nor);	// nor unused
			translateflag(em, 2, vec);
		}
		break;
	case PRIM_UVSPHERE: /*  UVsphere */
		
		/* clear all flags */
		eve= em->verts.first;
		while(eve) {
			eve->f= 0;
			eve= eve->next;
		}
		
		/* one segment first */
		phi= 0; 
		phid/=2;
		for(a=0; a<=tot; a++) {
			vec[0]= dia*sin(phi);
			vec[1]= 0.0;
			vec[2]= dia*cos(phi);
			eve= addvertlist(em, vec, NULL);
			eve->f= 1+2+4;
			if(a==0) v1= eve;
			else addedgelist(em, eve->prev, eve, NULL);
			phi+= phid;
		}
		
		/* extrude and rotate */
		phi= M_PI/seg;
		q[0]= cos(phi);
		q[3]= sin(phi);
		q[1]=q[2]= 0;
		QuatToMat3(q, cmat);
		
		for(a=0; a<seg; a++) {
			extrudeflag_vert(obedit, em, 2, nor); // nor unused
			rotateflag(em, 2, v1->co, cmat);
		}

		removedoublesflag(em, 4, 0, 0.0001);

		/* and now do imat */
		eve= em->verts.first;
		while(eve) {
			if(eve->f & SELECT) {
				Mat4MulVecfl(mat,eve->co);
			}
			eve= eve->next;
		}
		break;
	case PRIM_ICOSPHERE: /* Icosphere */
		{
			EditVert *eva[12];
			EditEdge *eed;
			
			/* clear all flags */
			eve= em->verts.first;
			while(eve) {
				eve->f= 0;
				eve= eve->next;
			}
			dia/=200;
			for(a=0;a<12;a++) {
				vec[0]= dia*icovert[a][0];
				vec[1]= dia*icovert[a][1];
				vec[2]= dia*icovert[a][2];
				eva[a]= addvertlist(em, vec, NULL);
				eva[a]->f= 1+2;
			}
			for(a=0;a<20;a++) {
				EditFace *evtemp;
				v1= eva[ icoface[a][0] ];
				v2= eva[ icoface[a][1] ];
				v3= eva[ icoface[a][2] ];
				evtemp = addfacelist(em, v1, v2, v3, 0, NULL, NULL);
				evtemp->e1->f = 1+2;
				evtemp->e2->f = 1+2;
				evtemp->e3->f = 1+2;
			}

			dia*=200;

			for(a=1; a<subdiv; a++) esubdivideflag(obedit, em, 2, dia, 0.0, 0, 1, 0);
			
			/* and now do imat */
			eve= em->verts.first;
			while(eve) {
				if(eve->f & 2) {
					Mat4MulVecfl(mat,eve->co);
				}
				eve= eve->next;
			}
			
			// Clear the flag 2 from the edges
			for(eed=em->edges.first;eed;eed=eed->next){
				if(eed->f & 2){
					   eed->f &= !2;
				}   
			}
		}
		break;
	case PRIM_MONKEY: /* Monkey */
		{
			//extern int monkeyo, monkeynv, monkeynf;
			//extern signed char monkeyf[][4];
			//extern signed char monkeyv[][3];
			EditVert **tv= MEM_mallocN(sizeof(*tv)*monkeynv*2, "tv");
			int i;

			for (i=0; i<monkeynv; i++) {
				float v[3];
				v[0]= (monkeyv[i][0]+127)/128.0, v[1]= monkeyv[i][1]/128.0, v[2]= monkeyv[i][2]/128.0;
				tv[i]= addvertlist(em, v, NULL);
				tv[i]->f |= SELECT;
				tv[monkeynv+i]= (fabs(v[0]= -v[0])<0.001)?tv[i]:addvertlist(em, v, NULL);
				tv[monkeynv+i]->f |= SELECT;
			}
			for (i=0; i<monkeynf; i++) {
				addfacelist(em, tv[monkeyf[i][0]+i-monkeyo], tv[monkeyf[i][1]+i-monkeyo], tv[monkeyf[i][2]+i-monkeyo], (monkeyf[i][3]!=monkeyf[i][2])?tv[monkeyf[i][3]+i-monkeyo]:NULL, NULL, NULL);
				addfacelist(em, tv[monkeynv+monkeyf[i][2]+i-monkeyo], tv[monkeynv+monkeyf[i][1]+i-monkeyo], tv[monkeynv+monkeyf[i][0]+i-monkeyo], (monkeyf[i][3]!=monkeyf[i][2])?tv[monkeynv+monkeyf[i][3]+i-monkeyo]:NULL, NULL, NULL);
			}

			MEM_freeN(tv);

			/* and now do imat */
			for(eve= em->verts.first; eve; eve= eve->next) {
				if(eve->f & SELECT) {
					Mat4MulVecfl(mat,eve->co);
				}
			}
			recalc_editnormals(em);
		}
		break;
	default: /* all types except grid, sphere... */
		if(type==PRIM_CONE);
		else if(ext==0) 
			depth= 0.0f;
	
		/* vertices */
		vtop= vdown= v1= v2= 0;
		for(b=0; b<=ext; b++) {
			for(a=0; a<tot; a++) {
				
				vec[0]= dia*sin(phi);
				vec[1]= dia*cos(phi);
				vec[2]= b?depth:-depth;
				
				Mat4MulVecfl(mat, vec);
				eve= addvertlist(em, vec, NULL);
				eve->f= SELECT;
				if(a==0) {
					if(b==0) v1= eve;
					else v2= eve;
				}
				phi+=phid;
			}
		}
			
		/* center vertices */
		/* type PRIM_CONE can only have 1 one side filled
		 * if the cone has no capping, dont add vtop */
		if((fill && type>1) || type == PRIM_CONE) {
			vec[0]= vec[1]= 0.0f;
			vec[2]= -depth;
			Mat4MulVecfl(mat, vec);
			vdown= addvertlist(em, vec, NULL);
			if((ext || type==PRIM_CONE) && fill) {
				vec[0]= vec[1]= 0.0f;
				vec[2]= depth;
				Mat4MulVecfl(mat,vec);
				vtop= addvertlist(em, vec, NULL);
			}
		} else {
			vdown= v1;
			vtop= v2;
		}
		if(vtop) vtop->f= SELECT;
		if(vdown) vdown->f= SELECT;
	
		/* top and bottom face */
		if(fill || type==PRIM_CONE) {
			if(tot==4 && (type==0 || type==1)) {
				v3= v1->next->next;
				if(ext) v4= v2->next->next;
				
				addfacelist(em, v3, v1->next, v1, v3->next, NULL, NULL);
				if(ext) addfacelist(em, v2, v2->next, v4, v4->next, NULL, NULL);
				
			}
			else {
				v3= v1;
				v4= v2;
				for(a=1; a<tot; a++) {
					addfacelist(em, vdown, v3, v3->next, 0, NULL, NULL);
					v3= v3->next;
					if(ext && fill) {
						addfacelist(em, vtop, v4, v4->next, 0, NULL, NULL);
						v4= v4->next;
					}
				}
				if(type>1) {
					addfacelist(em, vdown, v3, v1, 0, NULL, NULL);
					if(ext) addfacelist(em, vtop, v4, v2, 0, NULL, NULL);
				}
			}
		}
		else if(type==PRIM_CIRCLE) {  /* we need edges for a circle */
			v3= v1;
			for(a=1;a<tot;a++) {
				addedgelist(em, v3, v3->next, NULL);
				v3= v3->next;
			}
			addedgelist(em, v3, v1, NULL);
		}
		/* side faces */
		if(ext) {
			v3= v1;
			v4= v2;
			for(a=1; a<tot; a++) {
				addfacelist(em, v3, v3->next, v4->next, v4, NULL, NULL);
				v3= v3->next;
				v4= v4->next;
			}
			addfacelist(em, v3, v1, v2, v4, NULL, NULL);
		}
		else if(type==PRIM_CONE && fill) {
			/* add the bottom flat area of the cone
			 * if capping is disabled dont bother */
			v3= v1;
			for(a=1; a<tot; a++) {
				addfacelist(em, vtop, v3->next, v3, 0, NULL, NULL);
				v3= v3->next;
			}
			addfacelist(em, vtop, v1, v3, 0, NULL, NULL);
		}
	}
	
	EM_stats_update(em);
	/* simple selection flush OK, based on fact it's a single model */
	EM_select_flush(em); /* flushes vertex -> edge -> face selection */
	
	if(type!=0 && type!=13)
		righthandfaces(em, 1);	/* otherwise monkey has eyes in wrong direction */

	BKE_mesh_end_editmesh(obedit->data, em);
}


/* uses context to figure out transform for primitive */
/* returns standard diameter */
static float new_primitive_matrix(bContext *C, float primmat[][4])
{
	Object *obedit= CTX_data_edit_object(C);
	Scene *scene = CTX_data_scene(C);
	View3D *v3d =CTX_wm_view3d(C);
	RegionView3D *rv3d= ED_view3d_context_rv3d(C);
	float *curs, mat[3][3], vmat[3][3], cmat[3][3], imat[3][3];
	
	Mat4One(primmat);
	
	if(rv3d)
		Mat3CpyMat4(vmat, rv3d->viewmat);
	else
		Mat3One(vmat);
	
	/* inverse transform for view and object */
	Mat3CpyMat4(mat, obedit->obmat);
	Mat3MulMat3(cmat, vmat, mat);
	Mat3Inv(imat, cmat);
	Mat4CpyMat3(primmat, imat);

	/* center */
	curs= give_cursor(scene, v3d);
	VECCOPY(primmat[3], curs);
	VECSUB(primmat[3], primmat[3], obedit->obmat[3]);
	Mat3Inv(imat, mat);
	Mat3MulVecfl(imat, primmat[3]);
	
	if(v3d) return v3d->grid;
	return 1.0f;
}

/* ********* add primitive operators ************* */

static int add_primitive_plane_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	/* plane (diameter of 1.41 makes it unit size) */
	dia*= sqrt(2.0f);
	
	make_prim(obedit, PRIM_PLANE, mat, 4, 0, 0, dia, 0.0f, 0, 1);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_plane_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Plane";
	ot->idname= "MESH_OT_primitive_plane_add";
	
	/* api callbacks */
	ot->exec= add_primitive_plane_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int add_primitive_cube_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	/* plane (diameter of 1.41 makes it unit size) */
	dia*= sqrt(2.0f);
	
	make_prim(obedit, PRIM_CUBE, mat, 4, 0, 0, dia, 1.0f, 1, 1);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_cube_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Cube";
	ot->idname= "MESH_OT_primitive_cube_add";
	
	/* api callbacks */
	ot->exec= add_primitive_cube_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int add_primitive_circle_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	dia *= RNA_float_get(op->ptr,"radius");
	
	make_prim(obedit, PRIM_CIRCLE, mat, RNA_int_get(op->ptr, "vertices"), 0, 0, dia, 0.0f, 0, 
			  RNA_boolean_get(op->ptr, "fill"));
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_circle_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Circle";
	ot->idname= "MESH_OT_primitive_circle_add";
	
	/* api callbacks */
	ot->exec= add_primitive_circle_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_int(ot->srna, "vertices", 32, INT_MIN, INT_MAX, "Vertices", "", 3, 500);
	RNA_def_float(ot->srna, "radius", 1.0f, -FLT_MAX, FLT_MAX, "Radius", "", 0.001, 100.00);
	RNA_def_boolean(ot->srna, "fill", 0, "Fill", "");
}

static int add_primitive_cylinder_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	dia *= RNA_float_get(op->ptr, "radius");
	
	make_prim(obedit, PRIM_CYLINDER, mat, RNA_int_get(op->ptr, "vertices"), 0, 0, dia, 
			  RNA_float_get(op->ptr, "depth"), 1, 1);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_cylinder_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Cylinder";
	ot->idname= "MESH_OT_primitive_cylinder_add";
	
	/* api callbacks */
	ot->exec= add_primitive_cylinder_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_int(ot->srna, "vertices", 32, INT_MIN, INT_MAX, "Vertices", "", 2, 500);
	RNA_def_float(ot->srna, "radius", 1.0f, -FLT_MAX, FLT_MAX, "Radius", "", 0.001, 100.00);
	RNA_def_float(ot->srna, "depth", 1.0f, -FLT_MAX, FLT_MAX, "Depth", "", 0.001, 100.00);
}

static int add_primitive_tube_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	dia *= RNA_float_get(op->ptr, "radius");
	
	make_prim(obedit, PRIM_CYLINDER, mat, RNA_int_get(op->ptr, "vertices"), 0, 0, dia, 
			  RNA_float_get(op->ptr, "depth"), 1, 0);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_tube_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Tube";
	ot->idname= "MESH_OT_primitive_tube_add";
	
	/* api callbacks */
	ot->exec= add_primitive_tube_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_int(ot->srna, "vertices", 32, INT_MIN, INT_MAX, "Vertices", "", 2, 500);
	RNA_def_float(ot->srna, "radius", 1.0f, -FLT_MAX, FLT_MAX, "Radius", "", 0.001, 100.00);
	RNA_def_float(ot->srna, "depth", 1.0f, -FLT_MAX, FLT_MAX, "Depth", "", 0.001, 100.00);
}

static int add_primitive_cone_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	dia *= RNA_float_get(op->ptr, "radius");
	
	make_prim(obedit, PRIM_CONE, mat, RNA_int_get(op->ptr, "vertices"), 0, 0, dia, 
			  RNA_float_get(op->ptr, "depth"), 0, RNA_boolean_get(op->ptr, "cap_end"));
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_cone_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Cone";
	ot->idname= "MESH_OT_primitive_cone_add";
	
	/* api callbacks */
	ot->exec= add_primitive_cone_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_int(ot->srna, "vertices", 32, INT_MIN, INT_MAX, "Vertices", "", 2, 500);
	RNA_def_float(ot->srna, "radius", 1.0f, -FLT_MAX, FLT_MAX, "Radius", "", 0.001, 100.00);
	RNA_def_float(ot->srna, "depth", 1.0f, -FLT_MAX, FLT_MAX, "Depth", "", 0.001, 100.00);
	RNA_def_boolean(ot->srna, "cap_end", 0, "Cap End", "");

}

static int add_primitive_grid_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	dia*= RNA_float_get(op->ptr, "size");
	
	make_prim(obedit, PRIM_GRID, mat, RNA_int_get(op->ptr, "x_subdivisions"), 
			  RNA_int_get(op->ptr, "y_subdivisions"), 0, dia, 0.0f, 0, 1);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_grid_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Grid";
	ot->idname= "MESH_OT_primitive_grid_add";
	
	/* api callbacks */
	ot->exec= add_primitive_grid_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_int(ot->srna, "x_subdivisions", 10, INT_MIN, INT_MAX, "X Subdivisions", "", 3, 1000);
	RNA_def_int(ot->srna, "y_subdivisions", 10, INT_MIN, INT_MAX, "Y Subdivisons", "", 3, 1000);
	RNA_def_float(ot->srna, "size", 1.0f, -FLT_MAX, FLT_MAX, "Size", "", 0.001, FLT_MAX);
}

static int add_primitive_monkey_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float mat[4][4];
	
	new_primitive_matrix(C, mat);
	
	make_prim(obedit, PRIM_MONKEY, mat, 0, 0, 2, 0.0f, 0.0f, 0, 0);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_monkey_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Monkey";
	ot->idname= "MESH_OT_primitive_monkey_add";
	
	/* api callbacks */
	ot->exec= add_primitive_monkey_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
}

static int add_primitive_uvsphere_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	dia*= RNA_float_get(op->ptr, "size");

	make_prim(obedit, PRIM_UVSPHERE, mat, RNA_int_get(op->ptr, "rings"), 
			  RNA_int_get(op->ptr, "segments"), 0, dia, 0.0f, 0, 0);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_uv_sphere_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add UV Sphere";
	ot->idname= "MESH_OT_primitive_uv_sphere_add";
	
	/* api callbacks */
	ot->exec= add_primitive_uvsphere_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_int(ot->srna, "segments", 32, INT_MIN, INT_MAX, "Segments", "", 3, 500);
	RNA_def_int(ot->srna, "rings", 24, INT_MIN, INT_MAX, "Rings", "", 3, 500);
	RNA_def_float(ot->srna, "size", 1.0f, -FLT_MAX, FLT_MAX, "Size", "", 0.001, 100.00);
}

static int add_primitive_icosphere_exec(bContext *C, wmOperator *op)
{
	Scene *scene = CTX_data_scene(C);
	Object *obedit= CTX_data_edit_object(C);
	float dia, mat[4][4];
	
	dia= new_primitive_matrix(C, mat);
	dia*= RNA_float_get(op->ptr, "size");
	
	make_prim(obedit, PRIM_ICOSPHERE, mat, 0, 0, 
			  RNA_int_get(op->ptr, "subdivisions"), dia, 0.0f, 0, 0);
	
	DAG_object_flush_update(scene, obedit, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, obedit);
	
	return OPERATOR_FINISHED;	
}

void MESH_OT_primitive_ico_sphere_add(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Add Ico Sphere";
	ot->idname= "MESH_OT_primitive_ico_sphere_add";
	
	/* api callbacks */
	ot->exec= add_primitive_icosphere_exec;
	ot->poll= ED_operator_editmesh;
	
	/* flags */
	ot->flag= OPTYPE_REGISTER|OPTYPE_UNDO;
	
	/* props */
	RNA_def_int(ot->srna, "subdivisions", 2, 0, 6, "Subdivisions", "", 0, 8);
	RNA_def_float(ot->srna, "size", 1.0f, 0.0f, FLT_MAX, "Size", "", 0.001f, 100.00);
}

/****************** add duplicate operator ***************/

static int mesh_duplicate_exec(bContext *C, wmOperator *op)
{
	Scene *scene= CTX_data_scene(C);
	Object *ob= CTX_data_edit_object(C);
	EditMesh *em= BKE_mesh_get_editmesh(ob->data);

	adduplicateflag(em, SELECT);

	BKE_mesh_end_editmesh(ob->data, em);

	DAG_object_flush_update(scene, ob, OB_RECALC_DATA);
	WM_event_add_notifier(C, NC_OBJECT|ND_GEOM_SELECT, ob);
	
	return OPERATOR_FINISHED;
}

static int mesh_duplicate_invoke(bContext *C, wmOperator *op, wmEvent *event)
{
	WM_cursor_wait(1);
	mesh_duplicate_exec(C, op);
	WM_cursor_wait(0);
	
	RNA_int_set(op->ptr, "mode", TFM_TRANSLATION);
	WM_operator_name_call(C, "TFM_OT_transform", WM_OP_INVOKE_REGION_WIN, op->ptr);
	
	return OPERATOR_FINISHED;
}

void MESH_OT_duplicate(wmOperatorType *ot)
{
	/* identifiers */
	ot->name= "Duplicate";
	ot->idname= "MESH_OT_duplicate";
	
	/* api callbacks */
	ot->invoke= mesh_duplicate_invoke;
	ot->exec= mesh_duplicate_exec;
	
	ot->poll= ED_operator_editmesh;
	
	/* to give to transform */
	RNA_def_int(ot->srna, "mode", TFM_TRANSLATION, 0, INT_MAX, "Mode", "", 0, INT_MAX);
}

