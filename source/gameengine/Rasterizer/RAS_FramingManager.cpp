/**
 * $Id$
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
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
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

#include "RAS_FramingManager.h"
#include "RAS_Rect.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

	void
RAS_FramingManager::
ComputeDefaultFrustum(
	const float camnear,
	const float camfar,
	const float lens,
	const float design_aspect_ratio,
	RAS_FrameFrustum & frustum
){
		
	/*
	 * Magic Blender calculation.
	 * Blender does not give a Field of View as lens but a size
	 * at 16 units away from the lens.
	 */
	float halfSize = 16.f * camnear / lens;
	float sizeX;
	float sizeY;

	if (design_aspect_ratio > 1.f) {
		// halfsize defines the width
		sizeX = halfSize;
		sizeY = halfSize/design_aspect_ratio;
	} else {
		// halfsize defines the height
		sizeX = halfSize * design_aspect_ratio;
		sizeY = halfSize;
	}
		
	frustum.x2 = sizeX;
	frustum.x1 = -frustum.x2;
	frustum.y2 = sizeY;
	frustum.y1 = -frustum.y2;
	frustum.camnear = camnear;
	frustum.camfar = camfar;
}

	void
RAS_FramingManager::
ComputeBestFitViewRect(
	const RAS_Rect &availableViewport,
	const float design_aspect_ratio,
	RAS_Rect &viewport
){
	// try and honour the aspect ratio when setting the 
	// drawable area. If we don't do this we are liable
	// to get a lot of distortion in the rendered image.
	
	int width = availableViewport.GetWidth();
	int height = availableViewport.GetHeight();
	float window_aspect = float(width)/float(height);

	if (window_aspect < design_aspect_ratio) {
		int v_height = (int)(width / design_aspect_ratio); 
		int left_over = (height - v_height) / 2; 
			
		viewport.SetLeft(availableViewport.GetLeft());
		viewport.SetBottom(availableViewport.GetBottom() + left_over);
		viewport.SetRight(availableViewport.GetLeft() + width);
		viewport.SetTop(availableViewport.GetBottom() + left_over + v_height);

	} else {
		int v_width = (int)(height * design_aspect_ratio);
		int left_over = (width - v_width) / 2; 

		viewport.SetLeft(availableViewport.GetLeft() + left_over);
		viewport.SetBottom(availableViewport.GetBottom());
		viewport.SetRight(availableViewport.GetLeft() + v_width + left_over);
		viewport.SetTop(availableViewport.GetBottom() + height);
	}
}

	void
RAS_FramingManager::
ComputeViewport(
	const RAS_FrameSettings &settings,
	const RAS_Rect &availableViewport,
	RAS_Rect &viewport
){

	RAS_FrameSettings::RAS_FrameType type = settings.FrameType();
	const int winx = availableViewport.GetWidth();
	const int winy = availableViewport.GetHeight();

	const float design_width = float(settings.DesignAspectWidth());
	const float design_height = float(settings.DesignAspectHeight());

	float design_aspect_ratio = float(1);

	if (design_height == float(0)) {
		// well this is ill defined 
		// lets just scale the thing

		type = RAS_FrameSettings::e_frame_scale;
	} else {
		design_aspect_ratio = design_width/design_height;
	}

	switch (type) {

		case RAS_FrameSettings::e_frame_scale :
		case RAS_FrameSettings::e_frame_extend:
		{
			viewport.SetLeft(availableViewport.GetLeft());
			viewport.SetBottom(availableViewport.GetBottom());
			viewport.SetRight(availableViewport.GetLeft() + int(winx));
			viewport.SetTop(availableViewport.GetBottom() + int(winy));

			break;
		}

		case RAS_FrameSettings::e_frame_bars:
		{
			ComputeBestFitViewRect(
				availableViewport,
				design_aspect_ratio,	
				viewport
			);
		
			break;
		}
		default :
			break;
	}
}

	void
RAS_FramingManager::
ComputeFrustum(
	const RAS_FrameSettings &settings,
	const RAS_Rect &availableViewport,
	const RAS_Rect &viewport,
	const float lens,
	const float camnear,
	const float camfar,
	RAS_FrameFrustum &frustum
){

	RAS_FrameSettings::RAS_FrameType type = settings.FrameType();

	const float design_width = float(settings.DesignAspectWidth());
	const float design_height = float(settings.DesignAspectHeight());

	float design_aspect_ratio = float(1);

	if (design_height == float(0)) {
		// well this is ill defined 
		// lets just scale the thing

		type = RAS_FrameSettings::e_frame_scale;
	} else {
		design_aspect_ratio = design_width/design_height;
	}
	
	ComputeDefaultFrustum(
		camnear,
		camfar,
		lens,
		design_aspect_ratio,
		frustum
	);

	switch (type) {

		case RAS_FrameSettings::e_frame_extend:
		{
			RAS_Rect vt;
			ComputeBestFitViewRect(
				availableViewport,
				design_aspect_ratio,	
				vt
			);

			// now scale the calculated frustum by the difference
			// between vt and the viewport in each axis.
			// These are always > 1

			float x_scale = float(viewport.GetWidth())/float(vt.GetWidth());
			float y_scale = float(viewport.GetHeight())/float(vt.GetHeight());

			frustum.x1 *= x_scale;
			frustum.x2 *= x_scale;
			frustum.y1 *= y_scale;
			frustum.y2 *= y_scale;
	
			break;
		}	
		case RAS_FrameSettings::e_frame_scale :
		case RAS_FrameSettings::e_frame_bars:
		default :
			break;
	}
}	



