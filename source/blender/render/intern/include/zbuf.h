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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * Full recode: 2004-2006 Blender Foundation
 *
 * Contributor(s): none yet.
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#ifndef ZBUF_H
#define ZBUF_H

struct RenderPart;
struct RenderLayer;
struct LampRen;
struct VlakRen;
struct ListBase;

void fillrect(int *rect, int x, int y, int val);

/**
 * Converts a world coordinate into a homogenous coordinate in view
 * coordinates. 
 */
void projectvert(float *v1, float winmat[][4], float *adr);
void projectverto(float *v1, float winmat[][4], float *adr);
int testclip(float *v); 

void set_part_zbuf_clipflag(struct RenderPart *pa);
void zbuffer_shadow(struct Render *re, struct LampRen *lar, int *rectz, int size, float jitx, float jity);
void zbuffer_solid(struct RenderPart *pa, unsigned int layer, short layflag);
unsigned short *zbuffer_transp_shade(struct RenderPart *pa, struct RenderLayer *rl, float *pass);
void convert_zbuf_to_distbuf(struct RenderPart *pa, struct RenderLayer *rl);

typedef struct APixstr {
    unsigned short mask[4]; /* jitter mask */
    int z[4];			/* distance    */
    int p[4];			/* index       */
	short shadfac[4];	/* optimize storage for irregular shadow */
    struct APixstr *next;
} APixstr;

typedef struct APixstrMain
{
	struct APixstrMain *next, *prev;
	struct APixstr *ps;
} APixstrMain;

/* span fill in method, is also used to localize data for zbuffering */
typedef struct ZSpan {
	int rectx, recty;						/* range for clipping */
	
	int miny1, maxy1, miny2, maxy2;			/* actual filled in range */
	float *minp1, *maxp1, *minp2, *maxp2;	/* vertex pointers detect min/max range in */
	float *span1, *span2;
	
	float zmulx, zmuly, zofsx, zofsy;		/* transform from hoco to zbuf co */
	
	int *rectz, *arectz;					/* zbuffers, arectz is for transparant */
	int *rectz1;							/* seconday z buffer for shadowbuffer (2nd closest z) */
	int *rectp;								/* polygon index buffer */
	APixstr *apixbuf, *curpstr;				/* apixbuf for transparent */
	struct ListBase *apsmbase;
	
	int polygon_offset;						/* offset in Z */
	float shad_alpha;						/* copy from material, used by irregular shadbuf */
	int mask, apsmcounter;					/* in use by apixbuf */
	
	void (*zbuffunc)(struct ZSpan *, int, float *, float *, float *, float *);
	void (*zbuflinefunc)(struct ZSpan *, int, float *, float *);
	
} ZSpan;

/* exported to shadbuf.c */
void zbufclip4(struct ZSpan *zspan, int zvlnr, float *f1, float *f2, float *f3, float *f4, int c1, int c2, int c3, int c4);
void zbuf_free_span(struct ZSpan *zspan);

/* to rendercore.c */
void zspan_scanconvert(struct ZSpan *zpan, void *handle, float *v1, float *v2, float *v3, void (*func)(void *, int, int, float, float) );

/* exported to edge render... */
void zbufclip(struct ZSpan *zspan, int zvlnr, float *f1, float *f2, float *f3, int c1, int c2, int c3);
void zbuf_alloc_span(struct ZSpan *zspan, int rectx, int recty);
void zbufclipwire(struct ZSpan *zspan, int zvlnr, struct VlakRen *vlr); 

#endif

