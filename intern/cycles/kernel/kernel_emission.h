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

/* Direction Emission */

__device float3 direct_emissive_eval(KernelGlobals *kg, float rando,
	LightSample *ls, float u, float v, float3 I)
{
	/* setup shading at emitter */
	ShaderData sd;

	shader_setup_from_sample(kg, &sd, ls->P, ls->Ng, I, ls->shader, ls->object, ls->prim, u, v);
	ls->Ng = sd.Ng;

	/* no path flag, we're evaluating this for all closures. that's weak but
	   we'd have to do multiple evaluations otherwise */
	shader_eval_surface(kg, &sd, rando, 0);
	
	float3 eval;

	/* evaluate emissive closure */
	if(sd.flag & SD_EMISSION)
		eval = shader_emissive_eval(kg, &sd);
	else
		eval = make_float3(0.0f, 0.0f, 0.0f);

	shader_release(kg, &sd);

	return eval;
}

__device bool direct_emission(KernelGlobals *kg, ShaderData *sd, float randt, float rando,
	float randu, float randv, Ray *ray, float3 *eval)
{
	/* sample a position on a light */
	LightSample ls;

	light_sample(kg, randt, randu, randv, sd->P, &ls);

	/* compute incoming direction and distance */
	float t;
	float3 omega_in = normalize_len(ls.P - sd->P, &t);

	/* compute pdf */
	float pdf = light_pdf(kg, &ls, -omega_in, t);

	/* evaluate closure */
	*eval = direct_emissive_eval(kg, rando, &ls, randu, randv, -omega_in);

	if(is_zero(*eval) || pdf == 0.0f)
		return false;

	/* evaluate BSDF at shading point */
	float bsdf_pdf;
	float3 bsdf_eval = shader_bsdf_eval(kg, sd, omega_in, &bsdf_pdf);

	*eval *= bsdf_eval/pdf;

	if(is_zero(*eval))
		return false;

	if(ls.prim != ~0) {
		/* multiple importance sampling */
		float mis_weight = power_heuristic(pdf, bsdf_pdf);
		*eval *= mis_weight;
	}
	else {
		/* ensure point light works in Watts, this should be handled
		 * elsewhere but for now together with the diffuse emission
		 * closure it works out to the right value */
		*eval *= 0.25f;
	}

	/* setup ray */
	ray->P = ray_offset(sd->P, sd->Ng);
	ray->D = ray_offset(ls.P, ls.Ng) - ray->P;
	ray->D = normalize_len(ray->D, &ray->t);

	return true;
}

/* Indirect Emission */

__device float3 indirect_emission(KernelGlobals *kg, ShaderData *sd, float t, int path_flag, float bsdf_pdf)
{
	/* evaluate emissive closure */
	float3 L = shader_emissive_eval(kg, sd);

	if(!(path_flag & PATH_RAY_SINGULAR)) {
		/* multiple importance sampling */
		float pdf = triangle_light_pdf(kg, sd->Ng, sd->I, t);
		float mis_weight = power_heuristic(bsdf_pdf, pdf);

		return L*mis_weight;
	}

	return L;
}

CCL_NAMESPACE_END

