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
 * The Original Code is Copyright (C) 1990-1998 NeoGeo BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */


#include <math.h>
#include <string.h>
#include <stdlib.h>

#include "MEM_guardedalloc.h"

#include "DNA_material_types.h"
#include "DNA_lamp_types.h"
#include "DNA_mesh_types.h"

#include "BKE_utildefines.h"

#include "BLI_arithb.h"

#include "render.h"
#include "render_intern.h"
#include "rendercore.h"
#include "pixelblending.h"
#include "jitter.h"
#include "texture.h"

#define OCRES	64

#define DDA_SHADOW 0
#define DDA_MIRROR 1
#define DDA_SHADOW_TRA 2

#define DEPTH_SHADOW_TRA  10

/* ********** structs *************** */

typedef struct Octree {
	struct Branch *adrbranch[256];
	struct Node *adrnode[256];
	float ocsize;	/* ocsize: mult factor,  max size octree */
	float ocfacx,ocfacy,ocfacz;
	float min[3], max[3];
	/* for optimize, last intersected face */
	VlakRen *vlr_last;

} Octree;

typedef struct Isect {
	float start[3], end[3];
	float labda, u, v;
	struct VlakRen *vlr, *vlrcontr, *vlrorig;
	short isect, mode;	/* mode: DDA_SHADOW or DDA_MIRROR or DDA_SHADOW_TRA */
	float ddalabda;
	float col[4];		/* RGBA for shadow_tra */
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

static Octree g_oc;	/* can be scene pointer or so later... */

/* just for statistics */
static int raycount, branchcount, nodecount;
static int accepted, rejected, coherent_ray;


/* **************** ocval method ******************* */
/* within one octree node, a set of 3x15 bits defines a 'boundbox' to OR with */

#define OCVALRES	15
#define BROW(min, max)      (((max)>=OCVALRES? 0xFFFF: (1<<(max+1))-1) - ((min>0)? ((1<<(min))-1):0) )

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
	ov->ocx= BROW(ocmin, ocmax);
	
	ocmin= OCVALRES*(min[1]-y); 
	ocmax= OCVALRES*(max[1]-y);
	ov->ocy= BROW(ocmin, ocmax);
	
	ocmin= OCVALRES*(min[2]-z); 
	ocmax= OCVALRES*(max[2]-z);
	ov->ocz= BROW(ocmin, ocmax);

}

static void calc_ocval_ray(OcVal *ov, float x1, float y1, float z1, 
											  float x2, float y2, float z2)
{
	static float ox1, ox2, oy1, oy2, oz1, oz2;
	
	if(ov==NULL) {
		ox1= x1; ox2= x2;
		oy1= y1; oy2= y2;
		oz1= z1; oz2= z2;
	}
	else {
		int ocmin, ocmax;
		
		if(ox1<ox2) {
			ocmin= OCVALRES*(ox1 - ((int)x1));
			ocmax= OCVALRES*(ox2 - ((int)x1));
		} else {
			ocmin= OCVALRES*(ox2 - ((int)x1));
			ocmax= OCVALRES*(ox1 - ((int)x1));
		}
		ov->ocx= BROW(ocmin, ocmax);

		if(oy1<oy2) {
			ocmin= OCVALRES*(oy1 - ((int)y1));
			ocmax= OCVALRES*(oy2 - ((int)y1));
		} else {
			ocmin= OCVALRES*(oy2 - ((int)y1));
			ocmax= OCVALRES*(oy1 - ((int)y1));
		}
		ov->ocy= BROW(ocmin, ocmax);

		if(oz1<oz2) {
			ocmin= OCVALRES*(oz1 - ((int)z1));
			ocmax= OCVALRES*(oz2 - ((int)z1));
		} else {
			ocmin= OCVALRES*(oz2 - ((int)z1));
			ocmax= OCVALRES*(oz1 - ((int)z1));
		}
		ov->ocz= BROW(ocmin, ocmax);
		
	}
}

/* ************* octree ************** */

static Branch *addbranch(Branch *br, short oc)
{
	
	if(br->b[oc]) return br->b[oc];
	
	branchcount++;
	if(g_oc.adrbranch[branchcount>>8]==0)
		g_oc.adrbranch[branchcount>>8]= MEM_callocN(256*sizeof(Branch),"addbranch");

	if(branchcount>= 256*256) {
		printf("error; octree branches full\n");
		branchcount=0;
	}
	
	return br->b[oc]=g_oc.adrbranch[branchcount>>8]+(branchcount & 255);
}

static Node *addnode(void)
{
	
	nodecount++;
	if(g_oc.adrnode[nodecount>>12]==0)
		g_oc.adrnode[nodecount>>12]= MEM_callocN(4096*sizeof(Node),"addnode");

	if(nodecount> 256*4096) {
		printf("error; octree nodes full\n");
		nodecount=0;
	}
	
	return g_oc.adrnode[nodecount>>12]+(nodecount & 4095);
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
	
	if((x+0)*nor[0] + (y+0)*nor[1] + (z+0)*nor[2] + d > 0.0) {
		if((x+1)*nor[0] + (y+0)*nor[1] + (z+0)*nor[2] + d < 0.0) return 1;
		if((x+0)*nor[0] + (y+1)*nor[1] + (z+0)*nor[2] + d < 0.0) return 1;
		if((x+1)*nor[0] + (y+1)*nor[1] + (z+0)*nor[2] + d < 0.0) return 1;
	
		if((x+0)*nor[0] + (y+0)*nor[1] + (z+1)*nor[2] + d < 0.0) return 1;
		if((x+1)*nor[0] + (y+0)*nor[1] + (z+1)*nor[2] + d < 0.0) return 1;
		if((x+0)*nor[0] + (y+1)*nor[1] + (z+1)*nor[2] + d < 0.0) return 1;
		if((x+1)*nor[0] + (y+1)*nor[1] + (z+1)*nor[2] + d < 0.0) return 1;
	}
	else {
		if((x+1)*nor[0] + (y+0)*nor[1] + (z+0)*nor[2] + d > 0.0) return 1;
		if((x+0)*nor[0] + (y+1)*nor[1] + (z+0)*nor[2] + d > 0.0) return 1;
		if((x+1)*nor[0] + (y+1)*nor[1] + (z+0)*nor[2] + d > 0.0) return 1;
	
		if((x+0)*nor[0] + (y+0)*nor[1] + (z+1)*nor[2] + d > 0.0) return 1;
		if((x+1)*nor[0] + (y+0)*nor[1] + (z+1)*nor[2] + d > 0.0) return 1;
		if((x+0)*nor[0] + (y+1)*nor[1] + (z+1)*nor[2] + d > 0.0) return 1;
		if((x+1)*nor[0] + (y+1)*nor[1] + (z+1)*nor[2] + d > 0.0) return 1;
	}

	return 0;
}

static void ocwrite(VlakRen *vlr, short x, short y, short z, float rtf[][3])
{
	Branch *br;
	Node *no;
	short a, oc0, oc1, oc2, oc3, oc4, oc5;

	if(face_in_node(NULL, x,y,z, rtf)==0) return;

	x<<=2;
	y<<=1;
	oc0= ((x & 128)+(y & 64)+(z & 32))>>5;
	oc1= ((x & 64)+(y & 32)+(z & 16))>>4;
	oc2= ((x & 32)+(y & 16)+(z & 8))>>3;
	oc3= ((x & 16)+(y & 8)+(z & 4))>>2;
	oc4= ((x & 8)+(y & 4)+(z & 2))>>1;
	oc5= ((x & 4)+(y & 2)+(z & 1));

	br= addbranch(g_oc.adrbranch[0],oc0);
	br= addbranch(br,oc1);
	br= addbranch(br,oc2);
	br= addbranch(br,oc3);
	br= addbranch(br,oc4);
	no= (Node *)br->b[oc5];
	if(no==NULL) br->b[oc5]= (Branch *)(no= addnode());

	while(no->next) no= no->next;

	a= 0;
	if(no->v[7]) {		/* node full */
		no->next= addnode();
		no= no->next;
	}
	else {
		while(no->v[a]!=NULL) a++;
	}
	
	no->v[a]= vlr;
	
	calc_ocval_face(rtf[0], rtf[1], rtf[2], rtf[3], x>>2, y>>1, z, &no->ov[a]);

}

static void d2dda(short b1, short b2, short c1, short c2, char *ocvlak, short rts[][3], float rtf[][3])
{
	short ocx1,ocx2,ocy1,ocy2;
	short x,y,dx=0,dy=0;
	float ox1,ox2,oy1,oy2;
	float labda,labdao,labdax,labday,ldx,ldy;

	ocx1= rts[b1][c1];
	ocy1= rts[b1][c2];
	ocx2= rts[b2][c1];
	ocy2= rts[b2][c2];

	if(ocx1==ocx2 && ocy1==ocy2) {
		ocvlak[OCRES*ocx1+ocy1]= 1;
		return;
	}

	ox1= rtf[b1][c1];
	oy1= rtf[b1][c2];
	ox2= rtf[b2][c1];
	oy2= rtf[b2][c2];

	if(ox1!=ox2) {
		if(ox2-ox1>0.0) {
			labdax= (ox1-ocx1-1.0)/(ox1-ox2);
			ldx= -1.0/(ox1-ox2);
			dx= 1;
		} else {
			labdax= (ox1-ocx1)/(ox1-ox2);
			ldx= 1.0/(ox1-ox2);
			dx= -1;
		}
	} else {
		labdax=1.0;
		ldx=0;
	}

	if(oy1!=oy2) {
		if(oy2-oy1>0.0) {
			labday= (oy1-ocy1-1.0)/(oy1-oy2);
			ldy= -1.0/(oy1-oy2);
			dy= 1;
		} else {
			labday= (oy1-ocy1)/(oy1-oy2);
			ldy= 1.0/(oy1-oy2);
			dy= -1;
		}
	} else {
		labday=1.0;
		ldy=0;
	}
	
	x=ocx1; y=ocy1;
	labda= MIN2(labdax, labday);
	
	while(TRUE) {
		
		if(x<0 || y<0 || x>=OCRES || y>=OCRES);
		else ocvlak[OCRES*x+y]= 1;
		
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
		if(labda>=1.0) break;
	}
	ocvlak[OCRES*ocx2+ocy2]=1;
}

static void filltriangle(short c1, short c2, char *ocvlak, short *ocmin)
{
	short a,x,y,y1,y2,*ocmax;

	ocmax=ocmin+3;

	for(x=ocmin[c1];x<=ocmax[c1];x++) {
		a= OCRES*x;
		for(y=ocmin[c2];y<=ocmax[c2];y++) {
			if(ocvlak[a+y]) {
				y++;
				while(ocvlak[a+y] && y!=ocmax[c2]) y++;
				for(y1=ocmax[c2];y1>y;y1--) {
					if(ocvlak[a+y1]) {
						for(y2=y;y2<=y1;y2++) ocvlak[a+y2]=1;
						y1=0;
					}
				}
				y=ocmax[c2];
			}
		}
	}
}

void freeoctree(void)
{
	int a= 0;
	
 	while(g_oc.adrbranch[a]) {
		MEM_freeN(g_oc.adrbranch[a]);
		g_oc.adrbranch[a]= NULL;
		a++;
	}
	
	a= 0;
	while(g_oc.adrnode[a]) {
		MEM_freeN(g_oc.adrnode[a]);
		g_oc.adrnode[a]= NULL;
		a++;
	}
	
	printf("branches %d nodes %d\n", branchcount, nodecount);
	printf("raycount %d \n", raycount);	
//	printf("ray coherent %d \n", coherent_ray);
//	printf("accepted %d rejected %d\n", accepted, rejected);

	branchcount= 0;
	nodecount= 0;
}

void makeoctree()
{
	VlakRen *vlr=NULL;
	VertRen *v1, *v2, *v3, *v4;
	float ocfac[3], t00, t01, t02;
	float rtf[4][3];
	int v;
	short a,b,c, rts[4][3], oc1, oc2, oc3, oc4, ocmin[6], *ocmax, x, y, z;
	char ocvlak[3*OCRES*OCRES + 8];	// front, top, size view of face, to fill in

	ocmax= ocmin+3;

	memset(g_oc.adrnode, 0, sizeof(g_oc.adrnode));
	memset(g_oc.adrbranch, 0, sizeof(g_oc.adrbranch));

	branchcount=0;
	nodecount=0;
	raycount=0;
	accepted= 0;
	rejected= 0;
	coherent_ray= 0;
	
	g_oc.vlr_last= NULL;
	INIT_MINMAX(g_oc.min, g_oc.max);
	
	/* first min max octree space */
	for(v=0;v<R.totvlak;v++) {
		if((v & 255)==0) vlr= R.blovl[v>>8];	
		else vlr++;
		if(vlr->mat->mode & MA_TRACEBLE) {	
			
			DO_MINMAX(vlr->v1->co, g_oc.min, g_oc.max);
			DO_MINMAX(vlr->v2->co, g_oc.min, g_oc.max);
			DO_MINMAX(vlr->v3->co, g_oc.min, g_oc.max);
			if(vlr->v4) {
				DO_MINMAX(vlr->v4->co, g_oc.min, g_oc.max);
			}
		}
	}

	if(g_oc.min[0] > g_oc.max[0]) return;	/* empty octree */

	g_oc.adrbranch[0]=(Branch *)MEM_callocN(256*sizeof(Branch),"makeoctree");

	for(c=0;c<3;c++) {	/* octree enlarge, still needed? */
		g_oc.min[c]-= 0.01;
		g_oc.max[c]+= 0.01;
	}
	
	t00= g_oc.max[0]-g_oc.min[0];
	t01= g_oc.max[1]-g_oc.min[1];
	t02= g_oc.max[2]-g_oc.min[2];
	
	/* this minus 0.1 is old safety... seems to be needed? */
	g_oc.ocfacx=ocfac[0]= (OCRES-0.1)/t00;
	g_oc.ocfacy=ocfac[1]= (OCRES-0.1)/t01;
	g_oc.ocfacz=ocfac[2]= (OCRES-0.1)/t02;
	
	g_oc.ocsize= sqrt(t00*t00+t01*t01+t02*t02);	/* global, max size octree */

	for(v=0; v<R.totvlak; v++) {
		if((v & 255)==0) vlr= R.blovl[v>>8];	
		else vlr++;
		
		if(vlr->mat->mode & MA_TRACEBLE) {
			
			v1= vlr->v1;
			v2= vlr->v2;
			v3= vlr->v3;
			v4= vlr->v4;
			
			for(c=0;c<3;c++) {
				rtf[0][c]= (v1->co[c]-g_oc.min[c])*ocfac[c] ;
				rts[0][c]= (short)rtf[0][c];
				rtf[1][c]= (v2->co[c]-g_oc.min[c])*ocfac[c] ;
				rts[1][c]= (short)rtf[1][c];
				rtf[2][c]= (v3->co[c]-g_oc.min[c])*ocfac[c] ;
				rts[2][c]= (short)rtf[2][c];
				if(v4) {
					rtf[3][c]= (v4->co[c]-g_oc.min[c])*ocfac[c] ;
					rts[3][c]= (short)rtf[3][c];
				}
			}
			
			memset(ocvlak, 0, sizeof(ocvlak));
			
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
				if(ocmax[c]>OCRES-1) ocmax[c]=OCRES-1;
				if(ocmin[c]<0) ocmin[c]=0;
			}

			d2dda(0,1,0,1,ocvlak+OCRES*OCRES,rts,rtf);
			d2dda(0,1,0,2,ocvlak,rts,rtf);
			d2dda(0,1,1,2,ocvlak+2*OCRES*OCRES,rts,rtf);
			d2dda(1,2,0,1,ocvlak+OCRES*OCRES,rts,rtf);
			d2dda(1,2,0,2,ocvlak,rts,rtf);
			d2dda(1,2,1,2,ocvlak+2*OCRES*OCRES,rts,rtf);
			if(v4==NULL) {
				d2dda(2,0,0,1,ocvlak+OCRES*OCRES,rts,rtf);
				d2dda(2,0,0,2,ocvlak,rts,rtf);
				d2dda(2,0,1,2,ocvlak+2*OCRES*OCRES,rts,rtf);
			}
			else {
				d2dda(2,3,0,1,ocvlak+OCRES*OCRES,rts,rtf);
				d2dda(2,3,0,2,ocvlak,rts,rtf);
				d2dda(2,3,1,2,ocvlak+2*OCRES*OCRES,rts,rtf);
				d2dda(3,0,0,1,ocvlak+OCRES*OCRES,rts,rtf);
				d2dda(3,0,0,2,ocvlak,rts,rtf);
				d2dda(3,0,1,2,ocvlak+2*OCRES*OCRES,rts,rtf);
			}
			/* nothing todo with triangle..., just fills :) */
			filltriangle(0,1,ocvlak+OCRES*OCRES,ocmin);
			filltriangle(0,2,ocvlak,ocmin);
			filltriangle(1,2,ocvlak+2*OCRES*OCRES,ocmin);
			
			/* init static vars here */
			face_in_node(vlr, 0,0,0, rtf);
			
			for(x=ocmin[0];x<=ocmax[0];x++) {
				a= OCRES*x;
				for(y=ocmin[1];y<=ocmax[1];y++) {
					b= OCRES*y;
					if(ocvlak[a+y+OCRES*OCRES]) {
						for(z=ocmin[2];z<=ocmax[2];z++) {
							if(ocvlak[b+z+2*OCRES*OCRES] && ocvlak[a+z]) ocwrite(vlr, x,y,z, rtf);
						}
					}
				}
			}
		}
	}
}

/* ************ raytracer **************** */

/* only for self-intersecting test with current render face (where ray left) */
static short intersection2(VlakRen *vlr, float r0, float r1, float r2, float rx1, float ry1, float rz1)
{
	VertRen *v1,*v2,*v3,*v4=NULL;
	float x0,x1,x2,t00,t01,t02,t10,t11,t12,t20,t21,t22;
	float m0, m1, m2, divdet, det, det1;
	float u1, v, u2;

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
	
	if(divdet!=0.0) {
		u1= det1/divdet;

		if(u1<=0.0) {
			det= t00*(m1*r2-m2*r1);
			det+= t01*(m2*r0-m0*r2);
			det+= t02*(m0*r1-m1*r0);
			v= det/divdet;

			if(v<=0.0 && (u1 + v) >= -1.0) {
				return 1;
			}
		}
	}

	if(v4) {

		t20= v3->co[0]-v4->co[0];
		t21= v3->co[1]-v4->co[1];
		t22= v3->co[2]-v4->co[2];

		divdet= t20*x0+t21*x1+t22*x2;
		if(divdet!=0.0) {
			u2= det1/divdet;
		
			if(u2<=0.0) {
				det= t20*(m1*r2-m2*r1);
				det+= t21*(m2*r0-m0*r2);
				det+= t22*(m0*r1-m1*r0);
				v= det/divdet;
	
				if(v<=0.0 && (u2 + v) >= -1.0) {
					return 2;
				}
			}
		}
	}
	return 0;
}

static short intersection(Isect *is)
{
	VertRen *v1,*v2,*v3,*v4=NULL;
	float x0,x1,x2,t00,t01,t02,t10,t11,t12,t20,t21,t22,r0,r1,r2;
	float m0, m1, m2, divdet, det, det1;
	static short vlrisect=0;
	short ok=0;

	is->vlr->raycount= raycount;

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
	
	r0= is->start[0]-is->end[0];
	r1= is->start[1]-is->end[1];
	r2= is->start[2]-is->end[2];
	
	x0= t11*r2-t12*r1;
	x1= t12*r0-t10*r2;
	x2= t10*r1-t11*r0;

	divdet= t00*x0+t01*x1+t02*x2;

	m0= is->start[0]-v3->co[0];
	m1= is->start[1]-v3->co[1];
	m2= is->start[2]-v3->co[2];
	det1= m0*x0+m1*x1+m2*x2;
	
	if(divdet!=0.0) {
		float u= det1/divdet;

		if(u<0.0) {
			float v;
			det= t00*(m1*r2-m2*r1);
			det+= t01*(m2*r0-m0*r2);
			det+= t02*(m0*r1-m1*r0);
			v= det/divdet;

			if(v<0.0 && (u + v) > -1.0) {
				float labda;
				det=  m0*(t12*t01-t11*t02);
				det+= m1*(t10*t02-t12*t00);
				det+= m2*(t11*t00-t10*t01);
				labda= det/divdet;
					
				if(labda>0.0 && labda<1.0) {
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
		if(divdet!=0.0) {
			float u= det1/divdet;
		
			if(u<0.0) {
				float v;
				det= t20*(m1*r2-m2*r1);
				det+= t21*(m2*r0-m0*r2);
				det+= t22*(m0*r1-m1*r0);
				v= det/divdet;
	
				if(v<0.0 && (u + v) > -1.0) {
					float labda;
					det=  m0*(t12*t21-t11*t22);
					det+= m1*(t10*t22-t12*t20);
					det+= m2*(t11*t20-t10*t21);
					labda= det/divdet;
						
					if(labda>0.0 && labda<1.0) {
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
		
		if(is->mode==DDA_MIRROR) {
			/* for mirror: large faces can be filled in too often, this prevents
			   a face being detected too soon... */
			if(is->labda > is->ddalabda) {
				is->vlr->raycount= 0;
				return 0;
			}
		}
		
		/* when a shadow ray leaves a face, it can be little outside the edges of it, causing
		intersection to be detected in its neighbour face */
		
		if(is->vlrcontr && vlrisect);	// optimizing, the tests below are not needed
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
					vlrisect= intersection2(vlr, r0, r1, r2, is->start[0], is->start[1], is->start[2]);
				}

				if(vlrisect) return 1;
				return 0;
			}
		}
		
		return 1;
	}

	return 0;
}

/* check all faces in this node */
static int testnode(Isect *is, Node *no, int x, int y, int z)
{
	VlakRen *vlr;
	short nr=0, ocvaldone=0;
	OcVal ocval, *ov;
	
	if(is->mode==DDA_SHADOW) {
		
		vlr= no->v[0];
		while(vlr) {
		
			if(raycount != vlr->raycount) {
				
				if(ocvaldone==0) {
					calc_ocval_ray(&ocval, (float)x, (float)y, (float)z, 0.0, 0.0, 0.0);
					ocvaldone= 1;
				}
				
				ov= no->ov+nr;
				if( (ov->ocx & ocval.ocx) && (ov->ocy & ocval.ocy) && (ov->ocz & ocval.ocz) ) { 
					//accepted++;
					is->vlr= vlr;

					if(intersection(is)) {
						g_oc.vlr_last= vlr;
						return 1;
					}
				}
				//else rejected++;
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
	else {			/* else mirror and glass  */
		Isect isect;
		int found= 0;
		
		is->labda= 1.0;	/* needed? */
		isect= *is;		/* copy for sorting */
		
		vlr= no->v[0];
		while(vlr) {
			
			if(raycount != vlr->raycount) {
				
				if(ocvaldone==0) {
					calc_ocval_ray(&ocval, (float)x, (float)y, (float)z, 0.0, 0.0, 0.0);
					ocvaldone= 1;
				}
				
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
	static int mdiff=0, xo=OCRES, yo=OCRES, zo=OCRES;
	Branch *br;
	int oc1, diff;

	/* outside of octree check, reset */
	if( (x & ~(OCRES-1)) ||  (y & ~(OCRES-1)) ||  (z & ~(OCRES-1)) ) {
		xo=OCRES; yo=OCRES; zo=OCRES;
		return NULL;
	}
	
	diff= (xo ^ x) | (yo ^ y) | (zo ^ z);

	if(diff>mdiff) {
		
		xo=x; yo=y; zo=z;
		x<<=2;
		y<<=1;
		
		oc1= ((x & 128)+(y & 64)+(z & 32))>>5;
		br= g_oc.adrbranch[0]->b[oc1];
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
							mdiff=0;
							oc1= ((x & 4)+(y & 2)+(z & 1));
							return (Node *)br->b[oc1];
						}
						else mdiff=1;
					}
					else mdiff=3;
				}
				else mdiff=7;
			}
			else mdiff=15;
		}
		else mdiff=31;
	}
	return NULL;
}

static short cliptest(float p, float q, float *u1, float *u2)
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

/* return 1: found valid intersection */
/* starts with is->vlrorig */
static int d3dda(Isect *is)	
{
	Node *no;
	float u1,u2,ox1,ox2,oy1,oy2,oz1,oz2;
	float labdao,labdax,ldx,labday,ldy,labdaz,ldz, ddalabda;
	float vec1[3], vec2[3];
	int dx,dy,dz;	
	int xo,yo,zo,c1=0; //, testcoh=0;
	int ocx1,ocx2,ocy1, ocy2,ocz1,ocz2;
	
	/* clip with octree */
	if(branchcount==0) return NULL;
	
	/* do this before intersect calls */
	raycount++;
	is->vlrorig->raycount= raycount;
	is->vlrcontr= NULL;	/*  to check shared edge */

	/* only for shadow! */
	if(is->mode==DDA_SHADOW && g_oc.vlr_last!=NULL && g_oc.vlr_last!=is->vlrorig) {
		is->vlr= g_oc.vlr_last;
		if(intersection(is)) return 1;
	}
	
	ldx= is->end[0] - is->start[0];
	u1= 0.0;
	u2= 1.0;
	
	/* clip with octree cube */
	if(cliptest(-ldx, is->start[0]-g_oc.min[0], &u1,&u2)) {
		if(cliptest(ldx, g_oc.max[0]-is->start[0], &u1,&u2)) {
			ldy= is->end[1] - is->start[1];
			if(cliptest(-ldy, is->start[1]-g_oc.min[1], &u1,&u2)) {
				if(cliptest(ldy, g_oc.max[1]-is->start[1], &u1,&u2)) {
					ldz= is->end[2] - is->start[2];
					if(cliptest(-ldz, is->start[2]-g_oc.min[2], &u1,&u2)) {
						if(cliptest(ldz, g_oc.max[2]-is->start[2], &u1,&u2)) {
							c1=1;
							if(u2<1.0) {
								is->end[0]= is->start[0]+u2*ldx;
								is->end[1]= is->start[1]+u2*ldy;
								is->end[2]= is->start[2]+u2*ldz;
							}
							if(u1>0.0) {
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
	ocread(OCRES, OCRES, OCRES);

	/* setup 3dda to traverse octree */
	ox1= (is->start[0]-g_oc.min[0])*g_oc.ocfacx;
	oy1= (is->start[1]-g_oc.min[1])*g_oc.ocfacy;
	oz1= (is->start[2]-g_oc.min[2])*g_oc.ocfacz;
	ox2= (is->end[0]-g_oc.min[0])*g_oc.ocfacx;
	oy2= (is->end[1]-g_oc.min[1])*g_oc.ocfacy;
	oz2= (is->end[2]-g_oc.min[2])*g_oc.ocfacz;

	ocx1= (int)ox1;
	ocy1= (int)oy1;
	ocz1= (int)oz1;
	ocx2= (int)ox2;
	ocy2= (int)oy2;
	ocz2= (int)oz2;

	if(ocx1==ocx2 && ocy1==ocy2 && ocz1==ocz2) {
		/* no calc, this is store */
		calc_ocval_ray(NULL, ox1, oy1, oz1, ox2, oy2, oz2);

		no= ocread(ocx1, ocy1, ocz1);
		if(no) {
			is->ddalabda= 1.0;
			if( testnode(is, no, ocx1, ocy1, ocz1) ) return 1;
		}
	}
	else {
		float dox, doy, doz;
		
		dox= ox1-ox2;
		doy= oy1-oy2;
		doz= oz1-oz2;
		
		/* calc labda en ld */
		if(dox!=0.0) {
			if(dox<0.0) {
				labdax= (ox1-ocx1-1.0)/dox;
				ldx= -1.0/dox;
				dx= 1;
			} else {
				labdax= (ox1-ocx1)/dox;
				ldx= 1.0/dox;
				dx= -1;
			}
		} else {
			labdax=1.0;
			ldx=0;
			dx= 0;
		}

		if(doy!=0.0) {
			if(doy<0.0) {
				labday= (oy1-ocy1-1.0)/doy;
				ldy= -1.0/doy;
				dy= 1;
			} else {
				labday= (oy1-ocy1)/doy;
				ldy= 1.0/doy;
				dy= -1;
			}
		} else {
			labday=1.0;
			ldy=0;
			dy= 0;
		}

		if(doz!=0.0) {
			if(doz<0.0) {
				labdaz= (oz1-ocz1-1.0)/doz;
				ldz= -1.0/doz;
				dz= 1;
			} else {
				labdaz= (oz1-ocz1)/doz;
				ldz= 1.0/doz;
				dz= -1;
			}
		} else {
			labdaz=1.0;
			ldz=0;
			dz= 0;
		}
		
		xo=ocx1; yo=ocy1; zo=ocz1;
		ddalabda= MIN3(labdax,labday,labdaz);
		
		// dox,y,z is negative
		vec2[0]= ox1;
		vec2[1]= oy1;
		vec2[2]= oz1;
		
		/* this loop has been constructed to make sure the first and last node of ray
		   are always included, even when ddalabda==1.0 or larger */

		while(TRUE) {

			no= ocread(xo, yo, zo);
			if(no) {
				//if(xo==ocx1 && yo==ocy1 && zo==ocz1);
				//else testcoh= 1;
				
				/* calculate ray intersection with octree node */
				VECCOPY(vec1, vec2);
					// dox,y,z is negative
				vec2[0]= ox1-ddalabda*dox;
				vec2[1]= oy1-ddalabda*doy;
				vec2[2]= oz1-ddalabda*doz;
				/* no calc, this is store */
				calc_ocval_ray(NULL, vec1[0], vec1[1], vec1[2], vec2[0], vec2[1], vec2[2]);
				
				is->ddalabda= ddalabda;
				if( testnode(is, no, xo,yo,zo) ) return 1;
			}

			labdao= ddalabda;

			if(labdax<labday) {
				if(labday<labdaz) {
					xo+=dx;
					labdax+=ldx;
				} else if(labdax<labdaz) {
					xo+=dx;
					labdax+=ldx;
				} else {
					zo+=dz;
					labdaz+=ldz;
					if(labdax==labdaz) {
						xo+=dx;
						labdax+=ldx;
					}
				}
			} else if(labdax<labdaz) {
				yo+=dy;
				labday+=ldy;
				if(labday==labdax) {
					xo+=dx;
					labdax+=ldx;
				}
			} else if(labday<labdaz) {
				yo+=dy;
				labday+=ldy;
			} else if(labday<labdax) {
				zo+=dz;
				labdaz+=ldz;
				if(labdaz==labday) {
					yo+=dy;
					labday+=ldy;
				}
			} else {
				xo+=dx;
				labdax+=ldx;
				yo+=dy;
				labday+=ldy;
				zo+=dz;
				labdaz+=ldz;
			}

			ddalabda=MIN3(labdax,labday,labdaz);
			if(ddalabda==labdao) break;
			/* to make sure the last node is always checked */
			if(labdao>=1.0) break;
		}
		//if(testcoh==0) coherent_ray++;
	}
	
	/* reached end, no intersections found */
	g_oc.vlr_last= NULL;
	return 0;
}		


static void shade_ray(Isect *is, ShadeInput *shi, ShadeResult *shr, int mask)
{
	VlakRen *vlr= is->vlr;
	int flip= 0;
	
	/* set up view vector */
	VecSubf(shi->view, is->end, is->start);
		
	/* render co */
	shi->co[0]= is->start[0]+is->labda*(shi->view[0]);
	shi->co[1]= is->start[1]+is->labda*(shi->view[1]);
	shi->co[2]= is->start[2]+is->labda*(shi->view[2]);
	
	Normalise(shi->view);

	shi->vlr= vlr;
	shi->mat= vlr->mat;
	shi->matren= shi->mat->ren;
	
	/* face normal, check for flip */
	if((shi->matren->mode & MA_RAYTRANSP)==0) {
		float l= vlr->n[0]*shi->view[0]+vlr->n[1]*shi->view[1]+vlr->n[2]*shi->view[2];
		if(l<0.0) {	
			flip= 1;
			vlr->n[0]= -vlr->n[0];
			vlr->n[1]= -vlr->n[1];
			vlr->n[2]= -vlr->n[2];
			vlr->puno= ~(vlr->puno);
		}
	}
	
	// Osa structs we leave unchanged now
	shi->osatex= 0;	

	if(vlr->v4) {
		if(is->isect==2) 
			shade_input_set_coords(shi, is->u, is->v, 2, 1, 3);
		else
			shade_input_set_coords(shi, is->u, is->v, 0, 1, 3);
	}
	else {
		shade_input_set_coords(shi, is->u, is->v, 0, 1, 2);
	}
	
	shi->osatex= (shi->matren->texco & TEXCO_OSA);

	if(is->mode==DDA_SHADOW_TRA) shade_color(shi, shr);
	else {

		shade_lamp_loop(shi, shr, mask);	

		if(shi->matren->translucency!=0.0) {
			ShadeResult shr_t;
			VecMulf(shi->vn, -1.0);
			VecMulf(vlr->n, -1.0);
			shade_lamp_loop(shi, &shr_t, mask);
			shr->diff[0]+= shi->matren->translucency*shr_t.diff[0];
			shr->diff[1]+= shi->matren->translucency*shr_t.diff[1];
			shr->diff[2]+= shi->matren->translucency*shr_t.diff[2];
			VecMulf(shi->vn, -1.0);
			VecMulf(vlr->n, -1.0);
		}
	}
	
	if(flip) {	
		vlr->n[0]= -vlr->n[0];
		vlr->n[1]= -vlr->n[1];
		vlr->n[2]= -vlr->n[2];
		vlr->puno= ~(vlr->puno);
	}
}

static void refraction(float *refract, float *n, float *view, float index)
{
	float dot, fac;

	VECCOPY(refract, view);
	index= 1.0/index;
	
	dot= view[0]*n[0] + view[1]*n[1] + view[2]*n[2];

	if(dot>0.0) {
		fac= 1.0 - (1.0 - dot*dot)*index*index;
		if(fac<= 0.0) return;
		fac= -dot*index + sqrt(fac);
	}
	else {
		index = 1.0/index;
		fac= 1.0 - (1.0 - dot*dot)*index*index;
		if(fac<= 0.0) return;
		fac= -dot*index - sqrt(fac);
	}

	refract[0]= index*view[0] + fac*n[0];
	refract[1]= index*view[1] + fac*n[1];
	refract[2]= index*view[2] + fac*n[2];
}

static void calc_dx_dy_refract(float *ref, float *n, float *view, float index, int smooth)
{
	float dref[3], dview[3], dnor[3];
	
	refraction(ref, n, view, index);
	
	dview[0]= view[0]+ O.dxview;
	dview[1]= view[1];
	dview[2]= view[2];

	if(smooth) {
		VecAddf(dnor, n, O.dxno);
		refraction(dref, dnor, dview, index);
	}
	else {
		refraction(dref, n, dview, index);
	}
	VecSubf(O.dxrefract, ref, dref);
	
	dview[0]= view[0];
	dview[1]= view[1]+ O.dyview;

	if(smooth) {
		VecAddf(dnor, n, O.dyno);
		refraction(dref, dnor, dview, index);
	}
	else {
		refraction(dref, n, dview, index);
	}
	VecSubf(O.dyrefract, ref, dref);
	
}


/* orn = original face normal */
static void reflection(float *ref, float *n, float *view, float *orn)
{
	float f1;
	
	f1= -2.0*(n[0]*view[0]+ n[1]*view[1]+ n[2]*view[2]);
	
	if(orn==NULL) {
		// heuristic, should test this! is to prevent normal going to the back
		if(f1> -0.2) f1= -0.2;
	}
	
	ref[0]= (view[0]+f1*n[0]);
	ref[1]= (view[1]+f1*n[1]);
	ref[2]= (view[2]+f1*n[2]);

	if(orn) {
		/* test phong normals, then we should prevent vector going to the back */
		f1= ref[0]*orn[0]+ ref[1]*orn[1]+ ref[2]*orn[2];
		if(f1>0.0) {
			f1+= .01;
			ref[0]-= f1*orn[0];
			ref[1]-= f1*orn[1];
			ref[2]-= f1*orn[2];
		}
	}
}

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

/* the main recursive tracer itself */
static void traceray(short depth, float *start, float *vec, float *col, VlakRen *vlr, int mask)
{
	ShadeInput shi;
	ShadeResult shr;
	Isect isec;
	float f, f1, fr, fg, fb;
	float ref[3];
	
	VECCOPY(isec.start, start);
	isec.end[0]= start[0]+g_oc.ocsize*vec[0];
	isec.end[1]= start[1]+g_oc.ocsize*vec[1];
	isec.end[2]= start[2]+g_oc.ocsize*vec[2];
	isec.mode= DDA_MIRROR;
	isec.vlrorig= vlr;

	if( d3dda(&isec) ) {
	
		shade_ray(&isec, &shi, &shr, mask);
		
		if(depth>0) {

			if(shi.matren->mode & MA_RAYTRANSP && shr.alpha!=1.0) {
				float f, f1, refract[3], tracol[3];
				
				refraction(refract, shi.vn, shi.view, shi.matren->ang);
				traceray(depth-1, shi.co, refract, tracol, shi.vlr, mask);
				
				f= shr.alpha; f1= 1.0-f;
				shr.diff[0]= f*shr.diff[0] + f1*tracol[0];
				shr.diff[1]= f*shr.diff[1] + f1*tracol[1];
				shr.diff[2]= f*shr.diff[2] + f1*tracol[2];
				shr.alpha= 1.0;
			}

			if(shi.matren->mode & MA_RAYMIRROR) {
				f= shi.matren->ray_mirror;
				if(f!=0.0) f*= fresnel_fac(shi.view, shi.vn, shi.matren->fresnel_mir_i, shi.matren->fresnel_mir);
			}
			else f= 0.0;
			
			if(f!=0.0) {
			
				reflection(ref, shi.vn, shi.view, NULL);			
				traceray(depth-1, shi.co, ref, col, shi.vlr, mask);
			
				f1= 1.0-f;

				/* combine */
				//color_combine(col, f*fr*(1.0-shr.spec[0]), f1, col, shr.diff);
				//col[0]+= shr.spec[0];
				//col[1]+= shr.spec[1];
				//col[2]+= shr.spec[2];
				
				fr= shi.matren->mirr;
				fg= shi.matren->mirg;
				fb= shi.matren->mirb;
		
				col[0]= f*fr*(1.0-shr.spec[0])*col[0] + f1*shr.diff[0] + shr.spec[0];
				col[1]= f*fg*(1.0-shr.spec[1])*col[1] + f1*shr.diff[1] + shr.spec[1];
				col[2]= f*fb*(1.0-shr.spec[2])*col[2] + f1*shr.diff[2] + shr.spec[2];
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
		char skycol[4];
		
		VECCOPY(shi.view, vec);
		Normalise(shi.view);

		RE_sky(shi.view, skycol);	

		col[0]= skycol[0]/255.0;
		col[1]= skycol[1]/255.0;
		col[2]= skycol[2]/255.0;

	}
}

/* **************** jitter blocks ********** */

static float jit_plane2[2*2*3]={0.0};
static float jit_plane3[3*3*3]={0.0};
static float jit_plane4[4*4*3]={0.0};
static float jit_plane5[5*5*3]={0.0};
static float jit_plane6[5*5*3]={0.0};
static float jit_plane7[7*7*3]={0.0};
static float jit_plane8[8*8*3]={0.0};

static float jit_cube2[2*2*2*3]={0.0};
static float jit_cube3[3*3*3*3]={0.0};
static float jit_cube4[4*4*4*3]={0.0};
static float jit_cube5[5*5*5*3]={0.0};

/* table around origin, -.5 to 0.5 */
static float *jitter_plane(int resol)
{
	extern float hashvectf[];
	extern char hash[];
	extern int temp_x, temp_y;
	static int offs=0;
	float dsize, *jit, *fp, *hv;
	int x, y;
	
	if(resol<2) resol= 2;
	if(resol>8) resol= 8;

	switch (resol) {
	case 2: jit= jit_plane2; break;
	case 3: jit= jit_plane3; break;
	case 4: jit= jit_plane4; break;
	case 5: jit= jit_plane5; break;
	case 6: jit= jit_plane6; break;
	case 7: jit= jit_plane7; break;
	default: jit= jit_plane8; break;
	}
	//if(jit[0]!=0.0) return jit;

	offs++;

	dsize= 1.0/(resol-1.0);
	fp= jit;
	hv= hashvectf+3*(hash[ (temp_x&3)+4*(temp_y&3) ]);
	for(x=0; x<resol; x++) {
		for(y=0; y<resol; y++, fp+= 3, hv+=3) {
			fp[0]= -0.5 + (x+0.5*hv[0])*dsize;
			fp[1]= -0.5 + (y+0.5*hv[1])*dsize;
			fp[2]= fp[0]*fp[0] + fp[1]*fp[1];
			if(resol>2)
				if(fp[2]>0.3) fp[2]= 0.0;
		}
	}
	
	return jit;
}

static void *jitter_cube(int resol)
{
	float dsize, *jit, *fp;
	int x, y, z;
	
	if(resol<2) resol= 2;
	if(resol>5) resol= 5;

	switch (resol) {
	case 2: jit= jit_cube2; break;
	case 3: jit= jit_cube3; break;
	case 4: jit= jit_cube4; break;
	default: jit= jit_cube5; break;
	}
	if(jit[0]!=0.0) return jit;

	dsize= 1.0/(resol-1.0);
	fp= jit;
	for(x=0; x<resol; x++) {
		for(y=0; y<resol; y++) {
			for(z=0; z<resol; z++, fp+= 3) {
				fp[0]= -0.5 + x*dsize;
				fp[1]= -0.5 + y*dsize;
				fp[2]= -0.5 + z*dsize;
			}
		}
	}
	
	return jit;

}

/* ***************** main calls ************** */


/* extern call from render loop */
void ray_trace(ShadeInput *shi, ShadeResult *shr, int mask)
{
	VlakRen *vlr;
	float i, f, f1, fr, fg, fb, vec[3], mircol[3], tracol[3];
	int do_tra, do_mir;
	
	do_tra= ((shi->matren->mode & MA_RAYTRANSP) && shr->alpha!=1.0);
	do_mir= ((shi->matren->mode & MA_RAYMIRROR) && shi->matren->ray_mirror!=0.0);
	vlr= shi->vlr;
	
	if(R.r.mode & R_OSA) {
		float accum[3], rco[3], ref[3];
		float accur[3], refract[3], divr=0.0, div= 0.0;
		int j;
		
		if(do_tra) calc_dx_dy_refract(refract, shi->vn, shi->view, shi->matren->ang, vlr->flag & R_SMOOTH);
		if(do_mir) {
			if(vlr->flag & R_SMOOTH) 
				reflection(ref, shi->vn, shi->view, vlr->n);
			else
				reflection(ref, shi->vn, shi->view, NULL);
		}

		accum[0]= accum[1]= accum[2]= 0.0;
		accur[0]= accur[1]= accur[2]= 0.0;
		
		for(j=0; j<R.osa; j++) {
			if(mask & 1<<j) {
				
				if(do_tra || do_mir) {
					rco[0]= shi->co[0] + (jit[j][0]-0.5)*O.dxco[0] + (jit[j][1]-0.5)*O.dyco[0];
					rco[1]= shi->co[1] + (jit[j][0]-0.5)*O.dxco[1] + (jit[j][1]-0.5)*O.dyco[1];
					rco[2]= shi->co[2] + (jit[j][0]-0.5)*O.dxco[2] + (jit[j][1]-0.5)*O.dyco[2];
				}
				
				if(do_tra) {
					vec[0]= refract[0] + (jit[j][0]-0.5)*O.dxrefract[0] + (jit[j][1]-0.5)*O.dyrefract[0] ;
					vec[1]= refract[1] + (jit[j][0]-0.5)*O.dxrefract[1] + (jit[j][1]-0.5)*O.dyrefract[1] ;
					vec[2]= refract[2] + (jit[j][0]-0.5)*O.dxrefract[2] + (jit[j][1]-0.5)*O.dyrefract[2] ;

					traceray(shi->matren->ray_depth_tra, rco, vec, tracol, shi->vlr, mask);
					
					VecAddf(accur, accur, tracol);
					divr+= 1.0;
				}

				if(do_mir) {
					vec[0]= ref[0] + 2.0*(jit[j][0]-0.5)*O.dxref[0] + 2.0*(jit[j][1]-0.5)*O.dyref[0] ;
					vec[1]= ref[1] + 2.0*(jit[j][0]-0.5)*O.dxref[1] + 2.0*(jit[j][1]-0.5)*O.dyref[1] ;
					vec[2]= ref[2] + 2.0*(jit[j][0]-0.5)*O.dxref[2] + 2.0*(jit[j][1]-0.5)*O.dyref[2] ;
					
					/* prevent normal go to backside */
					i= vec[0]*vlr->n[0]+ vec[1]*vlr->n[1]+ vec[2]*vlr->n[2];
					if(i>0.0) {
						i+= .01;
						vec[0]-= i*vlr->n[0];
						vec[1]-= i*vlr->n[1];
						vec[2]-= i*vlr->n[2];
					}
					
					/* we use a new mask here, only shadow uses it */
					/* result in accum, this is copied to shade_lamp_loop */
					traceray(shi->matren->ray_depth, rco, vec, mircol, shi->vlr, 1<<j);
					
					VecAddf(accum, accum, mircol);
					div+= 1.0;
				}
			}
		}
		
		if(divr!=0.0) {
			f= shr->alpha; f1= 1.0-f; f1/= divr;
			shr->diff[0]= f*shr->diff[0] + f1*accur[0];
			shr->diff[1]= f*shr->diff[1] + f1*accur[1];
			shr->diff[2]= f*shr->diff[2] + f1*accur[2];
			shr->alpha= 1.0;
		}
		
		if(div!=0.0) {
			i= shi->matren->ray_mirror*fresnel_fac(shi->view, shi->vn, shi->matren->fresnel_mir_i, shi->matren->fresnel_mir);
			fr= shi->matren->mirr;
			fg= shi->matren->mirg;
			fb= shi->matren->mirb;
	
			/* result */
			f= i*fr*(1.0-shr->spec[0]);	f1= 1.0-i; f/= div;
			shr->diff[0]= f*accum[0] + f1*shr->diff[0];
			
			f= i*fg*(1.0-shr->spec[1]);	f1= 1.0-i; f/= div;
			shr->diff[1]= f*accum[1] + f1*shr->diff[1];
			
			f= i*fb*(1.0-shr->spec[2]);	f1= 1.0-i; f/= div;
			shr->diff[2]= f*accum[2] + f1*shr->diff[2];
		}
	}
	else {
		
		if(do_tra) {
			float refract[3];
			
			refraction(refract, shi->vn, shi->view, shi->matren->ang);
			traceray(shi->matren->ray_depth_tra, shi->co, refract, tracol, shi->vlr, mask);
			
			f= shr->alpha; f1= 1.0-f;
			shr->diff[0]= f*shr->diff[0] + f1*tracol[0];
			shr->diff[1]= f*shr->diff[1] + f1*tracol[1];
			shr->diff[2]= f*shr->diff[2] + f1*tracol[2];
			shr->alpha= 1.0;
		}
		
		if(do_mir) {
		
			i= shi->matren->ray_mirror*fresnel_fac(shi->view, shi->vn, shi->matren->fresnel_mir_i, shi->matren->fresnel_mir);
			if(i!=0.0) {
				fr= shi->matren->mirr;
				fg= shi->matren->mirg;
				fb= shi->matren->mirb;
	
				if(vlr->flag & R_SMOOTH) 
					reflection(vec, shi->vn, shi->view, vlr->n);
				else
					reflection(vec, shi->vn, shi->view, NULL);
		
				traceray(shi->matren->ray_depth, shi->co, vec, mircol, shi->vlr, mask);
				
				f= i*fr*(1.0-shr->spec[0]);	f1= 1.0-i;
				shr->diff[0]= f*mircol[0] + f1*shr->diff[0];
				
				f= i*fg*(1.0-shr->spec[1]);	f1= 1.0-i;
				shr->diff[1]= f*mircol[1] + f1*shr->diff[1];
				
				f= i*fb*(1.0-shr->spec[2]);	f1= 1.0-i;
				shr->diff[2]= f*mircol[2] + f1*shr->diff[2];
			}
		}
	}
}

/* no premul here! */
static void addAlphaLight(float *old, float *over)
{
	float div= old[3]+over[3];

	if(div > 0.0001) {
		old[0]= (over[3]*over[0] + old[3]*old[0])/div;
		old[1]= (over[3]*over[1] + old[3]*old[1])/div;
		old[2]= (over[3]*over[2] + old[3]*old[2])/div;
	}
	old[3]= over[3] + (1-over[3])*old[3];

}

static void ray_trace_shadow_tra(Isect *is, int depth)
{
	/* ray to lamp, find first face that intersects, check alpha properties,
	   if it has alpha<1  continue. exit when alpha is full */
	ShadeInput shi;
	ShadeResult shr;

	if( d3dda(is)) {
		float col[4];
		/* we got a face */
		
		shade_ray(is, &shi, &shr, 0);	// mask not needed
		
		/* add color */
		VECCOPY(col, shr.diff);
		col[3]= shr.alpha;
		addAlphaLight(is->col, col);

		if(depth>0 && is->col[3]<1.0) {
		
			/* adapt isect struct */
			VECCOPY(is->start, shi.co);
			is->vlrorig= shi.vlr;
			
			ray_trace_shadow_tra(is, depth-1);
		}
		else if(is->col[3]>1.0) is->col[3]= 1.0;

	}
}

int ray_trace_shadow_rad(ShadeInput *ship, ShadeResult *shr)
{
	static int counter=0, only_one= 0;
	extern float hashvectf[];
	Isect isec;
	ShadeInput shi;
	ShadeResult shr_t;
	float vec[3], accum[3], div= 0.0;
	int a;
	
	if(only_one) {
		return 0;
	}
	only_one= 1;
	
	accum[0]= accum[1]= accum[2]= 0.0;
	isec.mode= DDA_MIRROR;
	isec.vlrorig= ship->vlr;
	
	for(a=0; a<8*8; a++) {
		
		counter+=3;
		counter %= 768;
		VECCOPY(vec, hashvectf+counter);
		if(ship->vn[0]*vec[0]+ship->vn[1]*vec[1]+ship->vn[2]*vec[2]>0.0) {
			vec[0]-= vec[0];
			vec[1]-= vec[1];
			vec[2]-= vec[2];
		}
		VECCOPY(isec.start, ship->co);
		isec.end[0]= isec.start[0] + g_oc.ocsize*vec[0];
		isec.end[1]= isec.start[1] + g_oc.ocsize*vec[1];
		isec.end[2]= isec.start[2] + g_oc.ocsize*vec[2];
		
		if( d3dda(&isec)) {
			float fac;
			shade_ray(&isec, &shi, &shr_t, 0);	// mask not needed
			fac= isec.labda*isec.labda;
			fac= 1.0;
			accum[0]+= fac*(shr_t.diff[0]+shr_t.spec[0]);
			accum[1]+= fac*(shr_t.diff[1]+shr_t.spec[1]);
			accum[2]+= fac*(shr_t.diff[2]+shr_t.spec[2]);
			div+= fac;
		}
		else div+= 1.0;
	}
	
	if(div!=0.0) {
		shr->diff[0]+= accum[0]/div;
		shr->diff[1]+= accum[1]/div;
		shr->diff[2]+= accum[2]/div;
	}
	shr->alpha= 1.0;
	
	only_one= 0;
	return 1;
}


/* extern call from shade_lamp_loop */
void ray_shadow(ShadeInput *shi, LampRen *lar, float *shadfac, int mask)
{
	Isect isec;
	float fac, div=0.0, lampco[3];

	if(shi->matren->mode & MA_SHADOW_TRA)  isec.mode= DDA_SHADOW_TRA;
	else isec.mode= DDA_SHADOW;
	
	shadfac[3]= 1.0;	// 1=full light
	
	if(lar->type==LA_SUN || lar->type==LA_HEMI) {
		lampco[0]= shi->co[0] - g_oc.ocsize*lar->vec[0];
		lampco[1]= shi->co[1] - g_oc.ocsize*lar->vec[1];
		lampco[2]= shi->co[2] - g_oc.ocsize*lar->vec[2];
	}
	else {
		VECCOPY(lampco, lar->co);
	}
	
	if(lar->ray_samp<2) {
		if(R.r.mode & R_OSA) {
			float accum[4]={0.0, 0.0, 0.0, 0.0};
			int j;
			
			fac= 0.0;
			
			for(j=0; j<R.osa; j++) {
				if(mask & 1<<j) {
					/* set up isec */
					isec.start[0]= shi->co[0] + (jit[j][0]-0.5)*O.dxco[0] + (jit[j][1]-0.5)*O.dyco[0] ;
					isec.start[1]= shi->co[1] + (jit[j][0]-0.5)*O.dxco[1] + (jit[j][1]-0.5)*O.dyco[1] ;
					isec.start[2]= shi->co[2] + (jit[j][0]-0.5)*O.dxco[2] + (jit[j][1]-0.5)*O.dyco[2] ;
					VECCOPY(isec.end, lampco);
					isec.vlrorig= shi->vlr;
					
					if(isec.mode==DDA_SHADOW_TRA) {
						isec.col[0]= isec.col[1]= isec.col[2]=  1.0;
						isec.col[3]= 0.0;	//alpha

						ray_trace_shadow_tra(&isec, DEPTH_SHADOW_TRA);
						
						accum[0]+= isec.col[0]; accum[1]+= isec.col[1];
						accum[2]+= isec.col[2]; accum[3]+= isec.col[3];
					}
					else if( d3dda(&isec) ) fac+= 1.0;
					div+= 1.0;
				}
			}
			if(isec.mode==DDA_SHADOW_TRA) {
					// alpha to 'light'
				accum[3]/= div;
				shadfac[3]= 1.0-accum[3];
				shadfac[0]= shadfac[3]+accum[0]*accum[3]/div;
				shadfac[1]= shadfac[3]+accum[1]*accum[3]/div;
				shadfac[2]= shadfac[3]+accum[2]*accum[3]/div;
			}
			else shadfac[3]= 1.0-fac/div;
		}
		else {
			/* set up isec */
			VECCOPY(isec.start, shi->co);
			VECCOPY(isec.end, lampco);
			isec.vlrorig= shi->vlr;

			if(isec.mode==DDA_SHADOW_TRA) {
				isec.col[0]= isec.col[1]= isec.col[2]=  1.0;
				isec.col[3]= 0.0;	//alpha

				ray_trace_shadow_tra(&isec, DEPTH_SHADOW_TRA);

				VECCOPY(shadfac, isec.col);
					// alpha to 'light'
				shadfac[3]= 1.0-isec.col[3];
				shadfac[0]= shadfac[3]+shadfac[0]*isec.col[3];
				shadfac[1]= shadfac[3]+shadfac[1]*isec.col[3];
				shadfac[2]= shadfac[3]+shadfac[2]*isec.col[3];
			}
			else if( d3dda(&isec)) shadfac[3]= 0.0;
		}
	}
	else {
		float *jitlamp;
		float vec[3];
		int a, j=0;
		
		VECCOPY(isec.start, shi->co);
		isec.vlrorig= shi->vlr;

		fac= 0.0;
		a= lar->ray_samp*lar->ray_samp;
		jitlamp= jitter_plane(lar->ray_samp);
		
		while(a--) {
			if(jitlamp[2]!=0.0) {
				vec[0]= lar->ray_soft*jitlamp[0];
				vec[1]= lar->ray_soft*jitlamp[1];
				vec[2]= 0.0;
				Mat3TransMulVecfl(lar->imat, vec);
				
				isec.end[0]= lampco[0]+vec[0];
				isec.end[1]= lampco[1]+vec[1];
				isec.end[2]= lampco[2]+vec[2];
				
				if(R.r.mode & R_OSA) {
					isec.start[0]= shi->co[0] + (jit[j][0]-0.5)*O.dxco[0] + (jit[j][1]-0.5)*O.dyco[0] ;
					isec.start[1]= shi->co[1] + (jit[j][0]-0.5)*O.dxco[1] + (jit[j][1]-0.5)*O.dyco[1] ;
					isec.start[2]= shi->co[2] + (jit[j][0]-0.5)*O.dxco[2] + (jit[j][1]-0.5)*O.dyco[2] ;
					j++;
					if(j>=R.osa) j= 0;
				}
				
				if( d3dda(&isec) ) fac+= 1.0;
				div+= 1.0;
			}
			jitlamp+= 3;
		}
		shadfac[3]= 1.0-fac/div;
	}
}

