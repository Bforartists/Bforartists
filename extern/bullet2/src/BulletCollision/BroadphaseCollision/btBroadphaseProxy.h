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

#ifndef BROADPHASE_PROXY_H
#define BROADPHASE_PROXY_H

#include "LinearMath/btScalar.h" //for SIMD_FORCE_INLINE
#include "LinearMath/btAlignedAllocator.h"


/// btDispatcher uses these types
/// IMPORTANT NOTE:The types are ordered polyhedral, implicit convex and concave
/// to facilitate type checking
enum BroadphaseNativeTypes
{
// polyhedral convex shapes
	BOX_SHAPE_PROXYTYPE,
	TRIANGLE_SHAPE_PROXYTYPE,
	TETRAHEDRAL_SHAPE_PROXYTYPE,
	CONVEX_TRIANGLEMESH_SHAPE_PROXYTYPE,
	CONVEX_HULL_SHAPE_PROXYTYPE,
//implicit convex shapes
IMPLICIT_CONVEX_SHAPES_START_HERE,
	SPHERE_SHAPE_PROXYTYPE,
	MULTI_SPHERE_SHAPE_PROXYTYPE,
	CAPSULE_SHAPE_PROXYTYPE,
	CONE_SHAPE_PROXYTYPE,
	CONVEX_SHAPE_PROXYTYPE,
	CYLINDER_SHAPE_PROXYTYPE,
	UNIFORM_SCALING_SHAPE_PROXYTYPE,
	MINKOWSKI_SUM_SHAPE_PROXYTYPE,
	MINKOWSKI_DIFFERENCE_SHAPE_PROXYTYPE,
//concave shapes
CONCAVE_SHAPES_START_HERE,
	//keep all the convex shapetype below here, for the check IsConvexShape in broadphase proxy!
	TRIANGLE_MESH_SHAPE_PROXYTYPE,
	///used for demo integration FAST/Swift collision library and Bullet
	FAST_CONCAVE_MESH_PROXYTYPE,
	//terrain
	TERRAIN_SHAPE_PROXYTYPE,
///Used for GIMPACT Trimesh integration
	GIMPACT_SHAPE_PROXYTYPE,
	
	EMPTY_SHAPE_PROXYTYPE,
	STATIC_PLANE_PROXYTYPE,
CONCAVE_SHAPES_END_HERE,

	COMPOUND_SHAPE_PROXYTYPE,

	MAX_BROADPHASE_COLLISION_TYPES
};


///btBroadphaseProxy
ATTRIBUTE_ALIGNED16(struct) btBroadphaseProxy
{

BT_DECLARE_ALIGNED_ALLOCATOR();
	
	///optional filtering to cull potential collisions
	enum CollisionFilterGroups
	{
	        DefaultFilter = 1,
	        StaticFilter = 2,
	        KinematicFilter = 4,
	        DebrisFilter = 8,
			SensorTrigger = 16,
	        AllFilter = DefaultFilter | StaticFilter | KinematicFilter | DebrisFilter | SensorTrigger
	};

	//Usually the client btCollisionObject or Rigidbody class
	void*	m_clientObject;

	///in the case of btMultiSapBroadphase, we store the collifionFilterGroup/Mask in the m_multiSapParentProxy
	union
	{
		struct
		{
			short int m_collisionFilterGroup;
			short int m_collisionFilterMask;
		};

		void*	m_multiSapParentProxy;

	};

	int			m_uniqueId;//m_uniqueId is introduced for paircache. could get rid of this, by calculating the address offset etc.
	int m_unusedPadding; //making the structure 16 bytes, better for alignment etc.

	SIMD_FORCE_INLINE int getUid()
	{
		return m_uniqueId;//(int)this;
	}

	//used for memory pools
	btBroadphaseProxy() :m_clientObject(0){}

	btBroadphaseProxy(void* userPtr,short int collisionFilterGroup, short int collisionFilterMask)
		:m_clientObject(userPtr),
		m_collisionFilterGroup(collisionFilterGroup),
		m_collisionFilterMask(collisionFilterMask)
	{
	}

	

	static SIMD_FORCE_INLINE bool isPolyhedral(int proxyType)
	{
		return (proxyType  < IMPLICIT_CONVEX_SHAPES_START_HERE);
	}

	static SIMD_FORCE_INLINE bool	isConvex(int proxyType)
	{
		return (proxyType < CONCAVE_SHAPES_START_HERE);
	}

	static SIMD_FORCE_INLINE bool	isConcave(int proxyType)
	{
		return ((proxyType > CONCAVE_SHAPES_START_HERE) &&
			(proxyType < CONCAVE_SHAPES_END_HERE));
	}
	static SIMD_FORCE_INLINE bool	isCompound(int proxyType)
	{
		return (proxyType == COMPOUND_SHAPE_PROXYTYPE);
	}
	static SIMD_FORCE_INLINE bool isInfinite(int proxyType)
	{
		return (proxyType == STATIC_PLANE_PROXYTYPE);
	}
	
}
;

class btCollisionAlgorithm;

struct btBroadphaseProxy;



/// contains a pair of aabb-overlapping objects
ATTRIBUTE_ALIGNED16(struct) btBroadphasePair
{
	btBroadphasePair ()
		:
	m_pProxy0(0),
		m_pProxy1(0),
		m_algorithm(0),
		m_userInfo(0)
	{
	}

BT_DECLARE_ALIGNED_ALLOCATOR();

	btBroadphasePair(const btBroadphasePair& other)
		:		m_pProxy0(other.m_pProxy0),
				m_pProxy1(other.m_pProxy1),
				m_algorithm(other.m_algorithm),
				m_userInfo(other.m_userInfo)
	{
	}
	btBroadphasePair(btBroadphaseProxy& proxy0,btBroadphaseProxy& proxy1)
	{

		//keep them sorted, so the std::set operations work
		if (&proxy0 < &proxy1)
        { 
            m_pProxy0 = &proxy0; 
            m_pProxy1 = &proxy1; 
        }
        else 
        { 
			m_pProxy0 = &proxy1; 
            m_pProxy1 = &proxy0; 
        }

		m_algorithm = 0;
		m_userInfo = 0;

	}
	
	btBroadphaseProxy* m_pProxy0;
	btBroadphaseProxy* m_pProxy1;
	
	mutable btCollisionAlgorithm* m_algorithm;
	mutable void* m_userInfo;

};

/*
//comparison for set operation, see Solid DT_Encounter
SIMD_FORCE_INLINE bool operator<(const btBroadphasePair& a, const btBroadphasePair& b) 
{ 
    return a.m_pProxy0 < b.m_pProxy0 || 
        (a.m_pProxy0 == b.m_pProxy0 && a.m_pProxy1 < b.m_pProxy1); 
}
*/



class btBroadphasePairSortPredicate
{
	public:

		bool operator() ( const btBroadphasePair& a, const btBroadphasePair& b )
		{
			 return a.m_pProxy0 > b.m_pProxy0 || 
				(a.m_pProxy0 == b.m_pProxy0 && a.m_pProxy1 > b.m_pProxy1) ||
				(a.m_pProxy0 == b.m_pProxy0 && a.m_pProxy1 == b.m_pProxy1 && a.m_algorithm > b.m_algorithm); 
		}
};


SIMD_FORCE_INLINE bool operator==(const btBroadphasePair& a, const btBroadphasePair& b) 
{
	 return (a.m_pProxy0 == b.m_pProxy0) && (a.m_pProxy1 == b.m_pProxy1);
}


#endif //BROADPHASE_PROXY_H

