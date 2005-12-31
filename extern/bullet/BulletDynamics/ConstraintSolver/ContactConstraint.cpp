/*
 * Copyright (c) 2005 Erwin Coumans http://continuousphysics.com/Bullet/
 *
 * Permission to use, copy, modify, distribute and sell this software
 * and its documentation for any purpose is hereby granted without fee,
 * provided that the above copyright notice appear in all copies.
 * Erwin Coumans makes no representations about the suitability 
 * of this software for any purpose.  
 * It is provided "as is" without express or implied warranty.
*/
#include "ContactConstraint.h"
#include "Dynamics/RigidBody.h"
#include "SimdVector3.h"
#include "JacobianEntry.h"
#include "ContactSolverInfo.h"
#include "GEN_MinMax.h"

#define ASSERT2 assert

//some values to find stable penalty method tresholds
float MAX_FRICTION = 100.f;
static SimdScalar ContactThreshold = -10.0f;  
float useGlobalSettingContacts = false;//true;
SimdScalar contactDamping = 0.2f;
SimdScalar contactTau = .02f;//0.02f;//*0.02f;


SimdScalar restitutionCurve(SimdScalar rel_vel, SimdScalar restitution)
{
	return 0.f;
//	return restitution * GEN_min(1.0f, rel_vel / ContactThreshold);
}


SimdScalar	calculateCombinedFriction(RigidBody& body0,RigidBody& body1)
{
	SimdScalar friction = body0.getFriction() * body1.getFriction();
	if (friction < 0.f)
		friction = 0.f;
	if (friction > MAX_FRICTION)
		friction = MAX_FRICTION;
	return friction;

}


//bilateral constraint between two dynamic objects
void resolveSingleBilateral(RigidBody& body1, const SimdVector3& pos1,
                      RigidBody& body2, const SimdVector3& pos2,
                      SimdScalar distance, const SimdVector3& normal,SimdScalar& impulse ,float timeStep)
{
	float normalLenSqr = normal.length2();
	ASSERT2(fabs(normalLenSqr) < 1.1f);
	if (normalLenSqr > 1.1f)
	{
		impulse = 0.f;
		return;
	}
	SimdVector3 rel_pos1 = pos1 - body1.getCenterOfMassPosition(); 
	SimdVector3 rel_pos2 = pos2 - body2.getCenterOfMassPosition();
	//this jacobian entry could be re-used for all iterations
	
	SimdVector3 vel1 = body1.getVelocityInLocalPoint(rel_pos1);
	SimdVector3 vel2 = body2.getVelocityInLocalPoint(rel_pos2);
	SimdVector3 vel = vel1 - vel2;
	

	  JacobianEntry jac(body1.getCenterOfMassTransform().getBasis().transpose(),
		body2.getCenterOfMassTransform().getBasis().transpose(),
		rel_pos1,rel_pos2,normal,body1.getInvInertiaDiagLocal(),body1.getInvMass(),
		body2.getInvInertiaDiagLocal(),body2.getInvMass());

	SimdScalar jacDiagAB = jac.getDiagonal();
	SimdScalar jacDiagABInv = 1.f / jacDiagAB;
	
	  SimdScalar rel_vel = jac.getRelativeVelocity(
		body1.getLinearVelocity(),
		body1.getCenterOfMassTransform().getBasis().transpose() * body1.getAngularVelocity(),
		body2.getLinearVelocity(),
		body2.getCenterOfMassTransform().getBasis().transpose() * body2.getAngularVelocity()); 
	float a;
	a=jacDiagABInv;


	rel_vel = normal.dot(vel);
		

#ifdef ONLY_USE_LINEAR_MASS
	SimdScalar massTerm = 1.f / (body1.getInvMass() + body2.getInvMass());
	impulse = - contactDamping * rel_vel * massTerm;
#else	
	SimdScalar velocityImpulse = -contactDamping * rel_vel * jacDiagABInv;
	impulse = velocityImpulse;
#endif
}




//velocity + friction
//response  between two dynamic objects with friction
float resolveSingleCollisionWithFriction(

		RigidBody& body1, 
		const SimdVector3& pos1,
        RigidBody& body2, 
		const SimdVector3& pos2,
        SimdScalar distance, 
		const SimdVector3& normal, 

		const ContactSolverInfo& solverInfo
		)
{
	float normalLenSqr = normal.length2();
	ASSERT2(fabs(normalLenSqr) < 1.1f);
	if (normalLenSqr > 1.1f)
		return 0.f;

	SimdVector3 rel_pos1 = pos1 - body1.getCenterOfMassPosition(); 
	SimdVector3 rel_pos2 = pos2 - body2.getCenterOfMassPosition();
	//this jacobian entry could be re-used for all iterations
	
	JacobianEntry jac(body1.getCenterOfMassTransform().getBasis().transpose(),
		body2.getCenterOfMassTransform().getBasis().transpose(),
		rel_pos1,rel_pos2,normal,body1.getInvInertiaDiagLocal(),body1.getInvMass(),
		body2.getInvInertiaDiagLocal(),body2.getInvMass());

	SimdScalar jacDiagAB = jac.getDiagonal();
	SimdScalar jacDiagABInv = 1.f / jacDiagAB;
	SimdVector3 vel1 = body1.getVelocityInLocalPoint(rel_pos1);
	SimdVector3 vel2 = body2.getVelocityInLocalPoint(rel_pos2);
	SimdVector3 vel = vel1 - vel2;
SimdScalar rel_vel;
	/*	rel_vel = jac.getRelativeVelocity(
		body1.getLinearVelocity(),
		body1.getTransform().getBasis().transpose() * body1.getAngularVelocity(),
		body2.getLinearVelocity(),
		body2.getTransform().getBasis().transpose() * body2.getAngularVelocity()); 
*/	
	rel_vel = normal.dot(vel);
	
	float combinedRestitution = body1.getRestitution() * body2.getRestitution();

	SimdScalar restitution = restitutionCurve(rel_vel, combinedRestitution);

	SimdScalar Kfps = 1.f / solverInfo.m_timeStep ;

	float damping = solverInfo.m_damping ;
	float Kerp = solverInfo.m_tau;
	
	if (useGlobalSettingContacts)
	{
		damping = contactDamping;
		Kerp = contactTau;
	} 

	float Kcor = Kerp *Kfps;


	SimdScalar positionalError = Kcor *-distance;
	//jacDiagABInv;
	SimdScalar velocityError = -(1.0f + restitution) * damping * rel_vel;

	SimdScalar penetrationImpulse = positionalError * jacDiagABInv;

	SimdScalar	velocityImpulse = velocityError * jacDiagABInv;

	SimdScalar friction_impulse = 0.f;

	SimdScalar totalimpulse = penetrationImpulse+velocityImpulse;

	if (totalimpulse > 0.f)
	{
//		SimdVector3 impulse_vector = normal * impulse;
		body1.applyImpulse(normal*(velocityImpulse+penetrationImpulse), rel_pos1);
		
		body2.applyImpulse(-normal*(velocityImpulse+penetrationImpulse), rel_pos2);
		
		//friction

		{
		
		SimdVector3 vel1 = body1.getVelocityInLocalPoint(rel_pos1);
		SimdVector3 vel2 = body2.getVelocityInLocalPoint(rel_pos2);
		SimdVector3 vel = vel1 - vel2;
		
		rel_vel = normal.dot(vel);

#define PER_CONTACT_FRICTION
#ifdef PER_CONTACT_FRICTION
		SimdVector3 lat_vel = vel - normal * rel_vel;
		SimdScalar lat_rel_vel = lat_vel.length();

		float combinedFriction = calculateCombinedFriction(body1,body2);

		if (lat_rel_vel > SIMD_EPSILON)
		{
			lat_vel /= lat_rel_vel;
			SimdVector3 temp1 = body1.getInvInertiaTensorWorld() * rel_pos1.cross(lat_vel); 
			SimdVector3 temp2 = body2.getInvInertiaTensorWorld() * rel_pos2.cross(lat_vel); 
			 friction_impulse = lat_rel_vel / 
				(body1.getInvMass() + body2.getInvMass() + lat_vel.dot(temp1.cross(rel_pos1) + temp2.cross(rel_pos2)));
			SimdScalar normal_impulse = (penetrationImpulse+
				velocityImpulse) * combinedFriction;
			GEN_set_min(friction_impulse, normal_impulse);
			
			body1.applyImpulse(lat_vel * -friction_impulse, rel_pos1);
			body2.applyImpulse(lat_vel * friction_impulse, rel_pos2);
			
		}
#endif
		}
	} 
	return velocityImpulse + friction_impulse;
}
