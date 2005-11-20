/**
 * IMB_imbuf_types.h (mar-2001 nzc)
 *
 * Types needed for using the image buffer.
 *
 * Imbuf is external code, slightly adapted to live in the Blender
 * context. It requires an external jpeg module, and the avi-module
 * (also external code) in order to function correctly.
 *
 * This file contains types and some constants that go with them. Most
 * are self-explanatory (e.g. IS_amiga tests whether the buffer
 * contains an Amiga-format file).
 *
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
/**
 * \file IMB_imbuf_types.h
 * \ingroup imbuf
 * \brief Contains defines and structs used throughout the imbuf module.
 * \todo Clean up includes.
 */

#ifndef IMB_IMBUF_TYPES_H
#define IMB_IMBUF_TYPES_H

#include <stdio.h>        /* for size_t */
#include "DNA_listBase.h" /* for ListBase */
struct _AviMovie;
struct Mdec;

/**
 * \brief The basic imbuf type
 * \ingroup imbuf
 * This is the abstraction of an image.  ImBuf is the basic type used for all
 * imbuf operations.
 *
 * REMINDER: if any changes take place, they need to be carried over
 * to source/blender/blenpluginapi/iff.h too, OTHERWISE PLUGINS WON'T
 * WORK CORRECTLY!
 *
 * Also; add new variables to the end to save pain!
 *
 * Also, that iff.h needs to be in the final release "plugins/include" dir, too!
 */
typedef struct ImBuf{
	short	x, y;			/**< width and Height of our image buffer */
	short	skipx;			/**< Width in ints to get to the next scanline */
	unsigned char	depth;		/**< Active amount of bits/bitplanes */
	unsigned char	cbits;		/**< Amount of active bits in cmap */
	unsigned short	mincol;		/**< smallest color in colormap */
	unsigned short	maxcol;		/**< Largest color in colormap */
	int	type;			/**< 0=abgr, 1=bitplanes */
	int	ftype;			/**< File type we are going to save as */
	unsigned int	*cmap;		/**< Color map data. */
	unsigned int	*rect;		/**< pixel values stored here */
	unsigned int	**planes;	/**< bitplanes */
	int	flags;			/**< Controls which components should exist. */
	int	mall;			/**< what is malloced internal, and can be freed */
	short	xorig, yorig;		/**< Cordinates of first pixel of an image used in some formats (example: targa) */
	char	name[1023];		/**< The file name assocated with this image */
	char	namenull;		/**< Unused don't want to remove it thought messes things up */
	int	userflags;		/**< Used to set imbuf to Dirty and other stuff */
	int	*zbuf;			/**< z buffer data */
	void *userdata;	
	unsigned char *encodedbuffer;     /**< Compressed image only used with png currently */
	unsigned int   encodedsize;       /**< Size of data written to encodedbuffer */
	unsigned int   encodedbuffersize; /**< Size of encodedbuffer */
} ImBuf;

/* Moved from BKE_bmfont_types.h because it is a userflag bit mask. */
/**
 * \brief Flags used internally by blender for imagebuffers
 */
typedef enum {
	IB_BITMAPFONT = 1 << 0,		/* This image is a font */
	IB_BITMAPDIRTY = 1 << 1		/* Image needs to be saved is not the same as filename */
} ImBuf_userflagsMask;


/* From iff.h. This was once moved away by Frank, now Nzc moves it
 * back. Such is the way it is... It is a long list of defines, and
 * there are a few external defines in the back. Most of the stuff is
 * probably imbuf_intern only. This will need to be merged later
 * on. */

/**
 * \name Imbuf Component flags
 * \brief These flags determine the components of an ImBuf struct.
 */
/**@{*/
/** \brief Flag defining the components of the ImBuf struct. */
#define IB_rect			(1 << 0)
#define IB_planes		(1 << 1)
#define IB_cmap			(1 << 2)

#define IB_vert			(1 << 4)
#define IB_freem		(1 << 6)
#define IB_test			(1 << 7)

#define IB_ttob			(1 << 8)
#define IB_subdlta		(1 << 9)
#define IB_fields		(1 << 11)
#define IB_zbuf			(1 << 13)

#define IB_mem			(1 << 14)
/**@}*/

/** \name imbuf_formats Image file formats
 * \brief These defines are bit flags for the various image file formats.
 */
/**@{*/
/** \brief Identifier for an image file format.
 *
 * The bit flag is stored in the ImBuf.ftype variable.
 */
#define AMI	        (1 << 31)
#define PNG	        (1 << 30)
#define Anim	        (1 << 29)
#define TGA	        (1 << 28)
#define JPG		(1 << 27)
#define BMP		(1 << 26)
#ifdef WITH_QUICKTIME
#define QUICKTIME	(1 << 25)
#endif
#define RADHDR	(1<<24)

#define RAWTGA	        (TGA | 1)

#define JPG_STD	        (JPG | (0 << 8))
#define JPG_VID	        (JPG | (1 << 8))
#define JPG_JST	        (JPG | (2 << 8))
#define JPG_MAX	        (JPG | (3 << 8))
#define JPG_MSK	        (0xffffff00)

#define AM_ham	        (0x0800 | AMI)
#define AM_hbrite       (0x0080 | AMI)

#define C233	1
#define YUVX	2
#define HAMX	3
#define TANX	4

#define AN_c233			(Anim | C233)
#define AN_yuvx			(Anim | YUVX)
#define AN_hamx			(Anim | HAMX)
#define AN_tanx			(Anim | TANX)
/**@}*/

/** \name Imbuf File Type Tests
 * \brief These macros test if an ImBuf struct is the corresponding file type.
 */
/**@{*/
/** \brief Tests the ImBuf.ftype variable for the file format. */
#define IS_amiga(x)		(x->ftype & AMI)
#define IS_ham(x)		((x->ftype & AM_ham) == AM_ham)
#define IS_hbrite(x)	((x->ftype & AM_hbrite) == AM_hbrite)

#define IS_anim(x)		(x->ftype & Anim)
#define IS_hamx(x)		(x->ftype == AN_hamx)
#define IS_tga(x)		(x->ftype & TGA)
#define IS_png(x)		(x->ftype & PNG)
#define IS_bmp(x)		(x->ftype & BMP)
#define IS_radhdr(x)	(x->ftype & RADHDR)

#define IMAGIC 	0732
#define IS_iris(x)		(x->ftype == IMAGIC)

#define IS_jpg(x)		(x->ftype & JPG)
#define IS_stdjpg(x)	((x->ftype & JPG_MSK) == JPG_STD)
#define IS_vidjpg(x)	((x->ftype & JPG_MSK) == JPG_VID)
#define IS_jstjpg(x)	((x->ftype & JPG_MSK) == JPG_JST)
#define IS_maxjpg(x)	((x->ftype & JPG_MSK) == JPG_MAX)
/**@}*/

#endif

