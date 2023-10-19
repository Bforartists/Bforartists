/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "DEG_depsgraph_query.hh"
#ifdef WITH_OPENVDB
#  include <openvdb/tools/LevelSetFilter.h>
#endif

#include "node_geometry_util.hh"

#include "BKE_volume.h"
#include "BKE_volume_openvdb.hh"

#include "DNA_node_types.h"

#include "NOD_socket_search_link.hh"

#include "UI_interface.hh"
#include "UI_resources.hh"

namespace blender::nodes::node_geo_offset_sdf_volume_cc {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::Geometry>("Volume")
      .supported_type(GeometryComponent::Type::Volume)
      .translation_context(BLT_I18NCONTEXT_ID_ID);
  b.add_input<decl::Float>("Distance").default_value(0.1f).subtype(PROP_DISTANCE);
  b.add_output<decl::Geometry>("Volume").translation_context(BLT_I18NCONTEXT_ID_ID);
}

static void search_link_ops(GatherLinkSearchOpParams &params)
{
  if (U.experimental.use_new_volume_nodes) {
    nodes::search_link_ops_for_basic_node(params);
  }
}

#ifdef WITH_OPENVDB
static void sdf_volume_offset(Volume &volume, const GeoNodeExecParams &params)
{
  VolumeGrid *volume_grid = BKE_volume_grid_find_for_write(&volume, "distance");
  if (volume_grid == nullptr) {
    return;
  }
  openvdb::GridBase::Ptr base_grid = BKE_volume_grid_openvdb_for_write(
      &volume, volume_grid, false);

  if (!base_grid->isType<openvdb::FloatGrid>()) {
    return;
  }
  openvdb::FloatGrid::Ptr levelset_grid = openvdb::gridPtrCast<openvdb::FloatGrid>(base_grid);
  openvdb::tools::LevelSetFilter<openvdb::FloatGrid> filter(*levelset_grid);

  filter.offset(-params.get_input<float>("Distance"));
}
#endif

static void node_geo_exec(GeoNodeExecParams params)
{
#ifdef WITH_OPENVDB
  GeometrySet geometry_set = params.extract_input<GeometrySet>("Volume");

  geometry_set.modify_geometry_sets([&](GeometrySet &geometry_set) {
    if (!geometry_set.has_volume()) {
      return;
    }
    VolumeComponent &component = geometry_set.get_component_for_write<VolumeComponent>();
    Volume *volume = component.get_for_write();
    BKE_volume_load(volume, DEG_get_bmain(params.depsgraph()));
    sdf_volume_offset(*volume, params);
  });
  params.set_output("Volume", std::move(geometry_set));
#else
  params.set_default_remaining_outputs();
  params.error_message_add(NodeWarningType::Error,
                           TIP_("Disabled, Blender was compiled without OpenVDB"));
#endif
}

static void node_register()
{
  static bNodeType ntype;

  geo_node_type_base(&ntype, GEO_NODE_OFFSET_SDF_VOLUME, "Offset SDF Volume", NODE_CLASS_GEOMETRY);
  ntype.declare = node_declare;
  ntype.geometry_node_execute = node_geo_exec;
  ntype.gather_link_search_ops = search_link_ops;
  nodeRegisterType(&ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_offset_sdf_volume_cc
