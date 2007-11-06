/**
 * $Id$
 *
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
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
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */
#ifndef RAS_FRAMINGMANAGER_H
#define RAS_FRAMINGMANAGER_H

class RAS_Rect;

/**
 * @section RAS_FrameSettings
 * This is a value type describing the framing used
 * by a particular scene in the game engine.
 * Each KX_Scene contains a RAS_FrameSetting describing
 * how the frustum and viewport are to be modified 
 * depending on the canvas size.
 *
 * e_frame_scale means that the viewport is set to the current
 * canvas size. If the view frustum aspect ratio is different 
 * to the canvas aspect this will lead to stretching.
 *
 * e_frame_extend means that the best fit viewport will be 
 * computed based upon the design aspect ratio
 * and the view frustum will be adjusted so that 
 * more of the scene is visible.
 *
 * e_frame_bars means that the best fit viewport will be
 * be computed based upon the design aspect ratio.
 */

class RAS_FrameSettings 
{
public :

	/**
	 * enum defining the policy to use 
	 * in each axis.
	 */
	enum RAS_FrameType {
		e_frame_scale,
		e_frame_extend,
		e_frame_bars
	};
	
	/**
	 * Contructor
	 */

	RAS_FrameSettings(
		RAS_FrameType frame_type,
		float bar_r,
		float bar_g,
		float bar_b,
		unsigned int design_aspect_width,
		unsigned int design_aspect_height 
	):
		m_frame_type(frame_type),
		m_bar_r(bar_r),
		m_bar_g(bar_g),
		m_bar_b(bar_b),
		m_design_aspect_width(design_aspect_width),
		m_design_aspect_height(design_aspect_height)
	{
	};

	RAS_FrameSettings(
	):
		m_frame_type(e_frame_scale),
		m_bar_r(0),
		m_bar_g(0),
		m_bar_b(0),
		m_design_aspect_width(1),
		m_design_aspect_height(1)
	{
	};

	/**
	 * Accessors
	 */

	const
		RAS_FrameType &		
	FrameType(
	) const {
		return m_frame_type;
	};
	
		float
	BarRed(
	) const {
		return m_bar_r;
	};
		
		float
	BarGreen(
	) const {
		return m_bar_g;
	};

		float
	BarBlue(
	) const {
		return m_bar_b;
	};

		unsigned int
	DesignAspectWidth(
	) const {
		return m_design_aspect_width;	
	};

		unsigned int
	DesignAspectHeight(
	) const {
		return m_design_aspect_height;	
	};

private :
	
	/**
	 * private to force use of public constructor
	 */

	RAS_FrameSettings(
		const RAS_FrameSettings &
	);

	RAS_FrameType m_frame_type;
	float m_bar_r;
	float m_bar_g;
	float m_bar_b;
	unsigned int m_design_aspect_width;
	unsigned int m_design_aspect_height;
}; 

struct RAS_FrameFrustum
{
	float camnear,camfar;
	float x1,y1;
	float x2,y2;
};	


/**
 * @section RAS_FramingManager
 * This class helps to compute a view frustum
 * and a viewport rectangle given the 
 * above settings and a description of the 
 * current canvas dimensions.
 *
 * You do not have to instantiate this class
 * directly, it only contains static helper functions
 */

class RAS_FramingManager
{
public :

	/**
	 * Compute a viewport given
	 * a RAS_FrameSettings and a description of the
	 * canvas.
	 */

	static
		void
	ComputeViewport(
		const RAS_FrameSettings &settings,
		const RAS_Rect &availableViewport,
		RAS_Rect &viewport
	);

	
	/**
	 * compute a frustrum given a valid viewport,
	 * RAS_FrameSettings, canvas description 
	 * and camera description
	 */

	static
		void
	ComputeFrustum(
		const RAS_FrameSettings &settings,
		const RAS_Rect &availableViewport,
		const RAS_Rect &viewport,
		const float lens,
		const float camnear,
		const float camfar,
		RAS_FrameFrustum &frustum
	);


private :

	static
		void
	ComputeDefaultFrustum(
		const float camnear,
		const float camfar,
		const float lens,
		const float design_aspect_ratio,
		RAS_FrameFrustum & frustum
	);	

	static
		void
	ComputeBestFitViewRect(
		const RAS_Rect &availableViewport,
		const float design_aspect_ratio,
		RAS_Rect &viewport
	);



	/**
	 * Private constructor - this class is not meant
	 * for instanciation.
	 */

	RAS_FramingManager(
	);

	RAS_FramingManager(
		const RAS_FramingManager &
	);
};		
		
#endif

