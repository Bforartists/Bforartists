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

#ifndef CONCAVE_SHAPE_H
#define CONCAVE_SHAPE_H

#include "BulletCollision/CollisionShapes/btCollisionShape.h"
#include "BulletCollision/BroadphaseCollision/btBroadphaseProxy.h" // for the types

#include "btTriangleCallback.h"


///Concave shape proves an interface concave shapes that can produce triangles that overlapping a given AABB.
///Static triangle mesh, infinite plane, height field/landscapes are example that implement this interface.
class btConcaveShape : public btCollisionShape
{
protected:
	float m_collisionMargin;

public:
	btConcaveShape();

	virtual ~btConcaveShape();

	virtual void	processAllTriangles(btTriangleCallback* callback,const btVector3& aabbMin,const btVector3& aabbMax) const = 0;

	virtual float getMargin() const {
		return m_collisionMargin;
	}
	virtual void setMargin(float collisionMargin)
	{
		m_collisionMargin = collisionMargin;
	}



};

#endif //CONCAVE_SHAPE_H
