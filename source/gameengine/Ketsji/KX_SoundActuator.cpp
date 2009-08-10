/**
 * KX_SoundActuator.cpp
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
 *
 */

#include "KX_SoundActuator.h"
#include "SND_SoundObject.h"
#include "KX_GameObject.h"
#include "SND_SoundObject.h"
#include "SND_Scene.h" // needed for replication
#include "KX_PyMath.h" // needed for PyObjectFrom()
#include <iostream>

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */
KX_SoundActuator::KX_SoundActuator(SCA_IObject* gameobj,
								   AUD_Sound* sound,
								   float volume,
								   float pitch,
								   bool is3d,
								   KX_3DSoundSettings settings,
								   KX_SOUNDACT_TYPE type)//,
								   : SCA_IActuator(gameobj)
{
	m_sound = sound;
	m_volume = volume;
	m_pitch = pitch;
	m_is3d = is3d;
	m_3d = settings;
	m_handle = NULL;
	m_type = type;
	m_isplaying = false;
}



KX_SoundActuator::~KX_SoundActuator()
{
	if(m_handle)
		AUD_stop(m_handle);
}

void KX_SoundActuator::play()
{
	if(m_handle)
		AUD_stop(m_handle);

	if(!m_sound)
		return;

	// this is the sound that will be played and not deleted afterwards
	AUD_Sound* sound = m_sound;
	// this sounds are for temporary stacked sounds, will be deleted if not NULL
	AUD_Sound* sound2 = NULL;
	AUD_Sound* sound3 = NULL;

	switch (m_type)
	{
	case KX_SOUNDACT_LOOPBIDIRECTIONAL:
	case KX_SOUNDACT_LOOPBIDIRECTIONAL_STOP:
		// create a ping pong sound on sound2 stacked on the orignal sound
		sound2 = AUD_pingpongSound(sound);
		// create a loop sound on sound3 stacked on the pingpong sound and let that one play (save it to sound)
		sound = sound3 = AUD_loopSound(sound2);
		break;
	case KX_SOUNDACT_LOOPEND:
	case KX_SOUNDACT_LOOPSTOP:
		// create a loop sound on sound2 stacked on the pingpong sound and let that one play (save it to sound)
		sound = sound2 = AUD_loopSound(sound);
		break;
	case KX_SOUNDACT_PLAYSTOP:
	case KX_SOUNDACT_PLAYEND:
	default:
		break;
	}

	if(m_is3d)
	{
		// sound shall be played 3D
		m_handle = AUD_play3D(sound, 0);

		AUD_set3DSourceSetting(m_handle, AUD_3DSS_MAX_GAIN, m_3d.max_gain);
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_MIN_GAIN, m_3d.min_gain);
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_REFERENCE_DISTANCE, m_3d.reference_distance);
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_MAX_DISTANCE, m_3d.max_distance);
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_ROLLOFF_FACTOR, m_3d.rolloff_factor);
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_CONE_INNER_ANGLE, m_3d.cone_inner_angle);
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_CONE_OUTER_ANGLE, m_3d.cone_outer_angle);
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_CONE_OUTER_GAIN, m_3d.cone_outer_gain);
	}
	else
		m_handle = AUD_play(sound, 0);

	AUD_setSoundPitch(m_handle, m_pitch);
	AUD_setSoundVolume(m_handle, m_volume);
	m_isplaying = true;

	// now we unload the pingpong and loop sounds, as we don't need them anymore
	// the started sound will continue playing like it was created, don't worry!
	if(sound3)
		AUD_unload(sound3);
	if(sound2)
		AUD_unload(sound2);
}

CValue* KX_SoundActuator::GetReplica()
{
	KX_SoundActuator* replica = new KX_SoundActuator(*this);
	replica->ProcessReplica();
	return replica;
};

void KX_SoundActuator::ProcessReplica()
{
	SCA_IActuator::ProcessReplica();
	m_handle = 0;
}

bool KX_SoundActuator::Update(double curtime, bool frame)
{
	if (!frame)
		return true;
	bool result = false;

	// do nothing on negative events, otherwise sounds are played twice!
	bool bNegativeEvent = IsNegativeEvent();
	bool bPositiveEvent = m_posevent;
	
	RemoveAllEvents();

	if(!m_sound)
		return false;

	// actual audio device playing state
	bool isplaying = AUD_getStatus(m_handle) == AUD_STATUS_PLAYING;

	if (bNegativeEvent)
	{
		// here must be a check if it is still playing
		if (m_isplaying && isplaying)
		{
			switch (m_type)
			{
			case KX_SOUNDACT_PLAYSTOP:
			case KX_SOUNDACT_LOOPSTOP:
			case KX_SOUNDACT_LOOPBIDIRECTIONAL_STOP:
				{
					// stop immediately
					AUD_stop(m_handle);
					break;
				}
			case KX_SOUNDACT_PLAYEND:
				{
					// do nothing, sound will stop anyway when it's finished
					break;
				}
			case KX_SOUNDACT_LOOPEND:
			case KX_SOUNDACT_LOOPBIDIRECTIONAL:
				{
					// stop the looping so that the sound stops when it finished
					AUD_stopLoop(m_handle);
					break;
				}
			default:
				// implement me !!
				break;
			}
		}
		// remember that we tried to stop the actuator
		m_isplaying = false;
	}
	
#if 1
	// Warning: when de-activating the actuator, after a single negative event this runs again with...
	// m_posevent==false && m_posevent==false, in this case IsNegativeEvent() returns false 
	// and assumes this is a positive event.
	// check that we actually have a positive event so as not to play sounds when being disabled.
	else if(bPositiveEvent) { // <- added since 2.49
#else
	else {	// <- works in most cases except a loop-end sound will never stop unless
			// the negative pulse is done continuesly
#endif
		if (!m_isplaying)
			play();
	}
	// verify that the sound is still playing
	isplaying = AUD_getStatus(m_handle) == AUD_STATUS_PLAYING ? true : false;

	if (isplaying)
	{
		if(m_is3d)
		{
			AUD_3DData data;
			float f;
			((KX_GameObject*)this->GetParent())->NodeGetWorldPosition().getValue(data.position);
			((KX_GameObject*)this->GetParent())->GetLinearVelocity().getValue(data.velocity);
			((KX_GameObject*)this->GetParent())->NodeGetWorldOrientation().getValue3x3(data.orientation);

			/*
			 * The 3D data from blender has to be transformed for OpenAL:
			 *  - In blender z is up and y is forwards
			 *  - In OpenAL y is up and z is backwards
			 * We have to do that for all 5 vectors.
			 */
			f = data.position[1];
			data.position[1] = data.position[2];
			data.position[2] = -f;

			f = data.velocity[1];
			data.velocity[1] = data.velocity[2];
			data.velocity[2] = -f;

			f = data.orientation[1];
			data.orientation[1] = data.orientation[2];
			data.orientation[2] = -f;

			f = data.orientation[4];
			data.orientation[4] = data.orientation[5];
			data.orientation[5] = -f;

			f = data.orientation[7];
			data.orientation[7] = data.orientation[8];
			data.orientation[8] = -f;

			AUD_update3DSource(m_handle, &data);
		}
		result = true;
	}
	else
	{
		m_isplaying = false;
		result = false;
	}
	return result;
}




/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */



/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_SoundActuator::Type = {
	PyVarObject_HEAD_INIT(NULL, 0)
	"KX_SoundActuator",
	sizeof(PyObjectPlus_Proxy),
	0,
	py_base_dealloc,
	0,
	0,
	0,
	0,
	py_base_repr,
	0,0,0,0,0,0,0,0,0,
	Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
	0,0,0,0,0,0,0,
	Methods,
	0,
	0,
	&SCA_IActuator::Type,
	0,0,0,0,0,0,
	py_base_new
};

PyMethodDef KX_SoundActuator::Methods[] = {
	// Deprecated ----->
	{"setGain",(PyCFunction) KX_SoundActuator::sPySetGain,METH_VARARGS,NULL},
	{"getGain",(PyCFunction) KX_SoundActuator::sPyGetGain,METH_NOARGS,NULL},
	{"setPitch",(PyCFunction) KX_SoundActuator::sPySetPitch,METH_VARARGS,NULL},
	{"getPitch",(PyCFunction) KX_SoundActuator::sPyGetPitch,METH_NOARGS,NULL},
	{"setRollOffFactor",(PyCFunction) KX_SoundActuator::sPySetRollOffFactor,METH_VARARGS,NULL},
	{"getRollOffFactor",(PyCFunction) KX_SoundActuator::sPyGetRollOffFactor,METH_NOARGS,NULL},
	{"setType",(PyCFunction) KX_SoundActuator::sPySetType,METH_VARARGS,NULL},
	{"getType",(PyCFunction) KX_SoundActuator::sPyGetType,METH_NOARGS,NULL},
	// <-----

	KX_PYMETHODTABLE_NOARGS(KX_SoundActuator, startSound),
	KX_PYMETHODTABLE_NOARGS(KX_SoundActuator, pauseSound),
	KX_PYMETHODTABLE_NOARGS(KX_SoundActuator, stopSound),
	{NULL,NULL,NULL,NULL} //Sentinel
};

PyAttributeDef KX_SoundActuator::Attributes[] = {
	KX_PYATTRIBUTE_RW_FUNCTION("volume", KX_SoundActuator, pyattr_get_gain, pyattr_set_gain),
	KX_PYATTRIBUTE_RW_FUNCTION("pitch", KX_SoundActuator, pyattr_get_pitch, pyattr_set_pitch),
	KX_PYATTRIBUTE_RW_FUNCTION("rollOffFactor", KX_SoundActuator, pyattr_get_rollOffFactor, pyattr_set_rollOffFactor),
	KX_PYATTRIBUTE_ENUM_RW("mode",KX_SoundActuator::KX_SOUNDACT_NODEF+1,KX_SoundActuator::KX_SOUNDACT_MAX-1,false,KX_SoundActuator,m_type),
	{ NULL }	//Sentinel
};

/* Methods ----------------------------------------------------------------- */
KX_PYMETHODDEF_DOC_NOARGS(KX_SoundActuator, startSound,
"startSound()\n"
"\tStarts the sound.\n")
{
	switch(AUD_getStatus(m_handle))
	{
	case AUD_STATUS_PLAYING:
		break;
	case AUD_STATUS_PAUSED:
		AUD_resume(m_handle);
		break;
	default:
		play();
	}
	Py_RETURN_NONE;
}

KX_PYMETHODDEF_DOC_NOARGS(KX_SoundActuator, pauseSound,
"pauseSound()\n"
"\tPauses the sound.\n")
{
	AUD_pause(m_handle);
	Py_RETURN_NONE;
}

KX_PYMETHODDEF_DOC_NOARGS(KX_SoundActuator, stopSound,
"stopSound()\n"
"\tStops the sound.\n")
{
	AUD_stop(m_handle);
	Py_RETURN_NONE;
}

/* Atribute setting and getting -------------------------------------------- */

PyObject* KX_SoundActuator::pyattr_get_gain(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_SoundActuator * actuator = static_cast<KX_SoundActuator *> (self);
	float gain = actuator->m_volume;

	PyObject* result = PyFloat_FromDouble(gain);

	return result;
}

PyObject* KX_SoundActuator::pyattr_get_pitch(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_SoundActuator * actuator = static_cast<KX_SoundActuator *> (self);
	float pitch = actuator->m_pitch;

	PyObject* result = PyFloat_FromDouble(pitch);

	return result;
}

PyObject* KX_SoundActuator::pyattr_get_rollOffFactor(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_SoundActuator * actuator = static_cast<KX_SoundActuator *> (self);
	float rollofffactor = actuator->m_3d.rolloff_factor;
	PyObject* result = PyFloat_FromDouble(rollofffactor);

	return result;
}

int KX_SoundActuator::pyattr_set_gain(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	float gain = 1.0;
	KX_SoundActuator * actuator = static_cast<KX_SoundActuator *> (self);
	if (!PyArg_Parse(value, "f", &gain))
		return PY_SET_ATTR_FAIL;

	actuator->m_volume = gain;
	if(actuator->m_handle)
		AUD_setSoundVolume(actuator->m_handle, gain);

	return PY_SET_ATTR_SUCCESS;
}

int KX_SoundActuator::pyattr_set_pitch(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	float pitch = 1.0;
	KX_SoundActuator * actuator = static_cast<KX_SoundActuator *> (self);
	if (!PyArg_Parse(value, "f", &pitch))
		return PY_SET_ATTR_FAIL;

	actuator->m_pitch = pitch;
	if(actuator->m_handle)
		AUD_setSoundPitch(actuator->m_handle, pitch);

	return PY_SET_ATTR_SUCCESS;
}

int KX_SoundActuator::pyattr_set_rollOffFactor(void *self, const struct KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	KX_SoundActuator * actuator = static_cast<KX_SoundActuator *> (self);
	float rollofffactor = 1.0;
	if (!PyArg_Parse(value, "f", &rollofffactor))
		return PY_SET_ATTR_FAIL;

	actuator->m_3d.rolloff_factor = rollofffactor;
	if(actuator->m_handle)
		AUD_set3DSourceSetting(actuator->m_handle, AUD_3DSS_ROLLOFF_FACTOR, rollofffactor);

	return PY_SET_ATTR_SUCCESS;
}

PyObject* KX_SoundActuator::PySetGain(PyObject* args)
{
	ShowDeprecationWarning("setGain()", "the volume property");
	float gain = 1.0;
	if (!PyArg_ParseTuple(args, "f:setGain", &gain))
		return NULL;

	m_volume = gain;
	if(m_handle)
		AUD_setSoundVolume(m_handle, gain);

	Py_RETURN_NONE;
}



PyObject* KX_SoundActuator::PyGetGain()
{
	ShowDeprecationWarning("getGain()", "the volume property");
	float gain = m_volume;
	PyObject* result = PyFloat_FromDouble(gain);

	return result;
}



PyObject* KX_SoundActuator::PySetPitch(PyObject* args)
{
	ShowDeprecationWarning("setPitch()", "the pitch property");
	float pitch = 1.0;
	if (!PyArg_ParseTuple(args, "f:setPitch", &pitch))
		return NULL;

	m_pitch = pitch;
	if(m_handle)
		AUD_setSoundPitch(m_handle, pitch);

	Py_RETURN_NONE;
}



PyObject* KX_SoundActuator::PyGetPitch()
{
	ShowDeprecationWarning("getPitch()", "the pitch property");
	float pitch = m_pitch;
	PyObject* result = PyFloat_FromDouble(pitch);

	return result;
}



PyObject* KX_SoundActuator::PySetRollOffFactor(PyObject* args)
{
	ShowDeprecationWarning("setRollOffFactor()", "the rollOffFactor property");
	float rollofffactor = 1.0;
	if (!PyArg_ParseTuple(args, "f:setRollOffFactor", &rollofffactor))
		return NULL;

	m_3d.rolloff_factor = rollofffactor;
	if(m_handle)
		AUD_set3DSourceSetting(m_handle, AUD_3DSS_ROLLOFF_FACTOR, rollofffactor);

	Py_RETURN_NONE;
}



PyObject* KX_SoundActuator::PyGetRollOffFactor()
{
	ShowDeprecationWarning("getRollOffFactor()", "the rollOffFactor property");
	float rollofffactor = m_3d.rolloff_factor;
	PyObject* result = PyFloat_FromDouble(rollofffactor);

	return result;
}



PyObject* KX_SoundActuator::PySetType(PyObject* args)
{
	int typeArg;
	ShowDeprecationWarning("setType()", "the mode property");

	if (!PyArg_ParseTuple(args, "i:setType", &typeArg)) {
		return NULL;
	}

	if ( (typeArg > KX_SOUNDACT_NODEF)
	  && (typeArg < KX_SOUNDACT_MAX) ) {
		m_type = (KX_SOUNDACT_TYPE) typeArg;
	}

	Py_RETURN_NONE;
}

PyObject* KX_SoundActuator::PyGetType()
{
	ShowDeprecationWarning("getType()", "the mode property");
	return PyLong_FromSsize_t(m_type);
}
// <-----

