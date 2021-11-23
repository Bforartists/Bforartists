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
 */

#include "UI_interface.h"
#include "UI_resources.h"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_viewer_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>(N_("Geometry"));
  b.add_input<decl::Float>(N_("Value")).supports_field().hide_value();
  b.add_input<decl::Vector>(N_("Value"), "Value_001").supports_field().hide_value();
  b.add_input<decl::Color>(N_("Value"), "Value_002").supports_field().hide_value();
  b.add_input<decl::Int>(N_("Value"), "Value_003").supports_field().hide_value();
  b.add_input<decl::Bool>(N_("Value"), "Value_004").supports_field().hide_value();
}

static void node_init(bNodeTree *UNUSED(tree), bNode *node)
{
  NodeGeometryViewer *data = (NodeGeometryViewer *)MEM_callocN(sizeof(NodeGeometryViewer),
                                                               __func__);
  data->data_type = CD_PROP_FLOAT;

  node->storage = data;
}

static void node_layout(uiLayout *layout, bContext *UNUSED(C), PointerRNA *ptr)
{
  uiItemR(layout, ptr, "data_type", 0, "", ICON_NONE);
}

static eNodeSocketDatatype custom_data_type_to_socket_type(const CustomDataType type)
{
  switch (type) {
    case CD_PROP_FLOAT:
      return SOCK_FLOAT;
    case CD_PROP_INT32:
      return SOCK_INT;
    case CD_PROP_FLOAT3:
      return SOCK_VECTOR;
    case CD_PROP_BOOL:
      return SOCK_BOOLEAN;
    case CD_PROP_COLOR:
      return SOCK_RGBA;
    default:
      BLI_assert_unreachable();
      return SOCK_FLOAT;
  }
}

static void node_update(bNodeTree *ntree, bNode *node)
{
  const NodeGeometryViewer &storage = *(const NodeGeometryViewer *)node->storage;
  const CustomDataType data_type = static_cast<CustomDataType>(storage.data_type);
  const eNodeSocketDatatype socket_type = custom_data_type_to_socket_type(data_type);

  LISTBASE_FOREACH (bNodeSocket *, socket, &node->inputs) {
    if (socket->type == SOCK_GEOMETRY) {
      continue;
    }
    nodeSetSocketAvailability(ntree, socket, socket->type == socket_type);
  }
}

}  // namespace blender::nodes::node_geo_viewer_cc

void register_node_type_geo_viewer()
{
  namespace file_ns = blender::nodes::node_geo_viewer_cc;

  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_VIEWER, "Viewer", NODE_CLASS_OUTPUT, 0);
  node_type_storage(
      &ntype, "NodeGeometryViewer", node_free_standard_storage, node_copy_standard_storage);
  node_type_update(&ntype, file_ns::node_update);
  node_type_init(&ntype, file_ns::node_init);
  ntype.declare = file_ns::node_declare;
  ntype.draw_buttons_ex = file_ns::node_layout;
  nodeRegisterType(&ntype);
}
