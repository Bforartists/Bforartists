/* SPDX-License-Identifier: Apache-2.0
 * Copyright 2021-2022 Intel Corporation */

#pragma once

#ifdef WITH_ONEAPI

#  include <stddef.h>

/* NOTE(@nsirgien): Should match underlying type in the declaration inside "kernel/types.h"
 * TODO: use kernel/types.h directly. */
enum DeviceKernel : int;

#  ifndef CYCLES_KERNEL_ONEAPI_EXPORT
#    ifdef _WIN32
#      if defined(ONEAPI_EXPORT)
#        define CYCLES_KERNEL_ONEAPI_EXPORT extern __declspec(dllexport)
#      else
#        define CYCLES_KERNEL_ONEAPI_EXPORT extern __declspec(dllimport)
#      endif
#    else
#      define CYCLES_KERNEL_ONEAPI_EXPORT
#    endif
#  endif

class SyclQueue;

typedef void (*OneAPIErrorCallback)(const char *error, void *user_ptr);

struct KernelContext {
  /* Queue, associated with selected device */
  SyclQueue *queue;
  /* Pointer to USM device memory with all global/constant allocation on this device */
  void *kernel_globals;
};

/* Use extern C linking so that the symbols can be easily load from the dynamic library at runtime.
 */
#  ifdef __cplusplus
extern "C" {
#  endif

CYCLES_KERNEL_ONEAPI_EXPORT bool oneapi_run_test_kernel(SyclQueue *queue_);
CYCLES_KERNEL_ONEAPI_EXPORT void oneapi_set_error_cb(OneAPIErrorCallback cb, void *user_ptr);
CYCLES_KERNEL_ONEAPI_EXPORT size_t oneapi_kernel_preferred_local_size(
    SyclQueue *queue, const DeviceKernel kernel, const size_t kernel_global_size);
CYCLES_KERNEL_ONEAPI_EXPORT bool oneapi_enqueue_kernel(KernelContext *context,
                                                       int kernel,
                                                       size_t global_size,
                                                       void **args);
CYCLES_KERNEL_ONEAPI_EXPORT bool oneapi_load_kernels(SyclQueue *queue,
                                                     const unsigned int requested_features);
#  ifdef __cplusplus
}
#  endif
#endif /* WITH_ONEAPI */
