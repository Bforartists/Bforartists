/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2013 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup depsgraph
 */

#include "intern/builder/deg_builder_relations.h"

#include "DNA_scene_types.h"

namespace DEG {

void DepsgraphRelationBuilder::build_scene_render(Scene *scene, ViewLayer *view_layer)
{
  scene_ = scene;
  const bool build_compositor = (scene->r.scemode & R_DOCOMP);
  const bool build_sequencer = (scene->r.scemode & R_DOSEQ);
  build_scene_parameters(scene);
  build_animdata(&scene->id);
  build_scene_audio(scene);
  if (build_compositor) {
    build_scene_compositor(scene);
  }
  if (build_sequencer) {
    build_scene_sequencer(scene);
    build_scene_speakers(scene, view_layer);
  }
  if (scene->camera != nullptr) {
    build_object(nullptr, scene->camera);
  }
}

void DepsgraphRelationBuilder::build_scene_parameters(Scene *scene)
{
  if (built_map_.checkIsBuiltAndTag(scene, BuilderMap::TAG_PARAMETERS)) {
    return;
  }
  build_idproperties(scene->id.properties);
  build_parameters(&scene->id);
  OperationKey parameters_eval_key(
      &scene->id, NodeType::PARAMETERS, OperationCode::PARAMETERS_EXIT);
  OperationKey scene_eval_key(&scene->id, NodeType::PARAMETERS, OperationCode::SCENE_EVAL);
  add_relation(parameters_eval_key, scene_eval_key, "Parameters -> Scene Eval");
}

void DepsgraphRelationBuilder::build_scene_compositor(Scene *scene)
{
  if (built_map_.checkIsBuiltAndTag(scene, BuilderMap::TAG_SCENE_COMPOSITOR)) {
    return;
  }
  if (scene->nodetree == nullptr) {
    return;
  }
  build_nodetree(scene->nodetree);
}

}  // namespace DEG
