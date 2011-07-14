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
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef DNA_TRACKING_TYPES_H
#define DNA_TRACKING_TYPES_H

/** \file DNA_tracking_types.h
 *  \ingroup DNA
 *  \since may-2011
 *  \author Sergey Sharybin
 */

#include "DNA_listBase.h"

/* match-moving data */

struct MovieReconstructedCamera;
struct MovieTrackingCamera;
struct MovieTrackingBundle;
struct MovieTrackingMarker;
struct MovieTrackingTrack;
struct MovieTracking;

typedef struct MovieReconstructedCamera {
	int framenr, pad;
	float mat[4][4];
} MovieReconstructedCamera;

typedef struct MovieTrackingCamera {
	float sensor_width;	/* width of CCD sensor */
	float focal;		/* focal length */
	short units;		/* units of focal length user is working with */
	short pad;
	float principal[2];	/* principal point */
	float k1, k2, k3;	/* radial distortion */
	int last_camera;	/* most recently used camera */
	int reconnr;		/* number of reconstructed cameras */
	struct MovieReconstructedCamera *reconstructed;	/* reconstructed cameras */
} MovieTrackingCamera;

typedef struct MovieTrackingMarker {
	float pos[2];	/* 2d position of marker on frame (in unified 0..1 space) */
	int framenr;	/* number of frame marker is associated with */
	int flag;		/* Marker's flag (alive, ...) */
} MovieTrackingMarker;

typedef struct MovieTrackingTrack {
	struct MovieTrackingTrack *next, *prev;

	char name[24];

	/* ** setings ** */
	float pat_min[2], pat_max[2];		/* positions of left-bottom and right-top corners of pattern (in unified 0..1 space) */
	float search_min[2], search_max[2];	/* positions of left-bottom and right-top corners of search area (in unified 0..1 space) */

	int pad;

	/* ** track ** */
	int markersnr;					/* count of markers in track */
	int last_marker;				/* most recently used marker */
	int pad2;
	MovieTrackingMarker *markers;	/* markers in track */

	/* ** bundle ** */
	float bundle_pos[3];

	/* ** UI editing ** */
	int flag, pat_flag, search_flag;	/* flags (selection, ...) */
} MovieTrackingTrack;

typedef struct MovieTrackingSettings {
	int flag;		/* different flags (frames nr limit..) */
	short speed;	/* speed of tracking */
	short frames_limit;	/* number of frames to be tarcked during single tracking session (if TRACKING_FRAMES_LIMIT is set) */
	int keyframe1, keyframe2;	/* two keyframes for reconstrution initialization */
	float dist;		/* distance between two bundles used for scene scaling */
	float pad;
} MovieTrackingSettings;

typedef struct MovieTracking {
	MovieTrackingSettings settings;
	MovieTrackingCamera camera;
	ListBase tracks;
} MovieTracking;

/* MovieTrackingCamera->units */
enum {
	CAMERA_UNITS_PX = 0,
	CAMERA_UNITS_MM
};

/* MovieTrackingMarker->flag */
#define MARKER_DISABLED	1

/* MovieTrackingTrack->flag */
#define TRACK_HAS_BUNDLE	(1<<1)
#define TRACK_DISABLE_RED	(1<<2)
#define TRACK_DISABLE_GREEN	(1<<3)
#define TRACK_DISABLE_BLUE	(1<<4)
#define TRACK_HIDDEN		(1<<5)

/* MovieTrackingSettings->speed */
#define TRACKING_SPEED_FASTEST		0
#define TRACKING_SPEED_REALTIME		1
#define TRACKING_SPEED_HALF			2
#define TRACKING_SPEED_QUARTER		4

/* MovieTrackingSettings->flag */
#define TRACKING_FRAMES_LIMIT		1

#endif
