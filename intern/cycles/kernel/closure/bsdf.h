/*
 * Adapted from Open Shading Language with this license:
 *
 * Copyright (c) 2009-2010 Sony Pictures Imageworks Inc., et al.
 * All Rights Reserved.
 *
 * Modifications Copyright 2011, Blender Foundation.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are
 * met:
 * * Redistributions of source code must retain the above copyright
 *   notice, this list of conditions and the following disclaimer.
 * * Redistributions in binary form must reproduce the above copyright
 *   notice, this list of conditions and the following disclaimer in the
 *   documentation and/or other materials provided with the distribution.
 * * Neither the name of Sony Pictures Imageworks nor the names of its
 *   contributors may be used to endorse or promote products derived from
 *   this software without specific prior written permission.
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 * A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 * OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 * LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 * DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 * THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#ifndef __OSL_BSDF_H__
#define __OSL_BSDF_H__

CCL_NAMESPACE_BEGIN

__device float fresnel_dielectric(float eta, const float3 N,
		const float3 I, float3 *R, float3 *T,
#ifdef __RAY_DIFFERENTIALS__
		const float3 dIdx, const float3 dIdy,
		float3 *dRdx, float3 *dRdy,
		float3 *dTdx, float3 *dTdy, 
#endif
		bool *is_inside)
{
	float cos = dot(N, I), neta;
	float3 Nn;
	// compute reflection
	*R = (2 * cos)* N - I;
#ifdef __RAY_DIFFERENTIALS__
	*dRdx = (2 * dot(N, dIdx)) * N - dIdx;
	*dRdy = (2 * dot(N, dIdy)) * N - dIdy;
#endif
	// check which side of the surface we are on
	if(cos > 0) {
		// we are on the outside of the surface, going in
		neta = 1 / eta;
		Nn   = N;
		*is_inside = false;
	}
	else {
		// we are inside the surface, 
		cos  = -cos;
		neta = eta;
		Nn   = -N;
		*is_inside = true;
	}
	*R = (2 * cos)* Nn - I;
	float arg = 1 -(neta * neta *(1 -(cos * cos)));
	if(arg < 0) {
		*T = make_float3(0.0f, 0.0f, 0.0f);
#ifdef __RAY_DIFFERENTIALS__
		*dTdx = make_float3(0.0f, 0.0f, 0.0f);
		*dTdy = make_float3(0.0f, 0.0f, 0.0f);
#endif
		return 1; // total internal reflection
	}
	else {
		float dnp = sqrtf(arg);
		float nK = (neta * cos)- dnp;
		*T = -(neta * I)+(nK * Nn);
#ifdef __RAY_DIFFERENTIALS__
		*dTdx = -(neta * dIdx) + ((neta - neta * neta * cos / dnp) * dot(dIdx, Nn)) * Nn;
		*dTdy = -(neta * dIdy) + ((neta - neta * neta * cos / dnp) * dot(dIdy, Nn)) * Nn;
#endif
		// compute Fresnel terms
		float cosTheta1 = cos; // N.R
		float cosTheta2 = -dot(Nn, *T);
		float pPara = (cosTheta1 - eta * cosTheta2)/(cosTheta1 + eta * cosTheta2);
		float pPerp = (eta * cosTheta1 - cosTheta2)/(eta * cosTheta1 + cosTheta2);
		return 0.5f * (pPara * pPara + pPerp * pPerp);
	}
}

__device float fresnel_dielectric_cos(float cosi, float eta)
{
	// compute fresnel reflectance without explicitly computing
	// the refracted direction
	float c = fabsf(cosi);
	float g = eta * eta - 1 + c * c;
	if(g > 0) {
		g = sqrtf(g);
		float A = (g - c)/(g + c);
		float B = (c *(g + c)- 1)/(c *(g - c)+ 1);
		return 0.5f * A * A *(1 + B * B);
	}
	return 1.0f; // TIR(no refracted component)
}

__device float fresnel_conductor(float cosi, float eta, float k)
{
	float tmp_f = eta * eta + k * k;
	float tmp = tmp_f * cosi * cosi;
	float Rparl2 = (tmp - (2.0f * eta * cosi) + 1)/
	               (tmp + (2.0f * eta * cosi) + 1);
	float Rperp2 = (tmp_f - (2.0f * eta * cosi) + cosi * cosi)/
	               (tmp_f + (2.0f * eta * cosi) + cosi * cosi);
	return(Rparl2 + Rperp2) * 0.5f;
}

__device float smooth_step(float edge0, float edge1, float x)
{
	float result;
	if(x < edge0) result = 0.0f;
	else if(x >= edge1) result = 1.0f;
	else {
		float t = (x - edge0)/(edge1 - edge0);
		result = (3.0f-2.0f*t)*(t*t);
	}
	return result;
}

CCL_NAMESPACE_END

#endif /* __OSL_BSDF_H__ */

