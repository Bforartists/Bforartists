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
 * The Original Code is Copyright (C) 2005 by the Blender Foundation.
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#include "BMF_Api.h"

#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "DNA_constraint_types.h"
#include "DNA_ID.h"
#include "DNA_nla_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_view3d_types.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "BKE_action.h"
#include "BKE_armature.h"
#include "BKE_constraint.h"
#include "BKE_depsgraph.h"
#include "BKE_DerivedMesh.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_object.h"
#include "BKE_ipo.h"
#include "BKE_utildefines.h"

#include "BIF_editaction.h"
#include "BIF_editarmature.h"
#include "BIF_gl.h"
#include "BIF_glutil.h"
#include "BIF_graphics.h"
#include "BIF_interface.h"
#include "BIF_poseobject.h"
#include "BIF_mywindow.h"
#include "BIF_resources.h"
#include "BIF_screen.h"

#include "BDR_editobject.h"
#include "BDR_drawobject.h"
#include "BDR_drawaction.h"

#include "BSE_edit.h"
#include "BSE_view.h"

#include "mydevice.h"
#include "blendef.h"
#include "nla.h"

/* half the cube, in Y */
static float cube[8][3] = {
{-1.0,  0.0, -1.0},
{-1.0,  0.0,  1.0},
{-1.0,  1.0,  1.0},
{-1.0,  1.0, -1.0},
{ 1.0,  0.0, -1.0},
{ 1.0,  0.0,  1.0},
{ 1.0,  1.0,  1.0},
{ 1.0,  1.0, -1.0},
};


/* *************** Armature drawing, helper calls for parts ******************* */

static void drawsolidcube_size(float xsize, float ysize, float zsize)
{
	static GLuint displist=0;
	float n[3];
	
	glScalef(xsize, ysize, zsize);
	
	n[0]=0; n[1]=0; n[2]=0;

	if(displist==0) {
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE_AND_EXECUTE);

		glBegin(GL_QUADS);
		n[0]= -1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[0]); glVertex3fv(cube[1]); glVertex3fv(cube[2]); glVertex3fv(cube[3]);
		n[0]=0;
		n[1]= -1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[0]); glVertex3fv(cube[4]); glVertex3fv(cube[5]); glVertex3fv(cube[1]);
		n[1]=0;
		n[0]= 1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[4]); glVertex3fv(cube[7]); glVertex3fv(cube[6]); glVertex3fv(cube[5]);
		n[0]=0;
		n[1]= 1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[7]); glVertex3fv(cube[3]); glVertex3fv(cube[2]); glVertex3fv(cube[6]);
		n[1]=0;
		n[2]= 1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[1]); glVertex3fv(cube[5]); glVertex3fv(cube[6]); glVertex3fv(cube[2]);
		n[2]=0;
		n[2]= -1.0;
		glNormal3fv(n); 
		glVertex3fv(cube[7]); glVertex3fv(cube[4]); glVertex3fv(cube[0]); glVertex3fv(cube[3]);
		glEnd();

		glEndList();
	}
	else glCallList(displist);
	
}

static void drawcube_size(float xsize, float ysize, float zsize)
{
	static GLuint displist=0;
	
	glScalef(xsize, ysize, zsize);
	
	if(displist==0) {
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE_AND_EXECUTE);

		glBegin(GL_LINE_STRIP);
		glVertex3fv(cube[0]); glVertex3fv(cube[1]);glVertex3fv(cube[2]); glVertex3fv(cube[3]);
		glVertex3fv(cube[0]); glVertex3fv(cube[4]);glVertex3fv(cube[5]); glVertex3fv(cube[6]);
		glVertex3fv(cube[7]); glVertex3fv(cube[4]);
		glEnd();
		
		glBegin(GL_LINES);
		glVertex3fv(cube[1]); glVertex3fv(cube[5]);
		glVertex3fv(cube[2]); glVertex3fv(cube[6]);
		glVertex3fv(cube[3]); glVertex3fv(cube[7]);
		glEnd();

		glEndList();
	}
	else glCallList(displist);
	
}


static void draw_bonevert(void)
{
	static GLuint displist=0;
	
	if(displist==0) {
		GLUquadricObj	*qobj;
		
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE_AND_EXECUTE);
				
		glPushMatrix();
		
		qobj	= gluNewQuadric(); 
		gluQuadricDrawStyle(qobj, GLU_SILHOUETTE); 
		gluDisk( qobj, 0.0,  0.05, 16, 1);
		
		glRotatef (90, 0, 1, 0);
		gluDisk( qobj, 0.0,  0.05, 16, 1);
		
		glRotatef (90, 1, 0, 0);
		gluDisk( qobj, 0.0,  0.05, 16, 1);
		
		gluDeleteQuadric(qobj);  
		
		glPopMatrix();
		glEndList();
	}
	else glCallList(displist);
}

static void draw_bonevert_solid(void)
{
	static GLuint displist=0;
	
	if(displist==0) {
		GLUquadricObj	*qobj;
		
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE_AND_EXECUTE);
		
		qobj	= gluNewQuadric();
		gluQuadricDrawStyle(qobj, GLU_FILL); 
		glShadeModel(GL_SMOOTH);
		gluSphere( qobj, 0.05, 8, 5);
		glShadeModel(GL_FLAT);
		gluDeleteQuadric(qobj);  
		
		glEndList();
	}
	else glCallList(displist);
}

static void draw_bone_octahedral()
{
	static GLuint displist=0;
	
	if(displist==0) {
		float vec[6][3];	
		
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE_AND_EXECUTE);

		vec[0][0]= vec[0][1]= vec[0][2]= 0.0;
		vec[5][0]= vec[5][2]= 0.0; vec[5][1]= 1.0;
		
		vec[1][0]= 0.1; vec[1][2]= 0.1; vec[1][1]= 0.1;
		vec[2][0]= 0.1; vec[2][2]= -0.1; vec[2][1]= 0.1;
		vec[3][0]= -0.1; vec[3][2]= -0.1; vec[3][1]= 0.1;
		vec[4][0]= -0.1; vec[4][2]= 0.1; vec[4][1]= 0.1;
		
		/*	Section 1, sides */
		glBegin(GL_LINE_LOOP);
		glVertex3fv(vec[0]);
		glVertex3fv(vec[1]);
		glVertex3fv(vec[5]);
		glVertex3fv(vec[3]);
		glVertex3fv(vec[0]);
		glVertex3fv(vec[4]);
		glVertex3fv(vec[5]);
		glVertex3fv(vec[2]);
		glEnd();
		
		/*	Section 1, square */
		glBegin(GL_LINE_LOOP);
		glVertex3fv(vec[1]);
		glVertex3fv(vec[2]);
		glVertex3fv(vec[3]);
		glVertex3fv(vec[4]);
		glEnd();
		
		glEndList();
	}
	else glCallList(displist);
}	

static void draw_bone_solid_octahedral(void)
{
	static GLuint displist=0;
	
	if(displist==0) {
		float vec[6][3], nor[3];	
		
		displist= glGenLists(1);
		glNewList(displist, GL_COMPILE_AND_EXECUTE);
		
		vec[0][0]= vec[0][1]= vec[0][2]= 0.0;
		vec[5][0]= vec[5][2]= 0.0; vec[5][1]= 1.0;
		
		vec[1][0]= 0.1; vec[1][2]= 0.1; vec[1][1]= 0.1;
		vec[2][0]= 0.1; vec[2][2]= -0.1; vec[2][1]= 0.1;
		vec[3][0]= -0.1; vec[3][2]= -0.1; vec[3][1]= 0.1;
		vec[4][0]= -0.1; vec[4][2]= 0.1; vec[4][1]= 0.1;
		
		
		glBegin(GL_TRIANGLES);
		/* bottom */
		CalcNormFloat(vec[2], vec[1], vec[0], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[2]);glVertex3fv(vec[1]);glVertex3fv(vec[0]);
		
		CalcNormFloat(vec[3], vec[2], vec[0], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[3]);glVertex3fv(vec[2]);glVertex3fv(vec[0]);
		
		CalcNormFloat(vec[4], vec[3], vec[0], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[4]);glVertex3fv(vec[3]);glVertex3fv(vec[0]);

		CalcNormFloat(vec[1], vec[4], vec[0], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[1]);glVertex3fv(vec[4]);glVertex3fv(vec[0]);

		/* top */
		CalcNormFloat(vec[5], vec[1], vec[2], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[5]);glVertex3fv(vec[1]);glVertex3fv(vec[2]);
		
		CalcNormFloat(vec[5], vec[2], vec[3], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[5]);glVertex3fv(vec[2]);glVertex3fv(vec[3]);
		
		CalcNormFloat(vec[5], vec[3], vec[4], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[5]);glVertex3fv(vec[3]);glVertex3fv(vec[4]);
		
		CalcNormFloat(vec[5], vec[4], vec[1], nor);
		glNormal3fv(nor);
		glVertex3fv(vec[5]);glVertex3fv(vec[4]);glVertex3fv(vec[1]);
		
		glEnd();
		
		glEndList();
	}
	else glCallList(displist);
}	

/* *************** Armature drawing, bones ******************* */


static void draw_bone_points(int dt, int armflag, unsigned int boneflag, int id)
{
	/*	Draw root point if we are not connected */
	if (!(boneflag & BONE_CONNECTED)){
		if (id != -1)
			glLoadName (id | BONESEL_ROOT);
		
		if(dt<=OB_WIRE) {
			if(armflag & ARM_EDITMODE) {
				if (boneflag & BONE_ROOTSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
				else BIF_ThemeColor(TH_VERTEX);
			}
		}
		else 
			BIF_ThemeColor(TH_BONE_SOLID);
		
		if(dt>OB_WIRE) draw_bonevert_solid();
		else draw_bonevert();
	}
	
	/*	Draw tip point */
	if (id != -1)
		glLoadName (id | BONESEL_TIP);
	
	if(dt<=OB_WIRE) {
		if(armflag & ARM_EDITMODE) {
			if (boneflag & BONE_TIPSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
			else BIF_ThemeColor(TH_VERTEX);
		}
	}
	else {
		BIF_ThemeColor(TH_BONE_SOLID);
	}
	
	glTranslatef(0.0, 1.0, 0.0);
	if(dt>OB_WIRE) draw_bonevert_solid();
	else draw_bonevert();
	glTranslatef(0.0, -1.0, 0.0);
	
}

/* 16 values of sin function (still same result!) */
static float si[16] = {
	0.00000000,
	0.20129852, 0.39435585,
	0.57126821, 0.72479278,
	0.84864425, 0.93775213,
	0.98846832, 0.99871650,
	0.96807711, 0.89780453,
	0.79077573, 0.65137248,
	0.48530196, 0.29936312,
	0.10116832
};
/* 16 values of cos function (still same result!) */
static float co[16] ={
	1.00000000,
	0.97952994, 0.91895781,
	0.82076344, 0.68896691,
	0.52896401, 0.34730525,
	0.15142777, -0.05064916,
	-0.25065253, -0.44039415,
	-0.61210598, -0.75875812,
	-0.87434661, -0.95413925,
	-0.99486932
};



/* smat, imat = mat & imat to draw screenaligned */
static void draw_sphere_bone_dist(float smat[][4], float imat[][4], int boneflag, bPoseChannel *pchan, EditBone *ebone)
{
	float head, tail, length, dist;
	float *headvec, *tailvec, dirvec[3];
	
	/* figure out the sizes of spheres */
	if(ebone) {
		/* this routine doesn't call set_matrix_editbone() that calculates it */
		ebone->length = VecLenf(ebone->head, ebone->tail);
		
		length= ebone->length;
		tail= ebone->rad_tail;
		dist= ebone->dist;
		if (ebone->parent && (ebone->flag & BONE_CONNECTED))
			head= ebone->parent->rad_tail;
		else
			head= ebone->rad_head;
		headvec= ebone->head;
		tailvec= ebone->tail;
	}
	else {
		length= pchan->bone->length;
		tail= pchan->bone->rad_tail;
		dist= pchan->bone->dist;
		if (pchan->parent && (pchan->bone->flag & BONE_CONNECTED))
			head= pchan->parent->bone->rad_tail;
		else
			head= pchan->bone->rad_head;
		headvec= pchan->pose_head;
		tailvec= pchan->pose_tail;
	}
	
	/* ***** draw it ***** */
	
	/* move vector to viewspace */
	VecSubf(dirvec, tailvec, headvec);
	Mat4Mul3Vecfl(smat, dirvec);
	/* clear zcomp */
	dirvec[2]= 0.0;
	/* move vector back */
	Mat4Mul3Vecfl(imat, dirvec);
	
	if(0.0f != Normalize(dirvec)) {
		float norvec[3], vec1[3], vec2[3], vec[3];
		int a;
		
		//VecMulf(dirvec, head);
		Crossf(norvec, dirvec, imat[2]);
		
		glBegin(GL_QUAD_STRIP);

		for(a=0; a<16; a++) {
			vec[0]= - *(si+a) * dirvec[0] + *(co+a) * norvec[0];
			vec[1]= - *(si+a) * dirvec[1] + *(co+a) * norvec[1];
			vec[2]= - *(si+a) * dirvec[2] + *(co+a) * norvec[2];
			
			vec1[0]= headvec[0] + head*vec[0];
			vec1[1]= headvec[1] + head*vec[1];
			vec1[2]= headvec[2] + head*vec[2];
			vec2[0]= headvec[0] + (head+dist)*vec[0];
			vec2[1]= headvec[1] + (head+dist)*vec[1];
			vec2[2]= headvec[2] + (head+dist)*vec[2];
			
			glColor4ub(255, 255, 255, 50);
			glVertex3fv(vec1);
			//glColor4ub(255, 255, 255, 0);
			glVertex3fv(vec2);
		}
		
		for(a=15; a>=0; a--) {
			vec[0]= *(si+a) * dirvec[0] + *(co+a) * norvec[0];
			vec[1]= *(si+a) * dirvec[1] + *(co+a) * norvec[1];
			vec[2]= *(si+a) * dirvec[2] + *(co+a) * norvec[2];
			
			vec1[0]= tailvec[0] + tail*vec[0];
			vec1[1]= tailvec[1] + tail*vec[1];
			vec1[2]= tailvec[2] + tail*vec[2];
			vec2[0]= tailvec[0] + (tail+dist)*vec[0];
			vec2[1]= tailvec[1] + (tail+dist)*vec[1];
			vec2[2]= tailvec[2] + (tail+dist)*vec[2];
			
			//glColor4ub(255, 255, 255, 50);
			glVertex3fv(vec1);
			//glColor4ub(255, 255, 255, 0);
			glVertex3fv(vec2);
		}
		/* make it cyclic... */
		
		vec[0]= - *(si) * dirvec[0] + *(co) * norvec[0];
		vec[1]= - *(si) * dirvec[1] + *(co) * norvec[1];
		vec[2]= - *(si) * dirvec[2] + *(co) * norvec[2];
		
		vec1[0]= headvec[0] + head*vec[0];
		vec1[1]= headvec[1] + head*vec[1];
		vec1[2]= headvec[2] + head*vec[2];
		vec2[0]= headvec[0] + (head+dist)*vec[0];
		vec2[1]= headvec[1] + (head+dist)*vec[1];
		vec2[2]= headvec[2] + (head+dist)*vec[2];
		
		//glColor4ub(255, 255, 255, 50);
		glVertex3fv(vec1);
		//glColor4ub(255, 255, 255, 0);
		glVertex3fv(vec2);
		
		glEnd();
	}
}


/* smat, imat = mat & imat to draw screenaligned */
static void draw_sphere_bone_wire(float smat[][4], float imat[][4], int armflag, int boneflag, int constflag, unsigned int id, bPoseChannel *pchan, EditBone *ebone)
{
	float head, tail, length;
	float *headvec, *tailvec, dirvec[3];
	
	/* figure out the sizes of spheres */
	if(ebone) {
		/* this routine doesn't call set_matrix_editbone() that calculates it */
		ebone->length = VecLenf(ebone->head, ebone->tail);

		length= ebone->length;
		tail= ebone->rad_tail;
		if (ebone->parent && (boneflag & BONE_CONNECTED))
			head= ebone->parent->rad_tail;
		else
			head= ebone->rad_head;
		headvec= ebone->head;
		tailvec= ebone->tail;
	}
	else {
		length= pchan->bone->length;
		tail= pchan->bone->rad_tail;
		if (pchan->parent && (boneflag & BONE_CONNECTED))
			head= pchan->parent->bone->rad_tail;
		else
			head= pchan->bone->rad_head;
		headvec= pchan->pose_head;
		tailvec= pchan->pose_tail;
	}
	
	/* sphere root color */
	if(armflag & ARM_EDITMODE) {
		if (boneflag & BONE_ROOTSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
		else BIF_ThemeColor(TH_VERTEX);
	}
	else if(armflag & ARM_POSEMODE) {
		/* in black or selection color */
		if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
		else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
		else BIF_ThemeColor(TH_WIRE);
	}
	
	/*	Draw root point if we are not connected */
	if (!(boneflag & BONE_CONNECTED)){
		if (id != -1)
			glLoadName (id | BONESEL_ROOT);
		
		drawcircball(GL_LINE_LOOP, headvec, head, imat);
	}
	
	/*	Draw tip point */
	if(armflag & ARM_EDITMODE) {
		if (boneflag & BONE_TIPSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
		else BIF_ThemeColor(TH_VERTEX);
	}
	
	if (id != -1)
		glLoadName (id | BONESEL_TIP);
	
	drawcircball(GL_LINE_LOOP, tailvec, tail, imat);
	
	/* base */
	if(armflag & ARM_EDITMODE) {
		if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_SELECT);
		else BIF_ThemeColor(TH_WIRE);
	}
	
	VecSubf(dirvec, tailvec, headvec);
	
	/* move vector to viewspace */
	Mat4Mul3Vecfl(smat, dirvec);
	/* clear zcomp */
	dirvec[2]= 0.0;
	/* move vector back */
	Mat4Mul3Vecfl(imat, dirvec);
	
	if(0.0f != Normalize(dirvec)) {
		float norvech[3], norvect[3], vec[3];
		
		VECCOPY(vec, dirvec);
		
		VecMulf(dirvec, head);
		Crossf(norvech, dirvec, imat[2]);
		
		VecMulf(vec, tail);
		Crossf(norvect, vec, imat[2]);
		
		if (id != -1)
			glLoadName (id | BONESEL_BONE);

		glBegin(GL_LINES);
		vec[0]= headvec[0] + norvech[0];
		vec[1]= headvec[1] + norvech[1];
		vec[2]= headvec[2] + norvech[2];
		glVertex3fv(vec);
		vec[0]= tailvec[0] + norvect[0];
		vec[1]= tailvec[1] + norvect[1];
		vec[2]= tailvec[2] + norvect[2];
		glVertex3fv(vec);
		vec[0]= headvec[0] - norvech[0];
		vec[1]= headvec[1] - norvech[1];
		vec[2]= headvec[2] - norvech[2];
		glVertex3fv(vec);
		vec[0]= tailvec[0] - norvect[0];
		vec[1]= tailvec[1] - norvect[1];
		vec[2]= tailvec[2] - norvect[2];
		glVertex3fv(vec);
		
		glEnd();
	}
}

/* does wire only for outline selecting */
static void draw_sphere_bone(int dt, int armflag, int boneflag, int constflag, unsigned int id, bPoseChannel *pchan, EditBone *ebone)
{
	GLUquadricObj	*qobj;
	float head, tail, length;
	float fac1, fac2;
	
	glPushMatrix();
	qobj	= gluNewQuadric();

	/* figure out the sizes of spheres */
	if(ebone) {
		length= ebone->length;
		tail= ebone->rad_tail;
		if (ebone->parent && (boneflag & BONE_CONNECTED))
			head= ebone->parent->rad_tail;
		else
			head= ebone->rad_head;
	}
	else {
		length= pchan->bone->length;
		tail= pchan->bone->rad_tail;
		if (pchan->parent && (boneflag & BONE_CONNECTED))
			head= pchan->parent->bone->rad_tail;
		else
			head= pchan->bone->rad_head;
	}
	
	/* move to z-axis space */
	glRotatef (-90.0f, 1.0f, 0.0f, 0.0f);

	if(dt==OB_SOLID) {
		/* set up solid drawing */
		glEnable(GL_COLOR_MATERIAL);
		glEnable(GL_LIGHTING);
		
		gluQuadricDrawStyle(qobj, GLU_FILL); 
		glShadeModel(GL_SMOOTH);
	}
	else {
		gluQuadricDrawStyle(qobj, GLU_SILHOUETTE); 
	}
	
	/* sphere root color */
	if(armflag & ARM_EDITMODE) {
		if (boneflag & BONE_ROOTSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
		else BIF_ThemeColorShade(TH_BONE_SOLID, -30);
	}
	else if(armflag & ARM_POSEMODE) {
		if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 10);
		else if (boneflag & BONE_SELECTED) BIF_ThemeColorShade(TH_BONE_POSE, -30);
		else BIF_ThemeColorShade(TH_BONE_SOLID, -30);
		
	}
	else if(dt==OB_SOLID) 
		BIF_ThemeColorShade(TH_BONE_SOLID, -30);
	
	/*	Draw root point if we are not connected */
	if (!(boneflag & BONE_CONNECTED)){
		if (id != -1)
			glLoadName (id | BONESEL_ROOT);
		gluSphere( qobj, head, 16, 10);
	}
	
	/*	Draw tip point */
	if(armflag & ARM_EDITMODE) {
		if (boneflag & BONE_TIPSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
		else BIF_ThemeColorShade(TH_BONE_SOLID, -30);
	}

	if (id != -1)
		glLoadName (id | BONESEL_TIP);
	
	glTranslatef(0.0, 0.0, length);
	gluSphere( qobj, tail, 16, 10);
	glTranslatef(0.0, 0.0, -length);
	
	/* base */
	if(armflag & ARM_EDITMODE) {
		if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_SELECT);
		else BIF_ThemeColor(TH_BONE_SOLID);
	}
	else if(armflag & ARM_POSEMODE) {
		if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
		else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
		else BIF_ThemeColor(TH_BONE_SOLID);
		
	}
	else if(dt==OB_SOLID)
		BIF_ThemeColor(TH_BONE_SOLID);
	
	fac1= (length-head)/length;
	fac2= (length-tail)/length;
	
	if(length > head+tail) {
		if (id != -1)
			glLoadName (id | BONESEL_BONE);
		
		glEnable(GL_POLYGON_OFFSET_FILL);
		glPolygonOffset(-1.0, -1.0);
		
		glTranslatef(0.0f, 0.0f, head);
		gluCylinder(qobj, fac1*head + (1.0f-fac1)*tail, fac2*tail + (1.0f-fac2)*head, length-head-tail, 16, 1);
		glTranslatef(0.0f, 0.0f, -head);

		glDisable(GL_POLYGON_OFFSET_FILL);
		
		/* draw sphere on extrema */
		glTranslatef(0.0f, 0.0f, length-tail);
		gluSphere( qobj, fac2*tail + (1.0f-fac2)*head, 16, 10);
		glTranslatef(0.0f, 0.0f, -length+tail);

		glTranslatef(0.0f, 0.0f, head);
		gluSphere( qobj, fac1*head + (1.0f-fac1)*tail, 16, 10);
	}
	else {		
		/* 1 sphere in center */
		glTranslatef(0.0f, 0.0f, (head + length-tail)/2.0);
		gluSphere( qobj, fac1*head + (1.0f-fac1)*tail, 16, 10);
	}
	
	/* restore */
	if(dt==OB_SOLID) {
		glShadeModel(GL_FLAT);
		glDisable(GL_LIGHTING);
		glDisable(GL_COLOR_MATERIAL);
	}
	
	glPopMatrix();
	gluDeleteQuadric(qobj);  
}

static GLubyte bm_dot6[]= {0x0, 0x18, 0x3C, 0x7E, 0x7E, 0x3C, 0x18, 0x0}; 
static GLubyte bm_dot8[]= {0x3C, 0x7E, 0xFF, 0xFF, 0xFF, 0xFF, 0x7E, 0x3C}; 

static GLubyte bm_dot5[]= {0x0, 0x0, 0x10, 0x38, 0x7c, 0x38, 0x10, 0x0}; 
static GLubyte bm_dot7[]= {0x0, 0x38, 0x7C, 0xFE, 0xFE, 0xFE, 0x7C, 0x38}; 


static void draw_line_bone(int armflag, int boneflag, int constflag, unsigned int id, bPoseChannel *pchan, EditBone *ebone)
{
	float length;
	
	glPixelStorei(GL_UNPACK_ALIGNMENT, 1);
	
	if(pchan) 
		length= pchan->bone->length;
	else 
		length= ebone->length;
	
	glPushMatrix();
	glScalef(length, length, length);
	
	/* this chunk not in object mode */
	if(armflag & (ARM_EDITMODE|ARM_POSEMODE)) {
		glLineWidth(4.0);
		if(armflag & ARM_POSEMODE) {
			/* outline in black or selection color */
			if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
			else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
			else BIF_ThemeColor(TH_WIRE);
		}
		else if (armflag & ARM_EDITMODE) {
			BIF_ThemeColor(TH_WIRE);
		}
		
		/*	Draw root point if we are not connected */
		if (!(boneflag & BONE_CONNECTED)){
			if (G.f & G_PICKSEL) {	// no bitmap in selection mode, crashes 3d cards...
				glLoadName (id | BONESEL_ROOT);
				glBegin(GL_POINTS);
				glVertex3f(0.0f, 0.0f, 0.0f);
				glEnd();
			}
			else {
				glRasterPos3f(0.0f, 0.0f, 0.0f);
				glBitmap(8, 8, 4, 4, 0, 0, bm_dot8);
			}
		}
		
		if (id != -1)
			glLoadName ((GLuint) id|BONESEL_BONE);
		
		glBegin(GL_LINES);
		glVertex3f(0.0f, 0.0f, 0.0f);
		glVertex3f(0.0f, 1.0f, 0.0f);
		glEnd();
		
		/* tip */
		if (G.f & G_PICKSEL) {	// no bitmap in selection mode, crashes 3d cards...
			glLoadName (id | BONESEL_TIP);
			glBegin(GL_POINTS);
			glVertex3f(0.0f, 1.0f, 0.0f);
			glEnd();
		}
		else {
			glRasterPos3f(0.0f, 1.0f, 0.0f);
			glBitmap(8, 8, 4, 4, 0, 0, bm_dot7);
		}
		
		/* further we send no names */
		if (id != -1)
			glLoadName (id & 0xFFFF);	// object tag, for bordersel optim
		
		if(armflag & ARM_POSEMODE) {
			/* inner part in background color or constraint */
			if(constflag) {
				if(constflag & PCHAN_HAS_STRIDE) glColor3ub(0, 0, 200);
				else if(constflag & PCHAN_HAS_TARGET) glColor3ub(255, 150, 0);
				else if(constflag & PCHAN_HAS_IK) glColor3ub(255, 255, 0);
				else if(constflag & PCHAN_HAS_CONST) glColor3ub(0, 255, 120);
				else BIF_ThemeColor(TH_BONE_POSE);	// PCHAN_HAS_ACTION 
			}
			else BIF_ThemeColorShade(TH_BACK, -30);
		}
	}
	
	glLineWidth(2.0);
	
	/*	Draw root point if we are not connected */
	if (!(boneflag & BONE_CONNECTED)){
		if ((G.f & G_PICKSEL)==0) {	// no bitmap in selection mode, crashes 3d cards...
			if(armflag & ARM_EDITMODE) {
				if (boneflag & BONE_ROOTSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
				else BIF_ThemeColor(TH_VERTEX);
			}
			glRasterPos3f(0.0f, 0.0f, 0.0f);
			glBitmap(8, 8, 4, 4, 0, 0, bm_dot6);
		}
	}
	
   if(armflag & ARM_EDITMODE) {
	   if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_EDGE_SELECT);
	   else BIF_ThemeColorShade(TH_BACK, -30);
   }
	glBegin(GL_LINES);
	glVertex3f(0.0f, 0.0f, 0.0f);
	glVertex3f(0.0f, 1.0f, 0.0f);
	glEnd();
	
	/* tip */
	if ((G.f & G_PICKSEL)==0) {	// no bitmap in selection mode, crashes 3d cards...
		if(armflag & ARM_EDITMODE) {
			if (boneflag & BONE_TIPSEL) BIF_ThemeColor(TH_VERTEX_SELECT);
			else BIF_ThemeColor(TH_VERTEX);
		}
		glRasterPos3f(0.0f, 1.0f, 0.0f);
		glBitmap(8, 8, 4, 4, 0, 0, bm_dot5);
	}
	
	glLineWidth(1.0);
	
	glPopMatrix();
}

static void draw_b_bone_boxes(int dt, bPoseChannel *pchan, float xwidth, float length, float zwidth)
{
	int segments= 0;
	
	if(pchan) segments= pchan->bone->segments;
	
	if(segments>1 && pchan) {
		float dlen= length/(float)segments;
		Mat4 *bbone= b_bone_spline_setup(pchan, 0);
		int a;
		
		for(a=0; a<segments; a++, bbone++) {
			glPushMatrix();
			glMultMatrixf(bbone->mat);
			if(dt==OB_SOLID) drawsolidcube_size(xwidth, dlen, zwidth);
			else drawcube_size(xwidth, dlen, zwidth);
			glPopMatrix();
		}
	}
	else {
		glPushMatrix();
		if(dt==OB_SOLID) drawsolidcube_size(xwidth, length, zwidth);
		else drawcube_size(xwidth, length, zwidth);
		glPopMatrix();
	}
}

static void draw_b_bone(int dt, int armflag, int boneflag, int constflag, unsigned int id, bPoseChannel *pchan, EditBone *ebone)
{
	float xwidth, length, zwidth;
	
	if(pchan) {
		xwidth= pchan->bone->xwidth;
		length= pchan->bone->length;
		zwidth= pchan->bone->zwidth;
	}
	else {
		xwidth= ebone->xwidth;
		length= ebone->length;
		zwidth= ebone->zwidth;
	}
	
	/* draw points only if... */
	if(armflag & ARM_EDITMODE) {
		/* move to unitspace */
		glPushMatrix();
		glScalef(length, length, length);
		draw_bone_points(dt, armflag, boneflag, id);
		glPopMatrix();
		length*= 0.95f;	// make vertices visible
	}

	/* colors for modes */
	if (armflag & ARM_POSEMODE) {
		if(dt==OB_WIRE) {
			if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
			else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
			else BIF_ThemeColor(TH_WIRE);
		}
		else 
			BIF_ThemeColor(TH_BONE_SOLID);
	}
	else if (armflag & ARM_EDITMODE) {
		if(dt==OB_WIRE) {
			if (boneflag & BONE_ACTIVE) BIF_ThemeColor(TH_EDGE_SELECT);
			else if (boneflag & BONE_SELECTED) BIF_ThemeColorShade(TH_EDGE_SELECT, -20);
			else BIF_ThemeColor(TH_WIRE);
		}
		else 
			BIF_ThemeColor(TH_BONE_SOLID);
	}
	
	if (id != -1) {
		glLoadName ((GLuint) id|BONESEL_BONE);
	}
	
	/* set up solid drawing */
	if(dt > OB_WIRE) {
		glEnable(GL_COLOR_MATERIAL);
		glEnable(GL_LIGHTING);
		BIF_ThemeColor(TH_BONE_SOLID);
		
		draw_b_bone_boxes(OB_SOLID, pchan, xwidth, length, zwidth);
		
		/* disable solid drawing */
		glDisable(GL_COLOR_MATERIAL);
		glDisable(GL_LIGHTING);
	}
	else {	// wire
		if (armflag & ARM_POSEMODE){
			if(constflag) {
				glEnable(GL_BLEND);
				
				if(constflag & PCHAN_HAS_STRIDE) glColor4ub(0, 0, 200, 80);
				else if(constflag & PCHAN_HAS_TARGET) glColor4ub(255, 150, 0, 80);
				else if(constflag & PCHAN_HAS_IK) glColor4ub(255, 255, 0, 80);
				else if(constflag & PCHAN_HAS_CONST) glColor4ub(0, 255, 120, 80);
				else BIF_ThemeColor4(TH_BONE_POSE);	// PCHAN_HAS_ACTION 
				
				draw_b_bone_boxes(OB_SOLID, pchan, xwidth, length, zwidth);
				
				glDisable(GL_BLEND);
				
				/* restore colors */
				if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
				else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
				else BIF_ThemeColor(TH_WIRE);
			}
		}		
		
		draw_b_bone_boxes(OB_WIRE, pchan, xwidth, length, zwidth);		
	}
}

static void draw_bone(int dt, int armflag, int boneflag, int constflag, unsigned int id, float length)
{
	
	/*	Draw a 3d octahedral bone, we use normalized space based on length,
	    for glDisplayLists */
	
	glScalef(length, length, length);

	/* set up solid drawing */
	if(dt > OB_WIRE) {
		glEnable(GL_COLOR_MATERIAL);
		glEnable(GL_LIGHTING);
		BIF_ThemeColor(TH_BONE_SOLID);
	}
	
	/* colors for posemode */
	if (armflag & ARM_POSEMODE) {
		if(dt==OB_WIRE) {
			if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
			else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
			else BIF_ThemeColor(TH_WIRE);
		}
		else 
			BIF_ThemeColor(TH_BONE_SOLID);
	}
	
	
	draw_bone_points(dt, armflag, boneflag, id);
	
	/* now draw the bone itself */
	
	if (id != -1) {
		glLoadName ((GLuint) id|BONESEL_BONE);
	}
	
	/* wire? */
	if(dt <= OB_WIRE) {
		/* colors */
		if (armflag & ARM_EDITMODE) {
			if (boneflag & BONE_ACTIVE) BIF_ThemeColor(TH_EDGE_SELECT);
			else if (boneflag & BONE_SELECTED) BIF_ThemeColorShade(TH_EDGE_SELECT, -20);
			else BIF_ThemeColor(TH_WIRE);
		}
		else if (armflag & ARM_POSEMODE){
			if(constflag) {
				glEnable(GL_BLEND);
				
				if(constflag & PCHAN_HAS_STRIDE) glColor4ub(0, 0, 200, 80);
				else if(constflag & PCHAN_HAS_TARGET) glColor4ub(255, 150, 0, 80);
				else if(constflag & PCHAN_HAS_IK) glColor4ub(255, 255, 0, 80);
				else if(constflag & PCHAN_HAS_CONST) glColor4ub(0, 255, 120, 80);
				else BIF_ThemeColor4(TH_BONE_POSE);	// PCHAN_HAS_ACTION 
					
				draw_bone_solid_octahedral();
				glDisable(GL_BLEND);

				/* restore colors */
				if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
				else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
				else BIF_ThemeColor(TH_WIRE);
			}
		}		
		draw_bone_octahedral();
	}
	else {	/* solid */

		BIF_ThemeColor(TH_BONE_SOLID);
		draw_bone_solid_octahedral();
	}

	/* disable solid drawing */
	if(dt>OB_WIRE) {
		glDisable(GL_COLOR_MATERIAL);
		glDisable(GL_LIGHTING);
	}
}

static void draw_custom_bone(Object *ob, int dt, int armflag, int boneflag, unsigned int id, float length)
{
	
	if(ob==NULL) return;
	
	glScalef(length, length, length);
	
	/* colors for posemode */
	if (armflag & ARM_POSEMODE) {
		if (boneflag & BONE_ACTIVE) BIF_ThemeColorShade(TH_BONE_POSE, 40);
		else if (boneflag & BONE_SELECTED) BIF_ThemeColor(TH_BONE_POSE);
		else BIF_ThemeColor(TH_WIRE);
	}
	
	if (id != -1) {
		glLoadName ((GLuint) id|BONESEL_BONE);
	}
	
	draw_object_instance(ob, dt, armflag & ARM_POSEMODE);
}


static void pchan_draw_IK_root_lines(bPoseChannel *pchan)
{
	bConstraint *con;
	bPoseChannel *parchan;
	
	for(con= pchan->constraints.first; con; con= con->next) {
		if(con->type == CONSTRAINT_TYPE_KINEMATIC) {
			bKinematicConstraint *data = (bKinematicConstraint*)con->data;
			int segcount= 0;
			
			setlinestyle(3);
			glBegin(GL_LINES);
			
			/* exclude tip from chain? */
			if(!(data->flag & CONSTRAINT_IK_TIP))
				parchan= pchan->parent;
			else
				parchan= pchan;
			
			glVertex3fv(parchan->pose_tail);
			
			/* Find the chain's root */
			while (parchan->parent){
				segcount++;
				if(segcount==data->rootbone || segcount>255) break; // 255 is weak
				parchan= parchan->parent;
			}
			if(parchan)
				glVertex3fv(parchan->pose_head);
			
			glEnd();
			setlinestyle(0);
		}
	}
}

static void bgl_sphere_project(float ax, float az)
{
	float dir[3], sine, q3;

	sine= 1.0f-ax*ax-az*az;
	q3= (sine < 0.0f)? 0.0f: 2.0f*sqrt(sine);

	dir[0]= -az*q3;
	dir[1]= 1.0f-2.0f*sine;
	dir[2]= ax*q3;

	glVertex3fv(dir);
}

static void draw_dof_ellipse(float ax, float az)
{
	static float staticSine[16] = {
		0.0, 0.104528463268, 0.207911690818, 0.309016994375,
		0.406736643076, 0.5, 0.587785252292, 0.669130606359,
		0.743144825477, 0.809016994375, 0.866025403784,
		0.913545457643, 0.951056516295, 0.978147600734,
		0.994521895368, 1.0
	};

	int i, j, n=16;
	float x, z, px, pz;

	glEnable(GL_BLEND);
	glDepthMask(0);

	glColor4ub(70, 70, 70, 50);

	glBegin(GL_QUADS);
	pz= 0.0f;
	for(i=1; i<n; i++) {
		z= staticSine[i];

		px= 0.0f;
		for(j=1; j<n-i+1; j++) {
			x = staticSine[j];

			if(j == n-i) {
				glEnd();
				glBegin(GL_TRIANGLES);
				bgl_sphere_project(ax*px, az*z);
				bgl_sphere_project(ax*px, az*pz);
				bgl_sphere_project(ax*x, az*pz);
				glEnd();
				glBegin(GL_QUADS);
			}
			else {
				bgl_sphere_project(ax*x, az*z);
				bgl_sphere_project(ax*x, az*pz);
				bgl_sphere_project(ax*px, az*pz);
				bgl_sphere_project(ax*px, az*z);
			}

			px= x;
		}
		pz= z;
	}
	glEnd();

	glDisable(GL_BLEND);
	glDepthMask(1);

	glColor3ub(0, 0, 0);

	glBegin(GL_LINE_STRIP);
	for(i=0; i<n; i++)
		bgl_sphere_project(staticSine[n-i-1]*ax, staticSine[i]*az);
	glEnd();
}

static void draw_pose_dofs(Object *ob)
{
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	Bone *bone;
	
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		bone= pchan->bone;
		if(bone && !(bone->flag & BONE_HIDDEN_P)) {
			if(bone->flag & BONE_SELECTED) {
				if(bone->layer & arm->layer) {
					if(pchan->ikflag & (BONE_IK_XLIMIT|BONE_IK_ZLIMIT)) {
						if(pose_channel_in_IK_chain(ob, pchan)) {
							float corner[4][3], posetrans[3], mat[4][4];
							float phi=0.0f, theta=0.0f, scale;
							int a, i;

							/* in parent-bone pose, but own restspace */
							glPushMatrix();

							VECCOPY(posetrans, pchan->pose_mat[3]);
							glTranslatef(posetrans[0], posetrans[1], posetrans[2]);

							if(pchan->parent) {
								Mat4CpyMat4(mat, pchan->parent->pose_mat);
								mat[3][0]= mat[3][1]= mat[3][2]= 0.0f;
								glMultMatrixf(mat);
							}

							Mat4CpyMat3(mat, pchan->bone->bone_mat);
							glMultMatrixf(mat);

							scale= bone->length*pchan->size[1];
							glScalef(scale, scale, scale);

							if(pchan->ikflag & BONE_IK_XLIMIT) {
								if(pchan->ikflag & BONE_IK_ZLIMIT) {
									float amin[3], amax[3];

									for(i=0; i<3; i++) {
										amin[i]= sin(pchan->limitmin[i]*M_PI/360.0);
										amax[i]= sin(pchan->limitmax[i]*M_PI/360.0);
									}
									
									glScalef(1.0, -1.0, 1.0);
									if (amin[0] != 0.0 && amin[2] != 0.0)
										draw_dof_ellipse(amin[0], amin[2]);
									if (amin[0] != 0.0 && amax[2] != 0.0)
										draw_dof_ellipse(amin[0], amax[2]);
									if (amax[0] != 0.0 && amin[2] != 0.0)
										draw_dof_ellipse(amax[0], amin[2]);
									if (amax[0] != 0.0 && amax[2] != 0.0)
										draw_dof_ellipse(amax[0], amax[2]);
									glScalef(1.0, -1.0, 1.0);
								}
							}
							
							/* arcs */
							if(pchan->ikflag & BONE_IK_ZLIMIT) {
								theta= 0.5*(pchan->limitmin[2]+pchan->limitmax[2]);
								glRotatef(theta, 0.0f, 0.0f, 1.0f);

								glColor3ub(50, 50, 255);	// blue, Z axis limit
								glBegin(GL_LINE_STRIP);
								for(a=-16; a<=16; a++) {
									float fac= ((float)a)/16.0f;
									phi= fac*(M_PI/360.0f)*(pchan->limitmax[2]-pchan->limitmin[2]);
									
									if(a==-16) i= 0; else i= 1;
									corner[i][0]= sin(phi);
									corner[i][1]= cos(phi);
									corner[i][2]= 0.0f;
									glVertex3fv(corner[i]);
								}
								glEnd();

								glRotatef(-theta, 0.0f, 0.0f, 1.0f);
							}					

							if(pchan->ikflag & BONE_IK_XLIMIT) {
								theta=  0.5*( pchan->limitmin[0]+pchan->limitmax[0]);
								glRotatef(theta, 1.0f, 0.0f, 0.0f);

								glColor3ub(255, 50, 50);	// Red, X axis limit
								glBegin(GL_LINE_STRIP);
								for(a=-16; a<=16; a++) {
									float fac= ((float)a)/16.0f;
									phi= 0.5f*M_PI + fac*(M_PI/360.0f)*(pchan->limitmax[0]-pchan->limitmin[0]);

									if(a==-16) i= 2; else i= 3;
									corner[i][0]= 0.0f;
									corner[i][1]= sin(phi);
									corner[i][2]= cos(phi);
									glVertex3fv(corner[i]);
								}
								glEnd();

								glRotatef(-theta, 1.0f, 0.0f, 0.0f);
							}

							glPopMatrix(); // out of cone, out of bone
						}
					}
				}
			}
		}
	}
}

/* assumes object is Armature with pose */
static void draw_pose_channels(Base *base, int dt)
{
	Object *ob= base->object;
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	Bone *bone;
	GLfloat tmp;
	float smat[4][4], imat[4][4];
	int index= -1;
	int do_dashed= 1;
	short flag, constflag;
	
	/* hacky... prevent outline select from drawing dashed helplines */
	glGetFloatv(GL_LINE_WIDTH, &tmp);
	if(tmp > 1.1) do_dashed= 0;
	if (G.vd->flag & V3D_HIDE_HELPLINES) do_dashed= 0;
	
	/* precalc inverse matrix for drawing screen aligned */
	if(arm->drawtype==ARM_ENVELOPE) {
		/* precalc inverse matrix for drawing screen aligned */
		mygetmatrix(smat);
		Mat4MulFloat3(smat[0], 1.0f/VecLength(ob->obmat[0]));
		Mat4Invert(imat, smat);
		
		/* and draw blended distances */
		if(arm->flag & ARM_POSEMODE) {
			glEnable(GL_BLEND);
			//glShadeModel(GL_SMOOTH);
			
			if(G.vd->zbuf) glDisable(GL_DEPTH_TEST);
			
			for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
				bone= pchan->bone;
				if(bone && !(bone->flag & (BONE_HIDDEN_P|BONE_NO_DEFORM))) {
					if(bone->flag & (BONE_SELECTED))
						if(bone->layer & arm->layer)
							draw_sphere_bone_dist(smat, imat, bone->flag, pchan, NULL);
				}
			}
			
			if(G.vd->zbuf) glEnable(GL_DEPTH_TEST);
			glDisable(GL_BLEND);
			//glShadeModel(GL_FLAT);
		}
	}
	
	/* little speedup, also make sure transparent only draws once */
	glCullFace(GL_BACK); 
	glEnable(GL_CULL_FACE);
	
	/* if solid we draw that first, with selection codes, but without names, axes etc */
	if(dt>OB_WIRE) {
		if(arm->flag & ARM_POSEMODE) index= base->selcol;
		
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			bone= pchan->bone;
			if(bone && !(bone->flag & BONE_HIDDEN_P)) {
				if(bone->layer & arm->layer) {
					glPushMatrix();
					glMultMatrixf(pchan->pose_mat);
					
					/* catch exception for bone with hidden parent */
					flag= bone->flag;
					if(bone->parent && (bone->parent->flag & BONE_HIDDEN_P))
						flag &= ~BONE_CONNECTED;
					
					if(pchan->custom && !(arm->flag & ARM_NO_CUSTOM))
						draw_custom_bone(pchan->custom, OB_SOLID, arm->flag, flag, index, bone->length);
					else if(arm->drawtype==ARM_LINE)
						;	/* nothing in solid */
					else if(arm->drawtype==ARM_ENVELOPE)
						draw_sphere_bone(OB_SOLID, arm->flag, flag, 0, index, pchan, NULL);
					else if(arm->drawtype==ARM_B_BONE)
						draw_b_bone(OB_SOLID, arm->flag, flag, 0, index, pchan, NULL);
					else {
						draw_bone(OB_SOLID, arm->flag, flag, 0, index, bone->length);
					}
					glPopMatrix();
				}
			}
			if (index!= -1) index+= 0x10000;	// pose bones count in higher 2 bytes only
		}
		/* very very confusing... but in object mode, solid draw, we cannot do glLoadName yet, stick bones are dawn in next loop */
		if(arm->drawtype!=ARM_LINE) {
			glLoadName (index & 0xFFFF);	// object tag, for bordersel optim
			index= -1;
		}
	}
	
	/* wire draw over solid only in posemode */
	if( dt<=OB_WIRE || (arm->flag & ARM_POSEMODE) || arm->drawtype==ARM_LINE) {
	
		/* draw line check first. we do selection indices */
		if (arm->drawtype==ARM_LINE) {
			if (arm->flag & ARM_POSEMODE) index= base->selcol;
		}
		/* if solid && posemode, we draw again with polygonoffset */
		else if (dt>OB_WIRE && (arm->flag & ARM_POSEMODE))
			bglPolygonOffset(1.0);
		else
			/* and we use selection indices if not done yet */
			if (arm->flag & ARM_POSEMODE) index= base->selcol;
		
		for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
			bone= pchan->bone;
			if(bone && !(bone->flag & BONE_HIDDEN_P)) {
				if(bone->layer & arm->layer) {
					if (do_dashed && bone->parent) {
						/*	Draw a line from our root to the parent's tip */
						if(!(bone->flag & BONE_CONNECTED) ){
							if (arm->flag & ARM_POSEMODE) {
								glLoadName (index & 0xFFFF);	// object tag, for bordersel optim
								BIF_ThemeColor(TH_WIRE);
							}
							setlinestyle(3);
							glBegin(GL_LINES);
							glVertex3fv(pchan->pose_head);
							glVertex3fv(pchan->parent->pose_tail);
							glEnd();
							setlinestyle(0);
						}
						//	Draw a line to IK root bone
						if(arm->flag & ARM_POSEMODE) {
							if(pchan->constflag & PCHAN_HAS_IK) {
								if(bone->flag & BONE_SELECTED) {
									
									if(pchan->constflag & PCHAN_HAS_TARGET) glColor3ub(200, 120, 0);
									else glColor3ub(200, 200, 50);	// add theme!

									glLoadName (index & 0xFFFF);
									pchan_draw_IK_root_lines(pchan);
								}
							}
						}
					}
					
					if(arm->drawtype!=ARM_ENVELOPE) {
						glPushMatrix();
						glMultMatrixf(pchan->pose_mat);
					}
					
					/* catch exception for bone with hidden parent */
					flag= bone->flag;
					if(bone->parent && (bone->parent->flag & BONE_HIDDEN_P))
						flag &= ~BONE_CONNECTED;
					
					/* extra draw service for pose mode */
					constflag= pchan->constflag;
					if(pchan->flag & (POSE_ROT|POSE_LOC|POSE_SIZE))
						constflag |= PCHAN_HAS_ACTION;
					if(pchan->flag & POSE_STRIDE)
						constflag |= PCHAN_HAS_STRIDE;

					if(pchan->custom && !(arm->flag & ARM_NO_CUSTOM)) {
						if(dt<OB_SOLID)
							draw_custom_bone(pchan->custom, OB_WIRE, arm->flag, flag, index, bone->length);
					}
					else if(arm->drawtype==ARM_ENVELOPE) {
						if(dt<OB_SOLID)
							draw_sphere_bone_wire(smat, imat, arm->flag, flag, constflag, index, pchan, NULL);
					}
					else if(arm->drawtype==ARM_LINE)
						draw_line_bone(arm->flag, flag, constflag, index, pchan, NULL);
					else if(arm->drawtype==ARM_B_BONE)
						draw_b_bone(OB_WIRE, arm->flag, flag, constflag, index, pchan, NULL);
					else {
						draw_bone(OB_WIRE, arm->flag, flag, constflag, index, bone->length);
					}
					
					if(arm->drawtype!=ARM_ENVELOPE)
						glPopMatrix();
				}
			}
			if (index!= -1) index+= 0x10000;	// pose bones count in higher 2 bytes only
		}
		/* restore things */
		if (arm->drawtype!=ARM_LINE && dt>OB_WIRE && (arm->flag & ARM_POSEMODE))
			bglPolygonOffset(0.0);
		
	}	
	
	/* restore */
	glDisable(GL_CULL_FACE);
	
	/* draw DoFs */
	if (arm->flag & ARM_POSEMODE)
		draw_pose_dofs(ob);

	/* finally names and axes */
	if(arm->flag & (ARM_DRAWNAMES|ARM_DRAWAXES)) {
		// patch for several 3d cards (IBM mostly) that crash on glSelect with text drawing
		if((G.f & G_PICKSEL) == 0) {
			float vec[3];
			
			if(G.vd->zbuf) glDisable(GL_DEPTH_TEST);
			
			for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
				if((pchan->bone->flag & BONE_HIDDEN_P)==0) {
					if(pchan->bone->layer & arm->layer) {
						if (arm->flag & (ARM_EDITMODE|ARM_POSEMODE)) {
							bone= pchan->bone;
							if(bone->flag & BONE_SELECTED) BIF_ThemeColor(TH_TEXT_HI);
							else BIF_ThemeColor(TH_TEXT);
						}
						else if(dt > OB_WIRE) BIF_ThemeColor(TH_TEXT);
						
						if (arm->flag & ARM_DRAWNAMES){
							VecMidf(vec, pchan->pose_head, pchan->pose_tail);
							glRasterPos3fv(vec);
							BMF_DrawString(G.font, " ");
							BMF_DrawString(G.font, pchan->name);
						}				
						/*	Draw additional axes */
						if( (arm->flag & ARM_DRAWAXES) && (arm->flag & ARM_POSEMODE) ){
							glPushMatrix();
							glMultMatrixf(pchan->pose_mat);
							glTranslatef(0.0f, pchan->bone->length, 0.0f);
							drawaxes(0.25f*pchan->bone->length, 0, OB_ARROWS);
							glPopMatrix();
						}
					}
				}
			}
			
			if(G.vd->zbuf) glEnable(GL_DEPTH_TEST);
		}
	}

}

/* in editmode, we don't store the bone matrix... */
static void set_matrix_editbone(EditBone *eBone)
{
	float		delta[3],offset[3];
	float		mat[3][3], bmat[4][4];
	
	/*	Compose the parent transforms (i.e. their translations) */
	VECCOPY (offset, eBone->head);
	
	glTranslatef (offset[0],offset[1],offset[2]);
	
	VecSubf(delta, eBone->tail, eBone->head);	
	
	eBone->length = sqrt (delta[0]*delta[0] + delta[1]*delta[1] +delta[2]*delta[2]);
	
	vec_roll_to_mat3(delta, eBone->roll, mat);
	Mat4CpyMat3(bmat, mat);
				
	glMultMatrixf (bmat);
	
}

static void draw_ebones(Object *ob, int dt)
{
	EditBone *eBone;
	bArmature *arm= ob->data;
	float smat[4][4], imat[4][4];
	unsigned int index;
	int flag;
	
	/* envelope (deform distance) */
	if(arm->drawtype==ARM_ENVELOPE) {
		/* precalc inverse matrix for drawing screen aligned */
		mygetmatrix(smat);
		Mat4MulFloat3(smat[0], 1.0f/VecLength(ob->obmat[0]));
		Mat4Invert(imat, smat);
		
		/* and draw blended distances */
		glEnable(GL_BLEND);
		//glShadeModel(GL_SMOOTH);
		
		if(G.vd->zbuf) glDisable(GL_DEPTH_TEST);

		for (eBone=G.edbo.first, index=0; eBone; eBone=eBone->next, index++){
			if(eBone->layer & arm->layer)
				if(!(eBone->flag & (BONE_HIDDEN_A|BONE_NO_DEFORM)))
					if(eBone->flag & (BONE_SELECTED|BONE_TIPSEL|BONE_ROOTSEL))
						draw_sphere_bone_dist(smat, imat, eBone->flag, NULL, eBone);
		}
		
		if(G.vd->zbuf) glEnable(GL_DEPTH_TEST);
		glDisable(GL_BLEND);
		//glShadeModel(GL_FLAT);
	}
	
	/* if solid we draw it first */
	if(dt>OB_WIRE && arm->drawtype!=ARM_LINE) {
		index= 0;
		for (eBone=G.edbo.first, index=0; eBone; eBone=eBone->next, index++){
			if(eBone->layer & arm->layer) {
				if(!(eBone->flag & BONE_HIDDEN_A)) {
					glPushMatrix();
					set_matrix_editbone(eBone);
					
					/* catch exception for bone with hidden parent */
					flag= eBone->flag;
					if(eBone->parent && ((eBone->parent->flag & BONE_HIDDEN_A) || (eBone->parent->layer & arm->layer)==0) )
						flag &= ~BONE_CONNECTED;
					
					if(arm->drawtype==ARM_ENVELOPE)
						draw_sphere_bone(OB_SOLID, arm->flag, flag, 0, index, NULL, eBone);
					else if(arm->drawtype==ARM_B_BONE)
						draw_b_bone(OB_SOLID, arm->flag, flag, 0, index, NULL, eBone);
					else {
						draw_bone(OB_SOLID, arm->flag, flag, 0, index, eBone->length);
					}
					
					glPopMatrix();
				}
			}
		}
	}
	
	/* if wire over solid, set offset */
	index= -1;
	glLoadName(-1);
	if(arm->drawtype==ARM_LINE) {
		if(G.f & G_PICKSEL)
			index= 0;
	}
	else if (dt>OB_WIRE) 
		bglPolygonOffset(1.0);
	else if(arm->flag & ARM_EDITMODE) 
		index= 0;	// do selection codes
	
	for (eBone=G.edbo.first; eBone; eBone=eBone->next){
		if(eBone->layer & arm->layer) {
			if(!(eBone->flag & BONE_HIDDEN_A)) {
				
				/* catch exception for bone with hidden parent */
				flag= eBone->flag;
				if(eBone->parent && ((eBone->parent->flag & BONE_HIDDEN_A) || (eBone->parent->layer & arm->layer)==0) )
					flag &= ~BONE_CONNECTED;
				
				if(arm->drawtype==ARM_ENVELOPE) {
					if(dt<OB_SOLID)
						draw_sphere_bone_wire(smat, imat, arm->flag, flag, 0, index, NULL, eBone);
				}
				else {
					glPushMatrix();
					set_matrix_editbone(eBone);
					
					if(arm->drawtype==ARM_LINE) 
						draw_line_bone(arm->flag, flag, 0, index, NULL, eBone);
					else if(arm->drawtype==ARM_B_BONE)
						draw_b_bone(OB_WIRE, arm->flag, flag, 0, index, NULL, eBone);
					else
						draw_bone(OB_WIRE, arm->flag, flag, 0, index, eBone->length);

					glPopMatrix();
				}
			
				/* offset to parent */
				if (eBone->parent) {
					BIF_ThemeColor(TH_WIRE);
					glLoadName (-1);		// -1 here is OK!
					setlinestyle(3);
					
					glBegin(GL_LINES);
					glVertex3fv(eBone->parent->tail);
					glVertex3fv(eBone->head);
					glEnd();
					
					setlinestyle(0);
				}
			}
		}
		if(index!=-1) index++;
	}
	
	/* restore */
	if(arm->drawtype==ARM_LINE);
	else if (dt>OB_WIRE) bglPolygonOffset(0.0);
	
	/* finally names and axes */
	if(arm->flag & (ARM_DRAWNAMES|ARM_DRAWAXES)) {
		// patch for several 3d cards (IBM mostly) that crash on glSelect with text drawing
		if((G.f & G_PICKSEL) == 0) {
			float vec[3];
			
			if(G.vd->zbuf) glDisable(GL_DEPTH_TEST);
			
			for (eBone=G.edbo.first, index=0; eBone; eBone=eBone->next, index++){
				if(eBone->layer & arm->layer) {
					if(!(eBone->flag & BONE_HIDDEN_A)) {
						
						if(eBone->flag & BONE_SELECTED) BIF_ThemeColor(TH_TEXT_HI);
						else BIF_ThemeColor(TH_TEXT);
						
						/*	Draw name */
						if(arm->flag & ARM_DRAWNAMES){
							VecMidf(vec, eBone->head, eBone->tail);
							glRasterPos3fv(vec);
							BMF_DrawString(G.font, " ");
							BMF_DrawString(G.font, eBone->name);
						}					
						/*	Draw additional axes */
						if(arm->flag & ARM_DRAWAXES){
							glPushMatrix();
							set_matrix_editbone(eBone);
							glTranslatef(0.0f, eBone->length, 0.0f);
							drawaxes(eBone->length*0.25f, 0, OB_ARROWS);
							glPopMatrix();
						}
						
					}
				}
			}
			
			if(G.vd->zbuf) glEnable(GL_DEPTH_TEST);
		}
	}
}

/* in view space */
static void draw_pose_paths(Object *ob)
{
	bArmature *arm= ob->data;
	bPoseChannel *pchan;
	bAction *act;
	bActionChannel *achan;
	CfraElem *ce;
	ListBase ak;
	float *fp;
	int a;
	int stepsize, sfra;
	
	if(G.vd->zbuf) glDisable(GL_DEPTH_TEST);
	
	glPushMatrix();
	glLoadMatrixf(G.vd->viewmat);
	
	/* version patch here - cannot access frame info from file reading */
	if (arm->pathsize == 0) arm->pathsize= 1;
	stepsize = arm->pathsize;
	
	for(pchan= ob->pose->chanbase.first; pchan; pchan= pchan->next) {
		if(pchan->bone->layer & arm->layer) {
			if(pchan->path) {
				/* version patch here - cannot access frame info from file reading */
				if ((pchan->pathsf == 0) || (pchan->pathef == 0)) {
					pchan->pathsf= SFRA;
					pchan->pathef= EFRA;
				}
				sfra= pchan->pathsf;
				
				/* draw curve-line of path */
				BIF_ThemeColorBlend(TH_WIRE, TH_BACK, 0.7);
				glBegin(GL_LINE_STRIP);
				for(a=0, fp= pchan->path; a<pchan->pathlen; a++, fp+=3)
					glVertex3fv(fp);
				glEnd();
				
				glPointSize(1.0);
				
				/* draw little black point at each frame
				 * NOTE: this is not really visible/noticable
				 */
				glBegin(GL_POINTS);
				for(a=0, fp= pchan->path; a<pchan->pathlen; a++, fp+=3) 
					glVertex3fv(fp);
				glEnd();
				
				/* Draw little white dots at each framestep value */
				BIF_ThemeColor(TH_TEXT_HI);
				glBegin(GL_POINTS);
				for(a=0, fp= pchan->path; a<pchan->pathlen; a+=stepsize, fp+=(stepsize*3)) 
					glVertex3fv(fp);
				glEnd();
				
				/* Draw frame numbers at each framestep value */
				if (arm->pathflag & ARM_PATH_FNUMS) {
					for(a=0, fp= pchan->path; a<pchan->pathlen; a+=stepsize, fp+=(stepsize*3)) {
						char str[32];
						
						/* only draw framenum if several consecutive highlighted points occur on same point */
						if (a == 0) {
							glRasterPos3fv(fp);
							sprintf(str, "  %d\n", (a+sfra));
							BMF_DrawString(G.font, str);
						}
						else if ((a > stepsize) && (a < pchan->pathlen-stepsize)) { 
							if ((VecEqual(fp, fp-(stepsize*3))==0) || (VecEqual(fp, fp+(stepsize*3))==0)) {
								glRasterPos3fv(fp);
								sprintf(str, "  %d\n", (a+sfra));
								BMF_DrawString(G.font, str);
							}
						}
					}
				}
				
				/* Keyframes - dots and numbers */
				if (arm->pathflag & ARM_PATH_KFRAS) {
					/* build list of all keyframes in active action for pchan */
					ak.first = ak.last = NULL;	
					act= ob_get_action(ob);
					if (act) {
						achan= get_action_channel(act, pchan->name);
						if (achan) 
							ipo_to_keylist(achan->ipo, &ak, NULL);
					}
					
					/* Draw little yellow dots at each keyframe */
					BIF_ThemeColor(TH_VERTEX_SELECT);
					glBegin(GL_POINTS);
					for(a=0, fp= pchan->path; a<pchan->pathlen; a++, fp+=3) {
						for (ce= ak.first; ce; ce= ce->next) {
							if (ce->cfra == (a+sfra))
								glVertex3fv(fp);
						}
					}
					glEnd();
					
					/* Draw frame numbers of keyframes  */
					if (arm->pathflag & ARM_PATH_FNUMS) {
						for(a=0, fp= pchan->path; a<pchan->pathlen; a++, fp+=3) {
							for (ce= ak.first; ce; ce= ce->next) {
								if (ce->cfra == (a+sfra)) {
									char str[32];
									
									glRasterPos3fv(fp);
									sprintf(str, "  %d\n", (a+sfra));
									BMF_DrawString(G.font, str);
								}
							}
						}
					}
					
					BLI_freelistN(&ak);
				}
			}
		}
	}
	
	if(G.vd->zbuf) glEnable(GL_DEPTH_TEST);
	glPopMatrix();
}

/* draw ghosts that occur within a frame range 
 * 	note: object should be in posemode */
static void draw_ghost_poses_range(Base *base)
{
	Object *ob= base->object;
	bArmature *arm= ob->data;
	bPose *posen, *poseo;
	float start, end, stepsize, range, colfac;
	int cfrao, flago, ipoflago;
	
	start = arm->ghostsf;
	end = arm->ghostef;
	if (end<=start)
		return;
	
	stepsize= (float)(arm->ghostsize);
	range= (float)(end - start);
	
	/* store values */
	ob->flag &= ~OB_POSEMODE;
	cfrao= CFRA;
	flago= arm->flag;
	arm->flag &= ~(ARM_DRAWNAMES|ARM_DRAWAXES);
	ipoflago= ob->ipoflag; 
	ob->ipoflag |= OB_DISABLE_PATH;
	
	/* copy the pose */
	poseo= ob->pose;
	copy_pose(&posen, ob->pose, 1);
	ob->pose= posen;
	armature_rebuild_pose(ob, ob->data);	/* child pointers for IK */
	
	glEnable(GL_BLEND);
	if(G.vd->zbuf) glDisable(GL_DEPTH_TEST);
	
	/* draw from first frame of range to last */
	for(CFRA= start; CFRA<end; CFRA+=stepsize) {
		colfac = (end-CFRA)/range;
		BIF_ThemeColorShadeAlpha(TH_WIRE, 0, -128-(int)(120.0f*sqrt(colfac)));
		
		do_all_pose_actions(ob);
		where_is_pose(ob);
		draw_pose_channels(base, OB_WIRE);
	}
	glDisable(GL_BLEND);
	if(G.vd->zbuf) glEnable(GL_DEPTH_TEST);

	free_pose_channels(posen);
	MEM_freeN(posen);
	
	/* restore */
	CFRA= cfrao;
	ob->pose= poseo;
	arm->flag= flago;
	armature_rebuild_pose(ob, ob->data);
	ob->flag |= OB_POSEMODE;
	ob->ipoflag= ipoflago; 

}

/* object is supposed to be armature in posemode */
static void draw_ghost_poses(Base *base)
{
	Object *ob= base->object;
	bArmature *arm= ob->data;
	bPose *posen, *poseo;
	bActionStrip *strip;
	float cur, start, end, stepsize, range, colfac, actframe, ctime;
	int cfrao, maptime, flago, ipoflago;
	
	/* pre conditions, get an action with sufficient frames */
	if(ob->action==NULL)
		return;

	calc_action_range(ob->action, &start, &end, 0);
	if(start==end)
		return;

	stepsize= (float)(arm->ghostsize);
	range= (float)(arm->ghostep)*stepsize + 0.5f;	/* plus half to make the for loop end correct */
	
	/* we only map time for armature when an active strip exists */
	for (strip=ob->nlastrips.first; strip; strip=strip->next)
		if(strip->flag & ACTSTRIP_ACTIVE)
			break;
	
	maptime= (strip!=NULL);
	
	/* store values */
	ob->flag &= ~OB_POSEMODE;
	cfrao= CFRA;
	if(maptime) actframe= get_action_frame(ob, (float)CFRA);
	else actframe= CFRA;
	flago= arm->flag;
	arm->flag &= ~(ARM_DRAWNAMES|ARM_DRAWAXES);
	ipoflago= ob->ipoflag; 
	ob->ipoflag |= OB_DISABLE_PATH;
	
	/* copy the pose */
	poseo= ob->pose;
	copy_pose(&posen, ob->pose, 1);
	ob->pose= posen;
	armature_rebuild_pose(ob, ob->data);	/* child pointers for IK */
	
	glEnable(GL_BLEND);
	if(G.vd->zbuf) glDisable(GL_DEPTH_TEST);
	
	/* draw from darkest blend to lowest */
	for(cur= stepsize; cur<range; cur+=stepsize) {
		
		ctime= cur - fmod((float)cfrao, stepsize);	/* ensures consistant stepping */
		colfac= ctime/range;
		BIF_ThemeColorShadeAlpha(TH_WIRE, 0, -128-(int)(120.0f*sqrt(colfac)));
		
		/* only within action range */
		if(actframe+ctime >= start && actframe+ctime <= end) {
			
			if(maptime) CFRA= (int)get_action_frame_inv(ob, actframe+ctime);
			else CFRA= (int)floor(actframe+ctime);
			
			if(CFRA!=cfrao) {
				do_all_pose_actions(ob);
				where_is_pose(ob);
				draw_pose_channels(base, OB_WIRE);
			}
		}
		
		ctime= cur + fmod((float)cfrao, stepsize) - stepsize+1.0f;	/* ensures consistant stepping */
		colfac= ctime/range;
		BIF_ThemeColorShadeAlpha(TH_WIRE, 0, -128-(int)(120.0f*sqrt(colfac)));
		
		/* only within action range */
		if(actframe-ctime >= start && actframe-ctime <= end) {
			
			if(maptime) CFRA= (int)get_action_frame_inv(ob, actframe-ctime);
			else CFRA= (int)floor(actframe-ctime);

			if(CFRA!=cfrao) {
				do_all_pose_actions(ob);
				where_is_pose(ob);
				draw_pose_channels(base, OB_WIRE);
			}
		}
	}
	glDisable(GL_BLEND);
	if(G.vd->zbuf) glEnable(GL_DEPTH_TEST);

	free_pose_channels(posen);
	MEM_freeN(posen);
	
	/* restore */
	CFRA= cfrao;
	ob->pose= poseo;
	arm->flag= flago;
	armature_rebuild_pose(ob, ob->data);
	ob->flag |= OB_POSEMODE;
	ob->ipoflag= ipoflago; 

}

/* called from drawobject.c, return 1 if nothing was drawn */
int draw_armature(Base *base, int dt)
{
	Object *ob= base->object;
	bArmature *arm= ob->data;
	int retval= 0;
	
	if(dt>OB_WIRE && arm->drawtype!=ARM_LINE) {
		/* we use color for solid lighting */
		glColorMaterial(GL_FRONT_AND_BACK, GL_SPECULAR);
		glEnable(GL_COLOR_MATERIAL);
		glColor3ub(0,0,0);	// clear spec
		glDisable(GL_COLOR_MATERIAL);
		
		glColorMaterial(GL_FRONT_AND_BACK, GL_DIFFUSE);
		glFrontFace((ob->transflag&OB_NEG_SCALE)?GL_CW:GL_CCW);	// only for lighting...
	}
	
	/* arm->flag is being used to detect mode... */
	/* editmode? */
	if(ob==G.obedit || (G.obedit && ob->data==G.obedit->data)) {
		if(ob==G.obedit) arm->flag |= ARM_EDITMODE;
		draw_ebones(ob, dt);
		arm->flag &= ~ARM_EDITMODE;
	}
	else{
		/*	Draw Pose */
		if(ob->pose && ob->pose->chanbase.first) {
			/* drawing posemode selection indices or colors only in these cases */
			if(!(base->flag & OB_FROMDUPLI)) {
				if(G.f & G_PICKSEL) {
					if(ob->flag & OB_POSEMODE) 
						arm->flag |= ARM_POSEMODE;
				}
				else if(ob->flag & OB_POSEMODE) {
					if (arm->ghosttype == ARM_GHOST_RANGE){
						draw_ghost_poses_range(base);
					}
					else {
						if (arm->ghostep)
							draw_ghost_poses(base);
					}
					
					if(ob==OBACT) 
						arm->flag |= ARM_POSEMODE;
					else if(G.f & G_WEIGHTPAINT)
						arm->flag |= ARM_POSEMODE;
					
					draw_pose_paths(ob);
				}	
			}			
			draw_pose_channels(base, dt);
			arm->flag &= ~ARM_POSEMODE; 
			
			if(ob->flag & OB_POSEMODE)
				BIF_ThemeColor(TH_WIRE);	/* restore, for extra draw stuff */
		}
		else retval= 1;
	}
	/* restore */
	glFrontFace(GL_CCW);

	return retval;
}

/* *************** END Armature drawing ******************* */

