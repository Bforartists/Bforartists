/**
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
 * iris.c
 *
 * $Id$
 */

#include <string.h>
#include "BLI_blenlib.h"
#include "imbuf.h"
#include "imbuf_patch.h"
#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"
#include "IMB_allocimbuf.h"
#include "IMB_iris.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

typedef struct {
    unsigned short	imagic;		/* stuff saved on disk . . */
    unsigned short 	type;
    unsigned short 	dim;
    unsigned short 	xsize;
    unsigned short 	ysize;
    unsigned short 	zsize;
    unsigned int 	min;
    unsigned int 	max;
    unsigned int	wastebytes;	
    char 		name[80];
    unsigned int	colormap;

    int 		file;		/* stuff used in core only */
    unsigned short 	flags;
    short		dorev;
    short		x;
    short		y;
    short		z;
    short		cnt;
    unsigned short	*ptr;
    unsigned short	*base;
    unsigned short	*tmpbuf;
    unsigned int	offset;
    unsigned int	rleend;		/* for rle images */
    unsigned int	*rowstart;	/* for rle images */
    int			*rowsize;	/* for rle images */
} IMAGE;

#define RINTLUM (79)
#define GINTLUM (156)
#define BINTLUM (21)

#define ILUM(r,g,b)     ((int)(RINTLUM*(r)+GINTLUM*(g)+BINTLUM*(b))>>8)

#define OFFSET_R	0	/* this is byte order dependent */
#define OFFSET_G	1
#define OFFSET_B	2
#define OFFSET_A	3

#define CHANOFFSET(z)	(3-(z))	/* this is byte order dependent */

#define TYPEMASK		0xff00
#define BPPMASK			0x00ff
#define ITYPE_VERBATIM		0x0000
#define ITYPE_RLE		0x0100
#define ISRLE(type)		(((type) & 0xff00) == ITYPE_RLE)
#define ISVERBATIM(type)	(((type) & 0xff00) == ITYPE_VERBATIM)
#define BPP(type)		((type) & BPPMASK)
#define RLE(bpp)		(ITYPE_RLE | (bpp))
#define VERBATIM(bpp)		(ITYPE_VERBATIM | (bpp))
#define	IBUFSIZE(pixels)	((pixels+(pixels>>6))<<2)
#define	RLE_NOP			0x00

/* funcs */
static void readheader(FILE *inf, IMAGE *image);
static int writeheader(FILE *outf, IMAGE *image);

static unsigned short getshort(FILE *inf);
static unsigned int getlong(FILE *inf);
static void putshort(FILE *outf, unsigned short val);
static int putlong(FILE *outf, unsigned int val);
static int writetab(FILE *outf, unsigned int *tab, int len);
static void readtab(FILE *inf, unsigned int *tab, int len);

static void expandrow(unsigned char *optr, unsigned char *iptr, int z);
static void interleaverow(unsigned char *lptr, unsigned char *cptr, int z, int n);
static int compressrow(unsigned char *lbuf, unsigned char *rlebuf, int z, int cnt);
static void lumrow(unsigned char *rgbptr, unsigned char *lumptr, int n);

/* not used... */
/*  static void copybw(int *lptr, int n); */
/*  static void setalpha(unsigned char *lptr, int n); */

/*
 *	byte order independent read/write of shorts and ints.
 *
 */

static uchar * file_data;
static int file_offset;

static unsigned short getshort(FILE *inf)
{
	unsigned char * buf;
	
	buf = file_data + file_offset;
	file_offset += 2;
	
	return (buf[0]<<8)+(buf[1]<<0);
}

static unsigned int getlong(FILE *inf)
{
	unsigned char * buf;
	
	buf = file_data + file_offset;
	file_offset += 4;
	
	return (buf[0]<<24)+(buf[1]<<16)+(buf[2]<<8)+(buf[3]<<0);
}

static void putshort(FILE *outf, unsigned short val)
{
	unsigned char buf[2];

	buf[0] = (val>>8);
	buf[1] = (val>>0);
	fwrite(buf,2,1,outf);
}

static int putlong(FILE *outf, unsigned int val)
{
	unsigned char buf[4];

	buf[0] = (val>>24);
	buf[1] = (val>>16);
	buf[2] = (val>>8);
	buf[3] = (val>>0);
	return fwrite(buf,4,1,outf);
}

static void readheader(FILE *inf, IMAGE *image)
{
	memset(image, 0, sizeof(IMAGE));
	image->imagic = getshort(inf);
	image->type = getshort(inf);
	image->dim = getshort(inf);
	image->xsize = getshort(inf);
	image->ysize = getshort(inf);
	image->zsize = getshort(inf);
}

static int writeheader(FILE *outf, IMAGE *image)
{
	IMAGE t;

	memset(&t, 0, sizeof(IMAGE));
	fwrite(&t,sizeof(IMAGE),1,outf);
	fseek(outf,0,SEEK_SET);
	putshort(outf,image->imagic);
	putshort(outf,image->type);
	putshort(outf,image->dim);
	putshort(outf,image->xsize);
	putshort(outf,image->ysize);
	putshort(outf,image->zsize);
	putlong(outf,image->min);
	putlong(outf,image->max);
	putlong(outf,0);
	return fwrite("no name",8,1,outf);
}

static int writetab(FILE *outf, unsigned int *tab, int len)
{
	int r = 0;

	while(len) {
		r = putlong(outf,*tab++);
		len -= 4;
	}
	return r;
}

static void readtab(FILE *inf, unsigned int *tab, int len)
{
	while(len) {
		*tab++ = getlong(inf);
		len -= 4;
	}
}

static void test_endian_zbuf(struct ImBuf *ibuf)
{
	int len;
	int *zval;
	
	if( BIG_LONG(1) == 1 ) return;
	if(ibuf->zbuf==0) return;
	
	len= ibuf->x*ibuf->y;
	zval= ibuf->zbuf;
	
	while(len--) {
		zval[0]= BIG_LONG(zval[0]);
		zval++;
	}
}


/*
 *	longimagedata - 
 *		read in a B/W RGB or RGBA iris image file and return a 
 *	pointer to an array of ints.
 *
 */

struct ImBuf *imb_loadiris(unsigned char *mem, int flags)
{
	unsigned int *base, *lptr;
	unsigned int *zbase, *zptr;
	unsigned char *rledat;
	int *starttab, *lengthtab;
	FILE *inf;
	IMAGE image;
	int x, y, z, tablen;
	int xsize, ysize, zsize;
	int bpp, rle, cur, badorder;
	ImBuf * ibuf;
	uchar * rect;
	
	/*printf("new iris\n");*/
	
	file_data = mem;
	file_offset = 0;
	
	readheader(inf, &image);
	if(image.imagic != IMAGIC) {
		fprintf(stderr,"longimagedata: bad magic number in image file\n");
		return(0);
	}
	
	rle = ISRLE(image.type);
	bpp = BPP(image.type);
	if(bpp != 1 ) {
		fprintf(stderr,"longimagedata: image must have 1 byte per pix chan\n");
		return(0);
	}
	
	xsize = image.xsize;
	ysize = image.ysize;
	zsize = image.zsize;
	
	if (flags & IB_test) {
		ibuf = IMB_allocImBuf(image.xsize, image.ysize, 8 * image.zsize, 0, 0);
		if (ibuf) ibuf->ftype = IMAGIC;
		return(ibuf);
	}
	
	if (rle) {
		tablen = ysize*zsize*sizeof(int);
		starttab = (int *)malloc(tablen);
		lengthtab = (int *)malloc(tablen);
		file_offset = 512;
		
		readtab(inf,starttab,tablen);
		readtab(inf,lengthtab,tablen);

		/* check data order */
		cur = 0;
		badorder = 0;
		for (y = 0; y<ysize; y++) {
			for (z = 0; z<zsize; z++) {
				if (starttab[y+z*ysize]<cur) {
					badorder = 1;
					break;
				}
				cur = starttab[y+z*ysize];
			}
			if(badorder)
				break;
		}

		ibuf = IMB_allocImBuf(xsize, ysize, 8 * zsize, IB_rect, 0);
		if (ibuf->depth > 32) ibuf->depth = 32;
		base = ibuf->rect;
		zbase = (unsigned int *)ibuf->zbuf;
		
		if (badorder) {
			for(z=0; z<zsize; z++) {
				lptr = base;
				for(y=0; y<ysize; y++) {
					file_offset = starttab[y+z*ysize];
					
					rledat = file_data + file_offset;
					file_offset += lengthtab[y+z*ysize];
					
					expandrow((uchar *)lptr, rledat, 3-z);
					lptr += xsize;
				}
			}
		}
		else {
			lptr = base;
			zptr = zbase;
			for(y=0; y<ysize; y++) {
			
				for(z=0; z<zsize; z++) {
					
					file_offset = starttab[y+z*ysize];

					rledat = file_data + file_offset;
					file_offset += lengthtab[y+z*ysize];
					
					if(z<4) expandrow((uchar *)lptr, rledat, 3-z);
					else if(z<8) expandrow((uchar *)zptr, rledat, 7-z);
				}
				lptr += xsize;
				zptr += xsize;
			}
		}
		
		free(starttab);
		free(lengthtab);
	} 
	else {
	
		ibuf = IMB_allocImBuf(xsize, ysize, 8 * zsize, IB_rect, 0);
		if (ibuf->depth > 32) ibuf->depth = 32;

		base = ibuf->rect;
		zbase = (unsigned int *)ibuf->zbuf;
		
		file_offset = 512;
		rledat = file_data + file_offset;
		
		for(z = 0; z < zsize; z++) {
			
			if(z<4) lptr = base;
			else if(z<8) lptr= zbase;
			
			for(y = 0; y < ysize; y++) {

				interleaverow((uchar *)lptr, rledat, 3-z, xsize);
				rledat += xsize;
				
				lptr += xsize;
			}
		}
	}
	
	if (image.zsize == 1){
		rect = (uchar *) ibuf->rect;
		for (x = ibuf->x * ibuf->y; x > 0; x--) {
			rect[0] = 255;
			rect[1] = rect[2] = rect[3];
			rect += 4;
		}
        } else if (image.zsize == 2){
                /* grayscale with alpha */
                rect = (uchar *) ibuf->rect;
                for (x = ibuf->x * ibuf->y; x > 0; x--) {
                        rect[0] = rect[2];
                        rect[1] = rect[2] = rect[3];
                        rect += 4;
                }
	} else if (image.zsize == 3){
		/* add alpha */
		rect = (uchar *) ibuf->rect;
		for (x = ibuf->x * ibuf->y; x > 0; x--) {
			rect[0] = 255;
			rect += 4;
		}
	}
	
	ibuf->ftype = IMAGIC;
	if (flags & IB_ttob) IMB_flipy(ibuf);
	
	test_endian_zbuf(ibuf);
	
	if (ibuf) {
		if (ibuf->rect) 
			IMB_convert_rgba_to_abgr(ibuf->x*ibuf->y, ibuf->rect);
	}

	return(ibuf);
}

/* static utility functions for longimagedata */

static void interleaverow(unsigned char *lptr, unsigned char *cptr, int z, int n)
{
	lptr += z;
	while(n--) {
		*lptr = *cptr++;
		lptr += 4;
	}
}

/* not used? */
/*static void copybw(int *lptr, int n) */
/*  int *lptr; */
/*  int n; */
/*{
	while(n>=8) {
		lptr[0] = 0xff000000+(0x010101*(lptr[0]&0xff));
		lptr[1] = 0xff000000+(0x010101*(lptr[1]&0xff));
		lptr[2] = 0xff000000+(0x010101*(lptr[2]&0xff));
		lptr[3] = 0xff000000+(0x010101*(lptr[3]&0xff));
		lptr[4] = 0xff000000+(0x010101*(lptr[4]&0xff));
		lptr[5] = 0xff000000+(0x010101*(lptr[5]&0xff));
		lptr[6] = 0xff000000+(0x010101*(lptr[6]&0xff));
		lptr[7] = 0xff000000+(0x010101*(lptr[7]&0xff));
		lptr += 8;
		n-=8;
	}
	while(n--) {
		*lptr = 0xff000000+(0x010101*(*lptr&0xff));
		lptr++;
	}
}
*/

/* not used ? */
/*static void setalpha(unsigned char *lptr, int n)*/
/*  unsigned char *lptr; */
/*{
	while(n>=8) {
		lptr[0*4] = 0xff;
		lptr[1*4] = 0xff;
		lptr[2*4] = 0xff;
		lptr[3*4] = 0xff;
		lptr[4*4] = 0xff;
		lptr[5*4] = 0xff;
		lptr[6*4] = 0xff;
		lptr[7*4] = 0xff;
		lptr += 4*8;
		n -= 8;
	}
	while(n--) {
		*lptr = 0xff;
		lptr += 4;
	}
}
*/

static void expandrow(unsigned char *optr, unsigned char *iptr, int z)
{
	unsigned char pixel, count;

	optr += z;
	while(1) {
		pixel = *iptr++;
		if ( !(count = (pixel & 0x7f)) )
			return;
		if(pixel & 0x80) {
			while(count>=8) {
				optr[0*4] = iptr[0];
				optr[1*4] = iptr[1];
				optr[2*4] = iptr[2];
				optr[3*4] = iptr[3];
				optr[4*4] = iptr[4];
				optr[5*4] = iptr[5];
				optr[6*4] = iptr[6];
				optr[7*4] = iptr[7];
				optr += 8*4;
				iptr += 8;
				count -= 8;
			}
			while(count--) {
				*optr = *iptr++;
				optr+=4;
			}
		} else {
			pixel = *iptr++;
			while(count>=8) {
				optr[0*4] = pixel;
				optr[1*4] = pixel;
				optr[2*4] = pixel;
				optr[3*4] = pixel;
				optr[4*4] = pixel;
				optr[5*4] = pixel;
				optr[6*4] = pixel;
				optr[7*4] = pixel;
				optr += 8*4;
				count -= 8;
			}
			while(count--) {
				*optr = pixel;
				optr+=4;
			}
		}
	}
}

/*
 *	output_iris -
 *		copy an array of ints to an iris image file.  Each int
 *	represents one pixel.  xsize and ysize specify the dimensions of
 *	the pixel array.  zsize specifies what kind of image file to
 *	write out.  if zsize is 1, the luminance of the pixels are
 *	calculated, and a sinlge channel black and white image is saved.
 *	If zsize is 3, an RGB image file is saved.  If zsize is 4, an
 *	RGBA image file is saved.
 *
 *  Added: zbuf write
 */

static int output_iris(unsigned int *lptr, int xsize, int ysize, int zsize, int file, int *zptr)
{
	FILE *outf;
	IMAGE *image;
	int tablen, y, z, pos, len = 0;
	int *starttab, *lengthtab;
	unsigned char *rlebuf;
	unsigned int *lumbuf;
	int rlebuflen, goodwrite;

	goodwrite = 1;
	outf = fdopen(file, "wb");

	if(!outf) {
		perror("fdopen");
		fprintf(stderr,"output_iris: can't open output file\n");
		return 0;
	}
	tablen = ysize*zsize*sizeof(int);

	image = (IMAGE *)malloc(sizeof(IMAGE));
	starttab = (int *)malloc(tablen);
	lengthtab = (int *)malloc(tablen);
	rlebuflen = 1.05*xsize+10;
	rlebuf = (unsigned char *)malloc(rlebuflen);
	lumbuf = (unsigned int *)malloc(xsize*sizeof(int));

	memset(image, 0, sizeof(IMAGE));
	image->imagic = IMAGIC;
	image->type = RLE(1);
	if(zsize>1)
		image->dim = 3;
	else
		image->dim = 2;
	image->xsize = xsize;
	image->ysize = ysize;
	image->zsize = zsize;
	image->min = 0;
	image->max = 255;
	goodwrite *= writeheader(outf,image);
	fseek(outf,512+2*tablen,SEEK_SET);
	pos = 512+2*tablen;
	
	for (y = 0; y < ysize; y++) {
		for (z = 0; z < zsize; z++) {
			
			if (zsize == 1) {
				lumrow((uchar *)lptr,(uchar *)lumbuf,xsize);
				len = compressrow((uchar *)lumbuf,rlebuf,CHANOFFSET(z),xsize);
			}
			else {
				if(z<4) {
					len = compressrow((uchar *)lptr, rlebuf,CHANOFFSET(z),xsize);
				}
				else if(z<8 && zptr) {
					len = compressrow((uchar *)zptr, rlebuf,CHANOFFSET(z-4),xsize);
				}
			}
			if(len>rlebuflen) {
				fprintf(stderr,"output_iris: rlebuf is too small - bad poop\n");
				exit(1);
			}
			goodwrite *= fwrite(rlebuf, len, 1, outf);
			starttab[y+z*ysize] = pos;
			lengthtab[y+z*ysize] = len;
			pos += len;
		}
		lptr += xsize;
		if(zptr) zptr += xsize;
	}

	fseek(outf,512,SEEK_SET);
	goodwrite *= writetab(outf,starttab,tablen);
	goodwrite *= writetab(outf,lengthtab,tablen);
	free(image);
	free(starttab);
	free(lengthtab);
	free(rlebuf);
	free(lumbuf);
	fclose(outf);
	if(goodwrite)
		return 1;
	else {
		fprintf(stderr,"output_iris: not enough space for image!!\n");
		return 0;
	}
}

/* static utility functions for output_iris */

static void lumrow(unsigned char *rgbptr, unsigned char *lumptr, int n)
{
	lumptr += CHANOFFSET(0);
	while(n--) {
		*lumptr = ILUM(rgbptr[OFFSET_R],rgbptr[OFFSET_G],rgbptr[OFFSET_B]);
		lumptr += 4;
		rgbptr += 4;
	}
}

static int compressrow(unsigned char *lbuf, unsigned char *rlebuf, int z, int cnt)
{
	unsigned char *iptr, *ibufend, *sptr, *optr;
	short todo, cc;
	int count;

	lbuf += z;
	iptr = lbuf;
	ibufend = iptr+cnt*4;
	optr = rlebuf;

	while(iptr<ibufend) {
		sptr = iptr;
		iptr += 8;
		while((iptr<ibufend)&& ((iptr[-8]!=iptr[-4])||(iptr[-4]!=iptr[0])))
			iptr+=4;
		iptr -= 8;
		count = (iptr-sptr)/4;
		while(count) {
			todo = count>126 ? 126:count;
			count -= todo;
			*optr++ = 0x80|todo;
			while(todo>8) {
				optr[0] = sptr[0*4];
				optr[1] = sptr[1*4];
				optr[2] = sptr[2*4];
				optr[3] = sptr[3*4];
				optr[4] = sptr[4*4];
				optr[5] = sptr[5*4];
				optr[6] = sptr[6*4];
				optr[7] = sptr[7*4];

				optr += 8;
				sptr += 8*4;
				todo -= 8;
			}
			while(todo--) {
				*optr++ = *sptr;
				sptr += 4;
			}
		}
		sptr = iptr;
		cc = *iptr;
		iptr += 4;
		while( (iptr<ibufend) && (*iptr == cc) )
			iptr += 4;
		count = (iptr-sptr)/4;
		while(count) {
			todo = count>126 ? 126:count;
			count -= todo;
			*optr++ = todo;
			*optr++ = cc;
		}
	}
	*optr++ = 0;
	return optr - (unsigned char *)rlebuf;
}

short imb_saveiris(struct ImBuf * ibuf, int file, int flags)
{
	short zsize;
	int ret;

	zsize = (ibuf->depth + 7) >> 3;
	if (flags & IB_zbuf &&  ibuf->zbuf != 0) zsize = 8;
	
	IMB_convert_rgba_to_abgr(ibuf->x*ibuf->y, ibuf->rect);
	test_endian_zbuf(ibuf);

	ret = output_iris(ibuf->rect, ibuf->x, ibuf->y, zsize, file, ibuf->zbuf);

	/* restore! Quite clumsy, 2 times a switch... maybe better a malloc ? */
	IMB_convert_rgba_to_abgr(ibuf->x*ibuf->y, ibuf->rect);
	test_endian_zbuf(ibuf);

	return(ret);
}

