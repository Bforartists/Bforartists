//
// Add an object when this actuator is triggered
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
// Previously existed as:

// \source\gameengine\GameLogic\SCA_AddObjectActuator.cpp

// Please look here for revision history.


#include "KX_SCA_AddObjectActuator.h"
#include "SCA_IScene.h"
#include "KX_GameObject.h"
#include "KX_IPhysicsController.h"

#include "PyObjectPlus.h" 

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

KX_SCA_AddObjectActuator::KX_SCA_AddObjectActuator(SCA_IObject *gameobj,
												   SCA_IObject *original,
												   int time,
												   SCA_IScene* scene,
												   const MT_Vector3& linvel,
												   bool linv_local,
												   const MT_Vector3& angvel,
												   bool angv_local,
												   PyTypeObject* T)
	: 
	SCA_IActuator(gameobj, T),
	m_OriginalObject(original),
	m_scene(scene),
	
	m_linear_velocity(linvel),
	m_localLinvFlag(linv_local),
	
	m_angular_velocity(angvel),
	m_localAngvFlag(angv_local)
{
	if (m_OriginalObject)
		m_OriginalObject->RegisterActuator(this);

	m_lastCreatedObject = NULL;
	m_timeProp = time;
} 



KX_SCA_AddObjectActuator::~KX_SCA_AddObjectActuator()
{ 
	if (m_OriginalObject)
		m_OriginalObject->UnregisterActuator(this);
	if (m_lastCreatedObject)
		m_lastCreatedObject->Release();
} 



bool KX_SCA_AddObjectActuator::Update()
{
	//bool result = false;	/*unused*/
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();
	
	if (bNegativeEvent) return false; // do nothing on negative events

	InstantAddObject();

	
	return false;
}




SCA_IObject* KX_SCA_AddObjectActuator::GetLastCreatedObject() const 
{
	return m_lastCreatedObject;
}



CValue* KX_SCA_AddObjectActuator::GetReplica() 
{
	KX_SCA_AddObjectActuator* replica = new KX_SCA_AddObjectActuator(*this);

	if (replica == NULL)
		return NULL;

	// this will copy properties and so on...
	replica->ProcessReplica();
	CValue::AddDataToReplica(replica);

	return replica;
}

void KX_SCA_AddObjectActuator::ProcessReplica()
{
	if (m_OriginalObject)
		m_OriginalObject->RegisterActuator(this);
	m_lastCreatedObject=NULL;
	SCA_IActuator::ProcessReplica();
}

bool KX_SCA_AddObjectActuator::UnlinkObject(SCA_IObject* clientobj)
{
	if (clientobj == m_OriginalObject)
	{
		// this object is being deleted, we cannot continue to track it.
		m_OriginalObject = NULL;
		return true;
	}
	return false;
}

void KX_SCA_AddObjectActuator::Relink(GEN_Map<GEN_HashedPtr, void*> *obj_map)
{
	void **h_obj = (*obj_map)[m_OriginalObject];
	if (h_obj) {
		if (m_OriginalObject)
			m_OriginalObject->UnregisterActuator(this);
		m_OriginalObject = (SCA_IObject*)(*h_obj);
		m_OriginalObject->RegisterActuator(this);
	}
}


/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_SCA_AddObjectActuator::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"KX_SCA_AddObjectActuator",
	sizeof(KX_SCA_AddObjectActuator),
	0,
	PyDestructor,
	0,
	__getattr,
	__setattr,
	0, 
	__repr,
	0,
	0,
	0,
	0,
	0
};

PyParentObject KX_SCA_AddObjectActuator::Parents[] = {
	&SCA_IActuator::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};
PyMethodDef KX_SCA_AddObjectActuator::Methods[] = {
  {"setObject", (PyCFunction) KX_SCA_AddObjectActuator::sPySetObject, METH_O, (PY_METHODCHAR)SetObject_doc},
  {"setTime", (PyCFunction) KX_SCA_AddObjectActuator::sPySetTime, METH_O, (PY_METHODCHAR)SetTime_doc},
  {"getObject", (PyCFunction) KX_SCA_AddObjectActuator::sPyGetObject, METH_VARARGS, (PY_METHODCHAR)GetObject_doc},
  {"getTime", (PyCFunction) KX_SCA_AddObjectActuator::sPyGetTime, METH_NOARGS, (PY_METHODCHAR)GetTime_doc},
  {"getLinearVelocity", (PyCFunction) KX_SCA_AddObjectActuator::sPyGetLinearVelocity, METH_NOARGS, (PY_METHODCHAR)GetLinearVelocity_doc},
  {"setLinearVelocity", (PyCFunction) KX_SCA_AddObjectActuator::sPySetLinearVelocity, METH_VARARGS, (PY_METHODCHAR)SetLinearVelocity_doc},
  {"getAngularVelocity", (PyCFunction) KX_SCA_AddObjectActuator::sPyGetAngularVelocity, METH_NOARGS, (PY_METHODCHAR)GetAngularVelocity_doc},
  {"setAngularVelocity", (PyCFunction) KX_SCA_AddObjectActuator::sPySetAngularVelocity, METH_VARARGS, (PY_METHODCHAR)SetAngularVelocity_doc},
  {"getLastCreatedObject", (PyCFunction) KX_SCA_AddObjectActuator::sPyGetLastCreatedObject, METH_NOARGS,"getLastCreatedObject() : get the object handle to the last created object\n"},
  {"instantAddObject", (PyCFunction) KX_SCA_AddObjectActuator::sPyInstantAddObject, METH_NOARGS,"instantAddObject() : immediately add object without delay\n"},
  
  {NULL,NULL} //Sentinel
};


PyObject* KX_SCA_AddObjectActuator::_getattr(const STR_String& attr)
{
  _getattr_up(SCA_IActuator);
}

/* 1. setObject */
const char KX_SCA_AddObjectActuator::SetObject_doc[] = 
"setObject(object)\n"
"\t- object: KX_GameObject, string or None\n"
"\tSets the object that will be added. There has to be an object\n"
"\tof this name. If not, this function does nothing.\n";
PyObject* KX_SCA_AddObjectActuator::PySetObject(PyObject* self, PyObject* value)
{
	KX_GameObject *gameobj;
	
	if (!ConvertPythonToGameObject(value, &gameobj, true))
		return NULL; // ConvertPythonToGameObject sets the error
	
	if (m_OriginalObject != NULL)
		m_OriginalObject->UnregisterActuator(this);	

	m_OriginalObject = (SCA_IObject*)gameobj;
	if (m_OriginalObject)
		m_OriginalObject->RegisterActuator(this);
	
	Py_RETURN_NONE;
}



/* 2. setTime */
const char KX_SCA_AddObjectActuator::SetTime_doc[] = 
"setTime(duration)\n"
"\t- duration: integer\n"
"\tSets the lifetime of the object that will be added, in frames. \n"
"\tIf the duration is negative, it is set to 0.\n";


PyObject* KX_SCA_AddObjectActuator::PySetTime(PyObject* self, PyObject* value)
{
	int deltatime = PyInt_AsLong(value);
	if (deltatime==-1 && PyErr_Occurred()) {
		PyErr_SetString(PyExc_TypeError, "expected an int");
		return NULL;
	}
	
	m_timeProp = deltatime;
	if (m_timeProp < 0) m_timeProp = 0;
	
	Py_RETURN_NONE;
}



/* 3. getTime */
const char KX_SCA_AddObjectActuator::GetTime_doc[] = 
"GetTime()\n"
"\tReturns the lifetime of the object that will be added.\n";


PyObject* KX_SCA_AddObjectActuator::PyGetTime(PyObject* self)
{
	return PyInt_FromLong(m_timeProp);
}


/* 4. getObject */
const char KX_SCA_AddObjectActuator::GetObject_doc[] = 
"getObject(name_only = 1)\n"
"name_only - optional arg, when true will return the KX_GameObject rather then its name\n"
"\tReturns the name of the object that will be added.\n";
PyObject* KX_SCA_AddObjectActuator::PyGetObject(PyObject* self, PyObject* args)
{
	int ret_name_only = 1;
	if (!PyArg_ParseTuple(args, "|i", &ret_name_only))
		return NULL;
	
	if (!m_OriginalObject)
		Py_RETURN_NONE;
	
	if (ret_name_only)
		return PyString_FromString(m_OriginalObject->GetName());
	else
		return m_OriginalObject->AddRef();
}



/* 5. getLinearVelocity */
const char KX_SCA_AddObjectActuator::GetLinearVelocity_doc[] = 
"GetLinearVelocity()\n"
"\tReturns the linear velocity that will be assigned to \n"
"\tthe created object.\n";

PyObject* KX_SCA_AddObjectActuator::PyGetLinearVelocity(PyObject* self)
{
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_linear_velocity[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_linear_velocity[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_linear_velocity[2]));
	
	return retVal;
}



/* 6. setLinearVelocity                                                 */
const char KX_SCA_AddObjectActuator::SetLinearVelocity_doc[] = 
"setLinearVelocity(vx, vy, vz)\n"
"\t- vx: float\n"
"\t- vy: float\n"
"\t- vz: float\n"
"\t- local: bool\n"
"\tAssign this velocity to the created object. \n";

PyObject* KX_SCA_AddObjectActuator::PySetLinearVelocity(PyObject* self, PyObject* args)
{
	
	float vecArg[3];
	if (!PyArg_ParseTuple(args, "fff", &vecArg[0], &vecArg[1], &vecArg[2]))
		return NULL;

	m_linear_velocity.setValue(vecArg);
	Py_RETURN_NONE;
}

/* 7. getAngularVelocity */
const char KX_SCA_AddObjectActuator::GetAngularVelocity_doc[] = 
"GetAngularVelocity()\n"
"\tReturns the angular velocity that will be assigned to \n"
"\tthe created object.\n";

PyObject* KX_SCA_AddObjectActuator::PyGetAngularVelocity(PyObject* self)
{
	PyObject *retVal = PyList_New(3);

	PyList_SET_ITEM(retVal, 0, PyFloat_FromDouble(m_angular_velocity[0]));
	PyList_SET_ITEM(retVal, 1, PyFloat_FromDouble(m_angular_velocity[1]));
	PyList_SET_ITEM(retVal, 2, PyFloat_FromDouble(m_angular_velocity[2]));
	
	return retVal;
}



/* 8. setAngularVelocity                                                 */
const char KX_SCA_AddObjectActuator::SetAngularVelocity_doc[] = 
"setAngularVelocity(vx, vy, vz)\n"
"\t- vx: float\n"
"\t- vy: float\n"
"\t- vz: float\n"
"\t- local: bool\n"
"\tAssign this angular velocity to the created object. \n";

PyObject* KX_SCA_AddObjectActuator::PySetAngularVelocity(PyObject* self, PyObject* args)
{
	
	float vecArg[3];
	if (!PyArg_ParseTuple(args, "fff", &vecArg[0], &vecArg[1], &vecArg[2]))
		return NULL;

	m_angular_velocity.setValue(vecArg);
	Py_RETURN_NONE;
}

void	KX_SCA_AddObjectActuator::InstantAddObject()
{
	if (m_OriginalObject)
	{
		// Add an identical object, with properties inherited from the original object	
		// Now it needs to be added to the current scene.
		SCA_IObject* replica = m_scene->AddReplicaObject(m_OriginalObject,GetParent(),m_timeProp );
		KX_GameObject * game_obj = static_cast<KX_GameObject *>(replica);
		game_obj->setLinearVelocity(m_linear_velocity,m_localLinvFlag);
		game_obj->setAngularVelocity(m_angular_velocity,m_localAngvFlag);
		game_obj->ResolveCombinedVelocities(m_linear_velocity, m_angular_velocity, m_localLinvFlag, m_localAngvFlag);

		// keep a copy of the last object, to allow python scripters to change it
		if (m_lastCreatedObject)
		{
			//careful with destruction, it might still have outstanding collision callbacks
			m_scene->DelayedReleaseObject(m_lastCreatedObject);
			m_lastCreatedObject->Release();
		}
		
		m_lastCreatedObject = replica;
		m_lastCreatedObject->AddRef();
		// finished using replica? then release it
		replica->Release();
	}
}

PyObject* KX_SCA_AddObjectActuator::PyInstantAddObject(PyObject* self)
{
	InstantAddObject();

	Py_RETURN_NONE;
}



/* 7. GetLastCreatedObject                                                */
const char KX_SCA_AddObjectActuator::GetLastCreatedObject_doc[] = 
"getLastCreatedObject()\n"
"\tReturn the last created object. \n";


PyObject* KX_SCA_AddObjectActuator::PyGetLastCreatedObject(PyObject* self)
{
	SCA_IObject* result = this->GetLastCreatedObject();
	
	// if result->GetSGNode() is NULL
	// it means the object has ended, The BGE python api crashes in many places if the object is returned.
	if (result && (static_cast<KX_GameObject *>(result))->GetSGNode()) 
	{
		result->AddRef();
		return result;
	}
	// don't return NULL to python anymore, it gives trouble in the scripts
	Py_RETURN_NONE;
}
