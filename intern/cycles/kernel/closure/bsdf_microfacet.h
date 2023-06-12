/* SPDX-License-Identifier: BSD-3-Clause
 *
 * Adapted from Open Shading Language
 * Copyright (c) 2009-2010 Sony Pictures Imageworks Inc., et al.
 * All Rights Reserved.
 *
 * Modifications Copyright 2011-2022 Blender Foundation. */

#pragma once

#include "kernel/closure/bsdf_util.h"

#include "kernel/sample/pattern.h"

#include "kernel/util/lookup_table.h"

CCL_NAMESPACE_BEGIN

enum MicrofacetType {
  BECKMANN,
  GGX,
  SHARP,
};

enum MicrofacetFresnel {
  NONE = 0,
  DIELECTRIC,
  DIELECTRIC_TINT, /* used by the OSL MaterialX closures */
  CONDUCTOR,
  GENERALIZED_SCHLICK,
  CONSTANT, /* only needed by MultiGGX */
  PRINCIPLED_V1,
};

typedef struct FresnelPrincipledV1 {
  Spectrum color; /* only needed by MultiGGX */
  Spectrum cspec0;
} FresnelPrincipledV1;

typedef struct FresnelConstant {
  Spectrum color;
} FresnelConstant;

typedef struct FresnelDielectricTint {
  Spectrum reflection_tint;
  Spectrum transmission_tint;
} FresnelDielectricTint;

typedef struct FresnelConductor {
  Spectrum n, k;
} FresnelConductor;

typedef struct FresnelGeneralizedSchlick {
  Spectrum reflection_tint;
  Spectrum transmission_tint;
  Spectrum f0, f90;
  float exponent;
} FresnelGeneralizedSchlick;

typedef struct MicrofacetBsdf {
  SHADER_CLOSURE_BASE;

  float alpha_x, alpha_y, ior;
  int fresnel_type;
  ccl_private void *fresnel;
  float3 T;
} MicrofacetBsdf;

static_assert(sizeof(ShaderClosure) >= sizeof(MicrofacetBsdf), "MicrofacetBsdf is too large!");

/* Beckmann VNDF importance sampling algorithm from:
 * Importance Sampling Microfacet-Based BSDFs using the Distribution of Visible Normals.
 * Eric Heitz and Eugene d'Eon, EGSR 2014.
 * https://hal.inria.fr/hal-00996995v2/document */

ccl_device_forceinline float3 microfacet_beckmann_sample_vndf(const float3 wi,
                                                              const float alpha_x,
                                                              const float alpha_y,
                                                              const float randu,
                                                              const float randv)
{
  /* 1. stretch wi */
  float3 wi_ = make_float3(alpha_x * wi.x, alpha_y * wi.y, wi.z);
  wi_ = normalize(wi_);

  /* 2. sample P22_{wi}(x_slope, y_slope, 1, 1) */
  float slope_x, slope_y;
  float cos_phi_i = 1.0f;
  float sin_phi_i = 0.0f;

  if (wi_.z >= 0.99999f) {
    /* Special case (normal incidence). */
    const float r = sqrtf(-logf(randu));
    const float phi = M_2PI_F * randv;
    slope_x = r * cosf(phi);
    slope_y = r * sinf(phi);
  }
  else {
    /* Precomputations. */
    const float cos_theta_i = wi_.z;
    const float sin_theta_i = sin_from_cos(cos_theta_i);
    const float tan_theta_i = sin_theta_i / cos_theta_i;
    const float cot_theta_i = 1.0f / tan_theta_i;
    const float erf_a = fast_erff(cot_theta_i);
    const float exp_a2 = expf(-cot_theta_i * cot_theta_i);
    const float SQRT_PI_INV = 0.56418958354f;

    float invlen = 1.0f / sin_theta_i;
    cos_phi_i = wi_.x * invlen;
    sin_phi_i = wi_.y * invlen;

    /* Based on paper from Wenzel Jakob
     * An Improved Visible Normal Sampling Routine for the Beckmann Distribution
     *
     * http://www.mitsuba-renderer.org/~wenzel/files/visnormal.pdf
     *
     * Reformulation from OpenShadingLanguage which avoids using inverse
     * trigonometric functions.
     */

    /* Sample slope X.
     *
     * Compute a coarse approximation using the approximation:
     *   exp(-ierf(x)^2) ~= 1 - x * x
     *   solve y = 1 + b + K * (1 - b * b)
     */
    const float K = tan_theta_i * SQRT_PI_INV;
    const float y_approx = randu * (1.0f + erf_a + K * (1 - erf_a * erf_a));
    const float y_exact = randu * (1.0f + erf_a + K * exp_a2);
    float b = K > 0 ? (0.5f - sqrtf(K * (K - y_approx + 1.0f) + 0.25f)) / K : y_approx - 1.0f;

    float inv_erf = fast_ierff(b);
    float2 begin = make_float2(-1.0f, -y_exact);
    float2 end = make_float2(erf_a, 1.0f + erf_a + K * exp_a2 - y_exact);
    float2 current = make_float2(b, 1.0f + b + K * expf(-sqr(inv_erf)) - y_exact);

    /* Find root in a monotonic interval using newton method, under given precision and maximal
     * iterations. Falls back to bisection if newton step produces results outside of the valid
     * interval. */
    const float precision = 1e-6f;
    const int max_iter = 3;
    int iter = 0;
    while (fabsf(current.y) > precision && iter++ < max_iter) {
      if (signf(begin.y) == signf(current.y)) {
        begin.x = current.x;
        begin.y = current.y;
      }
      else {
        end.x = current.x;
      }
      const float newton_x = current.x - current.y / (1.0f - inv_erf * tan_theta_i);
      current.x = (newton_x >= begin.x && newton_x <= end.x) ? newton_x : 0.5f * (begin.x + end.x);
      inv_erf = fast_ierff(current.x);
      current.y = 1.0f + current.x + K * expf(-sqr(inv_erf)) - y_exact;
    }

    slope_x = inv_erf;
    slope_y = fast_ierff(2.0f * randv - 1.0f);
  }

  /* 3. rotate */
  float tmp = cos_phi_i * slope_x - sin_phi_i * slope_y;
  slope_y = sin_phi_i * slope_x + cos_phi_i * slope_y;
  slope_x = tmp;

  /* 4. unstretch */
  slope_x = alpha_x * slope_x;
  slope_y = alpha_y * slope_y;

  /* 5. compute normal */
  return normalize(make_float3(-slope_x, -slope_y, 1.0f));
}

/* GGX VNDF importance sampling algorithm from:
 * Sampling the GGX Distribution of Visible Normals.
 * Eric Heitz, JCGT Vol. 7, No. 4, 2018.
 * https://jcgt.org/published/0007/04/01/ */
ccl_device_forceinline float3 microfacet_ggx_sample_vndf(const float3 wi,
                                                         const float alpha_x,
                                                         const float alpha_y,
                                                         const float randu,
                                                         const float randv)
{
  /* Section 3.2: Transforming the view direction to the hemisphere configuration. */
  float3 wi_ = normalize(make_float3(alpha_x * wi.x, alpha_y * wi.y, wi.z));

  /* Section 4.1: Orthonormal basis. */
  float lensq = sqr(wi_.x) + sqr(wi_.y);
  float3 T1, T2;
  if (lensq > 1e-7f) {
    T1 = make_float3(-wi_.y, wi_.x, 0.0f) * inversesqrtf(lensq);
    T2 = cross(wi_, T1);
  }
  else {
    /* Normal incidence, any basis is fine. */
    T1 = make_float3(1.0f, 0.0f, 0.0f);
    T2 = make_float3(0.0f, 1.0f, 0.0f);
  }

  /* Section 4.2: Parameterization of the projected area. */
  float2 t = concentric_sample_disk(randu, randv);
  t.y = mix(safe_sqrtf(1.0f - sqr(t.x)), t.y, 0.5f * (1.0f + wi_.z));

  /* Section 4.3: Reprojection onto hemisphere. */
  float3 H_ = t.x * T1 + t.y * T2 + safe_sqrtf(1.0f - len_squared(t)) * wi_;

  /* Section 3.4: Transforming the normal back to the ellipsoid configuration. */
  return normalize(make_float3(alpha_x * H_.x, alpha_y * H_.y, max(0.0f, H_.z)));
}

/* Calculate the reflection color
 *
 * If fresnel is used, the color is an interpolation of the F0 color and white
 * with respect to the fresnel
 *
 * Else it is simply white
 */
ccl_device_forceinline Spectrum microfacet_fresnel(ccl_private const MicrofacetBsdf *bsdf,
                                                   const float3 wi,
                                                   const float3 H,
                                                   const bool refraction)
{
  if (bsdf->fresnel_type == MicrofacetFresnel::PRINCIPLED_V1) {
    /* For Principled v1 Glass, cspec0 only provides the specular tint, the main Fresnel term
     * is implicit in the phase function of the multi-scattering code.
     * Therefore, for Glass, include it here on top of the Principled-specific tints. */
    float F = 1.0f;
    if (bsdf->type == CLOSURE_BSDF_MICROFACET_MULTI_GGX_GLASS_ID) {
      F = fresnel_dielectric_cos(dot(wi, H), bsdf->ior);
    }

    ccl_private FresnelPrincipledV1 *fresnel = (ccl_private FresnelPrincipledV1 *)bsdf->fresnel;
    if (refraction) {
      return (1.0f - F) * fresnel->color;
    }
    else {
      return F * interpolate_fresnel_color(wi, H, bsdf->ior, fresnel->cspec0);
    }
  }
  else if (bsdf->fresnel_type == MicrofacetFresnel::DIELECTRIC) {
    const float F = fresnel_dielectric_cos(dot(wi, H), bsdf->ior);
    return make_spectrum(refraction ? 1.0f - F : F);
  }
  else if (bsdf->fresnel_type == MicrofacetFresnel::DIELECTRIC_TINT) {
    ccl_private FresnelDielectricTint *fresnel = (ccl_private FresnelDielectricTint *)
                                                     bsdf->fresnel;
    const float F = fresnel_dielectric_cos(dot(wi, H), bsdf->ior);
    return refraction ? (1.0f - F) * fresnel->transmission_tint : F * fresnel->reflection_tint;
  }
  else if (bsdf->fresnel_type == MicrofacetFresnel::CONDUCTOR) {
    kernel_assert(!refraction);
    ccl_private FresnelConductor *fresnel = (ccl_private FresnelConductor *)bsdf->fresnel;
    return fresnel_conductor(dot(wi, H), fresnel->n, fresnel->k);
  }
  else if (bsdf->fresnel_type == MicrofacetFresnel::GENERALIZED_SCHLICK) {
    ccl_private FresnelGeneralizedSchlick *fresnel = (ccl_private FresnelGeneralizedSchlick *)
                                                         bsdf->fresnel;
    float cosI = dot(wi, H);
    if (bsdf->ior < 1.0f) {
      /* When going from a higher to a lower IOR, we must use the transmitted angle. */
      float sinT2 = (1.0f - sqr(cosI)) / sqr(bsdf->ior);
      if (sinT2 >= 1.0f) {
        /* Total internal reflection */
        return refraction ? zero_spectrum() : fresnel->reflection_tint;
      }
      cosI = safe_sqrtf(1.0f - sinT2);
    }
    /* TODO(lukas): Is a special case for exponent==5 worth it? */
    const float s = powf(1.0f - cosI, fresnel->exponent);
    const Spectrum F = mix(fresnel->f0, fresnel->f90, s);
    if (refraction) {
      return (one_spectrum() - F) * fresnel->transmission_tint;
    }
    else {
      return F * fresnel->reflection_tint;
    }
  }
  else if (bsdf->fresnel_type == MicrofacetFresnel::CONSTANT) {
    /* CONSTANT is only used my MultiGGX, which doesn't call this function.
     * Therefore, this case only happens when determining the albedo of a MultiGGX closure.
     * In that case, the constant color is already baked into the weight.
     * So, just return the main dielectric Fresnel term for Glass and 1.0 for Glossy. */
    if (bsdf->type == CLOSURE_BSDF_MICROFACET_MULTI_GGX_GLASS_ID) {
      const float F = fresnel_dielectric_cos(dot(wi, H), bsdf->ior);
      return make_spectrum(refraction ? (1.0f - F) : F);
    }
    else {
      return refraction ? zero_spectrum() : one_spectrum();
    }
  }
  else {
    return one_spectrum();
  }
}

/* This function estimates the albedo of the BSDF (NOT including the bsdf->weight) as caused by
 * the applied Fresnel model for the given view direction.
 * The base microfacet model is assumed to have an albedo of 1, but e.g. a reflection-only
 * closure with Fresnel applied can end up having a very low overall albedo.
 * This is used to adjust the sample weight, as well as for the Diff/Gloss/Trans Color pass
 * and the Denoising Albedo pass. */
ccl_device Spectrum bsdf_microfacet_estimate_fresnel(ccl_private const ShaderData *sd,
                                                     ccl_private const MicrofacetBsdf *bsdf,
                                                     const bool reflection,
                                                     const bool transmission)
{
  const bool m_refraction = CLOSURE_IS_REFRACTION(bsdf->type);
  const bool m_glass = CLOSURE_IS_GLASS(bsdf->type);
  const bool m_reflection = !(m_refraction || m_glass);

  Spectrum albedo = zero_spectrum();
  if (reflection && (m_reflection || m_glass)) {
    /* BSDF has a reflective lobe. */
    albedo += microfacet_fresnel(bsdf, sd->wi, bsdf->N, false);
  }
  if (transmission && (m_refraction || m_glass)) {
    /* BSDF has a refractive lobe (unless there's TIR). */
    albedo += microfacet_fresnel(bsdf, sd->wi, bsdf->N, true);
  }

  return albedo;
}

/* Generalized Trowbridge-Reitz for clearcoat. */
ccl_device_forceinline float bsdf_clearcoat_D(float alpha2, float cos_NH)
{
  if (alpha2 >= 1.0f) {
    return M_1_PI_F;
  }

  const float t = 1.0f + (alpha2 - 1.0f) * cos_NH * cos_NH;
  return (alpha2 - 1.0f) / (M_PI_F * logf(alpha2) * t);
}

/* Smith shadowing-masking term, here in the non-separable form.
 * For details, see:
 * Understanding the Masking-Shadowing Function in Microfacet-Based BRDFs.
 * Eric Heitz, JCGT Vol. 3, No. 2, 2014.
 * https://jcgt.org/published/0003/02/03/ */
template<MicrofacetType m_type>
ccl_device_inline float bsdf_lambda_from_sqr_alpha_tan_n(float sqr_alpha_tan_n)
{
  if (m_type == MicrofacetType::GGX) {
    /* Equation 72. */
    return 0.5f * (sqrtf(1.0f + sqr_alpha_tan_n) - 1.0f);
  }
  else {
    kernel_assert(m_type == MicrofacetType::BECKMANN);
    /* Approximation from below Equation 69. */
    if (sqr_alpha_tan_n < 0.39f) {
      /* Equivalent to a >= 1.6f, but also handles sqr_alpha_tan_n == 0.0f cleanly. */
      return 0.0f;
    }

    const float a = inversesqrtf(sqr_alpha_tan_n);
    return ((0.396f * a - 1.259f) * a + 1.0f) / ((2.181f * a + 3.535f) * a);
  }
}

template<MicrofacetType m_type> ccl_device_inline float bsdf_lambda(float alpha2, float cos_N)
{
  return bsdf_lambda_from_sqr_alpha_tan_n<m_type>(alpha2 * fmaxf(1.0f / sqr(cos_N) - 1.0f, 0.0f));
}

template<MicrofacetType m_type>
ccl_device_inline float bsdf_aniso_lambda(float alpha_x, float alpha_y, float3 V)
{
  const float sqr_alpha_tan_n = (sqr(alpha_x * V.x) + sqr(alpha_y * V.y)) / sqr(V.z);
  return bsdf_lambda_from_sqr_alpha_tan_n<m_type>(sqr_alpha_tan_n);
}

/* Combined shadowing-masking term. */
template<MicrofacetType m_type>
ccl_device_inline float bsdf_G(float alpha2, float cos_NI, float cos_NO)
{
  return 1.0f / (1.0f + bsdf_lambda<m_type>(alpha2, cos_NI) + bsdf_lambda<m_type>(alpha2, cos_NO));
}

/* Normal distribution function. */
template<MicrofacetType m_type> ccl_device_inline float bsdf_D(float alpha2, float cos_NH)
{
  const float cos_NH2 = sqr(cos_NH);

  if (m_type == MicrofacetType::BECKMANN) {
    return expf((1.0f - 1.0f / cos_NH2) / alpha2) / (M_PI_F * alpha2 * sqr(cos_NH2));
  }
  else {
    kernel_assert(m_type == MicrofacetType::GGX);
    return alpha2 / (M_PI_F * sqr(1.0f + (alpha2 - 1.0f) * cos_NH2));
  }
}

template<MicrofacetType m_type>
ccl_device_inline float bsdf_aniso_D(float alpha_x, float alpha_y, float3 H)
{
  H /= make_float3(alpha_x, alpha_y, 1.0f);

  const float cos_NH2 = sqr(H.z);
  const float alpha2 = alpha_x * alpha_y;

  if (m_type == MicrofacetType::BECKMANN) {
    return expf(-(sqr(H.x) + sqr(H.y)) / cos_NH2) / (M_PI_F * alpha2 * sqr(cos_NH2));
  }
  else {
    kernel_assert(m_type == MicrofacetType::GGX);
    return M_1_PI_F / (alpha2 * sqr(len_squared(H)));
  }
}

template<MicrofacetType m_type>
ccl_device Spectrum bsdf_microfacet_eval(ccl_private const ShaderClosure *sc,
                                         const float3 Ng,
                                         const float3 wi,
                                         const float3 wo,
                                         ccl_private float *pdf)
{
  if (m_type == MicrofacetType::SHARP) {
    *pdf = 0.0f;
    return zero_spectrum();
  }

  ccl_private const MicrofacetBsdf *bsdf = (ccl_private const MicrofacetBsdf *)sc;
  /* Refraction: Only consider BTDF
   * Glass: Consider both BRDF and BTDF, mix based on Fresnel
   * Reflection: Only consider BRDF */
  const bool m_refraction = CLOSURE_IS_REFRACTION(bsdf->type);
  const bool m_glass = CLOSURE_IS_GLASS(bsdf->type);
  const bool m_reflection = !(m_refraction || m_glass);

  const float3 N = bsdf->N;
  const float cos_NI = dot(N, wi);
  const float cos_NO = dot(N, wo);
  const float cos_NgO = dot(Ng, wo);

  const float alpha_x = bsdf->alpha_x;
  const float alpha_y = bsdf->alpha_y;

  const bool is_transmission = (cos_NO < 0.0f);

  /* Check whether the pair of directions is valid for evaluation:
   * - Incoming direction has to be in the upper hemisphere (Cycles convention)
   * - Specular cases can't be evaluated, only sampled.
   * - The outgoing direction has to be the in the same hemisphere w.r.t. both normals.
   * - Purely reflective closures can't have refraction.
   * - Purely refractive closures can't have reflection.
   */
  if ((cos_NI <= 0) || (alpha_x * alpha_y <= 5e-7f) || ((cos_NgO < 0.0f) != is_transmission) ||
      (is_transmission && m_reflection) || (!is_transmission && m_refraction))
  {
    *pdf = 0.0f;
    return zero_spectrum();
  }

  /* Compute half vector. */
  float3 H = is_transmission ? -(bsdf->ior * wo + wi) : (wi + wo);
  const float inv_len_H = 1.0f / len(H);
  H *= inv_len_H;

  const float cos_NH = dot(N, H);
  float D, lambdaI, lambdaO;

  /* TODO: add support for anisotropic transmission. */
  if (alpha_x == alpha_y || is_transmission) { /* Isotropic. */
    float alpha2 = alpha_x * alpha_y;

    if (bsdf->type == CLOSURE_BSDF_MICROFACET_GGX_CLEARCOAT_ID) {
      D = bsdf_clearcoat_D(alpha2, cos_NH);

      /* The masking-shadowing term for clearcoat has a fixed alpha of 0.25
       * => alpha2 = 0.25 * 0.25 */
      alpha2 = 0.0625f;
    }
    else {
      D = bsdf_D<m_type>(alpha2, cos_NH);
    }

    lambdaI = bsdf_lambda<m_type>(alpha2, cos_NI);
    lambdaO = bsdf_lambda<m_type>(alpha2, cos_NO);
  }
  else { /* Anisotropic. */
    float3 X, Y;
    make_orthonormals_tangent(N, bsdf->T, &X, &Y);

    const float3 local_H = make_float3(dot(X, H), dot(Y, H), cos_NH);
    const float3 local_I = make_float3(dot(X, wi), dot(Y, wi), cos_NI);
    const float3 local_O = make_float3(dot(X, wo), dot(Y, wo), cos_NO);

    D = bsdf_aniso_D<m_type>(alpha_x, alpha_y, local_H);

    lambdaI = bsdf_aniso_lambda<m_type>(alpha_x, alpha_y, local_I);
    lambdaO = bsdf_aniso_lambda<m_type>(alpha_x, alpha_y, local_O);
  }

  float common = D / cos_NI *
                 (is_transmission ? sqr(bsdf->ior * inv_len_H) * fabsf(dot(H, wi) * dot(H, wo)) :
                                    0.25f);

  float lobe_pdf = 1.0f;
  if (m_glass) {
    float fresnel = fresnel_dielectric_cos(dot(H, wi), bsdf->ior);
    float reflect_pdf = (fresnel == 1.0f) ? 1.0f : clamp(fresnel, 0.125f, 0.875f);
    lobe_pdf = is_transmission ? (1.0f - reflect_pdf) : reflect_pdf;
  }

  *pdf = common * lobe_pdf / (1.0f + lambdaI);

  const Spectrum F = microfacet_fresnel(bsdf, wi, H, is_transmission);
  return F * common / (1.0f + lambdaO + lambdaI);
}

template<MicrofacetType m_type>
ccl_device int bsdf_microfacet_sample(ccl_private const ShaderClosure *sc,
                                      const int path_flag,
                                      float3 Ng,
                                      float3 wi,
                                      float randu,
                                      float randv,
                                      float randw,
                                      ccl_private Spectrum *eval,
                                      ccl_private float3 *wo,
                                      ccl_private float *pdf,
                                      ccl_private float2 *sampled_roughness,
                                      ccl_private float *eta)
{
  ccl_private const MicrofacetBsdf *bsdf = (ccl_private const MicrofacetBsdf *)sc;

  const float m_eta = bsdf->ior;
  const bool m_refraction = CLOSURE_IS_REFRACTION(bsdf->type);
  const bool m_glass = CLOSURE_IS_GLASS(bsdf->type);
  const bool m_reflection = !(m_refraction || m_glass);
  const float alpha_x = bsdf->alpha_x;
  const float alpha_y = bsdf->alpha_y;
  bool m_singular = (m_type == MicrofacetType::SHARP) || (alpha_x * alpha_y <= 5e-7f);

  const float3 N = bsdf->N;
  const float cos_NI = dot(N, wi);
  if (cos_NI <= 0) {
    *eval = zero_spectrum();
    *pdf = 0.0f;
    return (m_reflection ? LABEL_REFLECT : LABEL_TRANSMIT) |
           (m_singular ? LABEL_SINGULAR : LABEL_GLOSSY);
  }

  float3 H;
  float cos_NH, cos_HI;
  float3 local_H, local_I, X, Y; /* Needed for anisotropic microfacets later. */
  if (m_singular) {
    H = N;
    cos_NH = 1.0f;
    cos_HI = cos_NI;
  }
  else {
    if (alpha_x == alpha_y) {
      make_orthonormals(N, &X, &Y);
    }
    else {
      make_orthonormals_tangent(N, bsdf->T, &X, &Y);
    }

    /* Importance sampling with distribution of visible normals. Vectors are transformed to local
     * space before and after sampling. */
    local_I = make_float3(dot(X, wi), dot(Y, wi), cos_NI);
    if (m_type == MicrofacetType::GGX) {
      local_H = microfacet_ggx_sample_vndf(local_I, alpha_x, alpha_y, randu, randv);
    }
    else {
      /* m_type == MicrofacetType::BECKMANN */
      local_H = microfacet_beckmann_sample_vndf(local_I, alpha_x, alpha_y, randu, randv);
    }

    H = X * local_H.x + Y * local_H.y + N * local_H.z;
    cos_NH = local_H.z;
    cos_HI = dot(H, wi);
  }

  bool valid;
  bool do_refract;
  float lobe_pdf;
  if (m_refraction || m_glass) {
    bool inside;
    float fresnel = fresnel_dielectric(m_eta, H, wi, wo, &inside);
    valid = !inside;

    /* For glass closures, we decide between reflection and refraction here. */
    if (m_glass) {
      if (fresnel == 1.0f) {
        /* TIR, reflection is the only option. */
        do_refract = false;
        lobe_pdf = 1.0f;
      }
      else {
        /* Decide between reflection and refraction, using defensive sampling to avoid
         * excessive noise for reflection highlights. */
        float reflect_pdf = (path_flag & PATH_RAY_CAMERA) ? clamp(fresnel, 0.125f, 0.875f) :
                                                            fresnel;
        do_refract = (randw >= reflect_pdf);
        lobe_pdf = do_refract ? (1.0f - reflect_pdf) : reflect_pdf;
      }
    }
    else {
      /* For pure refractive closures, refraction is the only option. */
      do_refract = true;
      lobe_pdf = 1.0f;
      valid = valid && (fresnel != 1.0f);
    }
  }
  else {
    /* Pure reflective closure, reflection is the only option. */
    valid = true;
    lobe_pdf = 1.0f;
    do_refract = false;
  }

  int label;
  if (do_refract) {
    /* wo was already set to the refracted direction by fresnel_dielectric. */
    // valid = valid && (dot(Ng, *wo) < 0);
    label = LABEL_TRANSMIT;
    /* If the IOR is close enough to 1.0, just treat the interaction as specular. */
    m_singular = m_singular || (fabsf(m_eta - 1.0f) < 1e-4f);
  }
  else {
    /* Eq. 39 - compute actual reflected direction */
    *wo = 2 * cos_HI * H - wi;
    valid = valid && (dot(Ng, *wo) > 0);
    label = LABEL_REFLECT;
  }

  if (!valid) {
    *eval = zero_spectrum();
    *pdf = 0.0f;
    return label | (m_singular ? LABEL_SINGULAR : LABEL_GLOSSY);
  }

  if (m_singular) {
    label |= LABEL_SINGULAR;
    /* Some high number for MIS. */
    *pdf = lobe_pdf * 1e6f;
    *eval = make_spectrum(1e6f) * microfacet_fresnel(bsdf, wi, H, do_refract);
  }
  else {
    label |= LABEL_GLOSSY;
    float cos_NO = dot(N, *wo);
    float D, lambdaI, lambdaO;

    /* TODO: add support for anisotropic transmission. */
    if (alpha_x == alpha_y || do_refract) { /* Isotropic. */
      float alpha2 = alpha_x * alpha_y;

      if (bsdf->type == CLOSURE_BSDF_MICROFACET_GGX_CLEARCOAT_ID) {
        D = bsdf_clearcoat_D(alpha2, cos_NH);

        /* The masking-shadowing term for clearcoat has a fixed alpha of 0.25
         * => alpha2 = 0.25 * 0.25 */
        alpha2 = 0.0625f;
      }
      else {
        D = bsdf_D<m_type>(alpha2, cos_NH);
      }

      lambdaO = bsdf_lambda<m_type>(alpha2, cos_NO);
      lambdaI = bsdf_lambda<m_type>(alpha2, cos_NI);
    }
    else { /* Anisotropic. */
      const float3 local_O = make_float3(dot(X, *wo), dot(Y, *wo), cos_NO);

      D = bsdf_aniso_D<m_type>(alpha_x, alpha_y, local_H);

      lambdaO = bsdf_aniso_lambda<m_type>(alpha_x, alpha_y, local_O);
      lambdaI = bsdf_aniso_lambda<m_type>(alpha_x, alpha_y, local_I);
    }

    const float cos_HO = dot(H, *wo);
    const float common = D / cos_NI *
                         (do_refract ? fabsf(cos_HI * cos_HO) / sqr(cos_HO + cos_HI / m_eta) :
                                       0.25f);

    *pdf = common * lobe_pdf / (1.0f + lambdaI);

    const Spectrum F = microfacet_fresnel(bsdf, wi, H, do_refract);
    *eval = F * common / (1.0f + lambdaI + lambdaO);
  }

  *sampled_roughness = make_float2(alpha_x, alpha_y);
  *eta = do_refract ? 1.0f / m_eta : m_eta;

  return label;
}

/* Fresnel term setup functions. These get called after the distribution-specific setup functions
 * like bsdf_microfacet_ggx_setup. */

ccl_device void bsdf_microfacet_setup_fresnel_principledv1(
    ccl_private MicrofacetBsdf *bsdf,
    ccl_private const ShaderData *sd,
    ccl_private FresnelPrincipledV1 *fresnel)
{
  fresnel->cspec0 = saturate(fresnel->cspec0);

  bsdf->fresnel_type = MicrofacetFresnel::PRINCIPLED_V1;
  bsdf->fresnel = fresnel;
  bsdf->sample_weight *= average(bsdf_microfacet_estimate_fresnel(sd, bsdf, true, true));
}

ccl_device void bsdf_microfacet_setup_fresnel_conductor(ccl_private MicrofacetBsdf *bsdf,
                                                        ccl_private const ShaderData *sd,
                                                        ccl_private FresnelConductor *fresnel)
{
  bsdf->fresnel_type = MicrofacetFresnel::CONDUCTOR;
  bsdf->fresnel = fresnel;
  bsdf->sample_weight *= average(bsdf_microfacet_estimate_fresnel(sd, bsdf, true, true));
}

ccl_device void bsdf_microfacet_setup_fresnel_dielectric_tint(
    ccl_private MicrofacetBsdf *bsdf,
    ccl_private const ShaderData *sd,
    ccl_private FresnelDielectricTint *fresnel)
{
  bsdf->fresnel_type = MicrofacetFresnel::DIELECTRIC_TINT;
  bsdf->fresnel = fresnel;
  bsdf->sample_weight *= average(bsdf_microfacet_estimate_fresnel(sd, bsdf, true, true));
}

ccl_device void bsdf_microfacet_setup_fresnel_generalized_schlick(
    ccl_private MicrofacetBsdf *bsdf,
    ccl_private const ShaderData *sd,
    ccl_private FresnelGeneralizedSchlick *fresnel)
{
  bsdf->fresnel_type = MicrofacetFresnel::GENERALIZED_SCHLICK;
  bsdf->fresnel = fresnel;
  bsdf->sample_weight *= average(bsdf_microfacet_estimate_fresnel(sd, bsdf, true, true));
}

/* GGX microfacet with Smith shadow-masking from:
 *
 * Microfacet Models for Refraction through Rough Surfaces
 * B. Walter, S. R. Marschner, H. Li, K. E. Torrance, EGSR 2007
 *
 * Anisotropic from:
 *
 * Understanding the Masking-Shadowing Function in Microfacet-Based BRDFs
 * E. Heitz, Research Report 2014
 *
 * Anisotropy is only supported for reflection currently, but adding it for
 * transmission is just a matter of copying code from reflection if needed. */

ccl_device int bsdf_microfacet_ggx_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->alpha_x = saturatef(bsdf->alpha_x);
  bsdf->alpha_y = saturatef(bsdf->alpha_y);

  bsdf->fresnel_type = MicrofacetFresnel::NONE;
  bsdf->type = CLOSURE_BSDF_MICROFACET_GGX_ID;

  return SD_BSDF | SD_BSDF_HAS_EVAL;
}

ccl_device int bsdf_microfacet_ggx_clearcoat_setup(ccl_private MicrofacetBsdf *bsdf,
                                                   ccl_private const ShaderData *sd)
{
  bsdf->alpha_x = saturatef(bsdf->alpha_x);
  bsdf->alpha_y = bsdf->alpha_x;

  bsdf->fresnel_type = MicrofacetFresnel::DIELECTRIC;
  bsdf->type = CLOSURE_BSDF_MICROFACET_GGX_CLEARCOAT_ID;
  bsdf->sample_weight *= average(bsdf_microfacet_estimate_fresnel(sd, bsdf, true, true));

  return SD_BSDF | SD_BSDF_HAS_EVAL;
}

ccl_device int bsdf_microfacet_ggx_refraction_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->alpha_x = saturatef(bsdf->alpha_x);
  bsdf->alpha_y = bsdf->alpha_x;

  bsdf->fresnel_type = MicrofacetFresnel::NONE;
  bsdf->type = CLOSURE_BSDF_MICROFACET_GGX_REFRACTION_ID;

  return SD_BSDF | SD_BSDF_HAS_EVAL | SD_BSDF_HAS_TRANSMISSION;
}

ccl_device int bsdf_microfacet_ggx_glass_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->alpha_x = saturatef(bsdf->alpha_x);
  bsdf->alpha_y = bsdf->alpha_x;

  bsdf->fresnel_type = MicrofacetFresnel::DIELECTRIC;
  bsdf->type = CLOSURE_BSDF_MICROFACET_GGX_GLASS_ID;

  return SD_BSDF | SD_BSDF_HAS_EVAL | SD_BSDF_HAS_TRANSMISSION;
}

ccl_device void bsdf_microfacet_ggx_blur(ccl_private ShaderClosure *sc, float roughness)
{
  ccl_private MicrofacetBsdf *bsdf = (ccl_private MicrofacetBsdf *)sc;

  bsdf->alpha_x = fmaxf(roughness, bsdf->alpha_x);
  bsdf->alpha_y = fmaxf(roughness, bsdf->alpha_y);
}

ccl_device Spectrum bsdf_microfacet_ggx_eval(ccl_private const ShaderClosure *sc,
                                             const float3 Ng,
                                             const float3 wi,
                                             const float3 wo,
                                             ccl_private float *pdf)
{
  return bsdf_microfacet_eval<MicrofacetType::GGX>(sc, Ng, wi, wo, pdf);
}

ccl_device int bsdf_microfacet_ggx_sample(ccl_private const ShaderClosure *sc,
                                          const int path_flag,
                                          float3 Ng,
                                          float3 wi,
                                          float randu,
                                          float randv,
                                          float randw,
                                          ccl_private Spectrum *eval,
                                          ccl_private float3 *wo,
                                          ccl_private float *pdf,
                                          ccl_private float2 *sampled_roughness,
                                          ccl_private float *eta)
{
  return bsdf_microfacet_sample<MicrofacetType::GGX>(
      sc, path_flag, Ng, wi, randu, randv, randw, eval, wo, pdf, sampled_roughness, eta);
}

/* Beckmann microfacet with Smith shadow-masking from:
 *
 * Microfacet Models for Refraction through Rough Surfaces
 * B. Walter, S. R. Marschner, H. Li, K. E. Torrance, EGSR 2007 */

ccl_device int bsdf_microfacet_beckmann_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->alpha_x = saturatef(bsdf->alpha_x);
  bsdf->alpha_y = saturatef(bsdf->alpha_y);

  bsdf->fresnel_type = MicrofacetFresnel::NONE;
  bsdf->type = CLOSURE_BSDF_MICROFACET_BECKMANN_ID;
  return SD_BSDF | SD_BSDF_HAS_EVAL;
}

ccl_device int bsdf_microfacet_beckmann_refraction_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->alpha_x = saturatef(bsdf->alpha_x);
  bsdf->alpha_y = bsdf->alpha_x;

  bsdf->fresnel_type = MicrofacetFresnel::NONE;
  bsdf->type = CLOSURE_BSDF_MICROFACET_BECKMANN_REFRACTION_ID;
  return SD_BSDF | SD_BSDF_HAS_EVAL | SD_BSDF_HAS_TRANSMISSION;
}

ccl_device int bsdf_microfacet_beckmann_glass_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->alpha_x = saturatef(bsdf->alpha_x);
  bsdf->alpha_y = bsdf->alpha_x;

  bsdf->fresnel_type = MicrofacetFresnel::DIELECTRIC;
  bsdf->type = CLOSURE_BSDF_MICROFACET_BECKMANN_GLASS_ID;
  return SD_BSDF | SD_BSDF_HAS_EVAL | SD_BSDF_HAS_TRANSMISSION;
}

ccl_device void bsdf_microfacet_beckmann_blur(ccl_private ShaderClosure *sc, float roughness)
{
  ccl_private MicrofacetBsdf *bsdf = (ccl_private MicrofacetBsdf *)sc;

  bsdf->alpha_x = fmaxf(roughness, bsdf->alpha_x);
  bsdf->alpha_y = fmaxf(roughness, bsdf->alpha_y);
}

ccl_device Spectrum bsdf_microfacet_beckmann_eval(ccl_private const ShaderClosure *sc,
                                                  const float3 Ng,
                                                  const float3 wi,
                                                  const float3 wo,
                                                  ccl_private float *pdf)
{
  return bsdf_microfacet_eval<MicrofacetType::BECKMANN>(sc, Ng, wi, wo, pdf);
}

ccl_device int bsdf_microfacet_beckmann_sample(ccl_private const ShaderClosure *sc,
                                               const int path_flag,
                                               float3 Ng,
                                               float3 wi,
                                               float randu,
                                               float randv,
                                               float randw,
                                               ccl_private Spectrum *eval,
                                               ccl_private float3 *wo,
                                               ccl_private float *pdf,
                                               ccl_private float2 *sampled_roughness,
                                               ccl_private float *eta)
{
  return bsdf_microfacet_sample<MicrofacetType::BECKMANN>(
      sc, path_flag, Ng, wi, randu, randv, randw, eval, wo, pdf, sampled_roughness, eta);
}

/* Specular interface, not really a microfacet model but close enough that sharing code makes
 * sense. */

ccl_device int bsdf_reflection_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->fresnel_type = MicrofacetFresnel::NONE;
  bsdf->type = CLOSURE_BSDF_REFLECTION_ID;
  bsdf->alpha_x = 0.0f;
  bsdf->alpha_y = 0.0f;
  return SD_BSDF;
}

ccl_device int bsdf_refraction_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->fresnel_type = MicrofacetFresnel::NONE;
  bsdf->type = CLOSURE_BSDF_REFRACTION_ID;
  bsdf->alpha_x = 0.0f;
  bsdf->alpha_y = 0.0f;
  return SD_BSDF | SD_BSDF_HAS_TRANSMISSION;
}

ccl_device int bsdf_sharp_glass_setup(ccl_private MicrofacetBsdf *bsdf)
{
  bsdf->fresnel_type = MicrofacetFresnel::DIELECTRIC;
  bsdf->type = CLOSURE_BSDF_SHARP_GLASS_ID;
  bsdf->alpha_x = 0.0f;
  bsdf->alpha_y = 0.0f;
  return SD_BSDF | SD_BSDF_HAS_TRANSMISSION;
}

ccl_device Spectrum bsdf_microfacet_sharp_eval(ccl_private const ShaderClosure *sc,
                                               const float3 Ng,
                                               const float3 wi,
                                               const float3 wo,
                                               ccl_private float *pdf)
{
  return bsdf_microfacet_eval<MicrofacetType::SHARP>(sc, Ng, wi, wo, pdf);
}

ccl_device int bsdf_microfacet_sharp_sample(ccl_private const ShaderClosure *sc,
                                            const int path_flag,
                                            float3 Ng,
                                            float3 wi,
                                            float randu,
                                            float randv,
                                            float randw,
                                            ccl_private Spectrum *eval,
                                            ccl_private float3 *wo,
                                            ccl_private float *pdf,
                                            ccl_private float2 *sampled_roughness,
                                            ccl_private float *eta)
{
  return bsdf_microfacet_sample<MicrofacetType::SHARP>(
      sc, path_flag, Ng, wi, randu, randv, randw, eval, wo, pdf, sampled_roughness, eta);
}

CCL_NAMESPACE_END
