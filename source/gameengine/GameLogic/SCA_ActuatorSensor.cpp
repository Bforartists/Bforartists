/**
 * Actuator sensor
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

#include <iostream>
#include "SCA_ActuatorSensor.h"
#include "SCA_EventManager.h"
#include "SCA_LogicManager.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

SCA_ActuatorSensor::SCA_ActuatorSensor(SCA_EventManager* eventmgr,
									 SCA_IObject* gameobj,
									 const STR_String& actname,
									 PyTypeObject* T )
	: SCA_ISensor(gameobj,eventmgr,T),
	  m_checkactname(actname)
{
	m_actuator = GetParent()->FindActuator(m_checkactname);
	Init();
}

void SCA_ActuatorSensor::Init()
{
	m_lastresult = m_invert?true:false;
	m_midresult = m_lastresult;
	m_reset = true;
}

CValue* SCA_ActuatorSensor::GetReplica()
{
	SCA_ActuatorSensor* replica = new SCA_ActuatorSensor(*this);
	// m_range_expr must be recalculated on replica!
	replica->ProcessReplica();
	replica->Init();

	return replica;
}

void SCA_ActuatorSensor::ReParent(SCA_IObject* parent)
{
	m_actuator = parent->FindActuator(m_checkactname);
	SCA_ISensor::ReParent(parent);
}

bool SCA_ActuatorSensor::IsPositiveTrigger()
{
	bool result = m_lastresult;
	if (m_invert)
		result = !result;

	return result;
}



SCA_ActuatorSensor::~SCA_ActuatorSensor()
{
}



bool SCA_ActuatorSensor::Evaluate()
{
	if (m_actuator)
	{
		bool result = m_actuator->IsActive();
		bool reset = m_reset && m_level;
		
		m_reset = false;
		if (m_lastresult != result || m_midresult != result)
		{
			m_lastresult = m_midresult = result;
			return true;
		}
		return (reset) ? true : false;
	}
	return false;
}

void SCA_ActuatorSensor::Update()
{
	if (m_actuator)
	{
		m_midresult = m_actuator->IsActive() && !m_actuator->IsNegativeEvent();
	}
}


/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject SCA_ActuatorSensor::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"SCA_ActuatorSensor",
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

PyParentObject SCA_ActuatorSensor::Parents[] = {
	&SCA_ActuatorSensor::Type,
	&SCA_ISensor::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};

PyMethodDef SCA_ActuatorSensor::Methods[] = {
	//Deprecated functions ------>
	{"getActuator", (PyCFunction) SCA_ActuatorSensor::sPyGetActuator, METH_NOARGS, (PY_METHODCHAR)GetActuator_doc},
	{"setActuator", (PyCFunction) SCA_ActuatorSensor::sPySetActuator, METH_VARARGS, (PY_METHODCHAR)SetActuator_doc},
	//<----- Deprecated
	{NULL,NULL} //Sentinel
};

PyAttributeDef SCA_ActuatorSensor::Attributes[] = {
	KX_PYATTRIBUTE_STRING_RW_CHECK("actuator",0,100,false,SCA_ActuatorSensor,m_checkactname,CheckActuator),
	{ NULL }	//Sentinel
};

PyObject* SCA_ActuatorSensor::py_getattro(PyObject *attr) {
	py_getattro_up(SCA_ISensor);
}

PyObject* SCA_ActuatorSensor::py_getattro_dict() {
	py_getattro_dict_up(SCA_ISensor);
}

int SCA_ActuatorSensor::py_setattro(PyObject *attr, PyObject *value) {
	py_setattro_up(SCA_ISensor);
}

int SCA_ActuatorSensor::CheckActuator(void *self, const PyAttributeDef*)
{
	SCA_ActuatorSensor* sensor = reinterpret_cast<SCA_ActuatorSensor*>(self);
	SCA_IActuator* act = sensor->GetParent()->FindActuator(sensor->m_checkactname);
	if (act) {
		sensor->m_actuator = act;
		return 0;
	}
	PyErr_SetString(PyExc_AttributeError, "string does not correspond to an actuator");
	return 1;
}

/* 3. getActuator */
const char SCA_ActuatorSensor::GetActuator_doc[] = 
"getActuator()\n"
"\tReturn the Actuator with which the sensor operates.\n";
PyObject* SCA_ActuatorSensor::PyGetActuator() 
{
	ShowDeprecationWarning("getActuator()", "the actuator property");
	return PyString_FromString(m_checkactname);
}

/* 4. setActuator */
const char SCA_ActuatorSensor::SetActuator_doc[] = 
"setActuator(name)\n"
"\t- name: string\n"
"\tSets the Actuator with which to operate. If there is no Actuator\n"
"\tof this name, the call is ignored.\n";
PyObject* SCA_ActuatorSensor::PySetActuator(PyObject* args) 
{
	ShowDeprecationWarning("setActuator()", "the actuator property");
	/* We should query whether the name exists. Or should we create a prop   */
	/* on the fly?                                                           */
	char *actNameArg = NULL;

	if (!PyArg_ParseTuple(args, "s:setActuator", &actNameArg)) {
		return NULL;
	}

	SCA_IActuator* act = GetParent()->FindActuator(STR_String(actNameArg));
	if (act) {
		m_checkactname = actNameArg;
		m_actuator = act;
	} else {
		; /* error: bad actuator name */
	}
	Py_RETURN_NONE;
}

/* eof */
