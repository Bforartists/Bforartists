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
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

/** \file blender/makesrna/intern/rna_tracking.c
 *  \ingroup RNA
 */


#include <stdlib.h>
#include <limits.h>

#include "MEM_guardedalloc.h"

#include "BKE_movieclip.h"
#include "BKE_tracking.h"

#include "RNA_define.h"

#include "rna_internal.h"

#include "DNA_movieclip_types.h"
#include "DNA_scene_types.h"

#include "WM_types.h"

#ifdef RNA_RUNTIME

#include "BKE_depsgraph.h"
#include "BKE_node.h"

#include "IMB_imbuf.h"

#include "WM_api.h"

static void rna_tracking_tracks_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	rna_iterator_listbase_begin(iter, &clip->tracking.tracks, NULL);
}

static void rna_tracking_tracks_add(MovieTracking *tracking, int frame, int number)
{
	int a;

	for(a= 0; a<number; a++)
		BKE_tracking_add_track(tracking, 0, 0, frame, 1, 1);

	WM_main_add_notifier(NC_MOVIECLIP|NA_EDITED, NULL);
}

static PointerRNA rna_tracking_active_track_get(PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;

	return rna_pointer_inherit_refine(ptr, &RNA_MovieTrackingTrack, clip->tracking.act_track);
}

static void rna_tracking_active_track_set(PointerRNA *ptr, PointerRNA value)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	MovieTrackingTrack *track= (MovieTrackingTrack *)value.data;
	int index= BLI_findindex(&clip->tracking.tracks, track);

	if(index>=0) clip->tracking.act_track= track;
	else clip->tracking.act_track= NULL;
}

void rna_trackingTrack_name_set(PointerRNA *ptr, const char *value)
{
	MovieClip *clip= (MovieClip *)ptr->id.data;
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;
	BLI_strncpy(track->name, value, sizeof(track->name));

	BKE_track_unique_name(&clip->tracking, track);
}

static void rna_tracking_trackerPattern_update(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *ptr)
{
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;

	BKE_tracking_clamp_track(track, CLAMP_PAT_DIM);
}

static void rna_tracking_trackerSearch_update(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *ptr)
{
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;

	BKE_tracking_clamp_track(track, CLAMP_SEARCH_DIM);
}

static void rna_tracking_trackerAlgorithm_update(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *ptr)
{
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;

        if(track->tracker==TRACKER_KLT)
          BKE_tracking_clamp_track(track, CLAMP_PYRAMID_LEVELS);
        else
          BKE_tracking_clamp_track(track, CLAMP_SEARCH_DIM);
}

static void rna_tracking_trackerPyramid_update(Main *UNUSED(bmain), Scene *UNUSED(scene), PointerRNA *ptr)
{
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;

	BKE_tracking_clamp_track(track, CLAMP_PYRAMID_LEVELS);
}

static float rna_trackingCamera_focal_mm_get(PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	MovieTrackingCamera *camera= &clip->tracking.camera;
	float val= camera->focal;

	if(clip->lastsize[0])
		val= val*camera->sensor_width/(float)clip->lastsize[0];

	return val;
}

static void rna_trackingCamera_focal_mm_set(PointerRNA *ptr, float value)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	MovieTrackingCamera *camera= &clip->tracking.camera;

	if(clip->lastsize[0])
		value= clip->lastsize[0]*value/camera->sensor_width;

	camera->focal= value;
}

static int rna_track_2d_stabilization(CollectionPropertyIterator *UNUSED(iter), void *data)
{
	MovieTrackingTrack *track= (MovieTrackingTrack*)data;

	if((track->flag&TRACK_USE_2D_STAB)==0)
		return 1;

	return 0;
}

static void rna_tracking_stabTracks_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	rna_iterator_listbase_begin(iter, &clip->tracking.tracks, rna_track_2d_stabilization);
}

static int rna_tracking_stabTracks_active_index_get(PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	return clip->tracking.stabilization.act_track;
}

static void rna_tracking_stabTracks_active_index_set(PointerRNA *ptr, int value)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	clip->tracking.stabilization.act_track= value;
}

static void rna_tracking_stabTracks_active_index_range(PointerRNA *ptr, int *min, int *max)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;

	*min= 0;
	*max= clip->tracking.stabilization.tot_track-1;
	*max= MAX2(0, *max);
}

static void rna_tracking_flushUpdate(Main *UNUSED(bmain), Scene *scene, PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	MovieTrackingStabilization *stab= &clip->tracking.stabilization;

	stab->ok= 0;

	nodeUpdateID(scene->nodetree, &clip->id);

	WM_main_add_notifier(NC_SCENE|ND_NODES, NULL);
	DAG_id_tag_update(&clip->id, 0);
}

/* API */

static MovieTrackingMarker *rna_trackingTrack_marker_find_frame(MovieTrackingTrack *track, int framenr)
{
	return BKE_tracking_get_marker(track, framenr);
}

#else

static int rna_matrix_dimsize_4x4[]= {4, 4};

static void rna_def_trackingSettings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem speed_items[] = {
		{0, "FASTEST", 0, "Fastest", "Track as fast as it's possible"},
	    {TRACKING_SPEED_DOUBLE, "DOUBLE", 0, "Double", "Track with double speed"},
		{TRACKING_SPEED_REALTIME, "REALTIME", 0, "Realtime", "Track with realtime speed"},
		{TRACKING_SPEED_HALF, "HALF", 0, "Half", "Track with half of realtime speed"},
		{TRACKING_SPEED_QUARTER, "QUARTER", 0, "Quarter", "Track with quarter of realtime speed"},
		{0, NULL, 0, NULL, NULL}};

	static EnumPropertyItem cleanup_items[] = {
		{TRACKING_CLEAN_SELECT, "SELECT", 0, "Select", "Select unclean tracks"},
		{TRACKING_CLEAN_DELETE_TRACK, "DELETE_TRACK", 0, "Delete Track", "Delete unclean tracks"},
		{TRACKING_CLEAN_DELETE_SEGMENT, "DELETE_SEGMENTS", 0, "Delete Segments", "Delete unclean segments of tracks"},
		{0, NULL, 0, NULL, NULL}
	};

	srna= RNA_def_struct(brna, "MovieTrackingSettings", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking settings", "Match moving settings");

	/* speed */
	prop= RNA_def_property(srna, "speed", PROP_ENUM, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_enum_items(prop, speed_items);
	RNA_def_property_ui_text(prop, "Speed", "Speed to make tracking with");

	/* limit frames */
	prop= RNA_def_property(srna, "frames_limit", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "frames_limit");
	RNA_def_property_range(prop, 0, SHRT_MAX);
	RNA_def_property_ui_text(prop, "Frames Limit", "Amount of frames to be tracked during single tracking operation");

	/* adjust frames */
	prop= RNA_def_property(srna, "frames_adjust", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "adjframes");
	RNA_def_property_range(prop, 0, INT_MAX);
	RNA_def_property_ui_text(prop, "Adjust Frames", "Automatically re-adjust marker position using position on each N frames. 0 means only keyframed position is used");

	/* margin */
	prop= RNA_def_property(srna, "margin", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "margin");
	RNA_def_property_range(prop, 0, 300);
	RNA_def_property_ui_text(prop, "Margin", "Margin for markers from image boundary");

	/* keyframe_a */
	prop= RNA_def_property(srna, "keyframe_a", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "keyframe1");
	RNA_def_property_ui_text(prop, "Keyframe A", "First keyframe used for reconstruction initialization");

	/* keyframe_b */
	prop= RNA_def_property(srna, "keyframe_b", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "keyframe2");
	RNA_def_property_ui_text(prop, "Keyframe B", "Second keyframe used for reconstruction initialization");

	/* tool settings */

	/* distance */
	prop= RNA_def_property(srna, "distance", PROP_FLOAT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_float_sdna(prop, NULL, "dist");
	RNA_def_property_ui_text(prop, "Distance", "Distance between two bundles used for scene scaling");

	/* frames count */
	prop= RNA_def_property(srna, "clean_frames", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "clean_frames");
	RNA_def_property_range(prop, 0, INT_MAX);
	RNA_def_property_ui_text(prop, "Tracked Frames", "Effect on tracks which are tracked less than the specified amount of frames");

	/* reprojection error */
	prop= RNA_def_property(srna, "clean_error", PROP_FLOAT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_float_sdna(prop, NULL, "clean_error");
	RNA_def_property_range(prop, 0, FLT_MAX);
	RNA_def_property_ui_text(prop, "Reprojection Error", "Effect on tracks which have a larger reprojection error");

	/* cleanup action */
	prop= RNA_def_property(srna, "clean_action", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "clean_action");
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_enum_items(prop, cleanup_items);
	RNA_def_property_ui_text(prop, "Action", "Cleanup action to execute");
}

static void rna_def_trackingCamera(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem camera_units_items[] = {
		{CAMERA_UNITS_PX, "PIXELS", 0, "px", "Use pixels for units of focal length"},
		{CAMERA_UNITS_MM, "MILLIMETERS", 0, "mm", "Use millimeters for units of focal length"},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "MovieTrackingCamera", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking camera data", "Match-moving camera data for tracking");

	/* Sensor */
	prop= RNA_def_property(srna, "sensor_width", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "sensor_width");
	RNA_def_property_range(prop, 0.0f, 500.0f);
	RNA_def_property_ui_text(prop, "Sensor", "Width of CCD sensor in millimeters");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	/* Focal Length */
	prop= RNA_def_property(srna, "focal_length", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "focal");
	RNA_def_property_range(prop, 0.0f, 5000.0f);
	RNA_def_property_float_funcs(prop, "rna_trackingCamera_focal_mm_get", "rna_trackingCamera_focal_mm_set", NULL);
	RNA_def_property_ui_text(prop, "Focal Length", "Camera's focal length");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	/* Focal Length in pixels */
	prop= RNA_def_property(srna, "focal_length_pixels", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "focal");
	RNA_def_property_range(prop, 0.0f, 5000.0f);
	RNA_def_property_ui_text(prop, "Focal Length", "Camera's focal length");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	/* Units */
	prop= RNA_def_property(srna, "units", PROP_ENUM, PROP_NONE);
	RNA_def_property_enum_sdna(prop, NULL, "units");
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_enum_items(prop, camera_units_items);
	RNA_def_property_ui_text(prop, "Units", "Units used for camera focal length");

	/* Principal Point */
	prop= RNA_def_property(srna, "principal", PROP_FLOAT, PROP_NONE);
	RNA_def_property_array(prop, 2);
	RNA_def_property_float_sdna(prop, NULL, "principal");
	RNA_def_property_ui_text(prop, "Principal Point", "Optical center of lens");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	/* Radial distortion parameters */
	prop= RNA_def_property(srna, "k1", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "k1");
	RNA_def_property_ui_range(prop, -10, 10, .1, 3);
	RNA_def_property_ui_text(prop, "K1", "First coefficient of third order polynomial radial distortion");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_flushUpdate");

	prop= RNA_def_property(srna, "k2", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "k2");
	RNA_def_property_ui_range(prop, -10, 10, .1, 3);
	RNA_def_property_ui_text(prop, "K2", "Second coefficient of third order polynomial radial distortion");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_flushUpdate");

	prop= RNA_def_property(srna, "k3", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "k3");
	RNA_def_property_ui_range(prop, -10, 10, .1, 3);
	RNA_def_property_ui_text(prop, "K3", "Third coefficient of third order polynomial radial distortion");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_flushUpdate");

	/* pixel aspect */
	prop= RNA_def_property(srna, "pixel_aspect", PROP_FLOAT, PROP_XYZ);
	RNA_def_property_float_sdna(prop, NULL, "pixel_aspect");
	RNA_def_property_range(prop, 0.1f, 5000.0f);
	RNA_def_property_ui_range(prop, 0.1f, 5000.0f, 1, 2);
	RNA_def_property_ui_text(prop, "Pixel Aspect", "Pixel aspect ratio");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");
}

static void rna_def_trackingMarker(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MovieTrackingMarker", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking marker data", "Match-moving marker data for tracking");

	/* position */
	prop= RNA_def_property(srna, "co", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "pos");
	RNA_def_property_ui_text(prop, "Position", "Marker position at frame in normalized coordinates");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	/* frame */
	prop= RNA_def_property(srna, "frame", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);	/* can't be safty edited for now, need to re-sort markers array after change */
	RNA_def_property_int_sdna(prop, NULL, "framenr");
	RNA_def_property_ui_text(prop, "Frame", "Frame number marker is keyframed on");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	/* enable */
	prop= RNA_def_property(srna, "enable", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", MARKER_DISABLED);
	RNA_def_property_ui_text(prop, "Enable", "Is marker enabled for current frame");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);
}

static void rna_def_trackingTrack(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	FunctionRNA *func;
	PropertyRNA *parm;

	static EnumPropertyItem tracker_items[] = {
		{TRACKER_SAD, "SAD", 0, "SAD", "Sum of Absolute Differences tracker"},
		{TRACKER_KLT, "KLT", 0, "KLT", "Kanade–Lucas–Tomasi tracker"},
		{0, NULL, 0, NULL, NULL}};

	rna_def_trackingMarker(brna);

	srna= RNA_def_struct(brna, "MovieTrackingTrack", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking track data", "Match-moving track data for tracking");
	RNA_def_struct_ui_icon(srna, ICON_ANIM_DATA);

	/* name */
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "Unique name of track");
	RNA_def_property_string_funcs(prop, NULL, NULL, "rna_trackingTrack_name_set");
	RNA_def_property_string_maxlength(prop, MAX_ID_NAME);
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);
	RNA_def_struct_name_property(srna, prop);

	/* Pattern */
	prop= RNA_def_property(srna, "pattern_min", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "pat_min");
	RNA_def_property_ui_text(prop, "Pattern Min", "Left-bottom corner of pattern area in normalized coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerPattern_update");

	prop= RNA_def_property(srna, "pattern_max", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "pat_max");
	RNA_def_property_ui_text(prop, "Pattern Max", "Right-bottom corner of pattern area in normalized coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerPattern_update");

	/* Search */
	prop= RNA_def_property(srna, "search_min", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "search_min");
	RNA_def_property_ui_text(prop, "Search Min", "Left-bottom corner of search area in normalized coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerSearch_update");

	prop= RNA_def_property(srna, "search_max", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "search_max");
	RNA_def_property_ui_text(prop, "Search Max", "Right-bottom corner of search area in normalized coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerSearch_update");

	/* tracking algorithm */
	prop= RNA_def_property(srna, "tracker", PROP_ENUM, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_enum_items(prop, tracker_items);
	RNA_def_property_ui_text(prop, "Tracker", "Tracking algorithm to use");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerAlgorithm_update");

	/* pyramid level for pyramid klt tracking */
	prop= RNA_def_property(srna, "pyramid_levels", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "pyramid_levels");
	RNA_def_property_range(prop, 1, 16);
	RNA_def_property_ui_text(prop, "Pyramid levels", "Number of pyramid levels for KLT tracking");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerPyramid_update");

	/* minmal correlation - only used for SAD tracker */
	prop= RNA_def_property(srna, "correlation_min", PROP_FLOAT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_float_sdna(prop, NULL, "minimum_correlation");
	RNA_def_property_range(prop, -1.0f, 1.0f);
	RNA_def_property_ui_range(prop, -1.0f, 1.0f, 0.1, 3);
	RNA_def_property_ui_text(prop, "Correlation", "Minimal value of correlation between mathed pattern and reference which is still treated as successful tracking");

	/* markers */
	prop= RNA_def_property(srna, "markers", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieTrackingMarker");
	RNA_def_property_collection_sdna(prop, NULL, "markers", "markersnr");
	RNA_def_property_ui_text(prop, "Markers", "Collection of markers in track");

	/* ** channels ** */

	/* use_red_channel */
	prop= RNA_def_property(srna, "use_red_channel", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", TRACK_DISABLE_RED);
	RNA_def_property_ui_text(prop, "Use Red Channel", "Use red channel from footage for tracking");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, NULL);

	/* use_green_channel */
	prop= RNA_def_property(srna, "use_green_channel", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", TRACK_DISABLE_GREEN);
	RNA_def_property_ui_text(prop, "Use Green Channel", "Use green channel from footage for tracking");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, NULL);

	/* use_blue_channel */
	prop= RNA_def_property(srna, "use_blue_channel", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", TRACK_DISABLE_BLUE);
	RNA_def_property_ui_text(prop, "Use Blue Channel", "Use blue channel from footage for tracking");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, NULL);

	/* has bundle */
	prop= RNA_def_property(srna, "has_bundle", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACK_HAS_BUNDLE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Has Bundle", "True if track has a valid bundle");

	/* bundle position */
	prop= RNA_def_property(srna, "bundle", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 3);
	RNA_def_property_float_sdna(prop, NULL, "bundle_pos");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bundle", "Position of bundle reconstructed from this track");

	/* hide */
	prop= RNA_def_property(srna, "hide", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACK_HIDDEN);
	RNA_def_property_ui_text(prop, "Hide", "Track is hidden");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, NULL);

	/* locked */
	prop= RNA_def_property(srna, "lock", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACK_LOCKED);
	RNA_def_property_ui_text(prop, "Lock", "Track is locked and all changes to it are disabled");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, NULL);

	/* custom color */
	prop= RNA_def_property(srna, "use_custom_color", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACK_CUSTOMCOLOR);
	RNA_def_property_ui_text(prop, "Custom Color", "Use custom color instead of theme-defined");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, NULL);

	/* color */
	prop= RNA_def_property(srna, "color", PROP_FLOAT, PROP_COLOR);
	RNA_def_property_array(prop, 3);
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Color", "Color of the track in the Clip Editor");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, NULL);

	/* average error */
	prop= RNA_def_property(srna, "average_error", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "error");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Average Error", "Average error of re-projection");

	/* ** api ** */

	func= RNA_def_function(srna, "marker_find_frame", "rna_trackingTrack_marker_find_frame");
	RNA_def_function_ui_description(func, "Get marker for specified frame");
	parm= RNA_def_int(func, "frame", 1, MINFRAME, MAXFRAME, "Frame", "type for the new spline", MINFRAME, MAXFRAME);
	RNA_def_property_flag(parm, PROP_REQUIRED);
	parm= RNA_def_pointer(func, "marker", "MovieTrackingMarker", "", "Marker for specified frame");
	RNA_def_function_return(func, parm);
}

static void rna_def_trackingStabilization(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MovieTrackingStabilization", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking stabilization data", "Match-moving stabilization data for tracking");

	/* 2d stabilization */
	prop= RNA_def_property(srna, "use_2d_stabilization", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACKING_2D_STABILIZATION);
	RNA_def_property_ui_text(prop, "Use 2D stabilization", "Use 2D stabilization for footage");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");

	/* tracks */
	prop= RNA_def_property(srna, "tracks", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_funcs(prop, "rna_tracking_stabTracks_begin", "rna_iterator_listbase_next", "rna_iterator_listbase_end", "rna_iterator_listbase_get", 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "MovieTrackingTrack");
	RNA_def_property_ui_text(prop, "Tracks", "Collection of tracks used for stabilization");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");

	/* rotation track */
	prop= RNA_def_property(srna, "rotation_track", PROP_POINTER, PROP_NONE);
	RNA_def_property_pointer_sdna(prop, NULL, "rot_track");
	RNA_def_property_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Rotation Track", "Track used to compensate rotation");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_flushUpdate");

	/* active track index */
	prop= RNA_def_property(srna, "active_track_index", PROP_INT, PROP_NONE);
	RNA_def_property_int_sdna(prop, NULL, "act_track");
	RNA_def_property_int_funcs(prop, "rna_tracking_stabTracks_active_index_get", "rna_tracking_stabTracks_active_index_set", "rna_tracking_stabTracks_active_index_range");
	RNA_def_property_ui_text(prop, "Active Track Index", "Index of active track in stabilization tracks list");

	/* autoscale */
	prop= RNA_def_property(srna, "use_autoscale", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACKING_AUTOSCALE);
	RNA_def_property_ui_text(prop, "Autoscale", "Automatically scale footage to cover unfilled areas when stabilizating");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");

	/* max scale */
	prop= RNA_def_property(srna, "scale_max", PROP_FLOAT, PROP_FACTOR);
	RNA_def_property_float_sdna(prop, NULL, "maxscale");
	RNA_def_property_range(prop, 0.0f, 10.0f);
	RNA_def_property_ui_text(prop, "Miximal Scale", "Maximal value for scale factor");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");

	/* influence_location */
	prop= RNA_def_property(srna, "influence_location", PROP_FLOAT, PROP_FACTOR);
	RNA_def_property_float_sdna(prop, NULL, "locinf");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Location Influence", "Influence of stabilization algorithm on footage location");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");

	/* influence_scale */
	prop= RNA_def_property(srna, "influence_scale", PROP_FLOAT, PROP_FACTOR);
	RNA_def_property_float_sdna(prop, NULL, "scaleinf");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Scale Influence", "Influence of stabilization algorithm on footage scale");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");

	/* influence_rotation */
	prop= RNA_def_property(srna, "influence_rotation", PROP_FLOAT, PROP_FACTOR);
	RNA_def_property_float_sdna(prop, NULL, "rotinf");
	RNA_def_property_range(prop, 0.0f, 1.0f);
	RNA_def_property_ui_text(prop, "Rotation Influence", "Influence of stabilization algorithm on footage rotation");
	RNA_def_property_update(prop, NC_MOVIECLIP|ND_DISPLAY, "rna_tracking_flushUpdate");
}

static void rna_def_reconstructedCamera(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MovieReconstructedCamera", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking reconstructed camera data", "Match-moving reconstructed camera data from tracker");

	/* frame */
	prop= RNA_def_property(srna, "frame", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_int_sdna(prop, NULL, "framenr");
	RNA_def_property_ui_text(prop, "Frame", "Frame number marker is keyframed on");

	/* matrix */
	prop= RNA_def_property(srna, "matrix", PROP_FLOAT, PROP_MATRIX);
	RNA_def_property_float_sdna(prop, NULL, "mat");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_multi_array(prop, 2, rna_matrix_dimsize_4x4);
	RNA_def_property_ui_text(prop, "Matrix", "Worldspace transformation matrix");

	/* average_error */
	prop= RNA_def_property(srna, "average_error", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "error");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Average Error", "Average error of resonctruction");
}

static void rna_def_trackingReconstruction(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	rna_def_reconstructedCamera(brna);

	srna= RNA_def_struct(brna, "MovieTrackingReconstruction", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking reconstruction data", "Match-moving reconstruction data from tracker");

	/* is_valid */
	prop= RNA_def_property(srna, "is_valid", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACKING_RECONSTRUCTED);
	RNA_def_property_ui_text(prop, "Reconstructed", "Is tracking data contains valid reconstruction information");

	/* average_error */
	prop= RNA_def_property(srna, "average_error", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "error");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Average Error", "Average error of resonctruction");

	/* cameras */
	prop= RNA_def_property(srna, "cameras", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieReconstructedCamera");
	RNA_def_property_collection_sdna(prop, NULL, "cameras", "camnr");
	RNA_def_property_ui_text(prop, "Cameras", "Collection of solved cameras");
}

static void rna_def_trackingTracks(BlenderRNA *brna, PropertyRNA *cprop)
{
	StructRNA *srna;
	FunctionRNA *func;
	PropertyRNA *prop;

	RNA_def_property_srna(cprop, "MovieTrackingTracks");
	srna= RNA_def_struct(brna, "MovieTrackingTracks", NULL);
	RNA_def_struct_sdna(srna, "MovieTracking");
	RNA_def_struct_ui_text(srna, "Movie Tracks", "Collection of movie tracking tracks");

	func= RNA_def_function(srna, "add", "rna_tracking_tracks_add");
	RNA_def_function_ui_description(func, "Add a number of tracks to this movie clip");
	RNA_def_int(func, "frame", 1, MINFRAME, MAXFRAME, "Frame", "Frame number to add tracks on", MINFRAME, MAXFRAME);
	RNA_def_int(func, "count", 1, 0, INT_MAX, "Number", "Number of tracks to add to the movie clip", 0, INT_MAX);

	/* active track */
	prop= RNA_def_property(srna, "active", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieTrackingTrack");
	RNA_def_property_pointer_funcs(prop, "rna_tracking_active_track_get", "rna_tracking_active_track_set", NULL, NULL);
	RNA_def_property_flag(prop, PROP_EDITABLE|PROP_NEVER_UNLINK);
	RNA_def_property_ui_text(prop, "Active Track", "Active track in this tracking data object");
}

static void rna_def_tracking(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	rna_def_trackingSettings(brna);
	rna_def_trackingCamera(brna);
	rna_def_trackingTrack(brna);
	rna_def_trackingStabilization(brna);
	rna_def_trackingReconstruction(brna);

	srna= RNA_def_struct(brna, "MovieTracking", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking data", "Match-moving data for tracking");

	/* settings */
	prop= RNA_def_property(srna, "settings", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieTrackingSettings");

	/* camera properties */
	prop= RNA_def_property(srna, "camera", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieTrackingCamera");

	/* tracks */
	prop= RNA_def_property(srna, "tracks", PROP_COLLECTION, PROP_NONE);
	RNA_def_property_collection_funcs(prop, "rna_tracking_tracks_begin", "rna_iterator_listbase_next", "rna_iterator_listbase_end", "rna_iterator_listbase_get", 0, 0, 0, 0);
	RNA_def_property_struct_type(prop, "MovieTrackingTrack");
	RNA_def_property_ui_text(prop, "Tracks", "Collection of tracks in this tracking data object");
	rna_def_trackingTracks(brna, prop);

	/* stabilization */
	prop= RNA_def_property(srna, "stabilization", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieTrackingStabilization");

	/* reconstruction */
	prop= RNA_def_property(srna, "reconstruction", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieTrackingReconstruction");
}

void RNA_def_tracking(BlenderRNA *brna)
{
	rna_def_tracking(brna);
}

#endif
