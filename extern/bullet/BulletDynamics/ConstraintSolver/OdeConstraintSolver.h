/*
 * Copyright (c) 2005 Erwin Coumans http://www.erwincoumans.com
 *
 * Permission to use, copy, modify, distribute and sell this software
 * and its documentation for any purpose is hereby granted without fee,
 * provided that the above copyright notice appear in all copies.
 * Erwin Coumans makes no representations about the suitability 
 * of this software for any purpose.  
 * It is provided "as is" without express or implied warranty.
*/
#ifndef ODE_CONSTRAINT_SOLVER_H
#define ODE_CONSTRAINT_SOLVER_H

#include "ConstraintSolver.h"

class RigidBody;
class BU_Joint;

/// OdeConstraintSolver is one of the available solvers for Bullet dynamics framework
/// It uses the the unmodified version of quickstep solver from the open dynamics project
class OdeConstraintSolver : public ConstraintSolver
{
private:

	int m_CurBody;
	int m_CurJoint;


	int ConvertBody(RigidBody* body,RigidBody** bodies,int& numBodies);
	void ConvertConstraint(PersistentManifold* manifold,BU_Joint** joints,int& numJoints,
					   RigidBody** bodies,int _bodyId0,int _bodyId1,IDebugDraw* debugDrawer);

public:

	virtual ~OdeConstraintSolver() {}
	
	virtual float SolveGroup(PersistentManifold** manifold,int numManifolds,const ContactSolverInfo& info,IDebugDraw* debugDrawer = 0);

};




#endif //ODE_CONSTRAINT_SOLVER_H
