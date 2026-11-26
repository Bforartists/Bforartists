# SPDX-FileCopyrightText: 2010-2023 Blender Authors
#
# SPDX-License-Identifier: GPL-2.0-or-later

__all__ = (
    "draw_entry",
    "draw_km",
    "draw_kmi",
    "draw_filtered",
    "draw_hierarchy",
    "draw_intents",
    "draw_keymaps",
    "draw_keymaps_filter",
    "draw_keymaps_header",
    "draw_keymaps_tree",
    "draw_keymaps_usage",
    "usage_activity_visible",
    "usage_hidden_is_flashing",
    "usage_hidden_label",
    "usage_operation_label",
    "usage_suggested_name",
    "usage_variant_apply",
    "usage_variant_is_editor_scoped",
    "keymap_item_addon_name",
    "keymap_item_is_from_addon",
    "keymap_clash_is_certain",
    "keymap_conflict_check_clear",
    "keymap_conflict_check_count",
    "keymap_conflict_check_set",
    "keymap_item_clashes",
    "keymap_item_custom_name",
    "keymap_item_labels",
    "keymap_filter_labels",
    "keymap_selection_labels",
    "keymap_item_label",
    "keymap_item_search_names",
    "keymap_filter_refresh",
    "keymap_filtered_collapse",
    "keymap_row_is_drawn",
    "keymap_intents_region_visible",
    "scroll_to_keymap",
    "set_conflict_flash",
    "set_intent_reveal_target",
    "set_reveal_target",
)


import time

import bpy
from bpy.app.translations import (
    contexts as i18n_contexts,
    pgettext_iface as iface_,
    pgettext_rpt as rpt_,
)


_KMI_FLASH_SECONDS = 1.0
# {(keymap_name, operator_idname): key_string, ...} of items to flash this redraw.
_kmi_flash_map = {}
_kmi_flash_modal = set()
# Key map names with a flashing item, to highlight collapsed key map headers.
_kmi_flash_km_names = set()
# Keys of hidden entries used recently, see `usage_hidden_is_flashing`.
_kmi_flash_hidden_keys = set()
_kmi_flash_timer_pending = False

_kmi_filtered_expanded = set()


def keymap_filtered_collapse():
    """Collapse every expanded row of the filtered view."""
    _kmi_filtered_expanded.clear()


def _kmi_filtered_expanded_key(km, kmi):
    return (km.name, kmi.id)


def keymap_filtered_expand_toggle(keymap_name, item_id):
    """Toggle expansion of one filtered row."""
    key = (keymap_name, item_id)
    if key in _kmi_filtered_expanded:
        _kmi_filtered_expanded.discard(key)
    else:
        _kmi_filtered_expanded.add(key)

_KMI_REVEAL_SECONDS = 1.5
# Row key (see `_kmi_row_key_item`) to highlight, or None.
_kmi_reveal_target = None
_kmi_reveal_timer_pending = False
_kmi_reveal_expiry = 0.0

# The same for the intents column: the intent identifier to highlight, its row offsets
# (recorded as the column draws, in rows from the top) and the pending scroll.
_intent_reveal_target = None
_intent_reveal_timer_pending = False
_intent_reveal_expiry = 0.0
_intent_row_offsets = {}
_intent_row_cursor = 0.0
_intent_scroll_to = None
_intent_scroll_expiry = 0.0

_KMI_CONFLICT_FLASH_SECONDS = 3.0
# Row key to flash red (the item another item conflicts with), or None.
_kmi_conflict_flash_target = None
_kmi_conflict_flash_timer_pending = False
_kmi_conflict_flash_expiry = 0.0

# Row key (see `_kmi_row_key_*`) to scroll to, or None.
_kmi_scroll_to = None
# Time to wait for the row to be drawn before giving up.
_KMI_SCROLL_SECONDS = 0.5
_kmi_scroll_expiry = 0.0

# (view_y, draw_serial, expiry) of a scroll to restore after the next draw, or None.
_kmi_scroll_offset_to = None
# Incremented every tree draw, so a pending scroll can detect a stale layout.
_kmi_draw_serial = 0

# {row_key: rows from the top of the tree}, filled while drawing.
_kmi_row_offsets = {}
_kmi_row_cursor = 0.0
# A `separator()` is 6px against a row's 20, see `Layout::separator`.
_KMI_ROW_SEPARATOR = 0.3

_VIEW_HISTORY_MAX = 32
# [(view_state, scroll_y), ...] oldest first, for "Back".
_view_history = []
_view_state_now = None
# Set while restoring, so the restored state is not recorded again.
_view_restoring = False
# Consecutive search text edits are recorded as one history entry.
_view_last_was_text = False


def _view_state(spref):
    """The filter settings that decide which items are shown."""
    return (
        spref.filter_type,
        spref.filter_text,
        spref.use_filter_key_exact,
        spref.use_filter_user_modified,
        keymap_filter_labels(),
        spref.use_filter_addon,
        spref.use_filter_conflicts,
        bpy.context.preferences.keymap.show_ui_keyconfig,
    )


def _view_state_apply(spref, state):
    """Apply a `_view_state` tuple."""
    from bl_keymap_utils import editor_meta
    (spref.filter_type, spref.filter_text, spref.use_filter_key_exact,
     spref.use_filter_user_modified, filter_labels, spref.use_filter_addon,
     spref.use_filter_conflicts, show_ui_keyconfig) = state
    for label_name, _use_filter in editor_meta.labels_list():
        editor_meta.label_filter_set(label_name, label_name in filter_labels)
    bpy.context.preferences.keymap.show_ui_keyconfig = show_ui_keyconfig


def _view_history_note(spref):
    """Record the previous view when the view state changes."""
    global _view_state_now, _view_last_was_text

    state = _view_state(spref)
    if state == _view_state_now:
        return

    previous = _view_state_now
    _view_state_now = state
    if (previous is None) or _view_restoring:
        return

    # Only the search text changed.
    text_only = (previous[:1] + previous[2:]) == (state[:1] + state[2:])
    if not (text_only and _view_last_was_text):
        # Read the scroll before this draw lays out the new list.
        _view_history.append((previous, _kmi_scroll_offset_get()))
        del _view_history[:-_VIEW_HISTORY_MAX]
    _view_last_was_text = text_only


def keymap_view_history_depth():
    """Number of views "Back" can step through."""
    return len(_view_history)


def keymap_view_back(context):
    """Restore the previous view, returns False when there is none."""
    global _view_restoring, _view_state_now, _view_last_was_text
    if not _view_history:
        return False

    spref = context.space_data
    if (spref is None) or (spref.type != 'PREFERENCES'):
        return False

    state, scroll_y = _view_history.pop()
    _view_restoring = True
    try:
        _view_state_apply(spref, state)
    finally:
        _view_restoring = False
    _view_state_now = state
    _view_last_was_text = False
    # After the state is applied, so the scroll matches the restored list.
    _kmi_scroll_offset_set(scroll_y)
    return True


_keymap_tree_filter_ok = True

_kmi_conflicts_view = False

_keymap_filter_pinned = {}
_keymap_filter_signature = None
_kmi_filter_stale = {}
_keymap_filter_shown_count = 0
_keymap_filter_stale_count = 0
_keymap_filter_redraw_pending = False


def _kmi_filter_stale_clear():
    _kmi_filter_stale.clear()


def _keymap_redraw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'PREFERENCES':
                area.tag_redraw()


def _keymap_filter_redraw():
    global _keymap_filter_redraw_pending
    _keymap_filter_redraw_pending = False
    _keymap_redraw()
    return None


def _keymap_filter_counts_set(shown, stale):
    """Store the counts the tree drew, redrawing the header when they change."""
    global _keymap_filter_shown_count, _keymap_filter_stale_count
    global _keymap_filter_redraw_pending
    if (shown, stale) == (_keymap_filter_shown_count, _keymap_filter_stale_count):
        return
    _keymap_filter_shown_count = shown
    _keymap_filter_stale_count = stale
    if not _keymap_filter_redraw_pending:
        _keymap_filter_redraw_pending = True
        bpy.app.timers.register(_keymap_filter_redraw, first_interval=0.0)


def keymap_filter_refresh():
    """Drop pinned items that no longer match the filter."""
    _keymap_filter_pinned.clear()
    _kmi_filter_stale.clear()


def _kmi_flash_redraw():
    global _kmi_flash_timer_pending
    _kmi_flash_timer_pending = False
    _keymap_redraw()
    return None


def _kmi_hidden_flash_key(item):
    """Key for `_kmi_flash_hidden_keys`, matching `usage_hidden_is_flashing`."""
    if item.is_shortcut:
        return (item.keymap_name, item.idname, item.key_string, item.propvalue)
    return (item.idname, item.variant)


def usage_hidden_is_flashing(entry):
    """Whether the hidden entry was used within `_KMI_FLASH_SECONDS`."""
    if not _kmi_flash_hidden_keys:
        return False
    if entry.idname:
        return (entry.idname, entry.variant) in _kmi_flash_hidden_keys

    km = bpy.context.window_manager.keyconfigs.user.keymaps.get(entry.keymap_name)
    kmi = km.active().keymap_items.from_id(entry.item_id) if km is not None else None
    if kmi is None:
        return False
    return (
        entry.keymap_name,
        kmi.idname,
        kmi.to_string(),
        kmi.propvalue if km.active().is_modal else "",
    ) in _kmi_flash_hidden_keys


def _kmi_flash_update(wm):
    global _kmi_flash_timer_pending
    _kmi_flash_map.clear()
    _kmi_flash_modal.clear()
    _kmi_flash_km_names.clear()
    _kmi_flash_hidden_keys.clear()
    def flash_tree_row(item):
        if item.is_modal:
            _kmi_flash_modal.add((item.keymap_name, item.key_string, item.propvalue))
        else:
            _kmi_flash_map[(item.keymap_name, item.idname)] = item.key_string
        _kmi_flash_km_names.add(item.keymap_name)

    for item in wm.keymap_activity:
        if item.seconds_since < _KMI_FLASH_SECONDS:
            if item.is_shortcut:
                flash_tree_row(item)
            _kmi_flash_hidden_keys.add(_kmi_hidden_flash_key(item))
    if ((_kmi_flash_map or _kmi_flash_modal or _kmi_flash_hidden_keys)
            and not _kmi_flash_timer_pending):
        # Redraw after the flash expires to clear the highlight.
        _kmi_flash_timer_pending = True
        bpy.app.timers.register(_kmi_flash_redraw, first_interval=_KMI_FLASH_SECONDS + 0.05)


def _kmi_row_is_flashing(km, kmi):
    """Whether the item was used within `_KMI_FLASH_SECONDS`, see `_kmi_flash_update`."""
    if km.is_modal:
        return (km.name, kmi.to_string(), kmi.propvalue) in _kmi_flash_modal
    flash_key = _kmi_flash_map.get((km.name, kmi.idname))
    return flash_key is not None and flash_key == kmi.to_string()


def _kmi_reveal_clear():
    global _kmi_reveal_target, _kmi_reveal_timer_pending
    remaining = _kmi_reveal_expiry - time.monotonic()
    if remaining > 0.0:
        return remaining
    _kmi_reveal_target = None
    _kmi_reveal_timer_pending = False
    _keymap_redraw()
    return None


def _kmi_conflict_flash_clear():
    global _kmi_conflict_flash_target, _kmi_conflict_flash_timer_pending
    remaining = _kmi_conflict_flash_expiry - time.monotonic()
    if remaining > 0.0:
        return remaining
    _kmi_conflict_flash_target = None
    _kmi_conflict_flash_timer_pending = False
    _keymap_redraw()
    return None


def set_conflict_flash(km, kmi):
    """Flash a key map item red for a moment."""
    global _kmi_conflict_flash_target
    global _kmi_conflict_flash_timer_pending, _kmi_conflict_flash_expiry
    _kmi_conflict_flash_target = _kmi_row_key_item(km, kmi)
    _kmi_conflict_flash_expiry = time.monotonic() + _KMI_CONFLICT_FLASH_SECONDS
    _keymap_redraw()
    if not _kmi_conflict_flash_timer_pending:
        _kmi_conflict_flash_timer_pending = True
        bpy.app.timers.register(
            _kmi_conflict_flash_clear, first_interval=_KMI_CONFLICT_FLASH_SECONDS)


def keymap_row_is_drawn(km, kmi):
    """Whether the item's row was drawn in the last tree draw."""
    return (km.name, km.space_type, km.region_type, kmi.id) in _kmi_drawn_rows


def _kmi_row_key_keymap(km):
    """Key of a key map header row in `_kmi_row_offsets`."""
    return ("KEYMAP", km.name, km.space_type, km.region_type)


def _kmi_row_key_item(km, kmi):
    """Key of a key map item row in `_kmi_row_offsets`."""
    return ("ITEM", km.name, km.space_type, km.region_type, kmi.id)


def _kmi_row_advance(rows):
    global _kmi_row_cursor
    _kmi_row_cursor += rows


def _kmi_row_mark(key):
    """Record the offset of the row about to be drawn."""
    _kmi_row_offsets[key] = _kmi_row_cursor


def _kmi_rows_reset():
    global _kmi_row_cursor
    _kmi_row_cursor = 0.0
    _kmi_row_offsets.clear()


def _kmi_scroll_run():
    """Timer: scroll to `_kmi_scroll_to` once its row offset is known."""
    global _kmi_scroll_to
    key = _kmi_scroll_to
    if key is None:
        return None

    rows = _kmi_row_offsets.get(key)
    if rows is None:
        # Not drawn yet (or not visible), retry until expiry.
        return 0.05 if time.monotonic() < _kmi_scroll_expiry else None
    _kmi_scroll_to = None

    _scroll_regions_to_rows('WINDOW', rows)
    return None


def _scroll_regions_to_rows(region_type, rows):
    """Scroll this region of every preferences editor so the row at `rows` is at the top."""
    context = bpy.context
    row_height = round(20.0 * context.preferences.system.ui_scale)
    for window, area, region in _preferences_regions(region_type):
        with context.temp_override(window=window, area=area, region=region):
            bpy.ops.view2d.pan('EXEC_DEFAULT', deltax=0, deltay=100000)
            if rows > 0.0:
                bpy.ops.view2d.pan(
                    'EXEC_DEFAULT', deltax=0, deltay=-round(rows * row_height),
                )


def _preferences_regions(region_type):
    """Yield (window, area, region) for this region of every preferences editor."""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type != 'PREFERENCES':
                continue
            region = next((r for r in area.regions if r.type == region_type), None)
            if region is not None:
                yield window, area, region


def _preferences_tree_regions():
    """Yield (window, area, region) for every preferences editor's window region."""
    yield from _preferences_regions('WINDOW')


def _kmi_scroll_offset_get():
    """Scroll position as the view Y of the region's top edge (`View2D` exposes no offset directly)."""
    for _window, _area, region in _preferences_tree_regions():
        return region.view2d.region_to_view(0, region.height)[1]
    return None


def _kmi_scroll_offset_run():
    """Timer: restore `_kmi_scroll_offset_to` once the tree has redrawn."""
    global _kmi_scroll_offset_to
    pending = _kmi_scroll_offset_to
    if pending is None:
        return None

    target_y, serial, expiry = pending
    if _kmi_draw_serial == serial:
        # The restored view has not been drawn yet.
        return 0.05 if time.monotonic() < expiry else None
    _kmi_scroll_offset_to = None

    context = bpy.context
    for window, area, region in _preferences_tree_regions():
        with context.temp_override(window=window, area=area, region=region):
            # Pan to the top first, the stored offset is measured from there.
            bpy.ops.view2d.pan('EXEC_DEFAULT', deltax=0, deltay=100000)
            delta = round(region.view2d.region_to_view(0, region.height)[1] - target_y)
            if delta > 0:
                bpy.ops.view2d.pan('EXEC_DEFAULT', deltax=0, deltay=-delta)
    return None


def _kmi_scroll_offset_set(target_y):
    """Restore a scroll position from `_kmi_scroll_offset_get` after the next draw."""
    global _kmi_scroll_offset_to
    if target_y is None:
        return
    _kmi_scroll_offset_to = (target_y, _kmi_draw_serial, time.monotonic() + _KMI_SCROLL_SECONDS)
    _keymap_redraw()
    bpy.app.timers.register(_kmi_scroll_offset_run, first_interval=0.05)


def _kmi_scroll_to_row(key):
    """Scroll the row with this key to the top of the tree."""
    global _kmi_scroll_to, _kmi_scroll_expiry
    _kmi_scroll_to = key
    _kmi_scroll_expiry = time.monotonic() + _KMI_SCROLL_SECONDS
    _keymap_redraw()
    bpy.app.timers.register(_kmi_scroll_run, first_interval=0.05)


def scroll_to_keymap(km):
    """Scroll the tree to this key map's header."""
    _kmi_scroll_to_row(_kmi_row_key_keymap(km))


def set_reveal_target(km, kmi):
    """Highlight a key map item and scroll to it."""
    global _kmi_reveal_target
    global _kmi_reveal_timer_pending, _kmi_reveal_expiry
    _kmi_reveal_target = _kmi_row_key_item(km, kmi)
    _kmi_reveal_expiry = time.monotonic() + _KMI_REVEAL_SECONDS
    _kmi_scroll_to_row(_kmi_reveal_target)
    if not _kmi_reveal_timer_pending:
        _kmi_reveal_timer_pending = True
        bpy.app.timers.register(_kmi_reveal_clear, first_interval=_KMI_REVEAL_SECONDS)


# -----------------------------------------------------------------------------
# Intents Column: Reveal & Scroll
#
# Mirrors the tree's reveal, with the intents region and its own row offsets.

def _intent_rows_reset():
    global _intent_row_cursor
    _intent_row_cursor = 0.0
    _intent_row_offsets.clear()


def _intent_row_mark(key):
    _intent_row_offsets[key] = _intent_row_cursor


def _intent_row_advance(rows):
    global _intent_row_cursor
    _intent_row_cursor += rows


def _intent_scroll_run():
    """Timer: scroll the intents column to `_intent_scroll_to` once its row offset is known."""
    global _intent_scroll_to
    key = _intent_scroll_to
    if key is None:
        return None
    rows = _intent_row_offsets.get(key)
    if rows is None:
        return 0.05 if time.monotonic() < _intent_scroll_expiry else None
    _intent_scroll_to = None
    _scroll_regions_to_rows('CHANNELS', rows)
    return None


def _intent_reveal_clear():
    global _intent_reveal_target, _intent_reveal_timer_pending
    remaining = _intent_reveal_expiry - time.monotonic()
    if remaining > 0.0:
        return remaining
    _intent_reveal_target = None
    _intent_reveal_timer_pending = False
    _keymap_redraw()
    return None


def keymap_intents_region_visible(area):
    """Whether the intents column of this preferences editor is shown (a hidden region has no size)."""
    region = next((r for r in area.regions if r.type == 'CHANNELS'), None)
    return region is not None and region.width > 1


def set_intent_reveal_target(intent):
    """Highlight an intent in the intents column and scroll to it."""
    global _intent_reveal_target, _intent_scroll_to
    global _intent_reveal_timer_pending, _intent_reveal_expiry, _intent_scroll_expiry
    _intent_reveal_target = intent.name
    _intent_reveal_expiry = time.monotonic() + _KMI_REVEAL_SECONDS
    _intent_scroll_to = intent.name
    _intent_scroll_expiry = time.monotonic() + _KMI_SCROLL_SECONDS
    _intent_rows_reset()
    _keymap_redraw()
    bpy.app.timers.register(_intent_scroll_run, first_interval=0.05)
    if not _intent_reveal_timer_pending:
        _intent_reveal_timer_pending = True
        bpy.app.timers.register(_intent_reveal_clear, first_interval=_KMI_REVEAL_SECONDS)


def _activity_keymap_item(kc, item):
    """(key map, item) of an activity entry, None for whichever is not found."""
    km = kc.keymaps.get(item.keymap_name)
    if km is None:
        return (None, None)
    is_modal = item.is_modal
    for kmi in km.keymap_items:
        if kmi.to_string() != item.key_string:
            continue
        if (kmi.propvalue == item.propvalue) if is_modal else (kmi.idname == item.idname):
            return (km, kmi)
    return (km, None)


_kmi_conflict_cache = {}

_KMI_WHEEL_TYPES = frozenset({
    "WHEELUPMOUSE", "WHEELDOWNMOUSE", "WHEELINMOUSE", "WHEELOUTMOUSE",
})


_kmi_label_cache = None


def _kmi_label_cache_clear():
    global _kmi_label_cache
    _kmi_label_cache = None


def _kmi_item_labels_all():
    """{(keymap_name, space_type, region_type): {item_id: [label, ...]}}, cached per draw."""
    from bl_keymap_utils import editor_meta
    global _kmi_label_cache
    if _kmi_label_cache is None:
        cache = {}
        for km_name, space_type, region_type, item_id, label in editor_meta.label_items_all():
            cache.setdefault(
                (km_name, space_type, region_type), {},
            ).setdefault(item_id, []).append(label)
        _kmi_label_cache = cache
    return _kmi_label_cache


def keymap_item_labels(km, kmi):
    """Names of the labels the item carries, in the order they were added."""
    items = _kmi_item_labels_all().get((km.name, km.space_type, km.region_type))
    return items.get(kmi.id, []) if items else []


def keymap_selection_labels():
    """Names of the labels carried by any selected item, sorted."""
    names = set()
    for km, kmi in keymap_selection_items():
        names.update(keymap_item_labels(km, kmi))
    return sorted(names)


def keymap_filter_labels():
    """Names of the labels used as a filter, sorted."""
    from bl_keymap_utils import editor_meta
    return tuple(sorted(
        label_name for label_name, use_filter in editor_meta.labels_list() if use_filter
    ))


_kmi_custom_name_cache = None


def _kmi_custom_name_cache_clear():
    global _kmi_custom_name_cache
    _kmi_custom_name_cache = None


_kmi_suggested_name_cache = {}


def _kmi_suggested_name_cache_clear():
    _kmi_suggested_name_cache.clear()


def _kmi_suggested_name(idname, variant):
    """Cached `usage_suggested_name`, cleared every draw."""
    key = (idname, variant)
    name = _kmi_suggested_name_cache.get(key)
    if name is None:
        name = usage_suggested_name(bpy.context, idname, variant) or ""
        _kmi_suggested_name_cache[key] = name
    return name


def keymap_item_search_names(km, kmi):
    """All names the name search matches against."""
    names = [kmi.idname, kmi.name, keymap_item_custom_name(km, kmi)]
    if km.is_modal:
        names.append(keymap_item_label(km, kmi))
    variant = kmi.usage_variant
    if variant:
        names.append(variant)
        names.append(_kmi_suggested_name(kmi.idname, variant))

    seen = set()
    return [
        name for name in names
        if name and not (name in seen or seen.add(name))
    ]


_kmi_addon_name_cache = {}


def keymap_item_is_from_addon(kmi):
    """Whether an add-on added this item."""
    return kmi.is_from_addon or bool(kmi.owner_id)


def keymap_item_addon_name(kmi):
    """Display name of the add-on that added this item, or ""."""
    owner = kmi.owner_id
    if not owner:
        return iface_("Add-on") if kmi.is_from_addon else ""

    name = _kmi_addon_name_cache.get(owner)
    if name is None:
        name = ""
        import sys
        module = sys.modules.get(owner)
        if module is not None:
            import addon_utils
            try:
                name = addon_utils.module_bl_info(module).get("name") or ""
            except Exception:
                # Malformed add-on metadata, ignore.
                name = ""
        if not name or name == owner:
            name = owner.rpartition(".")[2] or owner
        _kmi_addon_name_cache[owner] = name
    return name


def keymap_item_custom_name(km, kmi):
    """The user's custom name for this item, or ""."""
    from bl_keymap_utils import editor_meta
    global _kmi_custom_name_cache
    if _kmi_custom_name_cache is None:
        _kmi_custom_name_cache = editor_meta.custom_names_map()
    named = _kmi_custom_name_cache.get((km.name, km.space_type, km.region_type))
    return named.get(kmi.id, "") if named else ""


_kmi_selection_cache = None

# [(keymap_name, space_type, region_type, item_id), ...] drawn in the last draw, in order.
_kmi_drawn_rows = []
# Row identity of the last plain click, the start of a shift-click range.
_kmi_select_anchor = None


def _kmi_selection_cache_clear():
    global _kmi_selection_cache
    _kmi_selection_cache = None


def keymap_selection_changed():
    """Clear the selection cache and redraw."""
    _kmi_selection_cache_clear()
    _keymap_redraw()


def keymap_visible_items(context=None):
    """[(key map, item), ...] for the rows drawn in the last draw."""
    if context is None:
        context = bpy.context
    if not _kmi_drawn_rows:
        return []

    wanted = {}
    for keymap_name, space_type, region_type, item_id in _kmi_drawn_rows:
        wanted.setdefault((keymap_name, space_type, region_type), set()).add(item_id)

    found = []
    for km in context.window_manager.keyconfigs.user.keymaps:
        km = km.active()
        ids = wanted.get((km.name, km.space_type, km.region_type))
        if not ids:
            continue
        for kmi in km.keymap_items:
            if kmi.id in ids:
                found.append((km, kmi))
    return found


def _kmi_selected_ids():
    """{(keymap_name, space_type, region_type): {item_id, ...}} of the selected items."""
    global _kmi_selection_cache
    if _kmi_selection_cache is None:
        picked = {}
        for entry in bpy.context.window_manager.keymap_selection:
            picked.setdefault(
                (entry.keymap_name, entry.space_type, entry.region_type), set(),
            ).add(entry.item_id)
        _kmi_selection_cache = picked
    return _kmi_selection_cache


def keymap_item_is_selected(km, kmi):
    """Whether the item is selected (edits propagate to the whole selection)."""
    ids = _kmi_selected_ids().get((km.name, km.space_type, km.region_type))
    return (ids is not None) and (kmi.id in ids)


def keymap_selection_count():
    """Number of selected items (without resolving them)."""
    return len(bpy.context.window_manager.keymap_selection)


def keymap_selection_items(kc=None):
    """[(key map, item), ...] for every selected item that still exists."""
    picked = _kmi_selected_ids()
    if not picked:
        return []
    if kc is None:
        kc = bpy.context.window_manager.keyconfigs.user

    found = []
    for km in kc.keymaps:
        km = km.active()
        ids = picked.get((km.name, km.space_type, km.region_type))
        if not ids:
            continue
        for kmi in km.keymap_items:
            if kmi.id in ids:
                found.append((km, kmi))
    return found


def keymap_selection_all_hidden():
    """Whether every selected item is hidden from the usage history."""
    picked = keymap_selection_items()
    if not picked:
        return False
    hidden = _usage_hidden_item_ids()
    return all(
        kmi.id in hidden.get((km.name, km.space_type, km.region_type), ())
        for km, kmi in picked
    )


def _kmi_row_identity(km, kmi):
    """Row identity as stored in `_kmi_drawn_rows`."""
    return (km.name, km.space_type, km.region_type, kmi.id)


def keymap_select_anchor_set(km, kmi):
    """Set the start of a shift-click range."""
    global _kmi_select_anchor
    _kmi_select_anchor = _kmi_row_identity(km, kmi)


def keymap_select_range(context, km, kmi):
    """Select the drawn rows between the anchor and this item (draw order), False if either is not drawn."""
    if _kmi_select_anchor is None:
        return False

    here = _kmi_row_identity(km, kmi)
    rows = _kmi_drawn_rows
    if (_kmi_select_anchor not in rows) or (here not in rows):
        return False

    first, last = sorted((rows.index(_kmi_select_anchor), rows.index(here)))
    drawn = {
        _kmi_row_identity(row_km, row_kmi): (row_km, row_kmi)
        for row_km, row_kmi in keymap_visible_items(context)
    }

    wm = context.window_manager
    for identity in rows[first:last + 1]:
        found = drawn.get(identity)
        if found is not None:
            wm.keymap_selection_set(found[0], found[1], True)
    return True


def keymap_selection_targets(km, kmi, use_selection=False):
    """(key map, item) pairs an edit on this row applies to: the whole selection if the row is selected."""
    if use_selection:
        return keymap_selection_items()
    if keymap_item_is_selected(km, kmi):
        picked = keymap_selection_items()
        if len(picked) > 1:
            return picked
    return [(km, kmi)]


def _kmi_conflict_cache_clear():
    _kmi_conflict_cache.clear()
    _kmi_event_index_cache.clear()


def _kmi_conflict_ids(km):
    """(shadowing, shadowed, shadowed_by, partners) of active items sharing an event in this key map."""
    key = (km.name, km.space_type, km.region_type)
    cached = _kmi_conflict_cache.get(key)
    if cached is not None:
        return cached

    buckets = {}
    type_any = []
    for index, kmi in enumerate(km.keymap_items):
        if not kmi.active:
            continue
        kmi_type = kmi.type
        if kmi_type == 'ANY':
            type_any.append((index, kmi))
            continue
        buckets.setdefault(
            "WHEEL" if kmi_type in _KMI_WHEEL_TYPES else kmi_type, [],
        ).append((index, kmi))

    candidate_lists = [sorted(bucket + type_any) for bucket in buckets.values()]
    if type_any:
        candidate_lists.append(type_any)

    shadowing = set()
    shadowed = set()
    shadowed_by = {}
    partners = {}
    for candidates in candidate_lists:
        for i, (_, kmi) in enumerate(candidates):
            for _, kmi_other in candidates[i + 1:]:
                if kmi.compare(kmi_other):
                    partners.setdefault(kmi.id, set()).add(kmi_other.id)
                    partners.setdefault(kmi_other.id, set()).add(kmi.id)
                    shadowing.add(kmi.id)
                    shadowed.add(kmi_other.id)
                    # Items are matched in order, so the first claimant of an event wins.
                    shadowed_by.setdefault(kmi_other.id, kmi.id)

    result = (shadowing, shadowed, shadowed_by, partners)
    _kmi_conflict_cache[key] = result
    return result


def _kmi_shadowed_ids(km):
    """Ids of items shadowed by an earlier item in the same key map."""
    return _kmi_conflict_ids(km)[1]


def _kmi_shadowed_by(km, item_id):
    """Id of the item shadowing this one, or None."""
    return _kmi_conflict_ids(km)[2].get(item_id)


_kmi_event_index_cache = {}


def _kmi_event_index(km):
    key = (km.name, km.space_type, km.region_type)
    index = _kmi_event_index_cache.get(key)
    if index is None:
        index = {}
        for kmi in km.keymap_items:
            # Only active items can shadow or be shadowed, as in `_kmi_conflict_ids`.
            if not kmi.active:
                continue
            kmi_type = kmi.type
            bucket = "WHEEL" if kmi_type in _KMI_WHEEL_TYPES else kmi_type
            index.setdefault(bucket, []).append(kmi)
        _kmi_event_index_cache[key] = index
    return index


def _kmi_event_answered_in(km_other, kmi):
    """The first item in `km_other` matching this item's event, or None."""
    index = _kmi_event_index(km_other)
    if kmi.type == 'ANY':
        candidates = [candidate for group in index.values() for candidate in group]
    else:
        bucket = "WHEEL" if kmi.type in _KMI_WHEEL_TYPES else kmi.type
        candidates = index.get(bucket, []) + index.get('ANY', [])
    for candidate in candidates:
        if kmi.compare(candidate):
            return candidate
    return None


def _kmi_keymaps_can_conflict(km_a, km_b):
    """Whether two key maps can be active at once (by editor only, mode/tool/poll are unknown here)."""
    if km_a.is_modal or km_b.is_modal:
        return False
    space_a = km_a.space_type
    space_b = km_b.space_type
    return (space_a == 'EMPTY') or (space_b == 'EMPTY') or (space_a == space_b)


# Key maps with window level handlers, offered events after modal, region and area handlers,
# see `wm_window_ghostwindow_ensure` and `wm_event_do_handlers`.
_KMI_KEYMAPS_WINDOW_LEVEL = frozenset({"Window", "Screen"})

_KMI_PRIORITY_WINDOW = 0
_KMI_PRIORITY_REGION = 1


def _kmi_keymap_priority(keymap_name):
    """Event handling priority: window level key maps come after all region key maps (which share a rank)."""
    if keymap_name in _KMI_KEYMAPS_WINDOW_LEVEL:
        return _KMI_PRIORITY_WINDOW
    return _KMI_PRIORITY_REGION


def _kmi_keymap_outranked(keymap_name, keymap_name_other):
    """Whether the other key map is certain to be offered the event first."""
    return _kmi_keymap_priority(keymap_name_other) > _kmi_keymap_priority(keymap_name)


def keymap_clash_is_certain(keymap_name, keymap_name_other, is_same_keymap):
    """
    Whether sharing a key means the item never runs, not only that the key is shared.

    True for the same key map or a key map always offered the event first.
    Shared by the tree and the Add Shortcut dialog so both agree.
    """
    return is_same_keymap or _kmi_keymap_outranked(keymap_name, keymap_name_other)


_KMI_CROSS_CONFLICT_MAX_KEYMAPS = 6

_KMI_CLASH_MAX_KEYMAPS = 4

_kmi_keymap_order_cache = None


def _kmi_keymap_order():
    global _kmi_keymap_order_cache
    if _kmi_keymap_order_cache is not None:
        return _kmi_keymap_order_cache

    from bl_keymap_utils import keymap_hierarchy

    order = {}

    def walk(entries):
        for name, _space_type, _region_type, children in entries:
            order.setdefault(name, len(order))
            walk(children)

    walk(keymap_hierarchy.generate())
    _kmi_keymap_order_cache = order
    return order


def keymap_item_clashes(km, kmi_new):
    """
    Items already bound to this key, in this key map and in key maps that can be active with it.

    Returns [(keymap_name, item_id, label, is_same_keymap), ...], this key map first.
    """
    if kmi_new.type == 'NONE':
        return []

    here = []
    for kmi in km.keymap_items:
        if kmi.id == kmi_new.id or not kmi.active:
            continue
        if kmi.compare(kmi_new):
            here.append((km.name, kmi.id, keymap_item_label(km, kmi), True))
            break

    order = _kmi_keymap_order()
    elsewhere = []
    for km_other in bpy.context.window_manager.keyconfigs.user.keymaps:
        km_other = km_other.active()
        if km_other.name == km.name or not _kmi_keymaps_can_conflict(km, km_other):
            continue
        kmi_other = _kmi_event_answered_in(km_other, kmi_new)
        if kmi_other is not None:
            elsewhere.append((
                km_other.name, kmi_other.id, keymap_item_label(km_other, kmi_other), False,
            ))

    elsewhere.sort(key=lambda entry: order.get(entry[0], len(order)))
    return here + elsewhere


_kmi_cross_conflicts = {}


def _kmi_cross_conflicts_clear():
    _kmi_cross_conflicts.clear()


# {(keymap_name, space_type, region_type, item_id), ...} the conflicts filter was asked to check.
# Set by `preferences.keymap_conflicts_check`, cleared when the filter is turned off.
_kmi_conflict_check = frozenset()


def keymap_conflict_check_set(targets):
    """Set the (key map, item) pairs the conflicts filter checks."""
    global _kmi_conflict_check
    _kmi_conflict_check = frozenset(
        (km.name, km.space_type, km.region_type, kmi.id) for km, kmi in targets
    )


def keymap_conflict_check_clear():
    global _kmi_conflict_check
    _kmi_conflict_check = frozenset()


def keymap_conflict_check_count():
    """Number of items being conflict checked, 0 outside a check."""
    return len(_kmi_conflict_check)


def keymap_item_is_checked(km, kmi):
    """Whether the item is one being conflict checked (not a conflict found)."""
    if not _kmi_conflict_check:
        return False
    return (km.name, km.space_type, km.region_type, kmi.id) in _kmi_conflict_check


def _kmi_cross_conflict_partner(km, kmi):
    """(keymap_name, item_id) of an item in another key map claiming this key, or None (conflicts filter only)."""
    return _kmi_cross_conflicts.get((km.name, km.space_type, km.region_type, kmi.id))


def _kmi_conflict_ids_own_all(display_keymaps, is_own):
    """
    {(keymap_name, space_type, region_type): {item_id, ...}} of conflicts involving `is_own` items.

    Also fills `_kmi_cross_conflicts`.
    """
    keymaps = [km.active() for km, _kc in display_keymaps]
    order = _kmi_keymap_order()
    found = {}

    def add(km, item_id):
        found.setdefault((km.name, km.space_type, km.region_type), set()).add(item_id)

    def add_cross(km, item_id, km_other, item_id_other):
        """Keep the partner whose key map is offered the event first (the one taking the key)."""
        key = (km.name, km.space_type, km.region_type, item_id)
        found = _kmi_cross_conflicts.get(key)
        if found is not None and not _kmi_keymap_outranked(found[0], km_other.name):
            return
        _kmi_cross_conflicts[key] = (km_other.name, item_id_other)

    for km in keymaps:
        owned = [kmi for kmi in km.keymap_items if kmi.active and is_own(km, kmi)]
        if not owned:
            continue

        # Computed only when needed, comparing a key map's items is the expensive part.
        _shadowing, _shadowed, _shadowed_by, partners = _kmi_conflict_ids(km)

        if partners:
            pending = [kmi.id for kmi in owned if kmi.id in partners]
            seen = set()
            while pending:
                item_id = pending.pop()
                if item_id in seen:
                    continue
                seen.add(item_id)
                add(km, item_id)
                pending.extend(partners[item_id] - seen)

        # Conflicts with key maps that can be active at the same time.
        for kmi in owned:
            claimed = []
            for km_other in keymaps:
                if km_other == km or not _kmi_keymaps_can_conflict(km, km_other):
                    continue
                kmi_other = _kmi_event_answered_in(km_other, kmi)
                if kmi_other is not None:
                    claimed.append((km_other, kmi_other))

            # Show the key maps offered the event first, only the display is capped.
            claimed.sort(key=lambda claim: (
                -_kmi_keymap_priority(claim[0].name),
                order.get(claim[0].name, len(order)),
            ))
            for km_other, kmi_other in claimed[:_KMI_CROSS_CONFLICT_MAX_KEYMAPS]:
                add(km, kmi.id)
                add(km_other, kmi_other.id)
                add_cross(km, kmi.id, km_other, kmi_other.id)
                add_cross(km_other, kmi_other.id, km, kmi.id)
                # Include the other item's partners in its own key map.
                _s, _sh, _sb, partners_other = _kmi_conflict_ids(km_other)
                for partner_id in partners_other.get(kmi_other.id, ()):
                    add(km_other, partner_id)
                    add_cross(km_other, partner_id, km, kmi.id)

    return found


# Written as a marker only, `_kmi_clipboard_parse` recognizes items by their shape.
_KMI_CLIPBOARD_KEY = "blender_keymap_item"
# Marker of the multi-item form, holding single items under "items".
_KMI_CLIPBOARD_SET_KEY = "blender_keymap_items"
_KMI_CLIPBOARD_VERSION = 1
_KMI_CLIPBOARD_ARGS = frozenset({
    "type", "value", "any", "shift", "ctrl", "alt", "oskey", "hyper",
    "key_modifier", "direction", "repeat",
})

_KMI_CLIPBOARD_UNREAD = object()
_kmi_clipboard_cache = _KMI_CLIPBOARD_UNREAD


def _kmi_clipboard_cache_clear():
    global _kmi_clipboard_cache
    _kmi_clipboard_cache = _KMI_CLIPBOARD_UNREAD


def _kmi_args_data(kmi):
    args = {"type": kmi.type, "value": kmi.value}
    if kmi.any:
        args["any"] = True
    else:
        for attr in ("shift", "ctrl", "alt", "oskey", "hyper"):
            if mod := getattr(kmi, attr):
                args[attr] = mod  # 1, or -1 for "any state" (KM_ANY).
    if (mod := kmi.key_modifier) and (mod != 'NONE'):
        args["key_modifier"] = mod
    if (direction := kmi.direction) and (direction != 'ANY'):
        args["direction"] = direction
    if kmi.repeat and (
            (kmi.map_type == 'KEYBOARD' and kmi.value in {'PRESS', 'ANY'}) or
            (kmi.map_type == 'TEXTINPUT')
    ):
        args["repeat"] = True
    return args


def _kmi_props_data(properties):
    from bpy.types import OperatorProperties
    data = []
    for pname in properties.bl_rna.properties.keys():
        if pname == "rna_type":
            continue
        value = getattr(properties, pname)
        if isinstance(value, OperatorProperties):
            if sub := _kmi_props_data(value):
                data.append((pname, sub))
        elif properties.is_property_set(pname):
            if isinstance(value, (str, bool, int, float, set)):
                data.append((pname, value))
            elif hasattr(value, "__len__"):
                data.append((pname, tuple(value)))
            # Anything else is not representable, skip.
    return data


def _kmi_props_to_json(data):
    """`_kmi_props_data` output as a JSON object, tagging the values JSON has no type for."""
    out = {}
    for name, value in data:
        if isinstance(value, list):
            value = {"values": _kmi_props_to_json(value)}
        elif isinstance(value, tuple):
            value = {"array": list(value)}
        elif isinstance(value, set):
            value = {"flags": sorted(value)}
        out[name] = value
    return out


def _kmi_props_from_json(data):
    """Inverse of `_kmi_props_to_json`."""
    if not isinstance(data, dict):
        raise ValueError("properties must be an object")
    out = []
    for name, value in data.items():
        if isinstance(value, dict):
            if (nested := value.get("values")) is not None:
                value = _kmi_props_from_json(nested)
            elif (array := value.get("array")) is not None:
                if not isinstance(array, list) or not all(
                        isinstance(v, (str, bool, int, float)) for v in array):
                    raise ValueError("array property must hold simple values")
                value = tuple(array)
            elif (flags := value.get("flags")) is not None:
                if not isinstance(flags, list) or not all(isinstance(v, str) for v in flags):
                    raise ValueError("flag property must hold strings")
                value = set(flags)
            else:
                raise ValueError("unknown tagged property value")
        elif not isinstance(value, (str, bool, int, float)):
            raise ValueError("unsupported property value")
        out.append((name, value))
    return out


def _kmi_clipboard_parse(text):
    """
    Key map items found in clipboard text, or None.

    Items are recognized by shape (an event under "args" and an operator or modal action),
    not by the surrounding JSON, which is often broken by pasting through messages.
    """
    import json

    # Cheap rejection, every item written here has "args".
    if "\"args\"" not in text:
        return None

    decoder = json.JSONDecoder()
    clips = []
    index = 0
    while (index := text.find("{", index)) != -1:
        try:
            data, end = decoder.raw_decode(text, index)
        except ValueError:
            # Not a complete object here, step in to find nested items.
            index += 1
            continue
        clip = _kmi_clipboard_parse_one(data) if isinstance(data, dict) else None
        if clip is None:
            # A wrapper or unrelated object, look inside.
            index += 1
            continue
        clips.append(clip)
        # Skip the item's contents.
        index = end
    return clips or None


def _kmi_clipboard_parse_one(data):
    """One item from a clipboard object, or None when it is not one."""
    args = data.get("args")
    # The event identifies an item, see `_kmi_args_data`.
    if not (isinstance(args, dict) and isinstance(args.get("type"), str)):
        return None

    modal = data.get("modal")
    if modal is not None:
        propvalue = data.get("propvalue")
        if not (isinstance(modal, str) and modal):
            return None
        if not (isinstance(propvalue, str) and propvalue):
            return None
        idname = ""
        properties = []
        available = True
    else:
        modal = None
        propvalue = ""
        idname = data.get("idname")
        if not isinstance(idname, str):
            return None
        try:
            properties = _kmi_props_from_json(data.get("properties", {}))
        except ValueError:
            return None
        available = bool(_is_operator_available(idname))

    # Source key map, for pasting when no key map is under the cursor.
    source = None
    keymap_name = data.get("keymap")
    if isinstance(keymap_name, str) and keymap_name:
        space_type = data.get("space_type")
        region_type = data.get("region_type")
        if isinstance(space_type, str) and isinstance(region_type, str):
            source = (keymap_name, space_type, region_type)

    label = data.get("label")
    name = data.get("name")
    return {
        "idname": idname,
        "name": name if (isinstance(name, str) and name) else "",
        # None for an operator binding, the source key map's name for a modal one.
        "modal": modal,
        "propvalue": propvalue,
        # (name, space_type, region_type) of the source key map, None for older text.
        "source": source,
        "args": {
            key: value for key, value in args.items()
            if key in _KMI_CLIPBOARD_ARGS and isinstance(value, (str, bool, int))
        },
        "properties": properties,
        "active": data.get("active") is not False,
        # Shown on the paste button only.
        "label": label if (isinstance(label, str) and label) else (idname or propvalue),
        "available": available,
    }


def keymap_item_clipboard(use_cache=True):
    """Key map items on the clipboard, or None."""
    global _kmi_clipboard_cache
    if use_cache and (_kmi_clipboard_cache is not _KMI_CLIPBOARD_UNREAD):
        return _kmi_clipboard_cache
    clips = _kmi_clipboard_parse(bpy.context.window_manager.clipboard)
    _kmi_clipboard_cache = clips
    return clips


def keymap_clipboard_label(clips):
    """Paste button label: the item's label, or the item count."""
    if not clips:
        return ""
    if len(clips) == 1:
        return clips[0]["label"]
    return iface_("{:d} Shortcuts").format(len(clips))


def keymap_clipboard_sources(clips, kc=None):
    """
    [(key map, clipboard item), ...] for items whose source key map still exists.

    Used to paste when no key map is drawn, e.g. when the filters leave the tree empty.
    """
    if not clips:
        return []
    if kc is None:
        kc = bpy.context.window_manager.keyconfigs.user

    keymaps = {}
    for km in kc.keymaps:
        km = km.active()
        keymaps.setdefault((km.name, km.space_type, km.region_type), km)

    found = []
    for clip in clips:
        km = keymaps.get(clip["source"]) if clip["source"] else None
        if (km is not None) and keymap_item_clipboard_compatible(km, clip):
            found.append((km, clip))
    return found


def keymap_clipboard_source_label(sources):
    """Paste button label for pasting into the source key maps."""
    if not sources:
        return ""
    names = {km.name for km, _clip in sources}
    if len(sources) == 1:
        return iface_("Paste \"{:s}\" into {:s}").format(sources[0][1]["label"],
                                                         sources[0][0].name)
    if len(names) == 1:
        return iface_("Paste {:d} Shortcuts into {:s}").format(len(sources), next(iter(names)))
    return iface_("Paste {:d} Shortcuts into {:d} Key Maps").format(len(sources), len(names))


def keymap_item_modal_actions(km):
    """The modal action identifiers `km` accepts, or None when they are unknown."""
    actions = {event.identifier for event in km.modal_event_values}
    return None if actions == {"NONE"} else actions


def keymap_item_label(km, kmi):
    """The name the item is drawn with."""
    if not km.is_modal:
        return keymap_item_custom_name(km, kmi) or kmi.name or kmi.idname
    propvalue = kmi.propvalue
    for event in km.modal_event_values:
        if event.identifier == propvalue:
            return event.name or propvalue
    return propvalue


def keymap_item_clipboard_set(km, kmi):
    """Copy a key map item to the clipboard as text."""
    keymap_items_clipboard_set(((km, kmi),))


def keymap_items_clipboard_set(pairs):
    """Copy (key map, item) pairs to the clipboard as text."""
    import json
    pairs = list(pairs)
    if len(pairs) == 1:
        km, kmi = pairs[0]
        # A single item keeps the plain form, for compatibility.
        data = _kmi_clipboard_data(km, kmi)
        data = {_KMI_CLIPBOARD_KEY: _KMI_CLIPBOARD_VERSION, **data}
    else:
        data = {
            _KMI_CLIPBOARD_SET_KEY: _KMI_CLIPBOARD_VERSION,
            "items": [_kmi_clipboard_data(km, kmi) for km, kmi in pairs],
        }

    # `WM_clipboard_text_set` converts newlines for the platform.
    bpy.context.window_manager.clipboard = _kmi_clipboard_text(data)
    _kmi_clipboard_cache_clear()


def _kmi_clipboard_text(data):
    """
    `data` as readable JSON, one field per line with nested values kept inline.

    `json.dumps(indent=...)` would break every nested value onto its own line.
    """
    import json

    def fields(item, indent):
        pad = " " * indent
        return ",\n".join(
            "{:s}{:s}: {:s}".format(pad, json.dumps(name), json.dumps(value))
            for name, value in item.items()
        )

    items = data.get("items")
    if items is None:
        return "{{\n{:s}\n}}".format(fields(data, 2))

    head = {name: value for name, value in data.items() if name != "items"}
    blocks = ",\n".join("    {{\n{:s}\n    }}".format(fields(item, 6)) for item in items)
    return "{{\n{:s},\n  \"items\": [\n{:s}\n  ]\n}}".format(fields(head, 2), blocks)


def _kmi_clipboard_data(km, kmi):
    """Clipboard data for one item."""
    # Human readable fields first (dict order is kept when written).
    data = {
        "label": keymap_item_label(km, kmi),
        "key": kmi.to_string(),
        # Source key map, see `keymap_clipboard_sources`.
        "keymap": km.name,
        "space_type": km.space_type,
        "region_type": km.region_type,
    }
    if km.is_modal:
        data["modal"] = km.name
        data["propvalue"] = kmi.propvalue
        data["args"] = _kmi_args_data(kmi)
    else:
        data["idname"] = kmi.idname
        if custom_name := keymap_item_custom_name(km, kmi):
            data["name"] = custom_name
        data["args"] = _kmi_args_data(kmi)
        data["properties"] = _kmi_props_to_json(_kmi_props_data(kmi.properties))
    data["active"] = kmi.active
    return data


def keymap_item_clipboard_compatible(km, clip):
    """Whether one clipboard item can be pasted into `km`."""
    if clip is None:
        return False
    if km.is_modal != (clip["modal"] is not None):
        return False
    if not km.is_modal:
        return True
    actions = keymap_item_modal_actions(km)
    return (actions is None) or (clip["propvalue"] in actions)


def keymap_clipboard_pasteable(km, clips):
    """The clipboard items compatible with `km`."""
    if not clips:
        return []
    return [clip for clip in clips if keymap_item_clipboard_compatible(km, clip)]


def _kmi_signature(km, kmi):
    """Comparable identity of an item, see `_kmi_clipboard_signature`."""
    if km.is_modal:
        what = ("modal", kmi.propvalue)
    else:
        props = kmi.properties
        what = (
            "op", kmi.idname,
            repr(_kmi_props_to_json(_kmi_props_data(props))) if props is not None else "",
        )
    return (what, repr(sorted(_kmi_args_data(kmi).items())), kmi.active)


def _kmi_clipboard_signature(clip):
    """`_kmi_signature` of a clipboard item."""
    if clip["modal"] is not None:
        what = ("modal", clip["propvalue"])
    else:
        what = ("op", clip["idname"], repr(_kmi_props_to_json(clip["properties"])))
    return (what, repr(sorted(clip["args"].items())), clip["active"])


def _kmi_copy_name(km, base):
    """A "(copy)" name from `base` not used by any item in `km`."""
    from itertools import count
    name = iface_("{:s} (copy)").format(base)
    taken = {keymap_item_label(km, kmi) for kmi in km.keymap_items}
    if name not in taken:
        return name
    for number in count(2):
        numbered = iface_("{:s} (copy {:d})").format(base, number)
        if numbered not in taken:
            return numbered


def keymap_item_clipboard_paste(km, clip):
    """Recreate one clipboard item in `km`."""
    if clip is None:
        return None

    if clip["modal"] is not None:
        candidates = (kmi for kmi in km.keymap_items if kmi.propvalue == clip["propvalue"])
    else:
        candidates = (kmi for kmi in km.keymap_items if kmi.idname == clip["idname"])
    signature = _kmi_clipboard_signature(clip)
    duplicate_of = next(
        (kmi for kmi in candidates if _kmi_signature(km, kmi) == signature), None)

    if clip["modal"] is not None:
        kmi = km.keymap_items.new_modal(clip["propvalue"], **clip["args"])
    else:
        kmi = km.keymap_items.new(clip["idname"], head=True, **clip["args"])
    if not clip["active"]:
        kmi.active = False
    if clip["properties"]:
        from bl_keymap_utils.io import _init_properties_from_data
        _init_properties_from_data(kmi.properties, clip["properties"])

    if duplicate_of is not None:
        kmi.is_user_duplicate = True
        if not km.is_modal:
            from bl_keymap_utils import editor_meta
            base = clip["name"] or keymap_item_custom_name(km, duplicate_of) or duplicate_of.name
            editor_meta.custom_name_set(km, kmi, _kmi_copy_name(km, base))
            _kmi_custom_name_cache_clear()
    elif clip["name"] and not km.is_modal:
        from bl_keymap_utils import editor_meta
        editor_meta.custom_name_set(km, kmi, clip["name"])
        _kmi_custom_name_cache_clear()
    return kmi


def _is_operator_available(idname):
    module, _, operator = idname.partition(".")
    if not (module and operator):
        return False

    try:
        getattr(getattr(bpy.ops, module), operator).get_rna_type()
    except (AttributeError, KeyError):
        return False
    return True


def _indented_layout(layout, level):
    indentpx = 16
    if level == 0:
        level = 0.0001   # Tweak so that a percentage of 0 won't split by half
    indent = level * indentpx / bpy.context.region.width

    split = layout.split(factor=indent)
    col = split.column()
    col = split.column()
    return col


def draw_entry(display_keymaps, entry, col, level=0):
    idname, spaceid, regionid, children = entry

    for km, kc in display_keymaps:
        if km.name == idname and km.space_type == spaceid and km.region_type == regionid:
            draw_km(display_keymaps, kc, km, children, col, level)

    '''
    km = kc.keymaps.find(idname, space_type=spaceid, region_type=regionid)
    if not km:
        kc = defkc
        km = kc.keymaps.find(idname, space_type=spaceid, region_type=regionid)

    if km:
        draw_km(kc, km, children, col, level)
    '''


def draw_km(display_keymaps, kc, km, children, layout, level):
    km = km.active()

    layout.context_pointer_set("keymap", km)

    _kmi_row_mark(_kmi_row_key_keymap(km))
    subcol = _indented_layout(layout, level)
    row = subcol.row(align=True)
    if km.name in _kmi_flash_km_names:
        row.warning = True
    row.prop(km, "show_expanded_children", text="", emboss=False)
    row.label(text=km.name, text_ctxt=i18n_contexts.id_windowmanager)

    if km.is_user_modified or km.is_modal:
        subrow = row.row()
        subrow.alignment = 'RIGHT'

        if km.is_user_modified:
            subrow.operator("preferences.keymap_restore", text="Restore")
            # Add margin to space the button from the scroll-bar.
            subrow.separator()
        if km.is_modal:
            subrow.label(text="", icon='LINKED')
        del subrow
    _kmi_row_advance(1.0)

    if km.show_expanded_children:
        col = layout.column()
        if children:
            # Put the Parent key map's entries in a 'global' sub-category
            # equal in hierarchy to the other children categories
            subcol = _indented_layout(col, level + 1)
            subrow = subcol.row(align=True)
            subrow.prop(km, "show_expanded_items", text="", emboss=False)
            subrow.label(
                text=iface_("{:s} (Global)").format(iface_(km.name, i18n_contexts.id_windowmanager)),
                translate=False,
            )
            _kmi_row_advance(1.0)
        else:
            km.show_expanded_items = True

        # Key Map items
        if km.show_expanded_items:
            kmi_level = level + 2 if children else level + 1

            subcol = _indented_layout(col, kmi_level)
            subrow = subcol.split(factor=0.4).row(align=True)
            subrow.operator(
                "preferences.keyitem_add",
                text="Add New",
                text_ctxt=i18n_contexts.id_windowmanager,
                icon='ADD',
            )
            pasteable = keymap_clipboard_pasteable(km, keymap_item_clipboard())
            sub = subrow.row(align=True)
            sub.enabled = bool(pasteable)
            sub.operator(
                "preferences.keyitem_paste",
                text=(
                    iface_("Paste \"{:s}\"").format(keymap_clipboard_label(pasteable))
                    if pasteable else iface_("Paste")
                ),
                translate=False,
                icon='PASTEDOWN',
            )
            _kmi_row_advance(1.0)

            for kmi in km.keymap_items:
                draw_kmi(display_keymaps, kc, km, kmi, col, kmi_level)
            col.separator()
            _kmi_row_advance(_KMI_ROW_SEPARATOR)

        # Child key maps
        if children:
            for entry in children:
                draw_entry(display_keymaps, entry, col, level + 1)

        col.separator()
        _kmi_row_advance(_KMI_ROW_SEPARATOR)


def draw_kmi(display_keymaps, kc, km, kmi, layout, level, use_local_expand=False):
    map_type = kmi.map_type
    is_op_available = _is_operator_available(kmi.idname)
    is_selected = keymap_item_is_selected(km, kmi)
    _kmi_drawn_rows.append((km.name, km.space_type, km.region_type, kmi.id))
    _kmi_row_mark(_kmi_row_key_item(km, kmi))
    # An expanded row's height depends on its properties, only collapsed rows are counted exactly.
    _kmi_row_advance(1.0)

    # The filtered view keeps its own expansion state, see `_kmi_filtered_expanded`.
    if use_local_expand:
        is_expanded = _kmi_filtered_expanded_key(km, kmi) in _kmi_filtered_expanded
    else:
        is_expanded = kmi.show_expanded

    col = _indented_layout(layout, level)

    if _kmi_row_is_flashing(km, kmi):
        col.warning = True

    if _kmi_reveal_target == _kmi_row_key_item(km, kmi):
        col.warning = True

    stale_ids = _kmi_filter_stale.get((km.name, km.space_type, km.region_type))
    if stale_ids is not None and kmi.id in stale_ids:
        col.info = True

    # Set last and in red, so it shows over any other highlight.
    if _kmi_conflict_flash_target == _kmi_row_key_item(km, kmi):
        col.alert = True

    # Items being conflict checked get a frame (expanded rows already have one).
    if is_expanded:
        col = col.column(align=True)
        box = col.box()
    elif keymap_item_is_checked(km, kmi):
        box = col.box()
    else:
        box = col.column()

    # For the context menu of this row's buttons.
    box.context_pointer_set("keymap_item", kmi)

    split = box.split()

    # header bar
    row = split.row(align=True)
    if use_local_expand:
        props = row.operator(
            "preferences.keyitem_expand",
            text="",
            icon='DISCLOSURE_TRI_DOWN' if is_expanded else 'DISCLOSURE_TRI_RIGHT',
            emboss=False,
        )
        props.keymap_name = km.name
        props.item_id = kmi.id
    else:
        row.prop(kmi, "show_expanded", text="", emboss=False)
    row.prop(kmi, "active", text="", emboss=False)

    if km.is_modal:
        # Modal rows show a menu instead of a name, so use a separate select toggle.
        props = row.operator(
            "preferences.keyitem_select",
            text="",
            icon='RADIOBUT_ON' if is_selected else 'RADIOBUT_OFF',
            emboss=False,
        )
        props.item_id = kmi.id
        props.idname = kmi.idname
        props.use_local_expand = use_local_expand
        row.separator()
        row.alert = not kmi.propvalue
        row.prop(kmi, "propvalue", text="")
    else:
        if is_op_available:
            sub = row.row(align=True)
            sub.alignment = 'LEFT'
            custom_name = keymap_item_custom_name(km, kmi)
            props = sub.operator(
                "preferences.keyitem_select",
                text=custom_name or kmi.name,
                translate=not custom_name,
                # Selected rows are drawn pressed, others flat.
                emboss=is_selected,
                depress=is_selected,
            )
            props.item_id = kmi.id
            props.idname = kmi.idname
            props.use_local_expand = use_local_expand
            if custom_name:
                sub = row.row(align=True)
                sub.alignment = 'LEFT'
                sub.active = False
                sub.label(text=kmi.name)
        # The default item when adding a new item is "none"
        # so consider this unassigned along with an empty string.
        elif kmi.idname in {"none", ""}:
            row.alert = True
            sub = row.row(align=True)
            sub.alignment = 'LEFT'
            props = sub.operator(
                "preferences.keyitem_select",
                text="(Unassigned)",
                emboss=is_selected,
                depress=is_selected,
            )
            props.item_id = kmi.id
            props.idname = kmi.idname
            props.use_local_expand = use_local_expand
        else:
            row.alert = True
            sub = row.row(align=True)
            sub.alignment = 'LEFT'
            props = sub.operator(
                "preferences.keyitem_select",
                text=rpt_("{:s} (unavailable)").format(kmi.idname),
                icon='STATUS_WARNING',
                translate=False,
                emboss=is_selected,
                depress=is_selected,
            )
            props.item_id = kmi.id
            props.idname = kmi.idname
            props.use_local_expand = use_local_expand

    addon_name = keymap_item_addon_name(kmi)
    if addon_name:
        sub = row.row(align=True)
        sub.alignment = 'LEFT'
        sub.active = False
        sub.label(text=addon_name, translate=False)

    labels = keymap_item_labels(km, kmi)
    if labels:
        sub = row.row(align=True)
        sub.alignment = 'LEFT'
        sub.active = False
        sub.label(text=", ".join(labels), translate=False, icon='TAG')

    row = split.row()
    key_row = row
    if kmi.intent:
        # Bound through an intent: the key comes from the intent, editing it here detaches the item.
        # The label shows the intent in the intents column, the link button detaches.
        intent = kc.intents.get(kmi.intent)
        subrow = row.row(align=True)
        subrow.operator(
            "preferences.keyitem_intent_detach",
            text="",
            icon='LINKED',
            emboss=False,
        ).item_id = kmi.id
        subrow.operator(
            "preferences.keyintent_reveal",
            text=iface_(intent.label) if intent else kmi.intent,
            translate=False,
            emboss=False,
        ).intent = kmi.intent
        key_row = row.row()
        key_row.active = False
    key_row.prop(kmi, "map_type", text="")

    event_row = key_row.row(align=True)
    if map_type == 'KEYBOARD':
        event_row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'MOUSE':
        event_row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'NDOF':
        event_row.prop(kmi, "type", text="", full_event=True)
    elif map_type == 'TWEAK':
        subrow = event_row.row()
        subrow.prop(kmi, "type", text="")
        subrow.prop(kmi, "value", text="")
    elif map_type == 'TIMER':
        event_row.prop(kmi, "type", text="")
    else:
        event_row.label()

    key_string = kmi.to_string()
    subrow = event_row.row(align=True)
    subrow.enabled = bool(key_string)
    props = subrow.operator("preferences.keymap_activity_find", text="", icon='VIEWZOOM')
    props.filter_type = 'KEY'
    props.filter_text = key_string
    props.use_exact = True

    is_shadowed = (
        (kmi.is_user_defined or _kmi_conflicts_view) and
        (kmi.id in _kmi_shadowed_ids(km))
    )
    # Shadowed inside the key map is certain (the item never runs), a claim from another key map
    # only possible. Both are marked, but only `is_shadowed` offers `preferences.keyitem_unshadow`.
    if is_shadowed:
        clash_with = (km.name, _kmi_shadowed_by(km, kmi.id))
    elif _kmi_conflicts_view:
        clash_with = _kmi_cross_conflict_partner(km, kmi)
    else:
        clash_with = None

    if clash_with is not None and clash_with[1] is not None:
        # Same rule as the Add Shortcut dialog.
        is_lost = keymap_clash_is_certain(km.name, clash_with[0], is_shadowed)
        is_outranked = is_lost and not is_shadowed
        subrow = row.row(align=True)
        subrow.alert = is_lost
        props = subrow.operator(
            "preferences.keyitem_flash_conflict",
            text="",
            icon='ERROR' if is_lost else 'INFO',
            emboss=False,
        )
        props.keymap_name = clash_with[0]
        props.item_id = clash_with[1]
        props.is_outranked = is_outranked
        # Source row, so the check can run from here when the target is not drawn.
        props.source_keymap_name = km.name
        props.source_item_id = kmi.id

    if (not kmi.is_user_defined) and kmi.is_user_modified:
        row.operator("preferences.keyitem_restore", text="", icon='BACK').item_id = kmi.id
    else:
        row.operator(
            "preferences.keyitem_remove",
            text="",
            # Abusing the tracking icon, but it works pretty well here.
            icon=('TRACKING_CLEAR_BACKWARDS' if kmi.is_user_defined else 'X')
        ).item_id = kmi.id

    # Add margin to space the buttons from the scroll-bar.
    row.separator(factor=0.25 if is_expanded else 1.0)

    # Expanded, additional event settings
    if is_expanded:
        from _bpy import _wm_capabilities
        capabilities = _wm_capabilities()

        box = col.box()

        if not km.is_modal:
            name_row = box.row(align=True)
            custom_name = keymap_item_custom_name(km, kmi)
            name_row.label(
                text=iface_("Name: {:s}").format(custom_name or kmi.name),
                translate=False,
            )
            props = name_row.operator(
                "preferences.keyitem_rename",
                text="",
                icon='GREASEPENCIL',
            )
            props.item_id = kmi.id
            box.separator(factor=0.5)

        split = box.split(factor=box.property_split_factor)
        sub = split.row()

        if km.is_modal:
            sub.alert = not kmi.propvalue
            sub.prop(kmi, "propvalue", text="")
        else:
            subrow = sub.row()
            subrow.alert = not is_op_available
            subrow.prop(kmi, "idname", text="", placeholder="Operator")

        if map_type not in {'TEXTINPUT', 'TIMER'}:
            from sys import platform

            sub = split.column()
            subrow = sub.row(align=True)

            if map_type == 'KEYBOARD':
                subrow.prop(kmi, "type", text="", event=True)
                subrow.prop(kmi, "value", text="")
                subrow_repeat = subrow.row(align=True)
                subrow_repeat.active = kmi.value in {'ANY', 'PRESS'}
                subrow_repeat.prop(kmi, "repeat", text="Repeat")
            elif map_type in {'MOUSE', 'NDOF'}:
                subrow.prop(kmi, "type", text="")
                subrow.prop(kmi, "value", text="")

            if map_type in {'KEYBOARD', 'MOUSE'} and kmi.value == 'CLICK_DRAG':
                subrow = sub.row()
                subrow.prop(kmi, "direction")

            subrow = sub.row()
            subrow.scale_x = 0.75
            subrow.prop(kmi, "any", toggle=True)

            # Match text in `WM_key_event_string`.
            match platform:
                case "darwin":
                    oskey_label = "Cmd"
                case "win32":
                    oskey_label = "Win"
                case _:
                    oskey_label = "OS"

            # Use `*_ui` properties as integers aren't practical.
            subrow.prop(kmi, "shift_ui", toggle=True)
            subrow.prop(kmi, "ctrl_ui", toggle=True)
            subrow.prop(kmi, "alt_ui", toggle=True)
            subrow.prop(kmi, "oskey_ui", text=oskey_label, toggle=True)

            # On systems that don't support Hyper, only show if it's enabled.
            # Otherwise the user may have a key binding that doesn't work and can't be changed.
            if capabilities['KEYBOARD_HYPER_KEY'] or kmi.hyper == 1:
                subrow.prop(kmi, "hyper_ui", text="Hyper", toggle=True)

            subrow.prop(kmi, "key_modifier", text="", event=True)

        if not km.is_modal:
            subrow = box.row()
            subrow.prop_search(kmi, "intent", kc, "intents", text="Shared Shortcut", icon='LINKED')

        # Operator properties
        box.template_keymap_item_properties(kmi)

        if is_shadowed:
            subrow = box.row(align=True)
            subrow.operator(
                "preferences.keyitem_unshadow",
                text="Override Conflicts",
                icon='ERROR',
            ).item_id = kmi.id

        # Modal key maps attached to this operator
        if not km.is_modal:
            kmm = kc.keymaps.find_modal(kmi.idname)
            if kmm:
                draw_km(display_keymaps, kc, kmm, None, layout, level + 1)
                layout.context_pointer_set("keymap", km)


_EVENT_TYPES = set()
_EVENT_TYPE_MAP = {}
_EVENT_TYPE_MAP_EXTRA = {}
_EVENT_TYPE_MAP_I18N = {}

_MODIFIER_ALIASES = {}
_VALUE_ALIASES = {}

_search_tables_language_init = None


def _init_search_tables():
    # Build all search lookup tables once from bl_rna enums + translations.
    global _search_tables_language_init

    current_language = bpy.context.preferences.view.language
    if _search_tables_language_init == current_language:
        return

    _search_tables_language_init = current_language

    _EVENT_TYPES.clear()
    _EVENT_TYPE_MAP.clear()
    _EVENT_TYPE_MAP_EXTRA.clear()
    _EVENT_TYPE_MAP_I18N.clear()
    _MODIFIER_ALIASES.clear()
    _VALUE_ALIASES.clear()

    from sys import platform

    # Event type tables.
    enum = bpy.types.Event.bl_rna.properties["type"].enum_items
    _EVENT_TYPES.update(enum.keys())
    _EVENT_TYPE_MAP.update({
        item.name.replace(" ", "_").upper(): key
        for key, item in enum.items()
    })

    # Translated event type names (only entries that differ from English).
    # Match context used by WM_key_event_string.
    for key, item in enum.items():
        translated = iface_(item.name, i18n_contexts.ui_events_keymaps)
        if translated != item.name:
            _EVENT_TYPE_MAP_I18N[translated.replace(" ", "_").upper()] = key

    del enum

    _EVENT_TYPE_MAP_EXTRA.update({
        "`": 'ACCENT_GRAVE',
        "*": 'NUMPAD_ASTERIX',
        "/": 'NUMPAD_SLASH',
        '+': 'NUMPAD_PLUS',
        "-": 'NUMPAD_MINUS',
        ".": 'NUMPAD_PERIOD',
        "'": 'QUOTE',
        "RMB": 'RIGHTMOUSE',
        "LMB": 'LEFTMOUSE',
        "MMB": 'MIDDLEMOUSE',
    })
    _EVENT_TYPE_MAP_EXTRA.update({
        "{:d}".format(i): "NUMPAD_{:d}".format(i) for i in range(10)
    })

    #  Modifier {alias: kmi_attribute}
    _MODIFIER_ALIASES.update({
        "ctrl": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "oskey": "oskey",
        "hyper": "hyper",
        "any": "any",

        # macOS specific modifiers names
        "control": "ctrl",
        "option": "alt",
        "cmd": "oskey",
        "command": "oskey",
    })

    match platform:
        case "darwin":
            pass  # "cmd" already mapped above
        case "win32":
            _MODIFIER_ALIASES["win"] = "oskey"
        case _:
            _MODIFIER_ALIASES["os"] = "oskey"

    # Translated modifier labels (e.g. "Maj" -> "shift" in French).
    # Match contexts used by WM_key_event_string.
    for english_label, attr, ctx in (
        ("Shift", "shift", i18n_contexts.id_windowmanager),
        ("Ctrl", "ctrl", None),
        ("Alt", "alt", None),
        ("Cmd", "oskey", None),
        ("Win", "oskey", None),
        ("OS", "oskey", None),
        ("Hyper", "hyper", None),
        ("Any", "any", None),
    ):
        translated = iface_(english_label, ctx).lower()
        if translated not in _MODIFIER_ALIASES:
            _MODIFIER_ALIASES[translated] = attr

    # Event value {alias: enum_identifier}
    _VALUE_ALIASES.update({
        "dbl": "DOUBLE_CLICK",
        "double": "DOUBLE_CLICK",
        "doubleclick": "DOUBLE_CLICK",
        "double_click": "DOUBLE_CLICK",
        "press": "PRESS",
        "release": "RELEASE",
        "click": "CLICK",
        "drag": "CLICK_DRAG",
        "clickdrag": "CLICK_DRAG",
        "click_drag": "CLICK_DRAG",
    })

    # Translated event value names from bl_rna.
    value_prop = bpy.types.Event.bl_rna.properties["value"]
    value_enum = value_prop.enum_items
    for key, item in value_enum.items():
        english_norm = item.name.replace(" ", "").replace("-", "").lower()
        if english_norm not in _VALUE_ALIASES:
            _VALUE_ALIASES[english_norm] = key
        translated = iface_(item.name, value_prop.translation_context)
        if translated != item.name:
            translated_norm = translated.replace(" ", "").replace("-", "").lower()
            if translated_norm not in _VALUE_ALIASES:
                _VALUE_ALIASES[translated_norm] = key
    del value_prop, value_enum


def draw_filtered(
        display_keymaps,
        filter_type,
        filter_text,
        layout,
        filter_user_modified=False,
        filter_conflicts=False,
        filter_labels=(),
        filter_addon=False,
        filter_key_exact=False,
):

    if filter_type == 'NAME':
        def filter_func(km, kmi):
            return any(
                filter_text in name.lower()
                for name in keymap_item_search_names(km, kmi)
            )
    else:
        _init_search_tables()

        filter_text_split = filter_text.split()

        # KeyMapItem like dict, use for comparing against
        # attr: {states, ...}
        kmi_test_dict = {}
        # Special handling of 'type' using a list if sets,
        # keymap items must match against all.
        kmi_test_type = []

        # altname: attr
        remaining = []
        for token in filter_text_split:
            attr = _MODIFIER_ALIASES.get(token)
            if attr is not None:
                kmi_test_dict[attr] = {True}
            else:
                remaining.append(token)
        filter_text_split = remaining

        # Recognize event value prefixes (e.g. "dbl-a", "press a").
        normalized_tokens = []
        for token in filter_text_split:
            prefix, sep, rest = token.partition("-")

            if sep:
                # "dbl-a", "drag-left" -> check prefix as event value.
                val = _VALUE_ALIASES.get(prefix)
                if val is not None:
                    kmi_test_dict.setdefault("value", set()).add(val)
                    if rest:
                        normalized_tokens.append(rest)
                    continue

            # Try the whole token as an event value (e.g. "press", "release").
            val = _VALUE_ALIASES.get(token)
            if val is not None:
                kmi_test_dict.setdefault("value", set()).add(val)
                continue

            # Not a value -> keep as an event type token.
            normalized_tokens.append(token)

        filter_text_split = normalized_tokens

        # what's left should be the event type
        def kmi_type_set_from_string(kmi_type):
            kmi_type = kmi_type.upper()
            kmi_type_set = set()

            if kmi_type in _EVENT_TYPES:
                kmi_type_set.add(kmi_type)

            if not kmi_type_set or len(kmi_type) > 1:
                # replacement table
                for event_type_map in (_EVENT_TYPE_MAP, _EVENT_TYPE_MAP_I18N, _EVENT_TYPE_MAP_EXTRA):
                    kmi_type_test = event_type_map.get(kmi_type)
                    if kmi_type_test is not None:
                        kmi_type_set.add(kmi_type_test)
                    else:
                        # print("Unknown Type:", kmi_type)

                        # Partial match
                        for k, v in event_type_map.items():
                            if (kmi_type in k) or (kmi_type in v):
                                kmi_type_set.add(v)
            return kmi_type_set

        for kmi_type in filter_text_split:
            kmi_type_set = kmi_type_set_from_string(kmi_type)

            if not kmi_type_set:
                return False

            kmi_test_type.append(kmi_type_set)
        # tiny optimization, sort sets so the smallest is first
        # improve chances of failing early
        kmi_test_type.sort(key=lambda kmi_type_set: len(kmi_type_set))

        exact = filter_key_exact and "any" not in kmi_test_dict
        exact_off = tuple(
            attr for attr in ("shift", "ctrl", "alt", "oskey", "hyper")
            if attr not in kmi_test_dict
        ) if exact else ()
        exact_values = ('DOUBLE_CLICK', 'CLICK_DRAG') if (
            exact and "value" not in kmi_test_dict) else ()

        def filter_func(_km, kmi):
            for kk, ki in kmi_test_dict.items():
                val = getattr(kmi, kk)
                if val not in ki:
                    return False

            if exact:
                for attr in exact_off:
                    if getattr(kmi, attr) != 0:
                        return False
                if kmi.value in exact_values:
                    return False
                key_modifier = kmi.key_modifier
                if key_modifier != 'NONE':
                    if not any(key_modifier in ki for ki in kmi_test_type):
                        return False

            # special handling of 'type'
            for ki in kmi_test_type:
                val = kmi.type
                if val == 'NONE' or val not in ki:
                    # exception for 'type'
                    # also inspect 'key_modifier' as a fallback
                    val = kmi.key_modifier
                    if not (val == 'NONE' or val not in ki):
                        continue
                    return False

            return True

    filter_func_text = filter_func

    filter_own = filter_user_modified or bool(filter_labels) or filter_addon
    filter_checked = bool(_kmi_conflict_check)

    # Cross key map conflicts compare an item against every key map, so they need a narrowed
    # set of items to start from: a checked group, the ownership filters or a search.
    filter_conflicts_cross = filter_conflicts and (
        filter_checked or filter_own or bool(filter_text))

    def _is_personal(km, kmi):
        """Whether the item passes the customized, label and add-on filters."""
        if filter_user_modified and not (kmi.is_user_modified or kmi.is_user_defined):
            return False
        if filter_labels and not any(
                label in filter_labels for label in keymap_item_labels(km, kmi)):
            return False
        if filter_addon and not keymap_item_is_from_addon(kmi):
            return False
        return True

    def _is_conflict_seed(km, kmi):
        """Whether the item seeds the cross key map conflict walk: the checked group if set, else the view."""
        if filter_checked:
            return (km.name, km.space_type, km.region_type, kmi.id) in _kmi_conflict_check
        if filter_own:
            return _is_personal(km, kmi)
        return filter_func_text(km, kmi)

    conflicts_own = None
    if filter_conflicts_cross:
        conflicts_own = _kmi_conflict_ids_own_all(display_keymaps, _is_conflict_seed)

    found_any = False
    shown_count = 0
    stale_count = 0

    for km, kc in display_keymaps:
        km = km.active()
        layout.context_pointer_set("keymap", km)

        matching = [kmi for kmi in km.keymap_items if filter_func(km, kmi)]

        if filter_own and not filter_conflicts_cross:
            matching = [kmi for kmi in matching if _is_personal(km, kmi)]

        if filter_conflicts_cross:
            # Show the whole checked group, a checked item with no conflicts is an answer too.
            conflict_ids = conflicts_own.get((km.name, km.space_type, km.region_type), ())
            matching = [
                kmi for kmi in km.keymap_items
                if (kmi.id in conflict_ids or
                    (filter_checked and keymap_item_is_checked(km, kmi))) and
                filter_func_text(km, kmi)
            ]
        elif filter_conflicts:
            shadowing, shadowed, _shadowed_by, _partners = _kmi_conflict_ids(km)
            matching = [kmi for kmi in matching if kmi.id in shadowing or kmi.id in shadowed]

        pin_key = (km.name, km.space_type, km.region_type)
        matching_ids = {kmi.id for kmi in matching}
        pinned_ids = _keymap_filter_pinned.get(pin_key)
        if pinned_ids:
            shown_ids = matching_ids | pinned_ids
            filtered_items = [kmi for kmi in km.keymap_items if kmi.id in shown_ids]
        else:
            shown_ids = matching_ids
            filtered_items = matching

        if shown_ids:
            _keymap_filter_pinned[pin_key] = shown_ids
        else:
            _keymap_filter_pinned.pop(pin_key, None)

        stale_ids = shown_ids - matching_ids
        if stale_ids:
            _kmi_filter_stale[pin_key] = stale_ids
            stale_count += len(stale_ids)
        else:
            _kmi_filter_stale.pop(pin_key, None)

        if filter_conflicts:
            filtered_items.sort(key=lambda kmi: kmi.to_string())

        km_removals_only = (
            filter_user_modified and
            not filter_labels and
            not filter_addon and
            not filter_conflicts and
            not filter_text and
            not filtered_items and
            km.is_user_modified
        )

        if filtered_items or km_removals_only:
            found_any = True
            col = layout.column()

            row = col.row(align=True)
            sub = row.row(align=True)
            sub.alignment = 'LEFT'
            sub.operator(
                "preferences.keymap_isolate",
                text=km.name,
                text_ctxt=i18n_contexts.id_windowmanager,
                icon='DISCLOSURE_TRI_RIGHT',
                emboss=False,
            ).keymap_name = km.name

            subrow = row.row(align=True)
            subrow.alignment = 'RIGHT'
            if km.is_user_modified:
                subrow.operator("preferences.keymap_restore", text="Restore")

            # Add margin to space the button from the scroll-bar.
            subrow.separator()

            if km_removals_only:
                sub = _indented_layout(col, 1)
                sub.label(text="Default items removed", icon='INFO')

            shown_count += len(filtered_items)
            for kmi in filtered_items:
                draw_kmi(display_keymaps, kc, km, kmi, col, 1, use_local_expand=True)

    _keymap_filter_counts_set(shown_count, stale_count)

    # `conflicts_own` only gets entries when a conflict is found, so empty means all clean.
    if filter_checked and found_any and conflicts_own is not None and not conflicts_own:
        count = keymap_conflict_check_count()
        col = layout.column()
        col.label(
            text=(
                iface_("Nothing conflicts with the shortcut being checked")
                if count == 1 else
                iface_("Nothing conflicts with the {:d} being checked").format(count)
            ),
            translate=False,
            icon='INFO',
        )

    if (filter_own or filter_conflicts) and not found_any:
        # With the conflicts filter on, an empty list means nothing clashed, not an empty search.
        if filter_checked:
            count = keymap_conflict_check_count()
            text = (
                iface_("Nothing conflicts with the shortcut being checked")
                if count == 1 else
                iface_("Nothing conflicts with the {:d} being checked").format(count)
            )
        elif filter_conflicts_cross:
            text = iface_("None of the items asked for conflicts with another")
        elif filter_conflicts:
            text = iface_("No key binding is claimed twice in the same key map")
        elif filter_text:
            text = iface_("No matching key map items found")
        elif filter_user_modified + bool(filter_labels) + filter_addon > 1:
            text = iface_("Nothing answers all of the filters that are on")
        elif filter_addon:
            text = iface_("No add-on has added a shortcut")
        elif filter_labels:
            text = iface_("No shortcut carries the labels that are on")
        else:
            text = iface_("Nothing customized in this key configuration")
        col = layout.column()
        col.label(text=text, translate=False, icon='INFO')

        # No key map row to paste into, offer pasting into the source key maps.
        sources = keymap_clipboard_sources(keymap_item_clipboard())
        if sources:
            sub = col.row(align=True)
            sub.alignment = 'LEFT'
            sub.operator(
                "preferences.keyitem_paste",
                text=keymap_clipboard_source_label(sources),
                translate=False,
                icon='PASTEDOWN',
            ).use_source_keymap = True

    return True


def _usage_hidden_item_ids():
    """{(keymap_name, space_type, region_type): {item_id, ...}} of hidden items."""
    from bl_keymap_utils import editor_meta
    hidden = {}
    for entry in editor_meta.hidden_list():
        if entry.get("idname"):
            # An operation rather than a key map item, see `_usage_hidden_operators`.
            continue
        hidden.setdefault(
            (entry.get("keymap_name", ""), entry.get("space_type", ""), entry.get("region_type", "")),
            set(),
        ).add(entry.get("item_id", 0))
    return hidden


def _usage_hidden_operators():
    """{(idname, variant), ...} of the hidden operations."""
    from bl_keymap_utils import editor_meta
    return {
        (entry["idname"], entry.get("variant", ""))
        for entry in editor_meta.hidden_list()
        if entry.get("idname")
    }


def _usage_hidden_activity_keys(kc):
    """{(keymap_name, idname, key_string, propvalue), ...} of hidden items."""
    keys = set()
    hidden = _usage_hidden_item_ids()
    if not hidden:
        return keys
    for km in kc.keymaps:
        km = km.active()
        ids = hidden.get((km.name, km.space_type, km.region_type))
        if not ids:
            continue
        for kmi in km.keymap_items:
            if kmi.id in ids:
                keys.add((
                    km.name,
                    kmi.idname,
                    kmi.to_string(),
                    kmi.propvalue if km.is_modal else "",
                ))
    return keys


def usage_operation_label(idname, variant):
    """Label of an operation in the usage lists."""
    if not variant:
        return idname
    return "{:s} [{:s}]".format(idname, variant)


_USAGE_NAME_CLASS_OPERATORS = {
    "wm.call_menu": "Menu",
    "wm.call_menu_pie": "Pie",
    "wm.call_panel": "Panel",
    "wm.call_asset_shelf_popover": "Shelf",
}

_USAGE_NAME_CONTEXT_VERBS = {
    "wm.context_toggle": "Toggle {:s}",
    "wm.context_toggle_enum": "Toggle {:s}",
    "wm.context_cycle_enum": "Cycle {:s}",
    "wm.context_menu_enum": "{:s} Menu",
    "wm.context_pie_enum": "{:s} Pie",
    "wm.context_scale_float": "Scale {:s}",
    "wm.context_modal_mouse": "Adjust {:s}",
}

_USAGE_NAME_CONTEXT_SETTERS = frozenset({
    "wm.context_set_enum",
    "wm.context_set_value",
    "wm.context_set_boolean",
    "wm.context_set_int",
    "wm.context_set_float",
    "wm.context_set_string",
    "wm.context_set_id",
})


def _usage_variant_props(idname):
    """Properties making up an operator's usage variant, matches `operator_usage_variants` in `wm_operators.cc`."""
    if (idname in _USAGE_NAME_CLASS_OPERATORS) or (idname == "wm.tool_set_by_id"):
        return ("name",)
    if idname in _USAGE_NAME_CONTEXT_VERBS:
        return ("data_path",)
    if idname in _USAGE_NAME_CONTEXT_SETTERS:
        return ("data_path", "value")
    if idname == "object.mode_set":
        return ("mode",)
    return ()


def usage_variant_apply(kmi, variant):
    """
    Set the properties so the item runs the operation `variant` names.

    `KeyMapItem.usage_variant` is read-only. Returns whether the item's variant now matches.
    """
    names = _usage_variant_props(kmi.idname)
    props = kmi.properties
    if not names or not variant or props is None:
        return False

    # Only split for the leading properties, the last value may contain "=".
    values = variant.split("=", len(names) - 1)
    if len(values) != len(names):
        return False

    definitions = props.bl_rna.properties
    for name, value in zip(names, values):
        prop = definitions.get(name)
        if prop is None:
            return False
        try:
            if prop.type == 'BOOLEAN':
                setattr(props, name, value == "True")
            elif prop.type == 'INT':
                setattr(props, name, int(value))
            elif prop.type == 'FLOAT':
                setattr(props, name, float(value))
            else:
                setattr(props, name, value)
        except (AttributeError, TypeError, ValueError):
            return False
    return kmi.usage_variant == variant


_USAGE_VARIANT_EDITOR_PATH_HEADS = frozenset({
    "space_data",
    "area",
    "region",
    "region_data",
})


def usage_variant_is_editor_scoped(idname, variant):
    """Whether the operation only applies inside one editor (`wm.context_*` with a `space_data.*` path)."""
    names = _usage_variant_props(idname)
    if not variant or not names or names[0] != "data_path":
        return False
    # Split as `usage_variant_apply` does.
    data_path = variant.split("=", len(names) - 1)[0]
    return data_path.partition(".")[0] in _USAGE_VARIANT_EDITOR_PATH_HEADS


def _usage_name_from_identifier(identifier):
    """`builtin.select_box` -> `Select Box`."""
    return identifier.rpartition(".")[2].replace("_", " ").strip().title()


def _usage_name_operator_label(idname):
    """The operator's RNA name, or "" if not registered."""
    module, _, operator = idname.partition(".")
    try:
        return getattr(getattr(bpy.ops, module), operator).get_rna_type().name
    except (AttributeError, KeyError, RuntimeError):
        return ""


def _usage_name_operator_enum_label(idname, value):
    """Name of `value` from any of the operator's enum properties, or ""."""
    module, _, operator = idname.partition(".")
    try:
        rna = getattr(getattr(bpy.ops, module), operator).get_rna_type()
    except (AttributeError, KeyError, RuntimeError):
        return ""
    for prop in rna.properties:
        if prop.type != 'ENUM':
            continue
        item = prop.enum_items.get(value)
        if item is not None:
            return item.name
    return ""


def _usage_name_tool_label(tool_id):
    """Label of a tool from the tool system, or ""."""
    from bl_ui.space_toolsystem_common import ToolSelectPanelHelper
    for cls in ToolSelectPanelHelper.__subclasses__():
        for _context_mode, tools in cls.tools_all():
            for item in cls._tools_flatten(tools):
                if item is not None and item.idname == tool_id:
                    return item.label
    return ""


def _usage_name_value_labels(prop, value):
    """Display labels for a variant's value string."""
    text = value.strip()
    if text.startswith("{") and text.endswith("}"):
        parts = [part.strip().strip("'\"") for part in text[1:-1].split(",")]
        parts = [part for part in parts if part]
    else:
        parts = [text.strip("'\"")]

    if prop is not None and getattr(prop, "type", "") == 'ENUM':
        labels = []
        for part in parts:
            item = prop.enum_items.get(part)
            labels.append(item.name if item is not None else _usage_name_from_identifier(part))
        return labels
    if getattr(prop, "type", "") == 'BOOLEAN':
        return ["On" if parts and parts[0] == "True" else "Off"]
    return [_usage_name_from_identifier(part) if part.isupper() else part for part in parts]


def usage_suggested_name(context, idname, variant):
    """Suggested custom name for a shortcut running this operation."""
    if not variant:
        return _usage_name_operator_label(idname)

    word = _USAGE_NAME_CLASS_OPERATORS.get(idname)
    if word is not None:
        cls = getattr(bpy.types, variant, None)
        label = getattr(cls, "bl_label", "") or _usage_name_from_identifier(variant)
        if word.lower() in label.lower().split():
            return label
        return "{:s} {:s}".format(label, word)

    if idname == "wm.tool_set_by_id":
        label = _usage_name_tool_label(variant) or _usage_name_from_identifier(variant)
        return label if "tool" in label.lower().split() else "{:s} Tool".format(label)

    if idname not in _USAGE_NAME_CONTEXT_VERBS and idname not in _USAGE_NAME_CONTEXT_SETTERS:
        label = _usage_name_operator_label(idname)
        value_label = (
            _usage_name_operator_enum_label(idname, variant) or
            _usage_name_from_identifier(variant)
        )
        return "{:s}: {:s}".format(label, value_label) if label else value_label

    data_path, _, value = variant.partition("=")
    prop = None
    try:
        from _bl_rna_utils.data_path import property_definition_from_data_path
        prop = property_definition_from_data_path(context, "." + data_path)
    except Exception:
        prop = None
    name = (getattr(prop, "name", "") or _usage_name_from_identifier(data_path))

    template = _USAGE_NAME_CONTEXT_VERBS.get(idname)
    if template is not None:
        return template.format(name)

    if not value:
        return name
    return "{:s}: {:s}".format(name, ", ".join(_usage_name_value_labels(prop, value)))


_KMI_UNPRESSABLE_MAP_TYPES = frozenset({'TIMER', 'TEXTINPUT'})


def _usage_operator_bindings(kc):
    """{(idname, variant): (km, kmi)} of the first pressable binding of each operation."""
    bindings = {}
    for km in kc.keymaps:
        km = km.active()
        for kmi in km.keymap_items:
            if not kmi.idname:
                continue
            if kmi.map_type in _KMI_UNPRESSABLE_MAP_TYPES:
                continue
            key = (kmi.idname, kmi.usage_variant)
            if key not in bindings:
                bindings[key] = (km, kmi)
    return bindings


_USAGE_ENUM_PATH_OPERATORS = (
    "wm.context_toggle_enum",
    "wm.context_cycle_enum",
    "wm.context_pie_enum",
    "wm.context_menu_enum",
)


def _usage_binding_near(bindings, usage):
    """A binding for the same data path via a toggle/cycle/pie/menu operator, or None."""
    if usage.idname not in {"wm.context_set_enum", "wm.context_set_value"}:
        return None
    data_path = usage.variant.partition("=")[0]
    if not data_path:
        return None
    for idname in _USAGE_ENUM_PATH_OPERATORS:
        binding = bindings.get((idname, data_path))
        if binding is not None:
            return binding
    return None


def draw_hierarchy(display_keymaps, layout):
    from bl_keymap_utils import keymap_hierarchy
    for entry in keymap_hierarchy.generate():
        draw_entry(display_keymaps, entry, layout)


# -----------------------------------------------------------------------------
# Intents

def _intent_event_matches(kmi, intent):
    """True when the item's event is triggered by the same input as the intent."""
    if kmi.type != intent.type:
        return False
    if kmi.value != intent.value and 'ANY' not in {kmi.value, intent.value}:
        return False
    for attr in ("shift", "ctrl", "alt", "oskey", "hyper"):
        a, b = getattr(kmi, attr), getattr(intent, attr)
        if a != b and -1 not in {a, b}:
            return False
    if kmi.key_modifier != intent.key_modifier:
        return False
    return True


def intent_served_items(kc, intent):
    """The (key map, item) pairs bound through the intent."""
    idname = intent.name
    return [
        (km, kmi)
        for km in kc.keymaps
        for kmi in km.keymap_items
        if kmi.intent == idname
    ]


def _intents_served_items_all(kc):
    """The (key map, item) pairs bound through each intent, one pass over the key maps."""
    served = {}
    for km in kc.keymaps:
        for kmi in km.keymap_items:
            if intent := kmi.intent:
                served.setdefault(intent, []).append((km, kmi))
    return served


# Icons for the context of a key map: the editor (space type) or, for the mode key maps
# which have no space type, the mode. Anything else falls back to the editor it is listed under.
_KEYMAP_ICONS = {
    "Window": 'WINDOW',
    "Screen": 'WORKSPACE',
    "Screen Editing": 'WORKSPACE',
    "Region Context Menu": 'MENU_PANEL',
    "View2D": 'VIEW_PAN',
    "View2D Buttons List": 'VIEW_PAN',
    "User Interface": 'WINDOW',
    "Toolbar Popup": 'TOOL_SETTINGS',
    "Object Mode": 'OBJECT_DATAMODE',
    "Mesh": 'EDITMODE_HLT',
    "Curve": 'CURVE_DATA',
    "Curves": 'CURVES_DATA',
    "Armature": 'ARMATURE_DATA',
    "Metaball": 'META_DATA',
    "Lattice": 'LATTICE_DATA',
    "Font": 'FONT_DATA',
    "Point Cloud": 'POINTCLOUD_DATA',
    "Pose": 'POSE_HLT',
    "Vertex Paint": 'VPAINT_HLT',
    "Weight Paint": 'WPAINT_HLT',
    "Image Paint": 'TPAINT_HLT',
    "Sculpt": 'SCULPTMODE_HLT',
    "Sculpt Curves": 'SCULPTMODE_HLT',
    "Particle": 'PARTICLEMODE',
    "Paint Curve": 'CURVE_BEZCURVE',
    "Paint Vertex Selection (Weight, Vertex)": 'VERTEXSEL',
    "Paint Face Mask (Weight, Vertex, Texture)": 'FACESEL',
    "Mask Editing": 'MOD_MASK',
    "Markers": 'MARKER_HLT',
    "Animation": 'ANIM',
    "Animation Channels": 'ANIM_DATA',
    "Frames": 'TIME',
}
_KEYMAP_ICONS_PREFIX = (
    ("Grease Pencil", 'OUTLINER_DATA_GREASEPENCIL'),
)
_keymap_icon_cache = None


def _keymap_order(km):
    """Position of the key map in the key map hierarchy, for a stable display order."""
    _keymap_icon(km)
    return _keymap_icon_cache[4].get(km.name, len(_keymap_icon_cache[4]))


def _keymap_icon(km):
    global _keymap_icon_cache
    if _keymap_icon_cache is None:
        icons_all = {item.identifier for item in bpy.types.UILayout.bl_rna.functions["label"].parameters["icon"].enum_items}
        space_items = bpy.types.KeyMap.bl_rna.properties["space_type"].enum_items
        space_icons = {item.identifier: item.icon for item in space_items}

        # Editor of every key map in the hierarchy, from the nearest ancestor with a space type,
        # and the position of the key map in the hierarchy (used to order the contexts).
        from bl_keymap_utils import keymap_hierarchy
        fallback = {}
        order = {}

        def walk(entries, space_parent):
            for name, space, _region, children in entries:
                space_here = space if space != 'EMPTY' else space_parent
                fallback.setdefault(name, space_here)
                order.setdefault(name, len(order))
                walk(children, space_here)
        walk(keymap_hierarchy.generate(), 'EMPTY')

        cache = {}
        for name, icon in _KEYMAP_ICONS.items():
            if icon in icons_all:
                cache[name] = icon
        _keymap_icon_cache = (cache, icons_all, space_icons, fallback, order)

    cache, icons_all, space_icons, fallback, _order = _keymap_icon_cache
    if (icon := cache.get(km.name)) is not None:
        return icon
    icon = 'DOT'
    space = km.space_type
    if space == 'EMPTY':
        for prefix, prefix_icon in _KEYMAP_ICONS_PREFIX:
            if km.name.startswith(prefix):
                icon = prefix_icon
                break
        else:
            space = fallback.get(km.name, 'EMPTY')
    if icon == 'DOT' and space != 'EMPTY':
        icon = space_icons.get(space, 'DOT')
    if icon not in icons_all:
        icon = 'DOT'
    cache[km.name] = icon
    return icon


def intent_conflicts(kc, intent, served=None):
    """
    Items in the key maps served by the intent which use its key without being bound through it,
    as (key map, item) pairs. Used before committing a re-bind to show what the new key collides with.
    """
    if served is None:
        served = intent_served_items(kc, intent)
    conflicts = []
    for km in {km.name: km for km, _ in served}.values():
        for kmi in km.keymap_items:
            if kmi.intent or not kmi.active or not kmi.idname:
                continue
            if _intent_event_matches(kmi, intent):
                conflicts.append((km, kmi))
    return conflicts


def _intent_is_flashing(served):
    """Whether any item bound through the intent was just used, see `_kmi_row_is_flashing`."""
    return any(_kmi_row_is_flashing(km, kmi) for km, kmi in served)


def _draw_intent(kc, intent, layout, served):
    _intent_row_mark(intent.name)
    # The expanded body is not measured, only rows below a collapsed intent scroll exactly.
    _intent_row_advance(1.0)

    col = layout.column(align=True)
    if _intent_is_flashing(served) or _intent_reveal_target == intent.name:
        col.warning = True
    if intent.show_expanded:
        box = col.box()
    else:
        box = col.column()

    split = box.split(factor=0.55)

    row = split.row(align=True)
    row.prop(intent, "show_expanded", text="", emboss=False)
    row.label(text=intent.label, translate=False)
    contexts = len(served)
    sub = row.row(align=True)
    sub.alignment = 'RIGHT'
    sub.active = False
    sub.label(text=str(contexts), translate=False)
    # Not used by any key map of the active configuration.
    col.active = contexts > 0

    row = split.row(align=True)
    if intent.map_type in {'KEYBOARD', 'MOUSE', 'NDOF'}:
        row.prop(intent, "type", text="", full_event=True)
    else:
        row.prop(intent, "type", text="")

    if intent.is_user_modified:
        row.operator("preferences.keyintent_restore", text="", icon='BACK').intent = intent.name
    else:
        row.label(text="", icon='BLANK1')
    row.separator(factor=0.25 if intent.show_expanded else 1.0)

    if not (intent.show_expanded or intent.is_user_modified):
        return

    conflicts = intent_conflicts(kc, intent, served)
    if conflicts:
        # The key is already taken in some of the contexts served by the intent.
        km, kmi = conflicts[0]
        row = box.row()
        row.alert = True
        row.label(
            text=iface_("{:s} is already {:s} in {:d} of these key maps").format(
                intent.type if intent.map_type != 'KEYBOARD' else kmi.to_string(),
                kmi.name or kmi.idname,
                len({km.name for km, _ in conflicts}),
            ),
            icon='ERROR',
            translate=False,
        )

    if not intent.show_expanded:
        return

    box = col.box()

    # Event settings, matching `draw_kmi`.
    if intent.map_type not in {'TEXTINPUT', 'TIMER'}:
        from _bpy import _wm_capabilities
        capabilities = _wm_capabilities()
        from sys import platform

        sub = box.column()
        subrow = sub.row(align=True)
        subrow.prop(intent, "map_type", text="")
        if intent.map_type == 'KEYBOARD':
            subrow.prop(intent, "type", text="", event=True)
            subrow.prop(intent, "value", text="")
        else:
            subrow.prop(intent, "type", text="")
            subrow.prop(intent, "value", text="")
        if intent.map_type in {'KEYBOARD', 'MOUSE'} and intent.value == 'CLICK_DRAG':
            subrow = sub.row()
            subrow.prop(intent, "direction")

        subrow = sub.row()
        subrow.scale_x = 0.75
        subrow.prop(intent, "any", toggle=True)
        match platform:
            case "darwin":
                oskey_label = "Cmd"
            case "win32":
                oskey_label = "Win"
            case _:
                oskey_label = "OS"
        subrow.prop(intent, "shift_ui", toggle=True)
        subrow.prop(intent, "ctrl_ui", toggle=True)
        subrow.prop(intent, "alt_ui", toggle=True)
        subrow.prop(intent, "oskey_ui", text=oskey_label, toggle=True)
        if capabilities['KEYBOARD_HYPER_KEY'] or intent.hyper == 1:
            subrow.prop(intent, "hyper_ui", text="Hyper", toggle=True)
        subrow.prop(intent, "key_modifier", text="", event=True)

    # The contexts: key map & the operator it runs there, in the order of the key map hierarchy.
    # Each is a button that shows the item in the key map tree.
    if served:
        col = box.column(align=True)
        col.label(text="Contexts")
        for km, kmi in sorted(served, key=lambda pair: _keymap_order(pair[0])):
            row = col.row()
            row.active = kmi.active
            if _kmi_row_is_flashing(km, kmi):
                row.warning = True
            sub = row.row()
            sub.alignment = 'LEFT'
            props = sub.operator(
                "preferences.keyitem_reveal",
                text=iface_(km.name, i18n_contexts.id_windowmanager),
                icon=_keymap_icon(km),
                translate=False,
                emboss=False,
            )
            props.keymap_name = km.name
            props.item_id = kmi.id
            row.label(text=kmi.name or kmi.idname, translate=False)
    else:
        box.label(text="No key map items use this shared shortcut")


def draw_intents(context, layout, kc):
    """The intents of the user key configuration, drawn in the intents column of the editor."""
    wm = context.window_manager
    _kmi_flash_update(wm)
    _intent_rows_reset()

    col = layout.column()
    row = col.row(align=True)
    row.label(text=iface_("Shared Shortcuts ({:d})").format(len(kc.intents)), translate=False)
    sub = col.column()
    sub.active = False
    sub.label(text="One shortcut used by several key maps, changing it changes them all")
    _intent_row_advance(2.0 + _KMI_ROW_SEPARATOR)
    col.separator()

    if not kc.intents:
        col.label(text="The active key configuration defines no shared shortcuts")
        return

    served_all = _intents_served_items_all(kc)

    # Group by category, in the order of the key configuration's table.
    categories = {}
    for intent in kc.intents:
        categories.setdefault(intent.category, []).append(intent)

    for category, intents in categories.items():
        if not category:
            # Uncategorized intents (add-ons, user defined) are listed after the groups.
            continue
        expanded = intents[0].show_category_expanded
        row = col.row(align=True)
        if not expanded:
            # As the key map headers in the tree: a collapsed group glows for its intents.
            if any(_intent_is_flashing(served_all.get(intent.name, ())) for intent in intents):
                row.warning = True
        row.operator(
            "preferences.keyintent_category_toggle",
            text="",
            icon='DISCLOSURE_TRI_DOWN' if expanded else 'DISCLOSURE_TRI_RIGHT',
            emboss=False,
        ).category = category
        row.label(text=iface_("{:s} ({:d})").format(iface_(category), len(intents)), translate=False)
        _intent_row_advance(1.0)
        if expanded:
            sub = col.column()
            for intent in intents:
                _draw_intent(kc, intent, sub, served_all.get(intent.name, ()))
            col.separator()
            _intent_row_advance(_KMI_ROW_SEPARATOR)

    if uncategorized := categories.get(""):
        if len(categories) > 1:
            col.label(text=iface_("Other ({:d})").format(len(uncategorized)), translate=False)
            _intent_row_advance(1.0)
        for intent in uncategorized:
            _draw_intent(kc, intent, col, served_all.get(intent.name, ()))


def draw_keymaps(context, layout):
    draw_keymaps_header(context, layout)
    layout.separator()
    draw_keymaps_tree(context, layout)
    layout.separator()
    draw_keymaps_usage(context, layout)


def draw_keymaps_header(context, layout):
    wm = context.window_manager
    kc_active = wm.keyconfigs.active
    spref = context.space_data

    # row.prop_search(wm.keyconfigs, "active", wm, "keyconfigs", text="Key Config")
    text = bpy.path.display_name(kc_active.name, has_ext=False)
    if not text:
        text = "Blender (default)"

    split = layout.split(factor=0.6)

    row = split.row()

    rowsub = row.row(align=True)

    rowsub.menu("USERPREF_MT_keyconfigs", text=text)
    rowsub.operator("wm.keyconfig_preset_add", text="", icon='ADD')
    rowsub.operator("wm.keyconfig_preset_remove", text="", icon='REMOVE')

    # Undo/redo of edits, then view history.
    rowsub = row.row(align=True)
    rowsub.operator("preferences.keymap_undo", text="", icon='LOOP_BACK')
    rowsub.operator("preferences.keymap_redo", text="", icon='LOOP_FORWARDS')
    rowsub.separator()
    rowsub.operator("preferences.keymap_view_back", text="", icon='BACK')

    rowsub = split.row(align=True)
    rowsub.operator("preferences.keyconfig_import", text="Import...", icon='IMPORT')
    rowsub.operator("preferences.keyconfig_export", text="Export...", icon='EXPORT')
    # The intents column, beside the tree.
    rowsub.separator()
    rowsub.operator(
        "screen.region_toggle",
        text="",
        icon='LINKED',
        depress=keymap_intents_region_visible(context.area),
    ).region_type = 'CHANNELS'

    filter_text = spref.filter_text.strip()

    row = layout.row()
    rowsub = row.split(factor=0.4, align=True)
    rowsubsub = rowsub.row(align=True)
    rowsubsub.prop(spref, "filter_type", expand=True)
    rowsubsub = rowsub.row(align=True)
    search_placeholder = ""
    if spref.filter_type == 'NAME':
        search_placeholder = iface_("Search by Name")
    elif spref.filter_type == 'KEY':
        search_placeholder = iface_("Search by Key-Binding")
    sub = rowsubsub.row(align=True)
    if filter_text and not _keymap_tree_filter_ok:
        sub.alert = True
    sub.prop(spref, "filter_text", text="", icon='VIEWZOOM', placeholder=search_placeholder)
    filter_active = keymap_filter_is_active(spref)
    filter_sub = rowsubsub.row(align=True)
    if filter_active:
        filter_sub.info = True
    filter_sub.popover(
        panel="USERPREF_PT_keymap_filter",
        text="",
        icon='FILTER' if filter_active else 'FILTER_OFF',
    )

    _draw_status_bar(layout, spref, filter_text)


def keymap_filter_is_active(spref):
    """Whether any filter besides the search text is on."""
    return (
        spref.use_filter_user_modified or
        bool(keymap_filter_labels()) or
        spref.use_filter_addon or
        spref.use_filter_conflicts or
        (spref.use_filter_key_exact and spref.filter_type == 'KEY')
    )


def draw_keymaps_filter(context, layout):
    """The filter popover, see `USERPREF_PT_keymap_filter`."""
    spref = context.space_data
    if spref is None or spref.type != 'PREFERENCES':
        return

    col = layout.column(heading="Show Only")
    col.prop(spref, "use_filter_user_modified", text="Customized")
    col.prop(spref, "use_filter_addon", text="From Add-ons")
    col.prop(spref, "use_filter_conflicts", text="Conflicts")

    layout.separator()
    col = layout.column(heading="Key Search")
    col.active = spref.filter_type == 'KEY'
    col.prop(spref, "use_filter_key_exact", text="Exact Binding")

    # Items carrying any of the checked labels are shown.
    layout.separator()
    col = layout.column()
    col.label(text="Labels")
    from bl_keymap_utils import editor_meta
    for label_name, use_filter in editor_meta.labels_list():
        row = col.row(align=True)
        row.operator(
            "preferences.keymap_label_filter_toggle",
            text=label_name,
            translate=False,
            icon='CHECKBOX_HLT' if use_filter else 'CHECKBOX_DEHLT',
            emboss=False,
        ).name = label_name
        row.operator(
            "preferences.keymap_label_remove", text="", icon='X', emboss=False,
        ).name = label_name
    col.operator("preferences.keymap_label_new", text="New Label...", icon='ADD')


def _draw_status_bar(layout, spref, filter_text):
    """Selection status left, filter status right. Always drawn so the tree does not shift."""
    row = layout.row(align=True)

    left = row.row(align=True)
    left.alignment = 'LEFT'
    _draw_selection_status(left)

    right = row.row(align=True)
    right.alignment = 'RIGHT'
    _draw_filter_status(right, spref, filter_text)


def _draw_filter_status(layout, spref, filter_text):
    """Filter match count and the "Update List" button for a stale list."""
    filter_user_modified = spref.use_filter_user_modified
    filter_labels = keymap_filter_labels()
    filter_addon = spref.use_filter_addon
    filter_conflicts = spref.use_filter_conflicts
    if not (filter_text or filter_user_modified or filter_labels or filter_addon or
            filter_conflicts):
        layout.label(text="")
        return

    shown = _keymap_filter_shown_count
    stale = _keymap_filter_stale_count

    origins = []
    if filter_user_modified:
        origins.append(iface_("customized by you"))
    if filter_labels:
        origins.append(iface_("labeled {:s}").format(", ".join(filter_labels)))
    if filter_addon:
        origins.append(iface_("added by an add-on"))

    checked = keymap_conflict_check_count()
    if filter_conflicts and checked:
        # The checked group is shown whole, so the count is of rows shown, not of conflicts.
        text = (
            iface_("{:d} shown: the shortcut being checked and its conflicts").format(shown)
            if checked == 1 else
            iface_("{:d} shown: the {:d} being checked and their conflicts").format(
                shown, checked)
        )
    elif origins and filter_conflicts:
        text = iface_("{:d} in conflicts involving items {:s}").format(
            shown, ", ".join(origins))
    elif filter_conflicts and filter_text:
        # Cross key map conflicts, see `filter_conflicts_cross`.
        text = iface_("{:d} in conflicts involving the search").format(shown)
    elif filter_conflicts:
        text = iface_("{:d} sharing a key binding inside their key map").format(shown)
    elif origins:
        text = "{:d} {:s}".format(shown, ", ".join(origins))
    elif filter_text and spref.filter_type == 'KEY' and spref.use_filter_key_exact:
        text = iface_("{:d} on exactly this key binding").format(shown)
    else:
        text = iface_("{:d} matching the search").format(shown)

    if stale:
        sub = layout.row(align=True)
        sub.alignment = 'RIGHT'
        sub.operator("preferences.keymap_filter_refresh", text="Update List")
        text = iface_("{:s} — {:d} no longer match").format(text, stale)

    sub = layout.row(align=True)
    sub.alignment = 'RIGHT'
    if stale:
        sub.info = True
    sub.label(text=text, translate=False, icon='INFO')


def _draw_selection_status(layout):
    """Selection count and the operators acting on the selection."""
    count = keymap_selection_count()
    if not count:
        layout.label(text="")
        return

    layout.label(
        text=iface_("{:d} Selected").format(count),
        translate=False,
        icon='RESTRICT_SELECT_OFF',
    )

    # Left aligned, or the buttons stretch to fill the row.
    sub = layout.row(align=True)
    sub.alignment = 'LEFT'
    sub.operator("preferences.keymap_select_all", text="All").action = 'SELECT'
    sub.operator("preferences.keymap_select_all", text="Invert").action = 'INVERT'
    sub.operator("preferences.keymap_select_all", text="None").action = 'DESELECT'
    sub.separator()
    sub.operator("preferences.keyitem_copy", text="", icon='COPYDOWN').use_selection = True

    sub.menu("USERPREF_MT_keymap_labels", text="", icon='TAG')

    # Hide toggles, the icon shows the action.
    all_hidden = keymap_selection_all_hidden()
    props = sub.operator(
        "preferences.keymap_hide_item",
        text="",
        icon='HIDE_OFF' if all_hidden else 'HIDE_ON',
    )
    props.use_selection = True
    props.hide = not all_hidden

    sub.operator("preferences.keyitem_restore", text="", icon='BACK').use_selection = True
    sub.operator("preferences.keyitem_remove", text="", icon='X').use_selection = True


_usage_bindings_cache = None


def _usage_bindings_cache_clear():
    global _usage_bindings_cache
    _usage_bindings_cache = None


def usage_bindings(kc):
    """`_usage_operator_bindings`, cached per draw."""
    global _usage_bindings_cache
    if _usage_bindings_cache is None:
        _usage_bindings_cache = _usage_operator_bindings(kc)
    return _usage_bindings_cache


def usage_row_binding(kc, item):
    """The binding that would have run this entry's operation, or None (resolved at draw time)."""
    bindings = usage_bindings(kc)
    return bindings.get((item.idname, item.variant)) or _usage_binding_near(bindings, item)


def usage_activity_visible(context):
    """The history entries not hidden, oldest first."""
    wm = context.window_manager
    skip_items = _usage_hidden_activity_keys(wm.keyconfigs.user)
    skip_ops = _usage_hidden_operators()

    visible = []
    for item in wm.keymap_activity:
        if item.is_shortcut:
            if (item.keymap_name, item.idname, item.key_string, item.propvalue) in skip_items:
                continue
            if (item.idname, "") in skip_ops:
                continue
        elif (item.idname, item.variant) in skip_ops:
            continue
        visible.append(item)
    return visible


def usage_hidden_label(entry):
    """Label of a hidden entry (item or operation)."""
    if entry.get("idname"):
        return usage_operation_label(entry["idname"], entry.get("variant", ""))

    km_name = entry.get("keymap_name", "")
    item_id = entry.get("item_id", 0)
    km = bpy.context.window_manager.keyconfigs.user.keymaps.get(km_name)
    kmi = km.active().keymap_items.from_id(item_id) if km is not None else None
    if kmi is None:
        return iface_("{:s} > (missing item {:d})").format(km_name, item_id)
    return "{:s} > {:s} [{:s}]".format(
        km_name,
        kmi.idname or kmi.propvalue or "?",
        kmi.to_string(),
    )


def draw_keymaps_usage(context, layout):
    """Draw the usage history lists."""
    from bl_keymap_utils import editor_meta

    wm = context.window_manager

    _usage_bindings_cache_clear()
    _kmi_flash_update(wm)

    row = layout.row(align=True)
    if not wm.keymap_activity_show:
        row.prop(
            wm, "keymap_activity_show", text="Show Recent",
            icon='DISCLOSURE_TRI_RIGHT', toggle=True,
        )
        return

    hidden = editor_meta.hidden_list()
    show_hidden = wm.keymap_activity_show_hidden

    split = row.split(factor=0.6 if hidden else 0.8, align=True)
    sub = split.row(align=True)
    sub.prop(
        wm, "keymap_activity_show", text="Show Recent",
        icon='DISCLOSURE_TRI_DOWN', toggle=True,
    )
    sub = split.row(align=True)
    if hidden:
        sub.prop(
            wm, "keymap_activity_show_hidden",
            text=iface_("{:d} Hidden").format(len(hidden)),
            translate=False,
            icon='HIDE_OFF' if show_hidden else 'HIDE_ON',
            toggle=True,
        )
    sub.operator("preferences.keymap_activity_clear", text="", icon='TRASH')

    show_hidden_list = bool(hidden and show_hidden)
    body_rows = _usage_body_rows(context, 2 if show_hidden_list else 1)
    hidden_rows = 0
    if show_hidden_list:
        hidden_rows = max(1, min(len(hidden), body_rows // 2))

    if show_hidden_list:
        box = layout.box()
        col = box.column(align=True)
        # Show the hidden entries with a quick unhide button (and most recent hit count).
        for entry in hidden[:hidden_rows * 2]:
            hrow = col.row(align=True)
            hrow.label(text=usage_hidden_label(entry), translate=False)
            if entry.get("idname"):
                props = hrow.operator(
                    "preferences.keymap_hide_operator", text="", icon='HIDE_OFF', emboss=False,
                )
                props.idname = entry["idname"]
                props.variant = entry.get("variant", "")
                props.hide = False
            else:
                props = hrow.operator(
                    "preferences.keymap_hide_item", text="", icon='HIDE_OFF', emboss=False,
                )
                props.keymap_name = entry.get("keymap_name", "")
                props.item_id = entry.get("item_id", 0)
                props.hide = False

    layout.template_list(
        "USERPREF_UL_keymap_activity", "keymap_activity",
        wm, "keymap_activity",
        wm, "keymap_activity_active",
        rows=max(1, body_rows - hidden_rows), maxrows=max(1, body_rows - hidden_rows),
    )


_USAGE_LIST_CHROME_ROWS = 2


def _usage_body_rows(context, list_count):
    """How many rows the lists may fill below the controls."""
    row_px = 20.0 * context.preferences.system.ui_scale
    region = context.region
    if region is None or row_px <= 0.0:
        return 4
    rows = int(region.height / row_px)
    rows -= 1  # The controls row.
    rows -= _USAGE_LIST_CHROME_ROWS * list_count
    return max(2, rows)


def draw_keymaps_tree(context, layout):
    from bl_keymap_utils.io import keyconfig_merge

    global _keymap_tree_filter_ok
    global _kmi_conflicts_view
    global _keymap_filter_signature
    global _kmi_draw_serial

    # See `_kmi_scroll_offset_run`.
    _kmi_draw_serial += 1

    wm = context.window_manager
    kc_user = wm.keyconfigs.user
    kc_active = wm.keyconfigs.active
    spref = context.space_data

    _kmi_flash_update(wm)
    _kmi_conflict_cache_clear()
    _kmi_cross_conflicts_clear()
    _kmi_clipboard_cache_clear()
    _kmi_filter_stale_clear()
    _kmi_label_cache_clear()
    _kmi_selection_cache_clear()
    _kmi_custom_name_cache_clear()
    _kmi_suggested_name_cache_clear()
    _kmi_drawn_rows.clear()
    _kmi_rows_reset()
    _view_history_note(spref)

    display_keymaps = keyconfig_merge(kc_user, kc_user)

    filter_type = spref.filter_type
    filter_text = spref.filter_text.strip()
    filter_user_modified = spref.use_filter_user_modified
    filter_labels = keymap_filter_labels()
    filter_addon = spref.use_filter_addon
    filter_conflicts = spref.use_filter_conflicts
    filter_key_exact = spref.use_filter_key_exact
    filtering = (
        bool(filter_text) or filter_user_modified or bool(filter_labels) or filter_addon or
        filter_conflicts
    )

    # The checked group belongs to the conflicts filter, clear it when the filter is turned off.
    if _kmi_conflict_check and not filter_conflicts:
        keymap_conflict_check_clear()

    signature = (
        filter_type, filter_text, filter_user_modified, filter_labels, filter_addon,
        filter_conflicts, filter_key_exact, kc_active.name, _kmi_conflict_check,
    ) if filtering else None
    if signature != _keymap_filter_signature:
        was_filtering = _keymap_filter_signature is not None
        _keymap_filter_signature = signature
        _keymap_filter_pinned.clear()
        if filtering and not was_filtering:
            _kmi_filtered_expanded.clear()

    if not filtering:
        kc_prefs = kc_active.preferences
        if kc_prefs is not None:
            box = layout.box()
            row = box.row(align=True)

            keymappref = context.preferences.keymap
            show_ui_keyconfig = keymappref.show_ui_keyconfig
            row.prop(
                keymappref,
                "show_ui_keyconfig",
                text="",
                icon='DISCLOSURE_TRI_DOWN' if show_ui_keyconfig else 'DISCLOSURE_TRI_RIGHT',
                emboss=False,
            )
            row.label(text="Preferences")
            # The preferences contents cannot be measured, only rows below a collapsed box are
            # scrolled to.
            _kmi_row_advance(1.0 + _KMI_ROW_SEPARATOR)

            if show_ui_keyconfig:
                # Defined by user preset, may contain mistakes out of our control.
                try:
                    kc_prefs.draw(box)
                except Exception:
                    import traceback
                    traceback.print_exc()
            del box
        del kc_prefs

    if filtering:
        filter_text = filter_text.lower()
        # Read by `draw_kmi`, which marks the shadowed items only in this view.
        _kmi_conflicts_view = filter_conflicts
        try:
            ok = draw_filtered(
                display_keymaps,
                filter_type,
                filter_text,
                layout,
                filter_user_modified,
                filter_conflicts,
                filter_labels,
                filter_addon,
                filter_key_exact,
            )
        finally:
            _kmi_conflicts_view = False
    else:
        draw_hierarchy(display_keymaps, layout)
        ok = True
        _keymap_filter_counts_set(0, 0)

    _keymap_tree_filter_ok = ok
