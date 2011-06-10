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
 * The Original Code is Copyright (C) Blender Foundation.
 * All rights reserved.
 *
 * Contributor(s): Blender Foundation,
 *                 Sergey Sharybin
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#ifndef BKE_TRACKING_H
#define BKE_TRACKING_H

/** \file BKE_trackingp.h
 *  \ingroup bke
 *  \author Sergey Sharybin
 */

struct MovieTrackingTrack;
struct MovieTrackingMarker;
struct MovieTracking;

void BKE_tracking_clamp_track(struct MovieTrackingTrack *track, int event);
void BKE_tracking_track_flag(struct MovieTrackingTrack *track, int area, int flag, int clear);
void BKE_tracking_insert_marker(struct MovieTrackingTrack *track, struct MovieTrackingMarker *marker);
struct MovieTrackingMarker *BKE_tracking_get_marker(struct MovieTrackingTrack *track, int framenr);
int BKE_tracking_has_marker(struct MovieTrackingTrack *track, int framenr);
void BKE_tracking_free_track(struct MovieTrackingTrack *track);
void BKE_tracking_free(struct MovieTracking *tracking);

#define TRACK_SELECTED(track) ((track)->flag&SELECT || (track)->pat_flag&SELECT || (track)->search_flag&SELECT)
#define TRACK_AREA_SELECTED(track, area) ((area)==TRACK_AREA_POINT?(track)->flag&SELECT : ((area)==TRACK_AREA_PAT?(track)->pat_flag&SELECT:(track)->search_flag&SELECT))

#define CLAMP_PAT_DIM		1
#define CLAMP_PAT_POS		2
#define CLAMP_SEARCH_DIM	3
#define CLAMP_SEARCH_POS	4

#define TRACK_AREA_NONE	-	1
#define TRACK_AREA_POINT	1
#define TRACK_AREA_PAT		2
#define TRACK_AREA_SEARCH	4

#define TRACK_AREA_ALL		(TRACK_AREA_POINT|TRACK_AREA_PAT|TRACK_AREA_SEARCH)

#endif
