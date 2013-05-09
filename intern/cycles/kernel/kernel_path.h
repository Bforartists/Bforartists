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

#ifdef __OSL__
#include "osl_shader.h"
#endif

#include "kernel_differential.h"
#include "kernel_montecarlo.h"
#include "kernel_projection.h"
#include "kernel_object.h"
#include "kernel_triangle.h"
#include "kernel_curve.h"
#include "kernel_primitive.h"
#include "kernel_projection.h"
#include "kernel_random.h"
#include "kernel_bvh.h"
#include "kernel_accumulate.h"
#include "kernel_camera.h"
#include "kernel_shader.h"
#include "kernel_light.h"
#include "kernel_emission.h"
#include "kernel_passes.h"

#ifdef __SUBSURFACE__
#include "kernel_subsurface.h"
#endif

CCL_NAMESPACE_BEGIN

typedef struct PathState {
	uint flag;
	int bounce;

	int diffuse_bounce;
	int glossy_bounce;
	int transmission_bounce;
	int transparent_bounce;
} PathState;

__device_inline void path_state_init(PathState *state)
{
	state->flag = PATH_RAY_CAMERA|PATH_RAY_SINGULAR|PATH_RAY_MIS_SKIP;
	state->bounce = 0;
	state->diffuse_bounce = 0;
	state->glossy_bounce = 0;
	state->transmission_bounce = 0;
	state->transparent_bounce = 0;
}

__device_inline void path_state_next(KernelGlobals *kg, PathState *state, int label)
{
	/* ray through transparent keeps same flags from previous ray and is
	 * not counted as a regular bounce, transparent has separate max */
	if(label & LABEL_TRANSPARENT) {
		state->flag |= PATH_RAY_TRANSPARENT;
		state->transparent_bounce++;

		if(!kernel_data.integrator.transparent_shadows)
			state->flag |= PATH_RAY_MIS_SKIP;

		return;
	}

	state->bounce++;

	/* reflection/transmission */
	if(label & LABEL_REFLECT) {
		state->flag |= PATH_RAY_REFLECT;
		state->flag &= ~(PATH_RAY_TRANSMIT|PATH_RAY_CAMERA|PATH_RAY_TRANSPARENT);

		if(label & LABEL_DIFFUSE)
			state->diffuse_bounce++;
		else
			state->glossy_bounce++;
	}
	else {
		kernel_assert(label & LABEL_TRANSMIT);

		state->flag |= PATH_RAY_TRANSMIT;
		state->flag &= ~(PATH_RAY_REFLECT|PATH_RAY_CAMERA|PATH_RAY_TRANSPARENT);

		state->transmission_bounce++;
	}

	/* diffuse/glossy/singular */
	if(label & LABEL_DIFFUSE) {
		state->flag |= PATH_RAY_DIFFUSE;
		state->flag &= ~(PATH_RAY_GLOSSY|PATH_RAY_SINGULAR|PATH_RAY_MIS_SKIP);
	}
	else if(label & LABEL_GLOSSY) {
		state->flag |= PATH_RAY_GLOSSY;
		state->flag &= ~(PATH_RAY_DIFFUSE|PATH_RAY_SINGULAR|PATH_RAY_MIS_SKIP);
	}
	else {
		kernel_assert(label & LABEL_SINGULAR);

		state->flag |= PATH_RAY_GLOSSY|PATH_RAY_SINGULAR|PATH_RAY_MIS_SKIP;
		state->flag &= ~PATH_RAY_DIFFUSE;
	}
}

__device_inline uint path_state_ray_visibility(KernelGlobals *kg, PathState *state)
{
	uint flag = state->flag;

	/* for visibility, diffuse/glossy are for reflection only */
	if(flag & PATH_RAY_TRANSMIT)
		flag &= ~(PATH_RAY_DIFFUSE|PATH_RAY_GLOSSY);
	/* for camera visibility, use render layer flags */
	if(flag & PATH_RAY_CAMERA)
		flag |= kernel_data.integrator.layer_flag;

	return flag;
}

__device_inline float path_state_terminate_probability(KernelGlobals *kg, PathState *state, const float3 throughput)
{
	if(state->flag & PATH_RAY_TRANSPARENT) {
		/* transparent rays treated separately */
		if(state->transparent_bounce >= kernel_data.integrator.transparent_max_bounce)
			return 0.0f;
		else if(state->transparent_bounce <= kernel_data.integrator.transparent_min_bounce)
			return 1.0f;
	}
	else {
		/* other rays */
		if((state->bounce >= kernel_data.integrator.max_bounce) ||
		   (state->diffuse_bounce >= kernel_data.integrator.max_diffuse_bounce) ||
		   (state->glossy_bounce >= kernel_data.integrator.max_glossy_bounce) ||
		   (state->transmission_bounce >= kernel_data.integrator.max_transmission_bounce))
		{
			return 0.0f;
		}
		else if(state->bounce <= kernel_data.integrator.min_bounce) {
			return 1.0f;
		}
	}

	/* probalistic termination */
	return average(throughput); /* todo: try using max here */
}

__device_inline bool shadow_blocked(KernelGlobals *kg, PathState *state, Ray *ray, float3 *shadow)
{
	*shadow = make_float3(1.0f, 1.0f, 1.0f);

	if(ray->t == 0.0f)
		return false;
	
	Intersection isect;
#ifdef __HAIR__
	bool result = scene_intersect(kg, ray, PATH_RAY_SHADOW_OPAQUE, &isect, NULL, 0.0f, 0.0f);
#else
	bool result = scene_intersect(kg, ray, PATH_RAY_SHADOW_OPAQUE, &isect);
#endif

#ifdef __TRANSPARENT_SHADOWS__
	if(result && kernel_data.integrator.transparent_shadows) {
		/* transparent shadows work in such a way to try to minimize overhead
		 * in cases where we don't need them. after a regular shadow ray is
		 * cast we check if the hit primitive was potentially transparent, and
		 * only in that case start marching. this gives on extra ray cast for
		 * the cases were we do want transparency.
		 *
		 * also note that for this to work correct, multi close sampling must
		 * be used, since we don't pass a random number to shader_eval_surface */
		if(shader_transparent_shadow(kg, &isect)) {
			float3 throughput = make_float3(1.0f, 1.0f, 1.0f);
			float3 Pend = ray->P + ray->D*ray->t;
			int bounce = state->transparent_bounce;

			for(;;) {
				if(bounce >= kernel_data.integrator.transparent_max_bounce) {
					return true;
				}
				else if(bounce >= kernel_data.integrator.transparent_min_bounce) {
					/* todo: get random number somewhere for probabilistic terminate */
#if 0
					float probability = average(throughput);
					float terminate = 0.0f;

					if(terminate >= probability)
						return true;

					throughput /= probability;
#endif
				}

#ifdef __HAIR__
				if(!scene_intersect(kg, ray, PATH_RAY_SHADOW_TRANSPARENT, &isect, NULL, 0.0f, 0.0f)) {
#else
				if(!scene_intersect(kg, ray, PATH_RAY_SHADOW_TRANSPARENT, &isect)) {
#endif
					*shadow *= throughput;
					return false;
				}

				if(!shader_transparent_shadow(kg, &isect))
					return true;

				ShaderData sd;
				shader_setup_from_ray(kg, &sd, &isect, ray);
				shader_eval_surface(kg, &sd, 0.0f, PATH_RAY_SHADOW, SHADER_CONTEXT_SHADOW);

				throughput *= shader_bsdf_transparency(kg, &sd);

				ray->P = ray_offset(sd.P, -sd.Ng);
				if(ray->t != FLT_MAX)
					ray->D = normalize_len(Pend - ray->P, &ray->t);

				bounce++;
			}
		}
	}
#endif

	return result;
}

__device float4 kernel_path_progressive(KernelGlobals *kg, RNG *rng, int sample, Ray ray, __global float *buffer)
{
	/* initialize */
	PathRadiance L;
	float3 throughput = make_float3(1.0f, 1.0f, 1.0f);
	float L_transparent = 0.0f;

	path_radiance_init(&L, kernel_data.film.use_light_pass);

	float min_ray_pdf = FLT_MAX;
	float ray_pdf = 0.0f;
#ifdef __LAMP_MIS__
	float ray_t = 0.0f;
#endif
	PathState state;
	int rng_offset = PRNG_BASE_NUM;

	path_state_init(&state);

	/* path iteration */
	for(;; rng_offset += PRNG_BOUNCE_NUM) {
		/* intersect scene */
		Intersection isect;
		uint visibility = path_state_ray_visibility(kg, &state);

#ifdef __HAIR__
		float difl = 0.0f, extmax = 0.0f;
		uint lcg_state = 0;

		if(kernel_data.bvh.have_curves) {
			if((kernel_data.cam.resolution == 1) && (state.flag & PATH_RAY_CAMERA)) {	
				float3 pixdiff = ray.dD.dx + ray.dD.dy;
				/*pixdiff = pixdiff - dot(pixdiff, ray.D)*ray.D;*/
				difl = kernel_data.curve_kernel_data.minimum_width * len(pixdiff) * 0.5f;
			}

			extmax = kernel_data.curve_kernel_data.maximum_width;
			lcg_state = lcg_init(*rng + rng_offset + sample*0x51633e2d);
		}

		bool hit = scene_intersect(kg, &ray, visibility, &isect, &lcg_state, difl, extmax);
#else
		bool hit = scene_intersect(kg, &ray, visibility, &isect);
#endif

#ifdef __LAMP_MIS__
		if(kernel_data.integrator.use_lamp_mis && !(state.flag & PATH_RAY_CAMERA)) {
			/* ray starting from previous non-transparent bounce */
			Ray light_ray;

			light_ray.P = ray.P - ray_t*ray.D;
			ray_t += isect.t;
			light_ray.D = ray.D;
			light_ray.t = ray_t;
			light_ray.time = ray.time;
			light_ray.dD = ray.dD;
			light_ray.dP = ray.dP;

			/* intersect with lamp */
			float light_t = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT);
			float3 emission;

			if(indirect_lamp_emission(kg, &light_ray, state.flag, ray_pdf, light_t, &emission))
				path_radiance_accum_emission(&L, throughput, emission, state.bounce);
		}
#endif

		if(!hit) {
			/* eval background shader if nothing hit */
			if(kernel_data.background.transparent && (state.flag & PATH_RAY_CAMERA)) {
				L_transparent += average(throughput);

#ifdef __PASSES__
				if(!(kernel_data.film.pass_flag & PASS_BACKGROUND))
#endif
					break;
			}

#ifdef __BACKGROUND__
			/* sample background shader */
			float3 L_background = indirect_background(kg, &ray, state.flag, ray_pdf);
			path_radiance_accum_background(&L, throughput, L_background, state.bounce);
#endif

			break;
		}

		/* setup shading */
		ShaderData sd;
		shader_setup_from_ray(kg, &sd, &isect, &ray);
		float rbsdf = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF);
		shader_eval_surface(kg, &sd, rbsdf, state.flag, SHADER_CONTEXT_MAIN);

		kernel_write_data_passes(kg, buffer, &L, &sd, sample, state.flag, throughput);

		/* blurring of bsdf after bounces, for rays that have a small likelihood
		 * of following this particular path (diffuse, rough glossy) */
		if(kernel_data.integrator.filter_glossy != FLT_MAX) {
			float blur_pdf = kernel_data.integrator.filter_glossy*min_ray_pdf;

			if(blur_pdf < 1.0f) {
				float blur_roughness = sqrtf(1.0f - blur_pdf)*0.5f;
				shader_bsdf_blur(kg, &sd, blur_roughness);
			}
		}

		/* holdout */
#ifdef __HOLDOUT__
		if((sd.flag & (SD_HOLDOUT|SD_HOLDOUT_MASK)) && (state.flag & PATH_RAY_CAMERA)) {
			if(kernel_data.background.transparent) {
				float3 holdout_weight;
				
				if(sd.flag & SD_HOLDOUT_MASK)
					holdout_weight = make_float3(1.0f, 1.0f, 1.0f);
				else
					holdout_weight = shader_holdout_eval(kg, &sd);

				/* any throughput is ok, should all be identical here */
				L_transparent += average(holdout_weight*throughput);
			}

			if(sd.flag & SD_HOLDOUT_MASK)
				break;
		}
#endif

#ifdef __EMISSION__
		/* emission */
		if(sd.flag & SD_EMISSION) {
			/* todo: is isect.t wrong here for transparent surfaces? */
			float3 emission = indirect_primitive_emission(kg, &sd, isect.t, state.flag, ray_pdf);
			path_radiance_accum_emission(&L, throughput, emission, state.bounce);
		}
#endif

		/* path termination. this is a strange place to put the termination, it's
		 * mainly due to the mixed in MIS that we use. gives too many unneeded
		 * shader evaluations, only need emission if we are going to terminate */
		float probability = path_state_terminate_probability(kg, &state, throughput);
		float terminate = path_rng(kg, rng, sample, rng_offset + PRNG_TERMINATE);

		if(terminate >= probability)
			break;

		throughput /= probability;

#ifdef __SUBSURFACE__
		/* bssrdf scatter to a different location on the same object, replacing
		 * the closures with a diffuse BSDF */
		if(sd.flag & SD_BSSRDF) {
			float bssrdf_probability;
			ShaderClosure *sc = subsurface_scatter_pick_closure(kg, &sd, &bssrdf_probability);

			/* modify throughput for picking bssrdf or bsdf */
			throughput *= bssrdf_probability;

			/* do bssrdf scatter step if we picked a bssrdf closure */
			if(sc) {
				uint lcg_state = lcg_init(*rng + rng_offset + sample*0x68bc21eb);
				subsurface_scatter_step(kg, &sd, state.flag, sc, &lcg_state, false);
			}
		}
#endif

#ifdef __AO__
		/* ambient occlusion */
		if(kernel_data.integrator.use_ambient_occlusion || (sd.flag & SD_AO)) {
			/* todo: solve correlation */
			float bsdf_u = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_U);
			float bsdf_v = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_V);

			float ao_factor = kernel_data.background.ao_factor;
			float3 ao_N;
			float3 ao_bsdf = shader_bsdf_ao(kg, &sd, ao_factor, &ao_N);
			float3 ao_D;
			float ao_pdf;

			sample_cos_hemisphere(ao_N, bsdf_u, bsdf_v, &ao_D, &ao_pdf);

			if(dot(sd.Ng, ao_D) > 0.0f && ao_pdf != 0.0f) {
				Ray light_ray;
				float3 ao_shadow;

				light_ray.P = ray_offset(sd.P, sd.Ng);
				light_ray.D = ao_D;
				light_ray.t = kernel_data.background.ao_distance;
#ifdef __OBJECT_MOTION__
				light_ray.time = sd.time;
#endif
				light_ray.dP = sd.dP;
				light_ray.dD = differential3_zero();

				if(!shadow_blocked(kg, &state, &light_ray, &ao_shadow))
					path_radiance_accum_ao(&L, throughput, ao_bsdf, ao_shadow, state.bounce);
			}
		}
#endif

#ifdef __EMISSION__
		if(kernel_data.integrator.use_direct_light) {
			/* sample illumination from lights to find path contribution */
			if(sd.flag & SD_BSDF_HAS_EVAL) {
				float light_t = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT);
				float light_o = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT_F);
				float light_u = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT_U);
				float light_v = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT_V);

				Ray light_ray;
				BsdfEval L_light;
				bool is_lamp;

#ifdef __OBJECT_MOTION__
				light_ray.time = sd.time;
#endif

				if(direct_emission(kg, &sd, -1, light_t, light_o, light_u, light_v, &light_ray, &L_light, &is_lamp)) {
					/* trace shadow ray */
					float3 shadow;

					if(!shadow_blocked(kg, &state, &light_ray, &shadow)) {
						/* accumulate */
						path_radiance_accum_light(&L, throughput, &L_light, shadow, 1.0f, state.bounce, is_lamp);
					}
				}
			}
		}
#endif

		/* no BSDF? we can stop here */
		if(!(sd.flag & SD_BSDF))
			break;

		/* sample BSDF */
		float bsdf_pdf;
		BsdfEval bsdf_eval;
		float3 bsdf_omega_in;
		differential3 bsdf_domega_in;
		float bsdf_u = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_U);
		float bsdf_v = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_V);
		int label;

		label = shader_bsdf_sample(kg, &sd, bsdf_u, bsdf_v, &bsdf_eval,
			&bsdf_omega_in, &bsdf_domega_in, &bsdf_pdf);

		if(bsdf_pdf == 0.0f || bsdf_eval_is_zero(&bsdf_eval))
			break;

		/* modify throughput */
		path_radiance_bsdf_bounce(&L, &throughput, &bsdf_eval, bsdf_pdf, state.bounce, label);

		/* set labels */
		if(!(label & LABEL_TRANSPARENT)) {
			ray_pdf = bsdf_pdf;
#ifdef __LAMP_MIS__
			ray_t = 0.0f;
#endif
			min_ray_pdf = fminf(bsdf_pdf, min_ray_pdf);
		}

		/* update path state */
		path_state_next(kg, &state, label);

		/* setup ray */
		ray.P = ray_offset(sd.P, (label & LABEL_TRANSMIT)? -sd.Ng: sd.Ng);
		ray.D = bsdf_omega_in;

		if(state.bounce == 0)
			ray.t -= sd.ray_length; /* clipping works through transparent */
		else
			ray.t = FLT_MAX;

#ifdef __RAY_DIFFERENTIALS__
		ray.dP = sd.dP;
		ray.dD = bsdf_domega_in;
#endif
	}

	float3 L_sum = path_radiance_sum(kg, &L);

#ifdef __CLAMP_SAMPLE__
	path_radiance_clamp(&L, &L_sum, kernel_data.integrator.sample_clamp);
#endif

	kernel_write_light_passes(kg, buffer, &L, sample);

	return make_float4(L_sum.x, L_sum.y, L_sum.z, 1.0f - L_transparent);
}

#ifdef __NON_PROGRESSIVE__

__device void kernel_path_indirect(KernelGlobals *kg, RNG *rng, int sample, Ray ray, __global float *buffer,
	float3 throughput, float num_samples_adjust,
	float min_ray_pdf, float ray_pdf, PathState state, int rng_offset, PathRadiance *L)
{
#ifdef __LAMP_MIS__
	float ray_t = 0.0f;
#endif

	/* path iteration */
	for(;; rng_offset += PRNG_BOUNCE_NUM) {
		/* intersect scene */
		Intersection isect;
		uint visibility = path_state_ray_visibility(kg, &state);
#ifdef __HAIR__
		bool hit = scene_intersect(kg, &ray, visibility, &isect, NULL, 0.0f, 0.0f);
#else
		bool hit = scene_intersect(kg, &ray, visibility, &isect);
#endif

#ifdef __LAMP_MIS__
		if(kernel_data.integrator.use_lamp_mis && !(state.flag & PATH_RAY_CAMERA)) {
			/* ray starting from previous non-transparent bounce */
			Ray light_ray;

			light_ray.P = ray.P - ray_t*ray.D;
			ray_t += isect.t;
			light_ray.D = ray.D;
			light_ray.t = ray_t;
			light_ray.time = ray.time;
			light_ray.dD = ray.dD;
			light_ray.dP = ray.dP;

			/* intersect with lamp */
			float light_t = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT);
			float3 emission;

			if(indirect_lamp_emission(kg, &light_ray, state.flag, ray_pdf, light_t, &emission))
				path_radiance_accum_emission(L, throughput, emission, state.bounce);
		}
#endif

		if(!hit) {
#ifdef __BACKGROUND__
			/* sample background shader */
			float3 L_background = indirect_background(kg, &ray, state.flag, ray_pdf);
			path_radiance_accum_background(L, throughput, L_background, state.bounce);
#endif

			break;
		}

		/* setup shading */
		ShaderData sd;
		shader_setup_from_ray(kg, &sd, &isect, &ray);
		float rbsdf = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF);
		shader_eval_surface(kg, &sd, rbsdf, state.flag, SHADER_CONTEXT_INDIRECT);
		shader_merge_closures(kg, &sd);

		/* blurring of bsdf after bounces, for rays that have a small likelihood
		 * of following this particular path (diffuse, rough glossy) */
		if(kernel_data.integrator.filter_glossy != FLT_MAX) {
			float blur_pdf = kernel_data.integrator.filter_glossy*min_ray_pdf;

			if(blur_pdf < 1.0f) {
				float blur_roughness = sqrtf(1.0f - blur_pdf)*0.5f;
				shader_bsdf_blur(kg, &sd, blur_roughness);
			}
		}

#ifdef __EMISSION__
		/* emission */
		if(sd.flag & SD_EMISSION) {
			float3 emission = indirect_primitive_emission(kg, &sd, isect.t, state.flag, ray_pdf);
			path_radiance_accum_emission(L, throughput, emission, state.bounce);
		}
#endif

		/* path termination. this is a strange place to put the termination, it's
		 * mainly due to the mixed in MIS that we use. gives too many unneeded
		 * shader evaluations, only need emission if we are going to terminate */
		float probability = path_state_terminate_probability(kg, &state, throughput*num_samples_adjust);
		float terminate = path_rng(kg, rng, sample, rng_offset + PRNG_TERMINATE);

		if(terminate >= probability)
			break;

		throughput /= probability;

#ifdef __SUBSURFACE__
		/* bssrdf scatter to a different location on the same object, replacing
		 * the closures with a diffuse BSDF */
		if(sd.flag & SD_BSSRDF) {
			float bssrdf_probability;
			ShaderClosure *sc = subsurface_scatter_pick_closure(kg, &sd, &bssrdf_probability);

			/* modify throughput for picking bssrdf or bsdf */
			throughput *= bssrdf_probability;

			/* do bssrdf scatter step if we picked a bssrdf closure */
			if(sc) {
				uint lcg_state = lcg_init(*rng + rng_offset + sample*0x68bc21eb);
				subsurface_scatter_step(kg, &sd, state.flag, sc, &lcg_state, false);
			}
		}
#endif

#ifdef __AO__
		/* ambient occlusion */
		if(kernel_data.integrator.use_ambient_occlusion || (sd.flag & SD_AO)) {
			/* todo: solve correlation */
			float bsdf_u = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_U);
			float bsdf_v = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_V);

			float ao_factor = kernel_data.background.ao_factor;
			float3 ao_N;
			float3 ao_bsdf = shader_bsdf_ao(kg, &sd, ao_factor, &ao_N);
			float3 ao_D;
			float ao_pdf;

			sample_cos_hemisphere(ao_N, bsdf_u, bsdf_v, &ao_D, &ao_pdf);

			if(dot(sd.Ng, ao_D) > 0.0f && ao_pdf != 0.0f) {
				Ray light_ray;
				float3 ao_shadow;

				light_ray.P = ray_offset(sd.P, sd.Ng);
				light_ray.D = ao_D;
				light_ray.t = kernel_data.background.ao_distance;
#ifdef __OBJECT_MOTION__
				light_ray.time = sd.time;
#endif
				light_ray.dP = sd.dP;
				light_ray.dD = differential3_zero();

				if(!shadow_blocked(kg, &state, &light_ray, &ao_shadow))
					path_radiance_accum_ao(L, throughput, ao_bsdf, ao_shadow, state.bounce);
			}
		}
#endif

#ifdef __EMISSION__
		if(kernel_data.integrator.use_direct_light) {
			/* sample illumination from lights to find path contribution */
			if(sd.flag & SD_BSDF_HAS_EVAL) {
				float light_t = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT);
				float light_o = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT_F);
				float light_u = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT_U);
				float light_v = path_rng(kg, rng, sample, rng_offset + PRNG_LIGHT_V);

				Ray light_ray;
				BsdfEval L_light;
				bool is_lamp;

#ifdef __OBJECT_MOTION__
				light_ray.time = sd.time;
#endif

				/* sample random light */
				if(direct_emission(kg, &sd, -1, light_t, light_o, light_u, light_v, &light_ray, &L_light, &is_lamp)) {
					/* trace shadow ray */
					float3 shadow;

					if(!shadow_blocked(kg, &state, &light_ray, &shadow)) {
						/* accumulate */
						path_radiance_accum_light(L, throughput, &L_light, shadow, 1.0f, state.bounce, is_lamp);
					}
				}
			}
		}
#endif

		/* no BSDF? we can stop here */
		if(!(sd.flag & SD_BSDF))
			break;

		/* sample BSDF */
		float bsdf_pdf;
		BsdfEval bsdf_eval;
		float3 bsdf_omega_in;
		differential3 bsdf_domega_in;
		float bsdf_u = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_U);
		float bsdf_v = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF_V);
		int label;

		label = shader_bsdf_sample(kg, &sd, bsdf_u, bsdf_v, &bsdf_eval,
			&bsdf_omega_in, &bsdf_domega_in, &bsdf_pdf);

		if(bsdf_pdf == 0.0f || bsdf_eval_is_zero(&bsdf_eval))
			break;

		/* modify throughput */
		path_radiance_bsdf_bounce(L, &throughput, &bsdf_eval, bsdf_pdf, state.bounce, label);

		/* set labels */
		if(!(label & LABEL_TRANSPARENT)) {
			ray_pdf = bsdf_pdf;
#ifdef __LAMP_MIS__
			ray_t = 0.0f;
#endif
			min_ray_pdf = fminf(bsdf_pdf, min_ray_pdf);
		}

		/* update path state */
		path_state_next(kg, &state, label);

		/* setup ray */
		ray.P = ray_offset(sd.P, (label & LABEL_TRANSMIT)? -sd.Ng: sd.Ng);
		ray.D = bsdf_omega_in;
		ray.t = FLT_MAX;
#ifdef __RAY_DIFFERENTIALS__
		ray.dP = sd.dP;
		ray.dD = bsdf_domega_in;
#endif
	}
}

__device_noinline void kernel_path_non_progressive_lighting(KernelGlobals *kg, RNG *rng, int sample,
	ShaderData *sd, float3 throughput, float num_samples_adjust,
	float min_ray_pdf, float ray_pdf, PathState state,
	int rng_offset, PathRadiance *L, __global float *buffer)
{
#ifdef __AO__
	/* ambient occlusion */
	if(kernel_data.integrator.use_ambient_occlusion || (sd->flag & SD_AO)) {
		int num_samples = ceil(kernel_data.integrator.ao_samples*num_samples_adjust);
		float num_samples_inv = num_samples_adjust/num_samples;
		float ao_factor = kernel_data.background.ao_factor;
		float3 ao_N;
		float3 ao_bsdf = shader_bsdf_ao(kg, sd, ao_factor, &ao_N);

		for(int j = 0; j < num_samples; j++) {
			/* todo: solve correlation */
			float bsdf_u = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_BSDF_U);
			float bsdf_v = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_BSDF_V);

			float3 ao_D;
			float ao_pdf;

			sample_cos_hemisphere(ao_N, bsdf_u, bsdf_v, &ao_D, &ao_pdf);

			if(dot(sd->Ng, ao_D) > 0.0f && ao_pdf != 0.0f) {
				Ray light_ray;
				float3 ao_shadow;

				light_ray.P = ray_offset(sd->P, sd->Ng);
				light_ray.D = ao_D;
				light_ray.t = kernel_data.background.ao_distance;
#ifdef __OBJECT_MOTION__
				light_ray.time = sd->time;
#endif
				light_ray.dP = sd->dP;
				light_ray.dD = differential3_zero();

				if(!shadow_blocked(kg, &state, &light_ray, &ao_shadow))
					path_radiance_accum_ao(L, throughput*num_samples_inv, ao_bsdf, ao_shadow, state.bounce);
			}
		}
	}
#endif


#ifdef __EMISSION__
	/* sample illumination from lights to find path contribution */
	if(sd->flag & SD_BSDF_HAS_EVAL) {
		Ray light_ray;
		BsdfEval L_light;
		bool is_lamp;

#ifdef __OBJECT_MOTION__
		light_ray.time = sd->time;
#endif

		/* lamp sampling */
		for(int i = 0; i < kernel_data.integrator.num_all_lights; i++) {
			int num_samples = ceil(num_samples_adjust*light_select_num_samples(kg, i));
			float num_samples_inv = num_samples_adjust/(num_samples*kernel_data.integrator.num_all_lights);

			if(kernel_data.integrator.pdf_triangles != 0.0f)
				num_samples_inv *= 0.5f;

			for(int j = 0; j < num_samples; j++) {
				float light_u = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_LIGHT_U);
				float light_v = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_LIGHT_V);

				if(direct_emission(kg, sd, i, 0.0f, 0.0f, light_u, light_v, &light_ray, &L_light, &is_lamp)) {
					/* trace shadow ray */
					float3 shadow;

					if(!shadow_blocked(kg, &state, &light_ray, &shadow)) {
						/* accumulate */
						path_radiance_accum_light(L, throughput*num_samples_inv, &L_light, shadow, num_samples_inv, state.bounce, is_lamp);
					}
				}
			}
		}

		/* mesh light sampling */
		if(kernel_data.integrator.pdf_triangles != 0.0f) {
			int num_samples = ceil(num_samples_adjust*kernel_data.integrator.mesh_light_samples);
			float num_samples_inv = num_samples_adjust/num_samples;

			if(kernel_data.integrator.num_all_lights)
				num_samples_inv *= 0.5f;

			for(int j = 0; j < num_samples; j++) {
				float light_t = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_LIGHT);
				float light_u = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_LIGHT_U);
				float light_v = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_LIGHT_V);

				/* only sample triangle lights */
				if(kernel_data.integrator.num_all_lights)
					light_t = 0.5f*light_t;

				if(direct_emission(kg, sd, -1, light_t, 0.0f, light_u, light_v, &light_ray, &L_light, &is_lamp)) {
					/* trace shadow ray */
					float3 shadow;

					if(!shadow_blocked(kg, &state, &light_ray, &shadow)) {
						/* accumulate */
						path_radiance_accum_light(L, throughput*num_samples_inv, &L_light, shadow, num_samples_inv, state.bounce, is_lamp);
					}
				}
			}
		}
	}
#endif

	for(int i = 0; i< sd->num_closure; i++) {
		const ShaderClosure *sc = &sd->closure[i];

		if(!CLOSURE_IS_BSDF(sc->type))
			continue;
		/* transparency is not handled here, but in outer loop */
		if(sc->type == CLOSURE_BSDF_TRANSPARENT_ID)
			continue;

		int num_samples;

		if(CLOSURE_IS_BSDF_DIFFUSE(sc->type))
			num_samples = kernel_data.integrator.diffuse_samples;
		else if(CLOSURE_IS_BSDF_GLOSSY(sc->type))
			num_samples = kernel_data.integrator.glossy_samples;
		else
			num_samples = kernel_data.integrator.transmission_samples;

		num_samples = ceil(num_samples_adjust*num_samples);

		float num_samples_inv = num_samples_adjust/num_samples;

		for(int j = 0; j < num_samples; j++) {
			/* sample BSDF */
			float bsdf_pdf;
			BsdfEval bsdf_eval;
			float3 bsdf_omega_in;
			differential3 bsdf_domega_in;
			float bsdf_u = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_BSDF_U);
			float bsdf_v = path_rng(kg, rng, sample*num_samples + j, rng_offset + PRNG_BSDF_V);
			int label;

			label = shader_bsdf_sample_closure(kg, sd, sc, bsdf_u, bsdf_v, &bsdf_eval,
				&bsdf_omega_in, &bsdf_domega_in, &bsdf_pdf);

			if(bsdf_pdf == 0.0f || bsdf_eval_is_zero(&bsdf_eval))
				continue;

			/* modify throughput */
			float3 tp = throughput;
			path_radiance_bsdf_bounce(L, &tp, &bsdf_eval, bsdf_pdf, state.bounce, label);

			/* set labels */
			float min_ray_pdf = FLT_MAX;

			if(!(label & LABEL_TRANSPARENT))
				min_ray_pdf = fminf(bsdf_pdf, min_ray_pdf);

			/* modify path state */
			PathState ps = state;
			path_state_next(kg, &ps, label);

			/* setup ray */
			Ray bsdf_ray;

			bsdf_ray.P = ray_offset(sd->P, (label & LABEL_TRANSMIT)? -sd->Ng: sd->Ng);
			bsdf_ray.D = bsdf_omega_in;
			bsdf_ray.t = FLT_MAX;
#ifdef __RAY_DIFFERENTIALS__
			bsdf_ray.dP = sd->dP;
			bsdf_ray.dD = bsdf_domega_in;
#endif
#ifdef __OBJECT_MOTION__
			bsdf_ray.time = sd->time;
#endif

			kernel_path_indirect(kg, rng, sample*num_samples + j, bsdf_ray, buffer,
				tp*num_samples_inv, num_samples,
				min_ray_pdf, bsdf_pdf, ps, rng_offset+PRNG_BOUNCE_NUM, L);

			/* for render passes, sum and reset indirect light pass variables
			 * for the next samples */
			path_radiance_sum_indirect(L);
			path_radiance_reset_indirect(L);
		}
	}
}

__device float4 kernel_path_non_progressive(KernelGlobals *kg, RNG *rng, int sample, Ray ray, __global float *buffer)
{
	/* initialize */
	PathRadiance L;
	float3 throughput = make_float3(1.0f, 1.0f, 1.0f);
	float L_transparent = 0.0f;

	path_radiance_init(&L, kernel_data.film.use_light_pass);

	float ray_pdf = 0.0f;
	PathState state;
	int rng_offset = PRNG_BASE_NUM;

	path_state_init(&state);

	for(;; rng_offset += PRNG_BOUNCE_NUM) {
		/* intersect scene */
		Intersection isect;
		uint visibility = path_state_ray_visibility(kg, &state);

#ifdef __HAIR__
		float difl = 0.0f, extmax = 0.0f;
		uint lcg_state = 0;

		if(kernel_data.bvh.have_curves) {
			if((kernel_data.cam.resolution == 1) && (state.flag & PATH_RAY_CAMERA)) {	
				float3 pixdiff = ray.dD.dx + ray.dD.dy;
				/*pixdiff = pixdiff - dot(pixdiff, ray.D)*ray.D;*/
				difl = kernel_data.curve_kernel_data.minimum_width * len(pixdiff) * 0.5f;
			}

			extmax = kernel_data.curve_kernel_data.maximum_width;
			lcg_state = lcg_init(*rng + rng_offset + sample*0x51633e2d);
		}

		if(!scene_intersect(kg, &ray, visibility, &isect, &lcg_state, difl, extmax)) {
#else
		if(!scene_intersect(kg, &ray, visibility, &isect)) {
#endif
			/* eval background shader if nothing hit */
			if(kernel_data.background.transparent) {
				L_transparent += average(throughput);

#ifdef __PASSES__
				if(!(kernel_data.film.pass_flag & PASS_BACKGROUND))
#endif
					break;
			}

#ifdef __BACKGROUND__
			/* sample background shader */
			float3 L_background = indirect_background(kg, &ray, state.flag, ray_pdf);
			path_radiance_accum_background(&L, throughput, L_background, state.bounce);
#endif

			break;
		}

		/* setup shading */
		ShaderData sd;
		shader_setup_from_ray(kg, &sd, &isect, &ray);
		float rbsdf = path_rng(kg, rng, sample, rng_offset + PRNG_BSDF);
		shader_eval_surface(kg, &sd, rbsdf, state.flag, SHADER_CONTEXT_MAIN);
		shader_merge_closures(kg, &sd);

		kernel_write_data_passes(kg, buffer, &L, &sd, sample, state.flag, throughput);

		/* holdout */
#ifdef __HOLDOUT__
		if((sd.flag & (SD_HOLDOUT|SD_HOLDOUT_MASK))) {
			if(kernel_data.background.transparent) {
				float3 holdout_weight;
				
				if(sd.flag & SD_HOLDOUT_MASK)
					holdout_weight = make_float3(1.0f, 1.0f, 1.0f);
				else
					holdout_weight = shader_holdout_eval(kg, &sd);

				/* any throughput is ok, should all be identical here */
				L_transparent += average(holdout_weight*throughput);
			}

			if(sd.flag & SD_HOLDOUT_MASK)
				break;
		}
#endif

#ifdef __EMISSION__
		/* emission */
		if(sd.flag & SD_EMISSION) {
			float3 emission = indirect_primitive_emission(kg, &sd, isect.t, state.flag, ray_pdf);
			path_radiance_accum_emission(&L, throughput, emission, state.bounce);
		}
#endif

		/* transparency termination */
		if(state.flag & PATH_RAY_TRANSPARENT) {
			/* path termination. this is a strange place to put the termination, it's
			 * mainly due to the mixed in MIS that we use. gives too many unneeded
			 * shader evaluations, only need emission if we are going to terminate */
			float probability = path_state_terminate_probability(kg, &state, throughput);
			float terminate = path_rng(kg, rng, sample, rng_offset + PRNG_TERMINATE);

			if(terminate >= probability)
				break;

			throughput /= probability;
		}

#ifdef __SUBSURFACE__
		/* bssrdf scatter to a different location on the same object */
		if(sd.flag & SD_BSSRDF) {
			for(int i = 0; i< sd.num_closure; i++) {
				ShaderClosure *sc = &sd.closure[i];

				if(!CLOSURE_IS_BSSRDF(sc->type))
					continue;

				/* set up random number generator */
				uint lcg_state = lcg_init(*rng + rng_offset + sample*0x68bc21eb);
				int num_samples = kernel_data.integrator.subsurface_samples;
				float num_samples_inv = 1.0f/num_samples;

				/* do subsurface scatter step with copy of shader data, this will
				 * replace the BSSRDF with a diffuse BSDF closure */
				for(int j = 0; j < num_samples; j++) {
					ShaderData bssrdf_sd = sd;
					subsurface_scatter_step(kg, &bssrdf_sd, state.flag, sc, &lcg_state, true);

					/* compute lighting with the BSDF closure */
					kernel_path_non_progressive_lighting(kg, rng, sample*num_samples + j,
						&bssrdf_sd, throughput, num_samples_inv,
						ray_pdf, ray_pdf, state, rng_offset, &L, buffer);
				}
			}
		}
#endif

		/* lighting */
		kernel_path_non_progressive_lighting(kg, rng, sample, &sd, throughput,
			1.0f, ray_pdf, ray_pdf, state, rng_offset, &L, buffer);

		/* continue in case of transparency */
		throughput *= shader_bsdf_transparency(kg, &sd);

		if(is_zero(throughput))
			break;

		path_state_next(kg, &state, LABEL_TRANSPARENT);
		ray.P = ray_offset(sd.P, -sd.Ng);
		ray.t -= sd.ray_length; /* clipping works through transparent */
	}

	float3 L_sum = path_radiance_sum(kg, &L);

#ifdef __CLAMP_SAMPLE__
	path_radiance_clamp(&L, &L_sum, kernel_data.integrator.sample_clamp);
#endif

	kernel_write_light_passes(kg, buffer, &L, sample);

	return make_float4(L_sum.x, L_sum.y, L_sum.z, 1.0f - L_transparent);
}

#endif

__device void kernel_path_trace(KernelGlobals *kg,
	__global float *buffer, __global uint *rng_state,
	int sample, int x, int y, int offset, int stride)
{
	/* buffer offset */
	int index = offset + x + y*stride;
	int pass_stride = kernel_data.film.pass_stride;

	rng_state += index;
	buffer += index*pass_stride;

	/* initialize random numbers */
	RNG rng;

	float filter_u;
	float filter_v;

	path_rng_init(kg, rng_state, sample, &rng, x, y, &filter_u, &filter_v);

	/* sample camera ray */
	Ray ray;

	float lens_u = path_rng(kg, &rng, sample, PRNG_LENS_U);
	float lens_v = path_rng(kg, &rng, sample, PRNG_LENS_V);

#ifdef __CAMERA_MOTION__
	float time = path_rng(kg, &rng, sample, PRNG_TIME);
#else
	float time = 0.0f;
#endif

	camera_sample(kg, x, y, filter_u, filter_v, lens_u, lens_v, time, &ray);

	/* integrate */
	float4 L;

	if (ray.t != 0.0f) {
#ifdef __NON_PROGRESSIVE__
		if(kernel_data.integrator.progressive)
#endif
			L = kernel_path_progressive(kg, &rng, sample, ray, buffer);
#ifdef __NON_PROGRESSIVE__
		else
			L = kernel_path_non_progressive(kg, &rng, sample, ray, buffer);
#endif
	}
	else
		L = make_float4(0.f, 0.f, 0.f, 0.f);

	/* accumulate result in output buffer */
	kernel_write_pass_float4(buffer, sample, L);

	path_rng_end(kg, rng_state, rng);
}

CCL_NAMESPACE_END

