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

#include "BKE_global.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"
#include "BKE_lattice.h"
#include "BKE_armature.h"
#include "BKE_curve.h"
#include "BKE_displist.h"

#include "BSE_view.h"
#include "BSE_edit.h"

#include "BLI_arithb.h"
#include "BLI_editVert.h"

#include "BDR_drawobject.h"

#include "blendef.h"

#include "mydevice.h"

#include "transform.h"
#include "transform_constraints.h"
#include "transform_generics.h"

extern ListBase editNurb;
extern ListBase editelems;

void recalcData();

/* ************************** CONSTRAINTS ************************* */
void getConstraintMatrix(TransInfo *t);

void postConstraintChecks(TransInfo *t, float vec[3]) {
	Mat3MulVecfl(t->con.imtx, vec);

	snapGrid(t, vec);

	if (t->num.flags & NULLONE) {
		if (!(t->con.mode & CON_AXIS0))
			vec[0] = 1.0f;

		if (!(t->con.mode & CON_AXIS1))
			vec[1] = 1.0f;

		if (!(t->con.mode & CON_AXIS2))
			vec[2] = 1.0f;
	}

	applyNumInput(&t->num, vec);

	Mat3MulVecfl(t->con.mtx, vec);
}

void getViewVector(TransInfo *t, float coord[3], float vec[3]) {
	if (G.vd->persp)
	{
		float p1[4], p2[4];

		VecAddf(p1, coord, t->con.center);
		p1[3] = 1.0f;
		VECCOPY(p2, p1);
		p2[3] = 1.0f;
		Mat4MulVec4fl(G.vd->viewmat, p2);

		p2[0] = 2.0f * p2[0];
		p2[1] = 2.0f * p2[1];
		p2[2] = 2.0f * p2[2];

		Mat4MulVec4fl(G.vd->viewinv, p2);

		VecSubf(vec, p2, p1);
		Normalise(vec);
	}
	else {
		VECCOPY(vec, G.vd->viewinv[2]);
	}
}

void axisProjection(TransInfo *t, float axis[3], float in[3], float out[3]) {
	float norm[3], n[3], vec[3], factor;

	getViewVector(t, in, norm);

	Normalise(axis);

	VECCOPY(n, axis);
	Mat4MulVecfl(G.vd->viewmat, n);
	n[2] = G.vd->viewmat[3][2];
	Mat4MulVecfl(G.vd->viewinv, n);

	if (Inpf(axis, norm) != 1.0f) {
		Projf(vec, in, n);
		factor = Normalise(vec);
		factor /= Inpf(axis, vec);

		VecMulf(axis, factor);
		VECCOPY(out, axis);
	}
	else {
		out[0] = out[1] = out[2] = 0.0f;
	}
}

void planeProjection(TransInfo *t, float in[3], float out[3]) {
	float vec[3], factor, angle, norm[3];

	getViewVector(t, in, norm);

	VecSubf(vec, out, in);
	factor = Normalise(vec);
	angle = Inpf(vec, norm);

	if (angle * angle >= 0.000001f) {
		factor /= angle;

		VECCOPY(vec, norm);
		VecMulf(vec, factor);

		VecAddf(out, in, vec);
	}
}

/*
 * Generic callback for constant spacial constraints applied to linear motion
 * 
 * The IN vector in projected into the constrained space and then further
 * projected along the view vector.
 * (in perspective mode, the view vector is relative to the position on screen)
 *
 */

void applyAxisConstraintVec(TransInfo *t, TransData *td, float in[3], float out[3])
{
	VECCOPY(out, in);
	if (!td && t->con.mode & CON_APPLY) {
		Mat3MulVecfl(t->con.pmtx, out);
		if (out[0] != 0.0f || out[1] != 0.0f || out[2] != 0.0f) {
			if (getConstraintSpaceDimension(t) == 2) {
				planeProjection(t, in, out);
			}
			else if (getConstraintSpaceDimension(t) == 1) {
				float c[3];

				if (t->con.mode & CON_AXIS0) {
					VECCOPY(c, t->con.mtx[0]);
				}
				else if (t->con.mode & CON_AXIS1) {
					VECCOPY(c, t->con.mtx[1]);
				}
				else if (t->con.mode & CON_AXIS2) {
					VECCOPY(c, t->con.mtx[2]);
				}
				axisProjection(t, c, in, out);
			}
		}

		postConstraintChecks(t, out);
	}
}

/*
 * Generic callback for constant spacial constraints applied to resize motion
 * 
 *
 */

void applyAxisConstraintSize(TransInfo *t, TransData *td, float smat[3][3])
{
	if (!td && t->con.mode & CON_APPLY) {
		float tmat[3][3];

		if (!(t->con.mode & CON_AXIS0)) {
			smat[0][0] = 1.0f;
		}
		if (!(t->con.mode & CON_AXIS1)) {
			smat[1][1] = 1.0f;
		}
		if (!(t->con.mode & CON_AXIS2)) {
			smat[2][2] = 1.0f;
		}

		Mat3MulMat3(tmat, smat, t->con.imtx);
		Mat3MulMat3(smat, t->con.mtx, tmat);
	}
}

/*
 * Generic callback for constant spacial constraints applied to rotations
 * 
 * The rotation axis is copied into VEC.
 *
 * In the case of single axis constraints, the rotation axis is directly the one constrained to.
 * For planar constraints (2 axis), the rotation axis is the normal of the plane.
 *
 * The vector is then modified to always point away from the screen (in global space)
 * This insures that the rotation is always logically following the mouse.
 * (ie: not doing counterclockwise rotations when the mouse moves clockwise).
 */

void applyAxisConstraintRot(TransInfo *t, TransData *td, float vec[3])
{
	if (!td && t->con.mode & CON_APPLY) {
		int mode = t->con.mode & (CON_AXIS0|CON_AXIS1|CON_AXIS2);

		switch(mode) {
		case CON_AXIS0:
		case (CON_AXIS1|CON_AXIS2):
			VECCOPY(vec, t->con.mtx[0]);
			break;
		case CON_AXIS1:
		case (CON_AXIS0|CON_AXIS2):
			VECCOPY(vec, t->con.mtx[1]);
			break;
		case CON_AXIS2:
		case (CON_AXIS0|CON_AXIS1):
			VECCOPY(vec, t->con.mtx[2]);
			break;
		}
		if (Inpf(vec, G.vd->viewinv[2]) > 0.0f) {
			VecMulf(vec, -1.0f);
		}
	}
}

/*
 * Returns the dimension of the constraint space.
 * 
 * For that reason, the flags always needs to be set to properly evaluate here,
 * even if they aren't actually used in the callback function. (Which could happen
 * for weird constraints not yet designed. Along a path for example.)
 */

int getConstraintSpaceDimension(TransInfo *t)
{
	int n = 0;

	if (t->con.mode & CON_AXIS0)
		n++;

	if (t->con.mode & CON_AXIS1)
		n++;

	if (t->con.mode & CON_AXIS2)
		n++;

	return n;
/*
  Someone willing to do it criptically could do the following instead:

  return t->con & (CON_AXIS0|CON_AXIS1|CON_AXIS2);
	
  Based on the assumptions that the axis flags are one after the other and start at 1
*/
}

void BIF_setSingleAxisConstraint(float vec[3]) {
	TransInfo *t = BIF_GetTransInfo();
	float space[3][3], v[3];
	VECCOPY(space[0], vec);

	v[0] = vec[2];
	v[1] = vec[0];
	v[2] = vec[1];

	Crossf(space[1], vec, v);
	Crossf(space[2], vec, space[1]);

	Mat3CpyMat3(t->con.mtx, space);
	t->con.mode = (CON_AXIS0|CON_APPLY);
	getConstraintMatrix(t);

	VECCOPY(t->con.center, t->center);
	if (G.obedit) {
		Mat4MulVecfl(G.obedit->obmat, t->con.center);
	}

	t->con.applyVec = applyAxisConstraintVec;
	t->con.applySize = applyAxisConstraintSize;
	t->con.applyRot = applyAxisConstraintRot;
	t->redraw = 1;
}

void setConstraint(TransInfo *t, float space[3][3], int mode) {
	Mat3CpyMat3(t->con.mtx, space);
	t->con.mode = mode;
	getConstraintMatrix(t);

	VECCOPY(t->con.center, t->center);
	if (G.obedit) {
		Mat4MulVecfl(G.obedit->obmat, t->con.center);
	}

	t->con.applyVec = applyAxisConstraintVec;
	t->con.applySize = applyAxisConstraintSize;
	t->con.applyRot = applyAxisConstraintRot;
	t->redraw = 1;
}

void BIF_drawConstraint()
{
	int i = -1;
	TransInfo *t = BIF_GetTransInfo();
	TransCon *tc = &(t->con);

	if (tc->mode == 0)
		return;

	if (tc->mode & CON_SELECT) {
			drawLine(tc->center, tc->mtx[0], 'x');
			drawLine(tc->center, tc->mtx[1], 'y');
			drawLine(tc->center, tc->mtx[2], 'z');
	}

	if (tc->mode & CON_AXIS0) {
		drawLine(tc->center, tc->mtx[0], 255 - 'x');
	}
	if (tc->mode & CON_AXIS1) {
		drawLine(tc->center, tc->mtx[1], 255 - 'y');
	}
	if (tc->mode & CON_AXIS2) {
		drawLine(tc->center, tc->mtx[2], 255 - 'z');
	}
}

/* called from drawview.c, as an extra per-window draw option */
void BIF_drawPropCircle()
{
	TransInfo *t = BIF_GetTransInfo();

	if (G.f & G_PROPORTIONAL) {
		float tmat[4][4], imat[4][4];

		BIF_ThemeColor(TH_GRID);
		
		/* if editmode we need to go into object space */
		if(G.obedit) mymultmatrix(G.obedit->obmat);
		
		mygetmatrix(tmat);
		Mat4Invert(imat, tmat);
		
 		drawcircball(t->center, t->propsize, imat);
		
		/* if editmode we restore */
		if(G.obedit) myloadmatrix(G.vd->viewmat);
	}
}

void startConstraint(TransInfo *t) {
	t->con.mode |= CON_APPLY;
	t->num.idx_max = min(getConstraintSpaceDimension(t) - 1, t->idx_max);
}

void stopConstraint(TransInfo *t) {
	t->con.mode &= ~CON_APPLY;
	t->num.idx_max = t->idx_max;
}

void getConstraintMatrix(TransInfo *t)
{
	Mat3Inv(t->con.pmtx, t->con.mtx);
	Mat3CpyMat3(t->con.imtx, t->con.pmtx);

	if (!(t->con.mode & CON_AXIS0)) {
		t->con.pmtx[0][0]		=
			t->con.pmtx[0][1]	=
			t->con.pmtx[0][2]	= 0.0f;
	}

	if (!(t->con.mode & CON_AXIS1)) {
		t->con.pmtx[1][0]		=
			t->con.pmtx[1][1]	=
			t->con.pmtx[1][2]	= 0.0f;
	}

	if (!(t->con.mode & CON_AXIS2)) {
		t->con.pmtx[2][0]		=
			t->con.pmtx[2][1]	=
			t->con.pmtx[2][2]	= 0.0f;
	}
}

void initSelectConstraint(TransInfo *t)
{
	Mat3One(t->con.mtx);
	Mat3One(t->con.pmtx);
	t->con.mode |= CON_APPLY;
	t->con.mode |= CON_SELECT;
	VECCOPY(t->con.center, t->center);
	if (G.obedit) {
		Mat4MulVecfl(G.obedit->obmat, t->con.center);
	}
	setNearestAxis(t);
	t->con.applyVec = applyAxisConstraintVec;
	t->con.applySize = applyAxisConstraintSize;
	t->con.applyRot = applyAxisConstraintRot;
}

void selectConstraint(TransInfo *t) {
	if (t->con.mode & CON_SELECT) {
		setNearestAxis(t);
	}
}

void postSelectConstraint(TransInfo *t)
{
	t->con.mode &= ~CON_AXIS0;
	t->con.mode &= ~CON_AXIS1;
	t->con.mode &= ~CON_AXIS2;
	t->con.mode &= ~CON_SELECT;

	setNearestAxis(t);

	t->con.mode |= CON_APPLY;
	VECCOPY(t->con.center, t->center);

	getConstraintMatrix(t);
	startConstraint(t);
	t->redraw = 1;
}

void setNearestAxis(TransInfo *t)
{
	short coord[2];
	float mvec[3], axis[3], center[3], proj[3];
	float len[3];
	int i;

	t->con.mode &= ~CON_AXIS0;
	t->con.mode &= ~CON_AXIS1;
	t->con.mode &= ~CON_AXIS2;

	VECCOPY(center, t->center);
	if (G.obedit) {
		Mat4MulVecfl(G.obedit->obmat, center);
	}

	getmouseco_areawin(coord);
	mvec[0] = (float)(coord[0] - t->center2d[0]);
	mvec[1] = (float)(coord[1] - t->center2d[1]);
	mvec[2] = 0.0f;

	for (i = 0; i<3; i++) {
		VECCOPY(axis, t->con.mtx[i]);
		VecAddf(axis, axis, center);
		project_short_noclip(axis, coord);
		axis[0] = (float)(coord[0] - t->center2d[0]);
		axis[1] = (float)(coord[1] - t->center2d[1]);
		axis[2] = 0.0f;

		if (Normalise(axis) != 0.0f) {
			Projf(proj, mvec, axis);
			VecSubf(axis, mvec, proj);
			len[i] = Normalise(axis);
		}
		else {
			len[i] = 10000000000.0f;
		}
	}

	if (len[0] < len[1] && len[0] < len[2]) {
		if (G.qual == LR_CTRLKEY) {
			t->con.mode |= (CON_AXIS1|CON_AXIS2);
		}
		else {
			t->con.mode |= CON_AXIS0;
		}
	}
	else if (len[1] < len[0] && len[1] < len[2]) {
		if (G.qual == LR_CTRLKEY) {
			t->con.mode |= (CON_AXIS0|CON_AXIS2);
		}
		else {
			t->con.mode |= CON_AXIS1;
		}
	}
	else if (len[2] < len[1] && len[2] < len[0]) {
		if (G.qual == LR_CTRLKEY) {
			t->con.mode |= (CON_AXIS0|CON_AXIS1);
		}
		else {
			t->con.mode |= CON_AXIS2;
		}
	}
	getConstraintMatrix(t);
}
