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
#include <string.h>		// memset
#include "SumoPhysicsEnvironment.h"
#include "PHY_IMotionState.h"
#include "SumoPhysicsController.h"
#include "SM_Scene.h"
#include "SumoPHYCallbackBridge.h"
#include <SOLID/SOLID.h>

SumoPhysicsEnvironment::SumoPhysicsEnvironment()
{
	m_fixedTimeStep = 1.f/60.f;
	m_useFixedTimeStep = true;
	m_currentTime = 0.f;

	m_sumoScene = new SM_Scene();
}



SumoPhysicsEnvironment::~SumoPhysicsEnvironment()
{
	delete m_sumoScene;
}



void SumoPhysicsEnvironment::beginFrame()
{
	m_sumoScene->beginFrame();
}

void SumoPhysicsEnvironment::endFrame()
{
	m_sumoScene->endFrame();
}

void		SumoPhysicsEnvironment::setFixedTimeStep(bool useFixedTimeStep,float fixedTimeStep)
{
	m_useFixedTimeStep = useFixedTimeStep;
	if (m_useFixedTimeStep)
	{
		m_fixedTimeStep = fixedTimeStep;
	} else
	{
		m_fixedTimeStep  = 0.f;
	}
	//reset current time ?
	m_currentTime = 0.f;
}
float		SumoPhysicsEnvironment::getFixedTimeStep()
{
	return m_fixedTimeStep;
}


bool		SumoPhysicsEnvironment::proceedDeltaTime(double  curTime,float timeStep,float interval)
{
	
	bool result = false;
	if (m_useFixedTimeStep)
	{
		m_currentTime += timeStep;
		float ticrate = 1.f/m_fixedTimeStep;

		result = m_sumoScene->proceed(curTime, ticrate);
	} else
	{
		m_currentTime += timeStep;
		result = m_sumoScene->proceed(m_currentTime, timeStep);
	}
	return result;
}

void SumoPhysicsEnvironment::setGravity(float x,float y,float z)
{
	m_sumoScene->setForceField(MT_Vector3(x,y,z));
}

int SumoPhysicsEnvironment::createConstraint(
	class PHY_IPhysicsController* ctrl,
	class PHY_IPhysicsController* ctrl2,
	PHY_ConstraintType type,
	float pivotX,float pivotY,float pivotZ,
	float axisX,float axisY,float axisZ,
	float axis1X,float axis1Y,float axis1Z,
	float axis2X,float axis2Y,float axis2Z,
	int flag
	)
{
	int constraintid = 0;
	return constraintid;
}

void SumoPhysicsEnvironment::removeConstraint(int	constraintid)
{
	if (constraintid)
	{
	}
}

PHY_IPhysicsController* SumoPhysicsEnvironment::rayTest(PHY_IRayCastFilterCallback &filterCallback, 
	float fromX,float fromY,float fromZ, 
	float toX,float toY,float toZ)
{
	SumoPhysicsController* ignoreCtr = static_cast<SumoPhysicsController*> (filterCallback.m_ignoreController);

	//collision detection / raytesting
	MT_Point3 hit, normal;
	PHY_RayCastResult result;

	SM_Object* sm_ignore = 0;
	if (ignoreCtr)
		sm_ignore = ignoreCtr->GetSumoObject();

	memset(&result, 0, sizeof(result));

	SM_Object* smOb = m_sumoScene->rayTest(sm_ignore,MT_Point3(fromX, fromY, fromZ),MT_Point3(toX, toY, toZ), hit, normal);
	if (smOb)
	{
		result.m_controller = (PHY_IPhysicsController *) smOb->getPhysicsClientObject();
		result.m_hitPoint[0] = hit[0];
		result.m_hitPoint[1] = hit[1];
		result.m_hitPoint[2] = hit[2];
		result.m_hitNormal[0] = normal[0];
		result.m_hitNormal[1] = normal[1];
		result.m_hitNormal[2] = normal[2];
		filterCallback.reportHit(&result);
	}
	return result.m_controller;
}
//gamelogic callbacks
void SumoPhysicsEnvironment::addSensor(PHY_IPhysicsController* ctrl)
{
	SumoPhysicsController* smctrl = dynamic_cast<SumoPhysicsController*>(ctrl);
	SM_Object* smObject = smctrl->GetSumoObject();
	assert(smObject);
	if (smObject)
	{
		m_sumoScene->addSensor(*smObject);
	}
}
void SumoPhysicsEnvironment::removeSensor(PHY_IPhysicsController* ctrl)
{
	SumoPhysicsController* smctrl = dynamic_cast<SumoPhysicsController*>(ctrl);
	SM_Object* smObject = smctrl->GetSumoObject();
	assert(smObject);
	if (smObject)
	{
		m_sumoScene->remove(*smObject);
	}
}


void SumoPhysicsEnvironment::addTouchCallback(int response_class, PHY_ResponseCallback callback, void *user)
{
	
	int sumoRespClass = 0;

	//map PHY_ convention into SM_ convention
	switch (response_class)
	{
	case	PHY_FH_RESPONSE:
			sumoRespClass = FH_RESPONSE; 
		break;
	case PHY_SENSOR_RESPONSE:
		sumoRespClass = SENSOR_RESPONSE;
		break;
	case PHY_CAMERA_RESPONSE:
		sumoRespClass =CAMERA_RESPONSE;
		break;
	case PHY_OBJECT_RESPONSE:
		sumoRespClass = OBJECT_RESPONSE;
		break;
	case PHY_STATIC_RESPONSE:
		sumoRespClass = PHY_STATIC_RESPONSE;
		break;
	case PHY_BROADPH_RESPONSE:
		return;
	default:
		assert(0);
		return;
	}

	SumoPHYCallbackBridge* bridge = new SumoPHYCallbackBridge(user,callback);

	m_sumoScene->addTouchCallback(sumoRespClass,SumoPHYCallbackBridge::StaticSolidToPHYCallback,bridge);
}
bool SumoPhysicsEnvironment::requestCollisionCallback(PHY_IPhysicsController* ctrl)
{
	SumoPhysicsController* smctrl = dynamic_cast<SumoPhysicsController*>(ctrl);
	MT_assert(smctrl);
	SM_Object* smObject = smctrl->GetSumoObject();
	MT_assert(smObject);
	if (smObject)
	{
		//assert(smObject->getPhysicsClientObject() == ctrl);
		smObject->setPhysicsClientObject(ctrl);
	
		m_sumoScene->requestCollisionCallback(*smObject);
		return true;
	}
	return false;
}

bool SumoPhysicsEnvironment::removeCollisionCallback(PHY_IPhysicsController* ctrl)
{
	// intentionally empty
	return false;
}

PHY_IPhysicsController*	SumoPhysicsEnvironment::CreateSphereController(float radius,const PHY__Vector3& position)
{
	DT_ShapeHandle shape	=	DT_NewSphere(0.0);
	SM_Object* ob = new SM_Object(shape,0,0,0);	
	ob->setPosition(MT_Point3(position));
	//testing
	MT_Quaternion rotquatje(MT_Vector3(0,0,1),MT_radians(90));		
	ob->setOrientation(rotquatje);
	PHY_IMotionState* motionState = new SumoDefaultMotionState();
	PHY_IPhysicsController* ctrl = new SumoPhysicsController(m_sumoScene,ob,motionState,false);
	ctrl->SetMargin(radius);
	return ctrl;
}
PHY_IPhysicsController* SumoPhysicsEnvironment::CreateConeController(float coneradius,float coneheight)
{
	DT_ShapeHandle shape	=	DT_NewCone(coneradius,coneheight);
	SM_Object* ob = new SM_Object(shape,0,0,0);	
	ob->setPosition(MT_Point3(0.f,0.f,0.f));
	MT_Quaternion rotquatje(MT_Vector3(0,0,1),MT_radians(90));		
	ob->setOrientation(rotquatje);
	PHY_IMotionState* motionState = new SumoDefaultMotionState();

	PHY_IPhysicsController* ctrl = new SumoPhysicsController(m_sumoScene,ob,motionState,false);

	return ctrl;
}

