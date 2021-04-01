/*
 * Copyright 2011-2013 Blender Foundation
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

#ifndef __LIGHT_H__
#define __LIGHT_H__

#include "kernel/kernel_types.h"

#include "graph/node.h"

/* included as Light::set_shader defined through NODE_SOCKET_API does not select
 * the right Node::set overload as it does not know that Shader is a Node */
#include "render/shader.h"

#include "util/util_ies.h"
#include "util/util_thread.h"
#include "util/util_types.h"
#include "util/util_vector.h"

CCL_NAMESPACE_BEGIN

class Device;
class DeviceScene;
class Object;
class Progress;
class Scene;
class Shader;

class Light : public Node {
 public:
  NODE_DECLARE;

  Light();

  NODE_SOCKET_API(LightType, light_type)
  NODE_SOCKET_API(float3, strength)
  NODE_SOCKET_API(float3, co)

  NODE_SOCKET_API(float3, dir)
  NODE_SOCKET_API(float, size)
  NODE_SOCKET_API(float, angle)

  NODE_SOCKET_API(float3, axisu)
  NODE_SOCKET_API(float, sizeu)
  NODE_SOCKET_API(float3, axisv)
  NODE_SOCKET_API(float, sizev)
  NODE_SOCKET_API(bool, round)
  NODE_SOCKET_API(float, spread)

  NODE_SOCKET_API(Transform, tfm)

  NODE_SOCKET_API(int, map_resolution)

  NODE_SOCKET_API(float, spot_angle)
  NODE_SOCKET_API(float, spot_smooth)

  NODE_SOCKET_API(bool, cast_shadow)
  NODE_SOCKET_API(bool, use_mis)
  NODE_SOCKET_API(bool, use_diffuse)
  NODE_SOCKET_API(bool, use_glossy)
  NODE_SOCKET_API(bool, use_transmission)
  NODE_SOCKET_API(bool, use_scatter)

  NODE_SOCKET_API(bool, is_portal)
  NODE_SOCKET_API(bool, is_enabled)

  NODE_SOCKET_API(Shader *, shader)
  NODE_SOCKET_API(int, samples)
  NODE_SOCKET_API(int, max_bounces)
  NODE_SOCKET_API(uint, random_id)

  void tag_update(Scene *scene);

  /* Check whether the light has contribution the scene. */
  bool has_contribution(Scene *scene);

  friend class LightManager;
};

class LightManager {
 public:
  enum : uint32_t {
    MESH_NEED_REBUILD = (1 << 0),
    EMISSIVE_MESH_MODIFIED = (1 << 1),
    LIGHT_MODIFIED = (1 << 2),
    LIGHT_ADDED = (1 << 3),
    LIGHT_REMOVED = (1 << 4),
    OBJECT_MANAGER = (1 << 5),
    SHADER_COMPILED = (1 << 6),
    SHADER_MODIFIED = (1 << 7),

    /* tag everything in the manager for an update */
    UPDATE_ALL = ~0u,

    UPDATE_NONE = 0u,
  };

  bool use_light_visibility;

  /* Need to update background (including multiple importance map) */
  bool need_update_background;

  LightManager();
  ~LightManager();

  /* IES texture management */
  int add_ies(const string &ies);
  int add_ies_from_file(const string &filename);
  void remove_ies(int slot);

  void device_update(Device *device, DeviceScene *dscene, Scene *scene, Progress &progress);
  void device_free(Device *device, DeviceScene *dscene, const bool free_background = true);

  void tag_update(Scene *scene, uint32_t flag);

  bool need_update() const;

  /* Check whether there is a background light. */
  bool has_background_light(Scene *scene);

 protected:
  /* Optimization: disable light which is either unsupported or
   * which doesn't contribute to the scene or which is only used for MIS
   * and scene doesn't need MIS.
   */
  void test_enabled_lights(Scene *scene);

  void device_update_points(Device *device, DeviceScene *dscene, Scene *scene);
  void device_update_distribution(Device *device,
                                  DeviceScene *dscene,
                                  Scene *scene,
                                  Progress &progress);
  void device_update_background(Device *device,
                                DeviceScene *dscene,
                                Scene *scene,
                                Progress &progress);
  void device_update_ies(DeviceScene *dscene);

  /* Check whether light manager can use the object as a light-emissive. */
  bool object_usable_as_light(Object *object);

  struct IESSlot {
    IESFile ies;
    uint hash;
    int users;
  };

  vector<IESSlot *> ies_slots;
  thread_mutex ies_mutex;

  bool last_background_enabled;
  int last_background_resolution;

  uint32_t update_flags;
};

CCL_NAMESPACE_END

#endif /* __LIGHT_H__ */
