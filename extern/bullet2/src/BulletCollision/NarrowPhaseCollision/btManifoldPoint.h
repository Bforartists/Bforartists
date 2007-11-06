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

#ifndef MANIFOLD_CONTACT_POINT_H
#define MANIFOLD_CONTACT_POINT_H

#include "LinearMath/btVector3.h"
#include "LinearMath/btTransformUtil.h"





/// ManifoldContactPoint collects and maintains persistent contactpoints.
/// used to improve stability and performance of rigidbody dynamics response.
class btManifoldPoint
	{
		public:
			btManifoldPoint()
				:m_userPersistentData(0),
				m_lifeTime(0)
			{
			}

			btManifoldPoint( const btVector3 &pointA, const btVector3 &pointB, 
					const btVector3 &normal, 
					btScalar distance ) :
					m_localPointA( pointA ), 
					m_localPointB( pointB ), 
					m_normalWorldOnB( normal ), 
					m_distance1( distance ),
					m_combinedFriction(btScalar(0.)),
					m_combinedRestitution(btScalar(0.)),
					m_userPersistentData(0),					
					m_lifeTime(0)
			{
				
					
			}

			

			btVector3 m_localPointA;			
			btVector3 m_localPointB;			
			btVector3	m_positionWorldOnB;
			///m_positionWorldOnA is redundant information, see getPositionWorldOnA(), but for clarity
			btVector3	m_positionWorldOnA;
			btVector3 m_normalWorldOnB;
		
			btScalar	m_distance1;
			btScalar	m_combinedFriction;
			btScalar	m_combinedRestitution;

				
			mutable void*	m_userPersistentData;

			int		m_lifeTime;//lifetime of the contactpoint in frames
			
			btScalar getDistance() const
			{
				return m_distance1;
			}
			int	getLifeTime() const
			{
				return m_lifeTime;
			}

			const btVector3& getPositionWorldOnA() const {
				return m_positionWorldOnA;
//				return m_positionWorldOnB + m_normalWorldOnB * m_distance1;
			}

			const btVector3& getPositionWorldOnB() const
			{
				return m_positionWorldOnB;
			}

			void	setDistance(btScalar dist)
			{
				m_distance1 = dist;
			}
			
			

	};

#endif //MANIFOLD_CONTACT_POINT_H
