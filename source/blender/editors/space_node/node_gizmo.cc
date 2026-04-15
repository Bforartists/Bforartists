/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spnode
 */

#include <cmath>

#include "BLI_listbase.h"
#include "BLI_math_base.hh"
#include "BLI_math_matrix.h"
#include "BLI_math_rotation.h"
#include "BLI_math_vector.h"
#include "BLI_rect.h"
#include "BLI_string.h"
#include "BLI_utildefines.h"

#include "BKE_context.hh"
#include "BKE_image.hh"
#include "BKE_node_runtime.hh"

#include "ED_gizmo_library.hh"
#include "ED_screen.hh"

#include "IMB_imbuf_types.hh"

#include "MEM_guardedalloc.h"

#include "RNA_access.hh"
#include "RNA_prototypes.hh"

#include "NOD_compositor_gizmos.hh"

#include "WM_types.hh"

#include "node_intern.hh"

namespace blender::ed::space_node {

/* -------------------------------------------------------------------- */
/** \name Backdrop Gizmo
 * \{ */

void NODE_GGT_backdrop_transform(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Backdrop Transform Widget";
  gzgt->idname = "NODE_GGT_backdrop_transform";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

  gzgt->poll = nodes::gizmos::transform_poll;
  gzgt->setup = nodes::gizmos::transform_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->refresh = nodes::gizmos::transform_refresh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Crop Gizmo
 * \{ */

void NODE_GGT_backdrop_crop(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Backdrop Crop Widget";
  gzgt->idname = "NODE_GGT_backdrop_crop";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

  gzgt->poll = nodes::gizmos::crop_poll_space_node;
  gzgt->setup = nodes::gizmos::crop_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->draw_prepare = nodes::gizmos::crop_draw_prepare_space_node;
  gzgt->refresh = nodes::gizmos::crop_refresh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Box Mask
 * \{ */

void NODE_GGT_backdrop_box_mask(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Backdrop Box Mask Widget";
  gzgt->idname = "NODE_GGT_backdrop_box_mask";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

  gzgt->poll = nodes::gizmos::box_mask_poll_space_node;
  gzgt->setup = nodes::gizmos::box_mask_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->draw_prepare = nodes::gizmos::bbox_draw_prepare_space_node;
  gzgt->refresh = nodes::gizmos::box_mask_refresh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Ellipse Mask
 * \{ */

void NODE_GGT_backdrop_ellipse_mask(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Backdrop Ellipse Mask Widget";
  gzgt->idname = "NODE_GGT_backdrop_ellipse_mask";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

  gzgt->poll = nodes::gizmos::ellipse_mask_poll_space_node;
  gzgt->setup = nodes::gizmos::ellipse_mask_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->draw_prepare = nodes::gizmos::bbox_draw_prepare_space_node;
  gzgt->refresh = nodes::gizmos::box_mask_refresh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Glare
 * \{ */

void NODE_GGT_backdrop_glare(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Glare Widget";
  gzgt->idname = "NODE_GGT_glare";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

  gzgt->poll = nodes::gizmos::glare_poll_space_node;
  gzgt->setup = nodes::gizmos::glare_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->draw_prepare = nodes::gizmos::glare_draw_prepare_space_node;
  gzgt->refresh = nodes::gizmos::glare_refresh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Corner Pin
 * \{ */

void NODE_GGT_backdrop_corner_pin(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Corner Pin Widget";
  gzgt->idname = "NODE_GGT_backdrop_corner_pin";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

  gzgt->poll = nodes::gizmos::corner_pin_poll_space_node;
  gzgt->setup = nodes::gizmos::corner_pin_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->draw_prepare = nodes::gizmos::corner_pin_draw_prepare_space_node;
  gzgt->refresh = nodes::gizmos::corner_pin_refresh;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Split
 * \{ */

void NODE_GGT_backdrop_split(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Split Widget";
  gzgt->idname = "NODE_GGT_backdrop_split";

  gzgt->flag |= WM_GIZMOGROUPTYPE_PERSISTENT;

  gzgt->poll = nodes::gizmos::split_poll_space_node;
  gzgt->setup = nodes::gizmos::split_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->draw_prepare = nodes::gizmos::bbox_draw_prepare_space_node;
  gzgt->refresh = nodes::gizmos::split_refresh;
}

/* -------------------------------------------------------------------- */
/** \name BFA Minimap Gizmo
 * \{ */

struct NodeMinimapWidgetGroup {
  wmGizmo *gizmo;
};

static bool WIDGETGROUP_node_minimap_poll(const bContext *C, wmGizmoGroupType * /*gzgt*/)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  ARegion *region = CTX_wm_region(C);
  View2D v2d = region->v2d;

  if (snode && !(snode->gizmo_flag & SNODE_GIZMO_HIDE) &&
      snode->gizmo_flag & SNODE_GIZMO_SHOW_MINIMAP && snode->edittree)
  {
    float min[2], max[2];
    INIT_MINMAX2(min, max);
    for (bNode &node : snode->edittree->nodes) {
      float pos_min[2] = {node.runtime->draw_bounds.xmin, node.runtime->draw_bounds.ymin};
      float pos_max[2] = {node.runtime->draw_bounds.xmax, node.runtime->draw_bounds.ymax};
      minmax_v2v2_v2(min, max, pos_min);
      minmax_v2v2_v2(min, max, pos_max);
    }
    rctf minimap_space;
    BLI_rctf_init(&minimap_space, min[0], max[0], min[1], max[1]);
    float minimap_space_width = BLI_rctf_size_x(&minimap_space);
    float minimap_space_height = BLI_rctf_size_y(&minimap_space);
    const float v2d_width = BLI_rctf_size_x(&v2d.cur);
    const float v2d_height = BLI_rctf_size_y(&v2d.cur);
    if (v2d_width >= minimap_space_width && v2d_height >= minimap_space_height && snode->gizmo_flag & SNODE_GIZMO_MINIMAP_AUTO_HIDE) {
      return false;
    }
    return true;
  }

  return false;
}

static void WIDGETGROUP_node_minimap_setup(const bContext * /*C*/, wmGizmoGroup *gzgroup)
{
  NodeMinimapWidgetGroup *minimap_group = MEM_new<NodeMinimapWidgetGroup>(__func__);
  minimap_group->gizmo = WM_gizmo_new("NODE_GT_minimap", gzgroup, nullptr);
  minimap_group->gizmo->flag |= (WM_GIZMO_MOVE_CURSOR | WM_GIZMO_DRAW_MODAL);

  gzgroup->customdata = minimap_group;
  gzgroup->customdata_free = [](void *customdata) {
    MEM_delete(static_cast<NodeMinimapWidgetGroup *>(customdata));
  };
}

static void WIDGETGROUP_node_minimap_draw_prepare(const bContext * /*C*/, wmGizmoGroup *gzgroup)
{
  NodeMinimapWidgetGroup *minimap_group = (NodeMinimapWidgetGroup *)gzgroup->customdata;
  wmGizmo *gz = minimap_group->gizmo;
  gz->scale_basis = 2.0f;
}

void NODE_GGT_minimap(wmGizmoGroupType *gzgt)
{
  gzgt->name = "Minimap Widget";
  gzgt->idname = "NODE_GGT_minimap";

  gzgt->flag |= (WM_GIZMOGROUPTYPE_PERSISTENT | WM_GIZMOGROUPTYPE_2D_UI);

  gzgt->poll = WIDGETGROUP_node_minimap_poll;
  gzgt->setup = WIDGETGROUP_node_minimap_setup;
  gzgt->setup_keymap = WM_gizmogroup_setup_keymap_generic_maybe_drag;
  gzgt->draw_prepare = WIDGETGROUP_node_minimap_draw_prepare;
}

/** \} */

}  // namespace blender::ed::space_node
