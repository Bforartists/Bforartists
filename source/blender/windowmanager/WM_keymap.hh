/* SPDX-FileCopyrightText: 2007 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup wm
 */

#include <optional>
#include <string>

#include "DNA_windowmanager_types.h"
#include "WM_types.hh"

namespace blender {

#ifdef hyper /* MSVC defines. */
#  undef hyper
#endif

struct EnumPropertyItem;

/* Key Configuration. */

void WM_keyconfig_init(bContext *C);
void WM_keyconfig_reload(bContext *C);

wmKeyConfig *WM_keyconfig_new(wmWindowManager *wm, const char *idname, bool user_defined);
wmKeyConfig *WM_keyconfig_ensure(wmWindowManager *wm, const char *idname, bool user_defined);
void WM_keyconfig_remove(wmWindowManager *wm, wmKeyConfig *keyconf);
void WM_keyconfig_clear(wmKeyConfig *keyconf);
void WM_keyconfig_free(wmKeyConfig *keyconf);

void WM_keyconfig_set_active(wmWindowManager *wm, const char *idname);

/**
 * \param keep_properties: When true, the properties for operators which cannot be found are kept.
 * This is needed for operator reloading that validates key-map items for operators that may have
 * their operators loaded back in the future, see: #113309.
 */
void WM_keyconfig_update_ex(wmWindowManager *wm, bool keep_properties);
void WM_keyconfig_update(wmWindowManager *wm);
void WM_keyconfig_update_on_startup(wmWindowManager *wm);
void WM_keyconfig_update_tag(wmKeyMap *keymap, wmKeyMapItem *kmi);
void WM_keyconfig_update_operatortype_tag();

void WM_keyconfig_update_suppress_begin();
void WM_keyconfig_update_suppress_end();

void WM_keyconfig_update_postpone_begin();
void WM_keyconfig_update_postpone_end();

/* Key Intents. */

/**
 * Find an intent by `idname`, in a list or a key configuration.
 */
wmKeyIntent *WM_keyintent_list_find(ListBaseT<wmKeyIntent> *lb, const char *idname);
wmKeyIntent *WM_keyconfig_intent_find(wmKeyConfig *keyconf, const char *idname);
/**
 * Add an intent, or update the label & event of the existing intent with this `idname`.
 */
wmKeyIntent *WM_keyconfig_intent_ensure(wmKeyConfig *keyconf,
                                        const char *idname,
                                        const char *label,
                                        const char *category,
                                        const struct KeyMapItem_Params *params);
void WM_keyconfig_intent_remove(wmKeyConfig *keyconf, wmKeyIntent *ki);
/**
 * Tag the key configuration for update after editing its intents,
 * edits to the user configuration are stored in the preferences.
 */
void WM_keyconfig_intent_update_tag(wmKeyConfig *keyconf);
void WM_keyintent_update_tag(wmKeyIntent *ki);
/**
 * Restore an intent of the user configuration to the preset (and add-on) definition.
 */
void WM_keyintent_restore_to_default(wmWindowManager *wm, wmKeyIntent *ki);
/**
 * Number of key map items that take their key from `ki`, within the configuration owning it.
 */
int WM_keyintent_contexts_count(wmWindowManager *wm, const wmKeyIntent *ki);
std::optional<std::string> WM_keyintent_to_string(const wmKeyIntent *ki, bool compact);

/**
 * Link `kmi` to the intent `idname` (an empty string detaches it),
 * the key is taken from the intent when the key configuration is next updated.
 */
void WM_keymap_item_intent_set(wmKeyMapItem *kmi, const char *idname);
/**
 * Detach `kmi` from its intent when its event no longer matches the intent,
 * call after the event of an item has been edited.
 */
void WM_keymap_item_intent_detach_if_changed(wmWindowManager *wm, wmKeyMapItem *kmi);

/** Keymap. */

/** Parameters for matching events, passed into functions that create key-map items. */
struct KeyMapItem_Params {
  /** #wmKeyMapItem.type. */
  int16_t type;
  /** #wmKeyMapItem.val. */
  int8_t value;
  /**
   * This value is used to initialize #wmKeyMapItem `ctrl, shift, alt, oskey, hyper`.
   *
   * Valid values:
   *
   * - Combinations of: #KM_SHIFT, #KM_CTRL, #KM_ALT, #KM_OSKEY, #KM_HYPER.
   *   Are mapped to #KM_MOD_HELD.
   * - Combinations of the modifier flags bit-shifted using #KMI_PARAMS_MOD_TO_ANY.
   *   Are mapped to #KM_ANY.
   * - The value #KM_ANY is represents all modifiers being set to #KM_ANY.
   */
  int16_t modifier;

  /** #wmKeyMapItem.keymodifier. */
  int16_t keymodifier;
  /** #wmKeyMapItem.direction. */
  int8_t direction;
};

/**
 * Use to assign modifiers to #KeyMapItem_Params::modifier
 * which can have any state (held or released).
 */
#define KMI_PARAMS_MOD_TO_ANY(mod) ((mod) << 8)
/**
 * Use to read modifiers from #KeyMapItem_Params::modifier
 * which can have any state (held or released).
 */
#define KMI_PARAMS_MOD_FROM_ANY(mod) ((mod) >> 8)

void WM_keymap_clear(wmKeyMap *keymap);

/**
 * Always add item.
 */
wmKeyMapItem *WM_keymap_add_item(wmKeyMap *keymap,
                                 const char *idname,
                                 const KeyMapItem_Params *params);
wmKeyMapItem *WM_keymap_add_item_copy(wmKeyMap *keymap, const wmKeyMapItem *kmi_src);

void WM_keymap_remove_item(wmKeyMap *keymap, wmKeyMapItem *kmi);
std::optional<std::string> WM_keymap_item_to_string(const wmKeyMapItem *kmi, bool compact);

/** Record \a kmi in the usage history. */
void WM_keymap_activity_record(wmWindowManager *wm,
                               const wmKeyMap *keymap,
                               const wmKeyMapItem *kmi);
/** Record a modal key map item, named by its modal action. */
void WM_keymap_activity_record_modal(wmWindowManager *wm,
                                     const wmKeyMap *keymap,
                                     const wmKeyMapItem *kmi);
/**
 * Record an operator run without a shortcut.
 * \param spaceid: An #eSpace_Type or #SPACE_EMPTY, needed to offer a key map to bind it in.
 */
void WM_keymap_activity_record_unbound(wmWindowManager *wm,
                                       const char *idname,
                                       const char *variant,
                                       int spaceid);
/** Clear the usage history. */
void WM_keymap_activity_clear(wmWindowManager *wm);

/* -------------------------------------------------------------------- */
/** \name Key-Map Editor Selection
 * \{ */

/** Whether \a kmi is selected. */
bool WM_keymap_selection_contains(const wmWindowManager *wm,
                                  const wmKeyMap *keymap,
                                  const wmKeyMapItem *kmi);
/** Select or deselect \a kmi. */
void WM_keymap_selection_set(wmWindowManager *wm,
                             const wmKeyMap *keymap,
                             const wmKeyMapItem *kmi,
                             bool value);
/** Deselect all. */
void WM_keymap_selection_clear(wmWindowManager *wm);
/** Copy the event of \a kmi to the other selected items. */
void WM_keymap_selection_propagate_event(wmKeyMapItem *kmi);
/** Copy the active state of \a kmi to the other selected items. */
void WM_keymap_selection_propagate_active(wmKeyMapItem *kmi);

/** \} */

/* -------------------------------------------------------------------- */
/** \name Key-Map Editor Undo
 * \{ */

/** Push an undo step if the key configuration changed since the last checkpoint. */
void WM_keymap_undo_checkpoint(wmWindowManager *wm);
/** Undo the last key configuration change, false when there is none. */
bool WM_keymap_undo(wmWindowManager *wm);
/** Redo the last undone change, false when there is none. */
bool WM_keymap_redo(wmWindowManager *wm);
/** Number of undo/redo steps available. */
int WM_keymap_undo_len(const wmWindowManager *wm);
int WM_keymap_redo_len(const wmWindowManager *wm);
/** Free the undo history on window manager runtime teardown. */
void wm_keymap_undo_runtime_free(bke::WindowManagerRuntime &runtime);

/** \} */

wmKeyMap *WM_keymap_list_find(ListBaseT<wmKeyMap> *lb,
                              const char *idname,
                              int spaceid,
                              int regionid);
wmKeyMap *WM_keymap_list_find_spaceid_or_empty(ListBaseT<wmKeyMap> *lb,
                                               const char *idname,
                                               int spaceid,
                                               int regionid);
wmKeyMap *WM_keymap_ensure(wmKeyConfig *keyconf, const char *idname, int spaceid, int regionid);
wmKeyMap *WM_keymap_find_all(wmWindowManager *wm, const char *idname, int spaceid, int regionid);
wmKeyMap *WM_keymap_find_all_spaceid_or_empty(wmWindowManager *wm,
                                              const char *idname,
                                              int spaceid,
                                              int regionid);
wmKeyMap *WM_keymap_active(const wmWindowManager *wm, wmKeyMap *keymap);
void WM_keymap_remove(wmKeyConfig *keyconf, wmKeyMap *keymap);
bool WM_keymap_poll(bContext *C, wmKeyMap *keymap);

wmKeyMapItem *WM_keymap_item_find_id(wmKeyMap *keymap, int id);
bool WM_keymap_item_compare(const wmKeyMapItem *k1, const wmKeyMapItem *k2);

/**
 * Return the user key-map item from `km_base` based on `km_match` & `kmi_match`,
 * currently the supported use case is looking up "User" key-map items from "Add-on" key-maps.
 * Other lookups may be supported.
 */
wmKeyMapItem *WM_keymap_item_find_match(wmKeyMap *km_base,
                                        wmKeyMap *km_match,
                                        const wmKeyMapItem *kmi_match,
                                        ReportList *reports);

/* `wm_keymap_utils.cc`. */

/* Wrappers for #WM_keymap_add_item. */

/**
 * Menu wrapper for #WM_keymap_add_item.
 */
wmKeyMapItem *WM_keymap_add_menu(wmKeyMap *keymap,
                                 const char *idname,
                                 const KeyMapItem_Params *params);
/**
 * Pie-menu wrapper for #WM_keymap_add_item.
 */
wmKeyMapItem *WM_keymap_add_menu_pie(wmKeyMap *keymap,
                                     const char *idname,
                                     const KeyMapItem_Params *params);
/**
 * Panel (popover) wrapper for #WM_keymap_add_item.
 */
wmKeyMapItem *WM_keymap_add_panel(wmKeyMap *keymap,
                                  const char *idname,
                                  const KeyMapItem_Params *params);
/**
 * Tool wrapper for #WM_keymap_add_item.
 */
wmKeyMapItem *WM_keymap_add_tool(wmKeyMap *keymap,
                                 const char *idname,
                                 const KeyMapItem_Params *params);

wmKeyMap *WM_keymap_guess_from_context(const bContext *C);

/**
 * Guess an appropriate key-map from the operator name.
 *
 * \note Needs to be kept up to date with Key-map and Operator naming.
 */
wmKeyMap *WM_keymap_guess_opname(const bContext *C, const char *opname);

bool WM_keymap_uses_event_modifier(const wmKeyMap *keymap, int event_modifier);

void WM_keymap_fix_linking();

/* Modal Keymap. */

std::optional<std::string> WM_modalkeymap_items_to_string(const wmKeyMap *km,
                                                          int propvalue,
                                                          bool compact);
std::optional<std::string> WM_modalkeymap_operator_items_to_string(wmOperatorType *ot,
                                                                   int propvalue,
                                                                   bool compact);

wmKeyMap *WM_modalkeymap_ensure(wmKeyConfig *keyconf,
                                const char *idname,
                                const EnumPropertyItem *items);
wmKeyMap *WM_modalkeymap_find(wmKeyConfig *keyconf, const char *idname);
wmKeyMapItem *WM_modalkeymap_add_item(wmKeyMap *km, const KeyMapItem_Params *params, int value);
wmKeyMapItem *WM_modalkeymap_add_item_str(wmKeyMap *km,
                                          const KeyMapItem_Params *params,
                                          const char *value);
const wmKeyMapItem *WM_modalkeymap_find_propvalue(const wmKeyMap *km, int propvalue);
void WM_modalkeymap_assign(wmKeyMap *km, const char *opname);

/* Keymap Editor. */

void WM_keymap_restore_to_default(wmKeyMap *keymap, wmWindowManager *wm);
/**
 * Properties can be NULL, otherwise the arg passed is used and ownership is given to the `kmi`.
 */
void WM_keymap_item_properties_reset(wmKeyMapItem *kmi, IDProperty *properties);
void WM_keymap_item_restore_to_default(wmWindowManager *wm, wmKeyMap *keymap, wmKeyMapItem *kmi);
int WM_keymap_item_map_type_get(const wmKeyMapItem *kmi);
/** The #eKMI_MapType for an event type. */
int WM_key_event_map_type_get(short type);

/* Key Event. */

const char *WM_key_event_string(short type, bool compact);
std::optional<std::string> WM_keymap_item_raw_to_string(int8_t shift,
                                                        int8_t ctrl,
                                                        int8_t alt,
                                                        int8_t oskey,
                                                        int8_t hyper,
                                                        short keymodifier,
                                                        short val,
                                                        short type,
                                                        bool compact);
/**
 * \param include_mask: Event types to include when looking up keys (#eEventType_Mask).
 * \param exclude_mask: Event types to exclude when looking up keys (#eEventType_Mask).
 */
wmKeyMapItem *WM_key_event_operator(const bContext *C,
                                    const char *opname,
                                    wm::OpCallContext opcontext,
                                    IDProperty *properties,
                                    short include_mask,
                                    short exclude_mask,
                                    wmKeyMap **r_keymap);
std::optional<std::string> WM_key_event_operator_string(const bContext *C,
                                                        const char *opname,
                                                        wm::OpCallContext opcontext,
                                                        IDProperty *properties,
                                                        bool is_strict);

wmKeyMapItem *WM_key_event_operator_from_keymap(wmKeyMap *keymap,
                                                const char *opname,
                                                IDProperty *properties,
                                                short include_mask,
                                                short exclude_mask);

const char *WM_bool_as_string(bool test);

}  // namespace blender
