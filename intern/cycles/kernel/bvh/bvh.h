/* SPDX-License-Identifier: Apache-2.0
 * Copyright 2011-2022 Blender Foundation */

/* BVH
 *
 * Bounding volume hierarchy for ray tracing. We compile different variations
 * of the same BVH traversal function for faster rendering when some types of
 * primitives are not needed, using #includes to work around the lack of
 * C++ templates in OpenCL.
 *
 * Originally based on "Understanding the Efficiency of Ray Traversal on GPUs",
 * the code has been extended and modified to support more primitives and work
 * with CPU/CUDA/OpenCL. */

#pragma once

#ifdef __EMBREE__
#  include "kernel/bvh/embree.h"
#endif

#ifdef __METALRT__
#  include "kernel/bvh/metal.h"
#endif

#include "kernel/bvh/types.h"
#include "kernel/bvh/util.h"

#include "kernel/integrator/state_util.h"

CCL_NAMESPACE_BEGIN

#if !defined(__KERNEL_GPU_RAYTRACING__)

/* Regular BVH traversal */

#  include "kernel/bvh/nodes.h"

#  define BVH_FUNCTION_NAME bvh_intersect
#  define BVH_FUNCTION_FEATURES BVH_POINTCLOUD
#  include "kernel/bvh/traversal.h"

#  if defined(__HAIR__)
#    define BVH_FUNCTION_NAME bvh_intersect_hair
#    define BVH_FUNCTION_FEATURES BVH_HAIR | BVH_POINTCLOUD
#    include "kernel/bvh/traversal.h"
#  endif

#  if defined(__OBJECT_MOTION__)
#    define BVH_FUNCTION_NAME bvh_intersect_motion
#    define BVH_FUNCTION_FEATURES BVH_MOTION | BVH_POINTCLOUD
#    include "kernel/bvh/traversal.h"
#  endif

#  if defined(__HAIR__) && defined(__OBJECT_MOTION__)
#    define BVH_FUNCTION_NAME bvh_intersect_hair_motion
#    define BVH_FUNCTION_FEATURES BVH_HAIR | BVH_MOTION | BVH_POINTCLOUD
#    include "kernel/bvh/traversal.h"
#  endif

/* Subsurface scattering BVH traversal */

#  if defined(__BVH_LOCAL__)
#    define BVH_FUNCTION_NAME bvh_intersect_local
#    define BVH_FUNCTION_FEATURES BVH_HAIR
#    include "kernel/bvh/local.h"

#    if defined(__OBJECT_MOTION__)
#      define BVH_FUNCTION_NAME bvh_intersect_local_motion
#      define BVH_FUNCTION_FEATURES BVH_MOTION | BVH_HAIR
#      include "kernel/bvh/local.h"
#    endif
#  endif /* __BVH_LOCAL__ */

/* Volume BVH traversal */

#  if defined(__VOLUME__)
#    define BVH_FUNCTION_NAME bvh_intersect_volume
#    define BVH_FUNCTION_FEATURES BVH_HAIR
#    include "kernel/bvh/volume.h"

#    if defined(__OBJECT_MOTION__)
#      define BVH_FUNCTION_NAME bvh_intersect_volume_motion
#      define BVH_FUNCTION_FEATURES BVH_MOTION | BVH_HAIR
#      include "kernel/bvh/volume.h"
#    endif
#  endif /* __VOLUME__ */

/* Record all intersections - Shadow BVH traversal */

#  if defined(__SHADOW_RECORD_ALL__)
#    define BVH_FUNCTION_NAME bvh_intersect_shadow_all
#    define BVH_FUNCTION_FEATURES BVH_POINTCLOUD
#    include "kernel/bvh/shadow_all.h"

#    if defined(__HAIR__)
#      define BVH_FUNCTION_NAME bvh_intersect_shadow_all_hair
#      define BVH_FUNCTION_FEATURES BVH_HAIR | BVH_POINTCLOUD
#      include "kernel/bvh/shadow_all.h"
#    endif

#    if defined(__OBJECT_MOTION__)
#      define BVH_FUNCTION_NAME bvh_intersect_shadow_all_motion
#      define BVH_FUNCTION_FEATURES BVH_MOTION | BVH_POINTCLOUD
#      include "kernel/bvh/shadow_all.h"
#    endif

#    if defined(__HAIR__) && defined(__OBJECT_MOTION__)
#      define BVH_FUNCTION_NAME bvh_intersect_shadow_all_hair_motion
#      define BVH_FUNCTION_FEATURES BVH_HAIR | BVH_MOTION | BVH_POINTCLOUD
#      include "kernel/bvh/shadow_all.h"
#    endif

#  endif /* __SHADOW_RECORD_ALL__ */

/* Record all intersections - Volume BVH traversal. */

#  if defined(__VOLUME_RECORD_ALL__)
#    define BVH_FUNCTION_NAME bvh_intersect_volume_all
#    define BVH_FUNCTION_FEATURES BVH_HAIR
#    include "kernel/bvh/volume_all.h"

#    if defined(__OBJECT_MOTION__)
#      define BVH_FUNCTION_NAME bvh_intersect_volume_all_motion
#      define BVH_FUNCTION_FEATURES BVH_MOTION | BVH_HAIR
#      include "kernel/bvh/volume_all.h"
#    endif
#  endif /* __VOLUME_RECORD_ALL__ */

#  undef BVH_FEATURE
#  undef BVH_NAME_JOIN
#  undef BVH_NAME_EVAL
#  undef BVH_FUNCTION_FULL_NAME

#endif /* !defined(__KERNEL_GPU_RAYTRACING__) */

ccl_device_inline bool scene_intersect_valid(ccl_private const Ray *ray)
{
  /* NOTE: Due to some vectorization code  non-finite origin point might
   * cause lots of false-positive intersections which will overflow traversal
   * stack.
   * This code is a quick way to perform early output, to avoid crashes in
   * such cases.
   * From production scenes so far it seems it's enough to test first element
   * only.
   * Scene intersection may also called with empty rays for conditional trace
   * calls that evaluate to false, so filter those out.
   */
  return isfinite_safe(ray->P.x) && isfinite_safe(ray->D.x) && len_squared(ray->D) != 0.0f;
}

ccl_device_intersect bool scene_intersect(KernelGlobals kg,
                                          ccl_private const Ray *ray,
                                          const uint visibility,
                                          ccl_private Intersection *isect)
{
#ifdef __KERNEL_OPTIX__
  uint p0 = 0;
  uint p1 = 0;
  uint p2 = 0;
  uint p3 = 0;
  uint p4 = visibility;
  uint p5 = PRIMITIVE_NONE;
  uint p6 = ((uint64_t)ray) & 0xFFFFFFFF;
  uint p7 = (((uint64_t)ray) >> 32) & 0xFFFFFFFF;

  uint ray_mask = visibility & 0xFF;
  uint ray_flags = OPTIX_RAY_FLAG_ENFORCE_ANYHIT;
  if (0 == ray_mask && (visibility & ~0xFF) != 0) {
    ray_mask = 0xFF;
  }
  else if (visibility & PATH_RAY_SHADOW_OPAQUE) {
    ray_flags |= OPTIX_RAY_FLAG_TERMINATE_ON_FIRST_HIT;
  }

  optixTrace(scene_intersect_valid(ray) ? kernel_data.bvh.scene : 0,
             ray->P,
             ray->D,
             0.0f,
             ray->t,
             ray->time,
             ray_mask,
             ray_flags,
             0, /* SBT offset for PG_HITD */
             0,
             0,
             p0,
             p1,
             p2,
             p3,
             p4,
             p5,
             p6,
             p7);

  isect->t = __uint_as_float(p0);
  isect->u = __uint_as_float(p1);
  isect->v = __uint_as_float(p2);
  isect->prim = p3;
  isect->object = p4;
  isect->type = p5;

  return p5 != PRIMITIVE_NONE;
#elif defined(__METALRT__)

  if (!scene_intersect_valid(ray)) {
    isect->t = ray->t;
    isect->type = PRIMITIVE_NONE;
    return false;
  }

#  if defined(__KERNEL_DEBUG__)
  if (is_null_instance_acceleration_structure(metal_ancillaries->accel_struct)) {
    isect->t = ray->t;
    isect->type = PRIMITIVE_NONE;
    kernel_assert(!"Invalid metal_ancillaries->accel_struct pointer");
    return false;
  }

  if (is_null_intersection_function_table(metal_ancillaries->ift_default)) {
    isect->t = ray->t;
    isect->type = PRIMITIVE_NONE;
    kernel_assert(!"Invalid ift_default");
    return false;
  }
#  endif

  metal::raytracing::ray r(ray->P, ray->D, 0.0f, ray->t);
  metalrt_intersector_type metalrt_intersect;

  if (!kernel_data.bvh.have_curves) {
    metalrt_intersect.assume_geometry_type(metal::raytracing::geometry_type::triangle);
  }

  MetalRTIntersectionPayload payload;
  payload.self = ray->self;
  payload.u = 0.0f;
  payload.v = 0.0f;
  payload.visibility = visibility;

  typename metalrt_intersector_type::result_type intersection;

  uint ray_mask = visibility & 0xFF;
  if (0 == ray_mask && (visibility & ~0xFF) != 0) {
    ray_mask = 0xFF;
    /* No further intersector setup required: Default MetalRT behavior is any-hit. */
  }
  else if (visibility & PATH_RAY_SHADOW_OPAQUE) {
    /* No further intersector setup required: Shadow ray early termination is controlled by the
     * intersection handler */
  }

#  if defined(__METALRT_MOTION__)
  payload.time = ray->time;
  intersection = metalrt_intersect.intersect(r,
                                             metal_ancillaries->accel_struct,
                                             ray_mask,
                                             ray->time,
                                             metal_ancillaries->ift_default,
                                             payload);
#  else
  intersection = metalrt_intersect.intersect(
      r, metal_ancillaries->accel_struct, ray_mask, metal_ancillaries->ift_default, payload);
#  endif

  if (intersection.type == intersection_type::none) {
    isect->t = ray->t;
    isect->type = PRIMITIVE_NONE;

    return false;
  }

  isect->t = intersection.distance;

  isect->prim = payload.prim;
  isect->type = payload.type;
  isect->object = intersection.user_instance_id;

  isect->t = intersection.distance;
  if (intersection.type == intersection_type::triangle) {
    isect->u = 1.0f - intersection.triangle_barycentric_coord.y -
               intersection.triangle_barycentric_coord.x;
    isect->v = intersection.triangle_barycentric_coord.x;
  }
  else {
    isect->u = payload.u;
    isect->v = payload.v;
  }

  return isect->type != PRIMITIVE_NONE;

#else

  if (!scene_intersect_valid(ray)) {
    return false;
  }

#  ifdef __EMBREE__
  if (kernel_data.bvh.scene) {
    isect->t = ray->t;
    CCLIntersectContext ctx(kg, CCLIntersectContext::RAY_REGULAR);
    IntersectContext rtc_ctx(&ctx);
    RTCRayHit ray_hit;
    ctx.ray = ray;
    kernel_embree_setup_rayhit(*ray, ray_hit, visibility);
    rtcIntersect1(kernel_data.bvh.scene, &rtc_ctx.context, &ray_hit);
    if (ray_hit.hit.geomID != RTC_INVALID_GEOMETRY_ID &&
        ray_hit.hit.primID != RTC_INVALID_GEOMETRY_ID) {
      kernel_embree_convert_hit(kg, &ray_hit.ray, &ray_hit.hit, isect);
      return true;
    }
    return false;
  }
#  endif /* __EMBREE__ */

#  ifdef __OBJECT_MOTION__
  if (kernel_data.bvh.have_motion) {
#    ifdef __HAIR__
    if (kernel_data.bvh.have_curves) {
      return bvh_intersect_hair_motion(kg, ray, isect, visibility);
    }
#    endif /* __HAIR__ */

    return bvh_intersect_motion(kg, ray, isect, visibility);
  }
#  endif   /* __OBJECT_MOTION__ */

#  ifdef __HAIR__
  if (kernel_data.bvh.have_curves) {
    return bvh_intersect_hair(kg, ray, isect, visibility);
  }
#  endif /* __HAIR__ */

  return bvh_intersect(kg, ray, isect, visibility);
#endif   /* __KERNEL_OPTIX__ */
}

#ifdef __BVH_LOCAL__
ccl_device_intersect bool scene_intersect_local(KernelGlobals kg,
                                                ccl_private const Ray *ray,
                                                ccl_private LocalIntersection *local_isect,
                                                int local_object,
                                                ccl_private uint *lcg_state,
                                                int max_hits)
{
#  ifdef __KERNEL_OPTIX__
  uint p0 = pointer_pack_to_uint_0(lcg_state);
  uint p1 = pointer_pack_to_uint_1(lcg_state);
  uint p2 = pointer_pack_to_uint_0(local_isect);
  uint p3 = pointer_pack_to_uint_1(local_isect);
  uint p4 = local_object;
  uint p6 = ((uint64_t)ray) & 0xFFFFFFFF;
  uint p7 = (((uint64_t)ray) >> 32) & 0xFFFFFFFF;

  /* Is set to zero on miss or if ray is aborted, so can be used as return value. */
  uint p5 = max_hits;

  if (local_isect) {
    local_isect->num_hits = 0; /* Initialize hit count to zero. */
  }
  optixTrace(scene_intersect_valid(ray) ? kernel_data.bvh.scene : 0,
             ray->P,
             ray->D,
             0.0f,
             ray->t,
             ray->time,
             0xFF,
             /* Need to always call into __anyhit__kernel_optix_local_hit. */
             OPTIX_RAY_FLAG_ENFORCE_ANYHIT,
             2, /* SBT offset for PG_HITL */
             0,
             0,
             p0,
             p1,
             p2,
             p3,
             p4,
             p5,
             p6,
             p7);

  return p5;
#  elif defined(__METALRT__)
  if (!scene_intersect_valid(ray)) {
    if (local_isect) {
      local_isect->num_hits = 0;
    }
    return false;
  }

#    if defined(__KERNEL_DEBUG__)
  if (is_null_instance_acceleration_structure(metal_ancillaries->accel_struct)) {
    if (local_isect) {
      local_isect->num_hits = 0;
    }
    kernel_assert(!"Invalid metal_ancillaries->accel_struct pointer");
    return false;
  }

  if (is_null_intersection_function_table(metal_ancillaries->ift_local)) {
    if (local_isect) {
      local_isect->num_hits = 0;
    }
    kernel_assert(!"Invalid ift_local");
    return false;
  }
#    endif

  metal::raytracing::ray r(ray->P, ray->D, 0.0f, ray->t);
  metalrt_intersector_type metalrt_intersect;

  metalrt_intersect.force_opacity(metal::raytracing::forced_opacity::non_opaque);
  if (!kernel_data.bvh.have_curves) {
    metalrt_intersect.assume_geometry_type(metal::raytracing::geometry_type::triangle);
  }

  MetalRTIntersectionLocalPayload payload;
  payload.self = ray->self;
  payload.local_object = local_object;
  payload.max_hits = max_hits;
  payload.local_isect.num_hits = 0;
  if (lcg_state) {
    payload.has_lcg_state = true;
    payload.lcg_state = *lcg_state;
  }
  payload.result = false;

  typename metalrt_intersector_type::result_type intersection;

#    if defined(__METALRT_MOTION__)
  intersection = metalrt_intersect.intersect(
      r, metal_ancillaries->accel_struct, 0xFF, ray->time, metal_ancillaries->ift_local, payload);
#    else
  intersection = metalrt_intersect.intersect(
      r, metal_ancillaries->accel_struct, 0xFF, metal_ancillaries->ift_local, payload);
#    endif

  if (lcg_state) {
    *lcg_state = payload.lcg_state;
  }
  *local_isect = payload.local_isect;

  return payload.result;

#  else

  if (!scene_intersect_valid(ray)) {
    if (local_isect) {
      local_isect->num_hits = 0;
    }
    return false;
  }

#    ifdef __EMBREE__
  if (kernel_data.bvh.scene) {
    const bool has_bvh = !(kernel_data_fetch(object_flag, local_object) &
                           SD_OBJECT_TRANSFORM_APPLIED);
    CCLIntersectContext ctx(
        kg, has_bvh ? CCLIntersectContext::RAY_SSS : CCLIntersectContext::RAY_LOCAL);
    ctx.lcg_state = lcg_state;
    ctx.max_hits = max_hits;
    ctx.ray = ray;
    ctx.local_isect = local_isect;
    if (local_isect) {
      local_isect->num_hits = 0;
    }
    ctx.local_object_id = local_object;
    IntersectContext rtc_ctx(&ctx);
    RTCRay rtc_ray;
    kernel_embree_setup_ray(*ray, rtc_ray, PATH_RAY_ALL_VISIBILITY);

    /* If this object has its own BVH, use it. */
    if (has_bvh) {
      RTCGeometry geom = rtcGetGeometry(kernel_data.bvh.scene, local_object * 2);
      if (geom) {
        float3 P = ray->P;
        float3 dir = ray->D;
        float3 idir = ray->D;
        Transform ob_itfm;
        rtc_ray.tfar = ray->t *
                       bvh_instance_motion_push(kg, local_object, ray, &P, &dir, &idir, &ob_itfm);
        /* bvh_instance_motion_push() returns the inverse transform but
         * it's not needed here. */
        (void)ob_itfm;

        rtc_ray.org_x = P.x;
        rtc_ray.org_y = P.y;
        rtc_ray.org_z = P.z;
        rtc_ray.dir_x = dir.x;
        rtc_ray.dir_y = dir.y;
        rtc_ray.dir_z = dir.z;
        RTCScene scene = (RTCScene)rtcGetGeometryUserData(geom);
        kernel_assert(scene);
        if (scene) {
          rtcOccluded1(scene, &rtc_ctx.context, &rtc_ray);
        }
      }
    }
    else {
      rtcOccluded1(kernel_data.bvh.scene, &rtc_ctx.context, &rtc_ray);
    }

    /* rtcOccluded1 sets tfar to -inf if a hit was found. */
    return (local_isect && local_isect->num_hits > 0) || (rtc_ray.tfar < 0);
    ;
  }
#    endif /* __EMBREE__ */

#    ifdef __OBJECT_MOTION__
  if (kernel_data.bvh.have_motion) {
    return bvh_intersect_local_motion(kg, ray, local_isect, local_object, lcg_state, max_hits);
  }
#    endif /* __OBJECT_MOTION__ */
  return bvh_intersect_local(kg, ray, local_isect, local_object, lcg_state, max_hits);
#  endif   /* __KERNEL_OPTIX__ */
}
#endif

#ifdef __SHADOW_RECORD_ALL__
ccl_device_intersect bool scene_intersect_shadow_all(KernelGlobals kg,
                                                     IntegratorShadowState state,
                                                     ccl_private const Ray *ray,
                                                     uint visibility,
                                                     uint max_hits,
                                                     ccl_private uint *num_recorded_hits,
                                                     ccl_private float *throughput)
{
#  ifdef __KERNEL_OPTIX__
  uint p0 = state;
  uint p1 = __float_as_uint(1.0f); /* Throughput. */
  uint p2 = 0;                     /* Number of hits. */
  uint p3 = max_hits;
  uint p4 = visibility;
  uint p5 = false;
  uint p6 = ((uint64_t)ray) & 0xFFFFFFFF;
  uint p7 = (((uint64_t)ray) >> 32) & 0xFFFFFFFF;

  uint ray_mask = visibility & 0xFF;
  if (0 == ray_mask && (visibility & ~0xFF) != 0) {
    ray_mask = 0xFF;
  }

  optixTrace(scene_intersect_valid(ray) ? kernel_data.bvh.scene : 0,
             ray->P,
             ray->D,
             0.0f,
             ray->t,
             ray->time,
             ray_mask,
             /* Need to always call into __anyhit__kernel_optix_shadow_all_hit. */
             OPTIX_RAY_FLAG_ENFORCE_ANYHIT,
             1, /* SBT offset for PG_HITS */
             0,
             0,
             p0,
             p1,
             p2,
             p3,
             p4,
             p5,
             p6,
             p7);

  *num_recorded_hits = uint16_unpack_from_uint_0(p2);
  *throughput = __uint_as_float(p1);

  return p5;
#  elif defined(__METALRT__)

  if (!scene_intersect_valid(ray)) {
    return false;
  }

#    if defined(__KERNEL_DEBUG__)
  if (is_null_instance_acceleration_structure(metal_ancillaries->accel_struct)) {
    kernel_assert(!"Invalid metal_ancillaries->accel_struct pointer");
    return false;
  }

  if (is_null_intersection_function_table(metal_ancillaries->ift_shadow)) {
    kernel_assert(!"Invalid ift_shadow");
    return false;
  }
#    endif

  metal::raytracing::ray r(ray->P, ray->D, 0.0f, ray->t);
  metalrt_intersector_type metalrt_intersect;

  metalrt_intersect.force_opacity(metal::raytracing::forced_opacity::non_opaque);
  if (!kernel_data.bvh.have_curves) {
    metalrt_intersect.assume_geometry_type(metal::raytracing::geometry_type::triangle);
  }

  MetalRTIntersectionShadowPayload payload;
  payload.self = ray->self;
  payload.visibility = visibility;
  payload.max_hits = max_hits;
  payload.num_hits = 0;
  payload.num_recorded_hits = 0;
  payload.throughput = 1.0f;
  payload.result = false;
  payload.state = state;

  uint ray_mask = visibility & 0xFF;
  if (0 == ray_mask && (visibility & ~0xFF) != 0) {
    ray_mask = 0xFF;
  }

  typename metalrt_intersector_type::result_type intersection;

#    if defined(__METALRT_MOTION__)
  payload.time = ray->time;
  intersection = metalrt_intersect.intersect(r,
                                             metal_ancillaries->accel_struct,
                                             ray_mask,
                                             ray->time,
                                             metal_ancillaries->ift_shadow,
                                             payload);
#    else
  intersection = metalrt_intersect.intersect(
      r, metal_ancillaries->accel_struct, ray_mask, metal_ancillaries->ift_shadow, payload);
#    endif

  *num_recorded_hits = payload.num_recorded_hits;
  *throughput = payload.throughput;

  return payload.result;

#  else
  if (!scene_intersect_valid(ray)) {
    *num_recorded_hits = 0;
    *throughput = 1.0f;
    return false;
  }

#    ifdef __EMBREE__
  if (kernel_data.bvh.scene) {
    CCLIntersectContext ctx(kg, CCLIntersectContext::RAY_SHADOW_ALL);
    Intersection *isect_array = (Intersection *)state->shadow_isect;
    ctx.isect_s = isect_array;
    ctx.max_hits = max_hits;
    ctx.ray = ray;
    IntersectContext rtc_ctx(&ctx);
    RTCRay rtc_ray;
    kernel_embree_setup_ray(*ray, rtc_ray, visibility);
    rtcOccluded1(kernel_data.bvh.scene, &rtc_ctx.context, &rtc_ray);

    *num_recorded_hits = ctx.num_recorded_hits;
    *throughput = ctx.throughput;
    return ctx.opaque_hit;
  }
#    endif /* __EMBREE__ */

#    ifdef __OBJECT_MOTION__
  if (kernel_data.bvh.have_motion) {
#      ifdef __HAIR__
    if (kernel_data.bvh.have_curves) {
      return bvh_intersect_shadow_all_hair_motion(
          kg, ray, state, visibility, max_hits, num_recorded_hits, throughput);
    }
#      endif /* __HAIR__ */

    return bvh_intersect_shadow_all_motion(
        kg, ray, state, visibility, max_hits, num_recorded_hits, throughput);
  }
#    endif   /* __OBJECT_MOTION__ */

#    ifdef __HAIR__
  if (kernel_data.bvh.have_curves) {
    return bvh_intersect_shadow_all_hair(
        kg, ray, state, visibility, max_hits, num_recorded_hits, throughput);
  }
#    endif /* __HAIR__ */

  return bvh_intersect_shadow_all(
      kg, ray, state, visibility, max_hits, num_recorded_hits, throughput);
#  endif   /* __KERNEL_OPTIX__ */
}
#endif /* __SHADOW_RECORD_ALL__ */

#ifdef __VOLUME__
ccl_device_intersect bool scene_intersect_volume(KernelGlobals kg,
                                                 ccl_private const Ray *ray,
                                                 ccl_private Intersection *isect,
                                                 const uint visibility)
{
#  ifdef __KERNEL_OPTIX__
  uint p0 = 0;
  uint p1 = 0;
  uint p2 = 0;
  uint p3 = 0;
  uint p4 = visibility;
  uint p5 = PRIMITIVE_NONE;
  uint p6 = ((uint64_t)ray) & 0xFFFFFFFF;
  uint p7 = (((uint64_t)ray) >> 32) & 0xFFFFFFFF;

  uint ray_mask = visibility & 0xFF;
  if (0 == ray_mask && (visibility & ~0xFF) != 0) {
    ray_mask = 0xFF;
  }

  optixTrace(scene_intersect_valid(ray) ? kernel_data.bvh.scene : 0,
             ray->P,
             ray->D,
             0.0f,
             ray->t,
             ray->time,
             ray_mask,
             /* Need to always call into __anyhit__kernel_optix_volume_test. */
             OPTIX_RAY_FLAG_ENFORCE_ANYHIT,
             3, /* SBT offset for PG_HITV */
             0,
             0,
             p0,
             p1,
             p2,
             p3,
             p4,
             p5,
             p6,
             p7);

  isect->t = __uint_as_float(p0);
  isect->u = __uint_as_float(p1);
  isect->v = __uint_as_float(p2);
  isect->prim = p3;
  isect->object = p4;
  isect->type = p5;

  return p5 != PRIMITIVE_NONE;
#  elif defined(__METALRT__)

  if (!scene_intersect_valid(ray)) {
    return false;
  }
#    if defined(__KERNEL_DEBUG__)
  if (is_null_instance_acceleration_structure(metal_ancillaries->accel_struct)) {
    kernel_assert(!"Invalid metal_ancillaries->accel_struct pointer");
    return false;
  }

  if (is_null_intersection_function_table(metal_ancillaries->ift_default)) {
    kernel_assert(!"Invalid ift_default");
    return false;
  }
#    endif

  metal::raytracing::ray r(ray->P, ray->D, 0.0f, ray->t);
  metalrt_intersector_type metalrt_intersect;

  metalrt_intersect.force_opacity(metal::raytracing::forced_opacity::non_opaque);
  if (!kernel_data.bvh.have_curves) {
    metalrt_intersect.assume_geometry_type(metal::raytracing::geometry_type::triangle);
  }

  MetalRTIntersectionPayload payload;
  payload.self = ray->self;
  payload.visibility = visibility;

  typename metalrt_intersector_type::result_type intersection;

  uint ray_mask = visibility & 0xFF;
  if (0 == ray_mask && (visibility & ~0xFF) != 0) {
    ray_mask = 0xFF;
  }

#    if defined(__METALRT_MOTION__)
  payload.time = ray->time;
  intersection = metalrt_intersect.intersect(r,
                                             metal_ancillaries->accel_struct,
                                             ray_mask,
                                             ray->time,
                                             metal_ancillaries->ift_default,
                                             payload);
#    else
  intersection = metalrt_intersect.intersect(
      r, metal_ancillaries->accel_struct, ray_mask, metal_ancillaries->ift_default, payload);
#    endif

  if (intersection.type == intersection_type::none) {
    return false;
  }

  isect->prim = payload.prim;
  isect->type = payload.type;
  isect->object = intersection.user_instance_id;

  isect->t = intersection.distance;
  if (intersection.type == intersection_type::triangle) {
    isect->u = 1.0f - intersection.triangle_barycentric_coord.y -
               intersection.triangle_barycentric_coord.x;
    isect->v = intersection.triangle_barycentric_coord.x;
  }
  else {
    isect->u = payload.u;
    isect->v = payload.v;
  }

  return isect->type != PRIMITIVE_NONE;

#  else
  if (!scene_intersect_valid(ray)) {
    return false;
  }

#    ifdef __OBJECT_MOTION__
  if (kernel_data.bvh.have_motion) {
    return bvh_intersect_volume_motion(kg, ray, isect, visibility);
  }
#    endif /* __OBJECT_MOTION__ */

  return bvh_intersect_volume(kg, ray, isect, visibility);
#  endif   /* __KERNEL_OPTIX__ */
}
#endif /* __VOLUME__ */

#ifdef __VOLUME_RECORD_ALL__
ccl_device_intersect uint scene_intersect_volume_all(KernelGlobals kg,
                                                     ccl_private const Ray *ray,
                                                     ccl_private Intersection *isect,
                                                     const uint max_hits,
                                                     const uint visibility)
{
  if (!scene_intersect_valid(ray)) {
    return false;
  }

#  ifdef __EMBREE__
  if (kernel_data.bvh.scene) {
    CCLIntersectContext ctx(kg, CCLIntersectContext::RAY_VOLUME_ALL);
    ctx.isect_s = isect;
    ctx.max_hits = max_hits;
    ctx.num_hits = 0;
    ctx.ray = ray;
    IntersectContext rtc_ctx(&ctx);
    RTCRay rtc_ray;
    kernel_embree_setup_ray(*ray, rtc_ray, visibility);
    rtcOccluded1(kernel_data.bvh.scene, &rtc_ctx.context, &rtc_ray);
    return ctx.num_hits;
  }
#  endif /* __EMBREE__ */

#  ifdef __OBJECT_MOTION__
  if (kernel_data.bvh.have_motion) {
    return bvh_intersect_volume_all_motion(kg, ray, isect, max_hits, visibility);
  }
#  endif /* __OBJECT_MOTION__ */

  return bvh_intersect_volume_all(kg, ray, isect, max_hits, visibility);
}
#endif /* __VOLUME_RECORD_ALL__ */

CCL_NAMESPACE_END
