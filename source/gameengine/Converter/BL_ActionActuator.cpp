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
*/

#if defined (__sgi)
#include <math.h>
#else
#include <cmath>
#endif

#include "SCA_LogicManager.h"
#include "BL_ActionActuator.h"
#include "BL_ArmatureObject.h"
#include "BL_SkinDeformer.h"
#include "KX_GameObject.h"
#include "STR_HashedString.h"
#include "DNA_nla_types.h"
#include "BKE_action.h"
#include "DNA_action_types.h"
#include "DNA_armature_types.h"
#include "MEM_guardedalloc.h"
#include "BLI_blenlib.h"
#include "BLI_arithb.h"
#include "MT_Matrix4x4.h"
#include "BKE_utildefines.h"
#include "FloatValue.h"
#include "PyObjectPlus.h"
#include "blendef.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

BL_ActionActuator::~BL_ActionActuator()
{
	if (m_pose)
		game_free_pose(m_pose);
	if (m_userpose)
		game_free_pose(m_userpose);
	if (m_blendpose)
		game_free_pose(m_blendpose);
}

void BL_ActionActuator::ProcessReplica(){
//	bPose *oldpose = m_pose;
//	bPose *oldbpose = m_blendpose;
	
	m_pose = NULL;
	m_blendpose = NULL;
	m_localtime=m_startframe;
	m_lastUpdate=-1;
	
}

void BL_ActionActuator::SetBlendTime (float newtime){
	m_blendframe = newtime;
}

CValue* BL_ActionActuator::GetReplica() {
	BL_ActionActuator* replica = new BL_ActionActuator(*this);//m_float,GetName());
	replica->ProcessReplica();
	
	// this will copy properties and so on...
	CValue::AddDataToReplica(replica);
	return replica;
}

bool BL_ActionActuator::ClampLocalTime()
{
	if (m_startframe < m_endframe)
	{
		if (m_localtime < m_startframe)
		{
			m_localtime = m_startframe;
			return true;
		} 
		else if (m_localtime > m_endframe)
		{
			m_localtime = m_endframe;
			return true;
		}
	} else {
		if (m_localtime > m_startframe)
		{
			m_localtime = m_startframe;
			return true;
		}
		else if (m_localtime < m_endframe)
		{
			m_localtime = m_endframe;
			return true;
		}
	}
	return false;
}

void BL_ActionActuator::SetStartTime(float curtime)
{
	float direction = m_startframe < m_endframe ? 1.0 : -1.0;
	
	if (!(m_flag & ACT_FLAG_REVERSE))
		m_starttime = curtime - direction*(m_localtime - m_startframe)/KX_KetsjiEngine::GetAnimFrameRate();
	else
		m_starttime = curtime - direction*(m_endframe - m_localtime)/KX_KetsjiEngine::GetAnimFrameRate();
}

void BL_ActionActuator::SetLocalTime(float curtime)
{
	float delta_time = (curtime - m_starttime)*KX_KetsjiEngine::GetAnimFrameRate();
	
	if (m_endframe < m_startframe)
		delta_time = -delta_time;

	if (!(m_flag & ACT_FLAG_REVERSE))
		m_localtime = m_startframe + delta_time;
	else
		m_localtime = m_endframe - delta_time;
}


bool BL_ActionActuator::Update(double curtime, bool frame)
{
	bool bNegativeEvent = false;
	bool bPositiveEvent = false;
	bool keepgoing = true;
	bool wrap = false;
	bool apply=true;
	int	priority;
	float newweight;

	curtime -= KX_KetsjiEngine::GetSuspendedDelta();
	
	// result = true if animation has to be continued, false if animation stops
	// maybe there are events for us in the queue !
	if (frame)
	{
		for (vector<CValue*>::iterator i=m_events.begin(); !(i==m_events.end());i++)
		{
			if ((*i)->GetNumber() == 0.0f)
				bNegativeEvent = true;
			else
				bPositiveEvent= true;
			(*i)->Release();
		
		}
		m_events.clear();
		
		if (bPositiveEvent)
			m_flag |= ACT_FLAG_ACTIVE;
		
		if (bNegativeEvent)
		{
			// dont continue where we left off when restarting
			if (m_end_reset) {
				m_flag &= ~ACT_FLAG_LOCKINPUT;
			}
			
			if (!(m_flag & ACT_FLAG_ACTIVE))
				return false;
			m_flag &= ~ACT_FLAG_ACTIVE;
		}
	}
	
	/*	We know that action actuators have been discarded from all non armature objects:
	if we're being called, we're attached to a BL_ArmatureObject */
	BL_ArmatureObject *obj = (BL_ArmatureObject*)GetParent();
	float length = m_endframe - m_startframe;
	
	priority = m_priority;
	
	/* Determine pre-incrementation behaviour and set appropriate flags */
	switch (m_playtype){
	case ACT_ACTION_MOTION:
		if (bNegativeEvent){
			keepgoing=false;
			apply=false;
		};
		break;
	case ACT_ACTION_FROM_PROP:
		if (bNegativeEvent){
			apply=false;
			keepgoing=false;
		}
		break;
	case ACT_ACTION_LOOP_END:
		if (bPositiveEvent){
			if (!(m_flag & ACT_FLAG_LOCKINPUT)){
				m_flag &= ~ACT_FLAG_KEYUP;
				m_flag &= ~ACT_FLAG_REVERSE;
				m_flag |= ACT_FLAG_LOCKINPUT;
				m_localtime = m_startframe;
				m_starttime = curtime;
			}
		}
		if (bNegativeEvent){
			m_flag |= ACT_FLAG_KEYUP;
		}
		break;
	case ACT_ACTION_LOOP_STOP:
		if (bPositiveEvent){
			if (!(m_flag & ACT_FLAG_LOCKINPUT)){
				m_flag &= ~ACT_FLAG_REVERSE;
				m_flag &= ~ACT_FLAG_KEYUP;
				m_flag |= ACT_FLAG_LOCKINPUT;
				SetStartTime(curtime);
			}
		}
		if (bNegativeEvent){
			m_flag |= ACT_FLAG_KEYUP;
			m_flag &= ~ACT_FLAG_LOCKINPUT;
			keepgoing=false;
			apply=false;
		}
		break;
	case ACT_ACTION_FLIPPER:
		if (bPositiveEvent){
			if (!(m_flag & ACT_FLAG_LOCKINPUT)){
				m_flag &= ~ACT_FLAG_REVERSE;
				m_flag |= ACT_FLAG_LOCKINPUT;
				SetStartTime(curtime);
			}
		}
		else if (bNegativeEvent){
			m_flag |= ACT_FLAG_REVERSE;
			m_flag &= ~ACT_FLAG_LOCKINPUT;
			SetStartTime(curtime);
		}
		break;
	case ACT_ACTION_PLAY:
		if (bPositiveEvent){
			if (!(m_flag & ACT_FLAG_LOCKINPUT)){
				m_flag &= ~ACT_FLAG_REVERSE;
				m_localtime = m_starttime;
				m_starttime = curtime;
				m_flag |= ACT_FLAG_LOCKINPUT;
			}
		}
		break;
	default:
		break;
	}
	
	/* Perform increment */
	if (keepgoing){
		if (m_playtype == ACT_ACTION_MOTION){
			MT_Point3	newpos;
			MT_Point3	deltapos;
			
			newpos = obj->NodeGetWorldPosition();
			
			/* Find displacement */
			deltapos = newpos-m_lastpos;
			m_localtime += (length/m_stridelength) * deltapos.length();
			m_lastpos = newpos;
		}
		else{
			SetLocalTime(curtime);
		}
	}
	
	/* Check if a wrapping response is needed */
	if (length){
		if (m_localtime < m_startframe || m_localtime > m_endframe)
		{
			m_localtime = m_startframe + fmod(m_localtime, length);
			wrap = true;
		}
	}
	else
		m_localtime = m_startframe;
	
	/* Perform post-increment tasks */
	switch (m_playtype){
	case ACT_ACTION_FROM_PROP:
		{
			CValue* propval = GetParent()->GetProperty(m_propname);
			if (propval)
				m_localtime = propval->GetNumber();
			
			if (bNegativeEvent){
				keepgoing=false;
			}
		}
		break;
	case ACT_ACTION_MOTION:
		break;
	case ACT_ACTION_LOOP_STOP:
		break;
	case ACT_ACTION_FLIPPER:
		if (wrap){
			if (!(m_flag & ACT_FLAG_REVERSE)){
				m_localtime=m_endframe;
				//keepgoing = false;
			}
			else {
				m_localtime=m_startframe;
				keepgoing = false;
			}
		}
		break;
	case ACT_ACTION_LOOP_END:
		if (wrap){
			if (m_flag & ACT_FLAG_KEYUP){
				keepgoing = false;
				m_localtime = m_endframe;
				m_flag &= ~ACT_FLAG_LOCKINPUT;
			}
			SetStartTime(curtime);
		}
		break;
	case ACT_ACTION_PLAY:
		if (wrap){
			m_localtime = m_endframe;
			keepgoing = false;
			m_flag &= ~ACT_FLAG_LOCKINPUT;
		}
		break;
	default:
		keepgoing = false;
		break;
	}
	
	/* Set the property if its defined */
	if (m_framepropname[0] != '\0') {
		CValue* propowner = GetParent();
		CValue* oldprop = propowner->GetProperty(m_framepropname);
		CValue* newval = new CFloatValue(m_localtime);
		if (oldprop) {
			oldprop->SetValue(newval);
		} else {
			propowner->SetProperty(m_framepropname, newval);
		}
		newval->Release();
	}
	
	if (bNegativeEvent)
		m_blendframe=0.0;
	
	/* Apply the pose if necessary*/
	if (apply){

		/* Priority test */
		if (obj->SetActiveAction(this, priority, curtime)){
			
			/* Get the underlying pose from the armature */
			obj->GetPose(&m_pose);
			
			/* Override the necessary channels with ones from the action */
			extract_pose_from_action(m_pose, m_action, m_localtime);

			/* Perform the user override (if any) */
			if (m_userpose){
				extract_pose_from_pose(m_pose, m_userpose);
//				clear_pose(m_userpose);
				MEM_freeN(m_userpose);
				m_userpose = NULL;
			}
#if 1
			/* Handle blending */
			if (m_blendin && (m_blendframe<m_blendin)){
				/* If this is the start of a blending sequence... */
				if ((m_blendframe==0.0) || (!m_blendpose)){
					obj->GetMRDPose(&m_blendpose);
					m_blendstart = curtime;
				}
				
				/* Find percentages */
				newweight = (m_blendframe/(float)m_blendin);
				blend_poses(m_pose, m_blendpose, 1.0 - newweight, ACTSTRIPMODE_BLEND);

				/* Increment current blending percentage */
				m_blendframe = (curtime - m_blendstart)*KX_KetsjiEngine::GetAnimFrameRate();
				if (m_blendframe>m_blendin)
					m_blendframe = m_blendin;
				
			}
#endif
			m_lastUpdate = m_localtime;
			obj->SetPose (m_pose);
		}
		else{
			m_blendframe = 0.0;
		}
	}
	
	if (!keepgoing){
		m_blendframe = 0.0;
	}
	return keepgoing;
};

/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/*     setStart                                                              */
const char BL_ActionActuator::GetAction_doc[] = 
"getAction()\n"
"\tReturns a string containing the name of the current action.\n";

PyObject* BL_ActionActuator::PyGetAction(PyObject* self, 
										 PyObject* args, 
										 PyObject* kwds) {
	ShowDeprecationWarning("getAction()", "the action property");

	if (m_action){
		return PyString_FromString(m_action->id.name+2);
	}
	Py_RETURN_NONE;
}

/*     getProperty                                                             */
const char BL_ActionActuator::GetProperty_doc[] = 
"getProperty()\n"
"\tReturns the name of the property to be used in FromProp mode.\n";

PyObject* BL_ActionActuator::PyGetProperty(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	ShowDeprecationWarning("getProperty()", "the property property");

	PyObject *result;
	
	result = Py_BuildValue("s", (const char *)m_propname);
	
	return result;
}

/*     getProperty                                                             */
const char BL_ActionActuator::GetFrameProperty_doc[] = 
"getFrameProperty()\n"
"\tReturns the name of the property, that is set to the current frame number.\n";

PyObject* BL_ActionActuator::PyGetFrameProperty(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	ShowDeprecationWarning("getFrameProperty()", "the frameProperty property");

	PyObject *result;
	
	result = Py_BuildValue("s", (const char *)m_framepropname);
	
	return result;
}

/*     getFrame                                                              */
const char BL_ActionActuator::GetFrame_doc[] = 
"getFrame()\n"
"\tReturns the current frame number.\n";

PyObject* BL_ActionActuator::PyGetFrame(PyObject* self, 
										PyObject* args, 
										PyObject* kwds) {
	ShowDeprecationWarning("getFrame()", "the frame property");

	PyObject *result;
	
	result = Py_BuildValue("f", m_localtime);
	
	return result;
}

/*     getEnd                                                                */
const char BL_ActionActuator::GetEnd_doc[] = 
"getEnd()\n"
"\tReturns the last frame of the action.\n";

PyObject* BL_ActionActuator::PyGetEnd(PyObject* self, 
									  PyObject* args, 
									  PyObject* kwds) {
	ShowDeprecationWarning("getEnd()", "the end property");

	PyObject *result;
	
	result = Py_BuildValue("f", m_endframe);
	
	return result;
}

/*     getStart                                                              */
const char BL_ActionActuator::GetStart_doc[] = 
"getStart()\n"
"\tReturns the starting frame of the action.\n";

PyObject* BL_ActionActuator::PyGetStart(PyObject* self, 
										PyObject* args, 
										PyObject* kwds) {
	ShowDeprecationWarning("getStart()", "the start property");

	PyObject *result;
	
	result = Py_BuildValue("f", m_startframe);
	
	return result;
}

/*     getBlendin                                                            */
const char BL_ActionActuator::GetBlendin_doc[] = 
"getBlendin()\n"
"\tReturns the number of interpolation animation frames to be\n"
"\tgenerated when this actuator is triggered.\n";

PyObject* BL_ActionActuator::PyGetBlendin(PyObject* self, 
										  PyObject* args, 
										  PyObject* kwds) {
	ShowDeprecationWarning("getBlendin()", "the blendin property");

	PyObject *result;
	
	result = Py_BuildValue("f", m_blendin);
	
	return result;
}

/*     getPriority                                                           */
const char BL_ActionActuator::GetPriority_doc[] = 
"getPriority()\n"
"\tReturns the priority for this actuator.  Actuators with lower\n"
"\tPriority numbers will override actuators with higher numbers.\n";

PyObject* BL_ActionActuator::PyGetPriority(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	ShowDeprecationWarning("getPriority()", "the priority property");

	PyObject *result;
	
	result = Py_BuildValue("i", m_priority);
	
	return result;
}

/*     setAction                                                             */
const char BL_ActionActuator::SetAction_doc[] = 
"setAction(action, (reset))\n"
"\t - action    : The name of the action to set as the current action.\n"
"\t - reset     : Optional parameter indicating whether to reset the\n"
"\t               blend timer or not.  A value of 1 indicates that the\n"
"\t               timer should be reset.  A value of 0 will leave it\n"
"\t               unchanged.  If reset is not specified, the timer will"
"\t	              be reset.\n";

PyObject* BL_ActionActuator::PySetAction(PyObject* self, 
										 PyObject* args, 
										 PyObject* kwds) {
	ShowDeprecationWarning("setAction()", "the action property");

	char *string;
	int	reset = 1;

	if (PyArg_ParseTuple(args,"s|i",&string, &reset))
	{
		bAction *action;
		
		action = (bAction*)SCA_ILogicBrick::m_sCurrentLogicManager->GetActionByName(STR_String(string));
		
		if (!action){
			/* NOTE!  Throw an exception or something */
			//			printf ("setAction failed: Action not found\n", string);
		}
		else{
			m_action=action;
			if (reset)
				m_blendframe = 0;
		}
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setStart                                                              */
const char BL_ActionActuator::SetStart_doc[] = 
"setStart(start)\n"
"\t - start     : Specifies the starting frame of the animation.\n";

PyObject* BL_ActionActuator::PySetStart(PyObject* self, 
										PyObject* args, 
										PyObject* kwds) {
	ShowDeprecationWarning("setStart()", "the start property");

	float start;
	
	if (PyArg_ParseTuple(args,"f",&start))
	{
		m_startframe = start;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setEnd                                                                */
const char BL_ActionActuator::SetEnd_doc[] = 
"setEnd(end)\n"
"\t - end       : Specifies the ending frame of the animation.\n";

PyObject* BL_ActionActuator::PySetEnd(PyObject* self, 
									  PyObject* args, 
									  PyObject* kwds) {
	ShowDeprecationWarning("setEnd()", "the end property");

	float end;
	
	if (PyArg_ParseTuple(args,"f",&end))
	{
		m_endframe = end;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setBlendin                                                            */
const char BL_ActionActuator::SetBlendin_doc[] = 
"setBlendin(blendin)\n"
"\t - blendin   : Specifies the number of frames of animation to generate\n"
"\t               when making transitions between actions.\n";

PyObject* BL_ActionActuator::PySetBlendin(PyObject* self, 
										  PyObject* args, 
										  PyObject* kwds) {
	ShowDeprecationWarning("setBlendin()", "the blendin property");

	float blendin;
	
	if (PyArg_ParseTuple(args,"f",&blendin))
	{
		m_blendin = blendin;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setBlendtime                                                          */
const char BL_ActionActuator::SetBlendtime_doc[] = 
"setBlendtime(blendtime)\n"
"\t - blendtime : Allows the script to directly modify the internal timer\n"
"\t               used when generating transitions between actions.  This\n"
"\t               parameter must be in the range from 0.0 to 1.0.\n";

PyObject* BL_ActionActuator::PySetBlendtime(PyObject* self, 
										  PyObject* args, 
										  PyObject* kwds) {
	ShowDeprecationWarning("setBlendtime()", "the blendtime property");

	float blendframe;
	
	if (PyArg_ParseTuple(args,"f",&blendframe))
	{
		m_blendframe = blendframe * m_blendin;
		if (m_blendframe<0)
			m_blendframe = 0;
		if (m_blendframe>m_blendin)
			m_blendframe = m_blendin;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setPriority                                                           */
const char BL_ActionActuator::SetPriority_doc[] = 
"setPriority(priority)\n"
"\t - priority  : Specifies the new priority.  Actuators will lower\n"
"\t               priority numbers will override actuators with higher\n"
"\t               numbers.\n";

PyObject* BL_ActionActuator::PySetPriority(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	ShowDeprecationWarning("setPriority()", "the priority property");

	int priority;
	
	if (PyArg_ParseTuple(args,"i",&priority))
	{
		m_priority = priority;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setFrame                                                              */
const char BL_ActionActuator::SetFrame_doc[] = 
"setFrame(frame)\n"
"\t - frame     : Specifies the new current frame for the animation\n";

PyObject* BL_ActionActuator::PySetFrame(PyObject* self, 
										PyObject* args, 
										PyObject* kwds) {
	ShowDeprecationWarning("setFrame()", "the frame property");

	float frame;
	
	if (PyArg_ParseTuple(args,"f",&frame))
	{
		m_localtime = frame;
		if (m_localtime<m_startframe)
			m_localtime=m_startframe;
		else if (m_localtime>m_endframe)
			m_localtime=m_endframe;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setProperty                                                           */
const char BL_ActionActuator::SetProperty_doc[] = 
"setProperty(prop)\n"
"\t - prop      : A string specifying the property name to be used in\n"
"\t               FromProp playback mode.\n";

PyObject* BL_ActionActuator::PySetProperty(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	ShowDeprecationWarning("setProperty()", "the property property");

	char *string;
	
	if (PyArg_ParseTuple(args,"s",&string))
	{
		m_propname = string;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*     setFrameProperty                                                          */
const char BL_ActionActuator::SetFrameProperty_doc[] = 
"setFrameProperty(prop)\n"
"\t - prop      : A string specifying the property of the frame set up update.\n";

PyObject* BL_ActionActuator::PySetFrameProperty(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	ShowDeprecationWarning("setFrameProperty()", "the frameProperty property");

	char *string;
	
	if (PyArg_ParseTuple(args,"s",&string))
	{
		m_framepropname = string;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}

/*
PyObject* BL_ActionActuator::PyGetChannel(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	char *string;
	
	if (PyArg_ParseTuple(args,"s",&string))
	{
		m_propname = string;
	}
	else {
		return NULL;
	}
	
	Py_RETURN_NONE;
}
*/

/* getType */
const char BL_ActionActuator::GetType_doc[] =
"getType()\n"
"\tReturns the operation mode of the actuator.\n";
PyObject* BL_ActionActuator::PyGetType(PyObject* self,
                                       PyObject* args, 
                                       PyObject* kwds) {
	ShowDeprecationWarning("getType()", "the type property");

    return Py_BuildValue("h", m_playtype);
}

/* setType */
const char BL_ActionActuator::SetType_doc[] =
"setType(mode)\n"
"\t - mode: Play (0), Flipper (2), LoopStop (3), LoopEnd (4) or Property (6)\n"
"\tSet the operation mode of the actuator.\n";
PyObject* BL_ActionActuator::PySetType(PyObject* self,
                                       PyObject* args,
                                       PyObject* kwds) {
	ShowDeprecationWarning("setType()", "the type property");

	short typeArg;
                                                                                                             
    if (!PyArg_ParseTuple(args, "h", &typeArg)) {
        return NULL;
    }

	switch (typeArg) {
	case ACT_ACTION_PLAY:
	case ACT_ACTION_FLIPPER:
	case ACT_ACTION_LOOP_STOP:
	case ACT_ACTION_LOOP_END:
	case ACT_ACTION_FROM_PROP:
		m_playtype = typeArg;
		break;
	default:
		printf("Invalid type for action actuator: %d\n", typeArg); /* error */
    }
	Py_RETURN_NONE;
}

PyObject* BL_ActionActuator::PyGetContinue(PyObject* self) {
	ShowDeprecationWarning("getContinue()", "the continue property");

    return PyInt_FromLong((long)(m_end_reset==0));
}

PyObject* BL_ActionActuator::PySetContinue(PyObject* self, PyObject* value) {
	ShowDeprecationWarning("setContinue()", "the continue property");

	int param = PyObject_IsTrue( value );
	
	if( param == -1 ) {
		PyErr_SetString( PyExc_TypeError, "expected True/False or 0/1" );
		return NULL;
	}

	if (param) {
		m_end_reset = 0;
	} else {
		m_end_reset = 1;
	}
    Py_RETURN_NONE;
}

//<-----Deprecated

/*     setChannel                                                         */
KX_PYMETHODDEF_DOC(BL_ActionActuator, setChannel,
"setChannel(channel, matrix)\n"
"\t - channel   : A string specifying the name of the bone channel.\n"
"\t - matrix    : A 4x4 matrix specifying the overriding transformation\n"
"\t               as an offset from the bone's rest position.\n")
{
	float matrix[4][4];
	char *string;
	PyObject* pylist;
	bool	error = false;
	int row,col;
	int	mode = 0;	/* 0 for bone space, 1 for armature/world space */
	
	if (!PyArg_ParseTuple(args,"sO|i", &string, &pylist, &mode))
		return NULL;
	
	if (pylist->ob_type == &CListValue::Type)
	{
		CListValue* listval = (CListValue*) pylist;
		if (listval->GetCount() == 4)
		{
			for (row=0;row<4;row++) // each row has a 4-vector [x,y,z, w]
			{
				CListValue* vecval = (CListValue*)listval->GetValue(row);
				for (col=0;col<4;col++)
				{
					matrix[row][col] = vecval->GetValue(col)->GetNumber();
					
				}
			}
		}
		else
		{
			error = true;
		}
	}
	else
	{
		// assert the list is long enough...
		int numitems = PyList_Size(pylist);
		if (numitems == 4)
		{
			for (row=0;row<4;row++) // each row has a 4-vector [x,y,z, w]
			{
				
				PyObject* veclist = PyList_GetItem(pylist,row); // here we have a vector4 list
				for (col=0;col<4;col++)
				{
					matrix[row][col] =  PyFloat_AsDouble(PyList_GetItem(veclist,col));
					
				}
			}
		}
		else
		{
			error = true;
		}
	}
	
	if (!error)
	{

/*	DO IT HERE */
		bPoseChannel *pchan= verify_pose_channel(m_userpose, string);

		Mat4ToQuat(matrix, pchan->quat);
		Mat4ToSize(matrix, pchan->size);
		VECCOPY (pchan->loc, matrix[3]);
		
		pchan->flag |= POSE_ROT|POSE_LOC|POSE_SIZE;

		if (!m_userpose){
			m_userpose = (bPose*)MEM_callocN(sizeof(bPose), "userPose");
		}
	}
	
	Py_RETURN_NONE;
}

/* ------------------------------------------------------------------------- */
/* Python Integration Hooks					                                 */
/* ------------------------------------------------------------------------- */

PyTypeObject BL_ActionActuator::Type = {
	PyObject_HEAD_INIT(NULL)
		0,
		"BL_ActionActuator",
		sizeof(BL_ActionActuator),
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

PyParentObject BL_ActionActuator::Parents[] = {
	&BL_ActionActuator::Type,
		&SCA_IActuator::Type,
		&SCA_ILogicBrick::Type,
		&CValue::Type,
		NULL
};

PyMethodDef BL_ActionActuator::Methods[] = {
	//Deprecated ----->
	{"setAction", (PyCFunction) BL_ActionActuator::sPySetAction, METH_VARARGS, (PY_METHODCHAR)SetAction_doc},
	{"setStart", (PyCFunction) BL_ActionActuator::sPySetStart, METH_VARARGS, (PY_METHODCHAR)SetStart_doc},
	{"setEnd", (PyCFunction) BL_ActionActuator::sPySetEnd, METH_VARARGS, (PY_METHODCHAR)SetEnd_doc},
	{"setBlendin", (PyCFunction) BL_ActionActuator::sPySetBlendin, METH_VARARGS, (PY_METHODCHAR)SetBlendin_doc},
	{"setPriority", (PyCFunction) BL_ActionActuator::sPySetPriority, METH_VARARGS, (PY_METHODCHAR)SetPriority_doc},
	{"setFrame", (PyCFunction) BL_ActionActuator::sPySetFrame, METH_VARARGS, (PY_METHODCHAR)SetFrame_doc},
	{"setProperty", (PyCFunction) BL_ActionActuator::sPySetProperty, METH_VARARGS, (PY_METHODCHAR)SetProperty_doc},
	{"setFrameProperty", (PyCFunction) BL_ActionActuator::sPySetFrameProperty, METH_VARARGS, (PY_METHODCHAR)SetFrameProperty_doc},
	{"setBlendtime", (PyCFunction) BL_ActionActuator::sPySetBlendtime, METH_VARARGS, (PY_METHODCHAR)SetBlendtime_doc},

	{"getAction", (PyCFunction) BL_ActionActuator::sPyGetAction, METH_VARARGS, (PY_METHODCHAR)GetAction_doc},
	{"getStart", (PyCFunction) BL_ActionActuator::sPyGetStart, METH_VARARGS, (PY_METHODCHAR)GetStart_doc},
	{"getEnd", (PyCFunction) BL_ActionActuator::sPyGetEnd, METH_VARARGS, (PY_METHODCHAR)GetEnd_doc},
	{"getBlendin", (PyCFunction) BL_ActionActuator::sPyGetBlendin, METH_VARARGS, (PY_METHODCHAR)GetBlendin_doc},
	{"getPriority", (PyCFunction) BL_ActionActuator::sPyGetPriority, METH_VARARGS, (PY_METHODCHAR)GetPriority_doc},
	{"getFrame", (PyCFunction) BL_ActionActuator::sPyGetFrame, METH_VARARGS, (PY_METHODCHAR)GetFrame_doc},
	{"getProperty", (PyCFunction) BL_ActionActuator::sPyGetProperty, METH_VARARGS, (PY_METHODCHAR)GetProperty_doc},
	{"getFrameProperty", (PyCFunction) BL_ActionActuator::sPyGetFrameProperty, METH_VARARGS, (PY_METHODCHAR)GetFrameProperty_doc},
//	{"getChannel", (PyCFunction) BL_ActionActuator::sPyGetChannel, METH_VARARGS},
	{"getType", (PyCFunction) BL_ActionActuator::sPyGetType, METH_VARARGS, (PY_METHODCHAR)GetType_doc},
	{"setType", (PyCFunction) BL_ActionActuator::sPySetType, METH_VARARGS, (PY_METHODCHAR)SetType_doc},
	{"getContinue", (PyCFunction) BL_ActionActuator::sPyGetContinue, METH_NOARGS, 0},	
	{"setContinue", (PyCFunction) BL_ActionActuator::sPySetContinue, METH_O, 0},
	//<------
	KX_PYMETHODTABLE(BL_ActionActuator, setChannel),
	{NULL,NULL} //Sentinel
};

PyAttributeDef BL_ActionActuator::Attributes[] = {
	KX_PYATTRIBUTE_FLOAT_RW("start", 0, MAXFRAMEF, BL_ActionActuator, m_startframe),
	KX_PYATTRIBUTE_FLOAT_RW("end", 0, MAXFRAMEF, BL_ActionActuator, m_endframe),
	KX_PYATTRIBUTE_FLOAT_RW("blendin", 0, MAXFRAMEF, BL_ActionActuator, m_blendin),
	KX_PYATTRIBUTE_RW_FUNCTION("action", BL_ActionActuator, pyattr_get_action, pyattr_set_action),
	KX_PYATTRIBUTE_SHORT_RW("priority", 0, 100, false, BL_ActionActuator, m_priority),
	KX_PYATTRIBUTE_FLOAT_RW_CHECK("frame", 0, MAXFRAMEF, BL_ActionActuator, m_localtime, CheckFrame),
	KX_PYATTRIBUTE_STRING_RW("property", 0, 31, false, BL_ActionActuator, m_propname),
	KX_PYATTRIBUTE_STRING_RW("frameProperty", 0, 31, false, BL_ActionActuator, m_framepropname),
	KX_PYATTRIBUTE_BOOL_RW("continue", BL_ActionActuator, m_end_reset),
	KX_PYATTRIBUTE_FLOAT_RW_CHECK("blendTime", 0, MAXFRAMEF, BL_ActionActuator, m_blendframe, CheckBlendTime),
	KX_PYATTRIBUTE_SHORT_RW_CHECK("type",0,100,false,BL_ActionActuator,m_playtype,CheckType),
	{ NULL }	//Sentinel
};

PyObject* BL_ActionActuator::py_getattro(PyObject *attr) {
	PyObject* object = py_getattro_self(Attributes, this, attr);
	if (object != NULL)
		return object;
	py_getattro_up(SCA_IActuator);
}

int BL_ActionActuator::py_setattro(PyObject *attr, PyObject* value) {
	int ret = py_setattro_self(Attributes, this, attr, value);
	if (ret >= 0)
		return ret;
	return SCA_IActuator::py_setattro(attr, value);
}



PyObject* BL_ActionActuator::pyattr_get_action(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef)
{
	BL_ActionActuator* self= static_cast<BL_ActionActuator*>(self_v);
	return PyString_FromString(self->GetAction()->id.name+2);
}

int BL_ActionActuator::pyattr_set_action(void *self_v, const KX_PYATTRIBUTE_DEF *attrdef, PyObject *value)
{
	BL_ActionActuator* self= static_cast<BL_ActionActuator*>(self_v);
	
	if (!PyString_Check(value))
	{
		PyErr_SetString(PyExc_ValueError, "expected the string name of the action");
		return -1;
	}

	bAction *action= NULL;
	STR_String val = PyString_AsString(value);
	
	if (val != "")
	{
		(bAction*)SCA_ILogicBrick::m_sCurrentLogicManager->GetActionByName(val);
		if (!action)
		{
			PyErr_SetString(PyExc_ValueError, "action not found!");
			return 1;
		}
	}
	
	self->SetAction(action);
	return 0;

}
