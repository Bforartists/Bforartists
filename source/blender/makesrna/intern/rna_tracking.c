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

static void rna_tracking_tracks_begin(CollectionPropertyIterator *iter, PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	rna_iterator_listbase_begin(iter, &clip->tracking.tracks, NULL);
}

void rna_trackingTrack_name_get(PointerRNA *ptr, char *value)
{
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;
	BLI_strncpy(value, track->name, sizeof(track->name));
}

int rna_trackingTrack_name_length(PointerRNA *ptr)
{
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;
	return strlen(track->name);
}

void rna_trackingTrack_name_set(PointerRNA *ptr, const char *value)
{
	MovieClip *clip= (MovieClip *)ptr->id.data;
	MovieTrackingTrack *track= (MovieTrackingTrack *)ptr->data;
	BLI_strncpy(track->name, value, sizeof(track->name));

	BKE_track_unique_name(&clip->tracking, track);
}

static void rna_tracking_trackerPattern_update(Main *bmain, Scene *scene, PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	MovieTrackingTrack *track;

	/* XXX: clamp modified marker only */
	track= clip->tracking.tracks.first;
	while(track) {
		BKE_tracking_clamp_track(track, CLAMP_PAT_DIM);
		track= track->next;
	}
}

static void rna_tracking_trackerSearch_update(Main *bmain, Scene *scene, PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	MovieTrackingTrack *track;

	/* XXX: clamp modified marker only */
	track= clip->tracking.tracks.first;
	while(track) {
		BKE_tracking_clamp_track(track, CLAMP_SEARCH_DIM);
		track= track->next;
	}
}

static PointerRNA rna_tracking_active_track_get(PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	int type;
	void *sel;

	BKE_movieclip_last_selection(clip, &type, &sel);

	if(type==MCLIP_SEL_TRACK)
		return rna_pointer_inherit_refine(ptr, &RNA_MovieTrackingTrack, sel);

	return rna_pointer_inherit_refine(ptr, &RNA_SceneRenderLayer, NULL);
}

static float rna_trackingCamera_focal_get(PointerRNA *ptr)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
	MovieTrackingCamera *camera= &clip->tracking.camera;
	float val= camera->focal;

	if(camera->units==CAMERA_UNITS_MM) {
		int width, height;

		BKE_movieclip_approx_size(clip, &width, &height);

		if(width)
			val= val*camera->sensor_width/(float)width;
	}

	return val;
}

static void rna_trackingCamera_focal_set(PointerRNA *ptr, float value)
{
	MovieClip *clip= (MovieClip*)ptr->id.data;
}

#else

static void rna_def_trackingSettings(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem speed_items[] = {
		{0, "FASTEST", 0, "Fastest", "Track as fast as it's possible"},
		{TRACKING_SPEED_REALTIME, "REALTIME", 0, "Realtime", "Track with realtime speed"},
		{TRACKING_SPEED_HALF, "HALF", 0, "Half", "Track with half of realtime speed"},
		{TRACKING_SPEED_HALF, "QUARTER", 0, "Quarter", "Track with quarter of realtime speed"},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "MovieTrackingSettings", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking settings", "Match-moving tracking settings");

	/* speed */
	prop= RNA_def_property(srna, "speed", PROP_ENUM, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_enum_items(prop, speed_items);
	RNA_def_property_ui_text(prop, "Speed", "Speed to make tracking with");

	/* use limit frames */
	prop= RNA_def_property(srna, "use_frames_limit", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACKING_FRAMES_LIMIT);
	RNA_def_property_ui_text(prop, "Limit Frames", "Limit number of frames be tracked during single tracking operation");

	/* limit frames */
	prop= RNA_def_property(srna, "frames_limit", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "frames_limit");
	RNA_def_property_range(prop, 1, INT_MAX);
	RNA_def_property_ui_text(prop, "Frames Limit", "Amount of frames to be tracked during single tracking operation");

	/* keyframe1 */
	prop= RNA_def_property(srna, "keyframe1", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "keyframe1");
	RNA_def_property_ui_text(prop, "Keyframe 1", "First keyframe used for reconstruction initialization");

	/* keyframe2 */
	prop= RNA_def_property(srna, "keyframe2", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_ANIMATABLE);
	RNA_def_property_int_sdna(prop, NULL, "keyframe2");
	RNA_def_property_ui_text(prop, "Keyframe 2", "Second keyframe used for reconstruction initialization");
}

static void rna_def_trackingCamera(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	static EnumPropertyItem camera_units_items[] = {
		{CAMERA_UNITS_PX, "PIXELS", 0, "Pixels", "Use pixels for units of focal length"},
		{CAMERA_UNITS_MM, "MILLIMETERS", 0, "Millimeters", "Use millimeters for units of focal length"},
		{0, NULL, 0, NULL, NULL}};

	srna= RNA_def_struct(brna, "MovieTrackingCamera", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking camera data", "Match-moving camera data for tracking");

	/* Sensor Wdth */
	prop= RNA_def_property(srna, "sensor_width", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "sensor_width");
	RNA_def_property_range(prop, 0.0f, 500.0f);
	RNA_def_property_ui_text(prop, "Sensor Width", "Width of CCD sensor in millimeters");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	/* Focal Length */
	prop= RNA_def_property(srna, "focal_length", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "focal");
	RNA_def_property_range(prop, 0.0f, 5000.0f);
	RNA_def_property_ui_text(prop, "Focal Length", "Camera's focal length in pixels");
	RNA_def_property_float_funcs(prop, "rna_trackingCamera_focal_get", "rna_trackingCamera_focal_set", NULL);
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
	RNA_def_property_ui_text(prop, "K1", "");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	prop= RNA_def_property(srna, "k2", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "k2");
	RNA_def_property_ui_text(prop, "K2", "");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);

	prop= RNA_def_property(srna, "k3", PROP_FLOAT, PROP_NONE);
	RNA_def_property_float_sdna(prop, NULL, "k3");
	RNA_def_property_ui_text(prop, "K3", "");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);
}

static void rna_def_trackingMarker(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	srna= RNA_def_struct(brna, "MovieTrackingMarker", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking marker data", "Match-moving marker data for tracking");

	/* Position */
	prop= RNA_def_property(srna, "pos", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "pos");
	RNA_def_property_ui_text(prop, "Position", "Marker position at frame in unified coordinates");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);
}

static void rna_def_trackingTrack(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	rna_def_trackingMarker(brna);

	srna= RNA_def_struct(brna, "MovieTrackingTrack", NULL);
	RNA_def_struct_ui_text(srna, "Movie tracking track data", "Match-moving track data for tracking");

	/* name */
	prop= RNA_def_property(srna, "name", PROP_STRING, PROP_NONE);
	RNA_def_property_ui_text(prop, "Name", "Unique name of track");
	RNA_def_property_string_funcs(prop, "rna_trackingTrack_name_get", "rna_trackingTrack_name_length", "rna_trackingTrack_name_set");
	RNA_def_property_string_maxlength(prop, MAX_ID_NAME);
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, NULL);
	RNA_def_struct_name_property(srna, prop);

	/* Pattern */
	prop= RNA_def_property(srna, "pattern_min", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "pat_min");
	RNA_def_property_ui_text(prop, "Pattern Min", "Left-bottom corner of pattern area in unified coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerPattern_update");

	prop= RNA_def_property(srna, "pattern_max", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "pat_max");
	RNA_def_property_ui_text(prop, "Pattern Max", "Right-bottom corner of pattern area in unified coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerPattern_update");

	/* Search */
	prop= RNA_def_property(srna, "search_min", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "search_min");
	RNA_def_property_ui_text(prop, "Search Min", "Left-bottom corner of search area in unified coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerSearch_update");

	prop= RNA_def_property(srna, "search_max", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 2);
	RNA_def_property_ui_range(prop, -FLT_MAX, FLT_MAX, 1, 5);
	RNA_def_property_float_sdna(prop, NULL, "search_max");
	RNA_def_property_ui_text(prop, "Search Max", "Right-bottom corner of search area in unified coordinates relative to marker position");
	RNA_def_property_update(prop, NC_MOVIECLIP|NA_EDITED, "rna_tracking_trackerSearch_update");

	/* markers_count */
	prop= RNA_def_property(srna, "markers_count", PROP_INT, PROP_NONE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_int_sdna(prop, NULL, "markersnr");
	RNA_def_property_ui_text(prop, "Markers Count", "Total number of markers in track");

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

	/* use_green_channel */
	prop= RNA_def_property(srna, "use_green_channel", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", TRACK_DISABLE_GREEN);
	RNA_def_property_ui_text(prop, "Use Green Channel", "Use green channel from footage for tracking");

	/* use_blue_channel */
	prop= RNA_def_property(srna, "use_blue_channel", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_negative_sdna(prop, NULL, "flag", TRACK_DISABLE_BLUE);
	RNA_def_property_ui_text(prop, "Use Blue Channel", "Use blue channel from footage for tracking");

	/* has bundle */
	prop= RNA_def_property(srna, "bas_bundle", PROP_BOOLEAN, PROP_NONE);
	RNA_def_property_boolean_sdna(prop, NULL, "flag", TRACK_HAS_BUNDLE);
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Has Bundle", "True if track has a valid bundle");

	/* bundle position */
	prop= RNA_def_property(srna, "bundle", PROP_FLOAT, PROP_TRANSLATION);
	RNA_def_property_array(prop, 3);
	RNA_def_property_float_sdna(prop, NULL, "bundle_pos");
	RNA_def_property_clear_flag(prop, PROP_EDITABLE);
	RNA_def_property_ui_text(prop, "Bundle", "Position of bundle reconstructed from this tarck");
}

static void rna_def_tracking(BlenderRNA *brna)
{
	StructRNA *srna;
	PropertyRNA *prop;

	rna_def_trackingSettings(brna);
	rna_def_trackingCamera(brna);
	rna_def_trackingTrack(brna);

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
	RNA_def_property_collection_funcs(prop, "rna_tracking_tracks_begin", "rna_iterator_listbase_next", "rna_iterator_listbase_end", "rna_iterator_listbase_get", 0, 0, 0);
	RNA_def_property_struct_type(prop, "MovieTrackingTrack");
	RNA_def_property_ui_text(prop, "Tracks", "Collection of tracks in this tracking data object");

	/* active tracks */
	prop= RNA_def_property(srna, "active_track", PROP_POINTER, PROP_NONE);
	RNA_def_property_struct_type(prop, "MovieTrackingTrack");
	RNA_def_property_pointer_funcs(prop, "rna_tracking_active_track_get", NULL, NULL, NULL);
	RNA_def_property_ui_text(prop, "Active Track", "Active track in this tracking data object");
}

void RNA_def_tracking(BlenderRNA *brna)
{
	rna_def_tracking(brna);
}

#endif
