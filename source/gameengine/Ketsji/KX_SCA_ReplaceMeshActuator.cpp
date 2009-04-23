//
// Replace the mesh for this actuator's parent
//
// $Id$
//
// ***** BEGIN GPL LICENSE BLOCK *****
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; if not, write to the Free Software Foundation,
// Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
//
// The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
// All rights reserved.
//
// The Original Code is: all of this file.
//
// Contributor(s): none yet.
//
// ***** END GPL LICENSE BLOCK *****

//
// Previously existed as:

// \source\gameengine\GameLogic\SCA_ReplaceMeshActuator.cpp

// Please look here for revision history.

#include "KX_SCA_ReplaceMeshActuator.h"
#include "KX_MeshProxy.h"

#include "PyObjectPlus.h" 

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */

	PyTypeObject 

KX_SCA_ReplaceMeshActuator::Type = {
	PyObject_HEAD_INIT(NULL)
	0,
	"KX_SCA_ReplaceMeshActuator",
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

PyParentObject KX_SCA_ReplaceMeshActuator::Parents[] = {
	&KX_SCA_ReplaceMeshActuator::Type,
	&SCA_IActuator::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};



PyMethodDef KX_SCA_ReplaceMeshActuator::Methods[] = {
	KX_PYMETHODTABLE(KX_SCA_ReplaceMeshActuator, instantReplaceMesh),
	// Deprecated ----->
	{"setMesh", (PyCFunction) KX_SCA_ReplaceMeshActuator::sPySetMesh, METH_O, (PY_METHODCHAR)SetMesh_doc},
   	KX_PYMETHODTABLE(KX_SCA_ReplaceMeshActuator, getMesh),
	{NULL,NULL} //Sentinel
};

PyAttributeDef KX_SCA_ReplaceMeshActuator::Attributes[] = {
	KX_PYATTRIBUTE_RW_FUNCTION("mesh", KX_SCA_ReplaceMeshActuator, pyattr_get_mesh, pyattr_set_mesh),
	{ NULL }	//Sentinel
};

PyObject* KX_SCA_ReplaceMeshActuator::py_getattro(PyObject *attr)
{
	py_getattro_up(SCA_IActuator);
}

PyObject* KX_SCA_ReplaceMeshActuator::py_getattro_dict() {
	py_getattro_dict_up(SCA_IActuator);
}

int KX_SCA_ReplaceMeshActuator::py_setattro(PyObject *attr, PyObject* value) 
{
	py_setattro_up(SCA_IActuator);
}

PyObject* KX_SCA_ReplaceMeshActuator::pyattr_get_mesh(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_SCA_ReplaceMeshActuator* actuator = static_cast<KX_SCA_ReplaceMeshActuator*>(self);
	if (!actuator->m_mesh)
		Py_RETURN_NONE;
	KX_MeshProxy* meshproxy = new KX_MeshProxy(actuator->m_mesh);
	return meshproxy->NewProxy(true);
}

int KX_SCA_ReplaceMeshActuator::pyattr_set_mesh(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_SCA_ReplaceMeshActuator* actuator = static_cast<KX_SCA_ReplaceMeshActuator*>(self);
	RAS_MeshObject* new_mesh;
	
	if (!ConvertPythonToMesh(value, &new_mesh, true, "actuator.mesh = value: KX_SCA_ReplaceMeshActuator"))
		return 1;
	
	actuator->m_mesh = new_mesh;
	return 0;
}

/* 1. setMesh */
const char KX_SCA_ReplaceMeshActuator::SetMesh_doc[] = 
	"setMesh(name)\n"
	"\t- name: string or None\n"
	"\tSet the mesh that will be substituted for the current one.\n";

PyObject* KX_SCA_ReplaceMeshActuator::PySetMesh(PyObject* value)
{
	ShowDeprecationWarning("setMesh()", "the mesh property");
	RAS_MeshObject* new_mesh;
	
	if (!ConvertPythonToMesh(value, &new_mesh, true, "actuator.mesh = value: KX_SCA_ReplaceMeshActuator"))
		return NULL;
	
	m_mesh = new_mesh;
	Py_RETURN_NONE;
}

KX_PYMETHODDEF_DOC(KX_SCA_ReplaceMeshActuator, getMesh,
"getMesh() -> string\n"
"Returns the name of the mesh to be substituted.\n"
)
{
	ShowDeprecationWarning("getMesh()", "the mesh property");
	if (!m_mesh)
		Py_RETURN_NONE;

	return PyString_FromString(const_cast<char *>(m_mesh->GetName().ReadPtr()));
}


KX_PYMETHODDEF_DOC(KX_SCA_ReplaceMeshActuator, instantReplaceMesh,
"instantReplaceMesh() : immediately replace mesh without delay\n")
{
	InstantReplaceMesh();
	Py_RETURN_NONE;
}

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

KX_SCA_ReplaceMeshActuator::KX_SCA_ReplaceMeshActuator(SCA_IObject *gameobj,
													   class RAS_MeshObject *mesh,
													   SCA_IScene* scene,
													   PyTypeObject* T) : 

	SCA_IActuator(gameobj, T),
	m_mesh(mesh),
	m_scene(scene)
{
} /* End of constructor */



KX_SCA_ReplaceMeshActuator::~KX_SCA_ReplaceMeshActuator()
{ 
	// there's nothing to be done here, really....
} /* end of destructor */



bool KX_SCA_ReplaceMeshActuator::Update()
{
	// bool result = false;	/*unused*/
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();

	if (bNegativeEvent)
		return false; // do nothing on negative events

	if (m_mesh) m_scene->ReplaceMesh(GetParent(),m_mesh);

	return false;
}



CValue* KX_SCA_ReplaceMeshActuator::GetReplica()
{
	KX_SCA_ReplaceMeshActuator* replica = 
		new KX_SCA_ReplaceMeshActuator(*this);

	if (replica == NULL)
		return NULL;

	replica->ProcessReplica();

	return replica;
};

void KX_SCA_ReplaceMeshActuator::InstantReplaceMesh()
{
	if (m_mesh) m_scene->ReplaceMesh(GetParent(),m_mesh);
}

/* eof */
