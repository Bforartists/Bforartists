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

#ifdef _WIN32
#include "BLI_winstuff.h"
#endif
#include "BLI_blenlib.h"

#include "imbuf.h"
#include "imbuf_patch.h"

#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"
#include "IMB_allocimbuf.h"
#include "IMB_cmap.h"
#include "IMB_bmp.h"

/* some code copied from article on microsoft.com, copied
  here for enhanced BMP support in the future
  http://www.microsoft.com/msj/defaultframe.asp?page=/msj/0197/mfcp1/mfcp1.htm&nav=/msj/0197/newnav.htm
*/

typedef struct BMPINFOHEADER{
	unsigned int	biSize;
	unsigned int	biWidth;
	unsigned int	biHeight;
	unsigned short	biPlanes;
	unsigned short	biBitCount;
	unsigned int	biCompression;
	unsigned int	biSizeImage;
	unsigned int	biXPelsPerMeter;
	unsigned int	biYPelsPerMeter;
	unsigned int	biClrUsed;
	unsigned int	biClrImportant;
} BMPINFOHEADER;

typedef struct BMPHEADER {
	unsigned short biType;
	unsigned int biSize;
	unsigned short biRes1;
	unsigned short biRes2;
	unsigned int biOffBits;
} BMPHEADER;

#define BMP_FILEHEADER_SIZE 14

static int checkbmp(unsigned char *mem)
{
	int ret_val = 0;
	BMPINFOHEADER bmi;
	unsigned int u;

	if (mem) {
		if ((mem[0] == 'B') && (mem[1] == 'M')) {
			/* skip fileheader */
			mem += BMP_FILEHEADER_SIZE;
		} else {
		}

		/* for systems where an int needs to be 4 bytes aligned */
		memcpy(&bmi, mem, sizeof(bmi));

		u = LITTLE_LONG(bmi.biSize);
		/* we only support uncompressed 24 or 32 bits images for now */
		if (u >= sizeof(BMPINFOHEADER)) {
			if ((bmi.biCompression == 0) && (bmi.biClrUsed == 0)) {
				u = LITTLE_SHORT(bmi.biBitCount);
				if (u >= 16) {
					ret_val = 1;
				}
			}
		}
	}

	return(ret_val);
}

int imb_is_a_bmp(void *buf) {
	
	return checkbmp(buf);
}

struct ImBuf *imb_bmp_decode(unsigned char *mem, int size, int flags)
{
	struct ImBuf *ibuf = 0;
	BMPINFOHEADER bmi;
	int x, y, depth, skip, i;
	unsigned char *bmp, *rect;
	unsigned short col;

	if (checkbmp(mem) == 0) return(0);

	if ((mem[0] == 'B') && (mem[1] == 'M')) {
		/* skip fileheader */
		mem += BMP_FILEHEADER_SIZE;
	}

	/* for systems where an int needs to be 4 bytes aligned */
	memcpy(&bmi, mem, sizeof(bmi));

	skip = LITTLE_LONG(bmi.biSize);
	x = LITTLE_LONG(bmi.biWidth);
	y = LITTLE_LONG(bmi.biHeight);
	depth = LITTLE_SHORT(bmi.biBitCount);

	/* printf("skip: %d, x: %d y: %d, depth: %d (%x)\n", skip, x, y, 
		depth, bmi.biBitCount); */
	/* printf("skip: %d, x: %d y: %d, depth: %d (%x)\n", skip, x, y, 
		depth, bmi.biBitCount); */
	if (flags & IB_test) {
		ibuf = IMB_allocImBuf(x, y, depth, 0, 0);
	} else {
		ibuf = IMB_allocImBuf(x, y, depth, IB_rect, 0);
		bmp = mem + skip;
		rect = (unsigned char *) ibuf->rect;

		if (depth == 16) {
			for (i = x * y; i > 0; i--) {
				col = bmp[0] + (bmp[1] << 8);
				rect[0] = ((col >> 10) & 0x1f) << 3;
				rect[1] = ((col >>  5) & 0x1f) << 3;
				rect[2] = ((col >>  0) & 0x1f) << 3;
				
				rect[3] = 255;
				rect += 4; bmp += 2;
			}

		} else if (depth == 24) {
			for (i = x * y; i > 0; i--) {
				rect[0] = bmp[2];
				rect[1] = bmp[1];
				rect[2] = bmp[0];
				
				rect[3] = 255;
				rect += 4; bmp += 3;
			}
		} else if (depth == 32) {
			for (i = x * y; i > 0; i--) {
				rect[0] = bmp[0];
				rect[1] = bmp[1];
				rect[2] = bmp[2];
				rect[3] = bmp[3];
				rect += 4; bmp += 4;
			}
		}
	}

	if (ibuf) {
		ibuf->ftype = BMP;
	}
	
	return(ibuf);
}

/* Couple of helper functions for writing our data */
static int putIntLSB(unsigned int ui,FILE *ofile) { 
	putc((ui>>0)&0xFF,ofile); 
	putc((ui>>8)&0xFF,ofile); 
	putc((ui>>16)&0xFF,ofile); 
	return putc((ui>>24)&0xFF,ofile); 
}

static int putShortLSB(unsigned short us,FILE *ofile) { 
	putc((us>>0)&0xFF,ofile); 
	return putc((us>>8)&0xFF,ofile); 
} 

/* Found write info at http://users.ece.gatech.edu/~slabaugh/personal/c/bitmapUnix.c */
short imb_savebmp(struct ImBuf *ibuf, char *name, int flags) {

	BMPINFOHEADER infoheader;
	int bytesize, extrabytes, x, y, t, ptr;
	uchar *data;
	FILE *ofile;

	extrabytes = (4 - ibuf->x*3 % 4) % 4;
	bytesize = (ibuf->x * 3 + extrabytes) * ibuf->y;

	data = (uchar *) ibuf->rect;
	ofile = fopen(name,"wb");
        if (!ofile) return 0;

	putShortLSB(19778,ofile); /* "BM" */
	putIntLSB(0,ofile); /* This can be 0 for BI_RGB bitmaps */
	putShortLSB(0,ofile); /* Res1 */
	putShortLSB(0,ofile); /* Res2 */
	putIntLSB(BMP_FILEHEADER_SIZE + sizeof(infoheader),ofile); 

	putIntLSB(sizeof(infoheader),ofile);
	putIntLSB(ibuf->x,ofile);
	putIntLSB(ibuf->y,ofile);
	putShortLSB(1,ofile);
	putShortLSB(24,ofile);
	putIntLSB(0,ofile);
	putIntLSB(bytesize + BMP_FILEHEADER_SIZE + sizeof(infoheader),ofile);
	putIntLSB(0,ofile);
	putIntLSB(0,ofile);
	putIntLSB(0,ofile);
	putIntLSB(0,ofile);

	/* Need to write out padded image data in bgr format */
	for (y=0;y<ibuf->y;y++) {
		for (x=0;x<ibuf->x;x++) {
			ptr=(x + y * ibuf->x) * 4;
			if (putc(data[ptr+2],ofile) == EOF) return 0;
			if (putc(data[ptr+1],ofile) == EOF) return 0;
			if (putc(data[ptr],ofile) == EOF) return 0;
		}
		/* add padding here */
		for (t=0;t<extrabytes;t++) if (putc(0,ofile) == EOF) return 0;
	}
	if (ofile) {
		fflush(ofile);
		fclose(ofile);
	}
	return 1;
}
