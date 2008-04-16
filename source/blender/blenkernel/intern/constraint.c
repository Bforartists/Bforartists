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
 * The Original Code is: all of this file.
 *
 * Contributor(s): 2007, Joshua Leung, major recode
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <stdio.h> 
#include <stddef.h>
#include <string.h>
#include <math.h>

#include "MEM_guardedalloc.h"
#include "nla.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_object_types.h"
#include "DNA_action_types.h"
#include "DNA_curve_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_lattice_types.h"
#include "DNA_scene_types.h"
#include "DNA_text_types.h"

#include "BKE_utildefines.h"
#include "BKE_action.h"
#include "BKE_anim.h" /* for the curve calculation part */
#include "BKE_armature.h"
#include "BKE_blender.h"
#include "BKE_constraint.h"
#include "BKE_displist.h"
#include "BKE_deform.h"
#include "BKE_DerivedMesh.h"	/* for geometry targets */
#include "BKE_cdderivedmesh.h" /* for geometry targets */
#include "BKE_object.h"
#include "BKE_ipo.h"
#include "BKE_global.h"
#include "BKE_library.h"
#include "BKE_idprop.h"


#include "BPY_extern.h"

#include "blendef.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef M_PI
#define M_PI		3.14159265358979323846
#endif


/* ******************* Constraint Channels ********************** */
/* Constraint Channels exist in one of two places:
 *	- Under Action Channels in an Action  (act->chanbase->achan->constraintChannels)
 *	- Under Object without Object-level Action yet (ob->constraintChannels)
 * 
 * The main purpose that Constraint Channels serve is to act as a link
 * between an IPO-block (which provides values to interpolate between for some settings)
 */

/* ------------ Data Management ----------- */
 
/* Free constraint channels, and reduce the number of users of the related ipo-blocks */
void free_constraint_channels (ListBase *chanbase)
{
	bConstraintChannel *chan;
	
	for (chan=chanbase->first; chan; chan=chan->next) {
		if (chan->ipo) {
			chan->ipo->id.us--;
		}
	}
	
	BLI_freelistN(chanbase);
}

/* Make a copy of the constraint channels from dst to src, and also give the
 * new constraint channels their own copy of the original's IPO.
 */
void copy_constraint_channels (ListBase *dst, ListBase *src)
{
	bConstraintChannel *dchan, *schan;
	
	dst->first = dst->last = NULL;
	duplicatelist(dst, src);
	
	for (dchan=dst->first, schan=src->first; dchan; dchan=dchan->next, schan=schan->next) {
		dchan->ipo = copy_ipo(schan->ipo);
	}
}

/* Make a copy of the constraint channels from dst to src, but make the
 * new constraint channels use the same IPO-data as their twin.
 */
void clone_constraint_channels (ListBase *dst, ListBase *src)
{
	bConstraintChannel *dchan, *schan;
	
	dst->first = dst->last = NULL;
	duplicatelist(dst, src);
	
	for (dchan=dst->first, schan=src->first; dchan; dchan=dchan->next, schan=schan->next) {
		id_us_plus((ID *)dchan->ipo);
	}
}

/* ------------- Constraint Channel Tools ------------ */

/* Find the constraint channel with a given name */
bConstraintChannel *get_constraint_channel (ListBase *list, const char name[])
{
	bConstraintChannel *chan;

	if (list) {
		for (chan = list->first; chan; chan=chan->next) {
			if (!strcmp(name, chan->name)) {
				return chan;
			}
		}
	}
	
	return NULL;
}

/* Find or create a new constraint channel */
bConstraintChannel *verify_constraint_channel (ListBase *list, const char name[])
{
	bConstraintChannel *chan;
	
	chan= get_constraint_channel(list, name);
	
	if (chan == NULL) {
		chan= MEM_callocN(sizeof(bConstraintChannel), "new constraint channel");
		BLI_addtail(list, chan);
		strcpy(chan->name, name);
	}
	
	return chan;
}

/* --------- Constraint Channel Evaluation/Execution --------- */

/* IPO-system call: calculate IPO-block for constraint channels, and flush that
 * info onto the corresponding constraint.
 */
void do_constraint_channels (ListBase *conbase, ListBase *chanbase, float ctime, short onlydrivers)
{
	bConstraint *con;
	
	/* for each Constraint, calculate its Influence from the corresponding ConstraintChannel */
	for (con=conbase->first; con; con=con->next) {
		Ipo *ipo= NULL;
		
		if (con->flag & CONSTRAINT_OWN_IPO)
			ipo= con->ipo;
		else {
			bConstraintChannel *chan = get_constraint_channel(chanbase, con->name);
			if (chan) ipo= chan->ipo;
		}
		
		if (ipo) {
			IpoCurve *icu;
			
			calc_ipo(ipo, ctime);
			
			for (icu=ipo->curve.first; icu; icu=icu->next) {
				if (!onlydrivers || icu->driver) {
					switch (icu->adrcode) {
						case CO_ENFORCE:
						{
							/* Influence is clamped to 0.0f -> 1.0f range */
							con->enforce = CLAMPIS(icu->curval, 0.0f, 1.0f);
						}
							break;
						case CO_HEADTAIL:
						{
							/* we need to check types of constraints that can get this here, as user
							 * may have created an IPO-curve for this from IPO-editor but for a constraint
							 * that cannot support this
							 */
							switch (con->type) {
								/* supported constraints go here... */
								case CONSTRAINT_TYPE_LOCLIKE:
								case CONSTRAINT_TYPE_TRACKTO:
								case CONSTRAINT_TYPE_MINMAX:
								case CONSTRAINT_TYPE_STRETCHTO:
								case CONSTRAINT_TYPE_DISTLIMIT:
									con->headtail = icu->curval;
									break;
									
								default:
									/* not supported */
									break;
							}
						}
							break;
					}
				}
			}
		}
	}
}

/* ************************ Constraints - General Utilities *************************** */
/* These functions here don't act on any specific constraints, and are therefore should/will
 * not require any of the special function-pointers afforded by the relevant constraint 
 * type-info structs.
 */

/* -------------- Naming -------------- */

/* Find the first available, non-duplicate name for a given constraint */
void unique_constraint_name (bConstraint *con, ListBase *list)
{
	BLI_uniquename(list, con, "Const", offsetof(bConstraint, name), 32);
}

/* ----------------- Evaluation Loop Preparation --------------- */

/* package an object/bone for use in constraint evaluation */
/* This function MEM_calloc's a bConstraintOb struct, that will need to be freed after evaluation */
bConstraintOb *constraints_make_evalob (Object *ob, void *subdata, short datatype)
{
	bConstraintOb *cob;
	
	/* create regardless of whether we have any data! */
	cob= MEM_callocN(sizeof(bConstraintOb), "bConstraintOb");
	
	/* based on type of available data */
	switch (datatype) {
		case CONSTRAINT_OBTYPE_OBJECT:
		{
			/* disregard subdata... calloc should set other values right */
			if (ob) {
				cob->ob = ob;
				cob->type = datatype;
				Mat4CpyMat4(cob->matrix, ob->obmat);
			}
			else
				Mat4One(cob->matrix);
			
			Mat4CpyMat4(cob->startmat, cob->matrix);
		}
			break;
		case CONSTRAINT_OBTYPE_BONE:
		{
			/* only set if we have valid bone, otherwise default */
			if (ob && subdata) {
				cob->ob = ob;
				cob->pchan = (bPoseChannel *)subdata;
				cob->type = datatype;
				
				/* matrix in world-space */
				Mat4MulMat4(cob->matrix, cob->pchan->pose_mat, ob->obmat);
			}
			else
				Mat4One(cob->matrix);
				
			Mat4CpyMat4(cob->startmat, cob->matrix);
		}
			break;
			
		default: /* other types not yet handled */
			Mat4One(cob->matrix);
			Mat4One(cob->startmat);
			break;
	}
	
	return cob;
}

/* cleanup after constraint evaluation */
void constraints_clear_evalob (bConstraintOb *cob)
{
	float delta[4][4], imat[4][4];
	
	/* prevent crashes */
	if (cob == NULL) 
		return;
	
	/* calculate delta of constraints evaluation */
	Mat4Invert(imat, cob->startmat);
	Mat4MulMat4(delta, imat, cob->matrix);
	
	/* copy matrices back to source */
	switch (cob->type) {
		case CONSTRAINT_OBTYPE_OBJECT:
		{
			/* cob->ob might not exist! */
			if (cob->ob) {
				/* copy new ob-matrix back to owner */
				Mat4CpyMat4(cob->ob->obmat, cob->matrix);
				
				/* copy inverse of delta back to owner */
				Mat4Invert(cob->ob->constinv, delta);
			}
		}
			break;
		case CONSTRAINT_OBTYPE_BONE:
		{
			/* cob->ob or cob->pchan might not exist */
			if (cob->ob && cob->pchan) {
				/* copy new pose-matrix back to owner */
				Mat4MulMat4(cob->pchan->pose_mat, cob->matrix, cob->ob->imat);
				
				/* copy inverse of delta back to owner */
				Mat4Invert(cob->pchan->constinv, delta);
			}
		}
			break;
	}
	
	/* free tempolary struct */
	MEM_freeN(cob);
}

/* -------------- Space-Conversion API -------------- */

/* This function is responsible for the correct transformations/conversions 
 * of a matrix from one space to another for constraint evaluation.
 * For now, this is only implemented for Objects and PoseChannels.
 */
void constraint_mat_convertspace (Object *ob, bPoseChannel *pchan, float mat[][4], short from, short to)
{
	float tempmat[4][4];
	float diff_mat[4][4];
	float imat[4][4];
	
	/* prevent crashes in these unlikely events  */
	if (ob==NULL || mat==NULL) return;
	/* optimise trick - check if need to do anything */
	if (from == to) return;
	
	/* are we dealing with pose-channels or objects */
	if (pchan) {
		/* pose channels */
		switch (from) {
			case CONSTRAINT_SPACE_WORLD: /* ---------- FROM WORLDSPACE ---------- */
			{
				/* world to pose */
				if (to==CONSTRAINT_SPACE_POSE || to==CONSTRAINT_SPACE_LOCAL || to==CONSTRAINT_SPACE_PARLOCAL) {
					Mat4Invert(imat, ob->obmat);
					Mat4CpyMat4(tempmat, mat);
					Mat4MulMat4(mat, tempmat, imat);
				}
				
				/* pose to local */
				if (to == CONSTRAINT_SPACE_LOCAL) {
					/* call self with slightly different values */
					constraint_mat_convertspace(ob, pchan, mat, CONSTRAINT_SPACE_POSE, to);
				}
				/* pose to local + parent */
				else if (to == CONSTRAINT_SPACE_PARLOCAL) {
					/* call self with slightly different values */
					constraint_mat_convertspace(ob, pchan, mat, CONSTRAINT_SPACE_POSE, to);
				}
			}
				break;
			case CONSTRAINT_SPACE_POSE:	/* ---------- FROM POSESPACE ---------- */
			{
				/* pose to world */
				if (to == CONSTRAINT_SPACE_WORLD) {
					Mat4CpyMat4(tempmat, mat);
					Mat4MulMat4(mat, tempmat, ob->obmat);
				}
				/* pose to local */
				else if (to == CONSTRAINT_SPACE_LOCAL) {
					if (pchan->bone) {
						if (pchan->parent) {
							float offs_bone[4][4];
								
							/* construct offs_bone the same way it is done in armature.c */
							Mat4CpyMat3(offs_bone, pchan->bone->bone_mat);
							VECCOPY(offs_bone[3], pchan->bone->head);
							offs_bone[3][1]+= pchan->bone->parent->length;
							
							if (pchan->bone->flag & BONE_HINGE) {
								/* pose_mat = par_pose-space_location * chan_mat */
								float tmat[4][4];
								
								/* the rotation of the parent restposition */
								Mat4CpyMat4(tmat, pchan->bone->parent->arm_mat);
								
								/* the location of actual parent transform */
								VECCOPY(tmat[3], offs_bone[3]);
								offs_bone[3][0]= offs_bone[3][1]= offs_bone[3][2]= 0.0f;
								Mat4MulVecfl(pchan->parent->pose_mat, tmat[3]);
								
								Mat4MulMat4(diff_mat, offs_bone, tmat);
								Mat4Invert(imat, diff_mat);
							}
							else {
								/* pose_mat = par_pose_mat * bone_mat * chan_mat */
								Mat4MulMat4(diff_mat, offs_bone, pchan->parent->pose_mat);
								Mat4Invert(imat, diff_mat);
							}
						}
						else {
							/* pose_mat = chan_mat * arm_mat */
							Mat4Invert(imat, pchan->bone->arm_mat);
						}
						
						Mat4CpyMat4(tempmat, mat);
						Mat4MulMat4(mat, tempmat, imat);
					}
				}
				/* pose to local with parent */
				else if (to == CONSTRAINT_SPACE_PARLOCAL) {
					if (pchan->bone) {
						Mat4Invert(imat, pchan->bone->arm_mat);
						Mat4CpyMat4(tempmat, mat);
						Mat4MulMat4(mat, tempmat, imat);
					}
				}
			}
				break;
			case CONSTRAINT_SPACE_LOCAL: /* ------------ FROM LOCALSPACE --------- */
			{
				/* local to pose */
				if (to==CONSTRAINT_SPACE_POSE || to==CONSTRAINT_SPACE_WORLD) {
					/* do inverse procedure that was done for pose to local */
					if (pchan->bone) {
						/* we need the posespace_matrix = local_matrix + (parent_posespace_matrix + restpos) */						
						if (pchan->parent) {
							float offs_bone[4][4];
							
							/* construct offs_bone the same way it is done in armature.c */
							Mat4CpyMat3(offs_bone, pchan->bone->bone_mat);
							VECCOPY(offs_bone[3], pchan->bone->head);
							offs_bone[3][1]+= pchan->bone->parent->length;
							
							if (pchan->bone->flag & BONE_HINGE) {
								/* pose_mat = par_pose-space_location * chan_mat */
								float tmat[4][4];
								
								/* the rotation of the parent restposition */
								Mat4CpyMat4(tmat, pchan->bone->parent->arm_mat);
								
								/* the location of actual parent transform */
								VECCOPY(tmat[3], offs_bone[3]);
								offs_bone[3][0]= offs_bone[3][1]= offs_bone[3][2]= 0.0f;
								Mat4MulVecfl(pchan->parent->pose_mat, tmat[3]);
								
								Mat4MulMat4(diff_mat, offs_bone, tmat);
								Mat4CpyMat4(tempmat, mat);
								Mat4MulMat4(mat, tempmat, diff_mat);
							}
							else {
								/* pose_mat = par_pose_mat * bone_mat * chan_mat */
								Mat4MulMat4(diff_mat, offs_bone, pchan->parent->pose_mat);
								Mat4CpyMat4(tempmat, mat);
								Mat4MulMat4(mat, tempmat, diff_mat);
							}
						}
						else {
							Mat4CpyMat4(diff_mat, pchan->bone->arm_mat);
							
							Mat4CpyMat4(tempmat, mat);
							Mat4MulMat4(mat, tempmat, diff_mat);
						}
					}
				}
				/* local to world */
				if (to == CONSTRAINT_SPACE_WORLD) {
					/* call self with slightly different values */
					constraint_mat_convertspace(ob, pchan, mat, CONSTRAINT_SPACE_POSE, to);
				}
			}
				break;
			case CONSTRAINT_SPACE_PARLOCAL: /* -------------- FROM LOCAL WITH PARENT ---------- */
			{
				/* local to pose */
				if (to==CONSTRAINT_SPACE_POSE || to==CONSTRAINT_SPACE_WORLD) {
					if (pchan->bone) {					
						Mat4CpyMat4(diff_mat, pchan->bone->arm_mat);
						Mat4CpyMat4(tempmat, mat);
						Mat4MulMat4(mat, diff_mat, tempmat);
					}
				}
				/* local to world */
				if (to == CONSTRAINT_SPACE_WORLD) {
					/* call self with slightly different values */
					constraint_mat_convertspace(ob, pchan, mat, CONSTRAINT_SPACE_POSE, to);
				}
			}
				break;
		}
	}
	else {
		/* objects */
		if (from==CONSTRAINT_SPACE_WORLD && to==CONSTRAINT_SPACE_LOCAL) {
			/* check if object has a parent - otherwise this won't work */
			if (ob->parent) {
				/* 'subtract' parent's effects from owner */
				Mat4MulMat4(diff_mat, ob->parentinv, ob->parent->obmat);
				Mat4Invert(imat, diff_mat);
				Mat4CpyMat4(tempmat, mat);
				Mat4MulMat4(mat, tempmat, imat);
			}
		}
		else if (from==CONSTRAINT_SPACE_LOCAL && to==CONSTRAINT_SPACE_WORLD) {
			/* check that object has a parent - otherwise this won't work */
			if (ob->parent) {
				/* 'add' parent's effect back to owner */
				Mat4CpyMat4(tempmat, mat);
				Mat4MulMat4(diff_mat, ob->parentinv, ob->parent->obmat);
				Mat4MulMat4(mat, tempmat, diff_mat);
			}
		}
	}
}

/* ------------ General Target Matrix Tools ---------- */

/* function that sets the given matrix based on given vertex group in mesh */
static void contarget_get_mesh_mat (Object *ob, char *substring, float mat[][4])
{
	DerivedMesh *dm;
	float vec[3] = {0.0f, 0.0f, 0.0f}, tvec[3];
	float normal[3] = {0.0f, 0.0f, 0.0f}, plane[3];
	float imat[3][3], tmat[3][3];
	int dgroup;
	
	/* initialize target matrix using target matrix */
	Mat4CpyMat4(mat, ob->obmat);
	
	/* get index of vertex group */
	dgroup = get_named_vertexgroup_num(ob, substring);
	if (dgroup < 0) return;
	
	/* get DerivedMesh */
	if (G.obedit && G.editMesh) {
		/* we are in editmode, so get a special derived mesh */
		dm = CDDM_from_editmesh(G.editMesh, ob->data);
	}
	else {
		/* when not in EditMode, this should exist */
		dm = (DerivedMesh *)ob->derivedFinal;
	}
	
	/* only continue if there's a valid DerivedMesh */
	if (dm) {
		MDeformVert *dvert = dm->getVertDataArray(dm, CD_MDEFORMVERT);
		int *index = (int *)dm->getVertDataArray(dm, CD_ORIGINDEX);
		int numVerts = dm->getNumVerts(dm);
		int i, j, count = 0;
		float co[3], nor[3];
		
		/* check that dvert and index are valid pointers (just in case) */
		if (dvert && index) {
			/* get the average of all verts with that are in the vertex-group */
			for (i = 0; i < numVerts; i++, index++) {	
				for (j = 0; j < dvert[i].totweight; j++) {
					/* does this vertex belong to nominated vertex group? */
					if (dvert[i].dw[j].def_nr == dgroup) {
						dm->getVertCo(dm, i, co);
						dm->getVertNo(dm, i, nor);
						VecAddf(vec, vec, co);
						VecAddf(normal, normal, nor);
						count++;
						break;
					}
					
				}
			}
			
			
			/* calculate averages of normal and coordinates */
			if (count > 0) {
				VecMulf(vec, 1.0f / count);
				VecMulf(normal, 1.0f / count);
			}
			
			
			/* derive the rotation from the average normal: 
			 *		- code taken from transform_manipulator.c, 
			 *			calc_manipulator_stats, V3D_MANIP_NORMAL case
			 */
			/*	we need the transpose of the inverse for a normal... */
			Mat3CpyMat4(imat, ob->obmat);
			
			Mat3Inv(tmat, imat);
			Mat3Transp(tmat);
			Mat3MulVecfl(tmat, normal);
			
			Normalize(normal);
			VECCOPY(plane, tmat[1]);
			
			VECCOPY(tmat[2], normal);
			Crossf(tmat[0], normal, plane);
			Crossf(tmat[1], tmat[2], tmat[0]);
			
			Mat4CpyMat3(mat, tmat);
			Mat4Ortho(mat);
			
			
			/* apply the average coordinate as the new location */
			VecMat4MulVecfl(tvec, ob->obmat, vec);
			VECCOPY(mat[3], tvec);
		}
	}
	
	/* free temporary DerivedMesh created (in EditMode case) */
	if (G.editMesh) {
		if (dm) dm->release(dm);
	}
}

/* function that sets the given matrix based on given vertex group in lattice */
static void contarget_get_lattice_mat (Object *ob, char *substring, float mat[][4])
{
	Lattice *lt= (Lattice *)ob->data;
	
	DispList *dl = find_displist(&ob->disp, DL_VERTS);
	float *co = dl?dl->verts:NULL;
	BPoint *bp = lt->def;
	
	MDeformVert *dvert = lt->dvert;
	int tot_verts= lt->pntsu*lt->pntsv*lt->pntsw;
	float vec[3]= {0.0f, 0.0f, 0.0f}, tvec[3];
	int dgroup=0, grouped=0;
	int i, n;
	
	/* initialize target matrix using target matrix */
	Mat4CpyMat4(mat, ob->obmat);
	
	/* get index of vertex group */
	dgroup = get_named_vertexgroup_num(ob, substring);
	if (dgroup < 0) return;
	if (dvert == NULL) return;
	
	/* 1. Loop through control-points checking if in nominated vertex-group.
	 * 2. If it is, add it to vec to find the average point.
	 */
	for (i=0; i < tot_verts; i++, dvert++) {
		for (n= 0; n < dvert->totweight; n++) {
			/* found match - vert is in vgroup */
			if (dvert->dw[n].def_nr == dgroup) {
				/* copy coordinates of point to temporary vector, then add to find average */
				if (co)
					memcpy(tvec, co, 3*sizeof(float));
				else
					memcpy(tvec, bp->vec, 3*sizeof(float));
					
				VecAddf(vec, vec, tvec);
				grouped++;
				
				break;
			}
		}
		
		/* advance pointer to coordinate data */
		if (co) co+= 3;
		else bp++;
	}
	
	/* find average location, then multiply by ob->obmat to find world-space location */
	if (grouped)
		VecMulf(vec, 1.0f / grouped);
	VecMat4MulVecfl(tvec, ob->obmat, vec);
	
	/* copy new location to matrix */
	VECCOPY(mat[3], tvec);
}

/* generic function to get the appropriate matrix for most target cases */
/* The cases where the target can be object data have not been implemented */
static void constraint_target_to_mat4 (Object *ob, char *substring, float mat[][4], short from, short to, float headtail)
{
	/*	Case OBJECT */
	if (!strlen(substring)) {
		Mat4CpyMat4(mat, ob->obmat);
		constraint_mat_convertspace(ob, NULL, mat, from, to);
	}
	/* 	Case VERTEXGROUP */
	/* Current method just takes the average location of all the points in the
	 * VertexGroup, and uses that as the location value of the targets. Where 
	 * possible, the orientation will also be calculated, by calculating an
	 * 'average' vertex normal, and deriving the rotaation from that.
	 *
	 * NOTE: EditMode is not currently supported, and will most likely remain that
	 *		way as constraints can only really affect things on object/bone level.
	 */
	else if (ob->type == OB_MESH) {
		contarget_get_mesh_mat(ob, substring, mat);
		constraint_mat_convertspace(ob, NULL, mat, from, to);
	}
	else if (ob->type == OB_LATTICE) {
		contarget_get_lattice_mat(ob, substring, mat);
		constraint_mat_convertspace(ob, NULL, mat, from, to);
	}
	/*	Case BONE */
	else {
		bPoseChannel *pchan;
		
		pchan = get_pose_channel(ob->pose, substring);
		if (pchan) {
			/* Multiply the PoseSpace accumulation/final matrix for this
			 * PoseChannel by the Armature Object's Matrix to get a worldspace
			 * matrix.
			 */
			if (headtail < 0.000001) {
				/* skip length interpolation if set to head */
				Mat4MulMat4(mat, pchan->pose_mat, ob->obmat);
			}
			else {
				float tempmat[4][4], loc[3];
				
				/* interpolate along length of bone */
				VecLerpf(loc, pchan->pose_head, pchan->pose_tail, headtail);	
				
				/* use interpolated distance for subtarget */
				Mat4CpyMat4(tempmat, pchan->pose_mat);	
				VecCopyf(tempmat[3], loc);
				
				Mat4MulMat4(mat, tempmat, ob->obmat);
			}
		} 
		else
			Mat4CpyMat4(mat, ob->obmat);
			
		/* convert matrix space as required */
		constraint_mat_convertspace(ob, pchan, mat, from, to);
	}
}

/* ************************* Specific Constraints ***************************** */
/* Each constraint defines a set of functions, which will be called at the appropriate
 * times. In addition to this, each constraint should have a type-info struct, where
 * its functions are attached for use. 
 */
 
/* Template for type-info data:
 *	- make a copy of this when creating new constraints, and just change the functions
 *	  pointed to as necessary
 *	- although the naming of functions doesn't matter, it would help for code
 *	  readability, to follow the same naming convention as is presented here
 * 	- any functions that a constraint doesn't need to define, don't define
 *	  for such cases, just use NULL 
 *	- these should be defined after all the functions have been defined, so that
 * 	  forward-definitions/prototypes don't need to be used!
 *	- keep this copy #if-def'd so that future constraints can get based off this
 */
#if 0
static bConstraintTypeInfo CTI_CONSTRNAME = {
	CONSTRAINT_TYPE_CONSTRNAME, /* type */
	sizeof(bConstrNameConstraint), /* size */
	"ConstrName", /* name */
	"bConstrNameConstraint", /* struct name */
	constrname_free, /* free data */
	constrname_relink, /* relink data */
	constrname_copy, /* copy data */
	constrname_new_data, /* new data */
	constrname_get_tars, /* get constraint targets */
	constrname_flush_tars, /* flush constraint targets */
	constrname_get_tarmat, /* get target matrix */
	constrname_evaluate /* evaluate */
};
#endif

/* This function should be used for the get_target_matrix member of all 
 * constraints that are not picky about what happens to their target matrix.
 */
static void default_get_tarmat (bConstraint *con, bConstraintOb *cob, bConstraintTarget *ct, float ctime)
{
	if (VALID_CONS_TARGET(ct))
		constraint_target_to_mat4(ct->tar, ct->subtarget, ct->matrix, CONSTRAINT_SPACE_WORLD, ct->space, con->headtail);
	else if (ct)
		Mat4One(ct->matrix);
}

/* This following macro should be used for all standard single-target *_get_tars functions 
 * to save typing and reduce maintainance woes.
 * (Hopefully all compilers will be happy with the lines with just a space on them. Those are
 *  really just to help this code easier to read)
 */
#define SINGLETARGET_GET_TARS(con, datatar, datasubtarget, ct, list) \
	{ \
		ct= MEM_callocN(sizeof(bConstraintTarget), "tempConstraintTarget"); \
		 \
		ct->tar= datatar; \
		strcpy(ct->subtarget, datasubtarget); \
		ct->space= con->tarspace; \
		ct->flag= CONSTRAINT_TAR_TEMP; \
		 \
		if (ct->tar) { \
			if ((ct->tar->type==OB_ARMATURE) && (ct->subtarget[0])) ct->type = CONSTRAINT_OBTYPE_BONE; \
			else if (ELEM(ct->tar->type, OB_MESH, OB_LATTICE) && (ct->subtarget[0])) ct->type = CONSTRAINT_OBTYPE_VERT; \
			else ct->type = CONSTRAINT_OBTYPE_OBJECT; \
		} \
		 \
		BLI_addtail(list, ct); \
	}
	
/* This following macro should be used for all standard single-target *_get_tars functions 
 * to save typing and reduce maintainance woes. It does not do the subtarget related operations
 * (Hopefully all compilers will be happy with the lines with just a space on them. Those are
 *  really just to help this code easier to read)
 */
#define SINGLETARGETNS_GET_TARS(con, datatar, ct, list) \
	{ \
		ct= MEM_callocN(sizeof(bConstraintTarget), "tempConstraintTarget"); \
		 \
		ct->tar= datatar; \
		ct->space= con->tarspace; \
		ct->flag= CONSTRAINT_TAR_TEMP; \
		 \
		if (ct->tar) ct->type = CONSTRAINT_OBTYPE_OBJECT; \
		 \
		BLI_addtail(list, ct); \
	}

/* This following macro should be used for all standard single-target *_flush_tars functions
 * to save typing and reduce maintainance woes.
 * Note: the pointer to ct will be changed to point to the next in the list (as it gets removed)
 * (Hopefully all compilers will be happy with the lines with just a space on them. Those are
 *  really just to help this code easier to read)
 */
#define SINGLETARGET_FLUSH_TARS(con, datatar, datasubtarget, ct, list, nocopy) \
	{ \
		if (ct) { \
			bConstraintTarget *ctn = ct->next; \
			if (nocopy == 0) { \
				datatar= ct->tar; \
				strcpy(datasubtarget, ct->subtarget); \
				con->tarspace= ct->space; \
			} \
			 \
			BLI_freelinkN(list, ct); \
			ct= ctn; \
		} \
	}
	
/* This following macro should be used for all standard single-target *_flush_tars functions
 * to save typing and reduce maintainance woes. It does not do the subtarget related operations.
 * Note: the pointer to ct will be changed to point to the next in the list (as it gets removed)
 * (Hopefully all compilers will be happy with the lines with just a space on them. Those are
 *  really just to help this code easier to read)
 */
#define SINGLETARGETNS_FLUSH_TARS(con, datatar, ct, list, nocopy) \
	{ \
		if (ct) { \
			bConstraintTarget *ctn = ct->next; \
			if (nocopy == 0) { \
				datatar= ct->tar; \
				con->tarspace= ct->space; \
			} \
			 \
			BLI_freelinkN(list, ct); \
			ct= ctn; \
		} \
	}
 
/* --------- ChildOf Constraint ------------ */

static void childof_new_data (void *cdata)
{
	bChildOfConstraint *data= (bChildOfConstraint *)cdata;
	
	data->flag = (CHILDOF_LOCX | CHILDOF_LOCY | CHILDOF_LOCZ |
					CHILDOF_ROTX |CHILDOF_ROTY | CHILDOF_ROTZ |
					CHILDOF_SIZEX | CHILDOF_SIZEY | CHILDOF_SIZEZ);
	Mat4One(data->invmat);
}

static int childof_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bChildOfConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void childof_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bChildOfConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void childof_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bChildOfConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	/* only evaluate if there is a target */
	if (VALID_CONS_TARGET(ct)) {
		float parmat[4][4], invmat[4][4], tempmat[4][4];
		float loc[3], eul[3], size[3];
		float loco[3], eulo[3], sizo[3];
		
		/* get offset (parent-inverse) matrix */
		Mat4CpyMat4(invmat, data->invmat);
		
		/* extract components of both matrices */
		VECCOPY(loc, ct->matrix[3]);
		Mat4ToEul(ct->matrix, eul);
		Mat4ToSize(ct->matrix, size);
		
		VECCOPY(loco, invmat[3]);
		Mat4ToEul(invmat, eulo);
		Mat4ToSize(invmat, sizo);
		
		/* disable channels not enabled */
		if (!(data->flag & CHILDOF_LOCX)) loc[0]= loco[0]= 0.0f;
		if (!(data->flag & CHILDOF_LOCY)) loc[1]= loco[1]= 0.0f;
		if (!(data->flag & CHILDOF_LOCZ)) loc[2]= loco[2]= 0.0f;
		if (!(data->flag & CHILDOF_ROTX)) eul[0]= eulo[0]= 0.0f;
		if (!(data->flag & CHILDOF_ROTY)) eul[1]= eulo[1]= 0.0f;
		if (!(data->flag & CHILDOF_ROTZ)) eul[2]= eulo[2]= 0.0f;
		if (!(data->flag & CHILDOF_SIZEX)) size[0]= sizo[0]= 1.0f;
		if (!(data->flag & CHILDOF_SIZEY)) size[1]= sizo[1]= 1.0f;
		if (!(data->flag & CHILDOF_SIZEZ)) size[2]= sizo[2]= 1.0f;
		
		/* make new target mat and offset mat */
		LocEulSizeToMat4(ct->matrix, loc, eul, size);
		LocEulSizeToMat4(invmat, loco, eulo, sizo);
		
		/* multiply target (parent matrix) by offset (parent inverse) to get 
		 * the effect of the parent that will be exherted on the owner
		 */
		Mat4MulMat4(parmat, invmat, ct->matrix);
		
		/* now multiply the parent matrix by the owner matrix to get the 
		 * the effect of this constraint (i.e.  owner is 'parented' to parent)
		 */
		Mat4CpyMat4(tempmat, cob->matrix);
		Mat4MulMat4(cob->matrix, tempmat, parmat); 
	}
}

static bConstraintTypeInfo CTI_CHILDOF = {
	CONSTRAINT_TYPE_CHILDOF, /* type */
	sizeof(bChildOfConstraint), /* size */
	"ChildOf", /* name */
	"bChildOfConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	childof_new_data, /* new data */
	childof_get_tars, /* get constraint targets */
	childof_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get a target matrix */
	childof_evaluate /* evaluate */
};

/* -------- TrackTo Constraint ------- */

static void trackto_new_data (void *cdata)
{
	bTrackToConstraint *data= (bTrackToConstraint *)cdata;
	
	data->reserved1 = TRACK_Y;
	data->reserved2 = UP_Z;
}	

static int trackto_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bTrackToConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void trackto_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bTrackToConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}


static int basis_cross (int n, int m)
{
	switch (n-m) {
		case 1: 
		case -2:
			return 1;
			
		case -1: 
		case 2:
			return -1;
			
		default:
			return 0;
	}
}

static void vectomat (float *vec, float *target_up, short axis, short upflag, short flags, float m[][3])
{
	float n[3];
	float u[3]; /* vector specifying the up axis */
	float proj[3];
	float right[3];
	float neg = -1;
	int right_index;
	
	VecCopyf(n, vec);
	if (Normalize(n) == 0.0) { 
		n[0] = 0.0;
		n[1] = 0.0;
		n[2] = 1.0;
	}
	if (axis > 2) axis -= 3;
	else VecMulf(n,-1);

	/* n specifies the transformation of the track axis */
	if (flags & TARGET_Z_UP) { 
		/* target Z axis is the global up axis */
		u[0] = target_up[0];
		u[1] = target_up[1];
		u[2] = target_up[2];
	}
	else { 
		/* world Z axis is the global up axis */
		u[0] = 0;
		u[1] = 0;
		u[2] = 1;
	}

	/* project the up vector onto the plane specified by n */
	Projf(proj, u, n); /* first u onto n... */
	VecSubf(proj, u, proj); /* then onto the plane */
	/* proj specifies the transformation of the up axis */

	if (Normalize(proj) == 0.0) { /* degenerate projection */
		proj[0] = 0.0;
		proj[1] = 1.0;
		proj[2] = 0.0;
	}

	/* Normalized cross product of n and proj specifies transformation of the right axis */
	Crossf(right, proj, n);
	Normalize(right);

	if (axis != upflag) {
		right_index = 3 - axis - upflag;
		neg = (float)basis_cross(axis, upflag);
		
		/* account for up direction, track direction */
		m[right_index][0] = neg * right[0];
		m[right_index][1] = neg * right[1];
		m[right_index][2] = neg * right[2];
		
		m[upflag][0] = proj[0];
		m[upflag][1] = proj[1];
		m[upflag][2] = proj[2];
		
		m[axis][0] = n[0];
		m[axis][1] = n[1];
		m[axis][2] = n[2];
	}
	/* identity matrix - don't do anything if the two axes are the same */
	else {
		m[0][0]= m[1][1]= m[2][2]= 1.0;
		m[0][1]= m[0][2]= m[0][3]= 0.0;
		m[1][0]= m[1][2]= m[1][3]= 0.0;
		m[2][0]= m[2][1]= m[2][3]= 0.0;
	}
}


static void trackto_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bTrackToConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	if (VALID_CONS_TARGET(ct)) {
		float size[3], vec[3];
		float totmat[3][3];
		float tmat[4][4];
		
		/* Get size property, since ob->size is only the object's own relative size, not its global one */
		Mat4ToSize(cob->matrix, size);
		
		/* Clear the object's rotation */ 	
		cob->matrix[0][0]=size[0];
		cob->matrix[0][1]=0;
		cob->matrix[0][2]=0;
		cob->matrix[1][0]=0;
		cob->matrix[1][1]=size[1];
		cob->matrix[1][2]=0;
		cob->matrix[2][0]=0;
		cob->matrix[2][1]=0;
		cob->matrix[2][2]=size[2];
		
		/* targetmat[2] instead of ownermat[2] is passed to vectomat
		 * for backwards compatability it seems... (Aligorith)
		 */
		VecSubf(vec, cob->matrix[3], ct->matrix[3]);
		vectomat(vec, ct->matrix[2], 
				(short)data->reserved1, (short)data->reserved2, 
				data->flags, totmat);
		
		Mat4CpyMat4(tmat, cob->matrix);
		Mat4MulMat34(cob->matrix, totmat, tmat);
	}
}

static bConstraintTypeInfo CTI_TRACKTO = {
	CONSTRAINT_TYPE_TRACKTO, /* type */
	sizeof(bTrackToConstraint), /* size */
	"TrackTo", /* name */
	"bTrackToConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	trackto_new_data, /* new data */
	trackto_get_tars, /* get constraint targets */
	trackto_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	trackto_evaluate /* evaluate */
};

/* --------- Inverse-Kinemetics --------- */

static void kinematic_new_data (void *cdata)
{
	bKinematicConstraint *data= (bKinematicConstraint *)cdata;
	
	data->weight= (float)1.0;
	data->orientweight= (float)1.0;
	data->iterations = 500;
	data->flag= CONSTRAINT_IK_TIP|CONSTRAINT_IK_STRETCH|CONSTRAINT_IK_POS;
}

static int kinematic_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bKinematicConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints is used twice here */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		SINGLETARGET_GET_TARS(con, data->poletar, data->polesubtarget, ct, list)
		
		return 2;
	}
	
	return 0;
}

static void kinematic_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bKinematicConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
		SINGLETARGET_FLUSH_TARS(con, data->poletar, data->polesubtarget, ct, list, nocopy)
	}
}

static void kinematic_get_tarmat (bConstraint *con, bConstraintOb *cob, bConstraintTarget *ct, float ctime)
{
	bKinematicConstraint *data= con->data;
	
	if (VALID_CONS_TARGET(ct)) 
		constraint_target_to_mat4(ct->tar, ct->subtarget, ct->matrix, CONSTRAINT_SPACE_WORLD, ct->space, con->headtail);
	else if (ct) {
		if (data->flag & CONSTRAINT_IK_AUTO) {
			Object *ob= cob->ob;
			
			if (ob == NULL) {
				Mat4One(ct->matrix);
			}
			else {
				float vec[3];
				/* move grabtarget into world space */
				VECCOPY(vec, data->grabtarget);
				Mat4MulVecfl(ob->obmat, vec);
				Mat4CpyMat4(ct->matrix, ob->obmat);
				VECCOPY(ct->matrix[3], vec);
			}
		}
		else
			Mat4One(ct->matrix);
	}
}

static bConstraintTypeInfo CTI_KINEMATIC = {
	CONSTRAINT_TYPE_KINEMATIC, /* type */
	sizeof(bKinematicConstraint), /* size */
	"IK", /* name */
	"bKinematicConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	kinematic_new_data, /* new data */
	kinematic_get_tars, /* get constraint targets */
	kinematic_flush_tars, /* flush constraint targets */
	kinematic_get_tarmat, /* get target matrix */
	NULL /* evaluate - solved as separate loop */
};

/* -------- Follow-Path Constraint ---------- */

static void followpath_new_data (void *cdata)
{
	bFollowPathConstraint *data= (bFollowPathConstraint *)cdata;
	
	data->trackflag = TRACK_Y;
	data->upflag = UP_Z;
	data->offset = 0;
	data->followflag = 0;
}

static int followpath_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bFollowPathConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints without subtargets */
		SINGLETARGETNS_GET_TARS(con, data->tar, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void followpath_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bFollowPathConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGETNS_FLUSH_TARS(con, data->tar, ct, list, nocopy)
	}
}

static void followpath_get_tarmat (bConstraint *con, bConstraintOb *cob, bConstraintTarget *ct, float ctime)
{
	bFollowPathConstraint *data= con->data;
	
	if (VALID_CONS_TARGET(ct)) {
		Curve *cu= ct->tar->data;
		float q[4], vec[4], dir[3], quat[4], x1;
		float totmat[4][4];
		float curvetime;
		
		Mat4One(totmat);
		Mat4One(ct->matrix);
		
		/* note: when creating constraints that follow path, the curve gets the CU_PATH set now,
		 *		currently for paths to work it needs to go through the bevlist/displist system (ton) 
		 */
		
		/* only happens on reload file, but violates depsgraph still... fix! */
		if (cu->path==NULL || cu->path->data==NULL) 
			makeDispListCurveTypes(ct->tar, 0);
		
		if (cu->path && cu->path->data) {
			curvetime= bsystem_time(ct->tar, (float)ctime, 0.0) - data->offset;
			
			if (calc_ipo_spec(cu->ipo, CU_SPEED, &curvetime)==0) {
				curvetime /= cu->pathlen;
				CLAMP(curvetime, 0.0, 1.0);
			}
			
			if ( where_on_path(ct->tar, curvetime, vec, dir) ) {
				if (data->followflag) {
					vectoquat(dir, (short) data->trackflag, (short) data->upflag, quat);
					
					Normalize(dir);
					q[0]= (float)cos(0.5*vec[3]);
					x1= (float)sin(0.5*vec[3]);
					q[1]= -x1*dir[0];
					q[2]= -x1*dir[1];
					q[3]= -x1*dir[2];
					QuatMul(quat, q, quat);
					
					QuatToMat4(quat, totmat);
				}
				VECCOPY(totmat[3], vec);
				
				Mat4MulSerie(ct->matrix, ct->tar->obmat, totmat, NULL, NULL, NULL, NULL, NULL, NULL);
			}
		}
	}
	else if (ct)
		Mat4One(ct->matrix);
}

static void followpath_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bConstraintTarget *ct= targets->first;
	
	/* only evaluate if there is a target */
	if (VALID_CONS_TARGET(ct)) {
		float obmat[4][4];
		float size[3], obsize[3];
		
		/* get Object local transform (loc/rot/size) to determine transformation from path */
		//object_to_mat4(ob, obmat);
		Mat4CpyMat4(obmat, cob->matrix); // FIXME!!!
		
		/* get scaling of object before applying constraint */
		Mat4ToSize(cob->matrix, size);
		
		/* apply targetmat - containing location on path, and rotation */
		Mat4MulSerie(cob->matrix, ct->matrix, obmat, NULL, NULL, NULL, NULL, NULL, NULL);
		
		/* un-apply scaling caused by path */
		Mat4ToSize(cob->matrix, obsize);
		if (obsize[0])
			VecMulf(cob->matrix[0], size[0] / obsize[0]);
		if (obsize[1])
			VecMulf(cob->matrix[1], size[1] / obsize[1]);
		if (obsize[2])
			VecMulf(cob->matrix[2], size[2] / obsize[2]);
	}
}

static bConstraintTypeInfo CTI_FOLLOWPATH = {
	CONSTRAINT_TYPE_FOLLOWPATH, /* type */
	sizeof(bFollowPathConstraint), /* size */
	"Follow Path", /* name */
	"bFollowPathConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	followpath_new_data, /* new data */
	followpath_get_tars, /* get constraint targets */
	followpath_flush_tars, /* flush constraint targets */
	followpath_get_tarmat, /* get target matrix */
	followpath_evaluate /* evaluate */
};

/* --------- Limit Location --------- */


static void loclimit_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bLocLimitConstraint *data = con->data;
	
	if (data->flag & LIMIT_XMIN) {
		if (cob->matrix[3][0] < data->xmin)
			cob->matrix[3][0] = data->xmin;
	}
	if (data->flag & LIMIT_XMAX) {
		if (cob->matrix[3][0] > data->xmax)
			cob->matrix[3][0] = data->xmax;
	}
	if (data->flag & LIMIT_YMIN) {
		if (cob->matrix[3][1] < data->ymin)
			cob->matrix[3][1] = data->ymin;
	}
	if (data->flag & LIMIT_YMAX) {
		if (cob->matrix[3][1] > data->ymax)
			cob->matrix[3][1] = data->ymax;
	}
	if (data->flag & LIMIT_ZMIN) {
		if (cob->matrix[3][2] < data->zmin) 
			cob->matrix[3][2] = data->zmin;
	}
	if (data->flag & LIMIT_ZMAX) {
		if (cob->matrix[3][2] > data->zmax)
			cob->matrix[3][2] = data->zmax;
	}
}

static bConstraintTypeInfo CTI_LOCLIMIT = {
	CONSTRAINT_TYPE_LOCLIMIT, /* type */
	sizeof(bLocLimitConstraint), /* size */
	"Limit Location", /* name */
	"bLocLimitConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	NULL, /* new data */
	NULL, /* get constraint targets */
	NULL, /* flush constraint targets */
	NULL, /* get target matrix */
	loclimit_evaluate /* evaluate */
};

/* -------- Limit Rotation --------- */

static void rotlimit_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bRotLimitConstraint *data = con->data;
	float loc[3];
	float eul[3];
	float size[3];
	
	VECCOPY(loc, cob->matrix[3]);
	Mat4ToSize(cob->matrix, size);
	
	Mat4ToEul(cob->matrix, eul);
	
	/* eulers: radians to degrees! */
	eul[0] = (eul[0] / M_PI * 180);
	eul[1] = (eul[1] / M_PI * 180);
	eul[2] = (eul[2] / M_PI * 180);
	
	/* limiting of euler values... */
	if (data->flag & LIMIT_XROT) {
		if (eul[0] < data->xmin) 
			eul[0] = data->xmin;
			
		if (eul[0] > data->xmax)
			eul[0] = data->xmax;
	}
	if (data->flag & LIMIT_YROT) {
		if (eul[1] < data->ymin)
			eul[1] = data->ymin;
			
		if (eul[1] > data->ymax)
			eul[1] = data->ymax;
	}
	if (data->flag & LIMIT_ZROT) {
		if (eul[2] < data->zmin)
			eul[2] = data->zmin;
			
		if (eul[2] > data->zmax)
			eul[2] = data->zmax;
	}
		
	/* eulers: degrees to radians ! */
	eul[0] = (eul[0] / 180 * M_PI); 
	eul[1] = (eul[1] / 180 * M_PI);
	eul[2] = (eul[2] / 180 * M_PI);
	
	LocEulSizeToMat4(cob->matrix, loc, eul, size);
}

static bConstraintTypeInfo CTI_ROTLIMIT = {
	CONSTRAINT_TYPE_ROTLIMIT, /* type */
	sizeof(bRotLimitConstraint), /* size */
	"Limit Rotation", /* name */
	"bRotLimitConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	NULL, /* new data */
	NULL, /* get constraint targets */
	NULL, /* flush constraint targets */
	NULL, /* get target matrix */
	rotlimit_evaluate /* evaluate */
};

/* --------- Limit Scaling --------- */


static void sizelimit_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bSizeLimitConstraint *data = con->data;
	float obsize[3], size[3];
	
	Mat4ToSize(cob->matrix, size);
	Mat4ToSize(cob->matrix, obsize);
	
	if (data->flag & LIMIT_XMIN) {
		if (size[0] < data->xmin) 
			size[0] = data->xmin;	
	}
	if (data->flag & LIMIT_XMAX) {
		if (size[0] > data->xmax) 
			size[0] = data->xmax;
	}
	if (data->flag & LIMIT_YMIN) {
		if (size[1] < data->ymin) 
			size[1] = data->ymin;	
	}
	if (data->flag & LIMIT_YMAX) {
		if (size[1] > data->ymax) 
			size[1] = data->ymax;
	}
	if (data->flag & LIMIT_ZMIN) {
		if (size[2] < data->zmin) 
			size[2] = data->zmin;	
	}
	if (data->flag & LIMIT_ZMAX) {
		if (size[2] > data->zmax) 
			size[2] = data->zmax;
	}
	
	if (obsize[0]) 
		VecMulf(cob->matrix[0], size[0]/obsize[0]);
	if (obsize[1]) 
		VecMulf(cob->matrix[1], size[1]/obsize[1]);
	if (obsize[2]) 
		VecMulf(cob->matrix[2], size[2]/obsize[2]);
}

static bConstraintTypeInfo CTI_SIZELIMIT = {
	CONSTRAINT_TYPE_SIZELIMIT, /* type */
	sizeof(bSizeLimitConstraint), /* size */
	"Limit Scaling", /* name */
	"bSizeLimitConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	NULL, /* new data */
	NULL, /* get constraint targets */
	NULL, /* flush constraint targets */
	NULL, /* get target matrix */
	sizelimit_evaluate /* evaluate */
};

/* ----------- Copy Location ------------- */

static void loclike_new_data (void *cdata)
{
	bLocateLikeConstraint *data= (bLocateLikeConstraint *)cdata;
	
	data->flag = LOCLIKE_X|LOCLIKE_Y|LOCLIKE_Z;
}

static int loclike_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bLocateLikeConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void loclike_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bLocateLikeConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void loclike_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bLocateLikeConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	if (VALID_CONS_TARGET(ct)) {
		float offset[3] = {0.0f, 0.0f, 0.0f};
		
		if (data->flag & LOCLIKE_OFFSET)
			VECCOPY(offset, cob->matrix[3]);
			
		if (data->flag & LOCLIKE_X) {
			cob->matrix[3][0] = ct->matrix[3][0];
			
			if (data->flag & LOCLIKE_X_INVERT) cob->matrix[3][0] *= -1;
			cob->matrix[3][0] += offset[0];
		}
		if (data->flag & LOCLIKE_Y) {
			cob->matrix[3][1] = ct->matrix[3][1];
			
			if (data->flag & LOCLIKE_Y_INVERT) cob->matrix[3][1] *= -1;
			cob->matrix[3][1] += offset[1];
		}
		if (data->flag & LOCLIKE_Z) {
			cob->matrix[3][2] = ct->matrix[3][2];
			
			if (data->flag & LOCLIKE_Z_INVERT) cob->matrix[3][2] *= -1;
			cob->matrix[3][2] += offset[2];
		}
	}
}

static bConstraintTypeInfo CTI_LOCLIKE = {
	CONSTRAINT_TYPE_LOCLIKE, /* type */
	sizeof(bLocateLikeConstraint), /* size */
	"Copy Location", /* name */
	"bLocateLikeConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	loclike_new_data, /* new data */
	loclike_get_tars, /* get constraint targets */
	loclike_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	loclike_evaluate /* evaluate */
};

/* ----------- Copy Rotation ------------- */

static void rotlike_new_data (void *cdata)
{
	bRotateLikeConstraint *data= (bRotateLikeConstraint *)cdata;
	
	data->flag = ROTLIKE_X|ROTLIKE_Y|ROTLIKE_Z;
}

static int rotlike_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bRotateLikeConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void rotlike_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bRotateLikeConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void rotlike_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bRotateLikeConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	if (VALID_CONS_TARGET(ct)) {
		float	loc[3];
		float	eul[3], obeul[3];
		float	size[3];
		
		VECCOPY(loc, cob->matrix[3]);
		Mat4ToSize(cob->matrix, size);
		
		Mat4ToEul(ct->matrix, eul);
		Mat4ToEul(cob->matrix, obeul);
		
		if ((data->flag & ROTLIKE_X)==0)
			eul[0] = obeul[0];
		else {
			if (data->flag & ROTLIKE_OFFSET)
				euler_rot(eul, obeul[0], 'x');
			
			if (data->flag & ROTLIKE_X_INVERT)
				eul[0] *= -1;
		}
		
		if ((data->flag & ROTLIKE_Y)==0)
			eul[1] = obeul[1];
		else {
			if (data->flag & ROTLIKE_OFFSET)
				euler_rot(eul, obeul[1], 'y');
			
			if (data->flag & ROTLIKE_Y_INVERT)
				eul[1] *= -1;
		}
		
		if ((data->flag & ROTLIKE_Z)==0)
			eul[2] = obeul[2];
		else {
			if (data->flag & ROTLIKE_OFFSET)
				euler_rot(eul, obeul[2], 'z');
			
			if (data->flag & ROTLIKE_Z_INVERT)
				eul[2] *= -1;
		}
		
		compatible_eul(eul, obeul);
		LocEulSizeToMat4(cob->matrix, loc, eul, size);
	}
}

static bConstraintTypeInfo CTI_ROTLIKE = {
	CONSTRAINT_TYPE_ROTLIKE, /* type */
	sizeof(bRotateLikeConstraint), /* size */
	"Copy Rotation", /* name */
	"bRotateLikeConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	rotlike_new_data, /* new data */
	rotlike_get_tars, /* get constraint targets */
	rotlike_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	rotlike_evaluate /* evaluate */
};

/* ---------- Copy Scaling ---------- */

static void sizelike_new_data (void *cdata)
{
	bSizeLikeConstraint *data= (bSizeLikeConstraint *)cdata;
	
	data->flag = SIZELIKE_X|SIZELIKE_Y|SIZELIKE_Z;
}

static int sizelike_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bSizeLikeConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void sizelike_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bSizeLikeConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void sizelike_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bSizeLikeConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	if (VALID_CONS_TARGET(ct)) {
		float obsize[3], size[3];
		
		Mat4ToSize(ct->matrix, size);
		Mat4ToSize(cob->matrix, obsize);
		
		if ((data->flag & SIZELIKE_X) && (obsize[0] != 0)) {
			if (data->flag & SIZELIKE_OFFSET) {
				size[0] += (obsize[0] - 1.0f);
				VecMulf(cob->matrix[0], size[0] / obsize[0]);
			}
			else
				VecMulf(cob->matrix[0], size[0] / obsize[0]);
		}
		if ((data->flag & SIZELIKE_Y) && (obsize[1] != 0)) {
			if (data->flag & SIZELIKE_OFFSET) {
				size[1] += (obsize[1] - 1.0f);
				VecMulf(cob->matrix[1], size[1] / obsize[1]);
			}
			else
				VecMulf(cob->matrix[1], size[1] / obsize[1]);
		}
		if ((data->flag & SIZELIKE_Z) && (obsize[2] != 0)) {
			if (data->flag & SIZELIKE_OFFSET) {
				size[2] += (obsize[2] - 1.0f);
				VecMulf(cob->matrix[2], size[2] / obsize[2]);
			}
			else
				VecMulf(cob->matrix[2], size[2] / obsize[2]);
		}
	}
}

static bConstraintTypeInfo CTI_SIZELIKE = {
	CONSTRAINT_TYPE_SIZELIKE, /* type */
	sizeof(bSizeLikeConstraint), /* size */
	"Copy Scale", /* name */
	"bSizeLikeConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	sizelike_new_data, /* new data */
	sizelike_get_tars, /* get constraint targets */
	sizelike_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	sizelike_evaluate /* evaluate */
};

/* ----------- Python Constraint -------------- */

static void pycon_free (bConstraint *con)
{
	bPythonConstraint *data= con->data;
	
	/* id-properties */
	IDP_FreeProperty(data->prop);
	MEM_freeN(data->prop);
	
	/* multiple targets */
	BLI_freelistN(&data->targets);
}	

static void pycon_relink (bConstraint *con)
{
	bPythonConstraint *data= con->data;
	
	ID_NEW(data->text);
}

static void pycon_copy (bConstraint *con, bConstraint *srccon)
{
	bPythonConstraint *pycon = (bPythonConstraint *)con->data;
	bPythonConstraint *opycon = (bPythonConstraint *)srccon->data;
	
	pycon->prop = IDP_CopyProperty(opycon->prop);
	duplicatelist(&pycon->targets, &opycon->targets);
}

static void pycon_new_data (void *cdata)
{
	bPythonConstraint *data= (bPythonConstraint *)cdata;
	
	/* everything should be set correctly by calloc, except for the prop->type constant.*/
	data->prop = MEM_callocN(sizeof(IDProperty), "PyConstraintProps");
	data->prop->type = IDP_GROUP;
}

static int pycon_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bPythonConstraint *data= con->data;
		
		list->first = data->targets.first;
		list->last = data->targets.last;
		
		return data->tarnum;
	}
	
	return 0;
}

/* Whether this approach is maintained remains to be seen (aligorith) */
static void pycon_get_tarmat (bConstraint *con, bConstraintOb *cob, bConstraintTarget *ct, float ctime)
{
	bPythonConstraint *data= con->data;
	
	if (VALID_CONS_TARGET(ct)) {
		/* special exception for curves - depsgraph issues */
		if (ct->tar->type == OB_CURVE) {
			Curve *cu= ct->tar->data;
			
			/* this check is to make sure curve objects get updated on file load correctly.*/
			if (cu->path==NULL || cu->path->data==NULL) /* only happens on reload file, but violates depsgraph still... fix! */
				makeDispListCurveTypes(ct->tar, 0);				
		}
		
		/* firstly calculate the matrix the normal way, then let the py-function override
		 * this matrix if it needs to do so
		 */
		constraint_target_to_mat4(ct->tar, ct->subtarget, ct->matrix, CONSTRAINT_SPACE_WORLD, ct->space, con->headtail);
		BPY_pyconstraint_target(data, ct);
	}
	else if (ct)
		Mat4One(ct->matrix);
}

static void pycon_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bPythonConstraint *data= con->data;
	
/* currently removed, until I this can be re-implemented for multiple targets */
#if 0
	/* Firstly, run the 'driver' function which has direct access to the objects involved 
	 * Technically, this is potentially dangerous as users may abuse this and cause dependency-problems,
	 * but it also allows certain 'clever' rigging hacks to work.
	 */
	BPY_pyconstraint_driver(data, cob, targets);
#endif
	
	/* Now, run the actual 'constraint' function, which should only access the matrices */
	BPY_pyconstraint_eval(data, cob, targets);
}

static bConstraintTypeInfo CTI_PYTHON = {
	CONSTRAINT_TYPE_PYTHON, /* type */
	sizeof(bPythonConstraint), /* size */
	"Script", /* name */
	"bPythonConstraint", /* struct name */
	pycon_free, /* free data */
	pycon_relink, /* relink data */
	pycon_copy, /* copy data */
	pycon_new_data, /* new data */
	pycon_get_tars, /* get constraint targets */
	NULL, /* flush constraint targets */
	pycon_get_tarmat, /* get target matrix */
	pycon_evaluate /* evaluate */
};

/* -------- Action Constraint ----------- */

static void actcon_relink (bConstraint *con)
{
	bActionConstraint *data= con->data;
	ID_NEW(data->act);
}

static void actcon_new_data (void *cdata)
{
	bActionConstraint *data= (bActionConstraint *)cdata;
	
	/* set type to 20 (Loc X), as 0 is Rot X for backwards compatability */
	data->type = 20;
}

static int actcon_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bActionConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void actcon_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bActionConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void actcon_get_tarmat (bConstraint *con, bConstraintOb *cob, bConstraintTarget *ct, float ctime)
{
	extern void chan_calc_mat(bPoseChannel *chan);
	bActionConstraint *data = con->data;
	
	if (VALID_CONS_TARGET(ct)) {
		float tempmat[4][4], vec[3];
		float s, t;
		short axis;
		
		/* initialise return matrix */
		Mat4One(ct->matrix);
		
		/* get the transform matrix of the target */
		constraint_target_to_mat4(ct->tar, ct->subtarget, tempmat, CONSTRAINT_SPACE_WORLD, ct->space, con->headtail);
		
		/* determine where in transform range target is */
		/* data->type is mapped as follows for backwards compatability:
		 *	00,01,02	- rotation (it used to be like this)
		 * 	10,11,12	- scaling
		 *	20,21,22	- location
		 */
		if (data->type < 10) {
			/* extract rotation (is in whatever space target should be in) */
			Mat4ToEul(tempmat, vec);
			vec[0] *= (float)(180.0/M_PI);
			vec[1] *= (float)(180.0/M_PI);
			vec[2] *= (float)(180.0/M_PI);
			axis= data->type;
		}
		else if (data->type < 20) {
			/* extract scaling (is in whatever space target should be in) */
			Mat4ToSize(tempmat, vec);
			axis= data->type - 10;
		}
		else {
			/* extract location */
			VECCOPY(vec, tempmat[3]);
			axis= data->type - 20;
		}
		
		/* Target defines the animation */
		s = (vec[axis]-data->min) / (data->max-data->min);
		CLAMP(s, 0, 1);
		t = ( s * (data->end-data->start)) + data->start;
		
		/* Get the appropriate information from the action */
		if (cob->type == CONSTRAINT_OBTYPE_BONE) {
			bPose *pose;
			bPoseChannel *pchan, *tchan;
			
			/* make a temporary pose and evaluate using that */
			pose = MEM_callocN(sizeof(bPose), "pose");
			
			pchan = cob->pchan;
			tchan= verify_pose_channel(pose, pchan->name);
			extract_pose_from_action(pose, data->act, t);
			
			chan_calc_mat(tchan);
			
			Mat4CpyMat4(ct->matrix, tchan->chan_mat);
			
			/* Clean up */
			free_pose(pose);
		}
		else if (cob->type == CONSTRAINT_OBTYPE_OBJECT) {
			/* evaluate using workob */
			what_does_obaction(cob->ob, data->act, t);
			object_to_mat4(&workob, ct->matrix);
		}
		else {
			/* behaviour undefined... */
			puts("Error: unknown owner type for Action Constraint");
		}
	}
}

static void actcon_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bConstraintTarget *ct= targets->first;
	
	if (VALID_CONS_TARGET(ct)) {
		float temp[4][4];
		
		/* Nice and simple... we just need to multiply the matrices, as the get_target_matrix
		 * function has already taken care of everything else.
		 */
		Mat4CpyMat4(temp, cob->matrix);
		Mat4MulMat4(cob->matrix, ct->matrix, temp);
	}
}

static bConstraintTypeInfo CTI_ACTION = {
	CONSTRAINT_TYPE_ACTION, /* type */
	sizeof(bActionConstraint), /* size */
	"Action", /* name */
	"bActionConstraint", /* struct name */
	NULL, /* free data */
	actcon_relink, /* relink data */
	NULL, /* copy data */
	actcon_new_data, /* new data */
	actcon_get_tars, /* get constraint targets */
	actcon_flush_tars, /* flush constraint targets */
	actcon_get_tarmat, /* get target matrix */
	actcon_evaluate /* evaluate */
};

/* --------- Locked Track ---------- */

static void locktrack_new_data (void *cdata)
{
	bLockTrackConstraint *data= (bLockTrackConstraint *)cdata;
	
	data->trackflag = TRACK_Y;
	data->lockflag = LOCK_Z;
}	

static int locktrack_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bLockTrackConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void locktrack_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bLockTrackConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void locktrack_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bLockTrackConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	if (VALID_CONS_TARGET(ct)) {
		float vec[3],vec2[3];
		float totmat[3][3];
		float tmpmat[3][3];
		float invmat[3][3];
		float tmat[4][4];
		float mdet;
		
		/* Vector object -> target */
		VecSubf(vec, ct->matrix[3], cob->matrix[3]);
		switch (data->lockflag){
		case LOCK_X: /* LOCK X */
		{
			switch (data->trackflag) {
				case TRACK_Y: /* LOCK X TRACK Y */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[0]);
					VecSubf(totmat[1], vec, vec2);
					Normalize(totmat[1]);
					
					/* the x axis is fixed */
					totmat[0][0] = cob->matrix[0][0];
					totmat[0][1] = cob->matrix[0][1];
					totmat[0][2] = cob->matrix[0][2];
					Normalize(totmat[0]);
					
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[2], totmat[0], totmat[1]);
				}
					break;
				case TRACK_Z: /* LOCK X TRACK Z */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[0]);
					VecSubf(totmat[2], vec, vec2);
					Normalize(totmat[2]);
					
					/* the x axis is fixed */
					totmat[0][0] = cob->matrix[0][0];
					totmat[0][1] = cob->matrix[0][1];
					totmat[0][2] = cob->matrix[0][2];
					Normalize(totmat[0]);
					
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[1], totmat[2], totmat[0]);
				}
					break;
				case TRACK_nY: /* LOCK X TRACK -Y */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[0]);
					VecSubf(totmat[1], vec, vec2);
					Normalize(totmat[1]);
					VecMulf(totmat[1],-1);
					
					/* the x axis is fixed */
					totmat[0][0] = cob->matrix[0][0];
					totmat[0][1] = cob->matrix[0][1];
					totmat[0][2] = cob->matrix[0][2];
					Normalize(totmat[0]);
					
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[2], totmat[0], totmat[1]);
				}
					break;
				case TRACK_nZ: /* LOCK X TRACK -Z */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[0]);
					VecSubf(totmat[2], vec, vec2);
					Normalize(totmat[2]);
					VecMulf(totmat[2],-1);
						
					/* the x axis is fixed */
					totmat[0][0] = cob->matrix[0][0];
					totmat[0][1] = cob->matrix[0][1];
					totmat[0][2] = cob->matrix[0][2];
					Normalize(totmat[0]);
						
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[1], totmat[2], totmat[0]);
				}
					break;
				default:
				{
					totmat[0][0] = 1;totmat[0][1] = 0;totmat[0][2] = 0;
					totmat[1][0] = 0;totmat[1][1] = 1;totmat[1][2] = 0;
					totmat[2][0] = 0;totmat[2][1] = 0;totmat[2][2] = 1;
				}
					break;
			}
		}
			break;
		case LOCK_Y: /* LOCK Y */
		{
			switch (data->trackflag) {
				case TRACK_X: /* LOCK Y TRACK X */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[1]);
					VecSubf(totmat[0], vec, vec2);
					Normalize(totmat[0]);
					
					/* the y axis is fixed */
					totmat[1][0] = cob->matrix[1][0];
					totmat[1][1] = cob->matrix[1][1];
					totmat[1][2] = cob->matrix[1][2];
					Normalize(totmat[1]);
					
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[2], totmat[0], totmat[1]);
				}
					break;
				case TRACK_Z: /* LOCK Y TRACK Z */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[1]);
					VecSubf(totmat[2], vec, vec2);
					Normalize(totmat[2]);

					/* the y axis is fixed */
					totmat[1][0] = cob->matrix[1][0];
					totmat[1][1] = cob->matrix[1][1];
					totmat[1][2] = cob->matrix[1][2];
					Normalize(totmat[1]);
					
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[0], totmat[1], totmat[2]);
				}
					break;
				case TRACK_nX: /* LOCK Y TRACK -X */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[1]);
					VecSubf(totmat[0], vec, vec2);
					Normalize(totmat[0]);
					VecMulf(totmat[0],-1);
					
					/* the y axis is fixed */
					totmat[1][0] = cob->matrix[1][0];
					totmat[1][1] = cob->matrix[1][1];
					totmat[1][2] = cob->matrix[1][2];
					Normalize(totmat[1]);
					
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[2], totmat[0], totmat[1]);
				}
					break;
				case TRACK_nZ: /* LOCK Y TRACK -Z */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[1]);
					VecSubf(totmat[2], vec, vec2);
					Normalize(totmat[2]);
					VecMulf(totmat[2],-1);
					
					/* the y axis is fixed */
					totmat[1][0] = cob->matrix[1][0];
					totmat[1][1] = cob->matrix[1][1];
					totmat[1][2] = cob->matrix[1][2];
					Normalize(totmat[1]);
					
					/* the z axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[0], totmat[1], totmat[2]);
				}
					break;
				default:
				{
					totmat[0][0] = 1;totmat[0][1] = 0;totmat[0][2] = 0;
					totmat[1][0] = 0;totmat[1][1] = 1;totmat[1][2] = 0;
					totmat[2][0] = 0;totmat[2][1] = 0;totmat[2][2] = 1;
				}
					break;
			}
		}
			break;
		case LOCK_Z: /* LOCK Z */
		{
			switch (data->trackflag) {
				case TRACK_X: /* LOCK Z TRACK X */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[2]);
					VecSubf(totmat[0], vec, vec2);
					Normalize(totmat[0]);
					
					/* the z axis is fixed */
					totmat[2][0] = cob->matrix[2][0];
					totmat[2][1] = cob->matrix[2][1];
					totmat[2][2] = cob->matrix[2][2];
					Normalize(totmat[2]);
					
					/* the x axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[1], totmat[2], totmat[0]);
				}
					break;
				case TRACK_Y: /* LOCK Z TRACK Y */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[2]);
					VecSubf(totmat[1], vec, vec2);
					Normalize(totmat[1]);
					
					/* the z axis is fixed */
					totmat[2][0] = cob->matrix[2][0];
					totmat[2][1] = cob->matrix[2][1];
					totmat[2][2] = cob->matrix[2][2];
					Normalize(totmat[2]);
						
					/* the x axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[0], totmat[1], totmat[2]);
				}
					break;
				case TRACK_nX: /* LOCK Z TRACK -X */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[2]);
					VecSubf(totmat[0], vec, vec2);
					Normalize(totmat[0]);
					VecMulf(totmat[0],-1);
					
					/* the z axis is fixed */
					totmat[2][0] = cob->matrix[2][0];
					totmat[2][1] = cob->matrix[2][1];
					totmat[2][2] = cob->matrix[2][2];
					Normalize(totmat[2]);
					
					/* the x axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[1], totmat[2], totmat[0]);
				}
					break;
				case TRACK_nY: /* LOCK Z TRACK -Y */
				{
					/* Projection of Vector on the plane */
					Projf(vec2, vec, cob->matrix[2]);
					VecSubf(totmat[1], vec, vec2);
					Normalize(totmat[1]);
					VecMulf(totmat[1],-1);
					
					/* the z axis is fixed */
					totmat[2][0] = cob->matrix[2][0];
					totmat[2][1] = cob->matrix[2][1];
					totmat[2][2] = cob->matrix[2][2];
					Normalize(totmat[2]);
						
					/* the x axis gets mapped onto a third orthogonal vector */
					Crossf(totmat[0], totmat[1], totmat[2]);
				}
					break;
				default:
				{
						totmat[0][0] = 1;totmat[0][1] = 0;totmat[0][2] = 0;
						totmat[1][0] = 0;totmat[1][1] = 1;totmat[1][2] = 0;
						totmat[2][0] = 0;totmat[2][1] = 0;totmat[2][2] = 1;
				}
					break;
			}
		}
			break;
		default:
			{
				totmat[0][0] = 1;totmat[0][1] = 0;totmat[0][2] = 0;
				totmat[1][0] = 0;totmat[1][1] = 1;totmat[1][2] = 0;
				totmat[2][0] = 0;totmat[2][1] = 0;totmat[2][2] = 1;
			}
			break;
		}
		/* Block to keep matrix heading */
		tmpmat[0][0] = cob->matrix[0][0];tmpmat[0][1] = cob->matrix[0][1];tmpmat[0][2] = cob->matrix[0][2];
		tmpmat[1][0] = cob->matrix[1][0];tmpmat[1][1] = cob->matrix[1][1];tmpmat[1][2] = cob->matrix[1][2];
		tmpmat[2][0] = cob->matrix[2][0];tmpmat[2][1] = cob->matrix[2][1];tmpmat[2][2] = cob->matrix[2][2];
		Normalize(tmpmat[0]);
		Normalize(tmpmat[1]);
		Normalize(tmpmat[2]);
		Mat3Inv(invmat, tmpmat);
		Mat3MulMat3(tmpmat, totmat, invmat);
		totmat[0][0] = tmpmat[0][0];totmat[0][1] = tmpmat[0][1];totmat[0][2] = tmpmat[0][2];
		totmat[1][0] = tmpmat[1][0];totmat[1][1] = tmpmat[1][1];totmat[1][2] = tmpmat[1][2];
		totmat[2][0] = tmpmat[2][0];totmat[2][1] = tmpmat[2][1];totmat[2][2] = tmpmat[2][2];
		
		Mat4CpyMat4(tmat, cob->matrix);
		
		mdet = Det3x3(	totmat[0][0],totmat[0][1],totmat[0][2],
						totmat[1][0],totmat[1][1],totmat[1][2],
						totmat[2][0],totmat[2][1],totmat[2][2]);
		if (mdet==0) {
			totmat[0][0] = 1;totmat[0][1] = 0;totmat[0][2] = 0;
			totmat[1][0] = 0;totmat[1][1] = 1;totmat[1][2] = 0;
			totmat[2][0] = 0;totmat[2][1] = 0;totmat[2][2] = 1;
		}
		
		/* apply out transformaton to the object */
		Mat4MulMat34(cob->matrix, totmat, tmat);
	}
}

static bConstraintTypeInfo CTI_LOCKTRACK = {
	CONSTRAINT_TYPE_LOCKTRACK, /* type */
	sizeof(bLockTrackConstraint), /* size */
	"Locked Track", /* name */
	"bLockTrackConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	locktrack_new_data, /* new data */
	locktrack_get_tars, /* get constraint targets */
	locktrack_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	locktrack_evaluate /* evaluate */
};

/* ---------- Limit Distance Constraint ----------- */

static void distlimit_new_data (void *cdata)
{
	bDistLimitConstraint *data= (bDistLimitConstraint *)cdata;
	
	data->dist= 0.0;
}

static int distlimit_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bDistLimitConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void distlimit_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bDistLimitConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void distlimit_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bDistLimitConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	/* only evaluate if there is a target */
	if (VALID_CONS_TARGET(ct)) {
		float dvec[3], dist=0.0f, sfac=1.0f;
		short clamp_surf= 0;
		
		/* calculate our current distance from the target */
		dist= VecLenf(cob->matrix[3], ct->matrix[3]);
		
		/* set distance (flag is only set when user demands it) */
		if (data->dist == 0)
			data->dist= dist;
		
		/* check if we're which way to clamp from, and calculate interpolation factor (if needed) */
		if (data->mode == LIMITDIST_OUTSIDE) {
			/* if inside, then move to surface */
			if (dist <= data->dist) {
				clamp_surf= 1;
				sfac= data->dist / dist;
			}
			/* if soft-distance is enabled, start fading once owner is dist+softdist from the target */
			else if (data->flag & LIMITDIST_USESOFT) {
				if (dist <= (data->dist + data->soft)) {
					
				}
			}
		}
		else if (data->mode == LIMITDIST_INSIDE) {
			/* if outside, then move to surface */
			if (dist >= data->dist) {
				clamp_surf= 1;
				sfac= data->dist / dist;
			}
			/* if soft-distance is enabled, start fading once owner is dist-soft from the target */
			else if (data->flag & LIMITDIST_USESOFT) {
				// FIXME: there's a problem with "jumping" when this kicks in
				if (dist >= (data->dist - data->soft)) {
					sfac = data->soft*(1.0 - exp(-(dist - data->dist)/data->soft)) + data->dist;
					sfac /= dist;
					
					clamp_surf= 1;
				}
			}
		}
		else {
			if (IS_EQ(dist, data->dist)==0) {
				clamp_surf= 1;
				sfac= data->dist / dist;
			}
		}
		
		/* clamp to 'surface' (i.e. move owner so that dist == data->dist) */
		if (clamp_surf) {
			/* simply interpolate along line formed by target -> owner */
			VecLerpf(dvec, ct->matrix[3], cob->matrix[3], sfac);
			
			/* copy new vector onto owner */
			VECCOPY(cob->matrix[3], dvec);
		}
	}
}

static bConstraintTypeInfo CTI_DISTLIMIT = {
	CONSTRAINT_TYPE_DISTLIMIT, /* type */
	sizeof(bDistLimitConstraint), /* size */
	"Limit Distance", /* name */
	"bDistLimitConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	distlimit_new_data, /* new data */
	distlimit_get_tars, /* get constraint targets */
	distlimit_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get a target matrix */
	distlimit_evaluate /* evaluate */
};

/* ---------- Stretch To ------------ */

static void stretchto_new_data (void *cdata)
{
	bStretchToConstraint *data= (bStretchToConstraint *)cdata;
	
	data->volmode = 0;
	data->plane = 0;
	data->orglength = 0.0; 
	data->bulge = 1.0;
}

static int stretchto_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bStretchToConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void stretchto_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bStretchToConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void stretchto_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bStretchToConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	/* only evaluate if there is a target */
	if (VALID_CONS_TARGET(ct)) {
		float size[3], scale[3], vec[3], xx[3], zz[3], orth[3];
		float totmat[3][3];
		float tmat[4][4];
		float dist;
		
		/* store scaling before destroying obmat */
		Mat4ToSize(cob->matrix, size);
		
		/* store X orientation before destroying obmat */
		xx[0] = cob->matrix[0][0];
		xx[1] = cob->matrix[0][1];
		xx[2] = cob->matrix[0][2];
		Normalize(xx);
		
		/* store Z orientation before destroying obmat */
		zz[0] = cob->matrix[2][0];
		zz[1] = cob->matrix[2][1];
		zz[2] = cob->matrix[2][2];
		Normalize(zz);
		
		VecSubf(vec, cob->matrix[3], ct->matrix[3]);
		vec[0] /= size[0];
		vec[1] /= size[1];
		vec[2] /= size[2];
		
		dist = Normalize(vec);
		//dist = VecLenf( ob->obmat[3], targetmat[3]);
		
		/* data->orglength==0 occurs on first run, and after 'R' button is clicked */
		if (data->orglength == 0)  
			data->orglength = dist;
		if (data->bulge == 0) 
			data->bulge = 1.0;
		
		scale[1] = dist/data->orglength;
		switch (data->volmode) {
		/* volume preserving scaling */
		case VOLUME_XZ :
			scale[0] = 1.0f - (float)sqrt(data->bulge) + (float)sqrt(data->bulge*(data->orglength/dist));
			scale[2] = scale[0];
			break;
		case VOLUME_X:
			scale[0] = 1.0f + data->bulge * (data->orglength /dist - 1);
			scale[2] = 1.0;
			break;
		case VOLUME_Z:
			scale[0] = 1.0;
			scale[2] = 1.0f + data->bulge * (data->orglength /dist - 1);
			break;
			/* don't care for volume */
		case NO_VOLUME:
			scale[0] = 1.0;
			scale[2] = 1.0;
			break;
		default: /* should not happen, but in case*/
			return;    
		} /* switch (data->volmode) */

		/* Clear the object's rotation and scale */
		cob->matrix[0][0]=size[0]*scale[0];
		cob->matrix[0][1]=0;
		cob->matrix[0][2]=0;
		cob->matrix[1][0]=0;
		cob->matrix[1][1]=size[1]*scale[1];
		cob->matrix[1][2]=0;
		cob->matrix[2][0]=0;
		cob->matrix[2][1]=0;
		cob->matrix[2][2]=size[2]*scale[2];
		
		VecSubf(vec, cob->matrix[3], ct->matrix[3]);
		Normalize(vec);
		
		/* new Y aligns  object target connection*/
		totmat[1][0] = -vec[0];
		totmat[1][1] = -vec[1];
		totmat[1][2] = -vec[2];
		switch (data->plane) {
		case PLANE_X:
			/* build new Z vector */
			/* othogonal to "new Y" "old X! plane */
			Crossf(orth, vec, xx);
			Normalize(orth);
			
			/* new Z*/
			totmat[2][0] = orth[0];
			totmat[2][1] = orth[1];
			totmat[2][2] = orth[2];
			
			/* we decided to keep X plane*/
			Crossf(xx, orth, vec);
			Normalize(xx);
			totmat[0][0] = xx[0];
			totmat[0][1] = xx[1];
			totmat[0][2] = xx[2];
			break;
		case PLANE_Z:
			/* build new X vector */
			/* othogonal to "new Y" "old Z! plane */
			Crossf(orth, vec, zz);
			Normalize(orth);
			
			/* new X */
			totmat[0][0] = -orth[0];
			totmat[0][1] = -orth[1];
			totmat[0][2] = -orth[2];
			
			/* we decided to keep Z */
			Crossf(zz, orth, vec);
			Normalize(zz);
			totmat[2][0] = zz[0];
			totmat[2][1] = zz[1];
			totmat[2][2] = zz[2];
			break;
		} /* switch (data->plane) */
		
		Mat4CpyMat4(tmat, cob->matrix);
		Mat4MulMat34(cob->matrix, totmat, tmat);
	}
}

static bConstraintTypeInfo CTI_STRETCHTO = {
	CONSTRAINT_TYPE_STRETCHTO, /* type */
	sizeof(bStretchToConstraint), /* size */
	"Stretch To", /* name */
	"bStretchToConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	stretchto_new_data, /* new data */
	stretchto_get_tars, /* get constraint targets */
	stretchto_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	stretchto_evaluate /* evaluate */
};

/* ---------- Floor ------------ */

static void minmax_new_data (void *cdata)
{
	bMinMaxConstraint *data= (bMinMaxConstraint *)cdata;
	
	data->minmaxflag = TRACK_Z;
	data->offset = 0.0f;
	data->cache[0] = data->cache[1] = data->cache[2] = 0.0f;
	data->flag = 0;
}

static int minmax_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bMinMaxConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void minmax_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bMinMaxConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void minmax_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bMinMaxConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	/* only evaluate if there is a target */
	if (VALID_CONS_TARGET(ct)) {
		float obmat[4][4], imat[4][4], tarmat[4][4], tmat[4][4];
		float val1, val2;
		int index;
		
		Mat4CpyMat4(obmat, cob->matrix);
		Mat4CpyMat4(tarmat, ct->matrix);
		
		if (data->flag & MINMAX_USEROT) {
			/* take rotation of target into account by doing the transaction in target's localspace */
			Mat4Invert(imat, tarmat);
			Mat4MulMat4(tmat, obmat, imat);
			Mat4CpyMat4(obmat, tmat);
			Mat4One(tarmat);
		}
		
		switch (data->minmaxflag) {
		case TRACK_Z:
			val1 = tarmat[3][2];
			val2 = obmat[3][2]-data->offset;
			index = 2;
			break;
		case TRACK_Y:
			val1 = tarmat[3][1];
			val2 = obmat[3][1]-data->offset;
			index = 1;
			break;
		case TRACK_X:
			val1 = tarmat[3][0];
			val2 = obmat[3][0]-data->offset;
			index = 0;
			break;
		case TRACK_nZ:
			val2 = tarmat[3][2];
			val1 = obmat[3][2]-data->offset;
			index = 2;
			break;
		case TRACK_nY:
			val2 = tarmat[3][1];
			val1 = obmat[3][1]-data->offset;
			index = 1;
			break;
		case TRACK_nX:
			val2 = tarmat[3][0];
			val1 = obmat[3][0]-data->offset;
			index = 0;
			break;
		default:
			return;
		}
		
		if (val1 > val2) {
			obmat[3][index] = tarmat[3][index] + data->offset;
			if (data->flag & MINMAX_STICKY) {
				if (data->flag & MINMAX_STUCK) {
					VECCOPY(obmat[3], data->cache);
				} 
				else {
					VECCOPY(data->cache, obmat[3]);
					data->flag |= MINMAX_STUCK;
				}
			}
			if (data->flag & MINMAX_USEROT) {
				/* get out of localspace */
				Mat4MulMat4(tmat, obmat, ct->matrix);
				Mat4CpyMat4(cob->matrix, tmat);
			} 
			else {			
				VECCOPY(cob->matrix[3], obmat[3]);
			}
		} 
		else {
			data->flag &= ~MINMAX_STUCK;
		}
	}
}

static bConstraintTypeInfo CTI_MINMAX = {
	CONSTRAINT_TYPE_MINMAX, /* type */
	sizeof(bMinMaxConstraint), /* size */
	"Floor", /* name */
	"bMinMaxConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	minmax_new_data, /* new data */
	minmax_get_tars, /* get constraint targets */
	minmax_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	minmax_evaluate /* evaluate */
};

/* ------- RigidBody Joint ---------- */

static void rbj_new_data (void *cdata)
{
	bRigidBodyJointConstraint *data= (bRigidBodyJointConstraint *)cdata;
	
	// removed code which set target of this constraint  
    data->type=1;
}

static int rbj_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bRigidBodyJointConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints without subtargets */
		SINGLETARGETNS_GET_TARS(con, data->tar, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void rbj_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bRigidBodyJointConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGETNS_FLUSH_TARS(con, data->tar, ct, list, nocopy)
	}
}

static bConstraintTypeInfo CTI_RIGIDBODYJOINT = {
	CONSTRAINT_TYPE_RIGIDBODYJOINT, /* type */
	sizeof(bRigidBodyJointConstraint), /* size */
	"RigidBody Joint", /* name */
	"bRigidBodyJointConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	rbj_new_data, /* new data */
	rbj_get_tars, /* get constraint targets */
	rbj_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get target matrix */
	NULL /* evaluate - this is not solved here... is just an interface for game-engine */
};

/* -------- Clamp To ---------- */

static int clampto_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bClampToConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints without subtargets */
		SINGLETARGETNS_GET_TARS(con, data->tar, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void clampto_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bClampToConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGETNS_FLUSH_TARS(con, data->tar, ct, list, nocopy)
	}
}

static void clampto_get_tarmat (bConstraint *con, bConstraintOb *cob, bConstraintTarget *ct, float ctime)
{
	if (VALID_CONS_TARGET(ct)) {
		Curve *cu= ct->tar->data;
		
		/* note: when creating constraints that follow path, the curve gets the CU_PATH set now,
		 *		currently for paths to work it needs to go through the bevlist/displist system (ton) 
		 */
		
		/* only happens on reload file, but violates depsgraph still... fix! */
		if (cu->path==NULL || cu->path->data==NULL) 
			makeDispListCurveTypes(ct->tar, 0);
	}
	
	/* technically, this isn't really needed for evaluation, but we don't know what else
	 * might end up calling this...
	 */
	if (ct)
		Mat4One(ct->matrix);
}

static void clampto_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bClampToConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	/* only evaluate if there is a target and it is a curve */
	if (VALID_CONS_TARGET(ct) && (ct->tar->type == OB_CURVE)) {
		Curve *cu= data->tar->data;
		float obmat[4][4], targetMatrix[4][4], ownLoc[3];
		float curveMin[3], curveMax[3];
		
		Mat4CpyMat4(obmat, cob->matrix);
		Mat4One(targetMatrix);
		VECCOPY(ownLoc, obmat[3]);
		
		INIT_MINMAX(curveMin, curveMax)
		minmax_object(ct->tar, curveMin, curveMax);
		
		/* get targetmatrix */
		if (cu->path && cu->path->data) {
			float vec[4], dir[3], totmat[4][4];
			float curvetime;
			short clamp_axis;
			
			/* find best position on curve */
			/* 1. determine which axis to sample on? */
			if (data->flag == CLAMPTO_AUTO) {
				float size[3];
				VecSubf(size, curveMax, curveMin);
				
				/* find axis along which the bounding box has the greatest
				 * extent. Otherwise, default to the x-axis, as that is quite
				 * frequently used.
				 */
				if ((size[2]>size[0]) && (size[2]>size[1]))
					clamp_axis= CLAMPTO_Z - 1;
				else if ((size[1]>size[0]) && (size[1]>size[2]))
					clamp_axis= CLAMPTO_Y - 1;
				else
					clamp_axis = CLAMPTO_X - 1;
			}
			else 
				clamp_axis= data->flag - 1;
				
			/* 2. determine position relative to curve on a 0-1 scale based on bounding box */
			if (data->flag2 & CLAMPTO_CYCLIC) {
				/* cyclic, so offset within relative bounding box is used */
				float len= (curveMax[clamp_axis] - curveMin[clamp_axis]);
				float offset;
				
				/* find bounding-box range where target is located */
				if (ownLoc[clamp_axis] < curveMin[clamp_axis]) {
					/* bounding-box range is before */
					offset= curveMin[clamp_axis];
					
					while (ownLoc[clamp_axis] < offset)
						offset -= len;
					
					/* now, we calculate as per normal, except using offset instead of curveMin[clamp_axis] */
					curvetime = (ownLoc[clamp_axis] - offset) / (len);
				}
				else if (ownLoc[clamp_axis] > curveMax[clamp_axis]) {
					/* bounding-box range is after */
					offset= curveMax[clamp_axis];
					
					while (ownLoc[clamp_axis] > offset) {
						if ((offset + len) > ownLoc[clamp_axis])
							break;
						else
							offset += len;
					}
					
					/* now, we calculate as per normal, except using offset instead of curveMax[clamp_axis] */
					curvetime = (ownLoc[clamp_axis] - offset) / (len);
				}
				else {
					/* as the location falls within bounds, just calculate */
					curvetime = (ownLoc[clamp_axis] - curveMin[clamp_axis]) / (len);
				}
			}
			else {
				/* no cyclic, so position is clamped to within the bounding box */
				if (ownLoc[clamp_axis] <= curveMin[clamp_axis])
					curvetime = 0.0;
				else if (ownLoc[clamp_axis] >= curveMax[clamp_axis])
					curvetime = 1.0;
				else
					curvetime = (ownLoc[clamp_axis] - curveMin[clamp_axis]) / (curveMax[clamp_axis] - curveMin[clamp_axis]);
			}
			
			/* 3. position on curve */
			if (where_on_path(ct->tar, curvetime, vec, dir) ) {
				Mat4One(totmat);
				VECCOPY(totmat[3], vec);
				
				Mat4MulSerie(targetMatrix, ct->tar->obmat, totmat, NULL, NULL, NULL, NULL, NULL, NULL);
			}
		}
		
		/* obtain final object position */
		VECCOPY(cob->matrix[3], targetMatrix[3]);
	}
}

static bConstraintTypeInfo CTI_CLAMPTO = {
	CONSTRAINT_TYPE_CLAMPTO, /* type */
	sizeof(bClampToConstraint), /* size */
	"Clamp To", /* name */
	"bClampToConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	NULL, /* new data */
	clampto_get_tars, /* get constraint targets */
	clampto_flush_tars, /* flush constraint targets */
	clampto_get_tarmat, /* get target matrix */
	clampto_evaluate /* evaluate */
};

/* ---------- Transform Constraint ----------- */

static void transform_new_data (void *cdata)
{
	bTransformConstraint *data= (bTransformConstraint *)cdata;
	
	data->map[0]= 0;
	data->map[1]= 1;
	data->map[2]= 2;
}

static int transform_get_tars (bConstraint *con, ListBase *list)
{
	if (con && list) {
		bTransformConstraint *data= con->data;
		bConstraintTarget *ct;
		
		/* standard target-getting macro for single-target constraints */
		SINGLETARGET_GET_TARS(con, data->tar, data->subtarget, ct, list)
		
		return 1;
	}
	
	return 0;
}

static void transform_flush_tars (bConstraint *con, ListBase *list, short nocopy)
{
	if (con && list) {
		bTransformConstraint *data= con->data;
		bConstraintTarget *ct= list->first;
		
		/* the following macro is used for all standard single-target constraints */
		SINGLETARGET_FLUSH_TARS(con, data->tar, data->subtarget, ct, list, nocopy)
	}
}

static void transform_evaluate (bConstraint *con, bConstraintOb *cob, ListBase *targets)
{
	bTransformConstraint *data= con->data;
	bConstraintTarget *ct= targets->first;
	
	/* only evaluate if there is a target */
	if (VALID_CONS_TARGET(ct)) {
		float loc[3], eul[3], size[3];
		float dvec[3], sval[3];
		short i;
		
		/* obtain target effect */
		switch (data->from) {
			case 2: /* scale */
				Mat4ToSize(ct->matrix, dvec);
				break;
			case 1: /* rotation (convert to degrees first) */
				Mat4ToEul(ct->matrix, dvec);
				for (i=0; i<3; i++)
					dvec[i] = dvec[i] / M_PI * 180;
				break;
			default: /* location */
				VecCopyf(dvec, ct->matrix[3]);
				break;
		}
		
		/* extract components of owner's matrix */
		VECCOPY(loc, cob->matrix[3]);
		Mat4ToEul(cob->matrix, eul);
		Mat4ToSize(cob->matrix, size);	
		
		/* determine where in range current transforms lie */
		if (data->expo) {
			for (i=0; i<3; i++) {
				if (data->from_max[i] - data->from_min[i])
					sval[i]= (dvec[i] - data->from_min[i]) / (data->from_max[i] - data->from_min[i]);
				else
					sval[i]= 0.0f;
			}
		}
		else {
			/* clamp transforms out of range */
			for (i=0; i<3; i++) {
				CLAMP(dvec[i], data->from_min[i], data->from_max[i]);
				if (data->from_max[i] - data->from_min[i])
					sval[i]= (dvec[i] - data->from_min[i]) / (data->from_max[i] - data->from_min[i]);
				else
					sval[i]= 0.0f;
			}
		}
		
		
		/* apply transforms */
		switch (data->to) {
			case 2: /* scaling */
				for (i=0; i<3; i++)
					size[i]= data->to_min[i] + (sval[data->map[i]] * (data->to_max[i] - data->to_min[i])); 
				break;
			case 1: /* rotation */
				for (i=0; i<3; i++) {
					float tmin, tmax;
					
					tmin= data->to_min[i];
					tmax= data->to_max[i];
					
					/* all values here should be in degrees */
					eul[i]= tmin + (sval[data->map[i]] * (tmax - tmin)); 
					
					/* now convert final value back to radians */
					eul[i] = eul[i] / 180 * M_PI;
				}
				break;
			default: /* location */
				/* get new location */
				for (i=0; i<3; i++)
					loc[i]= (data->to_min[i] + (sval[data->map[i]] * (data->to_max[i] - data->to_min[i])));
				
				/* add original location back on (so that it can still be moved) */
				VecAddf(loc, cob->matrix[3], loc);
				break;
		}
		
		/* apply to matrix */
		LocEulSizeToMat4(cob->matrix, loc, eul, size);
	}
}

static bConstraintTypeInfo CTI_TRANSFORM = {
	CONSTRAINT_TYPE_TRANSFORM, /* type */
	sizeof(bTransformConstraint), /* size */
	"Transform", /* name */
	"bTransformConstraint", /* struct name */
	NULL, /* free data */
	NULL, /* relink data */
	NULL, /* copy data */
	transform_new_data, /* new data */
	transform_get_tars, /* get constraint targets */
	transform_flush_tars, /* flush constraint targets */
	default_get_tarmat, /* get a target matrix */
	transform_evaluate /* evaluate */
};

/* ************************* Constraints Type-Info *************************** */
/* All of the constraints api functions use bConstraintTypeInfo structs to carry out
 * and operations that involve constraint specifc code.
 */

/* These globals only ever get directly accessed in this file */
static bConstraintTypeInfo *constraintsTypeInfo[NUM_CONSTRAINT_TYPES+1];
static short CTI_INIT= 1; /* when non-zero, the list needs to be updated */

/* This function only gets called when CTI_INIT is non-zero */
static void constraints_init_typeinfo () {
	constraintsTypeInfo[0]=  NULL; 					/* 'Null' Constraint */
	constraintsTypeInfo[1]=  &CTI_CHILDOF; 			/* ChildOf Constraint */
	constraintsTypeInfo[2]=  &CTI_TRACKTO;			/* TrackTo Constraint */
	constraintsTypeInfo[3]=  &CTI_KINEMATIC;		/* IK Constraint */
	constraintsTypeInfo[4]=  &CTI_FOLLOWPATH;		/* Follow-Path Constraint */
	constraintsTypeInfo[5]=  &CTI_ROTLIMIT;			/* Limit Rotation Constraint */
	constraintsTypeInfo[6]=  &CTI_LOCLIMIT;			/* Limit Location Constraint */
	constraintsTypeInfo[7]=  &CTI_SIZELIMIT;		/* Limit Scaling Constraint */
	constraintsTypeInfo[8]=  &CTI_ROTLIKE;			/* Copy Rotation Constraint */
	constraintsTypeInfo[9]=  &CTI_LOCLIKE;			/* Copy Location Constraint */
	constraintsTypeInfo[10]= &CTI_SIZELIKE;			/* Copy Scaling Constraint */
	constraintsTypeInfo[11]= &CTI_PYTHON;			/* Python/Script Constraint */
	constraintsTypeInfo[12]= &CTI_ACTION;			/* Action Constraint */
	constraintsTypeInfo[13]= &CTI_LOCKTRACK;		/* Locked-Track Constraint */
	constraintsTypeInfo[14]= &CTI_DISTLIMIT;		/* Limit Distance Constraint */
	constraintsTypeInfo[15]= &CTI_STRETCHTO; 		/* StretchTo Constaint */ 
	constraintsTypeInfo[16]= &CTI_MINMAX;  			/* Floor Constraint */
	constraintsTypeInfo[17]= &CTI_RIGIDBODYJOINT;	/* RigidBody Constraint */
	constraintsTypeInfo[18]= &CTI_CLAMPTO; 			/* ClampTo Constraint */	
	constraintsTypeInfo[19]= &CTI_TRANSFORM;		/* Transformation Constraint */
}

/* This function should be used for getting the appropriate type-info when only
 * a constraint type is known
 */
bConstraintTypeInfo *get_constraint_typeinfo (int type)
{
	/* initialise the type-info list? */
	if (CTI_INIT) {
		constraints_init_typeinfo();
		CTI_INIT = 0;
	}
	
	/* only return for valid types */
	if ( (type >= CONSTRAINT_TYPE_NULL) && 
		 (type <= NUM_CONSTRAINT_TYPES ) ) 
	{
		/* there shouldn't be any segfaults here... */
		return constraintsTypeInfo[type];
	}
	else {
		printf("No valid constraint type-info data available. Type = %i \n", type);
	}
	
	return NULL;
} 
 
/* This function should always be used to get the appropriate type-info, as it
 * has checks which prevent segfaults in some weird cases.
 */
bConstraintTypeInfo *constraint_get_typeinfo (bConstraint *con)
{
	/* only return typeinfo for valid constraints */
	if (con)
		return get_constraint_typeinfo(con->type);
	else
		return NULL;
}

/* ************************* General Constraints API ************************** */
/* The functions here are called by various parts of Blender. Very few (should be none if possible)
 * constraint-specific code should occur here.
 */
 
/* ---------- Data Management ------- */

/* Free data of a specific constraint if it has any info */
void free_constraint_data (bConstraint *con)
{
	if (con->data) {
		bConstraintTypeInfo *cti= constraint_get_typeinfo(con);
		
		/* perform any special freeing constraint may have */
		if (cti && cti->free_data)
			cti->free_data(con);
		
		/* free constraint data now */
		MEM_freeN(con->data);
	}
}

/* Free all constraints from a constraint-stack */
void free_constraints (ListBase *conlist)
{
	bConstraint *con;
	
	/* Free constraint data and also any extra data */
	for (con= conlist->first; con; con= con->next) {
		free_constraint_data(con);
	}
	
	/* Free the whole list */
	BLI_freelistN(conlist);
}

/* Reassign links that constraints have to other data (called during file loading?) */
void relink_constraints (ListBase *conlist)
{
	bConstraint *con;
	bConstraintTarget *ct;
	
	for (con= conlist->first; con; con= con->next) {
		bConstraintTypeInfo *cti= constraint_get_typeinfo(con);
		
		if (cti) {
			/* relink any targets */
			if (cti->get_constraint_targets) {
				ListBase targets = {NULL, NULL};
				
				cti->get_constraint_targets(con, &targets);
				for (ct= targets.first; ct; ct= ct->next) {
					ID_NEW(ct->tar);
				}
				
				if (cti->flush_constraint_targets)
					cti->flush_constraint_targets(con, &targets, 0);
			}
			
			/* relink any other special data */
			if (cti->relink_data)
				cti->relink_data(con);
		}
	}
}

/* duplicate all of the constraints in a constraint stack */
void copy_constraints (ListBase *dst, ListBase *src)
{
	bConstraint *con, *srccon;
	
	dst->first= dst->last= NULL;
	duplicatelist(dst, src);
	
	for (con=dst->first, srccon=src->first; con; srccon=srccon->next, con=con->next) {
		bConstraintTypeInfo *cti= constraint_get_typeinfo(con);
		
		/* make a new copy of the constraint's data */
		con->data = MEM_dupallocN(con->data);
		
		/* only do specific constraints if required */
		if (cti && cti->copy_data)
			cti->copy_data(con, srccon);
	}
}

/* -------- Constraints and Proxies ------- */

/* Rescue all constraints tagged as being CONSTRAINT_PROXY_LOCAL (i.e. added to bone that's proxy-synced in this file) */
void extract_proxylocal_constraints (ListBase *dst, ListBase *src)
{
	bConstraint *con, *next;
	
	/* for each tagged constraint, remove from src and move to dst */
	for (con= src->first; con; con= next) {
		next= con->next;
		
		/* check if tagged */
		if (con->flag & CONSTRAINT_PROXY_LOCAL) {
			BLI_remlink(src, con);
			BLI_addtail(dst, con);
		}
	}
}

/* Returns if the owner of the constraint is proxy-protected */
short proxylocked_constraints_owner (Object *ob, bPoseChannel *pchan)
{
	/* Currently, constraints can only be on object or bone level */
	if (ob && ob->proxy) {
		if (ob->pose && pchan) {
			bArmature *arm= ob->data;
			
			/* On bone-level, check if bone is on proxy-protected layer */
			if ((pchan->bone) && (pchan->bone->layer & arm->layer_protected))
				return 1;
		}
		else {
			/* FIXME: constraints on object-level are not handled well yet */
			return 1;
		}	
	}
	
	return 0;
}

/* -------- Target-Matrix Stuff ------- */

/* This function is a relic from the prior implementations of the constraints system, when all
 * constraints either had one or no targets. It used to be called during the main constraint solving
 * loop, but is now only used for the remaining cases for a few constraints. 
 *
 * None of the actual calculations of the matricies should be done here! Also, this function is 
 * not to be used by any new constraints, particularly any that have multiple targets.
 */
void get_constraint_target_matrix (bConstraint *con, int n, short ownertype, void *ownerdata, float mat[][4], float ctime)
{
	bConstraintTypeInfo *cti= constraint_get_typeinfo(con);
	ListBase targets = {NULL, NULL};
	bConstraintOb *cob;
	bConstraintTarget *ct;
	
	if (cti && cti->get_constraint_targets) {
		/* make 'constraint-ob' */
		cob= MEM_callocN(sizeof(bConstraintOb), "tempConstraintOb");
		cob->type= ownertype;
		switch (ownertype) {
			case CONSTRAINT_OBTYPE_OBJECT: /* it is usually this case */
			{
				cob->ob= (Object *)ownerdata;
				cob->pchan= NULL;
				if (cob->ob) {
					Mat4CpyMat4(cob->matrix, cob->ob->obmat);
					Mat4CpyMat4(cob->startmat, cob->matrix);
				}
				else {
					Mat4One(cob->matrix);
					Mat4One(cob->startmat);
				}
			}	
				break;
			case CONSTRAINT_OBTYPE_BONE: /* this may occur in some cases */
			{
				cob->ob= NULL; /* this might not work at all :/ */
				cob->pchan= (bPoseChannel *)ownerdata;
				if (cob->pchan) {
					Mat4CpyMat4(cob->matrix, cob->pchan->pose_mat);
					Mat4CpyMat4(cob->startmat, cob->matrix);
				}
				else {
					Mat4One(cob->matrix);
					Mat4One(cob->startmat);
				}
			}
				break;
		}
		
		/* get targets - we only need the first one though (and there should only be one) */
		cti->get_constraint_targets(con, &targets);
		
		/* only calculate the target matrix on the first target */
		ct= (bConstraintTarget *)targets.first;
		while(ct && n-- > 0)
			ct= ct->next;

		if (ct) {
			if (cti->get_target_matrix)
				cti->get_target_matrix(con, cob, ct, ctime);
			Mat4CpyMat4(mat, ct->matrix);
		}
		
		/* free targets + 'constraint-ob' */
		if (cti->flush_constraint_targets)
			cti->flush_constraint_targets(con, &targets, 1);
		MEM_freeN(cob);
	}
	else {
		/* invalid constraint - perhaps... */
		Mat4One(mat);
	}
}
 
/* ---------- Evaluation ----------- */

/* This function is called whenever constraints need to be evaluated. Currently, all
 * constraints that can be evaluated are everytime this gets run.
 *
 * constraints_make_evalob and constraints_clear_evalob should be called before and 
 * after running this function, to sort out cob
 */
void solve_constraints (ListBase *conlist, bConstraintOb *cob, float ctime)
{
	bConstraint *con;
	float solution[4][4], delta[4][4];
	float oldmat[4][4], imat[4][4];
	float enf;

	/* check that there is a valid constraint object to evaluate */
	if (cob == NULL)
		return;
	
	/* loop over available constraints, solving and blending them */
	for (con= conlist->first; con; con= con->next) {
		bConstraintTypeInfo *cti= constraint_get_typeinfo(con);
		ListBase targets = {NULL, NULL};
		
		/* these we can skip completely (invalid constraints...) */
		if (cti == NULL) continue;
		if (con->flag & CONSTRAINT_DISABLE) continue;
		/* these constraints can't be evaluated anyway */
		if (cti->evaluate_constraint == NULL) continue;
		/* influence == 0 should be ignored */
		if (con->enforce == 0.0f) continue;
		
		/* influence of constraint
		 * 	- value should have been set from IPO's/Constraint Channels already 
		 */
		enf = con->enforce;
		
		/* move owner matrix into right space */
		constraint_mat_convertspace(cob->ob, cob->pchan, cob->matrix, CONSTRAINT_SPACE_WORLD, con->ownspace);
		Mat4CpyMat4(oldmat, cob->matrix);
		
		/* prepare targets for constraint solving */
		if (cti->get_constraint_targets) {
			bConstraintTarget *ct;
			
			/* get targets 
			 * 	- constraints should use ct->matrix, not directly accessing values
			 *	- ct->matrix members have not yet been calculated here! 
			 */
			cti->get_constraint_targets(con, &targets);
			
			/* set matrices 
			 * 	- calculate if possible, otherwise just initialise as identity matrix 
			 */
			if (cti->get_target_matrix) {
				for (ct= targets.first; ct; ct= ct->next) 
					cti->get_target_matrix(con, cob, ct, ctime);
			}
			else {
				for (ct= targets.first; ct; ct= ct->next)
					Mat4One(ct->matrix);
			}
		}
		
		/* Solve the constraint */
		cti->evaluate_constraint(con, cob, &targets);
		
		/* clear targets after use 
		 *	- this should free temp targets but no data should be copied back
		 *	  as constraints may have done some nasty things to it...
		 */
		if (cti->flush_constraint_targets) {
			cti->flush_constraint_targets(con, &targets, 1);
		}
		
		/* Interpolate the enforcement, to blend result of constraint into final owner transform */
		/* 1. Remove effects of original matrix from constraint solution ==> delta */
		Mat4Invert(imat, oldmat);
		Mat4CpyMat4(solution, cob->matrix);
		Mat4MulMat4(delta, solution, imat);
		
		/* 2. If constraint influence is not full strength, then interpolate
		 * 	identity_matrix --> delta_matrix to get the effect the constraint actually exerts
		 */
		if (enf < 1.0) {
			float identity[4][4];
			Mat4One(identity);
			Mat4BlendMat4(delta, identity, delta, enf);
		}
		
		/* 3. Now multiply the delta by the matrix in use before the evaluation */
		Mat4MulMat4(cob->matrix, delta, oldmat);
		
		/* move owner back into worldspace for next constraint/other business */
		if ((con->flag & CONSTRAINT_SPACEONCE) == 0) 
			constraint_mat_convertspace(cob->ob, cob->pchan, cob->matrix, con->ownspace, CONSTRAINT_SPACE_WORLD);
	}
}
