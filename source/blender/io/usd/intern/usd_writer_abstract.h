/* SPDX-FileCopyrightText: 2019 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

#include "IO_abstract_hierarchy_iterator.h"
#include "usd_exporter_context.h"

#include <pxr/usd/sdf/path.h>
#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usdGeom/boundable.h>
#include <pxr/usd/usdShade/material.h>
#include <pxr/usd/usdUtils/sparseValueWriter.h>

#include <vector>

#include "DEG_depsgraph_query.hh"

#include "WM_types.hh"

#include "DNA_material_types.h"
#include "DNA_windowmanager_types.h"

struct Material;

namespace blender::io::usd {

using blender::io::AbstractHierarchyWriter;
using blender::io::HierarchyContext;

class USDAbstractWriter : public AbstractHierarchyWriter {
 protected:
  const USDExporterContext usd_export_context_;
  pxr::UsdUtilsSparseValueWriter usd_value_writer_;

  bool frame_has_been_written_;
  bool is_animated_;

 public:
  USDAbstractWriter(const USDExporterContext &usd_export_context);

  virtual void write(HierarchyContext &context) override;

  /**
   * Returns true if the data to be written is actually supported. This would, for example, allow a
   * hypothetical camera writer accept a perspective camera but reject an orthogonal one.
   *
   * Returning false from a transform writer will prevent the object and all its descendants from
   * being exported. Returning false from a data writer (object data, hair, or particles) will
   * only prevent that data from being written (and thus cause the object to be exported as an
   * Empty).
   */
  virtual bool is_supported(const HierarchyContext *context) const;

  const pxr::SdfPath &usd_path() const;

  /** Get the wmJobWorkerStatus-provided `reports` list pointer, to use with the BKE_report API. */
  ReportList *reports() const
  {
    return usd_export_context_.export_params.worker_status->reports;
  }

 protected:
  virtual void do_write(HierarchyContext &context) = 0;
  std::string get_export_file_path() const;
  pxr::UsdTimeCode get_export_time_code() const;

  /* Returns the parent path of exported materials. */
  pxr::SdfPath get_material_library_path() const;
  pxr::UsdShadeMaterial ensure_usd_material(const HierarchyContext &context, Material *material);

  void write_visibility(const HierarchyContext &context,
                        const pxr::UsdTimeCode timecode,
                        pxr::UsdGeomImageable &usd_geometry);

  /**
   * Turn `prim` into an instance referencing `context.original_export_path`.
   * Return true when the instancing was successful, false otherwise.
   *
   * Reference the original data instead of writing a copy.
   */
  virtual bool mark_as_instance(const HierarchyContext &context, const pxr::UsdPrim &prim);

  /**
   * Compute the bounds for a boundable prim, and author the result as the `extent` attribute.
   *
   * Although this method works for any boundable prim, it is preferred to use Blender's own
   * cached bounds when possible.
   *
   * This method does not author the `extentsHint` attribute, which is also important to provide.
   * Whereas the `extent` attribute can only be authored on prims inheriting from
   * `UsdGeomBoundable`, an `extentsHint` can be provided on any prim, including scopes.  This
   * `extentsHint` should be authored on every prim in a hierarchy being exported.
   *
   * Note that this hint is only useful when importing or inspecting layers, and should not be
   * taken into account when computing extents during export.
   *
   * TODO: also provide method for authoring extentsHint on every prim in a hierarchy.
   */
  virtual void author_extent(const pxr::UsdTimeCode timecode, pxr::UsdGeomBoundable &prim);
};

}  // namespace blender::io::usd
