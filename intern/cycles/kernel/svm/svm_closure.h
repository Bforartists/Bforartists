/*
 * Copyright 2011-2013 Blender Foundation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License
 */

CCL_NAMESPACE_BEGIN

/* Closure Nodes */

__device void svm_node_glass_setup(ShaderData *sd, ShaderClosure *sc, int type, float eta, float roughness, bool refract)
{
	if(type == CLOSURE_BSDF_SHARP_GLASS_ID) {
		if(refract) {
			sc->data0 = eta;
			sc->data1 = 0.0f;
			sd->flag |= bsdf_refraction_setup(sc);
		}
		else
			sd->flag |= bsdf_reflection_setup(sc);
	}
	else if(type == CLOSURE_BSDF_MICROFACET_BECKMANN_GLASS_ID) {
		sc->data0 = roughness;
		sc->data1 = eta;

		if(refract)
			sd->flag |= bsdf_microfacet_beckmann_refraction_setup(sc);
		else
			sd->flag |= bsdf_microfacet_beckmann_setup(sc);
	}
	else {
		sc->data0 = roughness;
		sc->data1 = eta;

		if(refract)
			sd->flag |= bsdf_microfacet_ggx_refraction_setup(sc);
		else
			sd->flag |= bsdf_microfacet_ggx_setup(sc);
	}
}

__device_inline ShaderClosure *svm_node_closure_get_non_bsdf(ShaderData *sd, ClosureType type, float mix_weight)
{
#ifdef __MULTI_CLOSURE__
	ShaderClosure *sc = &sd->closure[sd->num_closure];

	if(sd->num_closure < MAX_CLOSURE) {
		sc->weight *= mix_weight;
		sc->type = type;
#ifdef __OSL__
		sc->prim = NULL;
#endif
		sd->num_closure++;
		return sc;
	}

	return NULL;
#else
	return &sd->closure;
#endif
}

__device_inline ShaderClosure *svm_node_closure_get_bsdf(ShaderData *sd, float mix_weight)
{
#ifdef __MULTI_CLOSURE__
	ShaderClosure *sc = &sd->closure[sd->num_closure];
	float3 weight = sc->weight * mix_weight;
	float sample_weight = fabsf(average(weight));

	if(sample_weight > 1e-5f && sd->num_closure < MAX_CLOSURE) {
		sc->weight = weight;
		sc->sample_weight = sample_weight;
		sd->num_closure++;
#ifdef __OSL__
		sc->prim = NULL;
#endif
		return sc;
	}

	return NULL;
#else
	return &sd->closure;
#endif
}

__device void svm_node_closure_bsdf(KernelGlobals *kg, ShaderData *sd, float *stack, uint4 node, float randb, int path_flag, int *offset)
{
	uint type, param1_offset, param2_offset;

#ifdef __MULTI_CLOSURE__
	uint mix_weight_offset;
	decode_node_uchar4(node.y, &type, &param1_offset, &param2_offset, &mix_weight_offset);
	float mix_weight = (stack_valid(mix_weight_offset)? stack_load_float(stack, mix_weight_offset): 1.0f);

	/* note we read this extra node before weight check, so offset is added */
	uint4 data_node = read_node(kg, offset);

	if(mix_weight == 0.0f)
		return;

	float3 N = stack_valid(data_node.x)? stack_load_float3(stack, data_node.x): sd->N; 
#else
	decode_node_uchar4(node.y, &type, &param1_offset, &param2_offset, NULL);
	float mix_weight = 1.0f;

	uint4 data_node = read_node(kg, offset);
	float3 N = stack_valid(data_node.x)? stack_load_float3(stack, data_node.x): sd->N; 
#endif

	float param1 = (stack_valid(param1_offset))? stack_load_float(stack, param1_offset): __uint_as_float(node.z);
	float param2 = (stack_valid(param2_offset))? stack_load_float(stack, param2_offset): __uint_as_float(node.w);

	switch(type) {
		case CLOSURE_BSDF_DIFFUSE_ID: {
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->N = N;

				float roughness = param1;

				if(roughness == 0.0f) {
					sc->data0 = 0.0f;
					sc->data1 = 0.0f;
					sd->flag |= bsdf_diffuse_setup(sc);
				}
				else {
					sc->data0 = roughness;
					sc->data1 = 0.0f;
					sd->flag |= bsdf_oren_nayar_setup(sc);
				}
			}
			break;
		}
		case CLOSURE_BSDF_TRANSLUCENT_ID: {
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->data0 = 0.0f;
				sc->data1 = 0.0f;
				sc->N = N;
				sd->flag |= bsdf_translucent_setup(sc);
			}
			break;
		}
		case CLOSURE_BSDF_TRANSPARENT_ID: {
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->data0 = 0.0f;
				sc->data1 = 0.0f;
				sc->N = N;
				sd->flag |= bsdf_transparent_setup(sc);
			}
			break;
		}
		case CLOSURE_BSDF_REFLECTION_ID:
		case CLOSURE_BSDF_MICROFACET_GGX_ID:
		case CLOSURE_BSDF_MICROFACET_BECKMANN_ID: {
#ifdef __CAUSTICS_TRICKS__
			if(kernel_data.integrator.no_caustics && (path_flag & PATH_RAY_DIFFUSE))
				break;
#endif
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->N = N;
				sc->data0 = param1;
				sc->data1 = 0.0f;

				/* setup bsdf */
				if(type == CLOSURE_BSDF_REFLECTION_ID)
					sd->flag |= bsdf_reflection_setup(sc);
				else if(type == CLOSURE_BSDF_MICROFACET_BECKMANN_ID)
					sd->flag |= bsdf_microfacet_beckmann_setup(sc);
				else
					sd->flag |= bsdf_microfacet_ggx_setup(sc);
			}

			break;
		}
		case CLOSURE_BSDF_REFRACTION_ID:
		case CLOSURE_BSDF_MICROFACET_GGX_REFRACTION_ID:
		case CLOSURE_BSDF_MICROFACET_BECKMANN_REFRACTION_ID: {
#ifdef __CAUSTICS_TRICKS__
			if(kernel_data.integrator.no_caustics && (path_flag & PATH_RAY_DIFFUSE))
				break;
#endif
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->N = N;
				sc->data0 = param1;

				float eta = fmaxf(param2, 1.0f + 1e-5f);
				sc->data1 = (sd->flag & SD_BACKFACING)? 1.0f/eta: eta;

				/* setup bsdf */
				if(type == CLOSURE_BSDF_REFRACTION_ID)
					sd->flag |= bsdf_refraction_setup(sc);
				else if(type == CLOSURE_BSDF_MICROFACET_BECKMANN_REFRACTION_ID)
					sd->flag |= bsdf_microfacet_beckmann_refraction_setup(sc);
				else
					sd->flag |= bsdf_microfacet_ggx_refraction_setup(sc);
			}

			break;
		}
		case CLOSURE_BSDF_SHARP_GLASS_ID:
		case CLOSURE_BSDF_MICROFACET_GGX_GLASS_ID:
		case CLOSURE_BSDF_MICROFACET_BECKMANN_GLASS_ID: {
#ifdef __CAUSTICS_TRICKS__
			if(kernel_data.integrator.no_caustics && (path_flag & PATH_RAY_DIFFUSE))
				break;
#endif
			/* index of refraction */
			float eta = fmaxf(param2, 1.0f + 1e-5f);
			eta = (sd->flag & SD_BACKFACING)? 1.0f/eta: eta;

			/* fresnel */
			float cosNO = dot(N, sd->I);
			float fresnel = fresnel_dielectric_cos(cosNO, eta);
			float roughness = param1;

#ifdef __MULTI_CLOSURE__
			/* reflection */
			ShaderClosure *sc = &sd->closure[sd->num_closure];
			float3 weight = sc->weight;
			float sample_weight = sc->sample_weight;

			sc = svm_node_closure_get_bsdf(sd, mix_weight*fresnel);

			if(sc) {
				sc->N = N;
				svm_node_glass_setup(sd, sc, type, eta, roughness, false);
			}

			/* refraction */
			sc = &sd->closure[sd->num_closure];
			sc->weight = weight;
			sc->sample_weight = sample_weight;

			sc = svm_node_closure_get_bsdf(sd, mix_weight*(1.0f - fresnel));

			if(sc) {
				sc->N = N;
				svm_node_glass_setup(sd, sc, type, eta, roughness, true);
			}
#else
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->N = N;
				bool refract = (randb > fresnel);
				svm_node_glass_setup(sd, sc, type, eta, roughness, refract);
			}
#endif

			break;
		}
		case CLOSURE_BSDF_WARD_ID: {
#ifdef __CAUSTICS_TRICKS__
			if(kernel_data.integrator.no_caustics && (path_flag & PATH_RAY_DIFFUSE))
				break;
#endif
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->N = N;

#ifdef __ANISOTROPIC__
				sc->T = stack_load_float3(stack, data_node.y);

				/* rotate tangent */
				float rotation = stack_load_float(stack, data_node.z);

				if(rotation != 0.0f)
					sc->T = rotate_around_axis(sc->T, sc->N, rotation * M_2PI_F);

				/* compute roughness */
				float roughness = param1;
				float anisotropy = clamp(param2, -0.99f, 0.99f);

				if(anisotropy < 0.0f) {
					sc->data0 = roughness/(1.0f + anisotropy);
					sc->data1 = roughness*(1.0f + anisotropy);
				}
				else {
					sc->data0 = roughness*(1.0f - anisotropy);
					sc->data1 = roughness/(1.0f - anisotropy);
				}

				sd->flag |= bsdf_ward_setup(sc);
#else
				sd->flag |= bsdf_diffuse_setup(sc);
#endif
			}
			break;
		}
		case CLOSURE_BSDF_ASHIKHMIN_VELVET_ID: {
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				sc->N = N;

				/* sigma */
				sc->data0 = clamp(param1, 0.0f, 1.0f);
				sc->data1 = 0.0f;
				sd->flag |= bsdf_ashikhmin_velvet_setup(sc);
			}
			break;
		}
		case CLOSURE_BSDF_DIFFUSE_TOON_ID:
		case CLOSURE_BSDF_GLOSSY_TOON_ID: {
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				/* Normal, Size and Smooth */
				sc->N = N;
				sc->data0 = param1;
				sc->data1 = param2;
				
				if (type == CLOSURE_BSDF_DIFFUSE_TOON_ID)
					sd->flag |= bsdf_diffuse_toon_setup(sc);
				else
					sd->flag |= bsdf_glossy_toon_setup(sc);
			}
			break;
		}
#ifdef __HAIR__
		case CLOSURE_BSDF_HAIR_REFLECTION_ID:
		case CLOSURE_BSDF_HAIR_TRANSMISSION_ID: {
			
			if(sd->flag & SD_BACKFACING && sd->segment != ~0) {
				ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);
				if(sc) {
					sc->weight = make_float3(1.0f,1.0f,1.0f);
					sc->N = N;
					sd->flag |= bsdf_transparent_setup(sc);
				}
			}
			else {
				ShaderClosure *sc = &sd->closure[sd->num_closure];
				sc = svm_node_closure_get_bsdf(sd, mix_weight);

				if(sc) {
					sc->N = N;
					sc->data0 = param1;
					sc->data1 = param2;
					sc->offset = -stack_load_float(stack, data_node.z);
					if(sd->segment == ~0) {
						sc->T = normalize(sd->dPdv);
						sc->offset = 0.0f;
					}
					else
						sc->T = sd->dPdu;
					if(type == CLOSURE_BSDF_HAIR_REFLECTION_ID) {
						sd->flag |= bsdf_hair_reflection_setup(sc);
					}
					else {
						sd->flag |= bsdf_hair_transmission_setup(sc);
					}
				}
			}

			break;
		}
#endif

#ifdef __SUBSURFACE__
		case CLOSURE_BSSRDF_CUBIC_ID:
		case CLOSURE_BSSRDF_GAUSSIAN_ID: {
			ShaderClosure *sc = &sd->closure[sd->num_closure];
			float3 weight = sc->weight * mix_weight;
			float sample_weight = fabsf(average(weight));
			
			/* disable in case of diffuse ancestor, can't see it well then and
			 * adds considerably noise due to probabilities of continuing path
			 * getting lower and lower */
			if(path_flag & PATH_RAY_DIFFUSE_ANCESTOR)
				param1 = 0.0f;

			if(sample_weight > 1e-5f && sd->num_closure+2 < MAX_CLOSURE) {
				/* radius * scale */
				float3 radius = stack_load_float3(stack, data_node.z)*param1;
				/* sharpness */
				float sharpness = stack_load_float(stack, data_node.w);
				/* texture color blur */
				float texture_blur = param2;

				/* create one closure per color channel */
				if(fabsf(weight.x) > 0.0f) {
					sc->weight = make_float3(weight.x, 0.0f, 0.0f);
					sc->sample_weight = sample_weight;
					sc->data0 = radius.x;
					sc->data1 = texture_blur;
					sc->T.x = sharpness;
#ifdef __OSL__
					sc->prim = NULL;
#endif
					sc->N = N;
					sd->flag |= bssrdf_setup(sc, (ClosureType)type);

					sd->num_closure++;
					sc++;
				}

				if(fabsf(weight.y) > 0.0f) {
					sc->weight = make_float3(0.0f, weight.y, 0.0f);
					sc->sample_weight = sample_weight;
					sc->data0 = radius.y;
					sc->data1 = texture_blur;
					sc->T.x = sharpness;
#ifdef __OSL__
					sc->prim = NULL;
#endif
					sc->N = N;
					sd->flag |= bssrdf_setup(sc, (ClosureType)type);

					sd->num_closure++;
					sc++;
				}

				if(fabsf(weight.z) > 0.0f) {
					sc->weight = make_float3(0.0f, 0.0f, weight.z);
					sc->sample_weight = sample_weight;
					sc->data0 = radius.z;
					sc->data1 = texture_blur;
					sc->T.x = sharpness;
#ifdef __OSL__
					sc->prim = NULL;
#endif
					sc->N = N;
					sd->flag |= bssrdf_setup(sc, (ClosureType)type);

					sd->num_closure++;
					sc++;
				}
			}

			break;
		}
#endif
		default:
			break;
	}
}

__device void svm_node_closure_volume(KernelGlobals *kg, ShaderData *sd, float *stack, uint4 node, int path_flag)
{
	uint type, param1_offset, param2_offset;

#ifdef __MULTI_CLOSURE__
	uint mix_weight_offset;
	decode_node_uchar4(node.y, &type, &param1_offset, &param2_offset, &mix_weight_offset);
	float mix_weight = (stack_valid(mix_weight_offset)? stack_load_float(stack, mix_weight_offset): 1.0f);

	if(mix_weight == 0.0f)
		return;
#else
	decode_node_uchar4(node.y, &type, &param1_offset, &param2_offset, NULL);
	float mix_weight = 1.0f;
#endif

	float param1 = (stack_valid(param1_offset))? stack_load_float(stack, param1_offset): __uint_as_float(node.z);
	//float param2 = (stack_valid(param2_offset))? stack_load_float(stack, param2_offset): __uint_as_float(node.w);

	switch(type) {
		case CLOSURE_VOLUME_TRANSPARENT_ID: {
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				float density = param1;
				sd->flag |= volume_transparent_setup(sc, density);
			}
			break;
		}
		case CLOSURE_VOLUME_ISOTROPIC_ID: {
			ShaderClosure *sc = svm_node_closure_get_bsdf(sd, mix_weight);

			if(sc) {
				float density = param1;
				sd->flag |= volume_isotropic_setup(sc, density);
			}
			break;
		}
		default:
			break;
	}
}

__device void svm_node_closure_emission(ShaderData *sd, float *stack, uint4 node)
{
#ifdef __MULTI_CLOSURE__
	uint mix_weight_offset = node.y;

	if(stack_valid(mix_weight_offset)) {
		float mix_weight = stack_load_float(stack, mix_weight_offset);

		if(mix_weight == 0.0f)
			return;

		svm_node_closure_get_non_bsdf(sd, CLOSURE_EMISSION_ID, mix_weight);
	}
	else
		svm_node_closure_get_non_bsdf(sd, CLOSURE_EMISSION_ID, 1.0f);
#else
	ShaderClosure *sc = &sd->closure;
	sc->type = CLOSURE_EMISSION_ID;
#endif

	sd->flag |= SD_EMISSION;
}

__device void svm_node_closure_background(ShaderData *sd, float *stack, uint4 node)
{
#ifdef __MULTI_CLOSURE__
	uint mix_weight_offset = node.y;

	if(stack_valid(mix_weight_offset)) {
		float mix_weight = stack_load_float(stack, mix_weight_offset);

		if(mix_weight == 0.0f)
			return;

		svm_node_closure_get_non_bsdf(sd, CLOSURE_BACKGROUND_ID, mix_weight);
	}
	else
		svm_node_closure_get_non_bsdf(sd, CLOSURE_BACKGROUND_ID, 1.0f);
#else
	ShaderClosure *sc = &sd->closure;
	sc->type = CLOSURE_BACKGROUND_ID;
#endif
}

__device void svm_node_closure_holdout(ShaderData *sd, float *stack, uint4 node)
{
#ifdef __MULTI_CLOSURE__
	uint mix_weight_offset = node.y;

	if(stack_valid(mix_weight_offset)) {
		float mix_weight = stack_load_float(stack, mix_weight_offset);

		if(mix_weight == 0.0f)
			return;

		svm_node_closure_get_non_bsdf(sd, CLOSURE_HOLDOUT_ID, mix_weight);
	}
	else
		svm_node_closure_get_non_bsdf(sd, CLOSURE_HOLDOUT_ID, 1.0f);
#else
	ShaderClosure *sc = &sd->closure;
	sc->type = CLOSURE_HOLDOUT_ID;
#endif

	sd->flag |= SD_HOLDOUT;
}

__device void svm_node_closure_ambient_occlusion(ShaderData *sd, float *stack, uint4 node)
{
#ifdef __MULTI_CLOSURE__
	uint mix_weight_offset = node.y;

	if(stack_valid(mix_weight_offset)) {
		float mix_weight = stack_load_float(stack, mix_weight_offset);

		if(mix_weight == 0.0f)
			return;

		svm_node_closure_get_non_bsdf(sd, CLOSURE_AMBIENT_OCCLUSION_ID, mix_weight);
	}
	else
		svm_node_closure_get_non_bsdf(sd, CLOSURE_AMBIENT_OCCLUSION_ID, 1.0f);
#else
	ShaderClosure *sc = &sd->closure;
	sc->type = CLOSURE_AMBIENT_OCCLUSION_ID;
#endif

	sd->flag |= SD_AO;
}

/* Closure Nodes */

__device_inline void svm_node_closure_store_weight(ShaderData *sd, float3 weight)
{
#ifdef __MULTI_CLOSURE__
	if(sd->num_closure < MAX_CLOSURE)
		sd->closure[sd->num_closure].weight = weight;
#else
	sd->closure.weight = weight;
#endif
}

__device void svm_node_closure_set_weight(ShaderData *sd, uint r, uint g, uint b)
{
	float3 weight = make_float3(__uint_as_float(r), __uint_as_float(g), __uint_as_float(b));
	svm_node_closure_store_weight(sd, weight);
}

__device void svm_node_emission_set_weight_total(KernelGlobals *kg, ShaderData *sd, uint r, uint g, uint b)
{
	float3 weight = make_float3(__uint_as_float(r), __uint_as_float(g), __uint_as_float(b));

	if(sd->object != ~0)
		weight /= object_surface_area(kg, sd->object);

	svm_node_closure_store_weight(sd, weight);
}

__device void svm_node_closure_weight(ShaderData *sd, float *stack, uint weight_offset)
{
	float3 weight = stack_load_float3(stack, weight_offset);

	svm_node_closure_store_weight(sd, weight);
}

__device void svm_node_emission_weight(KernelGlobals *kg, ShaderData *sd, float *stack, uint4 node)
{
	uint color_offset = node.y;
	uint strength_offset = node.z;
	uint total_power = node.w;

	float strength = stack_load_float(stack, strength_offset);
	float3 weight = stack_load_float3(stack, color_offset)*strength;

	if(total_power && sd->object != ~0)
		weight /= object_surface_area(kg, sd->object);

	svm_node_closure_store_weight(sd, weight);
}

__device void svm_node_mix_closure(ShaderData *sd, float *stack,
	uint4 node, int *offset, float *randb)
{
#ifdef __MULTI_CLOSURE__
	/* fetch weight from blend input, previous mix closures,
	 * and write to stack to be used by closure nodes later */
	uint weight_offset, in_weight_offset, weight1_offset, weight2_offset;
	decode_node_uchar4(node.y, &weight_offset, &in_weight_offset, &weight1_offset, &weight2_offset);

	float weight = stack_load_float(stack, weight_offset);
	weight = clamp(weight, 0.0f, 1.0f);

	float in_weight = (stack_valid(in_weight_offset))? stack_load_float(stack, in_weight_offset): 1.0f;

	if(stack_valid(weight1_offset))
		stack_store_float(stack, weight1_offset, in_weight*(1.0f - weight));
	if(stack_valid(weight2_offset))
		stack_store_float(stack, weight2_offset, in_weight*weight);
#else
	/* pick a closure and make the random number uniform over 0..1 again.
	 * closure 1 starts on the next node, for closure 2 the start is at an
	 * offset from the current node, so we jump */
	uint weight_offset = node.y;
	uint node_jump = node.z;
	float weight = stack_load_float(stack, weight_offset);
	weight = clamp(weight, 0.0f, 1.0f);

	if(*randb < weight) {
		*offset += node_jump;
		*randb = *randb/weight;
	}
	else
		*randb = (*randb - weight)/(1.0f - weight);
#endif
}

__device void svm_node_add_closure(ShaderData *sd, float *stack, uint unused,
	uint node_jump, int *offset, float *randb, float *closure_weight)
{
#ifdef __MULTI_CLOSURE__
	/* nothing to do, handled in compiler */
#else
	/* pick one of the two closures with probability 0.5. sampling quality
	 * is not going to be great, for that we'd need to evaluate the weights
	 * of the two closures being added */
	float weight = 0.5f;

	if(*randb < weight) {
		*offset += node_jump;
		*randb = *randb/weight;
	}
	else
		*randb = (*randb - weight)/(1.0f - weight);
	
	*closure_weight *= 2.0f;
#endif
}

/* (Bump) normal */

__device void svm_node_set_normal(KernelGlobals *kg, ShaderData *sd, float *stack, uint in_direction, uint out_normal)
{
	float3 normal = stack_load_float3(stack, in_direction);
	sd->N = normal;
	stack_store_float3(stack, out_normal, normal);
}

CCL_NAMESPACE_END

