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

#pragma once

#include "device/device_memory.h"

#include "kernel/kernel_types.h"

#include "util/util_function.h"

CCL_NAMESPACE_BEGIN

class Device;
class Progress;

enum ShaderEvalType {
  SHADER_EVAL_DISPLACE,
  SHADER_EVAL_BACKGROUND,
};

/* ShaderEval class performs shader evaluation for background light and displacement. */
class ShaderEval {
 public:
  ShaderEval(Device *device, Progress &progress);

  /* Evaluate shader at points specified by KernelShaderEvalInput and write out
   * RGBA colors to output. */
  bool eval(const ShaderEvalType type,
            const int max_num_points,
            const function<int(device_vector<KernelShaderEvalInput> &)> &fill_input,
            const function<void(device_vector<float4> &)> &read_output);

 protected:
  bool eval_cpu(Device *device,
                const ShaderEvalType type,
                device_vector<KernelShaderEvalInput> &input,
                device_vector<float4> &output);
  bool eval_gpu(Device *device,
                const ShaderEvalType type,
                device_vector<KernelShaderEvalInput> &input,
                device_vector<float4> &output);

  Device *device_;
  Progress &progress_;
};

CCL_NAMESPACE_END
