/* SPDX-FileCopyrightText: 2023 Blender Foundation
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edgreasepencil
 */

#include "BKE_context.h"
#include "BKE_grease_pencil.hh"

#include "DEG_depsgraph.h"

#include "ED_grease_pencil.h"

#include "RNA_access.h"
#include "RNA_define.h"

#include "WM_api.h"

namespace blender::ed::greasepencil {

static int grease_pencil_layer_add_exec(bContext *C, wmOperator *op)
{
  using namespace blender::bke::greasepencil;
  Object *object = CTX_data_active_object(C);
  GreasePencil &grease_pencil = *static_cast<GreasePencil *>(object->data);

  int new_layer_name_length;
  char *new_layer_name = RNA_string_get_alloc(
      op->ptr, "new_layer_name", nullptr, 0, &new_layer_name_length);

  if (grease_pencil.has_active_layer()) {
    LayerGroup &active_group = grease_pencil.get_active_layer()->parent_group();
    Layer &new_layer = grease_pencil.add_layer_after(
        active_group, grease_pencil.get_active_layer_for_write(), new_layer_name);
    grease_pencil.set_active_layer(&new_layer);
  }
  else {
    Layer &new_layer = grease_pencil.add_layer(new_layer_name);
    grease_pencil.set_active_layer(&new_layer);
  }

  MEM_SAFE_FREE(new_layer_name);

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);

  return OPERATOR_FINISHED;
}

static void GREASE_PENCIL_OT_layer_add(wmOperatorType *ot)
{
  PropertyRNA *prop;
  /* identifiers */
  ot->name = "Add New Layer";
  ot->idname = "GREASE_PENCIL_OT_layer_add";
  ot->description = "Add new a new Grease Pencil layer in the active object";

  /* callbacks */
  ot->exec = grease_pencil_layer_add_exec;
  ot->poll = active_grease_pencil_poll;

  prop = RNA_def_string(
      ot->srna, "new_layer_name", "GP_Layer", INT16_MAX, "Name", "Name of the new layer");
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

  grease_pencil.remove_layer(*grease_pencil.get_active_layer_for_write());

  DEG_id_tag_update(&grease_pencil.id, ID_RECALC_GEOMETRY);
  WM_event_add_notifier(C, NC_GEOM | ND_DATA, &grease_pencil);

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
  ot->poll = active_grease_pencil_poll;
}

}  // namespace blender::ed::greasepencil

void ED_operatortypes_grease_pencil_layers(void)
{
  using namespace blender::ed::greasepencil;
  WM_operatortype_append(GREASE_PENCIL_OT_layer_add);
  WM_operatortype_append(GREASE_PENCIL_OT_layer_remove);
}