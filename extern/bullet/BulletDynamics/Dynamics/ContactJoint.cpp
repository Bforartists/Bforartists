#include "ContactJoint.h"
#include "RigidBody.h"
#include "NarrowPhaseCollision/PersistentManifold.h"



ContactJoint::ContactJoint(PersistentManifold* manifold,int index,bool swap,RigidBody* body0,RigidBody* body1)
:m_manifold(manifold),
m_index(index),
m_swapBodies(swap),
m_body0(body0),
m_body1(body1)
{
}

int m_numRows = 3;

float gContactFrictionFactor  = 30.5f;//100.f;//1e30f;//2.9f;



void ContactJoint::GetInfo1(Info1 *info)
{
	info->m = m_numRows;
	//friction adds another 2...
	
	info->nub = 0;
}

#define dCROSS(a,op,b,c) \
  (a)[0] op ((b)[1]*(c)[2] - (b)[2]*(c)[1]); \
  (a)[1] op ((b)[2]*(c)[0] - (b)[0]*(c)[2]); \
  (a)[2] op ((b)[0]*(c)[1] - (b)[1]*(c)[0]);

#define M_SQRT12 SimdScalar(0.7071067811865475244008443621048490)

#define dRecipSqrt(x) ((float)(1.0f/sqrtf(float(x))))		/* reciprocal square root */



void dPlaneSpace1 (const dVector3 n, dVector3 p, dVector3 q)
{
  if (fabsf(n[2]) > M_SQRT12) {
    // choose p in y-z plane
    SimdScalar a = n[1]*n[1] + n[2]*n[2];
    SimdScalar k = dRecipSqrt (a);
    p[0] = 0;
    p[1] = -n[2]*k;
    p[2] = n[1]*k;
    // set q = n x p
    q[0] = a*k;
    q[1] = -n[0]*p[2];
    q[2] = n[0]*p[1];
  }
  else {
    // choose p in x-y plane
    SimdScalar a = n[0]*n[0] + n[1]*n[1];
    SimdScalar k = dRecipSqrt (a);
    p[0] = -n[1]*k;
    p[1] = n[0]*k;
    p[2] = 0;
    // set q = n x p
    q[0] = -n[2]*p[1];
    q[1] = n[2]*p[0];
    q[2] = a*k;
  }
}



void ContactJoint::GetInfo2(Info2 *info)
{
	
	int s = info->rowskip;
	int s2 = 2*s;
	
	float swapFactor = m_swapBodies ? -1.f : 1.f;
	
	// get normal, with sign adjusted for body1/body2 polarity
	dVector3 normal;
	
	
	ManifoldPoint& point = m_manifold->GetContactPoint(m_index);
	
	normal[0] = swapFactor*point.m_normalWorldOnB[0];
	normal[1] = swapFactor*point.m_normalWorldOnB[1];
	normal[2] = swapFactor*point.m_normalWorldOnB[2];
	normal[3] = 0;	// @@@ hmmm
	
	//	if (GetBody0())
	SimdVector3 ccc1;
	{
		ccc1 = point.GetPositionWorldOnA() - m_body0->getCenterOfMassPosition();
		dVector3 c1;
		c1[0] = ccc1[0];
		c1[1] = ccc1[1];
		c1[2] = ccc1[2];
		
		// set jacobian for normal
		info->J1l[0] = normal[0];
		info->J1l[1] = normal[1];
		info->J1l[2] = normal[2];
		dCROSS (info->J1a,=,c1,normal);
		
	}
	//		if (GetBody1())
	SimdVector3 ccc2;
	{
		dVector3 c2;
		ccc2 = point.GetPositionWorldOnB() - m_body1->getCenterOfMassPosition();
		
		//			for (i=0; i<3; i++) c2[i] = j->contact.geom.pos[i] -
		//					  j->node[1].body->pos[i];
		c2[0] = ccc2[0];
		c2[1] = ccc2[1];
		c2[2] = ccc2[2];
		
		info->J2l[0] = -normal[0];
		info->J2l[1] = -normal[1];
		info->J2l[2] = -normal[2];
		dCROSS (info->J2a,= -,c2,normal);
	}
	
	SimdScalar k = info->fps * info->erp;
	
	float depth = -point.GetDistance();
	if (depth < 0.f)
		depth = 0.f;
	
	info->c[0] = k * depth;
	
	
	
	// set LCP limits for normal
	info->lo[0] = 0;
	info->hi[0] = 1e30f;//dInfinity;
	
#define DO_THE_FRICTION_2
#ifdef DO_THE_FRICTION_2
	// now do jacobian for tangential forces
	dVector3 t1,t2;	// two vectors tangential to normal
	
	dVector3 c1;
	c1[0] = ccc1[0];
	c1[1] = ccc1[1];
	c1[2] = ccc1[2];
	
	dVector3 c2;
	c2[0] = ccc2[0];
	c2[1] = ccc2[1];
	c2[2] = ccc2[2];
	// first friction direction
	if (m_numRows >= 2) 
	{
		
		
		
		dPlaneSpace1 (normal,t1,t2);
		
		info->J1l[s+0] = t1[0];
		info->J1l[s+1] = t1[1];
		info->J1l[s+2] = t1[2];
		dCROSS (info->J1a+s,=,c1,t1);
		if (1) { //j->node[1].body) {
			info->J2l[s+0] = -t1[0];
			info->J2l[s+1] = -t1[1];
			info->J2l[s+2] = -t1[2];
			dCROSS (info->J2a+s,= -,c2,t1);
		}
		// set right hand side
		if (0) {//j->contact.surface.mode & dContactMotion1) {
			//info->c[1] = j->contact.surface.motion1;
		}
		// set LCP bounds and friction index. this depends on the approximation
		// mode
		//1e30f
		
		info->lo[1] = -gContactFrictionFactor;//-j->contact.surface.mu;
		info->hi[1] = gContactFrictionFactor;//j->contact.surface.mu;
		if (0)//j->contact.surface.mode & dContactApprox1_1) 
			info->findex[1] = 0;
		
		// set slip (constraint force mixing)
		if (0)//j->contact.surface.mode & dContactSlip1)
		{
			//	info->cfm[1] = j->contact.surface.slip1;
		}
	}
	
	// second friction direction
	if (m_numRows >= 3) {
		info->J1l[s2+0] = t2[0];
		info->J1l[s2+1] = t2[1];
		info->J1l[s2+2] = t2[2];
		dCROSS (info->J1a+s2,=,c1,t2);
		if (1) { //j->node[1].body) {
			info->J2l[s2+0] = -t2[0];
			info->J2l[s2+1] = -t2[1];
			info->J2l[s2+2] = -t2[2];
			dCROSS (info->J2a+s2,= -,c2,t2);
		}
		// set right hand side
		if (0){//j->contact.surface.mode & dContactMotion2) {
			//info->c[2] = j->contact.surface.motion2;
		}
		// set LCP bounds and friction index. this depends on the approximation
		// mode
		if (0){//j->contact.surface.mode & dContactMu2) {
			//info->lo[2] = -j->contact.surface.mu2;
			//info->hi[2] = j->contact.surface.mu2;
		}
		else {
			info->lo[2] = -gContactFrictionFactor;
			info->hi[2] = gContactFrictionFactor;
		}
		if (0)//j->contact.surface.mode & dContactApprox1_2) 
			
		{
			info->findex[2] = 0;
		}
		// set slip (constraint force mixing)
		if (0) //j->contact.surface.mode & dContactSlip2)
			
		{
			//info->cfm[2] = j->contact.surface.slip2;
			
		}
	}
	
#endif //DO_THE_FRICTION_2
	
}

