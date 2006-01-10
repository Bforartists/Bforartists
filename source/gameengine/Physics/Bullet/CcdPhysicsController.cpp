#include "CcdPhysicsController.h"

#include "Dynamics/RigidBody.h"
#include "PHY_IMotionState.h"
#include "BroadphaseCollision/BroadphaseProxy.h"
#include "CollisionShapes/ConvexShape.h"
#include "CcdPhysicsEnvironment.h"


class BP_Proxy;

///todo: fill all the empty CcdPhysicsController methods, hook them up to the RigidBody class

//'temporarily' global variables
float	gDeactivationTime = 2.f;
bool	gDisableDeactivation = false;

float gLinearSleepingTreshold = 0.8f;
float gAngularSleepingTreshold = 1.0f;

#include "Dynamics/MassProps.h"

SimdVector3 startVel(0,0,0);//-10000);
CcdPhysicsController::CcdPhysicsController (const CcdConstructionInfo& ci)
:m_cci(ci)
{
	m_collisionDelay = 0;
	m_newClientInfo = 0;
	
	m_MotionState = ci.m_MotionState;


	m_broadphaseHandle = ci.m_broadphaseHandle;

	m_collisionShape = ci.m_collisionShape;

	CreateRigidbody();

	
	#ifdef WIN32
	if (m_body->getInvMass())
		m_body->setLinearVelocity(startVel);
	#endif

}

void CcdPhysicsController::CreateRigidbody()
{
	SimdTransform trans;
	float tmp[3];
	m_MotionState->getWorldPosition(tmp[0],tmp[1],tmp[2]);
	trans.setOrigin(SimdVector3(tmp[0],tmp[1],tmp[2]));

	SimdQuaternion orn;
	m_MotionState->getWorldOrientation(orn[0],orn[1],orn[2],orn[3]);
	trans.setRotation(orn);

	MassProps mp(m_cci.m_mass, m_cci.m_localInertiaTensor);

	m_body = new RigidBody(mp,0,0,m_cci.m_friction,m_cci.m_restitution);
	
	//
	// init the rigidbody properly
	//
	
	m_body->setMassProps(m_cci.m_mass, m_cci.m_localInertiaTensor * m_cci.m_inertiaFactor);
	m_body->setGravity( m_cci.m_gravity);
	m_body->setDamping(m_cci.m_linearDamping, m_cci.m_angularDamping);
	m_body->setCenterOfMassTransform( trans );


}

CcdPhysicsController::~CcdPhysicsController()
{
	//will be reference counted, due to sharing
	//delete m_collisionShape;
	m_cci.m_physicsEnv->removeCcdPhysicsController(this);
	delete m_MotionState;
	delete m_body;
}

		/**
			SynchronizeMotionStates ynchronizes dynas, kinematic and deformable entities (and do 'late binding')
		*/
bool		CcdPhysicsController::SynchronizeMotionStates(float time)
{
	const SimdVector3& worldPos = m_body->getCenterOfMassPosition();
	m_MotionState->setWorldPosition(worldPos[0],worldPos[1],worldPos[2]);
	
	const SimdQuaternion& worldquat = m_body->getOrientation();
	m_MotionState->setWorldOrientation(worldquat[0],worldquat[1],worldquat[2],worldquat[3]);

	m_MotionState->calculateWorldTransformations();

	float scale[3];
	m_MotionState->getWorldScaling(scale[0],scale[1],scale[2]);
	SimdVector3 scaling(scale[0],scale[1],scale[2]);
	m_collisionShape->setLocalScaling(scaling);

	return true;
}

		/**
			WriteMotionStateToDynamics synchronizes dynas, kinematic and deformable entities (and do 'late binding')
		*/
		
void		CcdPhysicsController::WriteMotionStateToDynamics(bool nondynaonly)
{

}
void		CcdPhysicsController::WriteDynamicsToMotionState()
{
}
		// controller replication
void		CcdPhysicsController::PostProcessReplica(class PHY_IMotionState* motionstate,class PHY_IPhysicsController* parentctrl)
{

	m_MotionState = motionstate;
	m_broadphaseHandle = 0;
	m_body = 0;
	CreateRigidbody();
			
	m_cci.m_physicsEnv->addCcdPhysicsController(this);


/*	SM_Object* dynaparent=0;
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
	*/



}

		// kinematic methods
void		CcdPhysicsController::RelativeTranslate(float dlocX,float dlocY,float dlocZ,bool local)
{
	SimdVector3 dloc(dlocX,dlocY,dlocZ);
	SimdTransform xform = m_body->getCenterOfMassTransform();

	if (local)
	{
		dloc = xform.getBasis()*dloc;
	}

	xform.setOrigin(xform.getOrigin() + dloc);
	this->m_body->setCenterOfMassTransform(xform);

}

void		CcdPhysicsController::RelativeRotate(const float rotval[9],bool local)
{
	if (m_body )
	{
		SimdMatrix3x3 drotmat(	rotval[0],rotval[1],rotval[2],
								rotval[4],rotval[5],rotval[6],
								rotval[8],rotval[9],rotval[10]);


		SimdMatrix3x3 currentOrn;
		GetWorldOrientation(currentOrn);

		SimdTransform xform = m_body->getCenterOfMassTransform();

		xform.setBasis(xform.getBasis()*(local ? 
		drotmat : (currentOrn.inverse() * drotmat * currentOrn)));

		m_body->setCenterOfMassTransform(xform);
	}

}

void CcdPhysicsController::GetWorldOrientation(SimdMatrix3x3& mat)
{
	float orn[4];
	m_MotionState->getWorldOrientation(orn[0],orn[1],orn[2],orn[3]);
	SimdQuaternion quat(orn[0],orn[1],orn[2],orn[3]);
	mat.setRotation(quat);
}

void		CcdPhysicsController::getOrientation(float &quatImag0,float &quatImag1,float &quatImag2,float &quatReal)
{
	SimdQuaternion q = m_body->getCenterOfMassTransform().getRotation();
	quatImag0 = q[0];
	quatImag1 = q[1];
	quatImag2 = q[2];
	quatReal = q[3];
}
void		CcdPhysicsController::setOrientation(float quatImag0,float quatImag1,float quatImag2,float quatReal)
{
	m_body->activate();

	SimdTransform xform  = m_body->getCenterOfMassTransform();
	xform.setRotation(SimdQuaternion(quatImag0,quatImag1,quatImag2,quatReal));
	m_body->setCenterOfMassTransform(xform);

}

void		CcdPhysicsController::setPosition(float posX,float posY,float posZ)
{
	m_body->activate();

	SimdTransform xform  = m_body->getCenterOfMassTransform();
	xform.setOrigin(SimdVector3(posX,posY,posZ));
	m_body->setCenterOfMassTransform(xform);

}
void		CcdPhysicsController::resolveCombinedVelocities(float linvelX,float linvelY,float linvelZ,float angVelX,float angVelY,float angVelZ)
{
}

void 		CcdPhysicsController::getPosition(PHY__Vector3&	pos) const
{
	const SimdTransform& xform = m_body->getCenterOfMassTransform();
	pos[0] = xform.getOrigin().x();
	pos[1] = xform.getOrigin().y();
	pos[2] = xform.getOrigin().z();
}

void		CcdPhysicsController::setScaling(float scaleX,float scaleY,float scaleZ)
{
	if (!SimdFuzzyZero(m_cci.m_scaling.x()-scaleX) ||
		!SimdFuzzyZero(m_cci.m_scaling.y()-scaleY) ||
		!SimdFuzzyZero(m_cci.m_scaling.z()-scaleZ))
	{
		m_cci.m_scaling = SimdVector3(scaleX,scaleY,scaleZ);

		if (m_body && m_body->GetCollisionShape())
		{
			m_body->GetCollisionShape()->setLocalScaling(m_cci.m_scaling);
			m_body->GetCollisionShape()->CalculateLocalInertia(m_cci.m_mass, m_cci.m_localInertiaTensor);
			m_body->setMassProps(m_cci.m_mass, m_cci.m_localInertiaTensor * m_cci.m_inertiaFactor);
		}
	}
}
		
		// physics methods
void		CcdPhysicsController::ApplyTorque(float torqueX,float torqueY,float torqueZ,bool local)
{
	SimdVector3 torque(torqueX,torqueY,torqueZ);
	SimdTransform xform = m_body->getCenterOfMassTransform();
	if (local)
	{
		torque	= xform.getBasis()*torque;
	}
	m_body->applyTorque(torque);
}

void		CcdPhysicsController::ApplyForce(float forceX,float forceY,float forceZ,bool local)
{
	SimdVector3 force(forceX,forceY,forceZ);
	SimdTransform xform = m_body->getCenterOfMassTransform();
	if (local)
	{
		force	= xform.getBasis()*force;
	}
	m_body->applyCentralForce(force);
}
void		CcdPhysicsController::SetAngularVelocity(float ang_velX,float ang_velY,float ang_velZ,bool local)
{
	SimdVector3 angvel(ang_velX,ang_velY,ang_velZ);
	SimdTransform xform = m_body->getCenterOfMassTransform();
	if (local)
	{
		angvel	= xform.getBasis()*angvel;
	}

	m_body->setAngularVelocity(angvel);

}
void		CcdPhysicsController::SetLinearVelocity(float lin_velX,float lin_velY,float lin_velZ,bool local)
{
	SimdVector3 linVel(lin_velX,lin_velY,lin_velZ);
	SimdTransform xform = m_body->getCenterOfMassTransform();
	if (local)
	{
		linVel	= xform.getBasis()*linVel;
	}
	m_body->setLinearVelocity(linVel);
}
void		CcdPhysicsController::applyImpulse(float attachX,float attachY,float attachZ, float impulseX,float impulseY,float impulseZ)
{
	
	SimdVector3 impulse(impulseX,impulseY,impulseZ);
	SimdVector3 pos(attachX,attachY,attachZ);

	m_body->activate();

	m_body->applyImpulse(impulse,pos);

}
void		CcdPhysicsController::SetActive(bool active)
{
}
		// reading out information from physics
void		CcdPhysicsController::GetLinearVelocity(float& linvX,float& linvY,float& linvZ)
{
	const SimdVector3& linvel = this->m_body->getLinearVelocity();
	linvX = linvel.x();
	linvY = linvel.y();
	linvZ = linvel.z();

}

void		CcdPhysicsController::GetAngularVelocity(float& angVelX,float& angVelY,float& angVelZ)
{
	const SimdVector3& angvel= m_body->getAngularVelocity();
	angVelX = angvel.x();
	angVelY = angvel.y();
	angVelZ = angvel.z();
}

void		CcdPhysicsController::GetVelocity(const float posX,const float posY,const float posZ,float& linvX,float& linvY,float& linvZ)
{
	SimdVector3 pos(posX,posY,posZ);
	SimdVector3 rel_pos = pos-m_body->getCenterOfMassPosition();
	SimdVector3 linvel = m_body->getVelocityInLocalPoint(rel_pos);
	linvX = linvel.x();
	linvY = linvel.y();
	linvZ = linvel.z();
}
void		CcdPhysicsController::getReactionForce(float& forceX,float& forceY,float& forceZ)
{
}

		// dyna's that are rigidbody are free in orientation, dyna's with non-rigidbody are restricted 
void		CcdPhysicsController::setRigidBody(bool rigid)
{
}

		// clientinfo for raycasts for example
void*		CcdPhysicsController::getNewClientInfo()
{
	return m_newClientInfo;
}
void		CcdPhysicsController::setNewClientInfo(void* clientinfo)
{
	m_newClientInfo = clientinfo;
}


void	CcdPhysicsController::UpdateDeactivation(float timeStep)
{
	if ( (m_body->GetActivationState() == 2))
		return;
	

	if ((m_body->getLinearVelocity().length2() < gLinearSleepingTreshold*gLinearSleepingTreshold) &&
		(m_body->getAngularVelocity().length2() < gAngularSleepingTreshold*gAngularSleepingTreshold))
	{
		m_body->m_deactivationTime += timeStep;
	} else
	{
		m_body->m_deactivationTime=0.f;
		m_body->SetActivationState(0);
	}

}

bool CcdPhysicsController::wantsSleeping()
{

	//disable deactivation
	if (gDisableDeactivation || (gDeactivationTime == 0.f))
		return false;
	//2 == ISLAND_SLEEPING, 3 == WANTS_DEACTIVATION
	if ( (m_body->GetActivationState() == 2) || (m_body->GetActivationState() == 3))
		return true;

	if (m_body->m_deactivationTime> gDeactivationTime)
	{
		return true;
	}
	return false;
}

