/**
 * $Id$
 *
 * ***** BEGIN GPL LICENSE BLOCK *****
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
 * The Original Code is Copyright (C) 2005 Blender Foundation.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): Brecht Van Lommel.
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>

#include "GL/glew.h"

#include "DNA_image_types.h"
#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"

#include "MEM_guardedalloc.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "BKE_bmfont.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_material.h"
#include "BKE_node.h"
#include "BKE_object.h"
#include "BKE_utildefines.h"

#include "GPU_extensions.h"
#include "GPU_material.h"
#include "GPU_draw.h"

/* These are some obscure rendering functions shared between the
 * game engine and the blender, in this module to avoid duplicaten
 * and abstract them away from the rest a bit */

/* Text Rendering */

static void gpu_mcol(unsigned int ucol)
{
	/* mcol order is swapped */
	char *cp= (char *)&ucol;
	glColor3ub(cp[3], cp[2], cp[1]);
}

void GPU_render_text(MTFace *tface, int mode,
	const char *textstr, int textlen, unsigned int *col,
	float *v1, float *v2, float *v3, float *v4, int glattrib)
{
	if (mode & TF_BMFONT) {
		Image* ima;
		int characters, index, character;
		float centerx, centery, sizex, sizey, transx, transy, movex, movey, advance;

		/* multiline */
		float line_start= 0.0f, line_height; 
		if (v4)
			line_height= MAX4(v1[1], v2[1], v3[1], v4[2]) - MIN4(v1[1], v2[1], v3[1], v4[2]);
		else
			line_height= MAX3(v1[1], v2[1], v3[1]) - MIN3(v1[1], v2[1], v3[1]);
		line_height *= 1.2; /* could be an option? */
		/* end multiline */
		
		characters = textlen;

		ima = (Image*)tface->tpage;
		if (ima == NULL)
			characters = 0;

		// color has been set
		if (tface->mode & TF_OBCOL)
			col= NULL;
		else if (!col)
			glColor3f(1.0f, 1.0f, 1.0f);

		glPushMatrix();
		
		for (index = 0; index < characters; index++) {
			float uv[4][2];

			// lets calculate offset stuff
			character = textstr[index];
			
			if (character=='\n') {
				glTranslatef(line_start, -line_height, 0.0);
				line_start = 0.0f;
				continue;
			}
			
			// space starts at offset 1
			// character = character - ' ' + 1;
			matrixGlyph((ImBuf *)ima->ibufs.first, character, & centerx, &centery,
				&sizex, &sizey, &transx, &transy, &movex, &movey, &advance);

			uv[0][0] = (tface->uv[0][0] - centerx) * sizex + transx;
			uv[0][1] = (tface->uv[0][1] - centery) * sizey + transy;
			uv[1][0] = (tface->uv[1][0] - centerx) * sizex + transx;
			uv[1][1] = (tface->uv[1][1] - centery) * sizey + transy;
			uv[2][0] = (tface->uv[2][0] - centerx) * sizex + transx;
			uv[2][1] = (tface->uv[2][1] - centery) * sizey + transy;
			
			glBegin(GL_POLYGON);
			if(glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[0]);
			else glTexCoord2fv(uv[0]);
			if(col) gpu_mcol(col[0]);
			glVertex3f(sizex * v1[0] + movex, sizey * v1[1] + movey, v1[2]);
			
			if(glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[1]);
			else glTexCoord2fv(uv[1]);
			if(col) gpu_mcol(col[1]);
			glVertex3f(sizex * v2[0] + movex, sizey * v2[1] + movey, v2[2]);

			if(glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[2]);
			else glTexCoord2fv(uv[2]);
			if(col) gpu_mcol(col[2]);
			glVertex3f(sizex * v3[0] + movex, sizey * v3[1] + movey, v3[2]);

			if(v4) {
				uv[3][0] = (tface->uv[3][0] - centerx) * sizex + transx;
				uv[3][1] = (tface->uv[3][1] - centery) * sizey + transy;

				if(glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[3]);
				else glTexCoord2fv(uv[3]);
				if(col) gpu_mcol(col[3]);
				glVertex3f(sizex * v4[0] + movex, sizey * v4[1] + movey, v4[2]);
			}
			glEnd();

			glTranslatef(advance, 0.0, 0.0);
			line_start -= advance; /* so we can go back to the start of the line */
		}
		glPopMatrix();
	}
}

/* Checking powers of two for images since opengl 1.x requires it */

static int is_pow2(int num)
{
	/* (n&(n-1)) zeros the least significant bit of n */
	return ((num)&(num-1))==0;
}

static int smaller_pow2(int num)
{
	while (!is_pow2(num))
		num= num&(num-1);

	return num;	
}

static int is_pow2_limit(int num)
{
	/* take texture clamping into account */
	if (G.f & G_TEXTUREPAINT)
		return 1;
	if (U.glreslimit != 0 && num > U.glreslimit)
		return 0;

	return ((num)&(num-1))==0;
}

static int smaller_pow2_limit(int num)
{
	if (G.f & G_TEXTUREPAINT)
		return 1;
	
	/* take texture clamping into account */
	if (U.glreslimit != 0 && num > U.glreslimit)
		return U.glreslimit;

	return smaller_pow2(num);
}

/* Current OpenGL state caching for GPU_set_tpage */

static struct GPUTextureState {
	int curtile, tile;
	int curtilemode, tilemode;
	int curtileXRep, tileXRep;
	int curtileYRep, tileYRep;
	Image *ima, *curima;

	int domipmap, linearmipmap;

	int alphamode;
	MTFace *lasttface;
} GTS = {0, 0, 0, 0, 0, 0, 0, 0, NULL, NULL, 1, 0, -1, NULL};

/* Mipmap settings */

void GPU_set_mipmap(int mipmap)
{
	if (GTS.domipmap != (mipmap != 0)) {
		GPU_free_images();
		GTS.domipmap = mipmap != 0;
	}
}

void GPU_set_linear_mipmap(int linear)
{
	if (GTS.linearmipmap != (linear != 0)) {
		GPU_free_images();
		GTS.linearmipmap = linear != 0;
	}
}

static int gpu_get_mipmap(void)
{
	return GTS.domipmap && (!(G.f & G_TEXTUREPAINT));
}

static GLenum gpu_get_mipmap_filter(int mag)
{
	/* linearmipmap is off by default *when mipmapping is off,
	 * use unfiltered display */
	if(mag) {
		if(GTS.linearmipmap || GTS.domipmap)
			return GL_LINEAR;
		else
			return GL_NEAREST;
	}
	else {
		if(GTS.linearmipmap)
			return GL_LINEAR_MIPMAP_LINEAR;
		else if(GTS.domipmap)
			return GL_LINEAR_MIPMAP_NEAREST;
		else
			return GL_NEAREST;
	}
}

/* Set OpenGL state for an MTFace */

static void gpu_make_repbind(Image *ima)
{
	ImBuf *ibuf;
	
	ibuf = BKE_image_get_ibuf(ima, NULL);
	if(ibuf==NULL)
		return;

	if(ima->repbind) {
		glDeleteTextures(ima->totbind, (GLuint *)ima->repbind);
		MEM_freeN(ima->repbind);
		ima->repbind= 0;
		ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
	}

	ima->totbind= ima->xrep*ima->yrep;

	if(ima->totbind>1)
		ima->repbind= MEM_callocN(sizeof(int)*ima->totbind, "repbind");
}

static void gpu_clear_tpage()
{
	if(GTS.lasttface==0)
		return;
	
	GTS.lasttface= 0;
	GTS.curtile= 0;
	GTS.curima= 0;
	if(GTS.curtilemode!=0) {
		glMatrixMode(GL_TEXTURE);
		glLoadIdentity();
		glMatrixMode(GL_MODELVIEW);
	}
	GTS.curtilemode= 0;
	GTS.curtileXRep=0;
	GTS.curtileYRep=0;
	GTS.alphamode= -1;
	
	glDisable(GL_BLEND);
	glDisable(GL_TEXTURE_2D);
	glDisable(GL_TEXTURE_GEN_S);
	glDisable(GL_TEXTURE_GEN_T);
	glDisable(GL_ALPHA_TEST);
}

static void gpu_set_blend_mode(GPUBlendMode blendmode)
{
	if(blendmode == GPU_BLEND_SOLID) {
		glDisable(GL_BLEND);
		glDisable(GL_ALPHA_TEST);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	}
	else if(blendmode==GPU_BLEND_ADD) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_ONE, GL_ONE);
		glDisable(GL_ALPHA_TEST);
	}
	else if(blendmode==GPU_BLEND_ALPHA) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		
		/* if U.glalphaclip == 1.0, some cards go bonkers...
		 * turn off alpha test in this case */

		/* added after 2.45 to clip alpha */
		if(U.glalphaclip == 1.0) {
			glDisable(GL_ALPHA_TEST);
		}
		else {
			glEnable(GL_ALPHA_TEST);
			glAlphaFunc(GL_GREATER, U.glalphaclip);
		}
	}
	else if(blendmode==GPU_BLEND_CLIP) {
		glDisable(GL_BLEND); 
		glEnable(GL_ALPHA_TEST);
		glAlphaFunc(GL_GREATER, 0.5f);
	}
}

static void gpu_verify_alpha_mode(MTFace *tface)
{
	/* verify alpha blending modes */
	if(GTS.alphamode == tface->transp)
		return;

	gpu_set_blend_mode(tface->transp);
	GTS.alphamode= tface->transp;
}

static void gpu_verify_reflection(Image *ima)
{
	if (ima && (ima->flag & IMA_REFLECT)) {
		/* enable reflection mapping */
		glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP);
		glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP);

		glEnable(GL_TEXTURE_GEN_S);
		glEnable(GL_TEXTURE_GEN_T);
	}
	else {
		/* disable reflection mapping */
		glDisable(GL_TEXTURE_GEN_S);
		glDisable(GL_TEXTURE_GEN_T);
	}
}

int GPU_verify_image(Image *ima, int tftile, int tfmode, int compare)
{
	ImBuf *ibuf = NULL;
	unsigned int *bind = NULL;
	int rectw, recth, tpx=0, tpy=0, y;
	unsigned int *rectrow, *tilerectrow;
	unsigned int *tilerect= NULL, *scalerect= NULL, *rect= NULL;
	short texwindx, texwindy, texwinsx, texwinsy;

	/* initialize tile mode and number of repeats */
	GTS.ima = ima;
	GTS.tilemode= (tfmode & TF_TILES) || (ima && (ima->tpageflag & IMA_TWINANIM));
	GTS.tileXRep = 0;
	GTS.tileYRep = 0;

	/* setting current tile according to frame */
	if(ima && (ima->tpageflag & IMA_TWINANIM))
		GTS.tile= ima->lastframe;
	else
		GTS.tile= tftile;

	GTS.tile = MAX2(0, GTS.tile);

	if(ima) {
		GTS.tileXRep = ima->xrep;
		GTS.tileYRep = ima->yrep;
	}

	/* if same image & tile, we're done */
	if(compare && ima == GTS.curima && GTS.curtile == GTS.tile &&
	   GTS.tilemode == GTS.curtilemode && GTS.curtileXRep == GTS.tileXRep &&
	   GTS.curtileYRep == GTS.tileYRep)
		return (ima!=0);

	/* if tiling mode or repeat changed, change texture matrix to fit */
	if(GTS.tilemode!=GTS.curtilemode || GTS.curtileXRep!=GTS.tileXRep ||
	   GTS.curtileYRep != GTS.tileYRep) {

		glMatrixMode(GL_TEXTURE);
		glLoadIdentity();

		if((tfmode & TF_TILES) && ima!=NULL)
			glScalef(ima->xrep, ima->yrep, 1.0);

		glMatrixMode(GL_MODELVIEW);
	}

	/* check if we have a valid image */
	if(ima==NULL || ima->ok==0)
		return 0;

	/* check if we have a valid image buffer */
	ibuf= BKE_image_get_ibuf(ima, NULL);

	if(ibuf==NULL)
		return 0;

	/* ensure we have a char buffer and not only float */
	if ((ibuf->rect==NULL) && ibuf->rect_float)
		IMB_rect_from_float(ibuf);

	if(GTS.tilemode) {
		/* tiled mode */
		if(ima->repbind==0) gpu_make_repbind(ima);
		if(GTS.tile>=ima->totbind) GTS.tile= 0;
		
		/* this happens when you change repeat buttons */
		if(ima->repbind) bind= &ima->repbind[GTS.tile];
		else bind= &ima->bindcode;
		
		if(*bind==0) {
			
			texwindx= ibuf->x/ima->xrep;
			texwindy= ibuf->y/ima->yrep;
			
			if(GTS.tile>=ima->xrep*ima->yrep)
				GTS.tile= ima->xrep*ima->yrep-1;
	
			texwinsy= GTS.tile / ima->xrep;
			texwinsx= GTS.tile - texwinsy*ima->xrep;
	
			texwinsx*= texwindx;
			texwinsy*= texwindy;
	
			tpx= texwindx;
			tpy= texwindy;

			rect= ibuf->rect + texwinsy*ibuf->x + texwinsx;
		}
	}
	else {
		/* regular image mode */
		bind= &ima->bindcode;
		
		if(*bind==0) {
			tpx= ibuf->x;
			tpy= ibuf->y;
			rect= ibuf->rect;
		}
	}

	if(*bind != 0) {
		/* enable opengl drawing with textures */
		glBindTexture(GL_TEXTURE_2D, *bind);
		return *bind;
	}

	rectw = tpx;
	recth = tpy;

	/* for tiles, copy only part of image into buffer */
	if (GTS.tilemode) {
		tilerect= MEM_mallocN(rectw*recth*sizeof(*tilerect), "tilerect");

		for (y=0; y<recth; y++) {
			rectrow= &rect[y*ibuf->x];
			tilerectrow= &tilerect[y*rectw];
				
			memcpy(tilerectrow, rectrow, tpx*sizeof(*rectrow));
		}
			
		rect= tilerect;
	}

	/* scale if not a power of two */
	if (!is_pow2_limit(rectw) || !is_pow2_limit(recth)) {
		rectw= smaller_pow2_limit(rectw);
		recth= smaller_pow2_limit(recth);
		
		scalerect= MEM_mallocN(rectw*recth*sizeof(*scalerect), "scalerect");
		gluScaleImage(GL_RGBA, tpx, tpy, GL_UNSIGNED_BYTE, rect, rectw, recth, GL_UNSIGNED_BYTE, scalerect);
		rect= scalerect;
	}

	/* create image */
	glGenTextures(1, (GLuint *)bind);
	glBindTexture( GL_TEXTURE_2D, *bind);

	if (!gpu_get_mipmap()) {
		glTexImage2D(GL_TEXTURE_2D, 0,  GL_RGBA,  rectw, recth, 0, GL_RGBA, GL_UNSIGNED_BYTE, rect);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));
	}
	else {
		gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, rectw, recth, GL_RGBA, GL_UNSIGNED_BYTE, rect);
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, gpu_get_mipmap_filter(0));
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));

		ima->tpageflag |= IMA_MIPMAP_COMPLETE;
	}

	/* set to modulate with vertex color */
	glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
		
	/* clean up */
	if (tilerect)
		MEM_freeN(tilerect);
	if (scalerect)
		MEM_freeN(scalerect);

	return *bind;
}

static void gpu_verify_repeat(Image *ima)
{
	/* set either clamp or repeat in X/Y */
	if (ima->tpageflag & IMA_CLAMP_U)
	   glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
	else
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);

	if (ima->tpageflag & IMA_CLAMP_V)
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
	else
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
}

int GPU_set_tpage(MTFace *tface)
{
	Image *ima;
	
	/* check if we need to clear the state */
	if(tface==0) {
		gpu_clear_tpage();
		return 0;
	}

	ima= tface->tpage;
	GTS.lasttface= tface;

	gpu_verify_alpha_mode(tface);
	gpu_verify_reflection(ima);

	if(GPU_verify_image(ima, tface->tile, tface->mode, 1)) {
		GTS.curtile= GTS.tile;
		GTS.curima= GTS.ima;
		GTS.curtilemode= GTS.tilemode;
		GTS.curtileXRep = GTS.tileXRep;
		GTS.curtileYRep = GTS.tileYRep;

		glEnable(GL_TEXTURE_2D);
	}
	else {
		glDisable(GL_TEXTURE_2D);
		
		GTS.curtile= 0;
		GTS.curima= 0;
		GTS.curtilemode= 0;
		GTS.curtileXRep = 0;
		GTS.curtileYRep = 0;

		return 0;
	}
	
	gpu_verify_repeat(ima);
	
	/* Did this get lost in the image recode? */
	/* tag_image_time(ima);*/

	return 1;
}

/* these two functions are called on entering and exiting texture paint mode,
   temporary disabling/enabling mipmapping on all images for quick texture
   updates with glTexSubImage2D. images that didn't change don't have to be
   re-uploaded to OpenGL */
void GPU_paint_set_mipmap(int mipmap)
{
	Image* ima;
	
	if(!GTS.domipmap)
		return;

	if(mipmap) {
		for(ima=G.main->image.first; ima; ima=ima->id.next) {
			if(ima->bindcode) {
				if(ima->tpageflag & IMA_MIPMAP_COMPLETE) {
					glBindTexture(GL_TEXTURE_2D, ima->bindcode);
					glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, gpu_get_mipmap_filter(0));
					glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));
				}
				else
					GPU_free_image(ima);
			}
		}

	}
	else {
		for(ima=G.main->image.first; ima; ima=ima->id.next) {
			if(ima->bindcode) {
				glBindTexture(GL_TEXTURE_2D, ima->bindcode);
				glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
				glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));
			}
		}
	}
}

void GPU_paint_update_image(Image *ima, int x, int y, int w, int h)
{
	ImBuf *ibuf;
	
	ibuf = BKE_image_get_ibuf(ima, NULL);
	
	if (ima->repbind || gpu_get_mipmap() || !ima->bindcode || !ibuf ||
		(!is_pow2(ibuf->x) || !is_pow2(ibuf->y)) ||
		(w == 0) || (h == 0)) {
		/* these cases require full reload still */
		GPU_free_image(ima);
	}
	else {
		/* for the special case, we can do a partial update
		 * which is much quicker for painting */
		GLint row_length, skip_pixels, skip_rows;

		glGetIntegerv(GL_UNPACK_ROW_LENGTH, &row_length);
		glGetIntegerv(GL_UNPACK_SKIP_PIXELS, &skip_pixels);
		glGetIntegerv(GL_UNPACK_SKIP_ROWS, &skip_rows);

		if ((ibuf->rect==NULL) && ibuf->rect_float)
			IMB_rect_from_float(ibuf);

		glBindTexture(GL_TEXTURE_2D, ima->bindcode);

		glPixelStorei(GL_UNPACK_ROW_LENGTH, ibuf->x);
		glPixelStorei(GL_UNPACK_SKIP_PIXELS, x);
		glPixelStorei(GL_UNPACK_SKIP_ROWS, y);

		glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, w, h, GL_RGBA,
			GL_UNSIGNED_BYTE, ibuf->rect);

		glPixelStorei(GL_UNPACK_ROW_LENGTH, row_length);
		glPixelStorei(GL_UNPACK_SKIP_PIXELS, skip_pixels);
		glPixelStorei(GL_UNPACK_SKIP_ROWS, skip_rows);

		if(ima->tpageflag & IMA_MIPMAP_COMPLETE)
			ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
	}
}

void GPU_update_images_framechange(void)
{
	Image *ima;
	
	for(ima=G.main->image.first; ima; ima=ima->id.next) {
		if(ima->tpageflag & IMA_TWINANIM) {
			if(ima->twend >= ima->xrep*ima->yrep)
				ima->twend= ima->xrep*ima->yrep-1;
		
			/* check: is bindcode not in the array? free. (to do) */
			
			ima->lastframe++;
			if(ima->lastframe > ima->twend)
				ima->lastframe= ima->twsta;
		}
	}
}

int GPU_update_image_time(Image *ima, double time)
{
	int	inc = 0;
	float	diff;
	int	newframe;

	if (!ima)
		return 0;

	if (ima->lastupdate<0)
		ima->lastupdate = 0;

	if (ima->lastupdate>time)
		ima->lastupdate=(float)time;

	if(ima->tpageflag & IMA_TWINANIM) {
		if(ima->twend >= ima->xrep*ima->yrep) ima->twend= ima->xrep*ima->yrep-1;
		
		/* check: is the bindcode not in the array? Then free. (still to do) */
		
		diff = (float)(time-ima->lastupdate);
		inc = (int)(diff*(float)ima->animspeed);

		ima->lastupdate+=((float)inc/(float)ima->animspeed);

		newframe = ima->lastframe+inc;

		if(newframe > (int)ima->twend) {
			if(ima->twend-ima->twsta != 0)
				newframe = (int)ima->twsta-1 + (newframe-ima->twend)%(ima->twend-ima->twsta);
			else
				newframe = ima->twsta;
		}

		ima->lastframe = newframe;
	}

	return inc;
}

void GPU_free_image(Image *ima)
{
	/* free regular image binding */
	if(ima->bindcode) {
		glDeleteTextures(1, (GLuint *)&ima->bindcode);
		ima->bindcode= 0;
		ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
	}

	/* free glsl image binding */
	if(ima->gputexture) {
		GPU_texture_free(ima->gputexture);
		ima->gputexture= NULL;
	}

	/* free repeated image binding */
	if(ima->repbind) {
		glDeleteTextures(ima->totbind, (GLuint *)ima->repbind);
	
		MEM_freeN(ima->repbind);
		ima->repbind= NULL;
		ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
	}
}

void GPU_free_images(void)
{
	Image* ima;

	if(G.main)
		for(ima=G.main->image.first; ima; ima=ima->id.next)
			GPU_free_image(ima);
}

/* OpenGL Materials */

/* materials start counting at # one.... */
#define MAXMATBUF (MAXMAT+1)

/* OpenGL state caching for materials */

static struct GPUMaterialState {
	float matbuf[MAXMATBUF][2][4];
	int totmat;

	Material *gmatbuf[MAXMATBUF];
	Material *gboundmat;
	Object *gob;
	Scene *gscene;

	GPUBlendMode blendmode[MAXMATBUF];
	int alphapass;

	int lastmatnr, lastretval;
	GPUBlendMode lastblendmode;
} GMS;

Material *gpu_active_node_material(Material *ma)
{
	if(ma && ma->use_nodes && ma->nodetree) {
		bNode *node= nodeGetActiveID(ma->nodetree, ID_MA);

		if(node)
			return (Material *)node->id;
		else
			return NULL;
	}

	return ma;
}

void GPU_set_object_materials(Scene *scene, Object *ob, int glsl, int *do_alpha_pass)
{
	extern Material defmaterial; /* from material.c */
	Material *ma;
	GPUMaterial *gpumat;
	GPUBlendMode blendmode;
	int a;
	
	/* initialize state */
	memset(&GMS, 0, sizeof(GMS));
	GMS.lastmatnr = -1;
	GMS.lastretval = -1;
	GMS.lastblendmode = GPU_BLEND_SOLID;

	GMS.gob = ob;
	GMS.gscene = scene;
	GMS.totmat= ob->totcol;

	GMS.alphapass = (G.vd && G.vd->transp);
	if(do_alpha_pass)
		*do_alpha_pass = 0;

	/* no materials assigned? */
	if(ob->totcol==0) {
		GMS.matbuf[0][0][0]= defmaterial.r;
		GMS.matbuf[0][0][1]= defmaterial.g;
		GMS.matbuf[0][0][2]= defmaterial.b;
		GMS.matbuf[0][0][3]= 1.0;

		GMS.matbuf[0][1][0]= defmaterial.specr;
		GMS.matbuf[0][1][1]= defmaterial.specg;
		GMS.matbuf[0][1][2]= defmaterial.specb;
		GMS.matbuf[0][1][3]= 1.0;
		
		/* do material 1 too, for displists! */
		QUATCOPY(GMS.matbuf[1][0], GMS.matbuf[0][0]);
		QUATCOPY(GMS.matbuf[1][1], GMS.matbuf[0][1]);

		if(glsl) {
			GMS.gmatbuf[0]= &defmaterial;
			GPU_material_from_blender(GMS.gscene, &defmaterial);
		}

		GMS.blendmode[0]= GPU_BLEND_SOLID;
	}
	
	/* setup materials */
	for(a=1; a<=ob->totcol; a++) {
		/* find a suitable material */
		ma= give_current_material(ob, a);
		if(!glsl) ma= gpu_active_node_material(ma);
		if(ma==NULL) ma= &defmaterial;

		/* this shouldn't happen .. */
		if(a>=MAXMATBUF)
			continue;

		/* create glsl material if requested */
		gpumat = (glsl)? GPU_material_from_blender(GMS.gscene, ma): NULL;

		if(gpumat) {
			/* do glsl only if creating it succeed, else fallback */
			GMS.gmatbuf[a]= ma;
			blendmode = GPU_material_blend_mode(gpumat, ob->col);
		}
		else {
			/* fixed function opengl materials */
			if (ma->mode & MA_SHLESS) {
				GMS.matbuf[a][0][0]= ma->r;
				GMS.matbuf[a][0][1]= ma->g;
				GMS.matbuf[a][0][2]= ma->b;
			} else {
				GMS.matbuf[a][0][0]= (ma->ref+ma->emit)*ma->r;
				GMS.matbuf[a][0][1]= (ma->ref+ma->emit)*ma->g;
				GMS.matbuf[a][0][2]= (ma->ref+ma->emit)*ma->b;

				GMS.matbuf[a][1][0]= ma->spec*ma->specr;
				GMS.matbuf[a][1][1]= ma->spec*ma->specg;
				GMS.matbuf[a][1][2]= ma->spec*ma->specb;
				GMS.matbuf[a][1][3]= 1.0;
			}

			blendmode = (ma->alpha == 1.0f)? GPU_BLEND_SOLID: GPU_BLEND_ALPHA;
			if(do_alpha_pass && GMS.alphapass)
				GMS.matbuf[a][0][3]= ma->alpha;
			else
				GMS.matbuf[a][0][3]= 1.0f;
		}

		/* setting do_alpha_pass = 1 indicates this object needs to be
		 * drawn in a second alpha pass for improved blending */
		if(do_alpha_pass) {
			GMS.blendmode[a]= blendmode;
			if(ELEM(blendmode, GPU_BLEND_ALPHA, GPU_BLEND_ADD) && !GMS.alphapass)
				*do_alpha_pass= 1;
		}
	}

	/* let's start with a clean state */
	GPU_disable_material();
}

int GPU_enable_material(int nr, void *attribs)
{
	GPUVertexAttribs *gattribs = attribs;
	GPUMaterial *gpumat;
	GPUBlendMode blendmode;

	/* prevent index to use un-initialized array items */
	if(nr>GMS.totmat)
		nr= GMS.totmat;

	if(gattribs)
		memset(gattribs, 0, sizeof(*gattribs));

	/* keep current material */
	if(nr>=MAXMATBUF || nr==GMS.lastmatnr)
		return GMS.lastretval;

	/* unbind glsl material */
	if(GMS.gboundmat) {
		if(GMS.alphapass) glDepthMask(0);
		GPU_material_unbind(GPU_material_from_blender(GMS.gscene, GMS.gboundmat));
		GMS.gboundmat= NULL;
	}

	/* draw materials with alpha in alpha pass */
	GMS.lastmatnr = nr;
	GMS.lastretval = ELEM(GMS.blendmode[nr], GPU_BLEND_SOLID, GPU_BLEND_CLIP);
	if(GMS.alphapass)
		GMS.lastretval = !GMS.lastretval;

	if(GMS.lastretval) {
		if(gattribs && GMS.gmatbuf[nr]) {
			/* bind glsl material and get attributes */
			Material *mat = GMS.gmatbuf[nr];

			gpumat = GPU_material_from_blender(GMS.gscene, mat);
			GPU_material_vertex_attributes(gpumat, gattribs);
			GPU_material_bind(gpumat, GMS.gob->lay, G.vd->lay, 1.0);
			GPU_material_bind_uniforms(gpumat, GMS.gob->obmat, G.vd->viewmat, G.vd->viewinv, GMS.gob->col);
			GMS.gboundmat= mat;

			if(GMS.alphapass) glDepthMask(1);
		}
		else {
			/* or do fixed function opengl material */
			glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, GMS.matbuf[nr][0]);
			glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, GMS.matbuf[nr][1]);
		}

		/* set (alpha) blending mode */
		blendmode = (GMS.alphapass)? GPU_BLEND_ALPHA: GPU_BLEND_SOLID;
		GPU_set_material_blend_mode(blendmode);
	}

	return GMS.lastretval;
}

void GPU_set_material_blend_mode(int blendmode)
{
	if(GMS.lastblendmode == blendmode)
		return;
	
	gpu_set_blend_mode(blendmode);
	GMS.lastblendmode = blendmode;
}

int GPU_get_material_blend_mode(void)
{
	return GMS.lastblendmode;
}

void GPU_disable_material(void)
{
	GMS.lastmatnr= -1;
	GMS.lastretval= 1;

	if(GMS.gboundmat) {
		if(GMS.alphapass) glDepthMask(0);
		GPU_material_unbind(GPU_material_from_blender(GMS.gscene, GMS.gboundmat));
		GMS.gboundmat= NULL;
	}

	GPU_set_material_blend_mode(GPU_BLEND_SOLID);
}

/* Lights */

int GPU_default_lights(void)
{
	int a, count = 0;
	
	/* initialize */
	if(U.light[0].flag==0 && U.light[1].flag==0 && U.light[2].flag==0) {
		U.light[0].flag= 1;
		U.light[0].vec[0]= -0.3; U.light[0].vec[1]= 0.3; U.light[0].vec[2]= 0.9;
		U.light[0].col[0]= 0.8; U.light[0].col[1]= 0.8; U.light[0].col[2]= 0.8;
		U.light[0].spec[0]= 0.5; U.light[0].spec[1]= 0.5; U.light[0].spec[2]= 0.5;
		U.light[0].spec[3]= 1.0;
		
		U.light[1].flag= 0;
		U.light[1].vec[0]= 0.5; U.light[1].vec[1]= 0.5; U.light[1].vec[2]= 0.1;
		U.light[1].col[0]= 0.4; U.light[1].col[1]= 0.4; U.light[1].col[2]= 0.8;
		U.light[1].spec[0]= 0.3; U.light[1].spec[1]= 0.3; U.light[1].spec[2]= 0.5;
		U.light[1].spec[3]= 1.0;
	
		U.light[2].flag= 0;
		U.light[2].vec[0]= 0.3; U.light[2].vec[1]= -0.3; U.light[2].vec[2]= -0.2;
		U.light[2].col[0]= 0.8; U.light[2].col[1]= 0.5; U.light[2].col[2]= 0.4;
		U.light[2].spec[0]= 0.5; U.light[2].spec[1]= 0.4; U.light[2].spec[2]= 0.3;
		U.light[2].spec[3]= 1.0;
	}

	glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_FALSE);

	glLightfv(GL_LIGHT0, GL_POSITION, U.light[0].vec); 
	glLightfv(GL_LIGHT0, GL_DIFFUSE, U.light[0].col); 
	glLightfv(GL_LIGHT0, GL_SPECULAR, U.light[0].spec); 

	glLightfv(GL_LIGHT1, GL_POSITION, U.light[1].vec); 
	glLightfv(GL_LIGHT1, GL_DIFFUSE, U.light[1].col); 
	glLightfv(GL_LIGHT1, GL_SPECULAR, U.light[1].spec); 

	glLightfv(GL_LIGHT2, GL_POSITION, U.light[2].vec); 
	glLightfv(GL_LIGHT2, GL_DIFFUSE, U.light[2].col); 
	glLightfv(GL_LIGHT2, GL_SPECULAR, U.light[2].spec); 

	for(a=0; a<8; a++) {
		if(a<3) {
			if(U.light[a].flag) {
				glEnable(GL_LIGHT0+a);
				count++;
			}
			else
				glDisable(GL_LIGHT0+a);
			
			// clear stuff from other opengl lamp usage
			glLightf(GL_LIGHT0+a, GL_SPOT_CUTOFF, 180.0);
			glLightf(GL_LIGHT0+a, GL_CONSTANT_ATTENUATION, 1.0);
			glLightf(GL_LIGHT0+a, GL_LINEAR_ATTENUATION, 0.0);
		}
		else
			glDisable(GL_LIGHT0+a);
	}
	
	glDisable(GL_LIGHTING);

	glDisable(GL_COLOR_MATERIAL);

	return count;
}

int GPU_scene_object_lights(Scene *scene, Object *ob, int lay, float viewmat[][4], int ortho)
{
	Base *base;
	Lamp *la;
	int count;
	float position[4], direction[4], energy[4];
	
	/* disable all lights */
	for(count=0; count<8; count++)
		glDisable(GL_LIGHT0+count);
	
	/* view direction for specular is not compute correct by default in
	 * opengl, so we set the settings ourselfs */
	glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, (ortho)? GL_FALSE: GL_TRUE);

	count= 0;
	
	for(base=scene->base.first; base; base=base->next) {
		if(base->object->type!=OB_LAMP)
			continue;

		if(!(base->lay & lay) || !(base->lay & ob->lay))
			continue;

		la= base->object->data;
		
		/* setup lamp transform */
		glPushMatrix();
		glLoadMatrixf((float *)viewmat);
		
		where_is_object_simul(base->object);
		
		if(la->type==LA_SUN) {
			/* sun lamp */
			VECCOPY(direction, base->object->obmat[2]);
			direction[3]= 0.0;

			glLightfv(GL_LIGHT0+count, GL_POSITION, direction); 
		}
		else {
			/* other lamps with attenuation */
			VECCOPY(position, base->object->obmat[3]);
			position[3]= 1.0f;

			glLightfv(GL_LIGHT0+count, GL_POSITION, position); 
			glLightf(GL_LIGHT0+count, GL_CONSTANT_ATTENUATION, 1.0);
			glLightf(GL_LIGHT0+count, GL_LINEAR_ATTENUATION, la->att1/la->dist);
			glLightf(GL_LIGHT0+count, GL_QUADRATIC_ATTENUATION, la->att2/(la->dist*la->dist));
			
			if(la->type==LA_SPOT) {
				/* spot lamp */
				direction[0]= -base->object->obmat[2][0];
				direction[1]= -base->object->obmat[2][1];
				direction[2]= -base->object->obmat[2][2];
				glLightfv(GL_LIGHT0+count, GL_SPOT_DIRECTION, direction);
				glLightf(GL_LIGHT0+count, GL_SPOT_CUTOFF, la->spotsize/2.0);
				glLightf(GL_LIGHT0+count, GL_SPOT_EXPONENT, 128.0*la->spotblend);
			}
			else
				glLightf(GL_LIGHT0+count, GL_SPOT_CUTOFF, 180.0);
		}
		
		/* setup energy */
		energy[0]= la->energy*la->r;
		energy[1]= la->energy*la->g;
		energy[2]= la->energy*la->b;
		energy[3]= 1.0;

		glLightfv(GL_LIGHT0+count, GL_DIFFUSE, energy); 
		glLightfv(GL_LIGHT0+count, GL_SPECULAR, energy);
		glEnable(GL_LIGHT0+count);
		
		glPopMatrix();					
		
		count++;
		if(count==8)
			break;
	}

	return count;
}

/* Default OpenGL State */

void GPU_state_init(void)
{
	/* also called when doing opengl rendering and in the game engine */
	float mat_ambient[] = { 0.0, 0.0, 0.0, 0.0 };
	float mat_specular[] = { 0.5, 0.5, 0.5, 1.0 };
	float mat_shininess[] = { 35.0 };
	int a, x, y;
	GLubyte pat[32*32];
	const GLubyte *patc= pat;
	
	glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient);
	glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_specular);
	glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular);
	glMaterialfv(GL_FRONT_AND_BACK, GL_SHININESS, mat_shininess);

	GPU_default_lights();
	
	glDepthFunc(GL_LEQUAL);
	/* scaling matrices */
	glEnable(GL_NORMALIZE);

	glShadeModel(GL_FLAT);

	glDisable(GL_ALPHA_TEST);
	glDisable(GL_BLEND);
	glDisable(GL_DEPTH_TEST);
	glDisable(GL_FOG);
	glDisable(GL_LIGHTING);
	glDisable(GL_LOGIC_OP);
	glDisable(GL_STENCIL_TEST);
	glDisable(GL_TEXTURE_1D);
	glDisable(GL_TEXTURE_2D);

	/* default on, disable/enable should be local per function */
	glEnableClientState(GL_VERTEX_ARRAY);
	glEnableClientState(GL_NORMAL_ARRAY);
	
	glPixelTransferi(GL_MAP_COLOR, GL_FALSE);
	glPixelTransferi(GL_RED_SCALE, 1);
	glPixelTransferi(GL_RED_BIAS, 0);
	glPixelTransferi(GL_GREEN_SCALE, 1);
	glPixelTransferi(GL_GREEN_BIAS, 0);
	glPixelTransferi(GL_BLUE_SCALE, 1);
	glPixelTransferi(GL_BLUE_BIAS, 0);
	glPixelTransferi(GL_ALPHA_SCALE, 1);
	glPixelTransferi(GL_ALPHA_BIAS, 0);
	
	glPixelTransferi(GL_DEPTH_BIAS, 0);
	glPixelTransferi(GL_DEPTH_SCALE, 1);
	glDepthRange(0.0, 1.0);
	
	a= 0;
	for(x=0; x<32; x++) {
		for(y=0; y<4; y++) {
			if( (x) & 1) pat[a++]= 0x88;
			else pat[a++]= 0x22;
		}
	}
	
	glPolygonStipple(patc);

	glMatrixMode(GL_TEXTURE);
	glLoadIdentity();
	glMatrixMode(GL_MODELVIEW);

	glFrontFace(GL_CCW);
	glCullFace(GL_BACK);
	glDisable(GL_CULL_FACE);
}

