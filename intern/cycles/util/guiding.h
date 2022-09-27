/* SPDX-License-Identifier: Apache-2.0
 * Copyright 2022 Blender Foundation */

#pragma once

#ifdef WITH_PATH_GUIDING
#  include <openpgl/cpp/OpenPGL.h>
#  include <openpgl/version.h>
#endif

#include "util/system.h"

CCL_NAMESPACE_BEGIN

static int guiding_device_type()
{
#ifdef WITH_PATH_GUIDING
#  if defined(__ARM_NEON)
  return 8;
#  else
#    if OPENPGL_VERSION_MINOR >= 4
  if (system_cpu_support_avx2()) {
    return 8;
  }
#    endif
  if (system_cpu_support_sse41()) {
    return 4;
  }
  return 0;
#  endif
#else
  return 0;
#endif
}

static inline bool guiding_supported()
{
  return guiding_device_type() != 0;
}

CCL_NAMESPACE_END
