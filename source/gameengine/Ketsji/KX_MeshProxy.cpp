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
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"KX_MeshProxy",
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

PyParentObject KX_MeshProxy::Parents[] = {
	&KX_MeshProxy::Type,
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
	KX_PYATTRIBUTE_RO_FUNCTION("numPolygons",	KX_MeshProxy, pyattr_get_numPolygons),
	KX_PYATTRIBUTE_RO_FUNCTION("numMaterials",	KX_MeshProxy, pyattr_get_numMaterials),

	{ NULL }	//Sentinel
};

void KX_MeshProxy::SetMeshModified(bool v)
{
	m_meshobj->SetMeshModified(v);
}


PyObject* KX_MeshProxy::py_getattro(PyObject *attr)
{
 	py_getattro_up(CValue);
}

PyObject* KX_MeshProxy::py_getattro_dict() {
	py_getattro_dict_up(CValue);
}

int KX_MeshProxy::py_setattro(PyObject *attr, PyObject* value)
{
	py_setattro_up(CValue);
}


KX_MeshProxy::KX_MeshProxy(RAS_MeshObject* mesh)
	: CValue(&Type), m_meshobj(mesh)
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
STR_String&	KX_MeshProxy::GetName() { return m_meshobj->GetName();}
void		KX_MeshProxy::SetName(const char *name) { };
CValue*		KX_MeshProxy::GetReplica() { return NULL;}


// stuff for python integration
	
PyObject* KX_MeshProxy::PyGetNumMaterials(PyObject* args, PyObject* kwds)
{
	int num = m_meshobj->NumMaterials();
	ShowDeprecationWarning("getNumMaterials()", "the numMaterials property");
	return PyInt_FromLong(num);
}

PyObject* KX_MeshProxy::PyGetNumPolygons()
{
	int num = m_meshobj->NumPolygons();
	ShowDeprecationWarning("getNumPolygons()", "the numPolygons property");
	return PyInt_FromLong(num);
}

PyObject* KX_MeshProxy::PyGetMaterialName(PyObject* args, PyObject* kwds)
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
	

PyObject* KX_MeshProxy::PyGetTextureName(PyObject* args, PyObject* kwds)
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

PyObject* KX_MeshProxy::PyGetVertexArrayLength(PyObject* args, PyObject* kwds)
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


PyObject* KX_MeshProxy::PyGetVertex(PyObject* args, PyObject* kwds)
{
    int vertexindex;
	int matindex;

	if (!PyArg_ParseTuple(args,"ii:getVertex",&matindex,&vertexindex))
		return NULL;
	
	RAS_TexVert* vertex = m_meshobj->GetVertex(matindex,vertexindex);
	
	if(vertex==NULL) {
		PyErr_SetString(PyExc_ValueError, "mesh.getVertex(mat_idx, vert_idx): KX_MeshProxy, could not get a vertex at the given indicies");
		return NULL;
	}
	
	return (new KX_VertexProxy(this, vertex))->NewProxy(true);
}

PyObject* KX_MeshProxy::PyGetPolygon(PyObject* args, PyObject* kwds)
{
    int polyindex= 1;
	PyObject* polyob = NULL;

	if (!PyArg_ParseTuple(args,"i:getPolygon",&polyindex))
		return NULL;
	
	if (polyindex<0 || polyindex >= m_meshobj->NumPolygons())
	{
		PyErr_SetString(PyExc_AttributeError, "mesh.getPolygon(int): KX_MeshProxy, invalid polygon index");
		return NULL;
	}
		

	RAS_Polygon* polygon = m_meshobj->GetPolygon(polyindex);
	if (polygon)
	{
		polyob = (new KX_PolyProxy(m_meshobj, polygon))->NewProxy(true);
	}
	else {
		PyErr_SetString(PyExc_AttributeError, "mesh.getPolygon(int): KX_MeshProxy, polygon is NULL, unknown reason");
	}
	return polyob;
}

KX_PYMETHODDEF_DOC(KX_MeshProxy, reinstancePhysicsMesh,
"Reinstance the physics mesh.")
{
#if 0
	//this needs to be reviewed, it is dependend on Sumo/Solid. Who is using this ?
	if(KX_ReInstanceShapeFromMesh(m_meshobj))
		Py_RETURN_TRUE;
#endif
	Py_RETURN_FALSE;
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
			PyList_SET_ITEM(materials, i, mat->GetProxy());
		}
		else { 	
			KX_PolygonMaterial *mat = static_cast<KX_PolygonMaterial*>(polymat);
			PyList_SET_ITEM(materials, i, mat->GetProxy());
		}
	}	
	return materials;
}

PyObject * KX_MeshProxy::pyattr_get_numMaterials(void * selfv, const KX_PYATTRIBUTE_DEF * attrdef) {
	KX_MeshProxy * self = static_cast<KX_MeshProxy *> (selfv);
	return PyInt_FromLong(self->m_meshobj->NumMaterials());
}

PyObject * KX_MeshProxy::pyattr_get_numPolygons(void * selfv, const KX_PYATTRIBUTE_DEF * attrdef) {
	KX_MeshProxy * self = static_cast<KX_MeshProxy *> (selfv);
	return PyInt_FromLong(self->m_meshobj->NumPolygons());
}

/* a close copy of ConvertPythonToGameObject but for meshes */
bool ConvertPythonToMesh(PyObject * value, RAS_MeshObject **object, bool py_none_ok, const char *error_prefix)
{
	if (value==NULL) {
		PyErr_Format(PyExc_TypeError, "%s, python pointer NULL, should never happen", error_prefix);
		*object = NULL;
		return false;
	}
		
	if (value==Py_None) {
		*object = NULL;
		
		if (py_none_ok) {
			return true;
		} else {
			PyErr_Format(PyExc_TypeError, "%s, expected KX_MeshProxy or a KX_MeshProxy name, None is invalid", error_prefix);
			return false;
		}
	}
	
	if (PyString_Check(value)) {
		*object = (RAS_MeshObject*)SCA_ILogicBrick::m_sCurrentLogicManager->GetMeshByName(STR_String( PyString_AsString(value) ));
		
		if (*object) {
			return true;
		} else {
			PyErr_Format(PyExc_ValueError, "%s, requested name \"%s\" did not match any KX_MeshProxy in this scene", error_prefix, PyString_AsString(value));
			return false;
		}
	}
	
	if (PyObject_TypeCheck(value, &KX_MeshProxy::Type)) {
		KX_MeshProxy *kx_mesh = static_cast<KX_MeshProxy*>BGE_PROXY_REF(value);
		
		/* sets the error */
		if (kx_mesh==NULL) {
			PyErr_Format(PyExc_SystemError, "%s, " BGE_PROXY_ERROR_MSG, error_prefix);
			return false;
		}		
		
		*object = kx_mesh->GetMesh();
		return true;
	}
	
	*object = NULL;
	
	if (py_none_ok) {
		PyErr_Format(PyExc_TypeError, "%s, expect a KX_MeshProxy, a string or None", error_prefix);
	} else {
		PyErr_Format(PyExc_TypeError, "%s, expect a KX_MeshProxy or a string", error_prefix);
	}
	
	return false;
}
