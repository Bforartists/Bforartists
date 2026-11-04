/* SPDX-FileCopyrightText: 2026 Bforartists Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup edinterface
 *
 * BFA - Tear-Off Menu/Panel: enum dropdowns and operator enum menus as tear-offs. An attached
 * dropdown depends on its source button, so a tear-off stores identifiers and resolves them on
 * every refresh and every click. No RNA pointer is kept between the two.
 */

#include <cstdint>
#include <memory>
#include <optional>
#include <string>

#include "DNA_ID.h"

#include "BLI_utildefines.hh"

#include "BLT_translation.hh"

#include "BKE_context.hh"
#include "BKE_idtype.hh"
#include "BKE_lib_id.hh"
#include "BKE_paint.hh"
#include "BKE_paint_types.hh"
#include "BKE_report.hh"
#include "BKE_scene.hh"

#include "ANIM_keyframing.hh"

#include "ED_undo.hh"

#include "RNA_access.hh"
#include "RNA_path.hh"
#include "RNA_prototypes.hh"

#include "UI_interface.hh"
#include "UI_interface_c.hh"
#include "UI_interface_layout.hh"
#include "UI_resources.hh"

#include "WM_api.hh"
#include "WM_types.hh"

#include "interface_intern.hh"

namespace blender::ui {

struct EnumTearOffSource {
  /* Property source. */
  bool use_context = false; /* Resolve `data_path` from the context, not from an ID. */
  short id_type = 0;
  uint32_t id_session_uid = 0;
  std::string data_path;
  /* Operator source, selected by a non-empty `op_idname`. */
  std::string op_idname;
  std::string op_propname;
  wm::OpCallContext op_context = wm::OpCallContext::InvokeRegionWin;
  /* Untranslated header label, kept so the header survives "Not available". */
  std::string label;
  std::string label_context;
};

static bool enum_tear_off_resolve(bContext *C,
                                  const EnumTearOffSource &source,
                                  PointerRNA *r_ptr,
                                  PropertyRNA **r_prop)
{
  PointerRNA root;
  if (source.use_context) {
    /* #rna_Context_tool_settings_get dereferences the scene. */
    if (CTX_data_scene(C) == nullptr) {
      return false;
    }
    root = RNA_pointer_create_discrete(nullptr, RNA_Context, C);
  }
  else {
    /* The typed lookup scans one list, and this runs on most notifiers. */
    ID *id = BKE_libblock_find_session_uid(
        CTX_data_main(C), source.id_type, source.id_session_uid);
    if (id == nullptr) {
      return false;
    }
    root = RNA_id_pointer_create(id);
  }
  return RNA_path_resolve_property(&root, source.data_path.c_str(), r_ptr, r_prop) &&
         RNA_property_type(*r_prop) == PROP_ENUM &&
         !(RNA_property_flag(*r_prop) & PROP_ENUM_FLAG);
}

/* The stored identifiers must lead back to this exact data, or the row isn't offered. This one
 * check covers unresolved PropertyGroup paths and anything else that doesn't round trip. */
static bool enum_tear_off_points_at(bContext *C,
                                    const EnumTearOffSource &source,
                                    const PointerRNA &ptr,
                                    const PropertyRNA *prop)
{
  PointerRNA r_ptr;
  PropertyRNA *r_prop;
  return enum_tear_off_resolve(C, source, &r_ptr, &r_prop) && r_prop == prop &&
         r_ptr.data == ptr.data;
}

static bool enum_tear_off_source_from_property(bContext *C,
                                               const PointerRNA &ptr,
                                               PropertyRNA *prop,
                                               EnumTearOffSource &r_source)
{
  ID *real_id = nullptr;
  /* The real ID, because a session UID lookup can't find embedded node trees or collections. */
  const std::optional<std::string> path = RNA_path_from_real_ID_to_property_index(
      CTX_data_main(C), &ptr, prop, 0, -1, &real_id);
  /* Index-based Screen paths can silently point at another area after an area edit. */
  if (!path || !real_id || ELEM(GS(real_id->name), ID_SCR, ID_WM)) {
    return false;
  }
  /* Data of the context's scene follows it, as the source button does, including the sequencer
   * scene through #rna_Context_tool_settings_get. A stored ID would stay on the old scene. */
  if (GS(real_id->name) == ID_SCE) {
    for (const std::string &candidate : {*path, "scene." + *path}) {
      r_source.use_context = true;
      r_source.data_path = candidate;
      if (enum_tear_off_points_at(C, r_source, ptr, prop)) {
        return true;
      }
    }
  }
  r_source.use_context = false;
  r_source.data_path = *path;
  r_source.id_type = GS(real_id->name);
  r_source.id_session_uid = real_id->session_uid;
  return enum_tear_off_points_at(C, r_source, ptr, prop);
}

static void enum_tear_off_row_draw(Layout *layout, const EnumTearOffSource &source)
{
  PointerRNA opptr = layout->op("WM_OT_enum_tear_off", IFACE_("Tear Off Menu"), ICON_GRIP);
  if (opptr.data) {
    RNA_string_set(&opptr, "data_path", source.data_path.c_str());
    RNA_boolean_set(&opptr, "use_context", source.use_context);
    RNA_int_set(&opptr, "id_type", source.id_type);
    RNA_int_set(&opptr, "session_uid", int(source.id_session_uid));
    RNA_string_set(&opptr, "op_idname", source.op_idname.c_str());
    RNA_string_set(&opptr, "op_propname", source.op_propname.c_str());
    RNA_int_set(&opptr, "op_context", int(source.op_context));
  }
  layout->separator(1.0f, LayoutSeparatorType::Line);
}

void enum_tear_off_row_draw_property(bContext *C, Layout *layout, const Button *but)
{
  /* No handle means no open popup, the same check as #enum_tear_off_row_draw_operator. */
  if (!tear_off_enabled() || layout->block()->handle == nullptr) {
    return;
  }
  /* A modal dialog owns the input. */
  const PopupBlockHandle *parent = but->block->handle;
  if (parent && parent->popup_op) {
    return;
  }
  /* A torn-off copy can't call the source button's callbacks, so it would silently lose them. */
  if (but->func || but->funcN || but->apply_func || but->block->handle_func) {
    return;
  }
  /* Flag enums toggle bits, which doesn't fit picking one value. */
  if (RNA_property_flag(but->rnaprop) & PROP_ENUM_FLAG) {
    return;
  }
  EnumTearOffSource source;
  if (enum_tear_off_source_from_property(C, but->rnapoin, but->rnaprop, source)) {
    enum_tear_off_row_draw(layout, source);
  }
}

void enum_tear_off_row_draw_operator(Layout *layout,
                                     const Button *but,
                                     const char *opname,
                                     const char *propname,
                                     const wm::OpCallContext opcontext)
{
  /* Menu Search draws these menus on a block with no popup handle to collect their buttons, and
   * the row would become a search result. This tests the block being drawn: the source button's
   * block has no handle under any header menu, where the row is wanted. */
  if (!tear_off_enabled() || layout->block()->handle == nullptr) {
    return;
  }
  const PopupBlockHandle *parent = but->block->handle;
  /* Context pointers and preset properties (such as `.only_active = False` on the Dope Sheet's
   * Add F-Curve Modifier) can't be stored in identifiers, and losing them would change what the
   * operator does. */
  const IDProperty *op_props = but->opptr ? but->opptr->data_as<IDProperty>() : nullptr;
  if ((parent && parent->popup_op) || but->context || (op_props && op_props->len > 0)) {
    return;
  }
  EnumTearOffSource source;
  source.op_idname = opname;
  source.op_propname = propname;
  source.op_context = opcontext;
  enum_tear_off_row_draw(layout, source);
}

/* The order and rules match the attached path: set, autokey and report (#apply_but_autokey), then
 * update, then undo (#apply_but_undo, #apply_but_funcs_after). Keep them in sync when merging. */
static void enum_tear_off_value_apply(bContext &C,
                                      const EnumTearOffSource &source,
                                      const std::string &identifier,
                                      const std::string &name)
{
  PointerRNA ptr;
  PropertyRNA *prop;
  int value;
  /* Resolved here and not at draw time, so a click arriving before the refresh writes nothing. */
  if (!enum_tear_off_resolve(&C, source, &ptr, &prop) || !RNA_property_editable(&ptr, prop) ||
      !RNA_property_enum_value(&C, &ptr, prop, identifier.c_str(), &value))
  {
    return;
  }
  RNA_property_enum_set(&ptr, prop, value);

  Scene *scene = CTX_data_scene(&C);
  animrig::autokeyframe_property(&C, scene, &ptr, prop, -1, BKE_scene_frame_get(scene), true);
  if (std::optional<const std::string> str = WM_prop_pystring_assign(&C, &ptr, prop, -1)) {
    BKE_report(CTX_wm_reports(&C), RPT_PROPERTY, str->c_str());
    WM_event_add_notifier(&C, NC_SPACE | ND_SPACE_INFO_REPORT, nullptr);
  }

  RNA_property_update(&C, &ptr, prop);

  if (!ptr.owner_id || !ID_CHECK_UNDO(ptr.owner_id) || !RNA_property_undo_check(prop, ptr.type)) {
    return;
  }
  std::optional<UndoEncodeHints> hints = ED_undo_is_legacy_compatible_for_property(
      &C, ptr.owner_id, ptr, *prop);
  /* Sculpt mode skips them because of the lag, see #71434. */
  if (!hints.has_value() || BKE_paintmode_get_active_from_context(&C) == PaintMode::Sculpt) {
    return;
  }
  WM_operator_stack_clear(CTX_wm_manager(&C));
  ED_undo_push(&C, name.c_str(), *hints);
}

void enum_tear_off_unavailable_draw(Layout *layout)
{
  Block *block = layout->block();
  block_layout_set_current(block, layout);
  /* Not a label: a label under Pulldown doesn't gray when disabled. A disabled menu item gets
   * half-alpha text and ignores clicks. */
  Button *but = uiDefBut(block,
                         ButtonType::ButMenu,
                         IFACE_("Not available"),
                         0,
                         0,
                         UI_UNIT_X * 5,
                         UI_UNIT_Y,
                         nullptr,
                         0.0,
                         0.0,
                         "");
  button_disable(but, "");
}

static wmOperatorType *enum_tear_off_operator_get(const EnumTearOffSource &source)
{
  wmOperatorType *ot = WM_operatortype_find(source.op_idname.c_str(), true);
  if (!ot || !ot->srna) {
    return nullptr;
  }
  PointerRNA ptr = WM_operator_properties_create_ptr(ot);
  PropertyRNA *prop = RNA_struct_find_property(&ptr, source.op_propname.c_str());
  return (prop && RNA_property_type(prop) == PROP_ENUM) ? ot : nullptr;
}

static void enum_tear_off_draw(bContext *C,
                               Layout *layout,
                               const std::shared_ptr<const EnumTearOffSource> &source)
{
  /* The title-less memory slot would move the first position, and every click would overwrite
   * it. */
  block_flag_disable(layout->block(), BLOCK_POPUP_MEMORY);

  tear_off_header_draw(layout,
                       source->label_context.c_str(),
                       source->label.c_str(),
                       "WM_OT_menu_tear_off_collapse",
                       "WM_OT_menu_tear_off_close");

  if (!source->op_idname.empty()) {
    /* Checked first, or #Layout::op_enum would show the raw idname through #item_disabled. */
    if (!enum_tear_off_operator_get(*source)) {
      enum_tear_off_unavailable_draw(layout);
      return;
    }
    layout->operator_context_set(source->op_context);
    layout->op_enum(
        source->op_idname, source->op_propname, nullptr, source->op_context, UI_ITEM_NONE);
    return;
  }

  PointerRNA ptr;
  PropertyRNA *prop;
  if (!enum_tear_off_resolve(C, *source, &ptr, &prop)) {
    enum_tear_off_unavailable_draw(layout);
    return;
  }
  const char *disabled_info = nullptr;
  const bool editable = RNA_property_editable_info(&ptr, prop, &disabled_info);

  EnumMenuDrawParams params;
  params.ptr = &ptr;
  params.prop = prop;
  params.aspect = 1.0f;      /* A torn-off block draws at window scale. */
  params.show_title = false; /* The header shows the same text. */
  params.copy_descriptions = true;
  params.item_fn = [&](Button &but, const EnumPropertyItem &item) {
    if (!editable) {
      button_disable(&but, disabled_info);
    }
    /* The identifier, because dynamic enums can renumber between drawing and the click. */
    button_func_set(&but,
                    [source,
                     identifier = std::string(item.identifier),
                     name = std::string(item.name ? item.name : "")](bContext &C) {
                      enum_tear_off_value_apply(C, *source, identifier, name);
                    });
  };
  enum_menu_draw(C, layout, params);
}

PopupBlockHandle *enum_tear_off_popup_create(bContext *C, PointerRNA *op_ptr)
{
  auto source = std::make_shared<EnumTearOffSource>();
  source->op_idname = RNA_string_get(op_ptr, "op_idname");

  if (!source->op_idname.empty()) {
    source->op_propname = RNA_string_get(op_ptr, "op_propname");
    source->op_context = wm::OpCallContext(RNA_int_get(op_ptr, "op_context"));
    wmOperatorType *ot = enum_tear_off_operator_get(*source);
    if (ot == nullptr) {
      return nullptr;
    }
    source->label = ot->name;
    source->label_context = ot->translation_context;
  }
  else {
    source->use_context = RNA_boolean_get(op_ptr, "use_context");
    source->id_type = short(RNA_int_get(op_ptr, "id_type"));
    source->id_session_uid = uint32_t(RNA_int_get(op_ptr, "session_uid"));
    source->data_path = RNA_string_get(op_ptr, "data_path");
    /* Python can call this, and #which_libbase asserts on a bad type. */
    if (!source->use_context && !BKE_idtype_idcode_is_valid(source->id_type)) {
      return nullptr;
    }
    PointerRNA ptr;
    PropertyRNA *prop;
    if (!enum_tear_off_resolve(C, *source, &ptr, &prop)) {
      return nullptr; /* The data went away between drawing the row and the click. */
    }
    source->label = RNA_property_ui_name_raw(prop, &ptr);
    source->label_context = RNA_property_translation_context(prop);
  }

  std::shared_ptr<const EnumTearOffSource> source_const = source;
  /* #srna_owner stays unset: it would stop the refresh when a type unregisters, and that refresh
   * is what shows "Not available". */
  return popup_menu_tear_off_create(C, [source_const](bContext *C, Layout *layout) {
    enum_tear_off_draw(C, layout, source_const);
  });
}

}  // namespace blender::ui
