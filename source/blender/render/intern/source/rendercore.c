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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Contributors: Hos, Robert Wenzlaff.
 * Contributors: 2004/2005/2006 Blender Foundation, full recode
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/* system includes */
#include <stdio.h>
#include <math.h>
#include <string.h>

/* External modules: */
#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_jitter.h"
#include "BLI_rand.h"
#include "BLI_threads.h"

#include "BKE_utildefines.h"

#include "DNA_image_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"

#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_texture.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

/* local include */
#include "renderpipeline.h"
#include "render_types.h"
#include "renderdatabase.h"
#include "pixelblending.h"
#include "pixelshading.h"
#include "shadbuf.h"
#include "shading.h"
#include "zbuf.h"

#include "PIL_time.h"

/* own include */
#include "rendercore.h"


/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
/* defined in pipeline.c, is hardcopy of active dynamic allocated Render */
/* only to be used here in this file, it's for speed */
extern struct Render R;
/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

/* x and y are current pixels in rect to be rendered */
/* do not normalize! */
void calc_view_vector(float *view, float x, float y)
{

	view[2]= -ABS(R.clipsta);
	
	if(R.r.mode & R_ORTHO) {
		view[0]= view[1]= 0.0f;
	}
	else {
		
		if(R.r.mode & R_PANORAMA)
			x-= R.panodxp;
		
		/* move x and y to real viewplane coords */
		x= (x/(float)R.winx);
		view[0]= R.viewplane.xmin + x*(R.viewplane.xmax - R.viewplane.xmin);
		
		y= (y/(float)R.winy);
		view[1]= R.viewplane.ymin + y*(R.viewplane.ymax - R.viewplane.ymin);
		
//		if(R.flag & R_SEC_FIELD) {
//			if(R.r.mode & R_ODDFIELD) view[1]= (y+R.ystart)*R.ycor;
//			else view[1]= (y+R.ystart+1.0)*R.ycor;
//		}
//		else view[1]= (y+R.ystart+R.bluroffsy+0.5)*R.ycor;
	
		if(R.r.mode & R_PANORAMA) {
			float u= view[0] + R.panodxv; float v= view[2];
			view[0]= R.panoco*u + R.panosi*v;
			view[2]= -R.panosi*u + R.panoco*v;
		}
	}
}

void calc_renderco_ortho(float *co, float x, float y, int z)
{
	/* x and y 3d coordinate can be derived from pixel coord and winmat */
	float fx= 2.0f/(R.winx*R.winmat[0][0]);
	float fy= 2.0f/(R.winy*R.winmat[1][1]);
	float zco;
	
	co[0]= (x - 0.5f*R.winx)*fx - R.winmat[3][0]/R.winmat[0][0];
	co[1]= (y - 0.5f*R.winy)*fy - R.winmat[3][1]/R.winmat[1][1];
	
	zco= ((float)z)/2147483647.0f;
	co[2]= R.winmat[3][2]/( R.winmat[2][3]*zco - R.winmat[2][2] );
}

void calc_renderco_zbuf(float *co, float *view, int z)
{
	float fac, zco;
	
	/* inverse of zbuf calc: zbuf = MAXZ*hoco_z/hoco_w */
	zco= ((float)z)/2147483647.0f;
	co[2]= R.winmat[3][2]/( R.winmat[2][3]*zco - R.winmat[2][2] );

	fac= co[2]/view[2];
	co[0]= fac*view[0];
	co[1]= fac*view[1];
}

/* also used in zbuf.c and shadbuf.c */
int count_mask(unsigned short mask)
{
	if(R.samples)
		return (R.samples->cmask[mask & 255]+R.samples->cmask[mask>>8]);
	return 0;
}

static int calchalo_z(HaloRen *har, int zz)
{
	
	if(har->type & HA_ONLYSKY) {
		if(zz!=0x7FFFFFFF) zz= - 0x7FFFFF;
	}
	else {
		zz= (zz>>8);
	}
	return zz;
}

static void halo_pixelstruct(HaloRen *har, float *rb, float dist, float xn, float yn, PixStr *ps)
{
	float col[4], accol[4];
	int amount, amountm, zz, flarec;
	
	amount= 0;
	accol[0]=accol[1]=accol[2]=accol[3]= 0.0f;
	flarec= har->flarec;
	
	while(ps) {
		amountm= count_mask(ps->mask);
		amount+= amountm;
		
		zz= calchalo_z(har, ps->z);
		if(zz> har->zs) {
			float fac;
			
			shadeHaloFloat(har, col, zz, dist, xn, yn, flarec);
			fac= ((float)amountm)/(float)R.osa;
			accol[0]+= fac*col[0];
			accol[1]+= fac*col[1];
			accol[2]+= fac*col[2];
			accol[3]+= fac*col[3];
			flarec= 0;
		}
		
		ps= ps->next;
	}
	/* now do the sky sub-pixels */
	amount= R.osa-amount;
	if(amount) {
		float fac;

		shadeHaloFloat(har, col, 0x7FFFFF, dist, xn, yn, flarec);
		fac= ((float)amount)/(float)R.osa;
		accol[0]+= fac*col[0];
		accol[1]+= fac*col[1];
		accol[2]+= fac*col[2];
		accol[3]+= fac*col[3];
	}
	col[0]= accol[0];
	col[1]= accol[1];
	col[2]= accol[2];
	col[3]= accol[3];
	
	addalphaAddfacFloat(rb, col, har->add);
	
}

static void halo_tile(RenderPart *pa, float *pass, unsigned int lay)
{
	HaloRen *har = NULL;
	rcti disprect= pa->disprect, testrect= pa->disprect;
	float dist, xsq, ysq, xn, yn, *rb;
	float col[4];
	long *rd= NULL;
	int a, *rz, zz, y;
	short minx, maxx, miny, maxy, x;

	/* we don't render halos in the cropped area, gives errors in flare counter */
	if(pa->crop) {
		testrect.xmin+= pa->crop;
		testrect.xmax-= pa->crop;
		testrect.ymin+= pa->crop;
		testrect.ymax-= pa->crop;
	}
	
	for(a=0; a<R.tothalo; a++) {
		if((a & 255)==0)
			har= R.bloha[a>>8];
		else har++;

		/* layer test, clip halo with y */
		if((har->lay & lay)==0);
		else if(testrect.ymin > har->maxy);
		else if(testrect.ymax < har->miny);
		else {
			
			minx= floor(har->xs-har->rad);
			maxx= ceil(har->xs+har->rad);
			
			if(testrect.xmin > maxx);
			else if(testrect.xmax < minx);
			else {
				
				minx= MAX2(minx, testrect.xmin);
				maxx= MIN2(maxx, testrect.xmax);
			
				miny= MAX2(har->miny, testrect.ymin);
				maxy= MIN2(har->maxy, testrect.ymax);
			
				for(y=miny; y<maxy; y++) {
					int rectofs= (y-disprect.ymin)*pa->rectx + (minx - disprect.xmin);
					rb= pass + 4*rectofs;
					rz= pa->rectz + rectofs;
					
					if(pa->rectdaps)
						rd= pa->rectdaps + rectofs;
					
					yn= (y-har->ys)*R.ycor;
					ysq= yn*yn;
					
					for(x=minx; x<maxx; x++, rb+=4, rz++) {
						xn= x- har->xs;
						xsq= xn*xn;
						dist= xsq+ysq;
						if(dist<har->radsq) {
							if(rd && *rd) {
								halo_pixelstruct(har, rb, dist, xn, yn, (PixStr *)*rd);
							}
							else {
								zz= calchalo_z(har, *rz);
								if(zz> har->zs) {
									shadeHaloFloat(har, col, zz, dist, xn, yn, har->flarec);
									addalphaAddfacFloat(rb, col, har->add);
								}
							}
						}
						if(rd) rd++;
					}
				}
			}
		}
		if(R.test_break() ) break; 
	}
}

static void lamphalo_tile(RenderPart *pa, RenderLayer *rl)
{
	ShadeInput shi;
	float *pass= rl->rectf;
	float fac;
	long *rd= pa->rectdaps;
	int x, y, *rz= pa->rectz;
	
	shade_input_initialize(&shi, pa, rl, 0);
	
	for(y=pa->disprect.ymin; y<pa->disprect.ymax; y++) {
		for(x=pa->disprect.xmin; x<pa->disprect.xmax; x++, rz++, pass+=4) {
			
			calc_view_vector(shi.view, x, y);
			
			if(rd && *rd) {
				PixStr *ps= (PixStr *)*rd;
				int samp, totsamp= 0;
				
				while(ps) {
					if(R.r.mode & R_ORTHO)
						calc_renderco_ortho(shi.co, (float)x, (float)y, ps->z);
					else
						calc_renderco_zbuf(shi.co, shi.view, ps->z);
					
					totsamp+= samp= count_mask(ps->mask);
					fac= ((float)samp)/(float)R.osa;
					renderspothalo(&shi, pass, fac);
					ps= ps->next;
				}
				if(totsamp<R.osa) {
					fac= ((float)R.osa-totsamp)/(float)R.osa;
					shi.co[2]= 0.0f;
					renderspothalo(&shi, pass, fac);
				}
			}
			else {
				if(R.r.mode & R_ORTHO)
					calc_renderco_ortho(shi.co, (float)x, (float)y, *rz);
				else
					calc_renderco_zbuf(shi.co, shi.view, *rz);
				
				renderspothalo(&shi, pass, 1.0f);
			}
			
			if(rd) rd++;
		}
		if(y&1)
			if(R.test_break()) break; 
	}
}				


/* ********************* MAINLOOPS ******************** */

/* osa version */
static void add_filt_passes(RenderLayer *rl, int curmask, int rectx, int offset, ShadeInput *shi, ShadeResult *shr)
{
	RenderPass *rpass;
	
	for(rpass= rl->passes.first; rpass; rpass= rpass->next) {
		float *fp, *col= NULL;
		int pixsize= 3;
		
		switch(rpass->passtype) {
			case SCE_PASS_RGBA:
				col= shr->col;
				pixsize= 4;
				break;
			case SCE_PASS_DIFFUSE:
				col= shr->diff;
				break;
			case SCE_PASS_SPEC:
				col= shr->spec;
				break;
			case SCE_PASS_SHADOW:
				col= shr->shad;
				break;
			case SCE_PASS_AO:
				col= shr->ao;
				break;
			case SCE_PASS_REFLECT:
				col= shr->refl;
				break;
			case SCE_PASS_REFRACT:
				col= shr->refr;
				break;
			case SCE_PASS_RADIO:
				col= shr->rad;
				break;
			case SCE_PASS_NORMAL:
				col= shr->nor;
				break;
			case SCE_PASS_UV:
				/* box filter only, gauss will screwup UV too much */
				if(shi->totuv) {
					float mult= (float)count_mask(curmask)/(float)R.osa;
					fp= rpass->rect + 3*offset;
					fp[0]+= mult*(0.5f + 0.5f*shi->uv[0].uv[0]);
					fp[1]+= mult*(0.5f + 0.5f*shi->uv[0].uv[1]);
					fp[2]+= mult;
				}
				break;
			case SCE_PASS_INDEXOB:
				/* no filter */
				if(shi->vlr) {
					fp= rpass->rect + offset;
					if(*fp==0.0f)
						*fp= (float)shi->vlr->ob->index;
				}
				break;
			case SCE_PASS_VECTOR:
			{
				/* add minimum speed in pixel, no filter */
				fp= rpass->rect + 4*offset;
				if( (ABS(shr->winspeed[0]) + ABS(shr->winspeed[1]))< (ABS(fp[0]) + ABS(fp[1])) ) {
					fp[0]= shr->winspeed[0];
					fp[1]= shr->winspeed[1];
				}
				if( (ABS(shr->winspeed[2]) + ABS(shr->winspeed[3]))< (ABS(fp[2]) + ABS(fp[3])) ) {
					fp[2]= shr->winspeed[2];
					fp[3]= shr->winspeed[3];
				}
			}
				break;
		}
		if(col) {
			fp= rpass->rect + pixsize*offset;
			add_filt_fmask_pixsize(curmask, col, fp, rectx, pixsize);
		}
	}
}

/* non-osa version */
static void add_passes(RenderLayer *rl, int offset, ShadeInput *shi, ShadeResult *shr)
{
	RenderPass *rpass;
	
	for(rpass= rl->passes.first; rpass; rpass= rpass->next) {
		float *fp, *col= NULL, uvcol[3];
		int a, pixsize= 3;
		
		switch(rpass->passtype) {
			case SCE_PASS_RGBA:
				col= shr->col;
				pixsize= 4;
				break;
			case SCE_PASS_DIFFUSE:
				col= shr->diff;
				break;
			case SCE_PASS_SPEC:
				col= shr->spec;
				break;
			case SCE_PASS_SHADOW:
				col= shr->shad;
				break;
			case SCE_PASS_AO:
				col= shr->ao;
				break;
			case SCE_PASS_REFLECT:
				col= shr->refl;
				break;
			case SCE_PASS_REFRACT:
				col= shr->refr;
				break;
			case SCE_PASS_RADIO:
				col= shr->rad;
				break;
			case SCE_PASS_NORMAL:
				col= shr->nor;
				break;
			case SCE_PASS_UV:
				if(shi->totuv) {
					uvcol[0]= 0.5f + 0.5f*shi->uv[0].uv[0];
					uvcol[1]= 0.5f + 0.5f*shi->uv[0].uv[1];
					uvcol[2]= 1.0f;
					col= uvcol;
				}
				break;
			case SCE_PASS_VECTOR:
				col= shr->winspeed;
				pixsize= 4;
				break;
			case SCE_PASS_INDEXOB:
				if(shi->vlr) {
					fp= rpass->rect + offset;
					*fp= (float)shi->vlr->ob->index;
				}
				break;
		}
		if(col) {
			fp= rpass->rect + pixsize*offset;
			for(a=0; a<pixsize; a++)
				fp[a]= col[a];
		}
	}
}

/* only do sky, is default in the solid layer (shade_tile) btw */
static void sky_tile(RenderPart *pa, float *pass)
{
	float col[4];
	int x, y;
	
	if(R.r.alphamode!=R_ADDSKY)
		return;
	
	for(y=pa->disprect.ymin; y<pa->disprect.ymax; y++) {
		for(x=pa->disprect.xmin; x<pa->disprect.xmax; x++, pass+=4) {
			if(pass[3]<1.0f) {
				if(pass[3]==0.0f)
					shadeSkyPixel(pass, x, y);
				else {
					shadeSkyPixel(col, x, y);
					addAlphaOverFloat(col, pass);
					QUATCOPY(pass, col);
				}
			}
		}
		
		if(y&1)
			if(R.test_break()) break; 
	}
}

static void shadeDA_tile(RenderPart *pa, RenderLayer *rl)
{
	RenderResult *rr= pa->result;
	ShadeSample ssamp;
	float *fcol, *rf, *rectf= rl->rectf;
	long *rd, *rectdaps= pa->rectdaps;
	int samp;
	int x, y, seed, crop=0, offs=0, od, addpassflag;
	
	if(R.test_break()) return; 
	
	/* irregular shadowb buffer creation */
	if(R.r.mode & R_SHADOW)
		ISB_create(pa, NULL);
	
	/* we set per pixel a fixed seed, for random AO and shadow samples */
	seed= pa->rectx*pa->disprect.ymin;
	
	/* general shader info, passes */
	shade_sample_initialize(&ssamp, pa, rl);
	addpassflag= rl->passflag & ~(SCE_PASS_Z|SCE_PASS_COMBINED);
				
	/* filtered render, for now we assume only 1 filter size */
	if(pa->crop) {
		crop= 1;
		rectf+= 4*(pa->rectx + 1);
		rectdaps+= pa->rectx + 1;
		offs= pa->rectx + 1;
	}
	
	/* scanline updates have to be 2 lines behind */
	rr->renrect.ymin= 0;
	rr->renrect.ymax= -2*crop;
	rr->renlay= rl;
				
	for(y=pa->disprect.ymin+crop; y<pa->disprect.ymax-crop; y++, rr->renrect.ymax++) {
		rf= rectf;
		rd= rectdaps;
		od= offs;
		
		for(x=pa->disprect.xmin+crop; x<pa->disprect.xmax-crop; x++, rd++, rf+=4, od++) {
			BLI_thread_srandom(pa->thread, seed++);
			
			if(*rd) {
				if(shade_samples(&ssamp, (PixStr *)(*rd), x, y)) {
					for(samp=0; samp<ssamp.tot; samp++) {
						
						fcol= ssamp.shr[samp].combined;
						add_filt_fmask(ssamp.shi[samp].mask, fcol, rf, pa->rectx);
						
						if(addpassflag)
							add_filt_passes(rl, ssamp.shi[samp].mask, pa->rectx, od, &ssamp.shi[samp], &ssamp.shr[samp]);
					}
				}
			}
		}
		
		rectf+= 4*pa->rectx;
		rectdaps+= pa->rectx;
		offs+= pa->rectx;
		
		if(y&1) if(R.test_break()) break; 
	}
	
	/* disable scanline updating */
	rr->renlay= NULL;
	
	if(R.r.mode & R_SHADOW)
		ISB_free(pa);
}

/* ************* pixel struct ******** */


static PixStrMain *addpsmain(ListBase *lb)
{
	PixStrMain *psm;
	
	psm= (PixStrMain *)MEM_mallocN(sizeof(PixStrMain),"pixstrMain");
	BLI_addtail(lb, psm);
	
	psm->ps= (PixStr *)MEM_mallocN(4096*sizeof(PixStr),"pixstr");
	psm->counter= 0;
	
	return psm;
}

static void freeps(ListBase *lb)
{
	PixStrMain *psm, *psmnext;
	
	for(psm= lb->first; psm; psm= psmnext) {
		psmnext= psm->next;
		if(psm->ps)
			MEM_freeN(psm->ps);
		MEM_freeN(psm);
	}
	lb->first= lb->last= NULL;
}

static void addps(ListBase *lb, long *rd, int facenr, int z, unsigned short mask)
{
	PixStrMain *psm;
	PixStr *ps, *last= NULL;
	
	if(*rd) {	
		ps= (PixStr *)(*rd);
		
		while(ps) {
			if( ps->facenr == facenr ) {
				ps->mask |= mask;
				return;
			}
			last= ps;
			ps= ps->next;
		}
	}
	
	/* make new PS (pixel struct) */
	psm= lb->last;
	
	if(psm->counter==4095)
		psm= addpsmain(lb);
	
	ps= psm->ps + psm->counter++;
	
	if(last) last->next= ps;
	else *rd= (long)ps;
	
	ps->next= NULL;
	ps->facenr= facenr;
	ps->z= z;
	ps->mask = mask;
}

static void make_pixelstructs(RenderPart *pa, ListBase *lb)
{
	long *rd= pa->rectdaps;
	int *rp= pa->rectp;
	int *rz= pa->rectz;
	int x, y;
	int mask= 1<<pa->sample;
	
	for(y=0; y<pa->recty; y++) {
		for(x=0; x<pa->rectx; x++, rd++, rp++) {
			if(*rp) {
				addps(lb, rd, *rp, *(rz+x), mask);
			}
		}
		rz+= pa->rectx;
	}
}

static void edge_enhance_add(RenderPart *pa, float *rectf, float *arect)
{
	float addcol[4];
	int pix;
	
	if(arect==NULL)
		return;
	
	for(pix= pa->rectx*pa->recty; pix>0; pix--, arect++, rectf+=4) {
		if(*arect != 0.0f) {
			addcol[0]= *arect * R.r.edgeR;
			addcol[1]= *arect * R.r.edgeG;
			addcol[2]= *arect * R.r.edgeB;
			addcol[3]= *arect;
			addAlphaOverFloat(rectf, addcol);
		}
	}
}


static void convert_to_key_alpha(RenderPart *pa, float *rectf)
{
	int y;
	
	for(y= pa->rectx*pa->recty; y>0; y--, rectf+=4) {
		if(rectf[3] >= 1.0f);
		else if(rectf[3] > 0.0f) {
			rectf[0] /= rectf[3];
			rectf[1] /= rectf[3];
			rectf[2] /= rectf[3];
		}
	}
}

/* adds only alpha values */
static void edge_enhance_tile(RenderPart *pa, float *rectf)	
{
	/* use zbuffer to define edges, add it to the image */
	int y, x, col, *rz, *rz1, *rz2, *rz3;
	int zval1, zval2, zval3;
	float *rf;
	
	/* shift values in zbuffer 4 to the right (anti overflows), for filter we need multiplying with 12 max */
	rz= pa->rectz;
	if(rz==NULL) return;
	
	for(y=0; y<pa->recty; y++)
		for(x=0; x<pa->rectx; x++, rz++) (*rz)>>= 4;
	
	rz1= pa->rectz;
	rz2= rz1+pa->rectx;
	rz3= rz2+pa->rectx;
	
	rf= rectf+pa->rectx+1;
	
	for(y=0; y<pa->recty-2; y++) {
		for(x=0; x<pa->rectx-2; x++, rz1++, rz2++, rz3++, rf++) {
			
			/* prevent overflow with sky z values */
			zval1=   rz1[0] + 2*rz1[1] +   rz1[2];
			zval2=  2*rz2[0]           + 2*rz2[2];
			zval3=   rz3[0] + 2*rz3[1] +   rz3[2];
			
			col= ( 4*rz2[1] - (zval1 + zval2 + zval3)/3 );
			if(col<0) col= -col;
			
			col >>= 5;
			if(col > (1<<16)) col= (1<<16);
			else col= (R.r.edgeint*col)>>8;
			
			if(col>0) {
				float fcol;
				
				if(col>255) fcol= 1.0f;
				else fcol= (float)col/255.0f;
				
				if(R.osa)
					*rf+= fcol/(float)R.osa;
				else
					*rf= fcol;
			}
		}
		rz1+= 2;
		rz2+= 2;
		rz3+= 2;
		rf+= 2;
	}
	
	/* shift back zbuf values, we might need it still */
	rz= pa->rectz;
	for(y=0; y<pa->recty; y++)
		for(x=0; x<pa->rectx; x++, rz++) (*rz)<<= 4;
	
}

static void reset_sky_speed(RenderPart *pa, RenderLayer *rl)
{
	/* for all pixels with max speed, set to zero */
	float *fp;
	int a;
	
	fp= RE_RenderLayerGetPass(rl, SCE_PASS_VECTOR);
	if(fp==NULL) return;
	
	for(a= 4*pa->rectx*pa->recty; a>0; a--)
		if(fp[a] == PASS_VECTOR_MAX) fp[a]= 0.0f;
}


static unsigned short *make_solid_mask(RenderPart *pa)
{ 
 	long *rd= pa->rectdaps;
 	short *solidmask, *sp;
 	int x;
 	
	if(rd==NULL) return NULL;
 	
	sp=solidmask= MEM_mallocN(sizeof(short)*pa->rectx*pa->recty, "solidmask");
 	
	for(x=pa->rectx*pa->recty; x>0; x--, rd++, sp++) {
		if(*rd) {
			PixStr *ps= (PixStr *)*rd;
			
			*sp= ps->mask;
			for(ps= ps->next; ps; ps= ps->next)
				*sp |= ps->mask;
		}
		else
			*sp= 0;
	}
 			
	return solidmask;
}

static void addAlphaOverFloatMask(float *dest, float *source, unsigned short dmask, unsigned short smask)
{
	unsigned short shared= dmask & smask;
	float mul= 1.0 - source[3];
	
	if(shared) {	/* overlapping masks */
		
		/* masks differ, we make a mixture of 'add' and 'over' */
		if(shared!=dmask) {
			float shared_bits= (float)count_mask(shared);		/* alpha over */
			float tot_bits= (float)count_mask(smask|dmask);		/* alpha add */
			
			float add= (tot_bits - shared_bits)/tot_bits;		/* add level */
			mul= add + (1.0f-add)*mul;
		}
	}
	else if(dmask && smask) {
		/* works for premul only, of course */
		dest[0]+= source[0];
		dest[1]+= source[1];
		dest[2]+= source[2];
		dest[3]+= source[3];
		
		return;
 	}

	dest[0]= (mul*dest[0]) + source[0];
	dest[1]= (mul*dest[1]) + source[1];
	dest[2]= (mul*dest[2]) + source[2];
	dest[3]= (mul*dest[3]) + source[3];
}


/* main call for shading Delta Accum, for OSA */
/* supposed to be fully threadable! */
void zbufshadeDA_tile(RenderPart *pa)
{
	RenderResult *rr= pa->result;
	RenderLayer *rl;
	ListBase psmlist= {NULL, NULL};
	float *edgerect= NULL;
	
	set_part_zbuf_clipflag(pa);
	
	/* allocate the necessary buffers */
				/* zbuffer inits these rects */
	pa->rectp= MEM_mallocN(sizeof(int)*pa->rectx*pa->recty, "rectp");
	pa->rectz= MEM_mallocN(sizeof(int)*pa->rectx*pa->recty, "rectz");
	
	for(rl= rr->layers.first; rl; rl= rl->next) {

		/* initialize pixelstructs and edge buffer */
		addpsmain(&psmlist);
		pa->rectdaps= MEM_callocN(sizeof(long)*pa->rectx*pa->recty+4, "zbufDArectd");
		
		if(rl->layflag & SCE_LAY_EDGE) 
			if(R.r.mode & R_EDGE) 
				edgerect= MEM_callocN(sizeof(float)*pa->rectx*pa->recty, "rectedge");
		
		/* always fill visibility */
		for(pa->sample=0; pa->sample<R.osa; pa->sample++) {
			zbuffer_solid(pa, rl->lay, rl->layflag);
			make_pixelstructs(pa, &psmlist);
			
			if(rl->layflag & SCE_LAY_EDGE) 
				if(R.r.mode & R_EDGE) 
					edge_enhance_tile(pa, edgerect);
			
			if(R.test_break()) break; 
		}
		
		/* shades solid */
		if(rl->layflag & SCE_LAY_SOLID) 
			shadeDA_tile(pa, rl);
		
		/* lamphalo after solid, before ztra, looks nicest because ztra does own halo */
		if(R.flag & R_LAMPHALO)
			if(rl->layflag & SCE_LAY_HALO)
				lamphalo_tile(pa, rl);
		
		/* halo before ztra, because ztra fills in zbuffer now */
		if(R.flag & R_HALO)
			if(rl->layflag & SCE_LAY_HALO)
				halo_tile(pa, rl->rectf, rl->lay);
		
		/* transp layer */
		if(R.flag & R_ZTRA) {
			if(rl->layflag & SCE_LAY_ZTRA) {
				unsigned short *ztramask, *solidmask= NULL; /* 16 bits, MAX_OSA */
				
				/* allocate, but not free here, for asynchronous display of this rect in main thread */
				rl->acolrect= MEM_callocN(4*sizeof(float)*pa->rectx*pa->recty, "alpha layer");
				
				/* swap for live updates */
				SWAP(float *, rl->acolrect, rl->rectf);
				ztramask= zbuffer_transp_shade(pa, rl, rl->rectf);
				SWAP(float *, rl->acolrect, rl->rectf);
				
				/* zbuffer transp only returns ztramask if there's solid rendered */
				if(ztramask)
					solidmask= make_solid_mask(pa);
				
				if(ztramask && solidmask) {
					unsigned short *sps= solidmask, *spz= ztramask;
					unsigned short fullmask= (1<<R.osa)-1;
					float *fcol= rl->rectf; float *acol= rl->acolrect;
					int x;
					
					for(x=pa->rectx*pa->recty; x>0; x--, acol+=4, fcol+=4, sps++, spz++) {
						if(*sps == fullmask)
							addAlphaOverFloat(fcol, acol);
						else
							addAlphaOverFloatMask(fcol, acol, *sps, *spz);
					}
 				}
				else {
					float *fcol= rl->rectf; float *acol= rl->acolrect;
					int x;
					for(x=pa->rectx*pa->recty; x>0; x--, acol+=4, fcol+=4) {
						addAlphaOverFloat(fcol, acol);
					}
				}
				if(solidmask) MEM_freeN(solidmask);
				if(ztramask) MEM_freeN(ztramask);
			}
		}
		/* sky before edge */
		if(rl->layflag & SCE_LAY_SKY)
			sky_tile(pa, rl->rectf);

		/* extra layers */
		if(rl->layflag & SCE_LAY_EDGE) 
			if(R.r.mode & R_EDGE) 
				edge_enhance_add(pa, rl->rectf, edgerect);
		
		if(rl->passflag & SCE_PASS_Z)
			convert_zbuf_to_distbuf(pa, rl);
		
		if(rl->passflag & SCE_PASS_VECTOR)
			reset_sky_speed(pa, rl);
		
		/* de-premul alpha */
		if(R.r.alphamode & R_ALPHAKEY)
			convert_to_key_alpha(pa, rl->rectf);
		
		/* free stuff within loop! */
		MEM_freeN(pa->rectdaps); pa->rectdaps= NULL;
		freeps(&psmlist);
		
		if(edgerect) MEM_freeN(edgerect);
		edgerect= NULL;
	}
	
	/* free all */
	MEM_freeN(pa->rectp); pa->rectp= NULL;
	MEM_freeN(pa->rectz); pa->rectz= NULL;
	MEM_freeN(pa->clipflag); pa->clipflag= NULL;
	
	/* display active layer */
	rr->renrect.ymin=rr->renrect.ymax= 0;
	rr->renlay= render_get_active_layer(&R, rr);
}


/* ------------------------------------------------------------------------ */

/* non OSA case, full tile render */
/* supposed to be fully threadable! */
void zbufshade_tile(RenderPart *pa)
{
	ShadeSample ssamp;
	RenderResult *rr= pa->result;
	RenderLayer *rl;
	PixStr ps;
	float *edgerect= NULL;
	int addpassflag;
	
	/* fake pixel struct, to comply to osa render */
	ps.next= NULL;
	ps.mask= 0xFFFF;
	
	set_part_zbuf_clipflag(pa);
	
	/* zbuffer code clears/inits rects */
	pa->rectp= MEM_mallocN(sizeof(int)*pa->rectx*pa->recty, "rectp");
	pa->rectz= MEM_mallocN(sizeof(int)*pa->rectx*pa->recty, "rectz");

	for(rl= rr->layers.first; rl; rl= rl->next) {
		
		/* general shader info, passes */
		shade_sample_initialize(&ssamp, pa, rl);
		addpassflag= rl->passflag & ~(SCE_PASS_Z|SCE_PASS_COMBINED);
		
		zbuffer_solid(pa, rl->lay, rl->layflag);
		
		if(!R.test_break()) {	/* NOTE: this if() is not consistant */
			
			/* edges only for solid part, ztransp doesn't support it yet anti-aliased */
			if(rl->layflag & SCE_LAY_EDGE) {
				if(R.r.mode & R_EDGE) {
					edgerect= MEM_callocN(sizeof(float)*pa->rectx*pa->recty, "rectedge");
					edge_enhance_tile(pa, edgerect);
				}
			}
			
			/* initialize scanline updates for main thread */
			rr->renrect.ymin= 0;
			rr->renlay= rl;
			
			if(rl->layflag & SCE_LAY_SOLID) {
				float *fcol= rl->rectf;
				int x, y, *rp= pa->rectp, *rz= pa->rectz, offs=0, seed;
				
				/* we set per pixel a fixed seed, for random AO and shadow samples */
				seed= pa->rectx*pa->disprect.ymin;
				
				/* irregular shadowb buffer creation */
				if(R.r.mode & R_SHADOW)
					ISB_create(pa, NULL);
				
				for(y=pa->disprect.ymin; y<pa->disprect.ymax; y++, rr->renrect.ymax++) {
					for(x=pa->disprect.xmin; x<pa->disprect.xmax; x++, rz++, rp++, fcol+=4, offs++) {
						/* per pixel fixed seed */
						BLI_thread_srandom(pa->thread, seed++);
						
						if(*rp) {
							ps.facenr= *rp;
							ps.z= *rz;
							if(shade_samples(&ssamp, &ps, x, y)) {
								QUATCOPY(fcol, ssamp.shr[0].combined);
								
								/* passes */
								if(addpassflag)
									add_passes(rl, offs, ssamp.shi, ssamp.shr);
							}
						}
					}
					if(y&1)
						if(R.test_break()) break; 
				}
				
				if(R.r.mode & R_SHADOW)
					ISB_free(pa);
			}
			
			/* disable scanline updating */
			rr->renlay= NULL;
		}
		
		/* lamphalo after solid, before ztra, looks nicest because ztra does own halo */
		if(R.flag & R_LAMPHALO)
			if(rl->layflag & SCE_LAY_HALO)
				lamphalo_tile(pa, rl);
		
		/* halo before ztra, because ztra fills in zbuffer now */
		if(R.flag & R_HALO)
			if(rl->layflag & SCE_LAY_HALO)
				halo_tile(pa, rl->rectf, rl->lay);
		
		if(R.flag & R_ZTRA) {
			if(rl->layflag & SCE_LAY_ZTRA) {
				float *fcol, *acol;
				int x;
				
				/* allocate, but not free here, for asynchronous display of this rect in main thread */
				rl->acolrect= MEM_callocN(4*sizeof(float)*pa->rectx*pa->recty, "alpha layer");
				
				/* swap for live updates */
				SWAP(float *, rl->acolrect, rl->rectf);
				zbuffer_transp_shade(pa, rl, rl->rectf);
				SWAP(float *, rl->acolrect, rl->rectf);
				
				fcol= rl->rectf; acol= rl->acolrect;
				for(x=pa->rectx*pa->recty; x>0; x--, acol+=4, fcol+=4) {
					addAlphaOverFloat(fcol, acol);
				}
			}
		}
		
		/* sky before edge */
		if(rl->layflag & SCE_LAY_SKY)
			sky_tile(pa, rl->rectf);
		
		if(!R.test_break()) {
			if(rl->layflag & SCE_LAY_EDGE) 
				if(R.r.mode & R_EDGE)
					edge_enhance_add(pa, rl->rectf, edgerect);
		}
		
		if(rl->passflag & SCE_PASS_Z)
			convert_zbuf_to_distbuf(pa, rl);
		
		if(rl->passflag & SCE_PASS_VECTOR)
			reset_sky_speed(pa, rl);
		
		/* de-premul alpha */
		if(R.r.alphamode & R_ALPHAKEY)
			convert_to_key_alpha(pa, rl->rectf);
		
		if(edgerect) MEM_freeN(edgerect);
		edgerect= NULL;
	}

	/* display active layer */
	rr->renrect.ymin=rr->renrect.ymax= 0;
	rr->renlay= render_get_active_layer(&R, rr);
	
	MEM_freeN(pa->rectp); pa->rectp= NULL;
	MEM_freeN(pa->rectz); pa->rectz= NULL;
	MEM_freeN(pa->clipflag); pa->clipflag= NULL;
}

/* ------------------------------------------------------------------------ */

static void renderhalo_post(RenderResult *rr, float *rectf, HaloRen *har)	/* postprocess version */
{
	float dist, xsq, ysq, xn, yn, colf[4], *rectft, *rtf;
	float haloxs, haloys;
	int minx, maxx, miny, maxy, x, y;

	/* calculate the disprect mapped coordinate for halo. note: rectx is disprect corrected */
	haloxs= har->xs - R.disprect.xmin;
	haloys= har->ys - R.disprect.ymin;
	
	har->miny= miny= haloys - har->rad/R.ycor;
	har->maxy= maxy= haloys + har->rad/R.ycor;
	
	if(maxy<0);
	else if(rr->recty<miny);
	else {
		minx= floor(haloxs-har->rad);
		maxx= ceil(haloxs+har->rad);
			
		if(maxx<0);
		else if(rr->rectx<minx);
		else {
		
			if(minx<0) minx= 0;
			if(maxx>=rr->rectx) maxx= rr->rectx-1;
			if(miny<0) miny= 0;
			if(maxy>rr->recty) maxy= rr->recty;
	
			rectft= rectf+ 4*rr->rectx*miny;

			for(y=miny; y<maxy; y++) {
	
				rtf= rectft+4*minx;
				
				yn= (y - haloys)*R.ycor;
				ysq= yn*yn;
				
				for(x=minx; x<=maxx; x++) {
					xn= x - haloxs;
					xsq= xn*xn;
					dist= xsq+ysq;
					if(dist<har->radsq) {
						
						shadeHaloFloat(har, colf, 0x7FFFFF, dist, xn, yn, har->flarec);
						addalphaAddfacFloat(rtf, colf, har->add);
					}
					rtf+=4;
				}
	
				rectft+= 4*rr->rectx;
				
				if(R.test_break()) break; 
			}
		}
	}
} 
/* ------------------------------------------------------------------------ */

static void renderflare(RenderResult *rr, float *rectf, HaloRen *har)
{
	extern float hashvectf[];
	HaloRen fla;
	Material *ma;
	float *rc, rad, alfa, visifac, vec[3];
	int b, type;
	
	fla= *har;
	fla.linec= fla.ringc= fla.flarec= 0;
	
	rad= har->rad;
	alfa= har->alfa;
	
	visifac= R.ycor*(har->pixels);
	/* all radials added / r^3  == 1.0f! */
	visifac /= (har->rad*har->rad*har->rad);
	visifac*= visifac;

	ma= har->mat;
	
	/* first halo: just do */
	
	har->rad= rad*ma->flaresize*visifac;
	har->radsq= har->rad*har->rad;
	har->zs= fla.zs= 0;
	
	har->alfa= alfa*visifac;

	renderhalo_post(rr, rectf, har);
	
	/* next halo's: the flares */
	rc= hashvectf + ma->seed2;
	
	for(b=1; b<har->flarec; b++) {
		
		fla.r= fabs(rc[0]);
		fla.g= fabs(rc[1]);
		fla.b= fabs(rc[2]);
		fla.alfa= ma->flareboost*fabs(alfa*visifac*rc[3]);
		fla.hard= 20.0f + fabs(70*rc[7]);
		fla.tex= 0;
		
		type= (int)(fabs(3.9*rc[6]));

		fla.rad= ma->subsize*sqrt(fabs(2.0f*har->rad*rc[4]));
		
		if(type==3) {
			fla.rad*= 3.0f;
			fla.rad+= R.rectx/10;
		}
		
		fla.radsq= fla.rad*fla.rad;
		
		vec[0]= 1.4*rc[5]*(har->xs-R.winx/2);
		vec[1]= 1.4*rc[5]*(har->ys-R.winy/2);
		vec[2]= 32.0f*sqrt(vec[0]*vec[0] + vec[1]*vec[1] + 1.0f);
		
		fla.xs= R.winx/2 + vec[0] + (1.2+rc[8])*R.rectx*vec[0]/vec[2];
		fla.ys= R.winy/2 + vec[1] + (1.2+rc[8])*R.rectx*vec[1]/vec[2];

		if(R.flag & R_SEC_FIELD) {
			if(R.r.mode & R_ODDFIELD) fla.ys += 0.5;
			else fla.ys -= 0.5;
		}
		if(type & 1) fla.type= HA_FLARECIRC;
		else fla.type= 0;
		renderhalo_post(rr, rectf, &fla);

		fla.alfa*= 0.5;
		if(type & 2) fla.type= HA_FLARECIRC;
		else fla.type= 0;
		renderhalo_post(rr, rectf, &fla);
		
		rc+= 7;
	}
}

/* needs recode... integrate this better! */
void add_halo_flare(Render *re)
{
	RenderResult *rr= re->result;
	RenderLayer *rl;
	HaloRen *har = NULL;
	int a, mode, do_draw=0;
	
	/* for now, we get the first renderlayer in list with halos set */
	for(rl= rr->layers.first; rl; rl= rl->next)
		if(rl->layflag & SCE_LAY_HALO)
			break;

	if(rl==NULL || rl->rectf==NULL)
		return;
	
	mode= R.r.mode;
	R.r.mode &= ~R_PANORAMA;
	
	project_renderdata(&R, projectverto, 0, 0);
	
	for(a=0; a<R.tothalo; a++) {
		if((a & 255)==0) har= R.bloha[a>>8];
		else har++;
		
		if(har->flarec) {
			do_draw= 1;
			renderflare(rr, rl->rectf, har);
		}
	}

	if(do_draw) {
		/* weak... the display callback wants an active renderlayer pointer... */
		rr->renlay= rl;
		re->display_draw(rr, NULL);
	}
	
	R.r.mode= mode;	
}

/* ************************* used for shaded view ************************ */

/* if *re, then initialize, otherwise execute */
void RE_shade_external(Render *re, ShadeInput *shi, ShadeResult *shr)
{
	static VlakRen vlr;
	
	/* init */
	if(re) {
		R= *re;
		
		/* fake render face */
		memset(&vlr, 0, sizeof(VlakRen));
		vlr.lay= -1;
		
		return;
	}
	shi->vlr= &vlr;
	
	if(shi->mat->nodetree && shi->mat->use_nodes)
		ntreeShaderExecTree(shi->mat->nodetree, shi, shr);
	else {
		/* copy all relevant material vars, note, keep this synced with render_types.h */
		memcpy(&shi->r, &shi->mat->r, 23*sizeof(float));
		shi->har= shi->mat->har;
		
		shade_material_loop(shi, shr);
	}
}

/* ************************* bake ************************ */

#define FTOCHAR(val) val<=0.0f?0: (val>=1.0f?255: (char)(255.0f*val))

typedef struct BakeShade {
	ShadeSample ssamp;
	VlakRen *vlr;
	
	ZSpan *zspan;
	Image *ima;
	ImBuf *ibuf;
	
	int rectx, recty, quad, type, vdone, ready;
	
	unsigned int *rect;
	float *rect_float;
} BakeShade;

static void do_bake_shade(void *handle, int x, int y, float u, float v)
{
	BakeShade *bs= handle;
	ShadeSample *ssamp= &bs->ssamp;
	ShadeInput *shi= ssamp->shi;
	ShadeResult shr;
	VlakRen *vlr= bs->vlr;
	float l, *v1, *v2, *v3;
	
	/* fast threadsafe break test */
	if(R.test_break())
		return;
	
	/* setup render coordinates */
	if(bs->quad) {
		v1= vlr->v1->co;
		v2= vlr->v3->co;
		v3= vlr->v4->co;
	}
	else {
		v1= vlr->v1->co;
		v2= vlr->v2->co;
		v3= vlr->v3->co;
	}
	
	/* renderco */
	l= 1.0f-u-v;
	
	shi->co[0]= l*v3[0]+u*v1[0]+v*v2[0];
	shi->co[1]= l*v3[1]+u*v1[1]+v*v2[1];
	shi->co[2]= l*v3[2]+u*v1[2]+v*v2[2];
	
	/* set up view vector */
	VECCOPY(shi->view, shi->co);
	Normalise(shi->view);
	
	/* no face normal flip */
	shi->puno= 0;
	
	/* cache for shadow */
	shi->samplenr++;
	
	if(bs->quad) 
		shade_input_set_triangle_i(shi, vlr, 0, 2, 3);
	else
		shade_input_set_triangle_i(shi, vlr, 0, 1, 2);
	
	shi->u= -u;
	shi->v= -v;
	shi->xs= x;
	shi->ys= y;
	
	shade_input_set_normals(shi);

	/* init material vars */
	memcpy(&shi->r, &shi->mat->r, 23*sizeof(float));	// note, keep this synced with render_types.h
	shi->har= shi->mat->har;
	
	if(bs->type==RE_BAKE_AO) {
		ambient_occlusion(shi);
		ambient_occlusion_to_diffuse(shi, shr.combined);
	}
	else {
		
		shade_input_set_shade_texco(shi);
		
		shade_samples_do_AO(ssamp);
		
		if(shi->mat->nodetree && shi->mat->use_nodes) {
			ntreeShaderExecTree(shi->mat->nodetree, shi, &shr);
			shi->mat= vlr->mat;		/* shi->mat is being set in nodetree */
		}
		else
			shade_material_loop(shi, &shr);
		
		if(bs->type==RE_BAKE_NORMALS) {
			shr.combined[0]= shi->vn[0]/2.0f + 0.5f;
			shr.combined[1]= 0.5f - shi->vn[1]/2.0f;
			shr.combined[2]= shi->vn[2]/2.0f + 0.5f;
		}
		else if(bs->type==RE_BAKE_TEXTURE) {
			shr.combined[0]= shi->r;
			shr.combined[1]= shi->g;
			shr.combined[2]= shi->b;
		}
	}
	
	if(bs->rect) {
		char *col= (char *)(bs->rect + bs->rectx*y + x);
		col[0]= FTOCHAR(shr.combined[0]);
		col[1]= FTOCHAR(shr.combined[1]);
		col[2]= FTOCHAR(shr.combined[2]);
		col[3]= 255;
	}
	else {
		float *col= bs->rect_float + 4*(bs->rectx*y + x);
		VECCOPY(col, shr.combined);
		col[3]= 1.0f;
	}
}

static int get_next_bake_face(BakeShade *bs)
{
	VlakRen *vlr;
	MTFace *tface;
	static int v= 0, vdone= 0;
	
	if(bs==NULL) {
		vlr= NULL;
		v= vdone= 0;
		return 0;
	}
	
	BLI_lock_thread(LOCK_CUSTOM1);	
	
	for(; v<R.totvlak; v++) {
		vlr= RE_findOrAddVlak(&R, v);
		
		if(vlr->ob->flag & SELECT) {
			tface= RE_vlakren_get_tface(&R, vlr, 0, NULL, 0);

			if(tface && tface->tpage) {
				Image *ima= tface->tpage;
				ImBuf *ibuf= BKE_image_get_ibuf(ima, NULL);
				float vec[4]= {0.0f, 0.0f, 0.0f, 0.0f};
				
				if(ibuf==NULL)
					continue;
				
				if(ibuf->rect==NULL && ibuf->rect_float==NULL)
					continue;
				
				if(ibuf->rect_float && !(ibuf->channels==0 || ibuf->channels==4))
					continue;
				
				/* find the image for the first time? */
				if(ima->id.flag & LIB_DOIT) {
					ima->id.flag &= ~LIB_DOIT;
					
					/* we either fill in float or char, this ensures things go fine */
					if(ibuf->rect_float)
						imb_freerectImBuf(ibuf);
					/* clear image */
					if(R.r.bake_flag & R_BAKE_CLEAR)
						IMB_rectfill(ibuf, vec);
				
					/* might be read by UI to set active image for display */
					R.bakebuf= ima;
				}				
				
				bs->vlr= vlr;
				
				bs->vdone++;	/* only for error message if nothing was rendered */
				v++;
				
				BLI_unlock_thread(LOCK_CUSTOM1);
				return 1;
			}
		}
	}
	
	BLI_unlock_thread(LOCK_CUSTOM1);
	return 0;
}

/* already have tested for tface and ima and zspan */
static void shade_tface(BakeShade *bs)
{
	VlakRen *vlr= bs->vlr;
	MTFace *tface= RE_vlakren_get_tface(&R, vlr, 0, NULL, 0);
	Image *ima= tface->tpage;
	float vec[4][2];
	int a, i1, i2, i3;
	
	/* check valid zspan */
	if(ima!=bs->ima) {
		bs->ima= ima;
		bs->ibuf= BKE_image_get_ibuf(ima, NULL);
		/* note, these calls only free/fill contents of zspan struct, not zspan itself */
		zbuf_free_span(bs->zspan);
		zbuf_alloc_span(bs->zspan, bs->ibuf->x, bs->ibuf->y);
	}				
	
	bs->rectx= bs->ibuf->x;
	bs->recty= bs->ibuf->y;
	bs->rect= bs->ibuf->rect;
	bs->rect_float= bs->ibuf->rect_float;
	bs->quad= 0;
	
	/* get pixel level vertex coordinates */
	for(a=0; a<4; a++) {
		vec[a][0]= tface->uv[a][0]*(float)bs->rectx - 0.5f;
		vec[a][1]= tface->uv[a][1]*(float)bs->recty - 0.5f;
	}
	
	/* UV indices have to be corrected for possible quad->tria splits */
	i1= 0; i2= 1; i3= 2;
	vlr_set_uv_indices(vlr, &i1, &i2, &i3);
	zspan_scanconvert(bs->zspan, bs, vec[i1], vec[i2], vec[i3], do_bake_shade);
	
	if(vlr->v4) {
		bs->quad= 1;
		zspan_scanconvert(bs->zspan, bs, vec[0], vec[2], vec[3], do_bake_shade);
	}
}

static void *do_bake_thread(void *bs_v)
{
	BakeShade *bs= bs_v;
	
	while(get_next_bake_face(bs)) {
		shade_tface(bs);
		
		/* fast threadsafe break test */
		if(R.test_break())
			break;
	}
	bs->ready= 1;
	
	return NULL;
}

/* using object selection tags, the faces with UV maps get baked */
/* render should have been setup */
/* returns 0 if nothing was handled */
int RE_bake_shade_all_selected(Render *re, int type)
{
	BakeShade handles[BLENDER_MAX_THREADS];
	ListBase threads;
	Image *ima;
	int a, vdone=0;
	
	/* initialize static vars */
	get_next_bake_face(NULL);
	
	/* baker uses this flag to detect if image was initialized */
	for(ima= G.main->image.first; ima; ima= ima->id.next)
		ima->id.flag |= LIB_DOIT;
	
	/* initialize render global */
	R= *re;
	R.bakebuf= NULL;
	
	BLI_init_threads(&threads, do_bake_thread, re->r.threads);

	/* get the threads running */
	for(a=0; a<re->r.threads; a++) {
		/* set defaults in handles */
		memset(&handles[a], 0, sizeof(BakeShade));
		
		handles[a].ssamp.shi[0].lay= re->scene->lay;
		handles[a].ssamp.shi[0].passflag= SCE_PASS_COMBINED;
		handles[a].ssamp.shi[0].combinedflag= ~(SCE_PASS_SPEC);
		handles[a].ssamp.shi[0].thread= a;
		handles[a].ssamp.tot= 1;
		
		handles[a].type= type;
		handles[a].zspan= MEM_callocN(sizeof(ZSpan), "zspan for bake");
		
		BLI_insert_thread(&threads, &handles[a]);
	}
	
	/* wait for everything to be done */
	a= 0;
	while(a!=re->r.threads) {
		
		PIL_sleep_ms(50);

		for(a=0; a<re->r.threads; a++)
			if(handles[a].ready==0)
				break;
	}
	
	/* filter images */
	for(ima= G.main->image.first; ima; ima= ima->id.next) {
		if((ima->id.flag & LIB_DOIT)==0) {
			ImBuf *ibuf= BKE_image_get_ibuf(ima, NULL);
			for(a=0; a<re->r.bake_filter; a++)
				IMB_filter_extend(ibuf);
			ibuf->userflags |= IB_BITMAPDIRTY;
		}
	}
	
	/* calculate return value */
	for(a=0; a<re->r.threads; a++) {
		vdone+= handles[a].vdone;
		
		zbuf_free_span(handles[a].zspan);
		MEM_freeN(handles[a].zspan);
	}
	
	BLI_end_threads(&threads);
	return vdone;
}

struct Image *RE_bake_shade_get_image(void)
{
	return R.bakebuf;
}

