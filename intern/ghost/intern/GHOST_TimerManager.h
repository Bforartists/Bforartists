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

#ifndef _GHOST_TIMER_MANAGER_H_
#define _GHOST_TIMER_MANAGER_H_

#ifdef WIN32
#pragma warning (disable:4786) // suppress stl-MSVC debug info warning
#endif // WIN32

#include <vector>

#include "GHOST_Types.h"

class GHOST_TimerTask;


/**
 * Manages a list of timer tasks.
 * Timer tasks added are owned by the manager.
 * Don't delete timer task objects.
 */
class GHOST_TimerManager
{
public:
	/**
	 * Constructor.
	 */
	GHOST_TimerManager();

	/**
	 * Destructor.
	 */
	virtual ~GHOST_TimerManager();

	/**
	 * Returns the number of timer tasks.
	 * @return The number of events on the stack.
	 */
	virtual	GHOST_TUns32 getNumTimers();

	/**
	 * Returns whther this timer task ins in our list.
	 * @return Indication of presence.
	 */
	virtual	bool getTimerFound(GHOST_TimerTask* timer);

	/**
	 * Adds a timer task to the list.
	 * It is only added when it not already present in the list.
	 * @param timer The timer task added to the list.
	 * @return Indication as to whether addition has succeeded.
	 */
	virtual GHOST_TSuccess addTimer(GHOST_TimerTask* timer);

	/**
	 * Removes a timer task from the list.
	 * It is only removed when it is found in the list.
	 * @param timer The timer task to be removed from the list.
	 * @return Indication as to whether removal has succeeded.
	 */
	virtual GHOST_TSuccess removeTimer(GHOST_TimerTask* timer);

	/**
	 * Finds the soonest time the next timer would fire.
	 * @return The soonest time the next timer would fire, 
	 * or GHOST_kFireTimeNever if no timers exist.
	 */
	virtual GHOST_TUns64 nextFireTime();
	
	/**
	 * Checks all timer tasks to see if they are expired and fires them if needed.
	 * @param time The current time.
	 * @return True if any timers were fired.
	 */
	virtual bool fireTimers(GHOST_TUns64 time);

	/**
	 * Checks this timer task to see if they are expired and fires them if needed.
	 * @param time The current time.
	 * @param task The timer task to check and optionally fire.
	 * @return True if the timer fired.
	 */
	virtual bool fireTimer(GHOST_TUns64 time, GHOST_TimerTask* task);

protected:
	/**
	 * Deletes all timers.
	 */
	void disposeTimers();

	typedef std::vector<GHOST_TimerTask*> TTimerVector;
	/** The list with event consumers. */
	TTimerVector m_timers;
};

#endif // _GHOST_TIMER_MANAGER_H_

