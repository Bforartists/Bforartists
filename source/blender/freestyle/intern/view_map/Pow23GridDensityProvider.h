/* SPDX-FileCopyrightText: 2023 Blender Authors
 *
 * SPDX-License-Identifier: GPL-2.0-or-later */

#pragma once

/** \file
 * \ingroup freestyle
 * \brief Class to define a cell grid surrounding the projected image of a scene
 */

#include "GridDensityProvider.h"

namespace Freestyle {

class Pow23GridDensityProvider : public GridDensityProvider {
  // Disallow copying and assignment
  Pow23GridDensityProvider(const Pow23GridDensityProvider &other);
  Pow23GridDensityProvider &operator=(const Pow23GridDensityProvider &other);

 public:
  Pow23GridDensityProvider(OccluderSource &source, const real proscenium[4], uint numFaces);
  Pow23GridDensityProvider(OccluderSource &source,
                           const BBox<Vec3r> &bbox,
                           const GridHelpers::Transform &transform,
                           uint numFaces);
  Pow23GridDensityProvider(OccluderSource &source, uint numFaces);

 protected:
  uint numFaces;

 private:
  void initialize(const real proscenium[4]);
};

class Pow23GridDensityProviderFactory : public GridDensityProviderFactory {
 public:
  Pow23GridDensityProviderFactory(uint numFaces);

  AutoPtr<GridDensityProvider> newGridDensityProvider(OccluderSource &source,
                                                      const real proscenium[4]);
  AutoPtr<GridDensityProvider> newGridDensityProvider(OccluderSource &source,
                                                      const BBox<Vec3r> &bbox,
                                                      const GridHelpers::Transform &transform);
  AutoPtr<GridDensityProvider> newGridDensityProvider(OccluderSource &source);

 protected:
  uint numFaces;
};

} /* namespace Freestyle */
