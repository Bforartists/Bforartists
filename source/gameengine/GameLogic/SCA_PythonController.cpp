/**
 * Execute Python scripts
 *
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

#include "SCA_PythonController.h"
#include "SCA_LogicManager.h"
#include "SCA_ISensor.h"
#include "SCA_IActuator.h"
#include "PyObjectPlus.h"
#include "compile.h"
#include "eval.h"
#include <algorithm>


#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

// initialize static member variables
SCA_PythonController* SCA_PythonController::m_sCurrentController = NULL;


SCA_PythonController::SCA_PythonController(SCA_IObject* gameobj,
										   PyTypeObject* T)
	: SCA_IController(gameobj, T),
	m_bytecode(NULL),
	m_bModified(true),
	m_pythondictionary(NULL)
{
}

/*
//debugging
CValue*		SCA_PythonController::AddRef()
{
	//printf("AddRef refcount = %i\n",GetRefCount());
	return CValue::AddRef();
}
int			SCA_PythonController::Release()
{
	//printf("Release refcount = %i\n",GetRefCount());
	return CValue::Release();
}
*/



SCA_PythonController::~SCA_PythonController()
{
	if (m_bytecode)
	{
		//
		//printf("released python byte script\n");
		Py_DECREF(m_bytecode);
	}
	
	if (m_pythondictionary)
	{
		// break any circular references in the dictionary
		PyDict_Clear(m_pythondictionary);
		Py_DECREF(m_pythondictionary);
	}
}



CValue* SCA_PythonController::GetReplica()
{
	SCA_PythonController* replica = new SCA_PythonController(*this);
	// Copy the compiled bytecode if possible.
	Py_XINCREF(replica->m_bytecode);
	replica->m_bModified = replica->m_bytecode == NULL;
	
	// The replica->m_pythondictionary is stolen - replace with a copy.
	if (m_pythondictionary)
		replica->m_pythondictionary = PyDict_Copy(m_pythondictionary);
		
	/*
	// The other option is to incref the replica->m_pythondictionary -
	// the replica objects can then share data.
	if (m_pythondictionary)
		Py_INCREF(replica->m_pythondictionary);
	*/
	
	// this will copy properties and so on...
	replica->ProcessReplica();

	return replica;
}



void SCA_PythonController::SetScriptText(const STR_String& text)
{ 
	m_scriptText = text;
	m_bModified = true;
}



void SCA_PythonController::SetScriptName(const STR_String& name)
{
	m_scriptName = name;
}



void SCA_PythonController::SetDictionary(PyObject*	pythondictionary)
{
	if (m_pythondictionary)
	{
		PyDict_Clear(m_pythondictionary);
		Py_DECREF(m_pythondictionary);
	}
	m_pythondictionary = PyDict_Copy(pythondictionary); /* new reference */
}

int SCA_PythonController::IsTriggered(class SCA_ISensor* sensor)
{
	if (std::find(m_triggeredSensors.begin(), m_triggeredSensors.end(), sensor) != 
		m_triggeredSensors.end())
		return 1;
	return 0;
}

#if 0
static const char* sPyGetCurrentController__doc__;
#endif

/* warning, self is not the SCA_PythonController, its a PyObjectPlus_Proxy */
PyObject* SCA_PythonController::sPyGetCurrentController(PyObject *self)
{
	return m_sCurrentController->GetProxy();
}

SCA_IActuator* SCA_PythonController::LinkedActuatorFromPy(PyObject *value)
{
	// for safety, todo: only allow for registered actuators (pointertable)
	// we don't want to crash gameengine/blender by python scripts
	std::vector<SCA_IActuator*> lacts =  m_sCurrentController->GetLinkedActuators();
	std::vector<SCA_IActuator*>::iterator it;
	
	if (PyString_Check(value)) {
		/* get the actuator from the name */
		char *name= PyString_AsString(value);
		for(it = lacts.begin(); it!= lacts.end(); it++) {
			if( name == (*it)->GetName() ) {
				return *it;
			}
		}
	}
	else if (BGE_PROXY_CHECK_TYPE(value)) {
		PyObjectPlus *value_plus= BGE_PROXY_REF(value); /* Expecting an actuator type */ // XXX TODO - CHECK TYPE
		for(it = lacts.begin(); it!= lacts.end(); it++) {
			if( static_cast<SCA_IActuator*>(value_plus) == (*it) ) {
				return *it;
			}
		}
	}
	
	/* set the exception */
	PyObject *value_str = PyObject_Repr(value); /* new ref */
	PyErr_Format(PyExc_ValueError, "'%s' not in this python controllers actuator list", PyString_AsString(value_str));
	Py_DECREF(value_str);
	
	return false;
}

#if 0
static const char* sPyAddActiveActuator__doc__;
#endif

/* warning, self is not the SCA_PythonController, its a PyObjectPlus_Proxy */
PyObject* SCA_PythonController::sPyAddActiveActuator(PyObject* self, PyObject* args)
{
	PyObject* ob1;
	int activate;
	if (!PyArg_ParseTuple(args, "Oi:addActiveActuator", &ob1,&activate))
		return NULL;
	
	SCA_IActuator* actu = LinkedActuatorFromPy(ob1);
	if(actu==NULL)
		return NULL;
	
	CValue* boolval = new CBoolValue(activate!=0);
	m_sCurrentLogicManager->AddActiveActuator((SCA_IActuator*)actu,boolval);
	boolval->Release();
	Py_RETURN_NONE;
}


const char* SCA_PythonController::sPyGetCurrentController__doc__ = "getCurrentController()";
const char* SCA_PythonController::sPyAddActiveActuator__doc__= "addActiveActuator(actuator,bool)";
const char SCA_PythonController::GetActuators_doc[] = "getActuator";

PyTypeObject SCA_PythonController::Type = {
	PyObject_HEAD_INIT(NULL)
		0,
		"SCA_PythonController",
		sizeof(PyObjectPlus_Proxy),
		0,
		py_base_dealloc,
		0,
		0,
		0,
		0,
		py_base_repr,
		0,0,0,0,0,0,
		py_base_getattro,
		py_base_setattro,
		0,0,0,0,0,0,0,0,0,
		Methods
};

PyParentObject SCA_PythonController::Parents[] = {
	&SCA_PythonController::Type,
	&SCA_IController::Type,
	&CValue::Type,
	NULL
};
PyMethodDef SCA_PythonController::Methods[] = {
	{"activate", (PyCFunction) SCA_PythonController::sPyActivate, METH_O},
	{"deactivate", (PyCFunction) SCA_PythonController::sPyDeActivate, METH_O},
	
	{"getActuators", (PyCFunction) SCA_PythonController::sPyGetActuators, METH_NOARGS, (PY_METHODCHAR)SCA_PythonController::GetActuators_doc},
	{"getActuator", (PyCFunction) SCA_PythonController::sPyGetActuator, METH_O, (PY_METHODCHAR)SCA_PythonController::GetActuator_doc},
	{"getSensors", (PyCFunction) SCA_PythonController::sPyGetSensors, METH_NOARGS, (PY_METHODCHAR)SCA_PythonController::GetSensors_doc},
	{"getSensor", (PyCFunction) SCA_PythonController::sPyGetSensor, METH_O, (PY_METHODCHAR)SCA_PythonController::GetSensor_doc},
	//Deprecated functions ------>
	{"setScript", (PyCFunction) SCA_PythonController::sPySetScript, METH_O},
	{"getScript", (PyCFunction) SCA_PythonController::sPyGetScript, METH_NOARGS},
	{"getState", (PyCFunction) SCA_PythonController::sPyGetState, METH_NOARGS},
	//<----- Deprecated
	{NULL,NULL} //Sentinel
};

PyAttributeDef SCA_PythonController::Attributes[] = {
	KX_PYATTRIBUTE_RO_FUNCTION("state", SCA_PythonController, pyattr_get_state),
	KX_PYATTRIBUTE_RW_FUNCTION("script", SCA_PythonController, pyattr_get_script, pyattr_set_script),
	{ NULL }	//Sentinel
};

bool SCA_PythonController::Compile()
{
	//printf("py script modified '%s'\n", m_scriptName.Ptr());
	
	// if a script already exists, decref it before replace the pointer to a new script
	if (m_bytecode)
	{
		Py_DECREF(m_bytecode);
		m_bytecode=NULL;
	}
	// recompile the scripttext into bytecode
	m_bytecode = Py_CompileString(m_scriptText.Ptr(), m_scriptName.Ptr(), Py_file_input);
	m_bModified=false;
	
	if (m_bytecode)
	{
		
		return true;
	}
	else {
		// didn't compile, so instead of compile, complain
		// something is wrong, tell the user what went wrong
		printf("Python compile error from controller \"%s\": \n", GetName().Ptr());
		//PyRun_SimpleString(m_scriptText.Ptr());
		PyErr_Print();
		
		/* Added in 2.48a, the last_traceback can reference Objects for example, increasing
		 * their user count. Not to mention holding references to wrapped data.
		 * This is especially bad when the PyObject for the wrapped data is free'd, after blender 
		 * has alredy dealocated the pointer */
		PySys_SetObject( (char *)"last_traceback", NULL);
		PyErr_Clear(); /* just to be sure */
		
		return false;
	}
}

void SCA_PythonController::Trigger(SCA_LogicManager* logicmgr)
{
	m_sCurrentController = this;
	m_sCurrentLogicManager = logicmgr;
	
	if (m_bModified)
	{
		if (Compile()==false) // sets m_bModified to false
			return;
	}
	if (!m_bytecode) {
		return;
	}
		
	
		/*
		 * This part here with excdict is a temporary patch
		 * to avoid python/gameengine crashes when python
		 * inadvertently holds references to game objects
		 * in global variables.
		 * 
		 * The idea is always make a fresh dictionary, and
		 * destroy it right after it is used to make sure
		 * python won't hold any gameobject references.
		 * 
		 * Note that the PyDict_Clear _is_ necessary before
		 * the Py_DECREF() because it is possible for the
		 * variables inside the dictionary to hold references
		 * to the dictionary (ie. generate a cycle), so we
		 * break it by hand, then DECREF (which in this case
		 * should always ensure excdict is cleared).
		 */

	PyObject *excdict= PyDict_Copy(m_pythondictionary);
	PyObject* resultobj = PyEval_EvalCode((PyCodeObject*)m_bytecode,
		excdict, excdict);

	if (resultobj)
	{
		Py_DECREF(resultobj);
	}
	else
	{
		// something is wrong, tell the user what went wrong
		printf("Python script error from controller \"%s\": \n", GetName().Ptr());
		PyErr_Print();
		
		/* Added in 2.48a, the last_traceback can reference Objects for example, increasing
		 * their user count. Not to mention holding references to wrapped data.
		 * This is especially bad when the PyObject for the wrapped data is free'd, after blender 
		 * has alredy dealocated the pointer */
		PySys_SetObject( (char *)"last_traceback", NULL);
		PyErr_Clear(); /* just to be sure */
		
		//PyRun_SimpleString(m_scriptText.Ptr());
	}

	// clear after PyErrPrint - seems it can be using
	// something in this dictionary and crash?
	PyDict_Clear(excdict);
	Py_DECREF(excdict);
	m_triggeredSensors.erase(m_triggeredSensors.begin(), m_triggeredSensors.end());
	m_sCurrentController = NULL;
}



PyObject* SCA_PythonController::py_getattro(PyObject *attr)
{
	py_getattro_up(SCA_IController);
}

int SCA_PythonController::py_setattro(PyObject *attr, PyObject *value)
{
	py_setattro_up(SCA_IController);
}

PyObject* SCA_PythonController::PyActivate(PyObject *value)
{
	SCA_IActuator* actu = LinkedActuatorFromPy(value);
	if(actu==NULL)
		return NULL;
	
	CValue* boolval = new CBoolValue(true);
	m_sCurrentLogicManager->AddActiveActuator((SCA_IActuator*)actu, boolval);
	boolval->Release();
	Py_RETURN_NONE;
}

PyObject* SCA_PythonController::PyDeActivate(PyObject *value)
{
	SCA_IActuator* actu = LinkedActuatorFromPy(value);
	if(actu==NULL)
		return NULL;
	
	CValue* boolval = new CBoolValue(false);
	m_sCurrentLogicManager->AddActiveActuator((SCA_IActuator*)actu, boolval);
	boolval->Release();
	Py_RETURN_NONE;
}

PyObject* SCA_PythonController::PyGetActuators()
{
	PyObject* resultlist = PyList_New(m_linkedactuators.size());
	for (unsigned int index=0;index<m_linkedactuators.size();index++)
	{
		PyList_SET_ITEM(resultlist,index, m_linkedactuators[index]->GetProxy());
	}

	return resultlist;
}

const char SCA_PythonController::GetSensor_doc[] = 
"getSensor (char sensorname) return linked sensor that is named [sensorname]\n";
PyObject*
SCA_PythonController::PyGetSensor(PyObject* value)
{

	char *scriptArg = PyString_AsString(value);
	if (scriptArg==NULL) {
		PyErr_SetString(PyExc_TypeError, "controller.getSensor(string): Python Controller, expected a string (sensor name)");
		return NULL;
	}
	
	for (unsigned int index=0;index<m_linkedsensors.size();index++)
	{
		SCA_ISensor* sensor = m_linkedsensors[index];
		STR_String realname = sensor->GetName();
		if (realname == scriptArg)
		{
			return sensor->GetProxy();
		}
	}
	
	PyErr_Format(PyExc_AttributeError, "controller.getSensor(string): Python Controller, unable to find requested sensor \"%s\"", scriptArg);
	return NULL;
}



const char SCA_PythonController::GetActuator_doc[] = 
"getActuator (char sensorname) return linked actuator that is named [actuatorname]\n";
PyObject*
SCA_PythonController::PyGetActuator(PyObject* value)
{

	char *scriptArg = PyString_AsString(value);
	if (scriptArg==NULL) {
		PyErr_SetString(PyExc_TypeError, "controller.getActuator(string): Python Controller, expected a string (actuator name)");
		return NULL;
	}
	
	for (unsigned int index=0;index<m_linkedactuators.size();index++)
	{
		SCA_IActuator* actua = m_linkedactuators[index];
		if (actua->GetName() == scriptArg)
		{
			return actua->GetProxy();
		}
	}
	
	PyErr_Format(PyExc_AttributeError, "controller.getActuator(string): Python Controller, unable to find requested actuator \"%s\"", scriptArg);
	return NULL;
}


const char SCA_PythonController::GetSensors_doc[]   = "getSensors returns a list of all attached sensors";
PyObject*
SCA_PythonController::PyGetSensors()
{
	PyObject* resultlist = PyList_New(m_linkedsensors.size());
	for (unsigned int index=0;index<m_linkedsensors.size();index++)
	{
		PyList_SET_ITEM(resultlist,index, m_linkedsensors[index]->GetProxy());
	}
	
	return resultlist;
}

/* 1. getScript */
PyObject* SCA_PythonController::PyGetScript()
{
	ShowDeprecationWarning("getScript()", "the script property");
	return PyString_FromString(m_scriptText);
}

/* 2. setScript */
PyObject* SCA_PythonController::PySetScript(PyObject* value)
{
	char *scriptArg = PyString_AsString(value);
	
	ShowDeprecationWarning("setScript()", "the script property");
	
	if (scriptArg==NULL) {
		PyErr_SetString(PyExc_TypeError, "expected a string (script name)");
		return NULL;
	}
	
	/* set scripttext sets m_bModified to true, 
		so next time the script is needed, a reparse into byte code is done */

	this->SetScriptText(scriptArg);
	
	Py_RETURN_NONE;
}

/* 1. getScript */
PyObject* SCA_PythonController::PyGetState()
{
	ShowDeprecationWarning("getState()", "the state property");
	return PyInt_FromLong(m_statemask);
}

PyObject* SCA_PythonController::pyattr_get_state(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	SCA_PythonController* self= static_cast<SCA_PythonController*>(self_v);
	return PyInt_FromLong(self->m_statemask);
}

PyObject* SCA_PythonController::pyattr_get_script(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	SCA_PythonController* self= static_cast<SCA_PythonController*>(self_v);
	return PyString_FromString(self->m_scriptText);
}

int SCA_PythonController::pyattr_set_script(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	SCA_PythonController* self= static_cast<SCA_PythonController*>(self_v);
	
	char *scriptArg = PyString_AsString(value);
	
	if (scriptArg==NULL) {
		PyErr_SetString(PyExc_TypeError, "controller.script = string: Python Controller, expected a string script text");
		return -1;
	}

	/* set scripttext sets m_bModified to true, 
		so next time the script is needed, a reparse into byte code is done */
	self->SetScriptText(scriptArg);
		
	return 0;
}


/* eof */
