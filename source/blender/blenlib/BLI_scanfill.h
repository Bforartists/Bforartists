/*
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

#ifndef __BLI_SCANFILL_H__
#define __BLI_SCANFILL_H__

/** \file BLI_scanfill.h
 *  \ingroup bli
 *  \since March 2001
 *  \author nzc
 *  \brief Filling meshes.
 */

struct ScanFillVert;

#ifdef __cplusplus
extern "C" {
#endif

typedef struct ScanFillContext {
	ListBase fillvertbase;
	ListBase filledgebase;
	ListBase fillfacebase;

	/* private */
	struct ScanFillVertLink *_scdata;
	struct MemArena *arena;
} ScanFillContext;

#define BLI_SCANFILL_ARENA_SIZE MEM_SIZE_OPTIMAL(1 << 14)

typedef struct ScanFillVert {
	struct ScanFillVert *next, *prev;
	union {
		struct ScanFillVert *v;
		void                *p;
		intptr_t             l;
		unsigned int         u;
	} tmp;
	float co[3];  /* vertex location */
	float xy[2];  /* 2D projection of vertex location */
	unsigned int keyindex; /* index, caller can use how it likes to match the scanfill result with own data */
	unsigned short poly_nr;
	unsigned char edge_tot;  /* number of edges using this vertex */
	unsigned char f;
} ScanFillVert;

typedef struct ScanFillEdge {
	struct ScanFillEdge *next, *prev;
	struct ScanFillVert *v1, *v2;
	unsigned short poly_nr;
	unsigned char f;
	union {
		unsigned char c;
	} tmp;
} ScanFillEdge;

typedef struct ScanFillFace {
	struct ScanFillFace *next, *prev;
	struct ScanFillVert *v1, *v2, *v3;
} ScanFillFace;

/* scanfill.c */
struct ScanFillVert *BLI_scanfill_vert_add(ScanFillContext *sf_ctx, const float vec[3]);
struct ScanFillEdge *BLI_scanfill_edge_add(ScanFillContext *sf_ctx, struct ScanFillVert *v1, struct ScanFillVert *v2);

enum {
	BLI_SCANFILL_CALC_QUADTRI_FASTPATH = (1 << 0),

	/* note: using BLI_SCANFILL_CALC_REMOVE_DOUBLES
	 * Assumes ordered edges, otherwise we risk an eternal loop
	 * removing double verts. - campbell */
	BLI_SCANFILL_CALC_REMOVE_DOUBLES   = (1 << 1),

	/* note: This flag removes checks for overlapping polygons.
	 * when this flag is set, we'll never get back more faces then (totvert - 2) */
	BLI_SCANFILL_CALC_HOLES            = (1 << 2)
};
void BLI_scanfill_begin(ScanFillContext *sf_ctx);
unsigned int BLI_scanfill_calc(ScanFillContext *sf_ctx, const int flag);
unsigned int BLI_scanfill_calc_ex(ScanFillContext *sf_ctx, const int flag,
                          const float nor_proj[3]);
void BLI_scanfill_end(ScanFillContext *sf_ctx);

void BLI_scanfill_begin_arena(ScanFillContext *sf_ctx, struct MemArena *arena);
void BLI_scanfill_end_arena(ScanFillContext *sf_ctx, struct MemArena *arena);

/* These callbacks are needed to make the lib finction properly */
void BLI_setErrorCallBack(void (*f)(const char *));

#ifdef __cplusplus
}
#endif

#endif

