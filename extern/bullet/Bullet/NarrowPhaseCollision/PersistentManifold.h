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

#ifndef PERSISTENT_MANIFOLD_H
#define PERSISTENT_MANIFOLD_H


#include "SimdVector3.h"
#include "SimdTransform.h"
#include "ManifoldPoint.h"

struct CollisionResult;

///contact breaking and merging treshold
extern float gContactBreakingTreshold;

#define MANIFOLD_CACHE_SIZE 4

///PersistentManifold maintains contact points, and reduces them to 4
class PersistentManifold 
{

	ManifoldPoint m_pointCache[MANIFOLD_CACHE_SIZE];

	/// this two body pointers can point to the physics rigidbody class.
	/// void* will allow any rigidbody class
	void* m_body0;
	void* m_body1;
	int	m_cachedPoints;

	
	/// sort cached points so most isolated points come first
	int	SortCachedPoints(const ManifoldPoint& pt);

	int		FindContactPoint(const ManifoldPoint* unUsed, int numUnused,const ManifoldPoint& pt);

public:

	int m_index1;

	PersistentManifold();

	PersistentManifold(void* body0,void* body1)
		: m_body0(body0),m_body1(body1),m_cachedPoints(0)
	{
	}

	inline void* GetBody0() { return m_body0;}
	inline void* GetBody1() { return m_body1;}

	inline const void* GetBody0() const { return m_body0;}
	inline const void* GetBody1() const { return m_body1;}

	void	SetBodies(void* body0,void* body1)
	{
		m_body0 = body0;
		m_body1 = body1;
	}

	

	inline int	GetNumContacts() const { return m_cachedPoints;}

	inline const ManifoldPoint& GetContactPoint(int index) const
	{
		ASSERT(index < m_cachedPoints);
		return m_pointCache[index];
	}

	inline ManifoldPoint& GetContactPoint(int index)
	{
		ASSERT(index < m_cachedPoints);
		return m_pointCache[index];
	}

	/// todo: get this margin from the current physics / collision environment
	float	GetManifoldMargin() const;
	
	int GetCacheEntry(const ManifoldPoint& newPoint) const;

	void AddManifoldPoint( const ManifoldPoint& newPoint);

	void RemoveContactPoint (int index)
	{
		m_pointCache[index] = m_pointCache[GetNumContacts() - 1];
		m_cachedPoints--;
	}
	void ReplaceContactPoint(const ManifoldPoint& newPoint,int insertIndex)
	{
		assert(ValidContactDistance(newPoint));
		m_pointCache[insertIndex] = newPoint;
	}

	bool ValidContactDistance(const ManifoldPoint& pt) const
	{
		return pt.m_distance1 < GetManifoldMargin();
	}
	/// calculated new worldspace coordinates and depth, and reject points that exceed the collision margin
	void	RefreshContactPoints(  const SimdTransform& trA,const SimdTransform& trB);

	void	ClearManifold();

	float	GetCollisionImpulse() const;


};



#endif //PERSISTENT_MANIFOLD_H
