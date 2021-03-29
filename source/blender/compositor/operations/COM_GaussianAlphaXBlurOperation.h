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
 * Copyright 2011, Blender Foundation.
 */

#pragma once

#include "COM_BlurBaseOperation.h"
#include "COM_NodeOperation.h"

namespace blender::compositor {

class GaussianAlphaXBlurOperation : public BlurBaseOperation {
 private:
  float *m_gausstab;
  float *m_distbuf_inv;
  int m_falloff; /* falloff for distbuf_inv */
  bool m_do_subtract;
  int m_filtersize;
  void updateGauss();

 public:
  GaussianAlphaXBlurOperation();

  /**
   * \brief The inner loop of this operation.
   */
  void executePixel(float output[4], int x, int y, void *data) override;

  /**
   * \brief initialize the execution
   */
  void initExecution() override;

  /**
   * \brief Deinitialize the execution
   */
  void deinitExecution() override;

  void *initializeTileData(rcti *rect) override;
  bool determineDependingAreaOfInterest(rcti *input,
                                        ReadBufferOperation *readOperation,
                                        rcti *output) override;

  /**
   * Set subtract for Dilate/Erode functionality
   */
  void setSubtract(bool subtract)
  {
    this->m_do_subtract = subtract;
  }
  void setFalloff(int falloff)
  {
    this->m_falloff = falloff;
  }
};

}  // namespace blender::compositor
