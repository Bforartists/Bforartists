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

__device_noinline float4 voronoi_Fn(float3 p, float e, int n1, int n2)
{
	float da[4];
	float3 pa[4];
	NodeDistanceMetric distance_metric = NODE_VORONOI_DISTANCE_SQUARED;

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
				float3 ip = make_float3((float)xx, (float)yy, (float)zz);
				float3 vp = cellnoise_color(ip);
				float3 pd = p - (vp + ip);
				float d = voronoi_distance(distance_metric, pd, e);

				vp += ip;

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

	float4 result = make_float4(pa[n1].x, pa[n1].y, pa[n1].z, da[n1]);

	if(n2 != -1)
		result = make_float4(pa[n2].x, pa[n2].y, pa[n2].z, da[n2]) - result;

	return result;
}

__device float voronoi_F1(float3 p) { return voronoi_Fn(p, 0.0f, 0, -1).w; }
__device float voronoi_F2(float3 p) { return voronoi_Fn(p, 0.0f, 1, -1).w; }
__device float voronoi_F3(float3 p) { return voronoi_Fn(p, 0.0f, 2, -1).w; }
__device float voronoi_F4(float3 p) { return voronoi_Fn(p, 0.0f, 3, -1).w; }
__device float voronoi_F1F2(float3 p) { return voronoi_Fn(p, 0.0f, 0, 1).w; }

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
	 * too big, with compile using > 4GB, due to everything being inlined. */

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

__device float noise_wave(NodeWaveBasis wave, float a)
{
	if(wave == NODE_WAVE_SINE) {
		return 0.5f + 0.5f * sinf(a);
	}
	else if(wave == NODE_WAVE_SAW) {
		float b = 2.0f*M_PI_F;
		int n = (int)(a / b);
		a -= n*b;
		if(a < 0.0f) a += b;

		return a / b;
	}
	else if(wave == NODE_WAVE_TRI) {
		float b = 2.0f*M_PI_F;
		float rmax = 1.0f;

		return rmax - 2.0f*fabsf(floorf((a*(1.0f/b))+0.5f) - (a*(1.0f/b)));
	}

	return 0.0f;
}

/* Turbulence */

__device_noinline float noise_turbulence(float3 p, NodeNoiseBasis basis, float octaves, int hard)
{
	float fscale = 1.0f;
	float amp = 1.0f;
	float sum = 0.0f;
	int i, n;

	octaves = clamp(octaves, 0.0f, 16.0f);
	n = (int)octaves;

	for(i = 0; i <= n; i++) {
		float t = noise_basis(fscale*p, basis);

		if(hard)
			t = fabsf(2.0f*t - 1.0f);

		sum += t*amp;
		amp *= 0.5f;
		fscale *= 2.0f;
	}

	float rmd = octaves - floorf(octaves);

	if(rmd != 0.0f) {
		float t = noise_basis(fscale*p, basis);

		if(hard)
			t = fabsf(2.0f*t - 1.0f);

		float sum2 = sum + t*amp;

		sum *= ((float)(1 << n)/(float)((1 << (n+1)) - 1));
		sum2 *= ((float)(1 << (n+1))/(float)((1 << (n+2)) - 1));

		return (1.0f - rmd)*sum + rmd*sum2;
	}
	else {
		sum *= ((float)(1 << n)/(float)((1 << (n+1)) - 1));
		return sum;
	}
}

CCL_NAMESPACE_END

