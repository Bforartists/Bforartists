/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "node_function_util.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

namespace blender::nodes::node_fn_input_string_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.is_function_node();
  b.add_output<decl::String>("String");
}

static void node_layout(uiLayout *layout, bContext * /*C*/, PointerRNA *ptr)
{
  uiItemR(layout, ptr, "string", UI_ITEM_NONE, "", ICON_NONE);
}

static void node_build_multi_function(NodeMultiFunctionBuilder &builder)
{
  const bNode &bnode = builder.node();
  NodeInputString *node_storage = static_cast<NodeInputString *>(bnode.storage);
  std::string string = std::string((node_storage->string) ? node_storage->string : "");
  builder.construct_and_set_matching_fn<mf::CustomMF_Constant<std::string>>(std::move(string));
}

static void node_init(bNodeTree * /*tree*/, bNode *node)
{
  node->storage = MEM_callocN(sizeof(NodeInputString), __func__);
}

static void node_storage_free(bNode *node)
{
  NodeInputString *storage = (NodeInputString *)node->storage;
  if (storage == nullptr) {
    return;
  }
  if (storage->string != nullptr) {
    MEM_freeN(storage->string);
  }
  MEM_freeN(storage);
}

static void node_storage_copy(bNodeTree * /*dst_ntree*/, bNode *dest_node, const bNode *src_node)
{
  NodeInputString *source_storage = (NodeInputString *)src_node->storage;
  NodeInputString *destination_storage = (NodeInputString *)MEM_dupallocN(source_storage);

  if (source_storage->string) {
    destination_storage->string = (char *)MEM_dupallocN(source_storage->string);
  }

  dest_node->storage = destination_storage;
}

static void node_register()
{
  static bNodeType ntype;

  fn_node_type_base(&ntype, FN_NODE_INPUT_STRING, "String", NODE_CLASS_INPUT);
  ntype.declare = node_declare;
  ntype.initfunc = node_init;
  node_type_storage(&ntype, "NodeInputString", node_storage_free, node_storage_copy);
  ntype.build_multi_function = node_build_multi_function;
  ntype.draw_buttons = node_layout;
  nodeRegisterType(&ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_fn_input_string_cc
