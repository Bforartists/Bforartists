/**
* global game stuff
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

#include "SCA_IActuator.h"
#include "KX_GameActuator.h"
//#include <iostream>
#include "KX_Scene.h"
#include "KX_KetsjiEngine.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

KX_GameActuator::KX_GameActuator(SCA_IObject *gameobj, 
								   int mode,
								   const STR_String& filename,
								   const STR_String& loadinganimationname,
								   KX_Scene* scene,
								   KX_KetsjiEngine* ketsjiengine,
								   PyTypeObject* T)
								   : SCA_IActuator(gameobj, T)
{
	m_mode = mode;
	m_filename = filename;
	m_loadinganimationname = loadinganimationname;
	m_scene = scene;
	m_ketsjiengine = ketsjiengine;
} /* End of constructor */



KX_GameActuator::~KX_GameActuator()
{ 
	// there's nothing to be done here, really....
} /* end of destructor */



CValue* KX_GameActuator::GetReplica()
{
	KX_GameActuator* replica = new KX_GameActuator(*this);
	replica->ProcessReplica();
	// this will copy properties and so on...
	CValue::AddDataToReplica(replica);
	
	return replica;
}



bool KX_GameActuator::Update(double curtime, double deltatime)
{
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();

	if (bNegativeEvent)
		return false; // do nothing on negative events

	switch (m_mode)
	{
	case KX_GAME_LOAD:
	case KX_GAME_START:
		{
			if (m_ketsjiengine)
			{
				STR_String exitstring = "start other game";
				m_ketsjiengine->RequestExit(KX_EXIT_REQUEST_START_OTHER_GAME);
				m_ketsjiengine->SetNameNextGame(m_filename);
				m_scene->AddDebugProperty((this)->GetParent(), exitstring);
			}

			break;
		}
	case KX_GAME_RESTART:
		{
			if (m_ketsjiengine)
			{
				STR_String exitstring = "restarting game";
				m_ketsjiengine->RequestExit(KX_EXIT_REQUEST_RESTART_GAME);
				m_scene->AddDebugProperty((this)->GetParent(), exitstring);
			}
			break;
		}
	case KX_GAME_QUIT:
		{
			if (m_ketsjiengine)
			{
				STR_String exitstring = "quiting game";
				m_ketsjiengine->RequestExit(KX_EXIT_REQUEST_QUIT_GAME);
				m_scene->AddDebugProperty((this)->GetParent(), exitstring);
			}
			break;
		}
	default:
		; /* do nothing? this is an internal error !!! */
	}
	
	return false;
}





/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_GameActuator::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
		0,
		"KX_SceneActuator",
		sizeof(KX_GameActuator),
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



PyParentObject KX_GameActuator::Parents[] =
{
	&KX_GameActuator::Type,
		&SCA_IActuator::Type,
		&SCA_ILogicBrick::Type,
		&CValue::Type,
		NULL
};



PyMethodDef KX_GameActuator::Methods[] =
{
	{NULL,NULL} //Sentinel
};



PyObject* KX_GameActuator::_getattr(char* attr)
{
	_getattr_up(SCA_IActuator);
}


