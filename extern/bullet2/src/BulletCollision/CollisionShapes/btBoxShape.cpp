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

#include "btBoxShape.h"


//{ 


void btBoxShape::getAabb(const btTransform& t,btVector3& aabbMin,btVector3& aabbMax) const
{
	const btVector3& halfExtents = getHalfExtentsWithoutMargin();

	btMatrix3x3 abs_b = t.getBasis().absolute();  
	btPoint3 center = t.getOrigin();
	btVector3 extent = btVector3(abs_b[0].dot(halfExtents),
		   abs_b[1].dot(halfExtents),
		  abs_b[2].dot(halfExtents));
	extent += btVector3(getMargin(),getMargin(),getMargin());

	aabbMin = center - extent;
	aabbMax = center + extent;


}


void	btBoxShape::calculateLocalInertia(btScalar mass,btVector3& inertia) const
{
	//btScalar margin = btScalar(0.);
	btVector3 halfExtents = getHalfExtentsWithMargin();

	btScalar lx=btScalar(2.)*(halfExtents.x());
	btScalar ly=btScalar(2.)*(halfExtents.y());
	btScalar lz=btScalar(2.)*(halfExtents.z());

	inertia.setValue(mass/(btScalar(12.0)) * (ly*ly + lz*lz),
					mass/(btScalar(12.0)) * (lx*lx + lz*lz),
					mass/(btScalar(12.0)) * (lx*lx + ly*ly));

}

