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

#ifndef COLLISION_ALGORITHM_H
#define COLLISION_ALGORITHM_H

struct btBroadphaseProxy;
class btDispatcher;
class btManifoldResult;
struct btCollisionObject;
struct btDispatcherInfo;
class	btPersistentManifold;


struct btCollisionAlgorithmConstructionInfo
{
	btCollisionAlgorithmConstructionInfo()
		:m_dispatcher(0),
		m_manifold(0)
	{
	}
	btCollisionAlgorithmConstructionInfo(btDispatcher* dispatcher,int temp)
		:m_dispatcher(dispatcher)
	{
	}

	btDispatcher*	m_dispatcher;
	btPersistentManifold*	m_manifold;

	int	getDispatcherId();

};


///btCollisionAlgorithm is an collision interface that is compatible with the Broadphase and btDispatcher.
///It is persistent over frames
class btCollisionAlgorithm
{

protected:

	btDispatcher*	m_dispatcher;

protected:
	int	getDispatcherId();
	
public:

	btCollisionAlgorithm() {};

	btCollisionAlgorithm(const btCollisionAlgorithmConstructionInfo& ci);

	virtual ~btCollisionAlgorithm() {};

	virtual void processCollision (btCollisionObject* body0,btCollisionObject* body1,const btDispatcherInfo& dispatchInfo,btManifoldResult* resultOut) = 0;

	virtual float calculateTimeOfImpact(btCollisionObject* body0,btCollisionObject* body1,const btDispatcherInfo& dispatchInfo,btManifoldResult* resultOut) = 0;

};


#endif //COLLISION_ALGORITHM_H
