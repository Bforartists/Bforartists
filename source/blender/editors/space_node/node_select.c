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
 *
 * The Original Code is Copyright (C) 2008 Blender Foundation.
 * All rights reserved.
 */

/** \file
 * \ingroup spnode
 */

#include <stdlib.h>

#include "DNA_node_types.h"
#include "DNA_windowmanager_types.h"

#include "BLI_lasso_2d.h"
#include "BLI_listbase.h"
#include "BLI_math.h"
#include "BLI_rect.h"
#include "BLI_string.h"
#include "BLI_string_utf8.h"
#include "BLI_utildefines.h"

#include "BKE_context.h"
#include "BKE_main.h"
#include "BKE_node.h"
#include "BKE_workspace.h"

#include "ED_node.h" /* own include */
#include "ED_screen.h"
#include "ED_select_utils.h"
#include "ED_view3d.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"
#include "WM_types.h"

#include "UI_interface.h"
#include "UI_resources.h"
#include "UI_view2d.h"

#include "DEG_depsgraph.h"

#include "MEM_guardedalloc.h"

#include "node_intern.h" /* own include */

/* Function to detect if there is a visible view3d that uses workbench in texture mode.
 * This function is for fixing T76970 for Blender 2.83. The actual fix should add a mechanism in
 * the depsgraph that can be used by the draw engines to check if they need to be redrawn.
 *
 * We don't want to add these risky changes this close before releasing 2.83 without good testing
 * hence this workaround. There are still cases were too many updates happen. For example when you
 * have both a Cycles and workbench with textures viewport.
 * */
static bool has_workbench_in_texture_color(const wmWindowManager *wm,
                                           const Scene *scene,
                                           const Object *ob)
{
  LISTBASE_FOREACH (wmWindow *, win, &wm->windows) {
    if (win->scene != scene) {
      continue;
    }
    const bScreen *screen = BKE_workspace_active_screen_get(win->workspace_hook);
    LISTBASE_FOREACH (ScrArea *, area, &screen->areabase) {
      if (area->spacetype == SPACE_VIEW3D) {
        const View3D *v3d = area->spacedata.first;

        if (ED_view3d_has_workbench_in_texture_color(scene, ob, v3d)) {
          return true;
        }
      }
    }
  }
  return false;
}

/* -------------------------------------------------------------------- */
/** \name Public Node Selection API
 * \{ */

static bNode *node_under_mouse_select(bNodeTree *ntree, int mx, int my)
{
  bNode *node;

  for (node = ntree->nodes.last; node; node = node->prev) {
    if (node->typeinfo->select_area_func) {
      if (node->typeinfo->select_area_func(node, mx, my)) {
        return node;
      }
    }
  }
  return NULL;
}

static bNode *node_under_mouse_tweak(bNodeTree *ntree, int mx, int my)
{
  bNode *node;

  for (node = ntree->nodes.last; node; node = node->prev) {
    if (node->typeinfo->tweak_area_func) {
      if (node->typeinfo->tweak_area_func(node, mx, my)) {
        return node;
      }
    }
  }
  return NULL;
}

static bool is_position_over_node_or_socket(SpaceNode *snode, float mouse[2])
{
  if (node_under_mouse_tweak(snode->edittree, mouse[0], mouse[1])) {
    return true;
  }

  bNode *node;
  bNodeSocket *sock;
  if (node_find_indicated_socket(snode, &node, &sock, mouse, SOCK_IN | SOCK_OUT)) {
    return true;
  }

  return false;
}

static bool is_event_over_node_or_socket(bContext *C, const wmEvent *event)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  ARegion *region = CTX_wm_region(C);
  float mouse[2];
  UI_view2d_region_to_view(&region->v2d, event->mval[0], event->mval[1], &mouse[0], &mouse[1]);
  return is_position_over_node_or_socket(snode, mouse);
}

static void node_toggle(bNode *node)
{
  nodeSetSelected(node, !(node->flag & SELECT));
}

void node_socket_select(bNode *node, bNodeSocket *sock)
{
  sock->flag |= SELECT;

  /* select node too */
  if (node) {
    node->flag |= SELECT;
  }
}

void node_socket_deselect(bNode *node, bNodeSocket *sock, const bool deselect_node)
{
  sock->flag &= ~SELECT;

  if (node && deselect_node) {
    bool sel = 0;

    /* if no selected sockets remain, also deselect the node */
    for (sock = node->inputs.first; sock; sock = sock->next) {
      if (sock->flag & SELECT) {
        sel = 1;
        break;
      }
    }
    for (sock = node->outputs.first; sock; sock = sock->next) {
      if (sock->flag & SELECT) {
        sel = 1;
        break;
      }
    }

    if (!sel) {
      node->flag &= ~SELECT;
    }
  }
}

static void node_socket_toggle(bNode *node, bNodeSocket *sock, int deselect_node)
{
  if (sock->flag & SELECT) {
    node_socket_deselect(node, sock, deselect_node);
  }
  else {
    node_socket_select(node, sock);
  }
}

/* no undo here! */
void node_deselect_all(SpaceNode *snode)
{
  bNode *node;

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    nodeSetSelected(node, false);
  }
}

void node_deselect_all_input_sockets(SpaceNode *snode, const bool deselect_nodes)
{
  bNode *node;
  bNodeSocket *sock;

  /* XXX not calling node_socket_deselect here each time, because this does iteration
   * over all node sockets internally to check if the node stays selected.
   * We can do that more efficiently here.
   */

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    int sel = 0;

    for (sock = node->inputs.first; sock; sock = sock->next) {
      sock->flag &= ~SELECT;
    }

    /* if no selected sockets remain, also deselect the node */
    if (deselect_nodes) {
      for (sock = node->outputs.first; sock; sock = sock->next) {
        if (sock->flag & SELECT) {
          sel = 1;
          break;
        }
      }

      if (!sel) {
        node->flag &= ~SELECT;
      }
    }
  }
}

void node_deselect_all_output_sockets(SpaceNode *snode, const bool deselect_nodes)
{
  bNode *node;
  bNodeSocket *sock;

  /* XXX not calling node_socket_deselect here each time, because this does iteration
   * over all node sockets internally to check if the node stays selected.
   * We can do that more efficiently here.
   */

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    bool sel = false;

    for (sock = node->outputs.first; sock; sock = sock->next) {
      sock->flag &= ~SELECT;
    }

    /* if no selected sockets remain, also deselect the node */
    if (deselect_nodes) {
      for (sock = node->inputs.first; sock; sock = sock->next) {
        if (sock->flag & SELECT) {
          sel = 1;
          break;
        }
      }

      if (!sel) {
        node->flag &= ~SELECT;
      }
    }
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Select Grouped Operator
 * \{ */

/* Return true if we need redraw, otherwise false. */

static bool node_select_grouped_type(SpaceNode *snode, bNode *node_act)
{
  bNode *node;
  bool changed = false;

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    if ((node->flag & SELECT) == 0) {
      if (node->type == node_act->type) {
        nodeSetSelected(node, true);
        changed = true;
      }
    }
  }

  return changed;
}

static bool node_select_grouped_color(SpaceNode *snode, bNode *node_act)
{
  bNode *node;
  bool changed = false;

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    if ((node->flag & SELECT) == 0) {
      if (compare_v3v3(node->color, node_act->color, 0.005f)) {
        nodeSetSelected(node, true);
        changed = true;
      }
    }
  }

  return changed;
}

static bool node_select_grouped_name(SpaceNode *snode, bNode *node_act, const bool from_right)
{
  bNode *node;
  bool changed = false;
  const uint delims[] = {'.', '-', '_', '\0'};
  size_t pref_len_act, pref_len_curr;
  const char *sep, *suf_act, *suf_curr;

  pref_len_act = BLI_str_partition_ex_utf8(
      node_act->name, NULL, delims, &sep, &suf_act, from_right);

  /* Note: in case we are searching for suffix, and found none, use whole name as suffix. */
  if (from_right && !(sep && suf_act)) {
    pref_len_act = 0;
    suf_act = node_act->name;
  }

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    if (node->flag & SELECT) {
      continue;
    }
    pref_len_curr = BLI_str_partition_ex_utf8(
        node->name, NULL, delims, &sep, &suf_curr, from_right);

    /* Same as with active node name! */
    if (from_right && !(sep && suf_curr)) {
      pref_len_curr = 0;
      suf_curr = node->name;
    }

    if ((from_right && STREQ(suf_act, suf_curr)) ||
        (!from_right && (pref_len_act == pref_len_curr) &&
         STREQLEN(node_act->name, node->name, pref_len_act))) {
      nodeSetSelected(node, true);
      changed = true;
    }
  }

  return changed;
}

enum {
  NODE_SELECT_GROUPED_TYPE = 0,
  NODE_SELECT_GROUPED_COLOR = 1,
  NODE_SELECT_GROUPED_PREFIX = 2,
  NODE_SELECT_GROUPED_SUFIX = 3,
};

static int node_select_grouped_exec(bContext *C, wmOperator *op)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  bNode *node_act = nodeGetActive(snode->edittree);
  bNode *node;
  bool changed = false;
  const bool extend = RNA_boolean_get(op->ptr, "extend");
  const int type = RNA_enum_get(op->ptr, "type");

  if (!extend) {
    for (node = snode->edittree->nodes.first; node; node = node->next) {
      nodeSetSelected(node, false);
    }
  }
  nodeSetSelected(node_act, true);

  switch (type) {
    case NODE_SELECT_GROUPED_TYPE:
      changed = node_select_grouped_type(snode, node_act);
      break;
    case NODE_SELECT_GROUPED_COLOR:
      changed = node_select_grouped_color(snode, node_act);
      break;
    case NODE_SELECT_GROUPED_PREFIX:
      changed = node_select_grouped_name(snode, node_act, false);
      break;
    case NODE_SELECT_GROUPED_SUFIX:
      changed = node_select_grouped_name(snode, node_act, true);
      break;
    default:
      break;
  }

  if (changed) {
    ED_node_sort(snode->edittree);
    WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);
    return OPERATOR_FINISHED;
  }

  return OPERATOR_CANCELLED;
}

void NODE_OT_select_grouped(wmOperatorType *ot)
{
  static const EnumPropertyItem prop_select_grouped_types[] = {
      {NODE_SELECT_GROUPED_TYPE, "TYPE", 0, "Type", ""},
      {NODE_SELECT_GROUPED_COLOR, "COLOR", 0, "Color", ""},
      {NODE_SELECT_GROUPED_PREFIX, "PREFIX", 0, "Prefix", ""},
      {NODE_SELECT_GROUPED_SUFIX, "SUFFIX", 0, "Suffix", ""},
      {0, NULL, 0, NULL, NULL},
  };

  /* identifiers */
  ot->name = "Select Grouped";
  ot->description = "Select nodes with similar properties";
  ot->idname = "NODE_OT_select_grouped";

  /* api callbacks */
  ot->invoke = WM_menu_invoke;
  ot->exec = node_select_grouped_exec;
  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(ot->srna,
                  "extend",
                  false,
                  "Extend",
                  "Extend selection instead of deselecting everything first");
  ot->prop = RNA_def_enum(ot->srna, "type", prop_select_grouped_types, 0, "Type", "");
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Select (Cursor Pick) Operator
 * \{ */

void node_select_single(bContext *C, bNode *node)
{
  Main *bmain = CTX_data_main(C);
  SpaceNode *snode = CTX_wm_space_node(C);
  const Object *ob = CTX_data_active_object(C);
  const Scene *scene = CTX_data_scene(C);
  const wmWindowManager *wm = CTX_wm_manager(C);
  bool active_texture_changed = false;
  bNode *tnode;

  for (tnode = snode->edittree->nodes.first; tnode; tnode = tnode->next) {
    if (tnode != node) {
      nodeSetSelected(tnode, false);
    }
  }
  nodeSetSelected(node, true);

  ED_node_set_active(bmain, snode->edittree, node, &active_texture_changed);
  ED_node_set_active_viewer_key(snode);

  ED_node_sort(snode->edittree);
  if (active_texture_changed && has_workbench_in_texture_color(wm, scene, ob)) {
    DEG_id_tag_update(&snode->edittree->id, ID_RECALC_COPY_ON_WRITE);
  }

  WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);
}

static int node_mouse_select(bContext *C,
                             wmOperator *op,
                             const int mval[2],
                             bool wait_to_deselect_others)
{
  Main *bmain = CTX_data_main(C);
  SpaceNode *snode = CTX_wm_space_node(C);
  ARegion *region = CTX_wm_region(C);
  const Object *ob = CTX_data_active_object(C);
  const Scene *scene = CTX_data_scene(C);
  const wmWindowManager *wm = CTX_wm_manager(C);
  bNode *node, *tnode;
  bNodeSocket *sock = NULL;
  bNodeSocket *tsock;
  float cursor[2];
  int ret_value = OPERATOR_CANCELLED;

  const bool extend = RNA_boolean_get(op->ptr, "extend");
  /* always do socket_select when extending selection. */
  const bool socket_select = extend || RNA_boolean_get(op->ptr, "socket_select");
  const bool deselect_all = RNA_boolean_get(op->ptr, "deselect_all");

  /* These cases are never modal. */
  if (extend || socket_select) {
    wait_to_deselect_others = false;
  }

  /* get mouse coordinates in view2d space */
  UI_view2d_region_to_view(&region->v2d, mval[0], mval[1], &cursor[0], &cursor[1]);

  /* first do socket selection, these generally overlap with nodes. */
  if (socket_select) {
    if (node_find_indicated_socket(snode, &node, &sock, cursor, SOCK_IN)) {
      /* NOTE: SOCK_IN does not take into account the extend case...
       * This feature is not really used anyway currently? */
      node_socket_toggle(node, sock, true);
      ret_value = OPERATOR_FINISHED;
    }
    else if (node_find_indicated_socket(snode, &node, &sock, cursor, SOCK_OUT)) {
      if (sock->flag & SELECT) {
        if (extend) {
          node_socket_deselect(node, sock, true);
        }
        else {
          ret_value = OPERATOR_FINISHED;
        }
      }
      else {
        /* Only allow one selected output per node, for sensible linking.
         * Allow selecting outputs from different nodes though, if extend is true. */
        if (node) {
          for (tsock = node->outputs.first; tsock; tsock = tsock->next) {
            if (tsock == sock) {
              continue;
            }
            node_socket_deselect(node, tsock, true);
          }
        }
        if (!extend) {
          for (tnode = snode->edittree->nodes.first; tnode; tnode = tnode->next) {
            if (tnode == node) {
              continue;
            }
            for (tsock = tnode->outputs.first; tsock; tsock = tsock->next) {
              node_socket_deselect(tnode, tsock, true);
            }
          }
        }
        node_socket_select(node, sock);
        ret_value = OPERATOR_FINISHED;
      }
    }
  }

  if (!sock) {
    /* find the closest visible node */
    node = node_under_mouse_select(snode->edittree, (int)cursor[0], (int)cursor[1]);

    if (extend) {
      if (node != NULL) {
        /* If node is selected but not active, we want to make it active,
         * but not toggle (deselect) it. */
        if (!((node->flag & SELECT) && (node->flag & NODE_ACTIVE) == 0)) {
          node_toggle(node);
        }
        ret_value = OPERATOR_FINISHED;
      }
    }
    else if (deselect_all && node == NULL) {
      /* Deselect in empty space. */
      for (tnode = snode->edittree->nodes.first; tnode; tnode = tnode->next) {
        nodeSetSelected(tnode, false);
      }
      ret_value = OPERATOR_FINISHED;
    }
    else if (node != NULL) {
      /* When clicking on an already selected node, we want to wait to deselect
       * others and allow the user to start moving the node without that. */
      if (wait_to_deselect_others && (node->flag & SELECT)) {
        ret_value = OPERATOR_RUNNING_MODAL;
      }
      else {
        nodeSetSelected(node, true);

        for (tnode = snode->edittree->nodes.first; tnode; tnode = tnode->next) {
          if (tnode != node) {
            nodeSetSelected(tnode, false);
          }
        }

        ret_value = OPERATOR_FINISHED;
      }
    }
  }

  /* update node order */
  if (ret_value != OPERATOR_CANCELLED) {
    bool active_texture_changed = false;
    if (node != NULL && ret_value != OPERATOR_RUNNING_MODAL) {
      ED_node_set_active(bmain, snode->edittree, node, &active_texture_changed);
    }
    ED_node_set_active_viewer_key(snode);
    ED_node_sort(snode->edittree);
    if (active_texture_changed && has_workbench_in_texture_color(wm, scene, ob)) {
      DEG_id_tag_update(&snode->edittree->id, ID_RECALC_COPY_ON_WRITE);
    }

    WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);
  }

  return ret_value;
}

static int node_select_exec(bContext *C, wmOperator *op)
{
  const bool wait_to_deselect_others = RNA_boolean_get(op->ptr, "wait_to_deselect_others");

  /* get settings from RNA properties for operator */
  int mval[2];
  mval[0] = RNA_int_get(op->ptr, "mouse_x");
  mval[1] = RNA_int_get(op->ptr, "mouse_y");

  /* perform the select */
  const int ret_value = node_mouse_select(C, op, mval, wait_to_deselect_others);

  /* allow tweak event to work too */
  return ret_value | OPERATOR_PASS_THROUGH;
}

void NODE_OT_select(wmOperatorType *ot)
{
  PropertyRNA *prop;

  /* identifiers */
  ot->name = "Select";
  ot->idname = "NODE_OT_select";
  ot->description = "Select the node under the cursor";

  /* api callbacks */
  ot->exec = node_select_exec;
  ot->invoke = WM_generic_select_invoke;
  ot->modal = WM_generic_select_modal;
  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  WM_operator_properties_generic_select(ot);
  RNA_def_boolean(ot->srna, "extend", false, "Extend", "");
  RNA_def_boolean(ot->srna, "socket_select", false, "Socket Select", "");
  prop = RNA_def_boolean(ot->srna,
                         "deselect_all",
                         false,
                         "Deselect On Nothing",
                         "Deselect all when nothing under the cursor");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Box Select Operator
 * \{ */

static int node_box_select_exec(bContext *C, wmOperator *op)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  ARegion *region = CTX_wm_region(C);
  rctf rectf;

  WM_operator_properties_border_to_rctf(op, &rectf);
  UI_view2d_region_to_view_rctf(&region->v2d, &rectf, &rectf);

  const eSelectOp sel_op = RNA_enum_get(op->ptr, "mode");
  const bool select = (sel_op != SEL_OP_SUB);
  if (SEL_OP_USE_PRE_DESELECT(sel_op)) {
    ED_node_select_all(&snode->edittree->nodes, SEL_DESELECT);
  }

  LISTBASE_FOREACH (bNode *, node, &snode->edittree->nodes) {
    bool is_inside;
    if (node->type == NODE_FRAME) {
      is_inside = BLI_rctf_inside_rctf(&rectf, &node->totr);
    }
    else {
      is_inside = BLI_rctf_isect(&rectf, &node->totr, NULL);
    }

    if (is_inside) {
      nodeSetSelected(node, select);
    }
  }

  ED_node_sort(snode->edittree);

  WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);

  return OPERATOR_FINISHED;
}

static int node_box_select_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  const bool tweak = RNA_boolean_get(op->ptr, "tweak");

  if (tweak && is_event_over_node_or_socket(C, event)) {
    return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
  }

  return WM_gesture_box_invoke(C, op, event);
}

void NODE_OT_select_box(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Box Select";
  ot->idname = "NODE_OT_select_box";
  ot->description = "Use box selection to select nodes";

  /* api callbacks */
  ot->invoke = node_box_select_invoke;
  ot->exec = node_box_select_exec;
  ot->modal = WM_gesture_box_modal;
  ot->cancel = WM_gesture_box_cancel;

  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(ot->srna,
                  "tweak",
                  0,
                  "Tweak",
                  "Only activate when mouse is not over a node - useful for tweak gesture");

  WM_operator_properties_gesture_box(ot);
  WM_operator_properties_select_operation_simple(ot);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Circle Select Operator
 * \{ */

static int node_circleselect_exec(bContext *C, wmOperator *op)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  ARegion *region = CTX_wm_region(C);
  bNode *node;

  int x, y, radius;
  float offset[2];

  float zoom = (float)(BLI_rcti_size_x(&region->winrct)) /
               (float)(BLI_rctf_size_x(&region->v2d.cur));

  const eSelectOp sel_op = ED_select_op_modal(RNA_enum_get(op->ptr, "mode"),
                                              WM_gesture_is_modal_first(op->customdata));
  const bool select = (sel_op != SEL_OP_SUB);
  if (SEL_OP_USE_PRE_DESELECT(sel_op)) {
    ED_node_select_all(&snode->edittree->nodes, SEL_DESELECT);
  }

  /* get operator properties */
  x = RNA_int_get(op->ptr, "x");
  y = RNA_int_get(op->ptr, "y");
  radius = RNA_int_get(op->ptr, "radius");

  UI_view2d_region_to_view(&region->v2d, x, y, &offset[0], &offset[1]);

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    if (BLI_rctf_isect_circle(&node->totr, offset, radius / zoom)) {
      nodeSetSelected(node, select);
    }
  }

  WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);

  return OPERATOR_FINISHED;
}

void NODE_OT_select_circle(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Circle Select";
  ot->idname = "NODE_OT_select_circle";
  ot->description = "Use circle selection to select nodes";

  /* api callbacks */
  ot->invoke = WM_gesture_circle_invoke;
  ot->exec = node_circleselect_exec;
  ot->modal = WM_gesture_circle_modal;

  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  WM_operator_properties_gesture_circle(ot);
  WM_operator_properties_select_operation_simple(ot);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Lasso Select Operator
 * \{ */

static int node_lasso_select_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  const bool tweak = RNA_boolean_get(op->ptr, "tweak");

  if (tweak && is_event_over_node_or_socket(C, event)) {
    return OPERATOR_CANCELLED | OPERATOR_PASS_THROUGH;
  }

  return WM_gesture_lasso_invoke(C, op, event);
}

static bool do_lasso_select_node(bContext *C,
                                 const int mcoords[][2],
                                 const int mcoords_len,
                                 eSelectOp sel_op)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  bNode *node;

  ARegion *region = CTX_wm_region(C);

  rcti rect;
  bool changed = false;

  const bool select = (sel_op != SEL_OP_SUB);
  if (SEL_OP_USE_PRE_DESELECT(sel_op)) {
    ED_node_select_all(&snode->edittree->nodes, SEL_DESELECT);
    changed = true;
  }

  /* get rectangle from operator */
  BLI_lasso_boundbox(&rect, mcoords, mcoords_len);

  /* do actual selection */
  for (node = snode->edittree->nodes.first; node; node = node->next) {

    if (select && (node->flag & NODE_SELECT)) {
      continue;
    }

    int screen_co[2];
    const float cent[2] = {BLI_rctf_cent_x(&node->totr), BLI_rctf_cent_y(&node->totr)};

    /* marker in screen coords */
    if (UI_view2d_view_to_region_clip(
            &region->v2d, cent[0], cent[1], &screen_co[0], &screen_co[1]) &&
        BLI_rcti_isect_pt(&rect, screen_co[0], screen_co[1]) &&
        BLI_lasso_is_point_inside(mcoords, mcoords_len, screen_co[0], screen_co[1], INT_MAX)) {
      nodeSetSelected(node, select);
      changed = true;
    }
  }

  if (changed) {
    WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);
  }

  return changed;
}

static int node_lasso_select_exec(bContext *C, wmOperator *op)
{
  int mcoords_len;
  const int(*mcoords)[2] = WM_gesture_lasso_path_to_array(C, op, &mcoords_len);

  if (mcoords) {
    const eSelectOp sel_op = RNA_enum_get(op->ptr, "mode");

    do_lasso_select_node(C, mcoords, mcoords_len, sel_op);

    MEM_freeN((void *)mcoords);

    return OPERATOR_FINISHED;
  }
  return OPERATOR_PASS_THROUGH;
}

void NODE_OT_select_lasso(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Lasso Select";
  ot->description = "Select nodes using lasso selection";
  ot->idname = "NODE_OT_select_lasso";

  /* api callbacks */
  ot->invoke = node_lasso_select_invoke;
  ot->modal = WM_gesture_lasso_modal;
  ot->exec = node_lasso_select_exec;
  ot->poll = ED_operator_node_active;
  ot->cancel = WM_gesture_lasso_cancel;

  /* flags */
  ot->flag = OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(ot->srna,
                  "tweak",
                  0,
                  "Tweak",
                  "Only activate when mouse is not over a node - useful for tweak gesture");

  WM_operator_properties_gesture_lasso(ot);
  WM_operator_properties_select_operation_simple(ot);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name (De)select All Operator
 * \{ */

static int node_select_all_exec(bContext *C, wmOperator *op)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  ListBase *node_lb = &snode->edittree->nodes;
  int action = RNA_enum_get(op->ptr, "action");

  ED_node_select_all(node_lb, action);

  ED_node_sort(snode->edittree);

  WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);
  return OPERATOR_FINISHED;
}

void NODE_OT_select_all(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "(De)select All";
  ot->description = "(De)select all nodes";
  ot->idname = "NODE_OT_select_all";

  /* api callbacks */
  ot->exec = node_select_all_exec;
  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  WM_operator_properties_select_all(ot);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Select Linked To Operator
 * \{ */

static int node_select_linked_to_exec(bContext *C, wmOperator *UNUSED(op))
{
  SpaceNode *snode = CTX_wm_space_node(C);
  bNodeLink *link;
  bNode *node;

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    node->flag &= ~NODE_TEST;
  }

  for (link = snode->edittree->links.first; link; link = link->next) {
    if (nodeLinkIsHidden(link)) {
      continue;
    }
    if (link->fromnode && link->tonode && (link->fromnode->flag & NODE_SELECT)) {
      link->tonode->flag |= NODE_TEST;
    }
  }

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    if (node->flag & NODE_TEST) {
      nodeSetSelected(node, true);
    }
  }

  ED_node_sort(snode->edittree);

  WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);
  return OPERATOR_FINISHED;
}

void NODE_OT_select_linked_to(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Select Linked To";
  ot->description = "Select nodes linked to the selected ones";
  ot->idname = "NODE_OT_select_linked_to";

  /* api callbacks */
  ot->exec = node_select_linked_to_exec;
  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Select Linked From Operator
 * \{ */

static int node_select_linked_from_exec(bContext *C, wmOperator *UNUSED(op))
{
  SpaceNode *snode = CTX_wm_space_node(C);
  bNodeLink *link;
  bNode *node;

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    node->flag &= ~NODE_TEST;
  }

  for (link = snode->edittree->links.first; link; link = link->next) {
    if (nodeLinkIsHidden(link)) {
      continue;
    }
    if (link->fromnode && link->tonode && (link->tonode->flag & NODE_SELECT)) {
      link->fromnode->flag |= NODE_TEST;
    }
  }

  for (node = snode->edittree->nodes.first; node; node = node->next) {
    if (node->flag & NODE_TEST) {
      nodeSetSelected(node, true);
    }
  }

  ED_node_sort(snode->edittree);

  WM_event_add_notifier(C, NC_NODE | NA_SELECTED, NULL);
  return OPERATOR_FINISHED;
}

void NODE_OT_select_linked_from(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Select Linked From";
  ot->description = "Select nodes linked from the selected ones";
  ot->idname = "NODE_OT_select_linked_from";

  /* api callbacks */
  ot->exec = node_select_linked_from_exec;
  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Select Same Type Step Operator
 * \{ */

static int node_select_same_type_step_exec(bContext *C, wmOperator *op)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  ARegion *region = CTX_wm_region(C);
  bNode **node_array;
  bNode *active = nodeGetActive(snode->edittree);
  int totnodes;
  const bool revert = RNA_boolean_get(op->ptr, "prev");
  const bool same_type = 1;

  ntreeGetDependencyList(snode->edittree, &node_array, &totnodes);

  if (totnodes > 1) {
    int a;

    for (a = 0; a < totnodes; a++) {
      if (node_array[a] == active) {
        break;
      }
    }

    if (same_type) {
      bNode *node = NULL;

      while (node == NULL) {
        if (revert) {
          a--;
        }
        else {
          a++;
        }

        if (a < 0 || a >= totnodes) {
          break;
        }

        node = node_array[a];

        if (node->type == active->type) {
          break;
        }
        else {
          node = NULL;
        }
      }
      if (node) {
        active = node;
      }
    }
    else {
      if (revert) {
        if (a == 0) {
          active = node_array[totnodes - 1];
        }
        else {
          active = node_array[a - 1];
        }
      }
      else {
        if (a == totnodes - 1) {
          active = node_array[0];
        }
        else {
          active = node_array[a + 1];
        }
      }
    }

    node_select_single(C, active);

    /* is note outside view? */
    if (active->totr.xmax < region->v2d.cur.xmin || active->totr.xmin > region->v2d.cur.xmax ||
        active->totr.ymax < region->v2d.cur.ymin || active->totr.ymin > region->v2d.cur.ymax) {
      const int smooth_viewtx = WM_operator_smooth_viewtx_get(op);
      space_node_view_flag(C, snode, region, NODE_SELECT, smooth_viewtx);
    }
  }

  if (node_array) {
    MEM_freeN(node_array);
  }

  return OPERATOR_FINISHED;
}

void NODE_OT_select_same_type_step(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Activate Same Type Next/Prev";
  ot->description = "Activate and view same node type, step by step";
  ot->idname = "NODE_OT_select_same_type_step";

  /* api callbacks */
  ot->exec = node_select_same_type_step_exec;
  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna, "prev", 0, "Previous", "");
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Find Node by Name Operator
 * \{ */

/* generic  search invoke */
static void node_find_update_fn(const struct bContext *C,
                                void *UNUSED(arg),
                                const char *str,
                                uiSearchItems *items)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  bNode *node;

  for (node = snode->edittree->nodes.first; node; node = node->next) {

    if (BLI_strcasestr(node->name, str) || BLI_strcasestr(node->label, str)) {
      char name[256];

      if (node->label[0]) {
        BLI_snprintf(name, 256, "%s (%s)", node->name, node->label);
      }
      else {
        BLI_strncpy(name, node->name, 256);
      }
      if (!UI_search_item_add(items, name, node, ICON_NONE, 0)) {
        break;
      }
    }
  }
}

static void node_find_exec_fn(struct bContext *C, void *UNUSED(arg1), void *arg2)
{
  SpaceNode *snode = CTX_wm_space_node(C);
  bNode *active = arg2;

  if (active) {
    ARegion *region = CTX_wm_region(C);
    node_select_single(C, active);

    /* is note outside view? */
    if (active->totr.xmax < region->v2d.cur.xmin || active->totr.xmin > region->v2d.cur.xmax ||
        active->totr.ymax < region->v2d.cur.ymin || active->totr.ymin > region->v2d.cur.ymax) {
      space_node_view_flag(C, snode, region, NODE_SELECT, U.smooth_viewtx);
    }
  }
}

static uiBlock *node_find_menu(bContext *C, ARegion *region, void *arg_op)
{
  static char search[256] = "";
  uiBlock *block;
  uiBut *but;
  wmOperator *op = (wmOperator *)arg_op;

  block = UI_block_begin(C, region, "_popup", UI_EMBOSS);
  UI_block_flag_enable(block, UI_BLOCK_LOOP | UI_BLOCK_MOVEMOUSE_QUIT | UI_BLOCK_SEARCH_MENU);
  UI_block_theme_style_set(block, UI_BLOCK_THEME_STYLE_POPUP);

  but = uiDefSearchBut(block,
                       search,
                       0,
                       ICON_VIEWZOOM,
                       sizeof(search),
                       10,
                       10,
                       UI_searchbox_size_x(),
                       UI_UNIT_Y,
                       0,
                       0,
                       "");
  UI_but_func_search_set(but, NULL, node_find_update_fn, op->type, NULL, node_find_exec_fn, NULL);
  UI_but_flag_enable(but, UI_BUT_ACTIVATE_ON_INIT);

  /* fake button, it holds space for search items */
  uiDefBut(block,
           UI_BTYPE_LABEL,
           0,
           "",
           10,
           10 - UI_searchbox_size_y(),
           UI_searchbox_size_x(),
           UI_searchbox_size_y(),
           NULL,
           0,
           0,
           0,
           0,
           NULL);

  /* Move it downwards, mouse over button. */
  UI_block_bounds_set_popup(block, 0.3f * U.widget_unit, (const int[2]){0, -UI_UNIT_Y});

  return block;
}

static int node_find_node_invoke(bContext *C, wmOperator *op, const wmEvent *UNUSED(event))
{
  UI_popup_block_invoke(C, node_find_menu, op, NULL);
  return OPERATOR_CANCELLED;
}

void NODE_OT_find_node(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Find Node";
  ot->description = "Search for named node and allow to select and activate it";
  ot->idname = "NODE_OT_find_node";

  /* api callbacks */
  ot->invoke = node_find_node_invoke;
  ot->poll = ED_operator_node_active;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna, "prev", 0, "Previous", "");
}

/** \} */
