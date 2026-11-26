/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup bke
 */

#pragma once

#include <optional>

#include "BKE_report.hh"

#include "DNA_windowmanager_types.h"

#include "BLI_map.hh"
#include "BLI_set.hh"
#include "BLI_vector.hh"

namespace blender {

struct UndoStack;
struct wmMsgBus;
struct wmKeyConfig;
struct wmEvent;
struct wmWindow;
struct TaskPool;
struct wmIMEData;
struct wmGesture;
struct wmJob;
struct wmDrag;
struct wmCursorOverlay;
struct WindowDrawCB;

enum eWM_JobType : uint8_t;

namespace bke {

struct wmNotifierHashForQueue {
  uint64_t operator()(const wmNotifier *note) const;
};
struct wmNotifierEqForQueue {
  bool operator()(const wmNotifier *a, const wmNotifier *b) const;
};
using wmNotifierQueueSet = Set<const wmNotifier *,
                               4,
                               DefaultProbingStrategy,
                               wmNotifierHashForQueue,
                               wmNotifierEqForQueue>;

/** A recorded activation of a key map item, see #WindowManagerRuntime::keymap_activity. */
struct KeymapActivityItem {
  /** #wmKeyMap::idname. */
  char keymap_idname[/*KMAP_MAX_NAME*/ 64] = "";
  /** #wmKeyMapItem::idname (non-modal items). */
  char op_idname[/*OP_MAX_TYPENAME*/ 64] = "";
  /** Enum identifier of #wmKeyMapItem::propvalue (modal items, see #is_modal). */
  char propvalue[/*OP_MAX_TYPENAME*/ 64] = "";
  /** Distinguishes uses of #op_idname, see #WM_operator_usage_variant. */
  char variant[/*OP_MAX_USAGE_VARIANT*/ 128] = "";
  /** Human readable key combination, see #WM_keymap_item_to_string. */
  char event_str[64] = "";
  /**
   * #eSpace_Type of the most recent activation, #SPACE_EMPTY when outside an editor.
   * For operations without a key map item this is the only record of the editor.
   */
  int spaceid = 0;
  /** Time of the most recent activation, see #BLI_time_now_seconds. */
  double time = 0.0;
  /** Number of consecutive activations collapsed into this entry. */
  int repeat = 1;
  /** False when the operator ran without a key map item (menu, button, search, script). */
  bool is_shortcut = true;
  /** Modal key map item. */
  bool is_modal = false;
  /** UI state: show the key map item expanded in the recently used list. */
  bool show_expanded = false;
};

/** A key map item selected in the key map editor, by identifier (key maps may be rebuilt). */
struct KeymapSelectionItem {
  /** #wmKeyMap::idname, #wmKeyMap::spaceid, #wmKeyMap::regionid. */
  char keymap_idname[/*KMAP_MAX_NAME*/ 64] = "";
  int spaceid = 0;
  int regionid = 0;
  /** #wmKeyMapItem::id. */
  int item_id = 0;
};

/** Snapshot of the user key configuration, see #WM_keymap_undo_checkpoint. */
struct KeymapUndoStep {
  ListBaseT<wmKeyMap> user_keymaps = {nullptr, nullptr};
  ListBaseT<wmKeyIntent> user_keyintents = {nullptr, nullptr};
};

struct WindowManagerRuntime {
  /** Separate active from drawable. */
  wmWindow *windrawable = nullptr;
  /**
   * \note `CTX_wm_window(C)` is usually preferred.
   * Avoid relying on this where possible as this may become NULL during when handling
   * events that close or replace windows (e.g. opening a file).
   * While this happens rarely in practice, it can cause difficult to reproduce bugs.
   */
  wmWindow *winactive = nullptr;

  /** Indicates whether interface is locked for user interaction. */
  bool is_interface_locked = false;

  /** Indicates whether modified images should be saved when saving the blend file. */
  char save_modified_images_when_file_is_saved = true;

  /**
   * Indicates the main loop (#WM_main()) to stop processing the event queue and move to the next
   * step. The Remaining events will then be processed during the next iteration of the loop.
   *
   * This is used e.g. to avoid handling events immediately after an undo/redo action, when UI has
   * not yet been updated.
   */
  bool break_events_handling = false;

  /** BFA - Tear-Off Menu/Panel: a workspace's stored pins may be ready to restore, see
   * #ui::tear_off_restore_tag. */
  bool tear_off_restore_pending = false;

  /** Information and error reports. */
  ReportList reports;

  /**
   * Refresh/redraw #wmNotifier structs.
   * \note Once in the queue, notifiers should be considered read-only.
   * With the exception of clearing notifiers for data which has been removed,
   * see: #NOTE_CATEGORY_TAG_CLEARED.
   */
  ListBaseT<wmNotifier> notifier_queue = {nullptr, nullptr};
  /**
   * For duplicate detection.
   * \note keep in sync with `notifier_queue` adding/removing elements must also update this set.
   */
  wmNotifierQueueSet notifier_queue_set;

  /** The current notifier in the `notifier_queue` being handled (clear instead of freeing). */
  const wmNotifier *notifier_current = nullptr;

  /** Operator registry. */
  ListBaseT<wmOperator> operators = {nullptr, nullptr};

  /** Extra overlay cursors to draw, like circles. */
  ListBaseT<wmCursorOverlay> cursor_overlays = {nullptr, nullptr};

  /**
   * Known key configurations.
   * This includes all the #wmKeyConfig members (`defaultconf`, `addonconf`, etc).
   */
  ListBaseT<wmKeyConfig> keyconfigs = {nullptr, nullptr};

  /** Active timers. */
  ListBaseT<wmTimer> timers = {nullptr, nullptr};

  /** Threaded jobs manager. */
  ListBaseT<wmJob> jobs = {nullptr, nullptr};

  /** Task pools for each job type. */
  Map<eWM_JobType, TaskPool *> job_task_pools;
  /** The time in seconds when each job task pool was last used. */
  Map<eWM_JobType, int64_t> job_task_pools_last_used_times;

  /** Active dragged items. */
  ListBaseT<wmDrag> drags = {nullptr, nullptr};

  /** Default configuration. */
  wmKeyConfig *defaultconf = nullptr;

  /** Addon configuration. */
  wmKeyConfig *addonconf = nullptr;

  /** User configuration. */
  wmKeyConfig *userconf = nullptr;

  /**
   * All undo history.
   *
   * \note This will be null in background mode unless explicitly created.
   */
  UndoStack *undo_stack = nullptr;

  wmMsgBus *message_bus = nullptr;

  /** Recently triggered key map items (oldest first), see #WM_keymap_activity_record. */
  Vector<KeymapActivityItem> keymap_activity;
  /** UI state: key map items selected in the key map editor. */
  Vector<KeymapSelectionItem> keymap_selection;
  /** Undo steps, oldest first, see #WM_keymap_undo_checkpoint. */
  Vector<KeymapUndoStep *> keymap_undo;
  /** Redo steps, newest first, cleared on any other change. */
  Vector<KeymapUndoStep *> keymap_redo;
  /** State at the last checkpoint, what undo restores. */
  KeymapUndoStep *keymap_undo_baseline = nullptr;
  /** Non-zero while undoing or redoing, suppresses recording. */
  int keymap_undo_suspend = 0;
  /** UI state: show the recently used key map item list in the key map editor. */
  bool keymap_activity_show = true;
  /** UI state: show the hidden key map item list expanded. */
  bool keymap_activity_show_hidden = false;
  /** UI state: usage region height while open, restored on reopening. */
  int keymap_activity_region_sizey = 0;
  /** UI state: usage region height when closed (a single row). */
  int keymap_activity_region_closed_sizey = 0;

  WindowManagerRuntime();
  ~WindowManagerRuntime();
};

/**
 * The kind of UI element that began the window's IME session, see #WindowRuntime::ime_owner.
 *
 * Popups store the type of session with the element that began them.
 * Avoids buttons/regions acting on an IME popup it doesn't own.
 */
enum class wmIMEOwnerType : int8_t {
  /**
   * A region's `cursor_ime` callback (via #WM_window_IME_region_refresh),
   * always the screen's active region.
   */
  Region,
  /** A text button being edited (which may be in a popup floating over an unrelated region). */
  Button,
};

struct WindowRuntime {
  /** All events #wmEvent (ghost level events were handled). */
  ListBaseT<wmEvent> event_queue = {nullptr, nullptr};

  /**
   * Input Method Editor data - complex character input (especially for Asian character input)
   * Only used when `WITH_INPUT_IME` is defined.
   */
  wmIMEData *ime_data = nullptr;
  /**
   * The UI element this session was begun with.
   * Set by #WM_window_IME_begin, cleared by #WM_window_IME_end.
   */
  std::optional<wmIMEOwnerType> ime_owner;
  /**
   * True while the user is composing text via an IME
   * (set by #WM_IME_COMPOSITE_START, cleared by #WM_IME_COMPOSITE_END or #WM_window_IME_end).
   *
   * Operators
   * =========
   *
   * When true, text input operators that support IME are skipped (returning canceled).
   * This is needed because keys that edit the composition (backspace, enter, arrow-keys... etc)
   * are consumed by the IME but *also* pass-through as regular key events,
   * which the key-map handles as usual: a backspace that removes a pre-edit
   * character would also delete committed text.
   * Theoretically these events could be filtered out before being handled,
   * however only the IME knows which keys it consumes and this isn't exposed by any API,
   * so operators must skip them while composing.
   * Canceling instead of passing the event through prevents other key-map items from matching it.
   *
   * See:
   * - #WM_operator_IME_edit_maybe
   * - #WM_operator_IME_insert_maybe
   */
  bool ime_data_is_composing = false;

  /* Optionally store the size and position using this key in the user's recents file. */
  std::string recents_storage_key = {};

  /** Don't want to include ghost.h stuff. */
  void *ghostwin = nullptr;

  /** Don't want to include gpu stuff. */
  void *gpuctx = nullptr;

  /** Window+screen handlers, handled last. */
  ListBaseT<wmEventHandler> handlers = {nullptr, nullptr};

  /** Priority handlers, handled first. */
  ListBaseT<wmEventHandler> modalhandlers = {nullptr, nullptr};

  /** Custom drawing callbacks. */
  ListBaseT<WindowDrawCB> drawcalls = {nullptr, nullptr};

  /** Gesture stuff. */
  ListBaseT<wmGesture> gesture = {nullptr, nullptr};

  /**
   * Keep the last handled event in `event_queue` here (owned and must be freed).
   *
   * \warning This must only to be used for event queue logic.
   * User interactions should use `eventstate` instead (if the event isn't passed to the function).
   */
  wmEvent *event_last_handled = nullptr;

  /**
   * Storage for event system.
   *
   * For the most part this is storage for `wmEvent.xy` & `wmEvent.modifiers`.
   * newly added key/button events copy the cursor location and modifier state stored here.
   *
   * It's also convenient at times to be able to pass this as if it's a regular event.
   *
   * - This is not simply the current event being handled.
   *   The type and value is always set to the last press/release events
   *   otherwise cursor motion would always clear these values.
   *
   * - The value of `eventstate->modifiers` is set from the last pressed/released modifier key.
   *   This has the down side that the modifier value will be incorrect if users hold both
   *   left/right modifiers then release one. See note in #wm_event_add_ghostevent for details.
   */
  wmEvent *eventstate = nullptr;

  /**
   * The time when the key is pressed in milliseconds (see #GHOST_IEvent::getTime).
   * Used to detect double-click events.
   */
  uint64_t eventstate_prev_press_time_ms = 0;

  /** Private runtime info to show text in the status bar. */
  void *cursor_keymap_status = nullptr;

  WindowRuntime() = default;
  ~WindowRuntime();
};

}  // namespace bke
}  // namespace blender
