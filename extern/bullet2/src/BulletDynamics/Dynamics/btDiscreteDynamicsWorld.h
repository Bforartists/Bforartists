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

#ifndef BT_DISCRETE_DYNAMICS_WORLD_H
#define BT_DISCRETE_DYNAMICS_WORLD_H

#include "btDynamicsWorld.h"

class btDispatcher;
class btOverlappingPairCache;
class btConstraintSolver;
class btSimulationIslandManager;
class btTypedConstraint;
#include "BulletDynamics/ConstraintSolver/btContactSolverInfo.h"

class btRaycastVehicle;
class btIDebugDraw;
#include "LinearMath/btAlignedObjectArray.h"


///btDiscreteDynamicsWorld provides discrete rigid body simulation
///those classes replace the obsolete CcdPhysicsEnvironment/CcdPhysicsController
class btDiscreteDynamicsWorld : public btDynamicsWorld
{
protected:

	btConstraintSolver*	m_constraintSolver;

	btSimulationIslandManager*	m_islandManager;

	btAlignedObjectArray<btTypedConstraint*> m_constraints;

	btIDebugDraw*	m_debugDrawer;

	btVector3	m_gravity;

	//for variable timesteps
	btScalar	m_localTime;
	//for variable timesteps

	bool	m_ownsIslandManager;
	bool	m_ownsConstraintSolver;

	btContactSolverInfo	m_solverInfo;


	btAlignedObjectArray<btRaycastVehicle*>	m_vehicles;

	int	m_profileTimings;

	void	predictUnconstraintMotion(btScalar timeStep);
	
	void	integrateTransforms(btScalar timeStep);
		
	void	calculateSimulationIslands();

	void	solveConstraints(btContactSolverInfo& solverInfo);
	
	void	updateActivationState(btScalar timeStep);

	void	updateVehicles(btScalar timeStep);

	void	startProfiling(btScalar timeStep);

	virtual void	internalSingleStepSimulation( btScalar timeStep);

	void	synchronizeMotionStates();

	void	saveKinematicState(btScalar timeStep);

	void	debugDrawSphere(btScalar radius, const btTransform& transform, const btVector3& color);

public:


	///this btDiscreteDynamicsWorld constructor gets created objects from the user, and will not delete those
	btDiscreteDynamicsWorld(btDispatcher* dispatcher,btBroadphaseInterface* pairCache,btConstraintSolver* constraintSolver,btCollisionConfiguration* collisionConfiguration);

	virtual ~btDiscreteDynamicsWorld();

	///if maxSubSteps > 0, it will interpolate motion between fixedTimeStep's
	virtual int	stepSimulation( btScalar timeStep,int maxSubSteps=1, btScalar fixedTimeStep=btScalar(1.)/btScalar(60.));

	virtual void	updateAabbs();

	void	addConstraint(btTypedConstraint* constraint, bool disableCollisionsBetweenLinkedBodies=false);

	void	removeConstraint(btTypedConstraint* constraint);

	void	addVehicle(btRaycastVehicle* vehicle);

	void	removeVehicle(btRaycastVehicle* vehicle);

	btSimulationIslandManager*	getSimulationIslandManager()
	{
		return m_islandManager;
	}

	const btSimulationIslandManager*	getSimulationIslandManager() const 
	{
		return m_islandManager;
	}

	btCollisionWorld*	getCollisionWorld()
	{
		return this;
	}

	virtual void	setDebugDrawer(btIDebugDraw*	debugDrawer)
	{
			m_debugDrawer = debugDrawer;
	}

	virtual btIDebugDraw*	getDebugDrawer()
	{
		return m_debugDrawer;
	}

	virtual void	setGravity(const btVector3& gravity);

	virtual void	addRigidBody(btRigidBody* body);

	virtual void	addRigidBody(btRigidBody* body, short group, short mask);

	virtual void	removeRigidBody(btRigidBody* body);

	void	debugDrawObject(const btTransform& worldTransform, const btCollisionShape* shape, const btVector3& color);

	virtual void	setConstraintSolver(btConstraintSolver* solver);

	virtual btConstraintSolver* getConstraintSolver();
	
	virtual	int		getNumConstraints() const;

	virtual btTypedConstraint* getConstraint(int index)	;

	virtual const btTypedConstraint* getConstraint(int index) const;

	btContactSolverInfo& getSolverInfo()
	{
		return m_solverInfo;
	}

	virtual btDynamicsWorldType	getWorldType() const
	{
		return BT_DISCRETE_DYNAMICS_WORLD;
	}


};

#endif //BT_DISCRETE_DYNAMICS_WORLD_H
