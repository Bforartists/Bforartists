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

#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifndef WIN32
#include <unistd.h>
#else
#include <io.h>
#include "BLI_winstuff.h"
#endif

#include "MEM_guardedalloc.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_camera_types.h"
#include "DNA_curve_types.h"
#include "DNA_effect_types.h"
#include "DNA_ika_types.h"
#include "DNA_image_types.h"
#include "DNA_ipo_types.h"
#include "DNA_key_types.h"
#include "DNA_lamp_types.h"
#include "DNA_lattice_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_meta_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_texture_types.h"
#include "DNA_view3d_types.h"
#include "DNA_world_types.h"
#include "DNA_userdef_types.h"
#include "DNA_property_types.h"
#include "DNA_vfont_types.h"
#include "DNA_constraint_types.h"

#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_editview.h"
#include "BIF_resources.h"
#include "BIF_mywindow.h"
#include "BIF_gl.h"
#include "BIF_editlattice.h"
#include "BIF_editarmature.h"
#include "BIF_editmesh.h"

#include "BKE_action.h"
#include "BKE_anim.h"
#include "BKE_armature.h"
#include "BKE_curve.h"
#include "BKE_displist.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_lattice.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"

#include "BSE_edit.h"
#include "BSE_view.h"

#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "blendef.h"

#include "mydevice.h"

#include "transform.h"
#include "transform_generics.h"
#include "transform_constraints.h"

extern ListBase editNurb;
extern ListBase editelems;

/* GLOBAL VARIABLE THAT SHOULD MOVED TO SCREEN MEMBER OR SOMETHING  */
extern TransInfo Trans;

/* ************************** Functions *************************** */

/* ************************** GENERICS **************************** */

/* called for objects updating while transform acts, once per redraw */
void recalcData(TransInfo *t)
{
	Base *base;
	
	if(G.obpose) {
		TransData *td= t->data;
		bPoseChannel	*chan;
		int	i;
		
		if (!G.obpose->pose) G.obpose->pose= MEM_callocN(sizeof(bPose), "pose");
		
		/*	Make channels for the transforming bones (in posemode) */
		for (i=0; i<t->total; i++, td++) {
			chan = MEM_callocN (sizeof (bPoseChannel), "transPoseChannel");
			
			if (t->mode == TFM_ROTATION || t->mode == TFM_TRACKBALL) {
				chan->flag |= POSE_ROT;
				memcpy (chan->quat, td->ext->quat, sizeof (chan->quat));
			}
			if (t->mode == TFM_TRANSLATION) {
				chan->flag |= POSE_LOC;
				memcpy (chan->loc, td->loc, sizeof (chan->loc));
			}
			if (t->mode == TFM_RESIZE) {
				chan->flag |= POSE_SIZE;
				memcpy (chan->size, td->ext->size, sizeof (chan->size));
			}
			
			strcpy (chan->name, ((Bone*) td->ext->bone)->name);
			
			set_pose_channel (G.obpose->pose, chan);

		}
		
		clear_pose_constraint_status(G.obpose);
		
		if (!is_delay_deform()) make_displists_by_armature(G.obpose);
		
	}
	else if (G.obedit) {
		if (G.obedit->type == OB_MESH) {
			recalc_editnormals();
			makeDispList(G.obedit);
		}
		else if ELEM(G.obedit->type, OB_CURVE, OB_SURF) {
			Nurb *nu= editNurb.first;
			while(nu) {
				test2DNurb(nu);
				testhandlesNurb(nu); /* test for bezier too */
				nu= nu->next;
			}
			makeDispList(G.obedit);

			makeBevelList(G.obedit); // might be needed for deform
			calc_curvepath(G.obedit);
			
			// deform, bevel, taper
			base= FIRSTBASE;
			while(base) {
				if(base->lay & G.vd->lay) {
					if(base->object->parent==G.obedit && base->object->partype==PARSKEL)
						makeDispList(base->object);
					else if(base->object->type==OB_CURVE) {
						Curve *cu= base->object->data;
						if(G.obedit==cu->bevobj || G.obedit==cu->taperobj)
							makeDispList(base->object);
					}
				}
				base= base->next;
			}
		}
		else if(G.obedit->type==OB_ARMATURE){
			EditBone *ebo;
			
			/* Ensure all bones are correctly adjusted */
			for (ebo=G.edbo.first; ebo; ebo=ebo->next){
				
				if ((ebo->flag & BONE_IK_TOPARENT) && ebo->parent){
					/* If this bone has a parent tip that has been moved */
					if (ebo->parent->flag & BONE_TIPSEL){
						VECCOPY (ebo->head, ebo->parent->tail);
					}
					/* If this bone has a parent tip that has NOT been moved */
					else{
						VECCOPY (ebo->parent->tail, ebo->head);
					}
				}
			}
		}
		else if(G.obedit->type==OB_LATTICE) {
			
			if(editLatt->flag & LT_OUTSIDE) outside_lattice(editLatt);
			
			base= FIRSTBASE;
			while(base) {
				if(base->lay & G.vd->lay) {
					if(base->object->parent==G.obedit) {
						makeDispList(base->object);
					}
				}
				base= base->next;
			}
		}
		else if (G.obedit->type == OB_MBALL) {
	 		makeDispList(G.obedit);	
  		}   	
	}
	else {
		
		base= FIRSTBASE;
		while(base) {
			if(base->flag & BA_DO_IPO) {
				if(base->object->ipo) {
					IpoCurve *icu;
					
					base->object->ctime= -1234567.0;
					
					icu= base->object->ipo->curve.first;
					while(icu) {
						calchandles_ipocurve(icu);
						icu= icu->next;
					}
				}				
			}
			if(base->object->partype & PARSLOW) {
				base->object->partype -= PARSLOW;
				where_is_object(base->object);
				base->object->partype |= PARSLOW;
			}
			else if(base->flag & BA_WHERE_UPDATE) {
				where_is_object(base->object);
			}
			
			base= base->next;
		} 
		
		base= FIRSTBASE;
		while(base) {
			
			if(base->flag & BA_DISP_UPDATE) makeDispList(base->object);
			
			base= base->next;
		}
	}
	
	/* ugly stuff for posemode, copied from old system */
	base= FIRSTBASE;
	while(base) {
		extern int pose_flags_reset_done(Object *ob);	// linker solves
		
		if (pose_flags_reset_done(base->object)) {
			if (!is_delay_deform())
				make_displists_by_armature(base->object);
		}
		
		base= base->next;
	}
	
	if (G.obpose && G.obpose->type == OB_ARMATURE)
		clear_pose_constraint_status(G.obpose);
	
	if (!is_delay_deform()) make_displists_by_armature(G.obpose);

	
	/* update shaded drawmode while transform */
	if(G.vd->drawtype == OB_SHADED) reshadeall_displist();
	
}

void initTransModeFlags(TransInfo *t, int mode) 
{
	t->flag = 0;
	t->num.flag = 0;
	t->mode = mode;
	
	switch (mode) {
	case TFM_RESIZE:
		t->num.flag |= NULLONE;
		t->num.flag |= AFFECTALL;
		if (!G.obedit) {
			t->flag |= NOZERO;
			t->num.flag |= NOZERO;
		}
		break;
	case TFM_TOSPHERE:
		t->num.flag |= NULLONE;
		t->num.flag |= NONEGATIVE;
		t->flag |= NOCONSTRAINT;
		break;
	case TFM_SHEAR:
		t->flag |= NOCONSTRAINT;
		break;
	}
}

void drawLine(float *center, float *dir, char axis, short options)
{
	extern void make_axis_color(char *col, char *col2, char axis);	// drawview.c
	float v1[3], v2[3], v3[3];
	char col[3], col2[3];
	
	//if(G.obedit) mymultmatrix(G.obedit->obmat);	// sets opengl viewing

	VecCopyf(v3, dir);
	VecMulf(v3, G.vd->far);
	
	VecSubf(v2, center, v3);
	VecAddf(v1, center, v3);

	if (options & DRAWLIGHT) {
		col[0] = col[1] = col[2] = 220;
	}
	else {
		BIF_GetThemeColor3ubv(TH_GRID, col);
	}
	make_axis_color(col, col2, axis);
	glColor3ubv(col2);

	setlinestyle(0);
	glLineWidth(2.0);
	glBegin(GL_LINE_STRIP); 
		glVertex3fv(v1); 
		glVertex3fv(v2); 
	glEnd();
	glLineWidth(1.0);
	
	myloadmatrix(G.vd->viewmat);
}

void initTrans (TransInfo *t)
{

	/* moving: is shown in drawobject() (transform color) */
	if(G.obedit || G.obpose) G.moving= G_TRANSFORM_EDIT;
	else G.moving= G_TRANSFORM_OBJ;

	t->data = NULL;
	t->ext = NULL;

	getmouseco_areawin(t->imval);
	t->con.imval[0] = t->imval[0];
	t->con.imval[1] = t->imval[1];

	t->transform		= NULL;

	t->total			=
		t->num.idx		=
		t->num.idx_max	=
		t->num.ctrl[0]	= 
		t->num.ctrl[1]	= 
		t->num.ctrl[2]	= 0;

	t->val = 0.0f;

	t->num.val[0]		= 
		t->num.val[1]	= 
		t->num.val[2]	= 0.0f;

	t->vec[0]			=
		t->vec[1]		=
		t->vec[2]		= 0.0f;
	
	Mat3One(t->mat);
}

/* Here I would suggest only TransInfo related issues, like free data & reset vars. Not redraws */
void postTrans (TransInfo *t) 
{
	TransData *td;
	int a;
	
	G.moving = 0; // Set moving flag off (display as usual)

	stopConstraint(t);
	t->con.drawExtra = NULL;
	t->con.applyVec	= NULL;
	t->con.applySize= NULL;
	t->con.applyRot	= NULL;
	t->con.mode		= 0;

	/* since ipokeys are optional on objects, we mallocced them per trans-data */
	for(a=0, td= t->data; a<t->total; a++, td++) {
		if(td->tdi) MEM_freeN(td->tdi);
	}
	
	MEM_freeN(t->data);
	t->data = NULL;

	if (t->ext) MEM_freeN(t->ext);
	
}

void apply_grid3(float *val, int max_index, float fac1, float fac2, float fac3)
{
	/* fac1 is for 'nothing', fac2 for CTRL, fac3 for SHIFT */
	int invert = U.flag & USER_AUTOGRABGRID;
	int ctrl;
	int i;

	for (i=0; i<=max_index; i++) {

		if(invert) {
			if(G.qual & LR_CTRLKEY) ctrl= 0;
			else ctrl= 1;
		}
		else ctrl= (G.qual & LR_CTRLKEY);

		if(ctrl && (G.qual & LR_SHIFTKEY)) {
			if(fac3!= 0.0) {
				for (i=0; i<=max_index; i++) {
					val[i]= fac3*(float)floor(val[i]/fac3 +.5);
				}
			}
		}
		else if(ctrl) {
			if(fac2!= 0.0) {
				for (i=0; i<=max_index; i++) {
					val[i]= fac2*(float)floor(val[i]/fac2 +.5);
				}
			}
		}
		else {
			if(fac1!= 0.0) {
				for (i=0; i<=max_index; i++) {
					val[i]= fac1*(float)floor(val[i]/fac1 +.5);
				}
			}
		}
	}
}

void snapGrid(TransInfo *t, float *val) {
	apply_grid3(val, t->idx_max, t->snap[0], t->snap[1], t->snap[2]);
}

void applyTransObjects(TransInfo *t)
{
	TransData *td;
	
	for (td = t->data; td < t->data + t->total; td++) {
		VECCOPY(td->iloc, td->loc);
		if (td->ext->rot) {
			VECCOPY(td->ext->irot, td->ext->rot);
		}
		if (td->ext->size) {
			VECCOPY(td->ext->isize, td->ext->size);
		}
	}	
	recalcData(t);
} 

/* helper for below */
static void restore_ipokey(float *poin, float *old)
{
	if(poin) {
		poin[0]= old[0];
		poin[-3]= old[3];
		poin[3]= old[6];
	}
}

void restoreElement(TransData *td) {
	VECCOPY(td->loc, td->iloc);
	if (td->val) {
		*td->val = td->ival;
	}
	if (td->ext) {
		if (td->ext->rot) {
			VECCOPY(td->ext->rot, td->ext->irot);
		}
		if (td->ext->size) {
			VECCOPY(td->ext->size, td->ext->isize);
		}
		if(td->flag & TD_USEQUAT) {
			if (td->ext->quat) {
				QUATCOPY(td->ext->quat, td->ext->iquat);
			}
		}
	}
	if(td->tdi) {
		TransDataIpokey *tdi= td->tdi;
		
		restore_ipokey(tdi->locx, tdi->oldloc);
		restore_ipokey(tdi->locy, tdi->oldloc+1);
		restore_ipokey(tdi->locz, tdi->oldloc+2);

		restore_ipokey(tdi->rotx, tdi->oldrot);
		restore_ipokey(tdi->roty, tdi->oldrot+1);
		restore_ipokey(tdi->rotz, tdi->oldrot+2);
		
		restore_ipokey(tdi->sizex, tdi->oldsize);
		restore_ipokey(tdi->sizey, tdi->oldsize+1);
		restore_ipokey(tdi->sizez, tdi->oldsize+2);
	}
}

void restoreTransObjects(TransInfo *t)
{
	TransData *td;
	
	for (td = t->data; td < t->data + t->total; td++) {
		restoreElement(td);
	}	
	recalcData(t);
} 

void calculateCenterCursor(TransInfo *t)
{
	float *cursor;

	cursor = give_cursor();
	VECCOPY(t->center, cursor);

	if(t->flag & (T_EDIT|T_POSE)) {
		Object *ob= G.obedit?G.obedit:G.obpose;
		float mat[3][3], imat[3][3];
		float vec[3];
		
		VecSubf(t->center, t->center, ob->obmat[3]);
		Mat3CpyMat4(mat, ob->obmat);
		Mat3Inv(imat, mat);
		Mat3MulVecfl(imat, t->center);
		
		VECCOPY(vec, t->center);
		Mat4MulVecfl(ob->obmat, vec);
		project_short_noclip(vec, t->center2d);
	}
	else {
		project_short_noclip(t->center, t->center2d);
	}
}

void calculateCenterMedian(TransInfo *t)
{
	float partial[3] = {0.0f, 0.0f, 0.0f};
	int i;
	for(i = 0; i < t->total; i++) {
		if (t->data[i].flag & TD_SELECTED) {
			VecAddf(partial, partial, t->data[i].center);
		}
		else {
			/* 
			   All the selected elements are at the head of the array 
			   which means we can stop when it finds unselected data
			*/
			break;
		}
	}
	VecMulf(partial, 1.0f / t->total);
	VECCOPY(t->center, partial);

	if (t->flag & (T_EDIT|T_POSE)) {
		Object *ob= G.obedit?G.obedit:G.obpose;
		float vec[3];
		
		VECCOPY(vec, t->center);
		Mat4MulVecfl(ob->obmat, vec);
		project_short_noclip(vec, t->center2d);
	}
	else {
		project_short_noclip(t->center, t->center2d);
	}
}

void calculateCenterBound(TransInfo *t)
{
	float max[3];
	float min[3];
	int i;
	for(i = 0; i < t->total; i++) {
		if (i) {
			if (t->data[i].flag & TD_SELECTED) {
				MinMax3(min, max, t->data[i].center);
			}
			else {
				/* 
				   All the selected elements are at the head of the array 
				   which means we can stop when it finds unselected data
				*/
				break;
			}
		}
		else {
			VECCOPY(max, t->data[i].center);
			VECCOPY(min, t->data[i].center);
		}
	}
	VecAddf(t->center, min, max);
	VecMulf(t->center, 0.5);

	if (t->flag & (T_EDIT|T_POSE)) {
		Object *ob= G.obedit?G.obedit:G.obpose;
		float vec[3];
		
		VECCOPY(vec, t->center);
		Mat4MulVecfl(ob->obmat, vec);
		project_short_noclip(vec, t->center2d);
	}
	else {
		project_short_noclip(t->center, t->center2d);
	}
}

void calculateCenter(TransInfo *t) 
{
	switch(G.vd->around) {
	case V3D_CENTRE:
		calculateCenterBound(t);
		break;
	case V3D_CENTROID:
		calculateCenterMedian(t);
		break;
	case V3D_CURSOR:
		calculateCenterCursor(t);
		break;
	case V3D_LOCAL:
		// NEED TO REPLACE THIS
		calculateCenterMedian(t);
		printf("local\n");
		break;
	}

	/* setting constraint center */
	VECCOPY(t->con.center, t->center);
	if(t->flag & (T_EDIT|T_POSE)) {
		Object *ob= G.obedit?G.obedit:G.obpose;
		Mat4MulVecfl(ob->obmat, t->con.center);
	}

	/* voor panning from cameraview */
	if(t->flag & T_OBJECT) {
		if( G.vd->camera==OBACT && G.vd->persp>1) {
			float axis[3];
			VECCOPY(axis, G.vd->persinv[2]);
			Normalise(axis);
			
			/* 6.0 = 6 grid units */
			t->center[0]+= -6.0f*axis[0];
			t->center[1]+= -6.0f*axis[1];
			t->center[2]+= -6.0f*axis[2];
		}
	}	
	initgrabz(t->center[0], t->center[1], t->center[2]);
}

void calculatePropRatio(TransInfo *t)
{
	TransData *td = t->data;
	int i;
	float dist;
	extern int prop_mode;

	if (G.f & G_PROPORTIONAL) {
		for(i = 0 ; i < t->total; i++, td++) {
			if (td->flag & TD_SELECTED) {
				td->factor = 1.0f;
			}
			else if (td->dist > t->propsize) {
				/* 
				   The elements are sorted according to their dist member in the array,
				   that means we can stop when it finds one element outside of the propsize.
				*/
				td->flag |= TD_NOACTION;
				td->factor = 0.0f;
				restoreElement(td);
			}
			else {
				td->flag &= ~TD_NOACTION;
				dist= (t->propsize-td->dist)/t->propsize;
				switch(prop_mode) {
				case PROP_SHARP:
					td->factor= dist*dist;
					break;
				case PROP_SMOOTH:
					td->factor= 3.0f*dist*dist - 2.0f*dist*dist*dist;
					break;
				case PROP_ROOT:
					td->factor = (float)sqrt(dist);
					break;
				case PROP_LIN:
					td->factor = dist;
					break;
				case PROP_CONST:
					td->factor = 1;
					//td->factor = (float)sqrt(2*dist - dist * dist);
					break;
				default:
					td->factor = 1;
				}
			}
		}
		switch(prop_mode) {
		case PROP_SHARP:
			strcpy(t->proptext, "(Quad)");
			break;
		case PROP_SMOOTH:
			strcpy(t->proptext, "(Smooth)");
			break;
		case PROP_ROOT:
			strcpy(t->proptext, "(Root)");
			break;
		case PROP_LIN:
			strcpy(t->proptext, "(Linear)");
			break;
		case PROP_CONST:
			//strcpy(t->proptext, "(Sphere)");
			strcpy(t->proptext, "(Constant)");
			break;
		default:
			strcpy(t->proptext, "");
		}
	}
	else {
		for(i = 0 ; i < t->total; i++, td++) {
			td->factor = 1.0;
		}
		strcpy(t->proptext, "");
	}
}

TransInfo * BIF_GetTransInfo() {
	return &Trans;
}

