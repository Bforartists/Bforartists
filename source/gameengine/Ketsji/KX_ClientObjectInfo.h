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
#ifndef __KX_CLIENTOBJECT_INFO_H
#define __KX_CLIENTOBJECT_INFO_H

#include <SM_Object.h>

#include <list>

class SCA_ISensor;
class KX_GameObject;
/**
 * Client Type and Additional Info. This structure can be use instead of a bare void* pointer, for safeness, and additional info for callbacks
 */
struct KX_ClientObjectInfo : public SM_ClientObject
{
	enum clienttype {
		STATIC,
		ACTOR,
		RESERVED1,
		RADAR,
		NEAR
	}		m_type;
	KX_GameObject*	m_gameobject;
	void*		m_auxilary_info;
	std::list<SCA_ISensor*>	m_sensors;
public:
	KX_ClientObjectInfo(KX_GameObject *gameobject, clienttype type = STATIC, void *auxilary_info = NULL) :
		SM_ClientObject(),
		m_type(type),
		m_gameobject(gameobject),
		m_auxilary_info(auxilary_info)
	{}
	
	KX_ClientObjectInfo(const KX_ClientObjectInfo &copy)
		: SM_ClientObject(copy),
		  m_type(copy.m_type),
		  m_gameobject(copy.m_gameobject),
		  m_auxilary_info(copy.m_auxilary_info)
	{
	}
	
	virtual ~KX_ClientObjectInfo() {}
	
	virtual bool hasCollisionCallback() 
	{
		return m_sensors.size() != 0;
	}
	
	bool isActor() { return m_type <= ACTOR; }
};

#endif //__KX_CLIENTOBJECT_INFO_H

