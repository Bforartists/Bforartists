/**
 *
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
 * Contributors: 2004/2005/2006 Blender Foundation, full recode
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */



#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <math.h>
#ifndef WIN32 
#include <unistd.h>
#else
#include <io.h>
#endif

#include "MEM_guardedalloc.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "DNA_image_types.h"
#include "DNA_scene_types.h"
#include "DNA_texture_types.h"

#include "BLI_blenlib.h"
#include "BLI_threads.h"

#include "BKE_utildefines.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_image.h"
#include "BKE_texture.h"
#include "BKE_library.h"

#include "renderpipeline.h"
#include "render_types.h"
#include "texture.h"

/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */
/* defined in pipeline.c, is hardcopy of active dynamic allocated Render */
/* only to be used here in this file, it's for speed */
extern struct Render R;
/* ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ */

int imaprepeat, imapextend;


/* *********** IMAGEWRAPPING ****************** */

/* x and y have to be checked for image size */
static void ibuf_get_color(float *col, struct ImBuf *ibuf, int x, int y)
{
	int ofs = y * ibuf->x + x;
	
	if(ibuf->rect_float) {
		float *fp= ibuf->rect_float + 4*ofs;
		QUATCOPY(col, fp);
	}
	else {
		char *rect = (char *)( ibuf->rect+ ofs);

		col[0] = ((float)rect[0])/255.0f;
		col[1] = ((float)rect[1])/255.0f;
		col[2] = ((float)rect[2])/255.0f;
		col[3] = ((float)rect[3])/255.0f;
	}	
}

int imagewrap(Tex *tex, Image *ima, float *texvec, TexResult *texres)
{
	struct ImBuf *ibuf;
	float fx, fy, val1, val2, val3;
	int x, y;

	texres->tin= texres->ta= texres->tr= texres->tg= texres->tb= 0.0;

	if(ima==NULL || ima->ok== 0) {
		if(texres->nor) return 3;
		else return 1;
	}
	
	if(ima->ibuf==NULL) {
		BLI_lock_thread(LOCK_MALLOC);
		if(ima->ibuf==NULL) ima_ibuf_is_nul(tex, ima);
		BLI_unlock_thread(LOCK_MALLOC);
	}

	if (ima->ok) {
		ibuf = ima->ibuf;

		if(tex->imaflag & TEX_IMAROT) {
			fy= texvec[0];
			fx= texvec[1];
		}
		else {
			fx= texvec[0];
			fy= texvec[1];
		}
		
		if(tex->extend == TEX_CHECKER) {
			int xs, ys;
			
			xs= (int)floor(fx);
			ys= (int)floor(fy);
			fx-= xs;
			fy-= ys;

			if( (tex->flag & TEX_CHECKER_ODD)==0) {
				if((xs+ys) & 1);else return 0;
			}
			if( (tex->flag & TEX_CHECKER_EVEN)==0) {
				if((xs+ys) & 1) return 0; 
			}
			/* scale around center, (0.5, 0.5) */
			if(tex->checkerdist<1.0) {
				fx= (fx-0.5)/(1.0-tex->checkerdist) +0.5;
				fy= (fy-0.5)/(1.0-tex->checkerdist) +0.5;
			}
		}

		x = (int)(fx*ibuf->x);
		y = (int)(fy*ibuf->y);

		if(tex->extend == TEX_CLIPCUBE) {
			if(x<0 || y<0 || x>=ibuf->x || y>=ibuf->y || texvec[2]<-1.0 || texvec[2]>1.0) {
				return 0;
			}
		}
		else if( tex->extend==TEX_CLIP || tex->extend==TEX_CHECKER) {
			if(x<0 || y<0 || x>=ibuf->x || y>=ibuf->y) {
				return 0;
			}
		}
		else {
			if(tex->extend==TEX_EXTEND) {
				if(x>=ibuf->x) x = ibuf->x-1;
				else if(x<0) x= 0;
			}
			else {
				x= x % ibuf->x;
				if(x<0) x+= ibuf->x;
			}
			if(tex->extend==TEX_EXTEND) {
				if(y>=ibuf->y) y = ibuf->y-1;
				else if(y<0) y= 0;
			}
			else {
				y= y % ibuf->y;
				if(y<0) y+= ibuf->y;
			}
		}
		
		/* warning, no return before setting back! */
		if( (R.flag & R_SEC_FIELD) && (ibuf->flags & IB_fields) ) {
			ibuf->rect+= (ibuf->x*ibuf->y);
		}

		ibuf_get_color(&texres->tr, ibuf, x, y);
		
		if( (R.flag & R_SEC_FIELD) && (ibuf->flags & IB_fields) ) {
			ibuf->rect-= (ibuf->x*ibuf->y);
		}

		if(tex->imaflag & TEX_USEALPHA) {
			if(tex->imaflag & TEX_CALCALPHA);
			else texres->talpha= 1;
		}
		
		if(texres->nor) {
			if(tex->imaflag & TEX_NORMALMAP) {
				texres->nor[0]= 0.5-texres->tr;
				texres->nor[1]= 0.5-texres->tg;
				texres->nor[2]= -texres->tb;
			}
			else {
				/* bump: take three samples */
				val1= texres->tr+texres->tg+texres->tb;

				if(x<ibuf->x-1) {
					float col[4];
					ibuf_get_color(col, ibuf, x+1, y);
					val2= (col[0]+col[1]+col[2]);
				}
				else val2= val1;

				if(y<ibuf->y-1) {
					float col[4];
					ibuf_get_color(col, ibuf, x, y+1);
					val3= (col[0]+col[1]+col[2]);
				}
				else val3= val1;

				/* do not mix up x and y here! */
				texres->nor[0]= (val1-val2);
				texres->nor[1]= (val1-val3);
			}
		}

		BRICONTRGB;

		if(texres->talpha) texres->tin= texres->ta;
		else if(tex->imaflag & TEX_CALCALPHA) {
			texres->ta= texres->tin= MAX3(texres->tr, texres->tg, texres->tb);
		}
		else texres->ta= texres->tin= 1.0;
		
		if(tex->flag & TEX_NEGALPHA) texres->ta= 1.0f-texres->ta;

	}

	if(texres->nor) return 3;
	else return 1;
}

static void clipx_rctf_swap(rctf *stack, short *count, float x1, float x2)
{
	rctf *rf, *newrct;
	short a;

	a= *count;
	rf= stack;
	for(;a>0;a--) {
		if(rf->xmin<x1) {
			if(rf->xmax<x1) {
				rf->xmin+= (x2-x1);
				rf->xmax+= (x2-x1);
			}
			else {
				if(rf->xmax>x2) rf->xmax= x2;
				newrct= stack+ *count;
				(*count)++;

				newrct->xmax= x2;
				newrct->xmin= rf->xmin+(x2-x1);
				newrct->ymin= rf->ymin;
				newrct->ymax= rf->ymax;
				
				if(newrct->xmin==newrct->xmax) (*count)--;
				
				rf->xmin= x1;
			}
		}
		else if(rf->xmax>x2) {
			if(rf->xmin>x2) {
				rf->xmin-= (x2-x1);
				rf->xmax-= (x2-x1);
			}
			else {
				if(rf->xmin<x1) rf->xmin= x1;
				newrct= stack+ *count;
				(*count)++;

				newrct->xmin= x1;
				newrct->xmax= rf->xmax-(x2-x1);
				newrct->ymin= rf->ymin;
				newrct->ymax= rf->ymax;

				if(newrct->xmin==newrct->xmax) (*count)--;

				rf->xmax= x2;
			}
		}
		rf++;
	}

}

static void clipy_rctf_swap(rctf *stack, short *count, float y1, float y2)
{
	rctf *rf, *newrct;
	short a;

	a= *count;
	rf= stack;
	for(;a>0;a--) {
		if(rf->ymin<y1) {
			if(rf->ymax<y1) {
				rf->ymin+= (y2-y1);
				rf->ymax+= (y2-y1);
			}
			else {
				if(rf->ymax>y2) rf->ymax= y2;
				newrct= stack+ *count;
				(*count)++;

				newrct->ymax= y2;
				newrct->ymin= rf->ymin+(y2-y1);
				newrct->xmin= rf->xmin;
				newrct->xmax= rf->xmax;

				if(newrct->ymin==newrct->ymax) (*count)--;

				rf->ymin= y1;
			}
		}
		else if(rf->ymax>y2) {
			if(rf->ymin>y2) {
				rf->ymin-= (y2-y1);
				rf->ymax-= (y2-y1);
			}
			else {
				if(rf->ymin<y1) rf->ymin= y1;
				newrct= stack+ *count;
				(*count)++;

				newrct->ymin= y1;
				newrct->ymax= rf->ymax-(y2-y1);
				newrct->xmin= rf->xmin;
				newrct->xmax= rf->xmax;

				if(newrct->ymin==newrct->ymax) (*count)--;

				rf->ymax= y2;
			}
		}
		rf++;
	}
}

static float square_rctf(rctf *rf)
{
	float x, y;

	x= rf->xmax- rf->xmin;
	y= rf->ymax- rf->ymin;
	return (x*y);
}

static float clipx_rctf(rctf *rf, float x1, float x2)
{
	float size;

	size= rf->xmax - rf->xmin;

	if(rf->xmin<x1) {
		rf->xmin= x1;
	}
	if(rf->xmax>x2) {
		rf->xmax= x2;
	}
	if(rf->xmin > rf->xmax) {
		rf->xmin = rf->xmax;
		return 0.0;
	}
	else if(size!=0.0) {
		return (rf->xmax - rf->xmin)/size;
	}
	return 1.0;
}

static float clipy_rctf(rctf *rf, float y1, float y2)
{
	float size;

	size= rf->ymax - rf->ymin;

	if(rf->ymin<y1) {
		rf->ymin= y1;
	}
	if(rf->ymax>y2) {
		rf->ymax= y2;
	}

	if(rf->ymin > rf->ymax) {
		rf->ymin = rf->ymax;
		return 0.0;
	}
	else if(size!=0.0) {
		return (rf->ymax - rf->ymin)/size;
	}
	return 1.0;

}

static void boxsampleclip(struct ImBuf *ibuf, rctf *rf, TexResult *texres)
{
	/* sample box, is clipped already, and minx etc. have been set at ibuf size.
       Enlarge with antialiased edges of the pixels */

	float muly, mulx, div, col[4];
	int x, y, startx, endx, starty, endy;

	startx= (int)floor(rf->xmin);
	endx= (int)floor(rf->xmax);
	starty= (int)floor(rf->ymin);
	endy= (int)floor(rf->ymax);

	if(startx < 0) startx= 0;
	if(starty < 0) starty= 0;
	if(endx>=ibuf->x) endx= ibuf->x-1;
	if(endy>=ibuf->y) endy= ibuf->y-1;

	if(starty==endy && startx==endx) {
		ibuf_get_color(&texres->tr, ibuf, startx, starty);
	}
	else {
		div= texres->tr= texres->tg= texres->tb= texres->ta= 0.0;
		for(y=starty; y<=endy; y++) {
			
			muly= 1.0;

			if(starty==endy);
			else {
				if(y==starty) muly= 1.0f-(rf->ymin - y);
				if(y==endy) muly= (rf->ymax - y);
			}
			
			if(startx==endx) {
				mulx= muly;
				
				ibuf_get_color(col, ibuf, startx, y);

				texres->ta+= mulx*col[3];
				texres->tr+= mulx*col[0];
				texres->tg+= mulx*col[1];
				texres->tb+= mulx*col[2];
				div+= mulx;
			}
			else {
				for(x=startx; x<=endx; x++) {
					mulx= muly;
					if(x==startx) mulx*= 1.0f-(rf->xmin - x);
					if(x==endx) mulx*= (rf->xmax - x);

					ibuf_get_color(col, ibuf, x, y);
					
					if(mulx==1.0) {
						texres->ta+= col[3];
						texres->tr+= col[0];
						texres->tg+= col[1];
						texres->tb+= col[2];
						div+= 1.0;
					}
					else {
						texres->ta+= mulx*col[3];
						texres->tr+= mulx*col[0];
						texres->tg+= mulx*col[1];
						texres->tb+= mulx*col[2];
						div+= mulx;
					}
				}
			}
		}
		if(div!=0.0) {
			div= 1.0f/div;
			texres->tb*= div;
			texres->tg*= div;
			texres->tr*= div;
			texres->ta*= div;
		}
		else {
			texres->tr= texres->tg= texres->tb= texres->ta= 0.0f;
		}
	}
}

static void boxsample(ImBuf *ibuf, float minx, float miny, float maxx, float maxy, TexResult *texres)
{
	/* Sample box, performs clip. minx etc are in range 0.0 - 1.0 .
     * Enlarge with antialiased edges of pixels.
     * If global variable 'imaprepeat' has been set, the
     *  clipped-away parts are sampled as well.
     */
	/* note: actually minx etc isnt in the proper range... this due to filter size and offset vectors for bump */
	TexResult texr;
	rctf *rf, stack[8];
	float opp, tot, alphaclip= 1.0;
	short count=1;

	rf= stack;
	rf->xmin= minx*(ibuf->x);
	rf->xmax= maxx*(ibuf->x);
	rf->ymin= miny*(ibuf->y);
	rf->ymax= maxy*(ibuf->y);

	texr.talpha= texres->talpha;	/* is read by boxsample_clip */
	
	if(imapextend) {
		CLAMP(rf->xmin, 0.0f, ibuf->x-1);
		CLAMP(rf->xmax, 0.0f, ibuf->x-1);
	}
	else if(imaprepeat) clipx_rctf_swap(stack, &count, 0.0, (float)(ibuf->x));
	else {
		alphaclip= clipx_rctf(rf, 0.0, (float)(ibuf->x));

		if(alphaclip<=0.0) {
			texres->tr= texres->tb= texres->tg= texres->ta= 0.0;
			return;
		}
	}

	if(imapextend) {
		CLAMP(rf->ymin, 0.0f, ibuf->y-1);
		CLAMP(rf->ymax, 0.0f, ibuf->y-1);
	}
	else if(imaprepeat) clipy_rctf_swap(stack, &count, 0.0, (float)(ibuf->y));
	else {
		alphaclip*= clipy_rctf(rf, 0.0, (float)(ibuf->y));

		if(alphaclip<=0.0) {
			texres->tr= texres->tb= texres->tg= texres->ta= 0.0;
			return;
		}
	}

	if(count>1) {
		tot= texres->tr= texres->tb= texres->tg= texres->ta= 0.0;
		while(count--) {
			boxsampleclip(ibuf, rf, &texr);
			
			opp= square_rctf(rf);
			tot+= opp;

			texres->tr+= opp*texr.tr;
			texres->tg+= opp*texr.tg;
			texres->tb+= opp*texr.tb;
			if(texres->talpha) texres->ta+= opp*texr.ta;
			rf++;
		}
		if(tot!= 0.0) {
			texres->tr/= tot;
			texres->tg/= tot;
			texres->tb/= tot;
			if(texres->talpha) texres->ta/= tot;
		}
	}
	else {
		boxsampleclip(ibuf, rf, texres);
	}

	if(texres->talpha==0) texres->ta= 1.0;
	
	if(alphaclip!=1.0) {
		/* this is for later investigation, premul or not? */
		/* texres->tr*= alphaclip; */
		/* texres->tg*= alphaclip; */
		/* texres->tb*= alphaclip; */
		texres->ta*= alphaclip;
	}
}	

static void makemipmap(Tex *tex, Image *ima)
{
	struct ImBuf *ibuf, *nbuf;
	int minsize, curmap=0;
	
	ibuf= ima->ibuf;
	minsize= MIN2(ibuf->x, ibuf->y);
	
	while(minsize>10 && curmap<BLI_ARRAY_NELEMS(ima->mipmap)) {
		if(tex->imaflag & TEX_GAUSS_MIP) {
			nbuf= IMB_allocImBuf(ibuf->x, ibuf->y, 32, IB_rect, 0);
			IMB_filterN(nbuf, ibuf);
			ima->mipmap[curmap]= (struct ImBuf *)IMB_onehalf(nbuf);
			IMB_freeImBuf(nbuf);
		}
		else {
			ima->mipmap[curmap]= (struct ImBuf *)IMB_onehalf(ibuf);
		}
		ibuf= ima->mipmap[curmap];
		
		curmap++;
		minsize= MIN2(ibuf->x, ibuf->y);
	}
}


int imagewraposa(Tex *tex, Image *ima, float *texvec, float *dxt, float *dyt, TexResult *texres)
{
	TexResult texr;
	ImBuf *ibuf, *previbuf;
	float fx, fy, minx, maxx, miny, maxy, dx, dy;
	float maxd, pixsize, val1, val2, val3;
	int curmap, retval;

	texres->tin= texres->ta= texres->tr= texres->tg= texres->tb= 0.0;
	
	/* we need to set retval OK, otherwise texture code generates normals itself... */
	retval= texres->nor?3:1;
	
	if(ima==NULL || ima->ok== 0) {
		return retval;
	}
	
	if(ima->ibuf==NULL) {
		BLI_lock_thread(LOCK_MALLOC);
		if(ima->ibuf==NULL) ima_ibuf_is_nul(tex, ima);
		BLI_unlock_thread(LOCK_MALLOC);
	}
	
	if (ima->ok) {
	
		if(tex->imaflag & TEX_MIPMAP) {
			if(ima->mipmap[0]==NULL) {
				BLI_lock_thread(LOCK_MALLOC);
				if(ima->mipmap[0]==NULL) makemipmap(tex, ima);
				BLI_unlock_thread(LOCK_MALLOC);
			}
		}
	
		ibuf = ima->ibuf;
		
		if(tex->imaflag & TEX_USEALPHA) {
			if(tex->imaflag & TEX_CALCALPHA);
			else texres->talpha= 1;
		}
		
		texr.talpha= texres->talpha;
		
		if(tex->imaflag & TEX_IMAROT) {
			fy= texvec[0];
			fx= texvec[1];
		}
		else {
			fx= texvec[0];
			fy= texvec[1];
		}
		
		if(ibuf->flags & IB_fields) {
			if(R.r.mode & R_FIELDS) {			/* field render */
				if(R.flag & R_SEC_FIELD) {		/* correction for 2nd field */
					/* fac1= 0.5/( (float)ibuf->y ); */
					/* fy-= fac1; */
				}
				else {				/* first field */
					fy+= 0.5f/( (float)ibuf->y );
				}
			}
		}
		
		/* pixel coordinates */

		minx= MIN3(dxt[0],dyt[0],dxt[0]+dyt[0] );
		maxx= MAX3(dxt[0],dyt[0],dxt[0]+dyt[0] );
		miny= MIN3(dxt[1],dyt[1],dxt[1]+dyt[1] );
		maxy= MAX3(dxt[1],dyt[1],dxt[1]+dyt[1] );

		/* tex_sharper has been removed */
		minx= tex->filtersize*(maxx-minx)/2.0f;
		miny= tex->filtersize*(maxy-miny)/2.0f;
		
		if(tex->filtersize!=1.0f) {
			dxt[0]*= tex->filtersize;
			dxt[1]*= tex->filtersize;
			dyt[0]*= tex->filtersize;
			dyt[1]*= tex->filtersize;
		}

		if(tex->imaflag & TEX_IMAROT) SWAP(float, minx, miny);
		
		if(minx>0.25) minx= 0.25;
		else if(minx<0.00001f) minx= 0.00001f;	/* side faces of unit-cube */
		if(miny>0.25) miny= 0.25;
		else if(miny<0.00001f) miny= 0.00001f;

		
		/* repeat and clip */
		
		/* watch it: imaprepeat is global value (see boxsample) */
		imaprepeat= (tex->extend==TEX_REPEAT);
		imapextend= (tex->extend==TEX_EXTEND);

		if(tex->extend == TEX_CHECKER) {
			int xs, ys, xs1, ys1, xs2, ys2, boundary;
			
			xs= (int)floor(fx);
			ys= (int)floor(fy);
			
			// both checkers available, no boundary exceptions, checkerdist will eat aliasing
			if( (tex->flag & TEX_CHECKER_ODD) && (tex->flag & TEX_CHECKER_EVEN) ) {
				fx-= xs;
				fy-= ys;
			}
			else {
				
				xs1= (int)floor(fx-minx);
				ys1= (int)floor(fy-miny);
				xs2= (int)floor(fx+minx);
				ys2= (int)floor(fy+miny);
				boundary= (xs1!=xs2) || (ys1!=ys2);
	
				if(boundary==0) {
					if( (tex->flag & TEX_CHECKER_ODD)==0) {
						if((xs+ys) & 1); 
						else return retval;
					}
					if( (tex->flag & TEX_CHECKER_EVEN)==0) {
						if((xs+ys) & 1) return retval;
					}
					fx-= xs;
					fy-= ys;
				}
				else {
					if(tex->flag & TEX_CHECKER_ODD) {
						if((xs1+ys) & 1) fx-= xs2;
						else fx-= xs1;
						
						if((ys1+xs) & 1) fy-= ys2;
						else fy-= ys1;
					}
					if(tex->flag & TEX_CHECKER_EVEN) {
						if((xs1+ys) & 1) fx-= xs1;
						else fx-= xs2;
						
						if((ys1+xs) & 1) fy-= ys1;
						else fy-= ys2;
					}
				}
			}

			/* scale around center, (0.5, 0.5) */
			if(tex->checkerdist<1.0) {
				fx= (fx-0.5)/(1.0-tex->checkerdist) +0.5;
				fy= (fy-0.5)/(1.0-tex->checkerdist) +0.5;
				minx/= (1.0-tex->checkerdist);
				miny/= (1.0-tex->checkerdist);
			}
		}

		if(tex->extend == TEX_CLIPCUBE) {
			if(fx+minx<0.0 || fy+miny<0.0 || fx-minx>1.0 || fy-miny>1.0 || texvec[2]<-1.0 || texvec[2]>1.0) {
				return retval;
			}
		}
		else if(tex->extend==TEX_CLIP || tex->extend==TEX_CHECKER) {
			if(fx+minx<0.0 || fy+miny<0.0 || fx-minx>1.0 || fy-miny>1.0) {
				return retval;
			}
		}
		else {
			if(tex->extend==TEX_EXTEND) {
				if(fx>1.0) fx = 1.0;
				else if(fx<0.0) fx= 0.0;
			}
			else {
				if(fx>1.0) fx -= (int)(fx);
				else if(fx<0.0) fx+= 1-(int)(fx);
			}
			
			if(tex->extend==TEX_EXTEND) {
				if(fy>1.0) fy = 1.0;
				else if(fy<0.0) fy= 0.0;
			}
			else {
				if(fy>1.0) fy -= (int)(fy);
				else if(fy<0.0) fy+= 1-(int)(fy);
			}
		}
	
		/* warning no return! */
		if( (R.flag & R_SEC_FIELD) && (ibuf->flags & IB_fields) ) {
			ibuf->rect+= (ibuf->x*ibuf->y);
		}

		/* choice:  */
		if(tex->imaflag & TEX_MIPMAP) {
			float bumpscale;
			
			dx= minx;
			dy= miny;
			maxd= MAX2(dx, dy);
			if(maxd>0.5) maxd= 0.5;

			pixsize = 1.0f/ (float) MIN2(ibuf->x, ibuf->y);
			
			bumpscale= pixsize/maxd;
			if(bumpscale>1.0f) bumpscale= 1.0f;
			else bumpscale*=bumpscale;
			
			curmap= 0;
			previbuf= ibuf;
			while(curmap<BLI_ARRAY_NELEMS(ima->mipmap) && ima->mipmap[curmap]) {
				if(maxd < pixsize) break;
				previbuf= ibuf;
				ibuf= ima->mipmap[curmap];
				pixsize= 1.0f / (float)MIN2(ibuf->x, ibuf->y); /* this used to be 1.0 */		
				curmap++;
			}

			if(previbuf!=ibuf || (tex->imaflag & TEX_INTERPOL)) {
				/* sample at least 1 pixel */
				if (minx < 0.5f / ima->ibuf->x) minx = 0.5f / ima->ibuf->x;
				if (miny < 0.5f / ima->ibuf->y) miny = 0.5f / ima->ibuf->y;
			}
			
			if(texres->nor && (tex->imaflag & TEX_NORMALMAP)==0) {
				/* a bit extra filter */
				//minx*= 1.35f;
				//miny*= 1.35f;
				
				boxsample(ibuf, fx-minx, fy-miny, fx+minx, fy+miny, texres);
				val1= texres->tr+texres->tg+texres->tb;
				boxsample(ibuf, fx-minx+dxt[0], fy-miny+dxt[1], fx+minx+dxt[0], fy+miny+dxt[1], &texr);
				val2= texr.tr + texr.tg + texr.tb;
				boxsample(ibuf, fx-minx+dyt[0], fy-miny+dyt[1], fx+minx+dyt[0], fy+miny+dyt[1], &texr);
				val3= texr.tr + texr.tg + texr.tb;
	
				/* don't switch x or y! */
				texres->nor[0]= (val1-val2);
				texres->nor[1]= (val1-val3);
				
				if(previbuf!=ibuf) {  /* interpolate */
					
					boxsample(previbuf, fx-minx, fy-miny, fx+minx, fy+miny, &texr);
					
					/* calc rgb */
					dx= 2.0f*(pixsize-maxd)/pixsize;
					if(dx>=1.0f) {
						texres->ta= texr.ta; texres->tb= texr.tb;
						texres->tg= texr.tg; texres->tr= texr.tr;
					}
					else {
						dy= 1.0f-dx;
						texres->tb= dy*texres->tb+ dx*texr.tb;
						texres->tg= dy*texres->tg+ dx*texr.tg;
						texres->tr= dy*texres->tr+ dx*texr.tr;
						texres->ta= dy*texres->ta+ dx*texr.ta;
					}
					
					val1= dy*val1+ dx*(texr.tr + texr.tg + texr.tb);
					boxsample(previbuf, fx-minx+dxt[0], fy-miny+dxt[1], fx+minx+dxt[0], fy+miny+dxt[1], &texr);
					val2= dy*val2+ dx*(texr.tr + texr.tg + texr.tb);
					boxsample(previbuf, fx-minx+dyt[0], fy-miny+dyt[1], fx+minx+dyt[0], fy+miny+dyt[1], &texr);
					val3= dy*val3+ dx*(texr.tr + texr.tg + texr.tb);
					
					texres->nor[0]= (val1-val2);	/* vals have been interpolated above! */
					texres->nor[1]= (val1-val3);
					
					if(dx<1.0f) {
						dy= 1.0f-dx;
						texres->tb= dy*texres->tb+ dx*texr.tb;
						texres->tg= dy*texres->tg+ dx*texr.tg;
						texres->tr= dy*texres->tr+ dx*texr.tr;
						texres->ta= dy*texres->ta+ dx*texr.ta;
					}
				}
				texres->nor[0]*= bumpscale;
				texres->nor[1]*= bumpscale;
			}
			else {
				maxx= fx+minx;
				minx= fx-minx;
				maxy= fy+miny;
				miny= fy-miny;
	
				boxsample(ibuf, minx, miny, maxx, maxy, texres);
	
				if(previbuf!=ibuf) {  /* interpolate */
					boxsample(previbuf, minx, miny, maxx, maxy, &texr);
					
					fx= 2.0f*(pixsize-maxd)/pixsize;
					
					if(fx>=1.0) {
						texres->ta= texr.ta; texres->tb= texr.tb;
						texres->tg= texr.tg; texres->tr= texr.tr;
					} else {
						fy= 1.0f-fx;
						texres->tb= fy*texres->tb+ fx*texr.tb;
						texres->tg= fy*texres->tg+ fx*texr.tg;
						texres->tr= fy*texres->tr+ fx*texr.tr;
						texres->ta= fy*texres->ta+ fx*texr.ta;
					}
				}
			}
		}
		else {
			if((tex->imaflag & TEX_INTERPOL)) {
				/* sample 1 pixel minimum */
				if (minx < 0.5f / ima->ibuf->x) minx = 0.5f / ima->ibuf->x;
				if (miny < 0.5f / ima->ibuf->y) miny = 0.5f / ima->ibuf->y;
			}

			if(texres->nor && (tex->imaflag & TEX_NORMALMAP)==0) {
				
				/* a bit extra filter */
				//minx*= 1.35f;
				//miny*= 1.35f;
				
				boxsample(ibuf, fx-minx, fy-miny, fx+minx, fy+miny, texres);
				val1= texres->tr+texres->tg+texres->tb;
				boxsample(ibuf, fx-minx+dxt[0], fy-miny+dxt[1], fx+minx+dxt[0], fy+miny+dxt[1], &texr);
				val2= texr.tr + texr.tg + texr.tb;
				boxsample(ibuf, fx-minx+dyt[0], fy-miny+dyt[1], fx+minx+dyt[0], fy+miny+dyt[1], &texr);
				val3= texr.tr + texr.tg + texr.tb;
				/* don't switch x or y! */
				texres->nor[0]= (val1-val2);
				texres->nor[1]= (val1-val3);
			}
			else {
				boxsample(ibuf, fx-minx, fy-miny, fx+minx, fy+miny, texres);
			}
		}
		
		BRICONTRGB;
		
		if(tex->imaflag & TEX_CALCALPHA) {
			texres->ta= texres->tin= texres->ta*MAX3(texres->tr, texres->tg, texres->tb);
		}
		else texres->tin= texres->ta;

		if(tex->flag & TEX_NEGALPHA) texres->ta= 1.0f-texres->ta;
		
		if( (R.flag & R_SEC_FIELD) && (ibuf->flags & IB_fields) ) {
			ibuf->rect-= (ibuf->x*ibuf->y);
		}

		if(texres->nor && (tex->imaflag & TEX_NORMALMAP)) {
			texres->nor[0]= 0.5-texres->tr;
			texres->nor[1]= 0.5-texres->tg;
			texres->nor[2]= -texres->tb;
		}
	}
	else {
		texres->tin= 0.0f;
	}
	
	return retval;
}
