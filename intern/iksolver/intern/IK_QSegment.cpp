/**
 * $Id$
 * ***** BEGIN GPL/BL DUAL LICENSE BLOCK *****
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version. The Blender
 * Foundation also sells licenses for use in proprietary software under
 * the Blender License.  See http://www.blender.org/BL/ for information
 * about this.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
 *
 * The Original Code is Copyright (C) 2001-2002 by NaN Holding BV.
 * All rights reserved.
 *
 * The Original Code is: all of this file.
 *
 * Original Author: Laurence
 * Contributor(s): Brecht
 *
 * ***** END GPL/BL DUAL LICENSE BLOCK *****
 */

#include "IK_QSegment.h"

#include <iostream>
using namespace std;

// Utility functions

static MT_Matrix3x3 RotationMatrix(MT_Scalar sine, MT_Scalar cosine, int axis)
{
	if (axis == 0)
		return MT_Matrix3x3(1.0, 0.0, 0.0,
		                    0.0, cosine, -sine,
		                    0.0, sine, cosine);
	else if (axis == 1)
		return MT_Matrix3x3(cosine, 0.0, sine,
		                    0.0, 1.0, 0.0,
		                    -sine, 0.0, cosine);
	else
		return MT_Matrix3x3(cosine, -sine, 0.0,
		                    sine, cosine, 0.0,
		                    0.0, 0.0, 1.0);
}

static MT_Matrix3x3 RotationMatrix(MT_Scalar angle, int axis)
{
	return RotationMatrix(sin(angle), cos(angle), axis);
}

static MT_Scalar safe_acos(MT_Scalar f)
{
	if (f <= -1.0f)
		return MT_PI;
	else if (f >= 1.0f)
		return 0.0;
	else
		return acos(f);
}

static MT_Scalar ComputeTwist(const MT_Matrix3x3& R)
{
	// qy and qw are the y and w components of the quaternion from R
	MT_Scalar qy = R[0][2] - R[2][0];
	MT_Scalar qw = R[0][0] + R[1][1] + R[2][2] + 1;

	MT_Scalar tau = 2*atan2(qy, qw);

	return tau;
}

static MT_Matrix3x3 ComputeTwistMatrix(MT_Scalar tau)
{
	return RotationMatrix(tau, 1);
}

static void RemoveTwist(MT_Matrix3x3& R)
{
	// compute twist parameter
	MT_Scalar tau = ComputeTwist(R);

	// compute twist matrix
	MT_Matrix3x3 T = ComputeTwistMatrix(tau);

	// remove twist
	R = R*T.transposed();
}

static MT_Vector3 SphericalRangeParameters(const MT_Matrix3x3& R)
{
	// compute twist parameter
	MT_Scalar tau = ComputeTwist(R);

	// compute swing parameters
	MT_Scalar num = 2.0*(1.0 + R[1][1]);

	// singularity at pi
	if (MT_abs(num) < MT_EPSILON)
		// TODO: this does now rotation of size pi over z axis, but could
		// be any axis, how to deal with this i'm not sure, maybe don't
		// enforce limits at all then
		return MT_Vector3(0.0, tau, 1.0);

	num = 1.0/sqrt(num);
	MT_Scalar ax = -R[2][1]*num;
	MT_Scalar az = R[0][1]*num;

	return MT_Vector3(ax, tau, az);
}

static MT_Matrix3x3 ComputeSwingMatrix(MT_Scalar ax, MT_Scalar az)
{
	// length of (ax, 0, az) = sin(theta/2)
	MT_Scalar sine2 = ax*ax + az*az;
	MT_Scalar cosine2 = sqrt((sine2 >= 1.0)? 0.0: 1.0-sine2);

	// compute swing matrix
	MT_Matrix3x3 S(MT_Quaternion(ax, 0.0, az, -cosine2));

	return S;
}

static MT_Vector3 MatrixToAxisAngle(const MT_Matrix3x3& R)
{
	MT_Vector3 delta = MT_Vector3(R[2][1] - R[1][2],
	                              R[0][2] - R[2][0],
	                              R[1][0] - R[0][1]);

	MT_Scalar c = safe_acos((R[0][0] + R[1][1] + R[2][2] - 1)/2);
	MT_Scalar l = delta.length();
	
	if (!MT_fuzzyZero(l))
		delta *= c/l;
	
	return delta;
}

// IK_QSegment

IK_QSegment::IK_QSegment(int num_DoF, bool translational)
: m_parent(NULL), m_child(NULL), m_sibling(NULL), m_num_DoF(num_DoF),
  m_translational(translational)
{
	m_locked[0] = m_locked[1] = m_locked[2] = false;
	m_weight[0] = m_weight[1] = m_weight[2] = 1.0;

	m_max_extension = 0.0;

	m_start = MT_Vector3(0, 0, 0);
	m_rest_basis.setIdentity();
	m_basis.setIdentity();
	m_translation = MT_Vector3(0, 0, 0);

	m_orig_basis = m_basis;
	m_orig_translation = m_translation;
}

void IK_QSegment::SetTransform(
	const MT_Vector3& start,
	const MT_Matrix3x3& rest_basis,
	const MT_Matrix3x3& basis,
	const MT_Scalar length
)
{
	m_max_extension = start.length() + length;	

	m_start = start;
	m_rest_basis = rest_basis;
	m_basis = basis;
	m_translation = MT_Vector3(0, length, 0);

	m_orig_basis = m_basis;
	m_orig_translation = m_translation;
}

MT_Matrix3x3 IK_QSegment::BasisChange() const
{
	return m_orig_basis.transposed()*m_basis;
}

MT_Vector3 IK_QSegment::TranslationChange() const
{
	return m_translation - m_orig_translation;
}

IK_QSegment::~IK_QSegment()
{
	if (m_parent)
		m_parent->RemoveChild(this);

	for (IK_QSegment *seg = m_child; seg; seg = seg->m_sibling)
		seg->m_parent = NULL;
}

void IK_QSegment::SetParent(IK_QSegment *parent)
{
	if (m_parent == parent)
		return;
	
	if (m_parent)
		m_parent->RemoveChild(this);
	
	if (parent) {
		m_sibling = parent->m_child;
		parent->m_child = this;
	}

	m_parent = parent;
}

void IK_QSegment::RemoveChild(IK_QSegment *child)
{
	if (m_child == NULL)
		return;
	else if (m_child == child)
		m_child = m_child->m_sibling;
	else {
		IK_QSegment *seg = m_child;

		while (seg->m_sibling != child);
			seg = seg->m_sibling;

		if (child == seg->m_sibling)
			seg->m_sibling = child->m_sibling;
	}
}

void IK_QSegment::UpdateTransform(const MT_Transform& global)
{
	// compute the global transform at the end of the segment
	m_global_start = global.getOrigin() + global.getBasis()*m_start;

	m_global_transform.setOrigin(m_global_start);
	m_global_transform.setBasis(global.getBasis() * m_rest_basis * m_basis);
	m_global_transform.translate(m_translation);

	// update child transforms
	for (IK_QSegment *seg = m_child; seg; seg = seg->m_sibling)
		seg->UpdateTransform(m_global_transform);
}

// IK_QSphericalSegment

IK_QSphericalSegment::IK_QSphericalSegment()
: IK_QSegment(3, false), m_limit_x(false), m_limit_y(false), m_limit_z(false)
{
}

MT_Vector3 IK_QSphericalSegment::Axis(int dof) const
{
	return m_global_transform.getBasis().getColumn(dof);
}

void IK_QSphericalSegment::SetLimit(int axis, MT_Scalar lmin, MT_Scalar lmax)
{
	if (lmin >= lmax)
		return;
	
	if (axis == 1) {
		lmin = MT_clamp(lmin, -180, 180);
		lmax = MT_clamp(lmax, -180, 180);

		m_min_y = MT_radians(lmin);
		m_max_y = MT_radians(lmax);

		m_limit_y = true;
	}
	else {
		// clamp and convert to axis angle parameters
		lmin = MT_clamp(lmin, -180, 180);
		lmax = MT_clamp(lmax, -180, 180);

		lmin = sin(MT_radians(lmin)*0.5);
		lmax = sin(MT_radians(lmax)*0.5);

		// put center of ellispe in the middle between min and max
		MT_Scalar offset = 0.5*(lmin + lmax);
		lmax = lmax - offset;

		if (axis == 0) {
			m_limit_x = true;
			m_offset_x = offset;
			m_max_x = lmax;
		}
		else if (axis == 2) {
			m_limit_z = true;
			m_offset_z = offset;
			m_max_z = lmax;
		}
	}
}

void IK_QSphericalSegment::SetWeight(int axis, MT_Scalar weight)
{
	m_weight[axis] = weight;
}

bool IK_QSphericalSegment::UpdateAngle(const IK_QJacobian &jacobian, MT_Vector3& delta, bool *clamp)
{
	if (m_locked[0] && m_locked[1] && m_locked[2])
		return false;

	MT_Vector3 dq;
	dq.x() = jacobian.AngleUpdate(m_DoF_id);
	dq.y() = jacobian.AngleUpdate(m_DoF_id+1);
	dq.z() = jacobian.AngleUpdate(m_DoF_id+2);

	// Directly update the rotation matrix, with Rodrigues' rotation formula,
	// to avoid singularities and allow smooth integration.

	MT_Scalar theta = dq.length();

	if (!MT_fuzzyZero(theta)) {
		MT_Vector3 w = dq*(1.0/theta);

		MT_Scalar sine = sin(theta);
		MT_Scalar cosine = cos(theta);
		MT_Scalar cosineInv = 1-cosine;

		MT_Scalar xsine = w.x()*sine;
		MT_Scalar ysine = w.y()*sine;
		MT_Scalar zsine = w.z()*sine;

		MT_Scalar xxcosine = w.x()*w.x()*cosineInv;
		MT_Scalar xycosine = w.x()*w.y()*cosineInv;
		MT_Scalar xzcosine = w.x()*w.z()*cosineInv;
		MT_Scalar yycosine = w.y()*w.y()*cosineInv;
		MT_Scalar yzcosine = w.y()*w.z()*cosineInv;
		MT_Scalar zzcosine = w.z()*w.z()*cosineInv;

		MT_Matrix3x3 M(
			cosine + xxcosine, -zsine + xycosine, ysine + xzcosine,
			zsine + xycosine, cosine + yycosine, -xsine + yzcosine,
			-ysine + xzcosine, xsine + yzcosine, cosine + zzcosine);

		m_new_basis = m_basis*M;
	}
	else
		m_new_basis = m_basis;

	
	if (m_limit_y == false && m_limit_x == false && m_limit_z == false)
		return false;

	MT_Vector3 a = SphericalRangeParameters(m_new_basis);

	if (m_locked[0])
		a.x() = m_locked_ax;
	if (m_locked[1])
		a.y() = m_locked_ay;
	if (m_locked[2])
		a.z() = m_locked_az;

	MT_Scalar ax = a.x(), ay = a.y(), az = a.z();

	clamp[0] = clamp[1] = clamp[2] =  false;
	
	if (m_limit_y) {
		if (a.y() > m_max_y) {
			ay = m_max_y;
			clamp[1] = true;
		}
		else if (a.y() < m_min_y) {
			ay = m_min_y;
			clamp[1] = true;
		}
	}

	if (m_limit_x && m_limit_z) {
		/* check in ellipsoid region */
		ax = a.x() + m_offset_x;
		az = a.z() + m_offset_z;

		MT_Scalar invX = 1.0/(m_max_x*m_max_x);
		MT_Scalar invZ = 1.0/(m_max_z*m_max_z);

		if ((ax*ax*invX + az*az*invZ) > 1.0) {
			clamp[0] = clamp[2] = true;

			if (MT_fuzzyZero(ax)) {
				ax = 0.0;
				az = (az > 0)? m_max_z: -m_max_z;
			}
			else {
				MT_Scalar rico = az/ax;
				MT_Scalar old_ax = ax;
				ax = sqrt(1.0/(invX + invZ*rico*rico));
				if (old_ax < 0.0)
					ax = -ax;
				az = rico*ax;
			}
		}

		ax = ax - m_offset_x;
		az = az - m_offset_z;
	}
	else if (m_limit_x) {
		ax = a.x() + m_offset_x;

		if (ax < -m_max_x) {
			ax = -m_max_x;
			clamp[0] = true;
		}
		else if (ax > m_max_x) {
			ax = m_max_x;
			clamp[0] = true;
		}

		ax = ax - m_offset_x;
		az = a.z();
	}
	else if (m_limit_z) {
		az = a.z() + m_offset_z;

		if (az < -m_max_z) {
			az = -m_max_z;
			clamp[2] = true;
		}
		else if (az > m_max_z) {
			az = m_max_z;
			clamp[2] = true;
		}

		ax = a.x();
		az = az - m_offset_z;
	}

	if (clamp[0] == false && clamp[1] == false && clamp[2] == false) {
		if (m_locked[0] || m_locked[1] || m_locked[2])
			m_new_basis = ComputeSwingMatrix(ax, az)*ComputeTwistMatrix(ay);
		return false;
	}
	
	m_new_basis = ComputeSwingMatrix(ax, az)*ComputeTwistMatrix(ay);

	delta = MatrixToAxisAngle(m_basis.transposed()*m_new_basis);

	if (!(m_locked[0] || m_locked[2]) && (clamp[0] || clamp[2])) {
		m_locked_ax = ax;
		m_locked_az = az;
	}

	if (!m_locked[1] && clamp[1])
		m_locked_ay = ay;
	
	return true;
}

void IK_QSphericalSegment::Lock(int dof, IK_QJacobian& jacobian, MT_Vector3& delta)
{
	if (dof == 1) {
		m_locked[1] = true;
		jacobian.Lock(m_DoF_id+1, delta[1]);
	}
	else {
		m_locked[0] = m_locked[2] = true;
		jacobian.Lock(m_DoF_id, delta[0]);
		jacobian.Lock(m_DoF_id+2, delta[2]);
	}
}

void IK_QSphericalSegment::UpdateAngleApply()
{
	m_basis = m_new_basis;
}

// IK_QNullSegment

IK_QNullSegment::IK_QNullSegment()
: IK_QSegment(0, false)
{
}

// IK_QRevoluteSegment

IK_QRevoluteSegment::IK_QRevoluteSegment(int axis)
: IK_QSegment(1, false), m_axis(axis), m_angle(0.0), m_limit(false)
{
}

MT_Vector3 IK_QRevoluteSegment::Axis(int) const
{
	return m_global_transform.getBasis().getColumn(m_axis);
}

bool IK_QRevoluteSegment::UpdateAngle(const IK_QJacobian &jacobian, MT_Vector3& delta, bool *clamp)
{
	if (m_locked[0])
		return false;

	m_new_angle = m_angle + jacobian.AngleUpdate(m_DoF_id);

	clamp[0] = false;

	if (m_limit == false)
		return false;

	if (m_new_angle > m_max)
		delta[0] = m_max - m_angle;
	else if (m_new_angle < m_min)
		delta[0] = m_min - m_angle;
	else
		return false;
	
	clamp[0] = true;
	m_new_angle = m_angle + delta[0];

	return true;
}

void IK_QRevoluteSegment::Lock(int, IK_QJacobian& jacobian, MT_Vector3& delta)
{
	m_locked[0] = true;
	jacobian.Lock(m_DoF_id, delta[0]);
}

void IK_QRevoluteSegment::UpdateAngleApply()
{
	m_angle = m_new_angle;

	m_basis = m_orig_basis*RotationMatrix(m_angle, m_axis);
}

void IK_QRevoluteSegment::SetLimit(int axis, MT_Scalar lmin, MT_Scalar lmax)
{
	if (lmin >= lmax || m_axis != axis)
		return;
	
	// clamp and convert to axis angle parameters
	lmin = MT_clamp(lmin, -180, 180);
	lmax = MT_clamp(lmax, -180, 180);

	m_min = MT_radians(lmin);
	m_max = MT_radians(lmax);

	m_limit = true;
}

void IK_QRevoluteSegment::SetWeight(int axis, MT_Scalar weight)
{
	if (axis == m_axis)
		m_weight[0] = weight;
}

// IK_QSwingSegment

IK_QSwingSegment::IK_QSwingSegment()
: IK_QSegment(2, false), m_limit_x(false), m_limit_z(false)
{
}

MT_Vector3 IK_QSwingSegment::Axis(int dof) const
{
	return m_global_transform.getBasis().getColumn((dof==0)? 0: 2);
}

bool IK_QSwingSegment::UpdateAngle(const IK_QJacobian &jacobian, MT_Vector3& delta, bool *clamp)
{
	if (m_locked[0] && m_locked[1])
		return false;

	MT_Vector3 dq;
	dq.x() = jacobian.AngleUpdate(m_DoF_id);
	dq.y() = 0.0;
	dq.z() = jacobian.AngleUpdate(m_DoF_id+1);

	// Directly update the rotation matrix, with Rodrigues' rotation formula,
	// to avoid singularities and allow smooth integration.

	MT_Scalar theta = dq.length();

	if (!MT_fuzzyZero(theta)) {
		MT_Vector3 w = dq*(1.0/theta);

		MT_Scalar sine = sin(theta);
		MT_Scalar cosine = cos(theta);
		MT_Scalar cosineInv = 1-cosine;

		MT_Scalar xsine = w.x()*sine;
		MT_Scalar zsine = w.z()*sine;

		MT_Scalar xxcosine = w.x()*w.x()*cosineInv;
		MT_Scalar xzcosine = w.x()*w.z()*cosineInv;
		MT_Scalar zzcosine = w.z()*w.z()*cosineInv;

		MT_Matrix3x3 M(
			cosine + xxcosine, -zsine, xzcosine,
			zsine, cosine, -xsine,
			xzcosine, xsine, cosine + zzcosine);

		m_new_basis = m_basis*M;

		RemoveTwist(m_new_basis);
	}
	else
		m_new_basis = m_basis;

	if (m_limit_x == false && m_limit_z == false)
		return false;

	MT_Vector3 a = SphericalRangeParameters(m_new_basis);
	MT_Scalar ax = 0, az = 0;

	clamp[0] = clamp[1] = false;
	
	if (m_limit_x && m_limit_z) {
		/* check in ellipsoid region */
		ax = a.x() + m_offset_x;
		az = a.z() + m_offset_z;

		MT_Scalar invX = 1.0/(m_max_x*m_max_x);
		MT_Scalar invZ = 1.0/(m_max_z*m_max_z);

		if ((ax*ax*invX + az*az*invZ) > 1.0) {
			clamp[0] = clamp[1] = true;

			if (MT_fuzzyZero(ax)) {
				ax = 0.0;
				az = (az > 0)? m_max_z: -m_max_z;
			}
			else {
				MT_Scalar rico = az/ax;
				MT_Scalar old_ax = ax;
				ax = sqrt(1.0/(invX + invZ*rico*rico));
				if (old_ax < 0.0)
					ax = -ax;
				az = rico*ax;
			}
		}

		ax = ax - m_offset_x;
		az = az - m_offset_z;
	}
	else if (m_limit_x) {
		ax = a.x() + m_offset_x;

		if (ax < -m_max_x) {
			ax = -m_max_x;
			clamp[0] = true;
		}
		else if (ax > m_max_x) {
			ax = m_max_x;
			clamp[0] = true;
		}

		ax = ax - m_offset_x;
		az = a.z();
	}
	else if (m_limit_z) {
		az = a.z() + m_offset_z;

		if (az < -m_max_z) {
			az = -m_max_z;
			clamp[1] = true;
		}
		else if (az > m_max_z) {
			az = m_max_z;
			clamp[1] = true;
		}

		ax = a.x();
		az = az - m_offset_z;
	}

	if (clamp[0] == false && clamp[1] == false)
		return false;

	m_new_basis = ComputeSwingMatrix(ax, az);

	delta = MatrixToAxisAngle(m_basis.transposed()*m_new_basis);
	delta[1] = delta[2]; delta[2] = 0.0;

	return true;
}

void IK_QSwingSegment::Lock(int, IK_QJacobian& jacobian, MT_Vector3& delta)
{
	m_locked[0] = m_locked[1] = true;
	jacobian.Lock(m_DoF_id, delta[0]);
	jacobian.Lock(m_DoF_id+1, delta[1]);
}

void IK_QSwingSegment::UpdateAngleApply()
{
	m_basis = m_new_basis;
}

void IK_QSwingSegment::SetLimit(int axis, MT_Scalar lmin, MT_Scalar lmax)
{
	if (lmin >= lmax)
		return;
	
	// clamp and convert to axis angle parameters
	lmin = MT_clamp(lmin, -180, 180);
	lmax = MT_clamp(lmax, -180, 180);

	lmin = sin(MT_radians(lmin)*0.5);
	lmax = sin(MT_radians(lmax)*0.5);

	// put center of ellispe in the middle between min and max
	MT_Scalar offset = 0.5*(lmin + lmax);
	lmax = lmax - offset;

	if (axis == 0) {
		m_limit_x = true;
		m_offset_x = offset;
		m_max_x = lmax;
	}
	else if (axis == 2) {
		m_limit_z = true;
		m_offset_z = offset;
		m_max_z = lmax;
	}
}

void IK_QSwingSegment::SetWeight(int axis, MT_Scalar weight)
{
	if (axis == 0)
		m_weight[0] = weight;
	else if (axis == 2)
		m_weight[1] = weight;
}

// IK_QElbowSegment

IK_QElbowSegment::IK_QElbowSegment(int axis)
: IK_QSegment(2, false), m_axis(axis), m_twist(0.0), m_angle(0.0),
  m_cos_twist(1.0), m_sin_twist(0.0), m_limit(false), m_limit_twist(false)
{
}

MT_Vector3 IK_QElbowSegment::Axis(int dof) const
{
	if (dof == 0) {
		MT_Vector3 v;
		if (m_axis == 0)
			v = MT_Vector3(m_cos_twist, 0, m_sin_twist);
		else
			v = MT_Vector3(-m_sin_twist, 0, m_cos_twist);

		return m_global_transform.getBasis() * v;
	}
	else
		return m_global_transform.getBasis().getColumn(1);
}

bool IK_QElbowSegment::UpdateAngle(const IK_QJacobian &jacobian, MT_Vector3& delta, bool *clamp)
{
	if (m_locked[0] && m_locked[1])
		return false;

	clamp[0] = clamp[1] = false;

	if (!m_locked[0]) {
		m_new_angle = m_angle + jacobian.AngleUpdate(m_DoF_id);

		if (m_limit) {
			if (m_new_angle > m_max) {
				delta[0] = m_max - m_angle;
				m_new_angle = m_max;
				clamp[0] = true;
			}
			else if (m_new_angle < m_min) {
				delta[0] = m_min - m_angle;
				m_new_angle = m_min;
				clamp[0] = true;
			}
		}
	}

	if (!m_locked[1]) {
		m_new_twist = m_twist + jacobian.AngleUpdate(m_DoF_id+1);

		if (m_limit_twist) {
			if (m_new_twist > m_max_twist) {
				delta[1] = m_max_twist - m_twist;
				m_new_twist = m_max_twist;
				clamp[1] = true;
			}
			else if (m_new_twist < m_min_twist) {
				delta[1] = m_min_twist - m_twist;
				m_new_twist = m_min_twist;
				clamp[1] = true;
			}
		}
	}

	return (clamp[0] || clamp[1]);
}

void IK_QElbowSegment::Lock(int dof, IK_QJacobian& jacobian, MT_Vector3& delta)
{
	if (dof == 0) {
		m_locked[0] = true;
		jacobian.Lock(m_DoF_id, delta[0]);
	}
	else {
		m_locked[1] = true;
		jacobian.Lock(m_DoF_id+1, delta[1]);
	}
}

void IK_QElbowSegment::UpdateAngleApply()
{
	m_angle = m_new_angle;
	m_twist = m_new_twist;

	m_sin_twist = sin(m_twist);
	m_cos_twist = cos(m_twist);

	MT_Matrix3x3 A = RotationMatrix(m_angle, m_axis);
	MT_Matrix3x3 T = RotationMatrix(m_sin_twist, m_cos_twist, 1);

	m_basis = m_orig_basis*A*T;
}

void IK_QElbowSegment::SetLimit(int axis, MT_Scalar lmin, MT_Scalar lmax)
{
	if (lmin >= lmax)
		return;

	// clamp and convert to axis angle parameters
	lmin = MT_clamp(lmin, -180, 180);
	lmax = MT_clamp(lmax, -180, 180);

	lmin = MT_radians(lmin);
	lmax = MT_radians(lmax);

	if (axis == 1) {
		m_min_twist = lmin;
		m_max_twist = lmax;
		m_limit_twist = true;
	}
	else if (axis == m_axis) {
		m_min = lmin;
		m_max = lmax;
		m_limit = true;
	}
}

void IK_QElbowSegment::SetWeight(int axis, MT_Scalar weight)
{
	if (axis == m_axis)
		m_weight[0] = weight;
	else if (axis == 1)
		m_weight[1] = weight;
}

// IK_QTranslateSegment

IK_QTranslateSegment::IK_QTranslateSegment(int axis1)
: IK_QSegment(1, true)
{
	m_axis_enabled[0] = m_axis_enabled[1] = m_axis_enabled[2] = false;
	m_axis_enabled[axis1] = true;

	m_axis[0] = axis1;
}

IK_QTranslateSegment::IK_QTranslateSegment(int axis1, int axis2)
: IK_QSegment(2, true)
{
	m_axis_enabled[0] = m_axis_enabled[1] = m_axis_enabled[2] = false;
	m_axis_enabled[axis1] = true;
	m_axis_enabled[axis2] = true;

	m_axis[0] = axis1;
	m_axis[1] = axis2;
}

IK_QTranslateSegment::IK_QTranslateSegment()
: IK_QSegment(3, true)
{
	m_axis_enabled[0] = m_axis_enabled[1] = m_axis_enabled[2] = true;

	m_axis[0] = 0;
	m_axis[1] = 1;
	m_axis[2] = 2;
}

MT_Vector3 IK_QTranslateSegment::Axis(int dof) const
{
	return m_global_transform.getBasis().getColumn(m_axis[dof]);
}

bool IK_QTranslateSegment::UpdateAngle(const IK_QJacobian &jacobian, MT_Vector3&, bool*)
{
	int dof_id = m_DoF_id;

	MT_Vector3 dx;
	dx.x() = (m_axis_enabled[0])? jacobian.AngleUpdate(dof_id++): 0.0;
	dx.y() = (m_axis_enabled[1])? jacobian.AngleUpdate(dof_id++): 0.0;
	dx.z() = (m_axis_enabled[2])? jacobian.AngleUpdate(dof_id++): 0.0;

	m_new_translation = m_translation + dx;

	return false;
}

void IK_QTranslateSegment::UpdateAngleApply()
{
	m_translation = m_new_translation;
}

void IK_QTranslateSegment::SetWeight(int axis, MT_Scalar weight)
{
	m_weight[axis] = weight;
}

