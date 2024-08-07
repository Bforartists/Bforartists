/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup obj
 */

#include "BKE_lib_id.hh"
#include "BKE_object.hh"

#include "BLI_listbase.h"
#include "BLI_math_vector.h"

#include "DNA_curve_types.h"

#include "IO_wavefront_obj.hh"
#include "importer_mesh_utils.hh"
#include "obj_import_nurbs.hh"
#include "obj_import_objects.hh"

namespace blender::io::obj {

Curve *blender::io::obj::CurveFromGeometry::create_curve()
{
  BLI_assert(!curve_geometry_.nurbs_element_.curv_indices.is_empty());

  Curve *curve = static_cast<Curve *>(BKE_id_new_nomain(ID_CU_LEGACY, nullptr));

  BKE_curve_init(curve, OB_CURVES_LEGACY);

  curve->flag = CU_3D;
  curve->resolu = curve->resolv = 12;
  /* Only one NURBS spline will be created in the curve object. */
  curve->actnu = 0;

  Nurb *nurb = static_cast<Nurb *>(MEM_callocN(sizeof(Nurb), __func__));
  BLI_addtail(BKE_curve_nurbs_get(curve), nurb);
  this->create_nurbs(curve);

  return curve;
}

Object *CurveFromGeometry::create_curve_object(Main *bmain, const OBJImportParams &import_params)
{
  std::string ob_name = get_geometry_name(curve_geometry_.geometry_name_,
                                          import_params.collection_separator);
  if (ob_name.empty() && !curve_geometry_.nurbs_element_.group_.empty()) {
    ob_name = curve_geometry_.nurbs_element_.group_;
  }
  if (ob_name.empty()) {
    ob_name = "Untitled";
  }
  BLI_assert(!curve_geometry_.nurbs_element_.curv_indices.is_empty());

  Curve *curve = BKE_curve_add(bmain, ob_name.c_str(), OB_CURVES_LEGACY);
  Object *obj = BKE_object_add_only_object(bmain, OB_CURVES_LEGACY, ob_name.c_str());

  curve->flag = CU_3D;
  curve->resolu = curve->resolv = 12;
  /* Only one NURBS spline will be created in the curve object. */
  curve->actnu = 0;

  Nurb *nurb = static_cast<Nurb *>(MEM_callocN(sizeof(Nurb), __func__));
  BLI_addtail(BKE_curve_nurbs_get(curve), nurb);
  this->create_nurbs(curve);

  obj->data = curve;
  transform_object(obj, import_params);

  return obj;
}

void CurveFromGeometry::create_nurbs(Curve *curve)
{
  const NurbsElement &nurbs_geometry = curve_geometry_.nurbs_element_;
  Nurb *nurb = static_cast<Nurb *>(curve->nurb.first);

  nurb->type = CU_NURBS;
  nurb->flag = CU_3D;
  nurb->next = nurb->prev = nullptr;
  /* BKE_nurb_points_add later on will update pntsu. If this were set to total curve points,
   * we get double the total points in viewport. */
  nurb->pntsu = 0;
  /* Total points = pntsu * pntsv. */
  nurb->pntsv = 1;
  nurb->orderu = nurb->orderv = (nurbs_geometry.degree + 1 > SHRT_MAX) ? 4 :
                                                                         nurbs_geometry.degree + 1;
  nurb->resolu = nurb->resolv = curve->resolu;

  const int64_t tot_vert{nurbs_geometry.curv_indices.size()};

  BKE_nurb_points_add(nurb, tot_vert);
  for (int i = 0; i < tot_vert; i++) {
    BPoint &bpoint = nurb->bp[i];
    copy_v3_v3(bpoint.vec, global_vertices_.vertices[nurbs_geometry.curv_indices[i]]);
    bpoint.vec[3] = 1.0f;
    bpoint.weight = 1.0f;
  }

  BKE_nurb_knot_calc_u(nurb);

  /* Figure out whether curve should have U endpoint flag set:
   * the parameters should have at least (degree+1) values on each end,
   * and their values should match curve range. */
  bool do_endpoints = false;
  int deg1 = nurbs_geometry.degree + 1;
  if (nurbs_geometry.parm.size() >= deg1 * 2) {
    do_endpoints = true;
    const float2 range = nurbs_geometry.range;
    for (int i = 0; i < deg1; ++i) {
      if (abs(nurbs_geometry.parm[i] - range.x) > 0.0001f) {
        do_endpoints = false;
        break;
      }
      if (abs(nurbs_geometry.parm[nurbs_geometry.parm.size() - 1 - i] - range.y) > 0.0001f) {
        do_endpoints = false;
        break;
      }
    }
  }
  if (do_endpoints) {
    nurb->flagu = CU_NURB_ENDPOINT;
  }
}

}  // namespace blender::io::obj
