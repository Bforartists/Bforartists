/*
 * Copyright 2019 Blender Foundation
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

#ifndef __BLENDER_VIEWPORT_H__
#define __BLENDER_VIEWPORT_H__

#include "MEM_guardedalloc.h"

#include "RNA_access.h"
#include "RNA_blender_cpp.h"
#include "RNA_types.h"

#include "render/film.h"

CCL_NAMESPACE_BEGIN

class BlenderViewportParameters {
 public:
  /* Shader. */
  bool use_scene_world;
  bool use_scene_lights;
  float studiolight_rotate_z;
  float studiolight_intensity;
  float studiolight_background_alpha;
  ustring studiolight_path;

  /* Film. */
  PassType display_pass;

  BlenderViewportParameters();
  explicit BlenderViewportParameters(BL::SpaceView3D &b_v3d);

  /* Check whether any of shading related settings are different from the given parameters. */
  bool shader_modified(const BlenderViewportParameters &other) const;

  /* Check whether any of film related settings are different from the given parameters. */
  bool film_modified(const BlenderViewportParameters &other) const;

  /* Check whether any of settings are different from the given parameters. */
  bool modified(const BlenderViewportParameters &other) const;

  /* Returns truth when a custom shader defined by the viewport is to be used instead of the
   * regular background shader or scene light. */
  bool use_custom_shader() const;
};

PassType update_viewport_display_passes(BL::SpaceView3D &b_v3d, vector<Pass> &passes);

CCL_NAMESPACE_END

#endif
