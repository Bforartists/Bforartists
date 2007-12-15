/*
 * shadbuf_ext.h
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

#ifndef SHADBUF_EXT_H
#define SHADBUF_EXT_H

#include "render_types.h"

struct ObjectRen;

/**
 * Calculates shadowbuffers for a vector of shadow-giving lamps
 * @param lar The vector of lamps
 */
void makeshadowbuf(struct Render *re, LampRen *lar);
void freeshadowbuf(struct LampRen *lar);

/**
 * Determines the shadow factor for a face and lamp. There is some
 * communication with global variables here.
 * @returns The shadow factors: 1.0 for no shadow, 0.0 for complete
 *          shadow.
 * @param shb The shadowbuffer to find the shadow factor in.
 * @param inp The inproduct between viewvector and ?
 *
 */
float testshadowbuf(struct ShadBuf *shb, float *rco, float *dxco, float *dyco, float inp);	

/**
 * Determines the shadow factor for lamp <lar>, between <p1>
 * and <p2>. (Which CS?)
 */
float shadow_halo(LampRen *lar, float *p1, float *p2);

/**
 * Irregular shadowbuffer
 */

struct MemArena;
struct APixstr;

void ISB_create(RenderPart *pa, struct APixstr *apixbuf);
void ISB_free(RenderPart *pa);
float ISB_getshadow(ShadeInput *shi, ShadBuf *shb);

/* data structures have to be accessible both in camview(x, y) as in lampview(x, y) */
/* since they're created per tile rendered, speed goes over memory requirements */


/* buffer samples, allocated in camera buffer and pointed to in lampbuffer nodes */
typedef struct ISBSample {
	float zco[3];			/* coordinate in lampview projection */
	short *shadfac;			/* initialized zero = full lighted */
	int obi;				/* object for face lookup */
	int facenr;				/* index in faces list */	
} ISBSample;

/* transparent version of buffer sample */
typedef struct ISBSampleA {
	float zco[3];				/* coordinate in lampview projection */
	short *shadfac;				/* NULL = full lighted */
	int obi;					/* object for face lookup */
	int facenr;					/* index in faces list */	
	struct ISBSampleA *next;	/* in end, we want the first items to align with ISBSample */
} ISBSampleA;

/* used for transparent storage only */
typedef struct ISBShadfacA {
	struct ISBShadfacA *next;
	int obi;
	int facenr;
	float shadfac;
} ISBShadfacA;

/* What needs to be stored to evaluate shadow, for each thread in ShadBuf */
typedef struct ISBData {
	short *shadfacs;				/* simple storage for solid only */
	ISBShadfacA **shadfaca;
	struct MemArena *memarena;
	int minx, miny, rectx, recty;	/* copy from part disprect */
} ISBData;

#endif /* SHADBUF_EXT_H */

