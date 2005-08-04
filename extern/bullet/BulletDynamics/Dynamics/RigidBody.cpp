#include "RigidBody.h"
#include "MassProps.h"
#include "CollisionShapes/ConvexShape.h"
#include "GEN_MinMax.h"
#include <SimdTransformUtil.h>

float gLinearAirDamping = 1.f;

static int uniqueId = 0;

RigidBody::RigidBody( const MassProps& massProps,SimdScalar linearDamping,SimdScalar angularDamping,SimdScalar friction,SimdScalar restitution)
: m_collisionShape(0),
	m_activationState1(1),
	m_deactivationTime(0.f),
	m_hitFraction(1.f),
	m_gravity(0.0f, 0.0f, 0.0f),
	m_linearDamping(0.f),
	m_angularDamping(0.5f),
	m_totalForce(0.0f, 0.0f, 0.0f),
	m_totalTorque(0.0f, 0.0f, 0.0f),
	m_linearVelocity(0.0f, 0.0f, 0.0f),
	m_angularVelocity(0.f,0.f,0.f),
	m_restitution(restitution),
	m_friction(friction)

{
	m_debugBodyId = uniqueId++;
	
	setMassProps(massProps.m_mass, massProps.m_inertiaLocal);
    setDamping(linearDamping, angularDamping);
	m_worldTransform.setIdentity();
	updateInertiaTensor();

}

void RigidBody::setLinearVelocity(const SimdVector3& lin_vel)
{ 

	m_linearVelocity = lin_vel; 
}


void RigidBody::predictIntegratedTransform(SimdScalar timeStep,SimdTransform& predictedTransform) const
{
	SimdTransformUtil::IntegrateTransform(m_worldTransform,m_linearVelocity,m_angularVelocity,timeStep,predictedTransform);
}

	
void	RigidBody::getAabb(SimdVector3& aabbMin,SimdVector3& aabbMax) const
{
	m_collisionShape ->GetAabb(m_worldTransform,aabbMin,aabbMax);
}

void	RigidBody::SetCollisionShape(CollisionShape* mink)
{
	m_collisionShape = mink;
	SimdTransform ident;
	ident.setIdentity();
	SimdVector3 aabbMin,aabbMax;
	m_collisionShape ->GetAabb(ident,aabbMin,aabbMax);
	SimdVector3 diag = (aabbMax-aabbMin)*0.5f;
}


void RigidBody::setGravity(const SimdVector3& acceleration) 
{
	if (m_inverseMass != 0.0f)
	{
		m_gravity = acceleration * (1.0f / m_inverseMass);
	}
}

bool RigidBody::mergesSimulationIslands() const
{
	return ( getInvMass() != 0) ;
}

void RigidBody::SetActivationState(int newState) 
{ 
	m_activationState1 = newState;
}



void RigidBody::setDamping(SimdScalar lin_damping, SimdScalar ang_damping)
{
	m_linearDamping = GEN_clamped(lin_damping, 0.0f, 1.0f);
	m_angularDamping = GEN_clamped(ang_damping, 0.0f, 1.0f);
}



#include <stdio.h>


void RigidBody::applyForces(SimdScalar step)
{
	
	applyCentralForce(m_gravity);	
	
	m_linearVelocity *= GEN_clamped((1.f - step * gLinearAirDamping * m_linearDamping), 0.0f, 1.0f);
	m_angularVelocity *= GEN_clamped((1.f - step * m_angularDamping), 0.0f, 1.0f);
	
}

void RigidBody::proceedToTransform(const SimdTransform& newTrans)
{
	setCenterOfMassTransform( newTrans );
}
	

void RigidBody::setMassProps(SimdScalar mass, const SimdVector3& inertia)
{
	m_inverseMass = mass != 0.0f ? 1.0f / mass : 0.0f;
	m_invInertiaLocal.setValue(inertia[0] != 0.0f ? 1.0f / inertia[0]: 0.0f,
						   inertia[1] != 0.0f ? 1.0f / inertia[1]: 0.0f,
						   inertia[2] != 0.0f ? 1.0f / inertia[2]: 0.0f);

}

	

void RigidBody::updateInertiaTensor() 
{
	m_invInertiaTensorWorld = m_worldTransform.getBasis().scaled(m_invInertiaLocal) * m_worldTransform.getBasis().transpose();
}


void RigidBody::integrateVelocities(SimdScalar step) 
{
	m_linearVelocity += m_totalForce * (m_inverseMass * step);
	m_angularVelocity += m_invInertiaTensorWorld * m_totalTorque * step;

#define MAX_ANGVEL SIMD_HALF_PI
	/// clamp angular velocity. collision calculations will fail on higher angular velocities	
	float angvel = m_angularVelocity.length();
	if (angvel*step > MAX_ANGVEL)
	{
		m_angularVelocity *= (MAX_ANGVEL/step) /angvel;
	}

	clearForces();
}

SimdQuaternion RigidBody::getOrientation() const
{
		SimdQuaternion orn;
		m_worldTransform.getBasis().getRotation(orn);
		return orn;
}
	
	
void RigidBody::setCenterOfMassTransform(const SimdTransform& xform)
{
	m_worldTransform = xform;
	SimdQuaternion orn;
//	m_worldTransform.getBasis().getRotation(orn);
//	orn.normalize();
//	m_worldTransform.setBasis(SimdMatrix3x3(orn));

//	m_worldTransform.getBasis().getRotation(m_orn1);
	updateInertiaTensor();
}



