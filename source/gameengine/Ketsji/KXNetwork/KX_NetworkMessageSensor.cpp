/**
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
 * Ketsji Logic Extenstion: Network Message Sensor generic implementation
 */

#include "KX_NetworkMessageSensor.h"
#include "KX_NetworkEventManager.h"
#include "NG_NetworkMessage.h"
#include "NG_NetworkScene.h"
#include "NG_NetworkObject.h"
#include "SCA_IObject.h"	
#include "InputParser.h"
#include "ListValue.h"
#include "StringValue.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

#ifdef NAN_NET_DEBUG
  #include <iostream>
#endif

KX_NetworkMessageSensor::KX_NetworkMessageSensor(
	class KX_NetworkEventManager* eventmgr,	// our eventmanager
	class NG_NetworkScene *NetworkScene,	// our scene
	SCA_IObject* gameobj,					// the sensor controlling object
	const STR_String &subject
) :
    SCA_ISensor(gameobj,eventmgr),
    m_Networkeventmgr(eventmgr),
    m_NetworkScene(NetworkScene),
    m_subject(subject),
    m_frame_message_count (0),
    m_BodyList(NULL),
    m_SubjectList(NULL)
{
	Init();
}

void KX_NetworkMessageSensor::Init()
{
    m_IsUp = false;
}

KX_NetworkMessageSensor::~KX_NetworkMessageSensor()
{
}

CValue* KX_NetworkMessageSensor::GetReplica() {
	// This is the standard sensor implementation of GetReplica
	// There may be more network message sensor specific stuff to do here.
	CValue* replica = new KX_NetworkMessageSensor(*this);

	if (replica == NULL) return NULL;
	replica->ProcessReplica();

	return replica;
}

// Return true only for flank (UP and DOWN)
bool KX_NetworkMessageSensor::Evaluate()
{
	bool result = false;
	bool WasUp = m_IsUp;

	m_IsUp = false;

	if (m_BodyList) {
		m_BodyList->Release();
		m_BodyList = NULL;
	}

	if (m_SubjectList) {
		m_SubjectList->Release();
		m_SubjectList = NULL;
	}

	STR_String& toname=GetParent()->GetName();
	STR_String& subject = this->m_subject;

	vector<NG_NetworkMessage*> messages =
		m_NetworkScene->FindMessages(toname,"",subject,true);

	m_frame_message_count = messages.size();

	if (!messages.empty()) {
#ifdef NAN_NET_DEBUG
		printf("KX_NetworkMessageSensor found one or more messages\n");
#endif
		m_IsUp = true;
		m_BodyList = new CListValue();
		m_SubjectList = new CListValue();
	}

	vector<NG_NetworkMessage*>::iterator mesit;
	for (mesit=messages.begin();mesit!=messages.end();mesit++)
	{
		// save the body
		const STR_String& body = (*mesit)->GetMessageText();
		// save the subject
		const STR_String& messub = (*mesit)->GetSubject();
#ifdef NAN_NET_DEBUG
		if (body) {
			cout << "body [" << body << "]\n";
		}
#endif
		m_BodyList->Add(new CStringValue(body,"body"));
		// Store Subject
		m_SubjectList->Add(new CStringValue(messub,"subject"));

		// free the message
		(*mesit)->Release();
	}
	messages.clear();

	result = (WasUp != m_IsUp);

	// Return always true if a message was received otherwise we can loose messages
	if (m_IsUp)
		return true;
	// Is it usefull to return also true when the first frame without a message?? 
	// This will cause a fast on/off cycle that seems useless!
	return result;
}

// return true for being up (no flank needed)
bool KX_NetworkMessageSensor::IsPositiveTrigger()
{
//	printf("KX_NetworkMessageSensor IsPositiveTrigger\n");
	//attempt to fix [ #3809 ] IPO Actuator does not work with some Sensors
	//a better solution is to properly introduce separate Edge and Level triggering concept

	return m_IsUp;
}

/* --------------------------------------------------------------------- */
/* Python interface ---------------------------------------------------- */
/* --------------------------------------------------------------------- */

/* Integration hooks --------------------------------------------------- */
PyTypeObject KX_NetworkMessageSensor::Type = {
#if (PY_VERSION_HEX >= 0x02060000)
	PyVarObject_HEAD_INIT(NULL, 0)
#else
	/* python 2.5 and below */
	PyObject_HEAD_INIT( NULL )  /* required py macro */
	0,                          /* ob_size */
#endif
	"KX_NetworkMessageSensor",
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
	&SCA_ISensor::Type,
	0,0,0,0,0,0,
	py_base_new
};

PyMethodDef KX_NetworkMessageSensor::Methods[] = {
	// Deprecated ----->
	{"setSubjectFilterText", (PyCFunction)
		KX_NetworkMessageSensor::sPySetSubjectFilterText, METH_O,
		(PY_METHODCHAR)SetSubjectFilterText_doc},
	{"getFrameMessageCount", (PyCFunction)
		KX_NetworkMessageSensor::sPyGetFrameMessageCount, METH_NOARGS,
		(PY_METHODCHAR)GetFrameMessageCount_doc},
	{"getBodies", (PyCFunction)
		KX_NetworkMessageSensor::sPyGetBodies, METH_NOARGS,
		(PY_METHODCHAR)GetBodies_doc},
	{"getSubject", (PyCFunction)
		KX_NetworkMessageSensor::sPyGetSubject, METH_NOARGS,
		(PY_METHODCHAR)GetSubject_doc},
	{"getSubjects", (PyCFunction)
		KX_NetworkMessageSensor::sPyGetSubjects, METH_NOARGS,
		(PY_METHODCHAR)GetSubjects_doc},
	// <-----
	{NULL,NULL} //Sentinel
};

PyAttributeDef KX_NetworkMessageSensor::Attributes[] = {
	KX_PYATTRIBUTE_STRING_RW("subject", 0, 100, false, KX_NetworkMessageSensor, m_subject),
	KX_PYATTRIBUTE_INT_RO("frameMessageCount", KX_NetworkMessageSensor, m_frame_message_count),
	KX_PYATTRIBUTE_RO_FUNCTION("bodies", KX_NetworkMessageSensor, pyattr_get_bodies),
	KX_PYATTRIBUTE_RO_FUNCTION("subjects", KX_NetworkMessageSensor, pyattr_get_subjects),
	{ NULL }	//Sentinel
};

PyObject* KX_NetworkMessageSensor::pyattr_get_bodies(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_NetworkMessageSensor *self = static_cast<KX_NetworkMessageSensor*>(self_v);
	if (self->m_BodyList) {
		return self->m_BodyList->GetProxy();
	} else {
		return (new CListValue())->NewProxy(true);
	}
}

PyObject* KX_NetworkMessageSensor::pyattr_get_subjects(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	KX_NetworkMessageSensor *self = static_cast<KX_NetworkMessageSensor*>(self_v);
	if (self->m_SubjectList) {
		return self->m_SubjectList->GetProxy();
	} else {
		return (new CListValue())->NewProxy(true);
	}
}

// Deprecated ----->
// 1. Set the message subject that this sensor listens for
const char KX_NetworkMessageSensor::SetSubjectFilterText_doc[] = 
"\tsetSubjectFilterText(value)\n"
"\tChange the message subject text that this sensor is listening to.\n";

PyObject* KX_NetworkMessageSensor::PySetSubjectFilterText(PyObject* value)
{
	ShowDeprecationWarning("setSubjectFilterText()", "subject");
	char* Subject = _PyUnicode_AsString(value);
	if (Subject==NULL) {
		PyErr_SetString(PyExc_TypeError, "sensor.tsetSubjectFilterText(string): KX_NetworkMessageSensor, expected a string message");
		return NULL;
	}
	
	m_subject = Subject;
	Py_RETURN_NONE;
}

// 2. Get the number of messages received since the last frame
const char KX_NetworkMessageSensor::GetFrameMessageCount_doc[] =
"\tgetFrameMessageCount()\n"
"\tGet the number of messages received since the last frame.\n";

PyObject* KX_NetworkMessageSensor::PyGetFrameMessageCount()
{
	ShowDeprecationWarning("getFrameMessageCount()", "frameMessageCount");
	return PyLong_FromSsize_t(long(m_frame_message_count));
}

// 3. Get the message bodies
const char KX_NetworkMessageSensor::GetBodies_doc[] =
"\tgetBodies()\n"
"\tGet the list of message bodies.\n";

PyObject* KX_NetworkMessageSensor::PyGetBodies()
{
	ShowDeprecationWarning("getBodies()", "bodies");
	if (m_BodyList) {
		return m_BodyList->GetProxy();
	} else {
		return (new CListValue())->NewProxy(true);
	}
}

// 4. Get the message subject: field of the message sensor
const char KX_NetworkMessageSensor::GetSubject_doc[] =
"\tgetSubject()\n"
"\tGet the subject: field of the message sensor.\n";

PyObject* KX_NetworkMessageSensor::PyGetSubject()
{
	ShowDeprecationWarning("getSubject()", "subject");
	return PyUnicode_FromString(m_subject ? m_subject : "");
}

// 5. Get the message subjects
const char KX_NetworkMessageSensor::GetSubjects_doc[] =
"\tgetSubjects()\n"
"\tGet list of message subjects.\n";

PyObject* KX_NetworkMessageSensor::PyGetSubjects()
{
	ShowDeprecationWarning("getSubjects()", "subjects");
	if (m_SubjectList) {
		return m_SubjectList->GetProxy();
	} else {
		return (new CListValue())->NewProxy(true);
	}
}
// <----- Deprecated
