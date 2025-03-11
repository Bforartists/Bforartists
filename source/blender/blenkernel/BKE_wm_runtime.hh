/* SPDX-FileCopyrightText: 2024 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

struct GSet;

#include "DNA_windowmanager_types.h"

namespace blender::bke {

struct WindowManagerRuntime {
  /** Indicates whether interface is locked for user interaction. */
  bool is_interface_locked = false;

  /** Information and error reports. */
  ReportList reports;

  /**
   * Refresh/redraw #wmNotifier structs.
   * \note Once in the queue, notifiers should be considered read-only.
   * With the exception of clearing notifiers for data which has been removed,
   * see: #NOTE_CATEGORY_TAG_CLEARED.
   */
  ListBase notifier_queue = {nullptr, nullptr};
  /**
   * For duplicate detection.
   * \note keep in sync with `notifier_queue` adding/removing elements must also update this set.
   */
  GSet *notifier_queue_set = nullptr;

  /** The current notifier in the `notifier_queue` being handled (clear instead of freeing). */
  const wmNotifier *notifier_current = nullptr;

  WindowManagerRuntime();
  ~WindowManagerRuntime();
};

struct WindowRuntime {
  /** All events #wmEvent (ghost level events were handled). */
  ListBase event_queue = {nullptr, nullptr};

  WindowRuntime() = default;
  ~WindowRuntime();
};

}  // namespace blender::bke
