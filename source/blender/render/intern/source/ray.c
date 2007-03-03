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
 * The Original Code is Copyright (C) 1990-1998 NeoGeo BV.
 * All rights reserved.
 *
 * Contributors: 2004/2005 Blender Foundation, full recode
 *
 * ***** END GPL LICENSE BLOCK *****
 */


#include <math.h>
#include <string.h>
#include <stdlib.h>
#include <float.h>

#include "MEM_guardedalloc.h"

#include "DNA_material_types.h"
#include "DNA_lamp_types.h"

#include "BKE_global.h"
#include "BKE_node.h"
#include "BKE_utildefines.h"

#include "BLI_arithb.h"
#include "BLI_rand.h"
#include "BLI_jitter.h"

#include "PIL_time.h"

#include "render_types.h"
#include "renderpipeline.h"
#include "rendercore.h"
#include "renderdatabase.h"
#include "pixelblending.h"
#include "pixelshading.h"
#include "shading.h"
#include "texture.h"

#define DDA_SHADOW 0
#define DDA_MIRROR 1
#define DDA_SHADOW_TRA 2

#define RAY_TRA		1
#define RAY_TRAFLIP	2

#define DEPTH_SHADOW_TRA  10

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
/* defined in pipeline.c, is hardcopy of active dynamic allocated Render */
/* only to be used here in this file, it's for speed */
extern struct Render R;
/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* ********** structs *************** */

#define BRANCH_ARRAY 1024
#define NODE_ARRAY 4096

typedef struct Isect {
	float start[3], vec[3], end[3];		/* start+vec = end, in d3dda */
	float labda, u, v;
	struct VlakRen *vlr, *vlrcontr, *vlrorig;	/* vlr is where to intersect with */
	short isect, mode;	/* isect: which half of quad, mode: DDA_SHADOW, DDA_MIRROR, DDA_SHADOW_TRA */
	float ddalabda;
	float col[4];		/* RGBA for shadow_tra */
	int lay;			/* -1 default, set for layer lamps */
	short vlrisect;		/* flag whether vlrcontr was done or not */
	/* for optimize, last intersected face */
	VlakRen *vlr_last;
} Isect;

typedef struct Branch
{
	struct Branch *b[8];
} Branch;

typedef struct OcVal 
{
	short ocx, ocy, ocz;
} OcVal;

typedef struct Node
{
	struct VlakRen *v[8];
	struct OcVal ov[8];
	struct Node *next;
} Node;


/* ******** globals ***************** */

/* just for statistics */
static int raycount;
static int accepted, rejected, coherent_ray;


/* **************** ocval method ******************* */
/* within one octree node, a set of 3x15 bits defines a 'boundbox' to OR with */

#define OCVALRES	15
#define BROW16(min, max)      (((max)>=OCVALRES? 0xFFFF: (1<<(max+1))-1) - ((min>0)? ((1<<(min))-1):0) )

static void calc_ocval_face(float *v1, float *v2, float *v3, float *v4, short x, short y, short z, OcVal *ov)
{
	float min[3], max[3];
	int ocmin, ocmax;
	
	VECCOPY(min, v1);
	VECCOPY(max, v1);
	DO_MINMAX(v2, min, max);
	DO_MINMAX(v3, min, max);
	if(v4) {
		DO_MINMAX(v4, min, max);
	}
	
	ocmin= OCVALRES*(min[0]-x); 
	ocmax= OCVALRES*(max[0]-x);
	ov->ocx= BROW16(ocmin, ocmax);
	
	ocmin= OCVALRES*(min[1]-y); 
	ocmax= OCVALRES*(max[1]-y);
	ov->ocy= BROW16(ocmin, ocmax);
	
	ocmin= OCVALRES*(min[2]-z); 
	ocmax= OCVALRES*(max[2]-z);
	ov->ocz= BROW16(ocmin, ocmax);

}

static void calc_ocval_ray(OcVal *ov, float xo, float yo, float zo, float *vec1, float *vec2)
{
	int ocmin, ocmax;
	
	if(vec1[0]<vec2[0]) {
		ocmin= OCVALRES*(vec1[0] - xo);
		ocmax= OCVALRES*(vec2[0] - xo);
	} else {
		ocmin= OCVALRES*(vec2[0] - xo);
		ocmax= OCVALRES*(vec1[0] - xo);
	}
	ov->ocx= BROW16(ocmin, ocmax);

	if(vec1[1]<vec2[1]) {
		ocmin= OCVALRES*(vec1[1] - yo);
		ocmax= OCVALRES*(vec2[1] - yo);
	} else {
		ocmin= OCVALRES*(vec2[1] - yo);
		ocmax= OCVALRES*(vec1[1] - yo);
	}
	ov->ocy= BROW16(ocmin, ocmax);

	if(vec1[2]<vec2[2]) {
		ocmin= OCVALRES*(vec1[2] - zo);
		ocmax= OCVALRES*(vec2[2] - zo);
	} else {
		ocmin= OCVALRES*(vec2[2] - zo);
		ocmax= OCVALRES*(vec1[2] - zo);
	}
	ov->ocz= BROW16(ocmin, ocmax);
}

/* ************* octree ************** */

static Branch *addbranch(Octree *oc, Branch *br, short ocb)
{
	int index;
	
	if(br->b[ocb]) return br->b[ocb];
	
	oc->branchcount++;
	index= oc->branchcount>>12;
	
	if(oc->adrbranch[index]==NULL)
		oc->adrbranch[index]= MEM_callocN(4096*sizeof(Branch), "new oc branch");

	if(oc->branchcount>= BRANCH_ARRAY*4096) {
		printf("error; octree branches full\n");
		oc->branchcount=0;
	}
	
	return br->b[ocb]= oc->adrbranch[index]+(oc->branchcount & 4095);
}

static Node *addnode(Octree *oc)
{
	int index;
	
	oc->nodecount++;
	index= oc->nodecount>>12;
	
	if(oc->adrnode[index]==NULL)
		oc->adrnode[index]= MEM_callocN(4096*sizeof(Node),"addnode");

	if(oc->nodecount> NODE_ARRAY*NODE_ARRAY) {
		printf("error; octree nodes full\n");
		oc->nodecount=0;
	}
	
	return oc->adrnode[index]+(oc->nodecount & 4095);
}

static int face_in_node(VlakRen *vlr, short x, short y, short z, float rtf[][3])
{
	static float nor[3], d;
	float fx, fy, fz;
	
	// init static vars 
	if(vlr) {
		CalcNormFloat(rtf[0], rtf[1], rtf[2], nor);
		d= -nor[0]*rtf[0][0] - nor[1]*rtf[0][1] - nor[2]*rtf[0][2];
		return 0;
	}
	
	fx= x;
	fy= y;
	fz= z;
	
	if((fx)*nor[0] + (fy)*nor[1] + (fz)*nor[2] + d > 0.0f) {
		if((fx+1)*nor[0] + (fy  )*nor[1] + (fz  )*nor[2] + d < 0.0f) return 1;
		if((fx  )*nor[0] + (fy+1)*nor[1] + (fz  )*nor[2] + d < 0.0f) return 1;
		if((fx+1)*nor[0] + (fy+1)*nor[1] + (fz  )*nor[2] + d < 0.0f) return 1;
	
		if((fx  )*nor[0] + (fy  )*nor[1] + (fz+1)*nor[2] + d < 0.0f) return 1;
		if((fx+1)*nor[0] + (fy  )*nor[1] + (fz+1)*nor[2] + d < 0.0f) return 1;
		if((fx  )*nor[0] + (fy+1)*nor[1] + (fz+1)*nor[2] + d < 0.0f) return 1;
		if((fx+1)*nor[0] + (fy+1)*nor[1] + (fz+1)*nor[2] + d < 0.0f) return 1;
	}
	else {
		if((fx+1)*nor[0] + (fy  )*nor[1] + (fz  )*nor[2] + d > 0.0f) return 1;
		if((fx  )*nor[0] + (fy+1)*nor[1] + (fz  )*nor[2] + d > 0.0f) return 1;
		if((fx+1)*nor[0] + (fy+1)*nor[1] + (fz  )*nor[2] + d > 0.0f) return 1;
	
		if((fx  )*nor[0] + (fy  )*nor[1] + (fz+1)*nor[2] + d > 0.0f) return 1;
		if((fx+1)*nor[0] + (fy  )*nor[1] + (fz+1)*nor[2] + d > 0.0f) return 1;
		if((fx  )*nor[0] + (fy+1)*nor[1] + (fz+1)*nor[2] + d > 0.0f) return 1;
		if((fx+1)*nor[0] + (fy+1)*nor[1] + (fz+1)*nor[2] + d > 0.0f) return 1;
	}
	
	return 0;
}

static void ocwrite(Octree *oc, VlakRen *vlr, short x, short y, short z, float rtf[][3])
{
	Branch *br;
	Node *no;
	short a, oc0, oc1, oc2, oc3, oc4, oc5;

	x<<=2;
	y<<=1;

	br= oc->adrbranch[0];

	if(oc->ocres==512) {
		oc0= ((x & 1024)+(y & 512)+(z & 256))>>8;
		br= addbranch(oc, br, oc0);
	}
	if(oc->ocres>=256) {
		oc0= ((x & 512)+(y & 256)+(z & 128))>>7;
		br= addbranch(oc, br, oc0);
	}
	if(oc->ocres>=128) {
		oc0= ((x & 256)+(y & 128)+(z & 64))>>6;
		br= addbranch(oc, br, oc0);
	}

	oc0= ((x & 128)+(y & 64)+(z & 32))>>5;
	oc1= ((x & 64)+(y & 32)+(z & 16))>>4;
	oc2= ((x & 32)+(y & 16)+(z & 8))>>3;
	oc3= ((x & 16)+(y & 8)+(z & 4))>>2;
	oc4= ((x & 8)+(y & 4)+(z & 2))>>1;
	oc5= ((x & 4)+(y & 2)+(z & 1));

	br= addbranch(oc, br,oc0);
	br= addbranch(oc, br,oc1);
	br= addbranch(oc, br,oc2);
	br= addbranch(oc, br,oc3);
	br= addbranch(oc, br,oc4);
	no= (Node *)br->b[oc5];
	if(no==NULL) br->b[oc5]= (Branch *)(no= addnode(oc));

	while(no->next) no= no->next;

	a= 0;
	if(no->v[7]) {		/* node full */
		no->next= addnode(oc);
		no= no->next;
	}
	else {
		while(no->v[a]!=NULL) a++;
	}
	
	no->v[a]= vlr;
	
	if(vlr->v4)
		calc_ocval_face(rtf[0], rtf[1], rtf[2], rtf[3], x>>2, y>>1, z, &no->ov[a]);
	else
		calc_ocval_face(rtf[0], rtf[1], rtf[2], NULL, x>>2, y>>1, z, &no->ov[a]);
}

static void d2dda(Octree *oc, short b1, short b2, short c1, short c2, char *ocface, short rts[][3], float rtf[][3])
{
	int ocx1,ocx2,ocy1,ocy2;
	int x,y,dx=0,dy=0;
	float ox1,ox2,oy1,oy2;
	float labda,labdao,labdax,labday,ldx,ldy;

	ocx1= rts[b1][c1];
	ocy1= rts[b1][c2];
	ocx2= rts[b2][c1];
	ocy2= rts[b2][c2];

	if(ocx1==ocx2 && ocy1==ocy2) {
		ocface[oc->ocres*ocx1+ocy1]= 1;
		return;
	}

	ox1= rtf[b1][c1];
	oy1= rtf[b1][c2];
	ox2= rtf[b2][c1];
	oy2= rtf[b2][c2];

	if(ox1!=ox2) {
		if(ox2-ox1>0.0f) {
			labdax= (ox1-ocx1-1.0f)/(ox1-ox2);
			ldx= -1.0f/(ox1-ox2);
			dx= 1;
		} else {
			labdax= (ox1-ocx1)/(ox1-ox2);
			ldx= 1.0f/(ox1-ox2);
			dx= -1;
		}
	} else {
		labdax=1.0f;
		ldx=0;
	}

	if(oy1!=oy2) {
		if(oy2-oy1>0.0f) {
			labday= (oy1-ocy1-1.0f)/(oy1-oy2);
			ldy= -1.0f/(oy1-oy2);
			dy= 1;
		} else {
			labday= (oy1-ocy1)/(oy1-oy2);
			ldy= 1.0f/(oy1-oy2);
			dy= -1;
		}
	} else {
		labday=1.0f;
		ldy=0;
	}
	
	x=ocx1; y=ocy1;
	labda= MIN2(labdax, labday);
	
	while(TRUE) {
		
		if(x<0 || y<0 || x>=oc->ocres || y>=oc->ocres);
		else ocface[oc->ocres*x+y]= 1;
		
		labdao=labda;
		if(labdax==labday) {
			labdax+=ldx;
			x+=dx;
			labday+=ldy;
			y+=dy;
		} else {
			if(labdax<labday) {
				labdax+=ldx;
				x+=dx;
			} else {
				labday+=ldy;
				y+=dy;
			}
		}
		labda=MIN2(labdax,labday);
		if(labda==labdao) break;
		if(labda>=1.0f) break;
	}
	ocface[oc->ocres*ocx2+ocy2]=1;
}

static void filltriangle(Octree *oc, short c1, short c2, char *ocface, short *ocmin)
{
	short *ocmax;
	int a, x, y, y1, y2;

	ocmax=ocmin+3;

	for(x=ocmin[c1];x<=ocmax[c1];x++) {
		a= oc->ocres*x;
		for(y=ocmin[c2];y<=ocmax[c2];y++) {
			if(ocface[a+y]) {
				y++;
				while(ocface[a+y] && y!=ocmax[c2]) y++;
				for(y1=ocmax[c2];y1>y;y1--) {
					if(ocface[a+y1]) {
						for(y2=y;y2<=y1;y2++) ocface[a+y2]=1;
						y1=0;
					}
				}
				y=ocmax[c2];
			}
		}
	}
}

void freeoctree(Render *re)
{
	Octree *oc= &re->oc;
	
#if 0
	printf("branches %d nodes %d\n", oc->branchcount, oc->nodecount);
	printf("raycount %d \n", raycount);	
	printf("ray coherent %d \n", coherent_ray);
	printf("accepted %d rejected %d\n", accepted, rejected);
#endif
	
	if(oc->adrbranch) {
		int a= 0;
		while(oc->adrbranch[a]) {
			MEM_freeN(oc->adrbranch[a]);
			oc->adrbranch[a]= NULL;
			a++;
		}
		MEM_freeN(oc->adrbranch);
		oc->adrbranch= NULL;
	}
	oc->branchcount= 0;
	
	if(oc->adrnode) {
		int a= 0;
		while(oc->adrnode[a]) {
			MEM_freeN(oc->adrnode[a]);
			oc->adrnode[a]= NULL;
			a++;
		}
		MEM_freeN(oc->adrnode);
		oc->adrnode= NULL;
	}
	oc->nodecount= 0;
}

void makeoctree(Render *re)
{
	Octree *oc;
	VlakRen *vlr=NULL;
	VertRen *v1, *v2, *v3, *v4;
	float ocfac[3], t00, t01, t02;
	float rtf[4][3];
	int v;
	int a, b, c, oc1, oc2, oc3, oc4, x, y, z, ocres2;
	short rts[4][3], ocmin[6], *ocmax;
	char *ocface;	// front, top, size view of face, to fill in
	double lasttime= PIL_check_seconds_timer();
	
	oc= &re->oc;
	oc->adrbranch= MEM_callocN(sizeof(void *)*BRANCH_ARRAY, "octree branches");
	oc->adrnode= MEM_callocN(sizeof(void *)*NODE_ARRAY, "octree nodes");

	ocmax= ocmin+3;
	
	/* only for debug info */
	raycount=0;
	accepted= 0;
	rejected= 0;
	coherent_ray= 0;
	
	/* fill main octree struct */
	oc->ocres= re->r.ocres;
	ocres2= oc->ocres*oc->ocres;
	INIT_MINMAX(oc->min, oc->max);
	
	/* first min max octree space */
	for(v=0;v<re->totvlak;v++) {
		if((v & 255)==0) vlr= re->vlaknodes[v>>8].vlak;
		else vlr++;
		if(vlr->mat->mode & MA_TRACEBLE) {	
			if((vlr->mat->mode & MA_WIRE)==0) {	
				
				DO_MINMAX(vlr->v1->co, oc->min, oc->max);
				DO_MINMAX(vlr->v2->co, oc->min, oc->max);
				DO_MINMAX(vlr->v3->co, oc->min, oc->max);
				if(vlr->v4) {
					DO_MINMAX(vlr->v4->co, oc->min, oc->max);
				}
			}
		}
	}

	if(oc->min[0] > oc->max[0]) return;	/* empty octree */

	oc->adrbranch[0]=(Branch *)MEM_callocN(4096*sizeof(Branch), "makeoctree");
	
	/* the lookup table, per face, for which nodes to fill in */
	ocface= MEM_callocN( 3*ocres2 + 8, "ocface");
	memset(ocface, 0, 3*ocres2);

	for(c=0;c<3;c++) {	/* octree enlarge, still needed? */
		oc->min[c]-= 0.01f;
		oc->max[c]+= 0.01f;
	}

	t00= oc->max[0]-oc->min[0];
	t01= oc->max[1]-oc->min[1];
	t02= oc->max[2]-oc->min[2];
	
	/* this minus 0.1 is old safety... seems to be needed? */
	oc->ocfacx=ocfac[0]= (oc->ocres-0.1)/t00;
	oc->ocfacy=ocfac[1]= (oc->ocres-0.1)/t01;
	oc->ocfacz=ocfac[2]= (oc->ocres-0.1)/t02;
	
	oc->ocsize= sqrt(t00*t00+t01*t01+t02*t02);	/* global, max size octree */

	for(v=0; v<re->totvlak; v++) {
		if((v & 255)==0) {
			double time= PIL_check_seconds_timer();

			vlr= re->vlaknodes[v>>8].vlak;
			if(re->test_break())
				break;
			if(time-lasttime>1.0f) {
				char str[32];
				sprintf(str, "Filling Octree: %d", v);
				re->i.infostr= str;
				re->stats_draw(&re->i);
				re->i.infostr= NULL;
				lasttime= time;
			}
		}
		else vlr++;
		
		if(vlr->mat->mode & MA_TRACEBLE) {
			if((vlr->mat->mode & MA_WIRE)==0) {	
				
				v1= vlr->v1;
				v2= vlr->v2;
				v3= vlr->v3;
				v4= vlr->v4;
				
				for(c=0;c<3;c++) {
					rtf[0][c]= (v1->co[c]-oc->min[c])*ocfac[c] ;
					rts[0][c]= (short)rtf[0][c];
					rtf[1][c]= (v2->co[c]-oc->min[c])*ocfac[c] ;
					rts[1][c]= (short)rtf[1][c];
					rtf[2][c]= (v3->co[c]-oc->min[c])*ocfac[c] ;
					rts[2][c]= (short)rtf[2][c];
					if(v4) {
						rtf[3][c]= (v4->co[c]-oc->min[c])*ocfac[c] ;
						rts[3][c]= (short)rtf[3][c];
					}
				}
				
				for(c=0;c<3;c++) {
					oc1= rts[0][c];
					oc2= rts[1][c];
					oc3= rts[2][c];
					if(v4==NULL) {
						ocmin[c]= MIN3(oc1,oc2,oc3);
						ocmax[c]= MAX3(oc1,oc2,oc3);
					}
					else {
						oc4= rts[3][c];
						ocmin[c]= MIN4(oc1,oc2,oc3,oc4);
						ocmax[c]= MAX4(oc1,oc2,oc3,oc4);
					}
					if(ocmax[c]>oc->ocres-1) ocmax[c]=oc->ocres-1;
					if(ocmin[c]<0) ocmin[c]=0;
				}
				
				if(ocmin[0]==ocmax[0] && ocmin[1]==ocmax[1] && ocmin[2]==ocmax[2]) {
					ocwrite(oc, vlr, ocmin[0], ocmin[1], ocmin[2], rtf);
				}
				else {
					
					d2dda(oc, 0,1,0,1,ocface+ocres2,rts,rtf);
					d2dda(oc, 0,1,0,2,ocface,rts,rtf);
					d2dda(oc, 0,1,1,2,ocface+2*ocres2,rts,rtf);
					d2dda(oc, 1,2,0,1,ocface+ocres2,rts,rtf);
					d2dda(oc, 1,2,0,2,ocface,rts,rtf);
					d2dda(oc, 1,2,1,2,ocface+2*ocres2,rts,rtf);
					if(v4==NULL) {
						d2dda(oc, 2,0,0,1,ocface+ocres2,rts,rtf);
						d2dda(oc, 2,0,0,2,ocface,rts,rtf);
						d2dda(oc, 2,0,1,2,ocface+2*ocres2,rts,rtf);
					}
					else {
						d2dda(oc, 2,3,0,1,ocface+ocres2,rts,rtf);
						d2dda(oc, 2,3,0,2,ocface,rts,rtf);
						d2dda(oc, 2,3,1,2,ocface+2*ocres2,rts,rtf);
						d2dda(oc, 3,0,0,1,ocface+ocres2,rts,rtf);
						d2dda(oc, 3,0,0,2,ocface,rts,rtf);
						d2dda(oc, 3,0,1,2,ocface+2*ocres2,rts,rtf);
					}
					/* nothing todo with triangle..., just fills :) */
					filltriangle(oc, 0,1,ocface+ocres2,ocmin);
					filltriangle(oc, 0,2,ocface,ocmin);
					filltriangle(oc, 1,2,ocface+2*ocres2,ocmin);
					
					/* init static vars here */
					face_in_node(vlr, 0,0,0, rtf);
					
					for(x=ocmin[0];x<=ocmax[0];x++) {
						a= oc->ocres*x;
						for(y=ocmin[1];y<=ocmax[1];y++) {
							if(ocface[a+y+ocres2]) {
								b= oc->ocres*y+2*ocres2;
								for(z=ocmin[2];z<=ocmax[2];z++) {
									if(ocface[b+z] && ocface[a+z]) {
										if(face_in_node(NULL, x, y, z, rtf))
											ocwrite(oc, vlr, x,y,z, rtf);
									}
								}
							}
						}
					}
					
					/* same loops to clear octree, doubt it can be done smarter */
					for(x=ocmin[0];x<=ocmax[0];x++) {
						a= oc->ocres*x;
						for(y=ocmin[1];y<=ocmax[1];y++) {
							/* x-y */
							ocface[a+y+ocres2]= 0;

							b= oc->ocres*y + 2*ocres2;
							for(z=ocmin[2];z<=ocmax[2];z++) {
								/* y-z */
								ocface[b+z]= 0;
								/* x-z */
								ocface[a+z]= 0;
							}
						}
					}
				}
			}
		}
	}
	
	MEM_freeN(ocface);
	re->i.infostr= NULL;
	re->stats_draw(&re->i);
}

/* ************ raytracer **************** */

/* only for self-intersecting test with current render face (where ray left) */
static int intersection2(VlakRen *vlr, float r0, float r1, float r2, float rx1, float ry1, float rz1)
{
	VertRen *v1,*v2,*v3,*v4=NULL;
	float x0,x1,x2,t00,t01,t02,t10,t11,t12,t20,t21,t22;
	float m0, m1, m2, divdet, det, det1;
	float u1, v, u2;

	/* happens for baking with non existing face */
	if(vlr->v1==NULL)
		return 1;
	
	v1= vlr->v1; 
	v2= vlr->v2; 
	if(vlr->v4) {
		v3= vlr->v4;
		v4= vlr->v3;
	}
	else v3= vlr->v3;	

	t00= v3->co[0]-v1->co[0];
	t01= v3->co[1]-v1->co[1];
	t02= v3->co[2]-v1->co[2];
	t10= v3->co[0]-v2->co[0];
	t11= v3->co[1]-v2->co[1];
	t12= v3->co[2]-v2->co[2];
	
	x0= t11*r2-t12*r1;
	x1= t12*r0-t10*r2;
	x2= t10*r1-t11*r0;

	divdet= t00*x0+t01*x1+t02*x2;

	m0= rx1-v3->co[0];
	m1= ry1-v3->co[1];
	m2= rz1-v3->co[2];
	det1= m0*x0+m1*x1+m2*x2;
	
	if(divdet!=0.0f) {
		u1= det1/divdet;

		if(u1<=0.0f) {
			det= t00*(m1*r2-m2*r1);
			det+= t01*(m2*r0-m0*r2);
			det+= t02*(m0*r1-m1*r0);
			v= det/divdet;

			if(v<=0.0f && (u1 + v) >= -1.0f) {
				return 1;
			}
		}
	}

	if(v4) {

		t20= v3->co[0]-v4->co[0];
		t21= v3->co[1]-v4->co[1];
		t22= v3->co[2]-v4->co[2];

		divdet= t20*x0+t21*x1+t22*x2;
		if(divdet!=0.0f) {
			u2= det1/divdet;
		
			if(u2<=0.0f) {
				det= t20*(m1*r2-m2*r1);
				det+= t21*(m2*r0-m0*r2);
				det+= t22*(m0*r1-m1*r0);
				v= det/divdet;
	
				if(v<=0.0f && (u2 + v) >= -1.0f) {
					return 2;
				}
			}
		}
	}
	return 0;
}

#if 0
/* ray - line intersection */
/* disabled until i got real & fast cylinder checking, this code doesnt work proper
for faster strands */

static int intersection_strand(Isect *is)
{
	float v1[3], v2[3];		/* length of strand */
	float axis[3], rc[3], nor[3], radline, dist, len;
	
	/* radius strand */
	radline= 0.5f*VecLenf(is->vlr->v1->co, is->vlr->v2->co);
	
	VecMidf(v1, is->vlr->v1->co, is->vlr->v2->co);
	VecMidf(v2, is->vlr->v3->co, is->vlr->v4->co);
	
	VECSUB(rc, v1, is->start);	/* vector from base ray to base cylinder */
	VECSUB(axis, v2, v1);		/* cylinder axis */
	
	CROSS(nor, is->vec, axis);
	len= VecLength(nor);
	
	if(len<FLT_EPSILON)
		return 0;

	dist= INPR(rc, nor)/len;	/* distance between ray and axis cylinder */
	
	if(dist<radline && dist>-radline) {
		float dot1, dot2, dot3, rlen, alen, div;
		float labda;
		
		/* calculating the intersection point of shortest distance */
		dot1 = INPR(rc, is->vec);
		dot2 = INPR(is->vec, axis);
		dot3 = INPR(rc, axis);
		rlen = INPR(is->vec, is->vec);
		alen = INPR(axis, axis);
		
		div = alen * rlen - dot2 * dot2;
		if (ABS(div) < FLT_EPSILON)
			return 0;
		
		labda = (dot1*dot2 - dot3*rlen)/div;
		
		radline/= sqrt(alen);
		
		/* labda: where on axis do we have closest intersection? */
		if(labda >= -radline && labda <= 1.0f+radline) {
			VlakRen *vlr= is->vlrorig;
			VertRen *v1= is->vlr->v1, *v2= is->vlr->v2, *v3= is->vlr->v3, *v4= is->vlr->v4;
				/* but we dont do shadows from faces sharing edge */
			
			if(v1==vlr->v1 || v2==vlr->v1 || v3==vlr->v1 || v4==vlr->v1) return 0;
			if(v1==vlr->v2 || v2==vlr->v2 || v3==vlr->v2 || v4==vlr->v2) return 0;
			if(v1==vlr->v3 || v2==vlr->v3 || v3==vlr->v3 || v4==vlr->v3) return 0;
			if(vlr->v4) {
				if(v1==vlr->v4 || v2==vlr->v4 || v3==vlr->v4 || v4==vlr->v4) return 0;
			}
			return 1;
		}
	}
	return 0;
}
#endif

/* ray - triangle or quad intersection */
static int intersection(Isect *is)
{
	VertRen *v1,*v2,*v3,*v4=NULL;
	float x0,x1,x2,t00,t01,t02,t10,t11,t12,t20,t21,t22,r0,r1,r2;
	float m0, m1, m2, divdet, det1;
	short ok=0;

	/* disabled until i got real & fast cylinder checking, this code doesnt work proper
	   for faster strands */
//	if(is->mode==DDA_SHADOW && is->vlr->flag & R_STRAND) 
//		return intersection_strand(is);
	
	v1= is->vlr->v1; 
	v2= is->vlr->v2; 
	if(is->vlr->v4) {
		v3= is->vlr->v4;
		v4= is->vlr->v3;
	}
	else v3= is->vlr->v3;	

	t00= v3->co[0]-v1->co[0];
	t01= v3->co[1]-v1->co[1];
	t02= v3->co[2]-v1->co[2];
	t10= v3->co[0]-v2->co[0];
	t11= v3->co[1]-v2->co[1];
	t12= v3->co[2]-v2->co[2];
	
	r0= is->vec[0];
	r1= is->vec[1];
	r2= is->vec[2];
	
	x0= t12*r1-t11*r2;
	x1= t10*r2-t12*r0;
	x2= t11*r0-t10*r1;

	divdet= t00*x0+t01*x1+t02*x2;

	m0= is->start[0]-v3->co[0];
	m1= is->start[1]-v3->co[1];
	m2= is->start[2]-v3->co[2];
	det1= m0*x0+m1*x1+m2*x2;
	
	if(divdet!=0.0f) {
		float u;

		divdet= 1.0f/divdet;
		u= det1*divdet;
		if(u<0.0f && u>-1.0f) {
			float v, cros0, cros1, cros2;
			
			cros0= m1*t02-m2*t01;
			cros1= m2*t00-m0*t02;
			cros2= m0*t01-m1*t00;
			v= divdet*(cros0*r0 + cros1*r1 + cros2*r2);

			if(v<0.0f && (u + v) > -1.0f) {
				float labda;
				labda= divdet*(cros0*t10 + cros1*t11 + cros2*t12);

				if(labda>0.0f && labda<1.0f) {
					is->labda= labda;
					is->u= u; is->v= v;
					ok= 1;
				}
			}
		}
	}

	if(ok==0 && v4) {

		t20= v3->co[0]-v4->co[0];
		t21= v3->co[1]-v4->co[1];
		t22= v3->co[2]-v4->co[2];

		divdet= t20*x0+t21*x1+t22*x2;
		if(divdet!=0.0f) {
			float u;
			divdet= 1.0f/divdet;
			u = det1*divdet;
			
			if(u<0.0f && u>-1.0f) {
				float v, cros0, cros1, cros2;
				cros0= m1*t22-m2*t21;
				cros1= m2*t20-m0*t22;
				cros2= m0*t21-m1*t20;
				v= divdet*(cros0*r0 + cros1*r1 + cros2*r2);
	
				if(v<0.0f && (u + v) > -1.0f) {
					float labda;
					labda= divdet*(cros0*t10 + cros1*t11 + cros2*t12);
					
					if(labda>0.0f && labda<1.0f) {
						ok= 2;
						is->labda= labda;
						is->u= u; is->v= v;
					}
				}
			}
		}
	}

	if(ok) {
		is->isect= ok;	// wich half of the quad
		
		if(is->mode!=DDA_SHADOW) {
			/* for mirror & tra-shadow: large faces can be filled in too often, this prevents
			   a face being detected too soon... */
			if(is->labda > is->ddalabda) {
				return 0;
			}
		}
		
		/* when a shadow ray leaves a face, it can be little outside the edges of it, causing
		intersection to be detected in its neighbour face */
		
		if(is->vlrcontr && is->vlrisect);	// optimizing, the tests below are not needed
		else if(is->labda< .1) {
			VlakRen *vlr= is->vlrorig;
			short de= 0;
			
			if(v1==vlr->v1 || v2==vlr->v1 || v3==vlr->v1 || v4==vlr->v1) de++;
			if(v1==vlr->v2 || v2==vlr->v2 || v3==vlr->v2 || v4==vlr->v2) de++;
			if(v1==vlr->v3 || v2==vlr->v3 || v3==vlr->v3 || v4==vlr->v3) de++;
			if(vlr->v4) {
				if(v1==vlr->v4 || v2==vlr->v4 || v3==vlr->v4 || v4==vlr->v4) de++;
			}
			if(de) {
				
				/* so there's a shared edge or vertex, let's intersect ray with vlr
				itself, if that's true we can safely return 1, otherwise we assume
				the intersection is invalid, 0 */
				
				if(is->vlrcontr==NULL) {
					is->vlrcontr= vlr;
					is->vlrisect= intersection2(vlr, -r0, -r1, -r2, is->start[0], is->start[1], is->start[2]);
				}

				if(is->vlrisect) return 1;
				return 0;
			}
		}
		
		return 1;
	}

	return 0;
}

/* check all faces in this node */
static int testnode(Isect *is, Node *no, OcVal ocval)
{
	VlakRen *vlr;
	short nr=0;
	OcVal *ov;

	/* return on any first hit */
	if(is->mode==DDA_SHADOW) {
		
		vlr= no->v[0];
		while(vlr) {
		
			if(is->vlrorig != vlr) {

				if(is->lay & vlr->lay) {
					
					ov= no->ov+nr;
					if( (ov->ocx & ocval.ocx) && (ov->ocy & ocval.ocy) && (ov->ocz & ocval.ocz) ) { 
						//accepted++;
						is->vlr= vlr;
	
						if(intersection(is)) {
							is->vlr_last= vlr;
							return 1;
						}
					}
					//else rejected++;
				}
			}
			
			nr++;
			if(nr==8) {
				no= no->next;
				if(no==0) return 0;
				nr=0;
			}
			vlr= no->v[nr];
		}
	}
	else {			/* else mirror or glass or shadowtra, return closest face  */
		Isect isect;
		int found= 0;
		
		is->labda= 1.0f;	/* needed? */
		isect= *is;		/* copy for sorting */
		
		vlr= no->v[0];
		while(vlr) {
			
			if(is->vlrorig != vlr) {
				/* I now... cpu cycle waste, might do smarter once */
				if(is->mode==DDA_MIRROR && (vlr->mat->mode & MA_ONLYCAST));
				else if(is->mode==DDA_SHADOW_TRA && !(is->lay & vlr->lay));
				else {
					ov= no->ov+nr;
					if( (ov->ocx & ocval.ocx) && (ov->ocy & ocval.ocy) && (ov->ocz & ocval.ocz) ) { 
						//accepted++;

						isect.vlr= vlr;
						if(intersection(&isect)) {
							if(isect.labda<is->labda) *is= isect;
							found= 1;
						}
					}
					//else rejected++;
				}
			}
			
			nr++;
			if(nr==8) {
				no= no->next;
				if(no==NULL) break;
				nr=0;
			}
			vlr= no->v[nr];
		}
		
		return found;
	}

	return 0;
}

/* find the Node for the octree coord x y z */
static Node *ocread(int x, int y, int z)
{
	Branch *br;
	int oc1;
	
	x<<=2;
	y<<=1;
	
	br= R.oc.adrbranch[0];
	
	if(R.oc.ocres==512) {
		oc1= ((x & 1024)+(y & 512)+(z & 256))>>8;
		br= br->b[oc1];
		if(br==NULL) {
			return NULL;
		}
	}
	if(R.oc.ocres>=256) {
		oc1= ((x & 512)+(y & 256)+(z & 128))>>7;
		br= br->b[oc1];
		if(br==NULL) {
			return NULL;
		}
	}
	if(R.oc.ocres>=128) {
		oc1= ((x & 256)+(y & 128)+(z & 64))>>6;
		br= br->b[oc1];
		if(br==NULL) {
			return NULL;
		}
	}
	
	oc1= ((x & 128)+(y & 64)+(z & 32))>>5;
	br= br->b[oc1];
	if(br) {
		oc1= ((x & 64)+(y & 32)+(z & 16))>>4;
		br= br->b[oc1];
		if(br) {
			oc1= ((x & 32)+(y & 16)+(z & 8))>>3;
			br= br->b[oc1];
			if(br) {
				oc1= ((x & 16)+(y & 8)+(z & 4))>>2;
				br= br->b[oc1];
				if(br) {
					oc1= ((x & 8)+(y & 4)+(z & 2))>>1;
					br= br->b[oc1];
					if(br) {
						oc1= ((x & 4)+(y & 2)+(z & 1));
						return (Node *)br->b[oc1];
					}
				}
			}
		}
	}
	
	return NULL;
}

static int cliptest(float p, float q, float *u1, float *u2)
{
	float r;

	if(p<0.0f) {
		if(q<p) return 0;
		else if(q<0.0f) {
			r= q/p;
			if(r>*u2) return 0;
			else if(r>*u1) *u1=r;
		}
	}
	else {
		if(p>0.0f) {
			if(q<0.0f) return 0;
			else if(q<p) {
				r= q/p;
				if(r<*u1) return 0;
				else if(r<*u2) *u2=r;
			}
		}
		else if(q<0.0f) return 0;
	}
	return 1;
}

/* extensive coherence checks/storage cancels out the benefit of it, and gives errors... we
   need better methods, sample code commented out below (ton) */
 
/*

in top: static int coh_nodes[16*16*16][6];
in makeoctree: memset(coh_nodes, 0, sizeof(coh_nodes));
 
static void add_coherence_test(int ocx1, int ocx2, int ocy1, int ocy2, int ocz1, int ocz2)
{
	short *sp;
	
	sp= coh_nodes[ (ocx2 & 15) + 16*(ocy2 & 15) + 256*(ocz2 & 15) ];
	sp[0]= ocx1; sp[1]= ocy1; sp[2]= ocz1;
	sp[3]= ocx2; sp[4]= ocy2; sp[5]= ocz2;
	
}

static int do_coherence_test(int ocx1, int ocx2, int ocy1, int ocy2, int ocz1, int ocz2)
{
	short *sp;
	
	sp= coh_nodes[ (ocx2 & 15) + 16*(ocy2 & 15) + 256*(ocz2 & 15) ];
	if(sp[0]==ocx1 && sp[1]==ocy1 && sp[2]==ocz1 &&
	   sp[3]==ocx2 && sp[4]==ocy2 && sp[5]==ocz2) return 1;
	return 0;
}

*/

/* return 1: found valid intersection */
/* starts with is->vlrorig */
static int d3dda(Isect *is)	
{
	Node *no;
	OcVal ocval;
	float vec1[3], vec2[3];
	float u1,u2,ox1,ox2,oy1,oy2,oz1,oz2;
	float labdao,labdax,ldx,labday,ldy,labdaz,ldz, ddalabda;
	int dx,dy,dz;	
	int xo,yo,zo,c1=0;
	int ocx1,ocx2,ocy1, ocy2,ocz1,ocz2;
	
	/* clip with octree */
	if(R.oc.branchcount==0) return 0;
	
	/* do this before intersect calls */
	is->vlrcontr= NULL;				/* to check shared edge */
	is->vlrisect= is->isect= 0;		/* shared edge, quad half flag */

	/* only for shadow! */
	if(is->mode==DDA_SHADOW) {
	
		/* check with last intersected shadow face */
		if(is->vlr_last!=NULL && is->vlr_last!=is->vlrorig) {
			if(is->lay & is->vlr_last->lay) {
				is->vlr= is->vlr_last;
				VECSUB(is->vec, is->end, is->start);
				if(intersection(is)) return 1;
			}
		}
	}
	
	ldx= is->end[0] - is->start[0];
	u1= 0.0f;
	u2= 1.0f;

	/* clip with octree cube */
	if(cliptest(-ldx, is->start[0]-R.oc.min[0], &u1,&u2)) {
		if(cliptest(ldx, R.oc.max[0]-is->start[0], &u1,&u2)) {
			ldy= is->end[1] - is->start[1];
			if(cliptest(-ldy, is->start[1]-R.oc.min[1], &u1,&u2)) {
				if(cliptest(ldy, R.oc.max[1]-is->start[1], &u1,&u2)) {
					ldz= is->end[2] - is->start[2];
					if(cliptest(-ldz, is->start[2]-R.oc.min[2], &u1,&u2)) {
						if(cliptest(ldz, R.oc.max[2]-is->start[2], &u1,&u2)) {
							c1=1;
							if(u2<1.0f) {
								is->end[0]= is->start[0]+u2*ldx;
								is->end[1]= is->start[1]+u2*ldy;
								is->end[2]= is->start[2]+u2*ldz;
							}
							if(u1>0.0f) {
								is->start[0]+=u1*ldx;
								is->start[1]+=u1*ldy;
								is->start[2]+=u1*ldz;
							}
						}
					}
				}
			}
		}
	}

	if(c1==0) return 0;

	/* reset static variables in ocread */
	//ocread(R.oc.ocres, 0, 0);

	/* setup 3dda to traverse octree */
	ox1= (is->start[0]-R.oc.min[0])*R.oc.ocfacx;
	oy1= (is->start[1]-R.oc.min[1])*R.oc.ocfacy;
	oz1= (is->start[2]-R.oc.min[2])*R.oc.ocfacz;
	ox2= (is->end[0]-R.oc.min[0])*R.oc.ocfacx;
	oy2= (is->end[1]-R.oc.min[1])*R.oc.ocfacy;
	oz2= (is->end[2]-R.oc.min[2])*R.oc.ocfacz;

	ocx1= (int)ox1;
	ocy1= (int)oy1;
	ocz1= (int)oz1;
	ocx2= (int)ox2;
	ocy2= (int)oy2;
	ocz2= (int)oz2;

	/* for intersection */
	VECSUB(is->vec, is->end, is->start);

	if(ocx1==ocx2 && ocy1==ocy2 && ocz1==ocz2) {
		no= ocread(ocx1, ocy1, ocz1);
		if(no) {
			/* exact intersection with node */
			vec1[0]= ox1; vec1[1]= oy1; vec1[2]= oz1;
			vec2[0]= ox2; vec2[1]= oy2; vec2[2]= oz2;
			calc_ocval_ray(&ocval, (float)ocx1, (float)ocy1, (float)ocz1, vec1, vec2);
			is->ddalabda= 1.0f;
			if( testnode(is, no, ocval) ) return 1;
		}
	}
	else {
		//static int coh_ocx1,coh_ocx2,coh_ocy1, coh_ocy2,coh_ocz1,coh_ocz2;
		float dox, doy, doz;
		int eqval;
		
		/* calc labda en ld */
		dox= ox1-ox2;
		doy= oy1-oy2;
		doz= oz1-oz2;

		if(dox<-FLT_EPSILON) {
			ldx= -1.0f/dox;
			labdax= (ocx1-ox1+1.0f)*ldx;
			dx= 1;
		} else if(dox>FLT_EPSILON) {
			ldx= 1.0f/dox;
			labdax= (ox1-ocx1)*ldx;
			dx= -1;
		} else {
			labdax=1.0f;
			ldx=0;
			dx= 0;
		}

		if(doy<-FLT_EPSILON) {
			ldy= -1.0f/doy;
			labday= (ocy1-oy1+1.0f)*ldy;
			dy= 1;
		} else if(doy>FLT_EPSILON) {
			ldy= 1.0f/doy;
			labday= (oy1-ocy1)*ldy;
			dy= -1;
		} else {
			labday=1.0f;
			ldy=0;
			dy= 0;
		}

		if(doz<-FLT_EPSILON) {
			ldz= -1.0f/doz;
			labdaz= (ocz1-oz1+1.0f)*ldz;
			dz= 1;
		} else if(doz>FLT_EPSILON) {
			ldz= 1.0f/doz;
			labdaz= (oz1-ocz1)*ldz;
			dz= -1;
		} else {
			labdaz=1.0f;
			ldz=0;
			dz= 0;
		}
		
		xo=ocx1; yo=ocy1; zo=ocz1;
		labdao= ddalabda= MIN3(labdax,labday,labdaz);
		
		vec2[0]= ox1;
		vec2[1]= oy1;
		vec2[2]= oz1;
		
		/* this loop has been constructed to make sure the first and last node of ray
		   are always included, even when ddalabda==1.0f or larger */

		while(TRUE) {

			no= ocread(xo, yo, zo);
			if(no) {
				
				/* calculate ray intersection with octree node */
				VECCOPY(vec1, vec2);
				// dox,y,z is negative
				vec2[0]= ox1-ddalabda*dox;
				vec2[1]= oy1-ddalabda*doy;
				vec2[2]= oz1-ddalabda*doz;
				calc_ocval_ray(&ocval, (float)xo, (float)yo, (float)zo, vec1, vec2);
							   
				is->ddalabda= ddalabda;
				if( testnode(is, no, ocval) ) return 1;
			}

			labdao= ddalabda;
			
			/* traversing ocree nodes need careful detection of smallest values, with proper
			   exceptions for equal labdas */
			eqval= (labdax==labday);
			if(labday==labdaz) eqval += 2;
			if(labdax==labdaz) eqval += 4;
			
			if(eqval) {	// only 4 cases exist!
				if(eqval==7) {	// x=y=z
					xo+=dx; labdax+=ldx;
					yo+=dy; labday+=ldy;
					zo+=dz; labdaz+=ldz;
				}
				else if(eqval==1) { // x=y 
					if(labday < labdaz) {
						xo+=dx; labdax+=ldx;
						yo+=dy; labday+=ldy;
					}
					else {
						zo+=dz; labdaz+=ldz;
					}
				}
				else if(eqval==2) { // y=z
					if(labdax < labday) {
						xo+=dx; labdax+=ldx;
					}
					else {
						yo+=dy; labday+=ldy;
						zo+=dz; labdaz+=ldz;
					}
				}
				else { // x=z
					if(labday < labdax) {
						yo+=dy; labday+=ldy;
					}
					else {
						xo+=dx; labdax+=ldx;
						zo+=dz; labdaz+=ldz;
					}
				}
			}
			else {	// all three different, just three cases exist
				eqval= (labdax<labday);
				if(labday<labdaz) eqval += 2;
				if(labdax<labdaz) eqval += 4;
				
				if(eqval==7 || eqval==5) { // x smallest
					xo+=dx; labdax+=ldx;
				}
				else if(eqval==2 || eqval==6) { // y smallest
					yo+=dy; labday+=ldy;
				}
				else { // z smallest
					zo+=dz; labdaz+=ldz;
				}
				
			}

			ddalabda=MIN3(labdax,labday,labdaz);
			if(ddalabda==labdao) break;
			/* to make sure the last node is always checked */
			if(labdao>=1.0f) break;
		}
	}
	
	/* reached end, no intersections found */
	is->vlr_last= NULL;
	return 0;
}		


static void shade_ray(Isect *is, ShadeInput *shi, ShadeResult *shr)
{
	VlakRen *vlr= is->vlr;
	int osatex= 0, norflip;
	
	/* set up view vector */
	VECCOPY(shi->view, is->vec);

	/* render co */
	shi->co[0]= is->start[0]+is->labda*(shi->view[0]);
	shi->co[1]= is->start[1]+is->labda*(shi->view[1]);
	shi->co[2]= is->start[2]+is->labda*(shi->view[2]);
	
	Normalise(shi->view);

	shi->vlr= vlr;
	shi->mat= vlr->mat;
	memcpy(&shi->r, &shi->mat->r, 23*sizeof(float));	// note, keep this synced with render_types.h
	shi->har= shi->mat->har;
	
	// Osa structs we leave unchanged now
	SWAP(int, osatex, shi->osatex);
	
	shi->dxco[0]= shi->dxco[1]= shi->dxco[2]= 0.0f;
	shi->dyco[0]= shi->dyco[1]= shi->dyco[2]= 0.0f;
	
	// but, set Osa stuff to zero where it can confuse texture code
	if(shi->mat->texco & (TEXCO_NORM|TEXCO_REFL) ) {
		shi->dxno[0]= shi->dxno[1]= shi->dxno[2]= 0.0f;
		shi->dyno[0]= shi->dyno[1]= shi->dyno[2]= 0.0f;
	}

	/* face normal, check for flip, need to set puno here */
	norflip= (vlr->n[0]*shi->view[0]+vlr->n[1]*shi->view[1]+vlr->n[2]*shi->view[2]) < 0.0f;
	
	if(norflip)
		shi->puno= vlr->puno ^ 15;// only flip lower 4 bits
	else
		shi->puno= vlr->puno;
	
	if(vlr->v4) {
		if(is->isect==2) 
			shade_input_set_triangle_i(shi, vlr, 2, 1, 3);
		else
			shade_input_set_triangle_i(shi, vlr, 0, 1, 3);
	}
	else {
		shade_input_set_triangle_i(shi, vlr, 0, 1, 2);
	}
	
	/* shade_input_set_triangle_i() sets facenor, now we flip */
	if(norflip) {
		shi->facenor[0]= -vlr->n[0];
		shi->facenor[1]= -vlr->n[1];
		shi->facenor[2]= -vlr->n[2];
	}	
	
	shi->u= is->u;
	shi->v= is->v;
	shi->dx_u= shi->dx_v= shi->dy_u= shi->dy_v=  0.0f;
	shade_input_set_normals(shi);
	shade_input_set_shade_texco(shi);
	
	if(is->mode==DDA_SHADOW_TRA) 
		shade_color(shi, shr);
	else {
		if(shi->mat->nodetree && shi->mat->use_nodes) {
			ntreeShaderExecTree(shi->mat->nodetree, shi, shr);
			shi->mat= vlr->mat;		/* shi->mat is being set in nodetree */
		}
		else
			shade_material_loop(shi, shr);
		
		/* raytrace likes to separate the spec color */
		VECSUB(shr->diff, shr->combined, shr->spec);
	}	
	
	SWAP(int, osatex, shi->osatex);  // XXXXX!!!!

}

static int refraction(float *refract, float *n, float *view, float index)
{
	float dot, fac;

	VECCOPY(refract, view);
	
	dot= view[0]*n[0] + view[1]*n[1] + view[2]*n[2];

	if(dot>0.0f) {
		index = 1.0f/index;
		fac= 1.0f - (1.0f - dot*dot)*index*index;
		if(fac<= 0.0f) return 0;
		fac= -dot*index + sqrt(fac);
	}
	else {
		fac= 1.0f - (1.0f - dot*dot)*index*index;
		if(fac<= 0.0f) return 0;
		fac= -dot*index - sqrt(fac);
	}

	refract[0]= index*view[0] + fac*n[0];
	refract[1]= index*view[1] + fac*n[1];
	refract[2]= index*view[2] + fac*n[2];

	return 1;
}

/* orn = original face normal */
static void reflection(float *ref, float *n, float *view, float *orn)
{
	float f1;
	
	f1= -2.0f*(n[0]*view[0]+ n[1]*view[1]+ n[2]*view[2]);
	
	ref[0]= (view[0]+f1*n[0]);
	ref[1]= (view[1]+f1*n[1]);
	ref[2]= (view[2]+f1*n[2]);

	if(orn) {
		/* test phong normals, then we should prevent vector going to the back */
		f1= ref[0]*orn[0]+ ref[1]*orn[1]+ ref[2]*orn[2];
		if(f1>0.0f) {
			f1+= .01f;
			ref[0]-= f1*orn[0];
			ref[1]-= f1*orn[1];
			ref[2]-= f1*orn[2];
		}
	}
}

#if 0
static void color_combine(float *result, float fac1, float fac2, float *col1, float *col2)
{
	float col1t[3], col2t[3];
	
	col1t[0]= sqrt(col1[0]);
	col1t[1]= sqrt(col1[1]);
	col1t[2]= sqrt(col1[2]);
	col2t[0]= sqrt(col2[0]);
	col2t[1]= sqrt(col2[1]);
	col2t[2]= sqrt(col2[2]);

	result[0]= (fac1*col1t[0] + fac2*col2t[0]);
	result[0]*= result[0];
	result[1]= (fac1*col1t[1] + fac2*col2t[1]);
	result[1]*= result[1];
	result[2]= (fac1*col1t[2] + fac2*col2t[2]);
	result[2]*= result[2];
}
#endif

static float shade_by_transmission(Isect *is, ShadeInput *shi, ShadeResult *shr)
{
	float dx, dy, dz, d, p;

	if (0 == (shi->mat->mode & (MA_RAYTRANSP|MA_ZTRA)))
		return -1;
	   
	if (shi->mat->tx_limit <= 0.0f) {
		d= 1.0f;
	} 
	else {
		/* shi.co[] calculated by shade_ray() */
		dx= shi->co[0] - is->start[0];
		dy= shi->co[1] - is->start[1];
		dz= shi->co[2] - is->start[2];
		d= sqrt(dx*dx+dy*dy+dz*dz);
		if (d > shi->mat->tx_limit)
			d= shi->mat->tx_limit;

		p = shi->mat->tx_falloff;
		if(p < 0.0f) p= 0.0f;
		else if (p > 10.0f) p= 10.0f;

		shr->alpha *= pow(d, p);
		if (shr->alpha > 1.0f)
			shr->alpha= 1.0f;
	}

	return d;
}

/* the main recursive tracer itself */
static void traceray(ShadeInput *origshi, short depth, float *start, float *vec, float *col, VlakRen *vlr, int traflag)
{
	ShadeInput shi;
	ShadeResult shr;
	Isect isec;
	float f, f1, fr, fg, fb;
	float ref[3];
	
	VECCOPY(isec.start, start);
	isec.end[0]= start[0]+R.oc.ocsize*vec[0];
	isec.end[1]= start[1]+R.oc.ocsize*vec[1];
	isec.end[2]= start[2]+R.oc.ocsize*vec[2];
	isec.mode= DDA_MIRROR;
	isec.vlrorig= vlr;

	if( d3dda(&isec) ) {
		float d= 1.0f;
		
		shi.mask= origshi->mask;
		shi.osatex= origshi->osatex;
		shi.depth= 1;					/* only used to indicate tracing */
		shi.thread= origshi->thread;
		shi.sample= 0;
		shi.xs= origshi->xs;
		shi.ys= origshi->ys;
		shi.lay= origshi->lay;
		shi.passflag= SCE_PASS_COMBINED; /* result of tracing needs no pass info */
		shi.combinedflag= 0xFFFFFF;		 /* ray trace does all options */
		shi.do_preview= 0;
		shi.light_override= origshi->light_override;
		shi.mat_override= origshi->mat_override;
		
		memset(&shr, 0, sizeof(ShadeResult));
		
		shade_ray(&isec, &shi, &shr);
		if (traflag & RAY_TRA)
			d= shade_by_transmission(&isec, &shi, &shr);
		
		if(depth>0) {

			if(shi.mat->mode_l & (MA_RAYTRANSP|MA_ZTRA) && shr.alpha < 1.0f) {
				float nf, f, f1, refract[3], tracol[4];
				
				tracol[0]= shi.r;
				tracol[1]= shi.g;
				tracol[2]= shi.b;
				tracol[3]= col[3];	// we pass on and accumulate alpha
				
				if(shi.mat->mode & MA_RAYTRANSP) {
					/* odd depths: use normal facing viewer, otherwise flip */
					if(traflag & RAY_TRAFLIP) {
						float norm[3];
						norm[0]= - shi.vn[0];
						norm[1]= - shi.vn[1];
						norm[2]= - shi.vn[2];
						if (!refraction(refract, norm, shi.view, shi.ang))
							reflection(refract, norm, shi.view, shi.vn);
					}
					else {
						if (!refraction(refract, shi.vn, shi.view, shi.ang))
							reflection(refract, shi.vn, shi.view, shi.vn);
					}
					traflag |= RAY_TRA;
					traceray(origshi, depth-1, shi.co, refract, tracol, shi.vlr, traflag ^ RAY_TRAFLIP);
				}
				else
					traceray(origshi, depth-1, shi.co, shi.view, tracol, shi.vlr, 0);
				
				f= shr.alpha; f1= 1.0f-f;
				nf= d * shi.mat->filter;
				fr= 1.0f+ nf*(shi.r-1.0f);
				fg= 1.0f+ nf*(shi.g-1.0f);
				fb= 1.0f+ nf*(shi.b-1.0f);
				shr.diff[0]= f*shr.diff[0] + f1*fr*tracol[0];
				shr.diff[1]= f*shr.diff[1] + f1*fg*tracol[1];
				shr.diff[2]= f*shr.diff[2] + f1*fb*tracol[2];
				
				shr.spec[0] *=f;
				shr.spec[1] *=f;
				shr.spec[2] *=f;

				col[3]= f1*tracol[3] + f;
			}
			else 
				col[3]= 1.0f;

			if(shi.mat->mode_l & MA_RAYMIRROR) {
				f= shi.ray_mirror;
				if(f!=0.0f) f*= fresnel_fac(shi.view, shi.vn, shi.mat->fresnel_mir_i, shi.mat->fresnel_mir);
			}
			else f= 0.0f;
			
			if(f!=0.0f) {
				float mircol[4];
				
				reflection(ref, shi.vn, shi.view, NULL);			
				traceray(origshi, depth-1, shi.co, ref, mircol, shi.vlr, 0);
			
				f1= 1.0f-f;

				/* combine */
				//color_combine(col, f*fr*(1.0f-shr.spec[0]), f1, col, shr.diff);
				//col[0]+= shr.spec[0];
				//col[1]+= shr.spec[1];
				//col[2]+= shr.spec[2];
				
				fr= shi.mirr;
				fg= shi.mirg;
				fb= shi.mirb;
		
				col[0]= f*fr*(1.0f-shr.spec[0])*mircol[0] + f1*shr.diff[0] + shr.spec[0];
				col[1]= f*fg*(1.0f-shr.spec[1])*mircol[1] + f1*shr.diff[1] + shr.spec[1];
				col[2]= f*fb*(1.0f-shr.spec[2])*mircol[2] + f1*shr.diff[2] + shr.spec[2];
			}
			else {
				col[0]= shr.diff[0] + shr.spec[0];
				col[1]= shr.diff[1] + shr.spec[1];
				col[2]= shr.diff[2] + shr.spec[2];
			}
		}
		else {
			col[0]= shr.diff[0] + shr.spec[0];
			col[1]= shr.diff[1] + shr.spec[1];
			col[2]= shr.diff[2] + shr.spec[2];
		}
		
	}
	else {	/* sky */
		VECCOPY(shi.view, vec);
		Normalise(shi.view);
		
		shadeSkyView(col, isec.start, shi.view, NULL);
	}
}

/* **************** jitter blocks ********** */

/* calc distributed planar energy */

static void DP_energy(float *table, float *vec, int tot, float xsize, float ysize)
{
	int x, y, a;
	float *fp, force[3], result[3];
	float dx, dy, dist, min;
	
	min= MIN2(xsize, ysize);
	min*= min;
	result[0]= result[1]= 0.0f;
	
	for(y= -1; y<2; y++) {
		dy= ysize*y;
		for(x= -1; x<2; x++) {
			dx= xsize*x;
			fp= table;
			for(a=0; a<tot; a++, fp+= 2) {
				force[0]= vec[0] - fp[0]-dx;
				force[1]= vec[1] - fp[1]-dy;
				dist= force[0]*force[0] + force[1]*force[1];
				if(dist < min && dist>0.0f) {
					result[0]+= force[0]/dist;
					result[1]+= force[1]/dist;
				}
			}
		}
	}
	vec[0] += 0.1*min*result[0]/(float)tot;
	vec[1] += 0.1*min*result[1]/(float)tot;
	// cyclic clamping
	vec[0]= vec[0] - xsize*floor(vec[0]/xsize + 0.5);
	vec[1]= vec[1] - ysize*floor(vec[1]/ysize + 0.5);
}

// random offset of 1 in 2
static void jitter_plane_offset(float *jitter1, float *jitter2, int tot, float sizex, float sizey, float ofsx, float ofsy)
{
	float dsizex= sizex*ofsx;
	float dsizey= sizey*ofsy;
	float hsizex= 0.5*sizex, hsizey= 0.5*sizey;
	int x;
	
	for(x=tot; x>0; x--, jitter1+=2, jitter2+=2) {
		jitter2[0]= jitter1[0] + dsizex;
		jitter2[1]= jitter1[1] + dsizey;
		if(jitter2[0] > hsizex) jitter2[0]-= sizex;
		if(jitter2[1] > hsizey) jitter2[1]-= sizey;
	}
}

/* called from convertBlenderScene.c */
/* we do this in advance to get consistant random, not alter the render seed, and be threadsafe */
void init_jitter_plane(LampRen *lar)
{
	float *fp;
	int x, iter=12, tot= lar->ray_totsamp;
	
	/* at least 4, or max threads+1 tables */
	if(BLENDER_MAX_THREADS < 4) x= 4;
	else x= BLENDER_MAX_THREADS+1;
	fp= lar->jitter= MEM_mallocN(x*tot*2*sizeof(float), "lamp jitter tab");
	
	/* set per-lamp fixed seed */
	BLI_srandom(tot);
	
	/* fill table with random locations, area_size large */
	for(x=0; x<tot; x++, fp+=2) {
		fp[0]= (BLI_frand()-0.5)*lar->area_size;
		fp[1]= (BLI_frand()-0.5)*lar->area_sizey;
	}
	
	while(iter--) {
		fp= lar->jitter;
		for(x=tot; x>0; x--, fp+=2) {
			DP_energy(lar->jitter, fp, tot, lar->area_size, lar->area_sizey);
		}
	}
	
	/* create the dithered tables (could just check lamp type!) */
	jitter_plane_offset(lar->jitter, lar->jitter+2*tot, tot, lar->area_size, lar->area_sizey, 0.5f, 0.0f);
	jitter_plane_offset(lar->jitter, lar->jitter+4*tot, tot, lar->area_size, lar->area_sizey, 0.5f, 0.5f);
	jitter_plane_offset(lar->jitter, lar->jitter+6*tot, tot, lar->area_size, lar->area_sizey, 0.0f, 0.5f);
}

/* table around origin, -0.5*size to 0.5*size */
static float *give_jitter_plane(LampRen *lar, int thread, int xs, int ys)
{
	int tot;
	
	tot= lar->ray_totsamp;
			
	if(lar->ray_samp_type & LA_SAMP_JITTER) {
		/* made it threadsafe */
		
		if(lar->xold[thread]!=xs || lar->yold[thread]!=ys) {
			jitter_plane_offset(lar->jitter, lar->jitter+2*(thread+1)*tot, tot, lar->area_size, lar->area_sizey, BLI_thread_frand(thread), BLI_thread_frand(thread));
			lar->xold[thread]= xs; 
			lar->yold[thread]= ys;
		}
		return lar->jitter+2*(thread+1)*tot;
	}
	if(lar->ray_samp_type & LA_SAMP_DITHER) {
		return lar->jitter + 2*tot*((xs & 1)+2*(ys & 1));
	}
	
	return lar->jitter;
}


/* ***************** main calls ************** */


/* extern call from render loop */
void ray_trace(ShadeInput *shi, ShadeResult *shr)
{
	VlakRen *vlr;
	float i, f, f1, fr, fg, fb, vec[3], mircol[4], tracol[4];
	float diff[3];
	int do_tra, do_mir;
	
	do_tra= ((shi->mat->mode & (MA_RAYTRANSP)) && shr->alpha!=1.0f);
	do_mir= ((shi->mat->mode & MA_RAYMIRROR) && shi->ray_mirror!=0.0f);
	vlr= shi->vlr;
	
	/* raytrace mirror amd refract like to separate the spec color */
	if(shi->combinedflag & SCE_PASS_SPEC)
		VECSUB(diff, shr->combined, shr->spec) /* no ; */
	else
		VECCOPY(diff, shr->combined);
	
	if(do_tra) {
		float refract[3];
		float olddiff[3];
		
		tracol[3]= shr->alpha;
		
		refraction(refract, shi->vn, shi->view, shi->ang);
		traceray(shi, shi->mat->ray_depth_tra, shi->co, refract, tracol, shi->vlr, RAY_TRA|RAY_TRAFLIP);
		
		f= shr->alpha; f1= 1.0f-f;
		fr= 1.0f+ shi->mat->filter*(shi->r-1.0f);
		fg= 1.0f+ shi->mat->filter*(shi->g-1.0f);
		fb= 1.0f+ shi->mat->filter*(shi->b-1.0f);
		
		/* for refract pass */
		VECCOPY(olddiff, diff);
		
		diff[0]= f*diff[0] + f1*fr*tracol[0];
		diff[1]= f*diff[1] + f1*fg*tracol[1];
		diff[2]= f*diff[2] + f1*fb*tracol[2];
		
		if(shi->passflag & SCE_PASS_REFRACT)
			VECSUB(shr->refr, diff, olddiff);
		
		if(shi->combinedflag & SCE_PASS_REFRACT)
			VECCOPY(olddiff, diff);
		
		shr->alpha= tracol[3];
	}
	
	if(do_mir) {
	
		i= shi->ray_mirror*fresnel_fac(shi->view, shi->vn, shi->mat->fresnel_mir_i, shi->mat->fresnel_mir);
		if(i!=0.0f) {
			
			fr= i*shi->mirr;
			fg= i*shi->mirg;
			fb= i*shi->mirb;

			if(vlr->flag & R_SMOOTH) 
				reflection(vec, shi->vn, shi->view, shi->facenor);
			else
				reflection(vec, shi->vn, shi->view, NULL);
	
			traceray(shi, shi->mat->ray_depth, shi->co, vec, mircol, shi->vlr, 0);
			
			if(shi->passflag & SCE_PASS_REFLECT) {
				/* mirror pass is not blocked out with spec */
				shr->refl[0]= fr*mircol[0] - fr*diff[0];
				shr->refl[1]= fg*mircol[1] - fg*diff[1];
				shr->refl[2]= fb*mircol[2] - fb*diff[2];
			}
			
			if(shi->combinedflag & SCE_PASS_REFLECT) {
				
				f= fr*(1.0f-shr->spec[0]);	f1= 1.0f-i;
				diff[0]= f*mircol[0] + f1*diff[0];
				
				f= fg*(1.0f-shr->spec[1]);	f1= 1.0f-i;
				diff[1]= f*mircol[1] + f1*diff[1];
				
				f= fb*(1.0f-shr->spec[2]);	f1= 1.0f-i;
				diff[2]= f*mircol[2] + f1*diff[2];
			}
		}
	}
	/* put back together */
	if(shi->combinedflag & SCE_PASS_SPEC)
		VECADD(shr->combined, diff, shr->spec) /* no ; */
	else
		VECCOPY(shr->combined, diff);
}

/* color 'shadfac' passes through 'col' with alpha and filter */
/* filter is only applied on alpha defined transparent part */
static void addAlphaLight(float *shadfac, float *col, float alpha, float filter)
{
	float fr, fg, fb;
	
	fr= 1.0f+ filter*(col[0]-1.0f);
	fg= 1.0f+ filter*(col[1]-1.0f);
	fb= 1.0f+ filter*(col[2]-1.0f);
	
	shadfac[0]= alpha*col[0] + fr*(1.0f-alpha)*shadfac[0];
	shadfac[1]= alpha*col[1] + fg*(1.0f-alpha)*shadfac[1];
	shadfac[2]= alpha*col[2] + fb*(1.0f-alpha)*shadfac[2];
	
	shadfac[3]= (1.0f-alpha)*shadfac[3];
}

static void ray_trace_shadow_tra(Isect *is, int depth, int traflag)
{
	/* ray to lamp, find first face that intersects, check alpha properties,
	   if it has col[3]>0.0f  continue. so exit when alpha is full */
	ShadeInput shi;
	ShadeResult shr;

	if( d3dda(is)) {
		float d= 1.0f;
		/* we got a face */
		
		shi.depth= 1;					/* only used to indicate tracing */
		shi.mask= 1;
		shi.osatex= 0;
		shi.thread= shi.sample= 0;
		shi.lay= 0;
		shi.passflag= 0;
		shi.combinedflag= 0;
		shi.do_preview= 0;
		shi.light_override= NULL;
		shi.mat_override= NULL;
		
		shade_ray(is, &shi, &shr);
		if (traflag & RAY_TRA)
			d= shade_by_transmission(is, &shi, &shr);
		
		/* mix colors based on shadfac (rgb + amount of light factor) */
		addAlphaLight(is->col, shr.diff, shr.alpha, d*shi.mat->filter);
		
		if(depth>0 && is->col[3]>0.0f) {
			
			/* adapt isect struct */
			VECCOPY(is->start, shi.co);
			is->vlrorig= shi.vlr;

			ray_trace_shadow_tra(is, depth-1, traflag | RAY_TRA);
		}
	}
}

/* not used, test function for ambient occlusion (yaf: pathlight) */
/* main problem; has to be called within shading loop, giving unwanted recursion */
int ray_trace_shadow_rad(ShadeInput *ship, ShadeResult *shr)
{
	static int counter=0, only_one= 0;
	extern float hashvectf[];
	Isect isec;
	ShadeInput shi;
	ShadeResult shr_t;
	float vec[3], accum[3], div= 0.0f;
	int a;
	
	if(only_one) {
		return 0;
	}
	only_one= 1;
	
	accum[0]= accum[1]= accum[2]= 0.0f;
	isec.mode= DDA_MIRROR;
	isec.vlrorig= ship->vlr;
	
	for(a=0; a<8*8; a++) {
		
		counter+=3;
		counter %= 768;
		VECCOPY(vec, hashvectf+counter);
		if(ship->vn[0]*vec[0]+ship->vn[1]*vec[1]+ship->vn[2]*vec[2]>0.0f) {
			vec[0]-= vec[0];
			vec[1]-= vec[1];
			vec[2]-= vec[2];
		}
		VECCOPY(isec.start, ship->co);
		isec.end[0]= isec.start[0] + R.oc.ocsize*vec[0];
		isec.end[1]= isec.start[1] + R.oc.ocsize*vec[1];
		isec.end[2]= isec.start[2] + R.oc.ocsize*vec[2];
		
		if( d3dda(&isec)) {
			float fac;
			shade_ray(&isec, &shi, &shr_t);
			fac= isec.labda*isec.labda;
			fac= 1.0f;
			accum[0]+= fac*(shr_t.diff[0]+shr_t.spec[0]);
			accum[1]+= fac*(shr_t.diff[1]+shr_t.spec[1]);
			accum[2]+= fac*(shr_t.diff[2]+shr_t.spec[2]);
			div+= fac;
		}
		else div+= 1.0f;
	}
	
	if(div!=0.0f) {
		shr->diff[0]+= accum[0]/div;
		shr->diff[1]+= accum[1]/div;
		shr->diff[2]+= accum[2]/div;
	}
	shr->alpha= 1.0f;
	
	only_one= 0;
	return 1;
}

/* aolight: function to create random unit sphere vectors for total random sampling */
static void RandomSpherical(float *v)
{
	float r;
	v[2] = 2.f*BLI_frand()-1.f;
	if ((r = 1.f - v[2]*v[2])>0.f) {
		float a = 6.283185307f*BLI_frand();
		r = sqrt(r);
		v[0] = r * cos(a);
		v[1] = r * sin(a);
	}
	else v[2] = 1.f;
}

/* calc distributed spherical energy */
static void DS_energy(float *sphere, int tot, float *vec)
{
	float *fp, fac, force[3], res[3];
	int a;
	
	res[0]= res[1]= res[2]= 0.0f;
	
	for(a=0, fp=sphere; a<tot; a++, fp+=3) {
		VecSubf(force, vec, fp);
		fac= force[0]*force[0] + force[1]*force[1] + force[2]*force[2];
		if(fac!=0.0f) {
			fac= 1.0f/fac;
			res[0]+= fac*force[0];
			res[1]+= fac*force[1];
			res[2]+= fac*force[2];
		}
	}

	VecMulf(res, 0.5);
	VecAddf(vec, vec, res);
	Normalise(vec);
	
}

/* called from convertBlenderScene.c */
/* creates an equally distributed spherical sample pattern */
/* and allocates threadsafe memory */
void init_ao_sphere(World *wrld)
{
	float *fp;
	int a, tot, iter= 16;

	/* we make twice the amount of samples, because only a hemisphere is used */
	tot= 2*wrld->aosamp*wrld->aosamp;
	
	wrld->aosphere= MEM_mallocN(3*tot*sizeof(float), "AO sphere");
	
	/* fixed random */
	BLI_srandom(tot);
	
	/* init */
	fp= wrld->aosphere;
	for(a=0; a<tot; a++, fp+= 3) {
		RandomSpherical(fp);
	}
	
	while(iter--) {
		for(a=0, fp= wrld->aosphere; a<tot; a++, fp+= 3) {
			DS_energy(wrld->aosphere, tot, fp);
		}
	}
	
	/* tables */
	wrld->aotables= MEM_mallocN(BLENDER_MAX_THREADS*3*tot*sizeof(float), "AO tables");
}

/* give per thread a table, we have to compare xs ys because of way OSA works... */
static float *threadsafe_table_sphere(int test, int thread, int xs, int ys, int tot)
{
	static int xso[BLENDER_MAX_THREADS], yso[BLENDER_MAX_THREADS];
	static int firsttime= 1;
	
	if(firsttime) {
		memset(xso, 255, sizeof(xso));
		memset(yso, 255, sizeof(yso));
		firsttime= 0;
	}
	
	if(xs==xso[thread] && ys==yso[thread]) return R.wrld.aotables+ thread*tot*3;
	if(test) return NULL;
	xso[thread]= xs; yso[thread]= ys;
	return R.wrld.aotables+ thread*tot*3;
}

static float *sphere_sampler(int type, int resol, int thread, int xs, int ys)
{
	int tot;
	float *vec;
	
	if(resol>16) resol= 16;
	
	tot= 2*resol*resol;

	if (type & WO_AORNDSMP) {
		static float sphere[2*3*256];
		int a;
		
		/* total random sampling. NOT THREADSAFE! (should be removed, is not useful) */
		vec= sphere;
		for (a=0; a<tot; a++, vec+=3) {
			RandomSpherical(vec);
		}
		
		return sphere;
	} 
	else {
		float *sphere;
		float cosfi, sinfi, cost, sint;
		float ang, *vec1;
		int a;
		
		sphere= threadsafe_table_sphere(1, thread, xs, ys, tot);	// returns table if xs and ys were equal to last call
		if(sphere==NULL) {
			sphere= threadsafe_table_sphere(0, thread, xs, ys, tot);
			
			// random rotation
			ang= BLI_thread_frand(thread);
			sinfi= sin(ang); cosfi= cos(ang);
			ang= BLI_thread_frand(thread);
			sint= sin(ang); cost= cos(ang);
			
			vec= R.wrld.aosphere;
			vec1= sphere;
			for (a=0; a<tot; a++, vec+=3, vec1+=3) {
				vec1[0]= cost*cosfi*vec[0] - sinfi*vec[1] + sint*cosfi*vec[2];
				vec1[1]= cost*sinfi*vec[0] + cosfi*vec[1] + sint*sinfi*vec[2];
				vec1[2]= -sint*vec[0] + cost*vec[2];			
			}
		}
		return sphere;
	}
}


/* extern call from shade_lamp_loop, ambient occlusion calculus */
void ray_ao(ShadeInput *shi, float *shadfac)
{
	Isect isec;
	float *vec, *nrm, div, bias, sh=0.0f;
	float maxdist = R.wrld.aodist;
	float dxyview[3];
	int j= -1, tot, actual=0, skyadded=0, aocolor;

	isec.vlrorig= shi->vlr;
	isec.vlr_last= NULL;
	isec.mode= (R.wrld.aomode & WO_AODIST)?DDA_SHADOW_TRA:DDA_SHADOW;
	isec.lay= -1;

	shadfac[0]= shadfac[1]= shadfac[2]= 0.0f;

	/* bias prevents smoothed faces to appear flat */
	if(shi->vlr->flag & R_SMOOTH) {
		bias= G.scene->world->aobias;
		nrm= shi->vn;
	}
	else {
		bias= 0.0f;
		nrm= shi->facenor;
	}

	/* prevent sky colors to be added for only shadow (shadow becomes alpha) */
	aocolor= R.wrld.aocolor;
	if(shi->mat->mode & MA_ONLYSHADOW)
		aocolor= WO_AOPLAIN;
	
	vec= sphere_sampler(R.wrld.aomode, R.wrld.aosamp, shi->thread, shi->xs, shi->ys);
	
	// warning: since we use full sphere now, and dotproduct is below, we do twice as much
	tot= 2*R.wrld.aosamp*R.wrld.aosamp;

	if(aocolor == WO_AOSKYTEX) {
		dxyview[0]= 1.0f/(float)R.wrld.aosamp;
		dxyview[1]= 1.0f/(float)R.wrld.aosamp;
		dxyview[2]= 0.0f;
	}
	
	while(tot--) {
		
		if ((vec[0]*nrm[0] + vec[1]*nrm[1] + vec[2]*nrm[2]) > bias) {
			/* only ao samples for mask */
			if(R.r.mode & R_OSA) {
				j++;
				if(j==R.osa) j= 0;
				if(!(shi->mask & (1<<j))) {
					vec+=3;
					continue;
				}
			}
			
			actual++;
			
			/* always set start/end, 3dda clips it */
			VECCOPY(isec.start, shi->co);
			isec.end[0] = shi->co[0] - maxdist*vec[0];
			isec.end[1] = shi->co[1] - maxdist*vec[1];
			isec.end[2] = shi->co[2] - maxdist*vec[2];
			
			/* do the trace */
			if (d3dda(&isec)) {
				if (R.wrld.aomode & WO_AODIST) sh+= exp(-isec.labda*R.wrld.aodistfac); 
				else sh+= 1.0f;
			}
			else if(aocolor!=WO_AOPLAIN) {
				float skycol[4];
				float fac, view[3];
				
				view[0]= -vec[0];
				view[1]= -vec[1];
				view[2]= -vec[2];
				Normalise(view);
				
				if(aocolor==WO_AOSKYCOL) {
					fac= 0.5*(1.0f+view[0]*R.grvec[0]+ view[1]*R.grvec[1]+ view[2]*R.grvec[2]);
					shadfac[0]+= (1.0f-fac)*R.wrld.horr + fac*R.wrld.zenr;
					shadfac[1]+= (1.0f-fac)*R.wrld.horg + fac*R.wrld.zeng;
					shadfac[2]+= (1.0f-fac)*R.wrld.horb + fac*R.wrld.zenb;
				}
				else {	/* WO_AOSKYTEX */
					shadeSkyView(skycol, isec.start, view, dxyview);
					shadfac[0]+= skycol[0];
					shadfac[1]+= skycol[1];
					shadfac[2]+= skycol[2];
				}
				skyadded++;
			}
		}
		// samples
		vec+= 3;
	}
	
	if(actual==0) sh= 1.0f;
	else sh = 1.0f - sh/((float)actual);
	
	if(aocolor!=WO_AOPLAIN && skyadded) {
		div= sh/((float)skyadded);
		
		shadfac[0]*= div;	// average color times distances/hits formula
		shadfac[1]*= div;	// average color times distances/hits formula
		shadfac[2]*= div;	// average color times distances/hits formula
	}
	else {
		shadfac[0]= shadfac[1]= shadfac[2]= sh;
	}
}



/* extern call from shade_lamp_loop */
void ray_shadow(ShadeInput *shi, LampRen *lar, float *shadfac)
{
	Isect isec;
	float lampco[3];

	/* setup isec */
	if(shi->mat->mode & MA_SHADOW_TRA) isec.mode= DDA_SHADOW_TRA;
	else isec.mode= DDA_SHADOW;
	
	if(lar->mode & LA_LAYER) isec.lay= lar->lay; else isec.lay= -1;

	/* only when not mir tracing, first hit optimm */
	if(shi->depth==0) 
		isec.vlr_last= lar->vlr_last[shi->thread];
	else 
		isec.vlr_last= NULL;
	
	
	if(lar->type==LA_SUN || lar->type==LA_HEMI) {
		lampco[0]= shi->co[0] - R.oc.ocsize*lar->vec[0];
		lampco[1]= shi->co[1] - R.oc.ocsize*lar->vec[1];
		lampco[2]= shi->co[2] - R.oc.ocsize*lar->vec[2];
	}
	else {
		VECCOPY(lampco, lar->co);
	}
	
	if(lar->ray_totsamp<2) {
		
		isec.vlrorig= shi->vlr;
		shadfac[3]= 1.0f; // 1.0=full light
		
		/* set up isec vec */
		VECCOPY(isec.start, shi->co);
		VECCOPY(isec.end, lampco);

		if(isec.mode==DDA_SHADOW_TRA) {
			/* isec.col is like shadfac, so defines amount of light (0.0 is full shadow) */
			isec.col[0]= isec.col[1]= isec.col[2]=  1.0f;
			isec.col[3]= 1.0f;

			ray_trace_shadow_tra(&isec, DEPTH_SHADOW_TRA, 0);
			QUATCOPY(shadfac, isec.col);
			//printf("shadfac %f %f %f %f\n", shadfac[0], shadfac[1], shadfac[2], shadfac[3]);
		}
		else if( d3dda(&isec)) shadfac[3]= 0.0f;
	}
	else {
		/* area soft shadow */
		float *jitlamp;
		float fac=0.0f, div=0.0f, vec[3];
		int a, j= -1, mask;
		
		if(isec.mode==DDA_SHADOW_TRA) {
			shadfac[0]= shadfac[1]= shadfac[2]= shadfac[3]= 0.0f;
		}
		else shadfac[3]= 1.0f;							// 1.0=full light
		
		fac= 0.0f;
		jitlamp= give_jitter_plane(lar, shi->thread, shi->xs, shi->ys);

		a= lar->ray_totsamp;
		
		/* this correction to make sure we always take at least 1 sample */
		mask= shi->mask;
		if(a==4) mask |= (mask>>4)|(mask>>8);
		else if(a==9) mask |= (mask>>9);
		
		while(a--) {
			
			if(R.r.mode & R_OSA) {
				j++;
				if(j>=R.osa) j= 0;
				if(!(mask & (1<<j))) {
					jitlamp+= 2;
					continue;
				}
			}
			
			isec.vlrorig= shi->vlr;	// ray_trace_shadow_tra changes it
			
			vec[0]= jitlamp[0];
			vec[1]= jitlamp[1];
			vec[2]= 0.0f;
			Mat3MulVecfl(lar->mat, vec);
			
			/* set start and end, d3dda clips it */
			VECCOPY(isec.start, shi->co);
			isec.end[0]= lampco[0]+vec[0];
			isec.end[1]= lampco[1]+vec[1];
			isec.end[2]= lampco[2]+vec[2];
			
			if(isec.mode==DDA_SHADOW_TRA) {
				/* isec.col is like shadfac, so defines amount of light (0.0 is full shadow) */
				isec.col[0]= isec.col[1]= isec.col[2]=  1.0f;
				isec.col[3]= 1.0f;
				
				ray_trace_shadow_tra(&isec, DEPTH_SHADOW_TRA, 0);
				shadfac[0] += isec.col[0];
				shadfac[1] += isec.col[1];
				shadfac[2] += isec.col[2];
				shadfac[3] += isec.col[3];
			}
			else if( d3dda(&isec) ) fac+= 1.0f;
			
			div+= 1.0f;
			jitlamp+= 2;
		}
		
		if(isec.mode==DDA_SHADOW_TRA) {
			shadfac[0] /= div;
			shadfac[1] /= div;
			shadfac[2] /= div;
			shadfac[3] /= div;
		}
		else {
			// sqrt makes nice umbra effect
			if(lar->ray_samp_type & LA_SAMP_UMBRA)
				shadfac[3]= sqrt(1.0f-fac/div);
			else
				shadfac[3]= 1.0f-fac/div;
		}
	}

	/* for first hit optim, set last interesected shadow face */
	if(shi->depth==0) 
		lar->vlr_last[shi->thread]= isec.vlr_last;

}

/* only when face points away from lamp, in direction of lamp, trace ray and find first exit point */
void ray_translucent(ShadeInput *shi, LampRen *lar, float *distfac, float *co)
{
	Isect isec;
	float lampco[3];
	
	/* setup isec */
	isec.mode= DDA_SHADOW_TRA;
	
	if(lar->mode & LA_LAYER) isec.lay= lar->lay; else isec.lay= -1;
	
	if(lar->type==LA_SUN || lar->type==LA_HEMI) {
		lampco[0]= shi->co[0] - R.oc.ocsize*lar->vec[0];
		lampco[1]= shi->co[1] - R.oc.ocsize*lar->vec[1];
		lampco[2]= shi->co[2] - R.oc.ocsize*lar->vec[2];
	}
	else {
		VECCOPY(lampco, lar->co);
	}
	
	isec.vlrorig= shi->vlr;
	
	/* set up isec vec */
	VECCOPY(isec.start, shi->co);
	VECCOPY(isec.end, lampco);
	
	if( d3dda(&isec)) {
		/* we got a face */
		
		/* render co */
		co[0]= isec.start[0]+isec.labda*(isec.vec[0]);
		co[1]= isec.start[1]+isec.labda*(isec.vec[1]);
		co[2]= isec.start[2]+isec.labda*(isec.vec[2]);
		
		*distfac= VecLength(isec.vec);
	}
	else
		*distfac= 0.0f;
}


