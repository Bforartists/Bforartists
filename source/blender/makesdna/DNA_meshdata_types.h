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
#ifndef DNA_MESHDATA_TYPES_H
#define DNA_MESHDATA_TYPES_H

#include "DNA_customdata_types.h"

struct Bone;
struct Image;

typedef struct MFace {
	unsigned int v1, v2, v3, v4;
	char pad, mat_nr;
	char edcode, flag;	/* we keep edcode, for conversion to edges draw flags in old files */
} MFace;

typedef struct MEdge {
	unsigned int v1, v2;
	char crease, pad;
	short flag;
} MEdge;

typedef struct MDeformWeight {
	int				def_nr;
	float			weight;
} MDeformWeight;

typedef struct MDeformVert {
	struct MDeformWeight *dw;
	int totweight;
	int flag;	// flag only in use for weightpaint now
} MDeformVert;

typedef struct MVert {
	float	co[3];
	short	no[3];
	char flag, mat_nr;
} MVert;

typedef struct MCol {
	char a, r, g, b;
} MCol;

typedef struct MSticky {
	float co[2];
} MSticky;

typedef struct MSelect {
	int index;
	int type;
} MSelect;

typedef struct MTFace {
	float uv[4][2];
	struct Image *tpage;
	char flag, transp;
	short mode, tile, unwrap;
} MTFace;

/* Multiresolution modeling */
typedef struct MultiresCol {
	float a, r, g, b, u, v;
} MultiresCol;
typedef struct MultiresFace {
	unsigned int v[4];
       	unsigned int mid;
	unsigned int childrenstart;
	char flag, mat_nr, pad[2];
} MultiresFace;
typedef struct MultiresEdge {
	unsigned int v[2];
	unsigned int mid;
} MultiresEdge;

typedef struct MultiresTexColFace {
	/* vertex colors and texfaces */
	void *tex_page;
	MultiresCol col[4];
	short tex_mode, tex_tile, tex_unwrap;
	char tex_flag, tex_transp;
} MultiresTexColFace;

struct MultiresMapNode;
typedef struct MultiresLevel {
	struct MultiresLevel *next, *prev;

	MVert *verts;
	MultiresFace *faces;
	MultiresTexColFace *texcolfaces;
	MultiresEdge *edges;
	struct ListBase *vert_edge_map;
	struct ListBase *vert_face_map;
	struct MultiresMapNode *map_mem;

	unsigned int totvert, totface, totedge, pad;
} MultiresLevel;

typedef struct Multires {
	ListBase levels;
	unsigned char level_count, current, newlvl, edgelvl, pinlvl, renderlvl;
	unsigned char use_col, use_tex;

	/* Vertex groups are stored only for the level 1 mesh, for all other
	 * levels it's calculated when multires_level_to_mesh() is called */
	struct CustomData vdata;
} Multires;

typedef struct PartialVisibility {
	unsigned int *vert_map; /* vert_map[Old Index]= New Index */
	int *edge_map; /* edge_map[Old Index]= New Index, -1= hidden */
	MFace *old_faces;
	MEdge *old_edges;
	unsigned int totface, totedge, totvert, pad;
} PartialVisibility;

/* mvert->flag (1=SELECT) */
#define ME_SPHERETEST	2
#define ME_SPHERETEMP	4
#define ME_HIDE			16
#define ME_VERT_MERGED		(1<<6)

/* medge->flag (1=SELECT)*/
#define ME_EDGEDRAW			(1<<1)
#define ME_SEAM				(1<<2)
#define ME_FGON				(1<<3)
						// reserve 16 for ME_HIDE
#define ME_EDGERENDER		(1<<5)
#define ME_LOOSEEDGE		(1<<7)
#define ME_SEAM_LAST		(1<<8)
#define ME_SHARP			(1<<9)

/* puno = vertexnormal (mface) */
/* render assumes flips to be ordered like this */
#define ME_FLIPV1		1
#define ME_FLIPV2		2
#define ME_FLIPV3		4
#define ME_FLIPV4		8
#define ME_PROJXY		16
#define ME_PROJXZ		32
#define ME_PROJYZ		64

/* edcode (mface) */
#define ME_V1V2			1
#define ME_V2V3			2
#define ME_V3V1			4
#define ME_V3V4			4
#define ME_V4V1			8

/* flag (mface) */
#define ME_SMOOTH			1
#define ME_FACE_SEL			2
						/* flag ME_HIDE==16 is used here too */ 
/* mselect->type */
#define ME_VSEl	0
#define ME_ESEl 1
#define ME_FSEL 2

/* mtface->flag */
#define TF_SELECT	1
#define TF_ACTIVE	2
#define TF_SEL1		4
#define TF_SEL2		8
#define TF_SEL3		16
#define TF_SEL4		32
#define TF_HIDE		64

/* mtface->mode */
#define TF_DYNAMIC		1
#define TF_DEPRECATED	2
#define TF_TEX			4
#define TF_SHAREDVERT	8
#define TF_LIGHT		16

#define TF_SHAREDCOL	64
#define TF_TILES		128
#define TF_BILLBOARD	256
#define TF_TWOSIDE		512
#define TF_INVISIBLE	1024

#define TF_OBCOL		2048
#define TF_BILLBOARD2	4096	/* with Z axis constraint */
#define TF_SHADOW		8192
#define TF_BMFONT		16384

/* mtface->transp */
#define TF_SOLID	0
#define TF_ADD		1
#define TF_ALPHA	2
#define TF_SUB		3

/* mtface->unwrap */
#define TF_DEPRECATED1	1
#define TF_DEPRECATED2	2
#define TF_DEPRECATED3	4
#define TF_DEPRECATED4	8
#define TF_PIN1		    16
#define TF_PIN2		    32
#define TF_PIN3	   		64
#define TF_PIN4	    	128

#endif
