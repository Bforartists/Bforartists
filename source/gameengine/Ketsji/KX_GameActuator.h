 
//
// actuator for global game stuff
//
// $Id$
//
// ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 2
// of the License, or (at your option) any later version. The Blender
// Foundation also sells licenses for use in proprietary software under
// the Blender License.  See http://www.blender.org/BL/ for information
// about this.
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
// ***** END GPL/BL DUAL LICENSE BLOCK *****
//

#ifndef __KX_GAMEACTUATOR
#define __KX_GAMEACTUATOR

#include "SCA_IActuator.h"

class KX_GameActuator : public SCA_IActuator
{
	Py_Header;
protected:
	int							m_mode;
	bool						m_restart;
	STR_String					m_filename;
	STR_String					m_loadinganimationname;
	class KX_Scene*				m_scene;
	class KX_KetsjiEngine*		m_ketsjiengine;

 public:
	enum KX_GameActuatorMode
	{
		KX_GAME_NODEF = 0,
		KX_GAME_LOAD,
		KX_GAME_START,
		KX_GAME_RESTART,
		KX_GAME_QUIT,
		KX_GAME_MAX

	};

	KX_GameActuator(SCA_IObject* gameobj,
					 int mode,
					 const STR_String& filename,
					 const STR_String& loadinganimationname,
					 KX_Scene* scene,
					 KX_KetsjiEngine* ketsjiEngine,
					 PyTypeObject* T=&Type);
	virtual ~KX_GameActuator();

	virtual CValue* GetReplica();

	virtual bool Update(double curtime,double deltatime);
	
	/* --------------------------------------------------------------------- */
	/* Python interface ---------------------------------------------------- */
	/* --------------------------------------------------------------------- */

	virtual PyObject* _getattr(const STR_String& attr);
	KX_PYMETHOD_DOC(KX_GameActuator,GetFile);
	KX_PYMETHOD_DOC(KX_GameActuator,SetFile);
	
}; /* end of class KX_GameActuator */

#endif

