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
 * limitations under the License.
 */

/* Functions to evaluate shaders and use the resulting shader closures. */

#pragma once

#include "kernel/closure/alloc.h"
#include "kernel/closure/bsdf.h"
#include "kernel/closure/bsdf_util.h"
#include "kernel/closure/emissive.h"

#include "kernel/film/accumulate.h"

#include "kernel/svm/svm.h"

#ifdef __OSL__
#  include "kernel/osl/shader.h"
#endif

CCL_NAMESPACE_BEGIN

/* Merging */

#if defined(__VOLUME__)
ccl_device_inline void shader_merge_volume_closures(ccl_private ShaderData *sd)
{
  /* Merge identical closures to save closure space with stacked volumes. */
  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private ShaderClosure *sci = &sd->closure[i];

    if (sci->type != CLOSURE_VOLUME_HENYEY_GREENSTEIN_ID) {
      continue;
    }

    for (int j = i + 1; j < sd->num_closure; j++) {
      ccl_private ShaderClosure *scj = &sd->closure[j];
      if (sci->type != scj->type) {
        continue;
      }

      ccl_private const HenyeyGreensteinVolume *hgi = (ccl_private const HenyeyGreensteinVolume *)
          sci;
      ccl_private const HenyeyGreensteinVolume *hgj = (ccl_private const HenyeyGreensteinVolume *)
          scj;
      if (!(hgi->g == hgj->g)) {
        continue;
      }

      sci->weight += scj->weight;
      sci->sample_weight += scj->sample_weight;

      int size = sd->num_closure - (j + 1);
      if (size > 0) {
        for (int k = 0; k < size; k++) {
          scj[k] = scj[k + 1];
        }
      }

      sd->num_closure--;
      kernel_assert(sd->num_closure >= 0);
      j--;
    }
  }
}

ccl_device_inline void shader_copy_volume_phases(ccl_private ShaderVolumePhases *ccl_restrict
                                                     phases,
                                                 ccl_private const ShaderData *ccl_restrict sd)
{
  phases->num_closure = 0;

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *from_sc = &sd->closure[i];
    ccl_private const HenyeyGreensteinVolume *from_hg =
        (ccl_private const HenyeyGreensteinVolume *)from_sc;

    if (from_sc->type == CLOSURE_VOLUME_HENYEY_GREENSTEIN_ID) {
      ccl_private ShaderVolumeClosure *to_sc = &phases->closure[phases->num_closure];

      to_sc->weight = from_sc->weight;
      to_sc->sample_weight = from_sc->sample_weight;
      to_sc->g = from_hg->g;
      phases->num_closure++;
      if (phases->num_closure >= MAX_VOLUME_CLOSURE) {
        break;
      }
    }
  }
}
#endif /* __VOLUME__ */

ccl_device_inline void shader_prepare_surface_closures(KernelGlobals kg,
                                                       ConstIntegratorState state,
                                                       ccl_private ShaderData *sd,
                                                       const uint32_t path_flag)
{
  /* Filter out closures. */
  if (kernel_data.integrator.filter_closures) {
    if (kernel_data.integrator.filter_closures & FILTER_CLOSURE_EMISSION) {
      sd->closure_emission_background = zero_float3();
    }

    if (kernel_data.integrator.filter_closures & FILTER_CLOSURE_DIRECT_LIGHT) {
      sd->flag &= ~SD_BSDF_HAS_EVAL;
    }

    if (path_flag & PATH_RAY_CAMERA) {
      for (int i = 0; i < sd->num_closure; i++) {
        ccl_private ShaderClosure *sc = &sd->closure[i];

        if ((CLOSURE_IS_BSDF_DIFFUSE(sc->type) &&
             (kernel_data.integrator.filter_closures & FILTER_CLOSURE_DIFFUSE)) ||
            (CLOSURE_IS_BSDF_GLOSSY(sc->type) &&
             (kernel_data.integrator.filter_closures & FILTER_CLOSURE_GLOSSY)) ||
            (CLOSURE_IS_BSDF_TRANSMISSION(sc->type) &&
             (kernel_data.integrator.filter_closures & FILTER_CLOSURE_TRANSMISSION))) {
          sc->type = CLOSURE_NONE_ID;
          sc->sample_weight = 0.0f;
        }
        else if ((CLOSURE_IS_BSDF_TRANSPARENT(sc->type) &&
                  (kernel_data.integrator.filter_closures & FILTER_CLOSURE_TRANSPARENT))) {
          sc->type = CLOSURE_HOLDOUT_ID;
          sc->sample_weight = 0.0f;
          sd->flag |= SD_HOLDOUT;
        }
      }
    }
  }

  /* Defensive sampling.
   *
   * We can likely also do defensive sampling at deeper bounces, particularly
   * for cases like a perfect mirror but possibly also others. This will need
   * a good heuristic. */
  if (INTEGRATOR_STATE(state, path, bounce) + INTEGRATOR_STATE(state, path, transparent_bounce) ==
          0 &&
      sd->num_closure > 1) {
    float sum = 0.0f;

    for (int i = 0; i < sd->num_closure; i++) {
      ccl_private ShaderClosure *sc = &sd->closure[i];
      if (CLOSURE_IS_BSDF_OR_BSSRDF(sc->type)) {
        sum += sc->sample_weight;
      }
    }

    for (int i = 0; i < sd->num_closure; i++) {
      ccl_private ShaderClosure *sc = &sd->closure[i];
      if (CLOSURE_IS_BSDF_OR_BSSRDF(sc->type)) {
        sc->sample_weight = max(sc->sample_weight, 0.125f * sum);
      }
    }
  }

  /* Filter glossy.
   *
   * Blurring of bsdf after bounces, for rays that have a small likelihood
   * of following this particular path (diffuse, rough glossy) */
  if (kernel_data.integrator.filter_glossy != FLT_MAX) {
    float blur_pdf = kernel_data.integrator.filter_glossy *
                     INTEGRATOR_STATE(state, path, min_ray_pdf);

    if (blur_pdf < 1.0f) {
      float blur_roughness = sqrtf(1.0f - blur_pdf) * 0.5f;

      for (int i = 0; i < sd->num_closure; i++) {
        ccl_private ShaderClosure *sc = &sd->closure[i];
        if (CLOSURE_IS_BSDF(sc->type)) {
          bsdf_blur(kg, sc, blur_roughness);
        }
      }
    }
  }
}

/* BSDF */

ccl_device_inline bool shader_bsdf_is_transmission(ccl_private const ShaderData *sd,
                                                   const float3 omega_in)
{
  return dot(sd->N, omega_in) < 0.0f;
}

ccl_device_forceinline bool _shader_bsdf_exclude(ClosureType type, uint light_shader_flags)
{
  if (!(light_shader_flags & SHADER_EXCLUDE_ANY)) {
    return false;
  }
  if (light_shader_flags & SHADER_EXCLUDE_DIFFUSE) {
    if (CLOSURE_IS_BSDF_DIFFUSE(type)) {
      return true;
    }
  }
  if (light_shader_flags & SHADER_EXCLUDE_GLOSSY) {
    if (CLOSURE_IS_BSDF_GLOSSY(type)) {
      return true;
    }
  }
  if (light_shader_flags & SHADER_EXCLUDE_TRANSMIT) {
    if (CLOSURE_IS_BSDF_TRANSMISSION(type)) {
      return true;
    }
  }
  return false;
}

ccl_device_inline float _shader_bsdf_multi_eval(KernelGlobals kg,
                                                ccl_private ShaderData *sd,
                                                const float3 omega_in,
                                                const bool is_transmission,
                                                ccl_private const ShaderClosure *skip_sc,
                                                ccl_private BsdfEval *result_eval,
                                                float sum_pdf,
                                                float sum_sample_weight,
                                                const uint light_shader_flags)
{
  /* This is the veach one-sample model with balance heuristic,
   * some PDF factors drop out when using balance heuristic weighting. */
  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];

    if (sc == skip_sc) {
      continue;
    }

    if (CLOSURE_IS_BSDF_OR_BSSRDF(sc->type)) {
      if (CLOSURE_IS_BSDF(sc->type) && !_shader_bsdf_exclude(sc->type, light_shader_flags)) {
        float bsdf_pdf = 0.0f;
        float3 eval = bsdf_eval(kg, sd, sc, omega_in, is_transmission, &bsdf_pdf);

        if (bsdf_pdf != 0.0f) {
          bsdf_eval_accum(result_eval, sc->type, eval * sc->weight);
          sum_pdf += bsdf_pdf * sc->sample_weight;
        }
      }

      sum_sample_weight += sc->sample_weight;
    }
  }

  return (sum_sample_weight > 0.0f) ? sum_pdf / sum_sample_weight : 0.0f;
}

#ifndef __KERNEL_CUDA__
ccl_device
#else
ccl_device_inline
#endif
    float
    shader_bsdf_eval(KernelGlobals kg,
                     ccl_private ShaderData *sd,
                     const float3 omega_in,
                     const bool is_transmission,
                     ccl_private BsdfEval *bsdf_eval,
                     const uint light_shader_flags)
{
  bsdf_eval_init(bsdf_eval, CLOSURE_NONE_ID, zero_float3());

  return _shader_bsdf_multi_eval(
      kg, sd, omega_in, is_transmission, NULL, bsdf_eval, 0.0f, 0.0f, light_shader_flags);
}

/* Randomly sample a BSSRDF or BSDF proportional to ShaderClosure.sample_weight. */
ccl_device_inline ccl_private const ShaderClosure *shader_bsdf_bssrdf_pick(
    ccl_private const ShaderData *ccl_restrict sd, ccl_private float *randu)
{
  int sampled = 0;

  if (sd->num_closure > 1) {
    /* Pick a BSDF or based on sample weights. */
    float sum = 0.0f;

    for (int i = 0; i < sd->num_closure; i++) {
      ccl_private const ShaderClosure *sc = &sd->closure[i];

      if (CLOSURE_IS_BSDF_OR_BSSRDF(sc->type)) {
        sum += sc->sample_weight;
      }
    }

    float r = (*randu) * sum;
    float partial_sum = 0.0f;

    for (int i = 0; i < sd->num_closure; i++) {
      ccl_private const ShaderClosure *sc = &sd->closure[i];

      if (CLOSURE_IS_BSDF_OR_BSSRDF(sc->type)) {
        float next_sum = partial_sum + sc->sample_weight;

        if (r < next_sum) {
          sampled = i;

          /* Rescale to reuse for direction sample, to better preserve stratification. */
          *randu = (r - partial_sum) / sc->sample_weight;
          break;
        }

        partial_sum = next_sum;
      }
    }
  }

  return &sd->closure[sampled];
}

/* Return weight for picked BSSRDF. */
ccl_device_inline float3
shader_bssrdf_sample_weight(ccl_private const ShaderData *ccl_restrict sd,
                            ccl_private const ShaderClosure *ccl_restrict bssrdf_sc)
{
  float3 weight = bssrdf_sc->weight;

  if (sd->num_closure > 1) {
    float sum = 0.0f;
    for (int i = 0; i < sd->num_closure; i++) {
      ccl_private const ShaderClosure *sc = &sd->closure[i];

      if (CLOSURE_IS_BSDF_OR_BSSRDF(sc->type)) {
        sum += sc->sample_weight;
      }
    }
    weight *= sum / bssrdf_sc->sample_weight;
  }

  return weight;
}

/* Sample direction for picked BSDF, and return evaluation and pdf for all
 * BSDFs combined using MIS. */
ccl_device int shader_bsdf_sample_closure(KernelGlobals kg,
                                          ccl_private ShaderData *sd,
                                          ccl_private const ShaderClosure *sc,
                                          float randu,
                                          float randv,
                                          ccl_private BsdfEval *bsdf_eval,
                                          ccl_private float3 *omega_in,
                                          ccl_private differential3 *domega_in,
                                          ccl_private float *pdf)
{
  /* BSSRDF should already have been handled elsewhere. */
  kernel_assert(CLOSURE_IS_BSDF(sc->type));

  int label;
  float3 eval = zero_float3();

  *pdf = 0.0f;
  label = bsdf_sample(kg, sd, sc, randu, randv, &eval, omega_in, domega_in, pdf);

  if (*pdf != 0.0f) {
    bsdf_eval_init(bsdf_eval, sc->type, eval * sc->weight);

    if (sd->num_closure > 1) {
      const bool is_transmission = shader_bsdf_is_transmission(sd, *omega_in);
      float sweight = sc->sample_weight;
      *pdf = _shader_bsdf_multi_eval(
          kg, sd, *omega_in, is_transmission, sc, bsdf_eval, *pdf * sweight, sweight, 0);
    }
  }

  return label;
}

ccl_device float shader_bsdf_average_roughness(ccl_private const ShaderData *sd)
{
  float roughness = 0.0f;
  float sum_weight = 0.0f;

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];

    if (CLOSURE_IS_BSDF(sc->type)) {
      /* sqrt once to undo the squaring from multiplying roughness on the
       * two axes, and once for the squared roughness convention. */
      float weight = fabsf(average(sc->weight));
      roughness += weight * sqrtf(safe_sqrtf(bsdf_get_roughness_squared(sc)));
      sum_weight += weight;
    }
  }

  return (sum_weight > 0.0f) ? roughness / sum_weight : 0.0f;
}

ccl_device float3 shader_bsdf_transparency(KernelGlobals kg, ccl_private const ShaderData *sd)
{
  if (sd->flag & SD_HAS_ONLY_VOLUME) {
    return one_float3();
  }
  else if (sd->flag & SD_TRANSPARENT) {
    return sd->closure_transparent_extinction;
  }
  else {
    return zero_float3();
  }
}

ccl_device void shader_bsdf_disable_transparency(KernelGlobals kg, ccl_private ShaderData *sd)
{
  if (sd->flag & SD_TRANSPARENT) {
    for (int i = 0; i < sd->num_closure; i++) {
      ccl_private ShaderClosure *sc = &sd->closure[i];

      if (sc->type == CLOSURE_BSDF_TRANSPARENT_ID) {
        sc->sample_weight = 0.0f;
        sc->weight = zero_float3();
      }
    }

    sd->flag &= ~SD_TRANSPARENT;
  }
}

ccl_device float3 shader_bsdf_alpha(KernelGlobals kg, ccl_private const ShaderData *sd)
{
  float3 alpha = one_float3() - shader_bsdf_transparency(kg, sd);

  alpha = max(alpha, zero_float3());
  alpha = min(alpha, one_float3());

  return alpha;
}

ccl_device float3 shader_bsdf_diffuse(KernelGlobals kg, ccl_private const ShaderData *sd)
{
  float3 eval = zero_float3();

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];

    if (CLOSURE_IS_BSDF_DIFFUSE(sc->type) || CLOSURE_IS_BSSRDF(sc->type))
      eval += sc->weight;
  }

  return eval;
}

ccl_device float3 shader_bsdf_glossy(KernelGlobals kg, ccl_private const ShaderData *sd)
{
  float3 eval = zero_float3();

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];

    if (CLOSURE_IS_BSDF_GLOSSY(sc->type))
      eval += sc->weight;
  }

  return eval;
}

ccl_device float3 shader_bsdf_transmission(KernelGlobals kg, ccl_private const ShaderData *sd)
{
  float3 eval = zero_float3();

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];

    if (CLOSURE_IS_BSDF_TRANSMISSION(sc->type))
      eval += sc->weight;
  }

  return eval;
}

ccl_device float3 shader_bsdf_average_normal(KernelGlobals kg, ccl_private const ShaderData *sd)
{
  float3 N = zero_float3();

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];
    if (CLOSURE_IS_BSDF_OR_BSSRDF(sc->type))
      N += sc->N * fabsf(average(sc->weight));
  }

  return (is_zero(N)) ? sd->N : normalize(N);
}

ccl_device float3 shader_bsdf_ao(KernelGlobals kg,
                                 ccl_private const ShaderData *sd,
                                 const float ao_factor,
                                 ccl_private float3 *N_)
{
  float3 eval = zero_float3();
  float3 N = zero_float3();

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];

    if (CLOSURE_IS_BSDF_DIFFUSE(sc->type)) {
      ccl_private const DiffuseBsdf *bsdf = (ccl_private const DiffuseBsdf *)sc;
      eval += sc->weight * ao_factor;
      N += bsdf->N * fabsf(average(sc->weight));
    }
  }

  *N_ = (is_zero(N)) ? sd->N : normalize(N);
  return eval;
}

#ifdef __SUBSURFACE__
ccl_device float3 shader_bssrdf_normal(ccl_private const ShaderData *sd)
{
  float3 N = zero_float3();

  for (int i = 0; i < sd->num_closure; i++) {
    ccl_private const ShaderClosure *sc = &sd->closure[i];

    if (CLOSURE_IS_BSSRDF(sc->type)) {
      ccl_private const Bssrdf *bssrdf = (ccl_private const Bssrdf *)sc;
      float avg_weight = fabsf(average(sc->weight));

      N += bssrdf->N * avg_weight;
    }
  }

  return (is_zero(N)) ? sd->N : normalize(N);
}
#endif /* __SUBSURFACE__ */

/* Constant emission optimization */

ccl_device bool shader_constant_emission_eval(KernelGlobals kg,
                                              int shader,
                                              ccl_private float3 *eval)
{
  int shader_index = shader & SHADER_MASK;
  int shader_flag = kernel_tex_fetch(__shaders, shader_index).flags;

  if (shader_flag & SD_HAS_CONSTANT_EMISSION) {
    *eval = make_float3(kernel_tex_fetch(__shaders, shader_index).constant_emission[0],
                        kernel_tex_fetch(__shaders, shader_index).constant_emission[1],
                        kernel_tex_fetch(__shaders, shader_index).constant_emission[2]);

    return true;
  }

  return false;
}

/* Background */

ccl_device float3 shader_background_eval(ccl_private const ShaderData *sd)
{
  if (sd->flag & SD_EMISSION) {
    return sd->closure_emission_background;
  }
  else {
    return zero_float3();
  }
}

/* Emission */

ccl_device float3 shader_emissive_eval(ccl_private const ShaderData *sd)
{
  if (sd->flag & SD_EMISSION) {
    return emissive_simple_eval(sd->Ng, sd->I) * sd->closure_emission_background;
  }
  else {
    return zero_float3();
  }
}

/* Holdout */

ccl_device float3 shader_holdout_apply(KernelGlobals kg, ccl_private ShaderData *sd)
{
  float3 weight = zero_float3();

  /* For objects marked as holdout, preserve transparency and remove all other
   * closures, replacing them with a holdout weight. */
  if (sd->object_flag & SD_OBJECT_HOLDOUT_MASK) {
    if ((sd->flag & SD_TRANSPARENT) && !(sd->flag & SD_HAS_ONLY_VOLUME)) {
      weight = one_float3() - sd->closure_transparent_extinction;

      for (int i = 0; i < sd->num_closure; i++) {
        ccl_private ShaderClosure *sc = &sd->closure[i];
        if (!CLOSURE_IS_BSDF_TRANSPARENT(sc->type)) {
          sc->type = NBUILTIN_CLOSURES;
        }
      }

      sd->flag &= ~(SD_CLOSURE_FLAGS - (SD_TRANSPARENT | SD_BSDF));
    }
    else {
      weight = one_float3();
    }
  }
  else {
    for (int i = 0; i < sd->num_closure; i++) {
      ccl_private const ShaderClosure *sc = &sd->closure[i];
      if (CLOSURE_IS_HOLDOUT(sc->type)) {
        weight += sc->weight;
      }
    }
  }

  return weight;
}

/* Surface Evaluation */

template<uint node_feature_mask, typename ConstIntegratorGenericState>
ccl_device void shader_eval_surface(KernelGlobals kg,
                                    ConstIntegratorGenericState state,
                                    ccl_private ShaderData *ccl_restrict sd,
                                    ccl_global float *ccl_restrict buffer,
                                    uint32_t path_flag)
{
  /* If path is being terminated, we are tracing a shadow ray or evaluating
   * emission, then we don't need to store closures. The emission and shadow
   * shader data also do not have a closure array to save GPU memory. */
  int max_closures;
  if (path_flag & (PATH_RAY_TERMINATE | PATH_RAY_SHADOW | PATH_RAY_EMISSION)) {
    max_closures = 0;
  }
  else {
    max_closures = kernel_data.max_closures;
  }

  sd->num_closure = 0;
  sd->num_closure_left = max_closures;

#ifdef __OSL__
  if (kg->osl) {
    if (sd->object == OBJECT_NONE && sd->lamp == LAMP_NONE) {
      OSLShader::eval_background(kg, state, sd, path_flag);
    }
    else {
      OSLShader::eval_surface(kg, state, sd, path_flag);
    }
  }
  else
#endif
  {
#ifdef __SVM__
    svm_eval_nodes<node_feature_mask, SHADER_TYPE_SURFACE>(kg, state, sd, buffer, path_flag);
#else
    if (sd->object == OBJECT_NONE) {
      sd->closure_emission_background = make_float3(0.8f, 0.8f, 0.8f);
      sd->flag |= SD_EMISSION;
    }
    else {
      ccl_private DiffuseBsdf *bsdf = (ccl_private DiffuseBsdf *)bsdf_alloc(
          sd, sizeof(DiffuseBsdf), make_float3(0.8f, 0.8f, 0.8f));
      if (bsdf != NULL) {
        bsdf->N = sd->N;
        sd->flag |= bsdf_diffuse_setup(bsdf);
      }
    }
#endif
  }
}

/* Volume */

#ifdef __VOLUME__

ccl_device_inline float _shader_volume_phase_multi_eval(
    ccl_private const ShaderData *sd,
    ccl_private const ShaderVolumePhases *phases,
    const float3 omega_in,
    int skip_phase,
    ccl_private BsdfEval *result_eval,
    float sum_pdf,
    float sum_sample_weight)
{
  for (int i = 0; i < phases->num_closure; i++) {
    if (i == skip_phase)
      continue;

    ccl_private const ShaderVolumeClosure *svc = &phases->closure[i];
    float phase_pdf = 0.0f;
    float3 eval = volume_phase_eval(sd, svc, omega_in, &phase_pdf);

    if (phase_pdf != 0.0f) {
      bsdf_eval_accum(result_eval, CLOSURE_VOLUME_HENYEY_GREENSTEIN_ID, eval);
      sum_pdf += phase_pdf * svc->sample_weight;
    }

    sum_sample_weight += svc->sample_weight;
  }

  return (sum_sample_weight > 0.0f) ? sum_pdf / sum_sample_weight : 0.0f;
}

ccl_device float shader_volume_phase_eval(KernelGlobals kg,
                                          ccl_private const ShaderData *sd,
                                          ccl_private const ShaderVolumePhases *phases,
                                          const float3 omega_in,
                                          ccl_private BsdfEval *phase_eval)
{
  bsdf_eval_init(phase_eval, CLOSURE_VOLUME_HENYEY_GREENSTEIN_ID, zero_float3());

  return _shader_volume_phase_multi_eval(sd, phases, omega_in, -1, phase_eval, 0.0f, 0.0f);
}

ccl_device int shader_volume_phase_sample(KernelGlobals kg,
                                          ccl_private const ShaderData *sd,
                                          ccl_private const ShaderVolumePhases *phases,
                                          float randu,
                                          float randv,
                                          ccl_private BsdfEval *phase_eval,
                                          ccl_private float3 *omega_in,
                                          ccl_private differential3 *domega_in,
                                          ccl_private float *pdf)
{
  int sampled = 0;

  if (phases->num_closure > 1) {
    /* pick a phase closure based on sample weights */
    float sum = 0.0f;

    for (sampled = 0; sampled < phases->num_closure; sampled++) {
      ccl_private const ShaderVolumeClosure *svc = &phases->closure[sampled];
      sum += svc->sample_weight;
    }

    float r = randu * sum;
    float partial_sum = 0.0f;

    for (sampled = 0; sampled < phases->num_closure; sampled++) {
      ccl_private const ShaderVolumeClosure *svc = &phases->closure[sampled];
      float next_sum = partial_sum + svc->sample_weight;

      if (r <= next_sum) {
        /* Rescale to reuse for BSDF direction sample. */
        randu = (r - partial_sum) / svc->sample_weight;
        break;
      }

      partial_sum = next_sum;
    }

    if (sampled == phases->num_closure) {
      *pdf = 0.0f;
      return LABEL_NONE;
    }
  }

  /* todo: this isn't quite correct, we don't weight anisotropy properly
   * depending on color channels, even if this is perhaps not a common case */
  ccl_private const ShaderVolumeClosure *svc = &phases->closure[sampled];
  int label;
  float3 eval = zero_float3();

  *pdf = 0.0f;
  label = volume_phase_sample(sd, svc, randu, randv, &eval, omega_in, domega_in, pdf);

  if (*pdf != 0.0f) {
    bsdf_eval_init(phase_eval, CLOSURE_VOLUME_HENYEY_GREENSTEIN_ID, eval);
  }

  return label;
}

ccl_device int shader_phase_sample_closure(KernelGlobals kg,
                                           ccl_private const ShaderData *sd,
                                           ccl_private const ShaderVolumeClosure *sc,
                                           float randu,
                                           float randv,
                                           ccl_private BsdfEval *phase_eval,
                                           ccl_private float3 *omega_in,
                                           ccl_private differential3 *domega_in,
                                           ccl_private float *pdf)
{
  int label;
  float3 eval = zero_float3();

  *pdf = 0.0f;
  label = volume_phase_sample(sd, sc, randu, randv, &eval, omega_in, domega_in, pdf);

  if (*pdf != 0.0f)
    bsdf_eval_init(phase_eval, CLOSURE_VOLUME_HENYEY_GREENSTEIN_ID, eval);

  return label;
}

/* Volume Evaluation */

template<const bool shadow, typename StackReadOp, typename ConstIntegratorGenericState>
ccl_device_inline void shader_eval_volume(KernelGlobals kg,
                                          ConstIntegratorGenericState state,
                                          ccl_private ShaderData *ccl_restrict sd,
                                          const uint32_t path_flag,
                                          StackReadOp stack_read)
{
  /* If path is being terminated, we are tracing a shadow ray or evaluating
   * emission, then we don't need to store closures. The emission and shadow
   * shader data also do not have a closure array to save GPU memory. */
  int max_closures;
  if (path_flag & (PATH_RAY_TERMINATE | PATH_RAY_SHADOW | PATH_RAY_EMISSION)) {
    max_closures = 0;
  }
  else {
    max_closures = kernel_data.max_closures;
  }

  /* reset closures once at the start, we will be accumulating the closures
   * for all volumes in the stack into a single array of closures */
  sd->num_closure = 0;
  sd->num_closure_left = max_closures;
  sd->flag = 0;
  sd->object_flag = 0;

  for (int i = 0;; i++) {
    const VolumeStack entry = stack_read(i);
    if (entry.shader == SHADER_NONE) {
      break;
    }

    /* Setup shader-data from stack. it's mostly setup already in
     * shader_setup_from_volume, this switching should be quick. */
    sd->object = entry.object;
    sd->lamp = LAMP_NONE;
    sd->shader = entry.shader;

    sd->flag &= ~SD_SHADER_FLAGS;
    sd->flag |= kernel_tex_fetch(__shaders, (sd->shader & SHADER_MASK)).flags;
    sd->object_flag &= ~SD_OBJECT_FLAGS;

    if (sd->object != OBJECT_NONE) {
      sd->object_flag |= kernel_tex_fetch(__object_flag, sd->object);

#  ifdef __OBJECT_MOTION__
      /* todo: this is inefficient for motion blur, we should be
       * caching matrices instead of recomputing them each step */
      shader_setup_object_transforms(kg, sd, sd->time);
#  endif
    }

    /* evaluate shader */
#  ifdef __SVM__
#    ifdef __OSL__
    if (kg->osl) {
      OSLShader::eval_volume(kg, state, sd, path_flag);
    }
    else
#    endif
    {
      svm_eval_nodes<KERNEL_FEATURE_NODE_MASK_VOLUME, SHADER_TYPE_VOLUME>(
          kg, state, sd, NULL, path_flag);
    }
#  endif

    /* Merge closures to avoid exceeding number of closures limit. */
    if (!shadow) {
      if (i > 0) {
        shader_merge_volume_closures(sd);
      }
    }
  }
}

#endif /* __VOLUME__ */

/* Displacement Evaluation */

template<typename ConstIntegratorGenericState>
ccl_device void shader_eval_displacement(KernelGlobals kg,
                                         ConstIntegratorGenericState state,
                                         ccl_private ShaderData *sd)
{
  sd->num_closure = 0;
  sd->num_closure_left = 0;

  /* this will modify sd->P */
#ifdef __SVM__
#  ifdef __OSL__
  if (kg->osl)
    OSLShader::eval_displacement(kg, state, sd);
  else
#  endif
  {
    svm_eval_nodes<KERNEL_FEATURE_NODE_MASK_DISPLACEMENT, SHADER_TYPE_DISPLACEMENT>(
        kg, state, sd, NULL, 0);
  }
#endif
}

/* Cryptomatte */

ccl_device float shader_cryptomatte_id(KernelGlobals kg, int shader)
{
  return kernel_tex_fetch(__shaders, (shader & SHADER_MASK)).cryptomatte_id;
}

CCL_NAMESPACE_END
