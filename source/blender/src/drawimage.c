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

#include <math.h>
#include <string.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef WIN32
#include <io.h>
#include "BLI_winstuff.h"
#else
#include <unistd.h>
#endif   
#include "MEM_guardedalloc.h"

#include "BLI_blenlib.h"

#include "IMB_imbuf_types.h"

#include "DNA_image_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_packedFile_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"

#include "BKE_utildefines.h"
#include "BKE_global.h"
#include "BKE_mesh.h"
#include "BKE_image.h"

#include "BDR_editface.h"
#include "BDR_editobject.h"
#include "BDR_drawmesh.h"

#include "BIF_gl.h"
#include "BIF_space.h"
#include "BIF_screen.h"
#include "BIF_mywindow.h"
#include "BIF_drawimage.h"
#include "BIF_resources.h"
#include "BIF_interface.h"
#include "BIF_editsima.h"

/* Modules used */
#include "mydevice.h"
#include "blendef.h"
#include "render.h"
#include "butspace.h"  // event codes


void rectwrite_part(int winxmin, int winymin, int winxmax, int winymax, int x1, int y1, int xim, int yim, float zoomx, float zoomy, unsigned int *rect)
{
	int cx, cy, oldxim, x2, y2;
	
	oldxim= xim;
		
	/* coordinates how its drawn at the screen */
	x2= x1+ zoomx*xim;
	y2= y1+ zoomy*yim;

	/* partial clip */
	if(x1<winxmin) {
		/* with OpenGL, rects are not allowed to start outside of the left/bottom window edge */
		cx= winxmin-x1+(int)zoomx;
		/* make sure the rect will be drawn pixel-exact */
		cx/= zoomx;
		cx++;
		x1+= zoomx*cx;
		xim-= cx;
		rect+= cx;
	}
	if(y1<winymin) {
		cy= winymin-y1+(int)zoomy;
		cy/= zoomy;
		cy++;
		y1+= zoomy*cy;
		rect+= cy*oldxim;
		yim-= cy;
	}
	if(x2>=winxmax) {
		cx= x2-winxmax;
		cx/= zoomx;
		xim-= cx+3;
	}
	if(y2>=winymax) {
		cy= y2-winymax;
		cy/= zoomy;
		yim-= cy+3;
	}
	
	if(xim<=0) return;
	if(yim<=0) return;

	mywinset(G.curscreen->mainwin);
	glScissor(winxmin, winymin, winxmax-winxmin+1, winymax-winymin+1);
	
	glPixelStorei(GL_UNPACK_ROW_LENGTH,  oldxim);
	
	glPixelZoom(zoomx,  zoomy);

	glRasterPos2i(x1, y1);
	glDrawPixels(xim, yim, GL_RGBA, GL_UNSIGNED_BYTE,  rect);

	glPixelZoom(1.0,  1.0);

	glPixelStorei(GL_UNPACK_ROW_LENGTH,  0);
	
	mywinset(curarea->win);
}

/**
 * Sets up the fields of the View2D member of the SpaceImage struct
 * This routine can be called in two modes:
 * mode == 'f': float mode ???
 * mode == 'p': pixel mode ???
 *
 * @param     sima  the image space to update
 * @param     mode  the mode to use for the update
 * @return    void
 *   
 */
void calc_image_view(SpaceImage *sima, char mode)
{
	float xim=256, yim=256;
	float x1, y1;
	float zoom;
	
	if(sima->image && sima->image->ibuf) {
		xim= sima->image->ibuf->x;
		yim= sima->image->ibuf->y;
	}
	
	sima->v2d.tot.xmin= 0;
	sima->v2d.tot.ymin= 0;
	sima->v2d.tot.xmax= xim;
	sima->v2d.tot.ymax= yim;
	
	sima->v2d.mask.xmin= sima->v2d.mask.ymin= 0;
	sima->v2d.mask.xmax= curarea->winx;
	sima->v2d.mask.ymax= curarea->winy;


	/* Which part of the image space do we see? */
	/* Same calculation as in lrectwrite: area left and down*/
	x1= curarea->winrct.xmin+(curarea->winx-sima->zoom*xim)/2;
	y1= curarea->winrct.ymin+(curarea->winy-sima->zoom*yim)/2;

	x1-= sima->zoom*sima->xof;
	y1-= sima->zoom*sima->yof;

	/* float! */
	zoom= sima->zoom;
	
	/* relative display right */
	sima->v2d.cur.xmin= ((curarea->winrct.xmin - (float)x1)/zoom);
	sima->v2d.cur.xmax= sima->v2d.cur.xmin + ((float)curarea->winx/zoom);
	
	/* relative display left */
	sima->v2d.cur.ymin= ((curarea->winrct.ymin-(float)y1)/zoom);
	sima->v2d.cur.ymax= sima->v2d.cur.ymin + ((float)curarea->winy/zoom);
	
	if(mode=='f') {		
		sima->v2d.cur.xmin/= xim;
		sima->v2d.cur.xmax/= xim;
		sima->v2d.cur.ymin/= yim;
		sima->v2d.cur.ymax/= yim;
	}
}

void what_image(SpaceImage *sima)
{
	extern TFace *lasttface;	/* editface.c */
	Mesh *me;
		
	if(sima->mode==SI_TEXTURE) {
		if(G.f & G_FACESELECT) {

			sima->image= 0;
			me= get_mesh((G.scene->basact) ? (G.scene->basact->object) : 0);
			set_lasttface();
			
			if(me && me->tface && lasttface && lasttface->mode & TF_TEX) {
				sima->image= lasttface->tpage;
					
				if(sima->flag & SI_EDITTILE);
				else sima->curtile= lasttface->tile;
				
				if(sima->image) {
					if(lasttface->mode & TF_TILES)
						sima->image->tpageflag |= IMA_TILES;
					else sima->image->tpageflag &= ~IMA_TILES;
				}
			}
		}
	}
}

void image_changed(SpaceImage *sima, int dotile)
{
	TFace *tface;
	Mesh *me;
	int a;
	
	if(sima->mode==SI_TEXTURE) {
		
		if(G.f & G_FACESELECT) {
			me= get_mesh((G.scene->basact) ? (G.scene->basact->object) : 0);
			if(me && me->tface) {
				tface= me->tface;
				a= me->totface;
				while(a--) {
					if(tface->flag & TF_SELECT) {
						
						if(dotile==2) {
							tface->mode &= ~TF_TILES;
						}
						else {
							tface->tpage= sima->image;
							tface->mode |= TF_TEX;
						
							if(dotile) tface->tile= sima->curtile;
						}
						
						if(sima->image) {
							if(sima->image->tpageflag & IMA_TILES) tface->mode |= TF_TILES;
							else tface->mode &= ~TF_TILES;
						
							if(sima->image->id.us==0) sima->image->id.us= 1;
						}
					}
					tface++;
				}
				allqueue(REDRAWVIEW3D, 0);
				allqueue(REDRAWBUTSEDIT, 0);
			}
		}
	}
}


void uvco_to_areaco(float *vec, short *mval)
{
	float x, y;

	mval[0]= 3200;
	
	x= (vec[0] - G.v2d->cur.xmin)/(G.v2d->cur.xmax-G.v2d->cur.xmin);
	y= (vec[1] - G.v2d->cur.ymin)/(G.v2d->cur.ymax-G.v2d->cur.ymin);

	if(x>=0.0 && x<=1.0) {
		if(y>=0.0 && y<=1.0) {		
			mval[0]= G.v2d->mask.xmin + x*(G.v2d->mask.xmax-G.v2d->mask.xmin);
			mval[1]= G.v2d->mask.ymin + y*(G.v2d->mask.ymax-G.v2d->mask.ymin);
		}
	}
}

void uvco_to_areaco_noclip(float *vec, short *mval)
{
	float x, y;

	mval[0]= 3200;
	
	x= (vec[0] - G.v2d->cur.xmin)/(G.v2d->cur.xmax-G.v2d->cur.xmin);
	y= (vec[1] - G.v2d->cur.ymin)/(G.v2d->cur.ymax-G.v2d->cur.ymin);

	x= G.v2d->mask.xmin + x*(G.v2d->mask.xmax-G.v2d->mask.xmin);
	y= G.v2d->mask.ymin + y*(G.v2d->mask.ymax-G.v2d->mask.ymin);
	
	mval[0]= x;
	mval[1]= y;
}

void draw_tfaces(void)
{
	TFace *tface,*activetface = NULL;
	MFace *mface,*activemface = NULL;
	Mesh *me;
	int a;
	char col1[4], col2[4];
 	
 	glPointSize(BIF_GetThemeValuef(TH_VERTEX_SIZE));

	if(G.f & G_FACESELECT) {
		me= get_mesh((G.scene->basact) ? (G.scene->basact->object) : 0);
		if(me && me->tface) {
			calc_image_view(G.sima, 'f');	/* float */
			myortho2(G.v2d->cur.xmin, G.v2d->cur.xmax, G.v2d->cur.ymin, G.v2d->cur.ymax);
			glLoadIdentity();
			
			/* draw shadow mesh */
			if(G.sima->flag & SI_DRAWSHADOW){		
				tface= me->tface;
				mface= me->mface;
				a= me->totface;			
				while(a--) {
					if(tface->flag & TF_HIDE);
					else if(mface->v3) {
						cpack(0x707070);
						glBegin(GL_LINE_LOOP);
						glVertex2fv(tface->uv[0]);
						glVertex2fv(tface->uv[1]);
						glVertex2fv(tface->uv[2]);
						if(mface->v4) glVertex2fv(tface->uv[3]);
						glEnd();
					} 
					tface++;
					mface++;					
				}
			}
			
			/* draw transparent faces */
			if(G.f & G_DRAWFACES) {
				BIF_GetThemeColor4ubv(TH_FACE, col1);
				BIF_GetThemeColor4ubv(TH_FACE_SELECT, col2);
				glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
				glEnable(GL_BLEND);
				tface= me->tface;
				mface= me->mface;
				a= me->totface;			
				while(a--) {
					if(mface->v3 && (tface->flag & TF_SELECT)) {
						if(!(~tface->flag & (TF_SEL1|TF_SEL2|TF_SEL3)) &&
						   (!mface->v4 || tface->flag & TF_SEL4))
							glColor4ubv(col2);
						else
							glColor4ubv(col1);
							
						glBegin(mface->v4?GL_QUADS:GL_TRIANGLES);
							glVertex2fv(tface->uv[0]);
							glVertex2fv(tface->uv[1]);
							glVertex2fv(tface->uv[2]);
							if(mface->v4) glVertex2fv(tface->uv[3]);
						glEnd();
					}
					tface++;
					mface++;					
				}
				glDisable(GL_BLEND);
			}


			tface= me->tface;
			mface= me->mface;
			a= me->totface;
			while(a--) {
				if(mface->v3 && (tface->flag & TF_SELECT) ) {
					if(tface->flag & TF_ACTIVE){
						activetface= tface; 
						activemface= mface; 
					}

					cpack(0x0);
 					glBegin(GL_LINE_LOOP);
						glVertex2fv(tface->uv[0]);
						glVertex2fv(tface->uv[1]);
						glVertex2fv(tface->uv[2]);
						if(mface->v4) glVertex2fv(tface->uv[3]);
					glEnd();
				
					setlinestyle(2);
					cpack(0xFFFFFF);
					glBegin(GL_LINE_STRIP);
						glVertex2fv(tface->uv[0]);
						glVertex2fv(tface->uv[1]);
					glEnd();

					glBegin(GL_LINE_STRIP);
						glVertex2fv(tface->uv[0]);
						if(mface->v4) glVertex2fv(tface->uv[3]);
						else glVertex2fv(tface->uv[2]);
					glEnd();
	
					glBegin(GL_LINE_STRIP);
						glVertex2fv(tface->uv[1]);
						glVertex2fv(tface->uv[2]);
						if(mface->v4) glVertex2fv(tface->uv[3]);
					glEnd();
					setlinestyle(0);
				}
					
				tface++;
				mface++;
			}

			/* draw active face edges */
			if (activetface){
				/* colors: R=u G=v */

				setlinestyle(2);
				tface=activetface; 
				mface=activemface; 

				cpack(0x0);
				glBegin(GL_LINE_LOOP);
				glVertex2fv(tface->uv[0]);
					glVertex2fv(tface->uv[1]);
					glVertex2fv(tface->uv[2]);
					if(mface->v4) glVertex2fv(tface->uv[3]);
				glEnd();
					
				cpack(0xFF00);
				glBegin(GL_LINE_STRIP);
					glVertex2fv(tface->uv[0]);
					glVertex2fv(tface->uv[1]);
				glEnd();

				cpack(0xFF);
				glBegin(GL_LINE_STRIP);
					glVertex2fv(tface->uv[0]);
					if(mface->v4) glVertex2fv(tface->uv[3]);
					else glVertex2fv(tface->uv[2]);
				glEnd();

				cpack(0xFFFFFF);
				glBegin(GL_LINE_STRIP);
					glVertex2fv(tface->uv[1]);
					glVertex2fv(tface->uv[2]);
					if(mface->v4) glVertex2fv(tface->uv[3]);
				glEnd();
 				
				setlinestyle(0);
			}

            /* to make sure vertices markers are visible, draw them last */
			/* we draw selected over unselected, so two loops */
			BIF_GetThemeColor3ubv(TH_VERTEX, col1);
			glColor4ubv(col1);
			tface= me->tface;
			mface= me->mface;
			a= me->totface;
			while(a--) {
				if(mface->v3  && (tface->flag & TF_SELECT) ) {
					glBegin(GL_POINTS);
					
					if(tface->flag & TF_SEL1); else glVertex2fv(tface->uv[0]);
					if(tface->flag & TF_SEL2); else glVertex2fv(tface->uv[1]);
					if(tface->flag & TF_SEL3); else glVertex2fv(tface->uv[2]);
					if(mface->v4) {
						if(tface->flag & TF_SEL4); else glVertex2fv(tface->uv[3]);
					}
					glEnd();
				}
				tface++;
				mface++;
			}
			/* selected */
			BIF_GetThemeColor3ubv(TH_VERTEX_SELECT, col2);
			glColor4ubv(col2);
			tface= me->tface;
			mface= me->mface;
			a= me->totface;
			while(a--) {
				if(mface->v3  && (tface->flag & TF_SELECT) ) {
					glBegin(GL_POINTS);
					
					if(tface->flag & TF_SEL1) glVertex2fv(tface->uv[0]);
					if(tface->flag & TF_SEL2) glVertex2fv(tface->uv[1]);
					if(tface->flag & TF_SEL3) glVertex2fv(tface->uv[2]);
					if(mface->v4) {
						if(tface->flag & TF_SEL4) glVertex2fv(tface->uv[3]);
					}
					glEnd();
				}
				tface++;
				mface++;
			}
		}
	}
	glPointSize(1.0);
}

static unsigned int *get_part_from_ibuf(ImBuf *ibuf, short startx, short starty, short endx, short endy)
{
	unsigned int *rt, *rp, *rectmain;
	short y, heigth, len;

	/* the right offset in rectot */

	rt= ibuf->rect+ (starty*ibuf->x+ startx);

	len= (endx-startx);
	heigth= (endy-starty);

	rp=rectmain= MEM_mallocN(heigth*len*sizeof(int), "rect");
	
	for(y=0; y<heigth; y++) {
		memcpy(rp, rt, len*4);
		rt+= ibuf->x;
		rp+= len;
	}
	return rectmain;
}

static void draw_image_prop_circle(ImBuf *ibuf)
{
	float aspx, aspy;
	extern float prop_cent[3];

	if(G.moving && G.f & G_PROPORTIONAL) {

		if(ibuf==0 || ibuf->rect==0 || ibuf->x==0 || ibuf->y==0) {
			aspx= aspy= 1.0;
		}
		else {
			aspx= 256.0/ibuf->x;
			aspy= 256.0/ibuf->y;
		}

		/* scale and translate the circle into place and draw it */
		glPushMatrix();
		glScalef(aspx, aspy, 1.0);
		glTranslatef((1/aspx)*prop_cent[0] - prop_cent[0],
		             (1/aspy)*prop_cent[1] - prop_cent[1], 0.0);
		draw_prop_circle();
		glPopMatrix();
	}
}

static void draw_image_view_icon(void)
{
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); 
	
	glRasterPos2f(5.0, 5.0);

	if(G.sima->flag & SI_STICKYUVS) {
		BIF_draw_icon(ICON_STICKY2_UVS);
		glRasterPos2f(25.0, 5.0);
	}
	else if(G.sima->flag & SI_LOCALSTICKY) {
		BIF_draw_icon(ICON_STICKY_UVS);
		glRasterPos2f(25.0, 5.0);
	}

	if(G.sima->flag & SI_SELACTFACE) {
			BIF_draw_icon(ICON_DRAW_UVFACES);
	}
	
	glBlendFunc(GL_ONE,  GL_ZERO); 
	glDisable(GL_BLEND);
}

/* ************ panel stuff ************* */

// button define is local, only events defined here possible
#define B_TRANS_IMAGE	1

/* is used for both read and write... */
static void image_editvertex_buts(uiBlock *block)
{
	static float ocent[2];
	float cent[2]= {0.0, 0.0};
	int imx, imy;
	int i, nactive= 0;
	Mesh *me;
	
	if( is_uv_tface_editing_allowed_silent()==0 ) return;
	me= get_mesh(OBACT);
	
	if (G.sima->image && G.sima->image->ibuf) {
		imx= G.sima->image->ibuf->x;
		imy= G.sima->image->ibuf->y;
	} else
		imx= imy= 256;
	
	for (i=0; i<me->totface; i++) {
		MFace *mf= &((MFace*) me->mface)[i];
		TFace *tf= &((TFace*) me->tface)[i];
		
		if (!mf->v3 || !(tf->flag & TF_SELECT))
			continue;
		
		if (tf->flag & TF_SEL1) {
			cent[0]+= tf->uv[0][0];
			cent[1]+= tf->uv[0][1];
			nactive++;
		}
		if (tf->flag & TF_SEL2) {
			cent[0]+= tf->uv[1][0];
			cent[1]+= tf->uv[1][1];
			nactive++;
		}
		if (tf->flag & TF_SEL3) {
			cent[0]+= tf->uv[2][0];
			cent[1]+= tf->uv[2][1];
			nactive++;
		}
		if (mf->v4 && (tf->flag & TF_SEL4)) {
			cent[0]+= tf->uv[3][0];
			cent[1]+= tf->uv[3][1];
			nactive++;
		}
	}
		
	if(block) {	// do the buttons
		if (nactive) {
			ocent[0]= (cent[0]*imx)/nactive;
			ocent[1]= (cent[1]*imy)/nactive;
			
			uiDefBut(block, LABEL, 0, "UV Vertex:",10,55,302,19,0,0,0,0,0,"");
			if(nactive==1) {
				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Vertex X:",	10, 35, 290, 19, &ocent[0], -10*imx, 10.0*imx, 100, 0, "");
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Vertex Y:",	10, 15, 290, 19, &ocent[1], -10*imy, 10.0*imy, 100, 0, "");
				uiBlockEndAlign(block);
			}
			else {
				uiBlockBeginAlign(block);
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Median X:",	10, 35, 290, 19, &ocent[0], -10*imx, 10.0*imx, 100, 0, "");
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Median Y:",	10, 15, 290, 19, &ocent[1], -10*imy, 10.0*imy, 100, 0, "");
				uiBlockEndAlign(block);
			}
		}
	}
	else {	// apply event
		float delta[2];
		
		cent[0]= (cent[0]*imx)/nactive;
		cent[1]= (cent[1]*imy)/nactive;
			
		delta[0]= (ocent[0]-cent[0])/imx;
		delta[1]= (ocent[1]-cent[1])/imy;

		for (i=0; i<me->totface; i++) {
			MFace *mf= &((MFace*) me->mface)[i];
			TFace *tf= &((TFace*) me->tface)[i];
		
			if (!mf->v3 || !(tf->flag & TF_SELECT))
				continue;
		
			if (tf->flag & TF_SEL1) {
				tf->uv[0][0]+= delta[0];
				tf->uv[0][1]+= delta[1];
			}
			if (tf->flag & TF_SEL2) {
				tf->uv[1][0]+= delta[0];
				tf->uv[1][1]+= delta[1];
			}
			if (tf->flag & TF_SEL3) {
				tf->uv[2][0]+= delta[0];
				tf->uv[2][1]+= delta[1];
			}
			if (mf->v4 && (tf->flag & TF_SEL4)) {
				tf->uv[3][0]+= delta[0];
				tf->uv[3][1]+= delta[1];
			}
		}
			
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWIMAGE, 0);
	}
}


void do_imagebuts(unsigned short event)
{
	switch(event) {
	case B_TRANS_IMAGE:
		image_editvertex_buts(NULL);
		break;

	case B_SIMAGEDRAW:
		if(G.f & G_FACESELECT) {
			make_repbind(G.sima->image);
			image_changed(G.sima, 1);
		}
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWIMAGE, 0);
		break;

	case B_SIMAGEDRAW1:
		image_changed(G.sima, 2);		/* 2: only tileflag */
		allqueue(REDRAWVIEW3D, 0);
		allqueue(REDRAWIMAGE, 0);
		break;
		
	case B_TWINANIM:
		{
			Image *ima;
			int nr;

			ima = G.sima->image;
			if (ima) {
				if(ima->flag & IMA_TWINANIM) {
					nr= ima->xrep*ima->yrep;
					if(ima->twsta>=nr) ima->twsta= 1;
					if(ima->twend>=nr) ima->twend= nr-1;
					if(ima->twsta>ima->twend) ima->twsta= 1;
					allqueue(REDRAWIMAGE, 0);
				}
			}
		}
		break;
	}
}

static void image_panel_properties(short cntrl)	// IMAGE_HANDLER_PROPERTIES
{
	uiBlock *block;

	block= uiNewBlock(&curarea->uiblocks, "image_panel_properties", UI_EMBOSS, UI_HELV, curarea->win);
	uiPanelControl(UI_PNL_SOLID | UI_PNL_CLOSE | cntrl);
	uiSetPanelHandler(IMAGE_HANDLER_PROPERTIES);  // for close and esc
	if(uiNewPanel(curarea, block, "Properties", "Image", 10, 230, 318, 204)==0)
		return;

	if (G.sima->image && G.sima->image->ibuf) {
		char str[32];

		sprintf(str, "Image: size %d x %d", G.sima->image->ibuf->x, G.sima->image->ibuf->y);
		uiDefBut(block, LABEL, 0, str,		10,180,300,19, 0, 0, 0, 0, 0, "");

		uiBlockBeginAlign(block);
		uiDefButS(block, TOG|BIT|1, B_TWINANIM, "Anim", 10,150,140,19, &G.sima->image->tpageflag, 0, 0, 0, 0, "Toggles use of animated texture");
		uiDefButS(block, NUM, B_TWINANIM, "Start:",		10,130,140,19, &G.sima->image->twsta, 0.0, 128.0, 0, 0, "Displays the start frame of an animated texture");
		uiDefButS(block, NUM, B_TWINANIM, "End:",		10,110,140,19, &G.sima->image->twend, 0.0, 128.0, 0, 0, "Displays the end frame of an animated texture");
		uiDefButS(block, NUM, 0, "Speed", 				10,90,140,19, &G.sima->image->animspeed, 1.0, 100.0, 0, 0, "Displays Speed of the animation in frames per second");
		uiBlockEndAlign(block);

		uiBlockBeginAlign(block);
		uiDefButS(block, TOG|BIT|0, B_SIMAGEDRAW1, "Tiles",	160,150,140,19, &G.sima->image->tpageflag, 0, 0, 0, 0, "Toggles use of tilemode for faces");
		uiDefButS(block, NUM, B_SIMAGEDRAW, "X:",		160,130,70,19, &G.sima->image->xrep, 1.0, 16.0, 0, 0, "Sets the degree of repetition in the X direction");
		uiDefButS(block, NUM, B_SIMAGEDRAW, "Y:",		230,130,70,19, &G.sima->image->yrep, 1.0, 16.0, 0, 0, "Sets the degree of repetition in the Y direction");
		uiBlockBeginAlign(block);
	}

	image_editvertex_buts(block);
}

static void image_blockhandlers(ScrArea *sa)
{
	SpaceImage *sima= sa->spacedata.first;
	short a;

	/* warning; blocks need to be freed each time, handlers dont remove  */
	uiFreeBlocksWin(&sa->uiblocks, sa->win);
	
	for(a=0; a<SPACE_MAXHANDLER; a+=2) {
		switch(sima->blockhandler[a]) {

		case IMAGE_HANDLER_PROPERTIES:
			image_panel_properties(sima->blockhandler[a+1]);
			break;
		
		}
		/* clear action value for event */
		sima->blockhandler[a+1]= 0;
	}
	uiDrawBlocksPanels(sa, 0);
}



void drawimagespace(ScrArea *sa, void *spacedata)
{
	ImBuf *ibuf= NULL;
	float col[3];
	unsigned int *rect;
	int x1, y1, xmin, xmax, ymin, ymax;
	short sx, sy, dx, dy;
	
	BIF_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	bwin_clear_viewmat(sa->win);	/* clear buttons view */
	glLoadIdentity();
	
	xmin= curarea->winrct.xmin; xmax= curarea->winrct.xmax;
	ymin= curarea->winrct.ymin; ymax= curarea->winrct.ymax;
	
	what_image(G.sima);
	
	if(G.sima->image) {
	
		if(G.sima->image->ibuf==0) {
			load_image(G.sima->image, IB_rect, G.sce, G.scene->r.cfra);
		}	
		ibuf= G.sima->image->ibuf;
	}
	
	if(ibuf==0 || ibuf->rect==0) {
		calc_image_view(G.sima, 'f');
		myortho2(G.v2d->cur.xmin, G.v2d->cur.xmax, G.v2d->cur.ymin, G.v2d->cur.ymax);
		cpack(0x404040);
		glRectf(0.0, 0.0, 1.0, 1.0);
		draw_tfaces();
	}
	else {
		/* calc location */
		x1= xmin+(curarea->winx-G.sima->zoom*ibuf->x)/2;
		y1= ymin+(curarea->winy-G.sima->zoom*ibuf->y)/2;
	
		x1-= G.sima->zoom*G.sima->xof;
		y1-= G.sima->zoom*G.sima->yof;
	
		
		if(G.sima->flag & SI_EDITTILE) {
			rectwrite_part(xmin, ymin, xmax, ymax, x1, y1, ibuf->x, ibuf->y, (float)G.sima->zoom, (float)G.sima->zoom, ibuf->rect);
			
			dx= ibuf->x/G.sima->image->xrep;
			dy= ibuf->y/G.sima->image->yrep;
			sy= (G.sima->curtile / G.sima->image->xrep);
			sx= G.sima->curtile - sy*G.sima->image->xrep;
	
			sx*= dx;
			sy*= dy;
			
			calc_image_view(G.sima, 'p');	/* pixel */
			myortho2(G.v2d->cur.xmin, G.v2d->cur.xmax, G.v2d->cur.ymin, G.v2d->cur.ymax);
			
			cpack(0x0);
			glPolygonMode(GL_FRONT_AND_BACK, GL_LINE); glRects(sx,  sy,  sx+dx-1,  sy+dy-1); glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
			cpack(0xFFFFFF);
			glPolygonMode(GL_FRONT_AND_BACK, GL_LINE); glRects(sx+1,  sy+1,  sx+dx,  sy+dy); glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
		}
		else if(G.sima->mode==SI_TEXTURE) {
			if(G.sima->image->tpageflag & IMA_TILES) {
				
				
				/* just leave this a while */
				if(G.sima->image->xrep<1) return;
				if(G.sima->image->yrep<1) return;
				
				if(G.sima->curtile >= G.sima->image->xrep*G.sima->image->yrep) 
					G.sima->curtile = G.sima->image->xrep*G.sima->image->yrep - 1; 
				
				dx= ibuf->x/G.sima->image->xrep;
				dy= ibuf->y/G.sima->image->yrep;
				
				sy= (G.sima->curtile / G.sima->image->xrep);
				sx= G.sima->curtile - sy*G.sima->image->xrep;
		
				sx*= dx;
				sy*= dy;
				
				rect= get_part_from_ibuf(ibuf, sx, sy, sx+dx, sy+dy);
				
				/* rect= ibuf->rect; */
				for(sy= 0; sy+dy<=ibuf->y; sy+= dy) {
					for(sx= 0; sx+dx<=ibuf->x; sx+= dx) {
						
						rectwrite_part(xmin, ymin, xmax, ymax, 
							x1+sx*G.sima->zoom, y1+sy*G.sima->zoom, dx, dy, (float)G.sima->zoom, (float)G.sima->zoom, rect);
					}
				}
				
				MEM_freeN(rect);
			}
			else 
				rectwrite_part(xmin, ymin, xmax, ymax, x1, y1, ibuf->x, ibuf->y, (float)G.sima->zoom,(float)G.sima->zoom, ibuf->rect);
		
			draw_tfaces();
		}
	
		calc_image_view(G.sima, 'f');	/* float */
	}

	draw_image_prop_circle(ibuf);

	myortho2(-0.375, sa->winx-0.375, -0.375, sa->winy-0.375);
	draw_image_view_icon();
	draw_area_emboss(sa);

	/* it is important to end a view in a transform compatible with buttons */
	bwin_scalematrix(sa->win, G.sima->blockscale, G.sima->blockscale, G.sima->blockscale);
	image_blockhandlers(sa);

	curarea->win_swap= WIN_BACK_OK;
}

void image_viewmove(void)
{
	short mval[2], mvalo[2], xof, yof;
	
	getmouseco_sc(mvalo);
	
	while(get_mbut()&(L_MOUSE|M_MOUSE)) {

		getmouseco_sc(mval);
		
		xof= (mvalo[0]-mval[0])/G.sima->zoom;
		yof= (mvalo[1]-mval[1])/G.sima->zoom;
		
		if(xof || yof) {
			
			G.sima->xof+= xof;
			G.sima->yof+= yof;
			
			mvalo[0]= mval[0];
			mvalo[1]= mval[1];
			
			scrarea_do_windraw(curarea);
			screen_swapbuffers();
		}		
		else BIF_wait_for_statechange();
	}
}

void image_viewzoom(unsigned short event)
{
	SpaceImage *sima= curarea->spacedata.first;
	int width, height;

	if(U.uiflag & USER_WHEELZOOMDIR) {
		if (event==WHEELDOWNMOUSE || event == PADPLUSKEY) {
			sima->zoom *= 2;
		} else {
			sima->zoom /= 2;
			/* Check if the image will still be visible after zooming out */
			if (sima->zoom < 1) {
				calc_image_view(G.sima, 'p');
				if (sima->image) {
					if (sima->image->ibuf) {
						width = sima->image->ibuf->x * sima->zoom;
						height = sima->image->ibuf->y * sima->zoom;
						if ((width < 4) && (height < 4)) {
							/* Image will become too small, reset value */
							sima->zoom *= 2;
						}
					}
				}
			}
		}
	} else {
		if (event==WHEELUPMOUSE || event == PADPLUSKEY) {
			sima->zoom *= 2;
		} else {
			sima->zoom /= 2;
			/* Check if the image will still be visible after zooming out */
			if (sima->zoom < 1) {
				calc_image_view(G.sima, 'p');
				if (sima->image) {
					if (sima->image->ibuf) {
						width = sima->image->ibuf->x * sima->zoom;
						height = sima->image->ibuf->y * sima->zoom;
						if ((width < 4) && (height < 4)) {
							/* Image will become too small, reset value */
							sima->zoom *= 2;
						}
					}
				}
			}
		}
	}
}

/**
 * Updates the fields of the View2D member of the SpaceImage struct.
 * Default behavior is to reset the position of the image and set the zoom to 1
 * If the image will not fit within the window rectangle, the zoom is adjusted
 *
 * @return    void
 *   
 */
void image_home(void)
{
	int width, height;
	float zoomX, zoomY;

	if (curarea->spacetype != SPACE_IMAGE) return;
	if ((G.sima->image == 0) || (G.sima->image->ibuf == 0)) return;

	/* Check if the image will fit in the image with zoom==1 */
	width = curarea->winx;
	height = curarea->winy;
	if (((G.sima->image->ibuf->x >= width) || (G.sima->image->ibuf->y >= height)) && 
		((width > 0) && (height > 0))) {
		/* Find the zoom value that will fit the image in the image space */
		zoomX = ((float)width) / ((float)G.sima->image->ibuf->x);
		zoomY = ((float)height) / ((float)G.sima->image->ibuf->y);
		G.sima->zoom= MIN2(zoomX, zoomY);

		/* Now make it a power of 2 */
		G.sima->zoom = 1 / G.sima->zoom;
		G.sima->zoom = log(G.sima->zoom) / log(2);
		G.sima->zoom = ceil(G.sima->zoom);
		G.sima->zoom = pow(2, G.sima->zoom);
		G.sima->zoom = 1 / G.sima->zoom;
	}
	else {
		G.sima->zoom= (float)1;
	}

	G.sima->xof= G.sima->yof= 0;
	
	calc_image_view(G.sima, 'p');
	
	scrarea_queue_winredraw(curarea);
}

