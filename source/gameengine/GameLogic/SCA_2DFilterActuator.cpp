/**
 * SCA_2DFilterActuator.cpp
 *
 * $Id: SCA_2DFilterActuator.cpp 19790 2009-04-19 14:57:52Z campbellbarton $
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
 *
 * ***** END GPL LICENSE BLOCK *****
 */

#include "SCA_IActuator.h"
#include "SCA_2DFilterActuator.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif
#include <iostream>

SCA_2DFilterActuator::~SCA_2DFilterActuator()
{
}

SCA_2DFilterActuator::SCA_2DFilterActuator(
        SCA_IObject *gameobj, 
        RAS_2DFilterManager::RAS_2DFILTER_MODE type,
		short flag,
		float float_arg,
		int int_arg,
		RAS_IRasterizer* rasterizer,
		RAS_IRenderTools* rendertools,
        PyTypeObject* T)
    : SCA_IActuator(gameobj, T),
     m_type(type),
	 m_disableMotionBlur(flag),
	 m_float_arg(float_arg),
	 m_int_arg(int_arg),
	 m_rasterizer(rasterizer),
	 m_rendertools(rendertools)
{
	m_gameObj = NULL;
	if(gameobj){
		m_propNames = gameobj->GetPropertyNames();
		m_gameObj = gameobj;
	}
}


CValue* SCA_2DFilterActuator::GetReplica()
{
    SCA_2DFilterActuator* replica = new SCA_2DFilterActuator(*this);
    replica->ProcessReplica();
    CValue::AddDataToReplica(replica);

    return replica;
}


bool SCA_2DFilterActuator::Update()
{
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();


	if (bNegativeEvent)
		return false; // do nothing on negative events

	if( m_type == RAS_2DFilterManager::RAS_2DFILTER_MOTIONBLUR )
	{
		if(!m_disableMotionBlur)
			m_rasterizer->EnableMotionBlur(m_float_arg);
		else
			m_rasterizer->DisableMotionBlur();

		return false;
	}
	else if(m_type < RAS_2DFilterManager::RAS_2DFILTER_NUMBER_OF_FILTERS)
	{
		m_rendertools->Update2DFilter(m_propNames, m_gameObj, m_type, m_int_arg, m_shaderText);
	}
	// once the filter is in place, no need to update it again => disable the actuator
    return false;
}


void SCA_2DFilterActuator::SetShaderText(STR_String text)
{
	m_shaderText = text;
}

/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */



/* Integration hooks ------------------------------------------------------- */
PyTypeObject SCA_2DFilterActuator::Type = {
        PyObject_HEAD_INIT(NULL)
        0,
        "SCA_2DFilterActuator",
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


PyParentObject SCA_2DFilterActuator::Parents[] = {
        &SCA_2DFilterActuator::Type,
        &SCA_IActuator::Type,
        &SCA_ILogicBrick::Type,
        &CValue::Type,
        NULL
};


PyMethodDef SCA_2DFilterActuator::Methods[] = {
	/* add python functions to deal with m_msg... */
    {NULL,NULL}
};

PyAttributeDef SCA_2DFilterActuator::Attributes[] = {
	KX_PYATTRIBUTE_STRING_RW("shaderText", 0, 64000, false, SCA_2DFilterActuator, m_shaderText),
	KX_PYATTRIBUTE_SHORT_RW("disableMotionBlur", 0, 1, true, SCA_2DFilterActuator, m_disableMotionBlur),
	KX_PYATTRIBUTE_ENUM_RW("type",RAS_2DFilterManager::RAS_2DFILTER_ENABLED,RAS_2DFilterManager::RAS_2DFILTER_NUMBER_OF_FILTERS,false,SCA_2DFilterActuator,m_type),
	KX_PYATTRIBUTE_INT_RW("passNb", 0, 100, true, SCA_2DFilterActuator, m_int_arg),
	KX_PYATTRIBUTE_FLOAT_RW("value", 0.0, 100.0, SCA_2DFilterActuator, m_float_arg),
	{ NULL }	//Sentinel
};

PyObject* SCA_2DFilterActuator::py_getattro(PyObject *attr) 
{
    py_getattro_up(SCA_IActuator);
}

int SCA_2DFilterActuator::py_setattro(PyObject *attr, PyObject* value) 
{
	py_setattro_up(SCA_IActuator);
}

