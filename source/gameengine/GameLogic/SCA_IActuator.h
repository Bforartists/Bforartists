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
#ifndef __KX_IACTUATOR
#define __KX_IACTUATOR

#include "SCA_ILogicBrick.h"
#include <vector>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

class SCA_IActuator : public SCA_ILogicBrick
{
protected:
	std::vector<CValue*> m_events;
	void RemoveAllEvents();

public:
	/**
	 * This class also inherits the default copy constructors
	 */

	SCA_IActuator(SCA_IObject* gameobj,
				  PyTypeObject* T =&Type); 

	/**
	 * Update(...)
	 * Update the actuator based upon the events received since 
	 * the last call to Update, the current time and deltatime the
	 * time elapsed in this frame ?
	 * It is the responsibility of concrete Actuators to clear
	 * their event's. This is usually done in the Update() method via 
	 * a call to RemoveAllEvents()
	 */


	virtual bool Update(double curtime,
						double deltatime);

	/** 
	 * Add an event to an actuator.
	 */ 
	void AddEvent(CValue* event);
	virtual void ProcessReplica();

	/** 
	 * Return true iff all the current events 
	 * are negative. The definition of negative event is
	 * not immediately clear. But usually refers to key-up events
	 * or events where no action is required.
	 */
	bool IsNegativeEvent() const;
	virtual ~SCA_IActuator();
};

#endif //__KX_IACTUATOR

