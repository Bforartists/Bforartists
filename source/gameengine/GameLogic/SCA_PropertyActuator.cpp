/**
 * Assign, change, copy properties
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

SCA_PropertyActuator::SCA_PropertyActuator(SCA_IObject* gameobj,SCA_IObject* sourceObj,const STR_String& propname,const STR_String& expr,int acttype,PyTypeObject* T )
   :	SCA_IActuator(gameobj,T),
	m_type(acttype),
	m_propname(propname),
	m_exprtxt(expr),
	m_sourceObj(sourceObj)
{
	// protect ourselves against someone else deleting the source object
	// don't protect against ourselves: it would create a dead lock
	if (m_sourceObj)
		m_sourceObj->RegisterActuator(this);
}

SCA_PropertyActuator::~SCA_PropertyActuator()
{
	if (m_sourceObj)
		m_sourceObj->UnregisterActuator(this);
}

bool SCA_PropertyActuator::Update()
{
	bool result = false;

	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();


	if (bNegativeEvent)
		return false; // do nothing on negative events


	CValue* propowner = GetParent();
	CParser parser;
	parser.SetContext( propowner->AddRef());
	
	CExpression* userexpr= NULL;
	
	if (m_type==KX_ACT_PROP_TOGGLE)
	{
		/* dont use */
		CValue* newval;
		CValue* oldprop = propowner->GetProperty(m_propname);
		if (oldprop)
		{
			newval = new CBoolValue((oldprop->GetNumber()==0.0) ? true:false);
			oldprop->SetValue(newval);
		} else
		{	/* as not been assigned, evaluate as false, so assign true */
			newval = new CBoolValue(true);
			propowner->SetProperty(m_propname,newval);
		}
		newval->Release();
	}
	else if ((userexpr = parser.ProcessText(m_exprtxt))) {
		switch (m_type)
		{

		case KX_ACT_PROP_ASSIGN:
			{
				
				CValue* newval = userexpr->Calculate();
				CValue* oldprop = propowner->GetProperty(m_propname);
				if (oldprop)
				{
					oldprop->SetValue(newval);
				} else
				{
					propowner->SetProperty(m_propname,newval);
				}
				newval->Release();
				break;
			}
		case KX_ACT_PROP_ADD:
			{
				CValue* oldprop = propowner->GetProperty(m_propname);
				if (oldprop)
				{
					// int waarde = (int)oldprop->GetNumber();  /*unused*/
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
						CValue *val = copyprop->GetReplica();
						GetParent()->SetProperty(
							 m_propname,
							 val);
						val->Release();

					}
				}
				break;
			}
		/* case KX_ACT_PROP_TOGGLE: */ /* accounted for above, no need for userexpr */
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

void SCA_PropertyActuator::ProcessReplica()
{
	// no need to check for self reference like in the constructor:
	// the replica will always have a different parent
	if (m_sourceObj)
		m_sourceObj->RegisterActuator(this);
	SCA_IActuator::ProcessReplica();
}

bool SCA_PropertyActuator::UnlinkObject(SCA_IObject* clientobj)
{
	if (clientobj == m_sourceObj)
	{
		// this object is being deleted, we cannot continue to track it.
		m_sourceObj = NULL;
		return true;
	}
	return false;
}

void SCA_PropertyActuator::Relink(GEN_Map<GEN_HashedPtr, void*> *obj_map)
{
	void **h_obj = (*obj_map)[m_sourceObj];
	if (h_obj) {
		if (m_sourceObj)
			m_sourceObj->UnregisterActuator(this);
		m_sourceObj = (SCA_IObject*)(*h_obj);
		m_sourceObj->RegisterActuator(this);
	}
}


/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject SCA_PropertyActuator::Type = {
	PyObject_HEAD_INIT(NULL)
	0,
	"SCA_PropertyActuator",
	sizeof(SCA_PropertyActuator),
	0,
	PyDestructor,
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

PyParentObject SCA_PropertyActuator::Parents[] = {
	&SCA_PropertyActuator::Type,
	&SCA_IActuator::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};

PyMethodDef SCA_PropertyActuator::Methods[] = {
	//Deprecated functions ------>
	{"setProperty", (PyCFunction) SCA_PropertyActuator::sPySetProperty, METH_VARARGS, (PY_METHODCHAR)SetProperty_doc},
	{"getProperty", (PyCFunction) SCA_PropertyActuator::sPyGetProperty, METH_VARARGS, (PY_METHODCHAR)GetProperty_doc},
	{"setValue", (PyCFunction) SCA_PropertyActuator::sPySetValue, METH_VARARGS, (PY_METHODCHAR)SetValue_doc},
	{"getValue", (PyCFunction) SCA_PropertyActuator::sPyGetValue, METH_VARARGS, (PY_METHODCHAR)GetValue_doc},
	//<----- Deprecated
	{NULL,NULL} //Sentinel
};

PyAttributeDef SCA_PropertyActuator::Attributes[] = {
	KX_PYATTRIBUTE_STRING_RW_CHECK("property",0,100,false,SCA_PropertyActuator,m_propname,CheckProperty),
	KX_PYATTRIBUTE_STRING_RW("value",0,100,false,SCA_PropertyActuator,m_exprtxt),
	{ NULL }	//Sentinel
};

PyObject* SCA_PropertyActuator::py_getattro(PyObject *attr) {
	py_getattro_up(SCA_IActuator);
}

int SCA_PropertyActuator::py_setattro(PyObject *attr, PyObject *value) {
	py_setattro_up(SCA_IActuator);
}

/* 1. setProperty                                                        */
const char SCA_PropertyActuator::SetProperty_doc[] = 
"setProperty(name)\n"
"\t- name: string\n"
"\tSet the property on which to operate. If there is no property\n"
"\tof this name, the call is ignored.\n";
PyObject* SCA_PropertyActuator::PySetProperty(PyObject* self, PyObject* args, PyObject* kwds)
{
	ShowDeprecationWarning("setProperty()", "the 'property' property");
	/* Check whether the name exists first ! */
	char *nameArg;
	if (!PyArg_ParseTuple(args, "s:setProperty", &nameArg)) {
		return NULL;
	}

	CValue* prop = GetParent()->FindIdentifier(nameArg);

	if (!prop->IsError()) {
		m_propname = nameArg;
	} else {
		; /* not found ... */
	}
	prop->Release();
	
	Py_RETURN_NONE;
}

/* 2. getProperty                                                        */
const char SCA_PropertyActuator::GetProperty_doc[] = 
"getProperty(name)\n"
"\tReturn the property on which the actuator operates.\n";
PyObject* SCA_PropertyActuator::PyGetProperty(PyObject* self, PyObject* args, PyObject* kwds)
{
	ShowDeprecationWarning("getProperty()", "the 'property' property");
	return PyString_FromString(m_propname);
}

/* 3. setValue                                                        */
const char SCA_PropertyActuator::SetValue_doc[] = 
"setValue(value)\n"
"\t- value: string\n"
"\tSet the value with which the actuator operates. If the value\n"
"\tis not compatible with the type of the property, the subsequent\n"
"\t action is ignored.\n";
PyObject* SCA_PropertyActuator::PySetValue(PyObject* self, PyObject* args, PyObject* kwds)
{
	ShowDeprecationWarning("setValue()", "the value property");
	char *valArg;
	if(!PyArg_ParseTuple(args, "s:setValue", &valArg)) {
		return NULL;		
	}
	
	if (valArg)	m_exprtxt = valArg;

	Py_RETURN_NONE;
}

/* 4. getValue                                                        */
const char SCA_PropertyActuator::GetValue_doc[] = 
"getValue()\n"
"\tReturns the value with which the actuator operates.\n";
PyObject* SCA_PropertyActuator::PyGetValue(PyObject* self, PyObject* args, PyObject* kwds)
{
	ShowDeprecationWarning("getValue()", "the value property");
	return PyString_FromString(m_exprtxt);
}

/* eof */
