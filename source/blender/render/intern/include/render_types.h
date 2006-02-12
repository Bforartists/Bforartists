/**
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
 * Contributor(s): (c) 2006 Blender Foundation, full refactor
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef RENDER_TYPES_H
#define RENDER_TYPES_H

/* ------------------------------------------------------------------------- */
/* exposed internal in render module only! */
/* ------------------------------------------------------------------------- */

#include "DNA_scene_types.h"
#include "DNA_world_types.h"
#include "DNA_object_types.h"
#include "DNA_vec_types.h"

#include "RE_pipeline.h"
#include "RE_shader_ext.h"	/* TexResult, ShadeResult, ShadeInput */

struct Object;
struct MemArena;
struct VertTableNode;
struct Octree;
struct GHash;

#define TABLEINITSIZE 1024
#define LAMPINITSIZE 256

typedef struct SampleTables
{
	float centLut[16];
	float *fmask1[9], *fmask2[9];
	char cmask[256], *centmask;
	
} SampleTables;

/* this is handed over to threaded hiding/passes/shading engine */
typedef struct RenderPart
{
	struct RenderPart *next, *prev;
	
	/* result of part rendering */
	RenderResult *result;
	
	unsigned int *rectp;			/* polygon index table */
	int *rectz;						/* zbuffer */
	long *rectdaps;					/* delta acum buffer for pixel structs */
	
	rcti disprect;					/* part coordinates within total picture */
	int rectx, recty;				/* the size */
	short crop, ready;				/* crop is amount of pixels we crop, for filter */
	short sample, nr;				/* sample can be used by zbuffers, nr is partnr */
	short thread;					/* thread id */
	
} RenderPart;

typedef struct Octree {
	struct Branch **adrbranch;
	struct Node **adrnode;
	float ocsize;	/* ocsize: mult factor,  max size octree */
	float ocfacx,ocfacy,ocfacz;
	float min[3], max[3];
	int ocres;
	int branchcount, nodecount;
} Octree;

/* controls state of render, everything that's read-only during render stage */
struct Render
{
	struct Render *next, *prev;
	char name[RE_MAXNAME];
	
	/* state settings */
	short flag, osa, ok, do_gamma;
	
	/* result of rendering */
	RenderResult *result;
	
	/* window size, display rect, viewplane */
	int winx, winy;
	rcti disprect;			/* part within winx winy */
	rctf viewplane;			/* mapped on winx winy */
	float viewdx, viewdy;	/* size of 1 pixel */
	
	/* final picture width and height (within disprect) */
	int rectx, recty;
	
	/* correction values for pixels or view */
	float ycor, viewfac;
	float bluroffsx, bluroffsy;
	float panosi, panoco;
	
	/* Matrices */
	float grvec[3];			/* for world */
	float imat[3][3];		/* copy of viewinv */
	float viewmat[4][4], viewinv[4][4];
	float winmat[4][4];
	
	/* clippping */
	float clipsta;
	float clipend;
	
	/* samples */
	SampleTables *samples;
	float jit[32][2];
	
	/* scene, and its full copy of renderdata and world */
	Scene *scene;
	RenderData r;
	World wrld;
	
	ListBase parts;
	
	/* octree tables and variables for raytrace */
	Octree oc;
	
	/* use this instead of R.r.cfra */
	float cfra;	
	
	/* render database */
	int totvlak, totvert, tothalo, totlamp;
	ListBase lights;
	
	int vertnodeslen;
	struct VertTableNode *vertnodes;
	int blohalen;
	struct HaloRen **bloha;
	int blovllen;
	struct VlakRen **blovl;
	ListBase objecttable;
	
	struct GHash *orco_hash;

	/* arena for allocating data for use during render, for
		* example dynamic TFaces to go in the VlakRen structure.
		*/
	struct MemArena *memArena;
	
	/* callbacks */
	void (*display_init)(RenderResult *rr);
	void (*display_clear)(RenderResult *rr);
	void (*display_draw)(RenderResult *rr, rcti *rect);
	
	void (*stats_draw)(RenderStats *ri);
	void (*timecursor)(int i);
	
	int (*test_break)(void);
	int (*test_return)(void);
	void (*error)(const char *str);
	
	RenderStats i;
};

/* ------------------------------------------------------------------------- */

typedef struct ShadSampleBuf {
	struct ShadSampleBuf *next, *prev;
	long *zbuf;
	char *cbuf;
} ShadSampleBuf;

typedef struct ShadBuf {
	short samp, shadhalostep, totbuf;
	float persmat[4][4];
	float viewmat[4][4];
	float winmat[4][4];
	float *jit, *weight;
	float d, clipend, pixsize, soft;
	int co[3];
	int size, bias;
	ListBase buffers;
} ShadBuf;

/* ------------------------------------------------------------------------- */
/* lookup of objects in database */
typedef struct ObjectRen {
	struct ObjectRen *next, *prev;
	struct Object *ob, *par;
	int index, startvert, endvert, startface, endface;
} ObjectRen;

/* ------------------------------------------------------------------------- */

typedef struct VertRen
{
	float co[3];
	float n[3];
	float ho[4];
	float *orco;
	short clip;	
	unsigned short flag;		/* in use for clipping zbuffer parts, temp setting stuff in convertblender.c */
	float accum;		/* accum for radio weighting, and for strand texco static particles */
	int index;			/* index allows extending vertren with any property */
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
	float n[3];
	struct Material *mat;
	struct TFace *tface;
	unsigned int *vcol;
	char snproj, puno;
	char flag, ec;
	RadFace *radface;
	Object *ob;
} VlakRen;

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
	/** amount of subsample buffers */
	short buffers, filtertype;
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

/* **************** defines ********************* */

/* mode flag is same as for renderdata */
/* flag */
#define R_ZTRA			1
#define R_HALO			2
#define R_SEC_FIELD		4
#define R_LAMPHALO		8
#define R_RENDERING		16
#define R_ANIMRENDER	32
#define R_REDRAW_PRV	64

/* vlakren->flag (vlak = face in dutch) char!!! */
#define R_SMOOTH		1
#define R_VISIBLE		2
/* strand flag, means special handling */
#define R_STRAND		4
#define R_NOPUNOFLIP	8
#define R_FULL_OSA		16
#define R_FACE_SPLIT	32
/* Tells render to divide face other way. */
#define R_DIVIDE_24		64	
/* vertex normals are tangent or view-corrected vector, for hair strands */
#define R_TANGENT		128		





#endif /* RENDER_TYPES_H */

