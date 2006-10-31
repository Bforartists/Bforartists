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

#include "btConvexConvexAlgorithm.h"

#include <stdio.h>
#include "BulletCollision/NarrowPhaseCollision/btDiscreteCollisionDetectorInterface.h"
#include "BulletCollision/BroadphaseCollision/btBroadphaseInterface.h"
#include "BulletCollision/CollisionDispatch/btCollisionObject.h"
#include "BulletCollision/CollisionShapes/btConvexShape.h"
#include "BulletCollision/NarrowPhaseCollision/btGjkPairDetector.h"
#include "BulletCollision/BroadphaseCollision/btBroadphaseProxy.h"
#include "BulletCollision/CollisionDispatch/btCollisionDispatcher.h"
#include "BulletCollision/CollisionShapes/btBoxShape.h"
#include "BulletCollision/CollisionDispatch/btManifoldResult.h"

#include "BulletCollision/NarrowPhaseCollision/btConvexPenetrationDepthSolver.h"
#include "BulletCollision/NarrowPhaseCollision/btContinuousConvexCollision.h"
#include "BulletCollision/NarrowPhaseCollision/btSubSimplexConvexCast.h"
#include "BulletCollision/NarrowPhaseCollision/btGjkConvexCast.h"



#include "BulletCollision/CollisionShapes/btMinkowskiSumShape.h"
#include "BulletCollision/NarrowPhaseCollision/btVoronoiSimplexSolver.h"
#include "BulletCollision/CollisionShapes/btSphereShape.h"

#include "BulletCollision/NarrowPhaseCollision/btMinkowskiPenetrationDepthSolver.h"

//#include "NarrowPhaseCollision/EpaPenetrationDepthSolver.h"

#ifdef WIN32
#if _MSC_VER >= 1310
//only use SIMD Hull code under Win32
#ifdef TEST_HULL
#define USE_HULL 1
#endif //TEST_HULL
#endif //_MSC_VER 
#endif //WIN32


#ifdef USE_HULL

#include "NarrowPhaseCollision/Hull.h"
#include "NarrowPhaseCollision/HullContactCollector.h"


#endif //USE_HULL

bool gUseEpa = false;


#ifdef WIN32
void DrawRasterizerLine(const float* from,const float* to,int color);
#endif




//#define PROCESS_SINGLE_CONTACT
#ifdef WIN32
bool gForceBoxBox = false;//false;//true;

#else
bool gForceBoxBox = false;//false;//true;
#endif
bool gBoxBoxUseGjk = true;//true;//false;
bool gDisableConvexCollision = false;



btConvexConvexAlgorithm::btConvexConvexAlgorithm(btPersistentManifold* mf,const btCollisionAlgorithmConstructionInfo& ci,btCollisionObject* body0,btCollisionObject* body1)
: btCollisionAlgorithm(ci),
m_gjkPairDetector(0,0,&m_simplexSolver,0),
m_useEpa(!gUseEpa),
m_ownManifold (false),
m_manifoldPtr(mf),
m_lowLevelOfDetail(false)
{
	checkPenetrationDepthSolver();

}




btConvexConvexAlgorithm::~btConvexConvexAlgorithm()
{
	if (m_ownManifold)
	{
		if (m_manifoldPtr)
			m_dispatcher->releaseManifold(m_manifoldPtr);
	}
}

void	btConvexConvexAlgorithm ::setLowLevelOfDetail(bool useLowLevel)
{
	m_lowLevelOfDetail = useLowLevel;
}




static btMinkowskiPenetrationDepthSolver	gPenetrationDepthSolver;

//static EpaPenetrationDepthSolver	gEpaPenetrationDepthSolver;

#ifdef USE_EPA
Solid3EpaPenetrationDepth	gSolidEpaPenetrationSolver;
#endif //USE_EPA

void	btConvexConvexAlgorithm::checkPenetrationDepthSolver()
{
	if (m_useEpa != gUseEpa)
	{
		m_useEpa  = gUseEpa;
		if (m_useEpa)
		{
			
		//	m_gjkPairDetector.setPenetrationDepthSolver(&gEpaPenetrationDepthSolver);
						
			
		} else
		{
			m_gjkPairDetector.setPenetrationDepthSolver(&gPenetrationDepthSolver);
		}
	}
	
}


//
// Convex-Convex collision algorithm
//
void btConvexConvexAlgorithm ::processCollision (btCollisionObject* body0,btCollisionObject* body1,const btDispatcherInfo& dispatchInfo,btManifoldResult* resultOut)
{

	if (!m_manifoldPtr)
	{
		//swapped?
		m_manifoldPtr = m_dispatcher->getNewManifold(body0,body1);
		m_ownManifold = true;
	}


	checkPenetrationDepthSolver();

	btConvexShape* min0 = static_cast<btConvexShape*>(body0->m_collisionShape);
	btConvexShape* min1 = static_cast<btConvexShape*>(body1->m_collisionShape);
	
	btGjkPairDetector::ClosestPointInput input;

	//TODO: if (dispatchInfo.m_useContinuous)
	m_gjkPairDetector.setMinkowskiA(min0);
	m_gjkPairDetector.setMinkowskiB(min1);
	input.m_maximumDistanceSquared = min0->getMargin() + min1->getMargin() + m_manifoldPtr->getContactBreakingThreshold();
	input.m_maximumDistanceSquared*= input.m_maximumDistanceSquared;
	
//	input.m_maximumDistanceSquared = 1e30f;
	
	input.m_transformA = body0->m_worldTransform;
	input.m_transformB = body1->m_worldTransform;
	
	resultOut->setPersistentManifold(m_manifoldPtr);
	m_gjkPairDetector.getClosestPoints(input,*resultOut,dispatchInfo.m_debugDraw);

}



bool disableCcd = false;
float	btConvexConvexAlgorithm::calculateTimeOfImpact(btCollisionObject* col0,btCollisionObject* col1,const btDispatcherInfo& dispatchInfo,btManifoldResult* resultOut)
{
	///Rather then checking ALL pairs, only calculate TOI when motion exceeds threshold
    
	///Linear motion for one of objects needs to exceed m_ccdSquareMotionThreshold
	///col0->m_worldTransform,
	float resultFraction = 1.f;


	float squareMot0 = (col0->m_interpolationWorldTransform.getOrigin() - col0->m_worldTransform.getOrigin()).length2();
    
	if (squareMot0 < col0->m_ccdSquareMotionThreshold &&
		squareMot0 < col0->m_ccdSquareMotionThreshold)
		return resultFraction;



	if (disableCcd)
		return 1.f;

	checkPenetrationDepthSolver();

	//An adhoc way of testing the Continuous Collision Detection algorithms
	//One object is approximated as a sphere, to simplify things
	//Starting in penetration should report no time of impact
	//For proper CCD, better accuracy and handling of 'allowed' penetration should be added
	//also the mainloop of the physics should have a kind of toi queue (something like Brian Mirtich's application of Timewarp for Rigidbodies)

		
	/// Convex0 against sphere for Convex1
	{
		btConvexShape* convex0 = static_cast<btConvexShape*>(col0->m_collisionShape);

		btSphereShape	sphere1(col1->m_ccdSweptSphereRadius); //todo: allow non-zero sphere sizes, for better approximation
		btConvexCast::CastResult result;
		btVoronoiSimplexSolver voronoiSimplex;
		//SubsimplexConvexCast ccd0(&sphere,min0,&voronoiSimplex);
		///Simplification, one object is simplified as a sphere
		btGjkConvexCast ccd1( convex0 ,&sphere1,&voronoiSimplex);
		//ContinuousConvexCollision ccd(min0,min1,&voronoiSimplex,0);
		if (ccd1.calcTimeOfImpact(col0->m_worldTransform,col0->m_interpolationWorldTransform,
			col1->m_worldTransform,col1->m_interpolationWorldTransform,result))
		{
		
			//store result.m_fraction in both bodies
		
			if (col0->m_hitFraction	> result.m_fraction)
				col0->m_hitFraction  = result.m_fraction;

			if (col1->m_hitFraction > result.m_fraction)
				col1->m_hitFraction  = result.m_fraction;

			if (resultFraction > result.m_fraction)
				resultFraction = result.m_fraction;

		}
		
		


	}

	/// Sphere (for convex0) against Convex1
	{
		btConvexShape* convex1 = static_cast<btConvexShape*>(col1->m_collisionShape);

		btSphereShape	sphere0(col0->m_ccdSweptSphereRadius); //todo: allow non-zero sphere sizes, for better approximation
		btConvexCast::CastResult result;
		btVoronoiSimplexSolver voronoiSimplex;
		//SubsimplexConvexCast ccd0(&sphere,min0,&voronoiSimplex);
		///Simplification, one object is simplified as a sphere
		btGjkConvexCast ccd1(&sphere0,convex1,&voronoiSimplex);
		//ContinuousConvexCollision ccd(min0,min1,&voronoiSimplex,0);
		if (ccd1.calcTimeOfImpact(col0->m_worldTransform,col0->m_interpolationWorldTransform,
			col1->m_worldTransform,col1->m_interpolationWorldTransform,result))
		{
		
			//store result.m_fraction in both bodies
		
			if (col0->m_hitFraction	> result.m_fraction)
				col0->m_hitFraction  = result.m_fraction;

			if (col1->m_hitFraction > result.m_fraction)
				col1->m_hitFraction  = result.m_fraction;

			if (resultFraction > result.m_fraction)
				resultFraction = result.m_fraction;

		}
	}
	
	return resultFraction;

}
