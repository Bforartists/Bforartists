/**
 * $Id$
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef WIN32
#include <unistd.h>
#else
#include <io.h>
#endif

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_effect_types.h"
#include "DNA_image_types.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_meta_types.h"
#include "DNA_object_types.h"
#include "DNA_object_force.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"
#include "DNA_userdef_types.h"
#include "DNA_property_types.h"
#include "DNA_vfont_types.h"
#include "DNA_constraint_types.h"

#include "BIF_editview.h"
#include "BIF_resources.h"
#include "BIF_mywindow.h"
#include "BIF_gl.h"
#include "BIF_editlattice.h"
#include "BIF_editconstraint.h"
#include "BIF_editarmature.h"
#include "BIF_editmesh.h"
#include "BIF_poseobject.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_blender.h"
#include "BKE_curve.h"
#include "BKE_constraint.h"
#include "BKE_depsgraph.h"
#include "BKE_displist.h"
#include "BKE_effect.h"
#include "BKE_font.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_lattice.h"
#include "BKE_mball.h"
#include "BKE_object.h"
#include "BKE_softbody.h"
#include "BKE_utildefines.h"

#include "BSE_view.h"
#include "BSE_edit.h"
#include "BSE_editaction.h"
#include "BSE_editipo.h"
#include "BSE_editipo_types.h"
#include "BSE_editaction.h"

#include "BDR_editobject.h"		// reset_slowparents()

#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "blendef.h"

#include "mydevice.h"

extern ListBase editNurb;
extern ListBase editelems;

#include "transform.h"


/* ************************** Functions *************************** */

static void qsort_trans_data(TransInfo *t, TransData *head, TransData *tail) {
	TransData pivot = *head;
	TransData *ihead = head;
	TransData *itail = tail;
	short connected = t->flag & T_PROP_CONNECTED;

	while (head < tail)
	{
		if (connected) {
			while ((tail->dist >= pivot.dist) && (head < tail))
				tail--;
		}
		else {
			while ((tail->rdist >= pivot.rdist) && (head < tail))
				tail--;
		}

		if (head != tail)
		{
			*head = *tail;
			head++;
		}

		if (connected) {
			while ((head->dist <= pivot.dist) && (head < tail))
				head++;
		}
		else {
			while ((head->rdist <= pivot.rdist) && (head < tail))
				head++;
		}

		if (head != tail)
		{
			*tail = *head;
			tail--;
		}
	}

	*head = pivot;
	if (ihead < head) {
		qsort_trans_data(t, ihead, head-1);
	}
	if (itail > head) {
		qsort_trans_data(t, head+1, itail);
	}
}

void sort_trans_data_dist(TransInfo *t) {
	TransData *start = t->data;
	int i = 1;

	while(i < t->total && start->flag & TD_SELECTED) {
		start++;
		i++;
	}
	qsort_trans_data(t, start, t->data + t->total - 1);
}

static void sort_trans_data(TransInfo *t) 
{
	TransData *sel, *unsel;
	TransData temp;
	unsel = t->data;
	sel = t->data;
	sel += t->total - 1;
	while (sel > unsel) {
		while (unsel->flag & TD_SELECTED) {
			unsel++;
			if (unsel == sel) {
				return;
			}
		}
		while (!(sel->flag & TD_SELECTED)) {
			sel--;
			if (unsel == sel) {
				return;
			}
		}
		temp = *unsel;
		*unsel = *sel;
		*sel = temp;
		sel--;
		unsel++;
	}
}


/* distance calculated from not-selected vertex to nearest selected vertex
   warning; this is loops inside loop, has minor N^2 issues, but by sorting list it is OK */
static void set_prop_dist(TransInfo *t, short with_dist)
{
	TransData *tob;
	int a;
	
	for(a=0, tob= t->data; a<t->total; a++, tob++) {
		
		tob->rdist= 0.0f; // init, it was mallocced
		
		if((tob->flag & TD_SELECTED)==0) {
			TransData *td;
			int i;
			float dist, vec[3];

			tob->rdist = -1.0f; // signal for next loop
				
			for (i = 0, td= t->data; i < t->total; i++, td++) {
				if(td->flag & TD_SELECTED) {
					VecSubf(vec, tob->center, td->center);
					Mat3MulVecfl(tob->mtx, vec);
					dist = Normalise(vec);
					if (tob->rdist == -1.0f) {
						tob->rdist = dist;
					}
					else if (dist < tob->rdist) {
						tob->rdist = dist;
					}
				}
				else break;	// by definition transdata has selected items in beginning
			}
			if (with_dist) {
				tob->dist = tob->rdist;
			}
		}	
	}
}

/* ************************** CONVERSIONS ************************* */

/* ********************* texture space ********* */

static void createTransTexspace(TransInfo *t)
{
	TransData *td;
	Object *ob;
	ID *id;
	
	ob= OBACT;
	t->total = 1;
	td= t->data= MEM_callocN(sizeof(TransData), "TransTexspace");
	td->ext= t->ext= MEM_callocN(sizeof(TransDataExtension), "TransTexspace");
	
	td->flag= TD_SELECTED;
	VECCOPY(td->center, ob->obmat[3]);
	td->ob = ob;
	
	Mat3CpyMat4(td->mtx, ob->obmat);
	Mat3Inv(td->smtx, td->mtx);
	
	id= ob->data;
	if(id==0);
	else if( GS(id->name)==ID_ME) {
		Mesh *me= ob->data;
		me->texflag &= ~AUTOSPACE;
		td->loc= me->loc;
		td->ext->rot= me->rot;
		td->ext->size= me->size;
	}
	else if( GS(id->name)==ID_CU) {
		Curve *cu= ob->data;
		cu->texflag &= ~CU_AUTOSPACE;
		td->loc= cu->loc;
		td->ext->rot= cu->rot;
		td->ext->size= cu->size;
	}
	else if( GS(id->name)==ID_MB) {
		MetaBall *mb= ob->data;
		mb->texflag &= ~MB_AUTOSPACE;
		td->loc= mb->loc;
		td->ext->rot= mb->rot;
		td->ext->size= mb->size;
	}
	
	VECCOPY(td->iloc, td->loc);
	VECCOPY(td->ext->irot, td->ext->rot);
	VECCOPY(td->ext->isize, td->ext->size);
}

/* ********************* edge (for crease) ***** */

static void createTransEdge(TransInfo *t) {
	TransData *td = NULL;
	EditMesh *em = G.editMesh;
	EditEdge *eed;
	Mesh *me = G.obedit->data;
	float mtx[3][3], smtx[3][3];
	int count=0, countsel=0;
	int propmode = t->flag & T_PROP_EDIT;

	/* THIS IS A REALLY STUPID HACK, MUST BE A BETTER WAY TO DO IT */
	/* this is sufficient to invoke edges added in mesh, but only in editmode */
	if(me->medge==NULL) {
		me->medge= MEM_callocN(sizeof(MEdge), "fake medge");
		me->totedge= 1;
		allqueue(REDRAWBUTSEDIT, 0);
	}
					
	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->h==0) {
			if (eed->f & SELECT) countsel++;
			if (propmode) count++;
		}
	}

	if (countsel == 0)
		return;

	if(propmode) {
		t->total = count;
	}
	else {
		t->total = countsel;
	}

	td= t->data= MEM_callocN(t->total * sizeof(TransData), "TransCrease");

	Mat3CpyMat4(mtx, G.obedit->obmat);
	Mat3Inv(smtx, mtx);

	for(eed= em->edges.first; eed; eed= eed->next) {
		if(eed->h==0 && (eed->f & SELECT || propmode)) {
			/* need to set center for center calculations */
			VecAddf(td->center, eed->v1->co, eed->v2->co);
			VecMulf(td->center, 0.5f);

			td->loc= NULL;
			if (eed->f & SELECT)
				td->flag= TD_SELECTED;
			else 
				td->flag= 0;


			Mat3CpyMat3(td->smtx, smtx);
			Mat3CpyMat3(td->mtx, mtx);

			td->ext = NULL;
			td->tdi = NULL;
			td->val = &(eed->crease);
			td->ival = eed->crease;

			td++;
		}
	}
}

/* ********************* pose mode ************* */

/* recursive, make sure it's identical structured as next one */
/* only counts the parent selection, and tags transform flag */
/* exported for manipulator */
void count_bone_select(TransInfo *t, ListBase *lb, int do_it) 
{
	Bone *bone;
	int do_next=do_it;
	
	for(bone= lb->first; bone; bone= bone->next) {
		bone->flag &= ~BONE_TRANSFORM;
		if(do_it) {
			if (bone->flag & BONE_SELECTED) {
				/* We don't let IK children get "grabbed" */
				if ( (t->mode!=TFM_TRANSLATION) || (bone->flag & BONE_IK_TOPARENT)==0 ) {
					bone->flag |= BONE_TRANSFORM;
					t->total++;
					do_next= 0;	// no transform on children if one parent bone is selected
				}
			}
		}
		count_bone_select(t, &bone->childbase, do_next);
	}
}

static int add_pose_transdata(TransInfo *t, bPoseChannel *pchan, Object *ob, TransData *td)
{
	Bone *bone= pchan->bone;
	float	parmat[4][4], tempmat[4][4];
	float vec[3];

	if(bone) {
		if (bone->flag & BONE_TRANSFORM) {
			/* We don't let IK children get "grabbed" */
			if ( (t->mode!=TFM_TRANSLATION) || (bone->flag & BONE_IK_TOPARENT)==0 ) {
				
				VECCOPY(vec, pchan->pose_mat[3]);
				VECCOPY(td->center, vec);
				
				td->ob = ob;
				td->flag= TD_SELECTED|TD_USEQUAT;
				td->loc = pchan->loc;
				VECCOPY(td->iloc, pchan->loc);
				
				td->ext->rot= NULL;
				td->ext->quat= pchan->quat;
				td->ext->size= pchan->size;
				td->ext->bone= bone; //	FIXME: Dangerous

				QUATCOPY(td->ext->iquat, pchan->quat);
				VECCOPY(td->ext->isize, pchan->size);

				if (bone->parent) { /* apply parent transformation if there is one */
					bPoseChannel *pchan= get_pose_channel(G.obpose->pose, bone->parent->name);

					Mat4MulMat4(tempmat, bone->arm_mat, pchan->chan_mat);
				}
				else {
					Mat4CpyMat4(tempmat, bone->arm_mat);
				}
				Mat4MulMat4 (parmat, tempmat, ob->obmat);	

				Mat3CpyMat4 (td->mtx, parmat);
				Mat3Inv (td->smtx, td->mtx);

				Mat3CpyMat3(td->axismtx, td->mtx);
				Mat3Ortho(td->axismtx);
				
				return 1;
			}
		}
	}
	return 0;
}

static void createTransPose(TransInfo *t)
{
	bArmature *arm;
	bPoseChannel *pchan;
	TransData *td;
	TransDataExtension *tdx;
	int i;
	
	/* check validity of state */
	arm=get_armature (G.obpose);
	if (arm==NULL || G.obpose->pose==NULL) return;
	
	if (arm->flag & ARM_RESTPOS){
		notice ("Transformation not possible while Rest Position is enabled");
		return;
	}
	if (!(G.obpose->lay & G.vd->lay)) return;

	/* count total */
	count_bone_select(t, &arm->bonebase, 1);
	
	if(t->total==0 && t->mode==TFM_TRANSLATION) {
		t->mode= TFM_ROTATION;
		count_bone_select(t, &arm->bonebase, 1);
	}		
	if(t->total==0) return;
	
	/* since we need to be able to insert keys, no actions should be assigned */
	arm->flag |= ARM_NO_ACTION;

	/* init trans data */
    td = t->data = MEM_callocN(t->total*sizeof(TransData), "TransPoseBone");
    tdx = t->ext = MEM_callocN(t->total*sizeof(TransDataExtension), "TransPoseBoneExt");
	for(i=0; i<t->total; i++, td++, tdx++) {
		td->ext= tdx;
		td->tdi = NULL;
		td->val = NULL;
	}	
	
	/* use pose channels to fill trans data */
	td= t->data;
	for(pchan= G.obpose->pose->chanbase.first; pchan; pchan= pchan->next) {
		if( add_pose_transdata(t, pchan, G.obpose, td) ) td++;
	}
	if(td != (t->data+t->total)) printf("Bone selection count error\n");
	
}

/* ********************* armature ************** */

static void createTransArmatureVerts(TransInfo *t)
{
	EditBone *ebo;
	TransData *td;
	float mtx[3][3], smtx[3][3];

	t->total = 0;
	for (ebo=G.edbo.first;ebo;ebo=ebo->next){
		if (ebo->flag & BONE_TIPSEL){
			t->total++;
		}
		if (ebo->flag & BONE_ROOTSEL){
			t->total++;
		}
	}

    if (!t->total) return;
	
	Mat3CpyMat4(mtx, G.obedit->obmat);
	Mat3Inv(smtx, mtx);

    td = t->data = MEM_mallocN(t->total*sizeof(TransData), "TransEditBone");
	
	for (ebo=G.edbo.first;ebo;ebo=ebo->next){
		if (ebo->flag & BONE_TIPSEL){
			VECCOPY (td->iloc, ebo->tail);
			VECCOPY (td->center, td->iloc);
			td->loc= ebo->tail;
			td->flag= TD_SELECTED;

			Mat3CpyMat3(td->smtx, smtx);
			Mat3CpyMat3(td->mtx, mtx);

			td->ext = NULL;
			td->tdi = NULL;
			td->val = NULL;

			td++;
		}
		if (ebo->flag & BONE_ROOTSEL){
			VECCOPY (td->iloc, ebo->head);
			VECCOPY (td->center, td->iloc);
			td->loc= ebo->head;
			td->flag= TD_SELECTED;

			Mat3CpyMat3(td->smtx, smtx);
			Mat3CpyMat3(td->mtx, mtx);

			td->ext = NULL;
			td->tdi = NULL;
			td->val = NULL;

			td++;
		}
			
	}
}

/* ********************* meta elements ********* */

static void createTransMBallVerts(TransInfo *t)
{
 	MetaElem *ml;
	TransData *td;
	TransDataExtension *tx;
	float mtx[3][3], smtx[3][3];
	int count=0, countsel=0;
	int propmode = t->flag & T_PROP_EDIT;

	/* count totals */
	for(ml= editelems.first; ml; ml= ml->next) {
		if(ml->flag & SELECT) countsel++;
		if(propmode) count++;
	}

	/* note: in prop mode we need at least 1 selected */
	if (countsel==0) return;
	
	if(propmode) t->total = count; 
	else t->total = countsel;
	
	td = t->data= MEM_mallocN(t->total*sizeof(TransData), "TransObData(MBall EditMode)");
	tx = t->ext = MEM_mallocN(t->total*sizeof(TransDataExtension), "MetaElement_TransExtension");

	Mat3CpyMat4(mtx, G.obedit->obmat);
	Mat3Inv(smtx, mtx);
    
	for(ml= editelems.first; ml; ml= ml->next) {
		if(propmode || (ml->flag & SELECT)) {
			td->loc= &ml->x;
			VECCOPY(td->iloc, td->loc);
			VECCOPY(td->center, td->loc);

			if(ml->flag & SELECT) td->flag= TD_SELECTED | TD_USEQUAT | TD_SINGLESIZE;
			else td->flag= TD_USEQUAT;

			Mat3CpyMat3(td->smtx, smtx);
			Mat3CpyMat3(td->mtx, mtx);

			td->ext = tx;
			td->tdi = NULL;

			/* Radius of MetaElem (mass of MetaElem influence) */
			if(ml->flag & MB_SCALE_RAD){
				td->val = &ml->rad;
				td->ival = ml->rad;
			}
			else{
				td->val = &ml->s;
				td->ival = ml->s;
			}

			/* expx/expy/expz determine "shape" of some MetaElem types */
			tx->size = &ml->expx;
			tx->isize[0] = ml->expx;
			tx->isize[1] = ml->expy;
			tx->isize[2] = ml->expz;

			/* quat is used for rotation of MetaElem */
			tx->quat = ml->quat;
			QUATCOPY(tx->iquat, ml->quat);

			tx->rot = NULL;

			td++;
			tx++;
		}
	}
} 

/* ********************* curve/surface ********* */

static void calc_distanceCurveVerts(TransData *head, TransData *tail) {
	TransData *td, *td_near = NULL;
	for (td = head; td<=tail; td++) {
		if (td->flag & TD_SELECTED) {
			td_near = td;
			td->dist = 0.0f;
		}
		else if(td_near) {
			float dist;
			dist = VecLenf(td_near->center, td->center);
			if (dist < (td-1)->dist) {
				td->dist = (td-1)->dist;
			}
			else {
				td->dist = dist;
			}
		}
		else {
			td->dist = MAXFLOAT;
			td->flag |= TD_NOTCONNECTED;
		}
	}
	td_near = NULL;
	for (td = tail; td>=head; td--) {
		if (td->flag & TD_SELECTED) {
			td_near = td;
			td->dist = 0.0f;
		}
		else if(td_near) {
			float dist;
			dist = VecLenf(td_near->center, td->center);
			if (td->flag & TD_NOTCONNECTED || dist < td->dist || (td+1)->dist < td->dist) {
				td->flag &= ~TD_NOTCONNECTED;
				if (dist < (td+1)->dist) {
					td->dist = (td+1)->dist;
				}
				else {
					td->dist = dist;
				}
			}
		}
	}
}

static void createTransCurveVerts(TransInfo *t)
{
	TransData *td = NULL;
  	Nurb *nu;
	BezTriple *bezt;
	BPoint *bp;
	float mtx[3][3], smtx[3][3];
	int a;
	int count=0, countsel=0;
	int propmode = t->flag & T_PROP_EDIT;

	/* count total of vertices, check identical as in 2nd loop for making transdata! */
	for(nu= editNurb.first; nu; nu= nu->next) {
		if((nu->type & 7)==CU_BEZIER) {
			for(a=0, bezt= nu->bezt; a<nu->pntsu; a++, bezt++) {
				if(bezt->hide==0) {
					if(bezt->f1 & 1) countsel++;
					if(bezt->f2 & 1) countsel++;
					if(bezt->f3 & 1) countsel++;
					if(propmode) count+= 3;
				}
			}
		}
		else {
			for(a= nu->pntsu*nu->pntsv, bp= nu->bp; a>0; a--, bp++) {
				if(bp->hide==0) {
					if(propmode) count++;
					if(bp->f1 & 1) countsel++;
				}
			}
		}
	}
	/* note: in prop mode we need at least 1 selected */
	if (countsel==0) return;
	
	if(propmode) t->total = count; 
	else t->total = countsel;
	t->data= MEM_mallocN(t->total*sizeof(TransData), "TransObData(Curve EditMode)");

	Mat3CpyMat4(mtx, G.obedit->obmat);
	Mat3Inv(smtx, mtx);

    td = t->data;
	for(nu= editNurb.first; nu; nu= nu->next) {
		if((nu->type & 7)==CU_BEZIER) {
			TransData *head, *tail;
			head = tail = td;
			for(a=0, bezt= nu->bezt; a<nu->pntsu; a++, bezt++) {
				if(bezt->hide==0) {
					if(propmode || (bezt->f1 & 1)) {
						VECCOPY(td->iloc, bezt->vec[0]);
						td->loc= bezt->vec[0];
						VECCOPY(td->center, bezt->vec[1]);
						if(bezt->f1 & 1) td->flag= TD_SELECTED;
						else td->flag= 0;
						td->ext = NULL;
						td->tdi = NULL;
						td->val = NULL;

						Mat3CpyMat3(td->smtx, smtx);
						Mat3CpyMat3(td->mtx, mtx);

						td++;
						count++;
						tail++;
					}
					/* THIS IS THE CV, the other two are handles */
					if(propmode || (bezt->f2 & 1)) {
						VECCOPY(td->iloc, bezt->vec[1]);
						td->loc= bezt->vec[1];
						VECCOPY(td->center, td->loc);
						if(bezt->f2 & 1) td->flag= TD_SELECTED;
						else td->flag= 0;
						td->ext = NULL;
						td->tdi = NULL;
						td->val = &(bezt->alfa);
						td->ival = bezt->alfa;

						Mat3CpyMat3(td->smtx, smtx);
						Mat3CpyMat3(td->mtx, mtx);

						td++;
						count++;
						tail++;
					}
					if(propmode || (bezt->f3 & 1)) {
						VECCOPY(td->iloc, bezt->vec[2]);
						td->loc= bezt->vec[2];
						VECCOPY(td->center, bezt->vec[1]);
						if(bezt->f3 & 1) td->flag= TD_SELECTED;
						else td->flag= 0;
						td->ext = NULL;
						td->tdi = NULL;
						td->val = NULL;

						Mat3CpyMat3(td->smtx, smtx);
						Mat3CpyMat3(td->mtx, mtx);

						td++;
						count++;
						tail++;
					}
				}
				else if (propmode && head != tail) {
					calc_distanceCurveVerts(head, tail-1);
					head = tail;
				}
			}
			if (propmode && head != tail)
				calc_distanceCurveVerts(head, tail);
		}
		else {
			TransData *head, *tail;
			head = tail = td;
			for(a= nu->pntsu*nu->pntsv, bp= nu->bp; a>0; a--, bp++) {
				if(bp->hide==0) {
					if(propmode || (bp->f1 & 1)) {
						VECCOPY(td->iloc, bp->vec);
						td->loc= bp->vec;
						VECCOPY(td->center, td->loc);
						if(bp->f1 & 1) td->flag= TD_SELECTED;
						else td->flag= 0;
						td->ext = NULL;
						td->tdi = NULL;
						td->val = &(bp->alfa);
						td->ival = bp->alfa;

						Mat3CpyMat3(td->smtx, smtx);
						Mat3CpyMat3(td->mtx, mtx);

						td++;
						count++;
						tail++;
					}
				}
				else if (propmode && head != tail) {
					calc_distanceCurveVerts(head, tail-1);
					head = tail;
				}
			}
			if (propmode && head != tail)
				calc_distanceCurveVerts(head, tail-1);
		}
	}
}

/* ********************* lattice *************** */

static void createTransLatticeVerts(TransInfo *t)
{
	TransData *td = NULL;
	BPoint *bp;
	float mtx[3][3], smtx[3][3];
	int a;
	int count=0, countsel=0;
	int propmode = t->flag & T_PROP_EDIT;

	bp= editLatt->def;
	a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
	while(a--) {
		if(bp->f1 & 1) countsel++;
		if(propmode) count++;
		bp++;
	}
	
 	/* note: in prop mode we need at least 1 selected */
	if (countsel==0) return;
	
	if(propmode) t->total = count; 
	else t->total = countsel;
	t->data= MEM_mallocN(t->total*sizeof(TransData), "TransObData(Lattice EditMode)");
	
	Mat3CpyMat4(mtx, G.obedit->obmat);
	Mat3Inv(smtx, mtx);

	td = t->data;
	bp= editLatt->def;
	a= editLatt->pntsu*editLatt->pntsv*editLatt->pntsw;
	while(a--) {
		if(propmode || (bp->f1 & 1)) {
			if(bp->hide==0) {
				VECCOPY(td->iloc, bp->vec);
				td->loc= bp->vec;
				VECCOPY(td->center, td->loc);
				if(bp->f1 & 1) td->flag= TD_SELECTED;
				else td->flag= 0;
				Mat3CpyMat3(td->smtx, smtx);
				Mat3CpyMat3(td->mtx, mtx);

				td->ext = NULL;
				td->tdi = NULL;
				td->val = NULL;

				td++;
				count++;
			}
		}
		bp++;
	}
} 

/* ********************* mesh ****************** */

/* proportional distance based on connectivity  */
#define E_VEC(a)	(vectors + (3 * (int)(a)->vn))
#define E_NEAR(a)	(nears[((int)(a)->vn)])
static void editmesh_set_connectivity_distance(int total, float *vectors, EditVert **nears)
{
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditEdge *eed;
	int i= 0, done= 1;

	/* f2 flag is used for 'selection' */
	/* vn is offset on scratch array   */
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->h==0) {
			eve->vn = (EditVert *)(i++);

			if(eve->f & SELECT) {
				eve->f2= 2;
				E_NEAR(eve) = eve;
				E_VEC(eve)[0] = 0.0f;
				E_VEC(eve)[1] = 0.0f;
				E_VEC(eve)[2] = 0.0f;
			}
			else {
				eve->f2 = 0;
			}
		}
	}


	/* Floodfill routine */
	/*
	At worst this is n*n of complexity where n is number of edges 
	Best case would be n if the list is ordered perfectly.
	Estimate is n log n in average (so not too bad)
	*/
	while(done) {
		done= 0;
		
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->h==0) {
				EditVert *v1= eed->v1, *v2= eed->v2;
				float *vec2 = E_VEC(v2);
				float *vec1 = E_VEC(v1);

				if (v1->f2 + v2->f2 == 4)
					continue;

				if (v1->f2) {
					if (v2->f2) {
						float nvec[3];
						float len1 = VecLength(vec1);
						float len2 = VecLength(vec2);
						float lenn;
						/* for v2 if not selected */
						if (v2->f2 != 2) {
							VecSubf(nvec, v2->co, E_NEAR(v1)->co);
							lenn = VecLength(nvec);
							if (lenn - len1 > 0.00001f && len2 - lenn > 0.00001f) {
								VECCOPY(vec2, nvec);
								E_NEAR(v2) = E_NEAR(v1);
								done = 1;
							}
							else if (len2 - len1 > 0.00001f && len1 - lenn > 0.00001f) {
								VECCOPY(vec2, vec1);
								E_NEAR(v2) = E_NEAR(v1);
								done = 1;
							}
						}
						/* for v1 if not selected */
						if (v1->f2 != 2) {
							VecSubf(nvec, v1->co, E_NEAR(v2)->co);
							lenn = VecLength(nvec);
							if (lenn - len2 > 0.00001f && len1 - lenn > 0.00001f) {
								VECCOPY(vec1, nvec);
								E_NEAR(v1) = E_NEAR(v2);
								done = 1;
							}
							else if (len1 - len2 > 0.00001f && len2 - lenn > 0.00001f) {
								VECCOPY(vec1, vec2);
								E_NEAR(v1) = E_NEAR(v2);
								done = 1;
							}
						}
					}
					else {
						v2->f2 = 1;
						VecSubf(vec2, v2->co, E_NEAR(v1)->co);
						if (VecLength(vec1) - VecLength(vec2) > 0.00001f) {
							VECCOPY(vec2, vec1);
						}
						E_NEAR(v2) = E_NEAR(v1);
						done = 1;
					}
				}
				else if (v2->f2) {
					v1->f2 = 1;
					VecSubf(vec1, v1->co, E_NEAR(v2)->co);
					if (VecLength(vec2) - VecLength(vec1) > 0.00001f) {
						VECCOPY(vec1, vec2);
					}
					E_NEAR(v1) = E_NEAR(v2);
					done = 1;
				}
			}
		}
	}
}


static void VertsToTransData(TransData *td, EditVert *eve)
{
	td->flag = 0;
	td->loc = eve->co;
	VECCOPY(td->center, td->loc);
	VECCOPY(td->iloc, td->loc);

	// Setting normals
	VECCOPY(td->axismtx[2], eve->no);
	td->axismtx[0][0]		=
		td->axismtx[0][1]	=
		td->axismtx[0][2]	=
		td->axismtx[1][0]	=
		td->axismtx[1][1]	=
		td->axismtx[1][2]	= 0.0f;

	td->ext = NULL;
	td->tdi = NULL;
	td->val = NULL;
}

static void createTransEditVerts(TransInfo *t)
{
	TransData *tob = NULL;
	EditMesh *em = G.editMesh;
	EditVert *eve;
	EditVert **nears = NULL;
	float *vectors = NULL;
	float mtx[3][3], smtx[3][3];
	int count=0, countsel=0;
	int propmode = t->flag & T_PROP_EDIT;
		
	// transform now requires awareness for select mode, so we tag the f1 flags in verts
	if(G.scene->selectmode & SCE_SELECT_VERTEX) {
		for(eve= em->verts.first; eve; eve= eve->next) {
			if(eve->h==0 && (eve->f & SELECT)) 
				eve->f1= SELECT;
			else
				eve->f1= 0;
		}
	}
	else if(G.scene->selectmode & SCE_SELECT_EDGE) {
		EditEdge *eed;
		for(eve= em->verts.first; eve; eve= eve->next) eve->f1= 0;
		for(eed= em->edges.first; eed; eed= eed->next) {
			if(eed->h==0 && (eed->f & SELECT))
				eed->v1->f1= eed->v2->f1= SELECT;
		}
	}
	else {
		EditFace *efa;
		for(eve= em->verts.first; eve; eve= eve->next) eve->f1= 0;
		for(efa= em->faces.first; efa; efa= efa->next) {
			if(efa->h==0 && (efa->f & SELECT)) {
				efa->v1->f1= efa->v2->f1= efa->v3->f1= SELECT;
				if(efa->v4) efa->v4->f1= SELECT;
			}
		}
	}
	
	/* now we can count */
	for(eve= em->verts.first; eve; eve= eve->next) {
		if(eve->h==0) {
			if(eve->f1) countsel++;
			if(propmode) count++;
		}
	}
	
 	/* note: in prop mode we need at least 1 selected */
	if (countsel==0) return;
	
	if(propmode) {
		t->total = count; 
	
		/* allocating scratch arrays */
		vectors = (float *)MEM_mallocN(t->total * 3 * sizeof(float), "scratch vectors");
		nears = (EditVert**)MEM_mallocN(t->total * sizeof(EditVert*), "scratch nears");
	}
	else t->total = countsel;
	tob= t->data= MEM_mallocN(t->total*sizeof(TransData), "TransObData(Mesh EditMode)");
	
	Mat3CpyMat4(mtx, G.obedit->obmat);
	Mat3Inv(smtx, mtx);

	if(propmode) editmesh_set_connectivity_distance(t->total, vectors, nears);
	
	for (eve=em->verts.first; eve; eve=eve->next) {
		if(eve->h==0) {
			if(propmode || eve->f1) {
				VertsToTransData(tob, eve);

				if(eve->f1) tob->flag |= TD_SELECTED;
				if(propmode) {
					if (eve->f2) {
						float vec[3];
						VECCOPY(vec, E_VEC(eve));
						Mat3MulVecfl(mtx, vec);
						tob->dist= VecLength(vec);
					}
					else {
						tob->flag |= TD_NOTCONNECTED;
						tob->dist = MAXFLOAT;
					}
				}
				
				Mat3CpyMat3(tob->smtx, smtx);
				Mat3CpyMat3(tob->mtx, mtx);

				tob++;
			}
		}	
	}
	if (propmode) {
		MEM_freeN(vectors);
		MEM_freeN(nears);
	}

}

/* **************** IpoKey stuff, for Object TransData ********** */

/* storage of bezier triple. thats why -3 and +3! */
static void set_tdi_old(float *old, float *poin)
{
	old[0]= *(poin);
	old[3]= *(poin-3);
	old[6]= *(poin+3);
}

/* while transforming */
void add_tdi_poin(float *poin, float *old, float delta)
{
	if(poin) {
		poin[0]= old[0]+delta;
		poin[-3]= old[3]+delta;
		poin[3]= old[6]+delta;
	}
}

/* fill ipokey transdata with old vals and pointers */
static void ipokey_to_transdata(IpoKey *ik, TransData *td)
{
	extern int ob_ar[];		// blenkernel ipo.c
	TransDataIpokey *tdi= td->tdi;
	BezTriple *bezt;
	int a, delta= 0;
	
	td->val= NULL;	// is read on ESC
	
	for(a=0; a<OB_TOTIPO; a++) {
		if(ik->data[a]) {
			bezt= ik->data[a];
			
			switch( ob_ar[a] ) {
				case OB_LOC_X:
				case OB_DLOC_X:
					tdi->locx= &(bezt->vec[1][1]); break;
				case OB_LOC_Y:
				case OB_DLOC_Y:
					tdi->locy= &(bezt->vec[1][1]); break;
				case OB_LOC_Z:
				case OB_DLOC_Z:
					tdi->locz= &(bezt->vec[1][1]); break;
					
				case OB_DROT_X:
					delta= 1;
				case OB_ROT_X:
					tdi->rotx= &(bezt->vec[1][1]); break;
				case OB_DROT_Y:
					delta= 1;
				case OB_ROT_Y:
					tdi->roty= &(bezt->vec[1][1]); break;
				case OB_DROT_Z:
					delta= 1;
				case OB_ROT_Z:
					tdi->rotz= &(bezt->vec[1][1]); break;
					
				case OB_SIZE_X:
				case OB_DSIZE_X:
					tdi->sizex= &(bezt->vec[1][1]); break;
				case OB_SIZE_Y:
				case OB_DSIZE_Y:
					tdi->sizey= &(bezt->vec[1][1]); break;
				case OB_SIZE_Z:
				case OB_DSIZE_Z:
					tdi->sizez= &(bezt->vec[1][1]); break;		
			}	
		}
	}
	
	/* oldvals for e.g. undo */
	if(tdi->locx) set_tdi_old(tdi->oldloc, tdi->locx);
	if(tdi->locy) set_tdi_old(tdi->oldloc+1, tdi->locy);
	if(tdi->locz) set_tdi_old(tdi->oldloc+2, tdi->locz);
	
	/* remember, for mapping curves ('1'=10 degrees)  */
	if(tdi->rotx) set_tdi_old(tdi->oldrot, tdi->rotx);
	if(tdi->roty) set_tdi_old(tdi->oldrot+1, tdi->roty);
	if(tdi->rotz) set_tdi_old(tdi->oldrot+2, tdi->rotz);
	
	/* this is not allowed to be dsize! */
	if(tdi->sizex) set_tdi_old(tdi->oldsize, tdi->sizex);
	if(tdi->sizey) set_tdi_old(tdi->oldsize+1, tdi->sizey);
	if(tdi->sizez) set_tdi_old(tdi->oldsize+2, tdi->sizez);
	
	tdi->flag= TOB_IPO;
	if(delta) tdi->flag |= TOB_IPODROT;
}


/* *************************** Object Transform data ******************* */

static void ObjectToTransData(TransData *td, Object *ob) 
{
	float obmtx[3][3];
	Object *tr;
	void *cfirst, *clast;

	/* set axismtx BEFORE clearing constraints to have the real orientation */
	Mat3CpyMat4(td->axismtx, ob->obmat);
	Mat3Ortho(td->axismtx);

	/* then why are constraints and track disabled here? 
		they dont alter loc/rot/size itself (ton) */
	cfirst = ob->constraints.first;
	clast = ob->constraints.last;
	ob->constraints.first=ob->constraints.last=NULL;

	tr= ob->track;
	ob->track= NULL;

	where_is_object(ob);

	ob->track= tr;

	ob->constraints.first = cfirst;
	ob->constraints.last = clast;

	td->ob = ob;

	td->loc = ob->loc;
	VECCOPY(td->iloc, td->loc);
	
	td->ext->rot = ob->rot;
	VECCOPY(td->ext->irot, ob->rot);
	VECCOPY(td->ext->drot, ob->drot);
	
	td->ext->size = ob->size;
	VECCOPY(td->ext->isize, ob->size);
	VECCOPY(td->ext->dsize, ob->dsize);

	VECCOPY(td->center, ob->obmat[3]);

	if (ob->parent)
	{
		float totmat[3][3], obinv[3][3];
		
		/* we calculate smtx without obmat: so a parmat */
		object_to_mat3(ob, obmtx);
		Mat3CpyMat4(totmat, ob->obmat);
		Mat3Inv(obinv, totmat);
		Mat3MulMat3(td->smtx, obmtx, obinv);
		Mat3Inv(td->mtx, td->smtx);
	}
	else
	{
		Mat3One(td->smtx);
		Mat3One(td->mtx);
	}
}


/* sets flags in Bases to define whether they take part in transform */
/* it deselects Bases, so we have to call the clear function always after */
static void set_trans_object_base_flags(TransInfo *t)
{
	/*
	 if Base selected and has parent selected:
	 base->flag= BA_WAS_SEL
	 */
	Base *base;
	
	/* makes sure base flags and object flags are identical */
	copy_baseflags();
	
	for (base= FIRSTBASE; base; base= base->next) {
		base->flag &= ~BA_WAS_SEL;
		
		if(TESTBASELIB(base)) {
			Object *ob= base->object;
			Object *parsel= ob->parent;
			
			/* if parent selected, deselect */
			while(parsel) {
				if(parsel->flag & SELECT) break;
				parsel= parsel->parent;
			}
			
			if(parsel) {
				base->flag &= ~SELECT;
				base->flag |= BA_WAS_SEL;
			}
			/* used for flush, depgraph will change recalcs if needed :) */
			ob->recalc |= OB_RECALC_OB;
		}
	}
	/* all recalc flags get flushed */
	DAG_scene_flush_update(G.scene);
	
	/* and we store them temporal in base (only used for transform code) */
	/* this because after doing updates, the object->recalc is cleared */
	for (base= FIRSTBASE; base; base= base->next) {
		if(base->object->recalc & OB_RECALC_OB)
			base->flag |= BA_HAS_RECALC_OB;
		if(base->object->recalc & OB_RECALC_DATA)
			base->flag |= BA_HAS_RECALC_DATA;
	}
}

void clear_trans_object_base_flags(void)
{
	Base *base;
	
	base= FIRSTBASE;
	while(base) {
		if(base->flag & BA_WAS_SEL) base->flag |= SELECT;
		base->flag &= ~(BA_WAS_SEL|BA_HAS_RECALC_OB|BA_HAS_RECALC_DATA|BA_DO_IPO);
		
		base = base->next;
	}
}

/* inserting keys, refresh ipo-keys, softbody, redraw events... (ton) */
void special_aftertrans_update(char mode, int flip, short cancelled)
{
	Object *ob;
	Base *base;
	int redrawipo=0;
	
	if (G.obpose){
		bArmature *arm= G.obpose->data;
		bAction	*act;
		bPose	*pose;
		bPoseChannel *pchan;

		arm->flag &= ~ARM_NO_ACTION;
		
		if ((G.flags & G_RECORDKEYS) && !cancelled){
			act=G.obpose->action;
			pose=G.obpose->pose;
			
			if (!act)
				act=G.obpose->action=add_empty_action();
			
			set_pose_keys(G.obpose);  // sets chan->flag to POSE_KEY if bone selected
			for (pchan=pose->chanbase.first; pchan; pchan=pchan->next){
				if (pchan->flag & POSE_KEY){
					
					set_action_key(act, pchan, AC_QUAT_X, 1);
					set_action_key(act, pchan, AC_QUAT_Y, 1);
					set_action_key(act, pchan, AC_QUAT_Z, 1);
					set_action_key(act, pchan, AC_QUAT_W, 1);
				
					set_action_key(act, pchan, AC_SIZE_X, 1);
					set_action_key(act, pchan, AC_SIZE_Y, 1);
					set_action_key(act, pchan, AC_SIZE_Z, 1);
				
					set_action_key(act, pchan, AC_LOC_X, 1);
					set_action_key(act, pchan, AC_LOC_Y, 1);
					set_action_key(act, pchan, AC_LOC_Z, 1);
				}
			}
			
			remake_action_ipos (act);
			allspace(REMAKEIPO, 0);
			allqueue(REDRAWACTION, 0);
			allqueue(REDRAWIPO, 0);
			allqueue(REDRAWNLA, 0);
			/* do not call this always, we dont want actions to update, for inserting keys */
			DAG_object_flush_update(G.scene, G.obpose, OB_RECALC_DATA);
		}
		else if(cancelled)	/* but if cancelled we do the update */
			DAG_object_flush_update(G.scene, G.obpose, OB_RECALC_DATA);

	}
	else {
		base= FIRSTBASE;
		while(base) {	
			
			if(base->flag & BA_DO_IPO) redrawipo= 1;
			ob= base->object;
						
			if(ob->softflag & OB_SB_ENABLE) sbObjectReset(ob);
			
			/* Set autokey if necessary */
			if ((G.flags & G_RECORDKEYS) && (!cancelled) && (base->flag & SELECT)){
			
				insertkey(&base->object->id, OB_ROT_X);
				insertkey(&base->object->id, OB_ROT_Y);
				insertkey(&base->object->id, OB_ROT_Z);
			
				insertkey(&base->object->id, OB_LOC_X);
				insertkey(&base->object->id, OB_LOC_Y);
				insertkey(&base->object->id, OB_LOC_Z);
			
				insertkey(&base->object->id, OB_SIZE_X);
				insertkey(&base->object->id, OB_SIZE_Y);
				insertkey(&base->object->id, OB_SIZE_Z);
				
				remake_object_ipos (ob);
				allqueue(REDRAWIPO, 0);
				allspace(REMAKEIPO, 0);
				allqueue(REDRAWVIEW3D, 0);
				allqueue(REDRAWNLA, 0);
			}
			
			base= base->next;
		}
		
	}
	
	if(redrawipo) {
		allqueue(REDRAWNLA, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWIPO, 0);
	}
	
	reset_slowparents();
	
	/* note; should actually only be done for all objects when a lamp is moved... (ton) */
	if(G.vd->drawtype == OB_SHADED) reshadeall_displist();
	
}

static void createTransObject(TransInfo *t)
{
	TransData *td = NULL;
	TransDataExtension *tx;
	Object *ob;
	Base *base;
	IpoKey *ik;
	ListBase elems;
	
	set_trans_object_base_flags(t);

	{
		/* this has to be done, or else constraints on armature
		 * bones that point to objects/bones that are outside
		 * of the armature don't work outside of posemode 
		 * (and yes, I know it's confusing ...).
		 */
		//figure_pose_updating();
	}
	
	/* count */	
	for(base= FIRSTBASE; base; base= base->next) {
		if TESTBASELIB(base) {
			ob= base->object;
			
			/* store ipo keys? */
			if(ob->ipo && ob->ipo->showkey && (ob->ipoflag & OB_DRAWKEY)) {
				elems.first= elems.last= NULL;
				make_ipokey_transform(ob, &elems, 1); /* '1' only selected keys */
				
				pushdata(&elems, sizeof(ListBase));
				
				for(ik= elems.first; ik; ik= ik->next) t->total++;

				if(elems.first==NULL) t->total++;
			}
			else {
				t->total++;
			}
		}
	}

	if(!t->total) {
		/* clear here, main transform function escapes too */
		clear_trans_object_base_flags();
		return;
	}
	
	td = t->data = MEM_callocN(t->total*sizeof(TransData), "TransOb");
	tx = t->ext = MEM_callocN(t->total*sizeof(TransDataExtension), "TransObExtension");

	for(base= FIRSTBASE; base; base= base->next) {
		if TESTBASELIB(base) {
			ob= base->object;
			
			td->flag= TD_SELECTED;
			td->ext = tx;

			/* store ipo keys? */
			if(ob->ipo && ob->ipo->showkey && (ob->ipoflag & OB_DRAWKEY)) {
				
				popfirst(&elems);	// bring back pushed listbase
				
				if(elems.first) {
					float cfraont;
					int ipoflag;
					
					base->flag |= BA_DO_IPO+BA_WAS_SEL;
					base->flag &= ~SELECT;
					
					cfraont= CFRA;
					set_no_parent_ipo(1);
					ipoflag= ob->ipoflag;
					ob->ipoflag &= ~OB_OFFS_OB;
					
					pushdata(ob->loc, 7*3*4); // tsk! tsk!
					
					for(ik= elems.first; ik; ik= ik->next) {
						
						/* weak... this doesn't correct for floating values, giving small errors */
						CFRA= (short)(ik->val/G.scene->r.framelen);
						
						do_ob_ipo(ob);
						ObjectToTransData(td, ob);	// does where_is_object()
						
						td->flag= TD_SELECTED;
						
						td->tdi= MEM_callocN(sizeof(TransDataIpokey), "TransDataIpokey");
						/* also does tdi->flag and oldvals, needs to be after ob_to_transob()! */
						ipokey_to_transdata(ik, td);
						
						td++;
						tx++;
						if(ik->next) td->ext= tx;	// prevent corrupting mem!
					}
					free_ipokey(&elems);
					
					poplast(ob->loc);
					set_no_parent_ipo(0);
					
					CFRA= (short)cfraont;
					ob->ipoflag= ipoflag;
					
					where_is_object(ob);	// restore 
				}
				else {
					ObjectToTransData(td, ob);
					td->tdi = NULL;
					td->val = NULL;
					td++;
					tx++;
				}
			}
			else {
				ObjectToTransData(td, ob);
				td->tdi = NULL;
				td->val = NULL;
				td++;
				tx++;
			}
		}
	}
}

void createTransData(TransInfo *t) 
{
	if (t->context == CTX_TEXTURE) {
		t->flag |= T_TEXTURE;
		createTransTexspace(t);
	}
	else if (t->context == CTX_EDGE) {
		t->ext = NULL;
		t->flag |= T_EDIT;
		createTransEdge(t);
		if(t->data && t->flag & T_PROP_EDIT) {
			sort_trans_data(t);	// makes selected become first in array
			set_prop_dist(t, 1);
			sort_trans_data_dist(t);
		}
	}
	else if (G.obpose) {
		t->flag |= T_POSE;
		createTransPose(t);
	}
	else if (G.obedit) {
		t->ext = NULL;
		if (G.obedit->type == OB_MESH) {
			if(t->mode==TFM_SHRINKFATTEN && (t->context & CTX_NO_NOR_RECALC)==0)
				vertexnormals(0);
			createTransEditVerts(t);	
   		}
		else if ELEM(G.obedit->type, OB_CURVE, OB_SURF) {
			createTransCurveVerts(t);
		}
		else if (G.obedit->type==OB_LATTICE) {
			createTransLatticeVerts(t);
		}
		else if (G.obedit->type==OB_MBALL) {
			createTransMBallVerts(t);
		}
		else if (G.obedit->type==OB_ARMATURE) {
			createTransArmatureVerts(t);
  		}					  		
		else {
			printf("not done yet! only have mesh surface curve\n");
		}

		if(t->data && t->flag & T_PROP_EDIT) {
			if (ELEM(G.obedit->type, OB_CURVE, OB_MESH)) {
				sort_trans_data(t);	// makes selected become first in array
				set_prop_dist(t, 0);
				sort_trans_data_dist(t);
			}
			else {
				sort_trans_data(t);	// makes selected become first in array
				set_prop_dist(t, 1);
				sort_trans_data_dist(t);
			}
		}
		t->flag |= T_EDIT;
	}
	else {
		createTransObject(t);
		t->flag |= T_OBJECT;
	}

	if((t->flag & T_OBJECT) && G.vd->camera==OBACT && G.vd->persp>1) {
		t->flag |= T_CAMERA;
	}
}

