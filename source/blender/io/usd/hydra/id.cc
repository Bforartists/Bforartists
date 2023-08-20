/* SPDX-FileCopyrightText: 2011-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#include "id.h"

#include "BKE_lib_id.h"

namespace blender::io::hydra {

IdData::IdData(HydraSceneDelegate *scene_delegate, const ID *id, pxr::SdfPath const &prim_id)
    : id(id), prim_id(prim_id), scene_delegate_(scene_delegate)
{
}

}  // namespace blender::io::hydra
