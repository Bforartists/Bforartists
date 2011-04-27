/*
 * Copyright 2011, Blender Foundation.
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 */

CCL_NAMESPACE_BEGIN

/* Voronoi Distances */

__device float voronoi_distance(NodeDistanceMetric distance_metric, float3 d, float e)
{
	if(distance_metric == NODE_VORONOI_DISTANCE_SQUARED)
		return dot(d, d);
	if(distance_metric == NODE_VORONOI_ACTUAL_DISTANCE)
		return len(d);
	if(distance_metric == NODE_VORONOI_MANHATTAN)
		return fabsf(d.x) + fabsf(d.y) + fabsf(d.z);
	if(distance_metric == NODE_VORONOI_CHEBYCHEV)
		return fmaxf(fabsf(d.x), fmaxf(fabsf(d.y), fabsf(d.z)));
	if(distance_metric == NODE_VORONOI_MINKOVSKY_H)
		return sqrtf(fabsf(d.x)) + sqrtf(fabsf(d.y)) + sqrtf(fabsf(d.y));
	if(distance_metric == NODE_VORONOI_MINKOVSKY_4)
		return sqrtf(sqrtf(dot(d*d, d*d)));
	if(distance_metric == NODE_VORONOI_MINKOVSKY)
		return powf(powf(fabsf(d.x), e) + powf(fabsf(d.y), e) + powf(fabsf(d.z), e), 1.0f/e);
	
	return 0.0f;
}

/* Voronoi / Worley like */

__device void voronoi(float3 p, NodeDistanceMetric distance_metric, float e, float da[4], float3 pa[4])
{
	/* returns distances in da and point coords in pa */
	int xx, yy, zz, xi, yi, zi;

	xi = (int)floorf(p.x);
	yi = (int)floorf(p.y);
	zi = (int)floorf(p.z);

	da[0] = 1e10f;
	da[1] = 1e10f;
	da[2] = 1e10f;
	da[3] = 1e10f;

	pa[0] = make_float3(0.0f, 0.0f, 0.0f);
	pa[1] = make_float3(0.0f, 0.0f, 0.0f);
	pa[2] = make_float3(0.0f, 0.0f, 0.0f);
	pa[3] = make_float3(0.0f, 0.0f, 0.0f);

	for(xx = xi-1; xx <= xi+1; xx++) {
		for(yy = yi-1; yy <= yi+1; yy++) {
			for(zz = zi-1; zz <= zi+1; zz++) {
				float3 ip = make_float3(xx, yy, zz);
				float3 vp = cellnoise_color(ip);
				float3 pd = p - (vp + ip);
				float d = voronoi_distance(distance_metric, pd, e);

				vp += make_float3(xx, yy, zz);

				if(d < da[0]) {
					da[3] = da[2];
					da[2] = da[1];
					da[1] = da[0];
					da[0] = d;

					pa[3] = pa[2];
					pa[2] = pa[1];
					pa[1] = pa[0];
					pa[0] = vp;
				}
				else if(d < da[1]) {
					da[3] = da[2];
					da[2] = da[1];
					da[1] = d;

					pa[3] = pa[2];
					pa[2] = pa[1];
					pa[1] = vp;
				}
				else if(d < da[2]) {
					da[3] = da[2];
					da[2] = d;

					pa[3] = pa[2];
					pa[2] = vp;
				}
				else if(d < da[3]) {
					da[3] = d;
					pa[3] = vp;
				}
			}
		}
	}
}

__device float voronoi_Fn(float3 p, int n)
{
	float da[4];
	float3 pa[4];

	voronoi(p, NODE_VORONOI_DISTANCE_SQUARED, 0, da, pa);

	return da[n];
}

__device float voronoi_FnFn(float3 p, int n1, int n2)
{
	float da[4];
	float3 pa[4];

	voronoi(p, NODE_VORONOI_DISTANCE_SQUARED, 0, da, pa);

	return da[n2] - da[n1];
}

__device float voronoi_F1(float3 p) { return voronoi_Fn(p, 0); }
__device float voronoi_F2(float3 p) { return voronoi_Fn(p, 1); }
__device float voronoi_F3(float3 p) { return voronoi_Fn(p, 2); }
__device float voronoi_F4(float3 p) { return voronoi_Fn(p, 3); }
__device float voronoi_F1F2(float3 p) { return voronoi_FnFn(p, 0, 1); }

__device float voronoi_Cr(float3 p)
{
	/* crackle type pattern, just a scale/clamp of F2-F1 */
	float t = 10.0f*voronoi_F1F2(p);
	return (t > 1.0f)? 1.0f: t;
}

__device float voronoi_F1S(float3 p) { return 2.0f*voronoi_F1(p) - 1.0f; }
__device float voronoi_F2S(float3 p) { return 2.0f*voronoi_F2(p) - 1.0f; }
__device float voronoi_F3S(float3 p) { return 2.0f*voronoi_F3(p) - 1.0f; }
__device float voronoi_F4S(float3 p) { return 2.0f*voronoi_F4(p) - 1.0f; }
__device float voronoi_F1F2S(float3 p) { return 2.0f*voronoi_F1F2(p) - 1.0f; }
__device float voronoi_CrS(float3 p) { return 2.0f*voronoi_Cr(p) - 1.0f; }

/* Noise Bases */

__device float noise_basis(float3 p, NodeNoiseBasis basis)
{
	/* Only Perlin enabled for now, others break CUDA compile by making kernel
	   too big, with compile using > 4GB, due to everything being inlined. */

#if 0
	if(basis == NODE_NOISE_PERLIN)
#endif
		return noise(p);
#if 0
	if(basis == NODE_NOISE_VORONOI_F1)
		return voronoi_F1S(p);
	if(basis == NODE_NOISE_VORONOI_F2)
		return voronoi_F2S(p);
	if(basis == NODE_NOISE_VORONOI_F3)
		return voronoi_F3S(p);
	if(basis == NODE_NOISE_VORONOI_F4)
		return voronoi_F4S(p);
	if(basis == NODE_NOISE_VORONOI_F2_F1)
		return voronoi_F1F2S(p);
	if(basis == NODE_NOISE_VORONOI_CRACKLE)
		return voronoi_CrS(p);
	if(basis == NODE_NOISE_CELL_NOISE)
		return cellnoise(p);
	
	return 0.0f;
#endif
}

/* Soft/Hard Noise */

__device float noise_basis_hard(float3 p, NodeNoiseBasis basis, int hard)
{
	float t = noise_basis(p, basis);
	return (hard)? fabsf(2.0f*t - 1.0f): t;
}

/* Waves */

__device float noise_wave(NodeWaveType wave, float a)
{
	if(wave == NODE_WAVE_SINE) {
    	return 0.5f + 0.5f*sin(a);
	}
	else if(wave == NODE_WAVE_SAW) {
		float b = 2*M_PI;
		int n = (int)(a / b);
		a -= n*b;
		if(a < 0) a += b;

		return a / b;
	}
	else if(wave == NODE_WAVE_TRI) {
		float b = 2*M_PI;
		float rmax = 1.0f;

		return rmax - 2.0f*fabsf(floorf((a*(1.0f/b))+0.5f) - (a*(1.0f/b)));
	}

	return 0.0f;
}

/* Turbulence */

__device float noise_turbulence(float3 p, NodeNoiseBasis basis, int octaves, int hard)
{
	float fscale = 1.0f;
	float amp = 1.0f;
	float sum = 0.0f;
	int i;

	for(i = 0; i <= octaves; i++) {
		float t = noise_basis(fscale*p, basis);

		if(hard)
			t = fabsf(2.0f*t - 1.0f);

		sum += t*amp;
		amp *= 0.5f;
		fscale *= 2.0f;
	}

	sum *= ((float)(1 << octaves)/(float)((1 << (octaves+1)) - 1));

	return sum;
}

CCL_NAMESPACE_END

