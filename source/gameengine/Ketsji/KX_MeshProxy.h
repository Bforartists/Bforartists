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
#ifndef __KX_MESHPROXY
#define __KX_MESHPROXY

#include "SCA_IObject.h"

class KX_MeshProxy	: public SCA_IObject
{
	Py_Header;

	class RAS_MeshObject*	m_meshobj;
public:
	KX_MeshProxy(class RAS_MeshObject* mesh);
	virtual ~KX_MeshProxy();

	// stuff for cvalue related things
	virtual CValue*		Calc(VALUE_OPERATOR op, CValue *val) ;
	virtual CValue*		CalcFinal(VALUE_DATA_TYPE dtype, VALUE_OPERATOR op, CValue *val);
	virtual const STR_String &	GetText();
	virtual float		GetNumber();
	virtual STR_String	GetName();
	virtual void		SetName(STR_String name);								// Set the name of the value
	virtual void		ReplicaSetName(STR_String name);
	virtual CValue*		GetReplica();

// stuff for python integration
	virtual PyObject*  _getattr(char *attr);
	KX_PYMETHOD(KX_MeshProxy,GetNumMaterials);
	KX_PYMETHOD(KX_MeshProxy,GetMaterialName);
	KX_PYMETHOD(KX_MeshProxy,GetTextureName);
	
	// both take materialid (int)
	KX_PYMETHOD(KX_MeshProxy,GetVertexArrayLength);
	KX_PYMETHOD(KX_MeshProxy,GetVertex);
};
#endif //__KX_MESHPROXY
