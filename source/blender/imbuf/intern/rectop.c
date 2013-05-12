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
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * allocimbuf.c
 *
 */

/** \file blender/imbuf/intern/rectop.c
 *  \ingroup imbuf
 */

#include <stdlib.h>

#include "BLI_utildefines.h"
#include "BLI_math_base.h"
#include "BLI_math_color.h"
#include "BLI_math_color_blend.h"
#include "BLI_math_vector.h"

#include "imbuf.h"
#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "IMB_allocimbuf.h"
#include "IMB_colormanagement.h"

void IMB_blend_color_byte(unsigned char dst[4], unsigned char src1[4], unsigned char src2[4], IMB_BlendMode mode)
{
	switch (mode) {
		case IMB_BLEND_MIX:
			blend_color_mix_byte(dst, src1, src2); break;
		case IMB_BLEND_ADD:
			blend_color_add_byte(dst, src1, src2); break;
		case IMB_BLEND_SUB:
			blend_color_sub_byte(dst, src1, src2); break;
		case IMB_BLEND_MUL:
			blend_color_mul_byte(dst, src1, src2); break;
		case IMB_BLEND_LIGHTEN:
			blend_color_lighten_byte(dst, src1, src2); break;
		case IMB_BLEND_DARKEN:
			blend_color_darken_byte(dst, src1, src2); break;
		case IMB_BLEND_ERASE_ALPHA:
			blend_color_erase_alpha_byte(dst, src1, src2); break;
		case IMB_BLEND_ADD_ALPHA:
			blend_color_add_alpha_byte(dst, src1, src2); break;
		default:
			dst[0] = src1[0];
			dst[1] = src1[1];
			dst[2] = src1[2];
			dst[3] = src1[3];
			break;
	}
}

void IMB_blend_color_float(float dst[4], float src1[4], float src2[4], IMB_BlendMode mode)
{
	switch (mode) {
		case IMB_BLEND_MIX:
			blend_color_mix_float(dst, src1, src2); break;
		case IMB_BLEND_ADD:
			blend_color_add_float(dst, src1, src2); break;
		case IMB_BLEND_SUB:
			blend_color_sub_float(dst, src1, src2); break;
		case IMB_BLEND_MUL:
			blend_color_mul_float(dst, src1, src2); break;
		case IMB_BLEND_LIGHTEN:
			blend_color_lighten_float(dst, src1, src2); break;
		case IMB_BLEND_DARKEN:
			blend_color_darken_float(dst, src1, src2); break;
		case IMB_BLEND_ERASE_ALPHA:
			blend_color_erase_alpha_float(dst, src1, src2); break;
		case IMB_BLEND_ADD_ALPHA:
			blend_color_add_alpha_float(dst, src1, src2); break;
		default:
			dst[0] = src1[0];
			dst[1] = src1[1];
			dst[2] = src1[2];
			dst[3] = src1[3];
			break;
	}
}

/* clipping */

void IMB_rectclip(ImBuf *dbuf, ImBuf *sbuf, int *destx, 
                  int *desty, int *srcx, int *srcy, int *width, int *height)
{
	int tmp;

	if (dbuf == NULL) return;
	
	if (*destx < 0) {
		*srcx -= *destx;
		*width += *destx;
		*destx = 0;
	}
	if (*srcx < 0) {
		*destx -= *srcx;
		*width += *srcx;
		*srcx = 0;
	}
	if (*desty < 0) {
		*srcy -= *desty;
		*height += *desty;
		*desty = 0;
	}
	if (*srcy < 0) {
		*desty -= *srcy;
		*height += *srcy;
		*srcy = 0;
	}

	tmp = dbuf->x - *destx;
	if (*width > tmp) *width = tmp;
	tmp = dbuf->y - *desty;
	if (*height > tmp) *height = tmp;

	if (sbuf) {
		tmp = sbuf->x - *srcx;
		if (*width > tmp) *width = tmp;
		tmp = sbuf->y - *srcy;
		if (*height > tmp) *height = tmp;
	}

	if ((*height <= 0) || (*width <= 0)) {
		*width = 0;
		*height = 0;
	}
}

static void imb_rectclip3(ImBuf *dbuf, ImBuf *obuf, ImBuf *sbuf, int *destx, 
                          int *desty, int *origx, int *origy, int *srcx, int *srcy,
                          int *width, int *height)
{
	int tmp;

	if (dbuf == NULL) return;
	
	if (*destx < 0) {
		*srcx -= *destx;
		*origx -= *destx;
		*width += *destx;
		*destx = 0;
	}
	if (*origx < 0) {
		*destx -= *origx;
		*srcx -= *origx;
		*width += *origx;
		*origx = 0;
	}
	if (*srcx < 0) {
		*destx -= *srcx;
		*origx -= *srcx;
		*width += *srcx;
		*srcx = 0;
	}

	if (*desty < 0) {
		*srcy -= *desty;
		*origy -= *desty;
		*height += *desty;
		*desty = 0;
	}
	if (*origy < 0) {
		*desty -= *origy;
		*srcy -= *origy;
		*height += *origy;
		*origy = 0;
	}
	if (*srcy < 0) {
		*desty -= *srcy;
		*origy -= *srcy;
		*height += *srcy;
		*srcy = 0;
	}

	tmp = dbuf->x - *destx;
	if (*width > tmp) *width = tmp;
	tmp = dbuf->y - *desty;
	if (*height > tmp) *height = tmp;

	if (obuf) {
		tmp = obuf->x - *origx;
		if (*width > tmp) *width = tmp;
		tmp = obuf->y - *origy;
		if (*height > tmp) *height = tmp;
	}

	if (sbuf) {
		tmp = sbuf->x - *srcx;
		if (*width > tmp) *width = tmp;
		tmp = sbuf->y - *srcy;
		if (*height > tmp) *height = tmp;
	}

	if ((*height <= 0) || (*width <= 0)) {
		*width = 0;
		*height = 0;
	}
}

/* copy and blend */

void IMB_rectcpy(ImBuf *dbuf, ImBuf *sbuf, int destx, 
                 int desty, int srcx, int srcy, int width, int height)
{
	IMB_rectblend(dbuf, dbuf, sbuf, NULL, NULL, 0, destx, desty, destx, desty, srcx, srcy, width, height, IMB_BLEND_COPY);
}

typedef void (*IMB_blend_func)(unsigned char *dst, const unsigned char *src1, const unsigned char *src2);
typedef void (*IMB_blend_func_float)(float *dst, const float *src1, const float *src2);


void IMB_rectblend(ImBuf *dbuf, ImBuf *obuf, ImBuf *sbuf, unsigned short *dmask,
                   unsigned short *smask, unsigned short mask_max,
                   int destx,  int desty, int origx, int origy, int srcx, int srcy, int width, int height,
                   IMB_BlendMode mode)
{
	unsigned int *drect = NULL, *orect, *srect = NULL, *dr, *or, *sr;
	float *drectf = NULL, *orectf, *srectf = NULL, *drf, *orf, *srf;
	unsigned short *smaskrect = smask, *smr;
	unsigned short *dmaskrect = dmask, *dmr;
	int do_float, do_char, srcskip, destskip, origskip, x;
	IMB_blend_func func = NULL;
	IMB_blend_func_float func_float = NULL;

	if (dbuf == NULL || obuf == NULL) return;

	imb_rectclip3(dbuf, obuf, sbuf, &destx, &desty, &origx, &origy, &srcx, &srcy, &width, &height);

	if (width == 0 || height == 0) return;
	if (sbuf && sbuf->channels != 4) return;
	if (dbuf->channels != 4) return;

	do_char = (sbuf && sbuf->rect && dbuf->rect && obuf->rect);
	do_float = (sbuf && sbuf->rect_float && dbuf->rect_float && obuf->rect_float);

	if (do_char) {
		drect = dbuf->rect + desty * dbuf->x + destx;
		orect = obuf->rect + origy * obuf->x + origx;
	}
	if (do_float) {
		drectf = dbuf->rect_float + (desty * dbuf->x + destx) * 4;
		orectf = obuf->rect_float + (origy * obuf->x + origx) * 4;
	}

	if (dmaskrect)
		dmaskrect += origy * obuf->x + origx;

	destskip = dbuf->x;
	origskip = obuf->x;

	if (sbuf) {
		if (do_char) srect = sbuf->rect + srcy * sbuf->x + srcx;
		if (do_float) srectf = sbuf->rect_float + (srcy * sbuf->x + srcx) * 4;
		srcskip = sbuf->x;

		if (smaskrect)
			smaskrect += srcy * sbuf->x + srcx;
	}
	else {
		srect = drect;
		srectf = drectf;
		srcskip = destskip;
	}

	if (mode == IMB_BLEND_COPY) {
		/* copy */
		for (; height > 0; height--) {
			if (do_char) {
				memcpy(drect, srect, width * sizeof(int));
				drect += destskip;
				srect += srcskip;
			}

			if (do_float) {
				memcpy(drectf, srectf, width * sizeof(float) * 4);
				drectf += destskip * 4;
				srectf += srcskip * 4;
			}
		}
	}
	else if (mode == IMB_BLEND_COPY_RGB) {
		/* copy rgb only */
		for (; height > 0; height--) {
			if (do_char) {
				dr = drect;
				sr = srect;
				for (x = width; x > 0; x--, dr++, sr++) {
					((char *)dr)[0] = ((char *)sr)[0];
					((char *)dr)[1] = ((char *)sr)[1];
					((char *)dr)[2] = ((char *)sr)[2];
				}
				drect += destskip;
				srect += srcskip;
			}

			if (do_float) {
				drf = drectf;
				srf = srectf;
				for (x = width; x > 0; x--, drf += 4, srf += 4) {
					drf[0] = srf[0];
					drf[1] = srf[1];
					drf[2] = srf[2];
				}
				drectf += destskip * 4;
				srectf += srcskip * 4;
			}
		}
	}
	else if (mode == IMB_BLEND_COPY_ALPHA) {
		/* copy alpha only */
		for (; height > 0; height--) {
			if (do_char) {
				dr = drect;
				sr = srect;
				for (x = width; x > 0; x--, dr++, sr++)
					((char *)dr)[3] = ((char *)sr)[3];
				drect += destskip;
				srect += srcskip;
			}

			if (do_float) {
				drf = drectf;
				srf = srectf;
				for (x = width; x > 0; x--, drf += 4, srf += 4)
					drf[3] = srf[3];
				drectf += destskip * 4;
				srectf += srcskip * 4;
			}
		}
	}
	else {
		switch (mode) {
			case IMB_BLEND_MIX:
				func = blend_color_mix_byte;
				func_float = blend_color_mix_float;
				break;
			case IMB_BLEND_ADD:
				func = blend_color_add_byte;
				func_float = blend_color_add_float;
				break;
			case IMB_BLEND_SUB:
				func = blend_color_sub_byte;
				func_float = blend_color_sub_float;
				break;
			case IMB_BLEND_MUL:
				func = blend_color_mul_byte;
				func_float = blend_color_mul_float;
				break;
			case IMB_BLEND_LIGHTEN:
				func = blend_color_lighten_byte;
				func_float = blend_color_lighten_float;
				break;
			case IMB_BLEND_DARKEN:
				func = blend_color_darken_byte;
				func_float = blend_color_darken_float;
				break;
			case IMB_BLEND_ERASE_ALPHA:
				func = blend_color_erase_alpha_byte;
				func_float = blend_color_erase_alpha_float;
				break;
			case IMB_BLEND_ADD_ALPHA:
				func = blend_color_add_alpha_byte;
				func_float = blend_color_add_alpha_float;
				break;
			default:
				break;
		}

		/* blend */
		for (; height > 0; height--) {
			if (do_char) {
				dr = drect;
				or = orect;
				sr = srect;

				if (dmaskrect && smaskrect) {
					/* mask accumulation for painting */
					dmr = dmaskrect;
					smr = smaskrect;

					for (x = width; x > 0; x--, dr++, or++, sr++, dmr++, smr++) {
						unsigned char *src = (unsigned char *)sr;

						if (src[3] && *smr) {
							unsigned short mask = *dmr + (((mask_max - *dmr) * (*smr)) / 65535);

							if (mask > *dmr) {
								unsigned char mask_src[4];

								*dmr = mask;

								mask_src[0] = src[0];
								mask_src[1] = src[1];
								mask_src[2] = src[2];
								mask_src[3] = divide_round_i(src[3] * mask, 65535);

								func((unsigned char *)dr, (unsigned char *)or, mask_src);
							}
						}
					}

					dmaskrect += origskip;
					smaskrect += srcskip;
				}
				else {
					/* regular blending */
					for (x = width; x > 0; x--, dr++, or++, sr++) {
						if (((unsigned char *)sr)[3])
							func((unsigned char *)dr, (unsigned char *)or, (unsigned char *)sr);
					}
				}

				drect += destskip;
				orect += origskip;
				srect += srcskip;
			}

			if (do_float) {
				drf = drectf;
				orf = orectf;
				srf = srectf;

				if (dmaskrect && smaskrect) {
					/* mask accumulation for painting */
					dmr = dmaskrect;
					smr = smaskrect;

					for (x = width; x > 0; x--, drf += 4, orf += 4, srf += 4, dmr++, smr++) {
						if (srf[3] != 0 && *smr) {
							unsigned short mask = *dmr + (((mask_max - *dmr) * (*smr)) / 65535);

							if (mask > *dmr) {
								float mask_srf[4];

								*dmr = mask;
								mul_v4_v4fl(mask_srf, srf, mask * (1.0f / 65535.0f));

								func_float(drf, orf, mask_srf);
							}
						}
					}

					dmaskrect += origskip;
					smaskrect += srcskip;
				}
				else {
					/* regular blending */
					for (x = width; x > 0; x--, drf += 4, orf += 4, srf += 4) {
						if (srf[3] != 0)
							func_float(drf, orf, srf);
					}
				}

				drectf += destskip * 4;
				orectf += origskip * 4;
				srectf += srcskip * 4;
			}
		}
	}
}

/* fill */

void IMB_rectfill(ImBuf *drect, const float col[4])
{
	int num;

	if (drect->rect) {
		unsigned int *rrect = drect->rect;
		char ccol[4];
		
		ccol[0] = (int)(col[0] * 255);
		ccol[1] = (int)(col[1] * 255);
		ccol[2] = (int)(col[2] * 255);
		ccol[3] = (int)(col[3] * 255);
		
		num = drect->x * drect->y;
		for (; num > 0; num--)
			*rrect++ = *((unsigned int *)ccol);
	}
	
	if (drect->rect_float) {
		float *rrectf = drect->rect_float;
		
		num = drect->x * drect->y;
		for (; num > 0; num--) {
			*rrectf++ = col[0];
			*rrectf++ = col[1];
			*rrectf++ = col[2];
			*rrectf++ = col[3];
		}
	}
}


void buf_rectfill_area(unsigned char *rect, float *rectf, int width, int height,
                       const float col[4], struct ColorManagedDisplay *display,
                       int x1, int y1, int x2, int y2)
{
	int i, j;
	float a; /* alpha */
	float ai; /* alpha inverted */
	float aich; /* alpha, inverted, ai/255.0 - Convert char to float at the same time */
	if ((!rect && !rectf) || (!col) || col[3] == 0.0f)
		return;
	
	/* sanity checks for coords */
	CLAMP(x1, 0, width);
	CLAMP(x2, 0, width);
	CLAMP(y1, 0, height);
	CLAMP(y2, 0, height);

	if (x1 > x2) SWAP(int, x1, x2);
	if (y1 > y2) SWAP(int, y1, y2);
	if (x1 == x2 || y1 == y2) return;
	
	a = col[3];
	ai = 1 - a;
	aich = ai / 255.0f;

	if (rect) {
		unsigned char *pixel; 
		unsigned char chr = 0, chg = 0, chb = 0;
		float fr = 0, fg = 0, fb = 0;

		const int alphaint = FTOCHAR(a);
		
		if (a == 1.0f) {
			chr = FTOCHAR(col[0]);
			chg = FTOCHAR(col[1]);
			chb = FTOCHAR(col[2]);
		}
		else {
			fr = col[0] * a;
			fg = col[1] * a;
			fb = col[2] * a;
		}
		for (j = 0; j < y2 - y1; j++) {
			for (i = 0; i < x2 - x1; i++) {
				pixel = rect + 4 * (((y1 + j) * width) + (x1 + i));
				if (pixel >= rect && pixel < rect + (4 * (width * height))) {
					if (a == 1.0f) {
						pixel[0] = chr;
						pixel[1] = chg;
						pixel[2] = chb;
						pixel[3] = 255;
					}
					else {
						int alphatest;
						pixel[0] = (char)((fr + ((float)pixel[0] * aich)) * 255.0f);
						pixel[1] = (char)((fg + ((float)pixel[1] * aich)) * 255.0f);
						pixel[2] = (char)((fb + ((float)pixel[2] * aich)) * 255.0f);
						pixel[3] = (char)((alphatest = ((int)pixel[3] + alphaint)) < 255 ? alphatest : 255);
					}
				}
			}
		}
	}
	
	if (rectf) {
		float col_conv[4];
		float *pixel;

		if (display) {
			copy_v4_v4(col_conv, col);
			IMB_colormanagement_display_to_scene_linear_v3(col_conv, display);
		}
		else {
			srgb_to_linearrgb_v4(col_conv, col);
		}

		for (j = 0; j < y2 - y1; j++) {
			for (i = 0; i < x2 - x1; i++) {
				pixel = rectf + 4 * (((y1 + j) * width) + (x1 + i));
				if (a == 1.0f) {
					pixel[0] = col_conv[0];
					pixel[1] = col_conv[1];
					pixel[2] = col_conv[2];
					pixel[3] = 1.0f;
				}
				else {
					float alphatest;
					pixel[0] = (col_conv[0] * a) + (pixel[0] * ai);
					pixel[1] = (col_conv[1] * a) + (pixel[1] * ai);
					pixel[2] = (col_conv[2] * a) + (pixel[2] * ai);
					pixel[3] = (alphatest = (pixel[3] + a)) < 1.0f ? alphatest : 1.0f;
				}
			}
		}
	}
}

void IMB_rectfill_area(ImBuf *ibuf, const float col[4], int x1, int y1, int x2, int y2, struct ColorManagedDisplay *display)
{
	if (!ibuf) return;
	buf_rectfill_area((unsigned char *) ibuf->rect, ibuf->rect_float, ibuf->x, ibuf->y, col, display,
	                  x1, y1, x2, y2);
}


void IMB_rectfill_alpha(ImBuf *ibuf, const float value)
{
	int i;

	if (ibuf->rect_float && (ibuf->channels == 4)) {
		float *fbuf = ibuf->rect_float + 3;
		for (i = ibuf->x * ibuf->y; i > 0; i--, fbuf += 4) { *fbuf = value; }
	}

	if (ibuf->rect) {
		const unsigned char cvalue = value * 255;
		unsigned char *cbuf = ((unsigned char *)ibuf->rect) + 3;
		for (i = ibuf->x * ibuf->y; i > 0; i--, cbuf += 4) { *cbuf = cvalue; }
	}
}
