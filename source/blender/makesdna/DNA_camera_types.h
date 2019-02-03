/*
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
 */

/** \file DNA_camera_types.h
 *  \ingroup DNA
 */

#ifndef __DNA_CAMERA_TYPES_H__
#define __DNA_CAMERA_TYPES_H__

#include "DNA_defs.h"
#include "DNA_gpu_types.h"
#include "DNA_movieclip_types.h"
#include "DNA_image_types.h"
#include "DNA_ID.h"

#ifdef __cplusplus
extern "C" {
#endif

struct AnimData;
struct Ipo;
struct Object;

/* ------------------------------------------- */
/* Stereo Settings */
typedef struct CameraStereoSettings {
	float interocular_distance;
	float convergence_distance;
	short convergence_mode;
	short pivot;
	short flag;
	short pad;
	/* Cut-off angle at which interocular distance start to fade down. */
	float pole_merge_angle_from;
	/* Cut-off angle at which interocular distance stops to fade down. */
	float pole_merge_angle_to;
} CameraStereoSettings;

/* Background Picture */
typedef struct CameraBGImage {
	struct CameraBGImage *next, *prev;

	struct Image *ima;
	struct ImageUser iuser;
	struct MovieClip *clip;
	struct MovieClipUser cuser;
	float offset[2], scale, rotation;
	float alpha;
	short flag;
	short source;
} CameraBGImage;

typedef struct Camera {
	ID id;
	/** Animation data (must be immediately after id for utilities to use it). */
	struct AnimData *adt;

	/** CAM_PERSP, CAM_ORTHO or CAM_PANO. */
	char type;
	/** Draw type extra. */
	char dtx;
	short flag;
	float passepartalpha;
	float clipsta, clipend;
	float lens, ortho_scale, drawsize;
	float sensor_x, sensor_y;
	float shiftx, shifty;

	/* yafray: dof params */
	/* qdn: yafray var 'YF_dofdist' now enabled for defocus composite node as well.
	 * The name was not changed so that no other files need to be modified */
	float YF_dofdist;

	/** Old animation system, deprecated for 2.5. */
	struct Ipo *ipo  DNA_DEPRECATED;

	struct Object *dof_ob;
	struct GPUDOFSettings gpu_dof;

	/* CameraBGImage reference images */
	struct ListBase bg_images;

	char sensor_fit;
	char pad[7];

	/* runtime only, used for drawing */
	float drwcorners[2][4][2];
	float drwtria[2][2];
	float drwdepth[2];
	float drwfocusmat[4][4];
	float drwnormalmat[4][4];

	/* Stereo settings */
	struct CameraStereoSettings stereo;
} Camera;

/* **************** CAMERA ********************* */

/* type */
enum {
	CAM_PERSP       = 0,
	CAM_ORTHO       = 1,
	CAM_PANO        = 2,
};

/* dtx */
enum {
	CAM_DTX_CENTER          = (1 << 0),
	CAM_DTX_CENTER_DIAG     = (1 << 1),
	CAM_DTX_THIRDS          = (1 << 2),
	CAM_DTX_GOLDEN          = (1 << 3),
	CAM_DTX_GOLDEN_TRI_A    = (1 << 4),
	CAM_DTX_GOLDEN_TRI_B    = (1 << 5),
	CAM_DTX_HARMONY_TRI_A   = (1 << 6),
	CAM_DTX_HARMONY_TRI_B   = (1 << 7),
};

/* flag */
enum {
	CAM_SHOWLIMITS          = (1 << 0),
	CAM_SHOWMIST            = (1 << 1),
	CAM_SHOWPASSEPARTOUT    = (1 << 2),
	CAM_SHOW_SAFE_MARGINS       = (1 << 3),
	CAM_SHOWNAME            = (1 << 4),
	CAM_ANGLETOGGLE         = (1 << 5),
	CAM_DS_EXPAND           = (1 << 6),
#ifdef DNA_DEPRECATED
	CAM_PANORAMA            = (1 << 7), /* deprecated */
#endif
	CAM_SHOWSENSOR          = (1 << 8),
	CAM_SHOW_SAFE_CENTER    = (1 << 9),
	CAM_SHOW_BG_IMAGE       = (1 << 10),
};

/* Sensor fit */
enum {
	CAMERA_SENSOR_FIT_AUTO  = 0,
	CAMERA_SENSOR_FIT_HOR   = 1,
	CAMERA_SENSOR_FIT_VERT  = 2,
};

#define DEFAULT_SENSOR_WIDTH	36.0f
#define DEFAULT_SENSOR_HEIGHT	24.0f

/* stereo->convergence_mode */
enum {
	CAM_S3D_OFFAXIS    = 0,
	CAM_S3D_PARALLEL   = 1,
	CAM_S3D_TOE        = 2,
};

/* stereo->pivot */
enum {
	CAM_S3D_PIVOT_LEFT      = 0,
	CAM_S3D_PIVOT_RIGHT     = 1,
	CAM_S3D_PIVOT_CENTER    = 2,
};

/* stereo->flag */
enum {
	CAM_S3D_SPHERICAL       = (1 << 0),
	CAM_S3D_POLE_MERGE      = (1 << 1),
};

/* CameraBGImage->flag */
/* may want to use 1 for select ? */
enum {
	CAM_BGIMG_FLAG_EXPANDED      = (1 << 1),
	CAM_BGIMG_FLAG_CAMERACLIP    = (1 << 2),
	CAM_BGIMG_FLAG_DISABLED      = (1 << 3),
	CAM_BGIMG_FLAG_FOREGROUND    = (1 << 4),

	/* Camera framing options */
	CAM_BGIMG_FLAG_CAMERA_ASPECT = (1 << 5),  /* don't stretch to fit the camera view  */
	CAM_BGIMG_FLAG_CAMERA_CROP   = (1 << 6),  /* crop out the image */

	/* Axis flip options */
	CAM_BGIMG_FLAG_FLIP_X        = (1 << 7),
	CAM_BGIMG_FLAG_FLIP_Y        = (1 << 8),
};

#define CAM_BGIMG_FLAG_EXPANDED (CAM_BGIMG_FLAG_EXPANDED | CAM_BGIMG_FLAG_CAMERACLIP)

/* CameraBGImage->source */
/* may want to use 1 for select ?*/
enum {
	CAM_BGIMG_SOURCE_IMAGE		= 0,
	CAM_BGIMG_SOURCE_MOVIE		= 1,
};

#ifdef __cplusplus
}
#endif

#endif
