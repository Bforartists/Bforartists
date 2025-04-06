/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "BLI_listbase.h"
#include "BLI_string.h"

#include "BKE_report.hh"

#include "IO_csv.hh"

#include "node_geometry_util.hh"

namespace blender::nodes::node_geo_import_csv {

static void node_declare(NodeDeclarationBuilder &b)
{
  b.add_input<decl::String>("Path")
      .subtype(PROP_FILEPATH)
      .path_filter("*.csv")
      .hide_label()
      .description("Path to a CSV file");
  b.add_input<decl::String>("Delimiter").default_value(",");

  b.add_output<decl::Geometry>("Point Cloud");
}

static void node_geo_exec(GeoNodeExecParams params)
{
#ifdef WITH_IO_CSV
  const std::optional<std::string> path = params.ensure_absolute_path(
      params.extract_input<std::string>("Path"));
  if (!path) {
    params.set_default_remaining_outputs();
    return;
  }
  const std::string delimiter = params.extract_input<std::string>("Delimiter");
  if (delimiter.size() != 1) {
    params.error_message_add(NodeWarningType::Error, TIP_("Delimiter must be a single character"));
    params.set_default_remaining_outputs();
    return;
  }
  if (ELEM(delimiter[0], '\n', '\r', '"', '\\')) {
    params.error_message_add(NodeWarningType::Error,
                             TIP_("Delimiter must not be \\n, \\r, \" or \\"));
    params.set_default_remaining_outputs();
    return;
  }

  blender::io::csv::CSVImportParams import_params{};
  import_params.delimiter = delimiter[0];
  STRNCPY(import_params.filepath, path->c_str());

  ReportList reports;
  BKE_reports_init(&reports, RPT_STORE);
  BLI_SCOPED_DEFER([&]() { BKE_reports_free(&reports); })
  import_params.reports = &reports;

  PointCloud *pointcloud = blender::io::csv::import_csv_as_pointcloud(import_params);

  LISTBASE_FOREACH (Report *, report, &(import_params.reports)->list) {
    NodeWarningType type;
    switch (report->type) {
      case RPT_ERROR:
        type = NodeWarningType::Error;
        break;
      default:
        type = NodeWarningType::Info;
        break;
    }
    params.error_message_add(type, TIP_(report->message));
  }

  params.set_output("Point Cloud", GeometrySet::from_pointcloud(pointcloud));
#else
  params.error_message_add(NodeWarningType::Error,
                           TIP_("Disabled, Blender was compiled without CSV I/O"));
  params.set_default_remaining_outputs();
#endif
}

static void node_register()
{
  static blender::bke::bNodeType ntype;

  geo_node_type_base(&ntype, "GeometryNodeImportCSV");
  ntype.ui_name = "Import CSV";
  ntype.ui_description = "Import geometry from an CSV file";
  ntype.nclass = NODE_CLASS_INPUT;
  ntype.geometry_node_execute = node_geo_exec;
  ntype.declare = node_declare;

  blender::bke::node_register_type(ntype);
}
NOD_REGISTER_NODE(node_register)

}  // namespace blender::nodes::node_geo_import_csv
