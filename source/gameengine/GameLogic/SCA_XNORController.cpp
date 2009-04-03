/**
 * 'Xnor' together all inputs
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

#include "SCA_XNORController.h"
#include "SCA_ISensor.h"
#include "SCA_LogicManager.h"
#include "BoolValue.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

SCA_XNORController::SCA_XNORController(SCA_IObject* gameobj,
									 PyTypeObject* T)
	:
	SCA_IController(gameobj,T)
{
}



SCA_XNORController::~SCA_XNORController()
{
}



void SCA_XNORController::Trigger(SCA_LogicManager* logicmgr)
{

	bool sensorresult = true;

	for (vector<SCA_ISensor*>::const_iterator is=m_linkedsensors.begin();
	!(is==m_linkedsensors.end());is++)
	{
		SCA_ISensor* sensor = *is;
		if (sensor->IsPositiveTrigger())
		{
			if (sensorresult == false)
			{
				sensorresult = true;
				break;
			}
			sensorresult = false;
		}
	}

	CValue* newevent = new CBoolValue(sensorresult);

	for (vector<SCA_IActuator*>::const_iterator i=m_linkedactuators.begin();
	!(i==m_linkedactuators.end());i++)
	{
		SCA_IActuator* actua = *i;//m_linkedactuators.at(i);
		logicmgr->AddActiveActuator(actua,newevent);
	}

	// every actuator that needs the event, has a it's own reference to it now so
	// release it (so to be clear: if there is no actuator, it's deleted right now)
	newevent->Release();

}



CValue* SCA_XNORController::GetReplica()
{
	CValue* replica = new SCA_XNORController(*this);
	// this will copy properties and so on...
	CValue::AddDataToReplica(replica);

	return replica;
}



/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject SCA_XNORController::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"SCA_XNORController",
	sizeof(SCA_XNORController),
	0,
	PyDestructor,
	0,
	__getattr,
	__setattr,
	0,
	__repr,
	0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,
	Methods
};

PyParentObject SCA_XNORController::Parents[] = {
	&SCA_XNORController::Type,
	&SCA_IController::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};

PyMethodDef SCA_XNORController::Methods[] = {
	{NULL,NULL} //Sentinel
};

PyAttributeDef SCA_XNORController::Attributes[] = {
	{ NULL }	//Sentinel
};

PyObject* SCA_XNORController::_getattr(const char *attr) {
	_getattr_up(SCA_IController);
}

/* eof */
