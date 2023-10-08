/* SPDX-FileCopyrightText: 2020 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edgizmolib
 *
 * \name Snap Gizmo
 *
 * 3D Gizmo
 *
 * \brief Snap gizmo which exposes the location, normal and index in the props.
 */

#include "MEM_guardedalloc.h"

#include "BLI_listbase.h"
#include "BLI_math_color.h"
#include "BLI_math_vector.h"

#include "BKE_context.h"
#include "BKE_global.h"
#include "BKE_main.h"

#include "ED_gizmo_library.hh"
#include "ED_screen.hh"
#include "ED_transform_snap_object_context.hh"
#include "ED_view3d.hh"

#include "UI_resources.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_prototypes.h"

#include "WM_api.hh"

/* own includes */
#include "../gizmo_library_intern.h"

struct SnapGizmo3D {
  wmGizmo gizmo;
  V3DSnapCursorState *snap_state;
};

/* -------------------------------------------------------------------- */
/** \name ED_gizmo_library specific API
 * \{ */

SnapObjectContext *ED_gizmotypes_snap_3d_context_ensure(Scene *scene, wmGizmo * /*gz*/)
{
  return ED_view3d_cursor_snap_context_ensure(scene);
}

void ED_gizmotypes_snap_3d_flag_set(wmGizmo *gz, int flag)
{
  V3DSnapCursorState *snap_state = ((SnapGizmo3D *)gz)->snap_state;
  snap_state->flag |= eV3DSnapCursor(flag);
}

bool ED_gizmotypes_snap_3d_is_enabled(const wmGizmo * /*gz*/)
{
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();
  return snap_data->is_enabled;
}

void ED_gizmotypes_snap_3d_data_get(const bContext *C,
                                    wmGizmo *gz,
                                    float r_loc[3],
                                    float r_nor[3],
                                    int r_elem_index[3],
                                    eSnapMode *r_snap_elem)
{
  if (C) {
    /* Snap values are updated too late at the cursor. Be sure to update ahead of time. */
    wmWindowManager *wm = CTX_wm_manager(C);
    const wmEvent *event = wm->winactive ? wm->winactive->eventstate : nullptr;
    if (event) {
      ARegion *region = CTX_wm_region(C);
      int x = event->xy[0] - region->winrct.xmin;
      int y = event->xy[1] - region->winrct.ymin;

      SnapGizmo3D *snap_gizmo = (SnapGizmo3D *)gz;
      ED_view3d_cursor_snap_data_update(snap_gizmo->snap_state, C, x, y);
    }
  }

  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();

  if (r_loc) {
    copy_v3_v3(r_loc, snap_data->loc);
  }
  if (r_nor) {
    copy_v3_v3(r_nor, snap_data->nor);
  }
  if (r_elem_index) {
    copy_v3_v3_int(r_elem_index, snap_data->elem_index);
  }
  if (r_snap_elem) {
    *r_snap_elem = snap_data->type_target;
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name RNA callbacks
 * \{ */

static SnapGizmo3D *gizmo_snap_rna_find_operator(PointerRNA *ptr)
{
  return (SnapGizmo3D *)gizmo_find_from_properties(
      static_cast<const IDProperty *>(ptr->data), SPACE_VIEW3D, RGN_TYPE_WINDOW);
}

static V3DSnapCursorState *gizmo_snap_state_from_rna_get(PointerRNA *ptr)
{
  SnapGizmo3D *snap_gizmo = gizmo_snap_rna_find_operator(ptr);
  if (snap_gizmo) {
    return snap_gizmo->snap_state;
  }

  return ED_view3d_cursor_snap_state_active_get();
}

static void gizmo_snap_rna_prevpoint_get_fn(PointerRNA *ptr, PropertyRNA * /*prop*/, float *values)
{
  V3DSnapCursorState *snap_state = gizmo_snap_state_from_rna_get(ptr);
  if (snap_state->prevpoint) {
    copy_v3_v3(values, snap_state->prevpoint);
  }
}

static void gizmo_snap_rna_prevpoint_set_fn(PointerRNA *ptr,
                                            PropertyRNA * /*prop*/,
                                            const float *values)
{
  V3DSnapCursorState *snap_state = gizmo_snap_state_from_rna_get(ptr);
  ED_view3d_cursor_snap_state_prevpoint_set(snap_state, values);
}

static void gizmo_snap_rna_location_get_fn(PointerRNA * /*ptr*/,
                                           PropertyRNA * /*prop*/,
                                           float *values)
{
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();
  copy_v3_v3(values, snap_data->loc);
}

static void gizmo_snap_rna_location_set_fn(PointerRNA * /*ptr*/,
                                           PropertyRNA * /*prop*/,
                                           const float *values)
{
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();
  copy_v3_v3(snap_data->loc, values);
}

static void gizmo_snap_rna_normal_get_fn(PointerRNA * /*ptr*/,
                                         PropertyRNA * /*prop*/,
                                         float *values)
{
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();
  copy_v3_v3(values, snap_data->nor);
}

static void gizmo_snap_rna_snap_elem_index_get_fn(PointerRNA * /*ptr*/,
                                                  PropertyRNA * /*prop*/,
                                                  int *values)
{
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();
  copy_v3_v3_int(values, snap_data->elem_index);
}

static int gizmo_snap_rna_snap_srouce_type_get_fn(PointerRNA * /*ptr*/, PropertyRNA * /*prop*/)
{
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();
  return (int)snap_data->type_source;
}

static void gizmo_snap_rna_snap_srouce_type_set_fn(PointerRNA * /*ptr*/,
                                                   PropertyRNA * /*prop*/,
                                                   const int value)
{
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();
  snap_data->type_source = (eSnapMode)value;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Snap Cursor Utils
 * \{ */

static void snap_cursor_free(SnapGizmo3D *snap_gizmo)
{
  if (snap_gizmo->snap_state) {
    ED_view3d_cursor_snap_state_free(snap_gizmo->snap_state);
    snap_gizmo->snap_state = nullptr;
  }
}

/* XXX: Delayed snap cursor removal. */
static bool snap_cursor_poll(ARegion *region, void *data)
{
  SnapGizmo3D *snap_gizmo = (SnapGizmo3D *)data;
  if (!(snap_gizmo->gizmo.state & WM_GIZMO_STATE_HIGHLIGHT) &&
      !(snap_gizmo->gizmo.flag & WM_GIZMO_DRAW_VALUE))
  {
    return false;
  }

  if (snap_gizmo->gizmo.flag & WM_GIZMO_HIDDEN) {
    snap_cursor_free(snap_gizmo);
    return false;
  }

  if (!WM_gizmomap_group_find_ptr(region->gizmo_map, snap_gizmo->gizmo.parent_gzgroup->type)) {
    /* Wrong viewport. */
    snap_cursor_free(snap_gizmo);
    return false;
  }
  return true;
}

static void snap_cursor_init(SnapGizmo3D *snap_gizmo)
{
  snap_gizmo->snap_state = ED_view3d_cursor_snap_state_create();
  snap_gizmo->snap_state->draw_point = true;
  snap_gizmo->snap_state->draw_plane = false;

  rgba_float_to_uchar(snap_gizmo->snap_state->target_color, snap_gizmo->gizmo.color);

  snap_gizmo->snap_state->poll = snap_cursor_poll;
  snap_gizmo->snap_state->poll_data = snap_gizmo;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name GIZMO_GT_snap_3d
 * \{ */

static void snap_gizmo_setup(wmGizmo *gz)
{
  gz->flag |= WM_GIZMO_NO_TOOLTIP;
  snap_cursor_init((SnapGizmo3D *)gz);
}

static void snap_gizmo_draw(const bContext * /*C*/, wmGizmo *gz)
{
  SnapGizmo3D *snap_gizmo = (SnapGizmo3D *)gz;
  if (snap_gizmo->snap_state == nullptr) {
    snap_cursor_init(snap_gizmo);
  }

  /* All drawing is handled at the paint cursor.
   * Therefore, make sure that the #V3DSnapCursorState is the one of the gizmo being drawn. */
  ED_view3d_cursor_snap_state_active_set(snap_gizmo->snap_state);
}

static int snap_gizmo_test_select(bContext *C, wmGizmo *gz, const int mval[2])
{
  SnapGizmo3D *snap_gizmo = (SnapGizmo3D *)gz;

  /* Snap values are updated too late at the cursor. Be sure to update ahead of time. */
  int x, y;
  {
    wmWindowManager *wm = CTX_wm_manager(C);
    const wmEvent *event = wm->winactive ? wm->winactive->eventstate : nullptr;
    if (event) {
      ARegion *region = CTX_wm_region(C);
      x = event->xy[0] - region->winrct.xmin;
      y = event->xy[1] - region->winrct.ymin;
    }
    else {
      x = mval[0];
      y = mval[1];
    }
  }
  ED_view3d_cursor_snap_data_update(snap_gizmo->snap_state, C, x, y);
  V3DSnapCursorData *snap_data = ED_view3d_cursor_snap_data_get();

  if (snap_data->type_target != SCE_SNAP_TO_NONE) {
    return 0;
  }
  return -1;
}

static int snap_gizmo_modal(bContext * /*C*/,
                            wmGizmo * /*gz*/,
                            const wmEvent * /*event*/,
                            eWM_GizmoFlagTweak /*tweak_flag*/)
{
  return OPERATOR_RUNNING_MODAL;
}

static int snap_gizmo_invoke(bContext * /*C*/, wmGizmo * /*gz*/, const wmEvent * /*event*/)
{
  return OPERATOR_RUNNING_MODAL;
}

static void snap_gizmo_free(wmGizmo *gz)
{
  snap_cursor_free((SnapGizmo3D *)gz);
}

static void GIZMO_GT_snap_3d(wmGizmoType *gzt)
{
  /* identifiers */
  gzt->idname = "GIZMO_GT_snap_3d";

  /* api callbacks */
  gzt->setup = snap_gizmo_setup;
  gzt->draw = snap_gizmo_draw;
  gzt->test_select = snap_gizmo_test_select;
  gzt->modal = snap_gizmo_modal;
  gzt->invoke = snap_gizmo_invoke;
  gzt->free = snap_gizmo_free;

  gzt->struct_size = sizeof(SnapGizmo3D);

  const EnumPropertyItem *rna_enum_snap_element_items;
  {
    /* Get Snap Element Items enum. */
    bool free;
    PointerRNA toolsettings_ptr = RNA_pointer_create(nullptr, &RNA_ToolSettings, nullptr);
    PropertyRNA *prop = RNA_struct_find_property(&toolsettings_ptr, "snap_elements");
    RNA_property_enum_items(
        nullptr, &toolsettings_ptr, prop, &rna_enum_snap_element_items, nullptr, &free);

    BLI_assert(free == false);
  }

  /* Setup. */
  PropertyRNA *prop;
  prop = RNA_def_float_array(gzt->srna,
                             "prev_point",
                             3,
                             nullptr,
                             FLT_MIN,
                             FLT_MAX,
                             "Previous Point",
                             "Point that defines the location of the perpendicular snap",
                             FLT_MIN,
                             FLT_MAX);
  RNA_def_property_float_array_funcs_runtime(
      prop, gizmo_snap_rna_prevpoint_get_fn, gizmo_snap_rna_prevpoint_set_fn, nullptr);

  /* Returns. */
  prop = RNA_def_float_translation(gzt->srna,
                                   "location",
                                   3,
                                   nullptr,
                                   FLT_MIN,
                                   FLT_MAX,
                                   "Location",
                                   "Snap Point Location",
                                   FLT_MIN,
                                   FLT_MAX);
  RNA_def_property_float_array_funcs_runtime(
      prop, gizmo_snap_rna_location_get_fn, gizmo_snap_rna_location_set_fn, nullptr);

  prop = RNA_def_float_vector_xyz(gzt->srna,
                                  "normal",
                                  3,
                                  nullptr,
                                  FLT_MIN,
                                  FLT_MAX,
                                  "Normal",
                                  "Snap Point Normal",
                                  FLT_MIN,
                                  FLT_MAX);
  RNA_def_property_float_array_funcs_runtime(prop, gizmo_snap_rna_normal_get_fn, nullptr, nullptr);

  prop = RNA_def_int_vector(gzt->srna,
                            "snap_elem_index",
                            3,
                            nullptr,
                            INT_MIN,
                            INT_MAX,
                            "Snap Element",
                            "Array index of face, edge and vert snapped",
                            INT_MIN,
                            INT_MAX);
  RNA_def_property_int_array_funcs_runtime(
      prop, gizmo_snap_rna_snap_elem_index_get_fn, nullptr, nullptr);

  prop = RNA_def_enum(gzt->srna,
                      "snap_source_type",
                      rna_enum_snap_element_items,
                      SCE_SNAP_TO_NONE,
                      "Snap Source Type",
                      "Snap Source type (influences drawing)");
  RNA_def_property_enum_funcs_runtime(prop,
                                      gizmo_snap_rna_snap_srouce_type_get_fn,
                                      gizmo_snap_rna_snap_srouce_type_set_fn,
                                      nullptr);
}

void ED_gizmotypes_snap_3d()
{
  WM_gizmotype_append(GIZMO_GT_snap_3d);
}

/** \} */
