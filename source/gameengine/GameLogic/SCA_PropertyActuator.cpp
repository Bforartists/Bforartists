/**
 * Assign, change, copy properties
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

#include "SCA_PropertyActuator.h"
#include "InputParser.h"
#include "Operator2Expr.h"
#include "ConstExpr.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

SCA_PropertyActuator::SCA_PropertyActuator(SCA_IObject* gameobj,CValue* sourceObj,const STR_String& propname,const STR_String& expr,int acttype,PyTypeObject* T )
   :	SCA_IActuator(gameobj,T),
	m_type(acttype),
	m_propname(propname),
	m_exprtxt(expr),
	m_sourceObj(sourceObj)
{
}

SCA_PropertyActuator::~SCA_PropertyActuator()
{
}

bool SCA_PropertyActuator::Update(double curtime,double deltatime)
{
	bool result = false;

	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();


	if (bNegativeEvent)
		return false; // do nothing on negative events


	CValue* propowner = GetParent();
	CParser parser;
	parser.SetContext( propowner->AddRef());
	
	CExpression* userexpr = parser.ProcessText(m_exprtxt);
	if (userexpr)
	{
		

		switch (m_type)
		{

		case KX_ACT_PROP_ASSIGN:
			{
				
				CValue* newval = userexpr->Calculate();
				CValue* oldprop = propowner->GetProperty(m_propname);
				if (oldprop)
				{
					oldprop->SetValue(newval);
					newval->Release();
				} else
				{
					propowner->SetProperty(m_propname,newval);
				}

				break;
			}
		case KX_ACT_PROP_ADD:
			{
				CValue* oldprop = propowner->GetProperty(m_propname);
				if (oldprop)
				{
					int waarde = (int)oldprop->GetNumber();
					CExpression* expr = new COperator2Expr(VALUE_ADD_OPERATOR,new CConstExpr(oldprop->AddRef()),
															userexpr->AddRef());

					CValue* newprop = expr->Calculate();
					oldprop->SetValue(newprop);
					newprop->Release();
					expr->Release();

				}

				break;
			}
		case KX_ACT_PROP_COPY:
			{
				if (m_sourceObj)
				{
					CValue* copyprop = m_sourceObj->GetProperty(m_exprtxt);
					if (copyprop)
					{
						GetParent()->SetProperty(
							 m_propname,
							copyprop->GetReplica());

					}
				}
				break;
			}
		default:
			{

			}
		}

		userexpr->Release();
	}
	
	return result;
}

	bool 

SCA_PropertyActuator::

isValid(

	SCA_PropertyActuator::KX_ACT_PROP_MODE mode

){
	bool res = false;	
	res = ((mode > KX_ACT_PROP_NODEF) && (mode < KX_ACT_PROP_MAX));
	return res;
}


	CValue* 

SCA_PropertyActuator::

GetReplica() {

	SCA_PropertyActuator* replica = new SCA_PropertyActuator(*this);

	replica->ProcessReplica();

	// this will copy properties and so on...

	CValue::AddDataToReplica(replica);

	return replica;

};




/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject SCA_PropertyActuator::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"SCA_PropertyActuator",
	sizeof(SCA_PropertyActuator),
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

PyParentObject SCA_PropertyActuator::Parents[] = {
	&SCA_PropertyActuator::Type,
	&SCA_IActuator::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};

PyMethodDef SCA_PropertyActuator::Methods[] = {
	{"setProperty", (PyCFunction) SCA_PropertyActuator::sPySetProperty, METH_VARARGS, SetProperty_doc},
	{"getProperty", (PyCFunction) SCA_PropertyActuator::sPyGetProperty, METH_VARARGS, GetProperty_doc},
	{"setValue", (PyCFunction) SCA_PropertyActuator::sPySetValue, METH_VARARGS, SetValue_doc},
	{"getValue", (PyCFunction) SCA_PropertyActuator::sPyGetValue, METH_VARARGS, GetValue_doc},
	{NULL,NULL} //Sentinel
};

PyObject* SCA_PropertyActuator::_getattr(const STR_String& attr) {
	_getattr_up(SCA_IActuator);
}

/* 1. setProperty                                                        */
char SCA_PropertyActuator::SetProperty_doc[] = 
"setProperty(name)\n"
"\t- name: string\n"
"\tSet the property on which to operate. If there is no property\n"
"\tof this name, the call is ignored.\n";
PyObject* SCA_PropertyActuator::PySetProperty(PyObject* self, PyObject* args, PyObject* kwds)
{
	/* Check whether the name exists first ! */
	char *nameArg;
	if (!PyArg_ParseTuple(args, "s", &nameArg)) {
		return NULL;
	}

	CValue* prop = GetParent()->FindIdentifier(nameArg);

	if (prop) {
		m_propname = nameArg;
	} else {
		; /* not found ... */
	}
	
	Py_Return;
}

/* 2. getProperty                                                        */
char SCA_PropertyActuator::GetProperty_doc[] = 
"getProperty(name)\n"
"\tReturn the property on which the actuator operates.\n";
PyObject* SCA_PropertyActuator::PyGetProperty(PyObject* self, PyObject* args, PyObject* kwds)
{
	return PyString_FromString(m_propname);
}

/* 3. setValue                                                        */
char SCA_PropertyActuator::SetValue_doc[] = 
"setValue(value)\n"
"\t- value: string\n"
"\tSet the value with which the actuator operates. If the value\n"
"\tis not compatible with the type of the property, the subsequent\n"
"\t action is ignored.\n";
PyObject* SCA_PropertyActuator::PySetValue(PyObject* self, PyObject* args, PyObject* kwds)
{
	char *valArg;
	if(!PyArg_ParseTuple(args, "s", &valArg)) {
		return NULL;		
	}
	
	if (valArg)	m_exprtxt = valArg;

	Py_Return;
}

/* 4. getValue                                                        */
char SCA_PropertyActuator::GetValue_doc[] = 
"getValue()\n"
"\tReturns the value with which the actuator operates.\n";
PyObject* SCA_PropertyActuator::PyGetValue(PyObject* self, PyObject* args, PyObject* kwds)
{
	return PyString_FromString(m_exprtxt);
}

/* eof */
