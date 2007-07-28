/* arithb.c
 *
 * simple math for blender code
 *
 * sort of cleaned up mar-01 nzc
 *
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

/* ************************ FUNKTIES **************************** */

#include <math.h>
#include <sys/types.h>
#include <string.h> 
#include <float.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#if defined(__sun__) || defined( __sun ) || defined (__sparc) || defined (__sparc__)
#include <strings.h>
#endif

#if !defined(__sgi) && !defined(WIN32)
#include <sys/time.h>
#include <unistd.h>
#endif

#include <stdio.h>
#include "BLI_arithb.h"

/* A few small defines. Keep'em local! */
#define SMALL_NUMBER	1.e-8
#define ABS(x)	((x) < 0 ? -(x) : (x))
#define SWAP(type, a, b)	{ type sw_ap; sw_ap=(a); (a)=(b); (b)=sw_ap; }


#if defined(WIN32) || defined(__APPLE__)
#include <stdlib.h>
#define M_PI 3.14159265358979323846
#define M_SQRT2 1.41421356237309504880   

#endif /* defined(WIN32) || defined(__APPLE__) */


float saacos(float fac)
{
	if(fac<= -1.0f) return (float)M_PI;
	else if(fac>=1.0f) return 0.0;
	else return (float)acos(fac);
}

float saasin(float fac)
{
	if(fac<= -1.0f) return (float)-M_PI/2.0f;
	else if(fac>=1.0f) return (float)M_PI/2.0f;
	else return (float)asin(fac);
}

float sasqrt(float fac)
{
	if(fac<=0.0) return 0.0;
	return (float)sqrt(fac);
}

float Normalize(float *n)
{
	float d;
	
	d= n[0]*n[0]+n[1]*n[1]+n[2]*n[2];
	/* A larger value causes normalize errors in a scaled down models with camera xtreme close */
	if(d>1.0e-35F) {
		d= (float)sqrt(d);

		n[0]/=d; 
		n[1]/=d; 
		n[2]/=d;
	} else {
		n[0]=n[1]=n[2]= 0.0;
		d= 0.0;
	}
	return d;
}

void Crossf(float *c, float *a, float *b)
{
	c[0] = a[1] * b[2] - a[2] * b[1];
	c[1] = a[2] * b[0] - a[0] * b[2];
	c[2] = a[0] * b[1] - a[1] * b[0];
}

/* Inpf returns the dot product, also called the scalar product and inner product */
float Inpf( float *v1, float *v2)
{
	return v1[0]*v2[0]+v1[1]*v2[1]+v1[2]*v2[2];
}

/* Project v1 on v2 */
void Projf(float *c, float *v1, float *v2)
{
	float mul;
	mul = Inpf(v1, v2) / Inpf(v2, v2);
	
	c[0] = mul * v2[0];
	c[1] = mul * v2[1];
	c[2] = mul * v2[2];
}

void Mat3Transp(float mat[][3])
{
	float t;

	t = mat[0][1] ; 
	mat[0][1] = mat[1][0] ; 
	mat[1][0] = t;
	t = mat[0][2] ; 
	mat[0][2] = mat[2][0] ; 
	mat[2][0] = t;
	t = mat[1][2] ; 
	mat[1][2] = mat[2][1] ; 
	mat[2][1] = t;
}

void Mat4Transp(float mat[][4])
{
	float t;

	t = mat[0][1] ; 
	mat[0][1] = mat[1][0] ; 
	mat[1][0] = t;
	t = mat[0][2] ; 
	mat[0][2] = mat[2][0] ; 
	mat[2][0] = t;
	t = mat[0][3] ; 
	mat[0][3] = mat[3][0] ; 
	mat[3][0] = t;

	t = mat[1][2] ; 
	mat[1][2] = mat[2][1] ; 
	mat[2][1] = t;
	t = mat[1][3] ; 
	mat[1][3] = mat[3][1] ; 
	mat[3][1] = t;

	t = mat[2][3] ; 
	mat[2][3] = mat[3][2] ; 
	mat[3][2] = t;
}


/*
 * invertmat - 
 * 		computes the inverse of mat and puts it in inverse.  Returns 
 *	TRUE on success (i.e. can always find a pivot) and FALSE on failure.
 * 	Uses Gaussian Elimination with partial (maximal column) pivoting.
 *
 *					Mark Segal - 1992
 */

int Mat4Invert(float inverse[][4], float mat[][4])
{
	int i, j, k;
	double temp;
	float tempmat[4][4];
	float max;
	int maxj;

	/* Set inverse to identity */
	for (i=0; i<4; i++)
		for (j=0; j<4; j++)
			inverse[i][j] = 0;
	for (i=0; i<4; i++)
		inverse[i][i] = 1;

	/* Copy original matrix so we don't mess it up */
	for(i = 0; i < 4; i++)
		for(j = 0; j <4; j++)
			tempmat[i][j] = mat[i][j];

	for(i = 0; i < 4; i++) {
		/* Look for row with max pivot */
		max = ABS(tempmat[i][i]);
		maxj = i;
		for(j = i + 1; j < 4; j++) {
			if(ABS(tempmat[j][i]) > max) {
				max = ABS(tempmat[j][i]);
				maxj = j;
			}
		}
		/* Swap rows if necessary */
		if (maxj != i) {
			for( k = 0; k < 4; k++) {
				SWAP(float, tempmat[i][k], tempmat[maxj][k]);
				SWAP(float, inverse[i][k], inverse[maxj][k]);
			}
		}

		temp = tempmat[i][i];
		if (temp == 0)
			return 0;  /* No non-zero pivot */
		for(k = 0; k < 4; k++) {
			tempmat[i][k] = (float)(tempmat[i][k]/temp);
			inverse[i][k] = (float)(inverse[i][k]/temp);
		}
		for(j = 0; j < 4; j++) {
			if(j != i) {
				temp = tempmat[j][i];
				for(k = 0; k < 4; k++) {
					tempmat[j][k] -= (float)(tempmat[i][k]*temp);
					inverse[j][k] -= (float)(inverse[i][k]*temp);
				}
			}
		}
	}
	return 1;
}
#ifdef TEST_ACTIVE
void Mat4InvertSimp(float inverse[][4], float mat[][4])
{
	/* only for Matrices that have a rotation */
	/* based at GG IV pag 205 */
	float scale;
	
	scale= mat[0][0]*mat[0][0] + mat[1][0]*mat[1][0] + mat[2][0]*mat[2][0];
	if(scale==0.0) return;
	
	scale= 1.0/scale;
	
	/* transpose and scale */
	inverse[0][0]= scale*mat[0][0];
	inverse[1][0]= scale*mat[0][1];
	inverse[2][0]= scale*mat[0][2];
	inverse[0][1]= scale*mat[1][0];
	inverse[1][1]= scale*mat[1][1];
	inverse[2][1]= scale*mat[1][2];
	inverse[0][2]= scale*mat[2][0];
	inverse[1][2]= scale*mat[2][1];
	inverse[2][2]= scale*mat[2][2];

	inverse[3][0]= -(inverse[0][0]*mat[3][0] + inverse[1][0]*mat[3][1] + inverse[2][0]*mat[3][2]);
	inverse[3][1]= -(inverse[0][1]*mat[3][0] + inverse[1][1]*mat[3][1] + inverse[2][1]*mat[3][2]);
	inverse[3][2]= -(inverse[0][2]*mat[3][0] + inverse[1][2]*mat[3][1] + inverse[2][2]*mat[3][2]);
	
	inverse[0][3]= inverse[1][3]= inverse[2][3]= 0.0;
	inverse[3][3]= 1.0;
}
#endif
/*  struct Matrix4; */

#ifdef TEST_ACTIVE
/* this seems to be unused.. */

void Mat4Inv(float *m1, float *m2)
{

/* This gets me into trouble:  */
	float mat1[3][3], mat2[3][3]; 
	
/*  	void Mat3Inv(); */
/*  	void Mat3CpyMat4(); */
/*  	void Mat4CpyMat3(); */

	Mat3CpyMat4((float*)mat2,m2);
	Mat3Inv((float*)mat1, (float*) mat2);
	Mat4CpyMat3(m1, mat1);

}
#endif


float Det2x2(float a,float b,float c,float d)
{

	return a*d - b*c;
}



float Det3x3(float a1, float a2, float a3,
			 float b1, float b2, float b3,
			 float c1, float c2, float c3 )
{
	float ans;

	ans = a1 * Det2x2( b2, b3, c2, c3 )
	    - b1 * Det2x2( a2, a3, c2, c3 )
	    + c1 * Det2x2( a2, a3, b2, b3 );

	return ans;
}

float Det4x4(float m[][4])
{
	float ans;
	float a1,a2,a3,a4,b1,b2,b3,b4,c1,c2,c3,c4,d1,d2,d3,d4;

	a1= m[0][0]; 
	b1= m[0][1];
	c1= m[0][2]; 
	d1= m[0][3];

	a2= m[1][0]; 
	b2= m[1][1];
	c2= m[1][2]; 
	d2= m[1][3];

	a3= m[2][0]; 
	b3= m[2][1];
	c3= m[2][2]; 
	d3= m[2][3];

	a4= m[3][0]; 
	b4= m[3][1];
	c4= m[3][2]; 
	d4= m[3][3];

	ans = a1 * Det3x3( b2, b3, b4, c2, c3, c4, d2, d3, d4)
	    - b1 * Det3x3( a2, a3, a4, c2, c3, c4, d2, d3, d4)
	    + c1 * Det3x3( a2, a3, a4, b2, b3, b4, d2, d3, d4)
	    - d1 * Det3x3( a2, a3, a4, b2, b3, b4, c2, c3, c4);

	return ans;
}


void Mat4Adj(float out[][4], float in[][4])	/* out = ADJ(in) */
{
	float a1, a2, a3, a4, b1, b2, b3, b4;
	float c1, c2, c3, c4, d1, d2, d3, d4;

	a1= in[0][0]; 
	b1= in[0][1];
	c1= in[0][2]; 
	d1= in[0][3];

	a2= in[1][0]; 
	b2= in[1][1];
	c2= in[1][2]; 
	d2= in[1][3];

	a3= in[2][0]; 
	b3= in[2][1];
	c3= in[2][2]; 
	d3= in[2][3];

	a4= in[3][0]; 
	b4= in[3][1];
	c4= in[3][2]; 
	d4= in[3][3];


	out[0][0]  =   Det3x3( b2, b3, b4, c2, c3, c4, d2, d3, d4);
	out[1][0]  = - Det3x3( a2, a3, a4, c2, c3, c4, d2, d3, d4);
	out[2][0]  =   Det3x3( a2, a3, a4, b2, b3, b4, d2, d3, d4);
	out[3][0]  = - Det3x3( a2, a3, a4, b2, b3, b4, c2, c3, c4);

	out[0][1]  = - Det3x3( b1, b3, b4, c1, c3, c4, d1, d3, d4);
	out[1][1]  =   Det3x3( a1, a3, a4, c1, c3, c4, d1, d3, d4);
	out[2][1]  = - Det3x3( a1, a3, a4, b1, b3, b4, d1, d3, d4);
	out[3][1]  =   Det3x3( a1, a3, a4, b1, b3, b4, c1, c3, c4);

	out[0][2]  =   Det3x3( b1, b2, b4, c1, c2, c4, d1, d2, d4);
	out[1][2]  = - Det3x3( a1, a2, a4, c1, c2, c4, d1, d2, d4);
	out[2][2]  =   Det3x3( a1, a2, a4, b1, b2, b4, d1, d2, d4);
	out[3][2]  = - Det3x3( a1, a2, a4, b1, b2, b4, c1, c2, c4);

	out[0][3]  = - Det3x3( b1, b2, b3, c1, c2, c3, d1, d2, d3);
	out[1][3]  =   Det3x3( a1, a2, a3, c1, c2, c3, d1, d2, d3);
	out[2][3]  = - Det3x3( a1, a2, a3, b1, b2, b3, d1, d2, d3);
	out[3][3]  =   Det3x3( a1, a2, a3, b1, b2, b3, c1, c2, c3);
}

void Mat4InvGG(float out[][4], float in[][4])	/* from Graphic Gems I, out= INV(in)  */
{
	int i, j;
	float det;

	/* calculate the adjoint matrix */

	Mat4Adj(out,in);

	det = Det4x4(out);

	if ( fabs( det ) < SMALL_NUMBER) {
		return;
	}

	/* scale the adjoint matrix to get the inverse */

	for (i=0; i<4; i++)
		for(j=0; j<4; j++)
			out[i][j] = out[i][j] / det;

	/* the last factor is not always 1. For that reason an extra division should be implemented? */
}


void Mat3Inv(float m1[][3], float m2[][3])
{
	short a,b;
	float det;

	/* calc adjoint */
	Mat3Adj(m1,m2);

	/* then determinant old matrix! */
	det= m2[0][0]* (m2[1][1]*m2[2][2] - m2[1][2]*m2[2][1])
	    -m2[1][0]* (m2[0][1]*m2[2][2] - m2[0][2]*m2[2][1])
	    +m2[2][0]* (m2[0][1]*m2[1][2] - m2[0][2]*m2[1][1]);

	if(det==0) det=1;
	det= 1/det;
	for(a=0;a<3;a++) {
		for(b=0;b<3;b++) {
			m1[a][b]*=det;
		}
	}
}

void Mat3Adj(float m1[][3], float m[][3])
{
	m1[0][0]=m[1][1]*m[2][2]-m[1][2]*m[2][1];
	m1[0][1]= -m[0][1]*m[2][2]+m[0][2]*m[2][1];
	m1[0][2]=m[0][1]*m[1][2]-m[0][2]*m[1][1];

	m1[1][0]= -m[1][0]*m[2][2]+m[1][2]*m[2][0];
	m1[1][1]=m[0][0]*m[2][2]-m[0][2]*m[2][0];
	m1[1][2]= -m[0][0]*m[1][2]+m[0][2]*m[1][0];

	m1[2][0]=m[1][0]*m[2][1]-m[1][1]*m[2][0];
	m1[2][1]= -m[0][0]*m[2][1]+m[0][1]*m[2][0];
	m1[2][2]=m[0][0]*m[1][1]-m[0][1]*m[1][0];
}

void Mat4MulMat4(float m1[][4], float m2[][4], float m3[][4])
{
  /* matrix product: m1[j][k] = m2[j][i].m3[i][k] */

	m1[0][0] = m2[0][0]*m3[0][0] + m2[0][1]*m3[1][0] + m2[0][2]*m3[2][0] + m2[0][3]*m3[3][0];
	m1[0][1] = m2[0][0]*m3[0][1] + m2[0][1]*m3[1][1] + m2[0][2]*m3[2][1] + m2[0][3]*m3[3][1];
	m1[0][2] = m2[0][0]*m3[0][2] + m2[0][1]*m3[1][2] + m2[0][2]*m3[2][2] + m2[0][3]*m3[3][2];
	m1[0][3] = m2[0][0]*m3[0][3] + m2[0][1]*m3[1][3] + m2[0][2]*m3[2][3] + m2[0][3]*m3[3][3];

	m1[1][0] = m2[1][0]*m3[0][0] + m2[1][1]*m3[1][0] + m2[1][2]*m3[2][0] + m2[1][3]*m3[3][0];
	m1[1][1] = m2[1][0]*m3[0][1] + m2[1][1]*m3[1][1] + m2[1][2]*m3[2][1] + m2[1][3]*m3[3][1];
	m1[1][2] = m2[1][0]*m3[0][2] + m2[1][1]*m3[1][2] + m2[1][2]*m3[2][2] + m2[1][3]*m3[3][2];
	m1[1][3] = m2[1][0]*m3[0][3] + m2[1][1]*m3[1][3] + m2[1][2]*m3[2][3] + m2[1][3]*m3[3][3];

	m1[2][0] = m2[2][0]*m3[0][0] + m2[2][1]*m3[1][0] + m2[2][2]*m3[2][0] + m2[2][3]*m3[3][0];
	m1[2][1] = m2[2][0]*m3[0][1] + m2[2][1]*m3[1][1] + m2[2][2]*m3[2][1] + m2[2][3]*m3[3][1];
	m1[2][2] = m2[2][0]*m3[0][2] + m2[2][1]*m3[1][2] + m2[2][2]*m3[2][2] + m2[2][3]*m3[3][2];
	m1[2][3] = m2[2][0]*m3[0][3] + m2[2][1]*m3[1][3] + m2[2][2]*m3[2][3] + m2[2][3]*m3[3][3];

	m1[3][0] = m2[3][0]*m3[0][0] + m2[3][1]*m3[1][0] + m2[3][2]*m3[2][0] + m2[3][3]*m3[3][0];
	m1[3][1] = m2[3][0]*m3[0][1] + m2[3][1]*m3[1][1] + m2[3][2]*m3[2][1] + m2[3][3]*m3[3][1];
	m1[3][2] = m2[3][0]*m3[0][2] + m2[3][1]*m3[1][2] + m2[3][2]*m3[2][2] + m2[3][3]*m3[3][2];
	m1[3][3] = m2[3][0]*m3[0][3] + m2[3][1]*m3[1][3] + m2[3][2]*m3[2][3] + m2[3][3]*m3[3][3];

}
#ifdef TEST_ACTIVE
void subMat4MulMat4(float *m1, float *m2, float *m3)
{

	m1[0]= m2[0]*m3[0] + m2[1]*m3[4] + m2[2]*m3[8];
	m1[1]= m2[0]*m3[1] + m2[1]*m3[5] + m2[2]*m3[9];
	m1[2]= m2[0]*m3[2] + m2[1]*m3[6] + m2[2]*m3[10];
	m1[3]= m2[0]*m3[3] + m2[1]*m3[7] + m2[2]*m3[11] + m2[3];
	m1+=4;
	m2+=4;
	m1[0]= m2[0]*m3[0] + m2[1]*m3[4] + m2[2]*m3[8];
	m1[1]= m2[0]*m3[1] + m2[1]*m3[5] + m2[2]*m3[9];
	m1[2]= m2[0]*m3[2] + m2[1]*m3[6] + m2[2]*m3[10];
	m1[3]= m2[0]*m3[3] + m2[1]*m3[7] + m2[2]*m3[11] + m2[3];
	m1+=4;
	m2+=4;
	m1[0]= m2[0]*m3[0] + m2[1]*m3[4] + m2[2]*m3[8];
	m1[1]= m2[0]*m3[1] + m2[1]*m3[5] + m2[2]*m3[9];
	m1[2]= m2[0]*m3[2] + m2[1]*m3[6] + m2[2]*m3[10];
	m1[3]= m2[0]*m3[3] + m2[1]*m3[7] + m2[2]*m3[11] + m2[3];
}
#endif

#ifndef TEST_ACTIVE
void Mat3MulMat3(float m1[][3], float m3[][3], float m2[][3])
#else
void Mat3MulMat3(float *m1, float *m3, float *m2)
#endif
{
   /*  m1[i][j] = m2[i][k]*m3[k][j], args are flipped!  */
#ifndef TEST_ACTIVE
  	m1[0][0]= m2[0][0]*m3[0][0] + m2[0][1]*m3[1][0] + m2[0][2]*m3[2][0]; 
  	m1[0][1]= m2[0][0]*m3[0][1] + m2[0][1]*m3[1][1] + m2[0][2]*m3[2][1]; 
  	m1[0][2]= m2[0][0]*m3[0][2] + m2[0][1]*m3[1][2] + m2[0][2]*m3[2][2]; 

  	m1[1][0]= m2[1][0]*m3[0][0] + m2[1][1]*m3[1][0] + m2[1][2]*m3[2][0]; 
  	m1[1][1]= m2[1][0]*m3[0][1] + m2[1][1]*m3[1][1] + m2[1][2]*m3[2][1]; 
  	m1[1][2]= m2[1][0]*m3[0][2] + m2[1][1]*m3[1][2] + m2[1][2]*m3[2][2]; 

  	m1[2][0]= m2[2][0]*m3[0][0] + m2[2][1]*m3[1][0] + m2[2][2]*m3[2][0]; 
  	m1[2][1]= m2[2][0]*m3[0][1] + m2[2][1]*m3[1][1] + m2[2][2]*m3[2][1]; 
  	m1[2][2]= m2[2][0]*m3[0][2] + m2[2][1]*m3[1][2] + m2[2][2]*m3[2][2]; 
#else
	m1[0]= m2[0]*m3[0] + m2[1]*m3[3] + m2[2]*m3[6];
	m1[1]= m2[0]*m3[1] + m2[1]*m3[4] + m2[2]*m3[7];
	m1[2]= m2[0]*m3[2] + m2[1]*m3[5] + m2[2]*m3[8];
	m1+=3;
	m2+=3;
	m1[0]= m2[0]*m3[0] + m2[1]*m3[3] + m2[2]*m3[6];
	m1[1]= m2[0]*m3[1] + m2[1]*m3[4] + m2[2]*m3[7];
	m1[2]= m2[0]*m3[2] + m2[1]*m3[5] + m2[2]*m3[8];
	m1+=3;
	m2+=3;
	m1[0]= m2[0]*m3[0] + m2[1]*m3[3] + m2[2]*m3[6];
	m1[1]= m2[0]*m3[1] + m2[1]*m3[4] + m2[2]*m3[7];
	m1[2]= m2[0]*m3[2] + m2[1]*m3[5] + m2[2]*m3[8];
#endif
} /* end of void Mat3MulMat3(float m1[][3], float m3[][3], float m2[][3]) */

void Mat4MulMat43(float (*m1)[4], float (*m3)[4], float (*m2)[3])
{
	m1[0][0]= m2[0][0]*m3[0][0] + m2[0][1]*m3[1][0] + m2[0][2]*m3[2][0];
	m1[0][1]= m2[0][0]*m3[0][1] + m2[0][1]*m3[1][1] + m2[0][2]*m3[2][1];
	m1[0][2]= m2[0][0]*m3[0][2] + m2[0][1]*m3[1][2] + m2[0][2]*m3[2][2];
	m1[1][0]= m2[1][0]*m3[0][0] + m2[1][1]*m3[1][0] + m2[1][2]*m3[2][0];
	m1[1][1]= m2[1][0]*m3[0][1] + m2[1][1]*m3[1][1] + m2[1][2]*m3[2][1];
	m1[1][2]= m2[1][0]*m3[0][2] + m2[1][1]*m3[1][2] + m2[1][2]*m3[2][2];
	m1[2][0]= m2[2][0]*m3[0][0] + m2[2][1]*m3[1][0] + m2[2][2]*m3[2][0];
	m1[2][1]= m2[2][0]*m3[0][1] + m2[2][1]*m3[1][1] + m2[2][2]*m3[2][1];
	m1[2][2]= m2[2][0]*m3[0][2] + m2[2][1]*m3[1][2] + m2[2][2]*m3[2][2];
}
/* m1 = m2 * m3, ignore the elements on the 4th row/column of m3*/
void Mat3IsMat3MulMat4(float m1[][3], float m2[][3], float m3[][4])
{
    /* m1[i][j] = m2[i][k] * m3[k][j] */
    m1[0][0] = m2[0][0] * m3[0][0] + m2[0][1] * m3[1][0] +m2[0][2] * m3[2][0];
    m1[0][1] = m2[0][0] * m3[0][1] + m2[0][1] * m3[1][1] +m2[0][2] * m3[2][1];
    m1[0][2] = m2[0][0] * m3[0][2] + m2[0][1] * m3[1][2] +m2[0][2] * m3[2][2];

    m1[1][0] = m2[1][0] * m3[0][0] + m2[1][1] * m3[1][0] +m2[1][2] * m3[2][0];
    m1[1][1] = m2[1][0] * m3[0][1] + m2[1][1] * m3[1][1] +m2[1][2] * m3[2][1];
    m1[1][2] = m2[1][0] * m3[0][2] + m2[1][1] * m3[1][2] +m2[1][2] * m3[2][2];

    m1[2][0] = m2[2][0] * m3[0][0] + m2[2][1] * m3[1][0] +m2[2][2] * m3[2][0];
    m1[2][1] = m2[2][0] * m3[0][1] + m2[2][1] * m3[1][1] +m2[2][2] * m3[2][1];
    m1[2][2] = m2[2][0] * m3[0][2] + m2[2][1] * m3[1][2] +m2[2][2] * m3[2][2];
}



void Mat4MulMat34(float (*m1)[4], float (*m3)[3], float (*m2)[4])
{
	m1[0][0]= m2[0][0]*m3[0][0] + m2[0][1]*m3[1][0] + m2[0][2]*m3[2][0];
	m1[0][1]= m2[0][0]*m3[0][1] + m2[0][1]*m3[1][1] + m2[0][2]*m3[2][1];
	m1[0][2]= m2[0][0]*m3[0][2] + m2[0][1]*m3[1][2] + m2[0][2]*m3[2][2];
	m1[1][0]= m2[1][0]*m3[0][0] + m2[1][1]*m3[1][0] + m2[1][2]*m3[2][0];
	m1[1][1]= m2[1][0]*m3[0][1] + m2[1][1]*m3[1][1] + m2[1][2]*m3[2][1];
	m1[1][2]= m2[1][0]*m3[0][2] + m2[1][1]*m3[1][2] + m2[1][2]*m3[2][2];
	m1[2][0]= m2[2][0]*m3[0][0] + m2[2][1]*m3[1][0] + m2[2][2]*m3[2][0];
	m1[2][1]= m2[2][0]*m3[0][1] + m2[2][1]*m3[1][1] + m2[2][2]*m3[2][1];
	m1[2][2]= m2[2][0]*m3[0][2] + m2[2][1]*m3[1][2] + m2[2][2]*m3[2][2];
}

void Mat4CpyMat4(float m1[][4], float m2[][4]) 
{
	memcpy(m1, m2, 4*4*sizeof(float));
}

void Mat4SwapMat4(float *m1, float *m2)
{
	float t;
	int i;

	for(i=0;i<16;i++) {
		t= *m1;
		*m1= *m2;
		*m2= t;
		m1++; 
		m2++;
	}
}

typedef float Mat3Row[3];
typedef float Mat4Row[4];

#ifdef TEST_ACTIVE
void Mat3CpyMat4(float *m1p, float *m2p)
#else
void Mat3CpyMat4(float m1[][3], float m2[][4])
#endif
{
#ifdef TEST_ACTIVE
	int i, j;
  	Mat3Row *m1= (Mat3Row *)m1p; 
  	Mat4Row *m2= (Mat4Row *)m2p; 
	for ( i = 0; i++; i < 3) {
		for (j = 0; j++; j < 3) {
			m1p[3*i + j] = m2p[4*i + j];
		}
	}	 		
#endif
	m1[0][0]= m2[0][0];
	m1[0][1]= m2[0][1];
	m1[0][2]= m2[0][2];

	m1[1][0]= m2[1][0];
	m1[1][1]= m2[1][1];
	m1[1][2]= m2[1][2];

	m1[2][0]= m2[2][0];
	m1[2][1]= m2[2][1];
	m1[2][2]= m2[2][2];
}

/* Butched. See .h for comment */
/*  void Mat4CpyMat3(float m1[][4], float m2[][3]) */
#ifdef TEST_ACTIVE
void Mat4CpyMat3(float* m1, float *m2)
{
	int i;
	for (i = 0; i < 3; i++) {
		m1[(4*i)]    = m2[(3*i)];
		m1[(4*i) + 1]= m2[(3*i) + 1];
		m1[(4*i) + 2]= m2[(3*i) + 2];
		m1[(4*i) + 3]= 0.0;
		i++;
	}

	m1[12]=m1[13]= m1[14]= 0.0;
	m1[15]= 1.0;
}
#else

void Mat4CpyMat3(float m1[][4], float m2[][3])	/* no clear */
{
	m1[0][0]= m2[0][0];
	m1[0][1]= m2[0][1];
	m1[0][2]= m2[0][2];

	m1[1][0]= m2[1][0];
	m1[1][1]= m2[1][1];
	m1[1][2]= m2[1][2];

	m1[2][0]= m2[2][0];
	m1[2][1]= m2[2][1];
	m1[2][2]= m2[2][2];

	/*	Reevan's Bugfix */
	m1[0][3]=0.0F;
	m1[1][3]=0.0F;
	m1[2][3]=0.0F;

	m1[3][0]=0.0F;	
	m1[3][1]=0.0F;	
	m1[3][2]=0.0F;	
	m1[3][3]=1.0F;


}
#endif

void Mat3CpyMat3(float m1[][3], float m2[][3]) 
{	
	/* destination comes first: */
	memcpy(&m1[0], &m2[0], 9*sizeof(float));
}

void Mat3MulSerie(float answ[][3],
				   float m1[][3], float m2[][3], float m3[][3],
				   float m4[][3], float m5[][3], float m6[][3],
				   float m7[][3], float m8[][3])
{
	float temp[3][3];
	
	if(m1==0 || m2==0) return;

	
	Mat3MulMat3(answ, m2, m1);
	if(m3) {
		Mat3MulMat3(temp, m3, answ);
		if(m4) {
			Mat3MulMat3(answ, m4, temp);
			if(m5) {
				Mat3MulMat3(temp, m5, answ);
				if(m6) {
					Mat3MulMat3(answ, m6, temp);
					if(m7) {
						Mat3MulMat3(temp, m7, answ);
						if(m8) {
							Mat3MulMat3(answ, m8, temp);
						}
						else Mat3CpyMat3(answ, temp);
					}
				}
				else Mat3CpyMat3(answ, temp);
			}
		}
		else Mat3CpyMat3(answ, temp);
	}
}

void Mat4MulSerie(float answ[][4], float m1[][4],
				float m2[][4], float m3[][4], float m4[][4],
				float m5[][4], float m6[][4], float m7[][4],
				float m8[][4])
{
	float temp[4][4];
	
	if(m1==0 || m2==0) return;
	
	Mat4MulMat4(answ, m2, m1);
	if(m3) {
		Mat4MulMat4(temp, m3, answ);
		if(m4) {
			Mat4MulMat4(answ, m4, temp);
			if(m5) {
				Mat4MulMat4(temp, m5, answ);
				if(m6) {
					Mat4MulMat4(answ, m6, temp);
					if(m7) {
						Mat4MulMat4(temp, m7, answ);
						if(m8) {
							Mat4MulMat4(answ, m8, temp);
						}
						else Mat4CpyMat4(answ, temp);
					}
				}
				else Mat4CpyMat4(answ, temp);
			}
		}
		else Mat4CpyMat4(answ, temp);
	}
}

void Mat4BlendMat4(float out[][4], float dst[][4], float src[][4], float srcweight)
{
	float squat[4], dquat[4], fquat[4];
	float ssize[3], dsize[3], fsize[4];
	float sloc[3], dloc[3], floc[3];
	
	Mat4ToQuat(dst, dquat);
	Mat4ToSize(dst, dsize);
	VecCopyf(dloc, dst[3]);

	Mat4ToQuat(src, squat);
	Mat4ToSize(src, ssize);
	VecCopyf(sloc, src[3]);
	
	/* do blending */
	VecLerpf(floc, dloc, sloc, srcweight);
	QuatInterpol(fquat, dquat, squat, srcweight);
	VecLerpf(fsize, dsize, ssize, srcweight);

	/* compose new matrix */
	LocQuatSizeToMat4(out, floc, fquat, fsize);
}

void Mat4Clr(float *m)
{
	memset(m, 0, 4*4*sizeof(float));
}

void Mat3Clr(float *m)
{
	memset(m, 0, 3*3*sizeof(float));
}

void Mat4One(float m[][4])
{

	m[0][0]= m[1][1]= m[2][2]= m[3][3]= 1.0;
	m[0][1]= m[0][2]= m[0][3]= 0.0;
	m[1][0]= m[1][2]= m[1][3]= 0.0;
	m[2][0]= m[2][1]= m[2][3]= 0.0;
	m[3][0]= m[3][1]= m[3][2]= 0.0;
}

void Mat3One(float m[][3])
{

	m[0][0]= m[1][1]= m[2][2]= 1.0;
	m[0][1]= m[0][2]= 0.0;
	m[1][0]= m[1][2]= 0.0;
	m[2][0]= m[2][1]= 0.0;
}

void Mat4MulVec( float mat[][4], int *vec)
{
	int x,y;

	x=vec[0]; 
	y=vec[1];
	vec[0]=(int)(x*mat[0][0] + y*mat[1][0] + mat[2][0]*vec[2] + mat[3][0]);
	vec[1]=(int)(x*mat[0][1] + y*mat[1][1] + mat[2][1]*vec[2] + mat[3][1]);
	vec[2]=(int)(x*mat[0][2] + y*mat[1][2] + mat[2][2]*vec[2] + mat[3][2]);
}

void Mat4MulVecfl( float mat[][4], float *vec)
{
	float x,y;

	x=vec[0]; 
	y=vec[1];
	vec[0]=x*mat[0][0] + y*mat[1][0] + mat[2][0]*vec[2] + mat[3][0];
	vec[1]=x*mat[0][1] + y*mat[1][1] + mat[2][1]*vec[2] + mat[3][1];
	vec[2]=x*mat[0][2] + y*mat[1][2] + mat[2][2]*vec[2] + mat[3][2];
}

void VecMat4MulVecfl(float *in, float mat[][4], float *vec)
{
	float x,y;

	x=vec[0]; 
	y=vec[1];
	in[0]= x*mat[0][0] + y*mat[1][0] + mat[2][0]*vec[2] + mat[3][0];
	in[1]= x*mat[0][1] + y*mat[1][1] + mat[2][1]*vec[2] + mat[3][1];
	in[2]= x*mat[0][2] + y*mat[1][2] + mat[2][2]*vec[2] + mat[3][2];
}

void Mat4Mul3Vecfl( float mat[][4], float *vec)
{
	float x,y;

	x= vec[0]; 
	y= vec[1];
	vec[0]= x*mat[0][0] + y*mat[1][0] + mat[2][0]*vec[2];
	vec[1]= x*mat[0][1] + y*mat[1][1] + mat[2][1]*vec[2];
	vec[2]= x*mat[0][2] + y*mat[1][2] + mat[2][2]*vec[2];
}

void Mat4MulVec3Project(float mat[][4], float *vec)
{
	float w;

	w = vec[0]*mat[0][3] + vec[1]*mat[1][3] + vec[2]*mat[2][3] + mat[3][3];
	Mat4MulVecfl(mat, vec);

	vec[0] /= w;
	vec[1] /= w;
	vec[2] /= w;
}

void Mat4MulVec4fl( float mat[][4], float *vec)
{
	float x,y,z;

	x=vec[0]; 
	y=vec[1]; 
	z= vec[2];
	vec[0]=x*mat[0][0] + y*mat[1][0] + z*mat[2][0] + mat[3][0]*vec[3];
	vec[1]=x*mat[0][1] + y*mat[1][1] + z*mat[2][1] + mat[3][1]*vec[3];
	vec[2]=x*mat[0][2] + y*mat[1][2] + z*mat[2][2] + mat[3][2]*vec[3];
	vec[3]=x*mat[0][3] + y*mat[1][3] + z*mat[2][3] + mat[3][3]*vec[3];
}

void Mat3MulVec( float mat[][3], int *vec)
{
	int x,y;

	x=vec[0]; 
	y=vec[1];
	vec[0]= (int)(x*mat[0][0] + y*mat[1][0] + mat[2][0]*vec[2]);
	vec[1]= (int)(x*mat[0][1] + y*mat[1][1] + mat[2][1]*vec[2]);
	vec[2]= (int)(x*mat[0][2] + y*mat[1][2] + mat[2][2]*vec[2]);
}

void Mat3MulVecfl( float mat[][3], float *vec)
{
	float x,y;

	x=vec[0]; 
	y=vec[1];
	vec[0]= x*mat[0][0] + y*mat[1][0] + mat[2][0]*vec[2];
	vec[1]= x*mat[0][1] + y*mat[1][1] + mat[2][1]*vec[2];
	vec[2]= x*mat[0][2] + y*mat[1][2] + mat[2][2]*vec[2];
}

void Mat3MulVecd( float mat[][3], double *vec)
{
	double x,y;

	x=vec[0]; 
	y=vec[1];
	vec[0]= x*mat[0][0] + y*mat[1][0] + mat[2][0]*vec[2];
	vec[1]= x*mat[0][1] + y*mat[1][1] + mat[2][1]*vec[2];
	vec[2]= x*mat[0][2] + y*mat[1][2] + mat[2][2]*vec[2];
}

void Mat3TransMulVecfl( float mat[][3], float *vec)
{
	float x,y;

	x=vec[0]; 
	y=vec[1];
	vec[0]= x*mat[0][0] + y*mat[0][1] + mat[0][2]*vec[2];
	vec[1]= x*mat[1][0] + y*mat[1][1] + mat[1][2]*vec[2];
	vec[2]= x*mat[2][0] + y*mat[2][1] + mat[2][2]*vec[2];
}

void Mat3MulFloat(float *m, float f)
{
	int i;

	for(i=0;i<9;i++) m[i]*=f;
}

void Mat4MulFloat(float *m, float f)
{
	int i;

	for(i=0;i<12;i++) m[i]*=f;	/* count to 12: without vector component */
}


void Mat4MulFloat3(float *m, float f)		/* only scale component */
{
	int i,j;

	for(i=0; i<3; i++) {
		for(j=0; j<3; j++) {
			
			m[4*i+j] *= f;
		}
	}
}

void Mat3AddMat3(float m1[][3], float m2[][3], float m3[][3])
{
	int i, j;

	for(i=0;i<3;i++)
		for(j=0;j<3;j++)
			m1[i][j]= m2[i][j] + m3[i][j];
}

void Mat4AddMat4(float m1[][4], float m2[][4], float m3[][4])
{
	int i, j;

	for(i=0;i<4;i++)
		for(j=0;j<4;j++)
			m1[i][j]= m2[i][j] + m3[i][j];
}

void VecStar(float mat[][3], float *vec)
{

	mat[0][0]= mat[1][1]= mat[2][2]= 0.0;
	mat[0][1]= -vec[2];	
	mat[0][2]= vec[1];
	mat[1][0]= vec[2];	
	mat[1][2]= -vec[0];
	mat[2][0]= -vec[1];	
	mat[2][1]= vec[0];
	
}
#ifdef TEST_ACTIVE
short EenheidsMat(float mat[][3])
{

	if(mat[0][0]==1.0 && mat[0][1]==0.0 && mat[0][2]==0.0)
		if(mat[1][0]==0.0 && mat[1][1]==1.0 && mat[1][2]==0.0)
			if(mat[2][0]==0.0 && mat[2][1]==0.0 && mat[2][2]==1.0)
				return 1;
	return 0;
}
#endif

int FloatCompare( float *v1,  float *v2, float limit)
{

	if( fabs(v1[0]-v2[0])<limit ) {
		if( fabs(v1[1]-v2[1])<limit ) {
			if( fabs(v1[2]-v2[2])<limit ) return 1;
		}
	}
	return 0;
}

float FloatLerpf( float target, float origin, float fac)
{
	return (fac*target) + (1.0f-fac)*origin;
}

void printvecf( char *str,  float v[3])
{
	printf("%s: %.3f %.3f %.3f\n", str, v[0], v[1], v[2]);

}

void printquat( char *str,  float q[4])
{
	printf("%s: %.3f %.3f %.3f %.3f\n", str, q[0], q[1], q[2], q[3]);

}

void printvec4f( char *str,  float v[4])
{
	printf("%s\n", str);
	printf("%f %f %f %f\n",v[0],v[1],v[2], v[3]);
	printf("\n");

}

void printmatrix4( char *str,  float m[][4])
{
	printf("%s\n", str);
	printf("%f %f %f %f\n",m[0][0],m[1][0],m[2][0],m[3][0]);
	printf("%f %f %f %f\n",m[0][1],m[1][1],m[2][1],m[3][1]);
	printf("%f %f %f %f\n",m[0][2],m[1][2],m[2][2],m[3][2]);
	printf("%f %f %f %f\n",m[0][3],m[1][3],m[2][3],m[3][3]);
	printf("\n");

}

void printmatrix3( char *str,  float m[][3])
{
	printf("%s\n", str);
	printf("%f %f %f\n",m[0][0],m[1][0],m[2][0]);
	printf("%f %f %f\n",m[0][1],m[1][1],m[2][1]);
	printf("%f %f %f\n",m[0][2],m[1][2],m[2][2]);
	printf("\n");

}

/* **************** QUATERNIONS ********** */


void QuatMul(float *q, float *q1, float *q2)
{
	float t0,t1,t2;

	t0=   q1[0]*q2[0]-q1[1]*q2[1]-q1[2]*q2[2]-q1[3]*q2[3];
	t1=   q1[0]*q2[1]+q1[1]*q2[0]+q1[2]*q2[3]-q1[3]*q2[2];
	t2=   q1[0]*q2[2]+q1[2]*q2[0]+q1[3]*q2[1]-q1[1]*q2[3];
	q[3]= q1[0]*q2[3]+q1[3]*q2[0]+q1[1]*q2[2]-q1[2]*q2[1];
	q[0]=t0; 
	q[1]=t1; 
	q[2]=t2;
}

/* Assumes a unit quaternion */
void QuatMulVecf(float *q, float *v)
{
	float t0, t1, t2;

	t0=  -q[1]*v[0]-q[2]*v[1]-q[3]*v[2];
	t1=   q[0]*v[0]+q[2]*v[2]-q[3]*v[1];
	t2=   q[0]*v[1]+q[3]*v[0]-q[1]*v[2];
	v[2]= q[0]*v[2]+q[1]*v[1]-q[2]*v[0];
	v[0]=t1; 
	v[1]=t2;

	t1=   t0*-q[1]+v[0]*q[0]-v[1]*q[3]+v[2]*q[2];
	t2=   t0*-q[2]+v[1]*q[0]-v[2]*q[1]+v[0]*q[3];
	v[2]= t0*-q[3]+v[2]*q[0]-v[0]*q[2]+v[1]*q[1];
	v[0]=t1; 
	v[1]=t2;
}

void QuatConj(float *q)
{
	q[1] = -q[1];
	q[2] = -q[2];
	q[3] = -q[3];
}

float QuatDot(float *q1, float *q2)
{
	return q1[0]*q2[0] + q1[1]*q2[1] + q1[2]*q2[2] + q1[3]*q2[3];
}

void QuatInv(float *q)
{
	float f = QuatDot(q, q);

	if (f == 0.0f)
		return;

	QuatConj(q);
	QuatMulf(q, 1.0f/f);
}

void QuatMulf(float *q, float f)
{
	q[0] *= f;
	q[1] *= f;
	q[2] *= f;
	q[3] *= f;
}

void QuatSub(float *q, float *q1, float *q2)
{
	q2[0]= -q2[0];
	QuatMul(q, q1, q2);
	q2[0]= -q2[0];
}


void QuatToMat3( float *q, float m[][3])
{
	double q0, q1, q2, q3, qda,qdb,qdc,qaa,qab,qac,qbb,qbc,qcc;

	q0= M_SQRT2 * q[0];
	q1= M_SQRT2 * q[1];
	q2= M_SQRT2 * q[2];
	q3= M_SQRT2 * q[3];

	qda= q0*q1;
	qdb= q0*q2;
	qdc= q0*q3;
	qaa= q1*q1;
	qab= q1*q2;
	qac= q1*q3;
	qbb= q2*q2;
	qbc= q2*q3;
	qcc= q3*q3;

	m[0][0]= (float)(1.0-qbb-qcc);
	m[0][1]= (float)(qdc+qab);
	m[0][2]= (float)(-qdb+qac);

	m[1][0]= (float)(-qdc+qab);
	m[1][1]= (float)(1.0-qaa-qcc);
	m[1][2]= (float)(qda+qbc);

	m[2][0]= (float)(qdb+qac);
	m[2][1]= (float)(-qda+qbc);
	m[2][2]= (float)(1.0-qaa-qbb);
}


void QuatToMat4( float *q, float m[][4])
{
	double q0, q1, q2, q3, qda,qdb,qdc,qaa,qab,qac,qbb,qbc,qcc;

	q0= M_SQRT2 * q[0];
	q1= M_SQRT2 * q[1];
	q2= M_SQRT2 * q[2];
	q3= M_SQRT2 * q[3];

	qda= q0*q1;
	qdb= q0*q2;
	qdc= q0*q3;
	qaa= q1*q1;
	qab= q1*q2;
	qac= q1*q3;
	qbb= q2*q2;
	qbc= q2*q3;
	qcc= q3*q3;

	m[0][0]= (float)(1.0-qbb-qcc);
	m[0][1]= (float)(qdc+qab);
	m[0][2]= (float)(-qdb+qac);
	m[0][3]= 0.0f;

	m[1][0]= (float)(-qdc+qab);
	m[1][1]= (float)(1.0-qaa-qcc);
	m[1][2]= (float)(qda+qbc);
	m[1][3]= 0.0f;

	m[2][0]= (float)(qdb+qac);
	m[2][1]= (float)(-qda+qbc);
	m[2][2]= (float)(1.0-qaa-qbb);
	m[2][3]= 0.0f;
	
	m[3][0]= m[3][1]= m[3][2]= 0.0f;
	m[3][3]= 1.0f;
}

void Mat3ToQuat( float wmat[][3], float *q)		/* from Sig.Proc.85 pag 253 */
{
	double tr, s;
	float mat[3][3];

	/* work on a copy */
	Mat3CpyMat3(mat, wmat);
	Mat3Ortho(mat);			/* this is needed AND a NormalQuat in the end */
	
	tr= 0.25*(1.0+mat[0][0]+mat[1][1]+mat[2][2]);
	
	if(tr>FLT_EPSILON) {
		s= sqrt( tr);
		q[0]= (float)s;
		s*= 4.0;
		q[1]= (float)((mat[1][2]-mat[2][1])/s);
		q[2]= (float)((mat[2][0]-mat[0][2])/s);
		q[3]= (float)((mat[0][1]-mat[1][0])/s);
	}
	else {
		q[0]= 0.0f;
		s= -0.5*(mat[1][1]+mat[2][2]);
		
		if(s>FLT_EPSILON) {
			s= sqrt(s);
			q[1]= (float)s;
			q[2]= (float)(mat[0][1]/(2*s));
			q[3]= (float)(mat[0][2]/(2*s));
		}
		else {
			q[1]= 0.0f;
			s= 0.5*(1.0-mat[2][2]);
			
			if(s>FLT_EPSILON) {
				s= sqrt(s);
				q[2]= (float)s;
				q[3]= (float)(mat[1][2]/(2*s));
			}
			else {
				q[2]= 0.0f;
				q[3]= 1.0f;
			}
		}
	}
	NormalQuat(q);
}

void Mat3ToQuat_is_ok( float wmat[][3], float *q)
{
	float mat[3][3], matr[3][3], matn[3][3], q1[4], q2[4], angle, si, co, nor[3];

	/* work on a copy */
	Mat3CpyMat3(mat, wmat);
	Mat3Ortho(mat);
	
	/* rotate z-axis of matrix to z-axis */

	nor[0] = mat[2][1];		/* cross product with (0,0,1) */
	nor[1] =  -mat[2][0];
	nor[2] = 0.0;
	Normalize(nor);
	
	co= mat[2][2];
	angle= 0.5f*saacos(co);
	
	co= (float)cos(angle);
	si= (float)sin(angle);
	q1[0]= co;
	q1[1]= -nor[0]*si;		/* negative here, but why? */
	q1[2]= -nor[1]*si;
	q1[3]= -nor[2]*si;

	/* rotate back x-axis from mat, using inverse q1 */
	QuatToMat3(q1, matr);
	Mat3Inv(matn, matr);
	Mat3MulVecfl(matn, mat[0]);
	
	/* and align x-axes */
	angle= (float)(0.5*atan2(mat[0][1], mat[0][0]));
	
	co= (float)cos(angle);
	si= (float)sin(angle);
	q2[0]= co;
	q2[1]= 0.0f;
	q2[2]= 0.0f;
	q2[3]= si;
	
	QuatMul(q, q1, q2);
}


void Mat4ToQuat( float m[][4], float *q)
{
	float mat[3][3];
	
	Mat3CpyMat4(mat, m);
	Mat3ToQuat(mat, q);
	
}

void QuatOne(float *q)
{
	q[0]= q[2]= q[3]= 0.0;
	q[1]= 1.0;
}

void NormalQuat(float *q)
{
	float len;
	
	len= (float)sqrt(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);
	if(len!=0.0) {
		q[0]/= len;
		q[1]/= len;
		q[2]/= len;
		q[3]/= len;
	} else {
		q[1]= 1.0f;
		q[0]= q[2]= q[3]= 0.0f;			
	}
}

float *vectoquat( float *vec, short axis, short upflag)
{
	static float q1[4];
	float q2[4], nor[3], *fp, mat[3][3], angle, si, co, x2, y2, z2, len1;
	
	/* first rotate to axis */
	if(axis>2) {	
		x2= vec[0] ; y2= vec[1] ; z2= vec[2];
		axis-= 3;
	}
	else {
		x2= -vec[0] ; y2= -vec[1] ; z2= -vec[2];
	}
	
	q1[0]=1.0; 
	q1[1]=q1[2]=q1[3]= 0.0;

	len1= (float)sqrt(x2*x2+y2*y2+z2*z2);
	if(len1 == 0.0) return(q1);

	/* nasty! I need a good routine for this...
	 * problem is a rotation of an Y axis to the negative Y-axis for example.
	 */

	if(axis==0) {	/* x-axis */
		nor[0]= 0.0;
		nor[1]= -z2;
		nor[2]= y2;

		if( fabs(y2)+fabs(z2)<0.0001 ) {
			nor[1]= 1.0;
		}

		co= x2;
	}
	else if(axis==1) {	/* y-axis */
		nor[0]= z2;
		nor[1]= 0.0;
		nor[2]= -x2;
		
		if( fabs(x2)+fabs(z2)<0.0001 ) {
			nor[2]= 1.0;
		}
		
		co= y2;
	}
	else {			/* z-axis */
		nor[0]= -y2;
		nor[1]= x2;
		nor[2]= 0.0;

		if( fabs(x2)+fabs(y2)<0.0001 ) {
			nor[0]= 1.0;
		}

		co= z2;
	}
	co/= len1;

	Normalize(nor);
	
	angle= 0.5f*saacos(co);
	si= (float)sin(angle);
	q1[0]= (float)cos(angle);
	q1[1]= nor[0]*si;
	q1[2]= nor[1]*si;
	q1[3]= nor[2]*si;
	
	if(axis!=upflag) {
		QuatToMat3(q1, mat);

		fp= mat[2];
		if(axis==0) {
			if(upflag==1) angle= (float)(0.5*atan2(fp[2], fp[1]));
			else angle= (float)(-0.5*atan2(fp[1], fp[2]));
		}
		else if(axis==1) {
			if(upflag==0) angle= (float)(-0.5*atan2(fp[2], fp[0]));
			else angle= (float)(0.5*atan2(fp[0], fp[2]));
		}
		else {
			if(upflag==0) angle= (float)(0.5*atan2(-fp[1], -fp[0]));
			else angle= (float)(-0.5*atan2(-fp[0], -fp[1]));
		}
				
		co= (float)cos(angle);
		si= (float)(sin(angle)/len1);
		q2[0]= co;
		q2[1]= x2*si;
		q2[2]= y2*si;
		q2[3]= z2*si;
			
		QuatMul(q1,q2,q1);
	}

	return(q1);
}

void VecUpMat3old( float *vec, float mat[][3], short axis)
{
	float inp, up[3];
	short cox = 0, coy = 0, coz = 0;
	
	/* using different up's is not useful, infact there is no real 'up'!
	 */

	up[0]= 0.0;
	up[1]= 0.0;
	up[2]= 1.0;

	if(axis==0) {
		cox= 0; coy= 1; coz= 2;		/* Y up Z tr */
	}
	if(axis==1) {
		cox= 1; coy= 2; coz= 0;		/* Z up X tr */
	}
	if(axis==2) {
		cox= 2; coy= 0; coz= 1;		/* X up Y tr */
	}
	if(axis==3) {
		cox= 0; coy= 2; coz= 1;		/*  */
	}
	if(axis==4) {
		cox= 1; coy= 0; coz= 2;		/*  */
	}
	if(axis==5) {
		cox= 2; coy= 1; coz= 0;		/* Y up X tr */
	}

	mat[coz][0]= vec[0];
	mat[coz][1]= vec[1];
	mat[coz][2]= vec[2];
	Normalize((float *)mat[coz]);
	
	inp= mat[coz][0]*up[0] + mat[coz][1]*up[1] + mat[coz][2]*up[2];
	mat[coy][0]= up[0] - inp*mat[coz][0];
	mat[coy][1]= up[1] - inp*mat[coz][1];
	mat[coy][2]= up[2] - inp*mat[coz][2];

	Normalize((float *)mat[coy]);
	
	Crossf(mat[cox], mat[coy], mat[coz]);
	
}

void VecUpMat3(float *vec, float mat[][3], short axis)
{
	float inp;
	short cox = 0, coy = 0, coz = 0;

	/* using different up's is not useful, infact there is no real 'up'!
	*/

	if(axis==0) {
		cox= 0; coy= 1; coz= 2;		/* Y up Z tr */
	}
	if(axis==1) {
		cox= 1; coy= 2; coz= 0;		/* Z up X tr */
	}
	if(axis==2) {
		cox= 2; coy= 0; coz= 1;		/* X up Y tr */
	}
	if(axis==3) {
		cox= 0; coy= 1; coz= 2;		/* Y op -Z tr */
		vec[0]= -vec[0];
		vec[1]= -vec[1];
		vec[2]= -vec[2];
	}
	if(axis==4) {
		cox= 1; coy= 0; coz= 2;		/*  */
	}
	if(axis==5) {
		cox= 2; coy= 1; coz= 0;		/* Y up X tr */
	}

	mat[coz][0]= vec[0];
	mat[coz][1]= vec[1];
	mat[coz][2]= vec[2];
	Normalize((float *)mat[coz]);
	
	inp= mat[coz][2];
	mat[coy][0]= - inp*mat[coz][0];
	mat[coy][1]= - inp*mat[coz][1];
	mat[coy][2]= 1.0f - inp*mat[coz][2];

	Normalize((float *)mat[coy]);
	
	Crossf(mat[cox], mat[coy], mat[coz]);
	
}

/* A & M Watt, Advanced animation and rendering techniques, 1992 ACM press */
void QuatInterpolW(float *, float *, float *, float );

void QuatInterpolW(float *result, float *quat1, float *quat2, float t)
{
	float omega, cosom, sinom, sc1, sc2;

	cosom = quat1[0]*quat2[0] + quat1[1]*quat2[1] + quat1[2]*quat2[2] + quat1[3]*quat2[3] ;
	
	/* rotate around shortest angle */
	if ((1.0 + cosom) > 0.0001) {
		
		if ((1.0 - cosom) > 0.0001) {
			omega = acos(cosom);
			sinom = sin(omega);
			sc1 = sin((1.0 - t) * omega) / sinom;
			sc2 = sin(t * omega) / sinom;
		} 
		else {
			sc1 = 1.0 - t;
			sc2 = t;
		}
		result[0] = sc1*quat1[0] + sc2*quat2[0];
		result[1] = sc1*quat1[1] + sc2*quat2[1];
		result[2] = sc1*quat1[2] + sc2*quat2[2];
		result[3] = sc1*quat1[3] + sc2*quat2[3];
	} 
	else {
		result[0] = quat2[3];
		result[1] = -quat2[2];
		result[2] = quat2[1];
		result[3] = -quat2[0];
		
		sc1 = sin((1.0 - t)*M_PI_2);
		sc2 = sin(t*M_PI_2);

		result[0] = sc1*quat1[0] + sc2*result[0];
		result[1] = sc1*quat1[1] + sc2*result[1];
		result[2] = sc1*quat1[2] + sc2*result[2];
		result[3] = sc1*quat1[3] + sc2*result[3];
	}
}

void QuatInterpol(float *result, float *quat1, float *quat2, float t)
{
	float quat[4], omega, cosom, sinom, sc1, sc2;

	cosom = quat1[0]*quat2[0] + quat1[1]*quat2[1] + quat1[2]*quat2[2] + quat1[3]*quat2[3] ;
	
	/* rotate around shortest angle */
	if (cosom < 0.0) {
		cosom = -cosom;
		quat[0]= -quat1[0];
		quat[1]= -quat1[1];
		quat[2]= -quat1[2];
		quat[3]= -quat1[3];
	} 
	else {
		quat[0]= quat1[0];
		quat[1]= quat1[1];
		quat[2]= quat1[2];
		quat[3]= quat1[3];
	}
	
	if ((1.0 - cosom) > 0.0001) {
		omega = acos(cosom);
		sinom = sin(omega);
		sc1 = sin((1 - t) * omega) / sinom;
		sc2 = sin(t * omega) / sinom;
	} else {
		sc1= 1.0 - t;
		sc2= t;
	}
	
	result[0] = sc1 * quat[0] + sc2 * quat2[0];
	result[1] = sc1 * quat[1] + sc2 * quat2[1];
	result[2] = sc1 * quat[2] + sc2 * quat2[2];
	result[3] = sc1 * quat[3] + sc2 * quat2[3];
}

void QuatAdd(float *result, float *quat1, float *quat2, float t)
{
	result[0]= quat1[0] + t*quat2[0];
	result[1]= quat1[1] + t*quat2[1];
	result[2]= quat1[2] + t*quat2[2];
	result[3]= quat1[3] + t*quat2[3];
}

/* **************** VIEW / PROJECTION ********************************  */


void i_ortho(
	float left, float right,
	float bottom, float top,
	float nearClip, float farClip,
	float matrix[][4]
){
    float Xdelta, Ydelta, Zdelta;
 
    Xdelta = right - left;
    Ydelta = top - bottom;
    Zdelta = farClip - nearClip;
    if (Xdelta == 0.0 || Ydelta == 0.0 || Zdelta == 0.0) {
		return;
    }
    Mat4One(matrix);
    matrix[0][0] = 2.0f/Xdelta;
    matrix[3][0] = -(right + left)/Xdelta;
    matrix[1][1] = 2.0f/Ydelta;
    matrix[3][1] = -(top + bottom)/Ydelta;
    matrix[2][2] = -2.0f/Zdelta;		/* note: negate Z	*/
    matrix[3][2] = -(farClip + nearClip)/Zdelta;
}

void i_window(
	float left, float right,
	float bottom, float top,
	float nearClip, float farClip,
	float mat[][4]
){
	float Xdelta, Ydelta, Zdelta;

	Xdelta = right - left;
	Ydelta = top - bottom;
	Zdelta = farClip - nearClip;

	if (Xdelta == 0.0 || Ydelta == 0.0 || Zdelta == 0.0) {
		return;
	}
	mat[0][0] = nearClip * 2.0f/Xdelta;
	mat[1][1] = nearClip * 2.0f/Ydelta;
	mat[2][0] = (right + left)/Xdelta;		/* note: negate Z	*/
	mat[2][1] = (top + bottom)/Ydelta;
	mat[2][2] = -(farClip + nearClip)/Zdelta;
	mat[2][3] = -1.0f;
	mat[3][2] = (-2.0f * nearClip * farClip)/Zdelta;
	mat[0][1] = mat[0][2] = mat[0][3] =
	    mat[1][0] = mat[1][2] = mat[1][3] =
	    mat[3][0] = mat[3][1] = mat[3][3] = 0.0;

}

void i_translate(float Tx, float Ty, float Tz, float mat[][4])
{
    mat[3][0] += (Tx*mat[0][0] + Ty*mat[1][0] + Tz*mat[2][0]);
    mat[3][1] += (Tx*mat[0][1] + Ty*mat[1][1] + Tz*mat[2][1]);
    mat[3][2] += (Tx*mat[0][2] + Ty*mat[1][2] + Tz*mat[2][2]);
}

void i_multmatrix( float icand[][4], float Vm[][4])
{
    int row, col;
    float temp[4][4];

    for(row=0 ; row<4 ; row++) 
        for(col=0 ; col<4 ; col++)
            temp[row][col] = icand[row][0] * Vm[0][col]
                           + icand[row][1] * Vm[1][col]
                           + icand[row][2] * Vm[2][col]
                           + icand[row][3] * Vm[3][col];
	Mat4CpyMat4(Vm, temp);
}

void i_rotate(float angle, char axis, float mat[][4])
{
	int col;
    float temp[4];
    float cosine, sine;

    for(col=0; col<4 ; col++)	/* init temp to zero matrix */
        temp[col] = 0;

    angle = (float)(angle*(3.1415926535/180.0));
    cosine = (float)cos(angle);
    sine = (float)sin(angle);
    switch(axis){
    case 'x':    
    case 'X':    
        for(col=0 ; col<4 ; col++)
            temp[col] = cosine*mat[1][col] + sine*mat[2][col];
        for(col=0 ; col<4 ; col++) {
	    mat[2][col] = - sine*mat[1][col] + cosine*mat[2][col];
            mat[1][col] = temp[col];
	}
        break;

    case 'y':
    case 'Y':
        for(col=0 ; col<4 ; col++)
            temp[col] = cosine*mat[0][col] - sine*mat[2][col];
        for(col=0 ; col<4 ; col++) {
            mat[2][col] = sine*mat[0][col] + cosine*mat[2][col];
            mat[0][col] = temp[col];
        }
	break;

    case 'z':
    case 'Z':
        for(col=0 ; col<4 ; col++)
            temp[col] = cosine*mat[0][col] + sine*mat[1][col];
        for(col=0 ; col<4 ; col++) {
            mat[1][col] = - sine*mat[0][col] + cosine*mat[1][col];
            mat[0][col] = temp[col];
        }
	break;
    }
}

void i_polarview(float dist, float azimuth, float incidence, float twist, float Vm[][4])
{

	Mat4One(Vm);

    i_translate(0.0, 0.0, -dist, Vm);
    i_rotate(-twist,'z', Vm);	
    i_rotate(-incidence,'x', Vm);
    i_rotate(-azimuth,'z', Vm);
}

void i_lookat(float vx, float vy, float vz, float px, float py, float pz, float twist, float mat[][4])
{
	float sine, cosine, hyp, hyp1, dx, dy, dz;
	float mat1[4][4];
	
	Mat4One(mat);
	Mat4One(mat1);

	i_rotate(-twist,'z', mat);

	dx = px - vx;
	dy = py - vy;
	dz = pz - vz;
	hyp = dx * dx + dz * dz;	/* hyp squared	*/
	hyp1 = (float)sqrt(dy*dy + hyp);
	hyp = (float)sqrt(hyp);		/* the real hyp	*/
	
	if (hyp1 != 0.0) {		/* rotate X	*/
		sine = -dy / hyp1;
		cosine = hyp /hyp1;
	} else {
		sine = 0;
		cosine = 1.0f;
	}
	mat1[1][1] = cosine;
	mat1[1][2] = sine;
	mat1[2][1] = -sine;
	mat1[2][2] = cosine;
	
	i_multmatrix(mat1, mat);

    mat1[1][1] = mat1[2][2] = 1.0f;	/* be careful here to reinit	*/
    mat1[1][2] = mat1[2][1] = 0.0;	/* those modified by the last	*/
	
	/* paragraph	*/
	if (hyp != 0.0f) {			/* rotate Y	*/
		sine = dx / hyp;
		cosine = -dz / hyp;
	} else {
		sine = 0;
		cosine = 1.0f;
	}
	mat1[0][0] = cosine;
	mat1[0][2] = -sine;
	mat1[2][0] = sine;
	mat1[2][2] = cosine;
	
	i_multmatrix(mat1, mat);
	i_translate(-vx,-vy,-vz, mat);	/* translate viewpoint to origin */
}





/* ************************************************  */

void Mat3Ortho(float mat[][3])
{	
	Normalize(mat[0]);
	Normalize(mat[1]);
	Normalize(mat[2]);
}

void Mat4Ortho(float mat[][4])
{
	float len;
	
	len= Normalize(mat[0]);
	if(len!=0.0) mat[0][3]/= len;
	len= Normalize(mat[1]);
	if(len!=0.0) mat[1][3]/= len;
	len= Normalize(mat[2]);
	if(len!=0.0) mat[2][3]/= len;
}

void VecCopyf(float *v1, float *v2)
{
	v1[0]= v2[0];
	v1[1]= v2[1];
	v1[2]= v2[2];
}

int VecLen( int *v1, int *v2)
{
	float x,y,z;

	x=(float)(v1[0]-v2[0]);
	y=(float)(v1[1]-v2[1]);
	z=(float)(v1[2]-v2[2]);
	return (int)floor(sqrt(x*x+y*y+z*z));
}

float VecLenf( float *v1, float *v2)
{
	float x,y,z;

	x=v1[0]-v2[0];
	y=v1[1]-v2[1];
	z=v1[2]-v2[2];
	return (float)sqrt(x*x+y*y+z*z);
}

float VecLength(float *v)
{
	return (float) sqrt(v[0]*v[0] + v[1]*v[1] + v[2]*v[2]);
}

void VecAddf(float *v, float *v1, float *v2)
{
	v[0]= v1[0]+ v2[0];
	v[1]= v1[1]+ v2[1];
	v[2]= v1[2]+ v2[2];
}

void VecSubf(float *v, float *v1, float *v2)
{
	v[0]= v1[0]- v2[0];
	v[1]= v1[1]- v2[1];
	v[2]= v1[2]- v2[2];
}

void VecLerpf(float *target, float *a, float *b, float t)
{
	float s = 1.0f-t;

	target[0]= s*a[0] + t*b[0];
	target[1]= s*a[1] + t*b[1];
	target[2]= s*a[2] + t*b[2];
}

void VecMidf(float *v, float *v1, float *v2)
{
	v[0]= 0.5f*(v1[0]+ v2[0]);
	v[1]= 0.5f*(v1[1]+ v2[1]);
	v[2]= 0.5f*(v1[2]+ v2[2]);
}

void VecMulf(float *v1, float f)
{

	v1[0]*= f;
	v1[1]*= f;
	v1[2]*= f;
}

int VecLenCompare(float *v1, float *v2, float limit)
{
    float x,y,z;

	x=v1[0]-v2[0];
	y=v1[1]-v2[1];
	z=v1[2]-v2[2];

	return ((x*x + y*y + z*z) < (limit*limit));
}

int VecCompare( float *v1, float *v2, float limit)
{
	if( fabs(v1[0]-v2[0])<limit )
		if( fabs(v1[1]-v2[1])<limit )
			if( fabs(v1[2]-v2[2])<limit ) return 1;
	return 0;
}

int VecEqual(float *v1, float *v2)
{
	return ((v1[0]==v2[0]) && (v1[1]==v2[1]) && (v1[2]==v2[2]));
}

void CalcNormShort( short *v1, short *v2, short *v3, float *n) /* is also cross product */
{
	float n1[3],n2[3];

	n1[0]= (float)(v1[0]-v2[0]);
	n2[0]= (float)(v2[0]-v3[0]);
	n1[1]= (float)(v1[1]-v2[1]);
	n2[1]= (float)(v2[1]-v3[1]);
	n1[2]= (float)(v1[2]-v2[2]);
	n2[2]= (float)(v2[2]-v3[2]);
	n[0]= n1[1]*n2[2]-n1[2]*n2[1];
	n[1]= n1[2]*n2[0]-n1[0]*n2[2];
	n[2]= n1[0]*n2[1]-n1[1]*n2[0];
	Normalize(n);
}

void CalcNormLong( int* v1, int*v2, int*v3, float *n)
{
	float n1[3],n2[3];

	n1[0]= (float)(v1[0]-v2[0]);
	n2[0]= (float)(v2[0]-v3[0]);
	n1[1]= (float)(v1[1]-v2[1]);
	n2[1]= (float)(v2[1]-v3[1]);
	n1[2]= (float)(v1[2]-v2[2]);
	n2[2]= (float)(v2[2]-v3[2]);
	n[0]= n1[1]*n2[2]-n1[2]*n2[1];
	n[1]= n1[2]*n2[0]-n1[0]*n2[2];
	n[2]= n1[0]*n2[1]-n1[1]*n2[0];
	Normalize(n);
}

float CalcNormFloat( float *v1, float *v2, float *v3, float *n)
{
	float n1[3],n2[3];

	n1[0]= v1[0]-v2[0];
	n2[0]= v2[0]-v3[0];
	n1[1]= v1[1]-v2[1];
	n2[1]= v2[1]-v3[1];
	n1[2]= v1[2]-v2[2];
	n2[2]= v2[2]-v3[2];
	n[0]= n1[1]*n2[2]-n1[2]*n2[1];
	n[1]= n1[2]*n2[0]-n1[0]*n2[2];
	n[2]= n1[0]*n2[1]-n1[1]*n2[0];
	return Normalize(n);
}

float CalcNormFloat4( float *v1, float *v2, float *v3, float *v4, float *n)
{
	/* real cross! */
	float n1[3],n2[3];

	n1[0]= v1[0]-v3[0];
	n1[1]= v1[1]-v3[1];
	n1[2]= v1[2]-v3[2];

	n2[0]= v2[0]-v4[0];
	n2[1]= v2[1]-v4[1];
	n2[2]= v2[2]-v4[2];

	n[0]= n1[1]*n2[2]-n1[2]*n2[1];
	n[1]= n1[2]*n2[0]-n1[0]*n2[2];
	n[2]= n1[0]*n2[1]-n1[1]*n2[0];

	return Normalize(n);
}


void CalcCent3f(float *cent, float *v1, float *v2, float *v3)
{

	cent[0]= 0.33333f*(v1[0]+v2[0]+v3[0]);
	cent[1]= 0.33333f*(v1[1]+v2[1]+v3[1]);
	cent[2]= 0.33333f*(v1[2]+v2[2]+v3[2]);
}

void CalcCent4f(float *cent, float *v1, float *v2, float *v3, float *v4)
{

	cent[0]= 0.25f*(v1[0]+v2[0]+v3[0]+v4[0]);
	cent[1]= 0.25f*(v1[1]+v2[1]+v3[1]+v4[1]);
	cent[2]= 0.25f*(v1[2]+v2[2]+v3[2]+v4[2]);
}

float Sqrt3f(float f)
{
	if(f==0.0) return 0;
	if(f<0) return (float)(-exp(log(-f)/3));
	else return (float)(exp(log(f)/3));
}

double Sqrt3d(double d)
{
	if(d==0.0) return 0;
	if(d<0) return -exp(log(-d)/3);
	else return exp(log(d)/3);
}

/* distance v1 to line v2-v3 */
/* using Hesse formula, NO LINE PIECE! */
float DistVL2Dfl( float *v1, float *v2, float *v3)  {
	float a[2],deler;

	a[0]= v2[1]-v3[1];
	a[1]= v3[0]-v2[0];
	deler= (float)sqrt(a[0]*a[0]+a[1]*a[1]);
	if(deler== 0.0f) return 0;

	return (float)(fabs((v1[0]-v2[0])*a[0]+(v1[1]-v2[1])*a[1])/deler);

}

/* distance v1 to line-piece v2-v3 */
float PdistVL2Dfl( float *v1, float *v2, float *v3) 
{
	float labda, rc[2], pt[2], len;
	
	rc[0]= v3[0]-v2[0];
	rc[1]= v3[1]-v2[1];
	len= rc[0]*rc[0]+ rc[1]*rc[1];
	if(len==0.0) {
		rc[0]= v1[0]-v2[0];
		rc[1]= v1[1]-v2[1];
		return (float)(sqrt(rc[0]*rc[0]+ rc[1]*rc[1]));
	}
	
	labda= ( rc[0]*(v1[0]-v2[0]) + rc[1]*(v1[1]-v2[1]) )/len;
	if(labda<=0.0) {
		pt[0]= v2[0];
		pt[1]= v2[1];
	}
	else if(labda>=1.0) {
		pt[0]= v3[0];
		pt[1]= v3[1];
	}
	else {
		pt[0]= labda*rc[0]+v2[0];
		pt[1]= labda*rc[1]+v2[1];
	}

	rc[0]= pt[0]-v1[0];
	rc[1]= pt[1]-v1[1];
	return (float)sqrt(rc[0]*rc[0]+ rc[1]*rc[1]);
}

float AreaF2Dfl( float *v1, float *v2, float *v3)
{
	return (float)(0.5*fabs( (v1[0]-v2[0])*(v2[1]-v3[1]) + (v1[1]-v2[1])*(v3[0]-v2[0]) ));
}


float AreaQ3Dfl( float *v1, float *v2, float *v3,  float *v4)  /* only convex Quadrilaterals */
{
	float len, vec1[3], vec2[3], n[3];

	VecSubf(vec1, v2, v1);
	VecSubf(vec2, v4, v1);
	Crossf(n, vec1, vec2);
	len= Normalize(n);

	VecSubf(vec1, v4, v3);
	VecSubf(vec2, v2, v3);
	Crossf(n, vec1, vec2);
	len+= Normalize(n);

	return (len/2.0f);
}

float AreaT3Dfl( float *v1, float *v2, float *v3)  /* Triangles */
{
	float len, vec1[3], vec2[3], n[3];

	VecSubf(vec1, v3, v2);
	VecSubf(vec2, v1, v2);
	Crossf(n, vec1, vec2);
	len= Normalize(n);

	return (len/2.0f);
}

#define MAX2(x,y)		( (x)>(y) ? (x) : (y) )
#define MAX3(x,y,z)		MAX2( MAX2((x),(y)) , (z) )


float AreaPoly3Dfl(int nr, float *verts, float *normal)
{
	float x, y, z, area, max;
	float *cur, *prev;
	int a, px=0, py=1;

	/* first: find dominant axis: 0==X, 1==Y, 2==Z */
	x= (float)fabs(normal[0]);
	y= (float)fabs(normal[1]);
	z= (float)fabs(normal[2]);
	max = MAX3(x, y, z);
	if(max==y) py=2;
	else if(max==x) {
		px=1; 
		py= 2;
	}

	/* The Trapezium Area Rule */
	prev= verts+3*(nr-1);
	cur= verts;
	area= 0;
	for(a=0; a<nr; a++) {
		area+= (cur[px]-prev[px])*(cur[py]+prev[py]);
		prev= cur;
		cur+=3;
	}

	return (float)fabs(0.5*area/max);
}

/* intersect Line-Line, shorts */
short IsectLL2Ds(short *v1, short *v2, short *v3, short *v4)
{
	/* return:
	-1: colliniar
	 0: no intersection of segments
	 1: exact intersection of segments
	 2: cross-intersection of segments
	*/
	float div, labda, mu;
	
	div= (v2[0]-v1[0])*(v4[1]-v3[1])-(v2[1]-v1[1])*(v4[0]-v3[0]);
	if(div==0.0) return -1;
	
	labda= ((float)(v1[1]-v3[1])*(v4[0]-v3[0])-(v1[0]-v3[0])*(v4[1]-v3[1]))/div;
	
	mu= ((float)(v1[1]-v3[1])*(v2[0]-v1[0])-(v1[0]-v3[0])*(v2[1]-v1[1]))/div;
	
	if(labda>=0.0 && labda<=1.0 && mu>=0.0 && mu<=1.0) {
		if(labda==0.0 || labda==1.0 || mu==0.0 || mu==1.0) return 1;
		return 2;
	}
	return 0;
}

/* intersect Line-Line, floats */
short IsectLL2Df(float *v1, float *v2, float *v3, float *v4)
{
	/* return:
	-1: colliniar
0: no intersection of segments
1: exact intersection of segments
2: cross-intersection of segments
	*/
	float div, labda, mu;
	
	div= (v2[0]-v1[0])*(v4[1]-v3[1])-(v2[1]-v1[1])*(v4[0]-v3[0]);
	if(div==0.0) return -1;
	
	labda= ((float)(v1[1]-v3[1])*(v4[0]-v3[0])-(v1[0]-v3[0])*(v4[1]-v3[1]))/div;
	
	mu= ((float)(v1[1]-v3[1])*(v2[0]-v1[0])-(v1[0]-v3[0])*(v2[1]-v1[1]))/div;
	
	if(labda>=0.0 && labda<=1.0 && mu>=0.0 && mu<=1.0) {
		if(labda==0.0 || labda==1.0 || mu==0.0 || mu==1.0) return 1;
		return 2;
	}
	return 0;
}

void MinMax3(float *min, float *max, float *vec)
{
	if(min[0]>vec[0]) min[0]= vec[0];
	if(min[1]>vec[1]) min[1]= vec[1];
	if(min[2]>vec[2]) min[2]= vec[2];

	if(max[0]<vec[0]) max[0]= vec[0];
	if(max[1]<vec[1]) max[1]= vec[1];
	if(max[2]<vec[2]) max[2]= vec[2];
}

static float TriSignedArea(float *v1, float *v2, float *v3, int i, int j)
{
	return 0.5f*((v1[i]-v2[i])*(v2[j]-v3[j]) + (v1[j]-v2[j])*(v3[i]-v2[i]));
}

static int BarycentricWeights(float *v1, float *v2, float *v3, float *co, float *n, float *w)
{
	float xn, yn, zn, a1, a2, a3, asum;
	short i, j;

	/* find best projection of face XY, XZ or YZ: barycentric weights of
	   the 2d projected coords are the same and faster to compute */
	xn= fabs(n[0]);
	yn= fabs(n[1]);
	zn= fabs(n[2]);
	if(zn>=xn && zn>=yn) {i= 0; j= 1;}
	else if(yn>=xn && yn>=zn) {i= 0; j= 2;}
	else {i= 1; j= 2;} 

	a1= TriSignedArea(v2, v3, co, i, j);
	a2= TriSignedArea(v3, v1, co, i, j);
	a3= TriSignedArea(v1, v2, co, i, j);

	asum= a1 + a2 + a3;

	if (fabs(asum) < FLT_EPSILON) {
		/* zero area triangle */
		w[0]= w[1]= w[2]= 1.0f/3.0f;
		return 1;
	}

	asum= 1.0f/asum;
	w[0]= a1*asum;
	w[1]= a2*asum;
	w[2]= a3*asum;

	return 0;
}

void InterpWeightsQ3Dfl(float *v1, float *v2, float *v3, float *v4, float *co, float *w)
{
	float w2[3];

	w[0]= w[1]= w[2]= w[3]= 0.0f;

	/* first check for exact match */
	if(VecEqual(co, v1))
		w[0]= 1.0f;
	else if(VecEqual(co, v2))
		w[1]= 1.0f;
	else if(VecEqual(co, v3))
		w[2]= 1.0f;
	else if(v4 && VecEqual(co, v4))
		w[3]= 1.0f;
	else {
		/* otherwise compute barycentric interpolation weights */
		float n1[3], n2[3], n[3];
		int degenerate;

		VecSubf(n1, v1, v3);
		if (v4) {
			VecSubf(n2, v2, v4);
		}
		else {
			VecSubf(n2, v2, v3);
		}
		Crossf(n, n1, n2);

		/* OpenGL seems to split this way, so we do too */
		if (v4) {
			degenerate= BarycentricWeights(v1, v2, v4, co, n, w);
			SWAP(float, w[2], w[3]);

			if(degenerate || (w[0] < 0.0f)) {
				/* if w[1] is negative, co is on the other side of the v1-v3 edge,
				   so we interpolate using the other triangle */
				degenerate= BarycentricWeights(v2, v3, v4, co, n, w2);

				if(!degenerate) {
					w[0]= 0.0f;
					w[1]= w2[0];
					w[2]= w2[1];
					w[3]= w2[2];
				}
			}
		}
		else
			BarycentricWeights(v1, v2, v3, co, n, w);
	}
} 

/* ************ EULER *************** */

void EulToMat3( float *eul, float mat[][3])
{
	double ci, cj, ch, si, sj, sh, cc, cs, sc, ss;
	
	ci = cos(eul[0]); 
	cj = cos(eul[1]); 
	ch = cos(eul[2]);
	si = sin(eul[0]); 
	sj = sin(eul[1]); 
	sh = sin(eul[2]);
	cc = ci*ch; 
	cs = ci*sh; 
	sc = si*ch; 
	ss = si*sh;

	mat[0][0] = (float)(cj*ch); 
	mat[1][0] = (float)(sj*sc-cs); 
	mat[2][0] = (float)(sj*cc+ss);
	mat[0][1] = (float)(cj*sh); 
	mat[1][1] = (float)(sj*ss+cc); 
	mat[2][1] = (float)(sj*cs-sc);
	mat[0][2] = (float)-sj;	 
	mat[1][2] = (float)(cj*si);    
	mat[2][2] = (float)(cj*ci);

}

void EulToMat4( float *eul,float mat[][4])
{
	double ci, cj, ch, si, sj, sh, cc, cs, sc, ss;
	
	ci = cos(eul[0]); 
	cj = cos(eul[1]); 
	ch = cos(eul[2]);
	si = sin(eul[0]); 
	sj = sin(eul[1]); 
	sh = sin(eul[2]);
	cc = ci*ch; 
	cs = ci*sh; 
	sc = si*ch; 
	ss = si*sh;

	mat[0][0] = (float)(cj*ch); 
	mat[1][0] = (float)(sj*sc-cs); 
	mat[2][0] = (float)(sj*cc+ss);
	mat[0][1] = (float)(cj*sh); 
	mat[1][1] = (float)(sj*ss+cc); 
	mat[2][1] = (float)(sj*cs-sc);
	mat[0][2] = (float)-sj;	 
	mat[1][2] = (float)(cj*si);    
	mat[2][2] = (float)(cj*ci);


	mat[3][0]= mat[3][1]= mat[3][2]= mat[0][3]= mat[1][3]= mat[2][3]= 0.0f;
	mat[3][3]= 1.0f;
}

/* returns two euler calculation methods, so we can pick the best */
static void mat3_to_eul2(float tmat[][3], float *eul1, float *eul2)
{
	float cy, quat[4], mat[3][3];
	
	Mat3ToQuat(tmat, quat);
	QuatToMat3(quat, mat);
	Mat3CpyMat3(mat, tmat);
	Mat3Ortho(mat);
	
	cy = (float)sqrt(mat[0][0]*mat[0][0] + mat[0][1]*mat[0][1]);
	
	if (cy > 16.0*FLT_EPSILON) {
		
		eul1[0] = (float)atan2(mat[1][2], mat[2][2]);
		eul1[1] = (float)atan2(-mat[0][2], cy);
		eul1[2] = (float)atan2(mat[0][1], mat[0][0]);
		
		eul2[0] = (float)atan2(-mat[1][2], -mat[2][2]);
		eul2[1] = (float)atan2(-mat[0][2], -cy);
		eul2[2] = (float)atan2(-mat[0][1], -mat[0][0]);
		
	} else {
		eul1[0] = (float)atan2(-mat[2][1], mat[1][1]);
		eul1[1] = (float)atan2(-mat[0][2], cy);
		eul1[2] = 0.0f;
		
		VecCopyf(eul2, eul1);
	}
}

void Mat3ToEul(float tmat[][3], float *eul)
{
	float eul1[3], eul2[3];
	
	mat3_to_eul2(tmat, eul1, eul2);
		
	/* return best, which is just the one with lowest values it in */
	if( fabs(eul1[0])+fabs(eul1[1])+fabs(eul1[2]) > fabs(eul2[0])+fabs(eul2[1])+fabs(eul2[2])) {
		VecCopyf(eul, eul2);
	}
	else {
		VecCopyf(eul, eul1);
	}
}

void Mat4ToEul(float tmat[][4], float *eul)
{
	float tempMat[3][3];

	Mat3CpyMat4 (tempMat, tmat);
	Mat3Ortho(tempMat);
	Mat3ToEul(tempMat, eul);
}

void QuatToEul( float *quat, float *eul)
{
	float mat[3][3];
	
	QuatToMat3(quat, mat);
	Mat3ToEul(mat, eul);
}


void EulToQuat( float *eul, float *quat)
{
    float ti, tj, th, ci, cj, ch, si, sj, sh, cc, cs, sc, ss;
 
    ti = eul[0]*0.5f; tj = eul[1]*0.5f; th = eul[2]*0.5f;
    ci = (float)cos(ti);  cj = (float)cos(tj);  ch = (float)cos(th);
    si = (float)sin(ti);  sj = (float)sin(tj);  sh = (float)sin(th);
    cc = ci*ch; cs = ci*sh; sc = si*ch; ss = si*sh;
	
	quat[0] = cj*cc + sj*ss;
	quat[1] = cj*sc - sj*cs;
	quat[2] = cj*ss + sj*cc;
	quat[3] = cj*cs - sj*sc;
}

void VecRotToMat3( float *vec, float phi, float mat[][3])
{
	/* rotation of phi radials around vec */
	float vx, vx2, vy, vy2, vz, vz2, co, si;
	
	vx= vec[0];
	vy= vec[1];
	vz= vec[2];
	vx2= vx*vx;
	vy2= vy*vy;
	vz2= vz*vz;
	co= (float)cos(phi);
	si= (float)sin(phi);
	
	mat[0][0]= vx2+co*(1.0f-vx2);
	mat[0][1]= vx*vy*(1.0f-co)+vz*si;
	mat[0][2]= vz*vx*(1.0f-co)-vy*si;
	mat[1][0]= vx*vy*(1.0f-co)-vz*si;
	mat[1][1]= vy2+co*(1.0f-vy2);
	mat[1][2]= vy*vz*(1.0f-co)+vx*si;
	mat[2][0]= vz*vx*(1.0f-co)+vy*si;
	mat[2][1]= vy*vz*(1.0f-co)-vx*si;
	mat[2][2]= vz2+co*(1.0f-vz2);
	
}

void VecRotToMat4( float *vec, float phi, float mat[][4])
{
	float tmat[3][3];
	
	VecRotToMat3(vec, phi, tmat);
	Mat4One(mat);
	Mat4CpyMat3(mat, tmat);
}

void VecRotToQuat( float *vec, float phi, float *quat)
{
	/* rotation of phi radials around vec */
	float si;

	quat[1]= vec[0];
	quat[2]= vec[1];
	quat[3]= vec[2];
	
	if( Normalize(quat+1) == 0.0) {
		QuatOne(quat);
	}
	else {
		quat[0]= (float)cos( phi/2.0 );
		si= (float)sin( phi/2.0 );
		quat[1] *= si;
		quat[2] *= si;
		quat[3] *= si;
	}
}

/* Return the angle in degrees between vecs 1-2 and 2-3 in degrees
   If v1 is a shoulder, v2 is the elbow and v3 is the hand,
   this would return the angle at the elbow */
float VecAngle3(float *v1, float *v2, float *v3)
{
	float vec1[3], vec2[3];

	VecSubf(vec1, v2, v1);
	VecSubf(vec2, v2, v3);
	Normalize(vec1);
	Normalize(vec2);

	return NormalizedVecAngle2(vec1, vec2) * 180.0/M_PI;
}

/* Return the shortest angle in degrees between the 2 vectors */
float VecAngle2(float *v1, float *v2)
{
	float vec1[3], vec2[3];

	VecCopyf(vec1, v1);
	VecCopyf(vec2, v2);
	Normalize(vec1);
	Normalize(vec2);

	return NormalizedVecAngle2(vec1, vec2)* 180.0/M_PI;
}

float NormalizedVecAngle2(float *v1, float *v2)
{
	/* this is the same as acos(Inpf(v1, v2)), but more accurate */
	if (Inpf(v1, v2) < 0.0f) {
		float vec[3];
		
		vec[0]= -v2[0];
		vec[1]= -v2[1];
		vec[2]= -v2[2];

		return (float)M_PI - 2.0f*saasin(VecLenf(vec, v1)/2.0f);
	}
	else
		return 2.0f*saasin(VecLenf(v2, v1)/2.0);
}

void euler_rot(float *beul, float ang, char axis)
{
	float eul[3], mat1[3][3], mat2[3][3], totmat[3][3];
	
	eul[0]= eul[1]= eul[2]= 0.0;
	if(axis=='x') eul[0]= ang;
	else if(axis=='y') eul[1]= ang;
	else eul[2]= ang;
	
	EulToMat3(eul, mat1);
	EulToMat3(beul, mat2);
	
	Mat3MulMat3(totmat, mat2, mat1);
	
	Mat3ToEul(totmat, beul);
	
}

/* exported to transform.c */
void compatible_eul(float *eul, float *oldrot)
{
	float dx, dy, dz;
	
	/* correct differences of about 360 degrees first */
	
	dx= eul[0] - oldrot[0];
	dy= eul[1] - oldrot[1];
	dz= eul[2] - oldrot[2];
	
	while( fabs(dx) > 5.1) {
		if(dx > 0.0) eul[0] -= 2.0*M_PI; else eul[0]+= 2.0*M_PI;
		dx= eul[0] - oldrot[0];
	}
	while( fabs(dy) > 5.1) {
		if(dy > 0.0) eul[1] -= 2.0*M_PI; else eul[1]+= 2.0*M_PI;
		dy= eul[1] - oldrot[1];
	}
	while( fabs(dz) > 5.1 ) {
		if(dz > 0.0) eul[2] -= 2.0*M_PI; else eul[2]+= 2.0*M_PI;
		dz= eul[2] - oldrot[2];
	}
	
	/* is 1 of the axis rotations larger than 180 degrees and the other small? NO ELSE IF!! */	
	if( fabs(dx) > 3.2 && fabs(dy)<1.6 && fabs(dz)<1.6 ) {
		if(dx > 0.0) eul[0] -= 2.0*M_PI; else eul[0]+= 2.0*M_PI;
	}
	if( fabs(dy) > 3.2 && fabs(dz)<1.6 && fabs(dx)<1.6 ) {
		if(dy > 0.0) eul[1] -= 2.0*M_PI; else eul[1]+= 2.0*M_PI;
	}
	if( fabs(dz) > 3.2 && fabs(dx)<1.6 && fabs(dy)<1.6 ) {
		if(dz > 0.0) eul[2] -= 2.0*M_PI; else eul[2]+= 2.0*M_PI;
	}
	
	/* the method below was there from ancient days... but why! probably because the code sucks :)
		*/
#if 0	
	/* calc again */
	dx= eul[0] - oldrot[0];
	dy= eul[1] - oldrot[1];
	dz= eul[2] - oldrot[2];
	
	/* special case, tested for x-z  */
	
	if( (fabs(dx) > 3.1 && fabs(dz) > 1.5 ) || ( fabs(dx) > 1.5 && fabs(dz) > 3.1 ) ) {
		if(dx > 0.0) eul[0] -= M_PI; else eul[0]+= M_PI;
		if(eul[1] > 0.0) eul[1]= M_PI - eul[1]; else eul[1]= -M_PI - eul[1];
		if(dz > 0.0) eul[2] -= M_PI; else eul[2]+= M_PI;
		
	}
	else if( (fabs(dx) > 3.1 && fabs(dy) > 1.5 ) || ( fabs(dx) > 1.5 && fabs(dy) > 3.1 ) ) {
		if(dx > 0.0) eul[0] -= M_PI; else eul[0]+= M_PI;
		if(dy > 0.0) eul[1] -= M_PI; else eul[1]+= M_PI;
		if(eul[2] > 0.0) eul[2]= M_PI - eul[2]; else eul[2]= -M_PI - eul[2];
	}
	else if( (fabs(dy) > 3.1 && fabs(dz) > 1.5 ) || ( fabs(dy) > 1.5 && fabs(dz) > 3.1 ) ) {
		if(eul[0] > 0.0) eul[0]= M_PI - eul[0]; else eul[0]= -M_PI - eul[0];
		if(dy > 0.0) eul[1] -= M_PI; else eul[1]+= M_PI;
		if(dz > 0.0) eul[2] -= M_PI; else eul[2]+= M_PI;
	}
#endif	
}

/* uses 2 methods to retrieve eulers, and picks the closest */
void Mat3ToCompatibleEul(float mat[][3], float *eul, float *oldrot)
{
	float eul1[3], eul2[3];
	float d1, d2;
	
	mat3_to_eul2(mat, eul1, eul2);
	
	compatible_eul(eul1, oldrot);
	compatible_eul(eul2, oldrot);
	
	d1= fabs(eul1[0]-oldrot[0]) + fabs(eul1[1]-oldrot[1]) + fabs(eul1[2]-oldrot[2]);
	d2= fabs(eul2[0]-oldrot[0]) + fabs(eul2[1]-oldrot[1]) + fabs(eul2[2]-oldrot[2]);
	
	/* return best, which is just the one with lowest difference */
	if( d1 > d2) {
		VecCopyf(eul, eul2);
	}
	else {
		VecCopyf(eul, eul1);
	}
	
}

/* ******************************************** */

void SizeToMat3( float *size, float mat[][3])
{
	mat[0][0]= size[0];
	mat[0][1]= 0.0;
	mat[0][2]= 0.0;
	mat[1][1]= size[1];
	mat[1][0]= 0.0;
	mat[1][2]= 0.0;
	mat[2][2]= size[2];
	mat[2][1]= 0.0;
	mat[2][0]= 0.0;
}

void SizeToMat4( float *size, float mat[][4])
{
	float tmat[3][3];
	
	SizeToMat3(size, tmat);
	Mat4One(mat);
	Mat4CpyMat3(mat, tmat);
}

void Mat3ToSize( float mat[][3], float *size)
{
	float vec[3];

	VecCopyf(vec, mat[0]);
	size[0]= Normalize(vec);
	VecCopyf(vec, mat[1]);
	size[1]= Normalize(vec);
	VecCopyf(vec, mat[2]);
	size[2]= Normalize(vec);

}

void Mat4ToSize( float mat[][4], float *size)
{
	float vec[3];
	

	VecCopyf(vec, mat[0]);
	size[0]= Normalize(vec);
	VecCopyf(vec, mat[1]);
	size[1]= Normalize(vec);
	VecCopyf(vec, mat[2]);
	size[2]= Normalize(vec);
}

/* ************* SPECIALS ******************* */

void triatoquat( float *v1,  float *v2,  float *v3, float *quat)
{
	/* imaginary x-axis, y-axis triangle is being rotated */
	float vec[3], q1[4], q2[4], n[3], si, co, angle, mat[3][3], imat[3][3];
	
	/* move z-axis to face-normal */
	CalcNormFloat(v1, v2, v3, vec);

	n[0]= vec[1];
	n[1]= -vec[0];
	n[2]= 0.0;
	Normalize(n);
	
	if(n[0]==0.0 && n[1]==0.0) n[0]= 1.0;
	
	angle= -0.5f*saacos(vec[2]);
	co= (float)cos(angle);
	si= (float)sin(angle);
	q1[0]= co;
	q1[1]= n[0]*si;
	q1[2]= n[1]*si;
	q1[3]= 0.0f;
	
	/* rotate back line v1-v2 */
	QuatToMat3(q1, mat);
	Mat3Inv(imat, mat);
	VecSubf(vec, v2, v1);
	Mat3MulVecfl(imat, vec);

	/* what angle has this line with x-axis? */
	vec[2]= 0.0;
	Normalize(vec);

	angle= (float)(0.5*atan2(vec[1], vec[0]));
	co= (float)cos(angle);
	si= (float)sin(angle);
	q2[0]= co;
	q2[1]= 0.0f;
	q2[2]= 0.0f;
	q2[3]= si;
	
	QuatMul(quat, q1, q2);
}

void MinMaxRGB(short c[])
{
	if(c[0]>255) c[0]=255;
	else if(c[0]<0) c[0]=0;
	if(c[1]>255) c[1]=255;
	else if(c[1]<0) c[1]=0;
	if(c[2]>255) c[2]=255;
	else if(c[2]<0) c[2]=0;
}

float Vec2Lenf(float *v1, float *v2)
{
	float x, y;

	x = v1[0]-v2[0];
	y = v1[1]-v2[1];
	return (float)sqrt(x*x+y*y);
}

void Vec2Mulf(float *v1, float f)
{
	v1[0]*= f;
	v1[1]*= f;
}

void Vec2Addf(float *v, float *v1, float *v2)
{
	v[0]= v1[0]+ v2[0];
	v[1]= v1[1]+ v2[1];
}

void Vec2Subf(float *v, float *v1, float *v2)
{
	v[0]= v1[0]- v2[0];
	v[1]= v1[1]- v2[1];
}

void Vec2Copyf(float *v1, float *v2)
{
	v1[0]= v2[0];
	v1[1]= v2[1];
}

float Inp2f(float *v1, float *v2)
{
	return v1[0]*v2[0]+v1[1]*v2[1];
}

float Normalize2(float *n)
{
	float d;
	
	d= n[0]*n[0]+n[1]*n[1];

	if(d>1.0e-35F) {
		d= (float)sqrt(d);

		n[0]/=d; 
		n[1]/=d; 
	} else {
		n[0]=n[1]= 0.0;
		d= 0.0;
	}
	return d;
}

void hsv_to_rgb(float h, float s, float v, float *r, float *g, float *b)
{
	int i;
	float f, p, q, t;

	h *= 360.0f;
	
	if(s==0.0) {
		*r = v;
		*g = v;
		*b = v;
	}
	else {
		if(h==360) h = 0;
		
		h /= 60;
		i = (int)floor(h);
		f = h - i;
		p = v*(1.0f-s);
		q = v*(1.0f-(s*f));
		t = v*(1.0f-(s*(1.0f-f)));
		
		switch (i) {
		case 0 :
			*r = v;
			*g = t;
			*b = p;
			break;
		case 1 :
			*r = q;
			*g = v;
			*b = p;
			break;
		case 2 :
			*r = p;
			*g = v;
			*b = t;
			break;
		case 3 :
			*r = p;
			*g = q;
			*b = v;
			break;
		case 4 :
			*r = t;
			*g = p;
			*b = v;
			break;
		case 5 :
			*r = v;
			*g = p;
			*b = q;
			break;
		}
	}
}

void rgb_to_yuv(float r, float g, float b, float *ly, float *lu, float *lv)
{
	float y, u, v;
	y= 0.299*r + 0.587*g + 0.114*b;
	u=-0.147*r - 0.289*g + 0.436*b;
	v= 0.615*r - 0.515*g - 0.100*b;
	
	*ly=y;
	*lu=u;
	*lv=v;
}

void yuv_to_rgb(float y, float u, float v, float *lr, float *lg, float *lb)
{
	float r, g, b;
	r=y+1.140*v;
	g=y-0.394*u - 0.581*v;
	b=y+2.032*u;
	
	*lr=r;
	*lg=g;
	*lb=b;
}

void rgb_to_ycc(float r, float g, float b, float *ly, float *lcb, float *lcr)
{
	float sr,sg, sb;
	float y, cr, cb;
	
	sr=255.0*r;
	sg=255.0*g;
	sb=255.0*b;
	
	
	y=(0.257*sr)+(0.504*sg)+(0.098*sb)+16.0;
	cb=(-0.148*sr)-(0.291*sg)+(0.439*sb)+128.0;
	cr=(0.439*sr)-(0.368*sg)-(0.071*sb)+128.0;
	
	*ly=y;
	*lcb=cb;
	*lcr=cr;
}

void ycc_to_rgb(float y, float cb, float cr, float *lr, float *lg, float *lb)
{
	float r,g,b;
	
	r=1.164*(y-16)+1.596*(cr-128);
	g=1.164*(y-16)-0.813*(cr-128)-0.392*(cb-128);
	b=1.164*(y-16)+2.017*(cb-128);
	
	*lr=r/255.0;
	*lg=g/255.0;
	*lb=b/255.0;
}

void hex_to_rgb(char *hexcol, float *r, float *g, float *b)
{
	unsigned int ri, gi, bi;
	
	if (hexcol[0] == '#') hexcol++;
	
	if (sscanf(hexcol, "%02x%02x%02x", &ri, &gi, &bi)) {
		*r = ri / 255.0;
		*g = gi / 255.0;		
		*b = bi / 255.0;
	}
}

void rgb_to_hsv(float r, float g, float b, float *lh, float *ls, float *lv)
{
	float h, s, v;
	float cmax, cmin, cdelta;
	float rc, gc, bc;

	cmax = r;
	cmin = r;
	cmax = (g>cmax ? g:cmax);
	cmin = (g<cmin ? g:cmin);
	cmax = (b>cmax ? b:cmax);
	cmin = (b<cmin ? b:cmin);

	v = cmax;		/* value */
	if (cmax!=0.0)
		s = (cmax - cmin)/cmax;
	else {
		s = 0.0;
		h = 0.0;
	}
	if (s == 0.0)
		h = -1.0;
	else {
		cdelta = cmax-cmin;
		rc = (cmax-r)/cdelta;
		gc = (cmax-g)/cdelta;
		bc = (cmax-b)/cdelta;
		if (r==cmax)
			h = bc-gc;
		else
			if (g==cmax)
				h = 2.0f+rc-bc;
			else
				h = 4.0f+gc-rc;
		h = h*60.0f;
		if (h<0.0f)
			h += 360.0f;
	}
	
	*ls = s;
	*lh = h/360.0f;
	if( *lh < 0.0) *lh= 0.0;
	*lv = v;
}


/* we define a 'cpack' here as a (3 byte color code) number that can be expressed like 0xFFAA66 or so.
   for that reason it is sensitive for endianness... with this function it works correctly
*/

unsigned int hsv_to_cpack(float h, float s, float v)
{
	short r, g, b;
	float rf, gf, bf;
	unsigned int col;
	
	hsv_to_rgb(h, s, v, &rf, &gf, &bf);
	
	r= (short)(rf*255.0f);
	g= (short)(gf*255.0f);
	b= (short)(bf*255.0f);
	
	col= ( r + (g*256) + (b*256*256) );
	return col;
}


unsigned int rgb_to_cpack(float r, float g, float b)
{
	int ir, ig, ib;
	
	ir= (int)floor(255.0*r);
	if(ir<0) ir= 0; else if(ir>255) ir= 255;
	ig= (int)floor(255.0*g);
	if(ig<0) ig= 0; else if(ig>255) ig= 255;
	ib= (int)floor(255.0*b);
	if(ib<0) ib= 0; else if(ib>255) ib= 255;
	
	return (ir+ (ig*256) + (ib*256*256));
}

void cpack_to_rgb(unsigned int col, float *r, float *g, float *b)
{
	
	*r= (float)((col)&0xFF);
	*r /= 255.0f;

	*g= (float)(((col)>>8)&0xFF);
	*g /= 255.0f;

	*b= (float)(((col)>>16)&0xFF);
	*b /= 255.0f;
}


/* *************** PROJECTIONS ******************* */

void tubemap(float x, float y, float z, float *u, float *v)
{
	float len;
	
	*v = (z + 1.0) / 2.0;
	
	len= sqrt(x*x+y*y);
	if(len>0) {
		*u = (1.0 - (atan2(x/len,y/len) / M_PI)) / 2.0;
	}
}

/* ------------------------------------------------------------------------- */

void spheremap(float x, float y, float z, float *u, float *v)
{
	float len;
	
	len= sqrt(x*x+y*y+z*z);
	if(len>0.0) {
		
		if(x==0.0 && y==0.0) *u= 0.0;	/* othwise domain error */
		else *u = (1.0 - atan2(x,y)/M_PI )/2.0;
		
		z/=len;
		*v = 1.0- saacos(z)/M_PI;
	}
}

/* ------------------------------------------------------------------------- */

/* *****************  m1 = m2 *****************  */
void cpy_m3_m3(float m1[][3], float m2[][3]) 
{	
	memcpy(m1[0], m2[0], 9*sizeof(float));
}

/* *****************  m1 = m2 *****************  */
void cpy_m4_m4(float m1[][4], float m2[][4]) 
{	
	memcpy(m1[0], m2[0], 16*sizeof(float));
}

/* ***************** identity matrix *****************  */
void ident_m4(float m[][4])
{
	
	m[0][0]= m[1][1]= m[2][2]= m[3][3]= 1.0;
	m[0][1]= m[0][2]= m[0][3]= 0.0;
	m[1][0]= m[1][2]= m[1][3]= 0.0;
	m[2][0]= m[2][1]= m[2][3]= 0.0;
	m[3][0]= m[3][1]= m[3][2]= 0.0;
}


/* *****************  m1 = m2 (pre) * m3 (post) ***************** */
void mul_m3_m3m3(float m1[][3], float m2[][3], float m3[][3])
{
	float m[3][3];
	
	m[0][0]= m2[0][0]*m3[0][0] + m2[1][0]*m3[0][1] + m2[2][0]*m3[0][2]; 
	m[0][1]= m2[0][1]*m3[0][0] + m2[1][1]*m3[0][1] + m2[2][1]*m3[0][2]; 
	m[0][2]= m2[0][2]*m3[0][0] + m2[1][2]*m3[0][1] + m2[2][2]*m3[0][2]; 

	m[1][0]= m2[0][0]*m3[1][0] + m2[1][0]*m3[1][1] + m2[2][0]*m3[1][2]; 
	m[1][1]= m2[0][1]*m3[1][0] + m2[1][1]*m3[1][1] + m2[2][1]*m3[1][2]; 
	m[1][2]= m2[0][2]*m3[1][0] + m2[1][2]*m3[1][1] + m2[2][2]*m3[1][2]; 

	m[2][0]= m2[0][0]*m3[2][0] + m2[1][0]*m3[2][1] + m2[2][0]*m3[2][2]; 
	m[2][1]= m2[0][1]*m3[2][0] + m2[1][1]*m3[2][1] + m2[2][1]*m3[2][2]; 
	m[2][2]= m2[0][2]*m3[2][0] + m2[1][2]*m3[2][1] + m2[2][2]*m3[2][2]; 

	cpy_m3_m3(m1, m2);
}

/*  ***************** m1 = m2 (pre) * m3 (post) ***************** */
void mul_m4_m4m4(float m1[][4], float m2[][4], float m3[][4])
{
	float m[4][4];
	
	m[0][0]= m2[0][0]*m3[0][0] + m2[1][0]*m3[0][1] + m2[2][0]*m3[0][2] + m2[3][0]*m3[0][3]; 
	m[0][1]= m2[0][1]*m3[0][0] + m2[1][1]*m3[0][1] + m2[2][1]*m3[0][2] + m2[3][1]*m3[0][3]; 
	m[0][2]= m2[0][2]*m3[0][0] + m2[1][2]*m3[0][1] + m2[2][2]*m3[0][2] + m2[3][2]*m3[0][3]; 
	m[0][3]= m2[0][3]*m3[0][0] + m2[1][3]*m3[0][1] + m2[2][3]*m3[0][2] + m2[3][3]*m3[0][3]; 

	m[1][0]= m2[0][0]*m3[1][0] + m2[1][0]*m3[1][1] + m2[2][0]*m3[1][2] + m2[3][0]*m3[1][3]; 
	m[1][1]= m2[0][1]*m3[1][0] + m2[1][1]*m3[1][1] + m2[2][1]*m3[1][2] + m2[3][1]*m3[1][3]; 
	m[1][2]= m2[0][2]*m3[1][0] + m2[1][2]*m3[1][1] + m2[2][2]*m3[1][2] + m2[3][2]*m3[1][3]; 
	m[1][3]= m2[0][3]*m3[1][0] + m2[1][3]*m3[1][1] + m2[2][3]*m3[1][2] + m2[3][3]*m3[1][3]; 

	m[2][0]= m2[0][0]*m3[2][0] + m2[1][0]*m3[2][1] + m2[2][0]*m3[2][2] + m2[3][0]*m3[2][3]; 
	m[2][1]= m2[0][1]*m3[2][0] + m2[1][1]*m3[2][1] + m2[2][1]*m3[2][2] + m2[3][1]*m3[2][3]; 
	m[2][2]= m2[0][2]*m3[2][0] + m2[1][2]*m3[2][1] + m2[2][2]*m3[2][2] + m2[3][2]*m3[2][3]; 
	m[2][3]= m2[0][3]*m3[2][0] + m2[1][3]*m3[2][1] + m2[2][3]*m3[2][2] + m2[3][3]*m3[2][3]; 
	
	m[3][0]= m2[0][0]*m3[3][0] + m2[1][0]*m3[3][1] + m2[2][0]*m3[3][2] + m2[3][0]*m3[3][3]; 
	m[3][1]= m2[0][1]*m3[3][0] + m2[1][1]*m3[3][1] + m2[2][1]*m3[3][2] + m2[3][1]*m3[3][3]; 
	m[3][2]= m2[0][2]*m3[3][0] + m2[1][2]*m3[3][1] + m2[2][2]*m3[3][2] + m2[3][2]*m3[3][3]; 
	m[3][3]= m2[0][3]*m3[3][0] + m2[1][3]*m3[3][1] + m2[2][3]*m3[3][2] + m2[3][3]*m3[3][3]; 
	
	cpy_m4_m4(m1, m2);
}

/*  ***************** m1 = inverse(m2)  *****************  */
void inv_m3_m3(float m1[][3], float m2[][3])
{
	short a,b;
	float det;
	
	/* calc adjoint */
	Mat3Adj(m1, m2);
	
	/* then determinant old matrix! */
	det= m2[0][0]* (m2[1][1]*m2[2][2] - m2[1][2]*m2[2][1])
	    -m2[1][0]* (m2[0][1]*m2[2][2] - m2[0][2]*m2[2][1])
	    +m2[2][0]* (m2[0][1]*m2[1][2] - m2[0][2]*m2[1][1]);
	
	if(det==0.0f) det=1.0f;
	det= 1.0f/det;
	for(a=0;a<3;a++) {
		for(b=0;b<3;b++) {
			m1[a][b]*=det;
		}
	}
}

/*  ***************** m1 = inverse(m2)  *****************  */
int inv_m4_m4(float inverse[][4], float mat[][4])
{
	int i, j, k;
	double temp;
	float tempmat[4][4];
	float max;
	int maxj;
	
	/* Set inverse to identity */
	ident_m4(inverse);
	
	/* Copy original matrix so we don't mess it up */
	cpy_m4_m4(tempmat, mat);
	
	for(i = 0; i < 4; i++) {
		/* Look for row with max pivot */
		max = ABS(tempmat[i][i]);
		maxj = i;
		for(j = i + 1; j < 4; j++) {
			if(ABS(tempmat[j][i]) > max) {
				max = ABS(tempmat[j][i]);
				maxj = j;
			}
		}
		/* Swap rows if necessary */
		if (maxj != i) {
			for( k = 0; k < 4; k++) {
				SWAP(float, tempmat[i][k], tempmat[maxj][k]);
				SWAP(float, inverse[i][k], inverse[maxj][k]);
			}
		}
		
		temp = tempmat[i][i];
		if (temp == 0)
			return 0;  /* No non-zero pivot */
		for(k = 0; k < 4; k++) {
			tempmat[i][k] = (float)(tempmat[i][k]/temp);
			inverse[i][k] = (float)(inverse[i][k]/temp);
		}
		for(j = 0; j < 4; j++) {
			if(j != i) {
				temp = tempmat[j][i];
				for(k = 0; k < 4; k++) {
					tempmat[j][k] -= (float)(tempmat[i][k]*temp);
					inverse[j][k] -= (float)(inverse[i][k]*temp);
				}
			}
		}
	}
	return 1;
}

/*  ***************** v1 = v2 * mat  ***************** */
void mul_v3_v3m4(float *v1, float *v2, float mat[][4])
{
	float x, y;
	
	x= v2[0];	/* work with a copy, v1 can be same as v2 */
	y= v2[1];
	v1[0]= x*mat[0][0] + y*mat[1][0] + mat[2][0]*v2[2] + mat[3][0];
	v1[1]= x*mat[0][1] + y*mat[1][1] + mat[2][1]*v2[2] + mat[3][1];
	v1[2]= x*mat[0][2] + y*mat[1][2] + mat[2][2]*v2[2] + mat[3][2];
	
}

/* moved from effect.c
   test if the line starting at p1 ending at p2 intersects the triangle v0..v2
   return non zero if it does 
*/
int LineIntersectsTriangle(float p1[3], float p2[3], float v0[3], float v1[3], float v2[3], float *lambda)
{

	float p[3], s[3], d[3], e1[3], e2[3], q[3];
	float a, f, u, v;
	
	VecSubf(e1, v1, v0);
	VecSubf(e2, v2, v0);
	VecSubf(d, p2, p1);
	
	Crossf(p, d, e2);
	a = Inpf(e1, p);
	if ((a > -0.000001) && (a < 0.000001)) return 0;
	f = 1.0f/a;
	
	VecSubf(s, p1, v0);
	
	Crossf(q, s, e1);
	*lambda = f * Inpf(e2, q);
	if ((*lambda < 0.0)||(*lambda > 1.0)) return 0;
	
	u = f * Inpf(s, p);
	if ((u < 0.0)||(u > 1.0)) return 0;
	
	v = f * Inpf(d, q);
	if ((v < 0.0)||((u + v) > 1.0)) return 0;
	
	return 1;
}


/*
find closest point to p on line through l1,l2
and return lambda, where (0 <= lambda <= 1) when cp is in the line segement l1,l2
*/
float lambda_cp_line_ex(float p[3], float l1[3], float l2[3], float cp[3])
{
	float h[3],u[3],lambda;
	VecSubf(u, l2, l1);
	VecSubf(h, p, l1);
	lambda =Inpf(u,h)/Inpf(u,u);
	cp[0] = l1[0] + u[0] * lambda;
	cp[1] = l1[1] + u[1] * lambda;
	cp[2] = l1[2] + u[2] * lambda;
	return lambda;
}
/* little sister we only need to know lambda */
float lambda_cp_line(float p[3], float l1[3], float l2[3])
{
	float h[3],u[3];
	VecSubf(u, l2, l1);
	VecSubf(h, p, l1);
	return(Inpf(u,h)/Inpf(u,u));
}



int point_in_slice(float p[3], float v1[3], float l1[3], float l2[3])
{
/* 
what is a slice ?
some maths:
a line including l1,l2 and a point not on the line 
define a subset of R3 delimeted by planes parallel to the line and orthogonal 
to the (point --> line) distance vector,one plane on the line one on the point, 
the room inside usually is rather small compared to R3 though still infinte
useful for restricting (speeding up) searches 
e.g. all points of triangular prism are within the intersection of 3 'slices'
onother trivial case : cube 
but see a 'spat' which is a deformed cube with paired parallel planes needs only 3 slices too
*/
	float h,rp[3],cp[3],q[3];

	lambda_cp_line_ex(v1,l1,l2,cp);
	VecSubf(q,cp,v1);

	VecSubf(rp,p,v1);
	h=Inpf(q,rp)/Inpf(q,q);
	if (h < 0.0f || h > 1.0f) return 0;
	return 1;
}

/*adult sister defining the slice planes by the origin and the normal  
NOTE |normal| may not be 1 but defining the thickness of the slice*/
int point_in_slice_as(float p[3],float origin[3],float normal[3])
{
	float h,rp[3];
	VecSubf(rp,p,origin);
	h=Inpf(normal,rp)/Inpf(normal,normal);
	if (h < 0.0f || h > 1.0f) return 0;
	return 1;
}

/*mama (knowing the squared lenght of the normal)*/
int point_in_slice_m(float p[3],float origin[3],float normal[3],float lns)
{
	float h,rp[3];
	VecSubf(rp,p,origin);
	h=Inpf(normal,rp)/lns;
	if (h < 0.0f || h > 1.0f) return 0;
	return 1;
}


int point_in_tri_prism(float p[3], float v1[3], float v2[3], float v3[3])
{
	if(!point_in_slice(p,v1,v2,v3)) return 0;
	if(!point_in_slice(p,v2,v3,v1)) return 0;
	if(!point_in_slice(p,v3,v1,v2)) return 0;
	return 1;
}

/* point closest to v1 on line v2-v3 in 3D */
void PclosestVL3Dfl(float *closest, float *v1, float *v2, float *v3)
{
	float lambda, cp[3], len;

	lambda= lambda_cp_line_ex(v1, v2, v3, cp);

	if(lambda <= 0.0f)
		VecCopyf(closest, v2);
	else if(lambda >= 1.0f)
		VecCopyf(closest, v3);
	else
		VecCopyf(closest, cp);
}

/* distance v1 to line-piece v2-v3 in 3D */
float PdistVL3Dfl(float *v1, float *v2, float *v3) 
{
	float closest[3];

	PclosestVL3Dfl(closest, v1, v2, v3);

	return VecLenf(closest, v1);
}

/********************************************************/

/* make a 4x4 matrix out of 3 transform components */
/* matrices are made in the order: scale * rot * loc */
void LocEulSizeToMat4(float mat[][4], float loc[3], float eul[3], float size[3])
{
	float rmat[3][3], smat[3][3], tmat[3][3];
	
	/* initialise new matrix */
	Mat4One(mat);
	
	/* make rotation + scaling part */
	EulToMat3(eul, rmat);
	SizeToMat3(size, smat);
	Mat3MulMat3(tmat, rmat, smat);
	
	/* copy rot/scale part to output matrix*/
	Mat4CpyMat3(mat, tmat);
	
	/* copy location to matrix */
	mat[3][0] = loc[0];
	mat[3][1] = loc[1];
	mat[3][2] = loc[2];
}

/* make a 4x4 matrix out of 3 transform components */
/* matrices are made in the order: scale * rot * loc */
void LocQuatSizeToMat4(float mat[][4], float loc[3], float quat[4], float size[3])
{
	float rmat[3][3], smat[3][3], tmat[3][3];
	
	/* initialise new matrix */
	Mat4One(mat);
	
	/* make rotation + scaling part */
	QuatToMat3(quat, rmat);
	SizeToMat3(size, smat);
	Mat3MulMat3(tmat, rmat, smat);
	
	/* copy rot/scale part to output matrix*/
	Mat4CpyMat3(mat, tmat);
	
	/* copy location to matrix */
	mat[3][0] = loc[0];
	mat[3][1] = loc[1];
	mat[3][2] = loc[2];
}

