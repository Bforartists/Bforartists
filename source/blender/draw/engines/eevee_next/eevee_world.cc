/* SPDX-FileCopyrightText: 2021 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup eevee
 */

#include "BKE_lib_id.h"
#include "BKE_node.hh"
#include "BKE_world.h"
#include "DEG_depsgraph_query.hh"
#include "NOD_shader.h"

#include "eevee_instance.hh"

namespace blender::eevee {

/* -------------------------------------------------------------------- */
/** \name Default Material
 *
 * \{ */

DefaultWorldNodeTree::DefaultWorldNodeTree()
{
  bNodeTree *ntree = ntreeAddTree(nullptr, "World Nodetree", ntreeType_Shader->idname);
  bNode *background = nodeAddStaticNode(nullptr, ntree, SH_NODE_BACKGROUND);
  bNode *output = nodeAddStaticNode(nullptr, ntree, SH_NODE_OUTPUT_WORLD);
  bNodeSocket *background_out = nodeFindSocket(background, SOCK_OUT, "Background");
  bNodeSocket *output_in = nodeFindSocket(output, SOCK_IN, "Surface");
  nodeAddLink(ntree, background, background_out, output, output_in);
  nodeSetActive(ntree, output);

  color_socket_ =
      (bNodeSocketValueRGBA *)nodeFindSocket(background, SOCK_IN, "Color")->default_value;
  ntree_ = ntree;
}

DefaultWorldNodeTree::~DefaultWorldNodeTree()
{
  ntreeFreeEmbeddedTree(ntree_);
  MEM_SAFE_FREE(ntree_);
}

/* Configure a default node-tree with the given world. */
bNodeTree *DefaultWorldNodeTree::nodetree_get(::World *wo)
{
  /* WARNING: This function is not thread-safe. Which is not a problem for the moment. */
  copy_v3_fl3(color_socket_->value, wo->horr, wo->horg, wo->horb);
  return ntree_;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name World
 *
 * \{ */

World::~World()
{
  if (default_world_ != nullptr) {
    BKE_id_free(nullptr, default_world_);
  }
}

::World *World::default_world_get()
{
  if (default_world_ == nullptr) {
    default_world_ = static_cast<::World *>(BKE_id_new_nomain(ID_WO, "EEVEEE default world"));
    default_world_->horr = default_world_->horg = default_world_->horb = 0.0f;
    default_world_->use_nodes = 0;
    default_world_->nodetree = nullptr;
    BLI_listbase_clear(&default_world_->gpumaterial);
  }
  return default_world_;
}

void World::sync()
{
  ::World *bl_world = inst_.use_studio_light() ? nullptr : inst_.scene->world;

  bool has_update = false;

  if (bl_world) {
    /* Detect world update before overriding it. */
    WorldHandle wo_handle = inst_.sync.sync_world();
    has_update = wo_handle.recalc != 0;
  }

  /* Sync volume first since its result can override the surface world. */
  sync_volume();

  if (inst_.use_studio_light()) {
    has_update = lookdev_world_.sync(LookdevParameters(inst_.v3d));
    bl_world = lookdev_world_.world_get();
  }
  else if (has_volume_absorption_) {
    bl_world = default_world_get();
  }
  else if (inst_.scene->world != nullptr) {
    bl_world = inst_.scene->world;
  }
  else {
    bl_world = default_world_get();
  }

  bNodeTree *ntree = (bl_world->nodetree && bl_world->use_nodes) ?
                         bl_world->nodetree :
                         default_tree.nodetree_get(bl_world);

  {
    if (has_volume_absorption_) {
      /* Replace world by black world. */
      bl_world = default_world_get();
    }
  }

  inst_.reflection_probes.sync_world(bl_world);
  if (has_update) {
    inst_.reflection_probes.do_world_update_set(true);
  }

  /* We have to manually test here because we have overrides. */
  ::World *orig_world = (::World *)DEG_get_original_id(&bl_world->id);
  if (assign_if_different(prev_original_world, orig_world)) {
    inst_.reflection_probes.do_world_update_set(true);
  }

  GPUMaterial *gpumat = inst_.shaders.world_shader_get(bl_world, ntree, MAT_PIPE_DEFERRED);

  inst_.manager->register_layer_attributes(gpumat);

  float opacity = inst_.use_studio_light() ? lookdev_world_.background_opacity_get() :
                                             inst_.film.background_opacity_get();

  inst_.pipelines.background.sync(gpumat, opacity);
  inst_.pipelines.world.sync(gpumat);
}

void World::sync_volume()
{
  /* Studio lights have no volume shader. */
  ::World *world = inst_.use_studio_light() ? nullptr : inst_.scene->world;

  GPUMaterial *gpumat = nullptr;

  /* Only the scene world nodetree can have volume shader. */
  if (world && world->nodetree && world->use_nodes) {
    gpumat = inst_.shaders.world_shader_get(world, world->nodetree, MAT_PIPE_VOLUME_MATERIAL);
  }

  if (gpumat && (GPU_material_status(gpumat) == GPU_MAT_SUCCESS)) {
    has_volume_ = true;
    has_volume_scatter_ = GPU_material_flag_get(gpumat, GPU_MATFLAG_VOLUME_SCATTER);
    has_volume_absorption_ = GPU_material_flag_get(gpumat, GPU_MATFLAG_VOLUME_ABSORPTION);
  }
  else {
    has_volume_ = has_volume_absorption_ = has_volume_scatter_ = false;
  }

  /* World volume needs to be always synced for correct clearing of parameter buffers. */
  inst_.pipelines.world_volume.sync(gpumat);
}

/** \} */

}  // namespace blender::eevee
