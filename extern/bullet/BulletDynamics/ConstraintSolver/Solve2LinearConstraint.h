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
#ifndef SOLVE_2LINEAR_CONSTRAINT_H
#define SOLVE_2LINEAR_CONSTRAINT_H

#include "SimdMatrix3x3.h"
#include "SimdVector3.h"


class RigidBody;



/// constraint class used for lateral tyre friction.
class	Solve2LinearConstraint
{
	SimdScalar	m_tau;
	SimdScalar	m_damping;

public:

	Solve2LinearConstraint(SimdScalar tau,SimdScalar damping)
	{
		m_tau = tau;
		m_damping = damping;
	}
	//
	// solve unilateral constraint (equality, direct method)
	//
	void resolveUnilateralPairConstraint(		
														   RigidBody* body0,
		RigidBody* body1,

		const SimdMatrix3x3& world2A,
						const SimdMatrix3x3& world2B,
						
						const SimdVector3& invInertiaADiag,
						const SimdScalar invMassA,
						const SimdVector3& linvelA,const SimdVector3& angvelA,
						const SimdVector3& rel_posA1,
						const SimdVector3& invInertiaBDiag,
						const SimdScalar invMassB,
						const SimdVector3& linvelB,const SimdVector3& angvelB,
						const SimdVector3& rel_posA2,

					  SimdScalar depthA, const SimdVector3& normalA, 
					  const SimdVector3& rel_posB1,const SimdVector3& rel_posB2,
					  SimdScalar depthB, const SimdVector3& normalB, 
					  SimdScalar& imp0,SimdScalar& imp1);


	//
	// solving 2x2 lcp problem (inequality, direct solution )
	//
	void resolveBilateralPairConstraint(
			RigidBody* body0,
						RigidBody* body1,
		const SimdMatrix3x3& world2A,
						const SimdMatrix3x3& world2B,
						
						const SimdVector3& invInertiaADiag,
						const SimdScalar invMassA,
						const SimdVector3& linvelA,const SimdVector3& angvelA,
						const SimdVector3& rel_posA1,
						const SimdVector3& invInertiaBDiag,
						const SimdScalar invMassB,
						const SimdVector3& linvelB,const SimdVector3& angvelB,
						const SimdVector3& rel_posA2,

					  SimdScalar depthA, const SimdVector3& normalA, 
					  const SimdVector3& rel_posB1,const SimdVector3& rel_posB2,
					  SimdScalar depthB, const SimdVector3& normalB, 
					  SimdScalar& imp0,SimdScalar& imp1);


	void resolveAngularConstraint(	const SimdMatrix3x3& invInertiaAWS,
						const SimdScalar invMassA,
						const SimdVector3& linvelA,const SimdVector3& angvelA,
						const SimdVector3& rel_posA1,
						const SimdMatrix3x3& invInertiaBWS,
						const SimdScalar invMassB,
						const SimdVector3& linvelB,const SimdVector3& angvelB,
						const SimdVector3& rel_posA2,

					  SimdScalar depthA, const SimdVector3& normalA, 
					  const SimdVector3& rel_posB1,const SimdVector3& rel_posB2,
					  SimdScalar depthB, const SimdVector3& normalB, 
					  SimdScalar& imp0,SimdScalar& imp1);


};

#endif //SOLVE_2LINEAR_CONSTRAINT_H
