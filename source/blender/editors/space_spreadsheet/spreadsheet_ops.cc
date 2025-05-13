/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include <fmt/format.h>

#include "DNA_space_types.h"

#include "ED_screen.hh"

#include "BLI_listbase.h"
#include "BLI_rect.h"

#include "BKE_context.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"

#include "UI_interface_c.hh"
#include "UI_view2d.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "spreadsheet_column.hh"
#include "spreadsheet_intern.hh"
#include "spreadsheet_row_filter.hh"

namespace blender::ed::spreadsheet {

static wmOperatorStatus row_filter_add_exec(bContext *C, wmOperator * /*op*/)
{
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);

  SpreadsheetRowFilter *row_filter = spreadsheet_row_filter_new();
  BLI_addtail(&sspreadsheet->row_filters, row_filter);

  WM_event_add_notifier(C, NC_SPACE | ND_SPACE_SPREADSHEET, sspreadsheet);

  return OPERATOR_FINISHED;
}

static void SPREADSHEET_OT_add_row_filter_rule(wmOperatorType *ot)
{
  ot->name = "Add Row Filter";
  ot->description = "Add a filter to remove rows from the displayed data";
  ot->idname = "SPREADSHEET_OT_add_row_filter_rule";

  ot->exec = row_filter_add_exec;
  ot->poll = ED_operator_spreadsheet_active;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;
}

static wmOperatorStatus row_filter_remove_exec(bContext *C, wmOperator *op)
{
  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);

  SpreadsheetRowFilter *row_filter = (SpreadsheetRowFilter *)BLI_findlink(
      &sspreadsheet->row_filters, RNA_int_get(op->ptr, "index"));
  if (row_filter == nullptr) {
    return OPERATOR_CANCELLED;
  }

  BLI_remlink(&sspreadsheet->row_filters, row_filter);
  spreadsheet_row_filter_free(row_filter);

  WM_event_add_notifier(C, NC_SPACE | ND_SPACE_SPREADSHEET, sspreadsheet);

  return OPERATOR_FINISHED;
}

static void SPREADSHEET_OT_remove_row_filter_rule(wmOperatorType *ot)
{
  ot->name = "Remove Row Filter";
  ot->description = "Remove a row filter from the rules";
  ot->idname = "SPREADSHEET_OT_remove_row_filter_rule";

  ot->exec = row_filter_remove_exec;
  ot->poll = ED_operator_spreadsheet_active;

  ot->flag = OPTYPE_REGISTER | OPTYPE_UNDO;

  RNA_def_int(ot->srna, "index", 0, 0, INT_MAX, "Index", "", 0, INT_MAX);
}

static wmOperatorStatus select_component_domain_invoke(bContext *C,
                                                       wmOperator *op,
                                                       const wmEvent * /*event*/)
{
  const auto component_type = bke::GeometryComponent::Type(RNA_int_get(op->ptr, "component_type"));
  bke::AttrDomain domain = bke::AttrDomain(RNA_int_get(op->ptr, "attribute_domain_type"));

  SpaceSpreadsheet *sspreadsheet = CTX_wm_space_spreadsheet(C);
  sspreadsheet->geometry_component_type = uint8_t(component_type);
  sspreadsheet->attribute_domain = uint8_t(domain);

  /* Refresh header and main region. */
  WM_main_add_notifier(NC_SPACE | ND_SPACE_SPREADSHEET, nullptr);

  return OPERATOR_FINISHED;
}

static void SPREADSHEET_OT_change_spreadsheet_data_source(wmOperatorType *ot)
{
  ot->name = "Change Visible Data Source";
  ot->description = "Change visible data source in the spreadsheet";
  ot->idname = "SPREADSHEET_OT_change_spreadsheet_data_source";

  ot->invoke = select_component_domain_invoke;
  ot->poll = ED_operator_spreadsheet_active;

  RNA_def_int(ot->srna, "component_type", 0, 0, INT16_MAX, "Component Type", "", 0, INT16_MAX);
  RNA_def_int(ot->srna,
              "attribute_domain_type",
              0,
              0,
              INT16_MAX,
              "Attribute Domain Type",
              "",
              0,
              INT16_MAX);

  ot->flag = OPTYPE_INTERNAL;
}

struct ResizeColumnData {
  SpreadsheetColumn *column = nullptr;
  int2 initial_cursor_re;
  int initial_width_px;
};

static wmOperatorStatus resize_column_modal(bContext *C, wmOperator *op, const wmEvent *event)
{
  ARegion &region = *CTX_wm_region(C);

  ResizeColumnData &data = *static_cast<ResizeColumnData *>(op->customdata);

  auto cancel = [&]() {
    data.column->width = data.initial_width_px / SPREADSHEET_WIDTH_UNIT;
    MEM_delete(&data);
    ED_region_tag_redraw(&region);
    return OPERATOR_CANCELLED;
  };
  auto finish = [&]() {
    MEM_delete(&data);
    ED_region_tag_redraw(&region);
    return OPERATOR_FINISHED;
  };

  const int2 cursor_re{event->mval[0], event->mval[1]};

  switch (event->type) {
    case RIGHTMOUSE:
    case EVT_ESCKEY: {
      return cancel();
    }
    case LEFTMOUSE: {
      return finish();
    }
    case MOUSEMOVE: {
      const int offset = cursor_re.x - data.initial_cursor_re.x;
      const float new_width_px = std::max<float>(SPREADSHEET_WIDTH_UNIT,
                                                 data.initial_width_px + offset);
      data.column->width = new_width_px / SPREADSHEET_WIDTH_UNIT;
      ED_region_tag_redraw(&region);
      return OPERATOR_RUNNING_MODAL;
    }
    default: {
      return OPERATOR_RUNNING_MODAL;
    }
  }
}

SpreadsheetColumn *find_column_to_resize(SpaceSpreadsheet &sspreadsheet,
                                         ARegion &region,
                                         const int2 &cursor_re)
{
  const int region_height = BLI_rcti_size_y(&region.winrct);
  if (cursor_re.y < region_height - sspreadsheet.runtime->top_row_height) {
    return nullptr;
  }
  const float cursor_x_view = UI_view2d_region_to_view_x(&region.v2d, cursor_re.x);
  LISTBASE_FOREACH (SpreadsheetColumn *, column, &sspreadsheet.columns) {
    if (std::abs(cursor_x_view - column->runtime->right_x) < SPREADSHEET_EDGE_ACTION_ZONE) {
      return column;
    }
  }
  return nullptr;
}

static wmOperatorStatus resize_column_invoke(bContext *C, wmOperator *op, const wmEvent *event)
{
  ARegion &region = *CTX_wm_region(C);
  SpaceSpreadsheet &sspreadsheet = *CTX_wm_space_spreadsheet(C);

  const int2 cursor_re{event->mval[0], event->mval[1]};
  SpreadsheetColumn *column_to_resize = find_column_to_resize(sspreadsheet, region, cursor_re);
  if (!column_to_resize) {
    return OPERATOR_PASS_THROUGH;
  }

  ResizeColumnData *data = MEM_new<ResizeColumnData>(__func__);
  data->column = column_to_resize;
  data->initial_cursor_re = cursor_re;
  data->initial_width_px = column_to_resize->width * SPREADSHEET_WIDTH_UNIT;
  op->customdata = data;

  WM_event_add_modal_handler(C, op);
  return OPERATOR_RUNNING_MODAL;
}

static void SPREADSHEET_OT_resize_column(wmOperatorType *ot)
{
  ot->name = "Resize Column";
  ot->description = "Resize a spreadsheet column";
  ot->idname = "SPREADSHEET_OT_resize_column";

  ot->invoke = resize_column_invoke;
  ot->modal = resize_column_modal;
  ot->poll = ED_operator_spreadsheet_active;
  ot->flag = OPTYPE_INTERNAL;
}

void spreadsheet_operatortypes()
{
  WM_operatortype_append(SPREADSHEET_OT_add_row_filter_rule);
  WM_operatortype_append(SPREADSHEET_OT_remove_row_filter_rule);
  WM_operatortype_append(SPREADSHEET_OT_change_spreadsheet_data_source);
  WM_operatortype_append(SPREADSHEET_OT_resize_column);
}

}  // namespace blender::ed::spreadsheet
