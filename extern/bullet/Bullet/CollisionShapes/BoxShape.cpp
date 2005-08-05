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

#include "BoxShape.h"

SimdVector3 BoxShape::GetHalfExtents() const
{
	return m_boxHalfExtents1 * m_localScaling;
}
//{ 


void BoxShape::GetAabb(const SimdTransform& t,SimdVector3& aabbMin,SimdVector3& aabbMax) const
{
	SimdVector3 halfExtents = GetHalfExtents();

	SimdMatrix3x3 abs_b = t.getBasis().absolute();  
	SimdPoint3 center = t.getOrigin();
	SimdVector3 extent = SimdVector3(abs_b[0].dot(halfExtents),
		   abs_b[1].dot(halfExtents),
		  abs_b[2].dot(halfExtents));
	extent += SimdVector3(GetMargin(),GetMargin(),GetMargin());


	//todo: this is a quick fix, we need to enlarge the aabb dependent on several criteria
	extent += SimdVector3(.2f,.2f,.2f);

	aabbMin = center - extent;
	aabbMax = center + extent;


}


void	BoxShape::CalculateLocalInertia(SimdScalar mass,SimdVector3& inertia)
{
	float margin = 0.f;
	SimdVector3 halfExtents = GetHalfExtents();

	SimdScalar lx=2.f*(halfExtents.x());
	SimdScalar ly=2.f*(halfExtents.y());
	SimdScalar lz=2.f*(halfExtents.z());

	inertia[0] = mass/(12.0f) * (ly*ly + lz*lz);
	inertia[1] = mass/(12.0f) * (lx*lx + lz*lz);
	inertia[2] = mass/(12.0f) * (lx*lx + ly*ly);


//		float radius = GetHalfExtents().length();
//		SimdScalar elem = 0.4f * mass * radius*radius;
//	inertia[0] = inertia[1] = inertia[2] = elem;
return;
/*
	float margin = GetMargin();
	SimdVector3 halfExtents = GetHalfExtents();

	SimdScalar lx=2.f*(halfExtents.x()+margin);
	SimdScalar ly=2.f*(halfExtents.y()+margin);
	SimdScalar lz=2.f*(halfExtents.z()+margin);
	const SimdScalar x2 = lx*lx;
	const SimdScalar y2 = ly*ly;
	const SimdScalar z2 = lz*lz;
	const SimdScalar scaledmass = mass * 0.08333333f;

	inertia = scaledmass * (SimdVector3(y2+z2,x2+z2,x2+y2));
*/
//		inertia.x() = scaledmass * (y2+z2);
//		inertia.y() = scaledmass * (x2+z2);
//		inertia.z() = scaledmass * (x2+y2);
}