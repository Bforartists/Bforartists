/**
 * $Id$
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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributor(s): Ton Roosendaal, Blender Foundation '05, full recode.
 *
 * ***** END GPL LICENSE BLOCK *****
 * support for animation modes - Reevan McKay
 */

#include <stdlib.h>
#include <string.h>

#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_view3d_types.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_blender.h"
#include "BKE_constraint.h"
#include "BKE_deform.h"
#include "BKE_depsgraph.h"
#include "BKE_DerivedMesh.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_modifier.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"

#include "BIF_editarmature.h"
#include "BIF_editaction.h"
#include "BIF_editconstraint.h"
#include "BIF_editdeform.h"
#include "BIF_gl.h"
#include "BIF_graphics.h"
#include "BIF_interface.h"
#include "BIF_poseobject.h"
#include "BIF_meshtools.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"
#include "BIF_screen.h"

#include "BDR_editobject.h"

#include "BSE_edit.h"
#include "BSE_editipo.h"
#include "BSE_trans_types.h"

#include "mydevice.h"
#include "blendef.h"

void enter_posemode(void)
{
	Base *base;
	Object *ob;
	bArmature *arm;
	
	if(G.scene->id.lib) return;
	base= BASACT;
	if(base==NULL) return;
	
	ob= base->object;
	
	if (ob->id.lib){
		error ("Can't pose libdata");
		return;
	}

	switch (ob->type){
	case OB_ARMATURE:
		arm= get_armature(ob);
		if( arm==NULL ) return;
		
		ob->flag |= OB_POSEMODE;
		base->flag= ob->flag;
		
		allqueue(REDRAWHEADERS, 0);	
		allqueue(REDRAWBUTSALL, 0);	
		allqueue(REDRAWOOPS, 0);
		allqueue(REDRAWVIEW3D, 0);
		break;
	default:
		return;
	}

	if (G.obedit) exit_editmode(EM_FREEDATA|EM_WAITCURSOR);
	G.f &= ~(G_VERTEXPAINT | G_FACESELECT | G_TEXTUREPAINT | G_WEIGHTPAINT);
}

void set_pose_keys (Object *ob)
{
	bArmature *arm= ob->data;
	bPoseChannel *chan;

	if (ob->pose){
		for (chan=ob->pose->chanbase.first; chan; chan=chan->next){
			Bone *bone= chan->bone;
			if(bone && (bone->flag & BONE_SELECTED) && (arm->layer & bone->layer)) {
				chan->flag |= POSE_KEY;		
			}
			else {
				chan->flag &= ~POSE_KEY;
			}
		}
	}
}


void exit_posemode(void)
{
	Object *ob= OBACT;
	Base *base= BASACT;

	if(ob==NULL) return;
	
	ob->flag &= ~OB_POSEMODE;
	base->flag= ob->flag;
	
	countall();
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWOOPS, 0);
	allqueue(REDRAWHEADERS, 0);	
	allqueue(REDRAWBUTSALL, 0);	

	scrarea_queue_headredraw(curarea);
}

/* called by buttons to find a bone to display/edit values for */
bPoseChannel *get_active_posechannel (Object *ob)
{
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	
	/* find active */
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(pchan->bone && (pchan->bone->flag & BONE_ACTIVE) && (pchan->bone->layer & arm->layer))
			return pchan;
	}
	
	return NULL;
}

/* only for real IK, not for auto-IK */
int pose_channel_in_IK_chain(Object *ob, bPoseChannel *pchan)
{
	bConstraint *con;
	Bone *bone;
	
	for(con= pchan->constraints.first; con; con= con->next) {
		if(con->type==CONSTRAINT_TYPE_KINEMATIC) {
			bKinematicConstraint *data= con->data;
			if((data->flag & CONSTRAINT_IK_AUTO)==0)
				return 1;
		}
	}
	for(bone= pchan->bone->childbase.first; bone; bone= bone->next) {
		pchan= get_pose_channel(ob->pose, bone->name);
		if(pchan && pose_channel_in_IK_chain(ob, pchan))
			return 1;
	}
	return 0;
}

/* ********************************************** */

/* for the object with pose/action: create path curves for selected bones */
void pose_calculate_path(Object *ob)
{
	bArmature *arm;
	bPoseChannel *pchan;
	Base *base;
	float *fp;
	int cfra;
	
	if(ob==NULL || ob->pose==NULL)
		return;
	arm= ob->data;
	
	if(EFRA<=SFRA) return;
	
	DAG_object_update_flags(G.scene, ob, screen_view3d_layers());
	
	/* malloc the path blocks */
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(pchan->bone && (pchan->bone->flag & BONE_SELECTED)) {
			if(arm->layer & pchan->bone->layer) {
				pchan->pathlen= EFRA-SFRA+1;
				if(pchan->path)
					MEM_freeN(pchan->path);
				pchan->path= MEM_callocN(3*pchan->pathlen*sizeof(float), "pchan path");
			}
		}
	}
	
	cfra= CFRA;
	for(CFRA=SFRA; CFRA<=EFRA; CFRA++) {
		
		/* do all updates */
		for(base= FIRSTBASE; base; base= base->next) {
			if(base->object->recalc) {
				int temp= base->object->recalc;
				object_handle_update(base->object);
				base->object->recalc= temp;
			}
		}
		
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			if(pchan->bone && (pchan->bone->flag & BONE_SELECTED)) {
				if(arm->layer & pchan->bone->layer) {
					if(pchan->path) {
						fp= pchan->path+3*(CFRA-SFRA);
						VECCOPY(fp, pchan->pose_tail);
						Mat4MulVecfl(ob->obmat, fp);
					}
				}
			}
		}
	}
	
	CFRA= cfra;
	allqueue(REDRAWVIEW3D, 0);	/* recalc tags are still there */
}


/* for the object with pose/action: clear all path curves */
void pose_clear_paths(Object *ob)
{
	bPoseChannel *pchan;
	
	if(ob==NULL || ob->pose==NULL)
		return;
	
	/* free the path blocks */
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(pchan->path) {
			MEM_freeN(pchan->path);
			pchan->path= NULL;
		}
	}
	
	allqueue(REDRAWVIEW3D, 0);
}



void pose_select_constraint_target(void)
{
	Object *ob= OBACT;
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	bConstraint *con;
	
	/* paranoia checks */
	if(!ob && !ob->pose) return;
	if(ob==G.obedit || (ob->flag & OB_POSEMODE)==0) return;
	
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(arm->layer & pchan->bone->layer) {
			if(pchan->bone->flag & (BONE_ACTIVE|BONE_SELECTED)) {
				
				for(con= pchan->constraints.first; con; con= con->next) {
					char *subtarget;
					Object *target= get_constraint_target(con, &subtarget);
					
					if(ob==target) {
						if(subtarget) {
							bPoseChannel *pchanc= get_pose_channel(ob->pose, subtarget);
							if(pchanc)
								pchanc->bone->flag |= BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL;
						}
					}
				}
			}
		}
	}
	
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWBUTSOBJECT, 0);
	allqueue (REDRAWOOPS, 0);
	
	BIF_undo_push("Select constraint target");

}

/* context: active channel */
void pose_special_editmenu(void)
{
	Object *ob= OBACT;
	short nr;
	
	/* paranoia checks */
	if(!ob && !ob->pose) return;
	if(ob==G.obedit || (ob->flag & OB_POSEMODE)==0) return;
	
	nr= pupmenu("Specials%t|Select Constraint Target%x1|Flip Left-Right Names%x2|Calculate Paths%x3|Clear All Paths%x4");
	if(nr==1) {
		pose_select_constraint_target();
	}
	else if(nr==2) {
		pose_flip_names();
	}
	else if(nr==3) {
		pose_calculate_path(ob);
	}
	else if(nr==4) {
		pose_clear_paths(ob);
	}
}

void pose_add_IK(void)
{
	Object *ob= OBACT;
	
	/* paranoia checks */
	if(!ob && !ob->pose) return;
	if(ob==G.obedit || (ob->flag & OB_POSEMODE)==0) return;
	
	add_constraint(1);	/* 1 means only IK */
}

/* context: all selected channels */
void pose_clear_IK(void)
{
	Object *ob= OBACT;
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	bConstraint *con;
	bConstraint *next;
	
	/* paranoia checks */
	if(!ob && !ob->pose) return;
	if(ob==G.obedit || (ob->flag & OB_POSEMODE)==0) return;
	
	if(okee("Remove IK constraint(s)")==0) return;

	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(arm->layer & pchan->bone->layer) {
			if(pchan->bone->flag & (BONE_ACTIVE|BONE_SELECTED)) {
				
				for(con= pchan->constraints.first; con; con= next) {
					next= con->next;
					if(con->type==CONSTRAINT_TYPE_KINEMATIC) {
						BLI_remlink(&pchan->constraints, con);
						free_constraint_data(con);
						MEM_freeN(con);
					}
				}
				pchan->constflag &= ~(PCHAN_HAS_IK|PCHAN_HAS_TARGET);
			}
		}
	}
	
	DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);	// and all its relations
	
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWBUTSOBJECT, 0);
	allqueue (REDRAWOOPS, 0);
	
	BIF_undo_push("Remove IK constraint(s)");
}

void pose_clear_constraints(void)
{
	Object *ob= OBACT;
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	
	/* paranoia checks */
	if(!ob && !ob->pose) return;
	if(ob==G.obedit || (ob->flag & OB_POSEMODE)==0) return;
	
	if(okee("Remove Constraints")==0) return;
	
	/* find active */
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(arm->layer & pchan->bone->layer) {
			if(pchan->bone->flag & (BONE_ACTIVE|BONE_SELECTED)) {
				free_constraints(&pchan->constraints);
				pchan->constflag= 0;
			}
		}
	}
	
	DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);	// and all its relations
	
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWBUTSOBJECT, 0);
	allqueue (REDRAWOOPS, 0);
	
	BIF_undo_push("Remove Constraint(s)");
	
}


void pose_copy_menu(void)
{
	Object *ob= OBACT;
	bArmature *arm= ob->data;
	bPoseChannel *pchan, *pchanact;
	short nr;
	int i=0;
	
	/* paranoia checks */
	if(!ob && !ob->pose) return;
	if(ob==G.obedit || (ob->flag & OB_POSEMODE)==0) return;
	
	/* find active */
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(pchan->bone->flag & BONE_ACTIVE) break;
	}
	
	if(pchan==NULL) return;
	pchanact= pchan;
	
	i= BLI_countlist(&(pchanact->constraints)); /* if there are 24 or less, allow for the user to select constraints */
	if (i<25)
		nr= pupmenu("Copy Pose Attributes %t|Location%x1|Rotation%x2|Size%x3|Constraints (All)%x4|Constraints...%x5");
	else
		nr= pupmenu("Copy Pose Attributes %t|Location%x1|Rotation%x2|Size%x3|Constraints (All)%x4");
	
	if(nr==-1) return;
	if(nr!=5)  {
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			if(	(arm->layer & pchan->bone->layer) &&
				(pchan->bone->flag & BONE_SELECTED) &&
				(pchan!=pchanact)
			) {
				if(nr==1) {
					VECCOPY(pchan->loc, pchanact->loc);
				}
				else if(nr==2) {
					QUATCOPY(pchan->quat, pchanact->quat);
				}
				else if(nr==3) {
					VECCOPY(pchan->size, pchanact->size);
				}
				else if(nr==4) {
					free_constraints(&pchan->constraints);
					copy_constraints(&pchan->constraints, &pchanact->constraints);
					pchan->constflag = pchanact->constflag;
				}
			}
		}
	} else { /* constraints, optional */
		bConstraint *con, *con_back;
		int const_toggle[24];
		ListBase const_copy={0, 0};
		
		duplicatelist (&const_copy, &(pchanact->constraints));
		
		/* build the puplist of constraints */
		for (con = pchanact->constraints.first, i=0; con; con=con->next, i++){
			const_toggle[i]= 1;
			add_numbut(i, TOG|INT, con->name, 0, 0, &(const_toggle[i]), "");
		}
		
		if (!do_clever_numbuts("Select Constraints", i, REDRAW)) {
			BLI_freelistN(&const_copy);
			return;
		}
		
		/* now build a new listbase from the options selected */
		for (i=0, con=const_copy.first; con; i++) {
			if (!const_toggle[i]) {
				con_back= con->next;
				BLI_freelinkN(&const_copy, con);
				con= con_back;
			} else {
				con= con->next;
			}
		}
		
		/* Copy the temo listbase to the selected posebones */
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			if(	(arm->layer & pchan->bone->layer) &&
				(pchan->bone->flag & BONE_SELECTED) &&
				(pchan!=pchanact)
			) {
				free_constraints(&pchan->constraints);
				copy_constraints(&pchan->constraints, &const_copy);
				pchan->constflag = pchanact->constflag;
			}
		}
		BLI_freelistN(&const_copy);
		update_pose_constraint_flags(ob->pose); /* we could work out the flags but its simpler to do this */
	}
	
	DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);	// and all its relations
	
	allqueue (REDRAWVIEW3D, 0);
	allqueue (REDRAWBUTSOBJECT, 0);
	allqueue (REDRAWOOPS, 0);
	
	BIF_undo_push("Copy Pose Attributes");
	
}

/* ******************** copy/paste pose ********************** */

static bPose	*g_posebuf=NULL;

void free_posebuf(void) 
{
	if (g_posebuf) {
		// was copied without constraints
		BLI_freelistN (&g_posebuf->chanbase);
		MEM_freeN (g_posebuf);
	}
	g_posebuf=NULL;
}

void copy_posebuf (void)
{
	Object *ob= OBACT;

	if (!ob || !ob->pose){
		error ("No Pose");
		return;
	}

	free_posebuf();
	
	set_pose_keys(ob);  // sets chan->flag to POSE_KEY if bone selected
	copy_pose(&g_posebuf, ob->pose, 0);

}

void paste_posebuf (int flip)
{
	Object *ob= OBACT;
	bPoseChannel *chan, *pchan;
	float eul[4];
	char name[32];
	
	if (!ob || !ob->pose)
		return;

	if (!g_posebuf){
		error ("Copy buffer is empty");
		return;
	}
	
	/* Safely merge all of the channels in this pose into
	any existing pose */
	for (chan=g_posebuf->chanbase.first; chan; chan=chan->next){
		if (chan->flag & POSE_KEY) {
			BLI_strncpy(name, chan->name, sizeof(name));
			if (flip)
				bone_flip_name (name, 0);		// 0 = don't strip off number extensions
				
			/* only copy when channel exists, poses are not meant to add random channels to anymore */
			pchan= get_pose_channel(ob->pose, name);
			
			if(pchan) {
				/* only loc rot size */
				/* only copies transform info for the pose */
				VECCOPY(pchan->loc, chan->loc);
				VECCOPY(pchan->size, chan->size);
				QUATCOPY(pchan->quat, chan->quat);
				pchan->flag= chan->flag;
				
				if (flip){
					pchan->loc[0]*= -1;

					QuatToEul(pchan->quat, eul);
					eul[1]*= -1;
					eul[2]*= -1;
					EulToQuat(eul, pchan->quat);
				}

				if (G.flags & G_RECORDKEYS){
					ID *id= &ob->id;

					/* Set keys on pose */
					if (chan->flag & POSE_ROT){
						insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_X);
						insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_Y);
						insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_Z);
						insertkey(id, ID_PO, pchan->name, NULL, AC_QUAT_W);
					}
					if (chan->flag & POSE_SIZE){
						insertkey(id, ID_PO, pchan->name, NULL, AC_SIZE_X);
						insertkey(id, ID_PO, pchan->name, NULL, AC_SIZE_Y);
						insertkey(id, ID_PO, pchan->name, NULL, AC_SIZE_Z);
					}
					if (chan->flag & POSE_LOC){
						insertkey(id, ID_PO, pchan->name, NULL, AC_LOC_X);
						insertkey(id, ID_PO, pchan->name, NULL, AC_LOC_Y);
						insertkey(id, ID_PO, pchan->name, NULL, AC_LOC_Z);
					}
				}
			}
		}
	}

	/* Update event for pose and deformation children */
	DAG_object_flush_update(G.scene, ob, OB_RECALC_DATA);
	
	if (G.flags & G_RECORDKEYS) {
		remake_action_ipos(ob->action);
		allqueue (REDRAWIPO, 0);
		allqueue (REDRAWVIEW3D, 0);
		allqueue (REDRAWACTION, 0);		
		allqueue(REDRAWNLA, 0);
	}
	else {
		/* need to trick depgraph, action is not allowed to execute on pose */
		where_is_pose(ob);
		ob->recalc= 0;
	}

	BIF_undo_push("Paste Action Pose");
}

/* ********************************************** */

struct vgroup_map {
	float head[3], tail[3];
	Bone *bone;
	bDeformGroup *dg, *dgflip;
	Object *meshobj;
};

static void pose_adds_vgroups__mapFunc(void *userData, int index, float *co, float *no_f, short *no_s)
{
	struct vgroup_map *map= userData;
	float vec[3], fac;
	
	VECCOPY(vec, co);
	Mat4MulVecfl(map->meshobj->obmat, vec);
		
	/* get the distance-factor from the vertex to bone */
	fac= distfactor_to_bone (vec, map->head, map->tail, map->bone->rad_head, map->bone->rad_tail, map->bone->dist);
	
	/* add to vgroup. this call also makes me->dverts */
	if(fac!=0.0f) 
		add_vert_to_defgroup (map->meshobj, map->dg, index, fac, WEIGHT_REPLACE);
	else
		remove_vert_defgroup (map->meshobj, map->dg, index);
	
	if(map->dgflip) {
		int j= mesh_get_x_mirror_vert(map->meshobj, index);
		if(j>=0) {
			if(fac!=0.0f) 
				add_vert_to_defgroup (map->meshobj, map->dgflip, j, fac, WEIGHT_REPLACE);
			else
				remove_vert_defgroup (map->meshobj, map->dgflip, j);
		}
	}
}

/* context weightpaint and deformer in posemode */
void pose_adds_vgroups(Object *meshobj)
{
	extern VPaint Gwp;         /* from vpaint */
	struct vgroup_map map;
	DerivedMesh *dm;
	Object *poseobj= modifiers_isDeformedByArmature(meshobj);
	bArmature *arm= poseobj->data;
	bPoseChannel *pchan;
	Bone *bone;
	bDeformGroup *dg, *curdef;
	int DMneedsFree;
	
	if(poseobj==NULL || (poseobj->flag & OB_POSEMODE)==0) return;
	
	dm = mesh_get_derived_final(meshobj, &DMneedsFree);
	
	map.meshobj= meshobj;
	
	for(pchan= poseobj->pose->chanbase.first; pchan; pchan= pchan->next) {
		bone= pchan->bone;
		if(arm->layer & pchan->bone->layer) {
			if(bone->flag & (BONE_SELECTED)) {
				
				/* check if mesh has vgroups */
				dg= get_named_vertexgroup(meshobj, bone->name);
				if(dg==NULL)
					dg= add_defgroup_name(meshobj, bone->name);
				
				/* flipped bone */
				if(Gwp.flag & VP_MIRROR_X) {
					char name[32];
					
					BLI_strncpy(name, dg->name, 32);
					bone_flip_name(name, 0);		// 0 = don't strip off number extensions
					
					for (curdef = meshobj->defbase.first; curdef; curdef=curdef->next)
						if (!strcmp(curdef->name, name))
							break;
					map.dgflip= curdef;
				}
				else map.dgflip= NULL;
				
				/* get the root of the bone in global coords */
				VECCOPY(map.head, bone->arm_head);
				Mat4MulVecfl(poseobj->obmat, map.head);
				
				/* get the tip of the bone in global coords */
				VECCOPY(map.tail, bone->arm_tail);
				Mat4MulVecfl(poseobj->obmat, map.tail);
				
				/* use the optimal vertices instead of mverts */
				map.dg= dg;
				map.bone= bone;
				if(dm->foreachMappedVert) 
					dm->foreachMappedVert(dm, pose_adds_vgroups__mapFunc, (void*) &map);
				else {
					Mesh *me= meshobj->data;
					int i;
					for(i=0; i<me->totvert; i++) 
						pose_adds_vgroups__mapFunc(&map, i, (me->mvert+i)->co, NULL, NULL);
				}
				
			}
		}
	}
	
	if (DMneedsFree) dm->release(dm);

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	
	DAG_object_flush_update(G.scene, meshobj, OB_RECALC_DATA);	// and all its relations

}

/* ********************************************** */

/* context active object */
void pose_flip_names(void)
{
	Object *ob= OBACT;
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	char newname[32];
	
	/* paranoia checks */
	if(!ob && !ob->pose) return;
	if(ob==G.obedit || (ob->flag & OB_POSEMODE)==0) return;
	
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(arm->layer & pchan->bone->layer) {
			if(pchan->bone->flag & (BONE_ACTIVE|BONE_SELECTED)) {
				BLI_strncpy(newname, pchan->name, sizeof(newname));
				bone_flip_name(newname, 1);	// 1 = do strip off number extensions
				armature_bone_rename(ob->data, pchan->name, newname);
			}
		}
	}
	
	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWBUTSEDIT, 0);
	allqueue(REDRAWBUTSOBJECT, 0);
	allqueue (REDRAWACTION, 0);
	allqueue(REDRAWOOPS, 0);
	BIF_undo_push("Flip names");
	
}

/* context active object, or weightpainted object with armature in posemode */
void pose_activate_flipped_bone(void)
{
	Object *ob= OBACT;
	bArmature *arm= ob->data;
	
	if(ob==NULL) return;

	if(G.f & G_WEIGHTPAINT) {
		ob= modifiers_isDeformedByArmature(ob);
	}
	if(ob && (ob->flag & OB_POSEMODE)) {
		bPoseChannel *pchan, *pchanf;
		
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			if(arm->layer & pchan->bone->layer) {
				if(pchan->bone->flag & BONE_ACTIVE)
					break;
			}
		}
		if(pchan) {
			char name[32];
			
			BLI_strncpy(name, pchan->name, 32);
			bone_flip_name(name, 1);	// 0 = do not strip off number extensions
			
			pchanf= get_pose_channel(ob->pose, name);
			if(pchanf && pchanf!=pchan) {
				pchan->bone->flag &= ~(BONE_SELECTED|BONE_ACTIVE);
				pchanf->bone->flag |= (BONE_SELECTED|BONE_ACTIVE);
			
				/* in weightpaint we select the associated vertex group too */
				if(G.f & G_WEIGHTPAINT) {
					vertexgroup_select_by_name(OBACT, name);
					DAG_object_flush_update(G.scene, OBACT, OB_RECALC_DATA);
				}
				
				select_actionchannel_by_name(ob->action, name, 1);
				
				allqueue(REDRAWVIEW3D, 0);
				allqueue(REDRAWACTION, 0);
				allqueue(REDRAWIPO, 0);		/* To force action/constraint ipo update */
				allqueue(REDRAWBUTSEDIT, 0);
				allqueue(REDRAWBUTSOBJECT, 0);
				allqueue(REDRAWOOPS, 0);
			}			
		}
	}
}


void pose_movetolayer(void)
{
	Object *ob= OBACT;
	bArmature *arm;
	short lay= 0;
	
	if(ob==NULL) return;
	arm= ob->data;
	
	if(ob->flag & OB_POSEMODE) {
		bPoseChannel *pchan;
		
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			if(arm->layer & pchan->bone->layer) {
				if(pchan->bone->flag & BONE_SELECTED)
					lay |= pchan->bone->layer;
			}
		}
		if(lay==0) return;
		
		if( movetolayer_short_buts(&lay)==0 ) return;
		if(lay==0) return;

		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			if(arm->layer & pchan->bone->layer) {
				if(pchan->bone->flag & BONE_SELECTED)
					pchan->bone->layer= lay;
			}
		}
		
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWACTION, 0);
		allqueue(REDRAWBUTSEDIT, 0);
	}
}
