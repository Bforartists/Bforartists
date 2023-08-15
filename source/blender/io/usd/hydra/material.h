/* SPDX-FileCopyrightText: 2011-2022 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

#include <pxr/imaging/hd/enums.h>
#include <pxr/usd/sdf/assetPath.h>
#include <pxr/usd/sdf/path.h>

#include "DNA_material_types.h"

#include "BLI_map.hh"

#include "id.h"

namespace blender::io::hydra {

class MaterialData : public IdData {
 public:
  bool double_sided = true;

 private:
  pxr::VtValue material_network_map_;

 public:
  MaterialData(HydraSceneDelegate *scene_delegate,
               const Material *material,
               pxr::SdfPath const &prim_id);

  void init() override;
  void insert() override;
  void remove() override;
  void update() override;

  pxr::VtValue get_data(pxr::TfToken const &key) const override;
  pxr::VtValue get_material_resource() const;
  pxr::HdCullStyle cull_style() const;
};

using MaterialDataMap = Map<pxr::SdfPath, std::unique_ptr<MaterialData>>;

}  // namespace blender::io::hydra
