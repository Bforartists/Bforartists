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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef LIBMV_C_API_H
#define LIBMV_C_API_H

#ifdef __cplusplus
extern "C" {
#endif

struct libmv_RegionTracker;
struct libmv_Tracks;
struct libmv_Reconstruction;
struct libmv_Corners;

/* Logging */
void libmv_initLogging(const char *argv0);
void libmv_startDebugLogging(void);
void libmv_setLoggingVerbosity(int verbosity);

/* RegionTracker */
struct libmv_RegionTracker *libmv_regionTrackerNew(int max_iterations, int pyramid_level, double tolerance);
int libmv_regionTrackerTrack(struct libmv_RegionTracker *tracker, const float *ima1, const float *ima2,
			int width, int height, int half_window_size,
			double  x1, double  y1, double *x2, double *y2);
void libmv_regionTrackerDestroy(struct libmv_RegionTracker *tracker);

/* Tracks */
struct libmv_Tracks *libmv_tracksNew(void);
void libmv_tracksInsert(struct libmv_Tracks *tracks, int image, int track, double x, double y);
void libmv_tracksDestroy(struct libmv_Tracks *tracks);

/* Reconstruction solver */
struct libmv_Reconstruction *libmv_solveReconstruction(struct libmv_Tracks *tracks, int keyframe1, int keyframe2,
			double focal_length, double principal_x, double principal_y, double k1, double k2, double k3);
int libmv_reporojectionPointForTrack(struct libmv_Reconstruction *reconstruction, int track, double pos[3]);
int libmv_reporojectionCameraForImage(struct libmv_Reconstruction *reconstruction, int image, double mat[4][4]);
void libmv_destroyReconstruction(struct libmv_Reconstruction *reconstruction);

/* feature detector */

struct libmv_Corners *libmv_detectCorners(unsigned char *data, int width, int height, int stride);
int libmv_countCorners(struct libmv_Corners *corners);
void libmv_getCorner(struct libmv_Corners *corners, int number, float *x, float *y, float *score, float *size);
void libmv_destroyCorners(struct libmv_Corners *corners);

/* utils */
void libmv_applyCameraIntrinsics(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			double x, double y, double *x1, double *y1);
void libmv_InvertIntrinsics(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			double x, double y, double *x1, double *y1);

#ifdef __cplusplus
}
#endif

#endif // LIBMV_C_API_H
