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

#ifndef STATIC_PLANE_SHAPE_H
#define STATIC_PLANE_SHAPE_H

#include "BulletCollision/CollisionShapes/btConcaveShape.h"


///StaticPlaneShape simulates an 'infinite' plane by dynamically reporting triangles approximated by intersection of the plane with the AABB.
///Assumed is that the other objects is not also infinite, so a reasonable sized AABB.
class btStaticPlaneShape : public ConcaveShape
{
protected:
	btVector3	m_localAabbMin;
	btVector3	m_localAabbMax;
	
	btVector3	m_planeNormal;
	btScalar      m_planeConstant;
	btVector3	m_localScaling;

public:
	btStaticPlaneShape(const btVector3& planeNormal,btScalar planeConstant);

	virtual ~btStaticPlaneShape();


	virtual int	getShapeType() const
	{
		return STATIC_PLANE_PROXYTYPE;
	}

	virtual void getAabb(const btTransform& t,btVector3& aabbMin,btVector3& aabbMax) const;

	virtual void	processAllTriangles(btTriangleCallback* callback,const btVector3& aabbMin,const btVector3& aabbMax) const;

	virtual void	calculateLocalInertia(btScalar mass,btVector3& inertia);

	virtual void	setLocalScaling(const btVector3& scaling);
	virtual const btVector3& getLocalScaling() const;
	

	//debugging
	virtual char*	getName()const {return "STATICPLANE";}


};

#endif //STATIC_PLANE_SHAPE_H
