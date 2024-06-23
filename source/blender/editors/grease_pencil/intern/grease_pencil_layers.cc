/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edgreasepencil
 */

#include "BKE_context.hh"
#include "BKE_grease_pencil.hh"
#include "BKE_report.hh"

#include "BLT_translation.hh"

#include "DEG_depsgraph.hh"

#include "ED_grease_pencil.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "UI_interface.hh"

#include "DNA_scene_types.h"

#include "WM_api.hh"

namespace blender::ed::greasepencil {

void select_layer_channel(GreasePencil &grease_pencil, bke::greasepencil::Layer *layer)
{
  using namespace blender::bke::greasepencil;

  if (layer != nullptr) {
    layer->set_selected(true);
  }

  if (grease_pencil.get_active_layer() != layer) {
    grease_pencil.set_active_layer(layer);
    WM_main_add_notifier(NC_GPENCIL | ND_DATA | NA_EDITED, &grease_pencil);
  }
}

static int grease_pencil_layer_add_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  Scene *scene = CTX_data_scene(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  int new_layer_name_length;
  char *new_layer_name = RNA_string_get_alloc(
      op->ptr, "new_layer_name", nullptr, 0, &new_layer_name_length);
  BLI_SCOPED_DEFER([&] { MEM_SAFE_FREE(new_layer_name); });
  Layer &new_layer = grease_pencil.add_layer(new_layer_name);

  if (grease_pencil.has_active_layer()) {
    grease_pencil.move_node_after(new_layer.as_node(),
                                  grease_pencil.get_active_layer()->as_node());
  }
  else if (grease_pencil.has_active_group()) {
    grease_pencil.move_node_into(new_layer.as_node(), *grease_pencil.get_active_group());
  }

  grease_pencil.set_active_layer(&new_layer);
  grease_pencil.insert_frame(new_layer, scene->r.cfra);

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);

  return OPERATOR_FINISHED;
}

static int grease_pencil_layer_add_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  return WM_operator_props_popup_confirm_ex(C,
                                            op,
                                            event,
                                            IFACE_("Add New Grease Pencil Layer"),
                                            CTX_IFACE_(BLT_I18NCONTEXT_OPERATOR_DEFAULT, "Add"));
}

static void GREASE_PENCIL_OT_layer_add(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Add New Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_add";
  ot->description = "Add a new Grease Pencil layer in the active object";

  /* callbacks */
  ot->invoke = grease_pencil_layer_add_invoke;
  ot->exec = grease_pencil_layer_add_exec;
  ot->poll = active_grease_pencil_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  PropertyRNA *prop = RNA_def_string(
      ot->srna, "new_layer_name", "Layer", INT16_MAX, "Name", "Name of the new layer");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
  ot->prop = prop;
}

static int grease_pencil_layer_remove_exec(bContext *C, wmOperator * /*op*/)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  if (!grease_pencil.has_active_layer()) {
    return OPERATOR_CANCELLED;
  }

  grease_pencil.remove_layer(*grease_pencil.get_active_layer());

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_remove(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Remove Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_remove";
  ot->description = "Remove the active Grease Pencil layer";

  /* callbacks */
  ot->exec = grease_pencil_layer_remove_exec;
  ot->poll = active_grease_pencil_layer_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static const EnumPropertyItem prop_layer_reorder_location[] = {
    {LAYER_REORDER_ABOVE, "ABOVE", 0, "Above", ""},
    {LAYER_REORDER_BELOW, "BELOW", 0, "Below", ""},
    {0, nullptr, 0, nullptr, nullptr},
};

static int grease_pencil_layer_reorder_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  if (!grease_pencil.has_active_layer()) {
    return OPERATOR_CANCELLED;
  }

  int target_layer_name_length;
  char *target_layer_name = RNA_string_get_alloc(
      op->ptr, "target_layer_name", nullptr, 0, &target_layer_name_length);
  const int reorder_location = RNA_enum_get(op->ptr, "location");

  TreeNode *target_node = grease_pencil.find_node_by_name(target_layer_name);
  if (!target_node || !target_node->is_layer()) {
    MEM_SAFE_FREE(target_layer_name);
    return OPERATOR_CANCELLED;
  }

  Layer &active_layer = *grease_pencil.get_active_layer();
  switch (reorder_location) {
    case LAYER_REORDER_ABOVE: {
      /* NOTE: The layers are stored from bottom to top, so inserting above (visually), means
       * inserting the link after the target. */
      grease_pencil.move_node_after(active_layer.as_node(), *target_node);
      break;
    }
    case LAYER_REORDER_BELOW: {
      /* NOTE: The layers are stored from bottom to top, so inserting below (visually), means
       * inserting the link before the target. */
      grease_pencil.move_node_before(active_layer.as_node(), *target_node);
      break;
    }
    default:
      BLI_assert_unreachable();
  }

  MEM_SAFE_FREE(target_layer_name);

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_reorder(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Reorder Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_reorder";
  ot->description = "Reorder the active Grease Pencil layer";

  /* callbacks */
  ot->exec = grease_pencil_layer_reorder_exec;
  ot->poll = active_grease_pencil_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  PropertyRNA *prop = RNA_def_string(ot->srna,
                                     "target_layer_name",
                                     "Layer",
                                     INT16_MAX,
                                     "Target Name",
                                     "Name of the target layer");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);

  RNA_def_enum(
      ot->srna, "location", prop_layer_reorder_location, LAYER_REORDER_ABOVE, "Location", "");
}

static int grease_pencil_layer_active_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);
  int layer_index = RNA_int_get(op->ptr, "layer");

  Layer &layer = *grease_pencil.layer(layer_index);
  if (grease_pencil.is_layer_active(&layer)) {
    return OPERATOR_CANCELLED;
  }
  grease_pencil.set_active_layer(&layer);

  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_active(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Set Active Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_active";
  ot->description = "Set the active Grease Pencil layer";

  /* callbacks */
  ot->exec = grease_pencil_layer_active_exec;
  ot->poll = active_grease_pencil_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  PropertyRNA *prop = RNA_def_int(
      ot->srna, "layer", 0, 0, INT_MAX, "Grease Pencil Layer", "", 0, INT_MAX);
  RNA_def_property_flag(prop, PROP_HIDDEN | PROP_SKIP_SAVE);
}

static int grease_pencil_layer_group_add_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  int new_layer_group_name_length;
  char *new_layer_group_name = RNA_string_get_alloc(
      op->ptr, "new_layer_group_name", nullptr, 0, &new_layer_group_name_length);

  LayerGroup &parent_group = [&]() -> LayerGroup & {
    if (grease_pencil.has_active_layer()) {
      return grease_pencil.get_active_layer()->parent_group();
    }
    return grease_pencil.root_group();
  }();

  LayerGroup &new_group = grease_pencil.add_layer_group(parent_group, new_layer_group_name);

  if (grease_pencil.has_active_layer()) {
    grease_pencil.move_node_after(new_group.as_node(),
                                  grease_pencil.get_active_layer()->as_node());
  }

  MEM_SAFE_FREE(new_layer_group_name);

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_group_add(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Add New Layer Group";
  ot->idname = "GREASE_PENCIL_OT_layer_group_add";
  ot->description = "Add a new Grease Pencil layer group in the active object";

  /* callbacks */
  ot->exec = grease_pencil_layer_group_add_exec;
  ot->poll = active_grease_pencil_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  PropertyRNA *prop = RNA_def_string(
      ot->srna, "new_layer_group_name", nullptr, INT16_MAX, "Name", "Name of the new layer group");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
  ot->prop = prop;
}

static int grease_pencil_layer_group_remove_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  const bool keep_children = RNA_boolean_get(op->ptr, "keep_children");
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  if (!grease_pencil.has_active_group()) {
    return OPERATOR_CANCELLED;
  }

  grease_pencil.remove_group(*grease_pencil.get_active_group(), keep_children);

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_group_remove(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Remove Layer Group";
  ot->idname = "GREASE_PENCIL_OT_layer_group_remove";
  ot->description = "Remove Grease Pencil layer group in the active object";

  /* callbacks */
  ot->exec = grease_pencil_layer_group_remove_exec;
  ot->poll = active_grease_pencil_poll;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna,
                  "keep_children",
                  false,
                  "Keep children nodes",
                  "Keep the children nodes of the group and only delete the group itself");
}

static int grease_pencil_layer_hide_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);
  const bool unselected = RNA_boolean_get(op->ptr, "unselected");

  if (!grease_pencil.has_active_layer()) {
    return OPERATOR_CANCELLED;
  }

  if (unselected) {
    /* hide unselected */
    for (Layer *layer : grease_pencil.layers_for_write()) {
      const bool is_active = grease_pencil.is_layer_active(layer);
      layer->set_visible(is_active);
    }
  }
  else {
    /* hide selected/active */
    Layer &active_layer = *grease_pencil.get_active_layer();
    active_layer.set_visible(false);
  }

  /* notifiers */
  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);
  WM_event_add_notifier(C, NC_GPENCIL | NA_EDITED, nullptr);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_hide(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Hide Layer(s)";
  ot->idname = "GREASE_PENCIL_OT_layer_hide";
  ot->description = "Hide selected/unselected Grease Pencil layers";

  /* callbacks */
  ot->exec = grease_pencil_layer_hide_exec;
  ot->poll = active_grease_pencil_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* props */
  PropertyRNA *prop = RNA_def_boolean(
      ot->srna, "unselected", false, "Unselected", "Hide unselected rather than selected layers");
  RNA_def_property_flag(prop, PROP_SKIP_SAVE);
  ot->prop = prop;
}

static int grease_pencil_layer_reveal_exec(bContext *C, wmOperator * /*op*/)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  if (!grease_pencil.has_active_layer()) {
    return OPERATOR_CANCELLED;
  }

  for (Layer *layer : grease_pencil.layers_for_write()) {
    layer->set_visible(true);
  }

  /* notifiers */
  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);
  WM_event_add_notifier(C, NC_GPENCIL | NA_EDITED, nullptr);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_reveal(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Show All Layers";
  ot->idname = "GREASE_PENCIL_OT_layer_reveal";
  ot->description = "Show all Grease Pencil layers";

  /* callbacks */
  ot->exec = grease_pencil_layer_reveal_exec;
  ot->poll = active_grease_pencil_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static int grease_pencil_layer_isolate_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);
  const int affect_visibility = RNA_boolean_get(op->ptr, "affect_visibility");
  bool isolate = false;

  for (const Layer *layer : grease_pencil.layers()) {
    if (grease_pencil.is_layer_active(layer)) {
      continue;
    }
    if ((affect_visibility && layer->is_visible()) || !layer->is_locked()) {
      isolate = true;
      break;
    }
  }

  for (Layer *layer : grease_pencil.layers_for_write()) {
    if (grease_pencil.is_layer_active(layer) || !isolate) {
      layer->set_locked(false);
      if (affect_visibility) {
        layer->set_visible(true);
      }
    }
    else {
      layer->set_locked(true);
      if (affect_visibility) {
        layer->set_visible(false);
      }
    }
  }

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);
  WM_event_add_notifier(C, NC_GPENCIL | NA_EDITED, nullptr);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_isolate(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Isolate Layers";
  ot->idname = "GREASE_PENCIL_OT_layer_isolate";
  ot->description = "Make only active layer visible/editable";

  /* callbacks */
  ot->exec = grease_pencil_layer_isolate_exec;
  ot->poll = active_grease_pencil_layer_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(
      ot->srna, "affect_visibility", false, "Affect Visibility", "Also affect the visibility");
}

static int grease_pencil_layer_lock_all_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);
  const bool lock_value = RNA_boolean_get(op->ptr, "lock");

  if (grease_pencil.layers().is_empty()) {
    return OPERATOR_CANCELLED;
  }

  for (Layer *layer : grease_pencil.layers_for_write()) {
    layer->set_locked(lock_value);
  }

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);
  WM_event_add_notifier(C, NC_GPENCIL | NA_EDITED, nullptr);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_lock_all(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Lock All Layers";
  ot->idname = "GREASE_PENCIL_OT_layer_lock_all";
  ot->description =
      "Lock all Grease Pencil layers to prevent them from being accidentally modified";

  /* callbacks */
  ot->exec = grease_pencil_layer_lock_all_exec;
  ot->poll = active_grease_pencil_layer_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(ot->srna, "lock", true, "Lock Value", "Lock/Unlock all layers");
}

static int grease_pencil_layer_duplicate_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);
  const bool empty_keyframes = RNA_boolean_get(op->ptr, "empty_keyframes");

  if (!grease_pencil.has_active_layer()) {
    BKE_reportf(op->reports, RPT_ERROR, "No active layer to duplicate");
    return OPERATOR_CANCELLED;
  }

  /* Duplicate layer. */
  Layer &active_layer = *grease_pencil.get_active_layer();
  Layer &new_layer = grease_pencil.duplicate_layer(active_layer);

  /* Clear source keyframes and recreate them with duplicated drawings. */
  new_layer.frames_for_write().clear();
  for (auto [frame_number, frame] : active_layer.frames().items()) {
    const int duration = active_layer.get_frame_duration_at(frame_number);

    Drawing *dst_drawing = grease_pencil.insert_frame(
        new_layer, frame_number, duration, eBezTriple_KeyframeType(frame.type));
    if (!empty_keyframes) {
      BLI_assert(dst_drawing != nullptr);
      /* TODO: This can fail (return `nullptr`) if the drawing is a drawing reference! */
      const Drawing &src_drawing = *grease_pencil.get_drawing_at(active_layer, frame_number);
      /* Duplicate the drawing. */
      *dst_drawing = src_drawing;
    }
  }

  grease_pencil.move_node_after(new_layer.as_node(), active_layer.as_node());
  grease_pencil.set_active_layer(&new_layer);

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, nullptr);
  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_duplicate(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Duplicate Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_duplicate";
  ot->description = "Make a copy of the active Grease Pencil layer";

  /* callbacks */
  ot->exec = grease_pencil_layer_duplicate_exec;
  ot->poll = active_grease_pencil_layer_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* properties */
  RNA_def_boolean(ot->srna, "empty_keyframes", false, "Empty Keyframes", "Add Empty Keyframes");
}

static int grease_pencil_layer_mask_add_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  if (!grease_pencil.has_active_layer()) {
    return OPERATOR_CANCELLED;
  }
  Layer &active_layer = *grease_pencil.get_active_layer();

  int mask_name_length;
  char *mask_name = RNA_string_get_alloc(op->ptr, "name", nullptr, 0, &mask_name_length);
  BLI_SCOPED_DEFER([&] { MEM_SAFE_FREE(mask_name); });

  if (TreeNode *node = grease_pencil.find_node_by_name(mask_name)) {
    if (grease_pencil.is_layer_active(&node->as_layer())) {
      BKE_report(op->reports, RPT_ERROR, "Cannot add active layer as mask");
      return OPERATOR_CANCELLED;
    }

    if (BLI_findstring(&active_layer.masks,
                       mask_name,
                       offsetof(GreasePencilLayerMask, layer_name)) != nullptr)
    {
      BKE_report(op->reports, RPT_ERROR, "Layer already added");
      return OPERATOR_CANCELLED;
    }

    LayerMask *new_mask = MEM_new<LayerMask>(__func__, mask_name);
    BLI_addtail(&active_layer.masks, reinterpret_cast<GreasePencilLayerMask *>(new_mask));
    /* Make the newly added mask active. */
    active_layer.active_mask_index = BLI_listbase_count(&active_layer.masks) - 1;
  }
  else {
    BKE_report(op->reports, RPT_ERROR, "Unable to find layer to add");
    return OPERATOR_CANCELLED;
  }

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_mask_add(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Add New Mask Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_mask_add";
  ot->description = "Add new layer as masking";

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* callbacks */
  ot->exec = grease_pencil_layer_mask_add_exec;
  ot->poll = active_grease_pencil_layer_poll;

  /* properties */
  RNA_def_string(ot->srna, "name", nullptr, 0, "Layer", "Name of the layer");
}

static int grease_pencil_layer_mask_remove_exec(bContext *C, wmOperator * /*op*/)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  if (!grease_pencil.has_active_layer()) {
    return OPERATOR_CANCELLED;
  }

  Layer &active_layer = *grease_pencil.get_active_layer();
  if (GreasePencilLayerMask *mask = reinterpret_cast<GreasePencilLayerMask *>(
          BLI_findlink(&active_layer.masks, active_layer.active_mask_index)))
  {
    BLI_remlink(&active_layer.masks, mask);
    MEM_delete(reinterpret_cast<LayerMask *>(mask));
    active_layer.active_mask_index = std::max(active_layer.active_mask_index - 1, 0);
  }
  else {
    return OPERATOR_CANCELLED;
  }

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_mask_remove(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Remove Mask Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_mask_remove";
  ot->description = "Remove Layer Mask";

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  /* callbacks */
  ot->exec = grease_pencil_layer_mask_remove_exec;
  ot->poll = active_grease_pencil_layer_poll;
}

enum class LayerMaskMoveDirection : int8_t { Up = -1, Down = 1 };

static int grease_pencil_layer_mask_reorder_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  if (!grease_pencil.has_active_layer()) {
    return OPERATOR_CANCELLED;
  }
  Layer &active_layer = *grease_pencil.get_active_layer();
  const int direction = RNA_enum_get(op->ptr, "direction");

  bool changed = false;
  if (GreasePencilLayerMask *mask = reinterpret_cast<GreasePencilLayerMask *>(
          BLI_findlink(&active_layer.masks, active_layer.active_mask_index)))
  {
    if (BLI_listbase_link_move(&active_layer.masks, mask, direction)) {
      active_layer.active_mask_index = std::max(active_layer.active_mask_index + direction, 0);
      changed = true;
    }
  }
  else {
    return OPERATOR_CANCELLED;
  }

  if (changed) {
    DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
    WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);
  }

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_mask_reorder(wmOperatorType *ot)
{
  static const EnumPropertyItem enum_direction[] = {
      {int(LayerMaskMoveDirection::Up), "UP", 0, "Up", ""},
      {int(LayerMaskMoveDirection::Down), "DOWN", 0, "Down", ""},
      {0, nullptr, 0, nullptr, nullptr},
  };

  /* identifiers */
  ot->name = "Reorder Grease Pencil Layer Mask";
  ot->idname = "GREASE_PENCIL_OT_layer_mask_reorder";
  ot->description = "Reorder the active Grease Pencil mask layer up/down in the list";

  /* api callbacks */
  ot->exec = grease_pencil_layer_mask_reorder_exec;
  ot->poll = active_grease_pencil_layer_poll;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  ot->prop = RNA_def_enum(ot->srna, "direction", enum_direction, 0, "Direction", "");
}

const EnumPropertyItem enum_layergroup_color_items[] = {
    {LAYERGROUP_COLOR_NONE, "NONE", ICON_X, "Set Default icon", ""},
    {LAYERGROUP_COLOR_01, "COLOR1", ICON_LAYERGROUP_COLOR_01, "Color tag 1", ""},
    {LAYERGROUP_COLOR_02, "COLOR2", ICON_LAYERGROUP_COLOR_02, "Color tag 2", ""},
    {LAYERGROUP_COLOR_03, "COLOR3", ICON_LAYERGROUP_COLOR_03, "Color tag 3", ""},
    {LAYERGROUP_COLOR_04, "COLOR4", ICON_LAYERGROUP_COLOR_04, "Color tag 4", ""},
    {LAYERGROUP_COLOR_05, "COLOR5", ICON_LAYERGROUP_COLOR_05, "Color tag 5", ""},
    {LAYERGROUP_COLOR_06, "COLOR6", ICON_LAYERGROUP_COLOR_06, "Color tag 6", ""},
    {LAYERGROUP_COLOR_07, "COLOR7", ICON_LAYERGROUP_COLOR_07, "Color tag 7", ""},
    {LAYERGROUP_COLOR_08, "COLOR8", ICON_LAYERGROUP_COLOR_08, "Color tag 8", ""},
    {0, NULL, 0, NULL, NULL},
};

static int grease_pencil_layer_group_color_tag_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  const int color_tag = RNA_enum_get(op->ptr, "color_tag");
  LayerGroup *active_group = grease_pencil.get_active_group();
  active_group->color_tag = color_tag;

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_group_color_tag(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Grease Pencil group color tag";
  ot->idname = "GREASE_PENCIL_OT_layer_group_color_tag";
  ot->description = "Change layer group icon";

  ot->exec = grease_pencil_layer_group_color_tag_exec;
  ot->poll = active_grease_pencil_poll;

  ot->prop = RNA_def_enum(ot->srna, "color_tag", enum_layergroup_color_items, 0, "color tag", "");
}

enum class DuplicateCopyMode {
  All = 0,
  Active,
};

static void duplicate_layer_and_frames(GreasePencil &dst_grease_pencil,
                                       const GreasePencil &src_grease_pencil,
                                       const blender::bke::greasepencil::Layer &src_layer,
                                       const DuplicateCopyMode copy_frame_mode,
                                       const int current_frame)
{
  using namespace blender::bke::greasepencil;
  Layer &dst_layer = dst_grease_pencil.duplicate_layer(src_layer);

  dst_layer.frames_for_write().clear();
  for (const auto [frame_number, frame] : src_layer.frames().items()) {
    if ((copy_frame_mode == DuplicateCopyMode::Active) &&
        (&frame != src_layer.frame_at(current_frame)))
    {
      continue;
    }
    const int duration = src_layer.get_frame_duration_at(frame_number);

    Drawing *dst_drawing = dst_grease_pencil.insert_frame(
        dst_layer, frame_number, duration, eBezTriple_KeyframeType(frame.type));
    if (dst_drawing != nullptr) {
      /* Duplicate drawing. */
      const Drawing &src_drawing = *src_grease_pencil.get_drawing_at(src_layer, frame_number);
      *dst_drawing = src_drawing;
    }
  }
}

static int grease_pencil_layer_duplicate_object_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *src_object = CTX_data_active_object(C);
  const Scene *scene = CTX_data_scene(C);
  const int current_frame = scene->r.cfra;
  const GreasePencil &src_grease_pencil = *static_cast<GreasePencil *>(src_object->data);
  const bool only_active = RNA_boolean_get(op->ptr, "only_active");
  const DuplicateCopyMode copy_frame_mode = DuplicateCopyMode(RNA_enum_get(op->ptr, "mode"));

  CTX_DATA_BEGIN (C, Object *, ob, selected_objects) {
    if (ob == src_object || ob->type != OB_GREASE_PENCIL) {
      continue;
    }
    GreasePencil &dst_grease_pencil = *static_cast<GreasePencil *>(ob->data);

    if (only_active) {
      const Layer &active_layer = *src_grease_pencil.get_active_layer();
      duplicate_layer_and_frames(
          dst_grease_pencil, src_grease_pencil, active_layer, copy_frame_mode, current_frame);
    }
    else {
      for (const Layer *layer : src_grease_pencil.layers()) {
        duplicate_layer_and_frames(
            dst_grease_pencil, src_grease_pencil, *layer, copy_frame_mode, current_frame);
      }
    }

    DEG_id_tag_update(&dst_grease_pencil.id, ID_RECALC_GEOMETRY);
    WM_event_add_notifier(C, NC_GPENCIL | ND_DATA | NA_SELECTED, nullptr);
  }
  CTX_DATA_END;

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_duplicate_object(wmOperatorType *ot)
{
  /* identifiers */
  ot->name = "Duplicate Layer to New Object";
  ot->idname = "GREASE_PENCIL_OT_layer_duplicate_object";
  ot->description = "Make a copy of the active Grease Pencil layer to selected object";

  /* api callbacks */
  ot->poll = active_grease_pencil_layer_poll;
  ot->exec = grease_pencil_layer_duplicate_object_exec;

  /* flags */
  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_boolean(ot->srna,
                  "only_active",
                  true,
                  "Only Active",
                  "Copy only active Layer, uncheck to append all layers");

  static const EnumPropertyItem copy_mode[] = {
      {int(DuplicateCopyMode::All), "ALL", 0, "All Frames", ""},
      {int(DuplicateCopyMode::Active), "ACTIVE", 0, "Active Frame", ""},
      {0, nullptr, 0, nullptr, nullptr},
  };

  ot->prop = RNA_def_enum(ot->srna, "mode", copy_mode, 0, "Mode", "");
}

}  // namespace blender::ed::greasepencil

void ED_operatortypes_grease_pencil_layers()
{
  using namespace blender::ed::greasepencil;
  WM_operatortype_append(GREASE_PENCIL_OT_layer_add);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_remove);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_reorder);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_active);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_hide);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_reveal);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_isolate);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_lock_all);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_duplicate);

  WM_operatortype_append(GREASE_PENCIL_OT_layer_group_add);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_group_remove);

  WM_operatortype_append(GREASE_PENCIL_OT_layer_mask_add);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_mask_remove);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_mask_reorder);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_group_color_tag);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_duplicate_object);
}
