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
 * editarmature.c: Interface for creating and posing armature objects
 */

#include <ctype.h>
#include <stdlib.h>
#include <string.h>
#include <math.h> 

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "BMF_Api.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_ID.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_view3d_types.h"
#include "DNA_modifier_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_object.h"
#include "BKE_subsurf.h"
#include "BKE_utildefines.h"
#include "BKE_modifier.h"

#include "BIF_editaction.h"
#include "BIF_editmode_undo.h"
#include "BIF_editdeform.h"
#include "BIF_editarmature.h"
#include "BIF_editconstraint.h"
#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_interface.h"
#include "BIF_poseobject.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"
#include "BIF_transform.h"

#include "BDR_editobject.h"
#include "BDR_drawobject.h"

#include "BSE_edit.h"
#include "BSE_view.h"
#include "BSE_trans_types.h"

#include "PIL_time.h"

#include "mydevice.h"
#include "blendef.h"
#include "nla.h"

extern	float centre[3], centroid[3];	/* Originally defined in editobject.c */

/*	Macros	*/
#define TEST_EDITARMATURE {if(G.obedit==0) return; if( (G.vd->lay & G.obedit->lay)==0 ) return;}


/* **************** tools on Editmode Armature **************** */

/* converts Bones to EditBone list, used for tools as well */
static void make_boneList(ListBase* list, ListBase *bones, EditBone *parent)
{
	EditBone	*eBone;
	Bone		*curBone;
	float delta[3];
	float premat[3][3];
	float postmat[3][3];
	float imat[3][3];
	float difmat[3][3];
		
	for (curBone=bones->first; curBone; curBone=curBone->next){
		eBone= MEM_callocN(sizeof(EditBone), "make_editbone");
		
		/*	Copy relevant data from bone to eBone */
		eBone->parent=parent;
		strcpy (eBone->name, curBone->name);
		eBone->flag = curBone->flag;
		
		/* fix selection flags */
		if(eBone->flag & BONE_SELECTED) {
			eBone->flag |= BONE_TIPSEL;
			if(eBone->parent && (eBone->flag & BONE_IK_TOPARENT))
				eBone->parent->flag |= BONE_TIPSEL;
			else 
				eBone->flag |= BONE_ROOTSEL;
		}
		
		VECCOPY(eBone->head, curBone->arm_head);
		VECCOPY(eBone->tail, curBone->arm_tail);		
		
		eBone->roll= 0.0;
		
		/* roll fixing */
		VecSubf (delta, eBone->tail, eBone->head);
		vec_roll_to_mat3(delta, 0.0, postmat);
		
		Mat3CpyMat4(premat, curBone->arm_mat);
		
		Mat3Inv(imat, postmat);
		Mat3MulMat3(difmat, imat, premat);
		
		eBone->roll = atan(difmat[2][0]/difmat[2][2]);
		if (difmat[0][0]<0.0) eBone->roll +=M_PI;
		
		/* rest of stuff copy */
		eBone->length= curBone->length;
		eBone->dist= curBone->dist;
		eBone->weight= curBone->weight;
		eBone->xwidth= curBone->xwidth;
		eBone->zwidth= curBone->zwidth;
		eBone->ease1= curBone->ease1;
		eBone->ease2= curBone->ease2;
		eBone->rad_head= curBone->rad_head;
		eBone->rad_tail= curBone->rad_tail;
		eBone->segments = curBone->segments;		
		eBone->boneclass = curBone->boneclass;
		
		BLI_addtail (list, eBone);
		
		/*	Add children if necessary */
		if (curBone->childbase.first) 
			make_boneList (list, &curBone->childbase, eBone);
	}
}

/* nasty stuff for converting roll in editbones into bones */
/* also sets restposition in armature (arm_mat) */
static void fix_bonelist_roll (ListBase *bonelist, ListBase *editbonelist)
{
	Bone *curBone;
	EditBone *ebone;
	float premat[3][3];
	float postmat[3][3];
	float difmat[3][3];
	float imat[3][3];
	float delta[3];
	
	for (curBone=bonelist->first; curBone; curBone=curBone->next) {
		/* sets local matrix and arm_mat (restpos) */
		where_is_armature_bone(curBone, curBone->parent);
		
		/* Find the associated editbone */
		for (ebone = editbonelist->first; ebone; ebone=ebone->next)
			if ((Bone*)ebone->temp == curBone)
				break;
		
		if (ebone) {
			/* Get the ebone premat */
			VecSubf (delta, ebone->tail, ebone->head);
			vec_roll_to_mat3(delta, ebone->roll, premat);
			
			/* Get the bone postmat */
			Mat3CpyMat4(postmat, curBone->arm_mat);

			Mat3Inv(imat, premat);
			Mat3MulMat3(difmat, imat, postmat);
#if 0
			printf ("Bone %s\n", curBone->name);
			printmatrix4 ("premat", premat);
			printmatrix4 ("postmat", postmat);
			printmatrix4 ("difmat", difmat);
			printf ("Roll = %f\n",  (-atan(difmat[2][0]/difmat[2][2]) * (180.0/M_PI)));
#endif
			curBone->roll = -atan(difmat[2][0]/difmat[2][2]);
			
			if (difmat[0][0]<0.0) curBone->roll +=M_PI;
			
			/* and set restposition again */
			where_is_armature_bone(curBone, curBone->parent);
		}
		fix_bonelist_roll (&curBone->childbase, editbonelist);
	}
}

/* converts the editbones back to the armature */
static void editbones_to_armature (ListBase *list, Object *ob)
{
	bArmature *arm;
	EditBone *eBone;
	Bone	*newBone;
	Object *obt;
	
	arm = get_armature(ob);
	if (!list) return;
	if (!arm) return;
	
	/* armature bones */
	free_bones(arm);
	
	/*	Copy the bones from the editData into the armature */
	for (eBone=list->first;eBone;eBone=eBone->next){
		newBone= MEM_callocN (sizeof(Bone), "bone");
		eBone->temp= newBone;	/* Associate the real Bones with the EditBones */
		
		strcpy (newBone->name, eBone->name);
		memcpy (newBone->head, eBone->head, sizeof(float)*3);
		memcpy (newBone->tail, eBone->tail, sizeof(float)*3);
		newBone->flag= eBone->flag;
		newBone->roll = 0.0f;
		
		newBone->weight = eBone->weight;
		newBone->dist = eBone->dist;
		
		newBone->xwidth = eBone->xwidth;
		newBone->zwidth = eBone->zwidth;
		newBone->ease1= eBone->ease1;
		newBone->ease2= eBone->ease2;
		newBone->rad_head= eBone->rad_head;
		newBone->rad_tail= eBone->rad_tail;
		newBone->segments= eBone->segments;
		newBone->boneclass = eBone->boneclass;
		
	}
	
	/*	Fix parenting in a separate pass to ensure ebone->bone connections
		are valid at this point */
	for (eBone=list->first;eBone;eBone=eBone->next) {
		newBone= (Bone*) eBone->temp;
		if (eBone->parent){
			newBone->parent=(Bone*) eBone->parent->temp;
			BLI_addtail (&newBone->parent->childbase,newBone);
			
			{
				float M_boneRest[3][3];
				float M_parentRest[3][3];
				float iM_parentRest[3][3];
				float	delta[3];
				
				/* Get the parent's  matrix (rotation only) */
				VecSubf (delta, eBone->parent->tail, eBone->parent->head);
				vec_roll_to_mat3(delta, eBone->parent->roll, M_parentRest);
				
				/* Get this bone's  matrix (rotation only) */
				VecSubf (delta, eBone->tail, eBone->head);
				vec_roll_to_mat3(delta, eBone->roll, M_boneRest);
				
				/* Invert the parent matrix */
				Mat3Inv(iM_parentRest, M_parentRest);
				
				/* Get the new head and tail */
				VecSubf (newBone->head, eBone->head, eBone->parent->tail);
				VecSubf (newBone->tail, eBone->tail, eBone->parent->tail);

				Mat3MulVecfl(iM_parentRest, newBone->head);
				Mat3MulVecfl(iM_parentRest, newBone->tail);
			}
		}
		/*	...otherwise add this bone to the armature's bonebase */
		else
			BLI_addtail (&arm->bonebase,newBone);
	}
	
	/* Make a pass through the new armature to fix rolling */
	/* also builds restposition again (like where_is_armature) */
	fix_bonelist_roll (&arm->bonebase, list);
	
	/* so all users of this armature should get rebuilt */
	for(obt= G.main->object.first; obt; obt= obt->id.next) {
		if(obt->data==arm)
			armature_rebuild_pose(obt, arm);
	}
	
	DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
}



void apply_rot_armature (Object *ob, float mat[3][3])
{
	ListBase	list;
	EditBone *ebone;
	bArmature *arm;

	arm = get_armature(ob);

	if (!arm)
		return;

	/* Put the armature into editmode */
	list.first= list.last = NULL;
	make_boneList(&list, &arm->bonebase, NULL);

	/* Do the rotations */
	for (ebone = list.first; ebone; ebone=ebone->next){
		Mat3MulVecfl(mat, ebone->head);
		Mat3MulVecfl(mat, ebone->tail);
	}
	
	/* Turn the list into an armature */
	editbones_to_armature(&list, ob);
	
	/* Free the editbones */
	if (list.first){
		BLI_freelistN (&list);
	}
}

void join_armature(void)
{
	Object	*ob;
	Base	*base, *nextbase;
	ListBase eblist;
	EditBone *curbone, *next;
	float	mat[4][4], imat[4][4];
	
	/*	Ensure we're not in editmode and that the active object is an armature*/
	if(G.obedit) return;
	
	ob= OBACT;
	if(ob->type!=OB_ARMATURE) return;
	
	/*	Make sure the user wants to continue*/
	if(okee("Join selected armatures")==0) return;
	
	/*	Put the active armature into editmode and join the bones from the other one*/

	enter_editmode();
	
	for (base=FIRSTBASE; base; base=nextbase) {
		nextbase = base->next;
		if (TESTBASE(base)){
			if ((base->object->type==OB_ARMATURE) && (base->object!=ob)){
				/* Make a list of editbones */
				eblist.first=eblist.last= NULL;
				make_boneList (&eblist, &((bArmature*)base->object->data)->bonebase,NULL);
				/* Find the difference matrix */
				Mat4Invert(imat, ob->obmat);
				Mat4MulMat4(mat, base->object->obmat, imat);
				
				/* Copy bones from the object to the edit armature */
				for (curbone=eblist.first; curbone; curbone=next){
					next = curbone->next;

					unique_editbone_name (curbone->name);
					
					/* Transform the bone */
					{
						float premat[4][4];
						float postmat[4][4];
						float difmat[4][4];
						float imat[4][4];
						float temp[3][3];
						float delta[3];
						
						/* Get the premat */
						VecSubf (delta, curbone->tail, curbone->head);
						vec_roll_to_mat3(delta, curbone->roll, temp);
						
						Mat4MulMat34 (premat, temp, mat);
						
						Mat4MulVecfl(mat, curbone->head);
						Mat4MulVecfl(mat, curbone->tail);
						
						/* Get the postmat */
						VecSubf (delta, curbone->tail, curbone->head);
						vec_roll_to_mat3(delta, curbone->roll, temp);
						Mat4CpyMat3(postmat, temp);
						
						/* Find the roll */
						Mat4Invert (imat, premat);
						Mat4MulMat4 (difmat, postmat, imat);
						
						curbone->roll -=atan(difmat[2][0]/difmat[2][2]);
						
						if (difmat[0][0]<0)
							curbone->roll +=M_PI;
						
					}
					BLI_remlink(&eblist, curbone);
					BLI_addtail(&G.edbo, curbone);
				}
				
				free_and_unlink_base(base);
			}
		}
	}
	
	DAG_scene_sort(G.scene);	// because we removed object(s)
	
	exit_editmode(1);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);

}

/* **************** END tools on Editmode Armature **************** */
/* **************** PoseMode & EditMode *************************** */

/* only for opengl selection indices */
Bone *get_indexed_bone (Object *ob, int index)
{
	bPoseChannel *pchan;
	int a= 0;
	
	if(ob->pose==NULL) return NULL;
	index>>=16;		// bone selection codes use left 2 bytes
	
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next, a++) {
		if(a==index) return pchan->bone;
	}
	return NULL;
}

/* See if there are any selected bones in this buffer */
static void *get_bone_from_selectbuffer(Base *base, unsigned int *buffer, short hits, short findunsel)
{
	Object *ob= base->object;
	Bone *bone;
	EditBone *ebone;
	void *firstunSel=NULL, *firstSel=NULL, *data;
	unsigned int hitresult;
	short i, takeNext=0, sel;
	
	for (i=0; i< hits; i++){
		hitresult = buffer[3+(i*4)];
		
		if (!(hitresult & BONESEL_NOSEL)) {	// -1
			if(hitresult & BONESEL_ANY) {	// to avoid including objects in selection
				
				hitresult &= ~(BONESEL_ANY);
				/* Determine what the current bone is */
				if (G.obedit==NULL) {
					/* no singular posemode, so check for correct object */
					if(base->selcol == (hitresult & 0xFFFF)) {
						bone = get_indexed_bone(ob, hitresult);

						if (findunsel)
							sel = (bone->flag & BONE_SELECTED);
						else
							sel = !(bone->flag & BONE_SELECTED);
						
						data = bone;
					}
					else {
						data= NULL;
						sel= 0;
					}
				}
				else{
					ebone = BLI_findlink(&G.edbo, hitresult);
					if (findunsel)
						sel = (ebone->flag & BONE_SELECTED);
					else
						sel = !(ebone->flag & BONE_SELECTED);
					
					data = ebone;
				}
				
				if(data) {
					if (sel) {
						if(!firstSel) firstSel= data;
						takeNext=1;
					}
					else {
						if (!firstunSel)
							firstunSel=data;
						if (takeNext)
							return data;
					}
				}
			}
		}
	}
	
	if (firstunSel)
		return firstunSel;
	else 
		return firstSel;
}

/* used by posemode as well editmode */
static void *get_nearest_bone (short findunsel)
{
	unsigned int buffer[MAXPICKBUF];
	short hits;
	
	persp(PERSP_VIEW);
	
	glInitNames();
	hits= view3d_opengl_select(buffer, MAXPICKBUF, 0, 0, 0, 0);

	if (hits)
		return get_bone_from_selectbuffer(BASACT, buffer, hits, findunsel);
	
	return NULL;
}


/* **************** END PoseMode & EditMode *************************** */
/* **************** Posemode stuff ********************** */

static int select_bonechildren_by_name (Bone *bone, char *name, int select)
{
	Bone *curBone;

	if (!strcmp (bone->name, name)){
		if (select)
			bone->flag |= BONE_SELECTED;
		else
			bone->flag &= ~(BONE_SELECTED|BONE_ACTIVE);
		return 1;
	}

	for (curBone=bone->childbase.first; curBone; curBone=curBone->next){
		if (select_bonechildren_by_name (curBone, name, select))
			return 1;
	}

	return 0;
}

/* called in editaction.c */
void select_bone_by_name (bArmature *arm, char *name, int select)
{
	Bone *bone;
	
	if (!arm)
		return;
	
	for (bone=arm->bonebase.first; bone; bone=bone->next)
		if (select_bonechildren_by_name (bone, name, select))
			break;
}

static void selectconnected_posebonechildren (Object *ob, Bone *bone)
{
	Bone *curBone;
	
	if (!(bone->flag & BONE_IK_TOPARENT))
		return;
	
	select_actionchannel_by_name (ob->action, bone->name, !(G.qual & LR_SHIFTKEY));
	
	if (G.qual & LR_SHIFTKEY)
		bone->flag &= ~BONE_SELECTED;
	else
		bone->flag |= BONE_SELECTED;
	
	for (curBone=bone->childbase.first; curBone; curBone=curBone->next){
		selectconnected_posebonechildren (ob, curBone);
	}
}

/* within active object context */
void selectconnected_posearmature(void)
{
	Bone *bone, *curBone, *next;
	Object *ob= OBACT;
	
	if(!ob || !ob->pose) return;
	
	if (G.qual & LR_SHIFTKEY)
		bone= get_nearest_bone(0);
	else
		bone = get_nearest_bone(1);
	
	if (!bone)
		return;
	
	/* Select parents */
	for (curBone=bone; curBone; curBone=next){
		select_actionchannel_by_name (ob->action, curBone->name, !(G.qual & LR_SHIFTKEY));
		if (G.qual & LR_SHIFTKEY)
			curBone->flag &= ~BONE_SELECTED;
		else
			curBone->flag |= BONE_SELECTED;
		
		if (curBone->flag & BONE_IK_TOPARENT)
			next=curBone->parent;
		else
			next=NULL;
	}
	
	/* Select children */
	for (curBone=bone->childbase.first; curBone; curBone=next){
		selectconnected_posebonechildren (ob, curBone);
	}
	
	countall(); // flushes selection!

	allqueue (REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue (REDRAWACTION, 0);
	allqueue(REDRAWOOPS, 0);
	BIF_undo_push("Select connected");

}

static int count_bonechildren (Bone *bone, int incount, int flagmask, int allbones){
	
	Bone	*curBone;
	
	if (!bone)
		return incount;
	
	if (bone->flag & flagmask || flagmask == 0xFFFFFFFF){
		incount++;
		if (!allbones)
			return incount;
	}
	
	for (curBone=bone->childbase.first; curBone; curBone=curBone->next){
		incount=count_bonechildren (curBone, incount, flagmask, allbones);
	}
	
	return incount;
}

static int	count_bones (bArmature *arm, int flagmask, int allbones)
{
	int	count=0;
	Bone	*curBone;
	
	if (!arm)
		return 0;
	
	for (curBone=arm->bonebase.first; curBone; curBone=curBone->next){
		count = count_bonechildren (curBone, count, flagmask, allbones);
	}
	
	return count;
	
}

/* **************** END Posemode stuff ********************** */
/* **************** EditMode stuff ********************** */

/* called in space.c */
void selectconnected_armature(void)
{
	EditBone *bone, *curBone, *next;

	if (G.qual & LR_SHIFTKEY)
		bone= get_nearest_bone(0);
	else
		bone= get_nearest_bone(1);

	if (!bone)
		return;

	/* Select parents */
	for (curBone=bone; curBone; curBone=next){
		if (G.qual & LR_SHIFTKEY){
			curBone->flag &= ~(BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL);
		}
		else{
			curBone->flag |= (BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL);
		}

		if (curBone->flag & BONE_IK_TOPARENT)
			next=curBone->parent;
		else
			next=NULL;
	}

	/* Select children */
	while (bone){
		for (curBone=G.edbo.first; curBone; curBone=next){
			next = curBone->next;
			if (curBone->parent == bone){
				if (curBone->flag & BONE_IK_TOPARENT){
					if (G.qual & LR_SHIFTKEY)
						curBone->flag &= ~(BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL);
					else
						curBone->flag |= (BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL);
					bone=curBone;
					break;
				}
				else{ 
					bone=NULL;
					break;
				}
			}
		}
		if (!curBone)
			bone=NULL;

	}

	countall(); // flushes selection!

	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWOOPS, 0);
	
	BIF_undo_push("Select connected");

}

/* does bones and points */
/* note that BONE ROOT only gets drawn for root bones (or without IK) */
static EditBone * get_nearest_editbonepoint (int findunsel, int *selmask)
{
	EditBone *ebone;
	unsigned int buffer[MAXPICKBUF];
	unsigned int hitresult, besthitresult=BONESEL_NOSEL;
	int i, mindep= 4;
	short hits, mval[2];

	persp(PERSP_VIEW);

	glInitNames();
	
	getmouseco_areawin(mval);
	hits= view3d_opengl_select(buffer, MAXPICKBUF, mval[0]-5, mval[1]-5, mval[0]+5, mval[1]+5);
	if(hits==0)
		hits= view3d_opengl_select(buffer, MAXPICKBUF, mval[0]-12, mval[1]-12, mval[0]+12, mval[1]+12);
		
	/* See if there are any selected bones in this group */
	if (hits) {
		
		if(hits==1) {
			if (!(buffer[3] & BONESEL_NOSEL)) 
				besthitresult= buffer[3];
		}
		else {
			for (i=0; i< hits; i++) {
				hitresult= buffer[3+(i*4)];
				if (!(hitresult & BONESEL_NOSEL)) {
					int dep;
					
					ebone = BLI_findlink(&G.edbo, hitresult & ~BONESEL_ANY);
					
					/* clicks on bone points get advantage */
					if( hitresult & (BONESEL_ROOT|BONESEL_TIP)) {
						/* but also the unselected one */
						if(findunsel) {
							if( (hitresult & BONESEL_ROOT) && (ebone->flag & BONE_ROOTSEL)==0) 
								dep= 1;
							else if( (hitresult & BONESEL_TIP) && (ebone->flag & BONE_TIPSEL)==0) 
								dep= 1;
							else 
								dep= 2;
						}
						else dep= 2;
					}
					else {
						/* bone found */
						if(findunsel) {
							if((ebone->flag & BONE_SELECTED)==0)
								dep= 2;
							else
								dep= 3;
						}
						else dep= 3;
					}
					if(dep < mindep) {
						mindep= dep;
						besthitresult= hitresult;
					}
				}
			}
		}
		
		if (!(besthitresult & BONESEL_NOSEL)) {
			
			ebone= BLI_findlink(&G.edbo, besthitresult & ~BONESEL_ANY);
			
			*selmask = 0;
			if (besthitresult & BONESEL_ROOT)
				*selmask |= BONE_ROOTSEL;
			if (besthitresult & BONESEL_TIP)
				*selmask |= BONE_TIPSEL;
			if (besthitresult & BONESEL_BONE)
				*selmask |= BONE_SELECTED;
			return ebone;
		}
	}
	*selmask = 0;
	return NULL;
}

static void delete_bone(EditBone* exBone)
{
	EditBone	*curBone;
	
	/*	Find any bones that refer to this bone	*/
	for (curBone=G.edbo.first;curBone;curBone=curBone->next){
		if (curBone->parent==exBone){
			curBone->parent=exBone->parent;
			curBone->flag &= ~BONE_IK_TOPARENT;
		}
	}
	
	BLI_freelinkN (&G.edbo,exBone);
}

static EditBone *editbone_name_exists (char *name);	// proto for below

/* only editmode! */
void delete_armature(void)
{
	EditBone	*curBone, *next;
	bConstraint *con;
	
	TEST_EDITARMATURE;
	if(okee("Erase selected bone(s)")==0) return;
	
	/*  First rase any associated pose channel */
	if (G.obedit->pose){
		bPoseChannel *chan, *next;
		for (chan=G.obedit->pose->chanbase.first; chan; chan=next) {
			next= chan->next;
			curBone = editbone_name_exists (chan->name);
			
			if (curBone && (curBone->flag&BONE_SELECTED)) {
				free_constraints(&chan->constraints);
				BLI_freelinkN (&G.obedit->pose->chanbase, chan);
			}
			else {
				for(con= chan->constraints.first; con; con= con->next) {
					char *subtarget = get_con_subtarget_name(con, G.obedit);
					if (subtarget) {
						curBone = editbone_name_exists (subtarget);
						if (curBone && (curBone->flag&BONE_SELECTED)) {
							con->flag |= CONSTRAINT_DISABLE;
							subtarget[0]= 0;
						}
					}
				}
			}
		}
	}
	
	
	for (curBone=G.edbo.first;curBone;curBone=next){
		next=curBone->next;
		if (curBone->flag&BONE_SELECTED)
			delete_bone(curBone);
	}
	
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWOOPS, 0);
	countall(); // flushes selection!
	
	BIF_undo_push("Delete bone(s)");
}

/* context: editmode armature */
void mouse_armature(void)
{
	EditBone *nearBone = NULL, *ebone;
	int	selmask;

	nearBone= get_nearest_editbonepoint(1, &selmask);
	if (nearBone) {
		
		if (!(G.qual & LR_SHIFTKEY)) {
			deselectall_armature(0);
		}
		
		/* by definition the non-root non-IK bones have no root point drawn,
	       so a root selection needs to be delivered to the parent tip,
	       countall() (bad location) flushes these flags */
		
		if(selmask & BONE_SELECTED) {
			if(nearBone->parent && (nearBone->flag & BONE_IK_TOPARENT)) {
				/* click in a chain */
				if(G.qual & LR_SHIFTKEY) {
					/* hold shift inverts this bone's selection */
					if(nearBone->flag & BONE_SELECTED) {
						/* deselect this bone */
						nearBone->flag &= ~(BONE_TIPSEL|BONE_SELECTED);
						/* only deselect parent tip if it is not selected */
						if(!(nearBone->parent->flag & BONE_SELECTED))
							nearBone->parent->flag &= ~BONE_TIPSEL;
					}
					else {
						/* select this bone */
						nearBone->flag |= BONE_TIPSEL;
						nearBone->parent->flag |= BONE_TIPSEL;
					}
				}
				else {
					/* select this bone */
					nearBone->flag |= BONE_TIPSEL;
					nearBone->parent->flag |= BONE_TIPSEL;
				}
			}
			else {
				if(G.qual & LR_SHIFTKEY) {
					/* hold shift inverts this bone's selection */
					if(nearBone->flag & BONE_SELECTED)
					   nearBone->flag &= ~(BONE_TIPSEL|BONE_ROOTSEL);
					else
						nearBone->flag |= (BONE_TIPSEL|BONE_ROOTSEL);
				}
				else nearBone->flag |= (BONE_TIPSEL|BONE_ROOTSEL);
			}
		}
		else {
			if ((G.qual & LR_SHIFTKEY) && (nearBone->flag & selmask))
				nearBone->flag &= ~selmask;
			else
				nearBone->flag |= selmask;
		}

		countall(); // flushes selection!
		
		if(nearBone) {
			/* then now check for active status */
			for (ebone=G.edbo.first;ebone;ebone=ebone->next) ebone->flag &= ~BONE_ACTIVE;
			if(nearBone->flag & BONE_SELECTED) nearBone->flag |= BONE_ACTIVE;
		}
		
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWBUTSEDIT, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWOOPS, 0);
	}

	rightmouse_transform();
}

void free_editArmature(void)
{
	
	/*	Clear the editbones list */
	if (G.edbo.first){
		BLI_freelistN (&G.edbo);
	}
}

void remake_editArmature(void)
{
	if(okee("Reload original data")==0) return;
	
	make_editArmature();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWBUTSHEAD, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	
//	BIF_undo_push("Delete bone");

}

/* Put object in EditMode */
void make_editArmature(void)
{
	bArmature	*arm;
	
	if (G.obedit==0) return;
	
	free_editArmature();
	
	arm= get_armature(G.obedit);
	if (!arm)
		return;
	
	make_boneList (&G.edbo, &arm->bonebase,NULL);
}

/* put EditMode back in Object */
void load_editArmature(void)
{
	bArmature		*arm;

	arm= get_armature(G.obedit);
	if (!arm) return;
	
	editbones_to_armature(&G.edbo, G.obedit);
}

/* toggle==0: deselect
   toggle==1: swap 
   toggle==2: only active tag
*/
void deselectall_armature(int toggle)
{
	EditBone	*eBone;
	int			sel=1;

	if(toggle==1) {
		/*	Determine if there are any selected bones
			And therefore whether we are selecting or deselecting */
		for (eBone=G.edbo.first;eBone;eBone=eBone->next){
			if (eBone->flag & (BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL)){
				sel=0;
				break;
			}
		}
	}
	else sel= toggle;
	
	/*	Set the flags */
	for (eBone=G.edbo.first;eBone;eBone=eBone->next){
		if (sel==1)
			eBone->flag |= (BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL);
		else if (sel==2)
			eBone->flag &= ~(BONE_ACTIVE);
		else
			eBone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL | BONE_ACTIVE);
	}
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWOOPS, 0);
	
	countall(); // flushes selection!
}

void auto_align_armature(void)
/* Sets the roll value of selected bones so that their zaxes point upwards */
{
	EditBone *ebone;
	float	xaxis[3]={1.0, 0.0, 0.0}, yaxis[3], zaxis[3]={0.0, 0.0, 1.0};
	float	targetmat[3][3], imat[3][3];
	float	curmat[3][3], diffmat[3][3];
	float	delta[3];
	
	for (ebone = G.edbo.first; ebone; ebone=ebone->next){
		if (ebone->flag & BONE_SELECTED){
			/* Find the current bone matrix */
			VecSubf(delta, ebone->tail, ebone->head);
			vec_roll_to_mat3(delta, 0.0, curmat);
			
			/* Make new matrix based on y axis & z-up */
			VECCOPY (yaxis, curmat[1]);
			
			Mat3One(targetmat);
			VECCOPY (targetmat[0], xaxis);
			VECCOPY (targetmat[1], yaxis);
			VECCOPY (targetmat[2], zaxis);
			Mat3Ortho(targetmat);
			
			/* Find the difference between the two matrices */
			Mat3Inv(imat, targetmat);
			Mat3MulMat3(diffmat, imat, curmat);
			
			ebone->roll = atan(diffmat[2][0]/diffmat[2][2]);
			
		}
	}
}

/* **************** undo for armatures ************** */

static void undoBones_to_editBones(void *lbv)
{
	ListBase *lb= lbv;
	EditBone *ebo, *newebo;
	
	BLI_freelistN(&G.edbo);
	
	/* copy  */
	for(ebo= lb->first; ebo; ebo= ebo->next) {
		newebo= MEM_dupallocN(ebo);
		ebo->temp= newebo;
		BLI_addtail(&G.edbo, newebo);
	}
	
	/* set pointers */
	for(newebo= G.edbo.first; newebo; newebo= newebo->next) {
		if(newebo->parent) newebo->parent= newebo->parent->temp;
	}
	/* be sure they dont hang ever */
	for(newebo= G.edbo.first; newebo; newebo= newebo->next) {
		newebo->temp= NULL;
	}
}

static void *editBones_to_undoBones(void)
{
	ListBase *lb;
	EditBone *ebo, *newebo;
	
	lb= MEM_callocN(sizeof(ListBase), "listbase undo");
	
	/* copy  */
	for(ebo= G.edbo.first; ebo; ebo= ebo->next) {
		newebo= MEM_dupallocN(ebo);
		ebo->temp= newebo;
		BLI_addtail(lb, newebo);
	}
	
	/* set pointers */
	for(newebo= lb->first; newebo; newebo= newebo->next) {
		if(newebo->parent) newebo->parent= newebo->parent->temp;
	}
	
	return lb;
}

static void free_undoBones(void *lbv)
{
	ListBase *lb= lbv;
	
	BLI_freelistN(lb);
	MEM_freeN(lb);
}

/* and this is all the undo system needs to know */
void undo_push_armature(char *name)
{
	undo_editmode_push(name, free_undoBones, undoBones_to_editBones, editBones_to_undoBones);
}



/* **************** END EditMode stuff ********************** */
/* *************** Adding stuff in editmode *************** */

/* default bone add, returns it selected, but without tail set */
static EditBone *add_editbone(void)
{
	EditBone *bone= MEM_callocN(sizeof(EditBone), "eBone");
	
	strcpy (bone->name,"Bone");
	unique_editbone_name (bone->name);
	
	BLI_addtail(&G.edbo, bone);
	
	bone->flag |= BONE_TIPSEL;
	bone->weight= 1.0F;
	bone->dist= 0.5F;
	bone->xwidth= 0.1;
	bone->zwidth= 0.1;
	bone->ease1= 1.0;
	bone->ease2= 1.0;
	bone->rad_head= 0.25;
	bone->rad_tail= 0.1;
	bone->segments= 1;
	
	return bone;
}

static void add_primitive_bone(Object *ob)
{
	float		obmat[3][3], curs[3], viewmat[3][3], totmat[3][3], imat[3][3];
	EditBone	*bone;
	
	VECCOPY (curs, give_cursor());	

	/* Get inverse point for head and orientation for tail */
	Mat4Invert(G.obedit->imat, G.obedit->obmat);
	Mat4MulVecfl(G.obedit->imat, curs);

	Mat3CpyMat4(obmat, G.vd->viewmat);
	Mat3CpyMat4(viewmat, G.obedit->obmat);
	Mat3MulMat3(totmat, obmat, viewmat);
	Mat3Inv(imat, totmat);
	
	deselectall_armature(0);
	
	/*	Create a bone	*/
	bone= add_editbone();

	VECCOPY(bone->head, curs);
	VecAddf(bone->tail, bone->head, imat[1]);	// bone with unit length 1
	
}

void add_primitiveArmature(int type)
{
	if(G.scene->id.lib) return;
	
	/* this function also comes from an info window */
	if ELEM(curarea->spacetype, SPACE_VIEW3D, SPACE_INFO); else return;
	if(G.vd==NULL) return;
	
	G.f &= ~(G_VERTEXPAINT+G_FACESELECT+G_TEXTUREPAINT+G_WEIGHTPAINT);
	setcursor_space(SPACE_VIEW3D, CURSOR_STD);

	check_editmode(OB_ARMATURE);
	
	/* If we're not the "obedit", make a new object and enter editmode */
	if(G.obedit==NULL) {
		add_object(OB_ARMATURE);
		base_init_from_view3d(BASACT, G.vd);
		G.obedit= BASACT->object;
		
		where_is_object(G.obedit);
		
		make_editArmature();
		setcursor_space(SPACE_VIEW3D, CURSOR_EDIT);
	}
	
	/* no primitive support yet */
	add_primitive_bone(G.obedit);
	
	countall(); // flushes selection!

	allqueue(REDRAWALL, 0);
	BIF_undo_push("Add primitive");
}

/* the ctrl-click method */
void addvert_armature(void)
{
	EditBone *ebone, *newbone, *partest;
	float *curs, mat[3][3],imat[3][3];
	int to_root= 0;
	
	TEST_EDITARMATURE;
	
	/* find the active or selected bone */
	for (ebone = G.edbo.first; ebone; ebone=ebone->next)
		if(ebone->flag & (BONE_ACTIVE|BONE_TIPSEL)) break;
	
	if(ebone==NULL) {
		for (ebone = G.edbo.first; ebone; ebone=ebone->next)
			if(ebone->flag & (BONE_ACTIVE|BONE_ROOTSEL)) break;
		
		if(ebone==NULL) 
			return;
		to_root= 1;
	}
	
	deselectall_armature(0);
	newbone= add_editbone();
	newbone->flag |= BONE_ACTIVE;
	
	if(to_root) {
		VECCOPY(newbone->head, ebone->head);
		
		newbone->parent= ebone->parent;
	}
	else {
		VECCOPY(newbone->head, ebone->tail);

		
		/* See if there are any ik children of the parent */
		for (partest = G.edbo.first; partest; partest= partest->next){
			if ((partest->parent == ebone) && (partest->flag & BONE_IK_TOPARENT))
				break;
		}
		if(!partest)
			newbone->flag |= BONE_IK_TOPARENT;
		
		newbone->parent= ebone;
	}
	
	curs= give_cursor();
	VECCOPY(newbone->tail, curs);
	VecSubf(newbone->tail, newbone->tail, G.obedit->obmat[3]);
	
	Mat3CpyMat4(mat, G.obedit->obmat);
	Mat3Inv(imat, mat);
	Mat3MulVecfl(imat, newbone->tail);

	newbone->length= VecLenf(newbone->head, newbone->tail);
	newbone->rad_tail= newbone->length*0.1f;
	newbone->dist= newbone->length*0.25f;
	
	countall();
	
	BIF_undo_push("Add Bone");
	allqueue(REDRAWVIEW3D, 0);
	
	while(get_mbut()&R_MOUSE);
}


void adduplicate_armature(void)
{
	EditBone	*eBone = NULL;
	EditBone	*curBone;
	EditBone	*firstDup=NULL;	/*	The beginning of the duplicated bones in the edbo list */
	
	countall(); // flushes selection!
	
	/*	Find the selected bones and duplicate them as needed */
	for (curBone=G.edbo.first; curBone && curBone!=firstDup; curBone=curBone->next){
		if (curBone->flag & BONE_SELECTED){
			
			eBone=MEM_callocN(sizeof(EditBone), "addup_editbone");
			eBone->flag |= BONE_SELECTED;
			
			/*	Copy data from old bone to new bone */
			memcpy (eBone, curBone, sizeof(EditBone));
			
			curBone->temp = eBone;
			eBone->temp = curBone;
			
			unique_editbone_name (eBone->name);
			BLI_addtail (&G.edbo, eBone);
			if (!firstDup)
				firstDup=eBone;
			
			/* Lets duplicate the list of constraits that the
				* current bone has.
				*/
			/* temporal removed (ton) */
		}
	}
	
	if (eBone){
		/*	Fix the head and tail */	
		if (eBone->parent && !eBone->parent->flag & BONE_SELECTED){
			VecSubf (eBone->tail, eBone->tail, eBone->head);
			VecSubf (eBone->head, eBone->head, eBone->head);
		}
	}
	
	/*	Run though the list and fix the pointers */
	for (curBone=G.edbo.first; curBone && curBone!=firstDup; curBone=curBone->next){
		
		if (curBone->flag & BONE_SELECTED){
			eBone=(EditBone*) curBone->temp;
			
			/*	If this bone has no parent,
			Set the duplicate->parent to NULL
			*/
			if (!curBone->parent){
				eBone->parent = NULL;
			}
			/*	If this bone has a parent that IS selected,
				Set the duplicate->parent to the curBone->parent->duplicate
				*/
			else if (curBone->parent->flag & BONE_SELECTED){
				eBone->parent=(EditBone*) curBone->parent->temp;
			}
			/*	If this bone has a parent that IS not selected,
				Set the duplicate->parent to the curBone->parent
				*/
			else {
				eBone->parent=(EditBone*) curBone->parent; 
				eBone->flag &= ~BONE_IK_TOPARENT;
			}
			
			/* Lets try to fix any constraint subtargets that might
				have been duplicated */
			/* temporal removed (ton) */
			
		}
	} 
	
	/*	Deselect the old bones and select the new ones */
	
	for (curBone=G.edbo.first; curBone && curBone!=firstDup; curBone=curBone->next){
		curBone->flag &= ~(BONE_SELECTED | BONE_TIPSEL | BONE_ROOTSEL | BONE_ACTIVE);
	}
	
	BIF_TransformSetUndo("Add Duplicate");
	initTransform(TFM_TRANSLATION, CTX_NO_PET);
	Transform();
	
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWOOPS, 0);
}



/* *************** END Adding stuff in editmode *************** */
/* *************** Tools in editmode *********** */


void hide_selected_armature_bones(void)
{
	EditBone *ebone;
	
	for (ebone = G.edbo.first; ebone; ebone=ebone->next){
		if(ebone->flag & (BONE_SELECTED)) {
			ebone->flag &= ~(BONE_TIPSEL|BONE_SELECTED|BONE_ROOTSEL|BONE_ACTIVE);
			ebone->flag |= BONE_HIDDEN_A;
		}
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
}

void hide_unselected_armature_bones(void)
{
	EditBone *ebone;
	
	for (ebone = G.edbo.first; ebone; ebone=ebone->next){
		if(ebone->flag & (BONE_TIPSEL|BONE_SELECTED|BONE_ROOTSEL));
		else {
			ebone->flag &= ~BONE_ACTIVE;
			ebone->flag |= BONE_HIDDEN_A;
		}
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
}

void show_all_armature_bones(void)
{
	EditBone *ebone;
	
	for (ebone = G.edbo.first; ebone; ebone=ebone->next){
		if(ebone->flag & BONE_HIDDEN_A) {
			ebone->flag |= (BONE_TIPSEL|BONE_SELECTED|BONE_ROOTSEL);
			ebone->flag &= ~BONE_HIDDEN_A;
		}
	}
	countall();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
}



/* the "IK" button in editbuttons */
void attach_bone_to_parent_cb(void *bonev, void *arg2_unused)
{
	EditBone *ebone= bonev;
	attach_bone_to_parent(ebone);
}

void attach_bone_to_parent(EditBone *bone)
{
	EditBone *ebone;

	if (bone->flag & BONE_IK_TOPARENT) {

		/* See if there are any other bones that refer to the same 
		 * parent and disconnect them 
		 */
		for (ebone = G.edbo.first; ebone; ebone=ebone->next){
			if (ebone!=bone){
				if (ebone->parent && (ebone->parent == bone->parent) && 
					(ebone->flag & BONE_IK_TOPARENT))
						ebone->flag &= ~BONE_IK_TOPARENT;
			}
		}

        /* Attach this bone to its parent */
		VECCOPY(bone->head, bone->parent->tail);
	}
}

void make_bone_parent(void)
{
	EditBone *ebone;
	float offset[3];
	short val;
	
	val= pupmenu("Make Parent%t|Connected%x1|Keep Offset%x2");
	
	if(val<1) return;
	
	/* find active */
	for (ebone = G.edbo.first; ebone; ebone=ebone->next)
		if(ebone->flag & BONE_ACTIVE) break;
	if(ebone) {
		EditBone *actbone= ebone, *selbone= NULL;
		
		/* find selected */
		for (ebone = G.edbo.first; ebone; ebone=ebone->next) {
			if(ebone->flag & BONE_SELECTED) {
				if(ebone!=actbone) {
					if(selbone==NULL) selbone= ebone;
					else {
						error("Need one active and one selected bone");
						return;
					}
				}
			}
		}
		if(selbone==NULL) error("Need one active and one selected bone");
		else {
			/* if selbone had a parent we clear parent tip */
			if(selbone->parent && (selbone->flag & BONE_IK_TOPARENT))
			   selbone->parent->flag &= ~(BONE_TIPSEL);
			
			selbone->parent= actbone;
			
			/* in actbone tree we cannot have a loop */
			for(ebone= actbone->parent; ebone; ebone= ebone->parent) {
				if(ebone->parent==selbone) {
					ebone->parent= NULL;
					ebone->flag &= ~BONE_IK_TOPARENT;
				}
			}
			
			if(val==1) {	// connected
				selbone->flag |= BONE_IK_TOPARENT;
				VecSubf(offset, actbone->tail, selbone->head);
				
				VECCOPY(selbone->head, actbone->tail);
				VecAddf(selbone->tail, selbone->tail, offset);
				
				// offset for all its children 
				for (ebone = G.edbo.first; ebone; ebone=ebone->next) {
					EditBone *par;
					for(par= ebone->parent; par; par= par->parent) {
						if(par==selbone) {
							VecAddf(ebone->head, ebone->head, offset);
							VecAddf(ebone->tail, ebone->tail, offset);
							break;
						}
					}
				}
			}
			else {
				selbone->flag &= ~BONE_IK_TOPARENT;
			}
			
			countall(); // checks selection
			allqueue(REDRAWVIEW3D, 0);
			allqueue(REDRAWBUTSEDIT, 0);
			allqueue(REDRAWOOPS, 0);
		}
	}
	return;
}

void clear_bone_parent(void)
{
	EditBone *ebone;
	short val;
	
	val= pupmenu("Clear Parent%t|Clear Parent%x1|Disconnect IK%x2");
	
	if(val<1) return;
	for (ebone = G.edbo.first; ebone; ebone=ebone->next) {
		if(ebone->flag & BONE_SELECTED) {
			if(ebone->parent) {
				/* for nice selection */
				ebone->parent->flag &= ~(BONE_TIPSEL);
				
				if(val==1) ebone->parent= NULL;
				ebone->flag &= ~BONE_IK_TOPARENT;
				
			}
		}
	}
	countall(); // checks selection
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWOOPS, 0);
}
	

static EditBone *editbone_name_exists (char *name)
{
	EditBone	*eBone;
	
	for (eBone=G.edbo.first; eBone; eBone=eBone->next){
		if (!strcmp (name, eBone->name))
			return eBone;
	}
	return NULL;
}

/* note: there's a unique_bone_name() too! */
void unique_editbone_name (char *name)
{
	char		tempname[64];
	int			number;
	char		*dot;
	
	
	if (editbone_name_exists(name)) {
		
		/*	Strip off the suffix, if it's a number */
		number= strlen(name);
		if(number && isdigit(name[number-1])) {
			dot= strrchr(name, '.');	// last occurrance
			if (dot)
				*dot=0;
		}
		
		for (number = 1; number <=999; number++){
			sprintf (tempname, "%s.%03d", name, number);
			if (!editbone_name_exists(tempname)){
				strcpy (name, tempname);
				return;
			}
		}
	}
}

/* context; editmode armature */
/* if forked && mirror-edit: makes two bones with flipped names */
void extrude_armature(int forked)
{
	bArmature *arm= G.obedit->data;
	EditBone *newbone, *ebone, *flipbone, *first=NULL, *partest;
	int a, totbone= 0, do_extrude;
	
	TEST_EDITARMATURE;
	
	/* since we allow root extrude too, we have to make sure selection is OK */
	for (ebone = G.edbo.first; ebone; ebone=ebone->next){
		if(ebone->flag & BONE_ROOTSEL) {
			if(ebone->parent && (ebone->flag & BONE_IK_TOPARENT)) {
				if(ebone->parent->flag & BONE_TIPSEL)
					ebone->flag &= ~BONE_ROOTSEL;
			}
		}
	}
	
	/* Duplicate the necessary bones */
	for (ebone = G.edbo.first; ((ebone) && (ebone!=first)); ebone=ebone->next){
		
		/* we extrude per definition the tip */
		do_extrude= 0;
		if (ebone->flag & (BONE_TIPSEL|BONE_SELECTED))
			do_extrude= 1;
		else if(ebone->flag & BONE_ROOTSEL) {
			/* but, a bone with parent deselected we do the root... */
			if(ebone->parent && (ebone->parent->flag & BONE_TIPSEL));
			else do_extrude= 2;
		}
		
		if (do_extrude) {
			
			/* we re-use code for mirror editing... */
			flipbone= NULL;
			if(arm->flag & ARM_MIRROR_EDIT) {
				flipbone= armature_bone_get_mirrored(ebone);
				if (flipbone) {
					forked= 0;	// we extrude 2 different bones
					if(flipbone->flag & (BONE_TIPSEL|BONE_ROOTSEL|BONE_SELECTED))
						/* don't want this bone to be selected... */
						flipbone->flag &= ~(BONE_TIPSEL|BONE_SELECTED|BONE_ROOTSEL|BONE_ACTIVE);
				}
				if(flipbone==NULL && forked)
					flipbone= ebone;
			}
			
			for(a=0; a<2; a++) {
				if(a==1) {
					if(flipbone==NULL)
						break;
					else {
						SWAP(EditBone *, flipbone, ebone);
					}
				}
				
				totbone++;
				newbone = MEM_callocN(sizeof(EditBone), "extrudebone");
				
				if(do_extrude==1) {
					VECCOPY (newbone->head, ebone->tail);
					VECCOPY (newbone->tail, newbone->head);
					newbone->parent = ebone;
					
					newbone->flag = ebone->flag & BONE_TIPSEL;	// copies it, in case mirrored bone
				}
				else {
					VECCOPY(newbone->head, ebone->head);
					VECCOPY(newbone->tail, ebone->head);
					newbone->parent= ebone->parent;
					
					newbone->flag= BONE_TIPSEL;
				}

				newbone->weight= ebone->weight;
				newbone->dist= ebone->dist;
				newbone->xwidth= ebone->xwidth;
				newbone->zwidth= ebone->zwidth;
				newbone->ease1= ebone->ease1;
				newbone->ease2= ebone->ease2;
				newbone->rad_head= ebone->rad_tail;	// dont copy entire bone...
				newbone->rad_tail= ebone->rad_tail;
				newbone->segments= 1;
				newbone->boneclass= ebone->boneclass;
				
				/* See if there are any ik children of the parent */
				if(do_extrude==1) {
					for (partest = G.edbo.first; partest; partest=partest->next){
						if ((partest->parent == ebone) && (partest->flag & BONE_IK_TOPARENT))
							break;
					}
					
					if (!partest)
						newbone->flag |= BONE_IK_TOPARENT;
				}
				
				strcpy (newbone->name, ebone->name);
				
				if(flipbone && forked) {	// only set if mirror edit
					if(strlen(newbone->name)<30) {
						if(a==0) strcat(newbone->name, "_L");
						else strcat(newbone->name, "_R");
					}
				}
				unique_editbone_name(newbone->name);
				
				/* Add the new bone to the list */
				BLI_addtail(&G.edbo, newbone);
				if (!first)
					first = newbone;
				
				/* restore ebone if we were flipping */
				if(a==1 && flipbone) 
					SWAP(EditBone *, flipbone, ebone);

			}
		}
		
		/* Deselect the old bone */
		ebone->flag &= ~(BONE_TIPSEL|BONE_SELECTED|BONE_ROOTSEL|BONE_ACTIVE);
		
	}
	/* if only one bone, make this one active */
	if(totbone==1 && first) first->flag |= BONE_ACTIVE;
	
	/* Transform the endpoints */
	countall(); // flushes selection!
	BIF_TransformSetUndo("Extrude");
	initTransform(TFM_TRANSLATION, CTX_NO_PET);
	Transform();
	
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWOOPS, 0);
}

/* ***************** Pose tools ********************* */

void clear_armature(Object *ob, char mode)
{
	bPoseChannel *pchan;
	bArmature	*arm;

	arm=get_armature(ob);
	
	if (!arm)
		return;
	
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(pchan->bone && (pchan->bone->flag & BONE_SELECTED)) {
			switch (mode){
				case 'r':
					pchan->quat[1]=pchan->quat[2]=pchan->quat[3]=0.0F; pchan->quat[0]=1.0F;
					break;
				case 'g':
					pchan->loc[0]=pchan->loc[1]=pchan->loc[2]=0.0F;
					break;
				case 's':
					pchan->size[0]=pchan->size[1]=pchan->size[2]=1.0F;
					break;
					
			}
		}
	}
	
	DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
	/* no update for this object, this will execute the action again */
	/* is weak... like for ipo editing which uses ctime now... */
	where_is_pose (ob);
	ob->recalc= 0;
}

/* helper for function below */
static int clear_active_flag(Object *ob, Bone *bone, void *data) 
{
	bone->flag &= ~BONE_ACTIVE;
	return 0;
}


/* called from editview.c, for mode-less pose selection */
int do_pose_selectbuffer(Base *base, unsigned int *buffer, short hits)
{
	Object *ob= base->object;
	Bone *nearBone;
	
	if (!ob || !ob->pose) return 0;

	nearBone= get_bone_from_selectbuffer(base, buffer, hits, 1);

	if (nearBone) {
		if (!(G.qual & LR_SHIFTKEY)){
			deselectall_posearmature(ob, 0);
			nearBone->flag |= (BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL|BONE_ACTIVE);
			select_actionchannel_by_name(ob->action, nearBone->name, 1);
		}
		else {
			if (nearBone->flag & BONE_SELECTED) {
				/* if not active, we make it active */
				if((nearBone->flag & BONE_ACTIVE)==0) {
					bArmature *arm= ob->data;
					bone_looper(ob, arm->bonebase.first, NULL, clear_active_flag);
					
					nearBone->flag |= BONE_ACTIVE;
				}
				else {
					nearBone->flag &= ~(BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL|BONE_ACTIVE);
					select_actionchannel_by_name(ob->action, nearBone->name, 0);
				}
			}
			else{
				bArmature *arm= ob->data;
				bone_looper(ob, arm->bonebase.first, NULL, clear_active_flag);
				
				nearBone->flag |= (BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL|BONE_ACTIVE);
				select_actionchannel_by_name(ob->action, nearBone->name, 1);
			}
		}
		
		/* in weightpaint we select the associated vertex group too */
		if(G.f & G_WEIGHTPAINT) {
			if(nearBone->flag & BONE_ACTIVE) {
				vertexgroup_select_by_name(OBACT, nearBone->name);
				DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
			}
		}
		
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWIPO, 0);		/* To force action/constraint ipo update */
		allqueue(REDRAWBUTSEDIT, 0);
		allqueue(REDRAWBUTSOBJECT, 0);
		allqueue(REDRAWOOPS, 0);
	}
	
	return nearBone!=NULL;
	
}

/*	mode==0: deselect
	mode==1: select
	mode==2: clear active tag 
*/
static void deselect_bonechildren (Object *ob, Bone *bone, int mode)
{
	Bone	*curBone;

	if (!bone)
		return;

	if (mode==0)
		bone->flag &= ~(BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL|BONE_ACTIVE);
	else if (mode==1) {
		if(!(bone->flag & BONE_HIDDEN_P))
			bone->flag |= (BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL);
	}
	else bone->flag &= ~BONE_ACTIVE;
	
	if(mode!=2) select_actionchannel_by_name(ob->action, bone->name, mode);

	for (curBone=bone->childbase.first; curBone; curBone=curBone->next){
		deselect_bonechildren(ob, curBone, mode);
	}
}

/* test==0: deselect all
   test==1: swap select
   test==2: only clear active tag 
*/
void deselectall_posearmature (Object *ob, int test)
{
	bArmature *arm;
	Bone *curBone;
	int	selectmode= 0;
	
	/* we call this from outliner too, but with OBACT set OK */
	if(!ob || !ob->pose) return;
	arm= get_armature(ob);
	
	/*	Determine if we're selecting or deselecting	*/
	if (test==1) {
		if (!count_bones (arm, BONE_SELECTED, 0))
			selectmode= 1;
	}
	else if(test==2)
		selectmode= 2;
	
	/*	Set the flags accordingly	*/
	for (curBone=arm->bonebase.first; curBone; curBone=curBone->next)
		deselect_bonechildren (ob, curBone, selectmode);
	
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWACTION, 0);

}


int bone_looper(Object *ob, Bone *bone, void *data,
                        int (*bone_func)(Object *, Bone *, void *)) 
{

    /* We want to apply the function bone_func to every bone 
     * in an armature -- feed bone_looper the first bone and 
     * a pointer to the bone_func and watch it go!. The int count 
     * can be useful for counting bones with a certain property
     * (e.g. skinnable)
     */
    int count = 0;

    if (bone) {

        /* only do bone_func if the bone is non null
         */
        count += bone_func(ob, bone, data);

        /* try to execute bone_func for the first child
         */
        count += bone_looper(ob, bone->childbase.first, data,
                                    bone_func);

        /* try to execute bone_func for the next bone at this
         * depth of the recursion.
         */
        count += bone_looper(ob, bone->next, data, bone_func);
    }

    return count;
}

int ik_chain_looper(Object *ob, Bone *bone, void *data,
				   int (*bone_func)(Object *, Bone *, void *)) 
{

    /* We want to apply the function bone_func to every bone 
     * in an ik chain -- feed ikchain_looper a bone in the chain and 
     * a pointer to the bone_func and watch it go!. The int count 
     * can be useful for counting bones with a certain property
     * (e.g. skinnable)
     */
	Bone *curBone;
    int   count = 0;

    if (bone) {

        /* This bone */
        count += bone_func(ob, bone, data);

        /* The parents */
		for (curBone = bone; curBone; curBone=curBone->parent) {
			if (!curBone->parent)
				break;
			else if (!(curBone->flag & BONE_IK_TOPARENT))
				break;
			count += bone_func(ob, curBone->parent, data);
		}

		/* The children */
		for (curBone = bone->childbase.first; curBone; curBone=curBone->next){
			if (curBone->flag & BONE_IK_TOPARENT) {
				count += bone_func(ob, curBone, data);
			}
		}
    }

    return count;
}

static int bone_skinnable(Object *ob, Bone *bone, void *data)
{
    /* Bones that are deforming
     * are regarded to be "skinnable" and are eligible for
     * auto-skinning.
     *
     * This function performs 2 functions:
     *
     *   a) It returns 1 if the bone is skinnable.
     *      If we loop over all bones with this 
     *      function, we can count the number of
     *      skinnable bones.
     *   b) If the pointer data is non null,
     *      it is treated like a handle to a
     *      bone pointer -- the bone pointer
     *      is set to point at this bone, and
     *      the pointer the handle points to
     *      is incremented to point to the
     *      next member of an array of pointers
     *      to bones. This way we can loop using
     *      this function to construct an array of
     *      pointers to bones that point to all
     *      skinnable bones.
     */
    Bone ***hbone;

    if (!(bone->flag & BONE_NO_DEFORM)) {
		if (data != NULL) {
			hbone = (Bone ***) data;
            **hbone = bone;
            ++*hbone;
        }
        return 1;
    }
    return 0;
}

static int add_defgroup_unique_bone(Object *ob, Bone *bone, void *data) 
{
    /* This group creates a vertex group to ob that has the
     * same name as bone (provided the bone is skinnable). 
	 * If such a vertex group aleady exist the routine exits.
     */
	if (!(bone->flag & BONE_NO_DEFORM)) {
		if (!get_named_vertexgroup(ob,bone->name)) {
			add_defgroup_name(ob, bone->name);
			return 1;
		}
    }
    return 0;
}

static int dgroup_skinnable(Object *ob, Bone *bone, void *data) 
{
    /* Bones that are not of boneclass BONE_UNSKINNABLE
     * are regarded to be "skinnable" and are eligible for
     * auto-skinning.
     *
     * This function performs 2 functions:
     *
     *   a) If the bone is skinnable, it creates 
     *      a vertex group for ob that has
     *      the name of the skinnable bone
     *      (if one doesn't exist already).
     *   b) If the pointer data is non null,
     *      it is treated like a handle to a
     *      bDeformGroup pointer -- the 
     *      bDeformGroup pointer is set to point
     *      to the deform group with the bone's
     *      name, and the pointer the handle 
     *      points to is incremented to point to the
     *      next member of an array of pointers
     *      to bDeformGroups. This way we can loop using
     *      this function to construct an array of
     *      pointers to bDeformGroups, all with names
     *      of skinnable bones.
     */
    bDeformGroup ***hgroup, *defgroup;

    if ( bone->boneclass != BONE_UNSKINNABLE ) {
        if ( !(defgroup = get_named_vertexgroup(ob, bone->name)) ) {
            defgroup = add_defgroup_name(ob, bone->name);
        }

        if (data != NULL) {
            hgroup = (bDeformGroup ***) data;
            **hgroup = defgroup;
            ++*hgroup;
        }
        return 1;
    }
    return 0;
}

static void add_verts_to_closest_dgroup(Object *ob, Object *par)
{
    /* This function implements a crude form of 
     * auto-skinning: vertices are assigned to the
     * deformation groups associated with bones based
     * on thier proximity to a bone. Every vert is
     * given a weight of 1.0 to the weight group
     * cooresponding to the bone that it is
     * closest to. The vertex may also be assigned to
     * a deformation group associated to a bone
     * that is within 10% of the mninimum distance
     * between the bone and the nearest vert -- the
     * cooresponding weight will fall-off to zero
     * as the distance approaches the 10% tolerance mark.
	 * If the mesh has subsurf enabled then the verts
	 * on the subsurf limit surface is used to generate 
	 * the weights rather than the verts on the cage
	 * mesh.
	 *
	 * ("Limit surface" = same amount of vertices as mesh, but vertices 
     *   moved to the subsurfed position, like for 'optimal').
     */

    bArmature *arm;
    Bone **bonelist, **bonehandle, *bone;
    bDeformGroup **dgrouplist, **dgrouphandle, *defgroup;
    float *distance;
    float   root[3];
    float   tip[3];
    float real_co[3];
	float *subverts = NULL;
    float *subvert;
    Mesh  *mesh;
    MVert *vert;

    int numbones, i, j;

    /* If the parent object is not an armature exit */
    arm = get_armature(par);
    if (!arm)
        return;

    /* count the number of skinnable bones */
    numbones = bone_looper(ob, arm->bonebase.first, NULL,
                                  bone_skinnable);

    /* create an array of pointer to bones that are skinnable
     * and fill it with all of the skinnable bones
     */
    bonelist = MEM_mallocN(numbones*sizeof(Bone *), "bonelist");
    bonehandle = bonelist;
    bone_looper(ob, arm->bonebase.first, &bonehandle,
                       bone_skinnable);

    /* create an array of pointers to the deform groups that
     * coorespond to the skinnable bones (creating them
     * as necessary.
     */
    dgrouplist = MEM_mallocN(numbones*sizeof(bDeformGroup *), "dgrouplist");
    dgrouphandle = dgrouplist;
    bone_looper(ob, arm->bonebase.first, &dgrouphandle,
                       dgroup_skinnable);

    /* create an array of floats that will be used for each vert
     * to hold the distance-factor to each bone.
     */
    distance = MEM_mallocN(numbones*sizeof(float), "distance");

    mesh = (Mesh*)ob->data;

	/* Is subsurf on? Lets use the verts on the limit surface then */
	if (modifiers_findByType(ob, eModifierType_Subsurf)) {
		subverts = MEM_mallocN(3*mesh->totvert*sizeof(float), "subverts");
		subsurf_calculate_limit_positions(mesh, (void *)subverts);	/* (ton) made void*, dunno how to cast */
	}

    /* for each vertex in the mesh ...
     */
    for ( i=0 ; i < mesh->totvert ; ++i ) {
        /* get the vert in global coords
         */
		
		if (subverts) {
			subvert = subverts + i*3;
			VECCOPY (real_co, subvert);
		}
		else {
			vert = mesh->mvert + i;
			VECCOPY (real_co, vert->co);
		}
        Mat4MulVecfl(ob->obmat, real_co);


        /* for each skinnable bone ...
         */
        for (j=0; j < numbones; ++j) {
            bone = bonelist[j];

            /* get the root of the bone in global coords
             */
			VECCOPY(root, bone->arm_head);
			Mat4MulVecfl(par->obmat, root);

            /* get the tip of the bone in global coords
             */
			VECCOPY(tip, bone->arm_tail);
            Mat4MulVecfl(par->obmat, tip);

            /* store the distance-factor from the vertex to
             * the bone
             */
			distance[j]= distfactor_to_bone (real_co, root, tip, bone->rad_head, bone->rad_tail, bone->dist);
        }

        /* for each deform group ...
         */
        for (j=0; j < numbones; ++j) {
            defgroup = dgrouplist[j];

            /* add the vert to the deform group if weight!=0.0
             */
            if (distance[j]!=0.0)
                add_vert_to_defgroup (ob, defgroup, i, distance[j], WEIGHT_REPLACE);
            else
                remove_vert_defgroup (ob, defgroup, i);
        }
    }

    /* free the memory allocated
     */
    MEM_freeN(bonelist);
    MEM_freeN(dgrouplist);
    MEM_freeN(distance);
	if (subverts) MEM_freeN(subverts);
}

void create_vgroups_from_armature(Object *ob, Object *par)
{
	/* Lets try to create some vertex groups 
	 * based on the bones of the parent armature.
	 */

	bArmature *arm;
	short mode;

	/* If the parent object is not an armature exit */
	arm = get_armature(par);
	if (!arm)
		return;

	/* Prompt the user on whether/how they want the vertex groups
	 * added to the child mesh */
    mode= pupmenu("Create Vertex Groups? %t|"
				  "Don't Create Groups %x1|"
				  "Name Groups %x2|"
                  "Create From Closest Bones %x3");
	switch (mode){
	case 2:
		/* Traverse the bone list, trying to create empty vertex 
		 * groups cooresponding to the bone.
		 */
		bone_looper(ob, arm->bonebase.first, NULL,
					add_defgroup_unique_bone);
		if (ob->type == OB_MESH)
			create_dverts((Mesh*)ob->data);

		break;

	case 3:
		/* Traverse the bone list, trying to create vertex groups 
		 * that are populated with the vertices for which the
		 * bone is closest.
		 */
		add_verts_to_closest_dgroup(ob, par);
		break;

	}
} 

static int hide_selected_pose_bone(Object *ob, Bone *bone, void *ptr) 
{
	if (bone->flag & BONE_SELECTED) {
		bone->flag |= BONE_HIDDEN_P;
		bone->flag &= ~BONE_SELECTED;
	}
	return 0;
}

/* active object is armature */
void hide_selected_pose_bones(void) 
{
	bArmature		*arm;

	arm= get_armature (OBACT);

	if (!arm)
		return;

	bone_looper(OBACT, arm->bonebase.first, NULL, 
				hide_selected_pose_bone);

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
}

static int hide_unselected_pose_bone(Object *ob, Bone *bone, void *ptr) 
{
	if (~bone->flag & BONE_SELECTED) {
		bone->flag |= BONE_HIDDEN_P;
	}
	return 0;
}

/* active object is armature */
void hide_unselected_pose_bones(void) 
{
	bArmature		*arm;

	arm=get_armature (OBACT);

	if (!arm)
		return;

	bone_looper(OBACT, arm->bonebase.first, NULL, 
				hide_unselected_pose_bone);

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
}

static int show_pose_bone(Object *ob, Bone *bone, void *ptr) 
{
	if (bone->flag & BONE_HIDDEN_P) {
		bone->flag &= ~BONE_HIDDEN_P;
		bone->flag |= BONE_SELECTED;
	}

	return 0;
}

/* active object is armature in posemode */
void show_all_pose_bones(void) 
{
	bArmature		*arm;

	arm=get_armature (OBACT);

	if (!arm)
		return;

	bone_looper(OBACT, arm->bonebase.first, NULL, 
				show_pose_bone);

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
}


/* ************* RENAMING DISASTERS ************ */

/* note: there's a unique_editbone_name() too! */
void unique_bone_name (bArmature *arm, char *name)
{
	char		tempname[64];
	int			number;
	char		*dot;
	
	if (get_named_bone(arm, name)) {
		
		/*	Strip off the suffix, if it's a number */
		number= strlen(name);
		if(number && isdigit(name[number-1])) {
			dot= strrchr(name, '.');	// last occurrance
			if (dot)
				*dot=0;
		}
		
		for (number = 1; number <=999; number++){
			sprintf (tempname, "%s.%03d", name, number);
			if (!get_named_bone(arm, tempname)){
				strcpy (name, tempname);
				return;
			}
		}
	}
}

#define MAXBONENAME 32
/* helper call for below */
static void constraint_bone_name_fix(Object *ob, ListBase *conlist, char *oldname, char *newname)
{
	bConstraint *curcon;
	char *subtarget;
	
	for (curcon = conlist->first; curcon; curcon=curcon->next){
		subtarget = get_con_subtarget_name(curcon, ob);
		if (subtarget)
			if (!strcmp(subtarget, oldname) )
				BLI_strncpy(subtarget, newname, MAXBONENAME);
	}
}

/* called by UI for renaming a bone */
/* warning: make sure the original bone was not renamed yet! */
/* seems messy, but thats what you get with not using pointers but channel names :) */
void armature_bone_rename(bArmature *arm, char *oldnamep, char *newnamep)
{
	Object *ob;
	char newname[MAXBONENAME];
	char oldname[MAXBONENAME];
	
	/* names better differ! */
	if(strncmp(oldnamep, newnamep, MAXBONENAME)) {
		
		/* we alter newname string... so make copy */
		BLI_strncpy(newname, newnamep, MAXBONENAME);
		/* we use oldname for search... so make copy */
		BLI_strncpy(oldname, oldnamep, MAXBONENAME);
		
		/* now check if we're in editmode, we need to find the unique name */
		if(G.obedit && G.obedit->data==arm) {
			EditBone	*eBone;

			eBone= editbone_name_exists(oldname);
			if(eBone) {
				unique_editbone_name (newname);
				BLI_strncpy(eBone->name, newname, MAXBONENAME);
			}
			else return;
		}
		else {
			Bone *bone= get_named_bone (arm, oldname);

			if(bone) {
				unique_bone_name (arm, newname);
				BLI_strncpy(bone->name, newname, MAXBONENAME);
			}
			else return;
		}
		
		/* do entire dbase */
		for(ob= G.main->object.first; ob; ob= ob->id.next) {
			/* we have the object using the armature */
			if(arm==ob->data) {
				Object *cob;
				bAction  *act;
				bActionChannel *chan;

				/* Rename action channel if necessary */
				act = ob->action;
				if (act && !act->id.lib){
					/*	Find the appropriate channel */
					chan= get_named_actionchannel(act, oldname);
					if(chan) BLI_strncpy(chan->name, newname, MAXBONENAME);
				}
		
				/* Rename the pose channel, if it exists */
				if (ob->pose) {
					bPoseChannel *pchan = get_pose_channel(ob->pose, oldname);
					if (pchan) {
						BLI_strncpy (pchan->name, newname, MAXBONENAME);
					}
				}
				
				/* and actually do the NLA too */
				/* (todo) */
				
				/* Update any object constraints to use the new bone name */
				for(cob= G.main->object.first; cob; cob= cob->id.next) {
					if(cob->constraints.first)
						constraint_bone_name_fix(ob, &cob->constraints, oldname, newname);
					if (cob->pose) {
						bPoseChannel *pchan;
						for (pchan = cob->pose->chanbase.first; pchan; pchan=pchan->next) {
							constraint_bone_name_fix(ob, &pchan->constraints, oldname, newname);
						}
					}
				}
				
			}
					
			/* See if an object is parented to this armature */
			if (ob->parent && (ob->parent->data == arm)) {
				if(ob->partype==PARBONE) {
					/* bone name in object */
					if (!strcmp(ob->parsubstr, oldname))
						BLI_strncpy(ob->parsubstr, newname, MAXBONENAME);
				}
				else if(ob->partype==PARSKEL) {
					bDeformGroup *dg;
					/* bone name in defgroup */
					for (dg=ob->defbase.first; dg; dg=dg->next) {
						if(!strcmp(dg->name, oldname))
						   BLI_strncpy(dg->name, newname, MAXBONENAME);
					}
				}
			}
		}
	}
}

/* context editmode object */
void armature_flip_names(void)
{
	EditBone *ebone;
	char newname[32];
	
	for (ebone = G.edbo.first; ebone; ebone=ebone->next) {
		if(ebone->flag & BONE_SELECTED) {
			BLI_strncpy(newname, ebone->name, sizeof(newname));
			bone_flip_name(newname, 1);		// 1 = do strip off number extensions
			armature_bone_rename(G.obedit->data, ebone->name, newname);
		}
	}
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue (REDRAWACTION, 0);
	allqueue(REDRAWOOPS, 0);
	BIF_undo_push("Flip names");
	
}

/* context; editmode armature */
EditBone *armature_bone_get_mirrored(EditBone *ebo)
{
	EditBone *eboflip= NULL;
	char name[32];
	
	BLI_strncpy(name, ebo->name, sizeof(name));
	bone_flip_name(name, 0);		// 0 = don't strip off number extensions

	for (eboflip=G.edbo.first; eboflip; eboflip=eboflip->next)
		if(ebo!=eboflip)
			if (!strcmp (name, eboflip->name)) break;
	
	return eboflip;
}

