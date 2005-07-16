#ifndef TOI_CONTACT_DISPATCHER_H
#define TOI_CONTACT_DISPATCHER_H

#include "BroadphaseCollision/CollisionDispatcher.h"
#include "NarrowPhaseCollision/PersistentManifold.h"
#include "CollisionDispatch/UnionFind.h"
#include "BroadphaseCollision/BroadphaseProxy.h"

class ConstraintSolver;

//island management
#define ACTIVE_TAG 1
#define ISLAND_SLEEPING 2
#define WANTS_DEACTIVATION 3

#define MAX_MANIFOLDS 512

struct CollisionAlgorithmCreateFunc
{
	bool m_swapped;
	
	CollisionAlgorithmCreateFunc()
		:m_swapped(false)
	{
	}
	virtual	CollisionAlgorithm* CreateCollisionAlgorithm(BroadphaseProxy& proxy0,BroadphaseProxy& proxy1)
	{
		return 0;
	}
};
#include <vector>
///ToiContactDispatcher (Time of Impact) is the main collision dispatcher.
///Basic implementation supports algorithms that handle ConvexConvex and ConvexConcave collision pairs.
///Time of Impact, Closest Points and Penetration Depth.
class ToiContactDispatcher : public Dispatcher
{
	
	bool m_useIslands;

	
	std::vector<PersistentManifold*>	m_manifoldsPtr;

//	PersistentManifold	m_manifolds[MAX_MANIFOLDS];
//	int	m_freeManifolds[MAX_MANIFOLDS];

	UnionFind m_unionFind;
	ConstraintSolver*	m_solver;
	
	CollisionAlgorithmCreateFunc* m_doubleDispatch[MAX_BROADPHASE_COLLISION_TYPES][MAX_BROADPHASE_COLLISION_TYPES];
	
public:
	
	UnionFind& GetUnionFind() { return m_unionFind;}

//	int	m_firstFreeManifold;
	
//	const PersistentManifold* GetManifoldByIndexInternal(int index)
//	{
//		return &m_manifolds[index];
//	}

	int	GetNumManifolds() { return m_manifoldsPtr.size();}

	 PersistentManifold* GetManifoldByIndexInternal(int index)
	{
	return m_manifoldsPtr[index];
	}


	void InitUnionFind()
	{
		if (m_useIslands)
			m_unionFind.reset();
	}
	
	void FindUnions();
	
	int m_count;
	
	ToiContactDispatcher (ConstraintSolver* solver);

	virtual PersistentManifold*	GetNewManifold(void* b0,void* b1);
	
	virtual void ReleaseManifold(PersistentManifold* manifold);

	//
	// todo: this is random access, it can be walked 'cache friendly'!
	//
	virtual void SolveConstraints(float timeStep, int numIterations,int numRigidBodies);
	
	
	CollisionAlgorithm* FindAlgorithm(BroadphaseProxy& proxy0,BroadphaseProxy& proxy1)
	{
		CollisionAlgorithm* algo = InternalFindAlgorithm(proxy0,proxy1);
		return algo;
	}
	
	CollisionAlgorithm* InternalFindAlgorithm(BroadphaseProxy& proxy0,BroadphaseProxy& proxy1);
	
	virtual int GetUniqueId() { return RIGIDBODY_DISPATCHER;}
	
};

#endif //TOI_CONTACT_DISPATCHER_H

