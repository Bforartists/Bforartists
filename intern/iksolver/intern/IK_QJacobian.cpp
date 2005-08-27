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

#include "IK_QJacobian.h"
#include "TNT/svd.h"

#include <iostream>
using namespace std;

IK_QJacobian::IK_QJacobian()
: m_sdls(true), m_min_damp(1.0)
{
}

IK_QJacobian::~IK_QJacobian()
{
}

void IK_QJacobian::ArmMatrices(int dof, int task_size, int tasks)
{
	m_dof = dof;
	m_task_size = task_size;
	m_tasks = tasks;

	m_jacobian.newsize(task_size, dof);
	m_jacobian = 0;

	m_alpha.newsize(dof);
	m_alpha = 0;

	m_null.newsize(dof, dof);

	m_d_theta.newsize(dof);
	m_d_theta_tmp.newsize(dof);

	m_norm.newsize(dof);
	m_norm = 0.0;

	m_beta.newsize(task_size);

	m_weight.newsize(dof);
	m_weight_sqrt.newsize(dof);
	m_weight = 1.0;
	m_weight_sqrt = 1.0;

	// m_svd_work_space.newsize(dof); // TNT resizes this?

	if (task_size >= dof) {
		m_transpose = false;

		m_svd_u.newsize(task_size, dof);
		m_svd_v.newsize(dof, dof);
		m_svd_w.newsize(dof);

		m_svd_u_t.newsize(dof, task_size);
		m_svd_u_beta.newsize(dof);
	}
	else {
		// use the SVD of the transpose jacobian, it works just as well
		// as the original, and often allows using smaller matrices.
		m_transpose = true;

		m_svd_u.newsize(task_size, task_size);
		m_svd_v.newsize(dof, task_size);
		m_svd_w.newsize(task_size);

		m_svd_u_t.newsize(task_size, task_size);
		m_svd_u_beta.newsize(task_size);
	}
}

void IK_QJacobian::SetBetas(int id, int, const MT_Vector3& v)
{
	m_beta[id] = v.x();
	m_beta[id+1] = v.y();
	m_beta[id+2] = v.z();

	//printf("#: %f %f %f\n", v.x(), v.y(), v.z());
}

void IK_QJacobian::SetDerivatives(int id, int dof_id, const MT_Vector3& v)
{
	m_jacobian[id][dof_id] = v.x()*m_weight_sqrt[dof_id];
	m_jacobian[id+1][dof_id] = v.y()*m_weight_sqrt[dof_id];
	m_jacobian[id+2][dof_id] = v.z()*m_weight_sqrt[dof_id];

	//printf("%d: %f %f %f\n", dof_id, v.x(), v.y(), v.z());
}

void IK_QJacobian::Invert()
{
	if (m_transpose) {
		// SVD will decompose Jt into V*W*Ut with U,V orthogonal and W diagonal,
		// so J = U*W*Vt and Jinv = V*Winv*Ut
		TNT::transpose(m_jacobian, m_svd_v);

		TNT::SVD(m_svd_v, m_svd_w, m_svd_u, m_svd_work_space);
	}
	else {
		// SVD will decompose J into U*W*Vt with U,V orthogonal and W diagonal,
		// so Jinv = V*Winv*Ut
		m_svd_u = m_jacobian;

		TNT::SVD(m_svd_u, m_svd_w, m_svd_v, m_svd_work_space);
	}

	if (m_sdls)
		InvertSDLS();
	else
		InvertDLS();
	
#if 0
	if (!ComputeNullProjection())
		return;
	
	int i, j;
	for (i = 0; i < m_weight.size(); i++)
		m_weight[i] = 1.0 - m_weight[i];

	TNT::matmultdiag(m_null, m_null, m_weight);

	for (i = 0; i < m_null.num_rows(); i++)
		for (j = 0; j < m_null.num_cols(); j++)
			if (i == j)
				m_null[i][j] = 1.0 - m_null[i][j];
			else
				m_null[i][j] = -m_null[i][j];
	
	TVector ntheta(m_d_theta);
	TNT::matmult(ntheta, m_null, m_d_theta);

	cout << "#" << endl;
	for (i = 0; i < m_d_theta.size(); i++)
		printf("%f >> %f (%f)\n", m_d_theta[i], ntheta[i], m_weight[i]);
	m_d_theta = ntheta;

	for (i = 0; i < m_weight.size(); i++)
		m_weight[i] = 1.0 - m_weight[i];
#endif
}

bool IK_QJacobian::ComputeNullProjection()
{
	MT_Scalar epsilon = 1e-10;
	
	// compute null space projection based on V
	int i, j, rank = 0;
	for (i = 0; i < m_svd_w.size(); i++)
		if (m_svd_w[i] > epsilon)
			rank++;

	if (rank < m_task_size)
		return false;

	TMatrix basis(m_svd_v.num_rows(), rank);
	TMatrix basis_t(rank, m_svd_v.num_rows());
	int b = 0;

	for (i = 0; i < m_svd_w.size(); i++)
		if (m_svd_w[i] > epsilon) {
			for (j = 0; j < m_svd_v.num_rows(); j++)
				basis[j][b] = m_svd_v[j][i];
			b++;
		}
	
	TNT::transpose(basis, basis_t);
	TNT::matmult(m_null, basis, basis_t);

	for (i = 0; i < m_null.num_rows(); i++)
		for (j = 0; j < m_null.num_cols(); j++)
			if (i == j)
				m_null[i][j] = 1.0 - m_null[i][j];
			else
				m_null[i][j] = -m_null[i][j];
	
	return true;
}

void IK_QJacobian::SubTask(IK_QJacobian& jacobian)
{
	if (!ComputeNullProjection())
		return;
	
#if 0
	int i, j;

	m_null.newsize(m_d_theta.size(), m_d_theta.size());

	for (i = 0; i < m_d_theta.size(); i++)
		for (j = 0; j < m_d_theta.size(); j++)
			if (i == j)
				m_null[i][j] = 1.0;
			else
				m_null[i][j] = 0.0;

	// restrict lower priority jacobian
	//jacobian.Restrict(m_d_theta, m_null);

	// add angle update from lower priority
	jacobian.Invert();

	TVector d2(m_d_theta.size());
	TVector n2(m_d_theta.size());

	for (i = 0; i < m_d_theta.size(); i++)
		d2[i] = jacobian.AngleUpdate(i);
	
	TNT::matmult(n2, m_null, d2);

	m_d_theta = m_d_theta + n2;
#else
	int i;

	// restrict lower priority jacobian
	jacobian.Restrict(m_d_theta, m_null);

	// add angle update from lower priority
	jacobian.Invert();

	// note: now damps secondary angles with minimum damping value from
	// SDLS, to avoid shaking when the primary task is near singularities,
	// doesn't work well at all
	for (i = 0; i < m_d_theta.size(); i++)
		m_d_theta[i] = m_d_theta[i] + /*m_min_damp**/jacobian.AngleUpdate(i);
#endif
}

void IK_QJacobian::Restrict(TVector& d_theta, TMatrix& null)
{
	// subtract part already moved by higher task from beta
	TVector beta_sub(m_beta.size());

	TNT::matmult(beta_sub, m_jacobian, d_theta);
	m_beta = m_beta - beta_sub;

	// note: should we be using the norm of the unrestricted jacobian for SDLS?
	
	// project jacobian on to null space of higher priority task
	TMatrix jacobian_copy(m_jacobian);
	TNT::matmult(m_jacobian, jacobian_copy, null);
}

void IK_QJacobian::InvertSDLS()
{
	// Compute the dampeds least squeares pseudo inverse of J.
	//
	// Since J is usually not invertible (most of the times it's not even
	// square), the psuedo inverse is used. This gives us a least squares
	// solution.
	//
	// This is fine when the J*Jt is of full rank. When J*Jt is near to
	// singular the least squares inverse tries to minimize |J(dtheta) - dX)|
	// and doesn't try to minimize  dTheta. This results in eratic changes in
	// angle. The damped least squares minimizes |dtheta| to try and reduce this
	// erratic behaviour.
	//
	// The selectively damped least squares (SDLS) is used here instead of the
	// DLS. The SDLS damps individual singular values, instead of using a single
	// damping term.

	MT_Scalar max_angle_change = MT_PI/4.0;
	MT_Scalar epsilon = 1e-10;
	int i, j;

	m_d_theta = 0;
	m_min_damp = 1.0;

	for (i = 0; i < m_dof; i++) {
		m_norm[i] = 0.0;
		for (j = 0; j < m_task_size; j+=3) {
			MT_Scalar n = 0.0;
			n += m_jacobian[j][i]*m_jacobian[j][i];
			n += m_jacobian[j+1][i]*m_jacobian[j+1][i];
			n += m_jacobian[j+2][i]*m_jacobian[j+2][i];
			m_norm[i] += sqrt(n);
		}
	}

	for (i = 0; i<m_svd_w.size(); i++) {
		if (m_svd_w[i] <= epsilon)
			continue;

		MT_Scalar wInv = 1.0/m_svd_w[i];
		MT_Scalar alpha = 0.0;
		MT_Scalar N = 0.0;

		// compute alpha and N
		for (j=0; j<m_svd_u.num_rows(); j+=3) {
			alpha += m_svd_u[j][i]*m_beta[j];
			alpha += m_svd_u[j+1][i]*m_beta[j+1];
			alpha += m_svd_u[j+2][i]*m_beta[j+2];

			// note: for 1 end effector, N will always be 1, since U is
			// orthogonal, .. so could be optimized
			MT_Scalar tmp;
			tmp = m_svd_u[j][i]*m_svd_u[j][i];
			tmp += m_svd_u[j+1][i]*m_svd_u[j+1][i];
			tmp += m_svd_u[j+2][i]*m_svd_u[j+2][i];
			N += sqrt(tmp);
		}
		alpha *= wInv;

		// compute M, dTheta and max_dtheta
		MT_Scalar M = 0.0;
		MT_Scalar max_dtheta = 0.0, abs_dtheta;

		for (j = 0; j < m_d_theta.size(); j++) {
			MT_Scalar v = m_svd_v[j][i];
			M += MT_abs(v)*m_norm[j];

			// compute tmporary dTheta's
			m_d_theta_tmp[j] = v*alpha;

			// find largest absolute dTheta
			// multiply with weight to prevent unnecessary damping
			abs_dtheta = MT_abs(m_d_theta_tmp[j])*m_weight_sqrt[j];
			if (abs_dtheta > max_dtheta)
				max_dtheta = abs_dtheta;
		}

		M *= wInv;

		// compute damping term and damp the dTheta's
		MT_Scalar gamma = max_angle_change;
		if (N < M)
			gamma *= N/M;

		MT_Scalar damp = (gamma < max_dtheta)? gamma/max_dtheta: 1.0;

		for (j = 0; j < m_d_theta.size(); j++)
			// slight hack: we do 0.80*, so that if there is some oscillation,
			// the system can still converge (for joint limits). also, it's
			// better to go a little to slow than to far
			m_d_theta[j] += 0.80*damp*m_d_theta_tmp[j];

		if (damp < m_min_damp)
			m_min_damp = damp;
	}

	// weight + prevent from doing angle updates with angles > max_angle_change
	MT_Scalar max_angle = 0.0, abs_angle;

	for (j = 0; j<m_dof; j++) {
		m_d_theta[j] *= m_weight[j];

		abs_angle = MT_abs(m_d_theta[j]);

		if (abs_angle > max_angle)
			max_angle = abs_angle;
	}
	
	if (max_angle > max_angle_change) {
		MT_Scalar damp = (max_angle_change)/(max_angle_change + max_angle);

		for (j = 0; j<m_dof; j++)
			m_d_theta[j] *= damp;
	}
}

void IK_QJacobian::InvertDLS()
{
	// Compute damped least squares inverse of pseudo inverse
	// Compute damping term lambda

	// Note when lambda is zero this is equivalent to the
	// least squares solution. This is fine when the m_jjt is
	// of full rank. When m_jjt is near to singular the least squares
	// inverse tries to minimize |J(dtheta) - dX)| and doesn't 
	// try to minimize  dTheta. This results in eratic changes in angle.
	// Damped least squares minimizes |dtheta| to try and reduce this
	// erratic behaviour.

	// We don't want to use the damped solution everywhere so we
	// only increase lamda from zero as we approach a singularity.

	// find the smallest non-zero W value, anything below epsilon is
	// treated as zero

	MT_Scalar epsilon = 1e-10;
	MT_Scalar max_angle_change = 0.1;
	MT_Scalar x_length = sqrt(TNT::dot_prod(m_beta, m_beta));

	int i, j;
	MT_Scalar w_min = MT_INFINITY;

	for (i = 0; i <m_svd_w.size() ; i++) {
		if (m_svd_w[i] > epsilon && m_svd_w[i] < w_min)
			w_min = m_svd_w[i];
	}
	
	// compute lambda damping term

	MT_Scalar d = x_length/max_angle_change;
	MT_Scalar lambda;

	if (w_min <= d/2)
		lambda = d/2;
	else if (w_min < d)
		lambda = sqrt(w_min*(d - w_min));
	else
		lambda = 0.0;

	lambda *= lambda;

	if (lambda > 10)
		lambda = 10;

	// immediately multiply with Beta, so we can do matrix*vector products
	// rather than matrix*matrix products

	// compute Ut*Beta
	TNT::transpose(m_svd_u, m_svd_u_t);
	TNT::matmult(m_svd_u_beta, m_svd_u_t, m_beta);

	m_d_theta = 0.0;

	for (i = 0; i < m_svd_w.size(); i++) {
		if (m_svd_w[i] > epsilon) {
			MT_Scalar wInv = m_svd_w[i]/(m_svd_w[i]*m_svd_w[i] + lambda);

			// compute V*Winv*Ut*Beta
			m_svd_u_beta[i] *= wInv;

			for (j = 0; j<m_d_theta.size(); j++)
				m_d_theta[j] += m_svd_v[j][i]*m_svd_u_beta[i];
		}
	}

	for (j = 0; j<m_d_theta.size(); j++)
		m_d_theta[j] *= m_weight[j];
}

void IK_QJacobian::Lock(int dof_id, MT_Scalar delta)
{
	int i;

	for (i = 0; i < m_task_size; i++) {
		m_beta[i] -= m_jacobian[i][dof_id]*delta;
		m_jacobian[i][dof_id] = 0.0;
	}

	m_norm[dof_id] = 0.0; // unneeded
	m_d_theta[dof_id] = 0.0;
}

#if 0
void IK_QJacobian::SetSecondary(int dof_id, MT_Scalar d)
{
	m_alpha[dof_id] = d;
}

void IK_QJacobian::SolveSecondary()
{
	if (!ComputeNullProjection())
		return;
	
	TNT::matmult(m_d_theta, m_null, m_alpha);

	m_alpha = 0;
}
#endif

MT_Scalar IK_QJacobian::AngleUpdate(int dof_id) const
{
	return m_d_theta[dof_id];
}

MT_Scalar IK_QJacobian::AngleUpdateNorm() const
{
	int i;
	MT_Scalar mx = 0.0, dtheta_abs;

	for (i = 0; i < m_d_theta.size(); i++) {
		dtheta_abs = MT_abs(m_d_theta[i]);
		if (dtheta_abs > mx)
			mx = dtheta_abs;
	}
	
	return mx;
}

void IK_QJacobian::SetDoFWeight(int dof, MT_Scalar weight)
{
	m_weight[dof] = weight;
	m_weight_sqrt[dof] = sqrt(weight);
}

