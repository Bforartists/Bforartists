/* SPDX-FileCopyrightText: 2006 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup cmpnodes
 */

#include <algorithm>

#include "FN_multi_function_builder.hh"

#include "NOD_multi_function.hh"

#include "BKE_texture.h"

#include "RNA_access.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "GPU_material.hh"

#include "node_composite_util.hh"

/* **************** MAP VALUE ******************** */

namespace blender::nodes::node_composite_map_value_cc {

NODE_STORAGE_FUNCS(TexMapping)

static void cmp_node_map_value_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Float>("Value")
      .default_value(1.0f)
      .min(0.0f)
      .max(1.0f)
      .compositor_domain_priority(0);
  b.add_output<decl::Float>("Value");
}

static void node_composit_init_map_value(bNodeTree * /*ntree*/, bNode *node)
{
  node->storage = BKE_texture_mapping_add(TEXMAP_TYPE_POINT);
}

static void node_composit_buts_map_value(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiLayout *sub, *col;

  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "offset", UI_ITEM_R_SPLIT_EMPTY_NAME, std::nullopt, ICON_NONE);
  uiItemR(col, ptr, "size", UI_ITEM_R_SPLIT_EMPTY_NAME, std::nullopt, ICON_NONE);

  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "use_min", UI_ITEM_R_SPLIT_EMPTY_NAME, std::nullopt, ICON_NONE);
  sub = uiLayoutColumn(col, false);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_min"));
  uiItemR(sub, ptr, "min", UI_ITEM_R_SPLIT_EMPTY_NAME, "", ICON_NONE);

  col = uiLayoutColumn(layout, true);
  uiItemR(col, ptr, "use_max", UI_ITEM_R_SPLIT_EMPTY_NAME, std::nullopt, ICON_NONE);
  sub = uiLayoutColumn(col, false);
  uiLayoutSetActive(sub, RNA_boolean_get(ptr, "use_max"));
  uiItemR(sub, ptr, "max", UI_ITEM_R_SPLIT_EMPTY_NAME, "", ICON_NONE);
}

using namespace blender::compositor;

static bool get_use_min(const bNode &node)
{
  return node_storage(node).flag & TEXMAP_CLIP_MIN;
}

static bool get_use_max(const bNode &node)
{
  return node_storage(node).flag & TEXMAP_CLIP_MAX;
}

static int node_gpu_material(GPUMaterial *material,
                             bNode *node,
                             bNodeExecData * /*execdata*/,
                             GPUNodeStack *inputs,
                             GPUNodeStack *outputs)
{
  const TexMapping &texture_mapping = node_storage(*node);

  const float use_min = get_use_min(*node);
  const float use_max = get_use_max(*node);

  return GPU_stack_link(material,
                        node,
                        "node_composite_map_value",
                        inputs,
                        outputs,
                        GPU_uniform(texture_mapping.loc),
                        GPU_uniform(texture_mapping.size),
                        GPU_constant(&use_min),
                        GPU_uniform(texture_mapping.min),
                        GPU_constant(&use_max),
                        GPU_uniform(texture_mapping.max));
}

template<bool UseMin, bool UseMax>
static float map_value(
    const float value, const float offset, const float size, const float min, const float max)
{
  float result = (value + offset) * size;

  if constexpr (UseMin) {
    result = std::max(result, min);
  }

  if constexpr (UseMax) {
    result = std::min(result, max);
  }

  return result;
}

static void node_build_multi_function(blender::nodes::NodeMultiFunctionBuilder &builder)
{
  const TexMapping &texture_mapping = node_storage(builder.node());
  const float offset = texture_mapping.loc[0];
  const float size = texture_mapping.size[0];
  const float min = texture_mapping.min[0];
  const float max = texture_mapping.max[0];
  const bool use_min = get_use_min(builder.node());
  const bool use_max = get_use_max(builder.node());

  if (use_min) {
    if (use_max) {
      builder.construct_and_set_matching_fn_cb([=]() {
        return mf::build::SI1_SO<float, float>(
            "Map Value With Min With Max",
            [=](const float value) -> float {
              return map_value<true, true>(value, offset, size, min, max);
            },
            mf::build::exec_presets::AllSpanOrSingle());
      });
    }
    else {
      builder.construct_and_set_matching_fn_cb([=]() {
        return mf::build::SI1_SO<float, float>(
            "Map Value With Min No Max",
            [=](const float value) -> float {
              return map_value<true, false>(value, offset, size, min, max);
            },
            mf::build::exec_presets::AllSpanOrSingle());
      });
    }
  }
  else {
    if (use_max) {
      builder.construct_and_set_matching_fn_cb([=]() {
        return mf::build::SI1_SO<float, float>(
            "Map Value No Min With Max",
            [=](const float value) -> float {
              return map_value<false, true>(value, offset, size, min, max);
            },
            mf::build::exec_presets::AllSpanOrSingle());
      });
    }
    else {
      builder.construct_and_set_matching_fn_cb([=]() {
        return mf::build::SI1_SO<float, float>(
            "Map Value No Min No Max",
            [=](const float value) -> float {
              return map_value<false, false>(value, offset, size, min, max);
            },
            mf::build::exec_presets::AllSpanOrSingle());
      });
    }
  }
}

}  // namespace blender::nodes::node_composite_map_value_cc

void register_node_type_cmp_map_value()
{
  namespace file_ns = blender::nodes::node_composite_map_value_cc;

  static blender::bke::bNodeType ntype;

  cmp_node_type_base(&ntype, "CompositorNodeMapValue", CMP_NODE_MAP_VALUE);
  ntype.ui_name = "Map Value";
  ntype.ui_description = "Scale, offset and clamp values";
  ntype.enum_name_legacy = "MAP_VALUE";
  ntype.nclass = NODE_CLASS_OP_VECTOR;
  ntype.declare = file_ns::cmp_node_map_value_declare;
  ntype.draw_buttons = file_ns::node_composit_buts_map_value;
  ntype.initfunc = file_ns::node_composit_init_map_value;
  blender::bke::node_type_storage(
      &ntype, "TexMapping", node_free_standard_storage, node_copy_standard_storage);
  ntype.gpu_fn = file_ns::node_gpu_material;
  ntype.build_multi_function = file_ns::node_build_multi_function;

  blender::bke::node_register_type(&ntype);
}
