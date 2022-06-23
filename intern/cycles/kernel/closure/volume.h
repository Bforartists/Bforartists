/* SPDX-License-Identifier: Apache-2.0
 * Copyright 2011-2022 Blender Foundation */

#pragma once

CCL_NAMESPACE_BEGIN

/* VOLUME EXTINCTION */

ccl_device void volume_extinction_setup(ccl_private ShaderData *sd, float3 weight)
{
  if (sd->flag & SD_EXTINCTION) {
    sd->closure_transparent_extinction += weight;
  }
  else {
    sd->flag |= SD_EXTINCTION;
    sd->closure_transparent_extinction = weight;
  }
}

/* HENYEY-GREENSTEIN CLOSURE */

typedef struct HenyeyGreensteinVolume {
  SHADER_CLOSURE_BASE;

  float g;
} HenyeyGreensteinVolume;

static_assert(sizeof(ShaderClosure) >= sizeof(HenyeyGreensteinVolume),
              "HenyeyGreensteinVolume is too large!");

/* Given cosine between rays, return probability density that a photon bounces
 * to that direction. The g parameter controls how different it is from the
 * uniform sphere. g=0 uniform diffuse-like, g=1 close to sharp single ray. */
ccl_device float single_peaked_henyey_greenstein(float cos_theta, float g)
{
  return ((1.0f - g * g) / safe_powf(1.0f + g * g - 2.0f * g * cos_theta, 1.5f)) *
         (M_1_PI_F * 0.25f);
};

ccl_device int volume_henyey_greenstein_setup(ccl_private HenyeyGreensteinVolume *volume)
{
  volume->type = CLOSURE_VOLUME_HENYEY_GREENSTEIN_ID;

  /* clamp anisotropy to avoid delta function */
  volume->g = signf(volume->g) * min(fabsf(volume->g), 1.0f - 1e-3f);

  return SD_SCATTER;
}

ccl_device float3 volume_henyey_greenstein_eval_phase(ccl_private const ShaderVolumeClosure *svc,
                                                      const float3 I,
                                                      float3 omega_in,
                                                      ccl_private float *pdf)
{
  float g = svc->g;

  /* note that I points towards the viewer */
  if (fabsf(g) < 1e-3f) {
    *pdf = M_1_PI_F * 0.25f;
  }
  else {
    float cos_theta = dot(-I, omega_in);
    *pdf = single_peaked_henyey_greenstein(cos_theta, g);
  }

  return make_float3(*pdf, *pdf, *pdf);
}

ccl_device float3
henyey_greenstrein_sample(float3 D, float g, float randu, float randv, ccl_private float *pdf)
{
  /* match pdf for small g */
  float cos_theta;
  bool isotropic = fabsf(g) < 1e-3f;

  if (isotropic) {
    cos_theta = (1.0f - 2.0f * randu);
    if (pdf) {
      *pdf = M_1_PI_F * 0.25f;
    }
  }
  else {
    float k = (1.0f - g * g) / (1.0f - g + 2.0f * g * randu);
    cos_theta = (1.0f + g * g - k * k) / (2.0f * g);
    if (pdf) {
      *pdf = single_peaked_henyey_greenstein(cos_theta, g);
    }
  }

  float sin_theta = safe_sqrtf(1.0f - cos_theta * cos_theta);
  float phi = M_2PI_F * randv;
  float3 dir = make_float3(sin_theta * cosf(phi), sin_theta * sinf(phi), cos_theta);

  float3 T, B;
  make_orthonormals(D, &T, &B);
  dir = dir.x * T + dir.y * B + dir.z * D;

  return dir;
}

ccl_device int volume_henyey_greenstein_sample(ccl_private const ShaderVolumeClosure *svc,
                                               float3 I,
                                               float3 dIdx,
                                               float3 dIdy,
                                               float randu,
                                               float randv,
                                               ccl_private float3 *eval,
                                               ccl_private float3 *omega_in,
                                               ccl_private float3 *domega_in_dx,
                                               ccl_private float3 *domega_in_dy,
                                               ccl_private float *pdf)
{
  float g = svc->g;

  /* note that I points towards the viewer and so is used negated */
  *omega_in = henyey_greenstrein_sample(-I, g, randu, randv, pdf);
  *eval = make_float3(*pdf, *pdf, *pdf); /* perfect importance sampling */

#ifdef __RAY_DIFFERENTIALS__
  /* todo: implement ray differential estimation */
  *domega_in_dx = make_float3(0.0f, 0.0f, 0.0f);
  *domega_in_dy = make_float3(0.0f, 0.0f, 0.0f);
#endif

  return LABEL_VOLUME_SCATTER;
}

/* VOLUME CLOSURE */

ccl_device float3 volume_phase_eval(ccl_private const ShaderData *sd,
                                    ccl_private const ShaderVolumeClosure *svc,
                                    float3 omega_in,
                                    ccl_private float *pdf)
{
  return volume_henyey_greenstein_eval_phase(svc, sd->I, omega_in, pdf);
}

ccl_device int volume_phase_sample(ccl_private const ShaderData *sd,
                                   ccl_private const ShaderVolumeClosure *svc,
                                   float randu,
                                   float randv,
                                   ccl_private float3 *eval,
                                   ccl_private float3 *omega_in,
                                   ccl_private differential3 *domega_in,
                                   ccl_private float *pdf)
{
  return volume_henyey_greenstein_sample(svc,
                                         sd->I,
                                         sd->dI.dx,
                                         sd->dI.dy,
                                         randu,
                                         randv,
                                         eval,
                                         omega_in,
                                         &domega_in->dx,
                                         &domega_in->dy,
                                         pdf);
}

/* Volume sampling utilities. */

/* todo: this value could be tweaked or turned into a probability to avoid
 * unnecessary work in volumes and subsurface scattering. */
#define VOLUME_THROUGHPUT_EPSILON 1e-6f

ccl_device float3 volume_color_transmittance(float3 sigma, float t)
{
  return exp(-sigma * t);
}

ccl_device float volume_channel_get(float3 value, int channel)
{
  return (channel == 0) ? value.x : ((channel == 1) ? value.y : value.z);
}

ccl_device int volume_sample_channel(float3 albedo,
                                     float3 throughput,
                                     float rand,
                                     ccl_private float3 *pdf)
{
  /* Sample color channel proportional to throughput and single scattering
   * albedo, to significantly reduce noise with many bounce, following:
   *
   * "Practical and Controllable Subsurface Scattering for Production Path
   *  Tracing". Matt Jen-Yuan Chiang, Peter Kutz, Brent Burley. SIGGRAPH 2016. */
  float3 weights = fabs(throughput * albedo);
  float sum_weights = weights.x + weights.y + weights.z;

  if (sum_weights > 0.0f) {
    *pdf = weights / sum_weights;
  }
  else {
    *pdf = make_float3(1.0f / 3.0f, 1.0f / 3.0f, 1.0f / 3.0f);
  }

  if (rand < pdf->x) {
    return 0;
  }
  else if (rand < pdf->x + pdf->y) {
    return 1;
  }
  else {
    return 2;
  }
}

CCL_NAMESPACE_END
