/**
 * KX_CDActuator.h
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

#ifndef __KX_CDACTUATOR
#define __KX_CDACTUATOR

#include "SCA_IActuator.h"
#include "SND_CDObject.h"

class KX_CDActuator : public SCA_IActuator
{
	Py_Header;
	bool					m_lastEvent;
	bool					m_isplaying;
	/* just some handles to the audio-data... */
	class SND_Scene*		m_soundscene;
	int						m_track;
	float					m_gain;
	short					m_startFrame;
	short					m_endFrame;

public:
	enum KX_CDACT_TYPE
	{
			KX_CDACT_NODEF = 0,
			KX_CDACT_PLAY_ALL,
			KX_CDACT_PLAY_TRACK,
			KX_CDACT_LOOP_TRACK,
			KX_CDACT_VOLUME,
			KX_CDACT_STOP,
			KX_CDACT_PAUSE,
			KX_CDACT_RESUME,
			KX_SOUNDACT_MAX
	};

	KX_CDACT_TYPE			m_type;

	KX_CDActuator(SCA_IObject* gameobject,
				  SND_Scene* soundscene,
				  KX_CDACT_TYPE type,
				  int track,
				  short start,
				  short end,
				  PyTypeObject* T=&Type);

	~KX_CDActuator();

	virtual bool Update();

	CValue* GetReplica();

	/* -------------------------------------------------------------------- */
	/* Python interface --------------------------------------------------- */
	/* -------------------------------------------------------------------- */

	virtual PyObject*  py_getattro(PyObject *attr);
	virtual int py_setattro(PyObject *attr, PyObject *value);

	// Deprecated ----->
	KX_PYMETHOD_VARARGS(KX_CDActuator,SetGain);
	KX_PYMETHOD_VARARGS(KX_CDActuator,GetGain);
	// <-----

	KX_PYMETHOD_DOC_NOARGS(KX_CDActuator, startCD);
	KX_PYMETHOD_DOC_NOARGS(KX_CDActuator, pauseCD);
	KX_PYMETHOD_DOC_NOARGS(KX_CDActuator, resumeCD);
	KX_PYMETHOD_DOC_NOARGS(KX_CDActuator, stopCD);
	KX_PYMETHOD_DOC_NOARGS(KX_CDActuator, playAll);
	KX_PYMETHOD_DOC_O(KX_CDActuator, playTrack);

	static int pyattr_setGain(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef);


};

#endif //__KX_CDACTUATOR

