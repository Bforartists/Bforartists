/* SPDX-FileCopyrightText: 2016 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

/** \file
 * \ingroup wm
 *
 * \name Gizmos Window Manager API
 * API for usage in window manager code only. It should contain all functionality
 * needed to hook up the gizmo system with Blender's window manager. It's
 * mostly the event system that needs to communicate with gizmo code.
 *
 * Only included in `wm.hh` and lower level files.
 */

#pragma once

#include "DNA_listBase.h"

namespace blender {

struct bContext;
struct wmEvent;
struct wmEventHandler_Gizmo;
struct wmEventHandler_Op;
struct wmGizmo;
struct wmGizmoGroup;
struct wmGizmoMap;
struct wmGizmoOpElem;
struct wmKeyConfig;
struct wmKeyMapItem;
struct wmOperatorType;
struct wmWindowManager;

/* -------------------------------------------------------------------- */
/** \name #wmGizmo
 * \{ */

constexpr int GIZMO_TWEAK_VARIANT_DEFAULT = -1;

wmGizmoOpElem *wm_gizmo_tweak_operator_get(const wmWindowManager *wm, wmGizmo *gz, int variant);
/**
 * Return false when \a kmi invokes a non-default #GIZMOGROUP_OT_gizmo_tweak variant that \a gz
 * does not define, so unrelated gizmos sharing the same key-map do not highlight or consume it.
 */
bool wm_gizmo_keymap_item_is_supported(const wmWindowManager *wm,
                                       const wmGizmo *gz,
                                       const wmKeyMapItem &kmi);

/* `wm_gizmo_type.cc`, for init/exit. */

void wm_gizmotype_free();
/**
 * Called on initialize #WM_init().
 */
void wm_gizmotype_init();

/* `wm_gizmogroup_type.cc`, for init/exit. */

void wm_gizmogrouptype_free();
/**
 * Called on initialize #WM_init().
 */
void wm_gizmogrouptype_init();

/** \} */

/* -------------------------------------------------------------------- */
/** \name #wmGizmoGroup
 * \{ */

void GIZMOGROUP_OT_gizmo_select(wmOperatorType *ot);
void GIZMOGROUP_OT_gizmo_tweak(wmOperatorType *ot);

bool wm_gizmogroup_is_any_selected(const wmGizmoGroup *gzgroup);

/** \} */

/* -------------------------------------------------------------------- */
/** \name #wmGizmoMap
 * \{ */

void wm_gizmomap_remove(wmGizmoMap *gzmap);

/**
 * Initialize key-maps for all existing gizmo-groups
 */
void wm_gizmos_keymap(wmKeyConfig *keyconf);

void wm_gizmomaps_handled_modal_update(bContext *C, wmEvent *event, wmEventHandler_Op *handler);
/**
 * Prepare context for gizmo handling (but only if area/region is
 * part of screen). Version of #wm_handler_op_context for gizmos.
 */
void wm_gizmomap_handler_context_op(bContext *C, wmEventHandler_Op *handler);
void wm_gizmomap_handler_context_gizmo(bContext *C, wmEventHandler_Gizmo *handler);

bool wm_gizmomap_highlight_pending(const wmGizmoMap *gzmap);
bool wm_gizmomap_highlight_handled(wmGizmoMap *gzmap);
/**
 * Try to find a gizmo under the mouse position. 2D intersections have priority over
 * 3D ones (could check for smallest screen-space distance but not needed right now).
 */
wmGizmo *wm_gizmomap_highlight_find(wmGizmoMap *gzmap,
                                    bContext *C,
                                    const wmEvent *event,
                                    int *r_part);
bool wm_gizmomap_highlight_set(wmGizmoMap *gzmap, const bContext *C, wmGizmo *gz, int part);
wmGizmo *wm_gizmomap_highlight_get(wmGizmoMap *gzmap);
/**
 * Caller should call exit when (enable == False).
 *
 * \param variant: Operator variant to invoke instead of the gizmo's highlighted part
 * (resolved with #wm_gizmo_tweak_operator_get). Used by #GIZMOGROUP_OT_gizmo_tweak to run
 * alternatives (e.g. duplicate/extrude) selected via a remappable key-map property.
 */
void wm_gizmomap_modal_set(wmGizmoMap *gzmap,
                           bContext *C,
                           wmGizmo *gz,
                           const wmEvent *event,
                           bool enable,
                           int variant = GIZMO_TWEAK_VARIANT_DEFAULT);

wmGizmo *wm_gizmomap_modal_get(wmGizmoMap *gzmap);
wmGizmo **wm_gizmomap_selected_get(wmGizmoMap *gzmap, int *r_selected_len);
ListBaseT<wmGizmoGroup> *wm_gizmomap_groups_get(wmGizmoMap *gzmap);

/** \} */

/* -------------------------------------------------------------------- */
/** \name #wmGizmoMapType
 * \{ */

void wm_gizmomaptypes_free();

/** \} */

}  // namespace blender
