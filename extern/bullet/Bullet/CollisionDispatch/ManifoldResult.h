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

#ifndef MANIFOLD_RESULT_H
#define MANIFOLD_RESULT_H

#include "NarrowPhaseCollision/DiscreteCollisionDetectorInterface.h"
struct CollisionObject;
class PersistentManifold;


class ManifoldResult : public DiscreteCollisionDetectorInterface::Result
{
	PersistentManifold* m_manifoldPtr;
	CollisionObject* m_body0;
	CollisionObject* m_body1;

public:

	ManifoldResult(CollisionObject* body0,CollisionObject* body1,PersistentManifold* manifoldPtr);


	virtual void AddContactPoint(const SimdVector3& normalOnBInWorld,const SimdVector3& pointInWorld,float depth);

};

#endif //MANIFOLD_RESULT_H
