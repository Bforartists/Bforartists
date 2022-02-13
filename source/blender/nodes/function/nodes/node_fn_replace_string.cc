/* SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_string_utf8.h"

#include "node_function_util.hh"

namespace blender::nodes::node_fn_replace_string_cc {

static void fn_node_replace_string_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::String>(N_("String"));
  b.add_input<decl::String>(N_("Find")).description(N_("The string to find in the input string"));
  b.add_input<decl::String>(N_("Replace"))
      .description(N_("The string to replace each match with"));
  b.add_output<decl::String>(N_("String"));
}

static std::string replace_all(std::string str, const std::string &from, const std::string &to)
{
  if (from.length() <= 0) {
    return str;
  }
  const size_t step = to.length() > 0 ? to.length() : 1;

  size_t offset = 0;
  while ((offset = str.find(from, offset)) != std::string::npos) {
    str.replace(offset, from.length(), to);
    offset += step;
  }
  return str;
}

static void fn_node_replace_string_build_multi_function(NodeMultiFunctionBuilder &builder)
{
  static fn::CustomMF_SI_SI_SI_SO<std::string, std::string, std::string, std::string> substring_fn{
      "Replace", [](const std::string &str, const std::string &find, const std::string &replace) {
        return replace_all(str, find, replace);
      }};
  builder.set_matching_fn(&substring_fn);
}

}  // namespace blender::nodes::node_fn_replace_string_cc

void register_node_type_fn_replace_string()
{
  namespace file_ns = blender::nodes::node_fn_replace_string_cc;

  static bNodeType ntype;

  fn_node_type_base(&ntype, FN_NODE_REPLACE_STRING, "Replace String", NODE_CLASS_CONVERTER);
  ntype.declare = file_ns::fn_node_replace_string_declare;
  ntype.build_multi_function = file_ns::fn_node_replace_string_build_multi_function;
  nodeRegisterType(&ntype);
}
