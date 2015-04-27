/*
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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
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

/** \file blender/gpu/intern/gpu_draw.c
 *  \ingroup gpu
 *
 * Utility functions for dealing with OpenGL texture & material context,
 * mipmap generation and light objects.
 *
 * These are some obscure rendering functions shared between the
 * game engine and the blender, in this module to avoid duplication
 * and abstract them away from the rest a bit.
 */

#include <string.h>

#include "GPU_glew.h"
#include "GPU_debug.h"

#include "BLI_blenlib.h"
#include "BLI_linklist.h"
#include "BLI_math.h"
#include "BLI_threads.h"
#include "BLI_utildefines.h"

#include "DNA_lamp_types.h"
#include "DNA_material_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_modifier_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_smoke_types.h"
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
#include "BKE_scene.h"
#include "BKE_DerivedMesh.h"

#include "GPU_buffers.h"
#include "GPU_draw.h"
#include "GPU_extensions.h"
#include "GPU_material.h"

#include "PIL_time.h"

#include "smoke_API.h"

extern Material defmaterial; /* from material.c */

/* Text Rendering */

static void gpu_mcol(unsigned int ucol)
{
	/* mcol order is swapped */
	const char *cp = (char *)&ucol;
	glColor3ub(cp[3], cp[2], cp[1]);
}

void GPU_render_text(MTFace *tface, int mode,
	const char *textstr, int textlen, unsigned int *col,
	float *v1, float *v2, float *v3, float *v4, int glattrib)
{
	if ((mode & GEMAT_TEXT) && (textlen > 0) && tface->tpage) {
		Image* ima = (Image *)tface->tpage;
		ImBuf *first_ibuf;
		const size_t textlen_st = textlen;
		size_t index;
		float centerx, centery, sizex, sizey, transx, transy, movex, movey, advance;
		float advance_tab;
		
		/* multiline */
		float line_start = 0.0f, line_height;
		
		if (v4)
			line_height = max_ffff(v1[1], v2[1], v3[1], v4[2]) - min_ffff(v1[1], v2[1], v3[1], v4[2]);
		else
			line_height = max_fff(v1[1], v2[1], v3[1]) - min_fff(v1[1], v2[1], v3[1]);
		line_height *= 1.2f; /* could be an option? */
		/* end multiline */

		
		/* color has been set */
		if (tface->mode & TF_OBCOL)
			col = NULL;
		else if (!col)
			glColor3f(1.0f, 1.0f, 1.0f);

		glPushMatrix();
		
		/* get the tab width */
		first_ibuf = BKE_image_get_first_ibuf(ima);
		matrixGlyph(first_ibuf, ' ', &centerx, &centery,
			&sizex, &sizey, &transx, &transy, &movex, &movey, &advance);
		
		advance_tab = advance * 4; /* tab width could also be an option */
		
		
		for (index = 0; index < textlen_st; ) {
			unsigned int character;
			float uv[4][2];

			/* lets calculate offset stuff */
			character = BLI_str_utf8_as_unicode_and_size_safe(textstr + index, &index);
			
			if (character == '\n') {
				glTranslatef(line_start, -line_height, 0.0f);
				line_start = 0.0f;
				continue;
			}
			else if (character == '\t') {
				glTranslatef(advance_tab, 0.0f, 0.0f);
				line_start -= advance_tab; /* so we can go back to the start of the line */
				continue;
				
			}
			else if (character > USHRT_MAX) {
				/* not much we can do here bmfonts take ushort */
				character = '?';
			}
			
			/* space starts at offset 1 */
			/* character = character - ' ' + 1; */
			matrixGlyph(first_ibuf, character, & centerx, &centery,
				&sizex, &sizey, &transx, &transy, &movex, &movey, &advance);

			uv[0][0] = (tface->uv[0][0] - centerx) * sizex + transx;
			uv[0][1] = (tface->uv[0][1] - centery) * sizey + transy;
			uv[1][0] = (tface->uv[1][0] - centerx) * sizex + transx;
			uv[1][1] = (tface->uv[1][1] - centery) * sizey + transy;
			uv[2][0] = (tface->uv[2][0] - centerx) * sizex + transx;
			uv[2][1] = (tface->uv[2][1] - centery) * sizey + transy;
			
			glBegin(GL_POLYGON);
			if (glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[0]);
			else glTexCoord2fv(uv[0]);
			if (col) gpu_mcol(col[0]);
			glVertex3f(sizex * v1[0] + movex, sizey * v1[1] + movey, v1[2]);
			
			if (glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[1]);
			else glTexCoord2fv(uv[1]);
			if (col) gpu_mcol(col[1]);
			glVertex3f(sizex * v2[0] + movex, sizey * v2[1] + movey, v2[2]);

			if (glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[2]);
			else glTexCoord2fv(uv[2]);
			if (col) gpu_mcol(col[2]);
			glVertex3f(sizex * v3[0] + movex, sizey * v3[1] + movey, v3[2]);

			if (v4) {
				uv[3][0] = (tface->uv[3][0] - centerx) * sizex + transx;
				uv[3][1] = (tface->uv[3][1] - centery) * sizey + transy;

				if (glattrib >= 0) glVertexAttrib2fvARB(glattrib, uv[3]);
				else glTexCoord2fv(uv[3]);
				if (col) gpu_mcol(col[3]);
				glVertex3f(sizex * v4[0] + movex, sizey * v4[1] + movey, v4[2]);
			}
			glEnd();

			glTranslatef(advance, 0.0f, 0.0f);
			line_start -= advance; /* so we can go back to the start of the line */
		}
		glPopMatrix();

		BKE_image_release_ibuf(ima, first_ibuf, NULL);
	}
}

/* Checking powers of two for images since opengl 1.x requires it */

static bool is_power_of_2_resolution(int w, int h)
{
	return is_power_of_2_i(w) && is_power_of_2_i(h);
}

static bool is_over_resolution_limit(int w, int h)
{
	int reslimit = (U.glreslimit != 0)?
		min_ii(U.glreslimit, GPU_max_texture_size()) :
		GPU_max_texture_size();

	return (w > reslimit || h > reslimit);
}

static int smaller_power_of_2_limit(int num)
{
	int reslimit = (U.glreslimit != 0)?
		min_ii(U.glreslimit, GPU_max_texture_size()) :
		GPU_max_texture_size();
	/* take texture clamping into account */
	if (num > reslimit)
		return reslimit;

	return power_of_2_min_i(num);
}

/* Current OpenGL state caching for GPU_set_tpage */

static struct GPUTextureState {
	int curtile, tile;
	int curtilemode, tilemode;
	int curtileXRep, tileXRep;
	int curtileYRep, tileYRep;
	Image *ima, *curima;

	/* also controls min/mag filtering */
	bool domipmap;
	/* only use when 'domipmap' is set */
	bool linearmipmap;
	/* store this so that new images created while texture painting won't be set to mipmapped */
	bool texpaint;

	int alphablend;
	float anisotropic;
	int gpu_mipmap;
	MTFace *lasttface;
} GTS = {0, 0, 0, 0, 0, 0, 0, 0, NULL, NULL, 1, 0, 0, -1, 1.0f, 0, NULL};

/* Mipmap settings */

void GPU_set_gpu_mipmapping(int gpu_mipmap)
{
	int old_value = GTS.gpu_mipmap;

	/* only actually enable if it's supported */
	GTS.gpu_mipmap = gpu_mipmap && GLEW_EXT_framebuffer_object;

	if (old_value != GTS.gpu_mipmap) {
		GPU_free_images();
	}
}

static void gpu_generate_mipmap(GLenum target)
{
	const bool is_ati = GPU_type_matches(GPU_DEVICE_ATI, GPU_OS_ANY, GPU_DRIVER_ANY);
	int target_enabled = 0;

	/* work around bug in ATI driver, need to have GL_TEXTURE_2D enabled
	 * http://www.opengl.org/wiki/Common_Mistakes#Automatic_mipmap_generation */
	if (is_ati) {
		target_enabled = glIsEnabled(target);
		if (!target_enabled)
			glEnable(target);
	}

	glGenerateMipmapEXT(target);

	if (is_ati && !target_enabled)
		glDisable(target);
}

void GPU_set_mipmap(bool mipmap)
{
	if (GTS.domipmap != mipmap) {
		GPU_free_images();
		GTS.domipmap = mipmap;
	}
}

void GPU_set_linear_mipmap(bool linear)
{
	if (GTS.linearmipmap != linear) {
		GTS.linearmipmap = linear;
	}
}

bool GPU_get_mipmap(void)
{
	return GTS.domipmap && !GTS.texpaint;
}

bool GPU_get_linear_mipmap(void)
{
	return GTS.linearmipmap;
}

static GLenum gpu_get_mipmap_filter(bool mag)
{
	/* linearmipmap is off by default *when mipmapping is off,
	 * use unfiltered display */
	if (mag) {
		if (GTS.domipmap)
			return GL_LINEAR;
		else
			return GL_NEAREST;
	}
	else {
		if (GTS.domipmap) {
			if (GTS.linearmipmap) {
				return GL_LINEAR_MIPMAP_LINEAR;
			}
			else {
				return GL_LINEAR_MIPMAP_NEAREST;
			}
		}
		else {
			return GL_NEAREST;
		}
	}
}

/* Anisotropic filtering settings */
void GPU_set_anisotropic(float value)
{
	if (GTS.anisotropic != value) {
		GPU_free_images();

		/* Clamp value to the maximum value the graphics card supports */
		if (value > GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT)
			value = GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT;

		GTS.anisotropic = value;
	}
}

float GPU_get_anisotropic(void)
{
	return GTS.anisotropic;
}

/* Set OpenGL state for an MTFace */

static void gpu_make_repbind(Image *ima)
{
	ImBuf *ibuf;
	
	ibuf = BKE_image_acquire_ibuf(ima, NULL, NULL);
	if (ibuf == NULL)
		return;

	if (ima->repbind) {
		glDeleteTextures(ima->totbind, (GLuint *)ima->repbind);
		MEM_freeN(ima->repbind);
		ima->repbind = NULL;
		ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
	}

	ima->totbind = ima->xrep*ima->yrep;

	if (ima->totbind>1)
		ima->repbind = MEM_callocN(sizeof(int) * ima->totbind, "repbind");

	BKE_image_release_ibuf(ima, ibuf, NULL);
}

void GPU_clear_tpage(bool force)
{
	if (GTS.lasttface == NULL && !force)
		return;
	
	GTS.lasttface = NULL;
	GTS.curtile = 0;
	GTS.curima = NULL;
	if (GTS.curtilemode != 0) {
		glMatrixMode(GL_TEXTURE);
		glLoadIdentity();
		glMatrixMode(GL_MODELVIEW);
	}
	GTS.curtilemode = 0;
	GTS.curtileXRep = 0;
	GTS.curtileYRep = 0;
	GTS.alphablend = -1;
	
	glDisable(GL_BLEND);
	glDisable(GL_TEXTURE_2D);
	glDisable(GL_TEXTURE_GEN_S);
	glDisable(GL_TEXTURE_GEN_T);
	glDisable(GL_ALPHA_TEST);
}

static void gpu_set_alpha_blend(GPUBlendMode alphablend)
{
	if (alphablend == GPU_BLEND_SOLID) {
		glDisable(GL_BLEND);
		glDisable(GL_ALPHA_TEST);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	}
	else if (alphablend == GPU_BLEND_ADD) {
		glEnable(GL_BLEND);
		glBlendFunc(GL_ONE, GL_ONE);
		glDisable(GL_ALPHA_TEST);
	}
	else if (ELEM(alphablend, GPU_BLEND_ALPHA, GPU_BLEND_ALPHA_SORT)) {
		glEnable(GL_BLEND);

		/* for OpenGL render we use the alpha channel, this makes alpha blend correct */
		if (GLEW_VERSION_1_4)
			glBlendFuncSeparate(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA, GL_ONE, GL_ONE_MINUS_SRC_ALPHA);
		else
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		
		/* if U.glalphaclip == 1.0, some cards go bonkers...
		 * turn off alpha test in this case */

		/* added after 2.45 to clip alpha */
		if (U.glalphaclip == 1.0f) {
			glDisable(GL_ALPHA_TEST);
		}
		else {
			glEnable(GL_ALPHA_TEST);
			glAlphaFunc(GL_GREATER, U.glalphaclip);
		}
	}
	else if (alphablend == GPU_BLEND_CLIP) {
		glDisable(GL_BLEND); 
		glEnable(GL_ALPHA_TEST);
		glAlphaFunc(GL_GREATER, 0.5f);
	}
}

static void gpu_verify_alpha_blend(int alphablend)
{
	/* verify alpha blending modes */
	if (GTS.alphablend == alphablend)
		return;

	gpu_set_alpha_blend(alphablend);
	GTS.alphablend = alphablend;
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

int GPU_verify_image(Image *ima, ImageUser *iuser, int tftile, bool compare, bool mipmap, bool is_data)
{
	ImBuf *ibuf = NULL;
	unsigned int *bind = NULL;
	int rectw, recth, tpx = 0, tpy = 0, y;
	unsigned int *tilerect = NULL, *rect = NULL;
	float *ftilerect = NULL, *frect = NULL;
	float *srgb_frect = NULL;
	short texwindx, texwindy, texwinsx, texwinsy;
	/* flag to determine whether high resolution format is used */
	bool use_high_bit_depth = false, do_color_management = false;

	/* initialize tile mode and number of repeats */
	GTS.ima = ima;
	GTS.tilemode = (ima && (ima->tpageflag & (IMA_TILES|IMA_TWINANIM)));
	GTS.tileXRep = 0;
	GTS.tileYRep = 0;

	/* setting current tile according to frame */
	if (ima && (ima->tpageflag & IMA_TWINANIM))
		GTS.tile = ima->lastframe;
	else
		GTS.tile = tftile;

	GTS.tile = MAX2(0, GTS.tile);

	if (ima) {
		GTS.tileXRep = ima->xrep;
		GTS.tileYRep = ima->yrep;
	}

	/* if same image & tile, we're done */
	if (compare && ima == GTS.curima && GTS.curtile == GTS.tile &&
	    GTS.tilemode == GTS.curtilemode && GTS.curtileXRep == GTS.tileXRep &&
	    GTS.curtileYRep == GTS.tileYRep)
	{
		return (ima != NULL);
	}

	/* if tiling mode or repeat changed, change texture matrix to fit */
	if (GTS.tilemode != GTS.curtilemode || GTS.curtileXRep != GTS.tileXRep ||
	    GTS.curtileYRep != GTS.tileYRep)
	{
		glMatrixMode(GL_TEXTURE);
		glLoadIdentity();

		if (ima && (ima->tpageflag & IMA_TILES))
			glScalef(ima->xrep, ima->yrep, 1.0f);

		glMatrixMode(GL_MODELVIEW);
	}

	/* check if we have a valid image */
	if (ima == NULL || ima->ok == 0)
		return 0;

	/* check if we have a valid image buffer */
	ibuf = BKE_image_acquire_ibuf(ima, iuser, NULL);

	if (ibuf == NULL)
		return 0;

	if (ibuf->rect_float) {
		if (U.use_16bit_textures) {
			/* use high precision textures. This is relatively harmless because OpenGL gives us
			 * a high precision format only if it is available */
			use_high_bit_depth = true;
		}
		/* we may skip this in high precision, but if not, we need to have a valid buffer here */
		else if (ibuf->userflags & IB_RECT_INVALID) {
			IMB_rect_from_float(ibuf);
		}

		/* TODO unneeded when float images are correctly treated as linear always */
		if (!is_data)
			do_color_management = true;

		if (ibuf->rect == NULL)
			IMB_rect_from_float(ibuf);
	}

	/* currently, tpage refresh is used by ima sequences */
	if (ima->tpageflag & IMA_TPAGE_REFRESH) {
		GPU_free_image(ima);
		ima->tpageflag &= ~IMA_TPAGE_REFRESH;
	}
	
	if (GTS.tilemode) {
		/* tiled mode */
		if (ima->repbind == NULL) gpu_make_repbind(ima);
		if (GTS.tile >= ima->totbind) GTS.tile = 0;
		
		/* this happens when you change repeat buttons */
		if (ima->repbind) bind = &ima->repbind[GTS.tile];
		else bind = &ima->bindcode;
		
		if (*bind == 0) {
			texwindx = ibuf->x / ima->xrep;
			texwindy = ibuf->y / ima->yrep;
			
			if (GTS.tile >= ima->xrep * ima->yrep)
				GTS.tile = ima->xrep * ima->yrep - 1;
	
			texwinsy = GTS.tile / ima->xrep;
			texwinsx = GTS.tile - texwinsy * ima->xrep;
	
			texwinsx *= texwindx;
			texwinsy *= texwindy;
	
			tpx = texwindx;
			tpy = texwindy;

			if (use_high_bit_depth) {
				if (do_color_management) {
					srgb_frect = MEM_mallocN(ibuf->x * ibuf->y * sizeof(float) * 4, "floar_buf_col_cor");
					IMB_buffer_float_from_float(srgb_frect, ibuf->rect_float,
						ibuf->channels, IB_PROFILE_SRGB, IB_PROFILE_LINEAR_RGB, true,
						ibuf->x, ibuf->y, ibuf->x, ibuf->x);
					IMB_buffer_float_unpremultiply(srgb_frect, ibuf->x, ibuf->y);
					/* clamp buffer colors to 1.0 to avoid artifacts due to glu for hdr images */
					IMB_buffer_float_clamp(srgb_frect, ibuf->x, ibuf->y);
					frect = srgb_frect + texwinsy*ibuf->x + texwinsx;
				}
				else
					frect = ibuf->rect_float + texwinsy*ibuf->x + texwinsx;
			}
			else
				rect = ibuf->rect + texwinsy*ibuf->x + texwinsx;
		}
	}
	else {
		/* regular image mode */
		bind= &ima->bindcode;

		if (*bind == 0) {
			tpx = ibuf->x;
			tpy = ibuf->y;
			rect = ibuf->rect;
			if (use_high_bit_depth) {
				if (do_color_management) {
					frect = srgb_frect = MEM_mallocN(ibuf->x * ibuf->y * sizeof(*srgb_frect) * 4, "floar_buf_col_cor");
					IMB_buffer_float_from_float(srgb_frect, ibuf->rect_float,
							ibuf->channels, IB_PROFILE_SRGB, IB_PROFILE_LINEAR_RGB, true,
							ibuf->x, ibuf->y, ibuf->x, ibuf->x);
					IMB_buffer_float_unpremultiply(srgb_frect, ibuf->x, ibuf->y);
					/* clamp buffer colors to 1.0 to avoid artifacts due to glu for hdr images */
					IMB_buffer_float_clamp(srgb_frect, ibuf->x, ibuf->y);
				}
				else
					frect = ibuf->rect_float;
			}
		}
	}

	if (*bind != 0) {
		/* enable opengl drawing with textures */
		glBindTexture(GL_TEXTURE_2D, *bind);
		BKE_image_release_ibuf(ima, ibuf, NULL);
		return *bind;
	}

	rectw = tpx;
	recth = tpy;

	/* for tiles, copy only part of image into buffer */
	if (GTS.tilemode) {
		if (use_high_bit_depth) {
			float *frectrow, *ftilerectrow;

			ftilerect = MEM_mallocN(rectw*recth*sizeof(*ftilerect), "tilerect");

			for (y = 0; y < recth; y++) {
				frectrow = &frect[y * ibuf->x];
				ftilerectrow = &ftilerect[y * rectw];

				memcpy(ftilerectrow, frectrow, tpx * sizeof(*frectrow));
			}

			frect = ftilerect;
		}
		else {
			unsigned int *rectrow, *tilerectrow;

			tilerect = MEM_mallocN(rectw*recth*sizeof(*tilerect), "tilerect");

			for (y = 0; y < recth; y++) {
				rectrow = &rect[y * ibuf->x];
				tilerectrow = &tilerect[y * rectw];

				memcpy(tilerectrow, rectrow, tpx * sizeof(*rectrow));
			}
			
			rect = tilerect;
		}
	}

#ifdef WITH_DDS
	if (ibuf->ftype & DDS)
		GPU_create_gl_tex_compressed(bind, rect, rectw, recth, mipmap, ima, ibuf);
	else
#endif
		GPU_create_gl_tex(bind, rect, frect, rectw, recth, mipmap, use_high_bit_depth, ima);
	
	/* mark as non-color data texture */
	if (*bind) {
		if (is_data)
			ima->tpageflag |= IMA_GLBIND_IS_DATA;	
		else
			ima->tpageflag &= ~IMA_GLBIND_IS_DATA;	
	}

	/* clean up */
	if (tilerect)
		MEM_freeN(tilerect);
	if (ftilerect)
		MEM_freeN(ftilerect);
	if (srgb_frect)
		MEM_freeN(srgb_frect);

	BKE_image_release_ibuf(ima, ibuf, NULL);

	return *bind;
}

/* Image *ima can be NULL */
void GPU_create_gl_tex(unsigned int *bind, unsigned int *rect, float *frect, int rectw, int recth,
                       bool mipmap, bool use_high_bit_depth, Image *ima)
{
	ImBuf *ibuf = NULL;

	int tpx = rectw;
	int tpy = recth;

	/* scale if not a power of two. this is not strictly necessary for newer
	 * GPUs (OpenGL version >= 2.0) since they support non-power-of-two-textures 
	 * Then don't bother scaling for hardware that supports NPOT textures! */
	if ((!GPU_non_power_of_two_support() && !is_power_of_2_resolution(rectw, recth)) ||
		is_over_resolution_limit(rectw, recth)) {
		rectw = smaller_power_of_2_limit(rectw);
		recth = smaller_power_of_2_limit(recth);
		
		if (use_high_bit_depth) {
			ibuf = IMB_allocFromBuffer(NULL, frect, tpx, tpy);
			IMB_scaleImBuf(ibuf, rectw, recth);

			frect = ibuf->rect_float;
		}
		else {
			ibuf = IMB_allocFromBuffer(rect, NULL, tpx, tpy);
			IMB_scaleImBuf(ibuf, rectw, recth);

			rect = ibuf->rect;
		}
	}

	/* create image */
	glGenTextures(1, (GLuint *)bind);
	glBindTexture(GL_TEXTURE_2D, *bind);

	if (use_high_bit_depth) {
		if (GLEW_ARB_texture_float)
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16F, rectw, recth, 0, GL_RGBA, GL_FLOAT, frect);
		else
			glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA16, rectw, recth, 0, GL_RGBA, GL_FLOAT, frect);
	}
	else
		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, rectw, recth, 0, GL_RGBA, GL_UNSIGNED_BYTE, rect);

	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));

	if (GPU_get_mipmap() && mipmap) {
		if (GTS.gpu_mipmap) {
			gpu_generate_mipmap(GL_TEXTURE_2D);
		}
		else {
			int i;

			if (!ibuf) {
				if (use_high_bit_depth) {
					ibuf = IMB_allocFromBuffer(NULL, frect, tpx, tpy);
				}
				else {
					ibuf = IMB_allocFromBuffer(rect, NULL, tpx, tpy);
				}
			}

			IMB_makemipmap(ibuf, true);

			for (i = 1; i < ibuf->miptot; i++) {
				ImBuf *mip = ibuf->mipmap[i - 1];
				if (use_high_bit_depth) {
					if (GLEW_ARB_texture_float)
						glTexImage2D(GL_TEXTURE_2D, i, GL_RGBA16F, mip->x, mip->y, 0, GL_RGBA, GL_FLOAT, mip->rect_float);
					else
						glTexImage2D(GL_TEXTURE_2D, i, GL_RGBA16, mip->x, mip->y, 0, GL_RGBA, GL_FLOAT, mip->rect_float);
				}
				else {
					glTexImage2D(GL_TEXTURE_2D, i, GL_RGBA, mip->x, mip->y, 0, GL_RGBA, GL_UNSIGNED_BYTE, mip->rect);
				}
			}
		}
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, gpu_get_mipmap_filter(0));

		if (ima)
			ima->tpageflag |= IMA_MIPMAP_COMPLETE;
	}
	else {
		glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	}

	if (GLEW_EXT_texture_filter_anisotropic)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, GPU_get_anisotropic());
	/* set to modulate with vertex color */
	glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);

	if (ibuf)
		IMB_freeImBuf(ibuf);
}

/**
 * GPU_upload_dxt_texture() assumes that the texture is already bound and ready to go.
 * This is so the viewport and the BGE can share some code.
 * Returns false if the provided ImBuf doesn't have a supported DXT compression format
 */
bool GPU_upload_dxt_texture(ImBuf *ibuf)
{
#ifdef WITH_DDS
	GLint format = 0;
	int blocksize, height, width, i, size, offset = 0;

	width = ibuf->x;
	height = ibuf->y;

	if (GLEW_EXT_texture_compression_s3tc) {
		if (ibuf->dds_data.fourcc == FOURCC_DXT1)
			format = GL_COMPRESSED_RGBA_S3TC_DXT1_EXT;
		else if (ibuf->dds_data.fourcc == FOURCC_DXT3)
			format = GL_COMPRESSED_RGBA_S3TC_DXT3_EXT;
		else if (ibuf->dds_data.fourcc == FOURCC_DXT5)
			format = GL_COMPRESSED_RGBA_S3TC_DXT5_EXT;
	}

	if (format == 0) {
		fprintf(stderr, "Unable to find a suitable DXT compression, falling back to uncompressed\n");
		return false;
	}

	if (!is_power_of_2_resolution(width, height)) {
		fprintf(stderr, "Unable to load non-power-of-two DXT image resolution, falling back to uncompressed\n");
		return false;
	}

	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, gpu_get_mipmap_filter(0));
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));

	glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);

	if (GLEW_EXT_texture_filter_anisotropic)
		glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, GPU_get_anisotropic());

	blocksize = (ibuf->dds_data.fourcc == FOURCC_DXT1) ? 8 : 16;
	for (i = 0; i < ibuf->dds_data.nummipmaps && (width||height); ++i) {
		if (width == 0)
			width = 1;
		if (height == 0)
			height = 1;

		size = ((width+3)/4)*((height+3)/4)*blocksize;

		glCompressedTexImage2D(GL_TEXTURE_2D, i, format, width, height,
			0, size, ibuf->dds_data.data + offset);

		offset += size;
		width >>= 1;
		height >>= 1;
	}

	/* set number of mipmap levels we have, needed in case they don't go down to 1x1 */
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAX_LEVEL, i - 1);

	return true;
#else
	(void)ibuf;
	return false;
#endif
}

void GPU_create_gl_tex_compressed(unsigned int *bind, unsigned int *pix, int x, int y, int mipmap, Image *ima, ImBuf *ibuf)
{
#ifndef WITH_DDS
	(void)ibuf;
	/* Fall back to uncompressed if DDS isn't enabled */
	GPU_create_gl_tex(bind, pix, NULL, x, y, mipmap, 0, ima);
#else


	glGenTextures(1, (GLuint *)bind);
	glBindTexture(GL_TEXTURE_2D, *bind);

	if (GPU_upload_dxt_texture(ibuf) == 0) {
		glDeleteTextures(1, (GLuint *)bind);
		GPU_create_gl_tex(bind, pix, NULL, x, y, mipmap, 0, ima);
	}
#endif
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

int GPU_set_tpage(MTFace *tface, int mipmap, int alphablend)
{
	Image *ima;
	
	/* check if we need to clear the state */
	if (tface == NULL) {
		GPU_clear_tpage(false);
		return 0;
	}

	ima = tface->tpage;
	GTS.lasttface = tface;

	gpu_verify_alpha_blend(alphablend);
	gpu_verify_reflection(ima);

	if (GPU_verify_image(ima, NULL, tface->tile, 1, mipmap, false)) {
		GTS.curtile = GTS.tile;
		GTS.curima = GTS.ima;
		GTS.curtilemode = GTS.tilemode;
		GTS.curtileXRep = GTS.tileXRep;
		GTS.curtileYRep = GTS.tileYRep;

		glEnable(GL_TEXTURE_2D);
	}
	else {
		glDisable(GL_TEXTURE_2D);
		
		GTS.curtile = 0;
		GTS.curima = NULL;
		GTS.curtilemode = 0;
		GTS.curtileXRep = 0;
		GTS.curtileYRep = 0;

		return 0;
	}
	
	gpu_verify_repeat(ima);
	
	/* Did this get lost in the image recode? */
	/* BKE_image_tag_time(ima);*/

	return 1;
}

/* these two functions are called on entering and exiting texture paint mode,
 * temporary disabling/enabling mipmapping on all images for quick texture
 * updates with glTexSubImage2D. images that didn't change don't have to be
 * re-uploaded to OpenGL */
void GPU_paint_set_mipmap(bool mipmap)
{
	Image *ima;
	
	if (!GTS.domipmap)
		return;

	GTS.texpaint = !mipmap;

	if (mipmap) {
		for (ima = G.main->image.first; ima; ima = ima->id.next) {
			if (ima->bindcode) {
				if (ima->tpageflag & IMA_MIPMAP_COMPLETE) {
					glBindTexture(GL_TEXTURE_2D, ima->bindcode);
					glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, gpu_get_mipmap_filter(0));
					glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));
				}
				else
					GPU_free_image(ima);
			}
			else
				ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
		}

	}
	else {
		for (ima = G.main->image.first; ima; ima = ima->id.next) {
			if (ima->bindcode) {
				glBindTexture(GL_TEXTURE_2D, ima->bindcode);
				glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
				glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, gpu_get_mipmap_filter(1));
			}
			else
				ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
		}
	}
}


/* check if image has been downscaled and do scaled partial update */
static bool GPU_check_scaled_image(ImBuf *ibuf, Image *ima, float *frect, int x, int y, int w, int h)
{
	if ((!GPU_non_power_of_two_support() && !is_power_of_2_resolution(ibuf->x, ibuf->y)) ||
	    is_over_resolution_limit(ibuf->x, ibuf->y))
	{
		int x_limit = smaller_power_of_2_limit(ibuf->x);
		int y_limit = smaller_power_of_2_limit(ibuf->y);

		float xratio = x_limit / (float)ibuf->x;
		float yratio = y_limit / (float)ibuf->y;

		/* find new width, height and x,y gpu texture coordinates */

		/* take ceiling because we will be losing 1 pixel due to rounding errors in x,y... */
		int rectw = (int)ceil(xratio * w);
		int recth = (int)ceil(yratio * h);

		x *= xratio;
		y *= yratio;

		/* ...but take back if we are over the limit! */
		if (rectw + x > x_limit) rectw--;
		if (recth + y > y_limit) recth--;

		/* float rectangles are already continuous in memory so we can use IMB_scaleImBuf */
		if (frect) {
			ImBuf *ibuf = IMB_allocFromBuffer(NULL, frect, w, h);
			IMB_scaleImBuf(ibuf, rectw, recth);

			glBindTexture(GL_TEXTURE_2D, ima->bindcode);
			glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, rectw, recth, GL_RGBA,
			                GL_FLOAT, ibuf->rect_float);

			IMB_freeImBuf(ibuf);
		}
		/* byte images are not continuous in memory so do manual interpolation */
		else {
			unsigned char *scalerect = MEM_mallocN(rectw * recth * sizeof(*scalerect) * 4, "scalerect");
			unsigned int *p = (unsigned int *)scalerect;
			int i, j;
			float inv_xratio = 1.0f / xratio;
			float inv_yratio = 1.0f / yratio;
			for (i = 0; i < rectw; i++) {
				float u = (x + i) * inv_xratio;
				for (j = 0; j < recth; j++) {
					float v = (y + j) * inv_yratio;
					bilinear_interpolation_color_wrap(ibuf, (unsigned char *)(p + i + j * (rectw)), NULL, u, v);
				}
			}
			glBindTexture(GL_TEXTURE_2D, ima->bindcode);
			glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, rectw, recth, GL_RGBA,
			                GL_UNSIGNED_BYTE, scalerect);

			MEM_freeN(scalerect);
		}

		if (GPU_get_mipmap()) {
			gpu_generate_mipmap(GL_TEXTURE_2D);
		}
		else {
			ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
		}

		return true;
	}

	return false;
}

void GPU_paint_update_image(Image *ima, ImageUser *iuser, int x, int y, int w, int h)
{
	ImBuf *ibuf;
	
	ibuf = BKE_image_acquire_ibuf(ima, iuser, NULL);
	
	if (ima->repbind || (GPU_get_mipmap() && !GTS.gpu_mipmap) || !ima->bindcode || !ibuf ||
		(w == 0) || (h == 0))
	{
		/* these cases require full reload still */
		GPU_free_image(ima);
	}
	else {
		/* for the special case, we can do a partial update
		 * which is much quicker for painting */
		GLint row_length, skip_pixels, skip_rows;

		/* if color correction is needed, we must update the part that needs updating. */
		if (ibuf->rect_float) {
			float *buffer = MEM_mallocN(w * h * sizeof(float) * 4, "temp_texpaint_float_buf");
			bool is_data = (ima->tpageflag & IMA_GLBIND_IS_DATA) != 0;
			IMB_partial_rect_from_float(ibuf, buffer, x, y, w, h, is_data);
			
			if (GPU_check_scaled_image(ibuf, ima, buffer, x, y, w, h)) {
				MEM_freeN(buffer);
				BKE_image_release_ibuf(ima, ibuf, NULL);
				return;
			}

			glBindTexture(GL_TEXTURE_2D, ima->bindcode);
			glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, w, h, GL_RGBA, GL_FLOAT, buffer);

			MEM_freeN(buffer);

			/* we have already accounted for the case where GTS.gpu_mipmap is false
			 * so we will be using GPU mipmap generation here */
			if (GPU_get_mipmap()) {
				gpu_generate_mipmap(GL_TEXTURE_2D);
			}
			else {
				ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
			}

			BKE_image_release_ibuf(ima, ibuf, NULL);
			return;
		}

		if (GPU_check_scaled_image(ibuf, ima, NULL, x, y, w, h)) {
			BKE_image_release_ibuf(ima, ibuf, NULL);
			return;
		}

		glBindTexture(GL_TEXTURE_2D, ima->bindcode);

		glGetIntegerv(GL_UNPACK_ROW_LENGTH, &row_length);
		glGetIntegerv(GL_UNPACK_SKIP_PIXELS, &skip_pixels);
		glGetIntegerv(GL_UNPACK_SKIP_ROWS, &skip_rows);

		glPixelStorei(GL_UNPACK_ROW_LENGTH, ibuf->x);
		glPixelStorei(GL_UNPACK_SKIP_PIXELS, x);
		glPixelStorei(GL_UNPACK_SKIP_ROWS, y);

		glTexSubImage2D(GL_TEXTURE_2D, 0, x, y, w, h, GL_RGBA,
			GL_UNSIGNED_BYTE, ibuf->rect);

		glPixelStorei(GL_UNPACK_ROW_LENGTH, row_length);
		glPixelStorei(GL_UNPACK_SKIP_PIXELS, skip_pixels);
		glPixelStorei(GL_UNPACK_SKIP_ROWS, skip_rows);

		/* see comment above as to why we are using gpu mipmap generation here */
		if (GPU_get_mipmap()) {
			gpu_generate_mipmap(GL_TEXTURE_2D);
		}
		else {
			ima->tpageflag &= ~IMA_MIPMAP_COMPLETE;
		}
	}

	BKE_image_release_ibuf(ima, ibuf, NULL);
}

void GPU_update_images_framechange(void)
{
	Image *ima;
	
	for (ima = G.main->image.first; ima; ima = ima->id.next) {
		if (ima->tpageflag & IMA_TWINANIM) {
			if (ima->twend >= ima->xrep * ima->yrep)
				ima->twend = ima->xrep * ima->yrep - 1;
		
			/* check: is bindcode not in the array? free. (to do) */
			
			ima->lastframe++;
			if (ima->lastframe > ima->twend)
				ima->lastframe = ima->twsta;
		}
	}
}

int GPU_update_image_time(Image *ima, double time)
{
	int	inc = 0;
	float diff;
	int	newframe;

	if (!ima)
		return 0;

	if (ima->lastupdate < 0)
		ima->lastupdate = 0;

	if (ima->lastupdate > (float)time)
		ima->lastupdate = (float)time;

	if (ima->tpageflag & IMA_TWINANIM) {
		if (ima->twend >= ima->xrep * ima->yrep) ima->twend = ima->xrep * ima->yrep - 1;
		
		/* check: is the bindcode not in the array? Then free. (still to do) */
		
		diff = (float)((float)time - ima->lastupdate);
		inc = (int)(diff * (float)ima->animspeed);

		ima->lastupdate += ((float)inc / (float)ima->animspeed);

		newframe = ima->lastframe + inc;

		if (newframe > (int)ima->twend) {
			if (ima->twend - ima->twsta != 0)
				newframe = (int)ima->twsta - 1 + (newframe - ima->twend) % (ima->twend - ima->twsta);
			else
				newframe = ima->twsta;
		}

		ima->lastframe = newframe;
	}

	return inc;
}


void GPU_free_smoke(SmokeModifierData *smd)
{
	if (smd->type & MOD_SMOKE_TYPE_DOMAIN && smd->domain) {
		if (smd->domain->tex)
			GPU_texture_free(smd->domain->tex);
		smd->domain->tex = NULL;

		if (smd->domain->tex_shadow)
			GPU_texture_free(smd->domain->tex_shadow);
		smd->domain->tex_shadow = NULL;

		if (smd->domain->tex_flame)
			GPU_texture_free(smd->domain->tex_flame);
		smd->domain->tex_flame = NULL;
	}
}

void GPU_create_smoke(SmokeModifierData *smd, int highres)
{
#ifdef WITH_SMOKE
	if (smd->type & MOD_SMOKE_TYPE_DOMAIN) {
		SmokeDomainSettings *sds = smd->domain;
		if (!sds->tex && !highres) {
			/* rgba texture for color + density */
			if (smoke_has_colors(sds->fluid)) {
				float *data = MEM_callocN(sizeof(float) * sds->total_cells * 4, "smokeColorTexture");
				smoke_get_rgba(sds->fluid, data, 0);
				sds->tex = GPU_texture_create_3D(sds->res[0], sds->res[1], sds->res[2], 4, data);
				MEM_freeN(data);
			}
			/* density only */
			else {
				sds->tex = GPU_texture_create_3D(sds->res[0], sds->res[1], sds->res[2], 1, smoke_get_density(sds->fluid));
			}
			sds->tex_flame = (smoke_has_fuel(sds->fluid)) ? GPU_texture_create_3D(sds->res[0], sds->res[1], sds->res[2], 1, smoke_get_flame(sds->fluid)) : NULL;
		}
		else if (!sds->tex && highres) {
			/* rgba texture for color + density */
			if (smoke_turbulence_has_colors(sds->wt)) {
				float *data = MEM_callocN(sizeof(float) * smoke_turbulence_get_cells(sds->wt) * 4, "smokeColorTexture");
				smoke_turbulence_get_rgba(sds->wt, data, 0);
				sds->tex = GPU_texture_create_3D(sds->res_wt[0], sds->res_wt[1], sds->res_wt[2], 4, data);
				MEM_freeN(data);
			}
			/* density only */
			else {
				sds->tex = GPU_texture_create_3D(sds->res_wt[0], sds->res_wt[1], sds->res_wt[2], 1, smoke_turbulence_get_density(sds->wt));
			}
			sds->tex_flame = (smoke_turbulence_has_fuel(sds->wt)) ? GPU_texture_create_3D(sds->res_wt[0], sds->res_wt[1], sds->res_wt[2], 1, smoke_turbulence_get_flame(sds->wt)) : NULL;
		}

		sds->tex_shadow = GPU_texture_create_3D(sds->res[0], sds->res[1], sds->res[2], 1, sds->shadow);
	}
#else // WITH_SMOKE
	(void)highres;
	smd->domain->tex = NULL;
	smd->domain->tex_flame = NULL;
	smd->domain->tex_shadow = NULL;
#endif // WITH_SMOKE
}

static LinkNode *image_free_queue = NULL;

static void gpu_queue_image_for_free(Image *ima)
{
	BLI_lock_thread(LOCK_OPENGL);
	BLI_linklist_prepend(&image_free_queue, ima);
	BLI_unlock_thread(LOCK_OPENGL);
}

void GPU_free_unused_buffers(void)
{
	LinkNode *node;
	Image *ima;

	if (!BLI_thread_is_main())
		return;

	BLI_lock_thread(LOCK_OPENGL);

	/* images */
	for (node = image_free_queue; node; node = node->next) {
		ima = node->link;

		/* check in case it was freed in the meantime */
		if (G.main && BLI_findindex(&G.main->image, ima) != -1)
			GPU_free_image(ima);
	}

	BLI_linklist_free(image_free_queue, NULL);
	image_free_queue = NULL;

	/* vbo buffers */
	GPU_global_buffer_pool_free_unused();

	BLI_unlock_thread(LOCK_OPENGL);
}

void GPU_free_image(Image *ima)
{
	if (!BLI_thread_is_main()) {
		gpu_queue_image_for_free(ima);
		return;
	}

	/* free regular image binding */
	if (ima->bindcode) {
		glDeleteTextures(1, (GLuint *)&ima->bindcode);
		ima->bindcode = 0;
	}

	/* free glsl image binding */
	if (ima->gputexture) {
		GPU_texture_free(ima->gputexture);
		ima->gputexture = NULL;
	}

	/* free repeated image binding */
	if (ima->repbind) {
		glDeleteTextures(ima->totbind, (GLuint *)ima->repbind);
	
		MEM_freeN(ima->repbind);
		ima->repbind = NULL;
	}

	ima->tpageflag &= ~(IMA_MIPMAP_COMPLETE|IMA_GLBIND_IS_DATA);
}

void GPU_free_images(void)
{
	Image *ima;

	if (G.main)
		for (ima = G.main->image.first; ima; ima = ima->id.next)
			GPU_free_image(ima);
}

/* same as above but only free animated images */
void GPU_free_images_anim(void)
{
	Image *ima;

	if (G.main)
		for (ima = G.main->image.first; ima; ima = ima->id.next)
			if (BKE_image_is_animated(ima))
				GPU_free_image(ima);
}


void GPU_free_images_old(void)
{
	Image *ima;
	static int lasttime = 0;
	int ctime = PIL_check_seconds_timer_i();

	/*
	 * Run garbage collector once for every collecting period of time
	 * if textimeout is 0, that's the option to NOT run the collector
	 */
	if (U.textimeout == 0 || ctime % U.texcollectrate || ctime == lasttime)
		return;

	/* of course not! */
	if (G.is_rendering)
		return;

	lasttime = ctime;

	ima = G.main->image.first;
	while (ima) {
		if ((ima->flag & IMA_NOCOLLECT) == 0 && ctime - ima->lastused > U.textimeout) {
			/* If it's in GL memory, deallocate and set time tag to current time
			 * This gives textures a "second chance" to be used before dying. */
			if (ima->bindcode || ima->repbind) {
				GPU_free_image(ima);
				ima->lastused = ctime;
			}
			/* Otherwise, just kill the buffers */
			else {
				BKE_image_free_buffers(ima);
			}
		}
		ima = ima->id.next;
	}
}


/* OpenGL Materials */

#define FIXEDMAT 8

/* OpenGL state caching for materials */

typedef struct GPUMaterialFixed {
	float diff[4];
	float spec[4];
	int hard;
} GPUMaterialFixed; 

static struct GPUMaterialState {
	GPUMaterialFixed (*matbuf);
	GPUMaterialFixed matbuf_fixed[FIXEDMAT];
	int totmat;

	Material **gmatbuf;
	Material *gmatbuf_fixed[FIXEDMAT];
	Material *gboundmat;
	Object *gob;
	Scene *gscene;
	int glay;
	bool gscenelock;
	float (*gviewmat)[4];
	float (*gviewinv)[4];
	float (*gviewcamtexcofac);

	bool backface_culling;

	GPUBlendMode *alphablend;
	GPUBlendMode alphablend_fixed[FIXEDMAT];
	bool use_alpha_pass, is_alpha_pass;
	bool use_matcaps;

	int lastmatnr, lastretval;
	GPUBlendMode lastalphablend;
} GMS = {NULL};

/* fixed function material, alpha handed by caller */
static void gpu_material_to_fixed(GPUMaterialFixed *smat, const Material *bmat, const int gamma, const Object *ob, const int new_shading_nodes, 
                                  const bool dimdown)
{
	if (bmat->mode & MA_SHLESS) {
		copy_v3_v3(smat->diff, &bmat->r);
		smat->diff[3] = 1.0;

		if (gamma)
			linearrgb_to_srgb_v3_v3(smat->diff, smat->diff);

		zero_v4(smat->spec);
		smat->hard = 0;
	}
	else if (new_shading_nodes) {
		copy_v3_v3(smat->diff, &bmat->r);
		smat->diff[3] = 1.0;
		
		copy_v3_v3(smat->spec, &bmat->specr);
		smat->spec[3] = 1.0;
		smat->hard = CLAMPIS(bmat->har, 0, 128);
		
		if (dimdown) {
			mul_v3_fl(smat->diff, 0.8f);
			mul_v3_fl(smat->spec, 0.5f);
		}
		
		if (gamma) {
			linearrgb_to_srgb_v3_v3(smat->diff, smat->diff);
			linearrgb_to_srgb_v3_v3(smat->spec, smat->spec);
		}
	}
	else {
		mul_v3_v3fl(smat->diff, &bmat->r, bmat->ref + bmat->emit);
		smat->diff[3] = 1.0; /* caller may set this to bmat->alpha */

		if (bmat->shade_flag & MA_OBCOLOR)
			mul_v3_v3(smat->diff, ob->col);
		
		mul_v3_v3fl(smat->spec, &bmat->specr, bmat->spec);
		smat->spec[3] = 1.0; /* always 1 */
		smat->hard= CLAMPIS(bmat->har, 0, 128);

		if (gamma) {
			linearrgb_to_srgb_v3_v3(smat->diff, smat->diff);
			linearrgb_to_srgb_v3_v3(smat->spec, smat->spec);
		}
	}
}

static Material *gpu_active_node_material(Material *ma)
{
	if (ma && ma->use_nodes && ma->nodetree) {
		bNode *node = nodeGetActiveID(ma->nodetree, ID_MA);

		if (node)
			return (Material *)node->id;
		else
			return NULL;
	}

	return ma;
}

void GPU_begin_object_materials(View3D *v3d, RegionView3D *rv3d, Scene *scene, Object *ob, bool glsl, bool *do_alpha_after)
{
	Material *ma;
	GPUMaterial *gpumat;
	GPUBlendMode alphablend;
	int a;
	const bool gamma = BKE_scene_check_color_management_enabled(scene);
	const bool new_shading_nodes = BKE_scene_use_new_shading_nodes(scene);
	const bool use_matcap = (v3d->flag2 & V3D_SHOW_SOLID_MATCAP) != 0;  /* assumes v3d->defmaterial->preview is set */

#ifdef WITH_GAMEENGINE
	if (rv3d->rflag & RV3D_IS_GAME_ENGINE) {
		ob = BKE_object_lod_matob_get(ob, scene);
	}
#endif

	/* initialize state */
	memset(&GMS, 0, sizeof(GMS));
	GMS.lastmatnr = -1;
	GMS.lastretval = -1;
	GMS.lastalphablend = GPU_BLEND_SOLID;
	GMS.use_matcaps = use_matcap;

	GMS.backface_culling = (v3d->flag2 & V3D_BACKFACE_CULLING) != 0;

	GMS.gob = ob;
	GMS.gscene = scene;
	GMS.totmat = use_matcap ? 1 : ob->totcol + 1;  /* materials start from 1, default material is 0 */
	GMS.glay = (v3d->localvd)? v3d->localvd->lay: v3d->lay; /* keep lamps visible in local view */
	GMS.gscenelock = (v3d->scenelock != 0);
	GMS.gviewmat = rv3d->viewmat;
	GMS.gviewinv = rv3d->viewinv;
	GMS.gviewcamtexcofac = rv3d->viewcamtexcofac;

	/* alpha pass setup. there's various cases to handle here:
	 * - object transparency on: only solid materials draw in the first pass,
	 * and only transparent in the second 'alpha' pass.
	 * - object transparency off: for glsl we draw both in a single pass, and
	 * for solid we don't use transparency at all. */
	GMS.use_alpha_pass = (do_alpha_after != NULL);
	GMS.is_alpha_pass = (v3d->transp != false);
	if (GMS.use_alpha_pass)
		*do_alpha_after = false;
	
	if (GMS.totmat > FIXEDMAT) {
		GMS.matbuf = MEM_callocN(sizeof(GPUMaterialFixed) * GMS.totmat, "GMS.matbuf");
		GMS.gmatbuf = MEM_callocN(sizeof(*GMS.gmatbuf) * GMS.totmat, "GMS.matbuf");
		GMS.alphablend = MEM_callocN(sizeof(*GMS.alphablend) * GMS.totmat, "GMS.matbuf");
	}
	else {
		GMS.matbuf = GMS.matbuf_fixed;
		GMS.gmatbuf = GMS.gmatbuf_fixed;
		GMS.alphablend = GMS.alphablend_fixed;
	}

	/* viewport material, setup in space_view3d, defaults to matcap using ma->preview now */
	if (use_matcap) {
		GMS.gmatbuf[0] = v3d->defmaterial;
		GPU_material_matcap(scene, v3d->defmaterial);

		/* do material 1 too, for displists! */
		memcpy(&GMS.matbuf[1], &GMS.matbuf[0], sizeof(GPUMaterialFixed));
	
		GMS.alphablend[0] = GPU_BLEND_SOLID;
	}
	else {
	
		/* no materials assigned? */
		if (ob->totcol == 0) {
			gpu_material_to_fixed(&GMS.matbuf[0], &defmaterial, 0, ob, new_shading_nodes, true);

			/* do material 1 too, for displists! */
			memcpy(&GMS.matbuf[1], &GMS.matbuf[0], sizeof(GPUMaterialFixed));

			if (glsl) {
				GMS.gmatbuf[0] = &defmaterial;
				GPU_material_from_blender(GMS.gscene, &defmaterial);
			}

			GMS.alphablend[0] = GPU_BLEND_SOLID;
		}
		
		/* setup materials */
		for (a = 1; a <= ob->totcol; a++) {
			/* find a suitable material */
			ma = give_current_material(ob, a);
			if (!glsl && !new_shading_nodes) ma = gpu_active_node_material(ma);
			if (ma == NULL) ma = &defmaterial;

			/* create glsl material if requested */
			gpumat = glsl? GPU_material_from_blender(GMS.gscene, ma): NULL;

			if (gpumat) {
				/* do glsl only if creating it succeed, else fallback */
				GMS.gmatbuf[a] = ma;
				alphablend = GPU_material_alpha_blend(gpumat, ob->col);
			}
			else {
				/* fixed function opengl materials */
				gpu_material_to_fixed(&GMS.matbuf[a], ma, gamma, ob, new_shading_nodes, false);

				if (GMS.use_alpha_pass && ((ma->mode & MA_TRANSP) || (new_shading_nodes && ma->alpha != 1.0f))) {
					GMS.matbuf[a].diff[3] = ma->alpha;
					alphablend = (ma->alpha == 1.0f)? GPU_BLEND_SOLID: GPU_BLEND_ALPHA;
				}
				else {
					GMS.matbuf[a].diff[3] = 1.0f;
					alphablend = GPU_BLEND_SOLID;
				}
			}

			/* setting 'do_alpha_after = true' indicates this object needs to be
			 * drawn in a second alpha pass for improved blending */
			if (do_alpha_after && !GMS.is_alpha_pass)
				if (ELEM(alphablend, GPU_BLEND_ALPHA, GPU_BLEND_ADD, GPU_BLEND_ALPHA_SORT))
					*do_alpha_after = true;

			GMS.alphablend[a] = alphablend;
		}
	}

	/* let's start with a clean state */
	GPU_disable_material();
}

int GPU_enable_material(int nr, void *attribs)
{
	GPUVertexAttribs *gattribs = attribs;
	GPUMaterial *gpumat;
	GPUBlendMode alphablend;

	/* no GPU_begin_object_materials, use default material */
	if (!GMS.matbuf) {
		float diff[4], spec[4];

		memset(&GMS, 0, sizeof(GMS));

		mul_v3_v3fl(diff, &defmaterial.r, defmaterial.ref + defmaterial.emit);
		diff[3] = 1.0;

		mul_v3_v3fl(spec, &defmaterial.specr, defmaterial.spec);
		spec[3] = 1.0;

		glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, diff);
		glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, spec);
		glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 35); /* blender default */

		return 0;
	}

	/* prevent index to use un-initialized array items */
	if (nr >= GMS.totmat)
		nr = 0;

	if (gattribs)
		memset(gattribs, 0, sizeof(*gattribs));

	/* keep current material */
	if (nr == GMS.lastmatnr)
		return GMS.lastretval;

	/* unbind glsl material */
	if (GMS.gboundmat) {
		if (GMS.is_alpha_pass) glDepthMask(0);
		GPU_material_unbind(GPU_material_from_blender(GMS.gscene, GMS.gboundmat));
		GMS.gboundmat = NULL;
	}

	/* draw materials with alpha in alpha pass */
	GMS.lastmatnr = nr;
	GMS.lastretval = 1;

	if (GMS.use_alpha_pass) {
		GMS.lastretval = ELEM(GMS.alphablend[nr], GPU_BLEND_SOLID, GPU_BLEND_CLIP);
		if (GMS.is_alpha_pass)
			GMS.lastretval = !GMS.lastretval;
	}
	else
		GMS.lastretval = !GMS.is_alpha_pass;

	if (GMS.lastretval) {
		/* for alpha pass, use alpha blend */
		alphablend = GMS.alphablend[nr];

		if (gattribs && GMS.gmatbuf[nr]) {
			/* bind glsl material and get attributes */
			Material *mat = GMS.gmatbuf[nr];
			float auto_bump_scale;

			gpumat = GPU_material_from_blender(GMS.gscene, mat);
			GPU_material_vertex_attributes(gpumat, gattribs);
			GPU_material_bind(gpumat, GMS.gob->lay, GMS.glay, 1.0, !(GMS.gob->mode & OB_MODE_TEXTURE_PAINT), GMS.gviewmat, GMS.gviewinv, GMS.gviewcamtexcofac, GMS.gscenelock);

			auto_bump_scale = GMS.gob->derivedFinal != NULL ? GMS.gob->derivedFinal->auto_bump_scale : 1.0f;
			GPU_material_bind_uniforms(gpumat, GMS.gob->obmat, GMS.gob->col, auto_bump_scale);
			GMS.gboundmat = mat;

			/* for glsl use alpha blend mode, unless it's set to solid and
			 * we are already drawing in an alpha pass */
			if (mat->game.alpha_blend != GPU_BLEND_SOLID)
				alphablend= mat->game.alpha_blend;

			if (GMS.is_alpha_pass) glDepthMask(1);

			if (GMS.backface_culling) {
				if (mat->game.flag)
					glEnable(GL_CULL_FACE);
				else
					glDisable(GL_CULL_FACE);
			}

			if (GMS.use_matcaps)
				glColor3f(1.0f, 1.0f, 1.0f);
		}
		else {
			/* or do fixed function opengl material */
			glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, GMS.matbuf[nr].diff);
			glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, GMS.matbuf[nr].spec);
			glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, GMS.matbuf[nr].hard);
		}

		/* set (alpha) blending mode */
		GPU_set_material_alpha_blend(alphablend);
	}

	return GMS.lastretval;
}

void GPU_set_material_alpha_blend(int alphablend)
{
	if (GMS.lastalphablend == alphablend)
		return;
	
	gpu_set_alpha_blend(alphablend);
	GMS.lastalphablend = alphablend;
}

int GPU_get_material_alpha_blend(void)
{
	return GMS.lastalphablend;
}

void GPU_disable_material(void)
{
	GMS.lastmatnr = -1;
	GMS.lastretval = 1;

	if (GMS.gboundmat) {
		if (GMS.backface_culling)
			glDisable(GL_CULL_FACE);

		if (GMS.is_alpha_pass) glDepthMask(0);
		GPU_material_unbind(GPU_material_from_blender(GMS.gscene, GMS.gboundmat));
		GMS.gboundmat = NULL;
	}

	GPU_set_material_alpha_blend(GPU_BLEND_SOLID);
}

void GPU_material_diffuse_get(int nr, float diff[4])
{
	/* prevent index to use un-initialized array items */
	if (nr >= GMS.totmat)
		nr = 0;

	/* no GPU_begin_object_materials, use default material */
	if (!GMS.matbuf) {
		mul_v3_v3fl(diff, &defmaterial.r, defmaterial.ref + defmaterial.emit);
	}
	else {
		copy_v4_v4(diff, GMS.matbuf[nr].diff);
	}
}

bool GPU_material_use_matcaps_get(void)
{
	return GMS.use_matcaps;
}


void GPU_end_object_materials(void)
{
	GPU_disable_material();

	if (GMS.matbuf && GMS.matbuf != GMS.matbuf_fixed) {
		MEM_freeN(GMS.matbuf);
		MEM_freeN(GMS.gmatbuf);
		MEM_freeN(GMS.alphablend);
	}

	GMS.matbuf = NULL;
	GMS.gmatbuf = NULL;
	GMS.alphablend = NULL;

	/* resetting the texture matrix after the scaling needed for tiled textures */
	if (GTS.tilemode) {
		glMatrixMode(GL_TEXTURE);
		glLoadIdentity();
		glMatrixMode(GL_MODELVIEW);
	}
}

/* Lights */

int GPU_default_lights(void)
{
	float zero[4] = {0.0f, 0.0f, 0.0f, 0.0f}, position[4];
	int a, count = 0;
	
	/* initialize */
	if (U.light[0].flag == 0 && U.light[1].flag == 0 && U.light[2].flag == 0) {
		U.light[0].flag = 1;
		U.light[0].vec[0] = -0.3; U.light[0].vec[1] = 0.3; U.light[0].vec[2] = 0.9;
		U.light[0].col[0] = 0.8; U.light[0].col[1] = 0.8; U.light[0].col[2] = 0.8;
		U.light[0].spec[0] = 0.5; U.light[0].spec[1] = 0.5; U.light[0].spec[2] = 0.5;
		U.light[0].spec[3] = 1.0;
		
		U.light[1].flag = 0;
		U.light[1].vec[0] = 0.5; U.light[1].vec[1] = 0.5; U.light[1].vec[2] = 0.1;
		U.light[1].col[0] = 0.4; U.light[1].col[1] = 0.4; U.light[1].col[2] = 0.8;
		U.light[1].spec[0] = 0.3; U.light[1].spec[1] = 0.3; U.light[1].spec[2] = 0.5;
		U.light[1].spec[3] = 1.0;
	
		U.light[2].flag = 0;
		U.light[2].vec[0] = 0.3; U.light[2].vec[1] = -0.3; U.light[2].vec[2] = -0.2;
		U.light[2].col[0] = 0.8; U.light[2].col[1] = 0.5; U.light[2].col[2] = 0.4;
		U.light[2].spec[0] = 0.5; U.light[2].spec[1] = 0.4; U.light[2].spec[2] = 0.3;
		U.light[2].spec[3] = 1.0;
	}

	glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, GL_FALSE);

	for (a = 0; a < 8; a++) {
		if (a < 3) {
			if (U.light[a].flag) {
				glEnable(GL_LIGHT0 + a);

				normalize_v3_v3(position, U.light[a].vec);
				position[3] = 0.0f;
				
				glLightfv(GL_LIGHT0 + a, GL_POSITION, position); 
				glLightfv(GL_LIGHT0 + a, GL_DIFFUSE, U.light[a].col); 
				glLightfv(GL_LIGHT0 + a, GL_SPECULAR, U.light[a].spec); 

				count++;
			}
			else {
				glDisable(GL_LIGHT0 + a);

				glLightfv(GL_LIGHT0 + a, GL_POSITION, zero); 
				glLightfv(GL_LIGHT0 + a, GL_DIFFUSE, zero); 
				glLightfv(GL_LIGHT0 + a, GL_SPECULAR, zero);
			}

			/* clear stuff from other opengl lamp usage */
			glLightf(GL_LIGHT0 + a, GL_SPOT_CUTOFF, 180.0);
			glLightf(GL_LIGHT0 + a, GL_CONSTANT_ATTENUATION, 1.0);
			glLightf(GL_LIGHT0 + a, GL_LINEAR_ATTENUATION, 0.0);
		}
		else
			glDisable(GL_LIGHT0 + a);
	}
	
	glDisable(GL_LIGHTING);

	glDisable(GL_COLOR_MATERIAL);

	return count;
}

int GPU_scene_object_lights(Scene *scene, Object *ob, int lay, float viewmat[4][4], int ortho)
{
	Base *base;
	Lamp *la;
	int count;
	float position[4], direction[4], energy[4];
	
	/* disable all lights */
	for (count = 0; count < 8; count++)
		glDisable(GL_LIGHT0 + count);
	
	/* view direction for specular is not computed correct by default in
	 * opengl, so we set the settings ourselfs */
	glLightModeli(GL_LIGHT_MODEL_LOCAL_VIEWER, ortho ? GL_FALSE : GL_TRUE);

	count = 0;

	for (base = scene->base.first; base; base = base->next) {
		if (base->object->type != OB_LAMP)
			continue;

		if (!(base->lay & lay) || !(base->lay & ob->lay))
			continue;

		la = base->object->data;
		
		/* setup lamp transform */
		glPushMatrix();
		glLoadMatrixf((float *)viewmat);
		
		if (la->type == LA_SUN) {
			/* sun lamp */
			copy_v3_v3(direction, base->object->obmat[2]);
			direction[3] = 0.0;

			glLightfv(GL_LIGHT0+count, GL_POSITION, direction); 
		}
		else {
			/* other lamps with attenuation */
			copy_v3_v3(position, base->object->obmat[3]);
			position[3] = 1.0f;

			glLightfv(GL_LIGHT0+count, GL_POSITION, position); 
			glLightf(GL_LIGHT0+count, GL_CONSTANT_ATTENUATION, 1.0);
			glLightf(GL_LIGHT0+count, GL_LINEAR_ATTENUATION, la->att1 / la->dist);
			glLightf(GL_LIGHT0+count, GL_QUADRATIC_ATTENUATION, la->att2 / (la->dist * la->dist));
			
			if (la->type == LA_SPOT) {
				/* spot lamp */
				negate_v3_v3(direction, base->object->obmat[2]);
				glLightfv(GL_LIGHT0 + count, GL_SPOT_DIRECTION, direction);
				glLightf(GL_LIGHT0 + count, GL_SPOT_CUTOFF, RAD2DEGF(la->spotsize * 0.5f));
				glLightf(GL_LIGHT0 + count, GL_SPOT_EXPONENT, 128.0f * la->spotblend);
			}
			else
				glLightf(GL_LIGHT0 + count, GL_SPOT_CUTOFF, 180.0);
		}
		
		/* setup energy */
		mul_v3_v3fl(energy, &la->r, la->energy);
		energy[3] = 1.0;

		glLightfv(GL_LIGHT0 + count, GL_DIFFUSE, energy); 
		glLightfv(GL_LIGHT0 + count, GL_SPECULAR, energy);
		glEnable(GL_LIGHT0 + count);
		
		glPopMatrix();
		
		count++;
		if (count == 8)
			break;
	}

	return count;
}

static void gpu_multisample(bool enable)
{
	if (GLEW_VERSION_1_3 || GLEW_ARB_multisample) {
#ifdef __linux__
		/* changing multisample from the default (enabled) causes problems on some
		 * systems (NVIDIA/Linux) when the pixel format doesn't have a multisample buffer */
		bool toggle_ok = true;

		if (GPU_type_matches(GPU_DEVICE_NVIDIA, GPU_OS_UNIX, GPU_DRIVER_ANY)) {
			int samples = 0;
			glGetIntegerv(GL_SAMPLES, &samples);

			if (samples == 0)
				toggle_ok = false;
		}

		if (toggle_ok) {
			if (enable)
				glEnable(GL_MULTISAMPLE);
			else
				glDisable(GL_MULTISAMPLE);
		}
#else
		if (enable)
			glEnable(GL_MULTISAMPLE);
		else
			glDisable(GL_MULTISAMPLE);
#endif
	}
}

/* Default OpenGL State */

void GPU_state_init(void)
{
	/* also called when doing opengl rendering and in the game engine */
	float mat_ambient[] = { 0.0, 0.0, 0.0, 0.0 };
	float mat_specular[] = { 0.5, 0.5, 0.5, 1.0 };
	int a, x, y;
	GLubyte pat[32 * 32];
	const GLubyte *patc = pat;
	
	glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT, mat_ambient);
	glMaterialfv(GL_FRONT_AND_BACK, GL_DIFFUSE, mat_specular);
	glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, mat_specular);
	glMateriali(GL_FRONT_AND_BACK, GL_SHININESS, 35);

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

	/* default disabled, enable should be local per function */
	glDisableClientState(GL_VERTEX_ARRAY);
	glDisableClientState(GL_NORMAL_ARRAY);
	glDisableClientState(GL_COLOR_ARRAY);
	glDisableClientState(GL_TEXTURE_COORD_ARRAY);
	
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
	
	a = 0;
	for (x = 0; x < 32; x++) {
		for (y = 0; y < 4; y++) {
			if (x & 1) pat[a++] = 0x88;
			else pat[a++] = 0x22;
		}
	}

	glPolygonStipple(patc);

	glMatrixMode(GL_TEXTURE);
	glLoadIdentity();
	glMatrixMode(GL_MODELVIEW);

	glFrontFace(GL_CCW);
	glCullFace(GL_BACK);
	glDisable(GL_CULL_FACE);

	gpu_multisample(false);
}

