/**
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
#ifndef __KX_IACTUATOR
#define __KX_IACTUATOR

#include "SCA_IController.h"
#include <vector>

/*
 * Use of SG_DList : element of actuator being deactivated
 *                   Head: SCA_LogicManager::m_removedActuators
 * Use of SG_QList : element of activated actuator list of their owner
 *                   Head: SCA_IObject::m_activeActuators
 */
class SCA_IActuator : public SCA_ILogicBrick
{
	friend class SCA_LogicManager;
protected:
	int					 m_links;	// number of active links to controllers
									// when 0, the actuator is automatically stopped
	//std::vector<CValue*> m_events;
	bool			     m_posevent;
	bool			     m_negevent;

	std::vector<class SCA_IController*>		m_linkedcontrollers;

	void RemoveAllEvents()
	{
		m_posevent = false;
		m_negevent = false;
	}


public:
	/**
	 * This class also inherits the default copy constructors
	 */

	SCA_IActuator(SCA_IObject* gameobj,
				  PyTypeObject* T =&Type); 

	/**
	 * UnlinkObject(...)
	 * Certain actuator use gameobject pointers (like TractTo actuator)
	 * This function can be called when an object is removed to make
	 * sure that the actuator will not use it anymore.
	 */

	virtual bool UnlinkObject(SCA_IObject* clientobj) { return false; }

	/**
	 * Update(...)
	 * Update the actuator based upon the events received since 
	 * the last call to Update, the current time and deltatime the
	 * time elapsed in this frame ?
	 * It is the responsibility of concrete Actuators to clear
	 * their event's. This is usually done in the Update() method via 
	 * a call to RemoveAllEvents()
	 */


	virtual bool Update(double curtime, bool frame);
	virtual bool Update();

	/** 
	 * Add an event to an actuator.
	 */ 
	//void AddEvent(CValue* event)
	void AddEvent(bool event)
	{
		if (event)
			m_posevent = true;
		else
			m_negevent = true;
	}

	virtual void ProcessReplica();

	/** 
	 * Return true iff all the current events 
	 * are negative. The definition of negative event is
	 * not immediately clear. But usually refers to key-up events
	 * or events where no action is required.
	 */
	bool IsNegativeEvent() const
	{
		return !m_posevent && m_negevent;
	}

	virtual ~SCA_IActuator();

	/**
	 * remove this actuator from the list of active actuators
	 */
	void Deactivate()
	{
		if (QDelink())
			// the actuator was in the active list
			if (m_gameobj->m_activeActuators.QEmpty())
				// the owner object has no more active actuators, remove it from the global list
				m_gameobj->m_activeActuators.Delink();
	}

	void Activate(SG_DList& head)
	{
		if (QEmpty())
		{
			InsertActiveQList(m_gameobj->m_activeActuators);
			head.AddBack(&m_gameobj->m_activeActuators);
		}
	}

	void	LinkToController(SCA_IController* controller);
	void	UnlinkController(class SCA_IController* cont);
	void	UnlinkAllControllers();

	void ClrLink() { m_links=0; }
	void IncLink() { m_links++; }
	void DecLink();
	bool IsNoLink() const { return !m_links; }
};

#endif //__KX_IACTUATOR

