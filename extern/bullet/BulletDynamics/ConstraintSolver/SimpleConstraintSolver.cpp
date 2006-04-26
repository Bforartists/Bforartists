/*
Bullet Continuous Collision Detection and Physics Library
Copyright (c) 2003-2006 Erwin Coumans  http://continuousphysics.com/Bullet/

This software is provided 'as-is', without any express or implied warranty.
In no event will the authors be held liable for any damages arising from the use of this software.
Permission is granted to anyone to use this software for any purpose, 
including commercial applications, and to alter it and redistribute it freely, 
subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not claim that you wrote the original software. If you use this software in a product, an acknowledgment in the product documentation would be appreciated but is not required.
2. Altered source versions must be plainly marked as such, and must not be misrepresented as being the original software.
3. This notice may not be removed or altered from any source distribution.
*/


#include "SimpleConstraintSolver.h"
#include "NarrowPhaseCollision/PersistentManifold.h"
#include "Dynamics/RigidBody.h"
#include "ContactConstraint.h"
#include "Solve2LinearConstraint.h"
#include "ContactSolverInfo.h"
#include "Dynamics/BU_Joint.h"
#include "Dynamics/ContactJoint.h"
#include "IDebugDraw.h"
#include "JacobianEntry.h"
#include "GEN_MinMax.h"

#ifdef USE_PROFILE
#include "quickprof.h"
#endif //USE_PROFILE

/// SimpleConstraintSolver Sequentially applies impulses
float SimpleConstraintSolver::SolveGroup(PersistentManifold** manifoldPtr, int numManifolds,const ContactSolverInfo& infoGlobal,IDebugDraw* debugDrawer)
{
	ContactSolverInfo info = infoGlobal;

	int numiter = infoGlobal.m_numIterations;
#ifdef USE_PROFILE
	Profiler::beginBlock("Solve");
#endif //USE_PROFILE

	//should traverse the contacts random order...
	int i;
	for ( i = 0;i<numiter;i++)
	{
		int j;
		for (j=0;j<numManifolds;j++)
		{
			int k=j;
			if (i&1)
				k=numManifolds-j-1;

			Solve(manifoldPtr[k],info,i,debugDrawer);
		}
		
	}
#ifdef USE_PROFILE
	Profiler::endBlock("Solve");

	Profiler::beginBlock("SolveFriction");
#endif //USE_PROFILE

	//now solve the friction		
	for (i = 0;i<numiter;i++)
	{
		int j;
	for (j=0;j<numManifolds;j++)
		{
			int k = j;
			if (i&1)
				k=numManifolds-j-1;
			SolveFriction(manifoldPtr[k],info,i,debugDrawer);
		}
	}
#ifdef USE_PROFILE
	Profiler::endBlock("SolveFriction");
#endif //USE_PROFILE

	return 0.f;
}


float penetrationResolveFactor = 0.9f;


float SimpleConstraintSolver::Solve(PersistentManifold* manifoldPtr, const ContactSolverInfo& info,int iter,IDebugDraw* debugDrawer)
{

	RigidBody* body0 = (RigidBody*)manifoldPtr->GetBody0();
	RigidBody* body1 = (RigidBody*)manifoldPtr->GetBody1();

	float maxImpulse = 0.f;

	//only necessary to refresh the manifold once (first iteration). The integration is done outside the loop
	if (iter == 0)
	{
		manifoldPtr->RefreshContactPoints(body0->getCenterOfMassTransform(),body1->getCenterOfMassTransform());
		
		const int numpoints = manifoldPtr->GetNumContacts();

		SimdVector3 color(0,1,0);
		for (int i=0;i<numpoints ;i++)
		{
			ManifoldPoint& cp = manifoldPtr->GetContactPoint(i);
			if (cp.GetDistance() <= 0.f)
			{
				const SimdVector3& pos1 = cp.GetPositionWorldOnA();
				const SimdVector3& pos2 = cp.GetPositionWorldOnB();

				SimdVector3 rel_pos1 = pos1 - body0->getCenterOfMassPosition(); 
				SimdVector3 rel_pos2 = pos2 - body1->getCenterOfMassPosition();
				
				//this jacobian entry is re-used for all iterations
				JacobianEntry jac(body0->getCenterOfMassTransform().getBasis().transpose(),
					body1->getCenterOfMassTransform().getBasis().transpose(),
					rel_pos1,rel_pos2,cp.m_normalWorldOnB,body0->getInvInertiaDiagLocal(),body0->getInvMass(),
					body1->getInvInertiaDiagLocal(),body1->getInvMass());

				SimdScalar jacDiagAB = jac.getDiagonal();
				
				cp.m_jacDiagABInv = 1.f / jacDiagAB;

				

				float relaxation = info.m_damping;
				cp.m_appliedImpulse *= relaxation;
				//for friction
				cp.m_prevAppliedImpulse = cp.m_appliedImpulse;
				
				//re-calculate friction direction every frame, todo: check if this is really needed
				SimdPlaneSpace1(cp.m_normalWorldOnB,cp.m_frictionWorldTangential0,cp.m_frictionWorldTangential1);
#define NO_FRICTION_WARMSTART 1

	#ifdef NO_FRICTION_WARMSTART
				cp.m_accumulatedTangentImpulse0 = 0.f;
				cp.m_accumulatedTangentImpulse1 = 0.f;
	#endif //NO_FRICTION_WARMSTART
				float denom0 = body0->ComputeImpulseDenominator(pos1,cp.m_frictionWorldTangential0);
				float denom1 = body1->ComputeImpulseDenominator(pos2,cp.m_frictionWorldTangential0);
				float denom = relaxation/(denom0+denom1);
				cp.m_jacDiagABInvTangent0 = denom;


				denom0 = body0->ComputeImpulseDenominator(pos1,cp.m_frictionWorldTangential1);
				denom1 = body1->ComputeImpulseDenominator(pos2,cp.m_frictionWorldTangential1);
				denom = relaxation/(denom0+denom1);
				cp.m_jacDiagABInvTangent1 = denom;

				SimdVector3 totalImpulse = 
	#ifndef NO_FRICTION_WARMSTART
					cp.m_frictionWorldTangential0*cp.m_accumulatedTangentImpulse0+
					cp.m_frictionWorldTangential1*cp.m_accumulatedTangentImpulse1+
	#endif //NO_FRICTION_WARMSTART
					cp.m_normalWorldOnB*cp.m_appliedImpulse;

				//apply previous frames impulse on both bodies
				body0->applyImpulse(totalImpulse, rel_pos1);
				body1->applyImpulse(-totalImpulse, rel_pos2);
			}
			
		}
	}

	{
		const int numpoints = manifoldPtr->GetNumContacts();

		SimdVector3 color(0,1,0);
		for (int i=0;i<numpoints ;i++)
		{

			int j=i;
			if (iter % 2)
				j = numpoints-1-i;
			else
				j=i;

			ManifoldPoint& cp = manifoldPtr->GetContactPoint(j);
				if (cp.GetDistance() <= 0.f)
			{

				if (iter == 0)
				{
					if (debugDrawer)
						debugDrawer->DrawContactPoint(cp.m_positionWorldOnB,cp.m_normalWorldOnB,cp.GetDistance(),cp.GetLifeTime(),color);
				}

				{


					//float dist =  cp.GetDistance();
					//printf("dist(%i)=%f\n",j,dist);
					float impulse = resolveSingleCollision(
						*body0,*body1,
						cp,
						info);
					
					if (maxImpulse < impulse)
						maxImpulse  = impulse;

				}
			}
		}
	}
	return maxImpulse;
}

float SimpleConstraintSolver::SolveFriction(PersistentManifold* manifoldPtr, const ContactSolverInfo& info,int iter,IDebugDraw* debugDrawer)
{
	RigidBody* body0 = (RigidBody*)manifoldPtr->GetBody0();
	RigidBody* body1 = (RigidBody*)manifoldPtr->GetBody1();


	{
		const int numpoints = manifoldPtr->GetNumContacts();

		SimdVector3 color(0,1,0);
		for (int i=0;i<numpoints ;i++)
		{

			int j=i;
			//if (iter % 2)
			//	j = numpoints-1-i;

			ManifoldPoint& cp = manifoldPtr->GetContactPoint(j);
				if (cp.GetDistance() <= 0.f)
			{

				resolveSingleFriction(
					*body0,*body1,
					cp,
					info);
				
			}
		}

	
	}
	return 0.f;
}
