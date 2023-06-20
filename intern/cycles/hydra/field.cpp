/* SPDX-FileCopyrightText: 2022 NVIDIA Corporation
 * SPDX-FileCopyrightText: 2022 Blender Foundation
 *
 * SPDX-License-Identifier: Apache-2.0 */

#include "hydra/field.h"
#include "hydra/session.h"
#include "scene/image_vdb.h"
#include "scene/scene.h"

#include <pxr/imaging/hd/sceneDelegate.h>
#include <pxr/usd/sdf/assetPath.h>

HDCYCLES_NAMESPACE_OPEN_SCOPE

#if PXR_VERSION < 2108
// clang-format off
TF_DEFINE_PRIVATE_TOKENS(_tokens,
   (fieldName)
);
// clang-format on
#endif

#ifdef WITH_OPENVDB
class HdCyclesVolumeLoader : public VDBImageLoader {
 public:
  HdCyclesVolumeLoader(const std::string &filePath, const std::string &gridName)
      : VDBImageLoader(gridName)
  {
    /* Disable delay loading and file copying, this has poor performance on network drives. */
    const bool delay_load = false;
    try {
      openvdb::io::File file(filePath);
      file.setCopyMaxBytes(0);
      if (file.open(delay_load)) {
        grid = file.readGrid(gridName);
      }
    }
    catch (const openvdb::IoError &e) {
      VLOG_WARNING << "Error loading OpenVDB file: " << e.what();
    }
    catch (...) {
      VLOG_WARNING << "Error loading OpenVDB file: Unknown error";
    }
  }
};
#endif

HdCyclesField::HdCyclesField(const SdfPath &bprimId, const TfToken &typeId) : HdField(bprimId) {}

HdCyclesField::~HdCyclesField() {}

HdDirtyBits HdCyclesField::GetInitialDirtyBitsMask() const
{
  return DirtyBits::DirtyParams;
}

void HdCyclesField::Sync(HdSceneDelegate *sceneDelegate,
                         HdRenderParam *renderParam,
                         HdDirtyBits *dirtyBits)
{
#ifdef WITH_OPENVDB
  VtValue value;
  const SdfPath &id = GetId();

  if (*dirtyBits & DirtyBits::DirtyParams) {
    value = sceneDelegate->Get(id, HdFieldTokens->filePath);
    if (value.IsHolding<SdfAssetPath>()) {
      std::string filename = value.UncheckedGet<SdfAssetPath>().GetResolvedPath();
      if (filename.empty()) {
        filename = value.UncheckedGet<SdfAssetPath>().GetAssetPath();
      }

#  if PXR_VERSION >= 2108
      value = sceneDelegate->Get(id, HdFieldTokens->fieldName);
#  else
      value = sceneDelegate->Get(id, _tokens->fieldName);
#  endif
      if (value.IsHolding<TfToken>()) {
        ImageLoader *const loader = new HdCyclesVolumeLoader(
            filename, value.UncheckedGet<TfToken>().GetString());

        const SceneLock lock(renderParam);

        ImageParams params;
        params.frame = 0.0f;

        _handle = lock.scene->image_manager->add_image(loader, params, false);
      }
    }
  }
#endif

  *dirtyBits = DirtyBits::Clean;
}

HDCYCLES_NAMESPACE_CLOSE_SCOPE
