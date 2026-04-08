/* SPDX-FileCopyrightText: 2026 Blender Authors
 *
 * SPDX-License-Identifier: Apache-2.0 */

#include "util/implicit_sharing.h"

#include "BLI_implicit_sharing.hh"

#include "blender/CCL_api.h"

namespace blender {

void CCL_implicit_sharing_init()
{
  ccl::implicit_sharing_init(
      [](ccl::ImplicitSharingInfo data) {
        const auto *info = static_cast<const blender::ImplicitSharingInfo *>(data);
        info->add_user();
      },
      [](ccl::ImplicitSharingInfo data) {
        const auto *info = static_cast<const blender::ImplicitSharingInfo *>(data);
        info->remove_user_and_delete_if_last();
      });
}

}  // namespace blender
