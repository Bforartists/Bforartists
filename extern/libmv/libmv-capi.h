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
struct libmv_Features;
struct libmv_CameraIntrinsics;

/* Logging */
void libmv_initLogging(const char *argv0);
void libmv_startDebugLogging(void);
void libmv_setLoggingVerbosity(int verbosity);

/* RegionTracker */
struct libmv_RegionTracker *libmv_regionTrackerNew(int max_iterations, int pyramid_level, double tolerance);
int libmv_regionTrackerTrack(struct libmv_RegionTracker *libmv_tracker, const float *ima1, const float *ima2,
			int width, int height, int half_window_size,
			double  x1, double  y1, double *x2, double *y2);
void libmv_regionTrackerDestroy(struct libmv_RegionTracker *libmv_tracker);

/* SAD Tracker */
void libmv_SADSamplePattern(unsigned char *image, int stride,
			float warp[3][2], unsigned char *pattern);
float libmv_SADTrackerTrack(unsigned char *pattern, unsigned char *warped, unsigned char *image,
			int stride, int width, int height, float warp[3][2]);

/* Tracks */
struct libmv_Tracks *libmv_tracksNew(void);
void libmv_tracksInsert(struct libmv_Tracks *libmv_tracks, int image, int track, double x, double y);
void libmv_tracksDestroy(struct libmv_Tracks *libmv_tracks);

/* Reconstruction solver */
struct libmv_Reconstruction *libmv_solveReconstruction(struct libmv_Tracks *tracks, int keyframe1, int keyframe2,
			double focal_length, double principal_x, double principal_y, double k1, double k2, double k3);
int libmv_reporojectionPointForTrack(struct libmv_Reconstruction *libmv_reconstruction, int track, double pos[3]);
double libmv_reporojectionErrorForTrack(struct libmv_Reconstruction *libmv_reconstruction, int track);
int libmv_reporojectionCameraForImage(struct libmv_Reconstruction *libmv_reconstruction, int image, double mat[4][4]);
double libmv_reprojectionError(struct libmv_Reconstruction *libmv_reconstruction);
void libmv_destroyReconstruction(struct libmv_Reconstruction *libmv_reconstruction);

/* feature detector */
struct libmv_Features *libmv_detectFeatures(unsigned char *data, int width, int height, int stride,
			int margin, int count, int min_distance);
int libmv_countFeatures(struct libmv_Features *libmv_features);
void libmv_getFeature(struct libmv_Features *libmv_features, int number, double *x, double *y, double *score, double *size);
void libmv_destroyFeatures(struct libmv_Features *libmv_features);

/* camera intrinsics */
struct libmv_CameraIntrinsics *libmv_CameraIntrinsicsNew(double focal_length, double principal_x, double principal_y,
			double k1, double k2, double k3, int width, int height);

struct libmv_CameraIntrinsics *libmv_CameraIntrinsicsCopy(struct libmv_CameraIntrinsics *libmvIntrinsics);

void libmv_CameraIntrinsicsDestroy(struct libmv_CameraIntrinsics *libmvIntrinsics);

void libmv_CameraIntrinsicsUpdate(struct libmv_CameraIntrinsics *libmvIntrinsics, double focal_length,
			double principal_x, double principal_y, double k1, double k2, double k3, int width, int height);

void libmv_CameraIntrinsicsUndistortByte(struct libmv_CameraIntrinsics *libmvIntrinsics,
			unsigned char *src, unsigned char *dst, int width, int height, int channels);

void libmv_CameraIntrinsicsUndistortFloat(struct libmv_CameraIntrinsics *libmvIntrinsics,
			float *src, float *dst, int width, int height, int channels);

void libmv_CameraIntrinsicsDistortByte(struct libmv_CameraIntrinsics *libmvIntrinsics,
			unsigned char *src, unsigned char *dst, int width, int height, int channels);

void libmv_CameraIntrinsicsDistortFloat(struct libmv_CameraIntrinsics *libmvIntrinsics,
			float *src, float *dst, int width, int height, int channels);

/* dsitortion */
void libmv_undistortByte(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			unsigned char *src, unsigned char *dst, int width, int height, int channels);
void libmv_undistortFloat(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			float *src, float *dst, int width, int height, int channels);

void libmv_distortByte(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			unsigned char *src, unsigned char *dst, int width, int height, int channels);
void libmv_distortFloat(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			float *src, float *dst, int width, int height, int channels);

/* utils */
void libmv_applyCameraIntrinsics(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			double x, double y, double *x1, double *y1);
void libmv_InvertIntrinsics(double focal_length, double principal_x, double principal_y, double k1, double k2, double k3,
			double x, double y, double *x1, double *y1);

#ifdef __cplusplus
}
#endif

#endif // LIBMV_C_API_H
