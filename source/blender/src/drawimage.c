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
#else
#include <unistd.h>
#endif   
#include "MEM_guardedalloc.h"

#include "BLI_arithb.h"
#include "BLI_blenlib.h"

#include "IMB_imbuf_types.h"

#include "DNA_image_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_packedFile_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"

#include "BKE_utildefines.h"
#include "BKE_global.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_image.h"
#include "BKE_DerivedMesh.h"
#include "BKE_displist.h"
#include "BKE_object.h"

#include "BDR_editface.h"
#include "BDR_drawobject.h"
#include "BDR_drawmesh.h"
#include "BDR_imagepaint.h"

#include "BIF_gl.h"
#include "BIF_mywindow.h"
#include "BIF_drawimage.h"
#include "BIF_resources.h"
#include "BIF_interface.h"
#include "BIF_editsima.h"
#include "BIF_glutil.h"
#include "BIF_space.h"
#include "BIF_screen.h"
#include "BIF_transform.h"

#include "BSE_headerbuttons.h"
#include "BSE_trans_types.h"
#include "BSE_view.h"

/* Modules used */
#include "mydevice.h"
#include "blendef.h"
#include "butspace.h"  // event codes

static unsigned char *alloc_alpha_clone_image(int *width, int *height)
{
	unsigned int size, alpha;
	unsigned char *rect, *cp;

	if(!Gip.clone.image)
		return NULL;

	if(!Gip.clone.image->ibuf)
		load_image(Gip.clone.image, IB_rect, G.sce, G.scene->r.cfra);

	if(!Gip.clone.image->ibuf || !Gip.clone.image->ibuf->rect)
		return NULL;

	rect= MEM_dupallocN(Gip.clone.image->ibuf->rect);

	if(!rect)
		return NULL;

	*width= Gip.clone.image->ibuf->x;
	*height= Gip.clone.image->ibuf->y;

	size= (*width)*(*height);
	alpha= (unsigned char)255*Gip.clone.alpha;
	cp= rect;

	while(size-- > 0) {
		cp[3]= alpha;
		cp += 4;
	}

	return rect;
}

static void setcloneimage()
{
	if(G.sima->menunr > 0) {
		Image *ima= (Image*)BLI_findlink(&G.main->image, G.sima->menunr-1);

		if(ima) {
			Gip.clone.image= ima;
			Gip.clone.offset[0]= Gip.clone.offset[0]= 0.0;
		}
	}
}

/**
 * Sets up the fields of the View2D member of the SpaceImage struct
 * This routine can be called in two modes:
 * mode == 'f': float mode (0.0 - 1.0)
 * mode == 'p': pixel mode (0 - size)
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
			me= get_mesh(OBACT);
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

				object_uvs_changed(OBACT);
				allqueue(REDRAWBUTSEDIT, 0);
			}
		}
	}
}


void uvco_to_areaco(float *vec, short *mval)
{
	float x, y;

	mval[0]= IS_CLIPPED;
	
	x= (vec[0] - G.v2d->cur.xmin)/(G.v2d->cur.xmax-G.v2d->cur.xmin);
	y= (vec[1] - G.v2d->cur.ymin)/(G.v2d->cur.ymax-G.v2d->cur.ymin);

	if(x>=0.0 && x<=1.0) {
		if(y>=0.0 && y<=1.0) {		
			mval[0]= G.v2d->mask.xmin + x*(G.v2d->mask.xmax-G.v2d->mask.xmin);
			mval[1]= G.v2d->mask.ymin + y*(G.v2d->mask.ymax-G.v2d->mask.ymin);
		}
	}
}

void uvco_to_areaco_noclip(float *vec, int *mval)
{
	float x, y;

	mval[0]= IS_CLIPPED;
	
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
	float pointsize= BIF_GetThemeValuef(TH_VERTEX_SIZE);
 	
	if(G.f & G_FACESELECT) {
		me= get_mesh((G.scene->basact) ? (G.scene->basact->object) : 0);
		if(me && me->tface) {
			calc_image_view(G.sima, 'f');	/* float */
			myortho2(G.v2d->cur.xmin, G.v2d->cur.xmax, G.v2d->cur.ymin, G.v2d->cur.ymax);
			glLoadIdentity();
			
			/* draw shadow mesh */
			if((G.sima->flag & SI_DRAWSHADOW) && !(G.obedit==OBACT)){
				int dmNeedsFree;
				DerivedMesh *dm = mesh_get_derived_final(OBACT, &dmNeedsFree);

				glColor3ub(112, 112, 112);
				if (dm->drawUVEdges) dm->drawUVEdges(dm);

				if (dmNeedsFree) dm->release(dm);
			}
			else if(G.sima->flag & SI_DRAWSHADOW){		
				tface= me->tface;
				mface= me->mface;
				a= me->totface;			
				while(a--) {
					if(!(tface->flag & TF_HIDE)) {
						glColor3ub(112, 112, 112);
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
					if(tface->flag & TF_SELECT) {
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
				if(tface->flag & TF_SELECT) {
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

            /* unselected uv's */
			BIF_ThemeColor(TH_VERTEX);
 			glPointSize(pointsize);

			bglBegin(GL_POINTS);
			tface= me->tface;
			mface= me->mface;
			a= me->totface;
			while(a--) {
				if(tface->flag & TF_SELECT) {
					
					if(tface->flag & TF_SEL1); else bglVertex2fv(tface->uv[0]);
					if(tface->flag & TF_SEL2); else bglVertex2fv(tface->uv[1]);
					if(tface->flag & TF_SEL3); else bglVertex2fv(tface->uv[2]);
					if(mface->v4) {
						if(tface->flag & TF_SEL4); else bglVertex2fv(tface->uv[3]);
					}
				}
				tface++;
				mface++;
			}
			bglEnd();

			/* pinned uv's */
			/* give odd pointsizes odd pin pointsizes */
 	        glPointSize(pointsize*2 + (((int)pointsize % 2)? (-1): 0));
			cpack(0xFF);

			bglBegin(GL_POINTS);
			tface= me->tface;
			mface= me->mface;
			a= me->totface;
			while(a--) {
				if(tface->flag & TF_SELECT) {
					
					if(tface->unwrap & TF_PIN1) bglVertex2fv(tface->uv[0]);
					if(tface->unwrap & TF_PIN2) bglVertex2fv(tface->uv[1]);
					if(tface->unwrap & TF_PIN3) bglVertex2fv(tface->uv[2]);
					if(mface->v4) {
						if(tface->unwrap & TF_PIN4) bglVertex2fv(tface->uv[3]);
					}
				}
				tface++;
				mface++;
			}
			bglEnd();

			/* selected uv's */
			BIF_ThemeColor(TH_VERTEX_SELECT);
 	        glPointSize(pointsize);

			bglBegin(GL_POINTS);
			tface= me->tface;
			mface= me->mface;
			a= me->totface;
			while(a--) {
				if(tface->flag & TF_SELECT) {
					
					if(tface->flag & TF_SEL1) bglVertex2fv(tface->uv[0]);
					if(tface->flag & TF_SEL2) bglVertex2fv(tface->uv[1]);
					if(tface->flag & TF_SEL3) bglVertex2fv(tface->uv[2]);
					if(mface->v4) {
						if(tface->flag & TF_SEL4) bglVertex2fv(tface->uv[3]);
					}
				}
				tface++;
				mface++;
			}
			bglEnd();
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

static void draw_image_transform(ImBuf *ibuf)
{
	if(G.moving) {
		float aspx, aspy, center[3];

        BIF_drawConstraint();

		if(ibuf==0 || ibuf->rect==0 || ibuf->x==0 || ibuf->y==0) {
			aspx= aspy= 1.0;
		}
		else {
			aspx= 256.0/ibuf->x;
			aspy= 256.0/ibuf->y;
		}

		BIF_getPropCenter(center);

		/* scale and translate the circle into place and draw it */
		glPushMatrix();
		glScalef(aspx, aspy, 1.0);
		glTranslatef((1/aspx)*center[0] - center[0],
		             (1/aspy)*center[1] - center[1], 0.0);

		BIF_drawPropCircle();

		glPopMatrix();
	}
}

static void draw_image_view_icon(void)
{
	float xPos = 5.0;

	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA,  GL_ONE_MINUS_SRC_ALPHA); 
	
	if(G.sima->flag & SI_STICKYUVS) {
		BIF_draw_icon(xPos, 5.0, ICON_STICKY2_UVS);
		xPos = 25.0;
	}
	else if(G.sima->flag & SI_LOCALSTICKY) {
		BIF_draw_icon(xPos, 5.0, ICON_STICKY_UVS);
		xPos = 25.0;
	}

	if(G.sima->flag & SI_SELACTFACE) {
		BIF_draw_icon(xPos, 5.0, ICON_DRAW_UVFACES);
	}
	
	glBlendFunc(GL_ONE,  GL_ZERO); 
	glDisable(GL_BLEND);
}

static void draw_image_view_tool(void)
{
	ImagePaintTool *tool = &Gip.tool[Gip.current];
	short mval[2];
	float radius;
	int draw= 0;

	if(Gip.flag & IMAGEPAINT_DRAWING) {
		if(Gip.flag & IMAGEPAINT_DRAW_TOOL_DRAWING)
			draw= 1;
	}
	else if(Gip.flag & IMAGEPAINT_DRAW_TOOL)
		draw= 1;
	
	if(draw) {
		getmouseco_areawin(mval);

		radius= tool->size*G.sima->zoom/2;
		fdrawXORcirc(mval[0], mval[1], radius);

		if (tool->innerradius != 1.0) {
			radius *= tool->innerradius;
			fdrawXORcirc(mval[0], mval[1], radius);
		}
	}
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
	int i, nactive= 0, step, digits;
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
		
		if (!(tf->flag & TF_SELECT))
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
			ocent[0]= cent[0]/nactive;
			ocent[1]= cent[1]/nactive;
			if (G.sima->flag & SI_COORDFLOATS) {
				step= 1;
				digits= 3;
			}
			else {
				ocent[0] *= imx;
				ocent[1] *= imy;
				step= 100;
				digits= 2;
			}
			
			uiDefBut(block, LABEL, 0, "UV Vertex:",10,55,302,19,0,0,0,0,0,"");
			uiBlockBeginAlign(block);
			if(nactive==1) {
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Vertex X:",	10, 35, 290, 19, &ocent[0], -10*imx, 10.0*imx, step, digits, "");
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Vertex Y:",	10, 15, 290, 19, &ocent[1], -10*imy, 10.0*imy, step, digits, "");
			}
			else {
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Median X:",	10, 35, 290, 19, &ocent[0], -10*imx, 10.0*imx, step, digits, "");
				uiDefButF(block, NUM, B_TRANS_IMAGE, "Median Y:",	10, 15, 290, 19, &ocent[1], -10*imy, 10.0*imy, step, digits, "");
			}
			uiBlockEndAlign(block);
		}
	}
	else {	// apply event
		float delta[2];
		
		cent[0]= cent[0]/nactive;
		cent[1]= cent[1]/nactive;
			
		if (G.sima->flag & SI_COORDFLOATS) {
			delta[0]= ocent[0]-cent[0];
			delta[1]= ocent[1]-cent[1];
		}
		else {
			delta[0]= ocent[0]/imx - cent[0];
			delta[1]= ocent[1]/imy - cent[1];
		}

		for (i=0; i<me->totface; i++) {
			MFace *mf= &((MFace*) me->mface)[i];
			TFace *tf= &((TFace*) me->tface)[i];
		
			if (!(tf->flag & TF_SELECT))
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

	case B_SIMACLONEBROWSE:
		setcloneimage();
		allqueue(REDRAWIMAGE, 0);
		break;
		
	case B_SIMACLONEDELETE:
		Gip.clone.image= NULL;
		allqueue(REDRAWIMAGE, 0);
		break;

	case B_SIMABRUSHCHANGE:
		allqueue(REDRAWIMAGE, 0);
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
		uiDefBut(block, LABEL, B_NOP, str,		10,180,300,19, 0, 0, 0, 0, 0, "");

		uiBlockBeginAlign(block);
		uiDefButBitS(block, TOG, IMA_TWINANIM, B_TWINANIM, "Anim", 10,150,140,19, &G.sima->image->tpageflag, 0, 0, 0, 0, "Toggles use of animated texture");
		uiDefButS(block, NUM, B_TWINANIM, "Start:",		10,130,140,19, &G.sima->image->twsta, 0.0, 128.0, 0, 0, "Displays the start frame of an animated texture");
		uiDefButS(block, NUM, B_TWINANIM, "End:",		10,110,140,19, &G.sima->image->twend, 0.0, 128.0, 0, 0, "Displays the end frame of an animated texture");
		uiDefButS(block, NUM, B_NOP, "Speed", 				10,90,140,19, &G.sima->image->animspeed, 1.0, 100.0, 0, 0, "Displays Speed of the animation in frames per second");
		uiBlockEndAlign(block);

		uiBlockBeginAlign(block);
		uiDefButBitS(block, TOG, IMA_TILES, B_SIMAGEDRAW1, "Tiles",	160,150,140,19, &G.sima->image->tpageflag, 0, 0, 0, 0, "Toggles use of tilemode for faces");
		uiDefButS(block, NUM, B_SIMAGEDRAW, "X:",		160,130,70,19, &G.sima->image->xrep, 1.0, 16.0, 0, 0, "Sets the degree of repetition in the X direction");
		uiDefButS(block, NUM, B_SIMAGEDRAW, "Y:",		230,130,70,19, &G.sima->image->yrep, 1.0, 16.0, 0, 0, "Sets the degree of repetition in the Y direction");
		uiBlockBeginAlign(block);
	}

	image_editvertex_buts(block);
}

static void image_panel_paint(short cntrl)	// IMAGE_HANDLER_PROPERTIES
{
	ImagePaintTool *tool= &Gip.tool[Gip.current];
	uiBlock *block;
	ID *id;

	block= uiNewBlock(&curarea->uiblocks, "image_panel_paint", UI_EMBOSS, UI_HELV, curarea->win);
	uiPanelControl(UI_PNL_SOLID | UI_PNL_CLOSE | cntrl);
	uiSetPanelHandler(IMAGE_HANDLER_PAINT);  // for close and esc
	if(uiNewPanel(curarea, block, "Image Paint", "Image", 10, 230, 318, 204)==0)
		return;

	uiBlockBeginAlign(block);
	uiDefButF(block, COL, B_VPCOLSLI, "",		979,160,230,19, tool->rgba, 0, 0, 0, 0, "");
	uiDefButF(block, NUMSLI, 0, "Opacity ",		979,140,230,19, tool->rgba+3, 0.0, 1.0, 0, 0, "The amount of pressure on the brush");
	uiDefButI(block, NUMSLI, 0, "Size ",		979,120,230,19, &tool->size, 2, 64, 0, 0, "The size of the brush");
	uiDefButF(block, NUMSLI, 0, "Fall ",		979,100,230,19, &tool->innerradius, 0.0, 1.0, 0, 0, "The fall off radius of the brush");

	if(Gip.current == IMAGEPAINT_BRUSH || Gip.current == IMAGEPAINT_SMEAR)
		uiDefButF(block, NUMSLI, 0, "Stepsize ",979,80,230,19, &tool->timing, 1.0, 100.0, 0, 0, "Repeating Paint On %of Brush diameter");
	else
		uiDefButF(block, NUMSLI, 0, "Flow ",	979,80,230,19, &tool->timing, 1.0, 100.0, 0, 0, "Paint Flow for Air Brush");
	uiBlockEndAlign(block);

	uiBlockBeginAlign(block);
	/* TODO: FLOATPANELMESSAGEEATER catching LMB on the panel buttons */
	/* so LMB does not "GO" through the floating panel */
	uiDefButS(block, ROW, B_SIMABRUSHCHANGE, "Brush",		890,160,80,19, &Gip.current, 7.0, IMAGEPAINT_BRUSH, 0, 0, "Brush");
	uiDefButS(block, ROW, B_SIMABRUSHCHANGE, "AirBrush",		890,140,80,19, &Gip.current, 7.0, IMAGEPAINT_AIRBRUSH, 0, 0, "AirBrush");
	uiDefButS(block, ROW, B_SIMABRUSHCHANGE, "Soften",		890,120,80,19, &Gip.current, 7.0, IMAGEPAINT_SOFTEN, 0, 0, "Soften");
	uiDefButS(block, ROW, B_SIMABRUSHCHANGE, "Aux AB1",		890,100,80,19, &Gip.current, 7.0, IMAGEPAINT_AUX1, 0, 0, "Auxiliary Air Brush1");
	uiDefButS(block, ROW, B_SIMABRUSHCHANGE, "Aux AB2",		890,80,80,19, &Gip.current, 7.0, IMAGEPAINT_AUX2, 0, 0, "Auxiliary Air Brush2");	
	uiDefButS(block, ROW, B_SIMABRUSHCHANGE, "Smear",		890,60,80,19, &Gip.current, 7.0, IMAGEPAINT_SMEAR, 0, 0, "Smear");	
	uiDefButS(block, ROW, B_SIMABRUSHCHANGE, "Clone",		890,40,80,19, &Gip.current, 7.0, IMAGEPAINT_CLONE, 0, 0, "Clone Brush / use RMB to drag source image");	
	uiBlockEndAlign(block);

	uiBlockBeginAlign(block);	
	id= (ID*)Gip.clone.image;
	std_libbuttons(block, 979, 40, 0, NULL, B_SIMACLONEBROWSE, id, 0, &G.sima->menunr, 0, 0, B_SIMACLONEDELETE, 0, 0);
	uiDefButF(block, NUMSLI, 0, "B ",979,20,230,19, &Gip.clone.alpha , 0.0, 1.0, 0, 0, "Blend clone image");
	uiBlockEndAlign(block);

#if 0
	uiDefButBitS(block, TOG|BIT, IMAGEPAINT_DRAW_TOOL_DRAWING, B_SIMABRUSHCHANGE, "TD", 890,1,50,19, &Gip.flag, 0, 0, 0, 0, "Enables tool shape while drawing");
	uiDefButBitS(block, TOG|BIT, IMAGEPAINT_DRAW_TOOL, B_SIMABRUSHCHANGE, "TP", 940,1,50,19, &Gip.flag, 0, 0, 0, 0, "Enables tool shape while not drawing");
#endif
	uiDefButBitS(block, TOG|BIT, IMAGEPAINT_TORUS, B_SIMABRUSHCHANGE, "Wrap", 890,1,50,19, &Gip.flag, 0, 0, 0, 0, "Enables torus wrapping");
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
		case IMAGE_HANDLER_PAINT:
			image_panel_paint(sima->blockhandler[a+1]);
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
	int x1, y1;
	short sx, sy, dx, dy;
	
		/* If derived data is used then make sure that object
		 * is up-to-date... might not be the case because updates
		 * are normally done in drawview and could get here before
		 * drawing a View3D.
		 */
	if (!G.obedit && OBACT && (G.sima->flag&SI_DRAWSHADOW)) {
		object_handle_update(OBACT);
	}

	BIF_GetThemeColor3fv(TH_BACK, col);
	glClearColor(col[0], col[1], col[2], 0.0);
	glClear(GL_COLOR_BUFFER_BIT);

	bwin_clear_viewmat(sa->win);	/* clear buttons view */
	glLoadIdentity();
	
	what_image(G.sima);
	
	if(G.sima->image) {
		if(G.sima->image->ibuf==0) {
			load_image(G.sima->image, IB_rect, G.sce, G.scene->r.cfra);
		}	
		tag_image_time(G.sima->image);
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
		x1= (curarea->winx-G.sima->zoom*ibuf->x)/2;
		y1= (curarea->winy-G.sima->zoom*ibuf->y)/2;
	
		x1-= G.sima->zoom*G.sima->xof;
		y1-= G.sima->zoom*G.sima->yof;
		
		/* needed for gla draw */
		glaDefine2DArea(&curarea->winrct);
		glPixelZoom((float)G.sima->zoom, (float)G.sima->zoom);
				
		if(G.sima->flag & SI_EDITTILE) {
			glaDrawPixelsSafe(x1, y1, ibuf->x, ibuf->y, ibuf->rect);
			
			glPixelZoom(1.0, 1.0);
			
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
						glaDrawPixelsSafe(x1+sx*G.sima->zoom, y1+sy*G.sima->zoom, dx, dy, rect);
					}
				}
				
				MEM_freeN(rect);
			}
			else 
				glaDrawPixelsSafe(x1, y1, ibuf->x, ibuf->y, ibuf->rect);
			
			if(Gip.current == IMAGEPAINT_CLONE) {
				int w, h;
				unsigned char *clonerect;

				/* this is not very efficient, but glDrawPixels doesn't allow
				   drawing with alpha */
				clonerect= alloc_alpha_clone_image(&w, &h);

				if(clonerect) {
					int offx, offy;
					offx = G.sima->zoom*ibuf->x * + Gip.clone.offset[0];
					offy = G.sima->zoom*ibuf->y * + Gip.clone.offset[1];

					glEnable(GL_BLEND);
					glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
					glaDrawPixelsSafe(x1 + offx, y1 + offy, w, h, clonerect);
					glDisable(GL_BLEND);

					MEM_freeN(clonerect);
				}
			}
			
			glPixelZoom(1.0, 1.0);
			
			draw_tfaces();
		}
	
		calc_image_view(G.sima, 'f');	/* float */
	}

	draw_image_transform(ibuf);

	myortho2(-0.375, sa->winx-0.375, -0.375, sa->winy-0.375);

	draw_image_view_tool();
	draw_image_view_icon();
	draw_area_emboss(sa);

	/* it is important to end a view in a transform compatible with buttons */
	bwin_scalematrix(sa->win, G.sima->blockscale, G.sima->blockscale, G.sima->blockscale);
	image_blockhandlers(sa);

	curarea->win_swap= WIN_BACK_OK;
}

static void image_zoom_power_of_two(void)
{
	/* Make zoom a power of 2 */

	G.sima->zoom = 1 / G.sima->zoom;
	G.sima->zoom = log(G.sima->zoom) / log(2);
	G.sima->zoom = ceil(G.sima->zoom);
	G.sima->zoom = pow(2, G.sima->zoom);
	G.sima->zoom = 1 / G.sima->zoom;
}

static void image_zoom_set_factor(float zoomfac)
{
	SpaceImage *sima= curarea->spacedata.first;
	int width, height;

	if (zoomfac <= 0.0f)
		return;

	sima->zoom *= zoomfac;

	if (sima->zoom > 0.1f && sima->zoom < 4.0f)
		return;

	/* check zoom limits */

	calc_image_view(G.sima, 'p');
	width= 256;
	height= 256;
	if (sima->image) {
		if (sima->image->ibuf) {
			width= sima->image->ibuf->x;
			height= sima->image->ibuf->y;
		}
	}
	width *= sima->zoom;
	height *= sima->zoom;

	if ((width < 4) && (height < 4))
		sima->zoom /= zoomfac;
	else if((curarea->winrct.xmax - curarea->winrct.xmin) <= sima->zoom)
		sima->zoom /= zoomfac;
	else if((curarea->winrct.ymax - curarea->winrct.ymin) <= sima->zoom)
		sima->zoom /= zoomfac;
}

void image_viewmove(int mode)
{
	short mval[2], mvalo[2], zoom0;
	
	getmouseco_sc(mvalo);
	zoom0= G.sima->zoom;
	
	while(get_mbut()&(L_MOUSE|M_MOUSE)) {

		getmouseco_sc(mval);

		if(mvalo[0]!=mval[0] || mvalo[1]!=mval[1]) {
		
			if(mode==0) {
				G.sima->xof += (mvalo[0]-mval[0])/G.sima->zoom;
				G.sima->yof += (mvalo[1]-mval[1])/G.sima->zoom;
			}
			else if (mode==1) {
				float factor;

				factor= 1.0+(float)(mvalo[0]-mval[0]+mvalo[1]-mval[1])/300.0;
				image_zoom_set_factor(factor);
			}

			mvalo[0]= mval[0];
			mvalo[1]= mval[1];
			
			scrarea_do_windraw(curarea);
			screen_swapbuffers();
		}
		else BIF_wait_for_statechange();
	}
}

void image_viewzoom(unsigned short event, int invert)
{
	SpaceImage *sima= curarea->spacedata.first;

	if(event==WHEELDOWNMOUSE || event==PADMINUS)
		image_zoom_set_factor((U.uiflag & USER_WHEELZOOMDIR)? 1.25: 0.8);
	else if(event==WHEELUPMOUSE || event==PADPLUSKEY)
		image_zoom_set_factor((U.uiflag & USER_WHEELZOOMDIR)? 0.8: 1.25);
	else if(event==PAD1)
		sima->zoom= 1.0;
	else if(event==PAD2)
		sima->zoom= (invert)? 2.0: 0.5;
	else if(event==PAD4)
		sima->zoom= (invert)? 4.0: 0.25;
	else if(event==PAD8)
		sima->zoom= (invert)? 8.0: 0.125;
	else
		return;
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

		image_zoom_power_of_two();
	}
	else {
		G.sima->zoom= (float)1;
	}

	G.sima->xof= G.sima->yof= 0;
	
	calc_image_view(G.sima, 'p');
	
	scrarea_queue_winredraw(curarea);
}

void image_viewcentre(void)
{
	float size, min[2], max[2], d[2], xim=256.0f, yim=256.0f;

	if( is_uv_tface_editing_allowed()==0 ) return;

	if (!minmax_tface_uv(min, max)) return;

	if(G.sima->image && G.sima->image->ibuf) {
		xim= G.sima->image->ibuf->x;
		yim= G.sima->image->ibuf->y;
	}

	G.sima->xof= ((min[0] + max[0])*0.5f - 0.5f)*xim;
	G.sima->yof= ((min[1] + max[1])*0.5f - 0.5f)*yim;

	d[0] = max[0] - min[0];
	d[1] = max[1] - min[1];
	size= 0.5*MAX2(d[0], d[1])*MAX2(xim, yim)/256.0f;
	
	if(size<=0.01) size= 0.01;

	G.sima->zoom= 0.7/size;

	calc_image_view(G.sima, 'p');

	scrarea_queue_winredraw(curarea);
}

