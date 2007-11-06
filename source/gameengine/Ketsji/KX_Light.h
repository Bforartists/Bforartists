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
#ifndef __KX_LIGHT
#define __KX_LIGHT

#include "RAS_LightObject.h"
#include "KX_GameObject.h"

class KX_LightObject : public KX_GameObject
{
	Py_Header;
protected:
	RAS_LightObject		m_lightobj;
	class RAS_IRenderTools*	m_rendertools;	//needed for registering and replication of lightobj
	static char		doc[];

public:
	KX_LightObject(void* sgReplicationInfo,SG_Callbacks callbacks,class RAS_IRenderTools* rendertools,const struct RAS_LightObject&	lightobj, PyTypeObject *T = &Type);
	virtual ~KX_LightObject();
	virtual CValue*		GetReplica();
	RAS_LightObject*	GetLightData() { return &m_lightobj;}
	
	virtual PyObject* _getattr(const STR_String& attr); /* lens, near, far, projection_matrix */
	virtual int       _setattr(const STR_String& attr, PyObject *pyvalue);
};

#endif //__KX_LIGHT

