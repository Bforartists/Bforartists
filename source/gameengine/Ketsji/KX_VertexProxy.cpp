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

#include "KX_VertexProxy.h"
#include "RAS_TexVert.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

PyTypeObject KX_VertexProxy::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"KX_VertexProxy",
	sizeof(KX_VertexProxy),
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

PyParentObject KX_VertexProxy::Parents[] = {
	&KX_VertexProxy::Type,
	&SCA_IObject::Type,
	&CValue::Type,
	NULL
};

PyMethodDef KX_VertexProxy::Methods[] = {
{"getXYZ", (PyCFunction)KX_VertexProxy::sPyGetXYZ,METH_VARARGS},
{"setXYZ", (PyCFunction)KX_VertexProxy::sPySetXYZ,METH_VARARGS},
{"getUV", (PyCFunction)KX_VertexProxy::sPyGetUV,METH_VARARGS},
{"setUV", (PyCFunction)KX_VertexProxy::sPySetUV,METH_VARARGS},
{"getRGBA", (PyCFunction)KX_VertexProxy::sPyGetRGBA,METH_VARARGS},
{"setRGBA", (PyCFunction)KX_VertexProxy::sPySetRGBA,METH_VARARGS},
{"getNormal", (PyCFunction)KX_VertexProxy::sPyGetNormal,METH_VARARGS},
{"setNormal", (PyCFunction)KX_VertexProxy::sPySetNormal,METH_VARARGS},
  {NULL,NULL} //Sentinel
};

PyObject*
KX_VertexProxy::_getattr(const STR_String& attr)
{
  _getattr_up(SCA_IObject);
}



KX_VertexProxy::KX_VertexProxy(RAS_TexVert* vertex)
:m_vertex(vertex)
{
	
}

KX_VertexProxy::~KX_VertexProxy()
{
	
}



// stuff for cvalue related things
CValue*		KX_VertexProxy::Calc(VALUE_OPERATOR op, CValue *val) { return NULL;}
CValue*		KX_VertexProxy::CalcFinal(VALUE_DATA_TYPE dtype, VALUE_OPERATOR op, CValue *val) { return NULL;}	
STR_String	sVertexName="vertex";
const STR_String &	KX_VertexProxy::GetText() {return sVertexName;};
float		KX_VertexProxy::GetNumber() { return -1;}
STR_String	KX_VertexProxy::GetName() { return sVertexName;}
void		KX_VertexProxy::SetName(STR_String name) { };
CValue*		KX_VertexProxy::GetReplica() { return NULL;}
void		KX_VertexProxy::ReplicaSetName(STR_String name) {};


// stuff for python integration
	
PyObject* KX_VertexProxy::PyGetXYZ(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
	
	MT_Point3 pos = m_vertex->getLocalXYZ();
	
	PyObject* resultlist = PyList_New(3);
	int index;
	for (index=0;index<3;index++)
	{
		PyList_SetItem(resultlist,index,PyFloat_FromDouble(pos[index]));
	}

	return resultlist;

}

PyObject* KX_VertexProxy::PySetXYZ(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{

	MT_Point3 pos = ConvertPythonVectorArg(args);
	m_vertex->SetXYZ(pos);


	Py_Return;
}

PyObject* KX_VertexProxy::PyGetNormal(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
	
	const short* shortnormal = m_vertex->getNormal();
	MT_Vector3 normal(shortnormal[0],shortnormal[1],shortnormal[2]);
	normal.normalize();
	
	PyObject* resultlist = PyList_New(3);
	int index;
	for (index=0;index<3;index++)
	{
		PyList_SetItem(resultlist,index,PyFloat_FromDouble(normal[index]));
	}

	return resultlist;

}

PyObject* KX_VertexProxy::PySetNormal(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
	MT_Point3 normal = ConvertPythonVectorArg(args);
	m_vertex->SetNormal(normal);
	Py_Return;
}


PyObject* KX_VertexProxy::PyGetRGBA(PyObject* self,
			       PyObject* args, 
			       PyObject* kwds)
{
	int rgba = m_vertex->getRGBA();
	return PyInt_FromLong(rgba);
}

PyObject* KX_VertexProxy::PySetRGBA(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
	int rgba;
	if (PyArg_ParseTuple(args,"i",&rgba))
	{
		m_vertex->SetRGBA(rgba);
	}
	Py_Return;
}


PyObject* KX_VertexProxy::PyGetUV(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
	MT_Vector2 uv = m_vertex->getUV1();
	PyObject* resultlist = PyList_New(2);
	int index;
	for (index=0;index<2;index++)
	{
		PyList_SetItem(resultlist,index,PyFloat_FromDouble(uv[index]));
	}

	return resultlist;

}

PyObject* KX_VertexProxy::PySetUV(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
	MT_Point3 uv = ConvertPythonVectorArg(args);
	m_vertex->SetUV(MT_Point2(uv[0],uv[1]));
	Py_Return;
}



