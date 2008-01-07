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
 * Ketsji Logic Extenstion: Network Event Manager generic implementation
 */

// Ketsji specific sensor part
#include "SCA_ISensor.h"

// Ketsji specific network part
#include "KX_NetworkEventManager.h"

// Network module specific
#include "NG_NetworkDeviceInterface.h"
#include "NG_NetworkMessage.h"
#include "NG_NetworkObject.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

KX_NetworkEventManager::KX_NetworkEventManager(class SCA_LogicManager*
logicmgr, class NG_NetworkDeviceInterface *ndi) :
SCA_EventManager(NETWORK_EVENTMGR), m_logicmgr(logicmgr), m_ndi(ndi)
{
	//printf("KX_NetworkEventManager constructor\n");
}

KX_NetworkEventManager::~KX_NetworkEventManager()
{
	//printf("KX_NetworkEventManager destructor\n");
}

void KX_NetworkEventManager::RegisterSensor(class SCA_ISensor* sensor)
{
	//printf("KX_NetworkEventManager RegisterSensor\n");
	m_sensors.push_back(sensor);
}

void KX_NetworkEventManager::RemoveSensor(class SCA_ISensor* sensor)
{
	//printf("KX_NetworkEventManager RemoveSensor\n");
	// Network specific RemoveSensor stuff goes here

	// parent
	SCA_EventManager::RemoveSensor(sensor);
}

void KX_NetworkEventManager::NextFrame()
{
// printf("KX_NetworkEventManager::proceed %.2f - %.2f\n", curtime, deltatime);
	// each frame, the logicmanager will call the network
	// eventmanager to look for network events, and process it's
	// 'network' sensors
	vector<class SCA_ISensor*>::iterator it;

	for (it = m_sensors.begin(); !(it==m_sensors.end()); it++) {
//	    printf("KX_NetworkEventManager::proceed sensor %.2f\n", curtime);
	    // process queue
	    (*it)->Activate(m_logicmgr, NULL);
	}

	// now a list of triggerer sensors has been built
}

void KX_NetworkEventManager::EndFrame()
{
}

