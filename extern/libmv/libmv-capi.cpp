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
 * The Original Code is Copyright (C) 2011 Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/* define this to generate PNG images with content of search areas
   tracking between which failed */
#undef DUMP_FAILURE

/* define this to generate PNG images with content of search areas
   on every itteration of tracking */
#undef DUMP_ALWAYS

#include "libmv-capi.h"

#include "libmv/logging/logging.h"

#include "libmv/tracking/track_region.h"

#include "libmv/simple_pipeline/callbacks.h"
#include "libmv/simple_pipeline/tracks.h"
#include "libmv/simple_pipeline/initialize_reconstruction.h"
#include "libmv/simple_pipeline/bundle.h"
#include "libmv/simple_pipeline/detect.h"
#include "libmv/simple_pipeline/pipeline.h"
#include "libmv/simple_pipeline/camera_intrinsics.h"
#include "libmv/simple_pipeline/modal_solver.h"
#include "libmv/simple_pipeline/reconstruction_scale.h"

#include <stdlib.h>
#include <assert.h>

#if defined(DUMP_FAILURE) || defined (DUMP_ALWAYS)
#  include <png.h>
#endif

#ifdef _MSC_VER
#  define snprintf _snprintf
#endif

typedef struct libmv_Reconstruction {
	libmv::EuclideanReconstruction reconstruction;

	/* used for per-track average error calculation after reconstruction */
	libmv::Tracks tracks;
	libmv::CameraIntrinsics intrinsics;

	double error;
} libmv_Reconstruction;

typedef struct libmv_Features {
	int count, margin;
	libmv::Feature *features;
} libmv_Features;

/* ************ Logging ************ */

void libmv_initLogging(const char *argv0)
{
	/* Make it so FATAL messages are always print into console */
	char severity_fatal[32];
	snprintf(severity_fatal, sizeof(severity_fatal), "%d",
	         google::GLOG_FATAL);

	google::InitGoogleLogging(argv0);
	google::SetCommandLineOption("logtostderr", "1");
	google::SetCommandLineOption("v", "0");
	google::SetCommandLineOption("stderrthreshold", severity_fatal);
	google::SetCommandLineOption("minloglevel", severity_fatal);
}

void libmv_startDebugLogging(void)
{
	google::SetCommandLineOption("logtostderr", "1");
	google::SetCommandLineOption("v", "2");
	google::SetCommandLineOption("stderrthreshold", "1");
	google::SetCommandLineOption("minloglevel", "0");
}

void libmv_setLoggingVerbosity(int verbosity)
{
	char val[10];
	snprintf(val, sizeof(val), "%d", verbosity);

	google::SetCommandLineOption("v", val);
}

/* ************ Utility ************ */

static void floatBufToImage(const float *buf, int width, int height, int channels, libmv::FloatImage *image)
{
	int x, y, k, a = 0;

	image->Resize(height, width, channels);

	for (y = 0; y < height; y++) {
		for (x = 0; x < width; x++) {
			for (k = 0; k < channels; k++) {
				(*image)(y, x, k) = buf[a++];
			}
		}
	}
}

static void imageToFloatBuf(const libmv::FloatImage *image, int channels, float *buf)
{
	int x, y, k, a = 0;

	for (y = 0; y < image->Height(); y++) {
		for (x = 0; x < image->Width(); x++) {
			for (k = 0; k < channels; k++) {
				buf[a++] = (*image)(y, x, k);
			}
		}
	}
}

#if defined(DUMP_FAILURE) || defined (DUMP_ALWAYS)
static void savePNGImage(png_bytep *row_pointers, int width, int height, int depth, int color_type, char *file_name)
{
	png_infop info_ptr;
	png_structp png_ptr;
	FILE *fp = fopen(file_name, "wb");

	if (!fp)
		return;

	/* Initialize stuff */
	png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
	info_ptr = png_create_info_struct(png_ptr);

	if (setjmp(png_jmpbuf(png_ptr))) {
		fclose(fp);
		return;
	}

	png_init_io(png_ptr, fp);

	/* write header */
	if (setjmp(png_jmpbuf(png_ptr))) {
		fclose(fp);
		return;
	}

	png_set_IHDR(png_ptr, info_ptr, width, height,
		depth, color_type, PNG_INTERLACE_NONE,
		PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);

	png_write_info(png_ptr, info_ptr);

	/* write bytes */
	if (setjmp(png_jmpbuf(png_ptr))) {
		fclose(fp);
		return;
	}

	png_write_image(png_ptr, row_pointers);

	/* end write */
	if (setjmp(png_jmpbuf(png_ptr))) {
		fclose(fp);
		return;
	}

	png_write_end(png_ptr, NULL);

	fclose(fp);
}

static void saveImage(const char *prefix, libmv::FloatImage image, int x0, int y0)
{
	int x, y;
	png_bytep *row_pointers;

	row_pointers= (png_bytep*)malloc(sizeof(png_bytep)*image.Height());

	for (y = 0; y < image.Height(); y++) {
		row_pointers[y]= (png_bytep)malloc(sizeof(png_byte)*4*image.Width());

		for (x = 0; x < image.Width(); x++) {
			if (x0 == x && image.Height() - y0 - 1 == y) {
				row_pointers[y][x*4+0]= 255;
				row_pointers[y][x*4+1]= 0;
				row_pointers[y][x*4+2]= 0;
				row_pointers[y][x*4+3]= 255;
			}
			else {
				float pixel = image(image.Height() - y - 1, x, 0);
				row_pointers[y][x*4+0]= pixel*255;
				row_pointers[y][x*4+1]= pixel*255;
				row_pointers[y][x*4+2]= pixel*255;
				row_pointers[y][x*4+3]= 255;
			}
		}
	}

	{
		static int a= 0;
		char buf[128];
		snprintf(buf, sizeof(buf), "%s_%02d.png", prefix, ++a);
		savePNGImage(row_pointers, image.Width(), image.Height(), 8, PNG_COLOR_TYPE_RGBA, buf);
	}

	for (y = 0; y < image.Height(); y++) {
		free(row_pointers[y]);
	}
	free(row_pointers);
}

static void saveBytesImage(const char *prefix, unsigned char *data, int width, int height)
{
	int x, y;
	png_bytep *row_pointers;

	row_pointers= (png_bytep*)malloc(sizeof(png_bytep)*height);

	for (y = 0; y < height; y++) {
		row_pointers[y]= (png_bytep)malloc(sizeof(png_byte)*4*width);

		for (x = 0; x < width; x++) {
			char pixel = data[width*y+x];
			row_pointers[y][x*4+0]= pixel;
			row_pointers[y][x*4+1]= pixel;
			row_pointers[y][x*4+2]= pixel;
			row_pointers[y][x*4+3]= 255;
		}
	}

	{
		static int a = 0;
		char buf[128];
		snprintf(buf, sizeof(buf), "%s_%02d.png", prefix, ++a);
		savePNGImage(row_pointers, width, height, 8, PNG_COLOR_TYPE_RGBA, buf);
	}

	for (y = 0; y < height; y++) {
		free(row_pointers[y]);
	}
	free(row_pointers);
}
#endif

/* ************ Planar tracker ************ */

/* TrackRegion (new planar tracker) */
int libmv_trackRegion(const struct libmv_trackRegionOptions *options,
                      const float *image1, int image1_width, int image1_height,
                      const float *image2, int image2_width, int image2_height,
                      const double *x1, const double *y1,
                      struct libmv_trackRegionResult *result,
                      double *x2, double *y2)
{
	double xx1[5], yy1[5];
	double xx2[5], yy2[5];
	bool tracking_result = false;

	/* Convert to doubles for the libmv api. The four corners and the center. */
	for (int i = 0; i < 5; ++i) {
		xx1[i] = x1[i];
		yy1[i] = y1[i];
		xx2[i] = x2[i];
		yy2[i] = y2[i];
	}

	libmv::TrackRegionOptions track_region_options;
	libmv::FloatImage image1_mask;

	switch (options->motion_model) {
#define LIBMV_CONVERT(the_model) \
    case libmv::TrackRegionOptions::the_model: \
		track_region_options.mode = libmv::TrackRegionOptions::the_model; \
		break;
		LIBMV_CONVERT(TRANSLATION)
		LIBMV_CONVERT(TRANSLATION_ROTATION)
		LIBMV_CONVERT(TRANSLATION_SCALE)
		LIBMV_CONVERT(TRANSLATION_ROTATION_SCALE)
		LIBMV_CONVERT(AFFINE)
		LIBMV_CONVERT(HOMOGRAPHY)
#undef LIBMV_CONVERT
	}

	track_region_options.minimum_correlation = options->minimum_correlation;
	track_region_options.max_iterations = options->num_iterations;
	track_region_options.sigma = options->sigma;
	track_region_options.num_extra_points = 1;
	track_region_options.image1_mask = NULL;
	track_region_options.use_brute_initialization = options->use_brute;
	track_region_options.use_normalized_intensities = options->use_normalization;

	if (options->image1_mask) {
		floatBufToImage(options->image1_mask, image1_width, image1_height, 1, &image1_mask);

		track_region_options.image1_mask = &image1_mask;
	}

	/* Convert from raw float buffers to libmv's FloatImage. */
	libmv::FloatImage old_patch, new_patch;
	floatBufToImage(image1, image1_width, image1_height, 1, &old_patch);
	floatBufToImage(image2, image2_width, image2_height, 1, &new_patch);

	libmv::TrackRegionResult track_region_result;
	libmv::TrackRegion(old_patch, new_patch, xx1, yy1, track_region_options, xx2, yy2, &track_region_result);

	/* Convert to floats for the blender api. */
	for (int i = 0; i < 5; ++i) {
		x2[i] = xx2[i];
		y2[i] = yy2[i];
	}

	/* TODO(keir): Update the termination string with failure details. */
	if (track_region_result.termination == libmv::TrackRegionResult::PARAMETER_TOLERANCE ||
	    track_region_result.termination == libmv::TrackRegionResult::FUNCTION_TOLERANCE  ||
	    track_region_result.termination == libmv::TrackRegionResult::GRADIENT_TOLERANCE  ||
	    track_region_result.termination == libmv::TrackRegionResult::NO_CONVERGENCE)
	{
		tracking_result = true;
	}

#if defined(DUMP_FAILURE) || defined(DUMP_ALWAYS)
#if defined(DUMP_ALWAYS)
	{
#else
	if (!tracking_result) {
#endif
		saveImage("old_patch", old_patch, x1[4], y1[4]);
		saveImage("new_patch", new_patch, x2[4], y2[4]);

		if (options->image1_mask)
			saveImage("mask", image1_mask, x2[4], y2[4]);
	}
#endif

	return tracking_result;
}

void libmv_samplePlanarPatch(const float *image, int width, int height,
                             int channels, const double *xs, const double *ys,
                             int num_samples_x, int num_samples_y,
                             const float *mask, float *patch,
                             double *warped_position_x, double *warped_position_y)
{
	libmv::FloatImage libmv_image, libmv_patch, libmv_mask;
	libmv::FloatImage *libmv_mask_for_sample = NULL;

	floatBufToImage(image, width, height, channels, &libmv_image);

	if (mask) {
		floatBufToImage(mask, width, height, 1, &libmv_mask);

		libmv_mask_for_sample = &libmv_mask;
	}

	libmv::SamplePlanarPatch(libmv_image, xs, ys, num_samples_x, num_samples_y,
	                         libmv_mask_for_sample, &libmv_patch,
	                         warped_position_x, warped_position_y);

	imageToFloatBuf(&libmv_patch, channels, patch);
}

/* ************ Tracks ************ */

libmv_Tracks *libmv_tracksNew(void)
{
	libmv::Tracks *libmv_tracks = new libmv::Tracks();

	return (libmv_Tracks *)libmv_tracks;
}

void libmv_tracksInsert(struct libmv_Tracks *libmv_tracks, int image, int track, double x, double y)
{
	((libmv::Tracks*)libmv_tracks)->Insert(image, track, x, y);
}

void libmv_tracksDestroy(libmv_Tracks *libmv_tracks)
{
	delete (libmv::Tracks*)libmv_tracks;
}

/* ************ Reconstruction solver ************ */

class ReconstructUpdateCallback : public libmv::ProgressUpdateCallback {
public:
	ReconstructUpdateCallback(reconstruct_progress_update_cb progress_update_callback,
			void *callback_customdata)
	{
		progress_update_callback_ = progress_update_callback;
		callback_customdata_ = callback_customdata;
	}

	void invoke(double progress, const char *message)
	{
		if(progress_update_callback_) {
			progress_update_callback_(callback_customdata_, progress, message);
		}
	}
protected:
	reconstruct_progress_update_cb progress_update_callback_;
	void *callback_customdata_;
};

static void libmv_solveRefineIntrinsics(libmv::Tracks *tracks, libmv::CameraIntrinsics *intrinsics,
			libmv::EuclideanReconstruction *reconstruction, int refine_intrinsics,
			reconstruct_progress_update_cb progress_update_callback, void *callback_customdata,
			int bundle_constraints = libmv::BUNDLE_NO_CONSTRAINTS)
{
	/* only a few combinations are supported but trust the caller */
	int libmv_refine_flags = 0;

	if (refine_intrinsics & LIBMV_REFINE_FOCAL_LENGTH) {
		libmv_refine_flags |= libmv::BUNDLE_FOCAL_LENGTH;
	}
	if (refine_intrinsics & LIBMV_REFINE_PRINCIPAL_POINT) {
		libmv_refine_flags |= libmv::BUNDLE_PRINCIPAL_POINT;
	}
	if (refine_intrinsics & LIBMV_REFINE_RADIAL_DISTORTION_K1) {
		libmv_refine_flags |= libmv::BUNDLE_RADIAL_K1;
	}
	if (refine_intrinsics & LIBMV_REFINE_RADIAL_DISTORTION_K2) {
		libmv_refine_flags |= libmv::BUNDLE_RADIAL_K2;
	}

	progress_update_callback(callback_customdata, 1.0, "Refining solution");

	libmv::EuclideanBundleCommonIntrinsics(*(libmv::Tracks *)tracks, libmv_refine_flags,
		reconstruction, intrinsics, bundle_constraints);
}

static void cameraIntrinsicsFromOptions(libmv::CameraIntrinsics *camera_intrinsics,
                                        libmv_cameraIntrinsicsOptions *camera_intrinsics_options)
{
	camera_intrinsics->SetFocalLength(camera_intrinsics_options->focal_length,
	                                  camera_intrinsics_options->focal_length);

	camera_intrinsics->SetPrincipalPoint(camera_intrinsics_options->principal_point_x,
	                                     camera_intrinsics_options->principal_point_y);

	camera_intrinsics->SetRadialDistortion(camera_intrinsics_options->k1,
	                                       camera_intrinsics_options->k2,
	                                       camera_intrinsics_options->k3);

	camera_intrinsics->SetImageSize(camera_intrinsics_options->image_width,
	                                camera_intrinsics_options->image_height);
}

static libmv::Tracks getNormalizedTracks(libmv::Tracks *tracks, libmv::CameraIntrinsics *camera_intrinsics)
{
	libmv::vector<libmv::Marker> markers = tracks->AllMarkers();

	for (int i = 0; i < markers.size(); ++i) {
		camera_intrinsics->InvertIntrinsics(markers[i].x, markers[i].y,
			&(markers[i].x), &(markers[i].y));
	}

	return libmv::Tracks(markers);
}

static void finishReconstruction(libmv::Tracks *tracks, libmv::CameraIntrinsics *camera_intrinsics,
                                 libmv_Reconstruction *libmv_reconstruction,
                                 reconstruct_progress_update_cb progress_update_callback,
                                 void *callback_customdata)
{
	libmv::EuclideanReconstruction *reconstruction = &libmv_reconstruction->reconstruction;

	/* reprojection error calculation */
	progress_update_callback(callback_customdata, 1.0, "Finishing solution");
	libmv_reconstruction->tracks = *tracks;
	libmv_reconstruction->error = libmv::EuclideanReprojectionError(*tracks, *reconstruction, *camera_intrinsics);
}

libmv_Reconstruction *libmv_solveReconstruction(libmv_Tracks *libmv_tracks,
			libmv_cameraIntrinsicsOptions *libmv_camera_intrinsics_options,
			libmv_reconstructionOptions *libmv_reconstruction_options,
			reconstruct_progress_update_cb progress_update_callback,
			void *callback_customdata)
{
	libmv_Reconstruction *libmv_reconstruction = new libmv_Reconstruction();

	libmv::Tracks *tracks = ((libmv::Tracks *) libmv_tracks);
	libmv::EuclideanReconstruction *reconstruction = &libmv_reconstruction->reconstruction;
	libmv::CameraIntrinsics *camera_intrinsics = &libmv_reconstruction->intrinsics;

	ReconstructUpdateCallback update_callback =
		ReconstructUpdateCallback(progress_update_callback, callback_customdata);

	cameraIntrinsicsFromOptions(camera_intrinsics, libmv_camera_intrinsics_options);

	/* Invert the camera intrinsics */
	libmv::Tracks normalized_tracks = getNormalizedTracks(tracks, camera_intrinsics);

	/* actual reconstruction */
	libmv::ReconstructionOptions reconstruction_options;
	reconstruction_options.success_threshold = libmv_reconstruction_options->success_threshold;
	reconstruction_options.use_fallback_reconstruction = libmv_reconstruction_options->use_fallback_reconstruction;

	int keyframe1 = libmv_reconstruction_options->keyframe1,
	    keyframe2 = libmv_reconstruction_options->keyframe2;

	LG << "frames to init from: " << keyframe1 << " " << keyframe2;

	libmv::vector<libmv::Marker> keyframe_markers =
		normalized_tracks.MarkersForTracksInBothImages(keyframe1, keyframe2);

	LG << "number of markers for init: " << keyframe_markers.size();

	update_callback.invoke(0, "Initial reconstruction");

	libmv::EuclideanReconstructTwoFrames(keyframe_markers, reconstruction);
	libmv::EuclideanBundle(normalized_tracks, reconstruction);
	libmv::EuclideanCompleteReconstruction(reconstruction_options, normalized_tracks,
	                                       reconstruction, &update_callback);

	/* refinement */
	if (libmv_reconstruction_options->refine_intrinsics) {
		libmv_solveRefineIntrinsics((libmv::Tracks *)tracks, camera_intrinsics, reconstruction,
			libmv_reconstruction_options->refine_intrinsics,
			progress_update_callback, callback_customdata);
	}

	/* set reconstruction scale to unity */
	libmv::EuclideanScaleToUnity(reconstruction);

	/* finish reconstruction */
	finishReconstruction(tracks, camera_intrinsics, libmv_reconstruction,
	                     progress_update_callback, callback_customdata);

	return (libmv_Reconstruction *)libmv_reconstruction;
}

struct libmv_Reconstruction *libmv_solveModal(struct libmv_Tracks *libmv_tracks,
			libmv_cameraIntrinsicsOptions *libmv_camera_intrinsics_options,
			libmv_reconstructionOptions *libmv_reconstruction_options,
			reconstruct_progress_update_cb progress_update_callback,
			void *callback_customdata)
{
	libmv_Reconstruction *libmv_reconstruction = new libmv_Reconstruction();

	libmv::Tracks *tracks = ((libmv::Tracks *) libmv_tracks);
	libmv::EuclideanReconstruction *reconstruction = &libmv_reconstruction->reconstruction;
	libmv::CameraIntrinsics *camera_intrinsics = &libmv_reconstruction->intrinsics;

	ReconstructUpdateCallback update_callback =
		ReconstructUpdateCallback(progress_update_callback, callback_customdata);

	cameraIntrinsicsFromOptions(camera_intrinsics, libmv_camera_intrinsics_options);

	/* Invert the camera intrinsics. */
	libmv::Tracks normalized_tracks = getNormalizedTracks(tracks, camera_intrinsics);

	/* Actual reconstruction. */
	libmv::ModalSolver(normalized_tracks, reconstruction, &update_callback);

	libmv::CameraIntrinsics empty_intrinsics;
	libmv::EuclideanBundleCommonIntrinsics(normalized_tracks,
	                                       libmv::BUNDLE_NO_INTRINSICS,
	                                       reconstruction,
	                                       &empty_intrinsics,
	                                       libmv::BUNDLE_NO_TRANSLATION);

	/* Refinement. */
	if (libmv_reconstruction_options->refine_intrinsics) {
		libmv_solveRefineIntrinsics((libmv::Tracks *)tracks, camera_intrinsics, reconstruction,
			libmv_reconstruction_options->refine_intrinsics,
			progress_update_callback, callback_customdata,
			libmv::BUNDLE_NO_TRANSLATION);
	}

	/* Finish reconstruction. */
	finishReconstruction(tracks, camera_intrinsics, libmv_reconstruction,
	                     progress_update_callback, callback_customdata);

	return (libmv_Reconstruction *)libmv_reconstruction;
}

int libmv_reporojectionPointForTrack(libmv_Reconstruction *libmv_reconstruction, int track, double pos[3])
{
	libmv::EuclideanReconstruction *reconstruction = &libmv_reconstruction->reconstruction;
	libmv::EuclideanPoint *point = reconstruction->PointForTrack(track);

	if(point) {
		pos[0] = point->X[0];
		pos[1] = point->X[2];
		pos[2] = point->X[1];

		return 1;
	}

	return 0;
}

static libmv::Marker ProjectMarker(const libmv::EuclideanPoint &point, const libmv::EuclideanCamera &camera,
			const libmv::CameraIntrinsics &intrinsics) {
	libmv::Vec3 projected = camera.R * point.X + camera.t;
	projected /= projected(2);

	libmv::Marker reprojected_marker;
	intrinsics.ApplyIntrinsics(projected(0), projected(1), &reprojected_marker.x, &reprojected_marker.y);

	reprojected_marker.image = camera.image;
	reprojected_marker.track = point.track;

	return reprojected_marker;
}

double libmv_reporojectionErrorForTrack(libmv_Reconstruction *libmv_reconstruction, int track)
{
	libmv::EuclideanReconstruction *reconstruction = &libmv_reconstruction->reconstruction;
	libmv::CameraIntrinsics *intrinsics = &libmv_reconstruction->intrinsics;
	libmv::vector<libmv::Marker> markers = libmv_reconstruction->tracks.MarkersForTrack(track);

	int num_reprojected = 0;
	double total_error = 0.0;

	for (int i = 0; i < markers.size(); ++i) {
		const libmv::EuclideanCamera *camera = reconstruction->CameraForImage(markers[i].image);
		const libmv::EuclideanPoint *point = reconstruction->PointForTrack(markers[i].track);

		if (!camera || !point) {
			continue;
		}

		num_reprojected++;

		libmv::Marker reprojected_marker = ProjectMarker(*point, *camera, *intrinsics);
		double ex = reprojected_marker.x - markers[i].x;
		double ey = reprojected_marker.y - markers[i].y;

		total_error += sqrt(ex*ex + ey*ey);
	}

	return total_error / num_reprojected;
}

double libmv_reporojectionErrorForImage(libmv_Reconstruction *libmv_reconstruction, int image)
{
	libmv::EuclideanReconstruction *reconstruction = &libmv_reconstruction->reconstruction;
	libmv::CameraIntrinsics *intrinsics = &libmv_reconstruction->intrinsics;
	libmv::vector<libmv::Marker> markers = libmv_reconstruction->tracks.MarkersInImage(image);
	const libmv::EuclideanCamera *camera = reconstruction->CameraForImage(image);
	int num_reprojected = 0;
	double total_error = 0.0;

	if (!camera)
		return 0;

	for (int i = 0; i < markers.size(); ++i) {
		const libmv::EuclideanPoint *point = reconstruction->PointForTrack(markers[i].track);

		if (!point) {
			continue;
		}

		num_reprojected++;

		libmv::Marker reprojected_marker = ProjectMarker(*point, *camera, *intrinsics);
		double ex = reprojected_marker.x - markers[i].x;
		double ey = reprojected_marker.y - markers[i].y;

		total_error += sqrt(ex*ex + ey*ey);
	}

	return total_error / num_reprojected;
}

int libmv_reporojectionCameraForImage(libmv_Reconstruction *libmv_reconstruction, int image, double mat[4][4])
{
	libmv::EuclideanReconstruction *reconstruction = &libmv_reconstruction->reconstruction;
	libmv::EuclideanCamera *camera = reconstruction->CameraForImage(image);

	if(camera) {
		for (int j = 0; j < 3; ++j) {
			for (int k = 0; k < 3; ++k) {
				int l = k;

				if (k == 1) l = 2;
				else if (k == 2) l = 1;

				if (j == 2) mat[j][l] = -camera->R(j,k);
				else mat[j][l] = camera->R(j,k);
			}
			mat[j][3]= 0.0;
		}

		libmv::Vec3 optical_center = -camera->R.transpose() * camera->t;

		mat[3][0] = optical_center(0);
		mat[3][1] = optical_center(2);
		mat[3][2] = optical_center(1);

		mat[3][3]= 1.0;

		return 1;
	}

	return 0;
}

double libmv_reprojectionError(libmv_Reconstruction *libmv_reconstruction)
{
	return libmv_reconstruction->error;
}

void libmv_destroyReconstruction(libmv_Reconstruction *libmv_reconstruction)
{
	delete libmv_reconstruction;
}

/* ************ feature detector ************ */

struct libmv_Features *libmv_detectFeaturesFAST(unsigned char *data, int width, int height, int stride,
			int margin, int min_trackness, int min_distance)
{
	libmv::Feature *features = NULL;
	std::vector<libmv::Feature> v;
	libmv_Features *libmv_features = new libmv_Features();
	int i= 0, count;

	if(margin) {
		data += margin*stride+margin;
		width -= 2*margin;
		height -= 2*margin;
	}

	v = libmv::DetectFAST(data, width, height, stride, min_trackness, min_distance);

	count = v.size();

	if(count) {
		features= new libmv::Feature[count];

		for(std::vector<libmv::Feature>::iterator it = v.begin(); it != v.end(); it++) {
			features[i++]= *it;
		}
	}

	libmv_features->features = features;
	libmv_features->count = count;
	libmv_features->margin = margin;

	return (libmv_Features *)libmv_features;
}

struct libmv_Features *libmv_detectFeaturesMORAVEC(unsigned char *data, int width, int height, int stride,
			int margin, int count, int min_distance)
{
	libmv::Feature *features = NULL;
	libmv_Features *libmv_features = new libmv_Features;

	if(count) {
		if(margin) {
			data += margin*stride+margin;
			width -= 2*margin;
			height -= 2*margin;
		}

		features = new libmv::Feature[count];
		libmv::DetectMORAVEC(data, stride, width, height, features, &count, min_distance, NULL);
	}

	libmv_features->count = count;
	libmv_features->margin = margin;
	libmv_features->features = features;

	return libmv_features;
}

int libmv_countFeatures(struct libmv_Features *libmv_features)
{
	return libmv_features->count;
}

void libmv_getFeature(struct libmv_Features *libmv_features, int number, double *x, double *y, double *score, double *size)
{
	libmv::Feature feature= libmv_features->features[number];

	*x = feature.x + libmv_features->margin;
	*y = feature.y + libmv_features->margin;
	*score = feature.score;
	*size = feature.size;
}

void libmv_destroyFeatures(struct libmv_Features *libmv_features)
{
	if(libmv_features->features)
		delete [] libmv_features->features;

	delete libmv_features;
}

/* ************ camera intrinsics ************ */

struct libmv_CameraIntrinsics *libmv_ReconstructionExtractIntrinsics(struct libmv_Reconstruction *libmv_Reconstruction) {
	return (struct libmv_CameraIntrinsics *)&libmv_Reconstruction->intrinsics;
}

struct libmv_CameraIntrinsics *libmv_CameraIntrinsicsNewEmpty(void)
{
	libmv::CameraIntrinsics *camera_intrinsics = new libmv::CameraIntrinsics();

	return (struct libmv_CameraIntrinsics *) camera_intrinsics;
}

struct libmv_CameraIntrinsics *libmv_CameraIntrinsicsNew(libmv_cameraIntrinsicsOptions *libmv_camera_intrinsics_options)
{
	libmv::CameraIntrinsics *camera_intrinsics = new libmv::CameraIntrinsics();

	cameraIntrinsicsFromOptions(camera_intrinsics, libmv_camera_intrinsics_options);

	return (struct libmv_CameraIntrinsics *) camera_intrinsics;
}

struct libmv_CameraIntrinsics *libmv_CameraIntrinsicsCopy(struct libmv_CameraIntrinsics *libmvIntrinsics)
{
	libmv::CameraIntrinsics *orig_intrinsics = (libmv::CameraIntrinsics *) libmvIntrinsics;
	libmv::CameraIntrinsics *new_intrinsics= new libmv::CameraIntrinsics(*orig_intrinsics);

	return (struct libmv_CameraIntrinsics *) new_intrinsics;
}

void libmv_CameraIntrinsicsDestroy(struct libmv_CameraIntrinsics *libmvIntrinsics)
{
	libmv::CameraIntrinsics *intrinsics = (libmv::CameraIntrinsics *) libmvIntrinsics;

	delete intrinsics;
}

void libmv_CameraIntrinsicsUpdate(struct libmv_CameraIntrinsics *libmv_intrinsics,
                                  libmv_cameraIntrinsicsOptions *libmv_camera_intrinsics_options)
{
	libmv::CameraIntrinsics *camera_intrinsics = (libmv::CameraIntrinsics *) libmv_intrinsics;

	double focal_length = libmv_camera_intrinsics_options->focal_length;
	double principal_x = libmv_camera_intrinsics_options->principal_point_x;
	double principal_y = libmv_camera_intrinsics_options->principal_point_y;
	double k1 = libmv_camera_intrinsics_options->k1;
	double k2 = libmv_camera_intrinsics_options->k2;
	double k3 = libmv_camera_intrinsics_options->k3;
	int image_width = libmv_camera_intrinsics_options->image_width;
	int image_height = libmv_camera_intrinsics_options->image_height;

	/* try avoid unnecessary updates so pre-computed distortion grids are not freed */

	if (camera_intrinsics->focal_length() != focal_length)
		camera_intrinsics->SetFocalLength(focal_length, focal_length);

	if (camera_intrinsics->principal_point_x() != principal_x ||
	    camera_intrinsics->principal_point_y() != principal_y)
	{
		camera_intrinsics->SetPrincipalPoint(principal_x, principal_y);
	}

	if (camera_intrinsics->k1() != k1 ||
	    camera_intrinsics->k2() != k2 ||
	    camera_intrinsics->k3() != k3)
	{
		camera_intrinsics->SetRadialDistortion(k1, k2, k3);
	}

	if (camera_intrinsics->image_width() != image_width ||
	    camera_intrinsics->image_height() != image_height)
	{
		camera_intrinsics->SetImageSize(image_width, image_height);
	}
}

void libmv_CameraIntrinsicsSetThreads(struct libmv_CameraIntrinsics *libmv_intrinsics, int threads)
{
	libmv::CameraIntrinsics *camera_intrinsics = (libmv::CameraIntrinsics *) libmv_intrinsics;

	camera_intrinsics->SetThreads(threads);
}

void libmv_CameraIntrinsicsExtract(struct libmv_CameraIntrinsics *libmv_intrinsics, double *focal_length,
			double *principal_x, double *principal_y, double *k1, double *k2, double *k3, int *width, int *height)
{
	libmv::CameraIntrinsics *camera_intrinsics = (libmv::CameraIntrinsics *) libmv_intrinsics;

	*focal_length = camera_intrinsics->focal_length();
	*principal_x = camera_intrinsics->principal_point_x();
	*principal_y = camera_intrinsics->principal_point_y();
	*k1 = camera_intrinsics->k1();
	*k2 = camera_intrinsics->k2();
}

void libmv_CameraIntrinsicsUndistortByte(struct libmv_CameraIntrinsics *libmv_intrinsics,
			unsigned char *src, unsigned char *dst, int width, int height, float overscan, int channels)
{
	libmv::CameraIntrinsics *camera_intrinsics = (libmv::CameraIntrinsics *) libmv_intrinsics;

	camera_intrinsics->Undistort(src, dst, width, height, overscan, channels);
}

void libmv_CameraIntrinsicsUndistortFloat(struct libmv_CameraIntrinsics *libmvIntrinsics,
			float *src, float *dst, int width, int height, float overscan, int channels)
{
	libmv::CameraIntrinsics *intrinsics = (libmv::CameraIntrinsics *) libmvIntrinsics;

	intrinsics->Undistort(src, dst, width, height, overscan, channels);
}

void libmv_CameraIntrinsicsDistortByte(struct libmv_CameraIntrinsics *libmvIntrinsics,
			unsigned char *src, unsigned char *dst, int width, int height, float overscan, int channels)
{
	libmv::CameraIntrinsics *intrinsics = (libmv::CameraIntrinsics *) libmvIntrinsics;
	intrinsics->Distort(src, dst, width, height, overscan, channels);
}

void libmv_CameraIntrinsicsDistortFloat(struct libmv_CameraIntrinsics *libmvIntrinsics,
			float *src, float *dst, int width, int height, float overscan, int channels)
{
	libmv::CameraIntrinsics *intrinsics = (libmv::CameraIntrinsics *) libmvIntrinsics;

	intrinsics->Distort(src, dst, width, height, overscan, channels);
}

/* ************ utils ************ */

void libmv_ApplyCameraIntrinsics(libmv_cameraIntrinsicsOptions *libmv_camera_intrinsics_options,
                                 double x, double y, double *x1, double *y1)
{
	libmv::CameraIntrinsics camera_intrinsics;

	cameraIntrinsicsFromOptions(&camera_intrinsics, libmv_camera_intrinsics_options);

	if (libmv_camera_intrinsics_options->focal_length) {
		/* do a lens undistortion if focal length is non-zero only */

		camera_intrinsics.ApplyIntrinsics(x, y, x1, y1);
	}
}

void libmv_InvertCameraIntrinsics(libmv_cameraIntrinsicsOptions *libmv_camera_intrinsics_options,
                                  double x, double y, double *x1, double *y1)
{
	libmv::CameraIntrinsics camera_intrinsics;

	cameraIntrinsicsFromOptions(&camera_intrinsics, libmv_camera_intrinsics_options);

	if (libmv_camera_intrinsics_options->focal_length) {
		/* do a lens distortion if focal length is non-zero only */

		camera_intrinsics.InvertIntrinsics(x, y, x1, y1);
	}
}
