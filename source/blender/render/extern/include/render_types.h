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

#ifndef RENDER_TYPES_H
#define RENDER_TYPES_H

#include "DNA_scene_types.h"
#include "DNA_world_types.h"
#include "DNA_object_types.h"

#define TABLEINITSIZE 1024
#define LAMPINITSIZE 256

/* This is needed to not let VC choke on near and far... old
 * proprietary MS extensions... */
#ifdef WIN32
#undef near
#undef far
#define near clipsta
#define far clipend
#endif

/* ------------------------------------------------------------------------- */

/* localized texture result data */
typedef struct TexResult {
	float tin, tr, tg, tb, ta;
	int talpha;
	float *nor;
} TexResult;

/* localized renderloop data */
typedef struct ShadeInput
{
	struct Material *mat;
	struct VlakRen *vlr;
	float co[3];
	
	/* copy from material, keep synced so we can do memcopy */
	/* current size: 23*4 */
	float r, g, b;
	float specr, specg, specb;
	float mirr, mirg, mirb;
	float ambr, ambb, ambg;
	
	float amb, emit, ang, spectra, ray_mirror;
	float alpha, refl, spec, zoffs, add;
	float translucency;
	/* end direct copy from material */
	
	/* individual copies: */
	int har;
	
	/* texture coordinates */
	float lo[3], gl[3], uv[3], ref[3], orn[3], winco[3], sticky[3], vcol[3], rad[3];
	float vn[3], facenor[3], view[3], refcol[4], displace[3], strand;
	/* dx/dy OSA coordinates */
	float dxco[3], dyco[3];
	float dxlo[3], dylo[3], dxgl[3], dygl[3], dxuv[3], dyuv[3];
	float dxref[3], dyref[3], dxorn[3], dyorn[3];
	float dxno[3], dyno[3], dxview, dyview;
	float dxlv[3], dylv[3];
	float dxwin[3], dywin[3];
	float dxsticky[3], dysticky[3];
	float dxrefract[3], dyrefract[3];
	float dxstrand, dystrand;
	
	float xs, ys;	/* pixel to be rendered */
	short osatex, puno;
	int mask;
	int depth;
	
} ShadeInput;

struct MemArena;

/* here only stuff to initalize the render itself */
typedef struct RE_Render
{
	float grvec[3];
	float imat[3][3];

	float viewmat[4][4], viewinv[4][4];
	float persmat[4][4], persinv[4][4];
	float winmat[4][4];
	
	short flag, osa, rt, pad;
	/**
	 * Screen sizes and positions, in pixels
	 */
	short xstart, xend, ystart, yend, afmx, afmy;
	short rectx;  /* Picture width - 1, normally xend - xstart. */  
	short recty;  /* picture height - 1, normally yend - ystart. */

	/**
	 * Distances and sizes in world coordinates nearvar, farvar were
	 * near and far, but VC in cpp mode chokes on it :( */
	float near;    /* near clip distance */
	float far;     /* far clip distance */
	float ycor, pixsize, viewfac;


	/* These three need to be 'handlerized'. Not an easy task... */
/*  	RE_RenderDataHandle r; */
	RenderData r;
	World wrld;
	ListBase parts;
	
	int totvlak, totvert, tothalo, totlamp;

	/* internal, fortunately */
	struct LampRen **la;
	struct VlakRen **blovl;
	struct VertRen **blove;
	struct HaloRen **bloha;

	/* arena for allocating data for use during render, for
	 * example dynamic TFaces to go in the VlakRen structure.
	 */
	struct MemArena *memArena;

	int *rectaccu;
	int *rectz; /* z buffer: distance buffer */
	unsigned int *rectf1, *rectf2;
	unsigned int *rectot; /* z buffer: face index buffer, recycled as colour buffer! */
	unsigned int *rectspare; /*  */
	/* for 8 byte systems! */
	long *rectdaps;
	float *rectftot;	/* original full color buffer */
	
	short win, winpos, winx, winy, winxof, winyof;
	short winpop, displaymode, sparex, sparey;

	/* Not sure what these do... But they're pointers, so good for handlerization */
	struct Image *backbuf, *frontbuf;
	/* backbuf is an image that drawn as background */
	
} RE_Render;

/* ------------------------------------------------------------------------- */


typedef struct ShadBuf {
	short samp, shadhalostep;
	float persmat[4][4];
	float viewmat[4][4];
	float winmat[4][4];
	float *jit;
	float d,far,pixsize,soft;
	int co[3];
	int size,bias;
	long *zbuf;
	char *cbuf;
} ShadBuf;

/* ------------------------------------------------------------------------- */

typedef struct VertRen
{
	float co[3];
	float n[3];
	float ho[4];
	float rad[3];			/* result radio rendering */
	float *orco;
	float *sticky;
	void *svert;			/* smooth vert, only used during initrender */
	short clip, texofs;		/* texofs= flag */
	float accum;			/* accum for radio weighting, and for strand texco static particles */
	short flag;				/* in use for clipping ztra parts */
} VertRen;

/* ------------------------------------------------------------------------- */

struct halosort {
	struct HaloRen *har;
	int z;
};

/* ------------------------------------------------------------------------- */
struct Material;
struct TFace;

typedef struct RadFace {
	float unshot[3], totrad[3];
	float norm[3], cent[3], area;
	int flag;
} RadFace;

typedef struct VlakRen
{
	struct VertRen *v1, *v2, *v3, *v4;
	unsigned int lay;
	unsigned int raycount;
	float n[3];
	struct Material *mat;
	struct TFace *tface;
	unsigned int *vcol;
	char snproj, puno;
	char flag, ec;
	RadFace *radface;
	Object *ob;
} VlakRen;

/* vlakren->flag is in DNA_scene_types.h */

typedef struct HaloRen
{	
    short miny, maxy;
    float alfa, xs, ys, rad, radsq, sin, cos, co[3], no[3];
	float hard, b, g, r;
    int zs, zd;
    int zBufDist;	/* depth in the z-buffer coordinate system */
    char starpoints, type, add, tex;
    char linec, ringc, seed;
	short flarec; /* used to be a char. why ?*/
    float hasize;
    int pixels;
    unsigned int lay;
    struct Material *mat;
} HaloRen;

struct LampRen;
struct MTex;

/**
 * For each lamp in a scene, a LampRen is created. It determines the
 * properties of a lightsource.
 */
typedef struct LampRen
{
	float xs, ys, dist;
	float co[3];
	short type, mode;
	float r, g, b, k;
	float energy, haint;
	int lay;
	float spotsi,spotbl;
	float vec[3];
	float xsp, ysp, distkw, inpr;
	float halokw, halo;
	float ld1,ld2;

	/* copied from Lamp, to decouple more rendering stuff */
	/** Size of the shadowbuffer */
	short bufsize;
	/** Number of samples for the shadows */
	short samp;
	/** Softness factor for shadow */
	float soft;
	/** shadow plus halo: detail level */
	short shadhalostep;
	/** Near clip of the lamp */
	float clipsta;
	/** Far clip of the lamp */
	float clipend;
	/** A small depth offset to prevent self-shadowing. */
	float bias;
	
	short ray_samp, ray_sampy, ray_sampz, ray_samp_type, area_shape, ray_totsamp;
	short xold1, yold1, xold2, yold2;	/* last jitter table for area lights */
	float area_size, area_sizey, area_sizez;
	
	struct ShadBuf *shb;
	float *jitter;
	
	float imat[3][3];
	float spottexfac;
	float sh_invcampos[3], sh_zfac;	/* sh_= spothalo */
	
	float mat[3][3];	/* 3x3 part from lampmat x viewmat */
	float area[8][3], areasize;
	
	/* yafray: photonlight params */
	int YF_numphotons, YF_numsearch;
	short YF_phdepth, YF_useqmc, YF_bufsize;
	float YF_causticblur, YF_ltradius;
	float YF_glowint, YF_glowofs;
	short YF_glowtype;
	
	/* ray optim */
	VlakRen *vlr_last;
	
	struct MTex *mtex[MAX_MTEX];
} LampRen;


#endif /* RENDER_TYPES_H */

