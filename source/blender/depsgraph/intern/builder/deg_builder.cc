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
 * The Original Code is Copyright (C) 2016 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup depsgraph
 */

#include "intern/builder/deg_builder.h"

#include <cstring>

#include "DNA_ID.h"
#include "DNA_anim_types.h"
#include "DNA_armature_types.h"
#include "DNA_layer_types.h"
#include "DNA_object_types.h"

#include "BLI_stack.h"
#include "BLI_utildefines.h"

#include "BKE_action.h"

#include "intern/builder/deg_builder_cache.h"
#include "intern/builder/deg_builder_remove_noop.h"
#include "intern/depsgraph.h"
#include "intern/depsgraph_relation.h"
#include "intern/depsgraph_tag.h"
#include "intern/depsgraph_type.h"
#include "intern/eval/deg_eval_copy_on_write.h"
#include "intern/node/deg_node.h"
#include "intern/node/deg_node_component.h"
#include "intern/node/deg_node_id.h"
#include "intern/node/deg_node_operation.h"

#include "DEG_depsgraph.h"

namespace DEG {

bool deg_check_id_in_depsgraph(const Depsgraph *graph, ID *id_orig)
{
  IDNode *id_node = graph->find_id_node(id_orig);
  return id_node != nullptr;
}

bool deg_check_base_in_depsgraph(const Depsgraph *graph, Base *base)
{
  Object *object_orig = base->base_orig->object;
  IDNode *id_node = graph->find_id_node(&object_orig->id);
  if (id_node == nullptr) {
    return false;
  }
  return id_node->has_base;
}

/*******************************************************************************
 * Base class for builders.
 */

DepsgraphBuilder::DepsgraphBuilder(Main *bmain, Depsgraph *graph, DepsgraphBuilderCache *cache)
    : bmain_(bmain), graph_(graph), cache_(cache)
{
}

DepsgraphBuilder::~DepsgraphBuilder()
{
}

bool DepsgraphBuilder::need_pull_base_into_graph(Base *base)
{
  /* Simple check: enabled bases are always part of dependency graph. */
  const int base_flag = (graph_->mode == DAG_EVAL_VIEWPORT) ? BASE_ENABLED_VIEWPORT :
                                                              BASE_ENABLED_RENDER;
  if (base->flag & base_flag) {
    return true;
  }
  /* More involved check: since we don't support dynamic changes in dependency graph topology and
   * all visible objects are to be part of dependency graph, we pull all objects which has animated
   * visibility. */
  Object *object = base->object;
  AnimatedPropertyID property_id;
  if (graph_->mode == DAG_EVAL_VIEWPORT) {
    property_id = AnimatedPropertyID(&object->id, &RNA_Object, "hide_viewport");
  }
  else if (graph_->mode == DAG_EVAL_RENDER) {
    property_id = AnimatedPropertyID(&object->id, &RNA_Object, "hide_render");
  }
  else {
    BLI_assert(!"Unknown evaluation mode.");
    return false;
  }
  return cache_->isPropertyAnimated(&object->id, property_id);
}

bool DepsgraphBuilder::check_pchan_has_bbone(Object *object, const bPoseChannel *pchan)
{
  BLI_assert(object->type == OB_ARMATURE);
  if (pchan == nullptr || pchan->bone == nullptr) {
    return false;
  }
  /* We don't really care whether segments are higher than 1 due to static user input (as in,
   * rigger entered value like 3 manually), or due to animation. In either way we need to create
   * special evaluation. */
  if (pchan->bone->segments > 1) {
    return true;
  }
  bArmature *armature = static_cast<bArmature *>(object->data);
  AnimatedPropertyID property_id(&armature->id, &RNA_Bone, pchan->bone, "bbone_segments");
  /* Check both Object and Armature animation data, because drivers modifying Armature
   * state could easily be created in the Object AnimData. */
  return cache_->isPropertyAnimated(&object->id, property_id) ||
         cache_->isPropertyAnimated(&armature->id, property_id);
}

bool DepsgraphBuilder::check_pchan_has_bbone_segments(Object *object, const bPoseChannel *pchan)
{
  /* Proxies don't have BONE_SEGMENTS */
  if (ID_IS_LINKED(object) && object->proxy_from != nullptr) {
    return false;
  }
  return check_pchan_has_bbone(object, pchan);
}

bool DepsgraphBuilder::check_pchan_has_bbone_segments(Object *object, const char *bone_name)
{
  const bPoseChannel *pchan = BKE_pose_channel_find_name(object->pose, bone_name);
  return check_pchan_has_bbone_segments(object, pchan);
}

/*******************************************************************************
 * Builder finalizer.
 */

namespace {

void deg_graph_build_flush_visibility(Depsgraph *graph)
{
  enum {
    DEG_NODE_VISITED = (1 << 0),
  };

  BLI_Stack *stack = BLI_stack_new(sizeof(OperationNode *), "DEG flush layers stack");
  for (IDNode *id_node : graph->id_nodes) {
    for (ComponentNode *comp_node : id_node->components.values()) {
      comp_node->affects_directly_visible |= id_node->is_directly_visible;
    }
  }
  for (OperationNode *op_node : graph->operations) {
    op_node->custom_flags = 0;
    op_node->num_links_pending = 0;
    for (Relation *rel : op_node->outlinks) {
      if ((rel->from->type == NodeType::OPERATION) && (rel->flag & RELATION_FLAG_CYCLIC) == 0) {
        ++op_node->num_links_pending;
      }
    }
    if (op_node->num_links_pending == 0) {
      BLI_stack_push(stack, &op_node);
      op_node->custom_flags |= DEG_NODE_VISITED;
    }
  }
  while (!BLI_stack_is_empty(stack)) {
    OperationNode *op_node;
    BLI_stack_pop(stack, &op_node);
    /* Flush layers to parents. */
    for (Relation *rel : op_node->inlinks) {
      if (rel->from->type == NodeType::OPERATION) {
        OperationNode *op_from = (OperationNode *)rel->from;
        op_from->owner->affects_directly_visible |= op_node->owner->affects_directly_visible;
      }
    }
    /* Schedule parent nodes. */
    for (Relation *rel : op_node->inlinks) {
      if (rel->from->type == NodeType::OPERATION) {
        OperationNode *op_from = (OperationNode *)rel->from;
        if ((rel->flag & RELATION_FLAG_CYCLIC) == 0) {
          BLI_assert(op_from->num_links_pending > 0);
          --op_from->num_links_pending;
        }
        if ((op_from->num_links_pending == 0) && (op_from->custom_flags & DEG_NODE_VISITED) == 0) {
          BLI_stack_push(stack, &op_from);
          op_from->custom_flags |= DEG_NODE_VISITED;
        }
      }
    }
  }
  BLI_stack_free(stack);
}

}  // namespace

void deg_graph_build_finalize(Main *bmain, Depsgraph *graph)
{
  /* Make sure dependencies of visible ID datablocks are visible. */
  deg_graph_build_flush_visibility(graph);
  deg_graph_remove_unused_noops(graph);

  /* Re-tag IDs for update if it was tagged before the relations
   * update tag. */
  for (IDNode *id_node : graph->id_nodes) {
    ID *id_orig = id_node->id_orig;
    id_node->finalize_build(graph);
    int flag = 0;
    /* Tag rebuild if special evaluation flags changed. */
    if (id_node->eval_flags != id_node->previous_eval_flags) {
      flag |= ID_RECALC_TRANSFORM | ID_RECALC_GEOMETRY;
    }
    /* Tag rebuild if the custom data mask changed. */
    if (id_node->customdata_masks != id_node->previous_customdata_masks) {
      flag |= ID_RECALC_GEOMETRY;
    }
    if (!deg_copy_on_write_is_expanded(id_node->id_cow)) {
      flag |= ID_RECALC_COPY_ON_WRITE;
      /* This means ID is being added to the dependency graph first
       * time, which is similar to "ob-visible-change" */
      if (GS(id_orig->name) == ID_OB) {
        flag |= ID_RECALC_TRANSFORM | ID_RECALC_GEOMETRY;
      }
    }
    /* Restore recalc flags from original ID, which could possibly contain recalc flags set by
     * an operator and then were carried on by the undo system. */
    flag |= id_orig->recalc;
    if (flag != 0) {
      graph_id_tag_update(bmain, graph, id_node->id_orig, flag, DEG_UPDATE_SOURCE_RELATIONS);
    }
  }
}

}  // namespace DEG
