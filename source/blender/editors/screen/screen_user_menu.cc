/* SPDX-FileCopyrightText: 2009 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup spview3d
 */

#include <cfloat>
#include <cstring>

#include "MEM_guardedalloc.h"

#include "BLI_listbase.h"
#include "BLI_string_utf8.h"
#include "BLI_utildefines.h"

#include "BLT_translation.hh"

#include "BKE_blender_user_menu.hh"
#include "BKE_context.hh"
#include "BKE_idprop.hh"
#include "BKE_screen.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "ED_screen.hh"

#include "UI_interface.hh"
#include "UI_interface_c.hh"
#include "UI_interface_layout.hh"
#include "UI_resources.hh"

#include "RNA_access.hh"
#include "RNA_define.hh"
#include "RNA_path.hh"
#include "RNA_prototypes.hh"

namespace blender {

using namespace ui;

/* -------------------------------------------------------------------- */
/** \name Internal Utilities
 * \{ */

static const char *screen_menu_context_string(const bContext *C, const SpaceLink *sl)
{
  if (sl->spacetype == SPACE_NODE) {
    const SpaceNode *snode = reinterpret_cast<const SpaceNode *>(sl);
    return snode->tree_idname;
  }
  return CTX_data_mode_string(C);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Menu Type
 * \{ */

bUserMenu **ED_screen_user_menus_find(const bContext *C, uint *r_len)
{
  SpaceLink *sl = CTX_wm_space_data(C);

  if (sl == nullptr) {
    *r_len = 0;
    return nullptr;
  }

  /* Return the global menu for all operations - filtering happens during display. */
  uint array_len = 1;
  bUserMenu **um_array = MEM_new_array_zeroed<bUserMenu *>(array_len, __func__);
  um_array[0] = BKE_blender_user_menu_find(&U.user_menus, SPACE_VIEW3D, "");

  *r_len = array_len;
  return um_array;
}

bUserMenu *ED_screen_user_menu_ensure(bContext *C)
{
  SpaceLink *sl = CTX_wm_space_data(C);
  const char *context = screen_menu_context_string(C, sl);
  
  /* Store all items in a global menu but track their original context. */
  bUserMenu *global_menu = BKE_blender_user_menu_ensure(&U.user_menus, SPACE_VIEW3D, "");
  
  /* Find existing menu to migrate items from context-specific storage. */
  bUserMenu *old_menu = BKE_blender_user_menu_find(&U.user_menus, sl->spacetype, context);
  if (old_menu && old_menu != global_menu) {
    /* Move items from old menu to global menu. */
    while (bUserMenuItem *umi = reinterpret_cast<bUserMenuItem *>(BLI_pophead(&old_menu->items))) {
      /* Store original context in the item. */
      umi->space_type = sl->spacetype;
      STRNCPY_UTF8(umi->context, context);
      BLI_addtail(&global_menu->items, umi);
    }
  }
  
  return global_menu;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Menu Item
 * \{ */

bUserMenuItem_Op *ED_screen_user_menu_item_find_operator(ListBaseT<bUserMenuItem> *lb,
                                                         const wmOperatorType *ot,
                                                         IDProperty *prop,
                                                         const char *op_prop_enum,
                                                         wm::OpCallContext opcontext)
{
  for (bUserMenuItem &umi : *lb) {
    if (umi.type == USER_MENU_TYPE_OPERATOR) {
      bUserMenuItem_Op *umi_op = reinterpret_cast<bUserMenuItem_Op *>(&umi);
      const bool ok_idprop = IDP_EqualsProperties_ex(prop, umi_op->prop, false);
      const bool ok_prop_enum = (umi_op->op_prop_enum[0] != '\0') ?
                                    STREQ(umi_op->op_prop_enum, op_prop_enum) :
                                    true;
      if (STREQ(ot->idname, umi_op->op_idname) &&
          (opcontext == wm::OpCallContext(umi_op->opcontext)) && ok_idprop && ok_prop_enum)
      {
        return umi_op;
      }
    }
  }
  return nullptr;
}

bUserMenuItem_Menu *ED_screen_user_menu_item_find_menu(ListBaseT<bUserMenuItem> *lb,
                                                       const MenuType *mt)
{
  for (bUserMenuItem &umi : *lb) {
    if (umi.type == USER_MENU_TYPE_MENU) {
      bUserMenuItem_Menu *umi_mt = reinterpret_cast<bUserMenuItem_Menu *>(&umi);
      if (STREQ(mt->idname, umi_mt->mt_idname)) {
        return umi_mt;
      }
    }
  }
  return nullptr;
}

bUserMenuItem_Prop *ED_screen_user_menu_item_find_prop(ListBaseT<bUserMenuItem> *lb,
                                                       const char *context_data_path,
                                                       const char *prop_id,
                                                       int prop_index)
{
  for (bUserMenuItem &umi : *lb) {
    if (umi.type == USER_MENU_TYPE_PROP) {
      bUserMenuItem_Prop *umi_pr = reinterpret_cast<bUserMenuItem_Prop *>(&umi);
      if (STREQ(context_data_path, umi_pr->context_data_path) && STREQ(prop_id, umi_pr->prop_id) &&
          (prop_index == umi_pr->prop_index))
      {
        return umi_pr;
      }
    }
  }
  return nullptr;
}

/* BFA: Quick Favorites - Add operator item with context-aware filtering */
void ED_screen_user_menu_item_add_operator(const bContext *C,
                                           ListBaseT<bUserMenuItem> *lb,
                                           const char *ui_name,
                                           const wmOperatorType *ot,
                                           const IDProperty *prop,
                                           const char *op_prop_enum,
                                           wm::OpCallContext opcontext,
                                           int icon)
{
  bUserMenuItem_Op *umi_op = reinterpret_cast<bUserMenuItem_Op *>(
      BKE_blender_user_menu_item_add(lb, USER_MENU_TYPE_OPERATOR));
  umi_op->opcontext = int8_t(opcontext);
  if (!STREQ(ui_name, ot->name)) {
    STRNCPY_UTF8(umi_op->item.ui_name, ui_name);
  }
  STRNCPY_UTF8(umi_op->op_idname, ot->idname);
  STRNCPY_UTF8(umi_op->op_prop_enum, op_prop_enum);
  umi_op->prop = prop ? IDP_CopyProperty(prop) : nullptr;
  umi_op->icon = icon;
  
  /* Set context information from the current context */
  SpaceLink *sl = CTX_wm_space_data(C);
  if (sl) {
    /* Always try to get the context from the active area, not from space_data */
    ScrArea *area = CTX_wm_area(C);
    if (area && area->spacetype != SPACE_TOPBAR) {
      /* Get the actual active editor context */
      sl = static_cast<SpaceLink *>(area->spacedata.first);
    }
    
    umi_op->item.space_type = sl->spacetype;
    const char *context = screen_menu_context_string(C, sl);
    STRNCPY_UTF8(umi_op->item.context, context);
    
    /* Store the current mode for mode-specific filtering */
    umi_op->item.mode = CTX_data_mode_enum(C);
    
    } else {
    /* No space data available, keep default values */
  }
}

/* BFA: Quick Favorites - Add menu item with context-aware filtering */
void ED_screen_user_menu_item_add_menu(const bContext *C,
                                       ListBaseT<bUserMenuItem> *lb,
                                       const char *ui_name,
                                       const MenuType *mt,
                                       int icon)
{
  bUserMenuItem_Menu *umi_mt = reinterpret_cast<bUserMenuItem_Menu *>(
      BKE_blender_user_menu_item_add(lb, USER_MENU_TYPE_MENU));
  if (!STREQ(ui_name, mt->label)) {
    STRNCPY_UTF8(umi_mt->item.ui_name, ui_name);
  }
  STRNCPY_UTF8(umi_mt->mt_idname, mt->idname);
  umi_mt->icon = icon;
  
  /* Set context information from the current context */
  SpaceLink *sl = CTX_wm_space_data(C);
  if (sl) {
    /* Always try to get the context from the active area, not from space_data */
    ScrArea *area = CTX_wm_area(C);
    if (area && area->spacetype != SPACE_TOPBAR) {
      /* Get the actual active editor context */
      sl = static_cast<SpaceLink *>(area->spacedata.first);
    }
    
    umi_mt->item.space_type = sl->spacetype;
    const char *context = screen_menu_context_string(C, sl);
    STRNCPY_UTF8(umi_mt->item.context, context);
    
    /* Store the current mode for mode-specific filtering */
    umi_mt->item.mode = CTX_data_mode_enum(C);
  }
}

/* BFA: Quick Favorites - Add property item with context-aware filtering */
void ED_screen_user_menu_item_add_prop(const bContext *C,
                                       ListBaseT<bUserMenuItem> *lb,
                                       const char *ui_name,
                                       const char *context_data_path,
                                       const char *prop_id,
                                       int prop_index,
                                       int icon)
{
  bUserMenuItem_Prop *umi_pr = reinterpret_cast<bUserMenuItem_Prop *>(
      BKE_blender_user_menu_item_add(lb, USER_MENU_TYPE_PROP));
  STRNCPY_UTF8(umi_pr->item.ui_name, ui_name);
  STRNCPY_UTF8(umi_pr->context_data_path, context_data_path);
  STRNCPY_UTF8(umi_pr->prop_id, prop_id);
  umi_pr->prop_index = prop_index;
  umi_pr->icon = icon;
  
  /* Set context information from the current context */
  SpaceLink *sl = CTX_wm_space_data(C);
  if (sl) {
    /* Always try to get the context from the active area, not from space_data */
    ScrArea *area = CTX_wm_area(C);
    if (area && area->spacetype != SPACE_TOPBAR) {
      /* Get the actual active editor context */
      sl = static_cast<SpaceLink *>(area->spacedata.first);
    }
    
    umi_pr->item.space_type = sl->spacetype;
    const char *context = screen_menu_context_string(C, sl);
    STRNCPY_UTF8(umi_pr->item.context, context);
    
    /* Store the current mode for mode-specific filtering */
    umi_pr->item.mode = CTX_data_mode_enum(C);
  }
}

void ED_screen_user_menu_item_remove(ListBaseT<bUserMenuItem> *lb, bUserMenuItem *umi)
{
  BLI_remlink(lb, umi);
  BKE_blender_user_menu_item_free(umi);
}

void ED_screen_user_menu_item_move_up(ListBaseT<bUserMenuItem> *lb, bUserMenuItem *umi)
{
  if (umi->prev) {
    BLI_listbase_swaplinks(lb, umi, umi->prev);
  }
}

void ED_screen_user_menu_item_move_down(ListBaseT<bUserMenuItem> *lb, bUserMenuItem *umi)
{
  if (umi->next) {
    BLI_listbase_swaplinks(lb, umi, umi->next);
  }
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Quick Favorites Editor Dialog
 * \{
 */

static void SCREEN_OT_user_menu_edit(wmOperatorType *ot);

/* Static variable to track selected item in the editor dialog.
 * This persists across operator calls within the dialog. */
static int g_user_menu_editor_selected_index = 0;

/* BFA: Quick Favorites - Context-aware edit menu with mode-specific filtering */
static void user_menu_edit_draw(bContext *C, wmOperator *op)
{
  uint um_array_len;
  bUserMenu **um_array = ED_screen_user_menus_find(C, &um_array_len);
  if (um_array == nullptr) {
    return;
  }

  /* Get current context for filtering */
  SpaceLink *sl = CTX_wm_space_data(C);
  char current_space_type = sl->spacetype;
  
  /* Find first user menu with items and count total items for button state calculation (filtered by context). */
  int total_items = 0;
  bUserMenu *first_um = nullptr;
  
  for (int um_index = 0; um_index < um_array_len; um_index++) {
    if (um_array[um_index]) {
      if (!first_um) {
        first_um = um_array[um_index];
      }
      /* Count only items that match current context */
      for (bUserMenuItem &umi : um_array[um_index]->items) {
        bool show_item = false;
        
        /* Show items from current space type AND mode */
        if (umi.space_type == current_space_type) {
          /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
          if (umi.mode == 0 || umi.mode == CTX_data_mode_enum(C) || umi.mode == 255) {
            show_item = true;
          }
        }
        /* Allow Topbar and Toolbar items to show in 3D View context */
        else if (current_space_type == SPACE_VIEW3D && 
                 (umi.space_type == SPACE_TOPBAR || umi.space_type == SPACE_TOOLBAR)) {
          /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
          if (umi.mode == 0 || umi.mode == CTX_data_mode_enum(C) || umi.mode == 255) {
            show_item = true;
          }
        }
        
        if (show_item) {
          total_items++;
        }
      }
    }
  }

  if (total_items == 0) {
    MEM_delete(um_array);
    ui::Layout *col = &op->layout->column(false);
    col->label(RPT_("No Quick Favorites items found."), ICON_INFO);
    col->label(RPT_("Right-click on buttons in menus to add them here."), ICON_NONE);
    return;
  }

  /* Get selected index from static variable (synced with operator property). */
  const int selected_index = g_user_menu_editor_selected_index;
  RNA_int_set(op->ptr, "selected_index", selected_index);
  const bool can_move_up = selected_index > 0;
  const bool can_move_down = selected_index < total_items - 1;
  const bool can_remove = selected_index >= 0 && selected_index < total_items;

  /* Main split layout - list on left, controls on right. */
  ui::Layout &main_row = op->layout->row(false);

  /* Left side - scrollable list of items. */
  ui::Layout &list_col = main_row.column(false);
  list_col.alignment_set(ui::LayoutAlign::Left);

  int current_index = 0;
  int last_space_type = -1;
  
  for (int um_index = 0; um_index < um_array_len; um_index++) {
    bUserMenu *um = um_array[um_index];
    if (um == nullptr) {
      continue;
    }

    for (bUserMenuItem &umi : um->items) {
      /* Apply context filtering */
      bool show_item = false;
      
      /* Show items from current space type AND mode */
      if (umi.space_type == current_space_type) {
        /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
        if (umi.mode == 0 || umi.mode == CTX_data_mode_enum(C) || umi.mode == 255) {
          show_item = true;
        }
      }
      /* Allow Topbar and Toolbar items to show in 3D View context */
      else if (current_space_type == SPACE_VIEW3D && 
               (umi.space_type == SPACE_TOPBAR || umi.space_type == SPACE_TOOLBAR)) {
        /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
        if (umi.mode == 0 || umi.mode == CTX_data_mode_enum(C) || umi.mode == 255) {
          show_item = true;
        }
      }
      
      if (!show_item) {
        continue;  /* Skip this item */
      }
      
      /* Add context header when space type changes. */
      if (umi.space_type != last_space_type) {
        if (last_space_type != -1) {
          list_col.separator();
        }
        const char *space_name = (umi.space_type == SPACE_TOPBAR) ? "Topbar" :
                               (umi.space_type == SPACE_VIEW3D) ? "3D View" :
                               (umi.space_type == SPACE_PROPERTIES) ? "Properties" :
                               (umi.space_type == SPACE_TOOLBAR) ? "Toolbar" :
                               "Other";
        list_col.label(space_name, ICON_NONE);
        last_space_type = umi.space_type;
      }
      
      const bool is_selected = (current_index == selected_index);

      /* Get display name and icon. */
      const char *name = umi.ui_name[0] ? umi.ui_name : nullptr;
      char label_buf[256] = {0};
      int icon = ICON_NONE;

      if (umi.type == USER_MENU_TYPE_OPERATOR) {
        bUserMenuItem_Op *umi_op = reinterpret_cast<bUserMenuItem_Op *>(&umi);
        if (wmOperatorType *ot = WM_operatortype_find(umi_op->op_idname, false)) {
          if (!name) {
            std::string op_name = WM_operatortype_name(ot, nullptr);
            SNPRINTF_UTF8(label_buf, "%s", op_name.c_str());
            name = label_buf;
          }
          icon = umi_op->icon;
        }
        else {
          SNPRINTF_UTF8(label_buf, RPT_("Missing: %s"), umi_op->op_idname);
          name = label_buf;
        }
      }
      else if (umi.type == USER_MENU_TYPE_MENU) {
        bUserMenuItem_Menu *umi_mt = reinterpret_cast<bUserMenuItem_Menu *>(&umi);
        MenuType *mt = WM_menutype_find(umi_mt->mt_idname, false);
        if (mt) {
          if (!name) {
            SNPRINTF_UTF8(label_buf, "%s", CTX_IFACE_(mt->translation_context, mt->label));
            name = label_buf;
          }
          icon = umi_mt->icon;
        }
        else {
          SNPRINTF_UTF8(label_buf, RPT_("Missing: %s"), umi_mt->mt_idname);
          name = label_buf;
        }
      }
      else if (umi.type == USER_MENU_TYPE_PROP) {
        bUserMenuItem_Prop *umi_pr = reinterpret_cast<bUserMenuItem_Prop *>(&umi);
        if (!name) {
          /* Try to resolve the property to get its actual name. */
          char *data_path = strchr(umi_pr->context_data_path, '.');
          if (data_path) {
            *data_path = '\0';
          }
          PointerRNA ptr = CTX_data_pointer_get(C, umi_pr->context_data_path);
          if (ptr.type == nullptr) {
            PointerRNA ctx_ptr = RNA_pointer_create_discrete(nullptr, RNA_Context, (void *)C);
            if (!RNA_path_resolve_full(&ctx_ptr, umi_pr->context_data_path, &ptr, nullptr, nullptr))
            {
              ptr.type = nullptr;
            }
          }
          if (data_path) {
            *data_path = '.';
            data_path += 1;
          }
          if (ptr.type != nullptr) {
            PointerRNA prop_ptr = ptr;
            if ((data_path == nullptr) ||
                RNA_path_resolve_full(&ptr, data_path, &prop_ptr, nullptr, nullptr))
            {
              PropertyRNA *prop = RNA_struct_find_property(&prop_ptr, umi_pr->prop_id);
              if (prop) {
                const char *prop_name = RNA_property_ui_name(prop);
                if (prop_name && prop_name[0]) {
                  SNPRINTF_UTF8(label_buf, "%s", prop_name);
                  name = label_buf;
                }
              }
            }
          }
          /* Fallback to raw path if we couldn't resolve. */
          if (!name) {
            SNPRINTF_UTF8(
                label_buf, RPT_("%s.%s"), umi_pr->context_data_path, umi_pr->prop_id);
            name = label_buf;
          }
        }
        icon = umi_pr->icon;
      }
      else if (umi.type == USER_MENU_TYPE_SEP) {
        name = "--- Separator ---";
        icon = ICON_NONE;
      }

      /* Selection row with radio button behavior. */
      ui::Layout &item_row = list_col.row(true);
      item_row.alignment_set(ui::LayoutAlign::Left);

      /* Selection indicator (filled circle if selected). */
      const int select_icon = is_selected ? ICON_CHECKBOX_HLT : ICON_CHECKBOX_DEHLT;
      ui::Layout &select_col = item_row.column(false);
      select_col.alignment_set(ui::LayoutAlign::Center);
      PointerRNA ptr_select = select_col.op("SCREEN_OT_user_menu_item_select",
                                           "",
                                           select_icon,
                                           wm::OpCallContext::InvokeDefault,
                                           UI_ITEM_NONE);
      RNA_int_set(&ptr_select, "index", current_index);

      /* Item label with icon - use separate column for name to allow truncation. */
      ui::Layout &name_col = item_row.column(false);
      name_col.alignment_set(ui::LayoutAlign::Left);
      name_col.label(name ? name : "", icon);

      current_index++;
    }
  }

  MEM_delete(um_array);

  /* Right side - control buttons column. */
  ui::Layout &control_col = main_row.column(true);
  control_col.alignment_set(ui::LayoutAlign::Right);

  /* Move Up button - wrapped in row to prevent expansion. */
  ui::Layout &up_row = control_col.row(false);
  up_row.alignment_set(ui::LayoutAlign::Right);
  if (can_move_up) {
    PointerRNA ptr_up = up_row.op("SCREEN_OT_user_menu_item_move",
                                 "",
                                 ICON_TRIA_UP,
                                 wm::OpCallContext::InvokeDefault,
                                 ITEM_R_ICON_ONLY);
    RNA_enum_set(&ptr_up, "direction", 0);
    RNA_int_set(&ptr_up, "index", selected_index);
  }
  else {
    up_row.label("", ICON_BLANK1);
  }

  /* Move Down button - wrapped in row to prevent expansion. */
  ui::Layout &down_row = control_col.row(false);
  down_row.alignment_set(ui::LayoutAlign::Right);
  if (can_move_down) {
    PointerRNA ptr_down = down_row.op("SCREEN_OT_user_menu_item_move",
                                     "",
                                     ICON_TRIA_DOWN,
                                     wm::OpCallContext::InvokeDefault,
                                     ITEM_R_ICON_ONLY);
    RNA_enum_set(&ptr_down, "direction", 1);
    RNA_int_set(&ptr_down, "index", selected_index);
  }
  else {
    down_row.label("", ICON_BLANK1);
  }

  control_col.separator();

  /* Remove button - wrapped in row to prevent expansion. */
  ui::Layout &remove_row = control_col.row(false);
  remove_row.alignment_set(ui::LayoutAlign::Right);
  if (can_remove) {
    PointerRNA ptr_remove = remove_row.op("SCREEN_OT_user_menu_item_remove",
                                       "",
                                       ICON_X,
                                       wm::OpCallContext::InvokeDefault,
                                       ITEM_R_ICON_ONLY);
    RNA_int_set(&ptr_remove, "index", selected_index);
  }
}

static wmOperatorStatus user_menu_edit_exec(bContext * /*C*/, wmOperator * /*op*/)
{
  return OPERATOR_FINISHED;
}

static wmOperatorStatus user_menu_edit_invoke(bContext *C, wmOperator *op, const wmEvent * /*event*/)
{
  g_user_menu_editor_selected_index = 0;
  RNA_int_set(op->ptr, "selected_index", 0);
  return WM_operator_props_dialog_popup(C, op, 250, std::nullopt);
}

static void SCREEN_OT_user_menu_edit(wmOperatorType *ot)
{
  ot->name = "Edit Quick Favorites";
  ot->idname = "SCREEN_OT_user_menu_edit";
  ot->description = "Open editor to reorder and manage Quick Favorites items";

  ot->invoke = user_menu_edit_invoke;
  ot->exec = user_menu_edit_exec;
  ot->poll = ED_operator_screenactive;

  ot->flag = OPTYPE_UNDO;

  RNA_def_int(ot->srna,
              "selected_index",
              0,
              0,
              INT_MAX,
              "Selected Index",
              "Index of the currently selected item",
              0,
              INT_MAX);

  ot->ui = user_menu_edit_draw;
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Select Item Operator (for editor dialog)
 * \{
 */

static wmOperatorStatus user_menu_item_select_exec(bContext * /*C*/, wmOperator *op)
{
  const int index = RNA_int_get(op->ptr, "index");
  g_user_menu_editor_selected_index = index;
  return OPERATOR_FINISHED;
}

static void SCREEN_OT_user_menu_item_select(wmOperatorType *ot)
{
  ot->name = "Select Quick Favorites Item";
  ot->idname = "SCREEN_OT_user_menu_item_select";
  ot->description = "Select an item in the Quick Favorites editor";

  ot->exec = user_menu_item_select_exec;
  ot->poll = ED_operator_screenactive;

  ot->flag = OPTYPE_INTERNAL;

  RNA_def_int(ot->srna,
              "index",
              0,
              0,
              INT_MAX,
              "Index",
              "Index of the item to select",
              0,
              INT_MAX);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Remove Item Operator
 * \{
 */

/* BFA: Quick Favorites - Remove item with context-aware filtering */
static wmOperatorStatus user_menu_item_remove_exec(bContext *C, wmOperator *op)
{
  const int target_index = RNA_int_get(op->ptr, "index");

  /* Get current context for filtering */
  SpaceLink *sl = CTX_wm_space_data(C);
  char current_space_type = sl->spacetype;

  /* Use the global menu directly. */
  bUserMenu *global_menu = BKE_blender_user_menu_find(&U.user_menus, SPACE_VIEW3D, "");
  if (global_menu == nullptr) {
    return OPERATOR_CANCELLED;
  }

  /* Find the actual item at the filtered index and collect visible items */
  blender::Vector<bUserMenuItem *> visible_items;
  for (bUserMenuItem *umi = static_cast<bUserMenuItem *>(global_menu->items.first); umi;
       umi = static_cast<bUserMenuItem *>(umi->next))
  {
    /* Apply context filtering */
    bool show_item = false;
    
    /* Show items from current space type AND mode */
    if (umi->space_type == current_space_type) {
      /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
      if (umi->mode == 0 || umi->mode == CTX_data_mode_enum(C) || umi->mode == 255) {
        show_item = true;
      }
    }
    /* Allow Topbar and Toolbar items to show in 3D View context */
    else if (current_space_type == SPACE_VIEW3D && 
             (umi->space_type == SPACE_TOPBAR || umi->space_type == SPACE_TOOLBAR)) {
      /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
      if (umi->mode == 0 || umi->mode == CTX_data_mode_enum(C) || umi->mode == 255) {
        show_item = true;
      }
    }
    
    if (show_item) {
      visible_items.append(umi);
    }
  }

  if (target_index < 0 || target_index >= visible_items.size()) {
    return OPERATOR_CANCELLED;
  }

  bUserMenuItem *target_umi = visible_items[target_index];
  
  U.runtime.is_dirty = true;
  ED_screen_user_menu_item_remove(&global_menu->items, target_umi);

  /* Update: selected index after removal. */
  if (g_user_menu_editor_selected_index == target_index) {
    /* Removed: selected item - select: item at same position (now:: next item). */
    g_user_menu_editor_selected_index = (target_index > 0) ? target_index - 1 : 0;
  }
  else if (g_user_menu_editor_selected_index > target_index) {
    /* Removed: an item before selection - adjust index. */
    g_user_menu_editor_selected_index--;
  }

  return OPERATOR_FINISHED;
}

static void SCREEN_OT_user_menu_item_remove(wmOperatorType *ot)
{
  ot->name = "Remove Quick Favorites Item";
  ot->idname = "SCREEN_OT_user_menu_item_remove";
  ot->description = "Remove an item from Quick Favorites";

  ot->exec = user_menu_item_remove_exec;
  ot->poll = ED_operator_screenactive;

  ot->flag = OPTYPE_UNDO;

  RNA_def_int(ot->srna,
              "index",
              0,
              0,
              INT_MAX,
              "Index",
              "Index of the item to remove",
              0,
              INT_MAX);
}

/** \} */

/* -------------------------------------------------------------------- */
/** \name Menu Definition
 * \{ */

static void screen_user_menu_draw(const bContext *C, Menu *menu)
{
  /* Enable when we have the ability to edit menus. */
  const bool show_missing = false;
  char label[512];

  uint um_array_len;
  bUserMenu **um_array = ED_screen_user_menus_find(C, &um_array_len);
  bool is_empty = true;
  
  /* Get current context for filtering */
  SpaceLink *sl = CTX_wm_space_data(C);
  char current_space_type = sl->spacetype;
  
  for (int um_index = 0; um_index < um_array_len; um_index++) {
    bUserMenu *um = um_array[um_index];
    if (um == nullptr) {
      continue;
    }
    for (bUserMenuItem &umi : um->items) {
      /* Filter items based on current context - show only items that work in this context */
      bool show_item = false;
      
      /* Show items from current space type AND mode */
      if (umi.space_type == current_space_type) {
        /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
        if (umi.mode == 0 || umi.mode == CTX_data_mode_enum(C) || umi.mode == 255) {
          show_item = true;
        }
      }
      /* Allow Topbar and Toolbar items to show in 3D View context */
      else if (current_space_type == SPACE_VIEW3D && 
               (umi.space_type == SPACE_TOPBAR || umi.space_type == SPACE_TOOLBAR)) {
        /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
        if (umi.mode == 0 || umi.mode == CTX_data_mode_enum(C) || umi.mode == 255) {
          show_item = true;
        }
      }
      
      if (!show_item) {
        continue;  /* Skip this item */
      }
      std::optional<StringRefNull> ui_name = umi.ui_name[0] ?
                                                 std::make_optional<StringRefNull>(umi.ui_name) :
                                                 std::nullopt;
      if (umi.type == USER_MENU_TYPE_OPERATOR) {
        bUserMenuItem_Op *umi_op = reinterpret_cast<bUserMenuItem_Op *>(&umi);
        if (wmOperatorType *ot = WM_operatortype_find(umi_op->op_idname, false)) {
          if (ui_name) {
            ui_name = CTX_IFACE_(ot->translation_context, ui_name->c_str());
          }
          if (umi_op->op_prop_enum[0] == '\0') {
            PointerRNA ptr = menu->layout->op(
                ot, ui_name, umi_op->icon, wm::OpCallContext(umi_op->opcontext), UI_ITEM_NONE);
            if (umi_op->prop) {
              IDP_CopyPropertyContent(ptr.data_as<IDProperty>(), umi_op->prop);
            }
          }
          else {
            /* umi_op->prop could be used to set other properties but it's currently unsupported.
             */
            menu->layout->op_menu_enum(C, ot, umi_op->op_prop_enum, ui_name, umi_op->icon);
          }
          is_empty = false;
        }
        else {
          if (show_missing) {
            SNPRINTF_UTF8(label, RPT_("Missing: %s"), umi_op->op_idname);
            menu->layout->label(label, ICON_NONE);
          }
        }
      }
      else if (umi.type == USER_MENU_TYPE_MENU) {
        bUserMenuItem_Menu *umi_mt = reinterpret_cast<bUserMenuItem_Menu *>(&umi);
        MenuType *mt = WM_menutype_find(umi_mt->mt_idname, false);
        if (mt != nullptr) {
          menu->layout->menu(mt, ui_name, umi_mt->icon);
          is_empty = false;
        }
        else {
          if (show_missing) {
            SNPRINTF_UTF8(label, RPT_("Missing: %s"), umi_mt->mt_idname);
            menu->layout->label(label, ICON_NONE);
          }
        }
      }
      else if (umi.type == USER_MENU_TYPE_PROP) {
        bUserMenuItem_Prop *umi_pr = reinterpret_cast<bUserMenuItem_Prop *>(&umi);

        char *data_path = strchr(umi_pr->context_data_path, '.');
        if (data_path) {
          *data_path = '\0';
        }
        PointerRNA ptr = CTX_data_pointer_get(C, umi_pr->context_data_path);
        if (ptr.type == nullptr) {
          PointerRNA ctx_ptr = RNA_pointer_create_discrete(nullptr, RNA_Context, (void *)C);
          if (!RNA_path_resolve_full(&ctx_ptr, umi_pr->context_data_path, &ptr, nullptr, nullptr))
          {
            ptr.type = nullptr;
          }
        }
        if (data_path) {
          *data_path = '.';
          data_path += 1;
        }

        bool ok = false;
        if (ptr.type != nullptr) {
          PropertyRNA *prop = nullptr;
          PointerRNA prop_ptr = ptr;
          if ((data_path == nullptr) ||
              RNA_path_resolve_full(&ptr, data_path, &prop_ptr, nullptr, nullptr))
          {
            prop = RNA_struct_find_property(&prop_ptr, umi_pr->prop_id);
            if (prop) {
              ok = true;
              menu->layout->prop(
                  &prop_ptr, prop, umi_pr->prop_index, 0, UI_ITEM_NONE, ui_name, umi_pr->icon);
              is_empty = false;
            }
          }
        }
        if (!ok) {
          if (show_missing) {
            SNPRINTF_UTF8(
                label, RPT_("Missing: %s.%s"), umi_pr->context_data_path, umi_pr->prop_id);
            menu->layout->label(label, ICON_NONE);
          }
        }
      }
      else if (umi.type == USER_MENU_TYPE_SEP) {
        menu->layout->separator();
      }
    }
  }
  if (um_array) {
    MEM_delete(um_array);
  }

  if (is_empty) {
    menu->layout->label(RPT_("No menu items found"), ICON_NONE);
    menu->layout->label(RPT_("Right click on buttons to add them to this menu"), ICON_NONE);
  }
  else {
    /* Add Edit button at the bottom of the menu. */
    menu->layout->separator();
    menu->layout->op("SCREEN_OT_user_menu_edit",
                     IFACE_("Edit Quick Favorites..."),
                     ICON_LASTOPERATOR,
                     wm::OpCallContext::InvokeDefault,
                     UI_ITEM_NONE);
  }
}

/* -------------------------------------------------------------------- */
/** \name Move Item Operator
 * \{
 */

/* BFA: Quick Favorites - Move item with context-aware filtering */
static wmOperatorStatus user_menu_item_move_exec(bContext *C, wmOperator *op)
{
  const int direction = RNA_enum_get(op->ptr, "direction");
  const int target_index = RNA_int_get(op->ptr, "index");

  /* Get current context for filtering */
  SpaceLink *sl = CTX_wm_space_data(C);
  char current_space_type = sl->spacetype;

  /* Use the global menu directly. */
  bUserMenu *global_menu = BKE_blender_user_menu_find(&U.user_menus, SPACE_VIEW3D, "");
  if (global_menu == nullptr) {
    return OPERATOR_CANCELLED;
  }

  /* Find the actual item at the filtered index and collect visible items */
  blender::Vector<bUserMenuItem *> visible_items;
  
  for (bUserMenuItem *umi = static_cast<bUserMenuItem *>(global_menu->items.first); umi;
       umi = static_cast<bUserMenuItem *>(umi->next))
  {
    /* Apply context filtering */
    bool show_item = false;
    
    /* Show items from current space type AND mode */
    if (umi->space_type == current_space_type) {
      /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
      if (umi->mode == 0 || umi->mode == CTX_data_mode_enum(C) || umi->mode == 255) {
        show_item = true;
      }
    }
    /* Allow Topbar and Toolbar items to show in 3D View context */
    else if (current_space_type == SPACE_VIEW3D && 
             (umi->space_type == SPACE_TOPBAR || umi->space_type == SPACE_TOOLBAR)) {
      /* Check if modes match, or if item has no specific mode (0 or uninitialized) */
      if (umi->mode == 0 || umi->mode == CTX_data_mode_enum(C) || umi->mode == 255) {
        show_item = true;
      }
    }
    
    if (show_item) {
      visible_items.append(umi);
    }
  }

  if (target_index < 0 || target_index >= visible_items.size()) {
    return OPERATOR_CANCELLED;
  }

  bool moved = false;
  int new_index = target_index;
  bUserMenuItem *target_umi = visible_items[target_index];

  if (direction == 0) { /* Up */
    if (target_index > 0) {
      /* Swap the items in the global list */
      ED_screen_user_menu_item_move_up(&global_menu->items, target_umi);
      new_index = target_index - 1;
      moved = true;
    }
  }
  else { /* Down */
    if (target_index < visible_items.size() - 1) {
      /* Swap the items in the global list */
      ED_screen_user_menu_item_move_down(&global_menu->items, target_umi);
      new_index = target_index + 1;
      moved = true;
    }
  }

  if (!moved) {
    return OPERATOR_CANCELLED;
  }

  U.runtime.is_dirty = true;

  /* Update: selected_index to follow the moved item. */
  g_user_menu_editor_selected_index = new_index;

  return OPERATOR_FINISHED;
}

static void SCREEN_OT_user_menu_item_move(wmOperatorType *ot)
{
  static const EnumPropertyItem direction_items[] = {
      {0, "UP", 0, "Up", "Move item up"},
      {1, "DOWN", 0, "Down", "Move item down"},
      {0, nullptr, 0, nullptr, nullptr},
  };

  ot->name = "Move Quick Favorites Item";
  ot->idname = "SCREEN_OT_user_menu_item_move";
  ot->description = "Move an item in the Quick Favorites menu up or down";

  ot->exec = user_menu_item_move_exec;
  ot->poll = ED_operator_screenactive;

  ot->flag = OPTYPE_UNDO;

  RNA_def_enum(ot->srna, "direction", direction_items, 0, "Direction", "Direction to move");
  RNA_def_int(ot->srna,
              "index",
              0,
              0,
              INT_MAX,
              "Index",
              "Index of the item to move",
              0,
              INT_MAX);
}

/** \} */

void ED_screen_user_menu_register()
{
  MenuType *mt = MEM_new_zeroed<MenuType>(__func__);
  STRNCPY_UTF8(mt->idname, "SCREEN_MT_user_menu");
  STRNCPY_UTF8(mt->label, N_("Quick Favorites"));
  STRNCPY_UTF8(mt->translation_context, BLT_I18NCONTEXT_DEFAULT_BPYRNA);
  mt->draw = screen_user_menu_draw;
  WM_menutype_add(mt);

  WM_operatortype_append(SCREEN_OT_user_menu_item_move);
  WM_operatortype_append(SCREEN_OT_user_menu_item_remove);
  WM_operatortype_append(SCREEN_OT_user_menu_item_select);
  WM_operatortype_append(SCREEN_OT_user_menu_edit);
}

/** \} */

}  // namespace blender
