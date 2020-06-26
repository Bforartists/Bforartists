/*
 * Copyright 2018, Blender Foundation.
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

/* This class implements a ray accelerator for Cycles using Intel's Embree library.
 * It supports triangles, curves, object and deformation blur and instancing.
 *
 * Since Embree allows object to be either curves or triangles but not both, Cycles object IDs are
 * mapped to Embree IDs by multiplying by two and adding one for curves.
 *
 * This implementation shares RTCDevices between Cycles instances. Eventually each instance should
 * get a separate RTCDevice to correctly keep track of memory usage.
 *
 * Vertex and index buffers are duplicated between Cycles device arrays and Embree. These could be
 * merged, which would require changes to intersection refinement, shader setup, mesh light
 * sampling and a few other places in Cycles where direct access to vertex data is required.
 */

#ifdef WITH_EMBREE

#  include <embree3/rtcore_geometry.h>
#  include <pmmintrin.h>
#  include <xmmintrin.h>

#  include "bvh/bvh_embree.h"

/* Kernel includes are necessary so that the filter function for Embree can access the packed BVH.
 */
#  include "kernel/bvh/bvh_embree.h"
#  include "kernel/kernel_compat_cpu.h"
#  include "kernel/kernel_globals.h"
#  include "kernel/kernel_random.h"
#  include "kernel/split/kernel_split_data_types.h"

#  include "render/hair.h"
#  include "render/mesh.h"
#  include "render/object.h"

#  include "util/util_foreach.h"
#  include "util/util_logging.h"
#  include "util/util_progress.h"
#  include "util/util_stats.h"

CCL_NAMESPACE_BEGIN

static_assert(Object::MAX_MOTION_STEPS <= RTC_MAX_TIME_STEP_COUNT,
              "Object and Embree max motion steps inconsistent");
static_assert(Object::MAX_MOTION_STEPS == Geometry::MAX_MOTION_STEPS,
              "Object and Geometry max motion steps inconsistent");

#  define IS_HAIR(x) (x & 1)

/* This gets called by Embree at every valid ray/object intersection.
 * Things like recording subsurface or shadow hits for later evaluation
 * as well as filtering for volume objects happen here.
 * Cycles' own BVH does that directly inside the traversal calls.
 */
static void rtc_filter_occluded_func(const RTCFilterFunctionNArguments *args)
{
  /* Current implementation in Cycles assumes only single-ray intersection queries. */
  assert(args->N == 1);

  const RTCRay *ray = (RTCRay *)args->ray;
  RTCHit *hit = (RTCHit *)args->hit;
  CCLIntersectContext *ctx = ((IntersectContext *)args->context)->userRayExt;
  KernelGlobals *kg = ctx->kg;

  switch (ctx->type) {
    case CCLIntersectContext::RAY_SHADOW_ALL: {
      /* Append the intersection to the end of the array. */
      if (ctx->num_hits < ctx->max_hits) {
        Intersection current_isect;
        kernel_embree_convert_hit(kg, ray, hit, &current_isect);
        for (size_t i = 0; i < ctx->max_hits; ++i) {
          if (current_isect.object == ctx->isect_s[i].object &&
              current_isect.prim == ctx->isect_s[i].prim && current_isect.t == ctx->isect_s[i].t) {
            /* This intersection was already recorded, skip it. */
            *args->valid = 0;
            break;
          }
        }
        Intersection *isect = &ctx->isect_s[ctx->num_hits];
        ++ctx->num_hits;
        *isect = current_isect;
        int prim = kernel_tex_fetch(__prim_index, isect->prim);
        int shader = 0;
        if (kernel_tex_fetch(__prim_type, isect->prim) & PRIMITIVE_ALL_TRIANGLE) {
          shader = kernel_tex_fetch(__tri_shader, prim);
        }
        else {
          float4 str = kernel_tex_fetch(__curves, prim);
          shader = __float_as_int(str.z);
        }
        int flag = kernel_tex_fetch(__shaders, shader & SHADER_MASK).flags;
        /* If no transparent shadows, all light is blocked. */
        if (flag & (SD_HAS_TRANSPARENT_SHADOW)) {
          /* This tells Embree to continue tracing. */
          *args->valid = 0;
        }
      }
      else {
        /* Increase the number of hits beyond ray.max_hits
         * so that the caller can detect this as opaque. */
        ++ctx->num_hits;
      }
      break;
    }
    case CCLIntersectContext::RAY_LOCAL:
    case CCLIntersectContext::RAY_SSS: {
      /* Check if it's hitting the correct object. */
      Intersection current_isect;
      if (ctx->type == CCLIntersectContext::RAY_SSS) {
        kernel_embree_convert_sss_hit(kg, ray, hit, &current_isect, ctx->local_object_id);
      }
      else {
        kernel_embree_convert_hit(kg, ray, hit, &current_isect);
        if (ctx->local_object_id != current_isect.object) {
          /* This tells Embree to continue tracing. */
          *args->valid = 0;
        }
      }

      /* No intersection information requested, just return a hit. */
      if (ctx->max_hits == 0) {
        break;
      }

      /* Ignore curves. */
      if (IS_HAIR(hit->geomID)) {
        /* This tells Embree to continue tracing. */
        *args->valid = 0;
        break;
      }

      /* See triangle_intersect_subsurface() for the native equivalent. */
      for (int i = min(ctx->max_hits, ctx->local_isect->num_hits) - 1; i >= 0; --i) {
        if (ctx->local_isect->hits[i].t == ray->tfar) {
          /* This tells Embree to continue tracing. */
          *args->valid = 0;
          break;
        }
      }

      int hit_idx = 0;

      if (ctx->lcg_state) {

        ++ctx->local_isect->num_hits;
        if (ctx->local_isect->num_hits <= ctx->max_hits) {
          hit_idx = ctx->local_isect->num_hits - 1;
        }
        else {
          /* reservoir sampling: if we are at the maximum number of
           * hits, randomly replace element or skip it */
          hit_idx = lcg_step_uint(ctx->lcg_state) % ctx->local_isect->num_hits;

          if (hit_idx >= ctx->max_hits) {
            /* This tells Embree to continue tracing. */
            *args->valid = 0;
            break;
          }
        }
      }
      else {
        ctx->local_isect->num_hits = 1;
      }
      /* record intersection */
      ctx->local_isect->hits[hit_idx] = current_isect;
      ctx->local_isect->Ng[hit_idx] = normalize(make_float3(hit->Ng_x, hit->Ng_y, hit->Ng_z));
      /* This tells Embree to continue tracing .*/
      *args->valid = 0;
      break;
    }
    case CCLIntersectContext::RAY_VOLUME_ALL: {
      /* Append the intersection to the end of the array. */
      if (ctx->num_hits < ctx->max_hits) {
        Intersection current_isect;
        kernel_embree_convert_hit(kg, ray, hit, &current_isect);
        for (size_t i = 0; i < ctx->max_hits; ++i) {
          if (current_isect.object == ctx->isect_s[i].object &&
              current_isect.prim == ctx->isect_s[i].prim && current_isect.t == ctx->isect_s[i].t) {
            /* This intersection was already recorded, skip it. */
            *args->valid = 0;
            break;
          }
        }
        Intersection *isect = &ctx->isect_s[ctx->num_hits];
        ++ctx->num_hits;
        *isect = current_isect;
        /* Only primitives from volume object. */
        uint tri_object = (isect->object == OBJECT_NONE) ?
                              kernel_tex_fetch(__prim_object, isect->prim) :
                              isect->object;
        int object_flag = kernel_tex_fetch(__object_flag, tri_object);
        if ((object_flag & SD_OBJECT_HAS_VOLUME) == 0) {
          --ctx->num_hits;
        }
        /* This tells Embree to continue tracing. */
        *args->valid = 0;
        break;
      }
    }
    case CCLIntersectContext::RAY_REGULAR:
    default:
      /* Nothing to do here. */
      break;
  }
}

static void rtc_filter_func_thick_curve(const RTCFilterFunctionNArguments *args)
{
  const RTCRay *ray = (RTCRay *)args->ray;
  RTCHit *hit = (RTCHit *)args->hit;

  /* Always ignore backfacing intersections. */
  if (dot(make_float3(ray->dir_x, ray->dir_y, ray->dir_z),
          make_float3(hit->Ng_x, hit->Ng_y, hit->Ng_z)) > 0.0f) {
    *args->valid = 0;
    return;
  }
}

static void rtc_filter_occluded_func_thick_curve(const RTCFilterFunctionNArguments *args)
{
  const RTCRay *ray = (RTCRay *)args->ray;
  RTCHit *hit = (RTCHit *)args->hit;

  /* Always ignore backfacing intersections. */
  if (dot(make_float3(ray->dir_x, ray->dir_y, ray->dir_z),
          make_float3(hit->Ng_x, hit->Ng_y, hit->Ng_z)) > 0.0f) {
    *args->valid = 0;
    return;
  }

  rtc_filter_occluded_func(args);
}

static size_t unaccounted_mem = 0;

static bool rtc_memory_monitor_func(void *userPtr, const ssize_t bytes, const bool)
{
  Stats *stats = (Stats *)userPtr;
  if (stats) {
    if (bytes > 0) {
      stats->mem_alloc(bytes);
    }
    else {
      stats->mem_free(-bytes);
    }
  }
  else {
    /* A stats pointer may not yet be available. Keep track of the memory usage for later. */
    if (bytes >= 0) {
      atomic_add_and_fetch_z(&unaccounted_mem, bytes);
    }
    else {
      atomic_sub_and_fetch_z(&unaccounted_mem, -bytes);
    }
  }
  return true;
}

static void rtc_error_func(void *, enum RTCError, const char *str)
{
  VLOG(1) << str;
}

static double progress_start_time = 0.0f;

static bool rtc_progress_func(void *user_ptr, const double n)
{
  Progress *progress = (Progress *)user_ptr;

  if (time_dt() - progress_start_time < 0.25) {
    return true;
  }

  string msg = string_printf("Building BVH %.0f%%", n * 100.0);
  progress->set_substatus(msg);
  progress_start_time = time_dt();

  return !progress->get_cancel();
}

/* This is to have a shared device between all BVH instances.
   It would be useful to actually to use a separte RTCDevice per Cycles instance. */
RTCDevice BVHEmbree::rtc_shared_device = NULL;
int BVHEmbree::rtc_shared_users = 0;
thread_mutex BVHEmbree::rtc_shared_mutex;

static size_t count_primitives(Geometry *geom)
{
  if (geom->type == Geometry::MESH) {
    Mesh *mesh = static_cast<Mesh *>(geom);
    return mesh->num_triangles();
  }
  else if (geom->type == Geometry::HAIR) {
    Hair *hair = static_cast<Hair *>(geom);
    return hair->num_segments();
  }

  return 0;
}

BVHEmbree::BVHEmbree(const BVHParams &params_,
                     const vector<Geometry *> &geometry_,
                     const vector<Object *> &objects_)
    : BVH(params_, geometry_, objects_),
      scene(NULL),
      mem_used(0),
      top_level(NULL),
      stats(NULL),
      curve_subdivisions(params.curve_subdivisions),
      build_quality(RTC_BUILD_QUALITY_REFIT),
      dynamic_scene(true)
{
  _MM_SET_FLUSH_ZERO_MODE(_MM_FLUSH_ZERO_ON);
  _MM_SET_DENORMALS_ZERO_MODE(_MM_DENORMALS_ZERO_ON);
  thread_scoped_lock lock(rtc_shared_mutex);
  if (rtc_shared_users == 0) {
    rtc_shared_device = rtcNewDevice("verbose=0");
    /* Check here if Embree was built with the correct flags. */
    ssize_t ret = rtcGetDeviceProperty(rtc_shared_device, RTC_DEVICE_PROPERTY_RAY_MASK_SUPPORTED);
    if (ret != 1) {
      assert(0);
      VLOG(1) << "Embree is compiled without the RTC_DEVICE_PROPERTY_RAY_MASK_SUPPORTED flag."
                 "Ray visibility will not work.";
    }
    ret = rtcGetDeviceProperty(rtc_shared_device, RTC_DEVICE_PROPERTY_FILTER_FUNCTION_SUPPORTED);
    if (ret != 1) {
      assert(0);
      VLOG(1)
          << "Embree is compiled without the RTC_DEVICE_PROPERTY_FILTER_FUNCTION_SUPPORTED flag."
             "Renders may not look as expected.";
    }
    ret = rtcGetDeviceProperty(rtc_shared_device, RTC_DEVICE_PROPERTY_CURVE_GEOMETRY_SUPPORTED);
    if (ret != 1) {
      assert(0);
      VLOG(1)
          << "Embree is compiled without the RTC_DEVICE_PROPERTY_CURVE_GEOMETRY_SUPPORTED flag. "
             "Line primitives will not be rendered.";
    }
    ret = rtcGetDeviceProperty(rtc_shared_device, RTC_DEVICE_PROPERTY_TRIANGLE_GEOMETRY_SUPPORTED);
    if (ret != 1) {
      assert(0);
      VLOG(1) << "Embree is compiled without the RTC_DEVICE_PROPERTY_TRIANGLE_GEOMETRY_SUPPORTED "
                 "flag. "
                 "Triangle primitives will not be rendered.";
    }
    ret = rtcGetDeviceProperty(rtc_shared_device, RTC_DEVICE_PROPERTY_BACKFACE_CULLING_ENABLED);
    if (ret != 0) {
      assert(0);
      VLOG(1) << "Embree is compiled with the RTC_DEVICE_PROPERTY_BACKFACE_CULLING_ENABLED flag. "
                 "Renders may not look as expected.";
    }
  }
  ++rtc_shared_users;

  rtcSetDeviceErrorFunction(rtc_shared_device, rtc_error_func, NULL);

  pack.root_index = -1;
}

BVHEmbree::~BVHEmbree()
{
  if (!params.top_level) {
    destroy(scene);
  }
}

void BVHEmbree::destroy(RTCScene scene)
{
  if (scene) {
    rtcReleaseScene(scene);
    scene = NULL;
  }
  thread_scoped_lock lock(rtc_shared_mutex);
  --rtc_shared_users;
  if (rtc_shared_users == 0) {
    rtcReleaseDevice(rtc_shared_device);
    rtc_shared_device = NULL;
  }
}

void BVHEmbree::delete_rtcScene()
{
  if (scene) {
    /* When this BVH is used as an instance in a top level BVH, don't delete now
     * Let the top_level BVH know that it should delete it later. */
    if (top_level) {
      top_level->add_delayed_delete_scene(scene);
    }
    else {
      rtcReleaseScene(scene);
      if (delayed_delete_scenes.size()) {
        foreach (RTCScene s, delayed_delete_scenes) {
          rtcReleaseScene(s);
        }
      }
      delayed_delete_scenes.clear();
    }
    scene = NULL;
  }
}

void BVHEmbree::build(Progress &progress, Stats *stats_)
{
  assert(rtc_shared_device);
  stats = stats_;
  rtcSetDeviceMemoryMonitorFunction(rtc_shared_device, rtc_memory_monitor_func, stats);

  progress.set_substatus("Building BVH");

  if (scene) {
    rtcReleaseScene(scene);
    scene = NULL;
  }

  const bool dynamic = params.bvh_type == SceneParams::BVH_DYNAMIC;

  scene = rtcNewScene(rtc_shared_device);
  const RTCSceneFlags scene_flags = (dynamic ? RTC_SCENE_FLAG_DYNAMIC : RTC_SCENE_FLAG_NONE) |
                                    RTC_SCENE_FLAG_COMPACT | RTC_SCENE_FLAG_ROBUST;
  rtcSetSceneFlags(scene, scene_flags);
  build_quality = dynamic ? RTC_BUILD_QUALITY_LOW :
                            (params.use_spatial_split ? RTC_BUILD_QUALITY_HIGH :
                                                        RTC_BUILD_QUALITY_MEDIUM);
  rtcSetSceneBuildQuality(scene, build_quality);

  /* Count triangles and curves first, reserve arrays once. */
  size_t prim_count = 0;

  foreach (Object *ob, objects) {
    if (params.top_level) {
      if (!ob->is_traceable()) {
        continue;
      }
      if (!ob->geometry->is_instanced()) {
        prim_count += count_primitives(ob->geometry);
      }
      else {
        ++prim_count;
      }
    }
    else {
      prim_count += count_primitives(ob->geometry);
    }
  }

  pack.prim_object.reserve(prim_count);
  pack.prim_type.reserve(prim_count);
  pack.prim_index.reserve(prim_count);
  pack.prim_tri_index.reserve(prim_count);

  int i = 0;

  pack.object_node.clear();

  foreach (Object *ob, objects) {
    if (params.top_level) {
      if (!ob->is_traceable()) {
        ++i;
        continue;
      }
      if (!ob->geometry->is_instanced()) {
        add_object(ob, i);
      }
      else {
        add_instance(ob, i);
      }
    }
    else {
      add_object(ob, i);
    }
    ++i;
    if (progress.get_cancel())
      return;
  }

  if (progress.get_cancel()) {
    delete_rtcScene();
    stats = NULL;
    return;
  }

  rtcSetSceneProgressMonitorFunction(scene, rtc_progress_func, &progress);
  rtcCommitScene(scene);

  pack_primitives();

  if (progress.get_cancel()) {
    delete_rtcScene();
    stats = NULL;
    return;
  }

  progress.set_substatus("Packing geometry");
  pack_nodes(NULL);

  stats = NULL;
}

void BVHEmbree::copy_to_device(Progress & /*progress*/, DeviceScene *dscene)
{
  dscene->data.bvh.scene = scene;
}

BVHNode *BVHEmbree::widen_children_nodes(const BVHNode * /*root*/)
{
  assert(!"Must not be called.");
  return NULL;
}

void BVHEmbree::add_object(Object *ob, int i)
{
  Geometry *geom = ob->geometry;

  if (geom->type == Geometry::MESH) {
    Mesh *mesh = static_cast<Mesh *>(geom);
    if (mesh->num_triangles() > 0) {
      add_triangles(ob, mesh, i);
    }
  }
  else if (geom->type == Geometry::HAIR) {
    Hair *hair = static_cast<Hair *>(geom);
    if (hair->num_curves() > 0) {
      add_curves(ob, hair, i);
    }
  }
}

void BVHEmbree::add_instance(Object *ob, int i)
{
  if (!ob || !ob->geometry) {
    assert(0);
    return;
  }
  BVHEmbree *instance_bvh = (BVHEmbree *)(ob->geometry->bvh);

  if (instance_bvh->top_level != this) {
    instance_bvh->top_level = this;
  }

  const size_t num_object_motion_steps = ob->use_motion() ? ob->motion.size() : 1;
  const size_t num_motion_steps = min(num_object_motion_steps, RTC_MAX_TIME_STEP_COUNT);
  assert(num_object_motion_steps <= RTC_MAX_TIME_STEP_COUNT);

  RTCGeometry geom_id = rtcNewGeometry(rtc_shared_device, RTC_GEOMETRY_TYPE_INSTANCE);
  rtcSetGeometryInstancedScene(geom_id, instance_bvh->scene);
  rtcSetGeometryTimeStepCount(geom_id, num_motion_steps);

  if (ob->use_motion()) {
    array<DecomposedTransform> decomp(ob->motion.size());
    transform_motion_decompose(decomp.data(), ob->motion.data(), ob->motion.size());
    for (size_t step = 0; step < num_motion_steps; ++step) {
      RTCQuaternionDecomposition rtc_decomp;
      rtcInitQuaternionDecomposition(&rtc_decomp);
      rtcQuaternionDecompositionSetQuaternion(
          &rtc_decomp, decomp[step].x.w, decomp[step].x.x, decomp[step].x.y, decomp[step].x.z);
      rtcQuaternionDecompositionSetScale(
          &rtc_decomp, decomp[step].y.w, decomp[step].z.w, decomp[step].w.w);
      rtcQuaternionDecompositionSetTranslation(
          &rtc_decomp, decomp[step].y.x, decomp[step].y.y, decomp[step].y.z);
      rtcQuaternionDecompositionSetSkew(
          &rtc_decomp, decomp[step].z.x, decomp[step].z.y, decomp[step].w.x);
      rtcSetGeometryTransformQuaternion(geom_id, step, &rtc_decomp);
    }
  }
  else {
    rtcSetGeometryTransform(geom_id, 0, RTC_FORMAT_FLOAT3X4_ROW_MAJOR, (const float *)&ob->tfm);
  }

  pack.prim_index.push_back_slow(-1);
  pack.prim_object.push_back_slow(i);
  pack.prim_type.push_back_slow(PRIMITIVE_NONE);
  pack.prim_tri_index.push_back_slow(-1);

  rtcSetGeometryUserData(geom_id, (void *)instance_bvh->scene);
  rtcSetGeometryMask(geom_id, ob->visibility_for_tracing());

  rtcCommitGeometry(geom_id);
  rtcAttachGeometryByID(scene, geom_id, i * 2);
  rtcReleaseGeometry(geom_id);
}

void BVHEmbree::add_triangles(const Object *ob, const Mesh *mesh, int i)
{
  size_t prim_offset = pack.prim_index.size();
  const Attribute *attr_mP = NULL;
  size_t num_geometry_motion_steps = 1;
  if (mesh->has_motion_blur()) {
    attr_mP = mesh->attributes.find(ATTR_STD_MOTION_VERTEX_POSITION);
    if (attr_mP) {
      num_geometry_motion_steps = mesh->motion_steps;
    }
  }

  const size_t num_motion_steps = min(num_geometry_motion_steps, RTC_MAX_TIME_STEP_COUNT);
  assert(num_geometry_motion_steps <= RTC_MAX_TIME_STEP_COUNT);

  const size_t num_triangles = mesh->num_triangles();
  RTCGeometry geom_id = rtcNewGeometry(rtc_shared_device, RTC_GEOMETRY_TYPE_TRIANGLE);
  rtcSetGeometryBuildQuality(geom_id, build_quality);
  rtcSetGeometryTimeStepCount(geom_id, num_motion_steps);

  unsigned *rtc_indices = (unsigned *)rtcSetNewGeometryBuffer(
      geom_id, RTC_BUFFER_TYPE_INDEX, 0, RTC_FORMAT_UINT3, sizeof(int) * 3, num_triangles);
  assert(rtc_indices);
  if (!rtc_indices) {
    VLOG(1) << "Embree could not create new geometry buffer for mesh " << mesh->name.c_str()
            << ".\n";
    return;
  }
  for (size_t j = 0; j < num_triangles; ++j) {
    Mesh::Triangle t = mesh->get_triangle(j);
    rtc_indices[j * 3] = t.v[0];
    rtc_indices[j * 3 + 1] = t.v[1];
    rtc_indices[j * 3 + 2] = t.v[2];
  }

  update_tri_vertex_buffer(geom_id, mesh);

  size_t prim_object_size = pack.prim_object.size();
  pack.prim_object.resize(prim_object_size + num_triangles);
  size_t prim_type_size = pack.prim_type.size();
  pack.prim_type.resize(prim_type_size + num_triangles);
  size_t prim_index_size = pack.prim_index.size();
  pack.prim_index.resize(prim_index_size + num_triangles);
  pack.prim_tri_index.resize(prim_index_size + num_triangles);
  int prim_type = (num_motion_steps > 1 ? PRIMITIVE_MOTION_TRIANGLE : PRIMITIVE_TRIANGLE);

  for (size_t j = 0; j < num_triangles; ++j) {
    pack.prim_object[prim_object_size + j] = i;
    pack.prim_type[prim_type_size + j] = prim_type;
    pack.prim_index[prim_index_size + j] = j;
    pack.prim_tri_index[prim_index_size + j] = j;
  }

  rtcSetGeometryUserData(geom_id, (void *)prim_offset);
  rtcSetGeometryOccludedFilterFunction(geom_id, rtc_filter_occluded_func);
  rtcSetGeometryMask(geom_id, ob->visibility_for_tracing());

  rtcCommitGeometry(geom_id);
  rtcAttachGeometryByID(scene, geom_id, i * 2);
  rtcReleaseGeometry(geom_id);
}

void BVHEmbree::update_tri_vertex_buffer(RTCGeometry geom_id, const Mesh *mesh)
{
  const Attribute *attr_mP = NULL;
  size_t num_motion_steps = 1;
  int t_mid = 0;
  if (mesh->has_motion_blur()) {
    attr_mP = mesh->attributes.find(ATTR_STD_MOTION_VERTEX_POSITION);
    if (attr_mP) {
      num_motion_steps = mesh->motion_steps;
      t_mid = (num_motion_steps - 1) / 2;
      if (num_motion_steps > RTC_MAX_TIME_STEP_COUNT) {
        assert(0);
        num_motion_steps = RTC_MAX_TIME_STEP_COUNT;
      }
    }
  }
  const size_t num_verts = mesh->verts.size();

  for (int t = 0; t < num_motion_steps; ++t) {
    const float3 *verts;
    if (t == t_mid) {
      verts = &mesh->verts[0];
    }
    else {
      int t_ = (t > t_mid) ? (t - 1) : t;
      verts = &attr_mP->data_float3()[t_ * num_verts];
    }

    float *rtc_verts = (float *)rtcSetNewGeometryBuffer(
        geom_id, RTC_BUFFER_TYPE_VERTEX, t, RTC_FORMAT_FLOAT3, sizeof(float) * 3, num_verts + 1);
    assert(rtc_verts);
    if (rtc_verts) {
      for (size_t j = 0; j < num_verts; ++j) {
        rtc_verts[0] = verts[j].x;
        rtc_verts[1] = verts[j].y;
        rtc_verts[2] = verts[j].z;
        rtc_verts += 3;
      }
    }
  }
}

void BVHEmbree::update_curve_vertex_buffer(RTCGeometry geom_id, const Hair *hair)
{
  const Attribute *attr_mP = NULL;
  size_t num_motion_steps = 1;
  if (hair->has_motion_blur()) {
    attr_mP = hair->attributes.find(ATTR_STD_MOTION_VERTEX_POSITION);
    if (attr_mP) {
      num_motion_steps = hair->motion_steps;
    }
  }

  const size_t num_curves = hair->num_curves();
  size_t num_keys = 0;
  for (size_t j = 0; j < num_curves; ++j) {
    const Hair::Curve c = hair->get_curve(j);
    num_keys += c.num_keys;
  }

  /* Catmull-Rom splines need extra CVs at the beginning and end of each curve. */
  size_t num_keys_embree = num_keys;
  num_keys_embree += num_curves * 2;

  /* Copy the CV data to Embree */
  const int t_mid = (num_motion_steps - 1) / 2;
  const float *curve_radius = &hair->curve_radius[0];
  for (int t = 0; t < num_motion_steps; ++t) {
    const float3 *verts;
    if (t == t_mid || attr_mP == NULL) {
      verts = &hair->curve_keys[0];
    }
    else {
      int t_ = (t > t_mid) ? (t - 1) : t;
      verts = &attr_mP->data_float3()[t_ * num_keys];
    }

    float4 *rtc_verts = (float4 *)rtcSetNewGeometryBuffer(
        geom_id, RTC_BUFFER_TYPE_VERTEX, t, RTC_FORMAT_FLOAT4, sizeof(float) * 4, num_keys_embree);

    assert(rtc_verts);
    if (rtc_verts) {
      const size_t num_curves = hair->num_curves();
      for (size_t j = 0; j < num_curves; ++j) {
        Hair::Curve c = hair->get_curve(j);
        int fk = c.first_key;
        int k = 1;
        for (; k < c.num_keys + 1; ++k, ++fk) {
          rtc_verts[k] = float3_to_float4(verts[fk]);
          rtc_verts[k].w = curve_radius[fk];
        }
        /* Duplicate Embree's Catmull-Rom spline CVs at the start and end of each curve. */
        rtc_verts[0] = rtc_verts[1];
        rtc_verts[k] = rtc_verts[k - 1];
        rtc_verts += c.num_keys + 2;
      }
    }
  }
}

void BVHEmbree::add_curves(const Object *ob, const Hair *hair, int i)
{
  size_t prim_offset = pack.prim_index.size();
  const Attribute *attr_mP = NULL;
  size_t num_geometry_motion_steps = 1;
  if (hair->has_motion_blur()) {
    attr_mP = hair->attributes.find(ATTR_STD_MOTION_VERTEX_POSITION);
    if (attr_mP) {
      num_geometry_motion_steps = hair->motion_steps;
    }
  }

  const size_t num_motion_steps = min(num_geometry_motion_steps, RTC_MAX_TIME_STEP_COUNT);
  const PrimitiveType primitive_type =
      (num_motion_steps > 1) ?
          ((hair->curve_shape == CURVE_RIBBON) ? PRIMITIVE_MOTION_CURVE_RIBBON :
                                                 PRIMITIVE_MOTION_CURVE_THICK) :
          ((hair->curve_shape == CURVE_RIBBON) ? PRIMITIVE_CURVE_RIBBON : PRIMITIVE_CURVE_THICK);

  assert(num_geometry_motion_steps <= RTC_MAX_TIME_STEP_COUNT);

  const size_t num_curves = hair->num_curves();
  size_t num_segments = 0;
  for (size_t j = 0; j < num_curves; ++j) {
    Hair::Curve c = hair->get_curve(j);
    assert(c.num_segments() > 0);
    num_segments += c.num_segments();
  }

  /* Make room for Cycles specific data. */
  size_t prim_object_size = pack.prim_object.size();
  pack.prim_object.resize(prim_object_size + num_segments);
  size_t prim_type_size = pack.prim_type.size();
  pack.prim_type.resize(prim_type_size + num_segments);
  size_t prim_index_size = pack.prim_index.size();
  pack.prim_index.resize(prim_index_size + num_segments);
  size_t prim_tri_index_size = pack.prim_index.size();
  pack.prim_tri_index.resize(prim_tri_index_size + num_segments);

  enum RTCGeometryType type = (hair->curve_shape == CURVE_RIBBON ?
                                   RTC_GEOMETRY_TYPE_FLAT_CATMULL_ROM_CURVE :
                                   RTC_GEOMETRY_TYPE_ROUND_CATMULL_ROM_CURVE);

  RTCGeometry geom_id = rtcNewGeometry(rtc_shared_device, type);
  rtcSetGeometryTessellationRate(geom_id, curve_subdivisions + 1);
  unsigned *rtc_indices = (unsigned *)rtcSetNewGeometryBuffer(
      geom_id, RTC_BUFFER_TYPE_INDEX, 0, RTC_FORMAT_UINT, sizeof(int), num_segments);
  size_t rtc_index = 0;
  for (size_t j = 0; j < num_curves; ++j) {
    Hair::Curve c = hair->get_curve(j);
    for (size_t k = 0; k < c.num_segments(); ++k) {
      rtc_indices[rtc_index] = c.first_key + k;
      /* Room for extra CVs at Catmull-Rom splines. */
      rtc_indices[rtc_index] += j * 2;
      /* Cycles specific data. */
      pack.prim_object[prim_object_size + rtc_index] = i;
      pack.prim_type[prim_type_size + rtc_index] = (PRIMITIVE_PACK_SEGMENT(primitive_type, k));
      pack.prim_index[prim_index_size + rtc_index] = j;
      pack.prim_tri_index[prim_tri_index_size + rtc_index] = rtc_index;

      ++rtc_index;
    }
  }

  rtcSetGeometryBuildQuality(geom_id, build_quality);
  rtcSetGeometryTimeStepCount(geom_id, num_motion_steps);

  update_curve_vertex_buffer(geom_id, hair);

  rtcSetGeometryUserData(geom_id, (void *)prim_offset);
  if (hair->curve_shape == CURVE_RIBBON) {
    rtcSetGeometryOccludedFilterFunction(geom_id, rtc_filter_occluded_func);
  }
  else {
    rtcSetGeometryIntersectFilterFunction(geom_id, rtc_filter_func_thick_curve);
    rtcSetGeometryOccludedFilterFunction(geom_id, rtc_filter_occluded_func_thick_curve);
  }
  rtcSetGeometryMask(geom_id, ob->visibility_for_tracing());

  rtcCommitGeometry(geom_id);
  rtcAttachGeometryByID(scene, geom_id, i * 2 + 1);
  rtcReleaseGeometry(geom_id);
}

void BVHEmbree::pack_nodes(const BVHNode *)
{
  /* Quite a bit of this code is for compatibility with Cycles' native BVH. */
  if (!params.top_level) {
    return;
  }

  for (size_t i = 0; i < pack.prim_index.size(); ++i) {
    if (pack.prim_index[i] != -1) {
      pack.prim_index[i] += objects[pack.prim_object[i]]->geometry->prim_offset;
    }
  }

  size_t prim_offset = pack.prim_index.size();

  /* reserve */
  size_t prim_index_size = pack.prim_index.size();
  size_t prim_tri_verts_size = pack.prim_tri_verts.size();

  size_t pack_prim_index_offset = prim_index_size;
  size_t pack_prim_tri_verts_offset = prim_tri_verts_size;
  size_t object_offset = 0;

  map<Geometry *, int> geometry_map;

  foreach (Object *ob, objects) {
    Geometry *geom = ob->geometry;
    BVH *bvh = geom->bvh;

    if (geom->need_build_bvh(BVH_LAYOUT_EMBREE)) {
      if (geometry_map.find(geom) == geometry_map.end()) {
        prim_index_size += bvh->pack.prim_index.size();
        prim_tri_verts_size += bvh->pack.prim_tri_verts.size();
        geometry_map[geom] = 1;
      }
    }
  }

  geometry_map.clear();

  pack.prim_index.resize(prim_index_size);
  pack.prim_type.resize(prim_index_size);
  pack.prim_object.resize(prim_index_size);
  pack.prim_visibility.clear();
  pack.prim_tri_verts.resize(prim_tri_verts_size);
  pack.prim_tri_index.resize(prim_index_size);
  pack.object_node.resize(objects.size());

  int *pack_prim_index = (pack.prim_index.size()) ? &pack.prim_index[0] : NULL;
  int *pack_prim_type = (pack.prim_type.size()) ? &pack.prim_type[0] : NULL;
  int *pack_prim_object = (pack.prim_object.size()) ? &pack.prim_object[0] : NULL;
  float4 *pack_prim_tri_verts = (pack.prim_tri_verts.size()) ? &pack.prim_tri_verts[0] : NULL;
  uint *pack_prim_tri_index = (pack.prim_tri_index.size()) ? &pack.prim_tri_index[0] : NULL;

  /* merge */
  foreach (Object *ob, objects) {
    Geometry *geom = ob->geometry;

    /* We assume that if mesh doesn't need own BVH it was already included
     * into a top-level BVH and no packing here is needed.
     */
    if (!geom->need_build_bvh(BVH_LAYOUT_EMBREE)) {
      pack.object_node[object_offset++] = prim_offset;
      continue;
    }

    /* if geom already added once, don't add it again, but used set
     * node offset for this object */
    map<Geometry *, int>::iterator it = geometry_map.find(geom);

    if (geometry_map.find(geom) != geometry_map.end()) {
      int noffset = it->second;
      pack.object_node[object_offset++] = noffset;
      continue;
    }

    BVHEmbree *bvh = (BVHEmbree *)geom->bvh;

    rtc_memory_monitor_func(stats, unaccounted_mem, true);
    unaccounted_mem = 0;

    int geom_prim_offset = geom->prim_offset;

    /* fill in node indexes for instances */
    pack.object_node[object_offset++] = prim_offset;

    geometry_map[geom] = pack.object_node[object_offset - 1];

    /* merge primitive, object and triangle indexes */
    if (bvh->pack.prim_index.size()) {
      size_t bvh_prim_index_size = bvh->pack.prim_index.size();
      int *bvh_prim_index = &bvh->pack.prim_index[0];
      int *bvh_prim_type = &bvh->pack.prim_type[0];
      uint *bvh_prim_tri_index = &bvh->pack.prim_tri_index[0];

      for (size_t i = 0; i < bvh_prim_index_size; ++i) {
        if (bvh->pack.prim_type[i] & PRIMITIVE_ALL_CURVE) {
          pack_prim_index[pack_prim_index_offset] = bvh_prim_index[i] + geom_prim_offset;
          pack_prim_tri_index[pack_prim_index_offset] = -1;
        }
        else {
          pack_prim_index[pack_prim_index_offset] = bvh_prim_index[i] + geom_prim_offset;
          pack_prim_tri_index[pack_prim_index_offset] = bvh_prim_tri_index[i] +
                                                        pack_prim_tri_verts_offset;
        }

        pack_prim_type[pack_prim_index_offset] = bvh_prim_type[i];
        pack_prim_object[pack_prim_index_offset] = 0;

        ++pack_prim_index_offset;
      }
    }

    /* Merge triangle vertices data. */
    if (bvh->pack.prim_tri_verts.size()) {
      const size_t prim_tri_size = bvh->pack.prim_tri_verts.size();
      memcpy(pack_prim_tri_verts + pack_prim_tri_verts_offset,
             &bvh->pack.prim_tri_verts[0],
             prim_tri_size * sizeof(float4));
      pack_prim_tri_verts_offset += prim_tri_size;
    }

    prim_offset += bvh->pack.prim_index.size();
  }
}

void BVHEmbree::refit_nodes()
{
  /* Update all vertex buffers, then tell Embree to rebuild/-fit the BVHs. */
  unsigned geom_id = 0;
  foreach (Object *ob, objects) {
    if (!params.top_level || (ob->is_traceable() && !ob->geometry->is_instanced())) {
      Geometry *geom = ob->geometry;

      if (geom->type == Geometry::MESH) {
        Mesh *mesh = static_cast<Mesh *>(geom);
        if (mesh->num_triangles() > 0) {
          update_tri_vertex_buffer(rtcGetGeometry(scene, geom_id), mesh);
          rtcCommitGeometry(rtcGetGeometry(scene, geom_id));
        }
      }
      else if (geom->type == Geometry::HAIR) {
        Hair *hair = static_cast<Hair *>(geom);
        if (hair->num_curves() > 0) {
          update_curve_vertex_buffer(rtcGetGeometry(scene, geom_id + 1), hair);
          rtcCommitGeometry(rtcGetGeometry(scene, geom_id + 1));
        }
      }
    }
    geom_id += 2;
  }
  rtcCommitScene(scene);
}
CCL_NAMESPACE_END

#endif /* WITH_EMBREE */
