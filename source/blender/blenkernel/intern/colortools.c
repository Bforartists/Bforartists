/* 
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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "DNA_color_types.h"
#include "DNA_curve_types.h"
#include "DNA_image_types.h"
#include "DNA_texture_types.h"

#include "BKE_colortools.h"
#include "BKE_curve.h"
#include "BKE_global.h"
#include "BKE_ipo.h"
#include "BKE_main.h"
#include "BKE_utildefines.h"

#include "BLI_blenlib.h"
#include "BLI_arithb.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

/* ********************************* color curve ********************* */

/* ***************** operations on full struct ************* */

CurveMapping *curvemapping_add(int tot, float minx, float miny, float maxx, float maxy)
{
	CurveMapping *cumap;
	int a;
	
	cumap= MEM_callocN(sizeof(CurveMapping), "new curvemap");
	cumap->flag= CUMA_DO_CLIP;
	if(tot==4) cumap->cur= 3;		/* rhms, hack for 'col' curve? */
	
	BLI_init_rctf(&cumap->curr, minx, maxx, miny, maxy);
	cumap->clipr= cumap->curr;
	
	cumap->white[0]= cumap->white[1]= cumap->white[2]= 1.0f;
	cumap->bwmul[0]= cumap->bwmul[1]= cumap->bwmul[2]= 1.0f;
	
	for(a=0; a<tot; a++) {
		cumap->cm[a].totpoint= 2;
		cumap->cm[a].curve= MEM_callocN(2*sizeof(CurveMapPoint), "curve points");
		
		cumap->cm[a].curve[0].x= minx;
		cumap->cm[a].curve[0].y= miny;
		cumap->cm[a].curve[1].x= maxx;
		cumap->cm[a].curve[1].y= maxy;
	}	
	return cumap;
}

void curvemapping_free(CurveMapping *cumap)
{
	int a;
	
	if(cumap) {
		for(a=0; a<CM_TOT; a++) {
			if(cumap->cm[a].curve) MEM_freeN(cumap->cm[a].curve);
			if(cumap->cm[a].table) MEM_freeN(cumap->cm[a].table);
		}
		MEM_freeN(cumap);
	}
}

CurveMapping *curvemapping_copy(CurveMapping *cumap)
{
	int a;
	
	if(cumap) {
		CurveMapping *cumapn= MEM_dupallocN(cumap);
		for(a=0; a<CM_TOT; a++) {
			if(cumap->cm[a].curve) 
				cumapn->cm[a].curve= MEM_dupallocN(cumap->cm[a].curve);
			if(cumap->cm[a].table) 
				cumapn->cm[a].table= MEM_dupallocN(cumap->cm[a].table);
		}
		return cumapn;
	}
	return NULL;
}

void curvemapping_set_black_white(CurveMapping *cumap, float *black, float *white)
{
	int a;
	
	if(white)
		VECCOPY(cumap->white, white);
	if(black)
		VECCOPY(cumap->black, black);
	
	for(a=0; a<3; a++) {
		if(cumap->white[a]==cumap->black[a])
			cumap->bwmul[a]= 0.0f;
		else
			cumap->bwmul[a]= 1.0f/(cumap->white[a] - cumap->black[a]);
	}	
}

/* ***************** operations on single curve ************* */
/* ********** NOTE: requires curvemapping_changed() call after ******** */

/* removes with flag set */
void curvemap_remove(CurveMap *cuma, int flag)
{
	CurveMapPoint *cmp= MEM_mallocN((cuma->totpoint)*sizeof(CurveMapPoint), "curve points");
	int a, b, removed=0;
	
	/* well, lets keep the two outer points! */
	cmp[0]= cuma->curve[0];
	for(a=1, b=1; a<cuma->totpoint-1; a++) {
		if(!(cuma->curve[a].flag & flag)) {
			cmp[b]= cuma->curve[a];
			b++;
		}
		else removed++;
	}
	cmp[b]= cuma->curve[a];
	
	MEM_freeN(cuma->curve);
	cuma->curve= cmp;
	cuma->totpoint -= removed;
}

void curvemap_insert(CurveMap *cuma, float x, float y)
{
	CurveMapPoint *cmp= MEM_callocN((cuma->totpoint+1)*sizeof(CurveMapPoint), "curve points");
	int a;
	
	memcpy(cmp, cuma->curve, (cuma->totpoint)*sizeof(CurveMapPoint));
	MEM_freeN(cuma->curve);
	cuma->curve= cmp;
	
	cuma->curve[cuma->totpoint].x= x;
	cuma->curve[cuma->totpoint].y= y;
	cuma->curve[cuma->totpoint].flag = CUMA_SELECT;
	for(a=0; a<cuma->totpoint; a++, cmp++)
		cmp->flag= 0;
	cuma->totpoint++;
}

void curvemap_reset(CurveMap *cuma, rctf *clipr)
{
	cuma->totpoint= 2;
	
	cuma->curve[0].x= clipr->xmin;
	cuma->curve[0].y= clipr->ymin;
	cuma->curve[0].flag= 0;
	cuma->curve[1].x= clipr->xmax;
	cuma->curve[1].y= clipr->ymax;
	cuma->curve[1].flag= 0;
	
	if(cuma->table) {
		MEM_freeN(cuma->table);
		cuma->table= NULL;
	}
}

/* if type==1: vector, else auto */
void curvemap_sethandle(CurveMap *cuma, int type)
{
	int a;
	
	for(a=0; a<cuma->totpoint; a++) {
		if(cuma->curve[a].flag & CUMA_SELECT) {
			if(type) cuma->curve[a].flag |= CUMA_VECTOR;
			else cuma->curve[a].flag &= ~CUMA_VECTOR;
		}
	}
}

/* *********************** Making the tables and display ************** */

/* reduced copy of garbled calchandleNurb() code in curve.c */
static void calchandle_curvemap(BezTriple *bezt, BezTriple *prev, BezTriple *next, int mode)
{
	float *p1,*p2,*p3,pt[3];
	float dx1,dy1, dx,dy, vx,vy, len,len1,len2;
	
	if(bezt->h1==0 && bezt->h2==0) return;
	
	p2= bezt->vec[1];
	
	if(prev==NULL) {
		p3= next->vec[1];
		pt[0]= 2*p2[0]- p3[0];
		pt[1]= 2*p2[1]- p3[1];
		p1= pt;
	}
	else p1= prev->vec[1];
	
	if(next==NULL) {
		p1= prev->vec[1];
		pt[0]= 2*p2[0]- p1[0];
		pt[1]= 2*p2[1]- p1[1];
		p3= pt;
	}
	else p3= next->vec[1];
	
	dx= p2[0]- p1[0];
	dy= p2[1]- p1[1];

	len1= (float)sqrt(dx*dx+dy*dy);
	
	dx1= p3[0]- p2[0];
	dy1= p3[1]- p2[1];

	len2= (float)sqrt(dx1*dx1+dy1*dy1);
	
	if(len1==0.0f) len1=1.0f;
	if(len2==0.0f) len2=1.0f;
	
	if(bezt->h1==HD_AUTO || bezt->h2==HD_AUTO) {    /* auto */
		vx= dx1/len2 + dx/len1;
		vy= dy1/len2 + dy/len1;
		
		len= 2.5614f*(float)sqrt(vx*vx + vy*vy);
		if(len!=0.0f) {
			
			if(bezt->h1==HD_AUTO) {
				len1/=len;
				*(p2-3)= *p2-vx*len1;
				*(p2-2)= *(p2+1)-vy*len1;
			}
			if(bezt->h2==HD_AUTO) {
				len2/=len;
				*(p2+3)= *p2+vx*len2;
				*(p2+4)= *(p2+1)+vy*len2;
			}
		}
	}

	if(bezt->h1==HD_VECT) {	/* vector */
		dx/=3.0; 
		dy/=3.0; 
		*(p2-3)= *p2-dx;
		*(p2-2)= *(p2+1)-dy;
	}
	if(bezt->h2==HD_VECT) {
		dx1/=3.0; 
		dy1/=3.0; 
		*(p2+3)= *p2+dx1;
		*(p2+4)= *(p2+1)+dy1;
	}
}

/* only creates a table for a single channel in CurveMapping */
static void curvemap_make_table(CurveMap *cuma, rctf *clipr)
{
	CurveMapPoint *cmp= cuma->curve;
	BezTriple *bezt;
	float *fp, *allpoints, curf, range;
	int a, totpoint;
	
	if(cuma->curve==NULL) return;
	
	/* default rect also is table range */
	cuma->mintable= clipr->xmin;
	cuma->maxtable= clipr->xmax;
	
	/* hrmf... we now rely on blender ipo beziers, these are more advanced */
	bezt= MEM_callocN(cuma->totpoint*sizeof(BezTriple), "beztarr");
	
	for(a=0; a<cuma->totpoint; a++) {
		cuma->mintable= MIN2(cuma->mintable, cmp[a].x);
		cuma->maxtable= MAX2(cuma->maxtable, cmp[a].x);
		bezt[a].vec[1][0]= cmp[a].x;
		bezt[a].vec[1][1]= cmp[a].y;
		if(cmp[a].flag & CUMA_VECTOR)
			bezt[a].h1= bezt[a].h2= HD_VECT;
		else
			bezt[a].h1= bezt[a].h2= HD_AUTO;
	}
	
	for(a=0; a<cuma->totpoint; a++) {
		if(a==0)
			calchandle_curvemap(bezt, NULL, bezt+1, 0);
		else if(a==cuma->totpoint-1)
			calchandle_curvemap(bezt+a, bezt+a-1, NULL, 0);
		else
			calchandle_curvemap(bezt+a, bezt+a-1, bezt+a+1, 0);
	}
	
	/* first and last handle need correction, instead of pointing to center of next/prev, 
		we let it point to the closest handle */
	if(cuma->totpoint>2) {
		float hlen, nlen, vec[3];
		
		if(bezt[0].h2==HD_AUTO) {
			
			hlen= VecLenf(bezt[0].vec[1], bezt[0].vec[2]);	/* original handle length */
			/* clip handle point */
			VECCOPY(vec, bezt[1].vec[0]);
			if(vec[0] < bezt[0].vec[1][0])
				vec[0]= bezt[0].vec[1][0];
			
			VecSubf(vec, vec, bezt[0].vec[1]);
			nlen= VecLength(vec);
			if(nlen>FLT_EPSILON) {
				VecMulf(vec, hlen/nlen);
				VecAddf(bezt[0].vec[2], vec, bezt[0].vec[1]);
			}
		}
		a= cuma->totpoint-1;
		if(bezt[a].h2==HD_AUTO) {
			
			hlen= VecLenf(bezt[a].vec[1], bezt[a].vec[0]);	/* original handle length */
			/* clip handle point */
			VECCOPY(vec, bezt[a-1].vec[2]);
			if(vec[0] > bezt[a].vec[1][0])
				vec[0]= bezt[a].vec[1][0];
			
			VecSubf(vec, vec, bezt[a].vec[1]);
			nlen= VecLength(vec);
			if(nlen>FLT_EPSILON) {
				VecMulf(vec, hlen/nlen);
				VecAddf(bezt[a].vec[0], vec, bezt[a].vec[1]);
			}
		}
	}	
	/* make the bezier curve */
	if(cuma->table)
		MEM_freeN(cuma->table);
	totpoint= (cuma->totpoint-1)*CM_RESOL;
	fp= allpoints= MEM_mallocN(totpoint*2*sizeof(float), "table");
	
	for(a=0; a<cuma->totpoint-1; a++, fp += 2*CM_RESOL) {
		correct_bezpart(bezt[a].vec[1], bezt[a].vec[2], bezt[a+1].vec[0], bezt[a+1].vec[1]);
		forward_diff_bezier(bezt[a].vec[1][0], bezt[a].vec[2][0], bezt[a+1].vec[0][0], bezt[a+1].vec[1][0], fp, CM_RESOL-1, 2);	
		forward_diff_bezier(bezt[a].vec[1][1], bezt[a].vec[2][1], bezt[a+1].vec[0][1], bezt[a+1].vec[1][1], fp+1, CM_RESOL-1, 2);
	}
	
	MEM_freeN(bezt);
	
	range= CM_TABLEDIV*(cuma->maxtable - cuma->mintable);
	cuma->range= 1.0f/range;
	
	/* now make a table with CM_TABLE equal x distances */
	fp= allpoints;
	cmp= MEM_callocN((CM_TABLE+1)*sizeof(CurveMapPoint), "dist table");
	cmp[0].x= cuma->mintable;
	cmp[0].y= allpoints[1];
	
	for(a=1; a<CM_TABLE; a++) {
		curf= cuma->mintable + range*(float)a;
		cmp[a].x= curf;
		
		/* get the first x coordinate larger than curf */
		while(curf >= fp[0] && fp!=allpoints-2) {
			fp+=2;
		}
		if(fp==allpoints-2)
			cmp[a].y= fp[1];
		else {
			float fac1= fp[0] - fp[-2];
			float fac2= fp[0] - curf;
			if(fac1 > FLT_EPSILON)
				fac1= fac2/fac1;
			else
				fac1= 0.0f;
			cmp[a].y= fac1*fp[-1] + (1.0f-fac1)*fp[1];
		}
	}
	cmp[CM_TABLE].x= cuma->maxtable;
	cmp[CM_TABLE].y= allpoints[2*totpoint-1];
	
	MEM_freeN(allpoints);
	cuma->table= cmp;
}

/* call when you do images etc, needs restore too. also verifies tables */
void curvemapping_premultiply(CurveMapping *cumap, int restore)
{
	static CurveMapPoint *table[3]= {NULL, NULL, NULL};
	int a;
	
	if(restore) {
		for(a=0; a<3; a++) {
			MEM_freeN(cumap->cm[a].table);
			cumap->cm[a].table= table[a];
		}
	}
	else {
		/* verify and copy */
		for(a=0; a<3; a++) {
			if(cumap->cm[a].table==NULL)
				curvemap_make_table(cumap->cm+a, &cumap->clipr);
			table[a]= cumap->cm[a].table;
			cumap->cm[a].table= MEM_dupallocN(cumap->cm[a].table);
		}
		
		if(cumap->cm[3].table==NULL)
			curvemap_make_table(cumap->cm+3, &cumap->clipr);
	
		/* premul */
		for(a=0; a<3; a++) {
			int b;
			for(b=0; b<=CM_TABLE; b++) {
				cumap->cm[a].table[b].y= curvemap_evaluateF(cumap->cm+3, cumap->cm[a].table[b].y);
			}
		}
	}
}

static int sort_curvepoints(const void *a1, const void *a2)
{
	const struct CurveMapPoint *x1=a1, *x2=a2;
	
	if( x1->x > x2->x ) return 1;
	else if( x1->x < x2->x) return -1;
	return 0;
}

/* ************************ more CurveMapping calls *************** */

/* note; only does current curvemap! */
void curvemapping_changed(CurveMapping *cumap, int rem_doubles)
{
	CurveMap *cuma= cumap->cm+cumap->cur;
	CurveMapPoint *cmp= cuma->curve;
	rctf *clipr= &cumap->clipr;
	float thresh= 0.01f*(clipr->xmax - clipr->xmin);
	float dx, dy;
	int a;
	
	/* clamp with clip */
	if(cumap->flag & CUMA_DO_CLIP) {
		for(a=0; a<cuma->totpoint; a++) {
			if(cmp[a].x < clipr->xmin)
				cmp[a].x= clipr->xmin;
			else if(cmp[a].x > clipr->xmax)
				cmp[a].x= clipr->xmax;
			if(cmp[a].y < clipr->ymin)
				cmp[a].y= clipr->ymin;
			else if(cmp[a].y > clipr->ymax)
				cmp[a].y= clipr->ymax;
		}
	}
	
	qsort(cmp, cuma->totpoint, sizeof(CurveMapPoint), sort_curvepoints);
	
	/* remove doubles, threshold set on 1% of default range */
	if(rem_doubles && cuma->totpoint>2) {
		for(a=0; a<cuma->totpoint-1; a++) {
			dx= cmp[a].x - cmp[a+1].x;
			dy= cmp[a].y - cmp[a+1].y;
			if( sqrt(dx*dx + dy*dy) < thresh ) {
				if(a==0) {
					cmp[a+1].flag|= 2;
					if(cmp[a+1].flag & CUMA_SELECT)
						cmp[a].flag |= CUMA_SELECT;
				}
				else {
					cmp[a].flag|= 2;
					if(cmp[a].flag & CUMA_SELECT)
						cmp[a+1].flag |= CUMA_SELECT;
				}
				break;	/* we assume 1 deletion per edit is ok */
			}
		}
		if(a != cuma->totpoint-1)
			curvemap_remove(cuma, 2);
	}	
	curvemap_make_table(cuma, clipr);
}

/* table should be verified */
float curvemap_evaluateF(CurveMap *cuma, float value)
{
	float fi;
	int i;

	/* index in table */
	fi= (value-cuma->mintable)*cuma->range;
	i= (int)fi;
	if(i<0) return cuma->table[0].y;
	if(i>=CM_TABLE) return cuma->table[CM_TABLE].y;
	
	fi= fi-(float)i;
	return (1.0f-fi)*cuma->table[i].y + (fi)*cuma->table[i+1].y; 
}

/* works with curve 'cur' */
float curvemapping_evaluateF(CurveMapping *cumap, int cur, float value)
{
	CurveMap *cuma= cumap->cm+cur;
	
	/* allocate or bail out */
	if(cuma->table==NULL) {
		curvemap_make_table(cuma, &cumap->clipr);
		if(cuma->table==NULL)
			return value;
	}
	return curvemap_evaluateF(cuma, value);
}

/* vector case */
void curvemapping_evaluate3F(CurveMapping *cumap, float *vecout, const float *vecin)
{
	vecout[0]= curvemapping_evaluateF(cumap, 0, vecin[0]);
	vecout[1]= curvemapping_evaluateF(cumap, 1, vecin[1]);
	vecout[2]= curvemapping_evaluateF(cumap, 2, vecin[2]);
}

/* RGB case, no black/white points, no premult */
void curvemapping_evaluateRGBF(CurveMapping *cumap, float *vecout, const float *vecin)
{
	vecout[0]= curvemapping_evaluateF(cumap, 0, curvemapping_evaluateF(cumap, 3, vecin[0]));
	vecout[1]= curvemapping_evaluateF(cumap, 1, curvemapping_evaluateF(cumap, 3, vecin[1]));
	vecout[2]= curvemapping_evaluateF(cumap, 2, curvemapping_evaluateF(cumap, 3, vecin[2]));
}


/* RGB with black/white points and premult. tables are checked */
void curvemapping_evaluate_premulRGBF(CurveMapping *cumap, float *vecout, const float *vecin)
{
	float fac;
	
	fac= (vecin[0] - cumap->black[0])*cumap->bwmul[0];
	vecout[0]= curvemap_evaluateF(cumap->cm, fac);
	
	fac= (vecin[1] - cumap->black[1])*cumap->bwmul[1];
	vecout[1]= curvemap_evaluateF(cumap->cm+1, fac);
	
	fac= (vecin[2] - cumap->black[2])*cumap->bwmul[2];
	vecout[2]= curvemap_evaluateF(cumap->cm+2, fac);
}

#define FTOCHAR(val) val<=0.0f?0: (val>=1.0f?255: (char)(255.0f*val))

void curvemapping_do_image(CurveMapping *cumap, Image *ima)
{
	int pixel;
	
	if(ima==NULL || ima->ibuf==NULL)
		return;
	if(ima->ibuf->rect_float==NULL)
		IMB_float_from_rect(ima->ibuf);
	
	curvemapping_premultiply(cumap, 0);
	
	if(ima->ibuf->rect_float && ima->ibuf->rect) {
		float *pixf= ima->ibuf->rect_float;
		float col[3];
		char *pixc= (char *)ima->ibuf->rect;
		
		for(pixel= ima->ibuf->x*ima->ibuf->y; pixel>0; pixel--, pixf+=4, pixc+=4) {
			curvemapping_evaluate_premulRGBF(cumap, col, pixf);
			pixc[0]= FTOCHAR(col[0]);
			pixc[1]= FTOCHAR(col[1]);
			pixc[2]= FTOCHAR(col[2]);
			/* assume alpha was set */
		}
	}
	
	curvemapping_premultiply(cumap, 1);
}
