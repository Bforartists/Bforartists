/*
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
 * Actuator to toggle visibility/invisibility of objects
 */

#include "KX_StateActuator.h"
#include "KX_GameObject.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

KX_StateActuator::KX_StateActuator(
	SCA_IObject* gameobj,
	int operation,
	unsigned int mask
	) 
	: SCA_IActuator(gameobj),
	  m_operation(operation),
	  m_mask(mask)
{
	// intentionally empty
}

KX_StateActuator::~KX_StateActuator(
	void
	)
{
	// intentionally empty
}

// used to put state actuator to be executed before any other actuators
SG_QList KX_StateActuator::m_stateActuatorHead;

CValue*
KX_StateActuator::GetReplica(
	void
	)
{
	KX_StateActuator* replica = new KX_StateActuator(*this);
	replica->ProcessReplica();
	return replica;
}

bool
KX_StateActuator::Update()
{
	bool bNegativeEvent = IsNegativeEvent();
	unsigned int objMask;

	// execution of state actuator means that we are in the execution phase, reset this pointer
	// because all the active actuator of this object will be removed for sure.
	m_gameobj->m_firstState = NULL;
	RemoveAllEvents();
	if (bNegativeEvent) return false;

	KX_GameObject *obj = (KX_GameObject*) GetParent();
	
	objMask = obj->GetState();
	switch (m_operation) 
	{
	case OP_CPY:
		objMask = m_mask;
		break;
	case OP_SET:
		objMask |= m_mask;
		break;
	case OP_CLR:
		objMask &= ~m_mask;
		break;
	case OP_NEG:
		objMask ^= m_mask;
		break;
	default:
		// unsupported operation, no  nothing
		return false;
	}
	obj->SetState(objMask);
	return false;
}

// this function is only used to deactivate actuators outside the logic loop
// e.g. when an object is deleted.
void KX_StateActuator::Deactivate()
{
	if (QDelink())
	{
		// the actuator was in the active list
		if (m_stateActuatorHead.QEmpty())
			// no more state object active
			m_stateActuatorHead.Delink();
	}
}

void KX_StateActuator::Activate(SG_DList& head)
{
	// sort the state actuators per object on the global list
	if (QEmpty())
	{
		InsertSelfActiveQList(m_stateActuatorHead, &m_gameobj->m_firstState);
		// add front to make sure it runs before other actuators
		head.AddFront(&m_stateActuatorHead);
	}
}


/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */



/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_StateActuator::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"KX_StateActuator",
	sizeof(PyObjectPlus_Proxy),
	0,
	py_base_dealloc,
	0,
	0,
	0,
	0,
	py_base_repr,
	0,0,0,0,0,0,
	NULL, //py_base_getattro,
	NULL, //py_base_setattro,
	0,
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	0,0,0,0,0,0,0,
	Methods,
	0,
	0,
	&SCA_IActuator::Type
};

PyMethodDef KX_StateActuator::Methods[] = {
	// deprecated -->
	{"setOperation", (PyCFunction) KX_StateActuator::sPySetOperation, 
	 METH_VARARGS, (PY_METHODCHAR)SetOperation_doc},
	{"setMask", (PyCFunction) KX_StateActuator::sPySetMask, 
	 METH_VARARGS, (PY_METHODCHAR)SetMask_doc},
	 // <--
	{NULL,NULL} //Sentinel
};

PyAttributeDef KX_StateActuator::Attributes[] = {
	KX_PYATTRIBUTE_INT_RW("operation",KX_StateActuator::OP_NOP+1,KX_StateActuator::OP_COUNT-1,false,KX_StateActuator,m_operation),
	KX_PYATTRIBUTE_INT_RW("mask",0,0x3FFFFFFF,false,KX_StateActuator,m_mask),
	{ NULL }	//Sentinel
};


/* set operation ---------------------------------------------------------- */
const char 
KX_StateActuator::SetOperation_doc[] = 
"setOperation(op)\n"
"\t - op : bit operation (0=Copy, 1=Set, 2=Clear, 3=Negate)"
"\tSet the type of bit operation to be applied on object state mask.\n"
"\tUse setMask() to specify the bits that will be modified.\n";
PyObject* 

KX_StateActuator::PySetOperation(PyObject* args) {
	ShowDeprecationWarning("setOperation()", "the operation property");
	int oper;

	if(!PyArg_ParseTuple(args, "i:setOperation", &oper)) {
		return NULL;
	}

	m_operation = oper;

	Py_RETURN_NONE;
}

/* set mask ---------------------------------------------------------- */
const char 
KX_StateActuator::SetMask_doc[] = 
"setMask(mask)\n"
"\t - mask : bits that will be modified"
"\tSet the value that defines the bits that will be modified by the operation.\n"
"\tThe bits that are 1 in the value will be updated in the object state,\n"
"\tthe bits that are 0 are will be left unmodified expect for the Copy operation\n"
"\twhich copies the value to the object state.\n";
PyObject* 

KX_StateActuator::PySetMask(PyObject* args) {
	ShowDeprecationWarning("setMask()", "the mask property");
	int mask;

	if(!PyArg_ParseTuple(args, "i:setMask", &mask)) {
		return NULL;
	}

	m_mask = mask;

	Py_RETURN_NONE;
}


