/**
 * Abstract class for sensor logic bricks
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

#include "SCA_ISensor.h"
#include "SCA_EventManager.h"
#include "SCA_LogicManager.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* Native functions */
void	SCA_ISensor::ReParent(SCA_IObject* parent)
{
	SCA_ILogicBrick::ReParent(parent);
	m_eventmgr->RegisterSensor(this);
	this->SetActive(false);
}


SCA_ISensor::SCA_ISensor(SCA_IObject* gameobj,
						 class SCA_EventManager* eventmgr,
						 PyTypeObject* T ) :
	SCA_ILogicBrick(gameobj,T),
	m_triggered(false)
{
	m_suspended = false;
	m_invert = false;
	m_pos_ticks = 0;
	m_neg_ticks = 0;
	m_pos_pulsemode = false;
	m_neg_pulsemode = false;
	m_pulse_frequency = 0;
	
	m_eventmgr = eventmgr;
}


SCA_ISensor::~SCA_ISensor()  
{
	// intentionally empty
}

bool SCA_ISensor::IsPositiveTrigger() { 
	bool result = false;
	
	if (m_eventval) {
		result = (m_eventval->GetNumber() != 0.0);
	}
	if (m_invert) {
		result = !result;
	}
	
	return result;
}

void SCA_ISensor::SetPulseMode(bool posmode, 
							   bool negmode,
							   int freq) {
	m_pos_pulsemode = posmode;
	m_neg_pulsemode = negmode;
	m_pulse_frequency = freq;
}

void SCA_ISensor::SetInvert(bool inv) {
	m_invert = inv;
}


float SCA_ISensor::GetNumber() {
	return IsPositiveTrigger();
}

void SCA_ISensor::Suspend() {
	m_suspended = true;
}

bool SCA_ISensor::IsSuspended() {
	return m_suspended;
}

void SCA_ISensor::Resume() {
	m_suspended = false;
}

/* python integration */

PyTypeObject SCA_ISensor::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"SCA_ISensor",
	sizeof(SCA_ISensor),
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

PyParentObject SCA_ISensor::Parents[] = {
	&SCA_ISensor::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};
PyMethodDef SCA_ISensor::Methods[] = {
	{"isPositive", (PyCFunction) SCA_ISensor::sPyIsPositive, 
	 METH_VARARGS, IsPositive_doc},
	{"getUsePosPulseMode", (PyCFunction) SCA_ISensor::sPyGetUsePosPulseMode, 
	 METH_VARARGS, GetUsePosPulseMode_doc},
	{"setUsePosPulseMode", (PyCFunction) SCA_ISensor::sPySetUsePosPulseMode, 
	 METH_VARARGS, SetUsePosPulseMode_doc},
	{"getFrequency", (PyCFunction) SCA_ISensor::sPyGetFrequency, 
	 METH_VARARGS, GetFrequency_doc},
	{"setFrequency", (PyCFunction) SCA_ISensor::sPySetFrequency, 
	 METH_VARARGS, SetFrequency_doc},
	{"getUseNegPulseMode", (PyCFunction) SCA_ISensor::sPyGetUseNegPulseMode, 
	 METH_VARARGS, GetUseNegPulseMode_doc},
	{"setUseNegPulseMode", (PyCFunction) SCA_ISensor::sPySetUseNegPulseMode, 
	 METH_VARARGS, SetUseNegPulseMode_doc},
	{"getInvert", (PyCFunction) SCA_ISensor::sPyGetInvert, 
	 METH_VARARGS, GetInvert_doc},
	{"setInvert", (PyCFunction) SCA_ISensor::sPySetInvert, 
	 METH_VARARGS, SetInvert_doc},
	{NULL,NULL} //Sentinel
};


PyObject*
SCA_ISensor::_getattr(char* attr)
{
  _getattr_up(SCA_ILogicBrick);
}


void SCA_ISensor::RegisterToManager()
{
	m_eventmgr->RegisterSensor(this);
}

void SCA_ISensor::Activate(class SCA_LogicManager* logicmgr,	  CValue* event)
{
	
	// calculate if a __triggering__ is wanted
	if (!m_suspended) {
		bool result = this->Evaluate(event);
		if (result) {
			logicmgr->AddActivatedSensor(this);	
		} else
		{
			/* First, the pulsing behaviour, if pulse mode is
			 * active. It seems something goes wrong if pulse mode is
			 * not set :( */
			if (m_pos_pulsemode) {
				m_pos_ticks++;
				if (m_pos_ticks > m_pulse_frequency) {
					if ( this->IsPositiveTrigger() )
					{
						logicmgr->AddActivatedSensor(this);
					}
					m_pos_ticks = 0;
				} 
			}
			
			if (m_neg_pulsemode)
			{
				m_neg_ticks++;
				if (m_neg_ticks > m_pulse_frequency) {
					if (!this->IsPositiveTrigger() )
					{
						logicmgr->AddActivatedSensor(this);
					}
					m_neg_ticks = 0;
				}
			}
		}
	} 
}

/* Python functions: */
char SCA_ISensor::IsPositive_doc[] = 
"isPositive()\n"
"\tReturns whether the sensor is registered a positive event.\n";
PyObject* SCA_ISensor::PyIsPositive(PyObject* self, PyObject* args, PyObject* kwds)
{
	int retval = IsPositiveTrigger();
	return PyInt_FromLong(retval);
}

/**
 * getUsePulseMode: getter for the pulse mode (KX_TRUE = on)
 */
char SCA_ISensor::GetUsePosPulseMode_doc[] = 
"getUsePosPulseMode()\n"
"\tReturns whether positive pulse mode is active.\n";
PyObject* SCA_ISensor::PyGetUsePosPulseMode(PyObject* self, PyObject* args, PyObject* kwds)
{
	return BoolToPyArg(m_pos_pulsemode);
}

/**
 * setUsePulseMode: setter for the pulse mode (KX_TRUE = on)
 */
char SCA_ISensor::SetUsePosPulseMode_doc[] = 
"setUsePosPulseMode(pulse?)\n"
"\t - pulse? : Pulse when a positive event occurs?\n"
"\t            (KX_TRUE, KX_FALSE)\n"
"\tSet whether to do pulsing when positive pulses occur.\n";
PyObject* SCA_ISensor::PySetUsePosPulseMode(PyObject* self, PyObject* args, PyObject* kwds)
{
	int pyarg = 0;
	if(!PyArg_ParseTuple(args, "i", &pyarg)) { return NULL; }
	m_pos_pulsemode = PyArgToBool(pyarg);
	Py_Return;
}

/**
 * getFrequency: getter for the pulse mode interval
 */
char SCA_ISensor::GetFrequency_doc[] = 
"getFrequency()\n"
"\tReturns the frequency of the updates in pulse mode.\n" ;
PyObject* SCA_ISensor::PyGetFrequency(PyObject* self, PyObject* args, PyObject* kwds)
{
	return PyInt_FromLong(m_pulse_frequency);
}

/**
 * setFrequency: setter for the pulse mode (KX_TRUE = on)
 */
char SCA_ISensor::SetFrequency_doc[] = 
"setFrequency(pulse_frequency)\n"
"\t- pulse_frequency: The frequency of the updates in pulse mode (integer)"
"\tSet the frequency of the updates in pulse mode.\n"
"\tIf the frequency is negative, it is set to 0.\n" ;
PyObject* SCA_ISensor::PySetFrequency(PyObject* self, PyObject* args, PyObject* kwds)
{
	int pulse_frequencyArg = 0;

	if(!PyArg_ParseTuple(args, "i", &pulse_frequencyArg)) {
		return NULL;
	}
	
	/* We can do three things here: clip, ignore and raise an exception.  */
	/* Exceptions don't work yet, ignoring is not desirable now...        */
	if (pulse_frequencyArg < 0) {
		pulse_frequencyArg = 0;
	};	
	m_pulse_frequency = pulse_frequencyArg;

	Py_Return;
}


char SCA_ISensor::GetInvert_doc[] = 
"getInvert()\n"
"\tReturns whether or not pulses from this sensor are inverted.\n" ;
PyObject* SCA_ISensor::PyGetInvert(PyObject* self, PyObject* args, PyObject* kwds)
{
	return BoolToPyArg(m_invert);
}

char SCA_ISensor::SetInvert_doc[] = 
"setInvert(invert?)\n"
"\t- invert?: Invert the event-values? (KX_TRUE, KX_FALSE)\n"
"\tSet whether to invert pulses.\n";
PyObject* SCA_ISensor::PySetInvert(PyObject* self, PyObject* args, PyObject* kwds)
{
	int pyarg = 0;
	if(!PyArg_ParseTuple(args, "i", &pyarg)) { return NULL; }
	m_invert = PyArgToBool(pyarg);
	Py_Return;
}

char SCA_ISensor::GetUseNegPulseMode_doc[] = 
"getUseNegPulseMode()\n"
"\tReturns whether negative pulse mode is active.\n";
PyObject* SCA_ISensor::PyGetUseNegPulseMode(PyObject* self, PyObject* args, PyObject* kwds)
{
	return BoolToPyArg(m_neg_pulsemode);
}

char SCA_ISensor::SetUseNegPulseMode_doc[] = 
"setUseNegPulseMode(pulse?)\n"
"\t - pulse? : Pulse when a negative event occurs?\n"
"\t            (KX_TRUE, KX_FALSE)\n"
"\tSet whether to do pulsing when negative pulses occur.\n";
PyObject* SCA_ISensor::PySetUseNegPulseMode(PyObject* self, PyObject* args, PyObject* kwds)
{
	int pyarg = 0;
	if(!PyArg_ParseTuple(args, "i", &pyarg)) { return NULL; }
	m_neg_pulsemode = PyArgToBool(pyarg);
	Py_Return;
}

/* eof */
