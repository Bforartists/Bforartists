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


#include "TypedConstraint.h"
#include "Dynamics/RigidBody.h"
#include "Dynamics/MassProps.h"

static RigidBody s_fixed(MassProps(0,SimdVector3(0.f,0.f,0.f)),0.f,0.f,1.f,1.f);

TypedConstraint::TypedConstraint()
: m_userConstraintType(-1),
m_userConstraintId(-1),
m_rbA(s_fixed),
m_rbB(s_fixed),
m_appliedImpulse(0.f)
{
	s_fixed.setMassProps(0.f,SimdVector3(0.f,0.f,0.f));
}
TypedConstraint::TypedConstraint(RigidBody& rbA)
: m_userConstraintType(-1),
m_userConstraintId(-1),
m_rbA(rbA),
m_rbB(s_fixed),
m_appliedImpulse(0.f)
{
		s_fixed.setMassProps(0.f,SimdVector3(0.f,0.f,0.f));

}


TypedConstraint::TypedConstraint(RigidBody& rbA,RigidBody& rbB)
: m_userConstraintType(-1),
m_userConstraintId(-1),
m_rbA(rbA),
m_rbB(rbB),
m_appliedImpulse(0.f)
{
		s_fixed.setMassProps(0.f,SimdVector3(0.f,0.f,0.f));

}

