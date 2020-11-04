/*
 * Copyright 2020 Blender Foundation
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

#include "graph/node.h"

#include "render/mesh.h"

CCL_NAMESPACE_BEGIN

class Volume : public Mesh {
 public:
  NODE_DECLARE

  Volume();

  NODE_SOCKET_API(float, clipping)
  NODE_SOCKET_API(float, step_size)
  NODE_SOCKET_API(bool, object_space)

  virtual void clear(bool preserve_shaders = false) override;
};

CCL_NAMESPACE_END
