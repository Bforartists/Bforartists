/*
 * Copyright 2011-2014 Blender Foundation
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

#ifndef __BAKE_H__
#define __BAKE_H__

#include "device/device.h"
#include "render/scene.h"

#include "util/util_progress.h"
#include "util/util_vector.h"

CCL_NAMESPACE_BEGIN

class BakeManager {
 public:
  BakeManager();
  ~BakeManager();

  void set(Scene *scene, const std::string &object_name, ShaderEvalType type, int pass_filter);
  bool get_baking();

  void device_update(Device *device, DeviceScene *dscene, Scene *scene, Progress &progress);
  void device_free(Device *device, DeviceScene *dscene);

  bool need_update;

 private:
  ShaderEvalType type;
  int pass_filter;
  std::string object_name;
};

CCL_NAMESPACE_END

#endif /* __BAKE_H__ */
