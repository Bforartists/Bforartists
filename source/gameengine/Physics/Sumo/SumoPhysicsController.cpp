/**
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

#include "SumoPhysicsController.h"
#include "PHY_IMotionState.h"
#include "SM_Object.h"
#include "MT_Quaternion.h"

#ifdef HAVE_CONFIG_H
#include <config.h>
#endif

SumoPhysicsController::SumoPhysicsController(
				class SM_Scene* sumoScene,
				class SM_Object* sumoObj,
				class PHY_IMotionState* motionstate,

				bool dyna) 
		: 
		m_sumoObj(sumoObj) , 
		m_sumoScene(sumoScene),
		m_bFirstTime(true),
		m_bDyna(dyna),
		m_MotionState(motionstate)
{
	if (m_sumoObj)
	{
		//m_sumoObj->setClientObject(this);
		//if it is a dyna, register for a callback
		m_sumoObj->registerCallback(*this);
	}
};



SumoPhysicsController::~SumoPhysicsController()
{
	if (m_sumoObj)
	{
		m_sumoScene->remove(*m_sumoObj);
		
		delete m_sumoObj;
		m_sumoObj = NULL;
	}
}

float SumoPhysicsController::getMass()
{
	if (m_sumoObj)
	{
		const SM_ShapeProps *shapeprops = m_sumoObj->getShapeProps();
		return shapeprops->m_mass;
	}
	return 0.f;
}

bool SumoPhysicsController::SynchronizeMotionStates(float time)
{

	if (m_bFirstTime)
	{
		setSumoTransform(false);
		m_bFirstTime = false;
	}

	if (!m_bDyna)
	{
		if (m_sumoObj)
		{
			MT_Point3 pos;
			GetWorldPosition(pos);

			m_sumoObj->setPosition(pos);
			if (m_bDyna)
			{
				m_sumoObj->setScaling(MT_Vector3(1,1,1));
			} else
			{
				MT_Vector3 scaling;
				GetWorldScaling(scaling);
				m_sumoObj->setScaling(scaling);
			}
			MT_Matrix3x3 orn;
			GetWorldOrientation(orn);
			m_sumoObj->setOrientation(orn.getRotation());
			m_sumoObj->calcXform();
		}
	}
	return false; // physics object are not part of
				 // hierarchy, or ignore it ??
}
 



void SumoPhysicsController::GetWorldOrientation(MT_Matrix3x3& mat)
{
	float orn[4];
	m_MotionState->getWorldOrientation(orn[0],orn[1],orn[2],orn[3]);
	MT_Quaternion quat(orn);
	mat.setRotation(quat);

}

void SumoPhysicsController::GetWorldPosition(MT_Point3& pos)
{
	float worldpos[3];
	m_MotionState->getWorldPosition(worldpos[0],worldpos[1],worldpos[2]);
	pos[0]=worldpos[0];
	pos[1]=worldpos[1];
	pos[2]=worldpos[2];
}

void SumoPhysicsController::GetWorldScaling(MT_Vector3& scale)
{
	float worldscale[3];
	m_MotionState->getWorldScaling(worldscale[0],worldscale[1],worldscale[2]);
	scale[0]=worldscale[0];
	scale[1]=worldscale[1];
	scale[2]=worldscale[2];
}


		// kinematic methods
void		SumoPhysicsController::RelativeTranslate(float dlocX,float dlocY,float dlocZ,bool local)
{
	if (m_sumoObj)
	{
		MT_Matrix3x3 mat;
		GetWorldOrientation(mat);
		MT_Vector3 dloc(dlocX,dlocY,dlocZ);

		MT_Point3 newpos = m_sumoObj->getPosition();
		
		newpos += (local ? mat * dloc : dloc);
		m_sumoObj->setPosition(newpos);
	}

}
void		SumoPhysicsController::RelativeRotate(const float drot[12],bool local)
{
	if (m_sumoObj )
	{
		MT_Matrix3x3 drotmat(drot);
		MT_Matrix3x3 currentOrn;
		GetWorldOrientation(currentOrn);

		m_sumoObj->setOrientation(m_sumoObj->getOrientation()*(local ? 
		drotmat : (currentOrn.inverse() * drotmat * currentOrn)).getRotation());
	}

}
void		SumoPhysicsController::setOrientation(float quatImag0,float quatImag1,float quatImag2,float quatReal)
{
	m_sumoObj->setOrientation(MT_Quaternion(quatImag0,quatImag1,quatImag2,quatReal));
}

void		SumoPhysicsController::getOrientation(float &quatImag0,float &quatImag1,float &quatImag2,float &quatReal)
{
	const MT_Quaternion& q = m_sumoObj->getOrientation();
	quatImag0 = q[0];
	quatImag1 = q[1];
	quatImag2 = q[2];
	quatReal = q[3];
}

void		SumoPhysicsController::setPosition(float posX,float posY,float posZ)
{
	m_sumoObj->setPosition(MT_Point3(posX,posY,posZ));
}

void		SumoPhysicsController::setScaling(float scaleX,float scaleY,float scaleZ)
{
	m_sumoObj->setScaling(MT_Vector3(scaleX,scaleY,scaleZ));
}
	
	// physics methods
void		SumoPhysicsController::ApplyTorque(float torqueX,float torqueY,float torqueZ,bool local)
{
	if (m_sumoObj)
	{
		MT_Vector3 torque(torqueX,torqueY,torqueZ);

		MT_Matrix3x3 orn;
		GetWorldOrientation(orn);
		m_sumoObj->applyTorque(local ?
			orn * torque :
			torque);
	}
}

void		SumoPhysicsController::ApplyForce(float forceX,float forceY,float forceZ,bool local)
{
	if (m_sumoObj)
	{
		MT_Vector3 force(forceX,forceY,forceZ);

		MT_Matrix3x3 orn;
		GetWorldOrientation(orn);

		m_sumoObj->applyCenterForce(local ?
						orn * force :
						force);
	}
}

void		SumoPhysicsController::SetAngularVelocity(float ang_velX,float ang_velY,float ang_velZ,bool local)
{
	if (m_sumoObj)
	{
		MT_Vector3 ang_vel(ang_velX,ang_velY,ang_velZ);

		MT_Matrix3x3 orn;
		GetWorldOrientation(orn);

		m_sumoObj->setAngularVelocity(local ?
						orn * ang_vel :
						ang_vel);
	}
}
	
void		SumoPhysicsController::SetLinearVelocity(float lin_velX,float lin_velY,float lin_velZ,bool local)
{
	if (m_sumoObj )
	{
		MT_Matrix3x3 orn;
		GetWorldOrientation(orn);

		MT_Vector3 lin_vel(lin_velX,lin_velY,lin_velZ);
		m_sumoObj->setLinearVelocity(local ?
							   orn * lin_vel :
							   lin_vel);
	}
}

void SumoPhysicsController::resolveCombinedVelocities(
		const MT_Vector3 & lin_vel,
		const MT_Vector3 & ang_vel
	)
{
	if (m_sumoObj)
		m_sumoObj->resolveCombinedVelocities(lin_vel, ang_vel);
}


void		SumoPhysicsController::applyImpulse(float attachX,float attachY,float attachZ, float impulseX,float impulseY,float impulseZ)
{
	if (m_sumoObj)
	{
		MT_Point3 attach(attachX,attachY,attachZ);
		MT_Vector3 impulse(impulseX,impulseY,impulseZ);
		m_sumoObj->applyImpulse(attach,impulse);
	}

}

void		SumoPhysicsController::SuspendDynamics()
{
	m_suspendDynamics=true;
		
	if (m_sumoObj)
	{
		m_sumoObj->suspendDynamics();
		m_sumoObj->setLinearVelocity(MT_Vector3(0,0,0));
		m_sumoObj->setAngularVelocity(MT_Vector3(0,0,0));
		m_sumoObj->calcXform();
	}
}

void		SumoPhysicsController::RestoreDynamics()
{
	m_suspendDynamics=false;

	if (m_sumoObj)
	{
		m_sumoObj->restoreDynamics();
	}
}


/**  
	reading out information from physics
*/
void		SumoPhysicsController::GetLinearVelocity(float& linvX,float& linvY,float& linvZ)
{
	if (m_sumoObj)
	{
		// get velocity from the physics object (m_sumoObj)
		const MT_Vector3& vel = m_sumoObj->getLinearVelocity();
		linvX = vel[0];
		linvY = vel[1];
		linvZ = vel[2];
	} 
	else
	{
		linvX = 0.f;
		linvY = 0.f;
		linvZ = 0.f;
	}
}

/** 
	GetVelocity parameters are in geometric coordinates (Origin is not center of mass!).
*/
void		SumoPhysicsController::GetVelocity(const float posX,const float posY,const float posZ,float& linvX,float& linvY,float& linvZ)
{
	if (m_sumoObj)
	{
		MT_Point3 pos(posX,posY,posZ);
		// get velocity from the physics object (m_sumoObj)
		const MT_Vector3& vel = m_sumoObj->getVelocity(pos);
		linvX = vel[0];
		linvY = vel[1];
		linvZ = vel[2];
	} 
	else
	{
		linvX = 0.f;
		linvY = 0.f;
		linvZ = 0.f;
		
	}
}

void		SumoPhysicsController::getReactionForce(float& forceX,float& forceY,float& forceZ)
{
	const MT_Vector3& force = m_sumoObj->getReactionForce();
	forceX = force[0];
	forceY = force[1];
	forceZ = force[2];
}

void		SumoPhysicsController::setRigidBody(bool rigid)
{
	m_sumoObj->setRigidBody(rigid);
}

void		SumoPhysicsController::PostProcessReplica(class PHY_IMotionState* motionstate,class PHY_IPhysicsController* parentctrl)
{
	m_MotionState = motionstate;

	SM_Object* dynaparent=0;
	SumoPhysicsController* sumoparentctrl = (SumoPhysicsController* )parentctrl;
	
	if (sumoparentctrl)
	{
		dynaparent = sumoparentctrl->GetSumoObject();
	}
	
	SM_Object* orgsumoobject = m_sumoObj;
	
	
	m_sumoObj	=	new SM_Object(
		orgsumoobject->getShapeHandle(), 
		orgsumoobject->getMaterialProps(),			
		orgsumoobject->getShapeProps(),
		dynaparent);
	
	m_sumoObj->setRigidBody(orgsumoobject->isRigidBody());
	
	m_sumoObj->setMargin(orgsumoobject->getMargin());
	m_sumoObj->setPosition(orgsumoobject->getPosition());
	m_sumoObj->setOrientation(orgsumoobject->getOrientation());
	//if it is a dyna, register for a callback
	m_sumoObj->registerCallback(*this);
	
	m_sumoScene->add(* (m_sumoObj));
}

void			SumoPhysicsController::SetSimulatedTime(float time)
{
}
	
	
void	SumoPhysicsController::WriteMotionStateToDynamics(bool nondynaonly)
{

}
// this is the actual callback from sumo, and the position/orientation
//is written to the scenegraph, using the motionstate abstraction

void SumoPhysicsController::do_me()
{
	const MT_Point3& pos = m_sumoObj->getPosition();
	const MT_Quaternion& orn = m_sumoObj->getOrientation();

	m_MotionState->setWorldPosition(pos[0],pos[1],pos[2]);
	m_MotionState->setWorldOrientation(orn[0],orn[1],orn[2],orn[3]);
}


void	SumoPhysicsController::setSumoTransform(bool nondynaonly)
{
	if (!nondynaonly || !m_bDyna)
	{
		if (m_sumoObj)
		{
			MT_Point3 pos;
			GetWorldPosition(pos);

			m_sumoObj->setPosition(pos);
			if (m_bDyna)
			{
				m_sumoObj->setScaling(MT_Vector3(1,1,1));
			} else
			{
				MT_Vector3 scale;
				GetWorldScaling(scale);
				m_sumoObj->setScaling(scale);
			}
			MT_Matrix3x3 orn;
			GetWorldOrientation(orn);
			m_sumoObj->setOrientation(orn.getRotation());
			m_sumoObj->calcXform();
		}
	}
}
