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
#ifndef __KX_TOUCHEVENTMANAGER
#define __KX_TOUCHEVENTMANAGER

#include "SCA_EventManager.h"
#include "KX_TouchSensor.h"
#include "KX_GameObject.h"

#include <vector>
#include <set>

class SCA_ISensor;
class SM_Object;

class KX_TouchEventManager : public SCA_EventManager
{
	typedef std::pair<SM_Object*, SM_Object*> Collision;
	class SCA_LogicManager* m_logicmgr;
	SM_Scene *m_scene;
	
	std::set<Collision> m_collisions;
	

	static DT_Bool collisionResponse(void *client_data, 
							void *object1,
							void *object2,
							const DT_CollData *coll_data);
	
	virtual DT_Bool HandleCollision(void* obj1,void* obj2,
						 const DT_CollData * coll_data); 
	

public:
	KX_TouchEventManager(class SCA_LogicManager* logicmgr,  
		SM_Scene *scene);
	virtual void NextFrame();
	virtual void	EndFrame();
	virtual void	RemoveSensor(class SCA_ISensor* sensor);
	virtual void RegisterSensor(SCA_ISensor* sensor);
	SCA_LogicManager* GetLogicManager() { return m_logicmgr;}
	SM_Scene *GetSumoScene() { return m_scene; }
};

#endif //__KX_TOUCHEVENTMANAGER

