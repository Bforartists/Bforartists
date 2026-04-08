/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: Apache-2.0 */

#include "util/implicit_sharing.h"

CCL_NAMESPACE_BEGIN

ImplicitSharingUserAddFn g_implicit_sharing_user_add_fn = nullptr;
ImplicitSharingUserAddFn g_implicit_sharing_user_remove_fn = nullptr;

void implicit_sharing_init(ImplicitSharingUserAddFn add_fn, ImplicitSharingUserRemoveFn remove_fn)
{
  g_implicit_sharing_user_add_fn = add_fn;
  g_implicit_sharing_user_remove_fn = remove_fn;
}

CCL_NAMESPACE_END
