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
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
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
/**
 * @file	GHOST_EventCursor.h
 * Declaration of GHOST_EventCursor class.
 */

#ifndef _GHOST_EVENT_CURSOR_H_
#define _GHOST_EVENT_CURSOR_H_

#include "GHOST_Event.h"

/**
 * Cursor event.
 * @author	Maarten Gribnau
 * @date	May 11, 2001
 */
class GHOST_EventCursor : public GHOST_Event
{
public:
	/**
	 * Constructor.
	 * @param msec		The time this event was generated.
	 * @param type		The type of this event.
	 * @param x			The x-coordinate of the location the cursor was at at the time of the event.
	 * @param y			The y-coordinate of the location the cursor was at at the time of the event.
	 */
	GHOST_EventCursor(GHOST_TUns64 msec, GHOST_TEventType type, GHOST_IWindow* window, GHOST_TInt32 x, GHOST_TInt32 y)
		: GHOST_Event(msec, type, window)
	{
		m_cursorEventData.x = x;
		m_cursorEventData.y = y;
		m_data = &m_cursorEventData;
	}

	GHOST_EventCursor(GHOST_TUns64 msec, GHOST_TEventType type, GHOST_IWindow* window, char buf[256])
		: GHOST_Event(msec, type, window)
	{
		int x, y;
		sscanf(buf, "mousecursor: %d %d", &x, &y);
		
		m_cursorEventData.x = x;
		m_cursorEventData.y = y;
		m_data = &m_cursorEventData;
	}
	
	virtual int serialize(char buf[256])
	{
		sprintf(buf, "mousecursor: %d %d", m_cursorEventData.x, m_cursorEventData.y);
		
		return 0;
	}
		
protected:
	/** The x,y-coordinates of the cursor position. */
	GHOST_TEventCursorData m_cursorEventData;
};


#endif // _GHOST_EVENT_CURSOR_H_

