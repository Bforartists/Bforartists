/**
 * Apply a constraint to a position or rotation value
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
#include "KX_ConstraintActuator.h"
#include "SCA_IObject.h"
#include "MT_Point3.h"
#include "MT_Matrix3x3.h"
#include "KX_GameObject.h"
#include "KX_RayCast.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

/* ------------------------------------------------------------------------- */
/* Native functions                                                          */
/* ------------------------------------------------------------------------- */

KX_ConstraintActuator::KX_ConstraintActuator(SCA_IObject *gameobj, 
											 int posDampTime,
											 int rotDampTime,
											 float minBound,
											 float maxBound,
											 float refDir[3],
											 int locrotxyz,
											 int time,
											 int option,
											 char *property,
											 PyTypeObject* T) : 
	m_refDirection(refDir),
	m_currentTime(0),
	SCA_IActuator(gameobj, T)
{
	m_posDampTime = posDampTime;
	m_rotDampTime = rotDampTime;
	m_locrot   = locrotxyz;
	m_option = option;
	m_activeTime = time;
	if (property) {
		strncpy(m_property, property, sizeof(m_property));
		m_property[sizeof(m_property)-1] = 0;
	} else {
		m_property[0] = 0;
	}
	/* The units of bounds are determined by the type of constraint. To      */
	/* make the constraint application easier and more transparent later on, */
	/* I think converting the bounds to the applicable domain makes more     */
	/* sense.                                                                */
	switch (m_locrot) {
	case KX_ACT_CONSTRAINT_ORIX:
	case KX_ACT_CONSTRAINT_ORIY:
	case KX_ACT_CONSTRAINT_ORIZ:
		{
			MT_Scalar len = m_refDirection.length();
			if (MT_fuzzyZero(len)) {
				// missing a valid direction
				std::cout << "WARNING: Constraint actuator " << GetName() << ":  There is no valid reference direction!" << std::endl;
				m_locrot = KX_ACT_CONSTRAINT_NODEF;
			} else {
				m_refDirection /= len;
			}
			m_minimumBound = cos(minBound);
			m_maximumBound = cos(maxBound);
			m_minimumSine = sin(minBound);
			m_maximumSine = sin(maxBound);
		}
		break;
	default:
		m_minimumBound = minBound;
		m_maximumBound = maxBound;
		m_minimumSine = 0.f;
		m_maximumSine = 0.f;
		break;
	}

} /* End of constructor */

KX_ConstraintActuator::~KX_ConstraintActuator()
{ 
	// there's nothing to be done here, really....
} /* end of destructor */

bool KX_ConstraintActuator::RayHit(KX_ClientObjectInfo* client, KX_RayCast* result, void * const data)
{

	m_hitObject = client->m_gameobject;
	
	bool bFound = false;

	if (m_property[0] == 0)
	{
		bFound = true;
	}
	else
	{
		if (m_option & KX_ACT_CONSTRAINT_MATERIAL)
		{
			if (client->m_auxilary_info)
			{
				bFound = !strcmp(m_property, ((char*)client->m_auxilary_info));
			}
		}
		else
		{
			bFound = m_hitObject->GetProperty(m_property) != NULL;
		}
	}
	// update the hit status
	result->m_hitFound = bFound;
	// stop looking
	return true;
}

/* this function is used to pre-filter the object before casting the ray on them.
   This is useful for "X-Ray" option when we want to see "through" unwanted object.
 */
bool KX_ConstraintActuator::NeedRayCast(KX_ClientObjectInfo* client)
{
	if (client->m_type > KX_ClientObjectInfo::ACTOR)
	{
		// Unknown type of object, skip it.
		// Should not occur as the sensor objects are filtered in RayTest()
		printf("Invalid client type %d found in ray casting\n", client->m_type);
		return false;
	}
	// no X-Ray function yet
	return true;
}

bool KX_ConstraintActuator::Update(double curtime, bool frame)
{

	bool result = false;	
	bool bNegativeEvent = IsNegativeEvent();
	RemoveAllEvents();

	if (!bNegativeEvent) {
		/* Constraint clamps the values to the specified range, with a sort of    */
		/* low-pass filtered time response, if the damp time is unequal to 0.     */

		/* Having to retrieve location/rotation and setting it afterwards may not */
		/* be efficient enough... Somthing to look at later.                      */
		KX_GameObject  *obj = (KX_GameObject*) GetParent();
		MT_Point3    position = obj->NodeGetWorldPosition();
		MT_Point3    newposition;
		MT_Vector3   normal, direction, refDirection;
		MT_Matrix3x3 rotation = obj->NodeGetWorldOrientation();
		MT_Scalar    filter, newdistance, cosangle;
		int axis, sign;

		if (m_posDampTime) {
			filter = m_posDampTime/(1.0+m_posDampTime);
		} else {
			filter = 0.0;
		}
		switch (m_locrot) {
		case KX_ACT_CONSTRAINT_ORIX:
		case KX_ACT_CONSTRAINT_ORIY:
		case KX_ACT_CONSTRAINT_ORIZ:
			switch (m_locrot) {
			case KX_ACT_CONSTRAINT_ORIX:
				direction[0] = rotation[0][0];
				direction[1] = rotation[1][0];
				direction[2] = rotation[2][0];
				axis = 0;
				break;
			case KX_ACT_CONSTRAINT_ORIY:
				direction[0] = rotation[0][1];
				direction[1] = rotation[1][1];
				direction[2] = rotation[2][1];
				axis = 1;
				break;
			default:
				direction[0] = rotation[0][2];
				direction[1] = rotation[1][2];
				direction[2] = rotation[2][2];
				axis = 2;
				break;
			}
			if ((m_maximumBound < (1.0f-FLT_EPSILON)) || (m_minimumBound < (1.0f-FLT_EPSILON))) {
				// reference direction needs to be evaluated
				// 1. get the cosine between current direction and target
				cosangle = direction.dot(m_refDirection);
				if (cosangle >= (m_maximumBound-FLT_EPSILON) && cosangle <= (m_minimumBound+FLT_EPSILON)) {
					// no change to do
					result = true;
					goto CHECK_TIME;
				}
				// 2. define a new reference direction
				//    compute local axis with reference direction as X and
				//    Y in direction X refDirection plane
				MT_Vector3 zaxis = m_refDirection.cross(direction);
				if (MT_fuzzyZero2(zaxis.length2())) {
					// direction and refDirection are identical,
					// choose any other direction to define plane
					if (direction[0] < 0.9999)
						zaxis = m_refDirection.cross(MT_Vector3(1.0,0.0,0.0));
					else
						zaxis = m_refDirection.cross(MT_Vector3(0.0,1.0,0.0));
				}
				MT_Vector3 yaxis = zaxis.cross(m_refDirection);
				yaxis.normalize();
				if (cosangle > m_minimumBound) {
					// angle is too close to reference direction,
					// choose a new reference that is exactly at minimum angle
					refDirection = m_minimumBound * m_refDirection + m_minimumSine * yaxis;
				} else {
					// angle is too large, choose new reference direction at maximum angle
					refDirection = m_maximumBound * m_refDirection + m_maximumSine * yaxis;
				}
			} else {
				refDirection = m_refDirection;
			}
			// apply damping on the direction
			direction = filter*direction + (1.0-filter)*refDirection;
			obj->AlignAxisToVect(direction, axis);
			result = true;
			goto CHECK_TIME;
		case KX_ACT_CONSTRAINT_DIRPX:
		case KX_ACT_CONSTRAINT_DIRPY:
		case KX_ACT_CONSTRAINT_DIRPZ:
		case KX_ACT_CONSTRAINT_DIRNX:
		case KX_ACT_CONSTRAINT_DIRNY:
		case KX_ACT_CONSTRAINT_DIRNZ:
			switch (m_locrot) {
			case KX_ACT_CONSTRAINT_DIRPX:
				normal[0] = rotation[0][0];
				normal[1] = rotation[1][0];
				normal[2] = rotation[2][0];
				axis = 0;		// axis according to KX_GameObject::AlignAxisToVect()
				sign = 0;		// X axis will be parrallel to direction of ray
				break;
			case KX_ACT_CONSTRAINT_DIRPY:
				normal[0] = rotation[0][1];
				normal[1] = rotation[1][1];
				normal[2] = rotation[2][1];
				axis = 1;
				sign = 0;
				break;
			case KX_ACT_CONSTRAINT_DIRPZ:
				normal[0] = rotation[0][2];
				normal[1] = rotation[1][2];
				normal[2] = rotation[2][2];
				axis = 2;
				sign = 0;
				break;
			case KX_ACT_CONSTRAINT_DIRNX:
				normal[0] = -rotation[0][0];
				normal[1] = -rotation[1][0];
				normal[2] = -rotation[2][0];
				axis = 0;
				sign = 1;
				break;
			case KX_ACT_CONSTRAINT_DIRNY:
				normal[0] = -rotation[0][1];
				normal[1] = -rotation[1][1];
				normal[2] = -rotation[2][1];
				axis = 1;
				sign = 1;
				break;
			case KX_ACT_CONSTRAINT_DIRNZ:
				normal[0] = -rotation[0][2];
				normal[1] = -rotation[1][2];
				normal[2] = -rotation[2][2];
				axis = 2;
				sign = 1;
				break;
			}
			normal.normalize();
			if (m_option & KX_ACT_CONSTRAINT_LOCAL) {
				// direction of the ray is along the local axis
				direction = normal;
			} else {
				switch (m_locrot) {
				case KX_ACT_CONSTRAINT_DIRPX:
					direction = MT_Vector3(1.0,0.0,0.0);
					break;
				case KX_ACT_CONSTRAINT_DIRPY:
					direction = MT_Vector3(0.0,1.0,0.0);
					break;
				case KX_ACT_CONSTRAINT_DIRPZ:
					direction = MT_Vector3(0.0,0.0,1.0);
					break;
				case KX_ACT_CONSTRAINT_DIRNX:
					direction = MT_Vector3(-1.0,0.0,0.0);
					break;
				case KX_ACT_CONSTRAINT_DIRNY:
					direction = MT_Vector3(0.0,-1.0,0.0);
					break;
				case KX_ACT_CONSTRAINT_DIRNZ:
					direction = MT_Vector3(0.0,0.0,-1.0);
					break;
				}
			}
			{
				MT_Point3 topoint = position + (m_maximumBound) * direction;
				PHY_IPhysicsEnvironment* pe = obj->GetPhysicsEnvironment();
				KX_IPhysicsController *spc = obj->GetPhysicsController();

				if (!pe) {
					std::cout << "WARNING: Constraint actuator " << GetName() << ":  There is no physics environment!" << std::endl;
					goto CHECK_TIME;
				}	 
				if (!spc) {
					// the object is not physical, we probably want to avoid hitting its own parent
					KX_GameObject *parent = obj->GetParent();
					if (parent) {
						spc = parent->GetPhysicsController();
						parent->Release();
					}
				}
				KX_RayCast::Callback<KX_ConstraintActuator> callback(this,spc);
				result = KX_RayCast::RayTest(pe, position, topoint, callback);
				if (result)	{
					MT_Vector3 newnormal = callback.m_hitNormal;
					// compute new position & orientation
					if ((m_option & (KX_ACT_CONSTRAINT_NORMAL|KX_ACT_CONSTRAINT_DISTANCE)) == 0) {
						// if none option is set, the actuator does nothing but detect ray 
						// (works like a sensor)
						goto CHECK_TIME;
					}
					if (m_option & KX_ACT_CONSTRAINT_NORMAL) {
						MT_Scalar rotFilter;
						// apply damping on the direction
						if (m_rotDampTime) {
							rotFilter = m_rotDampTime/(1.0+m_rotDampTime);
						} else {
							rotFilter = filter;
						}
						newnormal = rotFilter*normal - (1.0-rotFilter)*newnormal;
						obj->AlignAxisToVect((sign)?-newnormal:newnormal, axis);
						if (m_option & KX_ACT_CONSTRAINT_LOCAL) {
							direction = newnormal;
							direction.normalize();
						}
					}
					if (m_option & KX_ACT_CONSTRAINT_DISTANCE) {
						if (m_posDampTime) {
							newdistance = filter*(position-callback.m_hitPoint).length()+(1.0-filter)*m_minimumBound;
						} else {
							newdistance = m_minimumBound;
						}
						// logically we should cancel the speed along the ray direction as we set the
						// position along that axis
						spc = obj->GetPhysicsController();
						if (spc && spc->IsDyna()) {
							MT_Vector3 linV = spc->GetLinearVelocity();
							// cancel the projection along the ray direction
							MT_Scalar fallspeed = linV.dot(direction);
							if (!MT_fuzzyZero(fallspeed))
								spc->SetLinearVelocity(linV-fallspeed*direction,false);
						}
					} else {
						newdistance = (position-callback.m_hitPoint).length();
					}
					newposition = callback.m_hitPoint-newdistance*direction;
				} else if (m_option & KX_ACT_CONSTRAINT_PERMANENT) {
					// no contact but still keep running
					result = true;
					goto CHECK_TIME;
				}
			}
			break; 
		case KX_ACT_CONSTRAINT_FHPX:
		case KX_ACT_CONSTRAINT_FHPY:
		case KX_ACT_CONSTRAINT_FHPZ:
		case KX_ACT_CONSTRAINT_FHNX:
		case KX_ACT_CONSTRAINT_FHNY:
		case KX_ACT_CONSTRAINT_FHNZ:
			switch (m_locrot) {
			case KX_ACT_CONSTRAINT_FHPX:
				normal[0] = -rotation[0][0];
				normal[1] = -rotation[1][0];
				normal[2] = -rotation[2][0];
				direction = MT_Vector3(1.0,0.0,0.0);
				break;
			case KX_ACT_CONSTRAINT_FHPY:
				normal[0] = -rotation[0][1];
				normal[1] = -rotation[1][1];
				normal[2] = -rotation[2][1];
				direction = MT_Vector3(0.0,1.0,0.0);
				break;
			case KX_ACT_CONSTRAINT_FHPZ:
				normal[0] = -rotation[0][2];
				normal[1] = -rotation[1][2];
				normal[2] = -rotation[2][2];
				direction = MT_Vector3(0.0,0.0,1.0);
				break;
			case KX_ACT_CONSTRAINT_FHNX:
				normal[0] = rotation[0][0];
				normal[1] = rotation[1][0];
				normal[2] = rotation[2][0];
				direction = MT_Vector3(-1.0,0.0,0.0);
				break;
			case KX_ACT_CONSTRAINT_FHNY:
				normal[0] = rotation[0][1];
				normal[1] = rotation[1][1];
				normal[2] = rotation[2][1];
				direction = MT_Vector3(0.0,-1.0,0.0);
				break;
			case KX_ACT_CONSTRAINT_FHNZ:
				normal[0] = rotation[0][2];
				normal[1] = rotation[1][2];
				normal[2] = rotation[2][2];
				direction = MT_Vector3(0.0,0.0,-1.0);
				break;
			}
			normal.normalize();
			{
				PHY_IPhysicsEnvironment* pe = obj->GetPhysicsEnvironment();
				KX_IPhysicsController *spc = obj->GetPhysicsController();

				if (!pe) {
					std::cout << "WARNING: Constraint actuator " << GetName() << ":  There is no physics environment!" << std::endl;
					goto CHECK_TIME;
				}	 
				if (!spc || !spc->IsDyna()) {
					// the object is not dynamic, it won't support setting speed
					goto CHECK_TIME;
				}
				m_hitObject = NULL;
				// distance of Fh area is stored in m_minimum
				MT_Point3 topoint = position + (m_minimumBound+spc->GetRadius()) * direction;
				KX_RayCast::Callback<KX_ConstraintActuator> callback(this,spc);
				result = KX_RayCast::RayTest(pe, position, topoint, callback);
				// we expect a hit object
				if (!m_hitObject)
					result = false;
				if (result)	
				{
					MT_Vector3 newnormal = callback.m_hitNormal;
					// compute new position & orientation
					MT_Scalar distance = (callback.m_hitPoint-position).length()-spc->GetRadius(); 
					// estimate the velocity of the hit point
					MT_Point3 relativeHitPoint;
					relativeHitPoint = (callback.m_hitPoint-m_hitObject->NodeGetWorldPosition());
					MT_Vector3 velocityHitPoint = m_hitObject->GetVelocity(relativeHitPoint);
					MT_Vector3 relativeVelocity = spc->GetLinearVelocity() - velocityHitPoint;
					MT_Scalar relativeVelocityRay = direction.dot(relativeVelocity);
					MT_Scalar springExtent = 1.0 - distance/m_minimumBound;
					// Fh force is stored in m_maximum
					MT_Scalar springForce = springExtent * m_maximumBound;
					// damping is stored in m_refDirection [0] = damping, [1] = rot damping
					MT_Scalar springDamp = relativeVelocityRay * m_refDirection[0];
					MT_Vector3 newVelocity = spc->GetLinearVelocity()-(springForce+springDamp)*direction;
					if (m_option & KX_ACT_CONSTRAINT_NORMAL)
					{
						newVelocity+=(springForce+springDamp)*(newnormal-newnormal.dot(direction)*direction);
					}
					spc->SetLinearVelocity(newVelocity, false);
					if (m_option & KX_ACT_CONSTRAINT_DOROTFH)
					{
						MT_Vector3 angSpring = (normal.cross(newnormal))*m_maximumBound;
						MT_Vector3 angVelocity = spc->GetAngularVelocity();
						// remove component that is parallel to normal
						angVelocity -= angVelocity.dot(newnormal)*newnormal;
						MT_Vector3 angDamp = angVelocity * ((m_refDirection[1]>MT_EPSILON)?m_refDirection[1]:m_refDirection[0]);
						spc->SetAngularVelocity(spc->GetAngularVelocity()+(angSpring-angDamp), false);
					}
				} else if (m_option & KX_ACT_CONSTRAINT_PERMANENT) {
					// no contact but still keep running
					result = true;
				}
				// don't set the position with this constraint
				goto CHECK_TIME;
			}
			break; 
		case KX_ACT_CONSTRAINT_LOCX:
		case KX_ACT_CONSTRAINT_LOCY:
		case KX_ACT_CONSTRAINT_LOCZ:
			newposition = position = obj->GetSGNode()->GetLocalPosition();
			switch (m_locrot) {
			case KX_ACT_CONSTRAINT_LOCX:
				Clamp(newposition[0], m_minimumBound, m_maximumBound);
				break;
			case KX_ACT_CONSTRAINT_LOCY:
				Clamp(newposition[1], m_minimumBound, m_maximumBound);
				break;
			case KX_ACT_CONSTRAINT_LOCZ:
				Clamp(newposition[2], m_minimumBound, m_maximumBound);
				break;
			}
			result = true;
			if (m_posDampTime) {
				newposition = filter*position + (1.0-filter)*newposition;
			}
			obj->NodeSetLocalPosition(newposition);
			goto CHECK_TIME;
		}
		if (result) {
			// set the new position but take into account parent if any
			obj->NodeSetWorldPosition(newposition);
		}
	CHECK_TIME:
		if (result && m_activeTime > 0 ) {
			if (++m_currentTime >= m_activeTime)
				result = false;
		}
	}
	if (!result) {
		m_currentTime = 0;
	}
	return result;
} /* end of KX_ConstraintActuator::Update(double curtime,double deltatime)   */

void KX_ConstraintActuator::Clamp(MT_Scalar &var, 
								  float min, 
								  float max) {
	if (var < min) {
		var = min;
	} else if (var > max) {
		var = max;
	}
}


bool KX_ConstraintActuator::IsValidMode(KX_ConstraintActuator::KX_CONSTRAINTTYPE m) 
{
	bool res = false;

	if ( (m > KX_ACT_CONSTRAINT_NODEF) && (m < KX_ACT_CONSTRAINT_MAX)) {
		res = true;
	}

	return res;
}

/* ------------------------------------------------------------------------- */
/* Python functions                                                          */
/* ------------------------------------------------------------------------- */

/* Integration hooks ------------------------------------------------------- */
PyTypeObject KX_ConstraintActuator::Type = {
	PyObject_HEAD_INIT(&PyType_Type)
	0,
	"KX_ConstraintActuator",
	sizeof(KX_ConstraintActuator),
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

PyParentObject KX_ConstraintActuator::Parents[] = {
	&KX_ConstraintActuator::Type,
	&SCA_IActuator::Type,
	&SCA_ILogicBrick::Type,
	&CValue::Type,
	NULL
};

PyMethodDef KX_ConstraintActuator::Methods[] = {
	{"setDamp", (PyCFunction) KX_ConstraintActuator::sPySetDamp, METH_VARARGS, (PY_METHODCHAR)SetDamp_doc},
	{"getDamp", (PyCFunction) KX_ConstraintActuator::sPyGetDamp, METH_NOARGS, (PY_METHODCHAR)GetDamp_doc},
	{"setRotDamp", (PyCFunction) KX_ConstraintActuator::sPySetRotDamp, METH_VARARGS, (PY_METHODCHAR)SetRotDamp_doc},
	{"getRotDamp", (PyCFunction) KX_ConstraintActuator::sPyGetRotDamp, METH_NOARGS, (PY_METHODCHAR)GetRotDamp_doc},
	{"setDirection", (PyCFunction) KX_ConstraintActuator::sPySetDirection, METH_VARARGS, (PY_METHODCHAR)SetDirection_doc},
	{"getDirection", (PyCFunction) KX_ConstraintActuator::sPyGetDirection, METH_NOARGS, (PY_METHODCHAR)GetDirection_doc},
	{"setOption", (PyCFunction) KX_ConstraintActuator::sPySetOption, METH_VARARGS, (PY_METHODCHAR)SetOption_doc},
	{"getOption", (PyCFunction) KX_ConstraintActuator::sPyGetOption, METH_NOARGS, (PY_METHODCHAR)GetOption_doc},
	{"setTime", (PyCFunction) KX_ConstraintActuator::sPySetTime, METH_VARARGS, (PY_METHODCHAR)SetTime_doc},
	{"getTime", (PyCFunction) KX_ConstraintActuator::sPyGetTime, METH_NOARGS, (PY_METHODCHAR)GetTime_doc},
	{"setProperty", (PyCFunction) KX_ConstraintActuator::sPySetProperty, METH_VARARGS, (PY_METHODCHAR)SetProperty_doc},
	{"getProperty", (PyCFunction) KX_ConstraintActuator::sPyGetProperty, METH_NOARGS, (PY_METHODCHAR)GetProperty_doc},
	{"setMin", (PyCFunction) KX_ConstraintActuator::sPySetMin, METH_VARARGS, (PY_METHODCHAR)SetMin_doc},
	{"getMin", (PyCFunction) KX_ConstraintActuator::sPyGetMin, METH_NOARGS, (PY_METHODCHAR)GetMin_doc},
	{"setDistance", (PyCFunction) KX_ConstraintActuator::sPySetMin, METH_VARARGS, (PY_METHODCHAR)SetDistance_doc},
	{"getDistance", (PyCFunction) KX_ConstraintActuator::sPyGetMin, METH_NOARGS, (PY_METHODCHAR)GetDistance_doc},
	{"setMax", (PyCFunction) KX_ConstraintActuator::sPySetMax, METH_VARARGS, (PY_METHODCHAR)SetMax_doc},
	{"getMax", (PyCFunction) KX_ConstraintActuator::sPyGetMax, METH_NOARGS, (PY_METHODCHAR)GetMax_doc},
	{"setRayLength", (PyCFunction) KX_ConstraintActuator::sPySetMax, METH_VARARGS, (PY_METHODCHAR)SetRayLength_doc},
	{"getRayLength", (PyCFunction) KX_ConstraintActuator::sPyGetMax, METH_NOARGS, (PY_METHODCHAR)GetRayLength_doc},
	{"setLimit", (PyCFunction) KX_ConstraintActuator::sPySetLimit, METH_VARARGS, (PY_METHODCHAR)SetLimit_doc},
	{"getLimit", (PyCFunction) KX_ConstraintActuator::sPyGetLimit, METH_NOARGS, (PY_METHODCHAR)GetLimit_doc},
	{NULL,NULL} //Sentinel
};

PyObject* KX_ConstraintActuator::_getattr(const STR_String& attr) {
	_getattr_up(SCA_IActuator);
}

/* 2. setDamp                                                                */
const char KX_ConstraintActuator::SetDamp_doc[] = 
"setDamp(duration)\n"
"\t- duration: integer\n"
"\tSets the time constant of the orientation and distance constraint.\n"
"\tIf the duration is negative, it is set to 0.\n";
PyObject* KX_ConstraintActuator::PySetDamp(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	int dampArg;
	if(!PyArg_ParseTuple(args, "i", &dampArg)) {
		return NULL;		
	}
	
	m_posDampTime = dampArg;
	if (m_posDampTime < 0) m_posDampTime = 0;

	Py_Return;
}
/* 3. getDamp                                                                */
const char KX_ConstraintActuator::GetDamp_doc[] = 
"getDamp()\n"
"\tReturns the damping parameter.\n";
PyObject* KX_ConstraintActuator::PyGetDamp(PyObject* self){
	return PyInt_FromLong(m_posDampTime);
}

/* 2. setRotDamp                                                                */
const char KX_ConstraintActuator::SetRotDamp_doc[] = 
"setRotDamp(duration)\n"
"\t- duration: integer\n"
"\tSets the time constant of the orientation constraint.\n"
"\tIf the duration is negative, it is set to 0.\n";
PyObject* KX_ConstraintActuator::PySetRotDamp(PyObject* self, 
										      PyObject* args, 
										      PyObject* kwds) {
	int dampArg;
	if(!PyArg_ParseTuple(args, "i", &dampArg)) {
		return NULL;		
	}
	
	m_rotDampTime = dampArg;
	if (m_rotDampTime < 0) m_rotDampTime = 0;

	Py_Return;
}
/* 3. getRotDamp                                                                */
const char KX_ConstraintActuator::GetRotDamp_doc[] = 
"getRotDamp()\n"
"\tReturns the damping time for application of the constraint.\n";
PyObject* KX_ConstraintActuator::PyGetRotDamp(PyObject* self){
	return PyInt_FromLong(m_rotDampTime);
}

/* 2. setDirection                                                                */
const char KX_ConstraintActuator::SetDirection_doc[] = 
"setDirection(vector)\n"
"\t- vector: 3-tuple\n"
"\tSets the reference direction in world coordinate for the orientation constraint.\n";
PyObject* KX_ConstraintActuator::PySetDirection(PyObject* self, 
										        PyObject* args, 
										        PyObject* kwds) {
	float x, y, z;
	MT_Scalar len;
	MT_Vector3 dir;

	if(!PyArg_ParseTuple(args, "(fff)", &x, &y, &z)) {
		return NULL;		
	}
	dir[0] = x;
	dir[1] = y;
	dir[2] = z;
	len = dir.length();
	if (MT_fuzzyZero(len)) {
		std::cout << "Invalid direction" << std::endl;
		return NULL;
	}
	m_refDirection = dir/len;

	Py_Return;
}
/* 3. getDirection                                                                */
const char KX_ConstraintActuator::GetDirection_doc[] = 
"getDirection()\n"
"\tReturns the reference direction of the orientation constraint as a 3-tuple.\n";
PyObject* KX_ConstraintActuator::PyGetDirection(PyObject* self){
	PyObject *retVal = PyList_New(3);

	PyList_SetItem(retVal, 0, PyFloat_FromDouble(m_refDirection[0]));
	PyList_SetItem(retVal, 1, PyFloat_FromDouble(m_refDirection[1]));
	PyList_SetItem(retVal, 2, PyFloat_FromDouble(m_refDirection[2]));
	return retVal;
}

/* 2. setOption                                                                */
const char KX_ConstraintActuator::SetOption_doc[] = 
"setOption(option)\n"
"\t- option: integer\n"
"\tSets several options of the distance  constraint.\n"
"\tBinary combination of the following values:\n"
"\t\t 64 : Activate alignment to surface\n"
"\t\t128 : Detect material rather than property\n"
"\t\t256 : No deactivation if ray does not hit target\n"
"\t\t512 : Activate distance control\n";
PyObject* KX_ConstraintActuator::PySetOption(PyObject* self, 
										     PyObject* args, 
										     PyObject* kwds) {
	int option;
	if(!PyArg_ParseTuple(args, "i", &option)) {
		return NULL;		
	}
	
	m_option = option;

	Py_Return;
}
/* 3. getOption                                                              */
const char KX_ConstraintActuator::GetOption_doc[] = 
"getOption()\n"
"\tReturns the option parameter.\n";
PyObject* KX_ConstraintActuator::PyGetOption(PyObject* self){
	return PyInt_FromLong(m_option);
}

/* 2. setTime                                                                */
const char KX_ConstraintActuator::SetTime_doc[] = 
"setTime(duration)\n"
"\t- duration: integer\n"
"\tSets the activation time of the actuator.\n"
"\tThe actuator disables itself after this many frame.\n"
"\tIf set to 0 or negative, the actuator is not limited in time.\n";
PyObject* KX_ConstraintActuator::PySetTime(PyObject* self, 
										   PyObject* args, 
										   PyObject* kwds) {
	int t;
	if(!PyArg_ParseTuple(args, "i", &t)) {
		return NULL;		
	}
	
	if (t < 0)
		t = 0;
	m_activeTime = t;

	Py_Return;
}
/* 3. getTime                                                                */
const char KX_ConstraintActuator::GetTime_doc[] = 
"getTime()\n"
"\tReturns the time parameter.\n";
PyObject* KX_ConstraintActuator::PyGetTime(PyObject* self){
	return PyInt_FromLong(m_activeTime);
}

/* 2. setProperty                                                                */
const char KX_ConstraintActuator::SetProperty_doc[] = 
"setProperty(property)\n"
"\t- property: string\n"
"\tSets the name of the property or material for the ray detection of the distance constraint.\n"
"\tIf empty, the ray will detect any collisioning object.\n";
PyObject* KX_ConstraintActuator::PySetProperty(PyObject* self, 
										       PyObject* args, 
										       PyObject* kwds) {
	char *property;
	if (!PyArg_ParseTuple(args, "s", &property)) {
		return NULL;
	}
	if (property == NULL) {
		m_property[0] = 0;
	} else {
		strncpy(m_property, property, sizeof(m_property));
		m_property[sizeof(m_property)-1] = 0;
	}

	Py_Return;
}
/* 3. getProperty                                                                */
const char KX_ConstraintActuator::GetProperty_doc[] = 
"getProperty()\n"
"\tReturns the property parameter.\n";
PyObject* KX_ConstraintActuator::PyGetProperty(PyObject* self){
	return PyString_FromString(m_property);
}

/* 4. setDistance                                                                 */
const char KX_ConstraintActuator::SetDistance_doc[] = 
"setDistance(distance)\n"
"\t- distance: float\n"
"\tSets the target distance in distance constraint\n";
/* 4. setMin                                                                 */
const char KX_ConstraintActuator::SetMin_doc[] = 
"setMin(lower_bound)\n"
"\t- lower_bound: float\n"
"\tSets the lower value of the interval to which the value\n"
"\tis clipped.\n";
PyObject* KX_ConstraintActuator::PySetMin(PyObject* self, 
										  PyObject* args, 
										  PyObject* kwds) {
	float minArg;
	if(!PyArg_ParseTuple(args, "f", &minArg)) {
		return NULL;		
	}

	switch (m_locrot) {
	default:
		m_minimumBound = minArg;
		break;
	case KX_ACT_CONSTRAINT_ROTX:
	case KX_ACT_CONSTRAINT_ROTY:
	case KX_ACT_CONSTRAINT_ROTZ:
		m_minimumBound = MT_radians(minArg);
		break;
	}

	Py_Return;
}
/* 5. getDistance                                                                 */
const char KX_ConstraintActuator::GetDistance_doc[] = 
"getDistance()\n"
"\tReturns the distance parameter \n";
/* 5. getMin                                                                 */
const char KX_ConstraintActuator::GetMin_doc[] = 
"getMin()\n"
"\tReturns the lower value of the interval to which the value\n"
"\tis clipped.\n";
PyObject* KX_ConstraintActuator::PyGetMin(PyObject* self) {
	return PyFloat_FromDouble(m_minimumBound);
}

/* 6. setRayLength                                                                 */
const char KX_ConstraintActuator::SetRayLength_doc[] = 
"setRayLength(length)\n"
"\t- length: float\n"
"\tSets the maximum ray length of the distance constraint\n";
/* 6. setMax                                                                 */
const char KX_ConstraintActuator::SetMax_doc[] = 
"setMax(upper_bound)\n"
"\t- upper_bound: float\n"
"\tSets the upper value of the interval to which the value\n"
"\tis clipped.\n";
PyObject* KX_ConstraintActuator::PySetMax(PyObject* self, 
										  PyObject* args, 
										  PyObject* kwds){
	float maxArg;
	if(!PyArg_ParseTuple(args, "f", &maxArg)) {
		return NULL;		
	}

	switch (m_locrot) {
	default:
		m_maximumBound = maxArg;
		break;
	case KX_ACT_CONSTRAINT_ROTX:
	case KX_ACT_CONSTRAINT_ROTY:
	case KX_ACT_CONSTRAINT_ROTZ:
		m_maximumBound = MT_radians(maxArg);
		break;
	}

	Py_Return;
}
/* 7. getRayLength                                                                 */
const char KX_ConstraintActuator::GetRayLength_doc[] = 
"getRayLength()\n"
"\tReturns the length of the ray\n";
/* 7. getMax                                                                 */
const char KX_ConstraintActuator::GetMax_doc[] = 
"getMax()\n"
"\tReturns the upper value of the interval to which the value\n"
"\tis clipped.\n";
PyObject* KX_ConstraintActuator::PyGetMax(PyObject* self) {
	return PyFloat_FromDouble(m_maximumBound);
}


/* This setter/getter probably for the constraint type                       */
/* 8. setLimit                                                               */
const char KX_ConstraintActuator::SetLimit_doc[] = 
"setLimit(type)\n"
"\t- type: integer\n"
"\t  1  : LocX\n"
"\t  2  : LocY\n"
"\t  3  : LocZ\n"
"\t  7  : Distance along +X axis\n"
"\t  8  : Distance along +Y axis\n"
"\t  9  : Distance along +Z axis\n"
"\t  10 : Distance along -X axis\n"
"\t  11 : Distance along -Y axis\n"
"\t  12 : Distance along -Z axis\n"
"\t  13 : Align X axis\n"
"\t  14 : Align Y axis\n"
"\t  15 : Align Z axis\n"
"\tSets the type of constraint.\n";
PyObject* KX_ConstraintActuator::PySetLimit(PyObject* self, 
											PyObject* args, 
											PyObject* kwds) {
	int locrotArg;
	if(!PyArg_ParseTuple(args, "i", &locrotArg)) {
		return NULL;		
	}
	
	if (IsValidMode((KX_CONSTRAINTTYPE)locrotArg)) m_locrot = locrotArg;

	Py_Return;
}
/* 9. getLimit                                                               */
const char KX_ConstraintActuator::GetLimit_doc[] = 
"getLimit()\n"
"\tReturns the type of constraint.\n";
PyObject* KX_ConstraintActuator::PyGetLimit(PyObject* self) {
	return PyInt_FromLong(m_locrot);
}

/* eof */
