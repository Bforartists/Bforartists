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


/* Global includes */

#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#ifdef WIN32
#include "BLI_winstuff.h"
#endif

#include "MEM_guardedalloc.h"

#include "PIL_time.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_rand.h"

#include "MTC_matrixops.h"

#include "DNA_image_types.h"
#include "DNA_camera_types.h"
#include "DNA_lamp_types.h"
#include "DNA_scene_types.h"
#include "DNA_object_types.h"

#include "BKE_utildefines.h"
#include "BKE_global.h"
#include "BKE_material.h"
#include "BKE_object.h"
#include "BKE_image.h"
#include "BKE_ipo.h"
#include "BKE_key.h"
#include "BKE_ika.h"
#include "BKE_action.h"
#include "BKE_writeavi.h"
#include "BKE_scene.h"

#include "BIF_toolbox.h"
#include "BIF_writeavicodec.h"
#include "BIF_writemovie.h"		/* start_movie(), append_movie(), end_movie() */

#include "BSE_drawview.h"
#include "BSE_sequence.h"

/* this module */
#include "render.h"
#include "render_intern.h"

#include "RE_callbacks.h"
#include "zbuf.h"
#include "rendercore.h" /* part handler for the old renderer, shading functions */
#include "renderPreAndPost.h"
#include "outerRenderLoop.h"
#include "renderHelp.h"
#include "jitter.h"

/* Own includes */
#include "initrender.h"

/* Some crud :/ */
#define ELEM3(a, b, c, d)       ( ELEM(a, b, c) || (a)==(d) ) 


/* uit render.c */
extern float fmask[256], centLut[16];
extern unsigned short *mask1[9], *mask2[9], /*  *igamtab1, */ *igamtab2/*,  *gamtab */;
extern char cmask[256], *centmask;

Material defmaterial;
short pa; /* pa is globaal part ivm print */
short allparts[65][4];
int qscount;

/* ********************* *********************** */


void init_def_material(void)
{
	Material *ma;

	ma= &defmaterial;
	
	init_material(&defmaterial);

	init_render_material(ma);
}

void RE_init_render_data(void)
{
	memset(&R, 0, sizeof(RE_Render));
	memset(&O, 0, sizeof(Osa));
	O.dxwin[0]= 1.0;
	O.dywin[1]= 1.0;
	
	R.blove= (VertRen **)MEM_callocN(sizeof(void *)*(MAXVERT>>8),"Blove");
	R.blovl= (VlakRen **)MEM_callocN(sizeof(void *)*(MAXVLAK>>8),"Blovl");
	R.bloha= (HaloRen **)MEM_callocN(sizeof(void *)*(MAXVERT>>8),"Bloha");
	R.la= (LampRen **)MEM_mallocN(MAXLAMP*sizeof(void *),"renderlamparray");

	init_def_material();
}

void RE_free_render_data()
{
	MEM_freeN(R.blove);
	R.blove= 0;
	MEM_freeN(R.blovl);
	R.blovl= 0;
	MEM_freeN(R.bloha);
	R.bloha= 0;
	MEM_freeN(R.la);
	R.la= 0;
	if(R.rectot) MEM_freeN(R.rectot);
	if(R.rectz) MEM_freeN(R.rectz);
	if(R.rectspare) MEM_freeN(R.rectspare);
	R.rectot= 0;
	R.rectz= 0;
	R.rectspare= 0;

	end_render_material(&defmaterial);
}

/* ****************** GAMMA, MASKERS en LUTS **************** */

float  calc_weight(float *weight, int i, int j)
{
	float x, y, dist, totw= 0.0;
	int a;

	for(a=0; a<R.osa; a++) {
		x= jit[a][0]-0.5+ i;
		y= jit[a][1]-0.5+ j;
		dist= sqrt(x*x+y*y);

		weight[a]= 0.0;

		if(R.r.mode & R_GAUSS) {
			if(dist<1.5) {
				x = dist*1.5;
				weight[a]= (1.0/exp(x*x) - 1.0/exp(1.5*1.5*1.5*1.5));
			}
		}
		else {
			if(i==0 && j==0) weight[a]= 1.0;
		}

		totw+= weight[a];

	}
	return totw;
}

void RE_init_filt_mask(void)
{
	static int firsttime=1;
	static float lastgamma= 0.0;
	float gamma, igamma;
	float weight[32], totw, val, *fpx1, *fpx2, *fpy1, *fpy2;
	int i, j, a;
	unsigned short *m1, *m2, shweight[32];

	if(firsttime) {
		for(a=0; a<9;a++) {
			mask1[a]= MEM_mallocN(256*sizeof(short), "initfilt");
			mask2[a]= MEM_mallocN(256*sizeof(short), "initfilt");
		}
		for(a=0; a<256; a++) {
			cmask[a]= 0;
			if(a &   1) cmask[a]++;
			if(a &   2) cmask[a]++;
			if(a &   4) cmask[a]++;
			if(a &   8) cmask[a]++;
			if(a &  16) cmask[a]++;
			if(a &  32) cmask[a]++;
			if(a &  64) cmask[a]++;
			if(a & 128) cmask[a]++;
		}
		centmask= MEM_mallocN(65536, "Initfilt3");
		for(a=0; a<16; a++) {
			centLut[a]= -0.45+((float)a)/16.0;
		}

		gamtab= MEM_mallocN(65536*sizeof(short), "initGaus2");
		igamtab1= MEM_mallocN(256*sizeof(short), "initGaus2");
		igamtab2= MEM_mallocN(65536*sizeof(short), "initGaus2");

	}

	if(R.r.alphamode==R_ALPHAKEY) gamma= 1.0;	/* ??? */

	if(R.r.mode & R_GAMMA) gamma= 2.0;
	else gamma= 1.0;
	igamma= 1.0/gamma;

	if(gamma!= lastgamma) {
		lastgamma= gamma;

		/* gamtab: in short, uit short */
		for(a=0; a<65536; a++) {
			val= a;
			val/= 65535.0;

			if(gamma==2.0) val= sqrt(val);
			else if(gamma!=1.0) val= pow(val, igamma);

			gamtab[a]= (65535.99*val);
		}
		/* inv gamtab1 : in byte, uit short */
		for(a=1; a<=256; a++) {
			if(gamma==2.0) igamtab1[a-1]= a*a-1;
			else if(gamma==1.0) igamtab1[a-1]= 256*a-1;
			else {
				val= a/256.0;
				igamtab1[a-1]= (65535.0*pow(val, gamma)) -1 ;
			}
		}

		/* inv gamtab2 : in short, uit short */
		for(a=0; a<65536; a++) {
			val= a;
			val/= 65535.0;
			if(gamma==2.0) val= val*val;
			else val= pow(val, gamma);

			igamtab2[a]= 65535.0*val;
		}
	}

	if(firsttime) {
		firsttime= 0;
		return;
	}

	val= 1.0/((float)R.osa);
	for(a=0; a<256; a++) {
		fmask[a]= ((float)cmask[a])*val;
	}

	for(a=0; a<9;a++) {
		memset(mask1[a], 0, 256*2);
		memset(mask2[a], 0, 256*2);
	}

	/* bereken totw */
	totw= 0.0;
	for(j= -1; j<2; j++) {
		for(i= -1; i<2; i++) {
			totw+= calc_weight(weight, i, j);
		}
	}

	for(j= -1; j<2; j++) {
		for(i= -1; i<2; i++) {
			/* bereken ahv jit met ofset de gewichten */

			memset(weight, 0, 32*2);
			calc_weight(weight, i, j);

			for(a=0; a<16; a++) shweight[a]= weight[a]*(65535.0/totw);

			m1= mask1[ 3*(j+1)+i+1 ];
			m2= mask2[ 3*(j+1)+i+1 ];

			for(a=0; a<256; a++) {
				if(a &   1) {
					m1[a]+= shweight[0];
					m2[a]+= shweight[8];
				}
				if(a &   2) {
					m1[a]+= shweight[1];
					m2[a]+= shweight[9];
				}
				if(a &   4) {
					m1[a]+= shweight[2];
					m2[a]+= shweight[10];
				}
				if(a &   8) {
					m1[a]+= shweight[3];
					m2[a]+= shweight[11];
				}
				if(a &  16) {
					m1[a]+= shweight[4];
					m2[a]+= shweight[12];
				}
				if(a &  32) {
					m1[a]+= shweight[5];
					m2[a]+= shweight[13];
				}
				if(a &  64) {
					m1[a]+= shweight[6];
					m2[a]+= shweight[14];
				}
				if(a & 128) {
					m1[a]+= shweight[7];
					m2[a]+= shweight[15];
				}
			}
		}
	}

	/* centmask: de juiste subpixel ofset per masker */

	fpx1= MEM_mallocN(256*sizeof(float), "initgauss4");
	fpx2= MEM_mallocN(256*sizeof(float), "initgauss4");
	fpy1= MEM_mallocN(256*sizeof(float), "initgauss4");
	fpy2= MEM_mallocN(256*sizeof(float), "initgauss4");
	for(a=0; a<256; a++) {
		fpx1[a]= fpx2[a]= 0.0;
		fpy1[a]= fpy2[a]= 0.0;
		if(a & 1) {
			fpx1[a]+= jit[0][0];
			fpy1[a]+= jit[0][1];
			fpx2[a]+= jit[8][0];
			fpy2[a]+= jit[8][1];
		}
		if(a & 2) {
			fpx1[a]+= jit[1][0];
			fpy1[a]+= jit[1][1];
			fpx2[a]+= jit[9][0];
			fpy2[a]+= jit[9][1];
		}
		if(a & 4) {
			fpx1[a]+= jit[2][0];
			fpy1[a]+= jit[2][1];
			fpx2[a]+= jit[10][0];
			fpy2[a]+= jit[10][1];
		}
		if(a & 8) {
			fpx1[a]+= jit[3][0];
			fpy1[a]+= jit[3][1];
			fpx2[a]+= jit[11][0];
			fpy2[a]+= jit[11][1];
		}
		if(a & 16) {
			fpx1[a]+= jit[4][0];
			fpy1[a]+= jit[4][1];
			fpx2[a]+= jit[12][0];
			fpy2[a]+= jit[12][1];
		}
		if(a & 32) {
			fpx1[a]+= jit[5][0];
			fpy1[a]+= jit[5][1];
			fpx2[a]+= jit[13][0];
			fpy2[a]+= jit[13][1];
		}
		if(a & 64) {
			fpx1[a]+= jit[6][0];
			fpy1[a]+= jit[6][1];
			fpx2[a]+= jit[14][0];
			fpy2[a]+= jit[14][1];
		}
		if(a & 128) {
			fpx1[a]+= jit[7][0];
			fpy1[a]+= jit[7][1];
			fpx2[a]+= jit[15][0];
			fpy2[a]+= jit[15][1];
		}
	}

	for(a= (1<<R.osa)-1; a>0; a--) {
		val= count_mask(a);
		i= (15.9*(fpy1[a & 255]+fpy2[a>>8])/val);
		i<<=4;
		i+= (15.9*(fpx1[a & 255]+fpx2[a>>8])/val);
		centmask[a]= i;
	}

	MEM_freeN(fpx1);
	MEM_freeN(fpx2);
	MEM_freeN(fpy1);
	MEM_freeN(fpy2);

}

void RE_free_filt_mask()
{
	int a;

	for(a=0; a<9; a++) {
		MEM_freeN(mask1[a]);
		MEM_freeN(mask2[a]);
	}
	MEM_freeN(gamtab);
	MEM_freeN(igamtab1);
	MEM_freeN(igamtab2);

	MEM_freeN(centmask);
}

/* add stuff */


void defaultlamp()
{
	LampRen *lar;

	lar= (LampRen *)MEM_callocN(sizeof(LampRen),"lampren");
	R.la[R.totlamp++]=lar;

	lar->type= LA_SUN;
	lar->vec[0]= -R.viewmat[2][0];
	lar->vec[1]= -R.viewmat[2][1];
	lar->vec[2]= -R.viewmat[2][2];
	Normalise(lar->vec);
	lar->r= 1.0;
	lar->g= 1.0;
	lar->b= 1.0;
	lar->lay= 65535;
}


/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

void RE_make_existing_file(char *name)
{
	char di[FILE_MAXDIR], fi[FILE_MAXFILE];

	strcpy(di, name);
	BLI_splitdirstring(di, fi);

	/* exist testen */
	if (BLI_exists(di) == 0) {
		BLI_recurdir_fileops(di);
	}
}


/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

extern float holoofs;	/* render.c */
void RE_setwindowclip(int mode, int jmode)
{
	/* jmode>=0: alleen jitter doen, anders berekenen  */
	/* mode==1 zet persmat en grvec */
	Camera *cam=0;
	float lens, fac, minx, miny, maxx, maxy;
	float xd, yd, afmx, afmy;

	if(G.scene->camera==0) return;

	afmx= R.afmx;
	afmy= R.afmy;

	if(mode) {

		if(G.scene->camera->type==OB_LAMP) {
			/* fac= cos( PI*((float)(256- la->spsi))/512.0 ); */

			/* phi= acos(fac); */
			/* lens= 16.0*fac/sin(phi); */
			lens= 35.0;
			R.near= 0.1;
			R.far= 1000.0;
		}
		else if(G.scene->camera->type==OB_CAMERA) {
			cam= G.scene->camera->data;

			lens= cam->lens;
			R.near= cam->clipsta;
			R.far= cam->clipend;
		}
		else {
			lens= 16.0;
		}

		if( (R.r.xasp*afmx) >= (R.r.yasp*afmy) ) {
			R.viewfac= (afmx*lens)/16.0;
		}
		else {
			R.viewfac= R.ycor*(afmy*lens)/16.0;
		}
		if(R.r.mode & R_ORTHO) {
			R.near*= 100.0; /* R.far niet doen */
			R.viewfac*= 100.0;
		}

		R.pixsize= R.near/R.viewfac;

	}

	/* I think these offsets are wrong. They do not coincide with shadow     */
	/* calculations, btw.                                                    */	
  	minx= R.xstart+.5; 
  	miny= R.ycor*(R.ystart+.5); 
  	maxx= R.xend+.4999; 
  	maxy= R.ycor*(R.yend+.4999); 
	/* My guess: (or rather, what should be) */
/*    	minx= R.xstart - 0.5;  */
/*    	miny= R.ycor * (R.ystart - 0.5);  */
	/* Since the SCS-s map directly to the pixel center coordinates, we need */
	/* to stretch the clip area a bit, not just shift it. However, this gives*/
	/* nasty problems for parts...                                           */
	   
	if(R.flag & R_SEC_FIELD) {
		if(R.r.mode & R_ODDFIELD) {
			miny-= .5*R.ycor;
			maxy-= .5*R.ycor;
		}
		else {
			miny+= .5*R.ycor;
			maxy+= .5*R.ycor;
		}
	}

	xd= yd= 0.0;
	if(jmode!= -1) {
		xd= jit[jmode % R.osa][0];
		yd= R.ycor*jit[jmode % R.osa][1];

	}

	if(G.special1 & G_HOLO) {
		if(G.scene->camera->type==OB_CAMERA) {
			cam= G.scene->camera->data;
			if(cam->flag & CAM_HOLO2) {
				
				if(cam->netend==0.0) cam->netend= (G.scene->r.efra);
				
				fac= ((G.scene->r.cfra)-1.0)/(cam->netend)-0.5;
				fac*= (R.rectx);
				fac*= cam->hololen1;

				holoofs= -fac;
				minx-= fac;
				maxx-= fac;
			}
		}
	}

	minx= R.pixsize*(minx+xd);
	maxx= R.pixsize*(maxx+xd);
	miny= R.pixsize*(miny+yd);
	maxy= R.pixsize*(maxy+yd);

	if(R.r.mode & R_ORTHO) {
		/* hier de near & far vermenigvuldigen is voldoende! */

		i_window(minx, maxx, miny, maxy, R.near, 100.0*R.far, R.winmat);
	}
	else i_window(minx, maxx, miny, maxy, R.near, R.far, R.winmat);

}


/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
void initparts()
{
	short nr, xd, yd, xpart, ypart, xparts, yparts;
	short a, xminb, xmaxb, yminb, ymaxb;

	if(R.r.mode & R_BORDER) {
		xminb= R.r.border.xmin*R.rectx;
		xmaxb= R.r.border.xmax*R.rectx;

		yminb= R.r.border.ymin*R.recty;
		ymaxb= R.r.border.ymax*R.recty;

		if(xminb<0) xminb= 0;
		if(xmaxb>R.rectx) xmaxb= R.rectx;
		if(yminb<0) yminb= 0;
		if(ymaxb>R.recty) ymaxb= R.recty;
	}
	else {
		xminb=yminb= 0;
		xmaxb= R.rectx;
		ymaxb= R.recty;
	}

	xparts= R.r.xparts;	/* voor border */
	yparts= R.r.yparts;

	for(nr=0;nr<xparts*yparts;nr++)
		allparts[nr][0]= -1;	/* array leegmaken */

	xpart= R.rectx/xparts;
	ypart= R.recty/yparts;

	/* als border: testen of aantal parts minder kan */
	if(R.r.mode & R_BORDER) {
		a= (xmaxb-xminb-1)/xpart+1; /* zoveel parts in border */
		if(a<xparts) xparts= a;
		a= (ymaxb-yminb-1)/ypart+1; /* zoveel parts in border */
		if(a<yparts) yparts= a;

		xpart= (xmaxb-xminb)/xparts;
		ypart= (ymaxb-yminb)/yparts;
	}

	for(nr=0; nr<xparts*yparts; nr++) {

		if(R.r.mode & R_PANORAMA) {
			allparts[nr][0]= 0;
			allparts[nr][1]= 0;
			allparts[nr][2]= R.rectx;
			allparts[nr][3]= R.recty;
		}
		else {
			xd= (nr % xparts);
			yd= (nr-xd)/xparts;

			allparts[nr][0]= xminb+ xd*xpart;
			allparts[nr][1]= yminb+ yd*ypart;
			if(xd<R.r.xparts-1) allparts[nr][2]= allparts[nr][0]+xpart;
			else allparts[nr][2]= xmaxb;
			if(yd<R.r.yparts-1) allparts[nr][3]= allparts[nr][1]+ypart;
			else allparts[nr][3]= ymaxb;

			if(allparts[nr][2]-allparts[nr][0]<=0) allparts[nr][0]= -1;
			if(allparts[nr][3]-allparts[nr][1]<=0) allparts[nr][0]= -1;
		}
	}
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
short setpart(short nr)	/* return 0 als geen goede part */
{

	if(allparts[nr][0]== -1) return 0;

	R.xstart= allparts[nr][0]-R.afmx;
	R.ystart= allparts[nr][1]-R.afmy;
	R.xend= allparts[nr][2]-R.afmx;
	R.yend= allparts[nr][3]-R.afmy;
	R.rectx= R.xend-R.xstart;
	R.recty= R.yend-R.ystart;

	return 1;
}

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
void addparttorect(short nr, Part *part)
{
	unsigned int *rt, *rp;
	short y, heigth, len;

	/* de juiste offset in rectot */

	rt= R.rectot+ (allparts[nr][1]*R.rectx+ allparts[nr][0]);
	rp= part->rect;
	len= (allparts[nr][2]-allparts[nr][0]);
	heigth= (allparts[nr][3]-allparts[nr][1]);

	for(y=0;y<heigth;y++) {
		memcpy(rt, rp, 4*len);
		rt+=R.rectx;
		rp+= len;
	}
}


/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

 
void RE_holoview()
{
	Camera *cam;
	float dist, fac, fy, fz;

	if(G.scene==0 || G.scene->camera==0) return;

	if(G.scene->camera->type==OB_CAMERA) {
		cam= G.scene->camera->data;
		if(cam->flag & (CAM_HOLO1|CAM_HOLO2)) {
			fy= G.scene->camera->loc[1];
			fz= G.scene->camera->loc[2];
			dist= cam->hololen*sqrt( fy*fy+ fz*fz );

			fac= ((G.scene->r.cfra)-(G.scene->r.sfra))/((float)((G.scene->r.efra)-(G.scene->r.sfra)));

			G.scene->camera->loc[0]= -dist+ 2*fac*dist;
		}
	}
}

void add_to_blurbuf(int blur)
{
	static unsigned int *blurrect= 0;
	int tot, gamval;
	short facr, facb;
	char *rtr, *rtb;

	if(blur<0) {
		if(blurrect) {
			if(R.rectot) MEM_freeN(R.rectot);
			R.rectot= blurrect;
			blurrect= 0;
		}
	}
	else if(blur==R.osa-1) {
		/* eerste keer */
		blurrect= MEM_mallocN(R.rectx*R.recty*sizeof(int), "rectblur");
		if(R.rectot) memcpy(blurrect, R.rectot, R.rectx*R.recty*4);
	}
	else if(blurrect) {
		/* accumuleren */

		facr= 256/(R.osa-blur);
		facb= 256-facr;

		if(R.rectot) {
			rtr= (char *)R.rectot;
			rtb= (char *)blurrect;
			tot= R.rectx*R.recty;
			while(tot--) {
				if( *((unsigned int *)rtb) != *((unsigned int *)rtr) ) {

					if(R.r.mode & R_GAMMA) {
						gamval= (facr* igamtab2[ rtr[0]<<8 ] + facb* igamtab2[ rtb[0]<<8 ])>>8;
						rtb[0]= gamtab[ gamval ]>>8;
						gamval= (facr* igamtab2[ rtr[1]<<8 ] + facb* igamtab2[ rtb[1]<<8 ])>>8;
						rtb[1]= gamtab[ gamval ]>>8;
						gamval= (facr* igamtab2[ rtr[2]<<8 ] + facb* igamtab2[ rtb[2]<<8 ])>>8;
						rtb[2]= gamtab[ gamval ]>>8;
						gamval= (facr* igamtab2[ rtr[3]<<8 ] + facb* igamtab2[ rtb[3]<<8 ])>>8;
						rtb[3]= gamtab[ gamval ]>>8;
					}
					else {
						rtb[0]= (facr*rtr[0] + facb*rtb[0])>>8;
						rtb[1]= (facr*rtr[1] + facb*rtb[1])>>8;
						rtb[2]= (facr*rtr[2] + facb*rtb[2])>>8;
						rtb[3]= (facr*rtr[3] + facb*rtb[3])>>8;
					}
				}
				rtr+= 4;
				rtb+= 4;
			}
		}
		if(blur==0) {
			/* laatste keer */
			if(R.rectot) MEM_freeN(R.rectot);
			R.rectot= blurrect;
			blurrect= 0;
		}
	}
}


/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
void render() {
	/* not too neat... should improve... */
	if(R.r.mode & R_UNIFIED) {
		unifiedRenderingLoop();
	} else {
		oldRenderLoop();
	}
}


void oldRenderLoop(void)  /* hierbinnen de PART en FIELD lussen */
{
	Part *part;
	unsigned int *rt, *rt1, *rt2;
	int len, y;
	short blur, a,fields,fi,parts;  /* pa is globaal ivm print */
	unsigned int *border_buf= NULL;
	unsigned int border_x= 0;
	unsigned int border_y= 0;
	
	if((R.r.mode & R_BORDER) && !(R.r.mode & R_MOVIECROP)) {
		border_buf= R.rectot;
		border_x= R.rectx;
		border_y= R.recty;
		R.rectot= 0;
	}


	if (R.rectz) MEM_freeN(R.rectz);
	R.rectz = 0;

	/* FIELDLUS */
	fields= 1;
	parts= R.r.xparts*R.r.yparts;

	if(R.r.mode & R_FIELDS) {
		fields= 2;
		R.rectf1= R.rectf2= 0;	/* fieldrecten */
		R.r.ysch/= 2;
		R.afmy/= 2;
		R.r.yasp*= 2;
		R.ycor= ( (float)R.r.yasp)/( (float)R.r.xasp);

	}

	
	for(fi=0; fi<fields; fi++) {

		/* INIT */
		BLI_srand( 2*(G.scene->r.cfra)+fi);
	

		R.vlaknr= -1;
		R.flag|= R_RENDERING;
		if(fi==1) R.flag |= R_SEC_FIELD;
	

		/* MOTIONBLUR lus */
		if(R.r.mode & R_MBLUR) blur= R.osa;
		else blur= 1;

	
		while(blur--) {

			/* WINDOW */
			R.rectx= R.r.xsch;
			R.recty= R.r.ysch;
			R.xstart= -R.afmx;
			R.ystart= -R.afmy;
			R.xend= R.xstart+R.rectx-1;
			R.yend= R.ystart+R.recty-1;

	
			if(R.r.mode & R_MBLUR) set_mblur_offs(R.osa-blur);

			initparts(); /* altijd doen ivm border */
			setpart(0);
	
			RE_local_init_render_display();
			RE_local_clear_render_display(R.win);
			RE_local_timecursor((G.scene->r.cfra));

			prepareScene();
			
			/* PARTS */
			R.parts.first= R.parts.last= 0;
			for(pa=0; pa<parts; pa++) {
				
				if(RE_local_test_break()) break;
				
				if(pa) {	/* want pa==0 is al gedaan */
					if(setpart(pa)==0) break;
				}

				if(R.r.mode & R_MBLUR) RE_setwindowclip(0, blur);
				else RE_setwindowclip(0,-1);

				if(R.r.mode & R_PANORAMA) setPanoRot(pa);

				/* HOMOGENE COORDINATEN EN ZBUF EN CLIP OPT (per part) */
				/* There may be some interference with z-coordinate    */
				/* calculation here?                                   */

				doClipping(RE_projectverto);
				if(RE_local_test_break()) break;

				
				/* ZBUFFER & SHADE: zbuffer stores int distances, int face indices */
				R.rectot= (unsigned int *)MEM_callocN(sizeof(int)*R.rectx*R.recty, "rectot");
				R.rectz =  (unsigned int *)MEM_mallocN(sizeof(int)*R.rectx*R.recty, "rectz");

				if(R.r.mode & R_MBLUR) RE_local_printrenderinfo(0.0, R.osa - blur);
				else RE_local_printrenderinfo(0.0, -1);
				
				/* choose render pipeline type, and whether or not to use the */
				/* delta accumulation buffer. 3 choices.                      */
				if(R.r.mode & R_OSA) zbufshadeDA();
				else                 zbufshade();
				
				if(RE_local_test_break()) break;
				
				/* uitzondering */
				if( (R.r.mode & R_BORDER) && (R.r.mode & R_MOVIECROP));
				else {
					/* PART OF BORDER AFHANDELEN */
					if(parts>1 || (R.r.mode & R_BORDER)) {
						
						part= MEM_callocN(sizeof(Part), "part");
						BLI_addtail(&R.parts, part);
						part->rect= R.rectot;
						R.rectot= 0;
						
						if (R.rectz) {
							MEM_freeN(R.rectz);
							R.rectz= 0;
						}
					}
				}
			}

			/* PARTS SAMENVOEGEN OF BORDER INVOEGEN */

			/* uitzondering: crop */
			if( (R.r.mode & R_BORDER) && (R.r.mode & R_MOVIECROP)) ;
			else {
				R.rectx= R.r.xsch;
				R.recty= R.r.ysch;

				if(R.r.mode & R_PANORAMA) R.rectx*= R.r.xparts;

				if(parts>1 || (R.r.mode & R_BORDER)) {
					if(R.rectot) MEM_freeN(R.rectot);
					if(R.r.mode & R_BORDER) {
						if(border_x<R.rectx || border_y<R.recty || border_buf==NULL)
							R.rectot= (unsigned int *)MEM_callocN(sizeof(int)*R.rectx*R.recty, "rectot");
						else 
							R.rectot= border_buf;
					}
					else R.rectot=(unsigned int *)MEM_mallocN(sizeof(int)*R.rectx*R.recty, "rectot");
					
					part= R.parts.first;
					for(pa=0; pa<parts; pa++) {
						if(allparts[pa][0]== -1) break;
						if(part==0) break;
						
						if(R.r.mode & R_PANORAMA) {
							if(pa) {
								allparts[pa][0] += pa*R.r.xsch;
								allparts[pa][2] += pa*R.r.xsch;
							}
						}
						addparttorect(pa, part);
						
						part= part->next;
					}
					
					part= R.parts.first;
					while(part) {
						MEM_freeN(part->rect);
						part= part->next;
					}
					BLI_freelistN(&R.parts);
				}
			}

			if( (R.flag & R_HALO)) {
				add_halo_flare();
			}

			if(R.r.mode & R_MBLUR) {
				add_to_blurbuf(blur);
			}

			/* EINDE (blurlus) */
			finalizeScene();

			if(RE_local_test_break()) break;
		}

		/* definitief vrijgeven */
		add_to_blurbuf(-1);

		/* FIELD AFHANDELEN */
		if(R.r.mode & R_FIELDS) {
			if(R.flag & R_SEC_FIELD) R.rectf2= R.rectot;
			else R.rectf1= R.rectot;
			R.rectot= 0;
		}

		if(RE_local_test_break()) break;
	}

	/* FIELDS SAMENVOEGEN */
	if(R.r.mode & R_FIELDS) {
		R.r.ysch*= 2;
		R.afmy*= 2;
		R.recty*= 2;
		R.r.yasp/=2;

		if(R.rectot) MEM_freeN(R.rectot);	/* komt voor bij afbreek */
		R.rectot=(unsigned int *)MEM_mallocN(sizeof(int)*R.rectx*R.recty, "rectot");

		if(RE_local_test_break()==0) {
			rt= R.rectot;

			if(R.r.mode & R_ODDFIELD) {
				rt2= R.rectf1;
				rt1= R.rectf2;
			}
			else {
				rt1= R.rectf1;
				rt2= R.rectf2;
			}

			len= 4*R.rectx;

			for(a=0; a<R.recty; a+=2) {
				memcpy(rt, rt1, len);
				rt+= R.rectx;
				rt1+= R.rectx;
				memcpy(rt, rt2, len);
				rt+= R.rectx;
				rt2+= R.rectx;
			}
		}
	}

	/* R.rectx= R.r.xsch; */
	/* if(R.r.mode & R_PANORAMA) R.rectx*= R.r.xparts; */
	/* R.recty= R.r.ysch; */

	/* als border: wel de skybuf doen */
	if(R.r.mode & R_BORDER) {
		if( (R.r.mode & R_MOVIECROP)==0) {
			if(R.r.bufflag & 1) {
				R.xstart= -R.afmx;
				R.ystart= -R.afmy;
				rt= R.rectot;
				for(y=0; y<R.recty; y++, rt+= R.rectx) scanlinesky((char *)rt, y);
			}
		}
	}

	set_mblur_offs(0);

	/* VRIJGEVEN */

	/* zbuf test */

	/* don't free R.rectz, only when its size is not the same as R.rectot */

	if (R.rectz && parts == 1 && (R.r.mode & R_FIELDS) == 0);
	else {
		if(R.rectz) MEM_freeN(R.rectz);
		R.rectz= 0;
	}

	if(R.rectf1) MEM_freeN(R.rectf1);
	R.rectf1= 0;
	if(R.rectf2) MEM_freeN(R.rectf2);
	R.rectf2= 0;
}



/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
extern unsigned short usegamtab;
void RE_initrender(struct View3D *ogl_render_view3d)
{
	double start_time;
	Image *bima;
	char name[256];
	
	/* scenedata naar R */
	R.r= G.scene->r;
	R.r.postigamma= 1.0/R.r.postgamma;
	
	/* voor zekerheid: bij voortijdige return */
	R.rectx= R.r.xsch;
	R.recty= R.r.ysch;

	/* MAG ER WEL WORDEN GERENDERD */

	/* verboden combinatie */
	if((R.r.mode & R_BORDER) && (R.r.mode & R_PANORAMA)) {
		error("No border allowed for Panorama");
		G.afbreek= 1;
		return;
	}

	
	if(R.r.xparts*R.r.yparts>64) {
		error("No more than 64 parts");
		G.afbreek= 1;
		return;
	}

	if(R.r.yparts>1 && (R.r.mode & R_PANORAMA)) {
		error("No Y-Parts allowed for Panorama");
		G.afbreek= 1;
		return;
	}

	
	/* BACKBUF TESTEN */
	/* If an image is specified for use as backdrop, that image is loaded    */
	/* here.                                                                 */
	if((R.r.bufflag & 1) && (G.scene->r.scemode & R_OGL)==0) {
		if(R.r.alphamode == R_ADDSKY) {
			strcpy(name, R.r.backbuf);
			BLI_convertstringcode(name, G.sce, G.scene->r.cfra);

			if(R.backbuf) {
				R.backbuf->id.us--;
				bima= R.backbuf;
			}
			else bima= 0;

			R.backbuf= add_image(name);

			if(bima && bima->id.us<1) {
				free_image_buffers(bima);
			}
			if(R.backbuf==0) {
				error("No backbuf there!");
				G.afbreek= 1;
				return;
			}
		}
	}

	
	usegamtab= 0; /* zie hieronder */

	if(R.r.mode & (R_OSA|R_MBLUR)) {
		R.osa= R.r.osa;
		if(R.osa>16) R.osa= 16;

		init_render_jit(R.osa);
		RE_init_filt_mask();

		/* wordt af en toe tijdelijk op nul gezet, o.a. in transp zbuf */
		if(R.r.mode & R_GAMMA) {
			if((R.r.mode & R_OSA)) usegamtab= 1;
		}
	}
	else R.osa= 0;

	/* WINDOW */
	R.r.xsch= (R.r.size*R.r.xsch)/100;
	R.r.ysch= (R.r.size*R.r.ysch)/100;

	R.afmx= R.r.xsch/2;
	R.afmy= R.r.ysch/2;

	/* when rendered without camera object */
	/* it has to done here because of envmaps */
	R.near= 0.1;
	R.far= 1000.0;

	
	if(R.afmx<1 || R.afmy<1) {
		error("Image too small");
		return;
	}
	R.ycor= ( (float)R.r.yasp)/( (float)R.r.xasp);

	start_time= PIL_check_seconds_timer();

	if(R.r.scemode & R_DOSEQ) {
		R.rectx= R.r.xsch;
		R.recty= R.r.ysch;

		if(R.rectot) MEM_freeN(R.rectot);
		R.rectot= (unsigned int *)MEM_callocN(sizeof(int)*R.rectx*R.recty, "rectot");

		RE_local_timecursor((G.scene->r.cfra));

		if(RE_local_test_break()==0) do_render_seq();

		/* displayen */
		if(R.rectot) RE_local_render_display(0, R.recty-1,
											 R.rectx, R.recty,
											 R.rectot);
	}
	else if(R.r.scemode & R_OGL) {
		R.rectx= R.r.xsch;
		R.recty= R.r.ysch;

		if(R.rectot) MEM_freeN(R.rectot);
		R.rectot= (unsigned int *)MEM_callocN(sizeof(int)*R.rectx*R.recty, "rectot");

		RE_local_init_render_display();
		drawview3d_render(ogl_render_view3d);
	}
	else {
		if(G.scene->camera==0) {
			G.scene->camera= scene_find_camera(G.scene);
		}

		if(G.scene->camera==0) {
			error("No camera");
			G.afbreek=1;
			return;
		}
		else {

			if(G.scene->camera->type==OB_CAMERA) {
				Camera *cam= G.scene->camera->data;
				if(cam->type==CAM_ORTHO) R.r.mode |= R_ORTHO;
			}

			render(); /* keert terug met complete rect xsch-ysch */
		}
	}
	
	/* nog eens displayen: fields/seq/parts/pano etc */
	if(R.rectot) {	
		RE_local_init_render_display();
		RE_local_render_display(0, R.recty-1,
								R.rectx, R.recty,
								R.rectot); 
	}
	else RE_local_clear_render_display(R.win);

	RE_local_printrenderinfo((PIL_check_seconds_timer() - start_time), -1);
	
	/* variabelen weer goed */
	R.osatex= 0;
	R.vlr= 0;	/* bij cubemap */
	R.flag= 0;
}

void RE_animrender(struct View3D *ogl_render_view3d)
{
	int cfrao;
	char name[256];

	if(G.scene==0) return;

	/* scenedata naar R: (voor backbuf, R.rectx enz) */
	R.r= G.scene->r;

	/* START ANIMLUS overal wordt NIET de cfra uit R.r gebruikt: ivm rest blender */
	cfrao= (G.scene->r.cfra);

	if(G.scene->r.scemode & R_OGL) R.r.mode &= ~R_PANORAMA;
	
	// these calculations apply for
	// all movie formats
	R.rectx= (R.r.size*R.r.xsch)/100;
	R.recty= (R.r.size*R.r.ysch)/100;
	if(R.r.mode & R_PANORAMA) {
		R.rectx*= R.r.xparts;
		R.recty*= R.r.yparts;
	}

	if (0) {
#ifdef __sgi
	} else if (R.r.imtype==R_MOVIE) {
		start_movie();
#endif
#ifdef _WIN32
	} else if (R.r.imtype == R_AVICODEC) {
		start_avi_codec();
#endif
	} else if ELEM4(R.r.imtype, R_AVIRAW, R_AVIJPEG, R_MOVIE, R_AVICODEC) {
		if ELEM(R.r.imtype, R_MOVIE, R_AVICODEC) {
			printf("Selected movie format not supported on this platform,\nusing RAW AVI instead\n");
		}
		start_avi();
	}

	for((G.scene->r.cfra)=(G.scene->r.sfra); (G.scene->r.cfra)<=(G.scene->r.efra); (G.scene->r.cfra)++) {
		double starttime= PIL_check_seconds_timer();

		R.flag= R_ANIMRENDER;

		RE_initrender(ogl_render_view3d);
		
		/* SCHRIJF PLAATJE */
		if(RE_local_test_break()==0) {

			if (0) {
#ifdef __sgi
			} else if (R.r.imtype == R_MOVIE) {
				append_movie((G.scene->r.cfra));
#endif
#ifdef _WIN32
			} else if (R.r.imtype == R_AVICODEC) {
				append_avi_codec((G.scene->r.cfra));
#endif
			} else if ELEM4(R.r.imtype, R_AVIRAW, R_AVIJPEG, R_MOVIE, R_AVICODEC) {
				append_avi((G.scene->r.cfra));
			} else {
				makepicstring(name, (G.scene->r.cfra));
				schrijfplaatje(name);
				if(RE_local_test_break()==0) printf("Saved: %s", name);
			}

			timestr(PIL_check_seconds_timer()-starttime, name);
			printf(" Time: %s\n", name);
			fflush(stdout); /* nodig voor renderd !! */
		}

		if(G.afbreek==1) break;

	}

	(G.scene->r.cfra)= cfrao;

	/* restoren tijd */
	if(R.r.mode & (R_FIELDS|R_MBLUR)) {
		do_all_ipos();
		do_all_keys();
		do_all_actions();
		do_all_ikas();
	}

	if (0) {
#ifdef __sgi	
	} else if (R.r.imtype==R_MOVIE) {
		end_movie();
#endif
#ifdef _WIN32
	} else if (R.r.imtype == R_AVICODEC) {
		end_avi_codec();
#endif
	} else if ELEM4(R.r.imtype, R_AVIRAW, R_AVIJPEG, R_MOVIE, R_AVICODEC) {
		end_avi();
	}
}

/* *************************************************** */
/* ******************* Screendumps ******************** */
/* moved to the windowControl thing */
