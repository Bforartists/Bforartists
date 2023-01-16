/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_string_utf8.h"

#include "node_function_util.hh"

namespace blender::nodes::node_fn_slice_string_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::String>(N_("String"));
  b.add_input<decl::Int>(N_("Position"));
  b.add_input<decl::Int>(N_("Length")).min(0).default_value(10);
  b.add_output<decl::String>(N_("String"));
}

static void node_build_multi_function(NodeMultiFunctionBuilder &builder)
{
  static auto slice_fn = mf::build::SI3_SO<std::string, int, int, std::string>(
      "Slice", [](const std::string &str, int a, int b) {
        const int len = BLI_strlen_utf8(str.c_str());
        const int start = BLI_str_utf8_offset_from_index(str.c_str(), std::clamp(a, 0, len));
        const int end = BLI_str_utf8_offset_from_index(str.c_str(), std::clamp(a + b, 0, len));
        return str.substr(start, std::max<int>(end - start, 0));
      });
  builder.set_matching_fn(&slice_fn);
}

}  // namespace blender::nodes::node_fn_slice_string_cc

void register_node_type_fn_slice_string()
{
  namespace file_ns = blender::nodes::node_fn_slice_string_cc;

  static bNodeType ntype;

  fn_node_type_base(&ntype, FN_NODE_SLICE_STRING, "Slice String", NODE_CLASS_CONVERTER);
  ntype.declare = file_ns::node_declare;
  ntype.build_multi_function = file_ns::node_build_multi_function;
  nodeRegisterType(&ntype);
}
