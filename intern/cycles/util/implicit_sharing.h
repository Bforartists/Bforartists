/* SPDX-FileCopyrightText: 2026 Blender Foundation
 *
 * SPDX-License-Identifier: Apache-2.0 */

#pragma once

CCL_NAMESPACE_BEGIN

using ImplicitSharingInfo = const void *;

using ImplicitSharingUserAddFn = void (*)(ImplicitSharingInfo);
using ImplicitSharingUserRemoveFn = void (*)(ImplicitSharingInfo);

extern ImplicitSharingUserAddFn g_implicit_sharing_user_add_fn;
extern ImplicitSharingUserRemoveFn g_implicit_sharing_user_remove_fn;

/**
 * Set function pointers to be called when implicit sharing (use count tracking) is enabled.
 * "Sharing info" references that own data like attribute arrays are passed as void pointers to
 * various Cycles API functions, and these functions are called to change the reference count.
 */
void implicit_sharing_init(ImplicitSharingUserAddFn add_fn, ImplicitSharingUserRemoveFn remove_fn);

CCL_NAMESPACE_END
