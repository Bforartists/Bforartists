/**
 * $Id$
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

/**

 * $Id$
 * Copyright (C) 2001 NaN Technologies B.V.
 * @author	Maarten Gribnau
 * @date	September 21, 2001
 */

#ifndef _GHOST_DISPLAY_MANAGER_X11_H_
#define _GHOST_DISPLAY_MANAGER_X11_H_

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "GHOST_DisplayManager.h"


class GHOST_SystemX11;

/**
 * Manages system displays  (X11 implementation).
 */

class GHOST_DisplayManagerX11 : public GHOST_DisplayManager
{
public:
	/**
	 * Constructor.
	 */
	GHOST_DisplayManagerX11(
		GHOST_SystemX11 *system
	);

	/**
	 * Returns the number of display devices on this system.
	 * @param numDisplays The number of displays on this system.
	 * @return Indication of success.
	 */
		GHOST_TSuccess 
	getNumDisplays(
		GHOST_TUns8& numDisplays
	) const;

	/**
	 * Returns the number of display settings for this display device.
	 * @param display The index of the display to query with 0 <= display < getNumDisplays().
	 * @param setting The number of settings of the display device with this index.
	 * @return Indication of success.
	 */
		GHOST_TSuccess 
	getNumDisplaySettings(
		GHOST_TUns8 display,
		GHOST_TInt32& numSettings
	) const;

	/**
	 * Returns the current setting for this display device. 
	 * @param display The index of the display to query with 0 <= display < getNumDisplays().
	 * @param index	  The setting index to be returned.
	 * @param setting The setting of the display device with this index.
	 * @return Indication of success.
	 */
		GHOST_TSuccess 
	getDisplaySetting(
		GHOST_TUns8 display,
		GHOST_TInt32 index,
		GHOST_DisplaySetting& setting
	) const;

	/**
	 * Returns the current setting for this display device. 
	 * @param display The index of the display to query with 0 <= display < getNumDisplays().
	 * @param setting The current setting of the display device with this index.
	 * @return Indication of success.
	 */
		GHOST_TSuccess 
	getCurrentDisplaySetting(
		GHOST_TUns8 display,
		GHOST_DisplaySetting& setting
	) const;

	/**
	 * Changes the current setting for this display device. 
	 * @param display The index of the display to query with 0 <= display < getNumDisplays().
	 * @param setting The current setting of the display device with this index.
	 * @return Indication of success.
	 */
		GHOST_TSuccess 
	setCurrentDisplaySetting(
		GHOST_TUns8 display,
		const GHOST_DisplaySetting& setting
	);

private :

	GHOST_SystemX11 * m_system;
};


#endif // 

