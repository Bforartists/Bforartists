/**
 * $Id$
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


#include "SCA_IObject.h"
#include "SCA_ISensor.h"
#include "SCA_IController.h"
#include "SCA_IActuator.h"
#include "MT_Point3.h"

#include "ListValue.h"

MT_Point3 SCA_IObject::m_sDummy=MT_Point3(0,0,0);

SCA_IObject::SCA_IObject(PyTypeObject* T): CValue(T)
{
	m_suspended = false;
}
	


SCA_IObject::~SCA_IObject()
{
	SCA_SensorList::iterator its;
	for (its = m_sensors.begin(); !(its == m_sensors.end()); ++its)
	{
		((CValue*)(*its))->Release();
	}
	SCA_ControllerList::iterator itc; 
	for (itc = m_controllers.begin(); !(itc == m_controllers.end()); ++itc)
	{
		((CValue*)(*itc))->Release();
	}
	SCA_ActuatorList::iterator ita;
	for (ita = m_actuators.begin(); !(ita==m_actuators.end()); ++ita)
	{
		((CValue*)(*ita))->Release();
	}

	//T_InterpolatorList::iterator i;
	//for (i = m_interpolators.begin(); !(i == m_interpolators.end()); ++i) {
	//	delete *i;
	//}
}



SCA_ControllerList& SCA_IObject::GetControllers()
{
	return m_controllers;
}



SCA_SensorList& SCA_IObject::GetSensors()
{
	return m_sensors;
}



SCA_ActuatorList& SCA_IObject::GetActuators()
{
	return m_actuators;
}



void SCA_IObject::AddSensor(SCA_ISensor* act)
{
	m_sensors.push_back(act);
}



void SCA_IObject::AddController(SCA_IController* act)
{
	m_controllers.push_back(act);
}



void SCA_IObject::AddActuator(SCA_IActuator* act)
{
	m_actuators.push_back(act);
}



void SCA_IObject::SetIgnoreActivityCulling(bool b)
{
	m_ignore_activity_culling = b;
}



bool SCA_IObject::GetIgnoreActivityCulling()
{
	return m_ignore_activity_culling;
}



void SCA_IObject::ReParentLogic()
{
	SCA_SensorList& oldsensors = GetSensors();
	
	int sen = 0;
	SCA_SensorList::iterator its;
	for (its = oldsensors.begin(); !(its==oldsensors.end()); ++its)
	{
		SCA_ISensor* newsensor = (SCA_ISensor*)(*its)->GetReplica();
		newsensor->ReParent(this);
		oldsensors[sen++] = newsensor;
	}

	SCA_ControllerList& oldcontrollers = GetControllers();
	int con = 0;
	SCA_ControllerList::iterator itc;
	for (itc = oldcontrollers.begin(); !(itc==oldcontrollers.end()); ++itc)
	{
		SCA_IController* newcontroller = (SCA_IController*)(*itc)->GetReplica();
		newcontroller->ReParent(this);
		oldcontrollers[con++]=newcontroller;

	}
	SCA_ActuatorList& oldactuators  = GetActuators();
	
	int act = 0;
	SCA_ActuatorList::iterator ita;
	for (ita = oldactuators.begin(); !(ita==oldactuators.end()); ++ita)
	{
		SCA_IActuator* newactuator = (SCA_IActuator*) (*ita)->GetReplica();
		newactuator->ReParent(this);
		newactuator->SetActive(false);
		oldactuators[act++] = newactuator;
	}
		
}



SCA_ISensor* SCA_IObject::FindSensor(const STR_String& sensorname)
{
	SCA_ISensor* foundsensor = NULL;

	for (SCA_SensorList::iterator its = m_sensors.begin();!(its==m_sensors.end());its++)
	{
		if ((*its)->GetName() == sensorname)
		{
			foundsensor = (*its);
			break;
		}
	}
	return foundsensor;
}



SCA_IController* SCA_IObject::FindController(const STR_String& controllername)
{
	SCA_IController* foundcontroller = NULL;

	for (SCA_ControllerList::iterator itc = m_controllers.begin();!(itc==m_controllers.end());itc++)
	{
		if ((*itc)->GetName() == controllername)
		{
			foundcontroller = (*itc);
			break;
		}	
	}
	return foundcontroller;
}



SCA_IActuator* SCA_IObject::FindActuator(const STR_String& actuatorname)
{
	SCA_IActuator* foundactuator = NULL;

	for (SCA_ActuatorList::iterator ita = m_actuators.begin();!(ita==m_actuators.end());ita++)
	{
		if ((*ita)->GetName() == actuatorname)
		{
			foundactuator = (*ita);
			break;
		}
	}

	return foundactuator;
}



void SCA_IObject::SetCurrentTime(float currentTime) {
	//T_InterpolatorList::iterator i;
	//for (i = m_interpolators.begin(); !(i == m_interpolators.end()); ++i) {
	//	(*i)->Execute(currentTime);
	//}
}
	


const MT_Point3& SCA_IObject::ConvertPythonPylist(PyObject* pylist)
{
	bool error = false;
	m_sDummy = MT_Vector3(0,0,0);
	if (pylist->ob_type == &CListValue::Type)
	{
		CListValue* listval = (CListValue*) pylist;
		int numelem = listval->GetCount();
		if ( numelem <= 3)
		{
			int index;
			for (index = 0;index<numelem;index++)
			{
				m_sDummy[index] = listval->GetValue(index)->GetNumber();
			}
		}	else
		{
			error = true;
		}
		
	} else
	{
		
		// assert the list is long enough...
		int numitems = PyList_Size(pylist);
		if (numitems <= 3)
		{
			int index;
			for (index=0;index<numitems;index++)
			{
				m_sDummy[index] = PyFloat_AsDouble(PyList_GetItem(pylist,index));
			}
		}
		else
		{
			error = true;
		}

	}
	return m_sDummy;
}



const MT_Point3& SCA_IObject::ConvertPythonVectorArg(PyObject* args)
{

	PyObject* pylist;
	PyArg_ParseTuple(args,"O",&pylist);
	m_sDummy = ConvertPythonPylist(pylist);
	return m_sDummy;
}



void SCA_IObject::Suspend(void)
{
	if ((!m_ignore_activity_culling) 
		&& (!m_suspended))  {
		m_suspended = true;
		/* flag suspend for all sensors */
		SCA_SensorList::iterator i = m_sensors.begin();
		while (i != m_sensors.end()) {
			(*i)->Suspend();
			i++;
		}
	}
}



void SCA_IObject::Resume(void)
{
	if (m_suspended) {
		m_suspended = false;
		/* unflag suspend for all sensors */
		SCA_SensorList::iterator i = m_sensors.begin();
		while (i != m_sensors.end()) {
			(*i)->Resume();
			i++;
		}
	}
}



/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject SCA_IObject::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"SCA_IObject",
	sizeof(SCA_IObject),
	0,
	PyDestructor,
	0,
	__getattr,
	__setattr,
	0, //&MyPyCompare,
	__repr,
	0, //&cvalue_as_number,
	0,
	0,
	0,
	0
};



PyParentObject SCA_IObject::Parents[] = {
	&SCA_IObject::Type,
	&CValue::Type,
	NULL
};



PyMethodDef SCA_IObject::Methods[] = {
	//{"setOrientation", (PyCFunction) SCA_IObject::sPySetOrientation, METH_VARARGS},
	//{"getOrientation", (PyCFunction) SCA_IObject::sPyGetOrientation, METH_VARARGS},
	{NULL,NULL} //Sentinel
};



PyObject* SCA_IObject::_getattr(char* attr) {
	_getattr_up(CValue);
}

