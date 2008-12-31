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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Martin Poirier
 *
 * ***** END GPL LICENSE BLOCK *****
 */
 
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include <stdio.h>

#include "PIL_time.h"

#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_meshdata_types.h" // Temporary, for snapping to other unselected meshes
#include "DNA_space_types.h"
#include "DNA_screen_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"

#include "BLI_arithb.h"
#include "BLI_editVert.h"

//#include "BDR_drawobject.h"
//
//#include "editmesh.h"
//#include "BIF_editsima.h"
#include "BIF_gl.h"
#include "BIF_glutil.h"
//#include "BIF_mywindow.h"
//#include "BIF_resources.h"
//#include "BIF_screen.h"
//#include "BIF_editsima.h"
//#include "BIF_drawimage.h"
//#include "BIF_editmesh.h"

#include "BKE_global.h"
#include "BKE_utildefines.h"
#include "BKE_DerivedMesh.h"
#include "BKE_object.h"
#include "BKE_anim.h" /* for duplis */
#include "BKE_context.h"

#include "ED_view3d.h"

#include "MEM_guardedalloc.h"

#include "transform.h"
#include "WM_types.h"
//#include "blendef.h" /* for selection modes */

static EditVert *EM_get_vert_for_index(int x) {return 0;}	// XXX
static EditEdge *EM_get_edge_for_index(int x) {return 0;}	// XXX
static EditFace *EM_get_face_for_index(int x) {return 0;}	// XXX
static void EM_init_index_arrays(int x, int y, int z) {} // XXX
static void EM_free_index_arrays(void) {}		// XXX

/********************* PROTOTYPES ***********************/

void setSnappingCallback(TransInfo *t);

void ApplySnapTranslation(TransInfo *t, float vec[3]);
void ApplySnapRotation(TransInfo *t, float *vec);
void ApplySnapResize(TransInfo *t, float *vec);

void CalcSnapGrid(TransInfo *t, float *vec);
void CalcSnapGeometry(TransInfo *t, float *vec);

void TargetSnapMedian(TransInfo *t);
void TargetSnapCenter(TransInfo *t);
void TargetSnapClosest(TransInfo *t);
void TargetSnapActive(TransInfo *t);

float RotationBetween(TransInfo *t, float p1[3], float p2[3]);
float TranslationBetween(TransInfo *t, float p1[3], float p2[3]);
float ResizeBetween(TransInfo *t, float p1[3], float p2[3]);

/* Modes */
#define NOT_SELECTED 0
#define NOT_ACTIVE 1
int snapObjects(TransInfo *t, int *dist, float *loc, float *no, int mode);


/****************** IMPLEMENTATIONS *********************/

int BIF_snappingSupported(Object *obedit)
{
	int status = 0;
	
	if (obedit == NULL || obedit->type==OB_MESH) /* only support object or mesh */
	{
		status = 1;
	}
	
	return status;
}

void drawSnapping(TransInfo *t)
{
	if ((t->tsnap.status & (SNAP_ON|POINT_INIT|TARGET_INIT)) == (SNAP_ON|POINT_INIT|TARGET_INIT) &&
		(t->event->ctrl))
		{
		
		char col[4] = {1, 0, 1};
		//BIF_GetThemeColor3ubv(TH_TRANSFORM, col);
		glColor4ub(col[0], col[1], col[2], 128);
		
		if (t->spacetype == SPACE_VIEW3D) {
			View3D *v3d = t->view;
			float unitmat[4][4];
			float size;
			
			glDisable(GL_DEPTH_TEST);
	
			size = get_drawsize(v3d, t->sa, t->tsnap.snapPoint);
			
			//size *= 0.5f * BIF_GetThemeValuef(TH_VERTEX_SIZE);
			
			glPushMatrix();
			
			glTranslatef(t->tsnap.snapPoint[0], t->tsnap.snapPoint[1], t->tsnap.snapPoint[2]);
			
			/* draw normal if needed */
			if (usingSnappingNormal(t) && validSnappingNormal(t))
			{
				glBegin(GL_LINES);
					glVertex3f(0, 0, 0);
					glVertex3f(t->tsnap.snapNormal[0], t->tsnap.snapNormal[1], t->tsnap.snapNormal[2]);
				glEnd();
			}
			
			/* sets view screen aligned */
			glRotatef( -360.0f*saacos(v3d->viewquat[0])/(float)M_PI, v3d->viewquat[1], v3d->viewquat[2], v3d->viewquat[3]);
			
			Mat4One(unitmat);
			// TRANSFORM_FIX_ME
			//drawcircball(GL_LINE_LOOP, unitmat[3], size, unitmat);
			
			glPopMatrix();
			
			if(v3d->zbuf)
				glEnable(GL_DEPTH_TEST);
		}
		else if (t->spacetype==SPACE_IMAGE)
		{
			/*This will not draw, and Im nor sure why - campbell */
			
			/*			
			float xuser_asp, yuser_asp;
			int wi, hi;
			float w, h;
			
			calc_image_view(G.sima, 'f');	// float
			myortho2(G.v2d->cur.xmin, G.v2d->cur.xmax, G.v2d->cur.ymin, G.v2d->cur.ymax);
			glLoadIdentity();
			
			aspect_sima(G.sima, &xuser_asp, &yuser_asp);
			
			transform_width_height_tface_uv(&wi, &hi);
			w = (((float)wi)/256.0f)*G.sima->zoom * xuser_asp;
			h = (((float)hi)/256.0f)*G.sima->zoom * yuser_asp;
			
			cpack(0xFFFFFF);
			glTranslatef(t->tsnap.snapPoint[0], t->tsnap.snapPoint[1], 0.0f);
			
			//glRectf(0,0,1,1);
			
			setlinestyle(0);
			cpack(0x0);
			fdrawline(-0.020/w, 0, -0.1/w, 0);
			fdrawline(0.1/w, 0, .020/w, 0);
			fdrawline(0, -0.020/h, 0, -0.1/h);
			fdrawline(0, 0.1/h, 0, 0.020/h);
			
			glTranslatef(-t->tsnap.snapPoint[0], -t->tsnap.snapPoint[1], 0.0f);
			setlinestyle(0);
			*/
			
		}
	}
}

int  handleSnapping(TransInfo *t, wmEvent *event)
{
	int status = 0;
	
	if (BIF_snappingSupported(t->obedit) && event->type == TABKEY && event->shift)
	{
		/* toggle snap and reinit */
		G.scene->snap_flag ^= SCE_SNAP;
		initSnapping(t);
		status = 1;
	}
	
	return status;
}

void applySnapping(TransInfo *t, float *vec)
{
	if ((t->tsnap.status & SNAP_ON) && 
		(t->event->ctrl))
	{
		double current = PIL_check_seconds_timer();
		
		// Time base quirky code to go around findnearest slowness
		/* !TODO! add exception for object mode, no need to slow it down then */
		if (current - t->tsnap.last  >= 0.1)
		{
			t->tsnap.calcSnap(t, vec);
			t->tsnap.targetSnap(t);
	
			t->tsnap.last = current;
		}
		if ((t->tsnap.status & (POINT_INIT|TARGET_INIT)) == (POINT_INIT|TARGET_INIT))
		{
			t->tsnap.applySnap(t, vec);
		}
	}
}

void resetSnapping(TransInfo *t)
{
	t->tsnap.status = 0;
	t->tsnap.modePoint = 0;
	t->tsnap.modeTarget = 0;
	t->tsnap.last = 0;
	t->tsnap.applySnap = NULL;

	t->tsnap.snapNormal[0] = 0;
	t->tsnap.snapNormal[1] = 0;
	t->tsnap.snapNormal[2] = 0;
}

int usingSnappingNormal(TransInfo *t)
{
	if (G.scene->snap_flag & SCE_SNAP_ROTATE)
	{
		return 1;
	}
	else
	{
		return 0;
	}
}

int validSnappingNormal(TransInfo *t)
{
	if ((t->tsnap.status & (POINT_INIT|TARGET_INIT)) == (POINT_INIT|TARGET_INIT))
	{
		if (Inpf(t->tsnap.snapNormal, t->tsnap.snapNormal) > 0)
		{
			return 1;
		}
	}
	
	return 0;
}

void initSnapping(TransInfo *t)
{
	Scene *scene = t->scene;
	Object *obedit = NULL;
	resetSnapping(t);
	
	if ((t->spacetype == SPACE_VIEW3D || t->spacetype == SPACE_IMAGE) && // Only 3D view or UV
			(t->flag & T_CAMERA) == 0) { // Not with camera selected
		setSnappingCallback(t);

		/* Edit mode */
		if (t->tsnap.applySnap != NULL && // A snapping function actually exist
			(scene->snap_flag & SCE_SNAP) && // Only if the snap flag is on
			(obedit != NULL && obedit->type==OB_MESH) && // Temporary limited to edit mode meshes
			((t->flag & T_PROP_EDIT) == 0) ) // No PET, obviously
		{
			t->tsnap.status |= SNAP_ON;
			t->tsnap.modePoint = SNAP_GEO;
		}
		/* Object mode */
		else if (t->tsnap.applySnap != NULL && // A snapping function actually exist
			(scene->snap_flag & SCE_SNAP) && // Only if the snap flag is on
			(obedit == NULL) ) // Object Mode
		{
			t->tsnap.status |= SNAP_ON;
			t->tsnap.modePoint = SNAP_GEO;
		}
		else
		{	
			/* Grid if snap is not possible */
			t->tsnap.modePoint = SNAP_GRID;
		}
	}
	else
	{
		/* Always grid outside of 3D view */
		t->tsnap.modePoint = SNAP_GRID;
	}
}

void setSnappingCallback(TransInfo *t)
{
	Scene *scene = t->scene;
	t->tsnap.calcSnap = CalcSnapGeometry;

	switch(scene->snap_target)
	{
		case SCE_SNAP_TARGET_CLOSEST:
			t->tsnap.modeTarget = SNAP_CLOSEST;
			t->tsnap.targetSnap = TargetSnapClosest;
			break;
		case SCE_SNAP_TARGET_CENTER:
			t->tsnap.modeTarget = SNAP_CENTER;
			t->tsnap.targetSnap = TargetSnapCenter;
			break;
		case SCE_SNAP_TARGET_MEDIAN:
			t->tsnap.modeTarget = SNAP_MEDIAN;
			t->tsnap.targetSnap = TargetSnapMedian;
			break;
		case SCE_SNAP_TARGET_ACTIVE:
			t->tsnap.modeTarget = SNAP_ACTIVE;
			t->tsnap.targetSnap = TargetSnapActive;
			break;

	}

	switch (t->mode)
	{
	case TFM_TRANSLATION:
		t->tsnap.applySnap = ApplySnapTranslation;
		t->tsnap.distance = TranslationBetween;
		break;
	case TFM_ROTATION:
		t->tsnap.applySnap = ApplySnapRotation;
		t->tsnap.distance = RotationBetween;
		
		// Can't do TARGET_CENTER with rotation, use TARGET_MEDIAN instead
		if (scene->snap_target == SCE_SNAP_TARGET_CENTER) {
			t->tsnap.modeTarget = SNAP_MEDIAN;
			t->tsnap.targetSnap = TargetSnapMedian;
		}
		break;
	case TFM_RESIZE:
		t->tsnap.applySnap = ApplySnapResize;
		t->tsnap.distance = ResizeBetween;
		
		// Can't do TARGET_CENTER with resize, use TARGET_MEDIAN instead
		if (scene->snap_target == SCE_SNAP_TARGET_CENTER) {
			t->tsnap.modeTarget = SNAP_MEDIAN;
			t->tsnap.targetSnap = TargetSnapMedian;
		}
		break;
	default:
		t->tsnap.applySnap = NULL;
		break;
	}
}

/********************** APPLY **************************/

void ApplySnapTranslation(TransInfo *t, float vec[3])
{
	VecSubf(vec, t->tsnap.snapPoint, t->tsnap.snapTarget);
}

void ApplySnapRotation(TransInfo *t, float *vec)
{
	if (t->tsnap.modeTarget == SNAP_CLOSEST) {
		*vec = t->tsnap.dist;
	}
	else {
		*vec = RotationBetween(t, t->tsnap.snapTarget, t->tsnap.snapPoint);
	}
}

void ApplySnapResize(TransInfo *t, float vec[3])
{
	if (t->tsnap.modeTarget == SNAP_CLOSEST) {
		vec[0] = vec[1] = vec[2] = t->tsnap.dist;
	}
	else {
		vec[0] = vec[1] = vec[2] = ResizeBetween(t, t->tsnap.snapTarget, t->tsnap.snapPoint);
	}
}

/********************** DISTANCE **************************/

float TranslationBetween(TransInfo *t, float p1[3], float p2[3])
{
	return VecLenf(p1, p2);
}

float RotationBetween(TransInfo *t, float p1[3], float p2[3])
{
	float angle, start[3], end[3], center[3];
	
	VECCOPY(center, t->center);	
	if(t->flag & (T_EDIT|T_POSE)) {
		Object *ob= t->obedit?t->obedit:t->poseobj;
		Mat4MulVecfl(ob->obmat, center);
	}

	VecSubf(start, p1, center);
	VecSubf(end, p2, center);	
		
	// Angle around a constraint axis (error prone, will need debug)
	if (t->con.applyRot != NULL && (t->con.mode & CON_APPLY)) {
		float axis[3], tmp[3];
		
		t->con.applyRot(t, NULL, axis, NULL);

		Projf(tmp, end, axis);
		VecSubf(end, end, tmp);
		
		Projf(tmp, start, axis);
		VecSubf(start, start, tmp);
		
		Normalize(end);
		Normalize(start);
		
		Crossf(tmp, start, end);
		
		if (Inpf(tmp, axis) < 0.0)
			angle = -acos(Inpf(start, end));
		else	
			angle = acos(Inpf(start, end));
	}
	else {
		float mtx[3][3];
		
		Mat3CpyMat4(mtx, t->viewmat);

		Mat3MulVecfl(mtx, end);
		Mat3MulVecfl(mtx, start);
		
		angle = atan2(start[1],start[0]) - atan2(end[1],end[0]);
	}
	
	if (angle > M_PI) {
		angle = angle - 2 * M_PI;
	}
	else if (angle < -(M_PI)) {
		angle = 2 * M_PI + angle;
	}
	
	return angle;
}

float ResizeBetween(TransInfo *t, float p1[3], float p2[3])
{
	float d1[3], d2[3], center[3];
	
	VECCOPY(center, t->center);	
	if(t->flag & (T_EDIT|T_POSE)) {
		Object *ob= t->obedit?t->obedit:t->poseobj;
		Mat4MulVecfl(ob->obmat, center);
	}

	VecSubf(d1, p1, center);
	VecSubf(d2, p2, center);
	
	if (t->con.applyRot != NULL && (t->con.mode & CON_APPLY)) {
		Mat3MulVecfl(t->con.pmtx, d1);
		Mat3MulVecfl(t->con.pmtx, d2);
	}
	
	return VecLength(d2) / VecLength(d1);
}

/********************** CALC **************************/

void CalcSnapGrid(TransInfo *t, float *vec)
{
	snapGridAction(t, t->tsnap.snapPoint, BIG_GEARS);
}

void CalcSnapGeometry(TransInfo *t, float *vec)
{
	/* Object mode */
	if (t->obedit == NULL)
	{
		if (t->spacetype == SPACE_VIEW3D)
		{
			float vec[3];
			float no[3];
			int found = 0;
			int dist = 40; // Use a user defined value here
			
			found = snapObjects(t, &dist, vec, no, NOT_SELECTED);
			if (found == 1)
			{
				float tangent[3];
				
				VecSubf(tangent, vec, t->tsnap.snapPoint);
				tangent[2] = 0; 
				
				if (Inpf(tangent, tangent) > 0)
				{
					VECCOPY(t->tsnap.snapTangent, tangent);
				}
				
				VECCOPY(t->tsnap.snapPoint, vec);
				VECCOPY(t->tsnap.snapNormal, no);

				t->tsnap.status |=  POINT_INIT;
			}
			else
			{
				t->tsnap.status &= ~POINT_INIT;
			}
		}
	}
	/* Mesh edit mode */
	else if (t->obedit->type==OB_MESH)
	{
		if (t->spacetype == SPACE_VIEW3D)
		{
			float vec[3];
			float no[3];
			int found = 0;
			int dist = 40; // Use a user defined value here

			found = snapObjects(t, &dist, vec, no, NOT_ACTIVE);
			if (found == 1)
			{
				VECCOPY(t->tsnap.snapPoint, vec);
				VECCOPY(t->tsnap.snapNormal, no);
				
				t->tsnap.status |=  POINT_INIT;
			}
			else
			{
				t->tsnap.status &= ~POINT_INIT;
			}
		}
		else if (t->spacetype == SPACE_IMAGE)
		{	/* same as above but for UV's */
			MTFace *nearesttf=NULL;
			float aspx, aspy;
			int face_corner;
			
			// TRANSFORM_FIX_ME
			//find_nearest_uv(&nearesttf, NULL, NULL, &face_corner);

			if (nearesttf != NULL)
			{
				VECCOPY2D(t->tsnap.snapPoint, nearesttf->uv[face_corner]);

				// TRANSFORM_FIX_ME
				//transform_aspect_ratio_tface_uv(&aspx, &aspy);
				t->tsnap.snapPoint[0] *= aspx;
				t->tsnap.snapPoint[1] *= aspy;

				Mat4MulVecfl(t->obedit->obmat, t->tsnap.snapPoint);
				
				t->tsnap.status |=  POINT_INIT;
			}
			else
			{
				t->tsnap.status &= ~POINT_INIT;
			}
		}
	}
}

/********************** TARGET **************************/

void TargetSnapCenter(TransInfo *t)
{
	// Only need to calculate once
	if ((t->tsnap.status & TARGET_INIT) == 0)
	{
		VECCOPY(t->tsnap.snapTarget, t->center);	
		if(t->flag & (T_EDIT|T_POSE)) {
			Object *ob= t->obedit?t->obedit:t->poseobj;
			Mat4MulVecfl(ob->obmat, t->tsnap.snapTarget);
		}
		
		t->tsnap.status |= TARGET_INIT;		
	}
}

void TargetSnapActive(TransInfo *t)
{
	// Only need to calculate once
	if ((t->tsnap.status & TARGET_INIT) == 0)
	{
		TransData *td = NULL;
		TransData *active_td = NULL;
		int i;

		for(td = t->data, i = 0 ; i < t->total && td->flag & TD_SELECTED ; i++, td++)
		{
			if (td->flag & TD_ACTIVE)
			{
				active_td = td;
				break;
			}
		}

		if (active_td)
		{	
			VECCOPY(t->tsnap.snapTarget, active_td->center);
				
			if(t->flag & (T_EDIT|T_POSE)) {
				Object *ob= t->obedit?t->obedit:t->poseobj;
				Mat4MulVecfl(ob->obmat, t->tsnap.snapTarget);
			}
			
			t->tsnap.status |= TARGET_INIT;
		}
		/* No active, default to median */
		else
		{
			t->tsnap.modeTarget = SNAP_MEDIAN;
			t->tsnap.targetSnap = TargetSnapMedian;
			TargetSnapMedian(t);
		}		
	}
}

void TargetSnapMedian(TransInfo *t)
{
	// Only need to calculate once
	if ((t->tsnap.status & TARGET_INIT) == 0)
	{
		TransData *td = NULL;
		int i;

		t->tsnap.snapTarget[0] = 0;
		t->tsnap.snapTarget[1] = 0;
		t->tsnap.snapTarget[2] = 0;
		
		for(td = t->data, i = 0 ; i < t->total && td->flag & TD_SELECTED ; i++, td++)
		{
			VecAddf(t->tsnap.snapTarget, t->tsnap.snapTarget, td->center);
		}
		
		VecMulf(t->tsnap.snapTarget, 1.0 / t->total);
		
		if(t->flag & (T_EDIT|T_POSE)) {
			Object *ob= t->obedit?t->obedit:t->poseobj;
			Mat4MulVecfl(ob->obmat, t->tsnap.snapTarget);
		}
		
		t->tsnap.status |= TARGET_INIT;		
	}
}

void TargetSnapClosest(TransInfo *t)
{
	// Only valid if a snap point has been selected
	if (t->tsnap.status & POINT_INIT)
	{
		TransData *closest = NULL, *td = NULL;
		
		/* Object mode */
		if (t->flag & T_OBJECT)
		{
			int i;
			for(td = t->data, i = 0 ; i < t->total && td->flag & TD_SELECTED ; i++, td++)
			{
				struct BoundBox *bb = object_get_boundbox(td->ob);
				
				/* use boundbox if possible */
				if (bb)
				{
					int j;
					
					for (j = 0; j < 8; j++) {
						float loc[3];
						float dist;
						
						VECCOPY(loc, bb->vec[j]);
						Mat4MulVecfl(td->ext->obmat, loc);
						
						dist = t->tsnap.distance(t, loc, t->tsnap.snapPoint);
						
						if (closest == NULL || fabs(dist) < fabs(t->tsnap.dist))
						{
							VECCOPY(t->tsnap.snapTarget, loc);
							closest = td;
							t->tsnap.dist = dist; 
						}
					}
				}
				/* use element center otherwise */
				else
				{
					float loc[3];
					float dist;
					
					VECCOPY(loc, td->center);
					
					dist = t->tsnap.distance(t, loc, t->tsnap.snapPoint);
					
					if (closest == NULL || fabs(dist) < fabs(t->tsnap.dist))
					{
						VECCOPY(t->tsnap.snapTarget, loc);
						closest = td;
						t->tsnap.dist = dist; 
					}
				}
			}
		}
		else
		{
			int i;
			for(td = t->data, i = 0 ; i < t->total && td->flag & TD_SELECTED ; i++, td++)
			{
				float loc[3];
				float dist;
				
				VECCOPY(loc, td->center);
				
				if(t->flag & (T_EDIT|T_POSE)) {
					Object *ob= t->obedit?t->obedit:t->poseobj;
					Mat4MulVecfl(ob->obmat, loc);
				}
				
				dist = t->tsnap.distance(t, loc, t->tsnap.snapPoint);
				
				if (closest == NULL || fabs(dist) < fabs(t->tsnap.dist))
				{
					VECCOPY(t->tsnap.snapTarget, loc);
					closest = td;
					t->tsnap.dist = dist; 
				}
			}
		}
		
		t->tsnap.status |= TARGET_INIT;
	}
}
/*================================================================*/

int snapDerivedMesh(TransInfo *t, Object *ob, DerivedMesh *dm, float obmat[][4], float ray_start[3], float ray_normal[3], short mval[2], float *loc, float *no, int *dist, float *depth, short EditMesh)
{
	int retval = 0;
	int totvert = dm->getNumVerts(dm);
	int totface = dm->getNumFaces(dm);
	
	if (totvert > 0) {
		float imat[4][4];
		float timat[3][3]; /* transpose inverse matrix for normals */
		float ray_start_local[3], ray_normal_local[3];
		int test = 1;

		Mat4Invert(imat, obmat);

		Mat3CpyMat4(timat, imat);
		Mat3Transp(timat);
		
		VECCOPY(ray_start_local, ray_start);
		VECCOPY(ray_normal_local, ray_normal);
		
		Mat4MulVecfl(imat, ray_start_local);
		Mat4Mul3Vecfl(imat, ray_normal_local);
		
		
		/* If number of vert is more than an arbitrary limit, 
		 * test against boundbox first
		 * */
		if (totface > 16) {
			struct BoundBox *bb = object_get_boundbox(ob);
			test = ray_hit_boundbox(bb, ray_start_local, ray_normal_local);
		}
		
		if (test == 1) {
			
			switch (G.scene->snap_mode)
			{
				case SCE_SNAP_MODE_FACE:
				{ 
					MVert *verts = dm->getVertArray(dm);
					MFace *faces = dm->getFaceArray(dm);
					int *index_array = NULL;
					int index = 0;
					int i;
					
					if (EditMesh)
					{
						index_array = dm->getFaceDataArray(dm, CD_ORIGINDEX);
						EM_init_index_arrays(0, 0, 1);
					}
					
					for( i = 0; i < totface; i++) {
						EditFace *efa = NULL;
						MFace *f = faces + i;
						float lambda;
						int result;
						
						test = 1; /* reset for every face */
					
						if (EditMesh)
						{
							if (index_array)
							{
								index = index_array[i];
							}
							else
							{
								index = i;
							}
							
							if (index == ORIGINDEX_NONE)
							{
								test = 0;
							}
							else
							{
								efa = EM_get_face_for_index(index);
								
								if (efa && (efa->h || (efa->v1->f & SELECT) || (efa->v2->f & SELECT) || (efa->v3->f & SELECT) || (efa->v4 && efa->v4->f & SELECT)))
								{
									test = 0;
								}
							}
						}
						
						
						if (test)
						{
							result = RayIntersectsTriangle(ray_start_local, ray_normal_local, verts[f->v1].co, verts[f->v2].co, verts[f->v3].co, &lambda, NULL);
							
							if (result) {
								float location[3], normal[3];
								float intersect[3];
								float new_depth;
								int screen_loc[2];
								int new_dist;
								
								VECCOPY(intersect, ray_normal_local);
								VecMulf(intersect, lambda);
								VecAddf(intersect, intersect, ray_start_local);
								
								VECCOPY(location, intersect);
								
								if (f->v4)
									CalcNormFloat4(verts[f->v1].co, verts[f->v2].co, verts[f->v3].co, verts[f->v4].co, normal);
								else
									CalcNormFloat(verts[f->v1].co, verts[f->v2].co, verts[f->v3].co, normal);

								Mat4MulVecfl(obmat, location);
								
								new_depth = VecLenf(location, ray_start);					
								
								project_int(t->ar, t->view, location, screen_loc);
								new_dist = abs(screen_loc[0] - mval[0]) + abs(screen_loc[1] - mval[1]);
								
								if (new_dist <= *dist && new_depth < *depth)
								{
									*depth = new_depth;
									retval = 1;
									
									VECCOPY(loc, location);
									VECCOPY(no, normal);
									
									Mat3MulVecfl(timat, no);
									Normalize(no);
					
									*dist = new_dist;
								} 
							}
					
							if (f->v4 && result == 0)
							{
								result = RayIntersectsTriangle(ray_start_local, ray_normal_local, verts[f->v3].co, verts[f->v4].co, verts[f->v1].co, &lambda, NULL);
								
								if (result) {
									float location[3], normal[3];
									float intersect[3];
									float new_depth;
									int screen_loc[2];
									int new_dist;
									
									VECCOPY(intersect, ray_normal_local);
									VecMulf(intersect, lambda);
									VecAddf(intersect, intersect, ray_start_local);
									
									VECCOPY(location, intersect);
									
									if (f->v4)
										CalcNormFloat4(verts[f->v1].co, verts[f->v2].co, verts[f->v3].co, verts[f->v4].co, normal);
									else
										CalcNormFloat(verts[f->v1].co, verts[f->v2].co, verts[f->v3].co, normal);
	
									Mat4MulVecfl(obmat, location);
									
									new_depth = VecLenf(location, ray_start);					
									
									project_int(t->ar, t->view, location, screen_loc);
									new_dist = abs(screen_loc[0] - mval[0]) + abs(screen_loc[1] - mval[1]);
									
									if (new_dist <= *dist && new_depth < *depth)
									{
										*depth = new_depth;
										retval = 1;
										
										VECCOPY(loc, location);
										VECCOPY(no, normal);
										
										Mat3MulVecfl(timat, no);
										Normalize(no);
						
										*dist = new_dist;
									}
								} 
							}
						}
					}
					
					if (EditMesh)
					{
						EM_free_index_arrays();
					}
					break;
				}
				case SCE_SNAP_MODE_VERTEX:
				{
					MVert *verts = dm->getVertArray(dm);
					int *index_array = NULL;
					int index = 0;
					int i;
					
					if (EditMesh)
					{
						index_array = dm->getVertDataArray(dm, CD_ORIGINDEX);
						EM_init_index_arrays(1, 0, 0);
					}
					
					for( i = 0; i < totvert; i++) {
						EditVert *eve = NULL;
						MVert *v = verts + i;
						
						test = 1; /* reset for every vert */
					
						if (EditMesh)
						{
							if (index_array)
							{
								index = index_array[i];
							}
							else
							{
								index = i;
							}
							
							if (index == ORIGINDEX_NONE)
							{
								test = 0;
							}
							else
							{
								eve = EM_get_vert_for_index(index);
								
								if (eve && (eve->h || (eve->f & SELECT)))
								{
									test = 0;
								}
							}
						}
						
						
						if (test)
						{
							float dvec[3];
							
							VecSubf(dvec, v->co, ray_start_local);
							
							if (Inpf(ray_normal_local, dvec) > 0)
							{
								float location[3];
								float new_depth;
								int screen_loc[2];
								int new_dist;
								
								VECCOPY(location, v->co);
								
								Mat4MulVecfl(obmat, location);
								
								new_depth = VecLenf(location, ray_start);					
								
								project_int(t->ar, t->view, location, screen_loc);
								new_dist = abs(screen_loc[0] - mval[0]) + abs(screen_loc[1] - mval[1]);
								
								if (new_dist <= *dist && new_depth < *depth)
								{
									*depth = new_depth;
									retval = 1;
									
									VECCOPY(loc, location);
									
									NormalShortToFloat(no, v->no);
									Mat3MulVecfl(timat, no);
									Normalize(no);
					
									*dist = new_dist;
								} 
							}
						}
					}

					if (EditMesh)
					{
						EM_free_index_arrays();
					}
					break;
				}
				case SCE_SNAP_MODE_EDGE:
				{
					MVert *verts = dm->getVertArray(dm);
					MEdge *edges = dm->getEdgeArray(dm);
					int totedge = dm->getNumEdges(dm);
					int *index_array = NULL;
					int index = 0;
					int i;
					
					if (EditMesh)
					{
						index_array = dm->getEdgeDataArray(dm, CD_ORIGINDEX);
						EM_init_index_arrays(0, 1, 0);
					}
					
					for( i = 0; i < totedge; i++) {
						EditEdge *eed = NULL;
						MEdge *e = edges + i;
						
						test = 1; /* reset for every vert */
					
						if (EditMesh)
						{
							if (index_array)
							{
								index = index_array[i];
							}
							else
							{
								index = i;
							}
							
							if (index == ORIGINDEX_NONE)
							{
								test = 0;
							}
							else
							{
								eed = EM_get_edge_for_index(index);
								
								if (eed && (eed->h || (eed->v1->f & SELECT) || (eed->v2->f & SELECT)))
								{
									test = 0;
								}
							}
						}
						
						
						if (test)
						{
							float intersect[3] = {0, 0, 0}, ray_end[3], dvec[3];
							int result;
							
							VECCOPY(ray_end, ray_normal_local);
							VecMulf(ray_end, 2000);
							VecAddf(ray_end, ray_start_local, ray_end);
							
							result = LineIntersectLine(verts[e->v1].co, verts[e->v2].co, ray_start_local, ray_end, intersect, dvec); /* dvec used but we don't care about result */
							
							if (result)
							{
								float edge_loc[3], vec[3];
								float mul;
							
								/* check for behind ray_start */
								VecSubf(dvec, intersect, ray_start_local);
								
								VecSubf(edge_loc, verts[e->v1].co, verts[e->v2].co);
								VecSubf(vec, intersect, verts[e->v2].co);
								
								mul = Inpf(vec, edge_loc) / Inpf(edge_loc, edge_loc);
								
								if (mul > 1) {
									mul = 1;
									VECCOPY(intersect, verts[e->v1].co);
								}
								else if (mul < 0) {
									mul = 0;
									VECCOPY(intersect, verts[e->v2].co);
								}
	
								if (Inpf(ray_normal_local, dvec) > 0)
								{
									float location[3];
									float new_depth;
									int screen_loc[2];
									int new_dist;
									
									VECCOPY(location, intersect);
									
									Mat4MulVecfl(obmat, location);
									
									new_depth = VecLenf(location, ray_start);					
									
									project_int(t->ar, t->view, location, screen_loc);
									new_dist = abs(screen_loc[0] - mval[0]) + abs(screen_loc[1] - mval[1]);
									
									if (new_dist <= *dist && new_depth < *depth)
									{
										float n1[3], n2[3];
										
										*depth = new_depth;
										retval = 1;
										
										VecSubf(edge_loc, verts[e->v1].co, verts[e->v2].co);
										VecSubf(vec, intersect, verts[e->v2].co);
										
										mul = Inpf(vec, edge_loc) / Inpf(edge_loc, edge_loc);
										
										NormalShortToFloat(n1, verts[e->v1].no);						
										NormalShortToFloat(n2, verts[e->v2].no);
										VecLerpf(no, n2, n1, mul);
										Normalize(no);			
	
										VECCOPY(loc, location);
										
										Mat3MulVecfl(timat, no);
										Normalize(no);
										
										*dist = new_dist;
									} 
								}
							}
						}
					}

					if (EditMesh)
					{
						EM_free_index_arrays();
					}
					break;
				}
			}
		}
	}

	return retval;
} 

int snapObjects(TransInfo *t, int *dist, float *loc, float *no, int mode) {
	Scene *scene = t->scene;
	View3D *v3d = t->view;
	Base *base;
	float depth = FLT_MAX;
	int retval = 0;
	float ray_start[3], ray_normal[3];
	
	viewray(t->ar, v3d, t->mval, ray_start, ray_normal);

	if (mode == NOT_ACTIVE)
	{
		DerivedMesh *dm;
		Object *ob = t->obedit;
		EditMesh *em = ((Mesh *)t->obedit->data)->edit_mesh;
		
		dm = editmesh_get_derived_cage(em, CD_MASK_BAREMESH);
		
		retval = snapDerivedMesh(t, ob, dm, ob->obmat, ray_start, ray_normal, t->mval, loc, no, dist, &depth, 1);
		
		dm->release(dm);
	}
	
	for ( base = scene->base.first; base != NULL; base = base->next ) {
		if ( BASE_SELECTABLE(v3d, base) && (base->flag & (BA_HAS_RECALC_OB|BA_HAS_RECALC_DATA)) == 0 && ((mode == NOT_SELECTED && (base->flag & (SELECT|BA_WAS_SEL)) == 0) || (mode == NOT_ACTIVE && base != BASACT)) ) {
			Object *ob = base->object;
			
			if (ob->transflag & OB_DUPLI)
			{
				DupliObject *dupli_ob;
				ListBase *lb = object_duplilist(G.scene, ob);
				
				for(dupli_ob = lb->first; dupli_ob; dupli_ob = dupli_ob->next)
				{
					Object *ob = dupli_ob->ob;
					
					if (ob->type == OB_MESH) {
						DerivedMesh *dm = mesh_get_derived_final(ob, CD_MASK_BAREMESH);
						int val;
						
						val = snapDerivedMesh(t, ob, dm, dupli_ob->mat, ray_start, ray_normal, t->mval, loc, no, dist, &depth, 0);
	
						retval = retval || val;
	
						dm->release(dm);
					}
				}
				
				free_object_duplilist(lb);
			}
			
			if (ob->type == OB_MESH) {
				DerivedMesh *dm = mesh_get_derived_final(ob, CD_MASK_BAREMESH);
				int val;
				
				val = snapDerivedMesh(t, ob, dm, ob->obmat, ray_start, ray_normal, t->mval, loc, no, dist, &depth, 0);
				
				retval = retval || val;
				
				dm->release(dm);
			}
		}
	}
	
	return retval;
}

/*================================================================*/

static void applyGrid(TransInfo *t, float *val, int max_index, float fac[3], GearsType action);


void snapGridAction(TransInfo *t, float *val, GearsType action) {
	float fac[3];

	fac[NO_GEARS]    = t->snap[0];
	fac[BIG_GEARS]   = t->snap[1];
	fac[SMALL_GEARS] = t->snap[2];
	
	applyGrid(t, val, t->idx_max, fac, action);
}


void snapGrid(TransInfo *t, float *val) {
	int invert;
	GearsType action;

	// Only do something if using Snap to Grid
	if (t->tsnap.modePoint != SNAP_GRID)
		return;

	if(t->mode==TFM_ROTATION || t->mode==TFM_WARP || t->mode==TFM_TILT || t->mode==TFM_TRACKBALL || t->mode==TFM_BONE_ROLL)
		invert = U.flag & USER_AUTOROTGRID;
	else if(t->mode==TFM_RESIZE || t->mode==TFM_SHEAR || t->mode==TFM_BONESIZE || t->mode==TFM_SHRINKFATTEN || t->mode==TFM_CURVE_SHRINKFATTEN)
		invert = U.flag & USER_AUTOSIZEGRID;
	else
		invert = U.flag & USER_AUTOGRABGRID;

	if(invert) {
		action = (t->event->ctrl) ? NO_GEARS: BIG_GEARS;
	}
	else {
		action = (t->event->ctrl) ? BIG_GEARS : NO_GEARS;
	}

	if (action == BIG_GEARS && (t->event->shift)) {
		action = SMALL_GEARS;
	}

	snapGridAction(t, val, action);
}


static void applyGrid(TransInfo *t, float *val, int max_index, float fac[3], GearsType action)
{
	int i;
	float asp[3] = {1.0f, 1.0f, 1.0f}; // TODO: Remove hard coded limit here (3)

	// Early bailing out if no need to snap
	if (fac[action] == 0.0)
		return;
	
	/* evil hack - snapping needs to be adapted for image aspect ratio */
	if((t->spacetype==SPACE_IMAGE) && (t->mode==TFM_TRANSLATION)) {
		// TRANSFORM_FIX_ME
		//transform_aspect_ratio_tface_uv(asp, asp+1);
	}

	for (i=0; i<=max_index; i++) {
		val[i]= fac[action]*asp[i]*(float)floor(val[i]/(fac[action]*asp[i]) +.5);
	}
}
