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
 * @date	May 31, 2001
 */

#ifndef _GHOST_IEVENT_H_
#define _GHOST_IEVENT_H_

#include "GHOST_Types.h"

class GHOST_IWindow;

/**
 * Interface class for events received the operating system.
 * @author	Maarten Gribnau
 * @date	May 31, 2001
 */
class GHOST_IEvent
{
public:
	/**
	 * Destructor.
	 */
	virtual ~GHOST_IEvent()
	{
	}

	/**
	 * Returns the event type.
	 * @return The event type.
	 */
	virtual GHOST_TEventType getType() = 0;

	/**
	 * Returns the time this event was generated.
	 * @return The event generation time.
	 */
	virtual GHOST_TUns64 getTime() = 0;

	/**
	 * Returns the window this event was generated on, 
	 * or NULL if it is a 'system' event.
	 * @return The generating window.
	 */
	virtual GHOST_IWindow* getWindow() = 0;
	
	/**
	 * Returns the event data.
	 * @return The event data.
	 */
	virtual GHOST_TEventDataPtr getData() = 0;
};

#endif // _GHOST_IEVENT_H_

