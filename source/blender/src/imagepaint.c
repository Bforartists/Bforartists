/**
 * $Id$
 * imagepaint.c
 *
 * Functions to paint images in 2D and 3D.
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA	02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: some of this file.
 *
 * Contributor(s): Jens Ole Wund (bjornmose), Campbell Barton (ideasman42)
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include <string.h>
#include <stdio.h>
#include <math.h>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "MEM_guardedalloc.h"

#ifdef WIN32
#include "BLI_winstuff.h"
#endif
#include "BLI_arithb.h"
#include "BLI_blenlib.h"
#include "BLI_dynstr.h"
#include "BLI_linklist.h"
#include "BLI_memarena.h"
#include "PIL_time.h"

#include "IMB_imbuf.h"
#include "IMB_imbuf_types.h"

#include "DNA_brush_types.h"
#include "DNA_image_types.h"
#include "DNA_mesh_types.h"
#include "DNA_meshdata_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_scene_types.h"
#include "DNA_screen_types.h"
#include "DNA_space_types.h"
#include "DNA_userdef_types.h"
#include "DNA_view3d_types.h"

#include "BKE_brush.h"
#include "BKE_global.h"
#include "BKE_image.h"
#include "BKE_main.h"
#include "BKE_mesh.h"
#include "BKE_node.h"
#include "BKE_utildefines.h"
#include "BKE_DerivedMesh.h"

#include "BIF_interface.h"
#include "BIF_mywindow.h"
#include "BIF_screen.h"
#include "BIF_space.h"
#include "BIF_toolbox.h"

#include "BSE_drawipo.h"
#include "BSE_node.h"
#include "BSE_trans_types.h"
#include "BSE_view.h"

#include "BDR_imagepaint.h"
#include "BDR_vpaint.h"

#include "GPU_draw.h"

#include "GHOST_Types.h"

#include "blendef.h"
#include "butspace.h"
#include "mydevice.h"

/* Defines and Structs */

#define IMAPAINT_CHAR_TO_FLOAT(c) (c/255.0f)

#define IMAPAINT_FLOAT_RGB_TO_CHAR(c, f) { c[0]=FTOCHAR(f[0]); \
	c[1]=FTOCHAR(f[1]); c[2]=FTOCHAR(f[2]); }
#define IMAPAINT_CHAR_RGB_TO_FLOAT(f, c) { f[0]=IMAPAINT_CHAR_TO_FLOAT(c[0]); \
	f[1]=IMAPAINT_CHAR_TO_FLOAT(c[1]); f[2]=IMAPAINT_CHAR_TO_FLOAT(c[2]); }
#define IMAPAINT_FLOAT_RGB_COPY(a, b) VECCOPY(a, b)

#define IMAPAINT_TILE_BITS			6
#define IMAPAINT_TILE_SIZE			(1 << IMAPAINT_TILE_BITS)
#define IMAPAINT_TILE_NUMBER(size)	(((size)+IMAPAINT_TILE_SIZE-1) >> IMAPAINT_TILE_BITS)

#define MAXUNDONAME	64

typedef struct ImagePaintState {
	Brush *brush;
	short tool, blend;
	Image *image;
	ImBuf *canvas;
	ImBuf *clonecanvas;
	short clonefreefloat;
	char *warnpackedfile;
	char *warnmultifile;

	/* texture paint only */
	Object *ob;
	Mesh *me;
	int faceindex;
	float uv[2];
} ImagePaintState;


/* testing options */
#define PROJ_BUCKET_DIV 128 /* TODO - test other values, this is a guess, seems ok */

//#define PROJ_DEBUG_PAINT 1
#define PROJ_DEBUG_NOSCANLINE 1
//#define PROJ_DEBUG_NOSEAMBLEED 1

/* projectFaceSeamFlags options */
//#define PROJ_FACE_IGNORE	1<<0	/* When the face is hidden, backfacing or occluded */
//#define PROJ_FACE_INIT	1<<1	/* When we have initialized the faces data */
#define PROJ_FACE_SEAM1	1<<0	/* If this face has a seam on any of its edges */
#define PROJ_FACE_SEAM2	1<<1
#define PROJ_FACE_SEAM3	1<<2
#define PROJ_FACE_SEAM4	1<<3

#define PROJ_FACE_NOSEAM1	1<<4
#define PROJ_FACE_NOSEAM2	1<<5
#define PROJ_FACE_NOSEAM3	1<<6
#define PROJ_FACE_NOSEAM4	1<<7

#define PROJ_BUCKET_NULL		0
#define PROJ_BUCKET_INIT		1<<0
// #define PROJ_BUCKET_CLONE_INIT	1<<1

/* only for readability */
#define PROJ_BUCKET_LEFT		0
#define PROJ_BUCKET_RIGHT	1
#define PROJ_BUCKET_BOTTOM	2
#define PROJ_BUCKET_TOP		3

typedef struct ProjectPaintState {
	Brush *brush;
	short tool, blend;
	Object *ob;
	/* end similarities with ImagePaintState */
	
	DerivedMesh    *dm;
	int 			dm_totface;
	int 			dm_totvert;
	
	MVert 		   *dm_mvert;
	MFace 		   *dm_mface;
	MTFace 		   *dm_mtface;
	
	/* projection painting only */
	MemArena *projectArena;			/* use for alocating many pixel structs and link-lists */
	LinkNode **projectBuckets;		/* screen sized 2D array, each pixel has a linked list of ProjectPixel's */
	LinkNode **projectFaces;		/* projectBuckets alligned array linkList of faces overlapping each bucket */
	char *projectBucketFlags;		/* store if the bucks have been initialized  */
	char *projectFaceSeamFlags;		/* store info about faces, if they are initialized etc*/
	float (*projectFaceSeamUVs)[4][2];	/* expanded UVs for faces to use as seams */
	LinkNode **projectVertFaces;	/* Only needed for when projectSeamBleed is enabled, use to find UV seams */
	
	int bucketsX;					/* The size of the bucket grid, the grid span's viewMin2D/viewMax2D so you can paint outsize the screen or with 2 brushes at once */
	int bucketsY;
	
	Image **projectImages;			/* array of images we are painting onto while, use so we can tag for updates */
	
	int projectImageTotal;			/* size of projectImages array */
	int imaContextIndex;			/* current image, use for context switching */
	
	float (*projectVertScreenCos)[3];	/* verts projected into floating point screen space */
	
	/* options for projection painting */
	short projectIsOcclude;			/* Use raytraced occlusion? - ortherwise will paint right through to the back*/
	short projectIsBackfaceCull;	/* ignore faces with normals pointing away, skips a lot of raycasts if your normals are correctly flipped */
	short projectIsOrtho;
#ifndef PROJ_DEBUG_NOSEAMBLEED
	float projectSeamBleed;
#endif
	/* clone vars */
	float cloneOfs[2];
	
	
	float projectMat[4][4];		/* Projection matrix, use for getting screen coords */
	float viewMat[4][4];
	float viewDir[3];			/* View vector, use for projectIsBackfaceCull and for ray casting with an ortho viewport  */
	
	float viewMin2D[2];			/* 2D bounds for mesh verts on the screen's plane (screenspace) */
	float viewMax2D[2]; 
	float viewWidth;			/* Calculated from viewMin2D & viewMax2D */
	float viewHeight;
} ProjectPaintState;

typedef struct ProjectScanline {
	int v[3]; /* verts for this scanline, 0,1,2 or 0,2,3 */
	float x_limits[2]; /* UV min|max for this scanline */
} ProjectScanline;

typedef struct ProjectPixel {
	float projCo2D[2]; /* the floating point screen projection of this pixel */
	char *pixel;
	int image_index;
} ProjectPixel;

typedef struct ProjectPixelClone {
	struct ProjectPixel __pp;
	/*char backbuf[4];	*//* TODO - float buffer? */
	char clonebuf[4];
	//void *source;		/* pointer to source pixels */
} ProjectPixelClone;

/* Finish projection painting structs */


typedef struct UndoTile {
	struct UndoTile *next, *prev;
	ID id;
	void *rect;
	int x, y;
} UndoTile;

typedef struct UndoElem {
	struct UndoElem *next, *prev;
	char name[MAXUNDONAME];
	unsigned long undosize;

	ImBuf *ibuf;
	ListBase tiles;
} UndoElem;

typedef struct ImagePaintPartialRedraw {
	int x1, y1, x2, y2;
	int enabled;
} ImagePaintPartialRedraw;

static ListBase undobase = {NULL, NULL};
static UndoElem *curundo = NULL;
static ImagePaintPartialRedraw imapaintpartial = {0, 0, 0, 0, 0};

/* UNDO */

/* internal functions */

static void undo_copy_tile(UndoTile *tile, ImBuf *tmpibuf, ImBuf *ibuf, int restore)
{
	/* copy or swap contents of tile->rect and region in ibuf->rect */
	IMB_rectcpy(tmpibuf, ibuf, 0, 0, tile->x*IMAPAINT_TILE_SIZE,
		tile->y*IMAPAINT_TILE_SIZE, IMAPAINT_TILE_SIZE, IMAPAINT_TILE_SIZE);

	if(ibuf->rect_float) SWAP(void*, tmpibuf->rect_float, tile->rect)
	else SWAP(void*, tmpibuf->rect, tile->rect)
	
	if(restore)
		IMB_rectcpy(ibuf, tmpibuf, tile->x*IMAPAINT_TILE_SIZE,
			tile->y*IMAPAINT_TILE_SIZE, 0, 0, IMAPAINT_TILE_SIZE, IMAPAINT_TILE_SIZE);
}

static void undo_restore(UndoElem *undo)
{
	Image *ima = NULL;
	ImBuf *ibuf, *tmpibuf;
	UndoTile *tile;

	if(!undo)
		return;

	tmpibuf= IMB_allocImBuf(IMAPAINT_TILE_SIZE, IMAPAINT_TILE_SIZE, 32,
	                        IB_rectfloat|IB_rect, 0);
	
	for(tile=undo->tiles.first; tile; tile=tile->next) {
		/* find image based on name, pointer becomes invalid with global undo */
		if(ima && strcmp(tile->id.name, ima->id.name)==0);
		else {
			for(ima=G.main->image.first; ima; ima=ima->id.next)
				if(strcmp(tile->id.name, ima->id.name)==0)
					break;
		}

		ibuf= BKE_image_get_ibuf(ima, NULL);

		if (!ima || !ibuf || !(ibuf->rect || ibuf->rect_float))
			continue;

		undo_copy_tile(tile, tmpibuf, ibuf, 1);

		GPU_free_image(ima); /* force OpenGL reload */
		if(ibuf->rect_float)
			imb_freerectImBuf(ibuf); /* force recreate of char rect */
	}

	IMB_freeImBuf(tmpibuf);
}

static void undo_free(UndoElem *undo)
{
	UndoTile *tile;

	for(tile=undo->tiles.first; tile; tile=tile->next)
		MEM_freeN(tile->rect);
	BLI_freelistN(&undo->tiles);
}

static void undo_imagepaint_push_begin(char *name)
{
	UndoElem *uel;
	int nr;
	
	/* Undo push is split up in begin and end, the reason is that as painting
	 * happens more tiles are added to the list, and at the very end we know
	 * how much memory the undo used to remove old undo elements */

	/* remove all undos after (also when curundo==NULL) */
	while(undobase.last != curundo) {
		uel= undobase.last;
		undo_free(uel);
		BLI_freelinkN(&undobase, uel);
	}
	
	/* make new */
	curundo= uel= MEM_callocN(sizeof(UndoElem), "undo file");
	BLI_addtail(&undobase, uel);

	/* name can be a dynamic string */
	strncpy(uel->name, name, MAXUNDONAME-1);
	
	/* limit amount to the maximum amount*/
	nr= 0;
	uel= undobase.last;
	while(uel) {
		nr++;
		if(nr==U.undosteps) break;
		uel= uel->prev;
	}
	if(uel) {
		while(undobase.first!=uel) {
			UndoElem *first= undobase.first;
			undo_free(first);
			BLI_freelinkN(&undobase, first);
		}
	}
}

static void undo_imagepaint_push_end()
{
	UndoElem *uel;
	unsigned long totmem, maxmem;

	if(U.undomemory != 0) {
		/* limit to maximum memory (afterwards, we can't know in advance) */
		totmem= 0;
		maxmem= ((unsigned long)U.undomemory)*1024*1024;

		uel= undobase.last;
		while(uel) {
			totmem+= uel->undosize;
			if(totmem>maxmem) break;
			uel= uel->prev;
		}

		if(uel) {
			while(undobase.first!=uel) {
				UndoElem *first= undobase.first;
				undo_free(first);
				BLI_freelinkN(&undobase, first);
			}
		}
	}
}


static int project_paint_BucketOffset(ProjectPaintState *ps, float *projCo2D)
{
	/* If we were not dealing with screenspace 2D coords we could simple do...
	 * ps->projectBuckets[x + (y*ps->bucketsY)] */
	
	/* please explain?
	 * projCo2D[0] - ps->viewMin2D[0]	: zero origin
	 * ... / ps->viewWidth				: range from 0.0 to 1.0
	 * ... * ps->bucketsX		: use as a bucket index
	 *
	 * Second multiplication does similar but for vertical offset
	 */
	return	(	(int)(( (projCo2D[0] - ps->viewMin2D[0]) / ps->viewWidth)  * ps->bucketsX)) + 
		(	(	(int)(( (projCo2D[1] - ps->viewMin2D[1])  / ps->viewHeight) * ps->bucketsY)) * ps->bucketsX );
}

static int project_paint_BucketOffsetSafe(ProjectPaintState *ps, float *projCo2D)
{
	int bucket_index = project_paint_BucketOffset(ps, projCo2D);
	
	if (bucket_index < 0 || bucket_index >= ps->bucketsX*ps->bucketsY) {	
		return -1;
	} else {
		return bucket_index;
	}
}

/* The point must be inside the triangle */
static void BaryCentricWeightsSimple2f(float v1[2], float v2[2], float v3[2], float pt[2], float w[3]) {
	float wtot;
	w[0] = AreaF2Dfl(v2, v3, pt);
	w[1] = AreaF2Dfl(v3, v1, pt);
	w[2] = AreaF2Dfl(v1, v2, pt);
	wtot = w[0]+w[1]+w[2];
	if (wtot > 0.0) { /* just incase */
		w[0]/=wtot;
		w[1]/=wtot;
		w[2]/=wtot;
	} else {
		printf("WATCH oUT ZAREA FACE\n");
		w[0] = w[1] = w[2] = 1.0/3.0; /* dummy values for zero area face */
	}
}

/* also works for points outside the triangle */
#define SIDE_OF_LINE(pa,pb,pp)	((pa[0]-pp[0])*(pb[1]-pp[1]))-((pb[0]-pp[0])*(pa[1]-pp[1]))
static void BaryCentricWeights2f(float v1[2], float v2[2], float v3[2], float pt[2], float w[3]) {
	float wtot = AreaF2Dfl(v1, v2, v3);
	if (wtot > 0.0) {
		w[0] = AreaF2Dfl(v2, v3, pt);
		w[1] = AreaF2Dfl(v3, v1, pt);
		w[2] = AreaF2Dfl(v1, v2, pt);
		
		/* negate weights when 'pt' is on the outer side of the the triangles edge */
		if ((SIDE_OF_LINE(v2,v3, pt)>0.0) != (SIDE_OF_LINE(v2,v3, v1)>0.0))	w[0]/= -wtot;
		else																w[0]/=  wtot;

		if ((SIDE_OF_LINE(v3,v1, pt)>0.0) != (SIDE_OF_LINE(v3,v1, v2)>0.0))	w[1]/= -wtot;
		else																w[1]/=  wtot;

		if ((SIDE_OF_LINE(v1,v2, pt)>0.0) != (SIDE_OF_LINE(v1,v2, v3)>0.0))	w[2]/= -wtot;
		else																w[2]/=  wtot;
	} else {
		w[0] = w[1] = w[2] = 1.0/3.0; /* dummy values for zero area face */
	}
}

static float tri_depth_2d(float v1[3], float v2[3], float v3[3], float pt[2], float w[3])
{
	BaryCentricWeightsSimple2f(v1,v2,v3,pt,w);
	return (v1[2]*w[0]) + (v2[2]*w[1]) + (v3[2]*w[2]);
}


/* return the topmost face  in screen coords index or -1
 * bucket_index can be -1 if we dont know it to begin with */
static int screenco_pickface(ProjectPaintState *ps, float pt[2], float w[3], int *side) {
	LinkNode *node;
	float w_tmp[3];
	float *v1, *v2, *v3, *v4;
	int bucket_index;
	int face_index;
	int best_side = -1;
	int best_face_index = -1;
	float z_depth_best = MAXFLOAT, z_depth;
	MFace *mf;
	
	bucket_index = project_paint_BucketOffsetSafe(ps, pt);
	if (bucket_index==-1)
		return -1;
	
	node = ps->projectFaces[bucket_index];
	
	/* we could return 0 for 1 face buckets, as long as this function assumes
	 * that the point its testing is only every originated from an existing face */
	
	while (node) {
		face_index = (int)node->link;
		mf = ps->dm_mface + face_index;
		
		v1 = ps->projectVertScreenCos[mf->v1];
		v2 = ps->projectVertScreenCos[mf->v2];
		v3 = ps->projectVertScreenCos[mf->v3];
		
		if ( IsectPT2Df(pt, v1, v2, v3) ) {
			z_depth = tri_depth_2d(v1,v2,v3,pt,w_tmp);
			if (z_depth < z_depth_best) {
				best_face_index = face_index;
				best_side = 0;
				z_depth_best = z_depth;
				VECCOPY(w, w_tmp);
			}
		} else if (mf->v4) {
			v4 = ps->projectVertScreenCos[mf->v4];
			
			if ( IsectPT2Df(pt, v1, v3, v4) ) {
				z_depth = tri_depth_2d(v1,v3,v4,pt,w_tmp);
				if (z_depth < z_depth_best) {
					best_face_index = face_index;
					best_side = 1;
					z_depth_best = z_depth;
					VECCOPY(w, w_tmp);
				}
			}
		}
		
		node = node->next;
	}
	
	*side = best_side;
	return best_face_index; /* will be -1 or a valid face */
}

/* bucket_index is optional, since in some cases we know it */
static int screenco_pickcol(ProjectPaintState *ps, float pt[2], char rgba[4], int interp)
{
	float w[3], uv[2];
	int side;
	int face_index;
	MTFace *tf;
	ImBuf *ibuf;
	int x,y;
	char *pixel;
	
	face_index = screenco_pickface(ps,pt,w, &side);
	
	if (face_index == -1)
		return 0;
	
	tf = ps->dm_mtface + face_index;
	
	if (side==0) {
		uv[0] = tf->uv[0][0]*w[0] + tf->uv[1][0]*w[1] + tf->uv[2][0]*w[2];
		uv[1] = tf->uv[0][1]*w[0] + tf->uv[1][1]*w[1] + tf->uv[2][1]*w[2];
	} else { /* QUAD */
		uv[0] = tf->uv[0][0]*w[0] + tf->uv[2][0]*w[1] + tf->uv[3][0]*w[2];
		uv[1] = tf->uv[0][1]*w[0] + tf->uv[2][1]*w[1] + tf->uv[3][1]*w[2];
	}
	
	ibuf = BKE_image_get_ibuf((Image *)tf->tpage, NULL); /* TODO - this may be slow */
	
	x = uv[0]*ibuf->x;
	y = uv[1]*ibuf->y;
	
	if (x<0 || x>=ibuf->x  ||  y<0 || y>=ibuf->y) return 0;
	
	pixel = (( char * ) ibuf->rect) + (( x + y * ibuf->x ) * 4);
	
	rgba[0] = pixel[0];
	rgba[1] = pixel[1];
	rgba[2] = pixel[2];
	rgba[3] = pixel[3];
	return 1;
}

/* return...
 * 0	: no occlusion
 * -1	: no occlusion but 2D intersection is true (avoid testing the other half of a quad)
 * 1	: occluded */

static int screenco_tri_pt_occlude(float pt[3], float v1[3], float v2[3], float v3[3])
{
	/* if all are behind us, return false */
	if(v1[2] > pt[2] && v2[2] > pt[2] && v3[2] > pt[2])
		return 0;
		
	/* do a 2D point in try intersection */
	if ( !IsectPT2Df(pt, v1, v2, v3) )
		return 0; /* we know there is  */
	
	/* From here on we know there IS an intersection */
	
	/* if ALL of the verts are infront of us then we know it intersects ? */
	if(	v1[2] < pt[2] && v2[2] < pt[2] && v3[2] < pt[2]) {
		return 1;
	} else {
		float w[3];
		/* we intersect? - find the exact depth at the point of intersection */
		if (tri_depth_2d(v1,v2,v3,pt,w) < pt[2]) {
			return 1; /* This point is occluded by another face */
		}
	}
	return -1;
}


/* check, pixelScreenCo must be in screenspace, its Z-Depth only needs to be used for comparison */
static int project_bucket_point_occluded(ProjectPaintState *ps, int bucket_index, int orig_face, float pixelScreenCo[4])
{
	LinkNode *node = ps->projectFaces[bucket_index];
	MFace *mf;
	int face_index;
	int isect_ret;
	
	/* we could return 0 for 1 face buckets, as long as this function assumes
	 * that the point its testing is only every originated from an existing face */
	
	while (node) {
		face_index = (int)node->link;
		
		if (orig_face != face_index) {
			
			mf = ps->dm_mface + face_index;
			
			isect_ret = screenco_tri_pt_occlude(
					pixelScreenCo,
					ps->projectVertScreenCos[mf->v1],
					ps->projectVertScreenCos[mf->v2],
					ps->projectVertScreenCos[mf->v3]);
			
			/* Note, if isect_ret==-1 then we dont want to test the other side of the quad */
			if (isect_ret==0 && mf->v4) {
				isect_ret = screenco_tri_pt_occlude(
						pixelScreenCo,
						ps->projectVertScreenCos[mf->v1],
						ps->projectVertScreenCos[mf->v3],
						ps->projectVertScreenCos[mf->v4]);
			}
			
			if (isect_ret==1) {
#if 0
				/* Cheap Optimization!
				 * This function runs for every UV Screen pixel,
				 * therefor swapping the swapping the faces for this buckets list helps because
				 * the next ~5 to ~200 runs will can hit the first face each time. */
				if (ps->projectFaces[bucket_index] != node) {
					/* SWAP(void *, ps->projectFaces[bucket_index]->link, node->link); */
					
					/* dont need to use swap since we alredy have face_index */
					node->link = ps->projectFaces[bucket_index]->link; /* move the value item to the current value */
					ps->projectFaces[bucket_index]->link = (void *) face_index;
					
					/*printf("swapping %d %d\n", (int)node->link, face_index);*/
				} /*else {
					printf("first hit %d\n", face_index);
				}*/
#endif
				return 1; 
			}
		}
		node = node->next;
	}
	
	return 0;
}

/* basic line intersection, could move to arithb.c, 2 points with a horiz line
 * 1 for an intersection, 2 if the first point is aligned, 3 if the second point is aligned */
#define ISECT_TRUE 1
#define ISECT_TRUE_P1 2
#define ISECT_TRUE_P2 3
static int line_isect_y(float p1[2], float p2[2], float y_level, float *x_isect)
{
	if (y_level==p1[1]) {
		*x_isect = p1[0];
		return ISECT_TRUE_P1;
	}
	if (y_level==p2[1]) {
		*x_isect = p2[0];
		return ISECT_TRUE_P2;
	}
	
	if (p1[1] > y_level && p2[1] < y_level) {
		*x_isect = (p2[0]*(p1[1]-y_level) + p1[0]*(y_level-p2[1])) / (p1[1]-p2[1]);
		return ISECT_TRUE;
	} else if (p1[1] < y_level && p2[1] > y_level) {
		*x_isect = (p2[0]*(y_level-p1[1]) + p1[0]*(p2[1]-y_level)) / (p2[1]-p1[1]);
		return ISECT_TRUE;
	} else {
		return 0;
	}
}

static int line_isect_x(float p1[2], float p2[2], float x_level, float *y_isect)
{
	if (x_level==p1[0]) {
		*y_isect = p1[1];
		return ISECT_TRUE_P1;
	}
	if (x_level==p2[0]) {
		*y_isect = p2[1];
		return ISECT_TRUE_P2;
	}
	
	if (p1[0] > x_level && p2[0] < x_level) {
		*y_isect = (p2[1]*(p1[0]-x_level) + p1[1]*(x_level-p2[0])) / (p1[0]-p2[0]);
		return ISECT_TRUE;
	} else if (p1[0] < x_level && p2[0] > x_level) {
		*y_isect = (p2[1]*(x_level-p1[0]) + p1[1]*(p2[0]-x_level)) / (p2[0]-p1[0]);
		return ISECT_TRUE;
	} else {
		return 0;
	}
}

static int project_face_scanline(ProjectScanline *sc, float y_level, float v1[2], float v2[2], float v3[2], float v4[2])
{	
	/* Create a scanlines for the face at this Y level 
	 * triangles will only ever have 1 scanline, quads may have 2 */
	int totscanlines = 0;
	short i1=0,i2=0,i3=0;
	
	if (v4) { /* This is a quad?*/
		int i4=0, i_mid=0;
		float xi1, xi2, xi3, xi4, xi_mid;
				
		i1 = line_isect_y(v1, v2, y_level, &xi1);
		if (i1 != ISECT_TRUE_P2) /* rare cases we could be on the line, in these cases we dont want to intersect with the same point twice */
			i2 = line_isect_y(v2, v3, y_level, &xi2);
		
		if (i1 && i2) { /* both the first 2 edges intersect, this means the second half of the quad wont intersect */
			sc->v[0] = 0;
			sc->v[1] = 1;
			sc->v[2] = 2;
			sc->x_limits[0] = MIN2(xi1, xi2);
			sc->x_limits[1] = MAX2(xi1, xi2);
			totscanlines = 1;
		} else {
			if (i2 != ISECT_TRUE_P2) 
				i3 = line_isect_y(v3, v4, y_level, &xi3);
			if (i1 != ISECT_TRUE_P1 && i3 != ISECT_TRUE_P2) 
				i4 = line_isect_y(v4, v1, y_level, &xi4);
			
			if (i3 && i4) { /* second 2 edges only intersect, same as above */
				sc->v[0] = 0;
				sc->v[1] = 2;
				sc->v[2] = 3;
				sc->x_limits[0] = MIN2(xi3, xi4);
				sc->x_limits[1] = MAX2(xi3, xi4);
				totscanlines = 1;
			} else {
				/* OK - we have a not-so-simple case, both sides of the quad intersect.
				 * Will need to have 2 scanlines */
				if ((i1||i2) && (i3||i4)) {
					i_mid = line_isect_y(v1, v3, y_level, &xi_mid);
					/* it would be very rare this would be false, but possible */
					sc->v[0] = 0;
					sc->v[1] = 1;
					sc->v[2] = 2;
					sc->x_limits[0] = MIN2((i1?xi1:xi2), xi_mid);
					sc->x_limits[1] = MAX2((i1?xi1:xi2), xi_mid);
					
					sc++;
					sc->v[0] = 0;
					sc->v[1] = 2;
					sc->v[2] = 3;
					sc->x_limits[0] = MIN2((i3?xi3:xi4), xi_mid);
					sc->x_limits[1] = MAX2((i3?xi3:xi4), xi_mid);
					
					totscanlines = 2;
				}
			}
		}
	} else { /* triangle */
		int i = 0;
		
		i1 = line_isect_y(v1, v2, y_level, &sc->x_limits[0]);
		if (i1) i++;
		
		if (i1 != ISECT_TRUE_P2) {
			i2 = line_isect_y(v2, v3, y_level, &sc->x_limits[i]);
			if (i2) i++;
		}
		
		/* if the triangle intersects then the first 2 lines must */
		if (i!=0) {
			if (i!=2) {
				/* if we are here then this really should not fail since 2 edges MUST intersect  */
				if (i1 != ISECT_TRUE_P1 && i2 != ISECT_TRUE_P2) {
					i3 = line_isect_y(v3, v1, y_level, &sc->x_limits[i]);
					if (i3) i++;
					
				}
			}
			
			if (i==2) {
				if (sc->x_limits[0] > sc->x_limits[1]) {
					SWAP(float, sc->x_limits[0], sc->x_limits[1]);
				}
				sc->v[0] = 0;
				sc->v[1] = 1;
				sc->v[2] = 2;
				totscanlines = 1;
			}
		}
	}
	/* done setting up scanlines */
	return totscanlines;
}

static int cmp_uv(float vec2a[2], float vec2b[2])
{
	return ((fabs(vec2a[0]-vec2b[0]) < 0.0001) && (fabs(vec2a[1]-vec2b[1]) < 0.0001)) ? 1:0;
}
	

#ifndef PROJ_DEBUG_NOSEAMBLEED
/* TODO - set the seam flag on the other face to avoid double lookups */
static int check_seam(ProjectPaintState *ps, int orig_face, int orig_i1_fidx, int orig_i2_fidx, int *other_face, int *orig_fidx)
{
	LinkNode *node;
	int face_index;
	int i, i1, i2;
	int i1_fidx = -1, i2_fidx = -1; /* indexi in face */
	MFace *orig_mf, *mf;
	MTFace *orig_tf, *tf;
	
	orig_mf = ps->dm_mface + orig_face;
	orig_tf = ps->dm_mtface + orig_face;
	
	/* vert indicies from face vert order indicies */
	i1 = (*(&orig_mf->v1 + orig_i1_fidx));
	i2 = (*(&orig_mf->v1 + orig_i2_fidx));
	
	for (node = ps->projectVertFaces[i1]; node; node = node->next) {
		face_index = (int)node->link;
		if (face_index != orig_face) {
			mf = ps->dm_mface + face_index;
			
			/* We need to know the order of the verts in the adjacent face 
			 * set the i1_fidx and i2_fidx to (0,1,2,3) */
			i = mf->v4 ? 3:2;
			do {
				if (i1 == (*(&mf->v1 + i))) {
					i1_fidx = i;
				} else if (i2 == (*(&mf->v1 + i))) {
					i2_fidx = i;
				}
				
			} while (i--);
			
			if (i2_fidx != -1) {
				/* This IS an adjacent face!, now lets check if the UVs are ok */
				

				
				tf = ps->dm_mtface + face_index;
				
				/* set up the other face */
				*other_face = face_index;
				*orig_fidx = (i1_fidx < i2_fidx) ? i1_fidx : i2_fidx;
				
				/* first test if they have the same image */
				if (	(orig_tf->tpage == tf->tpage) &&
						cmp_uv(orig_tf->uv[orig_i1_fidx], tf->uv[i1_fidx]) &&
						cmp_uv(orig_tf->uv[orig_i2_fidx], tf->uv[i2_fidx]) )
				{
					// printf("SEAM (NONE)\n");
					return 0;
					
				} else {
					// printf("SEAM (UV GAP)\n");
					return 1;
				}
			}
		}
	}
	// printf("SEAM (NO FACE)\n");
	*other_face = -1;
	return 1;
}


static float angleToLength(float angle)
{
	float x,y, fac;
	
	// Alredy accounted for
	if (angle < 0.000001)
		return 1.0;
	
	angle = (2.0*M_PI/360.0) * angle;
	x = cos(angle);
	y = sin(angle);
	
	// print "YX", x,y
	// 0 d is hoz to the right.
	// 90d is vert upward.
	fac = 1.0/x;
	x = x*fac;
	y = y*fac;
	return sqrt((x*x)+(y*y));
}

/* return zero if there is no area in the returned rectangle */
static int uv_image_rect(float uv1[2], float uv2[2], float uv3[2], float uv4[2], int min_px[2], int max_px[2], int x_px, int y_px, int is_quad)
{
	float min_uv[2], max_uv[2]; /* UV bounds */
	int i;
	
	INIT_MINMAX2(min_uv, max_uv);
	
	DO_MINMAX2(uv1, min_uv, max_uv);
	DO_MINMAX2(uv2, min_uv, max_uv);
	DO_MINMAX2(uv3, min_uv, max_uv);
	if (is_quad)
		DO_MINMAX2(uv4, min_uv, max_uv);
	
	min_px[0] = (int)(x_px * min_uv[0]);
	min_px[1] = (int)(y_px * min_uv[1]);
	
	max_px[0] = (int)(x_px * max_uv[0]) +1;
	max_px[1] = (int)(y_px * max_uv[1]) +1;
	
	/*printf("%d %d %d %d \n", min_px[0], min_px[1], max_px[0], max_px[1]);*/
	CLAMP(min_px[0], 0, x_px);
	CLAMP(max_px[0], 0, x_px);
	
	CLAMP(min_px[1], 0, y_px);
	CLAMP(max_px[1], 0, y_px);
	
	/* face uses no UV area when quantized to pixels? */
	return (min_px[0] == max_px[0] || min_px[1] == max_px[1]) ? 0 : 1;
}

/* takes a faces UV's and assigns outset coords to outset_uv */
static void uv_image_outset(float (*orig_uv)[2], float (*outset_uv)[2], float scaler, int x_px, int y_px, int is_quad)
{
	float a1,a2,a3,a4=0.0;
	float puv[4][2]; /* pixelspace uv's */
	float no1[2], no2[2], no3[2], no4[2]; /* normals */
	float dir1[2], dir2[2], dir3[2], dir4[2];
	
	/* make UV's in pixel space so we can */
	puv[0][0] = orig_uv[0][0] * x_px;
	puv[0][1] = orig_uv[0][1] * y_px;
	
	puv[1][0] = orig_uv[1][0] * x_px;
	puv[1][1] = orig_uv[1][1] * y_px;
	
	puv[2][0] = orig_uv[2][0] * x_px;
	puv[2][1] = orig_uv[2][1] * y_px;
	
	if (is_quad) {
		puv[3][0] = orig_uv[3][0] * x_px;
		puv[3][1] = orig_uv[3][1] * y_px;
	}
	
	/* face edge directions */
	Vec2Subf(dir1, puv[1], puv[0]);
	Vec2Subf(dir2, puv[2], puv[1]);
	Normalize2(dir1);
	Normalize2(dir2);
	
	if (is_quad) {
		Vec2Subf(dir3, puv[3], puv[2]);
		Vec2Subf(dir4, puv[0], puv[3]);
		Normalize2(dir3);
		Normalize2(dir4);
	} else {
		Vec2Subf(dir3, puv[0], puv[2]);
		Normalize2(dir3);
	}
	
	if (is_quad) {
		a1 = NormalizedVecAngle2_2D(dir4, dir1);
		a2 = NormalizedVecAngle2_2D(dir1, dir2);
		a3 = NormalizedVecAngle2_2D(dir2, dir3);
		a4 = NormalizedVecAngle2_2D(dir3, dir4);
	} else {
		a1 = NormalizedVecAngle2_2D(dir3, dir1);
		a2 = NormalizedVecAngle2_2D(dir1, dir2);
		a3 = NormalizedVecAngle2_2D(dir2, dir3);
	}
	
	a1 = angleToLength(a1);
	a2 = angleToLength(a2);
	a3 = angleToLength(a3);
	if (is_quad)
		a4 = angleToLength(a4);
	
	if (is_quad) {
		Vec2Subf(no1, dir4, dir1);
		Vec2Subf(no2, dir1, dir2);
		Vec2Subf(no3, dir2, dir3);
		Vec2Subf(no4, dir3, dir4);
		Normalize2(no1);
		Normalize2(no2);
		Normalize2(no3);
		Normalize2(no4);
		Vec2Mulf(no1, a1*scaler);
		Vec2Mulf(no2, a2*scaler);
		Vec2Mulf(no3, a3*scaler);
		Vec2Mulf(no4, a4*scaler);
		Vec2Addf(outset_uv[0], puv[0], no1);
		Vec2Addf(outset_uv[1], puv[1], no2);
		Vec2Addf(outset_uv[2], puv[2], no3);
		Vec2Addf(outset_uv[3], puv[3], no4);
		outset_uv[0][0] /= x_px;
		outset_uv[0][1] /= y_px;
		
		outset_uv[1][0] /= x_px;
		outset_uv[1][1] /= y_px;
		
		outset_uv[2][0] /= x_px;
		outset_uv[2][1] /= y_px;
		
		outset_uv[3][0] /= x_px;
		outset_uv[3][1] /= y_px;
	} else {
		Vec2Subf(no1, dir3, dir1);
		Vec2Subf(no2, dir1, dir2);
		Vec2Subf(no3, dir2, dir3);
		Normalize2(no1);
		Normalize2(no2);
		Normalize2(no3);
		Vec2Mulf(no1, a1*scaler);
		Vec2Mulf(no2, a2*scaler);
		Vec2Mulf(no3, a3*scaler);
		Vec2Addf(outset_uv[0], puv[0], no1);
		Vec2Addf(outset_uv[1], puv[1], no2);
		Vec2Addf(outset_uv[2], puv[2], no3);
		outset_uv[0][0] /= x_px;
		outset_uv[0][1] /= y_px;
		
		outset_uv[1][0] /= x_px;
		outset_uv[1][1] /= y_px;
		
		outset_uv[2][0] /= x_px;
		outset_uv[2][1] /= y_px;
	}
}

/* 
 * Be tricky with flags, first 4 bits are PROJ_FACE_SEAM1 to 4, last 4 bits are PROJ_FACE_NOSEAM1 to 4
 * 1<<i - where i is (0-3) 
 */
static void project_face_seams_init(ProjectPaintState *ps, int face_index, int is_quad)
{
	int other_face, other_fidx; /* vars for the other face, we also set its flag */
	int fidx1, fidx2;
	
	fidx1 = is_quad ? 3 : 2;
	do {
		if (is_quad)
			fidx2 = (fidx1==3) ? 0 : fidx1+1; /* next fidx in the face (0,1,2,3) -> (1,2,3,0) */
		else
			fidx2 = (fidx1==2) ? 0 : fidx1+1; /* next fidx in the face (0,1,2) -> (1,2,0) */
		
		if ((ps->projectFaceSeamFlags[face_index] & (1<<fidx1|16<<fidx1)) == 0) {
			if (check_seam(ps, face_index, fidx1,fidx2, &other_face, &other_fidx)) {
				ps->projectFaceSeamFlags[face_index] |= 1<<fidx1;
				if (other_face != -1)
					ps->projectFaceSeamFlags[other_face] |= 1<<other_fidx;
			} else {
				ps->projectFaceSeamFlags[face_index] |= 16<<fidx1;
				if (other_face != -1)
					ps->projectFaceSeamFlags[other_face] |= 16<<other_fidx; /* second 4 bits for disabled */
			}
		}
	} while (fidx1--);
}
#endif // PROJ_DEBUG_NOSEAMBLEED


/* TODO - move to arithb.c */

/* little sister we only need to know lambda */
static float lambda_cp_line2(float p[2], float l1[2], float l2[2])
{
	float h[2],u[2];
	Vec2Subf(u, l2, l1);
	Vec2Subf(h, p, l1);
	return(Inp2f(u,h)/Inp2f(u,u));
}

static screen_px_from_ortho(
		ProjectPaintState *ps, float uv[2],
		float v1co[3], float v2co[3], float v3co[3], /* Screenspace coords */
		float uv1co[2], float uv2co[2], float uv3co[2],
		float pixelScreenCo[4] )
{
	float w[3];
	BaryCentricWeightsSimple2f(uv1co,uv2co,uv3co,uv,w);
	pixelScreenCo[0] = v1co[0]*w[0] + v2co[0]*w[1] + v3co[0]*w[2];
	pixelScreenCo[1] = v1co[1]*w[0] + v2co[1]*w[1] + v3co[1]*w[2];
	pixelScreenCo[2] = v1co[2]*w[0] + v2co[2]*w[1] + v3co[2]*w[2];	
}

static screen_px_from_persp(
		ProjectPaintState *ps, float uv[2],
		float v1co[3], float v2co[3], float v3co[3], /* Worldspace coords */
		float uv1co[2], float uv2co[2], float uv3co[2],
		float pixelScreenCo[4])
{
	float w[3];
	BaryCentricWeightsSimple2f(uv1co,uv2co,uv3co,uv,w);
	pixelScreenCo[0] = v1co[0]*w[0] + v2co[0]*w[1] + v3co[0]*w[2];
	pixelScreenCo[1] = v1co[1]*w[0] + v2co[1]*w[1] + v3co[1]*w[2];
	pixelScreenCo[2] = v1co[2]*w[0] + v2co[2]*w[1] + v3co[2]*w[2];
	pixelScreenCo[3] = 1.0;
	
	Mat4MulVec4fl(ps->projectMat, pixelScreenCo);
	
	// if( pixelScreenCo[3] > 0.001 ) { ??? TODO
	/* screen space, not clamped */
	pixelScreenCo[0] = (float)(curarea->winx/2.0)+(curarea->winx/2.0)*pixelScreenCo[0]/pixelScreenCo[3];	
	pixelScreenCo[1] = (float)(curarea->winy/2.0)+(curarea->winy/2.0)*pixelScreenCo[1]/pixelScreenCo[3];
	pixelScreenCo[2] = pixelScreenCo[2]/pixelScreenCo[3]; /* Use the depth for bucket point occlusion */
}


/* Only run this function once for new ProjectPixelClone's */
#define pixel_size 4

static void project_paint_uvpixel_init(ProjectPaintState *ps, ImBuf *ibuf, int x, int y, int bucket_index, int face_index, float pixelScreenCo[4])
{
	ProjectPixel *projPixel;
	
	// printf("adding px (%d %d), (%f %f)\n", x,y,uv[0],uv[1]);
	
	
	/* Use viewMin2D to make (0,0) the bottom left of the bounds 
	 * Then this can be used to index the bucket array */
	
	/* Is this UV visible from the view? - raytrace */
	/* screenco_pickface is less complex, use for testing */
	//if (screenco_pickface(ps, pixelScreenCo, w, &side) == face_index) {
	if (ps->projectIsOcclude==0 || !project_bucket_point_occluded(ps, bucket_index, face_index, pixelScreenCo)) {
		/* done with view3d_project_float inline */
		if (ps->tool==PAINT_TOOL_CLONE) {
			float co[2];
			
			projPixel = (ProjectPixel *)BLI_memarena_alloc(ps->projectArena, sizeof(ProjectPixelClone));
			projPixel->pixel = (( char * ) ibuf->rect) + (( x + y * ibuf->x ) * pixel_size);
			VECCOPY2D(projPixel->projCo2D, pixelScreenCo);
			
			/* copy pixel color to backbuf - not used yet */
			/* memcpy( &(((ProjectPixelClone *)projPixel)->backbuf), projPixel->pixel, pixel_size); */
			//((ProjectPixelClone *)projPixel)->source = NULL; /* must be set later */
			
			
			/* Initialize clone pixels - note that this is a bit of a waste since some of these are being indirectly initialized :/ */
			/* TODO - possibly only run this for directly ativated buckets when cloning */
			Vec2Subf(co, projPixel->projCo2D, ps->cloneOfs);
			
			/* no need to initialize the bucket, we're only checking buckets faces and for this
			 * the faces are alredy initialized in project_paint_delayed_face_init(...) */
			if (!screenco_pickcol(ps, co, ((ProjectPixelClone *)projPixel)->clonebuf, 1)) {
				((ProjectPixelClone *)projPixel)->clonebuf[3] = 0; /* zero alpha - ignore */
			}
		} else {
			/* smear needs the buffer from a clone pixel */
			projPixel = (ProjectPixel *)BLI_memarena_alloc(ps->projectArena, (ps->tool==PAINT_TOOL_SMEAR) ? sizeof(ProjectPixelClone) : sizeof(ProjectPixel));
			projPixel->pixel = (( char * ) ibuf->rect) + (( x + y * ibuf->x ) * pixel_size);
			VECCOPY2D(projPixel->projCo2D, pixelScreenCo);
		}
		
		/* screenspace unclamped */
		
#ifdef PROJ_DEBUG_PAINT
		projPixel->pixel[1] = 0;
#endif
		projPixel->image_index = ps->imaContextIndex;
		
		BLI_linklist_prepend_arena(
			&ps->projectBuckets[ bucket_index ],
			projPixel,
			ps->projectArena
		);
	}
}

static void uvpixel_rect_intersect(int min_target[2], int max_target[2],  int min_a[2], int max_a[2],  int min_b[2], int max_b[2])
{
	min_target[0] = MAX2(min_a[0], min_b[0]);
	min_target[1] = MAX2(min_a[1], min_b[1]);
	
	max_target[0] = MIN2(max_a[0], max_b[0]);
	max_target[1] = MIN2(max_a[1], max_b[1]);
}

static int line_clip_rect2f(float rect[4], float l1[2], float l2[2], float l1_clip[2], float l2_clip[2])
{
	float isect;
	short ok1 = 0;
	short ok2 = 0;
	
	/* are either of the points inside the rectangle ? */
	if (	l1[1] >= rect[PROJ_BUCKET_BOTTOM] &&	l1[1] <= rect[PROJ_BUCKET_TOP] &&
			l1[0] >= rect[PROJ_BUCKET_LEFT] &&		l1[0] <= rect[PROJ_BUCKET_RIGHT]
	) {
		VECCOPY2D(l1_clip, l1);
		ok1 = 1;
	}
	
	if (	l2[1] >= rect[PROJ_BUCKET_BOTTOM] &&	l2[1] <= rect[PROJ_BUCKET_TOP] &&
			l2[0] >= rect[PROJ_BUCKET_LEFT] &&		l2[0] <= rect[PROJ_BUCKET_RIGHT]
	) {
		VECCOPY2D(l2_clip, l2);
		ok2 = 1;
	}
	
	/* line inside rect */
	if (ok1 && ok2) {
		return 1;
	}
	
	/* top/bottom */
	if (line_isect_y(l1,l2, rect[PROJ_BUCKET_BOTTOM], &isect) && (isect > rect[PROJ_BUCKET_LEFT]) && (isect < rect[PROJ_BUCKET_RIGHT])) {
		if (l1[1] < l2[1]) { /* line 1 is outside */
			l1_clip[0] = isect;
			l1_clip[1] = rect[PROJ_BUCKET_BOTTOM];
			ok1 = 1;
		} else {
			l2_clip[0] = isect;
			l2_clip[1] = rect[PROJ_BUCKET_BOTTOM];
			ok2 = 2;
		}
	}
	if (line_isect_y(l1,l2, rect[PROJ_BUCKET_TOP], &isect) && (isect > rect[PROJ_BUCKET_LEFT]) && (isect < rect[PROJ_BUCKET_RIGHT])) {
		if (l1[1] > l2[1]) { /* line 1 is outside */
			l1_clip[0] = isect;
			l1_clip[1] = rect[PROJ_BUCKET_TOP];
			ok1 = 1;
		} else {
			l2_clip[0] = isect;
			l2_clip[1] = rect[PROJ_BUCKET_TOP];
			ok2 = 2;
		}
	}
	
	/* left/right */
	if (line_isect_x(l1,l2, rect[PROJ_BUCKET_LEFT], &isect) && (isect > rect[PROJ_BUCKET_BOTTOM]) && (isect < rect[PROJ_BUCKET_TOP])) {
		if (l1[0] < l2[0]) { /* line 1 is outside */
			l1_clip[0] = rect[PROJ_BUCKET_LEFT];
			l1_clip[1] = isect;
			ok1 = 1;
		} else {
			l2_clip[0] = rect[PROJ_BUCKET_LEFT];
			l2_clip[1] = isect;
			ok2 = 2;
		}
	}
	if (line_isect_x(l1,l2, rect[PROJ_BUCKET_RIGHT], &isect) && (isect > rect[PROJ_BUCKET_BOTTOM]) && (isect < rect[PROJ_BUCKET_TOP])) {
		if (l1[0] > l2[0]) { /* line 1 is outside */
			l1_clip[0] = rect[PROJ_BUCKET_RIGHT];
			l1_clip[1] = isect;
			ok1 = 1;
		} else {
			l2_clip[0] = rect[PROJ_BUCKET_RIGHT];
			l2_clip[1] = isect;
			ok2 = 2;
		}
	}
	
	if (ok1 && ok2) {
		return 1;
	} else {
		return 0;
	}
}



/* scale the quad & tri about its center
 * scaling by 0.99999 is used for getting fake UV pixel coords that are on the
 * edge of the face but slightly inside it occlusion tests dont return hits on adjacent faces */
static void scale_quad(float *origCos[4], float insetCos[4][3], float inset)
{
	float cent[3];
	cent[0] = (origCos[0][0] + origCos[1][0] + origCos[2][0] + origCos[3][0]) / 4.0;
	cent[1] = (origCos[0][1] + origCos[1][1] + origCos[2][1] + origCos[3][1]) / 4.0;
	cent[2] = (origCos[0][2] + origCos[1][2] + origCos[2][2] + origCos[3][2]) / 4.0;
	
	VecSubf(insetCos[0], origCos[0], cent);
	VecSubf(insetCos[1], origCos[1], cent);
	VecSubf(insetCos[2], origCos[2], cent);
	VecSubf(insetCos[3], origCos[3], cent);
	
	VecMulf(insetCos[0], inset);
	VecMulf(insetCos[1], inset);
	VecMulf(insetCos[2], inset);
	VecMulf(insetCos[3], inset);
	
	VecAddf(insetCos[0], insetCos[0], cent);
	VecAddf(insetCos[1], insetCos[1], cent);
	VecAddf(insetCos[2], insetCos[2], cent);
	VecAddf(insetCos[3], insetCos[3], cent);
}

static void scale_tri(float *origCos[4], float insetCos[4][3], float inset)
{
	float cent[3];
	cent[0] = (origCos[0][0] + origCos[1][0] + origCos[2][0]) / 3.0;
	cent[1] = (origCos[0][1] + origCos[1][1] + origCos[2][1]) / 3.0;
	cent[2] = (origCos[0][2] + origCos[1][2] + origCos[2][2]) / 3.0;
	
	VecSubf(insetCos[0], origCos[0], cent);
	VecSubf(insetCos[1], origCos[1], cent);
	VecSubf(insetCos[2], origCos[2], cent);
	
	VecMulf(insetCos[0], inset);
	VecMulf(insetCos[1], inset);
	VecMulf(insetCos[2], inset);
	
	VecAddf(insetCos[0], insetCos[0], cent);
	VecAddf(insetCos[1], insetCos[1], cent);
	VecAddf(insetCos[2], insetCos[2], cent);
}

/**/
static void project_paint_face_init(ProjectPaintState *ps, int bucket_index, int face_index, float bucket_bounds[4], ImBuf *ibuf)
{
	/* Projection vars, to get the 3D locations into screen space  */
	
	MFace *mf = ps->dm_mface + face_index;
	MTFace *tf = ps->dm_mtface + face_index;
	
	/* UV/pixel seeking data */
	int x; /* Image X-Pixel */
	int y;/* Image Y-Pixel */
	float uv[2]; /* Image floating point UV - same as x,y but from 0.0-1.0 */
	
	int min_px[2], max_px[2]; /* UV Bounds converted to int's for pixel */
	int min_px_tf[2], max_px_tf[2]; /* UV Bounds converted to int's for pixel */
	int min_px_bucket[2][2], max_px_bucket[2][2]; /* Bucket Bounds converted to int's for pixel */
	float *v1coSS, *v2coSS, *v3coSS, *v4coSS; /* vert co screen-space, these will be assigned to mf->v1,2,3 or mf->v1,3,4 */
	float *v1co, *v2co, *v3co; /* vert co */
	float *uv1co, *uv2co, *uv3co; /* for convenience only, these will be assigned to tf->uv[0],1,2 or tf->uv[0],2,3 */
	float pixelScreenCo[4], pixelScreenCoXMin[4], pixelScreenCoXMax[4];
	int i, j;
	
	/* vars for getting uvspace bounds */
	float bucket_bounds_uv[2] [4][2]; /* bucket bounds in UV space so we can init pixels only for this face,  */
	float w[3];
	int i1,i2,i3;
	
	/* scanlines since quads can have 2 triangles intersecting the same vertical location */
#ifndef PROJ_DEBUG_NOSCANLINE 
	ProjectScanline scanlines[2];
	ProjectScanline *sc;
	int totscanlines; /* can only be 1 or 2, oh well */
#endif
	i = mf->v4 ? 1:0;
	do {
		if (i==1) {
			i1=0; i2=1; i3=2;
		} else {
			i1=0; i2=2; i3=3;
		}
		
		uv1co = tf->uv[i1];
		uv2co = tf->uv[i2];
		uv3co = tf->uv[i3];

		v1coSS = ps->projectVertScreenCos[ (*(&mf->v1 + i1)) ];
		v2coSS = ps->projectVertScreenCos[ (*(&mf->v1 + i2)) ];
		v3coSS = ps->projectVertScreenCos[ (*(&mf->v1 + i3)) ];
		
		if (ps->projectIsOrtho==0) {
			v1co = ps->dm_mvert[ (*(&mf->v1 + i1)) ].co;
			v2co = ps->dm_mvert[ (*(&mf->v1 + i2)) ].co;
			v3co = ps->dm_mvert[ (*(&mf->v1 + i3)) ].co;
		}
		
		/* get the UV space bounding box */
		uv[0] = bucket_bounds[PROJ_BUCKET_RIGHT];
		uv[1] = bucket_bounds[PROJ_BUCKET_BOTTOM];
		BaryCentricWeights2f(v1coSS, v2coSS, v3coSS, uv, w);
		bucket_bounds_uv[i][0][0] = uv1co[0]*w[0] + uv2co[0]*w[1] + uv3co[0]*w[2];
		bucket_bounds_uv[i][0][1] = uv1co[1]*w[0] + uv2co[1]*w[1] + uv3co[1]*w[2];
		
		//uv[0] = bucket_bounds[PROJ_BUCKET_RIGHT]; // set above
		uv[1] = bucket_bounds[PROJ_BUCKET_TOP];
		BaryCentricWeights2f(v1coSS, v2coSS, v3coSS, uv, w);
		bucket_bounds_uv[i][1][0] = uv1co[0]*w[0] + uv2co[0]*w[1] + uv3co[0]*w[2];
		bucket_bounds_uv[i][1][1] = uv1co[1]*w[0] + uv2co[1]*w[1] + uv3co[1]*w[2];
		
		
		uv[0] = bucket_bounds[PROJ_BUCKET_LEFT];
		//uv[1] = bucket_bounds[PROJ_BUCKET_TOP]; // set above
		BaryCentricWeights2f(v1coSS, v2coSS, v3coSS, uv, w);
		bucket_bounds_uv[i][2][0] = uv1co[0]*w[0] + uv2co[0]*w[1] + uv3co[0]*w[2];
		bucket_bounds_uv[i][2][1] = uv1co[1]*w[0] + uv2co[1]*w[1] + uv3co[1]*w[2];
		
		//uv[0] = bucket_bounds[PROJ_BUCKET_LEFT]; // set above
		uv[1] = bucket_bounds[PROJ_BUCKET_BOTTOM];
		BaryCentricWeights2f(v1coSS, v2coSS, v3coSS, uv, w);
		bucket_bounds_uv[i][3][0] = uv1co[0]*w[0] + uv2co[0]*w[1] + uv3co[0]*w[2];
		bucket_bounds_uv[i][3][1] = uv1co[1]*w[0] + uv2co[1]*w[1] + uv3co[1]*w[2];
		
		//printf("Bounds: %f | %f | %f | %f\n", bucket_bounds[0], bucket_bounds[1], bucket_bounds[2], bucket_bounds[3]);

		if (	uv_image_rect(uv1co, uv2co, uv3co, NULL, min_px_tf, max_px_tf, ibuf->x, ibuf->y, 0) && 
				uv_image_rect(bucket_bounds_uv[i][0], bucket_bounds_uv[i][1], bucket_bounds_uv[i][2], bucket_bounds_uv[i][3], min_px_bucket[i], max_px_bucket[i], ibuf->x, ibuf->y, 1) )
		{
			
			uvpixel_rect_intersect(min_px, max_px, min_px_bucket[i], max_px_bucket[i], min_px_tf, max_px_tf);
			
			/* clip face and */


			for (y = min_px[1]; y < max_px[1]; y++) {
				uv[1] = (((float)y)+0.5) / (float)ibuf->y; /* TODO - this is not pixel aligned correctly */
				for (x = min_px[0]; x < max_px[0]; x++) {
					uv[0] = (((float)x)+0.5) / (float)ibuf->x;
					
					/* test we're inside uvspace bucket and triangle bounds */
					if (	IsectPQ2Df(uv, bucket_bounds_uv[i][0], bucket_bounds_uv[i][1], bucket_bounds_uv[i][2], bucket_bounds_uv[i][3]) &&
							IsectPT2Df(uv, uv1co, uv2co, uv3co) ) {
						
						if (ps->projectIsOrtho) {
							screen_px_from_ortho(ps, uv, v1coSS,v2coSS,v3coSS, uv1co,uv2co,uv3co, pixelScreenCo);
						} else {
							screen_px_from_persp(ps, uv, v1co,v2co,v3co, uv1co,uv2co,uv3co, pixelScreenCo);
						}
						
						project_paint_uvpixel_init(ps, ibuf, x,y, bucket_index, face_index, pixelScreenCo);
					}
				}
			}
		}
	} while(i--);
	
	if (ps->projectSeamBleed > 0.0) {
		
		int flag = ps->projectFaceSeamFlags[face_index];
		
		/* are any of our edges un-initialized? */
		if ((flag & (PROJ_FACE_SEAM1|PROJ_FACE_NOSEAM1))==0 || 
			(flag & (PROJ_FACE_SEAM2|PROJ_FACE_NOSEAM2))==0 || 
			(flag & (PROJ_FACE_SEAM3|PROJ_FACE_NOSEAM3))==0 || 
			(flag & (PROJ_FACE_SEAM4|PROJ_FACE_NOSEAM4))==0
		) {
			project_face_seams_init(ps, face_index, mf->v4);
			flag = ps->projectFaceSeamFlags[face_index];
			//printf("seams - %d %d %d %d\n", flag&PROJ_FACE_SEAM1, flag&PROJ_FACE_SEAM2, flag&PROJ_FACE_SEAM3, flag&PROJ_FACE_SEAM4);
		}
		
		if (flag & (PROJ_FACE_SEAM1|PROJ_FACE_SEAM2|PROJ_FACE_SEAM3|PROJ_FACE_SEAM4)) {
			/* we have a seam - deal with it! */
			
			/* Now create new UV's for the seam face */
			float (*outset_uv)[2];
			float insetCos[4][3]; /* expanded UV's */
			float cent[3];
			float *uv_seam_quads[4][4];
			float *edge_verts_inset[4][2];
			float *edge_verts[4][2];
			float fac;
			float *vCoSS[4]; /* vertex screenspace coords */
			
			float bucket_clip_edges[4][2][2]; /* store the screenspace coords of the face, clipped by the bucket's screen aligned rectangle */
			int totuvseamquads = 0;
			int fidx1, fidx2; /* face edge pairs - loop throuh these ((0,1), (1,2), (2,3), (3,0)) or ((0,1), (1,2), (2,0)) for a tri */
			
			outset_uv = ps->projectFaceSeamUVs[face_index];
			
			if (outset_uv[0][0]==MAXFLOAT) /* first time initialize */
				uv_image_outset(tf->uv, outset_uv, ps->projectSeamBleed, ibuf->x, ibuf->y, mf->v4);
			
			vCoSS[0] = ps->projectVertScreenCos[ mf->v1 ];
			vCoSS[1] = ps->projectVertScreenCos[ mf->v2 ];
			vCoSS[2] = ps->projectVertScreenCos[ mf->v3 ];
			if (mf->v4) {
				vCoSS[3] = ps->projectVertScreenCos[ mf->v4 ];
				scale_quad(vCoSS, insetCos, 0.99999);
			} else { 
				scale_tri(vCoSS, insetCos, 0.99999);
			}
			
			for (fidx1 = 0; fidx1 < (mf->v4 ? 4 : 3); fidx1++) {
				if (mf->v4)		fidx2 = (fidx1==3) ? 0 : fidx1+1; /* next fidx in the face (0,1,2,3) -> (1,2,3,0) */
				else			fidx2 = (fidx1==2) ? 0 : fidx1+1; /* next fidx in the face (0,1,2) -> (1,2,0) */
				
				if (	(ps->projectFaceSeamFlags[face_index] & (1<<fidx1) ) && /* 1<<fidx1 -> PROJ_FACE_SEAM# */
						line_clip_rect2f(bucket_bounds, vCoSS[fidx1], vCoSS[fidx2], bucket_clip_edges[totuvseamquads][0], bucket_clip_edges[totuvseamquads][1])
				) {
					uv_seam_quads[totuvseamquads][0] = tf->uv[fidx1];
					uv_seam_quads[totuvseamquads][1] = tf->uv[fidx2];
					uv_seam_quads[totuvseamquads][2] = outset_uv[fidx2];
					uv_seam_quads[totuvseamquads][3] = outset_uv[fidx1];
					edge_verts_inset[totuvseamquads][0] = insetCos[fidx1]; //ps->projectVertScreenCos[ mf->v3 ];
					edge_verts_inset[totuvseamquads][1] = insetCos[fidx2]; //ps->projectVertScreenCos[ mf->v1 ];
					edge_verts[totuvseamquads][0] = vCoSS[fidx1];
					edge_verts[totuvseamquads][1] = vCoSS[fidx2];
					totuvseamquads++;
				}
			}
			
			
			for (i=0; i< totuvseamquads; i++) { /* loop over our seams */
				
			
				/* make a quad spanning the subsection of the face the bucket intersects with */
				float seam_subsection[4][2];
				float fac1, fac2, ftot;
				float edge_verts_inset_clip[2][3];

				ftot = Vec2Lenf(edge_verts[i][0], edge_verts[i][1]);
				fac1 = Vec2Lenf(edge_verts[i][0], bucket_clip_edges[i][0]) / ftot;
				fac2 = Vec2Lenf(edge_verts[i][0], bucket_clip_edges[i][1]) / ftot;
				
				Vec2Lerpf(seam_subsection[0], uv_seam_quads[i][0], uv_seam_quads[i][1], fac1);
				Vec2Lerpf(seam_subsection[1], uv_seam_quads[i][0], uv_seam_quads[i][1], fac2);
				
				Vec2Lerpf(seam_subsection[2], uv_seam_quads[i][3], uv_seam_quads[i][2], fac2);
				Vec2Lerpf(seam_subsection[3], uv_seam_quads[i][3], uv_seam_quads[i][2], fac1);
				
				/* if the bucket_clip_edges values Z values was kept we could avoid this
				 * Inset needs to be added so occlusiuon tests wont hit adjacent faces */
				VecLerpf(edge_verts_inset_clip[0], edge_verts_inset[i][0], edge_verts_inset[i][1], fac1);
				VecLerpf(edge_verts_inset_clip[1], edge_verts_inset[i][0], edge_verts_inset[i][1], fac2);
				
				if (uv_image_rect(seam_subsection[0], seam_subsection[1], seam_subsection[2], seam_subsection[3], min_px, max_px, ibuf->x, ibuf->y, 1)) {
					/* bounds between the seam rect and the uvspace bucket pixels */
				
					for (y = min_px[1]; y < max_px[1]; y++) {
						
						uv[1] = (((float)y)+0.5) / (float)ibuf->y; /* TODO - this is not pixel aligned correctly */
						for (x = min_px[0]; x < max_px[0]; x++) {
							
							uv[0] = (((float)x)+0.5) / (float)ibuf->x;
							
							/* test we're inside uvspace bucket and triangle bounds */
							if (	IsectPQ2Df(uv, seam_subsection[0], seam_subsection[1], seam_subsection[2], seam_subsection[3]) ) {
								
								/* We need to find the closest point allong the face edge,
								 * getting the screen_px_from_*** wont work because our actual location
								 * is not relevent, since we are outside the face, Use VecLerpf to find
								 * our location on the side of the face's UV */
								/*
								if (ps->projectIsOrtho)	screen_px_from_ortho(ps, uv, v1co,v2co,v3co, uv1co,uv2co,uv3co, pixelScreenCo);
								else					screen_px_from_persp(ps, uv, v1co,v2co,v3co, uv1co,uv2co,uv3co, pixelScreenCo);
								*/
								
								/* Since this is a seam we need to work out where on the line this pixel is */
								//fac = lambda_cp_line2(uv, uv_seam_quads[i][0], uv_seam_quads[i][1]);
								fac = lambda_cp_line2(uv, seam_subsection[0], seam_subsection[1]);
								if (fac<0.0) {
									VECCOPY(pixelScreenCo, edge_verts_inset_clip[0]);
								} else if (fac>1.0) {
									VECCOPY(pixelScreenCo, edge_verts_inset_clip[1]);
								} else {
									VecLerpf(pixelScreenCo, edge_verts_inset_clip[0], edge_verts_inset_clip[1], fac);
								}
								
								if (!ps->projectIsOrtho) {
									pixelScreenCo[3] = 1.0;
									Mat4MulVec4fl(ps->projectMat, pixelScreenCo);
									pixelScreenCo[0] = (float)(curarea->winx/2.0)+(curarea->winx/2.0)*pixelScreenCo[0]/pixelScreenCo[3];	
									pixelScreenCo[1] = (float)(curarea->winy/2.0)+(curarea->winy/2.0)*pixelScreenCo[1]/pixelScreenCo[3];
									pixelScreenCo[2] = pixelScreenCo[2]/pixelScreenCo[3]; /* Use the depth for bucket point occlusion */
								}
								
								project_paint_uvpixel_init(ps, ibuf, x, y, bucket_index, face_index, pixelScreenCo);
							}
						}
					}
				}
			}
		}
	}
	return;	
}


/* takes floating point screenspace min/max and returns int min/max to be used as indicies for ps->projectBuckets, ps->projectBucketFlags */
static void project_paint_rect(ProjectPaintState *ps, float min[2], float max[2], int bucket_min[2], int bucket_max[2])
{
	/* divide by bucketWidth & bucketHeight so the bounds are offset in bucket grid units */
	bucket_min[0] = (int)(((float)(min[0] - ps->viewMin2D[0]) / ps->viewWidth) * ps->bucketsX) + 0.5; /* these offsets of 0.5 and 1.5 seem odd but they are correct */
	bucket_min[1] = (int)(((float)(min[1] - ps->viewMin2D[1]) / ps->viewHeight) * ps->bucketsY) + 0.5;
	
	bucket_max[0] = (int)(((float)(max[0] - ps->viewMin2D[0]) / ps->viewWidth) * ps->bucketsX) + 1.5;
	bucket_max[1] = (int)(((float)(max[1] - ps->viewMin2D[1]) / ps->viewHeight) * ps->bucketsY) + 1.5;	
	
	/* incase the rect is outside the mesh 2d bounds */
	CLAMP(bucket_min[0], 0, ps->bucketsX);
	CLAMP(bucket_min[1], 0, ps->bucketsY);
	
	CLAMP(bucket_max[0], 0, ps->bucketsX);
	CLAMP(bucket_max[1], 0, ps->bucketsY);
}

static void project_bucket_bounds(ProjectPaintState *ps, int bucket_x, int bucket_y, float bucket_bounds[4])
{
	bucket_bounds[ PROJ_BUCKET_LEFT ] =		ps->viewMin2D[0]+((bucket_x)*(ps->viewWidth / ps->bucketsX));		/* left */
	bucket_bounds[ PROJ_BUCKET_RIGHT ] =	ps->viewMin2D[0]+((bucket_x+1)*(ps->viewWidth / ps->bucketsX));	/* right */
	
	bucket_bounds[ PROJ_BUCKET_BOTTOM ] =	ps->viewMin2D[1]+((bucket_y)*(ps->viewHeight / ps->bucketsY));		/* bottom */
	bucket_bounds[ PROJ_BUCKET_TOP ] =		ps->viewMin2D[1]+((bucket_y+1)*(ps->viewHeight  / ps->bucketsY));	/* top */
}

/* have bucket_bounds as an arg so we dont need to give bucket_x/y the rect function need */
static void project_paint_bucket_init(ProjectPaintState *ps, int bucket_index, float bucket_bounds[4])
{
	LinkNode *node;
	int face_index;
	ImBuf *ibuf;
	MTFace *tf;
	
	Image *tpage_last = NULL;
	int tpage_index;
	
	if ((node = ps->projectFaces[bucket_index])) {
		do {
			face_index = (int)node->link;
				
			/* Image context switching */
			tf = ps->dm_mtface+face_index;
			if (tpage_last != tf->tpage) {
				tpage_last = tf->tpage;
				
				ps->imaContextIndex = -1; /* sanity check */
				
				for (tpage_index=0; tpage_index < ps->projectImageTotal; tpage_index++) {
					if (ps->projectImages[tpage_index] == tpage_last) {
						ps->imaContextIndex = tpage_index;
						break;
					}
				}
				
				if (ps->imaContextIndex==-1) {
					printf("Error, should never happen!\n");
					return;
				}
				
				ibuf = BKE_image_get_ibuf(tpage_last, NULL); /* TODO - this may be slow */
			}
			project_paint_face_init(ps, bucket_index, face_index, bucket_bounds, ibuf);
			
			node = node->next;
		} while (node);
	}
	
	ps->projectBucketFlags[bucket_index] |= PROJ_BUCKET_INIT; 
}


/* We want to know if a bucket and a face overlap in screenspace
 * 
 * Note, if this ever returns false positives its not that bad, since a face in the bounding area will have its pixels
 * calculated when it might not be needed later, (at the moment at least)
 * obviously it shouldnt have bugs though */

static int project_bucket_face_isect(ProjectPaintState *ps, float min[2], float max[2], int bucket_x, int bucket_y, int bucket_index, MFace *mf)
{
	/* TODO - replace this with a tricker method that uses sideofline for all projectVertScreenCos's edges against the closest bucket corner */
	float bucket_bounds[4];
	float p1[2], p2[2], p3[2], p4[2];
	float *v, *v1,*v2,*v3,*v4;
	int i;
	
	project_bucket_bounds(ps, bucket_x, bucket_y, bucket_bounds);
	
	/* Is one of the faces verts in the bucket bounds? */
	
	i = mf->v4 ? 3:2;
	do {
		v = ps->projectVertScreenCos[ (*(&mf->v1 + i)) ];
		
		if ((v[0] > bucket_bounds[PROJ_BUCKET_LEFT]) &&
			(v[0] < bucket_bounds[PROJ_BUCKET_RIGHT]) &&
			(v[1] > bucket_bounds[PROJ_BUCKET_BOTTOM]) &&
			(v[1] < bucket_bounds[PROJ_BUCKET_TOP]) )
		{
			return 1;
		}
	} while (i--);
		
	v1 = ps->projectVertScreenCos[mf->v1];
	v2 = ps->projectVertScreenCos[mf->v2];
	v3 = ps->projectVertScreenCos[mf->v3];
	if (mf->v4) {
		v4 = ps->projectVertScreenCos[mf->v4];
	}
	
	p1[0] = bucket_bounds[PROJ_BUCKET_LEFT];	p1[1] = bucket_bounds[PROJ_BUCKET_BOTTOM];
	p2[0] = bucket_bounds[PROJ_BUCKET_LEFT];	p2[1] = bucket_bounds[PROJ_BUCKET_TOP];
	p3[0] = bucket_bounds[PROJ_BUCKET_RIGHT];	p3[1] = bucket_bounds[PROJ_BUCKET_TOP];
	p4[0] = bucket_bounds[PROJ_BUCKET_RIGHT];	p4[1] = bucket_bounds[PROJ_BUCKET_BOTTOM];
		
	if (mf->v4) {
		if(	IsectPQ2Df(p1, v1, v2, v3, v4) || IsectPQ2Df(p2, v1, v2, v3, v4) || IsectPQ2Df(p3, v1, v2, v3, v4) || IsectPQ2Df(p4, v1, v2, v3, v4) ||
			/* we can avoid testing v3,v1 because another intersection MUST exist if this intersects */
			(IsectLL2Df(p1,p2, v1, v2) || IsectLL2Df(p1,p2, v2, v3) || IsectLL2Df(p1,p2, v3, v4)) ||
			(IsectLL2Df(p2,p3, v1, v2) || IsectLL2Df(p2,p3, v2, v3) || IsectLL2Df(p2,p3, v3, v4)) ||
			(IsectLL2Df(p3,p4, v1, v2) || IsectLL2Df(p3,p4, v2, v3) || IsectLL2Df(p3,p4, v3, v4)) ||
			(IsectLL2Df(p4,p1, v1, v2) || IsectLL2Df(p4,p1, v2, v3) || IsectLL2Df(p4,p1, v3, v4))
		) {
			return 1;
		}
	} else {
		if(	IsectPT2Df(p1, v1, v2, v3) || IsectPT2Df(p2, v1, v2, v3) || IsectPT2Df(p3, v1, v2, v3) || IsectPT2Df(p4, v1, v2, v3) ||
			/* we can avoid testing v3,v1 because another intersection MUST exist if this intersects */
			(IsectLL2Df(p1,p2, v1, v2) || IsectLL2Df(p1,p2, v2, v3)) ||
			(IsectLL2Df(p2,p3, v1, v2) || IsectLL2Df(p2,p3, v2, v3)) ||
			(IsectLL2Df(p3,p4, v1, v2) || IsectLL2Df(p3,p4, v2, v3)) ||
			(IsectLL2Df(p4,p1, v1, v2) || IsectLL2Df(p4,p1, v2, v3))
		) {
			return 1;
		}
	}

	return 0;
}

static void project_paint_delayed_face_init(ProjectPaintState *ps, MFace *mf, MTFace *tf, int face_index)
{
	float min[2], max[2];
	int bucket_min[2], bucket_max[2]; /* for  ps->projectBuckets indexing */
	int i, a, bucket_x, bucket_y, bucket_index;

	INIT_MINMAX2(min,max);
	
	i = mf->v4 ? 3:2;
	do {
		a = (*(&mf->v1 + i)); /* vertex index */
		
		DO_MINMAX2(ps->projectVertScreenCos[ a ], min, max);
		
#ifndef PROJ_DEBUG_NOSEAMBLEED
		/* add face user if we have bleed enabled, set the UV seam flags later */
		if (ps->projectSeamBleed > 0.0) {
			BLI_linklist_prepend_arena(
				&ps->projectVertFaces[ a ],
				(void *)face_index, /* cast to a pointer to shut up the compiler */
				ps->projectArena
			);
		}
#endif
	} while (i--);
	
	project_paint_rect(ps, min, max, bucket_min, bucket_max);
	
	for (bucket_y = bucket_min[1]; bucket_y < bucket_max[1]; bucket_y++) {
		for (bucket_x = bucket_min[0]; bucket_x < bucket_max[0]; bucket_x++) {
			
			bucket_index = bucket_x + (bucket_y * ps->bucketsX);
			
			if (project_bucket_face_isect(ps, min, max, bucket_x, bucket_y, bucket_index, mf)) {
				BLI_linklist_prepend_arena(
					&ps->projectFaces[ bucket_index ],
					(void *)face_index, /* cast to a pointer to shut up the compiler */
					ps->projectArena
				);
			}
		}
	}
	
	if (ps->projectSeamBleed > 0.0) {
		if (!mf->v4) {
			ps->projectFaceSeamFlags[face_index] |= PROJ_FACE_NOSEAM4; /* so this wont show up as an untagged egde */
		}
		**ps->projectFaceSeamUVs[face_index] = MAXFLOAT; /* set as uninitialized */
	}
}

static int BLI_linklist_index(struct LinkNode *list, void *ptr)
{
	int index;
	
	for (index = 0; list; list= list->next, index++) {
		if (list->link == ptr)
			return index;
	}
	
	return -1;
}


static void project_paint_begin( ProjectPaintState *ps, short mval[2])
{	
	/* Viewport vars */
	float mat[3][3];
	float f_no[3];
	
	float projCo[4];
	float (*projScreenCo)[3];
	float projMargin;
	/* Image Vars - keep track of images we have used */
	LinkNode *image_LinkList = NULL;
	LinkNode *node;
	
	Image *tpage_last = NULL;
	ImBuf *ibuf = NULL;
	
	/* Face vars */
	MFace *mf;
	MTFace *tf;
	
	int a, i; /* generic looping vars */
	
	/* memory sized to add to arena size */
	int tot_bucketMem=0;
	int tot_faceSeamFlagMem=0;
	int tot_faceSeamUVMem=0;
	int tot_faceListMem=0;
	int tot_bucketFlagMem=0;
	int tot_bucketVertFacesMem=0;

	/* ---- end defines ---- */
	
	/* paint onto the derived mesh
	 * note get_viewedit_datamask checks for paint mode and will always give UVs */
	ps->dm = mesh_get_derived_final(ps->ob, get_viewedit_datamask());
	
	ps->dm_mvert = ps->dm->getVertArray( ps->dm );
	ps->dm_mface = ps->dm->getFaceArray( ps->dm );
	ps->dm_mtface= ps->dm->getFaceDataArray( ps->dm, CD_MTFACE );
	
	ps->dm_totvert = ps->dm->getNumVerts( ps->dm );
	ps->dm_totface = ps->dm->getNumFaces( ps->dm );
	
	ps->bucketsX = PROJ_BUCKET_DIV;
	ps->bucketsY = PROJ_BUCKET_DIV;
	
	ps->imaContextIndex = -1;
	
	ps->viewDir[0] = 0.0;
	ps->viewDir[1] = 0.0;
	ps->viewDir[2] = 1.0;
	
	view3d_get_object_project_mat(curarea, ps->ob, ps->projectMat, ps->viewMat);
	
	tot_bucketMem =				sizeof(LinkNode *) * ps->bucketsX * ps->bucketsY;
	tot_faceListMem =			sizeof(LinkNode *) * ps->bucketsX * ps->bucketsY;
	
	tot_bucketFlagMem =			sizeof(char) * ps->bucketsX * ps->bucketsY;
#ifndef PROJ_DEBUG_NOSEAMBLEED
	if (ps->projectSeamBleed > 0.0) { /* UV Seams for bleeding */
		tot_bucketVertFacesMem =	sizeof(LinkNode *) * ps->dm_totvert;
		tot_faceSeamFlagMem =		sizeof(char) * ps->dm_totface;
		tot_faceSeamUVMem =			sizeof(float) * ps->dm_totface * 8;
	}
#endif

	ps->projectArena =
		BLI_memarena_new(	tot_bucketMem +
							tot_faceListMem +
							tot_faceSeamFlagMem +
							tot_faceSeamUVMem +
							tot_bucketVertFacesMem + (1<<16));
	
	ps->projectBuckets = (LinkNode **)BLI_memarena_alloc( ps->projectArena, tot_bucketMem);
	ps->projectFaces= (LinkNode **)BLI_memarena_alloc( ps->projectArena, tot_faceListMem);
	
	ps->projectBucketFlags= (char *)BLI_memarena_alloc( ps->projectArena, tot_bucketFlagMem);
#ifndef PROJ_DEBUG_NOSEAMBLEED
	if (ps->projectSeamBleed > 0.0) {
		ps->projectVertFaces= (LinkNode **)BLI_memarena_alloc( ps->projectArena, tot_bucketVertFacesMem);
		ps->projectFaceSeamFlags = (char *)BLI_memarena_alloc( ps->projectArena, tot_faceSeamFlagMem);
		ps->projectFaceSeamUVs= BLI_memarena_alloc( ps->projectArena, tot_faceSeamUVMem);
	}
#endif
	
	memset(ps->projectBuckets,		0, tot_bucketMem);
	memset(ps->projectFaces,		0, tot_faceListMem);
	memset(ps->projectFaceSeamFlags,0, tot_faceSeamFlagMem);
	memset(ps->projectBucketFlags,	0, tot_bucketFlagMem);
#ifndef PROJ_DEBUG_NOSEAMBLEED
	if (ps->projectSeamBleed > 0.0) {
		memset(ps->projectVertFaces,	0, tot_bucketVertFacesMem);
		/* TODO dosnt need zeroing? */
		memset(ps->projectFaceSeamUVs,	0, tot_faceSeamUVMem);
	}
#endif
	Mat4Invert(ps->ob->imat, ps->ob->obmat);
	
	Mat3CpyMat4(mat, G.vd->viewinv);
	Mat3MulVecfl(mat, ps->viewDir);
	Mat3CpyMat4(mat, ps->ob->imat);
	Mat3MulVecfl(mat, ps->viewDir);
	
	/* calculate vert screen coords */
	ps->projectVertScreenCos = BLI_memarena_alloc( ps->projectArena, sizeof(float) * ps->dm_totvert * 3);
	projScreenCo = ps->projectVertScreenCos;
	
	/* TODO - check cameras mode too */
	if (G.vd->persp == V3D_ORTHO) {
		ps->projectIsOrtho = 1;
	}
	
	INIT_MINMAX2(ps->viewMin2D, ps->viewMax2D);
	
	for(a=0; a < ps->dm_totvert; a++, projScreenCo++) {
		VECCOPY(projCo, ps->dm_mvert[a].co);		
		
		projCo[3] = 1.0;
		Mat4MulVec4fl(ps->projectMat, projCo);
		
		if( projCo[3] > 0.001 ) {
			/* screen space, not clamped */
			(*projScreenCo)[0] = (float)(curarea->winx/2.0)+(curarea->winx/2.0)*projCo[0]/projCo[3];	
			(*projScreenCo)[1] = (float)(curarea->winy/2.0)+(curarea->winy/2.0)*projCo[1]/projCo[3];
			(*projScreenCo)[2] = projCo[2]/projCo[3]; /* Use the depth for bucket point occlusion */
			DO_MINMAX2((*projScreenCo), ps->viewMin2D, ps->viewMax2D);
		} else {
			/* TODO - deal with cases where 1 side of a face goes behind the view ? */
			(*projScreenCo)[0] = (*projScreenCo)[1] = MAXFLOAT;
		}
	}
	
	/* setup clone offset */
	if (ps->tool == PAINT_TOOL_CLONE) {
		float *curs= give_cursor();
		VECCOPY(projCo, curs); /* TODO - what if were in local view? - get some better way */
		Mat4MulVec4fl(ps->ob->imat, projCo);
		projCo[3] = 1.0;
		Mat4MulVec4fl(ps->projectMat, projCo);
		ps->cloneOfs[0] = mval[0] - ((float)(curarea->winx/2.0)+(curarea->winx/2.0)*projCo[0]/projCo[3]);
		ps->cloneOfs[1] = mval[1] - ((float)(curarea->winy/2.0)+(curarea->winy/2.0)*projCo[1]/projCo[3]);
		
		// printf("%f %f   %f %f %f\n", ps->cloneOfs[0], ps->cloneOfs[1], curs[0], curs[1], curs[2]);
		
	}
	
	/* If this border is not added we get artifacts for faces that
	 * have a paralelle edge and at the bounds of the the 2D projected verts eg
	 * - a simgle screen aligned quad */
	projMargin = (ps->viewMax2D[0] - ps->viewMin2D[0]) * 0.000001;
	ps->viewMax2D[0] += projMargin;
	ps->viewMin2D[0] -= projMargin;
	projMargin = (ps->viewMax2D[1] - ps->viewMin2D[1]) * 0.000001;
	ps->viewMax2D[1] += projMargin;
	ps->viewMin2D[1] -= projMargin;
	
	
	/* only for convenience */
	ps->viewWidth  = ps->viewMax2D[0] - ps->viewMin2D[0];
	ps->viewHeight = ps->viewMax2D[1] - ps->viewMin2D[1];
	
	for( a = 0, tf = ps->dm_mtface, mf = ps->dm_mface; a < ps->dm_totface; mf++, tf++, a++ ) {
		if (tf->tpage && ((G.f & G_FACESELECT)==0 || mf->flag & ME_FACE_SEL)) {
			
			if (ps->projectIsBackfaceCull) {
				/* TODO - we dont really need the normal, just the direction, save a sqrt? */
				if (mf->v4)	CalcNormFloat4(ps->dm_mvert[mf->v1].co, ps->dm_mvert[mf->v2].co, ps->dm_mvert[mf->v3].co, ps->dm_mvert[mf->v4].co, f_no);
				else		CalcNormFloat(ps->dm_mvert[mf->v1].co, ps->dm_mvert[mf->v2].co, ps->dm_mvert[mf->v3].co, f_no);
				
				if (Inpf(f_no, ps->viewDir) < 0) {
					continue;
				}
			}
			
			if (tpage_last != tf->tpage) {
				ibuf= BKE_image_get_ibuf((Image *)tf->tpage, NULL);
				
				if (ibuf) {
					ps->imaContextIndex = BLI_linklist_index(image_LinkList, tf->tpage);
					
					if (ps->imaContextIndex==-1) { /* MemArena dosnt have an append func */
						BLI_linklist_append(&image_LinkList, tf->tpage);
						ps->imaContextIndex = ps->projectImageTotal;
						ps->projectImageTotal++;
					}
				}
				
				tpage_last = tf->tpage;
			}
			
			if (ibuf) {
				/* Initialize the faces screen pixels */
				/* Add this to a list to initialize later */
				project_paint_delayed_face_init(ps, mf, tf, a);
			}
		}
	}
	
	/* build an array of images we use*/
	ps->projectImages = BLI_memarena_alloc( ps->projectArena, sizeof(Image *) * ps->projectImageTotal);
	
	for (node= image_LinkList, i=0; node; node= node->next, i++) {
		
		ps->projectImages[i] = node->link;
		ps->projectImages[i]->id.flag &= ~LIB_DOIT;
		// printf("'%s' %d\n", ps->projectImages[i]->id.name+2, i);
	}
	/* we have built the array, discard the linked list */
	BLI_linklist_free(image_LinkList, NULL);
}

static void project_paint_end( ProjectPaintState *ps )
{
	BLI_memarena_free(ps->projectArena);
	ps->dm->release(ps->dm);
}


/* external functions */

/* 1= an undo, -1 is a redo. */
void undo_imagepaint_step(int step)
{
	UndoElem *undo;

	if(step==1) {
		if(curundo==NULL) error("No more steps to undo");
		else {
			if(G.f & G_DEBUG) printf("undo %s\n", curundo->name);
			undo_restore(curundo);
			curundo= curundo->prev;
		}
	}
	else if(step==-1) {
		if((curundo!=NULL && curundo->next==NULL) || undobase.first==NULL) error("No more steps to redo");
		else {
			undo= (curundo && curundo->next)? curundo->next: undobase.first;
			undo_restore(undo);
			curundo= undo;
			if(G.f & G_DEBUG) printf("redo %s\n", undo->name);
		}
	}

	allqueue(REDRAWVIEW3D, 0);
	allqueue(REDRAWIMAGE, 0);
}

void undo_imagepaint_clear(void)
{
	UndoElem *uel;
	
	uel= undobase.first;
	while(uel) {
		undo_free(uel);
		uel= uel->next;
	}

	BLI_freelistN(&undobase);
	curundo= NULL;
}

/* Imagepaint Partial Redraw & Dirty Region */

static void imapaint_clear_partial_redraw()
{
	memset(&imapaintpartial, 0, sizeof(imapaintpartial));
}

static void imapaint_dirty_region(Image *ima, ImBuf *ibuf, int x, int y, int w, int h)
{
	ImBuf *tmpibuf;
	UndoTile *tile;
	int srcx= 0, srcy= 0, origx, allocsize;

	IMB_rectclip(ibuf, NULL, &x, &y, &srcx, &srcy, &w, &h);

	if (w == 0 || h == 0)
		return;
	
	if (!imapaintpartial.enabled) {
		imapaintpartial.x1 = x;
		imapaintpartial.y1 = y;
		imapaintpartial.x2 = x+w;
		imapaintpartial.y2 = y+h;
		imapaintpartial.enabled = 1;
	}
	else {
		imapaintpartial.x1 = MIN2(imapaintpartial.x1, x);
		imapaintpartial.y1 = MIN2(imapaintpartial.y1, y);
		imapaintpartial.x2 = MAX2(imapaintpartial.x2, x+w);
		imapaintpartial.y2 = MAX2(imapaintpartial.y2, y+h);
	}

	w = ((x + w - 1) >> IMAPAINT_TILE_BITS);
	h = ((y + h - 1) >> IMAPAINT_TILE_BITS);
	origx = (x >> IMAPAINT_TILE_BITS);
	y = (y >> IMAPAINT_TILE_BITS);

	tmpibuf= IMB_allocImBuf(IMAPAINT_TILE_SIZE, IMAPAINT_TILE_SIZE, 32,
	                        IB_rectfloat|IB_rect, 0);
	
	for (; y <= h; y++) {
		for (x=origx; x <= w; x++) {
			for(tile=curundo->tiles.first; tile; tile=tile->next)
				if(tile->x == x && tile->y == y && strcmp(tile->id.name, ima->id.name)==0)
					break;

			if(!tile) {
				tile= MEM_callocN(sizeof(UndoTile), "ImaUndoTile");
				tile->id= ima->id;
				tile->x= x;
				tile->y= y;

				allocsize= IMAPAINT_TILE_SIZE*IMAPAINT_TILE_SIZE*4;
				allocsize *= (ibuf->rect_float)? sizeof(float): sizeof(char);
				tile->rect= MEM_mapallocN(allocsize, "ImaUndoRect");

				undo_copy_tile(tile, tmpibuf, ibuf, 0);
				curundo->undosize += allocsize;

				BLI_addtail(&curundo->tiles, tile);
			}
		}
	}

	ibuf->userflags |= IB_BITMAPDIRTY;

	IMB_freeImBuf(tmpibuf);
}

static void imapaint_image_update(Image *image, ImBuf *ibuf, short texpaint)
{
	if(ibuf->rect_float)
		imb_freerectImBuf(ibuf); /* force recreate of char rect */
	if(ibuf->mipmap[0])
		imb_freemipmapImBuf(ibuf);

	/* todo: should set_tpage create ->rect? */
	if(texpaint || G.sima->lock) {
		int w = imapaintpartial.x2 - imapaintpartial.x1;
		int h = imapaintpartial.y2 - imapaintpartial.y1;
		GPU_paint_update_image(image, imapaintpartial.x1, imapaintpartial.y1, w, h);
	}
}

/* note; gets called for both 2d image paint and 3d texture paint. in the
   latter case image may be NULL and G.sima may not exist */
static void imapaint_redraw(int final, int texpaint, Image *image)
{
	if(final) {
		if(texpaint)
			allqueue(REDRAWIMAGE, 0);
		else if(!G.sima->lock) {
			if(image)
				GPU_free_image(image); /* force OpenGL reload */
			allqueue(REDRAWVIEW3D, 0);
		}
		allqueue(REDRAWHEADERS, 0);
		
		if(!texpaint && image) {
			/* after paint, tag Image or RenderResult nodes changed */
			if(G.scene->nodetree) {
				imagepaint_composite_tags(G.scene->nodetree, image, &G.sima->iuser);
			}
			/* signal composite (hurmf, need an allqueue?) */
			if(G.sima->lock) {
				ScrArea *sa;
				for(sa=G.curscreen->areabase.first; sa; sa= sa->next) {
					if(sa->spacetype==SPACE_NODE) {
						if(((SpaceNode *)sa->spacedata.first)->treetype==NTREE_COMPOSIT) {
							addqueue(sa->win, UI_BUT_EVENT, B_NODE_TREE_EXEC);
							break;
						}
					}
				}
			}
		}		
	}
	else if(!texpaint && G.sima->lock)
		force_draw_plus(SPACE_VIEW3D, 0);
	else
		force_draw(0);
}

/* Image Paint Operations */

static void imapaint_ibuf_get_set_rgb(ImBuf *ibuf, int x, int y, short torus, short set, float *rgb)
{
	if (torus) {
		x %= ibuf->x;
		if (x < 0) x += ibuf->x;
		y %= ibuf->y;
		if (y < 0) y += ibuf->y;
	}

	if (ibuf->rect_float) {
		float *rrgbf = ibuf->rect_float + (ibuf->x*y + x)*4;

		if (set) IMAPAINT_FLOAT_RGB_COPY(rrgbf, rgb)
		else IMAPAINT_FLOAT_RGB_COPY(rgb, rrgbf)
	}
	else {
		char *rrgb = (char*)ibuf->rect + (ibuf->x*y + x)*4;

		if (set) IMAPAINT_FLOAT_RGB_TO_CHAR(rrgb, rgb)
		else IMAPAINT_CHAR_RGB_TO_FLOAT(rgb, rrgb)
	}
}

static int imapaint_ibuf_add_if(ImBuf *ibuf, unsigned int x, unsigned int y, float *outrgb, short torus)
{
	float inrgb[3];

	if ((x >= ibuf->x) || (y >= ibuf->y)) {
		if (torus) imapaint_ibuf_get_set_rgb(ibuf, x, y, 1, 0, inrgb);
		else return 0;
	}
	else imapaint_ibuf_get_set_rgb(ibuf, x, y, 0, 0, inrgb);

	outrgb[0] += inrgb[0];
	outrgb[1] += inrgb[1];
	outrgb[2] += inrgb[2];

	return 1;
}

static void imapaint_lift_soften(ImBuf *ibuf, ImBuf *ibufb, int *pos, short torus)
{
	int x, y, count, xi, yi, xo, yo;
	int out_off[2], in_off[2], dim[2];
	float outrgb[3];

	dim[0] = ibufb->x;
	dim[1] = ibufb->y;
	in_off[0] = pos[0];
	in_off[1] = pos[1];
	out_off[0] = out_off[1] = 0;

	if (!torus) {
		IMB_rectclip(ibuf, ibufb, &in_off[0], &in_off[1], &out_off[0],
			&out_off[1], &dim[0], &dim[1]);

		if ((dim[0] == 0) || (dim[1] == 0))
			return;
	}

	for (y=0; y < dim[1]; y++) {
		for (x=0; x < dim[0]; x++) {
			/* get input pixel */
			xi = in_off[0] + x;
			yi = in_off[1] + y;

			count = 1;
			imapaint_ibuf_get_set_rgb(ibuf, xi, yi, torus, 0, outrgb);

			count += imapaint_ibuf_add_if(ibuf, xi-1, yi-1, outrgb, torus);
			count += imapaint_ibuf_add_if(ibuf, xi-1, yi  , outrgb, torus);
			count += imapaint_ibuf_add_if(ibuf, xi-1, yi+1, outrgb, torus);

			count += imapaint_ibuf_add_if(ibuf, xi  , yi-1, outrgb, torus);
			count += imapaint_ibuf_add_if(ibuf, xi  , yi+1, outrgb, torus);

			count += imapaint_ibuf_add_if(ibuf, xi+1, yi-1, outrgb, torus);
			count += imapaint_ibuf_add_if(ibuf, xi+1, yi  , outrgb, torus);
			count += imapaint_ibuf_add_if(ibuf, xi+1, yi+1, outrgb, torus);

			outrgb[0] /= count;
			outrgb[1] /= count;
			outrgb[2] /= count;

			/* write into brush buffer */
			xo = out_off[0] + x;
			yo = out_off[1] + y;
			imapaint_ibuf_get_set_rgb(ibufb, xo, yo, 0, 1, outrgb);
		}
	}
}

static void imapaint_lift_smear(ImBuf *ibuf, ImBuf *ibufb, int *pos)
{
	IMB_rectblend_torus(ibufb, ibuf, 0, 0, pos[0], pos[1],
		ibufb->x, ibufb->y, IMB_BLEND_COPY_RGB);
}

static ImBuf *imapaint_lift_clone(ImBuf *ibuf, ImBuf *ibufb, int *pos)
{
	/* note: allocImbuf returns zero'd memory, so regions outside image will
	   have zero alpha, and hence not be blended onto the image */
	int w=ibufb->x, h=ibufb->y, destx=0, desty=0, srcx=pos[0], srcy=pos[1];
	ImBuf *clonebuf= IMB_allocImBuf(w, h, ibufb->depth, ibufb->flags, 0);

	IMB_rectclip(clonebuf, ibuf, &destx, &desty, &srcx, &srcy, &w, &h);
	IMB_rectblend(clonebuf, ibuf, destx, desty, srcx, srcy, w, h,
		IMB_BLEND_COPY_RGB);
	IMB_rectblend(clonebuf, ibufb, destx, desty, destx, desty, w, h,
		IMB_BLEND_COPY_ALPHA);

	return clonebuf;
}

static void imapaint_convert_brushco(ImBuf *ibufb, float *pos, int *ipos)
{
	ipos[0]= (int)(pos[0] - ibufb->x/2);
	ipos[1]= (int)(pos[1] - ibufb->y/2);
}

/* dosnt run for projection painting
 * only the old style painting in the 3d view */
static int imapaint_paint_op(void *state, ImBuf *ibufb, float *lastpos, float *pos)
{
	ImagePaintState *s= ((ImagePaintState*)state);
	ImBuf *clonebuf= NULL;
	short torus= s->brush->flag & BRUSH_TORUS;
	short blend= s->blend;
	float *offset= s->brush->clone.offset;
	float liftpos[2];
	int bpos[2], blastpos[2], bliftpos[2];

	imapaint_convert_brushco(ibufb, pos, bpos);

	/* lift from canvas */
	if(s->tool == PAINT_TOOL_SOFTEN) {
		imapaint_lift_soften(s->canvas, ibufb, bpos, torus);
	}
	else if(s->tool == PAINT_TOOL_SMEAR) {
		if (lastpos[0]==pos[0] && lastpos[1]==pos[1])
			return 0;

		imapaint_convert_brushco(ibufb, lastpos, blastpos);
		imapaint_lift_smear(s->canvas, ibufb, blastpos);
	}
	else if(s->tool == PAINT_TOOL_CLONE && s->clonecanvas) {
		liftpos[0]= pos[0] - offset[0]*s->canvas->x;
		liftpos[1]= pos[1] - offset[1]*s->canvas->y;

		imapaint_convert_brushco(ibufb, liftpos, bliftpos);
		clonebuf= imapaint_lift_clone(s->clonecanvas, ibufb, bliftpos);
	}

	imapaint_dirty_region(s->image, s->canvas, bpos[0], bpos[1], ibufb->x, ibufb->y);

	/* blend into canvas */
	if(torus)
		IMB_rectblend_torus(s->canvas, (clonebuf)? clonebuf: ibufb,
			bpos[0], bpos[1], 0, 0, ibufb->x, ibufb->y, blend);
	else
		IMB_rectblend(s->canvas, (clonebuf)? clonebuf: ibufb,
			bpos[0], bpos[1], 0, 0, ibufb->x, ibufb->y, blend);
			
	if(clonebuf) IMB_freeImBuf(clonebuf);

	return 1;
}

/* 2D ImagePaint */

static void imapaint_compute_uvco(short *mval, float *uv)
{
	areamouseco_to_ipoco(G.v2d, mval, &uv[0], &uv[1]);
}

/* 3D TexturePaint */

int facesel_face_pick(Mesh *me, short *mval, unsigned int *index, short rect);
void texpaint_pick_uv(Object *ob, Mesh *mesh, unsigned int faceindex, short *xy, float *mousepos);

static int texpaint_break_stroke(float *prevuv, float *fwuv, float *bkuv, float *uv)
{
	float d1[2], d2[2];
	float mismatch = Vec2Lenf(fwuv, uv);
	float len1 = Vec2Lenf(prevuv, fwuv);
	float len2 = Vec2Lenf(bkuv, uv);

	Vec2Subf(d1, fwuv, prevuv);
	Vec2Subf(d2, uv, bkuv);

	return ((Inp2f(d1, d2) < 0.0f) || (mismatch > MAX2(len1, len2)*2));
}

/* ImagePaint Common */

static int imapaint_canvas_set(ImagePaintState *s, Image *ima)
{
	ImBuf *ibuf= BKE_image_get_ibuf(ima, G.sima?&G.sima->iuser:NULL);
	
	/* verify that we can paint and set canvas */
	if(ima->packedfile && ima->rr) {
		s->warnpackedfile = ima->id.name + 2;
		return 0;
	}	
	else if(ibuf && ibuf->channels!=4) {
		s->warnmultifile = ima->id.name + 2;
		return 0;
	}
	else if(!ima || !ibuf || !(ibuf->rect || ibuf->rect_float))
		return 0;

	s->image= ima;
	s->canvas= ibuf;

	/* set clone canvas */
	if(s->tool == PAINT_TOOL_CLONE) {
		ima= s->brush->clone.image;
		ibuf= BKE_image_get_ibuf(ima, G.sima?&G.sima->iuser:NULL);
		
		if(!ima || !ibuf || !(ibuf->rect || ibuf->rect_float))
			return 0;

		s->clonecanvas= ibuf;

		if(s->canvas->rect_float && !s->clonecanvas->rect_float) {
			/* temporarily add float rect for cloning */
			IMB_float_from_rect(s->clonecanvas);
			s->clonefreefloat= 1;
		}
		else if(!s->canvas->rect_float && !s->clonecanvas->rect)
			IMB_rect_from_float(s->clonecanvas);
	}

	return 1;
}

static void imapaint_canvas_free(ImagePaintState *s)
{
	if (s->clonefreefloat)
		imb_freerectfloatImBuf(s->clonecanvas);
}

static int imapaint_paint_sub_stroke(ImagePaintState *s, BrushPainter *painter, Image *image, short texpaint, float *uv, double time, int update, float pressure)
{
	ImBuf *ibuf= BKE_image_get_ibuf(image, G.sima?&G.sima->iuser:NULL);
	float pos[2];

	if(!ibuf)
		return 0;

	pos[0] = uv[0]*ibuf->x;
	pos[1] = uv[1]*ibuf->y;

	brush_painter_require_imbuf(painter, ((ibuf->rect_float)? 1: 0), 0, 0);

	if (brush_painter_paint(painter, imapaint_paint_op, pos, time, pressure, s)) {
		if (update)
			imapaint_image_update(image, ibuf, texpaint);
		return 1;
	}
	else return 0;
}

static float Vec2Lenf_nosqrt(float *v1, float *v2)
{
	float x, y;

	x = v1[0]-v2[0];
	y = v1[1]-v2[1];
	return x*x+y*y;
}

static float Vec2Lenf_nosqrt_other(float *v1, float v2_1, float v2_2)
{
	float x, y;

	x = v1[0]-v2_1;
	y = v1[1]-v2_2;
	return x*x+y*y;
}

/* note, use a squared value so we can use Vec2Lenf_nosqrt
 * be sure that you have done a bounds check first or this may fail */
/* only give bucket_bounds as an arg because we need it elsewhere */
static int project_bucket_circle_isect(ProjectPaintState *ps, int bucket_x, int bucket_y, float cent[2], float radius_squared, float bucket_bounds[4])
{
	// printf("%d %d - %f %f %f %f - %f %f \n", bucket_x, bucket_y, bucket_bounds[0], bucket_bounds[1], bucket_bounds[2], bucket_bounds[3], cent[0], cent[1]);

	/* first check if we are INSIDE the bucket */
	/* if (	bucket_bounds[PROJ_BUCKET_LEFT] <=	cent[0] &&
			bucket_bounds[PROJ_BUCKET_RIGHT] >=	cent[0] &&
			bucket_bounds[PROJ_BUCKET_BOTTOM] <=	cent[1] &&
			bucket_bounds[PROJ_BUCKET_TOP] >=	cent[1]	)
	{
		return 1;
	}*/
	
	/* Would normally to a simple intersection test, however we know the bounds of these 2 alredy intersect 
	 * so we only need to test if the center is inside the vertical or horizontal bounds on either axis,
	 * this is even less work then an intersection test */
	if (  (	bucket_bounds[PROJ_BUCKET_LEFT] <=		cent[0] &&
			bucket_bounds[PROJ_BUCKET_RIGHT] >=		cent[0]) ||
		  (	bucket_bounds[PROJ_BUCKET_BOTTOM] <=	cent[1] &&
			bucket_bounds[PROJ_BUCKET_TOP] >=		cent[1]) )
	{
		return 1;
	}
	 
	/* out of bounds left */
	if (cent[0] < bucket_bounds[PROJ_BUCKET_LEFT]) {
		/* lower left out of radius test */
		if (cent[1] < bucket_bounds[PROJ_BUCKET_BOTTOM]) {
			return (Vec2Lenf_nosqrt_other(cent, bucket_bounds[PROJ_BUCKET_LEFT], bucket_bounds[PROJ_BUCKET_BOTTOM]) < radius_squared) ? 1 : 0;
		} 
		/* top left test */
		else if (cent[1] > bucket_bounds[PROJ_BUCKET_TOP]) {
			return (Vec2Lenf_nosqrt_other(cent, bucket_bounds[PROJ_BUCKET_LEFT], bucket_bounds[PROJ_BUCKET_TOP]) < radius_squared) ? 1 : 0;
		}
	}
	else if (cent[0] > bucket_bounds[PROJ_BUCKET_RIGHT]) {
		/* lower right out of radius test */
		if (cent[1] < bucket_bounds[PROJ_BUCKET_BOTTOM]) {
			return (Vec2Lenf_nosqrt_other(cent, bucket_bounds[PROJ_BUCKET_RIGHT], bucket_bounds[PROJ_BUCKET_BOTTOM]) < radius_squared) ? 1 : 0;
		} 
		/* top right test */
		else if (cent[1] > bucket_bounds[PROJ_BUCKET_TOP]) {
			return (Vec2Lenf_nosqrt_other(cent, bucket_bounds[PROJ_BUCKET_RIGHT], bucket_bounds[PROJ_BUCKET_TOP]) < radius_squared) ? 1 : 0;
		}
	}
	
	return 0;
}

static int imapaint_paint_sub_stroke_project(ProjectPaintState *ps, BrushPainter *painter, short prevmval[2], short mval[2], double time, int update, float pressure)
{
	/* TODO - texpaint option : is there any use in projection painting from the image window??? - could be interesting */
	/* TODO - floating point images */
	//bucketWidth = ps->viewWidth/ps->bucketsX;
	//bucketHeight = ps->viewHeight/ps->bucketsY;

	LinkNode *node;
	float mval_f[2];
	ProjectPixel *projPixel;
	int redraw = 0;
	int last_index = -1;
	float rgba[4], alpha, dist, dist_nosqrt;
	char rgba_ub[4];
	float brush_size_sqared;
	float min[2], max[2]; /* brush bounds in screenspace */
	int bucket_min[2], bucket_max[2]; /* brush bounds in bucket grid space */
	int bucket_index;
	int a;
	short blend= ps->blend;
	char *cp;
	
	float bucket_bounds[4];
	int bucket_x, bucket_y;
	
	
	/* for smear only */
	float mval_ofs[2]; 
	float co[2];
	LinkNode *smearPixels = NULL;
	MemArena *smearArena = NULL; /* mem arena for this brush projection only */
	
	mval_f[0] = mval[0]; mval_f[1] = mval[1]; 
	
	min[0] = mval_f[0] - (ps->brush->size/2);
	min[1] = mval_f[1] - (ps->brush->size/2);
	
	max[0] = mval_f[0] + (ps->brush->size/2);
	max[1] = mval_f[1] + (ps->brush->size/2);
	
	/* offset to make this a valid bucket index */
	project_paint_rect(ps, min, max, bucket_min, bucket_max);
	
	/* mouse outside the model areas? */
	if (bucket_min[0]==bucket_max[0] || bucket_min[1]==bucket_max[1]) {
		return 0;
	}
	
	if (ps->tool==PAINT_TOOL_SMEAR) {
		mval_ofs[0] = (float)(mval[0] - prevmval[0]);
		mval_ofs[1] = (float)(mval[1] - prevmval[1]);
		
		smearArena = BLI_memarena_new(1<<16);
	}
	
	/* avoid a square root with every dist comparison */
	brush_size_sqared = ps->brush->size * ps->brush->size; 
	
	/* printf("brush bounds %d %d %d %d\n", bucket_min[0], bucket_min[1], bucket_max[0], bucket_max[1]); */
	
	/* If there is ever problems with getting the bounds for the brush, set the bounds to include all */
	/*bucket_min[0] = 0; bucket_min[1] = 0; bucket_max[0] = ps->bucketsX; bucket_max[1] = ps->bucketsY;*/
	
	/* no clamping needed, dont use screen bounds, use vert bounds  */
	
	for (bucket_y = bucket_min[1]; bucket_y < bucket_max[1]; bucket_y++) {
		for (bucket_x = bucket_min[0]; bucket_x < bucket_max[0]; bucket_x++) {
			
			/* use bucket_bounds for project_bucket_circle_isect and project_paint_bucket_init*/
			project_bucket_bounds(ps, bucket_x, bucket_y, bucket_bounds);
			
			if (project_bucket_circle_isect(ps, bucket_x, bucket_y, mval_f, brush_size_sqared, bucket_bounds)) {
				
				bucket_index = bucket_x + (bucket_y * ps->bucketsX);
				
				/* Check this bucket and its faces are initialized */
				if (ps->projectBucketFlags[bucket_index] == PROJ_BUCKET_NULL) {
					/* No pixels initialized */
					project_paint_bucket_init(ps, bucket_index, bucket_bounds);
				}
				
				/* TODO - we may want to init clone data in a seperate to project_paint_bucket_init
				 * so we dont go overboard and init too many clone pixels  */

				if ((node = ps->projectBuckets[bucket_index])) {
				
					do {
						projPixel = (ProjectPixel *)node->link;
#ifdef PROJ_DEBUG_PAINT
						projPixel->pixel[0] = 0; // use for checking if the starting radius is too big
#endif
						
						/*dist = Vec2Lenf(projPixel->projCo2D, mval_f);*/ /* correct but uses a sqrt */
						dist_nosqrt = Vec2Lenf_nosqrt(projPixel->projCo2D, mval_f);
						
						/*if (dist < s->brush->size) {*/ /* correct but uses a sqrt */
						if (dist_nosqrt < brush_size_sqared) {
							
							dist = (float)sqrt(dist_nosqrt);
							
							switch(ps->tool) {
							case PAINT_TOOL_CLONE:
								if (((char *)((ProjectPixelClone*)projPixel)->clonebuf)[3]) {
									alpha = brush_sample_falloff(ps->brush, dist);
									if (alpha <= 0.0) {
										/* do nothing */
									} else {
										cp = (char *)((ProjectPixelClone*)projPixel)->clonebuf;
										if (alpha >= 1.0) {
											projPixel->pixel[0] = cp[0];
											projPixel->pixel[1] = cp[1];
											projPixel->pixel[2] = cp[2];
										} else {
											projPixel->pixel[0] = FTOCHAR( (((cp[0]/255.0) * alpha) + (((projPixel->pixel[0])/255.0)*(1.0-alpha))) );
											projPixel->pixel[1] = FTOCHAR( (((cp[1]/255.0) * alpha) + (((projPixel->pixel[1])/255.0)*(1.0-alpha))) );
											projPixel->pixel[2] = FTOCHAR( (((cp[2]/255.0) * alpha) + (((projPixel->pixel[2])/255.0)*(1.0-alpha))) );
										}
									}
									
								}
								break;
							case PAINT_TOOL_SMEAR:
								Vec2Subf(co, projPixel->projCo2D, mval_ofs);
								if (screenco_pickcol(ps, co, rgba_ub, 1)) {
									brush_sample_tex(ps->brush, projPixel->projCo2D, rgba);
									alpha = rgba[3]*brush_sample_falloff(ps->brush, dist);
									/* drat! - this could almost be very simple if we ignore
									 * the fact that applying the color directly gives feedback,
									 * instead, collect the colors and apply after :/ */
									
#if 0								/* looks OK but not correct */
									*((unsigned int *)projPixel->pixel) = IMB_blend_color( *((unsigned int *)projPixel->pixel), *((unsigned int *)rgba_ub), (int)(alpha*255), blend);
#endif
									
									/* add to memarena instead */
									*((unsigned int *) &((ProjectPixelClone *)projPixel)->clonebuf) = IMB_blend_color( *((unsigned int *)projPixel->pixel), *((unsigned int *)rgba_ub), (int)(alpha*255), blend);
									BLI_linklist_prepend_arena(
										&smearPixels,
										(void *)projPixel,
										smearArena
									);
									
								}
								break;
							default:
								brush_sample_tex(ps->brush, projPixel->projCo2D, rgba);
								alpha = rgba[3]*brush_sample_falloff(ps->brush, dist);
								if (alpha > 0.0) {
									rgba_ub[0] = FTOCHAR(rgba[0] * ps->brush->rgb[0]);
									rgba_ub[1] = FTOCHAR(rgba[1] * ps->brush->rgb[1]);
									rgba_ub[2] = FTOCHAR(rgba[2] * ps->brush->rgb[2]);
									rgba_ub[3] = FTOCHAR(rgba[3]);
									
									*((unsigned int *)projPixel->pixel) = IMB_blend_color( *((unsigned int *)projPixel->pixel), *((unsigned int *)rgba_ub), (int)(alpha*255), blend);
								}
								break;
								
							}
							
							
							if (last_index != projPixel->image_index) {
								last_index = projPixel->image_index;
								ps->projectImages[last_index]->id.flag |= LIB_DOIT;
							}
						}
						
						node = node->next;
					} while (node);
				}
			}
		}
	}

	
	if (ps->tool==PAINT_TOOL_SMEAR) {
		if ((node = smearPixels)) {
			do {
				projPixel = node->link;
				*((unsigned int *)projPixel->pixel) = *((unsigned int *)(((ProjectPixelClone *)projPixel)->clonebuf));
				node = node->next;
			} while (node);
		}
		
		BLI_memarena_free(smearArena);
	}
	/* Loop over all images on this mesh and update any we have touched */
	for (a=0; a < ps->projectImageTotal; a++) {
		Image *ima = ps->projectImages[a];
		if (ima->id.flag & LIB_DOIT) {
			imapaint_image_update(ima, BKE_image_get_ibuf(ima, NULL), 1 /*texpaint*/ );
			redraw = 1;
			
			ima->id.flag &= ~LIB_DOIT; /* clear for reuse */
		}
	}
	return redraw;
}


static void imapaint_paint_stroke(ImagePaintState *s, BrushPainter *painter, short texpaint, short *prevmval, short *mval, double time, float pressure)
{
	Image *newimage = NULL;
	float fwuv[2], bkuv[2], newuv[2];
	unsigned int newfaceindex;
	int breakstroke = 0, redraw = 0;

	if (texpaint) {
		/* pick new face and image */
		if (	facesel_face_pick(s->me, mval, &newfaceindex, 0) &&
				((G.f & G_FACESELECT)==0 || (s->me->mface+newfaceindex)->flag & ME_FACE_SEL)
		) {
			ImBuf *ibuf;
			
			newimage = (Image*)((s->me->mtface+newfaceindex)->tpage);
			ibuf= BKE_image_get_ibuf(newimage, G.sima?&G.sima->iuser:NULL);

			if(ibuf && ibuf->rect)
				texpaint_pick_uv(s->ob, s->me, newfaceindex, mval, newuv);
			else {
				newimage = NULL;
				newuv[0] = newuv[1] = 0.0f;
			}
		}
		else
			newuv[0] = newuv[1] = 0.0f;

		/* see if stroke is broken, and if so finish painting in old position */
		if (s->image) {
			texpaint_pick_uv(s->ob, s->me, s->faceindex, mval, fwuv);
			texpaint_pick_uv(s->ob, s->me, newfaceindex, prevmval, bkuv);

			if (newimage == s->image)
				breakstroke= texpaint_break_stroke(s->uv, fwuv, bkuv, newuv);
			else
				breakstroke= 1;
		}
		else
			fwuv[0]= fwuv[1]= 0.0f;

		if (breakstroke) {
			texpaint_pick_uv(s->ob, s->me, s->faceindex, mval, fwuv);
			redraw |= imapaint_paint_sub_stroke(s, painter, s->image, texpaint,
				fwuv, time, 1, pressure);
			imapaint_clear_partial_redraw();
			brush_painter_break_stroke(painter);
		}

		/* set new canvas */
		if (newimage && (newimage != s->image))
			if (!imapaint_canvas_set(s, newimage))
				newimage = NULL;

		/* paint in new image */
		if (newimage) {
			if (breakstroke)
				redraw|= imapaint_paint_sub_stroke(s, painter, newimage,
					texpaint, bkuv, time, 0, pressure);
			redraw|= imapaint_paint_sub_stroke(s, painter, newimage, texpaint,
				newuv, time, 1, pressure);
		}

		/* update state */
		s->image = newimage;
		s->faceindex = newfaceindex;
		s->uv[0] = newuv[0];
		s->uv[1] = newuv[1];
	}
	else {
		imapaint_compute_uvco(mval, newuv);
		redraw |= imapaint_paint_sub_stroke(s, painter, s->image, texpaint, newuv,
			time, 1, pressure);
	}

	if (redraw) {
		imapaint_redraw(0, texpaint, NULL);
		imapaint_clear_partial_redraw();
	}
}

static void imapaint_paint_stroke_project(ProjectPaintState *ps, BrushPainter *painter, short *prevmval, short *mval, double time, float pressure)
{
	int redraw = 0;
	
	/* TODO - support more brush operations, airbrush etc */
	{
		redraw |= imapaint_paint_sub_stroke_project(ps, painter, prevmval, mval, time, 1, pressure);
	}
	
	if (redraw) {
		imapaint_redraw(0, 1/*texpaint*/, NULL);
		imapaint_clear_partial_redraw();
	}
}

void imagepaint_paint(short mousebutton, short texpaint)
{
	ImagePaintState s;
	ProjectPaintState ps;
	BrushPainter *painter;
	ToolSettings *settings= G.scene->toolsettings;
	short prevmval[2], mval[2], project = 0;
	double time;
	float pressure;

	if(!settings->imapaint.brush)
		return;
	
	project = texpaint;
	
	
	if (G.qual & LR_CTRLKEY) {
		mouse_cursor();
		return;
	}
	
	/* initialize state */
	memset(&s, 0, sizeof(s));
	memset(&ps, 0, sizeof(ps));
	
	s.brush = settings->imapaint.brush;
	s.tool = settings->imapaint.tool;
	if(texpaint && (project==0) && (s.tool == PAINT_TOOL_CLONE))
		s.tool = PAINT_TOOL_DRAW;
	s.blend = s.brush->blend;
	
	if (project) {
		ps.brush = s.brush;
		ps.tool = s.tool;
		ps.blend = s.blend;
	}
	
	if(texpaint) {
		ps.ob = s.ob = OBACT;
		if (!s.ob || !(s.ob->lay & G.vd->lay)) return;
		s.me = get_mesh(s.ob);
		if (!s.me) return;

		persp(PERSP_VIEW);
	}
	else {
		s.image = G.sima->image;

		if(!imapaint_canvas_set(&s, G.sima->image)) {
			if(s.warnmultifile)
				error("Image requires 4 color channels to paint");
			if(s.warnpackedfile)
				error("Packed MultiLayer files cannot be painted");
			return;
		}
	}

	settings->imapaint.flag |= IMAGEPAINT_DRAWING;
	undo_imagepaint_push_begin("Image Paint");

	/* create painter and paint once */
	painter= brush_painter_new(s.brush);

	getmouseco_areawin(mval);

	pressure = get_pressure();
	s.blend = (get_activedevice() == 2)? BRUSH_BLEND_ERASE_ALPHA: s.brush->blend;
	
	time= PIL_check_seconds_timer();
	prevmval[0]= mval[0];
	prevmval[1]= mval[1];
	
	if (project) {
		/* setup projection painting data */
		ps.projectIsBackfaceCull = 1;
		ps.projectIsOcclude = 1;
#ifndef PROJ_DEBUG_NOSEAMBLEED
		ps.projectSeamBleed = 2.0; /* pixel num to bleed  */
#endif
		project_paint_begin(&ps, mval);
		
	} else {
		if (!((s.brush->flag & (BRUSH_ALPHA_PRESSURE|BRUSH_SIZE_PRESSURE|
			BRUSH_SPACING_PRESSURE|BRUSH_RAD_PRESSURE)) && (get_activedevice() != 0) && (pressure >= 0.99f)))
			imapaint_paint_stroke(&s, painter, texpaint, prevmval, mval, time, pressure);
	}
	/* paint loop */
	do {
		getmouseco_areawin(mval);

		pressure = get_pressure();
		s.blend = (get_activedevice() == 2)? BRUSH_BLEND_ERASE_ALPHA: s.brush->blend;
			
		time= PIL_check_seconds_timer();

		if (project) { /* Projection Painting */
			/* TODO - brush outline, dosnt work yet */
			/*
			persp(PERSP_WIN);
			fdrawXORcirc(mval[0], mval[1], ps.brush->size);
			draw_sel_circle(mval, prevmval, ps.brush->size, ps.brush->size, 0);
			persp(PERSP_VIEW);
			*/
			if((mval[0] != prevmval[0]) || (mval[1] != prevmval[1])) {
				imapaint_paint_stroke_project(&ps, painter, prevmval, mval, time, pressure);
				prevmval[0]= mval[0];
				prevmval[1]= mval[1];
			} else
				BIF_wait_for_statechange();
		} else {
			if((mval[0] != prevmval[0]) || (mval[1] != prevmval[1])) {
				imapaint_paint_stroke(&s, painter, texpaint, prevmval, mval, time, pressure);
				prevmval[0]= mval[0];
				prevmval[1]= mval[1];
			}
			else if (s.brush->flag & BRUSH_AIRBRUSH)
				imapaint_paint_stroke(&s, painter, texpaint, prevmval, mval, time, pressure);
			else
				BIF_wait_for_statechange();
		}
		/* do mouse checking at the end, so don't check twice, and potentially
		   miss a short tap */
	} while(get_mbut() & mousebutton);

	/* clean up */
	settings->imapaint.flag &= ~IMAGEPAINT_DRAWING;
	imapaint_canvas_free(&s);
	brush_painter_free(painter);

	if (project) {
		project_paint_end(&ps);
	}
	
	imapaint_redraw(1, texpaint, s.image);
	undo_imagepaint_push_end();
	
	if (texpaint) {
		if (s.warnmultifile)
			error("Image requires 4 color channels to paint: %s", s.warnmultifile);
		if(s.warnpackedfile)
			error("Packed MultiLayer files cannot be painted %s", s.warnpackedfile);

		persp(PERSP_WIN);
	}
}

void imagepaint_pick(short mousebutton)
{
	ToolSettings *settings= G.scene->toolsettings;
	Brush *brush= settings->imapaint.brush;

	if(brush && (settings->imapaint.tool == PAINT_TOOL_CLONE)) {
		if(brush->clone.image) {
			short prevmval[2], mval[2];
			float lastmousepos[2], mousepos[2];
		
			getmouseco_areawin(prevmval);

			while(get_mbut() & mousebutton) {
				getmouseco_areawin(mval);

				if((prevmval[0] != mval[0]) || (prevmval[1] != mval[1]) ) {
					/* mouse moved, so move the clone image */
					imapaint_compute_uvco(prevmval, lastmousepos);
					imapaint_compute_uvco(mval, mousepos);

					brush->clone.offset[0] += mousepos[0] - lastmousepos[0];
					brush->clone.offset[1] += mousepos[1] - lastmousepos[1];

					force_draw(0);

					prevmval[0]= mval[0];
					prevmval[1]= mval[1];
				}
			}
		}
	}
	else if(brush)
		sample_vpaint();
}

