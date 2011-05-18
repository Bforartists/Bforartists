/*
 * $Id$
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
 */
#ifndef DNA_ID_H
#define DNA_ID_H

/** \file DNA_ID.h
 *  \ingroup DNA
 *  \brief ID and Library types, which are fundamental for sdna.
 */

#include "DNA_listBase.h"

#ifdef __cplusplus
extern "C" {
#endif

struct Library;
struct FileData;
struct ID;

typedef struct IDPropertyData {
	void *pointer;
	ListBase group;
	int val, val2; /*note, we actually fit a double into these two ints*/
} IDPropertyData;

typedef struct IDProperty {
	struct IDProperty *next, *prev;
	char type, subtype;
	short flag;
	char name[32];
	int saved; /*saved is used to indicate if this struct has been saved yet.
				seemed like a good idea as a pad var was needed anyway :)*/
	IDPropertyData data;	/* note, alignment for 64 bits */
	int len; /* array length, also (this is important!) string length + 1.
				the idea is to be able to reuse array realloc functions on strings.*/
	/*totallen is total length of allocated array/string, including a buffer.
	  Note that the buffering is mild; the code comes from python's list implementation.*/
	int totallen; /*strings and arrays are both buffered, though the buffer isn't
					saved.*/
} IDProperty;

#define MAX_IDPROP_NAME	32
#define DEFAULT_ALLOC_FOR_NULL_STRINGS	64

/*->type*/
#define IDP_STRING		0
#define IDP_INT			1
#define IDP_FLOAT		2
#define IDP_ARRAY		5
#define IDP_GROUP		6
/* the ID link property type hasn't been implemented yet, this will require
   some cleanup of blenkernel, most likely.*/
#define IDP_ID			7
#define IDP_DOUBLE		8
#define IDP_IDPARRAY	9
#define IDP_NUMTYPES	10

/* add any future new id property types here.*/

/* watch it: Sequence has identical beginning. */
/**
 * ID is the first thing included in all serializable types. It
 * provides a common handle to place all data in double-linked lists.
 * */

#define MAX_ID_NAME	24

/* There's a nasty circular dependency here.... void* to the rescue! I
 * really wonder why this is needed. */
typedef struct ID {
	void *next, *prev;
	struct ID *newid;
	struct Library *lib;
	char name[24];
	short us;
	/**
	 * LIB_... flags report on status of the datablock this ID belongs
	 * to.
	 */
	short flag;
	int icon_id;
	IDProperty *properties;
} ID;

/**
 * For each library file used, a Library struct is added to Main
 * WARNING: readfile.c, expand_doit() reads this struct without DNA check!
 */
typedef struct Library {
	ID id;
	ID *idblock;
	struct FileData *filedata;
	char name[240];			/* path name used for reading, can be relative and edited in the outliner */
	char filepath[240];		/* temp. absolute filepath, only used while reading */
	int tot, pad;			/* tot, idblock and filedata are only fo read and write */
	struct Library *parent;	/* set for indirectly linked libs, used in the outliner and while reading */
} Library;

enum eIconSizes {
	ICON_SIZE_ICON,
	ICON_SIZE_PREVIEW,
};
#define NUM_ICON_SIZES (ICON_SIZE_PREVIEW + 1)

typedef struct PreviewImage {
	/* All values of 2 are really NUM_ICON_SIZES */
	unsigned int w[2];
	unsigned int h[2];
	short changed[2];
	short changed_timestamp[2];
	unsigned int * rect[2];
} PreviewImage;

/**
 * Defines for working with IDs.
 *
 * The tags represent types! This is a dirty way of enabling RTTI. The
 * sig_byte end endian defines aren't really used much.
 *
 **/

#if defined(__sgi) || defined(__sparc) || defined(__sparc__) || defined (__PPC__) || defined (__ppc__)  || defined (__hppa__) || defined (__BIG_ENDIAN__)
/* big endian */
#define MAKE_ID2(c, d)		( (c)<<8 | (d) )
#define MOST_SIG_BYTE				0
#define BBIG_ENDIAN
#else
/* little endian  */
#define MAKE_ID2(c, d)		( (d)<<8 | (c) )
#define MOST_SIG_BYTE				1
#define BLITTLE_ENDIAN
#endif

/* ID from database */
#define ID_SCE		MAKE_ID2('S', 'C') /* Scene */
#define ID_LI		MAKE_ID2('L', 'I') /* Library */
#define ID_OB		MAKE_ID2('O', 'B') /* Object */
#define ID_ME		MAKE_ID2('M', 'E') /* Mesh */
#define ID_CU		MAKE_ID2('C', 'U') /* Curve */
#define ID_MB		MAKE_ID2('M', 'B') /* MetaBall */
#define ID_MA		MAKE_ID2('M', 'A') /* Material */
#define ID_TE		MAKE_ID2('T', 'E') /* Texture */
#define ID_IM		MAKE_ID2('I', 'M') /* Image */
#define ID_LT		MAKE_ID2('L', 'T') /* Lattice */
#define ID_LA		MAKE_ID2('L', 'A') /* Lamp */
#define ID_CA		MAKE_ID2('C', 'A') /* Camera */
#define ID_IP		MAKE_ID2('I', 'P') /* Ipo (depreciated, replaced by FCurves) */
#define ID_KE		MAKE_ID2('K', 'E') /* Key (shape key) */
#define ID_WO		MAKE_ID2('W', 'O') /* World */
#define ID_SCR		MAKE_ID2('S', 'R') /* Screen */
#define ID_SCRN		MAKE_ID2('S', 'N') /* (depreciated?) */
#define ID_VF		MAKE_ID2('V', 'F') /* VectorFont */
#define ID_TXT		MAKE_ID2('T', 'X') /* Text */
#define ID_SO		MAKE_ID2('S', 'O') /* Sound */
#define ID_GR		MAKE_ID2('G', 'R') /* Group */
#define ID_ID		MAKE_ID2('I', 'D') /* (internal use only) */
#define ID_AR		MAKE_ID2('A', 'R') /* Armature */
#define ID_AC		MAKE_ID2('A', 'C') /* Action */
#define ID_SCRIPT	MAKE_ID2('P', 'Y') /* Script (depreciated) */
#define ID_NT		MAKE_ID2('N', 'T') /* NodeTree */
#define ID_BR		MAKE_ID2('B', 'R') /* Brush */
#define ID_PA		MAKE_ID2('P', 'A') /* ParticleSettings */
#define ID_GD		MAKE_ID2('G', 'D') /* GreasePencil */
#define ID_WM		MAKE_ID2('W', 'M') /* WindowManager */

	/* NOTE! Fake IDs, needed for g.sipo->blocktype or outliner */
#define ID_SEQ		MAKE_ID2('S', 'Q')
			/* constraint */
#define ID_CO		MAKE_ID2('C', 'O')
			/* pose (action channel, used to be ID_AC in code, so we keep code for backwards compat) */
#define ID_PO		MAKE_ID2('A', 'C')
			/* used in outliner... */
#define ID_NLA		MAKE_ID2('N', 'L')
			/* fluidsim Ipo */
#define ID_FLUIDSIM	MAKE_ID2('F', 'S')

#define ID_REAL_USERS(id) (((ID *)id)->us - ((((ID *)id)->flag & LIB_FAKEUSER) ? 1:0))

#ifdef GS
#undef GS
#endif
#define GS(a)	(*((short *)(a)))

/* id->flag: set frist 8 bits always at zero while reading */
#define LIB_LOCAL		0
#define LIB_EXTERN		1
#define LIB_INDIRECT	2
#define LIB_TEST		8
#define LIB_TESTEXT		(LIB_TEST | LIB_EXTERN)
#define LIB_TESTIND		(LIB_TEST | LIB_INDIRECT)
#define LIB_READ		16
#define LIB_NEEDLINK	32

#define LIB_NEW			256
#define LIB_FAKEUSER	512
/* free test flag */
#define LIB_DOIT		1024
/* tag existing data before linking so we know what is new */
#define LIB_PRE_EXISTING	2048
/* runtime */
#define LIB_ID_RECALC		4096
#define LIB_ID_RECALC_DATA	8192

#ifdef __cplusplus
}
#endif

#endif

