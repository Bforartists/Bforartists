/* SPDX-FileCopyrightText: 2001-2002 NaN Holding BV. All rights reserved.
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */
#pragma once

/** \file
 * \ingroup bke
 * \brief Blender util stuff
 */

#ifdef __cplusplus
extern "C" {
#endif

#include "BLI_compiler_attrs.h"

struct Main;
struct UserDef;

/**
 * Only to be called on exit Blender.
 */
void BKE_blender_free(void);

void BKE_blender_globals_init(void);
void BKE_blender_globals_clear(void);

/** Replace current global Main by the given one, freeing existing one. */
void BKE_blender_globals_main_replace(struct Main *bmain);
/**
 * Replace current global Main by the given one, returning the old one.
 *
 * \warning Advanced, risky workaround addressing the issue that current RNA is not able to process
 * correctly non-G_MAIN data, use with (a lot of) care.
 */
struct Main *BKE_blender_globals_main_swap(struct Main *new_gmain);

void BKE_blender_userdef_data_swap(struct UserDef *userdef_a, struct UserDef *userdef_b);
void BKE_blender_userdef_data_set(struct UserDef *userdef);
void BKE_blender_userdef_data_set_and_free(struct UserDef *userdef);

/**
 * This function defines which settings a template will override for the user preferences.
 *
 * \note the order of `userdef_a` & `userdef_b` isn't important as values are simply swapped.
 */
void BKE_blender_userdef_app_template_data_swap(struct UserDef *userdef_a,
                                                struct UserDef *userdef_b);
void BKE_blender_userdef_app_template_data_set(struct UserDef *userdef);
void BKE_blender_userdef_app_template_data_set_and_free(struct UserDef *userdef);

/**
 * When loading a new userdef from file,
 * or when exiting Blender.
 */
void BKE_blender_userdef_data_free(struct UserDef *userdef, bool clear_fonts);

/* Blenders' own atexit (avoids leaking) */
void BKE_blender_atexit_register(void (*func)(void *user_data), void *user_data);
void BKE_blender_atexit_unregister(void (*func)(void *user_data), const void *user_data);
void BKE_blender_atexit(void);

#ifdef __cplusplus
}
#endif
