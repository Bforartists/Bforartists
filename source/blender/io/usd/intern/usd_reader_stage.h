/*
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software Foundation,
 * Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
 *
 * The Original Code is Copyright (C) 2021 Tangent Animation and
 * NVIDIA Corporation. All rights reserved.
 */
#pragma once

struct Main;

#include "usd.h"
#include "usd_reader_prim.h"

#include <pxr/usd/usd/stage.h>
#include <pxr/usd/usdGeom/imageable.h>

#include <vector>

struct ImportSettings;

namespace blender::io::usd {

typedef std::map<pxr::SdfPath, std::vector<USDPrimReader *>> ProtoReaderMap;

class USDStageReader {

 protected:
  pxr::UsdStageRefPtr stage_;
  USDImportParams params_;
  ImportSettings settings_;

  std::vector<USDPrimReader *> readers_;

 public:
  USDStageReader(pxr::UsdStageRefPtr stage,
                 const USDImportParams &params,
                 const ImportSettings &settings);

  ~USDStageReader();

  USDPrimReader *create_reader_if_allowed(const pxr::UsdPrim &prim);

  USDPrimReader *create_reader(const pxr::UsdPrim &prim);

  void collect_readers(struct Main *bmain);

  bool valid() const;

  pxr::UsdStageRefPtr stage()
  {
    return stage_;
  }
  const USDImportParams &params() const
  {
    return params_;
  }

  const ImportSettings &settings() const
  {
    return settings_;
  }

  void clear_readers();

  const std::vector<USDPrimReader *> &readers() const
  {
    return readers_;
  };

 private:
  USDPrimReader *collect_readers(Main *bmain, const pxr::UsdPrim &prim);

  bool include_by_visibility(const pxr::UsdGeomImageable &imageable) const;

  bool include_by_purpose(const pxr::UsdGeomImageable &imageable) const;
};

};  // namespace blender::io::usd
