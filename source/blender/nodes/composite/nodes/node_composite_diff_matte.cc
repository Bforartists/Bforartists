/* SPDX-FileCopyrightText: 2006 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup cmpnodes
 */

#include "BLI_math_base.hh"
#include "BLI_math_vector.hh"
#include "BLI_math_vector_types.hh"

#include "FN_multi_function_builder.hh"

#include "NOD_multi_function.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "GPU_material.hh"

#include "node_composite_util.hh"

/* ******************* channel Difference Matte ********************************* */

namespace blender::nodes::node_composite_diff_matte_cc {

NODE_STORAGE_FUNCS(NodeChroma)

static void cmp_node_diff_matte_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>("Image 1").default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Color>("Image 2").default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>("Tolerance")
      .default_value(0.1f)
      .subtype(PROP_FACTOR)
      .min(0.0f)
      .max(1.0f)
      .description(
          "If the average color difference between the two images is less than this threshold, "
          "it is keyed");
  b.add_input<decl::Float>("Falloff")
      .default_value(0.1f)
      .subtype(PROP_FACTOR)
      .min(0.0f)
      .max(1.0f)
      .description(
          "If the average color difference between the two images is less than this threshold, "
          "it is partially keyed, otherwise, it is not keyed");

  b.add_output<decl::Color>("Image");
  b.add_output<decl::Float>("Matte");
}

static void node_composit_init_diff_matte(bNodeTree * /*ntree*/, bNode *node)
{
  NodeChroma *c = MEM_callocN<NodeChroma>(__func__);
  node->storage = c;
  c->t1 = 0.1f;
  c->t2 = 0.1f;
}

using namespace blender::compositor;

static int node_gpu_material(GPUMaterial *material,
                             bNode *node,
                             bNodeExecData * /*execdata*/,
                             GPUNodeStack *inputs,
                             GPUNodeStack *outputs)
{
  return GPU_stack_link(material, node, "node_composite_difference_matte", inputs, outputs);
}

static void node_build_multi_function(blender::nodes::NodeMultiFunctionBuilder &builder)
{
  builder.construct_and_set_matching_fn_cb([=]() {
    return mf::build::SI4_SO2<float4, float4, float, float, float4, float>(
        "Difference Key",
        [=](const float4 &color,
            const float4 &key,
            const float &tolerance,
            const float &falloff,
            float4 &result,
            float &matte) -> void {
          float difference = math::dot(math::abs(color - key).xyz(), float3(1.0f)) / 3.0f;

          bool is_opaque = difference > tolerance + falloff;
          float alpha = is_opaque ?
                            color.w :
                            math::safe_divide(math::max(0.0f, difference - tolerance), falloff);

          matte = math::min(alpha, color.w);
          result = color * matte;
        },
        mf::build::exec_presets::SomeSpanOrSingle<0, 1>());
  });
}

}  // namespace blender::nodes::node_composite_diff_matte_cc

void register_node_type_cmp_diff_matte()
{
  namespace file_ns = blender::nodes::node_composite_diff_matte_cc;

  static blender::bke::bNodeType ntype;

  cmp_node_type_base(&ntype, "CompositorNodeDiffMatte", CMP_NODE_DIFF_MATTE);
  ntype.ui_name = "Difference Key";
  ntype.ui_description =
      "Produce a matte that isolates foreground content by comparing it with a reference "
      "background image";
  ntype.enum_name_legacy = "DIFF_MATTE";
  ntype.nclass = NODE_CLASS_MATTE;
  ntype.declare = file_ns::cmp_node_diff_matte_declare;
  ntype.flag |= NODE_PREVIEW;
  ntype.initfunc = file_ns::node_composit_init_diff_matte;
  blender::bke::node_type_storage(
      ntype, "NodeChroma", node_free_standard_storage, node_copy_standard_storage);
  ntype.gpu_fn = file_ns::node_gpu_material;
  ntype.build_multi_function = file_ns::node_build_multi_function;

  blender::bke::node_register_type(ntype);
}
