//
// Add object to the game world on action of this actuator. A copy is made
// of a referenced object. The copy inherits some properties from the owner
// of this actuator.
//
// $Id$
//
// ***** BEGIN GPL LICENSE BLOCK *****
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software Foundation,
// Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
//
// The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
// All rights reserved.
//
// The Original Code is: all of this file.
//
// Contributor(s): none yet.
//
// ***** END GPL LICENSE BLOCK *****
//
// Previously existed as:
// \source\gameengine\GameLogic\SCA_AddObjectActuator.h
// Please look here for revision history.

#ifndef __KX_SCA_AddObjectActuator
#define __KX_SCA_AddObjectActuator

/* Actuator tree */
#include "SCA_IActuator.h"
#include "SCA_LogicManager.h"

#include "MT_Vector3.h"

class SCA_IScene;

class KX_SCA_AddObjectActuator : public SCA_IActuator
{
	Py_Header;

	/// Time field: lifetime of the new object
	int	m_timeProp;

	/// Original object reference (object to replicate)  	
	SCA_IObject*	m_OriginalObject;

	/// Object will be added to the following scene
	SCA_IScene*	m_scene;

	/// Linear velocity upon creation of the object. 
	float  m_linear_velocity[3];
	/// Apply the velocity locally 
	bool m_localLinvFlag;
	
	/// Angular velocity upon creation of the object. 
	float  m_angular_velocity[3];
	/// Apply the velocity locally 
	bool m_localAngvFlag; 
	
	
	
	
	SCA_IObject*	m_lastCreatedObject;
	
public:

	/** 
	 * This class also has the default constructors
	 * available. Use with care!
	 */

	KX_SCA_AddObjectActuator(
		SCA_IObject *gameobj,
		SCA_IObject *original,
		int time,
		SCA_IScene* scene,
		const float *linvel,
		bool linv_local,
		const float *angvel,
		bool angv_local,
		PyTypeObject* T=&Type
	);

	~KX_SCA_AddObjectActuator(void);

		CValue* 
	GetReplica(
	) ;

	virtual void 
	ProcessReplica();

	virtual bool 
	UnlinkObject(SCA_IObject* clientobj);

	virtual void 
	Relink(GEN_Map<GEN_HashedPtr, void*> *obj_map);

	virtual bool 
	Update();

	virtual PyObject* py_getattro(PyObject *attr);
	virtual PyObject* py_getattro_dict();
	virtual int py_setattro(PyObject *attr, PyObject* value);

		SCA_IObject*	
	GetLastCreatedObject(
	) const ;

	void	InstantAddObject();

	/* 1. setObject */
	KX_PYMETHOD_DOC_O(KX_SCA_AddObjectActuator,SetObject);
	/* 2. setTime */
	KX_PYMETHOD_DOC_O(KX_SCA_AddObjectActuator,SetTime);
	/* 3. getTime */
	KX_PYMETHOD_DOC_NOARGS(KX_SCA_AddObjectActuator,GetTime);
	/* 4. getObject */
	KX_PYMETHOD_DOC_VARARGS(KX_SCA_AddObjectActuator,GetObject);
	/* 5. getLinearVelocity */
	KX_PYMETHOD_DOC_NOARGS(KX_SCA_AddObjectActuator,GetLinearVelocity);
	/* 6. setLinearVelocity */
	KX_PYMETHOD_DOC_VARARGS(KX_SCA_AddObjectActuator,SetLinearVelocity);
	/* 7. getAngularVelocity */
	KX_PYMETHOD_DOC_NOARGS(KX_SCA_AddObjectActuator,GetAngularVelocity);
	/* 8. setAngularVelocity */
	KX_PYMETHOD_DOC_VARARGS(KX_SCA_AddObjectActuator,SetAngularVelocity);
	/* 9. getLastCreatedObject */
	KX_PYMETHOD_DOC_NOARGS(KX_SCA_AddObjectActuator,GetLastCreatedObject);
	/* 10. instantAddObject*/
	KX_PYMETHOD_DOC_NOARGS(KX_SCA_AddObjectActuator,InstantAddObject);

	static PyObject* pyattr_get_object(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef);
	static int pyattr_set_object(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value);
	static PyObject* pyattr_get_objectLastCreated(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef);
	
}; /* end of class KX_SCA_AddObjectActuator : public KX_EditObjectActuator */

#endif

