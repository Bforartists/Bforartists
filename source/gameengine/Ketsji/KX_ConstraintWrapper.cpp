/**
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
#include <Python.h>
#include "PyObjectPlus.h"
#include "KX_ConstraintWrapper.h"
#include "PHY_IPhysicsEnvironment.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

KX_ConstraintWrapper::KX_ConstraintWrapper(
						PHY_ConstraintType ctype,
						int constraintId,
						PHY_IPhysicsEnvironment* physenv) :
		PyObjectPlus(),
		m_constraintId(constraintId),
		m_constraintType(ctype),
		m_physenv(physenv)
{
}
KX_ConstraintWrapper::~KX_ConstraintWrapper()
{
}

PyObject* KX_ConstraintWrapper::PyGetConstraintId()
{
	return PyInt_FromLong(m_constraintId);
}


PyObject* KX_ConstraintWrapper::PyGetParam(PyObject* args, PyObject* kwds)
{
	int dof;
	float value;
	
	if (!PyArg_ParseTuple(args,"i:getParam",&dof))
		return NULL;
	
	value = m_physenv->getConstraintParam(m_constraintId,dof);
	return PyFloat_FromDouble(value);
	
}

PyObject* KX_ConstraintWrapper::PySetParam(PyObject* args, PyObject* kwds)
{
	int dof;
	float minLimit,maxLimit;
	
	if (!PyArg_ParseTuple(args,"iff:setParam",&dof,&minLimit,&maxLimit))
		return NULL;
	
	m_physenv->setConstraintParam(m_constraintId,dof,minLimit,maxLimit);
	Py_RETURN_NONE;
}


//python specific stuff
PyTypeObject KX_ConstraintWrapper::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
		"KX_ConstraintWrapper",
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
		&PyObjectPlus::Type
};

PyMethodDef KX_ConstraintWrapper::Methods[] = {
	{"getConstraintId",(PyCFunction) KX_ConstraintWrapper::sPyGetConstraintId, METH_NOARGS},
	{"setParam",(PyCFunction) KX_ConstraintWrapper::sPySetParam, METH_VARARGS},
	{"getParam",(PyCFunction) KX_ConstraintWrapper::sPyGetParam, METH_VARARGS},
	{NULL,NULL} //Sentinel
};

PyAttributeDef KX_ConstraintWrapper::Attributes[] = {
	//KX_PYATTRIBUTE_TODO("constraintId"),
	{ NULL }	//Sentinel
};
