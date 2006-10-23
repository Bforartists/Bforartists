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




#ifndef GJK_PAIR_DETECTOR_H
#define GJK_PAIR_DETECTOR_H

#include "btDiscreteCollisionDetectorInterface.h"
#include "LinearMath/btPoint3.h"

#include <BulletCollision/CollisionShapes/btCollisionMargin.h>

class btConvexShape;
#include "btSimplexSolverInterface.h"
class btConvexPenetrationDepthSolver;

/// btGjkPairDetector uses GJK to implement the btDiscreteCollisionDetectorInterface
class btGjkPairDetector : public btDiscreteCollisionDetectorInterface
{
	

	btVector3	m_cachedSeparatingAxis;
	btConvexPenetrationDepthSolver*	m_penetrationDepthSolver;
	btSimplexSolverInterface* m_simplexSolver;
	btConvexShape* m_minkowskiA;
	btConvexShape* m_minkowskiB;
	bool		m_ignoreMargin;
	

public:

	//experimental feature information, per triangle, per convex etc.
	//'material combiner' / contact added callback
	int	m_partId0;
	int	m_index0;
	int	m_partId1;
	int	m_index1;

	btGjkPairDetector(btConvexShape* objectA,btConvexShape* objectB,btSimplexSolverInterface* simplexSolver,btConvexPenetrationDepthSolver*	penetrationDepthSolver);
	virtual ~btGjkPairDetector() {};

	virtual void	getClosestPoints(const ClosestPointInput& input,Result& output,class btIDebugDraw* debugDraw);

	void setMinkowskiA(btConvexShape* minkA)
	{
		m_minkowskiA = minkA;
	}

	void setMinkowskiB(btConvexShape* minkB)
	{
		m_minkowskiB = minkB;
	}
	void setCachedSeperatingAxis(const btVector3& seperatingAxis)
	{
		m_cachedSeparatingAxis = seperatingAxis;
	}

	void	setPenetrationDepthSolver(btConvexPenetrationDepthSolver*	penetrationDepthSolver)
	{
		m_penetrationDepthSolver = penetrationDepthSolver;
	}

	void	setIgnoreMargin(bool ignoreMargin)
	{
		m_ignoreMargin = ignoreMargin;
	}

};

#endif //GJK_PAIR_DETECTOR_H
