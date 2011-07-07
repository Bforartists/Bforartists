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
#ifndef DNA_VIEW3D_TYPES_H
#define DNA_VIEW3D_TYPES_H

/** \file DNA_view3d_types.h
 *  \ingroup DNA
 */

struct ViewDepths;
struct Object;
struct Image;
struct Tex;
struct SpaceLink;
struct Base;
struct BoundBox;
struct MovieClip;
struct MovieClipUser;
struct RenderInfo;
struct bGPdata;
struct SmoothViewStore;
struct wmTimer;

/* This is needed to not let VC choke on near and far... old
 * proprietary MS extensions... */
#ifdef WIN32
#undef near
#undef far
#define near clipsta
#define far clipend
#endif

#include "DNA_listBase.h"
#include "DNA_image_types.h"
#include "DNA_movieclip_types.h"

/* ******************************** */

/* The near/far thing is a Win EXCEPTION. Thus, leave near/far in the
 * code, and patch for windows. */
 
/* Background Picture in 3D-View */
typedef struct BGpic {
	struct BGpic *next, *prev;

	struct Image *ima;
	struct ImageUser iuser;
	struct MovieClip *clip;
	struct MovieClipUser cuser;
	float xof, yof, size, blend;
	short view;
	short flag;
	short source, pad;
} BGpic;

/* ********************************* */

typedef struct RegionView3D {
	
	float winmat[4][4];			/* GL_PROJECTION matrix */
	float viewmat[4][4];		/* GL_MODELVIEW matrix */
	float viewinv[4][4];		/* inverse of viewmat */
	float persmat[4][4];		/* viewmat*winmat */
	float persinv[4][4];		/* inverse of persmat */

	/* viewmat/persmat multiplied with object matrix, while drawing and selection */
	float viewmatob[4][4];
	float persmatob[4][4];

	/* transform widget matrix */
	float twmat[4][4];

	float viewquat[4];			/* view rotation, must be kept normalized */
	float dist;					/* distance from 'ofs' along -viewinv[2] vector, where result is negative as is 'ofs' */
	float zfac;					/* initgrabz() result */
	float camdx, camdy;			/* camera view offsets, 1.0 = viewplane moves entire width/height */
	float pixsize;				/* runtime only */
	float ofs[3];				/* view center & orbit pivot, negative of worldspace location,
								 * also matches -viewinv[3][0:3] in ortho mode.*/
	short camzoom;				/* viewport zoom on the camera frame, see BKE_screen_view3d_zoom_to_fac */
	short twdrawflag;
	char is_persp;				/* check if persp/ortho view, since 'persp' cant be used for this since
								 * it can have cameras assigned as well. (only set in setwinmatrixview3d) */
	char pad[3];
	
	short rflag, viewlock;
	short persp;
	short view;
	
	/* user defined clipping planes */
	float clip[6][4];
	float clip_local[6][4]; /* clip in object space, means we can test for clipping in editmode without first going into worldspace */
	struct BoundBox *clipbb;	
	
	struct bGPdata *gpd;		/* Grease-Pencil Data (annotation layers) */
	
	struct RegionView3D *localvd; /* allocated backup of its self while in localview */
	struct RenderInfo *ri;
	struct ViewDepths *depths;
	
	/* animated smooth view */
	struct SmoothViewStore *sms;
	struct wmTimer *smooth_timer;
	
	/* last view */
	float lviewquat[4];
	short lpersp, lview; /* lpersp can never be set to 'RV3D_CAMOB' */
	float gridview;
	
	float twangle[3];

	float padf;

} RegionView3D;

/* 3D ViewPort Struct */
typedef struct View3D {
	struct SpaceLink *next, *prev;
	ListBase regionbase;		/* storage of regions for inactive spaces */
	int spacetype;
	float blockscale;
	short blockhandler[8];
	
	float viewquat[4], dist;	/* XXX depricated */
	float bundle_size;			/* size of bundles in reconstructed data */
	
	unsigned int lay_used; /* used while drawing */
	
	short persp;	/* XXX depricated */
	short view;	/* XXX depricated */
	
	struct Object *camera, *ob_centre;

	struct ListBase bgpicbase;
	struct BGpic *bgpic; /* deprecated, use bgpicbase, only kept for do_versions(...) */

	struct View3D *localvd; /* allocated backup of its self while in localview */
	
	char ob_centre_bone[32];		/* optional string for armature bone to define center */
	
	unsigned int lay;
	int layact;
	
	/**
	 * The drawing mode for the 3d display. Set to OB_WIRE, OB_SOLID,
	 * OB_SHADED or OB_TEXTURE */
	short drawtype;
	short ob_centre_cursor;		/* optional bool for 3d cursor to define center */
	short scenelock, around;
	short flag, flag2;
	
	float lens, grid;
	float near, far;
	float ofs[3];			/* XXX deprecated */
	float cursor[3];

	short modeselect;
	short gridlines;
	short gridsubdiv;	/* Number of subdivisions in the grid between each highlighted grid line */
	char gridflag;

	/* transform widget info */
	char twtype, twmode, twflag, pad2[2];
	
	/* afterdraw, for xray & transparent */
	struct ListBase afterdraw_transp;
	struct ListBase afterdraw_xray;
	struct ListBase afterdraw_xraytransp;
	
	/* drawflags, denoting state */
	short zbuf, transp, xray;

	char ndofmode;			/* mode of transform for 6DOF devices -1 not found, 0 normal, 1 fly, 2 ob transform */
	char ndoffilter;		/* filter for 6DOF devices 0 normal, 1 dominant */
	
	void *properties_storage;	/* Nkey panel stores stuff here (runtime only!) */
	
	/* XXX depricated? */
	struct bGPdata *gpd;		/* Grease-Pencil Data (annotation layers) */

} View3D;


/* View3D->flag (short) */
/*#define V3D_DISPIMAGE		1*/ /*UNUSED*/
#define V3D_DISPBGPICS		2
#define V3D_HIDE_HELPLINES	4
#define V3D_INVALID_BACKBUF	8

#define V3D_ALIGN			1024
#define V3D_SELECT_OUTLINE	2048
#define V3D_ZBUF_SELECT		4096
#define V3D_GLOBAL_STATS	8192
#define V3D_DRAW_CENTERS	32768

/* RegionView3d->persp */
#define RV3D_ORTHO				0
#define RV3D_PERSP				1
#define RV3D_CAMOB				2

/* RegionView3d->rflag */
#define RV3D_CLIPPING				4
#define RV3D_NAVIGATING				8
#define RV3D_GPULIGHT_UPDATE		16

/* RegionView3d->viewlock */
#define RV3D_LOCKED			1
#define RV3D_BOXVIEW		2
#define RV3D_BOXCLIP		4

/* RegionView3d->view */
#define RV3D_VIEW_USER			 0
#define RV3D_VIEW_FRONT			 1
#define RV3D_VIEW_BACK			 2
#define RV3D_VIEW_LEFT			 3
#define RV3D_VIEW_RIGHT			 4
#define RV3D_VIEW_TOP			 5
#define RV3D_VIEW_BOTTOM		 6
#define RV3D_VIEW_PERSPORTHO	 7
#define RV3D_VIEW_CAMERA		 8

/* View3d->flag2 (short) */
#define V3D_RENDER_OVERRIDE		4
#define V3D_SOLID_TEX			8
#define V3D_DISPGP				16
#define V3D_LOCK_CAMERA			32
#define V3D_SHOW_RECONSTRUCTION	64
#define V3D_SHOW_CAMERAPATH		128

/* View3D->around */
#define V3D_CENTER		 0
#define V3D_CENTROID	 3
#define V3D_CURSOR		 1
#define V3D_LOCAL		 2
#define V3D_ACTIVE		 4

/*View3D types (only used in tools, not actually saved)*/
#define V3D_VIEW_STEPLEFT		 1
#define V3D_VIEW_STEPRIGHT		 2
#define V3D_VIEW_STEPDOWN		 3
#define V3D_VIEW_STEPUP		 4
#define V3D_VIEW_PANLEFT		 5
#define V3D_VIEW_PANRIGHT		 6
#define V3D_VIEW_PANDOWN		 7
#define V3D_VIEW_PANUP			 8

/* View3d->gridflag */
#define V3D_SHOW_FLOOR			1
#define V3D_SHOW_X				2
#define V3D_SHOW_Y				4
#define V3D_SHOW_Z				8

/* View3d->twtype (bits, we can combine them) */
#define V3D_MANIP_TRANSLATE		1
#define V3D_MANIP_ROTATE		2
#define V3D_MANIP_SCALE			4

/* View3d->twmode */
#define V3D_MANIP_GLOBAL		0
#define V3D_MANIP_LOCAL			1
#define V3D_MANIP_NORMAL		2
#define V3D_MANIP_VIEW			3
#define V3D_MANIP_GIMBAL		4
#define V3D_MANIP_CUSTOM		5 /* anything of value 5 or higher is custom */

/* View3d->twflag */
   /* USE = user setting, DRAW = based on selection */
#define V3D_USE_MANIPULATOR		1
#define V3D_DRAW_MANIPULATOR	2
/* #define V3D_CALC_MANIPULATOR	4 */ /*UNUSED*/

/* BGPic->flag */
/* may want to use 1 for select ?*/
#define V3D_BGPIC_EXPANDED		2

/* BGPic->source */
/* may want to use 1 for select ?*/
#define V3D_BGPIC_IMAGE		0
#define V3D_BGPIC_MOVIE		1

#define RV3D_CAMZOOM_MIN -30
#define RV3D_CAMZOOM_MAX 600

#endif


