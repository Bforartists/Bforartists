/**
 * $Id$
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

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#include "KX_MeshProxy.h"
#include "RAS_IPolygonMaterial.h"
#include "RAS_MeshObject.h"

#include "KX_VertexProxy.h"
#include "KX_PolyProxy.h"

#include "KX_PolygonMaterial.h"
#include "KX_BlenderMaterial.h"

#include "KX_PyMath.h"
#include "KX_ConvertPhysicsObject.h"

#include "PyObjectPlus.h" 

PyTypeObject KX_MeshProxy::Type = {
	PyObject_HEAD_INIT(NULL)
	0,
	"KX_MeshProxy",
	sizeof(KX_MeshProxy),
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

PyParentObject KX_MeshProxy::Parents[] = {
	&KX_MeshProxy::Type,
	&SCA_IObject::Type,
	&CValue::Type,
	&PyObjectPlus::Type,
	NULL
};

PyMethodDef KX_MeshProxy::Methods[] = {
// Deprecated ----->
{"getNumMaterials", (PyCFunction)KX_MeshProxy::sPyGetNumMaterials,METH_VARARGS},
{"getNumPolygons", (PyCFunction)KX_MeshProxy::sPyGetNumPolygons,METH_NOARGS},
// <-----

{"getMaterialName", (PyCFunction)KX_MeshProxy::sPyGetMaterialName,METH_VARARGS},
{"getTextureName", (PyCFunction)KX_MeshProxy::sPyGetTextureName,METH_VARARGS},
{"getVertexArrayLength", (PyCFunction)KX_MeshProxy::sPyGetVertexArrayLength,METH_VARARGS},
{"getVertex", (PyCFunction)KX_MeshProxy::sPyGetVertex,METH_VARARGS},
{"getPolygon", (PyCFunction)KX_MeshProxy::sPyGetPolygon,METH_VARARGS},
KX_PYMETHODTABLE(KX_MeshProxy, reinstancePhysicsMesh),
//{"getIndexArrayLength", (PyCFunction)KX_MeshProxy::sPyGetIndexArrayLength,METH_VARARGS},

  {NULL,NULL} //Sentinel
};

PyAttributeDef KX_MeshProxy::Attributes[] = {
	KX_PYATTRIBUTE_RO_FUNCTION("materials",		KX_MeshProxy, pyattr_get_materials),
	KX_PYATTRIBUTE_RO_FUNCTION("numPolygons",	KX_MeshProxy, pyattr_get_materials),
	KX_PYATTRIBUTE_RO_FUNCTION("numMaterials",	KX_MeshProxy, pyattr_get_materials),

	{ NULL }	//Sentinel
};

void KX_MeshProxy::SetMeshModified(bool v)
{
	m_meshobj->SetMeshModified(v);
}


PyObject* KX_MeshProxy::py_getattro(PyObject *attr)
{
 	py_getattro_up(SCA_IObject);
}

int KX_MeshProxy::py_setattro(PyObject *attr, PyObject* value)
{
	py_setattro_up(SCA_IObject);
}


KX_MeshProxy::KX_MeshProxy(RAS_MeshObject* mesh)
	: SCA_IObject(&Type), m_meshobj(mesh)
{
}

KX_MeshProxy::~KX_MeshProxy()
{
}



// stuff for cvalue related things
CValue*		KX_MeshProxy::Calc(VALUE_OPERATOR op, CValue *val) { return NULL;}
CValue*		KX_MeshProxy::CalcFinal(VALUE_DATA_TYPE dtype, VALUE_OPERATOR op, CValue *val) { return NULL;}	

const STR_String &	KX_MeshProxy::GetText() {return m_meshobj->GetName();};
double		KX_MeshProxy::GetNumber() { return -1;}
STR_String	KX_MeshProxy::GetName() { return m_meshobj->GetName();}
void		KX_MeshProxy::SetName(STR_String name) { };
CValue*		KX_MeshProxy::GetReplica() { return NULL;}
void		KX_MeshProxy::ReplicaSetName(STR_String name) {};


// stuff for python integration
	
PyObject* KX_MeshProxy::PyGetNumMaterials(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
	int num = m_meshobj->NumMaterials();
	ShowDeprecationWarning("getNumMaterials()", "the numMaterials property");
	return PyInt_FromLong(num);
}

PyObject* KX_MeshProxy::PyGetNumPolygons(PyObject* self)
{
	int num = m_meshobj->NumPolygons();
	ShowDeprecationWarning("getNumPolygons()", "the numPolygons property");
	return PyInt_FromLong(num);
}

PyObject* KX_MeshProxy::PyGetMaterialName(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
    int matid= 1;
	STR_String matname;

	if (PyArg_ParseTuple(args,"i:getMaterialName",&matid))
	{
		matname = m_meshobj->GetMaterialName(matid);
	}
	else {
		return NULL;
	}

	return PyString_FromString(matname.Ptr());
		
}
	

PyObject* KX_MeshProxy::PyGetTextureName(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
    int matid= 1;
	STR_String matname;

	if (PyArg_ParseTuple(args,"i:getTextureName",&matid))
	{
		matname = m_meshobj->GetTextureName(matid);
	}
	else {
		return NULL;
	}

	return PyString_FromString(matname.Ptr());
		
}

PyObject* KX_MeshProxy::PyGetVertexArrayLength(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
    int matid= 0;
	int length = 0;

	
	if (!PyArg_ParseTuple(args,"i:getVertexArrayLength",&matid))
		return NULL;
	

	RAS_MeshMaterial *mmat = m_meshobj->GetMeshMaterial(matid); /* can be NULL*/
	
	if (mmat)
	{
		RAS_IPolyMaterial* mat = mmat->m_bucket->GetPolyMaterial();
		if (mat)
			length = m_meshobj->NumVertices(mat);
	}
	
	return PyInt_FromLong(length);
}


PyObject* KX_MeshProxy::PyGetVertex(PyObject* self, 
			       PyObject* args, 
			       PyObject* kwds)
{
    int vertexindex= 1;
	int matindex= 1;
	PyObject* vertexob = NULL;

	if (PyArg_ParseTuple(args,"ii:getVertex",&matindex,&vertexindex))
	{
		RAS_TexVert* vertex = m_meshobj->GetVertex(matindex,vertexindex);
		if (vertex)
		{
			vertexob = new KX_VertexProxy(this, vertex);
		}
	}
	else {
		return NULL;
	}

	return vertexob;
		
}

PyObject* KX_MeshProxy::PyGetPolygon(PyObject* self,
			       PyObject* args, 
			       PyObject* kwds)
{
    int polyindex= 1;
	PyObject* polyob = NULL;

	if (!PyArg_ParseTuple(args,"i:getPolygon",&polyindex))
		return NULL;
	
	if (polyindex<0 || polyindex >= m_meshobj->NumPolygons())
	{
		PyErr_SetString(PyExc_AttributeError, "Invalid polygon index");
		return NULL;
	}
		

	RAS_Polygon* polygon = m_meshobj->GetPolygon(polyindex);
	if (polygon)
	{
		polyob = new KX_PolyProxy(m_meshobj, polygon);
	}
	else {
		PyErr_SetString(PyExc_AttributeError, "polygon is NULL, unknown reason");
	}
	return polyob;
}

KX_PYMETHODDEF_DOC(KX_MeshProxy, reinstancePhysicsMesh,
"Reinstance the physics mesh.")
{
	//this needs to be reviewed, it is dependend on Sumo/Solid. Who is using this ?
	Py_RETURN_NONE;//(KX_ReInstanceShapeFromMesh(m_meshobj)) ? Py_RETURN_TRUE : Py_RETURN_FALSE;
}

PyObject* KX_MeshProxy::pyattr_get_materials(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_MeshProxy* self= static_cast<KX_MeshProxy*>(self_v);
	
	int tot= self->m_meshobj->NumMaterials();
	int i;
	
	PyObject *materials = PyList_New( tot );
	
	list<RAS_MeshMaterial>::iterator mit= self->m_meshobj->GetFirstMaterial();
	
	
	for(i=0; i<tot; mit++, i++) {
		RAS_IPolyMaterial *polymat = mit->m_bucket->GetPolyMaterial(); 	 
		
		/* Why do we need to check for RAS_BLENDERMAT if both are cast to a (PyObject*)? - Campbell */
		if(polymat->GetFlag() & RAS_BLENDERMAT) 	 
		{ 	 
			KX_BlenderMaterial *mat = static_cast<KX_BlenderMaterial*>(polymat); 	 
			PyList_SET_ITEM(materials, i, mat);
			Py_INCREF(mat);
		}
		else { 	
			KX_PolygonMaterial *mat = static_cast<KX_PolygonMaterial*>(polymat);
			PyList_SET_ITEM(materials, i, mat);
			Py_INCREF(mat);
		}
	}	
	return materials;
}

PyObject * KX_MeshProxy::pyattr_get_numMaterials(void * selfv, const KX_PYATTRIBUTE_DEF * attrdef) {
	KX_MeshProxy * self = static_cast<KX_MeshProxy *> (selfv);
	int num = self->m_meshobj->NumMaterials();
	return PyInt_FromLong(num);
}

PyObject * KX_MeshProxy::pyattr_get_numPolygons(void * selfv, const KX_PYATTRIBUTE_DEF * attrdef) {
	KX_MeshProxy * self = static_cast<KX_MeshProxy *> (selfv);
	int num = self->m_meshobj->NumPolygons();
	return PyInt_FromLong(num);
}
