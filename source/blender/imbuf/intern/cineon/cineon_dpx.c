/**
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	 See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA	02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL LICENSE BLOCK *****
 * cineon.c
 * contributors: joeedh
 * I hearby donate this code and all rights to the Blender Foundation.
 * $Id$
 */
 
#include <stdio.h>
#include <string.h> /*for memcpy*/

#include "logImageLib.h"
#include "cineonlib.h"
#include "dpxlib.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "MEM_guardedalloc.h"

static struct ImBuf *imb_load_dpx_cineon(unsigned char *mem, int use_cineon, int size, int flags)
{
	ImBuf *ibuf;
	LogImageFile *image;
	int x, y;
	unsigned short *row;
	int width, height, depth;
	float *frow;
	
	image = logImageOpenFromMem(mem, size, use_cineon);
	
	if (!image) {
		printf("no image!\n");
		return NULL;
	}
	
	logImageGetSize(image, &width, &height, &depth);
	
	if (depth != 3) { /*need to do greyscale loading eventually.*/
		logImageClose(image);
		return NULL;
	}
	if (width == 0 && height == 0) {
		logImageClose(image);
		return NULL;
	}
	
	ibuf = IMB_allocImBuf(width, height, 32, IB_rectfloat | flags, 0);

	row = MEM_mallocN(sizeof(unsigned short)*width*depth, "row in cineon_dpx.c");
	
	for (y = 0; y < height; y++) {
		unsigned int index = (width) * (height-y-1);
		index = index * 4;
		
		frow = &ibuf->rect_float[index];
		
		logImageGetRowBytes(image, row, y);
		
		for (x=0; x<width; x++) {
			unsigned short *upix = &row[x*depth];
			float *fpix = &frow[x*4];
			fpix[0] = ((float)upix[0]) / 65535.0f;
			fpix[1] = ((float)upix[1]) / 65535.0f;
			fpix[2] = ((float)upix[2]) / 65535.0f;
			fpix[3] = 1.0f;
		}
	}

	MEM_freeN(row);
	logImageClose(image);
	
	if (flags & IB_rect) {
		IMB_rect_from_float(ibuf);
	}
	return ibuf;
}

static int imb_save_dpx_cineon(ImBuf *buf, char *filename, int use_cineon, int flags)
{
	LogImageByteConversionParameters conversion;
	int width, height, depth;
	LogImageFile* logImage;
	unsigned short* line, *pixel;
	int i, j;
	int index;
	float *fline;
	
	conversion.blackPoint = 95;
	conversion.whitePoint = 685;
	conversion.gamma = 1;
	/*
	 * Get the drawable for the current image...
	 */

	width = buf->x;
	height = buf->y;
	depth = 3;
	
	if (!buf->rect_float) return 0;
	
	logImageSetVerbose(0);
	logImage = logImageCreate(filename, use_cineon, width, height, depth);

	if (!logImage) return 0;
	
	logImageSetByteConversion(logImage, &conversion);

	index = 0;
	line = MEM_mallocN(sizeof(unsigned short)*depth*width, "line");
	
	/*note that image is flipped when sent to logImageSetRowBytes (see last passed parameter).*/
	for (j = 0; j < height; ++j) {
		fline = &buf->rect_float[width*j*4];
		for (i=0; i<width; i++) {
			float *fpix, fpix2[3];
			/*we have to convert to cinepaint's 16-bit-per-channel here*/
			pixel = &line[i*depth];
			fpix = &fline[i*4];
			memcpy(fpix2, fpix, sizeof(float)*3);
			
			if (fpix2[0]>=1.0f) fpix2[0] = 1.0f; else if (fpix2[0]<0.0f) fpix2[0]= 0.0f;
			if (fpix2[1]>=1.0f) fpix2[1] = 1.0f; else if (fpix2[1]<0.0f) fpix2[1]= 0.0f;
			if (fpix2[2]>=1.0f) fpix2[2] = 1.0f; else if (fpix2[2]<0.0f) fpix2[2]= 0.0f;
			
			pixel[0] = (unsigned short)(fpix2[0] * 65535.0f); /*float-float math is faster*/
			pixel[1] = (unsigned short)(fpix2[1] * 65535.0f);
			pixel[2] = (unsigned short)(fpix2[2] * 65535.0f);
		}
		logImageSetRowBytes(logImage, (const unsigned short*)line, height-1-j);
	}
	logImageClose(logImage);

	MEM_freeN(line);
	return 1;
}

short imb_savecineon(struct ImBuf *buf, char *myfile, int flags)
{
	return imb_save_dpx_cineon(buf, myfile, 1, flags);
}

 
int imb_is_cineon(void *buf)
{
	return cineonIsMemFileCineon(buf);
}

ImBuf *imb_loadcineon(unsigned char *mem, int size, int flags)
{
	if(imb_is_cineon(mem))
		return imb_load_dpx_cineon(mem, 1, size, flags);
	return NULL;
}

short imb_save_dpx(struct ImBuf *buf, char *myfile, int flags)
{
	return imb_save_dpx_cineon(buf, myfile, 0, flags);
}

short imb_is_dpx(void *buf)
{
	return dpxIsMemFileCineon(buf);
}

ImBuf *imb_loaddpx(unsigned char *mem, int size, int flags)
{
	if(imb_is_dpx(mem))
		return imb_load_dpx_cineon(mem, 0, size, flags);
	return NULL;
}
