 
//
// Add object to the game world on action of this actuator
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

#ifndef __KX_SCENEACTUATOR
#define __KX_SCENEACTUATOR

#include "SCA_IActuator.h"

class KX_SceneActuator : public SCA_IActuator
{
	Py_Header;
	
	int							m_mode;
	// (restart) has become a toggle internally... not in the interface though
	bool						m_restart;
	// (set Scene) Scene
	/** The current scene. */
	class	KX_Scene*			m_scene;
	class	KX_KetsjiEngine*	m_KetsjiEngine;
	/** The scene to switch to. */
	STR_String					m_nextSceneName;
	
	// (Set Camera) Object
	class KX_Camera*			m_camera;

	/** Is this a valid scene? */
	class KX_Scene* FindScene(char* sceneName);
	/** Is this a valid camera? */
	class KX_Camera* FindCamera(char* cameraName);
	
 public:
	enum SCA_SceneActuatorMode
	{
		KX_SCENE_NODEF = 0,
		KX_SCENE_RESTART,
		KX_SCENE_SET_SCENE,
		KX_SCENE_SET_CAMERA,
		KX_SCENE_ADD_FRONT_SCENE,
		KX_SCENE_ADD_BACK_SCENE,
		KX_SCENE_REMOVE_SCENE,
		KX_SCENE_SUSPEND,
		KX_SCENE_RESUME,
		KX_SCENE_MAX
	};
	
	KX_SceneActuator(SCA_IObject* gameobj,
					 int mode,
					 KX_Scene* scene,
					 KX_KetsjiEngine* ketsjiEngine,
					 const STR_String& nextSceneName,
					 KX_Camera* camera);
	virtual ~KX_SceneActuator();

	virtual CValue* GetReplica();
	virtual void ProcessReplica();
	virtual bool UnlinkObject(SCA_IObject* clientobj);
	virtual void Relink(GEN_Map<GEN_HashedPtr, void*> *obj_map);

	virtual bool Update();
	
	/* --------------------------------------------------------------------- */
	/* Python interface ---------------------------------------------------- */
	/* --------------------------------------------------------------------- */

	/* 1. set                                                                */
	/* Removed */
	  
	/* 2. setUseRestart:                                                     */
	KX_PYMETHOD_DOC_VARARGS(KX_SceneActuator,SetUseRestart);
	/* 3. getUseRestart:                                                     */
	KX_PYMETHOD_DOC_NOARGS(KX_SceneActuator,GetUseRestart);
	/* 4. setScene:                                                          */
	KX_PYMETHOD_DOC_VARARGS(KX_SceneActuator,SetScene);
	/* 5. getScene:                                                          */
	KX_PYMETHOD_DOC_NOARGS(KX_SceneActuator,GetScene);
	/* 6. setCamera:                                                          */
	KX_PYMETHOD_DOC_O(KX_SceneActuator,SetCamera);
	/* 7. getCamera:                                                          */
	KX_PYMETHOD_DOC_NOARGS(KX_SceneActuator,GetCamera);
	
	static PyObject* pyattr_get_camera(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef);
	static int pyattr_set_camera(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value);

}; /* end of class KXSceneActuator */

#endif

