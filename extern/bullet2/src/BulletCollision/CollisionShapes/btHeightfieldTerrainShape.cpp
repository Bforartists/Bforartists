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

#include "btHeightfieldTerrainShape.h"

#include "LinearMath/btTransformUtil.h"


btHeightfieldTerrainShape::btHeightfieldTerrainShape()
:m_localScaling(0.f,0.f,0.f)
{
}


btHeightfieldTerrainShape::~btHeightfieldTerrainShape()
{
}



void btHeightfieldTerrainShape::getAabb(const btTransform& t,btVector3& aabbMin,btVector3& aabbMax) const
{
	aabbMin.setValue(-1e30f,-1e30f,-1e30f);
	aabbMax.setValue(1e30f,1e30f,1e30f);

}




void	btHeightfieldTerrainShape::processAllTriangles(btTriangleCallback* callback,const btVector3& aabbMin,const btVector3& aabbMax) const
{

	btVector3 halfExtents = (aabbMax - aabbMin) * 0.5f;
	btScalar radius = halfExtents.length();
	btVector3 center = (aabbMax + aabbMin) * 0.5f;
	
	//TODO
	//this is where the triangles are generated, given AABB and plane equation (normal/constant)
/*
	btVector3 tangentDir0,tangentDir1;

	//tangentDir0/tangentDir1 can be precalculated
	btPlaneSpace1(m_planeNormal,tangentDir0,tangentDir1);

	btVector3 supVertex0,supVertex1;

	btVector3 projectedCenter = center - (m_planeNormal.dot(center) - m_planeConstant)*m_planeNormal;
	
	btVector3 triangle[3];
	triangle[0] = projectedCenter + tangentDir0*radius + tangentDir1*radius;
	triangle[1] = projectedCenter + tangentDir0*radius - tangentDir1*radius;
	triangle[2] = projectedCenter - tangentDir0*radius - tangentDir1*radius;

	callback->processTriangle(triangle,0,0);

	triangle[0] = projectedCenter - tangentDir0*radius - tangentDir1*radius;
	triangle[1] = projectedCenter - tangentDir0*radius + tangentDir1*radius;
	triangle[2] = projectedCenter + tangentDir0*radius + tangentDir1*radius;

	callback->processTriangle(triangle,0,1);
*/

}

void	btHeightfieldTerrainShape::calculateLocalInertia(btScalar mass,btVector3& inertia)
{
	//moving concave objects not supported
	
	inertia.setValue(0.f,0.f,0.f);
}

void	btHeightfieldTerrainShape::setLocalScaling(const btVector3& scaling)
{
	m_localScaling = scaling;
}
const btVector3& btHeightfieldTerrainShape::getLocalScaling() const
{
	return m_localScaling;
}
