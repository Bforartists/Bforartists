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
 * allocimbuf.c
 *
 * $Id$
 */

#include "BLI_blenlib.h"

#include "imbuf.h"
#include "imbuf_patch.h"
#include "IMB_imbuf_types.h"
#include "IMB_imbuf.h"

#include "IMB_amiga.h"
#include "IMB_iris.h"
#include "IMB_targa.h"
#include "IMB_png.h"
#include "IMB_hamx.h"
#include "IMB_jpeg.h"
#include "IMB_bmp.h"

/* actually hard coded endianness */
#define GET_BIG_LONG(x) (((uchar *) (x))[0] << 24 | ((uchar *) (x))[1] << 16 | ((uchar *) (x))[2] << 8 | ((uchar *) (x))[3])
#define GET_LITTLE_LONG(x) (((uchar *) (x))[3] << 24 | ((uchar *) (x))[2] << 16 | ((uchar *) (x))[1] << 8 | ((uchar *) (x))[0])
#define SWAP_L(x) (((x << 24) & 0xff000000) | ((x << 8) & 0xff0000) | ((x >> 8) & 0xff00) | ((x >> 24) & 0xff))
#define SWAP_S(x) (((x << 8) & 0xff00) | ((x >> 8) & 0xff))

/* more endianness... should move to a separate file... */
#if defined(__sgi) || defined (__sparc) || defined(__sparc__) || defined (__PPC__) || defined (__ppc__) || defined (__BIG_ENDIAN__)
#define GET_ID GET_BIG_LONG
#define LITTLE_LONG SWAP_LONG
#else
#define GET_ID GET_LITTLE_LONG
#define LITTLE_LONG ENDIAN_NOP
#endif

/* from misc_util: flip the bytes from x  */
#define GS(x) (((unsigned char *)(x))[0] << 8 | ((unsigned char *)(x))[1])

/* this one is only def-ed once, strangely... */
#define GSS(x) (((uchar *)(x))[1] << 8 | ((uchar *)(x))[0])

int IB_verbose = TRUE;

ImBuf *IMB_ibImageFromMemory(int *mem, int size, int flags) {
	int len;
	struct ImBuf *ibuf;

	if (mem == NULL) {
		printf("Error in ibImageFromMemory: NULL pointer\n");
	} else {
		if ((GS(mem) == IMAGIC) || (GSS(mem) == IMAGIC)){
			return (imb_loadiris((uchar *) mem, flags));
		} else if ((BIG_LONG(mem[0]) & 0xfffffff0) == 0xffd8ffe0) {
			return (imb_ibJpegImageFromMemory((uchar *)mem, size, flags));
		}
		
		if (GET_ID(mem) == CAT){
			mem += 3;
			size -= 4;
			while (size > 0){
				if (GET_ID(mem) == FORM){
					len = ((GET_BIG_LONG(mem+1) + 1) & ~1) + 8;
					if ((GET_ID(mem+2) == ILBM) || (GET_ID(mem+2) == ANIM)) break;
					mem = (int *)((uchar *)mem +len);
					size -= len;
				} else return(0);
			}
		}
	
		if (size > 0){
			if (GET_ID(mem) == FORM){
				if (GET_ID(mem+2) == ILBM){
					return (imb_loadamiga(mem, flags));
				} else if (GET_ID(mem+5) == ILBM){			/* animaties */
					return (imb_loadamiga(mem+3, flags));
				} else if (GET_ID(mem+2) == ANIM){
					return (imb_loadanim(mem, flags));
				}
			}
		}
	
		ibuf = imb_png_decode((uchar *)mem, size, flags);
		if (ibuf) return(ibuf);

		ibuf = imb_bmp_decode((uchar *)mem, size, flags);
		if (ibuf) return(ibuf);

		ibuf = imb_loadtarga((uchar *)mem, flags);
		if (ibuf) return(ibuf);
	
		if (IB_verbose) fprintf(stderr, "Unknown fileformat\n");
	}
	
	return (0);
}


struct ImBuf *IMB_loadiffmem(int *mem, int flags) {
	int len,maxlen;
	struct ImBuf *ibuf;

	// IMB_loadiffmem shouldn't be used anymore in new development
	// it's still here to be backwards compatible...

	maxlen= (GET_BIG_LONG(mem+1) + 1) & ~1;

	if (GET_ID(mem) == CAT){
		mem += 3;
		maxlen -= 4;
		while(maxlen > 0){
			if (GET_ID(mem) == FORM){
				len = ((GET_BIG_LONG(mem+1) + 1) & ~1) + 8;
				if ((GET_ID(mem+2) == ILBM) || (GET_ID(mem+2) == ANIM)) break;
 				mem = (int *)((uchar *)mem +len);
				maxlen -= len;
			} else return(0);
		}
	}

	if (maxlen > 0){
		if (GET_ID(mem) == FORM){
			if (GET_ID(mem+2) == ILBM){
				return (imb_loadamiga(mem, flags));
			} else if (GET_ID(mem+5) == ILBM){			/* animaties */
				return (imb_loadamiga(mem+3, flags));
			} else if (GET_ID(mem+2) == ANIM){
				return (imb_loadanim(mem, flags));
			}
		} else if ((GS(mem) == IMAGIC) || (GSS(mem) == IMAGIC)){
			return (imb_loadiris((uchar *) mem,flags));
		} else if ((BIG_LONG(mem[0]) & 0xfffffff0) == 0xffd8ffe0) {
			return (0);
		}
	}

	ibuf = imb_loadtarga((uchar *) mem,flags);
	if (ibuf) return(ibuf);

	if (IB_verbose) fprintf(stderr,"Unknown fileformat\n");
	return (0);
}

struct ImBuf *IMB_loadifffile(int file, int flags) {
	struct ImBuf *ibuf;
	int size, *mem;

	if (file == -1) return (0);

	size = BLI_filesize(file);

#if defined(AMIGA) || defined(__BeOS) || defined(WIN32)
	mem= (int *)malloc(size);
	if (mem==0) {
		printf("Out of mem\n");
		return (0);
	}

	if (read(file, mem, size)!=size){
		printf("Read Error\n");
		free(mem);
		return (0);
	}

	ibuf = IMB_ibImageFromMemory(mem, size, flags);
	free(mem);

	/* for jpeg read */
	lseek(file, 0L, SEEK_SET);

#else
	mem= (int *)mmap(0,size,PROT_READ,MAP_SHARED,file,0);
	if (mem==(int *)-1){
		printf("Couldn't get mapping\n");
		return (0);
	}

	ibuf = IMB_ibImageFromMemory(mem, size, flags);

	if (munmap( (void *) mem, size)){
		printf("Couldn't unmap file.\n");
	}
#endif
	return(ibuf);
}


struct ImBuf *IMB_loadiffname(char *naam, int flags) {
	int file;
	struct ImBuf *ibuf;
	int buf[1];

	file = open(naam, O_BINARY|O_RDONLY);

	if (file == -1) return (0);

	ibuf= IMB_loadifffile(file, flags);

	if (ibuf == 0) {
		if (read(file, buf, 4) != 4) buf[0] = 0;
		if ((BIG_LONG(buf[0]) & 0xfffffff0) == 0xffd8ffe0)
			ibuf = imb_ibJpegImageFromFilename(naam, flags);			
	}

	if (ibuf) {
		strncpy(ibuf->name, naam, sizeof(ibuf->name));
		if (flags & IB_fields) IMB_de_interlace(ibuf);
	}
	close(file);
	return(ibuf);
}

struct ImBuf *IMB_testiffname(char *naam,int flags) {
	int file;
	struct ImBuf *ibuf;

	flags |= IB_test;
	file = open(naam,O_BINARY|O_RDONLY);

	if (file<=0) return (0);

	ibuf=IMB_loadifffile(file,flags);
	if (ibuf) {
		strncpy(ibuf->name, naam, sizeof(ibuf->name));
	}
	close(file);
	return(ibuf);
}
