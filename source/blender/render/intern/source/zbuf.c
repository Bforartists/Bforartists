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
 * Contributor(s): Hos, RPW.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

/*---------------------------------------------------------------------------*/
/* Common includes                                                           */
/*---------------------------------------------------------------------------*/

#include <math.h>
#include <stdlib.h>
#include <limits.h>
#include <string.h>
#include "MTC_matrixops.h"
#include "MEM_guardedalloc.h"

#include "DNA_lamp_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_global.h"
#include "BKE_utildefines.h"

#include "radio_types.h"
#include "radio.h"  /* needs RG, some root data for radiosity                */

#include "SDL_thread.h"

#include "render.h"
#include "RE_callbacks.h"

/* local includes */
#include "rendercore.h"  /* shade_pixel and count_mask */
#include "pixelblending.h"
#include "jitter.h"

/* own includes */
#include "zbuf.h"

#define FLT_EPSILON 1.19209290e-07F

/*-----------------------------------------------------------*/ 
/* Globals for this file                                     */
/* main reason for globals; unified zbuffunc() with simple args */
/*-----------------------------------------------------------*/ 

float Zmulx; /* Half the screenwidth, in pixels. (used in render.c, */
             /* zbuf.c)                                             */
float Zmuly; /* Half the screenheight, in pixels. (used in render.c,*/
             /* zbuf.c)                                             */
float Zjitx; /* Jitter offset in x. When jitter is disabled, this   */
             /* should be 0.5. (used in render.c, zbuf.c)           */
float Zjity; /* Jitter offset in y. When jitter is disabled, this   */
             /* should be 0.5. (used in render.c, zbuf.c)           */

int Zsample;
void (*zbuffunc)(ZSpan *, int, float *, float *, float *);
void (*zbuffunc4)(ZSpan *, int, float *, float *, float *, float *);
void (*zbuflinefunc)(int, float *, float *);

static APixstr       *APixbuf;      /* Zbuffer: linked list of face indices       */
static int           *Arectz;       /* Zbuffer: distance buffer, almost obsolete  */
static int            Aminy;        /* y value of first line in the accu buffer   */
static int            Amaxy;        /* y value of last line in the accu buffer    */
static int            Azvoordeel  = 0;
static APixstrMain    apsmfirst;
static short          apsmteller  = 0;

/* ****************** Spans ******************************* */

static void zbuf_alloc_span(ZSpan *zspan, int yres)
{
	zspan->yres= yres;
	
	zspan->span1= MEM_callocN(yres*sizeof(float), "zspan");
	zspan->span2= MEM_callocN(yres*sizeof(float), "zspan");
}

static void zbuf_free_span(ZSpan *zspan)
{
	if(zspan) {
		if(zspan->span1) MEM_freeN(zspan->span1);
		if(zspan->span2) MEM_freeN(zspan->span2);
		zspan->span1= zspan->span2= NULL;
	}
}

static void zbuf_init_span(ZSpan *zspan, int miny, int maxy)
{
	zspan->miny= miny;	/* range for clipping */
	zspan->maxy= maxy;
	zspan->miny1= zspan->miny2= maxy+1;
	zspan->maxy1= zspan->maxy2= miny-1;
	zspan->minp1= zspan->maxp1= zspan->minp2= zspan->maxp2= NULL;
}

static void zbuf_add_to_span(ZSpan *zspan, float *v1, float *v2)
{
	float *minv, *maxv, *span;
	float xx1, dx0, xs0;
	int y, my0, my2;
	
	if(v1[1]<v2[1]) {
		minv= v1; maxv= v2;
	}
	else {
		minv= v2; maxv= v1;
	}
	
	my0= ceil(minv[1]);
	my2= floor(maxv[1]);
	
	if(my2<zspan->miny || my0> zspan->maxy) return;
	
	/* clip top */
	if(my2>=zspan->maxy) my2= zspan->maxy-1;
	/* clip bottom */
	if(my0<zspan->miny) my0= zspan->miny;
	
	if(my0>my2) return;
	/* if(my0>my2) should still fill in, that way we get spans that skip nicely */
	
	xx1= maxv[1]-minv[1];
	if(xx1>FLT_EPSILON) {
		dx0= (minv[0]-maxv[0])/xx1;
		xs0= dx0*(minv[1]-my2) + minv[0];
	}
	else {
		dx0= 0.0f;
		xs0= MIN2(minv[0],maxv[0]);
	}
	
	/* empty span */
	if(zspan->maxp1 == NULL) {
		span= zspan->span1;
	}
	else {	/* does it complete left span? */
		if( maxv == zspan->minp1 || minv==zspan->maxp1) {
			span= zspan->span1;
		}
		else {
			span= zspan->span2;
		}
	}

	if(span==zspan->span1) {
//		printf("left span my0 %d my2 %d\n", my0, my2);
		if(zspan->minp1==NULL || zspan->minp1[1] > minv[1] ) {
			zspan->minp1= minv;
		}
		if(zspan->maxp1==NULL || zspan->maxp1[1] < maxv[1] ) {
			zspan->maxp1= maxv;
		}
		if(my0<zspan->miny1) zspan->miny1= my0;
		if(my2>zspan->maxy1) zspan->maxy1= my2;
	}
	else {
//		printf("right span my0 %d my2 %d\n", my0, my2);
		if(zspan->minp2==NULL || zspan->minp2[1] > minv[1] ) {
			zspan->minp2= minv;
		}
		if(zspan->maxp2==NULL || zspan->maxp2[1] < maxv[1] ) {
			zspan->maxp2= maxv;
		}
		if(my0<zspan->miny2) zspan->miny2= my0;
		if(my2>zspan->maxy2) zspan->maxy2= my2;
	}

	for(y=my2; y>=my0; y--, xs0+= dx0) {
		/* xs0 is the xcoord! */
		span[y]= xs0;
	}
}

/*-----------------------------------------------------------*/ 
/* Functions                                                 */
/*-----------------------------------------------------------*/ 


void fillrect(int *rect, int x, int y, int val)
{
	int len, *drect;

	len= x*y;
	drect= rect;
	while(len>0) {
		len--;
		*drect= val;
		drect++;
	}
}

/**
* Tests whether this coordinate is 'inside' or 'outside' of the view
 * volume? By definition, this is in [0, 1]. 
 * @param p vertex z difference plus coordinate difference?
 * @param q origin z plus r minus some coordinate?
 * @param u1 [in/out] clip fraction for ?
 * @param u2 [in/out]
 * @return 0 if point is outside, or 1 if the point lies on the clip
 *         boundary 
 */
static short cliptestf(float p, float q, float *u1, float *u2)
{
	float r;
	
	if(p<0.0) {
		if(q<p) return 0;
		else if(q<0.0) {
			r= q/p;
			if(r>*u2) return 0;
			else if(r>*u1) *u1=r;
		}
	}
	else {
		if(p>0.0) {
			if(q<0.0) return 0;
			else if(q<p) {
				r= q/p;
				if(r<*u1) return 0;
				else if(r<*u2) *u2=r;
			}
		}
		else if(q<0.0) return 0;
	}
	return 1;
}

int RE_testclip(float *v)
{
	float abs4;	/* WATCH IT: this function should do the same as cliptestf, otherwise troubles in zbufclip()*/
	short c=0;
	
	/* if we set clip flags, the clipping should be at least larger than epsilon. 
	   prevents issues with vertices lying exact on borders */
	abs4= fabs(v[3]) + FLT_EPSILON;
	
	if(v[2]< -abs4) c=16;			/* this used to be " if(v[2]<0) ", see clippz() */
	else if(v[2]> abs4) c+= 32;
	
	if( v[0]>abs4) c+=2;
	else if( v[0]< -abs4) c+=1;
	
	if( v[1]>abs4) c+=4;
	else if( v[1]< -abs4) c+=8;
	
	return c;
}



/* *************  ACCUMULATION ZBUF ************ */

/*-APixstr---------------------(antialised pixel struct)------------------------------*/ 

static APixstr *addpsmainA()
{
	APixstrMain *psm;

	psm= &apsmfirst;

	while(psm->next) {
		psm= psm->next;
	}

	psm->next= MEM_mallocN(sizeof(APixstrMain), "addpsmainA");

	psm= psm->next;
	psm->next=0;
	psm->ps= MEM_callocN(4096*sizeof(APixstr),"pixstr");
	apsmteller= 0;

	return psm->ps;
}

static void freepsA()
{
	APixstrMain *psm, *next;

	psm= &apsmfirst;

	while(psm) {
		next= psm->next;
		if(psm->ps) {
			MEM_freeN(psm->ps);
			psm->ps= 0;
		}
		if(psm!= &apsmfirst) MEM_freeN(psm);
		psm= next;
	}

	apsmfirst.next= 0;
	apsmfirst.ps= 0;
	apsmteller= 0;
}

static APixstr *addpsA(void)
{
	static APixstr *prev;

	/* make first PS */
	if((apsmteller & 4095)==0) prev= addpsmainA();
	else prev++;
	apsmteller++;
	
	return prev;
}

/**
 * Fill the z buffer for accumulation (transparency)
 *
 * This is one of the z buffer fill functions called in zbufclip() and
 * zbufwireclip(). 
 *
 * @param v1 [4 floats, world coordinates] first vertex
 * @param v2 [4 floats, world coordinates] second vertex
 * @param v3 [4 floats, world coordinates] third vertex
 */
static void zbufinvulAc(ZSpan *zspan, int zvlnr, float *v1, float *v2, float *v3)  
{
	APixstr *ap, *apofs, *apn;
	double x0,y0,z0,x1,y1,z1,x2,y2,z2,xx1;
	double zxd,zyd,zy0, tmp;
	float *minv,*maxv,*midv;
	int *rz,zverg,x;
	int my0,my2,sn1,sn2,rectx,zd,*rectzofs;
	int y,omsl,xs0,xs1,xs2,xs3, dx0,dx1,dx2, mask;
	
	/* MIN MAX */
	if(v1[1]<v2[1]) {
		if(v2[1]<v3[1]) 	{
			minv=v1; midv=v2; maxv=v3;
		}
		else if(v1[1]<v3[1]) 	{
			minv=v1; midv=v3; maxv=v2;
		}
		else	{
			minv=v3; midv=v1; maxv=v2;
		}
	}
	else {
		if(v1[1]<v3[1]) 	{
			minv=v2; midv=v1; maxv=v3;
		}
		else if(v2[1]<v3[1]) 	{
			minv=v2; midv=v3; maxv=v1;
		}
		else	{
			minv=v3; midv=v2; maxv=v1;
		}
	}

	if(minv[1] == maxv[1]) return;	/* prevent 'zero' size faces */

	my0= ceil(minv[1]);
	my2= floor(maxv[1]);
	omsl= floor(midv[1]);

	if(my2<Aminy || my0> Amaxy) return;

	if(my0<Aminy) my0= Aminy;

	/* EDGES : LONGEST */
	xx1= maxv[1]-minv[1];
	if(xx1>2.0/65536.0) {
		z0= (maxv[0]-minv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx0= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(my2-minv[1])+minv[0]);
		xs0= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx0= 0;
		xs0= 65536.0*(MIN2(minv[0],maxv[0]));
	}
	/* EDGES : THE TOP ONE */
	xx1= maxv[1]-midv[1];
	if(xx1>2.0/65536.0) {
		z0= (maxv[0]-midv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx1= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(my2-midv[1])+midv[0]);
		xs1= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx1= 0;
		xs1= 65536.0*(MIN2(midv[0],maxv[0]));
	}
	/* EDGES : BOTTOM ONE */
	xx1= midv[1]-minv[1];
	if(xx1>2.0/65536.0) {
		z0= (midv[0]-minv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx2= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(omsl-minv[1])+minv[0]);
		xs2= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx2= 0;
		xs2= 65536.0*(MIN2(minv[0],midv[0]));
	}

	/* ZBUF DX DY */
	x1= v1[0]- v2[0];
	x2= v2[0]- v3[0];
	y1= v1[1]- v2[1];
	y2= v2[1]- v3[1];
	z1= v1[2]- v2[2];
	z2= v2[2]- v3[2];
	x0= y1*z2-z1*y2;
	y0= z1*x2-x1*z2;
	z0= x1*y2-y1*x2;
	if(z0==0.0) return;

	if(midv[1]==maxv[1]) omsl= my2;
	if(omsl<Aminy) omsl= Aminy-1;  /* to make sure it does the first loop completely */

	while (my2 > Amaxy) {  /* my2 can be larger */
		xs0+=dx0;
		if (my2<=omsl) {
			xs2+= dx2;
		}
		else{
			xs1+= dx1;
		}
		my2--;
	}

	xx1= (x0*v1[0]+y0*v1[1])/z0+v1[2];

	zxd= -x0/z0;
	zyd= -y0/z0;
	zy0= my2*zyd+xx1;
	zd= (int)CLAMPIS(zxd, INT_MIN, INT_MAX);

	/* start-offset in rect */
	rectx= R.rectx;
	rectzofs= (int *)(Arectz+rectx*(my2-Aminy));
	apofs= (APixbuf+ rectx*(my2-Aminy));
	mask= 1<<Zsample;

	xs3= 0;		/* flag */
	if(dx0>dx1) {
		xs3= xs0;
		xs0= xs1;
		xs1= xs3;
		xs3= dx0;
		dx0= dx1;
		dx1= xs3;
		xs3= 1;	/* flag */

	}

	for(y=my2;y>omsl;y--) {

		sn1= xs0>>16;
		xs0+= dx0;

		sn2= xs1>>16;
		xs1+= dx1;

		sn1++;

		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		zverg= (int) CLAMPIS((sn1*zxd+zy0), INT_MIN, INT_MAX);
		rz= rectzofs+sn1;
		ap= apofs+sn1;
		x= sn2-sn1;
		
		zverg-= Azvoordeel;
		
		while(x>=0) {
			if(zverg< *rz) {
				apn= ap;
				while(apn) {	/* loop unrolled */
					if(apn->p[0]==0) {apn->p[0]= zvlnr; apn->z[0]= zverg; apn->mask[0]= mask; break; }
					if(apn->p[0]==zvlnr) {apn->mask[0]|= mask; break; }
					if(apn->p[1]==0) {apn->p[1]= zvlnr; apn->z[1]= zverg; apn->mask[1]= mask; break; }
					if(apn->p[1]==zvlnr) {apn->mask[1]|= mask; break; }
					if(apn->p[2]==0) {apn->p[2]= zvlnr; apn->z[2]= zverg; apn->mask[2]= mask; break; }
					if(apn->p[2]==zvlnr) {apn->mask[2]|= mask; break; }
					if(apn->p[3]==0) {apn->p[3]= zvlnr; apn->z[3]= zverg; apn->mask[3]= mask; break; }
					if(apn->p[3]==zvlnr) {apn->mask[3]|= mask; break; }
					if(apn->next==0) apn->next= addpsA();
					apn= apn->next;
				}				
			}
			zverg+= zd;
			rz++; 
			ap++; 
			x--;
		}
		zy0-= zyd;
		rectzofs-= rectx;
		apofs-= rectx;
	}

	if(xs3) {
		xs0= xs1;
		dx0= dx1;
	}
	if(xs0>xs2) {
		xs3= xs0;
		xs0= xs2;
		xs2= xs3;
		xs3= dx0;
		dx0= dx2;
		dx2= xs3;
	}

	for(; y>=my0; y--) {

		sn1= xs0>>16;
		xs0+= dx0;

		sn2= xs2>>16;
		xs2+= dx2;

		sn1++;

		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		zverg= (int) CLAMPIS((sn1*zxd+zy0), INT_MIN, INT_MAX);
		rz= rectzofs+sn1;
		ap= apofs+sn1;
		x= sn2-sn1;

		zverg-= Azvoordeel;

		while(x>=0) {
			if(zverg< *rz) {
				apn= ap;
				while(apn) {	/* loop unrolled */
					if(apn->p[0]==0) {apn->p[0]= zvlnr; apn->z[0]= zverg; apn->mask[0]= mask; break; }
					if(apn->p[0]==zvlnr) {apn->mask[0]|= mask; break; }
					if(apn->p[1]==0) {apn->p[1]= zvlnr; apn->z[1]= zverg; apn->mask[1]= mask; break; }
					if(apn->p[1]==zvlnr) {apn->mask[1]|= mask; break; }
					if(apn->p[2]==0) {apn->p[2]= zvlnr; apn->z[2]= zverg; apn->mask[2]= mask; break; }
					if(apn->p[2]==zvlnr) {apn->mask[2]|= mask; break; }
					if(apn->p[3]==0) {apn->p[3]= zvlnr; apn->z[3]= zverg; apn->mask[3]= mask; break; }
					if(apn->p[3]==zvlnr) {apn->mask[3]|= mask; break; }
					if(apn->next==0) apn->next= addpsA();
					apn= apn->next;
				}
			}
			zverg+= zd;
			rz++; 
			ap++; 
			x--;
		}

		zy0-=zyd;
		rectzofs-= rectx;
		apofs-= rectx;
	}
}

static void zbufinvulAc4(ZSpan *zspan, int zvlnr, float *v1, float *v2, float *v3, float *v4)
{
	APixstr *ap, *apofs, *apn;
	double zxd, zyd, zy0, zverg;
	float x0,y0,z0;
	float x1,y1,z1,x2,y2,z2,xx1;
	float *span1, *span2;
	int *rz, x, y;
	int sn1, sn2, rectx, *rectzofs, my0, my2, mask;
	
	/* init */
	zbuf_init_span(zspan, Aminy, Amaxy+1);
	
	/* set spans */
	zbuf_add_to_span(zspan, v1, v2);
	zbuf_add_to_span(zspan, v2, v3);
	zbuf_add_to_span(zspan, v3, v4);
	zbuf_add_to_span(zspan, v4, v1);
	
	/* clipped */
	if(zspan->minp2==NULL || zspan->maxp2==NULL) return;

	if(zspan->miny1 < zspan->miny2) my0= zspan->miny2; else my0= zspan->miny1;
	if(zspan->maxy1 > zspan->maxy2) my2= zspan->maxy2; else my2= zspan->maxy1;
	
	if(my2<my0) return;
	
	/* ZBUF DX DY, in floats still */
	x1= v1[0]- v2[0];
	x2= v2[0]- v3[0];
	y1= v1[1]- v2[1];
	y2= v2[1]- v3[1];
	z1= v1[2]- v2[2];
	z2= v2[2]- v3[2];
	x0= y1*z2-z1*y2;
	y0= z1*x2-x1*z2;
	z0= x1*y2-y1*x2;
	
	if(z0==0.0) return;
	
	xx1= (x0*v1[0] + y0*v1[1])/z0 + v1[2];
	
	zxd= -(double)x0/(double)z0;
	zyd= -(double)y0/(double)z0;
	zy0= ((double)my2)*zyd + (double)xx1;
	
	/* start-offset in rect */
	rectx= R.rectx;
	rectzofs= (int *)(Arectz+rectx*(my2-Aminy));
	apofs= (APixbuf+ rectx*(my2-Aminy));
	mask= 1<<Zsample;
	
	/* correct span */
	sn1= (my0 + my2)/2;
	if(zspan->span1[sn1] < zspan->span2[sn1]) {
		span1= zspan->span1+my2;
		span2= zspan->span2+my2;
	}
	else {
		span1= zspan->span2+my2;
		span2= zspan->span1+my2;
	}
	
	for(y=my2; y>=my0; y--, span1--, span2--) {
		
		sn1= (int)*span1;
		sn2= (int)*span2;
		sn1++; 
		
		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		
		if(sn2>=sn1) {
			zverg= (double)sn1*zxd + zy0;
			rz= rectzofs+sn1;
			ap= apofs+sn1;
			x= sn2-sn1;
			
			zverg-= Azvoordeel;
			
			while(x>=0) {
				if( (int)zverg < *rz) {
//					int i= zvlnr & 3;
					
					apn= ap;
					while(apn) {
						if(apn->p[0]==0) {apn->p[0]= zvlnr; apn->z[0]= zverg; apn->mask[0]= mask; break; }
						if(apn->p[0]==zvlnr) {apn->mask[0]|= mask; break; }
						if(apn->p[1]==0) {apn->p[1]= zvlnr; apn->z[1]= zverg; apn->mask[1]= mask; break; }
						if(apn->p[1]==zvlnr) {apn->mask[1]|= mask; break; }
						if(apn->p[2]==0) {apn->p[2]= zvlnr; apn->z[2]= zverg; apn->mask[2]= mask; break; }
						if(apn->p[2]==zvlnr) {apn->mask[2]|= mask; break; }
						if(apn->p[3]==0) {apn->p[3]= zvlnr; apn->z[3]= zverg; apn->mask[3]= mask; break; }
						if(apn->p[3]==zvlnr) {apn->mask[3]|= mask; break; }
//						if(apn->p[i]==0) {apn->p[i]= zvlnr; apn->z[i]= zverg; apn->mask[i]= mask; break; }
//						if(apn->p[i]==zvlnr) {apn->mask[i]|= mask; break; }
						if(apn->next==NULL) apn->next= addpsA();
						apn= apn->next;
					}				
				}
				zverg+= zxd;
				rz++; 
				ap++; 
				x--;
			}
		}
		
		zy0-=zyd;
		rectzofs-= rectx;
		apofs-= rectx;
	}
}



static void zbuflineAc(int zvlnr, float *vec1, float *vec2)
{
	APixstr *ap, *apn;
	int *rectz;
	int start, end, x, y, oldx, oldy, ofs;
	int dz, vergz, mask, maxtest=0;
	float dx, dy;
	float v1[3], v2[3];
	
	dx= vec2[0]-vec1[0];
	dy= vec2[1]-vec1[1];
	
	if(fabs(dx) > fabs(dy)) {

		/* all lines from left to right */
		if(vec1[0]<vec2[0]) {
			VECCOPY(v1, vec1);
			VECCOPY(v2, vec2);
		}
		else {
			VECCOPY(v2, vec1);
			VECCOPY(v1, vec2);
			dx= -dx; dy= -dy;
		}

		start= floor(v1[0]);
		end= start+floor(dx);
		if(end>=R.rectx) end= R.rectx-1;
		
		oldy= floor(v1[1]);
		dy/= dx;
		
		vergz= v1[2];
		vergz-= Azvoordeel;
		dz= (v2[2]-v1[2])/dx;
		if(vergz>0x50000000 && dz>0) maxtest= 1;		// prevent overflow
		
		rectz= (int *)(Arectz+R.rectx*(oldy-Aminy) +start);
		ap= (APixbuf+ R.rectx*(oldy-Aminy) +start);
		mask= 1<<Zsample;	
		
		if(dy<0) ofs= -R.rectx;
		else ofs= R.rectx;
		
		for(x= start; x<=end; x++, rectz++, ap++) {
			
			y= floor(v1[1]);
			if(y!=oldy) {
				oldy= y;
				rectz+= ofs;
				ap+= ofs;
			}
			
			if(x>=0 && y>=Aminy && y<=Amaxy) {
				if(vergz<*rectz) {
				
					apn= ap;
					while(apn) {	/* loop unrolled */
						if(apn->p[0]==0) {apn->p[0]= zvlnr; apn->z[0]= vergz; apn->mask[0]= mask; break; }
						if(apn->p[0]==zvlnr) {apn->mask[0]|= mask; break; }
						if(apn->p[1]==0) {apn->p[1]= zvlnr; apn->z[1]= vergz; apn->mask[1]= mask; break; }
						if(apn->p[1]==zvlnr) {apn->mask[1]|= mask; break; }
						if(apn->p[2]==0) {apn->p[2]= zvlnr; apn->z[2]= vergz; apn->mask[2]= mask; break; }
						if(apn->p[2]==zvlnr) {apn->mask[2]|= mask; break; }
						if(apn->p[3]==0) {apn->p[3]= zvlnr; apn->z[3]= vergz; apn->mask[3]= mask; break; }
						if(apn->p[3]==zvlnr) {apn->mask[3]|= mask; break; }
						if(apn->next==0) apn->next= addpsA();
						apn= apn->next;
					}				
					
				}
			}
			
			v1[1]+= dy;
			if(maxtest && (vergz > 0x7FFFFFF0 - dz)) vergz= 0x7FFFFFF0;
			else vergz+= dz;
		}
	}
	else {
	
		/* all lines from top to bottom */
		if(vec1[1]<vec2[1]) {
			VECCOPY(v1, vec1);
			VECCOPY(v2, vec2);
		}
		else {
			VECCOPY(v2, vec1);
			VECCOPY(v1, vec2);
			dx= -dx; dy= -dy;
		}

		start= floor(v1[1]);
		end= start+floor(dy);
		
		if(start>Amaxy || end<Aminy) return;
		
		if(end>Amaxy) end= Amaxy;
		
		oldx= floor(v1[0]);
		dx/= dy;
		
		vergz= v1[2];
		vergz-= Azvoordeel;
		dz= (v2[2]-v1[2])/dy;
		if(vergz>0x50000000 && dz>0) maxtest= 1;		// prevent overflow

		rectz= (int *)( Arectz+ (start-Aminy)*R.rectx+ oldx );
		ap= (APixbuf+ R.rectx*(start-Aminy) +oldx);
		mask= 1<<Zsample;
				
		if(dx<0) ofs= -1;
		else ofs= 1;

		for(y= start; y<=end; y++, rectz+=R.rectx, ap+=R.rectx) {
			
			x= floor(v1[0]);
			if(x!=oldx) {
				oldx= x;
				rectz+= ofs;
				ap+= ofs;
			}
			
			if(x>=0 && y>=Aminy && x<R.rectx) {
				if(vergz<*rectz) {
					
					apn= ap;
					while(apn) {	/* loop unrolled */
						if(apn->p[0]==0) {apn->p[0]= zvlnr; apn->z[0]= vergz; apn->mask[0]= mask; break; }
						if(apn->p[0]==zvlnr) {apn->mask[0]|= mask; break; }
						if(apn->p[1]==0) {apn->p[1]= zvlnr; apn->z[1]= vergz; apn->mask[1]= mask; break; }
						if(apn->p[1]==zvlnr) {apn->mask[1]|= mask; break; }
						if(apn->p[2]==0) {apn->p[2]= zvlnr; apn->z[2]= vergz; apn->mask[2]= mask; break; }
						if(apn->p[2]==zvlnr) {apn->mask[2]|= mask; break; }
						if(apn->p[3]==0) {apn->p[3]= zvlnr; apn->z[3]= vergz; apn->mask[3]= mask; break; }
						if(apn->p[3]==zvlnr) {apn->mask[3]|= mask; break; }
						if(apn->next==0) apn->next= addpsA();
						apn= apn->next;
					}	
					
				}
			}
			
			v1[0]+= dx;
			if(maxtest && (vergz > 0x7FFFFFF0 - dz)) vergz= 0x7FFFFFF0;
			else vergz+= dz;
		}
	}
}



/* *************  NORMAL ZBUFFER ************ */

/**
 * Convert a homogenous coordinate to a z buffer coordinate. The
 * function makes use of Zmulx, Zmuly, the x and y scale factors for
 * the screen, and Zjitx, Zjity, the pixel offset. (These are declared
													* in render.c) The normalised z coordinate must fall on [0, 1]. 
 * @param zco  [3, 4 floats] pointer to the resulting z buffer coordinate
 * @param hoco [4 floats] pointer to the homogenous coordinate of the
 * vertex in world space.
 */
static void hoco_to_zco(float *zco, float *hoco)
{
	float deler;

	deler= hoco[3];
	zco[0]= Zmulx*(1.0+hoco[0]/deler)+ Zjitx;
	zco[1]= Zmuly*(1.0+hoco[1]/deler)+ Zjity;
	zco[2]= 0x7FFFFFFF *(hoco[2]/deler);
}

static void zbufline(int zvlnr, float *vec1, float *vec2)
{
	int *rectz, *rectp;
	int start, end, x, y, oldx, oldy, ofs;
	int dz, vergz, maxtest= 0;
	float dx, dy;
	float v1[3], v2[3];
	
	dx= vec2[0]-vec1[0];
	dy= vec2[1]-vec1[1];
	
	if(fabs(dx) > fabs(dy)) {

		/* all lines from left to right */
		if(vec1[0]<vec2[0]) {
			VECCOPY(v1, vec1);
			VECCOPY(v2, vec2);
		}
		else {
			VECCOPY(v2, vec1);
			VECCOPY(v1, vec2);
			dx= -dx; dy= -dy;
		}

		start= floor(v1[0]);
		end= start+floor(dx);
		if(end>=R.rectx) end= R.rectx-1;
		
		oldy= floor(v1[1]);
		dy/= dx;
		
		vergz= floor(v1[2]);
		dz= floor((v2[2]-v1[2])/dx);
		if(vergz>0x50000000 && dz>0) maxtest= 1;		// prevent overflow
		
		rectz= R.rectz+ oldy*R.rectx+ start;
		rectp= R.rectot+ oldy*R.rectx+ start;
		
		if(dy<0) ofs= -R.rectx;
		else ofs= R.rectx;
		
		for(x= start; x<=end; x++, rectz++, rectp++) {
			
			y= floor(v1[1]);
			if(y!=oldy) {
				oldy= y;
				rectz+= ofs;
				rectp+= ofs;
			}
			
			if(x>=0 && y>=0 && y<R.recty) {
				if(vergz<*rectz) {
					*rectz= vergz;
					*rectp= zvlnr;
				}
			}
			
			v1[1]+= dy;
			
			if(maxtest && (vergz > 0x7FFFFFF0 - dz)) vergz= 0x7FFFFFF0;
			else vergz+= dz;
		}
	}
	else {
		/* all lines from top to bottom */
		if(vec1[1]<vec2[1]) {
			VECCOPY(v1, vec1);
			VECCOPY(v2, vec2);
		}
		else {
			VECCOPY(v2, vec1);
			VECCOPY(v1, vec2);
			dx= -dx; dy= -dy;
		}

		start= floor(v1[1]);
		end= start+floor(dy);
		
		if(end>=R.recty) end= R.recty-1;
		
		oldx= floor(v1[0]);
		dx/= dy;
		
		vergz= floor(v1[2]);
		dz= floor((v2[2]-v1[2])/dy);
		if(vergz>0x50000000 && dz>0) maxtest= 1;		// prevent overflow
		
		rectz= R.rectz+ start*R.rectx+ oldx;
		rectp= R.rectot+ start*R.rectx+ oldx;
		
		if(dx<0) ofs= -1;
		else ofs= 1;

		for(y= start; y<=end; y++, rectz+=R.rectx, rectp+=R.rectx) {
			
			x= floor(v1[0]);
			if(x!=oldx) {
				oldx= x;
				rectz+= ofs;
				rectp+= ofs;
			}
			
			if(x>=0 && y>=0 && x<R.rectx) {
				if(vergz<*rectz) {
					*rectz= vergz;
					*rectp= zvlnr;
				}
			}
			
			v1[0]+= dx;
			if(maxtest && (vergz > 0x7FFFFFF0 - dz)) vergz= 0x7FFFFFF0;
			else vergz+= dz;
		}
	}
}

static void zbufline_onlyZ(int zvlnr, float *vec1, float *vec2)
{
	int *rectz;
	int start, end, x, y, oldx, oldy, ofs;
	int dz, vergz, maxtest= 0;
	float dx, dy;
	float v1[3], v2[3];
	
	dx= vec2[0]-vec1[0];
	dy= vec2[1]-vec1[1];
	
	if(fabs(dx) > fabs(dy)) {
		
		/* all lines from left to right */
		if(vec1[0]<vec2[0]) {
			VECCOPY(v1, vec1);
			VECCOPY(v2, vec2);
		}
		else {
			VECCOPY(v2, vec1);
			VECCOPY(v1, vec2);
			dx= -dx; dy= -dy;
		}
		
		start= floor(v1[0]);
		end= start+floor(dx);
		if(end>=R.rectx) end= R.rectx-1;
		
		oldy= floor(v1[1]);
		dy/= dx;
		
		vergz= floor(v1[2]);
		dz= floor((v2[2]-v1[2])/dx);
		if(vergz>0x50000000 && dz>0) maxtest= 1;		// prevent overflow
		
		rectz= R.rectz+ oldy*R.rectx+ start;
		
		if(dy<0) ofs= -R.rectx;
		else ofs= R.rectx;
		
		for(x= start; x<=end; x++, rectz++) {
			
			y= floor(v1[1]);
			if(y!=oldy) {
				oldy= y;
				rectz+= ofs;
			}
			
			if(x>=0 && y>=0 && y<R.recty) {
				if(vergz<*rectz) {
					*rectz= vergz;
				}
			}
			
			v1[1]+= dy;
			
			if(maxtest && (vergz > 0x7FFFFFF0 - dz)) vergz= 0x7FFFFFF0;
			else vergz+= dz;
		}
	}
	else {
		/* all lines from top to bottom */
		if(vec1[1]<vec2[1]) {
			VECCOPY(v1, vec1);
			VECCOPY(v2, vec2);
		}
		else {
			VECCOPY(v2, vec1);
			VECCOPY(v1, vec2);
			dx= -dx; dy= -dy;
		}
		
		start= floor(v1[1]);
		end= start+floor(dy);
		
		if(end>=R.recty) end= R.recty-1;
		
		oldx= floor(v1[0]);
		dx/= dy;
		
		vergz= floor(v1[2]);
		dz= floor((v2[2]-v1[2])/dy);
		if(vergz>0x50000000 && dz>0) maxtest= 1;		// prevent overflow
		
		rectz= R.rectz+ start*R.rectx+ oldx;
		
		if(dx<0) ofs= -1;
		else ofs= 1;
		
		for(y= start; y<=end; y++, rectz+=R.rectx) {
			
			x= floor(v1[0]);
			if(x!=oldx) {
				oldx= x;
				rectz+= ofs;
			}
			
			if(x>=0 && y>=0 && x<R.rectx) {
				if(vergz<*rectz) {
					*rectz= vergz;
				}
			}
			
			v1[0]+= dx;
			if(maxtest && (vergz > 0x7FFFFFF0 - dz)) vergz= 0x7FFFFFF0;
			else vergz+= dz;
		}
	}
}


static int clipline(float *v1, float *v2)	/* return 0: do not draw */
{
	float dz,dw, u1=0.0, u2=1.0;
	float dx, dy, v13;
	
	dz= v2[2]-v1[2];
	dw= v2[3]-v1[3];
	
	/* this 1.01 is for clipping x and y just a tinsy larger. that way it is
		filled in with zbufwire correctly when rendering in parts. otherwise
		you see line endings at edges... */
	
	if(cliptestf(-dz-dw, v1[3]+v1[2], &u1,&u2)) {
		if(cliptestf(dz-dw, v1[3]-v1[2], &u1,&u2)) {
			
			dx= v2[0]-v1[0];
			dz= 1.01*(v2[3]-v1[3]);
			v13= 1.01*v1[3];
			
			if(cliptestf(-dx-dz, v1[0]+v13, &u1,&u2)) {
				if(cliptestf(dx-dz, v13-v1[0], &u1,&u2)) {
					
					dy= v2[1]-v1[1];
					
					if(cliptestf(-dy-dz, v1[1]+v13, &u1,&u2)) {
						if(cliptestf(dy-dz, v13-v1[1], &u1,&u2)) {
							
							if(u2<1.0) {
								v2[0]= v1[0]+u2*dx;
								v2[1]= v1[1]+u2*dy;
								v2[2]= v1[2]+u2*dz;
								v2[3]= v1[3]+u2*dw;
							}
							if(u1>0.0) {
								v1[0]= v1[0]+u1*dx;
								v1[1]= v1[1]+u1*dy;
								v1[2]= v1[2]+u1*dz;
								v1[3]= v1[3]+u1*dw;
							}
							return 1;
						}
					}
				}
			}
		}
	}
	
	return 0;
}


void zbufclipwire(int zvlnr, VlakRen *vlr)
{
	float vez[20], *f1, *f2, *f3, *f4= 0,  deler;
	int c1, c2, c3, c4, ec, and, or;

	/* edgecode: 1= draw */
	ec = vlr->ec;
	if(ec==0) return;

	c1= vlr->v1->clip;
	c2= vlr->v2->clip;
	c3= vlr->v3->clip;
	f1= vlr->v1->ho;
	f2= vlr->v2->ho;
	f3= vlr->v3->ho;
	
	if(vlr->v4) {
		f4= vlr->v4->ho;
		c4= vlr->v4->clip;
		
		and= (c1 & c2 & c3 & c4);
		or= (c1 | c2 | c3 | c4);
	}
	else {
		and= (c1 & c2 & c3);
		or= (c1 | c2 | c3);
	}
	
	if(or) {	/* not in the middle */
		if(and) {	/* out completely */
			return;
		}
		else {	/* clipping */

			if(ec & ME_V1V2) {
				QUATCOPY(vez, f1);
				QUATCOPY(vez+4, f2);
				if( clipline(vez, vez+4)) {
					hoco_to_zco(vez, vez);
					hoco_to_zco(vez+4, vez+4);
					zbuflinefunc(zvlnr, vez, vez+4);
				}
			}
			if(ec & ME_V2V3) {
				QUATCOPY(vez, f2);
				QUATCOPY(vez+4, f3);
				if( clipline(vez, vez+4)) {
					hoco_to_zco(vez, vez);
					hoco_to_zco(vez+4, vez+4);
					zbuflinefunc(zvlnr, vez, vez+4);
				}
			}
			if(vlr->v4) {
				if(ec & ME_V3V4) {
					QUATCOPY(vez, f3);
					QUATCOPY(vez+4, f4);
					if( clipline(vez, vez+4)) {
						hoco_to_zco(vez, vez);
						hoco_to_zco(vez+4, vez+4);
						zbuflinefunc(zvlnr, vez, vez+4);
					}
				}
				if(ec & ME_V4V1) {
					QUATCOPY(vez, f4);
					QUATCOPY(vez+4, f1);
					if( clipline(vez, vez+4)) {
						hoco_to_zco(vez, vez);
						hoco_to_zco(vez+4, vez+4);
						zbuflinefunc(zvlnr, vez, vez+4);
					}
				}
			}
			else {
				if(ec & ME_V3V1) {
					QUATCOPY(vez, f3);
					QUATCOPY(vez+4, f1);
					if( clipline(vez, vez+4)) {
						hoco_to_zco(vez, vez);
						hoco_to_zco(vez+4, vez+4);
						zbuflinefunc(zvlnr, vez, vez+4);
					}
				}
			}
			
			return;
		}
	}

	deler= f1[3];
	vez[0]= Zmulx*(1.0+f1[0]/deler)+ Zjitx;
	vez[1]= Zmuly*(1.0+f1[1]/deler)+ Zjity;
	vez[2]= 0x7FFFFFFF *(f1[2]/deler);

	deler= f2[3];
	vez[4]= Zmulx*(1.0+f2[0]/deler)+ Zjitx;
	vez[5]= Zmuly*(1.0+f2[1]/deler)+ Zjity;
	vez[6]= 0x7FFFFFFF *(f2[2]/deler);

	deler= f3[3];
	vez[8]= Zmulx*(1.0+f3[0]/deler)+ Zjitx;
	vez[9]= Zmuly*(1.0+f3[1]/deler)+ Zjity;
	vez[10]= 0x7FFFFFFF *(f3[2]/deler);
	
	if(vlr->v4) {
		deler= f4[3];
		vez[12]= Zmulx*(1.0+f4[0]/deler)+ Zjitx;
		vez[13]= Zmuly*(1.0+f4[1]/deler)+ Zjity;
		vez[14]= 0x7FFFFFFF *(f4[2]/deler);

		if(ec & ME_V3V4)  zbuflinefunc(zvlnr, vez+8, vez+12);
		if(ec & ME_V4V1)  zbuflinefunc(zvlnr, vez+12, vez);
	}
	else {
		if(ec & ME_V3V1)  zbuflinefunc(zvlnr, vez+8, vez);
	}

	if(ec & ME_V1V2)  zbuflinefunc(zvlnr, vez, vez+4);
	if(ec & ME_V2V3)  zbuflinefunc(zvlnr, vez+4, vez+8);

}

/**
 * Fill the z buffer, but invert z order, and add the face index to
 * the corresponing face buffer.
 *
 * This is one of the z buffer fill functions called in zbufclip() and
 * zbufwireclip(). 
 *
 * @param v1 [4 floats, world coordinates] first vertex
 * @param v2 [4 floats, world coordinates] second vertex
 * @param v3 [4 floats, world coordinates] third vertex
 */
static void zbufinvulGLinv(ZSpan *zspan, int zvlnr, float *v1, float *v2, float *v3) 
{
	double x0,y0,z0,x1,y1,z1,x2,y2,z2,xx1;
	double zxd,zyd,zy0,tmp;
	float *minv,*maxv,*midv;
	int *rectpofs,*rp;
	int *rz,zverg,zvlak,x;
	int my0,my2,sn1,sn2,rectx,zd,*rectzofs;
	int y,omsl,xs0,xs1,xs2,xs3, dx0,dx1,dx2;
	
	/* MIN MAX */
	if(v1[1]<v2[1]) {
		if(v2[1]<v3[1]) 	{
			minv=v1;  midv=v2;  maxv=v3;
		}
		else if(v1[1]<v3[1]) 	{
			minv=v1;  midv=v3;  maxv=v2;
		}
		else	{
			minv=v3;  midv=v1;  maxv=v2;
		}
	}
	else {
		if(v1[1]<v3[1]) 	{
			minv=v2;  midv=v1; maxv=v3;
		}
		else if(v2[1]<v3[1]) 	{
			minv=v2;  midv=v3;  maxv=v1;
		}
		else	{
			minv=v3;  midv=v2;  maxv=v1;
		}
	}

	my0= ceil(minv[1]);
	my2= floor(maxv[1]);
	omsl= floor(midv[1]);

	if(my2<0 || my0> R.recty) return;

	if(my0<0) my0=0;

	/* EDGES : LONGEST */
	xx1= maxv[1]-minv[1];
	if(xx1>2.0/65536.0) {
		z0= (maxv[0]-minv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx0= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(my2-minv[1])+minv[0]);
		xs0= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx0= 0;
		xs0= 65536.0*(MIN2(minv[0],maxv[0]));
	}
	/* EDGES : THE TOP ONE */
	xx1= maxv[1]-midv[1];
	if(xx1>2.0/65536.0) {
		z0= (maxv[0]-midv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx1= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(my2-midv[1])+midv[0]);
		xs1= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx1= 0;
		xs1= 65536.0*(MIN2(midv[0],maxv[0]));
	}
	/* EDGES : THE BOTTOM ONE */
	xx1= midv[1]-minv[1];
	if(xx1>2.0/65536.0) {
		z0= (midv[0]-minv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx2= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(omsl-minv[1])+minv[0]);
		xs2= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx2= 0;
		xs2= 65536.0*(MIN2(minv[0],midv[0]));
	}

	/* ZBUF DX DY */
	x1= v1[0]- v2[0];
	x2= v2[0]- v3[0];
	y1= v1[1]- v2[1];
	y2= v2[1]- v3[1];
	z1= v1[2]- v2[2];
	z2= v2[2]- v3[2];
	x0= y1*z2-z1*y2;
	y0= z1*x2-x1*z2;
	z0= x1*y2-y1*x2;

	if(z0==0.0) return;

	if(midv[1]==maxv[1]) omsl= my2;
	if(omsl<0) omsl= -1;  /* then it does the first loop entirely */

	while (my2 >= R.recty) {  /* my2 can be larger */
		xs0+=dx0;
		if (my2<=omsl) {
			xs2+= dx2;
		}
		else{
			xs1+= dx1;
		}
		my2--;
	}

	xx1= (x0*v1[0]+y0*v1[1])/z0+v1[2];

	zxd= -x0/z0;
	zyd= -y0/z0;
	zy0= my2*zyd+xx1;
	zd= (int)CLAMPIS(zxd, INT_MIN, INT_MAX);

	/* start-offset in rect */
	rectx= R.rectx;
	rectzofs= (int *)(R.rectz+rectx*my2);
	rectpofs= (R.rectot+rectx*my2);
	zvlak= zvlnr;

	xs3= 0;		/* flag */
	if(dx0>dx1) {
		xs3= xs0;
		xs0= xs1;
		xs1= xs3;
		xs3= dx0;
		dx0= dx1;
		dx1= xs3;
		xs3= 1;	/* flag */

	}

	for(y=my2;y>omsl;y--) {

		sn1= xs0>>16;
		xs0+= dx0;

		sn2= xs1>>16;
		xs1+= dx1;

		sn1++;

		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		zverg= (int) CLAMPIS((sn1*zxd+zy0), INT_MIN, INT_MAX);
		rz= rectzofs+sn1;
		rp= rectpofs+sn1;
		x= sn2-sn1;
		while(x>=0) {
			if(zverg> *rz || *rz==0x7FFFFFFF) {
				*rz= zverg;
				*rp= zvlak;
			}
			zverg+= zd;
			rz++; 
			rp++; 
			x--;
		}
		zy0-=zyd;
		rectzofs-= rectx;
		rectpofs-= rectx;
	}

	if(xs3) {
		xs0= xs1;
		dx0= dx1;
	}
	if(xs0>xs2) {
		xs3= xs0;
		xs0= xs2;
		xs2= xs3;
		xs3= dx0;
		dx0= dx2;
		dx2= xs3;
	}

	for(;y>=my0;y--) {

		sn1= xs0>>16;
		xs0+= dx0;

		sn2= xs2>>16;
		xs2+= dx2;

		sn1++;

		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		zverg= (int) CLAMPIS((sn1*zxd+zy0), INT_MIN, INT_MAX);
		rz= rectzofs+sn1;
		rp= rectpofs+sn1;
		x= sn2-sn1;
		while(x>=0) {
			if(zverg> *rz || *rz==0x7FFFFFFF) {
				*rz= zverg;
				*rp= zvlak;
			}
			zverg+= zd;
			rz++; 
			rp++; 
			x--;
		}

		zy0-=zyd;
		rectzofs-= rectx;
		rectpofs-= rectx;
	}
}

/* uses spanbuffers */

static void zbufinvulGL4(ZSpan *zspan, int zvlnr, float *v1, float *v2, float *v3, float *v4)
{
	double zxd, zyd, zy0, zverg;
	float x0,y0,z0;
	float x1,y1,z1,x2,y2,z2,xx1;
	float *span1, *span2;
	int *rectpofs, *rp;
	int *rz, x, y;
	int sn1, sn2, rectx, *rectzofs, my0, my2;
	
	/* init */
	zbuf_init_span(zspan, 0, R.recty);
	
	/* set spans */
	zbuf_add_to_span(zspan, v1, v2);
	zbuf_add_to_span(zspan, v2, v3);
	zbuf_add_to_span(zspan, v3, v4);
	zbuf_add_to_span(zspan, v4, v1);
	
	/* clipped */
	if(zspan->minp2==NULL || zspan->maxp2==NULL) return;
	
	if(zspan->miny1 < zspan->miny2) my0= zspan->miny2; else my0= zspan->miny1;
	if(zspan->maxy1 > zspan->maxy2) my2= zspan->maxy2; else my2= zspan->maxy1;
	
//	printf("my %d %d\n", my0, my2);
	if(my2<my0) return;
	
	
	/* ZBUF DX DY, in floats still */
	x1= v1[0]- v2[0];
	x2= v2[0]- v3[0];
	y1= v1[1]- v2[1];
	y2= v2[1]- v3[1];
	z1= v1[2]- v2[2];
	z2= v2[2]- v3[2];
	x0= y1*z2-z1*y2;
	y0= z1*x2-x1*z2;
	z0= x1*y2-y1*x2;
	
	if(z0==0.0) return;

	xx1= (x0*v1[0] + y0*v1[1])/z0 + v1[2];

	zxd= -(double)x0/(double)z0;
	zyd= -(double)y0/(double)z0;
	zy0= ((double)my2)*zyd + (double)xx1;

	/* start-offset in rect */
	rectx= R.rectx;
	rectzofs= (int *)(R.rectz+rectx*my2);
	rectpofs= (R.rectot+rectx*my2);

	/* correct span */
	sn1= (my0 + my2)/2;
	if(zspan->span1[sn1] < zspan->span2[sn1]) {
		span1= zspan->span1+my2;
		span2= zspan->span2+my2;
	}
	else {
		span1= zspan->span2+my2;
		span2= zspan->span1+my2;
	}
	
	for(y=my2; y>=my0; y--, span1--, span2--) {
		
		sn1= (int)*span1;
		sn2= (int)*span2;
		sn1++; 
		
		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		
		if(sn2>=sn1) {
			zverg= (double)sn1*zxd + zy0;
			rz= rectzofs+sn1;
			rp= rectpofs+sn1;
			x= sn2-sn1;
			
			while(x>=0) {
				if( (int)zverg < *rz) {
					*rz= (int)zverg;
					*rp= zvlnr;
				}
				zverg+= zxd;
				rz++; 
				rp++; 
				x--;
			}
		}
		
		zy0-=zyd;
		rectzofs-= rectx;
		rectpofs-= rectx;
	}
}

static void zbufinvulGL(ZSpan *zspan, int zvlnr, float *v1, float *v2, float *v3)
{
	double x0,y0,z0;
	double x1,y1,z1,x2,y2,z2,xx1;
	double zxd, zyd, zy0, zverg, zd;
	float *span1, *span2;
	int *rectpofs, *rp;
	int *rz, zvlak, x, y, my0, my2;
	int sn1,sn2, rectx, *rectzofs;
	
	/* init */
	zbuf_init_span(zspan, 0, R.recty);
	
	/* set spans */
	zbuf_add_to_span(zspan, v1, v2);
	zbuf_add_to_span(zspan, v2, v3);
	zbuf_add_to_span(zspan, v3, v1);
	
	/* clipped */
	if(zspan->minp2==NULL || zspan->maxp2==NULL) return;
	
	if(zspan->miny1 < zspan->miny2) my0= zspan->miny2; else my0= zspan->miny1;
	if(zspan->maxy1 > zspan->maxy2) my2= zspan->maxy2; else my2= zspan->maxy1;
	
	if(my2<my0) return;
	
	/* ZBUF DX DY */
	x1= v1[0]- v2[0];
	x2= v2[0]- v3[0];
	y1= v1[1]- v2[1];
	y2= v2[1]- v3[1];
	z1= v1[2]- v2[2];
	z2= v2[2]- v3[2];
	x0= y1*z2-z1*y2;
	y0= z1*x2-x1*z2;
	z0= x1*y2-y1*x2;
	
	if(z0==0.0) return;
	
	xx1= (x0*v1[0]+y0*v1[1])/z0+v1[2];
	
	zxd= -x0/z0;
	zyd= -y0/z0;
	zy0= my2*zyd+xx1;
	zd= zxd;
	
	/* start-offset in rect */
	rectx= R.rectx;
	rectzofs= (int *)(R.rectz+rectx*my2);
	rectpofs= (R.rectot+rectx*my2);
	zvlak= zvlnr;
	
	/* find correct span */
	sn1= (my0 + my2)/2;
	if(zspan->span1[sn1] < zspan->span2[sn1]) {
		span1= zspan->span1+my2;
		span2= zspan->span2+my2;
	}
	else {
		span1= zspan->span2+my2;
		span2= zspan->span1+my2;
	}
	
	for(y=my2; y>=my0; y--, span1--, span2--) {
		
		sn1= (int)*span1;
		sn2= (int)*span2;
		
		sn1++; 
		
		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		
		if(sn2>=sn1) {
			zverg= sn1*zxd+zy0;
			rz= rectzofs+sn1;
			rp= rectpofs+sn1;
			x= sn2-sn1;
			
			while(x>=0) {
				if(zverg< *rz) {
					*rz= floor(zverg);
					*rp= zvlak;
				}
				zverg+= zd;
				rz++; 
				rp++; 
				x--;
			}
		}
		
		zy0-=zyd;
		rectzofs-= rectx;
		rectpofs-= rectx;
	}
}



/**
 * Fill the z buffer. The face buffer is not operated on!
 *
 * This is one of the z buffer fill functions called in zbufclip() and
 * zbufwireclip(). 
 *
 * @param v1 [4 floats, world coordinates] first vertex
 * @param v2 [4 floats, world coordinates] second vertex
 * @param v3 [4 floats, world coordinates] third vertex
 */

static void zbufinvulGL_onlyZ(ZSpan *zspan, int zvlnr, float *v1, float *v2, float *v3) 
{
	double x0,y0,z0,x1,y1,z1,x2,y2,z2,xx1;
	double zxd,zyd,zy0,tmp;
	float *minv,*maxv,*midv;
	int *rz,zverg,x;
	int my0,my2,sn1,sn2,rectx,zd,*rectzofs;
	int y,omsl,xs0,xs1,xs2,xs3, dx0,dx1,dx2;
	
	/* MIN MAX */
	if(v1[1]<v2[1]) {
		if(v2[1]<v3[1]) 	{
			minv=v1; 
			midv=v2; 
			maxv=v3;
		}
		else if(v1[1]<v3[1]) 	{
			minv=v1; 
			midv=v3; 
			maxv=v2;
		}
		else	{
			minv=v3; 
			midv=v1; 
			maxv=v2;
		}
	}
	else {
		if(v1[1]<v3[1]) 	{
			minv=v2; 
			midv=v1; 
			maxv=v3;
		}
		else if(v2[1]<v3[1]) 	{
			minv=v2; 
			midv=v3; 
			maxv=v1;
		}
		else	{
			minv=v3; 
			midv=v2; 
			maxv=v1;
		}
	}

	my0= ceil(minv[1]);
	my2= floor(maxv[1]);
	omsl= floor(midv[1]);

	if(my2<0 || my0> R.recty) return;

	if(my0<0) my0=0;

	/* EDGES : LONGEST */
	xx1= maxv[1]-minv[1];
	if(xx1!=0.0) {
		z0= (maxv[0]-minv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx0= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(my2-minv[1])+minv[0]);
		xs0= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx0= 0;
		xs0= 65536.0*(MIN2(minv[0],maxv[0]));
	}
	/* EDGES : TOP */
	xx1= maxv[1]-midv[1];
	if(xx1!=0.0) {
		z0= (maxv[0]-midv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx1= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(my2-midv[1])+midv[0]);
		xs1= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx1= 0;
		xs1= 65536.0*(MIN2(midv[0],maxv[0]));
	}
	/* EDGES : BOTTOM */
	xx1= midv[1]-minv[1];
	if(xx1!=0.0) {
		z0= (midv[0]-minv[0])/xx1;
		
		tmp= (-65536.0*z0);
		dx2= CLAMPIS(tmp, INT_MIN, INT_MAX);
		
		tmp= 65536.0*(z0*(omsl-minv[1])+minv[0]);
		xs2= CLAMPIS(tmp, INT_MIN, INT_MAX);
	}
	else {
		dx2= 0;
		xs2= 65536.0*(MIN2(minv[0],midv[0]));
	}

	/* ZBUF DX DY */
	x1= v1[0]- v2[0];
	x2= v2[0]- v3[0];
	y1= v1[1]- v2[1];
	y2= v2[1]- v3[1];
	z1= v1[2]- v2[2];
	z2= v2[2]- v3[2];
	x0= y1*z2-z1*y2;
	y0= z1*x2-x1*z2;
	z0= x1*y2-y1*x2;

	if(z0==0.0) return;

	if(midv[1]==maxv[1]) omsl= my2;
	if(omsl<0) omsl= -1;  /* then it takes first loop entirely */

	while (my2 >= R.recty) {  /* my2 can be larger */
		xs0+=dx0;
		if (my2<=omsl) {
			xs2+= dx2;
		}
		else{
			xs1+= dx1;
		}
		my2--;
	}

	xx1= (x0*v1[0]+y0*v1[1])/z0+v1[2];

	zxd= -x0/z0;
	zyd= -y0/z0;
	zy0= my2*zyd+xx1;
	zd= (int)CLAMPIS(zxd, INT_MIN, INT_MAX);

	/* start-offset in rect */
	rectx= R.rectx;
	rectzofs= (int *)(R.rectz+rectx*my2);

	xs3= 0;		/* flag */
	if(dx0>dx1) {
		xs3= xs0;
		xs0= xs1;
		xs1= xs3;
		xs3= dx0;
		dx0= dx1;
		dx1= xs3;
		xs3= 1;	/* flag */

	}

	for(y=my2;y>omsl;y--) {

		sn1= xs0>>16;
		xs0+= dx0;

		sn2= xs1>>16;
		xs1+= dx1;

		sn1++;

		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		zverg= (int) CLAMPIS((sn1*zxd+zy0), INT_MIN, INT_MAX);
		rz= rectzofs+sn1;

		x= sn2-sn1;
		while(x>=0) {
			if(zverg< *rz) {
				*rz= zverg;
			}
			zverg+= zd;
			rz++; 
			x--;
		}
		zy0-=zyd;
		rectzofs-= rectx;
	}

	if(xs3) {
		xs0= xs1;
		dx0= dx1;
	}
	if(xs0>xs2) {
		xs3= xs0;
		xs0= xs2;
		xs2= xs3;
		xs3= dx0;
		dx0= dx2;
		dx2= xs3;
	}

	for(;y>=my0;y--) {

		sn1= xs0>>16;
		xs0+= dx0;

		sn2= xs2>>16;
		xs2+= dx2;

		sn1++;

		if(sn2>=rectx) sn2= rectx-1;
		if(sn1<0) sn1= 0;
		zverg= (int) CLAMPIS((sn1*zxd+zy0), INT_MIN, INT_MAX);
		rz= rectzofs+sn1;

		x= sn2-sn1;
		while(x>=0) {
			if(zverg< *rz) {
				*rz= zverg;
			}
			zverg+= zd;
			rz++; 
			x--;
		}

		zy0-=zyd;
		rectzofs-= rectx;
	}
}


/**
 * (clip pyramid)
 * Sets labda: flag, and parametrize the clipping of vertices in
 * viewspace coordinates. labda = -1 means no clipping, labda in [0,
	 * 1] means a clipping.
 * Note: uses globals.
 * @param v1 start coordinate s
 * @param v2 target coordinate t
 * @param b1 
 * @param b2 
 * @param b3
 * @param a index for coordinate (x, y, or z)
 */

static void clippyra(float *labda, float *v1, float *v2, int *b2, int *b3, int a)
{
	float da,db,u1=0.0,u2=1.0;

	labda[0]= -1.0;
	labda[1]= -1.0;

	da= v2[a]-v1[a];
	db= v2[3]-v1[3];

	/* according the original article by Liang&Barsky, for clipping of
	 * homeginic coordinates with viewplane, the value of "0" is used instead of "-w" .
	 * This differs from the other clipping cases (like left or top) and I considered
	 * it to be not so 'homogenic'. But later it has proven to be an error,
	 * who would have thought that of L&B!
	 */

	if(cliptestf(-da-db, v1[3]+v1[a], &u1,&u2)) {
		if(cliptestf(da-db, v1[3]-v1[a], &u1,&u2)) {
			*b3=1;
			if(u2<1.0) {
				labda[1]= u2;
				*b2=1;
			}
			else labda[1]=1.0;  /* u2 */
			if(u1>0.0) {
				labda[0]= u1;
				*b2=1;
			} else labda[0]=0.0;
		}
	}
}

/**
 * (make vertex pyramide clip)
 * Checks labda and uses this to make decision about clipping the line
 * segment from v1 to v2. labda is the factor by which the vector is
 * cut. ( calculate s + l * ( t - s )). The result is appended to the
 * vertex list of this face.
 * 
 * 
 * @param v1 start coordinate s
 * @param v2 target coordinate t
 * @param b1 
 * @param b2 
 * @param clve vertex vector.
 */

static void makevertpyra(float *vez, float *labda, float **trias, float *v1, float *v2, int *b1, int *clve)
{
	float l1, l2, *adr;

	l1= labda[0];
	l2= labda[1];

	if(l1!= -1.0) {
		if(l1!= 0.0) {
			adr= vez+4*(*clve);
			trias[*b1]=adr;
			(*clve)++;
			adr[0]= v1[0]+l1*(v2[0]-v1[0]);
			adr[1]= v1[1]+l1*(v2[1]-v1[1]);
			adr[2]= v1[2]+l1*(v2[2]-v1[2]);
			adr[3]= v1[3]+l1*(v2[3]-v1[3]);
		} 
		else trias[*b1]= v1;
		
		(*b1)++;
	}
	if(l2!= -1.0) {
		if(l2!= 1.0) {
			adr= vez+4*(*clve);
			trias[*b1]=adr;
			(*clve)++;
			adr[0]= v1[0]+l2*(v2[0]-v1[0]);
			adr[1]= v1[1]+l2*(v2[1]-v1[1]);
			adr[2]= v1[2]+l2*(v2[2]-v1[2]);
			adr[3]= v1[3]+l2*(v2[3]-v1[3]);
			(*b1)++;
		}
	}
}

/* ------------------------------------------------------------------------- */

void RE_projectverto(float *v1, float *adr)
{
	/* calcs homogenic coord of vertex v1 */
	float x,y,z;

	x= v1[0]; 
	y= v1[1]; 
	z= v1[2];
	adr[0]= x*R.winmat[0][0]				+	z*R.winmat[2][0] + R.winmat[3][0];
	adr[1]= 		      y*R.winmat[1][1]	+	z*R.winmat[2][1] + R.winmat[3][1];
	adr[2]=										z*R.winmat[2][2] + R.winmat[3][2];
	adr[3]=										z*R.winmat[2][3] + R.winmat[3][3];

	//printf("hoco %f %f %f %f\n", adr[0], adr[1], adr[2], adr[3]);
}

/* ------------------------------------------------------------------------- */

void projectvert(float *v1, float *adr)
{
	/* calcs homogenic coord of vertex v1 */
	float x,y,z;

	x= v1[0]; 
	y= v1[1]; 
	z= v1[2];
	adr[0]= x*R.winmat[0][0]+ y*R.winmat[1][0]+ z*R.winmat[2][0]+ R.winmat[3][0];
	adr[1]= x*R.winmat[0][1]+ y*R.winmat[1][1]+ z*R.winmat[2][1]+ R.winmat[3][1];
	adr[2]= x*R.winmat[0][2]+ y*R.winmat[1][2]+ z*R.winmat[2][2]+ R.winmat[3][2];
	adr[3]= x*R.winmat[0][3]+ y*R.winmat[1][3]+ z*R.winmat[2][3]+ R.winmat[3][3];
}

/* do zbuffering and clip, f1 f2 f3 are hocos, c1 c2 c3 are clipping flags */

void zbufclip(ZSpan *zspan, int zvlnr, float *f1, float *f2, float *f3, int c1, int c2, int c3)
{
	float deler;
	float *vlzp[32][3], labda[3][2];
	float vez[400], *trias[40];

	if(c1 | c2 | c3) {	/* not in middle */
		if(c1 & c2 & c3) {	/* completely out */
			return;
		} else {	/* clipping */
			int arg, v, b, clipflag[3], b1, b2, b3, c4, clve=3, clvlo, clvl=1;

			vez[0]= f1[0]; vez[1]= f1[1]; vez[2]= f1[2]; vez[3]= f1[3];
			vez[4]= f2[0]; vez[5]= f2[1]; vez[6]= f2[2]; vez[7]= f2[3];
			vez[8]= f3[0]; vez[9]= f3[1]; vez[10]= f3[2];vez[11]= f3[3];

			vlzp[0][0]= vez;
			vlzp[0][1]= vez+4;
			vlzp[0][2]= vez+8;

			clipflag[0]= ( (c1 & 48) | (c2 & 48) | (c3 & 48) );
			if(clipflag[0]==0) {	/* othwerwise it needs to be calculated again, after the first (z) clip */
				clipflag[1]= ( (c1 & 3) | (c2 & 3) | (c3 & 3) );
				clipflag[2]= ( (c1 & 12) | (c2 & 12) | (c3 & 12) );
			}
			
			for(b=0;b<3;b++) {
				
				if(clipflag[b]) {
				
					clvlo= clvl;
					
					for(v=0; v<clvlo; v++) {
					
						if(vlzp[v][0]!=0) {	/* face is still there */
							b2= b3 =0;	/* clip flags */

							if(b==0) arg= 2;
							else if (b==1) arg= 0;
							else arg= 1;
							
							clippyra(labda[0], vlzp[v][0],vlzp[v][1], &b2,&b3, arg);
							clippyra(labda[1], vlzp[v][1],vlzp[v][2], &b2,&b3, arg);
							clippyra(labda[2], vlzp[v][2],vlzp[v][0], &b2,&b3, arg);

							if(b2==0 && b3==1) {
								/* completely 'in' */;
							} else if(b3==0) {
								vlzp[v][0]=0;
								/* completely 'out' */;
							} else {
								b1=0;
								makevertpyra(vez, labda[0], trias, vlzp[v][0],vlzp[v][1], &b1,&clve);
								makevertpyra(vez, labda[1], trias, vlzp[v][1],vlzp[v][2], &b1,&clve);
								makevertpyra(vez, labda[2], trias, vlzp[v][2],vlzp[v][0], &b1,&clve);

								/* after front clip done: now set clip flags */
								if(b==0) {
									clipflag[1]= clipflag[2]= 0;
									f1= vez;
									for(b3=0; b3<clve; b3++) {
										c4= RE_testclip(f1);
										clipflag[1] |= (c4 & 3);
										clipflag[2] |= (c4 & 12);
										f1+= 4;
									}
								}
								
								vlzp[v][0]=0;
								if(b1>2) {
									for(b3=3; b3<=b1; b3++) {
										vlzp[clvl][0]= trias[0];
										vlzp[clvl][1]= trias[b3-2];
										vlzp[clvl][2]= trias[b3-1];
										clvl++;
									}
								}
							}
						}
					}
				}
			}

            /* warning, this should never happen! */
			if(clve>38 || clvl>31) printf("clip overflow: clve clvl %d %d\n",clve,clvl);

            /* perspective division */
			f1=vez;
			for(c1=0;c1<clve;c1++) {
				deler= f1[3];
				f1[0]= Zmulx*(1.0+f1[0]/deler)+ Zjitx;
				f1[1]= Zmuly*(1.0+f1[1]/deler)+ Zjity;
				f1[2]= 0x7FFFFFFF *(f1[2]/deler);
				f1+=4;
			}
			for(b=1;b<clvl;b++) {
				if(vlzp[b][0]) {
					zbuffunc(zspan, zvlnr, vlzp[b][0],vlzp[b][1],vlzp[b][2]);
				}
			}
			return;
		}
	}

	/* perspective division: HCS to ZCS */
	
	deler= f1[3];
	vez[0]= Zmulx*(1.0+f1[0]/deler)+ Zjitx;
	vez[1]= Zmuly*(1.0+f1[1]/deler)+ Zjity;
	vez[2]= 0x7FFFFFFF *(f1[2]/deler);

	deler= f2[3];
	vez[4]= Zmulx*(1.0+f2[0]/deler)+ Zjitx;
	vez[5]= Zmuly*(1.0+f2[1]/deler)+ Zjity;
	vez[6]= 0x7FFFFFFF *(f2[2]/deler);

	deler= f3[3];
	vez[8]= Zmulx*(1.0+f3[0]/deler)+ Zjitx;
	vez[9]= Zmuly*(1.0+f3[1]/deler)+ Zjity;
	vez[10]= 0x7FFFFFFF *(f3[2]/deler);

	zbuffunc(zspan, zvlnr, vez,vez+4,vez+8);
}

static void zbufclip4(ZSpan *zspan, int zvlnr, float *f1, float *f2, float *f3, float *f4, int c1, int c2, int c3, int c4)
{
	float div;
	float vez[16];
	
	if(c1 | c2 | c3 | c4) {	/* not in middle */
		if(c1 & c2 & c3 & c4) {	/* completely out */
			return;
		} else {	/* clipping */
			zbufclip(zspan, zvlnr, f1, f2, f3, c1, c2, c3);
			zbufclip(zspan, zvlnr, f1, f3, f4, c1, c3, c4);
		}
		return;
	}

	/* perspective division: HCS to ZCS */

	div= 1.0f/f1[3];
	vez[0]= Zmulx*(1.0+f1[0]*div)+ Zjitx;
	vez[1]= Zmuly*(1.0+f1[1]*div)+ Zjity;
	vez[2]= 0x7FFFFFFF *(f1[2]*div);

	div= 1.0f/f2[3];
	vez[4]= Zmulx*(1.0+f2[0]*div)+ Zjitx;
	vez[5]= Zmuly*(1.0+f2[1]*div)+ Zjity;
	vez[6]= 0x7FFFFFFF *(f2[2]*div);

	div= 1.0f/f3[3];
	vez[8]= Zmulx*(1.0+f3[0]*div)+ Zjitx;
	vez[9]= Zmuly*(1.0+f3[1]*div)+ Zjity;
	vez[10]= 0x7FFFFFFF *(f3[2]*div);

	div= 1.0f/f4[3];
	vez[12]= Zmulx*(1.0+f4[0]*div)+ Zjitx;
	vez[13]= Zmuly*(1.0+f4[1]*div)+ Zjity;
	vez[14]= 0x7FFFFFFF *(f4[2]*div);

	zbuffunc4(zspan, zvlnr, vez, vez+4, vez+8, vez+12);
}


/* ***************** ZBUFFER MAIN ROUTINES **************** */


void zbufferall(void)
{
	ZSpan zspan;
	VlakRen *vlr= NULL;
	Material *ma=0;
	int v, zvlnr;
	short transp=0, env=0, wire=0;

	Zmulx= ((float)R.rectx)/2.0;
	Zmuly= ((float)R.recty)/2.0;

	fillrect(R.rectz, R.rectx, R.recty, 0x7FFFFFFF);

	zbuf_alloc_span(&zspan, R.recty);
	
	zbuffunc= zbufinvulGL;
	zbuffunc4= zbufinvulGL4;
	zbuflinefunc= zbufline;

	for(v=0; v<R.totvlak; v++) {

		if((v & 255)==0) vlr= R.blovl[v>>8];
		else vlr++;
		
		if(vlr->flag & R_VISIBLE) {
			if(vlr->mat!=ma) {
				ma= vlr->mat;
				transp= ma->mode & MA_ZTRA;
				env= (ma->mode & MA_ENV);
				wire= (ma->mode & MA_WIRE);
				
				if(ma->mode & MA_ZINV) zbuffunc= zbufinvulGLinv;
				else zbuffunc= zbufinvulGL;
			}
			
			if(transp==0) {
				if(env) zvlnr= 0;
				else zvlnr= v+1;
				
				if(wire) zbufclipwire(zvlnr, vlr);
				else {
					if(vlr->v4 && (vlr->flag & R_STRAND)) {
						zbufclip4(&zspan, zvlnr, vlr->v1->ho, vlr->v2->ho, vlr->v3->ho, vlr->v4->ho, vlr->v1->clip, vlr->v2->clip, vlr->v3->clip, vlr->v4->clip);
					}
					else {
						zbufclip(&zspan, zvlnr, vlr->v1->ho, vlr->v2->ho, vlr->v3->ho, vlr->v1->clip, vlr->v2->clip, vlr->v3->clip);
						if(vlr->v4) {
							if(zvlnr) zvlnr+= 0x800000;
							zbufclip(&zspan, zvlnr, vlr->v1->ho, vlr->v3->ho, vlr->v4->ho, vlr->v1->clip, vlr->v3->clip, vlr->v4->clip);
						}
					}
				}
			}
		}
	}
	
	zbuf_free_span(&zspan);
}

static int hashlist_projectvert(float *v1, float *hoco)
{
	static VertBucket bucket[256], *buck;
	
	if(v1==0) {
		memset(bucket, 0, 256*sizeof(VertBucket));
		return 0;
	}
	
	buck= &bucket[ (((long)v1)/16) & 255 ];
	if(buck->vert==v1) {
		QUATCOPY(hoco, buck->hoco);
		return buck->clip;
	}
	
	projectvert(v1, hoco);
	buck->clip = RE_testclip(hoco);
	buck->vert= v1;
	QUATCOPY(buck->hoco, hoco);
	return buck->clip;
}

/* used for booth radio 'tool' as during render */
void RE_zbufferall_radio(struct RadView *vw, RNode **rg_elem, int rg_totelem)
{
	ZSpan zspan;
	float hoco[4][4];
	int a, zvlnr;
	int c1, c2, c3, c4= 0;
	int *rectoto, *rectzo;
	int rectxo, rectyo;

	if(rg_totelem==0) return;

	hashlist_projectvert(NULL, NULL);
	
	rectxo= R.rectx;
	rectyo= R.recty;
	rectoto= R.rectot;
	rectzo= R.rectz;
	
	R.rectx= vw->rectx;
	R.recty= vw->recty;
	R.rectot= vw->rect;
	R.rectz= vw->rectz;
	
	Zmulx= ((float)R.rectx)/2.0;
	Zmuly= ((float)R.recty)/2.0;

	/* needed for projectvert */
	MTC_Mat4MulMat4(R.winmat, vw->viewmat, vw->winmat);

	fillrect(R.rectz, R.rectx, R.recty, 0x7FFFFFFF);
	fillrect(R.rectot, R.rectx, R.recty, 0xFFFFFF);

	zbuf_alloc_span(&zspan, R.recty);
	
	zbuffunc= zbufinvulGL;
	
	if(rg_elem) {	/* radio tool */
		RNode **re, *rn;

		re= rg_elem;
		re+= (rg_totelem-1);
		for(a= rg_totelem-1; a>=0; a--, re--) {
			rn= *re;
			if( (rn->f & RAD_SHOOT)==0 ) {    /* no shootelement */
				
				if( rn->f & RAD_TWOSIDED) zvlnr= a;
				else if( rn->f & RAD_BACKFACE) zvlnr= 0xFFFFFF;	
				else zvlnr= a;
				
				c1= hashlist_projectvert(rn->v1, hoco[0]);
				c2= hashlist_projectvert(rn->v2, hoco[1]);
				c3= hashlist_projectvert(rn->v3, hoco[2]);
				
				if(rn->v4) {
					c4= hashlist_projectvert(rn->v4, hoco[3]);
				}
	
				zbufclip(&zspan, zvlnr, hoco[0], hoco[1], hoco[2], c1, c2, c3);
				if(rn->v4) {
					zbufclip(&zspan, zvlnr, hoco[0], hoco[2], hoco[3], c1, c3, c4);
				}
			}
		}
	}
	else {	/* radio render */
		VlakRen *vlr=NULL;
		RadFace *rf;
		int totface=0;
		
		for(a=0; a<R.totvlak; a++) {
			if((a & 255)==0) vlr= R.blovl[a>>8]; else vlr++;
		
			if(vlr->radface) {
				rf= vlr->radface;
				if( (rf->flag & RAD_SHOOT)==0 ) {    /* no shootelement */
					
					if( rf->flag & RAD_TWOSIDED) zvlnr= totface;
					else if( rf->flag & RAD_BACKFACE) zvlnr= 0xFFFFFF;	/* receives no energy, but is zbuffered */
					else zvlnr= totface;
					
					c1= hashlist_projectvert(vlr->v1->co, hoco[0]);
					c2= hashlist_projectvert(vlr->v2->co, hoco[1]);
					c3= hashlist_projectvert(vlr->v3->co, hoco[2]);
					
					if(vlr->v4) {
						c4= hashlist_projectvert(vlr->v4->co, hoco[3]);
					}
		
					zbufclip(&zspan, zvlnr, hoco[0], hoco[1], hoco[2], c1, c2, c3);
					if(vlr->v4) {
						zbufclip(&zspan, zvlnr, hoco[0], hoco[2], hoco[3], c1, c3, c4);
					}
				}
				totface++;
			}
		}
	}
	
	/* restore */
	R.rectx= rectxo;
	R.recty= rectyo;
	R.rectot= rectoto;
	R.rectz= rectzo;

	zbuf_free_span(&zspan);
}

void zbuffershad(LampRen *lar)
{
	ZSpan zspan;
	VlakRen *vlr= NULL;
	Material *ma=0;
	int a, ok=1, lay= -1;

	if(lar->mode & LA_LAYER) lay= lar->lay;

	Zmulx= ((float)R.rectx)/2.0;
	Zmuly= ((float)R.recty)/2.0;
	Zjitx= Zjity= -0.5;

	fillrect(R.rectz,R.rectx,R.recty,0x7FFFFFFE);

	zbuf_alloc_span(&zspan, R.recty);
	
	zbuflinefunc= zbufline_onlyZ;
	zbuffunc= zbufinvulGL_onlyZ;
				
	for(a=0;a<R.totvlak;a++) {

		if((a & 255)==0) vlr= R.blovl[a>>8];
		else vlr++;

		if(vlr->mat!= ma) {
			ma= vlr->mat;
			ok= 1;
			if((ma->mode & MA_TRACEBLE)==0) ok= 0;
		}
		
		if(ok && (vlr->flag & R_VISIBLE) && (vlr->lay & lay)) {
			if(ma->mode & MA_WIRE) zbufclipwire(a+1, vlr);
			else if(vlr->flag & R_STRAND) zbufclipwire(a+1, vlr);
			else {
				zbufclip(&zspan, 0, vlr->v1->ho, vlr->v2->ho, vlr->v3->ho, vlr->v1->clip, vlr->v2->clip, vlr->v3->clip);
				if(vlr->v4) zbufclip(&zspan, 0, vlr->v1->ho, vlr->v3->ho, vlr->v4->ho, vlr->v1->clip, vlr->v3->clip, vlr->v4->clip);
			}
		}
	}
	zbuf_free_span(&zspan);
}



/* ******************** ABUF ************************* */


void bgnaccumbuf(void)
{
	
	Arectz= MEM_mallocN(sizeof(int)*ABUFPART*R.rectx, "Arectz");
	APixbuf= MEM_mallocN(ABUFPART*R.rectx*sizeof(APixstr), "APixbuf");

	Aminy= -1000;
	Amaxy= -1000;
	
	apsmteller= 0;
	apsmfirst.next= 0;
	apsmfirst.ps= 0;
} 
/* ------------------------------------------------------------------------ */

void endaccumbuf(void)
{
	
	MEM_freeN(Arectz);
	MEM_freeN(APixbuf);
	freepsA();
}

/* ------------------------------------------------------------------------ */

/**
 * Copy results from the solid face z buffering to the transparent
 * buffer.
 */
static void copyto_abufz(int sample)
{
	PixStr *ps;
	int x, y, *rza;
	long *rd;
	
	/* now, in OSA the pixstructs contain all faces filled in */
	if(R.r.mode & R_OSA) fillrect(Arectz, R.rectx, Amaxy-Aminy+1, 0x7FFFFFFF);
	else {
		memcpy(Arectz, R.rectz+ R.rectx*Aminy, 4*R.rectx*(Amaxy-Aminy+1));
		return;
	}
	//if( (R.r.mode & R_OSA)==0 || sample==0) return;
		
	rza= Arectz;
	rd= (R.rectdaps+ R.rectx*Aminy);

	sample= (1<<sample);
	
	for(y=Aminy; y<=Amaxy; y++) {
		for(x=0; x<R.rectx; x++) {
			
			if(*rd) {	
				ps= (PixStr *)(*rd);

				while(ps) {
					if(sample & ps->mask) {
						//printf("filled xy %d %d mask %d\n", x, y, sample);
						*rza= ps->z;
						break;
					}
					ps= ps->next;
				}
			}
			
			rd++; rza++;
		}
	}
}


/* ------------------------------------------------------------------------ */

/**
* Do accumulation z buffering.
 */

static void zbuffer_abuf()
{
	ZSpan zspan;
	Material *ma=0;
	VlakRen *vlr=NULL;
	float vec[3], hoco[4], mul, zval, fval;
	int v, zvlnr;
	int len;
	
	Zjitx= Zjity= -0.5;
	Zmulx= ((float)R.rectx)/2.0;
	Zmuly= ((float)R.recty)/2.0;

	/* clear APixstructs */
	len= sizeof(APixstr)*R.rectx*ABUFPART;
	memset(APixbuf, 0, len);
	
	zbuf_alloc_span(&zspan, R.recty);
	
	zbuffunc= zbufinvulAc;
	zbuffunc4= zbufinvulAc4;
	zbuflinefunc= zbuflineAc;

	//set_faces_raycountflag();
	
	for(Zsample=0; Zsample<R.osa || R.osa==0; Zsample++) {
		
		copyto_abufz(Zsample);	/* init zbuffer */

		if(R.r.mode & R_OSA) {
			Zjitx= -jit[Zsample][0]-0.5;
			Zjity= -jit[Zsample][1]-0.5;
		}
		
		for(v=0; v<R.totvlak; v++) {
			if((v & 255)==0) {
				vlr= R.blovl[v>>8];
			}
			else vlr++;
			
			ma= vlr->mat;

			if(ma->mode & (MA_ZTRA)) {

				if(vlr->flag & R_VISIBLE) {
					
							/* a little advantage for transp rendering (a z offset) */
					if( ma->zoffs != 0.0) {
						mul= 0x7FFFFFFF;
						zval= mul*(1.0+vlr->v1->ho[2]/vlr->v1->ho[3]);

						VECCOPY(vec, vlr->v1->co);
						/* z is negative, otherwise its being clipped */ 
						vec[2]-= ma->zoffs;
						RE_projectverto(vec, hoco);
						fval= mul*(1.0+hoco[2]/hoco[3]);

						Azvoordeel= (int) fabs(zval - fval );
					}
					else Azvoordeel= 0;
					
					zvlnr= v+1;
		
					if(ma->mode & (MA_WIRE)) zbufclipwire(zvlnr, vlr);
					else {
						if(vlr->v4 && (vlr->flag & R_STRAND)) {
							zbufclip4(&zspan, zvlnr, vlr->v1->ho, vlr->v2->ho, vlr->v3->ho, vlr->v4->ho, vlr->v1->clip, vlr->v2->clip, vlr->v3->clip, vlr->v4->clip);
						}
						else {
							zbufclip(&zspan, zvlnr, vlr->v1->ho, vlr->v2->ho, vlr->v3->ho, vlr->v1->clip, vlr->v2->clip, vlr->v3->clip);
							if(vlr->v4) {
								zvlnr+= 0x800000;
								zbufclip(&zspan, zvlnr, vlr->v1->ho, vlr->v3->ho, vlr->v4->ho, vlr->v1->clip, vlr->v3->clip, vlr->v4->clip);
							}
						}
					}
				}
				if( (v & 255)==255) 
					if(RE_local_test_break()) 
						break; 
			}
		}
		
		if((R.r.mode & R_OSA)==0) break;
		if(RE_local_test_break()) break;
	}
	
	zbuf_free_span(&zspan);
}

int vergzvlak(const void *a1, const void *a2)
{
	const int *x1=a1, *x2=a2;

	if( x1[0] < x2[0] ) return 1;
	else if( x1[0] > x2[0]) return -1;
	return 0;
}

/**
* Shade this face at this location in SCS.
 */
static void shadetrapixel(float x, float y, int z, int facenr, int mask, float *fcol)
{
	
	if( (facenr & 0x7FFFFF) > R.totvlak) {
		printf("error in shadetrapixel nr: %d\n", (facenr & 0x7FFFFF));
		return;
	}
	if(R.r.mode & R_OSA) {
		VlakRen *vlr= RE_findOrAddVlak( (facenr-1) & 0x7FFFFF);
		float accumcol[4]={0,0,0,0}, tot=0.0;
		int a;
		
		if(vlr->flag & R_FULL_OSA) {
			for(a=0; a<R.osa; a++) {
				if(mask & (1<<a)) {
					shadepixel(x+jit[a][0], y+jit[a][1], z, facenr, 1<<a, fcol);
					accumcol[0]+= fcol[0];
					accumcol[1]+= fcol[1];
					accumcol[2]+= fcol[2];
					accumcol[3]+= fcol[3];
					tot+= 1.0;
				}
			}
			tot= 1.0/tot;
			fcol[0]= accumcol[0]*tot;
			fcol[1]= accumcol[1]*tot;
			fcol[2]= accumcol[2]*tot;
			fcol[3]= accumcol[3]*tot;
		}
		else {
			extern float centLut[16];
			extern char *centmask;
			
			int b= centmask[mask];
			x= x+centLut[b & 15];
			y= y+centLut[b>>4];
			shadepixel(x, y, z, facenr, mask, fcol);
	
		}
	}
	else shadepixel(x, y, z, facenr, mask, fcol);
}

static int addtosampcol(float *sampcol, float *fcol, int mask)
{
	int a, retval = R.osa;
	
	for(a=0; a < R.osa; a++) {
		if(mask & (1<<a)) addAlphaUnderFloat(sampcol, fcol);
		if(sampcol[3]>0.999) retval--;
		sampcol+= 4;
	}
	return retval;
}

/*
 * renders when needed the Abuffer with faces stored in pixels, returns 1 scanline rendered
 */

void abufsetrow(float *acolrow, int y)
{
	extern SDL_mutex *render_abuf_lock; // initrender.c
	APixstr *ap, *apn;
	float *col, fcol[4], tempcol[4], sampcol[16*4], *scol, accumcol[4];
	float ys, fac, alpha[32];
	int x, part, a, zrow[200][3], totface, nr;
	int sval;
	
	if(y<0) return;
	if(R.osa>16) {
		printf("abufsetrow: osa too large\n");
		G.afbreek= 1;
		return;
	}

	//R.flag &= ~R_LAMPHALO;

	/* alpha LUT */
	if(R.r.mode & R_OSA ) {
		fac= (1.0/(float)R.osa);
		for(a=0; a<=R.osa; a++) {
			alpha[a]= (float)a*fac;
		}
	}

	if(R.r.mode & R_THREADS) {
		/* lock thread if... */
		if(y>Aminy+2 && y<Amaxy-2);
		else {
			if(render_abuf_lock) SDL_mutexP(render_abuf_lock);
		}
	}
	
	/* does a pixbuf has to be created? */
	if(y<Aminy || y>Amaxy) {
		part= (y/ABUFPART);
		Aminy= part*ABUFPART;
		Amaxy= Aminy+ABUFPART-1;
		if(Amaxy>=R.recty) Amaxy= R.recty-1;
		freepsA();
		zbuffer_abuf();
	}
	
	/* render row */
	col= acolrow;
	memset(col, 0, 4*sizeof(float)*R.rectx);
	ap= APixbuf + R.rectx*(y-Aminy);
	ys= y;
	
	for(x=0; x<R.rectx; x++, col+=4, ap++) {
		if(ap->p[0]) {
			/* sort in z */
			totface= 0;
			apn= ap;
			while(apn) {
				for(a=0; a<4; a++) {
					if(apn->p[a]) {
						zrow[totface][0]= apn->z[a];
						zrow[totface][1]= apn->p[a];
						zrow[totface][2]= apn->mask[a];
						totface++;
						if(totface>199) totface= 199;
					}
					else break;
				}
				apn= apn->next;
			}
			
			if(totface==1) {
				
				shadetrapixel((float)x, (float)y, zrow[0][0], zrow[0][1], zrow[0][2], fcol);
	
				nr= count_mask(zrow[0][2]);
				if( (R.r.mode & R_OSA) && nr<R.osa) {
					fac= alpha[ nr ];
					col[0]= (fcol[0]*fac);
					col[1]= (fcol[1]*fac);
					col[2]= (fcol[2]*fac);
					col[3]= (fcol[3]*fac);
				}
				else {
					col[0]= fcol[0];
					col[1]= fcol[1];
					col[2]= fcol[2];
					col[3]= fcol[3];
				}
			}
			else {

				if(totface==2) {
					if(zrow[0][0] < zrow[1][0]) {
						a= zrow[0][0]; zrow[0][0]= zrow[1][0]; zrow[1][0]= a;
						a= zrow[0][1]; zrow[0][1]= zrow[1][1]; zrow[1][1]= a;
						a= zrow[0][2]; zrow[0][2]= zrow[1][2]; zrow[1][2]= a;
					}

				}
				else {	/* totface>2 */
					qsort(zrow, totface, sizeof(int)*3, vergzvlak);
				}
				
				/* join when pixels are adjacent */
				
				while(totface>0) {
					totface--;
					
					shadetrapixel((float)x, (float)y, zrow[totface][0], zrow[totface][1], zrow[totface][2], fcol);
					
					a= count_mask(zrow[totface][2]);
					if( (R.r.mode & R_OSA ) && a<R.osa) {
						if(totface>0) {
							memset(sampcol, 0, 4*sizeof(float)*R.osa);
							sval= addtosampcol(sampcol, fcol, zrow[totface][2]);

							/* sval==0: alpha completely full */
							while( (sval != 0) && (totface>0) ) {
								a= count_mask(zrow[totface-1][2]);
								if(a==R.osa) break;
								totface--;
							
								shadetrapixel((float)x, (float)y, zrow[totface][0], zrow[totface][1], zrow[totface][2], fcol);
								sval= addtosampcol(sampcol, fcol, zrow[totface][2]);
							}
							scol= sampcol;
							accumcol[0]= scol[0]; accumcol[1]= scol[1];
							accumcol[2]= scol[2]; accumcol[3]= scol[3];
							scol+= 4;
							for(a=1; a<R.osa; a++, scol+=4) {
								accumcol[0]+= scol[0]; accumcol[1]+= scol[1];
								accumcol[2]+= scol[2]; accumcol[3]+= scol[3];
							}
							tempcol[0]= accumcol[0]/R.osa;
							tempcol[1]= accumcol[1]/R.osa;
							tempcol[2]= accumcol[2]/R.osa;
							tempcol[3]= accumcol[3]/R.osa;
							
							addAlphaUnderFloat(col, tempcol);
							
						}
						else {
							fac= alpha[a];
							fcol[0]= (fcol[0]*fac);
							fcol[1]= (fcol[1]*fac);
							fcol[2]= (fcol[2]*fac);
							fcol[3]= (fcol[3]*fac);
							addAlphaUnderFloat(col, fcol);
						}
					}	
					else addAlphaUnderFloat(col, fcol);
							
					if(col[3]>=0.999) break;
				}
			}
		}
	}

	if(R.r.mode & R_THREADS) {
		if(y>Aminy+2 && y<Amaxy-2);
		else {
			if(render_abuf_lock) SDL_mutexV(render_abuf_lock);
		}
	}
}

/* end of zbuf.c */




