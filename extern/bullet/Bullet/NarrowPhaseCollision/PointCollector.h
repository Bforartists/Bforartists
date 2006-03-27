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

#ifndef POINT_COLLECTOR_H
#define POINT_COLLECTOR_H

#include "DiscreteCollisionDetectorInterface.h"



struct PointCollector : public DiscreteCollisionDetectorInterface::Result
{
	
	
	SimdVector3 m_normalOnBInWorld;
	SimdVector3 m_pointInWorld;
	SimdScalar	m_distance;//negative means penetration

	bool	m_hasResult;

	PointCollector () 
		: m_distance(1e30f),m_hasResult(false)
	{
	}

	virtual void AddContactPoint(const SimdVector3& normalOnBInWorld,const SimdVector3& pointInWorld,float depth)
	{
		if (depth< m_distance)
		{
			m_hasResult = true;
			m_normalOnBInWorld = normalOnBInWorld;
			m_pointInWorld = pointInWorld;
			//negative means penetration
			m_distance = depth;
		}
	}
};

#endif //POINT_COLLECTOR_H

