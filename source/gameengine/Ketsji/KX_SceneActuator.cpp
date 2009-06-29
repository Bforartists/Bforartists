/**
* Set scene/camera stuff
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

#include "SCA_IActuator.h"
#include "KX_SceneActuator.h"
#include <iostream>
#include "KX_Scene.h"
#include "KX_Camera.h"
#include "KX_KetsjiEngine.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

KX_SceneActuator::KX_SceneActuator(SCA_IObject *gameobj, 
								   int mode,
								   KX_Scene *scene,
								   KX_KetsjiEngine* ketsjiEngine,
								   const STR_String& nextSceneName,
								   KX_Camera* camera)
								   : SCA_IActuator(gameobj)
{
	m_mode = mode;
	m_scene  = scene;
	m_KetsjiEngine=ketsjiEngine;
	m_camera = camera;
	m_nextSceneName = nextSceneName;
	if (m_camera)
		m_camera->RegisterActuator(this);
} /* End of constructor */



KX_SceneActuator::~KX_SceneActuator()
{ 
	if (m_camera)
		m_camera->UnregisterActuator(this);
} /* end of destructor */



CValue* KX_SceneActuator::GetReplica()
{
	KX_SceneActuator* replica = new KX_SceneActuator(*this);
	replica->ProcessReplica();
	return replica;
}

void KX_SceneActuator::ProcessReplica()
{
	if (m_camera)
		m_camera->RegisterActuator(this);
	SCA_IActuator::ProcessReplica();
}

bool KX_SceneActuator::UnlinkObject(SCA_IObject* clientobj)
{
	if (clientobj == (SCA_IObject*)m_camera)
	{
		// this object is being deleted, we cannot continue to track it.
		m_camera = NULL;
		return true;
	}
	return false;
}

void KX_SceneActuator::Relink(GEN_Map<GEN_HashedPtr, void*> *obj_map)
{
	void **h_obj = (*obj_map)[m_camera];
	if (h_obj) {
		if (m_camera)
			m_camera->UnregisterActuator(this);
		m_camera = (KX_Camera*)(*h_obj);
		m_camera->RegisterActuator(this);
	}
}


bool KX_SceneActuator::Update()
{
	// bool result = false;	/*unused*/
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();

	if (bNegativeEvent)
		return false; // do nothing on negative events

	switch (m_mode)
	{
	case KX_SCENE_RESTART:
		{
			m_KetsjiEngine->ReplaceScene(m_scene->GetName(),m_scene->GetName());
			break;
		}
	case KX_SCENE_SET_CAMERA:
		if (m_camera)
		{
			m_scene->SetActiveCamera(m_camera);
		}
		else
		{
			// if no camera is set and the parent object is a camera, use it as the camera
			SCA_IObject* parent = GetParent();
			if (parent->GetGameObjectType()==SCA_IObject::OBJ_CAMERA)
			{
				m_scene->SetActiveCamera((KX_Camera*)parent);
			}
		}
		break;
	default:
		break;
	}
	
	if (!m_nextSceneName.Length())
		return false;
	
	switch (m_mode)
	{
	case KX_SCENE_SET_SCENE:
		{
			m_KetsjiEngine->ReplaceScene(m_scene->GetName(),m_nextSceneName);
			break;
		}
	case KX_SCENE_ADD_FRONT_SCENE:
		{
			bool overlay=true;
			m_KetsjiEngine->ConvertAndAddScene(m_nextSceneName,overlay);
			break;
		}
	case KX_SCENE_ADD_BACK_SCENE:
		{
			bool overlay=false;
			m_KetsjiEngine->ConvertAndAddScene(m_nextSceneName,overlay);
			break;
		}
	case KX_SCENE_REMOVE_SCENE:
		{
			m_KetsjiEngine->RemoveScene(m_nextSceneName);
			break;
		}
	case KX_SCENE_SUSPEND:
		{
			m_KetsjiEngine->SuspendScene(m_nextSceneName);
			break;
		}
	case KX_SCENE_RESUME:
		{
			m_KetsjiEngine->ResumeScene(m_nextSceneName);
			break;
		}
	default:
		; /* do nothing? this is an internal error !!! */
	}
	
	return false;
}



/*  returns a camera if the name is valid */
KX_Camera* KX_SceneActuator::FindCamera(char *camName)
{
	KX_SceneList* sl = m_KetsjiEngine->CurrentScenes();
	STR_String name = STR_String(camName);
	KX_SceneList::iterator it = sl->begin();
	KX_Camera* cam = NULL;

	while ((it != sl->end()) && (!cam))
	{
		cam = (*it)->FindCamera(name);
		it++;
	}

	return cam;
}



KX_Scene* KX_SceneActuator::FindScene(char * sceneName)
{
	return m_KetsjiEngine->FindScene(sceneName);
}




/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_SceneActuator::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
		"KX_SceneActuator",
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

PyMethodDef KX_SceneActuator::Methods[] =
{
	//Deprecated functions ------>
	{"setUseRestart", (PyCFunction) KX_SceneActuator::sPySetUseRestart, METH_VARARGS, (PY_METHODCHAR)SetUseRestart_doc},
	{"setScene",      (PyCFunction) KX_SceneActuator::sPySetScene, METH_VARARGS, (PY_METHODCHAR)SetScene_doc},
	{"setCamera",     (PyCFunction) KX_SceneActuator::sPySetCamera, METH_O, (PY_METHODCHAR)SetCamera_doc},
	{"getUseRestart", (PyCFunction) KX_SceneActuator::sPyGetUseRestart, METH_NOARGS, (PY_METHODCHAR)GetUseRestart_doc},
	{"getScene",      (PyCFunction) KX_SceneActuator::sPyGetScene, METH_NOARGS, (PY_METHODCHAR)GetScene_doc},
	{"getCamera",     (PyCFunction) KX_SceneActuator::sPyGetCamera, METH_NOARGS, (PY_METHODCHAR)GetCamera_doc},
	//<----- Deprecated
	{NULL,NULL} //Sentinel
};

PyAttributeDef KX_SceneActuator::Attributes[] = {
	KX_PYATTRIBUTE_STRING_RW("scene",0,32,true,KX_SceneActuator,m_nextSceneName),
	KX_PYATTRIBUTE_RW_FUNCTION("camera",KX_SceneActuator,pyattr_get_camera,pyattr_set_camera),
	KX_PYATTRIBUTE_BOOL_RW("useRestart", KX_SceneActuator, m_restart),
	KX_PYATTRIBUTE_INT_RW("mode", KX_SCENE_NODEF+1, KX_SCENE_MAX-1, true, KX_SceneActuator, m_mode),
	{ NULL }	//Sentinel
};

PyObject* KX_SceneActuator::pyattr_get_camera(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_SceneActuator* actuator = static_cast<KX_SceneActuator*>(self);
	if (!actuator->m_camera)
		Py_RETURN_NONE;
	
	return actuator->m_camera->GetProxy();
}

int KX_SceneActuator::pyattr_set_camera(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_SceneActuator* actuator = static_cast<KX_SceneActuator*>(self);
	KX_Camera *camOb;
	
	if (!ConvertPythonToCamera(value, &camOb, true, "actu.camera = value: KX_SceneActuator"))
		return PY_SET_ATTR_FAIL;
	
	if (actuator->m_camera)
		actuator->m_camera->UnregisterActuator(actuator);
	
	if(camOb==NULL) {
		actuator->m_camera= NULL;
	}
	else {	
		actuator->m_camera = camOb;
		actuator->m_camera->RegisterActuator(actuator);
	}
	
	return PY_SET_ATTR_SUCCESS;
}


/* 2. setUseRestart--------------------------------------------------------- */
const char KX_SceneActuator::SetUseRestart_doc[] = 
"setUseRestart(flag)\n"
"\t- flag: 0 or 1.\n"
"\tSet flag to 1 to restart the scene.\n" ;
PyObject* KX_SceneActuator::PySetUseRestart(PyObject* args)
{
	ShowDeprecationWarning("setUseRestart()", "the useRestart property");
	int boolArg;
	
	if (!PyArg_ParseTuple(args, "i:setUseRestart", &boolArg))
	{
		return NULL;
	}
	
	m_restart = boolArg != 0;
	
	Py_RETURN_NONE;
}



/* 3. getUseRestart:                                                         */
const char KX_SceneActuator::GetUseRestart_doc[] = 
"getUseRestart()\n"
"\tReturn whether the scene will be restarted.\n" ;
PyObject* KX_SceneActuator::PyGetUseRestart()
{
	ShowDeprecationWarning("getUseRestart()", "the useRestart property");
	return PyLong_FromSsize_t(!(m_restart == 0));
}



/* 4. set scene------------------------------------------------------------- */
const char KX_SceneActuator::SetScene_doc[] = 
"setScene(scene)\n"
"\t- scene: string\n"
"\tSet the name of scene the actuator will switch to.\n" ;
PyObject* KX_SceneActuator::PySetScene(PyObject* args)
{
	ShowDeprecationWarning("setScene()", "the scene property");
	/* one argument: a scene, ignore the rest */
	char *scene_name;

	if(!PyArg_ParseTuple(args, "s:setScene", &scene_name))
	{
		return NULL;
	}

	/* Scene switch is done by name. */
	m_nextSceneName = scene_name;

	Py_RETURN_NONE;
}



/* 5. getScene:                                                              */
const char KX_SceneActuator::GetScene_doc[] = 
"getScene()\n"
"\tReturn the name of the scene the actuator wants to switch to.\n" ;
PyObject* KX_SceneActuator::PyGetScene()
{
	ShowDeprecationWarning("getScene()", "the scene property");
	return PyUnicode_FromString(m_nextSceneName);
}



/* 6. set camera------------------------------------------------------------ */
const char KX_SceneActuator::SetCamera_doc[] = 
"setCamera(camera)\n"
"\t- camera: string\n"
"\tSet the camera to switch to.\n" ;
PyObject* KX_SceneActuator::PySetCamera(PyObject* value)
{
	ShowDeprecationWarning("setCamera()", "the camera property");
	KX_Camera *camOb;
	
	if (!ConvertPythonToCamera(value, &camOb, true, "actu.setCamera(value): KX_SceneActuator"))
		return NULL;
	
	if (m_camera)
		m_camera->UnregisterActuator(this);
	
	if(camOb==NULL) {
		m_camera= NULL;
	}
	else {	
		m_camera = camOb;
		m_camera->RegisterActuator(this);
	}
	Py_RETURN_NONE;
}



/* 7. getCamera:                                                             */
const char KX_SceneActuator::GetCamera_doc[] = 
"getCamera()\n"
"\tReturn the name of the camera to switch to.\n" ;
PyObject* KX_SceneActuator::PyGetCamera()
{
	ShowDeprecationWarning("getCamera()", "the camera property");
	if (m_camera) {
		return PyUnicode_FromString(m_camera->GetName());
	}
	else {
		Py_RETURN_NONE;
	}
}
/* eof */
