/**
 * Sense if other objects are near
 *
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

#ifndef KX_NEARSENSOR_H
#define KX_NEARSENSOR_H

#include "KX_TouchSensor.h"
#include "KX_ClientObjectInfo.h"

class KX_Scene;
class KX_ClientObjectInfo;

class KX_NearSensor : public KX_TouchSensor
{
	Py_Header;
	double	m_Margin;
	double  m_ResetMargin;
	KX_Scene*	m_scene;
	KX_ClientObjectInfo*	m_client_info;
protected:
	KX_NearSensor(class SCA_EventManager* eventmgr,
			class KX_GameObject* gameobj,
			void *shape,
			double margin,
			double resetmargin,
			bool bFindMaterial,
			const STR_String& touchedpropname,
			class KX_Scene* scene,
			PyTypeObject* T=&Type);

public:
	KX_NearSensor(class SCA_EventManager* eventmgr,
			class KX_GameObject* gameobj,
			double margin,
			double resetmargin,
			bool bFindMaterial,
			const STR_String& touchedpropname,
			class KX_Scene* scene,
			PyTypeObject* T=&Type);
	virtual ~KX_NearSensor(); 
	virtual CValue* GetReplica();
	virtual bool Evaluate(CValue* event);

	virtual void ReParent(SCA_IObject* parent);
	virtual DT_Bool HandleCollision(void* obj1,void* obj2,
						 const DT_CollData * coll_data); 
	virtual void RegisterSumo(KX_TouchEventManager *touchman);
	
	virtual PyObject*  _getattr(char *attr);

};

#endif //KX_NEARSENSOR_H

