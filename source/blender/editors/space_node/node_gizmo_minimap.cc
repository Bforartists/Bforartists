/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spnode
 */

#include "BLI_listbase.h"
#include "BLI_math_base.h"
#include "BLI_math_vector.h"
#include "BLI_rect.h"

#include "BKE_context.hh"
#include "BKE_node.hh"
#include "BKE_node_runtime.hh"
#include "BKE_screen.hh"

#include "DNA_screen_types.h"

#include "GPU_batch.hh"
#include "GPU_select.hh"
#include "GPU_state.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_screen.hh"

#include "UI_interface.hh"
#include "UI_interface_c.hh"
#include "UI_resources.hh"

#include "node_intern.hh" /* own include */

namespace blender::ed::space_node {

struct NodeGizmoMinimap {
  wmGizmo gizmo;
};

/* -------------------------------------------------------------------- */

static void gizmo_minimap_draw(const bContext * /*C*/, wmGizmo * /*gz*/)
{
  /* pass */
}

static int gizmo_minimap_test_select(bContext *C, wmGizmo * /*gz*/, const int mval[2])
{
  const float mval_fl[2] = {
      static_cast<float>(mval[0]),
      static_cast<float>(mval[1]),
  };
  SpaceNode *snode = CTX_wm_space_node(C);

  ARegion *region = CTX_wm_region(C);
  View2D v2d = region->v2d;

  float minimap_overlay_scale = snode->minimap_scale;
  float minimap_size = 150.0f * minimap_overlay_scale * UI_SCALE_FAC;
  float padding = 10.0f * UI_SCALE_FAC;

  float minimap_aspect_ratio = snode->minimap_aspect_ratio;

  float minimap_width = minimap_size * minimap_aspect_ratio;
  float minimap_height = minimap_size;
  if (minimap_aspect_ratio > 1) {
    minimap_width = minimap_size;
    minimap_height = minimap_size / minimap_aspect_ratio;
  }

  const rcti *rect_visible = ED_region_visible_rect(region);
  const float viewport_height = BLI_rcti_size_y(&v2d.mask);
  float viewport_width = BLI_rcti_size_x(&v2d.mask);
  float tile_height = viewport_height - BLI_rcti_size_y(rect_visible);
  float padding_top = padding;
  if (snode->gizmo_flag & SNODE_GIZMO_MINIMAP_MOVE_TO_TOP) {
    viewport_width = BLI_rcti_size_x(rect_visible);
    tile_height = 0;
    padding_top = viewport_height - minimap_height - padding;
  }

  rctf minimap_rect;
  BLI_rctf_init(&minimap_rect,
                viewport_width - padding - minimap_width,
                viewport_width - padding,
                padding_top + tile_height,
                padding_top + minimap_height + tile_height);
  if (BLI_rctf_isect_pt_v(&minimap_rect, mval_fl)) {
    return 1;
  }

  return -1;
}

/* -------------------------------------------------------------------- */
/** \name Cursor state
 * 0 = hover, 1 = dragging, 2 = double click
 * \{ */

static int gizmo_minimap_cursor_get(wmGizmo *gz)
{
  return WM_CURSOR_HAND;
}

static wmOperatorStatus gizmo_minimap_modal(bContext *C,
                                            wmGizmo *gz,
                                            const wmEvent *event,
                                            eWM_GizmoFlagTweak /*tweak_flag*/)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  if (!snode || !snode->edittree) {
    return OPERATOR_CANCELLED;
  }
  
  if (event->type != MOUSEMOVE) {
    return OPERATOR_RUNNING_MODAL;
  }

  ARegion *region = CTX_wm_region(C);

  float mval[2] = {static_cast<float>(event->mval[0]), static_cast<float>(event->mval[1])};
  float mval_last[2];
  RNA_float_get_array(gz->ptr, "drag_last_pos", mval_last);
  RNA_float_set_array(gz->ptr, "drag_last_pos", mval);

  float delta_factor = RNA_float_get(gz->ptr, "delta_factor");
  float delta_x = (mval[0] - mval_last[0]) * delta_factor;
  float delta_y = (mval[1] - mval_last[1]) * delta_factor;

  PointerRNA op_ptr = WM_operator_properties_create("VIEW2D_OT_pan");
  RNA_int_set(&op_ptr, "deltax", delta_x);
  RNA_int_set(&op_ptr, "deltay", delta_y);

  WM_operator_name_call(C, "VIEW2D_OT_pan", wm::OpCallContext::ExecDefault, &op_ptr, nullptr);
  WM_operator_properties_free(&op_ptr);

  ED_region_tag_redraw(region);

  /* tag the region for redraw */
  ED_region_tag_redraw_editor_overlays(region);
  WM_event_add_mousemove(CTX_wm_window(C));

  return OPERATOR_RUNNING_MODAL;
}

static wmOperatorStatus gizmo_minimap_invoke(bContext *C, wmGizmo *gz, const wmEvent *event)
{
  float mval[2] = {static_cast<float>(event->mval[0]), static_cast<float>(event->mval[1])};
  RNA_float_set_array(gz->ptr, "drag_start_pos", mval);
  RNA_float_set_array(gz->ptr, "drag_last_pos", mval);

  ARegion *region = CTX_wm_region(C);
  View2D v2d = region->v2d;
  SpaceNode *snode = CTX_wm_space_node(C);

  if (!snode || !snode->edittree) {
    return OPERATOR_CANCELLED;
  }

  const rcti *rect_visible = ED_region_visible_rect(region);
  const float viewport_height = BLI_rcti_size_y(&v2d.mask);
  float tile_height = 0;
  if (!(snode->gizmo_flag & SNODE_GIZMO_MINIMAP_MOVE_TO_TOP)) {
    tile_height = viewport_height - BLI_rcti_size_y(rect_visible);
  }

  const float zoom = (float)(BLI_rcti_size_x(&v2d.mask) + 1) / BLI_rctf_size_x(&v2d.cur);
  float min[2], max[2];
  INIT_MINMAX2(min, max);
  for (bNode &node : snode->edittree->nodes) {
    float pos_min[2] = {node.runtime->draw_bounds.xmin, node.runtime->draw_bounds.ymin};
    float pos_max[2] = {node.runtime->draw_bounds.xmax, node.runtime->draw_bounds.ymax};
    minmax_v2v2_v2(min, max, pos_min);
    minmax_v2v2_v2(min, max, pos_max);
  }
  float minimap_aspect_ratio = snode->minimap_aspect_ratio;
  float minimap_overlay_scale = snode->minimap_scale;

  float minimap_size = 150 * minimap_overlay_scale * UI_SCALE_FAC;
  float inner_padding = 10.0f * UI_SCALE_FAC;

  float minimap_width = minimap_size * minimap_aspect_ratio;
  float minimap_height = minimap_size;
  if (minimap_aspect_ratio > 1) {
    minimap_width = minimap_size;
    minimap_height = minimap_size / minimap_aspect_ratio;
  }

  float minimap_width_without_padding = minimap_width - inner_padding * 2;
  float minimap_height_without_padding = minimap_height - inner_padding * 2;
  rctf minimap_space;
  BLI_rctf_init(&minimap_space, min[0], max[0], min[1], max[1] + tile_height);
  float minimap_space_width = BLI_rctf_size_x(&minimap_space);
  float minimap_space_height = BLI_rctf_size_y(&minimap_space);
  float minimap_scale = min_ff(minimap_width_without_padding / minimap_space_width,
                               minimap_height_without_padding / minimap_space_height);

  float delta_factor = 1 / minimap_scale * zoom;
  RNA_float_set(gz->ptr, "delta_factor", delta_factor);

  return OPERATOR_RUNNING_MODAL;
}

/** \} */

void NODE_GT_minimap(wmGizmoType *gzt)
{
  /* identifiers */
  gzt->idname = "NODE_GT_minimap";

  /* api callbacks */
  gzt->draw = gizmo_minimap_draw;
  gzt->test_select = gizmo_minimap_test_select;
  gzt->cursor_get = gizmo_minimap_cursor_get;

  gzt->modal = gizmo_minimap_modal;
  gzt->invoke = gizmo_minimap_invoke;

  gzt->struct_size = sizeof(NodeGizmoMinimap);

  /* rna */
  RNA_def_float_vector(gzt->srna,
                       "drag_start_pos",
                       2,
                       nullptr,
                       -FLT_MAX,
                       FLT_MAX,
                       "Drag Start Pos",
                       "",
                       -FLT_MAX,
                       FLT_MAX);
  RNA_def_float_vector(gzt->srna,
                       "drag_last_pos",
                       2,
                       nullptr,
                       -FLT_MAX,
                       FLT_MAX,
                       "Drag Last Pos",
                       "",
                       -FLT_MAX,
                       FLT_MAX);
  RNA_def_float(gzt->srna,
                "delta_factor",
                0.0f,
                0.0f,
                FLT_MAX,
                "Delta factor depending on node space and zoom",
                "",
                0.0f,
                FLT_MAX);
}

}  // namespace blender::ed::space_node