//
// Replace the mesh for this actuator's parent
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

// todo: not all trackflags / upflags are implemented/tested !
// m_trackflag is used to determine the forward tracking direction
// m_upflag for the up direction
// normal situation is +y for forward, +z for up

#include "MT_Scalar.h"
#include "SCA_IActuator.h"
#include "KX_TrackToActuator.h"
#include "SCA_IScene.h"
#include "SCA_LogicManager.h"
#include <math.h>
#include <iostream>
#include "KX_GameObject.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */



KX_TrackToActuator::KX_TrackToActuator(SCA_IObject *gameobj, 
								       SCA_IObject *ob,
									   int time,
									   bool allow3D,
									   int trackflag,
									   int upflag,
									   PyTypeObject* T)
									   :
										SCA_IActuator(gameobj, T)
{
    m_time = time;
    m_allow3D = allow3D;
    m_object = ob;
	m_trackflag = trackflag;
	m_upflag = upflag;
} /* End of constructor */



/* old function from Blender */
MT_Matrix3x3 EulToMat3(float *eul)
{
	MT_Matrix3x3 mat;
	float ci, cj, ch, si, sj, sh, cc, cs, sc, ss;
	
	ci = cos(eul[0]); 
	cj = cos(eul[1]); 
	ch = cos(eul[2]);
	si = sin(eul[0]); 
	sj = sin(eul[1]); 
	sh = sin(eul[2]);
	cc = ci*ch; 
	cs = ci*sh; 
	sc = si*ch; 
	ss = si*sh;

	mat[0][0] = cj*ch; 
	mat[1][0] = sj*sc-cs; 
	mat[2][0] = sj*cc+ss;
	mat[0][1] = cj*sh; 
	mat[1][1] = sj*ss+cc; 
	mat[2][1] = sj*cs-sc;
	mat[0][2] = -sj;	 
	mat[1][2] = cj*si;    
	mat[2][2] = cj*ci;

	return mat;
}



/* old function from Blender */
void Mat3ToEul(MT_Matrix3x3 mat, float *eul)
{
	MT_Scalar cy;
	
	cy = sqrt(mat[0][0]*mat[0][0] + mat[0][1]*mat[0][1]);

	if (cy > 16.0*FLT_EPSILON) {
		eul[0] = atan2(mat[1][2], mat[2][2]);
		eul[1] = atan2(-mat[0][2], cy);
		eul[2] = atan2(mat[0][1], mat[0][0]);
	} else {
		eul[0] = atan2(-mat[2][1], mat[1][1]);
		eul[1] = atan2(-mat[0][2], cy);
		eul[2] = 0.0;
	}
}



/* old function from Blender */
void compatible_eulFast(float *eul, float *oldrot)
{
	float dx, dy, dz;
	
	/* verschillen van ong 360 graden corrigeren */

	dx= eul[0] - oldrot[0];
	dy= eul[1] - oldrot[1];
	dz= eul[2] - oldrot[2];

	if( fabs(dx) > 5.1) {
		if(dx > 0.0) eul[0] -= MT_2_PI; else eul[0]+= MT_2_PI;
	}
	if( fabs(dy) > 5.1) {
		if(dy > 0.0) eul[1] -= MT_2_PI; else eul[1]+= MT_2_PI;
	}
	if( fabs(dz) > 5.1 ) {
		if(dz > 0.0) eul[2] -= MT_2_PI; else eul[2]+= MT_2_PI;
	}
}



MT_Matrix3x3 matrix3x3_interpol(MT_Matrix3x3 oldmat, MT_Matrix3x3 mat, int m_time)
{
	float eul[3], oldeul[3];	

	Mat3ToEul(oldmat, oldeul);
	Mat3ToEul(mat, eul);
	compatible_eulFast(eul, oldeul);
	
	eul[0]= (m_time*oldeul[0] + eul[0])/(1.0+m_time);
	eul[1]= (m_time*oldeul[1] + eul[1])/(1.0+m_time);
	eul[2]= (m_time*oldeul[2] + eul[2])/(1.0+m_time);
	
	return EulToMat3(eul);
}



KX_TrackToActuator::~KX_TrackToActuator()
{ 
	// there's nothing to be done here, really....
} /* end of destructor */



bool KX_TrackToActuator::Update(double curtime,double deltatime)
{
	bool result = false;	
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();

	if (bNegativeEvent)
	{
		// do nothing on negative events
	}
	else if (m_object)
	{
		KX_GameObject* curobj = (KX_GameObject*) GetParent();
		MT_Vector3 dir = ((KX_GameObject*)m_object)->NodeGetWorldPosition() - curobj->NodeGetWorldPosition();
		dir.normalize();
		MT_Vector3 up(0,0,1);
		
		
#ifdef DSADSA
		switch (m_upflag)
		{
		case 0:
			{
				up = MT_Vector3(1.0,0,0);
				break;
			} 
		case 1:
			{
				up = MT_Vector3(0,1.0,0);
				break;
			}
		case 2:
		default:
			{
				up = MT_Vector3(0,0,1.0);
			}
		}
#endif 
		if (m_allow3D)
		{
			up = (up - up.dot(dir) * dir).normalized();
			
		}
		else
		{
			dir = (dir - up.dot(dir)*up).normalized();
		}
		
		MT_Vector3 left;
		MT_Matrix3x3 mat;
		
		switch (m_trackflag)
		{
		case 0: // TRACK X
			{
				// (1.0 , 0.0 , 0.0 ) x direction is forward, z (0.0 , 0.0 , 1.0 ) up
				left  = dir.normalized();
				dir = (left.cross(up)).normalized();
				mat.setValue (
					left[0], dir[0],up[0], 
					left[1], dir[1],up[1],
					left[2], dir[2],up[2]
					);
				
				break;
			};
		case 1:	// TRACK Y
			{
				// (0.0 , 1.0 , 0.0 ) y direction is forward, z (0.0 , 0.0 , 1.0 ) up
				left  = (dir.cross(up)).normalized();
				mat.setValue (
					left[0], dir[0],up[0], 
					left[1], dir[1],up[1],
					left[2], dir[2],up[2]
					);
				
				break;
			}
			
		case 2: // track Z
			{
				left = up.normalized();
				up = dir.normalized();
				dir = left;
				left  = (dir.cross(up)).normalized();
				mat.setValue (
					left[0], dir[0],up[0], 
					left[1], dir[1],up[1],
					left[2], dir[2],up[2]
					);
				break;
			}
			
		case 3: // TRACK -X
			{
				// (1.0 , 0.0 , 0.0 ) x direction is forward, z (0.0 , 0.0 , 1.0 ) up
				left  = -dir.normalized();
				dir = -(left.cross(up)).normalized();
				mat.setValue (
					left[0], dir[0],up[0], 
					left[1], dir[1],up[1],
					left[2], dir[2],up[2]
					);
				
				break;
			};
		case 4: // TRACK -Y
			{
				// (0.0 , -1.0 , 0.0 ) -y direction is forward, z (0.0 , 0.0 , 1.0 ) up
				left  = (-dir.cross(up)).normalized();
				mat.setValue (
					left[0], -dir[0],up[0], 
					left[1], -dir[1],up[1],
					left[2], -dir[2],up[2]
					);
				break;
			}
		case 5: // track -Z
			{
				left = up.normalized();
				up = -dir.normalized();
				dir = left;
				left  = (dir.cross(up)).normalized();
				mat.setValue (
					left[0], dir[0],up[0], 
					left[1], dir[1],up[1],
					left[2], dir[2],up[2]
					);
				
				break;
			}
			
		default:
			{
				// (1.0 , 0.0 , 0.0 ) -x direction is forward, z (0.0 , 0.0 , 1.0 ) up
				left  = -dir.normalized();
				dir = -(left.cross(up)).normalized();
				mat.setValue (
					left[0], dir[0],up[0], 
					left[1], dir[1],up[1],
					left[2], dir[2],up[2]
					);
			}
		}
		
		MT_Matrix3x3 oldmat;
		oldmat= curobj->NodeGetWorldOrientation();
		
		/* erwin should rewrite this! */
		mat= matrix3x3_interpol(oldmat, mat, m_time);
		
		curobj->NodeSetLocalOrientation(mat);
		
		//cout << "\n TrackTo!";
		result = true;
	}

	return result;
}



/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */



/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_TrackToActuator::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"KX_TrackToActuator",
	sizeof(KX_TrackToActuator),
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



PyParentObject KX_TrackToActuator::Parents[] = {
	&KX_TrackToActuator::Type,
		&SCA_IActuator::Type,
		&SCA_ILogicBrick::Type,
		&CValue::Type,
		NULL
};



PyMethodDef KX_TrackToActuator::Methods[] = {
	{"setObject", (PyCFunction) KX_TrackToActuator::sPySetObject, METH_VARARGS, SetObject_doc},
	{"getObject", (PyCFunction) KX_TrackToActuator::sPyGetObject, METH_VARARGS, GetObject_doc},
	{"setTime", (PyCFunction) KX_TrackToActuator::sPySetTime, METH_VARARGS, SetTime_doc},
	{"getTime", (PyCFunction) KX_TrackToActuator::sPyGetTime, METH_VARARGS, GetTime_doc},
	{"setUse3D", (PyCFunction) KX_TrackToActuator::sPySetUse3D, METH_VARARGS, SetUse3D_doc},
	{"getUse3D", (PyCFunction) KX_TrackToActuator::sPyGetUse3D, METH_VARARGS, GetUse3D_doc},
	{NULL,NULL} //Sentinel
};



PyObject* KX_TrackToActuator::_getattr(const STR_String& attr)
{
	_getattr_up(SCA_IActuator);
}



/* 1. setObject */
char KX_TrackToActuator::SetObject_doc[] = 
"setObject(object)\n"
"\t- object: string\n"
"\tSet the object to track with the parent of this actuator.\n";
PyObject* KX_TrackToActuator::PySetObject(PyObject* self, PyObject* args, PyObject* kwds) {
	PyObject* gameobj;
	if (PyArg_ParseTuple(args, "O!", &KX_GameObject::Type, &gameobj))
	{
		m_object = (SCA_IObject*)gameobj;

		Py_Return;
	}
	PyErr_Clear();
	
	char* objectname;
	if (PyArg_ParseTuple(args, "s", &objectname))
	{
		m_object= static_cast<SCA_IObject*>(SCA_ILogicBrick::m_sCurrentLogicManager->GetGameObjectByName(STR_String(objectname)));
		
		Py_Return;
	}
	
	return NULL;
}



/* 2. getObject */
char KX_TrackToActuator::GetObject_doc[] = 
"getObject()\n"
"\tReturns the object to track with the parent of this actuator.\n";
PyObject* KX_TrackToActuator::PyGetObject(PyObject* self, PyObject* args, PyObject* kwds)
{
	if (!m_object)
		Py_Return;

	return PyString_FromString(m_object->GetName());
}



/* 3. setTime */
char KX_TrackToActuator::SetTime_doc[] = 
"setTime(time)\n"
"\t- time: integer\n"
"\tSet the time in frames with which to delay the tracking motion.\n";
PyObject* KX_TrackToActuator::PySetTime(PyObject* self, PyObject* args, PyObject* kwds)
{
	int timeArg;
	
	if (!PyArg_ParseTuple(args, "i", &timeArg))
	{
		return NULL;
	}
	
	m_time= timeArg;
	
	Py_Return;
}



/* 4.getTime */
char KX_TrackToActuator::GetTime_doc[] = 
"getTime()\n"
"\t- time: integer\n"
"\tReturn the time in frames with which the tracking motion is delayed.\n";
PyObject* KX_TrackToActuator::PyGetTime(PyObject* self, PyObject* args, PyObject* kwds)
{
	return PyInt_FromLong(m_time);
}



/* 5. getUse3D */
char KX_TrackToActuator::GetUse3D_doc[] = 
"getUse3D()\n"
"\tReturns 1 if the motion is allowed to extend in the z-direction.\n";
PyObject* KX_TrackToActuator::PyGetUse3D(PyObject* self, PyObject* args, PyObject* kwds)
{
	return PyInt_FromLong(!(m_allow3D == 0));
}



/* 6. setUse3D */
char KX_TrackToActuator::SetUse3D_doc[] = 
"setUse3D(value)\n"
"\t- value: 0 or 1\n"
"\tSet to 1 to allow the tracking motion to extend in the z-direction,\n"
"\tset to 0 to lock the tracking motion to the x-y plane.\n";
PyObject* KX_TrackToActuator::PySetUse3D(PyObject* self, PyObject* args, PyObject* kwds)
{
	int boolArg;
	
	if (!PyArg_ParseTuple(args, "i", &boolArg)) {
		return NULL;
	}
	
	m_allow3D = !(boolArg == 0);
	
	Py_Return;
}

/* eof */
