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
#ifndef __RAS_LIGHTOBJECT_H
#define __RAS_LIGHTOBJECT_H

#include "MT_CmMatrix4x4.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

struct RAS_LightObject
{
	enum LightType{
		LIGHT_SPOT,
		LIGHT_SUN,
		LIGHT_NORMAL
	};
	bool	m_modified;
	int		m_layer;
	
	float	m_energy;
	float	m_distance;
	
	float	m_red;
	float	m_green;
	float	m_blue;

	float	m_att1;
	float	m_spotsize;
	float	m_spotblend;

	LightType	m_type;
	MT_CmMatrix4x4*	m_worldmatrix;
	
};

#endif //__RAS_LIGHTOBJECT_H

