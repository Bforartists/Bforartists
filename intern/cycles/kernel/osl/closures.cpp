/* SPDX-FileCopyrightText: 2009-2010 Sony Pictures Imageworks Inc., et al. All Rights Reserved.
 * SPDX-FileCopyrightText: 2011-2022 Blender Foundation
 *
 * SPDX-License-Identifier: BSD-3-Clause
 *
 * Adapted code from Open Shading Language. */

#include <OSL/genclosure.h>
#include <OSL/oslclosure.h>

#include "kernel/types.h"

#include "kernel/osl/globals.h"
#include "kernel/osl/services.h"

#include "util/math.h"
#include "util/param.h"

#include "kernel/globals.h"

#include "kernel/geom/object.h"
#include "kernel/util/differential.h"

#include "kernel/osl/osl.h"

#define TO_VEC3(v) OSL::Vec3(v.x, v.y, v.z)
#define TO_FLOAT3(v) make_float3(v[0], v[1], v[2])

CCL_NAMESPACE_BEGIN

static_assert(sizeof(OSLClosure) == sizeof(OSL::ClosureColor) &&
              sizeof(OSLClosureAdd) == sizeof(OSL::ClosureAdd) &&
              sizeof(OSLClosureMul) == sizeof(OSL::ClosureMul) &&
              sizeof(OSLClosureComponent) == sizeof(OSL::ClosureComponent));
static_assert(sizeof(ShaderGlobals) == sizeof(OSL::ShaderGlobals) &&
              offsetof(ShaderGlobals, Ci) == offsetof(OSL::ShaderGlobals, Ci));

/* Registration */

#define OSL_CLOSURE_STRUCT_BEGIN(Upper, lower) \
  static OSL::ClosureParam *osl_closure_##lower##_params() \
  { \
    static OSL::ClosureParam params[] = {
#define OSL_CLOSURE_STRUCT_END(Upper, lower) \
  CLOSURE_STRING_KEYPARAM(Upper##Closure, label, "label"), CLOSURE_FINISH_PARAM(Upper##Closure) \
  } \
  ; \
  return params; \
  }
#define OSL_CLOSURE_STRUCT_MEMBER(Upper, TYPE, type, name, key) \
  CLOSURE_##TYPE##_KEYPARAM(Upper##Closure, name, key),
#define OSL_CLOSURE_STRUCT_ARRAY_MEMBER(Upper, TYPE, type, name, key, size) \
  CLOSURE_##TYPE##_ARRAY_PARAM(Upper##Closure, name, size),

#include "closures_template.h"

static OSL::ClosureParam *osl_closure_layer_params()
{
  static OSL::ClosureParam params[] = {CLOSURE_CLOSURE_PARAM(LayerClosure, top),
                                       CLOSURE_CLOSURE_PARAM(LayerClosure, base),
                                       CLOSURE_FINISH_PARAM(LayerClosure)};
  return params;
}

void OSLRenderServices::register_closures(OSL::ShadingSystem *ss)
{
#define OSL_CLOSURE_STRUCT_BEGIN(Upper, lower) \
  ss->register_closure( \
      #lower, OSL_CLOSURE_##Upper##_ID, osl_closure_##lower##_params(), nullptr, nullptr);

#include "closures_template.h"
  ss->register_closure(
      "layer", OSL_CLOSURE_LAYER_ID, osl_closure_layer_params(), nullptr, nullptr);
}

/* Surface & Background */

template<>
void osl_eval_nodes<SHADER_TYPE_SURFACE>(const ThreadKernelGlobalsCPU *kg,
                                         const void *state,
                                         ShaderData *sd,
                                         const uint32_t path_flag)
{
  /* setup shader globals from shader data */
  shaderdata_to_shaderglobals(
      kg, sd, path_flag, reinterpret_cast<ShaderGlobals *>(&kg->osl.shader_globals));

  /* clear trace data */
  kg->osl.tracedata.init = false;

  /* Used by render-services. */
  sd->osl_globals = kg;
  if (path_flag & PATH_RAY_SHADOW) {
    sd->osl_path_state = nullptr;
    sd->osl_shadow_path_state = (const IntegratorShadowStateCPU *)state;
  }
  else {
    sd->osl_path_state = (const IntegratorStateCPU *)state;
    sd->osl_shadow_path_state = nullptr;
  }

  /* execute shader for this point */
  OSL::ShadingSystem *ss = (OSL::ShadingSystem *)kg->osl.ss;
  OSL::ShaderGlobals *globals = &kg->osl.shader_globals;
  OSL::ShadingContext *octx = kg->osl.context;
  const int shader = sd->shader & SHADER_MASK;

  if (sd->object == OBJECT_NONE && sd->lamp == LAMP_NONE) {
    /* background */
    if (kg->osl.globals->background_state) {
#if OSL_LIBRARY_VERSION_CODE >= 11304
      ss->execute(*octx,
                  *(kg->osl.globals->background_state),
                  kg->osl.thread_index,
                  0,
                  *globals,
                  nullptr,
                  nullptr);
#else
      ss->execute(octx, *(kg->osl.globals->background_state), *globals);
#endif
    }
  }
  else {
    /* automatic bump shader */
    if (kg->osl.globals->bump_state[shader]) {
      /* save state */
      const float3 P = sd->P;
      const float dP = sd->dP;
      const OSL::Vec3 dPdx = globals->dPdx;
      const OSL::Vec3 dPdy = globals->dPdy;

      /* set state as if undisplaced */
      if (sd->flag & SD_HAS_DISPLACEMENT) {
        float data[9];
        const bool found = kg->osl.globals->services->get_attribute(
            sd,
            true,
            OSLRenderServices::u_empty,
            TypeVector,
            OSLRenderServices::u_geom_undisplaced,
            data);
        (void)found;
        assert(found);

        differential3 tmp_dP;
        sd->P = make_float3(data[0], data[1], data[2]);
        tmp_dP.dx = make_float3(data[3], data[4], data[5]);
        tmp_dP.dy = make_float3(data[6], data[7], data[8]);

        object_position_transform(kg, sd, &sd->P);
        object_dir_transform(kg, sd, &tmp_dP.dx);
        object_dir_transform(kg, sd, &tmp_dP.dy);

        sd->dP = differential_make_compact(tmp_dP);

        globals->P = TO_VEC3(sd->P);
        globals->dPdx = TO_VEC3(tmp_dP.dx);
        globals->dPdy = TO_VEC3(tmp_dP.dy);
      }

/* execute bump shader */
#if OSL_LIBRARY_VERSION_CODE >= 11304
      ss->execute(*octx,
                  *(kg->osl.globals->bump_state[shader]),
                  kg->osl.thread_index,
                  0,
                  *globals,
                  nullptr,
                  nullptr);
#else
      ss->execute(octx, *(kg->osl.globals->bump_state[shader]), *globals);
#endif

      /* reset state */
      sd->P = P;
      sd->dP = dP;

      globals->P = TO_VEC3(P);
      globals->dPdx = TO_VEC3(dPdx);
      globals->dPdy = TO_VEC3(dPdy);
    }

    /* surface shader */
    if (kg->osl.globals->surface_state[shader]) {
#if OSL_LIBRARY_VERSION_CODE >= 11304
      ss->execute(*octx,
                  *(kg->osl.globals->surface_state[shader]),
                  kg->osl.thread_index,
                  0,
                  *globals,
                  nullptr,
                  nullptr);
#else
      ss->execute(octx, *(kg->osl.globals->surface_state[shader]), *globals);
#endif
    }
  }

  /* flatten closure tree */
  if (globals->Ci) {
    flatten_closure_tree(kg, sd, path_flag, reinterpret_cast<OSLClosure *>(globals->Ci));
  }
}

/* Volume */

template<>
void osl_eval_nodes<SHADER_TYPE_VOLUME>(const ThreadKernelGlobalsCPU *kg,
                                        const void *state,
                                        ShaderData *sd,
                                        const uint32_t path_flag)
{
  /* setup shader globals from shader data */
  shaderdata_to_shaderglobals(
      kg, sd, path_flag, reinterpret_cast<ShaderGlobals *>(&kg->osl.shader_globals));

  /* clear trace data */
  kg->osl.tracedata.init = false;

  /* Used by render-services. */
  sd->osl_globals = kg;
  if (path_flag & PATH_RAY_SHADOW) {
    sd->osl_path_state = nullptr;
    sd->osl_shadow_path_state = (const IntegratorShadowStateCPU *)state;
  }
  else {
    sd->osl_path_state = (const IntegratorStateCPU *)state;
    sd->osl_shadow_path_state = nullptr;
  }

  /* execute shader */
  OSL::ShadingSystem *ss = (OSL::ShadingSystem *)kg->osl.ss;
  OSL::ShaderGlobals *globals = &kg->osl.shader_globals;
  OSL::ShadingContext *octx = kg->osl.context;
  const int shader = sd->shader & SHADER_MASK;

  if (kg->osl.globals->volume_state[shader]) {
#if OSL_LIBRARY_VERSION_CODE >= 11304
    ss->execute(*octx,
                *(kg->osl.globals->volume_state[shader]),
                kg->osl.thread_index,
                0,
                *globals,
                nullptr,
                nullptr);
#else
    ss->execute(octx, *(kg->osl.globals->volume_state[shader]), *globals);
#endif
  }

  /* flatten closure tree */
  if (globals->Ci) {
    flatten_closure_tree(kg, sd, path_flag, reinterpret_cast<OSLClosure *>(globals->Ci));
  }
}

/* Displacement */

template<>
void osl_eval_nodes<SHADER_TYPE_DISPLACEMENT>(const ThreadKernelGlobalsCPU *kg,
                                              const void *state,
                                              ShaderData *sd,
                                              const uint32_t path_flag)
{
  /* setup shader globals from shader data */
  shaderdata_to_shaderglobals(
      kg, sd, path_flag, reinterpret_cast<ShaderGlobals *>(&kg->osl.shader_globals));

  /* clear trace data */
  kg->osl.tracedata.init = false;

  /* Used by render-services. */
  sd->osl_globals = kg;
  sd->osl_path_state = (const IntegratorStateCPU *)state;
  sd->osl_shadow_path_state = nullptr;

  /* execute shader */
  OSL::ShadingSystem *ss = (OSL::ShadingSystem *)kg->osl.ss;
  OSL::ShaderGlobals *globals = &kg->osl.shader_globals;
  OSL::ShadingContext *octx = kg->osl.context;
  const int shader = sd->shader & SHADER_MASK;

  if (kg->osl.globals->displacement_state[shader]) {
#if OSL_LIBRARY_VERSION_CODE >= 11304
    ss->execute(*octx,
                *(kg->osl.globals->displacement_state[shader]),
                kg->osl.thread_index,
                0,
                *globals,
                nullptr,
                nullptr);
#else
    ss->execute(octx, *(kg->osl.globals->displacement_state[shader]), *globals);
#endif
  }

  /* get back position */
  sd->P = TO_FLOAT3(globals->P);
}

CCL_NAMESPACE_END
