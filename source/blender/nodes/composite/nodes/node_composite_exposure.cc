/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup cmpnodes
 */

#include <cmath>

#include "BLI_math_vector_types.hh"

#include "FN_multi_function_builder.hh"

#include "NOD_multi_function.hh"

#include "GPU_material.hh"

#include "node_composite_util.hh"

/* **************** Exposure ******************** */

namespace blender::nodes::node_composite_exposure_cc {

static void cmp_node_exposure_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>("Image")
      .default_value({1.0f, 1.0f, 1.0f, 1.0f})
      .compositor_domain_priority(0);
  b.add_input<decl::Float>("Exposure").min(-10.0f).max(10.0f).compositor_domain_priority(1);
  b.add_output<decl::Color>("Image");
}

using namespace blender::compositor;

static int node_gpu_material(GPUMaterial *material,
                             bNode *node,
                             bNodeExecData * /*execdata*/,
                             GPUNodeStack *inputs,
                             GPUNodeStack *outputs)
{
  return GPU_stack_link(material, node, "node_composite_exposure", inputs, outputs);
}

static void node_build_multi_function(blender::nodes::NodeMultiFunctionBuilder &builder)
{
  static auto function = mf::build::SI2_SO<float4, float, float4>(
      "Exposure",
      [](const float4 &color, const float exposure) -> float4 {
        return float4(color.xyz() * std::exp2(exposure), color.w);
      },
      mf::build::exec_presets::SomeSpanOrSingle<0>());
  builder.set_matching_fn(function);
}

}  // namespace blender::nodes::node_composite_exposure_cc

void register_node_type_cmp_exposure()
{
  namespace file_ns = blender::nodes::node_composite_exposure_cc;

  static blender::bke::bNodeType ntype;

  cmp_node_type_base(&ntype, "CompositorNodeExposure", CMP_NODE_EXPOSURE);
  ntype.ui_name = "Exposure";
  ntype.ui_description = "Adjust brightness using a camera exposure parameter";
  ntype.enum_name_legacy = "EXPOSURE";
  ntype.nclass = NODE_CLASS_OP_COLOR;
  ntype.declare = file_ns::cmp_node_exposure_declare;
  ntype.gpu_fn = file_ns::node_gpu_material;
  ntype.build_multi_function = file_ns::node_build_multi_function;

  blender::bke::node_register_type(&ntype);
}
