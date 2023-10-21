/* SPDX-FileCopyrightText: 2008 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spnode
 */

#include "AS_asset_representation.hh"

#include "BLI_string.h"

#include "DNA_ID.h"
#include "DNA_gpencil_legacy_types.h"
#include "DNA_light_types.h"
#include "DNA_material_types.h"
#include "DNA_modifier_types.h"
#include "DNA_node_types.h"
#include "DNA_object_types.h"
#include "DNA_world_types.h"

#include "MEM_guardedalloc.h"

#include "BKE_asset.h"
#include "BKE_compute_contexts.hh"
#include "BKE_context.h"
#include "BKE_gpencil_legacy.h"
#include "BKE_idprop.h"
#include "BKE_lib_id.h"
#include "BKE_lib_query.h"
#include "BKE_lib_remap.h"
#include "BKE_node.hh"
#include "BKE_node_runtime.hh"
#include "BKE_node_tree_zones.hh"
#include "BKE_screen.hh"

#include "ED_node.hh"
#include "ED_node_preview.hh"
#include "ED_render.hh"
#include "ED_screen.hh"
#include "ED_space_api.hh"

#include "UI_resources.hh"
#include "UI_view2d.hh"

#include "DEG_depsgraph.hh"

#include "BLO_read_write.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_enum_types.hh"
#include "RNA_prototypes.h"

#include "WM_api.hh"
#include "WM_types.hh"

#include "node_intern.hh" /* own include */

using blender::float2;

/* ******************** tree path ********************* */

void ED_node_tree_start(SpaceNode *snode, bNodeTree *ntree, ID *id, ID *from)
{
  LISTBASE_FOREACH_MUTABLE (bNodeTreePath *, path, &snode->treepath) {
    MEM_freeN(path);
  }
  BLI_listbase_clear(&snode->treepath);

  if (ntree) {
    bNodeTreePath *path = MEM_cnew<bNodeTreePath>("node tree path");
    path->nodetree = ntree;
    path->parent_key = NODE_INSTANCE_KEY_BASE;

    /* copy initial offset from bNodeTree */
    copy_v2_v2(path->view_center, ntree->view_center);

    if (id) {
      STRNCPY(path->display_name, id->name + 2);
    }

    BLI_addtail(&snode->treepath, path);

    if (ntree->type != NTREE_GEOMETRY) {
      /* This can probably be removed for all node tree types. It mainly exists because it was not
       * possible to store id references in custom properties. Also see #36024. I don't want to
       * remove it for all tree types in bcon3 though. */
      id_us_ensure_real(&ntree->id);
    }
  }

  /* update current tree */
  snode->nodetree = snode->edittree = ntree;
  snode->id = id;
  snode->from = from;

  ED_node_set_active_viewer_key(snode);

  WM_main_add_notifier(NC_SCENE | ND_NODES, nullptr);
}

void ED_node_tree_push(SpaceNode *snode, bNodeTree *ntree, bNode *gnode)
{
  bNodeTreePath *path = MEM_cnew<bNodeTreePath>("node tree path");
  bNodeTreePath *prev_path = (bNodeTreePath *)snode->treepath.last;
  path->nodetree = ntree;
  if (gnode) {
    if (prev_path) {
      path->parent_key = BKE_node_instance_key(prev_path->parent_key, prev_path->nodetree, gnode);
    }
    else {
      path->parent_key = NODE_INSTANCE_KEY_BASE;
    }

    STRNCPY(path->node_name, gnode->name);
    STRNCPY(path->display_name, gnode->name);
  }
  else {
    path->parent_key = NODE_INSTANCE_KEY_BASE;
  }

  /* copy initial offset from bNodeTree */
  copy_v2_v2(path->view_center, ntree->view_center);

  BLI_addtail(&snode->treepath, path);

  id_us_ensure_real(&ntree->id);

  /* update current tree */
  snode->edittree = ntree;

  ED_node_set_active_viewer_key(snode);

  WM_main_add_notifier(NC_SCENE | ND_NODES, nullptr);
}

void ED_node_tree_pop(SpaceNode *snode)
{
  bNodeTreePath *path = (bNodeTreePath *)snode->treepath.last;

  /* don't remove root */
  if (path == snode->treepath.first) {
    return;
  }

  BLI_remlink(&snode->treepath, path);
  MEM_freeN(path);

  /* update current tree */
  path = (bNodeTreePath *)snode->treepath.last;
  snode->edittree = path->nodetree;

  ED_node_set_active_viewer_key(snode);

  /* listener updates the View2D center from edittree */
  WM_main_add_notifier(NC_SCENE | ND_NODES, nullptr);
}

int ED_node_tree_depth(SpaceNode *snode)
{
  return BLI_listbase_count(&snode->treepath);
}

bNodeTree *ED_node_tree_get(SpaceNode *snode, int level)
{
  bNodeTreePath *path;
  int i;
  for (path = (bNodeTreePath *)snode->treepath.last, i = 0; path; path = path->prev, i++) {
    if (i == level) {
      return path->nodetree;
    }
  }
  return nullptr;
}

int ED_node_tree_path_length(SpaceNode *snode)
{
  int length = 0;
  int i = 0;
  LISTBASE_FOREACH_INDEX (bNodeTreePath *, path, &snode->treepath, i) {
    length += strlen(path->display_name);
    if (i > 0) {
      length += 1; /* for separator char */
    }
  }
  return length;
}

void ED_node_tree_path_get(SpaceNode *snode, char *value)
{
  int i = 0;
#ifndef NDEBUG
  const char *value_orig = value;
#endif
  /* Note that the caller ensures there is enough space available. */
  LISTBASE_FOREACH_INDEX (bNodeTreePath *, path, &snode->treepath, i) {
    const int len = strlen(path->display_name);
    if (i != 0) {
      *value++ = '/';
    }
    memcpy(value, path->display_name, len);
    value += len;
  }
  *value = '\0';
  BLI_assert(ptrdiff_t(ED_node_tree_path_length(snode)) == ptrdiff_t(value - value_orig));
}

void ED_node_set_active_viewer_key(SpaceNode *snode)
{
  bNodeTreePath *path = (bNodeTreePath *)snode->treepath.last;
  if (snode->nodetree && path) {
    /* A change in active viewer may result in the change of the output node used by the
     * compositor, so we need to get notified about such changes. */
    if (snode->nodetree->active_viewer_key.value != path->parent_key.value &&
        snode->nodetree->type == NTREE_COMPOSIT)
    {
      DEG_id_tag_update(&snode->nodetree->id, ID_RECALC_NTREE_OUTPUT);
      WM_main_add_notifier(NC_NODE, nullptr);
    }

    snode->nodetree->active_viewer_key = path->parent_key;
  }
}

void ED_node_cursor_location_get(const SpaceNode *snode, float value[2])
{
  copy_v2_v2(value, snode->runtime->cursor);
}

void ED_node_cursor_location_set(SpaceNode *snode, const float value[2])
{
  copy_v2_v2(snode->runtime->cursor, value);
}

namespace blender::ed::space_node {

float2 space_node_group_offset(const SpaceNode &snode)
{
  const bNodeTreePath *path = (bNodeTreePath *)snode.treepath.last;

  if (path && path->prev) {
    return float2(path->view_center) - float2(path->prev->view_center);
  }
  return float2(0);
}

static const bNode *group_node_by_name(const bNodeTree &ntree, StringRef name)
{
  for (const bNode *node : ntree.group_nodes()) {
    if (node->name == name) {
      return node;
    }
  }
  return nullptr;
}

std::optional<int32_t> find_nested_node_id_in_root(const SpaceNode &snode, const bNode &query_node)
{
  BLI_assert(snode.edittree->runtime->nodes_by_id.contains(const_cast<bNode *>(&query_node)));

  std::optional<int32_t> id_in_node;
  const char *group_node_name = nullptr;
  const bNode *node = &query_node;
  LISTBASE_FOREACH_BACKWARD (const bNodeTreePath *, path, &snode.treepath) {
    const bNodeTree *ntree = path->nodetree;
    if (group_node_name) {
      node = group_node_by_name(*ntree, group_node_name);
    }
    bool found = false;
    for (const bNestedNodeRef &ref : ntree->nested_node_refs_span()) {
      if (node->is_group()) {
        if (ref.path.node_id == node->identifier && ref.path.id_in_node == id_in_node) {
          group_node_name = path->node_name;
          id_in_node = ref.id;
          found = true;
          break;
        }
      }
      else if (ref.path.node_id == node->identifier) {
        group_node_name = path->node_name;
        id_in_node = ref.id;
        found = true;
        break;
      }
    }
    if (!found) {
      return std::nullopt;
    }
  }
  return id_in_node;
}

std::optional<ObjectAndModifier> get_modifier_for_node_editor(const SpaceNode &snode)
{
  if (snode.id == nullptr) {
    return std::nullopt;
  }
  if (GS(snode.id->name) != ID_OB) {
    return std::nullopt;
  }
  const Object *object = reinterpret_cast<Object *>(snode.id);
  const NodesModifierData *used_modifier = nullptr;
  if (snode.flag & SNODE_PIN) {
    LISTBASE_FOREACH (const ModifierData *, md, &object->modifiers) {
      if (md->type == eModifierType_Nodes) {
        const NodesModifierData *nmd = reinterpret_cast<const NodesModifierData *>(md);
        /* Would be good to store the name of the pinned modifier in the node editor. */
        if (nmd->node_group == snode.nodetree) {
          used_modifier = nmd;
          break;
        }
      }
    }
  }
  else {
    LISTBASE_FOREACH (const ModifierData *, md, &object->modifiers) {
      if (md->type == eModifierType_Nodes) {
        const NodesModifierData *nmd = reinterpret_cast<const NodesModifierData *>(md);
        if (nmd->node_group == snode.nodetree) {
          if (md->flag & eModifierFlag_Active) {
            used_modifier = nmd;
            break;
          }
        }
      }
    }
  }
  if (used_modifier == nullptr) {
    return std::nullopt;
  }
  return ObjectAndModifier{object, used_modifier};
}

bool push_compute_context_for_tree_path(const SpaceNode &snode,
                                        ComputeContextBuilder &compute_context_builder)
{
  Vector<const bNodeTreePath *> tree_path;
  LISTBASE_FOREACH (const bNodeTreePath *, item, &snode.treepath) {
    tree_path.append(item);
  }
  if (tree_path.is_empty()) {
    return true;
  }

  for (const int i : tree_path.index_range().drop_back(1)) {
    bNodeTree *tree = tree_path[i]->nodetree;
    const char *group_node_name = tree_path[i + 1]->node_name;
    const bNode *group_node = nodeFindNodebyName(tree, group_node_name);
    if (group_node == nullptr) {
      return false;
    }
    const bke::bNodeTreeZones *tree_zones = tree->zones();
    if (tree_zones == nullptr) {
      return false;
    }
    const Vector<const bke::bNodeTreeZone *> zone_stack = tree_zones->get_zone_stack_for_node(
        group_node->identifier);
    for (const bke::bNodeTreeZone *zone : zone_stack) {
      switch (zone->output_node->type) {
        case GEO_NODE_SIMULATION_OUTPUT: {
          compute_context_builder.push<bke::SimulationZoneComputeContext>(*zone->output_node);
          break;
        }
        case GEO_NODE_REPEAT_OUTPUT: {
          const auto &storage = *static_cast<const NodeGeometryRepeatOutput *>(
              zone->output_node->storage);
          compute_context_builder.push<bke::RepeatZoneComputeContext>(*zone->output_node,
                                                                      storage.inspection_index);
          break;
        }
      }
    }
    compute_context_builder.push<bke::NodeGroupComputeContext>(*group_node);
  }
  return true;
}

/* ******************** default callbacks for node space ***************** */

static SpaceLink *node_create(const ScrArea * /*area*/, const Scene * /*scene*/)
{
  SpaceNode *snode = MEM_cnew<SpaceNode>("initnode");
  snode->spacetype = SPACE_NODE;

  snode->flag = SNODE_SHOW_GPENCIL | SNODE_USE_ALPHA;
  snode->overlay.flag = (SN_OVERLAY_SHOW_OVERLAYS | SN_OVERLAY_SHOW_WIRE_COLORS |
                         SN_OVERLAY_SHOW_PATH | SN_OVERLAY_SHOW_PREVIEWS);

  /* backdrop */
  snode->zoom = 1.0f;

  /* select the first tree type for valid type */
  NODE_TREE_TYPES_BEGIN (treetype) {
    STRNCPY(snode->tree_idname, treetype->idname);
    break;
  }
  NODE_TREE_TYPES_END;

  /* header */
  ARegion *region = MEM_cnew<ARegion>("header for node");

  BLI_addtail(&snode->regionbase, region);
  region->regiontype = RGN_TYPE_HEADER;
  region->alignment = (U.uiflag & USER_HEADER_BOTTOM) ? RGN_ALIGN_BOTTOM : RGN_ALIGN_TOP;

  /* buttons/list view */
  region = MEM_cnew<ARegion>("buttons for node");

  BLI_addtail(&snode->regionbase, region);
  region->regiontype = RGN_TYPE_UI;
  region->alignment = RGN_ALIGN_RIGHT;

  /* toolbar */
  region = MEM_cnew<ARegion>("node tools");

  BLI_addtail(&snode->regionbase, region);
  region->regiontype = RGN_TYPE_TOOLS;
  region->alignment = RGN_ALIGN_LEFT;

  region->flag = RGN_FLAG_HIDDEN;

  /* main region */
  region = MEM_cnew<ARegion>("main region for node");

  BLI_addtail(&snode->regionbase, region);
  region->regiontype = RGN_TYPE_WINDOW;

  region->v2d.tot.xmin = -12.8f * U.widget_unit;
  region->v2d.tot.ymin = -12.8f * U.widget_unit;
  region->v2d.tot.xmax = 38.4f * U.widget_unit;
  region->v2d.tot.ymax = 38.4f * U.widget_unit;

  region->v2d.cur = region->v2d.tot;

  region->v2d.min[0] = 1.0f;
  region->v2d.min[1] = 1.0f;

  region->v2d.max[0] = 32000.0f;
  region->v2d.max[1] = 32000.0f;

  region->v2d.minzoom = 0.05f;
  region->v2d.maxzoom = 2.31f;

  region->v2d.scroll = (V2D_SCROLL_RIGHT | V2D_SCROLL_BOTTOM);
  region->v2d.keepzoom = V2D_LIMITZOOM | V2D_KEEPASPECT;
  region->v2d.keeptot = 0;

  return (SpaceLink *)snode;
}

static void node_free(SpaceLink *sl)
{
  SpaceNode *snode = (SpaceNode *)sl;
  BLI_freelistN(&snode->treepath);
  MEM_delete(snode->runtime);
}

/* spacetype; init callback */
static void node_init(wmWindowManager * /*wm*/, ScrArea *area)
{
  SpaceNode *snode = (SpaceNode *)area->spacedata.first;

  if (snode->runtime == nullptr) {
    snode->runtime = MEM_new<SpaceNode_Runtime>(__func__);
  }
}

static void node_exit(wmWindowManager *wm, ScrArea *area)
{
  SpaceNode *snode = static_cast<SpaceNode *>(area->spacedata.first);

  if (snode->runtime) {
    free_previews(*wm, *snode);
  }
}

static bool any_node_uses_id(const bNodeTree *ntree, const ID *id)
{
  if (ELEM(nullptr, ntree, id)) {
    return false;
  }
  for (const bNode *node : ntree->all_nodes()) {
    if (node->id == id) {
      return true;
    }
  }
  return false;
}

/**
 * Tag the space to recalculate the compositing tree using auto-compositing pipeline.
 *
 * Will check the space to be using a compositing tree, and check whether auto-compositing
 * is enabled. If the checks do not pass then the function has no affect.
 */
static void node_area_tag_recalc_auto_compositing(SpaceNode *snode, ScrArea *area)
{
  if (!ED_node_is_compositor(snode)) {
    return;
  }

  if (snode->flag & SNODE_AUTO_RENDER) {
    snode->runtime->recalc_auto_compositing = true;
    ED_area_tag_refresh(area);
  }
}

/**
 * Tag the space to recalculate the current tree.
 *
 * For all node trees this will do `snode_set_context()` which takes care of setting an active
 * tree. This will be done in the area refresh callback.
 *
 * For compositor tree this will additionally start of the compositor job.
 */
static void node_area_tag_tree_recalc(SpaceNode *snode, ScrArea *area)
{
  if (ED_node_is_compositor(snode)) {
    snode->runtime->recalc_regular_compositing = true;
  }

  ED_area_tag_refresh(area);
}

static void node_area_listener(const wmSpaceTypeListenerParams *params)
{
  ScrArea *area = params->area;
  const wmNotifier *wmn = params->notifier;

  /* NOTE: #ED_area_tag_refresh will re-execute compositor. */
  SpaceNode *snode = (SpaceNode *)area->spacedata.first;
  /* shaderfrom is only used for new shading nodes, otherwise all shaders are from objects */
  short shader_type = snode->shaderfrom;

  /* preview renders */
  switch (wmn->category) {
    case NC_SCENE:
      switch (wmn->data) {
        case ND_NODES: {
          ARegion *region = BKE_area_find_region_type(area, RGN_TYPE_WINDOW);
          bNodeTreePath *path = (bNodeTreePath *)snode->treepath.last;
          /* shift view to node tree center */
          if (region && path) {
            UI_view2d_center_set(&region->v2d, path->view_center[0], path->view_center[1]);
          }

          node_area_tag_tree_recalc(snode, area);
          break;
        }
        case ND_FRAME:
          node_area_tag_tree_recalc(snode, area);
          break;
        case ND_COMPO_RESULT: {
          ED_area_tag_redraw(area);
          /* Backdrop image offset is calculated during compositing so gizmos need to be updated
           * afterwards. */
          const ARegion *region = BKE_area_find_region_type(area, RGN_TYPE_WINDOW);
          WM_gizmomap_tag_refresh(region->gizmo_map);
          break;
        }
        case ND_TRANSFORM_DONE:
          node_area_tag_recalc_auto_compositing(snode, area);
          break;
        case ND_LAYER_CONTENT:
          node_area_tag_tree_recalc(snode, area);
          break;
      }
      break;

    /* future: add ID checks? */
    case NC_MATERIAL:
      if (ED_node_is_shader(snode)) {
        if (wmn->data == ND_SHADING) {
          node_area_tag_tree_recalc(snode, area);
        }
        else if (wmn->data == ND_SHADING_DRAW) {
          node_area_tag_tree_recalc(snode, area);
        }
        else if (wmn->data == ND_SHADING_LINKS) {
          node_area_tag_tree_recalc(snode, area);
        }
      }
      break;
    case NC_TEXTURE:
      if (ED_node_is_shader(snode) || ED_node_is_texture(snode)) {
        if (wmn->data == ND_NODES) {
          node_area_tag_tree_recalc(snode, area);
        }
      }
      break;
    case NC_WORLD:
      if (ED_node_is_shader(snode) && shader_type == SNODE_SHADER_WORLD) {
        node_area_tag_tree_recalc(snode, area);
      }
      break;
    case NC_OBJECT:
      if (ED_node_is_shader(snode)) {
        if (wmn->data == ND_OB_SHADING) {
          node_area_tag_tree_recalc(snode, area);
        }
      }
      else if (ED_node_is_geometry(snode)) {
        /* Rather strict check: only redraw when the reference matches the current editor's ID. */
        if (wmn->data == ND_MODIFIER) {
          if (wmn->reference == snode->id || snode->id == nullptr) {
            node_area_tag_tree_recalc(snode, area);
          }
        }
      }
      break;
    case NC_SPACE:
      if (wmn->data == ND_SPACE_NODE) {
        node_area_tag_tree_recalc(snode, area);
      }
      else if (wmn->data == ND_SPACE_NODE_VIEW) {
        ED_area_tag_redraw(area);
      }
      break;
    case NC_NODE:
      if (wmn->action == NA_EDITED) {
        node_area_tag_tree_recalc(snode, area);
      }
      else if (wmn->action == NA_SELECTED) {
        ED_area_tag_redraw(area);
      }
      break;
    case NC_SCREEN:
      switch (wmn->data) {
        case ND_ANIMPLAY:
          node_area_tag_tree_recalc(snode, area);
          break;
      }
      break;
    case NC_MASK:
      if (wmn->action == NA_EDITED) {
        if (snode->nodetree && snode->nodetree->type == NTREE_COMPOSIT) {
          node_area_tag_tree_recalc(snode, area);
        }
      }
      break;

    case NC_IMAGE:
      if (wmn->action == NA_EDITED) {
        if (ED_node_is_compositor(snode)) {
          /* Without this check drawing on an image could become very slow when the compositor is
           * open. */
          if (any_node_uses_id(snode->nodetree, (ID *)wmn->reference)) {
            node_area_tag_tree_recalc(snode, area);
          }
        }
      }
      break;

    case NC_MOVIECLIP:
      if (wmn->action == NA_EDITED) {
        if (ED_node_is_compositor(snode)) {
          if (any_node_uses_id(snode->nodetree, (ID *)wmn->reference)) {
            node_area_tag_tree_recalc(snode, area);
          }
        }
      }
      break;

    case NC_LINESTYLE:
      if (ED_node_is_shader(snode) && shader_type == SNODE_SHADER_LINESTYLE) {
        node_area_tag_tree_recalc(snode, area);
      }
      break;
    case NC_WM:
      if (wmn->data == ND_UNDO) {
        node_area_tag_tree_recalc(snode, area);
      }
      break;
    case NC_GPENCIL:
      if (ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        ED_area_tag_redraw(area);
      }
      break;
  }
}

static void node_area_refresh(const bContext *C, ScrArea *area)
{
  /* default now: refresh node is starting preview */
  SpaceNode *snode = (SpaceNode *)area->spacedata.first;

  snode_set_context(*C);

  if (snode->nodetree) {
    if (snode->nodetree->type == NTREE_COMPOSIT) {
      Scene *scene = (Scene *)snode->id;
      if (scene->use_nodes) {
        /* recalc is set on 3d view changes for auto compo */
        if (snode->runtime->recalc_auto_compositing) {
          snode->runtime->recalc_auto_compositing = false;
          snode->runtime->recalc_regular_compositing = false;
          node_render_changed_exec((bContext *)C, nullptr);
        }
        else if (snode->runtime->recalc_regular_compositing) {
          snode->runtime->recalc_regular_compositing = false;
          ED_node_composite_job(C, snode->nodetree, scene);
        }
      }
    }
  }
}

static SpaceLink *node_duplicate(SpaceLink *sl)
{
  SpaceNode *snode = (SpaceNode *)sl;
  SpaceNode *snoden = (SpaceNode *)MEM_dupallocN(snode);

  BLI_duplicatelist(&snoden->treepath, &snode->treepath);

  snoden->runtime = nullptr;

  /* NOTE: no need to set node tree user counts,
   * the editor only keeps at least 1 (id_us_ensure_real),
   * which is already done by the original SpaceNode.
   */

  return (SpaceLink *)snoden;
}

/* add handlers, stuff you only do once or on area/region changes */
static void node_buttons_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  ED_region_panels_init(wm, region);

  keymap = WM_keymap_ensure(wm->defaultconf, "Node Generic", SPACE_NODE, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler(&region->handlers, keymap);
}

static void node_buttons_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}

/* add handlers, stuff you only do once or on area/region changes */
static void node_toolbar_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;

  ED_region_panels_init(wm, region);

  keymap = WM_keymap_ensure(wm->defaultconf, "Node Generic", SPACE_NODE, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler(&region->handlers, keymap);
}

static void node_toolbar_region_draw(const bContext *C, ARegion *region)
{
  ED_region_panels(C, region);
}

static void node_cursor(wmWindow *win, ScrArea *area, ARegion *region)
{
  SpaceNode *snode = (SpaceNode *)area->spacedata.first;

  /* convert mouse coordinates to v2d space */
  UI_view2d_region_to_view(&region->v2d,
                           win->eventstate->xy[0] - region->winrct.xmin,
                           win->eventstate->xy[1] - region->winrct.ymin,
                           &snode->runtime->cursor[0],
                           &snode->runtime->cursor[1]);

  /* here snode->runtime->cursor is used to detect the node edge for sizing */
  node_set_cursor(*win, *snode, snode->runtime->cursor);

  /* XXX snode->runtime->cursor is in placing new nodes space */
  snode->runtime->cursor[0] /= UI_SCALE_FAC;
  snode->runtime->cursor[1] /= UI_SCALE_FAC;
}

/* Initialize main region, setting handlers. */
static void node_main_region_init(wmWindowManager *wm, ARegion *region)
{
  wmKeyMap *keymap;
  ListBase *lb;

  UI_view2d_region_reinit(&region->v2d, V2D_COMMONVIEW_CUSTOM, region->winx, region->winy);

  /* own keymaps */
  keymap = WM_keymap_ensure(wm->defaultconf, "Node Generic", SPACE_NODE, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler(&region->handlers, keymap);

  keymap = WM_keymap_ensure(wm->defaultconf, "Node Editor", SPACE_NODE, RGN_TYPE_WINDOW);
  WM_event_add_keymap_handler_v2d_mask(&region->handlers, keymap);

  /* add drop boxes */
  lb = WM_dropboxmap_find("Node Editor", SPACE_NODE, RGN_TYPE_WINDOW);

  WM_event_add_dropbox_handler(&region->handlers, lb);

  /* The backdrop image gizmo needs to change together with the view. So always refresh gizmos on
   * region size changes. */
  WM_gizmomap_tag_refresh(region->gizmo_map);
}

static void node_main_region_draw(const bContext *C, ARegion *region)
{
  node_draw_space(*C, *region);
}

/* ************* dropboxes ************* */

static bool node_group_drop_poll(bContext *C, wmDrag *drag, const wmEvent * /*event*/)
{
  SpaceNode *snode = CTX_wm_space_node(C);

  if (snode->edittree == nullptr) {
    return false;
  }

  if (!WM_drag_is_ID_type(drag, ID_NT)) {
    return false;
  }

  if (drag->type == WM_DRAG_ID) {
    const bNodeTree *node_tree = reinterpret_cast<const bNodeTree *>(
        WM_drag_get_local_ID(drag, ID_NT));
    if (!node_tree) {
      return false;
    }
    return node_tree->type == snode->edittree->type;
  }

  if (drag->type == WM_DRAG_ASSET) {
    const wmDragAsset *asset_data = WM_drag_get_asset_data(drag, ID_NT);
    if (!asset_data) {
      return false;
    }
    const AssetMetaData *metadata = &asset_data->asset->get_metadata();
    const IDProperty *tree_type = BKE_asset_metadata_idprop_find(metadata, "type");
    if (!tree_type || IDP_Int(tree_type) != snode->edittree->type) {
      return false;
    }
  }

  return true;
}

static bool node_object_drop_poll(bContext *C, wmDrag *drag, const wmEvent * /*event*/)
{
  return WM_drag_is_ID_type(drag, ID_OB) && !UI_but_active_drop_name(C);
}

static bool node_collection_drop_poll(bContext *C, wmDrag *drag, const wmEvent * /*event*/)
{
  return WM_drag_is_ID_type(drag, ID_GR) && !UI_but_active_drop_name(C);
}

static bool node_ima_drop_poll(bContext * /*C*/, wmDrag *drag, const wmEvent * /*event*/)
{
  if (drag->type == WM_DRAG_PATH) {
    const eFileSel_File_Types file_type = static_cast<eFileSel_File_Types>(
        WM_drag_get_path_file_type(drag));
    return ELEM(file_type, 0, FILE_TYPE_IMAGE, FILE_TYPE_MOVIE);
  }
  return WM_drag_is_ID_type(drag, ID_IM);
}

static bool node_mask_drop_poll(bContext * /*C*/, wmDrag *drag, const wmEvent * /*event*/)
{
  return WM_drag_is_ID_type(drag, ID_MSK);
}

static bool node_material_drop_poll(bContext *C, wmDrag *drag, const wmEvent * /*event*/)
{
  return WM_drag_is_ID_type(drag, ID_MA) && !UI_but_active_drop_name(C);
}

static void node_group_drop_copy(bContext *C, wmDrag *drag, wmDropBox *drop)
{
  ID *id = WM_drag_get_local_ID_or_import_from_asset(C, drag, 0);

  RNA_int_set(drop->ptr, "session_uuid", int(id->session_uuid));

  RNA_boolean_set(drop->ptr, "show_datablock_in_node", (drag->type != WM_DRAG_ASSET));
}

static void node_id_drop_copy(bContext *C, wmDrag *drag, wmDropBox *drop)
{
  ID *id = WM_drag_get_local_ID_or_import_from_asset(C, drag, 0);

  RNA_int_set(drop->ptr, "session_uuid", int(id->session_uuid));
}

static void node_id_path_drop_copy(bContext *C, wmDrag *drag, wmDropBox *drop)
{
  ID *id = WM_drag_get_local_ID_or_import_from_asset(C, drag, 0);

  if (id) {
    RNA_int_set(drop->ptr, "session_uuid", int(id->session_uuid));
    RNA_struct_property_unset(drop->ptr, "filepath");
    return;
  }

  const char *path = WM_drag_get_path(drag);
  if (path) {
    RNA_string_set(drop->ptr, "filepath", path);
    RNA_struct_property_unset(drop->ptr, "name");
    return;
  }
}

/* this region dropbox definition */
static void node_dropboxes()
{
  ListBase *lb = WM_dropboxmap_find("Node Editor", SPACE_NODE, RGN_TYPE_WINDOW);

  WM_dropbox_add(lb,
                 "NODE_OT_add_object",
                 node_object_drop_poll,
                 node_id_drop_copy,
                 WM_drag_free_imported_drag_ID,
                 nullptr);
  WM_dropbox_add(lb,
                 "NODE_OT_add_collection",
                 node_collection_drop_poll,
                 node_id_drop_copy,
                 WM_drag_free_imported_drag_ID,
                 nullptr);
  WM_dropbox_add(lb,
                 "NODE_OT_add_group",
                 node_group_drop_poll,
                 node_group_drop_copy,
                 WM_drag_free_imported_drag_ID,
                 nullptr);
  WM_dropbox_add(lb,
                 "NODE_OT_add_file",
                 node_ima_drop_poll,
                 node_id_path_drop_copy,
                 WM_drag_free_imported_drag_ID,
                 nullptr);
  WM_dropbox_add(lb,
                 "NODE_OT_add_mask",
                 node_mask_drop_poll,
                 node_id_drop_copy,
                 WM_drag_free_imported_drag_ID,
                 nullptr);
  WM_dropbox_add(lb,
                 "NODE_OT_add_material",
                 node_material_drop_poll,
                 node_id_drop_copy,
                 WM_drag_free_imported_drag_ID,
                 nullptr);
}

/* ************* end drop *********** */

/* add handlers, stuff you only do once or on area/region changes */
static void node_header_region_init(wmWindowManager * /*wm*/, ARegion *region)
{
  ED_region_header_init(region);
}

static void node_header_region_draw(const bContext *C, ARegion *region)
{
  /* find and set the context */
  snode_set_context(*C);

  ED_region_header(C, region);
}

/* used for header + main region */
static void node_region_listener(const wmRegionListenerParams *params)
{
  ARegion *region = params->region;
  const wmNotifier *wmn = params->notifier;
  wmGizmoMap *gzmap = region->gizmo_map;

  /* context changes */
  switch (wmn->category) {
    case NC_SPACE:
      switch (wmn->data) {
        case ND_SPACE_NODE:
          ED_region_tag_redraw(region);
          break;
        case ND_SPACE_NODE_VIEW:
          WM_gizmomap_tag_refresh(gzmap);
          break;
      }
      break;
    case NC_SCREEN:
      if (wmn->data == ND_LAYOUTSET || wmn->action == NA_EDITED) {
        WM_gizmomap_tag_refresh(gzmap);
      }
      switch (wmn->data) {
        case ND_ANIMPLAY:
        case ND_LAYER:
          ED_region_tag_redraw(region);
          break;
      }
      break;
    case NC_WM:
      if (wmn->data == ND_JOB) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_SCENE:
      ED_region_tag_redraw(region);
      if (wmn->data == ND_RENDER_RESULT) {
        WM_gizmomap_tag_refresh(gzmap);
      }
      break;
    case NC_NODE:
      ED_region_tag_redraw(region);
      if (ELEM(wmn->action, NA_EDITED, NA_SELECTED)) {
        WM_gizmomap_tag_refresh(gzmap);
      }
      break;
    case NC_MATERIAL:
    case NC_TEXTURE:
    case NC_WORLD:
    case NC_LINESTYLE:
      ED_region_tag_redraw(region);
      break;
    case NC_OBJECT:
      if (wmn->data == ND_OB_SHADING) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_ID:
      if (ELEM(wmn->action, NA_RENAME, NA_EDITED)) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_GPENCIL:
      if (wmn->action == NA_EDITED) {
        ED_region_tag_redraw(region);
      }
      else if (wmn->data & ND_GPENCIL_EDITMODE) {
        ED_region_tag_redraw(region);
      }
      break;
    case NC_VIEWER_PATH:
      ED_region_tag_redraw(region);
      break;
  }
}

}  // namespace blender::ed::space_node

/* Outside of blender namespace to avoid Python documentation build error with `ctypes`. */
extern "C" {
const char *node_context_dir[] = {
    "selected_nodes", "active_node", "light", "material", "world", nullptr};
};

namespace blender::ed::space_node {

static int /*eContextResult*/ node_context(const bContext *C,
                                           const char *member,
                                           bContextDataResult *result)
{
  SpaceNode *snode = CTX_wm_space_node(C);

  if (CTX_data_dir(member)) {
    CTX_data_dir_set(result, node_context_dir);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "selected_nodes")) {
    if (snode->edittree) {
      for (bNode *node : snode->edittree->all_nodes()) {
        if (node->flag & NODE_SELECT) {
          CTX_data_list_add(result, &snode->edittree->id, &RNA_Node, node);
        }
      }
    }
    CTX_data_type_set(result, CTX_DATA_TYPE_COLLECTION);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "active_node")) {
    if (snode->edittree) {
      bNode *node = nodeGetActive(snode->edittree);
      CTX_data_pointer_set(result, &snode->edittree->id, &RNA_Node, node);
    }

    CTX_data_type_set(result, CTX_DATA_TYPE_POINTER);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "node_previews")) {
    if (snode->nodetree) {
      CTX_data_pointer_set(
          result, &snode->nodetree->id, &RNA_NodeInstanceHash, snode->nodetree->previews);
    }

    CTX_data_type_set(result, CTX_DATA_TYPE_POINTER);
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "material")) {
    if (snode->id && GS(snode->id->name) == ID_MA) {
      CTX_data_id_pointer_set(result, snode->id);
    }
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "light")) {
    if (snode->id && GS(snode->id->name) == ID_LA) {
      CTX_data_id_pointer_set(result, snode->id);
    }
    return CTX_RESULT_OK;
  }
  if (CTX_data_equals(member, "world")) {
    if (snode->id && GS(snode->id->name) == ID_WO) {
      CTX_data_id_pointer_set(result, snode->id);
    }
    return CTX_RESULT_OK;
  }

  return CTX_RESULT_MEMBER_NOT_FOUND;
}

static void node_widgets()
{
  /* Create the widget-map for the area here. */
  wmGizmoMapType_Params params{SPACE_NODE, RGN_TYPE_WINDOW};
  wmGizmoMapType *gzmap_type = WM_gizmomaptype_ensure(&params);
  WM_gizmogrouptype_append_and_link(gzmap_type, NODE_GGT_backdrop_transform);
  WM_gizmogrouptype_append_and_link(gzmap_type, NODE_GGT_backdrop_crop);
  WM_gizmogrouptype_append_and_link(gzmap_type, NODE_GGT_backdrop_sun_beams);
  WM_gizmogrouptype_append_and_link(gzmap_type, NODE_GGT_backdrop_corner_pin);
}

static void node_id_remap_cb(ID *old_id, ID *new_id, void *user_data)
{
  SpaceNode *snode = static_cast<SpaceNode *>(user_data);

  if (snode->id == old_id) {
    /* nasty DNA logic for SpaceNode:
     * ideally should be handled by editor code, but would be bad level call
     */
    BLI_freelistN(&snode->treepath);

    /* XXX Untested in case new_id != nullptr... */
    snode->id = new_id;
    snode->from = nullptr;
    snode->nodetree = nullptr;
    snode->edittree = nullptr;
  }
  else if (GS(old_id->name) == ID_OB) {
    if (snode->from == old_id) {
      if (new_id == nullptr) {
        snode->flag &= ~SNODE_PIN;
      }
      snode->from = new_id;
    }
  }
  else if (GS(old_id->name) == ID_GD_LEGACY) {
    if ((ID *)snode->gpd == old_id) {
      snode->gpd = (bGPdata *)new_id;
      id_us_min(old_id);
      id_us_plus(new_id);
    }
  }
  else if (GS(old_id->name) == ID_NT) {
    bNodeTreePath *path, *path_next;

    for (path = (bNodeTreePath *)snode->treepath.first; path; path = path->next) {
      if ((ID *)path->nodetree == old_id) {
        path->nodetree = (bNodeTree *)new_id;
        id_us_ensure_real(new_id);
      }
      if (path == snode->treepath.first) {
        /* first nodetree in path is same as snode->nodetree */
        snode->nodetree = path->nodetree;
      }
      if (path->nodetree == nullptr) {
        break;
      }
    }

    /* remaining path entries are invalid, remove */
    for (; path; path = path_next) {
      path_next = path->next;

      BLI_remlink(&snode->treepath, path);
      MEM_freeN(path);
    }

    /* edittree is just the last in the path,
     * set this directly since the path may have been shortened above */
    if (snode->treepath.last) {
      path = (bNodeTreePath *)snode->treepath.last;
      snode->edittree = path->nodetree;
    }
    else {
      snode->edittree = nullptr;
    }
  }
}

static void node_id_remap(ScrArea * /*area*/, SpaceLink *slink, const IDRemapper *mappings)
{
  /* Although we should be able to perform all the mappings in a single go this lead to issues when
   * running the python test cases. Somehow the nodetree/edittree weren't updated to the new
   * pointers that generated a SEGFAULT.
   *
   * To move forward we should perhaps remove snode->edittree and snode->nodetree as they are just
   * copies of pointers. All usages should be calling a function that will receive the appropriate
   * instance.
   *
   * We could also move a remap address at a time to use the IDRemapper as that should get closer
   * to cleaner code. See {D13615} for more information about this topic.
   */
  BKE_id_remapper_iter(mappings, node_id_remap_cb, slink);
}

static void node_foreach_id(SpaceLink *space_link, LibraryForeachIDData *data)
{
  SpaceNode *snode = reinterpret_cast<SpaceNode *>(space_link);
  const int data_flags = BKE_lib_query_foreachid_process_flags_get(data);
  const bool is_readonly = (data_flags & IDWALK_READONLY) != 0;
  const bool allow_pointer_access = (data_flags & IDWALK_NO_ORIG_POINTERS_ACCESS) == 0;
  bool is_embedded_nodetree = snode->id != nullptr && allow_pointer_access &&
                              ntreeFromID(snode->id) == snode->nodetree;

  BKE_LIB_FOREACHID_PROCESS_ID(data, snode->id, IDWALK_CB_NOP);
  BKE_LIB_FOREACHID_PROCESS_ID(data, snode->from, IDWALK_CB_NOP);

  bNodeTreePath *path = static_cast<bNodeTreePath *>(snode->treepath.first);
  BLI_assert(path == nullptr || path->nodetree == snode->nodetree);

  if (is_embedded_nodetree) {
    BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, snode->nodetree, IDWALK_CB_EMBEDDED_NOT_OWNING);
    if (path != nullptr) {
      BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, path->nodetree, IDWALK_CB_EMBEDDED_NOT_OWNING);
    }

    /* Embedded ID pointers are not remapped (besides exceptions), ensure it still matches
     * actual data. Note that `snode->id` was already processed (and therefore potentially
     * remapped) above. */
    if (!is_readonly) {
      snode->nodetree = (snode->id == nullptr) ? nullptr : ntreeFromID(snode->id);
      if (path != nullptr) {
        path->nodetree = snode->nodetree;
      }
    }
  }
  else {
    BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, snode->nodetree, IDWALK_CB_USER_ONE);
    if (path != nullptr) {
      BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, path->nodetree, IDWALK_CB_USER_ONE);
    }
  }

  BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, snode->geometry_nodes_tool_tree, IDWALK_CB_USER_ONE);

  /* Both `snode->id` and `snode->nodetree` have been remapped now, so their data can be
   * accessed. */
  BLI_assert(snode->id == nullptr || snode->nodetree == nullptr ||
             (snode->nodetree->id.flag & LIB_EMBEDDED_DATA) == 0 ||
             snode->nodetree == ntreeFromID(snode->id));

  /* This is mainly here for readfile case ('lib_link' process), as in such case there is no access
   * to original data allowed, so no way to know whether the SpaceNode nodetree pointer is an
   * embedded one or not. */
  if (!is_readonly && snode->id && !snode->nodetree) {
    is_embedded_nodetree = true;
    snode->nodetree = ntreeFromID(snode->id);
    if (path != nullptr) {
      path->nodetree = snode->nodetree;
    }
  }

  if (path != nullptr) {
    for (path = path->next; path != nullptr; path = path->next) {
      BLI_assert(path->nodetree != nullptr);
      if (allow_pointer_access) {
        BLI_assert((path->nodetree->id.flag & LIB_EMBEDDED_DATA) == 0);
      }

      BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, path->nodetree, IDWALK_CB_USER_ONE);

      if (path->nodetree == nullptr) {
        BLI_assert(!is_readonly);
        /* Remaining path entries are invalid, remove them. */
        for (bNodeTreePath *path_next; path; path = path_next) {
          path_next = path->next;
          BLI_remlink(&snode->treepath, path);
          MEM_freeN(path);
        }
        break;
      }
    }
  }
  BLI_assert(path == nullptr);

  if (!is_readonly) {
    /* `edittree` is just the last in the path, set this directly since the path may have
     * been shortened above. */
    if (snode->treepath.last != nullptr) {
      path = static_cast<bNodeTreePath *>(snode->treepath.last);
      snode->edittree = path->nodetree;
    }
    else {
      snode->edittree = nullptr;
    }
  }
  else {
    /* Only process this pointer in readonly case, otherwise could lead to a bad
     * double-remapping e.g. */
    if (is_embedded_nodetree && snode->edittree == snode->nodetree) {
      BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, snode->edittree, IDWALK_CB_EMBEDDED_NOT_OWNING);
    }
    else {
      BKE_LIB_FOREACHID_PROCESS_IDSUPER(data, snode->edittree, IDWALK_CB_NOP);
    }
  }
}

static int node_space_subtype_get(ScrArea *area)
{
  SpaceNode *snode = (SpaceNode *)area->spacedata.first;
  return rna_node_tree_idname_to_enum(snode->tree_idname);
}

static void node_space_subtype_set(ScrArea *area, int value)
{
  SpaceNode *snode = (SpaceNode *)area->spacedata.first;
  ED_node_set_tree_type(snode, rna_node_tree_type_from_enum(value));
}

static void node_space_subtype_item_extend(bContext *C, EnumPropertyItem **item, int *totitem)
{
  bool free;
  const EnumPropertyItem *item_src = RNA_enum_node_tree_types_itemf_impl(C, &free);
  RNA_enum_items_add(item, totitem, item_src);
  if (free) {
    MEM_freeN((void *)item_src);
  }
}

static void node_space_blend_read_data(BlendDataReader *reader, SpaceLink *sl)
{
  SpaceNode *snode = (SpaceNode *)sl;

  if (snode->gpd) {
    BLO_read_data_address(reader, &snode->gpd);
    BKE_gpencil_blend_read_data(reader, snode->gpd);
  }

  BLO_read_list(reader, &snode->treepath);
  snode->edittree = nullptr;
  snode->runtime = nullptr;
}

static void node_space_blend_write(BlendWriter *writer, SpaceLink *sl)
{
  SpaceNode *snode = (SpaceNode *)sl;
  BLO_write_struct(writer, SpaceNode, snode);

  LISTBASE_FOREACH (bNodeTreePath *, path, &snode->treepath) {
    BLO_write_struct(writer, bNodeTreePath, path);
  }
}

}  // namespace blender::ed::space_node

void ED_spacetype_node()
{
  using namespace blender::ed::space_node;

  SpaceType *st = MEM_cnew<SpaceType>("spacetype node");
  ARegionType *art;

  st->spaceid = SPACE_NODE;
  STRNCPY(st->name, "Node");

  st->create = node_create;
  st->free = node_free;
  st->init = node_init;
  st->exit = node_exit;
  st->duplicate = node_duplicate;
  st->operatortypes = node_operatortypes;
  st->keymap = node_keymap;
  st->listener = node_area_listener;
  st->refresh = node_area_refresh;
  st->context = node_context;
  st->dropboxes = node_dropboxes;
  st->gizmos = node_widgets;
  st->id_remap = node_id_remap;
  st->foreach_id = node_foreach_id;
  st->space_subtype_item_extend = node_space_subtype_item_extend;
  st->space_subtype_get = node_space_subtype_get;
  st->space_subtype_set = node_space_subtype_set;
  st->blend_read_data = node_space_blend_read_data;
  st->blend_read_after_liblink = nullptr;
  st->blend_write = node_space_blend_write;

  /* regions: main window */
  art = MEM_cnew<ARegionType>("spacetype node region");
  art->regionid = RGN_TYPE_WINDOW;
  art->init = node_main_region_init;
  art->draw = node_main_region_draw;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_GIZMO | ED_KEYMAP_TOOL | ED_KEYMAP_VIEW2D |
                    ED_KEYMAP_FRAMES | ED_KEYMAP_GPENCIL;
  art->listener = node_region_listener;
  art->cursor = node_cursor;
  art->event_cursor = true;
  art->clip_gizmo_events_by_ui = true;
  art->lock = 1;

  BLI_addhead(&st->regiontypes, art);

  /* regions: header */
  art = MEM_cnew<ARegionType>("spacetype node region");
  art->regionid = RGN_TYPE_HEADER;
  art->prefsizey = HEADERY;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_VIEW2D | ED_KEYMAP_FRAMES | ED_KEYMAP_HEADER;
  art->listener = node_region_listener;
  art->init = node_header_region_init;
  art->draw = node_header_region_draw;

  BLI_addhead(&st->regiontypes, art);

  /* regions: list-view/buttons */
  art = MEM_cnew<ARegionType>("spacetype node region");
  art->regionid = RGN_TYPE_UI;
  art->prefsizex = UI_SIDEBAR_PANEL_WIDTH;
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
  art->listener = node_region_listener;
  art->message_subscribe = ED_area_do_mgs_subscribe_for_tool_ui;
  art->init = node_buttons_region_init;
  art->draw = node_buttons_region_draw;
  BLI_addhead(&st->regiontypes, art);

  /* regions: toolbar */
  art = MEM_cnew<ARegionType>("spacetype view3d tools region");
  art->regionid = RGN_TYPE_TOOLS;
  art->prefsizex = int(UI_TOOLBAR_WIDTH);
  art->prefsizey = 50; /* XXX */
  art->keymapflag = ED_KEYMAP_UI | ED_KEYMAP_FRAMES;
  art->listener = node_region_listener;
  art->message_subscribe = ED_region_generic_tools_region_message_subscribe;
  art->snap_size = ED_region_generic_tools_region_snap_size;
  art->init = node_toolbar_region_init;
  art->draw = node_toolbar_region_draw;
  BLI_addhead(&st->regiontypes, art);

  WM_menutype_add(MEM_new<MenuType>(__func__, add_catalog_assets_menu_type()));
  WM_menutype_add(MEM_new<MenuType>(__func__, add_unassigned_assets_menu_type()));
  WM_menutype_add(MEM_new<MenuType>(__func__, add_root_catalogs_menu_type()));

  BKE_spacetype_register(st);
}
