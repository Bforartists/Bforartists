/*
 * Copyright 2011-2021 Blender Foundation
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

/* Device data taken from HIP occupancy calculator.
 *
 * Terminology
 * - HIP GPUs have multiple streaming multiprocessors
 * - Each multiprocessor executes multiple thread blocks
 * - Each thread block contains a number of threads, also known as the block size
 * - Multiprocessors have a fixed number of registers, and the amount of registers
 *   used by each threads limits the number of threads per block.
 */

/* Launch Bound Definitions */
#define GPU_MULTIPRESSOR_MAX_REGISTERS 65536
#define GPU_MULTIPROCESSOR_MAX_BLOCKS 64
#define GPU_BLOCK_MAX_THREADS 1024
#define GPU_THREAD_MAX_REGISTERS 255

#define GPU_KERNEL_BLOCK_NUM_THREADS 1024
#define GPU_KERNEL_MAX_REGISTERS 64

/* Compute number of threads per block and minimum blocks per multiprocessor
 * given the maximum number of registers per thread. */

#define ccl_gpu_kernel_threads(block_num_threads) \
  extern "C" __global__ void __launch_bounds__(block_num_threads)

#define ccl_gpu_kernel_threads_registers(block_num_threads, thread_num_registers) \
  extern "C" __global__ void __launch_bounds__(block_num_threads, \
                                               GPU_MULTIPRESSOR_MAX_REGISTERS / \
                                                   (block_num_threads * thread_num_registers))

/* allow ccl_gpu_kernel to accept 1 or 2 parameters */
#define SELECT_MACRO(_1, _2, NAME, ...) NAME
#define ccl_gpu_kernel(...) \
  SELECT_MACRO(__VA_ARGS__, ccl_gpu_kernel_threads_registers, ccl_gpu_kernel_threads)(__VA_ARGS__)

#define ccl_gpu_kernel_signature(name, ...) kernel_gpu_##name(__VA_ARGS__)

#define ccl_gpu_kernel_call(x) x

/* define a function object where "func" is the lambda body, and additional parameters are used to
 * specify captured state  */
#define ccl_gpu_kernel_lambda(func, ...) \
  struct KernelLambda { \
    __VA_ARGS__; \
    __device__ int operator()(const int state) \
    { \
      return (func); \
    } \
  } ccl_gpu_kernel_lambda_pass; \
  ccl_gpu_kernel_lambda_pass

/* sanity checks */

#if GPU_KERNEL_BLOCK_NUM_THREADS > GPU_BLOCK_MAX_THREADS
#  error "Maximum number of threads per block exceeded"
#endif

#if GPU_MULTIPRESSOR_MAX_REGISTERS / (GPU_KERNEL_BLOCK_NUM_THREADS * GPU_KERNEL_MAX_REGISTERS) > \
    GPU_MULTIPROCESSOR_MAX_BLOCKS
#  error "Maximum number of blocks per multiprocessor exceeded"
#endif

#if GPU_KERNEL_MAX_REGISTERS > GPU_THREAD_MAX_REGISTERS
#  error "Maximum number of registers per thread exceeded"
#endif
