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

#include "IMB_colormanagement.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

#include "GPU_material.hh"

#include "node_composite_util.hh"

/* ******************* Luma Matte Node ********************************* */

namespace blender::nodes::node_composite_luma_matte_cc {

NODE_STORAGE_FUNCS(NodeChroma)

static void cmp_node_luma_matte_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Color>("Image").default_value({1.0f, 1.0f, 1.0f, 1.0f});
  b.add_input<decl::Float>("Minimum")
      .default_value(0.0f)
      .subtype(PROP_FACTOR)
      .min(0.0f)
      .max(1.0f)
      .description("Pixels whose luminance values lower than this minimum are keyed");
  b.add_input<decl::Float>("Maximum")
      .default_value(1.0f)
      .subtype(PROP_FACTOR)
      .min(0.0f)
      .max(1.0f)
      .description("Pixels whose luminance values higher than this maximum are not keyed");

  b.add_output<decl::Color>("Image");
  b.add_output<decl::Float>("Matte");
}

static void node_composit_init_luma_matte(bNodeTree * /*ntree*/, bNode *node)
{
  NodeChroma *c = MEM_callocN<NodeChroma>(__func__);
  node->storage = c;
  c->t1 = 1.0f;
  c->t2 = 0.0f;
}

using namespace blender::compositor;

static int node_gpu_material(GPUMaterial *material,
                             bNode *node,
                             bNodeExecData * /*execdata*/,
                             GPUNodeStack *inputs,
                             GPUNodeStack *outputs)
{
  float luminance_coefficients[3];
  IMB_colormanagement_get_luminance_coefficients(luminance_coefficients);

  return GPU_stack_link(material,
                        node,
                        "node_composite_luminance_matte",
                        inputs,
                        outputs,
                        GPU_constant(luminance_coefficients));
}

static void node_build_multi_function(blender::nodes::NodeMultiFunctionBuilder &builder)
{
  float3 luminance_coefficients;
  IMB_colormanagement_get_luminance_coefficients(luminance_coefficients);

  builder.construct_and_set_matching_fn_cb([=]() {
    return mf::build::SI3_SO2<float4, float, float, float4, float>(
        "Luminance Key",
        [=](const float4 &color,
            const float &minimum,
            const float &maximum,
            float4 &result,
            float &matte) -> void {
          float luminance = math::dot(color.xyz(), luminance_coefficients);
          float alpha = math::clamp((luminance - minimum) / (maximum - minimum), 0.0f, 1.0f);
          matte = math::min(alpha, color.w);
          result = color * matte;
        },
        mf::build::exec_presets::SomeSpanOrSingle<0>());
  });
}

}  // namespace blender::nodes::node_composite_luma_matte_cc

void register_node_type_cmp_luma_matte()
{
  namespace file_ns = blender::nodes::node_composite_luma_matte_cc;

  static blender::bke::bNodeType ntype;

  cmp_node_type_base(&ntype, "CompositorNodeLumaMatte", CMP_NODE_LUMA_MATTE);
  ntype.ui_name = "Luminance Key";
  ntype.ui_description = "Create a matte based on luminance (brightness) difference";
  ntype.enum_name_legacy = "LUMA_MATTE";
  ntype.nclass = NODE_CLASS_MATTE;
  ntype.declare = file_ns::cmp_node_luma_matte_declare;
  ntype.flag |= NODE_PREVIEW;
  ntype.initfunc = file_ns::node_composit_init_luma_matte;
  blender::bke::node_type_storage(
      ntype, "NodeChroma", node_free_standard_storage, node_copy_standard_storage);
  ntype.gpu_fn = file_ns::node_gpu_material;
  ntype.build_multi_function = file_ns::node_build_multi_function;

  blender::bke::node_register_type(ntype);
}
