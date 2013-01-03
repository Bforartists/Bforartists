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

#ifdef __HAIR__

/* curve attributes */

__device float curve_attribute_float(KernelGlobals *kg, const ShaderData *sd, AttributeElement elem, int offset, float *dx, float *dy)
{
	if(elem == ATTR_ELEMENT_CURVE_SEGMENT) {
#ifdef __RAY_DIFFERENTIALS__
		if(dx) *dx = 0.0f;
		if(dy) *dy = 0.0f;
#endif

		return kernel_tex_fetch(__attributes_float, offset + sd->curve_seg);
	}
	else if(elem == ATTR_ELEMENT_CURVE_KEY) {
		float4 segment = kernel_tex_fetch(__curve_segments, sd->curve_seg);

		float f0 = kernel_tex_fetch(__attributes_float, offset + __float_as_int(segment.x));
		float f1 = kernel_tex_fetch(__attributes_float, offset + __float_as_int(segment.y));

#ifdef __RAY_DIFFERENTIALS__
		if(dx) *dx = sd->du.dx*(f1 - f0);
		if(dy) *dy = 0.0f;
#endif

		return (1.0f - sd->u)*f0 + sd->u*f1;
	}
	else {
#ifdef __RAY_DIFFERENTIALS__
		if(dx) *dx = 0.0f;
		if(dy) *dy = 0.0f;
#endif

		return 0.0f;
	}
}

__device float3 curve_attribute_float3(KernelGlobals *kg, const ShaderData *sd, AttributeElement elem, int offset, float3 *dx, float3 *dy)
{
	if(elem == ATTR_ELEMENT_CURVE_SEGMENT) {
		/* idea: we can't derive any useful differentials here, but for tiled
		 * mipmap image caching it would be useful to avoid reading the highest
		 * detail level always. maybe a derivative based on the hair density
		 * could be computed somehow? */
#ifdef __RAY_DIFFERENTIALS__
		if(dx) *dx = make_float3(0.0f, 0.0f, 0.0f);
		if(dy) *dy = make_float3(0.0f, 0.0f, 0.0f);
#endif

		return float4_to_float3(kernel_tex_fetch(__attributes_float3, offset + sd->curve_seg));
	}
	else if(elem == ATTR_ELEMENT_CURVE_KEY) {
		float4 segment = kernel_tex_fetch(__curve_segments, sd->curve_seg);

		float3 f0 = float4_to_float3(kernel_tex_fetch(__attributes_float3, offset + __float_as_int(segment.x)));
		float3 f1 = float4_to_float3(kernel_tex_fetch(__attributes_float3, offset + __float_as_int(segment.y)));

#ifdef __RAY_DIFFERENTIALS__
		if(dx) *dx = sd->du.dx*(f1 - f0);
		if(dy) *dy = make_float3(0.0f, 0.0f, 0.0f);
#endif

		return (1.0f - sd->u)*f0 + sd->u*f1;
	}
	else {
#ifdef __RAY_DIFFERENTIALS__
		if(dx) *dx = make_float3(0.0f, 0.0f, 0.0f);
		if(dy) *dy = make_float3(0.0f, 0.0f, 0.0f);
#endif

		return make_float3(0.0f, 0.0f, 0.0f);
	}
}

/* hair info node functions */

__device float curve_thickness(KernelGlobals *kg, ShaderData *sd)
{
	int prim = sd->curve_seg;
	float u = sd->u;
	float r = 0.0f;

	if(prim != -1) {
		float4 v00 = kernel_tex_fetch(__curve_segments, prim);

		int v1 = __float_as_int(v00.x);
		int v2 = __float_as_int(v00.y);

		float4 P1 = kernel_tex_fetch(__curve_keys, v1);
		float4 P2 = kernel_tex_fetch(__curve_keys, v2);
		r = (P2.w - P1.w) * u + P1.w;
	}

	return r*2.0f;
}

__device float3 curve_tangent_normal(KernelGlobals *kg, ShaderData *sd)
{	
	float3 tgN = make_float3(0.0f,0.0f,0.0f);

	if(sd->curve_seg != ~0) {
		float normalmix = kernel_data.curve_kernel_data.normalmix;

		tgN = -(-sd->I - sd->dPdu * (dot(sd->dPdu,-sd->I) * normalmix / len_squared(sd->dPdu)));
		tgN = normalize(tgN);

		/* need to find suitable scaled gd for corrected normal */
#if 0
		if (kernel_data.curve_kernel_data.use_tangent_normal_correction)
			tgN = normalize(tgN - gd * sd->dPdu);
#endif
	}

	return tgN;
}

#endif

CCL_NAMESPACE_END

