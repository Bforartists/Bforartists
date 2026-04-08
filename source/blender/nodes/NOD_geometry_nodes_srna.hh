/* SPDX-FileCopyrightText: 2025 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include "BLI_resource_scope.hh"

#include "RNA_types.hh"

namespace blender {

struct StructRNA;
struct bNodeTree;

namespace nodes {

/**
 * Shared across all socket types, though some entries don't make sense for some types.
 */
enum class GeometryNodesInputType {
  Fallback = 0,
  Value = 1,
  Attribute = 2,
  Layer = 3,
};

extern const EnumPropertyItem geometry_nodes_input_type_items_fallback[];
extern const EnumPropertyItem geometry_nodes_input_type_items_value[];
extern const EnumPropertyItem geometry_nodes_input_type_items_value_or_attribute[];
extern const EnumPropertyItem geometry_nodes_input_type_items_value_or_attribute_or_layer[];

/**
 * Contains a runtime registration of RNA types generated based on the node group's interface for
 * a particular context. These RNA types are not registered in the global list, but owned by the
 * node group so that RNA access to interface properties works as long as the node group exists.
 */
struct GeneratedTreeSrnaData {
  ResourceScope scope;
  StructRNA *properties_struct;
  BlenderRNA *generated_rna;
  GeneratedTreeSrnaData();
  ~GeneratedTreeSrnaData();
};

std::shared_ptr<GeneratedTreeSrnaData> create_geometry_nodes_rna_for_modifier(
    const bNodeTree &tree);

}  // namespace nodes
}  // namespace blender
